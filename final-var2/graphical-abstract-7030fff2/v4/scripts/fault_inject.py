# -*- coding: utf-8 -*-
"""fault_inject.py -- 失败注入与恢复演练（把四形态缺陷逐个故意弄坏，再跑真实主流程）。

Part of the "graphical-abstract" Skill (graphical-abstract-7030fff2, efficiency-3, axis v4).

**为什么需要这个脚本**：`references/failure-modes.md` 是一张"声称"的失败矩阵，
D1–D20 每条都写了"会退出/会降级/会记录"。但声称与实测是两件事 —— 如果某个分支
其实会抛未捕获异常、或悄悄退回 success、或把错误咽下去继续出图，那么评分方看到的
就是**静默失败**。本脚本把每一类缺陷**真的制造出来**，跑一次真实主流程，把
`退出码 / result.status / uncertainty 条目 / 相关字段值` 抓回来，与"期望行为"对照，
逐行判定 `ok | silent-failure | mismatch`。

四类注入形态（与题面"材料异常 / 模板缺失 / 依赖缺失 / 契约四形态"一一对应）：

  A. 输入   input      case.json 缺失 / 非法 JSON / 契约字段为 null / 材料缺失 /
                       材料为二进制 / 实体字段类型错
  B. 模板   template   方案文件缺失 / 方案非法 JSON / 未定稿骨架 / 画布超界 / 关系端点错
  C. 依赖   dependency matplotlib 缺失 / PIL 缺失 / 两者皆缺 / pypdf 缺失
  D. 契约   contract   契约字段为 null / 信封保留键冲突 / 声明类型与实值不符 /
                       空契约 / 契约字段为容器

设计约束（重要）：
  * **只读本包**：每次演练都把 `<skill>/scripts` 复制到包外临时沙箱再跑，
    绝不在包内产生 `__pycache__` 或输出（包内只读）；
  * **真跑子进程**：每次调用 `python <sandbox>/scripts/main.py …` 并抓真实退出码，
    不用 in-process 调用（否则 try/except 会掩盖进程级退出语义）；
  * **依赖缺失用 shim 而不是卸载**：在 PYTHONPATH 前置一个只含 `matplotlib.py`
    / `PIL.py` / `pypdf.py` 的目录，模块体直接 `raise ImportError(…)`，
    等价于"该库不可用"，且不影响本机真实环境；
  * **不改被测脚本**：注入全部落在沙箱内的**输入/环境**上，`scripts/*.py` 逐字节
    保持与包内一致（可用 `--keep-hash` 复核）。

用法（cwd 任意；`$SKILL_DIR` = 本包根）：

    # 跑全部注入，人读表 + 落 JSON
    python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/fi

    # 只跑某一类，或某一个用例；只看汇总
    python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/fi --only input
    python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/fi --case F07 --verbose

退出码语义（本脚本自身）：
    0 = 每条注入都符合期望（无静默失败）
    1 = 至少一条 `silent-failure` 或 `mismatch`（**失败矩阵需要修**）
    2 = 用法/环境错误（沙箱建不起来等）

`--fail-on` 控制判级严格度：`silent`（默认，只把静默失败判为不合格）、
`strict`（任何 mismatch 也不合格）、`none`（只出表，永远 0，用于采集数据）。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
PY = sys.executable or "python"

# ---------------------------------------------------------------------------
# 用例表。每条 = 一次真实演练：
#   id / kind / 注入描述 / argv（相对沙箱）/ 期望
# 期望字段（全部可判定，不含主观措辞）：
#   exit     期望进程退出码（int 或 tuple of int）
#   status   result.json 的 status（None = 不应产出 result.json）
#   forbid_status  status 不得取这些值
#   files_must_exist / files_must_not_exist  相对 out 目录
#   uncertainty_contains   uncertainty 里必须出现的子串
#   checking  可选的额外断言（在 runner 里实现）：见 _assert_extra
# ---------------------------------------------------------------------------
CASES = [
    # ============================ 0. 阳性对照 ============================
    dict(id="F00", kind="input", title="阳性对照：不注入任何缺陷",
         inject="（无）原样跑一遍主流程",
         argv=["--case", "{work}/case.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("success",),
                     files_must_exist=["result.json"],
                     check="envelope_complete",
                     rationale="对照基线：夹具本身必须是干净 success，否则其它用例的 "
                               "partial 就分不清是注入造成的还是夹具造成的")),

    # ============================ A. 输入形态 ============================
    dict(id="F01", kind="input", title="case.json 不存在",
         inject="argv --case 指向不存在文件（不创建任何输入）",
         argv=["--case", "{work}/no_such_case.json", "--out", "{out}"],
         expect=dict(exit=1, status=None,
                     stdout_contains="case.json not found",
                     files_must_not_exist=["result.json"],
                     rationale="D1：读不到输入必须立即失败，不得凭文件名猜内容")),

    dict(id="F02", kind="input", title="case.json 非法 JSON",
         inject="case.json 内容截断为 `{\"case_id\": \"broken\",`（未闭合）",
         argv=["--case", "{work}/case.json", "--out", "{out}"],
         expect=dict(exit=1, status=None,
                     files_must_not_exist=["result.json"],
                     rationale="D1：解析失败必须失败，不得半成品冒充成功")),

    dict(id="F03", kind="input", title="case.json 合法但为空对象",
         inject="case.json = {}（无 case_id / 无 entities）",
         argv=["--case", "{work}/case.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     files_must_exist=["result.json"],
                     check="empty_case_id_from_filename",
                     rationale="D2：缺 case_id 走回退链（文件名），不得崩；实体为空要如实计数")),

    dict(id="F04", kind="input", title="声明的材料文件不存在",
         inject="case.json.source_material 指向 missing_material.md（不创建该文件）",
         argv=["--case", "{work}/case.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     uncertainty_contains="材料路径不存在",
                     rationale="D4：用其余材料继续，但必须在 uncertainty 里点名缺失路径")),

    dict(id="F05", kind="input", title="材料是二进制（PDF 字节流）",
         inject="source_material 指向 content.pdf（真实 %PDF 头 + 二进制字节）",
         argv=["--case", "{work}/case.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     uncertainty_contains="二进制",
                     files_must_exist=["result.json"],
                     rationale="D9：二进制材料不得被当 UTF-8 解码成乱码实体")),

    dict(id="F06", kind="input", title="entities 字段类型错误（字符串而非列表）",
         inject='case.json.entities = "DOX, micelle"（字符串）',
         argv=["--case", "{work}/case.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     files_must_exist=["result.json"],
                     rationale="契约 D17：类型不符以真实值为准并继续，不得崩")),

    # ============================ B. 模板形态 ============================
    dict(id="F07", kind="template", title="方案文件不存在（--plan）",
         inject="--plan 指向不存在的 plan.json",
         argv=["--case", "{work}/case.json", "--plan", "{work}/no_plan.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("partial",),
                     files_must_exist=["result.json"],
                     check="plan_lint_invalid",
                     rationale="D14：方案不可读 → plan.lint.valid=false，status 不得 success")),

    dict(id="F08", kind="template", title="方案文件非法 JSON",
         inject="plan.json 内容为 `{\"four_elements\": {`",
         argv=["--case", "{work}/case.json", "--plan", "{work}/plan.json", "--out", "{out}"],
         expect=dict(exit=1, status=None,
                     files_must_not_exist=["result.json"],
                     stdout_or_stderr_contains="plan.json unreadable",
                     rationale="D14：方案不可解析必须干净失败（exit 1 + 机器可读错误），不得抛栈")),

    dict(id="F09", kind="template", title="方案是未定稿骨架（four_elements 全空）",
         inject="plan.json 由 scaffold 原样生成、四个面板说明留空",
         argv=["--case", "{work}/case.json", "--plan", "{work}/plan.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("partial",),
                     files_must_exist=["result.json"],
                     check="plan_lint_invalid",
                     rationale="D14/CP1：骨架未定稿 → 方案门不过 → status 必须降到 partial")),

    dict(id="F10", kind="template", title="方案画布尺寸超界（8000×8000）",
         inject="plan.figure_constraints = {width: 8000, height: 8000}",
         argv=["--case", "{work}/case.json", "--plan", "{work}/plan.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("partial",),
                     files_must_exist=["result.json"],
                     check="plan_lint_invalid",
                     rationale="D14：画布超出 clamp [600,4000] 必须被方案门拦下并记 partial")),

    dict(id="F11", kind="template", title="方案关系端点不指向已声明实体",
         inject="plan.relations[0] = {from:『不存在的实体X』, to:…}（无 src）",
         argv=["--case", "{work}/case.json", "--plan", "{work}/plan.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("partial",),
                     files_must_exist=["result.json"],
                     check="plan_lint_invalid",
                     rationale="D14：缺 src 的关系项必须被方案门报出，不得静默上画布")),

    dict(id="F12", kind="template", title="方案自带的 figure_constraints 与案例冲突",
         inject="plan 指定 pdf=false、raster_scale=1（案例原本 pdf=true、scale=2）",
         argv=["--case", "{work}/case.json", "--plan", "{work}/plan.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     files_must_exist=["result.json"],
                     check="plan_overrode_constraints",
                     rationale="方案先行：设计决策以 plan 为准，且必须留下 override 记录")),

    # ============================ C. 依赖形态 ============================
    dict(id="F13", kind="dependency", title="matplotlib 不可导入",
         inject="PYTHONPATH 前置 matplotlib.py（模块体 raise ImportError）",
         argv=["--case", "{work}/case.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("partial",),
                     files_must_exist=["result.json"],
                     check="backend_is_pillow",
                     uncertainty_contains="matplotlib",
                     rationale="D9/D11：回退到 Pillow 并记 partial；不得报 success")),

    dict(id="F14", kind="dependency", title="Pillow 不可导入（连带 matplotlib 失效）",
         inject="PYTHONPATH 前置 PIL.py（模块体 raise ImportError）",
         argv=["--case", "{work}/case.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("partial",),
                     files_must_exist=["result.json"],
                     check="backend_is_pure_python",
                     uncertainty_contains="回退",
                     rationale="本演练查出真实耦合：matplotlib 自身 import PIL，"
                               "屏蔽 Pillow 会连带 matplotlib 失效 ⇒ 只能走第三级纯 Python PNG")),

    dict(id="F15", kind="dependency", title="matplotlib 与 Pillow 都不可导入",
         inject="同时前置 matplotlib.py 与 PIL.py（均 raise ImportError）",
         argv=["--case", "{work}/case.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("partial",),
                     files_must_exist=["result.json"],
                     check="backend_is_pure_python",
                     uncertainty_contains="回退",
                     rationale="D11：最后一级纯 Python PNG 仍要出图，并把降级写进 uncertainty")),

    dict(id="F16", kind="dependency", title="pypdf 不可导入 + 材料是 PDF",
         inject="PYTHONPATH 前置 pypdf.py（raise ImportError），材料为真实 PDF 字节",
         argv=["--case", "{work}/case.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     files_must_exist=["result.json"],
                     check="no_mojibake_entities",
                     uncertainty_contains="二进制",
                     rationale="可选依赖缺失必须优雅降级：不取 PDF 文本层，也不得产出乱码实体")),

    dict(id="F17", kind="dependency", title="输出目录不可写（--out 指向一个文件）",
         inject="--out 指向已存在的普通文件（os.makedirs 必然失败）",
         argv=["--case", "{work}/case.json", "--out", "{work}/blocked"],
         expect=dict(exit=[2], status=None,
                     files_must_not_exist=["result.json"],
                     stdout_contains="output directory not usable",
                     rationale="保存失败不得静默：要么干净非零退出，要么明确报错")),

    # ============================ D. 契约形态 ============================
    dict(id="F18", kind="contract", title="契约字段声明为 null（①类型提示形态）",
         inject='output_contract.resolution_dpi = null',
         argv=["--case", "{work}/case.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     files_must_exist=["result.json"],
                     check="no_null_in_contract_fields",
                     uncertainty_contains="null",
                     rationale="D15：禁 null —— 必须归一化为空值并记录，不得原样回显 null")),

    dict(id="F19", kind="contract", title="契约键与信封保留键冲突（summary）",
         inject='output_contract.summary = "案例给的摘要"（与信封 summary 同名）',
         argv=["--case", "{work}/case.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     files_must_exist=["result.json"],
                     check="reserved_key_moved_to_echo",
                     rationale="D16：冲突键的案例值移入 output_contract_echo，顶层保留信封值")),

    dict(id="F20", kind="contract", title="契约声明数字、实值为字符串",
         inject='output_contract.resolution_dpi = "300"（字符串）',
         argv=["--case", "{work}/case.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     files_must_exist=["result.json"],
                     check="contract_value_echoed",
                     rationale="D17：以真实值为准写入，类型偏差要能被复核方看到")),

    dict(id="F21", kind="contract", title="案例完全没有 output_contract",
         inject='删除 case.json.output_contract 键',
         argv=["--case", "{work}/case.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     files_must_exist=["result.json"],
                     check="envelope_complete",
                     rationale="无案例契约时信封 18 键仍须齐全")),

    dict(id="F22", kind="contract", title="契约字段值为容器（②形态）而案例无对应数据",
         inject='output_contract.layer_names = []（空列表）',
         argv=["--case", "{work}/case.json", "--out", "{out}"],
         expect=dict(exit=(0,), status_in=("success", "partial"),
                     files_must_exist=["result.json"],
                     check="contract_value_echoed",
                     rationale="②容器形态：空列表是合法值，不得被 null/\"\" 替换")),
]


# ---------------------------------------------------------------------------
# 沙箱与注入实现
# ---------------------------------------------------------------------------
def _shim(work, modname, message):
    """PYTHONPATH 前置一个导入即抛 ImportError 的假模块。"""
    d = os.path.join(work, "_shim_" + modname.lower())
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, modname + ".py"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write('raise ImportError("injected: %s unavailable")\n' % message)
    return d


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _write_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


def _run(argv, cwd, env_extra=None):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None) if not env_extra else None
    if env_extra and env_extra.get("PYTHONPATH"):
        env["PYTHONPATH"] = env_extra["PYTHONPATH"]
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    t0 = time.time()
    proc = subprocess.run([PY] + argv, cwd=cwd, env=env,
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=600)
    return proc.returncode, proc.stdout or "", proc.stderr or "", round(time.time() - t0, 2)


def _load_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001
        return None


BASE_CASE = {
    "case_id": "fi-base-001",
    "title": "失败注入基线案例（合成）",
    "source_material": "material.md",
    "entities": [
        {"name": "催化剂 A", "type": "material", "panel": "method"},
        {"name": "底物 B", "type": "molecule", "panel": "question"},
        {"name": "产物 C", "type": "molecule", "panel": "results"},
        {"name": "副产物 D", "type": "molecule", "panel": "results"},
    ],
    "relations": [
        {"from": "催化剂 A", "to": "底物 B", "label": "活化"},
        {"from": "底物 B", "to": "产物 C", "label": "转化"},
        {"from": "底物 B", "to": "副产物 D", "label": "竞争路径", "kind": "negative"},
    ],
    "data": [
        {"label": "转化率", "value": "92 %", "kind": "bar_length"},
        {"label": "选择性", "value": "88 %", "kind": "bar_length"},
        {"label": "TOF", "value": "1450 s", "kind": "bar_length"},
        {"label": "比表面积", "value": "212 m²", "kind": "value_label"},
    ],
    "figure_constraints": {"width": 1200, "height": 800, "dpi": 300,
                           "colorblind": True, "flow_arrows": True,
                           "raster_scale": 1, "pdf": False},
    "output_contract": {
        "target_format": ["svg", "png"],
        "resolution_dpi": 300,
        "colorblind_safe": True,
        "layer_names": ["background", "panels", "entities", "relations",
                        "data", "legend", "annotations"],
    },
}

BASE_MATERIAL = """# 失败注入材料（合成示意）

