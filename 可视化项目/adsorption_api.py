#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抽取式吸附曲线预警系统HTTP接口
调用现有的Adsorption_isotherm.py算法处理数据
"""

from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from datetime import datetime
import tempfile
import os
import sys
import json

# 导入现有的算法
from Adsorption_isotherm import AdsorptionCurveProcessor

app = Flask(__name__)

class AdsorptionAPIWrapper:
    """吸附算法API包装器"""
    
    def __init__(self):
        self.processor = None
    
    def process_json_data(self, json_data: list) -> dict:
        """处理JSON数据并调用现有算法"""
        try:
            # 1. 验证数据格式
            if not isinstance(json_data, list) or len(json_data) == 0:
                return {"error": "数据格式错误或为空"}
            
            # 2. 转换JSON到DataFrame
            df = pd.DataFrame(json_data)
            
            # 3. 验证必要字段
            required_fields = ['gvocs', 'invoc', 'gwindspeed', 'access', 'createTime']
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                return {"error": f"缺少必要字段: {missing_fields}"}
            
            # 4. 数据映射和转换
            # 将JSON字段映射到算法期望的CSV列名
            df_mapped = pd.DataFrame()
            df_mapped['出口voc'] = df['gvocs']
            df_mapped['进口voc'] = df['invoc'] 
            df_mapped['风管内风速值'] = df['gwindspeed']
            df_mapped['进口0出口1'] = df['access']
            df_mapped['创建时间'] = pd.to_datetime(df['createTime'])
            
            # 5. 保存为临时CSV文件
            temp_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig')
            df_mapped.to_csv(temp_csv.name, index=False)
            temp_csv.close()
            
            # 6. 调用现有算法
            processor = AdsorptionCurveProcessor(temp_csv.name)
            
            # 加载数据
            if not processor.load_data():
                os.unlink(temp_csv.name)
                return {"error": "数据加载失败"}
            
            # 识别数据类型
            data_type = processor.identify_data_type(processor.raw_data)
            
            # 数据清洗
            cleaned_data = processor.basic_data_cleaning(processor.raw_data)
            cleaned_data = processor.ks_test_cleaning(cleaned_data)
            cleaned_data = processor.boxplot_cleaning(cleaned_data)
            
            # 计算效率数据
            efficiency_data = processor.calculate_efficiency_data(cleaned_data, "综合清洗")
            
            if efficiency_data is None or efficiency_data.empty:
                os.unlink(temp_csv.name)
                return {"error": "无法计算效率数据"}
            
            # 运行预警系统分析
            processor.analyze_warning_system()
            
            # 7. 提取结果
            result = self._extract_visualization_data(processor, efficiency_data)
            
            # 清理临时文件
            os.unlink(temp_csv.name)
            
            return result
            
        except Exception as e:
            return {"error": f"处理失败: {str(e)}"}
    
    def _extract_visualization_data(self, processor: AdsorptionCurveProcessor, efficiency_data: pd.DataFrame) -> dict:
        """从算法结果中提取可视化数据"""
        try:
            # 提取数据点
            data_points = []
            
            for _, row in efficiency_data.iterrows():
                # 使用算法计算的穿透率
                breakthrough_ratio = row['breakthrough_ratio'] * 100  # 转换为百分比
                
                # 时间转换为小时
                time_hours = row['time'] / 3600  # 从秒转换为小时
                
                # 生成时间段标识
                if 'window_start' in row and 'window_end' in row:
                    # 使用算法中的时间窗口格式
                    start_time = pd.to_datetime(row['window_start'])
                    end_time = pd.to_datetime(row['window_end'])
                    time_segment = f"{start_time.strftime('%m-%d %H:%M')}-{end_time.strftime('%H:%M')}"
                else:
                    # 如果没有时间窗口信息，使用索引
                    time_segment = f"时间段{len(data_points)+1}"
                
                # 按照算法内的标签格式：时间段、累计时长和穿透率
                label = f"时间段: {time_segment}\n累积时长: {time_hours:.2f}小时\n穿透率: {breakthrough_ratio:.1f}%"
                
                data_points.append({
                    "x": float(time_hours),  # X轴：时间（小时）
                    "y": float(breakthrough_ratio),  # Y轴：穿透率（%）
                    "label": label,  # 按算法格式的标签
                    "time_segment": time_segment,
                    "cumulative_hours": float(time_hours),
                    "breakthrough_percent": float(breakthrough_ratio),
                    "efficiency": float(row['efficiency']),
                    "inlet_concentration": float(row['inlet_conc']),
                    "outlet_concentration": float(row['outlet_conc'])
                })
            
            # 提取预警点
            warning_points = self._extract_warning_points(processor)
            
            return {
                "success": True,
                "data_points": data_points,
                "warning_points": warning_points,
                "total_points": len(data_points)
            }
            
        except Exception as e:
            return {"error": f"数据提取失败: {str(e)}"}
    
    def _extract_warning_points(self, processor: AdsorptionCurveProcessor) -> list:
        """提取预警点（五角星标注的点）"""
        warning_points = []
        
        try:
            # 检查是否有预警模型
            if hasattr(processor, 'warning_model') and processor.warning_model.fitted:
                model = processor.warning_model
                
                # 获取预警时间点（对应图像中的五角星标注）
                if hasattr(model, 'warning_time') and model.warning_time is not None:
                    # 计算预警时间点的穿透率
                    A, k, t0 = model.params
                    warning_breakthrough = model.logistic_function(model.warning_time, A, k, t0) * 100
                    warning_time_hours = model.warning_time / 3600  # 转换为小时
                    
                    warning_points.append({
                        "x": float(warning_time_hours),  # X轴：预警时间（小时）
                        "y": float(warning_breakthrough),  # Y轴：预警点穿透率（%）
                        "type": "warning_star",
                        "description": "预警系统计算的预警点（五角星标注）"
                    })
                
                # 如果有预测饱和时间点
                if hasattr(model, 'predicted_saturation_time') and model.predicted_saturation_time is not None:
                    saturation_breakthrough = model.logistic_function(model.predicted_saturation_time, A, k, t0) * 100
                    saturation_time_hours = model.predicted_saturation_time / 3600
                    
                    warning_points.append({
                        "x": float(saturation_time_hours),
                        "y": float(saturation_breakthrough),
                        "type": "saturation_star",
                        "description": "预测饱和点（五角星标注）"
                    })
        
        except Exception as e:
            print(f"预警点提取警告: {e}")
        
        return warning_points

# 创建API包装器实例
api_wrapper = AdsorptionAPIWrapper()

@app.route('/api/extraction-adsorption-curve/process', methods=['POST'])
def process_extraction_adsorption_curve():
    """抽取式吸附曲线预警系统API接口"""
    try:
        # 获取JSON数据
        json_data = request.get_json()
        
        if not json_data:
            return jsonify({"error": "未提供JSON数据"}), 400
        
        # 处理数据
        result = api_wrapper.process_json_data(json_data)
        
        if "error" in result:
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

@app.route('/api/extraction-adsorption-curve/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "healthy",
        "service": "extraction_adsorption_curve_warning_system",
        "version": "1.0.0"
    })

@app.route('/api/extraction-adsorption-curve/info', methods=['GET'])
def api_info():
    """API信息接口"""
    return jsonify({
        "api_name": "抽取式吸附曲线预警系统",
        "version": "1.0.0",
        "description": "基于现有Adsorption_isotherm.py算法的HTTP接口，处理VOC监测数据并返回可视化坐标点和预警信息",
        "endpoints": {
            "/api/extraction-adsorption-curve/process": {
                "method": "POST",
                "description": "处理抽取式吸附曲线数据，返回数据点坐标和预警点坐标",
                "input_format": {
                    "gvocs": "出口VOC浓度 -> 出口voc列",
                    "invoc": "进口VOC浓度 -> 进口voc列", 
                    "gwindspeed": "风管内风速 -> 风管内风速值列",
                    "access": "进口(0)或出口(1) -> 进口0出口1列",
                    "createTime": "创建时间 -> 创建时间列"
                },
                "output_format": {
                    "data_points": "数据点数组，包含x(时间)、y(穿透率)、label(标签)",
                    "warning_points": "预警点数组，包含x(时间)、y(穿透率)，对应图像中的五角星标注点"
                }
            },
            "/api/extraction-adsorption-curve/health": {
                "method": "GET",
                "description": "健康检查"
            },
            "/api/extraction-adsorption-curve/info": {
                "method": "GET", 
                "description": "API信息"
            }
        }
    })

if __name__ == '__main__':
    print("启动抽取式吸附曲线预警系统...")
    print("API文档: http://localhost:5000/api/extraction-adsorption-curve/info")
    print("健康检查: http://localhost:5000/api/extraction-adsorption-curve/health")
    print("数据处理: POST http://localhost:5000/api/extraction-adsorption-curve/process")
    app.run(debug=True, host='0.0.0.0', port=5000)
