# 预警系统API使用说明

## 🎯 接口概述

预警系统预测接口专门用于接收累计的时间-穿透率数据点，调用Logistic预警系统算法进行拟合，**严格按照算法定义计算并仅返回预警点XY坐标**。

### 核心功能
- ⭐ **预警点计算**: 基于时间跨度80%位置的预警点坐标
- ⭐ **饱和点预测**: 基于模型预测最大穿透率95%的饱和点坐标
- 🎯 **算法严格性**: 完全按照Logistic预警系统算法中的定义计算
- 📦 **简化输出**: 仅返回XY坐标，无额外信息

---

## 📡 API端点

### 服务信息
- **基础URL**: `http://localhost:5001`
- **编码**: UTF-8
- **响应格式**: JSON

### 1. 主要接口 - 预警点分析
```
POST /api/warning-prediction/analyze
```

#### 请求格式
```json
{
  "data_points": [
    {"x": 1.5, "y": 12.5},
    {"x": 3.0, "y": 25.8},
    {"x": 4.5, "y": 45.2},
    {"x": 6.0, "y": 68.5},
    {"x": 7.5, "y": 85.3}
  ]
}
```

**参数说明**:
- `data_points` (必需): 累计数据点数组
  - `x`: 累计时间（单位：小时）
  - `y`: 穿透率（单位：百分比，0-100%）

**支持的字段格式**:
- 标准格式: `x`, `y`
- 时间格式: `time`, `breakthrough_ratio`
- 中文格式: `cumulative_time`, `穿透率`

**注意**: 简化版接口不再支持session_id参数

#### 响应格式（简化版）
```json
{
  "warning_points": [
    {
      "x": 7.2,
      "y": 75.3
    },
    {
      "x": 9.0,
      "y": 88.5
    }
  ]
}
```

**响应说明**:
- `warning_points`: 预警点坐标数组
  - 第一个点：预警点（时间跨度80%位置）
  - 第二个点：预测饱和点（模型最大穿透率95%对应时间）
  - `x`: 时间坐标（小时）
  - `y`: 穿透率（百分比）

**简化说明**:
- 仅返回XY坐标，无其他额外信息
- 按时间顺序排列（预警点在前，饱和点在后）
- 严格按照算法中的定义计算

### 2. 辅助接口

#### 健康检查
```
GET /api/warning-prediction/health
```

#### API信息
```
GET /api/warning-prediction/info
```

**注意**: 简化版接口移除了以下功能：
- 模型信息查询
- 未来预测
- 会话管理
- 模型质量评估

---

## ⭐ 预警点算法定义

### 1. 预警点计算
- **定义**: 从穿透起始点到预测饱和点时间跨度的80%位置
- **公式**: `预警时间 = 起始时间 + (饱和时间 - 起始时间) × 0.8`
- **示例**: 起始0h，饱和9h → 预警时间 = 0 + (9-0) × 0.8 = 7.2h
- **穿透率**: 由Logistic模型在预警时间点预测得出

### 2. 预测饱和点计算
- **定义**: 模型预测最大穿透率95%对应的时间点
- **公式**: `t = t0 - ln(A / (A×0.95) - 1) / k`
- **参数**: A=最大穿透率, k=增长率, t0=中点时间
- **说明**: 非固定穿透率，基于Logistic模型参数动态计算

---

## 💻 使用示例

### Python示例

```python
import requests
import json

# API配置
api_url = "http://localhost:5001/api/warning-prediction/analyze"

# 准备累计数据点（来自数据处理接口的结果）
accumulated_data = [
    {"x": 1.0, "y": 8.5},   # 1小时时穿透率8.5%
    {"x": 2.5, "y": 22.3},  # 2.5小时时穿透率22.3%
    {"x": 4.0, "y": 42.8},  # 4小时时穿透率42.8%
    {"x": 5.5, "y": 65.2},  # 5.5小时时穿透率65.2%
    {"x": 7.0, "y": 82.6}   # 7小时时穿透率82.6%
]

# 发送请求（简化版格式）
request_data = {
    "data_points": accumulated_data
}

response = requests.post(
    api_url,
    json=request_data,
    headers={'Content-Type': 'application/json; charset=utf-8'}
)

if response.status_code == 200:
    result = response.json()

    # 提取预警点坐标
    warning_points = result['warning_points']

    print("🌟 预警点分析结果:")
    for i, point in enumerate(warning_points):
        if i == 0:
            print(f"  🟠 预警点: X={point['x']}h, Y={point['y']}%")
            print(f"     (时间跨度80%位置)")
        elif i == 1:
            print(f"  🔴 饱和点: X={point['x']}h, Y={point['y']}%")
            print(f"     (模型最大穿透率95%对应时间)")

    print(f"\n📊 算法说明:")
    print(f"  - 预警点基于时间跨度计算，非固定穿透率")
    print(f"  - 饱和点基于Logistic模型参数计算")
    print(f"  - 严格按照算法定义，确保准确性")

else:
    print(f"❌ 请求失败: {response.status_code}")
    print(f"错误信息: {response.text}")
```

