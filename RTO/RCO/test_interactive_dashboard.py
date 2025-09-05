#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试交互式大屏功能
验证点击交互和数据展示是否正常工作
"""

import time
import webbrowser
from warning_system import InteractiveDashboardServer

def test_dashboard():
    """测试交互式大屏"""
    print("🧪 测试交互式监控大屏")
    print("=" * 50)
    
    # 创建服务器实例
    server = InteractiveDashboardServer(port=8091)  # 使用不同端口避免冲突
    
    print("✅ 服务器创建成功")
    print("🎯 测试功能:")
    print("  1. 点击各个模块查看详情弹窗")
    print("  2. 验证数据展示完整性")
    print("  3. 检查报警信息轮播")
    print("  4. 测试实时数据更新")
    
    print("\n🚀 启动测试服务器...")
    print("📱 访问地址: http://localhost:8091")
    print("🛑 按 Ctrl+C 停止测试")
    
    try:
        # 启动服务器
        server.start_server()
    except KeyboardInterrupt:
        print("\n👋 测试完成")

if __name__ == "__main__":
    test_dashboard()
