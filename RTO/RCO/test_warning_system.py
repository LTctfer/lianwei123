#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预警系统测试脚本
演示数据清洗、预警检测和可视化功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from pathlib import Path

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def create_test_data():
    """创建测试数据"""
    print("🧪 创建测试数据...")
    
    # 设置随机种子以便重现结果
    np.random.seed(42)
    
    # 生成24小时的数据，每分钟一个数据点
    start_time = datetime.now() - timedelta(hours=24)
    timestamps = pd.date_range(start=start_time, periods=1440, freq='1min')
    
    # 基础数据生成
    data = {
        'timestamp': timestamps,
        'temperature_combustion': np.random.normal(780, 30, 1440),      # 燃烧室温度 (正常760+)
        'temperature_outlet': np.random.normal(45, 10, 1440),          # 出口温度 (正常<60)
        'concentration_in': np.random.normal(200, 40, 1440),           # 进口浓度
        'concentration_out': np.random.normal(15, 8, 1440),            # 出口浓度 (正常<50)
        'temperature_adsorption': np.random.normal(35, 5, 1440),       # 吸附温度 (正常<40)
        'temperature_desorption': np.random.normal(105, 10, 1440),     # 脱附温度 (正常90-120)
        'temperature_reactor_outlet': np.random.normal(550, 50, 1440), # 反应器出口温度 (正常<600)
        'emergency_valve': np.random.choice([0, 1], 1440, p=[0.98, 0.02]), # 应急阀门状态
        'pressure_loss_catalytic': np.random.normal(1.2, 0.3, 1440),   # 催化燃烧压力损失 (正常<2)
        'particle_content': np.random.normal(5, 2, 1440),              # 颗粒物含量 (正常<10)
    }
    
    # 添加一些异常情况来触发预警
    print("  添加异常情况...")
    
    # 1. 燃烧室温度过低 (8:00-8:30)
    start_idx = 480  # 8小时 * 60分钟
    end_idx = 510    # 8.5小时 * 60分钟
    data['temperature_combustion'][start_idx:end_idx] = np.random.normal(720, 20, end_idx-start_idx)
    
    # 2. 出口温度过高 (10:00-10:45)
    start_idx = 600
    end_idx = 645
    data['temperature_outlet'][start_idx:end_idx] = np.random.normal(75, 5, end_idx-start_idx)
    
    # 3. 出口浓度超标 (14:00-14:20)
    start_idx = 840
    end_idx = 860
    data['concentration_out'][start_idx:end_idx] = np.random.normal(80, 10, end_idx-start_idx)
    
    # 4. 吸附温度过高 (16:00-16:15)
    start_idx = 960
    end_idx = 975
    data['temperature_adsorption'][start_idx:end_idx] = np.random.normal(50, 3, end_idx-start_idx)
    
    # 5. 反应器出口温度过高 (18:00-18:10)
    start_idx = 1080
    end_idx = 1090
    data['temperature_reactor_outlet'][start_idx:end_idx] = np.random.normal(650, 20, end_idx-start_idx)
    
    # 6. 应急阀门异常开启 (20:00-20:05)
    start_idx = 1200
    end_idx = 1205
    data['emergency_valve'][start_idx:end_idx] = 1
    
    # 7. 添加一些负值和零值用于测试数据清洗
    data['temperature_combustion'][100:105] = -10  # 负值
    data['concentration_out'][200:203] = 0         # 零值
    data['temperature_outlet'][300:302] = -5      # 负值
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 计算处理效率
    df['treatment_efficiency'] = 1 - (df['concentration_out'] / df['concentration_in'])
    df['treatment_efficiency'] = df['treatment_efficiency'].clip(0, 1)  # 限制在0-1之间
    
    # 保存测试数据
    output_file = "test_equipment_data.xlsx"
    df.to_excel(output_file, index=False)
    
    print(f"✅ 测试数据已创建: {output_file}")
    print(f"   数据点数: {len(df)}")
    print(f"   时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
    
    return output_file

def run_warning_test():
    """运行预警系统测试"""
    print("🚨 预警系统测试")
    print("=" * 50)
    
    try:
        # 导入预警系统
        from warning_system import WarningSystem
        
        # 创建测试数据
        test_file = create_test_data()
        
        # 创建预警系统实例
        warning_system = WarningSystem()
        
        # 运行分析
        print(f"\n🔍 分析测试数据: {test_file}")
        violations, summary = warning_system.process_data_file(test_file)
        
        if violations:
            print(f"\n📊 发现 {len(violations)} 个违规事件:")
            
            # 按时间排序显示违规事件
            violations_df = pd.DataFrame(violations)
            violations_df = violations_df.sort_values('timestamp')
            
            for _, violation in violations_df.iterrows():
                timestamp = violation['timestamp'].strftime('%H:%M:%S')
                rule_name = violation['rule_name']
                value = violation['value']
                threshold = violation['threshold']
                severity = violation['severity']
                status = violation['status']
                
                if status == 'start':
                    print(f"  🔴 [{timestamp}] {rule_name} - 开始违规")
                    print(f"      当前值: {value:.2f}, 阈值: {threshold}, 严重程度: {severity}")
                elif status == 'end':
                    print(f"  🟢 [{timestamp}] {rule_name} - 违规结束")
            
            # 显示汇总统计
            print(f"\n📈 违规汇总统计:")
            print(f"  总违规次数: {summary.get('total', 0)}")
            print(f"  进行中违规: {summary.get('ongoing', 0)}")
            print(f"  已解决违规: {summary.get('resolved', 0)}")
            
            if summary.get('by_severity'):
                print("  按严重程度分布:")
                for severity, count in summary['by_severity'].items():
                    print(f"    {severity.upper()}级: {count} 次")
            
            if summary.get('by_equipment'):
                print("  按设备分布:")
                for equipment, count in summary['by_equipment'].items():
                    print(f"    {equipment}: {count} 次")
            
            # 生成可视化报告
            print(f"\n📊 生成可视化报告...")
            warning_system.visualizer.generate_violation_report(
                violations,
                warning_system.rule_engine.warning_records,
                summary,
                "D:/GitHub/lianwei123/RTO/RCO/可视化结果"
            )
            
        else:
            print("✅ 未发现违规事件")
        
        print(f"\n🎉 预警系统测试完成!")
        
    except ImportError as e:
        print(f"❌ 导入预警系统失败: {e}")
        print("请确保 warning_system.py 文件存在且可导入")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

def test_data_cleaning():
    """测试数据清洗功能"""
    print("\n🧹 测试数据清洗功能")
    print("-" * 30)
    
    try:
        from warning_system import DataCleaner
        
        # 创建包含异常数据的测试数据
        data = {
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='1min'),
            'temperature': [20, -5, 0, 25, 30, 1000, 22, 24, -10, 28] * 10,  # 包含负值、零值、异常值
            'concentration': [10, 15, 0, -2, 12, 500, 8, 9, 11, 13] * 10,
            'pressure': [1.0, 1.2, 0, 1.1, -0.5, 10.0, 1.3, 1.1, 1.2, 1.0] * 10
        }
        
        df_dirty = pd.DataFrame(data)
        print(f"原始数据: {len(df_dirty)} 行")
        print(f"温度列统计: 最小值={df_dirty['temperature'].min()}, 最大值={df_dirty['temperature'].max()}")
        
        # 执行数据清洗
        cleaner = DataCleaner()
        df_clean = cleaner.clean_data(df_dirty)
        
        print(f"清洗后数据: {len(df_clean)} 行")
        print(f"温度列统计: 最小值={df_clean['temperature'].min()}, 最大值={df_clean['temperature'].max()}")
        
        print("✅ 数据清洗测试完成")
        
    except Exception as e:
        print(f"❌ 数据清洗测试失败: {e}")

