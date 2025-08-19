import os
import re
import sys
import shutil
from datetime import datetime
from typing import List, Tuple, Optional
import csv


SUPPORTED_EXTS = {'.xlsx', '.xls', '.csv'}


def read_companies(companies_file: Optional[str]) -> List[str]:
    if not companies_file:
        return []
    if not os.path.exists(companies_file):
        print(f"⚠️ 未找到企业名单文件: {companies_file}，将尝试从文件名中自动匹配")
        return []
    names: List[str] = []
    with open(companies_file, 'r', encoding='utf-8') as f:
        for line in f:
            name = line.strip()
            if name:
                names.append(name)
    print(f"✅ 读取企业名单 {len(names)} 个")
    return names


def parse_date_from_dir(name: str) -> Tuple[int, int, int]:
    """解析类似 '2025年1月' 或 '2025-06-01' 的目录名为 (Y,M,D)。失败则返回 (0,0,0)。"""
    # 1) 匹配 2025年1月 / 2025年06月 / 2025年06月01日
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})(?:\s*月\s*(\d{1,2})\s*日?)?", name)
    if m:
        y = int(m.group(1))
        mth = int(m.group(2))
        d = int(m.group(3)) if m.group(3) else 1
        return y, mth, d
    # 2) 尝试常见分隔 2025-06 / 2025_06_01 / 2025/06/01
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y/%m/%d", "%Y/%m", "%Y_%m_%d", "%Y_%m"):
        try:
            dt = datetime.strptime(name, fmt)
            return dt.year, dt.month, dt.day if '%d' in fmt else (dt.year, dt.month, 1)
        except Exception:
            pass
    # 3) 兜底：提取四位年和两位月
    m = re.search(r"(\d{4}).*?(\d{1,2})", name)
    if m:
        return int(m.group(1)), int(m.group(2)), 1
    return 0, 0, 0


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def detect_company(filename: str, companies: List[str]) -> Optional[str]:
    low = filename.lower()
    if companies:
        for name in companies:
            if name and name.lower() in low:
                return name
        return None
    # 没有名单时，尝试从文件名中提取公司（按中文连续字符切片作为候选）
    m = re.findall(r"[\u4e00-\u9fa5]{2,}", filename)
    # 返回最长片段作为公司名的猜测
    if m:
        return max(m, key=len)
    return None


def list_date_dirs(root: str) -> List[str]:
    items = []
    for name in os.listdir(root):
        full = os.path.join(root, name)
        if os.path.isdir(full) and name not in {"预警文件输出", "__pycache__"}:
            items.append(full)
    # 按解析日期排序
    items.sort(key=lambda p: parse_date_from_dir(os.path.basename(p)))
    return items


def organize(input_root: str, output_root: str, companies_file: Optional[str] = None, move: bool = False) -> None:
    ensure_dir(output_root)
    companies = read_companies(companies_file)

    date_dirs = list_date_dirs(input_root)
    if not date_dirs:
        print(f"未在 {input_root} 找到日期子目录")
        return

    summary_rows = []  # 总汇总

    for date_dir in date_dirs:
        date_name = os.path.basename(date_dir)
        y, m, d = parse_date_from_dir(date_name)
        for fname in os.listdir(date_dir):
            src = os.path.join(date_dir, fname)
            if not os.path.isfile(src):
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext not in SUPPORTED_EXTS:
                continue

            comp = detect_company(fname, companies)
            if not comp:
                # 未识别公司，放入 _未识别 公司目录
                comp = "_未识别"

            dest_dir = os.path.join(output_root, comp, f"{y:04d}年{m:02d}月{d:02d}日") if y else os.path.join(output_root, comp, date_name)
            ensure_dir(dest_dir)
            dest = os.path.join(dest_dir, fname)

            # 若存在同名，添加序号避免覆盖
            base, ext = os.path.splitext(dest)
            counter = 1
            while os.path.exists(dest):
                dest = f"{base}({counter}){ext}"
                counter += 1

            if move:
                shutil.move(src, dest)
                action = 'moved'
            else:
                shutil.copy2(src, dest)
                action = 'copied'

            print(f"{action}: {src} -> {dest}")
            summary_rows.append([comp, f"{y:04d}-{m:02d}-{d:02d}" if y else date_name, fname, src, dest])

    # 写出总汇总CSV
    summary_csv = os.path.join(output_root, f"组织结果汇总_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    with open(summary_csv, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["企业", "日期", "文件名", "来源路径", "目标路径"])
        # 按 企业、日期 排序
        summary_rows.sort(key=lambda r: (r[0], r[1]))
        writer.writerows(summary_rows)
    print(f"✅ 汇总已保存: {summary_csv}")


def main():
    if len(sys.argv) < 3:
        print("用法: python 宁德世贸/organize_by_company.py <输入根目录> <输出根目录> [企业名单txt] [--move]")
        print("示例: python 宁德世贸/organize_by_company.py 宁德世贸 宁德世贸/按企业整理 companies.txt")
        sys.exit(0)

    input_root = sys.argv[1]
    output_root = sys.argv[2]
    companies_file = sys.argv[3] if len(sys.argv) >= 4 and not sys.argv[3].startswith('--') else None
    move = ('--move' in sys.argv)

    organize(input_root, output_root, companies_file, move)


if __name__ == '__main__':
    main()


