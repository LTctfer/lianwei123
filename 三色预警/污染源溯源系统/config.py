"""
污染源溯源系统配置文件
包含算法参数、系统设置等配置信息
"""

import os
from typing import Dict, Any, List, Tuple

class Config:
    """系统配置类"""
    
    def __init__(self):
        """初始化配置"""
        self.setup_directories()
        self.setup_algorithm_config()
        self.setup_web_config()
        self.setup_data_config()
    
    def setup_directories(self):
        """设置目录结构"""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 创建必要的目录
        self.directories = {
            'data': os.path.join(self.base_dir, 'data'),
            'results': os.path.join(self.base_dir, 'results'),
            'uploads': os.path.join(self.base_dir, 'uploads'),
            'sample_data': os.path.join(self.base_dir, 'sample_data'),
            'logs': os.path.join(self.base_dir, 'logs')
        }
        
        # 确保目录存在
        for dir_path in self.directories.values():
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
    
    def setup_algorithm_config(self):
        """设置算法配置"""
        self.algorithm_config = {
            # 遗传算法参数
            'genetic_algorithm': {
                'population_size': 50,
                'generations': 100,
                'mutation_rate': 0.1,
                'crossover_rate': 0.8,
                'elite_size': 5,
                'tournament_size': 3
            },
            
            # 模式搜索参数
            'pattern_search': {
                'initial_step_size': 10.0,
                'step_reduction_factor': 0.5,
                'min_step_size': 0.1,
                'max_iterations': 200,
                'tolerance': 1e-6
            },
            
            # 高斯烟羽模型参数
            'gaussian_plume': {
                'default_stability_class': 'D',
                'min_wind_speed': 0.5,
                'max_wind_speed': 20.0,
                'default_mixing_height': 1000.0,
                'roughness_length': 0.1
            },
            
            # 数据融合参数
            'data_fusion': {
                'quality_threshold': 0.7,
                'weight_method': 'quality_based',
                'fusion_method': 'weighted_average',
                'outlier_threshold': 3.0
            },
            
            # 搜索区域参数
            'search_domain': {
                'x_min': -1000.0,
                'x_max': 1000.0,
                'y_min': -1000.0,
                'y_max': 1000.0,
                'z_min': 1.0,
                'z_max': 100.0,
                'q_min': 0.1,
                'q_max': 100.0
            }
        }
    
    def setup_web_config(self):
        """设置Web配置"""
        self.web_config = {
            'host': '0.0.0.0',
            'port': 5000,
            'debug': True,
            'max_file_size': 16 * 1024 * 1024,  # 16MB
            'allowed_extensions': {'csv', 'txt', 'xlsx'},
            'secret_key': 'pollution_source_tracing_2024'
        }
    
    def setup_data_config(self):
        """设置数据配置"""
        self.data_config = {
            # 数据验证范围
            'validation_ranges': {
                'pm25': (0, 1000),
                'pm10': (0, 2000),
                'wind_speed': (0, 50),
                'wind_direction': (0, 360),
                'temperature': (-50, 60),
                'humidity': (0, 100),
                'pressure': (800, 1200)
            },
            
            # 必需的数据列
            'required_columns': {
                'monitoring': ['station_id', 'x', 'y', 'pm25', 'wind_speed', 'wind_direction'],
                'meteorological': ['timestamp', 'wind_speed', 'wind_direction', 'temperature']
            },
            
            # 数据格式
            'datetime_format': '%Y-%m-%d %H:%M:%S',
            'encoding': 'utf-8'
        }
    
    def get_algorithm_config(self) -> Dict[str, Any]:
        """获取算法配置"""
        return self.algorithm_config
    
    def get_web_config(self) -> Dict[str, Any]:
        """获取Web配置"""
        return self.web_config
    
    def get_data_config(self) -> Dict[str, Any]:
        """获取数据配置"""
        return self.data_config
    
    def get_directory(self, name: str) -> str:
        """获取指定目录路径"""
        return self.directories.get(name, self.base_dir)
    
    def get_all_directories(self) -> Dict[str, str]:
        """获取所有目录路径"""
        return self.directories.copy()
    
    def update_config(self, section: str, key: str, value: Any):
        """更新配置项"""
        if section == 'algorithm':
            if key in self.algorithm_config:
                self.algorithm_config[key] = value
        elif section == 'web':
            if key in self.web_config:
                self.web_config[key] = value
        elif section == 'data':
            if key in self.data_config:
                self.data_config[key] = value
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        try:
            # 检查必要的配置项
            required_sections = ['algorithm_config', 'web_config', 'data_config']
            for section in required_sections:
                if not hasattr(self, section):
                    return False
            
            # 检查目录是否存在
            for dir_path in self.directories.values():
                if not os.path.exists(dir_path):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def get_stability_classes(self) -> List[str]:
        """获取大气稳定度分类"""
        return ['A', 'B', 'C', 'D', 'E', 'F']
    
    def get_stability_parameters(self, stability_class: str) -> Tuple[float, float, float, float]:
        """
        获取稳定度参数
        
        Args:
            stability_class: 稳定度分类
            
        Returns:
            (ay, by, az, bz) 参数元组
        """
        stability_params = {
            'A': (0.527, 0.865, 0.28, 0.90),
            'B': (0.371, 0.866, 0.23, 0.85),
            'C': (0.209, 0.897, 0.22, 0.80),
            'D': (0.128, 0.905, 0.20, 0.76),
            'E': (0.098, 0.902, 0.15, 0.73),
            'F': (0.065, 0.902, 0.12, 0.67)
        }
        
        return stability_params.get(stability_class, stability_params['D'])
    
    def __str__(self) -> str:
        """配置信息字符串表示"""
        return f"Config(base_dir='{self.base_dir}', directories={len(self.directories)})"
    
    def __repr__(self) -> str:
        """配置信息详细表示"""
        return self.__str__()

# 创建全局配置实例
config = Config()

# 导出常用配置
ALGORITHM_CONFIG = config.get_algorithm_config()
WEB_CONFIG = config.get_web_config()
DATA_CONFIG = config.get_data_config()
DIRECTORIES = config.get_all_directories()

# 导出配置类
__all__ = ['Config', 'config', 'ALGORITHM_CONFIG', 'WEB_CONFIG', 'DATA_CONFIG', 'DIRECTORIES']