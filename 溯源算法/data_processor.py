#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理和可视化模块
用于污染物溯源系统的数据预处理、清洗和结果可视化

作者: AI Assistant
日期: 2025-01-18
版本: 1.0
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from typing import List, Dict, Tuple, Optional
import json
import os
from datetime import datetime, timedelta

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class DataProcessor:
    """数据处理器"""
    
    def __init__(self):
        """初始化数据处理器"""
        self.raw_data = []
        self.cleaned_data = []
        
    def load_monitoring_data(self, file_path: str) -> List[Dict]:
        """
        从文件加载监测数据
        
        Args:
            file_path: 数据文件路径
            
        Returns:
            监测数据列表
        """
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
            else:
                raise ValueError("不支持的文件格式，请使用CSV或JSON格式")
            
            # 转换为字典列表
            self.raw_data = df.to_dict('records')
            print(f"成功加载 {len(self.raw_data)} 条监测数据")
            return self.raw_data
            
        except Exception as e:
            print(f"加载数据失败: {e}")
            return []
    
    def clean_data(self, 
                   remove_negative: bool = True,
                   remove_outliers: bool = True,
                   outlier_threshold: float = 3.0) -> List[Dict]:
        """
        数据清洗
        
        Args:
            remove_negative: 是否移除负值
            remove_outliers: 是否移除异常值
            outlier_threshold: 异常值阈值(标准差倍数)
            
        Returns:
            清洗后的数据
        """
        if not self.raw_data:
            print("警告: 没有原始数据需要清洗")
            return []
        
        cleaned = self.raw_data.copy()
        original_count = len(cleaned)
        
        # 移除负值
        if remove_negative:
            cleaned = [d for d in cleaned if d.get('concentration', 0) >= 0]
            print(f"移除负值: {original_count - len(cleaned)} 条")
        
        # 移除异常值
        if remove_outliers and len(cleaned) > 0:
            concentrations = [d['concentration'] for d in cleaned]
            mean_conc = np.mean(concentrations)
            std_conc = np.std(concentrations)
            
            threshold_low = mean_conc - outlier_threshold * std_conc
            threshold_high = mean_conc + outlier_threshold * std_conc
            
            before_outlier = len(cleaned)
            cleaned = [d for d in cleaned if threshold_low <= d['concentration'] <= threshold_high]
            print(f"移除异常值: {before_outlier - len(cleaned)} 条")
        
        self.cleaned_data = cleaned
        print(f"数据清洗完成: {len(self.cleaned_data)} 条有效数据")
        return self.cleaned_data
    
    def interpolate_missing_data(self, 
                               time_column: str = 'timestamp',
                               value_column: str = 'concentration') -> List[Dict]:
        """
        插值补全缺失数据
        
        Args:
            time_column: 时间列名
            value_column: 数值列名
            
        Returns:
            补全后的数据
        """
        if not self.cleaned_data:
            print("警告: 没有清洗后的数据进行插值")
            return []
        
        # 转换为DataFrame进行插值
        df = pd.DataFrame(self.cleaned_data)
        
        # 转换时间列
        if time_column in df.columns:
            df[time_column] = pd.to_datetime(df[time_column])
            df = df.sort_values(time_column)
        
        # 线性插值
        if value_column in df.columns:
            original_nulls = df[value_column].isnull().sum()
            df[value_column] = df[value_column].interpolate(method='linear')
            final_nulls = df[value_column].isnull().sum()
            print(f"插值补全: {original_nulls - final_nulls} 个缺失值")
        
        return df.to_dict('records')
    
    def aggregate_data(self, 
                      time_window: str = '1H',
                      agg_method: str = 'mean') -> pd.DataFrame:
        """
        数据聚合
        
        Args:
            time_window: 时间窗口 ('1H', '30min', '1D' 等)
            agg_method: 聚合方法 ('mean', 'max', 'min', 'median')
            
        Returns:
            聚合后的数据
        """
        if not self.cleaned_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.cleaned_data)
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # 按时间窗口聚合
            if agg_method == 'mean':
                aggregated = df.resample(time_window).mean()
            elif agg_method == 'max':
                aggregated = df.resample(time_window).max()
            elif agg_method == 'min':
                aggregated = df.resample(time_window).min()
            elif agg_method == 'median':
                aggregated = df.resample(time_window).median()
            else:
                aggregated = df.resample(time_window).mean()
            
            print(f"数据聚合完成: {len(aggregated)} 个时间段")
            return aggregated
        
        return df


