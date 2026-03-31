#!/bin/bash
# ============================================
# 服务器一键部署脚本（Ubuntu 22.04）
# 使用方法: chmod +x deploy.sh && sudo ./deploy.sh
# ============================================

set -e

# ==================== 配置区（按需修改）====================
DOMAIN="api.zhstpbf.cn"       # 替换为你的域名
APP_DIR="/opt/kl8-api"            # 应用部署目录
VENV_DIR="/opt/kl8-api/venv"      # Python虚拟环境目录
LOG_DIR="/var/log/kl8-api"        # 日志目录
# ==========================================================

echo "=========================================="
echo "  KL8 API 生产环境部署脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[→]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# ==================== 第1步：系统更新 ====================
print_info "第1步：更新系统软件包..."
apt-get update -y && apt-get upgrade -y
print_step "系统更新完成"
echo ""

# ==================== 第2步：安装系统依赖 ====================
print_info "第2步：安装系统依赖..."
apt-get install -y \
    python3 python3-pip python3-venv \
    nginx \
    certbot python3-certbot-nginx \
    supervisor \
    git curl wget

print_step "系统依赖安装完成"
echo ""

# ==================== 第3步：创建目录结构 ====================
print_info "第3步：创建目录结构..."
mkdir -p ${APP_DIR}
mkdir -p ${APP_DIR}/cache
mkdir -p ${APP_DIR}/logs
mkdir -p ${LOG_DIR}
chown -R www-data:www-data ${APP_DIR}
chown -R www-data:www-data ${LOG_DIR}
print_step "目录创建完成"
echo ""

# ==================== 第4步：创建Python虚拟环境 ====================
print_info "第4步：创建Python虚拟环境..."
python3 -m venv ${VENV_DIR}
${VENV_DIR}/bin/pip install --upgrade pip
print_step "虚拟环境创建完成"
echo ""

# ==================== 第5步：安装Python依赖 ====================
print_info "第5步：安装Python依赖..."
${VENV_DIR}/bin/pip install \
    flask==3.0.0 \
    flask-cors==4.0.0 \
    requests==2.31.0 \
    beautifulsoup4==4.12.2 \
    gunicorn==21.2.0 \
    gevent==23.9.1

print_step "Python依赖安装完成"
echo ""

# ==================== 第6步：复制应用代码 ====================
print_info "第6步：复制应用代码..."
# 提示用户手动复制或使用 git
echo ""
echo "请将 kl8_api_server.py 和 requirements_api.txt 复制到 ${APP_DIR}/"
echo "例如："
echo "  scp kl8_api_server.py root@your-server:${APP_DIR}/"
echo "  scp requirements_api.txt root@your-server:${APP_DIR}/"
echo ""
read -p "代码已复制完成？(y/n): " confirm
if [ "$confirm" != "y" ]; then
    print_error "请先复制代码，然后重新运行此脚本"
    exit 1
fi
print_step "应用代码就绪"
echo ""

# ==================== 第7步：部署Gunicorn配置 ====================
print_info "第7步：部署Gunicorn配置..."
if [ -f "deploy/gunicorn.conf.py" ]; then
    cp deploy/gunicorn.conf.py ${APP_DIR}/gunicorn.conf.py
fi
chown www-data:www-data ${APP_DIR}/gunicorn.conf.py
print_step "Gunicorn配置完成"
echo ""

# ==================== 第8步：部署Systemd服务 ====================
print_info "第8步：部署Systemd服务..."
if [ -f "deploy/kl8-api.service" ]; then
    cp deploy/kl8-api.service /etc/systemd/system/
fi
systemctl daemon-reload
systemctl enable kl8-api
print_step "Systemd服务配置完成"
echo ""

# ==================== 第9步：部署Nginx配置 ====================
print_info "第9步：部署Nginx配置..."
if [ -f "deploy/nginx.conf" ]; then
    # 替换域名
    sed "s/api.zhstpbf.cn/${DOMAIN}/g" deploy/nginx.conf > /etc/nginx/sites-available/kl8-api
    ln -sf /etc/nginx/sites-available/kl8-api /etc/nginx/sites-enabled/
    # 删除默认配置
    rm -f /etc/nginx/sites-enabled/default
fi
print_step "Nginx配置完成"
echo ""

# ==================== 第10步：测试并启动服务 ====================
print_info "第10步：启动服务..."

# 测试Nginx配置
nginx -t
if [ $? -ne 0 ]; then
    print_error "Nginx配置测试失败！"
    exit 1
fi
print_step "Nginx配置测试通过"

# 启动API服务
systemctl start kl8-api
systemctl status kl8-api --no-pager
if [ $? -ne 0 ]; then
    print_error "API服务启动失败！请检查日志: journalctl -u kl8-api -f"
    exit 1
fi
print_step "API服务启动成功"

# 重启Nginx
systemctl restart nginx
systemctl status nginx --no-pager
if [ $? -ne 0 ]; then
    print_error "Nginx启动失败！"
    exit 1
fi
print_step "Nginx启动成功"
echo ""

# ==================== 第11步：配置SSL证书 ====================
print_info "第11步：配置SSL证书..."
echo ""
echo "请确保域名 ${DOMAIN} 已解析到本服务器IP"
read -p "域名已解析？准备申请SSL证书？(y/n): " ssl_confirm
if [ "$ssl_confirm" = "y" ]; then
    certbot --nginx -d ${DOMAIN} --non-interactive --agree-tos -m admin@${DOMAIN}
    if [ $? -eq 0 ]; then
        print_step "SSL证书配置成功"
    else
        print_error "SSL证书配置失败，请手动运行: certbot --nginx -d ${DOMAIN}"
    fi
fi
echo ""

# ==================== 完成 ====================
echo "=========================================="
echo -e "${GREEN}  部署完成！${NC}"
echo "=========================================="
echo ""
echo "API地址: https://${DOMAIN}"
echo "健康检查: https://${DOMAIN}/api/health"
echo "数据更新: https://${DOMAIN}/api/prediction/generate"
echo ""
echo "常用命令："
echo "  查看API状态:  systemctl status kl8-api"
echo "  查看API日志:  journalctl -u kl8-api -f"
echo "  重启API服务:  systemctl restart kl8-api"
echo "  查看Nginx日志: tail -f /var/log/nginx/kl8-api.access.log"
echo "  重启Nginx:   systemctl restart nginx"
echo ""
print_info "下一步："
echo "  1. 在微信小程序后台配置服务器域名: ${DOMAIN}"
echo "  2. 修改前端 config.js 的 IS_PRODUCTION = true"
echo "  3. 重新编译并上传小程序代码"
echo ""
