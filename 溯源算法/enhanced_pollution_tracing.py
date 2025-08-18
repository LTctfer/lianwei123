#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版污染源溯源系统主控制器
集成多种算法、可视化和用户交互功能
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
import time
import os
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass, asdict
import json
from datetime import datetime, timedelta

# 导入现有模块
from gaussian_plume_model import GaussianPlumeModel, PollutionSource, MeteoData
from optimized_source_inversion import OptimizedSourceInversion, OptimizedSensorData, AdaptiveGAParameters, OptimizedInversionResult
from visualization_module import PollutionSourceVisualizer

# 设置样式
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
warnings.filterwarnings('ignore')

# 统一中文字体设置（跨平台检测）
try:
    from zh_font import setup_chinese_fonts
    _font_used = setup_chinese_fonts()
    print(f"[字体] Matplotlib/Plotly 使用: {_font_used}")
except Exception as _e:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False


@dataclass
class EnhancedScenarioConfig:
    """增强版场景配置"""
    # 污染源配置
    source_x: float = 150.0
    source_y: float = 200.0
    source_z: float = 25.0
    emission_rate: float = 2.5
    
    # 气象配置
    wind_speed: float = 3.5
    wind_direction: float = 225.0
    temperature: float = 20.0
    pressure: float = 101325.0
    humidity: float = 60.0
    
    # 传感器配置
    sensor_grid_size: int = 7
    sensor_spacing: float = 100.0
    sensor_height: float = 2.0
    noise_level: float = 0.1
    
    # 算法配置
    population_size: int = 50  # 减小种群大小以加快计算
    max_generations: int = 500  # 减少迭代次数以加快计算
    use_parallel: bool = False  # 禁用并行计算以避免序列化问题
    use_cache: bool = True


