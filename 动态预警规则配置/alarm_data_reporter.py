#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预警数据上报程序
---------------------------------
功能：
1. 加载本地配置文件（config.json）
2. 根据规则配置自动生成预警数据
3. 调用远程API接口上报预警数据
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
# 配置参数
# ======================================================

# 远程API接口地址
REMOTE_API_URL = "http://192.168.0.137:8023/intelligence-center/data-import/importAlarmData"

# 本地配置文件路径
CONFIG_FILE = "config.json"

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("alarm_reporter.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)


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

    def _in_time_range(self) -> bool:
        """检查是否在规则的有效时间范围内"""
        start_time = self.rule.get("startTime")
        end_time = self.rule.get("endTime")
        
        if not start_time or not end_time:
            return True
        
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            
            # 处理跨天情况
            if start_time <= end_time:
                return start_time <= current_time <= end_time
            else:
                return current_time >= start_time or current_time <= end_time
        except Exception as e:
            logging.warning(f"时间范围检查失败: {e}")
            return True

    def _check_single(self, cfg, data):
        """检查单属性规则"""
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
        """检查双属性规则"""
        violate = False
        for d in cfg.get("doublePropertyRule", []):
            lp, rp = d.get("leftProperty"), d.get("rightProperty")
            if lp in data and rp in data:
                violate |= _cmp(data[lp], d.get("expression"), data[rp])
        return violate

    def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """执行单条规则判断"""
        # 检查规则是否启用
        if not self.rule.get("enabled", 0):
            return None
        
        # 检查时间范围
        if not self._in_time_range():
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
            
            # 构造预警数据（按照指定格式）
            alarm_data = {
                "alarmId": self.rule.get("alarmRuleId"),
                "alarmTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": {
                    k: data[k] 
                    for k in self.rule.get("showProperties", []) 
                    if k in data
                }
            }
            
            # 添加额外的规则信息（便于调试）
            alarm_data["data"]["alarmRuleName"] = self.rule.get("alarmRuleName")
            alarm_data["data"]["alarmLevel"] = self.rule.get("alarmLevel")
            alarm_data["data"]["alarmType"] = self.rule.get("alarmType")
            
            return alarm_data
        return None


# ======================================================
# 主引擎
# ======================================================

class AlarmDataReporter:
    """预警数据上报引擎"""
    
    def __init__(self, config_path: str = None, api_url: str = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), CONFIG_FILE
        )
        self.api_url = api_url or REMOTE_API_URL
        self.rules: List[RuleRunner] = []
        self.running = False
        
        logging.info(f"初始化预警数据上报引擎")
        logging.info(f"配置文件路径: {self.config_path}")
        logging.info(f"远程API地址: {self.api_url}")

    def load_rules(self):
        """从本地配置文件加载规则"""
        try:
            if not os.path.exists(self.config_path):
                logging.error(f"配置文件不存在: {self.config_path}")
                return
            
            with open(self.config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                rules = cfg.get("rules", [])
                self.rules = [RuleRunner(r) for r in rules if r.get("enabled", 0)]
                logging.info(f"✅ 成功加载 {len(self.rules)} 条启用的规则")
                
                # 打印规则摘要
                for idx, runner in enumerate(self.rules, 1):
                    rule = runner.rule
                    logging.info(
                        f"  规则 {idx}: {rule.get('alarmRuleName')} "
                        f"[{rule.get('alarmLevel')}] "
                        f"时间范围: {rule.get('startTime')}-{rule.get('endTime')}"
                    )
        except Exception as e:
            logging.error(f"❌ 加载规则失败: {e}")

    def _sync_loop(self):
        """后台定时同步规则"""
        while self.running:
            time.sleep(60)  # 每60秒重新加载一次规则
            logging.info("重新加载规则配置...")
            self.load_rules()

    def start(self):
        """启动引擎"""
        logging.info("=" * 60)
        logging.info("🚀 启动预警数据上报引擎")
        logging.info("=" * 60)
        
        self.load_rules()
        self.running = True
        
        # 启动后台规则同步线程
        threading.Thread(target=self._sync_loop, daemon=True).start()

    def stop(self):
        """停止引擎"""
        logging.info("停止预警数据上报引擎")
        self.running = False

    def process(self, data: Dict[str, Any]):
        """处理数据，执行规则检查"""
        for runner in self.rules:
            try:
                alarm = runner.process(data)
                if alarm:
                    logging.info(f"⚠️ 触发预警规则: {runner.rule.get('alarmRuleName')}")
                    self.report_alarm(alarm)
            except Exception as e:
                logging.error(f"规则处理异常: {e}")

    def report_alarm(self, alarm: Dict[str, Any]):
        """上报预警数据到远程API"""
        try:
            # 构造符合接口要求的数据格式
            alarm_message = {
                "alarmId": alarm.get("alarmId"),
                "alarmTime": alarm.get("alarmTime"),
                "data": alarm.get("data", {})
            }
            
            logging.info(f"📤 正在上报预警数据...")
            logging.debug(f"上报内容: {json.dumps(alarm_message, ensure_ascii=False)}")
            
            # 发送POST请求
            response = requests.post(
                self.api_url,
                json=alarm_message,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                logging.info(f"✅ 预警数据上报成功！响应: {response.text}")
            else:
                logging.warning(
                    f"⚠️ 预警数据上报失败！"
                    f"状态码: {response.status_code}, "
                    f"响应: {response.text}"
                )
        except requests.exceptions.Timeout:
            logging.error("❌ 预警数据上报超时")
        except requests.exceptions.ConnectionError:
            logging.error(f"❌ 无法连接到远程API: {self.api_url}")
        except Exception as e:
            logging.error(f"❌ 预警数据上报异常: {e}")


# ======================================================
# 数据模拟器（用于测试）
# ======================================================

class DataSimulator:
    """模拟实时数据生成器"""
    
    def __init__(self):
        self.properties = [
            "outlet_temperature",
            "preheat_temperature",
            "combustion_temperature",
            "inlet_temperature",
            "pressure",
            "flow_rate"
        ]
    
    def generate(self) -> Dict[str, Any]:
        """生成模拟数据"""
        data = {}
        
        # 模拟出口温度（有概率触发预警）
        data["outlet_temperature"] = random.choice([
            random.uniform(30, 80),   # 正常范围
            random.uniform(5, 9),     # 低温（触发预警）
            random.uniform(91, 110)   # 高温（触发预警）
        ])
        
        # 模拟预热温度
        data["preheat_temperature"] = random.uniform(200, 400)
        
        # 模拟燃烧温度
        data["combustion_temperature"] = random.choice([
            random.uniform(250, 380),  # 正常范围
            random.uniform(150, 200)   # 低温（可能触发预警）
        ])
        
        # 模拟其他传感器数据
        data["inlet_temperature"] = random.uniform(20, 100)
        data["pressure"] = random.uniform(0.8, 1.2)
        data["flow_rate"] = random.uniform(50, 150)
        
        # 添加工况状态
        data["workStatus"] = random.choice(["running", "idle", "maintenance"])
        
        # 添加时间戳
        data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 添加属性ID（如果配置中使用）
        data["1968595591692861442"] = data["outlet_temperature"]
        data["1968854956819726338"] = data["combustion_temperature"]
        
        return data


# ======================================================
# 程序入口
# ======================================================

def main():
    """主程序"""
    # 创建预警数据上报引擎
    reporter = AlarmDataReporter()
    reporter.start()
    
    # 创建数据模拟器
    simulator = DataSimulator()
    
    logging.info("=" * 60)
    logging.info("开始模拟数据生成和预警检测...")
    logging.info("按 Ctrl+C 停止程序")
    logging.info("=" * 60)
    
    try:
        while True:
            # 生成模拟数据
            data = simulator.generate()
            
            # 打印当前数据
            logging.info(f"📊 生成数据: 出口温度={data['outlet_temperature']:.2f}℃, "
                        f"燃烧温度={data['combustion_temperature']:.2f}℃, "
                        f"工况={data['workStatus']}")
            
            # 处理数据（执行规则检查）
            reporter.process(data)
            
            # 等待一段时间
            time.sleep(5)  # 每5秒生成一次数据
            
    except KeyboardInterrupt:
        logging.info("\n\n收到停止信号，正在关闭...")
        reporter.stop()
        logging.info("程序已退出")


if __name__ == "__main__":
    main()
