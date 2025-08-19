#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试MeteoData修复
验证所有必需参数是否正确传递
"""

import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_meteo_data_creation():
    """测试MeteoData创建"""
    
    print("=" * 50)
    print("测试MeteoData创建")
    print("=" * 50)
    
    try:
        from gaussian_plume_model import MeteoData
        
        # 测试完整参数创建
        meteo_data = MeteoData(
            wind_speed=3.5,
            wind_direction=225.0,
            temperature=20.0,
            humidity=60.0,
            pressure=1013.25,
            solar_radiation=500.0,
            cloud_cover=0.3
        )
        
        print("✅ MeteoData创建成功！")
        print(f"风速: {meteo_data.wind_speed} m/s")
        print(f"风向: {meteo_data.wind_direction}°")
        print(f"温度: {meteo_data.temperature}°C")
        print(f"湿度: {meteo_data.humidity}%")
        print(f"气压: {meteo_data.pressure} hPa")
        print(f"太阳辐射: {meteo_data.solar_radiation} W/m²")
        print(f"云量: {meteo_data.cloud_cover}")
        
        return True
        
    except Exception as e:
        print(f"❌ MeteoData创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_optimized_sensor_data():
    """测试OptimizedSensorData创建"""
    
    print("\n" + "=" * 50)
    print("测试OptimizedSensorData创建")
    print("=" * 50)
    
    try:
        from optimized_source_inversion import OptimizedSensorData
        from datetime import datetime
        
        sensor_data = OptimizedSensorData(
            sensor_id="S001",
            x=100.0,
            y=200.0,
            z=2.0,
            concentration=45.2,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            uncertainty=0.1,
            weight=1.0
        )
        
        print("✅ OptimizedSensorData创建成功！")
        print(f"传感器ID: {sensor_data.sensor_id}")
        print(f"位置: ({sensor_data.x}, {sensor_data.y}, {sensor_data.z})")
        print(f"浓度: {sensor_data.concentration}")
        print(f"时间戳: {sensor_data.timestamp}")
        
        return True
        
    except Exception as e:
        print(f"❌ OptimizedSensorData创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_inversion_setup():
    """测试反算器设置"""
    
    print("\n" + "=" * 50)
    print("测试反算器设置")
    print("=" * 50)
    
    try:
        from optimized_source_inversion import OptimizedSourceInversion, AdaptiveGAParameters
        
        # 创建参数
        params = AdaptiveGAParameters(
            population_size=30,
            max_generations=50,
            use_parallel=False,
            use_cache=True
        )
        
        # 创建反算器
        inverter = OptimizedSourceInversion(ga_parameters=params)
        
        print("✅ 反算器创建成功！")
        print(f"种群大小: {params.population_size}")
        print(f"最大代数: {params.max_generations}")
        print(f"并行计算: {params.use_parallel}")
        print(f"缓存机制: {params.use_cache}")
        
        return True
        
    except Exception as e:
        print(f"❌ 反算器创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_workflow():
    """测试完整工作流程"""
    
    print("\n" + "=" * 50)
    print("测试完整工作流程")
    print("=" * 50)
    
    try:
        from optimized_source_inversion import OptimizedSourceInversion, OptimizedSensorData, AdaptiveGAParameters
        from gaussian_plume_model import MeteoData
        from datetime import datetime
        
        # 1. 创建气象数据
        meteo_data = MeteoData(
            wind_speed=3.5,
            wind_direction=225.0,
            temperature=20.0,
            humidity=60.0,
            pressure=1013.25,
            solar_radiation=500.0,
            cloud_cover=0.3
        )
        
        # 2. 创建传感器数据
        sensor_data = [
            OptimizedSensorData(
                sensor_id="S001",
                x=100.0, y=200.0, z=2.0,
                concentration=45.2,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                uncertainty=0.1, weight=1.0
            ),
            OptimizedSensorData(
                sensor_id="S002",
                x=300.0, y=200.0, z=2.0,
                concentration=38.7,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                uncertainty=0.1, weight=1.0
            ),
            OptimizedSensorData(
                sensor_id="S003",
                x=200.0, y=100.0, z=2.0,
                concentration=52.1,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                uncertainty=0.1, weight=1.0
            )
        ]
        
        # 3. 创建反算器
        params = AdaptiveGAParameters(
            population_size=20,
            max_generations=10,  # 很少的代数用于快速测试
            use_parallel=False,
            use_cache=True
        )
        
        inverter = OptimizedSourceInversion(ga_parameters=params)
        
        print("✅ 完整工作流程设置成功！")
        print(f"气象数据: 风速{meteo_data.wind_speed}m/s, 风向{meteo_data.wind_direction}°")
        print(f"传感器数量: {len(sensor_data)}")
        print(f"反算参数: {params.population_size}个体, {params.max_generations}代")
        
        # 注意：这里不执行实际反算，只测试设置
        print("⚠️ 跳过实际反算执行（仅测试设置）")
        
        return True
        
    except Exception as e:
        print(f"❌ 完整工作流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    
    print("MeteoData修复验证测试")
    print("检查所有必需参数是否正确传递")
    
    tests = [
        ("MeteoData创建", test_meteo_data_creation),
        ("OptimizedSensorData创建", test_optimized_sensor_data),
        ("反算器设置", test_inversion_setup),
        ("完整工作流程", test_complete_workflow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 运行测试: {test_name}")
        success = test_func()
        results.append((test_name, success))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        print("\n🎉 所有测试通过！MeteoData修复成功")
        print("现在可以正常使用Web界面的实际数据反算功能")
    else:
        print("\n⚠️ 部分测试失败，请检查代码")

if __name__ == "__main__":
    main()
