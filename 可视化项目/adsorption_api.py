#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抽取式吸附曲线数据处理API接口
基于完整数据处理与可视化算法，提供数据点坐标、标签和预警点信息
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
from scipy.optimize import curve_fit
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass
import warnings
import os
warnings.filterwarnings('ignore')

# 导入原始算法的类和函数
from Adsorption_isotherm import (
    AdsorptionCurveProcessor,
    WarningLevel,
    WarningEvent,
    LogisticWarningModel
)

@dataclass
class DataPoint:
    """数据点信息"""
    x: float          # x轴坐标（时间）
    y: float          # y轴坐标（浓度或效率）
    label: str        # 数据点标签
    data_type: str    # 数据类型（原始/清洗后/拟合）

@dataclass
class WarningPoint:
    """预警点信息"""
    x: float                    # x轴坐标（时间）
    y: float                    # y轴坐标（浓度或效率）
    warning_level: WarningLevel # 预警等级
    reason: str                 # 预警原因
    recommendation: str         # 建议措施

@dataclass
class AdsorptionAnalysisResult:
    """吸附分析结果"""
    # 原始数据点
    raw_data_points: List[DataPoint]
    
    # 清洗后数据点
    cleaned_data_points_ks: List[DataPoint]
    cleaned_data_points_boxplot: List[DataPoint]
    
    # 效率数据点
    efficiency_data_points_ks: List[DataPoint]
    efficiency_data_points_boxplot: List[DataPoint]
    
    # 拟合曲线数据点
    fitted_curve_points: List[DataPoint]
    
    # 预警点
    warning_points: List[WarningPoint]
    
    # 统计信息
    statistics: Dict[str, Any]

