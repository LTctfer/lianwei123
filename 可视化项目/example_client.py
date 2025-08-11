#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
吸附曲线预警系统 HTTP API 客户端示例
演示如何调用HTTP接口进行数据分析
"""

import requests
import json
import os
from typing import Dict, Any

class AdsorptionAPIClient:
    """吸附曲线预警系统API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        初始化API客户端
        
        Args:
            base_url: API服务器地址
        """
        self.base_url = base_url.rstrip('/')
        
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            response = requests.get(f"{self.base_url}/api/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_api_info(self) -> Dict[str, Any]:
        """获取API信息"""
        try:
            response = requests.get(f"{self.base_url}/")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_warning_upload(self, file_path: str) -> Dict[str, Any]:
        """
        通过文件上传进行预警系统分析
        
        Args:
            file_path: 本地文件路径
            
        Returns:
            分析结果字典
        """
        try:
            if not os.path.exists(file_path):
                return {"error": f"文件不存在: {file_path}"}
            
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                response = requests.post(f"{self.base_url}/api/analyze/warning", files=files)
                
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_complete_upload(self, file_path: str) -> Dict[str, Any]:
        """
        通过文件上传进行完整数据分析
        
        Args:
            file_path: 本地文件路径
            
        Returns:
            分析结果字典
        """
        try:
            if not os.path.exists(file_path):
                return {"error": f"文件不存在: {file_path}"}
            
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                response = requests.post(f"{self.base_url}/api/analyze/complete", files=files)
                
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_file_path(self, file_path: str, analysis_type: str = "warning") -> Dict[str, Any]:
        """
        通过文件路径进行分析（服务器端文件）
        
        Args:
            file_path: 服务器端文件路径
            analysis_type: 分析类型 ("warning" 或 "complete")
            
        Returns:
            分析结果字典
        """
        try:
            data = {
                "file_path": file_path,
                "analysis_type": analysis_type
            }
            
            response = requests.post(
                f"{self.base_url}/api/analyze/file",
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}

def print_analysis_result(result: Dict[str, Any], analysis_type: str = "warning"):
    """打印分析结果"""
    if not result.get('success', False):
        print(f"❌ 分析失败: {result.get('error', '未知错误')}")
        return
    
    print("✅ 分析成功!")
    print(f"📊 分析类型: {analysis_type}")
    print(f"⏰ 处理时间: {result.get('timestamp', 'N/A')}")
    
    if analysis_type == "warning":
        # 预警系统分析结果
        data_points = result.get('data_points', [])
        warning_point = result.get('warning_point', {})
        statistics = result.get('statistics', {})
        
        print(f"\n📈 数据点信息:")
        print(f"  总数据点: {len(data_points)}")
        if data_points:
            print("  前3个数据点:")
            for i, point in enumerate(data_points[:3]):
                print(f"    {i+1}. t={point['x']:.2f}h, 穿透率={point['y']:.1f}%")
                print(f"       {point['label']}")
        
        print(f"\n⚠️ 预警点信息:")
        if warning_point.get('breakthrough_rate') is not None:
            print(f"  预警时间: {warning_point['time']:.2f}h")
            print(f"  预警穿透率: {warning_point['breakthrough_rate']:.1f}%")
            print(f"  描述: {warning_point['description']}")
        else:
            print("  无预警点")
        
        print(f"\n📊 统计信息:")
        print(f"  数据点总数: {statistics.get('total_data_points', 0)}")
        print(f"  是否有预警点: {statistics.get('has_warning_point', False)}")
        if statistics.get('time_range'):
            tr = statistics['time_range']
            print(f"  时间范围: {tr.get('min', 0):.2f}h - {tr.get('max', 0):.2f}h")
        
    elif analysis_type == "complete":
        # 完整数据分析结果
        all_data_points = result.get('all_data_points', [])
        warning_points = result.get('warning_points', [])
        data_summary = result.get('data_summary', {})
        
        print(f"\n📈 数据点信息:")
        print(f"  总数据点: {len(all_data_points)}")
        print(f"  预警点数: {len(warning_points)}")
        
        print(f"\n📋 数据摘要:")
        print(f"  总点数: {data_summary.get('total_points', 0)}")
        print(f"  预警数量: {data_summary.get('warning_count', 0)}")
        print(f"  数据类型: {data_summary.get('data_types', [])}")

def main():
    """示例用法"""
    print("=== 吸附曲线预警系统 HTTP API 客户端示例 ===\n")
    
    # 创建客户端
    client = AdsorptionAPIClient("http://localhost:5000")
    
    # 1. 健康检查
    print("1. 健康检查:")
    health = client.health_check()
    print(f"   状态: {health.get('status', 'unknown')}")
    print(f"   时间: {health.get('timestamp', 'N/A')}")
    
    # 2. 获取API信息
    print("\n2. API信息:")
    api_info = client.get_api_info()
    if 'message' in api_info:
        print(f"   服务: {api_info['message']}")
        print(f"   版本: {api_info.get('version', 'N/A')}")
        print(f"   支持格式: {api_info.get('supported_formats', [])}")
    
    # 3. 示例文件分析（需要先启动API服务）
    test_file = "可视化项目/7.24.csv"
    if os.path.exists(test_file):
        print(f"\n3. 预警系统分析示例 (文件上传):")
        result = client.analyze_warning_upload(test_file)
        print_analysis_result(result, "warning")
        
        print(f"\n4. 完整数据分析示例 (文件上传):")
        result = client.analyze_complete_upload(test_file)
        print_analysis_result(result, "complete")
        
        print(f"\n5. 文件路径分析示例 (服务器端文件):")
        result = client.analyze_file_path(test_file, "warning")
        print_analysis_result(result, "warning")
    else:
        print(f"\n⚠️ 测试文件不存在: {test_file}")
        print("   请确保有可用的测试数据文件")
    
    print("\n=== 示例完成 ===")
    print("💡 使用说明:")
    print("   1. 先运行 python adsorption_http_api.py 启动API服务")
    print("   2. 再运行此客户端示例进行测试")
    print("   3. 或直接使用curl/Postman等工具调用接口")

if __name__ == "__main__":
    main()
