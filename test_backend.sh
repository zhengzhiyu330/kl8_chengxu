#!/bin/bash

# 后端 API 测试脚本

echo "=========================================="
echo "测试后端 API 接口"
echo "=========================================="

BASE_URL="http://localhost:8000"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试函数
test_api() {
    local name=$1
    local url=$2

    echo ""
    echo "测试: $name"
    echo "URL: $url"
    
    response=$(curl -s -w "\n%{http_code}" "$url")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ 成功${NC} (HTTP $http_code)"
        echo "响应: $(echo $body | head -c 100)..."
    else
        echo -e "${RED}✗ 失败${NC} (HTTP $http_code)"
        echo "响应: $body"
    fi
}

# 测试健康检查
test_api "健康检查" "$BASE_URL/api/health"

# 测试获取期数列表
test_api "获取期数列表" "$BASE_URL/api/lottery/periods?limit=5"

# 测试获取最新预测
test_api "获取最新预测" "$BASE_URL/api/prediction/latest"

# 测试获取所有数据
test_api "获取所有数据" "$BASE_URL/api/all-data"

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""
echo "如果所有测试都显示绿色 ✓，说明后端 API 运行正常"
echo "如果有红色 ✗，请检查后端服务器是否正常运行"
echo ""
