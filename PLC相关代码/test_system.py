#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC到AI-BOX系统测试脚本
用于验证系统各个组件的功能
"""

import asyncio
import time
import json
import sqlite3
import numpy as np
from datetime import datetime, timedelta
import unittest
from unittest.mock import Mock, patch
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PLC相关代码.plc_to_aibox_system import (
    PLCDataCollector, DataProcessor, AIBoxUploader, DataStorage,
    PLCToAIBoxSystem, PLCDataPoint, ProcessedData, AIBoxConfig
)

class TestPLCDataCollector(unittest.TestCase):
    """测试PLC数据采集器"""
    
    def setUp(self):
        """测试前准备"""
        self.plc_config = {
            'ip_address': '192.168.1.10',
            'port': 502,
            'device_id': 'TEST_PLC',
            'scan_rate': 1000
        }
        self.collector = PLCDataCollector(self.plc_config)
    
    def test_collector_initialization(self):
        """测试采集器初始化"""
        self.assertEqual(self.collector.plc_config['device_id'], 'TEST_PLC')
        self.assertFalse(self.collector.is_running)
        self.assertIsNotNone(self.collector.data_queue)
    
    def test_simulate_plc_data(self):
        """测试模拟PLC数据生成"""
        data_points = self.collector._simulate_plc_data()
        
        self.assertIsInstance(data_points, list)
        self.assertGreater(len(data_points), 0)
        
        for point in data_points:
            self.assertIsInstance(point, PLCDataPoint)
            self.assertIsInstance(point.value, (int, float))
            self.assertIn(point.parameter_name, 
                         ['vibration_x', 'vibration_y', 'temperature', 'pressure', 'flow_rate'])
    
    def test_data_queue_operations(self):
        """测试数据队列操作"""
        # 生成测试数据
        test_data = self.collector._simulate_plc_data()
        
        # 添加数据到队列
        for point in test_data:
            self.collector.data_queue.put(point)
        
        # 获取数据批次
        batch = self.collector.get_data_batch(3)
        self.assertEqual(len(batch), 3)
        
        for point in batch:
            self.assertIsInstance(point, PLCDataPoint)

class TestDataProcessor(unittest.TestCase):
    """测试数据处理器"""
    
    def setUp(self):
        """测试前准备"""
        self.config = {
            'buffer_size': 100,
            'downsample_factor': 1,
            'enable_fft': True
        }
        self.processor = DataProcessor(self.config)
    
    def create_test_data_points(self, count=10):
        """创建测试数据点"""
        points = []
        base_time = datetime.now()
        
        for i in range(count):
            timestamp = base_time + timedelta(seconds=i)
            points.extend([
                PLCDataPoint(timestamp, 'TEST_DEVICE', 'vibration_x', 
                           np.sin(2*np.pi*i/10) + np.random.normal(0, 0.1), 'mm/s'),
                PLCDataPoint(timestamp, 'TEST_DEVICE', 'vibration_y', 
                           np.cos(2*np.pi*i/10) + np.random.normal(0, 0.1), 'mm/s'),
                PLCDataPoint(timestamp, 'TEST_DEVICE', 'temperature', 
                           25 + np.random.normal(0, 1), '°C'),
                PLCDataPoint(timestamp, 'TEST_DEVICE', 'pressure', 
                           1013 + np.random.normal(0, 5), 'hPa'),
            ])
        
        return points
    
    def test_data_cleaning(self):
        """测试数据清洗"""
        # 创建包含异常值的测试数据
        points = self.create_test_data_points(5)
        
        # 添加异常数据点
        bad_point = PLCDataPoint(datetime.now(), 'TEST_DEVICE', 'temperature', 
                                float('inf'), '°C', quality='BAD')
        points.append(bad_point)
        
        cleaned_points = self.processor._clean_data(points)
        
        # 验证异常数据被过滤
        self.assertLess(len(cleaned_points), len(points))
        
        for point in cleaned_points:
            self.assertEqual(point.quality, 'GOOD')
            self.assertTrue(np.isfinite(point.value))
    
    def test_data_filtering(self):
        """测试数据滤波"""
        points = self.create_test_data_points(20)
        
        # 处理数据以建立历史缓冲区
        for i in range(0, len(points), 4):
            batch = points[i:i+4]
            self.processor.process_data_batch(batch)
        
        # 测试滤波功能
        test_data = {'vibration_x': 5.0, 'temperature': 30.0}
        filtered_data = self.processor._apply_filters('TEST_DEVICE', test_data)
        
        self.assertIn('vibration_x', filtered_data)
        self.assertIn('temperature', filtered_data)
        self.assertIsInstance(filtered_data['vibration_x'], float)
        self.assertIsInstance(filtered_data['temperature'], float)
    
    def test_fft_feature_extraction(self):
        """测试FFT特征提取"""
        points = self.create_test_data_points(50)
        
        # 处理数据以建立足够的历史缓冲区
        for i in range(0, len(points), 4):
            batch = points[i:i+4]
            self.processor.process_data_batch(batch)
        
        # 提取FFT特征
        fft_features = self.processor._extract_fft_features('TEST_DEVICE')
        
        if fft_features:  # 如果有振动数据
            for param_name, features in fft_features.items():
                self.assertIn('dominant_frequency', features)
                self.assertIn('total_power', features)
                self.assertIn('peak_power', features)
                self.assertIn('rms_value', features)
                
                # 验证特征值的合理性
                self.assertGreaterEqual(features['total_power'], 0)
                self.assertGreaterEqual(features['peak_power'], 0)
                self.assertGreaterEqual(features['rms_value'], 0)
    
    def test_derived_calculations(self):
        """测试衍生值计算"""
        raw_data = {
            'vibration_x': 2.0,
            'vibration_y': 3.0,
            'temperature': 25.0,
            'pressure': 1013.25,
            'flow_rate': 100.0
        }
        
        filtered_data = raw_data.copy()
        calculated = self.processor._calculate_derived_values(raw_data, filtered_data)
        
        # 验证计算结果
        if 'vibration_magnitude' in calculated:
            expected_magnitude = np.sqrt(2.0**2 + 3.0**2)
            self.assertAlmostEqual(calculated['vibration_magnitude'], expected_magnitude, places=2)
        
        if 'temperature_f' in calculated:
            expected_f = 25.0 * 9/5 + 32
            self.assertAlmostEqual(calculated['temperature_f'], expected_f, places=1)
    
    def test_data_quality_assessment(self):
        """测试数据质量评估"""
        points = self.create_test_data_points(10)
        raw_data = {
            'vibration_x': 1.0,
            'vibration_y': 1.5,
            'temperature': 25.0,
            'pressure': 1013.0,
            'flow_rate': 100.0
        }
        
        quality_score = self.processor._assess_data_quality(points, raw_data)
        
        self.assertIsInstance(quality_score, float)
        self.assertGreaterEqual(quality_score, 0.0)
        self.assertLessEqual(quality_score, 1.0)

class TestDataStorage(unittest.TestCase):
    """测试数据存储"""
    
    def setUp(self):
        """测试前准备"""
        self.test_db = "test_plc_data.db"
        self.storage = DataStorage(self.test_db)
    
    def tearDown(self):
        """测试后清理"""
        import os
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_database_initialization(self):
        """测试数据库初始化"""
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        self.assertIn('raw_data', tables)
        self.assertIn('processed_data', tables)
        
        conn.close()
    
    def test_store_raw_data(self):
        """测试存储原始数据"""
        test_points = [
            PLCDataPoint(datetime.now(), 'TEST_DEVICE', 'temperature', 25.0, '°C'),
            PLCDataPoint(datetime.now(), 'TEST_DEVICE', 'pressure', 1013.0, 'hPa')
        ]
        
        self.storage.store_raw_data(test_points)
        
        # 验证数据是否存储成功
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM raw_data")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 2)
    
    def test_store_processed_data(self):
        """测试存储处理后数据"""
        processed_data = [
            ProcessedData(
                timestamp=datetime.now(),
                device_id='TEST_DEVICE',
                raw_data={'temperature': 25.0},
                filtered_data={'temperature': 24.8},
                downsampled_data={'temperature': 24.8},
                fft_features={},
                calculated_values={'temperature_f': 76.64},
                quality_score=0.95
            )
        ]
        
        self.storage.store_processed_data(processed_data)
        
        # 验证数据是否存储成功
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM processed_data")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 1)

class TestAIBoxUploader(unittest.TestCase):
    """测试AI-BOX上传器"""
    
    def setUp(self):
        """测试前准备"""
        self.config = AIBoxConfig(
            ip_address="127.0.0.1",
            port=8080,
            api_endpoint="/api/test",
            auth_token="test_token",
            batch_size=10,
            upload_interval=5
        )
        self.uploader = AIBoxUploader(self.config)
    
    def test_uploader_initialization(self):
        """测试上传器初始化"""
        self.assertEqual(self.uploader.config.ip_address, "127.0.0.1")
        self.assertEqual(self.uploader.config.port, 8080)
        self.assertFalse(self.uploader.is_running)
    
    def test_add_data_for_upload(self):
        """测试添加上传数据"""
        test_data = [
            ProcessedData(
                timestamp=datetime.now(),
                device_id='TEST_DEVICE',
                raw_data={'temperature': 25.0},
                filtered_data={'temperature': 24.8},
                downsampled_data={'temperature': 24.8},
                fft_features={},
                calculated_values={},
                quality_score=0.95
            )
        ]
        
        initial_size = self.uploader.upload_queue.qsize()
        self.uploader.add_data_for_upload(test_data)
        final_size = self.uploader.upload_queue.qsize()
        
        self.assertEqual(final_size - initial_size, 1)

class SystemIntegrationTest(unittest.TestCase):
    """系统集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.plc_config = {
            'ip_address': '127.0.0.1',
            'port': 502,
            'device_id': 'TEST_PLC',
            'scan_rate': 1000
        }
        
        self.aibox_config = AIBoxConfig(
            ip_address="127.0.0.1",
            port=8080,
            api_endpoint="/api/test",
            batch_size=5,
            upload_interval=10
        )
        
        self.processing_config = {
            'buffer_size': 50,
            'enable_fft': True
        }
    
    def test_system_initialization(self):
        """测试系统初始化"""
        system = PLCToAIBoxSystem(
            self.plc_config, 
            self.aibox_config, 
            self.processing_config
        )
        
        self.assertIsNotNone(system.data_collector)
        self.assertIsNotNone(system.data_processor)
        self.assertIsNotNone(system.aibox_uploader)
        self.assertIsNotNone(system.data_storage)
        self.assertFalse(system.is_running)
    
    def test_system_status(self):
        """测试系统状态获取"""
        system = PLCToAIBoxSystem(
            self.plc_config, 
            self.aibox_config, 
            self.processing_config
        )
        
        status = system.get_system_status()
        
        self.assertIn('is_running', status)
        self.assertIn('collector_queue_size', status)
        self.assertIn('uploader_queue_size', status)
        self.assertIn('timestamp', status)

