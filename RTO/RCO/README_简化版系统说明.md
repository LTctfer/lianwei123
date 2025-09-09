# RTO/RCO废气处理设备预警系统 - 精简版

## 📋 系统概述

这是一个用于监控RTO/RCO废气处理设备的智能预警系统，提供实时数据监控、异常检测和可视化大屏展示功能。

### 🎯 主要功能

- **实时数据监控**: 监控燃烧室温度、出口浓度、系统压力等关键参数
- **智能预警检测**: 基于预设规则自动检测异常情况并发出告警
- **现代化大屏**: 提供美观的Web监控界面，支持实时数据更新
- **历史数据分析**: 支持播放历史数据文件进行回溯分析
- **设备状态跟踪**: 实时显示各设备组件的运行状态

## 🏗️ 系统架构

```
RTO预警系统
├── DataGenerator (数据生成器)
│   ├── 模拟实时设备数据
│   └── 生成异常数据触发告警
├── RuleEngine (规则引擎)
│   ├── 预警规则定义
│   └── 异常检测逻辑
├── WebDashboard (监控大屏)
│   ├── Web服务器
│   ├── 实时数据API
│   └── 现代化界面
└── SimpleFilePlayer (文件播放器)
    ├── 历史数据播放
    └── 文件预览功能
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖包
pip install pandas numpy matplotlib
```

### 2. 启动系统

```bash
# 运行精简版系统
python simplified_warning_system.py
```

### 3. 访问监控大屏

系统启动后会自动打开浏览器，访问地址：`http://localhost:8090`

## 📊 监控参数说明

### 核心参数
- **燃烧室温度**: 正常范围 ≥760℃，低于此值触发高级告警
- **处理效率**: 正常范围 ≥90%，低于此值说明处理效果不佳
- **进口浓度**: 待处理废气的污染物浓度

### 温度监控
- **出口温度**: 正常范围 ≤60℃，超出触发中级告警
- **吸附温度**: 吸附设施运行温度
- **脱附温度**: 脱附设施运行温度
- **反应器温度**: 正常范围 ≤600℃，超出触发严重告警

### 浓度分析
- **出口浓度**: 正常范围 ≤50mg/m³，超出触发严重告警
- **系统压力**: 设备运行压力
- **流量**: 废气处理流量
- **应急阀门**: 正常状态为关闭

## ⚙️ 预警规则

| 规则ID | 规则名称 | 触发条件 | 严重程度 | 说明 |
|--------|----------|----------|----------|------|
| R001 | 燃烧室温度不达标 | <760℃ | 高级 | 燃烧室温度过低影响处理效果 |
| R002 | 废气出口浓度超标 | >50mg/m³ | 严重 | 出口污染物浓度超过排放标准 |
| R003 | 出口温度超标 | >60℃ | 中级 | 废气出口温度过高 |
| R004 | 反应器温度异常 | >600℃ | 严重 | 反应器温度过高存在安全风险 |
| R005 | 应急阀门违规开启 | =开启 | 严重 | 应急阀门不应在正常运行时开启 |

## 🎨 界面特色

### 现代化设计
- **科技感背景**: 动态网格背景营造科技氛围
- **渐变色彩**: 蓝色系渐变色彩搭配
- **动画效果**: 平滑的悬停和状态变化动画
- **响应式布局**: 支持不同屏幕尺寸自适应

### 实时更新
- **2秒刷新**: 每2秒自动更新所有监控数据
- **状态指示**: 实时设备状态指示灯
- **告警提醒**: 异常情况立即高亮显示
- **趋势图表**: 实时绘制数据变化趋势

## 📁 文件结构

```
RTO/RCO/
├── simplified_warning_system.py    # 主系统文件
├── simple_file_player.py          # 文件播放器
├── README_简化版系统说明.md        # 说明文档
└── 可视化结果/                     # 输出目录
    ├── cleaning_compare_*.png      # 数据清洗对比图
    └── violation_report_*.xlsx     # 违规报告
```

## 🔧 自定义配置

### 修改预警阈值

在 `RuleEngine._init_rules()` 方法中修改规则配置：

```python
{
    'id': 'R001',
    'name': '燃烧室温度不达标',
    'field': 'temperature_combustion',
    'condition': 'less_than',
    'threshold': 760,  # 修改这里的阈值
    'unit': '℃',
    'severity': 'high'
}
```

### 调整数据更新频率

在HTML中修改JavaScript定时器间隔：

```javascript
setInterval(fetchData, 2000); // 修改这里的毫秒数
```

### 自定义界面颜色

在CSS样式中修改颜色变量：

```css
:root {
    --primary-color: #00d4ff;    /* 主色调 */
    --accent-color: #00ffff;     /* 强调色 */
    --warning-color: #ffaa00;    /* 警告色 */
    --critical-color: #ff4444;   /* 严重色 */
}
```

## 🐛 故障排除

### 常见问题

1. **端口被占用**
   - 错误: `[Errno 10048] Only one usage of each socket address`
   - 解决: 修改 `WebDashboard.__init__()` 中的端口号

2. **依赖包缺失**
   - 错误: `ModuleNotFoundError: No module named 'pandas'`
   - 解决: 运行 `pip install pandas numpy matplotlib`

3. **浏览器无法访问**
   - 检查防火墙设置
   - 确认端口8090未被其他程序占用
   - 尝试使用 `127.0.0.1:8090` 访问

### 调试模式

在代码中添加调试信息：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 扩展功能

### 添加新的监控参数

1. 在 `DataGenerator.generate_data()` 中添加新参数
2. 在 `RuleEngine._init_rules()` 中添加对应规则
3. 在HTML界面中添加显示元素
4. 在JavaScript中添加更新逻辑

### 集成真实数据源

替换 `DataGenerator` 为真实的数据接口：

```python
class RealDataSource:
    def get_data(self):
        # 从PLC、数据库或API获取真实数据
        return real_data
```

## 📞 技术支持

如有问题或建议，请通过以下方式联系：

- 📧 邮箱: support@example.com
- 🐛 问题反馈: GitHub Issues
- 📚 技术文档: Wiki页面

---

**版本**: 2.0 (精简版)  
**更新时间**: 2024-01-15  
**作者**: AI Assistant
