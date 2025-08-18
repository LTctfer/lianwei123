#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI违规行为检测模型
基于YOLO v8的多类别违规行为识别系统
"""

import torch
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Tuple, Optional
import time
from datetime import datetime
import logging

class ViolationDetector:
    """违规行为检测器"""
    
    def __init__(self, model_path: str = None, device: str = 'auto'):
        """
        初始化违规检测器
        
        Args:
            model_path: 模型权重路径
            device: 计算设备 ('cpu', 'cuda', 'auto')
        """
        self.device = self._get_device(device)
        self.model = self._load_model(model_path)
        self.class_names = self._get_class_names()
        self.confidence_threshold = 0.5
        self.iou_threshold = 0.45
        
        # 违规行为类别映射
        self.violation_categories = {
            'construction': ['dust_emission', 'uncovered_soil', 'no_dust_suppression', 'night_construction'],
            'pollution': ['outdoor_barbecue', 'garbage_burning', 'uncovered_truck'],
            'safety': ['no_helmet', 'unsafe_operation', 'restricted_area']
        }
        
        # 报警级别配置
        self.alert_levels = {
            'dust_emission': 'high',
            'garbage_burning': 'critical',
            'night_construction': 'medium',
            'uncovered_soil': 'medium',
            'outdoor_barbecue': 'medium',
            'uncovered_truck': 'high'
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _get_device(self, device: str) -> str:
        """获取计算设备"""
        if device == 'auto':
            return 'cuda' if torch.cuda.is_available() else 'cpu'
        return device
    
    def _load_model(self, model_path: str) -> YOLO:
        """加载YOLO模型"""
        if model_path is None:
            # 强制从项目目录加载本地模型
            from pathlib import Path
            project_root = Path(__file__).parent.parent
            local_model_path = project_root / 'yolo-model' / 'yolov8n.pt'

            if local_model_path.exists():
                print(f"📦 从项目目录加载模型: {local_model_path}")
                model = YOLO(str(local_model_path))
            else:
                # 如果本地模型不存在，抛出错误而不是使用在线模型
                raise FileNotFoundError(
                    f"❌ 本地模型文件不存在: {local_model_path}\n"
                    f"请先运行以下命令下载模型:\n"
                    f"python run.py --mode web\n"
                    f"或手动下载模型到: {local_model_path}"
                )
        else:
            # 使用指定的模型路径
            from pathlib import Path
            model_file = Path(model_path)
            if not model_file.exists():
                raise FileNotFoundError(f"❌ 指定的模型文件不存在: {model_path}")

            print(f"📦 加载指定模型: {model_path}")
            model = YOLO(model_path)

        model.to(self.device)
        return model
    
    def _get_class_names(self) -> Dict[int, str]:
        """获取类别名称映射"""
        return {
            0: 'dust_emission',      # 扬尘
            1: 'uncovered_soil',     # 裸土未覆盖
            2: 'no_dust_suppression', # 土方作业未降尘
            3: 'night_construction', # 夜间违规施工
            4: 'outdoor_barbecue',   # 露天烧烤
            5: 'garbage_burning',    # 垃圾焚烧
            6: 'uncovered_truck',    # 渣土车未覆盖
            7: 'no_helmet',          # 未戴安全帽
            8: 'unsafe_operation',   # 不安全操作
            9: 'restricted_area'     # 禁入区域
        }
    
    def detect_violations(self, image: np.ndarray, timestamp: str = None) -> Dict:
        """
        检测图像中的违规行为
        
        Args:
            image: 输入图像 (BGR格式)
            timestamp: 检测时间戳
            
        Returns:
            检测结果字典
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        start_time = time.time()
        
        # YOLO推理
        results = self.model(image, conf=self.confidence_threshold, iou=self.iou_threshold)
        
        # 解析检测结果
        detections = self._parse_results(results[0], image.shape, timestamp)
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 生成报警信息
        alerts = self._generate_alerts(detections)
        
        return {
            'timestamp': timestamp,
            'processing_time': processing_time,
            'detections': detections,
            'alerts': alerts,
            'total_violations': len(detections),
            'image_shape': image.shape
        }
    
    def _parse_results(self, result, image_shape: Tuple, timestamp: str) -> List[Dict]:
        """解析YOLO检测结果"""
        detections = []
        
        if result.boxes is not None:
            boxes = result.boxes.xyxy.cpu().numpy()  # 边界框坐标
            confidences = result.boxes.conf.cpu().numpy()  # 置信度
            class_ids = result.boxes.cls.cpu().numpy().astype(int)  # 类别ID
            
            for i, (box, conf, cls_id) in enumerate(zip(boxes, confidences, class_ids)):
                if cls_id in self.class_names:
                    x1, y1, x2, y2 = box.astype(int)
                    
                    detection = {
                        'id': i,
                        'class_name': self.class_names[cls_id],
                        'class_id': int(cls_id),
                        'confidence': float(conf),
                        'bbox': {
                            'x1': int(x1), 'y1': int(y1),
                            'x2': int(x2), 'y2': int(y2),
                            'width': int(x2 - x1),
                            'height': int(y2 - y1)
                        },
                        'center': {
                            'x': int((x1 + x2) / 2),
                            'y': int((y1 + y2) / 2)
                        },
                        'area': int((x2 - x1) * (y2 - y1)),
                        'timestamp': timestamp,
                        'alert_level': self.alert_levels.get(self.class_names[cls_id], 'low')
                    }
                    
                    detections.append(detection)
        
        return detections
    
    def _generate_alerts(self, detections: List[Dict]) -> List[Dict]:
        """生成报警信息"""
        alerts = []
        
        for detection in detections:
            alert = {
                'id': f"alert_{detection['id']}_{int(time.time())}",
                'violation_type': detection['class_name'],
                'alert_level': detection['alert_level'],
                'confidence': detection['confidence'],
                'location': detection['center'],
                'timestamp': detection['timestamp'],
                'message': self._get_alert_message(detection),
                'recommended_action': self._get_recommended_action(detection['class_name'])
            }
            alerts.append(alert)
        
        return alerts
    
    def _get_alert_message(self, detection: Dict) -> str:
        """生成报警消息"""
        class_name = detection['class_name']
        confidence = detection['confidence']
        
        messages = {
            'dust_emission': f"检测到工地扬尘，置信度: {confidence:.2%}",
            'uncovered_soil': f"发现裸土未覆盖，置信度: {confidence:.2%}",
            'no_dust_suppression': f"土方作业未进行降尘处理，置信度: {confidence:.2%}",
            'night_construction': f"检测到夜间违规施工，置信度: {confidence:.2%}",
            'outdoor_barbecue': f"发现露天烧烤行为，置信度: {confidence:.2%}",
            'garbage_burning': f"检测到垃圾焚烧，置信度: {confidence:.2%}",
            'uncovered_truck': f"渣土车未覆盖，置信度: {confidence:.2%}"
        }
        
        return messages.get(class_name, f"检测到违规行为: {class_name}，置信度: {confidence:.2%}")
    
    def _get_recommended_action(self, class_name: str) -> str:
        """获取建议处理措施"""
        actions = {
            'dust_emission': "立即启动喷淋系统，停止产尘作业",
            'uncovered_soil': "使用防尘网或绿化覆盖裸土",
            'no_dust_suppression': "启动洒水降尘设备",
            'night_construction': "核实施工许可，如无许可立即停工",
            'outdoor_barbecue': "劝阻并清理烧烤设备",
            'garbage_burning': "立即扑灭火源，清理现场",
            'uncovered_truck': "要求车辆加盖篷布后通行"
        }
        
        return actions.get(class_name, "请及时处理违规行为")
    
    def draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """在图像上绘制检测结果"""
        result_image = image.copy()
        
        # 颜色配置
        colors = {
            'high': (0, 0, 255),      # 红色
            'critical': (0, 0, 139),  # 深红色
            'medium': (0, 165, 255),  # 橙色
            'low': (0, 255, 255)      # 黄色
        }
        
        for detection in detections:
            bbox = detection['bbox']
            class_name = detection['class_name']
            confidence = detection['confidence']
            alert_level = detection['alert_level']
            
            # 获取颜色
            color = colors.get(alert_level, (0, 255, 0))
            
            # 绘制边界框
            cv2.rectangle(result_image, 
                         (bbox['x1'], bbox['y1']), 
                         (bbox['x2'], bbox['y2']), 
                         color, 2)
            
            # 绘制标签
            label = f"{class_name}: {confidence:.2%}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # 标签背景
            cv2.rectangle(result_image,
                         (bbox['x1'], bbox['y1'] - label_size[1] - 10),
                         (bbox['x1'] + label_size[0], bbox['y1']),
                         color, -1)
            
            # 标签文字
            cv2.putText(result_image, label,
                       (bbox['x1'], bbox['y1'] - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return result_image
    
    def set_confidence_threshold(self, threshold: float):
        """设置置信度阈值"""
        self.confidence_threshold = max(0.0, min(1.0, threshold))
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            'model_type': 'YOLO v8',
            'device': self.device,
            'classes': len(self.class_names),
            'confidence_threshold': self.confidence_threshold,
            'iou_threshold': self.iou_threshold
        }
