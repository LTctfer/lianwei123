"""
污染源溯源系统Web界面 - 增强版
集成三色预警系统和实时监控功能
提供全面的用户界面和数据可视化
"""

from flask import Flask, render_template, request, jsonify, send_file, session
import pandas as pd
import numpy as np
import json
import os
import logging
from datetime import datetime, timedelta
import io
import base64
import uuid
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import sqlite3
from werkzeug.utils import secure_filename

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.source_inversion import SourceInversionEngine
from core.three_color_warning import ThreeColorWarningSystem
from core.real_time_monitoring import (
    RealTimeMonitoringSystem, MonitoringStation, SensorReading, RealTimeAlert
)
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pollution_source_tracing_2024'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 全局变量
inversion_engine = None
warning_system = None
monitoring_system = None
current_results = None
session_data = {}  # 存储会话数据

def init_systems():
    """初始化所有系统模块"""
    global inversion_engine, warning_system, monitoring_system
    
    config = Config()
    
    # 初始化反算引擎
    inversion_engine = SourceInversionEngine(config.get_algorithm_config())
    logger.info("反算引擎初始化完成")
    
    # 初始化三色预警系统
    warning_system = ThreeColorWarningSystem(config.get_algorithm_config())
    logger.info("三色预警系统初始化完成")
    
    # 初始化实时监控系统
    monitoring_system = RealTimeMonitoringSystem(config.get_algorithm_config())
    
    # 添加示例监测站
    stations = [
        MonitoringStation(
            station_id='ST001',
            name='监测站A',
            latitude=39.9093,
            longitude=116.3974,
            x=1000, y=500,
            sensors=['pm25', 'pm10', 'wind_speed', 'wind_direction']
        ),
        MonitoringStation(
            station_id='ST002',
            name='监测站B',
            latitude=39.9193,
            longitude=116.4074,
            x=-800, y=1200,
            sensors=['pm25', 'pm10', 'temperature', 'humidity']
        ),
        MonitoringStation(
            station_id='ST003',
            name='监测站C',
            latitude=39.8993,
            longitude=116.3874,
            x=500, y=-600,
            sensors=['pm25', 'wind_speed', 'wind_direction']
        )
    ]
    
    for station in stations:
        monitoring_system.add_monitoring_station(station)
    
    # 注册预警回调
    monitoring_system.register_alert_callback(handle_realtime_alert)
    
    # 启动监控系统
    monitoring_system.start_monitoring()
    
    logger.info("实时监控系统初始化完成")

def handle_realtime_alert(alert: RealTimeAlert):
    """处理实时预警的回调函数"""
    logger.info(f"实时预警: {alert.alert_id} - {alert.message}")
    # 这里可以添加更多处理逻辑，比如发送通知等

@app.route('/dashboard')
def dashboard():
    """主控制台页面"""
    try:
        # 获取系统统计信息
        system_stats = monitoring_system.get_system_statistics() if monitoring_system else {}
        warning_stats = warning_system.get_warning_statistics() if warning_system else {}
        
        # 获取活跃预警
        active_alerts = monitoring_system.get_active_alerts() if monitoring_system else []
        warning_alerts = warning_system.get_active_alerts() if warning_system else []
        
        dashboard_data = {
            'system_statistics': system_stats,
            'warning_statistics': warning_stats,
            'active_realtime_alerts': active_alerts,
            'active_warning_alerts': warning_alerts,
            'last_update': datetime.now().isoformat()
        }
        
        return render_template('dashboard.html', data=dashboard_data)
        
    except Exception as e:
        logger.error(f"主控制台数据获取失败: {e}")
        return render_template('dashboard.html', data={'error': str(e)})

