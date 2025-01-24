

```markdown
# 雀魂群友人场监控工具

一个基于 PaddleOCR 的监控聊天窗口的工具，可以实时监控指定窗口区域并识别字符，制作原因是群友友人场车牌总是赶不上，写个脚本懒人化，不用一直盯着窗口。

## 功能特点

- 实时监控指定窗口区域
- 自动识别雀魂友人场车牌号码（5位数字），识别过的不会重复识别
- 支持自定义关键词监控
- 可视化区域选择
- 支持设置扫描间隔和OCR置信度
- 弹窗提醒功能

## 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### 方式一：脚本启动

1. 配置监控窗口
```bash
# 运行配置工具
config_window.bat
```

2. 启动监控
```bash
# 运行主程序
yrc.bat
```

### 方式二：图形界面启动

#### 直接运行
```bash
# 激活虚拟环境
.venv\Scripts\activate

# 运行启动器
python launcher.py
```

#### 打包使用
1. 打包程序
```bash
# 激活虚拟环境
.venv\Scripts\activate

# 打包命令
python -m PyInstaller --name "车牌监控" --add-data "config.py;." --add-data "quehun.ico;." --add-data ".venv\Lib\site-packages\paddle\libs\*.dll;paddle\libs" --add-data ".venv\Lib\site-packages\paddleocr;paddleocr" --hidden-import paddleocr --hidden-import PIL --hidden-import cv2 --hidden-import win32gui --hidden-import win32ui --hidden-import win32con --hidden-import numpy --collect-all paddleocr --collect-all paddle --noconsole --icon=quehun.ico launcher.py
```

2. 运行打包后的程序
- 打包完成后，在 `dist/车牌监控` 目录下找到 `车牌监控.exe`
- 双击运行即可

## 使用说明

1. 选择监控窗口
   - 点击"选择监控窗口"按钮
   - 从列表中选择要监控的窗口
   - 用鼠标框选要监控的区域

2. 开始监控
   - 点击"开始监控"按钮
   - 程序会自动识别区域内的文字
   - 发现目标内容时会弹窗提醒

3. 设置选项
   - 点击"设置"按钮可以：
     - 调整扫描间隔
     - 设置OCR置信度
     - 管理关键词列表

4. 停止监控
   - 点击"停止监控"按钮
   - 或直接关闭程序

## 配置文件说明

`config.py` 包含以下配置项：
- MONITOR_SETTINGS：监控设置（窗口标题、扫描间隔、置信度阈值）
- OCR_SETTINGS：OCR引擎设置
- KEYWORDS：关键词列表

## 注意事项

- 被监控的窗口不能最小化，但可以被其他窗口遮挡
- 首次运行时需要下载OCR模型文件
- 建议使用虚拟环境运行程序

## 依赖项目

- PaddleOCR
- OpenCV
- PyWin32
- Tkinter
- NumPy
- Pillow

## License

MIT License

```

这个 README 包含了：
1. 项目简介和功能特点
2. 安装说明
3. 两种启动方式的详细说明
4. 使用指南
5. 配置文件说明
6. 注意事项
7. 依赖项目列表

你可能还需要：
1. 创建 requirements.txt 文件
2. 添加 LICENSE 文件
3. 可以考虑添加一些截图来展示程序界面

需要这些额外的文件我也可以帮你准备。
