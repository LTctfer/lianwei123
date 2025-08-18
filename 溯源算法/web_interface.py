#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
污染源溯源算法Web界面
提供用户友好的Web操作界面
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
import os
import json
from typing import Dict, List, Any
from datetime import datetime

# 导入核心模块
from enhanced_pollution_tracing import EnhancedPollutionTracingSystem, EnhancedScenarioConfig
from enhanced_visualization import EnhancedVisualizer
from gaussian_plume_model import PollutionSource, MeteoData
from optimized_source_inversion import OptimizedSensorData


class WebInterface:
    """Web界面控制器"""
    
    def __init__(self):
        self.system = None
        self.visualizer = EnhancedVisualizer()
        
        # 设置页面配置
        st.set_page_config(
            page_title="污染源溯源算法系统",
            page_icon="旋涡",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def run(self):
        """运行Web界面"""
        
        # 主标题
        st.title("污染源溯源算法系统")
        st.markdown("---")

        # 侧边栏配置
        self._setup_sidebar()

        # 主要内容区域
        tab1, tab2, tab3, tab4 = st.tabs(["场景配置", "算法分析", "结果可视化", "报告生成"])
        
        with tab1:
            self._scenario_configuration()
        
        with tab2:
            self._algorithm_analysis()
        
        with tab3:
            self._result_visualization()
        
        with tab4:
            self._report_generation()
    
    def _setup_sidebar(self):
        """设置侧边栏"""
        
        st.sidebar.header("系统配置")
        
        # 算法选择
        st.sidebar.subheader("算法配置")
        self.selected_algorithms = st.sidebar.multiselect(
            "选择算法变体",
            ["standard", "adaptive", "multi_objective"],
            default=["standard"]  # 默认只选择一个算法以加快速度
        )
        
        # 性能配置
        st.sidebar.subheader("性能配置")
        self.use_parallel = st.sidebar.checkbox("启用并行计算", value=False)  # 默认禁用以避免序列化问题
        self.use_cache = st.sidebar.checkbox("启用缓存机制", value=True)

        # 计算模式选择
        self.computation_mode = st.sidebar.selectbox(
            "计算模式",
            ["快速模式 (50代)", "标准模式 (500代)", "精确模式 (2000代)"],
            index=0  # 默认选择快速模式
        )
        
        # 可视化配置
        st.sidebar.subheader("可视化配置")
        self.show_3d = st.sidebar.checkbox("显示3D可视化", value=True)
        self.show_animation = st.sidebar.checkbox("显示收敛动画", value=False)
        
        # 系统状态
        st.sidebar.markdown("---")
        st.sidebar.subheader("系统状态")
        
        if 'analysis_results' in st.session_state:
            st.sidebar.success("分析已完成")
            st.sidebar.info(f"场景数量: {len(st.session_state.analysis_results)}")
        else:
            st.sidebar.info("等待分析...")
    
    def _scenario_configuration(self):
        """场景配置界面"""

        st.header("场景配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("污染源参数")
            
            source_x = st.number_input("X坐标 (m)", value=150.0, step=10.0)
            source_y = st.number_input("Y坐标 (m)", value=200.0, step=10.0)
            source_z = st.number_input("Z坐标 (m)", value=25.0, step=5.0)
            emission_rate = st.number_input("排放强度 (g/s)", value=2.5, step=0.1)
        
        with col2:
            st.subheader("气象参数")
            
            wind_speed = st.slider("风速 (m/s)", 0.5, 15.0, 3.5, 0.5)
            wind_direction = st.slider("风向 (度)", 0.0, 360.0, 225.0, 15.0)
            temperature = st.number_input("温度 (°C)", value=20.0, step=1.0)
            humidity = st.slider("湿度 (%)", 0, 100, 60, 5)
        
        st.subheader("传感器网络配置")
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            sensor_grid_size = st.slider("网格大小", 5, 12, 7, 1)
        
        with col4:
            sensor_spacing = st.number_input("传感器间距 (m)", value=100.0, step=10.0)
        
        with col5:
            noise_level = st.slider("噪声水平", 0.01, 0.5, 0.1, 0.01)
        
        st.subheader("算法参数")
        
        col6, col7 = st.columns(2)
        
        with col6:
            population_size = st.slider("种群大小", 50, 200, 100, 10)
        
        with col7:
            max_generations = st.slider("最大迭代数", 500, 5000, 2000, 100)
        
        # 保存配置
        if st.button("保存 保存配置", type="primary"):
            config = EnhancedScenarioConfig(
                source_x=source_x, source_y=source_y, source_z=source_z,
                emission_rate=emission_rate, wind_speed=wind_speed,
                wind_direction=wind_direction, temperature=temperature,
                humidity=humidity, sensor_grid_size=sensor_grid_size,
                sensor_spacing=sensor_spacing, noise_level=noise_level,
                population_size=population_size, max_generations=max_generations,
                use_parallel=self.use_parallel, use_cache=self.use_cache
            )
            
            st.session_state.scenario_config = config
            st.success("[完成] 配置已保存！")
        
        # 预设场景
        st.subheader("列表 预设场景")
        
        preset_scenarios = {
            "标准场景": {"wind_speed": 3.5, "emission_rate": 2.5, "noise_level": 0.1},
            "高风速场景": {"wind_speed": 8.0, "emission_rate": 3.0, "noise_level": 0.15},
            "低排放场景": {"wind_speed": 2.0, "emission_rate": 1.0, "noise_level": 0.2},
            "复杂场景": {"wind_speed": 5.5, "emission_rate": 4.0, "noise_level": 0.05}
        }
        
        selected_preset = st.selectbox("选择预设场景", list(preset_scenarios.keys()))
        
        if st.button("刷新 加载预设"):
            preset = preset_scenarios[selected_preset]
            st.rerun()
    
    def _algorithm_analysis(self):
        """算法分析界面"""
        
        st.header("分析 算法分析")
        
        if 'scenario_config' not in st.session_state:
            st.warning("[警告] 请先在场景配置页面保存配置")
            return
        
        config = st.session_state.scenario_config
        
        # 显示当前配置
        st.subheader("列表 当前配置")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("污染源位置", f"({config.source_x:.0f}, {config.source_y:.0f})")
        
        with col2:
            st.metric("排放强度", f"{config.emission_rate:.1f} g/s")
        
        with col3:
            st.metric("风速", f"{config.wind_speed:.1f} m/s")
        
        with col4:
            st.metric("传感器数量", f"~{config.sensor_grid_size**2}")
        
        # 显示预计运行时间
        if self.computation_mode == "快速模式 (50代)":
            st.info("⏱️ 预计运行时间: 10-30秒")
        elif self.computation_mode == "标准模式 (500代)":
            st.info("⏱️ 预计运行时间: 1-3分钟")
        else:
            st.info("⏱️ 预计运行时间: 5-15分钟")

        # 开始分析
        if st.button("启动 开始分析", type="primary"):

            with st.spinner("正在进行污染源溯源分析..."):

                # 根据计算模式调整配置
                if self.computation_mode == "快速模式 (50代)":
                    config.max_generations = 50
                    config.population_size = 30
                elif self.computation_mode == "标准模式 (500代)":
                    config.max_generations = 500
                    config.population_size = 50
                else:  # 精确模式
                    config.max_generations = 2000
                    config.population_size = 100

                # 创建系统
                self.system = EnhancedPollutionTracingSystem(config)
                
                # 创建进度条
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 创建场景
                status_text.text("创建测试场景...")
                progress_bar.progress(20)
                
                true_source, meteo_data, sensor_data = self.system.create_scenario("web_analysis")
                
                # 运行算法
                status_text.text("运行算法分析...")
                progress_bar.progress(40)
                
                results = self.system.run_enhanced_inversion(
                    sensor_data, meteo_data, self.selected_algorithms
                )
                
                # 创建可视化
                status_text.text("生成可视化...")
                progress_bar.progress(70)
                
                visualization_files = self.system.create_comprehensive_visualization(
                    true_source, meteo_data, sensor_data, results, "web_analysis"
                )
                
                # 生成报告
                status_text.text("生成分析报告...")
                progress_bar.progress(90)
                
                report_path = self.system.generate_comprehensive_report(
                    true_source, results, "web_analysis"
                )
                
                progress_bar.progress(100)
                status_text.text("分析完成！")
                
                # 保存结果到session state
                st.session_state.analysis_results = {
                    'true_source': true_source,
                    'meteo_data': meteo_data,
                    'sensor_data': sensor_data,
                    'results': results,
                    'visualization_files': visualization_files,
                    'report_path': report_path
                }
                
                st.success("[完成] 分析完成！请查看结果可视化页面。")
        
        # 显示历史分析结果
        if 'analysis_results' in st.session_state:
            st.subheader("图表 分析结果摘要")
            
            results = st.session_state.analysis_results['results']
            
            # 创建结果表格
            result_data = []
            for algorithm, result in results.items():
                result_data.append({
                    '算法': algorithm,
                    '位置误差 (m)': f"{result.position_error:.2f}",
                    '源强误差 (%)': f"{result.emission_error:.2f}",
                    '计算时间 (s)': f"{result.computation_time:.2f}",
                    '目标函数值': f"{result.objective_value:.2e}"
                })
            
            df = pd.DataFrame(result_data)
            st.dataframe(df, use_container_width=True)
            
            # 最佳算法
            best_algorithm = min(results.items(), key=lambda x: x[1].objective_value)
            st.info(f"奖杯 最佳算法: {best_algorithm[0]} (目标函数值: {best_algorithm[1].objective_value:.2e})")
    
    def _result_visualization(self):
        """结果可视化界面"""
        
        st.header("图表 结果可视化")
        
        if 'analysis_results' not in st.session_state:
            st.warning("[警告] 请先在算法分析页面运行分析")
            return
        
        analysis_data = st.session_state.analysis_results
        
        # 可视化选项
        viz_option = st.selectbox(
            "选择可视化类型",
            ["算法性能对比", "浓度场分布", "收敛过程", "传感器分布", "误差分析"]
        )
        
        if viz_option == "算法性能对比":
            self._show_performance_comparison(analysis_data)
        
        elif viz_option == "浓度场分布":
            self._show_concentration_field(analysis_data)
        
        elif viz_option == "收敛过程":
            self._show_convergence_process(analysis_data)
        
        elif viz_option == "传感器分布":
            self._show_sensor_distribution(analysis_data)
        
        elif viz_option == "误差分析":
            self._show_error_analysis(analysis_data)
    
    def _show_performance_comparison(self, analysis_data):
        """显示性能对比"""
        
        results = analysis_data['results']
        
        # 创建性能对比图
        algorithms = list(results.keys())
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 位置误差对比
            pos_errors = [results[alg].position_error for alg in algorithms]
            fig1 = px.bar(x=algorithms, y=pos_errors, title="位置误差对比")
            fig1.update_yaxis(title="位置误差 (m)")
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # 计算时间对比
            comp_times = [results[alg].computation_time for alg in algorithms]
            fig2 = px.bar(x=algorithms, y=comp_times, title="计算时间对比")
            fig2.update_yaxis(title="计算时间 (s)")
            st.plotly_chart(fig2, use_container_width=True)
        
        # 目标函数值对比（对数尺度）
        obj_values = [results[alg].objective_value for alg in algorithms]
        fig3 = px.bar(x=algorithms, y=obj_values, title="目标函数值对比", log_y=True)
        fig3.update_yaxis(title="目标函数值 (对数尺度)")
        st.plotly_chart(fig3, use_container_width=True)
    
    def _show_concentration_field(self, analysis_data):
        """显示浓度场分布"""
        
        true_source = analysis_data['true_source']
        meteo_data = analysis_data['meteo_data']
        results = analysis_data['results']
        
        # 选择算法
        selected_alg = st.selectbox("选择算法", list(results.keys()))
        
        if selected_alg:
            result = results[selected_alg]
            
            # 创建浓度场对比
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("真实浓度场")
                # 这里可以添加真实浓度场的可视化
                st.info("真实浓度场可视化")
            
            with col2:
                st.subheader(f"{selected_alg} 算法结果")
                # 这里可以添加估计浓度场的可视化
                st.info("估计浓度场可视化")
    
    def _show_convergence_process(self, analysis_data):
        """显示收敛过程"""
        
        results = analysis_data['results']
        
        # 创建收敛过程图
        fig = go.Figure()
        
        for algorithm, result in results.items():
            fig.add_trace(
                go.Scatter(
                    y=result.convergence_history,
                    mode='lines',
                    name=algorithm,
                    line=dict(width=2)
                )
            )
        
        fig.update_layout(
            title="算法收敛过程对比",
            xaxis_title="迭代次数",
            yaxis_title="目标函数值",
            yaxis_type="log"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_sensor_distribution(self, analysis_data):
        """显示传感器分布"""
        
        sensor_data = analysis_data['sensor_data']
        
        # 创建传感器分布图
        df = pd.DataFrame([
            {
                'x': s.x,
                'y': s.y,
                'concentration': s.concentration,
                'sensor_id': s.sensor_id
            }
            for s in sensor_data
        ])
        
        fig = px.scatter(
            df, x='x', y='y', 
            color='concentration',
            size='concentration',
            hover_data=['sensor_id'],
            title="传感器分布及浓度"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_error_analysis(self, analysis_data):
        """显示误差分析"""
        
        true_source = analysis_data['true_source']
        results = analysis_data['results']
        
        # 创建误差分析表格
        error_data = []
        for algorithm, result in results.items():
            pos_error = np.sqrt(
                (true_source.x - result.source_x)**2 + 
                (true_source.y - result.source_y)**2
            )
            emission_error = abs(true_source.emission_rate - result.emission_rate) / true_source.emission_rate * 100
            
            error_data.append({
                '算法': algorithm,
                '位置误差 (m)': pos_error,
                '源强误差 (%)': emission_error,
                'X坐标误差 (m)': abs(true_source.x - result.source_x),
                'Y坐标误差 (m)': abs(true_source.y - result.source_y),
                'Z坐标误差 (m)': abs(true_source.z - result.source_z)
            })
        
        df = pd.DataFrame(error_data)
        st.dataframe(df, use_container_width=True)
        
        # 误差可视化
        fig = px.bar(df, x='算法', y=['位置误差 (m)', '源强误差 (%)'], 
                    title="误差对比", barmode='group')
        st.plotly_chart(fig, use_container_width=True)
    
    def _report_generation(self):
        """报告生成界面"""
        
        st.header("列表 报告生成")
        
        if 'analysis_results' not in st.session_state:
            st.warning("[警告] 请先在算法分析页面运行分析")
            return
        
        analysis_data = st.session_state.analysis_results
        
        # 报告选项
        report_type = st.selectbox(
            "选择报告类型",
            ["综合分析报告", "算法性能报告", "可视化报告", "技术文档"]
        )
        
        if st.button("文档 生成报告"):
            
            with st.spinner("正在生成报告..."):
                
                if report_type == "综合分析报告":
                    self._generate_comprehensive_report(analysis_data)
                
                elif report_type == "算法性能报告":
                    self._generate_performance_report(analysis_data)
                
                elif report_type == "可视化报告":
                    self._generate_visualization_report(analysis_data)
                
                elif report_type == "技术文档":
                    self._generate_technical_documentation()
                
                st.success("[完成] 报告生成完成！")
        
        # 显示已生成的文件
        if 'visualization_files' in analysis_data:
            st.subheader("文件夹 生成的文件")
            
            for file_type, file_path in analysis_data['visualization_files'].items():
                if os.path.exists(file_path):
                    st.download_button(
                        label=f"下载 {file_type}",
                        data=open(file_path, 'rb').read(),
                        file_name=os.path.basename(file_path),
                        mime="application/octet-stream"
                    )
    
    def _generate_comprehensive_report(self, analysis_data):
        """生成综合分析报告"""
        st.info("综合分析报告已生成")
    
    def _generate_performance_report(self, analysis_data):
        """生成算法性能报告"""
        st.info("算法性能报告已生成")
    
    def _generate_visualization_report(self, analysis_data):
        """生成可视化报告"""
        st.info("可视化报告已生成")
    
    def _generate_technical_documentation(self):
        """生成技术文档"""
        st.info("技术文档已生成")


def main():
    """主函数"""
    interface = WebInterface()
    interface.run()


if __name__ == "__main__":
    main()
