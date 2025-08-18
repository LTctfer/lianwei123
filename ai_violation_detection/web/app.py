#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI违规检测Web应用
基于Flask的Web界面，提供图像上传、检测和结果展示功能
"""

import os
import sys
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import cv2
import numpy as np

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.yolo_violation import ViolationDetector
from models.dust_detector import DustDetector
from utils.image_processor import ImageProcessor
from utils.alert_system import AlertSystem

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 配置文件上传
UPLOAD_FOLDER = 'static/uploads'
RESULT_FOLDER = 'static/results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# 初始化组件
violation_detector = ViolationDetector()
dust_detector = DustDetector()
image_processor = ImageProcessor()
alert_system = AlertSystem()

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传和检测"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式'}), 400
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        upload_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(upload_path)
        
        # 加载图像
        image = image_processor.load_image(upload_path)
        if image is None:
            return jsonify({'error': '无法加载图像文件'}), 400
        
        # 图像预处理
        processed_image = image_processor.preprocess_image(image, target_size=(1024, 768))
        
        # 获取检测参数
        confidence_threshold = float(request.form.get('confidence', 0.5))
        enable_dust_detection = request.form.get('dust_detection', 'false') == 'true'
        
        # 设置置信度阈值
        violation_detector.set_confidence_threshold(confidence_threshold)
        
        # 执行违规检测
        detection_result = violation_detector.detect_violations(
            processed_image, 
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # 执行扬尘检测（如果启用）
        dust_result = None
        if enable_dust_detection:
            dust_result = dust_detector.detect_dust(processed_image)
        
        # 绘制检测结果
        result_image = violation_detector.draw_detections(processed_image, detection_result['detections'])
        
        # 如果有扬尘检测结果，也绘制上去
        if dust_result and dust_result['dust_detected']:
            result_image = dust_detector.draw_dust_detections(result_image, dust_result)
        
        # 添加水印
        result_image = image_processor.add_watermark(result_image)
        
        # 保存结果图像
        result_filename = f"result_{unique_filename}"
        result_path = os.path.join(RESULT_FOLDER, result_filename)
        cv2.imwrite(result_path, result_image)
        
        # 生成报警
        alerts = []
        for detection in detection_result['detections']:
            alert = alert_system.create_alert(detection, upload_path)
            if alert:
                alerts.append(alert)
        
        # 如果有扬尘检测，也生成相应报警
        if dust_result and dust_result['dust_detected']:
            for dust_detection in dust_result['detections']:
                # 转换扬尘检测结果为标准格式
                dust_alert_data = {
                    'id': f"dust_{uuid.uuid4()}",
                    'class_name': 'dust_emission',
                    'confidence': dust_detection['confidence'],
                    'alert_level': dust_detection['alert_level'],
                    'center': {
                        'x': dust_detection['bbox']['x'] + dust_detection['bbox']['width'] // 2,
                        'y': dust_detection['bbox']['y'] + dust_detection['bbox']['height'] // 2
                    },
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                alert = alert_system.create_alert(dust_alert_data, upload_path)
                if alert:
                    alerts.append(alert)
        
        # 准备响应数据
        response_data = {
            'success': True,
            'original_image': f'/static/uploads/{unique_filename}',
            'result_image': f'/static/results/{result_filename}',
            'detection_result': detection_result,
            'dust_result': dust_result,
            'alerts': alerts,
            'processing_time': detection_result['processing_time'],
            'total_violations': detection_result['total_violations'] + (dust_result['dust_count'] if dust_result else 0)
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': f'处理失败: {str(e)}'}), 500

@app.route('/detect_realtime', methods=['POST'])
def detect_realtime():
    """实时检测接口（用于摄像头或视频流）"""
    try:
        # 获取base64图像数据
        image_data = request.json.get('image_data')
        if not image_data:
            return jsonify({'error': '没有图像数据'}), 400
        
        # 解码图像
        image = image_processor.base64_to_image(image_data)
        if image is None:
            return jsonify({'error': '无法解码图像'}), 400
        
        # 调整图像尺寸以提高处理速度
        image = image_processor.resize_image(image, max_size=640)
        
        # 执行检测
        detection_result = violation_detector.detect_violations(image)
        
        # 只返回关键信息以减少数据传输
        response_data = {
            'success': True,
            'detections': detection_result['detections'],
            'total_violations': detection_result['total_violations'],
            'processing_time': detection_result['processing_time']
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': f'实时检测失败: {str(e)}'}), 500

@app.route('/alerts')
def alerts_page():
    """报警页面"""
    return render_template('alerts.html')

@app.route('/api/alerts')
def get_alerts():
    """获取报警列表API"""
    try:
        limit = int(request.args.get('limit', 50))
        status = request.args.get('status', None)
        
        alerts = alert_system.get_alerts(limit=limit, status=status)
        return jsonify({'success': True, 'alerts': alerts})
        
    except Exception as e:
        return jsonify({'error': f'获取报警失败: {str(e)}'}), 500

@app.route('/api/alerts/<alert_id>/status', methods=['PUT'])
def update_alert_status(alert_id):
    """更新报警状态"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': '缺少状态参数'}), 400
        
        success = alert_system.update_alert_status(alert_id, new_status)
        
        if success:
            return jsonify({'success': True, 'message': '状态更新成功'})
        else:
            return jsonify({'error': '状态更新失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'更新失败: {str(e)}'}), 500

@app.route('/statistics')
def statistics_page():
    """统计页面"""
    return render_template('statistics.html')

@app.route('/api/statistics')
def get_statistics():
    """获取统计数据API"""
    try:
        days = int(request.args.get('days', 7))
        stats = alert_system.get_statistics(days=days)
        return jsonify({'success': True, 'statistics': stats})
        
    except Exception as e:
        return jsonify({'error': f'获取统计失败: {str(e)}'}), 500

@app.route('/api/model_info')
def get_model_info():
    """获取模型信息"""
    try:
        model_info = violation_detector.get_model_info()
        return jsonify({'success': True, 'model_info': model_info})
        
    except Exception as e:
        return jsonify({'error': f'获取模型信息失败: {str(e)}'}), 500

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """处理配置"""
    if request.method == 'GET':
        # 返回当前配置
        config = {
            'confidence_threshold': violation_detector.confidence_threshold,
            'dust_detection_enabled': True,
            'alert_levels': violation_detector.alert_levels
        }
        return jsonify({'success': True, 'config': config})
    
    elif request.method == 'POST':
        # 更新配置
        try:
            data = request.get_json()
            
            if 'confidence_threshold' in data:
                violation_detector.set_confidence_threshold(data['confidence_threshold'])
            
            return jsonify({'success': True, 'message': '配置更新成功'})
            
        except Exception as e:
            return jsonify({'error': f'配置更新失败: {str(e)}'}), 500

@app.route('/help')
def help_page():
    """帮助页面"""
    return render_template('help.html')

@app.errorhandler(413)
def too_large(e):
    """文件过大错误处理"""
    return jsonify({'error': '文件大小超过限制（最大16MB）'}), 413

@app.errorhandler(404)
def not_found(e):
    """404错误处理"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """500错误处理"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("🚀 启动AI违规检测系统...")
    print("📱 访问地址: http://localhost:5000")
    print("📊 功能包括:")
    print("   - 图像上传检测")
    print("   - 实时视频检测")
    print("   - 智能报警系统")
    print("   - 统计分析")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
