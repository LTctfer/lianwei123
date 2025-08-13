# 抽取式吸附曲线API累加数据处理使用说明

## 功能概述

API现在支持累加数据处理模式，可以在连续多次数据输入中保持时间坐标的连续性。

### 核心功能
- **累加模式**: 通过`session_id`管理会话，后续数据的时间坐标在前次基础上累加
- **会话管理**: 查询、重置会话状态
- **兼容性**: 保持原有非累加模式的完全兼容

## API端点

### 1. 数据处理接口 (支持累加)
```
POST /api/extraction-adsorption-curve/process
```

#### 请求格式

**累加模式**（推荐）:
```json
{
  "session_id": "your_session_id", 
  "data": [
    {
      "gVocs": 10.5,
      "inVoc": 95.2,
      "gWindspeed": 2.8,
      "access": 2,
      "createTime": "2024-01-15T10:30:00"
    }
  ]
}
```

**非累加模式**（兼容原有方式）:
```json
[
  {
    "gVocs": 10.5,
    "inVoc": 95.2,
    "gWindspeed": 2.8,
    "access": 2,
    "createTime": "2024-01-15T10:30:00"
  }
]
```

#### 响应格式
```json
{
  "status": "success",
  "data_points": [
    {
      "x": 5.25,  // 累计运行时间（小时）- 已应用时间偏移
      "y": 12.5,  // 穿透率（%）
      "label": "时间段: 时间段1\n累积时长: 5.25小时\n穿透率: 12.5%",
      "cumulative_hours": 5.25,  // 累加后时间
      "original_hours": 1.25,    // 本批次原始时间
      "time_offset": 4.0,        // 应用的时间偏移
      // ... 其他字段
    }
  ],
  "warning_points": [
    {
      "x": 8.5,  // 预警点时间（已累加）
      "y": 85.0, // 预警点穿透率
      "type": "warning_star",
      "color": "orange",
      "original_time": 3.5,  // 原始预警时间
      "time_offset": 5.0     // 应用的时间偏移
    }
  ],
  "session_info": {
    "session_id": "your_session_id",
    "current_batch_points": 3,        // 本批次数据点数
    "total_accumulated_points": 8,    // 累计总数据点数
    "last_cumulative_time": 6.75,    // 最后累计时间
    "time_offset_applied": 4.0,      // 本次应用的时间偏移
    "all_accumulated_points": [...]  // 所有累积的数据点
  }
}
```

### 2. 会话管理接口

#### 查询会话信息
```
GET /api/extraction-adsorption-curve/session/{session_id}
```

响应:
```json
{
  "session_id": "your_session_id",
  "exists": true,
  "total_points": 8,
  "last_cumulative_time": 6.75,
  "data_points": [...]
}
```

#### 重置会话
```
DELETE /api/extraction-adsorption-curve/session/{session_id}
```

响应:
```json
{
  "message": "会话 your_session_id 已重置",
  "success": true
}
```

#### 列出所有会话
```
GET /api/extraction-adsorption-curve/sessions
```

响应:
```json
{
  "total_sessions": 2,
  "sessions": {
    "session_001": {
      "total_points": 5,
      "last_cumulative_time": 4.5
    },
    "session_002": {
      "total_points": 3,
      "last_cumulative_time": 2.1
    }
  }
}
```

## 累加机制说明

### 时间累加逻辑

1. **首次处理**: 时间偏移为0，直接使用算法计算的时间坐标
   ```
   第一批结果: x = [1.0, 3.0, 4.0, 5.0]
   最后累计时间: 5.0
   ```

2. **后续处理**: 以上次最后时间为偏移基础
   ```
   第二批原始: x = [1.5, 2.5, 3.0]
   时间偏移: 5.0
   第二批结果: x = [6.5, 7.5, 8.0]
   最后累计时间: 8.0
   ```

3. **预警点同步**: 预警点时间坐标也会应用相同偏移
   ```
   原始预警时间: 3.2小时
   应用偏移后: 3.2 + 5.0 = 8.2小时
   ```

### 会话生命周期

