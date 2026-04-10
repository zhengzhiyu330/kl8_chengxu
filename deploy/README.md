# 部署脚本说明（选一个，不要混用）

| 脚本 | 环境 | 说明 |
|------|------|------|
| **`deploy_baota.sh`** | **宝塔面板**（阿里云等常见） | **推荐**你当前方案：不装系统级 Nginx，避免和面板冲突；应用目录默认 `/www/wwwroot/kl8-api`；站点反代、SSL 在宝塔里配。 |
| **`deploy.ubuntu-standalone.sh`** | **裸机 Ubuntu**（无面板） | 用 `apt` 装 Nginx、Certbot，写 `/etc/nginx/sites-*`，目录默认 `/opt/kl8-api`；**不要在已装宝塔的机器上跑**。 |

日常发版、reload 等操作见 **`SERVER_UPDATE_OPERATIONS.md`**，路径约定见 **`SERVER_ENV.md`**。