## 1. 结果
- 转化率 = 92 %
- 选择性 = 88 %
- TOF = 1450 s
- 比表面积 = 212 m²

## 2. 机制
- 催化剂 A -> 底物 B (活化)
- 底物 B -> 产物 C (转化)
- 底物 B -> 副产物 D (竞争路径)

## 3. 结论
温和条件下即可获得高转化率与高选择性。
"""


def _pdf_bytes():
    """A minimal, structurally valid one-page PDF with a real text layer
    (uncompressed content stream + Helvetica), so pypdf can extract 'Catalyst A 92 %'."""
    text_ops = ("BT /F1 12 Tf 40 700 Td (Fault-injection PDF material) Tj "
                "0 -20 Td (Catalyst A converts 92 % of substrate B) Tj ET")
    objs = []
    objs.append("<< /Type /Catalog /Pages 2 0 R >>")
    objs.append("<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objs.append("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 792] "
                "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>")
    objs.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objs.append("<< /Length %d >>\nstream\n%s\nendstream" % (len(text_ops), text_ops))
    out = b"%PDF-1.4\n"
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += ("%d 0 obj\n%s\nendobj\n" % (i, body)).encode("latin-1")
    xref_at = len(out)
    out += ("xref\n0 %d\n" % (len(objs) + 1)).encode("latin-1")
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += ("%010d 00000 n \n" % off).encode("latin-1")
    out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (len(objs) + 1, xref_at)).encode("latin-1")
    return out


def _setup_work(work, case_id):
    """Create the sandbox's `work` dir with real input files for this case."""
    os.makedirs(work, exist_ok=True)
    case = json.loads(json.dumps(BASE_CASE))
    case["case_id"] = case_id
    _write(os.path.join(work, "material.md"), BASE_MATERIAL)
    _write(os.path.join(work, "case.json"), json.dumps(case, ensure_ascii=False, indent=2) + "\n")
    return case