class AdsorptionAPI:
    """吸附曲线预警系统API"""

    def __init__(self, data_file: str):
        """
        初始化API

        Args:
            data_file: 数据文件路径，支持CSV、XLSX、XLS格式
        """
        self.data_file = data_file
        self.processor = AdsorptionCurveProcessor(data_file)
        self.warning_result = None
    
    def analyze_warning_system(self) -> Dict[str, Any]:
        """
        执行预警系统分析，返回预警相关的数据点和预警点

        Returns:
            Dict: 包含预警系统数据点、标签和预警点坐标的字典
        """
        print("=== 开始预警系统分析 ===")

        # 1. 加载数据
        if not self.processor.load_data():
            raise ValueError("数据加载失败")

        # 2. 基础数据清洗
        basic_cleaned = self.processor.basic_data_cleaning(self.processor.raw_data)
        if len(basic_cleaned) == 0:
            raise ValueError("基础清洗后无数据")

        # 3. K-S检验清洗（用于预警系统）
        self.processor.cleaned_data_ks = self.processor.ks_test_cleaning(basic_cleaned)

        # 4. 计算吸附效率与穿透率数据（两套规则，预警系统核心数据）
        self.processor.efficiency_data_ks = self.processor.calculate_efficiency_with_two_rules(
            self.processor.cleaned_data_ks, "K-S检验"
        )

        # 5. 备用：箱型图清洗与效率数据（若需要回退使用）
        try:
            self.processor.cleaned_data_boxplot = self.processor.boxplot_cleaning(basic_cleaned)
            self.processor.efficiency_data_boxplot = self.processor.calculate_efficiency_with_two_rules(
                self.processor.cleaned_data_boxplot, "箱型图"
            ) if self.processor.cleaned_data_boxplot is not None and len(self.processor.cleaned_data_boxplot) > 0 else None
        except Exception:
            # 旧版本可能未提供该方法，忽略回退
            self.processor.cleaned_data_boxplot = None
            self.processor.efficiency_data_boxplot = None

        # 6. 预警分析
        if ((self.processor.efficiency_data_ks is not None and len(self.processor.efficiency_data_ks) > 0) or
            (getattr(self.processor, 'efficiency_data_boxplot', None) is not None and len(self.processor.efficiency_data_boxplot) > 0)):
            self.processor.analyze_warning_system()
        else:
            self.processor.warning_events = []

        # 7. 提取预警系统相关数据
        result = self._extract_warning_data()

        self.warning_result = result
        print("=== 预警系统分析完成 ===")

        return result
    
    def _extract_warning_data(self) -> Dict[str, Any]:
        """提取预警系统相关数据"""

        # 选择可用的效率数据（优先K-S，其次箱型图）
        efficiency_df = None
        if getattr(self.processor, 'efficiency_data_ks', None) is not None and len(self.processor.efficiency_data_ks) > 0:
            efficiency_df = self.processor.efficiency_data_ks
        elif getattr(self.processor, 'efficiency_data_boxplot', None) is not None and len(self.processor.efficiency_data_boxplot) > 0:
            efficiency_df = self.processor.efficiency_data_boxplot

        # 数据点
        data_points: List[Dict[str, Any]] = []
        if efficiency_df is not None and len(efficiency_df) > 0:
            for _, row in efficiency_df.iterrows():
                # X轴：时间坐标（小时）
                x_val = row.get('时间坐标', row.get('时间(s)', row.get('time', 0)))

                # Y轴：穿透率（百分比）
                if 'breakthrough_ratio' in row:
                    y_pct = float(row['breakthrough_ratio']) * 100
                elif '穿透率' in row:
                    y_pct = float(row['穿透率']) * 100
                else:
                    # 回退：由效率推算
                    eff_val = float(row.get('efficiency', row.get('处理效率', 0)))
                    y_pct = max(0.0, min(100.0, 100.0 - eff_val))

                # 浓度信息（多版本字段兼容）
                inlet = row.get('inlet_conc', row.get('进口浓度', row.get('进口voc', 0)))
                outlet = row.get('outlet_conc', row.get('出口浓度', row.get('出口voc', 0)))

                # 效率（百分比）
                efficiency_pct = row.get('efficiency', row.get('处理效率', None))
                if efficiency_pct is None and ('breakthrough_ratio' in row or '穿透率' in row):
                    br = float(row.get('breakthrough_ratio', row.get('穿透率', 0)))
                    efficiency_pct = (1 - br) * 100.0

                data_points.append({
                    "x": float(x_val),
                    "y": float(y_pct),
                    "label": f"t={float(x_val):.2f}h: 进口={float(inlet):.2f}, 出口={float(outlet):.2f}, 穿透率={float(y_pct):.1f}%, 效率={float(efficiency_pct):.1f}%"
                })

        # 预警点
        warning_time_val = None
        warning_bt_pct = None
        if hasattr(self.processor, 'warning_model') and getattr(self.processor.warning_model, 'fitted', False):
            if self.processor.warning_model.warning_time is not None:
                warning_time_val = float(self.processor.warning_model.warning_time)
                warning_bt_pct = float(self.processor.warning_model.predict_breakthrough(
                    np.array([warning_time_val]))[0] * 100.0)

        # 统计
        time_values = [p["x"] for p in data_points]
        y_values = [p["y"] for p in data_points]

        return {
            "data_points": data_points,
            "warning_point": {
                "time": warning_time_val,
                "breakthrough_rate": warning_bt_pct,
                "description": (f"预警点(穿透率: {warning_bt_pct:.1f}%)" if warning_bt_pct is not None else None)
            },
            "statistics": {
                "total_data_points": len(data_points),
                "has_warning_point": warning_bt_pct is not None,
                "time_range": {
                    "min": (min(time_values) if time_values else None),
                    "max": (max(time_values) if time_values else None)
                },
                "breakthrough_range": {
                    "min": (min(y_values) if y_values else None),
                    "max": (max(y_values) if y_values else None)
                }
            }
        }

    def _extract_data_points(self) -> AdsorptionAnalysisResult:
        """提取所有数据点信息"""
        
        # 原始数据点
        raw_points = []
        if self.processor.raw_data is not None:
            for _, row in self.processor.raw_data.iterrows():
                # 根据进口0出口1字段判断数据类型
                location = "进口" if row.get('进口0出口1', 1) == 0 else "出口"
                concentration = row.get('浓度(mg/m³)', row.get('出口浓度(mg/m³)', 0))
                time_val = row.get('时间(s)', row.get('时间', 0))

                raw_points.append(DataPoint(
                    x=float(time_val),
                    y=float(concentration),
                    label=f"原始数据({location}) t={time_val:.1f}s, C={concentration:.2f}mg/m³",
                    data_type="原始数据"
                ))
        
        # K-S检验清洗后数据点
        ks_points = []
        if self.processor.cleaned_data_ks is not None:
            for _, row in self.processor.cleaned_data_ks.iterrows():
                location = "进口" if row.get('进口0出口1', 1) == 0 else "出口"
                concentration = row.get('浓度(mg/m³)', row.get('出口浓度(mg/m³)', 0))
                time_val = row.get('时间(s)', row.get('时间', 0))

                ks_points.append(DataPoint(
                    x=float(time_val),
                    y=float(concentration),
                    label=f"K-S清洗({location}) t={time_val:.1f}s, C={concentration:.2f}mg/m³",
                    data_type="K-S清洗"
                ))

        # 箱型图清洗后数据点
        boxplot_points = []
        if self.processor.cleaned_data_boxplot is not None:
            for _, row in self.processor.cleaned_data_boxplot.iterrows():
                location = "进口" if row.get('进口0出口1', 1) == 0 else "出口"
                concentration = row.get('浓度(mg/m³)', row.get('出口浓度(mg/m³)', 0))
                time_val = row.get('时间(s)', row.get('时间', 0))

                boxplot_points.append(DataPoint(
                    x=float(time_val),
                    y=float(concentration),
                    label=f"箱型图清洗({location}) t={time_val:.1f}s, C={concentration:.2f}mg/m³",
                    data_type="箱型图清洗"
                ))
        
        # K-S效率数据点
        eff_ks_points = []
        if self.processor.efficiency_data_ks is not None:
            for _, row in self.processor.efficiency_data_ks.iterrows():
                eff_ks_points.append(DataPoint(
                    x=row['时间(s)'],
                    y=row['吸附效率(%)'],
                    label=f"K-S效率 t={row['时间(s)']:.1f}s, η={row['吸附效率(%)']:.1f}%",
                    data_type="K-S效率"
                ))
        
        # 箱型图效率数据点
        eff_boxplot_points = []
        if self.processor.efficiency_data_boxplot is not None:
            for _, row in self.processor.efficiency_data_boxplot.iterrows():
                eff_boxplot_points.append(DataPoint(
                    x=row['时间(s)'],
                    y=row['吸附效率(%)'],
                    label=f"箱型图效率 t={row['时间(s)']:.1f}s, η={row['吸附效率(%)']:.1f}%",
                    data_type="箱型图效率"
                ))
        
        # 拟合曲线数据点（如果有的话）
        fitted_points = []
        if hasattr(self.processor, 'fitted_data') and self.processor.fitted_data is not None:
            for _, row in self.processor.fitted_data.iterrows():
                fitted_points.append(DataPoint(
                    x=row['时间(s)'],
                    y=row['拟合浓度(mg/m³)'],
                    label=f"拟合曲线 t={row['时间(s)']:.1f}s, C={row['拟合浓度(mg/m³)']:.2f}mg/m³",
                    data_type="拟合曲线"
                ))
        
        # 预警点
        warning_points = []
        for event in self.processor.warning_events:
            # 找到对应时间点的浓度值
            y_value = 0
            if self.processor.efficiency_data_ks is not None:
                closest_row = self.processor.efficiency_data_ks.iloc[
                    (self.processor.efficiency_data_ks['时间(s)'] - event.timestamp).abs().argsort()[:1]
                ]
                if not closest_row.empty:
                    y_value = closest_row.iloc[0]['吸附效率(%)']
            
            warning_points.append(WarningPoint(
                x=event.timestamp,
                y=y_value,
                warning_level=event.warning_level,
                reason=event.reason,
                recommendation=event.recommendation
            ))
        
        # 统计信息
        statistics = self._calculate_statistics()
        
        return AdsorptionAnalysisResult(
            raw_data_points=raw_points,
            cleaned_data_points_ks=ks_points,
            cleaned_data_points_boxplot=boxplot_points,
            efficiency_data_points_ks=eff_ks_points,
            efficiency_data_points_boxplot=eff_boxplot_points,
            fitted_curve_points=fitted_points,
            warning_points=warning_points,
            statistics=statistics
        )
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """计算统计信息"""
        stats = {}
        
        if self.processor.raw_data is not None:
            stats['raw_data_count'] = len(self.processor.raw_data)
            stats['raw_data_time_range'] = {
                'start': self.processor.raw_data['时间(s)'].min(),
                'end': self.processor.raw_data['时间(s)'].max()
            }
            stats['raw_data_concentration_range'] = {
                'min': self.processor.raw_data['出口浓度(mg/m³)'].min(),
                'max': self.processor.raw_data['出口浓度(mg/m³)'].max(),
                'mean': self.processor.raw_data['出口浓度(mg/m³)'].mean()
            }
        
        if self.processor.cleaned_data_ks is not None:
            stats['ks_cleaned_count'] = len(self.processor.cleaned_data_ks)
            stats['ks_cleaning_ratio'] = len(self.processor.cleaned_data_ks) / len(self.processor.raw_data) if self.processor.raw_data is not None else 0
        
        if self.processor.cleaned_data_boxplot is not None:
            stats['boxplot_cleaned_count'] = len(self.processor.cleaned_data_boxplot)
            stats['boxplot_cleaning_ratio'] = len(self.processor.cleaned_data_boxplot) / len(self.processor.raw_data) if self.processor.raw_data is not None else 0
        
        stats['warning_count'] = len(self.processor.warning_events)
        stats['warning_levels'] = {}
        for event in self.processor.warning_events:
            level = event.warning_level.value
            stats['warning_levels'][level] = stats['warning_levels'].get(level, 0) + 1
        
        return stats
    
    def get_data_points_by_type(self, data_type: str) -> List[DataPoint]:
        """
        根据数据类型获取数据点
        
        Args:
            data_type: 数据类型 ("原始数据", "K-S清洗", "箱型图清洗", "K-S效率", "箱型图效率", "拟合曲线")
        
        Returns:
            List[DataPoint]: 指定类型的数据点列表
        """
        if self.analysis_result is None:
            raise ValueError("请先调用analyze()方法进行分析")
        
        type_mapping = {
            "原始数据": self.analysis_result.raw_data_points,
            "K-S清洗": self.analysis_result.cleaned_data_points_ks,
            "箱型图清洗": self.analysis_result.cleaned_data_points_boxplot,
            "K-S效率": self.analysis_result.efficiency_data_points_ks,
            "箱型图效率": self.analysis_result.efficiency_data_points_boxplot,
            "拟合曲线": self.analysis_result.fitted_curve_points
        }
        
        return type_mapping.get(data_type, [])
    
    def get_warning_points_by_level(self, warning_level: WarningLevel) -> List[WarningPoint]:
        """
        根据预警等级获取预警点
        
        Args:
            warning_level: 预警等级
        
        Returns:
            List[WarningPoint]: 指定等级的预警点列表
        """
        if self.analysis_result is None:
            raise ValueError("请先调用analyze()方法进行分析")
        
        return [point for point in self.analysis_result.warning_points 
                if point.warning_level == warning_level]
    
    def export_results_to_dict(self) -> Dict[str, Any]:
        """
        将分析结果导出为字典格式，便于JSON序列化
        
        Returns:
            Dict[str, Any]: 包含所有分析结果的字典
        """
        if self.analysis_result is None:
            raise ValueError("请先调用analyze()方法进行分析")
        
        result = self.analysis_result
        
        return {
            "raw_data_points": [
                {
                    "x": point.x,
                    "y": point.y,
                    "label": point.label,
                    "data_type": point.data_type
                } for point in result.raw_data_points
            ],
            "cleaned_data_points_ks": [
                {
                    "x": point.x,
                    "y": point.y,
                    "label": point.label,
                    "data_type": point.data_type
                } for point in result.cleaned_data_points_ks
            ],
            "cleaned_data_points_boxplot": [
                {
                    "x": point.x,
                    "y": point.y,
                    "label": point.label,
                    "data_type": point.data_type
                } for point in result.cleaned_data_points_boxplot
            ],
            "efficiency_data_points_ks": [
                {
                    "x": point.x,
                    "y": point.y,
                    "label": point.label,
                    "data_type": point.data_type
                } for point in result.efficiency_data_points_ks
            ],
            "efficiency_data_points_boxplot": [
                {
                    "x": point.x,
                    "y": point.y,
                    "label": point.label,
                    "data_type": point.data_type
                } for point in result.efficiency_data_points_boxplot
            ],
            "fitted_curve_points": [
                {
                    "x": point.x,
                    "y": point.y,
                    "label": point.label,
                    "data_type": point.data_type
                } for point in result.fitted_curve_points
            ],
            "warning_points": [
                {
                    "x": point.x,
                    "y": point.y,
                    "warning_level": point.warning_level.value,
                    "reason": point.reason,
                    "recommendation": point.recommendation
                } for point in result.warning_points
            ],
            "statistics": result.statistics
        }


