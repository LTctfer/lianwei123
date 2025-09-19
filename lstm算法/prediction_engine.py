"""
LSTM多站点多变量预测引擎
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import joblib
import os
from multi_station_lstm_system import MultiStationDataProcessor, MultiVariateLSTMModel, PredictionVisualizer

class LSTMPredictionEngine:
    """LSTM预测引擎"""
    
    def __init__(self, data_dir="air_pollutants_prediction_lstm-master/data"):
        """
        初始化预测引擎
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.data_processor = MultiStationDataProcessor(data_dir)
        self.model = None
        self.visualizer = None
        
        # 预测配置
        self.config = {
            'window_size': 240,  # 10天的历史数据
            'prediction_horizon': 24,  # 预测未来24小时
            'train_ratio': 0.8,
            'val_ratio': 0.1,
            'epochs': 100,
            'batch_size': 32
        }
        
        # 数据存储
        self.train_data = None
        self.val_data = None
        self.test_data = None
        self.feature_names = []
        
    def load_and_prepare_data(self):
        """加载和准备数据"""
        print("🚀 开始数据加载和预处理...")
        
        # 加载所有站点数据
        if not self.data_processor.load_all_stations():
            return False
        
        # 数据归一化
        if not self.data_processor.normalize_data():
            return False
        
        # 获取特征名称
        self.feature_names = self.data_processor.get_feature_names()
        print(f"📋 特征列表: {self.feature_names}")
        
        # 创建时间序列
        X, y = self.data_processor.create_sequences(
            window_size=self.config['window_size'],
            prediction_horizon=self.config['prediction_horizon']
        )
        
        if X is None or y is None:
            return False
        
        # 划分数据集
        self.train_data, self.val_data, self.test_data = self.data_processor.split_data(
            X, y, 
            train_ratio=self.config['train_ratio'],
            val_ratio=self.config['val_ratio']
        )
        
        # 初始化可视化器
        pollutant_names = ['nox', 'no2', 'no', 'o3', 'pm2.5']
        self.visualizer = PredictionVisualizer(self.feature_names, pollutant_names)
        
        print("✅ 数据准备完成")
        return True
    
    def build_and_train_model(self, model_config=None):
        """构建和训练模型"""
        if self.train_data is None:
            print("❌ 请先加载数据")
            return False
        
        print("🔄 开始构建和训练模型...")
        
        # 获取输入输出形状
        X_train, y_train = self.train_data
        input_shape = X_train.shape[1:]  # (time_steps, features)
        output_shape = y_train.shape[1:]  # (prediction_horizon, features)
        
        print(f"📊 模型配置:")
        print(f"   输入形状: {input_shape}")
        print(f"   输出形状: {output_shape}")
        
        # 创建模型
        self.model = MultiVariateLSTMModel(input_shape, output_shape, model_config)
        
        # 训练模型
        history = self.model.train(
            self.train_data,
            self.val_data,
            epochs=self.config['epochs'],
            batch_size=self.config['batch_size']
        )
        
        # 可视化训练历史
        if self.visualizer and history:
            self.visualizer.plot_training_history(history)
        
        print("✅ 模型训练完成")
        return True
    
    def evaluate_model(self):
        """评估模型性能"""
        if self.model is None or self.test_data is None:
            print("❌ 请先训练模型和准备测试数据")
            return None
        
        print("🔄 开始模型评估...")
        
        X_test, y_test = self.test_data
        
        # 评估模型
        metrics, y_pred = self.model.evaluate(X_test, y_test)
        
        if self.visualizer:
            # 绘制预测对比图
            pollutant_indices = [0, 1, 2, 3, 4]  # nox, no2, no, o3, pm2.5的索引
            station_names = ['B', 'M', 'E', 'H', 'N']  # 站点简称
            
            self.visualizer.plot_predictions_comparison(
                y_test, y_pred, 
                self.data_processor.scaler,
                station_names,
                pollutant_indices
            )
            
            # 创建综合仪表板
            self.visualizer.create_dashboard(metrics, y_test, y_pred, self.model.history)
        
        return metrics, y_pred
    
    def predict_future(self, hours=24):
        """预测未来指定小时的数据"""
        if self.model is None:
            print("❌ 请先训练模型")
            return None
        
        print(f"🔮 开始预测未来 {hours} 小时的数据...")
        
        # 使用最新的数据作为输入
        latest_data = self.data_processor.scaled_data[-self.config['window_size']:]
        latest_data = latest_data.reshape(1, *latest_data.shape)
        
        predictions = []
        current_input = latest_data.copy()
        
        # 逐步预测
        for i in range(0, hours, self.config['prediction_horizon']):
            # 预测下一个时间段
            pred = self.model.predict(current_input)
            predictions.append(pred[0])
            
            # 更新输入（滑动窗口）
            # 将预测结果添加到输入序列的末尾，移除最早的数据
            pred_reshaped = pred.reshape(pred.shape[1], pred.shape[2])
            current_input = np.concatenate([
                current_input[:, self.config['prediction_horizon']:, :],
                pred_reshaped.reshape(1, pred.shape[1], pred.shape[2])
            ], axis=1)
        
        # 合并所有预测结果
        all_predictions = np.concatenate(predictions, axis=0)
        
        # 只取需要的小时数
        all_predictions = all_predictions[:hours]
        
        # 反归一化
        original_predictions = self.data_processor.inverse_transform(
            all_predictions.reshape(-1, all_predictions.shape[-1])
        ).reshape(all_predictions.shape)
        
        # 创建预测结果DataFrame
        prediction_df = self._create_prediction_dataframe(original_predictions, hours)
        
        print(f"✅ 预测完成，生成了 {len(prediction_df)} 小时的预测数据")
        return prediction_df, original_predictions
    
    def _create_prediction_dataframe(self, predictions, hours):
        """创建预测结果DataFrame"""
        # 生成未来时间戳
        start_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        time_index = [start_time + timedelta(hours=i) for i in range(hours)]
        
        # 创建DataFrame
        data_dict = {}
        for i, feature_name in enumerate(self.feature_names):
            data_dict[feature_name] = predictions[:, i]
        
        df = pd.DataFrame(data_dict, index=time_index)
        return df
    
    def save_predictions(self, prediction_df, filename=None):
        """保存预测结果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lstm_predictions_{timestamp}.csv"
        
        prediction_df.to_csv(filename)
        print(f"✅ 预测结果已保存到: {filename}")
        return filename
    
    def save_model_and_scaler(self, model_path=None, scaler_path=None):
        """保存模型和缩放器"""
        if model_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_path = f"lstm_model_{timestamp}.h5"
        
        if scaler_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            scaler_path = f"scaler_{timestamp}.pkl"
        
        # 保存模型
        if self.model:
            self.model.save_model(model_path)
        
        # 保存缩放器
        if self.data_processor.scaler:
            joblib.dump(self.data_processor.scaler, scaler_path)
            print(f"✅ 缩放器已保存到: {scaler_path}")
        
        return model_path, scaler_path
    
    def load_model_and_scaler(self, model_path, scaler_path):
        """加载模型和缩放器"""
        try:
            # 加载缩放器
            self.data_processor.scaler = joblib.load(scaler_path)
            print(f"✅ 缩放器已从 {scaler_path} 加载")
            
            # 加载模型（需要先知道模型结构）
            # 这里需要根据实际情况调整
            print(f"⚠️ 模型加载需要先构建模型结构")
            
            return True
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            return False
    
    def get_model_summary(self):
        """获取模型摘要"""
        if self.model and self.model.model:
            return self.model.model.summary()
        else:
            print("❌ 模型未构建")
            return None
    
    def analyze_feature_correlation(self):
        """分析特征相关性"""
        if self.data_processor.combined_data is not None and self.visualizer:
            self.visualizer.plot_correlation_matrix(
                self.data_processor.combined_data.values,
                "多站点特征相关性矩阵"
            )
        else:
            print("❌ 数据未加载或可视化器未初始化")
    
    def analyze_feature_importance(self):
        """分析特征重要性"""
        if self.model and self.model.model and self.visualizer:
            self.visualizer.plot_feature_importance(
                self.model.model,
                self.feature_names
            )
        else:
            print("❌ 模型未训练或可视化器未初始化")

def run_complete_pipeline(data_dir="air_pollutants_prediction_lstm-master/data"):
    """运行完整的预测流程"""
    print("🚀 启动LSTM多站点多变量预测系统")
    print("=" * 60)
    
    # 创建预测引擎
    engine = LSTMPredictionEngine(data_dir)
    
    # 1. 数据加载和预处理
    if not engine.load_and_prepare_data():
        print("❌ 数据加载失败")
        return None
    
    # 2. 分析数据特征
    print("\n📊 数据特征分析...")
    engine.analyze_feature_correlation()
    
    # 3. 构建和训练模型
    model_config = {
        'lstm_units': [128, 64],
        'dense_units': [64, 32],
        'dropout_rate': 0.3,
        'learning_rate': 0.001
    }
    
    if not engine.build_and_train_model(model_config):
        print("❌ 模型训练失败")
        return None
    
    # 4. 模型评估
    print("\n📈 模型评估...")
    metrics, predictions = engine.evaluate_model()
    
    # 5. 特征重要性分析
    print("\n🔍 特征重要性分析...")
    engine.analyze_feature_importance()
    
    # 6. 未来预测
    print("\n🔮 未来预测...")
    prediction_df, pred_array = engine.predict_future(hours=72)
    
    # 7. 保存结果
    print("\n💾 保存结果...")
    pred_file = engine.save_predictions(prediction_df)
    model_file, scaler_file = engine.save_model_and_scaler()
    
    print("\n🎉 预测流程完成！")
    print(f"📁 预测结果: {pred_file}")
    print(f"🤖 模型文件: {model_file}")
    print(f"📏 缩放器文件: {scaler_file}")
    
    return engine, prediction_df, metrics

if __name__ == "__main__":
    # 运行完整流程
    engine, predictions, metrics = run_complete_pipeline()
    
    if engine:
        print("\n📋 最终结果摘要:")
        print(f"   模型性能: R² = {metrics['R2']:.4f}")
        print(f"   预测数据: {len(predictions)} 小时")
        print(f"   特征数量: {len(engine.feature_names)}")
        print(f"   站点数量: 5个")
