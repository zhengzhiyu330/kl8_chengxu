# 快速开始

## 1. 安装依赖

```bash
# macOS/Linux
pip3 install -r requirements_api.txt

# Windows
pip install -r requirements_api.txt
```

或者直接运行启动脚本，会自动安装依赖：

```bash
# macOS/Linux
./start_api_server.sh

# Windows
start_api_server.bat
```

## 2. 启动服务器

```bash
# macOS/Linux
./start_api_server.sh

# Windows
start_api_server.bat

# 或者直接使用 Python
python kl8_api_server.py
```

服务器将在 `http://localhost:5000` 启动

## 3. 测试 API

在另一个终端运行测试脚本：

```bash
python test_api.py
```

## 4. 在小程序中调用

```javascript
// 获取最新预测
wx.request({
  url: 'http://localhost:5000/api/prediction/latest',
  success(res) {
    console.log(res.data);
  }
});
```

## 常见问题

### Q: 如何让外部设备访问？
修改 `kl8_api_server.py` 最后一行，将 `host='0.0.0.0'` 保持不变即可。确保防火墙允许 5000 端口访问。

### Q: 数据多久更新一次？
默认每小时自动更新一次。也可以手动调用 `POST /api/prediction/generate` 触发更新。

### Q: 缓存文件在哪里？
缓存文件位于 `cache/api_cache.json`。

### Q: 如何修改更新频率？
在 `kl8_api_server.py` 的 `start_background_scheduler()` 内部（`scheduled_update` 闭包）修改 `time.sleep(3600)` 的参数（单位：秒）。

### Q: 支持部署到服务器吗？
支持。生产环境请使用仓库内 `deploy/gunicorn.conf.py`（`workers=1`、反代 8000 端口），宝塔机器请用 `deploy/deploy_baota.sh`。

```bash
# 仅供本地快速验证；生产请用 systemd + Nginx/宝塔反代
pip install gunicorn gevent
gunicorn -c deploy/gunicorn.conf.py kl8_api_server:app
```

## 更多信息

查看完整文档：[API_README.md](API_README.md)
