# 前后端更新说明

## 📋 需求总结

1. **列表页面**：
   - 粉球位置展示开奖号码（而不是推荐号码）
   - 命中率百分比应为推荐号的命中比例（命中数/推荐数 * 100%）

2. **详情页面**：
   - 展示10个推荐号
   - 推荐号结合 kl8ycshunew.py 中的代码逻辑
   - 高频推荐中命中的号码用黄色表示

---

## 🔧 后端修改 (kl8_chengxu/kl8_api_server.py)

### 1. `/api/lottery/periods` 接口修改

**修改内容**：
- 添加推荐号池计算（开机号 + 试机号 + 金码 + 关注码 + 对应码）
- 计算推荐号命中数和命中率
- 返回字段：
  - `recommend_count`: 推荐号总数
  - `hit_count`: 命中数
  - `hit_rate`: 命中率（百分比）

### 2. `/api/periods/detail` 接口修改

**修改内容**：
- 添加 `recommend_numbers` 字段：返回10个高频推荐号
- 推荐号选择逻辑：从高频推荐号（出现≥2次）中选择前10个

**返回数据格式**：
```json
{
  "success": true,
  "data": {
    "period": { /* 期数数据 */ },
    "grid": [ /* 9宫格数据 */ ],
    "high_freq_numbers": [ /* 高频推荐号 */ ],
    "recommend_numbers": [ /* 10个推荐号 */ ],
    "stats": { /* 统计数据 */ }
  }
}
```

---

## 📱 前端修改 (KL8_ui_副本/)

### 1. 列表页面 (pages/lottery/lottery.js)

**修改内容**：
- 预览号码始终显示开奖号码（如果已开奖）
- 显示后端返回的命中率 `item.hit_rate`
- 计算逻辑：
  - 如果已开奖：显示前6个开奖号码
  - 如果未开奖：显示前6个推荐号

### 2. 列表页面样式 (pages/lottery/lottery.wxss)

**修改内容**：
- 添加 `.preview-number.pending` 样式：待开奖号码显示为灰色
- 保留 `.preview-number.open` 样式：开奖号码显示为粉色球

### 3. 列表页面模板 (pages/lottery/lottery.wxml)

**修改内容**：
- 预览号码添加 `pending` 状态样式

### 4. 详情页面 (pages/detail/detail.js)

**修改内容**：
- 格式化10个推荐号：
  - 从 `res.recommend_numbers` 获取
  - 格式化为两位数
  - 判断是否命中（对比开奖号码）
- 格式化高频推荐号：
  - 添加 `isHit` 字段
  - 标记是否命中

### 5. 详情页面模板 (pages/detail/detail.wxml)

**修改内容**：
- 推荐号码标题改为"推荐号码（10个）"
- 高频推荐号添加 `is-hit` 类名绑定

### 6. 详情页面样式 (pages/detail/detail.wxss)

**修改内容**：
- 添加 `.hot-number-item.is-hit` 样式：
  - 背景色：`#ffd700`（黄色）
  - 文字颜色：`#333`（黑色）
- 修改 `.hot-number-item.is-hit .hot-number-value` 样式

---

## 🎨 样式说明

### 列表页面
- **开奖号码（粉色球）**：
  - 渐变背景：`linear-gradient(135deg, #f093fb 0%, #f5576c 100%)`
  - 白色文字

- **待开奖号码（灰色球）**：
  - 背景色：`#e0e0e0`
  - 灰色文字

### 详情页面
- **高频推荐号（紫色）**：
  - 背景色：`#9c27b0`
  - 白色文字

- **高频推荐号命中（黄色）**：
  - 背景色：`#ffd700`
  - 黑色文字

---

## 🔄 数据流程

### 列表页面数据流
```
后端 API (/api/lottery/periods)
  ↓
返回：期数列表 + 命中率数据
  ↓
前端处理：
  - 计算预览号码（开奖号或推荐号）
  - 显示命中率和状态
  ↓
展示：期数列表
```

### 详情页面数据流
```
后端 API (/api/periods/detail?issue=xxx)
  ↓
返回：
  - period: 期数数据
  - grid: 9宫格数据
  - high_freq_numbers: 高频推荐号
  - recommend_numbers: 10个推荐号
  - stats: 统计数据
  ↓
前端处理：
  - 格式化9宫格
  - 格式化推荐号（10个）
  - 格式化高频号（标记命中）
  - 计算命中率
  ↓
展示：期数详情页
```

---

## 📊 推荐号逻辑（参考 kl8ycshunew.py）

### 推荐号池
```python
recommend_pool = {
    开机号: 10个,
    试机号: 10个,
    金码: 3个,
    关注码: 8个,
    对应码: 5个
}
# 去重后约 36个号码
```

### 高频推荐号
```python
# 统计每个号码在5个推荐源中的出现次数
recommend_counter = {
    号码1: 出现次数,
    号码2: 出现次数,
    ...
}

# 选择出现≥2次的号码
high_freq_numbers = [
    num for num, count in recommend_counter.items()
    if count >= 2
]

# 按次数和号码排序
high_freq_numbers.sort(key=lambda x: (x['count'], x['number']), reverse=True)

# 选择前10个作为推荐号
top_10_recommend_numbers = high_freq_numbers[:10]
```

### 命中率计算
```python
# 推荐号池
recommend_pool = 开机号 ∪ 试机号 ∪ 金码 ∪ 关注码 ∪ 对应码

# 开奖号码
lottery_numbers = {1, 2, 3, ..., 20}

# 命中数
hits = len(recommend_pool & lottery_numbers)

# 命中率
hit_rate = (hits / len(recommend_pool) * 100)
```

---

## ✅ 验证清单

- [x] 后端返回推荐号命中率
- [x] 后端返回10个推荐号
- [x] 列表页显示开奖号码（粉色球）
- [x] 列表页显示推荐号命中比例
- [x] 详情页显示10个推荐号
- [x] 详情页高频推荐号命中显示为黄色
- [x] 所有样式正确应用

---

## 🚀 使用方法

### 1. 启动后端服务器
```bash
cd /Users/luluzhenlan/PycharmProjects/KL8/kl8_chengxu
python3 kl8_api_server.py
```

### 2. 启动小程序前端
- 用微信开发者工具打开 `KL8_ui_副本` 项目
- 点击"编译"按钮

### 3. 测试功能
- 列表页：查看开奖号码（粉色球）和命中率
- 详情页：查看10个推荐号和高频推荐号（命中黄色）

---

## 📝 注意事项

1. **数据更新**：
   - 后端会自动从网络获取数据
   - 首次启动需要时间初始化
   - 可以调用 `POST /api/prediction/generate` 手动触发更新

2. **域名校验**：
   - 开发环境：在微信开发者工具中关闭域名校验
   - 生产环境：需要在微信公众平台配置域名白名单

3. **缓存机制**：
   - 后端使用缓存机制，避免频繁请求
   - 缓存数据保存在 `../cache/api_cache.json`

---

## 🔍 调试技巧

### 查看后端日志
```bash
# 查看缓存数据
cat ../cache/api_cache.json

# 查看API响应
curl http://localhost:8000/api/lottery/periods?limit=5
```

### 查看前端日志
- 微信开发者工具 → Console 标签
- 查看网络请求：Network 标签

---

## 📧 更新日期

- 2026-03-31：初始版本
  - 添加推荐号命中率计算
  - 添加10个推荐号
  - 列表页显示开奖号码
  - 详情页高频号命中黄色标记
