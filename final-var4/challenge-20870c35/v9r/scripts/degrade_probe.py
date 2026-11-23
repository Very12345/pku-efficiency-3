#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
degrade_probe.py — 缺依赖降级链实测器（v9 轴）。

用**受控导入拦截**（sys.meta_path 上的 import blocker，按模块名前缀拒绝导入）
模拟评测机上缺某个第三方库，然后逐个配置跑完整主流程（`scripts/main.py` 真子进程），
记录**实测**降级形态：

    退出码 / result.json 的 status / 还剩哪些产物文件 /
    artifacts.editable_deck 是否为 null / artifacts.previews 剩什么 /
    是否写了 result.json / uncertainty 里关于该依赖的条目 /
    change_records 里关于该依赖的条目 / 模块是否真的被拦住（拦截是否生效）

产出 `degrade_matrix_report.json`（机器可读）与「最小可用环境」清单
（`minimal_environments[]` / `environment_ladder[]`：逐级放行依赖，实测每级还能不能跑）。

另外单独探测 **LibreOffice CLI 与 Office 真实栅格化**：本包**不假设**它存在，
因此这一项在两条路径上实测 —— 单独缺 soffice（应完全无影响）、
soffice 与 PIL 同时缺（预览彻底不可用）。

退出码：`0` = 全部配置都跑完且都能判读（含"如实降级"的配置）；
`1` = 有配置连 result.json 都没写出来（无法判读）；`2` = 参数用法错误。

设计约束：只用标准库；自定位（路径由 `__file__` 推出，cwd 任意）；
被调用的永远是**沙箱内的技能副本**（包内原目录只读，绝不写 __pycache__）；
拦截脚本只作用于被启动的那个子进程，不改本机任何已安装包。

用法（`$SKILL_DIR` = 含 SKILL.md 的包根；cwd 任意）：

    python "$SKILL_DIR/scripts/degrade_probe.py" \
        --sandbox /tmp/dg --report /tmp/dg/degrade_matrix_report.json
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPTS_DIR)

# ---------------------------------------------------------------------------
# 矩阵：每个配置 = 一组被拦的导入 + 期望判读
# ---------------------------------------------------------------------------
#   axis:  D 单依赖缺失 / C 组合缺失 / O 真实栅格化 / M 逐级最小环境

