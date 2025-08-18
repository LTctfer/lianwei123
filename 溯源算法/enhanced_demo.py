#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版污染源溯源算法演示脚本
展示完整的分析流程和可视化功能
"""

import sys
import os
import time
import argparse
from typing import Dict, Any

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_pollution_tracing import EnhancedPollutionTracingSystem, EnhancedScenarioConfig


def print_banner():
    """打印欢迎横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                 增强版污染源溯源算法演示系统                   ║
    ║                                                              ║
    ║  目标 多算法对比  图像 交互式可视化  图表 性能分析  列表 综合报告      ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def create_scenario_configs() -> Dict[str, EnhancedScenarioConfig]:
    """创建不同的测试场景配置"""
    
    scenarios = {
        'standard': EnhancedScenarioConfig(
            source_x=150.0, source_y=200.0, source_z=25.0, emission_rate=2.5,
            wind_speed=3.5, wind_direction=225.0,
            sensor_grid_size=7, noise_level=0.1,
            population_size=80, max_generations=1500
        ),
        
        'high_wind': EnhancedScenarioConfig(
            source_x=100.0, source_y=150.0, source_z=30.0, emission_rate=3.0,
            wind_speed=8.0, wind_direction=180.0,
            sensor_grid_size=8, noise_level=0.15,
            population_size=100, max_generations=2000
        ),
        
        'low_emission': EnhancedScenarioConfig(
            source_x=200.0, source_y=100.0, source_z=15.0, emission_rate=1.0,
            wind_speed=2.0, wind_direction=45.0,
            sensor_grid_size=9, noise_level=0.2,
            population_size=120, max_generations=2500
        ),
        
        'complex': EnhancedScenarioConfig(
            source_x=75.0, source_y=300.0, source_z=40.0, emission_rate=4.0,
            wind_speed=5.5, wind_direction=315.0,
            sensor_grid_size=6, noise_level=0.05,
            population_size=150, max_generations=3000
        )
    }
    
    return scenarios


def run_single_scenario(scenario_name: str, config: EnhancedScenarioConfig) -> Dict[str, Any]:
    """运行单个场景分析"""
    
    print(f"\n{'='*60}")
    print(f"目标 运行场景: {scenario_name}")
    print(f"{'='*60}")
    
    # 创建系统
    system = EnhancedPollutionTracingSystem(config)
    
    # 运行完整分析
    results = system.run_complete_analysis(scenario_name)
    
    return results


def run_comparative_analysis():
    """运行对比分析"""
    
    print_banner()
    print("启动 开始增强版污染源溯源算法演示...")
    
    # 获取场景配置
    scenarios = create_scenario_configs()
    
    # 存储所有结果
    all_results = {}
    
    # 运行各个场景
    for scenario_name, config in scenarios.items():
        try:
            results = run_single_scenario(scenario_name, config)
            all_results[scenario_name] = results
            
            # 打印简要结果
            print(f"\n图表 {scenario_name} 场景结果摘要:")
            best_algorithm = min(results['results'].items(), 
                               key=lambda x: x[1].objective_value)
            
            print(f"   最佳算法: {best_algorithm[0]}")
            print(f"   位置误差: {best_algorithm[1].position_error:.2f} m")
            print(f"   源强误差: {best_algorithm[1].emission_error:.2f} %")
            print(f"   计算时间: {best_algorithm[1].computation_time:.2f} s")
            
        except Exception as e:
            print(f"[错误] 场景 {scenario_name} 运行失败: {e}")
            continue
    
    # 生成总体对比报告
    generate_overall_comparison(all_results)
    
    print(f"\n[完成] 所有场景分析完成！")
    print(f"文件夹 结果文件保存在: enhanced_results/ 目录")
    
    return all_results


