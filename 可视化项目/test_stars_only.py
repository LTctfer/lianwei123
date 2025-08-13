#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修改后的预警系统接口（仅返回五角星预警点）
"""

import requests
import json
import numpy as np

def test_stars_only_api():
    """测试仅返回五角星预警点的API"""
    
    print("🧪 测试预警系统接口（仅五角星预警点）")
    print("=" * 50)
    
    # API地址
    api_url = "http://localhost:5001/api/warning-prediction/analyze"
    
    # 1. 检查服务状态
    try:
        health_response = requests.get("http://localhost:5001/api/warning-prediction/health")
        if health_response.status_code == 200:
            print("✅ API服务运行正常")
        else:
            print("❌ API服务异常")
            return
    except Exception as e:
        print(f"❌ 无法连接API服务: {e}")
        print("💡 请先启动API服务: python warning_prediction_api.py")
        return
    
    # 2. 准备测试数据（S型曲线）
    print("\n📊 准备S型穿透曲线测试数据...")
    
    # 生成典型的S型曲线数据
    time_hours = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
    # 模拟真实的S型穿透曲线
    breakthrough_percent = [5.2, 12.8, 25.6, 42.3, 58.7, 72.4, 83.1, 89.6, 93.2]
    
    data_points = []
    for time_h, bt_pct in zip(time_hours, breakthrough_percent):
        data_points.append({
            "x": time_h,
            "y": bt_pct
        })
    
    print(f"   生成 {len(data_points)} 个数据点")
    print(f"   时间范围: {time_hours[0]}h - {time_hours[-1]}h")
    print(f"   穿透率范围: {breakthrough_percent[0]:.1f}% - {breakthrough_percent[-1]:.1f}%")
    
    # 3. 发送分析请求
    print(f"\n🚀 发送预警分析请求...")
    
    request_data = {
        "session_id": "test_stars_only",
        "data_points": data_points
    }
    
    try:
        response = requests.post(
            api_url,
            json=request_data,
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 预警分析成功")
            
            # 检查返回的预警点
            warning_points = result.get('warning_points', [])
            print(f"\n⭐ 预警点分析结果 ({len(warning_points)} 个五角星标记):")
            print("-" * 50)
            
            orange_star_found = False
            red_star_found = False
            
            for point in warning_points:
                print(f"🌟 {point['name']}")
                print(f"   坐标: X={point['x']}小时, Y={point['y']}%")
                print(f"   类型: {point['type']}")
                print(f"   颜色: {point['color']}")
                print(f"   标记: {point['symbol']}")
                print(f"   说明: {point['description']}")
                print()
                
                # 检查预警点类型
                if point['type'] == 'warning_star' and point['color'] == 'orange':
                    orange_star_found = True
                    print(f"   🟠 橙色预警点已找到: {point['x']}h处达到{point['y']}%穿透率")
                
                elif point['type'] == 'saturation_star' and point['color'] == 'red':
                    red_star_found = True
                    print(f"   🔴 红色饱和点已找到: {point['x']}h处预计达到{point['y']}%穿透率")
            
            # 验证结果
            print("\n🔍 结果验证:")
            if orange_star_found:
                print("   ✅ 橙色五角星预警点正确返回")
            else:
                print("   ❌ 缺少橙色五角星预警点")
            
            if red_star_found:
                print("   ✅ 红色五角星饱和点正确返回")
            else:
                print("   ❌ 缺少红色五角星饱和点")
            
            # 检查是否只返回五角星标记
            only_stars = all(point['symbol'] == 'star' for point in warning_points)
            if only_stars:
                print("   ✅ 确认仅返回五角星标记的预警点")
            else:
                print("   ⚠️ 返回了非五角星标记的点")
            
            # 显示模型信息
            model_info = result.get('model_info', {})
            if model_info.get('fitted'):
                print("\n📈 模型拟合信息:")
                params = model_info.get('parameters', {})
                metrics = model_info.get('quality_metrics', {})
                print(f"   拟合质量: R²={metrics.get('r_squared', 0):.3f}")
                print(f"   模型参数: A={params.get('A', 0):.3f}")
                
                r_squared = metrics.get('r_squared', 0)
                if r_squared > 0.9:
                    print("   ✅ 模型拟合优秀")
                elif r_squared > 0.8:
                    print("   ✅ 模型拟合良好")
                else:
                    print("   ⚠️ 模型拟合一般")
            
        else:
            print(f"❌ 预警分析失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 预警分析异常: {e}")

def test_different_data_formats():
    """测试不同数据格式的兼容性"""
    print("\n🧪 测试数据格式兼容性...")
    
    api_url = "http://localhost:5001/api/warning-prediction/analyze"
    
    # 测试中文字段格式
    test_data = {
        "session_id": "format_test",
        "data_points": [
            {"cumulative_time": 1.0, "穿透率": 8.0},
            {"cumulative_time": 2.0, "穿透率": 18.0},
            {"cumulative_time": 3.0, "穿透率": 32.0},
            {"cumulative_time": 4.0, "穿透率": 58.0},
            {"cumulative_time": 5.0, "穿透率": 78.0},
            {"cumulative_time": 6.0, "穿透率": 88.0}
        ]
    }
    
    try:
        response = requests.post(api_url, json=test_data)
        if response.status_code == 200:
            result = response.json()
            warning_count = len(result.get('warning_points', []))
            print(f"   ✅ 中文字段格式兼容，生成 {warning_count} 个五角星预警点")
        else:
            print(f"   ❌ 中文字段格式不兼容: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 格式测试异常: {e}")

def test_api_info():
    """测试API信息接口"""
    print("\n📖 测试API信息接口...")
    
    try:
        info_response = requests.get("http://localhost:5001/api/warning-prediction/info")
        if info_response.status_code == 200:
            info_data = info_response.json()
            print("✅ API信息获取成功")
            
            # 检查算法信息
            algo_info = info_data.get('algorithm_info', {})
            warning_types = algo_info.get('warning_types', [])
            note = algo_info.get('note', '')
            
            print(f"   预警类型: {warning_types}")
            print(f"   说明: {note}")
            
            if '仅返回五角星标记' in note:
                print("   ✅ API文档正确说明仅返回五角星预警点")
            else:
                print("   ⚠️ API文档说明可能需要更新")
                
        else:
            print(f"❌ API信息获取失败: {info_response.status_code}")
            
    except Exception as e:
        print(f"❌ API信息查询异常: {e}")

def main():
    """主测试函数"""
    print("🚀 预警系统接口测试（仅五角星版本）")
    print("⚠️ 请确保API服务已启动: python warning_prediction_api.py")
    print()
    
    # 执行主要功能测试
    test_stars_only_api()
    
    # 执行格式兼容性测试
    test_different_data_formats()
    
    # 测试API信息
    test_api_info()
    
    print("\n" + "=" * 50)
    print("🎯 测试完成！")
    print("📋 验证要点:")
    print("  ✅ 仅返回五角星标记的预警点（橙色、红色）")
    print("  ✅ 不再返回穿透起始点等其他标记")
    print("  ✅ 预警点坐标准确可用于前端绘制")
    print("  ✅ 支持多种数据字段格式")

if __name__ == "__main__":
    main()
