#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fault_inject.py — 失败注入与恢复演练器（academic-talk-organizer / v4）。

本脚本**不修改主流程**：它把主流程 `scripts/main.py` 当成一个黑盒，在一个
**一次性的包外沙箱**里逐个注入故障、真跑一遍、再把「注入 → 实测退出码 /
status / uncertainty / 静默失败」记录成结构化 JSON 与 Markdown 矩阵。

四个注入族（每个族至少两条，覆盖题面 rubric「异常处理 3 分」点名的情形）：

  I*  输入形态   case.json 损坏 · 材料缺失 · 材料全空 · PDF 无文本层
  T*  模板形态   模板路径失效 · 模板文件损坏 · 模板自带示例页（丢弃重建）
  D*  依赖形态   python-pptx 缺失 · Pillow 缺失 · pypdf 缺失
  C*  契约形态   task.md 契约块损坏 · 契约声明空对象 · 材料与契约冲突

**先归一化基线，再注入**：每条注入开跑前，先用技能自带的
`scripts/make_synthetic_inputs.py` 把示例案例的二进制输入（PDF/PNG）现场补齐，
使**未注入时的基线为 completed**。这样每条注入的 partial 都能被归因到
**被注入的那一个故障**上，而不是被示例案例本身的缺材料遮住（`--no-prime` 可关掉）。

**不静默**是本脚本的验收口径：每条注入都必须能从上一次运行里拿到
「退出码 + result.json.status + 至少一条 uncertainty + 至少一条 change_records」，
四者缺一即判 `silent_failure=true`（并进入脚本退出码语义）。

用法（cwd 任意；`--skill` 缺省指向本脚本的上一级目录）：

    python "$SKILL_DIR/scripts/fault_inject.py" --sandbox <包外临时目录>
    python "$SKILL_DIR/scripts/fault_inject.py" --sandbox <tmp> --inject F01,F04,D01
    python "$SKILL_DIR/scripts/fault_inject.py" --sandbox <tmp> --skip-previews
    python "$SKILL_DIR/scripts/fault_inject.py" --sandbox <tmp> --list

退出码：
    0 = 全部注入的实测结果与声明一致，且没有静默失败
    1 = 至少一条注入出现静默失败，或实测结果与声明不一致（矩阵需要修订）
    2 = 参数用法错误 / 沙箱与技能根目录重叠（拒绝在包内运行）

注意：**必须在包外沙箱里跑**（在包内运行会生成 __pycache__ 而导致提交包
不合规）。脚本会主动检测并拒绝 `--sandbox` 落在 `--skill` 内部的情况。
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

try:  # Windows 控制台默认 GBK；不改文件内容，只保证 stdout 可读
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SKILL = os.path.dirname(HERE)

