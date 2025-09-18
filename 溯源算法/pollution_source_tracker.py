#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
污染物溯源系统
基于遗传-模式搜索算法的微尺度管控区域大气污染物PM2.5溯源

作者: AI Assistant
日期: 2025-01-18
版本: 1.0

主要功能:
1. 高斯烟羽模型实现污染物扩散计算
2. 遗传-模式搜索算法进行污染源反算
3. 正向扩散模拟验证反算结果
4. 实时监测数据处理和分析
"""

import numpy as np
import pandas as pd
import math
import random
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from deap import base, creator, tools, algorithms
import warnings
warnings.filterwarnings('ignore')

@dataclass
class MonitoringData:
    """监测站数据结构"""
    station_id: str
    x: float  # 东西方向坐标 (m)
    y: float  # 南北方向坐标 (m) 
    z: float  # 高度 (m)
    concentration: float  # 污染物浓度 (μg/m³)
    timestamp: str
    
@dataclass
class MeteorologicalData:
    """气象数据结构"""
    wind_speed: float  # 风速 (m/s)
    wind_direction: float  # 风向 (度，0-360)
    temperature: float  # 温度 (°C)
    humidity: float  # 湿度 (%)
    pressure: float  # 气压 (hPa)
    solar_radiation: float  # 太阳辐射强度 (W/m²)
    cloud_cover: float  # 云量 (0-1)
    timestamp: str

@dataclass
class PollutionSource:
    """污染源结构"""
    x: float  # 污染源x坐标 (m)
    y: float  # 污染源y坐标 (m)
    z: float  # 污染源高度 (m)
    emission_rate: float  # 排放强度 (g/s)
    confidence: float = 0.0  # 置信度

class AtmosphericStability:
    """大气稳定度分类"""
    
    # 大气稳定度等级
    STABILITY_CLASSES = ['A', 'B', 'C', 'D', 'E', 'F']
    
    @staticmethod
    def get_stability_class(wind_speed: float, solar_radiation: float, cloud_cover: float) -> str:
        """
        根据风速、太阳辐射和云量确定大气稳定度等级
        
        Args:
            wind_speed: 风速 (m/s)
            solar_radiation: 太阳辐射强度 (W/m²)
            cloud_cover: 云量 (0-1)
            
        Returns:
            大气稳定度等级 ('A'-'F')
        """
        # 白天条件判断
        if solar_radiation > 500:  # 强太阳辐射
            if wind_speed < 2:
                return 'A'  # 极不稳定
            elif wind_speed < 3:
                return 'A'
            elif wind_speed < 5:
                return 'B'  # 不稳定
            elif wind_speed < 6:
                return 'C'  # 弱不稳定
            else:
                return 'D'  # 中性
        elif solar_radiation > 200:  # 中等太阳辐射
            if wind_speed < 2:
                return 'B'
            elif wind_speed < 3:
                return 'B'
            elif wind_speed < 5:
                return 'C'
            elif wind_speed < 6:
                return 'D'
            else:
                return 'D'
        else:  # 夜晚或弱太阳辐射
            if cloud_cover > 0.5:  # 多云
                return 'D'  # 中性
            else:  # 晴朗夜晚
                if wind_speed < 2:
                    return 'F'  # 稳定
                elif wind_speed < 3:
                    return 'E'  # 弱稳定
                elif wind_speed < 5:
                    return 'D'
                else:
                    return 'D'
    
    @staticmethod
    def get_dispersion_coefficients(stability_class: str, distance: float) -> Tuple[float, float]:
        """
        根据大气稳定度等级和距离计算扩散系数（标准Pasquill-Gifford公式）

        Args:
            stability_class: 大气稳定度等级
            distance: 距离污染源的距离 (m)

        Returns:
            (sigma_y, sigma_z): 水平和垂直扩散系数 (m)
        """
        # 限制距离范围
        distance = max(10.0, min(distance, 100000.0))  # 10m到100km
        distance_km = distance / 1000.0  # 转换为公里

        # 标准Pasquill-Gifford扩散系数参数表
        # sigma_y = a * x^b, sigma_z = c * x^d (x为距离，单位km)
        coefficients = {
            'A': {'a_y': 213, 'b_y': 0.894, 'c_z': 440, 'd_z': 0.941},  # 极不稳定
            'B': {'a_y': 156, 'b_y': 0.894, 'c_z': 106, 'd_z': 0.718},  # 不稳定
            'C': {'a_y': 104, 'b_y': 0.894, 'c_z': 61, 'd_z': 0.718},   # 弱不稳定
            'D': {'a_y': 68, 'b_y': 0.894, 'c_z': 33, 'd_z': 0.718},    # 中性
            'E': {'a_y': 50.5, 'b_y': 0.894, 'c_z': 22.8, 'd_z': 0.718}, # 弱稳定
            'F': {'a_y': 34, 'b_y': 0.894, 'c_z': 14.35, 'd_z': 0.718}   # 稳定
        }

        if stability_class not in coefficients:
            stability_class = 'D'  # 默认中性条件

        coeff = coefficients[stability_class]

        # 计算扩散系数 (结果单位为米)
        sigma_y = coeff['a_y'] * (distance_km ** coeff['b_y'])
        sigma_z = coeff['c_z'] * (distance_km ** coeff['d_z'])

        # 对于近距离，增加扩散系数以避免过度集中
        if distance < 1000:  # 1000米以内
            min_sigma_y = 50.0  # 大幅增加最小水平扩散系数
            min_sigma_z = 25.0  # 大幅增加最小垂直扩散系数
            sigma_y = max(min_sigma_y, sigma_y)
            sigma_z = max(min_sigma_z, sigma_z)

        # 确保最小值，大幅增加扩散范围
        sigma_y = max(sigma_y, 40.0)
        sigma_z = max(sigma_z, 20.0)

        return sigma_y, sigma_z

class GaussianPlumeModel:
    """高斯烟羽模型"""
    
    def __init__(self):
        self.stability = AtmosphericStability()
    
    def calculate_concentration(self, 
                              source: PollutionSource,
                              receptor_x: float, 
                              receptor_y: float, 
                              receptor_z: float,
                              met_data: MeteorologicalData) -> float:
        """
        计算受体点的污染物浓度
        
        Args:
            source: 污染源信息
            receptor_x, receptor_y, receptor_z: 受体点坐标
            met_data: 气象数据
            
        Returns:
            污染物浓度 (μg/m³)
        """
        # 坐标转换到风向坐标系
        # 注意：气象风向是风吹来的方向，需要转换为风吹向的方向
        wind_to_rad = math.radians(met_data.wind_direction + 180)  # 转换为风吹向的方向

        # 相对位置
        dx = receptor_x - source.x
        dy = receptor_y - source.y
        dz = receptor_z - source.z

        # 转换到风向坐标系 (x为下风向，正值表示下风向)
        x = dx * math.cos(wind_to_rad) + dy * math.sin(wind_to_rad)
        y = -dx * math.sin(wind_to_rad) + dy * math.cos(wind_to_rad)
        z = receptor_z
        
        # 只计算下风向的浓度，但允许小的负值（考虑数值误差）
        if x < -10.0:  # 允许10米的容差
            return 0.0
            
        # 获取大气稳定度
        stability_class = self.stability.get_stability_class(
            met_data.wind_speed, 
            met_data.solar_radiation, 
            met_data.cloud_cover
        )
        
        # 计算扩散系数
        sigma_y, sigma_z = self.stability.get_dispersion_coefficients(stability_class, x)
        
        # 避免除零错误
        if sigma_y <= 0 or sigma_z <= 0 or met_data.wind_speed <= 0:
            return 0.0
            
        # 高斯烟羽模型公式
        try:
            # 检查指数函数的参数，避免数值溢出
            y_term = (y / sigma_y) ** 2
            z_term1 = ((z - source.z) / sigma_z) ** 2
            z_term2 = ((z + source.z) / sigma_z) ** 2

            # 限制指数参数，避免数值下溢
            max_exp_arg = 50.0  # exp(-50) ≈ 2e-22，足够小但不会下溢
            y_term = min(y_term, max_exp_arg)
            z_term1 = min(z_term1, max_exp_arg)
            z_term2 = min(z_term2, max_exp_arg)

            # 水平扩散项
            horizontal_term = math.exp(-0.5 * y_term)

            # 垂直扩散项 (考虑地面反射)
            vertical_term1 = math.exp(-0.5 * z_term1)
            vertical_term2 = math.exp(-0.5 * z_term2)
            vertical_term = vertical_term1 + vertical_term2

            # 分母计算
            denominator = 2 * math.pi * met_data.wind_speed * sigma_y * sigma_z

            # 检查分母是否过小
            if denominator < 1e-10:
                return 0.0

            # 浓度计算
            concentration = (source.emission_rate / denominator) * horizontal_term * vertical_term

            # 检查计算结果是否合理
            if not math.isfinite(concentration) or concentration < 0:
                return 0.0

            # 单位转换: g/m³ -> μg/m³
            concentration *= 1e6

            # 设置合理的浓度范围
            concentration = min(concentration, 1e6)  # 最大1000 mg/m³

            return max(0.0, concentration)

        except (OverflowError, ZeroDivisionError, ValueError):
            return 0.0
    
    def simulate_dispersion(self, 
                          source: PollutionSource,
                          grid_x: np.ndarray,
                          grid_y: np.ndarray,
                          height: float,
                          met_data: MeteorologicalData) -> np.ndarray:
        """
        模拟污染物在网格上的扩散分布
        
        Args:
            source: 污染源
            grid_x, grid_y: 网格坐标
            height: 计算高度
            met_data: 气象数据
            
        Returns:
            浓度分布矩阵
        """
        concentration_grid = np.zeros_like(grid_x)
        
        for i in range(grid_x.shape[0]):
            for j in range(grid_x.shape[1]):
                concentration_grid[i, j] = self.calculate_concentration(
                    source, grid_x[i, j], grid_y[i, j], height, met_data
                )
                
        return concentration_grid


class GeneticPatternSearch:
    """遗传-模式搜索算法"""

    def __init__(self,
                 population_size: int = 300,
                 max_generations: int = 1500,
                 crossover_prob: float = 0.85,
                 mutation_prob: float = 0.2,
                 elite_ratio: float = 0.2):
        """
        初始化遗传-模式搜索算法

        Args:
            population_size: 种群大小
            max_generations: 最大迭代次数
            crossover_prob: 交叉概率
            mutation_prob: 变异概率
            elite_ratio: 精英保留比例
        """
        self.population_size = population_size
        self.max_generations = max_generations
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.elite_ratio = elite_ratio
        self.elite_size = int(population_size * elite_ratio)

        # 早停参数
        self.patience = 100  # 连续多少代没有改进就停止
        self.min_improvement = 1e-6  # 最小改进阈值

        # 搜索边界 [x_min, x_max, y_min, y_max, z_min, z_max, q_min, q_max]
        self.bounds = [-1000, 1000, -1000, 1000, 0, 100, 0.1, 10.0]

        # 初始化DEAP
        self._setup_deap()

    def _setup_deap(self):
        """设置DEAP遗传算法框架"""
        # 创建适应度类型 (最大化适应度)
        if not hasattr(creator, "FitnessMax"):
            creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        if not hasattr(creator, "Individual"):
            creator.create("Individual", list, fitness=creator.FitnessMax)

        self.toolbox = base.Toolbox()

        # 注册基因生成函数
        self.toolbox.register("attr_x", random.uniform, self.bounds[0], self.bounds[1])
        self.toolbox.register("attr_y", random.uniform, self.bounds[2], self.bounds[3])
        self.toolbox.register("attr_z", random.uniform, self.bounds[4], self.bounds[5])
        self.toolbox.register("attr_q", random.uniform, self.bounds[6], self.bounds[7])

        # 注册个体和种群生成函数
        self.toolbox.register("individual", tools.initCycle, creator.Individual,
                             (self.toolbox.attr_x, self.toolbox.attr_y,
                              self.toolbox.attr_z, self.toolbox.attr_q), n=1)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)

        # 注册遗传操作
        self.toolbox.register("mate", self._crossover)
        self.toolbox.register("mutate", self._mutation)
        self.toolbox.register("select", tools.selTournament, tournsize=3)

    def _crossover(self, ind1, ind2):
        """自定义交叉操作"""
        # 模拟二进制交叉
        eta = 20.0  # 分布指数

        for i in range(len(ind1)):
            if random.random() <= 0.5:
                # 计算交叉参数
                u = random.random()
                if u <= 0.5:
                    beta = (2 * u) ** (1.0 / (eta + 1))
                else:
                    beta = (1.0 / (2 * (1 - u))) ** (1.0 / (eta + 1))

                # 执行交叉
                x1 = 0.5 * ((1 + beta) * ind1[i] + (1 - beta) * ind2[i])
                x2 = 0.5 * ((1 - beta) * ind1[i] + (1 + beta) * ind2[i])

                # 边界检查
                x1 = max(self.bounds[i*2], min(self.bounds[i*2+1], x1))
                x2 = max(self.bounds[i*2], min(self.bounds[i*2+1], x2))

                ind1[i] = x1
                ind2[i] = x2

        return ind1, ind2

    def _mutation(self, individual):
        """自定义变异操作"""
        eta = 20.0  # 分布指数

        for i in range(len(individual)):
            if random.random() <= (1.0 / len(individual)):
                # 多项式变异
                u = random.random()
                delta_max = (self.bounds[i*2+1] - self.bounds[i*2]) * 0.1

                if u <= 0.5:
                    delta = (2 * u) ** (1.0 / (eta + 1)) - 1
                else:
                    delta = 1 - (2 * (1 - u)) ** (1.0 / (eta + 1))

                individual[i] += delta * delta_max

                # 边界检查
                individual[i] = max(self.bounds[i*2],
                                  min(self.bounds[i*2+1], individual[i]))

        return individual,

    def _pattern_search(self, individual, fitness_func, step_size=10.0):
        """模式搜索局部优化"""
        best_individual = individual[:]
        best_fitness = fitness_func(individual)[0]

        # 搜索方向 (坐标轴方向)
        directions = [
            [1, 0, 0, 0], [-1, 0, 0, 0],  # x方向
            [0, 1, 0, 0], [0, -1, 0, 0],  # y方向
            [0, 0, 1, 0], [0, 0, -1, 0],  # z方向
            [0, 0, 0, 1], [0, 0, 0, -1]   # q方向
        ]

        improved = True
        current_step = step_size

        while improved and current_step > 0.1:
            improved = False

            for direction in directions:
                # 生成新的候选解
                candidate = [individual[i] + direction[i] * current_step
                           for i in range(len(individual))]

                # 边界检查
                for i in range(len(candidate)):
                    candidate[i] = max(self.bounds[i*2],
                                     min(self.bounds[i*2+1], candidate[i]))

                # 评估候选解
                candidate_fitness = fitness_func(candidate)[0]

                if candidate_fitness > best_fitness:
                    best_individual = candidate[:]
                    best_fitness = candidate_fitness
                    improved = True
                    break

            if not improved:
                current_step *= 0.5

        return best_individual, best_fitness

    def optimize(self, fitness_func) -> Tuple[List[float], float]:
        """
        执行遗传-模式搜索优化

        Args:
            fitness_func: 适应度函数

        Returns:
            (最优解, 最优适应度值)
        """
        # 注册适应度函数
        self.toolbox.register("evaluate", fitness_func)

        # 初始化种群
        population = self.toolbox.population(n=self.population_size)

        # 评估初始种群
        fitnesses = list(map(self.toolbox.evaluate, population))
        for ind, fit in zip(population, fitnesses):
            ind.fitness.values = fit

        # 记录最优解
        best_individual = None
        best_fitness = float('-inf')

        # 早停相关变量
        no_improvement_count = 0
        last_best_fitness = float('-inf')

        # 进化循环
        for generation in range(self.max_generations):
            # 选择
            offspring = self.toolbox.select(population, len(population))
            offspring = list(map(self.toolbox.clone, offspring))

            # 交叉
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < self.crossover_prob:
                    self.toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            # 变异
            for mutant in offspring:
                if random.random() < self.mutation_prob:
                    self.toolbox.mutate(mutant)
                    del mutant.fitness.values

            # 评估无效个体
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(self.toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            # 精英保留策略
            population.sort(key=lambda x: x.fitness.values[0], reverse=True)
            offspring.sort(key=lambda x: x.fitness.values[0], reverse=True)

            # 保留最优个体
            elite_count = int(self.population_size * self.elite_ratio)
            elite_individuals = population[:elite_count]

            # 对最差的个体进行模式搜索
            worst_individuals = offspring[-self.elite_size:]
            for ind in worst_individuals:
                improved_ind, improved_fitness = self._pattern_search(
                    ind, fitness_func
                )
                if improved_fitness > ind.fitness.values[0]:
                    ind[:] = improved_ind
                    ind.fitness.values = (improved_fitness,)

            # 更新种群：精英个体 + 改进后的后代
            population = elite_individuals + offspring[:-elite_count]

            # 记录最优解
            current_best = max(population, key=lambda x: x.fitness.values[0])
            if current_best.fitness.values[0] > best_fitness:
                best_individual = current_best[:]
                best_fitness = current_best.fitness.values[0]

            # 早停检查
            if best_fitness - last_best_fitness > self.min_improvement:
                no_improvement_count = 0
                last_best_fitness = best_fitness
            else:
                no_improvement_count += 1

            # 早停条件
            if no_improvement_count >= self.patience:
                print(f"Early stopping at generation {generation}: No improvement for {self.patience} generations")
                break

            # 收敛检查
            if generation % 50 == 0:
                avg_fitness = sum(ind.fitness.values[0] for ind in population) / len(population)
                print(f"Generation {generation}: Best={best_fitness:.6f}, Avg={avg_fitness:.6f}")

        return best_individual, best_fitness


class PollutionSourceTracker:
    """污染源溯源主类"""

    def __init__(self):
        """初始化污染源溯源器"""
        self.gaussian_model = GaussianPlumeModel()
        self.genetic_search = GeneticPatternSearch()
        self.monitoring_data = []
        self.meteorological_data = None

    def add_monitoring_data(self, data: MonitoringData):
        """添加监测数据"""
        self.monitoring_data.append(data)

    def set_meteorological_data(self, data: MeteorologicalData):
        """设置气象数据"""
        self.meteorological_data = data

    def _fitness_function(self, individual: List[float]) -> Tuple[float]:
        """
        改进的多目标适应度函数：计算理论浓度与观测浓度的匹配程度

        Args:
            individual: [x, y, z, emission_rate] 污染源参数

        Returns:
            适应度值 (越大越好)
        """
        if self.meteorological_data is None or len(self.monitoring_data) == 0:
            return (0.0,)

        x, y, z, emission_rate = individual

        # 检查解的有效性
        if emission_rate <= 0:
            return (0.0,)

        # 检查位置是否在合理范围内
        if not (-2000 <= x <= 2000 and -2000 <= y <= 2000 and 0 <= z <= 200):
            return (0.0,)

        # 创建污染源
        source = PollutionSource(x=x, y=y, z=z, emission_rate=emission_rate)

        # 计算各种误差指标
        total_relative_error = 0.0
        total_absolute_error = 0.0
        max_relative_error = 0.0
        valid_points = 0

        predicted_concentrations = []
        observed_concentrations = []

        for monitor in self.monitoring_data:
            # 计算理论浓度
            theoretical_conc = self.gaussian_model.calculate_concentration(
                source, monitor.x, monitor.y, monitor.z, self.meteorological_data
            )

            # 改进的误差计算：处理零值预测
            predicted_concentrations.append(theoretical_conc)
            observed_concentrations.append(monitor.concentration)

            # 如果预测值为0但观测值不为0，给予重惩罚
            if theoretical_conc <= 0.01 and monitor.concentration > 0.1:
                # 对于零预测但有观测值的情况，使用固定的大误差
                relative_error = 10.0  # 1000%的误差
                absolute_error = monitor.concentration
            else:
                # 正常的误差计算
                if monitor.concentration > 0.01:
                    relative_error = abs(theoretical_conc - monitor.concentration) / monitor.concentration
                else:
                    # 对于很小的观测值，使用绝对误差
                    relative_error = abs(theoretical_conc - monitor.concentration)

                absolute_error = abs(theoretical_conc - monitor.concentration)

            total_relative_error += relative_error
            max_relative_error = max(max_relative_error, relative_error)
            total_absolute_error += absolute_error
            valid_points += 1

        if valid_points == 0:
            return (0.0,)

        # 平均相对误差
        avg_relative_error = total_relative_error / valid_points

        # 计算相关系数
        correlation = 0.0
        if len(predicted_concentrations) > 1:
            try:
                import numpy as np
                correlation = np.corrcoef(predicted_concentrations, observed_concentrations)[0, 1]
                if np.isnan(correlation):
                    correlation = 0.0
            except:
                correlation = 0.0

        # 多目标适应度函数
        # 目标1: 最小化平均相对误差 (权重: 0.4)
        fitness_relative = 1.0 / (1.0 + avg_relative_error)

        # 目标2: 最小化最大相对误差 (权重: 0.3) - 确保所有站点精度
        fitness_max_error = 1.0 / (1.0 + max_relative_error)

        # 目标3: 最大化相关系数 (权重: 0.2)
        fitness_correlation = max(0.0, correlation)

        # 目标4: 空间约束检查 (权重: 0.15)
        spatial_constraint = self._calculate_spatial_constraints(
            source, predicted_concentrations, observed_concentrations
        )

        # 目标5: 物理合理性检查 (权重: 0.05)
        physical_constraint = self._calculate_physical_constraints(source)

        # 综合适应度
        fitness = (0.35 * fitness_relative +
                  0.25 * fitness_max_error +
                  0.2 * fitness_correlation +
                  0.15 * spatial_constraint +
                  0.05 * physical_constraint)

        # 严格的精度要求：如果平均相对误差超过20%，大幅降低适应度
        if avg_relative_error > 0.2:
            fitness *= 0.1

        # 如果最大相对误差超过50%，进一步降低适应度
        if max_relative_error > 0.5:
            fitness *= 0.1

        return (fitness,)

    def _calculate_spatial_constraints(self, source, predicted_concentrations, observed_concentrations):
        """
        计算空间约束项：检查浓度分布的空间合理性

        Args:
            source: 污染源
            predicted_concentrations: 预测浓度列表
            observed_concentrations: 观测浓度列表

        Returns:
            float: 空间约束得分 (0-1，越大越好)
        """
        if len(self.monitoring_data) < 3:
            return 0.5  # 监测站太少，无法进行空间约束

        constraint_score = 1.0

        # 1. 距离-浓度关系检查
        # 在下风向，距离污染源越近，浓度应该越高
        wind_to_rad = math.radians(self.meteorological_data.wind_direction + 180)

        downwind_stations = []
        for i, monitor in enumerate(self.monitoring_data):
            # 计算相对于污染源的位置
            dx = monitor.x - source.x
            dy = monitor.y - source.y

            # 转换到风向坐标系
            x_wind = dx * math.cos(wind_to_rad) + dy * math.sin(wind_to_rad)

            # 只考虑下风向的监测站
            if x_wind > 10:  # 下风向10米以外
                distance = math.sqrt(dx**2 + dy**2)
                downwind_stations.append((distance, predicted_concentrations[i], observed_concentrations[i]))

        # 检查距离-浓度的单调性
        if len(downwind_stations) >= 2:
            downwind_stations.sort(key=lambda x: x[0])  # 按距离排序

            # 检查浓度是否随距离递减（允许一定的波动）
            violations = 0
            for i in range(len(downwind_stations) - 1):
                dist1, pred1, obs1 = downwind_stations[i]
                dist2, pred2, obs2 = downwind_stations[i + 1]

                # 如果远距离的浓度明显高于近距离，给予惩罚
                if pred2 > pred1 * 1.5:  # 允许50%的波动
                    violations += 1

            if violations > 0:
                constraint_score *= (1.0 - violations / len(downwind_stations))

        # 2. 浓度梯度合理性检查
        # 相邻监测站的浓度变化应该平滑
        gradient_penalty = 0.0
        for i in range(len(self.monitoring_data)):
            for j in range(i + 1, len(self.monitoring_data)):
                monitor1 = self.monitoring_data[i]
                monitor2 = self.monitoring_data[j]

                distance = math.sqrt((monitor1.x - monitor2.x)**2 + (monitor1.y - monitor2.y)**2)

                # 只检查相对较近的监测站对
                if distance < 500:  # 500米以内
                    pred_diff = abs(predicted_concentrations[i] - predicted_concentrations[j])
                    obs_diff = abs(observed_concentrations[i] - observed_concentrations[j])

                    # 如果预测差异与观测差异相差太大，给予惩罚
                    if obs_diff > 0.01:  # 避免除零
                        ratio = pred_diff / obs_diff
                        if ratio > 3.0 or ratio < 0.33:  # 差异比例不合理
                            gradient_penalty += 0.1

        constraint_score *= max(0.0, 1.0 - gradient_penalty)

        return max(0.0, min(1.0, constraint_score))

    def _calculate_physical_constraints(self, source):
        """
        计算物理约束项：检查污染源参数的物理合理性

        Args:
            source: 污染源

        Returns:
            float: 物理约束得分 (0-1，越大越好)
        """
        constraint_score = 1.0

        # 1. 排放强度合理性
        # 排放强度应该在合理范围内
        if source.emission_rate < 0.1 or source.emission_rate > 1000:
            constraint_score *= 0.5

        # 2. 高度合理性
        # 污染源高度应该合理
        if source.z < 5 or source.z > 150:
            constraint_score *= 0.8

        # 3. 位置合理性
        # 污染源不应该距离所有监测站都太远
        min_distance = float('inf')
        max_distance = 0.0
        for monitor in self.monitoring_data:
            distance = math.sqrt((source.x - monitor.x)**2 + (source.y - monitor.y)**2)
            min_distance = min(min_distance, distance)
            max_distance = max(max_distance, distance)

        # 如果距离最近监测站太远，给予惩罚
        if min_distance > 1000:  # 1公里以外
            constraint_score *= 0.7

        # 如果距离最近监测站太近，也给予惩罚
        if min_distance < 30:  # 30米以内
            constraint_score *= 0.8

        return max(0.0, min(1.0, constraint_score))

    def trace_pollution_source(self) -> Optional[PollutionSource]:
        """
        执行污染源溯源

        Returns:
            溯源得到的污染源，如果失败返回None
        """
        if self.meteorological_data is None or len(self.monitoring_data) == 0:
            print("错误：缺少监测数据或气象数据")
            return None

        print("开始多阶段污染源溯源...")
        print(f"监测站点数量: {len(self.monitoring_data)}")
        print(f"气象条件: 风速={self.meteorological_data.wind_speed}m/s, "
              f"风向={self.meteorological_data.wind_direction}°")

        # 第一阶段：粗搜索 - 大范围快速定位
        print("\n=== 第一阶段：粗搜索 ===")
        coarse_search = GeneticPatternSearch(
            population_size=200,
            max_generations=500,
            crossover_prob=0.8,
            mutation_prob=0.3,  # 高变异率增加探索
            elite_ratio=0.1
        )

        # 设置大搜索范围
        coarse_search.bounds = [-2000, 2000, -2000, 2000, 0, 200, 0.1, 1000]
        coarse_search._setup_deap()

        best_coarse, fitness_coarse = coarse_search.optimize(self._fitness_function)

        if best_coarse is None:
            print("第一阶段搜索失败")
            return None

        print(f"粗搜索结果: 位置({best_coarse[0]:.1f}, {best_coarse[1]:.1f}), 适应度={fitness_coarse:.6f}")

        # 第二阶段：精搜索 - 小范围精确优化
        print("\n=== 第二阶段：精搜索 ===")
        fine_search = GeneticPatternSearch(
            population_size=300,
            max_generations=1000,
            crossover_prob=0.85,
            mutation_prob=0.15,  # 降低变异率，专注开发
            elite_ratio=0.25
        )

        # 设置小搜索范围（围绕粗搜索结果）
        search_radius = 500  # 500米搜索半径
        fine_search.bounds = [
            best_coarse[0] - search_radius, best_coarse[0] + search_radius,
            best_coarse[1] - search_radius, best_coarse[1] + search_radius,
            max(0, best_coarse[2] - 50), min(200, best_coarse[2] + 50),
            max(0.1, best_coarse[3] * 0.1), best_coarse[3] * 10
        ]
        fine_search._setup_deap()

        # 使用粗搜索结果初始化部分种群
        best_solution, best_fitness = fine_search.optimize(self._fitness_function)

        if best_solution is None:
            print("精搜索失败，使用粗搜索结果")
            best_solution = best_coarse
            best_fitness = fitness_coarse

        # 验证结果精度
        source = PollutionSource(
            x=best_solution[0],
            y=best_solution[1],
            z=best_solution[2],
            emission_rate=best_solution[3],
            confidence=best_fitness
        )

        # 计算所有监测站的预测精度
        relative_errors = []
        for monitor in self.monitoring_data:
            predicted = self.gaussian_model.calculate_concentration(
                source, monitor.x, monitor.y, monitor.z, self.meteorological_data
            )
            if monitor.concentration > 0:
                relative_error = abs(predicted - monitor.concentration) / monitor.concentration
                relative_errors.append(relative_error)

        avg_relative_error = sum(relative_errors) / len(relative_errors) if relative_errors else 1.0
        max_relative_error = max(relative_errors) if relative_errors else 1.0

        print(f"溯源完成:")
        print(f"  污染源位置: 东西方向{source.x:.1f}米, 南北方向{source.y:.1f}米, 高度{source.z:.1f}米")
        print(f"  排放强度: {source.emission_rate:.3f} 克/秒")
        print(f"  置信度: {source.confidence:.6f}")
        print(f"  平均相对误差: {avg_relative_error:.1%}")
        print(f"  最大相对误差: {max_relative_error:.1%}")

        # 检查是否满足精度要求
        if avg_relative_error > 0.2:
            print(f"警告：平均相对误差({avg_relative_error:.1%})超过20%，建议检查数据质量")
        if max_relative_error > 0.5:
            print(f"警告：最大相对误差({max_relative_error:.1%})超过50%，部分监测站预测精度较低")

        return source

    def verify_source(self, source: PollutionSource) -> Dict[str, float]:
        """
        验证污染源溯源结果

        Args:
            source: 溯源得到的污染源

        Returns:
            验证结果统计
        """
        if self.meteorological_data is None or len(self.monitoring_data) == 0:
            return {}

        print("\n开始验证溯源结果...")

        # 计算各监测点的理论浓度和误差
        results = []
        total_error = 0.0
        max_error = 0.0

        for i, monitor in enumerate(self.monitoring_data):
            # 计算理论浓度
            theoretical_conc = self.gaussian_model.calculate_concentration(
                source, monitor.x, monitor.y, monitor.z, self.meteorological_data
            )

            # 计算误差
            absolute_error = abs(monitor.concentration - theoretical_conc)
            relative_error = (absolute_error / max(monitor.concentration, 1.0)) * 100

            results.append({
                'station_id': monitor.station_id,
                'observed': monitor.concentration,
                'predicted': theoretical_conc,
                'absolute_error': absolute_error,
                'relative_error': relative_error
            })

            total_error += absolute_error
            max_error = max(max_error, absolute_error)

            print(f"  站点{monitor.station_id}: 实际观测={monitor.concentration:.1f}, "
                  f"模型预测={theoretical_conc:.1f}, 相对误差={relative_error:.1f}%")

        # 计算统计指标
        mean_absolute_error = total_error / len(self.monitoring_data)
        rmse = math.sqrt(sum((r['observed'] - r['predicted'])**2 for r in results) / len(results))

        # 计算相关系数
        observed_values = [r['observed'] for r in results]
        predicted_values = [r['predicted'] for r in results]

        obs_mean = sum(observed_values) / len(observed_values)
        pred_mean = sum(predicted_values) / len(predicted_values)

        numerator = sum((obs - obs_mean) * (pred - pred_mean)
                       for obs, pred in zip(observed_values, predicted_values))
        obs_var = sum((obs - obs_mean)**2 for obs in observed_values)
        pred_var = sum((pred - pred_mean)**2 for pred in predicted_values)

        correlation = numerator / math.sqrt(obs_var * pred_var) if obs_var > 0 and pred_var > 0 else 0

        verification_stats = {
            'mean_absolute_error': mean_absolute_error,
            'max_absolute_error': max_error,
            'rmse': rmse,
            'correlation': correlation,
            'num_stations': len(self.monitoring_data)
        }

        print(f"\n验证结果统计:")
        print(f"  平均绝对误差: {mean_absolute_error:.2f} μg/m³")
        print(f"  最大绝对误差: {max_error:.2f} μg/m³")
        print(f"  均方根误差: {rmse:.2f} μg/m³")
        print(f"  相关系数: {correlation:.3f}")

        return verification_stats

    def simulate_forward_dispersion(self,
                                  source: PollutionSource,
                                  grid_size: int = 50,
                                  domain_size: float = 2000) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        正向模拟污染物扩散

        Args:
            source: 污染源
            grid_size: 网格大小
            domain_size: 计算域大小 (m)

        Returns:
            (x_grid, y_grid, concentration_grid): 网格坐标和浓度分布
        """
        if self.meteorological_data is None:
            raise ValueError("缺少气象数据")

        # 创建计算网格
        x = np.linspace(-domain_size/2, domain_size/2, grid_size)
        y = np.linspace(-domain_size/2, domain_size/2, grid_size)
        x_grid, y_grid = np.meshgrid(x, y)

        # 计算浓度分布 (地面高度)
        concentration_grid = self.gaussian_model.simulate_dispersion(
            source, x_grid, y_grid, 2.0, self.meteorological_data
        )

        return x_grid, y_grid, concentration_grid


