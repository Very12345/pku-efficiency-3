# -*- coding: utf-8 -*-
"""fonts.py — 中文字体解析辅助。

目标：SVG 用 font-family 声明（字体名不强依赖宿主）；PNG(PIL) 尽量找本机
TrueType 中文字体；PDF(reportlab) 用 CID 字体 STSong-Light（reportlab 内置，
无需外部字体文件）。找不到本机字体时如实降级并记入 uncertainty（不造假）。
"""

from __future__ import annotations

import os
from typing import List, Optional, Tuple

# 常见中文字体路径（Windows / macOS / Linux 常见部署）
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",      # 微软雅黑
    r"C:\Windows\Fonts\msyh.ttf",
    r"C:\Windows\Fonts\simhei.ttf",    # 黑体
    r"C:\Windows\Fonts\simsun.ttc",    # 宋体
    r"/System/Library/Fonts/PingFang.ttc",
    r"/System/Library/Fonts/STHeiti Light.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
]

# PIL 字体族（渲染预览用）
PIL_FAMILIES = ["Microsoft YaHei", "SimHei", "PingFang SC", "Noto Sans CJK SC"]

# SVG 字体族声明（可编辑源文件使用；浏览器/Inkscape 按序回退）
SVG_FONT_FAMILY = (
    "'Noto Sans CJK SC','Microsoft YaHei','PingFang SC','SimHei',"
    "'DejaVu Sans',sans-serif"
)


def find_ttf_font() -> Optional[str]:
    """找第一个存在的本机中文字体文件；找不到返回 None。"""
    for p in FONT_CANDIDATES:
        if os.path.isfile(p):
            return p
    return None


def pil_font_path() -> Optional[str]:
    return find_ttf_font()


def is_cjk_supported() -> bool:
    return find_ttf_font() is not None


def reportlab_font_name() -> str:
    """reportlab 内置 CID 中文字体，无需外部文件。"""
    return "STSong-Light"


def font_report() -> List[dict]:
    """供 result.json 使用的字体信息（诚实记录）。"""
    ttf = find_ttf_font()
    return [
        {"role": "svg", "mode": "font-family declaration", "family": SVG_FONT_FAMILY},
        {"role": "png", "mode": "ttf", "path": ttf, "found": ttf is not None},
        {"role": "pdf", "mode": "cid", "name": reportlab_font_name(), "embedded": "CID font（查看方需具备中文字体）"},
    ]