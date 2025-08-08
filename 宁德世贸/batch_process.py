import os
import sys
import glob
from datetime import datetime
from typing import List, Dict

import pandas as pd

# 允许脚本独立运行：将当前目录加入sys.path后使用绝对导入
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
from shishi_data_yujing_gz import WasteIncinerationWarningSystemNingbo


def is_input_excel(file_path: str) -> bool:
    """判断是否为需要处理的输入Excel，排除已生成的报告/统计文件。"""
    lower = os.path.basename(file_path).lower()
    if not lower.endswith('.xlsx'):
        return False
    # 排除我们生成的报告/统计
    exclude_keywords = [
        '预警报警报告', '预警报警统计', '批量汇总'
    ]
    return not any(k in lower for k in exclude_keywords)


def summarize_events(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """对单个文件的事件DataFrame做简单统计汇总。"""
    if df.empty:
        return {
            'type_stats': pd.Series(dtype=int),
            'event_stats': pd.Series(dtype=int),
            'furnace_stats': pd.Series(dtype=int),
        }
    type_stats = df['预警/报警类型'].value_counts()
    event_stats = df['预警/报警事件'].value_counts()
    furnace_stats = df['炉号'].value_counts().sort_index()
    return {
        'type_stats': type_stats,
        'event_stats': event_stats,
        'furnace_stats': furnace_stats,
    }


def process_directory(input_dir: str, output_dir: str) -> None:
    """批量处理目录中的.xlsx文件，并输出整体汇总。"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 递归查找子目录（如 2025年1月、2025年2月 ...）中的 .xlsx 数据文件
    pattern = os.path.join(input_dir, '**', '*.xlsx')
    files = [
        f for f in glob.glob(pattern, recursive=True)
        if is_input_excel(f)
        and ('预警文件输出' not in f)
        and ('__pycache__' not in f)
    ]

    if not files:
        print(f"未在 {input_dir} 发现待处理的.xlsx数据文件")
        return

    system = WasteIncinerationWarningSystemNingbo()

    all_events: List[pd.DataFrame] = []
    file_level_summary: List[Dict] = []

    print(f"共发现 {len(files)} 个xlsx文件，开始批量处理...")
    for idx, file_path in enumerate(sorted(files)):
        print(f"[{idx+1}/{len(files)}] 处理: {file_path}")
        try:
            df = system.process_data(file_path, output_dir)
            if df is not None and not df.empty:
                df = df.copy()
                df.insert(0, '数据文件', os.path.basename(file_path))
                all_events.append(df)

                stats = summarize_events(df)
                file_level_summary.append({
                    '数据文件': os.path.basename(file_path),
                    '总事件数': len(df),
                    '预警数': int(stats['type_stats'].get('预警', 0)),
                    '报警数': int(stats['type_stats'].get('报警', 0)),
                })
            else:
                file_level_summary.append({
                    '数据文件': os.path.basename(file_path),
                    '总事件数': 0,
                    '预警数': 0,
                    '报警数': 0,
                })
        except Exception as exc:
            print(f"❌ 处理失败: {file_path} -> {exc}")
            file_level_summary.append({
                '数据文件': os.path.basename(file_path),
                '总事件数': -1,
                '预警数': -1,
                '报警数': -1,
                '错误': str(exc),
            })

    # 生成汇总输出
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = f"宁波世贸批量汇总_{timestamp}"

    # 总表：合并所有事件
    if all_events:
        all_df = pd.concat(all_events, ignore_index=True)
        combined_csv = os.path.join(output_dir, f"{base_name}_事件明细.csv")
        all_df.to_csv(combined_csv, index=False, encoding='utf-8-sig')
        print(f"✅ 批量事件明细已保存: {combined_csv}")

        # 统计：整体类型统计/事件统计/各炉统计
        overall_type = all_df['预警/报警类型'].value_counts().rename('数量')
        overall_event = all_df['预警/报警事件'].value_counts().rename('数量')
        overall_furnace = all_df['炉号'].value_counts().sort_index().rename('数量')

        # 输出到一个Excel中多sheet
        combined_xlsx = os.path.join(output_dir, f"{base_name}_统计.xlsx")
        with pd.ExcelWriter(combined_xlsx, engine='openpyxl') as writer:
            all_df.to_excel(writer, sheet_name='事件明细', index=False)
            overall_type.to_frame().to_excel(writer, sheet_name='类型统计')
            overall_event.to_frame().to_excel(writer, sheet_name='事件统计')
            overall_furnace.to_frame().to_excel(writer, sheet_name='各炉统计')

        print(f"✅ 批量统计Excel已保存: {combined_xlsx}")

    # 文件级简表
    if file_level_summary:
        summary_df = pd.DataFrame(file_level_summary)
        summary_csv = os.path.join(output_dir, f"{base_name}_各文件汇总.csv")
        summary_df.to_csv(summary_csv, index=False, encoding='utf-8-sig')
        print(f"✅ 各文件汇总已保存: {summary_csv}")


def main():
    DEFAULT_INPUT_DIR = os.path.join('宁德世贸')
    DEFAULT_OUTPUT_DIR = os.path.join('宁德世贸', '预警文件输出')

    if len(sys.argv) >= 2:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT_DIR
    else:
        print("🚀 批量处理模式（使用默认目录）")
        print("💡 用法: python 宁德世贸/batch_process.py <输入目录> [输出目录]")
        input_dir = DEFAULT_INPUT_DIR
        output_dir = DEFAULT_OUTPUT_DIR
        print(f"📁 输入目录: {input_dir}")
        print(f"📁 输出目录: {output_dir}")

    process_directory(input_dir, output_dir)


if __name__ == '__main__':
    main()


