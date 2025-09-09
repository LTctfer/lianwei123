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

from file_player import FileDataPlayer

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
        self.rules_file = "warning_rules.json"  # 规则配置文件
        self._load_rules_from_file()  # 从文件加载规则
    
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
    
    def _load_rules_from_file(self):
        """从文件加载规则配置"""
        try:
            if Path(self.rules_file).exists():
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                    self.rules = []
                    for rule_data in rules_data:
                        rule = WarningRule(
                            rule_id=rule_data['rule_id'],
                            rule_name=rule_data['rule_name'],
                            description=rule_data['description'],
                            condition=rule_data['condition'],
                            threshold_value=rule_data['threshold_value'],
                            threshold_unit=rule_data['threshold_unit'],
                            severity=rule_data['severity'],
                            is_active=rule_data.get('is_active', True)
                        )
                        self.rules.append(rule)
                print(f"✅ 从文件加载了 {len(self.rules)} 条预警规则")
            else:
                # 如果文件不存在，保存默认规则到文件
                self._save_rules_to_file()
        except Exception as e:
            print(f"⚠️ 加载规则文件失败: {e}")
    
    def _save_rules_to_file(self):
        """保存规则配置到文件"""
        try:
            rules_data = []
            for rule in self.rules:
                rules_data.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'description': rule.description,
                    'condition': rule.condition,
                    'threshold_value': rule.threshold_value,
                    'threshold_unit': rule.threshold_unit,
                    'severity': rule.severity,
                    'is_active': rule.is_active
                })
            
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 已保存 {len(self.rules)} 条预警规则到文件")
        except Exception as e:
            print(f"❌ 保存规则文件失败: {e}")
    
    def update_rule_threshold(self, rule_id: str, new_threshold: float) -> bool:
        """更新规则阈值"""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                old_threshold = rule.threshold_value
                rule.threshold_value = new_threshold
                # 更新条件表达式中的阈值
                if "temperature_combustion" in rule.condition:
                    rule.condition = f"temperature_combustion < {new_threshold}"
                elif "concentration_out" in rule.condition:
                    rule.condition = f"concentration_out > {new_threshold}"
                elif "temperature_outlet" in rule.condition:
                    rule.condition = f"temperature_outlet > {new_threshold}"
                elif "temperature_adsorption" in rule.condition:
                    rule.condition = f"temperature_adsorption > {new_threshold}"
                elif "temperature_desorption" in rule.condition:
                    rule.condition = f"temperature_desorption < {new_threshold} or temperature_desorption > {new_threshold + 30}"
                elif "temperature_reactor_outlet" in rule.condition:
                    rule.condition = f"temperature_reactor_outlet > {new_threshold}"
                elif "pressure_loss_catalytic" in rule.condition:
                    rule.condition = f"pressure_loss_catalytic > {new_threshold}"
                elif "particle_content" in rule.condition:
                    rule.condition = f"particle_content > {new_threshold}"
                
                self._save_rules_to_file()
                print(f"✅ 规则 {rule_id} 阈值已更新: {old_threshold} → {new_threshold}")
                return True
        
        print(f"❌ 未找到规则ID: {rule_id}")
        return False
    
    def toggle_rule_status(self, rule_id: str) -> bool:
        """切换规则启用/禁用状态"""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                rule.is_active = not rule.is_active
                self._save_rules_to_file()
                status = "启用" if rule.is_active else "禁用"
                print(f"✅ 规则 {rule_id} 已{status}")
                return True
        
        print(f"❌ 未找到规则ID: {rule_id}")
        return False
    
    def get_all_rules(self) -> List[Dict]:
        """获取所有规则信息"""
        return [asdict(rule) for rule in self.rules]
    
    def get_rule_by_id(self, rule_id: str) -> Optional[Dict]:
        """根据ID获取规则信息"""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return asdict(rule)
        return None
    
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

    def evaluate_row_for_alerts(self, row_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """对单条记录进行评估，返回用于前端展示的告警列表"""
        alerts: List[Dict[str, Any]] = []
        row = pd.Series(row_dict)
        timestamp = row_dict.get('timestamp', datetime.now())
        for rule in self.rules:
            if not rule.is_active:
                continue
            try:
                if self._evaluate_rule(rule, row):
                    value = self._get_rule_value(rule, row)
                    alerts.append({
                        'type': rule.rule_name,
                        'value': value,
                        'severity': rule.severity,
                        'equipment': self._get_equipment_name(rule),
                        'threshold': rule.threshold_value,
                        'unit': rule.threshold_unit,
                        'timestamp': timestamp,
                        'id': f"alert_{rule.rule_id}_{int(datetime.now().timestamp())}"
                    })
            except Exception:
                continue
        return alerts

class InteractiveDashboardServer:
    """交互式实时大屏服务器"""
    
    def __init__(self, port=8090):
        self.port = port
        self.data_generator = RealTimeDataGenerator()
        self.alert_history = []
        self.alert_rotation_index = 0
        self.rule_engine = WarningRuleEngine()  # 添加规则引擎实例
        self.mode = 'realtime'  # 'realtime' | 'file'
        self.file_player = FileDataPlayer()
        
    def start_server(self):
        """启动服务器"""
        class TechHTTPHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                self.data_generator = kwargs.pop('data_generator', None)
                self.rule_engine = kwargs.pop('rule_engine', None)
                self.mode = kwargs.pop('mode_ref', None)
                self.file_player = kwargs.pop('file_player', None)
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                if self.path == '/':
                    self.send_tech_dashboard()
                elif self.path == '/api/realtime-data':
                    self.send_realtime_data()
                elif self.path == '/api/rules':
                    self.send_rules_list()
                elif self.path == '/api/rules/thresholds':
                    self.send_rules_thresholds()
                elif self.path == '/api/data-source':
                    self.send_data_source()
                elif self.path.startswith('/api/rules/'):
                    rule_id = self.path.split('/')[-1]
                    self.send_rule_detail(rule_id)
                else:
                    super().do_GET()
            
            def do_POST(self):
                if self.path == '/api/rules/update-threshold':
                    self.update_rule_threshold()
                elif self.path == '/api/rules/toggle-status':
                    self.toggle_rule_status()
                elif self.path == '/api/load-data-file':
                    self.load_data_file()
                elif self.path == '/api/stop-file':
                    self.stop_file_mode()
                else:
                    self.send_error(404, "Not Found")
            
            def do_PUT(self):
                if self.path.startswith('/api/rules/'):
                    rule_id = self.path.split('/')[-1]
                    self.update_rule(rule_id)
                else:
                    self.send_error(404, "Not Found")
            
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
        .rules-container {
            max-height: 70vh;
            overflow-y: auto;
            padding-right: 6px;
        }
        .rule-item {
            background: linear-gradient(90deg, rgba(0, 40, 80, 0.7), rgba(0, 60, 120, 0.5));
            border: 1px solid #00d4ff;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            transition: all 0.3s ease;
        }
        .rule-item:hover {
            border-color: #00ffff;
            box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
        }
        .rule-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .rule-title {
            font-size: 1.1rem;
            font-weight: bold;
            color: #00ffff;
        }
        .rule-status {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        .status-active {
            background: #00ff00;
            color: #000;
        }
        .status-inactive {
            background: #ff0040;
            color: #fff;
        }
        .rule-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin: 10px 0;
        }
        .rule-detail-item {
            background: rgba(0, 0, 0, 0.3);
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #00d4ff;
        }
        .rule-detail-label {
            font-size: 0.8rem;
            color: #00d4ff;
            margin-bottom: 4px;
        }
        .rule-detail-value {
            font-size: 1rem;
            color: #00ffff;
            font-weight: bold;
        }
        .rule-actions {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        .rule-btn {
            padding: 6px 12px;
            border: 1px solid #00d4ff;
            background: rgba(0, 40, 80, 0.7);
            color: #00d4ff;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }
        .rule-btn:hover {
            background: rgba(0, 60, 120, 0.8);
            border-color: #00ffff;
            color: #00ffff;
        }
        .rule-btn.danger {
            border-color: #ff0040;
            color: #ff0040;
        }
        .rule-btn.danger:hover {
            background: rgba(255, 0, 64, 0.2);
            border-color: #ff6b6b;
            color: #ff6b6b;
        }
        .threshold-input {
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid #00d4ff;
            color: #00ffff;
            padding: 4px 8px;
            border-radius: 4px;
            width: 80px;
        }
        .threshold-input:focus {
            outline: none;
            border-color: #00ffff;
            box-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
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
        <div class="panel">
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
        <div class="panel" onclick="showDetail('rules')">
            <div class="panel-title">⚙️ 规则管理</div>
            <div style="text-align: center; padding: 20px;">
                <div style="color: #00ffff; font-size: 1.2rem; margin-bottom: 10px;">预警规则配置</div>
                <div style="color: #00ff41; font-size: 0.9rem;">点击查看和修改规则</div>
            </div>
        </div>
        <div class="panel" onclick="showDetail('datasource')">
            <div class="panel-title">📂 数据源</div>
            <div id="dataSourceStatus" style="color:#00ff41;line-height:1.6;">
                模式: 实时模拟<br/>文件: -
            </div>
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
        let thresholdsCache = {}; // 缓存阈值信息
        let dataSourceInfo = { mode: 'realtime', file: null };
        
        function updateTime() {
            document.getElementById('timeDisplay').textContent = new Date().toLocaleString('zh-CN');
        }
        
        async function fetchThresholds() {
            try {
                const response = await fetch('/api/rules/thresholds');
                const result = await response.json();
                if (result.success) {
                    thresholdsCache = result.data;
                    console.log('阈值信息已更新:', thresholdsCache);
                }
            } catch (error) {
                console.log('获取阈值信息失败:', error);
            }
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

        async function fetchDataSource() {
            try {
                const res = await fetch('/api/data-source');
                const result = await res.json();
                if (result.success) {
                    dataSourceInfo = result.data;
                    const el = document.getElementById('dataSourceStatus');
                    if (el) {
                        el.innerHTML = `模式: ${dataSourceInfo.mode === 'file' ? '文件播放' : '实时模拟'}<br/>文件: ${dataSourceInfo.file || '-'}`;
                    }
                }
            } catch (e) { }
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
                
                // 获取动态阈值
                let dynamicThreshold = threshold;
                if (threshold !== null) {
                    // 根据元素ID映射到对应的数据字段
                    let field = null;
                    if (elementId.includes('tempCombustion')) field = 'temperature_combustion';
                    else if (elementId.includes('concentrationOut')) field = 'concentration_out';
                    else if (elementId.includes('tempOutlet')) field = 'temperature_outlet';
                    else if (elementId.includes('tempAdsorption')) field = 'temperature_adsorption';
                    else if (elementId.includes('tempReactor')) field = 'temperature_reactor_outlet';
                    else if (elementId.includes('pressureLoss')) field = 'pressure_loss_catalytic';
                    else if (elementId.includes('particleContent')) field = 'particle_content';
                    else if (elementId.includes('efficiency')) field = 'efficiency';
                    
                    // 使用动态阈值
                    if (field && thresholdsCache[field]) {
                        dynamicThreshold = thresholdsCache[field].threshold;
                    }
                }
                
                if (dynamicThreshold !== null) {
                    if (elementId.includes('tempCombustion') && value < dynamicThreshold) {
                        element.className += ' critical';
                    } else if (elementId.includes('concentrationOut') && value > dynamicThreshold) {
                        element.className += ' critical';
                    } else if (elementId.includes('tempOutlet') && value > dynamicThreshold) {
                        element.className += ' warning';
                    } else if (elementId.includes('tempAdsorption') && value > dynamicThreshold) {
                        element.className += ' warning';
                    } else if (elementId.includes('tempReactor') && value > dynamicThreshold) {
                        element.className += ' critical';
                    } else if (elementId.includes('pressureLoss') && value > dynamicThreshold) {
                        element.className += ' warning';
                    } else if (elementId.includes('particleContent') && value > dynamicThreshold) {
                        element.className += ' warning';
                    } else if (elementId.includes('emergencyValve') && value > dynamicThreshold) {
                        element.className += ' critical';
                    } else if (elementId.includes('efficiency') && value < dynamicThreshold) {
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
                
                // 优先从缓存中获取最新阈值
                if (thresholdsCache[currentMetric]) {
                    currentThreshold = thresholdsCache[currentMetric].threshold;
                    currentUnit = thresholdsCache[currentMetric].unit;
                } else {
                    // 回退到硬编码值
                    const opt = select.options[select.selectedIndex];
                    currentThreshold = parseFloat(opt.getAttribute('data-threshold'));
                    currentUnit = opt.getAttribute('data-unit') || '';
                }
            }

            // 添加新数据点（携带时间戳）
            const value = data[currentMetric];
            // 优先使用数据中的时间戳
            let t = data.timestamp ? new Date(data.timestamp) : new Date();
            const timeLabel = t.toLocaleTimeString();
            trendData.push({ time: timeLabel, value: value });
            
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

            // 数据点（超限标红；效率/燃烧室温度低于阈值标红）
            trendData.forEach((p, i) => {
                const x = mapX(i, trendData.length, canvas.width);
                const y = mapY(p.value, yMin, yMax, canvas.height);
                let exceed = false;
                if (!isNaN(currentThreshold) && isFinite(currentThreshold)) {
                    if (currentMetric === 'efficiency' || currentMetric === 'temperature_combustion') {
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

            // X轴时间刻度标签（随数据滚动）
            const maxLabels = 6; // 控制标签数量避免重叠
            const step = Math.max(1, Math.floor(trendData.length / maxLabels));
            ctx.fillStyle = '#00d4ff';
            ctx.font = '12px Arial';
            for (let i = 0; i < trendData.length; i += step) {
                const x = mapX(i, trendData.length, canvas.width);
                const label = trendData[i].time;
                ctx.fillText(label, Math.max(40, Math.min(x - 18, canvas.width - 60)), canvas.height - 6);
            }

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
                            <tr><td>燃烧室温度</td><td id="detailTempCombustion">780</td><td id="rangeTempCombustion">>760℃</td><td id="statusTempCombustion">正常</td></tr>
                            <tr><td>处理效率</td><td id="detailEfficiency">95.2</td><td id="rangeEfficiency">>90%</td><td id="statusEfficiency">正常</td></tr>
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
                case 'rules':
                    detailContent = `
                        <h2>⚙️ 预警规则管理</h2>
                        <div id="rulesDetail"></div>
                    `;
                    break;
                case 'datasource':
                    detailContent = `
                        <h2>📂 数据源设置</h2>
                        <div style="margin:10px 0;">
                            <div class="data-source-current">
                                <div class="ds-info">
                                    <span class="ds-label">当前模式:</span> 
                                    <span id="dsMode" class="ds-value">${dataSourceInfo.mode === 'file' ? '文件播放' : '实时模拟'}</span>
                                </div>
                                <div class="ds-info" id="dsCurrentFile" style="display:${dataSourceInfo.mode === 'file' ? 'block' : 'none'}">
                                    <span class="ds-label">当前文件:</span>
                                    <span class="ds-value">${dataSourceInfo.file || '-'}</span>
                                </div>
                            </div>
                            
                            <div class="data-source-upload" style="margin-top:16px;">
                                <div class="ds-form">
                                    <div class="ds-form-row">
                                        <input id="filePathInput" placeholder="输入服务器可访问的CSV或XLSX文件路径" 
                                               class="ds-input full-width"/>
                                    </div>
                                    <div class="ds-form-row">
                                        <div class="ds-form-group">
                                            <label>播放速度:</label>
                                            <input id="fileSpeedInput" type="number" step="0.1" value="2" min="0.1" 
                                                   class="ds-input" style="width:80px;"/> 秒/条
                                        </div>
                                        <div class="ds-form-group">
                                            <label class="ds-checkbox">
                                                <input id="fileLoopInput" type="checkbox" checked/>
                                                <span>循环播放</span>
                                            </label>
                                        </div>
                                    </div>
                                    <div class="ds-form-row">
                                        <button class="rule-btn" onclick="loadDataFile()">加载文件</button>
                                        <button class="rule-btn danger" onclick="stopFileMode()">停止文件模式</button>
                                    </div>
                                </div>
                            </div>

                            <div id="dsMsg" class="ds-message"></div>

                            <!-- 文件预览区域 -->
                            <div id="filePreview" class="file-preview" style="display:none;">
                                <h3>📄 文件预览</h3>
                                <div class="file-info">
                                    <div class="info-row">
                                        <span class="info-label">文件名:</span>
                                        <span id="previewFileName" class="info-value"></span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">大小:</span>
                                        <span id="previewFileSize" class="info-value"></span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">总行数:</span>
                                        <span id="previewTotalRows" class="info-value"></span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">数据列:</span>
                                        <span id="previewColumns" class="info-value"></span>
                                    </div>
                                </div>
                                <div class="preview-data">
                                    <table id="previewTable" class="data-table">
                                        <thead>
                                            <tr id="previewHeaders"></tr>
                                        </thead>
                                        <tbody id="previewBody"></tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    `;

                    // 添加数据源相关样式
                    const styleEl = document.createElement('style');
                    styleEl.textContent = `
                        .data-source-current {
                            background: rgba(0,20,40,0.5);
                            padding: 12px;
                            border-radius: 8px;
                            border: 1px solid #00d4ff;
                        }
                        .ds-info { margin: 4px 0; }
                        .ds-label { color: #00d4ff; margin-right: 8px; }
                        .ds-value { color: #00ffff; }
                        .data-source-upload {
                            background: rgba(0,20,40,0.5);
                            padding: 16px;
                            border-radius: 8px;
                            border: 1px solid #00d4ff;
                        }
                        .ds-form { display: flex; flex-direction: column; gap: 12px; }
                        .ds-form-row {
                            display: flex;
                            gap: 12px;
                            align-items: center;
                        }
                        .ds-form-group {
                            display: flex;
                            align-items: center;
                            gap: 8px;
                        }
                        .ds-input {
                            background: rgba(0,0,0,0.3);
                            border: 1px solid #00d4ff;
                            color: #00ffff;
                            padding: 8px 12px;
                            border-radius: 4px;
                        }
                        .ds-input:focus {
                            outline: none;
                            border-color: #00ffff;
                            box-shadow: 0 0 5px rgba(0,255,255,0.5);
                        }
                        .full-width { width: 100%; }
                        .ds-checkbox {
                            display: flex;
                            align-items: center;
                            gap: 6px;
                            color: #00d4ff;
                            cursor: pointer;
                        }
                        .ds-checkbox input { 
                            width: 16px;
                            height: 16px;
                        }
                        .ds-message {
                            margin-top: 12px;
                            padding: 8px;
                            border-radius: 4px;
                            font-size: 0.9em;
                        }
                        .file-preview {
                            margin-top: 20px;
                            background: rgba(0,20,40,0.5);
                            padding: 16px;
                            border-radius: 8px;
                            border: 1px solid #00d4ff;
                        }
                        .file-preview h3 {
                            margin: 0 0 12px 0;
                            color: #00ffff;
                        }
                        .file-info {
                            display: grid;
                            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                            gap: 12px;
                            margin-bottom: 16px;
                        }
                        .info-row {
                            background: rgba(0,0,0,0.2);
                            padding: 8px;
                            border-radius: 4px;
                        }
                        .info-label {
                            color: #00d4ff;
                            margin-right: 8px;
                        }
                        .info-value {
                            color: #00ffff;
                        }
                        .preview-data {
                            max-height: 300px;
                            overflow: auto;
                        }
                    `;
                    document.head.appendChild(styleEl);
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
                case 'rules':
                    updateRulesDetail();
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
                case 'datasource':
                    fetchDataSource();
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
            
            // 获取动态阈值
            const tempCombustionThreshold = thresholdsCache['temperature_combustion']?.threshold || 760;
            const efficiencyThreshold = thresholdsCache['efficiency']?.threshold || 90;
            
            // 更新正常范围显示
            const rangeTempCombustion = document.getElementById('rangeTempCombustion');
            const rangeEfficiency = document.getElementById('rangeEfficiency');
            if (rangeTempCombustion) {
                rangeTempCombustion.textContent = `>${tempCombustionThreshold}℃`;
            }
            if (rangeEfficiency) {
                rangeEfficiency.textContent = `>${efficiencyThreshold}%`;
            }
            
            // 更新状态
            document.getElementById('statusTempCombustion').textContent = 
                realtime.temperature_combustion >= tempCombustionThreshold ? '正常' : '异常';
            document.getElementById('statusEfficiency').textContent = 
                realtime.efficiency >= efficiencyThreshold ? '正常' : '异常';
            document.getElementById('statusConcentrationIn').textContent = 
                realtime.concentration_in >= 100 && realtime.concentration_in <= 300 ? '正常' : '异常';
        }
        
        function updateTemperatureDetail(data) {
            const realtime = data.realtime;
            
            document.getElementById('detailTempOutlet').textContent = realtime.temperature_outlet.toFixed(1);
            document.getElementById('detailTempAdsorption').textContent = realtime.temperature_adsorption.toFixed(1);
            document.getElementById('detailTempDesorption').textContent = realtime.temperature_desorption.toFixed(1);
            document.getElementById('detailTempReactor').textContent = realtime.temperature_reactor_outlet.toFixed(1);
            
            // 获取动态阈值
            const tempOutletThreshold = thresholdsCache['temperature_outlet']?.threshold || 60;
            const tempAdsorptionThreshold = thresholdsCache['temperature_adsorption']?.threshold || 40;
            const tempDesorptionThreshold = thresholdsCache['temperature_desorption']?.threshold || 90;
            const tempReactorThreshold = thresholdsCache['temperature_reactor_outlet']?.threshold || 600;
            
            // 更新状态
            document.getElementById('statusTempOutlet').textContent = 
                realtime.temperature_outlet <= tempOutletThreshold ? '正常' : '异常';
            document.getElementById('statusTempAdsorption').textContent = 
                realtime.temperature_adsorption <= tempAdsorptionThreshold ? '正常' : '异常';
            document.getElementById('statusTempDesorption').textContent = 
                realtime.temperature_desorption >= tempDesorptionThreshold && realtime.temperature_desorption <= (tempDesorptionThreshold + 30) ? '正常' : '异常';
            document.getElementById('statusTempReactor').textContent = 
                realtime.temperature_reactor_outlet <= tempReactorThreshold ? '正常' : '异常';
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
        
        async function updateRulesDetail() {
            try {
                const response = await fetch('/api/rules');
                const result = await response.json();
                
                if (result.success) {
                    displayRules(result.data);
                } else {
                    document.getElementById('rulesDetail').innerHTML = 
                        '<div style="color: #ff0040; text-align: center; padding: 20px;">加载规则失败: ' + result.error + '</div>';
                }
            } catch (error) {
                document.getElementById('rulesDetail').innerHTML = 
                    '<div style="color: #ff0040; text-align: center; padding: 20px;">网络错误: ' + error.message + '</div>';
            }
        }

        async function loadDataFile() {
            const path = document.getElementById('filePathInput')?.value?.trim();
            const speed = parseFloat(document.getElementById('fileSpeedInput')?.value || '2');
            const loop = document.getElementById('fileLoopInput')?.checked;
            if (!path) { alert('请输入文件路径'); return; }
            
            // 清除之前的预览
            document.getElementById('filePreview').style.display = 'none';
            
            try {
                const res = await fetch('/api/load-data-file', {
                    method: 'POST', 
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({ path, speed_seconds: speed, loop })
                });
                const result = await res.json();
                const msg = document.getElementById('dsMsg');
                
                if (result.success) {
                    msg.textContent = result.message;
                    msg.style.color = '#00ff41';
                    fetchDataSource();
                    
                    // 显示文件预览
                    if (result.preview && result.info) {
                        const preview = document.getElementById('filePreview');
                        preview.style.display = 'block';
                        
                        // 更新文件信息
                        document.getElementById('previewFileName').textContent = result.info.filename;
                        document.getElementById('previewFileSize').textContent = formatFileSize(result.info.size);
                        document.getElementById('previewTotalRows').textContent = result.info.total_rows.toLocaleString();
                        document.getElementById('previewColumns').textContent = result.info.columns.length;
                        
                        // 更新预览表格
                        const headers = document.getElementById('previewHeaders');
                        headers.innerHTML = result.preview.headers.map(h => 
                            `<th>${h}</th>`
                        ).join('');
                        
                        const body = document.getElementById('previewBody');
                        body.innerHTML = result.preview.data.map(row => 
                            `<tr>${result.preview.headers.map(h => 
                                `<td>${formatValue(row[h])}</td>`
                            ).join('')}</tr>`
                        ).join('');
                    }
                } else { 
                    msg.textContent = result.error || '失败'; 
                    msg.style.color = '#ff0040'; 
                }
            } catch (e) { 
                alert('网络错误: ' + e.message); 
            }
        }
        
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return (bytes / Math.pow(k, i)).toFixed(1) + ' ' + sizes[i];
        }
        
        function formatValue(value) {
            if (value === null || value === undefined) return '-';
            if (typeof value === 'number') return value.toLocaleString();
            if (value instanceof Date) return value.toLocaleString();
            return value;
        }

        async function stopFileMode() {
            try {
                const res = await fetch('/api/stop-file', { method: 'POST' });
                const result = await res.json();
                const msg = document.getElementById('dsMsg');
                if (msg) msg.textContent = result.message || '';
                fetchDataSource();
            } catch (e) {}
        }
        
        function displayRules(rules) {
            const container = document.getElementById('rulesDetail');
            
            if (!rules || rules.length === 0) {
                container.innerHTML = '<div style="color: #00ff41; text-align: center; padding: 20px;">暂无规则配置</div>';
                return;
            }
            
            let html = '<div class="rules-container">';
            
            rules.forEach(rule => {
                const severityColor = rule.severity === 'critical' ? '#ff0040' : 
                                    rule.severity === 'high' ? '#ff4500' : 
                                    rule.severity === 'medium' ? '#ffaa00' : '#00ff00';
                
                html += `
                    <div class="rule-item">
                        <div class="rule-header">
                            <div class="rule-title">${rule.rule_name}</div>
                            <div class="rule-status ${rule.is_active ? 'status-active' : 'status-inactive'}">
                                ${rule.is_active ? '启用' : '禁用'}
                            </div>
                        </div>
                        <div class="rule-details">
                            <div class="rule-detail-item">
                                <div class="rule-detail-label">规则ID</div>
                                <div class="rule-detail-value">${rule.rule_id}</div>
                            </div>
                            <div class="rule-detail-item">
                                <div class="rule-detail-label">严重程度</div>
                                <div class="rule-detail-value" style="color: ${severityColor};">${rule.severity.toUpperCase()}</div>
                            </div>
                            <div class="rule-detail-item">
                                <div class="rule-detail-label">当前阈值</div>
                                <div class="rule-detail-value">
                                    <input type="number" class="threshold-input" id="threshold_${rule.rule_id}" 
                                           value="${rule.threshold_value}" step="0.1">
                                    <span style="margin-left: 5px;">${rule.threshold_unit}</span>
                                </div>
                            </div>
                            <div class="rule-detail-item">
                                <div class="rule-detail-label">条件表达式</div>
                                <div class="rule-detail-value" style="font-size: 0.8rem;">${rule.condition}</div>
                            </div>
                        </div>
                        <div style="margin: 10px 0; padding: 8px; background: rgba(0,0,0,0.3); border-radius: 4px;">
                            <div style="font-size: 0.8rem; color: #00d4ff; margin-bottom: 4px;">描述</div>
                            <div style="font-size: 0.9rem; color: #00ffff;">${rule.description}</div>
                            <div style="font-size: 0.8rem; color: #00ff41; margin-top: 4px;">
                                当前阈值: ${rule.threshold_value}${rule.threshold_unit}
                            </div>
                        </div>
                        <div class="rule-actions">
                            <button class="rule-btn" onclick="updateRuleThreshold('${rule.rule_id}')">
                                更新阈值
                            </button>
                            <button class="rule-btn ${rule.is_active ? 'danger' : ''}" 
                                    onclick="toggleRuleStatus('${rule.rule_id}')">
                                ${rule.is_active ? '禁用规则' : '启用规则'}
                            </button>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            container.innerHTML = html;
        }
        
        async function updateRuleThreshold(ruleId) {
            const input = document.getElementById(`threshold_${ruleId}`);
            const newThreshold = parseFloat(input.value);
            
            if (isNaN(newThreshold)) {
                alert('请输入有效的数值');
                return;
            }
            
            try {
                const response = await fetch('/api/rules/update-threshold', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        rule_id: ruleId,
                        threshold: newThreshold
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('阈值更新成功: ' + result.message);
                    // 重新获取阈值信息
                    await fetchThresholds();
                    // 重新加载规则列表
                    updateRulesDetail();
                } else {
                    alert('更新失败: ' + result.error);
                }
            } catch (error) {
                alert('网络错误: ' + error.message);
            }
        }
        
        async function toggleRuleStatus(ruleId) {
            try {
                const response = await fetch('/api/rules/toggle-status', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        rule_id: ruleId
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('规则状态更新成功: ' + result.message);
                    // 重新加载规则列表
                    updateRulesDetail();
                } else {
                    alert('操作失败: ' + result.error);
                }
            } catch (error) {
                alert('网络错误: ' + error.message);
            }
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
        fetchThresholds(); // 获取初始阈值信息
        fetchData();
        setInterval(fetchData, 2000);
        setInterval(fetchDataSource, 3000);
        setInterval(fetchThresholds, 10000); // 每10秒更新一次阈值信息
        
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
                    # 文件模式优先（以是否有已加载数据为准）
                    if hasattr(self, 'file_player') and self.file_player and self.file_player.has_data() and ((getattr(self, 'mode', None) is not None and self.mode[0] == 'file') or True):
                        row = self.file_player.get_next()
                        if row is None:
                            # 若暂未到时间或播放结束，返回最近一次数据（若无则空）
                            data = {
                                'realtime': {}, 'alerts': [],
                                'equipment_status': getattr(self.data_generator, 'equipment_status', {}),
                                'alert_history': getattr(self.data_generator, 'alert_history', [])
                            }
                        else:
                            # 利用规则引擎评估
                            alerts = self.rule_engine.evaluate_row_for_alerts(row)
                            # 更新历史与状态
                            self.data_generator.data_history.append(row)
                            if len(self.data_generator.data_history) > 100:
                                self.data_generator.data_history.pop(0)
                            severity_to_status = {'critical': 'critical', 'high': 'warning', 'medium': 'warning', 'low': 'normal'}
                            for a in alerts:
                                a['timestamp'] = row.get('timestamp', datetime.now())
                                self.data_generator.alert_history.append(a)
                                eq = a.get('equipment')
                                if eq:
                                    self.data_generator.equipment_status[eq] = severity_to_status.get(a.get('severity'), 'warning')
                            cutoff_time = datetime.now() - timedelta(minutes=3)
                            self.data_generator.alert_history = [a for a in self.data_generator.alert_history if a.get('timestamp', datetime.now()) > cutoff_time]
                            data = {
                                'realtime': row,
                                'alerts': alerts,
                                'alert_history': self.data_generator.alert_history,
                                'equipment_status': self.data_generator.equipment_status,
                                'trend_data': self.data_generator.data_history[-20:] if len(self.data_generator.data_history) >= 20 else self.data_generator.data_history
                            }
                    else:
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

            def send_data_source(self):
                info = {
                    'mode': 'file' if (self.file_player and self.file_player.has_data() and (self.mode and self.mode[0] == 'file')) else 'realtime',
                    'file': getattr(self.file_player, 'file_path', None),
                    'loaded_rows': int(len(self.file_player.df) if (self.file_player and self.file_player.df is not None) else 0),
                    'current_index': int(self.file_player.index if (self.file_player and self.file_player.df is not None) else 0)
                }
                json_data = json.dumps({'success': True, 'data': info}, ensure_ascii=False)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json_data.encode('utf-8'))
            
            def send_rules_list(self):
                """发送规则列表API"""
                if hasattr(self, 'rule_engine') and self.rule_engine:
                    rules = self.rule_engine.get_all_rules()
                    response_data = {
                        'success': True,
                        'data': rules,
                        'total': len(rules)
                    }
                else:
                    response_data = {
                        'success': False,
                        'error': '规则引擎未初始化'
                    }
                
                json_data = json.dumps(response_data, ensure_ascii=False, default=str)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json_data.encode('utf-8'))
            
            def send_rules_thresholds(self):
                """发送规则阈值信息API"""
                if hasattr(self, 'rule_engine') and self.rule_engine:
                    # 构建阈值映射
                    thresholds = {}
                    for rule in self.rule_engine.rules:
                        if rule.is_active:
                            # 根据规则ID映射到对应的数据字段
                            field_mapping = {
                                "R001": "temperature_combustion",
                                "R002": "concentration_out", 
                                "R005": "temperature_outlet",
                                "R007": "temperature_adsorption",
                                "R008": "temperature_desorption",
                                "R015": "temperature_reactor_outlet",
                                "R014": "pressure_loss_catalytic",
                                "R011": "particle_content",
                                "R004": "efficiency"
                            }
                            
                            field = field_mapping.get(rule.rule_id)
                            if field:
                                thresholds[field] = {
                                    'threshold': rule.threshold_value,
                                    'unit': rule.threshold_unit,
                                    'rule_id': rule.rule_id,
                                    'rule_name': rule.rule_name
                                }
                    
                    response_data = {
                        'success': True,
                        'data': thresholds
                    }
                else:
                    response_data = {
                        'success': False,
                        'error': '规则引擎未初始化'
                    }
                
                json_data = json.dumps(response_data, ensure_ascii=False, default=str)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json_data.encode('utf-8'))
            
            def send_rule_detail(self, rule_id):
                """发送单个规则详情API"""
                if hasattr(self, 'rule_engine') and self.rule_engine:
                    rule = self.rule_engine.get_rule_by_id(rule_id)
                    if rule:
                        response_data = {
                            'success': True,
                            'data': rule
                        }
                    else:
                        response_data = {
                            'success': False,
                            'error': f'未找到规则ID: {rule_id}'
                        }
                else:
                    response_data = {
                        'success': False,
                        'error': '规则引擎未初始化'
                    }
                
                json_data = json.dumps(response_data, ensure_ascii=False, default=str)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json_data.encode('utf-8'))
            
            def update_rule_threshold(self):
                """更新规则阈值API"""
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    
                    rule_id = data.get('rule_id')
                    new_threshold = data.get('threshold')
                    
                    if not rule_id or new_threshold is None:
                        response_data = {
                            'success': False,
                            'error': '缺少必要参数: rule_id 和 threshold'
                        }
                    elif hasattr(self, 'rule_engine') and self.rule_engine:
                        success = self.rule_engine.update_rule_threshold(rule_id, float(new_threshold))
                        if success:
                            response_data = {
                                'success': True,
                                'message': f'规则 {rule_id} 阈值已更新为 {new_threshold}'
                            }
                        else:
                            response_data = {
                                'success': False,
                                'error': f'更新失败: 未找到规则ID {rule_id}'
                            }
                    else:
                        response_data = {
                            'success': False,
                            'error': '规则引擎未初始化'
                        }
                        
                except Exception as e:
                    response_data = {
                        'success': False,
                        'error': f'请求处理失败: {str(e)}'
                    }
                
                json_data = json.dumps(response_data, ensure_ascii=False, default=str)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json_data.encode('utf-8'))
            
            def toggle_rule_status(self):
                """切换规则状态API"""
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    
                    rule_id = data.get('rule_id')
                    
                    if not rule_id:
                        response_data = {
                            'success': False,
                            'error': '缺少必要参数: rule_id'
                        }
                    elif hasattr(self, 'rule_engine') and self.rule_engine:
                        success = self.rule_engine.toggle_rule_status(rule_id)
                        if success:
                            rule = self.rule_engine.get_rule_by_id(rule_id)
                            status = "启用" if rule['is_active'] else "禁用"
                            response_data = {
                                'success': True,
                                'message': f'规则 {rule_id} 已{status}',
                                'is_active': rule['is_active']
                            }
                        else:
                            response_data = {
                                'success': False,
                                'error': f'操作失败: 未找到规则ID {rule_id}'
                            }
                    else:
                        response_data = {
                            'success': False,
                            'error': '规则引擎未初始化'
                        }
                        
                except Exception as e:
                    response_data = {
                        'success': False,
                        'error': f'请求处理失败: {str(e)}'
                    }
                
                json_data = json.dumps(response_data, ensure_ascii=False, default=str)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json_data.encode('utf-8'))
            
            def update_rule(self, rule_id):
                """更新规则API"""
                try:
                    content_length = int(self.headers['Content-Length'])
                    put_data = self.rfile.read(content_length)
                    data = json.loads(put_data.decode('utf-8'))
                    
                    if hasattr(self, 'rule_engine') and self.rule_engine:
                        # 查找并更新规则
                        rule_found = False
                        for rule in self.rule_engine.rules:
                            if rule.rule_id == rule_id:
                                # 更新规则属性
                                if 'threshold_value' in data:
                                    rule.threshold_value = float(data['threshold_value'])
                                if 'threshold_unit' in data:
                                    rule.threshold_unit = data['threshold_unit']
                                if 'severity' in data:
                                    rule.severity = data['severity']
                                if 'is_active' in data:
                                    rule.is_active = bool(data['is_active'])
                                if 'description' in data:
                                    rule.description = data['description']
                                
                                self.rule_engine._save_rules_to_file()
                                rule_found = True
                                break
                        
                        if rule_found:
                            response_data = {
                                'success': True,
                                'message': f'规则 {rule_id} 已更新'
                            }
                        else:
                            response_data = {
                                'success': False,
                                'error': f'未找到规则ID: {rule_id}'
                            }
                    else:
                        response_data = {
                            'success': False,
                            'error': '规则引擎未初始化'
                        }
                        
                except Exception as e:
                    response_data = {
                        'success': False,
                        'error': f'请求处理失败: {str(e)}'
                    }
                
                json_data = json.dumps(response_data, ensure_ascii=False, default=str)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json_data.encode('utf-8'))
            
            def load_data_file(self):
                """加载CSV/XLSX文件并切换为文件模式"""
                try:
                    content_length = int(self.headers.get('Content-Length', '0'))
                    body = self.rfile.read(content_length) if content_length > 0 else b''
                    data = json.loads(body.decode('utf-8') or '{}')
                    path = data.get('path')
                    speed = float(data.get('speed_seconds', 2.0))
                    loop = bool(data.get('loop', True))
                    if not path:
                        resp = {'success': False, 'error': '缺少参数: path'}
                    else:
                        # 先预览文件
                        preview = self.file_player.preview_file(path)
                        if not preview['success']:
                            resp = {'success': False, 'error': preview['error']}
                        else:
                            # 预览成功再加载
                            ok, msg = self.file_player.load_file(path, speed_seconds=speed, loop=loop)
                            if ok:
                                # 用一个可变对象存储模式，便于在handler中共享/修改
                                self.mode[0] = 'file'
                                resp = {
                                    'success': True, 
                                    'message': msg,
                                    'preview': preview['preview'],
                                    'info': preview['info']
                                }
                            else:
                                resp = {'success': False, 'error': msg}
                except Exception as e:
                    resp = {'success': False, 'error': f'加载失败: {e}'}

                json_data = json.dumps(resp, ensure_ascii=False)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json_data.encode('utf-8'))

            def stop_file_mode(self):
                try:
                    self.mode[0] = 'realtime'
                    resp = {'success': True, 'message': '已切换到实时模拟模式'}
                except Exception as e:
                    resp = {'success': False, 'error': str(e)}
                json_data = json.dumps(resp, ensure_ascii=False)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json_data.encode('utf-8'))
        
        def handler(*args, **kwargs):
            # 使用列表包装mode以在handler实例之间共享与修改
            if not hasattr(self, '_shared_mode_ref'):
                self._shared_mode_ref = [self.mode]
            return TechHTTPHandler(*args, data_generator=self.data_generator, rule_engine=self.rule_engine, mode_ref=self._shared_mode_ref, file_player=self.file_player, **kwargs)
        
        with HTTPServer(('localhost', self.port), handler) as server:
            print(f"🚀 RTO/RCO交互式监控大屏启动成功!")
            print(f"📱 访问地址: http://localhost:{self.port}")
            print(f"⚡ 交互式大屏 + 实时数据更新")
            print(f"🎯 报警频率: 5秒内1条报警")
            print(f"🖱️ 所有模块可点击交互")
            print(f"📊 数据更新频率: 每2秒一次")
            print(f"⚙️ 新增功能: 预警规则管理API")
            print(f"🔧 API端点:")
            print(f"   GET  /api/rules - 获取所有规则")
            print(f"   GET  /api/rules/thresholds - 获取规则阈值信息")
            print(f"   POST /api/rules/update-threshold - 更新规则阈值")
            print(f"   POST /api/rules/toggle-status - 切换规则状态")
            print(f"   PUT  /api/rules/{{rule_id}} - 更新规则详情")
            print(f"   POST /api/load-data-file - 加载CSV/XLSX为数据源")
            print(f"   POST /api/stop-file - 停止文件模式，恢复实时模拟")
            print(f"   GET  /api/data-source - 获取当前数据源状态")
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

