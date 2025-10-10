# http_smart_alarm.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time, json, os, logging, threading, requests, toml
from datetime import datetime
from typing import Dict, Any, Optional, Deque, List
from collections import deque

def _cmp(a, op: str, b) -> bool:
    op = (op or "").lower()
    try:
        if op in ("lt", "<"):  return a < b
        if op in ("le", "<="): return a <= b
        if op in ("eq", "=="): return a == b
        if op in ("ge", ">="): return a >= b
        if op in ("gt", ">"):  return a > b
    except Exception:
        return False
    return False

class FrequencyState:
    def __init__(self):
        self.violations: Deque[float] = deque()
        self.streak: int = 0

    def register(self, is_violate: bool, window_seconds: int, need_count: int, accumulate: bool) -> bool:
        now = time.time()
        if accumulate:
            if is_violate:
                self.violations.append(now)
            cutoff = now - window_seconds
            while self.violations and self.violations[0] < cutoff:
                self.violations.popleft()
            return len(self.violations) >= need_count
        else:
            if is_violate:
                self.streak += 1
            else:
                self.streak = 0
            return self.streak >= need_count

class RuleRuntime:
    """每条规则的运行态：频率状态 + 冷却时间"""
    def __init__(self):
        self.freq = FrequencyState()
        self.last_fire_at: Optional[float] = None

class SmartAlarmEngine:
    def __init__(self, config_path_json="config.json", config_path_toml="config.toml"):
        self.config_json = config_path_json
        self.config_toml = config_path_toml
        self.logger = logging.getLogger("SmartAlarmEngine")
        self.runtime: Dict[str, RuleRuntime] = {}  # 按 alarmRuleId
        self.config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_json):
            with open(self.config_json, "r", encoding="utf-8") as f:
                return json.load(f)
        if os.path.exists(self.config_toml):
            with open(self.config_toml, "r", encoding="utf-8") as f:
                return toml.load(f)
        return {}

    def reload_config(self, new_cfg: Dict[str, Any]):
        self.config = new_cfg
        self.runtime.clear()

    # ---------- 规则评估 ----------
    def _within_time_window(self, start: str, end: str) -> bool:
        try:
            now = datetime.now().time()
            s_hour, s_min = map(int, start.split(":"))
            e_hour, e_min = map(int, end.split(":"))
            s = now.replace(hour=s_hour, minute=s_min, second=0, microsecond=0)
            e = now.replace(hour=e_hour, minute=e_min, second=0, microsecond=0)
            return s <= now <= e if s <= e else (now >= s or now <= e)
        except Exception:
            return True

    def _eval_single_rule(self, rule: Dict[str, Any], data: Dict[str, Any]) -> Optional[bool]:
        prop = rule.get("property")
        if prop not in data:
            return None
        val = data[prop]
        low_v  = rule.get("lowValue")
        high_v = rule.get("highValue")
        e1 = rule.get("expression1", "lt")
        e2 = rule.get("expression2", "gt")  # 虽然表述列举 lt/le/eq，这里兼容所有比较符
        left_ok  = _cmp(val, e1, low_v)  if low_v  is not None else False
        right_ok = _cmp(val, e2, high_v) if high_v is not None else False
        symbol = (rule.get("symbol") or "OR").upper()
        return (left_ok and right_ok) if symbol == "AND" else (left_ok or right_ok)

    def _eval_double_rule(self, rule: Dict[str, Any], data: Dict[str, Any]) -> Optional[bool]:
        lp, rp = rule.get("leftProperty"), rule.get("rightProperty")
        if lp not in data or rp not in data:
            return None
        return _cmp(data[lp], rule.get("expression", "lt"), data[rp])

    def _hit_once_device(self, cfg: Dict[str, Any], data: Dict[str, Any]) -> bool:
        singles: List[Dict[str, Any]] = cfg.get("singlePropertyRule") or []
        doubles: List[Dict[str, Any]] = cfg.get("doublePropertyRule") or []
        for r in singles:
            res = self._eval_single_rule(r, data)
            if res is True:
                return True
        for r in doubles:
            res = self._eval_double_rule(r, data)
            if res is True:
                return True
        return False

    def _hit_once_enterprise(self, cfg: Dict[str, Any], data: Dict[str, Any]) -> bool:
        # workStatus 过滤：若配置了 workStatus，且数据含 workStatus 字段，则需匹配
        ws = cfg.get("workStatus")
        if ws and isinstance(ws, list):
            dws = data.get("workStatus")
            if dws is not None and dws not in ws:
                return False
        singles: List[Dict[str, Any]] = cfg.get("singlePropertyRule") or []
        for r in singles:
            res = self._eval_single_rule(r, data)
            if res is True:
                return True
        return False

    def _frequency_fire(self, rule_id: str, freq_cfg: Dict[str, Any], violate_now: bool) -> bool:
        rt = self.runtime.setdefault(rule_id, RuleRuntime())
        enabled = int(freq_cfg.get("enabled", 0)) == 1
        if not enabled:
            return violate_now
        accumulate = int(freq_cfg.get("hasAccumulate", 0)) == 1
        if accumulate:
            need = int(freq_cfg.get("accumulateCount", 1))
            window = int(freq_cfg.get("accumulateTimeRange", 60))
        else:
            need = int(freq_cfg.get("continuousCount", 1))
            window = 0
        return rt.freq.register(violate_now, window, need, accumulate)

    def _cooldown_pass(self, rule_id: str, alarm_internal_hours: int) -> bool:
        rt = self.runtime.setdefault(rule_id, RuleRuntime())
        cool_s = max(0, int(alarm_internal_hours)) * 3600
        now = time.time()
        if rt.last_fire_at is None or (now - rt.last_fire_at) >= cool_s:
            rt.last_fire_at = now
            return True
        return False

    def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """评估当前配置（单条规则对象），命中时返回报警包"""
        cfg = self.config or {}
        if not cfg or not int(cfg.get("enabled", 0)) == 1:
            return None

        rule_id = cfg.get("alarmRuleId", "ALARM_RULE")
        start, end = cfg.get("startTime", "00:00"), cfg.get("endTime", "23:59")
        if not self._within_time_window(start, end):
            return None

        alarm_clazz = (cfg.get("alarmClazz") or "").upper()
        rule_cfg = cfg.get("config") or {}

        if alarm_clazz == "ENTERPRISE_ALARM":
            violate = self._hit_once_enterprise(rule_cfg, data)
        else:  # 默认按 DEVICE_ALARM 处理
            violate = self._hit_once_device(rule_cfg, data)

        fired = self._frequency_fire(rule_id, rule_cfg.get("frequency", {}), violate)
        if not fired:
            return None

        # 冷却（alarmInternal 小时）
        if not self._cooldown_pass(rule_id, int(cfg.get("alarmInternal", 0))):
            return None

        # 组装上报包（允许包含更多元信息，后端只强校验 alarmId/alarmTime/data）
        return {
            "alarmId": rule_id,
            "alarmTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": data,
            "alarmRuleName": cfg.get("alarmRuleName"),
            "alarmClazz": alarm_clazz,
            "alarmType": cfg.get("alarmType"),
            "alarmLevel": cfg.get("alarmLevel"),
            "showProperties": cfg.get("showProperties"),
            "algorithmType": cfg.get("algorithmType"),
            "calculateWay": cfg.get("calculateWay")
        }