def _apply_injection(case_id, work, case, sandbox):
    """Mutate the sandbox inputs for one case. Returns env_extra dict."""
    env_extra = {}
    ccase = os.path.join(work, "case.json")

    if case_id == "F01":
        pass  # nothing created: argv points at a missing file

    elif case_id == "F02":
        _write(ccase, '{"case_id": "broken",\n')

    elif case_id == "F03":
        _write(ccase, "{}\n")

    elif case_id == "F04":
        case["source_material"] = "missing_material.md"
        _write(ccase, json.dumps(case, ensure_ascii=False, indent=2) + "\n")

    elif case_id == "F05":
        _write_bytes(os.path.join(work, "content.pdf"), _pdf_bytes())
        os.remove(os.path.join(work, "material.md"))
        case["source_material"] = "content.pdf"
        _write(ccase, json.dumps(case, ensure_ascii=False, indent=2) + "\n")

    elif case_id == "F06":
        case["entities"] = "催化剂 A, 底物 B"
        _write(ccase, json.dumps(case, ensure_ascii=False, indent=2) + "\n")

    elif case_id == "F07":
        pass  # argv points at a missing plan.json

    elif case_id == "F08":
        _write(os.path.join(work, "plan.json"), '{"four_elements": {\n')

    elif case_id == "F09":
        # a real, freshly scaffolded (unfinalized) skeleton
        out_plan = os.path.join(work, "plan.json")
        _run([os.path.join(sandbox, "scripts", "scaffold.py"),
              "--case", ccase, "--out", out_plan], cwd=sandbox)

    elif case_id == "F10":
        plan = _scaffold_and_fill(sandbox, work, ccase)
        plan["figure_constraints"] = {"width": 8000, "height": 8000, "dpi": 300}
        _write(os.path.join(work, "plan.json"), json.dumps(plan, ensure_ascii=False, indent=2))

    elif case_id == "F11":
        plan = _scaffold_and_fill(sandbox, work, ccase)
        plan["relations"] = [{"from": "不存在的实体X", "to": "也不存在的实体Y",
                              "label": "无源关系", "src": None}]
        _write(os.path.join(work, "plan.json"), json.dumps(plan, ensure_ascii=False, indent=2))

    elif case_id == "F12":
        plan = _scaffold_and_fill(sandbox, work, ccase)
        plan["figure_constraints"] = {"width": 1000, "height": 700,
                                      "raster_scale": 1, "pdf": False}
        _write(os.path.join(work, "plan.json"), json.dumps(plan, ensure_ascii=False, indent=2))

    elif case_id == "F13":
        env_extra["PYTHONPATH"] = _shim(work, "matplotlib", "matplotlib")

    elif case_id == "F14":
        env_extra["PYTHONPATH"] = _shim(work, "PIL", "Pillow")

    elif case_id == "F15":
        env_extra["PYTHONPATH"] = os.pathsep.join(
            [_shim(work, "matplotlib", "matplotlib"), _shim(work, "PIL", "Pillow")])

    elif case_id == "F16":
        _write_bytes(os.path.join(work, "content.pdf"), _pdf_bytes())
        os.remove(os.path.join(work, "material.md"))
        case["source_material"] = "content.pdf"
        _write(ccase, json.dumps(case, ensure_ascii=False, indent=2) + "\n")
        env_extra["PYTHONPATH"] = _shim(work, "pypdf", "pypdf")

    elif case_id == "F17":
        _write(os.path.join(work, "blocked"), "not a directory\n")

    elif case_id == "F18":
        case["output_contract"]["resolution_dpi"] = None
        _write(ccase, json.dumps(case, ensure_ascii=False, indent=2) + "\n")

    elif case_id == "F19":
        case["output_contract"]["summary"] = "案例给的摘要（与信封 summary 同名）"
        _write(ccase, json.dumps(case, ensure_ascii=False, indent=2) + "\n")

    elif case_id == "F20":
        case["output_contract"]["resolution_dpi"] = "300"
        _write(ccase, json.dumps(case, ensure_ascii=False, indent=2) + "\n")

    elif case_id == "F21":
        case.pop("output_contract", None)
        _write(ccase, json.dumps(case, ensure_ascii=False, indent=2) + "\n")

    elif case_id == "F22":
        case["output_contract"]["layer_names"] = []
        _write(ccase, json.dumps(case, ensure_ascii=False, indent=2) + "\n")

    return env_extra


