"""
工具模块，包含通用的辅助类和函数
"""
import sys
import tkinter as tk
import gc
import psutil

class Logger:
    """日志记录器，重定向输出到文本控件"""
    def __init__(self, text_widget):
        self.terminal = sys.stdout
        self.text_widget = text_widget
        self.max_lines = 500  # 默认最大行数，会被配置覆盖

    def write(self, message):
        try:
            if self.terminal:
                self.terminal.write(message)
            if self.text_widget:
                # 限制日志框中的行数
                lines = self.text_widget.get('1.0', tk.END).count('\n')
                if lines > self.max_lines:
                    # 删除前半部分的日志
                    self.text_widget.delete('1.0', f'{lines//2}.0')
                
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

def format_bytes(bytes_value):
    """将字节数格式化为易读的字符串"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024:
            return f"{bytes_value:.2f}{unit}"
        bytes_value /= 1024
    return f"{bytes_value:.2f}PB"

def clean_memory():
    """清理内存"""
    print("执行内存清理...")
    
    # 强制Python垃圾回收
    for _ in range(3):
        gc.collect()
    
    # 尝试清理numpy缓存
    try:
        import numpy as np
        np.clear_cache()
    except:
        pass
    
    # 尝试清理paddle缓存
    try:
        import paddle
        paddle.device.cuda.empty_cache()
        if hasattr(paddle, 'fluid') and hasattr(paddle.fluid, 'core') and hasattr(paddle.fluid.core, 'garbage_collect_memory'):
            paddle.fluid.core.garbage_collect_memory()
    except:
        pass
    
    # 尝试请求操作系统回收内存
    try:
        import ctypes
        if sys.platform == 'win32':
            # Windows平台
            ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, -1)
        else:
            # Linux/Unix平台
            import resource
            resource.setrlimit(resource.RLIMIT_AS, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
    except:
        pass
    
    # 输出清理后内存
    try:
        info = get_system_info()
        if info:
            print(f"清理后内存占用: {format_bytes(info['process_memory'])}")
    except:
        pass
    
    print("内存清理完成")

def get_system_info():
    """获取系统资源信息"""
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        process = psutil.Process()
        process_memory = process.memory_info().rss
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used': memory.used,
            'memory_total': memory.total,
            'memory_available': memory.available,
            'process_memory': process_memory
        }
    except Exception as e:
        print(f"获取系统信息失败: {str(e)}")
        return None 