#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC到AI-BOX系统安装脚本
自动安装依赖、配置环境、创建服务
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

class PLCAIBoxInstaller:
    def __init__(self):
        self.system = platform.system().lower()
        self.python_executable = sys.executable
        self.install_dir = Path.cwd()
        self.venv_dir = self.install_dir / "venv"
        self.config_file = self.install_dir / "config.py"
        
    def print_step(self, step, message):
        """打印安装步骤"""
        print(f"\n{'='*60}")
        print(f"步骤 {step}: {message}")
        print('='*60)
        
    def run_command(self, command, check=True):
        """执行系统命令"""
        print(f"执行命令: {command}")
        try:
            result = subprocess.run(command, shell=True, check=check, 
                                  capture_output=True, text=True)
            if result.stdout:
                print(result.stdout)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"命令执行失败: {e}")
            if e.stderr:
                print(f"错误信息: {e.stderr}")
            return False
            
    def check_python_version(self):
        """检查Python版本"""
        self.print_step(1, "检查Python版本")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print(f"错误: 需要Python 3.8或更高版本，当前版本: {version.major}.{version.minor}")
            return False
            
        print(f"Python版本检查通过: {version.major}.{version.minor}.{version.micro}")
        return True
        
    def create_virtual_environment(self):
        """创建虚拟环境"""
        self.print_step(2, "创建Python虚拟环境")
        
        if self.venv_dir.exists():
            print("虚拟环境已存在，跳过创建")
            return True
            
        command = f"{self.python_executable} -m venv {self.venv_dir}"
        return self.run_command(command)
        
    def get_venv_python(self):
        """获取虚拟环境中的Python路径"""
        if self.system == "windows":
            return self.venv_dir / "Scripts" / "python.exe"
        else:
            return self.venv_dir / "bin" / "python"
            
    def get_venv_pip(self):
        """获取虚拟环境中的pip路径"""
        if self.system == "windows":
            return self.venv_dir / "Scripts" / "pip.exe"
        else:
            return self.venv_dir / "bin" / "pip"
            
    def install_dependencies(self):
        """安装Python依赖包"""
        self.print_step(3, "安装Python依赖包")
        
        pip_executable = self.get_venv_pip()
        
        # 升级pip
        command = f"{pip_executable} install --upgrade pip"
        if not self.run_command(command):
            return False
            
        # 安装依赖包
        dependencies = [
            "numpy>=1.21.0",
            "pandas>=1.3.0",
            "scipy>=1.7.0",
            "scikit-learn>=1.0.0",
            "aiohttp>=3.8.0",
            "asyncio",
            "pymodbus>=3.0.0",  # Modbus通信
            "opcua>=0.98.0",    # OPC UA通信
            "psutil>=5.8.0",    # 系统监控
            "flask>=2.0.0",     # Web界面
            "plotly>=5.0.0",    # 数据可视化
            "dash>=2.0.0",      # Web仪表板
        ]
        
        for dep in dependencies:
            print(f"安装 {dep}...")
            command = f"{pip_executable} install {dep}"
            if not self.run_command(command, check=False):
                print(f"警告: {dep} 安装失败，可能影响某些功能")
                
        return True
        
    def create_config_file(self):
        """创建配置文件"""
        self.print_step(4, "创建配置文件")
        
        if self.config_file.exists():
            print("配置文件已存在，跳过创建")
            return True
            
        template_file = self.install_dir / "config_template.py"
        if not template_file.exists():
            print("错误: 配置模板文件不存在")
            return False
            
        shutil.copy(template_file, self.config_file)
        print(f"配置文件已创建: {self.config_file}")
        print("请编辑config.py文件，设置实际的PLC和AI-BOX参数")
        return True
        
    def create_directories(self):
        """创建必要的目录"""
        self.print_step(5, "创建系统目录")
        
        directories = [
            "data",      # 数据存储目录
            "logs",      # 日志目录
            "backup",    # 备份目录
            "temp",      # 临时文件目录
        ]
        
        for dir_name in directories:
            dir_path = self.install_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            print(f"创建目录: {dir_path}")
            
        return True
        
    def create_service_file(self):
        """创建系统服务文件"""
        self.print_step(6, "创建系统服务")
        
        if self.system == "linux":
            return self.create_systemd_service()
        elif self.system == "windows":
            return self.create_windows_service()
        else:
            print(f"不支持的操作系统: {self.system}")
            return False
            
    def create_systemd_service(self):
        """创建systemd服务文件 (Linux)"""
        service_content = f"""[Unit]
Description=PLC to AI-BOX Data Collection System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={self.install_dir}
Environment=PATH={self.venv_dir}/bin
ExecStart={self.get_venv_python()} plc_to_aibox_system.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        service_file = self.install_dir / "plc-aibox.service"
        with open(service_file, 'w') as f:
            f.write(service_content)
            
        print(f"服务文件已创建: {service_file}")
        print("要安装服务，请运行以下命令:")
        print(f"sudo cp {service_file} /etc/systemd/system/")
        print("sudo systemctl daemon-reload")
        print("sudo systemctl enable plc-aibox")
        print("sudo systemctl start plc-aibox")
        
        return True
        
    def create_windows_service(self):
        """创建Windows服务脚本"""
        batch_content = f"""@echo off
