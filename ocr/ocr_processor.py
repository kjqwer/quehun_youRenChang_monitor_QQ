import numpy as np
import cv2
from paddleocr import PaddleOCR
import gc
import os
import time
import psutil
import paddle

class OCRProcessor:
    """OCR处理类，封装PaddleOCR的功能"""
    
    def __init__(self, ocr_settings, confidence_threshold=0.8, memory_threshold=1800, auto_reset_enabled=True):
        """初始化OCR处理器
        
        Args:
            ocr_settings: OCR引擎的设置字典
            confidence_threshold: 置信度阈值
            memory_threshold: 内存阈值，单位MB
            auto_reset_enabled: 是否启用自动内存重置
        """
        # 基础设置
        self.ocr_settings = ocr_settings
        self.confidence_threshold = confidence_threshold
        self.ocr = None
        
        # 内存阈值设置
        self.memory_threshold = memory_threshold * 1024 * 1024  # 转换为字节
        self.auto_reset_enabled = auto_reset_enabled
        
        # 优化设置
        self.default_rec_model = None
        self.default_det_model = None
        
        # 设置环境变量，优化内存占用
        os.environ['FLAGS_allocator_strategy'] = 'auto_growth'
        os.environ['FLAGS_fraction_of_gpu_memory_to_use'] = '0'
        os.environ['FLAGS_eager_delete_tensor_gb'] = '0.0'  # 立即释放不需要的张量
        os.environ['FLAGS_fast_eager_deletion_mode'] = 'true'  # 快速内存释放
        os.environ['FLAGS_memory_fraction_of_eager_deletion'] = '1.0'  # 立即释放全部可释放内存
        
        # 内存监控
        self.last_process_memory = 0
        self.call_count = 0
        self.last_reset_time = time.time()
        self.reset_threshold = 50  # 每50次请求或内存增加超过200MB重置引擎
        self.memory_increase_threshold = 200 * 1024 * 1024  # 200MB
    
    def update_settings(self, memory_threshold=None, auto_reset_enabled=None):
        """更新设置
        
        Args:
            memory_threshold: 内存阈值，单位MB
            auto_reset_enabled: 是否启用自动内存重置
        """
        if memory_threshold is not None:
            self.memory_threshold = memory_threshold * 1024 * 1024
        if auto_reset_enabled is not None:
            self.auto_reset_enabled = auto_reset_enabled
        
    def get_process_memory(self):
        """获取当前进程内存占用"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss
        
    def initialize(self):
        """初始化OCR引擎"""
        if self.ocr is not None:
            return True
            
        try:
            print("初始化OCR引擎...")
            
            # 清理可能残留的缓存
            self._clean_paddle_cache()
            
            # 基于使用场景对OCR设置进行优化
            optimized_settings = self.ocr_settings.copy()
            
            # 关闭不必要的功能
            optimized_settings.update({
                'use_angle_cls': False,     # 不进行方向分类
                'det_db_unclip_ratio': 1.6, # 减小文本检测区域，提高速度
                'rec_batch_num': 6,         # 减小批处理数量
                'use_mp': False,            # 不使用多进程
                'total_process_num': 1,     # 单进程
                'cls_model_dir': None,      # 不加载方向分类模型
                'rec_char_dict_path': None, # 使用默认字典
                'use_tensorrt': False,      # 不使用TensorRT
                'enable_mkldnn': True,      # 启用MKL加速
                'det_limit_type': 'max',    # 限制最大边长而非最小边长
            })
            
            # 轻量级检测器设置
            if 'det_limit_side_len' not in optimized_settings:
                optimized_settings['det_limit_side_len'] = 960  # 限制最大检测尺寸
            
            self.ocr = PaddleOCR(**optimized_settings)
            print("OCR引擎初始化成功")
            
            # 保存初始内存占用
            self.last_process_memory = self.get_process_memory()
            self.call_count = 0
            self.last_reset_time = time.time()
            
            # 强制进行一次内存回收
            self._clean_paddle_cache()
            gc.collect()
            return True
        except Exception as e:
            print(f"OCR引擎初始化失败: {str(e)}")
            return False
    
    def _clean_paddle_cache(self):
        """清理Paddle框架缓存"""
        try:
            # 清理Paddle的缓存
            paddle.device.cuda.empty_cache()
            # 清理CPU内存缓存
            if hasattr(paddle, 'fluid') and hasattr(paddle.fluid, 'core') and hasattr(paddle.fluid.core, 'garbage_collect_memory'):
                paddle.fluid.core.garbage_collect_memory()
        except Exception as e:
            print(f"清理Paddle缓存出错 (可忽略): {e}")
    
    def release(self):
        """释放OCR引擎资源"""
        if self.ocr:
            # 释放OCR引擎
            self.ocr = None
            # 清理Paddle缓存
            self._clean_paddle_cache()
            # 强制垃圾回收
            gc.collect()
            gc.collect()  # 连续调用两次，更彻底地回收
            print("OCR引擎资源已释放")
    
    def _check_memory_and_reset_if_needed(self):
        """检查内存占用，必要时重置引擎"""
        # 如果自动重置被禁用，直接返回
        if not self.auto_reset_enabled:
            return False
            
        # 增加调用计数
        self.call_count += 1
        
        # 获取当前内存占用
        current_memory = self.get_process_memory()
        memory_increase = current_memory - self.last_process_memory
        time_elapsed = time.time() - self.last_reset_time
        
        # 检查是否超过配置的内存阈值
        if current_memory > self.memory_threshold:
            print(f"内存占用({current_memory/1024/1024:.2f}MB)超过阈值({self.memory_threshold/1024/1024:.2f}MB)，正在重置OCR引擎...")
            self.release()
            time.sleep(0.5)  # 短暂暂停，等待资源释放
            self.initialize()
            return True
        
        # 检查内存增长和调用次数
        elif (memory_increase > self.memory_increase_threshold and time_elapsed > 60) or \
             (self.call_count >= self.reset_threshold and time_elapsed > 120):
            print(f"内存占用增加: {memory_increase/1024/1024:.2f}MB, 调用次数: {self.call_count}")
            print("重置OCR引擎以释放内存...")
            self.release()
            time.sleep(0.5)  # 短暂暂停，等待资源释放
            self.initialize()
            return True
            
        return False
    
    def preprocess_image(self, image):
        """预处理图像以提高OCR精度
        
        Args:
            image: PIL图像对象
            
        Returns:
            处理后的numpy数组
        """
        # 降低图像分辨率以提高性能
        width, height = image.size
        # 如果图像过大，缩小它
        max_dimension = 1024  # 最大尺寸限制
        if width > max_dimension or height > max_dimension:
            if width > height:
                new_width = max_dimension
                new_height = int(height * (max_dimension / width))
            else:
                new_height = max_dimension
                new_width = int(width * (max_dimension / height))
            image = image.resize((new_width, new_height), image.LANCZOS)
        
        img_array = np.array(image)
        
        # 针对中文文本优化的预处理
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            # 转为灰度图
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # 计算图像的平均亮度，动态选择处理方法
            mean_brightness = np.mean(img_gray)
            
            if mean_brightness > 180:  # 亮图像
                # OTSU二值化
                _, img_binary = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            elif mean_brightness < 100:  # 暗图像
                # 先增强对比度
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(img_gray)
                # 再二值化
                _, img_binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                # 释放临时变量
                del enhanced
            else:  # 正常亮度图像
                _, img_binary = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 转回三通道图像
            img_array = cv2.cvtColor(img_binary, cv2.COLOR_GRAY2RGB)
            
            # 释放临时变量
            del img_gray
            del img_binary
            
        return img_array
    
    def recognize_text(self, image):
        """识别图像中的文字
        
        Args:
            image: PIL图像对象
            
        Returns:
            识别出的文本字符串
        """
        if not self.ocr:
            if not self.initialize():
                return ""
        
        # 检查内存占用并在需要时重置引擎
        engine_reset = self._check_memory_and_reset_if_needed()
        if engine_reset and not self.ocr:
            if not self.initialize():
                return ""
                
        try:
            # 预处理图像
            img_array = self.preprocess_image(image)
            
            # 执行OCR识别，禁用方向分类
            result = self.ocr.ocr(img_array, cls=False)
            
            # 释放数组资源
            del img_array
            
            if not result or not result[0]:
                return ""
            
            texts = []
            for line in result[0]:
                text = line[1][0]
                confidence = line[1][1]
                if confidence > self.confidence_threshold:
                    texts.append(text)
            
            final_text = "\n".join(texts)
            
            # 更新最后处理的内存占用
            self.last_process_memory = self.get_process_memory()
            
            return final_text
            
        except Exception as e:
            print(f"OCR识别出错: {str(e)}")
            # 出错时重置引擎
            self.release()
            return "" 