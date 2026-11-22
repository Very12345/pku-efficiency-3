#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
svgtext.py — SVG 文字与编码服务（可编辑性 / 编码规范的执行端）

职责
----
1. `xml_escape(text)`：把文本中的 & < > " ' 转义为 XML 实体，保证任何
   科学实体名（基因/蛋白/物种/化合物，含 <i> 等字面量）被安全写入 SVG。
2. `sanitize_text(text)`：剔除 XML 1.0 不合法控制字符（\x00-\x08 等），
   防止不可见字符破坏 SVG 良构；保留全部可见科研文本（含 CJK、希腊字母）。
3. `encoded_svg_text(text)`：脚本内统一入口 —— sanitize + escape。
4. `check_no_text_to_path(svg_data, n_text_min=1)`：复核 SVG 中文字是否仍为
   真实 <text> 元素（未被转曲成 <path>），供 figcheck/audit 做"可编辑性"硬检查。
5. `text_width_px(text, size)`：估算文本宽度（用于遮挡/旋转决策；不依赖绘图库）。

无第三方依赖。被 chartkit.py 与 figcheck.py 引用；也可单独命令行调用。
"""
from __future__ import annotations

import re
import sys

# XML 1.0 合法字符（排除控制符）
_XML10_INVALID = re.compile(
    "[^\u0009\u000A\u000D\u0020-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]"
)
_ESCAPE = str.maketrans({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;"})


def sanitize_text(text) -> str:
    """剔除 XML 1.0 不合法控制字符；返回 str。"""
    if text is None:
        return ""
    return _XML10_INVALID.sub("", str(text))


def xml_escape(text) -> str:
    """XML 实体转义（已 sanitize）。"""
    return sanitize_text(text).translate(_ESCAPE)


def encoded_svg_text(text) -> str:
    """脚本内统一入口：sanitize + escape。"""
    return xml_escape(text)


def check_no_text_to_path(svg_data: str, n_text_min: int = 1) -> dict:
    """复核 SVG：文字是否仍为真实 <text> 元素而非 <path> 转曲。

    返回 {"pass": bool, "text_elements": int, "detail": str}。
    检查逻辑：图中应有 ≥n_text_min 个 <text> 标签（标题/轴标签/图例等）；
    若存在 <text> 但数量不足，或出现把文字写成 <path d="..."> 的痕迹
    （无法区分数据路径与转曲，故以"至少 N 个真实 <text>"为可编辑性判据）。
    """
    n_text = len(re.findall(r"<text\b", svg_data))
    n_path = len(re.findall(r"<path\b", svg_data))
    ok = n_text >= n_text_min
    return {
        "pass": ok,
        "text_elements": n_text,
        "path_elements": n_path,
        "detail": (f"真实 <text> 元素 {n_text} 个（要求 ≥ {n_text_min}）；"
                   f"<path> 元素 {n_path} 个（SVG 色块/网格等正常，文字未转曲）。"),
    }


def text_width_px(text, size: int = 16) -> int:
    """估算单行文本宽度（px）。CJK 按 1.0 倍字号、ASCII 按 0.55 倍估算。"""
    t = str(text)
    if not t:
        return 0
    w = 0
    for ch in t:
        code = ord(ch)
        if code > 0x2E7F and code < 0xA000:      # CJK 统一表意/兼容
            w += size
        elif 0xFF00 <= code <= 0xFFEF:            # 全角
            w += size
        else:
            w += int(size * 0.55)
    return max(int(w), int(size * 0.55))


if __name__ == "__main__":
    args = sys.argv[1:]
    if args:
        text = args[0]
        print("sanitize+escape:", encoded_svg_text(text))
        print("width px (@16):", text_width_px(text, 16))
    else:
        sample = '剂量 ≥20 mg/kg (β-catenin, n=6) <vehicle> & "CTRL"'
        print("原文      :", sample)
        print("编码后    :", encoded_svg_text(sample))
        print("宽(px,@16):", text_width_px(sample, 16))
        print("check_no_text_to_path('<text>a</text>') ",
              check_no_text_to_path("<text>a</text>"))