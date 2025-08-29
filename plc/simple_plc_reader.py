#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单PLC数据读取器
直接根据IP地址和CSV中的寄存器地址读取PLC数据

映射规则: Q0.0=0, Q0.1=1, Q10.1=81
PLC IP: 192.168.0.1
"""

import pandas as pd
import struct
import re
from datetime import datetime

# 尝试导入pymodbus，如果没有则使用原生socket
try:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.utilities import BinaryPayloadDecoder
    from pymodbus.constants import Endian
    USE_PYMODBUS = True
    print("✅ 使用pymodbus库")
except ImportError:
    import socket
    USE_PYMODBUS = False
    print("⚠️ 使用原生socket (建议安装pymodbus: pip install pymodbus)")

class SimplePLCReader:
    """简单PLC读取器"""
    
    def __init__(self, ip: str = "192.168.0.1", port: int = 502):
        self.ip = ip
        self.port = port
        self.client = None
        self.connected = False
        
    def connect(self):
        """连接PLC"""
        try:
            if USE_PYMODBUS:
                self.client = ModbusTcpClient(host=self.ip, port=self.port, timeout=5)
                self.connected = self.client.connect()
            else:
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.settimeout(5)
                self.client.connect((self.ip, self.port))
                self.connected = True
                
            if self.connected:
                print(f"✅ 连接成功: {self.ip}:{self.port}")
            else:
                print(f"❌ 连接失败: {self.ip}:{self.port}")
                
            return self.connected
        except Exception as e:
            print(f"❌ 连接异常: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.client:
            try:
                if USE_PYMODBUS:
                    self.client.close()
                else:
                    self.client.close()
                self.connected = False
                print("🔌 连接已断开")
            except:
                pass
    
    def parse_address(self, logical_address: str):
        """
        解析PLC地址到Modbus地址
        Q0.0 = 0, Q0.1 = 1, Q10.1 = 81
        """
        address = logical_address.strip('%')
        
        if address.startswith('Q'):
            # 输出线圈: Q0.0, Q10.1等
            match = re.match(r'Q(\d+)\.(\d+)', address)
            if match:
                byte_addr = int(match.group(1))
                bit_addr = int(match.group(2))
                modbus_addr = byte_addr * 8 + bit_addr
                return modbus_addr, 'coil'
                
        elif address.startswith('I'):
            # 输入线圈: I0.0, I0.7等
            match = re.match(r'I(\d+)\.(\d+)', address)
            if match:
                byte_addr = int(match.group(1))
                bit_addr = int(match.group(2))
                modbus_addr = 10000 + byte_addr * 8 + bit_addr
                return modbus_addr, 'discrete'
                
        elif address.startswith('MW'):
            # 标志字: MW100等
            match = re.match(r'MW(\d+)', address)
            if match:
                word_addr = int(match.group(1))
                modbus_addr = 40000 + word_addr
                return modbus_addr, 'holding'
                
        elif address.startswith('MD'):
            # 标志双字: MD100等
            match = re.match(r'MD(\d+)', address)
            if match:
                dword_addr = int(match.group(1))
                modbus_addr = 40000 + dword_addr // 2
                return modbus_addr, 'holding'
                
        elif address.startswith('M'):
            # 标志位: M1.1等
            match = re.match(r'M(\d+)\.(\d+)', address)
            if match:
                byte_addr = int(match.group(1))
                bit_addr = int(match.group(2))
                modbus_addr = 20000 + byte_addr * 8 + bit_addr
                return modbus_addr, 'coil'
        
        raise ValueError(f"不支持的地址格式: {logical_address}")
    
    def read_coil(self, address: int):
        """读取线圈"""
        if not self.connected:
            return None
            
        try:
            if USE_PYMODBUS:
                result = self.client.read_coils(address, 1)
                if not result.isError():
                    return result.bits[0]
            else:
                # 使用原生socket实现
                # 这里简化处理，实际项目建议使用pymodbus
                pass
            return None
        except Exception as e:
            print(f"读取线圈失败 {address}: {e}")
            return None
    
    def read_discrete(self, address: int):
        """读取离散输入"""
        if not self.connected:
            return None
            
        try:
            if USE_PYMODBUS:
                result = self.client.read_discrete_inputs(address, 1)
                if not result.isError():
                    return result.bits[0]
            return None
        except Exception as e:
            print(f"读取离散输入失败 {address}: {e}")
            return None
    
    def read_holding_register(self, address: int, count: int = 1):
        """读取保持寄存器"""
        if not self.connected:
            return None
            
        try:
            if USE_PYMODBUS:
                result = self.client.read_holding_registers(address, count)
                if not result.isError():
                    return result.registers
            return None
        except Exception as e:
            print(f"读取保持寄存器失败 {address}: {e}")
            return None
    
    def convert_data_type(self, raw_data, data_type: str):
        """转换数据类型"""
        if not raw_data:
            return None
            
        try:
            if data_type == 'Bool':
                return bool(raw_data[0]) if isinstance(raw_data, list) else bool(raw_data)
            elif data_type == 'Word':
                return raw_data[0] if isinstance(raw_data, list) else raw_data
            elif data_type in ['DWord', 'UDInt']:
                if len(raw_data) >= 2:
                    return (raw_data[0] << 16) | raw_data[1]
                return raw_data[0]
            elif data_type == 'DInt':
                if len(raw_data) >= 2:
                    value = (raw_data[0] << 16) | raw_data[1]
                    return value if value < 2147483648 else value - 4294967296
                return raw_data[0]
            elif data_type == 'Real':
                if len(raw_data) >= 2 and USE_PYMODBUS:
                    decoder = BinaryPayloadDecoder.fromRegisters(
                        raw_data[:2], byteorder=Endian.Big, wordorder=Endian.Big
                    )
                    return decoder.decode_32bit_float()
                return 0.0
            else:
                return raw_data[0] if isinstance(raw_data, list) else raw_data
        except Exception as e:
            print(f"数据类型转换失败 {data_type}: {e}")
            return None
    
    def read_tag(self, name: str, logical_address: str, data_type: str):
        """读取单个标签"""
        try:
            # 解析地址
            modbus_addr, register_type = self.parse_address(logical_address)
            
            # 读取数据
            raw_data = None
            if register_type == 'coil':
                raw_data = self.read_coil(modbus_addr)
            elif register_type == 'discrete':
                raw_data = self.read_discrete(modbus_addr)
            elif register_type == 'holding':
                count = 2 if data_type in ['Real', 'DWord', 'UDInt', 'DInt'] else 1
                raw_data = self.read_holding_register(modbus_addr, count)
            
            # 转换数据类型
            if raw_data is not None:
                value = self.convert_data_type(raw_data, data_type)
                return {
                    'name': name,
                    'logical_address': logical_address,
                    'modbus_address': modbus_addr,
                    'data_type': data_type,
                    'raw_data': raw_data,
                    'value': value,
                    'timestamp': datetime.now()
                }
            
        except Exception as e:
            print(f"读取标签失败 {name}: {e}")
        
        return None
    
    def read_csv_tags(self, csv_file: str = "plc/PLCTags.csv"):
        """读取CSV中的所有标签"""
        try:
            # 读取CSV文件
            df = pd.read_csv(csv_file, encoding='utf-8')
            print(f"📊 加载CSV文件: {len(df)} 个标签")
            
            # 连接PLC
            if not self.connect():
                return []
            
            results = []
            success_count = 0
            
            print("🔄 开始读取标签数据...")
            
            for index, row in df.iterrows():
                name = row['Name']
                logical_address = row['Logical Address']
                data_type = row['Data Type']
                
                # 读取标签
                result = self.read_tag(name, logical_address, data_type)
                
                if result:
                    results.append(result)
                    success_count += 1
                    
                    # 显示读取结果
                    value = result['value']
                    modbus_addr = result['modbus_address']
                    
                    if isinstance(value, bool):
                        status = "ON" if value else "OFF"
                        print(f"  ✅ {name:25} ({logical_address:8} → {modbus_addr:6}): {status}")
                    elif isinstance(value, float):
                        print(f"  ✅ {name:25} ({logical_address:8} → {modbus_addr:6}): {value:.3f}")
                    else:
                        print(f"  ✅ {name:25} ({logical_address:8} → {modbus_addr:6}): {value}")
                else:
                    print(f"  ❌ {name:25} ({logical_address:8}): 读取失败")
            
            print(f"\n📈 读取完成: {success_count}/{len(df)} 个标签成功")
            
            return results
            
        except Exception as e:
            print(f"❌ 读取CSV失败: {e}")
            return []
        finally:
            self.disconnect()

def main():
    """主函数"""
    print("🏭 简单PLC数据读取器")
    print("=" * 50)
    print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建读取器
    reader = SimplePLCReader(ip="192.168.0.1", port=502)
    
    # 读取所有标签
    results = reader.read_csv_tags("plc/PLCTags.csv")
    
    if results:
        print("\n📋 读取结果汇总:")
        print("-" * 80)
        
        # 按数据类型分组显示
        bool_tags = [r for r in results if isinstance(r['value'], bool)]
        number_tags = [r for r in results if isinstance(r['value'], (int, float)) and not isinstance(r['value'], bool)]
        
        if bool_tags:
            print(f"\n🔘 布尔类型标签 ({len(bool_tags)} 个):")
            active_tags = [r for r in bool_tags if r['value']]
            if active_tags:
                for result in active_tags:
                    print(f"  🟢 {result['name']} = ON")
            else:
                print("  🔴 所有布尔标签都为OFF")
        
        if number_tags:
            print(f"\n📊 数值类型标签 ({len(number_tags)} 个):")
            for result in number_tags[:10]:  # 只显示前10个
                value = result['value']
                if isinstance(value, float):
                    print(f"  📈 {result['name']:25} = {value:10.3f}")
                else:
                    print(f"  📈 {result['name']:25} = {value:10}")
            
            if len(number_tags) > 10:
                print(f"  ... 还有 {len(number_tags) - 10} 个数值标签")
        
        # 保存结果到文件
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"plc/plc_data_{timestamp}.csv"
            
            # 转换为DataFrame并保存
            df_results = pd.DataFrame([
                {
                    'name': r['name'],
                    'logical_address': r['logical_address'],
                    'modbus_address': r['modbus_address'],
                    'data_type': r['data_type'],
                    'value': r['value'],
                    'timestamp': r['timestamp']
                }
                for r in results
            ])
            
            df_results.to_csv(output_file, index=False, encoding='utf-8')
            print(f"\n💾 结果已保存: {output_file}")
            
        except Exception as e:
            print(f"⚠️ 保存结果失败: {e}")
    
    else:
        print("\n❌ 没有成功读取到任何数据")
        print("请检查:")
        print("  1. PLC IP地址是否正确 (当前: 192.168.0.1)")
        print("  2. PLC是否启用Modbus TCP服务")
        print("  3. 网络连接是否正常")
        print("  4. CSV文件格式是否正确")

if __name__ == "__main__":
    main()