PROBES = [
    {
        "id": "D-00", "axis": "D 单依赖缺失", "block": [],
        "expect": {"exit": 0, "status": "partial", "writes_result": True,
                   "deck_present": True, "previews_present": True},
        "note": "对照臂：什么都不拦（本机已装 pptx/PIL/pypdf）。用来给所有降级格子做基线。",
    },
    {
        "id": "D-01", "axis": "D 单依赖缺失", "block": ["pptx"],
        "expect": {"exit": 0, "status": "partial", "writes_result": True,
                   "deck_present": False},
        "note": "缺 python-pptx：可编辑 .pptx 彻底不可用；其余产物应照常。",
    },
    {
        "id": "D-02", "axis": "D 单依赖缺失", "block": ["PIL"],
        "expect": {"exit": 0, "status": "partial", "writes_result": True,
                   "deck_present": False, "previews_present": False},
        "note": "缺 Pillow：PNG 预览一条都写不出来。实测还发现 deck 也**产不出来** —— "
                "python-pptx 的图片路径（pptx.util.Inches/dml 图片处理）会 import PIL，"
                "缺 Pillow 时 deck_builder 的顶层 try/except 直接判定 python-pptx 不可用。",
    },
    {
        "id": "D-03", "axis": "D 单依赖缺失", "block": ["pypdf"],
        "expect": {"exit": 0, "status": "partial", "writes_result": True},
        "note": "缺 pypdf：PDF 材料按未解析如实记录（本案例的 PDF 本就缺文件，"
                "因此这条主要验证不因缺 pypdf 而崩）。",
    },
    {
        "id": "D-04", "axis": "D 单依赖缺失", "block": ["matplotlib"],
        "expect": {"exit": 0, "status": "partial", "writes_result": True,
                   "deck_present": True, "previews_present": True, "no_op": True},
        "note": "拦截 matplotlib：包内**任何脚本都不导入它**，因此应为纯 no-op —— "
                "用 sys.modules 证明它从未被加载，避免假装测过。",
    },
    {
        "id": "D-05", "axis": "D 单依赖缺失", "block": ["numpy"],
        "expect": {"exit": 0, "status": "partial", "writes_result": True,
                   "deck_present": True, "previews_present": True, "no_op": True},
        "note": "拦截 numpy：同上，纯 no-op（Pillow 的图像路径不依赖 numpy）。",
    },
    {
        "id": "D-06", "axis": "D 单依赖缺失", "block": ["yaml", "ruamel"],
        "expect": {"exit": 0, "status": "partial", "writes_result": True,
                   "deck_present": True, "previews_present": True, "no_op": True},
        "note": "拦截 yaml/ruamel：包内没有任何 YAML 读取代码（frontmatter 由平台解析），"
                "纯 no-op。",
    },
    {
        "id": "C-01", "axis": "C 组合缺失", "block": ["pptx", "pypdf"],
        "expect": {"exit": 0, "status": "partial", "writes_result": True,
                   "deck_present": False},
        "note": "同时缺 python-pptx 与 pypdf（最小评测容器常见形态）。",
    },
    {
        "id": "C-02", "axis": "C 组合缺失", "block": ["pptx", "PIL"],
        "expect": {"exit": 0, "status": "partial", "writes_result": True,
                   "deck_present": False, "previews_present": False},
        "note": "同时缺 python-pptx 与 Pillow：核心可编辑交付与预览都没了，"
                "但页计划/证据链/result.json 必须仍在。",
    },
    {
        "id": "C-03", "axis": "C 组合缺失", "block": ["pptx", "PIL", "pypdf"],
        "expect": {"exit": 0, "status": "partial", "writes_result": True,
                   "deck_present": False, "previews_present": False},
        "note": "缺全部三个可选第三方库：只剩标准库能力。",
    },
    {
        "id": "O-01", "axis": "O 真实栅格化", "block": [], "missing_cli": ["soffice"],
        "expect": {"exit": 0, "status": "partial", "writes_result": True,
                   "deck_present": True, "previews_present": True, "no_op": True},
        "note": "soffice/libreoffice 不在 PATH 上（本机事实）：本包不调用它，"
                "预览仍是 PIL 模拟（result.json 里已有 uncertainty 说明）。",
    },
    {
        "id": "O-02", "axis": "O 真实栅格化", "block": ["PIL"], "missing_cli": ["soffice"],
        "expect": {"exit": 0, "status": "partial", "writes_result": True,
                   "deck_present": False, "previews_present": False},
        "note": "既没有 LibreOffice 真实栅格化、也没有 Pillow 模拟：预览**彻底不可用**；"
                "又因 python-pptx 依赖 Pillow，可编辑 .pptx 也一并产不出来 —— "
                "只剩页计划 / 证据链 / 审计 / result.json（这条是「哪些功能彻底不可用」的硬证据）。",
    },
]

# 逐级最小环境（每级 = 允许这些第三方顶层模块，其余第三方全拦）
# 实测教训：python-pptx 自己依赖 Pillow / lxml / XlsxWriter / typing_extensions
# （`importlib.metadata.distribution("python-pptx").requires` 的声明），
# 只放行 "pptx" 并不能让 `import pptx` 成功 —— lxml 缺了就直接 ImportError。
ENV_LADDER = [
    {"id": "M-01", "allow": [],
     "question": "只有 Python 标准库，能不能跑完并写出 result.json？"},
    {"id": "M-02", "allow": ["pptx"],
     "question": "标准库 + 只放行顶层模块 pptx（**不放行它的传递依赖**）：能产出可编辑 .pptx 吗？"},
    {"id": "M-03", "allow": ["PIL"],
     "question": "标准库 + Pillow：能产出 PNG 预览吗？"},
    {"id": "M-04", "allow": ["pptx", "PIL", "lxml", "xlsxwriter", "typing_extensions"],
     "question": "放行 python-pptx 及其**全部传递依赖**再加 Pillow：能拿到完整形态吗？"},
    {"id": "M-05", "allow": ["pptx", "PIL", "lxml", "xlsxwriter", "typing_extensions",
                             "pypdf"],
     "question": "再加 pypdf：PDF 材料也能解析（= 本机完整环境）。"},
]

