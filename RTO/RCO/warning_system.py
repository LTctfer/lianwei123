#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
废气处理设备预警系统
包含数据清洗、预警规则检测和可视化功能
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import warnings
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

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
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8')
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"不支持的文件格式: {file_path.suffix}")
            
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
    
    def check_rules(self, df: pd.DataFrame) -> List[Dict]:
        """检查预警规则"""
        violations = []
        
        for _, row in df.iterrows():
            timestamp = row.get('timestamp', datetime.now())
            
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
                return row.get('temperature_combustion', 0) < 760
            elif rule.rule_id == "R002":  # 出口浓度
                return row.get('concentration_out', 0) > rule.threshold_value
            elif rule.rule_id == "R003":  # 应急阀门
                return row.get('emergency_valve', 0) == 1
            elif rule.rule_id == "R004":  # 处理效率
                conc_in = row.get('concentration_in', 1)
                conc_out = row.get('concentration_out', 0)
                efficiency = 1 - (conc_out / conc_in) if conc_in > 0 else 0
                return efficiency < 0.9
            elif rule.rule_id == "R005":  # 出口温度
                return row.get('temperature_outlet', 0) > 60
            elif rule.rule_id == "R007":  # 吸附温度
                return row.get('temperature_adsorption', 0) > 40
            elif rule.rule_id == "R008":  # 脱附温度
                temp = row.get('temperature_desorption', 0)
                return temp < 90 or temp > 120
            elif rule.rule_id == "R015":  # 反应器出口温度
                return row.get('temperature_reactor_outlet', 0) > 600
            # 可以继续添加其他规则的具体实现
            
            return False
        except Exception as e:
            print(f"规则评估错误 {rule.rule_id}: {e}")
            return False
    
    def _get_rule_value(self, rule: WarningRule, row: pd.Series) -> float:
        """获取规则对应的数值"""
        value_mapping = {
            "R001": row.get('temperature_combustion', 0),
            "R002": row.get('concentration_out', 0),
            "R003": row.get('emergency_valve', 0),
            "R005": row.get('temperature_outlet', 0),
            "R007": row.get('temperature_adsorption', 0),
            "R008": row.get('temperature_desorption', 0),
            "R015": row.get('temperature_reactor_outlet', 0),
        }
        return value_mapping.get(rule.rule_id, 0)
    
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

