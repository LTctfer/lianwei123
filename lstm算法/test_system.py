"""
LSTM多站点多变量预测系统测试脚本
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

def test_data_availability():
    """测试数据文件可用性"""
    print("🔍 测试数据文件可用性...")
    
    data_dir = "air_pollutants_prediction_lstm-master/data"
    required_files = [
        "Bloomsbury_clean.csv",
        "Marylebone_Road_clean.csv", 
        "Eltham_clean.csv",
        "Harlington_clean.csv",
        "N_Kensington_clean.csv"
    ]
    
    available_files = []
    missing_files = []
    
    for file in required_files:
        file_path = os.path.join(data_dir, file)
        if os.path.exists(file_path):
            print(f"   ✅ {file}")
            available_files.append(file)
        else:
            print(f"   ❌ {file}")
            missing_files.append(file)
    
    print(f"\n📊 结果: {len(available_files)}/{len(required_files)} 文件可用")
    
    if available_files:
        # 测试读取第一个可用文件
        test_file = os.path.join(data_dir, available_files[0])
        try:
            df = pd.read_csv(test_file)
            print(f"   📋 测试文件 {available_files[0]}:")
            print(f"      数据形状: {df.shape}")
            print(f"      列名: {list(df.columns)}")
            print(f"      时间范围: {df['date'].min()} 到 {df['date'].max()}")
            return True
        except Exception as e:
            print(f"   ❌ 读取测试文件失败: {e}")
            return False
    else:
        print("   ❌ 没有可用的数据文件")
        return False

def test_tensorflow_import():
    """测试TensorFlow导入"""
    print("\n🤖 测试TensorFlow导入...")
    
    try:
        import tensorflow as tf
        print(f"   ✅ TensorFlow版本: {tf.__version__}")
        
        # 测试基本操作
        x = tf.constant([[1.0, 2.0], [3.0, 4.0]])
        y = tf.constant([[1.0, 1.0], [0.0, 1.0]])
        z = tf.matmul(x, y)
        print(f"   ✅ 基本张量运算测试通过")
        
        # 测试Keras
        from tensorflow import keras
        print(f"   ✅ Keras可用")
        
        return True
        
    except Exception as e:
        print(f"   ❌ TensorFlow导入失败: {e}")
        return False

def test_data_processor():
    """测试数据处理器"""
    print("\n📊 测试数据处理器...")
    
    try:
        from multi_station_lstm_system import MultiStationDataProcessor
        
        # 创建数据处理器
        processor = MultiStationDataProcessor("air_pollutants_prediction_lstm-master/data")
        print("   ✅ 数据处理器创建成功")
        
        # 测试加载数据
        if processor.load_all_stations():
            print("   ✅ 多站点数据加载成功")
            print(f"      合并数据形状: {processor.combined_data.shape}")
            
            # 测试归一化
            if processor.normalize_data():
                print("   ✅ 数据归一化成功")
                print(f"      归一化数据形状: {processor.scaled_data.shape}")
                
                # 测试序列创建
                X, y = processor.create_sequences(window_size=24, prediction_horizon=1)
                if X is not None and y is not None:
                    print("   ✅ 时间序列创建成功")
                    print(f"      输入序列形状: {X.shape}")
                    print(f"      目标序列形状: {y.shape}")
                    return True
                else:
                    print("   ❌ 时间序列创建失败")
                    return False
            else:
                print("   ❌ 数据归一化失败")
                return False
        else:
            print("   ❌ 数据加载失败")
            return False
            
    except Exception as e:
        print(f"   ❌ 数据处理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_lstm_model():
    """测试LSTM模型"""
    print("\n🧠 测试LSTM模型...")
    
    try:
        from multi_station_lstm_system import MultiVariateLSTMModel
        
        # 创建模型
        input_shape = (24, 40)  # 24小时，40个特征
        output_shape = (1, 40)  # 1小时，40个特征
        
        model = MultiVariateLSTMModel(input_shape, output_shape)
        print("   ✅ LSTM模型创建成功")
        
        # 构建模型
        keras_model = model.build_model()
        print("   ✅ 模型构建成功")
        print(f"      参数数量: {keras_model.count_params():,}")
        
        # 测试预测
        X_test = np.random.random((10, 24, 40))
        predictions = model.predict(X_test)
        print("   ✅ 模型预测测试成功")
        print(f"      预测形状: {predictions.shape}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ LSTM模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_visualization():
    """测试可视化功能"""
    print("\n📈 测试可视化功能...")
    
    try:
        # 生成测试数据
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
                seasonal = 10 * np.sin(2 * np.pi * np.arange(100) / 24)
                
                data[f"{pollutant}_{station}"] = trend + noise + seasonal
        
        df = pd.DataFrame(data, index=dates)
        print("   ✅ 测试数据生成成功")
        print(f"      数据形状: {df.shape}")
        
        # 测试基本绘图
        plt.figure(figsize=(12, 6))
        
        # 绘制PM2.5数据
        for station in stations:
            column = f"pm2.5_{station}"
            if column in df.columns:
                plt.plot(df.index[:24], df[column][:24], 
                        label=f"站点 {station}", alpha=0.7)
        
        plt.title("PM2.5 浓度变化（测试）")
        plt.xlabel("时间")
        plt.ylabel("浓度 (μg/m³)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # 保存图片而不显示
        plt.savefig("test_visualization.png", dpi=100, bbox_inches='tight')
        plt.close()
        
        print("   ✅ 可视化测试成功，图片已保存为 test_visualization.png")
        return True
        
    except Exception as e:
        print(f"   ❌ 可视化测试失败: {e}")
        return False

def test_prediction_engine():
    """测试预测引擎（简化版）"""
    print("\n🔮 测试预测引擎...")
    
    try:
        from prediction_engine import LSTMPredictionEngine
        
        # 创建预测引擎
        engine = LSTMPredictionEngine("air_pollutants_prediction_lstm-master/data")
        print("   ✅ 预测引擎创建成功")
        
        # 设置快速测试配置
        engine.config.update({
            'window_size': 24,  # 1天历史数据
            'prediction_horizon': 1,  # 预测1小时
            'epochs': 1,  # 快速训练
            'batch_size': 16
        })
        
        print("   ✅ 配置设置成功")
        return True
        
    except Exception as e:
        print(f"   ❌ 预测引擎测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 LSTM多站点多变量预测系统 - 系统测试")
    print("=" * 80)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    tests = [
        ("数据文件可用性", test_data_availability),
        ("TensorFlow导入", test_tensorflow_import),
        ("数据处理器", test_data_processor),
        ("LSTM模型", test_lstm_model),
        ("可视化功能", test_visualization),
        ("预测引擎", test_prediction_engine)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🎯 开始测试: {test_name}")
        print("-" * 50)
        
        try:
            success = test_func()
            results[test_name] = "✅ 通过" if success else "❌ 失败"
        except Exception as e:
            print(f"   ❌ 测试异常: {e}")
            results[test_name] = "❌ 异常"
    
    # 显示测试结果摘要
    print("\n" + "=" * 80)
    print("📋 测试结果摘要")
    print("=" * 80)
    
    for test_name, result in results.items():
        print(f"   {result} {test_name}")
    
    success_count = sum(1 for result in results.values() if "✅" in result)
    total_count = len(results)
    
    print(f"\n🎉 测试完成: {success_count}/{total_count} 个测试通过")
    
    if success_count == total_count:
        print("🏆 所有测试通过！系统运行正常。")
        
        print("\n💡 下一步操作建议:")
        print("   1. 运行 'python demo_lstm_system.py' 进行交互式演示")
        print("   2. 运行 'streamlit run interactive_dashboard.py' 启动Web界面")
        print("   3. 查看 README_LSTM.md 了解详细使用说明")
        
    else:
        print("⚠️ 部分测试失败，请检查系统配置。")
        
        if not any("数据文件可用性" in k and "✅" in v for k, v in results.items()):
            print("\n📁 数据文件问题:")
            print("   请确保数据文件位于 air_pollutants_prediction_lstm-master/data/ 目录")
            print("   需要的文件: Bloomsbury_clean.csv, Marylebone_Road_clean.csv 等")
    
    return success_count == total_count

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
