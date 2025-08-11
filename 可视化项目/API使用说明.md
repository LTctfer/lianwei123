# 抽取式吸附曲线预警系统API使用说明

## 概述
本API基于现有的 `Adsorption_isotherm.py` 算法，提供HTTP接口来处理VOC监测数据并返回可视化坐标点和预警信息。

## API接口

### 1. 数据处理接口
**URL:** `POST /api/extraction-adsorption-curve/process`

**输入格式 (JSON数组):**
```json
[
  {
    "gvocs": 12.5,      // 出口VOC浓度 (对应CSV中的"出口voc"列)
    "invoc": 150.0,     // 进口VOC浓度 (对应CSV中的"进口voc"列)  
    "gwindspeed": 1.2,  // 风管内风速 (对应CSV中的"风管内风速值"列)
    "access": 2,        // 状态值: 0=进口记录, 1=出口记录, 2=同时记录
    "createTime": "2024-01-01 10:00:00"  // 创建时间
  }
]
```

**输出格式:**
```json
{
  "success": true,
  "data_points": [
    {
      "x": 1.5,                    // X轴：累计运行时间（小时）
      "y": 25.3,                   // Y轴：穿透率（%）
      "label": "时间段: 风速段1\n累积时长: 1.50小时\n穿透率: 25.3%",
      "time_segment": "风速段1",    // 时间段标识
      "cumulative_hours": 1.5,     // 累计时长
      "breakthrough_percent": 25.3, // 穿透率百分比
      "efficiency": 74.7,          // 处理效率
      "inlet_concentration": 150.0, // 进口浓度
      "outlet_concentration": 37.9, // 出口浓度
      "calculation_rule": "规则1-风速段", // 计算规则
      "data_count": 12             // 该时间段的数据点数
    }
  ],
  "warning_points": [
    {
      "x": 8.2,                    // X轴：预警时间（小时）
      "y": 80.1,                   // Y轴：预警点穿透率（%）
      "type": "warning_star",       // 类型：预警点
      "color": "orange",           // 显示颜色
      "description": "预警点(穿透率:80.1%)"
    },
    {
      "x": 10.5,                   // X轴：饱和时间（小时）
      "y": 90.2,                   // Y轴：饱和点穿透率（%）
      "type": "saturation_star",    // 类型：饱和点
      "color": "red",              // 显示颜色
      "description": "预测饱和点(穿透率:90.2%)"
    }
  ],
  "total_points": 15
}
```

### 2. 健康检查接口
**URL:** `GET /api/extraction-adsorption-curve/health`

### 3. API信息接口
**URL:** `GET /api/extraction-adsorption-curve/info`

## 数据说明

### access字段含义
- `0`: 进口记录 - 该条数据记录的是进口浓度
- `1`: 出口记录 - 该条数据记录的是出口浓度  
- `2`: 同时记录 - 该条数据同时包含进口和出口浓度

### 算法处理逻辑
1. **数据类型识别**: 根据access字段值自动识别数据类型
   - 同时记录型 (access=2): 每条记录同时包含进出口浓度
   - 切换型 (access=0,1): 进出口数据分别记录，需要匹配时间段

2. **数据清洗**: 
   - 风速切分：根据风速>=0.5进行时间段划分
   - 异常值清理：去除浓度为0、出口>进口等异常数据
   - K-S检验和箱型图清洗

3. **效率计算**: 
   - 规则1：按风速段计算效率（适用于同时记录型）
   - 规则2：按拼接段计算效率（适用于切换型）

4. **预警分析**: 
   - 使用Logistic模型拟合穿透曲线
   - 计算预警时间点（起始到饱和的80%）
   - 生成预警点坐标（五角星标注）

## 返回数据详解

### 数据点 (data_points)
- **x**: 累计运行时间（小时），从数据开始时间计算
- **y**: 穿透率（%），出口浓度/进口浓度 × 100
- **label**: 包含时间段、累计时长、穿透率的完整标签
- **time_segment**: 时间段标识（如"风速段1"、"拼接段2"）

### 预警点 (warning_points)
- **warning_star**: 橙色五角星，预警时间点
- **saturation_star**: 红色五角星，预测饱和点
- **breakthrough_start**: 绿色标记，穿透起始点

## 使用示例

### 启动服务器
```bash
cd 可视化项目
python adsorption_api.py
```

### 测试API
```bash
python test_adsorption_api.py
```

### 调用示例 (Python)
```python
import requests
import json

# 准备测试数据
test_data = [
    {
        "gvocs": 15.2,
        "invoc": 120.5,
        "gwindspeed": 1.1,
        "access": 2,
        "createTime": "2024-01-01 10:00:00"
    }
    # ... 更多数据点
]

# 调用API
response = requests.post(
    "http://localhost:5000/api/extraction-adsorption-curve/process",
    json=test_data
)

if response.status_code == 200:
    result = response.json()
    if result["success"]:
        print(f"数据点数: {len(result['data_points'])}")
        print(f"预警点数: {len(result['warning_points'])}")
    else:
        print(f"处理失败: {result['error']}")
```

## 注意事项

1. **数据量**: 建议单次处理数据点不超过1000个
2. **时间格式**: createTime支持 "YYYY-MM-DD HH:MM:SS" 格式
3. **数据质量**: 确保进口浓度 > 出口浓度，否则会被清洗掉
4. **预警模型**: 需要足够的数据点才能成功拟合Logistic模型
5. **计算规则**: API会自动选择最适合的计算规则（风速段或拼接段）

## 错误处理

常见错误及解决方案：
- `缺少必要字段`: 检查JSON数据是否包含所有必需字段
- `数据加载失败`: 检查数据格式和数值范围
- `无法计算效率数据`: 数据清洗后无有效数据，检查数据质量
- `模型拟合失败`: 数据点不足或分布不合理，无法生成预警点
