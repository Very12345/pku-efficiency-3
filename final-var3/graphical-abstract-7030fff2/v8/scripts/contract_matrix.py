#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contract_matrix.py -- 契约四形态 × 边界值矩阵：把每种容器形态与边界值逐个注入并真跑主流程。

Part of the "graphical-abstract" Skill (graphical-abstract-7030fff2, efficiency-3, axis v8).

**为什么需要这个脚本**：`references/OUTPUT_CONTRACT.md` §3 用一张表声明了"四种声明形态
全覆盖、禁止 null"；`references/failure-modes.md` 的 D14–D17 也逐条写了"该怎么办"。
但**声明不等于实现**：一个形态只在文档里被"承诺"过，在代码里可能被静默丢掉
（既不报错、也不记录），评分方看到的 `result.json` 就少了一个字段。

本脚本把 `case.json.output_contract` 当成**被测接口**，逐个注入：

  * **六种容器形态**：字符串 / 列表 / 对象 / 整数 / 浮点 / 布尔 / 嵌套对象；
  * **九类边界值**：空串 `""`、空数组 `[]`、空对象 `{}`、`0`、`0.0`、`false`、
    超长字符串（4096 字符）、声明为 `null`、以及**整个 `output_contract` 键缺失**；
  * **非法/冲突形态**：容器类型非法（列表 / 数字 / 布尔当契约）、字符串契约、
    信封保留键冲突、保留键冲突且声明为 null；
  * **组合形态**：六形态同时出现 + Unicode 键值（含 emoji/箭头）、长列表（50 条对象）。

每条用例都**真跑子进程**（`python -B <sandbox>/scripts/main.py …`），抓真实
`退出码 / status / 契约字段回显位置与类型 / result.json 的 null 数 /
check_contract.py 的退出码与 problems`，与**预先写下的期望**对照，逐行判定：

    ok       期望全部满足
    mismatch 期望未满足，但缺陷被记录（uncertainty/warnings 里有说明）或状态如实降级
    silent   期望未满足，而进程仍报 success 且**一条记录都没有** —— 这就是"静默通过"
    crash    进程没跑出 result.json（未捕获异常 / 退出码非预期）

用法（cwd 任意；`$SKILL_DIR` = 本包根）：

    # 全部 26 条，人读表 + 落 contract_matrix.json
    python "$SKILL_DIR/scripts/contract_matrix.py" --out /tmp/cm

    # 只跑某一类 / 某一条；只看汇总
    python "$SKILL_DIR/scripts/contract_matrix.py" --out /tmp/cm --only boundary
    python "$SKILL_DIR/scripts/contract_matrix.py" --out /tmp/cm --only C19 --verbose

退出码语义（本脚本自身）：
    0 = 达到 `--fail-on` 等级（strict: 全 ok；silent: 无 silent/crash；none: 只采数据）
    1 = 未达到（逐行打印是哪条、哪条期望没满足）
    2 = 用法/环境错误

**只读本包**：把 `<skill>/scripts` 复制到 `<out>/_skill/` 再跑；包内不产生任何文件
（沙箱副本里的 `__pycache__` 随沙箱一起被清掉）。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
PY = sys.executable or "python"

