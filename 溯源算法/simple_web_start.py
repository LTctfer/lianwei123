#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版Web界面启动脚本
解决常见的网络访问问题
"""

import os
import sys
import subprocess
import time
import socket
from pathlib import Path

def check_port_available(port):
    """检查端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def find_available_port(start_port=8501):
    """找到可用端口"""
    for port in range(start_port, start_port + 10):
        if check_port_available(port):
            return port
    return None

def check_dependencies():
    """检查依赖"""
    try:
        import streamlit
        print("✅ Streamlit 已安装")
        return True
    except ImportError:
        print("❌ 缺少 Streamlit")
        print("正在安装 Streamlit...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
            print("✅ Streamlit 安装完成")
            return True
        except Exception as e:
            print(f"❌ Streamlit 安装失败: {e}")
            return False

def start_simple_web():
    """启动简化版Web界面"""
    
    print("🌐 启动污染源溯源算法Web界面（简化版）")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        return False
    
    # 检查Web界面文件
    current_dir = Path(__file__).parent
    web_file = current_dir / "web_interface.py"
    
    if not web_file.exists():
        print(f"❌ 找不到Web界面文件: {web_file}")
        return False
    
    # 找到可用端口
    port = find_available_port()
    if not port:
        print("❌ 找不到可用端口")
        return False
    
    print(f"🔌 使用端口: {port}")
    
    # 启动命令
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(web_file),
        "--server.port", str(port),
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    print("🚀 正在启动Web服务器...")
    print("📱 启动后请访问以下地址:")
    print(f"   - http://localhost:{port}")
    print(f"   - http://127.0.0.1:{port}")
    print("⏹️  按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    try:
        # 启动服务器
        process = subprocess.Popen(cmd, cwd=current_dir)
        
        # 等待启动
        print("⏳ 等待服务器启动...")
        time.sleep(3)
        
        print("✅ 服务器已启动！")
        print(f"🌐 请在浏览器中访问: http://localhost:{port}")
        
        # 等待用户中断
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n👋 正在停止服务器...")
            process.terminate()
            process.wait()
            print("✅ 服务器已停止")
        
        return True
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False

def main():
    """主函数"""
    
    print("🌪️ 污染源溯源算法系统 - 简化Web启动器")
    print()
    
    try:
        success = start_simple_web()
        if not success:
            print("\n❌ Web界面启动失败")
            print("\n🔧 故障排除建议:")
            print("1. 检查Python环境是否正确")
            print("2. 确保所有依赖包已安装: pip install streamlit")
            print("3. 检查防火墙是否阻止了端口访问")
            print("4. 尝试手动运行: streamlit run web_interface.py")
            print("5. 如果仍有问题，请使用命令行版本: python enhanced_demo.py")
            
    except KeyboardInterrupt:
        print("\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")

if __name__ == "__main__":
    main()
