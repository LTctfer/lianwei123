#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT智能预警引擎
支持动态配置更新和预警发送
"""

import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt
import logging
from queue import Queue, Empty
import toml
import os


class SimpleAlarmEngine:
    """简化的预警引擎"""

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = self._load_config()
        self.stats = {'config_version': 1}

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return toml.load(f)
            return {}
        except Exception:
            return {}

    def _save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                toml.dump(self.config, f)
            self.stats['config_version'] += 1
        except Exception:
            pass

    def update_config(self, updates: Dict[str, Any], persist: bool = True) -> Dict[str, Any]:
        """更新配置"""
        try:
            for key, value in updates.items():
                keys = key.split('.')
                current = self.config
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value

            if persist:
                self._save_config()

            return {"success": True, "version": self.stats['config_version']}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def process_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理数据并生成预警"""
        try:
            # 简单的预警逻辑
            alarm_rule = self.config.get('alarm_rule', {})
            if not alarm_rule.get('enabled'):
                return None

            # 检查单属性规则
            single_rules = self.config.get('device_alarm_config', {}).get('singlePropertyRule', [])
            for rule in single_rules:
                prop = rule.get('property')
                if prop in data:
                    value = data[prop]
                    low_val = rule.get('lowValue', 0)
                    high_val = rule.get('highValue', 100)
                    expr1 = rule.get('expression1', 'gt')
                    expr2 = rule.get('expression2', 'gt')

                    # 简单的表达式评估
                    triggered = False
                    if expr1 == 'lt' and value < low_val:
                        triggered = True
                    elif expr1 == 'gt' and value > high_val:
                        triggered = True

                    if triggered:
                        return {
                            'alarmId': alarm_rule.get('alarmRuleId', 'ALARM_001'),
                            'alarmTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'alarmLevel': alarm_rule.get('alarmLevel', 'HIGH'),
                            'data': data
                        }

            return None
        except Exception:
            return None

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats


