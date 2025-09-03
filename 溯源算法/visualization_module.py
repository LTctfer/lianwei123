"""
污染源溯源可视化模块
提供多种可视化功能：浓度场、传感器分布、收敛过程等
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from typing import List, Tuple, Optional, Dict
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from gaussian_plume_model import GaussianPlumeModel, PollutionSource, MeteoData
from optimized_source_inversion import OptimizedSensorData, OptimizedInversionResult

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class PollutionSourceVisualizer:
    """污染源溯源可视化器"""
    
    def __init__(self):
        self.gaussian_model = GaussianPlumeModel()
        
        # 自定义颜色映射
        self.concentration_cmap = LinearSegmentedColormap.from_list(
            'pollution', ['blue', 'green', 'yellow', 'orange', 'red'], N=256
        )
    
    def plot_concentration_field(self, 
                               source: PollutionSource,
                               meteo_data: MeteoData,
                               x_range: Tuple[float, float] = (-500, 500),
                               y_range: Tuple[float, float] = (-500, 500),
                               z_height: float = 2.0,
                               grid_size: int = 100,
                               sensor_data: Optional[List[OptimizedSensorData]] = None,
                               save_path: str = "可视化结果/concentration_field.png") -> plt.Figure:
        """
        绘制污染物浓度场
        
        Args:
            source: 污染源
            meteo_data: 气象数据
            x_range: x坐标范围
            y_range: y坐标范围
            z_height: 计算高度
            grid_size: 网格大小
            sensor_data: 传感器数据
            save_path: 保存路径
            
        Returns:
            matplotlib图形对象
        """
        # 计算浓度场
        X, Y, concentration_field = self.gaussian_model.calculate_concentration_field(
            source, x_range, y_range, z_height, grid_size, meteo_data
        )
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # 绘制浓度等高线和填充
        levels = np.logspace(np.log10(max(1e-3, concentration_field.min())), 
                           np.log10(concentration_field.max()), 20)
        
        contour_filled = ax.contourf(X, Y, concentration_field, levels=levels, 
                                   cmap=self.concentration_cmap, alpha=0.8)
        contour_lines = ax.contour(X, Y, concentration_field, levels=levels, 
                                 colors='black', alpha=0.3, linewidths=0.5)
        
        # 添加颜色条
        cbar = plt.colorbar(contour_filled, ax=ax, shrink=0.8)
        cbar.set_label('污染物浓度 (μg/m³)', fontsize=12)
        
        # 标记污染源位置
        ax.plot(source.x, source.y, 'r*', markersize=20, label=f'污染源 (q={source.emission_rate:.3f}g/s)')
        
        # 绘制传感器位置和观测值
        if sensor_data:
            for sensor in sensor_data:
                color = plt.cm.viridis(sensor.concentration / max(s.concentration for s in sensor_data))
                ax.plot(sensor.x, sensor.y, 'o', color=color, markersize=8, 
                       markeredgecolor='white', markeredgewidth=1)
                ax.annotate(f'{sensor.concentration:.1f}', 
                          (sensor.x, sensor.y), xytext=(5, 5), 
                          textcoords='offset points', fontsize=8,
                          bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
        
        # 绘制风向箭头
        wind_arrow_length = min(x_range[1] - x_range[0], y_range[1] - y_range[0]) * 0.1
        wind_x = wind_arrow_length * np.sin(np.radians(meteo_data.wind_direction))
        wind_y = wind_arrow_length * np.cos(np.radians(meteo_data.wind_direction))
        
        arrow_start_x = x_range[0] + (x_range[1] - x_range[0]) * 0.85
        arrow_start_y = y_range[1] - (y_range[1] - y_range[0]) * 0.15
        
        ax.arrow(arrow_start_x, arrow_start_y, wind_x, wind_y,
                head_width=20, head_length=30, fc='blue', ec='blue', alpha=0.7)
        ax.text(arrow_start_x, arrow_start_y - 50, 
               f'风向: {meteo_data.wind_direction}°\n风速: {meteo_data.wind_speed}m/s',
               fontsize=10, ha='center', 
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.7))
        
        # 设置图形属性
        ax.set_xlabel('X坐标 (m)', fontsize=12)
        ax.set_ylabel('Y坐标 (m)', fontsize=12)
        ax.set_title(f'污染物浓度分布 (高度: {z_height}m)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')
        ax.set_aspect('equal')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"浓度场图已保存至: {save_path}")
        
        return fig
    
    def plot_inversion_results(self, 
                             result: OptimizedInversionResult,
                             sensor_data: List[OptimizedSensorData],
                             meteo_data: MeteoData,
                             true_source: Optional[PollutionSource] = None,
                             save_path: str = "可视化结果/inversion_results.png") -> plt.Figure:
        """
        绘制反算结果综合图
        
        Args:
            result: 反算结果
            sensor_data: 传感器数据
            meteo_data: 气象数据
            true_source: 真实污染源
            save_path: 保存路径
            
        Returns:
            matplotlib图形对象
        """
        fig = plt.figure(figsize=(16, 12))
        
        # 创建子图布局
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. 浓度场图 (占据左上2x2区域)
        ax1 = fig.add_subplot(gs[0:2, 0:2])
        
        # 反算得到的污染源
        inverted_source = PollutionSource(
            x=result.source_x,
            y=result.source_y,
            z=result.source_z,
            emission_rate=result.emission_rate
        )
        
        # 计算浓度场
        x_range = (min(s.x for s in sensor_data) - 200, max(s.x for s in sensor_data) + 200)
        y_range = (min(s.y for s in sensor_data) - 200, max(s.y for s in sensor_data) + 200)
        
        X, Y, concentration_field = self.gaussian_model.calculate_concentration_field(
            inverted_source, x_range, y_range, 2.0, 80, meteo_data
        )
        
        levels = np.logspace(np.log10(max(1e-3, concentration_field.min())), 
                           np.log10(concentration_field.max()), 15)
        
        contour = ax1.contourf(X, Y, concentration_field, levels=levels, 
                              cmap=self.concentration_cmap, alpha=0.8)
        
        # 标记反算污染源
        ax1.plot(result.source_x, result.source_y, 'r*', markersize=15, 
                label=f'反算源 ({result.source_x:.1f}, {result.source_y:.1f})')
        
        # 标记真实污染源（如果有）
        if true_source:
            ax1.plot(true_source.x, true_source.y, 'g*', markersize=15,
                    label=f'真实源 ({true_source.x:.1f}, {true_source.y:.1f})')
        
        # 绘制传感器
        for sensor in sensor_data:
            ax1.plot(sensor.x, sensor.y, 'ko', markersize=6, markerfacecolor='white')
            ax1.text(sensor.x, sensor.y + 20, f'{sensor.concentration:.1f}', 
                    ha='center', fontsize=8)
        
        ax1.set_xlabel('X坐标 (m)')
        ax1.set_ylabel('Y坐标 (m)')
        ax1.set_title('反算结果浓度场', fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 收敛曲线
        ax2 = fig.add_subplot(gs[0, 2])
        ax2.semilogy(result.convergence_history, 'b-', linewidth=2)
        ax2.set_xlabel('迭代次数')
        ax2.set_ylabel('目标函数值')
        ax2.set_title('算法收敛过程')
        ax2.grid(True, alpha=0.3)
        
        # 3. 误差分析
        ax3 = fig.add_subplot(gs[1, 2])
        
        # 计算理论浓度vs观测浓度
        theoretical_conc = []
        observed_conc = []
        
        for sensor in sensor_data:
            theo_conc = self.gaussian_model.calculate_concentration(
                inverted_source, sensor.x, sensor.y, sensor.z, meteo_data
            )
            theoretical_conc.append(theo_conc)
            observed_conc.append(sensor.concentration)
        
        ax3.scatter(observed_conc, theoretical_conc, alpha=0.7, s=50)
        
        # 绘制理想线
        min_conc = min(min(observed_conc), min(theoretical_conc))
        max_conc = max(max(observed_conc), max(theoretical_conc))
        ax3.plot([min_conc, max_conc], [min_conc, max_conc], 'r--', alpha=0.7)
        
        ax3.set_xlabel('观测浓度 (μg/m³)')
        ax3.set_ylabel('理论浓度 (μg/m³)')
        ax3.set_title('观测vs理论浓度')
        ax3.grid(True, alpha=0.3)
        
        # 计算R²
        r_squared = np.corrcoef(observed_conc, theoretical_conc)[0, 1] ** 2
        ax3.text(0.05, 0.95, f'R² = {r_squared:.3f}', transform=ax3.transAxes,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 4. 性能指标表
        ax4 = fig.add_subplot(gs[2, :])
        ax4.axis('off')
        
        # 创建性能指标表格
        metrics_data = [
            ['反算位置', f'({result.source_x:.2f}, {result.source_y:.2f}, {result.source_z:.2f}) m'],
            ['反算源强', f'{result.emission_rate:.4f} g/s'],
            ['目标函数值', f'{result.objective_value:.2e}'],
            ['计算时间', f'{result.computation_time:.2f} s'],
            ['收敛代数', f'{result.performance_metrics.get("convergence_generations", "N/A")}'],
            ['评估次数', f'{result.performance_metrics.get("total_evaluations", "N/A")}'],
            ['缓存命中率', f'{result.performance_metrics.get("cache_hit_rate", 0):.1f}%'],
            ['评估速度', f'{result.performance_metrics.get("evaluations_per_second", 0):.1f} 次/s']
        ]
        
        if true_source:
            metrics_data.extend([
                ['位置误差', f'{result.position_error:.2f} m'],
                ['源强误差', f'{result.emission_error:.2f}%']
            ])
        
        # 绘制表格
        table = ax4.table(cellText=metrics_data,
                         colLabels=['指标', '数值'],
                         cellLoc='center',
                         loc='center',
                         colWidths=[0.3, 0.3])
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        # 设置表格样式
        for i in range(len(metrics_data) + 1):
            for j in range(2):
                cell = table[(i, j)]
                if i == 0:  # 表头
                    cell.set_facecolor('#4CAF50')
                    cell.set_text_props(weight='bold', color='white')
                else:
                    cell.set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')
        
        plt.suptitle('污染源反算结果综合分析', fontsize=16, fontweight='bold', y=0.95)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"反算结果图已保存至: {save_path}")
        
        return fig
    
    def plot_interactive_3d_concentration(self, 
                                        source: PollutionSource,
                                        meteo_data: MeteoData,
                                        sensor_data: Optional[List[OptimizedSensorData]] = None,
                                        save_path: Optional[str] = None) -> go.Figure:
        """
        创建交互式3D浓度可视化
        
        Args:
            source: 污染源
            meteo_data: 气象数据
            sensor_data: 传感器数据
            save_path: 保存路径
            
        Returns:
            plotly图形对象
        """
        # 创建3D网格
        x = np.linspace(-500, 500, 50)
        y = np.linspace(-500, 500, 50)
        z = np.linspace(1, 50, 20)
        
        X, Y, Z = np.meshgrid(x, y, z)
        
        # 计算3D浓度场
        concentration_3d = np.zeros_like(X)
        
        for i in range(len(x)):
            for j in range(len(y)):
                for k in range(len(z)):
                    concentration_3d[j, i, k] = self.gaussian_model.calculate_concentration(
                        source, X[j, i, k], Y[j, i, k], Z[j, i, k], meteo_data
                    )
        
        # 创建3D等值面
        fig = go.Figure()
        
        # 添加多个等值面
        max_conc = concentration_3d.max()
        isosurface_values = [max_conc * 0.1, max_conc * 0.3, max_conc * 0.5, max_conc * 0.7]
        colors = ['blue', 'green', 'yellow', 'red']
        
        for i, (value, color) in enumerate(zip(isosurface_values, colors)):
            fig.add_trace(go.Isosurface(
                x=X.flatten(),
                y=Y.flatten(),
                z=Z.flatten(),
                value=concentration_3d.flatten(),
                isomin=value,
                isomax=value,
                surface_count=1,
                colorscale=[[0, color], [1, color]],
                opacity=0.3,
                name=f'浓度 {value:.2f} μg/m³'
            ))
        
        # 添加污染源标记
        fig.add_trace(go.Scatter3d(
            x=[source.x],
            y=[source.y],
            z=[source.z],
            mode='markers',
            marker=dict(size=10, color='red', symbol='diamond'),
            name='污染源'
        ))
        
        # 添加传感器标记
        if sensor_data:
            sensor_x = [s.x for s in sensor_data]
            sensor_y = [s.y for s in sensor_data]
            sensor_z = [s.z for s in sensor_data]
            sensor_conc = [s.concentration for s in sensor_data]
            
            fig.add_trace(go.Scatter3d(
                x=sensor_x,
                y=sensor_y,
                z=sensor_z,
                mode='markers',
                marker=dict(
                    size=8,
                    color=sensor_conc,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="观测浓度 (μg/m³)")
                ),
                text=[f'传感器{s.sensor_id}: {s.concentration:.2f}' for s in sensor_data],
                name='传感器'
            ))
        
        # 设置布局 - 自适应浏览器大小
        fig.update_layout(
            title={
                'text': '3D污染物浓度分布',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            scene=dict(
                xaxis_title='X坐标 (m)',
                yaxis_title='Y坐标 (m)',
                zaxis_title='高度 (m)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                ),
                aspectmode='cube'  # 保持比例
            ),
            # 移除固定宽高，使用自适应
            autosize=True,
            margin=dict(l=0, r=0, t=50, b=0),
            # 添加响应式配置
            font=dict(size=12),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )

        # 添加响应式配置
        config = {
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
            'responsive': True,  # 关键：启用响应式
            'toImageButtonOptions': {
                'format': 'png',
                'filename': '3D污染物浓度分布',
                'height': 800,
                'width': 1200,
                'scale': 2
            }
        }
        
        if save_path:
            # 使用响应式配置保存HTML
            fig.write_html(
                save_path,
                config=config,
                include_plotlyjs='cdn',  # 使用CDN加载plotly.js，减小文件大小
                div_id="pollution-3d-viz"
            )

            # 添加自定义CSS和JavaScript来增强响应式效果
            self._enhance_html_responsiveness(save_path)
            print(f"3D交互图已保存至: {save_path}")

        return fig

    def _enhance_html_responsiveness(self, html_path: str):
        """增强HTML文件的响应式效果"""
        try:
            # 读取生成的HTML文件
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # 添加响应式CSS和JavaScript
            responsive_code = """
