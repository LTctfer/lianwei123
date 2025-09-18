#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试高斯烟羽模型计算
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pollution_source_tracker import *
import math

def debug_gaussian_calculation():
    """调试高斯烟羽模型的计算过程"""
    print("=== 调试高斯烟羽模型计算 ===\n")
    
    # 创建高斯模型
    gaussian_model = GaussianPlumeModel()
    
    # 设置测试参数 - 使用东风
    source = PollutionSource(x=500, y=500, z=30, emission_rate=10.0)
    met_data = MeteorologicalData(
        wind_speed=3.5,
        wind_direction=90,  # 东风，从东向西吹
        temperature=20.0,
        humidity=60.0,
        pressure=1013.25,
        solar_radiation=500.0,
        cloud_cover=0.3,
        timestamp="2024-01-01 12:00:00"
    )

    print(f"污染源: ({source.x}, {source.y}, {source.z}), 排放强度: {source.emission_rate} g/s")
    print(f"气象条件: 风速={met_data.wind_speed}m/s, 风向={met_data.wind_direction}° (东风)")
    print("风向说明: 90°表示风从东向西吹，下风向应该在污染源西侧")
    print()

    # 测试不同位置的浓度计算 - 重新布置在下风向
    test_points = [
        (300, 500, 10, "站点1-正西"),
        (200, 500, 10, "站点2-西远"),
        (100, 500, 10, "站点3-西很远"),
        (300, 400, 10, "站点4-西南"),
        (300, 600, 10, "站点5-西北"),
        (150, 450, 10, "站点6-西南远"),
        (600, 500, 10, "站点7-正东(上风向)"),
        (500, 400, 10, "站点8-正南(侧风向)"),
    ]
    
    for x, y, z, name in test_points:
        print(f"=== {name}: ({x}, {y}, {z}) ===")
        
        # 计算坐标转换
        wind_from_rad = math.radians(met_data.wind_direction)  # 风吹来的方向
        wind_to_rad = math.radians(met_data.wind_direction + 180)  # 风吹向的方向
        dx = x - source.x
        dy = y - source.y

        # 转换到风向坐标系 (使用风吹向的方向)
        x_wind = dx * math.cos(wind_to_rad) + dy * math.sin(wind_to_rad)
        y_wind = -dx * math.sin(wind_to_rad) + dy * math.cos(wind_to_rad)

        print(f"  风向转换: 风来向={met_data.wind_direction}°, 风去向={met_data.wind_direction + 180}°")
        
        print(f"  相对位置: dx={dx:.1f}, dy={dy:.1f}")
        print(f"  风向坐标系: x_wind={x_wind:.1f}, y_wind={y_wind:.1f}")
        
        if x_wind <= 0:
            print(f"  ❌ 上风向位置，浓度=0")
            continue
        
        # 获取稳定度等级
        stability_class = gaussian_model.stability.get_stability_class(
            met_data.wind_speed, met_data.solar_radiation, met_data.cloud_cover
        )
        print(f"  稳定度等级: {stability_class}")
        
        # 计算扩散系数
        sigma_y, sigma_z = gaussian_model.stability.get_dispersion_coefficients(stability_class, x_wind)
        print(f"  扩散系数: sigma_y={sigma_y:.2f}m, sigma_z={sigma_z:.2f}m")
        
        # 计算高斯烟羽项
        horizontal_term = math.exp(-0.5 * (y_wind / sigma_y) ** 2)
        vertical_term1 = math.exp(-0.5 * ((z - source.z) / sigma_z) ** 2)
        vertical_term2 = math.exp(-0.5 * ((z + source.z) / sigma_z) ** 2)
        vertical_term = vertical_term1 + vertical_term2
        
        print(f"  水平扩散项: {horizontal_term:.6f}")
        print(f"  垂直扩散项: {vertical_term:.6f}")
        
        # 计算分母
        denominator = 2 * math.pi * met_data.wind_speed * sigma_y * sigma_z
        print(f"  分母: {denominator:.2f}")
        
        # 计算浓度
        concentration = (source.emission_rate / denominator) * horizontal_term * vertical_term
        concentration_ug = concentration * 1e6  # 转换为μg/m³
        
        print(f"  浓度 (g/m³): {concentration:.2e}")
        print(f"  浓度 (μg/m³): {concentration_ug:.2f}")
        
        # 使用模型方法验证
        model_concentration = gaussian_model.calculate_concentration(source, x, y, z, met_data)
        print(f"  模型计算结果: {model_concentration:.2f} μg/m³")
        print()

def test_dispersion_coefficients():
    """测试扩散系数计算"""
    print("=== 测试扩散系数计算 ===\n")
    
    stability = AtmosphericStability()
    
    distances = [100, 500, 1000, 2000, 5000]
    stability_classes = ['A', 'B', 'C', 'D', 'E', 'F']
    
    print("距离(m)\\稳定度", end="")
    for sc in stability_classes:
        print(f"\t{sc}", end="")
    print()
    
    for dist in distances:
        print(f"{dist}", end="")
        for sc in stability_classes:
            sigma_y, sigma_z = stability.get_dispersion_coefficients(sc, dist)
            print(f"\t{sigma_y:.0f},{sigma_z:.0f}", end="")
        print()

if __name__ == "__main__":
    debug_gaussian_calculation()
    print("\n" + "="*60 + "\n")
    test_dispersion_coefficients()