class MQTTSmartAlarm:
    """MQTT智能预警引擎"""

    def __init__(self, device_id: str = "device_001", broker_host: str = "broker.emqx.io", broker_port: int = 1883):
        self.device_id = device_id
        self.broker_host = broker_host
        self.broker_port = broker_port

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # MQTT主题
        self.command_topic = f"command/{device_id}"
        self.alarm_topic = f"RTO/warning_data/{device_id}"
        self.status_topic = f"smart_alarm/status/feedback/{device_id}"

        # 预警引擎
        self.alarm_engine = SimpleAlarmEngine("config.toml")

        # MQTT客户端
        self.client = mqtt.Client(
            client_id=f"smart_alarm_{device_id}_{int(time.time())}",
            protocol=mqtt.MQTTv311
        )

        # 状态管理
        self.connected = False
        self.lock = threading.Lock()
        self.alarm_queue = Queue()
        self.sender_thread = None
        self.running = False

        # 简化统计
        self.stats = {
            'successful_updates': 0,
            'failed_updates': 0,
            'processed_data': 0,
            'generated_alarms': 0,
            'sent_alarms': 0
        }

        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """设置MQTT回调函数"""
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            self.logger.info(f"🔗 成功连接到MQTT代理: {self.broker_host}:{self.broker_port}")
            with self.lock:
                self.connected = True

            client.subscribe(self.command_topic, qos=1)
            self.logger.info(f"📡 已订阅命令主题: {self.command_topic}")

            self._publish_status("online", f"MQTT智能预警引擎已上线 - 设备ID: {self.device_id}")
        else:
            self.logger.error(f"❌ MQTT连接失败，错误码: {rc}")
            with self.lock:
                self.connected = False

    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        self.logger.warning(f"⚠️ MQTT连接断开，错误码: {rc}")
        with self.lock:
            self.connected = False
    
    def _on_message(self, client, userdata, message):
        """消息接收回调 - 处理ALARM_RULE命令"""
        try:
            command_data = json.loads(message.payload.decode('utf-8'))
            self.logger.info(f"📥 收到命令消息: {message.topic}")

            if not self._validate_alarm_rule_command(command_data):
                self._publish_status("error", "命令格式无效")
                self.stats['failed_updates'] += 1
                return

            updates = self._convert_alarm_rule_to_config(command_data.get("data", {}))

            self.logger.info(f"🔧 应用预警规则配置:")
            for key, value in updates.items():
                self.logger.info(f"   {key}: {value}")

            result = self.alarm_engine.update_config(updates, True)

            if result["success"]:
                self._publish_status("success", "配置更新成功")
                self.stats['successful_updates'] += 1
                self.logger.info(f"✅ 预警规则配置成功 (版本: {result['version']})")
            else:
                self._publish_status("error", result['message'])
                self.stats['failed_updates'] += 1
                self.logger.error(f"❌ 预警规则配置失败: {result['message']}")

        except Exception as e:
            self.logger.error(f"❌ 处理命令消息时发生错误: {e}")
            self._publish_status("error", f"处理错误: {str(e)}")
            self.stats['failed_updates'] += 1
    
    def _validate_alarm_rule_command(self, command_data: Dict[str, Any]) -> bool:
        """验证ALARM_RULE命令格式"""
        return (command_data.get("commandType") == "ALARM_RULE" and
                "data" in command_data)

    def _convert_alarm_rule_to_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """将ALARM_RULE命令数据转换为配置更新格式"""
        updates = {}

        # 基础预警规则字段
        field_mapping = {
            'alarmRuleId': 'alarm_rule.alarmRuleId',
            'alarmRuleName': 'alarm_rule.alarmRuleName',
            'alarmClazz': 'alarm_rule.alarmClazz',
            'alarmLevel': 'alarm_rule.alarmLevel',
            'enabled': 'alarm_rule.enabled',
            'startTime': 'alarm_rule.startTime',
            'endTime': 'alarm_rule.endTime'
        }

        for src_key, dst_key in field_mapping.items():
            if src_key in data:
                updates[dst_key] = data[src_key]

        # 处理config字段中的规则配置
        if 'config' in data and data['config']:
            try:
                config_obj = json.loads(data['config']) if isinstance(data['config'], str) else data['config']
                alarm_clazz = data.get('alarmClazz', 'DEVICE_ALARM')
                config_prefix = 'device_alarm_config' if alarm_clazz == 'DEVICE_ALARM' else 'enterprise_alarm_config'

                # 转换规则配置
                if 'singlePropertyRule' in config_obj:
                    updates[f'{config_prefix}.singlePropertyRule'] = config_obj['singlePropertyRule']
                if 'doublePropertyRule' in config_obj:
                    updates[f'{config_prefix}.doublePropertyRule'] = config_obj['doublePropertyRule']
                if 'frequency' in config_obj:
                    updates[f'{config_prefix}.frequency'] = config_obj['frequency']

            except (json.JSONDecodeError, TypeError):
                self.logger.warning("⚠️ config字段解析失败，跳过规则配置")

        return updates
    
    def _publish_status(self, status: str, message: str) -> bool:
        """发布状态消息"""
        try:
            status_message = {
                "device_id": self.device_id,
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "message": message
            }

            payload = json.dumps(status_message, ensure_ascii=False)
            result = self.client.publish(self.status_topic, payload, qos=1)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            self.logger.error(f"❌ 发布状态消息时发生错误: {e}")
            return False
    
    def _publish_alarm(self, alarm: Dict[str, Any]) -> bool:
        """发布预警消息"""
        try:
            alarm_message = {
                "alarmId": alarm.get("alarmId"),
                "alarmTime": alarm.get("alarmTime"),
                "data": alarm.get("data", {})
            }

            payload = json.dumps(alarm_message, ensure_ascii=False)
            result = self.client.publish(self.alarm_topic, payload, qos=1)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"🚨 预警消息已发布: {alarm.get('alarmId')} ({alarm.get('alarmLevel')})")
                self.stats['sent_alarms'] += 1
                return True
            return False
        except Exception as e:
            self.logger.error(f"❌ 发布预警消息时发生错误: {e}")
            return False
    
    def _alarm_sender_worker(self):
        """预警发送工作线程"""
        self.logger.info("🔄 预警发送线程已启动")

        while self.running:
            try:
                alarm = self.alarm_queue.get(timeout=1)
                if self.connected:
                    self._publish_alarm(alarm)
                self.alarm_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"❌ 预警发送线程错误: {e}")

        self.logger.info("🔄 预警发送线程已停止")
    
    def connect(self) -> bool:
        """连接到MQTT代理"""
        try:
            self.logger.info(f"🔌 正在连接到MQTT代理: {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            # 等待连接建立
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            return self.connected
        except Exception as e:
            self.logger.error(f"❌ MQTT连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开MQTT连接"""
        try:
            self.running = False
            if self.sender_thread and self.sender_thread.is_alive():
                self.sender_thread.join(timeout=2)

            if self.connected:
                self._publish_status("offline", "MQTT智能预警引擎即将下线")
                time.sleep(0.5)

            self.client.loop_stop()
            self.client.disconnect()

            with self.lock:
                self.connected = False

            self.logger.info("🔌 MQTT连接已断开")
        except Exception as e:
            self.logger.error(f"❌ 断开MQTT连接时发生错误: {e}")
    
    def start_sender(self):
        """启动预警发送器"""
        if not self.running:
            self.running = True
            self.sender_thread = threading.Thread(target=self._alarm_sender_worker, daemon=True)
            self.sender_thread.start()
            self.logger.info("✅ 预警发送器已启动")
    
    def process_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理数据并生成预警"""
        try:
            self.stats['processed_data'] += 1
            alarm = self.alarm_engine.process_data(data)
            
            if alarm:
                self.stats['generated_alarms'] += 1
                self.logger.info(f"⚠️ 生成预警: {alarm.get('alarmId')} - {alarm.get('alarmLevel')}")
                self.alarm_queue.put(alarm)
                return alarm
            
            return None
        except Exception as e:
            self.logger.error(f"❌ 处理数据时发生错误: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "connected": self.connected,
            "device_id": self.device_id
        }


class MQTTBackendSimulator:
    """MQTT后端模拟器"""

    def __init__(self, device_id: str = "device_001", broker_host: str = "broker.emqx.io", broker_port: int = 1883):
        self.device_id = device_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.logger = logging.getLogger("BackendSimulator")

        self.command_topic = f"command/{device_id}"
        self.alarm_topic = f"RTO/warning_data/{device_id}"
        self.status_topic = f"smart_alarm/status/feedback/{device_id}"

        self.client = mqtt.Client(
            client_id=f"backend_simulator_{int(time.time())}",
            protocol=mqtt.MQTTv311
        )

        self.connected = False
        self.received_alarms = []
        self.received_status = []

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            self.logger.info(f"🔗 后端模拟器连接成功")
            self.connected = True
            client.subscribe(self.alarm_topic, qos=1)
            client.subscribe(self.status_topic, qos=1)
        else:
            self.connected = False

    def _on_message(self, client, userdata, message):
        """消息接收回调"""
        try:
            data = json.loads(message.payload.decode('utf-8'))
            timestamp = datetime.now().strftime('%H:%M:%S')

            if message.topic == self.alarm_topic:
                self.received_alarms.append(data)
                self.logger.info(f"🚨 [{timestamp}] 收到预警: {data.get('alarm_id')} ({data.get('alarm_level')})")
            elif message.topic == self.status_topic:
                self.received_status.append(data)
                self.logger.info(f"📊 [{timestamp}] 收到状态: {data.get('status')} - {data.get('message')}")
        except Exception as e:
            self.logger.error(f"❌ 处理消息时发生错误: {e}")

    def connect(self) -> bool:
        """连接到MQTT代理"""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()

            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            return self.connected
        except Exception as e:
            self.logger.error(f"❌ 连接失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
        except Exception as e:
            self.logger.error(f"❌ 断开连接时发生错误: {e}")

    def send_alarm_rule_command(self, alarm_rule_data: Dict[str, Any]) -> bool:
        """发送ALARM_RULE命令"""
        if not self.connected:
            return False

        command_message = {
            "commandType": "ALARM_RULE",
            "data": alarm_rule_data
        }

        payload = json.dumps(command_message, ensure_ascii=False)
        result = self.client.publish(self.command_topic, payload, qos=1)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            self.logger.info(f"📤 ALARM_RULE命令已发送")
            return True
        return False


if __name__ == "__main__":
    # 简单的使用示例
    device_id = "device_001"
    smart_alarm = MQTTSmartAlarm(device_id=device_id)

    if smart_alarm.connect():
        smart_alarm.start_sender()
        print("✅ MQTT智能预警引擎已启动")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("⚠️ 正在关闭...")
        finally:
            smart_alarm.disconnect()
    else:
        print("❌ 连接失败")
