import re

class TextAnalyzer:
    """文本分析类，处理文本匹配和识别"""
    
    def __init__(self, rules):
        """初始化文本分析器
        
        Args:
            rules: 包含匹配规则的字典，需包含keywords, number_patterns, custom_patterns, exclude_patterns
        """
        self.rules = rules
        self.last_printed_text = None
        self.alerted_messages = set()  # 已经触发警报的消息集合
    
    def update_rules(self, rules):
        """更新匹配规则"""
        self.rules = rules
    
    def analyze_text(self, text):
        """分析OCR识别出的文本，检查是否匹配任何规则
        
        Args:
            text: OCR识别的文本
            
        Returns:
            匹配到的消息，如果没有匹配则返回None
        """
        if not text:
            return None
            
        # 只在文本变化时打印
        if text != self.last_printed_text:
            print("\n寻找车车中:")
            print(text)
            self.last_printed_text = text
            
        lines = text.splitlines()
        
        for line in lines:
            # 检查数字模式
            for pattern in self.rules['number_patterns']:
                matches = re.finditer(pattern, line)
                for match in matches:
                    number = match.group()
                    # 检查这个数字是否被排除规则排除
                    should_exclude = False
                    for exclude_pattern in self.rules['exclude_patterns']:
                        if re.search(exclude_pattern, number):
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        message = f"发现车牌: {number}"
                        if message not in self.alerted_messages:
                            return message
            
            # 检查自定义正则表达式
            for pattern in self.rules.get('custom_patterns', []):
                if not pattern:  # 跳过空模式
                    continue
                try:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        matched_text = match.group()
                        message = f"匹配正则'{pattern}': {matched_text}"
                        if message not in self.alerted_messages:
                            return message
                except re.error:
                    print(f"无效的正则表达式: {pattern}")
            
            # 检查关键词
            for keyword in self.rules['keywords']:
                if keyword in line:
                    message = f"发现关键词: {line}"
                    if message not in self.alerted_messages:
                        return message
                        
        return None
    
    def add_alerted_message(self, message):
        """添加已触发警报的消息"""
        self.alerted_messages.add(message)
    
    def clear_alerted_messages(self):
        """清空已触发警报的消息"""
        self.alerted_messages.clear()
    
    def get_alerted_messages(self):
        """获取已触发警报的消息列表"""
        return self.alerted_messages 