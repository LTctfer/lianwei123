#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扬尘检测专用模型
基于图像处理和深度学习的扬尘识别算法
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image

class DustDetector:
    """扬尘检测器"""
    
    def __init__(self, model_path: str = None):
        """
        初始化扬尘检测器
        
        Args:
            model_path: 预训练模型路径
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self._load_model(model_path)
        self.transform = self._get_transform()
        
        # 扬尘检测参数
        self.dust_threshold = 0.6
        self.area_threshold = 1000  # 最小检测区域
        
    def _load_model(self, model_path: str) -> nn.Module:
        """加载扬尘检测模型"""
        if model_path is None:
            # 使用简单的CNN模型作为示例
            model = DustClassificationModel()
        else:
            model = torch.load(model_path, map_location=self.device)
        
        model.to(self.device)
        model.eval()
        return model
    
    def _get_transform(self):
        """获取图像预处理变换"""
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def detect_dust(self, image: np.ndarray) -> Dict:
        """
        检测图像中的扬尘
        
        Args:
            image: 输入图像 (BGR格式)
            
        Returns:
            扬尘检测结果
        """
        # 1. 传统图像处理方法检测扬尘区域
        dust_regions = self._detect_dust_regions(image)
        
        # 2. 深度学习模型验证扬尘
        dust_classifications = []
        for region in dust_regions:
            classification = self._classify_dust_region(image, region)
            dust_classifications.append(classification)
        
        # 3. 综合分析结果
        result = self._analyze_dust_results(dust_regions, dust_classifications)
        
        return result
    
    def _detect_dust_regions(self, image: np.ndarray) -> List[Dict]:
        """使用传统图像处理方法检测可能的扬尘区域"""
        # 转换为HSV色彩空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 扬尘通常呈现灰白色，饱和度较低
        # 定义扬尘的HSV范围
        lower_dust = np.array([0, 0, 100])    # 低饱和度，中等亮度
        upper_dust = np.array([180, 50, 255]) # 全色相，低饱和度，高亮度
        
        # 创建扬尘掩码
        dust_mask = cv2.inRange(hsv, lower_dust, upper_dust)
        
        # 形态学操作去除噪声
        kernel = np.ones((5, 5), np.uint8)
        dust_mask = cv2.morphologyEx(dust_mask, cv2.MORPH_OPEN, kernel)
        dust_mask = cv2.morphologyEx(dust_mask, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(dust_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        dust_regions = []
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area > self.area_threshold:
                # 获取边界框
                x, y, w, h = cv2.boundingRect(contour)
                
                # 计算区域特征
                region_features = self._calculate_region_features(image, contour, (x, y, w, h))
                
                dust_region = {
                    'id': i,
                    'bbox': {'x': x, 'y': y, 'width': w, 'height': h},
                    'area': area,
                    'contour': contour,
                    'features': region_features
                }
                dust_regions.append(dust_region)
        
        return dust_regions
    
    def _calculate_region_features(self, image: np.ndarray, contour, bbox: Tuple) -> Dict:
        """计算区域特征"""
        x, y, w, h = bbox
        roi = image[y:y+h, x:x+w]
        
        # 创建掩码
        mask = np.zeros((h, w), dtype=np.uint8)
        contour_shifted = contour - [x, y]
        cv2.fillPoly(mask, [contour_shifted], 255)
        
        # 计算颜色特征
        roi_masked = cv2.bitwise_and(roi, roi, mask=mask)
        mean_color = cv2.mean(roi_masked, mask=mask)[:3]
        
        # 计算纹理特征（简化版）
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray_masked = cv2.bitwise_and(gray_roi, gray_roi, mask=mask)
        
        # 计算标准差作为纹理特征
        texture_std = np.std(gray_masked[mask > 0]) if np.any(mask > 0) else 0
        
        # 计算形状特征
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * cv2.contourArea(contour) / (perimeter * perimeter) if perimeter > 0 else 0
        
        return {
            'mean_color': mean_color,
            'texture_std': texture_std,
            'circularity': circularity,
            'aspect_ratio': w / h if h > 0 else 0
        }
    
    def _classify_dust_region(self, image: np.ndarray, region: Dict) -> Dict:
        """使用深度学习模型分类区域是否为扬尘"""
        bbox = region['bbox']
        x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
        
        # 提取区域图像
        roi = image[y:y+h, x:x+w]
        
        # 预处理
        pil_image = Image.fromarray(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))
        input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
        
        # 模型推理
        with torch.no_grad():
            output = self.model(input_tensor)
            probability = torch.softmax(output, dim=1)[0]
            dust_prob = probability[1].item()  # 假设索引1为扬尘类别
        
        return {
            'is_dust': dust_prob > self.dust_threshold,
            'confidence': dust_prob,
            'classification_score': dust_prob
        }
    
    def _analyze_dust_results(self, regions: List[Dict], classifications: List[Dict]) -> Dict:
        """分析扬尘检测结果"""
        dust_detections = []
        total_dust_area = 0
        max_confidence = 0
        
        for region, classification in zip(regions, classifications):
            if classification['is_dust']:
                detection = {
                    'bbox': region['bbox'],
                    'area': region['area'],
                    'confidence': classification['confidence'],
                    'features': region['features'],
                    'alert_level': self._get_dust_alert_level(classification['confidence'], region['area'])
                }
                dust_detections.append(detection)
                total_dust_area += region['area']
                max_confidence = max(max_confidence, classification['confidence'])
        
        # 计算扬尘严重程度
        severity = self._calculate_dust_severity(dust_detections, total_dust_area)
        
        return {
            'dust_detected': len(dust_detections) > 0,
            'dust_count': len(dust_detections),
            'detections': dust_detections,
            'total_dust_area': total_dust_area,
            'max_confidence': max_confidence,
            'severity': severity,
            'alert_level': self._get_overall_alert_level(severity, max_confidence)
        }
    
    def _get_dust_alert_level(self, confidence: float, area: int) -> str:
        """根据置信度和面积确定报警级别"""
        if confidence > 0.8 and area > 5000:
            return 'critical'
        elif confidence > 0.7 and area > 3000:
            return 'high'
        elif confidence > 0.6 and area > 1000:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_dust_severity(self, detections: List[Dict], total_area: int) -> str:
        """计算扬尘严重程度"""
        if not detections:
            return 'none'
        
        avg_confidence = np.mean([d['confidence'] for d in detections])
        
        if avg_confidence > 0.8 and total_area > 10000:
            return 'severe'
        elif avg_confidence > 0.7 and total_area > 5000:
            return 'moderate'
        elif avg_confidence > 0.6 and total_area > 2000:
            return 'mild'
        else:
            return 'light'
    
    def _get_overall_alert_level(self, severity: str, max_confidence: float) -> str:
        """获取整体报警级别"""
        severity_levels = {
            'severe': 'critical',
            'moderate': 'high',
            'mild': 'medium',
            'light': 'low',
            'none': 'none'
        }
        return severity_levels.get(severity, 'low')
    
    def draw_dust_detections(self, image: np.ndarray, result: Dict) -> np.ndarray:
        """在图像上绘制扬尘检测结果"""
        result_image = image.copy()
        
        if not result['dust_detected']:
            return result_image
        
        # 颜色配置
        colors = {
            'critical': (0, 0, 139),   # 深红色
            'high': (0, 0, 255),       # 红色
            'medium': (0, 165, 255),   # 橙色
            'low': (0, 255, 255)       # 黄色
        }
        
        for detection in result['detections']:
            bbox = detection['bbox']
            confidence = detection['confidence']
            alert_level = detection['alert_level']
            
            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
            color = colors.get(alert_level, (0, 255, 0))
            
            # 绘制边界框
            cv2.rectangle(result_image, (x, y), (x + w, y + h), color, 2)
            
            # 绘制标签
            label = f"Dust: {confidence:.2%}"
            cv2.putText(result_image, label, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # 添加整体信息
        info_text = f"Dust Severity: {result['severity']} | Count: {result['dust_count']}"
        cv2.putText(result_image, info_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return result_image


class DustClassificationModel(nn.Module):
    """简单的扬尘分类模型"""
    
    def __init__(self, num_classes: int = 2):
        super(DustClassificationModel, self).__init__()
        
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            
            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            
            nn.Conv2d(128, 256, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((7, 7))
        )
        
        self.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(256 * 7 * 7, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x
