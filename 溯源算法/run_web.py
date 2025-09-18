#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
污染源溯源系统Web应用启动脚本
"""

import os
import sys
import subprocess
import webbrowser
from threading import Timer

def check_dependencies():
    """检查依赖包是否安装"""
    required_packages = [
        'flask',
        'numpy',
        'pandas',
        'matplotlib',
        'scipy',
        'deap'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} 未安装")
    
    if missing_packages:
        print(f"\n缺少以下依赖包: {', '.join(missing_packages)}")
        print("请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def open_browser():
    """延迟打开浏览器"""
    webbrowser.open('http://localhost:5000')

def main():
    """主函数"""
    print("=" * 60)
    print("污染源溯源系统 Web 应用启动器")
    print("=" * 60)
    
    # 检查依赖
    print("\n1. 检查依赖包...")
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请先安装缺少的包")
        input("按回车键退出...")
        return
    
    print("\n✅ 所有依赖包已安装")
    
    # 检查文件
    print("\n2. 检查应用文件...")
    required_files = [
        'app.py',
        'pollution_source_tracker.py',
        'data_processor.py',
        'demo.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} 存在")
        else:
            print(f"❌ {file} 不存在")
            print(f"\n❌ 缺少必要文件: {file}")
            input("按回车键退出...")
            return
    
    print("\n✅ 所有必要文件存在")
    
    # 创建必要目录
    print("\n3. 创建必要目录...")
    directories = ['uploads', 'static/images', 'output']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ 创建目录: {directory}")
        else:
            print(f"✅ 目录已存在: {directory}")
    
    # 启动应用
    print("\n4. 启动Web应用...")
    print("应用将在 http://localhost:5000 启动")
    print("按 Ctrl+C 停止应用")
    
    # 延迟3秒后打开浏览器
    Timer(3.0, open_browser).start()
    
    try:
        # 导入并运行Flask应用
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n👋 应用已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        input("按回车键退出...")

if __name__ == '__main__':
    main()
