@echo off
REM 激活虚拟环境
call .venv\Scripts\activate

REM 运行配置工具
python config_tool.py

REM 保持窗口打开
pause 