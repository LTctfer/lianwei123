# RTO 设备预警数据上报系统

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-green.svg)](https://fastapi.tiangolo.com/)
[![Modbus](https://img.shields.io/badge/Protocol-Modbus_RTU-orange.svg)]()

## 📋 项目概述

RTO（蓄热式热氧化器）设备预警数据上报系统是一个工业物联网解决方案，用于实时监控 RTO 设备运行状态，自动检测异常情况并上报预警信息。系统通过 Modbus 协议从 PLC 读取设备数据，根据可配置的规则进行智能分析，实现设备的智能化监控和预警。

### 🎯 核心功能

- **实时数据采集**: 通过 Modbus RTU 协议从 PLC 设备读取实时运行数据
- **智能预警判断**: 基于灵活的规则引擎，支持单属性、双属性、频率控制等多种预警策略
- **数据存储管理**: 自动保存历史数据到 CSV 文件，支持数据清洗和异常检测
- **远程上报**: 自动将预警数据和实时数据上报到远程 API 接口
- **规则配置服务**: 提供 RESTful API 实现规则的远程配置和管理
- **时间范围控制**: 支持设置预警规则的生效时间段
- **冷却间隔**: 避免重复预警，支持配置预警间隔时间

---

## 📁 项目结构

```
rto/
├── rto/
│   ├── read_upload.py          # 主程序：数据读取与预警上报
│   ├── server_api.py            # FastAPI 服务：规则配置管理
│   ├── config.json              # 预警规则配置文件
│   └── __pycache__/             # Python 缓存文件
├── 预警规则配置接口说明.md      # API 接口文档
├── 代码优化总结.md              # 代码优化记录
└── README.md                    # 本文档
```

---

## 🔧 核心模块说明

### 1. read_upload.py - 数据采集与预警引擎

**主要功能**：
- 📡 从 PLC 读取 RTO 设备实时数据（Modbus RTU 协议）
- 💾 数据存储到 CSV 文件（按日期分文件）
- 🧹 数据清洗和异常值检测（IQR 方法）
- 📊 统计计算（分钟、小时、日均值）
- ⚠️ 预警规则执行和判断
- 📤 上报预警数据和实时数据到远程 API

**核心类**：

#### `ModbusDataReader`
PLC 数据读取器，负责通过 Modbus 协议读取设备数据。

```python
reader = ModbusDataReader()
reader.connect()
data = reader.read()  # 返回包含 t1, t2, t3, p1, fan_status 等数据
```

#### `CSVDataManager`
CSV 数据管理器，负责数据的持久化存储和读取。

```python
manager = CSVDataManager()
manager.save_data(data)                    # 保存数据
df = manager.read_recent_data(minutes=60)  # 读取最近60分钟数据
manager.clean_old_files(days=2)            # 清理2天前的文件
```

#### `DataProcessor`
数据处理器，提供数据清洗和统计功能。

```python
processor = DataProcessor()
df_clean = processor.clean_data(df)                      # 清洗数据
df_no_outliers = processor.remove_outliers_iqr(df)      # 去除异常值
stats = processor.calculate_statistics(df, '1min')       # 计算统计数据
```

#### `AlarmDataReporter`
预警数据上报引擎，核心业务逻辑。

```python
reporter = AlarmDataReporter()
reporter.load_rules()        # 加载规则
reporter.start()             # 启动引擎
reporter.process(data)       # 处理数据，执行规则检查
```

#### `RuleRunner`
单条规则执行器，负责执行具体的预警规则判断。

**支持的规则类型**：
- **单属性规则**: 检查单个属性是否满足条件（支持范围检测）
- **双属性规则**: 检查两个属性之间的关系
- **频率控制**: 累计次数触发 或 连续次数触发
- **时间范围**: 规则仅在指定时间段内生效
- **冷却间隔**: 避免重复预警

---

### 2. server_api.py - 规则配置管理服务

**主要功能**：
- 🌐 提供 RESTful API 进行规则管理
- 📝 支持规则的增删改查操作
- 🔄 规则同步和更新
- 📋 预警记录查询

**API 接口列表**：

#### 健康检查
```http
GET /health
```
返回服务状态信息。

#### 获取规则配置
```http
GET /get_config
```
获取当前所有预警规则配置。

#### 同步规则（完全覆盖）
```http
POST /sync_rules
Content-Type: application/json

{
  "rules": [...]
}
```

#### 批量添加规则
```http
POST /batch_add_rules
Content-Type: application/json

{
  "rules": [...]
}
```

#### 更新单条规则
```http
PUT /update_rule/{rule_id}
Content-Type: application/json

{
  "alarmRuleName": "新规则名称",
  ...
}
```

#### 删除单条规则
```http
DELETE /delete_rule/{rule_id}
```

#### 获取预警记录
```http
GET /get_alarms?limit=100&level=HIGH
```

详细 API 文档请参考：`预警规则配置接口说明.md`

---

### 3. config.json - 规则配置文件

配置文件定义了所有的预警规则，支持动态加载和更新。

**配置示例**：

```json
{
  "rules": [
    {
      "alarmRuleId": "rule_001",
      "alarmRuleName": "温度异常预警",
      "alarmClazz": "DEVICE_ALARM",
      "alarmType": "CONTROL_ALARM",
      "alarmLevel": "HIGH",
      "alarmInternal": 1,
      "dataInternal": "10s",
      "algorithmType": "threshold",
      "enabled": 1,
      "startTime": "00:00",
      "endTime": "23:59",
      "showProperties": ["t1", "t2", "t3"],
      "config": {
        "singlePropertyRule": [
          {
            "symbol": "AND",
            "property": "t2",
            "lowValue": 0,
            "expression1": "le",
            "highValue": 800,
            "expression2": "le"
          }
        ],
        "doublePropertyRule": [
          {
            "symbol": "OR",
            "leftProperty": "t3",
            "rightProperty": "t2",
            "expression": "gt"
          }
        ],
        "frequency": {
          "enabled": 1,
          "hasAccumulate": 1,
          "accumulateTimeRange": 60,
          "accumulateCount": 3
        },
        "workStatus": ["RUNNING", "HEATING"]
      }
    }
  ]
}
```

**配置字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `alarmRuleId` | String | 规则唯一标识符 |
| `alarmRuleName` | String | 规则名称 |
| `alarmClazz` | String | 预警分类：`DEVICE_ALARM`/`ENTERPRISE_ALARM` |
| `alarmType` | String | 预警类型：`CONTROL_ALARM`/`DATA_ALARM` |
| `alarmLevel` | String | 预警级别：`LOW`/`MEDIUM`/`HIGH`/`CRITICAL` |
| `alarmInternal` | Number | 冷却间隔（小时），0表示无限制 |
| `dataInternal` | String | 数据采集间隔，如 "10s" |
| `enabled` | Number | 是否启用：1启用/0禁用 |
| `startTime` | String | 生效开始时间，格式 "HH:MM" |
| `endTime` | String | 生效结束时间，格式 "HH:MM" |
| `showProperties` | Array | 预警时展示的属性列表 |
| `config` | Object | 规则详细配置（见下文） |

**规则配置详解**：

#### 单属性规则 (`singlePropertyRule`)
检查单个属性值是否满足条件。

```json
{
  "symbol": "AND",           // 逻辑运算符：AND/OR
  "property": "t2",          // 属性名称
  "lowValue": 0,             // 下界值
  "expression1": "le",       // 下界比较运算符：lt/le/eq/ge/gt
  "highValue": 800,          // 上界值
  "expression2": "le"        // 上界比较运算符
}
```

**范围检测逻辑**：
- 当 `symbol="AND"` 且同时有上下界时，表示**范围外检测**
- 例如：`lowValue=0, expression1="le", highValue=800, expression2="le"`
- 表示正常范围为 `(0, 800]`，即 `v <= 0 OR v > 800` 时触发预警

#### 双属性规则 (`doublePropertyRule`)
检查两个属性之间的关系。

```json
{
  "symbol": "OR",
  "leftProperty": "t3",      // 左侧属性
  "rightProperty": "t2",     // 右侧属性
  "expression": "gt"         // 比较运算符：lt/le/eq/ge/gt
}
```
表示：当 `t3 > t2` 时触发预警。

#### 频率控制 (`frequency`)
控制预警触发的频率。

```json
{
  "enabled": 1,              // 是否启用频率控制
  "hasAccumulate": 1,        // 是否累计模式：1累计/0连续
  "accumulateTimeRange": 60, // 累计时间范围（秒）
  "accumulateCount": 3,      // 累计触发次数
  "continuousCount": 5       // 连续触发次数（非累计模式）
}
```

**两种模式**：
- **累计模式** (`hasAccumulate=1`): 在指定时间范围内累计达到指定次数触发
- **连续模式** (`hasAccumulate=0`): 连续达到指定次数触发

#### 工况状态过滤 (`workStatus`)
仅在企业预警 (`ENTERPRISE_ALARM`) 中有效。

```json
{
  "workStatus": ["RUNNING", "HEATING"]
}
```
表示仅在设备处于这些工况状态时才检查此规则。

---

## 📊 监测参数

RTO 设备监测的主要参数：

| 参数代码 | 参数名称 | 单位 | Modbus地址 | 说明 |
|---------|---------|------|-----------|------|
| `t1` | 加热室平均温度 | °C | 0x0000-0x0001 | 浮点数（2个寄存器） |
| `t2` | RTO出口温度 | °C | 0x0002-0x0003 | 浮点数（2个寄存器） |
| `t3` | RTO进口温度 | °C | 0x0004-0x0005 | 浮点数（2个寄存器） |
| `p1` | RTO出口压力 | Pa | 0x0006-0x0007 | 浮点数（2个寄存器） |
| `fan_status` | 风机启停状态 | - | 0x0000（线圈） | 0关闭/1启动 |
| `workStatus` | 工况状态 | - | - | 设备运行状态 |

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.7+
- **操作系统**: Windows / Linux
- **硬件**: 支持串口通信的设备
- **PLC**: 支持 Modbus RTU 协议

### 安装依赖

```bash
cd rto/rto
pip install -r requirements.txt
```

**主要依赖包**：
```
pandas>=1.3.0
numpy>=1.21.0
requests>=2.26.0
pymodbus>=2.5.3
fastapi>=0.68.0
uvicorn>=0.15.0
```

### 配置说明

#### 1. PLC 通信配置

编辑 `read_upload.py` 中的 PLC 配置参数：

```python
# PLC Modbus 配置
PLC_SLAVE_ID = 1                # 从站ID
PLC_PORT = "/dev/ttyS8"         # Windows: "COM1", Linux: "/dev/ttyS8"
PLC_BAUDRATE = 9600             # 波特率
PLC_PARITY = "N"                # 校验位：N/E/O
PLC_STOPBITS = 1                # 停止位
PLC_BYTESIZE = 8                # 数据位
PLC_TIMEOUT = 1                 # 超时时间（秒）
PLC_INTERVAL = 10               # 读取间隔（秒）
```

#### 2. API 接口配置

```python
# 远程API接口地址
REMOTE_API_URL = "http://127.0.0.1:8023/intelligence-center/data-import/importAlarmData"
REAL_DATA_API_URL = "http://127.0.0.1:8023/intelligence-center/data-import/importRealData"
```

#### 3. 数据存储配置

```python
# CSV数据存储配置
CSV_DATA_DIR = "plc_data"       # CSV数据存储目录
CSV_FILE_PREFIX = "plc_data"    # CSV文件前缀
DATA_RETENTION_DAYS = 2         # 数据保留天数
```

#### 4. 设备信息配置

```python
# 设备信息
DEVICE_NUM = "255122420258d523"
DEVICE_MN = "001"
```

---

## 🎮 运行系统

### 启动数据采集和预警系统

```bash
cd rto/rto
python read_upload.py
```

**运行日志示例**：
```
============================================================
🚀 启动预警数据上报引擎
============================================================
✅ 成功加载 3 条启用的规则
  规则 1: 温度异常预警 [HIGH] 时间范围: 00:00-23:59
  规则 2: 压力过高预警 [MEDIUM] 时间范围: 08:00-20:00
  规则 3: 温差预警 [LOW] 时间范围: 00:00-23:59
✅ 成功连接到PLC设备
📊 读取数据: t1=650.5°C, t2=720.3°C, t3=480.2°C, p1=1200Pa
💾 数据已保存到CSV
⚠️ 触发预警规则: 温度异常预警
📤 正在上报预警数据...
✅ 预警数据上报成功！
```

### 启动规则配置服务

在另一个终端启动 FastAPI 服务：

```bash
cd rto/rto
uvicorn server_api:app --host 0.0.0.0 --port 8000 --reload
```

访问 API 文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 📖 使用示例

### 示例 1: 添加新的预警规则

```python
import requests

# 定义新规则
new_rule = {
    "alarmRuleId": "rule_temp_high",
    "alarmRuleName": "高温预警",
    "alarmClazz": "DEVICE_ALARM",
    "alarmType": "CONTROL_ALARM",
    "alarmLevel": "HIGH",
    "alarmInternal": 0.5,
    "enabled": 1,
    "startTime": "00:00",
    "endTime": "23:59",
    "showProperties": ["t1", "t2"],
    "config": {
        "singlePropertyRule": [
            {
                "symbol": "OR",
                "property": "t2",
                "lowValue": 850,
                "expression1": "gt",
                "highValue": None,
                "expression2": None
            }
        ],
        "frequency": {
            "enabled": 1,
            "hasAccumulate": 0,
            "continuousCount": 3
        }
    }
}

# 添加规则
response = requests.post(
    "http://localhost:8000/batch_add_rules",
    json={"rules": [new_rule]}
)
print(response.json())
```

### 示例 2: 查询预警记录

```python
import requests

# 查询最近100条高级别预警
response = requests.get(
    "http://localhost:8000/get_alarms",
    params={"limit": 100, "level": "HIGH"}
)

alarms = response.json()
for alarm in alarms["alarms"]:
    print(f"[{alarm['level']}] {alarm['ruleName']}: {alarm['time']}")
```

### 示例 3: 自定义数据处理

```python
from read_upload import DataProcessor, CSVDataManager

# 读取最近1小时的数据
manager = CSVDataManager()
df = manager.read_recent_data(minutes=60)

# 数据清洗
processor = DataProcessor()
df_clean = processor.clean_data(df)
df_no_outliers = processor.remove_outliers_iqr(df_clean)

# 计算1分钟统计数据
stats = processor.calculate_statistics(df_no_outliers, '1min')
print(f"1分钟平均温度: T1={stats['t1']}°C, T2={stats['t2']}°C")
```

---

## 🔍 预警规则设计指南

### 场景 1: 温度范围预警

**需求**: RTO 出口温度正常范围为 700-850°C，超出范围则预警。

```json
{
  "singlePropertyRule": [
    {
      "symbol": "AND",
      "property": "t2",
      "lowValue": 700,
      "expression1": "le",
      "highValue": 850,
      "expression2": "le"
    }
  ]
}
```

**逻辑**: 当 `t2 <= 700` 或 `t2 > 850` 时触发。

### 场景 2: 温差预警

**需求**: 当进口温度高于出口温度时预警（异常情况）。

```json
{
  "doublePropertyRule": [
    {
      "symbol": "OR",
      "leftProperty": "t3",
      "rightProperty": "t2",
      "expression": "gt"
    }
  ]
}
```

**逻辑**: 当 `t3 > t2` 时触发。

### 场景 3: 频繁波动预警

**需求**: 1分钟内温度超过800°C累计3次则预警。

```json
{
  "singlePropertyRule": [
    {
      "symbol": "OR",
      "property": "t2",
      "lowValue": 800,
      "expression1": "gt"
    }
  ],
  "frequency": {
    "enabled": 1,
    "hasAccumulate": 1,
    "accumulateTimeRange": 60,
    "accumulateCount": 3
  }
}
```

### 场景 4: 夜间预警

**需求**: 仅在夜间（20:00-08:00）监控设备温度。

```json
{
  "startTime": "20:00",
  "endTime": "08:00",
  "singlePropertyRule": [...]
}
```

**注意**: 跨天时间范围会自动处理。

---

## 📊 数据流程图

```
┌─────────────┐
│  PLC 设备   │
│  (Modbus)   │
└──────┬──────┘
       │ Modbus RTU
       ▼
┌─────────────────┐
│ ModbusDataReader│  读取实时数据
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ CSVDataManager  │  保存到CSV文件
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DataProcessor   │  数据清洗和统计
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ RuleRunner      │  执行预警规则
└────────┬────────┘
         │
         ├─── ✅ 无预警 ──────┐
         │                   │
         └─── ⚠️ 有预警 ───┐  │
                           │  │
                           ▼  ▼
                    ┌──────────────┐
                    │ 远程 API     │  上报数据
                    │ - 预警数据   │
                    │ - 实时数据   │
                    └──────────────┘
```

---

## 🛠️ 故障排查

### 问题 1: 无法连接到 PLC

**症状**: 日志显示 "❌ 无法连接到PLC设备"

**解决方案**:
1. 检查串口配置是否正确（端口号、波特率等）
2. 确认 PLC 设备已开机且正常运行
3. 检查串口线是否连接正确
4. Windows 系统检查设备管理器中的 COM 端口
5. Linux 系统确认串口权限：`sudo chmod 666 /dev/ttyS8`

### 问题 2: 规则不生效

**症状**: 满足条件但未触发预警

**解决方案**:
1. 检查规则是否启用（`enabled: 1`）
2. 确认当前时间在规则的生效时间范围内
3. 检查冷却间隔是否还在生效期
4. 查看频率控制配置是否正确
5. 检查日志中的规则加载信息

### 问题 3: 数据上报失败

**症状**: 日志显示 "❌ 预警数据上报失败"

**解决方案**:
1. 检查网络连接是否正常
2. 确认远程 API 地址配置正确
3. 测试 API 接口是否可访问：`curl http://api-url/health`
4. 检查 API 接口是否需要认证
5. 查看详细错误信息调整请求格式

### 问题 4: CSV 文件过大

**症状**: CSV 文件占用磁盘空间过大

**解决方案**:
1. 调整数据保留天数：`DATA_RETENTION_DAYS = 2`
2. 手动清理过期文件：`manager.clean_old_files(days=1)`
3. 增加数据采集间隔：`PLC_INTERVAL = 30`
4. 启用数据压缩存储

---

## 📈 性能优化

### 优化建议

1. **数据采集频率**: 根据实际需求调整 `PLC_INTERVAL`，避免过于频繁
2. **规则数量**: 建议单个系统规则数量不超过50条
3. **CSV文件管理**: 定期清理过期文件，建议保留2-7天数据
4. **异常值检测**: IQR方法适用于大多数场景，特殊需求可自定义
5. **内存管理**: 大数据量时使用分块读取和处理

### 性能指标

- **数据读取延迟**: <1秒
- **规则执行时间**: <100ms（单条规则）
- **CSV写入性能**: >1000条/秒
- **API响应时间**: <200ms

---

## 🔒 安全建议

1. **网络安全**:
   - 使用 HTTPS 协议传输数据
   - 配置 API 认证和授权
   - 限制 API 访问 IP 白名单

2. **数据安全**:
   - 定期备份配置文件和历史数据
   - 敏感信息（如 API 密钥）使用环境变量
   - 加密存储关键配置

3. **访问控制**:
   - 限制服务器端口访问权限
   - 使用防火墙保护内网设备
   - 定期更新系统和依赖包

---

## 📝 更新日志

### v1.2.0 (2025-10-28)
- ✨ 新增数据清洗和异常值检测功能
- ✨ 支持 CSV 数据存储和历史数据查询
- 🐛 修复时间范围跨天判断问题
- 📝 完善 API 文档和使用说明

### v1.1.0 (2025-10-15)
- ✨ 新增 FastAPI 规则配置服务
- ✨ 支持规则的远程管理
- 🐛 优化频率控制逻辑

### v1.0.0 (2025-10-01)
- 🎉 首次发布
- ✨ 实现基本的数据采集和预警功能
- ✨ 支持 Modbus RTU 协议

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发流程

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](../LICENSE) 文件

---

## 👥 联系方式

- **项目维护**: LTctfer
- **问题反馈**: [GitHub Issues](https://github.com/LTctfer/lianwei123/issues)

---

## 🌟 致谢

感谢以下开源项目：
- [pymodbus](https://github.com/pymodbus-dev/pymodbus) - Modbus 协议实现
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化 Web 框架
- [Pandas](https://pandas.pydata.org/) - 数据处理库

---

**最后更新**: 2025-10-28  
**版本**: v1.2.0
