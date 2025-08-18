#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统配置文件
包含模型配置、检测参数、报警设置等
"""

import os

# 基础配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
WEIGHTS_DIR = os.path.join(MODELS_DIR, 'weights')

# 模型配置
MODEL_CONFIG = {
    'yolo': {
        'model_path': os.path.join(WEIGHTS_DIR, 'violation_detection.pt'),
        'confidence_threshold': 0.5,
        'iou_threshold': 0.45,
        'device': 'auto',  # 'cpu', 'cuda', 'auto'
        'input_size': (640, 640)
    },
    'dust_detector': {
        'model_path': os.path.join(WEIGHTS_DIR, 'dust_classification.pt'),
        'confidence_threshold': 0.6,
        'area_threshold': 1000,
        'input_size': (224, 224)
    }
}

# 违规行为类别配置
VIOLATION_CLASSES = {
    0: {
        'name': 'dust_emission',
        'chinese_name': '工地扬尘',
        'category': 'construction',
        'alert_level': 'high',
        'description': '工地产生的粉尘污染',
        'icon': 'fas fa-smog'
    },
    1: {
        'name': 'uncovered_soil',
        'chinese_name': '裸土未覆盖',
        'category': 'construction',
        'alert_level': 'medium',
        'description': '裸露土地未进行覆盖防尘',
        'icon': 'fas fa-mountain'
    },
    2: {
        'name': 'no_dust_suppression',
        'chinese_name': '土方作业未降尘',
        'category': 'construction',
        'alert_level': 'high',
        'description': '土方作业过程中未采取降尘措施',
        'icon': 'fas fa-tint'
    },
    3: {
        'name': 'night_construction',
        'chinese_name': '夜间违规施工',
        'category': 'construction',
        'alert_level': 'medium',
        'description': '在禁止时间段进行施工作业',
        'icon': 'fas fa-moon'
    },
    4: {
        'name': 'outdoor_barbecue',
        'chinese_name': '露天烧烤',
        'category': 'pollution',
        'alert_level': 'medium',
        'description': '在禁止区域进行露天烧烤',
        'icon': 'fas fa-fire'
    },
    5: {
        'name': 'garbage_burning',
        'chinese_name': '垃圾焚烧',
        'category': 'pollution',
        'alert_level': 'critical',
        'description': '非法焚烧垃圾造成空气污染',
        'icon': 'fas fa-fire-alt'
    },
    6: {
        'name': 'uncovered_truck',
        'chinese_name': '渣土车未覆盖',
        'category': 'pollution',
        'alert_level': 'high',
        'description': '运输车辆未加盖篷布',
        'icon': 'fas fa-truck'
    },
    7: {
        'name': 'no_helmet',
        'chinese_name': '未戴安全帽',
        'category': 'safety',
        'alert_level': 'medium',
        'description': '施工人员未佩戴安全帽',
        'icon': 'fas fa-hard-hat'
    },
    8: {
        'name': 'unsafe_operation',
        'chinese_name': '不安全操作',
        'category': 'safety',
        'alert_level': 'high',
        'description': '违反安全操作规程的行为',
        'icon': 'fas fa-exclamation-triangle'
    },
    9: {
        'name': 'restricted_area',
        'chinese_name': '禁入区域',
        'category': 'safety',
        'alert_level': 'medium',
        'description': '进入禁止区域',
        'icon': 'fas fa-ban'
    }
}

# 报警级别配置
ALERT_LEVELS = {
    'critical': {
        'priority': 4,
        'color': '#8B0000',
        'bg_color': 'rgba(231, 76, 60, 0.2)',
        'sound': True,
        'auto_notify': True,
        'description': '严重违规，需要立即处理'
    },
    'high': {
        'priority': 3,
        'color': '#FF0000',
        'bg_color': 'rgba(231, 76, 60, 0.1)',
        'sound': True,
        'auto_notify': True,
        'description': '高风险违规，需要尽快处理'
    },
    'medium': {
        'priority': 2,
        'color': '#FFA500',
        'bg_color': 'rgba(243, 156, 18, 0.1)',
        'sound': False,
        'auto_notify': False,
        'description': '中等风险违规，需要关注'
    },
    'low': {
        'priority': 1,
        'color': '#FFFF00',
        'bg_color': 'rgba(255, 235, 59, 0.2)',
        'sound': False,
        'auto_notify': False,
        'description': '低风险违规，建议处理'
    }
}

# 图像处理配置
IMAGE_CONFIG = {
    'max_upload_size': 16 * 1024 * 1024,  # 16MB
    'allowed_extensions': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'],
    'resize_max_size': 1024,
    'quality': 95,
    'watermark_text': 'AI Detection System',
    'enhancement': {
        'brightness': 1.1,
        'contrast': 1.1,
        'sharpness': 1.05
    }
}

# Web应用配置
WEB_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True,
    'secret_key': 'your-secret-key-change-in-production',
    'upload_folder': 'static/uploads',
    'result_folder': 'static/results',
    'max_content_length': 16 * 1024 * 1024
}

# 数据库配置
DATABASE_CONFIG = {
    'path': os.path.join(DATA_DIR, 'alerts.db'),
    'retention_days': 30,
    'backup_enabled': True,
    'backup_interval': 24  # 小时
}

# 通知配置
NOTIFICATION_CONFIG = {
    'email': {
        'enabled': False,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': '',
        'password': '',
        'recipients': [],
        'subject_prefix': '[AI违规检测]'
    },
    'webhook': {
        'enabled': False,
        'url': '',
        'headers': {
            'Content-Type': 'application/json'
        },
        'timeout': 10
    },
    'sms': {
        'enabled': False,
        'api_key': '',
        'api_secret': '',
        'phone_numbers': []
    }
}

# 性能配置
PERFORMANCE_CONFIG = {
    'batch_size': 1,
    'num_workers': 4,
    'cache_enabled': True,
    'cache_size': 100,
    'gpu_memory_fraction': 0.8,
    'realtime_detection_interval': 3  # 秒
}

# 日志配置
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_path': os.path.join(DATA_DIR, 'system.log'),
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# 安全配置
SECURITY_CONFIG = {
    'rate_limiting': {
        'enabled': True,
        'requests_per_minute': 60,
        'requests_per_hour': 1000
    },
    'file_validation': {
        'check_file_header': True,
        'scan_for_malware': False,
        'max_file_size': 16 * 1024 * 1024
    },
    'api_key_required': False,
    'cors_enabled': True
}

# 监控配置
MONITORING_CONFIG = {
    'metrics_enabled': True,
    'health_check_interval': 60,  # 秒
    'performance_tracking': True,
    'error_reporting': True,
    'statistics_retention': 90  # 天
}

# 部署配置
DEPLOYMENT_CONFIG = {
    'environment': 'development',  # development, staging, production
    'auto_reload': True,
    'workers': 1,
    'worker_class': 'sync',
    'timeout': 30,
    'keepalive': 2
}

# 获取配置的辅助函数
def get_config(section: str = None):
    """获取配置信息"""
    if section is None:
        return {
            'model': MODEL_CONFIG,
            'violation_classes': VIOLATION_CLASSES,
            'alert_levels': ALERT_LEVELS,
            'image': IMAGE_CONFIG,
            'web': WEB_CONFIG,
            'database': DATABASE_CONFIG,
            'notification': NOTIFICATION_CONFIG,
            'performance': PERFORMANCE_CONFIG,
            'logging': LOGGING_CONFIG,
            'security': SECURITY_CONFIG,
            'monitoring': MONITORING_CONFIG,
            'deployment': DEPLOYMENT_CONFIG
        }
    
    config_map = {
        'model': MODEL_CONFIG,
        'violation_classes': VIOLATION_CLASSES,
        'alert_levels': ALERT_LEVELS,
        'image': IMAGE_CONFIG,
        'web': WEB_CONFIG,
        'database': DATABASE_CONFIG,
        'notification': NOTIFICATION_CONFIG,
        'performance': PERFORMANCE_CONFIG,
        'logging': LOGGING_CONFIG,
        'security': SECURITY_CONFIG,
        'monitoring': MONITORING_CONFIG,
        'deployment': DEPLOYMENT_CONFIG
    }
    
    return config_map.get(section, {})

def get_violation_info(class_id: int):
    """根据类别ID获取违规信息"""
    return VIOLATION_CLASSES.get(class_id, {
        'name': 'unknown',
        'chinese_name': '未知违规',
        'category': 'other',
        'alert_level': 'low',
        'description': '未知的违规行为',
        'icon': 'fas fa-question'
    })

def get_alert_level_info(level: str):
    """根据报警级别获取详细信息"""
    return ALERT_LEVELS.get(level, ALERT_LEVELS['low'])

# 环境变量覆盖配置
def load_env_config():
    """从环境变量加载配置覆盖"""
    import os
    
    # 数据库路径
    if os.getenv('DATABASE_PATH'):
        DATABASE_CONFIG['path'] = os.getenv('DATABASE_PATH')
    
    # Web配置
    if os.getenv('WEB_HOST'):
        WEB_CONFIG['host'] = os.getenv('WEB_HOST')
    if os.getenv('WEB_PORT'):
        WEB_CONFIG['port'] = int(os.getenv('WEB_PORT'))
    if os.getenv('SECRET_KEY'):
        WEB_CONFIG['secret_key'] = os.getenv('SECRET_KEY')
    
    # 邮件配置
    if os.getenv('EMAIL_ENABLED'):
        NOTIFICATION_CONFIG['email']['enabled'] = os.getenv('EMAIL_ENABLED').lower() == 'true'
    if os.getenv('SMTP_SERVER'):
        NOTIFICATION_CONFIG['email']['smtp_server'] = os.getenv('SMTP_SERVER')
    if os.getenv('SMTP_USERNAME'):
        NOTIFICATION_CONFIG['email']['username'] = os.getenv('SMTP_USERNAME')
    if os.getenv('SMTP_PASSWORD'):
        NOTIFICATION_CONFIG['email']['password'] = os.getenv('SMTP_PASSWORD')

# 初始化时加载环境配置
load_env_config()
