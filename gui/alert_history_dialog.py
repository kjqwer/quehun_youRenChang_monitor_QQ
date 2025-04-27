import tkinter as tk
from tkinter import ttk, messagebox

class AlertHistoryDialog:
    """警报历史对话框类，管理已经触发警报的消息"""
    
    def __init__(self, parent, text_analyzer):
        """初始化警报历史对话框
        
        Args:
            parent: 父窗口
            text_analyzer: 文本分析器实例，包含警报消息集合
        """
        self.parent = parent
        self.text_analyzer = text_analyzer
        
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
        
        # 加载现有记录
        self.load_history(self.text_analyzer.get_alerted_messages())
        
    def load_history(self, history_set):
        """加载历史记录到列表框
        
        Args:
            history_set: 包含历史消息的集合
        """
        self.history_list.delete(0, tk.END)
        for item in sorted(history_set):
            self.history_list.insert(tk.END, item)
    
    def add_history(self):
        """添加新的历史记录"""
        new_item = self.new_entry.get().strip()
        if new_item and new_item not in self.history_list.get(0, tk.END):
            self.history_list.insert(tk.END, new_item)
            self.new_entry.delete(0, tk.END)
    
    def delete_selected(self):
        """删除选中的记录"""
        selection = self.history_list.curselection()
        if selection:
            self.history_list.delete(selection)
    
    def clear_all(self):
        """清空所有记录"""
        if messagebox.askyesno("确认", "确定要清空所有记录吗？"):
            self.history_list.delete(0, tk.END)
    
    def save_changes(self):
        """保存更改到文本分析器"""
        new_history = set(self.history_list.get(0, tk.END))
        
        # 清空文本分析器中的记录并添加新记录
        self.text_analyzer.clear_alerted_messages()
        for message in new_history:
            self.text_analyzer.add_alerted_message(message)
            
        messagebox.showinfo("成功", "更改已保存")
        self.window.destroy() 