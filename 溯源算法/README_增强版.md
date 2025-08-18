# 增强版污染源溯源算法系统

## 🎯 项目概述

本项目是一个基于遗传算法和高斯烟羽模型的增强版污染源溯源系统，能够通过传感器网络的浓度观测数据，反推污染源的位置和排放强度。

### ✨ 主要特点

- **🧮 多算法支持**: 标准遗传算法、自适应遗传算法、多目标优化算法
- **🎨 丰富可视化**: 2D/3D浓度场、交互式图表、动画演示
- **🌐 Web界面**: 用户友好的Streamlit Web界面
- **📊 综合分析**: 性能对比、误差分析、敏感性分析
- **📋 自动报告**: JSON格式的详细分析报告
- **⚡ 高性能**: 并行计算、缓存机制、自适应参数

## 📁 项目结构

```
溯源算法/
├── enhanced_pollution_tracing.py    # 增强版主控制器
├── enhanced_demo.py                 # 增强版演示脚本
├── enhanced_visualization.py        # 增强版可视化模块
├── web_interface.py                 # Web界面控制器
├── gaussian_plume_model.py          # 高斯烟羽模型
├── optimized_source_inversion.py    # 优化的反算算法
├── visualization_module.py          # 基础可视化模块
├── optimized_demo.py               # 基础演示脚本
├── enhanced_results/               # 结果输出目录
└── README_增强版.md                # 本文档
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 必需依赖包：
  ```bash
  pip install numpy pandas matplotlib seaborn plotly streamlit
  pip install scipy scikit-learn deap tqdm
  ```

### 安装步骤

1. **克隆或下载项目**
   ```bash
   git clone <repository-url>
   cd 溯源算法
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行演示**
   ```bash
   # 命令行演示
   python enhanced_demo.py
   
   # Web界面
   streamlit run web_interface.py
   ```

## 📖 使用指南

### 1. 命令行模式

#### 基础使用
```bash
# 交互式模式（推荐）
python enhanced_demo.py --mode interactive

# 自动运行所有场景
python enhanced_demo.py --mode auto

# 运行单一场景
python enhanced_demo.py --mode single --scenario standard
```

#### 场景选项
- `standard`: 标准场景（风速3.5m/s，源强2.5g/s）
- `high_wind`: 高风速场景（风速8.0m/s）
- `low_emission`: 低排放场景（源强1.0g/s）
- `complex`: 复杂场景（多参数变化）

### 2. Web界面模式

启动Web界面：
```bash
streamlit run web_interface.py
```

#### Web界面功能

1. **🎯 场景配置**
   - 污染源参数设置（位置、排放强度）
   - 气象条件配置（风速、风向、温度、湿度）
   - 传感器网络设置（网格大小、间距、噪声水平）
   - 算法参数调整（种群大小、迭代次数）

2. **🔬 算法分析**
   - 多算法并行运行
   - 实时进度显示
   - 结果摘要表格
   - 最佳算法推荐

3. **📊 结果可视化**
   - 算法性能对比
   - 浓度场分布图
   - 收敛过程曲线
   - 传感器分布图
   - 误差分析图表

4. **📋 报告生成**
   - 综合分析报告
   - 算法性能报告
   - 可视化报告
   - 技术文档

### 3. 编程接口

#### 基础使用示例

```python
from enhanced_pollution_tracing import EnhancedPollutionTracingSystem, EnhancedScenarioConfig

# 创建配置
config = EnhancedScenarioConfig(
    source_x=150.0, source_y=200.0, source_z=25.0,
    emission_rate=2.5, wind_speed=3.5, wind_direction=225.0,
    sensor_grid_size=7, noise_level=0.1,
    population_size=100, max_generations=2000
)

# 创建系统
system = EnhancedPollutionTracingSystem(config)

# 运行完整分析
results = system.run_complete_analysis("my_scenario")

# 查看结果
print(f"分析完成，总耗时: {results['total_time']:.2f}秒")
```

#### 高级配置示例

```python
# 自定义算法参数
from optimized_source_inversion import AdaptiveGAParameters

custom_params = AdaptiveGAParameters(
    population_size=150,
    max_generations=3000,
    adaptive_mutation=True,
    diversity_threshold=0.1,
    use_parallel=True,
    use_cache=True
)

# 创建反算器
from optimized_source_inversion import OptimizedSourceInversion
inverter = OptimizedSourceInversion(ga_parameters=custom_params)

# 运行反算
result = inverter.invert_source(sensor_data, meteo_data, verbose=True)
```

## 🔧 配置说明

### 场景配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `source_x` | float | 150.0 | 污染源X坐标 (m) |
| `source_y` | float | 200.0 | 污染源Y坐标 (m) |
| `source_z` | float | 25.0 | 污染源高度 (m) |
| `emission_rate` | float | 2.5 | 排放强度 (g/s) |
| `wind_speed` | float | 3.5 | 风速 (m/s) |
| `wind_direction` | float | 225.0 | 风向 (度) |
| `temperature` | float | 20.0 | 温度 (°C) |
| `humidity` | float | 60.0 | 湿度 (%) |
| `sensor_grid_size` | int | 7 | 传感器网格大小 |
| `sensor_spacing` | float | 100.0 | 传感器间距 (m) |
| `noise_level` | float | 0.1 | 噪声水平 (0-1) |

