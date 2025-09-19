# LSTM多站点多变量空气质量预测系统

## 🌍 项目简介

这是一个基于深度学习LSTM网络的多站点多变量空气质量预测系统，能够利用多个监测站点的历史数据预测未来的空气质量状况。

## ✨ 主要特性

- **多站点数据融合**: 同时利用5个监测站点的数据进行预测
- **多变量预测**: 支持NOx, NO2, NO, O3, PM2.5等多种污染物预测
- **深度学习模型**: 基于TensorFlow/Keras的LSTM神经网络
- **实时可视化**: 提供丰富的图表和交互式界面
- **Web界面**: 基于Streamlit的用户友好界面
- **模型评估**: 完整的模型性能评估和分析

## 📊 数据说明

### 监测站点
- **Bloomsbury**: 伦敦布卢姆斯伯里
- **Marylebone Road**: 伦敦马里波恩路
- **Eltham**: 伦敦埃尔瑟姆
- **Harlington**: 伦敦哈灵顿
- **N Kensington**: 伦敦北肯辛顿

### 监测变量
- **污染物**: NOx, NO2, NO, O3, PM2.5
- **气象**: 风速(ws), 风向(wd), 气温(air_temp)

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements_lstm.txt
```

### 2. 数据准备

确保数据文件位于 `air_pollutants_prediction_lstm-master/data/` 目录下：
- Bloomsbury_clean.csv
- Marylebone_Road_clean.csv
- Eltham_clean.csv
- Harlington_clean.csv
- N_Kensington_clean.csv

### 3. 运行演示

```bash
# 运行命令行演示
python demo_lstm_system.py

# 启动Web界面
streamlit run interactive_dashboard.py
```

## 📁 项目结构

```
lstm算法/
├── multi_station_lstm_system.py    # 核心系统类
├── prediction_engine.py            # 预测引擎
├── interactive_dashboard.py        # Web界面
├── demo_lstm_system.py            # 演示脚本
├── requirements_lstm.txt          # 依赖文件
├── README_LSTM.md                 # 项目说明
└── air_pollutants_prediction_lstm-master/
    └── data/                      # 数据文件目录
```

## 🔧 核心组件

### MultiStationDataProcessor
- 多站点数据加载和预处理
- 数据清洗和归一化
- 时间序列窗口创建

### MultiVariateLSTMModel
- LSTM神经网络模型
- 支持多层LSTM和全连接层
- 批标准化和Dropout正则化

### PredictionVisualizer
- 训练历史可视化
- 预测结果对比图
- 特征相关性分析
- 综合仪表板

### LSTMPredictionEngine
- 完整预测流程管理
- 模型训练和评估
- 未来预测生成
- 结果保存和加载

## 📈 使用示例

### 基本预测流程

```python
from prediction_engine import LSTMPredictionEngine

# 创建预测引擎
engine = LSTMPredictionEngine("air_pollutants_prediction_lstm-master/data")

# 加载数据
engine.load_and_prepare_data()

# 训练模型
model_config = {
    'lstm_units': [128, 64],
    'dense_units': [64, 32],
    'dropout_rate': 0.3
}
engine.build_and_train_model(model_config)

# 评估模型
metrics, predictions = engine.evaluate_model()

# 预测未来72小时
prediction_df, pred_array = engine.predict_future(hours=72)

# 保存结果
engine.save_predictions(prediction_df)
```

### Web界面使用

1. 启动Web界面：`streamlit run interactive_dashboard.py`
2. 在浏览器中打开 `http://localhost:8501`
3. 按照界面提示配置参数
4. 点击"初始化系统"加载数据
5. 点击"开始训练模型"训练LSTM
6. 在预测分析页面生成预测结果

## 🎯 模型配置

### 默认配置
- **历史窗口**: 240小时（10天）
- **预测范围**: 24小时
- **LSTM层**: [128, 64]单元
- **全连接层**: [64, 32]单元
- **Dropout率**: 0.3
- **学习率**: 0.001

### 可调参数
- 窗口大小：24-720小时
- 预测时长：1-168小时
- 网络结构：可自定义层数和单元数
- 训练参数：学习率、批次大小、训练轮数

## 📊 性能指标

系统提供多种评估指标：
- **R²分数**: 决定系数，衡量模型拟合度
- **RMSE**: 均方根误差
- **MAE**: 平均绝对误差
- **MSE**: 均方误差

## 🔮 预测功能

### 支持的预测类型
- **单步预测**: 预测下一个时间点
- **多步预测**: 预测未来多个时间点
- **滚动预测**: 逐步更新预测窗口

### 预测输出
- **CSV文件**: 结构化预测数据
- **可视化图表**: 时间序列预测图
- **统计摘要**: 预测结果统计信息

## 🛠️ 高级功能

### 特征分析
- 特征相关性矩阵
- 特征重要性分析
- 数据分布分析

### 模型优化
- 早停机制
- 学习率调度
- 模型检查点保存

### 可视化选项
- 训练历史曲线
- 预测对比图
- 残差分析
- 置信区间显示

## 🚨 注意事项

1. **数据质量**: 确保输入数据完整且格式正确
2. **计算资源**: LSTM训练需要一定的计算资源
3. **内存使用**: 大窗口大小会增加内存消耗
4. **训练时间**: 根据数据量和模型复杂度调整训练轮数

## 🔧 故障排除

### 常见问题

1. **数据加载失败**
   - 检查数据文件路径
   - 确认CSV文件格式正确

2. **模型训练缓慢**
   - 减少训练轮数
   - 降低模型复杂度
   - 使用GPU加速

3. **内存不足**
   - 减少批次大小
   - 缩短历史窗口
   - 减少特征数量

4. **预测精度低**
   - 增加训练数据
   - 调整模型参数
   - 改进特征工程

## 📞 技术支持

如有问题或建议，请通过以下方式联系：
- 提交Issue到项目仓库
- 查看项目文档和示例代码
- 参考TensorFlow官方文档

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🙏 致谢

感谢以下开源项目的支持：
- TensorFlow/Keras
- Pandas & NumPy
- Matplotlib & Seaborn
- Plotly & Streamlit
- Scikit-learn
