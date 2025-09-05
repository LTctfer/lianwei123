#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
废气处理设备预警系统
包含数据清洗、预警规则检测和可视化功能
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import warnings
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import time
import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

warnings.filterwarnings('ignore')

class RealTimeDataGenerator:
    """实时数据生成器"""
    
    def __init__(self):
        self.running = False
        self.data_history = []
        self.alert_history = []
        self.equipment_status = {
            '燃烧室': 'normal',
            '废气出口': 'normal',
            '吸附设施': 'normal', 
            '脱附设施': 'normal',
            '反应器': 'normal',
            '应急系统': 'normal'
        }
        
    def generate_realtime_data(self):
        """生成实时数据，保证5秒内1条报警"""
        current_time = datetime.now()
        
        # 基础数据生成
        data = {
            'timestamp': current_time.isoformat(),
            'temperature_combustion': random.gauss(780, 30),
            'temperature_outlet': random.gauss(45, 12),
            'concentration_in': random.gauss(200, 40),
            'concentration_out': random.gauss(20, 8),
            'temperature_adsorption': random.gauss(35, 6),
            'temperature_desorption': random.gauss(105, 10),
            'temperature_reactor_outlet': random.gauss(550, 50),
            'pressure': random.gauss(1.2, 0.3),
            'flow_rate': random.gauss(1000, 80),
            'efficiency': random.gauss(95, 3),
            'emergency_valve': 0,
            'pressure_loss_catalytic': random.gauss(1.2, 0.3),
            'particle_content': random.gauss(5, 2)
        }
        
        # 保证报警频率：5秒内1条报警 (40%概率)
        alerts = []
        
        # 40%概率触发报警
        if random.random() < 0.4:
            # 随机选择一种报警类型
            alert_types = [
                {
                'type': '燃烧室温度不达标',
                    'field': 'temperature_combustion',
                    'value_range': (720, 759),
                'severity': 'high',
                    'equipment': '燃烧室',
                    'threshold': 760,
                    'unit': '℃'
                },
                {
                    'type': '废气出口污染物浓度超标',
                    'field': 'concentration_out',
                    'value_range': (55, 90),
                'severity': 'critical',
                    'equipment': '废气出口',
                    'threshold': 50,
                    'unit': 'mg/m³'
                },
                {
                'type': '出口温度超标',
                    'field': 'temperature_outlet',
                    'value_range': (65, 85),
                'severity': 'medium',
                    'equipment': '废气出口',
                    'threshold': 60,
                    'unit': '℃'
                },
                {
                'type': '反应器出口温度异常',
                    'field': 'temperature_reactor_outlet',
                    'value_range': (610, 650),
                'severity': 'critical',
                    'equipment': '反应器',
                    'threshold': 600,
                    'unit': '℃'
                },
                {
                'type': '吸附温度异常',
                    'field': 'temperature_adsorption',
                    'value_range': (42, 55),
                'severity': 'medium',
                    'equipment': '吸附设施',
                    'threshold': 40,
                    'unit': '℃'
                },
                {
                'type': '脱附温度异常',
                    'field': 'temperature_desorption',
                    'value_range': (70, 89),
                'severity': 'medium',
                    'equipment': '脱附设施',
                    'threshold': 90,
                    'unit': '℃'
                },
                {
                    'type': '应急阀门违规开启',
                    'field': 'emergency_valve',
                    'value_range': (1, 1),
                    'severity': 'critical',
                    'equipment': '应急系统',
                    'threshold': 0,
                    'unit': ''
                },
                {
                    'type': '催化燃烧压力异常',
                    'field': 'pressure_loss_catalytic',
                    'value_range': (2.1, 3.0),
                    'severity': 'medium',
                    'equipment': '催化燃烧装置',
                    'threshold': 2,
                    'unit': 'kPa'
                },
                {
                    'type': '颗粒物含量超标',
                    'field': 'particle_content',
                    'value_range': (11, 20),
                    'severity': 'medium',
                    'equipment': '过滤系统',
                    'threshold': 10,
                    'unit': 'mg/m³'
                }
            ]
            
            # 随机选择一个报警类型
            alert_config = random.choice(alert_types)
            
            # 设置异常值
            if alert_config['field'] == 'emergency_valve':
                data[alert_config['field']] = 1
            else:
                data[alert_config['field']] = random.uniform(*alert_config['value_range'])
            
            # 创建报警信息
            alert = {
                'type': alert_config['type'],
                'value': data[alert_config['field']],
                'severity': alert_config['severity'],
                'equipment': alert_config['equipment'],
                'threshold': alert_config['threshold'],
                'unit': alert_config['unit'],
                'timestamp': current_time.isoformat(),
                'id': f"alert_{int(current_time.timestamp())}"
            }
            alerts.append(alert)
            
            # 更新设备状态
            if alert_config['severity'] == 'critical':
                self.equipment_status[alert_config['equipment']] = 'critical'
            elif alert_config['severity'] == 'high':
                self.equipment_status[alert_config['equipment']] = 'warning'
            else:
                self.equipment_status[alert_config['equipment']] = 'warning'
        
        # 保存数据历史
        self.data_history.append(data)
        if len(self.data_history) > 100:
            self.data_history.pop(0)
            
        # 保存告警历史（保持3分钟）
        for alert in alerts:
            alert['timestamp'] = current_time
            self.alert_history.append(alert)
            
        # 清除3分钟前的告警
        cutoff_time = current_time - timedelta(minutes=3)
        self.alert_history = [alert for alert in self.alert_history 
                            if alert['timestamp'] > cutoff_time]
        
        # 随机重置正常设备状态
        for equipment in self.equipment_status:
            if random.random() < 0.3:  # 30%概率恢复正常
                self.equipment_status[equipment] = 'normal'
        
        return {
            'realtime': data,
            'alerts': alerts,
            'alert_history': self.alert_history,
            'equipment_status': self.equipment_status,
            'trend_data': self.data_history[-20:] if len(self.data_history) >= 20 else self.data_history
        }

@dataclass
class WarningRule:
    """预警规则配置"""
    rule_id: str
    rule_name: str
    description: str
    condition: str
    threshold_value: float
    threshold_unit: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    is_active: bool = True

@dataclass
class WarningRecord:
    """违规记录"""
    record_id: str
    rule_id: str
    rule_name: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[float]  # 持续时间(小时)
    max_value: float
    min_value: float
    avg_value: float
    severity: str
    status: str  # 'ongoing', 'resolved'
    affected_equipment: str

