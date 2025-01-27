import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import win32gui
import win32ui
import win32con
import json
from PIL import Image
import time
import ctypes
import re
from paddleocr import PaddleOCR
import numpy as np
import cv2
from config import *

class Logger:
    def __init__(self, text_widget):
        self.terminal = sys.stdout
        self.text_widget = text_widget

    def write(self, message):
        try:
            if self.terminal:
                self.terminal.write(message)
            if self.text_widget:
                self.text_widget.insert(tk.END, message)
                self.text_widget.see(tk.END)
                self.text_widget.update()
        except:
            pass  # 忽略错误，确保程序不会崩溃

    def flush(self):
        try:
            if self.terminal:
                self.terminal.flush()
        except:
            pass

class SettingsDialog:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("设置")
        self.window.geometry("400x500")
        
        # 创建notebook用于分页
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 基本设置页面
        self.basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.basic_frame, text="基本设置")
        
        # 扫描间隔设置
        ttk.Label(self.basic_frame, text="扫描间隔(秒):").pack(pady=5)
        self.scan_interval = ttk.Entry(self.basic_frame)
        self.scan_interval.insert(0, str(MONITOR_SETTINGS['scan_interval']))
        self.scan_interval.pack(pady=5)
        
        # 置信度阈值设置
        ttk.Label(self.basic_frame, text="OCR置信度阈值(0-1):").pack(pady=5)
        self.confidence = ttk.Entry(self.basic_frame)
        self.confidence.insert(0, str(MONITOR_SETTINGS['confidence_threshold']))
        self.confidence.pack(pady=5)
        
        # 关键词设置页面
        self.keywords_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.keywords_frame, text="关键词设置")
        
        # 关键词列表
        self.keywords_list = tk.Listbox(self.keywords_frame, height=10)
        self.keywords_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加现有关键词
        for keyword in KEYWORDS:
            self.keywords_list.insert(tk.END, keyword)
        
        # 关键词操作按钮
        self.keyword_frame = ttk.Frame(self.keywords_frame)
        self.keyword_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.keyword_entry = ttk.Entry(self.keyword_frame)
        self.keyword_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(self.keyword_frame, text="添加", 
                  command=self.add_keyword).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.keyword_frame, text="删除", 
                  command=self.delete_keyword).pack(side=tk.LEFT)
        
        # 保存按钮
        ttk.Button(self.window, text="保存设置", 
                  command=self.save_settings).pack(pady=10)
        
    def add_keyword(self):
        keyword = self.keyword_entry.get().strip()
        if keyword and keyword not in self.keywords_list.get(0, tk.END):
            self.keywords_list.insert(tk.END, keyword)
            self.keyword_entry.delete(0, tk.END)
    
    def delete_keyword(self):
        selection = self.keywords_list.curselection()
        if selection:
            self.keywords_list.delete(selection)
    
    def save_settings(self):
        try:
            # 更新MONITOR_SETTINGS
            MONITOR_SETTINGS['scan_interval'] = float(self.scan_interval.get())
            MONITOR_SETTINGS['confidence_threshold'] = float(self.confidence.get())
            
            # 更新KEYWORDS
            global KEYWORDS
            KEYWORDS = list(self.keywords_list.get(0, tk.END))
            
            # 保存到配置文件
            config_content = f"""# 监控设置
                    MONITOR_SETTINGS = {{
                        'window_title': '{MONITOR_SETTINGS["window_title"]}',
                        'scan_interval': {MONITOR_SETTINGS['scan_interval']},
                        'confidence_threshold': {MONITOR_SETTINGS['confidence_threshold']}
                    }}

                    # OCR设置
                    OCR_SETTINGS = {{
                        'use_angle_cls': False,
                        'lang': "ch",
                        'show_log': False
                    }}

                    # 关键词列表
                    KEYWORDS = {KEYWORDS}
                    """
            with open('config.py', 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            messagebox.showinfo("成功", "设置已保存")
            self.window.destroy()
            
        except ValueError as e:
            messagebox.showerror("错误", "请输入有效的数值")

class MonitorApp:
    def __init__(self):
        # 保存原始的stdout
        self.original_stdout = sys.stdout
        
        self.root = tk.Tk()
        self.root.title("车牌监控程序")
        self.root.geometry("600x400")
        
        # 添加关闭窗口的协议处理
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建日志文本框
        self.log_text = scrolledtext.ScrolledText(self.main_frame, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 重定向输出到日志框
        sys.stdout = Logger(self.log_text)
        
        # 创建按钮框架
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=5)
        
        # 创建按钮
        ttk.Button(self.button_frame, text="选择监控窗口", command=self.select_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="开始监控", command=self.start_monitor).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="停止监控", command=self.stop_monitor).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="设置", command=self.show_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="退出程序", command=self.quit_app).pack(side=tk.RIGHT, padx=5)
        
        # 初始化变量
        self.monitoring = False
        self.selected_window = None
        self.crop_area = None
        self.ocr = None
        self.alerted_messages = set()
        
        # 添加上次打印的文本记录
        self.last_printed_text = None
        
        print("程序已启动，请选择要监控的窗口...")

    def select_window(self):
        """选择要监控的窗口"""
        # 获取所有可见窗口
        windows = []
        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append((title, hwnd))
        win32gui.EnumWindows(enum_windows_callback, None)
        
        # 创建窗口选择对话框
        select_window = tk.Toplevel(self.root)
        select_window.title("选择窗口")
        select_window.geometry("400x300")
        
        # 创建列表框
        listbox = tk.Listbox(select_window)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 添加窗口到列表
        for title, _ in windows:
            listbox.insert(tk.END, title)
        
        def confirm_selection():
            if listbox.curselection():
                index = listbox.curselection()[0]
                self.selected_window = windows[index][1]
                print(f"已选择窗口: {windows[index][0]}")
                select_window.destroy()
                self.select_monitor_area()
                
        ttk.Button(select_window, text="确认", command=confirm_selection).pack(pady=5)

    def select_monitor_area(self):
        """选择监控区域"""
        if not self.selected_window:
            return
            
        # 获取窗口截图
        image = self.capture_window(self.selected_window)
        img_np = np.array(image)
        img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        
        # 创建窗口并选择ROI
        cv2.namedWindow('Select Region')
        print("请用鼠标选择监控区域，选择完成后按Enter键确认")
        roi = cv2.selectROI('Select Region', img_cv, False)
        cv2.destroyAllWindows()
        
        # 转换ROI格式
        x, y, w, h = roi
        self.crop_area = (x, y, x + w, y + h)
        print(f"已选择监控区域: {self.crop_area}")

    def capture_window(self, hwnd):
        """截图窗口"""
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

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        return im

    def start_monitor(self):
        """开始监控"""
        if not self.selected_window or not self.crop_area:
            messagebox.showwarning("警告", "请先选择监控窗口和区域")
            return
            
        if self.monitoring:
            return
            
        self.monitoring = True
        if not self.ocr:
            print("初始化OCR引擎...")
            self.ocr = PaddleOCR(**OCR_SETTINGS)
        
        print("开始监控...")
        self.monitor_loop()

    def monitor_loop(self):
        """监控循环"""
        if not self.monitoring:
            return
            
        try:
            image = self.capture_window(self.selected_window)
            cropped_image = image.crop(self.crop_area)
            text = self.recognize_text(cropped_image)
            
            if text:
                self.check_for_target(text)
                
        except Exception as e:
            print(f"监控过程出错: {str(e)}")
            
        finally:
            if self.monitoring:
                self.root.after(int(MONITOR_SETTINGS['scan_interval'] * 1000), self.monitor_loop)

    def recognize_text(self, image):
        """识别文字"""
        img_array = np.array(image)
        result = self.ocr.ocr(img_array, cls=False)
        
        if not result or not result[0]:
            return ""
        
        texts = []
        for line in result[0]:
            text = line[1][0]
            confidence = line[1][1]
            if confidence > MONITOR_SETTINGS['confidence_threshold']:
                texts.append(text)
        
        final_text = "\n".join(texts)
        
        # 只在文本变化时打印
        if final_text and final_text != self.last_printed_text:
            print("\n寻找车车中:")
            print(final_text)
            self.last_printed_text = final_text
        
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
                    self.show_alert(message)
                    self.alerted_messages.add(message)
                    return
                    
            # 关键词匹配
            for keyword in KEYWORDS:
                if keyword in line:
                    message = f"发现车车: {line}"
                    if message not in self.alerted_messages:
                        self.show_alert(message)
                        self.alerted_messages.add(message)
                        return

    def show_alert(self, message):
        """显示警告"""
        print(f"触发提醒: {message}")
        # 获取当前程序窗口句柄
        hwnd = self.root.winfo_id()
        # 显示置顶的消息框
        ctypes.windll.user32.MessageBoxW(hwnd, message, "警告", 0x30 | 0x40000)  # MB_ICONWARNING | MB_SETFOREGROUND

    def stop_monitor(self):
        """停止监控"""
        self.monitoring = False
        print("监控已停止")

    def quit_app(self):
        """退出程序"""
        if messagebox.askokcancel("确认退出", "确定要退出程序吗？"):
            self.stop_monitor()
            # 恢复原始的stdout
            sys.stdout = self.original_stdout
            self.root.quit()

    def show_settings(self):
        """显示设置对话框"""
        SettingsDialog(self.root)

    def run(self):
        """运行程序"""
        self.root.mainloop()

if __name__ == "__main__":
    app = MonitorApp()
    app.run() 