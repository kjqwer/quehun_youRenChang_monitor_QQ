# 监控设置
MONITOR_SETTINGS = {'window_title': '立直荣断幺九', 'scan_interval': 1.0, 'confidence_threshold': 0.8, 'memory_cleanup_interval': 30, 'max_log_lines': 500, 'use_background_capture': False, 'memory_threshold': 1500, 'auto_reset_enabled': True}

# OCR设置
OCR_SETTINGS = {'use_angle_cls': False, 'lang': 'ch', 'show_log': False, 'use_gpu': False, 'enable_mkldnn': True, 'cls_model_dir': None, 'rec_char_dict_path': None}

# 自义定规则设置
RULES = {'number_patterns': ['(?<!\\d)\\d{5}(?!\\d)', '\\d{6}(?!\\d)'], 'custom_patterns': [], 'keywords': ['等车', '车车', '约吗'], 'exclude_patterns': ['\\d+\\s*[=＝]\\s*\\d+', '^\\d+[=＝]', '[=＝]\\d+$']}

CROP_AREA_FILE = 'last_crop_area.txt'