class DataCleaner:
    """数据清洗器"""
    
    def __init__(self):
        self.cleaning_log = []
    
    def load_data(self, file_path: str) -> pd.DataFrame:
        """加载数据文件"""
        file_path = Path(file_path)
        
        try:
            if str(file_path).endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            elif str(file_path).endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"不支持的文件格式: {str(file_path)}")
            
            print(f"✅ 数据加载成功: {len(df)} 行, {len(df.columns)} 列")
            return df
            
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            return pd.DataFrame()
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据清洗"""
        if df.empty:
            return df
        
        original_rows = len(df)
        self.cleaning_log.clear()
        
        # 1. 处理时间列
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['timestamp'])
            self.cleaning_log.append(f"时间格式转换: 保留 {len(df)} 行")
        
        # 2. 处理数值列
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            # 记录原始统计
            original_count = df[col].count()
            
            # 处理负值 (设为NaN)
            negative_count = (df[col] < 0).sum()
            df.loc[df[col] < 0, col] = np.nan
            
            # 处理零值 (根据列名判断是否保留)
            zero_count = (df[col] == 0).sum()
            if col in ['concentration_in', 'concentration_out', 'temperature', 'pressure']:
                # 这些列的零值可能是异常，设为NaN
                df.loc[df[col] == 0, col] = np.nan
            
            # 处理异常值 (使用IQR方法)
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_count = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            df.loc[(df[col] < lower_bound) | (df[col] > upper_bound), col] = np.nan
            
            cleaned_count = df[col].count()
            
            self.cleaning_log.append(
                f"{col}: 原始{original_count} → 清洗后{cleaned_count} "
                f"(负值:{negative_count}, 零值:{zero_count}, 异常值:{outlier_count})"
            )
        
        # 3. 删除全为NaN的行
        df = df.dropna(how='all')
        
        # 4. 对于关键列，使用前向填充
        key_columns = ['temperature_combustion', 'temperature_outlet', 'concentration_in', 'concentration_out']
        for col in key_columns:
            if col in df.columns:
                df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
        
        cleaned_rows = len(df)
        self.cleaning_log.append(f"最终结果: {original_rows} → {cleaned_rows} 行 (清洗率: {(1-cleaned_rows/original_rows)*100:.1f}%)")
        
        print("🧹 数据清洗完成:")
        for log in self.cleaning_log:
            print(f"  {log}")
        
        return df

class WarningRuleEngine:
    """预警规则引擎"""
    
    def __init__(self):
        self.rules = self._initialize_rules()
        self.warning_records = []
        self.active_warnings = {}  # 正在进行的预警
    
    def _initialize_rules(self) -> List[WarningRule]:
        """初始化预警规则"""
        rules = [
            WarningRule("R001", "燃烧室温度不达标", "燃烧室温度未达到规定值760℃以上", "temperature_combustion < 760", 760, "℃", "high"),
            WarningRule("R002", "废气出口污染物浓度超标", "废气出口污染物浓度超标", "concentration_out > threshold", 50, "mg/m³", "critical"),
            WarningRule("R003", "应急阀门违规开启", "应急阀门违规开启", "emergency_valve == 1", 1, "", "critical"),
            WarningRule("R004", "处理效率不达标", "出口浓度/进口浓度 > 0.1", "efficiency < 0.9", 0.9, "", "high"),
            WarningRule("R005", "废气出口温度超标", "废气出口温度不能超过60℃", "temperature_outlet > 60", 60, "℃", "medium"),
            WarningRule("R006", "治污设备未先启后停", "治污设备未先启后停", "equipment_sequence_error == 1", 1, "", "high"),
            WarningRule("R007", "吸附温度异常", "吸附温度超过40℃", "temperature_adsorption > 40", 40, "℃", "medium"),
            WarningRule("R008", "脱附温度异常", "脱附温度不在90-120℃范围", "temperature_desorption < 90 or temperature_desorption > 120", 90, "℃", "medium"),
            WarningRule("R009", "脱附时长不符合", "脱附时长少于3小时", "desorption_duration < 3", 3, "小时", "medium"),
            WarningRule("R010", "长期未脱附", "超过1个月未脱附", "days_since_last_desorption > 30", 30, "天", "high"),
            WarningRule("R011", "过滤材料失效", "颗粒物含量超过10mg/m³或压力损失超过1KPA", "particle_content > 10 or pressure_loss > 1", 10, "mg/m³", "medium"),
            WarningRule("R012", "进气温度超标", "进入催化燃烧装置的废气温度超过400℃", "temperature_inlet > 400", 400, "℃", "high"),
            WarningRule("R013", "预热室温度异常", "预热室温度超过400℃或不在250-350℃范围", "temperature_preheat > 400 or temperature_preheat < 250", 350, "℃", "medium"),
            WarningRule("R014", "催化燃烧压力异常", "催化燃烧装置压力损失超过2kpa", "pressure_loss_catalytic > 2", 2, "kPa", "medium"),
            WarningRule("R015", "反应器出口温度异常", "反应器出口温度超过600℃", "temperature_reactor_outlet > 600", 600, "℃", "critical"),
            WarningRule("R016", "催化剂使用周期超标", "催化剂使用周期超标", "catalyst_usage_days > 365", 365, "天", "high"),
        ]
        return rules
    
    def check_rules(self, df: pd.DataFrame) -> List[Dict]:
        """检查预警规则"""
        violations = []
        
        for _, row in df.iterrows():
            timestamp = row.get('timestamp')
            if timestamp is None:
                timestamp = datetime.now()
            
            for rule in self.rules:
                if not rule.is_active:
                    continue
                
                violation_detected = self._evaluate_rule(rule, row)
                
                if violation_detected:
                    # 检查是否是新的违规或持续的违规
                    if rule.rule_id not in self.active_warnings:
                        # 新违规开始
                        record = WarningRecord(
                            record_id=f"{rule.rule_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                            rule_id=rule.rule_id,
                            rule_name=rule.rule_name,
                            start_time=timestamp,
                            end_time=None,
                            duration=None,
                            max_value=self._get_rule_value(rule, row),
                            min_value=self._get_rule_value(rule, row),
                            avg_value=self._get_rule_value(rule, row),
                            severity=rule.severity,
                            status='ongoing',
                            affected_equipment=self._get_equipment_name(rule)
                        )
                        self.active_warnings[rule.rule_id] = record
                        violations.append({
                            'timestamp': timestamp,
                            'rule_id': rule.rule_id,
                            'rule_name': rule.rule_name,
                            'value': self._get_rule_value(rule, row),
                            'threshold': rule.threshold_value,
                            'severity': rule.severity,
                            'status': 'start'
                        })
                    else:
                        # 更新持续违规
                        record = self.active_warnings[rule.rule_id]
                        current_value = self._get_rule_value(rule, row)
                        record.max_value = max(record.max_value, current_value)
                        record.min_value = min(record.min_value, current_value)
                        violations.append({
                            'timestamp': timestamp,
                            'rule_id': rule.rule_id,
                            'rule_name': rule.rule_name,
                            'value': current_value,
                            'threshold': rule.threshold_value,
                            'severity': rule.severity,
                            'status': 'ongoing'
                        })
                else:
                    # 检查是否有违规结束
                    if rule.rule_id in self.active_warnings:
                        record = self.active_warnings[rule.rule_id]
                        record.end_time = timestamp
                        record.duration = (record.end_time - record.start_time).total_seconds() / 3600
                        record.status = 'resolved'
                        
                        self.warning_records.append(record)
                        del self.active_warnings[rule.rule_id]
                        
                        violations.append({
                            'timestamp': timestamp,
                            'rule_id': rule.rule_id,
                            'rule_name': rule.rule_name,
                            'value': self._get_rule_value(rule, row),
                            'threshold': rule.threshold_value,
                            'severity': rule.severity,
                            'status': 'end'
                        })
        
        return violations
    
    def _evaluate_rule(self, rule: WarningRule, row: pd.Series) -> bool:
        """评估单个规则"""
        try:
            # 根据规则ID执行特定的检查逻辑
            if rule.rule_id == "R001":  # 燃烧室温度
                temp = row.get('temperature_combustion', 0)
                return float(temp or 0) < 760
            elif rule.rule_id == "R002":  # 出口浓度
                conc = row.get('concentration_out', 0)
                return float(conc or 0) > rule.threshold_value
            elif rule.rule_id == "R003":  # 应急阀门
                valve = row.get('emergency_valve', 0)
                return float(valve or 0) == 1
            elif rule.rule_id == "R004":  # 处理效率
                conc_in = float(row.get('concentration_in', 1) or 1)
                conc_out = float(row.get('concentration_out', 0) or 0)
                efficiency = 1 - (conc_out / conc_in) if conc_in > 0 else 0
                return efficiency < 0.9
            elif rule.rule_id == "R005":  # 出口温度
                temp = row.get('temperature_outlet', 0)
                return float(temp or 0) > 60
            elif rule.rule_id == "R007":  # 吸附温度
                temp = row.get('temperature_adsorption', 0)
                return float(temp or 0) > 40
            elif rule.rule_id == "R008":  # 脱附温度
                temp = float(row.get('temperature_desorption', 0) or 0)
                return temp < 90 or temp > 120
            elif rule.rule_id == "R015":  # 反应器出口温度
                temp = row.get('temperature_reactor_outlet', 0)
                return float(temp or 0) > 600
            # 可以继续添加其他规则的具体实现
            
            return False
        except Exception as e:
            print(f"规则评估错误 {rule.rule_id}: {e}")
            return False
    
    def _get_rule_value(self, rule: WarningRule, row: pd.Series) -> float:
        """获取规则对应的数值"""
        value_mapping = {
            "R001": float(row.get('temperature_combustion', 0) or 0),
            "R002": float(row.get('concentration_out', 0) or 0),
            "R003": float(row.get('emergency_valve', 0) or 0),
            "R005": float(row.get('temperature_outlet', 0) or 0),
            "R007": float(row.get('temperature_adsorption', 0) or 0),
            "R008": float(row.get('temperature_desorption', 0) or 0),
            "R015": float(row.get('temperature_reactor_outlet', 0) or 0),
        }
        return value_mapping.get(rule.rule_id, 0.0)
    
    def _get_equipment_name(self, rule: WarningRule) -> str:
        """获取设备名称"""
        equipment_mapping = {
            "R001": "燃烧室",
            "R002": "废气出口",
            "R003": "应急阀门",
            "R004": "处理系统",
            "R005": "废气出口",
            "R007": "吸附设施",
            "R008": "脱附设施",
            "R015": "反应器",
        }
        return equipment_mapping.get(rule.rule_id, "未知设备")
    
    def get_violation_summary(self) -> Dict:
        """获取违规汇总"""
        all_records = self.warning_records + list(self.active_warnings.values())
        
        if not all_records:
            return {"total": 0, "by_severity": {}, "by_equipment": {}}
        
        summary = {
            "total": len(all_records),
            "ongoing": len(self.active_warnings),
            "resolved": len(self.warning_records),
            "by_severity": {},
            "by_equipment": {},
            "by_rule": {}
        }
        
        for record in all_records:
            # 按严重程度统计
            severity = record.severity
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            
            # 按设备统计
            equipment = record.affected_equipment
            summary["by_equipment"][equipment] = summary["by_equipment"].get(equipment, 0) + 1
            
            # 按规则统计
            rule_name = record.rule_name
            summary["by_rule"][rule_name] = summary["by_rule"].get(rule_name, 0) + 1
        
        return summary

class InteractiveDashboardServer:
    """交互式实时大屏服务器"""
    
    def __init__(self, port=8090):
        self.port = port
        self.data_generator = RealTimeDataGenerator()
        self.alert_history = []
        self.alert_rotation_index = 0
        
    def start_server(self):
        """启动服务器"""
        class TechHTTPHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                self.data_generator = kwargs.pop('data_generator', None)
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                if self.path == '/':
                    self.send_tech_dashboard()
                elif self.path == '/api/realtime-data':
                    self.send_realtime_data()
                else:
                    super().do_GET()
            
            def send_tech_dashboard(self):
                """发送交互式大屏HTML"""
                html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RTO/RCO交互式监控大屏</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #0a0a0a 100%);
            color: #00d4ff;
            overflow: hidden;
            height: 100vh;
        }
        .tech-grid {
            position: absolute;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(0, 212, 255, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 212, 255, 0.05) 1px, transparent 1px);
            background-size: 40px 40px;
            animation: gridFlow 25s linear infinite;
        }
        @keyframes gridFlow {
            0% { transform: translate(0, 0); }
            100% { transform: translate(40px, 40px); }
        }
        .dashboard {
            position: relative;
            z-index: 2;
            display: grid;
            grid-template-columns: 300px 1fr 300px 300px;
            grid-template-rows: 80px 280px 280px 140px;
            height: 100vh;
            gap: 15px;
            padding: 15px;
        }
        .header {
            grid-column: 1 / -1;
            background: linear-gradient(90deg, rgba(0, 212, 255, 0.2), rgba(0, 150, 255, 0.2));
            border: 2px solid #00d4ff;
            border-radius: 12px;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }
        .header h1 {
            font-size: 2.8rem;
            text-shadow: 0 0 20px #00d4ff;
        }
        .panel {
            background: linear-gradient(135deg, rgba(0, 20, 40, 0.9), rgba(0, 40, 80, 0.7));
            border: 2px solid #00d4ff;
            border-radius: 12px;
            padding: 15px;
            backdrop-filter: blur(10px);
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .panel:hover {
            border-color: #00ffff;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
            transform: scale(1.02);
        }
        .panel.clicked {
            border-color: #ff6b6b;
            box-shadow: 0 0 25px rgba(255, 107, 107, 0.7);
        }
        .panel-title {
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 10px;
            color: #00ffff;
            text-shadow: 0 0 10px #00ffff;
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: bold;
            color: #00ffff;
            text-shadow: 0 0 15px #00ffff;
            transition: all 0.3s ease;
        }
        .metric-value.warning {
            color: #ffaa00;
            text-shadow: 0 0 15px #ffaa00;
        }
        .metric-value.critical {
            color: #ff0040;
            text-shadow: 0 0 15px #ff0040;
            animation: criticalPulse 1s ease-in-out infinite alternate;
        }
        @keyframes criticalPulse {
            from { transform: scale(1); }
            to { transform: scale(1.1); }
        }
        .chart-container {
            height: 200px;
            background: rgba(0, 0, 0, 0.9);
            border: 1px solid #00d4ff;
            border-radius: 8px;
            position: relative;
        }
        .alert-item {
            background: linear-gradient(90deg, rgba(255, 0, 64, 0.3), rgba(255, 100, 0, 0.2));
            border-left: 4px solid #ff0040;
            padding: 8px 12px;
            margin: 6px 0;
            border-radius: 6px;
            animation: alertPulse 1s ease-in-out infinite alternate;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .alert-item:hover {
            background: linear-gradient(90deg, rgba(255, 0, 64, 0.5), rgba(255, 100, 0, 0.4));
            transform: translateX(5px);
        }
        @keyframes alertPulse {
            from { box-shadow: 0 0 5px rgba(255, 0, 64, 0.5); }
            to { box-shadow: 0 0 20px rgba(255, 0, 64, 0.8); }
        }
        .status-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }
        .status-item {
            background: rgba(0, 40, 80, 0.7);
            border: 1px solid #00d4ff;
            border-radius: 6px;
            padding: 8px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .status-item:hover {
            background: rgba(0, 60, 120, 0.8);
            transform: scale(1.05);
        }
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin: 0 auto 5px;
            animation: statusBlink 2s infinite;
        }
        @keyframes statusBlink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.6; }
        }
        .status-normal { background: #00ff00; }
        .status-warning { background: #ffff00; }
        .status-critical { background: #ff0040; }
        .time-display {
            position: absolute;
            top: 20px;
            right: 30px;
            font-size: 1.2rem;
            color: #00ffff;
            text-shadow: 0 0 10px #00ffff;
        }
        .alert-rotation {
            height: 200px;
            overflow: hidden;
            position: relative;
        }
        .alert-slide {
            position: absolute;
            width: 100%;
            transition: transform 0.5s ease-in-out;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(5px);
        }
        .modal-content {
            background: linear-gradient(135deg, rgba(0, 20, 40, 0.95), rgba(0, 40, 80, 0.9));
            margin: 5% auto;
            padding: 20px;
            border: 2px solid #00d4ff;
            border-radius: 12px;
            width: 80%;
            max-width: 800px;
            color: #00d4ff;
            max-height: 85vh;
            overflow: hidden;
        }
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        .close:hover {
            color: #00ffff;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .data-table th, .data-table td {
            border: 1px solid #00d4ff;
            padding: 8px;
            text-align: left;
        }
        .data-table th {
            background: rgba(0, 40, 80, 0.7);
            color: #00ffff;
        }
        .trend-chart {
            width: 100%;
            height: 100%;
        }
    </style>
</head>
<body>
    <div class="tech-grid"></div>
    <div class="dashboard">
        <div class="header">
            <h1>🏭 RTO/RCO交互式监控大屏 🏭</h1>
            <div class="time-display" id="timeDisplay"></div>
        </div>
        <div class="panel" onclick="showDetail('core')">
            <div class="panel-title">🔥 核心参数</div>
            <div><span class="metric-value" id="tempCombustion">780</span>℃ 燃烧室</div>
            <div><span class="metric-value" id="efficiency">95.2</span>% 效率</div>
            <div><span class="metric-value" id="concentrationIn">200</span>mg/m³ 进口</div>
        </div>
        <div class="panel" onclick="showDetail('trend')">
            <div class="panel-title">📊 实时趋势</div>
            <div class="chart-container">
                <div style="display:flex;align-items:center;gap:8px;padding:6px 8px 4px 8px;">
                    <label for="metricSelect">选择指标:</label>
                    <select id="metricSelect" onchange="resetTrend()">
                        <option value="temperature_combustion" data-threshold="760" data-unit="℃">燃烧室温度</option>
                        <option value="concentration_out" data-threshold="50" data-unit="mg/m³">出口浓度</option>
                        <option value="temperature_outlet" data-threshold="60" data-unit="℃">出口温度</option>
                        <option value="temperature_reactor_outlet" data-threshold="600" data-unit="℃">反应器出口温度</option>
                        <option value="temperature_adsorption" data-threshold="40" data-unit="℃">吸附温度</option>
                        <option value="pressure_loss_catalytic" data-threshold="2" data-unit="kPa">压力损失</option>
                        <option value="particle_content" data-threshold="10" data-unit="mg/m³">颗粒物</option>
                        <option value="efficiency" data-threshold="90" data-unit="%">效率</option>
                    </select>
                </div>
                <canvas id="trendChart" class="trend-chart"></canvas>
            </div>
        </div>
        <div class="panel" onclick="showDetail('temperature')">
            <div class="panel-title">🌡️ 温度监控</div>
            <div><span class="metric-value" id="tempOutlet">45</span>℃ 出口</div>
            <div><span class="metric-value" id="tempAdsorption">35</span>℃ 吸附</div>
            <div><span class="metric-value" id="tempDesorption">105</span>℃ 脱附</div>
            <div><span class="metric-value" id="tempReactor">550</span>℃ 反应器</div>
        </div>
        <div class="panel" onclick="showDetail('equipment')">
            <div class="panel-title">🛠️ 设备状态</div>
            <div class="status-grid" id="equipmentStatus"></div>
        </div>
        <div class="panel" onclick="showDetail('pressure')">
            <div class="panel-title">⚡ 压力流量</div>
            <div><span class="metric-value" id="pressure">1.2</span>MPa 系统压力</div>
            <div><span class="metric-value" id="flowRate">1000</span>m³/h 流量</div>
            <div><span class="metric-value" id="pressureLoss">1.2</span>kPa 压力损失</div>
        </div>
        <div class="panel" onclick="showDetail('concentration')">
            <div class="panel-title">🧪 浓度分析</div>
            <div><span class="metric-value" id="concentrationOut">15</span>mg/m³ 出口</div>
            <div><span class="metric-value" id="particleContent">5</span>mg/m³ 颗粒物</div>
            <div><span class="metric-value" id="emergencyValve">0</span> 应急阀门</div>
        </div>
        <div class="panel" onclick="showDetail('alerts')">
            <div class="panel-title">🚨 实时告警</div>
            <div class="alert-rotation" id="alertRotation"></div>
        </div>
    </div>
    
    <!-- 模态框 -->
    <div id="detailModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <div id="modalContent"></div>
        </div>
    </div>
    
    <script>
        let trendData = [];
        let alertHistory = [];
        let currentAlertIndex = 0;
        let chart = null;
        let currentMetric = 'temperature_combustion';
        let currentThreshold = 760;
        let currentUnit = '℃';
        let alertCycles = [];
        
        function updateTime() {
            document.getElementById('timeDisplay').textContent = new Date().toLocaleString('zh-CN');
        }
        
        async function fetchData() {
            try {
                const response = await fetch('/api/realtime-data');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.log('获取数据失败，使用模拟数据');
                updateDashboard(generateMockData());
            }
        }
        
        function generateMockData() {
            return {
                realtime: {
                    temperature_combustion: 780 + Math.random() * 20 - 10,
                    temperature_outlet: 45 + Math.random() * 10 - 5,
                    concentration_in: 200 + Math.random() * 40 - 20,
                    concentration_out: 15 + Math.random() * 10 - 5,
                    temperature_adsorption: 35 + Math.random() * 6 - 3,
                    temperature_desorption: 105 + Math.random() * 10 - 5,
                    temperature_reactor_outlet: 550 + Math.random() * 50 - 25,
                    pressure: 1.2 + Math.random() * 0.3 - 0.15,
                    flow_rate: 1000 + Math.random() * 80 - 40,
                    efficiency: 95 + Math.random() * 3 - 1.5,
                    emergency_valve: 0,
                    pressure_loss_catalytic: 1.2 + Math.random() * 0.3 - 0.15,
                    particle_content: 5 + Math.random() * 2 - 1
                },
                alerts: [],
                equipment_status: {
                    '燃烧室': 'normal',
                    '废气出口': 'normal',
                    '吸附设施': 'normal',
                    '脱附设施': 'normal',
                    '反应器': 'normal',
                    '应急系统': 'normal'
                }
            };
        }
        
        function updateDashboard(data) {
            const realtime = data.realtime || {};
            
            // 更新核心参数
            updateMetric('tempCombustion', realtime.temperature_combustion, 760, '℃');
            updateMetric('efficiency', realtime.efficiency, 90, '%');
            updateMetric('concentrationIn', realtime.concentration_in, null, 'mg/m³');
            
            // 更新温度监控
            updateMetric('tempOutlet', realtime.temperature_outlet, 60, '℃');
            updateMetric('tempAdsorption', realtime.temperature_adsorption, 40, '℃');
            updateMetric('tempDesorption', realtime.temperature_desorption, 90, '℃');
            updateMetric('tempReactor', realtime.temperature_reactor_outlet, 600, '℃');
            
            // 更新压力流量
            updateMetric('pressure', realtime.pressure, null, 'MPa');
            updateMetric('flowRate', realtime.flow_rate, null, 'm³/h');
            updateMetric('pressureLoss', realtime.pressure_loss_catalytic, 2, 'kPa');
            
            // 更新浓度分析
            updateMetric('concentrationOut', realtime.concentration_out, 50, 'mg/m³');
            updateMetric('particleContent', realtime.particle_content, 10, 'mg/m³');
            updateMetric('emergencyValve', realtime.emergency_valve, 0, '');
            
            // 更新设备状态
            updateEquipmentStatus(data.equipment_status || {});
            
            // 更新告警
            updateAlerts(data.alerts || []);
            // 缓存报警周期（用于详情展示）
            if (data.alert_cycles) {
                alertCycles = data.alert_cycles;
            }
            
            // 更新趋势图
            updateTrendChart(realtime);
        }
        
        function updateMetric(elementId, value, threshold, unit) {
            const element = document.getElementById(elementId);
            if (element && value !== undefined) {
                element.textContent = value.toFixed(1);
                element.className = 'metric-value';
                
                if (threshold !== null) {
                    if (elementId.includes('tempCombustion') && value < threshold) {
                        element.className += ' critical';
                    } else if (elementId.includes('concentrationOut') && value > threshold) {
                        element.className += ' critical';
                    } else if (elementId.includes('tempOutlet') && value > threshold) {
                        element.className += ' warning';
                    } else if (elementId.includes('tempAdsorption') && value > threshold) {
                        element.className += ' warning';
                    } else if (elementId.includes('tempReactor') && value > threshold) {
                        element.className += ' critical';
                    } else if (elementId.includes('pressureLoss') && value > threshold) {
                        element.className += ' warning';
                    } else if (elementId.includes('particleContent') && value > threshold) {
                        element.className += ' warning';
                    } else if (elementId.includes('emergencyValve') && value > threshold) {
                        element.className += ' critical';
                    }
                }
            }
        }
        
        function updateEquipmentStatus(equipmentStatus) {
            const statusContainer = document.getElementById('equipmentStatus');
            statusContainer.innerHTML = '';
            Object.entries(equipmentStatus).forEach(([name, status]) => {
                const item = document.createElement('div');
                item.className = 'status-item';
                item.innerHTML = `<div class="status-dot status-${status}"></div>${name}`;
                statusContainer.appendChild(item);
            });
        }
        
        function updateAlerts(alerts) {
            if (alerts.length > 0) {
                alertHistory = [...alertHistory, ...alerts];
                if (alertHistory.length > 500) {
                    alertHistory = alertHistory.slice(-500);
                }
            }
            
            const alertContainer = document.getElementById('alertRotation');
            if (alertHistory.length > 0) {
                alertContainer.innerHTML = '';
                alertHistory.slice(-5).forEach((alert, index) => {
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert-item';
                    alertDiv.innerHTML = `
                        <div><strong>${alert.type}</strong></div>
                        <div>设备: ${alert.equipment}</div>
                        <div>数值: ${alert.value?.toFixed(1)}${alert.unit || ''}</div>
                        <div>阈值: ${alert.threshold}${alert.unit || ''}</div>
                        <div>时间: ${new Date(alert.timestamp).toLocaleTimeString()}</div>
                    `;
                    alertContainer.appendChild(alertDiv);
                });
            } else {
                alertContainer.innerHTML = '<div style="color: #00ff41; text-align: center; padding: 20px;">系统运行正常</div>';
            }
        }
        
        function updateTrendChart(data) {
            const canvas = document.getElementById('trendChart');
            const ctx = canvas.getContext('2d');
            
            // 读取当前选择
            const select = document.getElementById('metricSelect');
            if (select) {
                currentMetric = select.value;
                const opt = select.options[select.selectedIndex];
                currentThreshold = parseFloat(opt.getAttribute('data-threshold'));
                currentUnit = opt.getAttribute('data-unit') || '';
            }

            // 添加新数据点
            const value = data[currentMetric];
            trendData.push({ time: new Date().toLocaleTimeString(), value: value });
            
            // 保持最近20个数据点
            if (trendData.length > 20) {
                trendData.shift();
            }
            
            // 绘制带轴与阈值线的趋势图
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            const values = trendData.map(d => d.value).filter(v => v !== undefined && !isNaN(v));
            if (values.length === 0) return;
            const vMin = Math.min(...values.concat(isFinite(currentThreshold) ? [currentThreshold] : []));
            const vMax = Math.max(...values.concat(isFinite(currentThreshold) ? [currentThreshold] : []));
            const pad = (vMax - vMin) * 0.2 || 1;
            const yMin = vMin - pad;
            const yMax = vMax + pad;

            // 坐标轴
            ctx.strokeStyle = '#2a5670';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(40, 10);
            ctx.lineTo(40, canvas.height - 25);
            ctx.lineTo(canvas.width - 10, canvas.height - 25);
            ctx.stroke();

            // Y轴刻度和网格
            ctx.fillStyle = '#00d4ff';
            ctx.font = '12px Arial';
            const ticks = 4;
            for (let i = 0; i <= ticks; i++) {
                const val = yMin + (i / ticks) * (yMax - yMin);
                const y = mapY(val, yMin, yMax, canvas.height);
                ctx.fillText(val.toFixed(1), 5, y + 4);
                ctx.strokeStyle = 'rgba(0,212,255,0.15)';
                ctx.beginPath();
                ctx.moveTo(40, y);
                ctx.lineTo(canvas.width - 10, y);
                ctx.stroke();
            }

            // 阈值线
            if (!isNaN(currentThreshold) && isFinite(currentThreshold)) {
                const yTh = mapY(currentThreshold, yMin, yMax, canvas.height);
                ctx.strokeStyle = '#ffaa00';
                ctx.setLineDash([6, 6]);
                ctx.beginPath();
                ctx.moveTo(40, yTh);
                ctx.lineTo(canvas.width - 10, yTh);
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.fillStyle = '#ffaa00';
                ctx.fillText(`阈值 ${currentThreshold}${currentUnit}`, canvas.width - 130, yTh - 6);
            }

            // 折线
            ctx.strokeStyle = '#00ffff';
            ctx.lineWidth = 2;
            ctx.beginPath();
            trendData.forEach((p, i) => {
                const x = mapX(i, trendData.length, canvas.width);
                const y = mapY(p.value, yMin, yMax, canvas.height);
                if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            });
            ctx.stroke();

            // 数据点（超限标红；效率低于阈值标红）
            trendData.forEach((p, i) => {
                const x = mapX(i, trendData.length, canvas.width);
                const y = mapY(p.value, yMin, yMax, canvas.height);
                let exceed = false;
                if (!isNaN(currentThreshold) && isFinite(currentThreshold)) {
                    if (currentMetric === 'efficiency') {
                        exceed = p.value < currentThreshold;
                    } else {
                        exceed = p.value > currentThreshold;
                    }
                }
                ctx.fillStyle = exceed ? '#ff0040' : '#00ffff';
                ctx.beginPath();
                ctx.arc(x, y, 3, 0, Math.PI * 2);
                ctx.fill();
            });

            // 轴标题
            ctx.fillStyle = '#00d4ff';
            ctx.fillText('时间', canvas.width - 40, canvas.height - 8);
            ctx.fillText(`${currentMetric} (${currentUnit})`, 50, 20);

            function mapX(i, n, width) {
                const plotW = width - 50;
                return 40 + (i / Math.max(1, n - 1)) * (plotW - 10);
            }
            function mapY(val, minV, maxV, height) {
                const plotH = height - 35;
                const r = (val - minV) / Math.max(1e-9, (maxV - minV));
                return 10 + (1 - r) * (plotH - 10);
            }
        }

        function resetTrend() {
            trendData = [];
        }
        
        function showDetail(type) {
            const modal = document.getElementById('detailModal');
            const content = document.getElementById('modalContent');
            
            let detailContent = '';
            
            switch(type) {
                case 'core':
                    detailContent = `
                        <h2>🔥 核心参数详情</h2>
                        <table class="data-table">
                            <tr><th>参数</th><th>当前值</th><th>正常范围</th><th>状态</th></tr>
                            <tr><td>燃烧室温度</td><td id="detailTempCombustion">780</td><td>>760℃</td><td id="statusTempCombustion">正常</td></tr>
                            <tr><td>处理效率</td><td id="detailEfficiency">95.2</td><td>>90%</td><td id="statusEfficiency">正常</td></tr>
                            <tr><td>进口浓度</td><td id="detailConcentrationIn">200</td><td>100-300mg/m³</td><td id="statusConcentrationIn">正常</td></tr>
                        </table>
                    `;
                    break;
                case 'temperature':
                    detailContent = `
                        <h2>🌡️ 温度监控详情</h2>
                        <table class="data-table">
                            <tr><th>设备</th><th>当前温度</th><th>正常范围</th><th>状态</th></tr>
                            <tr><td>废气出口</td><td id="detailTempOutlet">45</td><td><60℃</td><td id="statusTempOutlet">正常</td></tr>
                            <tr><td>吸附设施</td><td id="detailTempAdsorption">35</td><td><40℃</td><td id="statusTempAdsorption">正常</td></tr>
                            <tr><td>脱附设施</td><td id="detailTempDesorption">105</td><td>90-120℃</td><td id="statusTempDesorption">正常</td></tr>
                            <tr><td>反应器出口</td><td id="detailTempReactor">550</td><td><600℃</td><td id="statusTempReactor">正常</td></tr>
                        </table>
                    `;
                    break;
                case 'equipment':
                    detailContent = `
                        <h2>🛠️ 设备状态详情</h2>
                        <div id="equipmentDetail"></div>
                    `;
                    break;
                case 'alerts':
                    detailContent = `
                        <h2>🚨 告警历史详情</h2>
                        <div id="alertDetail"></div>
                    `;
                    break;
                default:
                    detailContent = `<h2>📊 ${type} 详情</h2><p>详细信息加载中...</p>`;
            }
            
            content.innerHTML = detailContent;
            modal.style.display = 'block';
            
            // 更新详情数据
            setTimeout(() => updateDetailData(type), 100);
        }
        
        function updateDetailData(type) {
            // 获取当前数据
            const currentData = getCurrentData();
            
            switch(type) {
                case 'core':
                    updateCoreDetail(currentData);
                    break;
                case 'temperature':
                    updateTemperatureDetail(currentData);
                    break;
                case 'equipment':
                    updateEquipmentDetail(currentData);
                    break;
                case 'alerts':
                    updateAlertsDetail(currentData);
                    break;
                case 'pressure':
                    updatePressureDetail(currentData);
                    break;
                case 'concentration':
                    updateConcentrationDetail(currentData);
                    break;
                case 'trend':
                    updateTrendDetail(currentData);
                    break;
            }
        }
        
        function getCurrentData() {
            // 返回当前显示的数据
            return {
                realtime: {
                    temperature_combustion: parseFloat(document.getElementById('tempCombustion').textContent),
                    temperature_outlet: parseFloat(document.getElementById('tempOutlet').textContent),
                    concentration_in: parseFloat(document.getElementById('concentrationIn').textContent),
                    concentration_out: parseFloat(document.getElementById('concentrationOut').textContent),
                    temperature_adsorption: parseFloat(document.getElementById('tempAdsorption').textContent),
                    temperature_desorption: parseFloat(document.getElementById('tempDesorption').textContent),
                    temperature_reactor_outlet: parseFloat(document.getElementById('tempReactor').textContent),
                    pressure: parseFloat(document.getElementById('pressure').textContent),
                    flow_rate: parseFloat(document.getElementById('flowRate').textContent),
                    efficiency: parseFloat(document.getElementById('efficiency').textContent),
                    emergency_valve: parseFloat(document.getElementById('emergencyValve').textContent),
                    pressure_loss_catalytic: parseFloat(document.getElementById('pressureLoss').textContent),
                    particle_content: parseFloat(document.getElementById('particleContent').textContent)
                },
                equipment_status: getEquipmentStatus(),
                alerts: alertHistory,
                alert_cycles: alertCycles
            };
        }
        
        function getEquipmentStatus() {
            const statusContainer = document.getElementById('equipmentStatus');
            const statusItems = statusContainer.querySelectorAll('.status-item');
            const status = {};
            
            statusItems.forEach(item => {
                const name = item.textContent.trim();
                const dot = item.querySelector('.status-dot');
                const statusClass = dot.className;
                
                if (statusClass.includes('normal')) {
                    status[name] = 'normal';
                } else if (statusClass.includes('warning')) {
                    status[name] = 'warning';
                } else if (statusClass.includes('critical')) {
                    status[name] = 'critical';
                }
            });
            
            return status;
        }
        
        function updateCoreDetail(data) {
            const realtime = data.realtime;
            
            document.getElementById('detailTempCombustion').textContent = realtime.temperature_combustion.toFixed(1);
            document.getElementById('detailEfficiency').textContent = realtime.efficiency.toFixed(1);
            document.getElementById('detailConcentrationIn').textContent = realtime.concentration_in.toFixed(1);
            
            // 更新状态
            document.getElementById('statusTempCombustion').textContent = 
                realtime.temperature_combustion >= 760 ? '正常' : '异常';
            document.getElementById('statusEfficiency').textContent = 
                realtime.efficiency >= 90 ? '正常' : '异常';
            document.getElementById('statusConcentrationIn').textContent = 
                realtime.concentration_in >= 100 && realtime.concentration_in <= 300 ? '正常' : '异常';
        }
        
        function updateTemperatureDetail(data) {
            const realtime = data.realtime;
            
            document.getElementById('detailTempOutlet').textContent = realtime.temperature_outlet.toFixed(1);
            document.getElementById('detailTempAdsorption').textContent = realtime.temperature_adsorption.toFixed(1);
            document.getElementById('detailTempDesorption').textContent = realtime.temperature_desorption.toFixed(1);
            document.getElementById('detailTempReactor').textContent = realtime.temperature_reactor_outlet.toFixed(1);
            
            // 更新状态
            document.getElementById('statusTempOutlet').textContent = 
                realtime.temperature_outlet <= 60 ? '正常' : '异常';
            document.getElementById('statusTempAdsorption').textContent = 
                realtime.temperature_adsorption <= 40 ? '正常' : '异常';
            document.getElementById('statusTempDesorption').textContent = 
                realtime.temperature_desorption >= 90 && realtime.temperature_desorption <= 120 ? '正常' : '异常';
            document.getElementById('statusTempReactor').textContent = 
                realtime.temperature_reactor_outlet <= 600 ? '正常' : '异常';
        }
        
        function updateEquipmentDetail(data) {
            const equipmentDetail = document.getElementById('equipmentDetail');
            const equipmentStatus = data.equipment_status;
            
            let html = '<table class="data-table">';
            html += '<tr><th>设备名称</th><th>当前状态</th><th>状态描述</th><th>最后检查</th></tr>';
            
            Object.entries(equipmentStatus).forEach(([name, status]) => {
                const statusText = status === 'normal' ? '正常' : 
                                 status === 'warning' ? '警告' : '危险';
                const statusColor = status === 'normal' ? '#00ff00' : 
                                  status === 'warning' ? '#ffff00' : '#ff0040';
                const description = status === 'normal' ? '设备运行正常' : 
                                  status === 'warning' ? '设备需要关注' : '设备存在故障';
                
                html += `<tr>
                    <td>${name}</td>
                    <td style="color: ${statusColor};">${statusText}</td>
                    <td>${description}</td>
                    <td>${new Date().toLocaleTimeString()}</td>
                </tr>`;
            });
            
            html += '</table>';
            equipmentDetail.innerHTML = html;
        }
        
        function updateAlertsDetail(data) {
            const alertDetail = document.getElementById('alertDetail');
            const alerts = data.alerts;
            const cycles = (data.alert_cycles || []).slice(-10);
            
            let html = '';
            // 周期表
            if (cycles.length > 0) {
                html += '<h3>报警周期</h3>';
                html += '<table class="data-table">';
                html += '<tr><th>报警类型</th><th>设备</th><th>严重程度</th><th>开始时间</th><th>结束时间</th><th>持续时长</th><th>次数</th><th>最大值</th><th>最小值</th><th>阈值</th></tr>';
                cycles.forEach(c => {
                    const sevColor = c.severity === 'critical' ? '#ff0040' : c.severity === 'high' ? '#ff4500' : c.severity === 'medium' ? '#ffaa00' : '#00ff00';
                    const dur = (c.duration_sec || 0);
                    const durText = dur >= 3600 ? (dur/3600).toFixed(2) + ' 小时' : (dur/60).toFixed(1) + ' 分钟';
                    html += `<tr>
                        <td>${c.type}</td>
                        <td>${c.equipment}</td>
                        <td style="color:${sevColor};">${c.severity}</td>
                        <td>${new Date(c.start_time).toLocaleString()}</td>
                        <td>${new Date(c.end_time).toLocaleString()}</td>
                        <td>${durText}</td>
                        <td>${c.count}</td>
                        <td>${(c.max_value ?? '').toFixed ? c.max_value.toFixed(1) : c.max_value}${c.unit || ''}</td>
                        <td>${(c.min_value ?? '').toFixed ? c.min_value.toFixed(1) : c.min_value}${c.unit || ''}</td>
                        <td>${c.threshold}${c.unit || ''}</td>
                    </tr>`;
                });
                html += '</table>';
            }

            // 最近报警明细
            if (alerts.length > 0) {
                html += '<h3 style="margin-top:16px;">最近报警明细</h3>';
                html += '<table class="data-table">';
                html += '<tr><th>报警类型</th><th>设备</th><th>数值</th><th>阈值</th><th>严重程度</th><th>时间</th></tr>';
                alerts.slice(-10).forEach(alert => {
                    const severityColor = alert.severity === 'critical' ? '#ff0040' : alert.severity === 'high' ? '#ff4500' : alert.severity === 'medium' ? '#ffaa00' : '#00ff00';
                    const severityText = alert.severity === 'critical' ? '严重' : alert.severity === 'high' ? '高' : alert.severity === 'medium' ? '中' : '低';
                    html += `<tr>
                        <td>${alert.type}</td>
                        <td>${alert.equipment}</td>
                        <td>${alert.value?.toFixed(1)}${alert.unit || ''}</td>
                        <td>${alert.threshold}${alert.unit || ''}</td>
                        <td style="color: ${severityColor};">${severityText}</td>
                        <td>${new Date(alert.timestamp).toLocaleString()}</td>
                    </tr>`;
                });
                html += '</table>';
            }

            if (!html) {
                alertDetail.innerHTML = '<div style="color: #00ff41; text-align: center; padding: 20px;">暂无报警记录</div>';
            } else {
                alertDetail.innerHTML = `<div style="max-height:70vh; overflow-y:auto; padding-right:6px;">${html}</div>`;
            }
        }
        
        function updatePressureDetail(data) {
            const realtime = data.realtime;
            
            let html = '<table class="data-table">';
            html += '<tr><th>参数</th><th>当前值</th><th>正常范围</th><th>状态</th><th>单位</th></tr>';
            
            const pressureData = [
                {name: '系统压力', value: realtime.pressure, range: '1.0-2.0', unit: 'MPa'},
                {name: '流量', value: realtime.flow_rate, range: '800-1200', unit: 'm³/h'},
                {name: '压力损失', value: realtime.pressure_loss_catalytic, range: '<2.0', unit: 'kPa'}
            ];
            
            pressureData.forEach(item => {
                const isNormal = item.name === '压力损失' ? 
                    item.value < 2.0 : 
                    item.name === '系统压力' ? 
                    item.value >= 1.0 && item.value <= 2.0 :
                    item.value >= 800 && item.value <= 1200;
                
                const status = isNormal ? '正常' : '异常';
                const statusColor = isNormal ? '#00ff00' : '#ff0040';
                
                html += `<tr>
                    <td>${item.name}</td>
                    <td>${item.value.toFixed(1)}</td>
                    <td>${item.range}</td>
                    <td style="color: ${statusColor};">${status}</td>
                    <td>${item.unit}</td>
                </tr>`;
            });
            
            html += '</table>';
            document.getElementById('modalContent').innerHTML = `
                <h2>⚡ 压力流量详情</h2>
                ${html}
            `;
        }
        
        function updateConcentrationDetail(data) {
            const realtime = data.realtime;
            
            let html = '<table class="data-table">';
            html += '<tr><th>参数</th><th>当前值</th><th>正常范围</th><th>状态</th><th>单位</th></tr>';
            
            const concentrationData = [
                {name: '出口浓度', value: realtime.concentration_out, range: '<50', unit: 'mg/m³'},
                {name: '颗粒物含量', value: realtime.particle_content, range: '<10', unit: 'mg/m³'},
                {name: '应急阀门', value: realtime.emergency_valve, range: '0', unit: ''}
            ];
            
            concentrationData.forEach(item => {
                const isNormal = item.name === '出口浓度' ? item.value < 50 :
                               item.name === '颗粒物含量' ? item.value < 10 :
                               item.value === 0;
                
                const status = isNormal ? '正常' : '异常';
                const statusColor = isNormal ? '#00ff00' : '#ff0040';
                
                html += `<tr>
                    <td>${item.name}</td>
                    <td>${item.value.toFixed(1)}</td>
                    <td>${item.range}</td>
                    <td style="color: ${statusColor};">${status}</td>
                    <td>${item.unit}</td>
                </tr>`;
            });
            
            html += '</table>';
            document.getElementById('modalContent').innerHTML = `
                <h2>🧪 浓度分析详情</h2>
                ${html}
            `;
        }
        
        function updateTrendDetail(data) {
            const realtime = data.realtime;
            
            let html = '<div style="margin: 20px 0;">';
            html += '<h3>📈 实时数据趋势</h3>';
            html += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">';
            
            // 温度趋势
            html += '<div>';
            html += '<h4>🌡️ 温度趋势</h4>';
            html += '<div style="background: rgba(0,0,0,0.5); padding: 10px; border-radius: 5px;">';
            html += `<div>燃烧室: ${realtime.temperature_combustion.toFixed(1)}℃</div>`;
            html += `<div>出口: ${realtime.temperature_outlet.toFixed(1)}℃</div>`;
            html += `<div>吸附: ${realtime.temperature_adsorption.toFixed(1)}℃</div>`;
            html += `<div>脱附: ${realtime.temperature_desorption.toFixed(1)}℃</div>`;
            html += `<div>反应器: ${realtime.temperature_reactor_outlet.toFixed(1)}℃</div>`;
            html += '</div></div>';
            
            // 浓度趋势
            html += '<div>';
            html += '<h4>🧪 浓度趋势</h4>';
            html += '<div style="background: rgba(0,0,0,0.5); padding: 10px; border-radius: 5px;">';
            html += `<div>进口: ${realtime.concentration_in.toFixed(1)}mg/m³</div>`;
            html += `<div>出口: ${realtime.concentration_out.toFixed(1)}mg/m³</div>`;
            html += `<div>颗粒物: ${realtime.particle_content.toFixed(1)}mg/m³</div>`;
            html += `<div>效率: ${realtime.efficiency.toFixed(1)}%</div>`;
            html += '</div></div>';
            
            html += '</div>';
            html += '<div style="text-align: center; color: #00ffff; margin-top: 20px;">';
            html += '趋势图显示最近20个数据点的变化情况';
            html += '</div></div>';
            
            document.getElementById('modalContent').innerHTML = `
                <h2>📊 实时趋势详情</h2>
                ${html}
            `;
        }
        
        function closeModal() {
            document.getElementById('detailModal').style.display = 'none';
        }
        
        // 点击模态框外部关闭
        window.onclick = function(event) {
            const modal = document.getElementById('detailModal');
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        }
        
        // 初始化
        updateTime();
        setInterval(updateTime, 1000);
        fetchData();
        setInterval(fetchData, 2000);
        
        // 初始化趋势图
        const canvas = document.getElementById('trendChart');
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
    </script>
</body>
</html>'''
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html_content.encode('utf-8'))
            
            def send_realtime_data(self):
                """发送实时数据API"""
                if hasattr(self, 'data_generator') and self.data_generator:
                    data = self.data_generator.generate_realtime_data()
                    # 聚合连续报警为周期
                    try:
                        cycles = []
                        # 使用最近历史进行聚合
                        history = sorted(self.data_generator.alert_history, key=lambda a: (a.get('type'), a.get('equipment'), a.get('timestamp')))
                        current = None
                        gap_threshold = timedelta(seconds=10)  # 允许的间隔，连续报警界定
                        for a in history:
                            a_time = a.get('timestamp')
                            key = (a.get('type'), a.get('equipment'))
                            if current is None:
                                current = {
                                    'type': a.get('type'),
                                    'equipment': a.get('equipment'),
                                    'severity': a.get('severity'),
                                    'threshold': a.get('threshold'),
                                    'unit': a.get('unit'),
                                    'start_time': a_time,
                                    'end_time': a_time,
                                    'max_value': a.get('value'),
                                    'min_value': a.get('value'),
                                    'count': 1
                                }
                            else:
                                # 是否同一类型同一设备且间隔在阈值内
                                if current['type'] == a.get('type') and current['equipment'] == a.get('equipment') and (a_time - current['end_time']) <= gap_threshold:
                                    current['end_time'] = a_time
                                    val = a.get('value')
                                    if val is not None:
                                        current['max_value'] = max(current['max_value'], val)
                                        current['min_value'] = min(current['min_value'], val)
                                    current['count'] += 1
                                else:
                                    # 结束上一个周期
                                    current['duration_sec'] = (current['end_time'] - current['start_time']).total_seconds()
                                    cycles.append(current)
                                    # 开启新的周期
                                    current = {
                                        'type': a.get('type'),
                                        'equipment': a.get('equipment'),
                                        'severity': a.get('severity'),
                                        'threshold': a.get('threshold'),
                                        'unit': a.get('unit'),
                                        'start_time': a_time,
                                        'end_time': a_time,
                                        'max_value': a.get('value'),
                                        'min_value': a.get('value'),
                                        'count': 1
                                    }
                        if current is not None:
                            current['duration_sec'] = (current['end_time'] - current['start_time']).total_seconds()
                            cycles.append(current)
                        data['alert_cycles'] = cycles[-10:]
                    except Exception as e:
                        data['alert_cycles'] = []
                    
                    # 添加更多统计信息
                    data['statistics'] = {
                        'total_alerts_today': len(self.data_generator.alert_history),
                        'system_uptime': '24小时',
                        'data_quality': '99.8%',
                        'last_maintenance': '2024-01-15',
                        'next_maintenance': '2024-02-15'
                    }
                    
                    # 添加历史趋势数据
                    if len(self.data_generator.data_history) > 0:
                        data['trend_data'] = self.data_generator.data_history[-20:]  # 最近20个数据点
                    
                else:
                    data = {
                        'realtime': {}, 
                        'alerts': [],
                        'equipment_status': {},
                        'statistics': {},
                        'trend_data': []
                    }
                
                json_data = json.dumps(data, ensure_ascii=False, default=str)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json_data.encode('utf-8'))
        
        def handler(*args, **kwargs):
            return TechHTTPHandler(*args, data_generator=self.data_generator, **kwargs)
        
        with HTTPServer(('localhost', self.port), handler) as server:
            print(f"🚀 RTO/RCO交互式监控大屏启动成功!")
            print(f"📱 访问地址: http://localhost:{self.port}")
            print(f"⚡ 交互式大屏 + 实时数据更新")
            print(f"🎯 报警频率: 5秒内1条报警")
            print(f"🖱️ 所有模块可点击交互")
            print(f"📊 数据更新频率: 每2秒一次")
            print(f"🛑 按 Ctrl+C 停止服务")
            
            webbrowser.open(f'http://localhost:{self.port}')
            
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\n👋 服务器已停止")

class WarningSystem:
    """预警系统主类"""

    def __init__(self):
        self.cleaner = DataCleaner()
        self.rule_engine = WarningRuleEngine()
        self.visualizer = InteractiveDashboardServer()

    def process_data_file(self, file_path: str) -> Tuple[List[Dict], Dict]:
        """处理数据文件"""
        print(f"🔄 开始处理数据文件: {file_path}")

        # 1. 加载数据
        df = self.cleaner.load_data(file_path)
        if df.empty:
            return [], {}

        # 2. 数据清洗
        df_clean = self.cleaner.clean_data(df)
        if df_clean.empty:
            print("❌ 数据清洗后无有效数据")
            return [], {}

        # 2.1 生成清洗前后对比可视化
        try:
            output_dir = Path("D:/GitHub/lianwei123/RTO/RCO/可视化结果")
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # 选择关键指标进行对比展示
            compare_columns = [
                'temperature_combustion', 'temperature_outlet',
                'concentration_in', 'concentration_out'
            ]

            available_cols = [c for c in compare_columns if c in df.columns and c in df_clean.columns]
            if len(available_cols) > 0:
                num_plots = len(available_cols)
                rows = (num_plots + 1) // 2
                fig, axes = plt.subplots(rows, 2, figsize=(14, 4 * rows), constrained_layout=True)
                if rows == 1:
                    axes = np.array([axes])
                for idx, col in enumerate(available_cols):
                    ax = axes[idx // 2, idx % 2]
                    try:
                        # 时间序列覆盖绘制
                        if 'timestamp' in df.columns:
                            x_raw = pd.to_datetime(df['timestamp'], errors='coerce')
                        else:
                            x_raw = np.arange(len(df))
                        if 'timestamp' in df_clean.columns:
                            x_clean = pd.to_datetime(df_clean['timestamp'], errors='coerce')
                        else:
                            x_clean = np.arange(len(df_clean))

                        ax.plot(x_raw, df[col], label='清洗前', color='#8892b0', alpha=0.5)
                        ax.plot(x_clean, df_clean[col], label='清洗后', color='#00d4ff', linewidth=1.8)
                        ax.set_title(f"{col} 清洗前后对比")
                        ax.set_xlabel('时间/索引')
                        ax.set_ylabel(col)
                        ax.legend()
                        ax.grid(True, alpha=0.3)
                    except Exception:
                        # 回退到分布直方图对比
                        ax.hist(df[col].dropna(), bins=30, alpha=0.5, label='清洗前', color='#8892b0')
                        ax.hist(df_clean[col].dropna(), bins=30, alpha=0.6, label='清洗后', color='#00d4ff')
                        ax.set_title(f"{col} 分布对比")
                        ax.set_xlabel(col)
                        ax.set_ylabel('频数')
                        ax.legend()

                # 隐藏多余子图
                total_axes = rows * 2
                for j in range(len(available_cols), total_axes):
                    fig.delaxes(axes[j // 2, j % 2])

                compare_path = output_dir / f"cleaning_compare_{timestamp}.png"
                fig.suptitle('数据清洗前后对比', fontsize=16)
                fig.savefig(compare_path, dpi=150)
                plt.close(fig)
                print(f"🖼️ 清洗对比图已生成: {compare_path}")
        except Exception as e:
            print(f"⚠️ 清洗对比图生成失败: {e}")

        # 3. 预警检测
        print("🚨 开始预警规则检测...")
        violations = self.rule_engine.check_rules(df_clean)

        # 4. 生成汇总
        summary = self.rule_engine.get_violation_summary()

        print(f"✅ 预警检测完成: 发现 {len(violations)} 个违规事件")

        return violations, summary

    def run_analysis(self, file_path: str, generate_report: bool = True):
        """运行完整分析"""
        violations, summary = self.process_data_file(file_path)

        if not violations:
            print("✅ 未发现违规事件")
            return

        # 显示汇总信息
        print("\n📋 违规汇总:")
        print(f"  总违规次数: {summary.get('total', 0)}")
        print(f"  进行中违规: {summary.get('ongoing', 0)}")
        print(f"  已解决违规: {summary.get('resolved', 0)}")

        if summary.get('by_severity'):
            print("  按严重程度:")
            for severity, count in summary['by_severity'].items():
                print(f"    {severity.upper()}级: {count} 次")

        # 生成可视化
        if generate_report:
            print("\n📊 生成可视化报告...")
            # 传统报告生成（简化版）
            output_dir = Path("D:/GitHub/lianwei123/RTO/RCO/可视化结果")
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 生成Excel报告
            with pd.ExcelWriter(f"{output_dir}/violation_report_{timestamp}.xlsx") as writer:
                if violations:
                    df_violations = pd.DataFrame(violations)
                    df_violations.to_excel(writer, sheet_name='违规事件明细', index=False)
                
                summary_df = pd.DataFrame([
                    {'统计项目': '总违规次数', '数值': summary.get('total', 0)},
                    {'统计项目': '进行中违规', '数值': summary.get('ongoing', 0)},
                    {'统计项目': '已解决违规', '数值': summary.get('resolved', 0)},
                ])
                summary_df.to_excel(writer, sheet_name='统计汇总', index=False)
                
            print(f"📊 违规报告已生成: {output_dir}/violation_report_{timestamp}.xlsx")
    
    def start_realtime_monitoring(self):
        """启动实时监控大屏"""
        print("🚀 启动RTO/RCO交互式监控大屏...")
        print("🎯 特性: 交互式大屏 + 实时数据 + 点击交互")
        print("⚡ 报警频率: 5秒内1条")
        print("📊 数据更新: 每2秒一次")
        print("🖱️ 所有模块可点击查看详情")
        print("📈 实时趋势图表显示")
        
        self.visualizer.start_server()

def main():
    """主函数"""
    print("🏭 废气处理设备预警系统")
    print("=" * 50)
    
    # 创建预警系统
    warning_system = WarningSystem()
    
    print("🎆 选择操作模式:")
    print("1. 📊 传统数据分析")
    print("2. 🚀 启动实时监控大屏")
    print("3. 📈 创建示例数据并分析")
    
    choice = input("\n请选择 (1-3): ").strip()
    
    if choice == "1":
        # 传统数据分析模式
        test_files = [
            "data/equipment_data.xlsx",
            "data/equipment_data.csv", 
            "PLCTags.csv"
        ]
        
        for file_path in test_files:
            if Path(file_path).exists():
                print(f"\n🔍 分析文件: {file_path}")
                warning_system.run_analysis(file_path)
                break
        else:
            print("⚠️ 未找到数据文件")
            
    elif choice == "2":
        # 实时监控大屏模式
        warning_system.start_realtime_monitoring()
        
    elif choice == "3":
        # 创建示例数据并分析
        print("\n🧪 创建示例数据进行演示...")
        create_sample_data()
        warning_system.run_analysis("sample_data.xlsx")
        
    else:
        print("❌ 无效选择")

def create_sample_data():
    """创建示例数据"""
    np.random.seed(42)

    # 生成24小时的示例数据
    timestamps = pd.date_range(start='2024-01-01 00:00:00', periods=1440, freq='1min')

    data = {
        'timestamp': timestamps,
        'temperature_combustion': np.random.normal(780, 50, 1440),  # 燃烧室温度
        'temperature_outlet': np.random.normal(45, 15, 1440),      # 出口温度
        'concentration_in': np.random.normal(200, 50, 1440),       # 进口浓度
        'concentration_out': np.random.normal(20, 10, 1440),       # 出口浓度
        'temperature_adsorption': np.random.normal(35, 8, 1440),   # 吸附温度
        'temperature_desorption': np.random.normal(105, 15, 1440), # 脱附温度
        'temperature_reactor_outlet': np.random.normal(550, 80, 1440), # 反应器出口温度
        'emergency_valve': np.random.choice([0, 1], 1440, p=[0.95, 0.05]), # 应急阀门
    }

    # 添加一些异常值来触发预警
    data['temperature_combustion'][100:120] = 700  # 燃烧室温度过低
    data['temperature_outlet'][200:250] = 80       # 出口温度过高
    data['concentration_out'][300:350] = 80        # 出口浓度过高
    data['temperature_reactor_outlet'][400:420] = 650  # 反应器温度过高

    df = pd.DataFrame(data)
    df.to_excel("sample_data.xlsx", index=False)
    print("✅ 示例数据已创建: sample_data.xlsx")

if __name__ == "__main__":
    main()

