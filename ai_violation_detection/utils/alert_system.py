#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能报警系统
提供多级别报警、通知和记录功能
"""

import json
import sqlite3
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import logging
import threading
import time

class AlertSystem:
    """智能报警系统"""
    
    def __init__(self, db_path: str = "alerts.db", config_path: str = None):
        """
        初始化报警系统
        
        Args:
            db_path: 数据库文件路径
            config_path: 配置文件路径
        """
        self.db_path = db_path
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        
        # 初始化数据库
        self._init_database()
        
        # 报警级别配置
        self.alert_levels = {
            'critical': {'priority': 4, 'color': '#8B0000', 'sound': True},
            'high': {'priority': 3, 'color': '#FF0000', 'sound': True},
            'medium': {'priority': 2, 'color': '#FFA500', 'sound': False},
            'low': {'priority': 1, 'color': '#FFFF00', 'sound': False}
        }
        
        # 报警抑制配置（防止重复报警）
        self.suppression_window = 300  # 5分钟内相同类型报警抑制
        self.recent_alerts = {}
        
        # 启动后台清理线程
        self._start_cleanup_thread()
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        default_config = {
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'recipients': []
            },
            'webhook': {
                'enabled': False,
                'url': '',
                'headers': {}
            },
            'database': {
                'retention_days': 30
            }
        }
        
        if config_path:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"配置文件加载失败，使用默认配置: {e}")
        
        return default_config
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('AlertSystem')
        logger.setLevel(logging.INFO)
        
        # 创建文件处理器
        handler = logging.FileHandler('alerts.log', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建报警记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE,
                violation_type TEXT,
                alert_level TEXT,
                confidence REAL,
                location_x INTEGER,
                location_y INTEGER,
                timestamp TEXT,
                message TEXT,
                recommended_action TEXT,
                image_path TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                violation_type TEXT,
                alert_level TEXT,
                count INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_alert(self, detection: Dict, image_path: str = None) -> Dict:
        """
        创建报警
        
        Args:
            detection: 检测结果
            image_path: 相关图像路径
            
        Returns:
            报警信息
        """
        alert_id = f"alert_{detection.get('id', 0)}_{int(time.time())}"
        violation_type = detection.get('class_name', 'unknown')
        alert_level = detection.get('alert_level', 'low')
        confidence = detection.get('confidence', 0.0)
        location = detection.get('center', {'x': 0, 'y': 0})
        timestamp = detection.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # 检查是否需要抑制报警
        if self._should_suppress_alert(violation_type, alert_level):
            self.logger.info(f"报警被抑制: {violation_type} - {alert_level}")
            return None
        
        # 生成报警消息
        message = self._generate_alert_message(detection)
        recommended_action = self._get_recommended_action(violation_type)
        
        # 创建报警记录
        alert = {
            'alert_id': alert_id,
            'violation_type': violation_type,
            'alert_level': alert_level,
            'confidence': confidence,
            'location': location,
            'timestamp': timestamp,
            'message': message,
            'recommended_action': recommended_action,
            'image_path': image_path,
            'status': 'active'
        }
        
        # 保存到数据库
        self._save_alert_to_db(alert)
        
        # 发送通知
        self._send_notifications(alert)
        
        # 更新统计
        self._update_statistics(violation_type, alert_level)
        
        # 记录到抑制列表
        self._record_alert_for_suppression(violation_type, alert_level)
        
        self.logger.info(f"创建报警: {alert_id} - {violation_type} - {alert_level}")
        
        return alert
    
    def _should_suppress_alert(self, violation_type: str, alert_level: str) -> bool:
        """检查是否应该抑制报警"""
        key = f"{violation_type}_{alert_level}"
        current_time = time.time()
        
        if key in self.recent_alerts:
            last_alert_time = self.recent_alerts[key]
            if current_time - last_alert_time < self.suppression_window:
                return True
        
        return False
    
    def _record_alert_for_suppression(self, violation_type: str, alert_level: str):
        """记录报警用于抑制检查"""
        key = f"{violation_type}_{alert_level}"
        self.recent_alerts[key] = time.time()
    
    def _generate_alert_message(self, detection: Dict) -> str:
        """生成报警消息"""
        class_name = detection.get('class_name', 'unknown')
        confidence = detection.get('confidence', 0.0)
        timestamp = detection.get('timestamp', '')
        
        messages = {
            'dust_emission': f"🚨 检测到工地扬尘！置信度: {confidence:.1%}",
            'uncovered_soil': f"⚠️ 发现裸土未覆盖！置信度: {confidence:.1%}",
            'no_dust_suppression': f"🚨 土方作业未降尘！置信度: {confidence:.1%}",
            'night_construction': f"🌙 夜间违规施工！置信度: {confidence:.1%}",
            'outdoor_barbecue': f"🔥 露天烧烤行为！置信度: {confidence:.1%}",
            'garbage_burning': f"🔥 垃圾焚烧检测！置信度: {confidence:.1%}",
            'uncovered_truck': f"🚛 渣土车未覆盖！置信度: {confidence:.1%}"
        }
        
        base_message = messages.get(class_name, f"⚠️ 检测到违规行为: {class_name}，置信度: {confidence:.1%}")
        return f"{base_message}\n检测时间: {timestamp}"
    
    def _get_recommended_action(self, violation_type: str) -> str:
        """获取建议处理措施"""
        actions = {
            'dust_emission': "立即启动喷淋系统，停止产尘作业，检查防尘措施",
            'uncovered_soil': "使用防尘网或绿化覆盖裸土，定期洒水降尘",
            'no_dust_suppression': "启动洒水降尘设备，调整作业方式",
            'night_construction': "核实施工许可证，如无许可立即停工",
            'outdoor_barbecue': "劝阻并清理烧烤设备，加强巡查",
            'garbage_burning': "立即扑灭火源，清理现场，调查责任人",
            'uncovered_truck': "要求车辆加盖篷布，清洗车轮后通行"
        }
        
        return actions.get(violation_type, "请及时处理违规行为，加强现场管理")
    
    def _save_alert_to_db(self, alert: Dict):
        """保存报警到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (
                alert_id, violation_type, alert_level, confidence,
                location_x, location_y, timestamp, message,
                recommended_action, image_path, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            alert['alert_id'],
            alert['violation_type'],
            alert['alert_level'],
            alert['confidence'],
            alert['location']['x'],
            alert['location']['y'],
            alert['timestamp'],
            alert['message'],
            alert['recommended_action'],
            alert['image_path'],
            alert['status']
        ))
        
        conn.commit()
        conn.close()
    
    def _send_notifications(self, alert: Dict):
        """发送通知"""
        # 邮件通知
        if self.config['email']['enabled']:
            self._send_email_notification(alert)
        
        # Webhook通知
        if self.config['webhook']['enabled']:
            self._send_webhook_notification(alert)
    
    def _send_email_notification(self, alert: Dict):
        """发送邮件通知"""
        try:
            smtp_server = self.config['email']['smtp_server']
            smtp_port = self.config['email']['smtp_port']
            username = self.config['email']['username']
            password = self.config['email']['password']
            recipients = self.config['email']['recipients']
            
            if not recipients:
                return
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"AI违规检测报警 - {alert['violation_type']}"
            
            # 邮件正文
            body = f"""
            报警详情：
            
            违规类型: {alert['violation_type']}
            报警级别: {alert['alert_level']}
            置信度: {alert['confidence']:.1%}
            检测时间: {alert['timestamp']}
            位置: ({alert['location']['x']}, {alert['location']['y']})
            
            报警消息:
            {alert['message']}
            
            建议措施:
            {alert['recommended_action']}
            
            ---
            AI违规检测系统自动发送
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 发送邮件
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"邮件通知已发送: {alert['alert_id']}")
            
        except Exception as e:
            self.logger.error(f"邮件发送失败: {e}")
    
    def _send_webhook_notification(self, alert: Dict):
        """发送Webhook通知"""
        try:
            import requests
            
            url = self.config['webhook']['url']
            headers = self.config['webhook']['headers']
            
            payload = {
                'alert_id': alert['alert_id'],
                'violation_type': alert['violation_type'],
                'alert_level': alert['alert_level'],
                'confidence': alert['confidence'],
                'timestamp': alert['timestamp'],
                'message': alert['message'],
                'location': alert['location']
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Webhook通知已发送: {alert['alert_id']}")
            
        except Exception as e:
            self.logger.error(f"Webhook发送失败: {e}")
    
    def _update_statistics(self, violation_type: str, alert_level: str):
        """更新统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 检查今日统计是否存在
        cursor.execute('''
            SELECT count FROM alert_statistics 
            WHERE date = ? AND violation_type = ? AND alert_level = ?
        ''', (today, violation_type, alert_level))
        
        result = cursor.fetchone()
        
        if result:
            # 更新计数
            cursor.execute('''
                UPDATE alert_statistics 
                SET count = count + 1 
                WHERE date = ? AND violation_type = ? AND alert_level = ?
            ''', (today, violation_type, alert_level))
        else:
            # 插入新记录
            cursor.execute('''
                INSERT INTO alert_statistics (date, violation_type, alert_level, count)
                VALUES (?, ?, ?, 1)
            ''', (today, violation_type, alert_level))
        
        conn.commit()
        conn.close()
    
    def get_alerts(self, limit: int = 100, status: str = None) -> List[Dict]:
        """获取报警记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM alerts"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 转换为字典列表
        columns = [description[0] for description in cursor.description]
        alerts = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return alerts
    
    def get_statistics(self, days: int = 7) -> Dict:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 获取统计数据
        cursor.execute('''
            SELECT violation_type, alert_level, SUM(count) as total
            FROM alert_statistics 
            WHERE date >= ? AND date <= ?
            GROUP BY violation_type, alert_level
            ORDER BY total DESC
        ''', (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        
        stats = cursor.fetchall()
        
        # 获取每日统计
        cursor.execute('''
            SELECT date, SUM(count) as daily_total
            FROM alert_statistics 
            WHERE date >= ? AND date <= ?
            GROUP BY date
            ORDER BY date
        ''', (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        
        daily_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'violation_stats': [{'type': row[0], 'level': row[1], 'count': row[2]} for row in stats],
            'daily_stats': [{'date': row[0], 'count': row[1]} for row in daily_stats]
        }
    
    def _start_cleanup_thread(self):
        """启动后台清理线程"""
        def cleanup_worker():
            while True:
                try:
                    # 清理过期的抑制记录
                    current_time = time.time()
                    expired_keys = [
                        key for key, timestamp in self.recent_alerts.items()
                        if current_time - timestamp > self.suppression_window
                    ]
                    for key in expired_keys:
                        del self.recent_alerts[key]
                    
                    # 清理过期的数据库记录
                    retention_days = self.config['database']['retention_days']
                    cutoff_date = (datetime.now() - timedelta(days=retention_days)).strftime("%Y-%m-%d")
                    
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM alerts WHERE created_at < ?", (cutoff_date,))
                    cursor.execute("DELETE FROM alert_statistics WHERE date < ?", (cutoff_date,))
                    conn.commit()
                    conn.close()
                    
                except Exception as e:
                    self.logger.error(f"清理任务失败: {e}")
                
                # 每小时执行一次清理
                time.sleep(3600)
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def update_alert_status(self, alert_id: str, status: str) -> bool:
        """更新报警状态"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE alerts 
                SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE alert_id = ?
            ''', (status, alert_id))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"报警状态已更新: {alert_id} -> {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新报警状态失败: {e}")
            return False
