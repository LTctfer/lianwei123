#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI违规检测系统安装脚本
自动安装依赖、下载模型、配置环境
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """打印欢迎横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    AI违规检测系统安装程序                      ║
    ║                                                              ║
    ║  基于深度学习的智能违规行为识别系统                            ║
    ║  支持工地监控、环境保护、安全管理等场景                        ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ 需要Python 3.8或更高版本")
        print(f"   当前版本: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True

def check_system():
    """检查系统信息"""
    print("💻 检查系统信息...")
    
    system = platform.system()
    machine = platform.machine()
    
    print(f"   操作系统: {system}")
    print(f"   架构: {machine}")
    
    # 检查CUDA支持
    try:
        import torch
        if torch.cuda.is_available():
            print(f"   CUDA: 可用 (设备数量: {torch.cuda.device_count()})")
            for i in range(torch.cuda.device_count()):
                print(f"     - {torch.cuda.get_device_name(i)}")
        else:
            print("   CUDA: 不可用 (将使用CPU)")
    except ImportError:
        print("   CUDA: 未检测到PyTorch，稍后安装")
    
    return True

def install_dependencies():
    """安装依赖包"""
    print("📦 安装依赖包...")
    
    # 基础依赖
    base_packages = [
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "ultralytics>=8.0.0",
        "opencv-python>=4.5.0",
        "flask>=2.0.0",
        "pillow>=8.0.0",
        "numpy>=1.21.0",
        "requests>=2.25.0",
        "pyyaml>=5.4.0",
        "matplotlib>=3.3.0",
        "seaborn>=0.11.0"
    ]
    
    # 可选依赖
    optional_packages = [
        "psutil",  # 系统监控
        "gputil",  # GPU监控
        "flask-cors",  # CORS支持
        "gunicorn",  # 生产环境服务器
        "redis",  # 缓存支持
    ]
    
    try:
        # 升级pip
        print("   升级pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # 安装基础依赖
        print("   安装基础依赖...")
        for package in base_packages:
            print(f"     安装 {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        # 安装可选依赖
        print("   安装可选依赖...")
        for package in optional_packages:
            try:
                print(f"     安装 {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            except subprocess.CalledProcessError:
                print(f"     ⚠️ {package} 安装失败，跳过")
        
        print("✅ 依赖包安装完成")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖包安装失败: {e}")
        return False

def create_directories():
    """创建项目目录结构"""
    print("📁 创建目录结构...")
    
    directories = [
        "data",
        "models",
        "models/weights",
        "yolo-model",  # YOLO模型专用目录
        "web",
        "web/static",
        "web/static/uploads",
        "web/static/results",
        "web/templates",
        "utils",
        "logs",
        "datasets",
        "runs",
        "runs/detect",
        "runs/train"
    ]
    
    project_root = Path(__file__).parent
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"   创建: {directory}")
    
    print("✅ 目录结构创建完成")
    return True

def download_models():
    """强制下载预训练模型"""
    print("🤖 强制下载预训练模型...")

    try:
        import urllib.request
        import shutil
        import time

        # 创建yolo-model目录
        yolo_model_dir = Path(__file__).parent / "yolo-model"
        yolo_model_dir.mkdir(exist_ok=True)

        # 模型下载信息
        models = [
            ("yolov8n.pt", "YOLOv8 Nano - 轻量级模型", "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt"),
            ("yolov8s.pt", "YOLOv8 Small - 小型模型", "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8s.pt")
        ]

        all_success = True

        for model_file, description, url in models:
            model_path = yolo_model_dir / model_file

            if model_path.exists():
                file_size = model_path.stat().st_size / (1024 * 1024)  # MB
                print(f"   ✅ {description} 已存在 ({file_size:.1f}MB)")
                continue

            print(f"   📥 下载 {description}...")
            print(f"      URL: {url}")

            try:
                start_time = time.time()

                def show_progress(block_num, block_size, total_size):
                    downloaded = block_num * block_size
                    if total_size > 0:
                        percent = min(100, downloaded * 100 / total_size)
                        print(f"\r      进度: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')

                # 下载模型
                urllib.request.urlretrieve(url, model_path, reporthook=show_progress)
                print()  # 换行

                # 验证下载
                if model_path.exists() and model_path.stat().st_size > 1024 * 1024:  # 至少1MB
                    download_time = time.time() - start_time
                    file_size = model_path.stat().st_size / (1024 * 1024)  # MB
                    print(f"      ✅ {description} 下载完成: {file_size:.1f}MB, 耗时: {download_time:.1f}秒")

                    # 测试模型
                    try:
                        from ultralytics import YOLO
                        test_model = YOLO(str(model_path))
                        print(f"      ✅ 模型验证成功")
                    except Exception as test_error:
                        print(f"      ❌ 模型验证失败: {test_error}")
                        model_path.unlink()  # 删除损坏文件
                        all_success = False
                else:
                    print(f"      ❌ 下载失败: 文件大小异常")
                    if model_path.exists():
                        model_path.unlink()
                    all_success = False

            except Exception as e:
                print(f"      ❌ 下载失败: {e}")
                all_success = False

        if all_success:
            print("✅ 所有模型下载完成")
            return True
        else:
            print("❌ 部分模型下载失败")
            return False

    except Exception as e:
        print(f"❌ 模型下载过程出错: {e}")
        return False

def create_config_files():
    """创建配置文件"""
    print("⚙️ 创建配置文件...")
    
    project_root = Path(__file__).parent
    
    # 创建环境配置文件
    env_config = """# AI违规检测系统环境配置