class EnhancedPollutionTracingSystem:
    """增强版污染源溯源系统"""
    
    def __init__(self, config: Optional[EnhancedScenarioConfig] = None):
        """初始化系统"""
        self.config = config or EnhancedScenarioConfig()
        self.gaussian_model = GaussianPlumeModel()
        self.visualizer = PollutionSourceVisualizer()
        
        # 结果存储
        self.results_history = []
        self.performance_metrics = {}
        
        # 创建结果目录
        self.results_dir = "enhanced_results"
        os.makedirs(self.results_dir, exist_ok=True)
        
        print(">> 增强版污染源溯源系统已初始化")
        print(f">> 结果将保存到: {self.results_dir}")
    
    def create_scenario(self, scenario_name: str = "default") -> Tuple[PollutionSource, MeteoData, List[OptimizedSensorData]]:
        """创建测试场景"""
        print(f"\n>> 创建测试场景: {scenario_name}")
        
        # 创建污染源
        true_source = PollutionSource(
            x=self.config.source_x,
            y=self.config.source_y,
            z=self.config.source_z,
            emission_rate=self.config.emission_rate
        )
        
        # 创建气象数据
        meteo_data = MeteoData(
            wind_speed=self.config.wind_speed,
            wind_direction=self.config.wind_direction,
            temperature=self.config.temperature,
            pressure=self.config.pressure,
            humidity=self.config.humidity,
            solar_radiation=500.0,
            cloud_cover=0.3
        )
        
        # 创建传感器网络
        sensor_data = self._create_sensor_network(true_source, meteo_data)
        
        print(f"[完成] 场景创建完成:")
        print(f"   污染源位置: ({true_source.x:.1f}, {true_source.y:.1f}, {true_source.z:.1f}) m")
        print(f"   排放强度: {true_source.emission_rate:.2f} g/s")
        print(f"   风速: {meteo_data.wind_speed:.1f} m/s, 风向: {meteo_data.wind_direction:.1f}°")
        print(f"   传感器数量: {len(sensor_data)}")
        
        return true_source, meteo_data, sensor_data
    
    def _create_sensor_network(self, source: PollutionSource, meteo_data: MeteoData) -> List[OptimizedSensorData]:
        """创建传感器网络"""
        sensors = []
        
        # 网格布置
        grid_size = self.config.sensor_grid_size
        spacing = self.config.sensor_spacing
        center_x, center_y = 0, 0
        
        for i in range(grid_size):
            for j in range(grid_size):
                x = center_x + (i - grid_size//2) * spacing
                y = center_y + (j - grid_size//2) * spacing
                
                # 计算理论浓度
                concentration = self.gaussian_model.calculate_concentration(
                    source, x, y, self.config.sensor_height, meteo_data
                )
                
                # 添加噪声
                noise = np.random.normal(0, concentration * self.config.noise_level)
                observed_concentration = max(0, concentration + noise)
                
                # 只保留有效浓度的传感器
                if observed_concentration > 0.1:  # 阈值过滤
                    sensor = OptimizedSensorData(
                        sensor_id=f"S{i:02d}{j:02d}",
                        x=x, y=y, z=self.config.sensor_height,
                        concentration=observed_concentration,
                        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        uncertainty=observed_concentration * self.config.noise_level,
                        weight=1.0 / (1.0 + observed_concentration * self.config.noise_level)
                    )
                    sensors.append(sensor)
        
        return sensors
    
    def run_enhanced_inversion(self,
                             sensor_data: List[OptimizedSensorData],
                             meteo_data: MeteoData,
                             algorithm_variants: List[str] = None,
                             true_source: Optional[PollutionSource] = None) -> Dict[str, OptimizedInversionResult]:
        """运行增强版反算分析

        Args:
            sensor_data: 传感器数据
            meteo_data: 气象数据
            algorithm_variants: 需要运行的算法列表
            true_source: 真实污染源（用于计算误差指标）
        """

        if algorithm_variants is None:
            algorithm_variants = ['standard', 'adaptive', 'multi_objective']

        print(f"\n>> 开始增强版反算分析...")
        print(f"   算法变体: {', '.join(algorithm_variants)}")

        results = {}

        for variant in algorithm_variants:
            print(f"\n运行算法变体: {variant}")

            # 配置算法参数
            params = self._get_algorithm_parameters(variant)

            # 构建基于传感器分布的自适应搜索边界（大幅降低搜索难度）
            try:
                xs = [s.x for s in sensor_data]
                ys = [s.y for s in sensor_data]
                min_x, max_x = (min(xs), max(xs)) if xs else (-1000, 1000)
                min_y, max_y = (min(ys), max(ys)) if ys else (-1000, 1000)
                range_x = max_x - min_x
                range_y = max_y - min_y
                base_margin = max(150.0, 0.25 * max(range_x, range_y, 1.0))
                search_bounds = {
                    'x': (min_x - base_margin, max_x + base_margin),
                    'y': (min_y - base_margin, max_y + base_margin),
                    'z': (0.0, 100.0),
                    'q': (0.001, 50.0)
                }
            except Exception:
                search_bounds = None

            # 创建反算器
            inverter = OptimizedSourceInversion(ga_parameters=params, search_bounds=search_bounds)

            # 执行反算
            start_time = time.time()
            result = inverter.invert_source(
                sensor_data=sensor_data,
                meteo_data=meteo_data,
                true_source=true_source,
                verbose=True,
                uncertainty_analysis=True
            )

            # 记录结果
            results[variant] = result

            print(f"[完成] {variant} 完成:")
            print(f"   位置: ({result.source_x:.2f}, {result.source_y:.2f}, {result.source_z:.2f})")
            print(f"   源强: {result.emission_rate:.3f} g/s")
            print(f"   目标函数值: {result.objective_value:.2e}")
            print(f"   计算时间: {result.computation_time:.2f}s")

        return results

    def _get_algorithm_parameters(self, variant: str) -> AdaptiveGAParameters:
        """获取不同算法变体的参数"""
        base_params = {
            'population_size': self.config.population_size,
            'max_generations': self.config.max_generations,
            'use_parallel': self.config.use_parallel,
            'use_cache': self.config.use_cache
        }
        
        if variant == 'standard':
            return AdaptiveGAParameters(**base_params)
        
        elif variant == 'adaptive':
            # 使用自适应参数：调整多样性阈值和停滞阈值
            return AdaptiveGAParameters(
                **base_params,
                diversity_threshold=0.1,
                stagnation_threshold=50
            )

        elif variant == 'multi_objective':
            # 近似多目标设置：增大种群并略微减少代数，同时提高多样性
            mo_params = dict(base_params)
            mo_params['population_size'] = int(base_params['population_size'] * 1.5)
            mo_params['max_generations'] = int(base_params['max_generations'] * 0.8)
            mo_params['diversity_threshold'] = 0.15
            return AdaptiveGAParameters(**mo_params)

        else:
            return AdaptiveGAParameters(**base_params)
    
    def create_comprehensive_visualization(self,
                                         true_source: PollutionSource,
                                         meteo_data: MeteoData,
                                         sensor_data: List[OptimizedSensorData],
                                         results: Dict[str, OptimizedInversionResult],
                                         save_prefix: str = "enhanced") -> Dict[str, str]:
        """创建综合可视化"""
        
        print(f"\n>> 创建综合可视化...")
        
        saved_files = {}
        
        # 1. 浓度场对比图
        fig_concentration = self._create_concentration_comparison(
            true_source, meteo_data, sensor_data, results
        )
        concentration_path = os.path.join(self.results_dir, f"{save_prefix}_浓度场对比.png")
        fig_concentration.savefig(concentration_path, dpi=300, bbox_inches='tight')
        saved_files['concentration'] = concentration_path
        plt.close(fig_concentration)
        
        # 2. 算法性能对比图
        fig_performance = self._create_performance_comparison(results)
        performance_path = os.path.join(self.results_dir, f"{save_prefix}_算法性能对比.png")
        fig_performance.savefig(performance_path, dpi=300, bbox_inches='tight')
        saved_files['performance'] = performance_path
        plt.close(fig_performance)
        
        # 3. 3D交互式可视化
        interactive_path = self._create_interactive_3d_visualization(
            true_source, meteo_data, sensor_data, results, save_prefix
        )
        saved_files['interactive'] = interactive_path
        
        # 4. 收敛过程分析
        convergence_path = self._create_convergence_analysis(results, save_prefix)
        saved_files['convergence'] = convergence_path
        
        print(f"[完成] 可视化完成，文件保存到:")
        for key, path in saved_files.items():
            print(f"   {key}: {path}")
        
        return saved_files
    
    def _create_concentration_comparison(self, 
                                       true_source: PollutionSource,
                                       meteo_data: MeteoData,
                                       sensor_data: List[OptimizedSensorData],
                                       results: Dict[str, OptimizedInversionResult]) -> plt.Figure:
        """创建浓度场对比图"""
        
        n_results = len(results)
        fig, axes = plt.subplots(2, n_results + 1, figsize=(5 * (n_results + 1), 10))
        
        if n_results == 1:
            axes = axes.reshape(2, -1)
        
        # 真实浓度场
        self.visualizer.plot_concentration_field(
            true_source, meteo_data, sensor_data=sensor_data,
            ax=axes[0, 0], title="真实污染源"
        )
        
        # 各算法结果
        for i, (variant, result) in enumerate(results.items()):
            estimated_source = PollutionSource(
                x=result.source_x,
                y=result.source_y,
                z=result.source_z,
                emission_rate=result.emission_rate
            )
            
            self.visualizer.plot_concentration_field(
                estimated_source, meteo_data, sensor_data=sensor_data,
                ax=axes[0, i + 1], title=f"{variant}算法结果"
            )
            
            # 误差分析
            self._plot_error_analysis(true_source, result, axes[1, i + 1])
        
        # 传感器分布图
        self._plot_sensor_distribution(sensor_data, axes[1, 0])
        
        plt.tight_layout()
        return fig

    def _plot_error_analysis(self, true_source: PollutionSource, result: OptimizedInversionResult, ax):
        """绘制误差分析图"""
        # 位置误差
        pos_error = np.sqrt((true_source.x - result.source_x)**2 +
                           (true_source.y - result.source_y)**2)

        # 源强误差
        emission_error = abs(true_source.emission_rate - result.emission_rate) / true_source.emission_rate * 100

        # 创建误差条形图
        categories = ['位置误差\n(m)', '源强误差\n(%)']
        values = [pos_error, emission_error]
        colors = ['red' if v > 5 else 'orange' if v > 2 else 'green' for v in values]

        bars = ax.bar(categories, values, color=colors, alpha=0.7)
        ax.set_title('误差分析')
        ax.set_ylabel('误差值')

        # 添加数值标签
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + height*0.05,
                   f'{value:.2f}', ha='center', va='bottom')

    def _plot_sensor_distribution(self, sensor_data: List[OptimizedSensorData], ax):
        """绘制传感器分布图"""
        x_coords = [s.x for s in sensor_data]
        y_coords = [s.y for s in sensor_data]
        concentrations = [s.concentration for s in sensor_data]

        scatter = ax.scatter(x_coords, y_coords, c=concentrations,
                           cmap='viridis', s=100, alpha=0.8)

        ax.set_xlabel('X坐标 (m)')
        ax.set_ylabel('Y坐标 (m)')
        ax.set_title('传感器分布及浓度')
        ax.grid(True, alpha=0.3)

        # 添加颜色条
        plt.colorbar(scatter, ax=ax, label='浓度 (μg/m³)')

    def _create_performance_comparison(self, results: Dict[str, OptimizedInversionResult]) -> plt.Figure:
        """创建算法性能对比图"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))

        algorithms = list(results.keys())

        # 1. 计算时间对比
        times = [results[alg].computation_time for alg in algorithms]
        axes[0, 0].bar(algorithms, times, color='skyblue', alpha=0.7)
        axes[0, 0].set_title('计算时间对比')
        axes[0, 0].set_ylabel('时间 (秒)')
        axes[0, 0].tick_params(axis='x', rotation=45)

        # 2. 目标函数值对比
        obj_values = [results[alg].objective_value for alg in algorithms]
        axes[0, 1].bar(algorithms, obj_values, color='lightcoral', alpha=0.7)
        axes[0, 1].set_title('目标函数值对比')
        axes[0, 1].set_ylabel('目标函数值')
        axes[0, 1].set_yscale('log')
        axes[0, 1].tick_params(axis='x', rotation=45)

        # 3. 位置误差对比
        pos_errors = [results[alg].position_error for alg in algorithms]
        axes[1, 0].bar(algorithms, pos_errors, color='lightgreen', alpha=0.7)
        axes[1, 0].set_title('位置误差对比')
        axes[1, 0].set_ylabel('位置误差 (m)')
        axes[1, 0].tick_params(axis='x', rotation=45)

        # 4. 源强误差对比
        emission_errors = [results[alg].emission_error for alg in algorithms]
        axes[1, 1].bar(algorithms, emission_errors, color='gold', alpha=0.7)
        axes[1, 1].set_title('源强误差对比')
        axes[1, 1].set_ylabel('源强误差 (%)')
        axes[1, 1].tick_params(axis='x', rotation=45)

        plt.tight_layout()
        return fig

    def _create_interactive_3d_visualization(self,
                                           true_source: PollutionSource,
                                           meteo_data: MeteoData,
                                           sensor_data: List[OptimizedSensorData],
                                           results: Dict[str, OptimizedInversionResult],
                                           save_prefix: str) -> str:
        """创建3D交互式可视化"""

        # 创建3D浓度场
        x_range = np.linspace(-400, 400, 50)
        y_range = np.linspace(-400, 400, 50)
        X, Y = np.meshgrid(x_range, y_range)
        Z_true = np.zeros_like(X)

        # 计算真实浓度场
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                Z_true[i, j] = self.gaussian_model.calculate_concentration(
                    true_source, X[i, j], Y[i, j], 2.0, meteo_data
                )

        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['真实浓度场', '最佳算法结果', '传感器分布', '算法对比'],
            specs=[[{'type': 'surface'}, {'type': 'surface'}],
                   [{'type': 'scatter3d'}, {'type': 'bar'}]]
        )

        # 真实浓度场
        fig.add_trace(
            go.Surface(x=X, y=Y, z=Z_true, colorscale='Viridis', name='真实浓度'),
            row=1, col=1
        )

        # 最佳算法结果
        best_result = min(results.values(), key=lambda r: r.objective_value)
        best_source = PollutionSource(
            x=best_result.source_x, y=best_result.source_y,
            z=best_result.source_z, emission_rate=best_result.emission_rate
        )

        Z_estimated = np.zeros_like(X)
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                Z_estimated[i, j] = self.gaussian_model.calculate_concentration(
                    best_source, X[i, j], Y[i, j], 2.0, meteo_data
                )

        fig.add_trace(
            go.Surface(x=X, y=Y, z=Z_estimated, colorscale='Plasma', name='估计浓度'),
            row=1, col=2
        )

        # 传感器分布
        sensor_x = [s.x for s in sensor_data]
        sensor_y = [s.y for s in sensor_data]
        sensor_z = [s.concentration for s in sensor_data]

        fig.add_trace(
            go.Scatter3d(
                x=sensor_x, y=sensor_y, z=sensor_z,
                mode='markers',
                marker=dict(size=8, color=sensor_z, colorscale='Viridis'),
                name='传感器'
            ),
            row=2, col=1
        )

        # 算法对比
        algorithms = list(results.keys())
        obj_values = [results[alg].objective_value for alg in algorithms]

        fig.add_trace(
            go.Bar(x=algorithms, y=obj_values, name='目标函数值'),
            row=2, col=2
        )

        # 更新布局
        fig.update_layout(
            title='污染源溯源3D交互式分析',
            height=800,
            showlegend=True
        )

        # 保存HTML文件
        html_path = os.path.join(self.results_dir, f"{save_prefix}_3D交互式分析.html")
        fig.write_html(html_path)

        return html_path

    def _create_convergence_analysis(self, results: Dict[str, OptimizedInversionResult], save_prefix: str) -> str:
        """创建收敛过程分析"""

        fig = go.Figure()

        for algorithm, result in results.items():
            fig.add_trace(
                go.Scatter(
                    y=result.convergence_history,
                    mode='lines',
                    name=f'{algorithm}算法',
                    line=dict(width=2)
                )
            )

        fig.update_layout(
            title='算法收敛过程对比',
            xaxis_title='迭代次数',
            yaxis_title='目标函数值',
            yaxis_type='log',
            hovermode='x unified'
        )

        # 保存HTML文件
        html_path = os.path.join(self.results_dir, f"{save_prefix}_收敛分析.html")
        fig.write_html(html_path)

        return html_path

    def generate_comprehensive_report(self,
                                    true_source: PollutionSource,
                                    results: Dict[str, OptimizedInversionResult],
                                    scenario_name: str = "default") -> str:
        """生成综合分析报告"""

        report = {
            'scenario_name': scenario_name,
            'timestamp': datetime.now().isoformat(),
            'true_source': {
                'x': true_source.x,
                'y': true_source.y,
                'z': true_source.z,
                'emission_rate': true_source.emission_rate
            },
            'algorithm_results': {},
            'performance_summary': {},
            'recommendations': []
        }

        # 分析各算法结果
        best_algorithm = None
        best_score = float('inf')

        for algorithm, result in results.items():
            # 计算综合评分
            pos_error = result.position_error
            emission_error = result.emission_error
            time_penalty = result.computation_time / 60  # 时间惩罚（分钟）

            composite_score = pos_error + emission_error + time_penalty

            if composite_score < best_score:
                best_score = composite_score
                best_algorithm = algorithm

            report['algorithm_results'][algorithm] = {
                'position': [result.source_x, result.source_y, result.source_z],
                'emission_rate': result.emission_rate,
                'position_error': pos_error,
                'emission_error': emission_error,
                'computation_time': result.computation_time,
                'objective_value': result.objective_value,
                'composite_score': composite_score
            }

        # 性能总结
        # 计算平均计算时间
        average_computation_time = np.mean([r.computation_time for r in results.values()]) if results else 0.0

        report['performance_summary'] = {
            'best_algorithm': best_algorithm,
            'best_score': best_score,
            'total_algorithms_tested': len(results),
            'average_position_error': np.mean([r.position_error for r in results.values()]) if results else 0.0,
            'average_emission_error': np.mean([r.emission_error for r in results.values()]) if results else 0.0,
            'average_computation_time': float(average_computation_time),
            'total_computation_time': float(sum([r.computation_time for r in results.values()]))
        }

        # 生成建议
        if best_score < 5:
            report['recommendations'].append("算法性能优秀，建议在实际应用中使用")
        elif best_score < 10:
            report['recommendations'].append("算法性能良好，可考虑进一步优化参数")
        else:
            report['recommendations'].append("算法性能需要改进，建议调整参数或尝试其他方法")

        if report['performance_summary']['average_computation_time'] > 30:
            report['recommendations'].append("计算时间较长，建议启用并行计算或减少种群大小")

        # 保存报告
        report_path = os.path.join(self.results_dir, f"{scenario_name}_综合分析报告.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report_path

    def run_complete_analysis(self, scenario_name: str = "enhanced_demo") -> Dict:
        """运行完整分析流程"""

        print(">> 开始完整分析流程...")
        start_time = time.time()

        # 1. 创建场景
        true_source, meteo_data, sensor_data = self.create_scenario(scenario_name)

        # 2. 运行多种算法
        results = self.run_enhanced_inversion(sensor_data, meteo_data, true_source=true_source)

        # 3. 创建可视化
        visualization_files = self.create_comprehensive_visualization(
            true_source, meteo_data, sensor_data, results, scenario_name
        )

        # 4. 生成报告
        report_path = self.generate_comprehensive_report(true_source, results, scenario_name)

        total_time = time.time() - start_time

        print(f"\n>> 完整分析完成！总耗时: {total_time:.2f}秒")
        print(f">> 分析报告: {report_path}")

        return {
            'true_source': true_source,
            'meteo_data': meteo_data,
            'sensor_data': sensor_data,
            'results': results,
            'visualization_files': visualization_files,
            'report_path': report_path,
            'total_time': total_time
        }
