#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
西门子S7协议PLC数据读取器
使用snap7库直接通过S7协议读取西门子PLC数据

支持的PLC型号:
- S7-200/300/400/1200/1500系列
- LOGO! 0BA7/0BA8

安装依赖:
pip install python-snap7

PLC配置要求:
- 启用PUT/GET通信
- 设置正确的IP地址
- 确保防火墙允许S7通信
"""

import pandas as pd
import struct
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# 尝试导入snap7库
try:
    import snap7
    from snap7.util import *
    HAS_SNAP7 = True
    print("✅ 使用snap7库 (西门子S7协议)")
except ImportError:
    HAS_SNAP7 = False
    print("❌ 未安装snap7库")
    print("请安装: pip install python-snap7")
    print("并下载snap7库文件到系统路径")

class S7PLCReader:
    """西门子S7协议PLC读取器"""
    
    def __init__(self, ip: str = "192.168.0.1", rack: int = 0, slot: int = 1):
        """
        初始化S7连接
        
        Args:
            ip: PLC IP地址
            rack: 机架号 (通常为0)
            slot: 插槽号 (CPU通常为1或2)
        """
        if not HAS_SNAP7:
            raise ImportError("需要安装snap7库: pip install python-snap7")
            
        self.ip = ip
        self.rack = rack
        self.slot = slot
        self.client = None
        self.connected = False
        
    def connect(self) -> bool:
        """连接到S7 PLC"""
        try:
            self.client = snap7.client.Client()
            self.client.connect(self.ip, self.rack, self.slot)
            self.connected = True
            
            # 获取PLC信息
            cpu_info = self.client.get_cpu_info()
            print(f"✅ S7连接成功: {self.ip}")
            print(f"   PLC型号: {cpu_info.ModuleTypeName.decode('ascii')}")
            print(f"   序列号: {cpu_info.SerialNumber.decode('ascii')}")
            print(f"   固件版本: V{cpu_info.Major}.{cpu_info.Minor}")
            
            return True
            
        except Exception as e:
            print(f"❌ S7连接失败: {e}")
            print("请检查:")
            print("  1. PLC IP地址是否正确")
            print("  2. PLC是否启用PUT/GET通信")
            print("  3. 机架号和插槽号是否正确")
            print("  4. 网络连接是否正常")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开S7连接"""
        if self.client and self.connected:
            try:
                self.client.disconnect()
                self.connected = False
                print("🔌 S7连接已断开")
            except:
                pass
    
    def parse_s7_address(self, logical_address: str) -> Tuple[int, str, int, str]:
        """
        解析S7地址格式
        
        支持格式:
        - %Q0.0, %I0.1 (位地址)
        - %QB0, %IB1 (字节地址)  
        - %QW0, %IW2 (字地址)
        - %QD0, %ID4 (双字地址)
        - %MW100, %MD200 (标志区)
        - %DB1.DBX0.0, %DB1.DBB0, %DB1.DBW0, %DB1.DBD0 (数据块)
        
        Returns:
            (地址, 区域类型, 数据大小, 数据类型)
        """
        address = logical_address.strip('%')
        
        # 数据块地址 DB1.DBX0.0, DB1.DBW0等
        if address.startswith('DB'):
            match = re.match(r'DB(\d+)\.DB([XBWD])(\d+)(?:\.(\d+))?', address)
            if match:
                db_num = int(match.group(1))
                data_type = match.group(2)
                offset = int(match.group(3))
                bit_offset = int(match.group(4)) if match.group(4) else 0
                
                if data_type == 'X':  # 位
                    return offset, f'DB{db_num}', 1, 'BOOL'
                elif data_type == 'B':  # 字节
                    return offset, f'DB{db_num}', 1, 'BYTE'
                elif data_type == 'W':  # 字
                    return offset, f'DB{db_num}', 2, 'WORD'
                elif data_type == 'D':  # 双字
                    return offset, f'DB{db_num}', 4, 'DWORD'
        
        # 输入输出地址 Q0.0, I0.1, QB0, IW2等
        elif address[0] in ['Q', 'I']:
            area_type = 'Q' if address[0] == 'Q' else 'I'
            
            if len(address) > 1 and address[1] in ['B', 'W', 'D']:
                # 字节/字/双字格式 QB0, QW0, QD0
                data_type = address[1]
                offset = int(address[2:])
                
                if data_type == 'B':
                    return offset, area_type, 1, 'BYTE'
                elif data_type == 'W':
                    return offset, area_type, 2, 'WORD'
                elif data_type == 'D':
                    return offset, area_type, 4, 'DWORD'
            else:
                # 位格式 Q0.0, I0.1
                match = re.match(r'([QI])(\d+)\.(\d+)', address)
                if match:
                    byte_addr = int(match.group(2))
                    bit_addr = int(match.group(3))
                    return byte_addr, area_type, 1, 'BOOL'
        
        # 标志区地址 M0.0, MB0, MW100, MD200
        elif address.startswith('M'):
            if len(address) > 1 and address[1] in ['B', 'W', 'D']:
                # 字节/字/双字格式
                data_type = address[1]
                offset = int(address[2:])
                
                if data_type == 'B':
                    return offset, 'M', 1, 'BYTE'
                elif data_type == 'W':
                    return offset, 'M', 2, 'WORD'
                elif data_type == 'D':
                    return offset, 'M', 4, 'DWORD'
            else:
                # 位格式 M0.0
                match = re.match(r'M(\d+)\.(\d+)', address)
                if match:
                    byte_addr = int(match.group(1))
                    bit_addr = int(match.group(2))
                    return byte_addr, 'M', 1, 'BOOL'
        
        raise ValueError(f"不支持的S7地址格式: {logical_address}")
    
    def read_area(self, area: str, db_number: int, start: int, size: int) -> bytearray:
        """
        读取PLC存储区域
        
        Args:
            area: 存储区域 ('Q', 'I', 'M', 'DB')
            db_number: 数据块号 (仅DB区域需要)
            start: 起始地址
            size: 读取字节数
        """
        if not self.connected:
            raise Exception("未连接到PLC")
        
        try:
            if area == 'Q':
                # 输出区
                return self.client.read_area(snap7.types.Areas.PA, 0, start, size)
            elif area == 'I':
                # 输入区
                return self.client.read_area(snap7.types.Areas.PE, 0, start, size)
            elif area == 'M':
                # 标志区
                return self.client.read_area(snap7.types.Areas.MK, 0, start, size)
            elif area.startswith('DB'):
                # 数据块区
                db_num = int(area[2:]) if len(area) > 2 else db_number
                return self.client.read_area(snap7.types.Areas.DB, db_num, start, size)
            else:
                raise ValueError(f"不支持的存储区域: {area}")
                
        except Exception as e:
            raise Exception(f"读取存储区域失败 {area}: {e}")
    
    def convert_s7_data(self, data: bytearray, offset: int, data_type: str, s7_type: str) -> Any:
        """
        转换S7数据类型
        
        Args:
            data: 原始数据
            offset: 数据偏移
            data_type: PLC数据类型 (Bool, Word, DWord等)
            s7_type: S7内部类型 (BOOL, BYTE, WORD, DWORD)
        """
        try:
            if s7_type == 'BOOL' or data_type == 'Bool':
                # 布尔值 - 从字节中提取位
                if offset < len(data):
                    byte_val = data[offset]
                    # 如果是位地址，需要额外的位偏移信息
                    return bool(byte_val & 0x01)  # 简化处理，取最低位
                return False
                
            elif s7_type == 'BYTE' or data_type == 'Byte':
                # 8位无符号整数
                if offset < len(data):
                    return data[offset]
                return 0
                
            elif s7_type == 'WORD' or data_type == 'Word':
                # 16位无符号整数 (大端序)
                if offset + 1 < len(data):
                    return struct.unpack('>H', data[offset:offset+2])[0]
                return 0
                
            elif s7_type == 'DWORD' or data_type in ['DWord', 'UDInt']:
                # 32位无符号整数 (大端序)
                if offset + 3 < len(data):
                    return struct.unpack('>I', data[offset:offset+4])[0]
                return 0
                
            elif data_type == 'DInt':
                # 32位有符号整数 (大端序)
                if offset + 3 < len(data):
                    return struct.unpack('>i', data[offset:offset+4])[0]
                return 0
                
            elif data_type == 'Real':
                # 32位浮点数 (大端序)
                if offset + 3 < len(data):
                    return struct.unpack('>f', data[offset:offset+4])[0]
                return 0.0
                
            elif data_type == 'Time':
                # 时间类型 (32位毫秒数)
                if offset + 3 < len(data):
                    ms_value = struct.unpack('>I', data[offset:offset+4])[0]
                    return ms_value / 1000.0  # 转换为秒
                return 0.0
                
            else:
                # 默认按字节处理
                if offset < len(data):
                    return data[offset]
                return 0
                
        except Exception as e:
            print(f"数据转换失败 {data_type}: {e}")
            return None
    
    def read_tag(self, name: str, logical_address: str, data_type: str) -> Optional[Dict]:
        """读取单个S7标签"""
        try:
            # 解析S7地址
            address, area, size, s7_type = self.parse_s7_address(logical_address)
            
            # 读取数据
            db_number = 0
            if area.startswith('DB'):
                db_number = int(area[2:])
                area = 'DB'
            
            raw_data = self.read_area(area, db_number, address, size)
            
            # 转换数据类型
            value = self.convert_s7_data(raw_data, 0, data_type, s7_type)
            
            return {
                'name': name,
                'logical_address': logical_address,
                's7_address': address,
                'area': area,
                'data_type': data_type,
                's7_type': s7_type,
                'raw_data': raw_data.hex() if raw_data else '',
                'value': value,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"读取S7标签失败 {name}: {e}")
            return None
    
    def read_csv_tags(self, csv_file: str = "PLCTags.csv") -> List[Dict]:
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
            
            print("🔄 开始读取S7标签数据...")
            
            for index, row in df.iterrows():
                name = row['Name']
                logical_address = row['Logical Address']
                data_type = row['Data Type']
                
                # 读取标签
                result = self.read_tag(name, logical_address, data_type)
                
                if result and result['value'] is not None:
                    results.append(result)
                    success_count += 1
                    
                    # 显示读取结果
                    value = result['value']
                    s7_addr = result['s7_address']
                    area = result['area']
                    
                    if isinstance(value, bool):
                        status = "ON" if value else "OFF"
                        print(f"  ✅ {name:25} ({logical_address:12} → {area}:{s7_addr:4}): {status}")
                    elif isinstance(value, float):
                        print(f"  ✅ {name:25} ({logical_address:12} → {area}:{s7_addr:4}): {value:.3f}")
                    else:
                        print(f"  ✅ {name:25} ({logical_address:12} → {area}:{s7_addr:4}): {value}")
                else:
                    print(f"  ❌ {name:25} ({logical_address:12}): 读取失败")
            
            print(f"\n📈 S7读取完成: {success_count}/{len(df)} 个标签成功")
            
            return results
            
        except Exception as e:
            print(f"❌ 读取CSV失败: {e}")
            return []
        finally:
            self.disconnect()

