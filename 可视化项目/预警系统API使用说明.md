# 预警系统API使用说明

## 🎯 接口概述

预警系统预测接口专门用于接收累计的时间-穿透率数据点，调用Logistic预警系统算法进行拟合，**仅返回五角星标记的预警点坐标**（橙色预警点、红色饱和点）。

### 核心功能
- ⭐ **预警点分析**: 返回橙色五角星标记的预警点坐标
- ⭐ **饱和点预测**: 返回红色五角星标记的预测饱和点坐标
- 📊 **模型质量评估**: 提供拟合质量指标（R²、RMSE等）
- 🔮 **未来预测**: 基于拟合模型预测未来时间点的穿透率

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
  "session_id": "可选的会话ID",
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
- `session_id` (可选): 会话标识符，用于保存模型便于后续预测
- `data_points` (必需): 累计数据点数组
  - `x`: 累计时间（单位：小时）
  - `y`: 穿透率（单位：百分比，0-100%）

**支持的字段格式**:
- 标准格式: `x`, `y`
- 时间格式: `time`, `breakthrough_ratio`
- 中文格式: `cumulative_time`, `穿透率`

#### 响应格式
```json
{
  "status": "success",
  "warning_points": [
    {
      "type": "warning_star",
      "name": "预警点",
      "x": 6.25,
      "y": 76.8,
      "color": "orange",
      "symbol": "star",
      "description": "预警点: 76.8%穿透率，建议适时更换"
    },
    {
      "type": "saturation_star", 
      "name": "预测饱和点",
      "x": 8.45,
      "y": 90.0,
      "color": "red",
      "symbol": "star",
      "description": "预测饱和点: 90.0%穿透率，建议立即更换"
    }
  ],
  "model_info": {
    "fitted": true,
    "parameters": {
      "A": 0.95,
      "k": 0.8,
      "t0": 5.0
    },
    "quality_metrics": {
      "rmse": 0.025,
      "r_squared": 0.985,
      "mean_absolute_error": 0.018
    },
    "predictions": {
      "breakthrough_start_hours": 0.85,
      "warning_time_hours": 6.25,
      "saturation_time_hours": 8.45
    }
  },
  "data_summary": {
    "input_points": 5,
    "time_range_hours": {"start": 1.5, "end": 7.5},
    "breakthrough_range_percent": {"start": 12.5, "end": 85.3}
  }
}
```

### 2. 辅助接口

#### 模型信息查询
```
GET /api/warning-prediction/model/{session_id}
```

#### 未来预测
```
POST /api/warning-prediction/predict
```
请求:
```json
{
  "session_id": "会话ID",
  "future_hours": [10.0, 12.0, 15.0]
}
```

#### 健康检查
```
GET /api/warning-prediction/health
```

#### API信息
```
GET /api/warning-prediction/info
```

---

## ⭐ 预警点说明

### 1. 预警点 (warning_star)
- **颜色**: 🟠 橙色
- **标记**: ⭐ 五角星
- **含义**: 达到预警阈值的时间点（80%穿透率）
- **建议**: 适时更换吸附材料
- **示例**: `{"x": 6.25, "y": 76.8, "color": "orange"}`

### 2. 预测饱和点 (saturation_star)
- **颜色**: 🔴 红色  
- **标记**: ⭐ 五角星
- **含义**: 预测达到饱和的时间点（90%穿透率）
- **建议**: 立即更换吸附材料
- **示例**: `{"x": 8.45, "y": 90.0, "color": "red"}`

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

# 发送请求
request_data = {
    "session_id": "production_001",
    "data_points": accumulated_data
}

response = requests.post(
    api_url,
    json=request_data,
    headers={'Content-Type': 'application/json; charset=utf-8'}
)

