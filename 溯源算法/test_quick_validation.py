#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证改进效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pollution_source_tracker import *
import numpy as np
import math
import random

def generate_optimal_monitoring_layout(source_x, source_y, wind_direction, num_stations=8):
    """生成优化的监测站布局"""
    stations = []
    
    # 转换风向为弧度（风吹向的方向）
    wind_to_rad = math.radians(wind_direction + 180)
    
    # 1. 主轴布局：沿下风向布置监测站（增加更密集的布局）
    downwind_distances = [50, 100, 150, 200, 300, 400]  # 增加更多下风向距离
    for i, dist in enumerate(downwind_distances):
        x = source_x + dist * math.cos(wind_to_rad)
        y = source_y + dist * math.sin(wind_to_rad)
        stations.append((x, y, 10))
    
    # 2. 交叉布局：垂直于风向的监测站（进一步减少侧风向距离）
    cross_wind_rad = wind_to_rad + math.pi/2  # 垂直于风向
    cross_distances = [60, 100]  # 进一步减少侧风向距离
    base_distances = [100, 200]  # 多个基准下风向距离

    for base_dist in base_distances:
        for cross_dist in cross_distances:
            # 基准位置
            base_x = source_x + base_dist * math.cos(wind_to_rad)
            base_y = source_y + base_dist * math.sin(wind_to_rad)

            # 两侧的监测站
            x1 = base_x + cross_dist * math.cos(cross_wind_rad)
            y1 = base_y + cross_dist * math.sin(cross_wind_rad)
            stations.append((x1, y1, 10))

            x2 = base_x - cross_dist * math.cos(cross_wind_rad)
            y2 = base_y - cross_dist * math.sin(cross_wind_rad)
            stations.append((x2, y2, 10))

    # 3. 近场监测站：污染源附近（增加更多近场约束）
    near_distances = [60, 120]  # 两个近场距离圈
    near_angles = [wind_to_rad + math.pi/6, wind_to_rad - math.pi/6,  # 下风向两侧30度
                   wind_to_rad + math.pi/3, wind_to_rad - math.pi/3]  # 下风向两侧60度

    for dist in near_distances:
        for angle in near_angles[:2]:  # 每个距离圈只用前两个角度
            x = source_x + dist * math.cos(angle)
            y = source_y + dist * math.sin(angle)
            stations.append((x, y, 10))

    # 4. 极近场监测站：提供强位置约束（20-30米范围）
    ultra_near_distances = [25, 35]  # 极近场距离
    ultra_near_angles = [
        wind_to_rad,                    # 正下风向
        wind_to_rad + math.pi/12,       # 下风向右侧15度
        wind_to_rad - math.pi/12,       # 下风向左侧15度
        wind_to_rad + math.pi/6,        # 下风向右侧30度
        wind_to_rad - math.pi/6,        # 下风向左侧30度
    ]

    for dist in ultra_near_distances:
        for angle in ultra_near_angles:
            x = source_x + dist * math.cos(angle)
            y = source_y + dist * math.sin(angle)
            stations.append((x, y, 10))

    # 5. 超极近场监测站：提供最强位置约束（15-20米范围）
    super_near_distance = 18
    super_near_angles = [
        wind_to_rad,                    # 正下风向
        wind_to_rad + math.pi/4,        # 下风向右侧45度
        wind_to_rad - math.pi/4,        # 下风向左侧45度
    ]

    for angle in super_near_angles:
        x = source_x + super_near_distance * math.cos(angle)
        y = source_y + super_near_distance * math.sin(angle)
        stations.append((x, y, 10))

    # 返回指定数量的监测站，优先选择近场站点
    return stations[:num_stations]

