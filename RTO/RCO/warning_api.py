#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预警信息API服务
提供RESTful API接口获取预警系统信息
"""

import json
import time
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 导入预警系统相关模块
try:
    from file_player import FileDataPlayer
    import pandas as pd
    import numpy as np
    from dataclasses import dataclass, asdict
    import random
    
    # 复制必要的类定义
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
        
        def get_all_rules(self) -> List[Dict]:
            """获取所有规则信息"""
            return [asdict(rule) for rule in self.rules]
        
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

except ImportError as e:
    print(f"❌ 导入依赖模块失败: {e}")
    print("请确保pandas, numpy等依赖已安装")
    sys.exit(1)

class WarningAPIServer:
    """预警信息API服务器"""
    
    def __init__(self, port=8091):
        self.port = port
        self.data_generator = None
        self.rule_engine = None
        self.running = False
        self.start_time = time.time()
        
    def initialize_system(self):
        """初始化预警系统"""
        try:
            self.data_generator = RealTimeDataGenerator()
            self.rule_engine = WarningRuleEngine()
            print("✅ 预警系统初始化成功")
            return True
        except Exception as e:
            print(f"❌ 预警系统初始化失败: {e}")
            return False
    
    def start_server(self):
        """启动API服务器"""
        if not self.initialize_system():
            return
        
        class WarningAPIHandler(BaseHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                self.api_server = kwargs.pop('api_server', None)
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                """处理GET请求"""
                parsed_path = urlparse(self.path)
                path = parsed_path.path
                query_params = parse_qs(parsed_path.query)
                
                # 设置CORS头
                self.send_cors_headers()
                
                if path == '/api/warnings':
                    self.get_warnings_info()
                elif path == '/api/warnings/current':
                    self.get_current_alerts()
                elif path == '/api/warnings/history':
                    self.get_alert_history(query_params)
                elif path == '/api/warnings/statistics':
                    self.get_warning_statistics()
                elif path == '/api/warnings/equipment':
                    self.get_equipment_status()
                elif path == '/api/warnings/rules':
                    self.get_warning_rules()
                elif path == '/api/health':
                    self.get_health_status()
                else:
                    self.send_error(404, "API endpoint not found")
            
            def do_OPTIONS(self):
                """处理OPTIONS请求（CORS预检）"""
                self.send_cors_headers()
                self.end_headers()
            
            def send_cors_headers(self):
                """发送CORS头"""
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                self.send_header('Content-Type', 'application/json; charset=utf-8')
            
            def send_json_response(self, data, status_code=200):
                """发送JSON响应"""
                self.send_response(status_code)
                self.send_cors_headers()
                self.end_headers()
                json_data = json.dumps(data, ensure_ascii=False, default=str, indent=2)
                self.wfile.write(json_data.encode('utf-8'))
            
            def get_warnings_info(self):
                """获取完整预警信息"""
                try:
                    # 生成一些实时数据用于演示
                    if self.api_server.data_generator:
                        realtime_data = self.api_server.data_generator.generate_realtime_data()
                        alert_history = realtime_data.get('alert_history', [])
                        equipment_status = realtime_data.get('equipment_status', {})
                        current_alerts = realtime_data.get('alerts', [])
                    else:
                        alert_history = []
                        equipment_status = {}
                        current_alerts = []
                    
                    # 获取违规汇总
                    violation_summary = self.api_server.rule_engine.get_violation_summary()
                    
                    # 按严重程度分类告警
                    alerts_by_severity = {
                        'critical': [],
                        'high': [],
                        'medium': [],
                        'low': []
                    }
                    
                    for alert in alert_history[-20:]:  # 最近20条告警
                        severity = alert.get('severity', 'low')
                        if severity in alerts_by_severity:
                            alerts_by_severity[severity].append(alert)
                    
                    # 统计信息
                    stats = {
                        'total_alerts_today': len(alert_history),
                        'active_alerts_count': len(current_alerts),
                        'critical_alerts': len(alerts_by_severity['critical']),
                        'high_alerts': len(alerts_by_severity['high']),
                        'medium_alerts': len(alerts_by_severity['medium']),
                        'low_alerts': len(alerts_by_severity['low']),
                        'equipment_count': len(equipment_status),
                        'normal_equipment': sum(1 for status in equipment_status.values() if status == 'normal'),
                        'warning_equipment': sum(1 for status in equipment_status.values() if status == 'warning'),
                        'critical_equipment': sum(1 for status in equipment_status.values() if status == 'critical')
                    }
                    
                    response_data = {
                        'success': True,
                        'data': {
                            'current_alerts': current_alerts,
                            'alert_history': alert_history[-10:],  # 最近10条历史
                            'alerts_by_severity': alerts_by_severity,
                            'violation_summary': violation_summary,
                            'equipment_status': equipment_status,
                            'statistics': stats,
                            'last_updated': datetime.now().isoformat()
                        }
                    }
                    
                except Exception as e:
                    response_data = {
                        'success': False,
                        'error': f'获取预警信息失败: {str(e)}'
                    }
                
                self.send_json_response(response_data)
            
            def get_current_alerts(self):
                """获取当前活跃告警"""
                try:
                    if self.api_server.data_generator:
                        realtime_data = self.api_server.data_generator.generate_realtime_data()
                        current_alerts = realtime_data.get('alerts', [])
                    else:
                        current_alerts = []
                    
                    response_data = {
                        'success': True,
                        'data': {
                            'current_alerts': current_alerts,
                            'count': len(current_alerts),
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                except Exception as e:
                    response_data = {
                        'success': False,
                        'error': f'获取当前告警失败: {str(e)}'
                    }
                
                self.send_json_response(response_data)
            
            def get_alert_history(self, query_params):
                """获取告警历史"""
                try:
                    # 获取查询参数
                    limit = int(query_params.get('limit', ['50'])[0])
                    severity = query_params.get('severity', [None])[0]
                    
                    if self.api_server.data_generator:
                        realtime_data = self.api_server.data_generator.generate_realtime_data()
                        alert_history = realtime_data.get('alert_history', [])
                    else:
                        alert_history = []
                    
                    # 按严重程度过滤
                    if severity:
                        alert_history = [alert for alert in alert_history if alert.get('severity') == severity]
                    
                    # 限制数量
                    alert_history = alert_history[-limit:]
                    
                    response_data = {
                        'success': True,
                        'data': {
                            'alert_history': alert_history,
                            'count': len(alert_history),
                            'filters': {
                                'limit': limit,
                                'severity': severity
                            },
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                except Exception as e:
                    response_data = {
                        'success': False,
                        'error': f'获取告警历史失败: {str(e)}'
                    }
                
                self.send_json_response(response_data)
            
            def get_warning_statistics(self):
                """获取预警统计信息"""
                try:
                    if self.api_server.data_generator:
                        realtime_data = self.api_server.data_generator.generate_realtime_data()
                        alert_history = realtime_data.get('alert_history', [])
                        equipment_status = realtime_data.get('equipment_status', {})
                    else:
                        alert_history = []
                        equipment_status = {}
                    
                    # 按严重程度统计
                    severity_stats = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
                    for alert in alert_history:
                        severity = alert.get('severity', 'low')
                        if severity in severity_stats:
                            severity_stats[severity] += 1
                    
                    # 按设备统计
                    equipment_stats = {}
                    for alert in alert_history:
                        equipment = alert.get('equipment', '未知设备')
                        equipment_stats[equipment] = equipment_stats.get(equipment, 0) + 1
                    
                    # 按时间统计（最近24小时）
                    now = datetime.now()
                    hourly_stats = {}
                    for i in range(24):
                        hour = (now - timedelta(hours=i)).strftime('%H:00')
                        hourly_stats[hour] = 0
                    
                    for alert in alert_history:
                        if isinstance(alert.get('timestamp'), str):
                            try:
                                alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
                            except:
                                continue
                        else:
                            alert_time = alert.get('timestamp', now)
                        
                        if (now - alert_time).total_seconds() < 24 * 3600:  # 24小时内
                            hour = alert_time.strftime('%H:00')
                            if hour in hourly_stats:
                                hourly_stats[hour] += 1
                    
                    response_data = {
                        'success': True,
                        'data': {
                            'severity_distribution': severity_stats,
                            'equipment_distribution': equipment_stats,
                            'hourly_distribution': hourly_stats,
                            'total_alerts': len(alert_history),
                            'equipment_status': equipment_status,
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                except Exception as e:
                    response_data = {
                        'success': False,
                        'error': f'获取统计信息失败: {str(e)}'
                    }
                
                self.send_json_response(response_data)
            
            def get_equipment_status(self):
                """获取设备状态"""
                try:
                    if self.api_server.data_generator:
                        realtime_data = self.api_server.data_generator.generate_realtime_data()
                        equipment_status = realtime_data.get('equipment_status', {})
                    else:
                        equipment_status = {}
                    
                    # 统计设备状态
                    status_counts = {'normal': 0, 'warning': 0, 'critical': 0}
                    for status in equipment_status.values():
                        if status in status_counts:
                            status_counts[status] += 1
                    
                    response_data = {
                        'success': True,
                        'data': {
                            'equipment_status': equipment_status,
                            'status_counts': status_counts,
                            'total_equipment': len(equipment_status),
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                except Exception as e:
                    response_data = {
                        'success': False,
                        'error': f'获取设备状态失败: {str(e)}'
                    }
                
                self.send_json_response(response_data)
            
            def get_warning_rules(self):
                """获取预警规则"""
                try:
                    rules = self.api_server.rule_engine.get_all_rules()
                    
                    # 统计规则状态
                    active_rules = [rule for rule in rules if rule.get('is_active', True)]
                    inactive_rules = [rule for rule in rules if not rule.get('is_active', True)]
                    
                    response_data = {
                        'success': True,
                        'data': {
                            'all_rules': rules,
                            'active_rules': active_rules,
                            'inactive_rules': inactive_rules,
                            'total_rules': len(rules),
                            'active_count': len(active_rules),
                            'inactive_count': len(inactive_rules),
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                except Exception as e:
                    response_data = {
                        'success': False,
                        'error': f'获取预警规则失败: {str(e)}'
                    }
                
                self.send_json_response(response_data)
            
            def get_health_status(self):
                """获取API健康状态"""
                try:
                    uptime = time.time() - self.api_server.start_time
                    health_data = {
                        'status': 'healthy',
                        'timestamp': datetime.now().isoformat(),
                        'uptime_seconds': uptime,
                        'uptime_formatted': f"{int(uptime//3600)}h {int((uptime%3600)//60)}m {int(uptime%60)}s",
                        'version': '1.0.0',
                        'services': {
                            'data_generator': self.api_server.data_generator is not None,
                            'rule_engine': self.api_server.rule_engine is not None
                        }
                    }
                    
                    response_data = {
                        'success': True,
                        'data': health_data
                    }
                    
                except Exception as e:
                    response_data = {
                        'success': False,
                        'error': f'获取健康状态失败: {str(e)}'
                    }
                
                self.send_json_response(response_data)
            
            def log_message(self, format, *args):
                """自定义日志格式"""
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] {format % args}")
        
        def handler(*args, **kwargs):
            return WarningAPIHandler(*args, api_server=self, **kwargs)
        
        try:
            with HTTPServer(('localhost', self.port), handler) as server:
                self.running = True
                print(f"🚀 预警信息API服务器启动成功!")
                print(f"📡 服务地址: http://localhost:{self.port}")
                print(f"📋 可用API端点:")
                print(f"   GET /api/warnings - 获取完整预警信息")
                print(f"   GET /api/warnings/current - 获取当前活跃告警")
                print(f"   GET /api/warnings/history?limit=50&severity=critical - 获取告警历史")
                print(f"   GET /api/warnings/statistics - 获取预警统计信息")
                print(f"   GET /api/warnings/equipment - 获取设备状态")
                print(f"   GET /api/warnings/rules - 获取预警规则")
                print(f"   GET /api/health - 获取API健康状态")
                print(f"🛑 按 Ctrl+C 停止服务")
                
                server.serve_forever()
                
        except KeyboardInterrupt:
            print("\n👋 API服务器已停止")
            self.running = False
        except Exception as e:
            print(f"❌ 服务器启动失败: {e}")
            self.running = False

def main():
    """主函数"""
    print("🏭 预警信息API服务")
    print("=" * 50)
    
    # 创建并启动API服务器
    api_server = WarningAPIServer(port=8091)
    api_server.start_server()

if __name__ == "__main__":
    main()
