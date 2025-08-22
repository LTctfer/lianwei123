# PLC到算能AI-BOX数据采集系统

## 系统概述

本系统实现了从PLC现场采集数据，经过数据清洗、滤波、降采样、特征提取（FFT计算振动频谱）、公式计算等处理后，上传至算能AI-BOX的完整解决方案。

## 系统架构

```
PLC设备 → 数据采集器 → 数据处理器 → AI-BOX上传器
   ↓           ↓           ↓           ↓
现场传感器   实时采集    智能处理    云端存储
```

## 主要功能

### 1. 数据采集
- **多协议支持**: 支持Modbus TCP/RTU、OPC UA、Ethernet/IP等主流工业协议
- **实时采集**: 可配置采集频率，支持高频数据采集
- **数据缓存**: 内置队列缓存机制，防止数据丢失
- **异常处理**: 自动重连和错误恢复机制

### 2. 数据清洗
- **异常值检测**: 基于统计方法和业务规则的异常值识别
- **数据验证**: 数据类型、范围、完整性验证
- **质量标记**: 为每个数据点分配质量等级（GOOD/BAD/UNCERTAIN）
- **缺失值处理**: 插值和填充策略

### 3. 数字滤波
- **带通滤波**: 用于振动信号的频域滤波
- **低通滤波**: 用于温度等慢变信号的噪声滤除
- **移动平均**: 用于一般信号的平滑处理
- **自适应滤波**: 根据信号特性自动选择滤波参数

### 4. 降采样
- **智能降采样**: 保持信号特征的同时减少数据量
- **多级降采样**: 支持不同参数的不同降采样率
- **时间对齐**: 确保多路信号的时间同步

### 5. FFT特征提取
- **振动频谱分析**: 计算振动信号的频域特征
- **主频识别**: 自动识别设备的主要振动频率
- **功率谱密度**: 计算信号的能量分布
- **频域特征**: 提取频谱质心、峰值功率等特征

### 6. 公式计算
- **衍生参数**: 基于原始数据计算衍生指标
- **设备效率**: 计算设备运行效率指标
- **预警指标**: 计算设备健康度和预警参数
- **自定义公式**: 支持用户自定义计算公式

## 快速开始

### 1. 环境要求

```bash
Python >= 3.8
算能AI-BOX (支持HTTP API)
PLC设备 (支持标准工业协议)
```

### 2. 安装依赖

```bash
pip install numpy pandas scipy scikit-learn aiohttp sqlite3
```

### 3. 基本配置

```python
# PLC配置
plc_config = {
    'ip_address': '192.168.1.10',    # PLC IP地址
    'port': 502,                     # 通信端口
    'device_id': 'PLC_001',          # 设备ID
    'scan_rate': 1000,               # 扫描周期(ms)
    'parameters': [                  # 采集参数列表
        {'name': 'vibration_x', 'address': 'DB1.DBD0', 'type': 'REAL'},
        {'name': 'vibration_y', 'address': 'DB1.DBD4', 'type': 'REAL'},
        {'name': 'temperature', 'address': 'DB1.DBD8', 'type': 'REAL'},
        {'name': 'pressure', 'address': 'DB1.DBD12', 'type': 'REAL'},
        {'name': 'flow_rate', 'address': 'DB1.DBD16', 'type': 'REAL'},
    ]
}

# AI-BOX配置
aibox_config = AIBoxConfig(
    ip_address="192.168.1.100",      # AI-BOX IP地址
    port=8080,                       # API端口
    api_endpoint="/api/data/upload", # 上传接口
    auth_token="your_token_here",    # 认证令牌
    batch_size=50,                   # 批量上传大小
    upload_interval=30               # 上传间隔(秒)
)
```

### 4. 启动系统

```python
import asyncio
from plc_to_aibox_system import PLCToAIBoxSystem, create_demo_config

async def main():
    # 创建配置
    plc_config, aibox_config, processing_config = create_demo_config()

    # 创建系统实例
    system = PLCToAIBoxSystem(plc_config, aibox_config, processing_config)

    # 启动系统
    await system.start_system()

    # 系统运行...
    try:
        while True:
            status = system.get_system_status()
            print(f"系统状态: {status}")
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        system.stop_system()

if __name__ == "__main__":
    asyncio.run(main())
```

## 详细配置说明

### 数据处理配置

```python
processing_config = {
    'buffer_size': 1000,              # 历史数据缓冲区大小
    'downsample_factor': 1,           # 降采样因子
    'enable_fft': True,               # 启用FFT分析
    'fft_window_size': 128,           # FFT窗口大小
    'filter_config': {                # 滤波器配置
        'vibration': {
            'type': 'bandpass',       # 带通滤波
            'low': 0.1,               # 低频截止
            'high': 0.4               # 高频截止
        },
        'temperature': {
            'type': 'lowpass',        # 低通滤波
            'cutoff': 0.1             # 截止频率
        },
        'default': {
            'type': 'moving_average', # 移动平均
            'window': 5               # 窗口大小
        }
    }
}
```

