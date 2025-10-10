#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Alarm Engine (JSON version)
---------------------------------
算法模块：定期从后端同步规则，根据配置自动生成预警数据
兼容 backend_api.py (JSON 存储版本)
"""

import requests
import time
import threading
import logging
import json
import random
import os
from datetime import datetime
from collections import deque
from typing import Dict, Any, List, Optional


# ======================================================
# 工具函数
# ======================================================

def _cmp(a, op, b):
    """支持 lt/le/eq/ge/gt 与符号比较"""
    try:
        a, b = float(a), float(b)
    except Exception:
        return False
    op = str(op).lower().strip()
    return {
        "lt": a < b, "<": a < b,
        "le": a <= b, "<=": a <= b,
        "eq": a == b, "==": a == b,
        "ge": a >= b, ">=": a >= b,
        "gt": a > b, ">": a > b
    }.get(op, False)


# ======================================================
# 频率控制逻辑
# ======================================================

class Frequency:
    """单规则频率控制（累计 or 连续）"""
    def __init__(self):
        self.violations = deque()
        self.streak = 0

    def trigger(self, ok: bool, freq_cfg: Dict[str, Any]) -> bool:
        enabled = freq_cfg.get("enabled", 0)
        if not enabled:
            return ok

        has_acc = int(freq_cfg.get("hasAccumulate", 0))
        if has_acc:
            # 累计次数触发
            now = time.time()
            if ok:
                self.violations.append(now)
            cutoff = now - freq_cfg.get("accumulateTimeRange", 60)
            while self.violations and self.violations[0] < cutoff:
                self.violations.popleft()
            return len(self.violations) >= freq_cfg.get("accumulateCount", 1)
        else:
            # 连续触发
            if ok:
                self.streak += 1
            else:
                self.streak = 0
            return self.streak >= freq_cfg.get("continuousCount", 1)


# ======================================================
# 单条规则执行器
# ======================================================

class RuleRunner:
    def __init__(self, rule: Dict[str, Any]):
        self.rule = rule
        self.freq = Frequency()
        self.last_fire = 0.0

    def _json_cfg(self):
        """确保 config 为字典"""
        cfg = self.rule.get("config", {})
        if isinstance(cfg, str):
            try:
                return json.loads(cfg)
            except Exception:
                return {}
        return cfg

    def _cooldown_ok(self) -> bool:
        """冷却间隔控制 (小时)"""
        gap = float(self.rule.get("alarmInternal", 0))
        return time.time() - self.last_fire >= gap * 3600

    def _check_single(self, cfg, data):
        violate = False
        for s in cfg.get("singlePropertyRule", []):
            prop = s.get("property")
            if prop not in data:
                continue
            v = data[prop]
            low, high = s.get("lowValue"), s.get("highValue")
            e1, e2 = s.get("expression1"), s.get("expression2")
            symbol = (s.get("symbol") or "OR").upper()
            if symbol == "AND":
                violate |= _cmp(v, e1, low) and _cmp(v, e2, high)
            else:
                violate |= _cmp(v, e1, low) or _cmp(v, e2, high)
        return violate

    def _check_double(self, cfg, data):
        violate = False
        for d in cfg.get("doublePropertyRule", []):
            lp, rp = d.get("leftProperty"), d.get("rightProperty")
            if lp in data and rp in data:
                violate |= _cmp(data[lp], d.get("expression"), data[rp])
        return violate

    def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """执行单条规则判断"""
        if not self.rule.get("enabled", 0):
            return None

        cfg = self._json_cfg()
        clazz = self.rule.get("alarmClazz", "")
        violate = False

        # 判断单属性与双属性
        violate |= self._check_single(cfg, data)
        violate |= self._check_double(cfg, data)

        # 工况状态过滤（仅企业预警有效）
        if clazz == "ENTERPRISE_ALARM" and cfg.get("workStatus"):
            if data.get("workStatus") not in cfg["workStatus"]:
                violate = False

        # 频率控制
        fired = self.freq.trigger(violate, cfg.get("frequency", {}))

        # 冷却间隔
        if fired and self._cooldown_ok():
            self.last_fire = time.time()
            alarm_data = {
                "alarmId": self.rule.get("alarmRuleId"),
                "alarmTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": {k: data[k] for k in self.rule.get("showProperties", []) if k in data}
            }
            return alarm_data
        return None


# ======================================================
# 主引擎
# ======================================================

class SmartAlarmEngine:
    def __init__(self, backend_url: str, config_path: str = None):
        self.backend = backend_url.rstrip("/")
        self.rules: List[RuleRunner] = []
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "config.json")
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    def sync_rules(self):
        """从本地配置文件加载规则"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    rules = cfg.get("rules", [])
                    self.rules = [RuleRunner(r) for r in rules]
                    logging.info(f"✅ 从本地加载规则 {len(self.rules)} 条成功")
            else:
                logging.warning(f"配置文件 {self.config_path} 不存在")
        except Exception as e:
            logging.error(f"加载规则异常: {e}")

    def _sync_loop(self):
        """后台定时同步"""
        while True:
            self.sync_rules()
            time.sleep(30)

    def start(self):
        """启动引擎"""
        logging.info("🚀 启动 SmartAlarmEngine (JSON)")
        self.sync_rules()
        threading.Thread(target=self._sync_loop, daemon=True).start()

    def process(self, data: Dict[str, Any]):
        """逐条处理规则"""
        for runner in self.rules:
            alarm = runner.process(data)
            if alarm:
                logging.info(f"⚠️ 触发预警: {alarm}")
                self.push_alarm(alarm)

    def push_alarm(self, alarm: Dict[str, Any]):
        """上报预警"""
        try:
            res = requests.post(f"{self.backend}/push_alarm", json=alarm, timeout=5)
            if res.status_code == 200:
                logging.info("🚨 预警上报成功")
            else:
                logging.warning(f"⚠️ 上报失败 HTTP {res.status_code}")
        except Exception as e:
            logging.error(f"上报异常: {e}")


# ======================================================
# 程序入口
# ======================================================

if __name__ == "__main__":
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "config.json")
    
    backend_url = "http://127.0.0.1:8000"
    engine = SmartAlarmEngine(backend_url, config_path)
    engine.start()

    # 模拟实时数据流
    print(f"开始模拟数据生成... (配置文件路径: {config_path})")
    while True:
        # 模拟温度数据（正常、偏高、偏低）
        temp = random.choice([
            random.uniform(30, 80),  # 正常温度
            random.uniform(91, 100),  # 高温
            random.uniform(10, 19)    # 低温
        ])
        
        # 模拟传感器数据
        t1 = random.choice([
            random.uniform(2, 8),     # 正常范围
            random.uniform(0, 0.9),   # 异常低值
            random.uniform(11, 15)    # 异常高值
        ])
        
        # 模拟工况状态
        data = {
            "t1": t1,
            "t2": random.uniform(0, 10),
            "temperature": temp,
            "workStatus": random.choice(["spray", "unused", "idle"]),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print(f"生成模拟数据: {data}")
        engine.process(data)
        time.sleep(2)
