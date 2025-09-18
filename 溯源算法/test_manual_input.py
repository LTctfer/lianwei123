#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试手动输入功能
"""

import requests
import json

def test_manual_input():
    """测试手动输入数据处理"""
    
    # 准备测试数据
    test_data = {
        "data_source": "manual",
        "meteorological_data": {
            "wind_speed": 2.5,
            "wind_direction": 60.0,
            "temperature": 25.0,
            "pressure": 1013.25,
            "humidity": 65.0,
            "solar_radiation": 500.0,
            "cloud_cover": 0.5
        },
        "monitoring_data": [
            {
                "station_id": "测试站1",
                "x": 100.0,
                "y": 50.0,
                "z": 10.0,
                "concentration": 20.5
            },
            {
                "station_id": "测试站2",
                "x": -50.0,
                "y": 80.0,
                "z": 15.0,
                "concentration": 15.2
            },
            {
                "station_id": "测试站3",
                "x": 200.0,
                "y": -30.0,
                "z": 12.0,
                "concentration": 8.7
            }
        ]
    }
    
    print("测试手动输入数据处理...")
    print("发送数据:", json.dumps(test_data, indent=2, ensure_ascii=False))
    
    try:
        # 发送POST请求
        response = requests.post(
            'http://127.0.0.1:5000/process',
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("响应数据:", json.dumps(result, indent=2, ensure_ascii=False))
            
            if result.get('status') == 'success':
                print("\n✅ 手动输入测试成功！")
                source_result = result.get('source_result', {})
                print(f"污染源位置: X={source_result.get('x', 'N/A'):.2f}, Y={source_result.get('y', 'N/A'):.2f}")
                print(f"排放强度: {source_result.get('emission_rate', 'N/A'):.2f} g/s")
                print(f"置信度: {source_result.get('confidence', 'N/A'):.4f}")
            else:
                print(f"❌ 处理失败: {result.get('message', '未知错误')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print("响应内容:", response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")

def test_invalid_data():
    """测试无效数据处理"""
    
    print("\n" + "="*50)
    print("测试无效数据处理...")
    
    # 测试缺少必需字段
    invalid_data = {
        "data_source": "manual",
        "meteorological_data": {
            "wind_speed": 2.5,
            # 缺少其他字段
        },
        "monitoring_data": []  # 空的监测站数据
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:5000/process',
            json=invalid_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        result = response.json()
        print("无效数据测试结果:", json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('status') == 'error':
            print("✅ 无效数据正确被拒绝")
        else:
            print("❌ 无效数据未被正确处理")
            
    except Exception as e:
        print(f"❌ 无效数据测试异常: {e}")

if __name__ == '__main__':
    print("开始测试手动输入功能...")
    test_manual_input()
    test_invalid_data()
    print("\n测试完成！")
