# 快速开始

## 1. 安装依赖

```bash
pip3 install -r requirements_api.txt
```

或直接运行启动脚本（会在缺依赖时尝试安装）：

```bash
./start_api_server.sh
```

## 2. 启动服务器

```bash
./start_api_server.sh
```

或：

```bash
python3 kl8_api_server.py
```

开发模式默认监听 **`http://0.0.0.0:8000`**（与 `kl8_api_server.py` 末尾一致）。

## 3. 测试 API

在另一个终端：

```bash
python3 test_api.py
```

## 4. 在小程序中调用

生产环境请使用 HTTPS 域名（如 `https://api.zhstpbf.cn`），勿写死内网 IP。本地调试可指向开发机：

```javascript
wx.request({
  url: 'http://127.0.0.1:8000/api/prediction/latest',
  // ...
});
```

## 常见问题

### Q: 如何让外部设备访问？

`kl8_api_server.py` 已使用 `host='0.0.0.0'`。放行本机 **8000** 端口防火墙；生产环境建议 **Nginx 反代**（见 `deploy/`）。

### Q: 数据多久更新一次？

默认每小时自动更新；也可 `POST /api/prediction/generate` 触发。

### Q: 缓存文件在哪里？

`cache/api_cache.json`（首次运行会自动创建 `cache/`）。

### Q: 如何修改更新频率？

在 `kl8_api_server.py` 的 `start_background_scheduler()` 中修改 `time.sleep(3600)`（秒）。

### Q: 如何部署到服务器？

宝塔：见 `deploy/deploy_baota.sh`；通用清单：`deploy/DEPLOY_CHECKLIST.md`；操作备忘：`deploy/SERVER_UPDATE_OPERATIONS.md`、`deploy/SERVER_ENV.md`。

```bash
pip install gunicorn gevent
gunicorn -c deploy/gunicorn.conf.py kl8_api_server:app
```

## 更多信息

完整接口说明：[API_README.md](API_README.md)
