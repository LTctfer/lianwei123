#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
污染源溯源系统 Web 界面
基于Flask框架的交互式Web应用
"""

import os
import json
import time
import uuid
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for, Response
from werkzeug.utils import secure_filename
import numpy as np
from datetime import datetime
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt

# 导入现有模块
from pollution_source_tracker import PollutionSourceTracker, MonitoringData, MeteorologicalData, PollutionSource
from data_processor import DataProcessor, Visualizer
from demo import PollutionSourceDemo

app = Flask(__name__)
app.secret_key = 'pollution_source_tracker_secret_key_2024'

# 配置
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'json', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('static/images', exist_ok=True)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_plot_to_base64(fig):
    """将matplotlib图表转换为base64字符串"""
    img_buffer = BytesIO()
    fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close(fig)
    return img_base64

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    try:
        if 'monitoring_file' not in request.files and 'meteorological_file' not in request.files:
            flash('请选择要上传的文件')
            return redirect(url_for('index'))
        
        uploaded_files = {}
        
        # 处理监测数据文件
        if 'monitoring_file' in request.files:
            file = request.files['monitoring_file']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                uploaded_files['monitoring'] = filepath
        
        # 处理气象数据文件
        if 'meteorological_file' in request.files:
            file = request.files['meteorological_file']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                uploaded_files['meteorological'] = filepath
        
        if uploaded_files:
            flash('文件上传成功！')
            return jsonify({'status': 'success', 'files': uploaded_files})
        else:
            flash('文件上传失败，请检查文件格式')
            return jsonify({'status': 'error', 'message': '文件上传失败'})
            
    except Exception as e:
        flash(f'文件上传出错: {str(e)}')
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/manual_input')
def manual_input():
    """手动输入数据页面"""
    return render_template('manual_input.html')

@app.route('/demo_data')
def demo_data():
    """使用示例数据页面"""
    return render_template('demo_data.html')

@app.route('/advanced_settings')
def advanced_settings():
    """高级设置页面"""
    return render_template('advanced_settings.html')

@app.route('/monitoring')
def monitoring():
    """实时监控页面"""
    return render_template('monitoring.html')

@app.route('/process', methods=['POST'])
def process_data():
    """处理溯源请求"""
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 初始化进度
        progress_data[task_id] = {
            'status': 'starting',
            'progress': 0,
            'message': '正在初始化...'
        }

        data_source = request.json.get('data_source', 'demo')
        
        if data_source == 'demo':
            # 使用示例数据
            progress_data[task_id].update({
                'status': 'processing',
                'progress': 10,
                'message': '生成示例数据...'
            })
            demo = PollutionSourceDemo()
            monitoring_data, met_data = demo.generate_realistic_data()
            
        elif data_source == 'manual':
            # 处理手动输入的数据
            progress_data[task_id].update({
                'status': 'processing',
                'progress': 15,
                'message': '处理手动输入数据...'
            })

            try:
                monitoring_data = []
                met_data_dict = request.json.get('meteorological_data', {})

                # 验证气象数据
                required_met_fields = ['wind_speed', 'wind_direction', 'temperature', 'pressure', 'humidity']
                for field in required_met_fields:
                    if field not in met_data_dict or met_data_dict[field] == '':
                        raise ValueError(f'缺少必需的气象数据字段: {field}')

                # 处理监测站数据
                monitoring_data_list = request.json.get('monitoring_data', [])
                if not monitoring_data_list:
                    raise ValueError('至少需要一个监测站数据')

                for i, station_data in enumerate(monitoring_data_list):
                    try:
                        monitoring_data.append(MonitoringData(
                            station_id=station_data.get('station_id', f'站点{i+1}'),
                            x=float(station_data['x']),
                            y=float(station_data['y']),
                            z=float(station_data['z']),
                            concentration=float(station_data['concentration']),
                            timestamp=station_data.get('timestamp', datetime.now().isoformat())
                        ))
                    except (ValueError, KeyError) as e:
                        raise ValueError(f'监测站{i+1}数据格式错误: {str(e)}')

                # 处理气象数据
                met_data = MeteorologicalData(
                    wind_speed=float(met_data_dict['wind_speed']),
                    wind_direction=float(met_data_dict['wind_direction']),
                    temperature=float(met_data_dict['temperature']),
                    pressure=float(met_data_dict['pressure']),
                    humidity=float(met_data_dict['humidity']),
                    solar_radiation=float(met_data_dict.get('solar_radiation', 500.0)),  # 默认值
                    cloud_cover=float(met_data_dict.get('cloud_cover', 0.5)),  # 默认值
                    timestamp=met_data_dict.get('timestamp', datetime.now().isoformat())
                )

            except Exception as e:
                progress_data[task_id].update({
                    'status': 'error',
                    'progress': 0,
                    'message': f'数据处理失败: {str(e)}'
                })
                return jsonify({'status': 'error', 'message': f'手动输入数据处理失败: {str(e)}'})
            
        elif data_source == 'file':
            # 处理文件上传的数据
            # 这里需要实现文件解析逻辑
            flash('文件数据处理功能开发中')
            return jsonify({'status': 'error', 'message': '文件数据处理功能开发中'})
        
        # 执行溯源
        progress_data[task_id].update({
            'status': 'processing',
            'progress': 30,
            'message': '初始化溯源算法...'
        })

        tracker = PollutionSourceTracker()

        # 添加监测数据
        for data in monitoring_data:
            tracker.add_monitoring_data(data)

        # 设置气象数据
        tracker.set_meteorological_data(met_data)

        progress_data[task_id].update({
            'status': 'processing',
            'progress': 50,
            'message': '执行污染源溯源...'
        })

        # 执行溯源
        source_result = tracker.trace_pollution_source()
        
        progress_data[task_id].update({
            'status': 'processing',
            'progress': 70,
            'message': '验证溯源结果...'
        })

        # 验证结果
        verification_stats = tracker.verify_source(source_result)

        # 手动计算详细结果用于可视化
        detailed_results = []
        for monitor in monitoring_data:
            theoretical_conc = tracker.gaussian_model.calculate_concentration(
                source_result, monitor.x, monitor.y, monitor.z, met_data
            )
            absolute_error = abs(monitor.concentration - theoretical_conc)
            relative_error = (absolute_error / max(monitor.concentration, 1.0)) * 100

            detailed_results.append({
                'station_id': monitor.station_id,
                'observed': monitor.concentration,
                'predicted': theoretical_conc,
                'absolute_error': absolute_error,
                'relative_error': relative_error
            })
        
        progress_data[task_id].update({
            'status': 'processing',
            'progress': 85,
            'message': '生成可视化图表...'
        })

        # 生成可视化
        visualizer = Visualizer()
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 转换数据格式用于可视化
        data_dicts = []
        for data in monitoring_data:
            data_dicts.append({
                'x': data.x,
                'y': data.y,
                'z': data.z,
                'station_id': data.station_id,
                'concentration': data.concentration
            })
        
        # 生成监测站分布图
        visualizer.plot_monitoring_stations(
            monitoring_data=data_dicts,
            source_location=(source_result.x, source_result.y)
        )
        monitoring_plot = save_plot_to_base64(plt.gcf())
        
        # 生成验证结果图
        verification_data = []
        for result in detailed_results:
            verification_data.append({
                'station_id': result['station_id'],
                'observed': result['observed'],
                'predicted': result['predicted']
            })

        visualizer.plot_verification_results(verification_data)
        verification_plot = save_plot_to_base64(plt.gcf())
        
        progress_data[task_id].update({
            'status': 'completed',
            'progress': 100,
            'message': '分析完成！'
        })

        # 准备结果数据
        result_data = {
            'status': 'success',
            'task_id': task_id,
            'source_result': {
                'x': source_result.x,
                'y': source_result.y,
                'z': source_result.z,
                'emission_rate': source_result.emission_rate,
                'confidence': source_result.confidence
            },
            'verification_stats': verification_stats,
            'monitoring_plot': monitoring_plot,
            'verification_plot': verification_plot,
            'detailed_results': detailed_results
        }

        return jsonify(result_data)
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'处理过程中出错: {str(e)}'})

# 全局进度跟踪
progress_data = {}

@app.route('/progress/<task_id>')
def progress_stream(task_id):
    """Server-Sent Events进度流"""
    def generate():
        while True:
            if task_id in progress_data:
                data = progress_data[task_id]
                yield f"data: {json.dumps(data)}\n\n"

                # 如果任务完成，清理数据并结束流
                if data.get('status') in ['completed', 'error']:
                    del progress_data[task_id]
                    break
            else:
                yield f"data: {json.dumps({'status': 'waiting', 'message': '等待开始...'})}\n\n"

            time.sleep(0.5)  # 每0.5秒更新一次

    return Response(generate(), mimetype='text/event-stream')

@app.route('/results')
def results():
    """结果展示页面"""
    return render_template('results.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
