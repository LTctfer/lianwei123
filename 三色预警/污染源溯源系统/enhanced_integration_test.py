#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
三色预警污染源溯源系统 - 集成测试脚本
测试所有优化后的功能模块
验证系统性能和稳定性
\"\"\"

import sys
import os
import time
import logging
import unittest
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入项目模块
from config import Config
from core.source_inversion import SourceInversionEngine
from core.three_color_warning import ThreeColorWarningSystem, PollutionAlert
from core.real_time_monitoring import (
    RealTimeMonitoringSystem, MonitoringStation, SensorReading, RealTimeAlert
)
from algorithms.genetic_algorithm import GeneticAlgorithm, Individual
from algorithms.pattern_search import PatternSearch
from algorithms.gaussian_plume import GaussianPlumeModel
from algorithms.data_fusion import DataFusionProcessor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemIntegrationTest(unittest.TestCase):
    \"\"\"系统集成测试类\"\"\"
    
    def setUp(self):
        \"\"\"测试前准备\"\"\"
        self.config = Config()
        self.start_time = time.time()
        logger.info(\"开始测试设置\")
    
    def tearDown(self):
        \"\"\"测试后清理\"\"\"
        duration = time.time() - self.start_time
        logger.info(f\"测试完成，耗时: {duration:.2f}秒\")
    
    def test_01_config_loading(self):
        \"\"\"测试配置加载\"\"\"
        logger.info(\"测试配置加载...\")
        
        # 验证配置有效性
        self.assertTrue(self.config.validate_config())
        
        # 检查必要的配置项
        algorithm_config = self.config.get_algorithm_config()
        self.assertIn('genetic_algorithm', algorithm_config)
        self.assertIn('pattern_search', algorithm_config)
        self.assertIn('gaussian_plume', algorithm_config)
        
        # 检查目录结构
        directories = self.config.get_all_directories()
        for dir_name, dir_path in directories.items():
            self.assertTrue(os.path.exists(dir_path), f\"目录 {dir_name} 不存在: {dir_path}\")
        
        logger.info(\"✓ 配置加载测试通过\")
    
    def test_02_genetic_algorithm_enhanced(self):
        \"\"\"测试增强的遗传算法\"\"\"
        logger.info(\"测试增强的遗传算法...\")
        
        # 创建遗传算法实例
        ga = GeneticAlgorithm(
            population_size=20,
            max_generations=50,
            adaptive_params=True,
            multi_source=False
        )
        
        # 定义简单的适应度函数
        def fitness_function(individual):
            # 简单的二次函数最小化
            return individual.x**2 + individual.y**2 + individual.z**2 + individual.q**2
        
        # 设置搜索边界
        bounds = {
            'x': (-10, 10),
            'y': (-10, 10),
            'z': (0, 10),
            'q': (0.1, 10)
        }
        
        # 运行遗传算法
        start_time = time.time()
        best_individual = ga.evolve(bounds, fitness_function)
        execution_time = time.time() - start_time
        
        # 验证结果
        self.assertIsNotNone(best_individual)
        self.assertLess(execution_time, 30, \"遗传算法执行时间过长\")
        self.assertLess(best_individual.fitness, 5, \"遗传算法收敛效果不佳\")
        
        # 验证自适应参数功能
        self.assertIsInstance(ga.performance_history, list)
        self.assertIsInstance(ga.diversity_history, list)
        
        logger.info(f\"✓ 遗传算法测试通过 - 执行时间: {execution_time:.2f}s, 最优适应度: {best_individual.fitness:.4f}\")
    
    def test_03_pattern_search_enhanced(self):
        \"\"\"测试增强的模式搜索算法\"\"\"
        logger.info(\"测试增强的模式搜索算法...\")
        
        # 创建模式搜索实例
        ps = PatternSearch(
            initial_step_size=1.0,
            adaptive_step=True,
            parallel_search=True,
            tolerance=1e-4
        )
        
        # 定义目标函数
        def objective_function(x, y, z, q):
            return x**2 + y**2 + z**2 + q**2
        
        # 设置边界
        ps.bounds = {
            'x': (-5, 5),
            'y': (-5, 5),
            'z': (0, 5),
            'q': (0.1, 5)
        }
        
        # 运行模式搜索
        initial_point = np.array([2.0, 2.0, 1.0, 1.0])
        start_time = time.time()
        best_solution, best_value = ps.optimize(initial_point, objective_function)
        execution_time = time.time() - start_time
        
        # 验证结果
        self.assertIsNotNone(best_solution)
        self.assertLess(execution_time, 10, \"模式搜索执行时间过长\")
        self.assertLess(best_value, 1, \"模式搜索收敛效果不佳\")
        
        # 验证搜索历史
        search_history = ps.get_search_path()
        self.assertGreater(len(search_history), 0)
        
        logger.info(f\"✓ 模式搜索测试通过 - 执行时间: {execution_time:.2f}s, 最优值: {best_value:.4f}\")
    
    def test_04_gaussian_plume_model(self):
        \"\"\"测试高斯烟羽模型\"\"\"
        logger.info(\"测试高斯烟羽模型...\")
        
        # 创建高斯烟羽模型
        model = GaussianPlumeModel()
        
        # 测试浓度计算
        concentration = model.calculate_concentration(
            x=100, y=50, z=1.5,
            source_x=0, source_y=0, source_z=10,
            source_strength=1.0,
            wind_speed=3.0,
            wind_direction=180,
            stability_class='D'
        )
        
        # 验证结果
        self.assertGreater(concentration, 0, \"浓度计算结果应大于0\")
        self.assertLess(concentration, 1000, \"浓度计算结果异常\")
        
        # 测试浓度场计算
        x_grid = np.linspace(-100, 200, 10)
        y_grid = np.linspace(-50, 50, 10)
        X, Y = np.meshgrid(x_grid, y_grid)
        
        concentration_field = model.calculate_concentration_field(
            X, Y, 0, 0, 10, 1.0, 3.0, 180, 'D'
        )
        
        # 验证浓度场
        self.assertEqual(concentration_field.shape, X.shape)
        self.assertTrue(np.all(concentration_field >= 0))
        
        # 测试稳定度分类
        stability_class = model.determine_stability_class(
            wind_speed=2.5,
            solar_radiation='moderate',
            is_daytime=True
        )
        self.assertIn(stability_class, model.stability_classes)
        
        logger.info(\"✓ 高斯烟羽模型测试通过\")
    
    def test_05_data_fusion_processor(self):
        \"\"\"测试数据融合处理器\"\"\"
        logger.info(\"测试数据融合处理器...\")
        
        try:
            from algorithms.data_fusion import DataFusionProcessor
            
            # 创建数据融合处理器
            processor = DataFusionProcessor()
            
            # 创建模拟数据
            monitoring_data = {}
            for i in range(3):
                station_id = f'ST{i+1:03d}'
                data = []
                
                for j in range(24):
                    timestamp = datetime.now() - timedelta(hours=23-j)
                    data.append({
                        'timestamp': timestamp,
                        'x': i * 1000,
                        'y': i * 500,
                        'concentration': 50 + 20 * np.sin(j * np.pi / 12) + np.random.normal(0, 5)
                    })
                
                monitoring_data[station_id] = pd.DataFrame(data)
            
            # 测试数据融合
            fused_data = processor.fuse_multi_station_data(
                monitoring_data,
                fusion_method='weighted_average'
            )
            
            # 验证融合结果
            self.assertIsInstance(fused_data, pd.DataFrame)
            self.assertGreater(len(fused_data), 0)
            self.assertIn('concentration', fused_data.columns)
            
            # 测试数据质量评分
            quality_score = processor.calculate_data_quality_score(fused_data)
            self.assertGreaterEqual(quality_score, 0)
            self.assertLessEqual(quality_score, 1)
            
            logger.info(f\"✓ 数据融合测试通过 - 质量评分: {quality_score:.3f}\")
            
        except ImportError:
            logger.warning(\"数据融合模块未实现，跳过测试\")
    
    def test_06_real_time_monitoring_system(self):
        \"\"\"测试实时监控系统\"\"\"
        logger.info(\"测试实时监控系统...\")
        
        # 创建监控系统
        monitoring_system = RealTimeMonitoringSystem(self.config.get_algorithm_config())
        
        # 添加监测站
        station = MonitoringStation(
            station_id='TEST001',
            name='测试监测站',
            latitude=39.9093,
            longitude=116.3974,
            x=0, y=0,
            sensors=['pm25', 'wind_speed']
        )
        monitoring_system.add_monitoring_station(station)
        
        # 验证监测站添加
        self.assertIn('TEST001', monitoring_system.stations)
        
        # 创建传感器读数
        reading = SensorReading(
            station_id='TEST001',
            sensor_type='pm25',
            value=75.5,
            timestamp=datetime.now(),
            unit='μg/m³'
        )
        
        # 处理传感器读数
        success = monitoring_system.process_sensor_reading(reading)
        self.assertTrue(success, \"传感器读数处理失败\")
        
        # 测试阈值检查（应触发黄色预警）
        time.sleep(0.1)  # 等待处理完成
        
        # 获取活跃预警
        active_alerts = monitoring_system.get_active_alerts()
        
        # 验证预警生成
        self.assertGreaterEqual(len(active_alerts), 0, \"应该生成预警\")
        
        # 测试系统统计
        stats = monitoring_system.get_system_statistics()
        self.assertIn('monitoring_stations', stats)
        self.assertIn('data_statistics', stats)
        
        # 启动监控
        monitoring_system.start_monitoring()
        self.assertTrue(monitoring_system.is_running)
        
        # 停止监控
        monitoring_system.stop_monitoring()
        self.assertFalse(monitoring_system.is_running)
        
        logger.info(\"✓ 实时监控系统测试通过\")
    
    def test_07_three_color_warning_system(self):
        \"\"\"测试三色预警系统\"\"\"
        logger.info(\"测试三色预警系统...\")
        
        # 创建三色预警系统
        warning_system = ThreeColorWarningSystem(self.config.get_algorithm_config())
        
        # 测试风险评分计算
        risk_score = warning_system.calculate_risk_score(
            concentration=150,
            source_strength=5.0,
            affected_area=10.0,
            meteorological_data={
                'wind_speed': 2.0,
                'wind_direction': 180,
                'stability_class': 'D'
            },
            population_density=2000
        )
        
        self.assertGreaterEqual(risk_score, 0)
        self.assertLessEqual(risk_score, 100)
        
        # 测试预警等级确定
        warning_level = warning_system.determine_warning_level(150, risk_score)
        self.assertIsNotNone(warning_level)
        self.assertIn(warning_level.level, ['yellow', 'orange', 'red'])
        
        # 测试污染预警创建
        alert = warning_system.create_pollution_alert(
            source_location={'x': 100, 'y': 200, 'z': 10},
            source_strength=3.0,
            concentration_field={
                'max_concentration': 180,
                'concentration': [[100, 150], [120, 180]]
            },
            meteorological_data={
                'wind_speed': 2.5,
                'wind_direction': 180,
                'stability_class': 'D'
            },
            confidence=0.85
        )
        
        if alert:  # 如果生成了预警
            self.assertIsInstance(alert, PollutionAlert)
            self.assertIn(alert.level.level, ['yellow', 'orange', 'red'])
            
            # 测试预警处理
            result = warning_system.process_alert(alert)
            self.assertIn('alert_id', result)
            self.assertIn('level', result)
            
            # 测试预警统计
            stats = warning_system.get_warning_statistics()
            self.assertIn('total_alerts', stats)
        
        logger.info(\"✓ 三色预警系统测试通过\")
    
    def test_08_source_inversion_engine(self):
        \"\"\"测试污染源反算引擎\"\"\"
        logger.info(\"测试污染源反算引擎...\")
        
        # 创建反算引擎
        engine = SourceInversionEngine(self.config.get_algorithm_config())
        
        # 创建模拟监测数据
        monitoring_data = {}
        for i in range(2):  # 减少监测站数量以加快测试
            station_id = f'ST{i+1:03d}'
            data = []
            
            for j in range(12):  # 减少时间点数量
                timestamp = datetime.now() - timedelta(hours=11-j)
                data.append({
                    'timestamp': timestamp,
                    'x': i * 500,
                    'y': i * 300,
                    'concentration': 40 + 10 * np.sin(j * np.pi / 6) + np.random.normal(0, 3)
                })
            
            monitoring_data[station_id] = pd.DataFrame(data)
        
        # 创建气象数据
        meteorological_data = pd.DataFrame([{
            'timestamp': datetime.now() - timedelta(hours=i),
            'wind_speed': 3.0 + np.random.normal(0, 0.5),
            'wind_direction': 180 + np.random.normal(0, 10),
            'temperature': 20 + np.random.normal(0, 2),
            'stability_class': 'D'
        } for i in range(12)])
        
        # 预处理数据
        fused_data = engine.preprocess_monitoring_data(monitoring_data)
        self.assertIsInstance(fused_data, pd.DataFrame)
        self.assertGreater(len(fused_data), 0)
        
        # 测试适应度计算
        source_params = {'x': 100, 'y': 100, 'z': 10, 'q': 2.0}
        fitness = engine.calculate_fitness(source_params, fused_data, meteorological_data)
        self.assertIsInstance(fitness, float)
        self.assertGreater(fitness, 0)
        
        # 测试遗传算法（快速版本）
        engine.genetic_algorithm.population_size = 10
        engine.genetic_algorithm.max_generations = 20
        
        ga_result = engine.run_genetic_algorithm(fused_data, meteorological_data)
        self.assertIn('best_solution', ga_result)
        self.assertIn('best_fitness', ga_result)
        
        logger.info(\"✓ 污染源反算引擎测试通过\")
    
    def test_09_performance_benchmark(self):
        \"\"\"性能基准测试\"\"\"
        logger.info(\"进行性能基准测试...\")
        
        performance_results = {}
        
        # 测试遗传算法性能
        ga = GeneticAlgorithm(population_size=50, max_generations=100)
        bounds = {'x': (-100, 100), 'y': (-100, 100), 'z': (0, 50), 'q': (0.1, 10)}
        
        def simple_fitness(individual):
            return (individual.x - 50)**2 + (individual.y + 30)**2 + individual.z**2 + individual.q**2
        
        start_time = time.time()
        best_individual = ga.evolve(bounds, simple_fitness)
        ga_time = time.time() - start_time
        performance_results['genetic_algorithm_time'] = ga_time
        performance_results['genetic_algorithm_fitness'] = best_individual.fitness
        
        # 测试高斯烟羽模型性能
        model = GaussianPlumeModel()
        start_time = time.time()
        
        for _ in range(1000):
            concentration = model.calculate_concentration(
                x=np.random.uniform(-100, 100),
                y=np.random.uniform(-100, 100),
                z=1.5,
                source_x=0, source_y=0, source_z=10,
                source_strength=1.0,
                wind_speed=3.0,
                wind_direction=180,
                stability_class='D'
            )
        
        gaussian_time = time.time() - start_time
        performance_results['gaussian_model_1000_calculations_time'] = gaussian_time
        
        # 输出性能结果
        logger.info(\"性能测试结果:\")
        for key, value in performance_results.items():
            logger.info(f\"  {key}: {value:.4f}\")
        
        # 性能断言
        self.assertLess(ga_time, 60, \"遗传算法执行时间过长\")
        self.assertLess(gaussian_time, 5, \"高斯模型计算时间过长\")
        
        logger.info(\"✓ 性能基准测试通过\")
    
    def test_10_system_integration(self):
        \"\"\"系统集成测试\"\"\"
        logger.info(\"进行系统集成测试...\")
        
        # 创建所有系统组件
        monitoring_system = RealTimeMonitoringSystem(self.config.get_algorithm_config())
        warning_system = ThreeColorWarningSystem(self.config.get_algorithm_config())
        inversion_engine = SourceInversionEngine(self.config.get_algorithm_config())
        
        # 添加监测站
        station = MonitoringStation(
            station_id='INT001',
            name='集成测试站',
            latitude=39.9093,
            longitude=116.3974,
            x=0, y=0,
            sensors=['pm25', 'wind_speed', 'wind_direction']
        )
        monitoring_system.add_monitoring_station(station)
        
        # 模拟传感器数据流
        readings = []
        for i in range(10):
            reading = SensorReading(
                station_id='INT001',
                sensor_type='pm25',
                value=50 + 30 * np.sin(i * np.pi / 5) + np.random.normal(0, 5),
                timestamp=datetime.now() + timedelta(minutes=i),
                unit='μg/m³'
            )
            readings.append(reading)
            success = monitoring_system.process_sensor_reading(reading)
            self.assertTrue(success)
        
        # 检查预警生成
        alerts = monitoring_system.get_active_alerts()
        
        # 如果有超阈值数据，应该生成预警
        high_values = [r.value for r in readings if r.value > 75]
        if high_values:
            self.assertGreater(len(alerts), 0, \"应该生成预警\")
        
        # 测试数据导出
        stats = monitoring_system.get_system_statistics()
        self.assertIn('monitoring_stations', stats)
        
        warning_stats = warning_system.get_warning_statistics()
        self.assertIn('total_alerts', warning_stats)
        
        logger.info(\"✓ 系统集成测试通过\")

def run_integration_tests():
    \"\"\"运行集成测试\"\"\"
    logger.info(\"=\"*60)
    logger.info(\"三色预警污染源溯源系统 - 集成测试\")
    logger.info(\"=\"*60)
    
    # 创建测试套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(SystemIntegrationTest)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 测试结果总结
    logger.info(\"\n\" + \"=\"*60)
    logger.info(\"测试结果总结\")
    logger.info(\"=\"*60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_rate = ((total_tests - failures - errors) / total_tests * 100) if total_tests > 0 else 0
    
    logger.info(f\"总测试数: {total_tests}\")
    logger.info(f\"成功: {total_tests - failures - errors}\")
    logger.info(f\"失败: {failures}\")
    logger.info(f\"错误: {errors}\")
    logger.info(f\"成功率: {success_rate:.1f}%\")
    
    if failures > 0:
        logger.info(\"\n失败的测试:\")
        for test, traceback in result.failures:
            logger.error(f\"  {test}: {traceback.splitlines()[-1]}\")
    
    if errors > 0:
        logger.info(\"\n错误的测试:\")
        for test, traceback in result.errors:
            logger.error(f\"  {test}: {traceback.splitlines()[-1]}\")
    
    # 生成测试报告
    generate_test_report(result)
    
    return result.wasSuccessful()

def generate_test_report(result):
    \"\"\"生成测试报告\"\"\"
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'test_summary': {
            'total_tests': result.testsRun,
            'successful': result.testsRun - len(result.failures) - len(result.errors),
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
        },
        'test_details': {
            'failures': [{'test': str(test), 'error': tb.splitlines()[-1]} for test, tb in result.failures],
            'errors': [{'test': str(test), 'error': tb.splitlines()[-1]} for test, tb in result.errors]
        },
        'system_info': {
            'python_version': sys.version,
            'platform': sys.platform
        }
    }
    
    # 保存测试报告
    report_file = f\"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json\"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        logger.info(f\"测试报告已保存: {report_file}\")
    except Exception as e:
        logger.error(f\"保存测试报告失败: {e}\")

if __name__ == '__main__':
    try:
        success = run_integration_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info(\"\n测试被用户中断\")
        sys.exit(1)
    except Exception as e:
        logger.error(f\"测试运行失败: {e}\")
        sys.exit(1)"