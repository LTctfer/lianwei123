#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超级大屏可视化系统
创建最炫酷的工业级可视化大屏
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime, timedelta
import warnings
from typing import Dict, List, Any
from pathlib import Path

# 设置字体和样式
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False
warnings.filterwarnings('ignore')

class MegaDashboard:
    """超级大屏可视化系统"""
    
    def __init__(self):
        # 赛博朋克配色方案
        self.cyber_colors = {
            'neon_blue': '#00FFFF',
            'neon_pink': '#FF00FF', 
            'neon_green': '#00FF00',
            'neon_orange': '#FF8000',
            'neon_red': '#FF0040',
            'neon_yellow': '#FFFF00',
            'dark_bg': '#000008',
            'grid_color': '#001122',
            'text_glow': '#FFFFFF',
        }
        
        # 严重程度映射
        self.severity_cyber_map = {
            'low': self.cyber_colors['neon_green'],
            'medium': self.cyber_colors['neon_yellow'],
            'high': self.cyber_colors['neon_orange'],
            'critical': self.cyber_colors['neon_red']
        }
    
    def add_glow_text(self, ax, x, y, text, color='#00FFFF', size=12, weight='bold'):
        """添加发光文字效果"""
        # 外发光
        for offset in [(2, 2), (-2, 2), (2, -2), (-2, -2)]:
            ax.text(x + offset[0]*0.002, y + offset[1]*0.002, text, 
                   color=color, fontsize=size, fontweight=weight, 
                   alpha=0.3, ha='center', va='center')
        
        # 主文字
        ax.text(x, y, text, color=color, fontsize=size, fontweight=weight,
               ha='center', va='center', alpha=1.0)
    
    def create_cyber_gauge(self, ax, value, max_value, title, unit=''):
        """创建赛博朋克仪表盘"""
        ax.set_facecolor(self.cyber_colors['dark_bg'])
        
        # 外圈
        outer_circle = Circle((0.5, 0.5), 0.45, fill=False, 
                            edgecolor=self.cyber_colors['neon_blue'], 
                            linewidth=3, alpha=0.8)
        ax.add_patch(outer_circle)
        
        # 刻度
        angles = np.linspace(0, np.pi, 11)
        for angle in angles:
            x1 = 0.5 + 0.35 * np.cos(angle)
            y1 = 0.5 + 0.35 * np.sin(angle)
            x2 = 0.5 + 0.45 * np.cos(angle)
            y2 = 0.5 + 0.45 * np.sin(angle)
            ax.plot([x1, x2], [y1, y2], color=self.cyber_colors['neon_blue'], 
                   alpha=0.7, linewidth=2)
        
        # 指针
        value_ratio = value / max_value
        pointer_angle = np.pi * value_ratio
        pointer_x = 0.5 + 0.3 * np.cos(pointer_angle)
        pointer_y = 0.5 + 0.3 * np.sin(pointer_angle)
        
        ax.plot([0.5, pointer_x], [0.5, pointer_y], 
               color=self.cyber_colors['neon_red'], linewidth=4, alpha=0.9)
        
        # 中心点
        center = Circle((0.5, 0.5), 0.05, facecolor=self.cyber_colors['neon_red'])
        ax.add_patch(center)
        
        # 数值显示
        self.add_glow_text(ax, 0.5, 0.2, f'{value:.1f}{unit}', 
                          self.cyber_colors['neon_yellow'], 16)
        
        # 标题
        self.add_glow_text(ax, 0.5, 0.85, title, 
                          self.cyber_colors['neon_blue'], 14)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect('equal')
        ax.axis('off')
    
    def create_neon_bar_chart(self, ax, data, labels, title, colors=None):
        """创建霓虹灯风格柱状图"""
        ax.set_facecolor(self.cyber_colors['dark_bg'])
        
        if colors is None:
            colors = [self.severity_cyber_map.get(label.lower(), 
                     self.cyber_colors['neon_blue']) for label in labels]
        
        bars = ax.bar(range(len(data)), data, color=colors, alpha=0.8, width=0.6)
        
        # 添加发光效果
        for bar, color in zip(bars, colors):
            bar.set_edgecolor(color)
            bar.set_linewidth(2)
            
            # 顶部发光点
            ax.plot(bar.get_x() + bar.get_width()/2, bar.get_height(), 
                   'o', color=color, markersize=10, alpha=1.0)
        
        # 数值标签
        for i, (bar, value) in enumerate(zip(bars, data)):
            self.add_glow_text(ax, bar.get_x() + bar.get_width()/2, 
                             bar.get_height() + max(data)*0.05,
                             str(int(value)), colors[i], 12)
        
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, color=self.cyber_colors['text_glow'], fontweight='bold')
        
        self.add_glow_text(ax, len(labels)/2 - 0.5, max(data)*1.2, title, 
                          self.cyber_colors['neon_blue'], 16)
        
        # 网格
        ax.grid(True, alpha=0.2, color=self.cyber_colors['neon_blue'])
        ax.tick_params(colors=self.cyber_colors['text_glow'])
        
        for spine in ax.spines.values():
            spine.set_color(self.cyber_colors['neon_blue'])
            spine.set_linewidth(2)
    
    def create_matrix_timeline(self, ax, violations, title):
        """创建矩阵风格时间线"""
        ax.set_facecolor(self.cyber_colors['dark_bg'])
        
        if not violations:
            self.add_glow_text(ax, 0.5, 0.5, '系统运行正常', 
                             self.cyber_colors['neon_green'], 16)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            return
        
        df = pd.DataFrame(violations)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 按严重程度分组绘制
        for severity in ['critical', 'high', 'medium', 'low']:
            severity_data = df[df['severity'] == severity]
            if not severity_data.empty:
                color = self.severity_cyber_map[severity]
                
                ax.scatter(severity_data['timestamp'], severity_data['rule_name'],
                          c=color, s=150, alpha=0.9, edgecolors=color, linewidth=2,
                          label=f'{severity.upper()}级')
                
                # 能量波效果
                for size in [300, 500]:
                    ax.scatter(severity_data['timestamp'], severity_data['rule_name'],
                              c=color, s=size, alpha=0.1)
        
        self.add_glow_text(ax, 0.5, 0.95, title, self.cyber_colors['neon_green'], 18)
        
        ax.tick_params(colors=self.cyber_colors['text_glow'])
        ax.grid(True, alpha=0.2, color=self.cyber_colors['neon_green'])
        
        for spine in ax.spines.values():
            spine.set_color(self.cyber_colors['neon_green'])
            spine.set_linewidth(2)
        
        if len(df) > 0:
            legend = ax.legend(loc='upper right', facecolor=self.cyber_colors['dark_bg'])
            for text in legend.get_texts():
                text.set_color(self.cyber_colors['text_glow'])
    
    def generate_mega_dashboard(self, violations, records, summary, 
                              save_path="D:/GitHub/lianwei123/RTO/RCO/可视化结果"):
        """生成超级大屏"""
        save_path = Path(save_path)
        save_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 创建主画布 - 降低尺寸避免图像过大
        fig = plt.figure(figsize=(20, 12))  # 从(32, 18)降低到(20, 12)
        fig.patch.set_facecolor(self.cyber_colors['dark_bg'])
        
        # 创建网格布局
        gs = gridspec.GridSpec(5, 6, figure=fig, hspace=0.2, wspace=0.2)
        
        # 主标题
        title_ax = fig.add_subplot(gs[0, :])
        title_ax.set_facecolor(self.cyber_colors['dark_bg'])
        
        title_text = '🏭 MEGA 废气处理设备监控大屏 - CYBER EDITION 🏭'
        self.add_glow_text(title_ax, 0.5, 0.5, title_text, 
                          self.cyber_colors['neon_blue'], 28)
        
        time_text = f'◆ SYSTEM TIME: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ◆'
        self.add_glow_text(title_ax, 0.5, 0.1, time_text, 
                          self.cyber_colors['neon_yellow'], 14)
        
        title_ax.set_xlim(0, 1)
        title_ax.set_ylim(0, 1)
        title_ax.axis('off')
        
        # 仪表盘区域
        gauge_configs = [
            (gs[1, 0:2], 780, 1000, '燃烧室温度', '℃'),
            (gs[1, 2:4], 45, 100, '出口温度', '℃'),
            (gs[1, 4:6], 95, 100, '处理效率', '%')
        ]
        
        for grid_pos, value, max_val, title, unit in gauge_configs:
            ax = fig.add_subplot(grid_pos)
            self.create_cyber_gauge(ax, value, max_val, title, unit)
        
        # 统计图表
        if summary.get('by_severity'):
            severity_ax = fig.add_subplot(gs[2, 0:3])
            severities = list(summary['by_severity'].keys())
            counts = list(summary['by_severity'].values())
            colors = [self.severity_cyber_map[s] for s in severities]
            self.create_neon_bar_chart(severity_ax, counts, severities, 
                                     '◆ 违规严重程度分析 ◆', colors)
        
        if summary.get('by_equipment'):
            equipment_ax = fig.add_subplot(gs[2, 3:6])
            equipment = list(summary['by_equipment'].keys())
            eq_counts = list(summary['by_equipment'].values())
            self.create_neon_bar_chart(equipment_ax, eq_counts, equipment, 
                                     '◆ 设备违规统计 ◆')
        
        # 时间线
        timeline_ax = fig.add_subplot(gs[3:5, :])
        self.create_matrix_timeline(timeline_ax, violations, '◆ 违规事件矩阵时间线 ◆')
        
        # 保存超级大屏 - 降低DPI避免图像过大
        output_file = save_path / f"mega_dashboard_{timestamp}.png"
        
        try:
            plt.savefig(output_file, dpi=150, facecolor=self.cyber_colors['dark_bg'],  # 从300降低到150
                       bbox_inches='tight', edgecolor='none')
            print(f"🚀 超级大屏已生成: {output_file}")
        except Exception as e:
            print(f"❌ 保存超级大屏失败: {e}")
            # 尝试更低的DPI
            try:
                plt.savefig(output_file, dpi=100, facecolor=self.cyber_colors['dark_bg'],
                           bbox_inches='tight', edgecolor='none')
                print(f"🚀 超级大屏已生成（低分辨率）: {output_file}")
            except Exception as e2:
                print(f"❌ 保存失败: {e2}")
        
        # 尽量不显示图表，避免占用过多资源
        try:
            plt.show()
        except:
            pass
        
        # 清理内存
        plt.close(fig)

def main():
    """测试超级大屏"""
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
        }
    ]
    
    summary = {
        'total': 2,
        'ongoing': 1,
        'resolved': 1,
        'by_severity': {'high': 1, 'medium': 1},
        'by_equipment': {'燃烧室': 1, '废气出口': 1}
    }
    
    dashboard = MegaDashboard()
    dashboard.generate_mega_dashboard(violations, [], summary)

if __name__ == "__main__":
    main()