#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能对比测试工具
对比原版和增强版智能预警引擎的性能差异
"""

import time
import statistics
from typing import List, Dict, Any
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smart_alarm import SmartAlarmEngine
from smart_alarm_enhanced import SmartAlarmEngineEnhanced


class PerformanceComparator:
    """性能对比器"""
    
    def __init__(self):
        self.test_data = [
            {'t1': 5, 't2': 15, 't3': 30, 't4': 8},
            {'t1': 0.5, 't2': 15, 't3': 30, 't4': 8},
            {'t1': 15, 't2': 15, 't3': 30, 't4': 8},
            {'t1': 5, 't2': 3, 't3': 30, 't4': 8},
            {'t1': 5, 't2': 25, 't3': 30, 't4': 8},
            {'t1': 2, 't2': 15, 't3': 30, 't4': 8},
            {'t1': 1, 't2': 15, 't3': 30, 't4': 8},
            {'t1': 10, 't2': 15, 't3': 30, 't4': 8},
            {'t1': 5, 't2': 5, 't3': 30, 't4': 8},
            {'t1': 5, 't2': 20, 't3': 30, 't4': 8},
        ]
    
    def benchmark_engine(self, engine, name: str, iterations: int = 1000) -> Dict[str, Any]:
        """基准测试单个引擎"""
        print(f"\n🔬 测试 {name} (迭代次数: {iterations})")
        
        # 预热
        for data in self.test_data[:3]:
            engine.process_data(data)
        
        # 性能测试
        times = []
        alarms_count = 0
        
        start_total = time.time()
        
        for i in range(iterations):
            data = self.test_data[i % len(self.test_data)]
            
            start_time = time.time()
            alarm = engine.process_data(data)
            end_time = time.time()
            
            times.append(end_time - start_time)
            if alarm:
                alarms_count += 1
        
        end_total = time.time()
        
        # 统计结果
        total_time = end_total - start_total
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0
        
        throughput = iterations / total_time
        
        result = {
            'name': name,
            'iterations': iterations,
            'total_time': total_time,
            'avg_time': avg_time,
            'median_time': median_time,
            'min_time': min_time,
            'max_time': max_time,
            'std_time': std_time,
            'throughput': throughput,
            'alarms_count': alarms_count
        }
        
        print(f"   总耗时: {total_time:.4f}s")
        print(f"   平均耗时: {avg_time*1000:.4f}ms")
        print(f"   中位数耗时: {median_time*1000:.4f}ms")
        print(f"   最小耗时: {min_time*1000:.4f}ms")
        print(f"   最大耗时: {max_time*1000:.4f}ms")
        print(f"   标准差: {std_time*1000:.4f}ms")
        print(f"   吞吐量: {throughput:.2f} 次/秒")
        print(f"   触发预警: {alarms_count} 次")
        
        return result
    
    def test_config_update_performance(self, iterations: int = 100) -> Dict[str, Any]:
        """测试配置更新性能"""
        print(f"\n🔧 配置更新性能测试 (迭代次数: {iterations})")
        
        # 原版引擎
        original_engine = SmartAlarmEngine()
        original_times = []
        
        print("   测试原版引擎...")
        for i in range(iterations):
            start_time = time.time()
            original_engine.update_config({
                'alarm_rule.alarmLevel': 'HIGH' if i % 2 == 0 else 'LOW'
            })
            end_time = time.time()
            original_times.append(end_time - start_time)
        
        # 增强版引擎 - 内存模式
        enhanced_engine = SmartAlarmEngineEnhanced()
        enhanced_times = []
        
        print("   测试增强版引擎（内存模式）...")
        for i in range(iterations):
            start_time = time.time()
            enhanced_engine.update_config({
                'alarm_rule.alarmLevel': 'HIGH' if i % 2 == 0 else 'LOW'
            }, persist=False)
            end_time = time.time()
            enhanced_times.append(end_time - start_time)
        
        # 增强版引擎 - 持久化模式
        enhanced_persist_times = []
        
        print("   测试增强版引擎（持久化模式）...")
        for i in range(iterations):
            start_time = time.time()
            enhanced_engine.update_config({
                'alarm_rule.alarmLevel': 'HIGH' if i % 2 == 0 else 'LOW'
            }, persist=True)
            end_time = time.time()
            enhanced_persist_times.append(end_time - start_time)
        
        # 统计结果
        original_avg = statistics.mean(original_times) * 1000
        enhanced_avg = statistics.mean(enhanced_times) * 1000
        enhanced_persist_avg = statistics.mean(enhanced_persist_times) * 1000
        
        print(f"\n📊 配置更新性能对比:")
        print(f"   原版引擎: {original_avg:.4f}ms")
        print(f"   增强版（内存）: {enhanced_avg:.4f}ms")
        print(f"   增强版（持久化）: {enhanced_persist_avg:.4f}ms")
        print(f"   内存模式提升: {(original_avg/enhanced_avg):.2f}x")
        print(f"   持久化模式提升: {(original_avg/enhanced_persist_avg):.2f}x")
        
        return {
            'original_avg': original_avg,
            'enhanced_avg': enhanced_avg,
            'enhanced_persist_avg': enhanced_persist_avg,
            'memory_speedup': original_avg / enhanced_avg,
            'persist_speedup': original_avg / enhanced_persist_avg
        }
    
    def run_comparison(self, iterations: int = 1000) -> Dict[str, Any]:
        """运行完整的性能对比"""
        print("🚀 智能预警引擎性能对比测试")
        print("=" * 60)
        
        try:
            # 创建引擎实例
            original_engine = SmartAlarmEngine()
            enhanced_engine = SmartAlarmEngineEnhanced()
            
            # 数据处理性能测试
            original_result = self.benchmark_engine(original_engine, "原版引擎", iterations)
            enhanced_result = self.benchmark_engine(enhanced_engine, "增强版引擎", iterations)
            
            # 性能对比
            speedup = original_result['avg_time'] / enhanced_result['avg_time']
            throughput_improvement = enhanced_result['throughput'] / original_result['throughput']
            
            print(f"\n📊 数据处理性能对比:")
            print(f"   平均耗时提升: {speedup:.2f}x")
            print(f"   吞吐量提升: {throughput_improvement:.2f}x")
            print(f"   延迟降低: {((original_result['avg_time'] - enhanced_result['avg_time']) * 1000):.4f}ms")
            
            # 配置更新性能测试
            config_result = self.test_config_update_performance(100)
            
            # 获取增强版引擎统计信息
            enhanced_stats = enhanced_engine.get_stats()
            
            print(f"\n📈 增强版引擎统计信息:")
            print(f"   配置版本: {enhanced_stats['config_version']}")
            print(f"   已处理数据: {enhanced_stats['total_processed']} 条")
            print(f"   触发预警: {enhanced_stats['alarms_triggered']} 次")
            print(f"   活跃频率状态: {enhanced_stats['active_freq_states']} 个")
            
            return {
                'data_processing': {
                    'original': original_result,
                    'enhanced': enhanced_result,
                    'speedup': speedup,
                    'throughput_improvement': throughput_improvement
                },
                'config_update': config_result,
                'enhanced_stats': enhanced_stats
            }
            
        except Exception as e:
            print(f"❌ 性能测试过程中发生错误: {e}")
            return {}


def main():
    """主函数"""
    comparator = PerformanceComparator()
    
    # 运行性能对比
    results = comparator.run_comparison(1000)
    
    if results:
        print(f"\n✅ 性能对比测试完成!")
        print(f"\n🎯 关键改进:")
        print(f"   1. 数据处理速度提升: {results['data_processing']['speedup']:.2f}x")
        print(f"   2. 配置更新（内存模式）提升: {results['config_update']['memory_speedup']:.2f}x")
        print(f"   3. 吞吐量提升: {results['data_processing']['throughput_improvement']:.2f}x")
        print(f"   4. 支持热加载和详细异常处理")
        print(f"   5. 内存缓存避免频繁I/O操作")


if __name__ == "__main__":
    main()
