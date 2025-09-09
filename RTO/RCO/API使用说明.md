# 预警信息API使用说明

## 概述

`warning_api.py` 是一个独立的API服务器，提供RESTful接口来获取预警系统的各种信息。该API服务可以与主监控大屏并行运行，为其他系统提供预警数据。

## 启动方式

```bash
# 在RTO/RCO目录下运行
python warning_api.py
```

服务将在 `http://localhost:8091` 启动。

## API端点详情

### 1. 获取完整预警信息
**端点**: `GET /api/warnings`

**描述**: 获取系统的完整预警信息，包括当前告警、历史告警、设备状态等。

**响应示例**:
```json
{
  "success": true,
  "data": {
    "current_alerts": [
      {
        "type": "燃烧室温度不达标",
        "value": 750.5,
        "severity": "high",
        "equipment": "燃烧室",
        "threshold": 760,
        "unit": "℃",
        "timestamp": "2024-01-15T10:30:00",
        "id": "alert_1705302600"
      }
    ],
    "alert_history": [...],
    "alerts_by_severity": {
      "critical": [...],
      "high": [...],
      "medium": [...],
      "low": [...]
    },
    "violation_summary": {
      "total": 5,
      "ongoing": 2,
      "resolved": 3
    },
    "equipment_status": {
      "燃烧室": "warning",
      "废气出口": "normal"
    },
    "statistics": {
      "total_alerts_today": 15,
      "active_alerts_count": 3,
      "critical_alerts": 1,
      "high_alerts": 2
    },
    "last_updated": "2024-01-15T10:30:00"
  }
}
```

### 2. 获取当前活跃告警
**端点**: `GET /api/warnings/current`

**描述**: 仅获取当前活跃的告警信息。

**响应示例**:
```json
{
  "success": true,
  "data": {
    "current_alerts": [
      {
        "type": "废气出口污染物浓度超标",
        "value": 65.2,
        "severity": "critical",
        "equipment": "废气出口",
        "threshold": 50,
        "unit": "mg/m³",
        "timestamp": "2024-01-15T10:30:00",
        "id": "alert_1705302600"
      }
    ],
    "count": 1,
    "timestamp": "2024-01-15T10:30:00"
  }
}
```

### 3. 获取告警历史
**端点**: `GET /api/warnings/history`

**查询参数**:
- `limit`: 返回记录数量限制（默认50）
- `severity`: 按严重程度过滤（critical/high/medium/low）

**示例**:
```
GET /api/warnings/history?limit=100&severity=critical
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "alert_history": [
      {
        "type": "反应器出口温度异常",
        "value": 620.5,
        "severity": "critical",
        "equipment": "反应器",
        "threshold": 600,
        "unit": "℃",
        "timestamp": "2024-01-15T10:25:00",
        "id": "alert_1705302300"
      }
    ],
    "count": 1,
    "filters": {
      "limit": 100,
      "severity": "critical"
    },
    "timestamp": "2024-01-15T10:30:00"
  }
}
```

### 4. 获取预警统计信息
**端点**: `GET /api/warnings/statistics`

**描述**: 获取预警的统计分布信息。

**响应示例**:
```json
{
  "success": true,
  "data": {
    "severity_distribution": {
      "critical": 5,
      "high": 12,
      "medium": 8,
      "low": 3
    },
    "equipment_distribution": {
      "燃烧室": 8,
      "废气出口": 5,
      "吸附设施": 3,
      "反应器": 6,
      "应急系统": 2,
      "催化燃烧装置": 4
    },
    "hourly_distribution": {
      "10:00": 2,
      "11:00": 5,
      "12:00": 3,
      "13:00": 1
    },
    "total_alerts": 28,
    "equipment_status": {
      "燃烧室": "warning",
      "废气出口": "critical",
      "吸附设施": "normal"
    },
    "timestamp": "2024-01-15T10:30:00"
  }
}
```

### 5. 获取设备状态
**端点**: `GET /api/warnings/equipment`

**描述**: 获取所有设备的当前状态。

**响应示例**:
```json
{
  "success": true,
  "data": {
    "equipment_status": {
      "燃烧室": "warning",
      "废气出口": "critical",
      "吸附设施": "normal",
      "脱附设施": "normal",
      "反应器": "warning",
      "应急系统": "normal"
    },
    "status_counts": {
      "normal": 3,
      "warning": 2,
      "critical": 1
    },
    "total_equipment": 6,
    "timestamp": "2024-01-15T10:30:00"
  }
}
```

### 6. 获取预警规则
**端点**: `GET /api/warnings/rules`

**描述**: 获取所有预警规则的配置信息。

**响应示例**:
```json
{
  "success": true,
  "data": {
    "all_rules": [
      {
        "rule_id": "R001",
        "rule_name": "燃烧室温度不达标",
        "description": "燃烧室温度未达到规定值760℃以上",
        "condition": "temperature_combustion < 760",
        "threshold_value": 760,
        "threshold_unit": "℃",
        "severity": "high",
        "is_active": true
      }
    ],
    "active_rules": [...],
    "inactive_rules": [...],
    "total_rules": 16,
    "active_count": 14,
    "inactive_count": 2,
    "timestamp": "2024-01-15T10:30:00"
  }
}
```