# 「最小可用环境」候选：要放行的第三方模块集合
MINIMAL_CANDIDATES = [
    {"id": "MIN-json-only", "allow": [],
     "purpose": "拿到契约完整的 result.json（页计划 + 证据链 + 审计），没有可编辑 deck、没有预览"},
    {"id": "MIN-json+previews", "allow": ["PIL"],
     "purpose": "result.json + PNG 预览（可图形化检查页布局）"},
    {"id": "MIN-full", "allow": ["pptx", "PIL", "lxml", "xlsxwriter",
                                 "typing_extensions", "pypdf"],
     "purpose": "完整形态：可编辑 deck + 预览 + PDF 解析"},
]


# ---------------------------------------------------------------------------
# 子进程引导脚本：先装 import blocker，再跑 main.py
# ---------------------------------------------------------------------------
BOOTSTRAP = r'''
import json, os, runpy, sys

_cfg = json.loads(os.environ["DEGRADE_PROBE_CFG"])
_blocked = set(_cfg.get("block") or [])
_allow = _cfg.get("allow")

_list_file = os.environ.get("DEGRADE_PROBE_LISTFILE")
_target = os.environ["DEGRADE_PROBE_MAIN"]

# 技能自身模块（common / evidence / scaffold_plan / ...）永远放行：
# 它们随包提供，不算外部依赖；拦掉它们只会得到无意义的 ModuleNotFoundError。
_scripts_dir = os.path.dirname(os.path.abspath(_target))
_skill_modules = {os.path.splitext(fn)[0]
                  for fn in os.listdir(_scripts_dir) if fn.endswith(".py")}

def _is_blocked(name, _b=tuple(_blocked), _own=frozenset(_skill_modules)):
    top = name.split(".")[0]
    if top in _own:
        return False
    for p in _b:
        if name == p or name.startswith(p + "."):
            return True
    return False

class _Blocker:
    def find_spec(self, fullname, path=None, target=None):
        if _is_blocked(fullname):
            raise ImportError("[degrade_probe] %s blocked by controlled import interception"
                              % fullname)
        return None

class _AllowList:
    """只允许白名单里的第三方顶层模块（其余第三方一律拒绝）。"""
    _stdlib = set(sys.stdlib_module_names)
    _own = frozenset(_skill_modules)

    def __init__(self, allow=()):
        # allow 必须存在实例上：find_spec 是热路径，读实例属性最稳
        self._allow = tuple(allow or ())

    def find_spec(self, fullname, path=None, target=None):
        top = fullname.split(".")[0]
        if top in self._own or top in self._stdlib or top.startswith("_"):
            return None
        if top in (self._allow or ()):
            return None
        raise ImportError("[degrade_probe] non-whitelisted third-party module %s blocked"
                          % fullname)

# 让 `import common` 这类包内导入可用：脚本目录进 sys.path[0]（与直接跑 main.py 一致）
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

os.environ.setdefault("PYTHONPATH", _scripts_dir)

sys.meta_path.insert(0, _Blocker() if _allow is None else _AllowList(_allow))

sys.argv = [_target] + sys.argv[1:]
try:
    runpy.run_path(_target, run_name="__main__")
    _rc = 0
except SystemExit as exc:
    _rc = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
except BaseException as exc:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    _rc = 70
finally:
    if _list_file:
        try:
            with open(_list_file, "w", encoding="utf-8") as fh:
                json.dump({"loaded_modules": sorted(m for m in sys.modules if m),
                           "blocked_prefixes": sorted(_blocked),
                           "allow": _allow}, fh, ensure_ascii=False, indent=2)
        except Exception:
            pass
sys.exit(_rc)
'''


