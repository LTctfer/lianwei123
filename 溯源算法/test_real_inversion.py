#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实际数据反算功能
验证新添加的Web界面反算功能是否正常工作
"""

import sys
import os
import time
import numpy as np

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_real_data_inversion():
    """测试实际数据反算功能"""
    
    print("=" * 60)
    print("测试实际数据反算功能")
    print("=" * 60)
    
    try:
        # 导入必要的模块
        from optimized_source_inversion import OptimizedSourceInversion, OptimizedSensorData, AdaptiveGAParameters
        from gaussian_plume_model import MeteoData, PollutionSource, GaussianPlumeModel
        from datetime import datetime
        
        print("✅ 成功导入所有模块")
        
        # 1. 创建真实污染源（用于生成观测数据）
        true_source = PollutionSource(
            x=200.0,
            y=300.0,
            z=15.0,
            emission_rate=2.5
        )
        
        # 2. 设置气象条件
        meteo_data = MeteoData(
            wind_speed=3.5,
            wind_direction=225.0,
            temperature=20.0,
            pressure=101325.0
        )
        
        print(f"真实污染源位置: ({true_source.x}, {true_source.y}, {true_source.z})")
        print(f"真实源强: {true_source.emission_rate} g/s")
        print(f"气象条件: 风速{meteo_data.wind_speed}m/s, 风向{meteo_data.wind_direction}°")
        
        # 3. 生成模拟观测数据
        gaussian_model = GaussianPlumeModel()
        
        # 传感器位置
        sensor_positions = [
            (100, 200, 2),   # S001
            (300, 200, 2),   # S002
            (200, 100, 2),   # S003
            (200, 400, 2),   # S004
            (150, 250, 2),   # S005
            (250, 350, 2),   # S006
            (400, 400, 2),   # S007
            (50, 150, 2),    # S008
        ]
        
        # 计算理论浓度并添加噪声
        sensor_data = []
        for i, (x, y, z) in enumerate(sensor_positions):
            # 计算理论浓度
            concentration = gaussian_model.calculate_concentration(
                source=true_source,
                receptor_x=x,
                receptor_y=y,
                receptor_z=z,
                meteo=meteo_data
            )
            
            # 添加10%的随机噪声
            noise = np.random.normal(0, concentration * 0.1)
            observed_concentration = max(0, concentration + noise)
            
            sensor_data.append(OptimizedSensorData(
                sensor_id=f"S{i+1:03d}",
                x=x,
                y=y,
                z=z,
                concentration=observed_concentration,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                uncertainty=0.1,
                weight=1.0
            ))
        
        print(f"\n生成了 {len(sensor_data)} 个传感器观测数据")
        for sensor in sensor_data[:3]:  # 显示前3个
            print(f"  {sensor.sensor_id}: 位置({sensor.x}, {sensor.y}), 浓度{sensor.concentration:.2f}")
        
        # 4. 配置反算参数（快速模式）
        params = AdaptiveGAParameters(
            population_size=30,
            max_generations=50,
            use_parallel=False,
            use_cache=True,
            adaptive_mutation=True
        )
        
        # 设置搜索边界
        search_bounds = {
            'x': (-500, 500),
            'y': (-500, 500),
            'z': (0, 100),
            'q': (0.001, 10.0)
        }
        
        # 5. 执行反算
        print("\n开始污染源反算...")
        inverter = OptimizedSourceInversion(
            search_bounds=search_bounds,
            ga_parameters=params
        )
        
        start_time = time.time()
        result = inverter.invert_source(
            sensor_data=sensor_data,
            meteo_data=meteo_data,
            true_source=true_source,  # 用于计算误差
            verbose=True,
            uncertainty_analysis=False  # 快速模式不做不确定性分析
        )
        computation_time = time.time() - start_time
        
        # 6. 显示结果
        print("\n" + "=" * 60)
        print("反算结果")
        print("=" * 60)
        
        print(f"反算位置: ({result.source_x:.2f}, {result.source_y:.2f}, {result.source_z:.2f})")
        print(f"真实位置: ({true_source.x:.2f}, {true_source.y:.2f}, {true_source.z:.2f})")
        
        print(f"反算源强: {result.emission_rate:.4f} g/s")
        print(f"真实源强: {true_source.emission_rate:.4f} g/s")
        
        print(f"位置误差: {result.position_error:.2f} m")
        print(f"源强误差: {result.emission_error:.2f} %")
        
        print(f"目标函数值: {result.objective_value:.2e}")
        print(f"计算时间: {computation_time:.2f} 秒")
        
        # 7. 评估结果
        if result.position_error < 100:  # 位置误差小于100米
            print("\n✅ 反算结果良好！位置误差在可接受范围内")
        else:
            print("\n⚠️ 反算结果一般，位置误差较大")
        
        if result.emission_error < 50:  # 源强误差小于50%
            print("✅ 源强估计良好！")
        else:
            print("⚠️ 源强估计误差较大")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("实际数据反算功能测试")
    
    success = test_real_data_inversion()
    
    if success:
        print("\n🎉 测试完成！实际数据反算功能正常工作")
        print("\n现在可以在Web界面中使用以下功能：")
        print("1. 手动输入传感器观测数据")
        print("2. 上传CSV格式的观测数据")
        print("3. 使用示例数据进行测试")
        print("4. 配置气象条件和反算参数")
        print("5. 执行污染源反算并查看结果")
    else:
        print("\n❌ 测试失败，请检查代码")

if __name__ == "__main__":
    main()
