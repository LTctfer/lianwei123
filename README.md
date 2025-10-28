# LIANWEI123 环境监测与智能分析平台

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)]()

## 📋 项目概述

LIANWEI123 是一个综合性的环境监测与智能分析平台，集成了多个子系统，涵盖空气质量预测、污染源溯源、违规行为检测、数据可视化、智能分析等功能，为环境监测和管理提供全方位的技术支持。

---

## 📁 项目结构

```
lianwei123/
├── 可视化项目/                    # 活性炭吸附VOC穿透曲线数据处理与可视化
├── 溯源算法/                      # 污染物溯源系统（PM2.5）
├── ai_violation_detection/        # AI违规行为识别系统
├── lstm算法/                      # 空气质量LSTM预测系统
├── rto/                          # RTO设备预警数据上报系统
├── 智能体搭建/                    # Dify智能体开发
├── 智能体服务器端代码/            # 智能体后端服务
├── 智能体工作流/                  # 智能体工作流配置
├── 知识库准确率检测/              # RAGFlow知识库测试
└── data_clean_tongyong.py        # 通用数据清洗工具
```

---

## 🗂️ 各模块详细说明

### 1️⃣ 可视化项目 - 活性炭吸附VOC穿透曲线系统

**功能描述**：  
处理抽取式活性炭吸附VOC穿透曲线数据，进行数据清洗、统计计算、预警预测和可视化展示。

**核心文件**：
- `adsorption_api.py` - 吸附曲线数据处理API
- `warning_prediction_api.py` - 预警预测API
- `Adsorption_isotherm.py` - 吸附等温线模型

**主要功能**：
- ✅ 基于风速的时间段智能切分
- ✅ 双模式数据清洗（同时测量/分别测量）
- ✅ K-S检验和箱型图异常值过滤
- ✅ 穿透率和效率计算
- ✅ 基于历史数据的预警预测
- ✅ 可视化图表生成

**文档**：
- `算法需求文档.md` - 详细算法需求说明
- `修改后算法实现总结.md` - 算法实现总结
- `累加API使用说明.md` - API使用文档
- `预警系统API使用说明.md` - 预警系统文档

---

### 2️⃣ 溯源算法 - 污染物溯源系统

**功能描述**：  
基于遗传-模式搜索算法的微尺度管控区域大气污染物PM2.5溯源系统。

**核心技术**：
- 🔬 高斯烟羽模型
- 🧬 遗传-模式搜索混合算法
- 📊 双向验证机制（反算+正算）

**核心文件**：
- `pollution_source_tracker.py` - 主溯源算法
- `data_processor.py` - 数据处理模块
- `app.py` - Web应用接口
- `demo.py` - 演示脚本

**性能指标**：
- ✅ 源强反算相对误差：7.2%
- ✅ 位置误差：<10米
- ✅ 平均响应时间：2.44秒

**文档**：
- `README.md` - 系统说明文档
- `三色预警ai溯源方案.md` - 溯源方案说明
- `微尺度管控区域污染溯源算法.md` - 算法详细文档

---

### 3️⃣ ai_violation_detection - AI违规行为识别系统

**功能描述**：  
基于YOLOv8的智能违规行为实时检测系统，支持多场景违规识别。

**检测场景**：

🏗️ **工地违规**
- 工地扬尘检测
- 裸土未覆盖识别
- 土方作业未降尘检测
- 夜间违规施工监控

🌍 **环境污染**
- 露天烧烤识别
- 垃圾焚烧检测
- 渣土车未覆盖识别

🛡️ **安全管理**
- 未戴安全帽检测
- 不安全操作识别
- 禁入区域监控

**核心文件**：
- `models/yolo_violation.py` - YOLO违规检测模型
- `web/app.py` - Flask Web应用
- `utils/alert_system.py` - 智能报警系统
- `quick_start.py` - 快速启动脚本

**特性**：
- ✅ 实时图片/视频流检测
- ✅ 高精度识别（基于YOLOv8）
- ✅ 智能多级别报警
- ✅ Web可视化界面
- ✅ 完整报警管理系统

**文档**：
- `README.md` - 系统完整说明
- `AI违规检测系统说明文档.md` - 详细文档

---

### 4️⃣ lstm算法 - 空气质量LSTM预测系统

**功能描述**：  
基于深度学习LSTM网络的多站点多变量空气质量预测系统。

**监测站点**（伦敦5个站点）：
- Bloomsbury（布卢姆斯伯里）
- Marylebone Road（马里波恩路）
- Eltham（埃尔瑟姆）
- Harlington（哈灵顿）
- N Kensington（北肯辛顿）

