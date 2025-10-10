#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试规则完全覆盖功能
"""

import requests
import json
from pprint import pprint

def test_rules_override():
    BASE_URL = "http://localhost:8000"
    
    # 1. 查看当前规则
    print("\n1. 当前规则配置:")
    print("-" * 50)
    response = requests.get(f"{BASE_URL}/get_config")
    current_rules = response.json()
    pprint(current_rules)

    # 2. 使用新规则完全覆盖
    print("\n2. 使用新规则覆盖:")
    print("-" * 50)
    new_config = {
        "rules": [
            {
                "alarmRuleId": "NEW001",
                "alarmRuleName": "新温度预警",
                "alarmClazz": "DEVICE_ALARM",
                "alarmType": "1",
                "alarmLevel": "HIGH",
                "alarmInternal": 2,
                "dataInternal": "2h",
                "algorithmType": "T-ALG",
                "calculateWay": "max",
                "enabled": 1,
                "startTime": "00:00",
                "endTime": "23:59",
                "showProperties": ["temperature"],
                "config": {
                    "singlePropertyRule": [
                        {
                            "symbol": "OR",
                            "property": "temperature",
                            "lowValue": 15,
                            "expression1": "lt",
                            "highValue": 85,
                            "expression2": "gt"
                        }
                    ],
                    "doublePropertyRule": [],
                    "frequency": {
                        "enabled": 1,
                        "hasAccumulate": 1,
                        "accumulateCount": 5,
                        "accumulateTimeRange": 600
                    }
                }
            }
        ]
    }
    
    print("发送新规则:")
    pprint(new_config)
    
    response = requests.post(
        f"{BASE_URL}/sync_rules",
        json=new_config
    )
    print("\n更新响应:")
    pprint(response.json())

    # 3. 验证规则是否已完全覆盖
    print("\n3. 验证新规则:")
    print("-" * 50)
    response = requests.get(f"{BASE_URL}/get_config")
    updated_rules = response.json()
    pprint(updated_rules)

    # 4. 验证规则数量
    old_count = len(current_rules.get("rules", []))
    new_count = len(updated_rules.get("rules", []))
    print(f"\n原有规则数量: {old_count}")
    print(f"新规则数量: {new_count}")
    print(f"是否完全覆盖: {'是' if new_count != old_count else '否'}")

if __name__ == "__main__":
    print("测试规则完全覆盖功能...")
    print("=" * 50)
    try:
        test_rules_override()
        print("\n✅ 测试完成!")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