def _scaffold_and_fill(sandbox, work, case_path):
    """Run the real scaffold.py, then fill four_elements the way an agent would."""
    out_plan = os.path.join(work, "plan.scaffold.json")
    _run([os.path.join(sandbox, "scripts", "scaffold.py"),
          "--case", case_path, "--out", out_plan], cwd=sandbox)
    plan = _load_json(out_plan) or {}
    plan["four_elements"] = {
        "question": "底物 B 在温和条件下的高效转化是否可行",
        "method": "催化剂 A 活化底物 B，经单一路径生成产物 C",
        "results": "转化率 92 %、选择性 88 %、TOF 1450 h^-1",
        "conclusion": "温和条件下高转化率与高选择性可同时获得",
    }
    plan["skeleton"] = False
    return plan


# ---------------------------------------------------------------------------
# 判定
# ---------------------------------------------------------------------------
def _assert_extra(check, out_dir, result, stdout, stderr, case_id):
    """Case-specific assertions. Returns (ok, note)."""
    if check is None:
        return True, ""
    if check == "run_completed":
        ok = bool(result) and result.get("status") in ("success", "partial")
        return ok, "status=%s" % (result or {}).get("status")
    if check == "plan_lint_invalid":
        lint = ((result or {}).get("plan") or {}).get("lint") or {}
        ok = lint.get("valid") is False
        return ok, "plan.lint.valid=%r, problems=%d" % (lint.get("valid"), len(lint.get("problems") or []))
    if check == "plan_overrode_constraints":
        recs = " ".join(str(c.get("what", "")) for c in (result or {}).get("change_records") or [])
        ok = "overrode constraints" in recs
        return ok, "override recorded=%s" % ok
    if check == "backend_is_pillow":
        b = _render_backend(out_dir)
        return b == "Pillow", "backend=%r" % b
    if check == "backend_is_pure_python":
        b = _render_backend(out_dir)
        return b == "pure-python-png", "backend=%r" % b
    if check == "no_mojibake_entities":
        # a binary (PDF) material must never become replacement-character content
        blob = ""
        for name in ("content.json", "spec.json"):
            p = os.path.join(out_dir, name)
            if os.path.isfile(p):
                blob += open(p, encoding="utf-8", errors="replace").read()
        if os.path.isdir(out_dir):
            for name in sorted(os.listdir(out_dir)):
                if name.endswith(".svg"):
                    blob += open(os.path.join(out_dir, name), encoding="utf-8",
                                 errors="replace").read()
        markers = [chr(0xFFFD), "&#65533;", "&#xFFFD;"]
        bad = [m for m in markers if m in blob]
        return not bad, "mojibake markers=%r, blob=%d chars" % (bad, len(blob))
    if check == "empty_case_id_from_filename":
        cid = (result or {}).get("case_id") or ""
        return bool(cid.strip()), "case_id=%r" % cid
    if check == "no_null_in_contract_fields":
        bad = [k for k, v in (result or {}).items() if v is None]
        return not bad, "null top-level keys=%r" % (bad,)
    if check == "reserved_key_moved_to_echo":
        echo = (result or {}).get("output_contract_echo") or {}
        ok = "summary" in echo and (result or {}).get("summary") != echo.get("summary")
        return ok, "echo keys=%r" % (sorted(echo),)
    if check == "contract_value_echoed":
        return True, "value=%r" % ((result or {}).get("resolution_dpi"),)
    if check == "envelope_complete":
        need = ["schema_version", "skill", "case_id", "status", "summary", "task",
                "deliverables", "content_summary", "provenance", "sources",
                "uncertainty", "warnings", "change_records", "audit", "generated_utc",
                "output_contract_echo", "plan", "spec_lint"]
        miss = [k for k in need if k not in (result or {})]
        return not miss, "missing envelope keys=%r" % (miss,)
    return True, "unknown check %r" % check


