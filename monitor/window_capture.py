import win32gui
import win32ui
import win32con
import ctypes
import cv2
import numpy as np
import json
import os
from PIL import Image
import gc

class WindowCapture:
    """窗口捕获类，负责窗口截图和区域选择"""
    
    def __init__(self):
        """初始化窗口捕获"""
        self.selected_window = None
        self.crop_area = None
        self.crop_area_file = 'last_crop_area.txt'
    
    def get_window_list(self):
        """获取所有可见窗口列表"""
        windows = []
        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append((title, hwnd))
        win32gui.EnumWindows(enum_windows_callback, None)
        return windows
    
    def find_window_by_title(self, title):
        """根据标题查找窗口"""
        windows = self.get_window_list()
        for window_title, hwnd in windows:
            if title in window_title:
                return hwnd
        return None
    
    def capture_window(self, hwnd):
        """截图窗口内容"""
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)

            im = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )

            # 确保资源释放
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)

            return im
        except Exception as e:
            print(f"截图过程出错: {str(e)}")
            # 确保资源释放
            try:
                if 'saveBitMap' in locals():
                    win32gui.DeleteObject(saveBitMap.GetHandle())
                if 'saveDC' in locals():
                    saveDC.DeleteDC()
                if 'mfcDC' in locals():
                    mfcDC.DeleteDC()
                if 'hwndDC' in locals():
                    win32gui.ReleaseDC(hwnd, hwndDC)
            except:
                pass
            return None
    
    def select_monitor_area(self):
        """选择监控区域"""
        if not self.selected_window:
            print("请先选择监控窗口")
            return False
            
        # 获取窗口截图
        image = self.capture_window(self.selected_window)
        if image is None:
            print("无法捕获窗口内容")
            return False
            
        img_np = np.array(image)
        img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        
        # 创建窗口并选择ROI
        cv2.namedWindow('Select Region', cv2.WINDOW_NORMAL)
        print("请用鼠标选择监控区域，选择完成后按Enter键确认")
        roi = cv2.selectROI('Select Region', img_cv, False)
        cv2.destroyAllWindows()
        
        # 释放图像资源
        del img_np
        del img_cv
        del image
        gc.collect()  # 强制回收
        
        # 转换ROI格式
        x, y, w, h = roi
        if w > 0 and h > 0:  # 确保选择了有效区域
            self.crop_area = (x, y, x + w, y + h)
            print(f"已选择监控区域: {self.crop_area}")
            
            # 保存裁剪区域到文件
            try:
                with open(self.crop_area_file, 'w') as f:
                    json.dump(list(self.crop_area), f)
                print("已保存监控区域设置")
                return True
            except Exception as e:
                print(f"保存监控区域失败: {str(e)}")
                return False
        else:
            print("未选择有效的监控区域，请重试")
            return False
    
    def load_crop_area(self):
        """加载上次保存的裁剪区域"""
        try:
            if os.path.exists(self.crop_area_file):
                with open(self.crop_area_file, 'r') as f:
                    self.crop_area = tuple(json.load(f))
                print(f"已加载上次的监控区域: {self.crop_area}")
                return True
            return False
        except Exception as e:
            print(f"加载监控区域失败: {str(e)}")
            return False
    
    def get_cropped_image(self):
        """捕获窗口并裁剪指定区域"""
        if not self.selected_window or not self.crop_area:
            print("未设置监控窗口或区域")
            return None
            
        image = self.capture_window(self.selected_window)
        if image is None:
            return None
            
        try:
            cropped_image = image.crop(self.crop_area)
            # 释放原始图像资源
            del image
            return cropped_image
        except Exception as e:
            print(f"裁剪图像失败: {str(e)}")
            return None 