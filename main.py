import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import ctypes
import time
import gc
import traceback
import win32gui

# 添加资源路径处理函数
def resource_path(relative_path):
    """获取资源的绝对路径，适用于开发环境和PyInstaller打包后的环境
    
    说明：
    1. PyInstaller打包后，程序运行在临时目录中，需要使用此函数处理资源路径
    2. 如果找到_MEIPASS属性，说明是打包后的环境，使用_MEIPASS作为基础路径
    3. 否则使用当前目录作为基础路径
    """
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        # 如果不是通过PyInstaller打包，返回当前目录
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# 获取应用程序目录 - 这是关键，确保配置文件使用正确的路径
# 打包后，sys.argv[0]是可执行文件的完整路径，这样可以得到它所在的目录
APP_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
# 配置文件路径 - 存放在应用程序目录下，而不是临时目录
CONFIG_FILE = os.path.join(APP_DIR, 'config.py')
# 裁剪区域文件路径 - 同样存放在应用程序目录下
CROP_AREA_FILE_PATH = os.path.join(APP_DIR, 'last_crop_area.txt')

# 尝试导入配置，如果失败则创建默认配置
try:
    # 导入配置
    from config import MONITOR_SETTINGS, OCR_SETTINGS, RULES, CROP_AREA_FILE
except ImportError:
    print("配置文件不存在，将创建默认配置")
    # 默认监控设置
    MONITOR_SETTINGS = {
        'window_title': '',
        'scan_interval': 1.0,
        'confidence_threshold': 0.8,
        'memory_cleanup_interval': 30,
        'max_log_lines': 500,
        'use_background_capture': True,
        'memory_threshold': 1500,
        'auto_reset_enabled': True
    }
    
    # 默认OCR设置
    OCR_SETTINGS = {
        'use_angle_cls': False,
        'lang': 'ch',
        'show_log': False,
        'use_gpu': False,
        'enable_mkldnn': True,
        'cls_model_dir': None,
        'rec_char_dict_path': None
    }
    
    # 默认规则设置
    RULES = {
        'number_patterns': ['(?<!\\d)\\d{5}(?!\\d)', '\\d{6}(?!\\d)'],
        'custom_patterns': [],
        'keywords': ['等车', '车车', '约吗'],
        'exclude_patterns': ['\\d+\\s*[=＝]\\s*\\d+', '^\\d+[=＝]', '[=＝]\\d+$']
    }
    
    CROP_AREA_FILE = 'last_crop_area.txt'
    
    # 创建配置文件
    try:
        config_content = f"""# 监控设置
MONITOR_SETTINGS = {repr(MONITOR_SETTINGS)}

# OCR设置
OCR_SETTINGS = {repr(OCR_SETTINGS)}

# 自义定规则设置
RULES = {repr(RULES)}

CROP_AREA_FILE = 'last_crop_area.txt'"""
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print(f"已创建默认配置文件: {CONFIG_FILE}")
    except Exception as e:
        print(f"创建配置文件失败: {str(e)}")

# 导入自定义模块
from utils import Logger, clean_memory, get_system_info, format_bytes
from monitor.window_capture import WindowCapture
from monitor.text_analyzer import TextAnalyzer
from ocr.ocr_processor import OCRProcessor
from gui.settings_dialog import SettingsDialog
from gui.alert_history_dialog import AlertHistoryDialog

