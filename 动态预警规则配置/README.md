# 智能预警规则引擎

基于智算中心预警规则文档实现的精简高效预警系统，支持实时数据处理和智能预警判断。

## ⭐ 核心亮点

- **精简高效** - 核心算法仅250行，处理速度50+次/秒
- **功能完整** - 支持单属性、双属性规则和频率控制
- **标准兼容** - 完全符合智算中心文档规范
- **即插即用** - 基于配置文件，无需修改代码

## 📁 文件结构

| 文件 | 功能 | 推荐度 |
|------|------|--------|
| `compact_alarm_engine.py` | **精简预警引擎** | ⭐⭐⭐ |
| `demo_compact_engine.py` | 功能演示程序 | ⭐⭐ |
| `test_compact_engine.py` | 测试套件 | ⭐⭐ |
| `settings.toml` | 预警规则配置 | ⭐⭐⭐ |
| `alarm_rule_manager.py` | 配置管理器 | ⭐ |
| `alarm_rule_engine.py` | 原始引擎（对比用） | ⭐ |

## 🚀 快速开始

### 安装依赖

```bash
pip install dynaconf tomlkit
```

### 基础使用

```python
from compact_alarm_engine import CompactAlarmEngine

# 创建引擎并处理数据
engine = CompactAlarmEngine()
data = {'t1': 0.1, 't2': 25.8, 't3': 50.2, 't4': 2.1}
alarm = engine.process_data(data)

if alarm:
    print(f"🚨 {alarm['alarmInfo']['alarmRuleName']}")
else:
    print("✅ 数据正常")
```

### 运行演示

```bash
python demo_compact_engine.py    # 完整功能演示
python test_compact_engine.py    # 测试套件
```

## 📋 核心文件说明

### `compact_alarm_engine.py` ⭐ 精简预警引擎

**主要特点**:
- 250行精简代码，性能50+次/秒
- 支持单属性、双属性规则和频率控制
- 基于策略模式和工厂模式设计
- 完整类型注解，易于维护

**核心类**:
- `CompactAlarmEngine` - 主引擎
- `OperatorFactory` - 操作符处理
- `RuleEvaluator` - 规则评估
- `FrequencyManager` - 频率控制

### `settings.toml` 配置文件

**关键配置**:
```toml
[alarm_rule]
enabled = 1                     # 启用预警
alarmLevel = "HIGH"             # 预警等级

[device_alarm_config.singlePropertyRule]
property = "t1"                 # 监控属性
lowValue = 1                    # 最小阈值
highValue = 10                  # 最大阈值

[device_alarm_config.frequency]
accumulateCount = 5             # 累计5次异常触发
```

### 其他文件

- `demo_compact_engine.py` - 完整功能演示
- `test_compact_engine.py` - 测试套件（13个用例）
- `alarm_rule_manager.py` - 配置管理器
- `智算中心-预警规则文档.md` - 官方规范文档

## 📊 预警消息示例

触发预警时生成的标准JSON格式：

```json
{
  "alarmId": "999001",
  "alarmTime": "2025-09-24T16:43:10.783737",
  "data": {"t1": 0.1, "t2": 25.8, "t3": 50.2, "t4": 2.1},
  "alarmInfo": {
    "alarmRuleName": "新的温度异常预警",
    "alarmLevel": "HIGH",
    "alarmClazz": "DEVICE_ALARM",
    "triggeredRulesCount": 4,
    "triggeredRules": [...]
  }
}
```

## 🔧 主要API

```python
# 基础使用
engine = CompactAlarmEngine()
alarm = engine.process_data(data)
history = engine.get_alarm_history()

# 配置管理
manager = AlarmRuleManager()
manager.update_config({"alarm_rule.enabled": 1})
config = manager.get_fresh_config()
```

## 🛠️ 技术特点

- **Python 3.7+** 现代特性支持
- **策略模式** 操作符处理
- **工厂模式** 组件创建
- **类型安全** 完整注解
- **配置驱动** 无需修改代码

## 📞 支持

遇到问题请提供：Python版本、错误日志、配置文件、测试数据

---

**MIT License** | 基于智算中心预警规则文档实现
