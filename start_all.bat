@echo off
REM 前后端一键启动脚本 (Windows)

echo ==========================================
echo 快乐 8 智能预测系统 - 前后端启动脚本
echo ==========================================

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%kl8_chengxu

REM 检查后端目录是否存在
if not exist "%BACKEND_DIR%" (
    echo 错误：找不到后端目录 %BACKEND_DIR%
    pause
    exit /b 1
)

REM 进入后端目录
cd /d "%BACKEND_DIR%"

REM 检查 Python 环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未找到 Python，请先安装 Python
    pause
    exit /b 1
)

REM 检查依赖是否已安装
echo.
echo 检查依赖...
python -c "import flask, flask_cors" 2>nul
if %errorlevel% neq 0 (
    echo 安装依赖包...
    pip install -r requirements_api.txt
)

echo.
echo ==========================================
echo 启动后端 API 服务器
echo 地址：http://localhost:8000
echo ==========================================
echo.

REM 启动后端服务器
python kl8_api_server.py

pause
