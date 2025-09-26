





#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能预警引擎 - 精简版
基于智算中心预警规则文档的通用预警算法
所有功能集成在单一文件中，易于维护和部署

功能特点：
- 完全配置驱动，所有参数可动态调整
- 支持平台下发配置命令
- 智能频率控制（累积/连续模式）
- 标准预警消息推送
- 内置测试和演示功能
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import deque
import tomlkit


class SmartAlarmEngine:
    """智能预警引擎 - 集成所有功能的单一类"""
    
    # 操作符映射
    OPS = {
        'lt': lambda x, y: x < y, 'le': lambda x, y: x <= y, 'eq': lambda x, y: x == y,
        'gt': lambda x, y: x > y, 'ge': lambda x, y: x >= y, 'ne': lambda x, y: x != y
    }
    
    def __init__(self, config_file: str = "config.toml"):
        """初始化引擎"""
        self.config_file = config_file
        self.alarm_history = []
        self.freq_states = {}
        self._ensure_config()
    
    def _ensure_config(self):
        """确保配置文件存在"""
        if not os.path.exists(self.config_file):
            default_config = {
                "alarm_rule": {
                    "alarmRuleId": "123456",
                    "alarmRuleName": "智能预警规则",
                    "alarmClazz": "DEVICE_ALARM",
                    "alarmLevel": "HIGH",
                    "enabled": 1,
                    "startTime": "00:00",
                    "endTime": "23:59"
                },
                "device_alarm_config": {
                    "singlePropertyRule": [
                        {"symbol": "OR", "property": "t1", "lowValue": 1, "expression1": "lt", "highValue": 10, "expression2": "gt"},
                        {"symbol": "OR", "property": "t2", "lowValue": 5, "expression1": "lt", "highValue": 20, "expression2": "gt"}
                    ],
                    "doublePropertyRule": [
                        {"symbol": "AND", "leftProperty": "t1", "rightProperty": "t2", "expression": "lt"}
                    ],
                    "frequency": {"enabled": 1, "hasAccumulate": 1, "accumulateCount": 3, "accumulateTimeRange": 30}
                }
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(tomlkit.dumps(default_config))
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return tomlkit.parse(f.read())
        except:
            return {}
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            config = self.load_config()
            for key, value in updates.items():
                keys = key.split('.')
                current = config
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(tomlkit.dumps(config))
            return True
        except:
            return False
    
    def receive_platform_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """接收平台配置命令"""
        try:
            if command.get('commandType') != 'ALARM_RULE':
                return {'success': False, 'message': '不支持的命令类型'}
            
            data = command.get('data', {})
            updates = {}
            
            # 更新基础配置
            for field in ['alarmRuleId', 'alarmRuleName', 'alarmClazz', 'alarmLevel', 'enabled', 'startTime', 'endTime']:
                if field in data:
                    updates[f'alarm_rule.{field}'] = data[field]
            
            # 更新具体配置
            config_data = data.get('config', {})
            if isinstance(config_data, str):
                config_data = json.loads(config_data)
            
            alarm_clazz = data.get('alarmClazz', 'DEVICE_ALARM')
            config_prefix = 'device_alarm_config' if alarm_clazz == 'DEVICE_ALARM' else 'enterprise_alarm_config'
            
            for key in ['singlePropertyRule', 'doublePropertyRule', 'frequency']:
                if key in config_data:
                    updates[f'{config_prefix}.{key}'] = config_data[key]
            
            success = self.update_config(updates)
            return {
                'success': success,
                'message': '配置更新成功' if success else '配置更新失败',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'success': False, 'message': f'命令处理失败: {str(e)}'}
    
    def process_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理数据并生成预警"""
        config = self.load_config()
        alarm_rule = config.get('alarm_rule', {})
        
        # 基础检查
        if not alarm_rule.get('enabled', 1) or not self._in_time_range(alarm_rule):
            return None
        
        # 获取配置
        alarm_clazz = alarm_rule.get('alarmClazz', 'DEVICE_ALARM')
        alarm_config = config.get('device_alarm_config' if alarm_clazz == 'DEVICE_ALARM' else 'enterprise_alarm_config', {})
        
        # 评估规则
        triggered_rules = []
        for rule in alarm_config.get('singlePropertyRule', []) + alarm_config.get('doublePropertyRule', []):
            if self._eval_rule(rule, data):
                triggered_rules.append(rule)
        
        if not triggered_rules:
            self._update_frequency(alarm_rule.get('alarmRuleId', ''), alarm_config.get('frequency', {}), False)
            return None
        
        # 检查频率限制
        if not self._update_frequency(alarm_rule.get('alarmRuleId', ''), alarm_config.get('frequency', {}), True):
            return None
        
        # 生成预警
        alarm = {
            'alarmId': alarm_rule.get('alarmRuleId', ''),
            'alarmTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': data,
            'alarmInfo': {
                'alarmRuleName': alarm_rule.get('alarmRuleName', ''),
                'alarmLevel': alarm_rule.get('alarmLevel', 'HIGH'),
                'alarmClazz': alarm_rule.get('alarmClazz', 'DEVICE_ALARM'),
                'triggeredRulesCount': len(triggered_rules)
            }
        }
        
        self.alarm_history.append(alarm)
        return alarm
    
    def _eval_rule(self, rule: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """统一的规则评估"""
        if 'property' in rule:  # 单属性规则
            val = data.get(rule['property'], 0)
            c1 = self.OPS[rule['expression1']](val, rule['lowValue'])
            c2 = self.OPS[rule['expression2']](val, rule['highValue'])
            return c1 or c2 if rule['symbol'] == 'OR' else c1 and c2
        else:  # 双属性规则
            left = data.get(rule['leftProperty'], 0)
            right = data.get(rule['rightProperty'], 0)
            return self.OPS[rule['expression']](left, right)
    
    def _update_frequency(self, rule_id: str, config: Dict[str, Any], triggered: bool) -> bool:
        """频率控制"""
        if not config.get('enabled', 1):
            return True
        
        state = self.freq_states.setdefault(rule_id, {'events': deque(), 'count': 0})
        
        if config.get('hasAccumulate', 1):
            # 累积模式
            if triggered:
                state['events'].append(datetime.now())
            cutoff = datetime.now() - timedelta(minutes=config.get('accumulateTimeRange', 30))
            state['events'] = deque([t for t in state['events'] if t > cutoff])
            return len(state['events']) >= config.get('accumulateCount', 3)
        else:
            # 连续模式
            state['count'] = state['count'] + 1 if triggered else 0
            return state['count'] >= config.get('continuousCount', 3)
    
    def _in_time_range(self, rule: Dict[str, Any]) -> bool:
        """检查时间范围"""
        try:
            current = datetime.now().strftime('%H:%M')
            start, end = rule.get('startTime', '00:00'), rule.get('endTime', '23:59')
            return start <= current <= end
        except:
            return True
    
    def push_alarm(self, alarm: Dict[str, Any], device_id: str = "default") -> bool:
        """推送预警到平台"""
        try:
            mqtt_message = {
                'topic': f'qixiu/warning_data/{device_id}',
                'payload': {
                    'alarmId': alarm['alarmId'],
                    'alarmTime': alarm['alarmTime'],
                    'data': alarm['data']
                }
            }
            print(f"📤 推送预警: {mqtt_message['topic']}")
            print(f"   消息: {json.dumps(mqtt_message['payload'], ensure_ascii=False)}")
            return True
        except:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.alarm_history:
            return {'total_alarms': 0, 'alarm_levels': {}, 'latest_alarm_time': None}
        
        levels = {}
        for alarm in self.alarm_history:
            level = alarm['alarmInfo']['alarmLevel']
            levels[level] = levels.get(level, 0) + 1
        
        return {
            'total_alarms': len(self.alarm_history),
            'alarm_levels': levels,
            'latest_alarm_time': self.alarm_history[-1]['alarmTime']
        }
    
    def clear_history(self):
        """清空历史"""
        self.alarm_history.clear()
        self.freq_states.clear()
    
    def self_test(self):
        """内置自测试"""
        print("🧪 智能预警引擎自测试")
        print("=" * 40)
        
        self.clear_history()
        
        # 基础功能测试
        normal_data = {'t1': 5, 't2': 15, 't3': 8, 't4': 12}
        abnormal_data = {'t1': 0.5, 't2': 25, 't3': 50, 't4': 5}
        
        alarm1 = self.process_data(normal_data)
        print(f"✅ 正常数据测试: {'通过' if alarm1 is None else '失败'}")
        
        # 多次异常数据测试（触发频率控制）
        for i in range(3):
            alarm = self.process_data(abnormal_data)
        
        print(f"✅ 异常数据测试: {'通过' if alarm is not None else '失败'}")
        
        # 配置更新测试
        result = self.update_config({'alarm_rule.alarmLevel': 'MEDIUM'})
        print(f"✅ 配置更新测试: {'通过' if result else '失败'}")
        
        # 平台命令测试
        command = {
            "commandType": "ALARM_RULE",
            "data": {
                "alarmRuleId": "TEST_001",
                "alarmRuleName": "测试规则",
                "alarmLevel": "LOW"
            }
        }
        result = self.receive_platform_command(command)
        print(f"✅ 平台命令测试: {'通过' if result['success'] else '失败'}")
        
        print(f"\n📊 测试统计: {self.get_stats()}")
        print("🎉 自测试完成!")
    
    def demo(self):
        """内置演示"""
        print("🚀 智能预警引擎演示")
        print("=" * 40)
        
        self.clear_history()
        
        scenarios = [
            ({'t1': 5, 't2': 15, 't3': 8, 't4': 12}, "正常数据"),
            ({'t1': 0.1, 't2': 25, 't3': 50, 't4': 5}, "异常数据1"),
            ({'t1': 0.2, 't2': 26, 't3': 51, 't4': 6}, "异常数据2"),
            ({'t1': 0.3, 't2': 27, 't3': 52, 't4': 7}, "异常数据3"),
        ]
        
        for data, desc in scenarios:
            alarm = self.process_data(data)
            if alarm:
                print(f"🚨 {desc}: 触发预警 (ID: {alarm['alarmId']})")
                self.push_alarm(alarm, "DEMO_DEVICE")
            else:
                print(f"✅ {desc}: 正常")
        
        print(f"\n📈 演示统计: {self.get_stats()}")
        print("🎉 演示完成!")


if __name__ == "__main__":
    import sys
    
    engine = SmartAlarmEngine()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            engine.self_test()
        elif sys.argv[1] == 'demo':
            engine.demo()
        else:
            print("用法: python smart_alarm.py [test|demo]")
    else:
        # 默认运行自测试
        engine.self_test()
