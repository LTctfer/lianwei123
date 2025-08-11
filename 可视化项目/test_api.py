#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
吸附等温线数据处理API测试脚本
"""

import requests
import json
from datetime import datetime, timedelta
import random

def generate_test_data(num_points=20):
    """生成测试数据 - 模拟真实的VOC监测数据"""
    base_time = datetime.now() - timedelta(hours=12)
    test_data = []
    
    # 模拟吸附效率逐渐下降的过程
    for i in range(num_points):
        current_time = base_time + timedelta(minutes=i * 30)  # 每30分钟一个数据点
        
        # 模拟进口浓度（相对稳定）
        inlet_voc = 100 + random.uniform(-5, 5)
        
        # 模拟出口浓度（随时间逐渐增加，表示穿透率上升）
        time_factor = i / num_points
        base_outlet = inlet_voc * (0.005 + time_factor * 0.15)  # 从0.5%穿透到15%穿透
        outlet_voc = max(0, base_outlet + random.uniform(-1, 1))
        
        # 风速数据
        wind_speed = 10 + random.uniform(-1, 1)
        
        # 添加进口数据点
        test_data.append({
            "gvocs": 0,  # 进口处出口VOC为0
            "invoc": inlet_voc,
            "gwindspeed": wind_speed,
            "access": 0,  # 进口
            "createTime": current_time.isoformat()
        })
        
        # 添加出口数据点（稍微延迟）
        outlet_time = current_time + timedelta(minutes=1)
        test_data.append({
            "gvocs": outlet_voc,
            "invoc": 0,  # 出口处进口VOC为0
            "gwindspeed": wind_speed,
            "access": 1,  # 出口
            "createTime": outlet_time.isoformat()
        })
    
    return test_data

def test_api(base_url="http://localhost:5000"):
    """测试API功能"""
    print("=== 抽取式吸附曲线预警系统API测试 ===\n")
    
    # 1. 健康检查
    print("1. 健康检查...")
    try:
        response = requests.get(f"{base_url}/api/extraction-adsorption-curve/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}\n")
    except Exception as e:
        print(f"健康检查失败: {e}\n")
        return
    
    # 2. API信息
    print("2. 获取API信息...")
    try:
        response = requests.get(f"{base_url}/api/extraction-adsorption-curve/info")
        print(f"状态码: {response.status_code}")
        api_info = response.json()
        print(f"API名称: {api_info['api_name']}")
        print(f"版本: {api_info['version']}")
        print(f"描述: {api_info['description']}\n")
    except Exception as e:
        print(f"获取API信息失败: {e}\n")
    
    # 3. 生成测试数据
    print("3. 生成测试数据...")
    test_data = generate_test_data(15)  # 生成15个时间点，共30个数据点
    print(f"生成了 {len(test_data)} 个数据点（{len(test_data)//2}个时间点的进出口数据）")
    print(f"数据时间范围: {test_data[0]['createTime']} 到 {test_data[-1]['createTime']}\n")
    
    # 4. 处理数据
    print("4. 处理抽取式吸附曲线数据...")
    try:
        response = requests.post(
            f"{base_url}/api/extraction-adsorption-curve/process",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ 数据处理成功!")
            print(f"\n📊 统计信息:")
            stats = result['statistics']
            print(f"  - 数据点数量: {stats['total_points']}")
            print(f"  - 平均效率: {stats['avg_efficiency']:.2f}%")
            print(f"  - 最低效率: {stats['min_efficiency']:.2f}%")
            print(f"  - 最高效率: {stats['max_efficiency']:.2f}%")
            print(f"  - 时间跨度: {stats['time_span_hours']:.2f} 小时")
            print(f"  - 效率趋势: {stats['efficiency_trend']}")
            
            print(f"\n📈 数据点信息:")
            data_points = result['data_points']
            print(f"  - 总数据点: {len(data_points)}")
            if data_points:
                print(f"  - 第一个点: x={data_points[0]['x']:.2f}h, y={data_points[0]['y']:.2f}%, 标签={data_points[0]['label']}")
                print(f"  - 最后一个点: x={data_points[-1]['x']:.2f}h, y={data_points[-1]['y']:.2f}%, 标签={data_points[-1]['label']}")
            
            print(f"\n⭐ 预警点信息（五角星标注点）:")
            warning_points = result['warning_points']
            print(f"  - 预警点数量: {len(warning_points)}")
            for i, wp in enumerate(warning_points):
                print(f"  - {wp['type']}: x={wp['x']:.2f}h, y={wp['y']:.2f}%")
                print(f"    描述: {wp['description']}")
            
            if 'model_info' in result and result['model_info'].get('model_fitted'):
                print(f"\n🔬 模型信息:")
                model = result['model_info']
                params = model['parameters']
                print(f"  - 模型拟合: 成功")
                print(f"  - 参数A: {params['A']:.4f}")
                print(f"  - 参数k: {params['k']:.4f}")
                print(f"  - 参数t0: {params['t0']:.2f}")
                if model.get('warning_time'):
                    print(f"  - 预警时间: {model['warning_time']:.2f} 小时")
                if model.get('predicted_saturation_time'):
                    print(f"  - 预计饱和时间: {model['predicted_saturation_time']:.2f} 小时")
            
        else:
            error_info = response.json()
            print(f"❌ 数据处理失败: {error_info.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    print("\n=== 测试完成 ===")

def test_error_cases(base_url="http://localhost:5000"):
    """测试错误情况"""
    print("\n=== 错误情况测试 ===\n")
    
    # 测试空数据
    print("1. 测试空数据...")
    try:
        response = requests.post(f"{base_url}/api/extraction-adsorption-curve/process", json=[])
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}\n")
    except Exception as e:
        print(f"测试失败: {e}\n")
    
    # 测试格式错误的数据
    print("2. 测试格式错误的数据...")
    try:
        bad_data = [{"invalid": "data"}]
        response = requests.post(f"{base_url}/api/extraction-adsorption-curve/process", json=bad_data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}\n")
    except Exception as e:
        print(f"测试失败: {e}\n")

if __name__ == "__main__":
    print("请确保API服务已启动 (python adsorption_api.py)")
    print("如果API在不同地址运行，请修改base_url参数\n")
    
    # 基础功能测试
    test_api()
    
    # 错误情况测试
    test_error_cases()
    
    print("\n💡 使用说明:")
    print("1. 启动API服务: python adsorption_api.py")
    print("2. 发送POST请求到: http://localhost:5000/api/extraction-adsorption-curve/process")
    print("3. 请求体格式:")
    print(json.dumps([{
        "gvocs": 0,
        "invoc": 100,
        "gwindspeed": 10,
        "access": 0,
        "createTime": "2024-01-01T10:00:00"
    }], indent=2))
