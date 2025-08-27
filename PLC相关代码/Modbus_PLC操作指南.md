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
# 配置AI-BOX网络
sudo nano /etc/netplan/01-netcfg.yaml

# 添加以下配置
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: no
      addresses: [192.168.1.100/24]
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]

# 应用配置
sudo netplan apply

# 测试网络连通性
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
pip3 install numpy pandas pyyaml sqlite3
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

## 3. 运行和测试

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

## 4. 系统服务配置

### 4.1 创建systemd服务

```bash
# 创建服务文件
sudo nano /etc/systemd/system/aibox-modbus-reader.service
```

```ini
[Unit]
Description=AI-BOX Modbus PLC Data Reader
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/aibox-modbus-reader
ExecStart=/usr/bin/python3 /opt/aibox-modbus-reader/aibox_modbus_reader.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 4.2 启用和管理服务

```bash
# 重新加载systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable aibox-modbus-reader

# 启动服务
sudo systemctl start aibox-modbus-reader

# 查看服务状态
sudo systemctl status aibox-modbus-reader

# 查看服务日志
sudo journalctl -u aibox-modbus-reader -f
```

## 5. 故障排除

### 5.1 常见问题

1. **连接超时**
   ```bash
   # 检查网络连通性
   ping 192.168.1.10
   
   # 检查端口是否开放
   telnet 192.168.1.10 502
   ```

2. **权限问题**
   ```bash
   # 检查文件权限
   ls -la /opt/aibox-modbus-reader/
   
   # 修复权限
   sudo chown -R root:root /opt/aibox-modbus-reader/
   sudo chmod +x /opt/aibox-modbus-reader/aibox_modbus_reader.py
   ```

3. **依赖包问题**
   ```bash
   # 重新安装pymodbus
   pip3 uninstall pymodbus
   pip3 install pymodbus
   
   # 检查版本
   pip3 show pymodbus
   ```

### 5.2 调试技巧

1. **启用详细日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **使用Modbus测试工具**
   ```bash
   # 安装modbus工具
   pip3 install pymodbus[repl]
   
   # 启动交互式客户端
   pymodbus.console tcp --host 192.168.1.10 --port 502
   ```

## 6. 性能优化

### 6.1 连接池配置
```python
# 使用连接池提高性能
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.transaction import ModbusRtuFramer

client = ModbusTcpClient(
    host='192.168.1.10',
    port=502,
    timeout=3,
    retries=3,
    retry_on_empty=True
)
```

### 6.2 批量读取优化
```python
# 批量读取多个连续寄存器
result = client.read_holding_registers(40001, 30, unit=1)  # 一次读取30个寄存器
```

## 7. 安全配置

### 7.1 防火墙设置
```bash
# 允许Modbus TCP端口
sudo ufw allow 502/tcp

# 限制访问源IP
sudo ufw allow from 192.168.1.0/24 to any port 502
```

### 7.2 网络隔离
- 将PLC和AI-BOX放在独立的VLAN中
- 使用VPN进行远程访问
- 定期更新系统和软件包

## 8. 监控和维护

### 8.1 系统监控
```bash
# 监控系统资源
htop

# 监控网络连接
netstat -an | grep 502

# 监控磁盘空间
df -h
```

### 8.2 定期维护
- 定期备份配置文件和数据
- 清理旧的日志文件
- 更新软件依赖包
- 检查硬件状态

这个指南提供了从硬件配置到软件部署的完整流程，确保AI-BOX能够稳定可靠地从Modbus PLC读取数据。
