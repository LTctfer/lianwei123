import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import os
import warnings
warnings.filterwarnings('ignore')

# 宁波世贸字段按炉号的列名模板（匹配 20250101.csv 列名）
def get_field_mapping_for_furnace(furnace_no: int) -> Dict[str, str]:
    prefix = f"{furnace_no}号炉"
    return {
        "upper_temp": f"{prefix}炉膛上部温度",
        "middle_temp": f"{prefix}炉膛中部温度",
        "bag_pressure": f"{prefix}布袋进出口压差",
        "o2": f"{prefix}O2",
        "dust": f"{prefix}粉尘",
        "so2": f"{prefix}SO2",
        "nox": f"{prefix}Nox",
        "co": f"{prefix}CO",
        "hcl": f"{prefix}HCL",
        "carbon": f"{prefix}活性炭喷射量",
    }

# 建德数据字段映射 (基于实际CSV文件的列名)
JIANDE_FIELD_MAPPING = {
    "furnace_temp_points": [
        "上部烟气温度左", "上部烟气温度中", "上部烟气温度右",  # 上部断面
        "中部烟气温度左", "中部烟气温度中", "中部烟气温度右",  # 中部断面
        "下部烟气温度左", "下部烟气温度中", "下部烟气温度右"   # 下部断面
    ],
    "furnace_temp_1": "上部烟气温度左",
    "furnace_temp_2": "上部烟气温度中",
    "furnace_temp_3": "上部烟气温度右",
    "furnace_temp_4": "中部烟气温度左",
    "furnace_temp_5": "中部烟气温度中",
    "furnace_temp_6": "中部烟气温度右",
    "furnace_temp_7": "下部烟气温度左",
    "furnace_temp_8": "下部烟气温度中",
    "furnace_temp_9": "下部烟气温度右",
    "bag_pressure": "除尘器差压",
    "o2": "烟气氧量",
    "dust": "烟气烟尘",
    "so2": "SO2浓度",
    "nox": "NOX浓度",
    "co": "CO浓度",
    "hcl": "HCL浓度",
}

# 预警阈值配置（宁波世贸）
NINGBO_WARNING_THRESHOLDS = {
    "low_furnace_temp": 850,
    "high_furnace_temp": 1200,
    "very_high_furnace_temp": 1300,
    "bag_pressure_high": 2000,
    "bag_pressure_low": 500,
    "o2_high": 10,
    "o2_low": 6,
    "dust_warning_limit": 30,
    "nox_warning_limit": 300,
    "so2_warning_limit": 100,
    "hcl_warning_limit": 60,
    "co_warning_limit": 100,
    "activated_carbon_low": 3.0,    # 活性炭投加量不足(kg/h)
    "nh3_warning_limit": 8          # 氨逃逸偏高(ppm)
}

# 报警阈值配置（宁波世贸）- 根据报警规则文件更新
NINGBO_ALARM_THRESHOLDS = {
    "low_furnace_temp": 850,        # 低炉温焚烧报警
    "dust_alarm_limit": 20,         # 颗粒物(PM)排放超标(日均值)
    "nox_alarm_limit": 250,         # 氮氧化物(NOx)排放超标(日均值)
    "so2_alarm_limit": 80,          # 二氧化硫(SO₂)排放超标(日均值)
    "hcl_alarm_limit": 50,          # 氯化氢(HCl)排放超标(日均值)
    "co_alarm_limit": 80,           # 一氧化碳(CO)排放超标(日均值)
}

