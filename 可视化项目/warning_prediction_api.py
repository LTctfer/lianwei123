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
    """预警系统预测API包装器"""
    
    def __init__(self):
        self.models = {}  # 存储不同session的预警模型
    
    def process_accumulated_data(self, data_points: list, session_id: str = None) -> dict:
        """
        处理累计数据点，调用预警系统算法
        
        Args:
            data_points: 累计的数据点列表，每个点包含x(时间)和y(穿透率)
            session_id: 会话ID，可选
            
        Returns:
            包含预警点坐标的字典
        """
        try:
            # 1. 验证数据格式
            if not isinstance(data_points, list) or len(data_points) == 0:
                return {"status": "failure", "error": "数据格式错误或为空"}
            
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
                return {"status": "failure", "error": "有效数据点不足，至少需要3个点"}
            
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
                return {"status": "failure", "error": "预警模型拟合失败，数据可能不符合S型曲线特征"}
            
            # 6. 保存模型（如果提供了session_id）
            if session_id:
                self.models[session_id] = warning_model
            
            # 7. 提取预警点
            warning_points = self._extract_warning_points(warning_model)
            
            # 8. 生成额外的预测信息
            model_info = self._extract_model_info(warning_model, time_array, breakthrough_array)
            
            return {
                "status": "success",
                "warning_points": warning_points,
                "model_info": model_info,
                "data_summary": {
                    "input_points": len(time_data),
                    "time_range_hours": {
                        "start": float(time_array[0] / 3600),
                        "end": float(time_array[-1] / 3600)
                    },
                    "breakthrough_range_percent": {
                        "start": float(breakthrough_array[0] * 100),
                        "end": float(breakthrough_array[-1] * 100)
                    }
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": f"预警系统处理失败: {str(e)}"}
    
    def _extract_warning_points(self, warning_model: LogisticWarningModel) -> list:
        """提取预警点坐标（仅返回五角星标记的预警点）"""
        warning_points = []
        
        try:
            # 数值格式化函数
            def format_number(value):
                """格式化数值，保留2位小数"""
                if abs(value) < 0.01:
                    return 0.0
                return round(value, 2)
            
            # 1. 预警点（橙色五角星）
            if hasattr(warning_model, 'warning_time') and warning_model.warning_time is not None:
                warning_time_hours = warning_model.warning_time / 3600
                warning_breakthrough = warning_model.predict_breakthrough(np.array([warning_model.warning_time]))[0] * 100
                
                warning_points.append({
                    "type": "warning_star",
                    "name": "预警点",
                    "x": format_number(warning_time_hours),
                    "y": format_number(warning_breakthrough),
                    "color": "orange",
                    "symbol": "star",
                    "description": f"预警点: {format_number(warning_breakthrough)}%穿透率，建议适时更换"
                })
            
            # 2. 预测饱和点（红色五角星）
            if hasattr(warning_model, 'predicted_saturation_time') and warning_model.predicted_saturation_time is not None:
                saturation_time_hours = warning_model.predicted_saturation_time / 3600
                saturation_breakthrough = warning_model.predict_breakthrough(np.array([warning_model.predicted_saturation_time]))[0] * 100
                
                warning_points.append({
                    "type": "saturation_star",
                    "name": "预测饱和点",
                    "x": format_number(saturation_time_hours),
                    "y": format_number(saturation_breakthrough),
                    "color": "red",
                    "symbol": "star",
                    "description": f"预测饱和点: {format_number(saturation_breakthrough)}%穿透率，建议立即更换"
                })
            
        except Exception as e:
            print(f"预警点提取警告: {e}")
        
        # 按时间排序
        warning_points.sort(key=lambda p: p['x'])
        
        return warning_points
    
    def _extract_model_info(self, warning_model: LogisticWarningModel, time_data: np.array, breakthrough_data: np.array) -> dict:
        """提取模型信息"""
        model_info = {
            "fitted": warning_model.fitted,
            "parameters": {},
            "quality_metrics": {},
            "predictions": {}
        }
        
        try:
            if warning_model.fitted:
                # 模型参数
                model_info["parameters"] = {
                    "A": float(warning_model.A),  # 最大穿透率
                    "k": float(warning_model.k),  # 增长率
                    "t0": float(warning_model.t0)  # 中点时间
                }
                
                # 拟合质量评估
                predicted = warning_model.predict_breakthrough(time_data)
                residuals = breakthrough_data - predicted
                mse = np.mean(residuals ** 2)
                rmse = np.sqrt(mse)
                ss_res = np.sum(residuals ** 2)
                ss_tot = np.sum((breakthrough_data - np.mean(breakthrough_data)) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                
                model_info["quality_metrics"] = {
                    "rmse": float(rmse),
                    "r_squared": float(r_squared),
                    "mean_absolute_error": float(np.mean(np.abs(residuals)))
                }
                
                # 关键时间预测
                if hasattr(warning_model, 'breakthrough_start_time'):
                    model_info["predictions"]["breakthrough_start_hours"] = float(warning_model.breakthrough_start_time / 3600) if warning_model.breakthrough_start_time else None
                if hasattr(warning_model, 'warning_time'):
                    model_info["predictions"]["warning_time_hours"] = float(warning_model.warning_time / 3600) if warning_model.warning_time else None
                if hasattr(warning_model, 'predicted_saturation_time'):
                    model_info["predictions"]["saturation_time_hours"] = float(warning_model.predicted_saturation_time / 3600) if warning_model.predicted_saturation_time else None
                
        except Exception as e:
            model_info["error"] = f"模型信息提取失败: {str(e)}"
        
        return model_info
    
    def get_model_info(self, session_id: str) -> dict:
        """获取已保存的模型信息"""
        if session_id in self.models:
            model = self.models[session_id]
            return {
                "session_id": session_id,
                "exists": True,
                "fitted": model.fitted,
                "model_info": self._extract_model_info(model, np.array([]), np.array([]))
            }
        else:
            return {
                "session_id": session_id,
                "exists": False,
                "fitted": False
            }
    
    def predict_future_points(self, session_id: str, future_hours: list) -> dict:
        """基于已训练模型预测未来时间点的穿透率"""
        if session_id not in self.models:
            return {"status": "failure", "error": f"会话 {session_id} 不存在或模型未训练"}
        
        model = self.models[session_id]
        if not model.fitted:
            return {"status": "failure", "error": "模型未完成拟合"}
        
        try:
            future_seconds = [hour * 3600 for hour in future_hours]
            predicted_ratios = model.predict_breakthrough(np.array(future_seconds))
            
            predictions = []
            for hour, ratio in zip(future_hours, predicted_ratios):
                predictions.append({
                    "time_hours": round(hour, 2),
                    "predicted_breakthrough_percent": round(ratio * 100, 2)
                })
            
            return {
                "status": "success",
                "predictions": predictions,
                "session_id": session_id
            }
            
        except Exception as e:
            return {"status": "error", "error": f"预测失败: {str(e)}"}

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
        "session_id": "可选会话ID",
        "data_points": [
            {"x": 1.5, "y": 12.5},  // x: 累计时间(小时), y: 穿透率(%)
            {"x": 3.0, "y": 25.8},
            ...
        ]
    }
    """
    try:
        request_data = request.get_json(force=True)
        
        if not request_data:
            return create_json_response({"error": "未提供JSON数据"}, 400)
        
        # 提取数据
        session_id = request_data.get('session_id', None)
        data_points = request_data.get('data_points', [])
        
        if not data_points:
            return create_json_response({"error": "未提供数据点"}, 400)
        
        # 处理数据
        result = warning_api.process_accumulated_data(data_points, session_id)
        
        # 返回结果
        if result.get("status") == "success":
            return create_json_response(result, 200)
        elif result.get("status") == "error":
            return create_json_response(result, 500)
        else:  # failure
            return create_json_response(result, 400)
        
    except Exception as e:
        error_result = {"error": f"服务器内部错误: {str(e)}"}
        return create_json_response(error_result, 500)

@app.route('/api/warning-prediction/model/<session_id>', methods=['GET'])
def get_model_info(session_id):
    """获取指定会话的模型信息"""
    try:
        model_info = warning_api.get_model_info(session_id)
        return create_json_response(model_info)
    except Exception as e:
        error_result = {"error": f"获取模型信息失败: {str(e)}"}
        return create_json_response(error_result, 500)

@app.route('/api/warning-prediction/predict', methods=['POST'])
def predict_future():
    """
    基于已训练模型预测未来时间点
    
    请求格式:
    {
        "session_id": "会话ID",
        "future_hours": [10.0, 15.0, 20.0]  // 要预测的未来时间点(小时)
    }
    """
    try:
        request_data = request.get_json(force=True)
        
        if not request_data:
            return create_json_response({"error": "未提供JSON数据"}, 400)
        
        session_id = request_data.get('session_id')
        future_hours = request_data.get('future_hours', [])
        
        if not session_id:
            return create_json_response({"error": "未提供会话ID"}, 400)
        
        if not future_hours:
            return create_json_response({"error": "未提供预测时间点"}, 400)
        
        result = warning_api.predict_future_points(session_id, future_hours)
        
        if result.get("status") == "success":
            return create_json_response(result, 200)
        else:
            return create_json_response(result, 400)
        
    except Exception as e:
        error_result = {"error": f"预测失败: {str(e)}"}
        return create_json_response(error_result, 500)

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
        "version": "1.0.0",
        "description": "基于累计数据点调用预警系统算法，返回预警点坐标",
        "encoding": "UTF-8",
        "endpoints": {
            "/api/warning-prediction/analyze": {
                "method": "POST",
                "description": "分析累计数据点，返回预警点坐标（五角星标记）",
                "input_format": {
                    "session_id": "可选，会话ID",
                    "data_points": "数据点数组，每个点包含x(累计时间小时)和y(穿透率百分比)"
                },
                "output_format": {
                    "warning_points": "预警点数组，仅包含五角星标记的预警点（橙色预警点、红色饱和点）",
                    "model_info": "模型拟合信息和质量评估",
                    "data_summary": "输入数据摘要"
                }
            },
            "/api/warning-prediction/model/<session_id>": {
                "method": "GET",
                "description": "获取指定会话的模型信息"
            },
            "/api/warning-prediction/predict": {
                "method": "POST",
                "description": "基于已训练模型预测未来时间点的穿透率"
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
                "预警点 (橙色五角星)",
                "预测饱和点 (红色五角星)"
            ],
            "note": "仅返回五角星标记的预警点坐标"
        }
    }
    return create_json_response(info_data)

if __name__ == '__main__':
    print("启动预警系统预测接口...")
    print("=" * 60)
    print("📖 API端点:")
    print("  API文档: http://localhost:5001/api/warning-prediction/info")
    print("  健康检查: http://localhost:5001/api/warning-prediction/health")
    print("  预警分析: POST http://localhost:5001/api/warning-prediction/analyze")
    print("  模型信息: GET http://localhost:5001/api/warning-prediction/model/<session_id>")
    print("  未来预测: POST http://localhost:5001/api/warning-prediction/predict")
    print("=" * 60)
    print("🎯 功能说明:")
    print("  1. 接收累计的时间-穿透率数据点")
    print("  2. 调用Logistic预警系统算法进行拟合")
    print("  3. 返回五角星标记的预警点坐标（橙色预警点、红色饱和点）")
    print("  4. 支持模型质量评估和未来预测")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5001)
