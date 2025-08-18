#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web界面故障诊断脚本
帮助用户诊断和解决Web界面访问问题
"""

import os
import sys
import socket
import subprocess
import platform
from pathlib import Path

def print_banner():
    """打印横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    Web界面故障诊断工具                        ║
    ║                                                              ║
    ║  🔍 系统检查  🌐 网络诊断  🔧 问题修复  📋 解决方案          ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_environment():
    """检查Python环境"""
    print("🐍 检查Python环境...")
    
    # Python版本
    version = sys.version_info
    print(f"   Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("   ❌ Python版本过低，建议使用Python 3.7+")
        return False
    else:
        print("   ✅ Python版本符合要求")
    
    # 检查pip
    try:
        import pip
        print("   ✅ pip 可用")
    except ImportError:
        print("   ❌ pip 不可用")
        return False
    
    return True

def check_dependencies():
    """检查依赖包"""
    print("\n📦 检查依赖包...")
    
    required_packages = {
        'streamlit': 'Web界面框架',
        'numpy': '数值计算',
        'pandas': '数据处理',
        'matplotlib': '绘图库',
        'plotly': '交互式图表'
    }
    
    missing_packages = []
    
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"   ✅ {package} - {description}")
        except ImportError:
            print(f"   ❌ {package} - {description} (缺失)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n   缺少 {len(missing_packages)} 个依赖包")
        return False, missing_packages
    else:
        print("   ✅ 所有依赖包已安装")
        return True, []

def check_network():
    """检查网络配置"""
    print("\n🌐 检查网络配置...")
    
    # 检查端口可用性
    ports_to_check = [8501, 8502, 8503, 8504, 8505]
    available_ports = []
    
    for port in ports_to_check:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                available_ports.append(port)
                print(f"   ✅ 端口 {port} 可用")
        except OSError:
            print(f"   ❌ 端口 {port} 被占用")
    
    if not available_ports:
        print("   ❌ 没有可用端口")
        return False, []
    
    # 检查localhost解析
    try:
        socket.gethostbyname('localhost')
        print("   ✅ localhost 解析正常")
    except socket.gaierror:
        print("   ❌ localhost 解析失败")
        return False, available_ports
    
    return True, available_ports

def check_firewall():
    """检查防火墙设置"""
    print("\n🔥 检查防火墙设置...")
    
    system = platform.system()
    
    if system == "Windows":
        print("   💡 Windows防火墙检查:")
        print("      1. 打开 Windows Defender 防火墙")
        print("      2. 点击 '允许应用或功能通过Windows Defender防火墙'")
        print("      3. 确保Python.exe被允许通过防火墙")
        
    elif system == "Darwin":  # macOS
        print("   💡 macOS防火墙检查:")
        print("      1. 系统偏好设置 > 安全性与隐私 > 防火墙")
        print("      2. 确保防火墙未阻止Python")
        
    elif system == "Linux":
        print("   💡 Linux防火墙检查:")
        print("      1. 检查iptables: sudo iptables -L")
        print("      2. 检查ufw: sudo ufw status")
        
    print("   ⚠️ 如果防火墙阻止访问，请添加Python到允许列表")

def check_files():
    """检查文件完整性"""
    print("\n📁 检查文件完整性...")
    
    current_dir = Path(__file__).parent
    required_files = [
        'web_interface.py',
        'enhanced_pollution_tracing.py',
        'gaussian_plume_model.py',
        'optimized_source_inversion.py'
    ]
    
    missing_files = []
    
    for file_name in required_files:
        file_path = current_dir / file_name
        if file_path.exists():
            print(f"   ✅ {file_name}")
        else:
            print(f"   ❌ {file_name} (缺失)")
            missing_files.append(file_name)
    
    if missing_files:
        print(f"   缺少 {len(missing_files)} 个必需文件")
        return False, missing_files
    else:
        print("   ✅ 所有必需文件存在")
        return True, []

def provide_solutions(issues):
    """提供解决方案"""
    print("\n🔧 解决方案建议:")
    
    if 'python' in issues:
        print("\n📍 Python环境问题:")
        print("   1. 升级Python到3.7+版本")
        print("   2. 重新安装Python并确保pip可用")
    
    if 'dependencies' in issues:
        print("\n📍 依赖包问题:")
        print("   1. 运行: pip install -r requirements.txt")
        print("   2. 或手动安装: pip install streamlit numpy pandas matplotlib plotly")
        print("   3. 如果网络问题，使用国内镜像:")
        print("      pip install -i https://pypi.tuna.tsinghua.edu.cn/simple streamlit")
    
    if 'network' in issues:
        print("\n📍 网络端口问题:")
        print("   1. 关闭占用端口的程序")
        print("   2. 使用其他端口: streamlit run web_interface.py --server.port 8502")
        print("   3. 检查是否有其他Streamlit实例在运行")
    
    if 'firewall' in issues:
        print("\n📍 防火墙问题:")
        print("   1. 临时关闭防火墙测试")
        print("   2. 添加Python到防火墙允许列表")
        print("   3. 使用127.0.0.1而不是localhost")
    
    if 'files' in issues:
        print("\n📍 文件缺失问题:")
        print("   1. 重新下载完整的项目文件")
        print("   2. 检查文件是否被杀毒软件误删")
        print("   3. 确保在正确的目录中运行")

def run_quick_test():
    """运行快速测试"""
    print("\n🧪 运行快速测试...")
    
    try:
        # 测试Streamlit导入
        import streamlit as st
        print("   ✅ Streamlit导入成功")
        
        # 测试端口绑定
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 8501))
            print("   ✅ 端口8501绑定成功")
        
        # 测试文件访问
        current_dir = Path(__file__).parent
        web_file = current_dir / "web_interface.py"
        if web_file.exists():
            print("   ✅ Web界面文件可访问")
        else:
            print("   ❌ Web界面文件不存在")
            return False
        
        print("   ✅ 快速测试通过")
        return True
        
    except Exception as e:
        print(f"   ❌ 快速测试失败: {e}")
        return False

def main():
    """主函数"""
    
    print_banner()
    
    issues = []
    
    # 检查Python环境
    if not check_python_environment():
        issues.append('python')
    
    # 检查依赖包
    deps_ok, missing_deps = check_dependencies()
    if not deps_ok:
        issues.append('dependencies')
    
    # 检查网络
    network_ok, available_ports = check_network()
    if not network_ok:
        issues.append('network')
    
    # 检查防火墙
    check_firewall()
    
    # 检查文件
    files_ok, missing_files = check_files()
    if not files_ok:
        issues.append('files')
    
    # 运行快速测试
    if not issues:  # 只有在没有明显问题时才运行测试
        test_ok = run_quick_test()
        if not test_ok:
            issues.append('runtime')
    
    # 总结
    print("\n" + "="*60)
    if not issues:
        print("🎉 诊断完成：未发现明显问题")
        print("💡 如果仍无法访问Web界面，请尝试:")
        print("   1. 运行: python simple_web_start.py")
        print("   2. 或使用命令行版本: python enhanced_demo.py")
    else:
        print(f"🔍 诊断完成：发现 {len(issues)} 个问题")
        provide_solutions(issues)
    
    print("\n📞 如需更多帮助，请查看 README_增强版.md 文档")

if __name__ == "__main__":
    main()
