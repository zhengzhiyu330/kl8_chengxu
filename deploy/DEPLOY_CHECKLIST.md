# ============================================
# 小程序部署检查清单
# ============================================

## 一、你需要准备的东西

### 1. 服务器（必选，方案任选其一）
| 方案 | 推荐 | 价格 | 说明 |
|------|------|------|------|
| 腾讯云轻量应用服务器 | ⭐⭐⭐⭐⭐ | ~50元/月 | 2核2G，国内访问快 |
| 阿里云ECS | ⭐⭐⭐⭐ | ~60元/月 | 稳定可靠 |
| 华为云ECS | ⭐⭐⭐⭐ | ~50元/月 | 性价比高 |

**服务器最低配置要求：**
- CPU: 1核
- 内存: 1GB
- 硬盘: 20GB
- 系统: Ubuntu 22.04 LTS
- 带宽: 1Mbps（推荐3Mbps）

### 2. 域名（必选）
| 项目 | 说明 |
|------|------|
| 域名 | 如 kl8.example.com |
| ICP备案 | 国内服务器必须备案 |
| SSL证书 | Let's Encrypt 免费自动签发 |

### 3. 微信小程序账号（已有）
| 项目 | 当前状态 |
|------|----------|
| AppID | wx335f6ff8fbd5a564 |
| 类目 | 需选择合适的服务类目 |
| 服务器域名 | 需配置 request 合法域名 |

---

## 二、部署步骤总览

```
阶段1: 服务器准备          ──→  购买服务器 + 域名 + 备案
阶段2: 后端API部署         ──→  服务器安装环境 + 部署代码 + 配置Nginx
阶段3: SSL证书配置         ──→  申请HTTPS证书
阶段4: 微信小程序配置       ──→  服务器域名 + 类目
阶段5: 前端代码适配         ──→  修改API地址 + 上传代码
阶段6: 测试上线            ──→  提交审核 + 发布上线
```

---

## 三、详细步骤

### 阶段1：服务器准备

#### 1.1 购买服务器
- 推荐腾讯云轻量应用服务器（Ubuntu 22.04）
- 记录服务器公网IP：`YOUR_SERVER_IP`

#### 1.2 购买域名
- 在阿里云/腾讯云购买域名
- 做A记录解析：`api.yourdomain.com` → `YOUR_SERVER_IP`

#### 1.3 ICP备案（国内服务器必须）
- 通过服务器提供商进行ICP备案
- 备案周期：7-20个工作日
- 未备案域名无法在国内服务器使用

### 阶段2：后端API部署

#### 2.1 连接服务器
```bash
ssh root@YOUR_SERVER_IP
```

#### 2.2 上传代码
```bash
# 在本地执行
cd /Users/luluzhenlan/PycharmProjects/KL8/kl8_chengxu
scp kl8_api_server.py root@YOUR_SERVER_IP:/opt/kl8-api/
scp requirements_api.txt root@YOUR_SERVER_IP:/opt/kl8-api/
scp -r deploy/ root@YOUR_SERVER_IP:/opt/kl8-api/
```

#### 2.3 一键部署
```bash
# 在服务器上执行
cd /opt/kl8-api
chmod +x deploy/deploy.sh
sudo ./deploy/deploy.sh
```

#### 2.4 手动部署（如果脚本失败）
```bash
# 安装依赖
apt update && apt install -y python3 python3-pip python3-venv nginx

# 创建虚拟环境
python3 -m venv /opt/kl8-api/venv
/opt/kl8-api/venv/bin/pip install -r requirements_production.txt

# 测试运行
cd /opt/kl8-api
/opt/kl8-api/venv/bin/python kl8_api_server.py

# 验证API（在本地执行）
curl http://YOUR_SERVER_IP:8000/api/health
```

### 阶段3：SSL证书配置

```bash
# 在服务器上执行
certbot --nginx -d api.yourdomain.com
```

验证HTTPS:
```bash
curl https://api.yourdomain.com/api/health
```

### 阶段4：微信小程序配置

#### 4.1 登录微信小程序后台
- 网址：https://mp.weixin.qq.com/
- 使用小程序管理员账号登录

#### 4.2 配置服务器域名
- 路径：开发 → 开发管理 → 开发设置 → 服务器域名
- 在 `request合法域名` 中添加：`https://api.yourdomain.com`
- 注意：必须是 HTTPS，不能带端口号

#### 4.3 配置小程序类目
- 路径：设置 → 基本设置 → 服务类目
- 选择合适的类目（如：工具 > 信息查询）

### 阶段5：前端代码适配

#### 5.1 修改生产环境API地址
编辑 `KL8_ui_副本/config.js`：
```javascript
const CONFIG = {
  development: {
    baseURL: 'http://localhost:8000',
    timeout: 10000
  },
  production: {
    baseURL: 'https://api.yourdomain.com',  // 改为你的域名
    timeout: 10000
  }
}

// 切换为生产环境
const IS_PRODUCTION = true  // 改为 true
```

#### 5.2 关闭域名校验（仅开发调试时）
在 `project.private.config.json` 中：
```json
{
  "setting": {
    "urlCheck": false  // 上传前改为 true
  }
}
```

### 阶段6：测试上线

#### 6.1 本地测试
1. 微信开发者工具中点击 "预览"
2. 用手机扫码测试
3. 确认API请求正常、数据展示正确

#### 6.2 上传代码
1. 微信开发者工具 → 上传
2. 填写版本号：1.0.0
3. 填写项目备注

#### 6.3 提交审核
1. 微信小程序后台 → 管理 → 版本管理
2. 找到刚上传的版本 → 提交审核
3. 填写审核信息：
   - 功能页面：期数列表、期数详情
   - 测试账号：（如有）
4. 等待审核（通常1-3个工作日）

#### 6.4 发布上线
- 审核通过后 → 全量发布
- 用户即可搜索使用

---

## 四、部署后运维

### 常用命令
```bash
# 查看API状态
systemctl status kl8-api

# 查看实时日志
journalctl -u kl8-api -f

# 重启API
systemctl restart kl8-api

# 重启Nginx
systemctl restart nginx

# 更新代码
cd /opt/kl8-api
git pull  # 或手动上传
systemctl restart kl8-api

# 更新SSL证书（自动续期）
certbot renew
```

### 更新部署流程
```bash
# 1. 本地修改代码后上传
scp kl8_api_server.py root@YOUR_SERVER_IP:/opt/kl8-api/

# 2. 服务器重启服务
ssh root@YOUR_SERVER_IP
systemctl restart kl8-api

# 3. 前端修改 config.js 后重新上传小程序
# 在微信开发者工具中 → 上传 → 提交审核 → 发布
```

---

## 五、注意事项

### 合规相关
1. ⚠️ 小程序名称和描述不能包含"彩票"、"预测"、"开奖"等敏感词
2. ⚠️ 当前已优化为"数据统计分析"，但仍需注意类目选择
3. ⚠️ 小程序内容不能涉及赌博、预测中奖等违规内容
4. ⚠️ 审核可能要求提供相关资质，建议选择"工具>信息查询"类目

### 技术相关
1. 域名必须ICP备案（国内服务器）
2. API必须使用HTTPS
3. 小程序服务器域名必须在后台配置
4. 代码上传前确保 IS_PRODUCTION = true
5. 建议使用 Gunicorn + Nginx 部署，不要直接用 Flask run

### 成本估算
| 项目 | 月费用 |
|------|--------|
| 服务器（2核2G） | ~50元 |
| 域名 | ~5元/年 |
| SSL证书 | 免费 |
| **总计** | **~55元/月** |