if response.status_code == 200:
    result = response.json()
    
    # 提取五角星预警点
    warning_points = result['warning_points']
    
    print("🌟 预警点分析结果:")
    for point in warning_points:
        print(f"  {point['name']}: X={point['x']}h, Y={point['y']}%")
        print(f"  颜色: {point['color']}, 描述: {point['description']}")
        
        # 根据类型处理不同预警点
        if point['type'] == 'warning_star':
            # 橙色预警点 - 建议准备更换
            orange_star_x = point['x']
            orange_star_y = point['y']
            print(f"  🟠 预警: {orange_star_x}小时处达到{orange_star_y}%穿透率")
            
        elif point['type'] == 'saturation_star':
            # 红色饱和点 - 必须更换
            red_star_x = point['x']
            red_star_y = point['y']
            print(f"  🔴 饱和: {red_star_x}小时处预计达到{red_star_y}%穿透率")
    
    # 检查模型质量
    model_quality = result['model_info']['quality_metrics']['r_squared']
    print(f"\n📊 模型拟合质量: R² = {model_quality:.3f}")
    
    if model_quality > 0.9:
        print("✅ 模型拟合优秀，预警点可信度高")
    elif model_quality > 0.8:
        print("✅ 模型拟合良好，预警点较可信")
    else:
        print("⚠️ 模型拟合一般，预警点仅供参考")

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

// 调用预警分析API
async function analyzeWarningPoints() {
    const requestData = {
        session_id: 'web_session_001',
        data_points: accumulatedData
    };

    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(requestData)
        });

        const result = await response.json();
        
        if (result.status === 'success') {
            // 处理五角星预警点
            const warningPoints = result.warning_points;
            
            warningPoints.forEach(point => {
                console.log(`${point.name}: X=${point.x}, Y=${point.y}, 颜色=${point.color}`);
                
                // 在图表上添加五角星标记
                if (point.type === 'warning_star') {
                    // 添加橙色五角星
                    addWarningStarToChart(point.x, point.y, 'orange');
                    showWarningNotification(point.description);
                    
                } else if (point.type === 'saturation_star') {
                    // 添加红色五角星
                    addWarningStarToChart(point.x, point.y, 'red');
                    showCriticalNotification(point.description);
                }
            });
            
            // 显示模型质量
            const modelQuality = result.model_info.quality_metrics.r_squared;
            console.log(`模型拟合质量: R² = ${modelQuality.toFixed(3)}`);
            
            // 更新UI显示预警信息
            updateWarningUI(warningPoints);
            
        } else {
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
        name: '预警点',
        coord: [x, y],
        symbol: 'diamond', // 或其他星形符号
        symbolSize: 15,
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
# 发送预警分析请求
curl -X POST "http://localhost:5001/api/warning-prediction/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "curl_test_001",
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
  "status": "failure", 
  "error": "预警模型拟合失败，数据可能不符合S型曲线特征"
}
```

#### 3. 数据格式错误
```json
{
  "status": "failure",
  "error": "数据格式错误或为空"
}
```

#### 4. 服务器错误
```json
{
  "status": "error",
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

### 预警阈值
- **预警点**: 80%穿透率 → 橙色五角星⭐
- **饱和点**: 90%穿透率 → 红色五角星⭐

### 质量评估指标
- **R²**: 决定系数（0-1，越接近1越好）
- **RMSE**: 均方根误差（越小越好）
- **MAE**: 平均绝对误差

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
    
    if result['status'] != 'success':
        print(f"预警分析失败: {result['error']}")
        return None
        
    # 检查模型质量
    r_squared = result['model_info']['quality_metrics']['r_squared']
    if r_squared < 0.8:
        print("⚠️ 模型拟合质量较低，预警点可信度有限")
        
except Exception as e:
    print(f"API调用异常: {e}")
```

### 3. 前端集成
```javascript
// 将API返回的预警点转换为图表标记
function convertToChartMarkers(warningPoints) {
    return warningPoints.map(point => ({
        coord: [point.x, point.y],
        name: point.name,
        symbol: 'diamond',
        symbolSize: point.type === 'saturation_star' ? 18 : 15,
        itemStyle: {
            color: point.color,
            borderColor: '#fff',
            borderWidth: 2
        },
        label: {
            show: true,
            position: 'top',
            formatter: point.description
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
   **A**: 接口专门设计为只返回五角星标记的关键预警点（橙色预警、红色饱和）

2. **Q**: 模型拟合失败怎么办？
   **A**: 检查数据是否呈现S型增长趋势，增加数据点数量，确保数据质量

3. **Q**: 如何提高预测准确性？
   **A**: 提供更多高质量数据点，确保数据覆盖穿透过程的各个阶段

---

**版本信息**: API v1.0.0 | 文档更新: 2024年
