# 智算中心预警规则配置 - MQTT实现

## 概述

本项目实现了基于MQTT的智能预警规则配置系统，支持通过MQTT动态接收和更新预警规则配置，并按照智算中心文档要求的格式进行预警上报。

## 主要功能

1. **MQTT规则配置接收** - 通过 `command/{设备编号}` 主题接收ALARM_RULE命令
2. **配置文件动态更新** - 将接收到的规则配置转换并保存到配置文件
3. **预警生成和上报** - 按照文档格式通过 `RTO/warning_data/{设备编号}` 主题上报预警

## 修改内容

### 1. MQTT主题调整

**配置文件 (config.toml)**
```toml
[mqtt.topics]
# 按照智算中心文档要求的主题格式
command_topic = "command/{device_id}"
alarm_topic = "RTO/warning_data/{device_id}"
status_feedback = "smart_alarm/status/feedback/{device_id}"
```

### 2. ALARM_RULE命令处理

**支持的命令格式**
```json
{
  "commandType": "ALARM_RULE",
  "data": {
    "alarmRuleId": "123456",
    "alarmRuleName": "温度异常预警",
    "alarmClazz": "DEVICE_ALARM",
    "alarmLevel": "HIGH",
    "enabled": 1,
    "startTime": "08:00",
    "endTime": "18:00",
    "config": "{\"singlePropertyRule\":[...], \"frequency\":{...}}"
  }
}
```

### 3. 预警上报格式

**按照文档要求的格式**
```json
{
  "alarmId": "123456",
  "alarmTime": "2025-09-09 11:11:11",
  "data": {"t1": 0.5, "t2": 15}
}
```

## 使用方法

### 1. 启动预警引擎

```bash
python mqtt_smart_alarm.py
# 选择选项 2 - 启动预警引擎
```

### 2. 发送ALARM_RULE命令

```python
from mqtt_smart_alarm import MQTTBackendSimulator
import json

# 创建后端模拟器
backend = MQTTBackendSimulator(device_id="device_001")
backend.connect()

# 发送预警规则配置
alarm_rule_data = {
    "alarmRuleId": "RULE_001",
    "alarmRuleName": "温度预警",
    "alarmClazz": "DEVICE_ALARM",
    "alarmLevel": "HIGH",
    "enabled": 1,
    "config": json.dumps({
        "singlePropertyRule": [{
            "symbol": "OR",
            "property": "temperature",
            "lowValue": 0,
            "expression1": "lt",
            "highValue": 50,
            "expression2": "gt"
        }],
        "frequency": {
            "enabled": 1,
            "hasAccumulate": 1,
            "accumulateCount": 3,
            "accumulateTimeRange": 30
        }
    })
}

backend.send_alarm_rule_command(alarm_rule_data)
```

### 3. 测试预警生成

```python
from mqtt_smart_alarm import MQTTSmartAlarm

# 创建预警引擎
alarm = MQTTSmartAlarm(device_id="device_001")
alarm.connect()
alarm.start_sender()

# 处理数据
test_data = {"temperature": -5}  # 异常数据
result = alarm.process_data(test_data)
```

## 测试

运行测试脚本验证功能：

```bash
python test_alarm_rule.py
```

测试内容包括：
- ALARM_RULE命令格式验证
- 配置转换功能测试
- 完整的MQTT通信测试（可选）

## 配置文件结构

系统使用TOML格式的配置文件，支持：

- **基础预警规则配置** - alarmRuleId, alarmRuleName, alarmClazz等
- **设备异常预警配置** - singlePropertyRule, doublePropertyRule, frequency
- **企业违规预警配置** - 支持algorithmType, workStatus等字段
- **MQTT连接配置** - broker地址、端口、主题等

## 核心特性

1. **精简实现** - 最小化代码修改，保持现有架构
2. **文档兼容** - 严格按照智算中心文档要求实现
3. **配置热更新** - 支持通过MQTT动态更新配置
4. **错误处理** - 完善的错误处理和状态反馈机制
5. **测试验证** - 提供完整的测试用例

## 文件说明

- `config.toml` - 配置文件模板
- `mqtt_smart_alarm.py` - MQTT智能预警引擎（已修改）
- `smart_alarm_enhanced.py` - 预警引擎核心（无需修改）
- `test_alarm_rule.py` - 测试脚本
- `MQTT_ALARM_RULE_README.md` - 本说明文档
