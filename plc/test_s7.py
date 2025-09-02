#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
西门子S7协议测试脚本
测试S7连接和地址解析功能
"""

import sys
import os

# 尝试导入S7读取器
try:
    from s7_plc_reader import S7PLCReader
    HAS_S7_READER = True
except ImportError:
    HAS_S7_READER = False
    print("❌ 无法导入S7读取器")

def test_snap7_import():
    """测试snap7库导入"""
    print("🧪 测试snap7库导入")
    print("-" * 30)
    
    try:
        import snap7
        print("✅ snap7库导入成功")
        print(f"📋 snap7版本: {snap7.__version__}")
        
        # 测试创建客户端
        client = snap7.client.Client()
        print("✅ S7客户端创建成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ snap7库导入失败: {e}")
        print("请运行: python install_s7.py")
        return False
    except Exception as e:
        print(f"⚠️ snap7测试异常: {e}")
        return True

def test_address_parsing():
    """测试S7地址解析"""
    print("\n🧪 测试S7地址解析")
    print("-" * 30)
    
    if not HAS_S7_READER:
        print("❌ 无法测试地址解析")
        return False
    
    reader = S7PLCReader()
    
    # 测试用例
    test_cases = [
        # (S7地址, 期望结果描述)
        ("%Q0.0", "输出位 Q0.0"),
        ("%Q0.1", "输出位 Q0.1"),
        ("%I0.7", "输入位 I0.7"),
        ("%QB0", "输出字节 QB0"),
        ("%IW2", "输入字 IW2"),
        ("%QD4", "输出双字 QD4"),
        ("%M1.1", "标志位 M1.1"),
        ("%MB10", "标志字节 MB10"),
        ("%MW100", "标志字 MW100"),
        ("%MD200", "标志双字 MD200"),
        ("%DB1.DBX0.0", "数据块1位 DBX0.0"),
        ("%DB1.DBB0", "数据块1字节 DBB0"),
        ("%DB1.DBW0", "数据块1字 DBW0"),
        ("%DB1.DBD0", "数据块1双字 DBD0"),
    ]
    
    passed = 0
    failed = 0
    
    for s7_addr, description in test_cases:
        try:
            address, area, size, s7_type = reader.parse_s7_address(s7_addr)
            print(f"✅ {s7_addr:12} → {area}:{address:4} ({size}字节, {s7_type}) - {description}")
            passed += 1
        except Exception as e:
            print(f"❌ {s7_addr:12} → 解析失败: {e}")
            failed += 1
    
    print(f"\n地址解析结果: {passed} 通过, {failed} 失败")
    return failed == 0

def test_s7_connection():
    """测试S7连接"""
    print("\n🧪 测试S7连接")
    print("-" * 30)
    
    if not HAS_S7_READER:
        print("❌ 无法测试S7连接")
        return False
    
    # 测试不同的连接参数
    test_configs = [
        {"ip": "192.168.0.1", "rack": 0, "slot": 1, "desc": "默认配置 (S7-1200/1500)"},
        {"ip": "192.168.0.1", "rack": 0, "slot": 2, "desc": "S7-300/400配置"},
    ]
    
    for config in test_configs:
        print(f"\n🔌 测试连接: {config['desc']}")
        print(f"   IP: {config['ip']}, Rack: {config['rack']}, Slot: {config['slot']}")
        
        try:
            reader = S7PLCReader(
                ip=config['ip'],
                rack=config['rack'],
                slot=config['slot']
            )
            
            if reader.connect():
                print("✅ 连接成功")
                reader.disconnect()
                return True
            else:
                print("❌ 连接失败")
                
        except Exception as e:
            print(f"❌ 连接异常: {e}")
    
    print("\n⚠️ 所有连接测试失败")
    print("请检查:")
    print("  1. PLC IP地址是否正确")
    print("  2. PLC是否启用PUT/GET通信")
    print("  3. 机架号和插槽号是否正确")
    print("  4. 网络连接是否正常")
    
    return False

def test_csv_format():
    """测试CSV文件格式"""
    print("\n🧪 测试CSV文件格式")
    print("-" * 30)
    
    csv_file = "PLCTags.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV文件不存在: {csv_file}")
        return False
    
    try:
        import pandas as pd
        df = pd.read_csv(csv_file, encoding='utf-8')
        
        print(f"✅ CSV文件加载成功: {len(df)} 行")
        print(f"📋 列名: {list(df.columns)}")
        
        # 检查必要的列
        required_columns = ['Name', 'Logical Address', 'Data Type']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ 缺少必要的列: {missing_columns}")
            return False
        
        # 显示前几行数据
        print("\n📊 前5行数据:")
        for i, row in df.head(5).iterrows():
            name = row['Name']
            addr = row['Logical Address']
            dtype = row['Data Type']
            print(f"  {name:20} {addr:12} {dtype}")
        
        # 统计地址类型
        addr_types = {}
        for addr in df['Logical Address']:
            addr_clean = str(addr).strip('%')
            if addr_clean.startswith('Q'):
                addr_type = 'Q输出'
            elif addr_clean.startswith('I'):
                addr_type = 'I输入'
            elif addr_clean.startswith('M'):
                addr_type = 'M标志'
            elif addr_clean.startswith('DB'):
                addr_type = 'DB数据块'
            else:
                addr_type = '其他'
            
            addr_types[addr_type] = addr_types.get(addr_type, 0) + 1
        
        print(f"\n📈 地址类型统计:")
        for addr_type, count in addr_types.items():
            print(f"  {addr_type:10}: {count:3} 个")
        
        return True
        
    except Exception as e:
        print(f"❌ CSV文件测试失败: {e}")
        return False

def show_s7_help():
    """显示S7协议帮助信息"""
    print("\n" + "="*60)
    print("📚 西门子S7协议使用指南")
    print("="*60)
    
    print("\n🔧 PLC配置步骤:")
    print("1. 在TIA Portal或STEP 7中打开PLC项目")
    print("2. 进入PLC设备配置")
    print("3. 启用'PUT/GET通信'选项")
    print("4. 设置PLC的IP地址")
    print("5. 下载配置到PLC")
    
    print("\n🌐 网络配置:")
    print("- PLC IP: 192.168.0.1 (可修改)")
    print("- 子网掩码: 255.255.255.0")
    print("- 确保PC和PLC在同一网段")
    
    print("\n📍 机架和插槽配置:")
    print("- S7-1200/1500: Rack=0, Slot=1")
    print("- S7-300/400: Rack=0, Slot=2")
    print("- 具体值请查看硬件配置")
    
    print("\n📊 支持的地址格式:")
    print("- 数字量: %Q0.0, %I0.1 (位地址)")
    print("- 字节: %QB0, %IB1, %MB2")
    print("- 字: %QW0, %IW2, %MW100")
    print("- 双字: %QD0, %ID4, %MD200")
    print("- 数据块: %DB1.DBX0.0, %DB1.DBW0")
    
    print("\n🚨 常见问题:")
    print("- 连接超时: 检查IP地址和网络")
    print("- 访问被拒绝: 启用PUT/GET通信")
    print("- 地址错误: 检查机架号和插槽号")
    print("- 数据读取失败: 确认地址格式正确")

def main():
    """主函数"""
    print("🏭 西门子S7协议测试程序")
    print("="*50)
    
    # 运行所有测试
    tests = [
        ("snap7库导入", test_snap7_import),
        ("地址解析", test_address_parsing),
        ("CSV文件格式", test_csv_format),
        ("S7连接", test_s7_connection),
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            all_passed = False
    
    # 显示帮助信息
    show_s7_help()
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 所有测试通过!")
        print("\n💡 现在可以运行:")
        print("  python s7_plc_reader.py")
    else:
        print("⚠️ 部分测试失败")
        print("请根据上述提示检查配置")
        print("\n🔧 如果需要安装snap7:")
        print("  python install_s7.py")

if __name__ == "__main__":
    main()
    input("\n按回车键退出...")