class HttpSmartAlarm:
    def __init__(self, backend_url: str, config_json="config.json", config_toml="config.toml"):
        self.backend_url = backend_url.rstrip("/")
        self.engine = SmartAlarmEngine(config_json, config_toml)
        self.logger = logging.getLogger("HttpSmartAlarm")
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # --- 配置管理 ---
    def fetch_remote_config(self):
        try:
            r = requests.get(f"{self.backend_url}/get_config", timeout=5)
            if r.status_code == 200:
                cfg = r.json()
                with open("config.json", "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                self.engine.reload_config(cfg)
                self.logger.info("✅ 配置已从后端加载")
            else:
                self.logger.warning(f"⚠️ 拉取配置失败：{r.status_code}: {r.text}")
        except Exception as e:
            self.logger.error(f"❌ 拉取配置异常: {e}")

    def update_config_loop(self, interval=20):
        while True:
            self.fetch_remote_config()
            time.sleep(interval)

    # --- 数据处理 ---
    def process_data(self, data: Dict[str, Any]):
        alarm = self.engine.process(data)
        if alarm:
            self.logger.info(f"⚠️ 预警触发: {alarm}")
            self.send_alarm(alarm)

    # --- 上报 ---
    def send_alarm(self, alarm: Dict[str, Any]):
        try:
            url = f"{self.backend_url}/push_alarm"
            r = requests.post(url, json=alarm, timeout=5)
            if r.status_code == 200:
                self.logger.info("🚨 预警数据已上报成功")
            else:
                self.logger.warning(f"⚠️ 上报失败({r.status_code}): {r.text}")
        except Exception as e:
            self.logger.error(f"❌ 上报预警异常: {e}")

    def start(self):
        self.logger.info("🚀 启动HTTP智能预警引擎...")
        self.fetch_remote_config()
        threading.Thread(target=self.update_config_loop, daemon=True).start()

if __name__ == "__main__":
    backend_url = "http://127.0.0.1:8000"
    alarm = HttpSmartAlarm(backend_url)
    alarm.start()

    # 模拟数据流
    import random
    while True:
        sample = {
            "t1": random.uniform(0, 12),
            "t2": random.uniform(5, 15),
            "workStatus": random.choice(["spray", "unused", "idle"])
        }
        alarm.process_data(sample)
        time.sleep(2)
