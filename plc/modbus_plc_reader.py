#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
西门子S7-300 Modbus TCP/IP数据读取器
专门适配西门子S7-300系列PLC的Modbus TCP/IP协议

西门子S7-300特点:
- 地址映射: I区、Q区、M区、DB区
- 字节序: 大端序 (Big-Endian)
- 数据类型: BOOL、BYTE、WORD、DWORD、INT、DINT、REAL
- 地址格式: 按字节寻址

支持功能:
- S7-300专用地址映射
- 西门子数据类型转换
- DB块数据读取
- 连接管理和错误处理
- 批量数据读取
"""

import struct
import socket
import time
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class S7Register:
    """西门子S7-300寄存器配置"""
    name: str                    # 数据名称
    address: str                 # S7地址格式: "DB1.DBW0", "MW10", "IW0", "QW2"
    data_type: str              # S7数据类型: 'BOOL', 'BYTE', 'WORD', 'DWORD', 'INT', 'DINT', 'REAL'
    bit_offset: int = 0         # 位偏移 (仅BOOL类型使用)
    scale: float = 1.0          # 缩放因子
    offset: float = 0.0         # 偏移量
    unit: str = ""              # 单位
    description: str = ""       # 描述

class S7ModbusTCPClient:
    """西门子S7-300 Modbus TCP/IP客户端"""

    def __init__(self, host: str, port: int = 502, timeout: float = 5.0, unit_id: int = 1):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.unit_id = unit_id
        self.socket = None
        self.transaction_id = 0
        self.connected = False

        # 西门子S7-300地址映射表
        self.s7_address_mapping = {
            'I': {'base': 0, 'type': 'input'},      # 输入区 (Input)
            'Q': {'base': 512, 'type': 'holding'},  # 输出区 (Output)
            'M': {'base': 4096, 'type': 'holding'}, # 标志区 (Memory)
            'DB': {'base': 8192, 'type': 'holding'} # 数据块区 (Data Block)
        }

    def parse_s7_address(self, s7_address: str) -> tuple:
        """
        解析S7地址格式
        支持格式:
        - DB1.DBW0 (数据块1，字偏移0)
        - DB1.DBD4 (数据块1，双字偏移4)
        - MW10 (标志区字偏移10)
        - IW0 (输入区字偏移0)
        - QB2 (输出区字节偏移2)
        """
        import re

        # 数据块格式: DB1.DBW0, DB1.DBD4, DB1.DBB2
        db_pattern = r'DB(\d+)\.DB([BWDX])(\d+)'
        db_match = re.match(db_pattern, s7_address.upper())

        if db_match:
            db_number = int(db_match.group(1))
            data_type = db_match.group(2)  # B=Byte, W=Word, D=DWord, X=Bit
            offset = int(db_match.group(3))

            # 计算Modbus地址 (DB块基址 + DB号*1000 + 偏移)
            modbus_address = self.s7_address_mapping['DB']['base'] + db_number * 1000 + offset
            register_type = self.s7_address_mapping['DB']['type']

            return modbus_address, register_type, data_type

        # 标准格式: MW10, IW0, QB2
        std_pattern = r'([IQMV])([BWDX])(\d+)'
        std_match = re.match(std_pattern, s7_address.upper())

        if std_match:
            area = std_match.group(1)  # I, Q, M, V
            data_type = std_match.group(2)  # B, W, D, X
            offset = int(std_match.group(3))

            if area in self.s7_address_mapping:
                modbus_address = self.s7_address_mapping[area]['base'] + offset
                register_type = self.s7_address_mapping[area]['type']
                return modbus_address, register_type, data_type

        raise ValueError(f"不支持的S7地址格式: {s7_address}")

    def connect(self) -> bool:
        """连接到PLC设备"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            self.connected = True
            logging.info(f"成功连接到PLC: {self.host}:{self.port}")
            return True
        except Exception as e:
            logging.error(f"连接PLC失败: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.socket:
            try:
                self.socket.close()
                self.connected = False
                logging.info("已断开PLC连接")
            except:
                pass
    
    def _get_transaction_id(self) -> int:
        """获取事务ID"""
        self.transaction_id = (self.transaction_id + 1) % 65536
        return self.transaction_id
    
    def _build_request(self, function_code: int, address: int, count: int, data: bytes = b'') -> bytes:
        """构建Modbus请求"""
        transaction_id = self._get_transaction_id()
        protocol_id = 0
        length = 6 + len(data)
        
        # MBAP头部
        mbap_header = struct.pack('>HHHB', transaction_id, protocol_id, length, self.unit_id)
        
        # PDU
        pdu = struct.pack('>BHH', function_code, address, count) + data
        
        return mbap_header + pdu
    
    def _parse_response(self, response: bytes) -> bytes:
        """解析Modbus响应"""
        if len(response) < 8:
            raise Exception("响应数据太短")
        
        # 解析MBAP头部
        transaction_id, protocol_id, length, unit_id = struct.unpack('>HHHB', response[:7])
        
        # 检查单元ID
        if unit_id != self.unit_id:
            raise Exception(f"单元ID不匹配: 期望{self.unit_id}, 收到{unit_id}")
        
        # 解析PDU
        function_code = response[7]
        
        # 检查异常响应
        if function_code & 0x80:
            exception_code = response[8]
            raise Exception(f"Modbus异常: 功能码{function_code & 0x7F}, 异常码{exception_code}")
        
        return response[8:]  # 返回数据部分
    
    def read_holding_registers(self, address: int, count: int) -> List[int]:
        """读取保持寄存器 (功能码03)"""
        if not self.connected:
            raise Exception("未连接到PLC")
        
        request = self._build_request(0x03, address, count)
        
        try:
            self.socket.send(request)
            response = self.socket.recv(1024)
            
            data = self._parse_response(response)
            byte_count = data[0]
            
            if byte_count != count * 2:
                raise Exception(f"数据长度不匹配: 期望{count * 2}, 收到{byte_count}")
            
            # 解析寄存器值
            values = []
            for i in range(count):
                value = struct.unpack('>H', data[1 + i * 2:3 + i * 2])[0]
                values.append(value)
            
            return values
            
        except Exception as e:
            logging.error(f"读取保持寄存器失败: {e}")
            raise
    
    def read_input_registers(self, address: int, count: int) -> List[int]:
        """读取输入寄存器 (功能码04)"""
        if not self.connected:
            raise Exception("未连接到PLC")
        
        request = self._build_request(0x04, address, count)
        
        try:
            self.socket.send(request)
            response = self.socket.recv(1024)
            
            data = self._parse_response(response)
            byte_count = data[0]
            
            values = []
            for i in range(count):
                value = struct.unpack('>H', data[1 + i * 2:3 + i * 2])[0]
                values.append(value)
            
            return values
            
        except Exception as e:
            logging.error(f"读取输入寄存器失败: {e}")
            raise
    
    def read_coils(self, address: int, count: int) -> List[bool]:
        """读取线圈 (功能码01)"""
        if not self.connected:
            raise Exception("未连接到PLC")
        
        request = self._build_request(0x01, address, count)
        
        try:
            self.socket.send(request)
            response = self.socket.recv(1024)
            
            data = self._parse_response(response)
            byte_count = data[0]
            
            values = []
            for byte_idx in range(byte_count):
                byte_value = data[1 + byte_idx]
                for bit_idx in range(8):
                    if len(values) >= count:
                        break
                    bit_value = bool(byte_value & (1 << bit_idx))
                    values.append(bit_value)
            
            return values[:count]
            
        except Exception as e:
            logging.error(f"读取线圈失败: {e}")
            raise
    
    def read_discrete_inputs(self, address: int, count: int) -> List[bool]:
        """读取离散输入 (功能码02)"""
        if not self.connected:
            raise Exception("未连接到PLC")
        
        request = self._build_request(0x02, address, count)
        
        try:
            self.socket.send(request)
            response = self.socket.recv(1024)
            
            data = self._parse_response(response)
            byte_count = data[0]
            
            values = []
            for byte_idx in range(byte_count):
                byte_value = data[1 + byte_idx]
                for bit_idx in range(8):
                    if len(values) >= count:
                        break
                    bit_value = bool(byte_value & (1 << bit_idx))
                    values.append(bit_value)
            
            return values[:count]
            
        except Exception as e:
            logging.error(f"读取离散输入失败: {e}")
            raise

class S7DataReader:
    """西门子S7-300数据读取器"""

    def __init__(self, host: str, port: int = 502, unit_id: int = 1):
        self.client = S7ModbusTCPClient(host, port, unit_id=unit_id)
        self.registers: List[S7Register] = []
        
    def add_register(self, register: S7Register):
        """添加寄存器配置"""
        self.registers.append(register)

    def add_registers_from_config(self, config: List[Dict]):
        """从配置列表添加寄存器"""
        for reg_config in config:
            register = S7Register(**reg_config)
            self.add_register(register)
    
    def connect(self) -> bool:
        """连接到PLC"""
        return self.client.connect()
    
    def disconnect(self):
        """断开连接"""
        self.client.disconnect()
    
    def _convert_s7_data_type(self, raw_values: List[int], s7_data_type: str, bit_offset: int = 0) -> Union[int, float, bool]:
        """
        转换西门子S7数据类型
        支持: BOOL, BYTE, WORD, DWORD, INT, DINT, REAL
        """
        if s7_data_type == 'BOOL' or s7_data_type == 'X':
            # 布尔值，从指定位提取
            if len(raw_values) == 0:
                return False
            byte_value = raw_values[0] & 0xFF  # 取低字节
            return bool(byte_value & (1 << bit_offset))

        elif s7_data_type == 'BYTE' or s7_data_type == 'B':
            # 8位无符号整数
            return raw_values[0] & 0xFF

        elif s7_data_type == 'WORD' or s7_data_type == 'W':
            # 16位无符号整数
            return raw_values[0] & 0xFFFF

        elif s7_data_type == 'DWORD' or s7_data_type == 'D':
            # 32位无符号整数，需要2个寄存器
            if len(raw_values) < 2:
                raise ValueError("DWORD需要2个寄存器")
            # 西门子使用大端序
            high, low = raw_values[0], raw_values[1]
            return (high << 16) | low

        elif s7_data_type == 'INT':
            # 16位有符号整数
            value = raw_values[0] & 0xFFFF
            return value if value < 32768 else value - 65536

        elif s7_data_type == 'DINT':
            # 32位有符号整数，需要2个寄存器
            if len(raw_values) < 2:
                raise ValueError("DINT需要2个寄存器")
            high, low = raw_values[0], raw_values[1]
            value = (high << 16) | low
            return value if value < 2147483648 else value - 4294967296

        elif s7_data_type == 'REAL':
            # IEEE 754单精度浮点数，需要2个寄存器
            if len(raw_values) < 2:
                raise ValueError("REAL需要2个寄存器")
            # 西门子REAL格式：高字在前，低字在后
            high, low = raw_values[0], raw_values[1]
            int_value = (high << 16) | low
            return struct.unpack('>f', struct.pack('>I', int_value))[0]

        else:
            raise ValueError(f"不支持的S7数据类型: {s7_data_type}")
    
    def read_register(self, register: S7Register) -> Any:
        """读取单个S7寄存器"""
        try:
            # 解析S7地址
            modbus_address, register_type, s7_data_type = self.client.parse_s7_address(register.address)

            # 确定需要读取的寄存器数量
            if s7_data_type in ['B', 'BYTE', 'W', 'WORD', 'INT', 'X', 'BOOL']:
                count = 1
            elif s7_data_type in ['D', 'DWORD', 'DINT', 'REAL']:
                count = 2
            else:
                count = 1

            # 根据寄存器类型读取原始数据
            if register_type == 'holding':
                raw_values = self.client.read_holding_registers(modbus_address, count)
            elif register_type == 'input':
                raw_values = self.client.read_input_registers(modbus_address, count)
            else:
                raise ValueError(f"不支持的寄存器类型: {register_type}")

            # 转换S7数据类型
            value = self._convert_s7_data_type(raw_values, register.data_type, register.bit_offset)

            # 应用缩放和偏移
            if isinstance(value, (int, float)):
                value = value * register.scale + register.offset

            return value

        except Exception as e:
            logging.error(f"读取S7寄存器 {register.name} ({register.address}) 失败: {e}")
            return None
    
    def read_all_registers(self) -> Dict[str, Any]:
        """读取所有配置的寄存器"""
        results = {}
        
        for register in self.registers:
            value = self.read_register(register)
            results[register.name] = {
                'value': value,
                'unit': register.unit,
                'description': register.description,
                'timestamp': datetime.now()
            }
        
        return results
    
    def read_monitoring_data(self) -> Dict[str, Any]:
        """读取监测站数据格式"""
        data = self.read_all_registers()
        
        # 转换为监测站数据格式
        monitoring_data = {
            'timestamp': datetime.now(),
            'station_id': 'PLC_001',
            'station_name': 'PLC监测站'
        }
        
        # 映射常见的监测参数
        parameter_mapping = {
            'pm25': 'pm25_concentration',
            'pm10': 'pm10_concentration', 
            'wind_speed': 'wind_speed',
            'wind_direction': 'wind_direction',
            'temperature': 'temperature',
            'humidity': 'humidity',
            'pressure': 'pressure'
        }
        
        for key, mapped_key in parameter_mapping.items():
            if key in data and data[key]['value'] is not None:
                monitoring_data[mapped_key] = data[key]['value']
        
        return monitoring_data
