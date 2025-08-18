#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
污染源溯源算法系统Web界面启动脚本
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'streamlit', 'numpy', 'pandas', 'matplotlib', 
        'seaborn', 'plotly', 'scipy', 'deap', 'tqdm'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("[错误] 缺少以下依赖包:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n请运行以下命令安装:")
        print("pip install -r requirements.txt")
        return False
    
    print("[完成] 所有依赖包已安装")
    return True

def start_web_interface():
    """启动Web界面"""
    
    print("网络 启动污染源溯源算法Web界面...")
    
    # 检查依赖
    if not check_dependencies():
        return False
    
    # 获取当前目录
    current_dir = Path(__file__).parent
    web_interface_path = current_dir / "web_interface.py"
    
    if not web_interface_path.exists():
        print(f"[错误] 找不到Web界面文件: {web_interface_path}")
        return False
    
    try:
        # 启动Streamlit
        print("启动 正在启动Streamlit服务器...")
        print("📱 Web界面将在浏览器中自动打开")
        print("🔗 如果没有自动打开，请访问: http://localhost:8501")
        print("⏹️  按 Ctrl+C 停止服务器")
        print("=" * 60)
        
        # 启动命令 - 修复网络访问问题
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(web_interface_path),
            "--server.port", "8501",
            "--server.address", "0.0.0.0",  # 改为0.0.0.0允许所有网络接口访问
            "--server.headless", "true",    # 无头模式，避免自动打开浏览器冲突
            "--browser.gatherUsageStats", "false",
            "--server.enableCORS", "false",  # 禁用CORS检查
            "--server.enableXsrfProtection", "false"  # 禁用XSRF保护（开发环境）
        ]
        
        # 启动进程
        process = subprocess.Popen(
            cmd, 
            cwd=current_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 等待服务器启动
        print("[等待] 等待服务器启动...")
        time.sleep(5)  # 增加等待时间

        # 检测服务器是否启动成功
        server_ready = False
        for i in range(10):  # 最多等待10秒
            try:
                import requests
                response = requests.get("http://localhost:8501", timeout=2)
                if response.status_code == 200:
                    server_ready = True
                    break
            except:
                pass
            time.sleep(1)
            print(f"[等待] 检测服务器状态... ({i+1}/10)")

        if server_ready:
            print("[完成] 服务器启动成功！")
            print("网络 访问地址:")
            print("   - 本地访问: http://localhost:8501")
            print("   - 网络访问: http://127.0.0.1:8501")

            # 尝试自动打开浏览器
            try:
                print("🔗 正在打开浏览器...")
                webbrowser.open("http://localhost:8501")
                print("[完成] 浏览器已打开")
            except Exception as e:
                print(f"[警告] 无法自动打开浏览器: {e}")
                print("📱 请手动复制以下地址到浏览器:")
                print("   http://localhost:8501")
        else:
            print("[错误] 服务器启动失败或无法访问")
            print("工具 请尝试以下解决方案:")
            print("   1. 检查端口8501是否被占用")
            print("   2. 检查防火墙设置")
            print("   3. 尝试使用其他端口")
            print("   4. 直接运行: streamlit run web_interface.py --server.port 8502")
        
        # 实时输出日志
        try:
            for line in process.stdout:
                print(line.strip())
        except KeyboardInterrupt:
            print("\n👋 正在停止服务器...")
            process.terminate()
            process.wait()
            print("[完成] 服务器已停止")
        
        return True
        
    except FileNotFoundError:
        print("[错误] 找不到Streamlit，请安装: pip install streamlit")
        return False
    except Exception as e:
        print(f"[错误] 启动失败: {e}")
        return False

def main():
    """主函数"""
    
    print("风暴 污染源溯源算法系统")
    print("=" * 40)
    
    try:
        success = start_web_interface()
        if not success:
            print("\n[错误] Web界面启动失败")
            print("请检查依赖包是否正确安装")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"\n[错误] 程序运行出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
