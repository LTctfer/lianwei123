# AI-BOX读取Modbus PLC数据完整操作指南

## 系统架构流程

```
传感器设备 → Modbus PLC → 以太网(Modbus TCP) → AI-BOX → 数据处理分析
     ↓           ↓              ↓                ↓           ↓
  数据采集    数据存储        网络传输          数据读取    智能分析
```

## 1. 硬件准备和网络配置

### 1.1 Modbus PLC配置

#### 网络设置
1. **配置PLC以太网参数**：
   ```
   IP地址：192.168.1.10
   子网掩码：255.255.255.0
   网关：192.168.1.1
   Modbus TCP端口：502 (标准端口)
   ```
2. **启用Modbus TCP通信**：
   - 在PLC配置中启用Modbus TCP服务
   - 设置从站ID (Unit ID)，通常为1
   - 确保防火墙允许502端口通信

#### PLC程序配置
在PLC中配置Modbus寄存器映射存储传感器数据：

```
Modbus寄存器映射表:

保持寄存器 (功能码03 - 读保持寄存器):
40001-40002: FLOAT32  // 振动X轴 (mm/s)
40003-40004: FLOAT32  // 振动Y轴 (mm/s)
40005-40006: FLOAT32  // 振动Z轴 (mm/s)
40007-40008: FLOAT32  // 轴承1温度 (°C)
40009-40010: FLOAT32  // 轴承2温度 (°C)
40011-40012: FLOAT32  // 电机温度 (°C)
40013-40014: FLOAT32  // 进口压力 (bar)
40015-40016: FLOAT32  // 出口压力 (bar)
40017-40018: FLOAT32  // 流量 (L/min)
40019-40020: FLOAT32  // 电机转速 (rpm)
40021-40022: FLOAT32  // A相电流 (A)
40023-40024: FLOAT32  // B相电流 (A)
40025-40026: FLOAT32  // C相电流 (A)
40027-40028: FLOAT32  // 供电电压 (V)
40029-40030: FLOAT32  // 有功功率 (kW)

线圈 (功能码01 - 读线圈):
1: BOOL    // 设备运行状态
2: BOOL    // 设备报警状态
3: BOOL    // 急停状态
4: BOOL    // 维护模式
5: BOOL    // 自动模式
6: BOOL    // 手动模式

注意：FLOAT32类型占用2个连续的16位寄存器
```

#### 传感器数据采集程序示例
```plc
// 主程序循环 (以西门子PLC为例)
MAIN:
  // 读取模拟量输入并转换为工程单位
  // 温度传感器 (4-20mA转换为温度值)
  CALL "AI_Read"
    AI_Channel := 0
    Raw_Value := VD100

  // 转换为工程单位并存储到Modbus保持寄存器
  VD100 := (Raw_Value - 4.0) / 16.0 * 100.0 - 20.0  // 温度转换 (-20~80°C)
  MOVE VD100, MW100             // 存储到保持寄存器40007对应的内存

  // 振动传感器数据处理
  CALL "AI_Read"
    AI_Channel := 1
    Raw_Value := VD200

  VD200 := Raw_Value * 0.025    // 振动速度转换 (0-100 mm/s)
  MOVE VD200, MW102             // 存储到保持寄存器40001对应的内存

  // 读取数字量输入并存储到Modbus线圈
  CALL "DI_Read"
    DI_Channel := 0
    Status := VB300

  // 存储状态位到线圈
  MOVE VB300.0, M1.0            // 设备运行状态 -> 线圈1
  MOVE VB300.1, M1.1            // 设备报警状态 -> 线圈2

  // 计算衍生参数
  CALL "Calculate_Power"
    Voltage := MW120              // 电压值
    Current := MW122              // 电流值
    Power := MW124                // 计算功率并存储

// Modbus TCP服务器配置
// 将内存区域映射到Modbus地址空间
// MW100-MW199 映射到保持寄存器40001-40100
// M1.0-M1.7 映射到线圈1-8
```

### 1.2 AI-BOX网络配置

```bash
# 设置AI-BOX网络
sudo ifconfig eth0 192.168.1.100 netmask 255.255.255.0
sudo route add default gw 192.168.1.1

# 测试连通性
ping 192.168.1.10
```

## 2. AI-BOX软件安装

### 2.1 安装依赖包

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和pip
sudo apt install python3 python3-pip -y

# 安装pymodbus库 (Modbus通信库)
pip3 install pymodbus

# 安装其他依赖
pip3 install numpy pandas pyyaml sqlite3 flask
```

### 2.2 下载和配置程序

```bash
# 创建工作目录
mkdir -p /opt/aibox-modbus-reader
cd /opt/aibox-modbus-reader

# 复制程序文件
cp aibox_s7_reader.py /opt/aibox-modbus-reader/aibox_modbus_reader.py
cp s7_config.yaml /opt/aibox-modbus-reader/modbus_config.yaml

