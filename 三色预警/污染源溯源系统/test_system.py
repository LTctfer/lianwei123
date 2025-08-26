#!/usr/bin/env python3
"""
系统测试脚本
验证污染源溯源系统的基本功能
"""

import sys
import os
import traceback
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("=" * 50)
    print("测试模块导入...")
    
    try:
        # 测试基础科学计算库
        import numpy as np
        import pandas as pd
        import scipy
        import sklearn
        print("✓ 基础科学计算库导入成功")
        
        # 测试可视化库
        import matplotlib
        import plotly
        print("✓ 可视化库导入成功")
        
        # 测试Web框架
        import flask
        print("✓ Web框架导入成功")
        
        # 测试自定义模块
        from algorithms.genetic_algorithm import GeneticAlgorithm, Individual
        from algorithms.pattern_search import PatternSearch
        from algorithms.gaussian_plume import GaussianPlumeModel
        from algorithms.data_fusion import DataFusionProcessor
        print("✓ 自定义算法模块导入成功")
        
        return True
        
    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 导入过程中发生错误: {e}")
        traceback.print_exc()
        return False

def test_genetic_algorithm():
    """测试遗传算法"""
    print("=" * 50)
    print("测试遗传算法...")
    
    try:
        from algorithms.genetic_algorithm import GeneticAlgorithm, Individual
        
        # 创建测试数据
        monitoring_data = pd.DataFrame({
            'station_id': ['S1', 'S2', 'S3'],
            'x': [100, 200, 150],
            'y': [100, 150, 200],
            'pm25': [50, 60, 55],
            'wind_speed': [3.5, 4.0, 3.8],
            'wind_direction': [45, 90, 60],
            'temperature': [25, 26, 24],
            'humidity': [60, 65, 62]
        })
        
        # 创建遗传算法实例
        ga = GeneticAlgorithm(
            monitoring_data=monitoring_data,
            population_size=20,
            generations=10,
            mutation_rate=0.1,
            crossover_rate=0.8
        )
        
        # 运行算法
        result = ga.run()
        
        if result is not None:
            print(f"✓ 遗传算法运行成功")
            print(f"  最优解: x={result.x:.2f}, y={result.y:.2f}, z={result.z:.2f}, q={result.q:.4f}")
            print(f"  适应度: {result.fitness:.6f}")
            return True
        else:
            print("✗ 遗传算法返回空结果")
            return False
            
    except Exception as e:
        print(f"✗ 遗传算法测试失败: {e}")
        traceback.print_exc()
        return False

def test_gaussian_plume():
    """测试高斯烟羽模型"""
    print("=" * 50)
    print("测试高斯烟羽模型...")
    
    try:
        from algorithms.gaussian_plume import GaussianPlumeModel
        
        # 创建模型实例
        model = GaussianPlumeModel()
        
        # 测试浓度计算
        concentration = model.calculate_concentration(
            x=100, y=50, z=0,
            source_x=0, source_y=0, source_z=10,
            emission_rate=1.0,
            wind_speed=5.0,
            wind_direction=0,
            stability_class='D'
        )
        
        if concentration >= 0:
            print(f"✓ 高斯烟羽模型运行成功")
            print(f"  计算浓度: {concentration:.6f} μg/m³")
            return True
        else:
            print("✗ 高斯烟羽模型返回负值")
            return False
            
    except Exception as e:
        print(f"✗ 高斯烟羽模型测试失败: {e}")
        traceback.print_exc()
        return False

def test_data_fusion():
    """测试数据融合"""
    print("=" * 50)
    print("测试数据融合...")
    
    try:
        from algorithms.data_fusion import DataFusionProcessor
        
        # 创建测试数据
        station1_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=24, freq='H'),
            'pm25': np.random.normal(50, 10, 24),
            'wind_speed': np.random.normal(3, 1, 24),
            'wind_direction': np.random.uniform(0, 360, 24),
            'temperature': np.random.normal(20, 5, 24),
            'humidity': np.random.normal(60, 10, 24)
        })
        
        station2_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=24, freq='H'),
            'pm25': np.random.normal(55, 8, 24),
            'wind_speed': np.random.normal(3.5, 1.2, 24),
            'wind_direction': np.random.uniform(0, 360, 24),
            'temperature': np.random.normal(22, 4, 24),
            'humidity': np.random.normal(65, 8, 24)
        })
        
        stations_data = {
            'station1': station1_data,
            'station2': station2_data
        }
        
        # 创建数据融合处理器
        processor = DataFusionProcessor()
        
        # 测试数据融合
        fused_data = processor.fuse_multi_station_data(stations_data)
        
        if len(fused_data) > 0:
            print(f"✓ 数据融合运行成功")
            print(f"  融合数据记录数: {len(fused_data)}")
            print(f"  融合数据列数: {len(fused_data.columns)}")
            return True
        else:
            print("✗ 数据融合返回空结果")
            return False
            
    except Exception as e:
        print(f"✗ 数据融合测试失败: {e}")
        traceback.print_exc()
        return False

def test_web_app():
    """测试Web应用"""
    print("=" * 50)
    print("测试Web应用...")
    
    try:
        from web.app import app
        
        # 测试应用创建
        if app is not None:
            print("✓ Flask应用创建成功")
            
            # 测试路由
            with app.test_client() as client:
                response = client.get('/')
                if response.status_code == 200:
                    print("✓ 主页路由测试成功")
                    return True
                else:
                    print(f"✗ 主页路由返回状态码: {response.status_code}")
                    return False
        else:
            print("✗ Flask应用创建失败")
            return False
            
    except Exception as e:
        print(f"✗ Web应用测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("污染源溯源系统 - Python 3.13 兼容性测试")
    print(f"Python版本: {sys.version}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行所有测试
    tests = [
        ("模块导入", test_imports),
        ("遗传算法", test_genetic_algorithm),
        ("高斯烟羽模型", test_gaussian_plume),
        ("数据融合", test_data_fusion),
        ("Web应用", test_web_app)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name}测试过程中发生异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果总结
    print("=" * 50)
    print("测试结果总结:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统可以正常运行。")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关模块。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)