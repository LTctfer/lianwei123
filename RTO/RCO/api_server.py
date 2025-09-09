#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
废气处理设备预警系统 - API服务器
提供通过API接口获取预警消息的功能
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
from datetime import datetime
from warning_system_core import WarningSystem

class WarningAPIHandler(BaseHTTPRequestHandler):
    """处理API请求的HTTP处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # 设置跨域访问
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        if path == '/api/warnings':
            self.get_warnings()
        elif path == '/api/rules':
            self.get_rules()
        elif path == '/api/summary':
            self.get_summary()
        else:
            self.send_error(404, "接口未找到")
    
    def do_OPTIONS(self):
        """处理OPTIONS请求（用于CORS预检）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def get_warnings(self):
        """获取所有预警信息"""
        try:
            # 获取活跃预警和已解决预警
            active_warnings = [self.serialize_record(record) for record in self.server.warning_system.rule_engine.active_warnings.values()]
            resolved_warnings = [self.serialize_record(record) for record in self.server.warning_system.rule_engine.warning_records]
            
            response = {
                'timestamp': datetime.now().isoformat(),
                'active_warnings': active_warnings,
                'resolved_warnings': resolved_warnings,
                'total_active': len(active_warnings),
                'total_resolved': len(resolved_warnings)
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            error_response = {
                'error': 'Internal server error',
                'message': str(e)
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
    
    def get_rules(self):
        """获取所有规则信息"""
        try:
            rules = self.server.warning_system.rule_engine.get_all_rules()
            response = {
                'timestamp': datetime.now().isoformat(),
                'rules': rules,
                'total': len(rules)
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            error_response = {
                'error': 'Internal server error',
                'message': str(e)
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
    
    def get_summary(self):
        """获取违规汇总信息"""
        try:
            summary = self.server.warning_system.rule_engine.get_violation_summary()
            response = {
                'timestamp': datetime.now().isoformat(),
                'summary': summary
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            error_response = {
                'error': 'Internal server error',
                'message': str(e)
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
    
    def serialize_record(self, record):
        """序列化预警记录"""
        # 将数据类转换为字典，并处理时间字段
        record_dict = {
            'record_id': record.record_id,
            'rule_id': record.rule_id,
            'rule_name': record.rule_name,
            'start_time': record.start_time.isoformat() if record.start_time else None,
            'end_time': record.end_time.isoformat() if record.end_time else None,
            'duration': record.duration,
            'max_value': record.max_value,
            'min_value': record.min_value,
            'avg_value': record.avg_value,
            'severity': record.severity,
            'status': record.status,
            'affected_equipment': record.affected_equipment
        }
        return record_dict

class APIServer(HTTPServer):
    """扩展的HTTP服务器，用于提供预警API服务"""
    
    def __init__(self, host, port, warning_system):
        """
        初始化API服务器
        
        Args:
            host: 服务器主机地址
            port: 服务器端口
            warning_system: 预警系统实例
        """
        super().__init__((host, port), WarningAPIHandler)
        self.warning_system = warning_system
        self.host = host
        self.port = port

def run_api_server():
    """运行API服务器"""
    print("🏭 废气处理设备预警系统 - API服务器")
    print("=" * 50)
    
    # 创建预警系统实例
    warning_system = WarningSystem()
    
    # 创建并启动API服务器
    host = "localhost"
    port = 8080
    server = APIServer(host, port, warning_system)
    
    print(f"🚀 API服务器启动成功!")
    print(f"📍 访问地址: http://{host}:{port}")
    print(f"📋 可用接口:")
    print(f"   GET /api/warnings - 获取所有预警信息")
    print(f"   GET /api/rules    - 获取所有规则信息")
    print(f"   GET /api/summary  - 获取违规汇总信息")
    print(f"🛑 按 Ctrl+C 停止服务器")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")

if __name__ == "__main__":
    run_api_server()