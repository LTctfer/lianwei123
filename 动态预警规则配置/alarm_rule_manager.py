#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态预警规则配置管理器 - alarm_rule_manager.py

作用：
    实现配置文件的动态管理和实时读取功能

主要功能：
    - 实时配置读取和刷新
    - 动态配置文件修改
    - 配置验证和规则构建
    - JSON格式导出

技术特点：
    - 基于dynaconf实现动态配置
    - 支持TOML文件格式
    - 保持文件格式和注释
    - 实时配置更新

使用场景：
    配合预警引擎实现配置驱动的预警系统
"""

import json
import os
from typing import Dict, Any
from dynaconf import Dynaconf
import tomlkit


class AlarmRuleManager:
    """预警规则配置管理器"""

    def __init__(self, config_file: str = "settings.toml"):
        """初始化配置管理器"""
        self.config_file = config_file
        # 简化Dynaconf初始化，避免参数错误
        self.settings = Dynaconf(
            settings_files=[config_file],
            environments=False
        )
    
    def get_fresh_config(self) -> Dict[str, Any]:
        """获取实时配置数据"""
        try:
            # 重新加载配置文件以获取最新数据
            self.settings.reload()
            # 只返回我们关心的配置部分，过滤掉Dynaconf内部配置
            config = {}
            for key in self.settings:
                if not key.endswith('_FOR_DYNACONF') and key not in ['RENAMED_VARS', 'DYNACONF_NAMESPACE', 'NAMESPACE_FOR_DYNACONF']:
                    config[key.lower()] = self.settings[key]
            return config
        except Exception as e:
            print(f"读取配置失败: {e}")
            return {}
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """动态更新配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                doc = tomlkit.parse(f.read())

            for key, value in updates.items():
                self._update_nested_dict(doc, key, value)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(tomlkit.dumps(doc))

            return True
        except Exception as e:
            print(f"更新配置失败: {e}")
            return False
    
    def _update_nested_dict(self, doc: tomlkit.TOMLDocument, key: str, value: Any):
        """更新嵌套字典"""
        keys = key.split('.')
        current = doc

        for k in keys[:-1]:
            # 检查是否是数组索引
            if k.isdigit():
                # 这是数组索引，跳过处理
                continue
            elif k not in current:
                current[k] = tomlkit.table()
            current = current[k]

        final_key = keys[-1]
        # 检查是否是数组索引
        if final_key.isdigit():
            # 处理数组索引
            array_index = int(final_key)
            if isinstance(current, list) and len(current) > array_index:
                current[array_index] = value
        else:
            current[final_key] = value
    
    def build_alarm_rule(self) -> Dict[str, Any]:
        """构建完整的预警规则"""
        config = self.get_fresh_config()
        alarm_rule = config.get('alarm_rule', {})

        rule = {
            "commandType": "ALARM_RULE",
            "data": {
                "alarmRuleId": alarm_rule.get('alarmRuleId', ''),
                "alarmRuleName": alarm_rule.get('alarmRuleName', ''),
                "alarmClazz": alarm_rule.get('alarmClazz', 'DEVICE_ALARM'),
                "alarmType": alarm_rule.get('alarmType', '1'),
                "alarmLevel": alarm_rule.get('alarmLevel', 'HIGH'),
                "alarmInternal": alarm_rule.get('alarmInternal', 2),
                "dataInternal": alarm_rule.get('dataInternal', '1h'),
                "algorithmType": alarm_rule.get('algorithmType', 'test'),
                "calculateWay": alarm_rule.get('calculateWay', 'test'),
                "enabled": alarm_rule.get('enabled', 1),
                "startTime": alarm_rule.get('startTime', '08:00'),
                "endTime": alarm_rule.get('endTime', '18:00'),
                "showProperties": alarm_rule.get('showProperties', []),
                "config": self._build_config_json(config, alarm_rule.get('alarmClazz', 'DEVICE_ALARM'))
            }
        }

        return rule
    
    def _build_config_json(self, config: Dict[str, Any], alarm_clazz: str) -> str:
        """构建config字段的JSON字符串"""
        if alarm_clazz == "DEVICE_ALARM":
            config_data = config.get('device_alarm_config', {})
        elif alarm_clazz == "ENTERPRISE_ALARM":
            config_data = config.get('enterprise_alarm_config', {})
        else:
            config_data = {}

        return json.dumps(config_data, ensure_ascii=False, indent=2)

    def print_current_config(self):
        """打印当前配置信息"""
        config = self.get_fresh_config()
        print("=== 当前预警规则配置 ===")
        print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    # 简单测试
    manager = AlarmRuleManager()

    # 打印当前配置
    manager.print_current_config()

    # 构建预警规则
    rule = manager.build_alarm_rule()
    print("\n完整预警规则:")
    print(json.dumps(rule, ensure_ascii=False, indent=2))
