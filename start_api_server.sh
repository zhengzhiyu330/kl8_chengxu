#!/bin/bash

# 快乐 8 智能预测 API 服务器启动脚本

echo "=========================================="
echo "快乐 8 智能预测 API 服务器"
echo "=========================================="
echo ""

# 检查是否安装了必要的依赖
echo "检查依赖..."
python3 -c "import flask, flask_cors, requests, bs4" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "未安装依赖，正在安装..."
    pip3 install -r requirements_api.txt
    if [ $? -ne 0 ]; then
        echo "依赖安装失败，请手动运行: pip3 install -r requirements_api.txt"
        exit 1
    fi
fi

echo "✓ 依赖检查通过"
echo ""

# 创建缓存目录
mkdir -p cache
echo "✓ 缓存目录已准备"
echo ""

# 启动服务器
echo "启动 API 服务器..."
echo "访问地址: http://localhost:8000"
echo "按 Ctrl+C 停止服务器"
echo ""
python3 kl8_api_server.py