def _copy_skill(sandbox):
    dst = os.path.join(sandbox, "skill")
    shutil.copytree(SKILL_ROOT, dst,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return dst


def _which(name):
    return shutil.which(name)


def _probe_env():
    """本机第三方库现状（用于报告里的对照，不参与判读）。"""
    out = {}
    for mod in ("pptx", "PIL", "pypdf", "matplotlib", "numpy", "yaml"):
        try:
            m = __import__(mod)
            out[mod] = getattr(m, "__version__", "unknown")
        except Exception:  # noqa: BLE001
            out[mod] = None
    out["_cli_soffice"] = _which("soffice")
    out["_cli_libreoffice"] = _which("libreoffice")
    return out


def run_config(skill_copy, sandbox, cfg, timeout):
    pid = cfg["id"]
    work = os.path.join(sandbox, "probes", pid)
    os.makedirs(work, exist_ok=True)
    bootstrap = os.path.join(work, "bootstrap.py")
    with open(bootstrap, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(BOOTSTRAP)
    list_file = os.path.join(work, "loaded_modules.json")
    out_dir = os.path.join(work, "out")
    main_py = os.path.join(skill_copy, "scripts", "main.py")
    case = os.path.join(skill_copy, "examples")
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    env["DEGRADE_PROBE_CFG"] = json.dumps(
        {"block": cfg.get("block") or [], "allow": cfg.get("allow")})
    env["DEGRADE_PROBE_MAIN"] = main_py
    env["DEGRADE_PROBE_LISTFILE"] = list_file
    cmd = [sys.executable, bootstrap, "--case", case, "--out", out_dir, "--quiet"]
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(cmd, cwd=work, env=env, timeout=timeout,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        rc, out, err = -9, (exc.stdout or b""), (exc.stderr or b"") + b"\nTIMEOUT"
    wall = round(time.perf_counter() - t0, 3)

    rj = os.path.join(out_dir, "result.json")
    row = {
        "id": pid, "axis": cfg["axis"], "blocked_imports": cfg.get("block") or [],
        "allow_list": cfg.get("allow"), "note": cfg["note"],
        "missing_cli_probed": cfg.get("missing_cli") or [],
        "exit_code": rc, "wall_seconds": wall, "writes_result_json": os.path.exists(rj),
        "stderr_tail": err.decode("utf-8", "replace").strip().splitlines()[-3:],
        "stdout_tail": out.decode("utf-8", "replace").strip().splitlines()[-3:],
    }
    if os.path.exists(list_file):
        with open(list_file, "r", encoding="utf-8") as fh:
            lm = json.load(fh)
        row["loaded_modules_probe"] = {
            "matplotlib_loaded": any(m.split(".")[0] == "matplotlib"
                                     for m in lm.get("loaded_modules", [])),
            "numpy_loaded": any(m.split(".")[0] == "numpy"
                                for m in lm.get("loaded_modules", [])),
            "yaml_loaded": any(m.split(".")[0] == "yaml"
                               for m in lm.get("loaded_modules", [])),
            "pptx_loaded": any(m.split(".")[0] == "pptx"
                               for m in lm.get("loaded_modules", [])),
            "PIL_loaded": any(m.split(".")[0] == "PIL"
                              for m in lm.get("loaded_modules", [])),
            "pypdf_loaded": any(m.split(".")[0] in ("pypdf", "PyPDF2")
                                for m in lm.get("loaded_modules", [])),
            "total_modules": len(lm.get("loaded_modules", [])),
        }
    else:
        row["loaded_modules_probe"] = None

    # 产物清单（相对 out）
    products = []
    if os.path.isdir(out_dir):
        for dirpath, dirnames, filenames in os.walk(out_dir):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in sorted(filenames):
                products.append(os.path.relpath(os.path.join(dirpath, fn), out_dir)
                                .replace("\\", "/"))
    row["products"] = sorted(products)
    row["product_count"] = len(products)
    row["has_deck"] = "editable_deck.pptx" in row["products"]
    row["preview_pngs"] = sorted(p for p in row["products"]
                                 if p.startswith("previews/") and p.endswith(".png"))
    row["has_preview_manifest"] = "previews/preview_manifest.json" in row["products"]
    row["has_plan"] = "talk_plan.json" in row["products"]
    row["has_evidence_map"] = "evidence_map.json" in row["products"]
    row["has_evidence_audit"] = "evidence_audit.json" in row["products"]
    row["has_plan_gates"] = "plan_gates.json" in row["products"]
    row["has_self_check"] = "self_check.json" in row["products"]

    if not row["writes_result_json"]:
        row["verdict"] = "无法判读：没有写出 result.json"
        row["expectation_met"] = False
        row["expectation_failed"] = ["result.json missing"]
        return row

    with open(rj, "r", encoding="utf-8") as fh:
        result = json.load(fh)
    arts = result.get("artifacts") or {}
    row["status"] = result.get("status")
    row["n_pages"] = len(result.get("pages") or [])
    row["artifacts_editable_deck"] = arts.get("editable_deck")
    row["artifacts_deck_limitation"] = (str(arts.get("deck_limitation"))[:160]
                                        if arts.get("deck_limitation") else None)
    row["artifacts_previews"] = arts.get("previews")
    row["uncertainty_items"] = [str(u.get("item"))[:150]
                               for u in (result.get("uncertainty") or [])
                               if isinstance(u, dict)]
    row["environment"] = result.get("environment")
    dep_words = ("pptx", "python-pptx", "Pillow", "PIL", "pypdf", "预览", "依赖",
                 "matplotlib", "numpy", "yaml", "LibreOffice", "soffice")
    row["dependency_uncertainty"] = [u for u in row["uncertainty_items"]
                                     if any(w in u for w in dep_words)]
    row["dependency_change_records"] = [
        "%s: %s" % (c.get("step"), str(c.get("action"))[:180])
        for c in (result.get("change_records") or [])
        if isinstance(c, dict) and c.get("step") in ("environment", "deck", "preview",
                                                     "material")
        and any(w in str(c.get("action")) for w in dep_words)]

    # ---- 判读 ----
    exp = cfg["expect"]
    checks = [("exit_code == %s" % exp["exit"], row["exit_code"] == exp["exit"])]
    if "status" in exp:
        checks.append(("status == %s" % exp["status"], row["status"] == exp["status"]))
    if "writes_result" in exp:
        checks.append(("writes result.json", row["writes_result_json"] == exp["writes_result"]))
    if "deck_present" in exp:
        checks.append(("editable_deck present == %s" % exp["deck_present"],
                       row["has_deck"] == exp["deck_present"]))
    if "previews_present" in exp:
        got = len(row["preview_pngs"]) > 0
        checks.append(("preview PNG present == %s" % exp["previews_present"],
                       got == exp["previews_present"]))
    if exp.get("no_op"):
        lmp = row.get("loaded_modules_probe") or {}
        for mod, key in (("matplotlib", "matplotlib_loaded"), ("numpy", "numpy_loaded"),
                         ("yaml", "yaml_loaded")):
            if mod in (cfg.get("block") or []):
                checks.append(("%s never imported" % mod, lmp.get(key) is False))
    row["expectation_checks"] = [{"check": c, "ok": bool(ok)} for c, ok in checks]
    row["expectation_met"] = all(ok for _c, ok in checks)
    row["expectation_failed"] = [c for c, ok in checks if not ok]
    row["verdict"] = ("期望全部命中" if row["expectation_met"]
                      else "期望未全中：" + "; ".join(row["expectation_failed"]))
    return row


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="缺依赖降级链实测（受控导入拦截，真跑主流程）")
    ap.add_argument("--sandbox", default=None,
                    help="沙箱目录（默认 <系统临时目录>/dg-<pid>）；包内原目录全程只读")
    ap.add_argument("--report", default=None,
                    help="报告 JSON 落盘路径（默认 <sandbox>/degrade_matrix_report.json）")
    ap.add_argument("--only", default=None, help="只跑指定 id（逗号分隔，调试用）")
    ap.add_argument("--timeout", type=float, default=600.0, help="单配置超时秒")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    import tempfile
    sandbox = os.path.abspath(args.sandbox or os.path.join(
        tempfile.gettempdir(), "dg-%d" % os.getpid()))
    if os.path.isdir(sandbox):
        shutil.rmtree(sandbox)
    os.makedirs(sandbox, exist_ok=True)
    skill_copy = _copy_skill(sandbox)
    report_path = args.report or os.path.join(sandbox, "degrade_matrix_report.json")

    want = None
    if args.only:
        want = {x.strip() for x in args.only.split(",") if x.strip()}

    rows = []
    for cfg in PROBES:
        if want and cfg["id"] not in want:
            continue
        row = run_config(skill_copy, sandbox, cfg, args.timeout)
        rows.append(row)
        if not args.quiet:
            print("[%s] %-6s exit=%-3s status=%-9s deck=%-5s previews=%-3s %s" % (
                "OK" if row.get("expectation_met") else "!!", cfg["id"],
                row.get("exit_code"), row.get("status"), row.get("has_deck"),
                len(row.get("preview_pngs") or []), row.get("verdict")))

    ladder = []
    for env_cfg in ENV_LADDER:
        if want and env_cfg["id"] not in want:
            continue
        cfg = {"id": env_cfg["id"], "axis": "M 逐级最小环境",
               "block": [], "allow": env_cfg["allow"],
               "expect": {"exit": 0, "writes_result": True},
               "note": env_cfg["question"]}
        row = run_config(skill_copy, sandbox, cfg, args.timeout)
        row["question"] = env_cfg["question"]
        ladder.append(row)
        if not args.quiet:
            print("[%s] %-6s allow=%-22s exit=%-3s deck=%-5s previews=%-3s keys?" % (
                "OK" if row.get("expectation_met") else "!!", env_cfg["id"],
                ",".join(env_cfg["allow"]) or "(stdlib only)", row.get("exit_code"),
                row.get("has_deck"), len(row.get("preview_pngs") or [])))

    minimal = []
    for m in MINIMAL_CANDIDATES:
        hit = next((r for r in ladder if (r.get("allow_list") or []) == m["allow"]), None)
        minimal.append({
            "id": m["id"], "allow": m["allow"], "purpose": m["purpose"],
            "measured": None if hit is None else {
                "observed_in": hit["id"],
                "exit_code": hit["exit_code"], "status": hit.get("status"),
                "has_deck": hit.get("has_deck"),
                "preview_png_count": len(hit.get("preview_pngs") or []),
                "product_count": hit.get("product_count"),
                "writes_result_json": hit.get("writes_result_json"),
            },
        })

    unreadable = [r["id"] for r in rows + ladder if not r.get("writes_result_json")]
    unmet = [{"id": r["id"], "failed": r.get("expectation_failed")}
             for r in rows + ladder
             if r.get("writes_result_json") and not r.get("expectation_met")]
    report = {
        "tool": "scripts/degrade_probe.py",
        "skill_root": SKILL_ROOT,
        "sandbox": sandbox,
        "entry_point": "沙箱内技能副本 <sandbox>/skill/scripts/main.py（包内原目录只读）",
        "interception": "sys.meta_path 前缀拦截器，写在子进程 bootstrap 里；"
                        "只影响该子进程，不改本机已安装包",
        "host_dependency_snapshot": _probe_env(),
        "cli_availability": {"soffice": _which("soffice"),
                             "libreoffice": _which("libreoffice")},
        "probes_total": len(rows),
        "probes_unreadable": unreadable,
        "probes_expectation_unmet": unmet,
        "probes": rows,
        "environment_ladder": ladder,
        "minimal_environments": minimal,
        "coverage_declaration": COVERAGE,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": {"python": sys.version.split()[0], "platform": sys.platform},
    }
    os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    if not args.quiet:
        print("[degrade] probes=%d unreadable=%d unmet=%d; ladder=%d"
              % (len(rows), len(unreadable), len(unmet), len(ladder)))
        print("[degrade] report: %s" % report_path)
    return 0 if not unreadable else 1


COVERAGE = {
    "covered": [
        "单依赖缺失：python-pptx / Pillow(PIL) / pypdf / matplotlib / numpy / yaml",
        "组合缺失：pptx+pypdf、pptx+PIL、pptx+PIL+pypdf",
        "真实栅格化：soffice 与 libreoffice 都不在 PATH（本机事实）时的两条路径",
        "逐级最小环境：stdlib 起步，逐级放行 pptx / PIL / pypdf，实测每级可用形态",
        "每个配置都记录：退出码、status、产物清单、editable_deck、preview 文件数、"
        "是否写 result.json、依赖相关 uncertainty 与 change_records",
        "拦截是否真的生效：由子进程退出时导出的 sys.modules 清单证明"
        "（被拦模块从未被加载）",
    ],
    "not_covered": [
        "python-pptx 存在但版本过旧或运行期抛错：拦截器只模拟导入失败，未模拟导入成功但"
        "运行期抛错（后者在 main.py 里是 status=failed 路径）",
        "磁盘写满 / 只读输出目录：未模拟 IO 失败（属环境故障，不属缺依赖）",
        "字体缺失：本机有 msyh.ttc，未模拟无 CJK 字体（该路径由 render.font_status 记录，"
        "不在本探针）",
        "跨平台：只在 Windows + Python 3.13.9 上实测；Linux 容器上的差异未测",
        "pypdf 的真实解析降级：本案例的 dataset_card.pdf 本就缺文件，"
        "「有 PDF 但缺 pypdf」这一格只验证了不崩、未验证解析降级文案",
    ],
}


if __name__ == "__main__":
    sys.exit(main())
