#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
废气处理设备预警系统 - 核心算法部分
包含数据清洗、预警规则检测功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import warnings
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import random

warnings.filterwarnings('ignore')

@dataclass
class WarningRule:
    """预警规则配置"""
    rule_id: str
    rule_name: str
    description: str
    condition: str
    threshold_value: float
    threshold_unit: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    is_active: bool = True

@dataclass
class WarningRecord:
    """违规记录"""
    record_id: str
    rule_id: str
    rule_name: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[float]  # 持续时间(小时)
    max_value: float
    min_value: float
    avg_value: float
    severity: str
    status: str  # 'ongoing', 'resolved'
    affected_equipment: str

class DataCleaner:
    """数据清洗器"""
    
    def __init__(self):
        self.cleaning_log = []
    
    def load_data(self, file_path: str) -> pd.DataFrame:
        """加载数据文件"""
        file_path = Path(file_path)
        
        try:
            if str(file_path).endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            elif str(file_path).endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"不支持的文件格式: {str(file_path)}")
            
            print(f"✅ 数据加载成功: {len(df)} 行, {len(df.columns)} 列")
            return df
            
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            return pd.DataFrame()
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据清洗"""
        if df.empty:
            return df
        
        original_rows = len(df)
        self.cleaning_log.clear()
        
        # 1. 处理时间列
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['timestamp'])
            self.cleaning_log.append(f"时间格式转换: 保留 {len(df)} 行")
        
        # 2. 处理数值列
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            # 记录原始统计
            original_count = df[col].count()
            
            # 处理负值 (设为NaN)
            negative_count = (df[col] < 0).sum()
            df.loc[df[col] < 0, col] = np.nan
            
            # 处理零值 (根据列名判断是否保留)
            zero_count = (df[col] == 0).sum()
            if col in ['concentration_in', 'concentration_out', 'temperature', 'pressure']:
                # 这些列的零值可能是异常，设为NaN
                df.loc[df[col] == 0, col] = np.nan
            
            # 处理异常值 (使用IQR方法)
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_count = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            df.loc[(df[col] < lower_bound) | (df[col] > upper_bound), col] = np.nan
            
            cleaned_count = df[col].count()
            
            self.cleaning_log.append(
                f"{col}: 原始{original_count} → 清洗后{cleaned_count} "
                f"(负值:{negative_count}, 零值:{zero_count}, 异常值:{outlier_count})"
            )
        
        # 3. 删除全为NaN的行
        df = df.dropna(how='all')
        
        # 4. 对于关键列，使用前向填充
        key_columns = ['temperature_combustion', 'temperature_outlet', 'concentration_in', 'concentration_out']
        for col in key_columns:
            if col in df.columns:
                df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
        
        cleaned_rows = len(df)
        self.cleaning_log.append(f"最终结果: {original_rows} → {cleaned_rows} 行 (清洗率: {(1-cleaned_rows/original_rows)*100:.1f}%)")
        
        print("🧹 数据清洗完成:")
        for log in self.cleaning_log:
            print(f"  {log}")
        
        return df

class WarningRuleEngine:
    """预警规则引擎"""
    
    def __init__(self):
        self.rules = self._initialize_rules()
        self.warning_records = []
        self.active_warnings = {}  # 正在进行的预警
        self.rules_file = "warning_rules.json"  # 规则配置文件
        self._load_rules_from_file()  # 从文件加载规则
    
    def _initialize_rules(self) -> List[WarningRule]:
        """初始化预警规则"""
        rules = [
            WarningRule("R001", "燃烧室温度不达标", "燃烧室温度未达到规定值760℃以上", "temperature_combustion < 760", 760, "℃", "high"),
            WarningRule("R002", "废气出口污染物浓度超标", "废气出口污染物浓度超标", "concentration_out > threshold", 50, "mg/m³", "critical"),
            WarningRule("R003", "应急阀门违规开启", "应急阀门违规开启", "emergency_valve == 1", 1, "", "critical"),
            WarningRule("R004", "处理效率不达标", "出口浓度/进口浓度 > 0.1", "efficiency < 0.9", 0.9, "", "high"),
            WarningRule("R005", "废气出口温度超标", "废气出口温度不能超过60℃", "temperature_outlet > 60", 60, "℃", "medium"),
            WarningRule("R006", "治污设备未先启后停", "治污设备未先启后停", "equipment_sequence_error == 1", 1, "", "high"),
            WarningRule("R007", "吸附温度异常", "吸附温度超过40℃", "temperature_adsorption > 40", 40, "℃", "medium"),
            WarningRule("R008", "脱附温度异常", "脱附温度不在90-120℃范围", "temperature_desorption < 90 or temperature_desorption > 120", 90, "℃", "medium"),
            WarningRule("R009", "脱附时长不符合", "脱附时长少于3小时", "desorption_duration < 3", 3, "小时", "medium"),
            WarningRule("R010", "长期未脱附", "超过1个月未脱附", "days_since_last_desorption > 30", 30, "天", "high"),
            WarningRule("R011", "过滤材料失效", "颗粒物含量超过10mg/m³或压力损失超过1KPA", "particle_content > 10 or pressure_loss > 1", 10, "mg/m³", "medium"),
            WarningRule("R012", "进气温度超标", "进入催化燃烧装置的废气温度超过400℃", "temperature_inlet > 400", 400, "℃", "high"),
            WarningRule("R013", "预热室温度异常", "预热室温度超过400℃或不在250-350℃范围", "temperature_preheat > 400 or temperature_preheat < 250", 350, "℃", "medium"),
            WarningRule("R014", "催化燃烧压力异常", "催化燃烧装置压力损失超过2kpa", "pressure_loss_catalytic > 2", 2, "kPa", "medium"),
            WarningRule("R015", "反应器出口温度异常", "反应器出口温度超过600℃", "temperature_reactor_outlet > 600", 600, "℃", "critical"),
            WarningRule("R016", "催化剂使用周期超标", "催化剂使用周期超标", "catalyst_usage_days > 365", 365, "天", "high"),
        ]
        return rules
    
    def _load_rules_from_file(self):
        """从文件加载规则配置"""
        try:
            if Path(self.rules_file).exists():
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                    self.rules = []
                    for rule_data in rules_data:
                        rule = WarningRule(
                            rule_id=rule_data['rule_id'],
                            rule_name=rule_data['rule_name'],
                            description=rule_data['description'],
                            condition=rule_data['condition'],
                            threshold_value=rule_data['threshold_value'],
                            threshold_unit=rule_data['threshold_unit'],
                            severity=rule_data['severity'],
                            is_active=rule_data.get('is_active', True)
                        )
                        self.rules.append(rule)
                print(f"✅ 从文件加载了 {len(self.rules)} 条预警规则")
            else:
                # 如果文件不存在，保存默认规则到文件
                self._save_rules_to_file()
        except Exception as e:
            print(f"⚠️ 加载规则文件失败: {e}")
    
    def _save_rules_to_file(self):
        """保存规则配置到文件"""
        try:
            rules_data = []
            for rule in self.rules:
                rules_data.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'description': rule.description,
                    'condition': rule.condition,
                    'threshold_value': rule.threshold_value,
                    'threshold_unit': rule.threshold_unit,
                    'severity': rule.severity,
                    'is_active': rule.is_active
                })
            
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 已保存 {len(self.rules)} 条预警规则到文件")
        except Exception as e:
            print(f"❌ 保存规则文件失败: {e}")
    
    def update_rule_threshold(self, rule_id: str, new_threshold: float) -> bool:
        """更新规则阈值"""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                old_threshold = rule.threshold_value
                rule.threshold_value = new_threshold
                # 更新条件表达式中的阈值
                if "temperature_combustion" in rule.condition:
                    rule.condition = f"temperature_combustion < {new_threshold}"
                elif "concentration_out" in rule.condition:
                    rule.condition = f"concentration_out > {new_threshold}"
                elif "temperature_outlet" in rule.condition:
                    rule.condition = f"temperature_outlet > {new_threshold}"
                elif "temperature_adsorption" in rule.condition:
                    rule.condition = f"temperature_adsorption > {new_threshold}"
                elif "temperature_desorption" in rule.condition:
                    rule.condition = f"temperature_desorption < {new_threshold} or temperature_desorption > {new_threshold + 30}"
                elif "temperature_reactor_outlet" in rule.condition:
                    rule.condition = f"temperature_reactor_outlet > {new_threshold}"
                elif "pressure_loss_catalytic" in rule.condition:
                    rule.condition = f"pressure_loss_catalytic > {new_threshold}"
                elif "particle_content" in rule.condition:
                    rule.condition = f"particle_content > {new_threshold}"
                
                self._save_rules_to_file()
                print(f"✅ 规则 {rule_id} 阈值已更新: {old_threshold} → {new_threshold}")
                return True
        
        print(f"❌ 未找到规则ID: {rule_id}")
        return False
    
    def toggle_rule_status(self, rule_id: str) -> bool:
        """切换规则启用/禁用状态"""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                rule.is_active = not rule.is_active
                self._save_rules_to_file()
                status = "启用" if rule.is_active else "禁用"
                print(f"✅ 规则 {rule_id} 已{status}")
                return True
        
        print(f"❌ 未找到规则ID: {rule_id}")
        return False
    
    def get_all_rules(self) -> List[Dict]:
        """获取所有规则信息"""
        return [asdict(rule) for rule in self.rules]
    
    def get_rule_by_id(self, rule_id: str) -> Optional[Dict]:
        """根据ID获取规则信息"""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return asdict(rule)
        return None
    
    def check_rules(self, df: pd.DataFrame) -> List[Dict]:
        """检查预警规则"""
        violations = []
        
        for _, row in df.iterrows():
            timestamp = row.get('timestamp')
            if timestamp is None:
                timestamp = datetime.now()
            
            for rule in self.rules:
                if not rule.is_active:
                    continue
                
                violation_detected = self._evaluate_rule(rule, row)
                
                if violation_detected:
                    # 检查是否是新的违规或持续的违规
                    if rule.rule_id not in self.active_warnings:
                        # 新违规开始
                        record = WarningRecord(
                            record_id=f"{rule.rule_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                            rule_id=rule.rule_id,
                            rule_name=rule.rule_name,
                            start_time=timestamp,
                            end_time=None,
                            duration=None,
                            max_value=self._get_rule_value(rule, row),
                            min_value=self._get_rule_value(rule, row),
                            avg_value=self._get_rule_value(rule, row),
                            severity=rule.severity,
                            status='ongoing',
                            affected_equipment=self._get_equipment_name(rule)
                        )
                        self.active_warnings[rule.rule_id] = record
                        violations.append({
                            'timestamp': timestamp,
                            'rule_id': rule.rule_id,
                            'rule_name': rule.rule_name,
                            'value': self._get_rule_value(rule, row),
                            'threshold': rule.threshold_value,
                            'severity': rule.severity,
                            'status': 'start'
                        })
                    else:
                        # 更新持续违规
                        record = self.active_warnings[rule.rule_id]
                        current_value = self._get_rule_value(rule, row)
                        record.max_value = max(record.max_value, current_value)
                        record.min_value = min(record.min_value, current_value)
                        violations.append({
                            'timestamp': timestamp,
                            'rule_id': rule.rule_id,
                            'rule_name': rule.rule_name,
                            'value': current_value,
                            'threshold': rule.threshold_value,
                            'severity': rule.severity,
                            'status': 'ongoing'
                        })
                else:
                    # 检查是否有违规结束
                    if rule.rule_id in self.active_warnings:
                        record = self.active_warnings[rule.rule_id]
                        record.end_time = timestamp
                        record.duration = (record.end_time - record.start_time).total_seconds() / 3600
                        record.status = 'resolved'
                        
                        self.warning_records.append(record)
                        del self.active_warnings[rule.rule_id]
                        
                        violations.append({
                            'timestamp': timestamp,
                            'rule_id': rule.rule_id,
                            'rule_name': rule.rule_name,
                            'value': self._get_rule_value(rule, row),
                            'threshold': rule.threshold_value,
                            'severity': rule.severity,
                            'status': 'end'
                        })
        
        return violations
    
    def _evaluate_rule(self, rule: WarningRule, row: pd.Series) -> bool:
        """评估单个规则"""
        try:
            # 根据规则ID执行特定的检查逻辑
            if rule.rule_id == "R001":  # 燃烧室温度
                temp = row.get('temperature_combustion', 0)
                return float(temp or 0) < 760
            elif rule.rule_id == "R002":  # 出口浓度
                conc = row.get('concentration_out', 0)
                return float(conc or 0) > rule.threshold_value
            elif rule.rule_id == "R003":  # 应急阀门
                valve = row.get('emergency_valve', 0)
                return float(valve or 0) == 1
            elif rule.rule_id == "R004":  # 处理效率
                conc_in = float(row.get('concentration_in', 1) or 1)
                conc_out = float(row.get('concentration_out', 0) or 0)
                efficiency = 1 - (conc_out / conc_in) if conc_in > 0 else 0
                return efficiency < 0.9
            elif rule.rule_id == "R005":  # 出口温度
                temp = row.get('temperature_outlet', 0)
                return float(temp or 0) > 60
            elif rule.rule_id == "R007":  # 吸附温度
                temp = row.get('temperature_adsorption', 0)
                return float(temp or 0) > 40
            elif rule.rule_id == "R008":  # 脱附温度
                temp = float(row.get('temperature_desorption', 0) or 0)
                return temp < 90 or temp > 120
            elif rule.rule_id == "R015":  # 反应器出口温度
                temp = row.get('temperature_reactor_outlet', 0)
                return float(temp or 0) > 600
            # 可以继续添加其他规则的具体实现
            
            return False
        except Exception as e:
            print(f"规则评估错误 {rule.rule_id}: {e}")
            return False
    
    def _get_rule_value(self, rule: WarningRule, row: pd.Series) -> float:
        """获取规则对应的数值"""
        value_mapping = {
            "R001": float(row.get('temperature_combustion', 0) or 0),
            "R002": float(row.get('concentration_out', 0) or 0),
            "R003": float(row.get('emergency_valve', 0) or 0),
            "R005": float(row.get('temperature_outlet', 0) or 0),
            "R007": float(row.get('temperature_adsorption', 0) or 0),
            "R008": float(row.get('temperature_desorption', 0) or 0),
            "R015": float(row.get('temperature_reactor_outlet', 0) or 0),
        }
        return value_mapping.get(rule.rule_id, 0.0)
    
    def _get_equipment_name(self, rule: WarningRule) -> str:
        """获取设备名称"""
        equipment_mapping = {
            "R001": "燃烧室",
            "R002": "废气出口",
            "R003": "应急阀门",
            "R004": "处理系统",
            "R005": "废气出口",
            "R007": "吸附设施",
            "R008": "脱附设施",
            "R015": "反应器",
        }
        return equipment_mapping.get(rule.rule_id, "未知设备")
    
    def get_violation_summary(self) -> Dict:
        """获取违规汇总"""
        all_records = self.warning_records + list(self.active_warnings.values())
        
        if not all_records:
            return {"total": 0, "by_severity": {}, "by_equipment": {}}
        
        summary = {
            "total": len(all_records),
            "ongoing": len(self.active_warnings),
            "resolved": len(self.warning_records),
            "by_severity": {},
            "by_equipment": {},
            "by_rule": {}
        }
        
        for record in all_records:
            # 按严重程度统计
            severity = record.severity
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            
            # 按设备统计
            equipment = record.affected_equipment
            summary["by_equipment"][equipment] = summary["by_equipment"].get(equipment, 0) + 1
            
            # 按规则统计
            rule_name = record.rule_name
            summary["by_rule"][rule_name] = summary["by_rule"].get(rule_name, 0) + 1
        
        return summary

    def evaluate_row_for_alerts(self, row_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """对单条记录进行评估，返回用于前端展示的告警列表"""
        alerts: List[Dict[str, Any]] = []
        row = pd.Series(row_dict)
        timestamp = row_dict.get('timestamp', datetime.now())
        for rule in self.rules:
            if not rule.is_active:
                continue
            try:
                if self._evaluate_rule(rule, row):
                    value = self._get_rule_value(rule, row)
                    alerts.append({
                        'type': rule.rule_name,
                        'value': value,
                        'severity': rule.severity,
                        'equipment': self._get_equipment_name(rule),
                        'threshold': rule.threshold_value,
                        'unit': rule.threshold_unit,
                        'timestamp': timestamp,
                        'id': f"alert_{rule.rule_id}_{int(datetime.now().timestamp())}"
                    })
            except Exception:
                continue
        return alerts

class WarningSystem:
    """预警系统主类"""

    def __init__(self):
        self.cleaner = DataCleaner()
        self.rule_engine = WarningRuleEngine()

    def process_data_file(self, file_path: str) -> Tuple[List[Dict], Dict]:
        """处理数据文件"""
        print(f"🔄 开始处理数据文件: {file_path}")

        # 1. 加载数据
        df = self.cleaner.load_data(file_path)
        if df.empty:
            return [], {}

        # 2. 数据清洗
        df_clean = self.cleaner.clean_data(df)
        if df_clean.empty:
            print("❌ 数据清洗后无有效数据")
            return [], {}

        # 3. 预警检测
        print("🚨 开始预警规则检测...")
        violations = self.rule_engine.check_rules(df_clean)

        # 4. 生成汇总
        summary = self.rule_engine.get_violation_summary()

        print(f"✅ 预警检测完成: 发现 {len(violations)} 个违规事件")

        return violations, summary

    def run_analysis(self, file_path: str, generate_report: bool = True):
        """运行完整分析"""
        violations, summary = self.process_data_file(file_path)

        if not violations:
            print("✅ 未发现违规事件")
            return

        # 显示汇总信息
        print("\n📋 违规汇总:")
        print(f"  总违规次数: {summary.get('total', 0)}")
        print(f"  进行中违规: {summary.get('ongoing', 0)}")
        print(f"  已解决违规: {summary.get('resolved', 0)}")

        if summary.get('by_severity'):
            print("  按严重程度:")
            for severity, count in summary['by_severity'].items():
                print(f"    {severity.upper()}级: {count} 次")

def main():
    """主函数"""
    print("🏭 废气处理设备预警系统 - 核心算法")
    print("=" * 50)
    
    # 创建预警系统
    warning_system = WarningSystem()
    
    print("🎆 选择操作模式:")
    print("1. 📊 传统数据分析")
    print("2. 📈 创建示例数据并分析")
    
    choice = input("\n请选择 (1-2): ").strip()
    
    if choice == "1":
        # 传统数据分析模式
        test_files = [
            "data/equipment_data.xlsx",
            "data/equipment_data.csv", 
            "PLCTags.csv"
        ]
        
        for file_path in test_files:
            if Path(file_path).exists():
                print(f"\n🔍 分析文件: {file_path}")
                warning_system.run_analysis(file_path)
                break
        else:
            print("⚠️ 未找到数据文件")
            
    elif choice == "2":
        # 创建示例数据并分析
        print("\n🧪 创建示例数据进行演示...")
        create_sample_data()
        warning_system.run_analysis("sample_data.xlsx")
        
    else:
        print("❌ 无效选择")

def create_sample_data():
    """创建示例数据"""
    np.random.seed(42)

    # 生成24小时的示例数据
    timestamps = pd.date_range(start='2024-01-01 00:00:00', periods=1440, freq='1min')

    data = {
        'timestamp': timestamps,
        'temperature_combustion': np.random.normal(780, 50, 1440),  # 燃烧室温度
        'temperature_outlet': np.random.normal(45, 15, 1440),      # 出口温度
        'concentration_in': np.random.normal(200, 50, 1440),       # 进口浓度
        'concentration_out': np.random.normal(20, 10, 1440),       # 出口浓度
        'temperature_adsorption': np.random.normal(35, 8, 1440),   # 吸附温度
        'temperature_desorption': np.random.normal(105, 15, 1440), # 脱附温度
        'temperature_reactor_outlet': np.random.normal(550, 80, 1440), # 反应器出口温度
        'emergency_valve': np.random.choice([0, 1], 1440, p=[0.95, 0.05]), # 应急阀门
    }

    # 添加一些异常值来触发预警
    data['temperature_combustion'][100:120] = 700  # 燃烧室温度过低
    data['temperature_outlet'][200:250] = 80       # 出口温度过高
    data['concentration_out'][300:350] = 80        # 出口浓度过高
    data['temperature_reactor_outlet'][400:420] = 650  # 反应器温度过高

    df = pd.DataFrame(data)
    df.to_excel("sample_data.xlsx", index=False)
    print("✅ 示例数据已创建: sample_data.xlsx")

if __name__ == "__main__":
    main()