<style>
    /* 响应式样式 */
    body {
        margin: 0;
        padding: 10px;
        font-family: Arial, sans-serif;
        background-color: #f5f5f5;
    }

    .plotly-graph-div {
        width: 100% !important;
        height: calc(100vh - 40px) !important;
        min-height: 600px;
        max-height: none !important;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: white;
    }

    /* 移动设备适配 */
    @media (max-width: 768px) {
        body {
            padding: 5px;
        }

        .plotly-graph-div {
            height: calc(100vh - 20px) !important;
            min-height: 400px;
        }

        /* 调整图例位置 */
        .legend {
            font-size: 10px !important;
        }
    }

    /* 平板设备适配 */
    @media (min-width: 769px) and (max-width: 1024px) {
        .plotly-graph-div {
            height: calc(100vh - 30px) !important;
            min-height: 500px;
        }
    }

    /* 大屏幕适配 */
    @media (min-width: 1200px) {
        .plotly-graph-div {
            height: calc(100vh - 50px) !important;
            min-height: 700px;
        }
    }

    /* 工具栏样式优化 */
    .modebar {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
</style>

<script>
    // 响应式JavaScript
    window.addEventListener('load', function() {
        // 监听窗口大小变化
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(function() {
                // 重新调整图表大小
                const plotDiv = document.querySelector('.plotly-graph-div');
                if (plotDiv && window.Plotly) {
                    window.Plotly.Plots.resize(plotDiv);
                }
            }, 250);
        });

        // 初始化时调整大小
        setTimeout(function() {
            const plotDiv = document.querySelector('.plotly-graph-div');
            if (plotDiv && window.Plotly) {
                window.Plotly.Plots.resize(plotDiv);
            }
        }, 1000);

        // 添加全屏功能
        const plotDiv = document.querySelector('.plotly-graph-div');
        if (plotDiv) {
            plotDiv.addEventListener('dblclick', function() {
                if (document.fullscreenElement) {
                    document.exitFullscreen();
                } else {
                    plotDiv.requestFullscreen().catch(err => {
                        console.log('无法进入全屏模式:', err);
                    });
                }
            });
        }
    });

    // 添加页面标题
    document.title = '3D污染物浓度分布 - 交互式可视化';
