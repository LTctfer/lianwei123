#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能预警引擎 - 增强版
解决性能和可靠性问题：
1. 内存缓存 + 文件监控热加载
2. 详细异常处理和错误分类
3. 高频场景性能优化
"""

import os
import json
import threading
import time
import tomlkit
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from collections import deque
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
import hashlib


class ConfigErrorType(Enum):
    """配置错误类型枚举"""
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    PARSE_ERROR = "PARSE_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PERMISSION_ERROR = "PERMISSION_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class ConfigError:
    """详细的配置错误信息"""
    error_type: ConfigErrorType
    message: str
    details: str
    suggestion: str
    error_code: str


class ConfigException(Exception):
    """配置异常类"""
    def __init__(self, error: ConfigError):
        self.error = error
        super().__init__(f"[{error.error_code}] {error.message}")


class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> Optional[ConfigError]:
        """验证配置格式和内容"""
        try:
            # 检查必需的顶级键
            required_keys = ['alarm_rule']
            for key in required_keys:
                if key not in config:
                    return ConfigError(
                        error_type=ConfigErrorType.VALIDATION_ERROR,
                        message=f"缺少必需的配置项: {key}",
                        details=f"配置文件中未找到 '{key}' 配置项",
                        suggestion=f"请在配置文件中添加 [{key}] 配置项",
                        error_code="CFG001"
                    )
            
            # 验证alarm_rule配置
            alarm_rule = config.get('alarm_rule', {})
            if not isinstance(alarm_rule.get('enabled'), int):
                return ConfigError(
                    error_type=ConfigErrorType.VALIDATION_ERROR,
                    message="alarm_rule.enabled 必须是整数",
                    details=f"当前值: {alarm_rule.get('enabled')}, 类型: {type(alarm_rule.get('enabled'))}",
                    suggestion="请设置 enabled = 0 (禁用) 或 enabled = 1 (启用)",
                    error_code="CFG002"
                )
            
            # 验证设备预警配置
            if 'device_alarm_config' in config:
                device_config = config['device_alarm_config']
                if 'singlePropertyRule' in device_config:
                    rules = device_config['singlePropertyRule']
                    if not isinstance(rules, list):
                        return ConfigError(
                            error_type=ConfigErrorType.VALIDATION_ERROR,
                            message="singlePropertyRule 必须是数组",
                            details=f"当前类型: {type(rules)}",
                            suggestion="请使用 [[device_alarm_config.singlePropertyRule]] 格式",
                            error_code="CFG003"
                        )
            
            return None  # 验证通过
            
        except Exception as e:
            return ConfigError(
                error_type=ConfigErrorType.VALIDATION_ERROR,
                message="配置验证时发生未知错误",
                details=str(e),
                suggestion="请检查配置文件格式是否正确",
                error_code="CFG999"
            )


class FileWatcher:
    """文件监控器"""
    
    def __init__(self, file_path: str, callback: Callable):
        self.file_path = file_path
        self.callback = callback
        self.last_modified = 0
        self.running = False
        self.thread = None
        
    def start(self):
        """启动文件监控"""
        if self.running:
            return
            
        self.running = True
        self.last_modified = self._get_file_mtime()
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        """停止文件监控"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
            
    def _get_file_mtime(self) -> float:
        """获取文件修改时间"""
        try:
            return os.path.getmtime(self.file_path)
        except:
            return 0
            
    def _watch_loop(self):
        """监控循环"""
        while self.running:
            try:
                current_mtime = self._get_file_mtime()
                if current_mtime > self.last_modified:
                    self.last_modified = current_mtime
                    self.callback()
                time.sleep(0.5)  # 检查间隔
            except Exception:
                pass  # 忽略监控过程中的错误


