#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI违规检测系统快速启动脚本
跳过复杂的依赖检查，直接启动系统
"""

import os
import sys
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    AI违规检测系统                            ║
    ║                     快速启动模式                             ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def create_directories():
    """创建必要的目录"""
    directories = [
        'data',
        'models/weights',
        'yolo-model',  # YOLO模型专用目录
        'web/static/uploads',
        'web/static/results',
        'logs'
    ]

    project_root = Path(__file__).parent

    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)

def check_critical_imports():
    """检查关键导入"""
    critical_modules = {
        'flask': 'Flask Web框架',
        'cv2': 'OpenCV图像处理库',
        'PIL': 'Pillow图像库',
        'numpy': 'NumPy数值计算库'
    }
    
    missing = []
    
    for module, description in critical_modules.items():
        try:
            __import__(module)
            print(f"✅ {description}")
        except ImportError:
            missing.append((module, description))
            print(f"❌ {description}")
    
    if missing:
        print("\n⚠️ 缺少关键依赖，但系统将尝试启动...")
        print("如果启动失败，请运行: pip install flask opencv-python pillow numpy")
        print("\n按回车键继续...")
        input()
    
    return len(missing) == 0

def start_web_app():
    """启动Web应用"""
    try:
        # 添加项目根目录到Python路径
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        print("🚀 正在启动AI违规检测系统...")
        print("📱 系统将在 http://localhost:5000 启动")
        print("🔄 首次启动可能需要下载模型，请耐心等待...")
        print("=" * 60)
        
        # 导入并启动Flask应用
        from web.app import app
        
        # 启动应用
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # 避免重复启动
        )
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("\n请安装缺少的依赖包:")
        print("pip install flask opencv-python pillow numpy torch torchvision ultralytics")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("\n请检查:")
        print("1. 是否安装了所有依赖包")
        print("2. 端口5000是否被占用")
        print("3. 查看详细错误信息")
        sys.exit(1)

def main():
    """主函数"""
    print_banner()
    
    print("🔧 准备启动环境...")
    
    # 创建必要目录
    create_directories()
    print("📁 目录结构检查完成")
    
    # 检查关键导入
    print("\n📦 检查关键依赖...")
    check_critical_imports()
    
    print("\n" + "=" * 60)
    print("🎯 系统功能:")
    print("   - 图像上传检测违规行为")
    print("   - 实时摄像头监控")
    print("   - 智能报警系统")
    print("   - 统计分析功能")
    print("   - 报警管理")
    print("=" * 60)
    
    # 启动Web应用
    start_web_app()

if __name__ == '__main__':
    main()
