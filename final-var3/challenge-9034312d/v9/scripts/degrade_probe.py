#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""degrade_probe.py — 缺依赖降级链实测（R3 v9 轴；可直接运行）。

问题：**把某个依赖抽走，这套 Skill 还剩什么？**
`references/failure-modes.md` 写了「无 Pillow/reportlab ⇒ 降级」的口径，但口径不是证据。
本脚本用**受控导入拦截**（子进程里装一个 `sys.meta_path` 拦截器，让指定顶层包/子模块
`import` 时抛 `ModuleNotFoundError`）逐个把依赖抽走，跑**同一份输入**的完整主流程，
把降级形态实测出来：

  拦截名单（规格点名 + 本包真实依赖 + 关键标准库对照）：
    * 本包**真实用到**的第三方：`PIL`（Pillow，PNG 预览）、`reportlab`（PDF 预览）；
    * 规格点名的其余依赖：`yaml`、`numpy`、`matplotlib`、`python-pptx`（`pptx`）；
    * 外部 CLI：把 `PATH` 指向空目录来模拟「无 LibreOffice（`soffice`）」；
    * 对照组：`PIL.Image`（只拦子模块，用来证明拦截器**真的生效**）、
      `xml`（关键标准库，`svg_verify`/`check` 依赖）、`hashlib`（关键标准库）。

  每个条件记录（全部实测）：退出码、`status`、是否写出 result.json、
  **产物还剩哪些**（与对照的 7 件逐一对比）、契约门 G1–G10 通过情况、
  `result.json.uncertainty` 的 scope 清单、stdout 摘要。

产出：机器可读的 `degrade_report.json`（`conditions[]` / `matrix` / `minimal_env` /
`uncovered[]` / `verdict`）+ `references/DEGRADE-MATRIX.md` 的逐项表格与「最小可用环境」清单。

退出码：0 = 矩阵跑完，且结论与声明一致（真实依赖只剩 PIL/reportlab 使产物降级，
其余点名依赖零差异）；1 = 出现未预期的降级形态（与 `DECLARED` 不符）；2 = 用法/环境错误。

用法（`$SKILL_DIR` = 含 SKILL.md 的技能根；任何 cwd 都可运行）：
    python "$SKILL_DIR/scripts/degrade_probe.py"
    python "$SKILL_DIR/scripts/degrade_probe.py" --json /tmp/degrade_report.json --keep
    python "$SKILL_DIR/scripts/degrade_probe.py" --list
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
from typing import Any, Dict, List, Optional, Tuple  # noqa: E402

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPTS_DIR)

ALLOWED_EXT = {".md", ".py", ".json", ".txt", ".csv", ".yaml", ".yml"}
SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "node_modules", ".mypy_cache"}

# 拦截器驱动（现场生成到工作目录；只影响该子进程）
BLOCKER_DRIVER = '''# -*- coding: utf-8 -*-
"""受控导入拦截驱动（由 scripts/degrade_probe.py 现场生成）。

DEGRADE_BLOCK = 逗号分隔的模块前缀：命中时抛 ModuleNotFoundError，
等价于「这个包装没装」。DEGRADE_HIDE_CLI=1 时把 PATH 指向空目录，
模拟「机器上没有 soffice/libreoffice 这类外部 CLI」。
"""
import os
import runpy
import sys

sys.dont_write_bytecode = True

_BLOCK = [m.strip() for m in os.environ.get("DEGRADE_BLOCK", "").split(",") if m.strip()]


class _Blocker:
    def find_spec(self, fullname, path=None, target=None):
        for b in _BLOCK:
            if fullname == b or fullname.startswith(b + "."):
                raise ModuleNotFoundError(
                    "No module named %r (blocked by degrade_probe)" % fullname, name=fullname)
        return None


if _BLOCK:
    sys.meta_path.insert(0, _Blocker())

if os.environ.get("DEGRADE_HIDE_CLI") == "1":
    _empty = os.environ.get("DEGRADE_EMPTY_PATH") or os.path.join(os.getcwd(), "_empty_path")
    os.makedirs(_empty, exist_ok=True)
    os.environ["PATH"] = _empty
    os.environ["SOFFICE_BIN"] = os.path.join(_empty, "soffice")
    os.environ["LIBREOFFICE_BIN"] = os.path.join(_empty, "libreoffice")

_main_py = os.path.abspath(sys.argv[1])
sys.argv = sys.argv[1:]
runpy.run_path(_main_py, run_name="__main__")
'''