# 设置权限
chmod +x aibox_modbus_reader.py
```

### 2.3 配置文件修改

编辑 `modbus_config.yaml` 文件：

```yaml
# 修改PLC连接参数
plc_connection:
  ip_address: "192.168.1.10"  # 改为实际PLC IP
  port: 502                   # Modbus TCP端口
  unit_id: 1                  # 从站ID

# 根据实际PLC程序修改数据点地址
data_points:
  vibration_x:
    address: 40001            # 确保与PLC寄存器映射一致
    type: "FLOAT32"
    function_code: 3          # 读保持寄存器
    # ... 其他配置
```

## 3. 程序运行和测试

### 3.1 手动测试连接

```python
# 测试脚本 test_connection.py
from pymodbus.client.sync import ModbusTcpClient
import struct

def test_modbus_connection():
    client = ModbusTcpClient(host='192.168.1.10', port=502, timeout=5)
    try:
        connection = client.connect()
        if connection:
            print("✅ Modbus连接成功")

            # 测试读取保持寄存器
            result = client.read_holding_registers(40001, 2, unit=1)
            if not result.isError():
                registers = result.registers
                print(f"读取寄存器: {registers}")

                # 转换为FLOAT32
                combined = (registers[0] << 16) | registers[1]
                packed = struct.pack('>I', combined)
                float_value = struct.unpack('>f', packed)[0]
                print(f"FLOAT32值: {float_value}")
            else:
                print(f"读取寄存器失败: {result}")

            # 测试读取线圈
            coil_result = client.read_coils(1, 6, unit=1)
            if not coil_result.isError():
                coils = coil_result.bits[:6]
                print(f"读取线圈: {coils}")
            else:
                print(f"读取线圈失败: {coil_result}")

        else:
            print("❌ Modbus连接失败")

    except Exception as e:
        print(f"❌ 连接异常: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    test_modbus_connection()
```

### 3.2 启动主程序

```bash
# 前台运行 (调试模式)
python3 aibox_modbus_reader.py

# 后台运行
nohup python3 aibox_modbus_reader.py > output.log 2>&1 &

# 查看运行状态
ps aux | grep aibox_modbus_reader
```

### 3.3 查看运行日志

```bash
# 实时查看日志
tail -f aibox_modbus_reader.log

# 查看最近的错误
grep "ERROR" aibox_modbus_reader.log

# 查看连接状态
grep "连接" aibox_modbus_reader.log
```

## 4. 数据验证和监控

### 4.1 数据库查询

```sql
-- 连接SQLite数据库
sqlite3 aibox_data.db

-- 查看最新数据
SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 10;

-- 查看特定参数数据
SELECT timestamp, value FROM sensor_data 
WHERE name = 'vibration_x' 
ORDER BY timestamp DESC LIMIT 20;

-- 统计数据质量
SELECT name, COUNT(*) as count, AVG(value) as avg_value 
FROM sensor_data 
WHERE timestamp > datetime('now', '-1 hour')
GROUP BY name;
```

### 4.2 实时监控脚本

```python
# monitor.py - 实时监控脚本
import sqlite3
import time
from datetime import datetime, timedelta

def monitor_data():
    while True:
        conn = sqlite3.connect('aibox_data.db')
        cursor = conn.cursor()
        
        # 查询最近1分钟的数据
        one_minute_ago = (datetime.now() - timedelta(minutes=1)).isoformat()
        cursor.execute('''
            SELECT name, COUNT(*) as count, AVG(value) as avg_value
            FROM sensor_data 
            WHERE timestamp > ?
            GROUP BY name
        ''', (one_minute_ago,))
        
        results = cursor.fetchall()
        
        print(f"\n=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
        for name, count, avg_value in results:
            print(f"{name}: {count}个数据点, 平均值: {avg_value:.2f}")
        
        conn.close()
        time.sleep(30)  # 每30秒检查一次

if __name__ == "__main__":
    monitor_data()
```

## 5. 故障排除

### 5.1 常见问题

#### 问题1: 无法连接到PLC
```
错误: snap7.snap7exceptions.Snap7Exception: CLI : ISO Connection failed
```

**解决方案**:
1. 检查网络连通性: `ping 192.168.1.10`
2. 检查PLC以太网配置
3. 确认PLC程序中启用了以太网通信
4. 检查防火墙设置

#### 问题2: 数据读取失败
```
错误: 读取数据块DB1失败
```

**解决方案**:
1. 确认DB1在PLC中存在
2. 检查数据块大小和偏移地址
3. 验证PLC程序中数据块的定义

#### 问题3: 数据格式错误
```
错误: struct.error: unpack requires a buffer of 4 bytes
```

**解决方案**:
1. 检查数据类型配置是否正确
2. 确认PLC中数据类型与配置一致
3. 验证地址偏移计算

### 5.2 调试技巧

#### 启用详细日志
```python
# 在程序开头添加
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 数据包抓取
```bash
# 使用tcpdump抓取S7通信包
sudo tcpdump -i eth0 host 192.168.1.10 -w s7_traffic.pcap

# 使用Wireshark分析
wireshark s7_traffic.pcap
```

#### 手动读取测试
```python
# 手动测试读取特定地址
import snap7
import struct

client = snap7.client.Client()
client.connect('192.168.1.10', 0, 1)

# 读取DB1的前64字节
data = client.db_read(1, 0, 64)
print(f"原始数据: {data.hex()}")

# 解析REAL类型数据
for i in range(0, 64, 4):
    if i + 4 <= len(data):
        value = struct.unpack('>f', data[i:i+4])[0]
        print(f"偏移{i}: {value}")

client.disconnect()
```

## 6. 系统优化

### 6.1 性能优化

```python
# 批量读取优化
def read_all_data_optimized(self):
    # 一次性读取整个数据块
    db_data = self.read_data_block(1, 0, 100)
    
    # 批量解析所有数据点
    data_points = []
    for name, config in self.data_points.items():
        # 解析逻辑...
        pass
    
    return data_points
```

### 6.2 数据压缩存储

```python
# 使用压缩存储减少磁盘占用
import gzip
import json

def store_compressed_data(data):
    json_data = json.dumps(data)
    compressed_data = gzip.compress(json_data.encode())
    
    with open('data_compressed.gz', 'wb') as f:
        f.write(compressed_data)
```

### 6.3 自动重启服务

```bash
# 创建systemd服务文件
sudo tee /etc/systemd/system/aibox-s7-reader.service > /dev/null <<EOF
[Unit]
Description=AI-BOX S7 Data Reader
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/aibox-s7-reader
ExecStart=/usr/bin/python3 /opt/aibox-s7-reader/aibox_s7_reader.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable aibox-s7-reader
sudo systemctl start aibox-s7-reader

# 查看服务状态
sudo systemctl status aibox-s7-reader
```

## 7. 数据分析示例

### 7.1 振动分析

```python
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

def analyze_vibration_data():
    # 从数据库读取振动数据
    conn = sqlite3.connect('aibox_data.db')
    df = pd.read_sql_query('''
        SELECT timestamp, value FROM sensor_data 
        WHERE name = 'vibration_x' 
        ORDER BY timestamp DESC LIMIT 1000
    ''', conn)
    
    # FFT分析
    vibration_data = df['value'].values
    fft_result = np.fft.fft(vibration_data)
    frequencies = np.fft.fftfreq(len(vibration_data), d=1.0)
    
    # 找出主频
    dominant_freq = frequencies[np.argmax(np.abs(fft_result[1:len(fft_result)//2]) + 1)]
    
    print(f"主频: {dominant_freq:.2f} Hz")
    
    # 绘制频谱图
    plt.figure(figsize=(10, 6))
    plt.plot(frequencies[:len(frequencies)//2], np.abs(fft_result[:len(fft_result)//2]))
    plt.xlabel('频率 (Hz)')
    plt.ylabel('幅值')
    plt.title('振动频谱分析')
    plt.savefig('vibration_spectrum.png')
    
    conn.close()
```

### 7.2 趋势分析

```python
def trend_analysis():
    conn = sqlite3.connect('aibox_data.db')
    
    # 查询最近24小时的温度数据
    df = pd.read_sql_query('''
        SELECT timestamp, value FROM sensor_data 
        WHERE name = 'temperature_bearing1' 
        AND timestamp > datetime('now', '-24 hours')
        ORDER BY timestamp
    ''', conn)
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 计算趋势
    from scipy.stats import linregress
    x = np.arange(len(df))
    slope, intercept, r_value, p_value, std_err = linregress(x, df['value'])
    
    print(f"温度趋势: {slope:.4f} °C/小时")
    print(f"相关系数: {r_value:.3f}")
    
    # 预测未来1小时的温度
    future_temp = slope * len(df) + intercept
    print(f"预测1小时后温度: {future_temp:.2f} °C")
    
    conn.close()
```

## 8. 总结

通过以上配置和代码，您可以实现：

✅ **完整的数据采集链路**: 传感器 → PLC → AI-BOX
✅ **实时数据读取**: 支持多种数据类型和地址格式
✅ **数据存储和分析**: SQLite数据库存储，支持历史查询
✅ **故障诊断**: 详细的日志和错误处理
✅ **性能监控**: 实时监控连接状态和数据质量
✅ **扩展性**: 易于添加新的传感器和分析功能

**下一步操作**:
1. 根据实际PLC程序修改配置文件
2. 测试网络连接和数据读取
3. 部署为系统服务实现自动运行
4. 根据需要添加数据分析和报警功能
