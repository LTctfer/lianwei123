#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC数据采集到算能AI-BOX系统
实现PLC现场数据采集、上传、数据清洗、滤波、降采样、特征提取（FFT）、公式计算等功能
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
import datetime
import json
import time
import logging
from scipy import signal, fft
from scipy.stats import zscore
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import sqlite3
import threading
import queue
import socket
import struct
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('plc_aibox_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PLCDataPoint:
    """PLC数据点结构"""
    timestamp: datetime.datetime
    device_id: str
    parameter_name: str
    value: float
    unit: str
    quality: str = "GOOD"  # GOOD, BAD, UNCERTAIN
    source_address: str = ""
    
@dataclass
class ProcessedData:
    """处理后的数据结构"""
    timestamp: datetime.datetime
    device_id: str
    raw_data: Dict[str, float]
    filtered_data: Dict[str, float]
    downsampled_data: Dict[str, float]
    fft_features: Dict[str, Dict[str, float]]
    calculated_values: Dict[str, float]
    quality_score: float

@dataclass
class AIBoxConfig:
    """AI-BOX配置"""
    ip_address: str = "192.168.1.100"
    port: int = 8080
    api_endpoint: str = "/api/data/upload"
    auth_token: str = ""
    batch_size: int = 100
    upload_interval: int = 30  # 秒

class PLCDataCollector:
    """PLC数据采集器"""
    
    def __init__(self, plc_config: Dict[str, Any]):
        self.plc_config = plc_config
        self.data_queue = queue.Queue(maxsize=10000)
        self.is_running = False
        self.collection_thread = None
        
    def start_collection(self):
        """启动数据采集"""
        self.is_running = True
        self.collection_thread = threading.Thread(target=self._collect_data_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        logger.info("PLC数据采集已启动")
        
    def stop_collection(self):
        """停止数据采集"""
        self.is_running = False
        if self.collection_thread:
            self.collection_thread.join()
        logger.info("PLC数据采集已停止")
        
    def _collect_data_loop(self):
        """数据采集循环"""
        while self.is_running:
            try:
                # 模拟PLC数据采集（实际应用中需要根据具体PLC协议实现）
                data_points = self._simulate_plc_data()
                
                for point in data_points:
                    if not self.data_queue.full():
                        self.data_queue.put(point)
                    else:
                        logger.warning("数据队列已满，丢弃数据点")
                        
                time.sleep(1)  # 采集间隔
                
            except Exception as e:
                logger.error(f"数据采集错误: {e}")
                time.sleep(5)
                
    def _simulate_plc_data(self) -> List[PLCDataPoint]:
        """模拟PLC数据（实际应用中替换为真实PLC通信）"""
        timestamp = datetime.datetime.now()
        device_id = "PLC_001"
        
        # 模拟振动、温度、压力等传感器数据
        data_points = [
            PLCDataPoint(timestamp, device_id, "vibration_x", 
                        np.random.normal(0, 1) + 0.5*np.sin(2*np.pi*time.time()/10), "mm/s"),
            PLCDataPoint(timestamp, device_id, "vibration_y", 
                        np.random.normal(0, 0.8) + 0.3*np.cos(2*np.pi*time.time()/15), "mm/s"),
            PLCDataPoint(timestamp, device_id, "temperature", 
                        np.random.normal(25, 2), "°C"),
            PLCDataPoint(timestamp, device_id, "pressure", 
                        np.random.normal(1013, 10), "hPa"),
            PLCDataPoint(timestamp, device_id, "flow_rate", 
                        np.random.normal(100, 5), "L/min"),
        ]
        
        return data_points
        
    def get_data_batch(self, batch_size: int = 100) -> List[PLCDataPoint]:
        """获取一批数据"""
        batch = []
        for _ in range(min(batch_size, self.data_queue.qsize())):
            try:
                batch.append(self.data_queue.get_nowait())
            except queue.Empty:
                break
        return batch

class DataProcessor:
    """数据处理器 - 实现数据清洗、滤波、降采样、特征提取等功能"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.scaler = StandardScaler()
        self.min_max_scaler = MinMaxScaler()
        self.history_buffer = {}  # 存储历史数据用于滤波和FFT
        self.buffer_size = self.config.get('buffer_size', 1000)
        
    def process_data_batch(self, data_points: List[PLCDataPoint]) -> List[ProcessedData]:
        """处理一批数据"""
        if not data_points:
            return []
            
        # 按设备和时间戳分组
        grouped_data = self._group_data_by_device_time(data_points)
        
        processed_results = []
        for (device_id, timestamp), points in grouped_data.items():
            try:
                processed = self._process_single_group(device_id, timestamp, points)
                if processed:
                    processed_results.append(processed)
            except Exception as e:
                logger.error(f"处理数据组错误 {device_id}-{timestamp}: {e}")
                
        return processed_results
        
    def _group_data_by_device_time(self, data_points: List[PLCDataPoint]) -> Dict[Tuple[str, datetime.datetime], List[PLCDataPoint]]:
        """按设备ID和时间戳分组数据"""
        grouped = {}
        for point in data_points:
            # 将时间戳舍入到秒
            rounded_time = point.timestamp.replace(microsecond=0)
            key = (point.device_id, rounded_time)
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(point)
            
        return grouped
        
    def _process_single_group(self, device_id: str, timestamp: datetime.datetime, 
                            points: List[PLCDataPoint]) -> Optional[ProcessedData]:
        """处理单个数据组"""
        # 1. 数据清洗
        cleaned_points = self._clean_data(points)
        if not cleaned_points:
            return None
            
        # 2. 构建原始数据字典
        raw_data = {point.parameter_name: point.value for point in cleaned_points}
        
        # 3. 更新历史缓冲区
        self._update_history_buffer(device_id, timestamp, raw_data)
        
        # 4. 数据滤波
        filtered_data = self._apply_filters(device_id, raw_data)
        
        # 5. 降采样（如果需要）
        downsampled_data = self._downsample_data(device_id, filtered_data)
        
        # 6. FFT特征提取
        fft_features = self._extract_fft_features(device_id)
        
        # 7. 公式计算
        calculated_values = self._calculate_derived_values(raw_data, filtered_data)
        
        # 8. 质量评估
        quality_score = self._assess_data_quality(cleaned_points, raw_data)
        
        return ProcessedData(
            timestamp=timestamp,
            device_id=device_id,
            raw_data=raw_data,
            filtered_data=filtered_data,
            downsampled_data=downsampled_data,
            fft_features=fft_features,
            calculated_values=calculated_values,
            quality_score=quality_score
        )
        
    def _clean_data(self, points: List[PLCDataPoint]) -> List[PLCDataPoint]:
        """数据清洗 - 去除异常值和无效数据"""
        cleaned = []
        
        for point in points:
            # 检查数据质量标志
            if point.quality != "GOOD":
                continue
                
            # 检查数值有效性
            if not isinstance(point.value, (int, float)) or np.isnan(point.value) or np.isinf(point.value):
                continue
                
            # 基于参数类型的范围检查
            if not self._is_value_in_valid_range(point.parameter_name, point.value):
                continue
                
            cleaned.append(point)
            
        return cleaned
        
    def _is_value_in_valid_range(self, parameter_name: str, value: float) -> bool:
        """检查数值是否在有效范围内"""
        ranges = {
            'temperature': (-50, 150),
            'pressure': (800, 1200),
            'vibration_x': (-100, 100),
            'vibration_y': (-100, 100),
            'flow_rate': (0, 1000),
        }
        
        if parameter_name in ranges:
            min_val, max_val = ranges[parameter_name]
            return min_val <= value <= max_val
            
        return True  # 未知参数默认通过
        
    def _update_history_buffer(self, device_id: str, timestamp: datetime.datetime, data: Dict[str, float]):
        """更新历史数据缓冲区"""
        if device_id not in self.history_buffer:
            self.history_buffer[device_id] = {}
            
        for param_name, value in data.items():
            if param_name not in self.history_buffer[device_id]:
                self.history_buffer[device_id][param_name] = []
                
            # 添加新数据点
            self.history_buffer[device_id][param_name].append((timestamp, value))
            
            # 保持缓冲区大小
            if len(self.history_buffer[device_id][param_name]) > self.buffer_size:
                self.history_buffer[device_id][param_name].pop(0)

    def _apply_filters(self, device_id: str, raw_data: Dict[str, float]) -> Dict[str, float]:
        """应用数字滤波器"""
        filtered_data = {}

        for param_name, value in raw_data.items():
            if device_id not in self.history_buffer or param_name not in self.history_buffer[device_id]:
                filtered_data[param_name] = value
                continue

            history = self.history_buffer[device_id][param_name]
            if len(history) < 5:  # 需要足够的历史数据
                filtered_data[param_name] = value
                continue

            # 提取数值序列
            values = [item[1] for item in history[-20:]]  # 使用最近20个点

            # 根据参数类型选择滤波方法
            if 'vibration' in param_name.lower():
                # 振动信号使用带通滤波
                filtered_value = self._apply_bandpass_filter(values, param_name)
            elif 'temperature' in param_name.lower():
                # 温度使用低通滤波
                filtered_value = self._apply_lowpass_filter(values)
            else:
                # 其他参数使用移动平均
                filtered_value = self._apply_moving_average(values)

            filtered_data[param_name] = filtered_value

        return filtered_data

    def _apply_bandpass_filter(self, values: List[float], param_name: str) -> float:
        """应用带通滤波器（用于振动信号）"""
        if len(values) < 10:
            return values[-1]

        # 设计带通滤波器
        fs = 1.0  # 假设采样频率1Hz
        lowcut = 0.1
        highcut = 0.4

        try:
            # 使用Butterworth带通滤波器
            sos = signal.butter(4, [lowcut, highcut], btype='band', fs=fs, output='sos')
            filtered = signal.sosfilt(sos, values)
            return float(filtered[-1])
        except:
            return values[-1]

    def _apply_lowpass_filter(self, values: List[float]) -> float:
        """应用低通滤波器"""
        if len(values) < 5:
            return values[-1]

        try:
            # 使用Butterworth低通滤波器
            fs = 1.0
            cutoff = 0.1
            sos = signal.butter(4, cutoff, btype='low', fs=fs, output='sos')
            filtered = signal.sosfilt(sos, values)
            return float(filtered[-1])
        except:
            return values[-1]

    def _apply_moving_average(self, values: List[float], window: int = 5) -> float:
        """应用移动平均滤波"""
        if len(values) < window:
            return np.mean(values)
        return np.mean(values[-window:])

    def _downsample_data(self, device_id: str, filtered_data: Dict[str, float]) -> Dict[str, float]:
        """数据降采样"""
        # 简单的降采样策略：每N个点取一个
        downsample_factor = self.config.get('downsample_factor', 1)

        if downsample_factor <= 1:
            return filtered_data.copy()

        downsampled = {}
        for param_name, value in filtered_data.items():
            if device_id not in self.history_buffer or param_name not in self.history_buffer[device_id]:
                downsampled[param_name] = value
                continue

            history_len = len(self.history_buffer[device_id][param_name])
            if history_len % downsample_factor == 0:
                downsampled[param_name] = value
            # 否则跳过这个数据点

        return downsampled

    def _extract_fft_features(self, device_id: str) -> Dict[str, Dict[str, float]]:
        """提取FFT特征（主要用于振动分析）"""
        fft_features = {}

        if device_id not in self.history_buffer:
            return fft_features

        for param_name, history in self.history_buffer[device_id].items():
            if 'vibration' not in param_name.lower() or len(history) < 64:
                continue

            # 提取最近的数据用于FFT分析
            values = [item[1] for item in history[-128:]]  # 使用最近128个点

            try:
                # 计算FFT
                fft_result = fft.fft(values)
                freqs = fft.fftfreq(len(values), d=1.0)  # 假设采样间隔1秒

                # 计算功率谱密度
                psd = np.abs(fft_result) ** 2

                # 提取特征
                features = {
                    'dominant_frequency': float(freqs[np.argmax(psd[1:len(psd)//2]) + 1]),
                    'total_power': float(np.sum(psd)),
                    'peak_power': float(np.max(psd[1:len(psd)//2])),
                    'spectral_centroid': float(np.sum(freqs[:len(freqs)//2] * psd[:len(psd)//2]) / np.sum(psd[:len(psd)//2])),
                    'rms_value': float(np.sqrt(np.mean(np.array(values)**2))),
                }

                fft_features[param_name] = features

            except Exception as e:
                logger.warning(f"FFT特征提取失败 {param_name}: {e}")

        return fft_features

    def _calculate_derived_values(self, raw_data: Dict[str, float],
                                filtered_data: Dict[str, float]) -> Dict[str, float]:
        """计算衍生值和公式计算"""
        calculated = {}

        try:
            # 振动烈度计算（如果有振动数据）
            if 'vibration_x' in filtered_data and 'vibration_y' in filtered_data:
                vib_x = filtered_data['vibration_x']
                vib_y = filtered_data['vibration_y']
                calculated['vibration_magnitude'] = np.sqrt(vib_x**2 + vib_y**2)
                calculated['vibration_angle'] = np.arctan2(vib_y, vib_x) * 180 / np.pi

            # 温度相关计算
            if 'temperature' in filtered_data:
                temp_c = filtered_data['temperature']
                calculated['temperature_f'] = temp_c * 9/5 + 32  # 华氏温度
                calculated['temperature_k'] = temp_c + 273.15    # 开尔文温度

            # 压力相关计算
            if 'pressure' in filtered_data:
                pressure_hpa = filtered_data['pressure']
                calculated['pressure_bar'] = pressure_hpa / 1000  # 转换为bar
                calculated['pressure_psi'] = pressure_hpa * 0.0145038  # 转换为psi

            # 流量相关计算
            if 'flow_rate' in filtered_data and 'pressure' in filtered_data:
                flow = filtered_data['flow_rate']
                pressure = filtered_data['pressure']
                # 简化的流量系数计算
                calculated['flow_coefficient'] = flow / np.sqrt(pressure / 1013.25)

            # 设备效率指标（示例）
            if 'temperature' in filtered_data and 'flow_rate' in filtered_data:
                temp = filtered_data['temperature']
                flow = filtered_data['flow_rate']
                # 简化的效率计算
                calculated['thermal_efficiency'] = min(100, max(0, 100 - abs(temp - 25) * 2 - abs(flow - 100) * 0.5))

        except Exception as e:
            logger.error(f"衍生值计算错误: {e}")

        return calculated

    def _assess_data_quality(self, points: List[PLCDataPoint], raw_data: Dict[str, float]) -> float:
        """评估数据质量"""
        if not points:
            return 0.0

        quality_score = 1.0

        # 检查数据完整性
        expected_params = ['vibration_x', 'vibration_y', 'temperature', 'pressure', 'flow_rate']
        missing_params = set(expected_params) - set(raw_data.keys())
        completeness = 1.0 - len(missing_params) / len(expected_params)

        # 检查数据质量标志
        good_quality_count = sum(1 for p in points if p.quality == "GOOD")
        quality_ratio = good_quality_count / len(points) if points else 0

        # 检查数值稳定性（变异系数）
        stability_score = 1.0
        for param_name, value in raw_data.items():
            if param_name in self.history_buffer.get(points[0].device_id, {}):
                history = self.history_buffer[points[0].device_id][param_name]
                if len(history) >= 10:
                    recent_values = [item[1] for item in history[-10:]]
                    cv = np.std(recent_values) / (np.mean(recent_values) + 1e-6)
                    stability_score *= max(0.1, 1.0 - min(1.0, cv))

        # 综合质量评分
        quality_score = (completeness * 0.4 + quality_ratio * 0.3 + stability_score * 0.3)

        return float(quality_score)

class AIBoxUploader:
    """AI-BOX数据上传器"""

    def __init__(self, config: AIBoxConfig):
        self.config = config
        self.upload_queue = queue.Queue(maxsize=5000)
        self.is_running = False
        self.upload_thread = None
        self.session = None

    async def start_uploader(self):
        """启动上传器"""
        self.is_running = True
        self.session = aiohttp.ClientSession()
        self.upload_thread = threading.Thread(target=self._upload_loop)
        self.upload_thread.daemon = True
        self.upload_thread.start()
        logger.info("AI-BOX上传器已启动")

    def stop_uploader(self):
        """停止上传器"""
        self.is_running = False
        if self.upload_thread:
            self.upload_thread.join()
        if self.session:
            asyncio.create_task(self.session.close())
        logger.info("AI-BOX上传器已停止")

    def add_data_for_upload(self, processed_data: List[ProcessedData]):
        """添加数据到上传队列"""
        for data in processed_data:
            if not self.upload_queue.full():
                self.upload_queue.put(data)
            else:
                logger.warning("上传队列已满，丢弃数据")

    def _upload_loop(self):
        """上传循环"""
        while self.is_running:
            try:
                # 收集一批数据
                batch = []
                for _ in range(min(self.config.batch_size, self.upload_queue.qsize())):
                    try:
                        batch.append(self.upload_queue.get_nowait())
                    except queue.Empty:
                        break

                if batch:
                    asyncio.run(self._upload_batch(batch))

                time.sleep(self.config.upload_interval)

            except Exception as e:
                logger.error(f"上传循环错误: {e}")
                time.sleep(10)

    async def _upload_batch(self, batch: List[ProcessedData]):
        """上传一批数据到AI-BOX"""
        try:
            # 构建上传数据
            upload_data = {
                'timestamp': datetime.datetime.now().isoformat(),
                'batch_size': len(batch),
                'data': []
            }

            for data in batch:
                data_dict = {
                    'timestamp': data.timestamp.isoformat(),
                    'device_id': data.device_id,
                    'raw_data': data.raw_data,
                    'filtered_data': data.filtered_data,
                    'downsampled_data': data.downsampled_data,
                    'fft_features': data.fft_features,
                    'calculated_values': data.calculated_values,
                    'quality_score': data.quality_score
                }
                upload_data['data'].append(data_dict)

            # 发送HTTP请求
            url = f"http://{self.config.ip_address}:{self.config.port}{self.config.api_endpoint}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.config.auth_token}' if self.config.auth_token else None
            }
            headers = {k: v for k, v in headers.items() if v is not None}

            async with self.session.post(url, json=upload_data, headers=headers, timeout=30) as response:
                if response.status == 200:
                    logger.info(f"成功上传 {len(batch)} 条数据到AI-BOX")
                else:
                    logger.error(f"上传失败，状态码: {response.status}, 响应: {await response.text()}")

        except Exception as e:
            logger.error(f"上传数据到AI-BOX失败: {e}")
            # 将失败的数据重新放回队列（可选）
            for data in batch:
                if not self.upload_queue.full():
                    self.upload_queue.put(data)

class DataStorage:
    """本地数据存储"""

    def __init__(self, db_path: str = "plc_data.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建原始数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS raw_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                device_id TEXT NOT NULL,
                parameter_name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                quality TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建处理后数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                device_id TEXT NOT NULL,
                raw_data TEXT,
                filtered_data TEXT,
                downsampled_data TEXT,
                fft_features TEXT,
                calculated_values TEXT,
                quality_score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_raw_timestamp ON raw_data(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_raw_device ON raw_data(device_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_processed_timestamp ON processed_data(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_processed_device ON processed_data(device_id)')

        conn.commit()
        conn.close()

    def store_raw_data(self, data_points: List[PLCDataPoint]):
        """存储原始数据"""
        if not data_points:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            for point in data_points:
                cursor.execute('''
                    INSERT INTO raw_data (timestamp, device_id, parameter_name, value, unit, quality)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    point.timestamp.isoformat(),
                    point.device_id,
                    point.parameter_name,
                    point.value,
                    point.unit,
                    point.quality
                ))

            conn.commit()
            logger.debug(f"存储了 {len(data_points)} 条原始数据")

        except Exception as e:
            logger.error(f"存储原始数据失败: {e}")
            conn.rollback()
        finally:
            conn.close()

    def store_processed_data(self, processed_data: List[ProcessedData]):
        """存储处理后数据"""
        if not processed_data:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            for data in processed_data:
                cursor.execute('''
                    INSERT INTO processed_data
                    (timestamp, device_id, raw_data, filtered_data, downsampled_data,
                     fft_features, calculated_values, quality_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.timestamp.isoformat(),
                    data.device_id,
                    json.dumps(data.raw_data),
                    json.dumps(data.filtered_data),
                    json.dumps(data.downsampled_data),
                    json.dumps(data.fft_features),
                    json.dumps(data.calculated_values),
                    data.quality_score
                ))

            conn.commit()
            logger.debug(f"存储了 {len(processed_data)} 条处理后数据")

        except Exception as e:
            logger.error(f"存储处理后数据失败: {e}")
            conn.rollback()
        finally:
            conn.close()

class PLCToAIBoxSystem:
    """PLC到AI-BOX完整系统"""

    def __init__(self, plc_config: Dict[str, Any], aibox_config: AIBoxConfig,
                 processing_config: Dict[str, Any] = None):
        self.plc_config = plc_config
        self.aibox_config = aibox_config
        self.processing_config = processing_config or {}

        # 初始化各个组件
        self.data_collector = PLCDataCollector(plc_config)
        self.data_processor = DataProcessor(processing_config)
        self.aibox_uploader = AIBoxUploader(aibox_config)
        self.data_storage = DataStorage()

        self.is_running = False
        self.main_thread = None

    async def start_system(self):
        """启动整个系统"""
        logger.info("启动PLC到AI-BOX系统...")

        # 启动各个组件
        self.data_collector.start_collection()
        await self.aibox_uploader.start_uploader()

        self.is_running = True
        self.main_thread = threading.Thread(target=self._main_processing_loop)
        self.main_thread.daemon = True
        self.main_thread.start()

        logger.info("PLC到AI-BOX系统启动完成")

    def stop_system(self):
        """停止整个系统"""
        logger.info("停止PLC到AI-BOX系统...")

        self.is_running = False

        # 停止各个组件
        self.data_collector.stop_collection()
        self.aibox_uploader.stop_uploader()

        if self.main_thread:
            self.main_thread.join()

        logger.info("PLC到AI-BOX系统已停止")

    def _main_processing_loop(self):
        """主处理循环"""
        while self.is_running:
            try:
                # 从PLC采集器获取数据
                raw_data_batch = self.data_collector.get_data_batch(100)

                if raw_data_batch:
                    # 存储原始数据
                    self.data_storage.store_raw_data(raw_data_batch)

                    # 数据处理
                    processed_data = self.data_processor.process_data_batch(raw_data_batch)

                    if processed_data:
                        # 存储处理后数据
                        self.data_storage.store_processed_data(processed_data)

                        # 添加到上传队列
                        self.aibox_uploader.add_data_for_upload(processed_data)

                        logger.info(f"处理了 {len(processed_data)} 条数据")

                time.sleep(1)  # 处理间隔

            except Exception as e:
                logger.error(f"主处理循环错误: {e}")
                time.sleep(5)

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'is_running': self.is_running,
            'collector_queue_size': self.data_collector.data_queue.qsize(),
            'uploader_queue_size': self.aibox_uploader.upload_queue.qsize(),
            'timestamp': datetime.datetime.now().isoformat()
        }

# 使用示例和配置
def create_demo_config():
    """创建演示配置"""

    # PLC配置
    plc_config = {
        'ip_address': '192.168.1.10',
        'port': 502,
        'device_id': 'PLC_001',
        'scan_rate': 1000,  # ms
        'parameters': [
            {'name': 'vibration_x', 'address': 'DB1.DBD0', 'type': 'REAL'},
            {'name': 'vibration_y', 'address': 'DB1.DBD4', 'type': 'REAL'},
            {'name': 'temperature', 'address': 'DB1.DBD8', 'type': 'REAL'},
            {'name': 'pressure', 'address': 'DB1.DBD12', 'type': 'REAL'},
            {'name': 'flow_rate', 'address': 'DB1.DBD16', 'type': 'REAL'},
        ]
    }

    # AI-BOX配置
    aibox_config = AIBoxConfig(
        ip_address="192.168.1.100",
        port=8080,
        api_endpoint="/api/data/upload",
        auth_token="your_auth_token_here",
        batch_size=50,
        upload_interval=30
    )

    # 数据处理配置
    processing_config = {
        'buffer_size': 1000,
        'downsample_factor': 1,
        'enable_fft': True,
        'fft_window_size': 128,
        'filter_config': {
            'vibration': {'type': 'bandpass', 'low': 0.1, 'high': 0.4},
            'temperature': {'type': 'lowpass', 'cutoff': 0.1},
            'default': {'type': 'moving_average', 'window': 5}
        }
    }

    return plc_config, aibox_config, processing_config

async def main():
    """主函数示例"""
    print("PLC到AI-BOX数据采集系统演示")
    print("=" * 50)

    # 创建配置
    plc_config, aibox_config, processing_config = create_demo_config()

    # 创建系统
    system = PLCToAIBoxSystem(plc_config, aibox_config, processing_config)

    try:
        # 启动系统
        await system.start_system()

        # 运行一段时间
        print("系统运行中，按Ctrl+C停止...")
        for i in range(60):  # 运行60秒
            status = system.get_system_status()
            print(f"状态更新 {i+1}/60: "
                  f"采集队列: {status['collector_queue_size']}, "
                  f"上传队列: {status['uploader_queue_size']}")
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n收到停止信号...")
    finally:
        # 停止系统
        system.stop_system()
        print("系统已停止")

if __name__ == "__main__":
    asyncio.run(main())
