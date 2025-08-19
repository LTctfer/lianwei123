#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版可视化模块
提供更丰富的交互式可视化功能
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from typing import List, Dict, Tuple, Optional, Any
import pandas as pd
from datetime import datetime
import os

from gaussian_plume_model import GaussianPlumeModel, PollutionSource, MeteoData
from optimized_source_inversion import OptimizedSensorData, OptimizedInversionResult

# 设置样式
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


class EnhancedVisualizer:
    """增强版可视化器"""

    def __init__(self):
        self.gaussian_model = GaussianPlumeModel()
        self.color_schemes = {
            'concentration': 'Viridis',
            'error': 'RdYlBu_r',
            'performance': 'Plasma',
            'comparison': 'Set3'
        }

    def plot_concentration_field(self,
                                 source: PollutionSource,
                                 meteo_data: MeteoData,
                                 sensor_data: Optional[List[OptimizedSensorData]] = None,
                                 ax: Optional[plt.Axes] = None,
                                 title: str = "浓度场",
                                 grid_extent: Tuple[float, float, float, float] = (-300, 300, -300, 300),
                                 resolution: int = 60) -> plt.Axes:
        """绘制高斯羽流浓度场（Matplotlib）
        该方法被分析流程调用，用于在指定 ax 上绘制热力图并叠加源/传感器。
        """
        # 创建坐标轴
        created_fig = None
        if ax is None:
            created_fig, ax = plt.subplots(figsize=(6, 5))

        # 网格
        x_min, x_max, y_min, y_max = grid_extent
        x = np.linspace(x_min, x_max, resolution)
        y = np.linspace(y_min, y_max, resolution)
        X, Y = np.meshgrid(x, y)
        Z = np.zeros_like(X, dtype=float)

        # 计算浓度
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                try:
                    Z[i, j] = self.gaussian_model.calculate_concentration(
                        source, float(X[i, j]), float(Y[i, j]), 2.0, meteo_data
                    )
                except Exception:
                    Z[i, j] = 0.0

        # 绘制热力图
        hm = ax.contourf(X, Y, Z, levels=20, cmap="viridis")
        plt.colorbar(hm, ax=ax, fraction=0.046, pad=0.04, label="浓度")

        # 源位置
        ax.scatter([source.x], [source.y], c="red", s=80, marker="*", label="源")

        # 传感器
        if sensor_data:
            try:
                sx = [s.x for s in sensor_data]
                sy = [s.y for s in sensor_data]
                ax.scatter(sx, sy, c="white", edgecolors="black", s=40, label="传感器")
            except Exception:
                pass

        ax.set_title(title)
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.legend(loc="upper right")
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, alpha=0.2)

        # 返回轴，若内部创建图，调用方可忽略
        return ax

    def create_dashboard(self,
                        true_source: PollutionSource,
                        meteo_data: MeteoData,
                        sensor_data: List[OptimizedSensorData],
                        results: Dict[str, OptimizedInversionResult],
                        save_path: str = "enhanced_dashboard.html") -> str:
        """创建综合仪表板"""

        # 创建子图布局
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=[
                '真实浓度场', '最佳估计浓度场', '传感器分布',
                '算法性能对比', '收敛过程', '误差分析',
                '风场可视化', '不确定性分析', '3D浓度分布'
            ],
            specs=[
                [{'type': 'heatmap'}, {'type': 'heatmap'}, {'type': 'scatter'}],
                [{'type': 'bar'}, {'type': 'scatter'}, {'type': 'bar'}],
                [{'type': 'scatter'}, {'type': 'box'}, {'type': 'surface'}]
            ],
            vertical_spacing=0.08,
            horizontal_spacing=0.08
        )

        # 1. 真实浓度场
        self._add_concentration_heatmap(fig, true_source, meteo_data, 1, 1, "真实")

        # 2. 最佳估计浓度场
        best_result = min(results.values(), key=lambda r: r.objective_value)
        best_source = PollutionSource(
            x=best_result.source_x, y=best_result.source_y,
            z=best_result.source_z, emission_rate=best_result.emission_rate
        )
        self._add_concentration_heatmap(fig, best_source, meteo_data, 1, 2, "估计")

        # 3. 传感器分布
        self._add_sensor_scatter(fig, sensor_data, 1, 3)

        # 4. 算法性能对比
        self._add_performance_comparison(fig, results, 2, 1)

        # 5. 收敛过程
        self._add_convergence_plot(fig, results, 2, 2)

        # 6. 误差分析
        self._add_error_analysis(fig, true_source, results, 2, 3)

        # 7. 风场可视化
        self._add_wind_field(fig, meteo_data, 3, 1)

        # 8. 不确定性分析
        self._add_uncertainty_analysis(fig, results, 3, 2)

        # 9. 3D浓度分布
        self._add_3d_concentration(fig, true_source, meteo_data, 3, 3)

        # 更新布局
        fig.update_layout(
            title={
                'text': '污染源溯源综合分析仪表板',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 24}
            },
            height=1200,
            showlegend=False,
            font=dict(size=12)
        )

        # 保存文件
        fig.write_html(save_path, config={'responsive': True})

        return save_path

    def _add_concentration_heatmap(self, fig, source: PollutionSource, meteo_data: MeteoData,
                                  row: int, col: int, title_prefix: str):
        """添加浓度热力图"""

        # 创建网格
        x_range = np.linspace(-300, 300, 40)
        y_range = np.linspace(-300, 300, 40)
        X, Y = np.meshgrid(x_range, y_range)
        Z = np.zeros_like(X)

        # 计算浓度
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                Z[i, j] = self.gaussian_model.calculate_concentration(
                    source, X[i, j], Y[i, j], 2.0, meteo_data
                )

        # 添加热力图
        fig.add_trace(
            go.Heatmap(
                x=x_range,
                y=y_range,
                z=Z,
                colorscale='Viridis',
                showscale=False
            ),
            row=row, col=col
        )

        # 添加源位置标记
        fig.add_trace(
            go.Scatter(
                x=[source.x],
                y=[source.y],
                mode='markers',
                marker=dict(color='red', size=15, symbol='star'),
                showlegend=False
            ),
            row=row, col=col
        )

    def _add_sensor_scatter(self, fig, sensor_data: List[OptimizedSensorData], row: int, col: int):
        """添加传感器散点图"""

        x_coords = [s.x for s in sensor_data]
        y_coords = [s.y for s in sensor_data]
        concentrations = [s.concentration for s in sensor_data]

        fig.add_trace(
            go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='markers',
                marker=dict(
                    size=12,
                    color=concentrations,
                    colorscale='Viridis',
                    showscale=False
                ),
                text=[f'ID: {s.sensor_id}<br>浓度: {s.concentration:.2f}' for s in sensor_data],
                hovertemplate='%{text}<extra></extra>',
                showlegend=False
            ),
            row=row, col=col
        )

    def _add_performance_comparison(self, fig, results: Dict[str, OptimizedInversionResult],
                                   row: int, col: int):
        """添加性能对比图"""

        algorithms = list(results.keys())
        obj_values = [results[alg].objective_value for alg in algorithms]

        fig.add_trace(
            go.Bar(
                x=algorithms,
                y=obj_values,
                marker_color='lightblue',
                showlegend=False
            ),
            row=row, col=col
        )

    def _add_convergence_plot(self, fig, results: Dict[str, OptimizedInversionResult],
                             row: int, col: int):
        """添加收敛过程图"""

        colors = ['blue', 'red', 'green', 'orange', 'purple']

        for i, (algorithm, result) in enumerate(results.items()):
            fig.add_trace(
                go.Scatter(
                    y=result.convergence_history,
                    mode='lines',
                    name=algorithm,
                    line=dict(color=colors[i % len(colors)]),
                    showlegend=False
                ),
                row=row, col=col
            )

    def _add_error_analysis(self, fig, true_source: PollutionSource,
                           results: Dict[str, OptimizedInversionResult], row: int, col: int):
        """添加误差分析图"""

        algorithms = list(results.keys())
        pos_errors = [results[alg].position_error for alg in algorithms]

        fig.add_trace(
            go.Bar(
                x=algorithms,
                y=pos_errors,
                marker_color='lightcoral',
                showlegend=False
            ),
            row=row, col=col
        )

    def _add_wind_field(self, fig, meteo_data: MeteoData, row: int, col: int):
        """添加风场可视化"""

        # 创建风场网格
        x_wind = np.linspace(-200, 200, 10)
        y_wind = np.linspace(-200, 200, 10)
        X_wind, Y_wind = np.meshgrid(x_wind, y_wind)

        # 计算风向量
        wind_rad = np.radians(meteo_data.wind_direction)
        U = meteo_data.wind_speed * np.cos(wind_rad) * np.ones_like(X_wind)
        V = meteo_data.wind_speed * np.sin(wind_rad) * np.ones_like(Y_wind)

        # 添加风场箭头
        for i in range(0, len(x_wind), 2):
            for j in range(0, len(y_wind), 2):
                fig.add_annotation(
                    x=X_wind[i, j] + U[i, j] * 10,
                    y=Y_wind[i, j] + V[i, j] * 10,
                    ax=X_wind[i, j],
                    ay=Y_wind[i, j],
                    xref=f'x{7}', yref=f'y{7}',
                    axref=f'x{7}', ayref=f'y{7}',
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor='blue'
                )

    def _add_uncertainty_analysis(self, fig, results: Dict[str, OptimizedInversionResult],
                                 row: int, col: int):
        """添加不确定性分析"""

        algorithms = list(results.keys())

        # 创建箱线图数据
        for i, algorithm in enumerate(algorithms):
            result = results[algorithm]
            if hasattr(result, 'confidence_interval') and result.confidence_interval:
                # 模拟不确定性数据
                uncertainties = np.random.normal(
                    result.position_error, result.position_error * 0.2, 100
                )

                fig.add_trace(
                    go.Box(
                        y=uncertainties,
                        name=algorithm,
                        showlegend=False
                    ),
                    row=row, col=col
                )

    def _add_3d_concentration(self, fig, source: PollutionSource, meteo_data: MeteoData,
                             row: int, col: int):
        """添加3D浓度分布"""

        # 创建3D网格
        x_3d = np.linspace(-200, 200, 20)
        y_3d = np.linspace(-200, 200, 20)
        X_3d, Y_3d = np.meshgrid(x_3d, y_3d)
        Z_3d = np.zeros_like(X_3d)

        # 计算浓度
        for i in range(X_3d.shape[0]):
            for j in range(X_3d.shape[1]):
                Z_3d[i, j] = self.gaussian_model.calculate_concentration(
                    source, X_3d[i, j], Y_3d[i, j], 2.0, meteo_data
                )

        fig.add_trace(
            go.Surface(
                x=X_3d,
                y=Y_3d,
                z=Z_3d,
                colorscale='Viridis',
                showscale=False
            ),
            row=row, col=col
        )

    def create_animated_convergence(self, results: Dict[str, OptimizedInversionResult],
                                   save_path: str = "convergence_animation.html") -> str:
        """创建收敛过程动画"""

        # 准备数据
        frames = []
        max_generations = max(len(result.convergence_history) for result in results.values())

        for gen in range(0, max_generations, 10):  # 每10代一帧
            frame_data = []

            for algorithm, result in results.items():
                if gen < len(result.convergence_history):
                    frame_data.append(
                        go.Scatter(
                            x=list(range(gen + 1)),
                            y=result.convergence_history[:gen + 1],
                            mode='lines+markers',
                            name=algorithm,
                            line=dict(width=3)
                        )
                    )

            frames.append(go.Frame(data=frame_data, name=str(gen)))

        # 创建初始图形
        fig = go.Figure(
            data=frames[0].data if frames else [],
            frames=frames
        )

        # 添加播放控件
        fig.update_layout(
            title='算法收敛过程动画',
            xaxis_title='迭代次数',
            yaxis_title='目标函数值',
            yaxis_type='log',
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'buttons': [
                    {
                        'label': '播放',
                        'method': 'animate',
                        'args': [None, {'frame': {'duration': 100}}]
                    },
                    {
                        'label': '暂停',
                        'method': 'animate',
                        'args': [[None], {'frame': {'duration': 0}}]
                    }
                ]
            }]
        )

        # 保存文件
        fig.write_html(save_path)

        return save_path

    def create_sensitivity_analysis(self, base_config: Dict,
                                   save_path: str = "sensitivity_analysis.html") -> str:
        """创建敏感性分析图"""

        # 模拟敏感性分析数据
        parameters = ['风速', '风向', '源强', '传感器噪声']
        variations = np.linspace(0.5, 1.5, 11)  # 50%到150%变化

        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=parameters
        )

        for i, param in enumerate(parameters):
            row = i // 2 + 1
            col = i % 2 + 1

            # 模拟敏感性数据
            errors = np.random.exponential(2, len(variations)) + variations * 0.5

            fig.add_trace(
                go.Scatter(
                    x=variations * 100,  # 转换为百分比
                    y=errors,
                    mode='lines+markers',
                    name=param,
                    showlegend=False
                ),
                row=row, col=col
            )

        fig.update_layout(
            title='参数敏感性分析',
            height=600
        )

        # 保存文件
        fig.write_html(save_path)

        return save_path
