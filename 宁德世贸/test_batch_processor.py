#!/usr/bin/env python3
"""
测试宁德世贸批量数据处理器
"""

import os
import sys
from pathlib import Path

# 添加当前目录到系统路径
sys.path.append(str(Path(__file__).parent))

from ningde_data_processor import NingdeDataProcessor

def test_scan_monthly_files():
    """测试月度文件扫描功能"""
    print("🔍 测试文件扫描功能...")
    
    processor = NingdeDataProcessor()
    base_dir = "宁德世贸"
    
    # 扫描月度文件
    monthly_files = processor.scan_monthly_files(base_dir)
    
    if monthly_files:
        print(f"✅ 成功扫描到 {len(monthly_files)} 个月的数据:")
        for month_name, files in monthly_files.items():
            print(f"   {month_name}: {len(files)} 个文件")
            if files:
                print(f"     首个文件: {Path(files[0]).name}")
                print(f"     末个文件: {Path(files[-1]).name}")
    else:
        print("❌ 未扫描到任何月度文件")
    
    return monthly_files

def test_single_file_processing():
    """测试单文件处理功能"""
    print("\n📄 测试单文件处理功能...")
    
    processor = NingdeDataProcessor()
    test_file = "宁德世贸/20250101.csv"
    
    if os.path.exists(test_file):
        print(f"📁 测试文件: {test_file}")
        
        # 加载数据测试
        df = processor.load_data(test_file)
        if not df.empty:
            print(f"✅ 文件加载成功，数据行数: {len(df)}")
            print(f"📊 可用列数: {len(df.columns)}")
            
            # 测试处理几个字段
            test_fields = ['furnace_temp_avg', 'dust_emission']
            for field_name in test_fields:
                if field_name in processor.field_mapping:
                    field_config = processor.field_mapping[field_name]
                    try:
                        results = processor.process_field(df, field_name, field_config)
                        print(f"✅ 字段 {field_name} 处理成功，结果数: {len(results)}")
                    except Exception as e:
                        print(f"❌ 字段 {field_name} 处理失败: {e}")
        else:
            print(f"❌ 文件加载失败")
    else:
        print(f"⚠️ 测试文件不存在: {test_file}")

def test_data_cleaning():
    """测试数据清洗功能"""
    print("\n🧹 测试数据清洗功能...")
    
    import pandas as pd
    import numpy as np
    
    processor = NingdeDataProcessor()
    
    # 创建测试数据
    test_data = pd.Series([
        0, 1, 2, 3, 4, 5, 100, 1000, -1, -5,  # 包含0值、负值、异常值
        np.nan, 'invalid', '--', '10.5', '20'
    ])
    
    print(f"原始数据: {test_data.tolist()}")
    
    # 测试正常清洗（不允许负值）
    cleaned = processor._clean_outliers_for_calculation(test_data, "测试数据", allow_negative=False)
    print(f"清洗后数据（不允许负值）: {cleaned.dropna().tolist()}")
    
    # 测试允许负值的清洗
    cleaned_with_negative = processor._clean_outliers_for_calculation(test_data, "测试数据（允许负值）", allow_negative=True)
    print(f"清洗后数据（允许负值）: {cleaned_with_negative.dropna().tolist()}")

def main():
    """主测试函数"""
    print("🚀 宁德世贸数据处理器测试")
    print("=" * 50)
    
    # 测试1: 文件扫描
    monthly_files = test_scan_monthly_files()
    
    # 测试2: 单文件处理
    test_single_file_processing()
    
    # 测试3: 数据清洗
    test_data_cleaning()
    
    # 测试4: 批量处理（如果有文件的话）
    if monthly_files:
        print(f"\n📋 发现月度数据，可以运行完整批量处理测试")
        print("💡 运行命令: python ningde_data_processor.py batch")
    else:
        print(f"\n⚠️ 未发现月度数据文件夹，无法进行批量处理测试")
        print("💡 请确保在'宁德世贸'目录下有'2025年*月'格式的文件夹")
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    main()
