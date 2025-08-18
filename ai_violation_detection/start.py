#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI违规检测系统启动脚本
确保模型下载完成后再启动系统
"""

import sys
from pathlib import Path

def check_models():
    """检查模型文件是否存在"""
    project_root = Path(__file__).parent
    yolo_model_dir = project_root / 'yolo-model'
    
    required_models = ['yolov8n.pt']
    missing_models = []
    
    for model_file in required_models:
        model_path = yolo_model_dir / model_file
        if not model_path.exists():
            missing_models.append(model_file)
        else:
            file_size = model_path.stat().st_size / (1024 * 1024)  # MB
            print(f"✅ 模型已存在: {model_file} ({file_size:.1f}MB)")
    
    return missing_models

def download_missing_models(missing_models):
    """下载缺失的模型"""
    if not missing_models:
        return True
    
    print(f"❌ 缺少模型文件: {', '.join(missing_models)}")
    print("🔄 开始下载模型...")
    
    try:
        # 调用run.py的下载功能
        from run import download_models
        return download_models()
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False

def main():
    """主函数"""
    print("🤖 AI违规检测系统启动检查")
    print("=" * 50)
    
    # 检查模型文件
    print("📦 检查模型文件...")
    missing_models = check_models()
    
    if missing_models:
        # 下载缺失的模型
        if not download_missing_models(missing_models):
            print("\n❌ 模型下载失败，无法启动系统！")
            print("请检查网络连接或手动下载模型文件")
            print("\n手动下载地址:")
            print("yolov8n.pt: https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt")
            print(f"保存到: {Path(__file__).parent / 'yolo-model' / 'yolov8n.pt'}")
            sys.exit(1)
    
    print("\n✅ 模型检查完成！")
    print("🚀 启动Web应用...")
    print("=" * 50)
    
    # 启动Web应用
    try:
        from run import run_web_app
        run_web_app(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 系统已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
