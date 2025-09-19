"""
交互式LSTM预测仪表板
使用Streamlit创建Web界面
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime
import os
import sys

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prediction_engine import LSTMPredictionEngine

# 页面配置
st.set_page_config(
    page_title="LSTM多站点预测系统",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

class InteractiveDashboard:
    """交互式仪表板类"""
    
    def __init__(self):
        self.engine = None
        self.prediction_data = None
        self.metrics = None
        
    def initialize_session_state(self):
        """初始化会话状态"""
        if 'engine_initialized' not in st.session_state:
            st.session_state.engine_initialized = False
        if 'model_trained' not in st.session_state:
            st.session_state.model_trained = False
        if 'predictions_made' not in st.session_state:
            st.session_state.predictions_made = False
    
    def render_header(self):
        """渲染页面头部"""
        st.markdown('<h1 class="main-header">🌍 LSTM多站点多变量空气质量预测系统</h1>', 
                   unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <p style="font-size: 1.2rem; color: #666;">
                基于深度学习的多站点空气质量预测与可视化平台
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """渲染侧边栏"""
        st.sidebar.title("🎛️ 控制面板")
        
        # 数据配置
        st.sidebar.header("📊 数据配置")
        data_dir = st.sidebar.text_input(
            "数据目录路径", 
            value="air_pollutants_prediction_lstm-master/data",
            help="包含CSV数据文件的目录路径"
        )
        
        # 模型配置
        st.sidebar.header("🤖 模型配置")
        
        window_size = st.sidebar.slider(
            "历史窗口大小（小时）", 
            min_value=24, max_value=720, value=240, step=24,
            help="用于预测的历史数据长度"
        )
        
        prediction_horizon = st.sidebar.slider(
            "预测时间范围（小时）", 
            min_value=1, max_value=72, value=24, step=1,
            help="单次预测的时间长度"
        )
        
        lstm_units = st.sidebar.multiselect(
            "LSTM层单元数",
            options=[32, 64, 128, 256],
            default=[128, 64],
            help="LSTM层的神经元数量"
        )
        
        epochs = st.sidebar.slider(
            "训练轮数", 
            min_value=10, max_value=200, value=50, step=10,
            help="模型训练的轮数"
        )
        
        batch_size = st.sidebar.selectbox(
            "批次大小",
            options=[16, 32, 64, 128],
            index=1,
            help="训练时的批次大小"
        )
        
        return {
            'data_dir': data_dir,
            'window_size': window_size,
            'prediction_horizon': prediction_horizon,
            'lstm_units': lstm_units,
            'epochs': epochs,
            'batch_size': batch_size
        }
    
    def initialize_engine(self, config):
        """初始化预测引擎"""
        if st.button("🚀 初始化系统", type="primary"):
            with st.spinner("正在初始化系统..."):
                try:
                    self.engine = LSTMPredictionEngine(config['data_dir'])
                    self.engine.config.update({
                        'window_size': config['window_size'],
                        'prediction_horizon': config['prediction_horizon'],
                        'epochs': config['epochs'],
                        'batch_size': config['batch_size']
                    })
                    
                    if self.engine.load_and_prepare_data():
                        st.session_state.engine_initialized = True
                        st.success("✅ 系统初始化成功！")
                        
                        # 显示数据信息
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("数据点数", len(self.engine.data_processor.combined_data))
                        with col2:
                            st.metric("特征数量", len(self.engine.feature_names))
                        with col3:
                            st.metric("站点数量", "5")
                        
                        return True
                    else:
                        st.error("❌ 数据加载失败")
                        return False
                        
                except Exception as e:
                    st.error(f"❌ 初始化失败: {str(e)}")
                    return False
        
        return st.session_state.engine_initialized
    
    def train_model(self, config):
        """训练模型"""
        if not st.session_state.engine_initialized:
            st.warning("⚠️ 请先初始化系统")
            return False
        
        if st.button("🎯 开始训练模型", type="primary"):
            with st.spinner("正在训练模型，请稍候..."):
                try:
                    model_config = {
                        'lstm_units': config['lstm_units'],
                        'dense_units': [64, 32],
                        'dropout_rate': 0.3,
                        'learning_rate': 0.001
                    }
                    
                    if self.engine.build_and_train_model(model_config):
                        st.session_state.model_trained = True
                        st.success("✅ 模型训练完成！")
                        
                        # 评估模型
                        self.metrics, _ = self.engine.evaluate_model()
                        
                        # 显示性能指标
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("R² 分数", f"{self.metrics['R2']:.4f}")
                        with col2:
                            st.metric("RMSE", f"{self.metrics['RMSE']:.4f}")
                        with col3:
                            st.metric("MAE", f"{self.metrics['MAE']:.4f}")
                        with col4:
                            st.metric("MSE", f"{self.metrics['MSE']:.4f}")
                        
                        return True
                    else:
                        st.error("❌ 模型训练失败")
                        return False
                        
                except Exception as e:
                    st.error(f"❌ 训练失败: {str(e)}")
                    return False
        
        return st.session_state.model_trained
    
    def make_predictions(self):
        """进行预测"""
        if not st.session_state.model_trained:
            st.warning("⚠️ 请先训练模型")
            return False
        
        # 预测配置
        st.subheader("🔮 预测配置")
        
        col1, col2 = st.columns(2)
        with col1:
            prediction_hours = st.slider(
                "预测时长（小时）", 
                min_value=1, max_value=168, value=72, step=1
            )
        with col2:
            start_time = st.datetime_input(
                "预测起始时间",
                value=datetime.datetime.now().replace(hour=0, minute=0, second=0)
            )
        
        if st.button("🎯 开始预测", type="primary"):
            with st.spinner("正在生成预测..."):
                try:
                    prediction_df, pred_array = self.engine.predict_future(prediction_hours)
                    self.prediction_data = prediction_df
                    st.session_state.predictions_made = True
                    
                    st.success(f"✅ 成功生成 {prediction_hours} 小时的预测数据！")
                    
                    # 保存预测结果
                    filename = self.engine.save_predictions(prediction_df)
                    st.info(f"📁 预测结果已保存到: {filename}")
                    
                    return True
                    
                except Exception as e:
                    st.error(f"❌ 预测失败: {str(e)}")
                    return False
        
        return st.session_state.predictions_made
    
    def render_prediction_charts(self):
        """渲染预测图表"""
        if self.prediction_data is None:
            st.warning("⚠️ 暂无预测数据")
            return
        
        st.subheader("📈 预测结果可视化")
        
        # 选择要显示的污染物
        pollutants = ['nox', 'no2', 'no', 'o3', 'pm2.5']
        selected_pollutants = st.multiselect(
            "选择要显示的污染物",
            options=pollutants,
            default=pollutants[:3]
        )
        
        if not selected_pollutants:
            st.warning("请至少选择一个污染物")
            return
        
        # 选择站点
        stations = ['B', 'M', 'E', 'H', 'N']
        station_names = ['Bloomsbury', 'Marylebone Road', 'Eltham', 'Harlington', 'N Kensington']
        selected_station = st.selectbox(
            "选择监测站点",
            options=stations,
            format_func=lambda x: station_names[stations.index(x)]
        )
        
        # 创建时间序列图
        fig = make_subplots(
            rows=len(selected_pollutants), cols=1,
            subplot_titles=[f"{pollutant.upper()} 浓度预测" for pollutant in selected_pollutants],
            vertical_spacing=0.08
        )
        
        colors = px.colors.qualitative.Set1
        
        for i, pollutant in enumerate(selected_pollutants):
            column_name = f"{pollutant}_{selected_station}"
            if column_name in self.prediction_data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=self.prediction_data.index,
                        y=self.prediction_data[column_name],
                        mode='lines+markers',
                        name=f"{pollutant.upper()}",
                        line=dict(color=colors[i % len(colors)], width=2),
                        marker=dict(size=4)
                    ),
                    row=i+1, col=1
                )
        
        fig.update_layout(
            height=300 * len(selected_pollutants),
            title_text=f"🌍 {station_names[stations.index(selected_station)]} 站点预测结果",
            showlegend=True
        )
        
        fig.update_xaxes(title_text="时间")
        fig.update_yaxes(title_text="浓度 (μg/m³)")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 数据表格
        if st.checkbox("显示预测数据表格"):
            display_columns = [f"{p}_{selected_station}" for p in selected_pollutants 
                             if f"{p}_{selected_station}" in self.prediction_data.columns]
            
            if display_columns:
                st.dataframe(
                    self.prediction_data[display_columns].round(3),
                    use_container_width=True
                )
    
    def render_analysis_charts(self):
        """渲染分析图表"""
        if not st.session_state.engine_initialized:
            return
        
        st.subheader("📊 数据分析")
        
        tab1, tab2, tab3 = st.tabs(["相关性分析", "特征分布", "站点对比"])
        
        with tab1:
            st.write("### 特征相关性矩阵")
            if hasattr(self.engine, 'data_processor') and self.engine.data_processor.combined_data is not None:
                corr_matrix = self.engine.data_processor.combined_data.corr()
                
                fig = px.imshow(
                    corr_matrix,
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale="RdBu_r",
                    title="多站点特征相关性分析"
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.write("### 特征分布分析")
            if hasattr(self.engine, 'data_processor') and self.engine.data_processor.combined_data is not None:
                # 选择要分析的特征
                feature_to_analyze = st.selectbox(
                    "选择特征",
                    options=self.engine.feature_names
                )
                
                if feature_to_analyze:
                    data = self.engine.data_processor.combined_data[feature_to_analyze]
                    
                    fig = px.histogram(
                        x=data,
                        nbins=50,
                        title=f"{feature_to_analyze} 分布",
                        labels={'x': feature_to_analyze, 'y': '频次'}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.write("### 站点数据对比")
            if hasattr(self.engine, 'data_processor') and self.engine.data_processor.combined_data is not None:
                # 选择污染物进行站点对比
                pollutant_for_comparison = st.selectbox(
                    "选择污染物",
                    options=['nox', 'no2', 'no', 'o3', 'pm2.5']
                )
                
                if pollutant_for_comparison:
                    station_columns = [col for col in self.engine.feature_names 
                                     if col.startswith(pollutant_for_comparison)]
                    
                    if station_columns:
                        fig = go.Figure()
                        
                        for col in station_columns:
                            station_name = col.split('_')[-1]
                            data = self.engine.data_processor.combined_data[col]
                            
                            fig.add_trace(go.Scatter(
                                x=data.index,
                                y=data.values,
                                mode='lines',
                                name=f"站点 {station_name}",
                                line=dict(width=1)
                            ))
                        
                        fig.update_layout(
                            title=f"{pollutant_for_comparison.upper()} 各站点对比",
                            xaxis_title="时间",
                            yaxis_title="浓度 (μg/m³)"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
    
    def run(self):
        """运行仪表板"""
        self.initialize_session_state()
        self.render_header()
        
        # 侧边栏配置
        config = self.render_sidebar()
        
        # 主要内容区域
        tab1, tab2, tab3, tab4 = st.tabs(["🚀 系统初始化", "🎯 模型训练", "🔮 预测分析", "📊 数据分析"])
        
        with tab1:
            st.header("系统初始化")
            st.write("配置系统参数并加载数据")
            self.initialize_engine(config)
        
        with tab2:
            st.header("模型训练")
            st.write("训练LSTM预测模型")
            self.train_model(config)
        
        with tab3:
            st.header("预测分析")
            st.write("生成未来空气质量预测")
            self.make_predictions()
            self.render_prediction_charts()
        
        with tab4:
            st.header("数据分析")
            st.write("深入分析数据特征和模式")
            self.render_analysis_charts()

def main():
    """主函数"""
    dashboard = InteractiveDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
