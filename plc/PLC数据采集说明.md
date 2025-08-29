# PLC数据采集系统使用说明

## 系统概述

本系统通过Modbus TCP/IP协议从PLC设备读取监测站数据，支持多种数据类型和寄存器类型，可用于环境监测数据的实时采集。

## 🚀 快速开始

### 1. 环境要求

- Python 3.7+
- 网络连接到PLC设备

### 2. 配置PLC连接

编辑 `plc_config.json` 文件：

```json
{
  "plc_settings": {
    "host": "192.168.1.100",    // PLC设备IP地址
    "port": 502,                // Modbus TCP端口 (默认502)
    "unit_id": 1,               // 设备单元ID
    "timeout": 5.0              // 连接超时时间(秒)
  }
}
```

### 3. 配置寄存器映射

在 `plc_config.json` 中配置要读取的寄存器：

```json
{
  "registers": [
    {
      "name": "pm25",              // 参数名称
      "address": 40001,            // 寄存器地址
      "register_type": "holding",  // 寄存器类型
      "data_type": "float32",      // 数据类型
      "count": 2,                  // 读取数量
      "scale": 1.0,                // 缩放因子
      "offset": 0.0,               // 偏移量
      "unit": "μg/m³",             // 单位
      "description": "PM2.5浓度"   // 描述
    }
  ]
}
```

### 4. 运行数据采集

```bash
# 测试连接
python plc_data_collector.py --test

# 开始连续采集 (默认60秒间隔)
python plc_data_collector.py

# 自定义采集间隔
python plc_data_collector.py --interval 30
```

## 📊 支持的数据类型

### 寄存器类型

| 类型 | 功能码 | 说明 |
|------|--------|------|
| holding | 03 | 保持寄存器 (可读写) |
| input | 04 | 输入寄存器 (只读) |
| coil | 01 | 线圈 (布尔值，可读写) |
| discrete | 02 | 离散输入 (布尔值，只读) |

### 数据类型

| 类型 | 字节数 | 寄存器数 | 说明 |
|------|--------|----------|------|
| bool | 1 bit | 1 | 布尔值 |
| int16 | 2 | 1 | 有符号16位整数 |
| uint16 | 2 | 1 | 无符号16位整数 |
| int32 | 4 | 2 | 有符号32位整数 |
| uint32 | 4 | 2 | 无符号32位整数 |
| float32 | 4 | 2 | IEEE 754单精度浮点数 |

## 🔧 寄存器地址说明

### 常见地址格式

- **保持寄存器**: 40001-49999 (实际地址 = 配置地址 - 40001)
- **输入寄存器**: 30001-39999 (实际地址 = 配置地址 - 30001)
- **线圈**: 00001-09999 (实际地址 = 配置地址 - 1)
- **离散输入**: 10001-19999 (实际地址 = 配置地址 - 10001)

### 地址配置示例

```json
{
  "name": "temperature",
  "address": 40007,        // Modbus地址40007 (实际地址6)
  "register_type": "holding",
  "data_type": "int16",
  "scale": 0.1,           // 原始值 × 0.1
  "offset": 0.0           // 结果 + 0.0
}
```

## 📈 数据处理流程

1. **连接PLC**: 建立Modbus TCP连接
2. **读取寄存器**: 根据配置读取原始数据
3. **数据转换**: 转换为指定数据类型
4. **缩放处理**: 应用缩放因子和偏移量
5. **格式化输出**: 转换为监测站数据格式
6. **数据存储**: 保存到CSV文件

## 🛠️ 使用示例

### 基本使用

```python
from modbus_plc_reader import PLCDataReader, PLCRegister

# 创建PLC读取器
reader = PLCDataReader(host="192.168.1.100", port=502)

# 添加寄存器配置
pm25_reg = PLCRegister(
    name="pm25",
    address=40001,
    register_type="holding",
    data_type="float32",
    count=2,
    unit="μg/m³"
)
reader.add_register(pm25_reg)

# 连接并读取数据
if reader.connect():
    data = reader.read_all_registers()
    print(f"PM2.5浓度: {data['pm25']['value']} {data['pm25']['unit']}")
    reader.disconnect()
```

### 批量配置

```python
import json
from plc_data_collector import PLCDataCollector

# 从配置文件创建采集器
collector = PLCDataCollector("plc_config.json")

# 测试连接
if collector.test_connection():
    print("连接成功")
    
    # 采集单次数据
    data = collector.collect_single_data()
    print(data)
```

## 🚨 错误处理

### 常见错误及解决方案

1. **连接超时**
   - 检查PLC设备IP地址和端口
   - 确认网络连通性
   - 检查防火墙设置

2. **Modbus异常**
   - 验证寄存器地址是否正确
   - 检查数据类型配置
   - 确认PLC设备支持相应功能码

3. **数据转换错误**
   - 检查数据类型与寄存器数量匹配
   - 验证缩放因子和偏移量设置

### 调试方法

```bash
# 启用详细日志
python plc_data_collector.py --test

# 查看日志文件
tail -f plc_collector.log
```

## 📋 配置模板

### 完整配置示例

```json
{
  "plc_settings": {
    "host": "192.168.1.100",
    "port": 502,
    "unit_id": 1,
    "timeout": 5.0
  },
  "registers": [
    {
      "name": "pm25",
      "address": 40001,
      "register_type": "holding",
      "data_type": "float32",
      "count": 2,
      "scale": 1.0,
      "offset": 0.0,
      "unit": "μg/m³",
      "description": "PM2.5浓度"
    },
    {
      "name": "wind_speed",
      "address": 40005,
      "register_type": "holding", 
      "data_type": "uint16",
      "count": 1,
      "scale": 0.1,
      "offset": 0.0,
      "unit": "m/s",
      "description": "风速"
    },
    {
      "name": "device_status",
      "address": 1,
      "register_type": "coil",
      "data_type": "bool",
      "count": 1,
      "scale": 1.0,
      "offset": 0.0,
      "unit": "",
      "description": "设备运行状态"
    }
  ]
}
```

## 🔄 数据输出格式

采集的数据将保存为CSV格式，包含以下字段：

- `timestamp`: 采集时间
- `station_id`: 监测站ID
- `station_name`: 监测站名称
- `pm25`: PM2.5浓度 (μg/m³)
- `wind_speed`: 风速 (m/s)
- `temperature`: 温度 (°C)
- 其他配置的监测参数

## 📞 技术支持

如遇问题，请检查：
1. PLC设备网络连接
2. Modbus TCP服务是否启用
3. 寄存器地址和数据类型配置
4. 防火墙和网络安全设置

---

*PLC数据采集系统 v1.0*  
*支持Modbus TCP/IP协议*
