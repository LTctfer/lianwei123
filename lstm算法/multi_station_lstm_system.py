"""
多站点多变量LSTM预测系统
基于TensorFlow/Keras实现的空气质量预测系统
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# TensorFlow/Keras imports
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

class MultiStationDataProcessor:
    """多站点数据处理器"""
    
    def __init__(self, data_dir="air_pollutants_prediction_lstm-master/data"):
        """
        初始化数据处理器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.stations = {
            'Bloomsbury': 'Bloomsbury_clean.csv',
            'Marylebone_Road': 'Marylebone_Road_clean.csv', 
            'Eltham': 'Eltham_clean.csv',
            'Harlington': 'Harlington_clean.csv',
            'N_Kensington': 'N_Kensington_clean.csv'
        }
        
        # 污染物和气象变量
        self.pollutants = ['nox', 'no2', 'no', 'o3', 'pm2.5']
        self.meteorological = ['ws', 'wd', 'air_temp']
        self.features = self.pollutants + self.meteorological
        
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.combined_data = None
        self.scaled_data = None
        
    def load_station_data(self, station_name):
        """加载单个站点数据"""
        try:
            file_path = os.path.join(self.data_dir, self.stations[station_name])
            data = pd.read_csv(file_path)
            
            # 选择需要的列
            data = data[['date'] + self.features]
            data['date'] = pd.to_datetime(data['date'])
            data.set_index('date', inplace=True)
            
            # 重命名列，添加站点后缀
            suffix = station_name[0]  # 取首字母作为后缀
            new_columns = [f"{col}_{suffix}" for col in self.features]
            data.columns = new_columns
            
            print(f"✅ 成功加载 {station_name} 数据: {len(data)} 条记录")
            return data
            
        except Exception as e:
            print(f"❌ 加载 {station_name} 数据失败: {e}")
            return None
    
    def load_all_stations(self):
        """加载所有站点数据并合并"""
        print("🔄 开始加载多站点数据...")
        
        station_data_list = []
        
        for station_name in self.stations.keys():
            data = self.load_station_data(station_name)
            if data is not None:
                station_data_list.append(data)
        
        if station_data_list:
            # 按时间索引合并所有站点数据
            self.combined_data = station_data_list[0]
            for data in station_data_list[1:]:
                self.combined_data = self.combined_data.join(data, how='inner')
            
            print(f"✅ 成功合并所有站点数据: {self.combined_data.shape}")
            print(f"   时间范围: {self.combined_data.index.min()} 到 {self.combined_data.index.max()}")
            
            # 处理缺失值
            self.combined_data = self.combined_data.dropna()
            print(f"   清理后数据: {self.combined_data.shape}")
            
            return True
        else:
            print("❌ 没有成功加载任何站点数据")
            return False
    
    def normalize_data(self):
        """数据归一化"""
        if self.combined_data is None:
            print("❌ 请先加载数据")
            return False
        
        print("🔄 开始数据归一化...")
        
        # 使用MinMaxScaler进行归一化
        self.scaled_data = self.scaler.fit_transform(self.combined_data.values)
        
        print(f"✅ 数据归一化完成: {self.scaled_data.shape}")
        return True
    
    def create_sequences(self, window_size=240, prediction_horizon=1):
        """
        创建时间序列窗口
        
        Args:
            window_size: 输入窗口大小（小时）
            prediction_horizon: 预测时间范围（小时）
            
        Returns:
            X, y: 输入序列和目标序列
        """
        if self.scaled_data is None:
            print("❌ 请先进行数据归一化")
            return None, None
        
        print(f"🔄 创建时间序列窗口 (窗口大小: {window_size}, 预测范围: {prediction_horizon})...")
        
        X, y = [], []
        
        for i in range(window_size, len(self.scaled_data) - prediction_horizon + 1):
            # 输入序列：过去window_size小时的所有特征
            X.append(self.scaled_data[i-window_size:i])
            
            # 目标序列：未来prediction_horizon小时的所有特征
            y.append(self.scaled_data[i:i+prediction_horizon])
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"✅ 序列创建完成: X={X.shape}, y={y.shape}")
        return X, y
    
    def split_data(self, X, y, train_ratio=0.8, val_ratio=0.1):
        """划分训练集、验证集和测试集"""
        total_samples = len(X)
        train_size = int(total_samples * train_ratio)
        val_size = int(total_samples * val_ratio)
        
        X_train = X[:train_size]
        y_train = y[:train_size]
        
        X_val = X[train_size:train_size+val_size]
        y_val = y[train_size:train_size+val_size]
        
        X_test = X[train_size+val_size:]
        y_test = y[train_size+val_size:]
        
        print(f"📊 数据划分完成:")
        print(f"   训练集: {X_train.shape[0]} 样本")
        print(f"   验证集: {X_val.shape[0]} 样本") 
        print(f"   测试集: {X_test.shape[0]} 样本")
        
        return (X_train, y_train), (X_val, y_val), (X_test, y_test)
    
    def get_feature_names(self):
        """获取特征名称列表"""
        if self.combined_data is not None:
            return list(self.combined_data.columns)
        return []
    
    def inverse_transform(self, scaled_data):
        """反归一化"""
        return self.scaler.inverse_transform(scaled_data)

