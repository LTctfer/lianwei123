"""
三色预警系统核心模块
基于污染物浓度、源强、风险等级实现智能分级预警
支持黄色-橙色-红色三级预警机制
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class WarningLevel:
    """预警等级数据类"""
    level: str  # 'yellow', 'orange', 'red'
    name: str   # 预警名称
    color: str  # 颜色代码
    threshold_min: float  # 最小阈值
    threshold_max: float  # 最大阈值
    description: str      # 描述
    actions: List[str]    # 应对措施

@dataclass
class PollutionAlert:
    """污染预警数据类"""
    alert_id: str
    timestamp: datetime
    level: WarningLevel
    source_location: Dict[str, float]  # {x, y, z}
    source_strength: float
    affected_area: float  # 影响面积 (km²)
    max_concentration: float  # 最大预测浓度
    risk_score: float  # 风险评分 (0-100)
    confidence: float  # 置信度 (0-1)
    duration_forecast: int  # 预计持续时间 (小时)
    meteorological_conditions: Dict[str, Any]
    recommended_actions: List[str]
    status: str = 'active'  # 'active', 'resolved', 'escalated'

class ThreeColorWarningSystem:
    """三色预警系统"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化三色预警系统
        
        Args:
            config: 系统配置参数
        """
        self.config = config
        self.warning_levels = self._initialize_warning_levels()
        self.active_alerts: List[PollutionAlert] = []
        self.alert_history: List[PollutionAlert] = []
        self.risk_assessment_weights = {
            'concentration': 0.3,
            'source_strength': 0.25,
            'affected_area': 0.2,
            'wind_conditions': 0.15,
            'population_density': 0.1
        }
        
    def _initialize_warning_levels(self) -> Dict[str, WarningLevel]:
        """初始化预警等级定义"""
        return {
            'yellow': WarningLevel(
                level='yellow',
                name='黄色预警',
                color='#FFA500',
                threshold_min=75,    # PM2.5 μg/m³
                threshold_max=150,
                description='轻度污染，建议采取初步防护措施',
                actions=[
                    '加强监测频率',
                    '通知敏感人群减少户外活动',
                    '检查污染源排放情况',
                    '准备应急响应方案'
                ]
            ),
            'orange': WarningLevel(
                level='orange',
                name='橙色预警',
                color='#FF4500',
                threshold_min=150,
                threshold_max=250,
                description='中度污染，需要采取有效防护措施',
                actions=[
                    '启动二级响应',
                    '限制重点污染源排放',
                    '建议学校停止户外活动',
                    '增加道路清洁频次',
                    '发布健康提示'
                ]
            ),
            'red': WarningLevel(
                level='red',
                name='红色预警',
                color='#FF0000',
                threshold_min=250,
                threshold_max=float('inf'),
                description='重度污染，必须采取紧急措施',
                actions=[
                    '启动一级响应',
                    '强制重点污染源停产限产',
                    '实施机动车限行',
                    '中小学停课',
                    '建议停止一切户外活动',
                    '启动人工影响天气作业'
                ]
            )
        }
    
    def calculate_risk_score(self, 
                           concentration: float,
                           source_strength: float,
                           affected_area: float,
                           meteorological_data: Dict[str, Any],
                           population_density: float = 1000) -> float:
        """
        计算风险评分
        
        Args:
            concentration: 最大预测浓度
            source_strength: 源强
            affected_area: 影响面积
            meteorological_data: 气象数据
            population_density: 人口密度 (人/km²)
            
        Returns:
            风险评分 (0-100)
        """
        # 浓度风险评分 (0-30分)
        conc_score = min(30, (concentration / 500) * 30)
        
        # 源强风险评分 (0-25分)
        strength_score = min(25, (source_strength / 100) * 25)
        
        # 影响面积风险评分 (0-20分)
        area_score = min(20, (affected_area / 100) * 20)
        
        # 气象条件风险评分 (0-15分)
        wind_speed = meteorological_data.get('wind_speed', 2.0)
        stability_class = meteorological_data.get('stability_class', 'D')
        
        # 低风速和稳定大气条件增加风险
        wind_risk = max(0, 15 - wind_speed * 3)
        stability_risk = {'A': 2, 'B': 4, 'C': 6, 'D': 8, 'E': 12, 'F': 15}.get(stability_class, 8)
        weather_score = min(15, (wind_risk + stability_risk) / 2)
        
        # 人口密度风险评分 (0-10分)
        pop_score = min(10, (population_density / 5000) * 10)
        
        # 总风险评分
        total_score = conc_score + strength_score + area_score + weather_score + pop_score
        
        return min(100, total_score)
    
    def determine_warning_level(self, 
                              concentration: float,
                              risk_score: float) -> WarningLevel:
        """
        确定预警等级
        
        Args:
            concentration: 最大预测浓度
            risk_score: 风险评分
            
        Returns:
            预警等级
        """
        # 基于浓度的初步判断
        if concentration >= self.warning_levels['red'].threshold_min:
            primary_level = 'red'
        elif concentration >= self.warning_levels['orange'].threshold_min:
            primary_level = 'orange'
        elif concentration >= self.warning_levels['yellow'].threshold_min:
            primary_level = 'yellow'
        else:
            # 低于黄色预警阈值，但考虑风险评分
            if risk_score >= 70:
                primary_level = 'yellow'
            else:
                return None  # 无需预警
        
        # 风险评分调整
        if risk_score >= 80 and primary_level != 'red':
            # 高风险评分可能升级预警
            if primary_level == 'orange':
                primary_level = 'red'
            elif primary_level == 'yellow':
                primary_level = 'orange'
        
        return self.warning_levels[primary_level]
    
    def forecast_pollution_trend(self,
                               current_concentration: float,
                               source_strength: float,
                               meteorological_forecast: List[Dict[str, Any]],
                               hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """
        预测污染趋势
        
        Args:
            current_concentration: 当前浓度
            source_strength: 源强
            meteorological_forecast: 气象预报数据
            hours_ahead: 预测小时数
            
        Returns:
            未来污染趋势预测
        """
        trend_forecast = []
        
        for hour in range(hours_ahead):
            if hour < len(meteorological_forecast):
                meteo = meteorological_forecast[hour]
            else:
                meteo = meteorological_forecast[-1]  # 使用最后的气象数据
            
            # 简化的浓度预测模型
            wind_speed = meteo.get('wind_speed', 2.0)
            wind_direction = meteo.get('wind_direction', 180)
            stability = meteo.get('stability_class', 'D')
            
            # 扩散因子计算
            diffusion_factor = wind_speed * {'A': 2.0, 'B': 1.5, 'C': 1.0, 'D': 0.8, 'E': 0.5, 'F': 0.3}.get(stability, 0.8)
            
            # 预测浓度（简化模型）
            predicted_conc = current_concentration * np.exp(-diffusion_factor * hour / 24)
            
            # 考虑源强持续影响
            if source_strength > 0:
                source_contribution = source_strength / diffusion_factor * (1 - np.exp(-hour / 6))
                predicted_conc += source_contribution
            
            trend_forecast.append({
                'hour': hour + 1,
                'predicted_concentration': max(0, predicted_conc),
                'wind_speed': wind_speed,
                'wind_direction': wind_direction,
                'diffusion_factor': diffusion_factor
            })
        
        return trend_forecast
    
    def create_pollution_alert(self,
                             source_location: Dict[str, float],
                             source_strength: float,
                             concentration_field: Dict[str, Any],
                             meteorological_data: Dict[str, Any],
                             confidence: float = 0.8) -> Optional[PollutionAlert]:
        """
        创建污染预警
        
        Args:
            source_location: 污染源位置
            source_strength: 源强
            concentration_field: 浓度场数据
            meteorological_data: 气象数据
            confidence: 预测置信度
            
        Returns:
            污染预警对象或None
        """
        # 计算最大浓度和影响面积
        max_concentration = concentration_field.get('max_concentration', 0)
        
        # 计算影响面积（浓度 > 35 μg/m³的区域）
        conc_array = np.array(concentration_field.get('concentration', []))
        affected_cells = np.sum(conc_array > 35)
        grid_resolution = len(conc_array)
        area_per_cell = (2000 / grid_resolution) ** 2 / 1e6  # km²
        affected_area = affected_cells * area_per_cell
        
        # 计算风险评分
        risk_score = self.calculate_risk_score(
            max_concentration, source_strength, affected_area, meteorological_data
        )
        
        # 确定预警等级
        warning_level = self.determine_warning_level(max_concentration, risk_score)
        
        if warning_level is None:
            logger.info(f"浓度 {max_concentration:.1f} μg/m³ 未达到预警阈值")
            return None
        
        # 预测持续时间
        duration_forecast = max(1, int(12 - meteorological_data.get('wind_speed', 2) * 2))
        
        # 创建预警对象
        alert_id = f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        alert = PollutionAlert(
            alert_id=alert_id,
            timestamp=datetime.now(),
            level=warning_level,
            source_location=source_location,
            source_strength=source_strength,
            affected_area=affected_area,
            max_concentration=max_concentration,
            risk_score=risk_score,
            confidence=confidence,
            duration_forecast=duration_forecast,
            meteorological_conditions=meteorological_data.copy(),
            recommended_actions=warning_level.actions.copy()
        )
        
        logger.info(f"创建 {warning_level.name} 预警: {alert_id}")
        logger.info(f"最大浓度: {max_concentration:.1f} μg/m³, 风险评分: {risk_score:.1f}")
        
        return alert
    
    def process_alert(self, alert: PollutionAlert) -> Dict[str, Any]:
        """
        处理预警
        
        Args:
            alert: 预警对象
            
        Returns:
            处理结果
        """
        # 添加到活跃预警列表
        self.active_alerts.append(alert)
        
        # 生成预警报告
        report = self.generate_alert_report(alert)
        
        # 触发应急响应流程
        response_actions = self.trigger_emergency_response(alert)
        
        # 记录预警历史
        self.alert_history.append(alert)
        
        logger.info(f"预警 {alert.alert_id} 处理完成")
        
        return {
            'alert_id': alert.alert_id,
            'level': alert.level.level,
            'status': 'processed',
            'report': report,
            'response_actions': response_actions,
            'timestamp': alert.timestamp.isoformat()
        }
    
    def generate_alert_report(self, alert: PollutionAlert) -> Dict[str, Any]:
        """
        生成预警报告
        
        Args:
            alert: 预警对象
            
        Returns:
            预警报告
        """
        report = {
            'alert_summary': {
                'id': alert.alert_id,
                'level': alert.level.name,
                'timestamp': alert.timestamp.isoformat(),
                'status': alert.status
            },
            'pollution_analysis': {
                'source_location': alert.source_location,
                'source_strength': alert.source_strength,
                'max_concentration': alert.max_concentration,
                'affected_area_km2': alert.affected_area,
                'risk_score': alert.risk_score,
                'confidence': alert.confidence
            },
            'meteorological_conditions': alert.meteorological_conditions,
            'impact_assessment': {
                'duration_forecast_hours': alert.duration_forecast,
                'affected_population_estimate': int(alert.affected_area * 1000),  # 假设每km² 1000人
                'health_risk_level': self._assess_health_risk(alert.level.level)
            },
            'recommended_actions': alert.recommended_actions,
            'response_urgency': self._calculate_response_urgency(alert)
        }
        
        return report
    
    def trigger_emergency_response(self, alert: PollutionAlert) -> List[Dict[str, Any]]:
        """
        触发应急响应
        
        Args:
            alert: 预警对象
            
        Returns:
            应急响应措施列表
        """
        response_actions = []
        
        for action in alert.recommended_actions:
            response_actions.append({
                'action': action,
                'priority': self._get_action_priority(action, alert.level.level),
                'responsible_department': self._get_responsible_department(action),
                'timeline': self._get_action_timeline(action, alert.level.level),
                'status': 'pending'
            })
        
        # 特殊响应措施
        if alert.level.level == 'red':
            response_actions.extend([
                {
                    'action': '启动应急指挥中心',
                    'priority': 'urgent',
                    'responsible_department': '应急管理部门',
                    'timeline': '立即',
                    'status': 'pending'
                },
                {
                    'action': '通知媒体发布预警信息',
                    'priority': 'high',
                    'responsible_department': '宣传部门',
                    'timeline': '30分钟内',
                    'status': 'pending'
                }
            ])
        
        return response_actions
    
    def update_alert_status(self, alert_id: str, new_status: str, notes: str = "") -> bool:
        """
        更新预警状态
        
        Args:
            alert_id: 预警ID
            new_status: 新状态
            notes: 备注
            
        Returns:
            更新是否成功
        """
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.status = new_status
                logger.info(f"预警 {alert_id} 状态更新为: {new_status}")
                
                if new_status in ['resolved', 'cancelled']:
                    self.active_alerts.remove(alert)
                
                return True
        
        return False
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃预警列表"""
        return [{
            'alert_id': alert.alert_id,
            'level': alert.level.level,
            'level_name': alert.level.name,
            'timestamp': alert.timestamp.isoformat(),
            'max_concentration': alert.max_concentration,
            'risk_score': alert.risk_score,
            'status': alert.status,
            'duration_forecast': alert.duration_forecast
        } for alert in self.active_alerts]
    
    def get_warning_statistics(self) -> Dict[str, Any]:
        """获取预警统计信息"""
        total_alerts = len(self.alert_history)
        
        if total_alerts == 0:
            return {'total_alerts': 0, 'message': '暂无预警记录'}
        
        level_counts = {'yellow': 0, 'orange': 0, 'red': 0}
        for alert in self.alert_history:
            level_counts[alert.level.level] += 1
        
        # 最近30天的预警趋势
        recent_alerts = [alert for alert in self.alert_history 
                        if alert.timestamp > datetime.now() - timedelta(days=30)]
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': len(self.active_alerts),
            'level_distribution': level_counts,
            'recent_30days': len(recent_alerts),
            'average_risk_score': np.mean([alert.risk_score for alert in self.alert_history]),
            'average_duration': np.mean([alert.duration_forecast for alert in self.alert_history])
        }
    
    def _assess_health_risk(self, level: str) -> str:
        """评估健康风险等级"""
        risk_map = {
            'yellow': '轻微健康风险',
            'orange': '中等健康风险',
            'red': '严重健康风险'
        }
        return risk_map.get(level, '未知风险')
    
    def _calculate_response_urgency(self, alert: PollutionAlert) -> str:
        """计算响应紧急程度"""
        if alert.level.level == 'red' or alert.risk_score >= 80:
            return 'urgent'
        elif alert.level.level == 'orange' or alert.risk_score >= 60:
            return 'high'
        else:
            return 'medium'
    
    def _get_action_priority(self, action: str, level: str) -> str:
        """获取措施优先级"""
        urgent_keywords = ['停产', '限行', '停课', '启动一级']
        high_keywords = ['限制', '减少', '启动二级', '增加']
        
        if level == 'red' or any(keyword in action for keyword in urgent_keywords):
            return 'urgent'
        elif level == 'orange' or any(keyword in action for keyword in high_keywords):
            return 'high'
        else:
            return 'medium'
    
    def _get_responsible_department(self, action: str) -> str:
        """获取负责部门"""
        department_map = {
            '监测': '环保部门',
            '限产': '工业管理部门',
            '限行': '交通管理部门',
            '停课': '教育部门',
            '清洁': '城管部门',
            '健康': '卫生部门'
        }
        
        for keyword, dept in department_map.items():
            if keyword in action:
                return dept
        
        return '环保部门'  # 默认
    
    def _get_action_timeline(self, action: str, level: str) -> str:
        """获取措施时限"""
        if level == 'red':
            return '立即执行'
        elif level == 'orange':
            return '2小时内'
        else:
            return '6小时内'
    
    def export_alert_data(self, filepath: str):
        """导出预警数据"""
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'warning_levels': {level: {
                'name': wl.name,
                'threshold_min': wl.threshold_min,
                'threshold_max': wl.threshold_max,
                'description': wl.description,
                'actions': wl.actions
            } for level, wl in self.warning_levels.items()},
            'active_alerts': self.get_active_alerts(),
            'statistics': self.get_warning_statistics(),
            'total_historical_alerts': len(self.alert_history)
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            logger.info(f"预警数据已导出到: {filepath}")
        except Exception as e:
            logger.error(f"预警数据导出失败: {e}")