def quick_test():
    """快速测试改进效果"""
    print("=== 快速验证改进效果 ===\n")
    
    # 创建溯源器
    tracker = PollutionSourceTracker()
    
    # 设置高精度气象数据 - 东风
    met_data = MeteorologicalData(
        wind_speed=3.52,        # 更精确的风速
        wind_direction=89.8,    # 更精确的风向
        temperature=20.3,       # 更精确的温度
        humidity=58.7,          # 更精确的湿度
        pressure=1013.42,       # 更精确的气压
        solar_radiation=485.6,  # 更精确的太阳辐射
        cloud_cover=0.28,       # 更精确的云量
        timestamp="2024-01-01 12:00:00"
    )
    tracker.set_meteorological_data(met_data)
    
    # 真实污染源
    true_source = PollutionSource(x=500, y=500, z=30, emission_rate=10.0)
    print(f"真实污染源位置: ({true_source.x}, {true_source.y}, {true_source.z})")
    print(f"真实排放强度: {true_source.emission_rate} g/s\n")
    
    # 使用优化的监测站布局（增加更多近场站点）
    monitoring_stations = generate_optimal_monitoring_layout(
        true_source.x, true_source.y, met_data.wind_direction, num_stations=16
    )
    
    print("监测站布局:")
    for i, (x, y, z) in enumerate(monitoring_stations):
        print(f"  站点{i+1}: ({x:.1f}, {y:.1f}, {z})")
    print()
    
    # 生成观测数据
    monitoring_data = []
    print("生成监测站观测数据:")
    for i, (x, y, z) in enumerate(monitoring_stations):
        # 计算理论浓度
        theoretical_conc = tracker.gaussian_model.calculate_concentration(
            true_source, x, y, z, met_data
        )
        
        # 添加5%的随机噪声
        noise_factor = 1.0 + random.uniform(-0.05, 0.05)
        observed_conc = max(0.1, theoretical_conc * noise_factor)  # 最小0.1 μg/m³
        
        print(f"  站点{i+1}: 位置({x:.1f}, {y:.1f}, {z}), 理论浓度={theoretical_conc:.2f} μg/m³")
        print(f"    观测浓度={observed_conc:.2f} μg/m³")
        
        monitoring_data.append(MonitoringData(
            station_id=f"S{i+1:02d}",
            x=x, y=y, z=z,
            concentration=observed_conc,
            timestamp=met_data.timestamp
        ))
    
    # 设置监测数据
    for data in monitoring_data:
        tracker.add_monitoring_data(data)
    
    print("\n" + "="*60)
    print("开始污染源溯源...")
    print(f"监测站点数量: {len(monitoring_data)}")
    print(f"气象条件: 风速={met_data.wind_speed}m/s, 风向={met_data.wind_direction}°")
    
    # 执行溯源（只运行一次快速测试）
    source = tracker.trace_pollution_source()
    
    print("\n" + "="*60)
    print("=== 精度评估 ===")
    
    # 计算位置误差
    position_error = math.sqrt(
        (source.x - true_source.x)**2 + 
        (source.y - true_source.y)**2
    )
    
    # 计算排放强度相对误差
    emission_error = abs(source.emission_rate - true_source.emission_rate) / true_source.emission_rate * 100
    
    print(f"位置误差: {position_error:.1f} 米")
    print(f"排放强度相对误差: {emission_error:.1f}%")
    
    # 计算各监测站预测精度
    print("\n各监测站预测精度:")
    relative_errors = []
    for i, monitor in enumerate(monitoring_data):
        predicted = tracker.gaussian_model.calculate_concentration(
            source, monitor.x, monitor.y, monitor.z, met_data
        )
        relative_error = abs(predicted - monitor.concentration) / monitor.concentration * 100
        relative_errors.append(relative_error)
        print(f"  {monitor.station_id}: 观测={monitor.concentration:.2f}, 预测={predicted:.2f}, 相对误差={relative_error:.1f}%")
    
    avg_relative_error = sum(relative_errors) / len(relative_errors)
    max_relative_error = max(relative_errors)
    
    print(f"\n总体精度评估:")
    print(f"  平均相对误差: {avg_relative_error:.1f}%")
    print(f"  最大相对误差: {max_relative_error:.1f}%")
    
    print(f"\n目标精度检查:")
    print(f"  位置误差 ≤ 100米: {'✓' if position_error <= 100 else '✗'} ({position_error:.1f}米)")
    print(f"  平均相对误差 ≤ 20%: {'✓' if avg_relative_error <= 20 else '✗'} ({avg_relative_error:.1f}%)")
    
    if position_error <= 100 and avg_relative_error <= 20:
        print("\n🎉 所有精度目标已达成！")
    else:
        print("\n⚠️  部分精度目标未达成，需要进一步优化")

if __name__ == "__main__":
    quick_test()
