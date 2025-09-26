# 智能预警引擎 - 精简版

基于智算中心预警规则文档的通用预警算法，单文件解决方案，易于维护和部署。

## 🎯 核心特点

- **单文件解决方案**: 所有功能集成在一个文件中，易于维护
- **完全配置驱动**: 所有参数通过配置文件动态调整
- **平台集成友好**: 支持标准MQTT格式的配置下发和预警推送
- **智能频率控制**: 累积异常和连续异常两种模式
- **内置测试演示**: 自带测试和演示功能，无需额外文件

## 📁 项目结构

```
lianwei123\动态预警规则配置\
├── smart_alarm.py               # 智能预警引擎主文件 (250行)
├── config.toml                  # 预警配置文件
├── 智算中心-预警规则文档.md        # 官方规范文档
└── README.md                    # 项目说明文档
```

## 🚀 快速开始

### 1. 运行测试

```bash
# 运行自测试
python smart_alarm.py test

# 运行演示
python smart_alarm.py demo

# 默认运行（自测试）
python smart_alarm.py
```

### 2. 基础使用

```python
from smart_alarm import SmartAlarmEngine

# 创建引擎实例
engine = SmartAlarmEngine()

# 处理数据
data = {'t1': 0.5, 't2': 25, 't3': 50, 't4': 5}
alarm = engine.process_data(data)

if alarm:
    print(f"触发预警: {alarm['alarmId']}")
    # 推送到平台
    engine.push_alarm(alarm, "device_001")
```

### 3. 平台配置下发

```python
# 接收平台配置命令
platform_command = {
    "commandType": "ALARM_RULE",
    "data": {
        "alarmRuleId": "123456",
        "alarmRuleName": "温度异常预警",
        "alarmClazz": "DEVICE_ALARM",
        "alarmLevel": "HIGH",
        "enabled": 1
    }
}

result = engine.receive_platform_command(platform_command)
print(f"配置更新: {result['message']}")
```

## 🔧 核心功能

### 1. 预警规则评估
- **单属性规则**: 支持OR/AND逻辑，所有比较操作符 (lt, le, eq, gt, ge, ne)
- **双属性规则**: 支持两个属性间的比较操作

### 2. 频率控制机制
- **累积模式**: 时间窗口内累积异常次数，达到阈值触发预警
- **连续模式**: 统计连续异常次数，正常数据重置计数

### 3. 配置管理
- **实时更新**: 配置修改立即生效
- **平台下发**: 支持标准JSON格式配置命令
- **动态调整**: 所有参数均可通过配置文件修改

### 4. 预警消息推送
标准MQTT格式推送到 `qixiu/warning_data/{设备编号}`:
```json
{
  "alarmId": "123456",
  "alarmTime": "2025-09-26 10:30:00",
  "data": {"t1": 0.5, "t2": 25}
}
```

## 📊 配置文件格式 (config.toml)

```toml
[alarm_rule]
alarmRuleId = "123456"
alarmRuleName = "智能预警规则"
alarmClazz = "DEVICE_ALARM"  # DEVICE_ALARM | ENTERPRISE_ALARM
alarmLevel = "HIGH"          # LOW | MEDIUM | HIGH | CRITICAL
enabled = 1                  # 0:禁用, 1:启用
startTime = "00:00"         # 预警开始时间
endTime = "23:59"           # 预警结束时间

[device_alarm_config]
# 单属性规则
[[device_alarm_config.singlePropertyRule]]
symbol = "OR"               # AND | OR
property = "t1"
lowValue = 1
expression1 = "lt"          # lt | le | eq | gt | ge | ne
highValue = 10
expression2 = "gt"

# 双属性规则
[[device_alarm_config.doublePropertyRule]]
symbol = "AND"
leftProperty = "t1"
rightProperty = "t2"
expression = "lt"

# 频率控制
[device_alarm_config.frequency]
enabled = 1
hasAccumulate = 1           # 1:累积模式, 0:连续模式
accumulateCount = 3         # 累积异常次数
accumulateTimeRange = 30    # 累积时间范围(分钟)
continuousCount = 3         # 连续异常次数
```

## 🧪 测试和演示

### 内置功能

```bash
# 运行自测试 - 验证所有核心功能
python smart_alarm.py test

# 运行演示 - 展示预警处理流程
python smart_alarm.py demo

# 默认运行自测试
python smart_alarm.py
```

### 测试覆盖
- ✅ 基础预警功能测试
- ✅ 配置动态修改测试
- ✅ 频率控制机制测试
- ✅ 平台命令处理测试
- ✅ 预警消息推送测试

## 🔌 平台集成

### 配置下发接口
MQTT主题: `command/{设备编号}`
```json
{
  "commandType": "ALARM_RULE",
  "data": {
    "alarmRuleId": "123456",
    "alarmRuleName": "温度异常预警",
    "alarmClazz": "DEVICE_ALARM",
    "alarmLevel": "HIGH"
  }
}
```

### 预警上报接口
MQTT主题: `qixiu/warning_data/{设备编号}`
```json
{
  "alarmId": "123456",
  "alarmTime": "2025-09-26 10:30:00",
  "data": {"t1": 0.5, "t2": 25}
}
```

## 📈 性能特点

- **代码量**: 250行，易于维护
- **处理速度**: 高性能数据处理
- **内存占用**: 轻量级设计
- **响应时间**: 毫秒级预警响应
- **配置更新**: 实时生效

## 🎉 项目优势

1. **单文件解决方案** - 所有功能集成在一个文件中
2. **易于维护** - 代码结构清晰，逻辑简单
3. **快速部署** - 无复杂依赖，即拷即用
4. **功能完整** - 涵盖所有预警需求
5. **内置测试** - 自带测试和演示功能

## 📄 许可证

MIT License
