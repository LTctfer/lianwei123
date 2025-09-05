#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
现代化仪表板可视化器
创建美观炫酷的可视化大屏
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
from typing import Dict, List, Any
from pathlib import Path
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap, to_rgba
import matplotlib.animation as animation

# 设置中文字体和样式
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.style.use('dark_background')
warnings.filterwarnings('ignore')

class ModernDashboardVisualizer:
    """现代化仪表板可视化器"""
    
    def __init__(self):
        # 现代化配色方案
        self.colors = {
            'primary': '#00D4FF',      # 科技蓝
            'secondary': '#FF6B35',    # 活力橙
            'success': '#00E676',      # 成功绿
            'warning': '#FFD600',      # 警告黄
            'danger': '#FF1744',       # 危险红
            'background': '#0A0E27',   # 深蓝背景
            'surface': '#1A1F3A',      # 表面色
            'text': '#FFFFFF',         # 白色文字
            'text_secondary': '#B0BEC5', # 次要文字
            'accent': '#E91E63'        # 强调色
        }
        
        # 严重程度配色
        self.severity_colors = {
            'low': self.colors['success'],
            'medium': self.colors['warning'], 
            'high': self.colors['secondary'],
            'critical': self.colors['danger']
        }
        
        # 渐变配色
        self.gradients = {
            'blue': ['#0F4C75', '#3282B8', '#0F4C75'],
            'orange': ['#FF6B35', '#F7931E', '#FF6B35'],
            'green': ['#00E676', '#4CAF50', '#00E676'],
            'red': ['#FF1744', '#F44336', '#FF1744']
        }
    
    def create_modern_figure(self, figsize=(16, 10)):
        """创建现代化图表基础 - 降低默认尺寸"""
        fig = plt.figure(figsize=figsize, facecolor=self.colors['background'])
        fig.patch.set_facecolor(self.colors['background'])
        return fig
    
    def add_glow_effect(self, ax, color='#00D4FF', alpha=0.3):
        """添加发光效果"""
        ax.spines['top'].set_color(color)
        ax.spines['bottom'].set_color(color)
        ax.spines['left'].set_color(color)
        ax.spines['right'].set_color(color)
        ax.spines['top'].set_linewidth(2)
        ax.spines['bottom'].set_linewidth(2)
        ax.spines['left'].set_linewidth(2)
        ax.spines['right'].set_linewidth(2)
        
        # 添加外发光
        for spine in ax.spines.values():
            spine.set_path_effects([
                plt.matplotlib.patheffects.withStroke(linewidth=4, foreground=color, alpha=alpha)
            ])
    
    def create_gradient_background(self, ax, direction='vertical'):
        """创建渐变背景"""
        if direction == 'vertical':
            gradient = np.linspace(0, 1, 256).reshape(256, -1)
        else:
            gradient = np.linspace(0, 1, 256).reshape(-1, 256)
        
        ax.imshow(gradient, extent=ax.get_xlim() + ax.get_ylim(), 
                 aspect='auto', alpha=0.1, cmap='Blues')
    
    def plot_cyber_gauge(self, ax, value, max_value, title, unit='', color=None):
        """绘制赛博朋克风格仪表盘"""
        if color is None:
            color = self.colors['primary']
        
        # 计算角度
        angle = (value / max_value) * 180
        
        # 绘制外圆
        circle_outer = patches.Circle((0.5, 0.5), 0.45, 
                                    fill=False, edgecolor=color, linewidth=3, alpha=0.8)
        ax.add_patch(circle_outer)
        
        # 绘制内圆
        circle_inner = patches.Circle((0.5, 0.5), 0.35, 
                                    fill=False, edgecolor=color, linewidth=2, alpha=0.6)
        ax.add_patch(circle_inner)
        
        # 绘制刻度
        for i in range(0, 181, 20):
            x = 0.5 + 0.4 * np.cos(np.radians(i))
            y = 0.5 + 0.4 * np.sin(np.radians(i))
            x2 = 0.5 + 0.35 * np.cos(np.radians(i))
            y2 = 0.5 + 0.35 * np.sin(np.radians(i))
            ax.plot([x, x2], [y, y2], color=color, alpha=0.7, linewidth=1)
        
        # 绘制指针
        pointer_x = 0.5 + 0.3 * np.cos(np.radians(angle))
        pointer_y = 0.5 + 0.3 * np.sin(np.radians(angle))
        ax.plot([0.5, pointer_x], [0.5, pointer_y], 
               color=self.colors['danger'], linewidth=4, alpha=0.9)
        
        # 中心点
        center = patches.Circle((0.5, 0.5), 0.05, 
                              facecolor=self.colors['danger'], edgecolor=color)
        ax.add_patch(center)
        
        # 数值显示
        ax.text(0.5, 0.2, f'{value:.1f}{unit}', 
               ha='center', va='center', fontsize=16, fontweight='bold',
               color=self.colors['text'])
        
        # 标题
        ax.text(0.5, 0.9, title, ha='center', va='center', 
               fontsize=14, fontweight='bold', color=color)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect('equal')
        ax.axis('off')
    
    def plot_neon_bar_chart(self, ax, data, labels, title, colors=None):
        """绘制霓虹灯风格柱状图"""
        if colors is None:
            colors = [self.severity_colors.get(label.lower(), self.colors['primary']) 
                     for label in labels]
        
        bars = ax.bar(range(len(data)), data, color=colors, alpha=0.8, width=0.6)
        
        # 添加发光效果
        for bar, color in zip(bars, colors):
            bar.set_edgecolor(color)
            bar.set_linewidth(2)
            # 添加顶部发光点
            ax.plot(bar.get_x() + bar.get_width()/2, bar.get_height(), 
                   'o', color=color, markersize=8, alpha=0.9)
        
        # 添加数值标签
        for i, (bar, value) in enumerate(zip(bars, data)):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(data)*0.02,
                   str(int(value)), ha='center', va='bottom', 
                   fontweight='bold', color=self.colors['text'])
        
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, color=self.colors['text'], fontweight='bold')
        ax.set_title(title, color=self.colors['text'], fontsize=16, fontweight='bold')
        ax.set_facecolor(self.colors['background'])
        
        # 美化网格
        ax.grid(True, alpha=0.3, color=self.colors['primary'])
        ax.set_axisbelow(True)
        
        # 设置轴样式
        ax.tick_params(colors=self.colors['text'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(self.colors['primary'])
        ax.spines['left'].set_color(self.colors['primary'])
    
    def plot_hologram_timeline(self, ax, violations, title):
        """绘制全息风格时间线"""
        if not violations:
            ax.text(0.5, 0.5, '暂无违规数据', ha='center', va='center',
                   transform=ax.transAxes, color=self.colors['text'], fontsize=14)
            return
        
        df = pd.DataFrame(violations)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 按严重程度分组
        for severity in ['critical', 'high', 'medium', 'low']:
            severity_data = df[df['severity'] == severity]
            if not severity_data.empty:
                color = self.severity_colors[severity]
                ax.scatter(severity_data['timestamp'], 
                          severity_data['rule_name'],
                          c=color, s=100, alpha=0.8, 
                          edgecolors=color, linewidth=2, label=f'{severity.upper()}级')
                
                # 添加发光效果
                ax.scatter(severity_data['timestamp'], 
                          severity_data['rule_name'],
                          c=color, s=200, alpha=0.3)
        
        ax.set_title(title, color=self.colors['text'], fontsize=16, fontweight='bold')
        ax.tick_params(colors=self.colors['text'])
        ax.set_facecolor(self.colors['background'])
        
        # 美化时间轴
        ax.tick_params(axis='x', rotation=45)
        
        # 添加图例
        if len(df) > 0:
            ax.legend(loc='upper right', facecolor=self.colors['surface'], 
                     edgecolor=self.colors['primary'], labelcolor=self.colors['text'])
        
        # 网格线
        ax.grid(True, alpha=0.2, color=self.colors['primary'])
    
    def create_status_indicator(self, ax, status, title):
        """创建状态指示器"""
        # 状态颜色映射
        status_colors = {
            'normal': self.colors['success'],
            'warning': self.colors['warning'], 
            'critical': self.colors['danger'],
            'offline': '#666666'
        }
        
        color = status_colors.get(status, self.colors['text'])
        
        # 绘制指示器
        circle = patches.Circle((0.5, 0.5), 0.3, 
                              facecolor=color, alpha=0.8,
                              edgecolor=color, linewidth=3)
        ax.add_patch(circle)
        
        # 添加脉冲效果
        pulse_circle = patches.Circle((0.5, 0.5), 0.4, 
                                    fill=False, edgecolor=color, 
                                    linewidth=2, alpha=0.5)
        ax.add_patch(pulse_circle)
        
        # 状态文字
        ax.text(0.5, 0.5, status.upper(), ha='center', va='center',
               fontsize=12, fontweight='bold', color=self.colors['text'])
        
        # 标题
        ax.text(0.5, 0.1, title, ha='center', va='center',
               fontsize=10, color=self.colors['text'])
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    
    def generate_modern_dashboard(self, violations, records, summary, 
                                save_path="D:/GitHub/lianwei123/RTO/RCO/可视化结果"):
        """生成现代化仪表板"""
        save_path = Path(save_path)
        save_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 创建主仪表板
        fig = self.create_modern_figure(figsize=(18, 12))  # 降低尺寸
        
        # 创建网格布局
        gs = gridspec.GridSpec(4, 6, figure=fig, hspace=0.3, wspace=0.3)
        
        # 标题区域
        title_ax = fig.add_subplot(gs[0, :])
        title_ax.text(0.5, 0.5, '🏭 废气处理设备实时监控大屏', 
                     ha='center', va='center', fontsize=32, fontweight='bold',
                     color=self.colors['primary'])
        title_ax.text(0.5, 0.1, f'数据更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                     ha='center', va='center', fontsize=14, 
                     color=self.colors['text_secondary'])
        title_ax.axis('off')
        
        # 状态指示器区域
        status_indicators = [
            (gs[1, 0], 'normal', '燃烧室'),
            (gs[1, 1], 'warning', '废气出口'), 
            (gs[1, 2], 'critical', '吸附设施'),
            (gs[1, 3], 'normal', '脱附设施'),
            (gs[1, 4], 'normal', '反应器'),
            (gs[1, 5], 'normal', '应急系统')
        ]
        
        for grid_pos, status, title in status_indicators:
            ax = fig.add_subplot(grid_pos)
            self.create_status_indicator(ax, status, title)
            self.add_glow_effect(ax, self.severity_colors.get(status, self.colors['primary']))
        
        # 仪表盘区域
        gauge_data = [
            (gs[2, 0:2], 780, 1000, '燃烧室温度', '℃', self.colors['primary']),
            (gs[2, 2:4], 45, 100, '出口温度', '℃', self.colors['warning']),
            (gs[2, 4:6], 85, 100, '处理效率', '%', self.colors['success'])
        ]
        
        for grid_pos, value, max_val, title, unit, color in gauge_data:
            ax = fig.add_subplot(grid_pos)
            self.plot_cyber_gauge(ax, value, max_val, title, unit, color)
            self.add_glow_effect(ax, color)
        
        # 违规统计区域
        if summary.get('by_severity'):
            ax1 = fig.add_subplot(gs[3, 0:2])
            severities = list(summary['by_severity'].keys())
            counts = list(summary['by_severity'].values())
            colors = [self.severity_colors[s] for s in severities]
            self.plot_neon_bar_chart(ax1, counts, severities, '违规严重程度统计', colors)
            self.add_glow_effect(ax1, self.colors['primary'])
        
        # 设备违规统计
        if summary.get('by_equipment'):
            ax2 = fig.add_subplot(gs[3, 2:4])
            equipment = list(summary['by_equipment'].keys())
            eq_counts = list(summary['by_equipment'].values()) 
            self.plot_neon_bar_chart(ax2, eq_counts, equipment, '设备违规统计')
            self.add_glow_effect(ax2, self.colors['secondary'])
        
        # 时间线图
        ax3 = fig.add_subplot(gs[3, 4:6])
        self.plot_hologram_timeline(ax3, violations, '违规事件时间线')
        self.add_glow_effect(ax3, self.colors['accent'])
        
        # 保存图片 - 降低DPI避免图像过大
        output_file = save_path / f"modern_dashboard_{timestamp}.png"
        
        try:
            plt.savefig(output_file, dpi=150, facecolor=self.colors['background'],  # 从300降低到150
                       bbox_inches='tight', edgecolor='none')
            print(f"✅ 现代化仪表板已生成: {output_file}")
        except Exception as e:
            print(f"❌ 保存仪表板失败: {e}")
            # 尝试更低的DPI
            try:
                plt.savefig(output_file, dpi=100, facecolor=self.colors['background'],
                           bbox_inches='tight', edgecolor='none')
                print(f"✅ 现代化仪表板已生成（低分辨率）: {output_file}")
            except Exception as e2:
                print(f"❌ 保存失败: {e2}")
        
        try:
            plt.show()
        except:
            pass
        
        # 清理内存
        plt.close(fig)
        
        # 生成动画时间线
        self.create_animated_timeline(violations, save_path, timestamp)
    
    def create_animated_timeline(self, violations, save_path, timestamp):
        """创建动画时间线"""
        if not violations:
            return
        
        fig, ax = plt.subplots(figsize=(16, 10), facecolor=self.colors['background'])
        ax.set_facecolor(self.colors['background'])
        
        df = pd.DataFrame(violations)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        def animate(frame):
            ax.clear()
            ax.set_facecolor(self.colors['background'])
            
            # 显示到当前帧的数据
            current_data = df.iloc[:frame+1]
            
            if not current_data.empty:
                for severity in ['critical', 'high', 'medium', 'low']:
                    severity_data = current_data[current_data['severity'] == severity]
                    if not severity_data.empty:
                        color = self.severity_colors[severity]
                        ax.scatter(severity_data['timestamp'], 
                                  severity_data['rule_name'],
                                  c=color, s=150, alpha=0.8, 
                                  edgecolors=color, linewidth=2)
                        
                        # 添加发光效果
                        ax.scatter(severity_data['timestamp'], 
                                  severity_data['rule_name'],
                                  c=color, s=300, alpha=0.3)
            
            ax.set_title(f'违规事件实时监控 - 事件 {frame+1}/{len(df)}', 
                        color=self.colors['text'], fontsize=18, fontweight='bold')
            ax.tick_params(colors=self.colors['text'])
            ax.grid(True, alpha=0.2, color=self.colors['primary'])
        
        # 创建动画
        anim = animation.FuncAnimation(fig, animate, frames=len(df), 
                                     interval=500, repeat=True)
        
        # 保存为GIF
        gif_file = save_path / f"animated_timeline_{timestamp}.gif"
        anim.save(gif_file, writer='pillow', fps=2)
        print(f"✅ 动画时间线已生成: {gif_file}")
        
        plt.close()

def main():
    """测试现代化仪表板"""
    # 创建测试数据
    violations = [
        {
            'timestamp': datetime.now() - timedelta(hours=2),
            'rule_name': '燃烧室温度不达标',
            'severity': 'high',
            'value': 720,
            'threshold': 760
        },
        {
            'timestamp': datetime.now() - timedelta(hours=1),
            'rule_name': '出口温度超标',
            'severity': 'medium',
            'value': 75,
            'threshold': 60
        },
        {
            'timestamp': datetime.now() - timedelta(minutes=30),
            'rule_name': '应急阀门违规开启',
            'severity': 'critical',
            'value': 1,
            'threshold': 0
        }
    ]
    
    summary = {
        'total': 3,
        'ongoing': 1,
        'resolved': 2,
        'by_severity': {'high': 1, 'medium': 1, 'critical': 1},
        'by_equipment': {'燃烧室': 1, '废气出口': 1, '应急阀门': 1}
    }
    
    # 创建可视化器
    visualizer = ModernDashboardVisualizer()
    
    # 生成现代化仪表板
    visualizer.generate_modern_dashboard(violations, [], summary)

if __name__ == "__main__":
    main()