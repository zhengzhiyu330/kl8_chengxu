#!/bin/bash
# ============================================
# 宝塔面板服务器部署 KL8 API（不安装系统 Nginx，避免与面板冲突）
# 适用：阿里云等预装「宝塔 Linux 面板」的镜像
# 用法：
#   1. 将项目上传到 APP_DIR（或通过 git clone 到该目录）
#   2. chmod +x deploy/deploy_baota.sh && sudo ./deploy/deploy_baota.sh
# 公网 IP 示例（仅 DNS 解析用，勿写进代码）：在用户域名控制台将 A 记录指向服务器公网 IP
# ============================================

set -e

# 宝塔常见站点根目录；可按需在面板「网站」里自定义
APP_DIR="${APP_DIR:-/www/wwwroot/kl8-api}"
VENV_DIR="${APP_DIR}/venv"

echo "=========================================="
echo "  KL8 API — 宝塔面板环境部署"
echo "  应用目录: ${APP_DIR}"
echo "=========================================="
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() { echo -e "${GREEN}[✓]${NC} $1"; }
print_info() { echo -e "${YELLOW}[→]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }

if [ "$(id -u)" -ne 0 ]; then
    print_error "请使用 root 执行：sudo ./deploy/deploy_baota.sh"
    exit 1
fi

# 宝塔常用运行用户为 www；部分系统为 www-data
if id -u www &>/dev/null; then
    RUN_USER=www
    RUN_GROUP=www
elif id -u www-data &>/dev/null; then
    RUN_USER=www-data
    RUN_GROUP=www-data
else
    print_error "未找到 www 或 www-data 用户，请手动指定 RUN_USER"
    exit 1
fi
print_info "进程运行用户: ${RUN_USER}:${RUN_GROUP}"

print_info "安装 Python 环境（若已安装会跳过）..."
if command -v apt-get &>/dev/null; then
    apt-get update -y
    apt-get install -y python3 python3-pip python3-venv curl
elif command -v yum &>/dev/null; then
    yum install -y python3 python3-pip curl || true
else
    print_info "未检测到 apt/yum，请自行确保已安装 python3、pip、venv"
fi
print_step "系统依赖检查完成"

if [ ! -d "${APP_DIR}" ]; then
    mkdir -p "${APP_DIR}"
fi
mkdir -p "${APP_DIR}/cache" "${APP_DIR}/logs"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ ! -f "${PROJECT_ROOT}/kl8_api_server.py" ]; then
    print_error "未找到 ${PROJECT_ROOT}/kl8_api_server.py，请从项目根目录执行或调整路径"
    exit 1
fi

print_info "同步应用与部署文件到 ${APP_DIR} ..."
cp -f "${PROJECT_ROOT}/kl8_api_server.py" "${APP_DIR}/"
if [ -f "${PROJECT_ROOT}/requirements_api.txt" ]; then
    cp -f "${PROJECT_ROOT}/requirements_api.txt" "${APP_DIR}/"
fi
cp -f "${SCRIPT_DIR}/gunicorn.conf.py" "${APP_DIR}/gunicorn.conf.py"
chown -R "${RUN_USER}:${RUN_GROUP}" "${APP_DIR}"
print_step "文件已同步"

print_info "创建虚拟环境并安装依赖..."
if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
fi
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install \
    flask==3.0.0 \
    flask-cors==4.0.0 \
    requests==2.31.0 \
    beautifulsoup4==4.12.2 \
    gunicorn==21.2.0 \
    gevent==23.9.1
print_step "Python 依赖安装完成"

print_info "写入 systemd 服务 kl8-api ..."
SERVICE_FILE="/etc/systemd/system/kl8-api.service"
cat >"${SERVICE_FILE}" <<EOF
[Unit]
Description=KL8 Data Analysis API Server (Baota)
After=network.target

[Service]
Type=simple
User=${RUN_USER}
Group=${RUN_GROUP}
WorkingDirectory=${APP_DIR}
Environment="PATH=${VENV_DIR}/bin"
ExecStart=${VENV_DIR}/bin/gunicorn -c gunicorn.conf.py kl8_api_server:app
ExecReload=/bin/kill -s HUP \$MAINPID
ExecStop=/bin/kill -s TERM \$MAINPID
Restart=always
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable kl8-api
systemctl restart kl8-api
sleep 1
if systemctl is-active --quiet kl8-api; then
    print_step "kl8-api 服务已启动"
else
    print_error "kl8-api 启动失败，请查看: journalctl -u kl8-api -n 50 --no-pager"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  部署完成（后端已监听 127.0.0.1:8000）${NC}"
echo "=========================================="
echo ""
print_info "请在阿里云安全组放行：TCP 80、443（宝塔面板端口如 8888 按需放行）"
echo ""
print_info "宝塔面板中配置网站（HTTPS 在面板里申请）："
echo "  1. 网站 → 添加站点 → 填写你的域名（需已做 DNS A 记录指向本机公网 IP）"
echo "  2. 网站 → 设置 → 反向代理 → 目标 URL: http://127.0.0.1:8000"
echo "  3. 网站 → SSL → Let's Encrypt 申请证书并强制 HTTPS"
echo ""
print_info "本机自检: curl -s http://127.0.0.1:8000/api/health | head"
echo ""