- **自动创建**: 首次使用session_id时自动创建会话
- **持久化**: 会话数据在内存中持久保存（服务重启会丢失）
- **手动重置**: 通过DELETE接口清除会话数据
- **数据累积**: 每次处理的数据点都会累积保存在会话中

## 使用示例

### Python示例代码

```python
import requests
import json
from datetime import datetime

# API基础URL
base_url = "http://localhost:5000/api/extraction-adsorption-curve"
session_id = "my_session_001"

# 第一批数据
first_batch = {
    "session_id": session_id,
    "data": [
        {
            "gVocs": 10.0,
            "inVoc": 100.0,
            "gWindspeed": 2.5,
            "access": 2,
            "createTime": "2024-01-15T10:00:00"
        },
        {
            "gVocs": 15.0,
            "inVoc": 95.0,
            "gWindspeed": 2.6,
            "access": 2,
            "createTime": "2024-01-15T10:30:00"
        }
    ]
}

# 发送第一批
response1 = requests.post(f"{base_url}/process", json=first_batch)
result1 = response1.json()
print("第一批X坐标:", [p['x'] for p in result1['data_points']])

# 第二批数据
second_batch = {
    "session_id": session_id,
    "data": [
        {
            "gVocs": 20.0,
            "inVoc": 90.0,
            "gWindspeed": 2.7,
            "access": 2,
            "createTime": "2024-01-15T11:00:00"
        }
    ]
}

# 发送第二批
response2 = requests.post(f"{base_url}/process", json=second_batch)
result2 = response2.json()
print("第二批X坐标:", [p['x'] for p in result2['data_points']])
print("时间偏移:", result2['session_info']['time_offset_applied'])

# 查询会话
session_info = requests.get(f"{base_url}/session/{session_id}").json()
print("累计数据点:", session_info['total_points'])

# 重置会话
reset_result = requests.delete(f"{base_url}/session/{session_id}").json()
print("重置结果:", reset_result['message'])
```

### JavaScript示例代码

```javascript
const baseUrl = 'http://localhost:5000/api/extraction-adsorption-curve';
const sessionId = 'js_session_001';

// 发送累加数据
async function sendCumulativeData() {
    // 第一批数据
    const firstBatch = {
        session_id: sessionId,
        data: [
            {
                gVocs: 12.0,
                inVoc: 98.0,
                gWindspeed: 2.4,
                access: 2,
                createTime: new Date().toISOString()
            }
        ]
    };

    const response1 = await fetch(`${baseUrl}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(firstBatch)
    });
    
    const result1 = await response1.json();
    console.log('第一批结果:', result1.data_points.map(p => p.x));

    // 第二批数据
    const secondBatch = {
        session_id: sessionId,
        data: [
            {
                gVocs: 18.0,
                inVoc: 92.0,
                gWindspeed: 2.8,
                access: 2,
                createTime: new Date().toISOString()
            }
        ]
    };

    const response2 = await fetch(`${baseUrl}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(secondBatch)
    });
    
    const result2 = await response2.json();
    console.log('第二批结果:', result2.data_points.map(p => p.x));
    console.log('时间偏移:', result2.session_info.time_offset_applied);
}

sendCumulativeData();
```

## 注意事项

1. **会话ID唯一性**: 不同的数据流应使用不同的session_id
2. **内存限制**: 会话数据存储在内存中，服务重启会丢失
3. **并发安全**: 同一session_id的并发请求可能导致数据不一致
4. **时间单位**: 所有时间坐标均为小时单位
5. **兼容性**: 不提供session_id时保持原有行为不变

## 故障排除

### 常见问题

1. **时间不连续**: 检查session_id是否正确，是否被意外重置
2. **数据点重复**: 避免使用相同session_id处理不同数据流
3. **内存占用**: 定期重置不再使用的会话
4. **预警点偏移**: 预警点时间会自动应用时间偏移，这是正常行为

### 调试技巧

- 使用会话查询接口检查累计状态
- 检查响应中的`time_offset_applied`字段
- 对比`original_hours`和`cumulative_hours`字段
- 查看`session_info`中的详细信息

## 版本信息

- **API版本**: 1.0.0
- **累加功能**: 新增
- **兼容性**: 完全向后兼容
- **编码**: UTF-8支持中文
