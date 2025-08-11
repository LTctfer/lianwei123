#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试抽取式吸附曲线预警系统API
"""

import requests
import json
from datetime import datetime, timedelta
import pandas as pd

def generate_test_data():
    """生成测试用的JSON数据"""
    # 模拟24小时的数据，每30分钟一个数据点
    base_time = datetime.now()
    test_data = []
    
    # 模拟穿透率逐渐增加的情况
    for i in range(48):  # 48个数据点，每30分钟一个
        time_offset = timedelta(minutes=30 * i)
        current_time = base_time + time_offset
        
        # 模拟穿透率从5%逐渐增加到85%
        breakthrough_ratio = 0.05 + (i / 47) * 0.80  # 从5%到85%
        
        # 模拟进口浓度在100-200之间波动
        inlet_conc = 150 + (i % 10 - 5) * 5
        
        # 根据穿透率计算出口浓度
        outlet_conc = inlet_conc * breakthrough_ratio
        
        # 模拟风速在0.5-2.0之间
        wind_speed = 1.0 + (i % 8) * 0.2
        
        # access值：前24个点为2（同时记录），后24个点交替0和1（切换记录）
        if i < 24:
            access = 2
        else:
            access = i % 2
        
        test_data.append({
            "gVocs": round(outlet_conc, 2),
            "inVoc": round(inlet_conc, 2),
            "gWindspeed": round(wind_speed, 2),
            "access": access,
            "createTime": current_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return test_data

def test_api():
    """测试API接口"""
    # 生成测试数据
    test_data = generate_test_data()
    
    print("=== 抽取式吸附曲线预警系统API测试 ===")
    print(f"生成测试数据: {len(test_data)} 个数据点")
    print(f"数据时间范围: {test_data[0]['createTime']} 到 {test_data[-1]['createTime']}")
    print(f"进口浓度范围: {min(d['inVoc'] for d in test_data):.1f} - {max(d['inVoc'] for d in test_data):.1f}")
    print(f"出口浓度范围: {min(d['gVocs'] for d in test_data):.1f} - {max(d['gVocs'] for d in test_data):.1f}")
    
    # API地址
    api_url = "http://localhost:5000/api/extraction-adsorption-curve/process"
    
    try:
        # 发送请求
        print("\n正在调用API...")
        response = requests.post(api_url, json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                print("✅ API调用成功!")
                
                # 显示数据点信息
                data_points = result.get("data_points", [])
                print(f"\n📊 数据点信息:")
                print(f"   总数据点数: {len(data_points)}")
                
                if data_points:
                    print(f"   时间范围: {min(p['x'] for p in data_points):.2f}h - {max(p['x'] for p in data_points):.2f}h")
                    print(f"   穿透率范围: {min(p['y'] for p in data_points):.1f}% - {max(p['y'] for p in data_points):.1f}%")
                    
                    # 显示前3个数据点的详细信息
                    print(f"\n前3个数据点详情:")
                    for i, point in enumerate(data_points[:3]):
                        print(f"   数据点 {i+1}:")
                        print(f"     X轴(累计时间): {point['x']:.2f}小时")
                        print(f"     Y轴(穿透率): {point['y']:.1f}%")
                        print(f"     标签: {point['label'].replace(chr(10), ', ')}")
                        print(f"     时间段: {point['time_segment']}")
                        print(f"     计算规则: {point.get('calculation_rule', 'N/A')}")
                
                # 显示预警点信息
                warning_points = result.get("warning_points", [])
                print(f"\n⚠️  预警点信息:")
                print(f"   预警点数量: {len(warning_points)}")
                
                if warning_points:
                    for i, point in enumerate(warning_points):
                        print(f"   预警点 {i+1}:")
                        print(f"     X轴(累计时间): {point['x']:.2f}小时")
                        print(f"     Y轴(穿透率): {point['y']:.1f}%")
                        print(f"     类型: {point['type']}")
                        print(f"     颜色: {point['color']}")
                        print(f"     描述: {point['description']}")
                else:
                    print("   无预警点（可能模型未拟合成功）")
                
                # 保存结果到文件
                with open("可视化项目/api_test_result.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\n💾 结果已保存到: api_test_result.json")
                
            else:
                print("❌ API返回错误:")
                print(f"   错误信息: {result.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            print(f"   响应内容: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 请确保API服务器正在运行")
        print("   启动命令: python adsorption_api.py")
    except requests.exceptions.Timeout:
        print("❌ 请求超时: API处理时间过长")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_health_check():
    """测试健康检查接口"""
    try:
        response = requests.get("http://localhost:5000/api/extraction-adsorption-curve/health")
        if response.status_code == 200:
            result = response.json()
            print("✅ 健康检查通过:")
            print(f"   状态: {result.get('status')}")
            print(f"   服务: {result.get('service')}")
            print(f"   版本: {result.get('version')}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except:
        print("❌ 无法连接到API服务器")

if __name__ == "__main__":
    print("开始测试...")
    
    # 健康检查
    print("\n1. 健康检查:")
    test_health_check()
    
    # API功能测试
    print("\n2. API功能测试:")
    test_api()
    
    print("\n测试完成!")
