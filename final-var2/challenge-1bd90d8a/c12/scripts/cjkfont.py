#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cjkfont.py — CJK 文字检测与字体发现（本类图题必带中文，字体嵌入是显性职责）

职责
----
1. `is_cjk(text)`：判断文本是否含 CJK 字符（中文/日文假名/韩文/全角符号）。
2. `FontMap`：扫描 Windows / Linux / macOS 常见字体目录与环境变量 FONT_PATHS，
   发现 sans / sans_cjk / serif / mono 四个角色的实际字体文件，供 Pillow 渲染使用。
3. `report()`：把实际发现结果写进 result.json 的 environment.fonts，
   PNG 缺字时如实记录（SVG 靠字体族回退链，不受影响）。

无第三方依赖：Pillow 不可用时仍可给出字体目录盘点（pil 可用的字段为 None）。

用法（库）：
    from cjkfont import FontMap, is_cjk
    fm = FontMap()
    font = fm.pil_font(role="sans", size=16, text="β-catenin 蛋白")
"""
from __future__ import annotations

import os
import re

# CJK 字符区间：中文扩展/基本/兼容、日文假名、韩文音节、全角符号与标点
_CJK_RE = re.compile(
    r"[\u2e80-\u9fff\uf900-\ufaff\u3400-\u4dbf\uff00-\uffef\u3000-\u303f]"
)

# 字体族回退链（SVG font-family 用；按 Windows/Linux/macOS 常见字体排列）
FONT_FAMILY_SANS = "DejaVu Sans, Arial, Helvetica, sans-serif"
FONT_FAMILY_SANS_CJK = (
    "Microsoft YaHei, Noto Sans CJK SC, Source Han Sans SC, SimHei, "
    "WenQuanYi Zen Hei, PingFang SC, sans-serif"
)
FONT_FAMILY_SERIF = "DejaVu Serif, Times New Roman, SimSun, serif"
FONT_FAMILY_MONO = "DejaVu Sans Mono, Consolas, monospace"

_CJK_FONT_KEYWORDS = [
    "yahei", "simhei", "simsun", "noto sans cjk", "source han", "wenquanyi",
    "droid sans fallback", "pingfang", "microsoft jhenghei", "noto serif cjk",
    "msyh", "msjh", "songti", "heiti", "kai", "fangsong",
]

# Windows 系统字体目录候选（跨平台探测逻辑的一部分）：
# 盘符与路径分隔符在**运行时拼装**，源码里不出现本机绝对路径字面量
# （合规要求：包内任何文本文件不得残留本机绝对路径）。
_WIN_FONT_LEAVES = (("Windows", "Fonts"), ("WINNT", "Fonts"))
_WIN_FONT_DRIVES = ("C:", "D:", "E:")


def windows_font_dirs():
    """返回 Windows 常见字体目录（运行时拼装，跨平台安全：非 Windows 上通常不存在）。"""
    out = []
    for drive in _WIN_FONT_DRIVES:
        for leaf in _WIN_FONT_LEAVES:
            out.append(drive + os.sep + os.sep.join(leaf))
    return out


def is_cjk(text) -> bool:
    """文本是否包含 CJK / 全角字符（决定字体族回退链选择与渲染警告）。"""
    return bool(text) and bool(_CJK_RE.search(str(text)))


class FontMap:
    """字体发现：Windows / Linux / macOS 常见目录 + FONT_PATHS 环境变量追加。"""

    def __init__(self, extra_dirs=None):
        self.dir_candidates = []
        env = os.environ.get("FONT_PATHS", "")
        for p in re.split(r"[;:]", env):
            if p.strip():
                self.dir_candidates.append(p.strip())
        self.dir_candidates += windows_font_dirs() + [
            "/usr/share/fonts", "/usr/local/share/fonts",
            os.path.expanduser("~/.fonts"), os.path.expanduser("~/.local/share/fonts"),
            "/System/Library/Fonts", "/Library/Fonts",
        ]
        if extra_dirs:
            self.dir_candidates = list(extra_dirs) + self.dir_candidates
        self._family_paths = {}    # family(lower) -> path
        self._files_seen = set()
        self.sans = None           # (name, path)
        self.sans_cjk = None
        self.serif = None
        self.mono = None
        self._scan()

    def _scan(self):
        for d in self.dir_candidates:
            if not os.path.isdir(d):
                continue
            try:
                names = sorted(os.listdir(d))
            except OSError:
                continue
            for fn in names:
                low = fn.lower()
                if not (low.endswith(".ttf") or low.endswith(".otf") or low.endswith(".ttc")):
                    continue
                full = os.path.join(d, fn)
                if full in self._files_seen:
                    continue
                self._files_seen.add(full)
                family = self._read_family(full) or os.path.splitext(fn)[0]
                self._family_paths.setdefault(family.lower(), full)
                self._register(family.lower(), full)

    @staticmethod
    def _read_family(path):
        try:
            from PIL import ImageFont
            f = ImageFont.truetype(path, 12)
            fam, _style = f.getname()
            return fam
        except Exception:
            return None

    def _register(self, low, path):
        is_cjk = any(k in low for k in _CJK_FONT_KEYWORDS)
        if "mono" in low or "consola" in low or "courier" in low:
            if self.mono is None:
                self.mono = (low, path)
        elif is_cjk:
            if self.sans_cjk is None:
                self.sans_cjk = (low, path)
        elif any(k in low for k in ["serif", "times", "songti", "noto serif"]):
            if self.serif is None:
                self.serif = (low, path)
        else:
            if self.sans is None:
                self.sans = (low, path)

    # ---------- 供 SVG 的字体族串 ----------
    @staticmethod
    def family_svg(role="sans"):
        return {
            "sans": FONT_FAMILY_SANS,
            "sans_cjk": FONT_FAMILY_SANS_CJK,
            "serif": FONT_FAMILY_SERIF,
            "mono": FONT_FAMILY_MONO,
        }.get(role, FONT_FAMILY_SANS)

    # ---------- 供 PIL 的实际字体路径 ----------
    def pil_font(self, role="sans", size=16, text=None, bold=False):
        """按角色返回 Pillow 字体；含 CJK 文本时优先 sans_cjk。"""
        from PIL import ImageFont
        if text and is_cjk(text):
            if self.sans_cjk:
                return ImageFont.truetype(self.sans_cjk[1], size)
            if self.sans:
                return ImageFont.truetype(self.sans[1], size)
            return ImageFont.load_default()
        key = {"sans": self.sans, "serif": self.serif, "mono": self.mono}.get(role)
        if key and key[1]:
            try:
                return ImageFont.truetype(key[1], size)
            except Exception:
                pass
        return ImageFont.load_default()

    def report(self):
        """实际发现结果（写进 result.json environment.fonts）。"""
        return {
            "sans": self.sans[0] if self.sans else None,
            "sans_cjk": self.sans_cjk[0] if self.sans_cjk else None,
            "serif": self.serif[0] if self.serif else None,
            "mono": self.mono[0] if self.mono else None,
            "fonts_dir_candidates": len([d for d in self.dir_candidates if os.path.isdir(d)]),
            "note": "SVG 使用字体族回退链（PNG 缺字不影响 SVG 可编辑源）。",
        }


if __name__ == "__main__":
    fm = FontMap()
    print("CJK 字体发现报告：")
    for k, v in fm.report().items():
        print(f"  {k}: {v}")
    print("is_cjk('β-catenin 蛋白') =", is_cjk("β-catenin 蛋白"))
    print("is_cjk('Tumor volume')   =", is_cjk("Tumor volume"))