"""
中文字体设置工具
- 自动检测系统可用中文字体
- 统一配置 Matplotlib rcParams
- 设置 Plotly 全局模板以使用中文字体（带多级回退）
"""
from __future__ import annotations

import platform
from typing import List

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

try:
    import plotly.io as pio
    import plotly.graph_objects as go
except Exception:
    pio = None
    go = None


def _candidate_fonts_for_system() -> List[str]:
    system = platform.system()
    if system == "Windows":
        return [
            "Microsoft YaHei",  # 微软雅黑
            "SimHei",            # 黑体
            "SimSun",            # 宋体
            "KaiTi",             # 楷体
            "FangSong",          # 仿宋
            "Arial Unicode MS",
            "Noto Sans CJK SC",
            "Source Han Sans CN",
            "WenQuanYi Micro Hei",
            "DejaVu Sans",
        ]
    elif system == "Darwin":  # macOS
        return [
            "PingFang SC",
            "Heiti SC",
            "STHeiti",
            "STSong",
            "Arial Unicode MS",
            "Noto Sans CJK SC",
            "Source Han Sans CN",
            "DejaVu Sans",
        ]
    else:  # Linux
        return [
            "Noto Sans CJK SC",
            "Source Han Sans CN",
            "WenQuanYi Micro Hei",
            "WenQuanYi Zen Hei",
            "AR PL UKai CN",
            "AR PL UMing CN",
            "DejaVu Sans",
        ]


def setup_chinese_fonts() -> str:
    """配置 Matplotlib 与 Plotly 的中文字体。

    Returns: 被选中的中文字体名称（若未找到则返回 'DejaVu Sans'）。
    """
    candidates = _candidate_fonts_for_system()
    available = {f.name for f in fm.fontManager.ttflist}

    selected = "DejaVu Sans"
    for font in candidates:
        if font in available:
            selected = font
            break

    # Matplotlib 配置
    plt.rcParams["font.sans-serif"] = [selected, "DejaVu Sans", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    # Plotly 配置（若可用）
    if pio is not None and go is not None:
        # 构造 CSS 字体回退串
        fallback_chain = ", ".join([
            selected,
            "Microsoft YaHei",
            "SimHei",
            "PingFang SC",
            "Noto Sans CJK SC",
            "Source Han Sans CN",
            "WenQuanYi Micro Hei",
            "DejaVu Sans",
            "Arial Unicode MS",
            "sans-serif",
        ])
        try:
            pio.templates["zh_cn_font"] = go.layout.Template(
                layout=go.Layout(font=dict(family=fallback_chain))
            )
            default_tpl = pio.templates.default or "plotly"
            # 叠加中文字体模板
            pio.templates.default = f"{default_tpl}+zh_cn_font"
        except Exception:
            pass

    return selected

