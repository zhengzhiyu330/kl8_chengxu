@echo off
chcp 65001 >nul
REM 快乐 8 智能预测 API 服务器启动脚本 (Windows)

echo ==========================================
echo 快乐 8 智能预测 API 服务器
echo ==========================================
echo.

REM 检查是否安装了必要的依赖
echo 检查依赖...
python -c "import flask, flask_cors, requests, bs4" 2>nul
if %errorlevel% neq 0 (
    echo 未安装依赖，正在安装...
    pip install -r requirements_api.txt
    if %errorlevel% neq 0 (
        echo 依赖安装失败，请手动运行: pip install -r requirements_api.txt
        pause
        exit /b 1
    )
)

echo ✓ 依赖检查通过
echo.

REM 创建缓存目录
if not exist cache mkdir cache
echo ✓ 缓存目录已准备
echo.

REM 启动服务器
echo 启动 API 服务器...
echo 访问地址: http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo.
python kl8_api_server.py

pause