# 复制此文件为 .env 并修改相应配置

# Web服务配置
WEB_HOST=0.0.0.0
WEB_PORT=5000
SECRET_KEY=your-secret-key-change-in-production

# 数据库配置
DATABASE_PATH=data/alerts.db

# 邮件通知配置
EMAIL_ENABLED=false
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# 模型配置
MODEL_CONFIDENCE=0.5
DUST_DETECTION_ENABLED=true

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/system.log
"""
    
    env_file = project_root / ".env.example"
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_config)
    
    print(f"   创建: {env_file}")
    
    # 创建启动脚本
    if platform.system() == "Windows":
        start_script = """@echo off
echo 启动AI违规检测系统...
python run.py --mode web
pause
"""
        script_file = project_root / "start.bat"
    else:
        start_script = """#!/bin/bash
echo "启动AI违规检测系统..."
python3 run.py --mode web
"""
        script_file = project_root / "start.sh"
    
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(start_script)
    
    if platform.system() != "Windows":
        os.chmod(script_file, 0o755)
    
    print(f"   创建: {script_file}")
    
    print("✅ 配置文件创建完成")
    return True

def run_tests():
    """运行基础测试"""
    print("🧪 运行基础测试...")
    
    try:
        # 测试导入
        print("   测试模块导入...")
        
        import torch
        print(f"     PyTorch: {torch.__version__}")
        
        import cv2
        print(f"     OpenCV: {cv2.__version__}")
        
        from ultralytics import YOLO
        print("     Ultralytics: 可用")
        
        import flask
        print(f"     Flask: {flask.__version__}")
        
        # 测试CUDA
        if torch.cuda.is_available():
            print(f"     CUDA: 可用 ({torch.version.cuda})")
        else:
            print("     CUDA: 不可用，将使用CPU")
        
        # 测试模型加载
        print("   测试模型加载...")
        try:
            model = YOLO('yolov8n.pt')
            print("     ✅ YOLO模型加载成功")
        except Exception as e:
            print(f"     ⚠️ YOLO模型加载失败: {e}")
        
        print("✅ 基础测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def print_completion_info():
    """打印安装完成信息"""
    info = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                        安装完成！                            ║
    ╚══════════════════════════════════════════════════════════════╝
    
    🚀 启动系统:
       python run.py --mode web
       或者运行: start.bat (Windows) / ./start.sh (Linux/Mac)
    
    📱 访问地址:
       http://localhost:5000
    
    📚 功能说明:
       - 图像上传检测
       - 实时视频检测
       - 智能报警系统
       - 统计分析
       - 报警管理
    
    ⚙️ 配置文件:
       - 复制 .env.example 为 .env 并修改配置
       - 修改 data/config.py 进行高级配置
    
    📖 更多信息:
       - 查看 README.md 了解详细使用说明
       - 查看 data/classes.yaml 了解检测类别
    
    🎯 开始使用吧！
    """
    print(info)

def main():
    """主安装流程"""
    print_banner()
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查系统
    if not check_system():
        sys.exit(1)
    
    # 安装依赖
    if not install_dependencies():
        print("❌ 安装失败：依赖包安装出错")
        sys.exit(1)
    
    # 创建目录
    if not create_directories():
        print("❌ 安装失败：目录创建出错")
        sys.exit(1)
    
    # 下载模型
    if not download_models():
        print("⚠️ 警告：模型下载失败，系统将使用在线模型")
    
    # 创建配置文件
    if not create_config_files():
        print("❌ 安装失败：配置文件创建出错")
        sys.exit(1)
    
    # 运行测试
    if not run_tests():
        print("⚠️ 警告：基础测试失败，可能存在兼容性问题")
    
    # 显示完成信息
    print_completion_info()

if __name__ == '__main__':
    main()