def run_performance_test():
    """运行性能测试"""
    print("\n" + "="*60)
    print("性能测试")
    print("="*60)
    
    # 测试数据处理性能
    processor = DataProcessor({'buffer_size': 1000})
    
    # 生成大量测试数据
    points = []
    base_time = datetime.now()
    
    print("生成测试数据...")
    for i in range(1000):
        timestamp = base_time + timedelta(seconds=i)
        points.extend([
            PLCDataPoint(timestamp, 'PERF_TEST', 'vibration_x', 
                        np.sin(2*np.pi*i/100) + np.random.normal(0, 0.1), 'mm/s'),
            PLCDataPoint(timestamp, 'PERF_TEST', 'temperature', 
                        25 + np.random.normal(0, 1), '°C'),
        ])
    
    # 测试处理性能
    print(f"处理 {len(points)} 个数据点...")
    start_time = time.time()
    
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i+batch_size]
        processor.process_data_batch(batch)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"处理时间: {processing_time:.2f} 秒")
    print(f"处理速度: {len(points)/processing_time:.0f} 点/秒")
    
    # 测试内存使用
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f"内存使用: {memory_info.rss / 1024 / 1024:.1f} MB")

def run_all_tests():
    """运行所有测试"""
    print("PLC到AI-BOX系统测试套件")
    print("="*60)
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    test_classes = [
        TestPLCDataCollector,
        TestDataProcessor,
        TestDataStorage,
        TestAIBoxUploader,
        SystemIntegrationTest
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 运行性能测试
    run_performance_test()
    
    # 输出测试结果摘要
    print("\n" + "="*60)
    print("测试结果摘要")
    print("="*60)
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n测试成功率: {success_rate:.1f}%")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
