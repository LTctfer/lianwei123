#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC到AI-BOX系统Web监控界面
提供实时数据监控、系统状态查看、配置管理等功能
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import sqlite3
import json
import datetime
from typing import Dict, List, Any
import threading
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebMonitor:
    """Web监控界面"""
    
    def __init__(self, db_path: str = "plc_data.db", port: int = 8888):
        self.db_path = db_path
        self.port = port
        self.app = dash.Dash(__name__)
        self.setup_layout()
        self.setup_callbacks()
        
    def setup_layout(self):
        """设置页面布局"""
        self.app.layout = html.Div([
            # 页面标题
            html.H1("PLC到AI-BOX数据采集系统监控", 
                   style={'textAlign': 'center', 'marginBottom': 30}),
            
            # 自动刷新组件
            dcc.Interval(
                id='interval-component',
                interval=5*1000,  # 5秒刷新一次
                n_intervals=0
            ),
            
            # 系统状态卡片
            html.Div([
                html.H3("系统状态", style={'marginBottom': 20}),
                html.Div(id='system-status-cards', children=[]),
            ], style={'marginBottom': 30}),
            
            # 实时数据图表
            html.Div([
                html.H3("实时数据监控", style={'marginBottom': 20}),
                
                # 设备选择下拉框
                html.Div([
                    html.Label("选择设备:"),
                    dcc.Dropdown(
                        id='device-dropdown',
                        options=[],
                        value=None,
                        style={'width': '200px'}
                    )
                ], style={'marginBottom': 20}),
                
                # 参数选择复选框
                html.Div([
                    html.Label("选择参数:"),
                    dcc.Checklist(
                        id='parameter-checklist',
                        options=[],
                        value=[],
                        inline=True
                    )
                ], style={'marginBottom': 20}),
                
                # 时间范围选择
                html.Div([
                    html.Label("时间范围:"),
                    dcc.Dropdown(
                        id='time-range-dropdown',
                        options=[
                            {'label': '最近1小时', 'value': 1},
                            {'label': '最近6小时', 'value': 6},
                            {'label': '最近24小时', 'value': 24},
                            {'label': '最近7天', 'value': 168}
                        ],
                        value=1,
                        style={'width': '200px'}
                    )
                ], style={'marginBottom': 20}),
                
                # 数据图表
                dcc.Graph(id='realtime-data-graph'),
                
            ], style={'marginBottom': 30}),
            
            # FFT频谱分析
            html.Div([
                html.H3("振动频谱分析", style={'marginBottom': 20}),
                dcc.Graph(id='fft-spectrum-graph'),
            ], style={'marginBottom': 30}),
            
            # 数据质量统计
            html.Div([
                html.H3("数据质量统计", style={'marginBottom': 20}),
                html.Div(id='data-quality-stats'),
            ], style={'marginBottom': 30}),
            
            # 最新数据表格
            html.Div([
                html.H3("最新数据", style={'marginBottom': 20}),
                dash_table.DataTable(
                    id='latest-data-table',
                    columns=[],
                    data=[],
                    style_cell={'textAlign': 'left'},
                    style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                    page_size=10
                )
            ])
        ])
        
    def setup_callbacks(self):
        """设置回调函数"""
        
        @self.app.callback(
            [Output('system-status-cards', 'children'),
             Output('device-dropdown', 'options'),
             Output('parameter-checklist', 'options')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_system_status(n):
            """更新系统状态"""
            try:
                # 获取系统状态
                status_cards = self.create_status_cards()
                
                # 获取设备列表
                devices = self.get_device_list()
                device_options = [{'label': device, 'value': device} for device in devices]
                
                # 获取参数列表
                parameters = self.get_parameter_list()
                param_options = [{'label': param, 'value': param} for param in parameters]
                
                return status_cards, device_options, param_options
                
            except Exception as e:
                logger.error(f"更新系统状态失败: {e}")
                return [], [], []
                
        @self.app.callback(
            Output('realtime-data-graph', 'figure'),
            [Input('interval-component', 'n_intervals'),
             Input('device-dropdown', 'value'),
             Input('parameter-checklist', 'value'),
             Input('time-range-dropdown', 'value')]
        )
        def update_realtime_graph(n, device, parameters, time_range):
            """更新实时数据图表"""
            try:
                if not device or not parameters:
                    return go.Figure()
                    
                # 获取历史数据
                data = self.get_historical_data(device, parameters, time_range)
                
                if data.empty:
                    return go.Figure()
                    
                # 创建图表
                fig = go.Figure()
                
                for param in parameters:
                    if param in data.columns:
                        fig.add_trace(go.Scatter(
                            x=data['timestamp'],
                            y=data[param],
                            mode='lines',
                            name=param,
                            line=dict(width=2)
                        ))
                        
                fig.update_layout(
                    title=f"设备 {device} 实时数据",
                    xaxis_title="时间",
                    yaxis_title="数值",
                    hovermode='x unified',
                    height=400
                )
                
                return fig
                
            except Exception as e:
                logger.error(f"更新实时图表失败: {e}")
                return go.Figure()
                
        @self.app.callback(
            Output('fft-spectrum-graph', 'figure'),
            [Input('interval-component', 'n_intervals'),
             Input('device-dropdown', 'value')]
        )
        def update_fft_graph(n, device):
            """更新FFT频谱图"""
            try:
                if not device:
                    return go.Figure()
                    
                # 获取最新的FFT特征数据
                fft_data = self.get_latest_fft_data(device)
                
                if not fft_data:
                    return go.Figure()
                    
                fig = go.Figure()
                
                # 为每个振动参数创建频谱图
                for param, features in fft_data.items():
                    if 'vibration' in param.lower():
                        # 这里应该获取实际的频谱数据，现在用示例数据
                        frequencies = list(range(0, 50))  # 示例频率范围
                        amplitudes = [features.get('peak_power', 0) * (1 - abs(f-25)/25) for f in frequencies]
                        
                        fig.add_trace(go.Scatter(
                            x=frequencies,
                            y=amplitudes,
                            mode='lines',
                            name=f"{param} 频谱",
                            fill='tonexty' if param != list(fft_data.keys())[0] else 'tozeroy'
                        ))
                        
                fig.update_layout(
                    title=f"设备 {device} 振动频谱分析",
                    xaxis_title="频率 (Hz)",
                    yaxis_title="幅值",
                    height=400
                )
                
                return fig
                
            except Exception as e:
                logger.error(f"更新FFT图表失败: {e}")
                return go.Figure()
                
        @self.app.callback(
            Output('data-quality-stats', 'children'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_quality_stats(n):
            """更新数据质量统计"""
            try:
                stats = self.get_quality_statistics()
                
                cards = []
                for stat_name, stat_value in stats.items():
                    color = 'success' if stat_value > 0.8 else 'warning' if stat_value > 0.6 else 'danger'
                    
                    card = html.Div([
                        html.H4(f"{stat_value:.2%}", style={'margin': 0}),
                        html.P(stat_name, style={'margin': 0, 'fontSize': '14px'})
                    ], style={
                        'backgroundColor': f'var(--bs-{color})',
                        'color': 'white',
                        'padding': '20px',
                        'borderRadius': '8px',
                        'textAlign': 'center',
                        'margin': '10px',
                        'minWidth': '150px'
                    })
                    
                    cards.append(card)
                    
                return html.Div(cards, style={'display': 'flex', 'flexWrap': 'wrap'})
                
            except Exception as e:
                logger.error(f"更新质量统计失败: {e}")
                return html.Div("数据加载失败")
                
        @self.app.callback(
            Output('latest-data-table', 'data'),
            Output('latest-data-table', 'columns'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_latest_data_table(n):
            """更新最新数据表格"""
            try:
                data = self.get_latest_processed_data()
                
                if data.empty:
                    return [], []
                    
                columns = [{"name": col, "id": col} for col in data.columns]
                data_dict = data.to_dict('records')
                
                return data_dict, columns
                
            except Exception as e:
                logger.error(f"更新数据表格失败: {e}")
                return [], []
    
    def create_status_cards(self) -> List[html.Div]:
        """创建系统状态卡片"""
        # 这里应该从实际系统获取状态，现在用示例数据
        status_data = {
            "系统运行状态": "正常",
            "连接设备数": "2",
            "数据采集率": "98.5%",
            "上传成功率": "99.2%"
        }
        
        cards = []
        colors = ['primary', 'success', 'info', 'warning']
        
        for i, (key, value) in enumerate(status_data.items()):
            card = html.Div([
                html.H4(value, style={'margin': 0, 'color': 'white'}),
                html.P(key, style={'margin': 0, 'fontSize': '14px', 'color': 'white'})
            ], style={
                'backgroundColor': f'var(--bs-{colors[i % len(colors)]})',
                'padding': '20px',
                'borderRadius': '8px',
                'textAlign': 'center',
                'margin': '10px',
                'minWidth': '200px'
            })
            cards.append(card)
            
        return html.Div(cards, style={'display': 'flex', 'flexWrap': 'wrap'})
    
    def get_device_list(self) -> List[str]:
        """获取设备列表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT device_id FROM processed_data ORDER BY device_id")
            devices = [row[0] for row in cursor.fetchall()]
            conn.close()
            return devices
        except Exception as e:
            logger.error(f"获取设备列表失败: {e}")
            return []
    
    def get_parameter_list(self) -> List[str]:
        """获取参数列表"""
        # 返回常见的参数列表
        return [
            'vibration_x', 'vibration_y', 'vibration_z',
            'temperature_bearing1', 'temperature_bearing2',
            'pressure_inlet', 'pressure_outlet',
            'flow_rate', 'motor_speed', 'motor_current'
        ]
    
    def get_historical_data(self, device: str, parameters: List[str], hours: int) -> pd.DataFrame:
        """获取历史数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 计算时间范围
            end_time = datetime.datetime.now()
            start_time = end_time - datetime.timedelta(hours=hours)
            
            query = """
                SELECT timestamp, raw_data, filtered_data
                FROM processed_data
                WHERE device_id = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp
            """
            
            df = pd.read_sql_query(query, conn, params=(device, start_time.isoformat(), end_time.isoformat()))
            conn.close()
            
            if df.empty:
                return pd.DataFrame()
            
            # 解析JSON数据
            data_rows = []
            for _, row in df.iterrows():
                try:
                    raw_data = json.loads(row['raw_data']) if row['raw_data'] else {}
                    filtered_data = json.loads(row['filtered_data']) if row['filtered_data'] else {}
                    
                    data_row = {'timestamp': pd.to_datetime(row['timestamp'])}
                    
                    for param in parameters:
                        data_row[param] = filtered_data.get(param, raw_data.get(param, None))
                    
                    data_rows.append(data_row)
                except:
                    continue
            
            return pd.DataFrame(data_rows)
            
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return pd.DataFrame()
    
    def get_latest_fft_data(self, device: str) -> Dict[str, Dict[str, float]]:
        """获取最新的FFT数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT fft_features
                FROM processed_data
                WHERE device_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (device,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return json.loads(result[0])
            return {}
            
        except Exception as e:
            logger.error(f"获取FFT数据失败: {e}")
            return {}
    
    def get_quality_statistics(self) -> Dict[str, float]:
        """获取数据质量统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取最近24小时的质量统计
            end_time = datetime.datetime.now()
            start_time = end_time - datetime.timedelta(hours=24)
            
            cursor.execute("""
                SELECT AVG(quality_score) as avg_quality,
                       COUNT(*) as total_records,
                       COUNT(CASE WHEN quality_score >= 0.8 THEN 1 END) as good_records
                FROM processed_data
                WHERE timestamp >= ? AND timestamp <= ?
            """, (start_time.isoformat(), end_time.isoformat()))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                avg_quality = result[0] or 0
                total_records = result[1] or 0
                good_records = result[2] or 0
                
                return {
                    "平均数据质量": avg_quality,
                    "优质数据比例": good_records / total_records if total_records > 0 else 0,
                    "数据完整性": 0.95,  # 示例值
                    "系统可用性": 0.99   # 示例值
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"获取质量统计失败: {e}")
            return {}
    
    def get_latest_processed_data(self) -> pd.DataFrame:
        """获取最新的处理数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
                SELECT timestamp, device_id, quality_score, raw_data, calculated_values
                FROM processed_data
                ORDER BY timestamp DESC
                LIMIT 20
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # 格式化时间戳
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                df['quality_score'] = df['quality_score'].round(3)
            
            return df
            
        except Exception as e:
            logger.error(f"获取最新数据失败: {e}")
            return pd.DataFrame()
    
    def run(self, debug: bool = False):
        """运行Web服务器"""
        logger.info(f"启动Web监控界面，端口: {self.port}")
        self.app.run_server(host='0.0.0.0', port=self.port, debug=debug)

def main():
    """主函数"""
    monitor = WebMonitor()
    monitor.run(debug=True)

if __name__ == "__main__":
    main()
