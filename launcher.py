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
        self.window.geometry("600x600")
        
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
        for keyword in RULES['keywords']:  # 从RULES中获取关键词
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
        
        # 规则设置页面
        self.rules_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.rules_frame, text="规则设置")
        
        # 数字模式设置
        ttk.Label(self.rules_frame, text="数字模式:").pack(pady=5)
        self.number_patterns_list = tk.Listbox(self.rules_frame, height=5)
        self.number_patterns_list.pack(fill=tk.X, padx=5)
        for pattern in RULES['number_patterns']:
            self.number_patterns_list.insert(tk.END, pattern)
            
        # 数字模式操作按钮
        self.number_pattern_frame = ttk.Frame(self.rules_frame)
        self.number_pattern_frame.pack(fill=tk.X, padx=5, pady=5)
        self.number_pattern_entry = ttk.Entry(self.number_pattern_frame)
        self.number_pattern_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(self.number_pattern_frame, text="添加", 
                  command=lambda: self.add_pattern('number')).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.number_pattern_frame, text="删除",
                  command=lambda: self.delete_pattern('number')).pack(side=tk.LEFT)
        
        # 自定义正则设置
        ttk.Label(self.rules_frame, text="自定义正则:").pack(pady=5)
        self.custom_patterns_list = tk.Listbox(self.rules_frame, height=5)
        self.custom_patterns_list.pack(fill=tk.X, padx=5)
        for pattern in RULES['custom_patterns']:
            self.custom_patterns_list.insert(tk.END, pattern)
            
        # 自定义正则操作按钮
        self.custom_pattern_frame = ttk.Frame(self.rules_frame)
        self.custom_pattern_frame.pack(fill=tk.X, padx=5, pady=5)
        self.custom_pattern_entry = ttk.Entry(self.custom_pattern_frame)
        self.custom_pattern_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(self.custom_pattern_frame, text="添加",
                  command=lambda: self.add_pattern('custom')).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.custom_pattern_frame, text="删除",
                  command=lambda: self.delete_pattern('custom')).pack(side=tk.LEFT)
        
        # 排除规则设置
        ttk.Label(self.rules_frame, text="排除规则:").pack(pady=5)
        self.exclude_patterns_list = tk.Listbox(self.rules_frame, height=5)
        self.exclude_patterns_list.pack(fill=tk.X, padx=5)
        for pattern in RULES['exclude_patterns']:
            self.exclude_patterns_list.insert(tk.END, pattern)
            
        # 排除规则操作按钮
        self.exclude_pattern_frame = ttk.Frame(self.rules_frame)
        self.exclude_pattern_frame.pack(fill=tk.X, padx=5, pady=5)
        self.exclude_pattern_entry = ttk.Entry(self.exclude_pattern_frame)
        self.exclude_pattern_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(self.exclude_pattern_frame, text="添加",
                  command=lambda: self.add_pattern('exclude')).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.exclude_pattern_frame, text="删除",
                  command=lambda: self.delete_pattern('exclude')).pack(side=tk.LEFT)
        
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
    
    def add_pattern(self, pattern_type):
        entry_map = {
            'number': self.number_pattern_entry,
            'custom': self.custom_pattern_entry,
            'exclude': self.exclude_pattern_entry
        }
        list_map = {
            'number': self.number_patterns_list,
            'custom': self.custom_patterns_list,
            'exclude': self.exclude_patterns_list
        }
        
        entry = entry_map[pattern_type]
        listbox = list_map[pattern_type]
        
        pattern = entry.get().strip()
        if pattern and pattern not in listbox.get(0, tk.END):
            try:
                # 测试正则表达式是否有效
                re.compile(pattern)
                listbox.insert(tk.END, pattern)
                entry.delete(0, tk.END)
            except re.error:
                messagebox.showerror("错误", "无效的正则表达式")

    def delete_pattern(self, pattern_type):
        list_map = {
            'number': self.number_patterns_list,
            'custom': self.custom_patterns_list,
            'exclude': self.exclude_patterns_list
        }
        listbox = list_map[pattern_type]
        selection = listbox.curselection()
        if selection:
            listbox.delete(selection)

    def save_settings(self):
        try:
            # 更新MONITOR_SETTINGS
            MONITOR_SETTINGS['scan_interval'] = float(self.scan_interval.get())
            MONITOR_SETTINGS['confidence_threshold'] = float(self.confidence.get())
            
            # 更新RULES
            global RULES
            RULES['number_patterns'] = list(self.number_patterns_list.get(0, tk.END))
            RULES['custom_patterns'] = list(self.custom_patterns_list.get(0, tk.END))
            RULES['exclude_patterns'] = list(self.exclude_patterns_list.get(0, tk.END))
            RULES['keywords'] = list(self.keywords_list.get(0, tk.END))
            
            # 保存到配置文件，注意去掉多余的缩进
            config_content = f"""# 监控设置
MONITOR_SETTINGS = {MONITOR_SETTINGS}

# OCR设置
OCR_SETTINGS = {OCR_SETTINGS}

# 规则设置
RULES = {RULES}

# 保存裁剪区域的文件
CROP_AREA_FILE = 'last_crop_area.txt'"""
            
            with open('config.py', 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            messagebox.showinfo("成功", "设置已保存")
            self.window.destroy()
            
        except ValueError as e:
            messagebox.showerror("错误", "请输入有效的数值")

class AlertHistoryDialog:
    def __init__(self, parent):
        self.parent = parent  # 保存父窗口引用
        self.window = tk.Toplevel(parent)
        self.window.title("已识别记录")
        self.window.geometry("500x400")
        
        # 创建列表框显示已识别内容
        self.history_frame = ttk.Frame(self.window)
        self.history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(self.history_frame, text="已识别内容列表:").pack(pady=5)
        self.history_list = tk.Listbox(self.history_frame, height=15)
        self.history_list.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.history_list)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_list.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.history_list.yview)
        
        # 添加操作按钮框架
        self.button_frame = ttk.Frame(self.window)
        self.button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加新记录输入框和按钮
        self.entry_frame = ttk.Frame(self.button_frame)
        self.entry_frame.pack(fill=tk.X, pady=5)
        self.new_entry = ttk.Entry(self.entry_frame)
        self.new_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(self.entry_frame, text="添加", 
                  command=self.add_history).pack(side=tk.RIGHT)
        
        # 删除和清空按钮
        ttk.Button(self.button_frame, text="删除选中", 
                  command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="清空所有", 
                  command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="保存", 
                  command=self.save_changes).pack(side=tk.RIGHT, padx=5)
        
        # 修改加载现有记录的方式
        self.load_history(self.parent.app.alerted_messages)  # 通过app访问alerted_messages
        
    def load_history(self, history_set):
        self.history_list.delete(0, tk.END)
        for item in sorted(history_set):
            self.history_list.insert(tk.END, item)
    
    def add_history(self):
        new_item = self.new_entry.get().strip()
        if new_item and new_item not in self.history_list.get(0, tk.END):
            self.history_list.insert(tk.END, new_item)
            self.new_entry.delete(0, tk.END)
    
    def delete_selected(self):
        selection = self.history_list.curselection()
        if selection:
            self.history_list.delete(selection)
    
    def clear_all(self):
        if messagebox.askyesno("确认", "确定要清空所有记录吗？"):
            self.history_list.delete(0, tk.END)
    
    def save_changes(self):
        new_history = set(self.history_list.get(0, tk.END))
        self.parent.app.alerted_messages = new_history  # 通过app保存更改
        messagebox.showinfo("成功", "更改已保存")
        self.window.destroy()

