# 快乐 8 智能预测 API 服务器

## 安装依赖

```bash
pip install -r requirements_api.txt
```

## 启动服务器

```bash
python kl8_api_server.py
```

本地开发默认监听 **`http://localhost:8000`**（与 `kl8_api_server.py` 中 `app.run` 一致）。

## API 接口文档

### 健康检查
- **URL**: `GET /api/health`
- **描述**: 检查服务器运行状态
- **响应**:
```json
{
  "success": true,
  "status": "ok",
  "message": "快乐 8 智能预测 API 运行正常",
  "last_update": "2026-03-30T10:30:00",
  "is_updating": false
}
```

### 获取最新预测
- **URL**: `GET /api/prediction/latest`
- **描述**: 获取最新一期的预测结果
- **响应**:
```json
{
  "success": true,
  "data": {
    "period": "2026031",
    "predicted_numbers": [1, 5, 12, 23, 34, 45, 56, 67, 78, 80],
    "dan_codes": [1, 5],
    "generated_at": "2026-03-30T10:30:00"
  }
}
```

### 获取历史预测
- **URL**: `GET /api/prediction/history?limit=10`
- **描述**: 获取历史预测记录
- **参数**:
  - `limit`: 返回记录数（默认 15，最大 15）
- **响应**:
```json
{
  "success": true,
  "data": {
    "predictions": {
      "2026031": [1, 5, 12, 23, 34, 45, 56, 67, 78, 80],
      "2026030": [2, 6, 13, 24, 35, 46, 57, 68, 79, 80]
    },
    "total": 15
  }
}
```

### 获取开奖数据
- **URL**: `GET /api/lottery/data?limit=30`
- **描述**: 获取开奖数据
- **参数**:
  - `limit`: 返回期数（默认 30）
- **响应**:
```json
{
  "success": true,
  "data": {
    "current_draw": "2026031",
    "draws": {
      "2026031": {
        "numbers": [1, 5, 12, 23, 34, 45, 56, 67, 78, 80, 2, 6, 13, 24, 35, 46, 57, 68, 79, 3],
        "date": "2026-03-30",
        "sum": 810,
        "span": 79,
        "odd_even_ratio": "10:10",
        "big_small_ratio": "10:10"
      }
    },
    "total": 30
  }
}
```

### 获取推荐数据
- **URL**: `GET /api/lottery/periods?limit=15`
- **描述**: 获取推荐数据（开机号、试机号、金码等）
- **参数**:
  - `limit`: 返回期数（默认 15）
- **响应**:
```json
{
  "success": true,
  "data": {
    "periods": [
      {
        "issue": "2026031",
        "date": "2026-03-30",
        "kaiji": [1, 5, 12],
        "shiji": [23, 34, 45],
        "jin": [56],
        "guanzhu": [67, 78, 80],
        "duiying": [2, 6, 13],
        "lottery_numbers": [1, 5, 12, 23, 34, 45, 56, 67, 78, 80, 2, 6, 13, 24, 35, 46, 57, 68, 79, 3]
      }
    ],
    "total": 15
  }
}
```

### 获取回测统计
- **URL**: `GET /api/analysis/backtest`
- **描述**: 获取回测统计数据
- **响应**:
```json
{
  "success": true,
  "data": {
    "total_periods": 15,
    "max_hit_rate": 35.5,
    "high_freq_hit_rate": 42.3,
    "low_freq_hit_rate": 28.7
  }
}
```

### 获取周期性分析
- **URL**: `GET /api/analysis/periodicity`
- **描述**: 获取周期性分析结果
- **响应**:
```json
{
  "success": true,
  "data": {
    "optimal_periods": 15,
    "all_results": {
      "5": {"avg_hit_rate": 5.2, "stability": 0.85},
      "10": {"avg_hit_rate": 5.5, "stability": 0.87},
      "15": {"avg_hit_rate": 5.3, "stability": 0.89}
    }
  }
}
```

### 生成新预测
- **URL**: `POST /api/prediction/generate`
- **描述**: 触发生成新的预测（异步执行）
- **响应**:
```json
{
  "success": true,
  "message": "开始生成预测，请稍后查询结果"
}
```

### 获取单期详情
- **URL**: `GET /api/periods/detail?issue=2026031`
- **描述**: 获取单期详细数据，包括 9 宫格布局
- **参数**:
  - `issue`: 期号（必需）
- **响应**:
```json
{
  "success": true,
  "data": {
    "period": {
      "issue": "2026031",
      "date": "2026-03-30",
      "kaiji": [1, 5, 12],
      "shiji": [23, 34, 45],
      "jin": [56],
      "guanzhu": [67, 78, 80],
      "duiying": [2, 6, 13],
      "lottery_numbers": [1, 5, 12, 23, 34, 45, 56, 67, 78, 80, 2, 6, 13, 24, 35, 46, 57, 68, 79, 3]
    },
    "grid": [
      [
        {"number": 1, "is_lottery": true, "is_recommend": true, "is_hit": true, "type_labels": ["开"]},
        {"number": 2, "is_lottery": true, "is_recommend": true, "is_hit": true, "type_labels": ["对"]},
        ...
      ],
      ...
    ],
    "high_freq_numbers": [
      {"number": 1, "count": 2, "is_hit": true},
      {"number": 5, "count": 3, "is_hit": true},
      ...
    ],
    "stats": {
      "total_hits": 8,
      "hit_rate": 40.0,
      "kaiji_hits": 3,
      "shiji_hits": 2,
      "jin_hits": 1,
      "guanzhu_hits": 1,
      "duiying_hits": 1,
      "total_recommends": 12
    },
    "prediction": [1, 5, 12, 23, 34, 45, 56, 67, 78, 80]
  }
}
```

### 获取所有数据
- **URL**: `GET /api/all-data`
- **描述**: 一次性获取所有数据
- **响应**:
```json
{
  "success": true,
  "data": {
    "prediction": {...},
    "backtest": {...},
    "periodicity": {...},
    "all_predictions": {...},
    "last_update": "2026-03-30T10:30:00",
    "is_updating": false
  }
}
```

## 特性

- ✅ 自动缓存数据，减少外部 API 调用
- ✅ 后台定时更新（每小时）
- ✅ 线程安全的数据访问
- ✅ 跨域支持（CORS）
- ✅ 错误处理和日志记录
- ✅ 健康检查接口

## 小程序调用示例

```javascript
// 生产环境请使用合法请求域名（HTTPS），例如：
const BASE = 'https://api.zhstpbf.cn';

// 获取最新预测
wx.request({
  url: BASE + '/api/prediction/latest',
  success(res) {
    console.log('最新预测:', res.data.data);
  }
});

// 生成新预测
wx.request({
  url: BASE + '/api/prediction/generate',
  method: 'POST',
  success(res) {
    console.log('开始生成预测:', res.data.message);
  }
});

// 获取单期详情（含 9 宫格）
wx.request({
  url: BASE + '/api/periods/detail',
  data: { issue: '2026031' },
  success(res) {
    console.log('期数详情:', res.data.data);
  }
});
```

## 注意事项

1. 首次启动时会自动获取初始数据
2. 数据每小时自动更新一次
3. 所有数据都会缓存到 `cache/api_cache.json`
4. 生成预测是异步操作，需要稍后查询结果
5. 开发模式监听 `0.0.0.0:8000`；生产环境由 Nginx/宝塔反代到 HTTPS