def create_sample_data() -> Tuple[List[MonitoringData], MeteorologicalData]:
    """
    创建示例数据用于测试

    Returns:
        (监测数据列表, 气象数据)
    """
    # 真实污染源位置 (用于生成模拟观测数据)
    true_source = PollutionSource(x=100, y=50, z=10, emission_rate=2.0)

    # 气象条件
    met_data = MeteorologicalData(
        wind_speed=3.0,
        wind_direction=45.0,  # 东北风
        temperature=20.0,
        humidity=60.0,
        pressure=1013.25,
        solar_radiation=300.0,
        cloud_cover=0.3,
        timestamp="2024-01-01 12:00:00"
    )

    # 监测站位置
    station_positions = [
        ("S001", 200, 100, 2),
        ("S002", 300, 150, 2),
        ("S003", 150, 200, 2),
        ("S004", 400, 200, 2),
        ("S005", 250, 50, 2),
        ("S006", 350, 100, 2)
    ]

    # 创建高斯模型用于生成观测数据
    gaussian_model = GaussianPlumeModel()

    # 生成监测数据
    monitoring_data = []
    for station_id, x, y, z in station_positions:
        # 计算理论浓度
        concentration = gaussian_model.calculate_concentration(
            true_source, x, y, z, met_data
        )

        # 添加噪声 (±10%)
        noise = random.uniform(-0.1, 0.1) * concentration
        observed_concentration = max(0, concentration + noise)

        monitoring_data.append(MonitoringData(
            station_id=station_id,
            x=x, y=y, z=z,
            concentration=observed_concentration,
            timestamp="2024-01-01 12:00:00"
        ))

    return monitoring_data, met_data