class MonitorApp:
    def __init__(self):
        # 保存原始的stdout
        self.original_stdout = sys.stdout
        
        self.root = tk.Tk()
        self.root.title("车牌监控程序")
        self.root.geometry("600x400")
        
        # 将app引用保存到root中
        self.root.app = self
        
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
        ttk.Button(self.button_frame, text="识别记录", command=self.show_alert_history).pack(side=tk.LEFT, padx=5)
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
            # print(f"正在检查行: '{line}'")  # 调试信息
            
            # 检查数字模式
            for pattern in RULES['number_patterns']:
                matches = re.finditer(pattern, line)
                for match in matches:
                    number = match.group()
                    # 检查这个数字是否被排除规则排除
                    should_exclude = False
                    for exclude_pattern in RULES['exclude_patterns']:
                        if re.search(exclude_pattern, number):
                            # print(f"  - 数字 '{number}' 被规则 '{exclude_pattern}' 排除")
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        # print(f"  + 找到匹配: '{number}'")
                        message = f"发现车牌: {number}"
                        if message not in self.alerted_messages:
                            self.show_alert(message)
                            self.alerted_messages.add(message)
                            return
            
            # 检查关键词
            for keyword in RULES['keywords']:
                if keyword in line:
                    # print(f"  + 找到关键词: '{keyword}'")  # 调试信息
                    message = f"发现关键词: {line}"
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

    def show_alert_history(self):
        """显示已识别记录对话框"""
        AlertHistoryDialog(self.root)

    def run(self):
        """运行程序"""
        self.root.mainloop()

if __name__ == "__main__":
    app = MonitorApp()
    app.run() 