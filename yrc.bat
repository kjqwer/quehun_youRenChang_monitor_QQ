@echo off
REM 激活虚拟环境
call .venv\Scripts\activate

REM 运行 main.py
python main.py

REM 保持窗口打开
pause