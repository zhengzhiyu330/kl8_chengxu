# 服务器更新代码后的常用操作说明

面向阿里云 + **宝塔**环境下的 KL8 API：systemd 服务名一般为 **`kl8-api`**（Gunicorn）。

**本机路径约定**见同目录 **`SERVER_ENV.md`**（源码目录与运行目录可能不同，请先读该文件）。

以下用本文已对齐的路径：

- 源码（有 Git）：**`/www/wwwroot/kl8_chengxu`**
- 运行（无 Git，含 venv）：**`/www/wwwroot/kl8-api`**

---

## 一、更新代码之后推荐顺序（日常只改 `kl8_api_server.py` 等）

在服务器 SSH 中依次执行：

| 步骤 | 命令 | 作用 |
|------|------|------|
| 1 | `cd /www/wwwroot/kl8_chengxu` | 进入 **Git 仓库**根目录。 |
| 2 | `git pull` | 拉取最新代码；**仅更新本目录**，不会自动改 `kl8-api`。 |
| 3 | `cp /www/wwwroot/kl8_chengxu/kl8_api_server.py /www/wwwroot/kl8-api/kl8_api_server.py` | 把主程序同步到 **Gunicorn 实际运行的目录**（路径按你文件名调整）。 |
| 4 | `systemctl reload kl8-api` | 向 Gunicorn **平滑重载**：新 worker 加载磁盘上的新 `.py`，尽量不打断正在处理的请求。**（宝塔 root 下一般可直接执行，无 `sudo` 亦可）** |

若你改为 **单目录 Git 部署**（直接在 `kl8-api` 里维护仓库），则省略步骤 3，仅在运行目录 `git pull` 后 **reload**——以 **`SERVER_ENV.md`** 为准。

此时 **一般不需要** `restart`；**一般不需要**因改 Python 而单独重载 Nginx（除非你改的是站点/Nginx 配置）。

---

## 二、`reload` 与 `restart` 的区别

| 命令 | 作用 | 适用场景 |
|------|------|----------|
| `systemctl reload kl8-api` | **重载**：`ExecReload` 对主进程发 **HUP**，Gunicorn **优雅换 worker**。 | **日常发版**：只替换了运行目录下的业务代码。 |
| `systemctl restart kl8-api` | **重启**：整服务停再起，连接会断。 | 改了 **systemd 单元**、**环境变量**、**Gunicorn 核心配置**；`reload` 异常；**`pip install` 后**建议 restart。 |

查看状态：

```bash
systemctl status kl8-api --no-pager
```

---

## 三、其它常用操作

| 操作 | 命令 | 作用 |
|------|------|------|
| 最近日志 | `journalctl -u kl8-api -n 80 --no-pager` | 排错。 |
| 跟踪日志 | `journalctl -u kl8-api -f` | 实时看日志。 |
| Nginx（改配置后） | `nginx -t && systemctl reload nginx` | 先测语法再平滑加载。 |
| 改 unit 文件 | `systemctl daemon-reload` 后 **`systemctl restart kl8-api`** | 让 systemd 识别新单元配置。 |
| 依赖更新 | 在 **`/www/wwwroot/kl8-api`** 下对 **venv** 执行 `pip install -r requirements_api.txt` | 装完后多 **`systemctl restart kl8-api`**。 |

---

## 四、为什么要 `reload` / `restart`

- `git pull` 与 **`cp` 到运行目录** 只改**磁盘文件**；已运行的进程不会自动重载 Python 模块。
- **`reload`**：用新 worker 跑新代码，适合常规发版。
- **`restart`**：进程全新拉起，最干净。

---

## 五、自检

```bash
curl -sS 'https://api.zhstpbf.cn/api/health'
```

返回 JSON 且含 `"status": "ok"` 即链路基本正常（域名以 **`SERVER_ENV.md`** 为准）。

---

## 六、服务名与路径不一致时

```bash
systemctl list-units --type=service | grep -i kl8
```

以实际单元名为准；路径以 **`SERVER_ENV.md`** 为单一事实来源并随环境更新。
