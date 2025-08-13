import pandas as pd
import numpy as np
from datetime import datetime
import os
import glob
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class NingdeDataProcessor:
    """
    宁德世贸数据处理算法
    基于点位表要求，结合CSV文件列名，参考折算公式
    """
    
    def __init__(self):
        # 根据点位表定义的字段映射（从CSV列名到点位表列标识）
        self.field_mapping = {
            # 燃料计量模块
            'waste_processing_month': {
                'description': '垃圾月处理量',
                'columns': ['垃圾抓斗1', '垃圾抓斗2'],  # B列和C列
                'calculation': 'sum'  # 求和
            },
            
            # 炉膛燃烧模块
            'furnace_temp_avg': {
                'description': '炉膛温度月平均值（上部中部取平均后再取月平均）',
                '3号炉': ['3号炉炉膛上部温度', '3号炉炉膛中部温度'],  # AH、AI
                '4号炉': ['4号炉炉膛上部温度', '4号炉炉膛中部温度'],  # AJ、AK
                '5号炉': ['5号炉炉膛上部温度', '5号炉炉膛中部温度'],  # AL、AM
                '6号炉': ['6号炉炉膛上部温度', '6号炉炉膛中部温度'],  # AN、AO
                'calculation': 'mean_then_monthly_mean'
            },
            
            'furnace_pressure': {
                'description': '炉膛压力',
                '3号炉': '3号炉炉膛压力',  # AP
                '4号炉': '4号炉炉膛压力',  # AQ
                '5号炉': '5号炉炉膛压力',  # AR
                '6号炉': '6号炉炉膛压力',  # AS
                'allow_negative': True  # 压力列保留负值
            },
            
            # 烟气净化模块 - 半干法脱酸
            'lime_slurry_flow': {
                'description': '雾化石灰浆流量月平均值',
                '3号炉': '3号炉雾化石灰浆流量',  # FT
                '4号炉': '4号炉雾化石灰浆流量',  # FZ
                '5号炉': '5号炉雾化石灰浆流量',  # GE
                '6号炉': '6号炉雾化石灰浆流量',  # GI
            },
            
            'semi_dry_reactor_temp': {
                'description': '半干法反应塔温度月平均值',
                '3号炉': ['3号炉半干法反应塔温度1', '3号炉半干法反应塔温度2', '3号炉半干法反应塔温度3'],  # FU、FV、FW
                '4号炉': ['4号炉半干法反应塔温度1', '4号炉半干法反应塔温度2', '4号炉半干法反应塔温度3'],  # GA、GB、GC
                '5号炉': ['5号炉半干法反应塔温度1', '5号炉半干法反应塔温度2'],  # GF、GG、GH (实际CSV中只有2个)
                '6号炉': ['6号炉半干法反应塔温度1', '6号炉半干法反应塔温度2', '6号炉半干法反应塔温度3'],  # GJ、GK、GL
                'calculation': 'mean'
            },
            
            # 烟气净化模块 - 湿法脱酸
            'naoh_flow': {
                'description': '湿式洗涤塔氢氧化钠流量月平均值',
                '3号炉': '3号炉湿式洗涤塔氢氧化钠流量流量',  # GQ
                '4号炉': '4号炉湿式洗涤塔氢氧化钠流量流量',  # GV
                '5号炉': '5号炉湿式洗涤塔氢氧化钠流量流量',  # HA
                '6号炉': '6号炉湿式洗涤塔氢氧化钠流量流量',  # HF
            },
            
            'ph_avg': {
                'description': '炉pH月平均值',
                '3号炉': ['3号炉PH1', '3号炉PH2'],  # GO、GP
                '4号炉': ['4号炉PH1', '4号炉PH2'],  # GT、GU
                '5号炉': ['5号炉PH1', '5号炉PH2'],  # GY、GZ
                '6号炉': ['6号炉PH1', '6号炉PH2'],  # HD、HE
                'calculation': 'mean'
            },
            
            'reactor_temp_avg': {
                'description': '炉反应塔温度月平均值',
                '3号炉': ['3号炉反应塔温度1', '3号炉反应塔温度2'],  # GR、GS
                '4号炉': ['4号炉反应塔温度1', '4号炉反应塔温度2'],  # GW、GX
                '5号炉': ['5号炉反应塔温度1', '5号炉反应塔温度2'],  # HB、HC
                '6号炉': ['6号炉反应塔温度1', '6号炉反应塔温度2'],  # HG、HH
                'calculation': 'mean'
            },
            
            # SNCR脱硝
            'sncr_reductant_flow': {
                'description': '炉还原剂流量月平均值',
                '3号炉': ['3号炉还原剂流量1', '3号炉还原剂流量2'],  # HI、HJ
                '4号炉': ['4号炉还原剂流量1', '4号炉还原剂流量2'],  # HN、HO
                '5号炉': ['5号炉还原剂流量1', '5号炉还原剂流量2'],  # HS、HT
                '6号炉': ['6号炉还原剂流量1', '6号炉还原剂流量2'],  # HX、HY
                'calculation': 'mean'
            },
            
            'furnace_outlet_temp': {
                'description': '炉膛出口温度月平均值',
                '3号炉': '3号炉炉膛出口温度',  # HK
                '4号炉': '4号炉炉膛出口温度',  # HP
                '5号炉': '5号炉炉膛出口温度',  # HU
                '6号炉': '6号炉炉膛出口温度',  # HZ
            },
            
            # SCR脱硝 (仅3号炉和6号炉)
            'scr_inlet_temp': {
                'description': '反应器进口温度月平均值',
                '3号炉': '3号炉反应器进口温度',  # IE
                '6号炉': '6号炉反应器进口温度',  # IJ
            },
            
            'scr_outlet_temp': {
                'description': '反应器出口温度月平均值',
                '3号炉': '3号炉反应器出口温度',  # IF
                '6号炉': '6号炉反应器出口温度',  # IK
            },
            
            'nh3_escape': {
                'description': '氨逃逸量月平均值',
                '3号炉': '3号炉氨逃逸量',  # IC
                '6号炉': '6号炉氨逃逸量',  # IH
            },
            
            'scr_reductant_flow': {
                'description': '还原剂流量月平均值',
                '3号炉': '3号炉还原剂流量',  # ID
                '6号炉': '6号炉还原剂流量',  # II
            },
            
            # 活性炭
            'activated_carbon_flow': {
                'description': '每月活性炭平均流量',
                '3号炉': '3号炉活性炭喷射量',  # IM
                '4号炉': '4号炉活性炭喷射量',  # IN
                '5号炉': '5号炉活性炭喷射量',  # IO
                '6号炉': '6号炉活性炭喷射量',  # IP
            },
            
            # 布袋除尘
            'bag_pressure_diff': {
                'description': '布袋进出口压差月平均值',
                '3号炉': '3号炉布袋进出口压差',  # IQ
                '4号炉': '4号炉布袋进出口压差',  # IT
                '5号炉': '5号炉布袋进出口压差',  # IW
                '6号炉': '6号炉布袋进出口压差',  # IZ
                'allow_negative': True  # 压力列保留负值
            },
            
            'bag_dust_temp': {
                'description': '布袋除尘器温度月平均值',
                '3号炉': '3号炉布袋除尘器温度',  # IR
                '4号炉': '4号炉布袋除尘器温度',  # IU
                '5号炉': '5号炉布袋除尘器温度',  # IX
                '6号炉': '6号炉布袋除尘器温度',  # IA
            },
            
            # 烟气排放模块
            'dust_emission': {
                'description': '粉尘排放浓度月平均值',
                '3号炉': {'conc': '3号炉粉尘', 'o2': '3号炉O2'},  # JG
                '4号炉': {'conc': '4号炉粉尘', 'o2': '4号炉O2'},  # JP
                '5号炉': {'conc': '5号炉粉尘', 'o2': '5号炉O2'},  # JZ
                '6号炉': {'conc': '6号炉粉尘', 'o2': '6号炉O2'},  # KI
                'need_correction': True  # 需要折算
            },
            
            'so2_emission': {
                'description': 'SO2排放浓度月平均值',
                '3号炉': {'conc': '3号炉SO2', 'o2': '3号炉O2'},  # JH
                '4号炉': {'conc': '4号炉SO2', 'o2': '4号炉O2'},  # JQ
                '5号炉': {'conc': '5号炉SO2', 'o2': '5号炉O2'},  # KA
                '6号炉': {'conc': '6号炉SO2', 'o2': '6号炉O2'},  # KJ
                'need_correction': True
            },
            
            'nox_emission': {
                'description': 'NOx排放浓度月平均值',
                '3号炉': {'conc': '3号炉Nox', 'o2': '3号炉O2'},  # JI
                '4号炉': {'conc': '4号炉Nox', 'o2': '4号炉O2'},  # JR
                '5号炉': {'conc': '5号炉Nox', 'o2': '5号炉O2'},  # KB
                '6号炉': {'conc': '6号炉Nox', 'o2': '6号炉O2'},  # KK
                'need_correction': True
            },
            
            'co_emission': {
                'description': 'CO排放浓度月平均值',
                '3号炉': {'conc': '3号炉CO', 'o2': '3号炉O2'},  # JJ
                '4号炉': {'conc': '4号炉CO', 'o2': '4号炉O2'},  # JS
                '5号炉': {'conc': '5号炉CO', 'o2': '5号炉O2'},  # KC
                '6号炉': {'conc': '6号炉CO', 'o2': '6号炉O2'},  # KL
                'need_correction': True
            },
            
            'hcl_emission': {
                'description': 'HCL排放浓度月平均值',
                '3号炉': {'conc': '3号炉HCL', 'o2': '3号炉O2'},  # JK
                '4号炉': {'conc': '4号炉HCL', 'o2': '4号炉O2'},  # JT
                '5号炉': {'conc': '5号炉HCL', 'o2': '5号炉O2'},  # KD
                '6号炉': {'conc': '6号炉HCL', 'o2': '6号炉O2'},  # KM
                'need_correction': True
            }
        }
        
        self.furnace_list = ['3号炉', '4号炉', '5号炉', '6号炉']
        
    def load_data(self, file_path: str) -> pd.DataFrame:
        """加载数据文件"""
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

            print(f"成功加载数据文件: {file_path}")
            print(f"数据行数: {len(df)}, 列数: {len(df.columns)}")
            print(f"数据时间范围: {df['数据时间'].min()} 到 {df['数据时间'].max()}")
            return df

        except Exception as e:
            print(f"加载数据文件失败: {e}")
            return pd.DataFrame()

    def _coerce_numeric(self, series: pd.Series) -> pd.Series:
        """将列安全转换为数值，无法转换的设为NaN"""
        s = series.astype(str)
        s = s.replace({'--': '0', 'nan': '0'})
        s = s.str.extract(r'(-?\d+\.?\d*)', expand=False)
        s = pd.to_numeric(s, errors='coerce')
        return s

    def _clean_outliers_for_calculation(self, series: pd.Series, column_name: str = "", allow_negative: bool = False) -> pd.Series:
        """
        计算时清洗异常值，不修改原始数据
        
        清洗规则:
        1. 移除0值
        2. 移除负值（except压力列）
        3. 使用箱型图移除极端异常值
        """
        if series.empty:
            return series
        
        # 首先转换为数值
        cleaned_series = self._coerce_numeric(series).copy()
        original_count = len(cleaned_series)
        
        # 记录清洗前的有效数据数量
        valid_before = cleaned_series.notna().sum()
        
        # 1. 移除0值
        zero_mask = cleaned_series == 0
        cleaned_series[zero_mask] = np.nan
        zero_removed = zero_mask.sum()
        
        # 2. 移除负值（压力列除外）
        negative_removed = 0
        if not allow_negative:
            negative_mask = cleaned_series < 0
            cleaned_series[negative_mask] = np.nan
            negative_removed = negative_mask.sum()
        
        # 3. 箱型图异常值检测
        outlier_removed = 0
        valid_data = cleaned_series.dropna()
        if len(valid_data) > 4:  # 至少需要4个数据点才能计算四分位数
            Q1 = valid_data.quantile(0.25)
            Q3 = valid_data.quantile(0.75)
            IQR = Q3 - Q1
            
            # 定义异常值边界
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # 移除异常值
            outlier_mask = (cleaned_series < lower_bound) | (cleaned_series > upper_bound)
            cleaned_series[outlier_mask] = np.nan
            outlier_removed = outlier_mask.sum()
        
        # 记录清洗后的有效数据数量
        valid_after = cleaned_series.notna().sum()
        
        # 输出清洗统计（仅在有清洗操作时）
        total_removed = zero_removed + negative_removed + outlier_removed
        if total_removed > 0 and column_name:
            print(f"   数据清洗 [{column_name}]: 移除 {total_removed} 个异常值 "
                  f"(零值:{zero_removed}, 负值:{negative_removed}, 异常值:{outlier_removed}) "
                  f"剩余有效数据: {valid_after}/{original_count}")
        
        return cleaned_series

    def calculate_corrected_concentration(self, measured_conc, measured_o2):
        """计算标准状态下的浓度（折算）- 参考现有折算公式"""
        # ρ（标准）=ρ（实测）*10/(21-ρ（实测O2））
        
        # 处理异常的氧含量数据，避免折算异常
        o2_cleaned = measured_o2.copy()
        conc_cleaned = measured_conc.copy()
        
        # 氧含量合理范围检查：正常情况下应在4%-15%之间
        invalid_o2_mask = (o2_cleaned <= 2) | (o2_cleaned >= 18) | pd.isna(o2_cleaned)
        
        # 浓度数据检查
        invalid_conc_mask = (conc_cleaned < 0) | pd.isna(conc_cleaned)
        
        # 合并无效数据掩码
        invalid_mask = invalid_o2_mask | invalid_conc_mask
        
        # 计算分母，避免分母过小导致折算值异常放大
        denominator = 21 - o2_cleaned
        # 当分母小于5时（氧含量>16%），折算系数过大，认为数据异常
        small_denominator_mask = denominator < 5.0
        
        # 最终的无效数据掩码
        final_invalid_mask = invalid_mask | small_denominator_mask
        
        # 计算折算浓度
        corrected = pd.Series(index=measured_conc.index, dtype=float)
        valid_mask = ~final_invalid_mask
        
        if valid_mask.any():
            corrected[valid_mask] = conc_cleaned[valid_mask] * 10 / denominator[valid_mask]
        
        # 无效数据设为NaN
        corrected[final_invalid_mask] = np.nan
        
        return corrected

    def process_field(self, df: pd.DataFrame, field_name: str, field_config: dict) -> dict:
        """处理单个字段的数据"""
        results = {}
        
        print(f"\n处理字段: {field_config.get('description', field_name)}")
        
        # 特殊处理垃圾月处理量（求和）
        if field_name == 'waste_processing_month':
            columns = field_config['columns']
            cleaned_data = []
            for col in columns:
                if col in df.columns:
                    cleaned = self._clean_outliers_for_calculation(df[col], col)
                    cleaned_data.append(cleaned)
            
            if cleaned_data:
                total_series = sum(cleaned_data)
                monthly_avg = total_series.mean()
                results['总计'] = {
                    'monthly_avg': monthly_avg,
                    'data_count': total_series.notna().sum(),
                    'raw_data': total_series
                }
            return results
        
        # 处理各炉数据
        for furnace in self.furnace_list:
            if furnace not in field_config:
                continue
                
            furnace_config = field_config[furnace]
            allow_negative = field_config.get('allow_negative', False)
            need_correction = field_config.get('need_correction', False)
            calculation = field_config.get('calculation', 'mean')
            
            print(f"  处理 {furnace}")
            
            # 处理需要折算的排放数据
            if need_correction and isinstance(furnace_config, dict):
                conc_col = furnace_config['conc']
                o2_col = furnace_config['o2']
                
                if conc_col in df.columns and o2_col in df.columns:
                    # 清洗数据
                    conc_cleaned = self._clean_outliers_for_calculation(df[conc_col], f"{furnace}_{conc_col}")
                    o2_cleaned = self._clean_outliers_for_calculation(df[o2_col], f"{furnace}_{o2_col}")
                    
                    # 计算折算浓度
                    corrected_conc = self.calculate_corrected_concentration(conc_cleaned, o2_cleaned)
                    
                    # 计算月平均值
                    monthly_avg = corrected_conc.mean()
                    
                    results[furnace] = {
                        'monthly_avg': monthly_avg,
                        'data_count': corrected_conc.notna().sum(),
                        'raw_avg': conc_cleaned.mean(),
                        'o2_avg': o2_cleaned.mean(),
                        'corrected_data': corrected_conc
                    }
                    
                    print(f"    原始浓度均值: {conc_cleaned.mean():.2f}")
                    print(f"    O2均值: {o2_cleaned.mean():.2f}%")
                    print(f"    折算后均值: {monthly_avg:.2f}")
            
            # 处理单个列或多个列的平均
            elif isinstance(furnace_config, str):
                # 单个列
                col = furnace_config
                if col in df.columns:
                    cleaned = self._clean_outliers_for_calculation(df[col], f"{furnace}_{col}", allow_negative)
                    monthly_avg = cleaned.mean()
                    
                    results[furnace] = {
                        'monthly_avg': monthly_avg,
                        'data_count': cleaned.notna().sum(),
                        'raw_data': cleaned
                    }
                    
                    print(f"    月平均值: {monthly_avg:.2f}")
            
            elif isinstance(furnace_config, list):
                # 多个列需要先平均
                cleaned_data = []
                for col in furnace_config:
                    if col in df.columns:
                        cleaned = self._clean_outliers_for_calculation(df[col], f"{furnace}_{col}", allow_negative)
                        cleaned_data.append(cleaned)
                
                if cleaned_data:
                    if calculation == 'mean_then_monthly_mean':
                        # 先取各测点平均，再取月平均
                        point_avg = sum(cleaned_data) / len(cleaned_data)
                        monthly_avg = point_avg.mean()
                    else:
                        # 直接取所有数据的平均
                        all_data = pd.concat(cleaned_data)
                        monthly_avg = all_data.mean()
                    
                    results[furnace] = {
                        'monthly_avg': monthly_avg,
                        'data_count': sum(data.notna().sum() for data in cleaned_data),
                        'point_count': len(cleaned_data),
                        'combined_data': cleaned_data
                    }
                    
                    print(f"    月平均值: {monthly_avg:.2f} (基于{len(cleaned_data)}个测点)")
        
        return results

    def process_all_data(self, file_path: str, output_dir: str = None) -> dict:
        """处理所有数据并生成报告"""
        # 加载数据
        df = self.load_data(file_path)
        if df.empty:
            return {}

        print(f"\n开始处理宁德世贸数据（基于点位表要求）...")
        print(f"数据时间范围: {df['数据时间'].min()} 到 {df['数据时间'].max()}")
        
        all_results = {}
        
        # 处理每个字段
        for field_name, field_config in self.field_mapping.items():
            try:
                results = self.process_field(df, field_name, field_config)
                all_results[field_name] = results
            except Exception as e:
                print(f"处理字段 {field_name} 时出错: {e}")
                continue
        
        # 生成报告
        if output_dir:
            self.save_results_report(all_results, output_dir, file_path)
        
        return all_results

    def save_results_report(self, results: dict, output_dir: str, input_file: str):
        """保存处理结果报告"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        base_name = os.path.splitext(os.path.basename(input_file))[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 生成Excel报告
        excel_file = os.path.join(output_dir, f"{base_name}_宁德世贸月度数据处理报告_{timestamp}.xlsx")
        
        # 创建Excel writer
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # 汇总报告
            summary_data = []
            for field_name, field_results in results.items():
                field_config = self.field_mapping[field_name]
                description = field_config.get('description', field_name)
                
                for furnace_or_type, result in field_results.items():
                    if isinstance(result, dict) and 'monthly_avg' in result:
                        summary_data.append({
                            '模块': description,
                            '炉号/类型': furnace_or_type,
                            '月平均值': result['monthly_avg'],
                            '有效数据点数': result['data_count'],
                            '原始均值': result.get('raw_avg', ''),
                            'O2均值': result.get('o2_avg', ''),
                            '测点数量': result.get('point_count', 1)
                        })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='月度汇总报告', index=False)
            
            # 分模块详细报告
            module_groups = {
                '燃料计量模块': ['waste_processing_month'],
                '炉膛燃烧模块': ['furnace_temp_avg', 'furnace_pressure'],
                '半干法脱酸': ['lime_slurry_flow', 'semi_dry_reactor_temp'],
                '湿法脱酸': ['naoh_flow', 'ph_avg', 'reactor_temp_avg'],
                'SNCR脱硝': ['sncr_reductant_flow', 'furnace_outlet_temp'],
                'SCR脱硝': ['scr_inlet_temp', 'scr_outlet_temp', 'nh3_escape', 'scr_reductant_flow'],
                '活性炭': ['activated_carbon_flow'],
                '布袋除尘': ['bag_pressure_diff', 'bag_dust_temp'],
                '烟气排放': ['dust_emission', 'so2_emission', 'nox_emission', 'co_emission', 'hcl_emission']
            }
            
            for module_name, field_list in module_groups.items():
                module_data = []
                for field_name in field_list:
                    if field_name in results:
                        field_config = self.field_mapping[field_name]
                        description = field_config.get('description', field_name)
                        field_results = results[field_name]
                        
                        for furnace_or_type, result in field_results.items():
                            if isinstance(result, dict) and 'monthly_avg' in result:
                                module_data.append({
                                    '参数': description,
                                    '炉号/类型': furnace_or_type,
                                    '月平均值': result['monthly_avg'],
                                    '有效数据点数': result['data_count'],
                                    '原始均值': result.get('raw_avg', ''),
                                    'O2均值': result.get('o2_avg', ''),
                                    '备注': '折算后' if 'corrected_data' in result else ''
                                })
                
                if module_data:
                    module_df = pd.DataFrame(module_data)
                    sheet_name = module_name[:31]  # Excel工作表名称限制
                    module_df.to_excel(writer, sheet_name=sheet_name, index=False)

        print(f"📊 月度数据处理报告已保存: {excel_file}")

        # 生成文本统计报告
        txt_file = os.path.join(output_dir, f"{base_name}_宁德世贸数据处理统计_{timestamp}.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"宁德世贸月度数据处理统计报告\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"数据文件: {input_file}\n\n")
            
            f.write("=" * 50 + "\n")
            f.write("各模块处理结果汇总\n")
            f.write("=" * 50 + "\n\n")
            
            for field_name, field_results in results.items():
                field_config = self.field_mapping[field_name]
                description = field_config.get('description', field_name)
                f.write(f"{description}:\n")
                
                for furnace_or_type, result in field_results.items():
                    if isinstance(result, dict) and 'monthly_avg' in result:
                        f.write(f"  {furnace_or_type}: {result['monthly_avg']:.2f}")
                        if 'raw_avg' in result:
                            f.write(f" (原始: {result['raw_avg']:.2f}, 折算后)")
                        f.write(f" [数据点: {result['data_count']}]\n")
                f.write("\n")

        print(f"📈 统计报告已保存: {txt_file}")

    def scan_monthly_files(self, base_dir: str) -> dict:
        """扫描指定目录下的月度文件夹，返回每个月的文件列表"""
        monthly_files = {}
        base_path = Path(base_dir)
        
        # 查找年月文件夹（格式：2025年1月, 2025年2月等）
        year_month_pattern = "2025年*月"
        month_dirs = list(base_path.glob(year_month_pattern))
        
        if not month_dirs:
            print(f"⚠️ 在 {base_dir} 中未找到月度文件夹（格式：2025年*月）")
            return {}
        
        for month_dir in sorted(month_dirs):
            month_name = month_dir.name
            print(f"📁 扫描月度文件夹: {month_name}")
            
            # 查找该月的所有xlsx文件
            xlsx_files = list(month_dir.glob("*.xlsx"))
            if xlsx_files:
                monthly_files[month_name] = sorted([str(f) for f in xlsx_files])
                print(f"   找到 {len(xlsx_files)} 个Excel文件")
            else:
                print(f"   ⚠️ 该月文件夹中未找到Excel文件")
        
        return monthly_files

    def process_monthly_data(self, month_files: list, month_name: str) -> dict:
        """处理单个月的所有文件，合并数据并计算月度统计"""
        print(f"\n🔄 开始处理 {month_name} 的数据...")
        print(f"   文件数量: {len(month_files)}")
        
        all_dfs = []
        successful_files = 0
        
        # 加载该月所有文件
        for file_path in month_files:
            try:
                df = self.load_data(file_path)
                if not df.empty:
                    all_dfs.append(df)
                    successful_files += 1
                    if successful_files % 5 == 0:  # 每5个文件显示一次进度
                        print(f"   已处理 {successful_files}/{len(month_files)} 个文件...")
            except Exception as e:
                print(f"   ⚠️ 文件 {Path(file_path).name} 加载失败: {e}")
                continue
        
        if not all_dfs:
            print(f"   ❌ {month_name} 没有成功加载任何文件")
            return {}
        
        # 合并所有数据
        print(f"   📊 合并 {len(all_dfs)} 个文件的数据...")
        combined_df = pd.concat(all_dfs, ignore_index=True)
        combined_df = combined_df.sort_values('数据时间')
        
        print(f"   ✅ 合并完成，总数据行数: {len(combined_df)}")
        print(f"   📅 数据时间范围: {combined_df['数据时间'].min()} 到 {combined_df['数据时间'].max()}")
        
        # 计算月度统计
        monthly_results = {}
        
        # 处理每个字段
        for field_name, field_config in self.field_mapping.items():
            try:
                results = self.process_field(combined_df, field_name, field_config)
                if results:  # 只保存有结果的字段
                    monthly_results[field_name] = results
            except Exception as e:
                print(f"   ⚠️ 处理字段 {field_name} 时出错: {e}")
                continue
        
        print(f"   ✅ {month_name} 数据处理完成，生成 {len(monthly_results)} 个字段结果")
        return monthly_results

    def process_all_months(self, base_dir: str, output_dir: str = None) -> dict:
        """批量处理所有月份的数据"""
        print("🚀 开始批量处理多月数据...")
        
        # 扫描月度文件
        monthly_files = self.scan_monthly_files(base_dir)
        if not monthly_files:
            print("❌ 未找到任何月度数据文件")
            return {}
        
        print(f"📋 找到 {len(monthly_files)} 个月的数据:")
        for month_name, files in monthly_files.items():
            print(f"   {month_name}: {len(files)} 个文件")
        
        # 处理每个月的数据
        all_monthly_results = {}
        
        for month_name, files in monthly_files.items():
            try:
                monthly_result = self.process_monthly_data(files, month_name)
                if monthly_result:
                    all_monthly_results[month_name] = monthly_result
                    
                    # 保存单月报告
                    if output_dir:
                        month_output_dir = os.path.join(output_dir, month_name)
                        self.save_monthly_report(monthly_result, month_output_dir, month_name)
                        
            except Exception as e:
                print(f"❌ 处理 {month_name} 时出现错误: {e}")
                continue
        
        # 生成汇总报告
        if output_dir and all_monthly_results:
            self.save_summary_report(all_monthly_results, output_dir)
        
        return all_monthly_results

    def save_monthly_report(self, monthly_results: dict, output_dir: str, month_name: str):
        """保存单月处理报告"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 生成Excel报告
        excel_file = os.path.join(output_dir, f"{month_name}_月度数据处理报告_{timestamp}.xlsx")
        
        # 创建Excel writer
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # 汇总报告
            summary_data = []
            for field_name, field_results in monthly_results.items():
                field_config = self.field_mapping[field_name]
                description = field_config.get('description', field_name)
                
                for furnace_or_type, result in field_results.items():
                    if isinstance(result, dict) and 'monthly_avg' in result:
                        summary_data.append({
                            '参数': description,
                            '炉号/类型': furnace_or_type,
                            '月平均值': result['monthly_avg'],
                            '有效数据点数': result['data_count'],
                            '原始均值': result.get('raw_avg', ''),
                            'O2均值': result.get('o2_avg', ''),
                            '测点数量': result.get('point_count', 1),
                            '备注': '折算后' if 'corrected_data' in result else ''
                        })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name=f'{month_name}汇总', index=False)

        print(f"📊 {month_name} 报告已保存: {excel_file}")

    def save_summary_report(self, all_monthly_results: dict, output_dir: str):
        """保存6个月汇总报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_file = os.path.join(output_dir, f"宁德世贸_6个月汇总报告_{timestamp}.xlsx")
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # 创建对比汇总表
            comparison_data = []
            
            # 获取所有字段和炉号的组合
            all_fields = set()
            all_furnaces = set()
            for monthly_result in all_monthly_results.values():
                for field_name, field_results in monthly_result.items():
                    all_fields.add(field_name)
                    for furnace in field_results.keys():
                        all_furnaces.add(furnace)
            
            # 生成对比数据
            for field_name in sorted(all_fields):
                field_config = self.field_mapping[field_name]
                description = field_config.get('description', field_name)
                
                for furnace in sorted(all_furnaces):
                    row_data = {
                        '参数': description,
                        '炉号/类型': furnace
                    }
                    
                    # 添加每个月的数据
                    for month_name in sorted(all_monthly_results.keys()):
                        monthly_result = all_monthly_results[month_name]
                        if field_name in monthly_result and furnace in monthly_result[field_name]:
                            result = monthly_result[field_name][furnace]
                            if isinstance(result, dict) and 'monthly_avg' in result:
                                row_data[month_name] = result['monthly_avg']
                            else:
                                row_data[month_name] = None
                        else:
                            row_data[month_name] = None
                    
                    # 只有当至少一个月有数据时才添加行
                    if any(row_data[month] is not None for month in sorted(all_monthly_results.keys())):
                        comparison_data.append(row_data)
            
            if comparison_data:
                comparison_df = pd.DataFrame(comparison_data)
                comparison_df.to_excel(writer, sheet_name='6个月数据对比', index=False)
            
            # 为每个月创建单独的工作表
            for month_name, monthly_result in all_monthly_results.items():
                month_data = []
                for field_name, field_results in monthly_result.items():
                    field_config = self.field_mapping[field_name]
                    description = field_config.get('description', field_name)
                    
                    for furnace_or_type, result in field_results.items():
                        if isinstance(result, dict) and 'monthly_avg' in result:
                            month_data.append({
                                '参数': description,
                                '炉号/类型': furnace_or_type,
                                '月平均值': result['monthly_avg'],
                                '有效数据点数': result['data_count'],
                                '原始均值': result.get('raw_avg', ''),
                                'O2均值': result.get('o2_avg', ''),
                                '备注': '折算后' if 'corrected_data' in result else ''
                            })
                
                if month_data:
                    month_df = pd.DataFrame(month_data)
                    sheet_name = month_name[:31]  # Excel工作表名称限制
                    month_df.to_excel(writer, sheet_name=sheet_name, index=False)

        print(f"📊 6个月汇总报告已保存: {excel_file}")
        
        # 生成文本统计报告
        txt_file = os.path.join(output_dir, f"宁德世贸_6个月统计汇总_{timestamp}.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"宁德世贸6个月数据处理统计汇总报告\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"处理月份: {', '.join(sorted(all_monthly_results.keys()))}\n\n")
            
            f.write("=" * 70 + "\n")
            f.write("各月主要参数对比（月平均值）\n")
            f.write("=" * 70 + "\n\n")
            
            # 选择几个重要参数进行对比
            key_params = [
                'furnace_temp_avg',
                'dust_emission', 
                'so2_emission',
                'nox_emission',
                'co_emission'
            ]
            
            for param in key_params:
                if any(param in monthly_result for monthly_result in all_monthly_results.values()):
                    field_config = self.field_mapping[param]
                    description = field_config.get('description', param)
                    f.write(f"{description}:\n")
                    
                    for furnace in ['3号炉', '4号炉', '5号炉', '6号炉']:
                        f.write(f"  {furnace}: ")
                        values = []
                        for month_name in sorted(all_monthly_results.keys()):
                            monthly_result = all_monthly_results[month_name]
                            if param in monthly_result and furnace in monthly_result[param]:
                                result = monthly_result[param][furnace]
                                if isinstance(result, dict) and 'monthly_avg' in result:
                                    values.append(f"{month_name}:{result['monthly_avg']:.2f}")
                        
                        if values:
                            f.write(" | ".join(values))
                        else:
                            f.write("无数据")
                        f.write("\n")
                    f.write("\n")

        print(f"📈 6个月统计汇总已保存: {txt_file}")

def main():
    """主函数"""
    import sys

    DEFAULT_BASE_DIR = "宁德世贸"  # 默认基础目录（包含各月份文件夹）
    DEFAULT_OUTPUT_DIR = "宁德世贸/6个月批量处理输出"  # 默认输出目录

    print("🚀 宁德世贸数据处理工具")
    print("=" * 50)
    
    if len(sys.argv) >= 2:
        mode = sys.argv[1].lower()
        
        if mode == "batch" or mode == "批量":
            # 批量处理模式
            base_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_BASE_DIR
            output_dir = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_OUTPUT_DIR
            
            print("📋 批量处理模式")
            print(f"📁 基础目录: {base_dir}")
            print(f"📤 输出目录: {output_dir}")
            
            # 检查基础目录是否存在
            if not os.path.exists(base_dir):
                print(f"❌ 错误: 基础目录不存在 - {base_dir}")
                return

            # 创建数据处理实例
            print("\n🔧 创建宁德世贸数据处理实例...")
            processor = NingdeDataProcessor()

            # 批量处理所有月份数据
            try:
                all_results = processor.process_all_months(base_dir, output_dir)

                if all_results:
                    print(f"\n✅ 批量数据处理完成! 输出目录: {output_dir}")
                    print(f"📊 总计处理 {len(all_results)} 个月的数据")
                    
                    # 显示各月数据摘要
                    for month_name, monthly_result in all_results.items():
                        field_count = len(monthly_result)
                        print(f"  {month_name}: {field_count} 个参数完成处理")
                else:
                    print("\n⚠️ 批量处理完成，但未生成有效结果。")

            except Exception as e:
                print(f"❌ 批量处理过程中出现错误: {e}")
                import traceback
                traceback.print_exc()
        
        elif mode == "single" or mode == "单个":
            # 单文件处理模式
            input_file = sys.argv[2] if len(sys.argv) > 2 else "宁德世贸/20250101.csv"
            output_dir = sys.argv[3] if len(sys.argv) > 3 else "宁德世贸/单文件处理输出"
            
            print("📄 单文件处理模式")
            print(f"📁 输入文件: {input_file}")
            print(f"📤 输出目录: {output_dir}")
            
            # 检查输入文件是否存在
            if not os.path.exists(input_file):
                print(f"❌ 错误: 输入文件不存在 - {input_file}")
                return

            # 创建数据处理实例
            print("\n🔧 创建宁德世贸数据处理实例...")
            processor = NingdeDataProcessor()

            # 处理单个文件
            try:
                results = processor.process_all_data(input_file, output_dir)

                if results:
                    print(f"\n✅ 数据处理完成! 输出目录: {output_dir}")
                    
                    # 显示主要结果
                    print(f"\n📋 主要处理结果:")
                    for field_name, field_results in list(results.items())[:5]:  # 显示前5个结果
                        field_config = processor.field_mapping[field_name]
                        description = field_config.get('description', field_name)
                        print(f"  {description}:")
                        for furnace_or_type, result in field_results.items():
                            if isinstance(result, dict) and 'monthly_avg' in result:
                                print(f"    {furnace_or_type}: {result['monthly_avg']:.2f}")
                else:
                    print("\n⚠️ 数据处理完成，但未生成有效结果。")

            except Exception as e:
                print(f"❌ 处理过程中出现错误: {e}")
                import traceback
                traceback.print_exc()
        
        else:
            print("❌ 错误: 无效的模式参数")
            print_usage()
    
    else:
        # 默认批量处理模式
        print("📋 默认批量处理模式")
        print("💡 提示: 使用参数 'batch' 或 'single' 可显式选择处理模式")
        print(f"📁 基础目录: {DEFAULT_BASE_DIR}")
        print(f"📤 输出目录: {DEFAULT_OUTPUT_DIR}")
        
        # 检查基础目录是否存在
        if not os.path.exists(DEFAULT_BASE_DIR):
            print(f"❌ 错误: 基础目录不存在 - {DEFAULT_BASE_DIR}")
            print_usage()
            return

        # 创建数据处理实例
        print("\n🔧 创建宁德世贸数据处理实例...")
        processor = NingdeDataProcessor()

        # 批量处理所有月份数据
        try:
            all_results = processor.process_all_months(DEFAULT_BASE_DIR, DEFAULT_OUTPUT_DIR)

            if all_results:
                print(f"\n✅ 批量数据处理完成! 输出目录: {DEFAULT_OUTPUT_DIR}")
                print(f"📊 总计处理 {len(all_results)} 个月的数据")
                
                # 显示各月数据摘要
                for month_name, monthly_result in all_results.items():
                    field_count = len(monthly_result)
                    print(f"  {month_name}: {field_count} 个参数完成处理")
            else:
                print("\n⚠️ 批量处理完成，但未生成有效结果。")

        except Exception as e:
            print(f"❌ 批量处理过程中出现错误: {e}")
            import traceback
            traceback.print_exc()

def print_usage():
    """打印使用说明"""
    print("\n" + "=" * 60)
    print("📖 使用说明:")
    print("=" * 60)
    print("批量处理模式（处理6个月数据）:")
    print("  python ningde_data_processor.py batch [基础目录] [输出目录]")
    print("  python ningde_data_processor.py 批量 [基础目录] [输出目录]")
    print()
    print("单文件处理模式:")
    print("  python ningde_data_processor.py single [文件路径] [输出目录]")
    print("  python ningde_data_processor.py 单个 [文件路径] [输出目录]")
    print()
    print("默认运行（批量模式）:")
    print("  python ningde_data_processor.py")
    print()
    print("示例:")
    print("  python ningde_data_processor.py batch 宁德世贸 宁德世贸/输出")
    print("  python ningde_data_processor.py single 宁德世贸/20250101.csv 宁德世贸/输出")
    print("=" * 60)

if __name__ == "__main__":
    main()
