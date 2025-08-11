#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
吸附曲线预警系统 HTTP API 接口
基于Flask框架提供RESTful API服务
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import traceback
from datetime import datetime
import pandas as pd
from werkzeug.utils import secure_filename
from adsorption_api import get_warning_system_data, analyze_adsorption_data

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_error_response(message: str, code: int = 400):
    """创建错误响应"""
    return jsonify({
        'success': False,
        'error': message,
        'timestamp': datetime.now().isoformat()
    }), code

def create_success_response(data: dict):
    """创建成功响应"""
    response_data = {
        'success': True,
        'timestamp': datetime.now().isoformat()
    }
    response_data.update(data)
    return jsonify(response_data)

@app.route('/', methods=['GET'])
def home():
    """API首页"""
    return jsonify({
        'message': '吸附曲线预警系统 HTTP API',
        'version': '1.0.0',
        'endpoints': {
            'GET /': '查看API信息',
            'POST /api/analyze/warning': '预警系统分析（推荐）',
            'POST /api/analyze/complete': '完整数据分析',
            'POST /api/analyze/file': '通过文件路径分析',
            'GET /api/health': '健康检查'
        },
        'supported_formats': ['CSV', 'XLSX', 'XLS'],
        'max_file_size': '16MB'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': '吸附曲线预警系统'
    })

@app.route('/api/analyze/warning', methods=['POST'])
def analyze_warning_api():
    """
    预警系统分析接口（推荐使用）
    
    请求方式：POST
    Content-Type: multipart/form-data
    参数：
        file: 上传的数据文件（CSV/XLSX/XLS）
    
    返回：
        {
            "success": true,
            "data_points": [...],
            "warning_point": {...},
            "statistics": {...},
            "timestamp": "2025-01-01T12:00:00"
        }
    """
    try:
        # 检查文件是否存在
        if 'file' not in request.files:
            return create_error_response('未找到上传文件，请使用"file"字段上传文件')
        
        file = request.files['file']
        if file.filename == '':
            return create_error_response('未选择文件')
        
        if not allowed_file(file.filename):
            return create_error_response(f'不支持的文件格式，仅支持: {", ".join(ALLOWED_EXTENSIONS)}')
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(file_path)
        
        try:
            # 调用预警系统分析
            result = get_warning_system_data(file_path)
            
            # 清理临时文件
            if os.path.exists(file_path):
                os.remove(file_path)
            
            if result['success']:
                return create_success_response({
                    'data_points': result['data_points'],
                    'warning_point': result['warning_point'],
                    'statistics': result['statistics'],
                    'file_info': {
                        'original_name': file.filename,
                        'file_size': len(file.read()),
                        'processed_at': datetime.now().isoformat()
                    }
                })
            else:
                return create_error_response(f"数据分析失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            # 清理临时文件
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
            
    except Exception as e:
        return create_error_response(f"处理请求时发生错误: {str(e)}", 500)

@app.route('/api/analyze/complete', methods=['POST'])
def analyze_complete_api():
    """
    完整数据分析接口
    
    请求方式：POST
    Content-Type: multipart/form-data
    参数：
        file: 上传的数据文件（CSV/XLSX/XLS）
    
    返回：
        {
            "success": true,
            "all_data_points": [...],
            "warning_points": [...],
            "statistics": {...},
            "data_summary": {...},
            "timestamp": "2025-01-01T12:00:00"
        }
    """
    try:
        # 检查文件是否存在
        if 'file' not in request.files:
            return create_error_response('未找到上传文件，请使用"file"字段上传文件')
        
        file = request.files['file']
        if file.filename == '':
            return create_error_response('未选择文件')
        
        if not allowed_file(file.filename):
            return create_error_response(f'不支持的文件格式，仅支持: {", ".join(ALLOWED_EXTENSIONS)}')
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(file_path)
        
        try:
            # 调用完整数据分析
            result = analyze_adsorption_data(file_path)
            
            # 清理临时文件
            if os.path.exists(file_path):
                os.remove(file_path)
            
            if result['success']:
                return create_success_response({
                    'all_data_points': result['all_data_points'],
                    'warning_points': result['warning_points'],
                    'statistics': result['statistics'],
                    'data_summary': result['data_summary'],
                    'file_info': {
                        'original_name': file.filename,
                        'processed_at': datetime.now().isoformat()
                    }
                })
            else:
                return create_error_response(f"数据分析失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            # 清理临时文件
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
            
    except Exception as e:
        return create_error_response(f"处理请求时发生错误: {str(e)}", 500)

@app.route('/api/analyze/file', methods=['POST'])
def analyze_file_path_api():
    """
    通过文件路径分析接口（用于服务器本地文件）
    
    请求方式：POST
    Content-Type: application/json
    参数：
        {
            "file_path": "path/to/data/file.csv",
            "analysis_type": "warning" | "complete"  // 可选，默认为"warning"
        }
    
    返回：
        根据analysis_type返回对应的分析结果
    """
    try:
        data = request.get_json()
        if not data or 'file_path' not in data:
            return create_error_response('请提供file_path参数')
        
        file_path = data['file_path']
        analysis_type = data.get('analysis_type', 'warning')
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return create_error_response(f'文件不存在: {file_path}')
        
        # 检查文件扩展名
        if not allowed_file(file_path):
            return create_error_response(f'不支持的文件格式，仅支持: {", ".join(ALLOWED_EXTENSIONS)}')
        
        # 根据分析类型调用对应函数
        if analysis_type == 'warning':
            result = get_warning_system_data(file_path)
            if result['success']:
                return create_success_response({
                    'data_points': result['data_points'],
                    'warning_point': result['warning_point'],
                    'statistics': result['statistics'],
                    'analysis_type': 'warning',
                    'file_path': file_path
                })
        elif analysis_type == 'complete':
            result = analyze_adsorption_data(file_path)
            if result['success']:
                return create_success_response({
                    'all_data_points': result['all_data_points'],
                    'warning_points': result['warning_points'],
                    'statistics': result['statistics'],
                    'data_summary': result['data_summary'],
                    'analysis_type': 'complete',
                    'file_path': file_path
                })
        else:
            return create_error_response('analysis_type参数无效，请使用"warning"或"complete"')
        
        # 如果分析失败
        return create_error_response(f"数据分析失败: {result.get('error', '未知错误')}")
        
    except Exception as e:
        return create_error_response(f"处理请求时发生错误: {str(e)}", 500)

@app.errorhandler(413)
def too_large(e):
    """文件过大错误处理"""
    return create_error_response('上传文件过大，最大支持16MB', 413)

@app.errorhandler(404)
def not_found(e):
    """404错误处理"""
    return create_error_response('接口不存在', 404)

@app.errorhandler(500)
def internal_error(e):
    """500错误处理"""
    return create_error_response('服务器内部错误', 500)

if __name__ == '__main__':
    print("🚀 启动吸附曲线预警系统 HTTP API 服务")
    print("📋 可用接口:")
    print("  GET  /                     - API信息")
    print("  GET  /api/health           - 健康检查")
    print("  POST /api/analyze/warning  - 预警系统分析（文件上传）")
    print("  POST /api/analyze/complete - 完整数据分析（文件上传）")
    print("  POST /api/analyze/file     - 文件路径分析（JSON请求）")
    print("\n🌐 服务地址: http://localhost:5000")
    print("📚 API文档: 请访问根路径查看接口说明")
    
    # 开发模式启动
    app.run(host='0.0.0.0', port=5000, debug=True)
