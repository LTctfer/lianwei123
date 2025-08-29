#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC Modbus TCP/IP数据读取器 (使用pymodbus库)
根据PLCTags.csv自动生成地址映射并读取PLC数据

依赖库安装:
pip install pymodbus pandas

地址映射规则:
- Q0.0 = Modbus地址0, Q0.1 = 1, Q10.1 = 81
- I区: 输入线圈，从地址10000开始
- M区: 标志位，从地址20000开始
- MW/MD: 保持寄存器，从地址40000开始

PLC IP: 192.168.0.1
"""

import struct
import time
import logging
import pandas as pd
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import re

# 导入pymodbus库
try:
    from pymodbus.client.sync import ModbusTcpClient
    from pymodbus.constants import Endian
    from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
    HAS_PYMODBUS = True
except ImportError:
    print("⚠️ 未安装pymodbus库，请运行: pip install pymodbus")
    HAS_PYMODBUS = False

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

class PyModbusClient:
    """基于pymodbus的Modbus TCP/IP客户端"""
    
    def __init__(self, host: str, port: int = 502, timeout: float = 5.0, unit_id: int = 1):
        if not HAS_PYMODBUS:
            raise ImportError("需要安装pymodbus库: pip install pymodbus")
            
        self.host = host
        self.port = port
        self.timeout = timeout
        self.unit_id = unit_id
        self.client = None
        self.connected = False
        
    def connect(self) -> bool:
        """连接到PLC设备"""
        try:
            self.client = ModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=self.timeout
            )
            
            # 尝试连接
            connection = self.client.connect()
            
            if connection:
                self.connected = True
                logging.info(f"成功连接到PLC: {self.host}:{self.port}")
                
                # 测试连接 - 读取一个寄存器
                try:
                    result = self.client.read_holding_registers(0, 1, unit=self.unit_id)
                    if result.isError():
                        logging.warning(f"连接测试警告: {result}")
                    else:
                        logging.info("连接测试成功")
                except Exception as e:
                    logging.warning(f"连接测试异常: {e}")
                
                return True
            else:
                logging.error("Modbus连接失败")
                self.connected = False
                return False
                
        except Exception as e:
            logging.error(f"连接PLC失败: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.client and self.connected:
            try:
                self.client.close()
                self.connected = False
                logging.info("已断开PLC连接")
            except Exception as e:
                logging.warning(f"断开连接时出现异常: {e}")
    
    def read_coils(self, address: int, count: int) -> List[bool]:
        """读取线圈 (功能码01)"""
        if not self.connected:
            raise Exception("未连接到PLC")
        
        try:
            result = self.client.read_coils(address, count, unit=self.unit_id)
            
            if result.isError():
                raise Exception(f"读取线圈失败: {result}")
            
            return result.bits[:count]
            
        except Exception as e:
            logging.error(f"读取线圈失败 (地址{address}, 数量{count}): {e}")
            raise
    
    def read_discrete_inputs(self, address: int, count: int) -> List[bool]:
        """读取离散输入 (功能码02)"""
        if not self.connected:
            raise Exception("未连接到PLC")
        
        try:
            result = self.client.read_discrete_inputs(address, count, unit=self.unit_id)
            
            if result.isError():
                raise Exception(f"读取离散输入失败: {result}")
            
            return result.bits[:count]
            
        except Exception as e:
            logging.error(f"读取离散输入失败 (地址{address}, 数量{count}): {e}")
            raise
    
    def read_holding_registers(self, address: int, count: int) -> List[int]:
        """读取保持寄存器 (功能码03)"""
        if not self.connected:
            raise Exception("未连接到PLC")
        
        try:
            result = self.client.read_holding_registers(address, count, unit=self.unit_id)
            
            if result.isError():
                raise Exception(f"读取保持寄存器失败: {result}")
            
            return result.registers
            
        except Exception as e:
            logging.error(f"读取保持寄存器失败 (地址{address}, 数量{count}): {e}")
            raise
    
    def read_input_registers(self, address: int, count: int) -> List[int]:
        """读取输入寄存器 (功能码04)"""
        if not self.connected:
            raise Exception("未连接到PLC")
        
        try:
            result = self.client.read_input_registers(address, count, unit=self.unit_id)
            
            if result.isError():
                raise Exception(f"读取输入寄存器失败: {result}")
            
            return result.registers
            
        except Exception as e:
            logging.error(f"读取输入寄存器失败 (地址{address}, 数量{count}): {e}")
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
                # 按照您的映射规则: Q0.0=0, Q0.1=1, Q10.1=81
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
    """PLC数据读取器 (使用pymodbus)"""

    def __init__(self, host: str = "192.168.0.1", port: int = 502):
        self.client = PyModbusClient(host, port)
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
                # 使用pymodbus的BinaryPayloadDecoder处理字节序
                decoder = BinaryPayloadDecoder.fromRegisters(
                    raw_values[:2],
                    byteorder=Endian.Big,
                    wordorder=Endian.Big
                )
                return decoder.decode_32bit_uint()
            return 0

        elif data_type == 'DInt':
            if len(raw_values) >= 2:
                decoder = BinaryPayloadDecoder.fromRegisters(
                    raw_values[:2],
                    byteorder=Endian.Big,
                    wordorder=Endian.Big
                )
                return decoder.decode_32bit_int()
            return 0

        elif data_type == 'Real':
            if len(raw_values) >= 2:
                decoder = BinaryPayloadDecoder.fromRegisters(
                    raw_values[:2],
                    byteorder=Endian.Big,
                    wordorder=Endian.Big
                )
                return decoder.decode_32bit_float()
            return 0.0

        elif data_type == 'Time':
            if len(raw_values) >= 2:
                # 时间类型，通常是毫秒数
                decoder = BinaryPayloadDecoder.fromRegisters(
                    raw_values[:2],
                    byteorder=Endian.Big,
                    wordorder=Endian.Big
                )
                ms_value = decoder.decode_32bit_uint()
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

            elif tag.register_type == 'input':
                # 读取输入寄存器
                if tag.data_type in ['Real', 'DWord', 'UDInt', 'DInt', 'Time']:
                    count = 2
                else:
                    count = 1

                raw_values = self.client.read_input_registers(tag.modbus_address, count)

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

    def test_connection(self) -> bool:
        """测试连接"""
        print("🔧 测试PLC连接...")

        try:
            if not self.connect():
                print("❌ PLC连接失败")
                return False

            print("✅ PLC连接成功")

            # 尝试读取一些标签
            if self.mapper.tags:
                test_tag = self.mapper.tags[0]
                print(f"🧪 测试读取标签: {test_tag.name}")

                value = self.read_tag(test_tag)
                if value is not None:
                    print(f"✅ 读取成功: {test_tag.name} = {value}")
                else:
                    print(f"⚠️ 读取失败: {test_tag.name}")

            return True

        except Exception as e:
            print(f"❌ 连接测试失败: {e}")
            return False
        finally:
            self.disconnect()

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
    print("🏭 PLC Modbus TCP/IP数据读取器 (pymodbus版本)")
    print("=" * 60)

    if not HAS_PYMODBUS:
        print("❌ 缺少pymodbus库")
        print("请运行: pip install pymodbus")
        return

    # 创建读取器
    reader = PLCDataReader(host="192.168.0.1", port=502)

    try:
        # 加载标签配置
        print("📊 加载标签配置...")
        reader.load_tags("plc/PLCTags.csv")

        # 导出地址映射表
        print("📋 导出地址映射表...")
        reader.export_address_mapping("plc/address_mapping_v2.json")

        # 测试连接
        if reader.test_connection():
            print("\n🎉 系统测试成功！")
            print("\n💡 使用方法:")
            print("  python plc_modbus_reader_v2.py")
            print("  python plc_monitor_v2.py --test")
        else:
            print("\n⚠️ 连接测试失败，请检查:")
            print("  1. PLC设备IP地址是否正确")
            print("  2. PLC是否启用了Modbus TCP服务")
            print("  3. 网络连接是否正常")
            print("  4. 防火墙设置")

    except Exception as e:
        print(f"❌ 运行出错: {e}")

if __name__ == "__main__":
    main()
