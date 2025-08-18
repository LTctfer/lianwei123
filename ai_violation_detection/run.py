#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI违规检测系统启动脚本
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('system.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_dependencies():
    """检查依赖包"""
    # 包名映射：pip包名 -> 导入名
    package_mapping = {
        'torch': 'torch',
        'torchvision': 'torchvision',
        'ultralytics': 'ultralytics',
        'opencv-python': 'cv2',
        'flask': 'flask',
        'pillow': 'PIL',
        'numpy': 'numpy',
        'requests': 'requests'
    }

    missing_packages = []

    for pip_name, import_name in package_mapping.items():
        try:
            __import__(import_name)
            print(f"✅ {pip_name} 已安装")
        except ImportError:
            missing_packages.append(pip_name)
            print(f"❌ {pip_name} 未安装")

    if missing_packages:
        print("\n❌ 缺少以下依赖包:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    print("\n✅ 所有依赖包已安装")
    return True

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

    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 创建目录: {directory}")

def download_models():
    """强制下载预训练模型到项目目录"""
    try:
        from ultralytics import YOLO
        import shutil
        import os
        import urllib.request
        import time

        # 创建yolo-model目录
        yolo_model_dir = project_root / 'yolo-model'
        yolo_model_dir.mkdir(exist_ok=True)

        # 模型下载URL映射
        model_urls = {
            'yolov8n.pt': 'https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt',
            'yolov8s.pt': 'https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8s.pt'
        }

        all_downloaded = True

        for model_file, url in model_urls.items():
            model_path = yolo_model_dir / model_file

            if not model_path.exists():
                print(f"📥 强制下载模型: {model_file}")
                print(f"   下载地址: {url}")
                print(f"   保存路径: {model_path}")

                try:
                    # 方法1: 直接下载
                    print("   正在下载，请稍候...")
                    start_time = time.time()

                    def show_progress(block_num, block_size, total_size):
                        downloaded = block_num * block_size
                        if total_size > 0:
                            percent = min(100, downloaded * 100 / total_size)
                            print(f"\r   下载进度: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')

                    urllib.request.urlretrieve(url, model_path, reporthook=show_progress)
                    print()  # 换行

                    # 验证下载的文件
                    if model_path.exists() and model_path.stat().st_size > 1024 * 1024:  # 至少1MB
                        download_time = time.time() - start_time
                        file_size = model_path.stat().st_size / (1024 * 1024)  # MB
                        print(f"   ✅ 下载完成: {file_size:.1f}MB, 耗时: {download_time:.1f}秒")

                        # 测试模型是否可用
                        try:
                            test_model = YOLO(str(model_path))
                            print(f"   ✅ 模型验证成功: {model_file}")
                        except Exception as test_error:
                            print(f"   ❌ 模型验证失败: {test_error}")
                            model_path.unlink()  # 删除损坏的文件
                            all_downloaded = False
                    else:
                        print(f"   ❌ 下载失败: 文件大小异常")
                        if model_path.exists():
                            model_path.unlink()
                        all_downloaded = False

                except Exception as download_error:
                    print(f"   ❌ 下载失败: {download_error}")

                    # 方法2: 使用ultralytics下载
                    print("   尝试使用ultralytics下载...")
                    try:
                        model = YOLO(model_file)  # 这会触发自动下载

                        # 查找并复制模型文件
                        ultralytics_path = Path.home() / '.ultralytics' / 'models' / model_file
                        if ultralytics_path.exists():
                            shutil.copy2(ultralytics_path, model_path)
                            print(f"   ✅ 通过ultralytics下载成功: {model_file}")
                        else:
                            print(f"   ❌ ultralytics下载也失败")
                            all_downloaded = False
                    except Exception as ultralytics_error:
                        print(f"   ❌ ultralytics下载失败: {ultralytics_error}")
                        all_downloaded = False
            else:
                file_size = model_path.stat().st_size / (1024 * 1024)  # MB
                print(f"✅ 模型已存在: {model_file} ({file_size:.1f}MB)")

        print(f"\n📁 模型目录: {yolo_model_dir}")

        if not all_downloaded:
            print("\n❌ 部分模型下载失败！")
            print("请检查网络连接或手动下载模型文件")
            print("下载地址:")
            for model_file, url in model_urls.items():
                print(f"  {model_file}: {url}")
            return False

        print("\n✅ 所有模型下载完成！")
        return True

    except Exception as e:
        print(f"\n❌ 模型下载过程出错: {e}")
        return False

def run_web_app(host='0.0.0.0', port=5000, debug=True):
    """运行Web应用"""
    try:
        # 导入Flask应用
        from web.app import app
        
        print("🚀 启动AI违规检测系统...")
        print("=" * 60)
        print(f"📱 访问地址: http://localhost:{port}")
        print("📊 功能包括:")
        print("   - 图像上传检测")
        print("   - 实时视频检测") 
        print("   - 智能报警系统")
        print("   - 统计分析")
        print("   - 报警管理")
        print("=" * 60)
        
        # 启动应用
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

def run_training(config_path=None):
    """运行模型训练"""
    try:
        from ultralytics import YOLO
        
        # 加载配置
        if config_path is None:
            config_path = project_root / 'data' / 'classes.yaml'
        
        print("🏋️ 开始模型训练...")
        print(f"📋 配置文件: {config_path}")
        
        # 创建模型
        model = YOLO('yolov8n.pt')
        
        # 开始训练
        results = model.train(
            data=str(config_path),
            epochs=100,
            imgsz=640,
            batch=16,
            name='violation_detection',
            project='runs/detect'
        )
        
        print("✅ 训练完成!")
        print(f"📊 结果保存在: {results.save_dir}")
        
    except Exception as e:
        print(f"❌ 训练失败: {e}")
        sys.exit(1)

def run_evaluation(model_path, data_path):
    """运行模型评估"""
    try:
        from ultralytics import YOLO
        
        print("📊 开始模型评估...")
        print(f"🤖 模型路径: {model_path}")
        print(f"📋 数据路径: {data_path}")
        
        # 加载模型
        model = YOLO(model_path)
        
        # 运行评估
        results = model.val(data=data_path)
        
        print("✅ 评估完成!")
        print(f"📈 mAP@0.5: {results.box.map50:.3f}")
        print(f"📈 mAP@0.5:0.95: {results.box.map:.3f}")
        
    except Exception as e:
        print(f"❌ 评估失败: {e}")
        sys.exit(1)

def run_inference(model_path, source):
    """运行推理"""
    try:
        from ultralytics import YOLO
        
        print("🔍 开始推理...")
        print(f"🤖 模型路径: {model_path}")
        print(f"📁 数据源: {source}")
        
        # 加载模型
        model = YOLO(model_path)
        
        # 运行推理
        results = model.predict(
            source=source,
            conf=0.5,
            save=True,
            project='runs/detect',
            name='inference'
        )
        
        print("✅ 推理完成!")
        print(f"📁 结果保存在: runs/detect/inference")
        
    except Exception as e:
        print(f"❌ 推理失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI违规检测系统')
    parser.add_argument('--mode', choices=['web', 'train', 'eval', 'infer'], 
                       default='web', help='运行模式')
    parser.add_argument('--host', default='0.0.0.0', help='Web服务器主机')
    parser.add_argument('--port', type=int, default=5000, help='Web服务器端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    parser.add_argument('--model', help='模型路径')
    parser.add_argument('--data', help='数据路径')
    parser.add_argument('--source', help='推理数据源')
    parser.add_argument('--config', help='配置文件路径')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    # 显示欢迎信息
    print("🤖 AI违规检测系统")
    print("=" * 60)
    print("基于深度学习的智能违规行为识别系统")
    print("支持工地监控、环境保护、安全管理等场景")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 创建目录
    create_directories()
    
    # 根据模式运行
    if args.mode == 'web':
        # 强制下载模型（必须完成）
        print("🤖 检查和下载模型...")
        if not download_models():
            print("\n❌ 模型下载失败，无法启动系统！")
            print("请检查网络连接或手动下载模型文件")
            sys.exit(1)

        print("\n🚀 模型准备完成，启动Web应用...")
        # 运行Web应用
        run_web_app(host=args.host, port=args.port, debug=args.debug)
        
    elif args.mode == 'train':
        # 运行训练
        run_training(config_path=args.config)
        
    elif args.mode == 'eval':
        # 运行评估
        if not args.model or not args.data:
            print("❌ 评估模式需要指定 --model 和 --data 参数")
            sys.exit(1)
        run_evaluation(args.model, args.data)
        
    elif args.mode == 'infer':
        # 运行推理
        if not args.model or not args.source:
            print("❌ 推理模式需要指定 --model 和 --source 参数")
            sys.exit(1)
        run_inference(args.model, args.source)

if __name__ == '__main__':
    main()