### 7. 获取API健康状态
**端点**: `GET /api/health`

**描述**: 检查API服务的健康状态。

**响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00",
    "uptime_seconds": 3600.123,
    "uptime_formatted": "1h 0m 0s",
    "version": "1.0.0",
    "services": {
      "data_generator": true,
      "rule_engine": true
    }
  }
}
```

## 使用示例

### Python客户端示例
```python
import requests
import json

# 获取完整预警信息
response = requests.get('http://localhost:8091/api/warnings')
data = response.json()

if data['success']:
    alerts = data['data']['current_alerts']
    print(f"当前告警数量: {len(alerts)}")
    
    for alert in alerts:
        print(f"告警: {alert['type']}")
        print(f"设备: {alert['equipment']}")
        print(f"严重程度: {alert['severity']}")
        print(f"当前值: {alert['value']}{alert['unit']}")
        print(f"阈值: {alert['threshold']}{alert['unit']}")
        print("-" * 30)

# 获取设备状态
response = requests.get('http://localhost:8091/api/warnings/equipment')
data = response.json()

if data['success']:
    equipment_status = data['data']['equipment_status']
    for equipment, status in equipment_status.items():
        status_text = {
            'normal': '正常',
            'warning': '警告', 
            'critical': '严重'
        }.get(status, '未知')
        print(f"{equipment}: {status_text}")
```

### JavaScript客户端示例
```javascript
// 获取当前告警
async function getCurrentAlerts() {
    try {
        const response = await fetch('http://localhost:8091/api/warnings/current');
        const data = await response.json();
        
        if (data.success) {
            console.log('当前告警:', data.data.current_alerts);
            return data.data.current_alerts;
        } else {
            console.error('获取告警失败:', data.error);
        }
    } catch (error) {
        console.error('网络错误:', error);
    }
}

// 获取统计信息
async function getStatistics() {
    try {
        const response = await fetch('http://localhost:8091/api/warnings/statistics');
        const data = await response.json();
        
        if (data.success) {
            console.log('严重程度分布:', data.data.severity_distribution);
            console.log('设备分布:', data.data.equipment_distribution);
            return data.data;
        }
    } catch (error) {
        console.error('获取统计失败:', error);
    }
}

// 定期获取数据
setInterval(async () => {
    await getCurrentAlerts();
    await getStatistics();
}, 5000); // 每5秒更新一次
```

### curl命令示例
```bash
# 获取完整预警信息
curl http://localhost:8091/api/warnings

# 获取严重告警历史
curl "http://localhost:8091/api/warnings/history?severity=critical&limit=20"

# 获取设备状态
curl http://localhost:8091/api/warnings/equipment

# 检查API健康状态
curl http://localhost:8091/api/health

# 获取统计信息
curl http://localhost:8091/api/warnings/statistics
```

## 错误处理

所有API都会返回统一的错误格式：

```json
{
  "success": false,
  "error": "具体的错误描述信息"
}
```

常见HTTP状态码：
- `200`: 请求成功
- `404`: API端点不存在
- `500`: 服务器内部错误

## 数据模型

### 告警对象结构
```json
{
  "type": "告警类型名称",
  "value": 123.45,
  "severity": "critical|high|medium|low",
  "equipment": "设备名称", 
  "threshold": 100.0,
  "unit": "单位",
  "timestamp": "2024-01-15T10:30:00",
  "id": "alert_1705302600"
}
```

### 设备状态
- `normal`: 正常运行
- `warning`: 警告状态
- `critical`: 严重故障

### 严重程度级别
- `critical`: 严重 - 需要立即处理
- `high`: 高 - 需要尽快处理  
- `medium`: 中等 - 需要关注
- `low`: 低 - 一般提醒

## 部署和配置

### 系统要求
- Python 3.7+
- pandas, numpy 库
- 可选：file_player.py（用于文件数据播放功能）

### 安装依赖
```bash
pip install pandas numpy
```

### 配置选项
- 端口号：默认8091，可在代码中修改
- 数据保留时间：告警历史保留3分钟，可调整
- 更新频率：实时数据每次请求生成新数据

### 注意事项

1. **CORS支持**: API支持跨域请求，适合前端应用调用
2. **数据实时性**: 每次请求都会生成新的模拟数据和告警
3. **并发访问**: 支持多个客户端同时访问
4. **内存使用**: 告警历史有自动清理机制，避免内存泄漏
5. **依赖关系**: 可独立运行，不依赖主监控大屏系统

### 扩展功能

可以根据需要添加更多功能：
- 告警确认和处理接口
- 历史数据持久化存储
- 规则配置修改接口
- 数据导出功能
- 告警推送通知
- 用户权限管理
