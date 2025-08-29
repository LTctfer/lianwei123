#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC Modbus TCP/IP数据读取器
根据PLCTags.csv自动生成地址映射并读取PLC数据

地址映射规则:
- Q0.0 = Modbus地址0, Q0.1 = 1, Q10.1 = 11
- I区: 输入线圈，从地址10000开始
- M区: 标志位，从地址20000开始
- MW/MD: 保持寄存器，从地址40000开始

PLC IP: 192.168.0.1
"""

import struct
import socket
import time
import logging
import pandas as pd
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import re

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class PLCTag:
    """PLC标签数据结构"""
    name: str
    logical_address: str
    data_type: str
    comment: str
    modbus_address: int
    register_type: str  # 'coil', 'discrete', 'holding', 'input'
    bit_offset: int = 0

class ModbusTCPClient:
    """Modbus TCP/IP客户端"""
    
    def __init__(self, host: str, port: int = 502, timeout: float = 5.0, unit_id: int = 1):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.unit_id = unit_id
        self.socket = None
        self.transaction_id = 0
        self.connected = False
        
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

class PLCTagMapper:
    """PLC标签地址映射器"""
    
    def __init__(self):
        self.tags: List[PLCTag] = []
        
    def parse_plc_address(self, logical_address: str) -> tuple:
        """
        解析PLC逻辑地址
        支持格式: %Q0.0, %I0.7, %M1.1, %MW100, %MD100等
        """
        # 移除%符号
        address = logical_address.strip('%')
        
        # 解析不同类型的地址
        if address.startswith('Q'):
            # 输出线圈: Q0.0, Q10.1等
            match = re.match(r'Q(\d+)\.(\d+)', address)
            if match:
                byte_addr = int(match.group(1))
                bit_addr = int(match.group(2))
                # 按照您的映射规则: Q0.0=0, Q0.1=1, Q10.1=11
                modbus_addr = byte_addr * 8 + bit_addr
                return modbus_addr, 'coil', bit_addr
                
        elif address.startswith('I'):
            # 输入线圈: I0.0, I0.7等
            match = re.match(r'I(\d+)\.(\d+)', address)
            if match:
                byte_addr = int(match.group(1))
                bit_addr = int(match.group(2))
                modbus_addr = 10000 + byte_addr * 8 + bit_addr  # I区从10000开始
                return modbus_addr, 'discrete', bit_addr
                
        elif address.startswith('MW'):
            # 标志字: MW100等
            match = re.match(r'MW(\d+)', address)
            if match:
                word_addr = int(match.group(1))
                modbus_addr = 40000 + word_addr  # MW从40000开始
                return modbus_addr, 'holding', 0
                
        elif address.startswith('MD'):
            # 标志双字: MD100等
            match = re.match(r'MD(\d+)', address)
            if match:
                dword_addr = int(match.group(1))
                modbus_addr = 40000 + dword_addr // 2  # MD按双字地址
                return modbus_addr, 'holding', 0
                
        elif address.startswith('M'):
            # 标志位: M1.1, M100.0等
            match = re.match(r'M(\d+)\.(\d+)', address)
            if match:
                byte_addr = int(match.group(1))
                bit_addr = int(match.group(2))
                modbus_addr = 20000 + byte_addr * 8 + bit_addr  # M区从20000开始
                return modbus_addr, 'coil', bit_addr
        
        raise ValueError(f"不支持的地址格式: {logical_address}")
    
    def load_tags_from_csv(self, csv_file: str):
        """从CSV文件加载标签"""
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            
            for _, row in df.iterrows():
                try:
                    name = row['Name']
                    logical_address = row['Logical Address']
                    data_type = row['Data Type']
                    comment = row.get('Comment', '')
                    
                    # 解析地址
                    modbus_address, register_type, bit_offset = self.parse_plc_address(logical_address)
                    
                    # 创建标签
                    tag = PLCTag(
                        name=name,
                        logical_address=logical_address,
                        data_type=data_type,
                        comment=comment,
                        modbus_address=modbus_address,
                        register_type=register_type,
                        bit_offset=bit_offset
                    )
                    
                    self.tags.append(tag)
                    
                except Exception as e:
                    logging.warning(f"解析标签失败 {row.get('Name', 'Unknown')}: {e}")
            
            logging.info(f"成功加载 {len(self.tags)} 个标签")
            
        except Exception as e:
            logging.error(f"加载CSV文件失败: {e}")
            raise
    
    def get_tags_by_type(self, register_type: str) -> List[PLCTag]:
        """按寄存器类型获取标签"""
        return [tag for tag in self.tags if tag.register_type == register_type]
    
    def get_tag_by_name(self, name: str) -> Optional[PLCTag]:
        """按名称获取标签"""
        for tag in self.tags:
            if tag.name == name:
                return tag
        return None

class PLCDataReader:
    """PLC数据读取器"""

    def __init__(self, host: str = "192.168.0.1", port: int = 502):
        self.client = ModbusTCPClient(host, port)
        self.mapper = PLCTagMapper()

    def load_tags(self, csv_file: str):
        """加载标签配置"""
        self.mapper.load_tags_from_csv(csv_file)

    def connect(self) -> bool:
        """连接到PLC"""
        return self.client.connect()

    def disconnect(self):
        """断开连接"""
        self.client.disconnect()

    def _convert_data_type(self, raw_values: List[int], data_type: str, tag: PLCTag) -> Any:
        """转换数据类型"""
        if data_type == 'Bool':
            if tag.register_type in ['coil', 'discrete']:
                return raw_values[0] if raw_values else False
            else:
                # 从寄存器中提取位
                if raw_values:
                    byte_value = raw_values[0] & 0xFF
                    return bool(byte_value & (1 << tag.bit_offset))
                return False

        elif data_type == 'Word':
            return raw_values[0] if raw_values else 0

        elif data_type == 'DWord' or data_type == 'UDInt':
            if len(raw_values) >= 2:
                # 32位无符号整数，大端序
                return (raw_values[0] << 16) | raw_values[1]
            return 0

        elif data_type == 'DInt':
            if len(raw_values) >= 2:
                # 32位有符号整数
                value = (raw_values[0] << 16) | raw_values[1]
                return value if value < 2147483648 else value - 4294967296
            return 0

        elif data_type == 'Real':
            if len(raw_values) >= 2:
                # IEEE 754单精度浮点数
                int_value = (raw_values[0] << 16) | raw_values[1]
                return struct.unpack('>f', struct.pack('>I', int_value))[0]
            return 0.0

        elif data_type == 'Time':
            if len(raw_values) >= 2:
                # 时间类型，通常是毫秒数
                ms_value = (raw_values[0] << 16) | raw_values[1]
                return ms_value / 1000.0  # 转换为秒
            return 0.0

        else:
            # 默认返回原始值
            return raw_values[0] if raw_values else 0

    def read_tag(self, tag: PLCTag) -> Any:
        """读取单个标签"""
        try:
            if tag.register_type == 'coil':
                # 读取线圈
                values = self.client.read_coils(tag.modbus_address, 1)
                raw_values = [int(v) for v in values]

            elif tag.register_type == 'discrete':
                # 读取离散输入
                values = self.client.read_discrete_inputs(tag.modbus_address, 1)
                raw_values = [int(v) for v in values]

            elif tag.register_type == 'holding':
                # 确定需要读取的寄存器数量
                if tag.data_type in ['Real', 'DWord', 'UDInt', 'DInt', 'Time']:
                    count = 2  # 32位数据需要2个寄存器
                else:
                    count = 1  # 16位数据需要1个寄存器

                raw_values = self.client.read_holding_registers(tag.modbus_address, count)

            else:
                raise ValueError(f"不支持的寄存器类型: {tag.register_type}")

            # 转换数据类型
            value = self._convert_data_type(raw_values, tag.data_type, tag)
            return value

        except Exception as e:
            logging.error(f"读取标签 {tag.name} 失败: {e}")
            return None

    def read_all_tags(self) -> Dict[str, Any]:
        """读取所有标签"""
        results = {}

        for tag in self.mapper.tags:
            value = self.read_tag(tag)
            results[tag.name] = {
                'value': value,
                'logical_address': tag.logical_address,
                'data_type': tag.data_type,
                'modbus_address': tag.modbus_address,
                'comment': tag.comment,
                'timestamp': datetime.now()
            }

        return results

    def read_tags_by_type(self, register_type: str) -> Dict[str, Any]:
        """按寄存器类型读取标签"""
        results = {}
        tags = self.mapper.get_tags_by_type(register_type)

        for tag in tags:
            value = self.read_tag(tag)
            results[tag.name] = {
                'value': value,
                'logical_address': tag.logical_address,
                'data_type': tag.data_type,
                'modbus_address': tag.modbus_address,
                'comment': tag.comment,
                'timestamp': datetime.now()
            }

        return results

    def read_tags_by_names(self, tag_names: List[str]) -> Dict[str, Any]:
        """按名称读取指定标签"""
        results = {}

        for name in tag_names:
            tag = self.mapper.get_tag_by_name(name)
            if tag:
                value = self.read_tag(tag)
                results[name] = {
                    'value': value,
                    'logical_address': tag.logical_address,
                    'data_type': tag.data_type,
                    'modbus_address': tag.modbus_address,
                    'comment': tag.comment,
                    'timestamp': datetime.now()
                }
            else:
                logging.warning(f"未找到标签: {name}")

        return results

    def export_address_mapping(self, output_file: str = "address_mapping.json"):
        """导出地址映射表"""
        mapping = []

        for tag in self.mapper.tags:
            mapping.append({
                'name': tag.name,
                'logical_address': tag.logical_address,
                'data_type': tag.data_type,
                'modbus_address': tag.modbus_address,
                'register_type': tag.register_type,
                'bit_offset': tag.bit_offset,
                'comment': tag.comment
            })

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)

        logging.info(f"地址映射表已导出: {output_file}")

def main():
    """主函数 - 演示用法"""
    print("🏭 PLC Modbus TCP/IP数据读取器")
    print("=" * 50)

    # 创建读取器
    reader = PLCDataReader(host="192.168.0.1", port=502)

    try:
        # 加载标签配置
        print("📊 加载标签配置...")
        reader.load_tags("plc/PLCTags.csv")

        # 导出地址映射表
        print("📋 导出地址映射表...")
        reader.export_address_mapping("plc/address_mapping.json")

        # 连接PLC
        print("🔌 连接PLC...")
        if not reader.connect():
            print("❌ PLC连接失败")
            return

        print("✅ PLC连接成功")

        # 读取一些关键标签
        key_tags = [
            "横轴_脉冲", "横轴_方向", "竖轴_脉冲", "竖轴_方向",
            "横轴_LowHwLimitSwitch", "横轴_HighHwLimitSwitch",
            "Tag_4", "Tag_8"  # Word和Real类型示例
        ]

        print("\n📖 读取关键标签...")
        results = reader.read_tags_by_names(key_tags)

        for name, data in results.items():
            print(f"  {name:20} = {data['value']:10} ({data['logical_address']}) - {data['comment']}")

        # 读取所有输出线圈
        print("\n🔄 读取输出线圈状态...")
        coil_results = reader.read_tags_by_type('coil')

        active_coils = []
        for name, data in coil_results.items():
            if data['value']:
                active_coils.append(f"{name}({data['logical_address']})")

        if active_coils:
            print(f"  激活的线圈: {', '.join(active_coils)}")
        else:
            print("  没有激活的线圈")

        # 读取所有输入状态
        print("\n📥 读取输入状态...")
        input_results = reader.read_tags_by_type('discrete')

        active_inputs = []
        for name, data in input_results.items():
            if data['value']:
                active_inputs.append(f"{name}({data['logical_address']})")

        if active_inputs:
            print(f"  激活的输入: {', '.join(active_inputs)}")
        else:
            print("  没有激活的输入")

        print("\n✅ 数据读取完成")

    except Exception as e:
        print(f"❌ 运行出错: {e}")

    finally:
        reader.disconnect()

if __name__ == "__main__":
    main()