def get_warning_system_data(data_file: str) -> Dict[str, Any]:
    """
    获取预警系统数据的主要接口函数

    Args:
        data_file: 数据文件路径，支持CSV、XLSX、XLS格式

    Returns:
        Dict: 包含以下信息的字典:
            - data_points: 时间段穿透率数据点列表，每个点包含 x(时间h), y(穿透率%), label(描述)
            - warning_point: 预警时间点与穿透率信息
            - statistics: 统计信息
            - success: 是否成功
    """
    try:
        # 创建API实例并分析
        api = AdsorptionAPI(data_file)
        result = api.analyze_warning_system()

        return {
            "success": True,
            "data_points": result["data_points"],  # 所有时间段的穿透率数据点
            "warning_point": result["warning_point"],  # 预警时间点的穿透率
            "statistics": result["statistics"]
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data_points": [],
            "warning_point": {
                "time": None,
                "breakthrough_rate": None,
                "description": None
            },
            "statistics": {}
        }


def create_adsorption_api(data_file: str) -> AdsorptionAPI:
    """
    创建吸附曲线分析API实例

    Args:
        data_file: 数据文件路径

    Returns:
        AdsorptionAPI: API实例
    """
    return AdsorptionAPI(data_file)

def analyze_adsorption_data(data_file: str) -> Dict[str, Any]:
    """
    一键分析吸附数据，返回所有数据点坐标、标签和预警点信息

    Args:
        data_file: 数据文件路径，支持CSV、XLSX、XLS格式

    Returns:
        Dict[str, Any]: 包含以下信息的字典:
            - all_data_points: 所有数据点的x,y坐标和标签
            - warning_points: 预警点的x,y坐标和相关信息
            - statistics: 统计信息
            - success: 是否成功
    """
    try:
        # 创建API实例并分析
        api = AdsorptionAPI(data_file)
        # 旧接口保留：若需要完整数据点可在后续补充。此处直接复用预警系统输出
        warning_result = api.analyze_warning_system()

        # 整理所有数据点（用预警系统数据点作为统一输出）
        all_data_points = []

        for dp in warning_result.get('data_points', []):
            all_data_points.append({
                "x": dp.get('x'),
                "y": dp.get('y'),
                "label": dp.get('label'),
                "type": "时间段穿透率",
                "data_category": "breakthrough"
            })

        # 整理预警点信息
        warning_points = []
        wp = warning_result.get('warning_point', {})
        if wp.get('breakthrough_rate') is not None:
            warning_points.append({
                "x": wp.get('time'),
                "y": wp.get('breakthrough_rate'),
                "warning_level": "预警点",
                "reason": wp.get('description'),
                "recommendation": "超过预警点，请关注更换周期",
                "color_code": "#FFA500"
            })

        return {
            "success": True,
            "all_data_points": all_data_points,
            "warning_points": warning_points,
            "statistics": warning_result.get('statistics', {}),
            "data_summary": {
                "total_points": len(all_data_points),
                "warning_count": len(warning_points),
                "data_types": list(set([p["type"] for p in all_data_points])),
                "time_range": {
                    "min": min([p["x"] for p in all_data_points]) if all_data_points else None,
                    "max": max([p["x"] for p in all_data_points]) if all_data_points else None
                }
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "all_data_points": [],
            "warning_points": [],
            "statistics": {},
            "data_summary": {}
        }


# 示例使用
if __name__ == "__main__":
    print("=== 预警系统API示例 ===")

    # 使用主要接口函数
    data_file = "可视化项目/7.24.csv"
    result = get_warning_system_data(data_file)

    if result["success"]:
        print("✅ 预警系统分析成功")

        # 显示时间段穿透率数据点
        data_points = result["data_points"]
        print(f"\n📊 时间段穿透率数据点: {len(data_points)} 个")
        if data_points:
            print("前5个数据点:")
            for i, point in enumerate(data_points[:5]):
                print(f"  t={point['x']:.2f}h: 穿透率={point['y']:.1f}%")
                print(f"    标签: {point['label']}")

        # 显示预警时间点的穿透率
        warning_point = result["warning_point"]
        print(f"\n⭐ 预警时间点信息:")
        if warning_point["breakthrough_rate"] is not None:
            print(f"  时间: {warning_point['time']:.2f}h")
            print(f"  穿透率: {warning_point['breakthrough_rate']:.1f}%")
            print(f"  描述: {warning_point['description']}")
        else:
            print("  无预警点")

        # 显示统计信息
        stats = result["statistics"]
        print(f"\n📈 统计信息:")
        print(f"  数据点总数: {stats['total_data_points']}")
        print(f"  是否有预警点: {stats['has_warning_point']}")
        if stats.get('time_range'):
            print(f"  时间范围(h): {stats['time_range']['min']:.2f} - {stats['time_range']['max']:.2f}")
        if stats.get('breakthrough_range'):
            print(f"  穿透率范围(%): {stats['breakthrough_range']['min']:.1f} - {stats['breakthrough_range']['max']:.1f}")

        # 返回格式示例
        print(f"\n📋 返回数据格式:")
        print(f"  data_points: 列表，每个元素包含 x(时间h), y(穿透率%), label(描述)")
        print(f"  warning_point: 字典，包含 time(时间h), breakthrough_rate(%) 和描述")
        print(f"  statistics: 字典，包含统计信息")

        # 提取坐标用于绘图
        x_coords = [p['x'] for p in data_points]  # 时间(h)
        y_coords = [p['y'] for p in data_points]  # 穿透率%
        labels = [p['label'] for p in data_points]  # 标签

        print(f"\n🎯 可用于绘图的数据:")
        print(f"  X坐标(时间h): {x_coords[:10]}...")  # 显示前10个
        print(f"  Y坐标(穿透率%): {y_coords[:10]}...")  # 显示前10个
        print(f"  预警点穿透率: {warning_point['breakthrough_rate']:.1f}%" if warning_point['breakthrough_rate'] else "无预警点")

    else:
        print(f"❌ 预警系统分析失败: {result['error']}")

    print("\n=== API调用完成 ===")