### PLC通信协议配置

#### Modbus TCP配置示例
```python
modbus_config = {
    'protocol': 'modbus_tcp',
    'ip_address': '192.168.1.10',
    'port': 502,
    'unit_id': 1,
    'timeout': 3,
    'registers': [
        {'name': 'vibration_x', 'address': 40001, 'type': 'float32', 'scale': 1.0},
        {'name': 'vibration_y', 'address': 40003, 'type': 'float32', 'scale': 1.0},
        {'name': 'temperature', 'address': 40005, 'type': 'int16', 'scale': 0.1},
        {'name': 'pressure', 'address': 40006, 'type': 'uint16', 'scale': 0.01},
    ]
}
```

#### OPC UA配置示例
```python
opcua_config = {
    'protocol': 'opcua',
    'endpoint': 'opc.tcp://192.168.1.10:4840',
    'security_policy': 'None',
    'username': 'admin',
    'password': 'password',
    'nodes': [
        {'name': 'vibration_x', 'node_id': 'ns=2;s=Vibration.X'},
        {'name': 'vibration_y', 'node_id': 'ns=2;s=Vibration.Y'},
        {'name': 'temperature', 'node_id': 'ns=2;s=Temperature'},
        {'name': 'pressure', 'node_id': 'ns=2;s=Pressure'},
    ]
}
```

## 系统监控与维护

### 实时状态监控

```python
# 获取系统状态
status = system.get_system_status()
print(f"系统运行状态: {status['is_running']}")
print(f"采集队列大小: {status['collector_queue_size']}")
print(f"上传队列大小: {status['uploader_queue_size']}")
print(f"最后更新时间: {status['timestamp']}")

# 监控数据质量
def monitor_data_quality(processed_data):
    for data in processed_data:
        if data.quality_score < 0.8:
            print(f"警告: 设备 {data.device_id} 数据质量较低: {data.quality_score}")

        # 检查FFT特征异常
        for param, features in data.fft_features.items():
            if features.get('peak_power', 0) > 100:  # 阈值可调
                print(f"警告: {param} 振动异常，峰值功率: {features['peak_power']}")
```

### 数据存储管理

```python
# 数据库查询示例
import sqlite3

def query_historical_data(device_id, start_time, end_time):
    conn = sqlite3.connect('plc_data.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT timestamp, raw_data, filtered_data, quality_score
        FROM processed_data
        WHERE device_id = ? AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp
    ''', (device_id, start_time, end_time))

    results = cursor.fetchall()
    conn.close()
    return results

# 数据清理（删除过期数据）
def cleanup_old_data(days_to_keep=30):
    conn = sqlite3.connect('plc_data.db')
    cursor = conn.cursor()

    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)

    cursor.execute('DELETE FROM raw_data WHERE timestamp < ?', (cutoff_date.isoformat(),))
    cursor.execute('DELETE FROM processed_data WHERE timestamp < ?', (cutoff_date.isoformat(),))

    conn.commit()
    conn.close()
```

## 故障排除指南

### 常见问题及解决方案

#### 1. PLC连接问题

**问题**: 无法连接到PLC设备
```
错误信息: ConnectionError: [Errno 10061] 由于目标计算机积极拒绝，无法连接
```

**解决方案**:
- 检查PLC设备IP地址和端口配置
- 确认网络连通性: `ping 192.168.1.10`
- 检查防火墙设置，开放相应端口
- 验证PLC设备的通信协议设置

#### 2. 数据上传失败

**问题**: 数据无法上传到AI-BOX
```
错误信息: aiohttp.ClientError: Cannot connect to host 192.168.1.100:8080
```

**解决方案**:
- 检查AI-BOX网络连接和API服务状态
- 验证认证令牌是否正确
- 检查API接口路径和参数格式
- 查看AI-BOX日志获取详细错误信息

#### 3. 数据处理异常

**问题**: FFT计算失败或滤波器错误
```
错误信息: ValueError: Input signal length is too short for FFT
```

**解决方案**:
- 增加历史数据缓冲区大小
- 调整FFT窗口大小参数
- 检查输入数据的有效性和连续性
- 优化滤波器参数设置

### 性能优化建议

#### 1. 内存优化
```python
# 限制缓冲区大小，避免内存溢出
processing_config = {
    'buffer_size': 500,  # 减少缓冲区大小
    'batch_size': 50,    # 适当的批处理大小
}

# 定期清理过期数据
import threading
import time

def periodic_cleanup():
    while True:
        cleanup_old_data(days_to_keep=7)
        time.sleep(3600)  # 每小时清理一次

cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()
```