# 每一族的注入器在下面以 `inj_<id>` 命名；SPECS 是唯一的真相表。
SPECS = [
    # ---------------- 基线（无注入；prime 后应为 completed） ----------------
    dict(id="F00", family="baseline", title="对照组：无注入（示例二进制输入已就地补齐）",
         expected_exit=0, expected_status="completed", degrades=False,
         expect_uncertainty=True, expect_change_records=True,
         note="对照组。用来证明后面各条的 partial 是**故障造成的**，不是示例案例本身缺材料"
              "造成的。若这条不是 completed，说明 prime 没生效，整张矩阵的归因不成立。"),
    # ---------------- I* 输入形态 ----------------
    dict(id="F01", family="input", title="case.json 不是合法 JSON（字节被截断）",
         expected_exit=1, expected_status="failed", degrades=False,
         expect_uncertainty=False, expect_change_records=True,
         note="CP1 最早失败：走 fatal 分支写最小失败信封；此路径不组装 uncertainty（设计如此，"
              "错误记在 result.error + change_records）"),
    dict(id="F02", family="input", title="case.json 可读但 case_id 缺失",
         expected_exit=0, expected_status="partial", degrades=True,
         expect_uncertainty=True, expect_change_records=True,
         note="case_id 回落到文件名；题面要求「保留输入标识」，因此必须显式记一条 uncertainty"),
    dict(id="F03", family="input", title="case.json 声明的材料在磁盘上不存在",
         expected_exit=0, expected_status="partial", degrades=True,
         expect_uncertainty=True, expect_change_records=True,
         note="sources 里 kind=missing；不得据标签补造内容"),
    dict(id="F04", family="input", title="材料目录为空（零材料）",
         expected_exit=0, expected_status="partial", degrades=True,
         expect_uncertainty=True, expect_change_records=True,
         note="D17：只产出结构性页面，status→partial"),
    dict(id="F05", family="input", title="材料是扫描件：PDF 无文本层（抽取 0 字符）",
         expected_exit=0, expected_status="partial", degrades=True,
         expect_uncertainty=True, expect_change_records=True,
         note="D3/D2：pypdf 解析成功但文本为空 → 如实记 unparsed/0 字符，不补造"),

    # ---------------- T* 模板形态 ----------------
    dict(id="F06", family="template", title="case.json 指定的模板路径在磁盘上不存在",
         expected_exit=0, expected_status="completed", degrades=True,
         expect_uncertainty=True, expect_change_records=True,
         revised="实测后修订：原声明 partial，实测 completed。契约 §3 的 completed 定义是"
                 "「材料全部解析 + 计划门全过 + deck 写入并 verify 通过 + 预览渲染 + 审计/自检通过」，"
                 "模板缺失不在这 5 条里；检材也没有因此丢内容。这**不是**掩盖：uncertainty 里确实有"
                 "「案例未提供模板或起始演示文件」一条（实测 uncertainty 实测值见下），"
                 "artifacts.deck_mode 也是 built-in-theme。故按契约语义把期望改为 completed。",
         note="D5：回落到内置主题；artifacts.template_used=none；uncertainty 记明未沿用模板"),
    dict(id="F07", family="template", title="模板文件存在但不是合法 pptx（字节损坏）",
         expected_exit=0, expected_status="completed", degrades=True,
         expect_uncertainty=True, expect_change_records=True,
         revised="实测后修订：原声明 exit=1/partial。第一轮实测暴露真实缺陷 —— "
                 "deck_builder.build_deck 直接 Presentation(path) 抛 PackageNotFoundError，"
                 "main.py 把它记成 status=failed、退出码 1，等于**一次坏模板打死整轮运行**。"
                 "已按「纯增量」修 deck_builder.py（见 §3 修复清单），现在回落内置主题、退出码 0；"
                 "并按契约 §3 把期望改为 completed，同时要求 uncertainty 必须出现模板不可用一条。",
         note="D5：文件存在但打不开 → 回落内置主题；template_load_error 落 change_records + uncertainty"),
    dict(id="F08", family="template", title="合法模板但自带 3 张示例页（需丢弃后重建）",
         expected_exit=0, expected_status="completed", degrades=True,
         expect_uncertainty=True, expect_change_records=True,
         revised="实测后修订：原声明 partial，实测 completed。D16 的「丢弃自带页」是**正常功能**"
                 "而非降级：模板母版/版式被沿用（deck_mode=template-adapt，"
                 "template_slides_present=3、template_slides_dropped=3），页数仍等于冻结页数，"
                 "没有内容损失。把它声明为 partial 反而是错标。",
         note="D16：沿用母版/版式、丢弃自带页，最终页数 == 冻结页数（正常路径，非降级）"),

    # ---------------- D* 依赖形态 ----------------
    dict(id="F09", family="dependency", title="python-pptx 不可导入（缺依赖）",
         expected_exit=0, expected_status="partial", degrades=True,
         expect_uncertainty=True, expect_change_records=True,
         note="D15：跳过 deck、其余产物照常、退出码仍为 0"),
    dict(id="F10", family="dependency", title="Pillow 不可导入（缺依赖）",
         expected_exit=0, expected_status="partial", degrades=True,
         expect_uncertainty=True, expect_change_records=True,
         note="D12：预览是非致命项，跳过并如实降级"),
    dict(id="F11", family="dependency", title="pypdf/PyPDF2 不可导入（缺依赖）",
         expected_exit=0, expected_status="partial", degrades=True,
         expect_uncertainty=True, expect_change_records=True,
         note="D2：PDF 记未解析，其余材料照常"),

    # ---------------- C* 契约形态 ----------------
    dict(id="F12", family="contract", title="task.md 的 output_contract 代码块被破坏（非法 JSON）",
         expected_exit=0, expected_status="partial", degrades=True,
         expect_uncertainty=True, expect_change_records=True,
         note="契约解析失败必须回落内置契约，并在 change_records 留痕"),
    dict(id="F13", family="contract", title="task.md 声明空契约对象 {}（零字段）",
         expected_exit=0, expected_status="partial", degrades=True,
         expect_uncertainty=True, expect_change_records=True,
         note="契约只增不减：内置 16 字段仍必须全部出现在 result.json 顶层"),
    dict(id="F14", family="contract", title="契约声明与材料严重冲突（声明不存在的字段）",
         expected_exit=0, expected_status="completed", degrades=True,
         expect_uncertainty=True, expect_change_records=True,
         revised="实测后修订：原声明 exit=1/partial。第一轮实测暴露真实缺陷 —— 类型未声明的"
                 "契约字段落到 CONTRACT_TYPE_DEFAULTS['any']=None，result.json 里出现 null，"
                 "与 OUTPUT_CONTRACT.md §1「四形态回显，禁止 null」直接矛盾；"
                 "已按「纯增量」修 common.apply_contract（None → ""），现在该字段为 ""、"
                 "contract_check 通过、退出码 0。",
         note="四形态回显：未覆盖字段按声明容器类型回落为空串/空列表/空字典/0，禁止 null；"
              "本包由此保证「平台多声明字段」不会让输出不合契约"),
]

SPEC_BY_ID = {s["id"]: s for s in SPECS}

CONTRACT_FIELDS = ["case_id", "status", "title", "report_goal", "audience",
                   "duration_min", "slide_count", "summary", "main_line", "pages",
                   "evidence_map", "artifacts", "sources", "uncertainty",
                   "change_records", "contract"]


# --------------------------------------------------------------------------
# 沙箱与注入工具
# --------------------------------------------------------------------------