class MultiVariateLSTMModel:
    """多变量LSTM模型"""
    
    def __init__(self, input_shape, output_shape, model_config=None):
        """
        初始化LSTM模型
        
        Args:
            input_shape: 输入形状 (time_steps, features)
            output_shape: 输出形状 (prediction_horizon, features)
            model_config: 模型配置字典
        """
        self.input_shape = input_shape
        self.output_shape = output_shape
        
        # 默认配置
        self.config = {
            'lstm_units': [128, 64],
            'dense_units': [64, 32],
            'dropout_rate': 0.2,
            'recurrent_dropout': 0.2,
            'activation': 'tanh',
            'optimizer': 'adam',
            'learning_rate': 0.001,
            'loss': 'mse',
            'metrics': ['mae']
        }
        
        if model_config:
            self.config.update(model_config)
        
        self.model = None
        self.history = None
    
    def build_model(self):
        """构建LSTM模型"""
        print("🔄 构建多变量LSTM模型...")
        
        # 输入层
        inputs = layers.Input(shape=self.input_shape, name='input_sequence')
        
        x = inputs
        
        # LSTM层
        for i, units in enumerate(self.config['lstm_units']):
            return_sequences = (i < len(self.config['lstm_units']) - 1)
            
            x = layers.LSTM(
                units,
                return_sequences=return_sequences,
                dropout=self.config['dropout_rate'],
                recurrent_dropout=self.config['recurrent_dropout'],
                activation=self.config['activation'],
                name=f'lstm_{i+1}'
            )(x)
            
            # 批标准化
            x = layers.BatchNormalization(name=f'batch_norm_lstm_{i+1}')(x)
        
        # 全连接层
        for i, units in enumerate(self.config['dense_units']):
            x = layers.Dense(
                units,
                activation='relu',
                name=f'dense_{i+1}'
            )(x)
            
            x = layers.Dropout(self.config['dropout_rate'], name=f'dropout_{i+1}')(x)
            x = layers.BatchNormalization(name=f'batch_norm_dense_{i+1}')(x)
        
        # 输出层 - 重塑为目标形状
        output_size = self.output_shape[0] * self.output_shape[1]
        x = layers.Dense(output_size, activation='linear', name='output_dense')(x)
        
        # 重塑为目标形状
        outputs = layers.Reshape(self.output_shape, name='output_reshape')(x)
        
        # 创建模型
        self.model = keras.Model(inputs=inputs, outputs=outputs, name='multivariate_lstm')
        
        # 编译模型
        optimizer = keras.optimizers.Adam(learning_rate=self.config['learning_rate'])
        
        self.model.compile(
            optimizer=optimizer,
            loss=self.config['loss'],
            metrics=self.config['metrics']
        )
        
        print(f"✅ 模型构建完成，参数数量: {self.model.count_params():,}")
        return self.model
    
    def train(self, train_data, val_data, epochs=100, batch_size=32, verbose=1):
        """训练模型"""
        if self.model is None:
            self.build_model()
        
        X_train, y_train = train_data
        X_val, y_val = val_data
        
        print(f"🔄 开始训练模型 (epochs={epochs}, batch_size={batch_size})...")
        
        # 回调函数
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=15,
                restore_best_weights=True,
                verbose=1
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=8,
                min_lr=1e-6,
                verbose=1
            ),
            keras.callbacks.ModelCheckpoint(
                'best_multivariate_lstm.h5',
                monitor='val_loss',
                save_best_only=True,
                verbose=1
            )
        ]
        
        # 训练模型
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=verbose
        )
        
        print("✅ 模型训练完成")
        return self.history
    
    def predict(self, X):
        """预测"""
        if self.model is None:
            print("❌ 模型未训练")
            return None
        
        return self.model.predict(X)
    
    def evaluate(self, X_test, y_test):
        """评估模型"""
        if self.model is None:
            print("❌ 模型未训练")
            return None
        
        print("🔄 评估模型性能...")
        
        # 预测
        y_pred = self.model.predict(X_test)
        
        # 计算评估指标
        mse = mean_squared_error(y_test.reshape(-1), y_pred.reshape(-1))
        mae = mean_absolute_error(y_test.reshape(-1), y_pred.reshape(-1))
        rmse = np.sqrt(mse)
        
        # R²分数
        r2 = r2_score(y_test.reshape(-1), y_pred.reshape(-1))
        
        metrics = {
            'MSE': mse,
            'RMSE': rmse,
            'MAE': mae,
            'R2': r2
        }
        
        print("📊 模型评估结果:")
        for metric, value in metrics.items():
            print(f"   {metric}: {value:.6f}")
        
        return metrics, y_pred
    
    def save_model(self, filepath):
        """保存模型"""
        if self.model is None:
            print("❌ 模型未训练")
            return False
        
        self.model.save(filepath)
        print(f"✅ 模型已保存到: {filepath}")
        return True
    
    def load_model(self, filepath):
        """加载模型"""
        try:
            self.model = keras.models.load_model(filepath)
            print(f"✅ 模型已从 {filepath} 加载")
            return True
        except Exception as e:
            print(f"❌ 加载模型失败: {e}")
            return False