**预测变量**：
- 污染物：NOx, NO2, NO, O3, PM2.5
- 气象：风速(ws), 风向(wd), 气温(air_temp)

**核心文件**：
- `multi_station_lstm_system.py` - 多站点LSTM主系统
- `prediction_engine.py` - 预测引擎
- `interactive_dashboard.py` - 交互式仪表盘
- `demo_lstm_system.py` - 演示脚本

**特性**：
- ✅ 多站点数据融合
- ✅ 多变量同时预测
- ✅ TensorFlow/Keras深度学习
- ✅ Streamlit Web界面
- ✅ 完整模型评估

**文档**：
- `README_LSTM.md` - 系统说明文档
- `系统说明文档.md` - 详细说明
- `小白使用指南.md` - 新手指南

**快速启动**：
```bash
启动Web界面.bat
```

---

### 5️⃣ rto - RTO设备预警数据上报系统

**功能描述**：  
从PLC设备读取RTO（蓄热式热氧化器）实时数据，根据配置规则自动生成预警并上报到远程API。

**核心功能**：
- 📡 Modbus串口通信读取PLC数据
- 📊 实时数据CSV存储和管理
- 🔔 基于规则的智能预警判断
- 📤 自动上报预警到远程API
- 🧹 数据清洗和异常值检测

**核心文件**：
- `rto/read_upload.py` - 数据读取与上报主程序
- `rto/server_api.py` - 本地API服务器
- `rto/config.json` - 预警规则配置

**监测参数**：
- T1：加热室平均温度
- T2：RTO出口温度
- T3：RTO进口温度
- P1：RTO出口压力
- 风机启停状态

**文档**：
- `预警规则配置接口说明.md` - 规则配置说明
- `代码优化总结.md` - 优化记录

---

### 6️⃣ 智能体搭建 - Dify智能体开发

**功能描述**：  
基于Dify平台的环境数据分析智能体，支持自然语言查询数据库并生成分析报告。

**已实现功能**：
- ✅ 自然语言 → SQL语句转换
- ✅ 数据库查询插件
- ✅ 智能分析和建议生成
- ✅ 自动生成可视化图表
- ✅ Markdown转Word文档生成

**核心文件**：
- `测试联通.py` - 连接测试
- `垃圾焚烧数据分析智能体提示词.md` - 提示词配置

**文档**：
- `功能总结及需求文档.md` - 功能说明
- `分析报告模板.md` - 报告模板
- `数据库建表语句.md` - 数据库结构

---

### 7️⃣ 智能体工作流

**功能描述**：  
Dify工作流配置文件，定义智能体的处理流程。

**核心文件**：
- `垃圾分析文本生成.yml` - 文本生成流程
- `文生word_http_post.yml` - Word生成流程

---

### 8️⃣ 智能体服务器端代码

**功能描述**：  
智能体后端服务代码，处理文档生成和格式转换。

**目录**：
- `ceshi2(word有图片但是文字格式乱)_jm2ts/` - Word生成测试代码

---

### 9️⃣ 知识库准确率检测

**功能描述**：  
基于RAGFlow的知识库搭建和准确率测试。

**工作内容**：
- ✅ RAGFlow服务器部署
- ✅ 知识库文档上传和解析
- ✅ Dify外挂知识库集成
- ✅ 准确率测试（约90%）

**核心文件**：
- `chuanjian.py` - 知识库创建脚本
- `焚烧发电厂监测数据示例.csv` - 示例数据

**文档**：
- `知识库搭建工作.md` - 搭建文档

---

### 🔟 通用工具

**data_clean_tongyong.py**  
通用数据清洗工具，提供标准化的数据预处理功能。

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.7+
- **操作系统**: Windows / Linux
- **数据库**: MySQL / PostgreSQL（智能体模块）
- **硬件**: 
  - AI检测系统建议GPU支持
  - 其他模块CPU即可

### 安装依赖

每个子项目都有独立的依赖文件：

```bash
# 溯源算法
cd 溯源算法
pip install -r requirements.txt

# AI违规检测
cd ai_violation_detection
pip install -r requirements.txt

# LSTM预测
cd lstm算法
pip install -r requirements_lstm.txt

# RTO系统
cd rto/rto
pip install pandas numpy requests pymodbus
```

### 运行示例

**AI违规检测系统**：
```bash
cd ai_violation_detection
python quick_start.py
# 或直接双击 start.bat
```

