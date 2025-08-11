# 抽取式吸附曲线预警系统HTTP接口

这是一个HTTP API接口，调用现有的`Adsorption_isotherm.py`算法处理VOC监测数据。接收JSON格式数据，通过算法计算穿透率，返回可视化所需的数据点坐标、标签，以及预警系统计算出的预警点坐标（对应图像中五角星标注的点）。

## 功能特点

- ✅ 调用现有`Adsorption_isotherm.py`算法
- ✅ JSON数据格式映射到算法期望的CSV列格式
- ✅ 返回数据点的X轴（时间）、Y轴（穿透率）和标签
- ✅ 返回预警系统计算的预警点坐标（图像中五角星标注的点）
- ✅ 数据验证和清洗
- ✅ 基于Logistic模型的预警分析

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动服务

```bash
python adsorption_api.py
```

服务将在 `http://localhost:5000` 启动

## API接口

### 1. 数据处理接口

**POST** `/api/extraction-adsorption-curve/process`

处理抽取式吸附曲线数据，返回穿透率坐标点和预测预警信息。

#### 请求格式

```json
[
  {
    "gvocs": 5.2,
    "invoc": 100.0,
    "gwindspeed": 10.5,
    "access": 0,
    "createTime": "2024-01-01T10:00:00"
  },
  {
    "gvocs": 5.8,
    "invoc": 0,
    "gwindspeed": 10.5,
    "access": 1,
    "createTime": "2024-01-01T10:01:00"
  }
]
```

#### 字段说明

- `gvocs`: 出口VOC浓度值 → 映射到算法的"出口voc"列
- `invoc`: 进口VOC浓度值 → 映射到算法的"进口voc"列
- `gwindspeed`: 风管内风速值 → 映射到算法的"风管内风速值"列
- `access`: 进口(0)或出口(1)标识 → 映射到算法的"进口0出口1"列
- `createTime`: 数据创建时间(ISO格式) → 映射到算法的"创建时间"列

#### 响应格式

```json
{
  "success": true,
  "data_points": [
    {
      "x": 0.5,
      "y": 5.8,
      "label": "时间段: 01-01 10:00-10:30\n累积时长: 0.50小时\n穿透率: 5.8%",
      "time_segment": "01-01 10:00-10:30",
      "cumulative_hours": 0.5,
      "breakthrough_percent": 5.8,
      "efficiency": 94.2,
      "inlet_concentration": 100.0,
      "outlet_concentration": 5.8
    }
  ],
  "warning_points": [
    {
      "x": 8.5,
      "y": 12.3,
      "type": "warning_star",
      "description": "预警系统计算的预警点（五角星标注）"
    },
    {
      "x": 15.2,
      "y": 18.7,
      "type": "saturation_star", 
      "description": "预测饱和点（五角星标注）"
    }
  ],
  "statistics": {
    "total_points": 25,
    "avg_breakthrough_ratio": 7.8,
    "min_breakthrough_ratio": 1.5,
    "max_breakthrough_ratio": 21.5,
    "avg_efficiency": 92.2,
    "min_efficiency": 78.5,
    "max_efficiency": 98.5,
    "time_span_hours": 24.0,
    "breakthrough_trend": "上升"
  },
  "model_info": {
    "model_fitted": true,
    "parameters": {
      "A": 0.95,
      "k": 0.15,
      "t0": 18.5
    },
    "breakthrough_start_time": 2.3,
    "predicted_saturation_time": 36.8,
    "warning_time": 29.7
  }
}
```

### 2. 健康检查接口

**GET** `/api/extraction-adsorption-curve/health`

检查服务状态。

### 3. API信息接口

**GET** `/api/extraction-adsorption-curve/info`

获取API详细信息和使用说明。

## 数据点标签说明

数据点标签采用算法内预警系统的标准格式：

```
时间段: MM-dd HH:mm-HH:mm
累积时长: X.XX小时  
穿透率: X.X%
```

标签包含三个关键信息：
- **时间段**: 数据采集的时间窗口
- **累积时长**: 从开始监测到当前点的累积运行时间
- **穿透率**: 当前时间段的穿透率百分比

## 预警点说明

预警点是由`Adsorption_isotherm.py`算法的预警系统计算出的关键点，对应可视化图像中的五角星标注：

- **warning_star**: 预警系统计算的预警点
- **saturation_star**: 预测饱和点

每个预警点包含：
- `x`: 预警时间点（小时）
- `y`: 对应的穿透率（%）
- `type`: 预警点类型
- `description`: 预警点描述

这些点是算法基于Logistic模型分析数据后确定的关键时间节点，用于指导吸附剂更换时机。

## 使用示例

### Python示例

```python
import requests
import json
from datetime import datetime

# 准备测试数据
test_data = [
    {
        "gvocs": 0,
        "invoc": 100.0,
        "gwindspeed": 10.0,
        "access": 0,
        "createTime": "2024-01-01T10:00:00"
    },
    {
        "gvocs": 5.0,
        "invoc": 0,
        "gwindspeed": 10.0,
        "access": 1,
        "createTime": "2024-01-01T10:01:00"
    }
]

# 发送请求
response = requests.post(
    'http://localhost:5000/api/extraction-adsorption-curve/process',
    json=test_data,
    headers={'Content-Type': 'application/json'}
)

# 处理响应
if response.status_code == 200:
    result = response.json()
    print(f"处理成功，数据点数量: {len(result['data_points'])}")
    print(f"预警点数量: {len(result['warning_points'])}")
else:
    print(f"处理失败: {response.json()}")
```

### JavaScript示例

```javascript
const testData = [
  {
    gvocs: 0,
    invoc: 100.0,
    gwindspeed: 10.0,
    access: 0,
    createTime: "2024-01-01T10:00:00"
  },
  {
    gvocs: 5.0,
    invoc: 0,
    gwindspeed: 10.0,
    access: 1,
    createTime: "2024-01-01T10:01:00"
  }
];

fetch('http://localhost:5000/api/extraction-adsorption-curve/process', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(testData)
})
.then(response => response.json())
.then(data => {
  console.log('处理结果:', data);
})
.catch(error => {
  console.error('错误:', error);
});
```

## 测试

运行测试脚本：

```bash
python test_api.py
```

测试脚本将自动生成模拟数据并测试所有API功能。

## 注意事项

1. 确保输入数据包含足够的进口和出口数据点对
2. 时间格式必须是ISO 8601格式
3. VOC浓度值应为非负数
4. 建议至少提供10个以上的数据点以获得更准确的预警分析
5. 服务默认运行在5000端口，可根据需要修改

## 错误处理

API会返回详细的错误信息，常见错误包括：

- 数据格式错误
- 缺少必要字段
- 数据质量不足
- 时间格式错误

## 技术架构

- **框架**: Flask
- **数据处理**: pandas, numpy
- **科学计算**: scipy
- **预警模型**: 基于Logistic回归的穿透预测
- **数据验证**: 自动清洗和质量检查