#### 2. 网络优化
```python
# 调整上传参数以适应网络条件
aibox_config = AIBoxConfig(
    batch_size=20,        # 较小的批次大小
    upload_interval=60,   # 较长的上传间隔
    timeout=30           # 适当的超时时间
)
```

## 部署指南

### 1. 生产环境部署

#### 系统要求
- **操作系统**: Linux (推荐 Ubuntu 20.04+) 或 Windows Server
- **Python版本**: 3.8+
- **内存**: 最少2GB，推荐4GB+
- **存储**: 最少10GB可用空间
- **网络**: 稳定的以太网连接

#### 安装步骤

1. **创建虚拟环境**
```bash
python -m venv plc_aibox_env
source plc_aibox_env/bin/activate  # Linux
# 或
plc_aibox_env\Scripts\activate     # Windows
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置文件设置**
```bash
cp config_template.py config.py
# 编辑config.py文件，设置实际的PLC和AI-BOX参数
```

4. **创建系统服务** (Linux)
```bash
sudo cp plc_aibox.service /etc/systemd/system/
sudo systemctl enable plc_aibox
sudo systemctl start plc_aibox
```

### 2. Docker部署

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "plc_to_aibox_system.py"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  plc-aibox:
    build: .
    container_name: plc-aibox-system
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config.py:/app/config.py
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - industrial_network

networks:
  industrial_network:
    driver: bridge
```

#### 启动命令
```bash
docker-compose up -d
```

### 3. 监控和日志

#### 日志配置
```python
import logging
from logging.handlers import RotatingFileHandler

# 配置日志轮转
handler = RotatingFileHandler(
    'plc_aibox_system.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[handler, logging.StreamHandler()]
)
```

#### 系统监控脚本
```python
#!/usr/bin/env python3
import psutil
import time
import requests

def monitor_system():
    while True:
        # CPU和内存使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent

        # 磁盘使用率
        disk_percent = psutil.disk_usage('/').percent

        # 网络连接状态
        try:
            response = requests.get('http://localhost:8080/health', timeout=5)
            service_status = 'UP' if response.status_code == 200 else 'DOWN'
        except:
            service_status = 'DOWN'

        print(f"CPU: {cpu_percent}%, Memory: {memory_percent}%, "
              f"Disk: {disk_percent}%, Service: {service_status}")

        time.sleep(60)

if __name__ == "__main__":
    monitor_system()
```

## API文档

### 系统状态API

#### 获取系统状态
```http
GET /api/status
```

**响应示例**:
```json
{
    "status": "running",
    "uptime": 3600,
    "devices": [
        {
            "device_id": "PLC_001",
            "status": "online",
            "last_update": "2024-01-01T12:00:00Z",
            "data_rate": 0.98
        }
    ],
    "statistics": {
        "total_data_points": 145632,
        "upload_success_rate": 0.992,
        "average_quality_score": 0.87
    }
}
```

#### 获取设备列表
```http
GET /api/devices
```

#### 获取实时数据
```http
GET /api/data/realtime?device_id=PLC_001&parameters=vibration_x,temperature
```

### 配置管理API

#### 获取配置
```http
GET /api/config
```

#### 更新配置
```http
PUT /api/config
Content-Type: application/json

{
    "plc_config": {
        "scan_rate": 2000,
        "timeout": 10
    },
    "processing_config": {
        "buffer_size": 1500,
        "enable_fft": true
    }
}
```

## 扩展开发指南

### 添加新的PLC协议

1. **继承PLCDataCollector类**:
```python
class CustomPLCCollector(PLCDataCollector):
    def __init__(self, plc_config):
        super().__init__(plc_config)
        self.custom_client = CustomProtocolClient()

    def _collect_data_loop(self):
        while self.is_running:
            try:
                # 实现自定义协议的数据采集逻辑
                data = self.custom_client.read_data()
                data_points = self._convert_to_data_points(data)

                for point in data_points:
                    self.data_queue.put(point)

            except Exception as e:
                logger.error(f"自定义协议采集错误: {e}")
```

2. **实现协议特定的数据转换**:
```python
def _convert_to_data_points(self, raw_data):
    """将原始数据转换为PLCDataPoint格式"""
    points = []
    timestamp = datetime.datetime.now()

    for param_config in self.plc_config['parameters']:
        value = raw_data.get(param_config['address'])
        if value is not None:
            # 应用缩放和偏移
            scaled_value = value * param_config.get('scale', 1.0) + param_config.get('offset', 0.0)

            point = PLCDataPoint(
                timestamp=timestamp,
                device_id=self.plc_config['device_id'],
                parameter_name=param_config['name'],
                value=scaled_value,
                unit=param_config['unit']
            )
            points.append(point)

    return points
```