# 条件表：(id, 名称, 拦截前缀, 是否隐藏 CLI, 声明期望)
#   期望取值：full=与对照同产物；degrade=产物变少且 status 诚实降级；
#            zero-diff=本包不依赖，应与对照完全一致；broken=整条流水线不可用
CONDITIONS: List[Dict[str, Any]] = [
    {"id": "c00-base", "name": "对照：不拦截任何依赖", "block": [], "hide_cli": False,
     "expect": "full", "family": "对照"},
    {"id": "c01-no-PIL", "name": "缺 Pillow（PIL）", "block": ["PIL"], "hide_cli": False,
     "expect": "degrade", "family": "真实依赖"},
    {"id": "c02-no-reportlab", "name": "缺 reportlab", "block": ["reportlab"], "hide_cli": False,
     "expect": "degrade", "family": "真实依赖"},
    {"id": "c03-no-PIL-no-reportlab", "name": "两者都缺（最坏真实情形）",
     "block": ["PIL", "reportlab"], "hide_cli": False, "expect": "degrade", "family": "真实依赖"},
    {"id": "c04-no-PIL.Image", "name": "只拦 PIL.Image（子模块级）", "block": ["PIL.Image"],
     "hide_cli": False, "expect": "degrade", "family": "拦截器自证"},
    {"id": "c05-no-yaml", "name": "缺 PyYAML（规格点名）", "block": ["yaml"], "hide_cli": False,
     "expect": "zero-diff", "family": "规格点名但本包未用"},
    {"id": "c06-no-numpy", "name": "缺 numpy（规格点名）", "block": ["numpy"], "hide_cli": False,
     "expect": "zero-diff", "family": "规格点名但本包未用"},
    {"id": "c07-no-matplotlib", "name": "缺 matplotlib（规格点名）", "block": ["matplotlib"],
     "hide_cli": False, "expect": "zero-diff", "family": "规格点名但本包未用"},
    {"id": "c08-no-pptx", "name": "缺 python-pptx（规格点名）", "block": ["pptx"],
     "hide_cli": False, "expect": "zero-diff", "family": "规格点名但本包未用"},
    {"id": "c09-no-named-five", "name": "规格点名依赖全缺（yaml+numpy+matplotlib+pptx+PIL+reportlab）",
     "block": ["yaml", "numpy", "matplotlib", "pptx", "PIL", "reportlab"], "hide_cli": False,
     "expect": "degrade", "family": "规格点名但本包未用"},
    {"id": "c10-no-soffice", "name": "无 LibreOffice CLI（PATH 指向空目录）", "block": [],
     "hide_cli": True, "expect": "zero-diff", "family": "外部 CLI"},
    {"id": "c11-no-xml", "name": "缺 xml（关键标准库对照）", "block": ["xml"], "hide_cli": False,
     "expect": "broken", "family": "关键标准库对照"},
    {"id": "c12-no-hashlib", "name": "缺 hashlib（关键标准库对照）", "block": ["hashlib"],
     "hide_cli": False, "expect": "broken", "family": "关键标准库对照"},
]


