import numpy as np
import cv2
from paddleocr import PaddleOCR
import gc

class OCRProcessor:
    """OCR处理类，封装PaddleOCR的功能"""
    
    def __init__(self, ocr_settings, confidence_threshold=0.8):
        """初始化OCR处理器
        
        Args:
            ocr_settings: OCR引擎的设置字典
            confidence_threshold: 置信度阈值
        """
        self.ocr_settings = ocr_settings
        self.confidence_threshold = confidence_threshold
        self.ocr = None
        
    def initialize(self):
        """初始化OCR引擎"""
        if self.ocr is not None:
            return
            
        try:
            print("初始化OCR引擎...")
            self.ocr = PaddleOCR(**self.ocr_settings)
            print("OCR引擎初始化成功")
            # 强制进行一次内存回收
            gc.collect()
            return True
        except Exception as e:
            print(f"OCR引擎初始化失败: {str(e)}")
            return False
    
    def release(self):
        """释放OCR引擎资源"""
        if self.ocr:
            self.ocr = None
            gc.collect()  # 强制垃圾回收
            print("OCR引擎资源已释放")
    
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
            print(f"已缩小图像尺寸: {width}x{height} -> {new_width}x{new_height}")
        
        img_array = np.array(image)
        # 使用灰度模式提高性能
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            # 二值化处理增强对比度
            _, img_binary = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            # 转回三通道图像（OCR需要）
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
                
        try:
            # 预处理图像
            img_array = self.preprocess_image(image)
            
            # 执行OCR识别
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
            return final_text
            
        except Exception as e:
            print(f"OCR识别出错: {str(e)}")
            return "" 