class MonitorApp:
    """主应用类，整合所有功能模块"""
    
    def __init__(self):
        """初始化主应用"""
        # 保存原始的stdout
        self.original_stdout = sys.stdout
        
        # 捕获全局异常
        sys.excepthook = self.handle_exception
        
        # 创建主窗口
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
        # 设置日志最大行数
        sys.stdout.max_lines = MONITOR_SETTINGS.get('max_log_lines', 500)
        
        # 创建按钮框架 - 分成两行
        self.button_frame1 = ttk.Frame(self.main_frame)
        self.button_frame1.pack(fill=tk.X, pady=(5, 2))
        
        self.button_frame2 = ttk.Frame(self.main_frame)
        self.button_frame2.pack(fill=tk.X, pady=(2, 5))
        
        # 第一行按钮 - 主要操作按钮
        ttk.Button(self.button_frame1, text="选择监控窗口", command=self.select_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame1, text="切换窗口置顶", command=self.toggle_window_topmost).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame1, text="开始监控", command=self.start_monitor).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame1, text="停止监控", command=self.stop_monitor).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame1, text="设置", command=self.show_settings).pack(side=tk.LEFT, padx=5)
        
        # 第二行按钮 - 辅助功能按钮
        ttk.Button(self.button_frame2, text="识别记录", command=self.show_alert_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame2, text="切换捕获模式", command=self.toggle_capture_mode).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame2, text="清理内存", command=self.clean_memory).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame2, text="系统信息", command=self.show_system_info).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame2, text="退出程序", command=self.quit_app).pack(side=tk.RIGHT, padx=5)
        
        # 初始化模块
        self.window_capture = WindowCapture()
        self.window_capture.crop_area_file = CROP_AREA_FILE_PATH  # 使用绝对路径
        # 设置捕获模式
        self.window_capture.use_background_capture = MONITOR_SETTINGS.get('use_background_capture', True)
        self.text_analyzer = TextAnalyzer(RULES)
        self.ocr_processor = OCRProcessor(
            OCR_SETTINGS,
            MONITOR_SETTINGS['confidence_threshold'],
            MONITOR_SETTINGS.get('memory_threshold', 1800),  # 内存阈值，默认1800MB
            MONITOR_SETTINGS.get('auto_reset_enabled', True)  # 是否启用自动内存重置
        )
        
        # 初始化变量
        self.monitoring = False
        self.loop_counter = 0
        self.memory_cleanup_interval = MONITOR_SETTINGS.get('memory_cleanup_interval', 30)
        
        # 开始定期更新系统信息
        self.start_system_monitor()
        
        print("车牌监控程序已启动")
        print("-" * 30)
        self.print_system_info()
        print("-" * 30)
        self.print_config_info()
        print("-" * 30)
        print("请选择要监控的窗口...")
        
        # 尝试自动选择上次的监控区域
        self.try_auto_load_settings()
    
    def try_auto_load_settings(self):
        """尝试自动加载上次的设置"""
        if 'window_title' in MONITOR_SETTINGS and MONITOR_SETTINGS['window_title']:
            print(f"尝试查找上次的窗口: {MONITOR_SETTINGS['window_title']}")
            hwnd = self.window_capture.find_window_by_title(MONITOR_SETTINGS['window_title'])
            if hwnd:
                self.window_capture.selected_window = hwnd
                print(f"已找到上次的窗口: {MONITOR_SETTINGS['window_title']}")
                
                # 尝试加载裁剪区域
                if self.window_capture.load_crop_area():
                    print("已加载监控窗口和区域，可以开始监控")
                else:
                    print("未找到上次的监控区域，请重新选择")
    
    def print_system_info(self):
        """打印系统资源信息"""
        system_info = get_system_info()
        if system_info:
            print("系统资源信息:")
            print(f"  CPU使用率: {system_info['cpu_percent']}%")
            print(f"  内存使用: {system_info['memory_percent']}% ({format_bytes(system_info['memory_used'])}/{format_bytes(system_info['memory_total'])})")
            print(f"  可用内存: {format_bytes(system_info['memory_available'])}")
            print(f"  程序内存占用: {format_bytes(system_info['process_memory'])}")
    
    def show_system_info(self):
        """显示系统信息对话框"""
        system_info = get_system_info()
        if system_info:
            info = f"""系统资源信息:
CPU使用率: {system_info['cpu_percent']}%
内存使用: {system_info['memory_percent']}% ({format_bytes(system_info['memory_used'])}/{format_bytes(system_info['memory_total'])})
可用内存: {format_bytes(system_info['memory_available'])}
程序内存占用: {format_bytes(system_info['process_memory'])}

性能设置:
扫描间隔: {MONITOR_SETTINGS['scan_interval']}秒
内存清理间隔: 每{self.memory_cleanup_interval}次扫描
使用GPU: {'是' if OCR_SETTINGS.get('use_gpu', False) else '否'}
使用MKL加速: {'是' if OCR_SETTINGS.get('enable_mkldnn', True) else '否'}
"""
            messagebox.showinfo("系统信息", info)
        else:
            messagebox.showerror("错误", "获取系统信息失败")
    
    def start_system_monitor(self):
        """开始定期监控系统资源"""
        # 每60秒更新一次系统资源信息
        try:
            system_info = get_system_info()
            if system_info:
                # 检查内存使用是否超过90%，如果是则自动清理
                if system_info['memory_percent'] > 90:
                    print("系统内存使用超过90%，正在自动清理...")
                    self.clean_memory()
                    
                # 检查程序内存占用是否超过阈值
                memory_threshold_bytes = MONITOR_SETTINGS.get('memory_threshold', 1800) * 1024 * 1024
                if system_info['process_memory'] > memory_threshold_bytes:
                    print(f"程序内存占用较高: {format_bytes(system_info['process_memory'])}，正在自动清理...")
                    self.clean_memory()
                    
        except Exception as e:
            print(f"监控系统资源时出错: {str(e)}")
        finally:
            # 继续定期监控
            if hasattr(self, 'root') and self.root:  # 确保root仍然存在
                self.root.after(60000, self.start_system_monitor)  # 60秒后再次调用
    
    def clean_memory(self):
        """主动清理内存"""
        print("正在清理内存...")
        # 停止OCR引擎
        if hasattr(self, 'ocr_processor') and self.ocr_processor:
            self.ocr_processor.release()
        
        # 强制运行多次垃圾回收
        for _ in range(3):
            gc.collect()
        
        # 获取清理后的内存信息
        system_info = get_system_info()
        if system_info:
            print(f"清理完成，当前内存占用: {format_bytes(system_info['process_memory'])}")
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """处理未捕获的异常"""
        # 打印到控制台
        print("发生未捕获的异常:")
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        # 显示错误对话框
        if hasattr(self, 'root') and self.root:
            messagebox.showerror("程序错误", f"发生异常: {exc_value}\n\n请检查日志或重启程序。")
    
    def select_window(self):
        """选择要监控的窗口"""
        # 获取所有可见窗口
        windows = self.window_capture.get_window_list()
        
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
                window_title = windows[index][0]
                self.window_capture.selected_window = windows[index][1]
                print(f"已选择窗口: {window_title}")
                
                # 显示窗口置顶状态
                is_topmost = self.window_capture.is_window_topmost(self.window_capture.selected_window)
                print(f"窗口置顶状态: {'是' if is_topmost else '否'}")
                
                # 保存窗口标题到配置
                MONITOR_SETTINGS['window_title'] = window_title
                try:
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        config_content = f.read()
                    
                    # 替换窗口标题
                    import re
                    pattern = r"'window_title': '.*?'"
                    replacement = f"'window_title': '{window_title}'"
                    if re.search(pattern, config_content):
                        config_content = re.sub(pattern, replacement, config_content)
                    else:
                        # 如果没找到，在第一行后添加
                        lines = config_content.split('\n')
                        for i, line in enumerate(lines):
                            if "MONITOR_SETTINGS" in line and "{" in line:
                                # 在下一行添加窗口标题
                                indent = line.index('{') + 4  # 缩进4个空格
                                lines.insert(i+1, ' ' * indent + f"'window_title': '{window_title}',")
                                config_content = '\n'.join(lines)
                                break
                    
                    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                        f.write(config_content)
                        
                    print(f"已保存窗口标题到配置文件: {CONFIG_FILE}")
                except Exception as e:
                    print(f"保存窗口标题失败: {str(e)}")
                
                select_window.destroy()
                self.window_capture.select_monitor_area()
                
        ttk.Button(select_window, text="确认", command=confirm_selection).pack(pady=5)

    def start_monitor(self):
        """开始监控"""
        if not self.window_capture.selected_window or not self.window_capture.crop_area:
            messagebox.showwarning("警告", "请先选择监控窗口和区域")
            return
            
        if self.monitoring:
            return
            
        self.monitoring = True
        
        # 先清理内存再初始化OCR引擎
        self.clean_memory()
        
        # 初始化OCR引擎
        if not self.ocr_processor.initialize():
            self.monitoring = False
            return
        
        print("开始监控...")
        self.loop_counter = 0  # 重置计数器
        self.monitor_loop()

    def monitor_loop(self):
        """监控循环"""
        if not self.monitoring:
            return
            
        try:
            # 计数器增加，定期清理一次内存
            self.loop_counter += 1
            if self.loop_counter >= self.memory_cleanup_interval:
                # 检查内存占用
                system_info = get_system_info()
                if system_info and system_info['process_memory'] > MONITOR_SETTINGS.get('memory_threshold', 1800) * 1024 * 1024:
                    print(f"程序内存占用较高: {format_bytes(system_info['process_memory'])}，正在自动清理...")
                    self.clean_memory()
                    # 重新初始化OCR引擎
                    self.ocr_processor.initialize()
                else:
                    # 仅做一般垃圾回收
                    gc.collect()
                
                self.loop_counter = 0
                print("已自动清理内存")
                
            # 捕获并处理窗口图像
            cropped_image = self.window_capture.get_cropped_image()
            if cropped_image is None:
                raise Exception("无法获取窗口图像")
            
            # 识别文字
            text = self.ocr_processor.recognize_text(cropped_image)
            
            # 释放图像资源
            del cropped_image
            
            # 分析文本，检查是否有匹配项
            if text:
                message = self.text_analyzer.analyze_text(text)
                if message:
                    self.show_alert(message)
                    self.text_analyzer.add_alerted_message(message)
            
        except Exception as e:
            print(f"监控过程出错: {str(e)}")
            
        finally:
            # 确保资源释放
            if 'cropped_image' in locals():
                del cropped_image
            
            # 确保即使发生异常也会继续循环
            if self.monitoring:
                # 使用更长的间隔让系统有时间释放资源
                self.root.after(int(MONITOR_SETTINGS['scan_interval'] * 1000), self.monitor_loop)

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
        # 释放OCR资源
        self.ocr_processor.release()
        # 主动清理内存
        self.clean_memory()

    def quit_app(self):
        """退出程序"""
        if messagebox.askokcancel("确认退出", "确定要退出程序吗？"):
            self.stop_monitor()
            # 恢复原始的stdout
            sys.stdout = self.original_stdout
            # 清理内存
            gc.collect()
            self.root.quit()

    def show_settings(self):
        """显示设置对话框"""
        settings_dialog = SettingsDialog(self.root, MONITOR_SETTINGS, OCR_SETTINGS, RULES, CONFIG_FILE)
        # 等待设置对话框关闭
        self.root.wait_window(settings_dialog.window)
        # 更新捕获模式
        self.window_capture.use_background_capture = MONITOR_SETTINGS.get('use_background_capture', True)
        # 更新日志最大行数
        sys.stdout.max_lines = MONITOR_SETTINGS.get('max_log_lines', 500)
        # 更新OCR处理器设置
        self.ocr_processor.update_settings(
            memory_threshold=MONITOR_SETTINGS.get('memory_threshold', 1800),
            auto_reset_enabled=MONITOR_SETTINGS.get('auto_reset_enabled', True)
        )
        print(f"设置已更新，内存阈值: {MONITOR_SETTINGS.get('memory_threshold', 1800)}MB, 自动重置: {'开启' if MONITOR_SETTINGS.get('auto_reset_enabled', True) else '关闭'}")

    def show_alert_history(self):
        """显示已识别记录对话框"""
        AlertHistoryDialog(self.root, self.text_analyzer)

    def toggle_capture_mode(self):
        """切换捕获模式"""
        if self.monitoring:
            messagebox.showwarning("警告", "请先停止监控再切换捕获模式")
            return
            
        mode = self.window_capture.toggle_capture_mode()
        mode_text = "背景模式（无需窗口置顶）" if mode else "前台模式（需要窗口置顶）"
        
        # 检查窗口置顶状态
        window_topmost_warning = ""
        if self.window_capture.selected_window and win32gui.IsWindow(self.window_capture.selected_window):
            is_topmost = self.window_capture.is_window_topmost(self.window_capture.selected_window)
            if not mode and not is_topmost:
                window_topmost_warning = "\n\n注意：当前选择的窗口未置顶！在前台模式下，未置顶的窗口可能无法正确捕获。建议点击\"切换窗口置顶\"按钮来置顶监控窗口。"
            elif mode and is_topmost:
                window_topmost_warning = "\n\n提示：您已切换到背景模式，但当前窗口仍然处于置顶状态。在背景模式下，您可以取消窗口置顶，不会影响监控效果。"
        
        info = f"""已切换到{mode_text}

背景模式说明：
- 可以监控被覆盖或后台的窗口
- 使用多种技术尝试获取窗口实际内容
- 适用于大多数应用程序

前台模式说明：
- 需要监控窗口处于最前面（置顶）
- 稳定性更好，但使用不太方便
- 适用于所有类型的窗口

如果背景模式不能正确捕获某些应用，请尝试切换到前台模式。{window_topmost_warning}"""
        
        messagebox.showinfo("切换捕获模式", info)
        
        # 更新配置信息
        self.print_config_info()

    def toggle_window_topmost(self):
        """切换监控窗口的置顶状态"""
        if not self.window_capture.selected_window:
            messagebox.showwarning("警告", "请先选择监控窗口")
            return
        
        try:
            # 获取当前窗口标题
            window_title = win32gui.GetWindowText(self.window_capture.selected_window)
            
            # 检查窗口是否存在
            if not win32gui.IsWindow(self.window_capture.selected_window):
                messagebox.showerror("错误", "所选窗口已关闭或不可用")
                return
                
            # 切换窗口置顶状态
            is_topmost = self.window_capture.toggle_window_topmost(self.window_capture.selected_window)
            
            # 显示结果
            status = "已置顶" if is_topmost else "已取消置顶"
            messagebox.showinfo("窗口置顶状态", f"窗口 \"{window_title}\" {status}")
            
            # 更新配置信息显示
            self.print_config_info()
            
        except Exception as e:
            messagebox.showerror("错误", f"切换窗口置顶状态失败: {str(e)}")

    def print_config_info(self):
        """打印配置信息"""
        print("当前配置:")
        print(f"  扫描间隔: {MONITOR_SETTINGS['scan_interval']}秒")
        print(f"  置信度阈值: {MONITOR_SETTINGS['confidence_threshold']}")
        print(f"  内存清理间隔: 每{MONITOR_SETTINGS.get('memory_cleanup_interval', 30)}次扫描")
        print(f"  使用GPU: {'是' if OCR_SETTINGS.get('use_gpu', False) else '否'}")
        print(f"  使用MKL加速: {'是' if OCR_SETTINGS.get('enable_mkldnn', True) else '否'}")
        print(f"  捕获模式: {'背景模式（无需窗口置顶）' if self.window_capture.use_background_capture else '前台模式（需要窗口置顶）'}")
        
        # 显示窗口置顶状态
        if self.window_capture.selected_window and win32gui.IsWindow(self.window_capture.selected_window):
            is_topmost = self.window_capture.is_window_topmost(self.window_capture.selected_window)
            window_title = win32gui.GetWindowText(self.window_capture.selected_window)
            print(f"  监控窗口: {window_title}")
            print(f"  窗口置顶: {'是' if is_topmost else '否'}")

    def run(self):
        """运行程序"""
        self.root.mainloop()

if __name__ == "__main__":
    app = MonitorApp()
    app.run() 