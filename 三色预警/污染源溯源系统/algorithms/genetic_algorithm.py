"""
遗传算法模块
基于遗传-模式搜索混合算法的污染源溯源
"""

import numpy as np
import random
from typing import List, Tuple, Callable, Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Individual:
    """个体类，表示一个可能的污染源解"""
    x: float  # x坐标
    y: float  # y坐标
    z: float  # z坐标(高度)
    q: float  # 源强
    fitness: float = 0.0  # 适应度
    
    def __post_init__(self):
        """初始化后处理"""
        self.genes: np.ndarray[Any, np.dtype[np.float64]] = np.array([self.x, self.y, self.z, self.q], dtype=np.float64)
    
    def update_genes(self):
        """更新基因数组"""
        self.genes = np.array([self.x, self.y, self.z, self.q], dtype=np.float64)
        
    def from_genes(self, genes: np.ndarray[Any, np.dtype[np.float64]]):
        """从基因数组更新个体"""
        self.x, self.y, self.z, self.q = float(genes[0]), float(genes[1]), float(genes[2]), float(genes[3])
        self.genes = genes.copy()

class GeneticAlgorithm:
    """遗传算法类 - 增强版支持多污染源和自适应参数"""
    
    def __init__(self, 
                 population_size: int = 100,
                 max_generations: int = 400,
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.8,
                 elite_rate: float = 0.1,
                 convergence_threshold: float = 1e-6,
                 adaptive_params: bool = True,
                 multi_source: bool = False,
                 max_sources: int = 3):
        """
        初始化遗传算法
        
        Args:
            population_size: 种群大小
            max_generations: 最大代数
            mutation_rate: 变异率
            crossover_rate: 交叉率
            elite_rate: 精英保留率
            convergence_threshold: 收敛阈值
        """
        self.population_size = population_size
        self.max_generations = max_generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_rate = elite_rate
        self.convergence_threshold = convergence_threshold
        self.adaptive_params = adaptive_params
        self.multi_source = multi_source
        self.max_sources = max_sources
        
        # 自适应参数
        self.initial_mutation_rate = mutation_rate
        self.initial_crossover_rate = crossover_rate
        self.performance_history = []
        self.diversity_history = []
        
        # 算法状态
        self.population: List[Individual] = []
        self.best_individual: Optional[Individual] = None
        self.convergence_history: List[float] = []
        self.generation = 0
        
        # 搜索边界
        self.bounds: Dict[str, Tuple[float, float]] = {}
        
    def initialize_population(self, bounds: Dict[str, Tuple[float, float]]) -> List[Individual]:
        """
        初始化种群
        
        Args:
            bounds: 搜索边界 {'x': (min, max), 'y': (min, max), 'z': (min, max), 'q': (min, max)}
            
        Returns:
            初始化的种群
        """
        self.bounds = bounds
        population = []
        
        for _ in range(self.population_size):
            x = random.uniform(bounds['x'][0], bounds['x'][1])
            y = random.uniform(bounds['y'][0], bounds['y'][1])
            z = random.uniform(bounds['z'][0], bounds['z'][1])
            q = random.uniform(bounds['q'][0], bounds['q'][1])
            
            individual = Individual(x, y, z, q)
            population.append(individual)
        
        self.population = population
        logger.info(f"初始化种群完成，种群大小: {len(population)}")
        return population
    
    def evaluate_fitness(self, fitness_function: Callable[[Individual], float]):
        """
        评估种群适应度
        
        Args:
            fitness_function: 适应度函数
        """
        for individual in self.population:
            individual.fitness = fitness_function(individual)
        
        # 排序种群（适应度从小到大，因为我们要最小化误差）
        self.population.sort(key=lambda x: x.fitness)
        
        # 更新最优个体
        if self.best_individual is None or self.population[0].fitness < self.best_individual.fitness:
            self.best_individual = Individual(
                self.population[0].x,
                self.population[0].y,
                self.population[0].z,
                self.population[0].q
            )
            self.best_individual.fitness = self.population[0].fitness
        
        # 记录收敛历史
        self.convergence_history.append(float(self.population[0].fitness))
    
    def selection(self) -> List[Individual]:
        """
        选择操作 - 锦标赛选择
        
        Returns:
            选择的父代个体
        """
        tournament_size = 3
        selected = []
        
        for _ in range(self.population_size):
            # 锦标赛选择
            tournament_indices = random.choices(range(len(self.population)), k=tournament_size)
            tournament = [self.population[i] for i in tournament_indices]
            winner = min(tournament, key=lambda x: x.fitness)
            selected.append(winner)
        
        return selected
    
    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """
        交叉操作 - 算术交叉
        
        Args:
            parent1: 父代1
            parent2: 父代2
            
        Returns:
            两个子代个体
        """
        if random.random() > self.crossover_rate:
            return parent1, parent2
        
        # 算术交叉
        alpha = random.random()
        
        child1_genes = alpha * parent1.genes + (1 - alpha) * parent2.genes
        child2_genes = (1 - alpha) * parent1.genes + alpha * parent2.genes
        
        # 边界检查
        child1_genes = self._apply_bounds(child1_genes)
        child2_genes = self._apply_bounds(child2_genes)
        
        child1 = Individual(0, 0, 0, 0)
        child1.from_genes(child1_genes)
        
        child2 = Individual(0, 0, 0, 0)
        child2.from_genes(child2_genes)
        
        return child1, child2
    
    def mutation(self, individual: Individual) -> Individual:
        """
        变异操作 - 高斯变异
        
        Args:
            individual: 待变异个体
            
        Returns:
            变异后的个体
        """
        if random.random() > self.mutation_rate:
            return individual
        
        # 高斯变异
        mutated_genes = individual.genes.copy()
        
        for i in range(len(mutated_genes)):
            if random.random() < 0.1:  # 每个基因10%的变异概率
                # 根据搜索范围调整变异强度
                param_names = ['x', 'y', 'z', 'q']
                param_name = param_names[i]
                range_size = self.bounds[param_name][1] - self.bounds[param_name][0]
                mutation_strength = range_size * 0.1  # 10%的范围作为变异强度
                
                mutated_genes[i] += random.gauss(0, mutation_strength)
        
        # 边界检查
        mutated_genes = self._apply_bounds(mutated_genes)
        
        mutated_individual = Individual(0, 0, 0, 0)
        mutated_individual.from_genes(mutated_genes)
        
        return mutated_individual
    
    def adapt_parameters(self, generation: int):
        """
        自适应参数调整
        
        Args:
            generation: 当前代数
        """
        if not self.adaptive_params or generation < 10:
            return
        
        # 计算种群多样性
        diversity = self.get_population_diversity()
        self.diversity_history.append(diversity)
        
        # 计算性能指标
        if len(self.convergence_history) > 5:
            recent_improvement = abs(self.convergence_history[-1] - self.convergence_history[-5])
            self.performance_history.append(recent_improvement)
        
        # 自适应调整策略
        if diversity < 0.1:  # 种群多样性低
            self.mutation_rate = min(0.3, self.mutation_rate * 1.2)
            logger.info(f"种群多样性低，增加变异率至 {self.mutation_rate:.3f}")
        elif diversity > 0.5:  # 种群多样性高
            self.mutation_rate = max(0.01, self.mutation_rate * 0.9)
            logger.info(f"种群多样性高，降低变异率至 {self.mutation_rate:.3f}")
        
        # 根据收敛情况调整交叉率
        if len(self.performance_history) > 5:
            avg_improvement = np.mean(self.performance_history[-5:])
            if avg_improvement < 1e-6:
                self.crossover_rate = min(0.9, self.crossover_rate * 1.1)
    
    def create_multi_source_individual(self, bounds: Dict[str, Tuple[float, float]]) -> Individual:
        """
        创建多污染源个体
        
        Args:
            bounds: 搜索边界
            
        Returns:
            多源个体
        """
        if not self.multi_source:
            return self._create_single_source_individual(bounds)
        
        # 随机确定污染源数量（1-max_sources）
        num_sources = random.randint(1, self.max_sources)
        
        # 创建多个源的参数
        sources = []
        for _ in range(num_sources):
            x = random.uniform(bounds['x'][0], bounds['x'][1])
            y = random.uniform(bounds['y'][0], bounds['y'][1])
            z = random.uniform(bounds['z'][0], bounds['z'][1])
            q = random.uniform(bounds['q'][0], bounds['q'][1])
            sources.append([x, y, z, q])
        
        # 转换为平坑数组
        genes = np.array([param for source in sources for param in source])
        
        individual = Individual(0, 0, 0, 0)
        individual.genes = genes
        individual.num_sources = num_sources
        
        return individual
    
    def _create_single_source_individual(self, bounds: Dict[str, Tuple[float, float]]) -> Individual:
        """创建单一污染源个体"""
        x = random.uniform(bounds['x'][0], bounds['x'][1])
        y = random.uniform(bounds['y'][0], bounds['y'][1])
        z = random.uniform(bounds['z'][0], bounds['z'][1])
        q = random.uniform(bounds['q'][0], bounds['q'][1])
        
        return Individual(x, y, z, q)
        """应用边界约束"""
        param_names = ['x', 'y', 'z', 'q']
        
        for i, param_name in enumerate(param_names):
            min_val, max_val = self.bounds[param_name]
            genes[i] = np.clip(genes[i], min_val, max_val)
        
        return genes
    
    def evolve_generation(self, fitness_function: Callable[[Individual], float]):
        """
        进化一代
        
        Args:
            fitness_function: 适应度函数
        """
        # 评估适应度
        self.evaluate_fitness(fitness_function)
        
        # 精英保留
        elite_count = int(self.population_size * self.elite_rate)
        elite = self.population[:elite_count]
        
        # 选择
        selected = self.selection()
        
        # 生成新一代
        new_population = elite.copy()
        
        while len(new_population) < self.population_size:
            # 随机选择两个父代
            parent1 = random.choice(selected)
            parent2 = random.choice(selected)
            
            # 交叉
            child1, child2 = self.crossover(parent1, parent2)
            
            # 变异
            child1 = self.mutation(child1)
            child2 = self.mutation(child2)
            
            new_population.extend([child1, child2])
        
        # 保持种群大小
        self.population = new_population[:self.population_size]
        self.generation += 1
    
    def check_convergence(self) -> bool:
        """
        检查收敛性
        
        Returns:
            是否收敛
        """
        if len(self.convergence_history) < 10:
            return False
        
        # 检查最近10代的改进
        recent_history = self.convergence_history[-10:]
        improvement = abs(recent_history[0] - recent_history[-1])
        
        return improvement < self.convergence_threshold
    
    def evolve(self, 
               bounds: Dict[str, Tuple[float, float]], 
               fitness_function: Callable[[Individual], float]) -> Individual:
        """
        运行完整的进化过程
        
        Args:
            bounds: 搜索边界
            fitness_function: 适应度函数
            
        Returns:
            最优个体
        """
        logger.info("开始遗传算法进化")
        
        # 初始化种群
        self.initialize_population(bounds)
        
        # 进化循环
        for generation in range(self.max_generations):
            self.evolve_generation(fitness_function)
            
            # 记录进度
            if generation % 10 == 0:
                best_fitness = self.population[0].fitness
                logger.info(f"第 {generation} 代，最优适应度: {best_fitness:.6f}")
            
            # 检查收敛
            if self.check_convergence():
                logger.info(f"算法在第 {generation} 代收敛")
                break
        
        # 最终评估
        self.evaluate_fitness(fitness_function)
        
        if self.best_individual is not None:
            logger.info(f"遗传算法完成，最优适应度: {self.best_individual.fitness:.6f}")
            logger.info(f"最优解: x={self.best_individual.x:.2f}, y={self.best_individual.y:.2f}, "
                       f"z={self.best_individual.z:.2f}, q={self.best_individual.q:.4f}")
            return self.best_individual
        else:
            # 如果没有找到最优个体，返回种群中最好的
            if self.population:
                return self.population[0]
            else:
                # 创建一个默认个体
                return Individual(0.0, 0.0, 10.0, 1.0)
    
    def get_convergence_history(self) -> List[float]:
        """获取收敛历史"""
        return self.convergence_history.copy()
    
    def get_population_diversity(self) -> float:
        """计算种群多样性"""
        if len(self.population) < 2:
            return 0.0
        
        total_distance = 0.0
        count = 0
        
        for i in range(len(self.population)):
            for j in range(i + 1, len(self.population)):
                distance = np.linalg.norm(self.population[i].genes - self.population[j].genes)
                total_distance += float(distance)
                count += 1
        
        return total_distance / count if count > 0 else 0.0
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取算法统计信息"""
        if not self.population:
            return {}
        
        fitness_values = [ind.fitness for ind in self.population]
        
        return {
            'generation': self.generation,
            'population_size': len(self.population),
            'best_fitness': float(self.best_individual.fitness) if self.best_individual else float('inf'),
            'worst_fitness': float(max(fitness_values)),
            'average_fitness': float(np.mean(fitness_values)),
            'fitness_std': float(np.std(fitness_values)),
            'diversity': self.get_population_diversity(),
            'convergence_history': self.convergence_history
        }