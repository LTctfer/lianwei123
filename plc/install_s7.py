#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
西门子S7协议环境安装脚本
自动安装snap7库和相关依赖
"""

import subprocess
import sys
import os
import platform
import urllib.request
import zipfile
import shutil

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 6):
        print("❌ 需要Python 3.6或更高版本")
        return False
    
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True

def install_python_snap7():
    """安装python-snap7库"""
    try:
        print("📦 安装python-snap7库...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-snap7"])
        print("✅ python-snap7安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ python-snap7安装失败: {e}")
        return False

def download_snap7_library():
    """下载snap7动态库"""
    system = platform.system().lower()
    architecture = platform.architecture()[0]
    
    print(f"🖥️ 检测到系统: {system} {architecture}")
    
    if system == "windows":
        if architecture == "64bit":
            lib_url = "https://github.com/gijzelaerr/python-snap7/raw/master/snap7/lib/snap7.dll"
            lib_name = "snap7.dll"
        else:
            print("❌ 不支持32位Windows系统")
            return False
    elif system == "linux":
        if architecture == "64bit":
            lib_url = "https://github.com/gijzelaerr/python-snap7/raw/master/snap7/lib/libsnap7.so"
            lib_name = "libsnap7.so"
        else:
            print("❌ 不支持32位Linux系统")
            return False
    else:
        print(f"❌ 不支持的操作系统: {system}")
        return False
    
    try:
        print(f"📥 下载snap7库文件: {lib_name}")
        
        # 创建lib目录
        lib_dir = os.path.join(os.path.dirname(__file__), "lib")
        os.makedirs(lib_dir, exist_ok=True)
        
        # 下载库文件
        lib_path = os.path.join(lib_dir, lib_name)
        urllib.request.urlretrieve(lib_url, lib_path)
        
        print(f"✅ snap7库文件下载成功: {lib_path}")
        
        # 设置环境变量
        if system == "windows":
            # Windows系统，将库文件复制到系统目录或当前目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            shutil.copy2(lib_path, current_dir)
            print(f"📁 库文件已复制到: {current_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ 下载snap7库失败: {e}")
        print("请手动下载snap7库文件:")
        print(f"  URL: {lib_url}")
        print(f"  保存到: {lib_path}")
        return False

def test_snap7_installation():
    """测试snap7安装"""
    try:
        print("🧪 测试snap7安装...")
        import snap7
        
        # 创建客户端测试
        client = snap7.client.Client()
        print("✅ snap7库导入成功")
        
        # 显示版本信息
        print(f"📋 snap7版本: {snap7.__version__}")
        
        return True
        
    except ImportError as e:
        print(f"❌ snap7导入失败: {e}")
        return False
    except Exception as e:
        print(f"⚠️ snap7测试异常: {e}")
        return True  # 导入成功就算通过

def create_s7_config():
    """创建S7配置文件"""
    config_content = """{
  "s7_settings": {
    "ip": "192.168.0.1",
    "rack": 0,
    "slot": 1,
    "timeout": 5.0,
    "description": "西门子S7 PLC配置"
  },
  "plc_info": {
    "supported_models": [
      "S7-200",
      "S7-300", 
      "S7-400",
      "S7-1200",
      "S7-1500",
      "LOGO! 0BA7/0BA8"
    ],
    "communication_requirements": [
      "启用PUT/GET通信",
      "设置正确的IP地址",
      "确保防火墙允许S7通信",
      "检查机架号和插槽号"
    ]
  },
  "address_examples": {
    "digital_outputs": "%Q0.0, %Q0.1, %QB0",
    "digital_inputs": "%I0.0, %I0.1, %IB0", 
    "memory_bits": "%M0.0, %M1.1, %MB0",
    "memory_words": "%MW100, %MD200",
    "data_blocks": "%DB1.DBX0.0, %DB1.DBB0, %DB1.DBW0, %DB1.DBD0"
  }
}"""
    
    try:
        config_file = os.path.join(os.path.dirname(__file__), "s7_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✅ S7配置文件已创建: {config_file}")
        return True
        
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")
        return False

def show_usage_instructions():
    """显示使用说明"""
    print("\n" + "="*60)
    print("🎉 西门子S7协议环境安装完成!")
    print("="*60)
    
    print("\n📋 使用方法:")
    print("  python s7_plc_reader.py")
    
    print("\n⚙️ PLC配置要求:")
    print("  1. 启用PUT/GET通信")
    print("  2. 设置正确的IP地址 (默认: 192.168.0.1)")
    print("  3. 确认机架号和插槽号 (默认: Rack=0, Slot=1)")
    print("  4. 确保防火墙允许S7通信")
    
    print("\n🔧 常见PLC配置:")
    print("  S7-300/400: Rack=0, Slot=2")
    print("  S7-1200/1500: Rack=0, Slot=1") 
    print("  S7-200: 使用以太网模块")
    
    print("\n📊 支持的地址格式:")
    print("  数字量输出: %Q0.0, %Q0.1, %QB0")
    print("  数字量输入: %I0.0, %I0.1, %IB0")
    print("  标志位: %M0.0, %M1.1, %MB0")
    print("  标志字: %MW100, %MD200")
    print("  数据块: %DB1.DBX0.0, %DB1.DBW0")
    
    print("\n🚨 故障排除:")
    print("  如果连接失败，请检查:")
    print("  - PLC IP地址和网络连通性")
    print("  - PUT/GET通信是否启用")
    print("  - 机架号和插槽号是否正确")
    print("  - Windows防火墙设置")

def main():
    """主函数"""
    print("🏭 西门子S7协议环境安装程序")
    print("="*50)
    
    # 检查Python版本
    if not check_python_version():
        return False
    
    success = True
    
    # 安装python-snap7
    if not install_python_snap7():
        success = False
    
    # 下载snap7库文件
    if not download_snap7_library():
        success = False
        print("⚠️ 可以尝试手动安装snap7库文件")
    
    # 测试安装
    if not test_snap7_installation():
        success = False
    
    # 创建配置文件
    if not create_s7_config():
        success = False
    
    if success:
        show_usage_instructions()
    else:
        print("\n❌ 安装过程中出现错误")
        print("请参考错误信息进行手动安装")
    
    return success

if __name__ == "__main__":
    success = main()
    input("\n按回车键退出...")
    sys.exit(0 if success else 1)
