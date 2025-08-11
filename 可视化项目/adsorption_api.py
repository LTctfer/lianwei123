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

# 设置JSON编码，确保中文正确显示
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

class AdsorptionAPIWrapper:
    """吸附算法API包装器"""
    
    def __init__(self):
        self.processor = None
    
    def process_json_data(self, json_data: list) -> dict:
        """处理JSON数据并调用现有算法"""
        try:
            # 1. 验证数据格式
            if not isinstance(json_data, list) or len(json_data) == 0:
                return {"status": "failure", "error": "数据格式错误或为空"}
            
            # 2. 转换JSON到DataFrame
            df = pd.DataFrame(json_data)
            
            # 3. 验证必要字段
            required_fields = ['gVocs', 'inVoc', 'gWindspeed', 'access', 'createTime']
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                return {"status": "failure", "error": f"缺少必要字段: {missing_fields}"}
            
            # 4. 数据映射和转换
            # 将JSON字段映射到算法期望的CSV列名
            df_mapped = pd.DataFrame()
            df_mapped['出口voc'] = df['gVocs']
            df_mapped['进口voc'] = df['inVoc'] 
            df_mapped['风管内风速值'] = df['gWindspeed']
            df_mapped['进口0出口1'] = df['access']
            df_mapped['创建时间'] = pd.to_datetime(df['createTime'])
            
            # 添加风量字段（算法中需要，设置默认值为1.0，避免被过滤掉）
            df_mapped['风量'] = 1.0
            
            # 5. 保存为临时CSV文件
            temp_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig')
            df_mapped.to_csv(temp_csv.name, index=False)
            temp_csv.close()
            
            # 6. 调用现有算法
            processor = AdsorptionCurveProcessor(temp_csv.name)
            
            # 加载数据
            if not processor.load_data():
                os.unlink(temp_csv.name)
                return {"status": "failure", "error": "数据加载失败"}
            
            # 按照算法的完整流程处理数据
            
            # 1. 基础数据清洗（包含风速切分和两套清洗规则）
            basic_cleaned = processor.basic_data_cleaning(processor.raw_data)
            if basic_cleaned is None or basic_cleaned.empty:
                os.unlink(temp_csv.name)
                return {"status": "failure", "error": "基础数据清洗后无有效数据"}
            
            # 2. 高级筛选（K-S检验和箱型图）
            processor.cleaned_data_ks = processor.ks_test_cleaning(basic_cleaned)
            processor.cleaned_data_boxplot = processor.boxplot_cleaning(basic_cleaned)
            
            # 3. 选择数据量更少的筛选结果
            ks_count = len(processor.cleaned_data_ks) if processor.cleaned_data_ks is not None else 0
            boxplot_count = len(processor.cleaned_data_boxplot) if processor.cleaned_data_boxplot is not None else 0
            
            if ks_count > 0 and boxplot_count > 0:
                if ks_count <= boxplot_count:
                    processor.final_cleaned_data = processor.cleaned_data_ks
                    processor.selected_method = "K-S检验"
                else:
                    processor.final_cleaned_data = processor.cleaned_data_boxplot
                    processor.selected_method = "箱型图"
            elif ks_count > 0:
                processor.final_cleaned_data = processor.cleaned_data_ks
                processor.selected_method = "K-S检验"
            elif boxplot_count > 0:
                processor.final_cleaned_data = processor.cleaned_data_boxplot
                processor.selected_method = "箱型图"
            else:
                os.unlink(temp_csv.name)
                return {"status": "failure", "error": "K-S检验和箱型图筛选后均无有效数据"}
            
            # 4. 计算效率数据（两套规则）
            processor.efficiency_data = processor.calculate_efficiency_with_two_rules(
                processor.final_cleaned_data, processor.selected_method)
            
            if processor.efficiency_data is None or processor.efficiency_data.empty:
                os.unlink(temp_csv.name)
                return {"status": "failure", "error": "无法计算效率数据"}
            
            # 5. 预警系统分析
            processor.analyze_warning_system_with_final_data()
            
            # 7. 提取结果
            result = self._extract_visualization_data(processor, processor.efficiency_data)
            
            # 清理临时文件
            os.unlink(temp_csv.name)
            
            # 添加成功状态
            result["status"] = "success"
            return result
            
        except Exception as e:
            return {"status": "yichang", "error": f"处理失败: {str(e)}"}

    def _extract_visualization_data(self, processor: AdsorptionCurveProcessor, efficiency_data: pd.DataFrame) -> dict:
        """从算法结果中提取可视化数据"""
        try:
            # 提取数据点
            data_points = []
            
            for idx, row in efficiency_data.iterrows():
                # 获取累计运行时间（小时）- 算法中已经计算好的时间坐标
                time_hours = float(row['时间坐标'])  # 算法中时间坐标已经是小时单位
                
                # 获取穿透率（百分比）
                breakthrough_ratio = float(row['穿透率']) * 100  # 转换为百分比
                
                # 获取处理效率
                efficiency = float(row['处理效率'])
                
                # 生成时间段标识
                if 'window_start' in row and 'window_end' in row:
                    # 使用算法中的时间窗口格式
                    start_time = pd.to_datetime(row['window_start'])
                    end_time = pd.to_datetime(row['window_end'])
                    time_segment = f"{start_time.strftime('%m-%d %H:%M')}-{end_time.strftime('%H:%M')}"
                else:
                    # 根据计算规则生成时间段标识
                    if '计算规则' in row:
                        rule = row['计算规则']
                        if rule == '规则1-风速段' and '风速段' in row:
                            time_segment = f"风速段{int(row['风速段'])}"
                        elif rule == '规则2-拼接段' and '拼接时间段' in row:
                            time_segment = f"拼接段{int(row['拼接时间段'])}"
                        else:
                            time_segment = f"时间段{idx+1}"
                    else:
                        time_segment = f"时间段{idx+1}"
                
                # 按照算法内的标签格式：时间段、累计时长和穿透率
                label = f"时间段: {time_segment}\n累积时长: {time_hours:.2f}小时\n穿透率: {breakthrough_ratio:.1f}%"
                
                # 数值格式化：保留2位小数，接近0则返回0
                def format_number(value):
                    """格式化数值，保留2位小数，接近0则返回0"""
                    if abs(value) < 0.01:  # 小于0.01视为接近0
                        return 0.0
                    return round(value, 2)
                
                data_points.append({
                    "x": format_number(time_hours),  # X轴：累计运行时间（小时）
                    "y": format_number(breakthrough_ratio),  # Y轴：穿透率（%）
                    "label": label,  # 按算法格式的标签
                    "time_segment": time_segment,
                    "cumulative_hours": format_number(time_hours),
                    "breakthrough_percent": format_number(breakthrough_ratio),
                    "efficiency": format_number(efficiency),
                    "inlet_concentration": format_number(float(row.get('进口浓度', 0))),
                    "outlet_concentration": format_number(float(row.get('出口浓度', 0))),
                    "calculation_rule": row.get('计算规则', ''),
                    "data_count": int(row.get('数据点数', 1))
                })
            
            # 提取预警点
            warning_points = self._extract_warning_points(processor)
            
            return {
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
            # 检查是否有预警模型并且已拟合
            if hasattr(processor, 'warning_model') and processor.warning_model.fitted:
                model = processor.warning_model
                
                # 数值格式化函数
                def format_number(value):
                    """格式化数值，保留2位小数，接近0则返回0"""
                    if abs(value) < 0.01:  # 小于0.01视为接近0
                        return 0.0
                    return round(value, 2)
                
                # 获取预警时间点（对应图像中的橙色五角星标注）
                if hasattr(model, 'warning_time') and model.warning_time is not None:
                    # 计算预警时间点的穿透率（使用Logistic模型预测）
                    warning_time_seconds = model.warning_time
                    warning_breakthrough = model.predict_breakthrough(np.array([warning_time_seconds]))[0] * 100
                    warning_time_hours = warning_time_seconds / 3600  # 转换为小时
                    
                    warning_points.append({
                        "x": format_number(warning_time_hours),  # X轴：预警时间（小时）
                        "y": format_number(warning_breakthrough),  # Y轴：预警点穿透率（%）
                        "type": "warning_star",
                        "color": "orange",
                        "description": f"预警点(穿透率:{format_number(warning_breakthrough)}%)"
                    })
                
                # 获取预测饱和时间点（对应图像中的红色五角星标注）
                if hasattr(model, 'predicted_saturation_time') and model.predicted_saturation_time is not None:
                    saturation_time_seconds = model.predicted_saturation_time
                    saturation_breakthrough = model.predict_breakthrough(np.array([saturation_time_seconds]))[0] * 100
                    saturation_time_hours = saturation_time_seconds / 3600
                    
                    warning_points.append({
                        "x": format_number(saturation_time_hours),
                        "y": format_number(saturation_breakthrough),
                        "type": "saturation_star",
                        "color": "red",
                        "description": f"预测饱和点(穿透率:{format_number(saturation_breakthrough)}%)"
                    })
                
                # 获取穿透起始时间点（对应图像中的绿色垂直线）
                if hasattr(model, 'breakthrough_start_time') and model.breakthrough_start_time is not None:
                    start_time_seconds = model.breakthrough_start_time
                    start_breakthrough = model.predict_breakthrough(np.array([start_time_seconds]))[0] * 100
                    start_time_hours = start_time_seconds / 3600
                    
                    warning_points.append({
                        "x": format_number(start_time_hours),
                        "y": format_number(start_breakthrough),
                        "type": "breakthrough_start",
                        "color": "green",
                        "description": f"穿透起始点(穿透率:{format_number(start_breakthrough)}%)"
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
        
        # 根据状态返回不同的HTTP状态码
        if result.get("status") == "success":
            # 设置响应头确保中文正确显示
            response = jsonify(result)
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response, 200
        elif result.get("status") == "yichang":
            response = jsonify(result)
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response, 500
        else:  # failure
            response = jsonify(result)
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response, 400
        
    except Exception as e:
        response = jsonify({"error": f"服务器内部错误: {str(e)}"})
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, 500

@app.route('/api/extraction-adsorption-curve/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    response = jsonify({
        "status": "healthy",
        "service": "extraction_adsorption_curve_warning_system",
        "version": "1.0.0"
    })
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

@app.route('/api/extraction-adsorption-curve/info', methods=['GET'])
def api_info():
    """API信息接口"""
    response = jsonify({
        "api_name": "抽取式吸附曲线预警系统",
        "version": "1.0.0",
        "description": "基于现有Adsorption_isotherm.py算法的HTTP接口，处理VOC监测数据并返回可视化坐标点和预警信息",
        "endpoints": {
            "/api/extraction-adsorption-curve/process": {
                "method": "POST",
                "description": "处理抽取式吸附曲线数据，返回数据点坐标和预警点坐标",
                "input_format": {
                    "gVocs": "出口VOC浓度 -> 出口voc列",
                    "inVoc": "进口VOC浓度 -> 进口voc列", 
                    "gWindspeed": "风管内风速 -> 风管内风速值列",
                    "access": "进口(0)或出口(1)或同时(2) -> 进口0出口1列",
                    "createTime": "创建时间 -> 创建时间列",
                    "风量": "自动设置为1.0（算法内部需要，无需用户提供）"
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
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

if __name__ == '__main__':
    print("启动抽取式吸附曲线预警系统...")
    print("API文档: http://localhost:5000/api/extraction-adsorption-curve/info")
    print("健康检查: http://localhost:5000/api/extraction-adsorption-curve/health")
    print("数据处理: POST http://localhost:5000/api/extraction-adsorption-curve/process")
    app.run(debug=True, host='0.0.0.0', port=5000)
