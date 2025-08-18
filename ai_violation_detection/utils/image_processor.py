#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像处理工具模块
提供图像预处理、后处理和可视化功能
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from typing import Tuple, List, Dict, Optional
import base64
import io

class ImageProcessor:
    """图像处理器"""
    
    def __init__(self):
        """初始化图像处理器"""
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        加载图像文件
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            BGR格式的图像数组，失败返回None
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"无法加载图像: {image_path}")
            return image
        except Exception as e:
            print(f"图像加载失败: {e}")
            return None
    
    def load_image_from_bytes(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        从字节数据加载图像
        
        Args:
            image_bytes: 图像字节数据
            
        Returns:
            BGR格式的图像数组
        """
        try:
            # 将字节转换为numpy数组
            nparr = np.frombuffer(image_bytes, np.uint8)
            # 解码图像
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return image
        except Exception as e:
            print(f"从字节加载图像失败: {e}")
            return None
    
    def preprocess_image(self, image: np.ndarray, target_size: Tuple[int, int] = None) -> np.ndarray:
        """
        图像预处理
        
        Args:
            image: 输入图像
            target_size: 目标尺寸 (width, height)
            
        Returns:
            预处理后的图像
        """
        processed_image = image.copy()
        
        # 调整尺寸
        if target_size is not None:
            processed_image = cv2.resize(processed_image, target_size)
        
        # 图像增强
        processed_image = self.enhance_image(processed_image)
        
        return processed_image
    
    def enhance_image(self, image: np.ndarray) -> np.ndarray:
        """
        图像增强
        
        Args:
            image: 输入图像
            
        Returns:
            增强后的图像
        """
        # 转换为PIL图像进行增强
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # 亮度增强
        enhancer = ImageEnhance.Brightness(pil_image)
        pil_image = enhancer.enhance(1.1)
        
        # 对比度增强
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(1.1)
        
        # 锐度增强
        enhancer = ImageEnhance.Sharpness(pil_image)
        pil_image = enhancer.enhance(1.05)
        
        # 转换回OpenCV格式
        enhanced_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        return enhanced_image
    
    def denoise_image(self, image: np.ndarray) -> np.ndarray:
        """
        图像去噪
        
        Args:
            image: 输入图像
            
        Returns:
            去噪后的图像
        """
        # 使用非局部均值去噪
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        return denoised
    
    def adjust_lighting(self, image: np.ndarray) -> np.ndarray:
        """
        光照调整
        
        Args:
            image: 输入图像
            
        Returns:
            光照调整后的图像
        """
        # 转换为LAB色彩空间
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # 对L通道进行CLAHE（限制对比度自适应直方图均衡化）
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # 合并通道并转换回BGR
        lab = cv2.merge([l, a, b])
        adjusted = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return adjusted
    
    def create_detection_overlay(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        创建检测结果覆盖层
        
        Args:
            image: 原始图像
            detections: 检测结果列表
            
        Returns:
            带有检测结果的图像
        """
        overlay = image.copy()
        
        # 颜色配置
        colors = {
            'critical': (0, 0, 139),   # 深红色
            'high': (0, 0, 255),       # 红色
            'medium': (0, 165, 255),   # 橙色
            'low': (0, 255, 255),      # 黄色
            'default': (0, 255, 0)     # 绿色
        }
        
        for detection in detections:
            bbox = detection.get('bbox', {})
            class_name = detection.get('class_name', 'unknown')
            confidence = detection.get('confidence', 0.0)
            alert_level = detection.get('alert_level', 'low')
            
            # 获取边界框坐标
            if 'x1' in bbox:  # YOLO格式
                x1, y1, x2, y2 = bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']
            else:  # 宽高格式
                x, y, w, h = bbox.get('x', 0), bbox.get('y', 0), bbox.get('width', 0), bbox.get('height', 0)
                x1, y1, x2, y2 = x, y, x + w, y + h
            
            # 获取颜色
            color = colors.get(alert_level, colors['default'])
            
            # 绘制边界框
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 3)
            
            # 绘制填充的半透明矩形
            overlay_rect = overlay.copy()
            cv2.rectangle(overlay_rect, (x1, y1), (x2, y2), color, -1)
            cv2.addWeighted(overlay, 0.8, overlay_rect, 0.2, 0, overlay)
            
            # 准备标签文本
            label = f"{class_name}: {confidence:.1%}"
            
            # 计算文本尺寸
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            thickness = 2
            (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)
            
            # 绘制标签背景
            label_y = y1 - 10 if y1 - 10 > text_height else y1 + text_height + 10
            cv2.rectangle(overlay, 
                         (x1, label_y - text_height - 5), 
                         (x1 + text_width + 10, label_y + 5), 
                         color, -1)
            
            # 绘制标签文字
            cv2.putText(overlay, label, 
                       (x1 + 5, label_y - 5), 
                       font, font_scale, (255, 255, 255), thickness)
            
            # 添加置信度条
            confidence_bar_width = int((x2 - x1) * confidence)
            cv2.rectangle(overlay, 
                         (x1, y2 + 5), 
                         (x1 + confidence_bar_width, y2 + 15), 
                         color, -1)
        
        return overlay
    
    def create_heatmap(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        创建检测热力图
        
        Args:
            image: 原始图像
            detections: 检测结果列表
            
        Returns:
            热力图图像
        """
        height, width = image.shape[:2]
        heatmap = np.zeros((height, width), dtype=np.float32)
        
        for detection in detections:
            bbox = detection.get('bbox', {})
            confidence = detection.get('confidence', 0.0)
            
            # 获取边界框坐标
            if 'x1' in bbox:
                x1, y1, x2, y2 = bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']
            else:
                x, y, w, h = bbox.get('x', 0), bbox.get('y', 0), bbox.get('width', 0), bbox.get('height', 0)
                x1, y1, x2, y2 = x, y, x + w, y + h
            
            # 在热力图上添加权重
            heatmap[y1:y2, x1:x2] += confidence
        
        # 归一化热力图
        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()
        
        # 应用颜色映射
        heatmap_colored = cv2.applyColorMap((heatmap * 255).astype(np.uint8), cv2.COLORMAP_JET)
        
        # 与原图像混合
        result = cv2.addWeighted(image, 0.7, heatmap_colored, 0.3, 0)
        
        return result
    
    def image_to_base64(self, image: np.ndarray, format: str = 'JPEG') -> str:
        """
        将图像转换为base64字符串
        
        Args:
            image: 输入图像
            format: 图像格式
            
        Returns:
            base64编码的图像字符串
        """
        # 转换为PIL图像
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # 保存到字节流
        buffer = io.BytesIO()
        pil_image.save(buffer, format=format, quality=95)
        
        # 编码为base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/{format.lower()};base64,{image_base64}"
    
    def base64_to_image(self, base64_string: str) -> Optional[np.ndarray]:
        """
        将base64字符串转换为图像
        
        Args:
            base64_string: base64编码的图像字符串
            
        Returns:
            BGR格式的图像数组
        """
        try:
            # 移除data URL前缀
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # 解码base64
            image_bytes = base64.b64decode(base64_string)
            
            # 转换为图像
            return self.load_image_from_bytes(image_bytes)
        except Exception as e:
            print(f"base64转图像失败: {e}")
            return None
    
    def resize_image(self, image: np.ndarray, max_size: int = 1024) -> np.ndarray:
        """
        调整图像尺寸（保持宽高比）
        
        Args:
            image: 输入图像
            max_size: 最大尺寸
            
        Returns:
            调整后的图像
        """
        height, width = image.shape[:2]
        
        if max(height, width) <= max_size:
            return image
        
        # 计算缩放比例
        if height > width:
            new_height = max_size
            new_width = int(width * max_size / height)
        else:
            new_width = max_size
            new_height = int(height * max_size / width)
        
        # 调整尺寸
        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return resized
    
    def add_watermark(self, image: np.ndarray, text: str = "AI Detection System") -> np.ndarray:
        """
        添加水印
        
        Args:
            image: 输入图像
            text: 水印文字
            
        Returns:
            带水印的图像
        """
        watermarked = image.copy()
        height, width = watermarked.shape[:2]
        
        # 设置水印参数
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2
        color = (255, 255, 255)
        
        # 计算文字尺寸
        (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
        
        # 计算水印位置（右下角）
        x = width - text_width - 20
        y = height - 20
        
        # 添加半透明背景
        overlay = watermarked.copy()
        cv2.rectangle(overlay, (x - 10, y - text_height - 10), (x + text_width + 10, y + 10), (0, 0, 0), -1)
        cv2.addWeighted(watermarked, 0.8, overlay, 0.2, 0, watermarked)
        
        # 添加文字
        cv2.putText(watermarked, text, (x, y), font, font_scale, color, thickness)
        
        return watermarked
