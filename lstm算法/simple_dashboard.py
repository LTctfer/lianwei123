"""
🌍 智能空气质量预测系统 - 小白友好版
专为非技术用户设计的简单易用界面
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prediction_engine import LSTMPredictionEngine

# 页面配置
st.set_page_config(
    page_title="🌍 智能空气质量预测系统",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .step-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 5px solid #4CAF50;
    }
    
    .step-number {
        background: #4CAF50;
        color: white;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 1.2rem;
        margin-right: 1rem;
    }
    
    .info-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #1976d2;
        margin: 1rem 0;
    }
    
    .success-box {
        background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #2e7d32;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fff3e0 0%, #fce4ec 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #f57c00;
        margin: 1rem 0;
    }
    
    .big-button {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 1rem 2rem;
        border: none;
        border-radius: 10px;
        font-size: 1.2rem;
        font-weight: bold;
        cursor: pointer;
        width: 100%;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        margin: 0.5rem;
        border-top: 4px solid #1f77b4;
    }
    
    .progress-bar {
        background: #e0e0e0;
        border-radius: 10px;
        height: 20px;
        margin: 1rem 0;
    }
    
    .progress-fill {
        background: linear-gradient(90deg, #4CAF50, #45a049);
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

def show_welcome_page():
    """显示欢迎页面"""
    st.markdown("""
    <div class="main-header">
        🌍 智能空气质量预测系统
        <br><small style="font-size: 1.2rem;">让AI帮您预测未来空气质量</small>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h3>🎯 系统功能</h3>
        <p>本系统可以根据历史空气质量数据，智能预测未来1-3天的空气质量状况，帮助您：</p>
        <ul>
            <li>🏃‍♂️ 规划户外运动时间</li>
            <li>🏠 决定是否开窗通风</li>
            <li>😷 提前准备防护措施</li>
            <li>📅 安排出行计划</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>🏭 监测站点</h4>
            <h2 style="color: #1f77b4;">5个</h2>
            <p>伦敦地区主要监测点</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>🌡️ 监测指标</h4>
            <h2 style="color: #ff7f0e;">8种</h2>
            <p>PM2.5、NO2、O3等</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>🔮 预测时长</h4>
            <h2 style="color: #2ca02c;">72小时</h2>
            <p>未来3天详细预测</p>
        </div>
        """, unsafe_allow_html=True)

def show_simple_guide():
    """显示简单使用指南"""
    st.markdown("""
    <div class="step-container">
        <h3><span class="step-number">1</span>准备数据</h3>
        <p>系统会自动加载历史空气质量数据，无需您手动操作。</p>
    </div>
    
    <div class="step-container">
        <h3><span class="step-number">2</span>训练AI模型</h3>
        <p>点击"开始训练"按钮，AI会学习历史数据中的规律。</p>
    </div>
    
    <div class="step-container">
        <h3><span class="step-number">3</span>生成预测</h3>
        <p>训练完成后，系统会自动生成未来3天的空气质量预测。</p>
    </div>
    
    <div class="step-container">
        <h3><span class="step-number">4</span>查看结果</h3>
        <p>通过直观的图表查看预测结果，了解空气质量变化趋势。</p>
    </div>
    """, unsafe_allow_html=True)

def show_data_status():
    """显示数据状态"""
    st.markdown("### 📊 数据检查")
    
    data_dir = "air_pollutants_prediction_lstm-master/data"
    required_files = [
        "Bloomsbury_clean.csv",
        "Marylebone_Road_clean.csv", 
        "Eltham_clean.csv",
        "Harlington_clean.csv",
        "N_Kensington_clean.csv"
    ]
    
    available_count = 0
    for file in required_files:
        file_path = os.path.join(data_dir, file)
        if os.path.exists(file_path):
            available_count += 1
    
    progress = available_count / len(required_files)
    
    st.markdown(f"""
    <div class="progress-bar">
        <div class="progress-fill" style="width: {progress*100}%"></div>
    </div>
    """, unsafe_allow_html=True)
    
    if available_count == len(required_files):
        st.markdown("""
        <div class="success-box">
            <h4>✅ 数据准备完成</h4>
            <p>所有5个监测站的数据文件都已就绪，可以开始训练模型。</p>
        </div>
        """, unsafe_allow_html=True)
        return True
    else:
        st.markdown(f"""
        <div class="warning-box">
            <h4>⚠️ 数据不完整</h4>
            <p>找到 {available_count}/{len(required_files)} 个数据文件。请确保所有数据文件都在正确位置。</p>
        </div>
        """, unsafe_allow_html=True)
        return False

def show_training_interface():
    """显示训练界面"""
    st.markdown("### 🤖 AI模型训练")
    
    # 简化的参数设置
    st.markdown("""
    <div class="info-box">
        <h4>🎛️ 训练设置</h4>
        <p>我们为您预设了最佳参数，您也可以根据需要调整：</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        prediction_hours = st.selectbox(
            "🔮 预测时长",
            [24, 48, 72],
            index=2,
            help="选择要预测未来多少小时的空气质量",
            key="training_prediction_hours"
        )
        
        training_speed = st.selectbox(
            "⚡ 训练速度",
            ["快速训练（5分钟）", "标准训练（15分钟）", "精确训练（30分钟）"],
            index=1,
            help="训练时间越长，预测精度越高",
            key="training_speed_select"
        )
    
    with col2:
        model_complexity = st.selectbox(
            "🧠 模型复杂度",
            ["简单模型", "标准模型", "复杂模型"],
            index=1,
            help="复杂模型预测更准确，但需要更多时间",
            key="model_complexity_select"
        )
        
        data_amount = st.selectbox(
            "📊 使用数据量",
            ["最近6个月", "最近1年", "全部数据"],
            index=2,
            help="更多数据通常能提高预测准确性",
            key="data_amount_select"
        )
    
    # 转换用户选择为技术参数
    speed_mapping = {
        "快速训练（5分钟）": {"epochs": 10, "batch_size": 64},
        "标准训练（15分钟）": {"epochs": 50, "batch_size": 32},
        "精确训练（30分钟）": {"epochs": 100, "batch_size": 16}
    }
    
    complexity_mapping = {
        "简单模型": {"lstm_units": [32, 16], "dense_units": [16, 8]},
        "标准模型": {"lstm_units": [64, 32], "dense_units": [32, 16]},
        "复杂模型": {"lstm_units": [128, 64], "dense_units": [64, 32]}
    }
    
    if st.button("🚀 开始训练AI模型", key="start_training"):
        with st.spinner("🤖 AI正在学习数据中的规律..."):
            try:
                # 创建预测引擎
                engine = LSTMPredictionEngine("air_pollutants_prediction_lstm-master/data")
                
                # 设置配置
                speed_config = speed_mapping[training_speed]
                complexity_config = complexity_mapping[model_complexity]
                
                engine.config.update({
                    'prediction_horizon': prediction_hours,
                    **speed_config
                })
                
                # 显示训练进度
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 数据加载
                status_text.text("📊 正在加载数据...")
                progress_bar.progress(20)
                
                if engine.load_and_prepare_data():
                    status_text.text("🔧 正在构建AI模型...")
                    progress_bar.progress(40)
                    
                    # 模型训练
                    if engine.build_and_train_model(complexity_config):
                        status_text.text("📈 正在评估模型性能...")
                        progress_bar.progress(80)
                        
                        # 模型评估
                        metrics, predictions = engine.evaluate_model()
                        progress_bar.progress(100)
                        
                        st.session_state['engine'] = engine
                        st.session_state['training_complete'] = True
                        
                        st.markdown("""
                        <div class="success-box">
                            <h4>🎉 训练完成！</h4>
                            <p>AI模型已经成功学习了历史数据，现在可以进行预测了。</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 显示模型性能
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📊 预测准确度", f"{metrics.get('r2_score', 0):.1%}")
                        with col2:
                            st.metric("📉 平均误差", f"{metrics.get('mae', 0):.2f}")
                        with col3:
                            st.metric("🎯 模型评分", f"{min(metrics.get('r2_score', 0) * 100, 99):.0f}/100")
                    
                    else:
                        st.error("❌ 模型训练失败，请检查数据或降低模型复杂度")
                else:
                    st.error("❌ 数据加载失败，请检查数据文件")
                    
            except Exception as e:
                st.error(f"❌ 训练过程中出现错误: {str(e)}")

def show_prediction_results():
    """显示预测结果"""
    st.markdown("### 🔮 空气质量预测结果")
    
    if 'engine' not in st.session_state:
        st.markdown("""
        <div class="warning-box">
            <h4>⚠️ 请先训练模型</h4>
            <p>在查看预测结果之前，请先完成AI模型的训练。</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    engine = st.session_state['engine']
    
    # 预测时长选择
    prediction_hours = st.selectbox(
        "选择预测时长",
        [24, 48, 72],
        index=2,
        key="prediction_hours_select"
    )
    
    if st.button("🔮 生成预测", key="generate_prediction"):
        with st.spinner("🔮 AI正在预测未来空气质量..."):
            try:
                # 生成预测
                prediction_df, pred_array = engine.predict_future(hours=prediction_hours)
                
                if prediction_df is not None:
                    st.session_state['predictions'] = prediction_df
                    
                    st.markdown("""
                    <div class="success-box">
                        <h4>✅ 预测完成</h4>
                        <p>AI已经成功预测了未来的空气质量状况。</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 显示预测图表
                    show_prediction_charts(prediction_df)
                    
                else:
                    st.error("❌ 预测生成失败")
                    
            except Exception as e:
                st.error(f"❌ 预测过程中出现错误: {str(e)}")
    
    # 如果已有预测结果，直接显示
    if 'predictions' in st.session_state:
        show_prediction_charts(st.session_state['predictions'])

def show_prediction_charts(prediction_df):
    """显示预测图表"""
    st.markdown("#### 📈 预测图表")
    
    # 主要污染物
    main_pollutants = ['pm2.5', 'no2', 'o3']
    pollutant_names = {
        'pm2.5': 'PM2.5 细颗粒物',
        'no2': 'NO2 二氧化氮', 
        'o3': 'O3 臭氧'
    }
    
    # 为每个污染物创建图表
    for pollutant in main_pollutants:
        # 查找包含该污染物的列
        pollutant_columns = [col for col in prediction_df.columns if pollutant in col.lower()]
        
        if pollutant_columns:
            st.markdown(f"##### {pollutant_names[pollutant]} 预测")
            
            fig = go.Figure()
            
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
            
            for i, col in enumerate(pollutant_columns[:5]):  # 最多显示5个站点
                station_name = col.split('_')[-1] if '_' in col else f"站点{i+1}"
                
                fig.add_trace(go.Scatter(
                    x=prediction_df.index,
                    y=prediction_df[col],
                    mode='lines+markers',
                    name=station_name,
                    line=dict(color=colors[i % len(colors)], width=3),
                    marker=dict(size=6)
                ))
            
            fig.update_layout(
                title=f"{pollutant_names[pollutant]} 浓度预测趋势",
                xaxis_title="时间",
                yaxis_title="浓度 (μg/m³)",
                height=400,
                showlegend=True,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{pollutant}_{time.time()}")
            
            # 添加健康建议
            avg_value = prediction_df[pollutant_columns].mean().mean()
            show_health_advice(pollutant, avg_value)

def show_health_advice(pollutant, avg_value):
    """显示健康建议"""
    advice_map = {
        'pm2.5': {
            'thresholds': [35, 75, 115],
            'levels': ['优', '良', '轻度污染', '中度污染'],
            'colors': ['#00e400', '#ffff00', '#ff7e00', '#ff0000'],
            'advice': [
                '空气质量优秀，适合所有户外活动',
                '空气质量良好，可以正常户外活动',
                '敏感人群应减少户外活动',
                '建议减少户外活动，佩戴口罩'
            ]
        },
        'no2': {
            'thresholds': [80, 180, 280],
            'levels': ['优', '良', '轻度污染', '中度污染'],
            'colors': ['#00e400', '#ffff00', '#ff7e00', '#ff0000'],
            'advice': [
                'NO2浓度很低，空气清新',
                'NO2浓度正常，可以放心呼吸',
                '敏感人群应注意防护',
                '建议减少户外活动时间'
            ]
        },
        'o3': {
            'thresholds': [100, 160, 215],
            'levels': ['优', '良', '轻度污染', '中度污染'],
            'colors': ['#00e400', '#ffff00', '#ff7e00', '#ff0000'],
            'advice': [
                '臭氧浓度低，空气质量优秀',
                '臭氧浓度适中，适合户外活动',
                '午后臭氧浓度较高，注意防护',
                '避免午后户外剧烈运动'
            ]
        }
    }
    
    if pollutant in advice_map:
        info = advice_map[pollutant]
        level_index = 0
        
        for i, threshold in enumerate(info['thresholds']):
            if avg_value > threshold:
                level_index = i + 1
        
        level = info['levels'][level_index]
        color = info['colors'][level_index]
        advice = info['advice'][level_index]
        
        st.markdown(f"""
        <div style="background-color: {color}; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
            <h5 style="margin: 0; color: black;">🏥 健康建议</h5>
            <p style="margin: 0.5rem 0 0 0; color: black;"><strong>空气质量等级：{level}</strong></p>
            <p style="margin: 0.5rem 0 0 0; color: black;">{advice}</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    """主函数"""
    # 侧边栏导航
    with st.sidebar:
        st.markdown("### 🧭 导航菜单")
        page = st.radio(
            "选择功能",
            ["🏠 首页", "📚 使用指南", "🤖 AI训练", "🔮 查看预测"],
            key="navigation"
        )
    
    # 根据选择显示不同页面
    if page == "🏠 首页":
        show_welcome_page()
        st.markdown("---")
        if show_data_status():
            st.markdown("""
            <div class="info-box">
                <h4>🎯 下一步操作</h4>
                <p>数据已准备就绪！请点击左侧菜单中的"🤖 AI训练"开始训练模型。</p>
            </div>
            """, unsafe_allow_html=True)
    
    elif page == "📚 使用指南":
        st.markdown("## 📚 使用指南")
        show_simple_guide()
    
    elif page == "🤖 AI训练":
        show_training_interface()
    
    elif page == "🔮 查看预测":
        show_prediction_results()
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>🌍 智能空气质量预测系统 | 让AI守护您的健康</p>
        <p><small>基于深度学习LSTM神经网络 | 数据来源：伦敦空气质量监测网络</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
