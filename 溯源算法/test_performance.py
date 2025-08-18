#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试脚本
测试不同配置下的运行时间
"""

import time
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_pollution_tracing import EnhancedPollutionTracingSystem, EnhancedScenarioConfig

def test_quick_mode():
    """测试快速模式"""
    print("=" * 60)
    print("测试快速模式 (50代, 30个体)")
    print("=" * 60)
    
    # 配置快速模式
    config = EnhancedScenarioConfig(
        source_x=150.0,
        source_y=200.0,
        emission_rate=2.5,
        wind_speed=3.5,
        sensor_grid_size=7,
        population_size=30,
        max_generations=50,
        use_parallel=True,
        use_cache=True
    )
    
    # 创建系统
    system = EnhancedPollutionTracingSystem(config)
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 创建场景
        print("创建测试场景...")
        true_source, meteo_data, sensor_data = system.create_scenario("quick_test")
        
        # 运行单个算法
        print("运行标准算法...")
        results = system.run_enhanced_inversion(
            sensor_data, meteo_data, ['standard']
        )
        
        # 计算总时间
        total_time = time.time() - start_time
        
        print(f"\n✅ 快速模式测试完成!")
        print(f"总运行时间: {total_time:.2f}秒")
        
        # 显示结果
        for alg, result in results.items():
            print(f"\n{alg} 算法结果:")
            print(f"  位置: ({result.source_x:.1f}, {result.source_y:.1f}, {result.source_z:.1f})")
            print(f"  源强: {result.emission_rate:.3f} g/s")
            print(f"  计算时间: {result.computation_time:.2f}s")
            print(f"  目标函数值: {result.objective_value:.2e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 快速模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_standard_mode():
    """测试标准模式"""
    print("\n" + "=" * 60)
    print("测试标准模式 (500代, 50个体)")
    print("=" * 60)
    
    # 配置标准模式
    config = EnhancedScenarioConfig(
        source_x=150.0,
        source_y=200.0,
        emission_rate=2.5,
        wind_speed=3.5,
        sensor_grid_size=7,
        population_size=50,
        max_generations=500,
        use_parallel=True,
        use_cache=True
    )
    
    # 创建系统
    system = EnhancedPollutionTracingSystem(config)
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 创建场景
        print("创建测试场景...")
        true_source, meteo_data, sensor_data = system.create_scenario("standard_test")
        
        # 运行单个算法
        print("运行标准算法...")
        results = system.run_enhanced_inversion(
            sensor_data, meteo_data, ['standard']
        )
        
        # 计算总时间
        total_time = time.time() - start_time
        
        print(f"\n✅ 标准模式测试完成!")
        print(f"总运行时间: {total_time:.2f}秒")
        
        # 显示结果
        for alg, result in results.items():
            print(f"\n{alg} 算法结果:")
            print(f"  位置: ({result.source_x:.1f}, {result.source_y:.1f}, {result.source_z:.1f})")
            print(f"  源强: {result.emission_rate:.3f} g/s")
            print(f"  计算时间: {result.computation_time:.2f}s")
            print(f"  目标函数值: {result.objective_value:.2e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 标准模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("污染源溯源算法性能测试")
    print("测试不同配置下的运行时间")
    
    # 测试快速模式
    quick_success = test_quick_mode()
    
    if quick_success:
        # 询问是否继续测试标准模式
        response = input("\n是否继续测试标准模式? (y/n): ").lower().strip()
        if response == 'y' or response == 'yes':
            test_standard_mode()
    
    print("\n" + "=" * 60)
    print("性能测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
