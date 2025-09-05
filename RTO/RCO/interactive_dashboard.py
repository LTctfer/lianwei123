#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式可视化大屏
使用Plotly创建交互式Web界面
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any
from pathlib import Path
import warnings

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    print("⚠️ Plotly未安装，使用matplotlib替代方案")
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTLY_AVAILABLE = False
    
# matplotlib作为后备方案，始终导入
# import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

class InteractiveDashboard:
    """交互式仪表板"""
    
    def __init__(self):
        # 配色方案
        self.colors = {
            'primary': '#00D4FF',
            'secondary': '#FF6B35', 
            'success': '#00E676',
            'warning': '#FFD600',
            'danger': '#FF1744',
            'background': '#0A0E27',
            'surface': '#1A1F3A',
            'text': '#FFFFFF'
        }
        
        self.severity_colors = {
            'low': '#00E676',
            'medium': '#FFD600',
            'high': '#FF6B35', 
            'critical': '#FF1744'
        }
    
    def create_gauge_chart(self, value, max_value, title, unit=''):
        """创建仪表盘图表"""
        if not PLOTLY_AVAILABLE:
            return self._create_matplotlib_gauge(value, max_value, title, unit)
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = value,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"{title} ({unit})"},
            delta = {'reference': max_value * 0.8},
            gauge = {
                'axis': {'range': [None, max_value]},
                'bar': {'color': self.colors['primary']},
                'steps': [
                    {'range': [0, max_value * 0.6], 'color': self.colors['success']},
                    {'range': [max_value * 0.6, max_value * 0.8], 'color': self.colors['warning']},
                    {'range': [max_value * 0.8, max_value], 'color': self.colors['danger']}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_value * 0.9
                }
            }
        ))
        
        fig.update_layout(
            paper_bgcolor=self.colors['background'],
            plot_bgcolor=self.colors['background'],
            font={'color': self.colors['text']}
        )
        
        return fig
    
    def create_violation_timeline(self, violations):
        """创建违规时间线"""
        if not violations:
            return None
        
        if not PLOTLY_AVAILABLE:
            return self._create_matplotlib_timeline(violations)
        
        df = pd.DataFrame(violations)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        fig = px.scatter(df, x='timestamp', y='rule_name', 
                        color='severity', size_max=15,
                        color_discrete_map=self.severity_colors,
                        title='违规事件时间线')
        
        fig.update_layout(
            paper_bgcolor=self.colors['background'],
            plot_bgcolor=self.colors['background'],
            font={'color': self.colors['text']},
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
        )
        
        return fig
    
    def create_3d_violation_analysis(self, violations):
        """创建3D违规分析图"""
        if not violations or not PLOTLY_AVAILABLE:
            return None
        
        df = pd.DataFrame(violations)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        
        # 按小时和严重程度聚合
        pivot_data = df.groupby(['hour', 'severity']).size().reset_index(name='count')
        
        fig = go.Figure(data=[go.Scatter3d(
            x=pivot_data['hour'],
            y=pivot_data['severity'], 
            z=pivot_data['count'],
            mode='markers',
            marker=dict(
                size=pivot_data['count'] * 5,
                color=pivot_data['count'],
                colorscale='Viridis',
                opacity=0.8
            ),
            text=[f'小时: {h}<br>严重程度: {s}<br>数量: {c}' 
                  for h, s, c in zip(pivot_data['hour'], pivot_data['severity'], pivot_data['count'])],
            hovertemplate='%{text}<extra></extra>'
        )])
        
        fig.update_layout(
            title='3D违规分析 - 时间/严重程度/数量',
            scene=dict(
                xaxis_title='小时',
                yaxis_title='严重程度',
                zaxis_title='违规数量',
                bgcolor=self.colors['background']
            ),
            paper_bgcolor=self.colors['background'],
            font={'color': self.colors['text']}
        )
        
        return fig
    
    def create_radar_chart(self, summary):
        """创建雷达图"""
        if not summary.get('by_equipment') or not PLOTLY_AVAILABLE:
            return None
        
        equipment = list(summary['by_equipment'].keys())
        values = list(summary['by_equipment'].values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=equipment,
            fill='toself',
            name='违规次数',
            line_color=self.colors['primary'],
            fillcolor=f"rgba(0, 212, 255, 0.3)"
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(values) * 1.2] if values else [0, 10]
                )),
            title="设备违规雷达图",
            paper_bgcolor=self.colors['background'],
            font={'color': self.colors['text']}
        )
        
        return fig
    
    def create_heatmap(self, violations):
        """创建热力图"""
        if not violations or not PLOTLY_AVAILABLE:
            return None
        
        df = pd.DataFrame(violations)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day'] = df['timestamp'].dt.day
        
        # 创建热力图数据
        heatmap_data = df.groupby(['day', 'hour']).size().reset_index(name='count')
        heatmap_pivot = heatmap_data.pivot(index='day', columns='hour', values='count').fillna(0)
        
        # 确保所有24小时都有列，即使没有数据
        all_hours = list(range(24))
        for hour in all_hours:
            if hour not in heatmap_pivot.columns:
                heatmap_pivot[hour] = 0
        
        # 按小时排序列
        heatmap_pivot = heatmap_pivot.reindex(columns=sorted(heatmap_pivot.columns))
        
        # 如果没有数据，创建一个默认的热力图
        if heatmap_pivot.empty:
            # 创建一个示例数据
            import numpy as np
            demo_data = np.random.poisson(2, (7, 24))  # 7天24小时的示例数据
            heatmap_pivot = pd.DataFrame(demo_data, 
                                       index=range(1, 8), 
                                       columns=range(24))
        
        fig = px.imshow(heatmap_pivot,
                       labels=dict(x="小时", y="日期", color="违规次数"),
                       x=list(heatmap_pivot.columns),  # 使用实际的列索引
                       y=list(heatmap_pivot.index),    # 使用实际的行索引
                       color_continuous_scale='Reds',
                       title='违规热力图 - 按时间分布')
        
        fig.update_layout(
            paper_bgcolor=self.colors['background'],
            font={'color': self.colors['text']}
        )
        
        return fig
    
    def create_sankey_diagram(self, violations):
        """创建桑基图"""
        if not violations or not PLOTLY_AVAILABLE:
            return None
        
        df = pd.DataFrame(violations)
        
        # 准备桑基图数据
        equipment_severity = df.groupby(['rule_name', 'severity']).size().reset_index(name='count')
        
        # 创建节点
        rules = df['rule_name'].unique()
        severities = df['severity'].unique()
        
        all_nodes = list(rules) + list(severities)
        # 使用Plotly的颜色系统而不是matplotlib
        rule_colors = ['rgba(0, 212, 255, 0.8)'] * len(rules)
        severity_colors_rgba = []
        for s in severities:
            if s in self.severity_colors:
                color = self.severity_colors[s]
                # 将十六进制颜色转换为rgba
                if color.startswith('#'):
                    hex_color = color[1:]
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16) 
                    b = int(hex_color[4:6], 16)
                    severity_colors_rgba.append(f'rgba({r}, {g}, {b}, 0.8)')
                else:
                    severity_colors_rgba.append('rgba(255, 255, 255, 0.8)')
            else:
                severity_colors_rgba.append('rgba(255, 255, 255, 0.8)')
        
        node_colors = rule_colors + severity_colors_rgba
        
        # 创建连接
        source = []
        target = []
        value = []
        
        for _, row in equipment_severity.iterrows():
            source.append(all_nodes.index(row['rule_name']))
            target.append(all_nodes.index(row['severity']))
            value.append(row['count'])
        
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_nodes,
                color=node_colors
            ),
            link=dict(
                source=source,
                target=target,
                value=value
            )
        )])
        
        fig.update_layout(
            title_text="违规规则 → 严重程度 流向图",
            font_size=10,
            paper_bgcolor=self.colors['background'],
            font={'color': self.colors['text']}
        )
        
        return fig
    
    def generate_interactive_dashboard(self, violations, records, summary, 
                                    save_path="D:/GitHub/lianwei123/RTO/RCO/可视化结果"):
        """生成交互式仪表板"""
        if not PLOTLY_AVAILABLE:
            print("❌ Plotly不可用，请安装: pip install plotly")
            return
        
        save_path = Path(save_path)
        save_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 创建子图布局
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=('燃烧室温度', '出口温度', '处理效率',
                          '违规时间线', '3D分析', '雷达图',
                          '热力图', '流向图', '总体统计'),
            specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
                   [{"colspan": 3}, None, None],
                   [{"type": "polar"}, {"type": "xy"}, {"type": "xy"}]],
            vertical_spacing=0.08
        )
        
        # 添加仪表盘
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=780,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "燃烧室温度(℃)"},
            gauge={'axis': {'range': [None, 1000]},
                   'bar': {'color': self.colors['primary']},
                   'steps': [{'range': [0, 760], 'color': self.colors['danger']},
                            {'range': [760, 1000], 'color': self.colors['success']}]}
        ), row=1, col=1)
        
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=45,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "出口温度(℃)"},
            gauge={'axis': {'range': [None, 100]},
                   'bar': {'color': self.colors['warning']},
                   'steps': [{'range': [0, 60], 'color': self.colors['success']},
                            {'range': [60, 100], 'color': self.colors['danger']}]}
        ), row=1, col=2)
        
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=85,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "处理效率(%)"},
            gauge={'axis': {'range': [None, 100]},
                   'bar': {'color': self.colors['success']},
                   'steps': [{'range': [0, 90], 'color': self.colors['danger']},
                            {'range': [90, 100], 'color': self.colors['success']}]}
        ), row=1, col=3)
        
        # 添加时间线
        if violations:
            df = pd.DataFrame(violations)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            for severity in df['severity'].unique():
                severity_data = df[df['severity'] == severity]
                fig.add_trace(go.Scatter(
                    x=severity_data['timestamp'],
                    y=severity_data['rule_name'],
                    mode='markers',
                    name=f'{severity.upper()}级',
                    marker=dict(color=self.severity_colors[severity], size=10)
                ), row=2, col=1)
        
        # 添加雷达图
        if summary.get('by_equipment'):
            equipment = list(summary['by_equipment'].keys())
            values = list(summary['by_equipment'].values())
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=equipment,
                fill='toself',
                name='违规次数',
                line_color=self.colors['primary']
            ), row=3, col=1)
        
        # 更新布局
        fig.update_layout(
            height=1200,
            title_text="🏭 废气处理设备交互式监控大屏",
            title_x=0.5,
            paper_bgcolor=self.colors['background'],
            plot_bgcolor=self.colors['background'],
            font={'color': self.colors['text'], 'size': 12}
        )
        
        # 保存为HTML
        html_file = save_path / f"interactive_dashboard_{timestamp}.html"
        pyo.plot(fig, filename=str(html_file), auto_open=False)
        
        print(f"✅ 交互式仪表板已生成: {html_file}")
        
        # 生成独立图表
        self._generate_individual_charts(violations, summary, save_path, timestamp)
    
    def _generate_individual_charts(self, violations, summary, save_path, timestamp):
        """生成独立图表"""
        if not PLOTLY_AVAILABLE:
            return
        
        # 3D分析图
        fig_3d = self.create_3d_violation_analysis(violations)
        if fig_3d:
            html_file = save_path / f"3d_analysis_{timestamp}.html"
            pyo.plot(fig_3d, filename=str(html_file), auto_open=False)
            print(f"✅ 3D分析图已生成: {html_file}")
        
        # 热力图
        fig_heatmap = self.create_heatmap(violations)
        if fig_heatmap:
            html_file = save_path / f"heatmap_{timestamp}.html"
            pyo.plot(fig_heatmap, filename=str(html_file), auto_open=False)
            print(f"✅ 热力图已生成: {html_file}")
        
        # 桑基图
        fig_sankey = self.create_sankey_diagram(violations)
        if fig_sankey:
            html_file = save_path / f"sankey_{timestamp}.html"
            pyo.plot(fig_sankey, filename=str(html_file), auto_open=False)
            print(f"✅ 桑基图已生成: {html_file}")
    
    def _create_matplotlib_gauge(self, value, max_value, title, unit):
        """Matplotlib仪表盘替代方案"""
        fig, ax = plt.subplots(figsize=(8, 6), facecolor='black')
        ax.set_facecolor('black')
        
        # 简单的仪表盘实现
        angles = np.linspace(0, np.pi, 100)
        values_norm = value / max_value
        
        # 绘制弧线
        ax.plot(np.cos(angles), np.sin(angles), 'w-', linewidth=3, alpha=0.3)
        
        # 绘制指针
        pointer_angle = np.pi * (1 - values_norm)
        ax.plot([0, np.cos(pointer_angle) * 0.8], [0, np.sin(pointer_angle) * 0.8], 
               'r-', linewidth=4)
        
        # 添加文字
        ax.text(0, -0.3, f'{value:.1f} {unit}', ha='center', va='center',
               fontsize=16, color='white', fontweight='bold')
        ax.text(0, 0.7, title, ha='center', va='center',
               fontsize=14, color='cyan', fontweight='bold')
        
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-0.5, 1.2)
        ax.set_aspect('equal')
        ax.axis('off')
        
        return fig
    
    def _create_matplotlib_timeline(self, violations):
        """Matplotlib时间线替代方案"""
        fig, ax = plt.subplots(figsize=(15, 8), facecolor='black')
        ax.set_facecolor('black')
        
        df = pd.DataFrame(violations)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        colors = {'low': 'green', 'medium': 'yellow', 'high': 'orange', 'critical': 'red'}
        
        for severity in df['severity'].unique():
            severity_data = df[df['severity'] == severity]
            ax.scatter(severity_data['timestamp'], severity_data['rule_name'],
                      c=colors.get(severity, 'white'), s=100, alpha=0.8,
                      label=f'{severity.upper()}级')
        
        ax.set_title('违规事件时间线', color='white', fontsize=16)
        ax.tick_params(colors='white')
        ax.legend()
        plt.xticks(rotation=45)
        
        return fig

def main():
    """测试交互式仪表板"""
    # 创建测试数据
    violations = [
        {
            'timestamp': datetime.now() - timedelta(hours=i),
            'rule_name': f'规则{i%3+1}',
            'severity': ['low', 'medium', 'high', 'critical'][i%4],
            'value': 50 + i*10,
            'threshold': 100
        } for i in range(20)
    ]
    
    summary = {
        'total': 20,
        'ongoing': 5,
        'resolved': 15,
        'by_severity': {'low': 5, 'medium': 7, 'high': 5, 'critical': 3},
        'by_equipment': {'设备A': 8, '设备B': 6, '设备C': 4, '设备D': 2}
    }
    
    # 创建可视化器
    dashboard = InteractiveDashboard()
    
    # 生成交互式仪表板
    dashboard.generate_interactive_dashboard(violations, [], summary)

if __name__ == "__main__":
    main()