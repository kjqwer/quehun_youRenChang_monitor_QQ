# 监控设置
MONITOR_SETTINGS = {
    'window_title': '',
    'scan_interval': 1.0,
    'confidence_threshold': 0.8
}


# OCR设置
OCR_SETTINGS = {
    'use_angle_cls': False,
    'lang': "ch",
    'show_log': False
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