"""
实时监控系统模块
支持流式数据处理、异常检测和自动预警触发
提供高性能的实时数据处理能力
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Callable, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
import threading
import queue
import time
from collections import deque
import sqlite3

logger = logging.getLogger(__name__)

@dataclass
class MonitoringStation:
    """监测站数据类"""
    station_id: str
    name: str
    latitude: float
    longitude: float
    x: float  # 平面坐标
    y: float  # 平面坐标
    elevation: float = 0.0
    station_type: str = 'air_quality'  # 'air_quality', 'meteorological'
    sensors: List[str] = field(default_factory=list)
    is_active: bool = True
    last_update: Optional[datetime] = None
    data_quality_score: float = 1.0

@dataclass
class SensorReading:
    """传感器读数数据类"""
    station_id: str
    sensor_type: str  # 'pm25', 'pm10', 'wind_speed', etc.
    value: float
    timestamp: datetime
    unit: str
    quality_flag: str = 'good'  # 'good', 'suspect', 'bad'
    raw_value: Optional[float] = None

@dataclass
class RealTimeAlert:
    """实时预警数据类"""
    alert_id: str
    station_id: str
    alert_type: str  # 'threshold_exceeded', 'abnormal_trend', 'sensor_failure'
    severity: str    # 'low', 'medium', 'high', 'critical'
    message: str
    timestamp: datetime
    value: float
    threshold: float
    is_acknowledged: bool = False

class DataValidator:
    """数据验证器"""
    
    def __init__(self):
        self.validation_rules = {
            'pm25': {'min': 0, 'max': 1000, 'rate_change_max': 100},
            'pm10': {'min': 0, 'max': 2000, 'rate_change_max': 150},
            'wind_speed': {'min': 0, 'max': 50, 'rate_change_max': 10},
            'wind_direction': {'min': 0, 'max': 360, 'rate_change_max': 90},
            'temperature': {'min': -50, 'max': 60, 'rate_change_max': 10},
            'humidity': {'min': 0, 'max': 100, 'rate_change_max': 20},
            'pressure': {'min': 800, 'max': 1200, 'rate_change_max': 50}
        }
    
    def validate_reading(self, reading: SensorReading, 
                        previous_readings: List[SensorReading]) -> Tuple[bool, str]:
        """
        验证传感器读数
        
        Args:
            reading: 当前读数
            previous_readings: 历史读数
            
        Returns:
            (是否有效, 验证信息)
        """
        sensor_type = reading.sensor_type
        value = reading.value
        
        # 检查基本范围
        if sensor_type in self.validation_rules:
            rules = self.validation_rules[sensor_type]
            
            if value < rules['min'] or value > rules['max']:
                return False, f"数值 {value} 超出有效范围 [{rules['min']}, {rules['max']}]"
        
        # 检查变化率
        if previous_readings and len(previous_readings) > 0:
            last_reading = previous_readings[-1]
            if last_reading.sensor_type == sensor_type:
                time_diff = (reading.timestamp - last_reading.timestamp).total_seconds() / 3600
                if time_diff > 0 and time_diff < 1:  # 1小时内
                    rate_change = abs(value - last_reading.value) / time_diff
                    max_rate = self.validation_rules.get(sensor_type, {}).get('rate_change_max', float('inf'))
                    
                    if rate_change > max_rate:
                        return False, f"变化率 {rate_change:.1f}/h 过大，超过阈值 {max_rate}/h"
        
        return True, "有效"
    
    def calculate_quality_score(self, readings: List[SensorReading]) -> float:
        """
        计算数据质量评分
        
        Args:
            readings: 传感器读数列表
            
        Returns:
            质量评分 (0-1)
        """
        if not readings:
            return 0.0
        
        valid_count = sum(1 for r in readings if r.quality_flag == 'good')
        completeness = valid_count / len(readings)
        
        # 时间序列完整性
        if len(readings) > 1:
            time_gaps = []
            for i in range(1, len(readings)):
                gap = (readings[i].timestamp - readings[i-1].timestamp).total_seconds()
                time_gaps.append(gap)
            
            expected_interval = 300  # 5分钟
            time_consistency = sum(1 for gap in time_gaps if abs(gap - expected_interval) < 60) / len(time_gaps)
        else:
            time_consistency = 1.0
        
        # 数值稳定性（避免异常波动）
        if len(readings) > 2:
            values = [r.value for r in readings if r.quality_flag == 'good']
            if values:
                cv = np.std(values) / np.mean(values) if np.mean(values) > 0 else 1
                stability = max(0, 1 - cv / 2)  # 变异系数越小越稳定
            else:
                stability = 0
        else:
            stability = 1.0
        
        # 综合评分
        quality_score = (completeness * 0.4 + time_consistency * 0.3 + stability * 0.3)
        return min(1.0, max(0.0, quality_score))

class AnomalyDetector:
    """异常检测器"""
    
    def __init__(self, window_size: int = 24):
        self.window_size = window_size
        self.baseline_data = {}  # 存储各传感器的基线数据
    
    def update_baseline(self, station_id: str, sensor_type: str, values: List[float]):
        """更新基线数据"""
        key = f"{station_id}_{sensor_type}"
        if key not in self.baseline_data:
            self.baseline_data[key] = deque(maxlen=self.window_size * 7)  # 保存一周数据
        
        self.baseline_data[key].extend(values)
    
    def detect_anomaly(self, reading: SensorReading) -> Tuple[bool, float, str]:
        """
        检测异常
        
        Args:
            reading: 传感器读数
            
        Returns:
            (是否异常, 异常程度, 异常类型)
        """
        key = f"{reading.station_id}_{reading.sensor_type}"
        
        if key not in self.baseline_data or len(self.baseline_data[key]) < 10:
            return False, 0.0, "数据不足"
        
        baseline_values = list(self.baseline_data[key])
        current_value = reading.value
        
        # 统计异常检测（3σ原则）
        mean_val = np.mean(baseline_values)
        std_val = np.std(baseline_values)
        
        if std_val > 0:
            z_score = abs(current_value - mean_val) / std_val
            if z_score > 3:
                return True, z_score, "统计异常"
            elif z_score > 2:
                return True, z_score, "统计偏差"
        
        # 趋势异常检测
        if len(baseline_values) >= 5:
            recent_values = baseline_values[-5:]
            trend = np.polyfit(range(len(recent_values)), recent_values, 1)[0]
            
            # 如果当前值与趋势预测差异很大
            predicted_value = recent_values[-1] + trend
            trend_deviation = abs(current_value - predicted_value) / (std_val + 1e-6)
            
            if trend_deviation > 2:
                return True, trend_deviation, "趋势异常"
        
        # 极值检测
        percentile_95 = np.percentile(baseline_values, 95)
        percentile_5 = np.percentile(baseline_values, 5)
        
        if current_value > percentile_95 * 1.5 or current_value < percentile_5 * 0.5:
            extreme_score = max(current_value / percentile_95, percentile_5 / current_value)
            return True, extreme_score, "极值异常"
        
        return False, 0.0, "正常"

class RealTimeMonitoringSystem:
    """实时监控系统"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化实时监控系统
        
        Args:
            config: 系统配置
        """
        self.config = config
        self.stations: Dict[str, MonitoringStation] = {}
        self.data_validator = DataValidator()
        self.anomaly_detector = AnomalyDetector()
        
        # 数据缓存
        self.reading_buffer = {}  # 每个传感器的最近读数
        self.alert_queue = queue.Queue()
        
        # 阈值配置
        self.thresholds = {
            'pm25': {'yellow': 75, 'orange': 150, 'red': 250},
            'pm10': {'yellow': 150, 'orange': 250, 'red': 350},
            'wind_speed': {'low': 1.0, 'high': 15.0}
        }
        
        # 运行状态
        self.is_running = False
        self.monitoring_thread = None
        self.db_connection = None
        
        # 回调函数
        self.alert_callbacks: List[Callable] = []
        self.data_callbacks: List[Callable] = []
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化SQLite数据库"""
        try:
            self.db_connection = sqlite3.connect(':memory:', check_same_thread=False)
            cursor = self.db_connection.cursor()
            
            # 创建表
            cursor.execute('''
                CREATE TABLE sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id TEXT,
                    sensor_type TEXT,
                    value REAL,
                    timestamp TEXT,
                    unit TEXT,
                    quality_flag TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT,
                    station_id TEXT,
                    alert_type TEXT,
                    severity TEXT,
                    message TEXT,
                    timestamp TEXT,
                    value REAL,
                    threshold REAL,
                    is_acknowledged INTEGER DEFAULT 0
                )
            ''')
            
            self.db_connection.commit()
            logger.info("数据库初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
    
    def add_monitoring_station(self, station: MonitoringStation):
        """添加监测站"""
        self.stations[station.station_id] = station
        self.reading_buffer[station.station_id] = {}
        logger.info(f"添加监测站: {station.name} ({station.station_id})")
    
    def remove_monitoring_station(self, station_id: str):
        """移除监测站"""
        if station_id in self.stations:
            del self.stations[station_id]
            if station_id in self.reading_buffer:
                del self.reading_buffer[station_id]
            logger.info(f"移除监测站: {station_id}")
    
    def register_alert_callback(self, callback: Callable[[RealTimeAlert], None]):
        """注册预警回调函数"""
        self.alert_callbacks.append(callback)
    
    def register_data_callback(self, callback: Callable[[SensorReading], None]):
        """注册数据回调函数"""
        self.data_callbacks.append(callback)
    
    def process_sensor_reading(self, reading: SensorReading) -> bool:
        """
        处理传感器读数
        
        Args:
            reading: 传感器读数
            
        Returns:
            是否处理成功
        """
        try:
            station_id = reading.station_id
            sensor_type = reading.sensor_type
            
            # 检查监测站是否存在
            if station_id not in self.stations:
                logger.warning(f"未知监测站: {station_id}")
                return False
            
            # 获取历史读数用于验证
            station_buffer = self.reading_buffer.get(station_id, {})
            previous_readings = station_buffer.get(sensor_type, [])
            
            # 数据验证
            is_valid, validation_msg = self.data_validator.validate_reading(reading, previous_readings)
            
            if not is_valid:
                reading.quality_flag = 'bad'
                logger.warning(f"数据验证失败 {station_id}-{sensor_type}: {validation_msg}")
            
            # 异常检测
            is_anomaly, anomaly_score, anomaly_type = self.anomaly_detector.detect_anomaly(reading)
            
            if is_anomaly:
                alert = RealTimeAlert(\n                    alert_id=f\"ANOMALY_{station_id}_{int(time.time())}\",\n                    station_id=station_id,\n                    alert_type='abnormal_reading',\n                    severity='medium' if anomaly_score < 5 else 'high',\n                    message=f\"{sensor_type} 检测到 {anomaly_type}: {reading.value:.2f} {reading.unit} (异常评分: {anomaly_score:.2f})\",\n                    timestamp=reading.timestamp,\n                    value=reading.value,\n                    threshold=0.0\n                )\n                self._trigger_alert(alert)\n            \n            # 阈值检查\n            self._check_thresholds(reading)\n            \n            # 更新缓存\n            if station_id not in self.reading_buffer:\n                self.reading_buffer[station_id] = {}\n            if sensor_type not in self.reading_buffer[station_id]:\n                self.reading_buffer[station_id][sensor_type] = deque(maxlen=100)\n            \n            self.reading_buffer[station_id][sensor_type].append(reading)\n            \n            # 更新异常检测基线\n            if reading.quality_flag == 'good':\n                self.anomaly_detector.update_baseline(station_id, sensor_type, [reading.value])\n            \n            # 存储到数据库\n            self._store_reading_to_db(reading)\n            \n            # 更新监测站状态\n            self.stations[station_id].last_update = reading.timestamp\n            \n            # 触发数据回调\n            for callback in self.data_callbacks:\n                try:\n                    callback(reading)\n                except Exception as e:\n                    logger.error(f\"数据回调执行失败: {e}\")\n            \n            return True\n            \n        except Exception as e:\n            logger.error(f\"处理传感器读数失败: {e}\")\n            return False\n    \n    def _check_thresholds(self, reading: SensorReading):\n        \"\"\"检查阈值并触发预警\"\"\"\n        sensor_type = reading.sensor_type\n        value = reading.value\n        \n        if sensor_type in self.thresholds:\n            thresholds = self.thresholds[sensor_type]\n            \n            alert_level = None\n            threshold_value = 0\n            \n            if 'red' in thresholds and value >= thresholds['red']:\n                alert_level = 'critical'\n                threshold_value = thresholds['red']\n            elif 'orange' in thresholds and value >= thresholds['orange']:\n                alert_level = 'high'\n                threshold_value = thresholds['orange']\n            elif 'yellow' in thresholds and value >= thresholds['yellow']:\n                alert_level = 'medium'\n                threshold_value = thresholds['yellow']\n            \n            if alert_level:\n                alert = RealTimeAlert(\n                    alert_id=f\"THRESHOLD_{reading.station_id}_{int(time.time())}\",\n                    station_id=reading.station_id,\n                    alert_type='threshold_exceeded',\n                    severity=alert_level,\n                    message=f\"{sensor_type} 超过 {alert_level} 阈值: {value:.2f} {reading.unit} (阈值: {threshold_value})\",\n                    timestamp=reading.timestamp,\n                    value=value,\n                    threshold=threshold_value\n                )\n                self._trigger_alert(alert)\n    \n    def _trigger_alert(self, alert: RealTimeAlert):\n        \"\"\"触发预警\"\"\"\n        try:\n            # 添加到预警队列\n            self.alert_queue.put(alert)\n            \n            # 存储到数据库\n            self._store_alert_to_db(alert)\n            \n            # 触发预警回调\n            for callback in self.alert_callbacks:\n                try:\n                    callback(alert)\n                except Exception as e:\n                    logger.error(f\"预警回调执行失败: {e}\")\n            \n            logger.info(f\"触发预警: {alert.alert_id} - {alert.message}\")\n            \n        except Exception as e:\n            logger.error(f\"触发预警失败: {e}\")\n    \n    def _store_reading_to_db(self, reading: SensorReading):\n        \"\"\"存储读数到数据库\"\"\"\n        try:\n            cursor = self.db_connection.cursor()\n            cursor.execute('''\n                INSERT INTO sensor_readings \n                (station_id, sensor_type, value, timestamp, unit, quality_flag)\n                VALUES (?, ?, ?, ?, ?, ?)\n            ''', (\n                reading.station_id,\n                reading.sensor_type,\n                reading.value,\n                reading.timestamp.isoformat(),\n                reading.unit,\n                reading.quality_flag\n            ))\n            self.db_connection.commit()\n        except Exception as e:\n            logger.error(f\"存储读数到数据库失败: {e}\")\n    \n    def _store_alert_to_db(self, alert: RealTimeAlert):\n        \"\"\"存储预警到数据库\"\"\"\n        try:\n            cursor = self.db_connection.cursor()\n            cursor.execute('''\n                INSERT INTO alerts \n                (alert_id, station_id, alert_type, severity, message, timestamp, value, threshold)\n                VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n            ''', (\n                alert.alert_id,\n                alert.station_id,\n                alert.alert_type,\n                alert.severity,\n                alert.message,\n                alert.timestamp.isoformat(),\n                alert.value,\n                alert.threshold\n            ))\n            self.db_connection.commit()\n        except Exception as e:\n            logger.error(f\"存储预警到数据库失败: {e}\")\n    \n    def get_latest_readings(self, station_id: str, hours: int = 1) -> List[SensorReading]:\n        \"\"\"获取最新读数\"\"\"\n        try:\n            cursor = self.db_connection.cursor()\n            since_time = (datetime.now() - timedelta(hours=hours)).isoformat()\n            \n            cursor.execute('''\n                SELECT station_id, sensor_type, value, timestamp, unit, quality_flag\n                FROM sensor_readings\n                WHERE station_id = ? AND timestamp >= ?\n                ORDER BY timestamp DESC\n            ''', (station_id, since_time))\n            \n            readings = []\n            for row in cursor.fetchall():\n                reading = SensorReading(\n                    station_id=row[0],\n                    sensor_type=row[1],\n                    value=row[2],\n                    timestamp=datetime.fromisoformat(row[3]),\n                    unit=row[4],\n                    quality_flag=row[5]\n                )\n                readings.append(reading)\n            \n            return readings\n            \n        except Exception as e:\n            logger.error(f\"获取最新读数失败: {e}\")\n            return []\n    \n    def get_active_alerts(self) -> List[RealTimeAlert]:\n        \"\"\"获取活跃预警\"\"\"\n        try:\n            cursor = self.db_connection.cursor()\n            cursor.execute('''\n                SELECT alert_id, station_id, alert_type, severity, message, timestamp, value, threshold\n                FROM alerts\n                WHERE is_acknowledged = 0\n                ORDER BY timestamp DESC\n            ''')\n            \n            alerts = []\n            for row in cursor.fetchall():\n                alert = RealTimeAlert(\n                    alert_id=row[0],\n                    station_id=row[1],\n                    alert_type=row[2],\n                    severity=row[3],\n                    message=row[4],\n                    timestamp=datetime.fromisoformat(row[5]),\n                    value=row[6],\n                    threshold=row[7]\n                )\n                alerts.append(alert)\n            \n            return alerts\n            \n        except Exception as e:\n            logger.error(f\"获取活跃预警失败: {e}\")\n            return []\n    \n    def acknowledge_alert(self, alert_id: str) -> bool:\n        \"\"\"确认预警\"\"\"\n        try:\n            cursor = self.db_connection.cursor()\n            cursor.execute('''\n                UPDATE alerts SET is_acknowledged = 1 WHERE alert_id = ?\n            ''', (alert_id,))\n            self.db_connection.commit()\n            \n            if cursor.rowcount > 0:\n                logger.info(f\"预警 {alert_id} 已确认\")\n                return True\n            else:\n                logger.warning(f\"预警 {alert_id} 不存在\")\n                return False\n                \n        except Exception as e:\n            logger.error(f\"确认预警失败: {e}\")\n            return False\n    \n    def get_system_statistics(self) -> Dict[str, Any]:\n        \"\"\"获取系统统计信息\"\"\"\n        try:\n            cursor = self.db_connection.cursor()\n            \n            # 统计读数数量\n            cursor.execute('SELECT COUNT(*) FROM sensor_readings')\n            total_readings = cursor.fetchone()[0]\n            \n            # 统计预警数量\n            cursor.execute('SELECT COUNT(*) FROM alerts')\n            total_alerts = cursor.fetchone()[0]\n            \n            # 活跃预警数量\n            cursor.execute('SELECT COUNT(*) FROM alerts WHERE is_acknowledged = 0')\n            active_alerts = cursor.fetchone()[0]\n            \n            # 监测站统计\n            active_stations = sum(1 for station in self.stations.values() if station.is_active)\n            \n            # 数据质量统计\n            cursor.execute('''\n                SELECT quality_flag, COUNT(*) \n                FROM sensor_readings \n                WHERE timestamp >= datetime('now', '-24 hours')\n                GROUP BY quality_flag\n            ''')\n            quality_stats = dict(cursor.fetchall())\n            \n            return {\n                'monitoring_stations': {\n                    'total': len(self.stations),\n                    'active': active_stations,\n                    'inactive': len(self.stations) - active_stations\n                },\n                'data_statistics': {\n                    'total_readings': total_readings,\n                    'quality_distribution': quality_stats\n                },\n                'alert_statistics': {\n                    'total_alerts': total_alerts,\n                    'active_alerts': active_alerts,\n                    'acknowledged_alerts': total_alerts - active_alerts\n                },\n                'system_status': {\n                    'is_running': self.is_running,\n                    'buffer_size': sum(len(sensors) for sensors in self.reading_buffer.values()),\n                    'alert_queue_size': self.alert_queue.qsize()\n                }\n            }\n            \n        except Exception as e:\n            logger.error(f\"获取系统统计失败: {e}\")\n            return {}\n    \n    def start_monitoring(self):\n        \"\"\"启动实时监控\"\"\"\n        if self.is_running:\n            logger.warning(\"监控系统已在运行\")\n            return\n        \n        self.is_running = True\n        logger.info(\"启动实时监控系统\")\n        \n        # 可以在这里添加后台监控线程\n        # 例如：定期清理过期数据、计算统计指标等\n    \n    def stop_monitoring(self):\n        \"\"\"停止实时监控\"\"\"\n        if not self.is_running:\n            return\n        \n        self.is_running = False\n        logger.info(\"停止实时监控系统\")\n        \n        # 清理资源\n        if self.db_connection:\n            self.db_connection.close()\n    \n    def simulate_sensor_data(self, station_id: str, duration_minutes: int = 60):\n        \"\"\"模拟传感器数据（用于测试）\"\"\"\n        if station_id not in self.stations:\n            logger.error(f\"监测站 {station_id} 不存在\")\n            return\n        \n        logger.info(f\"开始模拟 {station_id} 的传感器数据，持续 {duration_minutes} 分钟\")\n        \n        sensor_types = ['pm25', 'pm10', 'wind_speed', 'wind_direction', 'temperature', 'humidity']\n        start_time = datetime.now()\n        \n        for minute in range(duration_minutes):\n            timestamp = start_time + timedelta(minutes=minute)\n            \n            for sensor_type in sensor_types:\n                # 生成模拟数据\n                if sensor_type == 'pm25':\n                    base_value = 50 + 30 * np.sin(minute * np.pi / 30)\n                    value = max(0, base_value + np.random.normal(0, 10))\n                elif sensor_type == 'pm10':\n                    base_value = 80 + 40 * np.sin(minute * np.pi / 30)\n                    value = max(0, base_value + np.random.normal(0, 15))\n                elif sensor_type == 'wind_speed':\n                    value = max(0.1, 3 + np.random.normal(0, 1))\n                elif sensor_type == 'wind_direction':\n                    value = (180 + np.random.normal(0, 30)) % 360\n                elif sensor_type == 'temperature':\n                    value = 20 + 10 * np.sin(minute * np.pi / 60) + np.random.normal(0, 2)\n                elif sensor_type == 'humidity':\n                    value = np.clip(60 + np.random.normal(0, 10), 0, 100)\n                else:\n                    value = np.random.uniform(0, 100)\n                \n                # 创建传感器读数\n                reading = SensorReading(\n                    station_id=station_id,\n                    sensor_type=sensor_type,\n                    value=value,\n                    timestamp=timestamp,\n                    unit=self._get_sensor_unit(sensor_type)\n                )\n                \n                # 处理读数\n                self.process_sensor_reading(reading)\n        \n        logger.info(f\"模拟数据生成完成\")\n    \n    def _get_sensor_unit(self, sensor_type: str) -> str:\n        \"\"\"获取传感器单位\"\"\"\n        unit_map = {\n            'pm25': 'μg/m³',\n            'pm10': 'μg/m³',\n            'wind_speed': 'm/s',\n            'wind_direction': '°',\n            'temperature': '°C',\n            'humidity': '%',\n            'pressure': 'hPa'\n        }\n        return unit_map.get(sensor_type, '')"