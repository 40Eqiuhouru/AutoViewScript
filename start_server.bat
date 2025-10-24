@echo off
REM 启动AutoViewScript服务器脚本

REM 设置项目目录
cd /d D:\pyCharmProject\AutoViewScript

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 启动服务器
python server_down.py

REM 暂停以查看输出
pause