</script>
"""

            # 在</head>标签前插入响应式代码
            if '</head>' in html_content:
                html_content = html_content.replace('</head>', responsive_code + '\n</head>')
            else:
                # 如果没有head标签，在body开始后插入
                html_content = html_content.replace('<body>', '<body>\n' + responsive_code)

            # 写回文件
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

        except Exception as e:
            print(f"增强响应式效果时出错: {e}")

    def create_responsive_3d_template(self, save_path: str) -> str:
        """创建响应式3D可视化模板"""
        template_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D污染物浓度分布 - 交互式可视化</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 10px;
        }

        .container {
            max-width: 100%;
            height: calc(100vh - 20px);
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .header {
            background: linear-gradient(90deg, #4CAF50, #45a049);
            color: white;
            padding: 15px 20px;
            text-align: center;
        }

        .header h1 {
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }

        .plot-container {
            flex: 1;
            position: relative;
            min-height: 0;
        }

        #plotDiv {
            width: 100%;
            height: 100%;
        }

        .controls {
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 1000;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .control-btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 8px 12px;
            margin: 2px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: background 0.3s;
        }

        .control-btn:hover {
            background: #45a049;
        }

        /* 响应式设计 */
        @media (max-width: 768px) {
            body {
                padding: 5px;
            }

            .container {
                height: calc(100vh - 10px);
                border-radius: 8px;
            }

            .header {
                padding: 10px 15px;
            }

            .header h1 {
                font-size: 18px;
            }

            .controls {
                top: 5px;
                right: 5px;
                padding: 5px;
            }

            .control-btn {
                padding: 6px 8px;
                font-size: 10px;
            }
        }

        @media (max-width: 480px) {
            .controls {
                position: relative;
                top: auto;
                right: auto;
                margin: 5px;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>3D污染物浓度分布交互式可视化</h1>
        </div>
        <div class="plot-container">
            <div class="controls">
                <button class="control-btn" onclick="resetView()">重置视角</button>
                <button class="control-btn" onclick="toggleFullscreen()">全屏</button>
                <button class="control-btn" onclick="downloadImage()">下载图片</button>
            </div>
            <div id="plotDiv"></div>
        </div>
    </div>

    <script>
        // 这里将插入Plotly图表数据
        // PLOTLY_DATA_PLACEHOLDER

        // 控制函数
        function resetView() {
            Plotly.relayout('plotDiv', {
                'scene.camera': {
                    eye: {x: 1.5, y: 1.5, z: 1.5}
                }
            });
        }

        function toggleFullscreen() {
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                document.documentElement.requestFullscreen();
            }
        }

        function downloadImage() {
            Plotly.downloadImage('plotDiv', {
                format: 'png',
                width: 1200,
                height: 800,
                filename: '3D污染物浓度分布'
            });
        }

        // 响应式处理
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(function() {
                Plotly.Plots.resize('plotDiv');
            }, 250);
        });

        // 初始化完成后调整大小
        window.addEventListener('load', function() {
            setTimeout(function() {
                Plotly.Plots.resize('plotDiv');
            }, 500);
        });
    </script>
</body>
</html>
"""
        return template_html

    def plot_responsive_3d_concentration(self,
                                       source: PollutionSource,
                                       meteo_data: MeteoData,
                                       sensor_data: List,
                                       save_path: str = None) -> go.Figure:
        """
        创建完全响应式的3D浓度可视化

        Args:
            source: 污染源对象
            meteo_data: 气象数据
            sensor_data: 传感器数据列表
            save_path: 保存路径

        Returns:
            Plotly图形对象
        """
        # 创建基础3D图形
        fig = self.plot_interactive_3d_concentration(source, meteo_data, sensor_data)

        # 更新布局为完全响应式
        fig.update_layout(
            title={
                'text': '3D污染物浓度分布 - 响应式可视化',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': '#2c3e50'}
            },
            scene=dict(
                xaxis_title='X坐标 (m)',
                yaxis_title='Y坐标 (m)',
                zaxis_title='高度 (m)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                ),
                aspectmode='cube',
                bgcolor='rgba(240, 240, 240, 0.1)'
            ),
            autosize=True,
            margin=dict(l=0, r=0, t=60, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12, color='#2c3e50'),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.95,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1
            )
        )

        if save_path:
            # 创建完全自定义的响应式HTML
            self._create_custom_responsive_html(fig, save_path)
            print(f"响应式3D交互图已保存至: {save_path}")

        return fig

    def _create_custom_responsive_html(self, fig: go.Figure, save_path: str):
        """创建自定义的响应式HTML文件"""
        # 获取图形的JSON数据
        fig_json = fig.to_json()

        # 创建完整的响应式HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>3D污染物浓度分布 - 响应式交互可视化</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        html, body {{
            height: 100%;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            overflow: hidden;
            -webkit-overflow-scrolling: touch; /* iOS平滑滚动 */
        }}

        .main-container {{
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
            padding: 10px;
        }}

        .header {{
            background: linear-gradient(90deg, #4CAF50, #45a049);
            color: white;
            padding: 15px 20px;
            text-align: center;
            border-radius: 12px 12px 0 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}

        .header h1 {{
            margin: 0;
            font-size: clamp(16px, 4vw, 24px);
            font-weight: 600;
        }}

        .plot-wrapper {{
            flex: 1;
            background: white;
            border-radius: 0 0 12px 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
            min-height: 0;
        }}

        #plotDiv {{
            width: 100%;
            height: 100%;
            min-height: 300px; /* 确保最小高度 */
            position: relative;
        }}

        .controls {{
            position: absolute;
            top: 15px;
            right: 15px;
            z-index: 1000;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            backdrop-filter: blur(10px);
        }}

        .control-btn {{
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 8px 12px;
            margin: 2px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}

        .control-btn:hover {{
            background: linear-gradient(45deg, #45a049, #3d8b40);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }}

        .control-btn:active {{
            transform: translateY(0);
        }}

        .info-panel {{
            position: absolute;
            bottom: 15px;
            left: 15px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 8px;
            padding: 10px;
            font-size: 12px;
            color: #2c3e50;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            backdrop-filter: blur(10px);
            max-width: 250px;
        }}

        /* 响应式断点 */
        @media (max-width: 768px) {{
            .main-container {{
                padding: 5px;
            }}

            .header {{
                padding: 10px 15px;
                border-radius: 8px 8px 0 0;
            }}

            .plot-wrapper {{
                border-radius: 0 0 8px 8px;
            }}

            .controls {{
                top: 10px;
                right: 10px;
                padding: 8px;
            }}

            .control-btn {{
                padding: 6px 8px;
                font-size: 10px;
                margin: 1px;
            }}

            .info-panel {{
                bottom: 10px;
                left: 10px;
                padding: 8px;
                font-size: 10px;
                max-width: 200px;
            }}
        }}

        @media (max-width: 480px) {{
            .main-container {{
                padding: 2px;
            }}

            .controls {{
                position: relative;
                top: auto;
                right: auto;
                margin: 5px;
                text-align: center;
                background: rgba(255, 255, 255, 0.9);
            }}

            .info-panel {{
                position: relative;
                bottom: auto;
                left: auto;
                margin: 5px;
                max-width: none;
            }}
        }}

        /* 加载动画 */
        .loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            color: #4CAF50;
            font-size: 18px;
        }}

        .spinner {{
            border: 3px solid #f3f3f3;
            border-top: 3px solid #4CAF50;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        /* 隐藏类 */
        .hidden {{
            display: none;
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <div class="header">
            <h1>🌍 3D污染物浓度分布 - 交互式可视化</h1>
        </div>
        <div class="plot-wrapper">
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <div>正在加载3D可视化...</div>
            </div>
            <div class="controls">
                <button class="control-btn" onclick="resetView()" title="重置视角">🔄 重置</button>
                <button class="control-btn" onclick="toggleFullscreen()" title="全屏显示">⛶ 全屏</button>
                <button class="control-btn" onclick="downloadImage()" title="下载图片">📷 下载</button>
                <button class="control-btn" onclick="toggleInfo()" title="显示/隐藏信息">ℹ️ 信息</button>
            </div>
            <div class="info-panel" id="infoPanel">
                <strong>操作说明:</strong><br>
                • 鼠标拖拽: 旋转视角<br>
                • 滚轮: 缩放<br>
                • 双击: 全屏切换<br>
                • 悬停: 查看数值
            </div>
            <div id="plotDiv"></div>
        </div>
    </div>

    <script>
        // 图形数据
        const figData = {fig_json};

        // 响应式配置
        const config = {{
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
            responsive: true,
            toImageButtonOptions: {{
                format: 'png',
                filename: '3D污染物浓度分布',
                height: 1000,
                width: 1400,
                scale: 2
            }}
        }};

        // 初始化图表
        function initPlot() {{
            const plotDiv = document.getElementById('plotDiv');
            const loading = document.getElementById('loading');

            Plotly.newPlot(plotDiv, figData.data, figData.layout, config)
                .then(function() {{
                    loading.classList.add('hidden');
                    console.log('3D可视化加载完成');
                }})
                .catch(function(err) {{
                    console.error('加载失败:', err);
                    loading.innerHTML = '<div style="color: red;">加载失败，请刷新页面重试</div>';
                }});
        }}

        // 控制函数
        function resetView() {{
            Plotly.relayout('plotDiv', {{
                'scene.camera': {{
                    eye: {{x: 1.5, y: 1.5, z: 1.5}}
                }}
            }});
        }}

        function toggleFullscreen() {{
            if (document.fullscreenElement) {{
                document.exitFullscreen();
            }} else {{
                document.documentElement.requestFullscreen().catch(err => {{
                    console.log('无法进入全屏模式:', err);
                }});
            }}
        }}

        function downloadImage() {{
            Plotly.downloadImage('plotDiv', {{
                format: 'png',
                width: 1400,
                height: 1000,
                filename: '3D污染物浓度分布_' + new Date().toISOString().slice(0,10)
            }});
        }}

        function toggleInfo() {{
            const infoPanel = document.getElementById('infoPanel');
            infoPanel.style.display = infoPanel.style.display === 'none' ? 'block' : 'none';
        }}

        // 增强的响应式处理
        let resizeTimeout;
        let orientationTimeout;

        function handleResize() {{
            const plotDiv = document.getElementById('plotDiv');
            if (plotDiv && window.Plotly) {{
                // 强制重新计算布局
                Plotly.Plots.resize(plotDiv);

                // 针对移动设备的额外处理
                if (window.innerWidth <= 768) {{
                    Plotly.relayout(plotDiv, {{
                        'scene.camera.eye': {{x: 2, y: 2, z: 1.5}}, // 调整移动端视角
                        'legend.orientation': 'h',
                        'legend.x': 0,
                        'legend.y': -0.1
                    }});
                }} else {{
                    Plotly.relayout(plotDiv, {{
                        'scene.camera.eye': {{x: 1.5, y: 1.5, z: 1.5}},
                        'legend.orientation': 'v',
                        'legend.x': 1.02,
                        'legend.y': 0.95
                    }});
                }}
            }}
        }}

        // 窗口大小变化
        window.addEventListener('resize', function() {{
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(handleResize, 250);
        }});

        // 设备方向变化（移动设备）
        window.addEventListener('orientationchange', function() {{
            clearTimeout(orientationTimeout);
            orientationTimeout = setTimeout(function() {{
                handleResize();
                // 方向变化后额外延迟调整
                setTimeout(handleResize, 500);
            }}, 100);
        }});

        // 视口变化检测
        if (window.visualViewport) {{
            window.visualViewport.addEventListener('resize', function() {{
                clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(handleResize, 250);
            }});
        }}

        // 双击全屏
        document.getElementById('plotDiv').addEventListener('dblclick', toggleFullscreen);

        // 页面加载完成后初始化
        window.addEventListener('load', function() {{
            initPlot();

            // 延迟调整大小确保正确渲染
            setTimeout(function() {{
                const plotDiv = document.getElementById('plotDiv');
                if (plotDiv && window.Plotly) {{
                    Plotly.Plots.resize(plotDiv);
                }}
            }}, 1000);
        }});

        // 防止页面意外关闭
        window.addEventListener('beforeunload', function(e) {{
            e.preventDefault();
            e.returnValue = '';
        }});
    </script>
</body>
</html>
"""

        # 保存文件
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