### JavaScript示例

```javascript
const apiUrl = 'http://localhost:5001/api/warning-prediction/analyze';

// 累计数据点（从前端图表或数据处理接口获取）
const accumulatedData = [
    {x: 1.2, y: 10.5},
    {x: 2.8, y: 28.3},
    {x: 4.5, y: 48.7},
    {x: 6.1, y: 70.2},
    {x: 7.8, y: 86.9}
];

// 调用预警分析API（简化版）
async function analyzeWarningPoints() {
    const requestData = {
        data_points: accumulatedData
    };

    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(requestData)
        });

        const result = await response.json();

        if (result.warning_points) {
            // 处理预警点坐标
            const warningPoints = result.warning_points;

            warningPoints.forEach((point, index) => {
                if (index === 0) {
                    // 第一个点是预警点
                    console.log(`🟠 预警点: X=${point.x}h, Y=${point.y}%`);
                    addWarningStarToChart(point.x, point.y, 'orange');
                    showWarningNotification(`预警点: ${point.x}小时处达到${point.y}%穿透率`);

                } else if (index === 1) {
                    // 第二个点是饱和点
                    console.log(`🔴 饱和点: X=${point.x}h, Y=${point.y}%`);
                    addWarningStarToChart(point.x, point.y, 'red');
                    showCriticalNotification(`饱和点: ${point.x}小时处预计达到${point.y}%穿透率`);
                }
            });

            // 更新UI显示预警信息
            updateWarningUI(warningPoints);

        } else if (result.error) {
            console.error('预警分析失败:', result.error);
        }
    } catch (error) {
        console.error('API调用失败:', error);
    }
}

// 在图表上添加五角星标记的示例函数
function addWarningStarToChart(x, y, color) {
    // 使用图表库（如Chart.js, ECharts等）添加五角星标记
    // 示例：ECharts格式
    const starPoint = {
        name: color === 'orange' ? '预警点' : '饱和点',
        coord: [x, y],
        symbol: 'diamond', // 或其他星形符号
        symbolSize: color === 'red' ? 18 : 15,
        itemStyle: {
            color: color,
            borderColor: '#fff',
            borderWidth: 2
        }
    };

    // 添加到图表的markPoint配置中
    chart.setOption({
        series: [{
            markPoint: {
                data: [starPoint]
            }
        }]
    });
}

// 调用分析
analyzeWarningPoints();
```

### cURL示例

```bash
# 发送预警分析请求（简化版）
curl -X POST "http://localhost:5001/api/warning-prediction/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "data_points": [
      {"x": 1.0, "y": 8.5},
      {"x": 2.5, "y": 22.3},
      {"x": 4.0, "y": 42.8},
      {"x": 5.5, "y": 65.2},
      {"x": 7.0, "y": 82.6}
    ]
  }'

# 查询健康状态
curl "http://localhost:5001/api/warning-prediction/health"

# 查询API信息
curl "http://localhost:5001/api/warning-prediction/info"
```

---

## 📋 数据要求

### 最小要求
- **数据点数**: 至少3个点
- **数据特征**: 应呈现S型增长趋势
- **时间单位**: 小时（正数）
- **穿透率单位**: 百分比（0-100%）

### 最佳实践
- **推荐点数**: 5-15个点
- **时间分布**: 覆盖穿透过程的起始、中期、后期
- **数据质量**: 相对平滑，避免大幅波动
- **时间排序**: 按时间顺序排列

### 数据示例
```json
{
  "data_points": [
    {"x": 0.5, "y": 2.1},   // 初期低穿透率
    {"x": 1.5, "y": 8.5},   // 缓慢上升
    {"x": 3.0, "y": 25.3},  // 加速期
    {"x": 4.5, "y": 52.8},  // 快速增长
    {"x": 6.0, "y": 78.2},  // 接近饱和
    {"x": 7.0, "y": 88.5}   // 高穿透率
  ]
}
```

### 预期响应示例
```json
{
  "warning_points": [
    {"x": 5.6, "y": 72.3},  // 预警点(时间跨度80%位置)
    {"x": 7.0, "y": 85.2}   // 饱和点(模型最大穿透率95%)
  ]
}
```

---

## 🚨 错误处理

### 常见错误响应

#### 1. 数据不足
```json
{
  "status": "failure",
  "error": "有效数据点不足，至少需要3个点"
}
```

#### 2. 模型拟合失败
```json
{
  "error": "预警模型拟合失败，数据可能不符合S型曲线特征"
}
```

#### 3. 数据格式错误
```json
{
  "error": "数据格式错误或为空"
}
```

