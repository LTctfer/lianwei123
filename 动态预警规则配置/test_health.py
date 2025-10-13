#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试服务健康检查接口
"""

import requests
import time
from pprint import pprint

def test_health_check():
    BASE_URL = "http://localhost:8000"
    
    print("测试健康检查接口...")
    print("=" * 50)
    
    # 1. 检查服务健康状态
    print("\n1. 获取服务状态:")
    print("-" * 50)
    try:
        response = requests.get(f"{BASE_URL}/health")
        status_code = response.status_code
        data = response.json()
        
        print(f"HTTP状态码: {status_code}")
        print("\n响应数据:")
        pprint(data)
        
        # 分析响应
        if status_code == 200:
            print("\n✅ 服务运行正常")
            print(f"- 预警记录数: {data.get('alarm_count', 0)}")
            print(f"- 配置已加载: {data.get('config_loaded', False)}")
        elif status_code == 503:
            print("\n⚠️ 服务正在启动")
        else:
            print(f"\n❌ 未知状态码: {status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_health_check()
