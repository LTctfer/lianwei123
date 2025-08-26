#模式搜索算法
import numpy as np
from typing import Callable, Tuple, List
import logging

logger = logging.getLogger(__name__)

class PatternSearch:
    """模式搜索算法类 - 增强版支持自适应步长和并行搜索"""
    
    def __init__(self,
                 initial_step_size: float = 10.0,
                 step_reduction_factor: float = 0.5,
                 min_step_size: float = 0.1,
                 max_iterations: int = 100,
                 adaptive_step: bool = True,
                 parallel_search: bool = True,
                 tolerance: float = 1e-6):
        """
        初始化模式搜索算法
        
        Args:
            initial_step_size: 初始步长
            step_reduction_factor: 步长缩减因子
            min_step_size: 最小步长
            max_iterations: 最大迭代次数
        """
        self.initial_step_size = initial_step_size
        self.step_reduction_factor = step_reduction_factor
        self.min_step_size = min_step_size
        self.max_iterations = max_iterations
        self.adaptive_step = adaptive_step
        self.parallel_search = parallel_search
        self.tolerance = tolerance
        
        # 自适应参数
        self.success_count = 0
        self.failure_count = 0
        self.step_expansion_factor = 2.0
        self.performance_history = []
        
        # 搜索边界
        self.bounds = {
            'x': (-1000, 1000),
            'y': (-1000, 1000),
            'z': (0, 100),
            'q': (0.1, 100)
        }
        
        # 搜索历史
        self.search_history: List[Tuple[float, float, float, float, float]] = []
        
    def set_bounds(self, bounds: dict):
        """设置搜索边界"""
        self.bounds.update(bounds)
    
    def _apply_bounds(self, point: np.ndarray) -> np.ndarray:
        """应用边界约束"""
        bounded_point = point.copy()
        
        bounded_point[0] = np.clip(bounded_point[0], *self.bounds['x'])  # x
        bounded_point[1] = np.clip(bounded_point[1], *self.bounds['y'])  # y
        bounded_point[2] = np.clip(bounded_point[2], *self.bounds['z'])  # z
        bounded_point[3] = np.clip(bounded_point[3], *self.bounds['q'])  # q
        
        return bounded_point
    
    def adaptive_step_adjustment(self, improved: bool, step_size: float) -> float:
        """
        自适应步长调整
        
        Args:
            improved: 是否找到更好的解
            step_size: 当前步长
            
        Returns:
            调整后的步长
        """
        if not self.adaptive_step:
            return step_size * self.step_reduction_factor if not improved else step_size
        
        if improved:
            self.success_count += 1
            self.failure_count = 0
            
            # 连续成功时扩大步长
            if self.success_count >= 3:
                new_step_size = min(step_size * self.step_expansion_factor, 
                                   self.initial_step_size * 2)
                self.success_count = 0
                logger.debug(f"连续成功，扩大步长至 {new_step_size:.4f}")
                return new_step_size
        else:
            self.failure_count += 1
            self.success_count = 0
            
            # 连续失败时加速缩小步长
            if self.failure_count >= 2:
                reduction_factor = self.step_reduction_factor ** (self.failure_count - 1)
                new_step_size = step_size * reduction_factor
                logger.debug(f"连续失败，加速缩小步长至 {new_step_size:.4f}")
                return new_step_size
            else:
                return step_size * self.step_reduction_factor
        
        return step_size
    
    def parallel_exploratory_search(self, 
                                  current_point: np.ndarray,
                                  step_size: float,
                                  objective_function: Callable) -> Tuple[np.ndarray, float, bool]:
        """
        并行探索性搜索（模拟并行，实际为批量处理）
        
        Args:
            current_point: 当前点
            step_size: 步长
            objective_function: 目标函数
            
        Returns:
            最佳点, 最佳函数值, 是否找到更好的点
        """
        if not self.parallel_search:
            return self.exploratory_search(current_point, step_size, objective_function)
        
        current_value = objective_function(*current_point)
        best_point = current_point.copy()
        best_value = current_value
        improved = False
        
        # 获取搜索方向
        directions = self._generate_search_directions()
        
        # 批量生成候选点
        candidate_points = []
        for direction in directions:
            new_point = current_point + step_size * direction
            new_point = self._apply_bounds(new_point)
            candidate_points.append(new_point)
        
        # 批量评估（模拟并行）
        for new_point in candidate_points:
            try:
                new_value = objective_function(*new_point)
                
                if new_value < best_value:
                    best_point = new_point.copy()
                    best_value = new_value
                    improved = True
                    
            except Exception as e:
                logger.warning(f"目标函数评估失败: {e}")
                continue
        
        return best_point, best_value, improved
    
    def check_convergence(self, value_history: List[float]) -> bool:
        """
        检查收敛性
        
        Args:
            value_history: 目标函数值历史
            
        Returns:
            是否收敛
        """
        if len(value_history) < 10:
            return False
        
        # 检查最近10次迭代的改进
        recent_values = value_history[-10:]
        improvement = abs(recent_values[0] - recent_values[-1])
        
        return improvement < self.tolerance
        """生成搜索方向"""
        # 坐标轴方向 + 对角线方向
        directions = np.array([
            [1, 0, 0, 0],   # +x方向
            [-1, 0, 0, 0],  # -x方向
            [0, 1, 0, 0],   # +y方向
            [0, -1, 0, 0],  # -y方向
            [0, 0, 1, 0],   # +z方向
            [0, 0, -1, 0],  # -z方向
            [0, 0, 0, 1],   # +q方向
            [0, 0, 0, -1],  # -q方向
            # 对角线方向
            [1, 1, 0, 0],
            [1, -1, 0, 0],
            [-1, 1, 0, 0],
            [-1, -1, 0, 0],
            [1, 0, 1, 0],
            [1, 0, -1, 0],
            [-1, 0, 1, 0],
            [-1, 0, -1, 0]
        ])
        
        return directions
    
    def exploratory_search(self, 
                          current_point: np.ndarray,
                          step_size: float,
                          objective_function: Callable) -> Tuple[np.ndarray, float, bool]:
        """
        探索性搜索
        
        Args:
            current_point: 当前点
            step_size: 步长
            objective_function: 目标函数
            
        Returns:
            最佳点, 最佳函数值, 是否找到更好的点
        """
        current_value = objective_function(*current_point)
        best_point = current_point.copy()
        best_value = current_value
        improved = False
        
        # 获取搜索方向
        directions = self._generate_search_directions()
        
        for direction in directions:
            # 计算新点
            new_point = current_point + step_size * direction
            
            # 应用边界约束
            new_point = self._apply_bounds(new_point)
            
            # 评估新点
            try:
                new_value = objective_function(*new_point)
                
                # 如果找到更好的点
                if new_value < best_value:
                    best_point = new_point.copy()
                    best_value = new_value
                    improved = True
                    
            except Exception as e:
                logger.warning(f"目标函数评估失败: {e}")
                continue
        
        return best_point, best_value, improved
    
    def pattern_move(self,
                    base_point: np.ndarray,
                    current_point: np.ndarray) -> np.ndarray:
        """
        模式移动
        
        Args:
            base_point: 基点
            current_point: 当前点
            
        Returns:
            模式移动后的点
        """
        # 计算移动方向
        direction = current_point - base_point
        
        # 模式移动
        pattern_point = current_point + direction
        
        # 应用边界约束
        pattern_point = self._apply_bounds(pattern_point)
        
        return pattern_point
    
    def optimize(self,
                initial_point: np.ndarray,
                objective_function: Callable) -> Tuple[np.ndarray, float]:
        """
        模式搜索优化
        
        Args:
            initial_point: 初始点 [x, y, z, q]
            objective_function: 目标函数
            
        Returns:
            最优点, 最优函数值
        """
        logger.info("开始模式搜索优化")
        
        # 初始化
        base_point = initial_point.copy()
        current_point = initial_point.copy()
        step_size = self.initial_step_size
        
        current_value = objective_function(*current_point)
        
        # 记录搜索历史
        self.search_history = [(current_point[0], current_point[1], 
                               current_point[2], current_point[3], current_value)]
        
        for iteration in range(self.max_iterations):
            # 探索性搜索
            new_point, new_value, improved = self.exploratory_search(
                current_point, step_size, objective_function
            )
            
            if improved:
                # 如果找到更好的点，进行模式移动
                base_point = current_point.copy()
                current_point = new_point.copy()
                current_value = new_value
                
                # 尝试模式移动
                pattern_point = self.pattern_move(base_point, current_point)
                
                try:
                    pattern_value = objective_function(*pattern_point)
                    
                    if pattern_value < current_value:
                        current_point = pattern_point.copy()
                        current_value = pattern_value
                        
                except Exception as e:
                    logger.warning(f"模式移动评估失败: {e}")
                
                # 记录搜索历史
                self.search_history.append((current_point[0], current_point[1],
                                          current_point[2], current_point[3], current_value))
                
                logger.debug(f"第{iteration}次迭代找到更好解: {current_value:.6f}")
                
            else:
                # 如果没有改进，缩小步长
                step_size *= self.step_reduction_factor
                
                if step_size < self.min_step_size:
                    logger.info(f"步长小于最小值，算法收敛于第{iteration}次迭代")
                    break
                    
                logger.debug(f"第{iteration}次迭代缩小步长至: {step_size:.4f}")
        
        logger.info(f"模式搜索完成，最优值: {current_value:.6f}")
        logger.info(f"最优解: x={current_point[0]:.2f}, y={current_point[1]:.2f}, "
                   f"z={current_point[2]:.2f}, q={current_point[3]:.2f}")
        
        return current_point, current_value
    
    def get_search_path(self) -> List[Tuple[float, float, float, float, float]]:
        """获取搜索路径"""
        return self.search_history
    
    def get_statistics(self) -> dict:
        """获取算法统计信息"""
        if not self.search_history:
            return {}
            
        initial_value = self.search_history[0][4]
        final_value = self.search_history[-1][4]
        
        return {
            'iterations': len(self.search_history),
            'initial_value': initial_value,
            'final_value': final_value,
            'improvement': initial_value - final_value,
            'improvement_ratio': (initial_value - final_value) / initial_value if initial_value != 0 else 0,
            'search_path': self.search_history
        }