#### 4. 服务器错误
```json
{
  "error": "预警系统处理失败: 具体错误信息"
}
```

### 状态码说明
- **200**: 成功
- **400**: 请求参数错误
- **500**: 服务器内部错误

---

## 🔧 部署和运行

### 环境要求
```bash
pip install flask numpy pandas scipy
```

### 启动服务
```bash
python warning_prediction_api.py
```

### 默认配置
- **端口**: 5001
- **主机**: 0.0.0.0
- **调试模式**: 开启

### 服务验证
```bash
# 检查服务状态
curl http://localhost:5001/api/warning-prediction/health

# 查看API文档
curl http://localhost:5001/api/warning-prediction/info
```

---

## 📊 算法说明

### Logistic回归模型
使用Logistic函数拟合S型穿透曲线：
```
y = A / (1 + exp(-k*(t-t0)))
```

**参数含义**:
- `A`: 最大穿透率（通常接近1.0或100%）
- `k`: 增长率参数（决定曲线陡峭程度）
- `t0`: 中点时间（50%穿透率对应的时间）

### 关键时间点计算

#### 1. 预测饱和时间
```
actual_saturation_ratio = A × 0.95
predicted_saturation_time = t0 - ln(A / actual_saturation_ratio - 1) / k
```

#### 2. 预警时间
```
warning_time = breakthrough_start_time + (predicted_saturation_time - breakthrough_start_time) × 0.8
```

### 算法特点
- **非固定阈值**: 预警点和饱和点都基于模型参数动态计算
- **时间跨度**: 预警点是时间跨度的80%位置，非固定穿透率
- **严格定义**: 完全按照算法中的数学公式计算

---

## 🎯 最佳实践

### 1. 数据质量控制
```python
# 确保数据按时间排序
data_points.sort(key=lambda p: p['x'])

# 检查数据合理性
for point in data_points:
    assert 0 <= point['y'] <= 100, "穿透率应在0-100%范围内"
    assert point['x'] > 0, "时间应为正数"
```

### 2. 错误处理
```python
try:
    response = requests.post(api_url, json=data)
    result = response.json()

    if 'error' in result:
        print(f"预警分析失败: {result['error']}")
        return None

    # 检查是否有预警点
    if 'warning_points' not in result or len(result['warning_points']) == 0:
        print("⚠️ 未生成预警点，可能数据不符合S型曲线特征")
        return None

except Exception as e:
    print(f"API调用异常: {e}")
```

### 3. 前端集成
```javascript
// 将API返回的预警点转换为图表标记
function convertToChartMarkers(warningPoints) {
    return warningPoints.map((point, index) => ({
        coord: [point.x, point.y],
        name: index === 0 ? '预警点' : '饱和点',
        symbol: 'diamond',
        symbolSize: index === 1 ? 18 : 15, // 饱和点更大
        itemStyle: {
            color: index === 0 ? 'orange' : 'red',
            borderColor: '#fff',
            borderWidth: 2
        },
        label: {
            show: true,
            position: 'top',
            formatter: index === 0 ?
                `预警点: ${point.x}h, ${point.y}%` :
                `饱和点: ${point.x}h, ${point.y}%`
        }
    }));
}
```

---

## 📞 技术支持

### 服务监控
- 健康检查: `GET /api/warning-prediction/health`
- 服务日志: 控制台输出
- 性能监控: 建议添加日志记录

### 常见问题
1. **Q**: 为什么只返回2个预警点？
   **A**: 接口严格按照算法定义，只返回预警点和饱和点的XY坐标

2. **Q**: 预警点的穿透率为什么不是固定的80%？
   **A**: 预警点是基于时间跨度的80%位置计算，穿透率由模型在该时间点预测得出

3. **Q**: 饱和点的穿透率为什么不是固定的90%？
   **A**: 饱和点是模型预测最大穿透率95%对应的时间点，穿透率基于模型参数动态计算

4. **Q**: 模型拟合失败怎么办？
   **A**: 检查数据是否呈现S型增长趋势，增加数据点数量，确保数据质量

5. **Q**: 如何提高预测准确性？
   **A**: 提供更多高质量数据点，确保数据覆盖穿透过程的各个阶段

---

**版本信息**: API v2.0.0 (简化版) | 文档更新: 2024年

## 📋 版本更新说明

### v2.0.0 (简化版)
- ✅ 严格按照算法定义计算预警点和饱和点
- ✅ 简化响应格式，仅返回XY坐标
- ✅ 移除session_id支持，专注核心功能
- ✅ 移除模型质量评估和未来预测功能
- ✅ 预警点基于时间跨度80%位置计算
- ✅ 饱和点基于模型最大穿透率95%计算

### v1.0.0 (完整版)
- 支持会话管理和模型信息查询
- 提供详细的模型质量评估
- 包含未来预测功能
- 复杂的响应格式
