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

其实核心依赖就这几个，也可以直接安装：
```bash
pip install paddlepaddle
pip install "paddleocr>=2.0.1"
pip install pillow
pip install opencv-python
pip install pywin32
pip install psutil
```

如果安装过程中遇到问题，可以尝试先安装这些核心包，程序也能正常运行。其他依赖包会在安装这些核心包时自动安装。

## 使用方法

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

# 安装打包工具
pip install PyInstaller

# 打包命令
python -m PyInstaller --name "车牌监控" --add-data "config.py;." --add-data "quehun.ico;." --add-data "utils.py;." --add-data "gui;gui" --add-data "monitor;monitor" --add-data "ocr;ocr" --add-data ".venv\Lib\site-packages\paddle\libs\*.dll;paddle\libs" --add-data ".venv\Lib\site-packages\paddleocr;paddleocr" --hidden-import paddleocr --hidden-import PIL --hidden-import cv2 --hidden-import win32gui --hidden-import win32ui --hidden-import win32con --hidden-import numpy --hidden-import psutil --collect-all paddleocr --collect-all paddle --noconsole --icon=quehun.ico main.py
```


1. 运行打包后的程序
- 打包完成后，在 `dist/车牌监控` 目录下找到 `车牌监控.exe`
- 双击运行即可

2. 下载我提供打包好的程序（包有点大是因为包含了模型文件）
-  度盘:链接：https://pan.baidu.com/s/1qg5VtNSs7giQkyKBdLcXuw?pwd=sdxl 
-  提取码：sdxl 

## 使用说明

1. 选择监控窗口
   - 点击"选择监控窗口"按钮
   - 从列表中选择要监控的窗口
   - 用鼠标框选要监控的区域

   ![选择窗口](运行图片/选择窗口.png)
   ![框选区域](运行图片/框选区域.png)

2. 开始监控
   - 点击"开始监控"按钮
   - 程序会自动识别区域内的文字
   - 发现目标内容时会弹窗提醒

   ![主界面](运行图片/主界面.png)
   ![运行中](运行图片/运行中.png)

3. 设置选项
   - 点击"设置"按钮可以：
     - 调整扫描间隔
     - 设置OCR置信度
     - 管理关键词列表

   ![设置界面](运行图片/设置界面.png)
   ![设置界面2](运行图片/设置界面2.png)
   ![设置界面3](运行图片/设置界面3.png)

4. 停止监控
   - 点击"停止监控"按钮
   - 或直接关闭程序

5. 最终效果
   ![最终效果](运行图片/最终效果.png)
   ![最终效果2](运行图片/最终效果2.png)

## 配置文件说明

`config.py` 包含以下配置项：
- MONITOR_SETTINGS：监控设置（窗口标题、扫描间隔、置信度阈值）
- OCR_SETTINGS：OCR引擎设置
- KEYWORDS：关键词列表

## 注意事项

- 被监控的窗口不能最小化，但可以被其他窗口遮挡
- 首次运行时需要下载OCR模型文件
- 建议使用虚拟环境运行程序
- gpu设置支持需要修改环境重新打包（改为安装paddlepaddle-gpu）

## 依赖项目

- PaddleOCR
- OpenCV
- PyWin32
- Tkinter
- NumPy
- Pillow
- psutil

## License

MIT License

最后，本人雀魂名 筱诗 id 47739304 欢迎加好友一起打牌