def generate_overall_comparison(all_results: Dict[str, Dict[str, Any]]):
    """生成总体对比报告"""
    
    print(f"\n列表 生成总体对比报告...")
    
    import json
    from datetime import datetime
    
    comparison_report = {
        'timestamp': datetime.now().isoformat(),
        'total_scenarios': len(all_results),
        'scenario_summary': {},
        'algorithm_performance': {},
        'recommendations': []
    }
    
    # 统计各场景结果
    for scenario_name, results in all_results.items():
        if 'results' in results:
            best_result = min(results['results'].values(), 
                            key=lambda r: r.objective_value)
            
            comparison_report['scenario_summary'][scenario_name] = {
                'best_algorithm': min(results['results'].items(), 
                                    key=lambda x: x[1].objective_value)[0],
                'position_error': best_result.position_error,
                'emission_error': best_result.emission_error,
                'computation_time': best_result.computation_time,
                'total_time': results.get('total_time', 0)
            }
    
    # 算法性能统计
    algorithm_stats = {}
    for scenario_name, results in all_results.items():
        if 'results' in results:
            for alg_name, result in results['results'].items():
                if alg_name not in algorithm_stats:
                    algorithm_stats[alg_name] = {
                        'position_errors': [],
                        'emission_errors': [],
                        'computation_times': [],
                        'objective_values': []
                    }
                
                algorithm_stats[alg_name]['position_errors'].append(result.position_error)
                algorithm_stats[alg_name]['emission_errors'].append(result.emission_error)
                algorithm_stats[alg_name]['computation_times'].append(result.computation_time)
                algorithm_stats[alg_name]['objective_values'].append(result.objective_value)
    
    # 计算平均性能
    for alg_name, stats in algorithm_stats.items():
        comparison_report['algorithm_performance'][alg_name] = {
            'avg_position_error': sum(stats['position_errors']) / len(stats['position_errors']),
            'avg_emission_error': sum(stats['emission_errors']) / len(stats['emission_errors']),
            'avg_computation_time': sum(stats['computation_times']) / len(stats['computation_times']),
            'avg_objective_value': sum(stats['objective_values']) / len(stats['objective_values'])
        }
    
    # 生成建议
    if algorithm_stats:
        best_overall = min(comparison_report['algorithm_performance'].items(),
                          key=lambda x: x[1]['avg_objective_value'])
        
        comparison_report['recommendations'] = [
            f"总体最佳算法: {best_overall[0]}",
            f"平均位置误差: {best_overall[1]['avg_position_error']:.2f} m",
            f"平均源强误差: {best_overall[1]['avg_emission_error']:.2f} %",
            f"平均计算时间: {best_overall[1]['avg_computation_time']:.2f} s"
        ]
    
    # 保存报告
    os.makedirs('enhanced_results', exist_ok=True)
    report_path = os.path.join('enhanced_results', 'overall_comparison_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(comparison_report, f, ensure_ascii=False, indent=2)
    
    print(f"图表 总体对比报告已保存: {report_path}")


def run_interactive_demo():
    """运行交互式演示"""
    
    print_banner()
    print("🎮 交互式演示模式")
    print("请选择要运行的场景:")
    
    scenarios = create_scenario_configs()
    scenario_list = list(scenarios.keys())
    
    for i, name in enumerate(scenario_list, 1):
        config = scenarios[name]
        print(f"  {i}. {name} - 风速:{config.wind_speed}m/s, 源强:{config.emission_rate}g/s")
    
    print(f"  {len(scenario_list)+1}. 运行所有场景对比")
    print(f"  0. 退出")
    
    while True:
        try:
            choice = input("\n请输入选择 (0-{}): ".format(len(scenario_list)+1))
            choice = int(choice)
            
            if choice == 0:
                print("👋 再见！")
                break
            elif choice == len(scenario_list) + 1:
                run_comparative_analysis()
                break
            elif 1 <= choice <= len(scenario_list):
                scenario_name = scenario_list[choice - 1]
                config = scenarios[scenario_name]
                run_single_scenario(scenario_name, config)
                break
            else:
                print("[错误] 无效选择，请重新输入")
                
        except ValueError:
            print("[错误] 请输入有效数字")
        except KeyboardInterrupt:
            print("\n👋 用户中断，退出程序")
            break


def main():
    """主函数"""
    
    parser = argparse.ArgumentParser(description='增强版污染源溯源算法演示')
    parser.add_argument('--mode', choices=['auto', 'interactive', 'single'], 
                       default='interactive', help='运行模式')
    parser.add_argument('--scenario', choices=['standard', 'high_wind', 'low_emission', 'complex'],
                       default='standard', help='单一场景模式下的场景选择')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'auto':
            # 自动运行所有场景
            run_comparative_analysis()
            
        elif args.mode == 'interactive':
            # 交互式模式
            run_interactive_demo()
            
        elif args.mode == 'single':
            # 单一场景模式
            scenarios = create_scenario_configs()
            config = scenarios[args.scenario]
            run_single_scenario(args.scenario, config)
        
        print(f"\n🎉 演示完成！")
        
    except KeyboardInterrupt:
        print(f"\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"\n[错误] 程序运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
