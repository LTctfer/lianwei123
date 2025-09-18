#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试改进后的污染源溯源精度
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pollution_source_tracker import *
import numpy as np

def test_improved_accuracy():
    """测试改进后的溯源精度"""
    print("=== 测试改进后的污染源溯源精度 ===\n")
    
    # 创建溯源器
    tracker = PollutionSourceTracker()
    
    # 设置气象数据
    met_data = MeteorologicalData(
        wind_speed=3.5,
        wind_direction=45,
        temperature=20.0,
        humidity=60.0,
        pressure=1013.25,
        solar_radiation=500.0,
        cloud_cover=0.3,
        timestamp="2024-01-01 12:00:00"
    )
    tracker.set_meteorological_data(met_data)
    
    # 真实污染源（用于生成模拟数据）
    true_source = PollutionSource(x=800, y=600, z=50, emission_rate=10.0)
    print(f"真实污染源位置: ({true_source.x}, {true_source.y}, {true_source.z})")
    print(f"真实排放强度: {true_source.emission_rate} g/s\n")
    
    # 生成监测站数据（模拟真实观测）
    monitoring_stations = [
        (200, 300, 10),   # 站点1
        (500, 800, 10),   # 站点2
        (1000, 400, 10),  # 站点3
        (1200, 900, 10),  # 站点4
        (300, 1000, 10),  # 站点5
        (1500, 700, 10),  # 站点6
    ]
    
    gaussian_model = GaussianPlumeModel()
    
    print("生成监测站观测数据:")
    for i, (x, y, z) in enumerate(monitoring_stations):
        # 计算理论浓度
        true_concentration = gaussian_model.calculate_concentration(
            true_source, x, y, z, met_data
        )
        
        # 添加5%的随机噪声模拟观测误差
        noise = np.random.normal(0, 0.05 * true_concentration)
        observed_concentration = max(0.1, true_concentration + noise)
        
        # 添加监测数据
        monitor_data = MonitoringData(
            station_id=f"S{i+1:02d}",
            x=x, y=y, z=z,
            concentration=observed_concentration,
            timestamp="2024-01-01 12:00:00"
        )
        tracker.add_monitoring_data(monitor_data)
        
        print(f"  站点{monitor_data.station_id}: 位置({x}, {y}, {z}), "
              f"浓度={observed_concentration:.2f} μg/m³")
    
    print("\n" + "="*60)
    
    # 执行溯源
    result_source = tracker.trace_pollution_source()
    
    if result_source:
        print("\n" + "="*60)
        print("=== 精度评估 ===")
        
        # 计算位置误差
        position_error = np.sqrt(
            (result_source.x - true_source.x)**2 + 
            (result_source.y - true_source.y)**2
        )
        
        # 计算排放强度误差
        emission_error = abs(result_source.emission_rate - true_source.emission_rate) / true_source.emission_rate
        
        print(f"位置误差: {position_error:.1f} 米")
        print(f"排放强度相对误差: {emission_error:.1%}")
        
        # 验证所有监测站的预测精度
        print("\n各监测站预测精度:")
        relative_errors = []
        
        for monitor in tracker.monitoring_data:
            predicted = gaussian_model.calculate_concentration(
                result_source, monitor.x, monitor.y, monitor.z, met_data
            )
            relative_error = abs(predicted - monitor.concentration) / monitor.concentration
            relative_errors.append(relative_error)
            
            print(f"  {monitor.station_id}: 观测={monitor.concentration:.2f}, "
                  f"预测={predicted:.2f}, 相对误差={relative_error:.1%}")
        
        avg_relative_error = np.mean(relative_errors)
        max_relative_error = np.max(relative_errors)
        
        print(f"\n总体精度评估:")
        print(f"  平均相对误差: {avg_relative_error:.1%}")
        print(f"  最大相对误差: {max_relative_error:.1%}")
        
        # 检查是否满足目标精度
        print(f"\n目标精度检查:")
        position_target = position_error <= 100
        accuracy_target = avg_relative_error <= 0.2
        
        print(f"  位置误差 ≤ 100米: {'✓' if position_target else '✗'} ({position_error:.1f}米)")
        print(f"  平均相对误差 ≤ 20%: {'✓' if accuracy_target else '✗'} ({avg_relative_error:.1%})")
        
        if position_target and accuracy_target:
            print("\n🎉 所有精度目标均已达成！")
        else:
            print("\n⚠️  部分精度目标未达成，需要进一步优化")
            
        return position_error, avg_relative_error, max_relative_error
    else:
        print("溯源失败！")
        return None, None, None

def run_multiple_tests(num_tests=5):
    """运行多次测试评估稳定性"""
    print(f"\n=== 运行{num_tests}次测试评估算法稳定性 ===\n")
    
    position_errors = []
    avg_errors = []
    max_errors = []
    
    for i in range(num_tests):
        print(f"--- 第{i+1}次测试 ---")
        pos_err, avg_err, max_err = test_improved_accuracy()
        
        if pos_err is not None:
            position_errors.append(pos_err)
            avg_errors.append(avg_err)
            max_errors.append(max_err)
        
        print()
    
    if position_errors:
        print("=== 多次测试统计结果 ===")
        print(f"位置误差: 平均={np.mean(position_errors):.1f}米, "
              f"标准差={np.std(position_errors):.1f}米")
        print(f"平均相对误差: 平均={np.mean(avg_errors):.1%}, "
              f"标准差={np.std(avg_errors):.1%}")
        print(f"最大相对误差: 平均={np.mean(max_errors):.1%}, "
              f"标准差={np.std(max_errors):.1%}")
        
        success_rate = sum(1 for pos, avg in zip(position_errors, avg_errors) 
                          if pos <= 100 and avg <= 0.2) / len(position_errors)
        print(f"精度目标达成率: {success_rate:.1%}")

if __name__ == "__main__":
    # 设置随机种子以便复现结果
    np.random.seed(42)
    
    # 单次测试
    test_improved_accuracy()
    
    # 多次测试
    run_multiple_tests(3)
