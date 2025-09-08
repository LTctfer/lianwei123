# RTO/RCO预警系统API使用说明

## 概述
本系统提供了完整的REST API接口，用于管理预警规则的阈值和状态。所有API都支持JSON格式的请求和响应。

## API端点

### 1. 获取所有规则
**GET** `/api/rules`

**响应示例：**
```json
{
  "success": true,
  "data": [
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
  "total": 16
}
```

### 2. 获取单个规则详情
**GET** `/api/rules/{rule_id}`

**响应示例：**
```json
{
  "success": true,
  "data": {
    "rule_id": "R001",
    "rule_name": "燃烧室温度不达标",
    "description": "燃烧室温度未达到规定值760℃以上",
    "condition": "temperature_combustion < 760",
    "threshold_value": 760,
    "threshold_unit": "℃",
    "severity": "high",
    "is_active": true
  }
}
```

### 3. 更新规则阈值
**POST** `/api/rules/update-threshold`

**请求体：**
```json
{
  "rule_id": "R001",
  "threshold": 780
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "规则 R001 阈值已更新为 780"
}
```

### 4. 切换规则状态
**POST** `/api/rules/toggle-status`

**请求体：**
```json
{
  "rule_id": "R001"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "规则 R001 已禁用",
  "is_active": false
}
```

### 5. 更新规则详情
**PUT** `/api/rules/{rule_id}`

**请求体：**
```json
{
  "threshold_value": 780,
  "threshold_unit": "℃",
  "severity": "critical",
  "is_active": true,
  "description": "更新后的描述"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "规则 R001 已更新"
}
```

## 使用示例

### Python示例
```python
import requests
import json

# 获取所有规则
response = requests.get('http://localhost:8090/api/rules')
rules = response.json()
print(f"共有 {rules['total']} 条规则")

# 更新规则阈值
update_data = {
    "rule_id": "R001",
    "threshold": 780
}
response = requests.post(
    'http://localhost:8090/api/rules/update-threshold',
    json=update_data
)
result = response.json()
print(result['message'])

# 禁用规则
toggle_data = {"rule_id": "R001"}
response = requests.post(
    'http://localhost:8090/api/rules/toggle-status',
    json=toggle_data
)
result = response.json()
print(result['message'])
```

### JavaScript示例
```javascript
// 获取所有规则
async function getRules() {
    const response = await fetch('/api/rules');
    const data = await response.json();
    return data.data;
}

// 更新规则阈值
async function updateThreshold(ruleId, newThreshold) {
    const response = await fetch('/api/rules/update-threshold', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            rule_id: ruleId,
            threshold: newThreshold
        })
    });
    return await response.json();
}

// 切换规则状态
async function toggleRuleStatus(ruleId) {
    const response = await fetch('/api/rules/toggle-status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            rule_id: ruleId
        })
    });
    return await response.json();
}
```

### curl示例
```bash
# 获取所有规则
curl -X GET http://localhost:8090/api/rules

# 更新规则阈值
curl -X POST http://localhost:8090/api/rules/update-threshold \
  -H "Content-Type: application/json" \
  -d '{"rule_id": "R001", "threshold": 780}'

# 切换规则状态
curl -X POST http://localhost:8090/api/rules/toggle-status \
  -H "Content-Type: application/json" \
  -d '{"rule_id": "R001"}'
```

## 错误处理

所有API都会返回统一的错误格式：

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

常见错误：
- `缺少必要参数: rule_id 和 threshold`
- `未找到规则ID: R999`
- `规则引擎未初始化`
- `请求处理失败: 具体错误信息`

## 规则配置持久化

所有规则配置都会自动保存到 `warning_rules.json` 文件中，系统重启后会自动加载保存的配置。

## 前端界面

系统还提供了完整的前端管理界面，访问 `http://localhost:8090` 后点击"规则管理"模块即可通过图形界面管理所有规则。