**LSTM预测系统**：
```bash
cd lstm算法
# Windows用户双击：启动Web界面.bat
# Linux用户：
streamlit run interactive_dashboard.py
```

**污染源溯源系统**：
```bash
cd 溯源算法
python demo.py
```

**RTO预警系统**：
```bash
cd rto/rto
python read_upload.py
```

---

## 📊 技术栈

### 后端
- **Python 3.7+**
- **Flask** - Web框架
- **TensorFlow/Keras** - 深度学习
- **PyTorch** - YOLOv8模型
- **Pandas/NumPy** - 数据处理
- **SciPy** - 科学计算
- **DEAP** - 遗传算法

### 前端
- **Streamlit** - 快速Web应用
- **Matplotlib/Seaborn** - 数据可视化
- **Plotly** - 交互式图表

### 数据库
- **MySQL/PostgreSQL** - 关系型数据库
- **SQLite** - 轻量级数据库

### AI/ML
- **YOLOv8** - 目标检测
- **LSTM** - 时序预测
- **遗传算法** - 优化求解
- **高斯烟羽模型** - 污染扩散

### 通信协议
- **Modbus RTU** - PLC通信
- **HTTP/REST API** - 远程接口

---

## 🎯 应用场景

### 环境监测
- ✅ 实时空气质量监测
- ✅ 污染物浓度预测
- ✅ 污染源定位溯源

### 工业控制
- ✅ RTO设备运行监控
- ✅ 活性炭吸附效率分析
- ✅ 设备预警和故障诊断

### 安全管理
- ✅ 工地违规行为检测
- ✅ 安全装备佩戴监控
- ✅ 危险区域入侵检测

### 智能分析
- ✅ 环境数据智能问答
- ✅ 自动生成分析报告
- ✅ 可视化图表生成

---

## 📝 开发文档

各子项目都有详细的文档说明：

| 模块 | 主要文档 |
|------|---------|
| 可视化项目 | `算法需求文档.md`、`修改后算法实现总结.md` |
| 溯源算法 | `README.md`、`三色预警ai溯源方案.md` |
| AI违规检测 | `README.md`、`AI违规检测系统说明文档.md` |
| LSTM算法 | `README_LSTM.md`、`系统说明文档.md` |
| RTO系统 | `预警规则配置接口说明.md`、`代码优化总结.md` |
| 智能体 | `功能总结及需求文档.md` |
| 知识库 | `知识库搭建工作.md` |

---

## 🔧 配置说明

### RTO系统配置
编辑 `rto/rto/config.json` 配置预警规则：
```json
{
  "rules": [
    {
      "alarmRuleId": "rule001",
      "alarmRuleName": "温度异常预警",
      "enabled": 1,
      "config": {
        "singlePropertyRule": [...],
        "frequency": {...}
      }
    }
  ]
}
```

### API接口配置
各系统API地址可在相应的配置文件或代码中修改：
- 可视化项目：`adsorption_api.py`
- RTO系统：`read_upload.py` 中的 `REMOTE_API_URL`

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发流程
1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👥 联系方式

- **项目维护**: LTctfer
- **仓库**: [github.com/LTctfer/lianwei123](https://github.com/LTctfer/lianwei123)

---

## 🌟 致谢

感谢所有为本项目做出贡献的开发者！

特别感谢以下开源项目：
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [TensorFlow](https://www.tensorflow.org/)
- [Streamlit](https://streamlit.io/)
- [Dify](https://dify.ai/)
- [RAGFlow](https://github.com/infiniflow/ragflow)

---

## 📈 项目统计

- **子系统数量**: 10+
- **代码语言**: Python
- **文档数量**: 20+
- **应用场景**: 环境监测、工业控制、安全管理、智能分析

---

**更新时间**: 2025-10-28  
**版本**: v1.0.0

---

## 🗺️ 路线图

### 已完成 ✅
- [x] 活性炭吸附VOC穿透曲线分析系统
- [x] PM2.5污染源溯源系统
- [x] AI违规行为检测系统
- [x] 空气质量LSTM预测系统
- [x] RTO设备预警系统
- [x] Dify智能体数据分析
- [x] RAGFlow知识库集成

### 进行中 🚧
- [ ] 智能体PPT自动生成功能
- [ ] 知识库准确率优化（目标>95%）
- [ ] 多系统数据整合分析

### 计划中 📋
- [ ] 移动端App开发
- [ ] 实时监控大屏
- [ ] 多租户系统支持
- [ ] 云端部署方案
- [ ] 国际化支持

---

> **注意**：本项目仅供学习和研究使用，实际应用请根据具体场景进行适当调整和测试。
