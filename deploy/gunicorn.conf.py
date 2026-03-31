# ============================================
# Gunicorn WSGI 配置文件（与 kl8_api_server.py 同目录部署）
# ============================================

import os

# 项目根目录：生产环境 gunicorn.conf.py 与 kl8_api_server.py 同目录；
# 本地若使用 deploy/gunicorn.conf.py，则取上一级目录。
_CONF_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(_CONF_DIR) == "deploy":
    _candidate = os.path.normpath(os.path.join(_CONF_DIR, ".."))
    if os.path.isfile(os.path.join(_candidate, "kl8_api_server.py")):
        _ROOT = _candidate
    else:
        _ROOT = _CONF_DIR
else:
    _ROOT = _CONF_DIR
_LOG_DIR = os.path.join(_ROOT, "logs")
os.makedirs(_LOG_DIR, exist_ok=True)

# 绑定地址（本地，由 Nginx / 宝塔 反向代理）
bind = '127.0.0.1:8000'

# Worker 进程数：本应用使用进程内内存缓存，多 worker 会数据不一致，生产环境建议固定为 1。
workers = 1

# Worker 类（使用 gevent 提升并发）
worker_class = 'gevent'

# 每个 Worker 的最大并发请求数
worker_connections = 1000

# 超时时间（秒）
timeout = 120

# 保持连接
keepalive = 5

# 最大请求数后重启 Worker（防止内存泄漏）
max_requests = 5000
max_requests_jitter = 500

# 日志（写在项目目录内，避免 www-data/www 无权限写 /var/log）
accesslog = os.path.join(_LOG_DIR, 'access.log')
errorlog = os.path.join(_LOG_DIR, 'error.log')
loglevel = 'info'

# PID 文件
pidfile = os.path.join(_ROOT, 'gunicorn.pid')

# 守护进程
daemon = False

# 预加载应用（与 gevent worker 搭配时关闭更稳妥，且本应用仅 1 worker）
preload_app = False


def post_worker_init(worker):
    """Gunicorn 不会执行 if __name__ == '__main__'，在此处完成加载缓存与定时更新。"""
    from kl8_api_server import bootstrap_worker

    bootstrap_worker()