class WarningVisualizer:
    """预警可视化器"""

    def __init__(self):
        self.colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        }

    def plot_violation_timeline(self, violations: List[Dict], save_path: str = None):
        """绘制违规时间线"""
        if not violations:
            print("没有违规数据可视化")
            return

        df_violations = pd.DataFrame(violations)

        fig, ax = plt.subplots(figsize=(15, 8))

        # 按严重程度分组绘制
        for severity in ['low', 'medium', 'high', 'critical']:
            severity_data = df_violations[df_violations['severity'] == severity]
            if not severity_data.empty:
                ax.scatter(severity_data['timestamp'], severity_data['rule_name'],
                          c=self.colors[severity], label=f'{severity.upper()}级',
                          alpha=0.7, s=60)

        ax.set_xlabel('时间')
        ax.set_ylabel('预警规则')
        ax.set_title('违规事件时间线', fontsize=16, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.xticks(rotation=45)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def plot_severity_distribution(self, summary: Dict, save_path: str = None):
        """绘制严重程度分布"""
        if not summary.get('by_severity'):
            print("没有严重程度数据可视化")
            return

        severities = list(summary['by_severity'].keys())
        counts = list(summary['by_severity'].values())
        colors = [self.colors.get(s, '#gray') for s in severities]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 饼图
        ax1.pie(counts, labels=severities, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.set_title('违规严重程度分布', fontsize=14, fontweight='bold')

        # 柱状图
        bars = ax2.bar(severities, counts, color=colors)
        ax2.set_title('违规数量统计', fontsize=14, fontweight='bold')
        ax2.set_ylabel('违规次数')

        # 在柱状图上添加数值标签
        for bar, count in zip(bars, counts):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    str(count), ha='center', va='bottom')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def plot_equipment_violations(self, summary: Dict, save_path: str = None):
        """绘制设备违规统计"""
        if not summary.get('by_equipment'):
            print("没有设备违规数据可视化")
            return

        equipment = list(summary['by_equipment'].keys())
        counts = list(summary['by_equipment'].values())

        fig, ax = plt.subplots(figsize=(12, 8))

        bars = ax.barh(equipment, counts, color='steelblue')
        ax.set_title('各设备违规次数统计', fontsize=16, fontweight='bold')
        ax.set_xlabel('违规次数')

        # 添加数值标签
        for bar, count in zip(bars, counts):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                   str(count), ha='left', va='center')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def plot_violation_duration(self, records: List[WarningRecord], save_path: str = None):
        """绘制违规持续时间分析"""
        if not records:
            print("没有违规记录数据可视化")
            return

        # 只分析已结束的违规记录
        resolved_records = [r for r in records if r.status == 'resolved' and r.duration is not None]

        if not resolved_records:
            print("没有已结束的违规记录")
            return

        df_records = pd.DataFrame([asdict(r) for r in resolved_records])

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

        # 违规持续时间分布
        ax1.hist(df_records['duration'], bins=20, color='lightcoral', alpha=0.7, edgecolor='black')
        ax1.set_title('违规持续时间分布', fontsize=14, fontweight='bold')
        ax1.set_xlabel('持续时间 (小时)')
        ax1.set_ylabel('频次')
        ax1.grid(True, alpha=0.3)

        # 各规则平均持续时间
        avg_duration = df_records.groupby('rule_name')['duration'].mean().sort_values(ascending=True)
        bars = ax2.barh(range(len(avg_duration)), avg_duration.values, color='lightgreen')
        ax2.set_yticks(range(len(avg_duration)))
        ax2.set_yticklabels(avg_duration.index)
        ax2.set_title('各规则平均违规持续时间', fontsize=14, fontweight='bold')
        ax2.set_xlabel('平均持续时间 (小时)')

        # 添加数值标签
        for i, (bar, duration) in enumerate(zip(bars, avg_duration.values)):
            ax2.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                    f'{duration:.2f}h', ha='left', va='center')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def generate_violation_report(self, violations: List[Dict], records: List[WarningRecord],
                                summary: Dict, output_dir: str = "reports"):
        """生成违规报告"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 生成图表
        self.plot_violation_timeline(violations, f"{output_dir}/timeline_{timestamp}.png")
        self.plot_severity_distribution(summary, f"{output_dir}/severity_{timestamp}.png")
        self.plot_equipment_violations(summary, f"{output_dir}/equipment_{timestamp}.png")
        self.plot_violation_duration(records, f"{output_dir}/duration_{timestamp}.png")

        # 生成Excel报告
        with pd.ExcelWriter(f"{output_dir}/violation_report_{timestamp}.xlsx") as writer:
            # 违规事件明细
            if violations:
                df_violations = pd.DataFrame(violations)
                df_violations.to_excel(writer, sheet_name='违规事件明细', index=False)

            # 违规记录汇总
            if records:
                df_records = pd.DataFrame([asdict(r) for r in records])
                df_records.to_excel(writer, sheet_name='违规记录汇总', index=False)

            # 统计汇总
            summary_df = pd.DataFrame([
                {'统计项目': '总违规次数', '数值': summary.get('total', 0)},
                {'统计项目': '进行中违规', '数值': summary.get('ongoing', 0)},
                {'统计项目': '已解决违规', '数值': summary.get('resolved', 0)},
            ])
            summary_df.to_excel(writer, sheet_name='统计汇总', index=False)

        print(f"📊 违规报告已生成: {output_dir}/violation_report_{timestamp}.xlsx")

class WarningSystem:
    """预警系统主类"""

    def __init__(self):
        self.cleaner = DataCleaner()
        self.rule_engine = WarningRuleEngine()
        self.visualizer = WarningVisualizer()

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

        # 生成可视化
        if generate_report:
            print("\n📊 生成可视化报告...")
            self.visualizer.generate_violation_report(
                violations,
                self.rule_engine.warning_records,
                summary
            )

def main():
    """主函数"""
    print("🏭 废气处理设备预警系统")
    print("=" * 50)

    # 创建预警系统
    warning_system = WarningSystem()

    # 示例：处理数据文件
    # 您可以替换为实际的数据文件路径
    test_files = [
        "data/equipment_data.xlsx",
        "data/equipment_data.csv",
        "PLCTags.csv"  # 如果有PLC数据
    ]

    for file_path in test_files:
        if Path(file_path).exists():
            print(f"\n🔍 分析文件: {file_path}")
            warning_system.run_analysis(file_path)
            break
    else:
        print("⚠️ 未找到数据文件，请将数据文件放在以下位置:")
        for file_path in test_files:
            print(f"  {file_path}")

        # 创建示例数据进行演示
        print("\n🧪 创建示例数据进行演示...")
        create_sample_data()
        warning_system.run_analysis("sample_data.xlsx")

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
