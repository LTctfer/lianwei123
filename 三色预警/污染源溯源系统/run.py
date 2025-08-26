#!/usr/bin/env python3
"""
污染源溯源系统启动脚本
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from web.app import app, init_inversion_engine

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('system.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """主函数"""
    print("=" * 60)
    print("🌪️  污染源溯源系统")
    print("   基于遗传算法和模式搜索的智能溯源技术")
    print("=" * 60)
    
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 初始化反算引擎
        logger.info("正在初始化反算引擎...")
        init_inversion_engine()
        logger.info("反算引擎初始化完成")
        
        # 启动Web服务
        logger.info("启动Web服务...")
        print("\n🚀 系统启动成功！")
        print("📱 Web界面地址: http://localhost:5000")
        print("📊 可视化页面: http://localhost:5000/visualization")
        print("📤 数据上传页面: http://localhost:5000/upload")
        print("\n按 Ctrl+C 停止服务")
        print("-" * 60)
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("用户中断，正在关闭系统...")
        print("\n👋 系统已关闭")
        
    except Exception as e:
        logger.error(f"系统启动失败: {e}")
        print(f"\n❌ 系统启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()