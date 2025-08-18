#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
污染源溯源算法系统演示启动脚本
"""

import os
import sys
import argparse
from pathlib import Path

def print_banner():
    """打印欢迎横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                 污染源溯源算法系统启动器                       ║
    ║                                                              ║
    ║  目标 多种运行模式  图像 丰富可视化  图表 性能分析  网络 Web界面      ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'numpy', 'pandas', 'matplotlib', 'seaborn', 
        'plotly', 'scipy', 'deap', 'tqdm'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("[错误] 缺少以下依赖包:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n请运行以下命令安装:")
        print("pip install -r requirements.txt")
        return False
    
    print("[完成] 所有依赖包已安装")
    return True

def show_menu():
    """显示主菜单"""
    print("\n🎮 请选择运行模式:")
    print("1. 网络 Web界面模式 (推荐)")
    print("2. 🖥️  命令行演示模式")
    print("3. 分析 交互式分析模式")
    print("4. 启动 自动运行所有场景")
    print("5. 📚 查看使用说明")
    print("6. 工具 Web界面故障排除")
    print("7. 网络 简化Web启动器")
    print("0. 🚪 退出")

    return input("\n请输入选择 (0-7): ").strip()

def run_web_interface():
    """运行Web界面"""
    print("\n网络 启动Web界面...")

    try:
        import subprocess

        # 检查streamlit
        try:
            import streamlit
            print("[完成] Streamlit 已安装")
        except ImportError:
            print("[错误] 缺少streamlit，正在安装...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
                print("[完成] Streamlit 安装完成")
            except Exception as install_error:
                print(f"[错误] Streamlit 安装失败: {install_error}")
                print("灯泡 请手动安装: pip install streamlit")
                return

        # 启动Web界面
        current_dir = Path(__file__).parent
        web_script = current_dir / "start_web.py"

        if web_script.exists():
            print("启动 正在启动Web服务器...")
            print("灯泡 如果无法访问，请尝试选项7（简化Web启动器）")
            subprocess.run([sys.executable, str(web_script)])
        else:
            print("[错误] 找不到Web界面启动脚本")
            print("灯泡 请尝试选项7（简化Web启动器）")

    except Exception as e:
        print(f"[错误] Web界面启动失败: {e}")
        print("灯泡 请尝试选项6（故障排除）或选项7（简化启动器）")

def run_command_demo():
    """运行命令行演示"""
    print("\n🖥️ 启动命令行演示...")
    
    try:
        current_dir = Path(__file__).parent
        demo_script = current_dir / "enhanced_demo.py"
        
        if demo_script.exists():
            import subprocess
            subprocess.run([sys.executable, str(demo_script), "--mode", "interactive"])
        else:
            print("[错误] 找不到演示脚本")
            
    except Exception as e:
        print(f"[错误] 命令行演示启动失败: {e}")

def run_interactive_analysis():
    """运行交互式分析"""
    print("\n分析 启动交互式分析...")
    
    try:
        from enhanced_pollution_tracing import EnhancedPollutionTracingSystem, EnhancedScenarioConfig
        
        print("创建默认配置...")
        config = EnhancedScenarioConfig()
        system = EnhancedPollutionTracingSystem(config)
        
        print("运行分析...")
        results = system.run_complete_analysis("interactive_demo")
        
        print(f"\n[完成] 分析完成！")
        print(f"文件夹 结果保存在: enhanced_results/ 目录")
        
    except Exception as e:
        print(f"[错误] 交互式分析失败: {e}")

def run_auto_scenarios():
    """自动运行所有场景"""
    print("\n启动 自动运行所有场景...")
    
    try:
        current_dir = Path(__file__).parent
        demo_script = current_dir / "enhanced_demo.py"
        
        if demo_script.exists():
            import subprocess
            subprocess.run([sys.executable, str(demo_script), "--mode", "auto"])
        else:
            print("[错误] 找不到演示脚本")
            
    except Exception as e:
        print(f"[错误] 自动场景运行失败: {e}")

def show_documentation():
    """显示使用说明"""
    print("\n📚 使用说明")
    print("=" * 50)
    
    doc_content = """
    目标 系统功能:
    - 污染源位置和排放强度反算
    - 多种遗传算法变体对比
    - 丰富的可视化功能
    - 综合性能分析报告
    
    启动 快速开始:
    1. 选择Web界面模式（推荐新手）
    2. 在场景配置页面设置参数
    3. 运行算法分析
    4. 查看可视化结果
    
    工具 高级功能:
    - 自定义传感器网络布置
    - 多场景对比分析
    - 算法参数优化
    - 敏感性分析
    
    文件夹 输出文件:
    - PNG格式的静态图表
    - HTML格式的交互式图表
    - JSON格式的分析报告
    
    灯泡 使用技巧:
    - 增加传感器数量可提高精度
    - 降低噪声水平可改善结果
    - 启用并行计算可加速运行
    - 使用自适应算法可提高收敛性
    """
    
    print(doc_content)
    
    # 显示文档文件
    current_dir = Path(__file__).parent
    readme_file = current_dir / "README_增强版.md"
    
    if readme_file.exists():
        print(f"\n📖 详细文档: {readme_file}")
        
        choice = input("\n是否打开详细文档? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            try:
                import webbrowser
                webbrowser.open(str(readme_file))
            except Exception as e:
                print(f"无法打开文档: {e}")
    
    input("\n按回车键返回主菜单...")

def run_web_diagnosis():
    """运行Web界面故障诊断"""
    print("\n工具 启动Web界面故障诊断...")

    try:
        current_dir = Path(__file__).parent
        diagnosis_script = current_dir / "diagnose_web.py"

        if diagnosis_script.exists():
            import subprocess
            subprocess.run([sys.executable, str(diagnosis_script)])
        else:
            print("[错误] 找不到故障诊断脚本")

    except Exception as e:
        print(f"[错误] 故障诊断启动失败: {e}")

def run_simple_web():
    """运行简化Web启动器"""
    print("\n网络 启动简化Web启动器...")

    try:
        current_dir = Path(__file__).parent
        simple_web_script = current_dir / "simple_web_start.py"

        if simple_web_script.exists():
            import subprocess
            subprocess.run([sys.executable, str(simple_web_script)])
        else:
            print("[错误] 找不到简化Web启动脚本")

    except Exception as e:
        print(f"[错误] 简化Web启动器启动失败: {e}")

def main():
    """主函数"""
    
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        print("\n请先安装依赖包后再运行")
        sys.exit(1)
    
    while True:
        try:
            choice = show_menu()
            
            if choice == '0':
                print("\n👋 再见！")
                break
            elif choice == '1':
                run_web_interface()
            elif choice == '2':
                run_command_demo()
            elif choice == '3':
                run_interactive_analysis()
            elif choice == '4':
                run_auto_scenarios()
            elif choice == '5':
                show_documentation()
            else:
                print("[错误] 无效选择，请重新输入")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，程序退出")
            break
        except Exception as e:
            print(f"\n[错误] 程序运行出错: {e}")
            continue

if __name__ == "__main__":
    main()
