#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
吸附等温线数据处理API启动脚本
"""

import sys
import os
import subprocess

def check_dependencies():
    """检查依赖是否安装"""
    required_packages = [
        'flask', 'pandas', 'numpy', 'scipy', 'matplotlib'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少以下依赖包:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ 所有依赖包已安装")
    return True

def start_api_server():
    """启动API服务"""
    if not check_dependencies():
        return
    
    print("\n🚀 启动吸附等温线数据处理API服务...")
    print("📍 服务地址: http://localhost:5000")
    print("📚 API文档: http://localhost:5000/api/adsorption/info")
    print("💚 健康检查: http://localhost:5000/api/adsorption/health")
    print("🔄 数据处理: POST http://localhost:5000/api/adsorption/process")
    print("\n按 Ctrl+C 停止服务\n")
    
    try:
        # 导入并启动Flask应用
        from adsorption_api import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    start_api_server()
