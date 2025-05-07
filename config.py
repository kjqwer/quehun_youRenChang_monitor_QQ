# 监控设置
MONITOR_SETTINGS = {
    'window_title': '小小诗',
    'scan_interval': 1.0,
    'confidence_threshold': 0.8,
    'memory_cleanup_interval': 30,  # 每30次循环清理一次内存
    'max_log_lines': 500,  # 日志最大行数
    'use_background_capture': True  # 使用背景捕获模式（无需窗口置顶）
}



# OCR设置
OCR_SETTINGS = {
    'use_angle_cls': False,
    'lang': "ch",
    'show_log': False,
    'use_gpu': False,  # 不使用GPU，减少内存占用
    'enable_mkldnn': True,  # 启用MKL加速
    'cls_model_dir': None,  # 不加载分类模型，减少内存占用
    'rec_char_dict_path': None  # 使用默认字典
}

# 自义定规则设置
RULES = {
    'number_patterns': [
        r'(?<!\d)\d{5}(?!\d)',  # 匹配独立的5位数字（前后不能是数字）
        r'\d{6}(?!\d)',  # 匹配6位数字
    ],
    'custom_patterns': [
        # 用户自定义的正则表达式列表
    ],
    'keywords': [
        # 关键词列表
        '等车', '车车', '约吗'
    ],
    'exclude_patterns': [
        r'\d+\s*[=＝]\s*\d+',  # 只排除紧密相连的等式
        r'^\d+[=＝]',  # 排除以等号开始的表达式
        r'[=＝]\d+$'   # 排除以等号结束的表达式
    ]
}

CROP_AREA_FILE = 'last_crop_area.txt'