def main():
    """主函数 - 演示污染源溯源系统的使用"""
    print("=== 污染物溯源系统演示 ===\n")

    # 创建示例数据
    monitoring_data, met_data = create_sample_data()

    print("1. 加载数据")
    print(f"   监测站数量: {len(monitoring_data)}")
    print(f"   气象条件: 风速{met_data.wind_speed}米/秒, 风向{met_data.wind_direction}度")

    # 显示监测数据
    print("\n   监测数据:")
    for data in monitoring_data:
        print(f"     {data.station_id}: 位置(东西{data.x}米, 南北{data.y}米, 高度{data.z}米), "
              f"浓度{data.concentration:.1f} 微克/立方米")

    # 创建溯源器
    tracker = PollutionSourceTracker()

    # 添加数据
    for data in monitoring_data:
        tracker.add_monitoring_data(data)
    tracker.set_meteorological_data(met_data)

    print("\n2. 执行污染源溯源")
    # 执行溯源
    source = tracker.trace_pollution_source()

    if source is not None:
        print("\n3. 验证溯源结果")
        # 验证结果
        verification_stats = tracker.verify_source(source)

        print("\n4. 正向扩散模拟")
        # 正向模拟验证
        try:
            x_grid, y_grid, conc_grid = tracker.simulate_forward_dispersion(source)
            print(f"   生成扩散网格: {x_grid.shape}")
            print(f"   最大浓度: {np.max(conc_grid):.2f} μg/m³")
            print(f"   平均浓度: {np.mean(conc_grid):.2f} μg/m³")
        except Exception as e:
            print(f"   正向模拟失败: {e}")

        print("\n=== 溯源完成 ===")

        # 返回结果用于进一步分析
        return {
            'source': source,
            'verification': verification_stats,
            'monitoring_data': monitoring_data,
            'meteorological_data': met_data
        }
    else:
        print("\n溯源失败")
        return None


if __name__ == "__main__":
    # 设置随机种子以获得可重复的结果
    random.seed(42)
    np.random.seed(42)

    # 运行主程序
    result = main()
