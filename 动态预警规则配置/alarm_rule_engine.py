#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原始预警规则引擎 - alarm_rule_engine.py

作用：
    基础版本的预警引擎实现，用于功能对比和学习参考

主要功能：
    - 基础预警规则处理
    - 单属性和双属性规则评估
    - 简单的预警消息生成

技术特点：
    - 传统实现方式
    - 功能完整但代码较长（258行）
    - 适合学习和对比

对比说明：
    相比精简版引擎，此版本代码结构较为传统，
    主要用于展示优化前后的差异
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from alarm_rule_manager import AlarmRuleManager


class AlarmRuleEngine:
    """预警规则引擎"""
    
    def __init__(self, config_file: str = "settings.toml"):
        """初始化预警规则引擎"""
        self.manager = AlarmRuleManager(config_file)
        self.alarm_history = []  # 预警历史记录
        
    def evaluate_single_property_rule(self, rule: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """评估单属性规则"""
        property_name = rule.get('property', '')
        low_value = rule.get('lowValue', 0)
        high_value = rule.get('highValue', 0)
        expression1 = rule.get('expression1', 'lt')  # 最小值比较表达式
        expression2 = rule.get('expression2', 'lt')  # 最大值比较表达式
        
        if property_name not in data:
            return False
            
        value = data[property_name]
        
        # 评估最小值条件
        low_condition = self._evaluate_expression(value, expression1, low_value)
        # 评估最大值条件
        high_condition = self._evaluate_expression(value, expression2, high_value)
        
        # 通常单属性规则是范围检查：value < low_value OR value > high_value
        return low_condition or high_condition
    
    def evaluate_double_property_rule(self, rule: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """评估双属性规则"""
        left_property = rule.get('leftProperty', '')
        right_property = rule.get('rightProperty', '')
        expression = rule.get('expression', 'lt')
        
        if left_property not in data or right_property not in data:
            return False
            
        left_value = data[left_property]
        right_value = data[right_property]
        
        return self._evaluate_expression(left_value, expression, right_value)
    
    def _evaluate_expression(self, left_value: Any, operator: str, right_value: Any) -> bool:
        """评估表达式"""
        try:
            if operator == 'lt':  # 小于
                return left_value < right_value
            elif operator == 'le':  # 小于等于
                return left_value <= right_value
            elif operator == 'gt':  # 大于
                return left_value > right_value
            elif operator == 'ge':  # 大于等于
                return left_value >= right_value
            elif operator == 'eq':  # 等于
                return left_value == right_value
            elif operator == 'ne':  # 不等于
                return left_value != right_value
            else:
                return False
        except:
            return False
    
    def evaluate_rules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """评估所有规则"""
        config = self.manager.get_fresh_config()
        alarm_rule = config.get('alarm_rule', {})
        
        # 检查预警是否启用
        if not alarm_rule.get('enabled', 1):
            return {'triggered': False, 'reason': '预警规则已禁用'}
        
        # 检查时间范围
        if not self._is_in_time_range(alarm_rule):
            return {'triggered': False, 'reason': '不在预警时间范围内'}
        
        # 获取预警类别对应的配置
        alarm_clazz = alarm_rule.get('alarmClazz', 'DEVICE_ALARM')
        if alarm_clazz == 'DEVICE_ALARM':
            alarm_config = config.get('device_alarm_config', {})
        elif alarm_clazz == 'ENTERPRISE_ALARM':
            alarm_config = config.get('enterprise_alarm_config', {})
        else:
            return {'triggered': False, 'reason': '未知的预警类别'}
        
        # 评估单属性规则
        single_rules = alarm_config.get('singlePropertyRule', [])
        single_results = []
        
        for rule in single_rules:
            result = self.evaluate_single_property_rule(rule, data)
            single_results.append({
                'rule': rule,
                'result': result,
                'type': 'single'
            })
        
        # 评估双属性规则
        double_rules = alarm_config.get('doublePropertyRule', [])
        double_results = []
        
        for rule in double_rules:
            result = self.evaluate_double_property_rule(rule, data)
            double_results.append({
                'rule': rule,
                'result': result,
                'type': 'double'
            })
        
        # 组合规则结果
        all_results = single_results + double_results
        triggered_rules = [r for r in all_results if r['result']]
        
        if triggered_rules:
            # 检查频率限制
            frequency_config = alarm_config.get('frequency', {})
            if self._check_frequency_limit(frequency_config, alarm_rule):
                return {
                    'triggered': True,
                    'alarm_rule': alarm_rule,
                    'triggered_rules': triggered_rules,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {'triggered': False, 'reason': '频率限制未满足'}
        
        return {'triggered': False, 'reason': '未触发任何规则'}
    
    def _is_in_time_range(self, alarm_rule: Dict[str, Any]) -> bool:
        """检查是否在预警时间范围内"""
        try:
            start_time = alarm_rule.get('startTime', '00:00')
            end_time = alarm_rule.get('endTime', '23:59')
            
            current_time = datetime.now().strftime('%H:%M')
            
            return start_time <= current_time <= end_time
        except:
            return True  # 如果时间格式错误，默认允许
    
    def _check_frequency_limit(self, frequency_config: Dict[str, Any], alarm_rule: Dict[str, Any]) -> bool:
        """检查频率限制"""
        if not frequency_config.get('enabled', 1):
            return True  # 频率检查未启用，直接通过
        
        # 简化实现：这里可以根据实际需求实现更复杂的频率检查逻辑
        # 例如检查累计异常次数、连续异常次数等
        return True
    
    def generate_alarm_message(self, evaluation_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成预警消息"""
        if not evaluation_result.get('triggered', False):
            return None
        
        alarm_rule = evaluation_result['alarm_rule']
        triggered_rules = evaluation_result['triggered_rules']
        data = evaluation_result['data']
        
        # 构建预警消息
        alarm_message = {
            'alarmId': alarm_rule.get('alarmRuleId', ''),
            'alarmTime': evaluation_result['timestamp'],
            'data': data,
            'alarmInfo': {
                'alarmRuleName': alarm_rule.get('alarmRuleName', ''),
                'alarmLevel': alarm_rule.get('alarmLevel', 'HIGH'),
                'alarmClazz': alarm_rule.get('alarmClazz', 'DEVICE_ALARM'),
                'triggeredRulesCount': len(triggered_rules),
                'triggeredRules': [
                    {
                        'type': rule['type'],
                        'rule': rule['rule'],
                        'result': rule['result']
                    } for rule in triggered_rules
                ]
            }
        }
        
        # 记录预警历史
        self.alarm_history.append(alarm_message)
        
        return alarm_message
    
    def process_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理数据并生成预警（如果需要）"""
        # 评估规则
        evaluation_result = self.evaluate_rules(data)
        
        # 如果触发预警，生成预警消息
        if evaluation_result.get('triggered', False):
            return self.generate_alarm_message(evaluation_result)
        
        return None
    
    def get_alarm_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取预警历史记录"""
        return self.alarm_history[-limit:]
    
    def clear_alarm_history(self):
        """清空预警历史记录"""
        self.alarm_history.clear()


if __name__ == "__main__":
    # 测试预警规则引擎
    engine = AlarmRuleEngine()
    
    # 模拟测试数据
    test_data_sets = [
        # 正常数据
        {'t1': 5, 't2': 15, 't3': 8, 't4': 12},
        # 异常数据 - t1过小
        {'t1': 0.5, 't2': 15, 't3': 8, 't4': 12},
        # 异常数据 - t1过大
        {'t1': 15, 't2': 15, 't3': 8, 't4': 12},
        # 异常数据 - 双属性规则触发
        {'t1': 20, 't2': 15, 't3': 8, 't4': 12},
    ]
    
    print("=== 预警规则引擎测试 ===")
    
    for i, data in enumerate(test_data_sets, 1):
        print(f"\n测试数据 {i}: {data}")
        
        # 处理数据
        alarm = engine.process_data(data)
        
        if alarm:
            print("🚨 触发预警!")
            print(f"预警ID: {alarm['alarmId']}")
            print(f"预警时间: {alarm['alarmTime']}")
            print(f"预警等级: {alarm['alarmInfo']['alarmLevel']}")
            print(f"触发规则数量: {alarm['alarmInfo']['triggeredRulesCount']}")
        else:
            print("✅ 数据正常，未触发预警")
    
    # 显示预警历史
    history = engine.get_alarm_history()
    if history:
        print(f"\n=== 预警历史记录 ({len(history)}条) ===")
        for alarm in history:
            print(f"时间: {alarm['alarmTime']}, 等级: {alarm['alarmInfo']['alarmLevel']}")