def main():
    """主函数"""
    print("🏭 西门子S7协议PLC数据读取器")
    print("=" * 50)
    print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not HAS_SNAP7:
        print("❌ 缺少snap7库，无法使用S7协议")
        print("请安装: pip install python-snap7")
        print("并确保snap7动态库在系统路径中")
        return
    
    # 创建S7读取器
    reader = S7PLCReader(ip="192.168.0.1", rack=0, slot=1)
    
    # 读取所有标签
    results = reader.read_csv_tags("PLCTags.csv")
    
    if results:
        print("\n📋 S7读取结果汇总:")
        print("-" * 80)
        
        # 按数据类型分组显示
        bool_tags = [r for r in results if isinstance(r['value'], bool)]
        number_tags = [r for r in results if isinstance(r['value'], (int, float)) and not isinstance(r['value'], bool)]
        
        if bool_tags:
            print(f"\n🔘 布尔类型标签 ({len(bool_tags)} 个):")
            active_tags = [r for r in bool_tags if r['value']]
            if active_tags:
                for result in active_tags:
                    print(f"  🟢 {result['name']} = ON ({result['area']})")
            else:
                print("  🔴 所有布尔标签都为OFF")
        
        if number_tags:
            print(f"\n📊 数值类型标签 ({len(number_tags)} 个):")
            for result in number_tags[:10]:  # 只显示前10个
                value = result['value']
                area = result['area']
                if isinstance(value, float):
                    print(f"  📈 {result['name']:25} = {value:10.3f} ({area})")
                else:
                    print(f"  📈 {result['name']:25} = {value:10} ({area})")
            
            if len(number_tags) > 10:
                print(f"  ... 还有 {len(number_tags) - 10} 个数值标签")
        
        # 保存结果到文件
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"s7_data_{timestamp}.csv"
            
            # 转换为DataFrame并保存
            df_results = pd.DataFrame([
                {
                    'name': r['name'],
                    'logical_address': r['logical_address'],
                    's7_address': r['s7_address'],
                    'area': r['area'],
                    'data_type': r['data_type'],
                    's7_type': r['s7_type'],
                    'value': r['value'],
                    'timestamp': r['timestamp']
                }
                for r in results
            ])
            
            df_results.to_csv(output_file, index=False, encoding='utf-8')
            print(f"\n💾 S7读取结果已保存: {output_file}")
            
        except Exception as e:
            print(f"⚠️ 保存结果失败: {e}")
    
    else:
        print("\n❌ 没有成功读取到任何S7数据")
        print("请检查:")
        print("  1. PLC IP地址是否正确 (当前: 192.168.0.1)")
        print("  2. PLC是否启用PUT/GET通信")
        print("  3. 机架号和插槽号是否正确 (当前: Rack=0, Slot=1)")
        print("  4. 网络连接是否正常")
        print("  5. CSV文件中的S7地址格式是否正确")

if __name__ == "__main__":
    main()