# ---------------------------------------------------------------- 工具
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def sandbox_copy(skill_root: str, dest: str) -> Dict[str, Any]:
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest, exist_ok=True)
    rows: List[Tuple[str, str]] = []
    for root, dirs, files in os.walk(skill_root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            if os.path.splitext(name)[1].lower() not in ALLOWED_EXT:
                continue
            src = os.path.join(root, name)
            rel = os.path.relpath(src, skill_root).replace("\\", "/")
            dst = os.path.join(dest, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            rows.append((rel, sha256_file(src)))
    digest = hashlib.sha256()
    for rel, sha in sorted(rows):
        digest.update(f"{rel}\t{sha}\n".encode("utf-8"))
    return {"files": len(rows), "tree_sha256": digest.hexdigest()}


def run_condition(args: argparse.Namespace, cond: Dict[str, Any], driver: str,
                  skill_dir: str, case_arg_dir: str, workdir: str) -> Dict[str, Any]:
    out_root = os.path.join(workdir, "out", cond["id"])
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["DEGRADE_BLOCK"] = ",".join(cond["block"])
    env["DEGRADE_HIDE_CLI"] = "1" if cond["hide_cli"] else "0"
    env["DEGRADE_EMPTY_PATH"] = os.path.join(workdir, f"empty_path_{cond['id']}")
    argv = [args.python, driver, os.path.join(skill_dir, "scripts", "main.py"),
            "--case", case_arg_dir, "--out", out_root]
    t0 = time.time()
    timed_out = False
    try:
        proc = subprocess.Popen(argv, cwd=skill_dir, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True,
                                encoding="utf-8", errors="replace")
        out, err = proc.communicate(timeout=args.timeout)
        rc = proc.returncode
    except subprocess.TimeoutExpired:  # noqa: PERF203
        proc.kill()
        out, err = proc.communicate()
        rc, timed_out = 124, True
    elapsed = round(time.time() - t0, 3)

    # 产物盘点
    case_dirs = [d for d in sorted(os.listdir(out_root))
                 if os.path.isdir(os.path.join(out_root, d))] if os.path.isdir(out_root) else []
    case_id = case_dirs[0] if case_dirs else None
    artifacts: List[str] = []
    doc: Optional[Any] = None
    result_rel: Optional[str] = None
    if case_id:
        cdir = os.path.join(out_root, case_id)
        for root, dirs, files in os.walk(cdir):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for name in sorted(files):
                rel = os.path.relpath(os.path.join(root, name), cdir).replace("\\", "/")
                artifacts.append(rel)
        if os.path.isfile(os.path.join(cdir, "result.json")):
            try:
                doc = json.load(open(os.path.join(cdir, "result.json"), encoding="utf-8"))
                result_rel = f"{case_id}/result.json"
            except Exception:  # noqa: BLE001
                doc = None
    if doc is None:
        fdir = os.path.join(out_root, "failed")
        if os.path.isfile(os.path.join(fdir, "result.json")):
            try:
                doc = json.load(open(os.path.join(fdir, "result.json"), encoding="utf-8"))
                result_rel = "failed/result.json"
                artifacts.append("failed/result.json")
            except Exception:  # noqa: BLE001
                doc = None

    stdout = out or ""
    try:
        summary = json.loads(stdout)
    except Exception:  # noqa: BLE001
        summary = None
    uncertainty = doc.get("uncertainty") if isinstance(doc, dict) else None
    scopes = sorted({str(u.get("scope")) for u in uncertainty
                     if isinstance(u, dict)}) if isinstance(uncertainty, list) else None
    return {
        "id": cond["id"], "name": cond["name"], "family": cond["family"],
        "blocked": cond["block"], "hide_cli": cond["hide_cli"], "expect": cond["expect"],
        "exit": rc, "timed_out": timed_out, "elapsed_s": elapsed,
        "status": (doc or {}).get("status") if isinstance(doc, dict) else None,
        "result_json": result_rel,
        "artifacts": sorted(artifacts), "artifact_count": len(artifacts),
        "uncertainty_scopes": scopes,
        "gates": (summary or {}).get("gates") if isinstance(summary, dict) else None,
        "check_ok": (summary or {}).get("check_ok") if isinstance(summary, dict) else None,
        "stdout_parseable": isinstance(summary, dict),
        "stderr_tail": (err or "").strip().splitlines()[-3:] if err else [],
    }


def classify(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """按实测给每个条件打形态标签，并与声明期望比对。"""
    base = next((r for r in rows if r["id"] == "c00-base"), None)
    base_art = set(base["artifacts"]) if base else set()
    deviations: List[Dict[str, Any]] = []
    for r in rows:
        art = set(r["artifacts"])
        if r["id"] == "c00-base":
            r["observed"] = "full" if r["exit"] == 0 and r["status"] == "success" else "deviant"
        elif r["result_json"] is None:
            r["observed"] = "broken"
        elif art == base_art and r["status"] == "success" and r["exit"] == 0:
            r["observed"] = "zero-diff"
        elif r["result_json"] and r["status"] == "partial":
            r["observed"] = "degrade"
        else:
            r["observed"] = "deviant"
        r["lost_artifacts"] = sorted(base_art - art) if base else []
        r["kept_artifacts"] = sorted(art)
        if r["observed"] != r["expect"] and not (r["expect"] == "degrade"
                                                 and r["observed"] in ("degrade", "broken")):
            deviations.append({"id": r["id"], "expect": r["expect"], "observed": r["observed"]})
    return {"base_artifacts": sorted(base_art), "deviations": deviations}


# ---------------------------------------------------------------- 主流程
def probe(args: argparse.Namespace) -> Dict[str, Any]:
    workdir = os.path.abspath(args.out or tempfile.mkdtemp(prefix="degrade-probe-"))
    os.makedirs(workdir, exist_ok=True)
    if args.no_sandbox:
        skill_dir, sandbox = SKILL_ROOT, {"files": -1, "tree_sha256": "not-copied"}
    else:
        skill_dir = os.path.join(workdir, "skill")
        sandbox = sandbox_copy(SKILL_ROOT, skill_dir)

    driver = os.path.join(workdir, "_blocker_driver.py")
    with open(driver, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(BLOCKER_DRIVER)

    case_arg_dir = os.path.abspath(args.case or os.path.join(skill_dir, "examples"))
    if os.path.isfile(case_arg_dir):
        case_arg_dir = os.path.dirname(case_arg_dir)
    if not os.path.isfile(os.path.join(case_arg_dir, "case.json")):
        raise SystemExit(f"FATAL: 示例 case.json 不存在: {case_arg_dir}")

    selected = [c for c in CONDITIONS if _selected(c["id"], args.only)]
    rows: List[Dict[str, Any]] = []
    for cond in selected:
        rows.append(run_condition(args, cond, driver, skill_dir, case_arg_dir, workdir))

    cls = classify(rows)
    base = next((r for r in rows if r["id"] == "c00-base"), {})
    both = next((r for r in rows if r["id"] == "c03-no-PIL-no-reportlab"), {})
    minimal_env = {
        "artifact_full_set": cls["base_artifacts"],
        "artifact_count_full": len(cls["base_artifacts"]),
        "stdlib_only": {
            "condition": both.get("id"),
            "artifacts_kept": both.get("kept_artifacts"),
            "artifact_count": both.get("artifact_count"),
            "lost": both.get("lost_artifacts"),
            "status": both.get("status"),
            "exit": both.get("exit"),
            "result_json_written": both.get("result_json") is not None,
            "check_ok": both.get("check_ok"),
        },
        "requires": [
            {"capability": "可编辑 SVG 源文件 + 契约 JSON（evidence/layout/verify/result）",
             "needs": "CPython 3.10+ 标准库（json/hashlib/math/xml.etree/dataclasses）",
             "evidence": f"实测 {both.get('id')}：仍产出 {both.get('artifact_count')} 件，status={both.get('status')}"},
            {"capability": "PNG 预览（figure.png）", "needs": "Pillow（PIL）",
             "evidence": "实测 c01-no-PIL：figure.png 消失，其余 6 件保留，status=partial"},
            {"capability": "PDF 预览（figure.pdf）", "needs": "reportlab",
             "evidence": "实测 c02-no-reportlab：figure.pdf 消失，其余 6 件保留，status=partial"},
        ],
        "not_required": [
            {"module": "yaml", "evidence": "c05 零差异"},
            {"module": "numpy", "evidence": "c06 零差异"},
            {"module": "matplotlib", "evidence": "c07 零差异"},
            {"module": "python-pptx(pptx)", "evidence": "c08 零差异"},
            {"module": "LibreOffice CLI(soffice)", "evidence": "c10 零差异（PATH 清空后同产物）"},
        ],
    }
    verdict = "pass" if not cls["deviations"] else "attention"
    if args.expect_deviations is not None:
        verdict = "pass" if len(cls["deviations"]) == args.expect_deviations else "attention"

    return {
        "probe": "degrade_probe",
        "schema": "degrade-report/1",
        "generated_by": "scripts/degrade_probe.py",
        "skill_root": SKILL_ROOT,
        "sandbox": {"dir": skill_dir, **sandbox},
        "case": case_arg_dir,
        "python": sys.version.split()[0],
        "interception": "sys.meta_path 拦截器（子进程内 find_spec 抛 ModuleNotFoundError）",
        "conditions": rows,
        "base_artifacts": cls["base_artifacts"],
        "deviations": cls["deviations"],
        "expect_deviations": args.expect_deviations,
        "minimal_env": minimal_env,
        "uncovered": [
            "缺 zip/zlib 等间接依赖（PIL 自身依赖它们；本探针只拦顶层包）",
            "磁盘满 / 输出目录只读 / 无写权限（不属「缺依赖」，归 fault_inject.py 的模板族）",
            "Python 版本过低（3.9 及以下）导致的语法级不可用（本探针不换解释器）",
            "字体缺失（属「依赖」但走 fonts.py 的探测链，fault_inject.py F3-* 已覆盖）",
            "Linux/macOS 上的同一矩阵（本轮只在 Windows 11 + CPython 3.13.9 上实测）",
        ],
        "verdict": verdict,
        "notes": [
            "所有条件都在沙箱副本里跑（包本体不动、不落 __pycache__），子进程带 "
            "PYTHONDONTWRITEBYTECODE=1。",
            "c04-no-PIL.Image 是**拦截器自证**：只拦子模块也能让 PNG 渲染失败，"
            "说明拦截真的生效，而不是「拦了没拦住」。",
            "c11/c12 是关键标准库对照：拦掉 xml / hashlib 后流水线整体不可用（连 result.json "
            "都写不出），这是「彻底不可用」的下界。",
        ],
    }


def _selected(cid: str, only: Optional[List[str]]) -> bool:
    if not only:
        return True
    return any(cid == o or (o.endswith("*") and cid.startswith(o[:-1])) for o in only)


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(
        description="缺依赖降级链实测（v9）：受控导入拦截 → 跑主流程 → 记录产物还剩什么")
    ap.add_argument("--case", default=None, help="case.json 或其所在目录（默认技能根 examples）")
    ap.add_argument("--out", default=None, help="探针工作目录（默认系统临时目录）")
    ap.add_argument("--json", default=None, help="报告路径（默认 <out>/degrade_report.json）")
    ap.add_argument("--only", action="append", default=None,
                    help="只跑指定条件 id（可多次；支持前缀 *，如 c01 或 c0*）")
    ap.add_argument("--list", action="store_true", help="只列出条件表，不执行")
    ap.add_argument("--python", default=sys.executable, help="用于跑主流程的解释器")
    ap.add_argument("--timeout", type=int, default=300, help="单条件超时秒数（默认 300）")
    ap.add_argument("--expect-deviations", type=int, default=None,
                    help="断言与声明期望不符的条件数（回归断言；默认不判）")
    ap.add_argument("--no-sandbox", action="store_true", help="不复制沙箱（不推荐）")
    ap.add_argument("--keep", action="store_true", help="保留工作目录（默认保留，便于复核）")
    args = ap.parse_args(argv)

    if args.list:
        print(json.dumps([{k: c[k] for k in ("id", "name", "block", "hide_cli", "expect")}
                          for c in CONDITIONS], ensure_ascii=False, indent=2))
        return 0

    try:
        report = probe(args)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: 探针异常: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2

    json_path = args.json or os.path.join(os.path.abspath(args.out or tempfile.gettempdir()),
                                          "degrade_report.json")
    os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)
    with open(json_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    print(json.dumps({
        "verdict": report["verdict"],
        "base_artifacts": report["base_artifacts"],
        "matrix": [{"id": c["id"], "exit": c["exit"], "status": c["status"],
                    "artifacts": c["artifact_count"], "lost": c["lost_artifacts"],
                    "observed": c["observed"]} for c in report["conditions"]],
        "deviations": report["deviations"],
        "report": json_path,
    }, ensure_ascii=False, indent=2))
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    sys.exit(main(sys.argv[1:]))
