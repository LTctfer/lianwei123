"""
污染源反算核心模块
整合遗传算法、模式搜索和高斯烟羽模型进行污染源溯源
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms.genetic_algorithm import GeneticAlgorithm
from algorithms.pattern_search import PatternSearch
from algorithms.gaussian_plume import GaussianPlumeModel
from algorithms.data_fusion import DataFusionProcessor

logger = logging.getLogger(__name__)

class SourceInversionEngine:
    """污染源反算引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化反算引擎
        
        Args:
            config: 配置参数
        """
        self.config = config
        
        # 初始化算法组件
        self.genetic_algorithm = GeneticAlgorithm(
            population_size=config.get('ga_population_size', 50),
            max_generations=config.get('ga_max_generations', 100),
            mutation_rate=config.get('ga_mutation_rate', 0.1),
            crossover_rate=config.get('ga_crossover_rate', 0.8)
        )
        
        self.pattern_search = PatternSearch(
            initial_step_size=config.get('ps_initial_step_size', 1.0),
            step_reduction_factor=config.get('ps_step_reduction_factor', 0.5),
            tolerance=config.get('ps_tolerance', 1e-6),
            max_iterations=config.get('ps_max_iterations', 1000)
        )
        
        self.gaussian_model = GaussianPlumeModel()
        self.data_fusion = DataFusionProcessor()
        
        # 搜索边界
        self.search_bounds = {
            'x': config.get('x_bounds', (-5000, 5000)),
            'y': config.get('y_bounds', (-5000, 5000)),
            'z': config.get('z_bounds', (0, 500)),
            'q': config.get('q_bounds', (0.1, 1000))
        }
        
        # 结果存储
        self.inversion_results = []
        self.convergence_history = []
        
    def preprocess_monitoring_data(self, 
                                 monitoring_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        预处理监测数据
        
        Args:
            monitoring_data: 各监测站数据
            
        Returns:
            融合后的监测数据
        """
        logger.info("开始预处理监测数据")
        
        # 数据融合
        fused_data = self.data_fusion.fuse_multi_station_data(
            monitoring_data, 
            fusion_method='weighted_average'
        )
        
        # 数据质量检查
        quality_score = self.data_fusion.calculate_data_quality_score(fused_data)
        logger.info(f"融合数据质量评分: {quality_score:.3f}")
        
        if quality_score < 0.5:
            logger.warning("数据质量较低，可能影响反算精度")
        
        return fused_data
    
    def calculate_fitness(self, 
                         source_params: Dict[str, float],
                         monitoring_data: pd.DataFrame,
                         meteorological_data: pd.DataFrame) -> float:
        """
        计算适应度函数
        
        Args:
            source_params: 污染源参数 {x, y, z, q}
            monitoring_data: 监测数据
            meteorological_data: 气象数据
            
        Returns:
            适应度值（越小越好）
        """
        try:
            total_error = 0.0
            valid_points = 0
            
            # 遍历每个监测点和时间
            for idx, row in monitoring_data.iterrows():
                if pd.isna(row['concentration']) or row['concentration'] <= 0:
                    continue
                
                # 获取对应的气象数据
                meteo_row = meteorological_data.iloc[idx] if idx < len(meteorological_data) else meteorological_data.iloc[-1]
                
                # 计算预测浓度
                predicted_conc = self.gaussian_model.calculate_concentration(
                    x=row['x'], y=row['y'], z=row.get('z', 1.5),
                    source_x=source_params['x'],
                    source_y=source_params['y'],
                    source_z=source_params['z'],
                    source_strength=source_params['q'],
                    wind_speed=meteo_row['wind_speed'],
                    wind_direction=meteo_row['wind_direction'],
                    stability_class=meteo_row.get('stability_class', 'D')
                )
                
                # 计算误差
                observed_conc = row['concentration']
                if predicted_conc > 0 and observed_conc > 0:
                    # 使用相对误差
                    error = abs(predicted_conc - observed_conc) / observed_conc
                    total_error += error
                    valid_points += 1
                else:
                    # 绝对误差
                    total_error += abs(predicted_conc - observed_conc)
                    valid_points += 1
            
            if valid_points == 0:
                return float('inf')
            
            # 平均相对误差
            fitness = total_error / valid_points
            
            # 添加正则化项（防止参数过大）
            regularization = (
                0.001 * (source_params['x']**2 + source_params['y']**2) / 1e6 +
                0.001 * source_params['z']**2 / 1e4 +
                0.001 * source_params['q']**2 / 1e4
            )
            
            return fitness + regularization
            
        except Exception as e:
            logger.error(f"适应度计算错误: {e}")
            return float('inf')
    
    def run_genetic_algorithm(self,
                            monitoring_data: pd.DataFrame,
                            meteorological_data: pd.DataFrame) -> Dict[str, Any]:
        """
        运行遗传算法进行粗略搜索
        
        Args:
            monitoring_data: 监测数据
            meteorological_data: 气象数据
            
        Returns:
            遗传算法结果
        """
        logger.info("开始遗传算法搜索")
        
        # 定义适应度函数
        def fitness_function(individual):
            source_params = {
                'x': individual.x,
                'y': individual.y,
                'z': individual.z,
                'q': individual.q
            }
            return self.calculate_fitness(source_params, monitoring_data, meteorological_data)
        
        # 运行遗传算法
        best_individual = self.genetic_algorithm.evolve(
            bounds=self.search_bounds,
            fitness_function=fitness_function
        )
        
        # 获取收敛历史
        ga_history = self.genetic_algorithm.get_convergence_history()
        
        result = {
            'algorithm': 'genetic_algorithm',
            'best_solution': {
                'x': best_individual.x,
                'y': best_individual.y,
                'z': best_individual.z,
                'q': best_individual.q
            },
            'best_fitness': best_individual.fitness,
            'convergence_history': ga_history,
            'generations': len(ga_history)
        }
        
        logger.info(f"遗传算法完成，最优适应度: {best_individual.fitness:.6f}")
        return result
    
    def run_pattern_search(self,
                          initial_solution: Dict[str, float],
                          monitoring_data: pd.DataFrame,
                          meteorological_data: pd.DataFrame) -> Dict[str, Any]:
        """
        运行模式搜索进行精细优化
        
        Args:
            initial_solution: 初始解
            monitoring_data: 监测数据
            meteorological_data: 气象数据
            
        Returns:
            模式搜索结果
        """
        logger.info("开始模式搜索优化")
        
        # 定义目标函数
        def objective_function(params):
            source_params = {
                'x': params[0],
                'y': params[1],
                'z': params[2],
                'q': params[3]
            }
            return self.calculate_fitness(source_params, monitoring_data, meteorological_data)
        
        # 初始点
        initial_point = [
            initial_solution['x'],
            initial_solution['y'],
            initial_solution['z'],
            initial_solution['q']
        ]
        
        # 运行模式搜索
        best_solution, best_value, ps_history = self.pattern_search.optimize(
            objective_function=objective_function,
            initial_point=initial_point,
            bounds=[
                self.search_bounds['x'],
                self.search_bounds['y'],
                self.search_bounds['z'],
                self.search_bounds['q']
            ]
        )
        
        result = {
            'algorithm': 'pattern_search',
            'best_solution': {
                'x': best_solution[0],
                'y': best_solution[1],
                'z': best_solution[2],
                'q': best_solution[3]
            },
            'best_fitness': best_value,
            'convergence_history': ps_history,
            'iterations': len(ps_history)
        }
        
        logger.info(f"模式搜索完成，最优适应度: {best_value:.6f}")
        return result
    
    def validate_solution(self,
                         solution: Dict[str, float],
                         monitoring_data: pd.DataFrame,
                         meteorological_data: pd.DataFrame) -> Dict[str, Any]:
        """
        验证解的准确性
        
        Args:
            solution: 反算解
            monitoring_data: 监测数据
            meteorological_data: 气象数据
            
        Returns:
            验证结果
        """
        logger.info("开始解验证")
        
        predictions = []
        observations = []
        errors = []
        
        for idx, row in monitoring_data.iterrows():
            if pd.isna(row['concentration']) or row['concentration'] <= 0:
                continue
            
            # 获取气象数据
            meteo_row = meteorological_data.iloc[idx] if idx < len(meteorological_data) else meteorological_data.iloc[-1]
            
            # 预测浓度
            predicted_conc = self.gaussian_model.calculate_concentration(
                x=row['x'], y=row['y'], z=row.get('z', 1.5),
                source_x=solution['x'],
                source_y=solution['y'],
                source_z=solution['z'],
                source_strength=solution['q'],
                wind_speed=meteo_row['wind_speed'],
                wind_direction=meteo_row['wind_direction'],
                stability_class=meteo_row.get('stability_class', 'D')
            )
            
            observed_conc = row['concentration']
            
            predictions.append(predicted_conc)
            observations.append(observed_conc)
            
            # 计算相对误差
            if observed_conc > 0:
                relative_error = abs(predicted_conc - observed_conc) / observed_conc * 100
            else:
                relative_error = abs(predicted_conc - observed_conc)
            
            errors.append(relative_error)
        
        # 统计指标
        predictions = np.array(predictions)
        observations = np.array(observations)
        errors = np.array(errors)
        
        # 计算统计指标
        mae = np.mean(np.abs(predictions - observations))
        rmse = np.sqrt(np.mean((predictions - observations)**2))
        mape = np.mean(errors)
        
        # 相关系数
        correlation = np.corrcoef(predictions, observations)[0, 1] if len(predictions) > 1 else 0
        
        # R²
        ss_res = np.sum((observations - predictions)**2)
        ss_tot = np.sum((observations - np.mean(observations))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        validation_result = {
            'mae': float(mae),
            'rmse': float(rmse),
            'mape': float(mape),
            'correlation': float(correlation),
            'r_squared': float(r_squared),
            'predictions': predictions.tolist(),
            'observations': observations.tolist(),
            'errors': errors.tolist(),
            'validation_points': len(predictions)
        }
        
        logger.info(f"验证完成 - MAE: {mae:.3f}, RMSE: {rmse:.3f}, MAPE: {mape:.1f}%, R²: {r_squared:.3f}")
        
        return validation_result
    
    def run_complete_inversion(self,
                             monitoring_data: Dict[str, pd.DataFrame],
                             meteorological_data: pd.DataFrame) -> Dict[str, Any]:
        """
        运行完整的污染源反算流程
        
        Args:
            monitoring_data: 监测站数据
            meteorological_data: 气象数据
            
        Returns:
            完整的反算结果
        """
        logger.info("开始完整污染源反算流程")
        
        start_time = datetime.now()
        
        try:
            # 1. 数据预处理
            fused_monitoring_data = self.preprocess_monitoring_data(monitoring_data)
            
            if len(fused_monitoring_data) == 0:
                raise ValueError("融合后的监测数据为空")
            
            # 2. 遗传算法粗略搜索
            ga_result = self.run_genetic_algorithm(fused_monitoring_data, meteorological_data)
            
            # 3. 模式搜索精细优化
            ps_result = self.run_pattern_search(
                ga_result['best_solution'],
                fused_monitoring_data,
                meteorological_data
            )
            
            # 4. 解验证
            validation_result = self.validate_solution(
                ps_result['best_solution'],
                fused_monitoring_data,
                meteorological_data
            )
            
            # 5. 生成浓度场预测
            concentration_field = self.generate_concentration_field(
                ps_result['best_solution'],
                meteorological_data.iloc[-1]  # 使用最新气象数据
            )
            
            end_time = datetime.now()
            computation_time = (end_time - start_time).total_seconds()
            
            # 整合结果
            complete_result = {
                'timestamp': start_time.isoformat(),
                'computation_time': computation_time,
                'data_quality': self.data_fusion.calculate_data_quality_score(fused_monitoring_data),
                'genetic_algorithm': ga_result,
                'pattern_search': ps_result,
                'final_solution': ps_result['best_solution'],
                'validation': validation_result,
                'concentration_field': concentration_field,
                'monitoring_stations': list(monitoring_data.keys()),
                'total_monitoring_points': len(fused_monitoring_data)
            }
            
            # 保存结果
            self.inversion_results.append(complete_result)
            
            logger.info(f"污染源反算完成，计算时间: {computation_time:.2f}秒")
            logger.info(f"最终解: x={ps_result['best_solution']['x']:.1f}m, "
                       f"y={ps_result['best_solution']['y']:.1f}m, "
                       f"z={ps_result['best_solution']['z']:.1f}m, "
                       f"q={ps_result['best_solution']['q']:.3f}g/s")
            
            return complete_result
            
        except Exception as e:
            logger.error(f"污染源反算失败: {e}")
            raise
    
    def generate_concentration_field(self,
                                   solution: Dict[str, float],
                                   meteorological_data: pd.Series,
                                   grid_resolution: int = 50) -> Dict[str, Any]:
        """
        生成浓度场分布
        
        Args:
            solution: 反算解
            meteorological_data: 气象数据
            grid_resolution: 网格分辨率
            
        Returns:
            浓度场数据
        """
        logger.info("生成浓度场分布")
        
        # 创建网格
        x_range = np.linspace(self.search_bounds['x'][0], self.search_bounds['x'][1], grid_resolution)
        y_range = np.linspace(self.search_bounds['y'][0], self.search_bounds['y'][1], grid_resolution)
        X, Y = np.meshgrid(x_range, y_range)
        
        # 计算浓度场
        concentration_field = self.gaussian_model.calculate_concentration_field(
            grid_x=X, grid_y=Y,
            source_x=solution['x'],
            source_y=solution['y'],
            source_z=solution['z'],
            source_strength=solution['q'],
            wind_speed=meteorological_data['wind_speed'],
            wind_direction=meteorological_data['wind_direction'],
            stability_class=meteorological_data.get('stability_class', 'D')
        )
        
        return {
            'x_grid': X.tolist(),
            'y_grid': Y.tolist(),
            'concentration': concentration_field.tolist(),
            'max_concentration': float(np.max(concentration_field)),
            'meteorological_conditions': {
                'wind_speed': float(meteorological_data['wind_speed']),
                'wind_direction': float(meteorological_data['wind_direction']),
                'stability_class': meteorological_data.get('stability_class', 'D')
            }
        }
    
    def get_inversion_summary(self) -> Dict[str, Any]:
        """获取反算结果摘要"""
        
        if not self.inversion_results:
            return {'message': '暂无反算结果'}
        
        latest_result = self.inversion_results[-1]
        
        summary = {
            'total_inversions': len(self.inversion_results),
            'latest_inversion': {
                'timestamp': latest_result['timestamp'],
                'computation_time': latest_result['computation_time'],
                'final_solution': latest_result['final_solution'],
                'validation_metrics': {
                    'mae': latest_result['validation']['mae'],
                    'rmse': latest_result['validation']['rmse'],
                    'mape': latest_result['validation']['mape'],
                    'r_squared': latest_result['validation']['r_squared']
                },
                'data_quality': latest_result['data_quality']
            }
        }
        
        return summary
    
    def export_results(self, filepath: str):
        """导出反算结果"""
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.inversion_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"结果已导出到: {filepath}")
            
        except Exception as e:
            logger.error(f"结果导出失败: {e}")
            raise