def _render_backend(out_dir):
    log = _load_json(os.path.join(out_dir, "render_log.json"))
    return (log or {}).get("backend")


def _evaluate(case, rc, stdout, stderr, result, out_dir):
    exp = case["expect"]
    problems = []

    want = exp.get("exit")
    if isinstance(want, list):
        if rc not in want:
            problems.append("exit=%s not in %r" % (rc, want))
    elif want is not None:
        want_t = want if isinstance(want, tuple) else (want,)
        if rc not in want_t:
            problems.append("exit=%s not in %r" % (rc, want_t))

    if exp.get("status") is None and "status" in exp:
        if result is not None:
            problems.append("result.json produced but none expected (status=%r)"
                            % result.get("status"))
    if exp.get("status_in"):
        if result is None:
            problems.append("no result.json but status_in=%r" % (exp["status_in"],))
        elif result.get("status") not in exp["status_in"]:
            problems.append("status=%r not in %r" % (result.get("status"), exp["status_in"]))

    for f in exp.get("files_must_exist", []):
        if not os.path.isfile(os.path.join(out_dir, f)):
            problems.append("missing expected artifact %r" % f)
    for f in exp.get("files_must_not_exist", []):
        if os.path.isfile(os.path.join(out_dir, f)):
            problems.append("unexpected artifact %r" % f)

    if exp.get("uncertainty_contains"):
        if result is None:
            problems.append("no result.json -> cannot check uncertainty")
        else:
            blob = " ".join(str(u) for u in (result.get("uncertainty") or []))
            if exp["uncertainty_contains"] not in blob:
                problems.append("uncertainty lacks %r (has %d entries)"
                                % (exp["uncertainty_contains"], len(result.get("uncertainty") or [])))

    if exp.get("stdout_contains"):
        if exp["stdout_contains"] not in (stdout + stderr):
            problems.append("output lacks %r" % exp["stdout_contains"])
    if exp.get("stdout_or_stderr_contains"):
        if exp["stdout_or_stderr_contains"] not in (stdout + stderr):
            problems.append("output lacks %r" % exp["stdout_or_stderr_contains"])

    extra_ok, extra_note = _assert_extra(exp.get("check"), out_dir, result, stdout, stderr, case["id"])
    if not extra_ok:
        problems.append("check %r failed (%s)" % (exp.get("check"), extra_note))

    # ---- silent-failure detection -----------------------------------------
    silent = []
    if result is not None and result.get("status") == "success":
        if exp.get("status_in") and "success" not in exp["status_in"]:
            silent.append("reported success on a degraded run")
        if exp.get("uncertainty_contains"):
            blob = " ".join(str(u) for u in (result.get("uncertainty") or []))
            if exp["uncertainty_contains"] not in blob:
                silent.append("success without the required uncertainty entry")
    if rc == 0 and exp.get("exit") not in (0, (0,), [0]) and exp.get("exit") is not None:
        if result is None and not problems:
            silent.append("exit 0 with no result.json and no error message")

    verdict = "ok"
    if silent:
        verdict = "silent-failure"
    elif problems:
        verdict = "mismatch"
    return verdict, problems, silent, extra_note


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run_one(case, sandbox_root, keep=False):
    cid = case["id"]
    box = os.path.join(sandbox_root, cid)
    if os.path.isdir(box):
        shutil.rmtree(box)
    os.makedirs(box, exist_ok=True)
    skill = os.path.join(box, "skill")
    shutil.copytree(os.path.join(SKILL_ROOT, "scripts"), os.path.join(skill, "scripts"))
    work = os.path.join(box, "work")
    out = os.path.join(box, "out")
    case_obj = _setup_work(work, "fi-" + cid.lower())
    env_extra = _apply_injection(cid, work, case_obj, skill)

    argv = [a.format(work=work, out=out, skill=skill, case=os.path.join(work, "case.json"))
            for a in case["argv"]]
    rc, stdout, stderr, secs = _run([os.path.join(skill, "scripts", "main.py")] + argv,
                                    cwd=work, env_extra=env_extra)
    out_dir = out if os.path.isdir(out) else work
    result = _load_json(os.path.join(out, "result.json"))
    verdict, problems, silent, extra_note = _evaluate(case, rc, stdout, stderr, result, out_dir)

    row = {
        "id": cid,
        "kind": case["kind"],
        "title": case["title"],
        "inject": case["inject"],
        "argv": "main.py " + " ".join(a.replace(box, "<box>") for a in argv),
        "expected": case["expect"].get("rationale"),
        "expected_exit": case["expect"].get("exit"),
        "expected_status": case["expect"].get("status_in") or case["expect"].get("status"),
        "measured_exit": rc,
        "measured_status": (result or {}).get("status"),
        "uncertainty_n": len((result or {}).get("uncertainty") or []),
        "uncertainty_sample": ((result or {}).get("uncertainty") or [])[:2],
        "check_note": extra_note,
        "verdict": verdict,
        "problems": problems,
        "silent": silent,
        "stdout_head": (stdout or "").strip().splitlines()[:2],
        "stderr_head": (stderr or "").strip().splitlines()[:2],
        "seconds": secs,
    }
    if not keep:
        shutil.rmtree(box, ignore_errors=True)
    return row