MATRIX_SCHEMA = "contract-matrix/1"
LONG_LEN = 4096
LONG_STR = (("A" * 96) + "·") * (LONG_LEN // 97 + 1)
LONG_STR = LONG_STR[:LONG_LEN]

U_KEYS = {"注记": {"中文键": "值 → 箭头 ⇒ 等价", "emoji": "🎯", "unit": "µm"}}
BIG_LIST = [{"index": i, "label": "条目 %02d" % i, "value": i * 1.5} for i in range(50)]

# ---------------------------------------------------------------------------
# 用例表：每条 = 一次真实注入 + 一组可判定的期望
#   inject: 写入 case.json.output_contract 的值；"__MISSING__" = 删除该键
#   expect:
#     exit / status_in          进程退出码与 status 取值域
#     echo                      {字段: ("top"|"echo"|"absent", 期望的 JSON 类型名)}
#     echo_values               {字段: 期望的 echo 值}（保留键冲突时用）
#     value / value_len / list_len   回显值的严格断言
#     no_null                   True = 顶层键与契约字段都不得为 null
#     record                    uncertainty/warnings 里必须出现的子串
#     check_contract_exit       期望 check_contract.py 的退出码
# ---------------------------------------------------------------------------
CASES = [
    # ======================= 容器形态 =======================
    dict(id="C01", cls="form", form="string", title="字符串形态回显到顶层",
         inject={"figure_note": "GA · 合成示例 · 2026"},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"figure_note": ("top", "str")},
                     value={"figure_note": "GA · 合成示例 · 2026"},
                     no_null=True, check_contract_exit=0,
                     rationale="OUTPUT_CONTRACT §3 ①：字段→类型提示，真实值必须出现在顶层")),
    dict(id="C02", cls="form", form="list", title="列表形态回显到顶层",
         inject={"target_format": ["svg", "png", "pdf"]},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"target_format": ("top", "list")},
                     value={"target_format": ["svg", "png", "pdf"]},
                     no_null=True, check_contract_exit=0,
                     rationale="§3 ②：容器形态按原值回显")),
    dict(id="C03", cls="form", form="object", title="对象形态回显到顶层",
         inject={"legend": {"position": "bottom", "font_pt": 9}},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"legend": ("top", "dict")},
                     value={"legend": {"position": "bottom", "font_pt": 9}},
                     no_null=True, check_contract_exit=0,
                     rationale="对象形态：嵌套对象必须原样保留，不得压成字符串")),
    dict(id="C04", cls="form", form="int", title="整数形态回显到顶层",
         inject={"resolution_dpi": 300},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"resolution_dpi": ("top", "int")},
                     value={"resolution_dpi": 300},
                     no_null=True, check_contract_exit=0,
                     rationale="§3 ①：整数值不得被转成字符串（下游按数值用）")),
    dict(id="C05", cls="form", form="float", title="浮点形态回显到顶层",
         inject={"bar_width_pt": 1.5},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"bar_width_pt": ("top", "float")},
                     value={"bar_width_pt": 1.5},
                     no_null=True, check_contract_exit=0,
                     rationale="§3 ①：浮点精度必须原样（JSON 往返不失真）")),
    dict(id="C06", cls="form", form="bool", title="布尔 true 形态回显到顶层",
         inject={"colorblind_safe": True},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"colorblind_safe": ("top", "bool")},
                     value={"colorblind_safe": True},
                     no_null=True, check_contract_exit=0,
                     rationale="§3 ③：布尔开关必须是真实布尔，不得写成字符串 true")),
    dict(id="C07", cls="form", form="bool", title="布尔 false 形态回显到顶层",
         inject={"grayscale_print": False},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"grayscale_print": ("top", "bool")},
                     value={"grayscale_print": False},
                     no_null=True, check_contract_exit=0,
                     rationale="§3 ③：false 是合法值，不得被空值替换（与 null 区分）")),
    dict(id="C08", cls="form", form="nested", title="三层嵌套（对象→列表→对象）",
         inject={"export": {"formats": ["svg", "png"], "dpi": {"print": 300, "screen": 96}}},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"export": ("top", "dict")},
                     value={"export": {"formats": ["svg", "png"],
                                       "dpi": {"print": 300, "screen": 96}}},
                     no_null=True, check_contract_exit=0,
                     rationale="嵌套容器任意深度都必须保持结构（评分方要按层取值）")),

    # ======================= 边界值 =======================
    dict(id="C09", cls="boundary", form="string", title="空字符串",
         inject={"annotation": ""},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"annotation": ("top", "str")},
                     value={"annotation": ""},
                     no_null=True, check_contract_exit=0,
                     rationale="空串是合法的『无内容』声明：必须以空串存在，不能变成 null 或消失")),
    dict(id="C10", cls="boundary", form="list", title="空数组",
         inject={"extra_layers": []},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"extra_layers": ("top", "list")},
                     value={"extra_layers": []},
                     no_null=True, check_contract_exit=0,
                     rationale="§3 ②：容器缺失时给空列表，显式空数组同理")),
    dict(id="C11", cls="boundary", form="int", title="整数 0",
         inject={"min_font_pt": 0},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"min_font_pt": ("top", "int")},
                     value={"min_font_pt": 0},
                     no_null=True, check_contract_exit=0,
                     rationale="0 是真值，不得被 falsy 判断误吞成空值")),
    dict(id="C12", cls="boundary", form="float", title="浮点 0.0",
         inject={"tolerance": 0.0},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"tolerance": ("top", "float")},
                     value={"tolerance": 0.0},
                     no_null=True, check_contract_exit=0,
                     rationale="0.0 与 0 在 JSON 里可区分，回显不得改写类型")),
    dict(id="C13", cls="boundary", form="object", title="空对象",
         inject={"style_overrides": {}},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"style_overrides": ("top", "dict")},
                     value={"style_overrides": {}},
                     no_null=True, check_contract_exit=0,
                     rationale="容器无内容时给空对象而不是 null")),
    dict(id="C14", cls="boundary", form="bool", title="布尔 false（边界：显式关闭）",
         inject={"require_scale_bar": False},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"require_scale_bar": ("top", "bool")},
                     value={"require_scale_bar": False},
                     no_null=True, check_contract_exit=0,
                     rationale="显式关闭与『未声明』必须可区分")),
    dict(id="C15", cls="boundary", form="string", title="超长字符串（4096 字符）",
         inject={"long_note": LONG_STR},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"long_note": ("top", "str")},
                     value_len={"long_note": LONG_LEN},
                     no_null=True, check_contract_exit=0,
                     rationale="超长值不得被截断或丢弃（截断会让复核方拿到半句话）")),
    dict(id="C16", cls="boundary", form="null", title="字段显式声明为 null",
         inject={"resolution_dpi": None},
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     echo={"resolution_dpi": ("top", "str")},
                     no_null=True, check_contract_exit=0, record="null",
                     rationale="D15：禁 null —— 归一化为空值并**记录**，不得原样回显 null")),
    dict(id="C17", cls="boundary", form="missing", title="整个 output_contract 键缺失",
         inject="__MISSING__",
         expect=dict(exit=(0,), status_in=("success",),
                     echo={}, no_null=True, check_contract_exit=0,
                     rationale="无案例契约时信封 18 键仍须齐全、不得崩")),
    dict(id="C18", cls="boundary", form="object", title="空契约对象（声明了但没字段）",
         inject={},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={}, no_null=True, check_contract_exit=0,
                     rationale="空契约是合法的『无额外字段』声明，不得被当成缺失而报错")),

    # ======================= 非法形态 / 保留键冲突 =======================
    dict(id="C19", cls="illegal", form="list", title="非法容器：用列表当 output_contract",
         inject=["svg", "png"],
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     echo={}, no_null=True, check_contract_exit=0,
                     record="output_contract",
                     rationale="容器类型非法：不得崩；必须**记录**这是一次忽略")),
    dict(id="C20", cls="illegal", form="string", title="字符串当 output_contract（合法归一化）",
         inject="svg+png",
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     echo={"note": ("top", "str")},
                     value={"note": "svg+png"},
                     no_null=True, check_contract_exit=0,
                     rationale="字符串契约按 {note: <串>} 归一化（extract.normalize_contract）")),
    dict(id="C21", cls="illegal", form="number", title="非法容器：用数字当 output_contract",
         inject=300,
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     echo={}, no_null=True, check_contract_exit=0,
                     record="output_contract",
                     rationale="数字容器非法：不得崩；必须记录忽略，不得静默丢弃")),
    dict(id="C22", cls="illegal", form="bool", title="非法容器：用 true 当 output_contract",
         inject=True,
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     echo={}, no_null=True, check_contract_exit=0,
                     record="output_contract",
                     rationale="布尔容器非法：同上；true 不是『字段清单』")),
    dict(id="C23", cls="illegal", form="object", title="保留键冲突（status / case_id）",
         inject={"status": "ready", "case_id": "brand-x", "target_format": ["svg"]},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"status": ("echo", "str"), "case_id": ("echo", "str"),
                           "target_format": ("top", "list")},
                     echo_values={"status": "ready", "case_id": "brand-x"},
                     value={"target_format": ["svg"]},
                     no_null=True, check_contract_exit=0,
                     rationale="D16：冲突键的案例值移入 output_contract_echo，顶层保留信封值")),
    dict(id="C24", cls="illegal", form="null", title="保留键冲突且声明为 null",
         inject={"summary": None, "warnings": None},
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     echo={"summary": ("echo", "str"), "warnings": ("echo", "str")},
                     echo_values={"summary": "", "warnings": ""},
                     no_null=True, check_contract_exit=0, record="null",
                     rationale="保留键 + null：既不得覆盖信封，也不得把 null 带进产物")),

    # ======================= 组合形态 =======================
    dict(id="C25", cls="combo", form="mixed", title="六种形态同时出现 + Unicode 键值",
         inject={"s": "文本", "l": [1, 2, 3], "o": {"k": "v"}, "i": 7, "f": 0.5,
                 "b": True, "u": U_KEYS},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"s": ("top", "str"), "l": ("top", "list"), "o": ("top", "dict"),
                           "i": ("top", "int"), "f": ("top", "float"), "b": ("top", "bool"),
                           "u": ("top", "dict")},
                     value={"l": [1, 2, 3], "o": {"k": "v"}, "i": 7, "f": 0.5, "b": True,
                            "u": U_KEYS},
                     no_null=True, check_contract_exit=0,
                     rationale="形态互不干扰；Unicode 键/emoji/箭头必须原样存活（UTF-8 全链）")),
    dict(id="C26", cls="combo", form="list", title="长列表（50 个对象）",
         inject={"regions": BIG_LIST},
         expect=dict(exit=(0,), status_in=("success",),
                     echo={"regions": ("top", "list")},
                     list_len={"regions": 50},
                     value={"regions": BIG_LIST},
                     no_null=True, check_contract_exit=0,
                     rationale="长结构不得被截断；顺序必须保持（评分方按下标取值）")),
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def _load_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001
        return None


