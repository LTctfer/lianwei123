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
import struct
from datetime import datetime
from collections import deque
from typing import Dict, Any, List, Optional
from pymodbus.client import ModbusSerialClient


# ======================================================
# 配置参数
# ======================================================

# 远程API接口地址
REMOTE_API_URL = "http://127.0.0.1:8023/intelligence-center/data-import/importAlarmData"
REAL_DATA_API_URL = "http://127.0.0.1:8023/intelligence-center/data-import/importRealData"

# 本地配置文件路径
CONFIG_FILE = "config.json"

# PLC Modbus 配置
PLC_SLAVE_ID = 1
PLC_PORT = "/dev/ttyS8"  # Windows系统使用COM端口，Linux系统使用/dev/ttyS8
PLC_BAUDRATE = 9600
PLC_PARITY = "N"
PLC_STOPBITS = 1
PLC_BYTESIZE = 8
PLC_TIMEOUT = 1
PLC_INTERVAL = 60  # 每次读取间隔秒数

# 设备信息
DEVICE_NUM = "255122420258d523"
DEVICE_MN = "001"

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

def registers_to_float(registers, byteorder="big"):
    """将两个寄存器转换为浮点数"""
    try:
        raw = (registers[0] << 16) + registers[1]
        return struct.unpack(">f" if byteorder == "big" else "<f",
                             raw.to_bytes(4, byteorder=byteorder))[0]
    except Exception:
        return None

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
            
            # 当symbol="AND"且有两个边界值时，表示范围检测：超出范围则触发预警
            # 例如：lowValue=0, expression1="le", highValue=30, expression2="le"
            # 表示正常范围为 (0, 30]，即 v <= 0 OR v > 30 时触发预警
            if symbol == "AND" and low is not None and high is not None:
                # 范围外检测：小于等于下界 OR 大于上界
                violate |= _cmp(v, e1, low) or not _cmp(v, e2, high)
            elif symbol == "AND":
                # 普通 AND 逻辑
                violate |= _cmp(v, e1, low) and _cmp(v, e2, high)
            else:
                # OR 逻辑
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
# PLC数据读取器
# ======================================================

class ModbusDataReader:
    """从PLC读取实时数据"""
    
    def __init__(self):
        self.client = ModbusSerialClient(
            method="rtu",
            port=PLC_PORT,
            baudrate=PLC_BAUDRATE,
            parity=PLC_PARITY,
            stopbits=PLC_STOPBITS,
            bytesize=PLC_BYTESIZE,
            timeout=PLC_TIMEOUT
        )
        self.connected = False
        logging.info(f"初始化Modbus客户端: {PLC_PORT}")
    
    def connect(self) -> bool:
        """连接到PLC设备"""
        try:
            if self.client.connect():
                self.connected = True
                logging.info("✅ 成功连接到PLC设备")
                return True
            else:
                logging.error("❌ 无法连接到PLC设备")
                return False
        except Exception as e:
            logging.error(f"❌ 连接PLC失败: {e}")
            return False
    
    def read(self) -> Dict[str, Any]:
        """读取PLC数据"""
        if not self.connected:
            logging.warning("PLC未连接，尝试重新连接...")
            if not self.connect():
                return {}
        
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 读取风机启停状态 (线圈)
            coils = self.client.read_coils(0x0000, 1, slave=PLC_SLAVE_ID)
            fan_status = 1 if (not coils.isError() and coils.bits[0]) else 0
            
            # 定义读取浮点数的内部函数
            def read_float(addr):
                r = self.client.read_holding_registers(addr, 2, slave=PLC_SLAVE_ID)
                return registers_to_float(r.registers) if not r.isError() else None
            
            # 分别读取寄存器
            t1 = read_float(0x0000)  # 加热室平均温度
            t2 = read_float(0x0002)  # RTO出口温度
            t3 = read_float(0x0004)  # RTO进口温度
            p1 = read_float(0x0006)  # RTO出口压力
            
            # 构造数据字典
            data = {
                "fan_status": fan_status,
                "t1": round(t1, 2) if t1 is not None else None,
                "t2": round(t2, 2) if t2 is not None else None,
                "t3": round(t3, 2) if t3 is not None else None,
                "p1": round(p1, 2) if p1 is not None else None,
                "workStatus": "qx1",  # 工况状态，可根据实际情况从PLC读取
                "timestamp": now
            }
            
            logging.info(
                f"📊 读取PLC数据: fan_status={fan_status}, "
                f"t1={data['t1']}℃, t2={data['t2']}℃, "
                f"t3={data['t3']}℃, p1={data['p1']}"
            )
            
            return data
            
        except Exception as e:
            logging.error(f"❌ 读取PLC数据失败: {e}")
            self.connected = False
            return {}
    
    def close(self):
        """关闭连接"""
        try:
            if self.connected:
                self.client.close()
                self.connected = False
                logging.info("🔌 已断开PLC连接")
        except Exception as e:
            logging.error(f"关闭连接异常: {e}")


