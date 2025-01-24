import win32gui
import win32ui
import win32con
from PIL import Image
import time
import ctypes
import re
from paddleocr import PaddleOCR
import numpy as np
import cv2
import tkinter as tk
from tkinter import ttk
import json
from config import *


# 用于记录已经弹窗过的内容
alerted_messages = set()

# 用于记录上一次的打印结果
final_text_last = None

# 加载 user32.dll
user32 = ctypes.windll.user32

# 用于记录上一次的识别结果
last_recognized_text = None

# 初始化 PaddleOCR
ocr = PaddleOCR(use_angle_cls=False, lang="ch", show_log=False)

class RegionSelector:
    def __init__(self, window_title):
        self.window_title = window_title
        self.crop_area = None
        
    def load_last_area(self):
        """加载上次保存的区域"""
        try:
            with open(CROP_AREA_FILE, 'r') as f:
                return tuple(map(int, json.load(f)))
        except:
            return None

    def save_area(self, area):
        """保存选择的区域"""
        with open(CROP_AREA_FILE, 'w') as f:
            json.dump(list(area), f)

    def select_region(self):
        """可视化选择区域"""
        # 获取窗口截图
        hwnd = get_window_handle(self.window_title)
        image = capture_window(hwnd)
        img_np = np.array(image)
        img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        # 创建窗口和选择ROI
        cv2.namedWindow('Select Region')
        last_area = self.load_last_area()
        
        if last_area:
            # 显示上次的选择区域
            img_with_rect = img_cv.copy()
            cv2.rectangle(img_with_rect, (last_area[0], last_area[1]), 
                        (last_area[2], last_area[3]), (0, 255, 0), 2)
            cv2.imshow('Select Region', img_with_rect)
            
            # 创建确认对话框
            root = tk.Tk()
            root.title("确认")
            
            def use_last():
                self.crop_area = last_area
                root.quit()
                root.destroy()
                
            def select_new():
                root.quit()
                root.destroy()
                self.crop_area = cv2.selectROI('Select Region', img_cv, False)
                
            tk.Label(root, text="是否使用上次的选择区域？").pack(pady=10)
            ttk.Button(root, text="使用上次区域", command=use_last).pack(pady=5)
            ttk.Button(root, text="重新选择", command=select_new).pack(pady=5)
            
            root.mainloop()
        else:
            # 直接进入选择模式
            self.crop_area = cv2.selectROI('Select Region', img_cv, False)

        cv2.destroyAllWindows()
        
        # 转换ROI格式并保存
        if isinstance(self.crop_area, tuple):
            x, y, w, h = self.crop_area
            self.crop_area = (x, y, x + w, y + h)
            self.save_area(self.crop_area)
            
        return self.crop_area

class OCRMonitor:
    def __init__(self):
        # 初始化OCR
        self.ocr = PaddleOCR(**OCR_SETTINGS)
        self.last_recognized_text = None
        self.alerted_messages = set()
        
    def start_monitoring(self, window_title, crop_area):
        """开始监控"""
        try:
            hwnd = get_window_handle(window_title)
            print("程序启动成功，开始监控...")

            while True:
                try:
                    # 截图并识别
                    image = capture_window(hwnd)
                    cropped_image = crop_image(image, *crop_area)
                    text = self.recognize_text(cropped_image)

                    # 只在文本变化时进行处理
                    if text and text != self.last_recognized_text:
                        self.last_recognized_text = text
                        is_target, message = self.check_for_target(text)
                        if is_target:
                            print(f"触发提醒: {message}")

                    time.sleep(MONITOR_SETTINGS['scan_interval'])

                except Exception as e:
                    print(f"识别过程出错: {e}")
                    time.sleep(1)
                    continue

        except Exception as e:
            print(f"程序出错: {e}")

    def recognize_text(self, image):
        """识别文字"""
        global final_text_last  # 上次识别的变量声明
        
        img_array = np.array(image)
        result = self.ocr.ocr(img_array, cls=False)
        
        if not result or not result[0]:
            return ""
        
        texts = []
        for line in result[0]:
            text = line[1][0]  # 文本内容
            confidence = line[1][1]  # 置信度
            if confidence > MONITOR_SETTINGS['confidence_threshold']:
                texts.append(text)
        
        final_text = "\n".join(texts)

        if final_text != final_text_last:
            print("\n寻找车车中:")
            if final_text:
                print(f"{final_text}")
        
        final_text_last = final_text
        return final_text

    def check_for_target(self, text):
        """检查目标内容"""
        lines = text.splitlines()

        for line in lines:
            # 匹配5位数字的车牌
            number_match = re.search(r'\b\d{5}\b', line)
            if number_match:
                number = number_match.group()
                message = f"发现车牌: {number}"
                if message not in self.alerted_messages:
                    show_alert(message)
                    self.alerted_messages.add(message)
                    return True, message
                    
            # 关键词匹配
            for keyword in KEYWORDS:
                if keyword in line:
                    message = f"发现车车: {line}"
                    if message not in self.alerted_messages:
                        show_alert(message)
                        self.alerted_messages.add(message)
                        return True, message
        return False, None

