@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   自动化数据可视化脚本 - 开始执行
echo ========================================
echo.

echo [%time%] 步骤1: 切换到虚拟环境目录
cd /d "D:\AutoViewScript\.venv\Scripts"
if %errorlevel% neq 0 (
    echo 错误: 无法切换到虚拟环境目录
    pause
    exit /b 1
)

echo [%time%] 步骤2: 激活虚拟环境
call activate
if %errorlevel% neq 0 (
    echo 错误: 虚拟环境激活失败
    pause
    exit /b 1
)

echo [%time%] 步骤3: 执行contents.py数据分析脚本
python "D:\AutoViewScript\contents.py"
set content_result=%errorlevel%
if !content_result! neq 0 (
    echo 警告: contents.py执行返回错误代码 !content_result!
)

echo [%time%] 等待6秒...
timeout /t 4 /nobreak >nul

echo [%time%] 步骤4: 执行comments.py数据分析脚本
python "D:\AutoViewScript\comments.py"
set comment_result=%errorlevel%
if !comment_result! neq 0 (
    echo 警告: comments.py执行返回错误代码 !comment_result!
)

echo.
echo ========================================
echo   脚本执行完成
echo   生成的文件保存在桌面contents和comments文件夹中
echo ========================================
echo.

if !content_result! equ 0 (
    echo ✓ contents.py 执行成功
) else (
    echo ✗ contents.py 执行异常
)

if !comment_result! equ 0 (
    echo ✓ comments.py 执行成功
) else (
    echo ✗ comments.py 执行异常
)

echo.
pause