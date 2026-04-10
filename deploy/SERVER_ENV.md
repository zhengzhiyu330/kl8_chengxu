# 本仓库约定：生产环境与服务器信息

> **单一事实来源**：后续对话里若出现新的域名、路径或服务名，请同步改本文件（并可按同一事实去改 `SERVER_UPDATE_OPERATIONS.md`、脚本注释等）。

## 机器与面板

- **云厂商**：阿里云
- **面板**：宝塔（典型站点根：`/www/wwwroot/`）
- **示例主机名**（可随实例变）：`iZ2zecgotu59r1rtx192xqZ`

## 目录结构（与当前约定一致）

| 用途 | 路径 | 说明 |
|------|------|------|
| **Git 源码** | `/www/wwwroot/kl8_chengxu` | 有 `.git`，在此 `git pull`。 |
| **线上运行目录** | `/www/wwwroot/kl8-api` | **无 Git**；放 `venv`、`kl8_api_server.py`、`gunicorn.conf.py` 等，**systemd / Gunicorn 工作目录通常指向这里**。 |
| **站点目录（面板）** | `/www/wwwroot/api.zhstpbf.cn` | 宝塔站点根之一，用于 **Nginx / 证书 / 反代**（具体以面板配置为准）。 |
| **同级其它** | `/www/wwwroot/default` 等 | 面板默认站点，与 API 代码可无关。 |

## 域名与访问

- **API 对外域名**：`https://api.zhstpbf.cn`（健康检查：`GET /api/health`）
- 历史上联调曾用公网 IP + HTTPS，**以域名与 Nginx 配置为准**。

## systemd 服务（约定名）

- 服务名：**`kl8-api`**（以服务器上 `systemctl list-units | grep kl8` 为准）
- 常用：**`systemctl reload kl8-api`**（平滑重载 Gunicorn worker）、**`systemctl restart kl8-api`**（整服务重启）
- 日志：**`journalctl -u kl8-api -n 80 --no-pager`**

## 发布流程（源码目录 ≠ 运行目录）

当前结构下 **`kl8-api` 不是 Git 仓库**，典型步骤为：

1. 在 **`/www/wwwroot/kl8_chengxu`**：`git pull`
2. 将需生效文件同步到 **`/www/wwwroot/kl8-api`**（至少 **`kl8_api_server.py`**；依赖变更时还要动 `requirements_api.txt` 并在该目录 venv 里 `pip install`）
3. **`systemctl reload kl8-api`**（日常）；依赖或 unit 变更时多用 **`restart`**

同步示例（在服务器上、按实际改文件名）：

```bash
cp /www/wwwroot/kl8_chengxu/kl8_api_server.py /www/wwwroot/kl8-api/kl8_api_server.py
cp /www/wwwroot/kl8_chengxu/requirements_api.txt /www/wwwroot/kl8-api/requirements_api.txt
# 然后视情况：cd /www/wwwroot/kl8-api && ./venv/bin/pip install -r requirements_api.txt
# 再：systemctl restart kl8-api   # 只改 py 时常用 reload 即可，见 SERVER_UPDATE_OPERATIONS.md
```

若你改为 **直接在 `kl8-api` 里 `git clone` 单目录部署**，可删掉「两步目录」段落，仅保留一步 `git pull`——以你机器为准更新本文件。

**初次装机用哪个脚本：** 宝塔见 **`deploy/README.md`** 中的 **`deploy_baota.sh`**；不要用 **`deploy.ubuntu-standalone.sh`**（会与面板 Nginx 冲突）。

## 用户常用身份

- 维护时多为 **`root`** SSH（示例提示符：`[root@... kl8_chengxu]#`）

---

*最后更新：与对话中确认的 `/www/wwwroot` 布局同步。域名 `api.zhstpbf.cn`。*