def _run(argv, cwd, timeout=300):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    t0 = time.time()
    proc = subprocess.run([PY, "-B"] + argv, cwd=cwd, env=env, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return proc.returncode, proc.stdout or "", proc.stderr or "", round(time.time() - t0, 2)


def _jtype(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return type(value).__name__


def _preview(value, limit=48):
    text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    text = str(text).replace("\n", " ")
    return text if len(text) <= limit else text[:limit] + "…"


def _nested_nulls(obj, prefix=""):
    out = []
    if isinstance(obj, dict):
        for k in obj:
            if obj[k] is None:
                out.append("%s%s" % (prefix, k))
            else:
                out.extend(_nested_nulls(obj[k], "%s%s." % (prefix, k)))
    return out


def _find_hits(text, needle):
    return needle.lower() in (text or "").lower()


def _copy_fixture(base_case_dir, work):
    os.makedirs(work, exist_ok=True)
    for name in ("material.md", "task.md"):
        src = os.path.join(base_case_dir, name)
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(work, name))


# ---------------------------------------------------------------------------
# one case
# ---------------------------------------------------------------------------
def run_one(case, base_case, base_dir, sandbox_skill, box_root, keep=False):
    cid = case["id"]
    box = os.path.join(box_root, cid)
    if os.path.isdir(box):
        shutil.rmtree(box, ignore_errors=True)
    work = os.path.join(box, "work")
    out = os.path.join(box, "out")
    _copy_fixture(base_dir, work)

    injected = case["inject"]
    case_obj = json.loads(json.dumps(base_case, ensure_ascii=False))
    if injected == "__MISSING__":
        case_obj.pop("output_contract", None)
    else:
        case_obj["output_contract"] = injected
        case_obj["case_id"] = "cm-" + cid.lower()
    _write_json(os.path.join(work, "case.json"), case_obj)

    case_path = os.path.join(work, "case.json")
    rc, stdout, stderr, secs = _run([os.path.join(sandbox_skill, "main.py"),
                                     "--case", case_path, "--out", out], cwd=work)
    result = _load_json(os.path.join(out, "result.json"))
    cc_rc, cc_out = None, ""
    if result is not None:
        cc_rc, cc_out, _err, _s = _run(
            [os.path.join(sandbox_skill, "check_contract.py"),
             "--result", os.path.join(out, "result.json"), "--case", case_path], cwd=work)

    row = _evaluate(case, case_obj, rc, result, cc_rc, cc_out, stdout, stderr)
    row["seconds"] = secs
    if not keep:
        shutil.rmtree(box, ignore_errors=True)
    return row


def _evaluate(case, case_obj, rc, result, cc_rc, cc_out, stdout, stderr):
    exp = case["expect"]
    problems, observations = [], []
    contract = case_obj.get("output_contract")
    declared = contract if isinstance(contract, dict) else {}
    result = result or {}
    echo = result.get("output_contract_echo") or {}
    echo = echo if isinstance(echo, dict) else {}

    # 1) exit code -----------------------------------------------------------
    if rc not in exp.get("exit", (0,)):
        problems.append("exit %s 不在期望 %s 内" % (rc, list(exp.get("exit", (0,)))))
    if result is None:
        problems.append("未产出 result.json（stderr: %s）" % (stderr or "").strip()[:120])

    # 2) status --------------------------------------------------------------
    status = result.get("status")
    if status is not None and exp.get("status_in") and status not in exp["status_in"]:
        problems.append("status=%r 不在期望 %s 内" % (status, list(exp["status_in"])))

    # 3) echo location / type / value ----------------------------------------
    echo_values = exp.get("echo_values") or {}
    observed_echo = {}
    for key, spec_pair in (exp.get("echo") or {}).items():
        want_loc, want_type = spec_pair
        in_top, in_echo = key in result, key in echo
        top_val, echo_val = result.get(key), echo.get(key)
        got = echo_val if want_loc == "echo" else top_val
        if want_loc == "echo" and in_echo:
            loc = "echo"
        elif want_loc == "top" and in_top:
            loc = "top"
        elif not in_top and not in_echo:
            loc = "absent"
        elif (in_top and top_val is None) or (in_echo and echo_val is None):
            loc = "null"
        else:
            loc = "elsewhere"
        observed_echo[key] = {
            "location": loc,
            "type": _jtype(got),
            "preview": _preview(got),
            "top_level_value": _preview(top_val),
            "echo_value": _preview(echo_val),
        }
        if loc != want_loc or (want_type and _jtype(got) != want_type):
            problems.append("字段 %s：实测 %s/%s，期望 %s/%s"
                            % (key, loc, _jtype(got), want_loc, want_type))
            continue
        if want_loc == "echo":
            want_val = echo_values.get(key, declared.get(key))
            if want_val is not None and echo_val != want_val:
                problems.append("字段 %s：echo 值 %s 应为案例声明值 %s"
                                % (key, _preview(echo_val), _preview(want_val)))
            if declared.get(key) is not None and top_val == declared[key]:
                problems.append("字段 %s：顶层被案例值覆盖（保留键必须保留信封值）" % key)

    undeclared_missing = [k for k in declared if k not in result and k not in echo]
    if undeclared_missing:
        problems.append("声明的契约字段在产物里找不到：" + ", ".join(sorted(undeclared_missing)))

    # 4) exact values --------------------------------------------------------
    value_problems = []
    for key, want in (exp.get("value") or {}).items():
        got = result.get(key, echo.get(key)) if (key in result or key in echo) else "<absent>"
        if got != want:
            value_problems.append("字段 %s 值不符：实测 %s，期望 %s"
                                  % (key, _preview(got), _preview(want)))
    for key, want_len in (exp.get("value_len") or {}).items():
        got = result.get(key, echo.get(key))
        if not isinstance(got, str) or len(got) != want_len:
            value_problems.append("字段 %s 长度不符：实测 %s，期望 %s"
                                  % (key, len(got) if isinstance(got, str) else _jtype(got),
                                     want_len))
    for key, want_len in (exp.get("list_len") or {}).items():
        got = result.get(key, echo.get(key))
        if not isinstance(got, list) or len(got) != want_len:
            value_problems.append("字段 %s 列表长度不符：实测 %s，期望 %s"
                                  % (key, len(got) if isinstance(got, list) else _jtype(got),
                                     want_len))
    problems += value_problems

    # 5) nulls: two scopes (top-level keys / contract-declared fields) --------
    nulls_top = sorted(k for k in result if result[k] is None)
    nulls_contract = sorted(k for k in declared
                            if (k in result and result[k] is None)
                            or (k in echo and echo[k] is None))
    nulls_recursive = _nested_nulls(result)             # observation only
    if exp.get("no_null", True):
        if nulls_top:
            problems.append("result.json 顶层出现 null：" + ", ".join(nulls_top))
        if nulls_contract:
            problems.append("契约声明字段出现 null：" + ", ".join(nulls_contract))

    # 6) records -------------------------------------------------------------
    uncertainty = result.get("uncertainty") or []
    warnings = result.get("warnings") or []
    record_text = " || ".join([str(x) for x in uncertainty] + [str(x) for x in warnings])
    if exp.get("record") and not _find_hits(record_text, exp["record"]):
        problems.append("uncertainty/warnings 里找不到记录关键词 %r" % exp["record"])

    # 7) independent contract checker ----------------------------------------
    cc_valid, cc_problems = None, []
    if cc_rc is not None:
        cc_obj = json.loads(cc_out) if cc_out.strip().startswith("{") else {}
        cc_valid = cc_obj.get("valid")
        cc_problems = cc_obj.get("problems") or []
        if cc_rc != exp.get("check_contract_exit", 0):
            problems.append("check_contract exit=%s（期望 %s）：%s"
                            % (cc_rc, exp.get("check_contract_exit"), cc_problems[:2]))

    # 8) verdict -------------------------------------------------------------
    silent = bool(problems) and status == "success" and not uncertainty and not warnings
    if problems and result is None:
        verdict = "crash"
    elif not problems:
        verdict = "ok"
    elif silent:
        verdict = "silent"
    else:
        verdict = "mismatch"

    if contract is not None and not isinstance(contract, (dict, str)) and not problems:
        observations.append("非法容器（%s）被归一化为空契约，未见字段回显" % _jtype(contract))
    if status == "partial" and not uncertainty and not warnings:
        observations.append("status=partial 但 uncertainty/warnings 均为空（降级原因不可见）")
    for key, spec in observed_echo.items():
        want = (exp.get("echo") or {}).get(key)
        if want and spec["location"] == "top" and spec["type"] != want[1]:
            observations.append("字段 %s 的实际类型 %s 与声明不同且未被 flag"
                                % (key, spec["type"]))

    return {
        "id": case["id"],
        "cls": case["cls"],
        "form": case["form"],
        "title": case["title"],
        "injected": ("<output_contract 键被删除>" if case["inject"] == "__MISSING__"
                     else _preview(case["inject"], 70)),
        "declared_keys": sorted(declared) if isinstance(declared, dict) else [],
        "declared_json_type": _jtype(contract),
        "expected": case["expect"].get("rationale"),
        "measured_exit": rc,
        "measured_status": status,
        "result_json": result is not None,
        "result_top_keys": len(result) if result else 0,
        "echo_observed": observed_echo,
        "nulls_top": nulls_top,
        "nulls_contract": nulls_contract,
        "nulls_recursive": nulls_recursive,
        "uncertainty_n": len(uncertainty),
        "warnings_n": len(warnings),
        "uncertainty_sample": [str(x)[:110] for x in uncertainty[:2]],
        "check_contract_exit": cc_rc,
        "check_contract_valid": cc_valid,
        "check_contract_problems": [str(x)[:110] for x in cc_problems[:3]],
        "verdict": verdict,
        "problems": problems,
        "observations": observations,
        "stdout_head": (stdout or "").strip().splitlines()[:2],
        "stderr_head": (stderr or "").strip().splitlines()[:2],
    }


def _print_table(rows):
    print("%-5s %-9s %-8s %-9s %-8s %-6s %-6s %s"
          % ("id", "class", "form", "verdict", "exit", "status", "unc", "title"))
    print("-" * 122)
    for r in rows:
        print("%-5s %-9s %-8s %-9s %-8s %-6s %-6s %s"
              % (r["id"], r["cls"], r["form"], r["verdict"], r["measured_exit"],
                 str(r["measured_status"]), r["uncertainty_n"], r["title"][:40]))
        for p in r["problems"]:
            print("        ! %s" % p)
        for o in r["observations"]:
            print("        ~ %s" % o)


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(
        prog="contract_matrix",
        description="inject every output_contract container form and boundary value and "
                    "record the real exit/status/echo/silent behaviour")
    ap.add_argument("--out", required=True,
                    help="directory for contract_matrix.json (outside this package)")
    ap.add_argument("--case", default=os.path.join(SKILL_ROOT, "examples", "case.json"),
                    help="base case.json whose output_contract gets replaced per row")
    ap.add_argument("--only", default=None,
                    help="run one class (form|boundary|illegal|combo) or one id (C15)")
    ap.add_argument("--fail-on", default="silent", choices=["silent", "strict", "none"],
                    help="silent = only silent/crash rows fail; strict = any non-ok row fails")
    ap.add_argument("--keep", action="store_true", help="keep per-case sandboxes")
    ap.add_argument("--verbose", action="store_true", help="print per-case stdout/stderr heads")
    args = ap.parse_args(argv)

    base_path = os.path.abspath(args.case)
    if not os.path.isfile(base_path):
        print(json.dumps({"status": "error", "error": "base case.json not found: %s" % base_path},
                         ensure_ascii=False, indent=2))
        return 2
    base_case = _load_json(base_path)
    if not isinstance(base_case, dict):
        print(json.dumps({"status": "error", "error": "base case.json is not a JSON object"},
                         ensure_ascii=False, indent=2))
        return 2

    cases = CASES
    if args.only:
        sel = args.only.lower()
        cases = [c for c in CASES if c["cls"] == sel or c["id"].lower() == sel]
        if not cases:
            print(json.dumps({"error": "no case matches --only %r" % args.only,
                              "classes": sorted({c["cls"] for c in CASES}),
                              "ids": [c["id"] for c in CASES]}, ensure_ascii=False, indent=2))
            return 2

    out_root = os.path.abspath(args.out)
    if out_root == SKILL_ROOT or out_root.startswith(SKILL_ROOT + os.sep):
        print(json.dumps({"status": "error",
                          "error": "--out must be outside the skill package: %s" % out_root},
                         ensure_ascii=False, indent=2))
        return 2
    os.makedirs(out_root, exist_ok=True)
    sandbox_root = os.path.join(out_root, "_skill")
    if os.path.isdir(sandbox_root):
        shutil.rmtree(sandbox_root, ignore_errors=True)
    shutil.copytree(SCRIPT_DIR, os.path.join(sandbox_root, "scripts"))
    sandbox_skill = os.path.join(sandbox_root, "scripts")
    box_root = os.path.join(out_root, "_box")
    os.makedirs(box_root, exist_ok=True)

    rows, t0 = [], time.time()
    for c in cases:
        row = run_one(c, base_case, os.path.dirname(base_path), sandbox_skill, box_root,
                      keep=args.keep)
        rows.append(row)
        if args.verbose:
            print("[%s] exit=%s status=%s verdict=%s" % (row["id"], row["measured_exit"],
                                                         row["measured_status"], row["verdict"]))
            for line in row["stdout_head"]:
                print("    out| " + line[:150])
            for line in row["stderr_head"]:
                print("    err| " + line[:150])

    if not args.keep:
        shutil.rmtree(box_root, ignore_errors=True)
        shutil.rmtree(sandbox_root, ignore_errors=True)

    summary = {
        "rows": len(rows),
        "ok": sum(1 for r in rows if r["verdict"] == "ok"),
        "mismatch": sum(1 for r in rows if r["verdict"] == "mismatch"),
        "silent_failure": sum(1 for r in rows if r["verdict"] == "silent"),
        "crash": sum(1 for r in rows if r["verdict"] == "crash"),
        "nulls_in_result_top_level": sum(1 for r in rows if r["nulls_top"]),
        "nulls_in_contract_fields": sum(1 for r in rows if r["nulls_contract"]),
        "rows_with_nested_null_only": sum(1 for r in rows if r["nulls_recursive"]
                                          and not r["nulls_top"] and not r["nulls_contract"]),
        "check_contract_failures": sum(1 for r in rows if r["check_contract_exit"] not in (0, None)),
        "seconds_total": round(time.time() - t0, 2),
        "by_class": {k: {v: sum(1 for r in rows if r["cls"] == k and r["verdict"] == v)
                         for v in ("ok", "mismatch", "silent", "crash")}
                     for k in sorted({r["cls"] for r in rows})},
        "by_form": {k: {v: sum(1 for r in rows if r["form"] == k and r["verdict"] == v)
                        for v in ("ok", "mismatch", "silent", "crash")}
                    for k in sorted({r["form"] for r in rows})},
    }
    silent_rows = [r["id"] for r in rows if r["verdict"] == "silent"]
    crash_rows = [r["id"] for r in rows if r["verdict"] == "crash"]

    report = {
        "schema": MATRIX_SCHEMA,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "skill": "graphical-abstract",
        "python": sys.version.split()[0],
        "base_case": {"file": os.path.basename(base_path), "case_id": base_case.get("case_id")},
        "invocation": {"rows": len(rows), "only": args.only,
                       "argv": "python -B <sandbox>/scripts/main.py --case <work>/case.json "
                               "--out <box>/out"},
        "summary": summary,
        "silent_pass_list": silent_rows,
        "crash_list": crash_rows,
        "rows": rows,
        "uncovered": [
            "契约字段的**语义正确性**（例如 resolution_dpi=300 是否真的写进了 SVG）不在本矩阵范围，"
            "由 audit.checks / spec_lint 覆盖",
            "并发、超时、磁盘满等环境故障不在本矩阵范围",
            "平台侧注入（挂载缺失、配额、超时）不在本矩阵范围",
        ],
        "notes": [
            "判级口径：silent = 期望未满足 且 status=success 且 uncertainty/warnings 均为空。"
            "这个定义故意严格——『记录了但状态没降级』算 mismatch，不算 silent。",
            "每条用例的期望写在脚本 CASES 表的 rationale 里，与 references/OUTPUT_CONTRACT.md §3 "
            "和 references/failure-modes.md 的 D14–D17 对应。",
            "本矩阵的 null 判据分两个作用域：result.json **顶层键**与**契约声明字段**。"
            "嵌套信封字段 `plan.hash` 在没有 --plan 时为 null，这是 docs/OUTPUT_CONTRACT.md §2 "
            "声明过的形态（source=none 时无方案哈希），check_contract.py 判定通过，"
            "因此只作为观测列出（rows_with_nested_null_only），不计为契约违规。",
        ],
    }
    report_path = os.path.join(out_root, "contract_matrix.json")
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    _print_table(rows)
    print("")
    print("summary: rows=%d ok=%d mismatch=%d silent=%d crash=%d nulls_top=%d nulls_contract=%d "
          "cc_fail=%d  %.1fs"
          % (summary["rows"], summary["ok"], summary["mismatch"], summary["silent_failure"],
             summary["crash"], summary["nulls_in_result_top_level"],
             summary["nulls_in_contract_fields"], summary["check_contract_failures"],
             summary["seconds_total"]))
    print("report: %s" % report_path)

    if args.fail_on == "none":
        return 0
    if args.fail_on == "strict":
        return 0 if summary["ok"] == summary["rows"] else 1
    return 0 if not silent_rows and not crash_rows else 1


if __name__ == "__main__":
    sys.exit(main())
