#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-BOX端Modbus PLC数据读取程序
实现从PLC通过Modbus协议读取传感器数据并进行处理分析
"""

from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
import struct
import time
import json
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from dataclasses import dataclass
import sqlite3
import queue

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aibox_s7_reader.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ModbusDataPoint:
    """Modbus数据点结构"""
    timestamp: datetime
    address: int
    name: str
    value: float
    data_type: str
    unit: str
    quality: str = "GOOD"

@dataclass
class ModbusConfig:
    """Modbus连接配置"""
    ip_address: str = "192.168.1.10"
    port: int = 502
    unit_id: int = 1
    timeout: int = 5  # 秒
    
class ModbusDataReader:
    """Modbus PLC数据读取器"""

    def __init__(self, config: ModbusConfig):
        self.config = config
        self.client = ModbusTcpClient(host=config.ip_address, port=config.port, timeout=config.timeout)
        self.is_connected = False
        self.data_queue = queue.Queue(maxsize=10000)
        self.is_running = False
        self.read_thread = None

        # 数据点配置 - 根据实际PLC程序配置
        self.data_points = {
            # 振动传感器数据 (保持寄存器)
            'vibration_x': {
                'address': 40001,    # 保持寄存器地址
                'type': 'FLOAT32',   # 32位浮点数
                'unit': 'mm/s',
                'description': 'X轴振动速度',
                'function_code': 3   # 读保持寄存器
            },
            'vibration_y': {
                'address': 40003,    # 保持寄存器地址
                'type': 'FLOAT32',
                'unit': 'mm/s',
                'description': 'Y轴振动速度',
                'function_code': 3
            },
            'vibration_z': {
                'address': 40005,    # 保持寄存器地址
                'type': 'FLOAT32',
                'unit': 'mm/s',
                'description': 'Z轴振动速度',
                'function_code': 3
            },
            # 温度传感器数据
            'temperature_1': {
                'address': 40007,    # 保持寄存器地址
                'type': 'FLOAT32',
                'unit': '°C',
                'description': '轴承1温度',
                'function_code': 3
            },
            'temperature_2': {
                'address': 40009,    # 保持寄存器地址
                'type': 'FLOAT32',
                'unit': '°C',
                'description': '轴承2温度',
                'function_code': 3
            },
            # 压力传感器数据
            'pressure_inlet': {
                'address': 40011,    # 保持寄存器地址
                'type': 'FLOAT32',
                'unit': 'bar',
                'description': '进口压力',
                'function_code': 3
            },
            'pressure_outlet': {
                'address': 40013,    # 保持寄存器地址
                'type': 'FLOAT32',
                'unit': 'bar',
                'description': '出口压力',
                'function_code': 3
            },
            # 流量传感器数据
            'flow_rate': {
                'address': 40015,    # 保持寄存器地址
                'type': 'FLOAT32',
                'unit': 'L/min',
                'description': '流量',
                'function_code': 3
            },
            # 转速传感器数据
            'motor_speed': {
                'address': 40017,    # 保持寄存器地址
                'type': 'FLOAT32',
                'unit': 'rpm',
                'description': '电机转速',
                'function_code': 3
            },
            # 电流传感器数据
            'motor_current': {
                'address': 40019,    # 保持寄存器地址
                'type': 'FLOAT32',
                'unit': 'A',
                'description': '电机电流',
                'function_code': 3
            },
            # 设备状态 (线圈)
            'device_status': {
                'address': 1,        # 线圈地址
                'type': 'BOOL',
                'unit': '',
                'description': '设备运行状态',
                'function_code': 1   # 读线圈
            },
            'alarm_status': {
                'address': 2,        # 线圈地址
                'type': 'BOOL',
                'unit': '',
                'description': '报警状态',
                'function_code': 1   # 读线圈
            }
        }
    
    def connect(self) -> bool:
        """连接到Modbus PLC"""
        try:
            logger.info(f"正在连接到Modbus PLC: {self.config.ip_address}:{self.config.port}")

            # 建立连接
            connection = self.client.connect()

            if connection:
                self.is_connected = True
                logger.info("Modbus PLC连接成功")

                # 测试读取一个寄存器验证连接
                try:
                    result = self.client.read_holding_registers(40001, 1, unit=self.config.unit_id)
                    if not result.isError():
                        logger.info("Modbus连接验证成功")
                    else:
                        logger.warning(f"Modbus连接验证失败: {result}")
                except Exception as e:
                    logger.warning(f"Modbus连接验证异常: {e}")

                return True
            else:
                logger.error("Modbus PLC连接失败")
                return False

        except Exception as e:
            logger.error(f"连接Modbus PLC异常: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """断开PLC连接"""
        try:
            if self.is_connected:
                self.client.close()
                self.is_connected = False
                logger.info("Modbus PLC连接已断开")
        except Exception as e:
            logger.error(f"断开Modbus PLC连接异常: {e}")
    
    def read_holding_registers(self, address: int, count: int) -> Optional[list]:
        """读取保持寄存器"""
        try:
            if not self.is_connected:
                logger.warning("PLC未连接，尝试重新连接")
                if not self.connect():
                    return None

            # 读取保持寄存器
            result = self.client.read_holding_registers(address, count, unit=self.config.unit_id)

            if result.isError():
                logger.error(f"读取保持寄存器{address}失败: {result}")
                return None

            return result.registers

        except Exception as e:
            logger.error(f"读取保持寄存器{address}异常: {e}")
            self.is_connected = False
            return None

    def read_coils(self, address: int, count: int) -> Optional[list]:
        """读取线圈"""
        try:
            if not self.is_connected:
                logger.warning("PLC未连接，尝试重新连接")
                if not self.connect():
                    return None

            # 读取线圈
            result = self.client.read_coils(address, count, unit=self.config.unit_id)

            if result.isError():
                logger.error(f"读取线圈{address}失败: {result}")
                return None

            return result.bits

        except Exception as e:
            logger.error(f"读取线圈{address}异常: {e}")
            self.is_connected = False
            return None

    def convert_registers_to_float32(self, registers: list, byte_order: str = 'big') -> float:
        """将两个寄存器转换为32位浮点数"""
        try:
            if len(registers) < 2:
                return 0.0

            # 组合两个16位寄存器为32位
            if byte_order == 'big':
                # 大端序：高位在前
                combined = (registers[0] << 16) | registers[1]
            else:
                # 小端序：低位在前
                combined = (registers[1] << 16) | registers[0]

            # 转换为浮点数
            packed = struct.pack('>I', combined)
            value = struct.unpack('>f', packed)[0]
            return float(value)

        except Exception as e:
            logger.error(f"寄存器转换浮点数失败: {e}")
            return 0.0

    def convert_registers_to_int32(self, registers: list, byte_order: str = 'big') -> int:
        """将两个寄存器转换为32位整数"""
        try:
            if len(registers) < 2:
                return 0

            # 组合两个16位寄存器为32位
            if byte_order == 'big':
                combined = (registers[0] << 16) | registers[1]
            else:
                combined = (registers[1] << 16) | registers[0]

            return int(combined)

        except Exception as e:
            logger.error(f"寄存器转换整数失败: {e}")
            return 0
    
    def read_all_data_points(self) -> List[ModbusDataPoint]:
        """读取所有配置的数据点"""
        data_points = []
        timestamp = datetime.now()

        try:
            # 解析每个数据点
            for name, config in self.data_points.items():
                try:
                    address = config['address']
                    data_type = config['type']
                    unit = config['unit']
                    function_code = config['function_code']

                    value = 0.0

                    # 根据功能码和数据类型读取数据
                    if function_code == 3:  # 读保持寄存器
                        if data_type == 'FLOAT32':
                            # 读取2个寄存器组成32位浮点数
                            registers = self.read_holding_registers(address, 2)
                            if registers:
                                value = self.convert_registers_to_float32(registers)
                        elif data_type == 'INT32':
                            # 读取2个寄存器组成32位整数
                            registers = self.read_holding_registers(address, 2)
                            if registers:
                                value = float(self.convert_registers_to_int32(registers))
                        elif data_type == 'INT16':
                            # 读取1个寄存器
                            registers = self.read_holding_registers(address, 1)
                            if registers:
                                value = float(registers[0])
                        else:
                            logger.warning(f"不支持的数据类型: {data_type}")
                            continue

                    elif function_code == 1:  # 读线圈
                        if data_type == 'BOOL':
                            coils = self.read_coils(address, 1)
                            if coils:
                                value = float(coils[0])
                        else:
                            logger.warning(f"线圈只支持BOOL类型，当前: {data_type}")
                            continue
                    else:
                        logger.warning(f"不支持的功能码: {function_code}")
                        continue

                    # 创建数据点
                    point = ModbusDataPoint(
                        timestamp=timestamp,
                        address=address,
                        name=name,
                        value=value,
                        data_type=data_type,
                        unit=unit,
                        quality="GOOD"
                    )

                    data_points.append(point)

                except Exception as e:
                    logger.error(f"解析数据点 {name} 失败: {e}")
                    continue

            logger.debug(f"成功读取 {len(data_points)} 个数据点")
            return data_points

        except Exception as e:
            logger.error(f"读取数据点失败: {e}")
            return data_points
    
    def start_reading(self, interval: float = 1.0):
        """启动数据读取线程"""
        if self.is_running:
            logger.warning("数据读取已在运行")
            return
        
        self.is_running = True
        self.read_thread = threading.Thread(
            target=self._reading_loop,
            args=(interval,),
            daemon=True
        )
        self.read_thread.start()
        logger.info(f"数据读取线程已启动，间隔: {interval}秒")
    
    def stop_reading(self):
        """停止数据读取"""
        self.is_running = False
        if self.read_thread:
            self.read_thread.join()
        logger.info("数据读取已停止")
    
    def _reading_loop(self, interval: float):
        """数据读取循环"""
        while self.is_running:
            try:
                # 读取数据点
                data_points = self.read_all_data_points()
                
                # 将数据放入队列
                for point in data_points:
                    if not self.data_queue.full():
                        self.data_queue.put(point)
                    else:
                        logger.warning("数据队列已满，丢弃数据")
                
                # 等待下次读取
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"数据读取循环异常: {e}")
                time.sleep(5)  # 异常时等待5秒再重试
    
    def get_data_batch(self, max_size: int = 100) -> List[ModbusDataPoint]:
        """获取一批数据"""
        batch = []
        for _ in range(min(max_size, self.data_queue.qsize())):
            try:
                batch.append(self.data_queue.get_nowait())
            except queue.Empty:
                break
        return batch
    
    def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            'connected': self.is_connected,
            'plc_ip': self.config.ip_address,
            'queue_size': self.data_queue.qsize(),
            'is_reading': self.is_running,
            'timestamp': datetime.now().isoformat()
        }

class DataProcessor:
    """数据处理器"""
    
    def __init__(self):
        self.db_path = "aibox_data.db"
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                data_type TEXT,
                quality TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON sensor_data(timestamp)
        ''')
        
        conn.commit()
        conn.close()
    
    def process_data_batch(self, data_points: List[ModbusDataPoint]):
        """处理数据批次"""
        if not data_points:
            return

        # 存储到数据库
        self._store_data(data_points)

        # 数据分析
        analysis_result = self._analyze_data(data_points)

        # 输出分析结果
        self._output_analysis(analysis_result)

    def _store_data(self, data_points: List[ModbusDataPoint]):
        """存储数据到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            for point in data_points:
                cursor.execute('''
                    INSERT INTO sensor_data (timestamp, name, value, unit, data_type, quality)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    point.timestamp.isoformat(),
                    point.name,
                    point.value,
                    point.unit,
                    point.data_type,
                    point.quality
                ))

            conn.commit()
            logger.debug(f"存储了 {len(data_points)} 个数据点")

        except Exception as e:
            logger.error(f"存储数据失败: {e}")
            conn.rollback()
        finally:
            conn.close()

    def _analyze_data(self, data_points: List[ModbusDataPoint]) -> Dict[str, Any]:
        """分析数据"""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'data_count': len(data_points),
            'parameters': {}
        }
        
        # 按参数分组分析
        param_data = {}
        for point in data_points:
            if point.name not in param_data:
                param_data[point.name] = []
            param_data[point.name].append(point.value)
        
        # 计算统计信息
        for param_name, values in param_data.items():
            if values:
                analysis['parameters'][param_name] = {
                    'count': len(values),
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'latest': values[-1]
                }
        
        return analysis
    
    def _output_analysis(self, analysis: Dict[str, Any]):
        """输出分析结果"""
        logger.info("=== 数据分析结果 ===")
        logger.info(f"时间: {analysis['timestamp']}")
        logger.info(f"数据点数量: {analysis['data_count']}")
        
        for param_name, stats in analysis['parameters'].items():
            logger.info(f"{param_name}: 最新值={stats['latest']:.2f}, "
                       f"平均值={stats['mean']:.2f}, "
                       f"标准差={stats['std']:.2f}")

def main():
    """主函数"""
    logger.info("AI-BOX Modbus数据读取程序启动")

    # 创建Modbus配置
    modbus_config = ModbusConfig(
        ip_address="192.168.1.10",  # 修改为实际PLC IP
        port=502,
        unit_id=1
    )

    # 创建数据读取器和处理器
    reader = ModbusDataReader(modbus_config)
    processor = DataProcessor()

    try:
        # 连接PLC
        if not reader.connect():
            logger.error("无法连接到PLC，程序退出")
            return

        # 启动数据读取
        reader.start_reading(interval=1.0)  # 每秒读取一次

        logger.info("系统运行中，按Ctrl+C停止...")

        # 主循环
        while True:
            # 获取数据批次
            data_batch = reader.get_data_batch(50)

            if data_batch:
                # 处理数据
                processor.process_data_batch(data_batch)

            # 显示连接状态
            status = reader.get_connection_status()
            if not status['connected']:
                logger.warning("PLC连接丢失，尝试重连...")
                reader.connect()

            time.sleep(5)  # 每5秒处理一次

    except KeyboardInterrupt:
        logger.info("收到停止信号")
    except Exception as e:
        logger.error(f"程序异常: {e}")
    finally:
        # 清理资源
        reader.stop_reading()
        reader.disconnect()
        logger.info("程序已停止")

if __name__ == "__main__":
    main()