class WasteIncinerationWarningSystemNingbo:
    """垃圾焚烧预警/报警系统 - 宁波世贸 (支持3-6号炉)"""

    def __init__(self):
        self.warning_events = []
        self.warning_status = {}
        self.furnace_list = [3, 4, 5, 6]

    def load_data(self, file_path: str) -> pd.DataFrame:
        """加载数据文件 (支持csv和xlsx)"""
        try:
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8-sig')
            else:
                raise ValueError("不支持的文件格式，请使用csv或xlsx文件")

            # 转换时间列
            if '数据时间' in df.columns:
                df['数据时间'] = pd.to_datetime(df['数据时间'])

            # 基础清理：仅将时间转为时间戳，数值列在用到时按列转换
            df = df.copy()

            print(f"成功加载数据文件: {file_path}")
            print(f"数据行数: {len(df)}, 列数: {len(df.columns)}")
            return df

        except Exception as e:
            print(f"加载数据文件失败: {e}")
            return pd.DataFrame()

    def clean_numeric_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """兼容旧调用，现不做全局清洗。"""
        return df

    def _coerce_numeric(self, series: pd.Series) -> pd.Series:
        """将列安全转换为数值，无法转换的设为NaN，保留原长度。"""
        s = series.astype(str)
        s = s.replace({'--': '0', 'nan': '0'})
        s = s.str.extract(r'(-?\d+\.?\d*)', expand=False)
        s = pd.to_numeric(s, errors='coerce')
        return s

    def calculate_furnace_temperature(self, df: pd.DataFrame, furnace_no: int) -> pd.Series:
        """计算某炉的代表温度（上部与中部两个测点的平均）。返回 Series。"""
        mapping = get_field_mapping_for_furnace(furnace_no)
        upper_col = mapping["upper_temp"]
        middle_col = mapping["middle_temp"]
        if upper_col not in df.columns or middle_col not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index, name=f"furnace_temp_{furnace_no}")
        upper = self._coerce_numeric(df[upper_col])
        middle = self._coerce_numeric(df[middle_col])
        temp = (upper + middle) / 2.0
        temp.name = f"furnace_temp_{furnace_no}"
        return temp

    def calculate_time_windows(self, df: pd.DataFrame, window_type: str = '5min') -> pd.DataFrame:
        """计算时间窗口数据 (5分钟、1小时、24小时)"""
        if '数据时间' not in df.columns:
            return df

        df_copy = df.copy()
        df_copy.set_index('数据时间', inplace=True)

        # 只选择数值列进行重采样
        numeric_cols = df_copy.select_dtypes(include=[np.number]).columns
        df_numeric = df_copy[numeric_cols]

        if window_type == '5min':
            # 5分钟窗口
            resampled = df_numeric.resample('5T').mean()
        elif window_type == '1hour':
            # 1小时窗口
            resampled = df_numeric.resample('1H').mean()
        elif window_type == '1day' or window_type == '24hour':
            # 24小时窗口（日均值）
            resampled = df_numeric.resample('24H').mean()
        else:
            return df

        resampled.reset_index(inplace=True)
        return resampled

    def check_low_furnace_temp_warning(self, df: pd.DataFrame) -> List[Dict]:
        """各炉5分钟均值低于850℃预警"""
        events: List[Dict] = []
        df_temp = df.copy()
        for fn in self.furnace_list:
            df_temp[f"furnace_temp_{fn}"] = self.calculate_furnace_temperature(df_temp, fn)
        df_temp.set_index('数据时间', inplace=True)
        df_5min = df_temp[[c for c in df_temp.columns if str(c).startswith('furnace_temp_')]].resample('5T').mean().reset_index()
        for fn in self.furnace_list:
            col = f"furnace_temp_{fn}"
            if col not in df_5min.columns:
                continue
            mask = df_5min[col] < NINGBO_WARNING_THRESHOLDS['low_furnace_temp']
            for _, row in df_5min[mask].iterrows():
                events.append({
                    '时间': row['数据时间'],
                    '炉号': str(fn),
                    '预警/报警类型': '预警',
                    '预警/报警事件': '瞬时低炉温焚烧',
                    '预警/报警区分': '预警'
                })
        return events

    def check_low_furnace_temp_alarm(self, df: pd.DataFrame) -> List[Dict]:
        """各炉5分钟均值低于850℃报警"""
        events: List[Dict] = []
        df_temp = df.copy()
        for fn in self.furnace_list:
            df_temp[f"furnace_temp_{fn}"] = self.calculate_furnace_temperature(df_temp, fn)
        df_temp.set_index('数据时间', inplace=True)
        df_5min = df_temp[[c for c in df_temp.columns if str(c).startswith('furnace_temp_')]].resample('5T').mean().reset_index()
        for fn in self.furnace_list:
            col = f"furnace_temp_{fn}"
            if col not in df_5min.columns:
                continue
            mask = df_5min[col] < NINGBO_ALARM_THRESHOLDS['low_furnace_temp']
            for _, row in df_5min[mask].iterrows():
                events.append({
                    '时间': row['数据时间'],
                    '炉号': str(fn),
                    '预警/报警类型': '报警',
                    '预警/报警事件': '低炉温焚烧',
                    '预警/报警区分': '报警'
                })
        return events

    def check_pollutant_daily_alarm(self, df: pd.DataFrame) -> List[Dict]:
        """各炉污染物日均值排放超标报警（折算后）"""
        alarms: List[Dict] = []

        # 按日期分组计算日均值
        df_daily = self.calculate_time_windows(df, '1day')

        # 过滤掉含有0值的记录
        df_daily = df_daily[(df_daily != 0).all(axis=1)]

        # 检查各种污染物日均值（需要进行折算）
        pollutants = {
            'dust': ('烟气中颗粒物（PM）排放超标', 'dust_alarm_limit'),
            'nox': ('烟气中氮氧化物（NOx）排放超标', 'nox_alarm_limit'),
            'so2': ('烟气中二氧化硫（SO₂）排放超标', 'so2_alarm_limit'),
            'hcl': ('烟气中氯化氢（HCl）排放超标', 'hcl_alarm_limit'),
            'co': ('烟气中一氧化碳（CO）排放超标', 'co_alarm_limit')
        }

        # 此处保留旧结构，但将按炉号处理（见后续重写版本）

        # 使用新逻辑（按炉号与点位映射）
        alarms = []
        for fn in self.furnace_list:
            fmap = get_field_mapping_for_furnace(fn)
            o2_col = fmap['o2']
            if o2_col not in df.columns:
                continue
            df_num = pd.DataFrame({'数据时间': df['数据时间']})
            df_num[o2_col] = self._coerce_numeric(df[o2_col])
            for p_key, _ in pollutants.items():
                p_col = fmap[p_key]
                if p_col in df.columns:
                    df_num[p_col] = self._coerce_numeric(df[p_col])
            df_num = df_num.set_index('数据时间')
            df_daily = df_num.resample('24H').mean().reset_index()
            for p_key, (event_name, threshold_key) in pollutants.items():
                p_col = fmap.get(p_key)
                if p_col not in df_daily.columns:
                    continue
                corrected = self.calculate_corrected_concentration(df_daily[p_col], df_daily[o2_col])
                threshold = NINGBO_ALARM_THRESHOLDS[threshold_key]
                mask = corrected > threshold
                for _, row in df_daily[mask].iterrows():
                                alarms.append({
                        '时间': row['数据时间'],
                        '炉号': str(fn),
                                    '预警/报警类型': '报警',
                                    '预警/报警事件': event_name,
                                    '预警/报警区分': '报警'
                                })

        return alarms

    def check_high_furnace_temp_warning(self, df: pd.DataFrame) -> List[Dict]:
        """各炉1小时平均温度>1200/1300℃ 预警"""
        warnings: List[Dict] = []

        df_temp = df.copy()
        for fn in self.furnace_list:
            df_temp[f"furnace_temp_{fn}"] = self.calculate_furnace_temperature(df_temp, fn)
        df_temp.set_index('数据时间', inplace=True)
        df_1h = df_temp[[c for c in df_temp.columns if str(c).startswith('furnace_temp_')]].resample('1H').mean().reset_index()
        for fn in self.furnace_list:
            col = f"furnace_temp_{fn}"
            if col not in df_1h.columns:
                continue
            very_high = df_1h[col] > NINGBO_WARNING_THRESHOLDS['very_high_furnace_temp']
            high = (df_1h[col] > NINGBO_WARNING_THRESHOLDS['high_furnace_temp']) & (~very_high)
            for _, row in df_1h[very_high].iterrows():
            warnings.append({
                '时间': row['数据时间'],
                    '炉号': str(fn),
                '预警/报警类型': '预警',
                '预警/报警事件': '炉膛温度过高',
                '预警/报警区分': '预警'
            })
            for _, row in df_1h[high].iterrows():
            warnings.append({
                '时间': row['数据时间'],
                    '炉号': str(fn),
                '预警/报警类型': '预警',
                '预警/报警事件': '炉膛温度偏高',
                '预警/报警区分': '预警'
            })
        return warnings

    def check_bag_pressure_warning(self, df: pd.DataFrame) -> List[Dict]:
        """各炉布袋除尘器压力损失偏高/偏低 预警（实时进入-退出事件）"""
        warnings: List[Dict] = []

        # 按时间排序确保正确的状态跟踪
        df_sorted = df.sort_values('数据时间')

        for fn in self.furnace_list:
            fmap = get_field_mapping_for_furnace(fn)
            pressure_field = fmap['bag_pressure']
            if pressure_field not in df_sorted.columns:
                continue
            series = self._coerce_numeric(df_sorted[pressure_field])
            high_start = None
            low_start = None
            for t, val in zip(df_sorted['数据时间'], series):
                if pd.isna(val):
                    continue
                if val > NINGBO_WARNING_THRESHOLDS['bag_pressure_high']:
                    if high_start is None:
                        high_start = t
                elif high_start is not None:
                    warnings.append({
                        '时间': high_start,
                        '炉号': str(fn),
                        '预警/报警类型': '预警',
                        '预警/报警事件': '布袋除尘器压力损失偏高',
                        '预警/报警区分': '预警'
                    })
                    high_start = None
                if val < NINGBO_WARNING_THRESHOLDS['bag_pressure_low']:
                    if low_start is None:
                        low_start = t
                elif low_start is not None:
                    warnings.append({
                        '时间': low_start,
                        '炉号': str(fn),
                        '预警/报警类型': '预警',
                        '预警/报警事件': '布袋除尘器压力损失偏低',
                        '预警/报警区分': '预警'
                    })
                    low_start = None
            if high_start is not None:
                warnings.append({
                    '时间': high_start,
                    '炉号': str(fn),
                    '预警/报警类型': '预警',
                    '预警/报警事件': '布袋除尘器压力损失偏高',
                    '预警/报警区分': '预警'
                })
            if low_start is not None:
                warnings.append({
                    '时间': low_start,
                    '炉号': str(fn),
                '预警/报警类型': '预警',
                '预警/报警事件': '布袋除尘器压力损失偏低',
                '预警/报警区分': '预警'
            })

        return warnings

    def check_o2_warning(self, df: pd.DataFrame) -> List[Dict]:
        """各炉焚烧炉出口氧含量偏高/偏低 预警（实时进入-退出事件）"""
        warnings: List[Dict] = []

        # 按时间排序确保正确的状态跟踪
        df_sorted = df.sort_values('数据时间')

        for fn in self.furnace_list:
            fmap = get_field_mapping_for_furnace(fn)
            o2_field = fmap['o2']
            if o2_field not in df_sorted.columns:
                continue
            series = self._coerce_numeric(df_sorted[o2_field])
            high_start = None
            low_start = None
            for t, val in zip(df_sorted['数据时间'], series):
                if pd.isna(val):
                    continue
                if val > NINGBO_WARNING_THRESHOLDS['o2_high']:
                    if high_start is None:
                        high_start = t
                elif high_start is not None:
                    warnings.append({
                        '时间': high_start,
                        '炉号': str(fn),
                        '预警/报警类型': '预警',
                        '预警/报警事件': '焚烧炉出口氧含量偏高',
                        '预警/报警区分': '预警'
                    })
                    high_start = None
                if val < NINGBO_WARNING_THRESHOLDS['o2_low']:
                    if low_start is None:
                        low_start = t
                elif low_start is not None:
                    warnings.append({
                        '时间': low_start,
                        '炉号': str(fn),
                        '预警/报警类型': '预警',
                        '预警/报警事件': '焚烧炉出口氧含量偏低',
                        '预警/报警区分': '预警'
                    })
                    low_start = None
            if high_start is not None:
                warnings.append({
                    '时间': high_start,
                    '炉号': str(fn),
                    '预警/报警类型': '预警',
                    '预警/报警事件': '焚烧炉出口氧含量偏高',
                    '预警/报警区分': '预警'
                })
            if low_start is not None:
                warnings.append({
                    '时间': low_start,
                    '炉号': str(fn),
                    '预警/报警类型': '预警',
                    '预警/报警事件': '焚烧炉出口氧含量偏低',
                    '预警/报警区分': '预警'
                })

        return warnings

    def check_activated_carbon_warning(self, df: pd.DataFrame) -> List[Dict]:
        """各炉活性炭投加量不足预警（实时监控）"""
        warnings: List[Dict] = []
        
        for fn in self.furnace_list:
            col = f"{fn}号炉活性炭喷射量"
            if col not in df.columns:
                continue
                
            df_sorted = df.sort_values('数据时间')
            series = df_sorted[col]
            
            # 实时监控活性炭投加量
            low_start = None
            for t, val in zip(df_sorted['数据时间'], series):
                if pd.isna(val):
                    continue
                if val < NINGBO_WARNING_THRESHOLDS['activated_carbon_low']:
                    if low_start is None:
                        low_start = t
                elif low_start is not None:
                    warnings.append({
                        '时间': low_start,
                        '炉号': str(fn),
                        '预警/报警类型': '预警',
                        '预警/报警事件': '活性炭投加量不足',
                        '预警/报警区分': '预警'
                    })
                    low_start = None
            
            # 处理未结束的预警
            if low_start is not None:
            warnings.append({
                    '时间': low_start,
                    '炉号': str(fn),
                '预警/报警类型': '预警',
                    '预警/报警事件': '活性炭投加量不足',
                '预警/报警区分': '预警'
            })

        return warnings

    def check_nh3_warning(self, df: pd.DataFrame) -> List[Dict]:
        """氨逃逸偏高预警（仅3号炉和6号炉有此监测点）"""
        warnings: List[Dict] = []
        
        # 根据点位表，只有3号炉和6号炉有氨逃逸监测
        for fn in ["3", "6"]:
            col = f"{fn}号炉氨逃逸量"
            if col not in df.columns:
                continue
                
            # 计算小时均值
            df_temp = df.copy()
            df_temp['数据时间'] = pd.to_datetime(df_temp['数据时间'])
            df_temp.set_index('数据时间', inplace=True)
            
            df_1h = df_temp[[col]].resample('1H').mean().reset_index()
            
            # 检查超标
            for _, row in df_1h.iterrows():
                if pd.isna(row[col]):
                    continue
                if row[col] > NINGBO_WARNING_THRESHOLDS['nh3_warning_limit']:
            warnings.append({
                        '时间': row['数据时间'],
                        '炉号': str(fn),
                '预警/报警类型': '预警',
                        '预警/报警事件': '氨逃逸偏高',
                '预警/报警区分': '预警'
            })

        return warnings

    def calculate_corrected_concentration(self, measured_conc, measured_o2):
        """计算标准状态下的浓度（折算）"""
        # ρ（标准）=ρ（实测）*10/(21-ρ（实测O2））
        corrected = measured_conc * 10 / (21 - measured_o2)
        return corrected

    def check_pollutant_warning(self, df: pd.DataFrame) -> List[Dict]:
        """各炉污染物小时均值预警（折算后）"""
        warnings: List[Dict] = []
        pollutants = {
            'dust': ('烟气中颗粒物（PM）浓度较高', 'dust_warning_limit'),
            'nox': ('烟气中氮氧化物（NOx）浓度较高', 'nox_warning_limit'),
            'so2': ('烟气中二氧化硫（SO₂）浓度较高', 'so2_warning_limit'),
            'hcl': ('烟气中氯化氢（HCl）浓度较高', 'hcl_warning_limit'),
            'co': ('烟气中一氧化碳（CO）浓度较高', 'co_warning_limit')
        }
        for fn in self.furnace_list:
            fmap = get_field_mapping_for_furnace(fn)
            o2_col = fmap['o2']
            if o2_col not in df.columns:
                continue
            df_num = pd.DataFrame({'数据时间': df['数据时间']})
            df_num[o2_col] = self._coerce_numeric(df[o2_col])
            for p_key, _ in pollutants.items():
                p_col = fmap[p_key]
                if p_col in df.columns:
                    df_num[p_col] = self._coerce_numeric(df[p_col])
            df_num = df_num.set_index('数据时间')
            df_1h = df_num.resample('1H').mean().reset_index()
            for p_key, (event_name, thresh_key) in pollutants.items():
                p_col = fmap.get(p_key)
                if p_col not in df_1h.columns:
                    continue
                corrected = self.calculate_corrected_concentration(df_1h[p_col], df_1h[o2_col])
                threshold = NINGBO_WARNING_THRESHOLDS[thresh_key]
                mask = corrected > threshold
                for _, row in df_1h[mask].iterrows():
                                warnings.append({
                        '时间': row['数据时间'],
                        '炉号': str(fn),
                                    '预警/报警类型': '预警',
                                    '预警/报警事件': event_name,
                                    '预警/报警区分': '预警'
                                })
        return warnings

    def check_pollutant_alarm(self, df: pd.DataFrame) -> List[Dict]:
        """各炉污染物日均值排放超标报警（折算后）"""
        alarms: List[Dict] = []
        pollutants = {
            'dust': ('烟气中颗粒物（PM）排放超标', 'dust_alarm_limit'),
            'nox': ('烟气中氮氧化物（NOx）排放超标', 'nox_alarm_limit'),
            'so2': ('烟气中二氧化硫（SO₂）排放超标', 'so2_alarm_limit'),
            'hcl': ('烟气中氯化氢（HCl）排放超标', 'hcl_alarm_limit'),
            'co': ('烟气中一氧化碳（CO）排放超标', 'co_alarm_limit')
        }
        for fn in self.furnace_list:
            fmap = get_field_mapping_for_furnace(fn)
            o2_col = fmap['o2']
            if o2_col not in df.columns:
                continue
            df_num = pd.DataFrame({'数据时间': df['数据时间']})
            df_num[o2_col] = self._coerce_numeric(df[o2_col])
            for p_key, _ in pollutants.items():
                p_col = fmap[p_key]
                if p_col in df.columns:
                    df_num[p_col] = self._coerce_numeric(df[p_col])
            df_num = df_num.set_index('数据时间')
            df_daily = df_num.resample('24H').mean().reset_index()
            for p_key, (event_name, threshold_key) in pollutants.items():
                p_col = fmap.get(p_key)
                if p_col not in df_daily.columns:
                    continue
                corrected = self.calculate_corrected_concentration(df_daily[p_col], df_daily[o2_col])
                threshold = NINGBO_ALARM_THRESHOLDS[threshold_key]
                mask = corrected > threshold
                for _, row in df_daily[mask].iterrows():
                                alarms.append({
                        '时间': row['数据时间'],
                        '炉号': str(fn),
                                    '预警/报警类型': '报警',
                                    '预警/报警事件': event_name,
                                    '预警/报警区分': '报警'
                                })
        return alarms

    def process_data(self, file_path: str, output_dir: str = None) -> pd.DataFrame:
        """处理数据并生成预警报告"""
        # 加载数据
        df = self.load_data(file_path)
        if df.empty:
            return pd.DataFrame()

        # 清空之前的预警事件
        self.warning_events = []

        print(f"\n检查宁波世贸焚烧炉预警/报警 (3-6号炉)...")

        # === 预警规则 ===
        low_temp_warnings = self.check_low_furnace_temp_warning(df)
        self.warning_events.extend(low_temp_warnings)
        print(f"瞬时低炉温预警: {len(low_temp_warnings)} 条")

        high_temp_warnings = self.check_high_furnace_temp_warning(df)
        self.warning_events.extend(high_temp_warnings)
        print(f"高炉温预警: {len(high_temp_warnings)} 条")

        pressure_warnings = self.check_bag_pressure_warning(df)
        self.warning_events.extend(pressure_warnings)
        print(f"压力预警: {len(pressure_warnings)} 条")

        o2_warnings = self.check_o2_warning(df)
        self.warning_events.extend(o2_warnings)
        print(f"氧含量预警: {len(o2_warnings)} 条")

        pollutant_warnings = self.check_pollutant_warning(df)
        self.warning_events.extend(pollutant_warnings)
        print(f"污染物预警: {len(pollutant_warnings)} 条")

        # 活性炭投加量预警
        carbon_warnings = self.check_activated_carbon_warning(df)
        self.warning_events.extend(carbon_warnings)
        print(f"活性炭投加量预警: {len(carbon_warnings)} 条")

        # 氨逃逸预警
        nh3_warnings = self.check_nh3_warning(df)
        self.warning_events.extend(nh3_warnings)
        print(f"氨逃逸预警: {len(nh3_warnings)} 条")

        # === 报警规则 ===
        low_temp_alarms = self.check_low_furnace_temp_alarm(df)
        self.warning_events.extend(low_temp_alarms)
        print(f"低炉温报警: {len(low_temp_alarms)} 条")

        pollutant_alarms = self.check_pollutant_alarm(df)
        self.warning_events.extend(pollutant_alarms)
        print(f"污染物报警: {len(pollutant_alarms)} 条")

        # 转换为DataFrame
        if self.warning_events:
            warning_df = pd.DataFrame(self.warning_events)
            warning_df = warning_df.sort_values('时间')

            print(f"\n共检测到 {len(warning_df)} 条预警事件")

            furnace_stats = warning_df['炉号'].value_counts().sort_index()
            print("各炉预警分布:")
            for furnace, count in furnace_stats.items():
                print(f"  {furnace}号炉: {count} 条预警")

            if output_dir:
                self.save_warning_report(warning_df, output_dir, file_path)

            return warning_df
        else:
            print("\n未检测到预警事件")
            return pd.DataFrame()

    def save_warning_report(self, warning_df: pd.DataFrame, output_dir: str, input_file: str):
        """保存预警报警报告"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        base_name = os.path.splitext(os.path.basename(input_file))[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存Excel格式
        excel_file = os.path.join(output_dir, f"{base_name}_宁波世贸预警报警报告_{timestamp}.xlsx")
        warning_df.to_excel(excel_file, index=False)
        print(f"📊 预警报警报告已保存: {excel_file}")

        # 保存CSV格式
        csv_file = os.path.join(output_dir, f"{base_name}_宁波世贸预警报警报告_{timestamp}.csv")

        if '预警/报警区分' not in warning_df.columns:
            warning_df['预警/报警区分'] = warning_df['预警/报警类型']

        required_columns = ['时间', '炉号', '预警/报警类型', '预警/报警事件', '预警/报警区分']
        template_df = warning_df[required_columns].copy()
        template_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"📋 CSV报告已保存: {csv_file}")

        # 生成统计报告
        stats_file = os.path.join(output_dir, f"{base_name}_宁波世贸预警报警统计_{timestamp}.txt")
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write(f"宁波世贸垃圾焚烧预警报警统计报告\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"数据文件: {input_file}\n")
            f.write(f"总事件数量: {len(warning_df)}\n\n")

            type_stats = warning_df['预警/报警类型'].value_counts()
            f.write("事件类型统计:\n")
            for event_type, count in type_stats.items():
                f.write(f"  {event_type}: {count} 条\n")

            event_stats = warning_df['预警/报警事件'].value_counts()
            f.write("\n事件详细统计:\n")
            for event, count in event_stats.items():
                f.write(f"  {event}: {count} 条\n")

            f.write(f"\n1号炉总事件数: {len(warning_df)} 条\n")

        print(f"📈 统计报告已保存: {stats_file}")

def main():
    """主函数 - 支持命令行和直接运行"""
    import sys

    DEFAULT_INPUT_FILE = "宁德世贸/20250101.csv"  # 默认输入文件
    DEFAULT_OUTPUT_DIR = "宁德世贸/预警文件输出"  # 默认输出目录

    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT_DIR
    else:
        print("🚀 直接运行模式")
        print("💡 提示: 可以修改代码中的DEFAULT_INPUT_FILE变量来指定要分析的文件")
        print("💡 提示: 使用 python shishi_data_yujing_gz.py <文件路径> 分析指定文件")

        input_file = DEFAULT_INPUT_FILE
        output_dir = DEFAULT_OUTPUT_DIR

        print(f"📁 使用默认输入文件: {input_file}")

    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"❌ 错误: 输入文件不存在 - {input_file}")
        print("请修改代码中的DEFAULT_INPUT_FILE变量或使用命令行参数")
        return

    # 创建预警系统实例
    print("\n🔧 创建宁波世贸预警系统实例...")
    warning_system = WasteIncinerationWarningSystemNingbo()

    # 处理数据
    print(f"📊 开始处理数据文件: {input_file}")
    try:
        warning_df = warning_system.process_data(input_file, output_dir)

        if not warning_df.empty:
            print(f"\n✅ 预警处理完成! 输出目录: {output_dir}")
            print(f"📊 总计检测到 {len(warning_df)} 条预警报警事件")

            # 显示事件类型统计
            type_stats = warning_df['预警/报警类型'].value_counts()
            print("\n📈 事件类型统计:")
            for event_type, count in type_stats.items():
                print(f"  {event_type}: {count} 条")

            # 显示前几条事件
            print(f"\n📋 前5条事件:")
            for i, (_, row) in enumerate(warning_df.head().iterrows()):
                print(f"  {i+1}. {row['时间']} - {row['预警/报警事件']} ({row['预警/报警类型']})")
        else:
            print("\n✅ 数据处理完成，未发现预警报警事件。")

    except Exception as e:
        print(f"❌ 处理过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