class ConfigManager:
    """配置管理器 - 支持内存缓存和热加载"""

    def __init__(self, config_file: str):
        # 处理相对路径，确保配置文件在脚本同级目录
        if not os.path.isabs(config_file):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_file = os.path.join(script_dir, config_file)
        else:
            self.config_file = config_file
        self.config_cache = {}
        self.config_version = 0
        self.config_hash = ""
        self.last_load_time = 0
        self.file_watcher = None
        self.lock = threading.RLock()
        self.validator = ConfigValidator()
        
        # 初始化加载配置
        self._load_config_from_file()
        
        # 启动文件监控
        self._start_file_watcher()
        
    def get_config(self) -> Dict[str, Any]:
        """获取配置（从缓存）"""
        with self.lock:
            return self.config_cache.copy()
            
    def get_config_version(self) -> int:
        """获取配置版本号"""
        return self.config_version
        
    def update_config_memory(self, updates: Dict[str, Any], persist: bool = True) -> None:
        """更新内存配置（高频场景优化）"""
        with self.lock:
            # 更新内存配置
            config = self.config_cache.copy()
            
            for key, value in updates.items():
                keys = key.split('.')
                current = config
                
                # 导航到目标位置
                for k in keys[:-1]:
                    if k.isdigit():
                        index = int(k)
                        current = current[index]
                    else:
                        if k not in current:
                            current[k] = {}
                        current = current[k]
                
                # 设置最终值
                final_key = keys[-1]
                if final_key.isdigit():
                    index = int(final_key)
                    current[index] = value
                else:
                    current[final_key] = value
            
            # 验证配置
            error = self.validator.validate_config(config)
            if error:
                raise ConfigException(error)
            
            # 更新缓存
            self.config_cache = config
            self.config_version += 1
            
            # 可选持久化
            if persist:
                self._save_config_to_file(config)
                
    def _load_config_from_file(self) -> None:
        """从文件加载配置"""
        try:
            if not os.path.exists(self.config_file):
                raise ConfigException(ConfigError(
                    error_type=ConfigErrorType.FILE_NOT_FOUND,
                    message=f"配置文件不存在: {self.config_file}",
                    details=f"文件路径: {os.path.abspath(self.config_file)}",
                    suggestion="请确保配置文件存在或使用默认配置",
                    error_code="CFG101"
                ))
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 计算文件哈希
            new_hash = hashlib.md5(content.encode()).hexdigest()
            if new_hash == self.config_hash:
                return  # 内容未变化，无需重新加载
                
            # 解析配置
            config = tomlkit.parse(content)
            
            # 验证配置
            error = self.validator.validate_config(config)
            if error:
                raise ConfigException(error)
            
            # 更新缓存
            with self.lock:
                self.config_cache = config
                self.config_hash = new_hash
                self.config_version += 1
                self.last_load_time = time.time()
                
        except ConfigException:
            raise
        except PermissionError as e:
            raise ConfigException(ConfigError(
                error_type=ConfigErrorType.PERMISSION_ERROR,
                message="没有权限读取配置文件",
                details=str(e),
                suggestion="请检查文件权限或以管理员身份运行",
                error_code="CFG102"
            ))
        except Exception as e:
            raise ConfigException(ConfigError(
                error_type=ConfigErrorType.PARSE_ERROR,
                message="配置文件解析失败",
                details=str(e),
                suggestion="请检查TOML格式是否正确",
                error_code="CFG103"
            ))
            
    def _save_config_to_file(self, config: Dict[str, Any]) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(tomlkit.dumps(config))
                
            # 更新哈希
            with open(self.config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.config_hash = hashlib.md5(content.encode()).hexdigest()
            
        except PermissionError as e:
            raise ConfigException(ConfigError(
                error_type=ConfigErrorType.PERMISSION_ERROR,
                message="没有权限写入配置文件",
                details=str(e),
                suggestion="请检查文件权限或以管理员身份运行",
                error_code="CFG104"
            ))
        except Exception as e:
            raise ConfigException(ConfigError(
                error_type=ConfigErrorType.UNKNOWN_ERROR,
                message="保存配置文件失败",
                details=str(e),
                suggestion="请检查磁盘空间和文件权限",
                error_code="CFG105"
            ))
            
    def _start_file_watcher(self):
        """启动文件监控"""
        if self.file_watcher:
            self.file_watcher.stop()
            
        self.file_watcher = FileWatcher(
            self.config_file, 
            self._on_file_changed
        )
        self.file_watcher.start()
        
    def _on_file_changed(self):
        """文件变更回调"""
        try:
            self._load_config_from_file()
            print(f"🔄 配置文件已自动重新加载 (版本: {self.config_version})")
        except Exception as e:
            print(f"⚠️ 配置文件重新加载失败: {e}")
            
    def __del__(self):
        """析构函数"""
        if self.file_watcher:
            self.file_watcher.stop()


class SmartAlarmEngineEnhanced:
    """智能预警引擎 - 增强版"""

    # 操作符映射
    OPS = {
        'lt': lambda x, y: x < y, 'le': lambda x, y: x <= y, 'eq': lambda x, y: x == y,
        'gt': lambda x, y: x > y, 'ge': lambda x, y: x >= y, 'ne': lambda x, y: x != y
    }

    def __init__(self, config_file: str = "config.toml"):
        """初始化增强版引擎"""
        self.config_manager = ConfigManager(config_file)
        self.alarm_history = []
        self.freq_states = {}
        self.stats = {
            'total_processed': 0,
            'alarms_triggered': 0,
            'config_reloads': 0,
            'last_process_time': 0
        }

    def process_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理数据并生成预警 - 优化版本"""
        start_time = time.time()

        try:
            # 获取缓存的配置（无I/O操作）
            config = self.config_manager.get_config()
            alarm_rule = config.get('alarm_rule', {})

            # 基础检查
            if not alarm_rule.get('enabled', 1) or not self._in_time_range(alarm_rule):
                return None

            # 获取配置
            alarm_clazz = alarm_rule.get('alarmClazz', 'DEVICE_ALARM')
            config_key = 'device_alarm_config' if alarm_clazz == 'DEVICE_ALARM' else 'enterprise_alarm_config'
            alarm_config = config.get(config_key, {})

            # 评估规则
            triggered = self._evaluate_rules(data, alarm_config)

            # 频率控制
            rule_id = alarm_rule.get('alarmRuleId', 'default')
            freq_config = alarm_config.get('frequency', {})

            if not self._update_frequency(rule_id, freq_config, triggered):
                return None

            # 生成预警
            if triggered:
                alarm = {
                    'alarmId': rule_id,
                    'alarmTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'alarmLevel': alarm_rule.get('alarmLevel', 'LOW'),
                    'alarmClazz': alarm_clazz,
                    'data': data
                }

                self.alarm_history.append(alarm)
                self.stats['alarms_triggered'] += 1

                return alarm

            return None

        except ConfigException as e:
            print(f"❌ 配置错误: {e}")
            return None
        except Exception as e:
            print(f"❌ 处理数据时发生错误: {e}")
            return None
        finally:
            # 更新统计信息
            self.stats['total_processed'] += 1
            self.stats['last_process_time'] = time.time() - start_time

    def update_config(self, updates: Dict[str, Any], persist: bool = True) -> Dict[str, Any]:
        """更新配置 - 增强版本"""
        try:
            self.config_manager.update_config_memory(updates, persist)

            return {
                'success': True,
                'message': '配置更新成功',
                'version': self.config_manager.get_config_version(),
                'persist': persist
            }

        except ConfigException as e:
            return {
                'success': False,
                'error_type': e.error.error_type.value,
                'error_code': e.error.error_code,
                'message': e.error.message,
                'details': e.error.details,
                'suggestion': e.error.suggestion
            }
        except Exception as e:
            return {
                'success': False,
                'error_type': 'UNKNOWN_ERROR',
                'error_code': 'UNK001',
                'message': '更新配置时发生未知错误',
                'details': str(e),
                'suggestion': '请检查配置格式和权限'
            }

    def receive_platform_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """接收平台配置命令 - 增强版本"""
        try:
            if command.get('commandType') != 'ALARM_RULE':
                return {
                    'success': False,
                    'error_type': 'VALIDATION_ERROR',
                    'error_code': 'CMD001',
                    'message': '不支持的命令类型',
                    'details': f"收到命令类型: {command.get('commandType')}",
                    'suggestion': '请使用 ALARM_RULE 命令类型'
                }

            data = command.get('data', {})
            if not data:
                return {
                    'success': False,
                    'error_type': 'VALIDATION_ERROR',
                    'error_code': 'CMD002',
                    'message': '命令数据为空',
                    'details': '未找到 data 字段或 data 为空',
                    'suggestion': '请在命令中包含有效的 data 字段'
                }

            updates = {}

            # 更新基础配置
            for field in ['alarmRuleId', 'alarmRuleName', 'alarmClazz', 'alarmLevel', 'enabled', 'startTime', 'endTime']:
                if field in data:
                    updates[f'alarm_rule.{field}'] = data[field]

            # 高频场景优化：默认不持久化，可通过参数控制
            persist = command.get('persist', False)

            return self.update_config(updates, persist)

        except Exception as e:
            return {
                'success': False,
                'error_type': 'UNKNOWN_ERROR',
                'error_code': 'CMD999',
                'message': '处理平台命令时发生未知错误',
                'details': str(e),
                'suggestion': '请检查命令格式和系统状态'
            }

    def get_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        return {
            **self.stats,
            'config_version': self.config_manager.get_config_version(),
            'config_last_load': self.config_manager.last_load_time,
            'active_freq_states': len(self.freq_states),
            'alarm_history_count': len(self.alarm_history)
        }

    def _in_time_range(self, alarm_rule: Dict[str, Any]) -> bool:
        """检查是否在预警时间范围内"""
        try:
            start_time = alarm_rule.get('startTime', '00:00')
            end_time = alarm_rule.get('endTime', '23:59')
            current_time = datetime.now().strftime('%H:%M')
            return start_time <= current_time <= end_time
        except:
            return True

    def _evaluate_rules(self, data: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """评估预警规则"""
        # 单属性规则
        single_rules = config.get('singlePropertyRule', [])
        for rule in single_rules:
            if self._evaluate_single_rule(data, rule):
                return True

        # 双属性规则
        double_rules = config.get('doublePropertyRule', [])
        for rule in double_rules:
            if self._evaluate_double_rule(data, rule):
                return True

        return False

    def _evaluate_single_rule(self, data: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """评估单属性规则"""
        try:
            prop = rule.get('property')
            if prop not in data:
                return False

            value = data[prop]
            symbol = rule.get('symbol', 'OR')

            # 第一个条件
            low_value = rule.get('lowValue')
            expr1 = rule.get('expression1')
            condition1 = low_value is not None and expr1 and self.OPS[expr1](value, low_value)

            # 第二个条件
            high_value = rule.get('highValue')
            expr2 = rule.get('expression2')
            condition2 = high_value is not None and expr2 and self.OPS[expr2](value, high_value)

            # 根据逻辑符号组合条件
            if symbol == 'AND':
                return condition1 and condition2
            else:  # OR
                return condition1 or condition2

        except Exception:
            return False

    def _evaluate_double_rule(self, data: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """评估双属性规则"""
        try:
            left_prop = rule.get('leftProperty')
            right_prop = rule.get('rightProperty')

            if left_prop not in data or right_prop not in data:
                return False

            left_value = data[left_prop]
            right_value = data[right_prop]
            expression = rule.get('expression')

            return expression and self.OPS[expression](left_value, right_value)
        except Exception:
            return False

    def _update_frequency(self, rule_id: str, config: Dict[str, Any], triggered: bool) -> bool:
        """频率控制"""
        if not config.get('enabled', 1):
            return True

        state = self.freq_states.setdefault(rule_id, {'events': deque(), 'count': 0})

        if config.get('hasAccumulate', 1):
            # 累积模式
            if triggered:
                state['events'].append(datetime.now())

            # 清理过期事件
            time_range = config.get('accumulateTimeRange', 30) * 60
            cutoff = datetime.now().timestamp() - time_range

            while state['events'] and state['events'][0].timestamp() < cutoff:
                state['events'].popleft()

            return len(state['events']) >= config.get('accumulateCount', 3)
        else:
            # 连续模式
            if triggered:
                state['count'] += 1
            else:
                state['count'] = 0

            return state['count'] >= config.get('continuousCount', 3)

    def push_alarm(self, alarm: Dict[str, Any], device_id: str) -> bool:
        """推送预警到平台"""
        try:
            # 这里可以实现实际的推送逻辑
            print(f"📤 推送预警到设备 {device_id}: {alarm['alarmId']}")
            return True
        except Exception as e:
            print(f"❌ 推送预警失败: {e}")
            return False


def main():
    """演示增强版引擎的使用"""
    print("🚀 智能预警引擎 - 增强版演示")
    print("=" * 50)

    try:
        # 创建增强版引擎
        engine = SmartAlarmEngineEnhanced()

        # 显示初始统计信息
        stats = engine.get_stats()
        print(f"📊 初始状态:")
        print(f"   配置版本: {stats['config_version']}")
        print(f"   已处理数据: {stats['total_processed']} 条")
        print(f"   触发预警: {stats['alarms_triggered']} 次")

        # 测试数据处理
        test_data = [
            {'name': '正常数据', 'data': {'t1': 5, 't2': 15, 't3': 30, 't4': 8}},
            {'name': '异常数据', 'data': {'t1': 0.5, 't2': 15, 't3': 30, 't4': 8}},
        ]

        print(f"\n🧪 测试数据处理:")
        for test in test_data:
            alarm = engine.process_data(test['data'])
            if alarm:
                print(f"   ⚠️  {test['name']}: 触发预警 - {alarm['alarmId']}")
            else:
                print(f"   ✅ {test['name']}: 正常")

        # 测试配置更新（内存模式）
        print(f"\n🔧 测试高频配置更新（内存模式）:")
        result = engine.update_config({
            'alarm_rule.alarmLevel': 'CRITICAL'
        }, persist=False)

        if result['success']:
            print(f"   ✅ 配置更新成功 (版本: {result['version']})")
        else:
            print(f"   ❌ 配置更新失败: {result['message']}")

        # 测试平台命令
        print(f"\n📡 测试平台命令:")
        command = {
            'commandType': 'ALARM_RULE',
            'data': {
                'alarmLevel': 'HIGH',
                'enabled': 1
            },
            'persist': False  # 高频场景不持久化
        }

        result = engine.receive_platform_command(command)
        if result['success']:
            print(f"   ✅ 平台命令处理成功")
        else:
            print(f"   ❌ 平台命令处理失败: {result['message']}")

        # 显示最终统计信息
        stats = engine.get_stats()
        print(f"\n📊 最终统计:")
        print(f"   配置版本: {stats['config_version']}")
        print(f"   已处理数据: {stats['total_processed']} 条")
        print(f"   触发预警: {stats['alarms_triggered']} 次")
        print(f"   平均处理时间: {stats['last_process_time']:.4f}s")

        print(f"\n✅ 增强版引擎演示完成!")

    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")


if __name__ == "__main__":
    main()
