#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RTO/RCO废气处理设备预警系统 - 精简版
=================================

这是一个用于监控废气处理设备的预警系统，主要功能包括：
1. 实时数据监控
2. 预警规则检测
3. 可视化大屏展示
4. 历史数据分析

作者: AI Assistant
版本: 2.0 (精简版)
"""

import json
import random
import threading
import time
import webbrowser
from datetime import datetime, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class DataGenerator:
    """
    数据生成器 - 负责生成模拟的设备运行数据
    
    这个类模拟真实的RTO/RCO设备，生成包括温度、浓度、压力等关键参数的数据
    """
    
    def __init__(self):
        self.alert_history = []  # 告警历史记录
        self.equipment_status = {  # 设备状态
            '燃烧室': 'normal',
            '废气出口': 'normal', 
            '吸附设施': 'normal',
            '脱附设施': 'normal',
            '反应器': 'normal'
        }
    
    def generate_data(self) -> Dict:
        """
        生成一条实时数据
        
        Returns:
            Dict: 包含所有监控参数的字典
        """
        # 基础参数 - 正态分布生成，符合实际设备运行规律
        data = {
            'timestamp': datetime.now().isoformat(),
            'temperature_combustion': random.gauss(780, 30),    # 燃烧室温度 (℃)
            'temperature_outlet': random.gauss(45, 12),         # 废气出口温度 (℃)
            'concentration_in': random.gauss(200, 40),          # 进口浓度 (mg/m³)
            'concentration_out': random.gauss(20, 8),           # 出口浓度 (mg/m³)
            'temperature_adsorption': random.gauss(35, 6),      # 吸附温度 (℃)
            'temperature_desorption': random.gauss(105, 10),    # 脱附温度 (℃)
            'temperature_reactor': random.gauss(550, 50),       # 反应器出口温度 (℃)
            'pressure': random.gauss(1.2, 0.3),                # 系统压力 (MPa)
            'flow_rate': random.gauss(1000, 80),               # 流量 (m³/h)
            'efficiency': random.gauss(95, 3),                 # 处理效率 (%)
            'emergency_valve': 0,                              # 应急阀门状态
        }
        
        # 30%概率生成异常数据来触发告警
        if random.random() < 0.3:
            data.update(self._generate_alert_data())
        
        return data
    
    def _generate_alert_data(self) -> Dict:
        """
        生成异常数据来触发告警
        
        Returns:
            Dict: 包含异常参数的字典
        """
        alert_scenarios = [
            {'temperature_combustion': random.uniform(700, 759)},  # 燃烧室温度过低
            {'concentration_out': random.uniform(55, 90)},         # 出口浓度超标
            {'temperature_outlet': random.uniform(65, 85)},        # 出口温度过高
            {'temperature_reactor': random.uniform(610, 650)},     # 反应器温度过高
            {'emergency_valve': 1},                               # 应急阀门开启
        ]
        
        return random.choice(alert_scenarios)


class RuleEngine:
    """
    预警规则引擎 - 负责检测数据是否违反预设规则
    
    这个类定义了各种预警规则，并能够实时检测数据是否触发告警
    """
    
    def __init__(self):
        self.rules = self._init_rules()
    
    def _init_rules(self) -> List[Dict]:
        """
        初始化预警规则
        
        Returns:
            List[Dict]: 预警规则列表
        """
        return [
            {
                'id': 'R001',
                'name': '燃烧室温度不达标',
                'field': 'temperature_combustion',
                'condition': 'less_than',
                'threshold': 760,
                'unit': '℃',
                'severity': 'high',
                'description': '燃烧室温度必须保持在760℃以上'
            },
            {
                'id': 'R002', 
                'name': '废气出口浓度超标',
                'field': 'concentration_out',
                'condition': 'greater_than',
                'threshold': 50,
                'unit': 'mg/m³',
                'severity': 'critical',
                'description': '废气出口污染物浓度不得超过50mg/m³'
            },
            {
                'id': 'R003',
                'name': '出口温度超标', 
                'field': 'temperature_outlet',
                'condition': 'greater_than',
                'threshold': 60,
                'unit': '℃',
                'severity': 'medium',
                'description': '废气出口温度不得超过60℃'
            },
            {
                'id': 'R004',
                'name': '反应器温度异常',
                'field': 'temperature_reactor', 
                'condition': 'greater_than',
                'threshold': 600,
                'unit': '℃',
                'severity': 'critical',
                'description': '反应器出口温度不得超过600℃'
            },
            {
                'id': 'R005',
                'name': '应急阀门违规开启',
                'field': 'emergency_valve',
                'condition': 'equals',
                'threshold': 1,
                'unit': '',
                'severity': 'critical', 
                'description': '应急阀门不应在正常运行时开启'
            }
        ]
    
    def check_alerts(self, data: Dict) -> List[Dict]:
        """
        检查数据是否触发告警
        
        Args:
            data: 待检查的数据
            
        Returns:
            List[Dict]: 触发的告警列表
        """
        alerts = []
        
        for rule in self.rules:
            if self._evaluate_rule(rule, data):
                alert = {
                    'id': f"alert_{rule['id']}_{int(time.time())}",
                    'rule_id': rule['id'],
                    'name': rule['name'],
                    'value': data.get(rule['field'], 0),
                    'threshold': rule['threshold'],
                    'unit': rule['unit'],
                    'severity': rule['severity'],
                    'timestamp': datetime.now(),
                    'description': rule['description']
                }
                alerts.append(alert)
        
        return alerts
    
    def _evaluate_rule(self, rule: Dict, data: Dict) -> bool:
        """
        评估单个规则是否被触发
        
        Args:
            rule: 规则定义
            data: 数据
            
        Returns:
            bool: 是否触发规则
        """
        value = data.get(rule['field'], 0)
        threshold = rule['threshold']
        condition = rule['condition']
        
        if condition == 'greater_than':
            return value > threshold
        elif condition == 'less_than':
            return value < threshold
        elif condition == 'equals':
            return value == threshold
        
        return False


class WebDashboard:
    """
    Web监控大屏 - 提供美观的监控界面
    
    这个类创建一个现代化的Web界面，实时显示设备状态和告警信息
    """
    
    def __init__(self, port=8090):
        self.port = port
        self.data_generator = DataGenerator()
        self.rule_engine = RuleEngine()
        self.is_running = False
    
    def start(self):
        """启动Web服务器"""
        print(f"🚀 启动RTO/RCO监控大屏...")
        print(f"📱 访问地址: http://localhost:{self.port}")
        print(f"🛑 按 Ctrl+C 停止服务")
        
        # 自动打开浏览器
        webbrowser.open(f'http://localhost:{self.port}')
        
        # 启动HTTP服务器
        with HTTPServer(('localhost', self.port), self._create_handler()) as server:
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\n👋 服务器已停止")
    
    def _create_handler(self):
        """创建HTTP请求处理器"""
        data_generator = self.data_generator
        rule_engine = self.rule_engine
        
        class RequestHandler(SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/':
                    self.send_dashboard_html()
                elif self.path == '/api/data':
                    self.send_realtime_data()
                else:
                    super().do_GET()
            
            def send_dashboard_html(self):
                """发送监控大屏HTML页面"""
                html = self._get_dashboard_html()
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            
            def send_realtime_data(self):
                """发送实时数据API"""
                # 生成数据
                data = data_generator.generate_data()
                
                # 检查告警
                alerts = rule_engine.check_alerts(data)
                
                # 更新告警历史
                data_generator.alert_history.extend(alerts)
                
                # 保持最近100条告警记录
                if len(data_generator.alert_history) > 100:
                    data_generator.alert_history = data_generator.alert_history[-100:]
                
                # 更新设备状态
                for alert in alerts:
                    equipment_map = {
                        'R001': '燃烧室',
                        'R002': '废气出口', 
                        'R003': '废气出口',
                        'R004': '反应器',
                        'R005': '应急系统'
                    }
                    equipment = equipment_map.get(alert['rule_id'])
                    if equipment and equipment in data_generator.equipment_status:
                        status_map = {
                            'critical': 'critical',
                            'high': 'warning', 
                            'medium': 'warning',
                            'low': 'normal'
                        }
                        data_generator.equipment_status[equipment] = status_map.get(alert['severity'], 'warning')
                
                # 构建响应数据
                response = {
                    'data': data,
                    'alerts': [
                        {
                            'id': alert['id'],
                            'name': alert['name'],
                            'value': round(alert['value'], 1),
                            'threshold': alert['threshold'],
                            'unit': alert['unit'],
                            'severity': alert['severity'],
                            'time': alert['timestamp'].strftime('%H:%M:%S')
                        }
                        for alert in alerts
                    ],
                    'equipment_status': data_generator.equipment_status,
                    'recent_alerts': [
                        {
                            'name': alert['name'],
                            'severity': alert['severity'],
                            'time': alert['timestamp'].strftime('%H:%M:%S')
                        }
                        for alert in data_generator.alert_history[-5:]  # 最近5条告警
                    ]
                }
                
                json_data = json.dumps(response, ensure_ascii=False, default=str)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json_data.encode('utf-8'))
            
            def _get_dashboard_html(self):
                """获取监控大屏HTML代码"""
                return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RTO/RCO监控大屏</title>
    <style>
        /* 全局样式 */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #0c1445 0%, #1a1a2e 50%, #16213e 100%);
            color: #ffffff;
            overflow: hidden;
            height: 100vh;
        }
        
        /* 网格背景 */
        .grid-bg {
            position: absolute;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(0, 212, 255, 0.1) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 212, 255, 0.1) 1px, transparent 1px);
            background-size: 50px 50px;
            animation: gridMove 20s linear infinite;
            z-index: 0;
        }
        
        @keyframes gridMove {
            0% { transform: translate(0, 0); }
            100% { transform: translate(50px, 50px); }
        }
        
        /* 主容器 */
        .dashboard {
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            grid-template-rows: 80px 1fr 1fr 1fr;
            height: 100vh;
            gap: 20px;
            padding: 20px;
        }
        
        /* 标题栏 */
        .header {
            grid-column: 1 / -1;
            background: linear-gradient(90deg, rgba(0, 212, 255, 0.2), rgba(0, 150, 255, 0.2));
            border: 2px solid #00d4ff;
            border-radius: 15px;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            font-size: 2.5rem;
            color: #00d4ff;
            text-shadow: 0 0 20px #00d4ff;
            font-weight: bold;
        }
        
        .time-display {
            position: absolute;
            right: 30px;
            font-size: 1.2rem;
            color: #00ffff;
        }
        
        /* 监控面板 */
        .panel {
            background: linear-gradient(135deg, rgba(0, 40, 80, 0.8), rgba(0, 20, 40, 0.9));
            border: 2px solid #00d4ff;
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(15px);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .panel::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            transition: left 0.5s;
        }
        
        .panel:hover::before {
            left: 100%;
        }
        
        .panel:hover {
            border-color: #00ffff;
            box-shadow: 0 0 30px rgba(0, 255, 255, 0.3);
            transform: scale(1.02);
        }
        
        .panel-title {
            font-size: 1.3rem;
            font-weight: bold;
            margin-bottom: 15px;
            color: #00ffff;
            text-shadow: 0 0 10px #00ffff;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .panel-title::before {
            content: '';
            width: 4px;
            height: 20px;
            background: linear-gradient(to bottom, #00d4ff, #00ffff);
            border-radius: 2px;
        }
        
        /* 数值显示 */
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 10px 0;
            padding: 8px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            border-left: 3px solid #00d4ff;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #a0a0a0;
        }
        
        .metric-value {
            font-size: 1.4rem;
            font-weight: bold;
            color: #00ffff;
            text-shadow: 0 0 10px #00ffff;
        }
        
        .metric-value.warning {
            color: #ffaa00;
            text-shadow: 0 0 10px #ffaa00;
        }
        
        .metric-value.critical {
            color: #ff4444;
            text-shadow: 0 0 10px #ff4444;
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        /* 设备状态 */
        .equipment-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        
        .equipment-item {
            background: rgba(0, 0, 0, 0.4);
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #00d4ff;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin: 0 auto 8px;
            animation: statusBlink 2s infinite;
        }
        
        @keyframes statusBlink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.6; }
        }
        
        .status-normal { background: #00ff00; }
        .status-warning { background: #ffaa00; }
        .status-critical { background: #ff4444; }
        
        /* 告警列表 */
        .alert-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .alert-item {
            background: linear-gradient(90deg, rgba(255, 68, 68, 0.2), rgba(255, 170, 0, 0.1));
            border-left: 4px solid #ff4444;
            padding: 10px;
            margin: 8px 0;
            border-radius: 8px;
            animation: alertSlide 0.5s ease-out;
        }
        
        @keyframes alertSlide {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .alert-name {
            font-weight: bold;
            color: #ff4444;
            margin-bottom: 5px;
        }
        
        .alert-details {
            font-size: 0.9rem;
            color: #cccccc;
        }
        
        /* 趋势图容器 */
        .trend-container {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            padding: 10px;
            height: 200px;
            position: relative;
        }
        
        .trend-chart {
            width: 100%;
            height: 100%;
        }
        
        /* 响应式设计 */
        @media (max-width: 1200px) {
            .dashboard {
                grid-template-columns: 1fr 1fr;
                grid-template-rows: 80px repeat(4, 1fr);
            }
        }
        
        /* 滚动条样式 */
        ::-webkit-scrollbar {
            width: 6px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.3);
        }
        
        ::-webkit-scrollbar-thumb {
            background: #00d4ff;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="grid-bg"></div>
    
    <div class="dashboard">
        <!-- 标题栏 -->
        <div class="header">
            <h1>🏭 RTO/RCO监控大屏</h1>
            <div class="time-display" id="timeDisplay"></div>
        </div>
        
        <!-- 核心参数 -->
        <div class="panel">
            <div class="panel-title">🔥 核心参数</div>
            <div class="metric">
                <span class="metric-label">燃烧室温度</span>
                <span class="metric-value" id="tempCombustion">780.0</span>
                <span>℃</span>
            </div>
            <div class="metric">
                <span class="metric-label">处理效率</span>
                <span class="metric-value" id="efficiency">95.0</span>
                <span>%</span>
            </div>
            <div class="metric">
                <span class="metric-label">进口浓度</span>
                <span class="metric-value" id="concentrationIn">200.0</span>
                <span>mg/m³</span>
            </div>
        </div>
        
        <!-- 温度监控 -->
        <div class="panel">
            <div class="panel-title">🌡️ 温度监控</div>
            <div class="metric">
                <span class="metric-label">出口温度</span>
                <span class="metric-value" id="tempOutlet">45.0</span>
                <span>℃</span>
            </div>
            <div class="metric">
                <span class="metric-label">吸附温度</span>
                <span class="metric-value" id="tempAdsorption">35.0</span>
                <span>℃</span>
            </div>
            <div class="metric">
                <span class="metric-label">脱附温度</span>
                <span class="metric-value" id="tempDesorption">105.0</span>
                <span>℃</span>
            </div>
            <div class="metric">
                <span class="metric-label">反应器温度</span>
                <span class="metric-value" id="tempReactor">550.0</span>
                <span>℃</span>
            </div>
        </div>
        
        <!-- 浓度分析 -->
        <div class="panel">
            <div class="panel-title">🧪 浓度分析</div>
            <div class="metric">
                <span class="metric-label">出口浓度</span>
                <span class="metric-value" id="concentrationOut">20.0</span>
                <span>mg/m³</span>
            </div>
            <div class="metric">
                <span class="metric-label">系统压力</span>
                <span class="metric-value" id="pressure">1.2</span>
                <span>MPa</span>
            </div>
            <div class="metric">
                <span class="metric-label">流量</span>
                <span class="metric-value" id="flowRate">1000.0</span>
                <span>m³/h</span>
            </div>
            <div class="metric">
                <span class="metric-label">应急阀门</span>
                <span class="metric-value" id="emergencyValve">关闭</span>
                <span></span>
            </div>
        </div>
        
        <!-- 设备状态 -->
        <div class="panel">
            <div class="panel-title">🛠️ 设备状态</div>
            <div class="equipment-grid" id="equipmentStatus">
                <!-- 动态生成设备状态 -->
            </div>
        </div>
        
        <!-- 实时告警 -->
        <div class="panel">
            <div class="panel-title">🚨 实时告警</div>
            <div class="alert-list" id="alertList">
                <div style="text-align: center; color: #00ff41; padding: 20px;">
                    系统运行正常
                </div>
            </div>
        </div>
        
        <!-- 趋势图 -->
        <div class="panel">
            <div class="panel-title">📊 数据趋势</div>
            <div class="trend-container">
                <canvas id="trendChart" class="trend-chart"></canvas>
            </div>
        </div>
        
        <!-- 系统信息 -->
        <div class="panel">
            <div class="panel-title">ℹ️ 系统信息</div>
            <div class="metric">
                <span class="metric-label">运行时间</span>
                <span class="metric-value">24小时</span>
            </div>
            <div class="metric">
                <span class="metric-label">数据质量</span>
                <span class="metric-value">99.8%</span>
            </div>
            <div class="metric">
                <span class="metric-label">告警总数</span>
                <span class="metric-value" id="alertCount">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">最后更新</span>
                <span class="metric-value" id="lastUpdate">--:--:--</span>
            </div>
        </div>
    </div>
    
    <script>
        // 全局变量
        let trendData = [];
        let alertCount = 0;
        
        // 更新时间显示
        function updateTime() {
            const now = new Date();
            document.getElementById('timeDisplay').textContent = now.toLocaleString('zh-CN');
        }
        
        // 获取实时数据
        async function fetchData() {
            try {
                const response = await fetch('/api/data');
                const result = await response.json();
                updateDashboard(result);
            } catch (error) {
                console.error('获取数据失败:', error);
            }
        }
        
        // 更新监控大屏
        function updateDashboard(result) {
            const data = result.data;
            const alerts = result.alerts;
            const equipmentStatus = result.equipment_status;
            const recentAlerts = result.recent_alerts;
            
            // 更新核心参数
            updateMetric('tempCombustion', data.temperature_combustion, 760, 'less');
            updateMetric('efficiency', data.efficiency, 90, 'less');
            updateMetric('concentrationIn', data.concentration_in);
            
            // 更新温度监控
            updateMetric('tempOutlet', data.temperature_outlet, 60, 'greater');
            updateMetric('tempAdsorption', data.temperature_adsorption, 40, 'greater');
            updateMetric('tempDesorption', data.temperature_desorption);
            updateMetric('tempReactor', data.temperature_reactor, 600, 'greater');
            
            // 更新浓度分析
            updateMetric('concentrationOut', data.concentration_out, 50, 'greater');
            updateMetric('pressure', data.pressure);
            updateMetric('flowRate', data.flow_rate);
            document.getElementById('emergencyValve').textContent = data.emergency_valve ? '开启' : '关闭';
            document.getElementById('emergencyValve').className = data.emergency_valve ? 'metric-value critical' : 'metric-value';
            
            // 更新设备状态
            updateEquipmentStatus(equipmentStatus);
            
            // 更新告警
            updateAlerts(alerts, recentAlerts);
            
            // 更新趋势图
            updateTrendChart(data);
            
            // 更新系统信息
            document.getElementById('alertCount').textContent = alertCount;
            document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
        }
        
        // 更新单个指标
        function updateMetric(elementId, value, threshold = null, condition = null) {
            const element = document.getElementById(elementId);
            if (!element || value === undefined) return;
            
            element.textContent = value.toFixed(1);
            element.className = 'metric-value';
            
            // 检查是否超出阈值
            if (threshold !== null && condition) {
                let isAlert = false;
                if (condition === 'greater' && value > threshold) isAlert = true;
                if (condition === 'less' && value < threshold) isAlert = true;
                
                if (isAlert) {
                    element.className += ' critical';
                }
            }
        }
        
        // 更新设备状态
        function updateEquipmentStatus(status) {
            const container = document.getElementById('equipmentStatus');
            container.innerHTML = '';
            
            Object.entries(status).forEach(([name, state]) => {
                const item = document.createElement('div');
                item.className = 'equipment-item';
                item.innerHTML = `
                    <div class="status-dot status-${state}"></div>
                    <div>${name}</div>
                `;
                container.appendChild(item);
            });
        }
        
        // 更新告警信息
        function updateAlerts(currentAlerts, recentAlerts) {
            const alertList = document.getElementById('alertList');
            
            // 更新告警计数
            alertCount += currentAlerts.length;
            
            if (recentAlerts.length === 0) {
                alertList.innerHTML = '<div style="text-align: center; color: #00ff41; padding: 20px;">系统运行正常</div>';
                return;
            }
            
            alertList.innerHTML = '';
            recentAlerts.forEach(alert => {
                const alertItem = document.createElement('div');
                alertItem.className = 'alert-item';
                alertItem.innerHTML = `
                    <div class="alert-name">${alert.name}</div>
                    <div class="alert-details">
                        严重程度: ${alert.severity} | 时间: ${alert.time}
                    </div>
                `;
                alertList.appendChild(alertItem);
            });
        }
        
        // 更新趋势图
        function updateTrendChart(data) {
            const canvas = document.getElementById('trendChart');
            const ctx = canvas.getContext('2d');
            
            // 设置canvas尺寸
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
            
            // 添加数据点
            trendData.push({
                time: new Date().getTime(),
                temp: data.temperature_combustion,
                concentration: data.concentration_out
            });
            
            // 保持最近20个数据点
            if (trendData.length > 20) {
                trendData.shift();
            }
            
            // 绘制图表
            drawTrendChart(ctx, canvas);
        }
        
        // 绘制趋势图
        function drawTrendChart(ctx, canvas) {
            const width = canvas.width;
            const height = canvas.height;
            const padding = 40;
            
            // 清空画布
            ctx.clearRect(0, 0, width, height);
            
            if (trendData.length < 2) return;
            
            // 计算数据范围
            const temps = trendData.map(d => d.temp);
            const minTemp = Math.min(...temps);
            const maxTemp = Math.max(...temps);
            const tempRange = maxTemp - minTemp || 1;
            
            // 绘制网格
            ctx.strokeStyle = 'rgba(0, 212, 255, 0.2)';
            ctx.lineWidth = 1;
            
            // 垂直网格线
            for (let i = 0; i <= 10; i++) {
                const x = padding + (width - 2 * padding) * i / 10;
                ctx.beginPath();
                ctx.moveTo(x, padding);
                ctx.lineTo(x, height - padding);
                ctx.stroke();
            }
            
            // 水平网格线
            for (let i = 0; i <= 5; i++) {
                const y = padding + (height - 2 * padding) * i / 5;
                ctx.beginPath();
                ctx.moveTo(padding, y);
                ctx.lineTo(width - padding, y);
                ctx.stroke();
            }
            
            // 绘制温度曲线
            ctx.strokeStyle = '#00ffff';
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            trendData.forEach((point, index) => {
                const x = padding + (width - 2 * padding) * index / (trendData.length - 1);
                const y = height - padding - (height - 2 * padding) * (point.temp - minTemp) / tempRange;
                
                if (index === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });
            
            ctx.stroke();
            
            // 绘制数据点
            ctx.fillStyle = '#00ffff';
            trendData.forEach((point, index) => {
                const x = padding + (width - 2 * padding) * index / (trendData.length - 1);
                const y = height - padding - (height - 2 * padding) * (point.temp - minTemp) / tempRange;
                
                ctx.beginPath();
                ctx.arc(x, y, 3, 0, 2 * Math.PI);
                ctx.fill();
            });
            
            // 绘制标签
            ctx.fillStyle = '#ffffff';
            ctx.font = '12px Arial';
            ctx.fillText('燃烧室温度趋势', padding, 20);
            ctx.fillText(`${minTemp.toFixed(1)}℃`, 5, height - padding);
            ctx.fillText(`${maxTemp.toFixed(1)}℃`, 5, padding);
        }
        
        // 初始化
        updateTime();
        setInterval(updateTime, 1000);
        
        fetchData();
        setInterval(fetchData, 2000); // 每2秒更新一次数据
        
        // 初始化趋势图canvas尺寸
        window.addEventListener('resize', () => {
            const canvas = document.getElementById('trendChart');
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
        });
    </script>
</body>
</html>'''
        
        return RequestHandler
    
    def stop(self):
        """停止服务器"""
        self.is_running = False


class RTOWarningSystem:
    """
    RTO/RCO预警系统主类
    
    这是系统的入口点，整合了所有功能模块
    """
    
    def __init__(self):
        self.dashboard = WebDashboard()
    
    def start_monitoring(self):
        """启动实时监控"""
        print("🏭 RTO/RCO废气处理设备预警系统")
        print("=" * 50)
        print("✨ 功能特点:")
        print("  • 实时数据监控")
        print("  • 智能预警检测") 
        print("  • 现代化监控大屏")
        print("  • 设备状态跟踪")
        print("  • 历史趋势分析")
        print()
        
        # 启动Web监控大屏
        self.dashboard.start()


def main():
    """主程序入口"""
    system = RTOWarningSystem()
    system.start_monitoring()


if __name__ == "__main__":
    main()
