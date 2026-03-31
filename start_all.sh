#!/bin/bash

# 前后端一键启动脚本

echo "=========================================="
echo "快乐 8 智能预测系统 - 前后端启动脚本"
echo "=========================================="

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/kl8_chengxu"

# 检查后端目录是否存在
if [ ! -d "$BACKEND_DIR" ]; then
    echo "错误：找不到后端目录 $BACKEND_DIR"
    exit 1
fi

# 进入后端目录
cd "$BACKEND_DIR"

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到 Python3，请先安装 Python"
    exit 1
fi

# 检查依赖是否已安装
echo ""
echo "检查依赖..."
if ! python3 -c "import flask, flask_cors" 2>/dev/null; then
    echo "安装依赖包..."
    pip3 install -r requirements_api.txt
fi

echo ""
echo "=========================================="
echo "启动后端 API 服务器"
echo "地址：http://localhost:8000"
echo "=========================================="
echo ""

# 启动后端服务器
python3 kl8_api_server.py