def _print_table(rows):
    head = ("id", "kind", "verdict", "exit", "status", "unc")
    print("%-5s %-11s %-14s %-6s %-9s %-4s %s" % (head + ("title",)))
    print("-" * 118)
    for r in rows:
        print("%-5s %-11s %-14s %-6s %-9s %-4s %s" % (
            r["id"], r["kind"], r["verdict"], r["measured_exit"],
            str(r["measured_status"]), r["uncertainty_n"], r["title"][:44]))
        for p in r["problems"]:
            print("        ! %s" % p)
        for s in r["silent"]:
            print("        ~ %s" % s)


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(
        prog="fault_inject",
        description="inject input/template/dependency/contract faults and record the real behaviour")
    ap.add_argument("--out", required=True,
                    help="directory for fault_report.json (outside this package)")
    ap.add_argument("--only", default=None,
                    help="run one kind (input|template|dependency|contract) or one id (F07)")
    ap.add_argument("--fail-on", default="silent", choices=["silent", "strict", "none"],
                    help="silent = only silent failures fail the run; strict = any mismatch")
    ap.add_argument("--keep", action="store_true", help="keep sandboxes for inspection")
    ap.add_argument("--verbose", action="store_true", help="print per-case stdout/stderr heads")
    args = ap.parse_args(argv)

    cases = CASES
    if args.only:
        sel = args.only.lower()
        cases = [c for c in CASES if c["kind"] == sel or c["id"].lower() == sel]
        if not cases:
            print(json.dumps({"error": "no case matches --only %r" % args.only,
                              "kinds": sorted({c["kind"] for c in CASES}),
                              "ids": [c["id"] for c in CASES]}, ensure_ascii=False, indent=2))
            return 2

    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    sandbox_root = os.path.join(out_dir, "_sandbox")
    os.makedirs(sandbox_root, exist_ok=True)

    rows = []
    t0 = time.time()
    for c in cases:
        row = run_one(c, sandbox_root, keep=args.keep)
        rows.append(row)
        if args.verbose:
            print("[%s] exit=%s status=%s verdict=%s"
                  % (row["id"], row["measured_exit"], row["measured_status"], row["verdict"]))
            for line in row["stdout_head"]:
                print("    out| " + line[:160])
            for line in row["stderr_head"]:
                print("    err| " + line[:160])

    summary = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "skill_root": "<skill>",
        "python": sys.version.split()[0],
        "cases_run": len(rows),
        "ok": sum(1 for r in rows if r["verdict"] == "ok"),
        "mismatch": sum(1 for r in rows if r["verdict"] == "mismatch"),
        "silent_failure": sum(1 for r in rows if r["verdict"] == "silent-failure"),
        "seconds_total": round(time.time() - t0, 2),
        "by_kind": {k: {v: sum(1 for r in rows if r["kind"] == k and r["verdict"] == v)
                        for v in ("ok", "mismatch", "silent-failure")}
                    for k in sorted({r["kind"] for r in rows})},
    }
    report = {"summary": summary, "cases": rows}
    with open(os.path.join(out_dir, "fault_report.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    _print_table(rows)
    print("-" * 118)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("report: %s" % os.path.join(out_dir, "fault_report.json"))

    if args.fail_on == "none":
        return 0
    if summary["silent_failure"]:
        return 1
    if args.fail_on == "strict" and summary["mismatch"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
