import snap7
from snap7.util import *
import struct

class SiemensPLC:
    def __init__(self, ip, rack=0, slot=1):
        """
        初始化PLC连接
        :param ip: PLC的IP地址
        :param rack: 机架号，默认0
        :param slot: 插槽号，默认1
        """
        self.ip = ip
        self.rack = rack
        self.slot = slot
        self.client = snap7.client.Client()
        
    def connect(self):
        """连接到PLC"""
        try:
            self.client.connect(self.ip, self.rack, self.slot)
            if self.client.get_connected():
                print(f"成功连接到PLC {self.ip}")
                return True
            else:
                print("连接失败")
                return False
        except Exception as e:
            print(f"连接错误: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        try:
            self.client.disconnect()
            print("已断开连接")
        except Exception as e:
            print(f"断开连接错误: {e}")
    
    def read_memory(self, area, db_number, start, size):
        """
        读取PLC内存
        :param area: 存储区域 (snap7.types.Areas)
        :param db_number: DB块号 (对于DB区域)
        :param start: 起始地址
        :param size: 读取字节数
        :return: 读取的数据
        """
        try:
            data = self.client.read_area(area, db_number, start, size)
            return data
        except Exception as e:
            print(f"读取错误: {e}")
            return None
    
    def write_memory(self, area, db_number, start, data):
        """
        写入PLC内存
        :param area: 存储区域
        :param db_number: DB块号
        :param start: 起始地址
        :param data: 要写入的数据
        """
        try:
            self.client.write_area(area, db_number, start, data)
            print("写入成功")
        except Exception as e:
            print(f"写入错误: {e}")
    
    def read_db(self, db_number, start, size):
        """读取DB块"""
        return self.read_memory(snap7.types.Areas.DB, db_number, start, size)
    
    def write_db(self, db_number, start, data):
        """写入DB块"""
        self.write_memory(snap7.types.Areas.DB, db_number, start, data)
    
    def read_mb(self, start, size):
        """读取M区（位存储区）"""
        return self.read_memory(snap7.types.Areas.MK, 0, start, size)
    
    def write_mb(self, start, data):
        """写入M区"""
        self.write_memory(snap7.types.Areas.MK, 0, start, data)
    
    def read_ib(self, start, size):
        """读取I区（输入）"""
        return self.read_memory(snap7.types.Areas.PE, 0, start, size)
    
    def read_qb(self, start, size):
        """读取Q区（输出）"""
        return self.read_memory(snap7.types.Areas.PA, 0, start, size)
    
    def write_qb(self, start, data):
        """写入Q区"""
        self.write_memory(snap7.types.Areas.PA, 0, start, data)

# 使用示例
def main():
    # PLC的IP地址
    plc_ip = "192.168.0.1"  # 请修改为你的PLC实际IP地址
    
    # 创建PLC对象
    plc = SiemensPLC(plc_ip)
    
    # 连接PLC
    if not plc.connect():
        return
    
    try:
        # 示例1: 读取DB100的前4个字节（通常用于读取整数）
        data = plc.read_db(100, 0, 4)
        if data:
            # 将字节数据转换为整数
            value = struct.unpack('>I', data)[0]  # 大端序
            print(f"DB100.0-3的值: {value}")
        
        # 示例2: 写入数据到DB100
        # 写入一个整数12345到DB100的前4个字节
        value_to_write = 12345
        data_to_write = struct.pack('>I', value_to_write)
        plc.write_db(100, 0, data_to_write)
        
        # 示例3: 读取M区（位存储区）的前10个字节
        m_data = plc.read_mb(0, 10)
        if m_data:
            print(f"M区数据: {m_data.hex()}")
        
        # 示例4: 读取输入I区
        i_data = plc.read_ib(0, 4)
        if i_data:
            print(f"I区数据: {i_data.hex()}")
        
        # 示例5: 读取输出Q区
        q_data = plc.read_qb(0, 4)
        if q_data:
            print(f"Q区数据: {q_data.hex()}")
            
    except Exception as e:
        print(f"操作错误: {e}")
    finally:
        # 断开连接
        plc.disconnect()

if __name__ == "__main__":
    main()