### 自定义数据处理算法

1. **扩展DataProcessor类**:
```python
class CustomDataProcessor(DataProcessor):
    def __init__(self, config):
        super().__init__(config)
        self.custom_algorithms = self._load_custom_algorithms()

    def _apply_custom_processing(self, data):
        """应用自定义处理算法"""
        processed_data = {}

        for param_name, value in data.items():
            # 应用自定义算法
            if param_name in self.custom_algorithms:
                algorithm = self.custom_algorithms[param_name]
                processed_data[param_name] = algorithm.process(value)
            else:
                processed_data[param_name] = value

        return processed_data
```

2. **实现自定义特征提取**:
```python
def extract_custom_features(self, signal_data):
    """提取自定义特征"""
    features = {}

    # 时域特征
    features['mean'] = np.mean(signal_data)
    features['std'] = np.std(signal_data)
    features['rms'] = np.sqrt(np.mean(signal_data**2))
    features['peak_to_peak'] = np.max(signal_data) - np.min(signal_data)
    features['crest_factor'] = np.max(np.abs(signal_data)) / features['rms']
    features['kurtosis'] = scipy.stats.kurtosis(signal_data)
    features['skewness'] = scipy.stats.skew(signal_data)

    # 频域特征
    fft_result = np.fft.fft(signal_data)
    frequencies = np.fft.fftfreq(len(signal_data))
    power_spectrum = np.abs(fft_result)**2

    features['dominant_frequency'] = frequencies[np.argmax(power_spectrum[1:len(power_spectrum)//2]) + 1]
    features['spectral_centroid'] = np.sum(frequencies[:len(frequencies)//2] * power_spectrum[:len(power_spectrum)//2]) / np.sum(power_spectrum[:len(power_spectrum)//2])
    features['spectral_rolloff'] = self._calculate_spectral_rolloff(frequencies, power_spectrum)

    return features
```

### 添加新的上传目标

1. **实现新的上传器**:
```python
class CustomUploader:
    def __init__(self, config):
        self.config = config
        self.client = CustomAPIClient(config)

    async def upload_data(self, processed_data):
        """上传数据到自定义目标"""
        try:
            # 转换数据格式
            upload_payload = self._format_data_for_upload(processed_data)

            # 发送数据
            response = await self.client.post('/api/upload', data=upload_payload)

            if response.status == 200:
                logger.info(f"成功上传 {len(processed_data)} 条数据")
                return True
            else:
                logger.error(f"上传失败: {response.status}")
                return False

        except Exception as e:
            logger.error(f"上传异常: {e}")
            return False
```

## 最佳实践

### 性能优化

1. **数据采集优化**:
   - 合理设置采集频率，避免过度采集
   - 使用批量读取减少网络开销
   - 实现连接池管理多个PLC设备

2. **数据处理优化**:
   - 使用NumPy向量化操作提高计算效率
   - 合理设置缓冲区大小，平衡内存和性能
   - 考虑使用多进程处理大量数据

3. **存储优化**:
   - 定期清理过期数据
   - 使用数据库索引优化查询性能
   - 考虑使用时序数据库存储大量时间序列数据

### 安全考虑

1. **网络安全**:
   - 使用VPN或专用网络连接PLC设备
   - 实施访问控制和身份认证
   - 加密敏感数据传输

2. **数据安全**:
   - 定期备份重要数据
   - 实施数据完整性检查
   - 考虑数据加密存储

### 可靠性设计

1. **故障恢复**:
   - 实现自动重连机制
   - 设计数据缓存和重传机制
   - 监控系统健康状态

2. **高可用性**:
   - 部署多个采集节点实现冗余
   - 使用负载均衡分散处理压力
   - 实施故障转移机制

## 技术支持

### 常见问题解答

**Q: 如何添加新的传感器参数？**
A: 在config.py的PLC_CONFIG中添加新的参数配置，包括名称、地址、类型等信息。

**Q: 系统支持哪些PLC品牌？**
A: 目前支持西门子、施耐德、AB等主流品牌，通过Modbus和OPC UA协议通信。

**Q: 如何调整数据处理算法？**
A: 修改PROCESSING_CONFIG中的滤波器配置，或扩展DataProcessor类实现自定义算法。

**Q: 数据上传失败怎么办？**
A: 检查网络连接、API配置和认证信息，查看日志获取详细错误信息。

### 联系方式

- **技术支持邮箱**: support@example.com
- **技术支持电话**: 400-xxx-xxxx
- **在线文档**: https://docs.example.com
- **GitHub仓库**: https://github.com/your-repo/plc-aibox-system
- **问题反馈**: https://github.com/your-repo/plc-aibox-system/issues

---

**版权声明**: 本系统遵循MIT开源协议，欢迎贡献代码和反馈问题。
