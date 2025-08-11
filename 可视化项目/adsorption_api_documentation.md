## 吸附曲线预警系统 API 文档 (Markdown)

### 概述
- 位置: `可视化项目/adsorption_api.py`
- 作用: 基于吸附曲线数据完成加载→清洗→效率/穿透率计算→Logistic 预警拟合→输出绘图数据点与预警点
- 支持数据源: CSV / XLSX / XLS
- 时间单位: 小时（内部会从秒等字段统一转换）
- 穿透率: 以百分比返回（0–100）

### 环境与依赖
- Python 3.8+
- 依赖: pandas, numpy, scipy

---

## 公共接口

### get_warning_system_data
- 签名: `get_warning_system_data(data_file: str) -> Dict[str, Any]`
- 说明: 推荐主入口。完成数据处理与预警分析，直接返回绘图数据和预警点、统计信息
- 参数
  - `data_file`: 数据文件路径（CSV/XLSX/XLS）
- 返回
  - `success`: bool
  - `data_points`: List
    - `x`: float 时间（小时）
    - `y`: float 穿透率（%）
    - `label`: str 描述（包含进口/出口平均、穿透率、效率等）
  - `warning_point`: Object
    - `time`: Optional[float] 预警时间（小时）
    - `breakthrough_rate`: Optional[float] 预警穿透率（%）
    - `description`: Optional[str]
  - `statistics`: Object
    - `total_data_points`: int
    - `has_warning_point`: bool
    - `time_range`: { min?: float, max?: float }
    - `breakthrough_range`: { min?: float, max?: float }
  - 失败时:
    - `error`: str
    - `data_points`: []
    - `warning_point`: { time: None, breakthrough_rate: None, description: None }
    - `statistics`: {}

示例 (Python)
```python
from adsorption_api import get_warning_system_data

res = get_warning_system_data("可视化项目/7.24.csv")
if res["success"]:
    print(len(res["data_points"]))
    print(res["warning_point"])
else:
    print("error:", res["error"])
```

返回示例 (JSON)
```json
{
  "success": true,
  "data_points": [
    {
      "x": 0.5,
      "y": 12.3,
      "label": "t=0.50h: 进口=1.23, 出口=0.15, 穿透率=12.3%, 效率=87.7%"
    }
  ],
  "warning_point": {
    "time": 5.75,
    "breakthrough_rate": 80.1,
    "description": "预警点(穿透率: 80.1%)"
  },
  "statistics": {
    "total_data_points": 36,
    "has_warning_point": true,
    "time_range": { "min": 0.0, "max": 12.0 },
    "breakthrough_range": { "min": 3.2, "max": 85.4 }
  }
}
```

---

### analyze_adsorption_data
- 签名: `analyze_adsorption_data(data_file: str) -> Dict[str, Any]`
- 说明: 一键分析（复用预警主流程），统一输出“绘图数据 + 预警点 + 摘要”
- 参数
  - `data_file`: 数据文件路径（CSV/XLSX/XLS）
- 返回
  - `success`: bool
  - `all_data_points`: List
    - `x`: float 时间（小时）
    - `y`: float 穿透率（%）
    - `label`: str
    - `type`: "时间段穿透率"
    - `data_category`: "breakthrough"
  - `warning_points`: List（若存在）
    - `x`: float 预警时间（小时）
    - `y`: float 预警穿透率（%）
    - `warning_level`: "预警点"
    - `reason`: str
    - `recommendation`: str
    - `color_code`: "#FFA500"
  - `statistics`: 同上
  - `data_summary`:
    - `total_points`: int
    - `warning_count`: int
    - `data_types`: List[str]
    - `time_range`: { min?: float, max?: float }
  - 失败时:
    - `error`: str
    - 其余为空

示例 (Python)
```python
from adsorption_api import analyze_adsorption_data

res = analyze_adsorption_data("可视化项目/7.24.csv")
if res["success"]:
    print(res["data_summary"])
    print(res["warning_points"])
```

---

### create_adsorption_api
- 签名: `create_adsorption_api(data_file: str) -> AdsorptionAPI`
- 说明: 返回 `AdsorptionAPI` 实例，便于自定义或调试

示例
```python
from adsorption_api import create_adsorption_api

api = create_adsorption_api("可视化项目/7.24.csv")
result = api.analyze_warning_system()
print(result["statistics"])
```

---

## AdsorptionAPI 类（简要）
- 初始化: `AdsorptionAPI(data_file: str)`
  - `data_file`: 输入文件路径
  - `processor`: `Adsorption_isotherm.AdsorptionCurveProcessor` 实例
- 方法
  - `analyze_warning_system() -> Dict[str, Any]`
    - 完整预警流程，返回结构与 `get_warning_system_data` 内部一致（`data_points`, `warning_point`, `statistics`）
- 提示
  - 文件中 `get_data_points_by_type` / `get_warning_points_by_level` / `export_results_to_dict` 依赖内部 `self.analysis_result`，当前公开入口建议用上述三个公共函数

---

## 数据与字段约定
- **时间 (x)**: 小时（从 `时间(s)`/`时间`/`时间坐标` 等字段统一对齐）
- **穿透率 (y)**: 百分比（0–100）
  - 若记录中有 `breakthrough_ratio` 或 `穿透率`（0–1），自动 ×100
  - 若缺失，则由效率推算: y = 100 - efficiency(%)
- **标签 (label)**: 格式为
  - `t={x:.2f}h: 进口={inlet:.2f}, 出口={outlet:.2f}, 穿透率={y:.1f}%, 效率={eff:.1f}%`
- **预警点**:
  - Logistic 拟合得到 `warning_time`，用 `predict_breakthrough(warning_time)` 得 `breakthrough_rate(%)`

---

## 输入数据列（常见/兼容）
- **时间**: `时间坐标`(小时) 或 `时间(s)`/`时间`(秒)
- **浓度**: `进口浓度` / `出口浓度` 或 `进口voc` / `出口voc`
- **穿透率(可选)**: `breakthrough_ratio` / `穿透率`（0–1）
- **效率(可选)**: `efficiency` / `处理效率`（0–100）

---

## 错误与排障
- **数据加载失败/清洗后无数据**: 检查文件路径与必需列是否存在
- **无预警点**: 模型拟合或触发条件不满足，属正常
- **穿透率异常**: 核对进口浓度是否为零或异常；算法对明显异常穿透率点会过滤

---

## 端到端示例
```python
from adsorption_api import get_warning_system_data

data_file = "可视化项目/7.24.csv"
res = get_warning_system_data(data_file)

if res["success"]:
    # 绘图数据
    points = res["data_points"]
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    labels = [p["label"] for p in points]

    # 预警点
    wp = res["warning_point"]
    if wp["breakthrough_rate"] is not None:
        print("预警时间(h):", wp["time"])
        print("预警穿透率(%):", wp["breakthrough_rate"])
else:
    print("错误:", res["error"])
```

---

## 版本与维护
- **API 文件**: `可视化项目/adsorption_api.py`
- **依赖文件**: `可视化项目/Adsorption_isotherm.py`
- **建议入口**: `get_warning_system_data`（绘图/看板最小集字段齐备）
- **最后更新**: 以代码库为准


