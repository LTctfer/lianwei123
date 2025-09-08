#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件数据播放器
支持CSV和XLSX文件的读取、预览和播放功能
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import json

class FilePreview:
    """文件预览功能"""
    
    @staticmethod
    def get_preview(file_path: str, max_rows: int = 5) -> Dict[str, Any]:
        """获取文件预览信息
        
        Args:
            file_path: 文件路径
            max_rows: 预览的最大行数
            
        Returns:
            包含预览信息的字典:
            - success: 是否成功
            - error: 错误信息(如果有)
            - info: 文件基本信息
            - preview: 预览数据(表头和前几行)
        """
        try:
            p = Path(file_path)
            if not p.exists():
                return {"success": False, "error": f"文件不存在: {file_path}"}
            
            # 读取文件
            if str(p).lower().endswith('.csv'):
                df = pd.read_csv(p, encoding='utf-8', nrows=max_rows+1)
            elif str(p).lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(p, nrows=max_rows+1)
            else:
                return {"success": False, "error": f"不支持的文件类型: {p.suffix}"}
            
            # 基本信息
            info = {
                "filename": p.name,
                "size": p.stat().st_size,
                "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                "total_rows": len(pd.read_csv(p, encoding='utf-8') if str(p).lower().endswith('.csv') else pd.read_excel(p)),
                "columns": list(df.columns),
                "dtypes": df.dtypes.astype(str).to_dict()
            }
            
            # 预览数据
            preview = {
                "headers": list(df.columns),
                "data": df.head(max_rows).to_dict('records')
            }
            
            return {
                "success": True,
                "info": info,
                "preview": preview
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

class FileDataPlayer:
    """文件数据播放器"""
    
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.file_path: Optional[str] = None
        self.index: int = 0
        self.loop: bool = True
        self.speed_seconds: float = 2.0
        self.last_emit_time: Optional[datetime] = None
        self._preview = FilePreview()
        
    def preview_file(self, path: str, max_rows: int = 5) -> Dict[str, Any]:
        """预览文件内容"""
        return self._preview.get_preview(path, max_rows)
    
    def load_file(self, path: str, speed_seconds: float = 2.0, loop: bool = True) -> Tuple[bool, str]:
        """加载数据文件
        
        Args:
            path: 文件路径
            speed_seconds: 每条记录播放间隔(秒)
            loop: 是否循环播放
            
        Returns:
            (成功标志, 消息)元组
        """
        try:
            p = Path(path)
            if not p.exists():
                return False, f"文件不存在: {path}"
                
            # 读取文件
            if str(p).lower().endswith('.csv'):
                df = pd.read_csv(p, encoding='utf-8')
            elif str(p).lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(p)
            else:
                return False, f"不支持的文件类型: {p.suffix}"
            
            # 规范化时间列
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            else:
                df['timestamp'] = pd.date_range(start=datetime.now(), periods=len(df), freq='1min')
            
            # 规范化数据列
            for col in df.columns:
                if col != 'timestamp' and df[col].dtype.name not in ('float64', 'int64'):
                    try:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    except:
                        continue
            
            self.df = df.reset_index(drop=True)
            self.file_path = str(p)
            self.index = 0
            self.loop = bool(loop)
            self.speed_seconds = max(0.1, float(speed_seconds))
            self.last_emit_time = None
            
            return True, f"已加载 {len(self.df)} 行数据: {self.file_path}"
            
        except Exception as e:
            return False, f"加载失败: {e}"
    
    def has_data(self) -> bool:
        """是否有可用数据"""
        return self.df is not None and len(self.df) > 0
    
    def get_next(self) -> Optional[Dict[str, Any]]:
        """获取下一条记录"""
        if not self.has_data():
            return None
            
        now = datetime.now()
        if self.last_emit_time is not None:
            if (now - self.last_emit_time).total_seconds() < self.speed_seconds:
                return None
        
        if self.index >= len(self.df):
            if self.loop:
                self.index = 0
            else:
                self.last_emit_time = now
                return None
        
        row = self.df.iloc[self.index].to_dict()
        
        # 规范字段名
        standard_fields = {
            'temperature_combustion': 'temperature_combustion',
            'temperature_outlet': 'temperature_outlet', 
            'concentration_in': 'concentration_in',
            'concentration_out': 'concentration_out',
            'temperature_adsorption': 'temperature_adsorption',
            'temperature_desorption': 'temperature_desorption',
            'temperature_reactor_outlet': 'temperature_reactor_outlet',
            'pressure': 'pressure',
            'flow_rate': 'flow_rate',
            'efficiency': 'efficiency',
            'emergency_valve': 'emergency_valve',
            'pressure_loss_catalytic': 'pressure_loss_catalytic',
            'particle_content': 'particle_content'
        }
        
        # 自动映射字段
        for standard, field in standard_fields.items():
            # 尝试多种可能的命名
            variants = [
                field,  # 标准名
                field.upper(),  # 大写
                field.lower(),  # 小写
                field.replace('_', ''),  # 无下划线
                ''.join(w.capitalize() for w in field.split('_')),  # 驼峰
                field.replace('temperature_', 'temp_'),  # 简写
                field.replace('temperature_', 'T_'),
                field.replace('concentration_', 'conc_'),
                field.replace('pressure_loss_', 'dp_'),
            ]
            
            # 查找第一个匹配的变体
            for var in variants:
                if var in self.df.columns:
                    row[standard] = row.get(var)
                    break
            else:
                # 未找到匹配，使用默认值
                row.setdefault(standard, 0)
        
        row['timestamp'] = row.get('timestamp', datetime.now())
        
        self.index += 1
        self.last_emit_time = now
        return row
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        if not self.has_data():
            return {
                "loaded": False,
                "file_path": None,
                "total_rows": 0,
                "current_index": 0,
                "loop": self.loop,
                "speed": self.speed_seconds
            }
        
        return {
            "loaded": True,
            "file_path": self.file_path,
            "total_rows": len(self.df),
            "current_index": self.index,
            "loop": self.loop,
            "speed": self.speed_seconds,
            "columns": list(self.df.columns)
        }
        
    def reset(self):
        """重置播放器"""
        self.index = 0
        self.last_emit_time = None