cd /d "{self.install_dir}"
"{self.get_venv_python()}" plc_to_aibox_system.py
pause
"""
        
        batch_file = self.install_dir / "start_service.bat"
        with open(batch_file, 'w') as f:
            f.write(batch_content)
            
        print(f"启动脚本已创建: {batch_file}")
        print("双击该脚本即可启动服务")
        
        return True
        
    def create_startup_script(self):
        """创建启动脚本"""
        self.print_step(7, "创建启动脚本")
        
        if self.system == "windows":
            script_name = "start.bat"
            script_content = f"""@echo off
echo 启动PLC到AI-BOX数据采集系统...
cd /d "{self.install_dir}"
"{self.get_venv_python()}" plc_to_aibox_system.py
pause
"""
        else:
            script_name = "start.sh"
            script_content = f"""#!/bin/bash
echo "启动PLC到AI-BOX数据采集系统..."
cd "{self.install_dir}"
source venv/bin/activate
python plc_to_aibox_system.py
"""
        
        script_file = self.install_dir / script_name
        with open(script_file, 'w') as f:
            f.write(script_content)
            
        if self.system != "windows":
            os.chmod(script_file, 0o755)
            
        print(f"启动脚本已创建: {script_file}")
        return True
        
    def run_tests(self):
        """运行系统测试"""
        self.print_step(8, "运行系统测试")
        
        python_executable = self.get_venv_python()
        
        # 测试导入
        test_imports = [
            "numpy", "pandas", "scipy", "sklearn", "aiohttp"
        ]
        
        for module in test_imports:
            command = f"{python_executable} -c \"import {module}; print('{module} 导入成功')\""
            if not self.run_command(command, check=False):
                print(f"警告: {module} 导入失败")
                
        # 测试主程序语法
        command = f"{python_executable} -m py_compile plc_to_aibox_system.py"
        if self.run_command(command, check=False):
            print("主程序语法检查通过")
        else:
            print("警告: 主程序语法检查失败")
            
        return True
        
    def print_installation_summary(self):
        """打印安装总结"""
        self.print_step("完成", "安装总结")
        
        print("✓ Python版本检查")
        print("✓ 虚拟环境创建")
        print("✓ 依赖包安装")
        print("✓ 配置文件创建")
        print("✓ 系统目录创建")
        print("✓ 服务文件创建")
        print("✓ 启动脚本创建")
        print("✓ 系统测试")
        
        print("\n下一步操作:")
        print("1. 编辑 config.py 文件，设置实际的PLC和AI-BOX参数")
        print("2. 运行启动脚本测试系统")
        if self.system == "windows":
            print("3. 双击 start.bat 启动系统")
        else:
            print("3. 运行 ./start.sh 启动系统")
            print("4. 或者安装为系统服务 (参考服务安装说明)")
            
        print(f"\n系统安装目录: {self.install_dir}")
        print(f"配置文件: {self.config_file}")
        print(f"日志目录: {self.install_dir / 'logs'}")
        
    def install(self):
        """执行完整安装流程"""
        print("PLC到AI-BOX数据采集系统安装程序")
        print("="*60)
        
        steps = [
            self.check_python_version,
            self.create_virtual_environment,
            self.install_dependencies,
            self.create_config_file,
            self.create_directories,
            self.create_service_file,
            self.create_startup_script,
            self.run_tests,
        ]
        
        for step in steps:
            if not step():
                print(f"\n安装失败: {step.__name__}")
                return False
                
        self.print_installation_summary()
        return True

def main():
    """主函数"""
    installer = PLCAIBoxInstaller()
    
    try:
        success = installer.install()
        if success:
            print("\n🎉 安装完成!")
            sys.exit(0)
        else:
            print("\n❌ 安装失败!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n安装被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n安装过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
