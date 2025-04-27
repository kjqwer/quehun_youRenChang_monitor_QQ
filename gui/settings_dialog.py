import tkinter as tk
from tkinter import ttk, messagebox
import re

class SettingsDialog:
    """设置对话框类，用于配置程序的各项参数"""
    
    def __init__(self, parent, monitor_settings, ocr_settings, rules):
        """初始化设置对话框
        
        Args:
            parent: 父窗口
            monitor_settings: 监控设置字典
            ocr_settings: OCR设置字典
            rules: 规则设置字典
        """
        self.window = tk.Toplevel(parent)
        self.window.title("设置")
        self.window.geometry("600x650")  # 窗口大小
        
        # 保存原始设置
        self.monitor_settings = monitor_settings
        self.ocr_settings = ocr_settings
        self.rules = rules
        
        # 创建notebook用于分页
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建各个设置页面
        self._create_basic_settings_page()
        self._create_keywords_page()
        self._create_rules_page()
        
        # 保存按钮
        ttk.Button(self.window, text="保存设置", 
                  command=self.save_settings).pack(pady=10)
    
    def _create_basic_settings_page(self):
        """创建基本设置页面"""
        self.basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.basic_frame, text="基本设置")
        
        # 扫描间隔设置
        ttk.Label(self.basic_frame, text="扫描间隔(秒):").pack(pady=5)
        self.scan_interval = ttk.Entry(self.basic_frame)
        self.scan_interval.insert(0, str(self.monitor_settings['scan_interval']))
        self.scan_interval.pack(pady=5)
        
        # 置信度阈值设置
        ttk.Label(self.basic_frame, text="OCR置信度阈值(0-1):").pack(pady=5)
        self.confidence = ttk.Entry(self.basic_frame)
        self.confidence.insert(0, str(self.monitor_settings['confidence_threshold']))
        self.confidence.pack(pady=5)
        
        # 性能设置
        ttk.Label(self.basic_frame, text="内存清理间隔(次数):").pack(pady=5)
        self.memory_cleanup_interval = ttk.Entry(self.basic_frame)
        self.memory_cleanup_interval.insert(0, str(self.monitor_settings.get('memory_cleanup_interval', 30)))
        self.memory_cleanup_interval.pack(pady=5)
        
        ttk.Label(self.basic_frame, text="日志最大行数:").pack(pady=5)
        self.max_log_lines = ttk.Entry(self.basic_frame)
        self.max_log_lines.insert(0, str(self.monitor_settings.get('max_log_lines', 500)))
        self.max_log_lines.pack(pady=5)
        
        # GPU设置
        self.use_gpu_var = tk.BooleanVar(value=self.ocr_settings.get('use_gpu', False))
        ttk.Checkbutton(self.basic_frame, text="使用GPU加速(需要支持CUDA)", 
                       variable=self.use_gpu_var).pack(pady=5)
        
        self.enable_mkldnn_var = tk.BooleanVar(value=self.ocr_settings.get('enable_mkldnn', True))
        ttk.Checkbutton(self.basic_frame, text="启用MKL加速", 
                       variable=self.enable_mkldnn_var).pack(pady=5)
    
    def _create_keywords_page(self):
        """创建关键词设置页面"""
        self.keywords_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.keywords_frame, text="关键词设置")
        
        # 关键词列表
        self.keywords_list = tk.Listbox(self.keywords_frame, height=10)
        self.keywords_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加现有关键词
        for keyword in self.rules['keywords']:
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
    
    def _create_rules_page(self):
        """创建规则设置页面"""
        self.rules_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.rules_frame, text="规则设置")
        
        # 数字模式设置
        ttk.Label(self.rules_frame, text="数字模式:").pack(pady=5)
        self.number_patterns_list = tk.Listbox(self.rules_frame, height=5)
        self.number_patterns_list.pack(fill=tk.X, padx=5)
        for pattern in self.rules['number_patterns']:
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
        for pattern in self.rules['custom_patterns']:
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
        for pattern in self.rules['exclude_patterns']:
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
    
    def add_keyword(self):
        """添加关键词"""
        keyword = self.keyword_entry.get().strip()
        if keyword and keyword not in self.keywords_list.get(0, tk.END):
            self.keywords_list.insert(tk.END, keyword)
            self.keyword_entry.delete(0, tk.END)
    
    def delete_keyword(self):
        """删除选中的关键词"""
        selection = self.keywords_list.curselection()
        if selection:
            self.keywords_list.delete(selection)
    
    def add_pattern(self, pattern_type):
        """添加模式
        
        Args:
            pattern_type: 模式类型，'number', 'custom' 或 'exclude'
        """
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
        """删除选中的模式
        
        Args:
            pattern_type: 模式类型，'number', 'custom' 或 'exclude'
        """
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
        """保存设置"""
        try:
            # 更新MONITOR_SETTINGS
            self.monitor_settings['scan_interval'] = float(self.scan_interval.get())
            self.monitor_settings['confidence_threshold'] = float(self.confidence.get())
            self.monitor_settings['memory_cleanup_interval'] = int(self.memory_cleanup_interval.get())
            self.monitor_settings['max_log_lines'] = int(self.max_log_lines.get())
            
            # 更新OCR_SETTINGS
            self.ocr_settings['use_gpu'] = self.use_gpu_var.get()
            self.ocr_settings['enable_mkldnn'] = self.enable_mkldnn_var.get()
            
            # 更新RULES
            self.rules['number_patterns'] = list(self.number_patterns_list.get(0, tk.END))
            self.rules['custom_patterns'] = list(self.custom_patterns_list.get(0, tk.END))
            self.rules['exclude_patterns'] = list(self.exclude_patterns_list.get(0, tk.END))
            self.rules['keywords'] = list(self.keywords_list.get(0, tk.END))
            
            # 保存到配置文件
            config_content = f"""# 监控设置
MONITOR_SETTINGS = {repr(self.monitor_settings)}

# OCR设置
OCR_SETTINGS = {repr(self.ocr_settings)}

# 规则设置
RULES = {repr(self.rules)}

# 保存裁剪区域的文件
CROP_AREA_FILE = 'last_crop_area.txt'"""
            
            with open('config.py', 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            messagebox.showinfo("成功", "设置已保存")
            
            # 询问是否需要重启监控
            if messagebox.askyesno("提示", "部分设置需要重启监控才能生效，是否立即重启监控？"):
                parent_app = self.window.master.app
                if hasattr(parent_app, 'monitoring') and parent_app.monitoring:
                    parent_app.stop_monitor()
                    if hasattr(parent_app, 'ocr_processor'):
                        parent_app.ocr_processor.release()
                    parent_app.start_monitor()
            
            self.window.destroy()
            
        except ValueError as e:
            messagebox.showerror("错误", "请输入有效的数值") 