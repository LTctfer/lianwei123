"""
高斯烟羽模型模块
用于模拟大气污染物的扩散过程
"""

import numpy as np
import math
from typing import Tuple, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class GaussianPlumeModel:
    """高斯烟羽模型类"""
    
    def __init__(self):
        """初始化高斯烟羽模型"""
        
        # 大气稳定度分类
        self.stability_classes = ['A', 'B', 'C', 'D', 'E', 'F']
        
        # 扩散系数参数 [a, b, c] for sigma = a * x^b * (1 + c*x)^(-0.5)
        self.diffusion_coefficients = {
            'A': {  # 极不稳定
                'sigma_y': [0.22, 0.0001, 2.0],
                'sigma_z': [0.20, 0.0, 2.0]
            },
            'B': {  # 不稳定
                'sigma_y': [0.16, 0.0001, 1.0],
                'sigma_z': [0.12, 0.0, 1.0]
            },
            'C': {  # 弱不稳定
                'sigma_y': [0.11, 0.0001, 0.5],
                'sigma_z': [0.08, 0.0002, 0.5]
            },
            'D': {  # 中性
                'sigma_y': [0.08, 0.0001, 0.5],
                'sigma_z': [0.06, 0.0015, 0.5]
            },
            'E': {  # 弱稳定
                'sigma_y': [0.06, 0.0001, 0.5],
                'sigma_z': [0.03, 0.0003, 0.5]
            },
            'F': {  # 稳定
                'sigma_y': [0.04, 0.0001, 0.5],
                'sigma_z': [0.016, 0.0003, 0.5]
            }
        }
        
        # Pasquill-Gifford稳定度分类表
        self.stability_table = {
            # 风速范围: [日间太阳辐射强度, 夜间云量]
            (0, 2): {
                'strong': 'A', 'moderate': 'A', 'slight': 'B',
                'clear': 'F', 'partly_cloudy': 'F', 'overcast': 'D'
            },
            (2, 3): {
                'strong': 'A', 'moderate': 'B', 'slight': 'C',
                'clear': 'E', 'partly_cloudy': 'F', 'overcast': 'D'
            },
            (3, 5): {
                'strong': 'B', 'moderate': 'B', 'slight': 'C',
                'clear': 'D', 'partly_cloudy': 'E', 'overcast': 'D'
            },
            (5, 6): {
                'strong': 'C', 'moderate': 'C', 'slight': 'D',
                'clear': 'D', 'partly_cloudy': 'D', 'overcast': 'D'
            },
            (6, float('inf')): {
                'strong': 'C', 'moderate': 'D', 'slight': 'D',
                'clear': 'D', 'partly_cloudy': 'D', 'overcast': 'D'
            }
        }
    
    def determine_stability_class(self, 
                                wind_speed: float,
                                solar_radiation: str = 'moderate',
                                cloud_cover: str = 'partly_cloudy',
                                is_daytime: bool = True) -> str:
        """
        确定大气稳定度等级
        
        Args:
            wind_speed: 风速 (m/s)
            solar_radiation: 太阳辐射强度 ('strong', 'moderate', 'slight')
            cloud_cover: 云量 ('clear', 'partly_cloudy', 'overcast')
            is_daytime: 是否为白天
            
        Returns:
            稳定度等级 ('A', 'B', 'C', 'D', 'E', 'F')
        """
        # 根据风速找到对应的稳定度表
        for (min_speed, max_speed), conditions in self.stability_table.items():
            if min_speed <= wind_speed < max_speed:
                if is_daytime:
                    return conditions.get(solar_radiation, 'D')
                else:
                    return conditions.get(cloud_cover, 'D')
        
        return 'D'  # 默认中性条件
    
    def calculate_diffusion_coefficients(self, 
                                       distance: float,
                                       stability_class: str) -> Tuple[float, float]:
        """
        计算扩散系数
        
        Args:
            distance: 下风向距离 (m)
            stability_class: 大气稳定度等级
            
        Returns:
            (sigma_y, sigma_z) 水平和垂直扩散系数
        """
        if stability_class not in self.diffusion_coefficients:
            stability_class = 'D'  # 默认中性条件
        
        coeffs = self.diffusion_coefficients[stability_class]
        
        # 计算水平扩散系数 sigma_y
        a_y, b_y, c_y = coeffs['sigma_y']
        if distance > 0:
            sigma_y = a_y * (distance ** b_y) * ((1 + c_y * distance) ** (-0.5))
        else:
            sigma_y = 0.1  # 最小值
        
        # 计算垂直扩散系数 sigma_z
        a_z, b_z, c_z = coeffs['sigma_z']
        if distance > 0:
            sigma_z = a_z * (distance ** b_z) * ((1 + c_z * distance) ** (-0.5))
        else:
            sigma_z = 0.1  # 最小值
        
        return sigma_y, sigma_z
    
    def calculate_concentration(self,
                             x: float, y: float, z: float,
                             source_x: float, source_y: float, source_z: float,
                             source_strength: float,
                             wind_speed: float, wind_direction: float,
                             stability_class: str = 'D') -> float:
        """
        计算指定点的污染物浓度
        
        Args:
            x, y, z: 接受点坐标 (m)
            source_x, source_y, source_z: 污染源坐标 (m)
            source_strength: 源强 (g/s)
            wind_speed: 风速 (m/s)
            wind_direction: 风向 (度，0度为北风)
            stability_class: 大气稳定度等级
            
        Returns:
            污染物浓度 (μg/m³)
        """
        # 坐标转换：将坐标系转换为以污染源为原点，风向为x轴正方向
        dx = x - source_x
        dy = y - source_y
        dz = z - source_z
        
        # 风向角度转换（气象角度转数学角度）
        wind_rad = math.radians(270 - wind_direction)
        
        # 坐标旋转
        x_wind = dx * math.cos(wind_rad) + dy * math.sin(wind_rad)
        y_wind = -dx * math.sin(wind_rad) + dy * math.cos(wind_rad)
        z_wind = dz
        
        # 只考虑下风向的点
        if x_wind <= 0:
            return 0.0
        
        # 计算扩散系数
        sigma_y, sigma_z = self.calculate_diffusion_coefficients(x_wind, stability_class)
        
        # 确保风速不为零
        if wind_speed < 0.1:
            wind_speed = 0.1
        
        # 高斯烟羽公式
        try:
            # 水平扩散项
            horizontal_term = math.exp(-(y_wind ** 2) / (2 * sigma_y ** 2))
            
            # 垂直扩散项（考虑地面反射）
            vertical_term1 = math.exp(-((z_wind - source_z) ** 2) / (2 * sigma_z ** 2))
            vertical_term2 = math.exp(-((z_wind + source_z) ** 2) / (2 * sigma_z ** 2))
            vertical_term = vertical_term1 + vertical_term2
            
            # 浓度计算
            concentration = (source_strength / (2 * math.pi * wind_speed * sigma_y * sigma_z)) * \
                          horizontal_term * vertical_term
            
            # 转换单位：g/m³ -> μg/m³
            concentration *= 1e6
            
            return max(0.0, concentration)
            
        except (OverflowError, ZeroDivisionError, ValueError) as e:
            logger.warning(f"浓度计算异常: {e}")
            return 0.0
    
    def calculate_concentration_field(self,
                                   grid_x: np.ndarray, grid_y: np.ndarray,
                                   source_x: float, source_y: float, source_z: float,
                                   source_strength: float,
                                   wind_speed: float, wind_direction: float,
                                   stability_class: str = 'D',
                                   receptor_height: float = 1.5) -> np.ndarray:
        """
        计算浓度场分布
        
        Args:
            grid_x, grid_y: 网格坐标
            source_x, source_y, source_z: 污染源坐标
            source_strength: 源强
            wind_speed: 风速
            wind_direction: 风向
            stability_class: 大气稳定度
            receptor_height: 接受点高度
            
        Returns:
            浓度场数组
        """
        concentration_field = np.zeros_like(grid_x)
        
        for i in range(grid_x.shape[0]):
            for j in range(grid_x.shape[1]):
                concentration_field[i, j] = self.calculate_concentration(
                    grid_x[i, j], grid_y[i, j], receptor_height,
                    source_x, source_y, source_z,
                    source_strength, wind_speed, wind_direction, stability_class
                )
        
        return concentration_field
    
    def validate_parameters(self, **params) -> bool:
        """验证模型参数"""
        try:
            # 检查必需参数
            required_params = ['source_strength', 'wind_speed', 'wind_direction']
            for param in required_params:
                if param not in params or params[param] is None:
                    logger.error(f"缺少必需参数: {param}")
                    return False
            
            # 参数范围检查
            if params['source_strength'] <= 0:
                logger.error("源强必须大于0")
                return False
            
            if params['wind_speed'] <= 0:
                logger.error("风速必须大于0")
                return False
            
            if not (0 <= params['wind_direction'] <= 360):
                logger.error("风向必须在0-360度之间")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"参数验证失败: {e}")
            return False
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            'model_name': 'Gaussian Plume Model',
            'stability_classes': self.stability_classes,
            'diffusion_coefficients': self.diffusion_coefficients,
            'description': '高斯烟羽模型用于模拟大气污染物的扩散过程'
        }