@app.route('/api/warnings')
def get_warnings():
    """获取三色预警信息"""
    if not warning_system:
        return jsonify({'error': '预警系统未初始化'}), 500
    
    try:
        active_alerts = warning_system.get_active_alerts()
        statistics = warning_system.get_warning_statistics()
        
        return jsonify({
            'success': True,
            'active_alerts': active_alerts,
            'statistics': statistics
        })
        
    except Exception as e:
        logger.error(f"获取预警信息失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/stations')
def get_monitoring_stations():
    """获取监测站信息"""
    if not monitoring_system:
        return jsonify({'error': '监控系统未初始化'}), 500
    
    try:
        stations_data = []
        for station_id, station in monitoring_system.stations.items():
            station_info = {
                'station_id': station.station_id,
                'name': station.name,
                'latitude': station.latitude,
                'longitude': station.longitude,
                'x': station.x,
                'y': station.y,
                'is_active': station.is_active,
                'sensors': station.sensors,
                'last_update': station.last_update.isoformat() if station.last_update else None,
                'data_quality_score': station.data_quality_score
            }
            stations_data.append(station_info)
        
        return jsonify({
            'success': True,
            'stations': stations_data,
            'total_count': len(stations_data)
        })
        
    except Exception as e:
        logger.error(f"获取监测站信息失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/data/<station_id>')
def get_station_data(station_id):
    """获取指定监测站数据"""
    if not monitoring_system:
        return jsonify({'error': '监控系统未初始化'}), 500
    
    try:
        hours = request.args.get('hours', 1, type=int)
        readings = monitoring_system.get_latest_readings(station_id, hours)
        
        readings_data = []
        for reading in readings:
            reading_info = {
                'station_id': reading.station_id,
                'sensor_type': reading.sensor_type,
                'value': reading.value,
                'timestamp': reading.timestamp.isoformat(),
                'unit': reading.unit,
                'quality_flag': reading.quality_flag
            }
            readings_data.append(reading_info)
        
        return jsonify({
            'success': True,
            'station_id': station_id,
            'readings': readings_data,
            'count': len(readings_data)
        })
        
    except Exception as e:
        logger.error(f"获取监测站数据失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/simulate', methods=['POST'])
def simulate_monitoring_data():
    """模拟监控数据"""
    if not monitoring_system:
        return jsonify({'error': '监控系统未初始化'}), 500
    
    try:
        data = request.get_json()
        station_id = data.get('station_id', 'ST001')
        duration = data.get('duration_minutes', 60)
        
        # 在后台线程中运行模拟
        import threading
        simulation_thread = threading.Thread(
            target=monitoring_system.simulate_sensor_data,
            args=(station_id, duration)
        )
        simulation_thread.daemon = True
        simulation_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'开始模拟 {station_id} 的数据，持续 {duration} 分钟'
        })
        
    except Exception as e:
        logger.error(f"模拟数据失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['GET', 'POST'])
def upload_data():
    """数据上传页面"""
    if request.method == 'GET':
        return render_template('upload.html')
    
    try:
        # 处理文件上传
        monitoring_files = request.files.getlist('monitoring_data')
        meteorological_file = request.files.get('meteorological_data')
        
        if not monitoring_files or not meteorological_file:
            return jsonify({'error': '请上传监测数据和气象数据文件'}), 400
        
        # 读取监测数据
        monitoring_data = {}
        for file in monitoring_files:
            if file.filename.endswith('.csv'):
                station_name = file.filename.replace('.csv', '')
                df = pd.read_csv(file)
                monitoring_data[station_name] = df
        
        # 读取气象数据
        meteorological_data = pd.read_csv(meteorological_file)
        
        # 数据验证
        validation_result = validate_uploaded_data(monitoring_data, meteorological_data)
        
        if not validation_result['valid']:
            return jsonify({'error': validation_result['message']}), 400
        
        # 存储数据到session或临时文件
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return jsonify({
            'success': True,
            'message': '数据上传成功',
            'session_id': session_id,
            'monitoring_stations': list(monitoring_data.keys()),
            'data_summary': get_data_summary(monitoring_data, meteorological_data)
        })
        
    except Exception as e:
        logger.error(f"数据上传失败: {e}")
        return jsonify({'error': f'数据上传失败: {str(e)}'}), 500

@app.route('/run_inversion', methods=['POST'])
def run_inversion():
    """运行污染源反算"""
    global current_results
    
    try:
        data = request.get_json()
        
        # 获取参数
        algorithm_params = data.get('algorithm_params', {})
        
        # 模拟数据（实际应用中从上传的数据获取）
        monitoring_data, meteorological_data = generate_sample_data()
        
        # 更新算法参数
        if inversion_engine:
            inversion_engine.config.update(algorithm_params)
        else:
            init_inversion_engine()
        
        # 运行反算
        logger.info("开始运行污染源反算")
        results = inversion_engine.run_complete_inversion(monitoring_data, meteorological_data)
        
        current_results = results
        
        return jsonify({
            'success': True,
            'message': '反算完成',
            'results': {
                'final_solution': results['final_solution'],
                'validation_metrics': results['validation'],
                'computation_time': results['computation_time'],
                'data_quality': results['data_quality']
            }
        })
        
    except Exception as e:
        logger.error(f"反算运行失败: {e}")
        return jsonify({'error': f'反算运行失败: {str(e)}'}), 500

@app.route('/get_results')
def get_results():
    """获取反算结果"""
    global current_results
    
    if current_results is None:
        return jsonify({'error': '暂无反算结果'}), 404
    
    return jsonify(current_results)

@app.route('/visualization')
def visualization():
    """可视化页面"""
    return render_template('visualization.html')

@app.route('/generate_plots')
def generate_plots():
    """生成可视化图表"""
    global current_results
    
    if current_results is None:
        return jsonify({'error': '暂无反算结果'}), 404
    
    try:
        plots = {}
        
        # 1. 收敛曲线
        plots['convergence'] = create_convergence_plot(current_results)
        
        # 2. 浓度场分布
        plots['concentration_field'] = create_concentration_field_plot(current_results)
        
        # 3. 验证散点图
        plots['validation_scatter'] = create_validation_scatter_plot(current_results)
        
        # 4. 算法性能对比
        plots['algorithm_comparison'] = create_algorithm_comparison_plot(current_results)
        
        return jsonify({
            'success': True,
            'plots': plots
        })
        
    except Exception as e:
        logger.error(f"图表生成失败: {e}")
        return jsonify({'error': f'图表生成失败: {str(e)}'}), 500

def generate_sample_data():
    """生成示例数据（用于演示）"""
    
    # 生成监测数据
    np.random.seed(42)
    
    monitoring_data = {}
    
    # 创建3个监测站
    stations = [
        {'name': 'Station_A', 'x': 1000, 'y': 500},
        {'name': 'Station_B', 'x': -800, 'y': 1200},
        {'name': 'Station_C', 'x': 500, 'y': -600}
    ]
    
    for station in stations:
        data = []
        for i in range(24):  # 24小时数据
            timestamp = pd.Timestamp('2024-01-01') + pd.Timedelta(hours=i)
            
            # 模拟浓度数据（添加噪声）
            base_conc = 50 + 30 * np.sin(i * np.pi / 12) + np.random.normal(0, 5)
            concentration = max(0, base_conc)
            
            data.append({
                'timestamp': timestamp,
                'x': station['x'],
                'y': station['y'],
                'concentration': concentration
            })
        
        monitoring_data[station['name']] = pd.DataFrame(data)
    
    # 生成气象数据
    meteo_data = []
    for i in range(24):
        timestamp = pd.Timestamp('2024-01-01') + pd.Timedelta(hours=i)
        
        # 模拟气象数据
        wind_speed = 3 + 2 * np.sin(i * np.pi / 12) + np.random.normal(0, 0.5)
        wind_direction = 180 + 30 * np.sin(i * np.pi / 6) + np.random.normal(0, 10)
        
        meteo_data.append({
            'timestamp': timestamp,
            'wind_speed': max(0.1, wind_speed),
            'wind_direction': wind_direction % 360,
            'temperature': 20 + 5 * np.sin(i * np.pi / 12),
            'humidity': 60 + 20 * np.sin(i * np.pi / 8),
            'stability_class': 'D'
        })
    
    meteorological_data = pd.DataFrame(meteo_data)
    
    return monitoring_data, meteorological_data

def create_convergence_plot(results):
    """创建收敛曲线图"""
    
    fig = go.Figure()
    
    # 遗传算法收敛曲线
    ga_history = results['genetic_algorithm']['convergence_history']
    fig.add_trace(go.Scatter(
        x=list(range(len(ga_history))),
        y=ga_history,
        mode='lines+markers',
        name='遗传算法',
        line=dict(color='blue')
    ))
    
    # 模式搜索收敛曲线
    ps_history = results['pattern_search']['convergence_history']
    fig.add_trace(go.Scatter(
        x=list(range(len(ps_history))),
        y=ps_history,
        mode='lines+markers',
        name='模式搜索',
        line=dict(color='red')
    ))
    
    fig.update_layout(
        title='算法收敛曲线',
        xaxis_title='迭代次数',
        yaxis_title='适应度值',
        yaxis_type='log'
    )
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)

def create_concentration_field_plot(results):
    """创建浓度场分布图"""
    
    conc_field = results['concentration_field']
    
    fig = go.Figure(data=go.Contour(
        x=conc_field['x_grid'][0],
        y=[row[0] for row in conc_field['y_grid']],
        z=conc_field['concentration'],
        colorscale='Viridis',
        contours=dict(
            showlabels=True,
            labelfont=dict(size=12, color='white')
        )
    ))
    
    # 添加污染源位置
    solution = results['final_solution']
    fig.add_trace(go.Scatter(
        x=[solution['x']],
        y=[solution['y']],
        mode='markers',
        marker=dict(size=15, color='red', symbol='star'),
        name='预测污染源'
    ))
    
    fig.update_layout(
        title='污染物浓度场分布',
        xaxis_title='X坐标 (m)',
        yaxis_title='Y坐标 (m)'
    )
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)