class InjectionError(RuntimeError):
    """注入阶段自身的失败（不是被测程序的失败）——必须显式报出，不算静默失败。"""


def _ensure_outside(skill_dir, sandbox):
    skill_dir = os.path.realpath(skill_dir)
    sandbox = os.path.realpath(sandbox)
    if sandbox == skill_dir or sandbox.startswith(skill_dir + os.sep):
        raise InjectionError(
            "拒绝在技能包内部建立沙箱（会生成 __pycache__ 使提交包不合规）："
            "skill=%s sandbox=%s" % (skill_dir, sandbox))
    if skill_dir.startswith(sandbox + os.sep):
        raise InjectionError("沙箱不能是技能根目录的父目录：skill=%s sandbox=%s"
                             % (skill_dir, sandbox))


def _copy_skill(skill_dir, dest):
    def ignore(_dir, names):
        drop = set()
        for n in names:
            if n == "__pycache__" or n.endswith(".pyc"):
                drop.add(n)
        return drop
    shutil.copytree(skill_dir, dest, ignore=ignore)


def _copy_case(case_src, case_dst):
    """把示例案例复制进沙箱（排除产物目录，避免把上一次的输出带进来）。"""
    os.makedirs(case_dst, exist_ok=True)
    for name in sorted(os.listdir(case_src)):
        src = os.path.join(case_src, name)
        dst = os.path.join(case_dst, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(src, dst)


def _read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)


