#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
污染物溯源系统演示程序
展示完整的污染源溯源流程，包括数据处理、溯源计算、结果验证和可视化

作者: AI Assistant
日期: 2025-01-18
版本: 1.0
"""

import numpy as np
import matplotlib.pyplot as plt
import random
import os
from typing import List, Dict, Tuple

# 导入自定义模块
try:
    from pollution_source_tracker import (
        PollutionSourceTracker, MonitoringData, MeteorologicalData, 
        PollutionSource, create_sample_data
    )
    from data_processor import DataProcessor, Visualizer
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保 pollution_source_tracker.py 和 data_processor.py 在同一目录下")
    exit(1)

class PollutionSourceDemo:
    """污染源溯源演示类"""

    def __init__(self, output_dir: str = None):
        """
        初始化演示程序

        Args:
            output_dir: 输出目录，默认为脚本所在目录下的output文件夹
        """
        if output_dir is None:
            # 获取当前脚本所在目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir = os.path.join(script_dir, "output")

        self.output_dir = output_dir
        self.tracker = PollutionSourceTracker()
        self.visualizer = Visualizer()

        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"创建输出目录: {output_dir}")
        else:
            print(f"使用输出目录: {output_dir}")
    
    def run_complete_demo(self):
        """运行完整的演示流程"""
        print("=" * 60)
        print("污染物溯源系统完整演示")
        print("=" * 60)
        
        # 步骤1：生成和加载数据
        print("\n步骤1: 生成示例数据")
        monitoring_data, met_data = self.generate_realistic_data()
        
        # 步骤2：数据可视化
        print("\n步骤2: 数据可视化")
        self.visualize_initial_data(monitoring_data, met_data)
        
        # 步骤3：执行溯源
        print("\n步骤3: 执行污染源溯源")
        source_result = self.perform_source_tracking(monitoring_data, met_data)
        
        if source_result is None:
            print("溯源失败，演示结束")
            return
        
        # 步骤4：结果验证
        print("\n步骤4: 验证溯源结果")
        verification_results = self.verify_results(source_result, monitoring_data, met_data)
        
        # 步骤5：正向扩散模拟
        print("\n步骤5: 正向扩散模拟验证")
        self.simulate_forward_dispersion(source_result, monitoring_data, met_data)
        
        # 步骤6：生成报告
        print("\n步骤6: 生成分析报告")
        self.generate_comprehensive_report(source_result, verification_results, monitoring_data, met_data)
        
        print("\n" + "=" * 60)
        print("演示完成！所有结果已保存到output目录")
        print("=" * 60)
    
    def generate_realistic_data(self) -> Tuple[List[MonitoringData], MeteorologicalData]:
        """
        生成更真实的示例数据
        
        Returns:
            (监测数据, 气象数据)
        """
        # 设置真实污染源 (模拟工厂排放)
        true_source = PollutionSource(x=150, y=80, z=15, emission_rate=1.5)
        
        # 设置气象条件 (典型的污染天气)
        met_data = MeteorologicalData(
            wind_speed=2.5,
            wind_direction=60.0,  # 东北风
            temperature=18.0,
            humidity=75.0,
            pressure=1015.0,
            solar_radiation=250.0,
            cloud_cover=0.6,
            timestamp="2024-01-15 14:00:00"
        )
        
        # 监测站网络布局 (围绕污染源的不规则分布)
        station_configs = [
            ("环保局站", 300, 200, 3),
            ("学校站", 400, 150, 3),
            ("医院站", 250, 300, 3),
            ("工业区站", 100, 100, 3),
            ("居民区站", 500, 250, 3),
            ("交通站", 350, 50, 3),
            ("背景站", 600, 400, 3),
            ("对照站", 50, 350, 3)
        ]
        
        # 使用高斯模型生成观测数据
        from pollution_source_tracker import GaussianPlumeModel
        gaussian_model = GaussianPlumeModel()
        
        monitoring_data = []
        for station_id, x, y, z in station_configs:
            # 计算理论浓度
            theoretical_conc = gaussian_model.calculate_concentration(
                true_source, x, y, z, met_data
            )
            
            # 添加现实的观测误差和噪声
            # 1. 仪器误差 (±5%)
            instrument_error = random.uniform(-0.05, 0.05) * theoretical_conc
            
            # 2. 环境噪声 (基于距离的随机噪声)
            distance = np.sqrt((x - true_source.x)**2 + (y - true_source.y)**2)
            noise_level = min(0.2, 0.05 + distance / 2000)  # 距离越远噪声越大
            environmental_noise = random.uniform(-noise_level, noise_level) * theoretical_conc
            
            # 3. 背景浓度
            background = random.uniform(5, 15)  # 5-15 微克/立方米 背景浓度
            
            # 最终观测值
            observed_concentration = max(0, theoretical_conc + instrument_error + 
                                       environmental_noise + background)
            
            monitoring_data.append(MonitoringData(
                station_id=station_id,
                x=x, y=y, z=z,
                concentration=observed_concentration,
                timestamp="2024-01-15 14:00:00"
            ))
        
        print(f"生成了 {len(monitoring_data)} 个监测站的数据")
        print(f"真实污染源位置: 东西方向{true_source.x}米, 南北方向{true_source.y}米, 高度{true_source.z}米")
        print(f"真实排放强度: {true_source.emission_rate} 克/秒")
        
        return monitoring_data, met_data
    
    def visualize_initial_data(self, monitoring_data: List[MonitoringData], 
                             met_data: MeteorologicalData):
        """可视化初始数据"""
        # 转换数据格式
        data_dicts = [
            {
                'station_id': d.station_id,
                'x': d.x,
                'y': d.y,
                'z': d.z,
                'concentration': d.concentration
            }
            for d in monitoring_data
        ]
        
        # 绘制监测站分布
        save_path = os.path.join(self.output_dir, "monitoring_stations.png")
        self.visualizer.plot_monitoring_stations(data_dicts, save_path=save_path)
        
        # 显示数据统计
        concentrations = [d.concentration for d in monitoring_data]
        print(f"浓度统计: 最小值={min(concentrations):.1f}, "
              f"最大值={max(concentrations):.1f}, "
              f"平均值={np.mean(concentrations):.1f} 微克/立方米")
    
    def perform_source_tracking(self, monitoring_data: List[MonitoringData],
                              met_data: MeteorologicalData) -> Dict:
        """执行污染源溯源"""
        # 添加数据到溯源器
        for data in monitoring_data:
            self.tracker.add_monitoring_data(data)
        self.tracker.set_meteorological_data(met_data)
        
        # 执行溯源
        source = self.tracker.trace_pollution_source()
        
        if source is None:
            return None
        
        return {
            'source': source,
            'monitoring_data': monitoring_data,
            'meteorological_data': met_data
        }
    
    def verify_results(self, source_result: Dict, 
                      monitoring_data: List[MonitoringData],
                      met_data: MeteorologicalData) -> Dict:
        """验证溯源结果"""
        verification_stats = self.tracker.verify_source(source_result['source'])
        
        # 准备验证数据用于可视化
        verification_data = []
        for monitor in monitoring_data:
            theoretical_conc = self.tracker.gaussian_model.calculate_concentration(
                source_result['source'], monitor.x, monitor.y, monitor.z, met_data
            )
            
            verification_data.append({
                'station_id': monitor.station_id,
                'observed': monitor.concentration,
                'predicted': theoretical_conc,
                'absolute_error': abs(monitor.concentration - theoretical_conc),
                'relative_error': (abs(monitor.concentration - theoretical_conc) / 
                                 max(monitor.concentration, 1.0)) * 100
            })
        
        # 绘制验证结果
        save_path = os.path.join(self.output_dir, "verification_results.png")
        self.visualizer.plot_verification_results(verification_data, save_path=save_path)
        
        return {
            'statistics': verification_stats,
            'detailed_results': verification_data
        }
    
    def simulate_forward_dispersion(self, source_result: Dict,
                                  monitoring_data: List[MonitoringData],
                                  met_data: MeteorologicalData):
        """正向扩散模拟"""
        try:
            # 执行正向模拟
            x_grid, y_grid, conc_grid = self.tracker.simulate_forward_dispersion(
                source_result['source'], grid_size=60, domain_size=1200
            )
            
            # 转换监测数据格式
            data_dicts = [
                {
                    'station_id': d.station_id,
                    'x': d.x,
                    'y': d.y,
                    'concentration': d.concentration
                }
                for d in monitoring_data
            ]
            
            # 绘制扩散等值线图
            save_path = os.path.join(self.output_dir, "dispersion_simulation.png")
            self.visualizer.plot_dispersion_contour(
                x_grid, y_grid, conc_grid,
                monitoring_data=data_dicts,
                source_location=(source_result['source'].x, source_result['source'].y),
                save_path=save_path
            )
            
            print(f"正向模拟完成，最大浓度: {np.max(conc_grid):.2f} 微克/立方米")
            
        except Exception as e:
            print(f"正向模拟失败: {e}")
    
    def generate_comprehensive_report(self, source_result: Dict, 
                                    verification_results: Dict,
                                    monitoring_data: List[MonitoringData],
                                    met_data: MeteorologicalData):
        """生成综合分析报告"""
        report_path = os.path.join(self.output_dir, "comprehensive_report.txt")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("污染源溯源分析报告\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("1. 溯源结果\n")
            f.write("-" * 20 + "\n")
            f.write(f"污染源位置: ({source_result['source'].x:.1f}, "
                   f"{source_result['source'].y:.1f}, {source_result['source'].z:.1f}) m\n")
            f.write(f"排放强度: {source_result['source'].emission_rate:.3f} g/s\n")
            f.write(f"置信度: {source_result['source'].confidence:.6f}\n\n")
            
            f.write("2. 验证统计\n")
            f.write("-" * 20 + "\n")
            stats = verification_results['statistics']
            f.write(f"平均绝对误差: {stats['mean_absolute_error']:.2f} 微克/立方米\n")
            f.write(f"最大绝对误差: {stats['max_absolute_error']:.2f} 微克/立方米\n")
            f.write(f"均方根误差: {stats['rmse']:.2f} 微克/立方米\n")
            f.write(f"相关系数: {stats['correlation']:.3f}\n\n")
            
            f.write("3. 各站点详细结果\n")
            f.write("-" * 20 + "\n")
            for result in verification_results['detailed_results']:
                f.write(f"{result['station_id']}: 观测={result['observed']:.1f}, "
                       f"预测={result['predicted']:.1f}, "
                       f"误差={result['relative_error']:.1f}%\n")
            
            f.write(f"\n4. 气象条件\n")
            f.write("-" * 20 + "\n")
            f.write(f"风速: {met_data.wind_speed} m/s\n")
            f.write(f"风向: {met_data.wind_direction}°\n")
            f.write(f"温度: {met_data.temperature}°C\n")
            f.write(f"湿度: {met_data.humidity}%\n")
        
        print(f"综合报告已保存: {report_path}")


def main():
    """主函数"""
    # 设置随机种子
    random.seed(42)
    np.random.seed(42)
    
    # 创建演示实例
    demo = PollutionSourceDemo()
    
    # 运行完整演示
    demo.run_complete_demo()


if __name__ == "__main__":
    main()