def create_validation_scatter_plot(results):
    """创建验证散点图"""
    
    validation = results['validation']
    
    fig = go.Figure()
    
    # 散点图
    fig.add_trace(go.Scatter(
        x=validation['observations'],
        y=validation['predictions'],
        mode='markers',
        name='预测vs观测',
        marker=dict(size=8, opacity=0.7)
    ))
    
    # 1:1线
    min_val = min(min(validation['observations']), min(validation['predictions']))
    max_val = max(max(validation['observations']), max(validation['predictions']))
    
    fig.add_trace(go.Scatter(
        x=[min_val, max_val],
        y=[min_val, max_val],
        mode='lines',
        name='1:1线',
        line=dict(color='red', dash='dash')
    ))
    
    fig.update_layout(
        title=f'模型验证 (R² = {validation["r_squared"]:.3f})',
        xaxis_title='观测浓度 (μg/m³)',
        yaxis_title='预测浓度 (μg/m³)'
    )
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)

def create_algorithm_comparison_plot(results):
    """创建算法性能对比图"""
    
    algorithms = ['遗传算法', '模式搜索']
    fitness_values = [
        results['genetic_algorithm']['best_fitness'],
        results['pattern_search']['best_fitness']
    ]
    
    fig = go.Figure(data=[
        go.Bar(x=algorithms, y=fitness_values, 
               text=[f'{val:.6f}' for val in fitness_values],
               textposition='auto')
    ])
    
    fig.update_layout(
        title='算法性能对比',
        xaxis_title='算法',
        yaxis_title='最优适应度值',
        yaxis_type='log'
    )
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)

