#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式监控大屏启动脚本
快速启动实时数据生成和交互式大屏
"""

import sys
import os
from pathlib import Path

def main():
    """主函数"""
    print("🚀 RTO/RCO交互式监控大屏启动器")
    print("=" * 50)
    
    try:
        # 导入预警系统
        from warning_system import WarningSystem
        
        # 创建预警系统实例
        warning_system = WarningSystem()
        
        print("✅ 系统初始化完成")
        print("\n🎯 功能特性:")
        print("  📊 实时数据生成 (5秒内1条报警)")
        print("  🖱️ 所有模块可点击交互")
        print("  📈 实时趋势图表")
        print("  🚨 报警信息轮播显示")
        print("  📱 响应式大屏布局")
        print("  🎨 科技风格界面")
        
        print("\n🚀 正在启动交互式监控大屏...")
        
        # 启动实时监控大屏
        warning_system.start_realtime_monitoring()
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保 warning_system.py 文件存在且可导入")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()