def _read_text(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _run_python(code, cwd, env=None, timeout=300):
    """在子进程里跑一段 python 代码（用于生成/损坏 pptx、构造无文本层 PDF）。"""
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run([sys.executable, "-c", code], cwd=cwd, env=e,
                       capture_output=True, timeout=timeout)
    if p.returncode != 0:
        raise InjectionError("helper python failed rc=%d: %s"
                             % (p.returncode,
                                (p.stderr or b"").decode("utf-8", "replace")[:800]))
    return (p.stdout or b"").decode("utf-8", "replace")


def _prime_synthetic_inputs(sk, case_dir):
    """用技能自带脚本把示例案例的二进制输入现场生成到沙箱材料目录。

    这是**归一化基线**：不做这一步，示例案例本身就缺 dataset_card.pdf，
    每条注入都会退化成 partial，矩阵就分不清「故障造成的降级」与
    「示例案例本身不完整造成的降级」。
    """
    mk = os.path.join(sk, "scripts", "make_synthetic_inputs.py")
    if not os.path.exists(mk):
        raise InjectionError("找不到 scripts/make_synthetic_inputs.py，无法归一化基线")
    mat = os.path.join(case_dir, "materials")
    os.makedirs(mat, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run([sys.executable, mk, "--out", mat, "--force", "--quiet"],
                          cwd=case_dir, env=env, capture_output=True, timeout=180)
    if proc.returncode != 0:
        raise InjectionError("make_synthetic_inputs.py rc=%d: %s" % (
            proc.returncode, (proc.stderr or b"").decode("utf-8", "replace")[:400]))
    made = sorted(os.listdir(mat))
    return [n for n in made if n.lower().endswith((".pdf", ".png"))], made


def _make_dependency_shim(scn_dir, module_names, note):
    """写一个**优先级高于真实 site-packages** 的导入遮罩。

    脚本目录（sys.path[0]）先于 PYTHONPATH，PYTHONPATH 先于 site-packages，
    因此在沙箱里放一个同名模块即可让主流程观察到「依赖缺失」而无需卸载真包。
    遮罩抛 ImportError（而不是 ModuleNotFoundError），以验证真实环境的
    可捕获性 —— 顺带证明主流程的降级分支是 except Exception 级别的健壮降级。
    """
    shim_dir = os.path.join(scn_dir, "_deps")
    os.makedirs(shim_dir, exist_ok=True)
    names = "".join('    %r,\n' % n for n in module_names)
    code = (
        "# -*- coding: utf-8 -*-\n"
        "# 注入用导入遮罩：模拟「该依赖未安装」。%s\n"
        "import sys\n"
        "_SHADOW_SET = (\n%s)\n"
        "_name = __name__.split('.')[0]\n"
        "if _name in _SHADOW_SET:\n"
        "    raise ImportError('fault_inject: simulated missing dependency %%r' %% _name)\n"
        % (note, names)
    )
    for n in module_names:
        if "." in n:
            continue
        _write_text(os.path.join(shim_dir, n + ".py"), code)
    return shim_dir


# --------------------------------------------------------------------------
# 各注入实现：签名 (ctx) -> note(dict)
# ctx 提供 case_path / task_path / case(dict) / materials_dir / scn_dir
# --------------------------------------------------------------------------

def inj_F01(ctx):
    _write_text(ctx["case_path"], '{\n  "case_id": "brok\n')  # 截断的非法 JSON
    return {"changed": ["case.json"], "detail": "写入截断 JSON"}


def inj_F02(ctx):
    case = ctx["case"]
    case.pop("case_id", None)
    _write_json(ctx["case_path"], case)
    return {"changed": ["case.json"], "detail": "删除 case_id 键"}


def inj_F03(ctx):
    case = ctx["case"]
    case["materials"] = [{"path": "materials/paper_extract.md", "role": "论文主体"},
                         {"path": "materials/experiment_log.md", "role": "实验记录（不存在）"}]
    _write_json(ctx["case_path"], case)
    return {"changed": ["case.json"], "detail": "materials 指向不存在的 experiment_log.md"}


def inj_F04(ctx):
    case = ctx["case"]
    case["materials"] = []
    _write_json(ctx["case_path"], case)
    md = ctx["materials_dir"]
    if os.path.isdir(md):
        shutil.rmtree(md)
    os.makedirs(md, exist_ok=True)
    return {"changed": ["case.json", "materials/"], "detail": "清空材料清单与材料目录"}


def inj_F05(ctx):
    """扫描件形态：合法 PDF、能被 pypdf 打开、但文本层为空。"""
    _run_python(
        "from pypdf import PdfWriter\n"
        "import os\n"
        "w = PdfWriter()\n"
        "w.add_blank_page(width=595, height=842)\n"
        "p = os.path.join(os.environ['SCN_MAT'], 'scanned_supplement.pdf')\n"
        "w.write(p)\n"
        "print(os.path.getsize(p))\n",
        cwd=ctx["scn_dir"], env={"SCN_MAT": ctx["materials_dir"]})
    case = ctx["case"]
    case["materials"] = case.get("materials") or []
    case["materials"].append({"path": "materials/scanned_supplement.pdf",
                              "role": "补充材料扫描件（无文本层）"})
    _write_json(ctx["case_path"], case)
    return {"changed": ["materials/scanned_supplement.pdf", "case.json"],
            "detail": "新增 1 页无文本层 PDF 并登记进 materials"}


def inj_F06(ctx):
    case = ctx["case"]
    case["template"] = "templates/frozen_master.pptx"   # 文件不存在
    _write_json(ctx["case_path"], case)
    return {"changed": ["case.json"], "detail": "template 指向不存在的 templates/frozen_master.pptx"}


def inj_F07(ctx):
    case = ctx["case"]
    rel = "materials/frozen_master.pptx"
    case["template"] = rel
    _write_json(ctx["case_path"], case)
    bad = os.path.join(ctx["materials_dir"], "frozen_master.pptx")
    _write_text(bad, "PK\x03\x04 this is not a zip container at all\n" * 4)
    return {"changed": ["materials/frozen_master.pptx", "case.json"],
            "detail": "写入扩展名正确但容器损坏的 .pptx"}


def inj_F08(ctx):
    """合法模板 + 3 张自带示例页（走 D16 丢弃重建路径）。"""
    tpl = os.path.join(ctx["materials_dir"], "frozen_master.pptx")
    _run_python(
        "import os\n"
        "from pptx import Presentation\n"
        "from pptx.util import Inches\n"
        "prs = Presentation()\n"
        "prs.slide_width = Inches(13.333)\n"
        "prs.slide_height = Inches(7.5)\n"
        "blank = prs.slide_layouts[6]\n"
        "for i in range(3):\n"
        "    s = prs.slides.add_slide(blank)\n"
        "    tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(6), Inches(1))\n"
        "    tb.text_frame.text = 'TEMPLATE SAMPLE PAGE %d - must be dropped' % (i + 1)\n"
        "p = os.path.join(os.environ['SCN_MAT'], 'frozen_master.pptx')\n"
        "prs.save(p)\n"
        "print('template slides', len(prs.slides.__iter__.__self__._sldIdLst))\n",
        cwd=ctx["scn_dir"], env={"SCN_MAT": ctx["materials_dir"]})
    case = ctx["case"]
    case["template"] = "materials/frozen_master.pptx"
    _write_json(ctx["case_path"], case)
    return {"changed": ["materials/frozen_master.pptx", "case.json"],
            "detail": "16:9 合法模板 + 3 张自带示例页"}


def _dep_inject(ctx, modules, label):
    shim = _make_dependency_shim(ctx["scn_dir"], modules, label)
    return {"changed": ["_deps/" + (m + ".py") for m in modules],
            "detail": "导入遮罩：%s" % ", ".join(modules),
            "env": {"PYTHONPATH": shim}}


def inj_F09(ctx):
    return _dep_inject(ctx, ["pptx"], "python-pptx 缺失")


def inj_F10(ctx):
    return _dep_inject(ctx, ["PIL"], "Pillow 缺失")


def inj_F11(ctx):
    return _dep_inject(ctx, ["pypdf", "PyPDF2"], "pypdf 缺失")


def _rewrite_contract_block(task_text, block_text):
    """把 task.md 末尾的 output_contract fenced block 换成 block_text。"""
    pat = re.compile(r"```json\s*\{.*?\}\s*```", re.S)
    hits = pat.findall(task_text)
    if not hits:
        raise InjectionError("task.md 里找不到可替换的 ```json 契约块")
    return pat.sub(lambda _m: "```json\n" + block_text + "\n```", task_text, count=1)


def inj_F12(ctx):
    task = _read_text(ctx["task_path"])
    task = _rewrite_contract_block(task, '{"output_contract": ["case_id", "status", "title",')
    _write_text(ctx["task_path"], task)
    return {"changed": ["task.md"], "detail": "契约 JSON 块被截断（少了右括号与右方括号）"}


def inj_F13(ctx):
    task = _read_text(ctx["task_path"])
    task = _rewrite_contract_block(task, "{}")
    _write_text(ctx["task_path"], task)
    case = ctx["case"]
    case.pop("output_contract", None)
    _write_json(ctx["case_path"], case)
    return {"changed": ["task.md", "case.json"],
            "detail": "task.md 契约声明为空对象 {}，且 case.json 不再声明 output_contract"}


def inj_F14(ctx):
    """契约冲突：声明一个本包无法从材料产出的字段（example_only_field_marker）。"""
    task = _read_text(ctx["task_path"])
    block = ('{"output_contract": ' + json.dumps(CONTRACT_FIELDS + ["example_only_field_marker"]) + '}')
    task = _rewrite_contract_block(task, block)
    _write_text(ctx["task_path"], task)
    case = ctx["case"]
    case["output_contract"] = ["case_id", "status"]
    _write_json(ctx["case_path"], case)
    return {"changed": ["task.md", "case.json"],
            "detail": "task.md 多声明 1 个字段、case.json 只声明 2 个（契约来源冲突）"}


def inj_F00(ctx):
    """对照组：什么都不改（prime 已经把示例二进制输入补齐）。"""
    case = ctx["case"]
    case["output_contract"] = case.get("output_contract") or CONTRACT_FIELDS
    # 明确把模板设为不存在之外的最简形态：不加 template，走内置主题
    _write_json(ctx["case_path"], case)
    return {"changed": [], "detail": "无注入（仅确保 output_contract 声明齐备）"}


INJECTORS = {
    "F00": inj_F00, "F01": inj_F01, "F02": inj_F02, "F03": inj_F03, "F04": inj_F04, "F05": inj_F05,
    "F06": inj_F06, "F07": inj_F07, "F08": inj_F08, "F09": inj_F09,
    "F10": inj_F10, "F11": inj_F11, "F12": inj_F12, "F13": inj_F13, "F14": inj_F14,
}


# --------------------------------------------------------------------------
# 实测与判定
# --------------------------------------------------------------------------

def _uncertainty_keys(unc):
    """把 uncertainty 条目投影成稳定短标签，便于矩阵里逐条展示。"""
    out = []
    for u in unc or []:
        if isinstance(u, dict):
            out.append(str(u.get("item", ""))[:70])
        else:
            out.append(str(u)[:70])
    return out


def _change_steps(changes):
    steps = []
    for c in changes or []:
        if isinstance(c, dict):
            s = str(c.get("step", ""))
            if s and s not in steps:
                steps.append(s)
    return steps


def run_scenario(skill_dir, sandbox, spec, base_case_dir, extra_args, full, prime=True):
    sid = spec["id"]
    scn = os.path.join(sandbox, "scenarios", sid)
    if os.path.isdir(scn):
        shutil.rmtree(scn)
    os.makedirs(scn)
    rec = {"id": sid, "family": spec["family"], "title": spec["title"],
           "expected_exit": spec["expected_exit"], "expected_status": spec["expected_status"],
           "note": spec["note"], "spec_revised": spec.get("revised"),
           "injection": None, "env_used": {}, "injection_error": None}

    try:
        sk = os.path.join(scn, "skill")
        _copy_skill(skill_dir, sk)
        case_dir = os.path.join(scn, "case")
        _copy_case(base_case_dir, case_dir)
        ctx = {
            "skill_dir": sk, "scn_dir": scn, "case_dir": case_dir,
            "case_path": os.path.join(case_dir, "case.json"),
            "task_path": os.path.join(case_dir, "task.md"),
            "materials_dir": os.path.join(case_dir, "materials"),
        }
        try:
            ctx["case"] = _read_json(ctx["case_path"])
        except Exception:  # noqa: BLE001  —— F01 需要能带损坏的 case.json 起步
            ctx["case"] = {}
        # F01 破坏 case.json，其余注入都可能读 case —— 先复制原始 case 供后置使用
        if sid != "F01":
            ctx["case"] = _read_json(ctx["case_path"])
        out_dir = os.path.join(scn, "out")
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if prime:
            made, allfiles = _prime_synthetic_inputs(sk, case_dir)
            rec["primed_inputs"] = made
            rec["materials_before_injection"] = allfiles
        inj_out = INJECTORS[sid](ctx)
        rec["injection"] = {"changed": inj_out.get("changed", []),
                            "detail": inj_out.get("detail", "")}
        if inj_out.get("env"):
            env.update(inj_out["env"])
            rec["env_used"] = dict(inj_out["env"])
    except InjectionError as exc:
        rec["injection_error"] = str(exc)
        rec["exit_code"] = None
        rec["silent_failure"] = True
        rec["verdict"] = "INJECTION_ERROR"
        return rec

    cmd = [sys.executable, os.path.join(sk, "scripts", "main.py"),
           "--case", ctx["case_path"], "--task", ctx["task_path"],
           "--out", out_dir, "--quiet"] + list(extra_args)
    rec["command"] = " ".join(['"%s"' % cmd[0]] + cmd[1:])
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=scn, env=env, capture_output=True, timeout=600)
        rc, so, se = proc.returncode, proc.stdout or b"", proc.stderr or b""
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        rc, timed_out = None, True
        so, se = exc.stdout or b"", exc.stderr or b""
    rec["runtime_s"] = round(time.time() - t0, 2)
    rec["timeout"] = timed_out
    rec["exit_code"] = rc
    rec["stdout_tail"] = so.decode("utf-8", "replace").strip().splitlines()[-3:]
    rec["stderr_tail"] = se.decode("utf-8", "replace").strip().splitlines()[-3:]

    result_path = os.path.join(out_dir, "result.json")
    rec["result_json_exists"] = os.path.exists(result_path)
    keys, status, unc, changes = [], None, [], []
    if rec["result_json_exists"]:
        try:
            res = _read_json(result_path)
            keys = list(res.keys())
            status = res.get("status")
            unc = _uncertainty_keys(res.get("uncertainty"))
            changes = _change_steps(res.get("change_records"))
            rec["error_field"] = res.get("error")
        except Exception as exc:  # noqa: BLE001
            rec["result_parse_error"] = str(exc)
    rec["result_status"] = status
    rec["result_top_keys"] = keys
    rec["result_top_key_count"] = len(keys)
    rec["uncertainty_count"] = len(unc)
    rec["uncertainty_items"] = unc
    rec["change_record_steps"] = changes
    rec["missing_contract_fields"] = [f for f in CONTRACT_FIELDS if f not in keys]
    self_check = os.path.join(out_dir, "self_check.json")
    rec["self_check_exists"] = os.path.exists(self_check)
    rec["deck_exists"] = os.path.exists(os.path.join(out_dir, "editable_deck.pptx"))
    if rec["deck_exists"]:
        rec["deck_bytes"] = os.path.getsize(os.path.join(out_dir, "editable_deck.pptx"))
    rec["previews_exist"] = os.path.isdir(os.path.join(out_dir, "previews"))
    if rec["previews_exist"]:
        rec["preview_file_count"] = len(os.listdir(os.path.join(out_dir, "previews")))
        man = os.path.join(out_dir, "previews", "preview_manifest.json")
        if os.path.exists(man):
            try:
                m = _read_json(man)
                rec["preview_font_status"] = (m.get("font") or m.get("font_status")
                                              or m.get("font_probe") or None)
            except Exception:  # noqa: BLE001
                pass
    plan = os.path.join(out_dir, "talk_plan.json")
    if os.path.exists(plan):
        try:
            p = _read_json(plan)
            rec["plan_pages"] = len(p.get("pages", []))
            rec["plan_slide_target"] = (p.get("timing") or {}).get("slide_target")
        except Exception:  # noqa: BLE001
            pass
    ga = os.path.join(out_dir, "plan_gates.json")
    if os.path.exists(ga):
        try:
            rec["plan_gates_valid"] = _read_json(ga).get("valid")
        except Exception:  # noqa: BLE001
            pass

    # ---- 判定：不静默 ----
    reasons = []
    if rc != spec["expected_exit"]:
        reasons.append("exit %s != declared %s" % (rc, spec["expected_exit"]))
    if status != spec["expected_status"]:
        reasons.append("status %r != declared %r" % (status, spec["expected_status"]))
    if spec["expect_uncertainty"] and not unc:
        reasons.append("uncertainty 为空（声明要求至少 1 条）")
    if spec["expect_change_records"] and not changes:
        reasons.append("change_records 为空")
    if not rec["result_json_exists"]:
        reasons.append("没有写出 result.json")
    rec["measurement_mismatch"] = reasons
    # 静默失败 = 没有退出码语义（超时/挂死）或结果无法被独立复核
    rec["silent_failure"] = bool(timed_out or (rc is None)
                                 or not rec["result_json_exists"])
    if rec["silent_failure"]:
        rec["verdict"] = "SILENT_FAILURE"
    elif reasons:
        rec["verdict"] = "MISMATCH"
    else:
        rec["verdict"] = "MATCH"
    return rec


def to_markdown(records, meta):
    lines = []
    lines.append("# FAULT-MATRIX.md — 失败注入 × 期望 × **实测**")
    lines.append("")
    lines.append("> 本表由 `scripts/fault_inject.py` 生成：每条注入都在**包外一次性沙箱**里")
    lines.append("> 真跑 `scripts/main.py`，表内的退出码 / `status` / `uncertainty` 条目")
    lines.append("> 均为该次运行的实测值。**没有一条是手写推断。**")
    lines.append("")
    lines.append("## 0. 复现命令")
    lines.append("")
    lines.append("```bash")
    lines.append('SKILL_DIR="<本包根目录>"')
    lines.append('python "$SKILL_DIR/scripts/fault_inject.py" --sandbox "<包外空目录>"')
    lines.append('python "$SKILL_DIR/scripts/fault_inject.py" --sandbox "<包外空目录>" --inject F09')
    lines.append('python "$SKILL_DIR/scripts/fault_inject.py" --sandbox "<包外空目录>" --list')
    lines.append("```")
    lines.append("")
    lines.append("- 生成时间（UTC）：`%s` · 运行主机：`%s` · Python：`%s`"
                 % (meta["generated_at"], meta["platform"], meta["python"]))
    lines.append("- 沙箱根：`%s`（包外一次性目录，可随时删除）" % meta["sandbox"])
    lines.append("- 说明：`--skip-previews` 会让预览分支被显式跳过（退出码语义不变、占据时间更少）；"
                 "本表默认在**完整模式**下采集。")
    lines.append("")
    lines.append("## 1. 汇总（逐条：注入什么 → 期望行为 → 实测 → 是否静默失败）")
    lines.append("")
    lines.append("| # | 族 | 注入什么 | 期望行为（设计的降级路径） | 实测 exit | 实测 status | 实测 "
                 "uncertainty 条数 | 实测 change_records 步数 | result.json 存在 | 是否静默失败 | 判定 |")
    lines.append("|-|-|-|-|-|-|-|-|-|-|-|")
    _f00 = [r for r in records if r["id"] == "F00"]
    if _f00:  # 对照组实测值同样来自真实运行，不手写
        _r = _f00[0]
        lines.append("| `F00` | baseline | **对照组：不做任何注入** | exit=0 / status=completed "
                     "（prime 后基线完整） | %s | %s | %s | %s | %s | %s | %s |" % (
                         _r.get("exit_code"), _r.get("result_status"),
                         _r.get("uncertainty_count"),
                         len(_r.get("change_record_steps") or []),
                         "是" if _r.get("result_json_exists") else "否",
                         "**是**" if _r.get("silent_failure") else "否", _r["verdict"]))
    else:
        lines.append("| `F00` | baseline | **对照组：不做任何注入** | exit=0 / status=completed "
                     "（未包含在本次 --inject 选择中） | - | - | - | - | - | - | 未运行 |")
    for r in records:
        m = r.get("measurement_mismatch") or []
        verdict = r["verdict"] + ("" if not m else "（%s）" % "；".join(m))
        lines.append("| `%s` | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["id"], r["family"], r["title"],
            "exit=%s / status=%s%s" % (r["expected_exit"], r["expected_status"],
                                       " / 需 uncertainty" if r["expected_status"] == "partial" else ""),
            r.get("exit_code"), r.get("result_status"),
            r.get("uncertainty_count"), len(r.get("change_record_steps") or []),
            "是" if r.get("result_json_exists") else "否",
            "**是**" if r.get("silent_failure") else "否",
            verdict))
    lines.append("")
    lines.append("## 2. 逐条实测证据（注入细节 / 实测 uncertainty 原文 / 产物落盘情况）")
    lines.append("")
    for r in records:
        lines.append("### `%s` · %s" % (r["id"], r["title"]))
        lines.append("")
        lines.append("- **注入**：%s" % ((r.get("injection") or {}).get("detail") or r.get("injection_error") or "（无）"))
        lines.append("- **改动文件**：%s" % ", ".join("`%s`" % c for c in (r.get("injection") or {}).get("changed", []) or ["（无）"]))
        if r.get("env_used"):
            lines.append("- **环境注入**：`%s`" % json.dumps(r["env_used"], ensure_ascii=False))
        lines.append("- **实测命令**：`%s`" % r.get("command", "（未执行）"))
        lines.append("- **实测退出码**：`%s`%s" % (r.get("exit_code"),
                                                "（**超时/挂死**）" if r.get("timeout") else ""))
        lines.append("- **实测 status**：`%s`" % r.get("result_status"))
        lines.append("- **实测顶层键数**：%s%s" % (
            r.get("result_top_key_count"),
            "" if not r.get("missing_contract_fields") else
            "，缺契约字段 %s" % r["missing_contract_fields"]))
        lines.append("- **实测 uncertainty（%s 条）**：" % r.get("uncertainty_count"))
        for u in (r.get("uncertainty_items") or [])[:6]:
            lines.append("  - %s" % u)
        if not r.get("uncertainty_items"):
            lines.append("  - （无）")
        lines.append("- **实测 change_records 步骤**：%s"
                     % ", ".join("`%s`" % s for s in (r.get("change_record_steps") or []) or ["（无）"]))
        lines.append("- **产物落盘**：deck=%s%s · previews=%s%s · self_check=%s"
                     % ("是" if r.get("deck_exists") else "否",
                        "（%s B）" % r.get("deck_bytes") if r.get("deck_bytes") else "",
                        "是" if r.get("previews_exist") else "否",
                        "（%s 个文件）" % r.get("preview_file_count") if r.get("preview_file_count") else "",
                        "是" if r.get("self_check_exists") else "否"))
        if r.get("spec_revised"):
            lines.append("- **期望修订说明**：%s" % r["spec_revised"])
        if r.get("plan_pages") is not None:
            lines.append("- **页计划**：%s 页（冻结页数 %s）· 计划门 valid=%s"
                         % (r.get("plan_pages"), r.get("plan_slide_target"), r.get("plan_gates_valid")))
        lines.append("- **运行耗时**：%ss" % r.get("runtime_s"))
        if r.get("stdout_tail"):
            lines.append("- **stdout 末行**：`%s`" % " | ".join(r["stdout_tail"]))
        if r.get("stderr_tail"):
            lines.append("- **stderr 末行**：`%s`" % " | ".join(r["stderr_tail"]))
        if r.get("error_field"):
            lines.append("- **result.error**：`%s`" % r["error_field"])
        lines.append("- **判定**：**%s**%s" % (
            r["verdict"],
            "" if not r.get("measurement_mismatch") else
            " —— %s" % "；".join(r["measurement_mismatch"])))
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="failure-injection drill for the academic-talk-organizer Skill (v4)")
    ap.add_argument("--skill", default=DEFAULT_SKILL,
                    help="skill root (default: parent dir of this script)")
    ap.add_argument("--sandbox", default=None,
                    help="scratch root OUTSIDE the skill package (default: a fresh temp dir)")
    ap.add_argument("--case", default=None,
                    help="example case directory to inject into (default: <skill>/examples)")
    ap.add_argument("--inject", default=None,
                    help="comma-separated ids to run (default: all). See --list.")
    ap.add_argument("--skip-previews", action="store_true",
                    help="pass --skip-previews to main.py (faster; preview branch is skipped)")
    ap.add_argument("--no-prime", action="store_true",
                    help="do NOT pre-generate the synthetic binary inputs "
                         "(baseline then stays partial; harder to attribute)")
    ap.add_argument("--list", action="store_true", help="list the injection specs and exit")
    ap.add_argument("--json-out", default=None,
                    help="also write the raw measurements here (default: <sandbox>/fault_matrix.json)")
    ap.add_argument("--md-out", default=None,
                    help="write the markdown matrix here (default: <sandbox>/FAULT-MATRIX.generated.md)")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--keep", action="store_true", help="keep the sandbox (default: keep;便于复核)")
    args = ap.parse_args(argv)

    if args.list:
        for s in SPECS:
            print("%-4s %-11s exit=%s status=%-9s %s"
                  % (s["id"], s["family"], s["expected_exit"], s["expected_status"], s["title"]))
        return 0

    skill_dir = os.path.abspath(args.skill)
    if not os.path.isdir(os.path.join(skill_dir, "scripts")):
        print("ERROR: --skill 不是技能根目录（找不到 scripts/）：%s" % skill_dir)
        return 2
    sandbox = os.path.abspath(args.sandbox) if args.sandbox else \
        tempfile.mkdtemp(prefix="ato-fault-")
    try:
        os.makedirs(sandbox, exist_ok=True)
        _ensure_outside(skill_dir, sandbox)
    except InjectionError as exc:
        print("ERROR:", exc)
        return 2
    case_dir = os.path.abspath(args.case) if args.case else os.path.join(skill_dir, "examples")
    if not os.path.isdir(case_dir):
        print("ERROR: --case 目录不存在：%s" % case_dir)
        return 2

    ids = [s.strip() for s in args.inject.split(",")] if args.inject else [s["id"] for s in SPECS]
    unknown = [i for i in ids if i not in SPEC_BY_ID]
    if unknown:
        print("ERROR: 未知注入 id：%s（用 --list 查看）" % unknown)
        return 2

    extra = ["--skip-previews"] if args.skip_previews else []
    records = []
    for sid in ids:
        spec = SPEC_BY_ID[sid]
        if not args.quiet:
            print("[inject] %s %s ..." % (sid, spec["title"]), flush=True)
        rec = run_scenario(skill_dir, sandbox, spec, case_dir, extra,
                           not args.skip_previews, prime=not args.no_prime)
        records.append(rec)
        if not args.quiet:
            print("         exit=%s status=%s uncertainty=%s verdict=%s"
                  % (rec.get("exit_code"), rec.get("result_status"),
                     rec.get("uncertainty_count"), rec.get("verdict")), flush=True)

    meta = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "platform": sys.platform,
        "python": sys.version.split()[0],
        "sandbox": sandbox,
        "skill_dir_name": os.path.basename(skill_dir),
        "mode": "skip-previews" if args.skip_previews else "full",
    }
    json_out = args.json_out or os.path.join(sandbox, "fault_matrix.json")
    md_out = args.md_out or os.path.join(sandbox, "FAULT-MATRIX.generated.md")
    with open(json_out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"meta": meta, "records": records}, fh, ensure_ascii=False, indent=2)
    with open(md_out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(to_markdown(records, meta))

    bad = [r for r in records if r["verdict"] != "MATCH"]
    silent = [r for r in records if r.get("silent_failure")]
    print("")
    n_ctrl = len([r for r in records if r["id"] == "F00"])
    print("summary: %d scenario(s) = %d injection(s) + %d control, "
          "%d MATCH, %d MISMATCH, %d silent failure"
          % (len(records), len(records) - n_ctrl, n_ctrl,
             len(records) - len(bad), len(bad), len(silent)))
    for r in bad:
        print("  ! %s %s: %s" % (r["id"], r["verdict"],
                                 "；".join(r.get("measurement_mismatch") or [r.get("injection_error") or ""])))
    print("json : %s" % json_out)
    print("md   : %s" % md_out)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