def get_window_handle(window_title):
    """获取窗口句柄"""
    hwnd = win32gui.FindWindow(None, window_title)
    if hwnd == 0:
        raise Exception(f"未找到标题为 '{window_title}' 的窗口")
    return hwnd

def capture_window(hwnd):
    """截图窗口（支持后台窗口）"""
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top

    # 创建设备上下文
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    # 创建位图对象
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)

    # 将位图选入设备上下文
    saveDC.SelectObject(saveBitMap)

    # 使用 PrintWindow 捕获窗口内容
    result = user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)  # 2 表示 PW_RENDERFULLCONTENT
    if result == 0:
        raise Exception("无法捕获窗口内容")

    # 将位图转换为 PIL 图像
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)

    im = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1
    )

    # 释放资源
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)

    return im

def crop_image(image, left, top, right, bottom):
    """裁剪图像到指定区域"""
    return image.crop((left, top, right, bottom))

def show_alert(message):
    """显示弹窗警告"""
    ctypes.windll.user32.MessageBoxW(0, message, "警告", 0x30)  # 0x30 表示警告图标

def main():
    """主函数"""
    try:
        # 初始化OCR
        ocr = PaddleOCR(**OCR_SETTINGS)
        last_recognized_text = None
        alerted_messages = set()

        # 获取窗口句柄
        hwnd = get_window_handle(MONITOR_SETTINGS['window_title'])
        print("找到游戏窗口，准备选择监控区域...")

        # 获取初始截图用于选择区域
        initial_image = capture_window(hwnd)
        crop_area = select_region(initial_image)
        print(f"选择的监控区域: {crop_area}")

        print("开始监控...")
        while True:
            try:
                # 截图并识别
                image = capture_window(hwnd)
                cropped_image = crop_image(image, *crop_area)
                text = recognize_text(cropped_image, ocr)

                # 只在文本变化时进行处理
                if text and text != last_recognized_text:
                    print("-" * 50)
                    print(f"识别到新内容: \n{text}")
                    last_recognized_text = text
                    is_target, message = check_for_target(text, alerted_messages)
                    if is_target:
                        print(f"触发提醒: {message}")
                    print("-" * 50)

                time.sleep(MONITOR_SETTINGS['scan_interval'])

            except Exception as e:
                print(f"识别过程出错: {e}")
                time.sleep(1)
                continue

    except Exception as e:
        print(f"程序出错: {e}")

if __name__ == "__main__":
    try:
        # 初始化区域选择器
        selector = RegionSelector(MONITOR_SETTINGS['window_title'])
        crop_area = selector.select_region()
        
        if crop_area:
            # 初始化监控器并开始监控
            monitor = OCRMonitor()
            monitor.start_monitoring(MONITOR_SETTINGS['window_title'], crop_area)
        else:
            print("未选择监控区域，程序退出")
            
    except Exception as e:
        print(f"程序异常退出: {e}")