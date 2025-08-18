#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预警系统预测接口
基于累计的数据点调用预警系统算法，返回预警点坐标
"""

from flask import Flask, request, jsonify, Response
import pandas as pd
import numpy as np
from datetime import datetime
import json
import sys
import os

# 导入预警系统算法
from Adsorption_isotherm import LogisticWarningModel

app = Flask(__name__)

# 设置JSON编码，确保中文正确显示
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# 设置默认编码
import locale
try:
    locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Chinese_China.65001')  # Windows中文UTF-8
    except:
        pass

class WarningPredictionAPI:
    """预警系统预测API包装器（简化版）"""

    def __init__(self):
        pass  # 简化版不需要存储模型
    
    def process_accumulated_data(self, data_points: list) -> dict:
        """
        处理累计数据点，调用预警系统算法，仅返回预警点坐标

        Args:
            data_points: 累计的数据点列表，每个点包含x(时间)和y(穿透率)

        Returns:
            仅包含预警点坐标的字典
        """
        try:
            # 1. 验证数据格式
            if not isinstance(data_points, list) or len(data_points) == 0:
                return {"error": "数据格式错误或为空"}

            # 2. 提取时间和穿透率数据
            time_data = []
            breakthrough_data = []

            for point in data_points:
                if not isinstance(point, dict):
                    continue

                # 支持多种字段名格式
                x_value = point.get('x') or point.get('time') or point.get('cumulative_time')
                y_value = point.get('y') or point.get('breakthrough_ratio') or point.get('穿透率')

                if x_value is not None and y_value is not None:
                    try:
                        # 时间转换为秒（算法内部使用秒）
                        time_seconds = float(x_value) * 3600  # 小时转秒
                        # 穿透率转换为比例（算法内部使用0-1）
                        breakthrough_ratio = float(y_value) / 100.0  # 百分比转比例

                        time_data.append(time_seconds)
                        breakthrough_data.append(breakthrough_ratio)
                    except (ValueError, TypeError):
                        continue

            if len(time_data) < 3:
                return {"error": "有效数据点不足，至少需要3个点"}

            # 3. 转换为numpy数组
            time_array = np.array(time_data)
            breakthrough_array = np.array(breakthrough_data)

            print(f"处理数据点: {len(time_data)} 个")
            print(f"时间范围: {time_array[0]/3600:.2f}h - {time_array[-1]/3600:.2f}h")
            print(f"穿透率范围: {breakthrough_array[0]*100:.1f}% - {breakthrough_array[-1]*100:.1f}%")

            # 4. 创建预警模型
            warning_model = LogisticWarningModel(
                breakthrough_start_threshold=0.01,  # 1%穿透起始点
                warning_ratio=0.8,                 # 80%预警点
                saturation_threshold=0.9            # 90%饱和点
            )

            # 5. 拟合模型
            if not warning_model.fit_model(time_array, breakthrough_array):
                return {"error": "预警模型拟合失败，数据可能不符合S型曲线特征"}

            # 6. 提取预警点坐标（仅返回XY坐标）
            warning_points = self._extract_warning_points_simple(warning_model)

            return warning_points

        except Exception as e:
            return {"error": f"预警系统处理失败: {str(e)}"}

    def _extract_warning_points_simple(self, warning_model: LogisticWarningModel) -> dict:
        """
        提取预警点坐标（仅返回XY坐标，无额外信息）

        严格按照算法中的定义：
        1. 预测饱和点：模型预测最大穿透率的95%对应的时间点
        2. 预警点：从穿透起始点到预测饱和点时间跨度的80%位置
        """
        warning_points = []

        try:
            # 数值格式化函数
            def format_number(value):
                """格式化数值，保留2位小数"""
                if abs(value) < 0.01:
                    return 0.0
                return round(value, 2)

            # 检查模型是否已拟合
            if not warning_model.fitted:
                print("警告：模型未拟合，无法提取预警点")
                return {"warning_points": warning_points}

            # 检查模型是否已经计算了关键时间点
            if not hasattr(warning_model, 'params') or warning_model.params is None:
                print("警告：模型参数未设置")
                return {"warning_points": warning_points}

            # 如果算法已经计算了关键时间点，直接使用
            if (hasattr(warning_model, 'breakthrough_start_time') and warning_model.breakthrough_start_time is not None and
                hasattr(warning_model, 'predicted_saturation_time') and warning_model.predicted_saturation_time is not None and
                hasattr(warning_model, 'warning_time') and warning_model.warning_time is not None):

                # 1. 预警点（算法已计算）
                warning_time_hours = warning_model.warning_time / 3600
                warning_breakthrough = warning_model.predict_breakthrough(np.array([warning_model.warning_time]))[0] * 100

                warning_points.append({
                    "x": format_number(warning_time_hours),
                    "y": format_number(warning_breakthrough)
                })

                # 2. 预测饱和点（算法已计算）
                saturation_time_hours = warning_model.predicted_saturation_time / 3600
                saturation_breakthrough = warning_model.predict_breakthrough(np.array([warning_model.predicted_saturation_time]))[0] * 100

                warning_points.append({
                    "x": format_number(saturation_time_hours),
                    "y": format_number(saturation_breakthrough)
                })

                print(f"使用算法计算的关键时间点:")
                print(f"  起始时间: {warning_model.breakthrough_start_time/3600:.2f}h")
                print(f"  预警时间: {warning_time_hours:.2f}h (时间跨度的{warning_model.warning_ratio:.0%})")
                print(f"  饱和时间: {saturation_time_hours:.2f}h (模型最大值的95%)")

            else:
                print("警告：算法未计算关键时间点，无法提取预警点")

        except Exception as e:
            print(f"预警点提取警告: {e}")
            import traceback
            traceback.print_exc()

        # 按时间排序
        warning_points.sort(key=lambda p: p['x'])

        return {"warning_points": warning_points}

# 移除了原始的复杂预警点提取方法
    
# 移除了不需要的辅助方法，简化代码结构

def create_json_response(data, status_code=200):
    """创建UTF-8编码的JSON响应"""
    try:
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        response = Response(
            json_str,
            status=status_code,
            mimetype='application/json; charset=utf-8'
        )
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.headers['Cache-Control'] = 'no-cache'
        return response
    except Exception as e:
        error_data = {"error": f"响应编码错误: {str(e)}"}
        error_json = json.dumps(error_data, ensure_ascii=False)
        return Response(
            error_json,
            status=500,
            mimetype='application/json; charset=utf-8'
        )

# 创建API实例
warning_api = WarningPredictionAPI()

@app.route('/api/warning-prediction/analyze', methods=['POST'])
def analyze_warning_points():
    """
    分析累计数据点，返回预警点坐标

    请求格式:
    {
        "data_points": [
            {"x": 1.5, "y": 12.5},  // x: 累计时间(小时), y: 穿透率(%)
            {"x": 3.0, "y": 25.8},
            ...
        ]
    }

    响应格式:
    {
        "warning_points": [
            {"x": 6.25, "y": 80.0},  // 预警点
            {"x": 8.45, "y": 90.0}   // 饱和点
        ]
    }
    """
    try:
        request_data = request.get_json(force=True)

        if not request_data:
            return create_json_response({"error": "未提供JSON数据"}, 400)

        # 提取数据点
        data_points = request_data.get('data_points', [])

        if not data_points:
            return create_json_response({"error": "未提供数据点"}, 400)

        # 处理数据，获取预警点坐标
        result = warning_api.process_accumulated_data(data_points)

        # 检查是否有错误
        if "error" in result:
            return create_json_response(result, 400)

        # 返回预警点坐标
        return create_json_response(result, 200)

    except Exception as e:
        error_result = {"error": f"服务器内部错误: {str(e)}"}
        return create_json_response(error_result, 500)

# 移除了不需要的辅助接口，只保留核心预警点分析功能

@app.route('/api/warning-prediction/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    health_data = {
        "status": "healthy",
        "service": "warning_prediction_system",
        "version": "1.0.0",
        "encoding": "UTF-8"
    }
    return create_json_response(health_data)

@app.route('/api/warning-prediction/info', methods=['GET'])
def api_info():
    """API信息接口"""
    info_data = {
        "api_name": "预警系统预测接口",
        "version": "2.0.0",
        "description": "基于累计数据点调用预警系统算法，仅返回预警点XY坐标",
        "encoding": "UTF-8",
        "endpoints": {
            "/api/warning-prediction/analyze": {
                "method": "POST",
                "description": "分析累计数据点，仅返回预警点XY坐标（五角星标记）",
                "input_format": {
                    "data_points": "数据点数组，每个点包含x(累计时间小时)和y(穿透率百分比)"
                },
                "output_format": {
                    "warning_points": "预警点坐标数组，每个点仅包含x(小时)和y(百分比)"
                },
                "example_request": {
                    "data_points": [
                        {"x": 1.5, "y": 12.5},
                        {"x": 3.0, "y": 25.8},
                        {"x": 4.5, "y": 45.2},
                        {"x": 6.0, "y": 68.5}
                    ]
                },
                "example_response": {
                    "warning_points": [
                        {"x": 6.25, "y": 80.0},
                        {"x": 8.45, "y": 90.0}
                    ]
                }
            },
            "/api/warning-prediction/health": {
                "method": "GET",
                "description": "健康检查"
            },
            "/api/warning-prediction/info": {
                "method": "GET",
                "description": "API信息"
            }
        },
        "algorithm_info": {
            "model": "Logistic回归模型",
            "curve_type": "S型穿透曲线",
            "warning_types": [
                "预警点 (从起始到饱和时间跨度的80%位置)",
                "预测饱和点 (模型预测最大穿透率95%对应的时间点)"
            ],
            "calculation_formulas": {
                "预测饱和时间": "t0 - ln(A / (A*0.95) - 1) / k",
                "预警时间": "起始时间 + (饱和时间 - 起始时间) × 0.8",
                "参数说明": "A=最大穿透率, k=增长率, t0=中点时间"
            },
            "example": {
                "描述": "起始时间0h，预测饱和时间9h",
                "预警时间": "0 + (9-0) × 0.8 = 7.2h",
                "饱和点": "基于Logistic模型参数计算，非固定穿透率"
            },
            "note": "严格按照算法中的定义计算，仅返回XY坐标"
        }
    }
    return create_json_response(info_data)

if __name__ == '__main__':
    print("启动预警系统预测接口（简化版）...")
    print("=" * 60)
    print("📖 API端点:")
    print("  API文档: http://localhost:5001/api/warning-prediction/info")
    print("  健康检查: http://localhost:5001/api/warning-prediction/health")
    print("  预警分析: POST http://localhost:5001/api/warning-prediction/analyze")
    print("=" * 60)
    print("🎯 功能说明:")
    print("  1. 接收累计的时间-穿透率数据点")
    print("  2. 调用Logistic预警系统算法进行拟合")
    print("  3. 严格按照算法定义计算预警点和饱和点")
    print("  4. 预测饱和点：模型预测最大穿透率95%对应的时间点")
    print("  5. 预警点：从起始到饱和时间跨度的80%位置")
    print("  6. 仅返回预警点XY坐标（X轴：小时，Y轴：百分比）")
    print("=" * 60)
    print("📝 请求示例:")
    print('  POST /api/warning-prediction/analyze')
    print('  {')
    print('    "data_points": [')
    print('      {"x": 1.5, "y": 12.5},')
    print('      {"x": 3.0, "y": 25.8},')
    print('      {"x": 4.5, "y": 45.2}')
    print('    ]')
    print('  }')
    print("=" * 60)
    print("📤 响应示例:")
    print('  {')
    print('    "warning_points": [')
    print('      {"x": 7.2, "y": 75.3},   // 预警点(时间跨度80%位置)')
    print('      {"x": 9.0, "y": 88.5}    // 饱和点')
    print('    ]')
    print('  }')
    print("💡 算法说明:")
    print("   饱和点=模型最大穿透率95%的时间点(非固定穿透率)")
    print("   预警点=起始+(饱和-起始)×0.8 (时间跨度80%位置)")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5001)
