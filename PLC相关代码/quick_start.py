#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC到AI-BOX系统快速启动脚本
提供交互式配置和一键启动功能
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime

def print_banner():
    """打印系统横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                PLC到算能AI-BOX数据采集系统                    ║
║                     快速启动向导                             ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        return False
    
    print(f"✅ Python版本: {sys.version.split()[0]}")
    
    # 检查必要文件
    required_files = [
        'plc_to_aibox_system.py',
        'config_template.py',
        'requirements.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
        return False
    
    print("✅ 必要文件检查通过")
    
    # 检查虚拟环境
    venv_path = Path("venv")
    if not venv_path.exists():
        print("⚠️  虚拟环境不存在，将自动创建")
        return "create_venv"
    
    print("✅ 虚拟环境已存在")
    return True

def create_virtual_environment():
    """创建虚拟环境"""
    print("🔧 创建Python虚拟环境...")
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ 虚拟环境创建成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 虚拟环境创建失败: {e}")
        return False

def install_dependencies():
    """安装依赖包"""
    print("📦 安装依赖包...")
    
    # 获取pip路径
    if sys.platform == "win32":
        pip_path = Path("venv/Scripts/pip.exe")
    else:
        pip_path = Path("venv/bin/pip")
    
    if not pip_path.exists():
        print("❌ 找不到pip，请检查虚拟环境")
        return False
    
    try:
        # 升级pip
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
        
        # 安装依赖
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
        
        print("✅ 依赖包安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖包安装失败: {e}")
        return False

def interactive_config():
    """交互式配置"""
    print("\n🔧 系统配置向导")
    print("=" * 50)
    
    config = {}
    
    # PLC配置
    print("\n📡 PLC设备配置:")
    config['plc_ip'] = input("PLC IP地址 [192.168.1.10]: ").strip() or "192.168.1.10"
    config['plc_port'] = int(input("PLC端口 [502]: ").strip() or "502")
    config['device_id'] = input("设备ID [PLC_001]: ").strip() or "PLC_001"
    
    protocol_options = {
        '1': 'modbus_tcp',
        '2': 'modbus_rtu', 
        '3': 'opcua'
    }
    
    print("\n通信协议:")
    print("1. Modbus TCP")
    print("2. Modbus RTU")
    print("3. OPC UA")
    
    protocol_choice = input("选择协议 [1]: ").strip() or "1"
    config['protocol'] = protocol_options.get(protocol_choice, 'modbus_tcp')
    
    # AI-BOX配置
    print("\n🤖 AI-BOX配置:")
    config['aibox_ip'] = input("AI-BOX IP地址 [192.168.1.100]: ").strip() or "192.168.1.100"
    config['aibox_port'] = int(input("AI-BOX端口 [8080]: ").strip() or "8080")
    config['auth_token'] = input("认证令牌 [可选]: ").strip() or ""
    
    # 数据处理配置
    print("\n⚙️ 数据处理配置:")
    config['scan_rate'] = int(input("数据采集间隔(毫秒) [1000]: ").strip() or "1000")
    config['upload_interval'] = int(input("数据上传间隔(秒) [30]: ").strip() or "30")
    
    enable_fft = input("启用FFT频谱分析? [y/N]: ").strip().lower()
    config['enable_fft'] = enable_fft in ['y', 'yes', '1', 'true']
    
    return config

def generate_config_file(config):
    """生成配置文件"""
    print("\n📝 生成配置文件...")
    
    config_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC到AI-BOX系统配置文件
由快速启动向导自动生成于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

from plc_to_aibox_system import AIBoxConfig

# PLC配置
PLC_CONFIG = {{
    'ip_address': '{config['plc_ip']}',
    'port': {config['plc_port']},
    'device_id': '{config['device_id']}',
    'protocol': '{config['protocol']}',
    'scan_rate': {config['scan_rate']},
    'timeout': 5,
    'retry_count': 3,
    'retry_delay': 2,
    
    # 数据点配置 (示例)
    'parameters': [
        {{
            'name': 'vibration_x',
            'address': 'DB1.DBD0',
            'type': 'REAL',
            'unit': 'mm/s',
            'scale': 1.0,
            'offset': 0.0,
            'min_value': -100.0,
            'max_value': 100.0,
            'description': 'X轴振动速度'
        }},
        {{
            'name': 'vibration_y',
            'address': 'DB1.DBD4',
            'type': 'REAL',
            'unit': 'mm/s',
            'scale': 1.0,
            'offset': 0.0,
            'min_value': -100.0,
            'max_value': 100.0,
            'description': 'Y轴振动速度'
        }},
        {{
            'name': 'temperature',
            'address': 'DB1.DBD8',
            'type': 'REAL',
            'unit': '°C',
            'scale': 1.0,
            'offset': 0.0,
            'min_value': -40.0,
            'max_value': 150.0,
            'description': '设备温度'
        }},
        {{
            'name': 'pressure',
            'address': 'DB1.DBD12',
            'type': 'REAL',
            'unit': 'bar',
            'scale': 1.0,
            'offset': 0.0,
            'min_value': 0.0,
            'max_value': 50.0,
            'description': '系统压力'
        }},
        {{
            'name': 'flow_rate',
            'address': 'DB1.DBD16',
            'type': 'REAL',
            'unit': 'L/min',
            'scale': 1.0,
            'offset': 0.0,
            'min_value': 0.0,
            'max_value': 1000.0,
            'description': '流量'
        }}
    ]
}}

# AI-BOX配置
AIBOX_CONFIG = AIBoxConfig(
    ip_address="{config['aibox_ip']}",
    port={config['aibox_port']},
    api_endpoint="/api/data/upload",
    auth_token="{config['auth_token']}",
    batch_size=50,
    upload_interval={config['upload_interval']},
    timeout=30,
    max_retries=3,
    retry_delay=5
)

# 数据处理配置
PROCESSING_CONFIG = {{
    'buffer_size': 1000,
    'downsample_factor': 1,
    'enable_fft': {str(config['enable_fft']).lower()},
    'fft_window_size': 128,
    'filter_config': {{
        'vibration': {{
            'type': 'bandpass',
            'low_freq': 0.1,
            'high_freq': 0.4,
            'order': 4,
            'method': 'butterworth'
        }},
        'temperature': {{
            'type': 'lowpass',
            'cutoff_freq': 0.1,
            'order': 4,
            'method': 'butterworth'
        }},
        'default': {{
            'type': 'moving_average',
            'window_size': 5,
            'method': 'simple'
        }}
    }},
    'anomaly_detection': {{
        'enable': True,
        'method': 'statistical',
        'threshold': 3.0,
        'window_size': 100
    }}
}}

# 数据库配置
DATABASE_CONFIG = {{
    'type': 'sqlite',
    'path': 'plc_data.db',
    'backup_interval': 3600,
    'cleanup_days': 30
}}

# 日志配置
LOGGING_CONFIG = {{
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_path': 'plc_aibox_system.log',
    'max_file_size': 10 * 1024 * 1024,
    'backup_count': 5,
    'console_output': True
}}
'''
    
    try:
        with open('config.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("✅ 配置文件生成成功: config.py")
        return True
    except Exception as e:
        print(f"❌ 配置文件生成失败: {e}")
        return False

def run_system_test():
    """运行系统测试"""
    print("\n🧪 运行系统测试...")
    
    # 获取Python路径
    if sys.platform == "win32":
        python_path = Path("venv/Scripts/python.exe")
    else:
        python_path = Path("venv/bin/python")
    
    try:
        result = subprocess.run([
            str(python_path), "test_system.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ 系统测试通过")
            return True
        else:
            print("⚠️  系统测试发现问题:")
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  系统测试超时")
        return False
    except Exception as e:
        print(f"❌ 系统测试失败: {e}")
        return False

def start_system():
    """启动系统"""
    print("\n🚀 启动系统...")
    
    # 获取Python路径
    if sys.platform == "win32":
        python_path = Path("venv/Scripts/python.exe")
    else:
        python_path = Path("venv/bin/python")
    
    print("系统正在启动，按Ctrl+C停止...")
    print("Web监控界面: http://localhost:8888")
    print("=" * 50)
    
    try:
        # 启动主系统
        subprocess.run([str(python_path), "plc_to_aibox_system.py"])
    except KeyboardInterrupt:
        print("\n\n系统已停止")
    except Exception as e:
        print(f"\n❌ 系统启动失败: {e}")

def main():
    """主函数"""
    print_banner()
    
    # 检查环境
    env_check = check_environment()
    if env_check == False:
        print("\n❌ 环境检查失败，请解决问题后重试")
        return
    
    # 创建虚拟环境（如果需要）
    if env_check == "create_venv":
        if not create_virtual_environment():
            return
        
        if not install_dependencies():
            return
    
    # 检查配置文件
    if not Path("config.py").exists():
        print("\n📋 配置文件不存在，启动配置向导...")
        config = interactive_config()
        
        if not generate_config_file(config):
            return
    else:
        print("✅ 配置文件已存在")
    
    # 询问是否运行测试
    run_test = input("\n🧪 是否运行系统测试? [Y/n]: ").strip().lower()
    if run_test not in ['n', 'no', '0', 'false']:
        run_system_test()
    
    # 询问是否启动系统
    start_now = input("\n🚀 是否立即启动系统? [Y/n]: ").strip().lower()
    if start_now not in ['n', 'no', '0', 'false']:
        start_system()
    else:
        print("\n✅ 系统准备完成!")
        print("\n手动启动命令:")
        if sys.platform == "win32":
            print("  venv\\Scripts\\python.exe plc_to_aibox_system.py")
        else:
            print("  venv/bin/python plc_to_aibox_system.py")
        
        print("\nWeb监控界面:")
        if sys.platform == "win32":
            print("  venv\\Scripts\\python.exe web_monitor.py")
        else:
            print("  venv/bin/python web_monitor.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 再见!")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)