class PredictionVisualizer:
    """预测结果可视化器"""

    def __init__(self, feature_names, pollutant_names):
        """
        初始化可视化器

        Args:
            feature_names: 特征名称列表
            pollutant_names: 污染物名称列表
        """
        self.feature_names = feature_names
        self.pollutant_names = pollutant_names

        # 设置绘图样式
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

    def plot_training_history(self, history):
        """绘制训练历史"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # 损失曲线
        axes[0, 0].plot(history.history['loss'], label='训练损失', linewidth=2)
        axes[0, 0].plot(history.history['val_loss'], label='验证损失', linewidth=2)
        axes[0, 0].set_title('模型损失', fontsize=14, fontweight='bold')
        axes[0, 0].set_xlabel('轮次')
        axes[0, 0].set_ylabel('损失')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # MAE曲线
        axes[0, 1].plot(history.history['mae'], label='训练MAE', linewidth=2)
        axes[0, 1].plot(history.history['val_mae'], label='验证MAE', linewidth=2)
        axes[0, 1].set_title('平均绝对误差', fontsize=14, fontweight='bold')
        axes[0, 1].set_xlabel('轮次')
        axes[0, 1].set_ylabel('MAE')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # 学习率曲线（如果有）
        if 'lr' in history.history:
            axes[1, 0].plot(history.history['lr'], linewidth=2, color='orange')
            axes[1, 0].set_title('学习率变化', fontsize=14, fontweight='bold')
            axes[1, 0].set_xlabel('轮次')
            axes[1, 0].set_ylabel('学习率')
            axes[1, 0].set_yscale('log')
            axes[1, 0].grid(True, alpha=0.3)

        # 训练时间分析
        epochs = len(history.history['loss'])
        axes[1, 1].bar(['训练轮次'], [epochs], color='skyblue', alpha=0.7)
        axes[1, 1].set_title('训练统计', fontsize=14, fontweight='bold')
        axes[1, 1].set_ylabel('轮次数')

        plt.tight_layout()
        plt.show()

    def plot_predictions_comparison(self, y_true, y_pred, scaler, station_names,
                                  pollutant_indices, time_steps=None):
        """
        绘制预测结果对比图

        Args:
            y_true: 真实值
            y_pred: 预测值
            scaler: 数据缩放器
            station_names: 站点名称列表
            pollutant_indices: 污染物在特征中的索引
            time_steps: 时间步长（可选）
        """
        # 反归一化
        y_true_orig = scaler.inverse_transform(y_true.reshape(-1, y_true.shape[-1]))
        y_pred_orig = scaler.inverse_transform(y_pred.reshape(-1, y_pred.shape[-1]))

        # 重新整形
        y_true_orig = y_true_orig.reshape(y_true.shape)
        y_pred_orig = y_pred_orig.reshape(y_pred.shape)

        # 为每个污染物创建对比图
        n_pollutants = len(pollutant_indices)
        fig, axes = plt.subplots(n_pollutants, 1, figsize=(15, 4*n_pollutants))

        if n_pollutants == 1:
            axes = [axes]

        for i, pollutant_idx in enumerate(pollutant_indices):
            # 选择第一个预测时间步的数据进行可视化
            true_values = y_true_orig[:, 0, pollutant_idx]
            pred_values = y_pred_orig[:, 0, pollutant_idx]

            # 创建时间轴
            if time_steps is not None:
                x_axis = time_steps[:len(true_values)]
            else:
                x_axis = range(len(true_values))

            axes[i].plot(x_axis, true_values, label='真实值', linewidth=2, alpha=0.8)
            axes[i].plot(x_axis, pred_values, label='预测值', linewidth=2, alpha=0.8)

            # 计算误差指标
            mse = mean_squared_error(true_values, pred_values)
            mae = mean_absolute_error(true_values, pred_values)
            r2 = r2_score(true_values, pred_values)

            pollutant_name = self.feature_names[pollutant_idx].split('_')[0]
            axes[i].set_title(f'{pollutant_name.upper()} 预测对比 (MSE: {mse:.4f}, MAE: {mae:.4f}, R²: {r2:.4f})',
                            fontsize=12, fontweight='bold')
            axes[i].set_xlabel('时间')
            axes[i].set_ylabel('浓度')
            axes[i].legend()
            axes[i].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

    def plot_correlation_matrix(self, data, title="特征相关性矩阵"):
        """绘制特征相关性矩阵"""
        plt.figure(figsize=(12, 10))

        # 计算相关性矩阵
        corr_matrix = np.corrcoef(data.T)

        # 创建热力图
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(corr_matrix,
                   mask=mask,
                   annot=True,
                   cmap='coolwarm',
                   center=0,
                   square=True,
                   fmt='.2f',
                   cbar_kws={"shrink": .8})

        plt.title(title, fontsize=16, fontweight='bold')
        plt.xticks(range(len(self.feature_names)), self.feature_names, rotation=45)
        plt.yticks(range(len(self.feature_names)), self.feature_names, rotation=0)
        plt.tight_layout()
        plt.show()

    def plot_feature_importance(self, model, feature_names):
        """绘制特征重要性（基于权重分析）"""
        # 这是一个简化的特征重要性分析
        # 在实际应用中，可以使用更复杂的方法如SHAP值

        try:
            # 获取第一个LSTM层的权重
            lstm_weights = model.layers[1].get_weights()[0]  # 输入权重

            # 计算每个特征的平均权重绝对值
            feature_importance = np.mean(np.abs(lstm_weights), axis=1)

            # 创建特征重要性图
            plt.figure(figsize=(12, 8))

            indices = np.argsort(feature_importance)[::-1]

            plt.bar(range(len(feature_importance)),
                   feature_importance[indices],
                   color='skyblue',
                   alpha=0.7)

            plt.title('特征重要性分析', fontsize=16, fontweight='bold')
            plt.xlabel('特征')
            plt.ylabel('重要性分数')
            plt.xticks(range(len(feature_importance)),
                      [feature_names[i] for i in indices],
                      rotation=45)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()

        except Exception as e:
            print(f"⚠️ 特征重要性分析失败: {e}")

    def plot_prediction_intervals(self, y_true, y_pred, confidence_level=0.95):
        """绘制预测区间"""
        # 计算预测误差
        errors = np.abs(y_true - y_pred)

        # 计算置信区间
        confidence_interval = np.percentile(errors, confidence_level * 100)

        plt.figure(figsize=(15, 8))

        # 选择前100个样本进行可视化
        n_samples = min(100, len(y_true))
        x_axis = range(n_samples)

        plt.plot(x_axis, y_true[:n_samples], 'o-', label='真实值', alpha=0.7)
        plt.plot(x_axis, y_pred[:n_samples], 's-', label='预测值', alpha=0.7)

        # 添加置信区间
        plt.fill_between(x_axis,
                        y_pred[:n_samples] - confidence_interval,
                        y_pred[:n_samples] + confidence_interval,
                        alpha=0.2, label=f'{confidence_level*100}% 置信区间')

        plt.title(f'预测结果与 {confidence_level*100}% 置信区间', fontsize=14, fontweight='bold')
        plt.xlabel('样本')
        plt.ylabel('值')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    def create_dashboard(self, metrics, y_true, y_pred, history=None):
        """创建综合仪表板"""
        fig = plt.figure(figsize=(20, 12))

        # 创建网格布局
        gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)

        # 1. 模型性能指标
        ax1 = fig.add_subplot(gs[0, 0])
        metric_names = list(metrics.keys())
        metric_values = list(metrics.values())

        bars = ax1.bar(metric_names, metric_values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
        ax1.set_title('模型性能指标', fontweight='bold')
        ax1.set_ylabel('值')

        # 在柱状图上添加数值标签
        for bar, value in zip(bars, metric_values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.4f}', ha='center', va='bottom')

        # 2. 预测vs真实值散点图
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.scatter(y_true.flatten(), y_pred.flatten(), alpha=0.5, s=1)

        # 添加完美预测线
        min_val = min(y_true.min(), y_pred.min())
        max_val = max(y_true.max(), y_pred.max())
        ax2.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2)

        ax2.set_xlabel('真实值')
        ax2.set_ylabel('预测值')
        ax2.set_title('预测值 vs 真实值', fontweight='bold')
        ax2.grid(True, alpha=0.3)

        # 3. 残差分布
        ax3 = fig.add_subplot(gs[0, 2])
        residuals = (y_pred - y_true).flatten()
        ax3.hist(residuals, bins=50, alpha=0.7, color='lightblue', edgecolor='black')
        ax3.set_xlabel('残差')
        ax3.set_ylabel('频次')
        ax3.set_title('残差分布', fontweight='bold')
        ax3.grid(True, alpha=0.3)

        # 4. 训练历史（如果提供）
        if history is not None:
            ax4 = fig.add_subplot(gs[0, 3])
            ax4.plot(history.history['loss'], label='训练损失')
            ax4.plot(history.history['val_loss'], label='验证损失')
            ax4.set_xlabel('轮次')
            ax4.set_ylabel('损失')
            ax4.set_title('训练历史', fontweight='bold')
            ax4.legend()
            ax4.grid(True, alpha=0.3)

        # 5-8. 时间序列预测对比（占据下面两行）
        ax5 = fig.add_subplot(gs[1:, :])

        # 选择前200个样本进行可视化
        n_samples = min(200, len(y_true))
        x_axis = range(n_samples)

        ax5.plot(x_axis, y_true[:n_samples, 0, 0], label='真实值', linewidth=2, alpha=0.8)
        ax5.plot(x_axis, y_pred[:n_samples, 0, 0], label='预测值', linewidth=2, alpha=0.8)

        ax5.set_xlabel('时间步')
        ax5.set_ylabel('值')
        ax5.set_title('时间序列预测对比', fontsize=16, fontweight='bold')
        ax5.legend()
        ax5.grid(True, alpha=0.3)

        plt.suptitle('多站点多变量LSTM预测系统 - 综合仪表板', fontsize=20, fontweight='bold')
        plt.show()