### 算法配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `population_size` | int | 100 | 遗传算法种群大小 |
| `max_generations` | int | 2000 | 最大迭代次数 |
| `use_parallel` | bool | True | 是否启用并行计算 |
| `use_cache` | bool | True | 是否启用缓存机制 |
| `adaptive_mutation` | bool | False | 是否启用自适应变异 |
| `diversity_threshold` | float | 0.1 | 多样性阈值 |

## 📊 输出结果

### 1. 可视化文件

系统会在 `enhanced_results/` 目录下生成以下文件：

- `{scenario}_浓度场对比.png`: 真实vs估计浓度场对比图
- `{scenario}_算法性能对比.png`: 各算法性能对比图
- `{scenario}_3D交互式分析.html`: 3D交互式可视化
- `{scenario}_收敛分析.html`: 算法收敛过程分析

### 2. 分析报告

JSON格式的综合分析报告包含：

```json
{
  "scenario_name": "场景名称",
  "timestamp": "分析时间",
  "true_source": {
    "x": 150.0,
    "y": 200.0,
    "z": 25.0,
    "emission_rate": 2.5
  },
  "algorithm_results": {
    "standard": {
      "position": [148.5, 201.2, 24.8],
      "emission_rate": 2.48,
      "position_error": 2.1,
      "emission_error": 0.8,
      "computation_time": 15.6,
      "objective_value": 1.23e-4
    }
  },
  "performance_summary": {
    "best_algorithm": "adaptive",
    "best_score": 3.2,
    "average_position_error": 2.5,
    "average_emission_error": 1.2
  },
  "recommendations": [
    "算法性能优秀，建议在实际应用中使用"
  ]
}
```

## 🎨 可视化功能

### 1. 静态图表

- **浓度场对比图**: 真实污染源vs各算法估计结果
- **算法性能对比**: 位置误差、源强误差、计算时间对比
- **传感器分布图**: 传感器位置及观测浓度分布
- **误差分析图**: 详细的误差统计和分析

### 2. 交互式可视化

- **3D浓度场**: 可旋转、缩放的3D浓度分布
- **收敛过程动画**: 算法收敛过程的动态展示
- **参数敏感性分析**: 交互式参数影响分析
- **综合仪表板**: 多维度数据展示面板

### 3. Web界面图表

- **实时更新图表**: 分析过程中的实时数据展示
- **可下载图表**: 支持PNG、HTML格式下载
- **响应式设计**: 适配不同屏幕尺寸

## ⚡ 性能优化

### 1. 并行计算

```python
# 启用并行计算
config = EnhancedScenarioConfig(use_parallel=True)

# 自定义并行参数
import multiprocessing
n_cores = multiprocessing.cpu_count()
# 系统会自动使用可用核心数
```

### 2. 缓存机制

```python
# 启用缓存（默认开启）
config = EnhancedScenarioConfig(use_cache=True)

# 缓存会自动存储计算结果，避免重复计算
```

### 3. 算法优化

```python
# 自适应参数调整
params = AdaptiveGAParameters(
    adaptive_mutation=True,      # 自适应变异率
    diversity_threshold=0.1,     # 多样性维持
    stagnation_threshold=50      # 停滞检测
)
```

## 🔍 故障排除

### 常见问题

1. **导入错误**
   ```bash
   # 确保所有依赖已安装
   pip install -r requirements.txt
   
   # 检查Python版本
   python --version  # 需要3.8+
   ```

2. **内存不足**
   ```python
   # 减少种群大小
   config.population_size = 50
   
   # 减少传感器数量
   config.sensor_grid_size = 5
   ```

3. **计算速度慢**
   ```python
   # 启用并行计算
   config.use_parallel = True
   
   # 减少迭代次数
   config.max_generations = 1000
   ```

4. **Web界面无法启动**
   ```bash
   # 检查Streamlit安装
   pip install streamlit
   
   # 指定端口启动
   streamlit run web_interface.py --server.port 8502
   ```

### 调试模式

```python
# 启用详细输出
result = inverter.invert_source(
    sensor_data, meteo_data, 
    verbose=True,           # 显示详细信息
    uncertainty_analysis=True  # 进行不确定性分析
)

# 查看收敛历史
print(result.convergence_history)

# 查看最终参数
print(f"最优解: ({result.source_x}, {result.source_y}, {result.source_z})")
print(f"源强: {result.emission_rate}")
```

## 📚 API参考

### 主要类

- `EnhancedPollutionTracingSystem`: 主控制器
- `EnhancedScenarioConfig`: 场景配置
- `EnhancedVisualizer`: 增强可视化器
- `WebInterface`: Web界面控制器

### 主要方法

- `create_scenario()`: 创建测试场景
- `run_enhanced_inversion()`: 运行多算法反算
- `create_comprehensive_visualization()`: 创建综合可视化
- `generate_comprehensive_report()`: 生成分析报告
- `run_complete_analysis()`: 运行完整分析流程

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！

### 开发环境设置

```bash
# 克隆项目
git clone <repository-url>
cd 溯源算法

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 代码规范

- 遵循PEP 8编码规范
- 添加适当的注释和文档字符串
- 编写单元测试
- 提交前运行代码检查

## 📄 许可证

本项目采用MIT许可证 - 查看LICENSE文件了解详情。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交GitHub Issue
- 发送邮件至：[your-email@example.com]

---

**🎯 开始使用增强版污染源溯源算法系统，体验智能环境监测的强大功能！**
