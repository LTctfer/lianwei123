#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的文件播放器
===============

用于播放历史数据文件，支持CSV和Excel格式
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd


class SimpleFilePlayer:
    """
    简化的文件播放器
    
    支持播放CSV和Excel文件，模拟实时数据流
    """
    
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.current_index = 0
        self.file_path: Optional[str] = None
        self.speed_seconds = 2.0  # 播放速度（秒/条）
        self.loop = True  # 是否循环播放
        self.last_play_time = 0
    
    def load_file(self, file_path: str, speed_seconds: float = 2.0, loop: bool = True) -> bool:
        """
        加载数据文件
        
        Args:
            file_path: 文件路径
            speed_seconds: 播放速度（秒/条）
            loop: 是否循环播放
            
        Returns:
            bool: 是否加载成功
        """
        try:
            path = Path(file_path)
            if not path.exists():
                print(f"❌ 文件不存在: {file_path}")
                return False
            
            # 根据文件扩展名选择读取方法
            if path.suffix.lower() == '.csv':
                self.df = pd.read_csv(file_path, encoding='utf-8')
            elif path.suffix.lower() in ['.xlsx', '.xls']:
                self.df = pd.read_excel(file_path)
            else:
                print(f"❌ 不支持的文件格式: {path.suffix}")
                return False
            
            # 处理时间列
            if 'timestamp' in self.df.columns:
                self.df['timestamp'] = pd.to_datetime(self.df['timestamp'], errors='coerce')
            
            # 重置播放状态
            self.current_index = 0
            self.file_path = file_path
            self.speed_seconds = speed_seconds
            self.loop = loop
            self.last_play_time = time.time()
            
            print(f"✅ 文件加载成功: {len(self.df)} 行数据")
            print(f"📄 文件: {path.name}")
            print(f"⏱️ 播放速度: {speed_seconds}秒/条")
            print(f"🔄 循环播放: {'是' if loop else '否'}")
            
            return True
            
        except Exception as e:
            print(f"❌ 文件加载失败: {e}")
            return False
    
    def get_next_data(self) -> Optional[Dict]:
        """
        获取下一条数据
        
        Returns:
            Optional[Dict]: 数据字典，如果没有数据则返回None
        """
        if self.df is None or len(self.df) == 0:
            return None
        
        # 检查播放时间间隔
        current_time = time.time()
        if current_time - self.last_play_time < self.speed_seconds:
            return None
        
        # 检查是否到达文件末尾
        if self.current_index >= len(self.df):
            if self.loop:
                self.current_index = 0  # 重新开始
                print("🔄 文件播放完毕，重新开始循环播放")
            else:
                print("⏹️ 文件播放完毕")
                return None
        
        # 获取当前行数据
        row = self.df.iloc[self.current_index]
        data = row.to_dict()
        
        # 更新时间戳为当前时间
        data['timestamp'] = datetime.now().isoformat()
        
        # 更新播放状态
        self.current_index += 1
        self.last_play_time = current_time
        
        return data
    
    def has_data(self) -> bool:
        """检查是否有数据可播放"""
        return self.df is not None and len(self.df) > 0
    
    def get_progress(self) -> Dict:
        """
        获取播放进度信息
        
        Returns:
            Dict: 进度信息
        """
        if not self.has_data():
            return {
                'current_index': 0,
                'total_rows': 0,
                'progress_percent': 0,
                'file_name': None
            }
        
        return {
            'current_index': self.current_index,
            'total_rows': len(self.df),
            'progress_percent': (self.current_index / len(self.df)) * 100,
            'file_name': Path(self.file_path).name if self.file_path else None
        }
    
    def preview_file(self, file_path: str, rows: int = 5) -> Dict:
        """
        预览文件内容
        
        Args:
            file_path: 文件路径
            rows: 预览行数
            
        Returns:
            Dict: 预览信息
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {'success': False, 'error': f'文件不存在: {file_path}'}
            
            # 读取文件
            if path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8')
            elif path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                return {'success': False, 'error': f'不支持的文件格式: {path.suffix}'}
            
            # 生成预览信息
            preview_data = df.head(rows).to_dict('records')
            
            return {
                'success': True,
                'info': {
                    'filename': path.name,
                    'size': path.stat().st_size,
                    'total_rows': len(df),
                    'columns': list(df.columns)
                },
                'preview': {
                    'headers': list(df.columns),
                    'data': preview_data
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'预览失败: {e}'}
