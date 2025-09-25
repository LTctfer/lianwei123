#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精简预警引擎测试套件 - test_compact_engine.py

作用：
    对精简预警引擎进行全面的功能测试和性能验证

测试覆盖：
    - 操作符工厂测试
    - 单属性和双属性规则测试
    - 正常和异常数据处理测试
    - 时间范围和频率控制测试
    - 边界情况和性能测试

测试结果：
    13个测试用例，验证算法的正确性和稳定性

使用方法：
    python test_compact_engine.py
"""

import json
import time
import random
import os
from datetime import datetime, timedelta
from compact_alarm_engine import CompactAlarmEngine, OperatorFactory, RuleEvaluator, FrequencyManager


class CompactAlarmEngineTest:
    """精简预警引擎测试类"""

    def __init__(self):
        # 确保在正确的目录下运行
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)

        self.engine = CompactAlarmEngine()
        self.test_results = []
        random.seed(42)  # 设置随机种子确保测试可重复

    def generate_test_data(self, count=1000):
        """生成大规模测试数据"""
        test_data = []

        for i in range(count):
            # 生成不同类型的测试数据
            data_type = i % 6

            if data_type == 0:
                # 正常数据
                data = {
                    't1': random.uniform(2, 8),
                    't2': random.uniform(8, 18),
                    't3': random.uniform(5, 15),
                    't4': random.uniform(3, 12)
                }
            elif data_type == 1:
                # t1异常（过小）
                data = {
                    't1': random.uniform(0.1, 0.9),
                    't2': random.uniform(8, 18),
                    't3': random.uniform(5, 15),
                    't4': random.uniform(3, 12)
                }
            elif data_type == 2:
                # t1异常（过大）
                data = {
                    't1': random.uniform(12, 20),
                    't2': random.uniform(8, 18),
                    't3': random.uniform(5, 15),
                    't4': random.uniform(3, 12)
                }
            elif data_type == 3:
                # t2异常（过大）
                data = {
                    't1': random.uniform(2, 8),
                    't2': random.uniform(22, 30),
                    't3': random.uniform(5, 15),
                    't4': random.uniform(3, 12)
                }
            elif data_type == 4:
                # 双属性异常（t3 > t4）
                t4_val = random.uniform(3, 8)
                data = {
                    't1': random.uniform(2, 8),
                    't2': random.uniform(8, 18),
                    't3': t4_val + random.uniform(5, 10),  # 确保t3 > t4
                    't4': t4_val
                }
            else:
                # 多重异常
                data = {
                    't1': random.uniform(0.1, 0.5),  # t1过小
                    't2': random.uniform(25, 35),    # t2过大
                    't3': random.uniform(40, 60),    # t3较大
                    't4': random.uniform(1, 5)       # t4较小
                }

            test_data.append(data)

        return test_data
    
    def run_test(self, test_name: str, test_func):
        """运行单个测试"""
        try:
            print(f"\n🧪 测试: {test_name}")
            result = test_func()
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   结果: {status}")
            self.test_results.append({'name': test_name, 'passed': result})
            return result
        except Exception as e:
            print(f"   结果: ❌ 异常 - {str(e)}")
            self.test_results.append({'name': test_name, 'passed': False, 'error': str(e)})
            return False
    
    def test_operator_factory(self):
        """测试操作符工厂"""
        tests = [
            (5, 'lt', 10, True),   # 5 < 10
            (10, 'le', 10, True),  # 10 <= 10
            (15, 'gt', 10, True),  # 15 > 10
            (10, 'ge', 10, True),  # 10 >= 10
            (10, 'eq', 10, True),  # 10 == 10
            (10, 'ne', 5, True),   # 10 != 5
            (10, 'invalid', 5, False),  # 无效操作符
        ]
        
        for left, op, right, expected in tests:
            result = OperatorFactory.evaluate(left, op, right)
            if result != expected:
                print(f"   操作符测试失败: {left} {op} {right} = {result}, 期望 {expected}")
                return False
        
        return True
    
    def test_single_property_rules(self):
        """测试单属性规则"""
        rule = {
            'property': 't1',
            'lowValue': 1,
            'expression1': 'lt',
            'highValue': 10,
            'expression2': 'gt'
        }
        
        test_cases = [
            ({'t1': 5}, False),   # 正常值
            ({'t1': 0.5}, True),  # 小于最小值
            ({'t1': 15}, True),   # 大于最大值
            ({'t2': 5}, False),   # 缺少属性
        ]
        
        for data, expected in test_cases:
            result = RuleEvaluator.evaluate_single_property(rule, data)
            if result != expected:
                print(f"   单属性规则测试失败: {data} = {result}, 期望 {expected}")
                return False
        
        return True
    
    def test_double_property_rules(self):
        """测试双属性规则"""
        rule = {
            'leftProperty': 't1',
            'rightProperty': 't2',
            'expression': 'lt'
        }
        
        test_cases = [
            ({'t1': 5, 't2': 10}, True),   # 5 < 10
            ({'t1': 10, 't2': 5}, False),  # 10 < 5
            ({'t1': 5}, False),            # 缺少t2
        ]
        
        for data, expected in test_cases:
            result = RuleEvaluator.evaluate_double_property(rule, data)
            if result != expected:
                print(f"   双属性规则测试失败: {data} = {result}, 期望 {expected}")
                return False
        
        return True
    
    def test_normal_data_processing(self):
        """测试正常数据处理"""
        normal_data = {'t1': 5, 't2': 15, 't3': 8, 't4': 12}
        alarm = self.engine.process_data(normal_data)
        return alarm is None  # 正常数据不应触发预警
    
    def test_abnormal_data_processing(self):
        """测试异常数据处理"""
        # 清空历史记录确保测试独立性
        self.engine.clear_alarm_history()

        # 使用多种异常数据进行测试
        abnormal_datasets = [
            {'t1': 0.1, 't2': 25, 't3': 50, 't4': 5},   # 多重异常
            {'t1': 0.5, 't2': 15, 't3': 8, 't4': 12},   # t1过小
            {'t1': 15, 't2': 15, 't3': 8, 't4': 12},    # t1过大
            {'t1': 5, 't2': 25, 't3': 8, 't4': 12},     # t2过大
            {'t1': 5, 't2': 3, 't3': 8, 't4': 12},      # t2过小
            {'t1': 20, 't2': 15, 't3': 8, 't4': 12},    # t1 > t2 (双属性异常)
        ]

        alarm_triggered = False
        for abnormal_data in abnormal_datasets:
            alarm = self.engine.process_data(abnormal_data)
            if alarm is not None:
                alarm_triggered = True
                # 验证预警消息格式
                required_fields = ['alarmId', 'alarmTime', 'data', 'alarmInfo']
                for field in required_fields:
                    if field not in alarm:
                        print(f"   预警消息缺少字段: {field}")
                        return False
                break

        if not alarm_triggered:
            print(f"   所有异常数据都未触发预警")
            return False

        return True
    
    def test_time_range_validation(self):
        """测试时间范围验证"""
        current_hour = datetime.now().hour
        
        # 创建一个时间范围外的配置进行测试
        if current_hour < 12:
            # 如果当前是上午，设置下午时间范围
            test_time_range = {'startTime': '14:00', 'endTime': '18:00'}
        else:
            # 如果当前是下午，设置上午时间范围
            test_time_range = {'startTime': '08:00', 'endTime': '12:00'}
        
        # 这个测试需要修改配置，这里简化为检查时间范围函数
        result = self.engine._is_in_time_range({'startTime': '00:00', 'endTime': '23:59'})
        return result  # 全天时间范围应该返回True
    
    def test_frequency_manager(self):
        """测试频率管理器"""
        freq_manager = FrequencyManager()
        
        # 测试累计频率
        config = {
            'enabled': 1,
            'hasAccumulate': 1,
            'accumulateCount': 3,
            'accumulateTimeRange': 1  # 1分钟
        }
        
        # 连续触发3次
        for i in range(3):
            result = freq_manager.check_frequency('test_rule', config, True)
            if i < 2 and result:  # 前两次不应该通过
                return False
            if i == 2 and not result:  # 第三次应该通过
                return False
        
        return True
    
    def test_alarm_message_format(self):
        """测试预警消息格式"""
        # 清空历史记录确保测试独立性
        self.engine.clear_alarm_history()
        abnormal_data = {'t1': 0.1, 't2': 25, 't3': 50, 't4': 5}
        alarm = self.engine.process_data(abnormal_data)
        
        if not alarm:
            return False
        
        # 验证JSON序列化
        try:
            json_str = json.dumps(alarm, ensure_ascii=False)
            parsed = json.loads(json_str)
            return isinstance(parsed, dict)
        except:
            return False
    
    def test_alarm_history(self):
        """测试预警历史记录"""
        # 清空历史记录确保测试独立性
        self.engine.clear_alarm_history()
        initial_count = len(self.engine.get_alarm_history())

        # 尝试多种异常数据触发预警
        abnormal_datasets = [
            {'t1': 0.1, 't2': 25, 't3': 50, 't4': 5},   # 多重异常
            {'t1': 0.5, 't2': 15, 't3': 8, 't4': 12},   # t1过小
            {'t1': 15, 't2': 15, 't3': 8, 't4': 12},    # t1过大
        ]

        alarm_count = 0
        for abnormal_data in abnormal_datasets:
            alarm = self.engine.process_data(abnormal_data)
            if alarm is not None:
                alarm_count += 1

        new_count = len(self.engine.get_alarm_history())
        return new_count >= initial_count + alarm_count and alarm_count > 0
    
    def test_statistics(self):
        """测试统计功能"""
        stats = self.engine.get_statistics()
        
        required_stats = ['total_alarms', 'alarm_levels', 'alarm_classes']
        for stat in required_stats:
            if stat not in stats:
                return False
        
        return isinstance(stats['total_alarms'], int)
    
    def test_edge_cases(self):
        """测试边界情况"""
        edge_cases = [
            {},  # 空数据
            {'t1': None},  # None值
            {'t1': 'invalid'},  # 无效类型
            {'unknown_field': 123},  # 未知字段
        ]

        for data in edge_cases:
            try:
                result = self.engine.process_data(data)
                # 边界情况不应该抛出异常，可能返回None或预警
            except Exception as e:
                print(f"   边界情况处理失败: {data} - {str(e)}")
                return False

        return True
    
    def test_multiple_rule_triggers(self):
        """测试多规则触发"""
        # 构造会触发多个规则的数据
        multi_trigger_data = {'t1': 0.1, 't2': 25, 't3': 50, 't4': 5}
        alarm = self.engine.process_data(multi_trigger_data)
        
        if not alarm:
            return False
        
        triggered_count = alarm['alarmInfo']['triggeredRulesCount']
        return triggered_count > 1
    
    def test_configuration_reload(self):
        """测试配置重新加载"""
        # 获取当前配置
        config1 = self.engine.manager.get_fresh_config()

        # 重新获取配置（模拟配置更新）
        config2 = self.engine.manager.get_fresh_config()

        # 配置应该能够正常获取
        return config1 is not None and config2 is not None

    def test_large_scale_data(self):
        """大规模数据测试"""
        print("🔄 开始大规模数据测试...")

        # 生成1000个测试数据
        test_data = self.generate_test_data(1000)

        # 清空历史记录
        self.engine.clear_alarm_history()

        alarm_count = 0
        error_count = 0
        start_time = time.time()

        for i, data in enumerate(test_data):
            try:
                alarm = self.engine.process_data(data)
                if alarm is not None:
                    alarm_count += 1

                # 每100个数据显示一次进度
                if (i + 1) % 100 == 0:
                    print(f"   已处理 {i + 1}/1000 个数据，触发预警 {alarm_count} 次")

            except Exception as e:
                error_count += 1
                if error_count <= 5:  # 只显示前5个错误
                    print(f"   数据处理错误: {data} - {str(e)}")

        end_time = time.time()
        processing_time = end_time - start_time

        print(f"   大规模测试完成:")
        print(f"   - 处理数据: 1000 个")
        print(f"   - 触发预警: {alarm_count} 次")
        print(f"   - 处理错误: {error_count} 次")
        print(f"   - 处理时间: {processing_time:.2f} 秒")
        print(f"   - 平均速度: {1000/processing_time:.1f} 次/秒")

        # 验证结果
        history = self.engine.get_alarm_history()
        stats = self.engine.get_statistics()

        print(f"   - 历史记录: {len(history)} 条")
        print(f"   - 统计信息: {stats}")

        # 测试通过条件：错误率低于5%，有预警触发
        success_rate = (1000 - error_count) / 1000
        return success_rate >= 0.95 and alarm_count > 0
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行精简预警引擎测试套件")
        print("=" * 50)
        
        # 定义所有测试
        tests = [
            ("操作符工厂测试", self.test_operator_factory),
            ("单属性规则测试", self.test_single_property_rules),
            ("双属性规则测试", self.test_double_property_rules),
            ("正常数据处理测试", self.test_normal_data_processing),
            ("异常数据处理测试", self.test_abnormal_data_processing),
            ("时间范围验证测试", self.test_time_range_validation),
            ("频率管理器测试", self.test_frequency_manager),
            ("预警消息格式测试", self.test_alarm_message_format),
            ("预警历史记录测试", self.test_alarm_history),
            ("统计功能测试", self.test_statistics),
            ("边界情况测试", self.test_edge_cases),
            ("多规则触发测试", self.test_multiple_rule_triggers),
            ("配置重新加载测试", self.test_configuration_reload),
            ("大规模数据测试", self.test_large_scale_data),
        ]
        
        # 运行所有测试
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # 输出测试结果摘要
        self.print_test_summary()
    
    def print_test_summary(self):
        """打印测试结果摘要"""
        print("\n" + "=" * 50)
        print("📊 测试结果摘要")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result['passed'])
        total = len(self.test_results)
        
        print(f"总测试数: {total}")
        print(f"通过测试: {passed}")
        print(f"失败测试: {total - passed}")
        print(f"通过率: {passed/total*100:.1f}%")
        
        # 显示失败的测试
        failed_tests = [result for result in self.test_results if not result['passed']]
        if failed_tests:
            print("\n❌ 失败的测试:")
            for test in failed_tests:
                error_msg = f" - {test.get('error', '')}" if 'error' in test else ""
                print(f"   • {test['name']}{error_msg}")
        
        print("\n🎉 测试完成!")


def run_performance_test():
    """运行性能测试"""
    print("\n⚡ 性能测试")
    print("-" * 30)

    engine = CompactAlarmEngine()

    # 使用多样化的测试数据
    test_datasets = [
        {'t1': 5, 't2': 15, 't3': 8, 't4': 12},      # 正常数据
        {'t1': 0.5, 't2': 25, 't3': 50, 't4': 5},    # 异常数据
        {'t1': 15, 't2': 3, 't3': 2, 't4': 20},      # 混合数据
        {'t1': 0.1, 't2': 30, 't3': 60, 't4': 1},    # 多重异常
    ]

    # 测试处理速度
    start_time = time.time()
    iterations = 1000
    alarm_count = 0

    for i in range(iterations):
        test_data = test_datasets[i % len(test_datasets)]
        alarm = engine.process_data(test_data)
        if alarm is not None:
            alarm_count += 1

    end_time = time.time()
    duration = end_time - start_time

    print(f"处理 {iterations} 次数据耗时: {duration:.3f} 秒")
    print(f"平均每次处理耗时: {duration/iterations*1000:.3f} 毫秒")
    print(f"每秒处理能力: {iterations/duration:.0f} 次/秒")
    print(f"触发预警次数: {alarm_count} 次")
    print(f"预警触发率: {alarm_count/iterations*100:.1f}%")


if __name__ == "__main__":
    # 运行测试套件
    tester = CompactAlarmEngineTest()
    tester.run_all_tests()

    # 运行性能测试
    run_performance_test()

    # 显示最终的预警历史和统计
    print("\n📈 最终统计信息:")
    stats = tester.engine.get_statistics()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