class Visualizer:
    """可视化器"""
    
    def __init__(self, figsize: Tuple[int, int] = (12, 8)):
        """
        初始化可视化器
        
        Args:
            figsize: 图形大小
        """
        self.figsize = figsize
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
    def plot_monitoring_stations(self, 
                               monitoring_data: List[Dict],
                               source_location: Optional[Tuple[float, float]] = None,
                               save_path: Optional[str] = None):
        """
        绘制监测站分布图
        
        Args:
            monitoring_data: 监测数据
            source_location: 污染源位置 (x, y)
            save_path: 保存路径
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # 提取坐标和浓度
        x_coords = [d['x'] for d in monitoring_data]
        y_coords = [d['y'] for d in monitoring_data]
        concentrations = [d['concentration'] for d in monitoring_data]
        station_ids = [d.get('station_id', f'S{i}') for i, d in enumerate(monitoring_data)]
        
        # 绘制监测站
        scatter = ax.scatter(x_coords, y_coords, c=concentrations, 
                           s=100, cmap='YlOrRd', alpha=0.8, edgecolors='black')
        
        # 添加站点标签
        for i, (x, y, sid) in enumerate(zip(x_coords, y_coords, station_ids)):
            ax.annotate(sid, (x, y), xytext=(5, 5), textcoords='offset points',
                       fontsize=8, ha='left')
        
        # 添加污染源位置
        if source_location:
            ax.scatter(source_location[0], source_location[1], 
                      marker='*', s=200, c='red', edgecolors='black',
                      label='污染源', zorder=5)
            ax.legend()
        
        # 设置图形属性
        ax.set_xlabel('东西方向距离 (米)', fontsize=12)
        ax.set_ylabel('南北方向距离 (米)', fontsize=12)
        ax.set_title('监测站分布及污染物浓度分布图', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

        # 添加颜色条
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('污染物浓度 (微克/立方米)', fontsize=11)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"监测站分布图已保存至: {save_path}")
        
        plt.show()
    
    def plot_dispersion_contour(self, 
                              x_grid: np.ndarray,
                              y_grid: np.ndarray, 
                              concentration_grid: np.ndarray,
                              monitoring_data: Optional[List[Dict]] = None,
                              source_location: Optional[Tuple[float, float]] = None,
                              save_path: Optional[str] = None):
        """
        绘制污染物扩散等值线图
        
        Args:
            x_grid, y_grid: 网格坐标
            concentration_grid: 浓度网格
            monitoring_data: 监测数据
            source_location: 污染源位置
            save_path: 保存路径
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # 绘制等值线
        levels = np.logspace(np.log10(max(1, np.min(concentration_grid[concentration_grid > 0]))),
                           np.log10(np.max(concentration_grid)), 15)
        
        contour = ax.contourf(x_grid, y_grid, concentration_grid, 
                            levels=levels, cmap='YlOrRd', alpha=0.8)
        
        # 绘制等值线
        contour_lines = ax.contour(x_grid, y_grid, concentration_grid,
                                 levels=levels, colors='black', alpha=0.4, linewidths=0.5)
        
        # 添加监测站
        if monitoring_data:
            x_coords = [d['x'] for d in monitoring_data]
            y_coords = [d['y'] for d in monitoring_data]
            ax.scatter(x_coords, y_coords, c='blue', s=50, 
                      marker='o', edgecolors='white', label='监测站', zorder=5)
        
        # 添加污染源
        if source_location:
            ax.scatter(source_location[0], source_location[1],
                      marker='*', s=200, c='red', edgecolors='black',
                      label='污染源', zorder=5)
        
        # 设置图形属性
        ax.set_xlabel('东西方向距离 (米)', fontsize=12)
        ax.set_ylabel('南北方向距离 (米)', fontsize=12)
        ax.set_title('污染物扩散分布模拟图', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.set_aspect('equal')

        # 添加颜色条
        cbar = plt.colorbar(contour, ax=ax)
        cbar.set_label('污染物浓度 (微克/立方米)', fontsize=11)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"扩散等值线图已保存至: {save_path}")
        
        plt.show()

    def plot_verification_results(self,
                                verification_data: List[Dict],
                                save_path: Optional[str] = None):
        """
        绘制验证结果对比图

        Args:
            verification_data: 验证数据 [{'station_id', 'observed', 'predicted', ...}]
            save_path: 保存路径
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 提取数据
        station_ids = [d['station_id'] for d in verification_data]
        observed = [d['observed'] for d in verification_data]
        predicted = [d['predicted'] for d in verification_data]

        # 左图：观测值vs预测值散点图
        ax1.scatter(observed, predicted, alpha=0.7, s=60)

        # 添加1:1线
        min_val = min(min(observed), min(predicted))
        max_val = max(max(observed), max(predicted))
        ax1.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.8, label='1:1线')

        # 计算R²
        correlation = np.corrcoef(observed, predicted)[0, 1]
        r_squared = correlation ** 2
        ax1.text(0.05, 0.95, f'R² = {r_squared:.3f}', transform=ax1.transAxes,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        ax1.set_xlabel('实际观测浓度 (微克/立方米)', fontsize=11)
        ax1.set_ylabel('模型预测浓度 (微克/立方米)', fontsize=11)
        ax1.set_title('实际观测值与模型预测值对比', fontsize=12, fontweight='bold')
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)

        # 右图：各站点对比柱状图
        x_pos = np.arange(len(station_ids))
        width = 0.35

        ax2.bar(x_pos - width/2, observed, width, label='实际观测值', alpha=0.8, color='#1f77b4')
        ax2.bar(x_pos + width/2, predicted, width, label='模型预测值', alpha=0.8, color='#ff7f0e')

        ax2.set_xlabel('监测站点', fontsize=11)
        ax2.set_ylabel('污染物浓度 (微克/立方米)', fontsize=11)
        ax2.set_title('各监测站点数值对比', fontsize=12, fontweight='bold')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(station_ids, rotation=45, fontsize=9)
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"验证结果图已保存至: {save_path}")

        plt.show()

    def plot_time_series(self,
                        data: pd.DataFrame,
                        value_column: str = 'concentration',
                        station_column: str = 'station_id',
                        save_path: Optional[str] = None):
        """
        绘制时间序列图

        Args:
            data: 时间序列数据
            value_column: 数值列名
            station_column: 站点列名
            save_path: 保存路径
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        # 按站点分组绘制
        if station_column in data.columns:
            stations = data[station_column].unique()
            for i, station in enumerate(stations):
                station_data = data[data[station_column] == station]
                ax.plot(station_data.index, station_data[value_column],
                       label=station, color=self.colors[i % len(self.colors)],
                       marker='o', markersize=3, alpha=0.8)
        else:
            ax.plot(data.index, data[value_column],
                   marker='o', markersize=3, alpha=0.8)

        ax.set_xlabel('时间', fontsize=12)
        ax.set_ylabel('污染物浓度 (微克/立方米)', fontsize=12)
        ax.set_title('污染物浓度随时间变化趋势图', fontsize=14, fontweight='bold')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3)

        # 旋转x轴标签
        plt.xticks(rotation=45)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"时间序列图已保存至: {save_path}")

        plt.show()

    def plot_wind_rose(self,
                      wind_data: List[Dict],
                      save_path: Optional[str] = None):
        """
        绘制风玫瑰图

        Args:
            wind_data: 风向风速数据 [{'wind_direction', 'wind_speed'}]
            save_path: 保存路径
        """
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

        # 提取风向和风速数据
        directions = [d['wind_direction'] for d in wind_data]
        speeds = [d['wind_speed'] for d in wind_data]

        # 转换角度 (气象角度转数学角度)
        theta = [(90 - d) * np.pi / 180 for d in directions]

        # 绘制散点图
        scatter = ax.scatter(theta, speeds, c=speeds, cmap='viridis', alpha=0.6)

        # 设置角度标签
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_thetagrids(np.arange(0, 360, 45), ['北', '东北', '东', '东南', '南', '西南', '西', '西北'])

        ax.set_title('风向风速分布图', pad=20, fontsize=14, fontweight='bold')
        ax.set_ylabel('风速 (米/秒)', labelpad=30, fontsize=12)

        # 添加颜色条
        cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
        cbar.set_label('风速 (米/秒)', fontsize=11)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"风玫瑰图已保存至: {save_path}")

        plt.show()
