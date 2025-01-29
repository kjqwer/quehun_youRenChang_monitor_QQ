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
        r'\b\d{5}\b',  # 精确匹配5位数字
        r'\b\d{6}\b',  # 精确匹配6位数字
        r'(?<![a-zA-Z\u4e00-\u9fff])\d{5}(?![a-zA-Z\u4e00-\u9fff=])',  # 匹配前后不是字母和汉字的5位数字
        r'(?<![a-zA-Z\u4e00-\u9fff])\d{6}(?![a-zA-Z\u4e00-\u9fff=])',  # 匹配前后不是字母和汉字的6位数字
    ],
    'custom_patterns': [
        # 自定义的正则表达式列表
    ],
    'keywords': [
        # 关键词列表
    ],
    'exclude_patterns': [
        r'\d+[=＝]+\d+',  # 排除等式
        r'[a-zA-Z\u4e00-\u9fff]\d+[a-zA-Z\u4e00-\u9fff]',  # 排除被字母或汉字完全包围的数字
    ]
}

# 关键词列表
KEYWORDS = ['等车', '车车', '约吗']

CROP_AREA_FILE = 'last_crop_area.txt'