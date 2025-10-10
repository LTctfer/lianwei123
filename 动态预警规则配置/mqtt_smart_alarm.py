#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT智能预警引擎 - 完整解决方案
集成配置接收、预警发送、后端模拟和测试功能
使用在线MQTT代理：broker.emqx.io
"""

import json
import os
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
import paho.mqtt.client as mqtt
import logging
from queue import Queue, Empty
from smart_alarm_enhanced import SmartAlarmEngineEnhanced


class MQTTSmartAlarm:
    """MQTT智能预警引擎 - 完整功能"""
    
    def __init__(self, device_id: str = "device_001", broker_host: str = "broker.emqx.io", broker_port: int = 1883):
        # 配置参数
        self.device_id = device_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        
        # 初始化日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # MQTT主题 - 按照智算中心文档要求
        self.command_topic = f"command/{device_id}"
        self.alarm_topic = f"RTO/warning_data/{device_id}"
        self.status_topic = f"smart_alarm/status/feedback/{device_id}"
        
        # 初始化预警引擎
        self.alarm_engine = SmartAlarmEngineEnhanced("config.toml")
        
        # MQTT客户端
        self.client = mqtt.Client(
            client_id=f"smart_alarm_{device_id}_{int(time.time())}",
            protocol=mqtt.MQTTv311
        )
        
        # 连接状态
        self.connected = False
        self.lock = threading.Lock()
        
        # 预警队列
        self.alarm_queue = Queue()
        self.sender_thread = None
        self.running = False
        
        # 统计信息
        self.stats = {
            'received_configs': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'processed_data': 0,
            'generated_alarms': 0,
            'sent_alarms': 0,
            'failed_sends': 0,
            'start_time': datetime.now()
        }
        
        # 设置MQTT回调
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """设置MQTT回调函数"""
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
    
    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            self.logger.info(f"🔗 成功连接到MQTT代理: {self.broker_host}:{self.broker_port}")
            with self.lock:
                self.connected = True
            
            # 订阅命令主题
            result = client.subscribe(self.command_topic, qos=1)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"📡 已订阅命令主题: {self.command_topic}")
            
            # 发送上线状态
            self._publish_status({
                "status": "online",
                "message": f"MQTT智能预警引擎已上线 - 设备ID: {self.device_id}",
                "config_version": self.alarm_engine.get_stats()['config_version']
            })
        else:
            self.logger.error(f"❌ MQTT连接失败，错误码: {rc}")
            with self.lock:
                self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        self.logger.warning(f"⚠️ MQTT连接断开，错误码: {rc}")
        with self.lock:
            self.connected = False
    
    def _on_publish(self, client, userdata, mid):
        """发布成功回调"""
        self.logger.debug(f"📤 消息发布成功，消息ID: {mid}")
    
    def _on_message(self, client, userdata, message):
        """消息接收回调 - 处理ALARM_RULE命令"""
        try:
            payload = message.payload.decode('utf-8')
            self.logger.info(f"📥 收到命令消息: {message.topic}")

            command_data = json.loads(payload)
            self.stats['received_configs'] += 1

            # 验证ALARM_RULE命令格式
            if not self._validate_alarm_rule_command(command_data):
                self._publish_error_status("命令格式无效")
                self.stats['failed_updates'] += 1
                return

            # 转换ALARM_RULE命令为配置更新
            updates = self._convert_alarm_rule_to_config(command_data.get("data", {}))
            persist = True  # 预警规则配置默认持久化

            self.logger.info(f"🔧 应用预警规则配置:")
            for key, value in updates.items():
                self.logger.info(f"   {key}: {value}")

            result = self.alarm_engine.update_config(updates, persist)

            # 发送响应
            if result["success"]:
                self._publish_success_status(result)
                self.stats['successful_updates'] += 1
                self.logger.info(f"✅ 预警规则配置成功 (版本: {result['version']})")
            else:
                self._publish_error_status(result)
                self.stats['failed_updates'] += 1
                self.logger.error(f"❌ 预警规则配置失败: {result['message']}")

        except Exception as e:
            self.logger.error(f"❌ 处理命令消息时发生错误: {e}")
            self._publish_error_status(f"处理错误: {str(e)}")
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
    
    def _publish_status(self, status_data: Dict[str, Any]) -> bool:
        """发布状态消息"""
        try:
            status_message = {
                "device_id": self.device_id,
                "timestamp": datetime.now().isoformat(),
                **status_data
            }
            
            payload = json.dumps(status_message, ensure_ascii=False)
            result = self.client.publish(self.status_topic, payload, qos=1)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            self.logger.error(f"❌ 发布状态消息时发生错误: {e}")
            return False
    
    def _publish_success_status(self, result: Dict[str, Any]):
        """发布成功状态"""
        self._publish_status({
            "status": "success",
            "message": "配置更新成功",
            "config_version": result.get("version"),
            "persist": result.get("persist", True)
        })
    
    def _publish_error_status(self, error_info):
        """发布错误状态"""
        if isinstance(error_info, str):
            status_data = {"status": "error", "message": error_info}
        else:
            status_data = {
                "status": "error",
                "message": error_info.get("message", "未知错误"),
                "error_type": error_info.get("error_type"),
                "error_code": error_info.get("error_code")
            }
        self._publish_status(status_data)
    
    def _publish_alarm(self, alarm: Dict[str, Any]) -> bool:
        """发布预警消息 - 按照智算中心文档格式"""
        try:
            # 按照文档要求的格式：{"alarmId":"", "alarmTime":"", "data":{}}
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
            else:
                self.stats['failed_sends'] += 1
                return False
        except Exception as e:
            self.logger.error(f"❌ 发布预警消息时发生错误: {e}")
            self.stats['failed_sends'] += 1
            return False
    
    def _alarm_sender_worker(self):
        """预警发送工作线程"""
        self.logger.info("🔄 预警发送线程已启动")
        
        while self.running:
            try:
                alarm = self.alarm_queue.get(timeout=1)
                if self.connected:
                    self._publish_alarm(alarm)
                else:
                    self.logger.warning("⚠️ MQTT未连接，预警消息丢失")
                    self.stats['failed_sends'] += 1
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
                self._publish_status({
                    "status": "offline",
                    "message": "MQTT智能预警引擎即将下线"
                })
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
        engine_stats = self.alarm_engine.get_stats()
        uptime = datetime.now() - self.stats['start_time']

        return {
            **self.stats,
            "uptime_seconds": uptime.total_seconds(),
            "connected": self.connected,
            "broker": f"{self.broker_host}:{self.broker_port}",
            "device_id": self.device_id,
            "queue_size": self.alarm_queue.qsize(),
            "sender_running": self.running,
            "engine_stats": engine_stats
        }


class MQTTBackendSimulator:
    """MQTT后端模拟器 - 用于测试"""

    def __init__(self, device_id: str = "device_001", broker_host: str = "broker.emqx.io", broker_port: int = 1883):
        self.device_id = device_id
        self.broker_host = broker_host
        self.broker_port = broker_port

        self.logger = logging.getLogger("BackendSimulator")

        # MQTT主题 - 按照智算中心文档要求
        self.command_topic = f"command/{device_id}"
        self.alarm_topic = f"RTO/warning_data/{device_id}"
        self.status_topic = f"smart_alarm/status/feedback/{device_id}"

        # MQTT客户端
        self.client = mqtt.Client(
            client_id=f"backend_simulator_{int(time.time())}",
            protocol=mqtt.MQTTv311
        )

        self.connected = False
        self.received_alarms = []
        self.received_status = []

        self._setup_callbacks()

    def _setup_callbacks(self):
        """设置MQTT回调"""
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
            payload = message.payload.decode('utf-8')
            data = json.loads(payload)
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


def run_comprehensive_test():
    """运行综合测试"""
    print("🧪 MQTT智能预警引擎综合测试")
    print("=" * 50)

    device_id = "test_device_001"

    # 创建组件
    smart_alarm = MQTTSmartAlarm(device_id=device_id)
    backend_sim = MQTTBackendSimulator(device_id=device_id)

    try:
        # 连接所有组件
        print("🔌 连接MQTT代理...")
        if not backend_sim.connect():
            print("❌ 后端模拟器连接失败")
            return

        if not smart_alarm.connect():
            print("❌ 智能预警引擎连接失败")
            return

        smart_alarm.start_sender()
        print("✅ 所有组件连接成功")

        # 等待连接稳定
        time.sleep(2)

        # 测试ALARM_RULE命令
        print("\n🔧 测试ALARM_RULE命令...")
        alarm_rule_data = {
            "alarmRuleId": "TEST_RULE_001",
            "alarmRuleName": "测试预警规则",
            "alarmClazz": "DEVICE_ALARM",
            "alarmLevel": "HIGH",
            "enabled": 1,
            "startTime": "08:00",
            "endTime": "18:00",
            "config": json.dumps({
                "singlePropertyRule": [{
                    "symbol": "OR",
                    "property": "t1",
                    "lowValue": 1,
                    "expression1": "lt",
                    "highValue": 10,
                    "expression2": "gt"
                }],
                "frequency": {
                    "enabled": 1,
                    "hasAccumulate": 1,
                    "accumulateCount": 2,
                    "accumulateTimeRange": 30
                }
            })
        }
        backend_sim.send_alarm_rule_command(alarm_rule_data)
        time.sleep(2)

        # 测试预警生成
        print("\n🚨 测试预警生成...")
        test_data = [
            {'t1': 5, 't2': 15, 't3': 30, 't4': 8},  # 正常
            {'t1': 0.5, 't2': 15, 't3': 30, 't4': 8},  # 异常
            {'t1': 8, 't2': 3, 't3': 30, 't4': 8},  # 异常
        ]

        for i, data in enumerate(test_data):
            print(f"处理数据 {i+1}...")
            alarm = smart_alarm.process_data(data)
            if alarm:
                print(f"  ⚠️ 触发预警: {alarm.get('alarmId')}")
            else:
                print(f"  ✅ 数据正常")
            time.sleep(1)

        # 等待处理完成
        smart_alarm.alarm_queue.join()
        time.sleep(2)

        # 显示统计信息
        stats = smart_alarm.get_stats()
        print(f"\n📈 测试完成统计:")
        print(f"  配置更新: {stats['successful_updates']} 成功, {stats['failed_updates']} 失败")
        print(f"  数据处理: {stats['processed_data']} 条")
        print(f"  预警生成: {stats['generated_alarms']} 次")
        print(f"  预警发送: {stats['sent_alarms']} 次")
        print(f"  后端收到预警: {len(backend_sim.received_alarms)} 条")
        print(f"  后端收到状态: {len(backend_sim.received_status)} 条")

        print("\n🎉 综合测试完成！")

    except KeyboardInterrupt:
        print("⚠️ 用户中断测试")
    finally:
        smart_alarm.disconnect()
        backend_sim.disconnect()


def main():
    """主函数"""
    print("🚀 MQTT智能预警引擎")
    print("=" * 30)
    print("1. 运行综合测试")
    print("2. 启动预警引擎")
    print("3. 启动后端模拟器")

    choice = input("\n请选择运行模式 (1-3): ").strip()

    if choice == "1":
        run_comprehensive_test()
    elif choice == "2":
        device_id = input("请输入设备ID (默认: device_001): ").strip() or "device_001"
        smart_alarm = MQTTSmartAlarm(device_id=device_id)

        if smart_alarm.connect():
            smart_alarm.start_sender()
            print("✅ 预警引擎已启动，按 Ctrl+C 退出")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("⚠️ 正在关闭...")
            finally:
                smart_alarm.disconnect()
        else:
            print("❌ 连接失败")
    elif choice == "3":
        device_id = input("请输入设备ID (默认: device_001): ").strip() or "device_001"
        backend_sim = MQTTBackendSimulator(device_id=device_id)

        if backend_sim.connect():
            print("✅ 后端模拟器已启动")
            print("发送配置更新示例:")
            print("backend_sim.send_config_update({'alarm_rule.alarmLevel': 'HIGH'})")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("⚠️ 正在关闭...")
            finally:
                backend_sim.disconnect()
        else:
            print("❌ 连接失败")
    else:
        print("❌ 无效选择")


if __name__ == "__main__":
    main()