def test_visualization():
    """测试可视化功能"""
    print("\n📊 测试可视化功能")
    print("-" * 30)
    
    try:
        from warning_system import WarningVisualizer
        
        # 创建模拟违规数据
        violations = [
            {
                'timestamp': datetime.now() - timedelta(hours=2),
                'rule_name': '燃烧室温度不达标',
                'severity': 'high',
                'value': 720,
                'threshold': 760
            },
            {
                'timestamp': datetime.now() - timedelta(hours=1),
                'rule_name': '出口温度超标',
                'severity': 'medium',
                'value': 75,
                'threshold': 60
            }
        ]
        
        summary = {
            'total': 2,
            'ongoing': 0,
            'resolved': 2,
            'by_severity': {'high': 1, 'medium': 1},
            'by_equipment': {'燃烧室': 1, '废气出口': 1}
        }
        
        # 创建可视化器
        visualizer = WarningVisualizer()
        
        # 测试严重程度分布图
        visualizer.plot_severity_distribution(summary, "D:/GitHub/lianwei123/RTO/RCO/可视化结果/test_severity.png")
        
        # 测试设备违规统计图
        visualizer.plot_equipment_violations(summary, "D:/GitHub/lianwei123/RTO/RCO/可视化结果/test_equipment.png")
        
        print("✅ 可视化测试完成，图片已保存")
        
    except Exception as e:
        print(f"❌ 可视化测试失败: {e}")

def main():
    """主函数"""
    print("🧪 预警系统完整测试")
    print("=" * 60)
    
    # 检查依赖
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        print("✅ 依赖库检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖库: {e}")
        print("请安装: pip install matplotlib seaborn pandas numpy openpyxl")
        return
    
    # 运行各项测试
    test_data_cleaning()
    test_visualization()
    run_warning_test()
    
    print("\n" + "=" * 60)
    print("🎊 所有测试完成!")
    print("\n💡 查看生成的文件:")
    print("  - test_equipment_data.xlsx (测试数据)")
    print("  - D:/GitHub/lianwei123/RTO/RCO/可视化结果/ (可视化报告)")
    print("  - D:/GitHub/lianwei123/RTO/RCO/可视化结果/*.png (测试图片)")

if __name__ == "__main__":
    main()