if __name__ == '__main__':
    init_systems()
    app.run(debug=True, host='0.0.0.0', port=5000)

@app.route('/api/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """确认预警"""
    if not monitoring_system:
        return jsonify({'error': '监控系统未初始化'}), 500
    
    try:
        success = monitoring_system.acknowledge_alert(alert_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'预警 {alert_id} 已确认'
            })
        else:
            return jsonify({'error': f'预警 {alert_id} 不存在'}), 404
            
    except Exception as e:
        logger.error(f"确认预警失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/dashboard')
def export_dashboard_data():
    """导出主控制台数据"""
    try:
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'system_statistics': monitoring_system.get_system_statistics() if monitoring_system else {},
            'warning_statistics': warning_system.get_warning_statistics() if warning_system else {},
            'active_alerts': monitoring_system.get_active_alerts() if monitoring_system else [],
            'stations': [{
                'station_id': station.station_id,
                'name': station.name,
                'is_active': station.is_active,
                'last_update': station.last_update.isoformat() if station.last_update else None
            } for station in monitoring_system.stations.values()] if monitoring_system else []
        }
        
        # 创建临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
            temp_filepath = f.name
        
        return send_file(temp_filepath, 
                        as_attachment=True,
                        download_name=f'dashboard_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                        mimetype='application/json')
        
    except Exception as e:
        logger.error(f"导出数据失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/status')
def get_system_status():
    """获取系统状态"""
    try:
        status = {
            'timestamp': datetime.now().isoformat(),
            'components': {
                'inversion_engine': inversion_engine is not None,
                'warning_system': warning_system is not None,
                'monitoring_system': monitoring_system is not None and monitoring_system.is_running
            },
            'statistics': {
                'monitoring': monitoring_system.get_system_statistics() if monitoring_system else {},
                'warnings': warning_system.get_warning_statistics() if warning_system else {}
            }
        }
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return jsonify({'error': str(e)}), 500