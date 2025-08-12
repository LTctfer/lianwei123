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
    
    # 必须是xlsx文件
    if not lower.endswith('.xlsx'):
        return False
    
    # 排除明确的输出文件（更精确的排除规则）
    exclude_keywords = [
        '预警报警报告_',      # 我们生成的预警报警报告
        '预警报警统计_',      # 我们生成的统计文件  
        '批量汇总_',          # 批量处理生成的汇总文件
        '_事件明细',          # 批量事件明细
        '_统计.xlsx',        # 批量统计Excel
        '_各文件汇总'         # 各文件汇总
    ]
    
    # 只有当文件名明确包含这些关键词时才排除
    for keyword in exclude_keywords:
        if keyword in lower:
            return False
    
    return True


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
    """批量处理目录中的Excel/CSV文件，并输出整体汇总。"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"🔍 正在搜索目录: {input_dir}")
    
    # 扩展支持的文件类型：xlsx和csv
    patterns = [
        os.path.join(input_dir, '**', '*.xlsx'),
        os.path.join(input_dir, '**', '*.csv')
    ]
    
    all_found_files = []
    for pattern in patterns:
        found = glob.glob(pattern, recursive=True)
        all_found_files.extend(found)
    
    print(f"📁 发现所有Excel/CSV文件 {len(all_found_files)} 个:")
    for f in sorted(all_found_files):
        print(f"   - {f}")
    
    # 过滤出需要处理的数据文件
    files = []
    excluded_files = []
    
    for f in all_found_files:
        # 排除输出目录中的文件
        if output_dir in f:
            excluded_files.append((f, "在输出目录中"))
            continue
            
        # 排除__pycache__等系统目录
        if '__pycache__' in f or '.git' in f:
            excluded_files.append((f, "系统目录"))
            continue
            
        # 对于xlsx文件，检查是否为输入文件
        if f.lower().endswith('.xlsx'):
            if is_input_excel(f):
                files.append(f)
            else:
                excluded_files.append((f, "识别为输出文件"))
        # CSV文件直接包含（更宽松的策略）
        elif f.lower().endswith('.csv'):
            # 简单排除明显的输出文件
            basename = os.path.basename(f).lower()
            if any(keyword in basename for keyword in ['预警报警', '批量汇总', '统计']):
                excluded_files.append((f, "识别为输出文件"))
            else:
                files.append(f)
    
    print(f"\n📋 待处理文件 {len(files)} 个:")
    for f in sorted(files):
        print(f"   ✅ {f}")
    
    if excluded_files:
        print(f"\n🚫 已排除文件 {len(excluded_files)} 个:")
        for f, reason in excluded_files:
            print(f"   ❌ {f} ({reason})")

    if not files:
        print(f"\n⚠️  未在 {input_dir} 发现待处理的数据文件")
        print("💡 提示: 请检查文件路径和文件格式是否正确")
        return

    system = WasteIncinerationWarningSystemNingbo()

    all_events: List[pd.DataFrame] = []
    file_level_summary: List[Dict] = []

    print(f"\n🚀 开始批量处理 {len(files)} 个文件...")
    successful_count = 0
    failed_count = 0
    
    for idx, file_path in enumerate(sorted(files)):
        file_name = os.path.basename(file_path)
        print(f"\n[{idx+1}/{len(files)}] 📄 处理: {file_name}")
        print(f"   路径: {file_path}")
        
        try:
            # 检查文件是否存在且可读
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            if os.path.getsize(file_path) == 0:
                raise ValueError(f"文件为空: {file_path}")
            
            # 处理数据
            df = system.process_data(file_path, output_dir)
            
            if df is not None and not df.empty:
                df = df.copy()
                df.insert(0, '数据文件', file_name)
                all_events.append(df)

                stats = summarize_events(df)
                file_level_summary.append({
                    '数据文件': file_name,
                    '总事件数': len(df),
                    '预警数': int(stats['type_stats'].get('预警', 0)),
                    '报警数': int(stats['type_stats'].get('报警', 0)),
                    '状态': '成功'
                })
                successful_count += 1
                print(f"   ✅ 成功处理，发现 {len(df)} 条预警/报警事件")
            else:
                file_level_summary.append({
                    '数据文件': file_name,
                    '总事件数': 0,
                    '预警数': 0,
                    '报警数': 0,
                    '状态': '成功（无事件）'
                })
                successful_count += 1
                print(f"   ✅ 成功处理，未发现预警/报警事件")
                
        except Exception as exc:
            failed_count += 1
            error_msg = str(exc)
            print(f"   ❌ 处理失败: {error_msg}")
            file_level_summary.append({
                '数据文件': file_name,
                '总事件数': -1,
                '预警数': -1,
                '报警数': -1,
                '状态': '失败',
                '错误信息': error_msg,
            })
    
    print(f"\n📊 批量处理完成:")
    print(f"   ✅ 成功: {successful_count} 个文件")
    print(f"   ❌ 失败: {failed_count} 个文件")
    print(f"   📈 总计: {len(files)} 个文件")

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

    print("=" * 60)
    print("🏭 宁波世贸垃圾焚烧预警报警系统 - 批量处理工具")
    print("=" * 60)

    if len(sys.argv) >= 2:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT_DIR
        print("📝 使用命令行参数:")
    else:
        print("🚀 使用默认配置:")
        print("💡 提示: 可使用命令行参数指定目录")
        print("   用法: python batch_process.py <输入目录> [输出目录]")
        input_dir = DEFAULT_INPUT_DIR
        output_dir = DEFAULT_OUTPUT_DIR

    print(f"📂 输入目录: {os.path.abspath(input_dir)}")
    print(f"📂 输出目录: {os.path.abspath(output_dir)}")
    
    # 检查输入目录是否存在
    if not os.path.exists(input_dir):
        print(f"❌ 错误: 输入目录不存在 - {input_dir}")
        print("💡 请检查路径是否正确")
        return
    
    print(f"\n🔄 支持的文件格式: .xlsx, .csv")
    print(f"🔍 搜索方式: 递归搜索所有子目录")
    
    try:
        process_directory(input_dir, output_dir)
        print(f"\n🎉 批量处理任务完成！")
        print(f"📁 输出文件保存在: {os.path.abspath(output_dir)}")
    except Exception as e:
        print(f"\n❌ 批量处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()


