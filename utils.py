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
    """主动清理内存"""
    # 存储监控前的内存使用情况
    try:
        process = psutil.Process()
        before_memory = process.memory_info().rss
        
        # 执行清理
        gc.collect()
        
        # 清理后的内存使用情况
        after_memory = process.memory_info().rss
        saved = before_memory - after_memory
        
        if saved > 0:
            print(f"内存清理完成: 释放了 {format_bytes(saved)} 内存")
        else:
            print("内存清理完成")
            
        return saved
    except Exception as e:
        print(f"清理内存时出错: {str(e)}")
        gc.collect()  # 仍然尝试清理
        print("已清理内存")
        return 0

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