"""
LSTM多站点多变量预测系统演示脚本
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prediction_engine import LSTMPredictionEngine, run_complete_pipeline

def demo_quick_test():
    """快速测试演示"""
    print("🚀 LSTM多站点多变量预测系统 - 快速测试")
    print("=" * 60)
    
    # 检查数据文件是否存在
    data_dir = "air_pollutants_prediction_lstm-master/data"
    required_files = [
        "Bloomsbury_clean.csv",
        "Marylebone_Road_clean.csv", 
        "Eltham_clean.csv",
        "Harlington_clean.csv",
        "N_Kensington_clean.csv"
    ]
    
    print("🔍 检查数据文件...")
    missing_files = []
    for file in required_files:
        file_path = os.path.join(data_dir, file)
        if os.path.exists(file_path):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ 缺少数据文件: {missing_files}")
        print("请确保数据文件在正确的目录中")
        return False
    
    print("\n✅ 所有数据文件检查完成")
    
    # 创建预测引擎
    print("\n🔄 初始化预测引擎...")
    engine = LSTMPredictionEngine(data_dir)
    
    # 设置快速测试配置
    engine.config.update({
        'window_size': 48,  # 2天历史数据
        'prediction_horizon': 12,  # 预测12小时
        'epochs': 5,  # 快速训练
        'batch_size': 32
    })
    
    try:
        # 1. 数据加载
        print("📊 加载和预处理数据...")
        if not engine.load_and_prepare_data():
            print("❌ 数据加载失败")
            return False
        
        print(f"   数据形状: {engine.data_processor.combined_data.shape}")
        print(f"   特征数量: {len(engine.feature_names)}")
        print(f"   时间范围: {engine.data_processor.combined_data.index.min()} 到 {engine.data_processor.combined_data.index.max()}")
        
        # 2. 模型构建和训练
        print("\n🤖 构建和训练模型...")
        model_config = {
            'lstm_units': [64, 32],
            'dense_units': [32, 16],
            'dropout_rate': 0.2,
            'learning_rate': 0.001
        }
        
        if not engine.build_and_train_model(model_config):
            print("❌ 模型训练失败")
            return False
        
        # 3. 模型评估
        print("\n📈 评估模型性能...")
        metrics, predictions = engine.evaluate_model()
        
        print("   模型性能指标:")
        for metric, value in metrics.items():
            print(f"     {metric}: {value:.6f}")
        
        # 4. 未来预测
        print("\n🔮 生成未来预测...")
        prediction_df, pred_array = engine.predict_future(hours=24)
        
        print(f"   预测数据形状: {prediction_df.shape}")
        print(f"   预测时间范围: {prediction_df.index.min()} 到 {prediction_df.index.max()}")
        
        # 5. 显示预测结果样本
        print("\n📋 预测结果样本:")
        print(prediction_df.head(10))
        
        # 6. 保存结果
        print("\n💾 保存结果...")
        pred_file = engine.save_predictions(prediction_df, "demo_predictions.csv")
        model_file, scaler_file = engine.save_model_and_scaler("demo_model.h5", "demo_scaler.pkl")
        
        print(f"   预测结果: {pred_file}")
        print(f"   模型文件: {model_file}")
        print(f"   缩放器文件: {scaler_file}")
        
        print("\n🎉 快速测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_visualization():
    """可视化演示"""
    print("\n📊 可视化演示")
    print("=" * 40)
    
    try:
        # 创建一些示例数据进行可视化
        dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
        
        # 模拟多站点数据
        stations = ['B', 'M', 'E', 'H', 'N']
        pollutants = ['nox', 'no2', 'no', 'o3', 'pm2.5']
        
        data = {}
        for station in stations:
            for pollutant in pollutants:
                # 生成带有趋势和噪声的模拟数据
                trend = np.linspace(10, 50, 100)
                noise = np.random.normal(0, 5, 100)
                seasonal = 10 * np.sin(2 * np.pi * np.arange(100) / 24)  # 日周期
                
                data[f"{pollutant}_{station}"] = trend + noise + seasonal
        
        df = pd.DataFrame(data, index=dates)
        
        # 创建可视化
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes = axes.flatten()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        for i, pollutant in enumerate(pollutants):
            ax = axes[i]
            
            for j, station in enumerate(stations):
                column = f"{pollutant}_{station}"
                if column in df.columns:
                    ax.plot(df.index, df[column], 
                           label=f"站点 {station}", 
                           color=colors[j], 
                           alpha=0.7,
                           linewidth=1.5)
            
            ax.set_title(f"{pollutant.upper()} 浓度变化", fontsize=12, fontweight='bold')
            ax.set_xlabel("时间")
            ax.set_ylabel("浓度 (μg/m³)")
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        # 隐藏多余的子图
        axes[5].axis('off')
        
        plt.suptitle("多站点多变量空气质量数据可视化", fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.show()
        
        print("✅ 可视化演示完成")
        
        # 相关性分析
        print("\n🔍 相关性分析...")
        corr_matrix = df.corr()
        
        plt.figure(figsize=(12, 10))
        import seaborn as sns
        
        # 创建热力图
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(corr_matrix, 
                   mask=mask,
                   annot=False, 
                   cmap='coolwarm', 
                   center=0,
                   square=True,
                   cbar_kws={"shrink": .8})
        
        plt.title("多站点特征相关性矩阵", fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.show()
        
        print("✅ 相关性分析完成")
        
    except Exception as e:
        print(f"❌ 可视化演示失败: {e}")

def demo_model_comparison():
    """模型对比演示"""
    print("\n🏆 模型对比演示")
    print("=" * 40)
    
    # 模拟不同模型的性能指标
    models = ['基础LSTM', '多层LSTM', '双向LSTM', '注意力LSTM', '集成模型']
    metrics = {
        'R²': [0.85, 0.88, 0.91, 0.93, 0.95],
        'RMSE': [2.5, 2.2, 1.9, 1.7, 1.5],
        'MAE': [1.8, 1.6, 1.4, 1.2, 1.1],
        'MAPE': [15.2, 13.8, 12.1, 10.5, 9.2]
    }
    
    # 创建对比图
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    axes = axes.flatten()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57']
    
    for i, (metric, values) in enumerate(metrics.items()):
        ax = axes[i]
        
        bars = ax.bar(models, values, color=colors, alpha=0.8)
        ax.set_title(f"{metric} 对比", fontsize=12, fontweight='bold')
        ax.set_ylabel(metric)
        
        # 在柱状图上添加数值标签
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                   f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
        
        ax.grid(True, alpha=0.3, axis='y')
        
        # 旋转x轴标签
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    plt.suptitle("LSTM模型性能对比", fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.show()
    
    print("✅ 模型对比演示完成")

def demo_prediction_analysis():
    """预测分析演示"""
    print("\n🔮 预测分析演示")
    print("=" * 40)
    
    # 生成模拟的预测数据
    future_dates = pd.date_range(start=datetime.now(), periods=72, freq='H')
    
    # 模拟预测结果
    np.random.seed(42)
    
    pollutants = ['PM2.5', 'NO2', 'O3']
    predictions = {}
    
    for pollutant in pollutants:
        # 生成带有趋势的预测数据
        base_value = np.random.uniform(20, 60)
        trend = np.linspace(0, 10, 72)
        daily_cycle = 15 * np.sin(2 * np.pi * np.arange(72) / 24)
        noise = np.random.normal(0, 3, 72)
        
        predictions[pollutant] = base_value + trend + daily_cycle + noise
    
    pred_df = pd.DataFrame(predictions, index=future_dates)
    
    # 创建预测可视化
    fig, axes = plt.subplots(len(pollutants), 1, figsize=(15, 4*len(pollutants)))
    
    if len(pollutants) == 1:
        axes = [axes]
    
    colors = ['#e74c3c', '#3498db', '#f39c12']
    
    for i, pollutant in enumerate(pollutants):
        ax = axes[i]
        
        # 绘制预测曲线
        ax.plot(pred_df.index, pred_df[pollutant], 
               color=colors[i], linewidth=2, label='预测值')
        
        # 添加置信区间
        confidence_interval = pred_df[pollutant] * 0.1
        ax.fill_between(pred_df.index,
                       pred_df[pollutant] - confidence_interval,
                       pred_df[pollutant] + confidence_interval,
                       alpha=0.2, color=colors[i], label='95% 置信区间')
        
        # 添加预警线
        if pollutant == 'PM2.5':
            warning_level = 75
            ax.axhline(y=warning_level, color='red', linestyle='--', 
                      alpha=0.7, label='预警线')
        elif pollutant == 'NO2':
            warning_level = 200
            ax.axhline(y=warning_level, color='red', linestyle='--', 
                      alpha=0.7, label='预警线')
        elif pollutant == 'O3':
            warning_level = 160
            ax.axhline(y=warning_level, color='red', linestyle='--', 
                      alpha=0.7, label='预警线')
        
        ax.set_title(f"{pollutant} 未来72小时预测", fontsize=12, fontweight='bold')
        ax.set_xlabel("时间")
        ax.set_ylabel("浓度 (μg/m³)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 格式化x轴
        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=12))
        plt.setp(ax.get_xticklabels(), rotation=45)
    
    plt.suptitle("多污染物未来预测分析", fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.show()
    
    print("✅ 预测分析演示完成")
    
    # 显示预测统计
    print("\n📊 预测统计摘要:")
    for pollutant in pollutants:
        values = pred_df[pollutant]
        print(f"   {pollutant}:")
        print(f"     平均值: {values.mean():.2f} μg/m³")
        print(f"     最大值: {values.max():.2f} μg/m³")
        print(f"     最小值: {values.min():.2f} μg/m³")
        print(f"     标准差: {values.std():.2f} μg/m³")

def main():
    """主演示函数"""
    print("🌍 LSTM多站点多变量空气质量预测系统")
    print("=" * 80)
    print(f"⏰ 演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 演示菜单
    demos = {
        '1': ('快速系统测试', demo_quick_test),
        '2': ('数据可视化演示', demo_visualization),
        '3': ('模型对比分析', demo_model_comparison),
        '4': ('预测分析演示', demo_prediction_analysis),
        '5': ('完整流程演示', lambda: run_complete_pipeline())
    }
    
    print("\n📋 可用演示:")
    for key, (name, _) in demos.items():
        print(f"   {key}. {name}")
    
    print("\n💡 使用说明:")
    print("   - 选择 1 进行快速测试（推荐首次使用）")
    print("   - 选择 2-4 查看各种可视化演示")
    print("   - 选择 5 运行完整的训练和预测流程")
    
    # 交互式选择
    try:
        choice = input("\n请选择演示类型 (1-5): ").strip()
        
        if choice in demos:
            name, demo_func = demos[choice]
            print(f"\n🎯 开始演示: {name}")
            print("-" * 50)
            
            success = demo_func()
            
            if success is not False:
                print(f"\n✅ {name} 完成")
            else:
                print(f"\n❌ {name} 失败")
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n\n👋 演示已取消")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
    
    print("\n🎉 感谢使用LSTM多站点多变量预测系统！")

if __name__ == "__main__":
    main()