# ======================================================
# 实时数据上传
# ======================================================

def upload_real_data(data: Dict[str, Any]):
    """上传实时数据到远程接口"""
    try:
        # 获取数据值
        fan_status = data.get("fan_status")
        t1 = data.get("t1")
        t2 = data.get("t2")
        t3 = data.get("t3")
        p1 = data.get("p1")
        now = data.get("timestamp")
        
        # 构造上传数据格式
        data_json = {
            "deviceNum": DEVICE_NUM,
            "data_time": now,
            "MN": DEVICE_MN,
            "data_internal": "1m",
            "data": {
                "fan_status": fan_status,
                "t1": round(t1, 2) if t1 is not None else None,
                "t2": round(t2, 2) if t2 is not None else None,
                "t3": round(t3, 2) if t3 is not None else None,
                "p1": round(p1, 2) if p1 is not None else None
            }
        }
        
        logging.info(f"📤 上传实时数据...")
        logging.debug(f"上传内容: {json.dumps(data_json, ensure_ascii=False)}")
        
        # 发送POST请求
        response = requests.post(
            REAL_DATA_API_URL,
            json=data_json,
            headers={"Content-Type": "application/json"},
            timeout=3
        )
        
        if response.status_code == 200:
            logging.info(f"✅ 实时数据上传成功！响应: {response.text[:200]}")
        else:
            logging.warning(
                f"⚠️ 实时数据上传失败！"
                f"状态码: {response.status_code}, "
                f"响应: {response.text[:200]}"
            )
    except requests.exceptions.Timeout:
        logging.error("❌ 实时数据上传超时")
    except requests.exceptions.ConnectionError:
        logging.error(f"❌ 无法连接到实时数据API: {REAL_DATA_API_URL}")
    except Exception as e:
        logging.error(f"❌ 实时数据上传异常: {e}")


# ======================================================
# 程序入口
# ======================================================

def main():
    """主程序"""
    # 创建预警数据上报引擎
    reporter = AlarmDataReporter()
    reporter.start()
    
    # 创建PLC数据读取器
    reader = ModbusDataReader()
    
    # 连接到PLC
    if not reader.connect():
        logging.error("无法启动程序，PLC连接失败")
        return
    
    logging.info("=" * 60)
    logging.info("开始读取PLC数据并执行预警检测...")
    logging.info("按 Ctrl+C 停止程序")
    logging.info("=" * 60)
    
    try:
        while True:
            # 从PLC读取数据
            data = reader.read()
            
            if data:
                # 上传实时数据
                upload_real_data(data)
                
                # 处理数据（执行规则检查）
                reporter.process(data)
            else:
                logging.warning("未能读取到有效数据")
            
            # 等待一段时间
            time.sleep(PLC_INTERVAL)
            
    except KeyboardInterrupt:
        logging.info("\n\n收到停止信号，正在关闭...")
        reader.close()
        reporter.stop()
        logging.info("程序已退出")


if __name__ == "__main__":
    main()
