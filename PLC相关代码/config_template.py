#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC到AI-BOX系统配置文件模板
请根据实际环境修改相应参数
"""

from PLC相关代码.plc_to_aibox_system import AIBoxConfig

# =============================================================================
# PLC设备配置
# =============================================================================

# 主PLC配置
PLC_CONFIG = {
    # 基本连接参数
    'ip_address': '192.168.1.10',        # PLC设备IP地址
    'port': 502,                         # 通信端口 (Modbus TCP: 502, OPC UA: 4840)
    'device_id': 'PLC_001',              # 设备唯一标识
    'protocol': 'modbus_tcp',            # 通信协议: modbus_tcp, modbus_rtu, opcua
    'scan_rate': 1000,                   # 数据扫描周期(毫秒)
    'timeout': 5,                        # 连接超时时间(秒)
    'retry_count': 3,                    # 连接重试次数
    'retry_delay': 2,                    # 重试间隔(秒)
    
    # Modbus特定参数
    'unit_id': 1,                        # Modbus从站ID
    'byte_order': 'big',                 # 字节序: big, little
    'word_order': 'big',                 # 字序: big, little
    
    # OPC UA特定参数 (如果使用OPC UA)
    'endpoint': 'opc.tcp://192.168.1.10:4840',
    'security_policy': 'None',           # 安全策略: None, Basic256Sha256
    'username': '',                      # 用户名 (可选)
    'password': '',                      # 密码 (可选)
    
    # 数据点配置
    'parameters': [
        # 振动传感器数据
        {
            'name': 'vibration_x',           # 参数名称
            'address': 'DB1.DBD0',           # 西门子地址格式
            # 'address': 40001,              # Modbus地址格式
            # 'node_id': 'ns=2;s=Vibration.X', # OPC UA节点ID格式
            'type': 'REAL',                  # 数据类型: REAL, INT, DINT, BOOL
            'unit': 'mm/s',                  # 单位
            'scale': 1.0,                    # 缩放因子
            'offset': 0.0,                   # 偏移量
            'min_value': -100.0,             # 最小有效值
            'max_value': 100.0,              # 最大有效值
            'description': 'X轴振动速度'
        },
        {
            'name': 'vibration_y',
            'address': 'DB1.DBD4',
            'type': 'REAL',
            'unit': 'mm/s',
            'scale': 1.0,
            'offset': 0.0,
            'min_value': -100.0,
            'max_value': 100.0,
            'description': 'Y轴振动速度'
        },
        {
            'name': 'vibration_z',
            'address': 'DB1.DBD8',
            'type': 'REAL',
            'unit': 'mm/s',
            'scale': 1.0,
            'offset': 0.0,
            'min_value': -100.0,
            'max_value': 100.0,
            'description': 'Z轴振动速度'
        },
        # 温度传感器数据
        {
            'name': 'temperature_bearing1',
            'address': 'DB1.DBD12',
            'type': 'REAL',
            'unit': '°C',
            'scale': 1.0,
            'offset': 0.0,
            'min_value': -40.0,
            'max_value': 150.0,
            'description': '轴承1温度'
        },
        {
            'name': 'temperature_bearing2',
            'address': 'DB1.DBD16',
            'type': 'REAL',
            'unit': '°C',
            'scale': 1.0,
            'offset': 0.0,
            'min_value': -40.0,
            'max_value': 150.0,
            'description': '轴承2温度'
        },
        # 压力传感器数据
        {
            'name': 'pressure_inlet',
            'address': 'DB1.DBD20',
            'type': 'REAL',
            'unit': 'bar',
            'scale': 0.01,                   # 如果PLC中存储的是整数*100
            'offset': 0.0,
            'min_value': 0.0,
            'max_value': 50.0,
            'description': '进口压力'
        },
        {
            'name': 'pressure_outlet',
            'address': 'DB1.DBD24',
            'type': 'REAL',
            'unit': 'bar',
            'scale': 0.01,
            'offset': 0.0,
            'min_value': 0.0,
            'max_value': 50.0,
            'description': '出口压力'
        },
        # 流量传感器数据
        {
            'name': 'flow_rate',
            'address': 'DB1.DBD28',
            'type': 'REAL',
            'unit': 'L/min',
            'scale': 1.0,
            'offset': 0.0,
            'min_value': 0.0,
            'max_value': 1000.0,
            'description': '流量'
        },
        # 转速传感器数据
        {
            'name': 'motor_speed',
            'address': 'DB1.DBD32',
            'type': 'REAL',
            'unit': 'rpm',
            'scale': 1.0,
            'offset': 0.0,
            'min_value': 0.0,
            'max_value': 3600.0,
            'description': '电机转速'
        },
        # 电流传感器数据
        {
            'name': 'motor_current',
            'address': 'DB1.DBD36',
            'type': 'REAL',
            'unit': 'A',
            'scale': 1.0,
            'offset': 0.0,
            'min_value': 0.0,
            'max_value': 100.0,
            'description': '电机电流'
        },
        # 设备状态
        {
            'name': 'device_status',
            'address': 'DB1.DBX40.0',
            'type': 'BOOL',
            'unit': '',
            'scale': 1.0,
            'offset': 0.0,
            'description': '设备运行状态'
        },
        {
            'name': 'alarm_status',
            'address': 'DB1.DBX40.1',
            'type': 'BOOL',
            'unit': '',
            'scale': 1.0,
            'offset': 0.0,
            'description': '报警状态'
        }
    ]
}

# 多设备配置示例
MULTI_PLC_CONFIG = [
    {
        **PLC_CONFIG,
        'device_id': 'PLC_001',
        'ip_address': '192.168.1.10',
        'description': '主生产线设备'
    },
    {
        **PLC_CONFIG,
        'device_id': 'PLC_002',
        'ip_address': '192.168.1.11',
        'description': '辅助生产线设备'
    }
]

# =============================================================================
# AI-BOX配置
# =============================================================================

AIBOX_CONFIG = AIBoxConfig(
    ip_address="192.168.1.100",          # AI-BOX设备IP地址
    port=8080,                           # API服务端口
    api_endpoint="/api/data/upload",     # 数据上传接口路径
    auth_token="your_auth_token_here",   # 认证令牌，请联系AI-BOX管理员获取
    batch_size=50,                       # 批量上传数据条数
    upload_interval=30,                  # 上传间隔时间(秒)
    timeout=30,                          # HTTP请求超时时间(秒)
    max_retries=3,                       # 上传失败重试次数
    retry_delay=5                        # 重试间隔时间(秒)
)

# =============================================================================
# 数据处理配置
# =============================================================================

PROCESSING_CONFIG = {
    # 缓冲区配置
    'buffer_size': 1000,                 # 历史数据缓冲区大小
    'max_queue_size': 10000,             # 最大队列大小
    
    # 降采样配置
    'downsample_factor': 1,              # 降采样因子 (1=不降采样)
    'downsample_method': 'average',      # 降采样方法: average, max, min, last
    
    # FFT分析配置
    'enable_fft': True,                  # 启用FFT特征提取
    'fft_window_size': 128,              # FFT窗口大小 (建议2的幂次)
    'fft_overlap': 0.5,                  # 窗口重叠率
    'fft_parameters': [                  # 需要进行FFT分析的参数
        'vibration_x', 'vibration_y', 'vibration_z'
    ],
    
    # 滤波器配置
    'filter_config': {
        # 振动信号带通滤波
        'vibration': {
            'type': 'bandpass',          # 滤波器类型: lowpass, highpass, bandpass, bandstop
            'low_freq': 0.1,             # 低频截止频率 (Hz)
            'high_freq': 0.4,            # 高频截止频率 (Hz)
            'order': 4,                  # 滤波器阶数
            'method': 'butterworth'      # 滤波器方法: butterworth, chebyshev1, chebyshev2
        },
        # 温度信号低通滤波
        'temperature': {
            'type': 'lowpass',
            'cutoff_freq': 0.1,          # 截止频率 (Hz)
            'order': 4,
            'method': 'butterworth'
        },
        # 压力信号低通滤波
        'pressure': {
            'type': 'lowpass',
            'cutoff_freq': 0.05,
            'order': 2,
            'method': 'butterworth'
        },
        # 默认滤波器 (移动平均)
        'default': {
            'type': 'moving_average',
            'window_size': 5,            # 移动平均窗口大小
            'method': 'simple'           # 移动平均方法: simple, weighted, exponential
        }
    },
    
    # 异常检测配置
    'anomaly_detection': {
        'enable': True,                  # 启用异常检测
        'method': 'statistical',        # 检测方法: statistical, isolation_forest, one_class_svm
        'threshold': 3.0,                # 统计方法的标准差阈值
        'window_size': 100,              # 检测窗口大小
        'min_samples': 50                # 最少样本数
    },
    
    # 数据质量评估配置
    'quality_assessment': {
        'completeness_weight': 0.4,      # 完整性权重
        'accuracy_weight': 0.3,          # 准确性权重
        'stability_weight': 0.3,         # 稳定性权重
        'min_quality_score': 0.6         # 最低质量分数阈值
    }
}

# =============================================================================
# 数据库配置
# =============================================================================

DATABASE_CONFIG = {
    'type': 'sqlite',                    # 数据库类型: sqlite, mysql, postgresql
    'path': 'plc_data.db',              # SQLite数据库文件路径
    'backup_interval': 3600,             # 数据库备份间隔(秒)
    'cleanup_days': 30,                  # 数据保留天数
    'batch_insert_size': 1000,           # 批量插入大小
    
    # MySQL/PostgreSQL配置 (如果使用)
    'host': 'localhost',
    'port': 3306,                        # MySQL: 3306, PostgreSQL: 5432
    'username': 'plc_user',
    'password': 'your_password',
    'database': 'plc_data'
}

# =============================================================================
# 日志配置
# =============================================================================

LOGGING_CONFIG = {
    'level': 'INFO',                     # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_path': 'plc_aibox_system.log',
    'max_file_size': 10 * 1024 * 1024,  # 最大文件大小 (10MB)
    'backup_count': 5,                   # 备份文件数量
    'console_output': True               # 是否输出到控制台
}

# =============================================================================
# 系统配置
# =============================================================================

SYSTEM_CONFIG = {
    'max_workers': 4,                    # 最大工作线程数
    'health_check_interval': 60,         # 健康检查间隔(秒)
    'auto_restart': True,                # 自动重启功能
    'max_restart_attempts': 5,           # 最大重启尝试次数
    'restart_delay': 10,                 # 重启延迟时间(秒)
    'enable_web_interface': True,        # 启用Web管理界面
    'web_port': 8888,                    # Web界面端口
    'enable_metrics': True,              # 启用性能指标收集
    'metrics_interval': 30               # 指标收集间隔(秒)
}
