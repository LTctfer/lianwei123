#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的代码
"""

import sys
import os
sys.path.append('溯源算法')

try:
    # 测试导入
    from enhanced_pollution_tracing import EnhancedPollutionTracingSystem
    from optimized_source_inversion import OptimizedInversionResult
    from gaussian_plume_model import PollutionSource
    import plotly.express as px
    
    print("✓ 所有模块导入成功")
    
    # 测试 plotly 图表创建
    algorithms = ['test_alg']
    pos_errors = [5.0]
    
    fig1 = px.bar(x=algorithms, y=pos_errors, title="位置误差对比")
    print(f"✓ plotly 图表创建成功，类型: {type(fig1)}")
    
    # 测试 update_yaxes 方法
    fig1.update_yaxes(title="位置误差 (m)")
    print("✓ update_yaxes 方法调用成功")
    
    # 测试结果对象创建
    result = OptimizedInversionResult(
        source_x=100.0, source_y=200.0, source_z=25.0, emission_rate=2.5,
        objective_value=0.1, computation_time=15.0, convergence_history=[1.0, 0.5, 0.1],
        position_error=5.0, emission_error=10.0, confidence_interval={}, performance_metrics={}
    )
    print("✓ OptimizedInversionResult 对象创建成功")
    
    # 测试属性访问
    print(f"✓ position_error: {result.position_error}")
    print(f"✓ computation_time: {result.computation_time}")
    print(f"✓ objective_value: {result.objective_value}")
    
    # 测试报告生成
    true_source = PollutionSource(x=150.0, y=200.0, z=25.0, emission_rate=2.5)
    results = {'test_algorithm': result}
    
    system = EnhancedPollutionTracingSystem()
    report_path = system.generate_comprehensive_report(true_source, results, 'test')
    print(f"✓ 报告生成成功，路径: {report_path}")
    
    print("\n🎉 所有测试通过！修复成功！")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
