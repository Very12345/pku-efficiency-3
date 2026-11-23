#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_rerun.py — 再跑验证与确定性检验（CP5 收尾 / D18 / 增益可验证性）

两种模式：
1. 默认（--rerun-dir 指定）：用与首次完全相同的输入/参数把 main.py 再跑一遍到
   新目录，然后逐文件对比 sha256 —— SVG/PNG/data_manifest/validation 应字节级
   稳定；result.json 允许仅时间戳（steps/change_records ts）不同，做归一化对比。
2. --record-only：不重跑，只对现有输出目录记录 artifacts sha256 清单
   （供 result.json artifacts_sha256 使用）。

cli：
  python verify_rerun.py --case <case.json> --out <out_dir> [--rerun-dir <tmp>] [--json]
  python verify_rerun.py --record-only --dir <out_dir> [--json]

退出码：0 = 确定性通过（或无差异文件）；1 = 存在非时间戳差异或产物缺失。
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chartkit as ck  # noqa: E402

_COMPARE_NAMES = ["figure-%s.svg", "figure-%s.png", "figure-%s.pdf",
                  "data_manifest.json", "validation.json", "result.json"]


def sha256_of(path):
    h = ck.sha256_file(path)
    return h


def _ts_strip(obj):
    """归一化 result.json 用于对比：剔除时间戳(ts)、自引用哈希(artifacts_sha256)
    与人工 --note 记录（输入级差异，不属图稿字节，D11/D12）。"""
    if isinstance(obj, dict):
        if obj.get("action") == "manual" and {"ts", "action", "detail"}.issuperset(obj.keys()):
            return None
        return {k: _ts_strip(v) for k, v in obj.items() if k not in ("ts", "artifacts_sha256")}
    if isinstance(obj, list):
        return [v for v in (_ts_strip(x) for x in obj) if v is not None]
    return obj


def _pdf_date_strip(data: bytes) -> bytes:
    """剔除 PDF 内嵌日期（Pillow 写入的 /CreationDate /ModDate），用于公平对比。"""
    import re
    data = re.sub(rb"/CreationDate \([^)]*\)", b"/CreationDate (D:0)", data)
    data = re.sub(rb"/ModDate \([^)]*\)", b"/ModDate (D:0)", data)
    return data


def _list_outputs(out_dir):
    names = set()
    rp = os.path.join(out_dir, "result.json")
    if os.path.exists(rp):
        with open(rp, "r", encoding="utf-8") as f:
            res = json.load(f)
        for o in res.get("outputs", []):
            names.add(str(o.get("file", "")))
    else:
        for fn in os.listdir(out_dir):
            if fn.endswith((".svg", ".png", ".pdf")):
                names.add(fn)
    names.update(["data_manifest.json", "validation.json", "result.json"])
    return sorted(n for n in names if n)


def record_shas(out_dir):
    """记录输出目录内产出文件的 sha256（供 result.json artifacts_sha256）。"""
    out = {}
    for n in _list_outputs(out_dir):
        p = os.path.join(out_dir, n)
        if os.path.exists(p):
            try:
                out[n] = sha256_of(p)
            except Exception as exc:
                out[n] = f"error: {exc}"
    return out


def verify_rerun(case_path, out_dir, rerun_dir, extra_args=None):
    """重跑 main.py 到 rerun_dir，与 out_dir 逐文件对比。
    重跑使用与原输出相同的 style/dpi（从原 result.json environment 读取），
    保证"同输入同参数"；extra_args 可显式覆盖。
    """
    import main as main_mod
    report = {"case": case_path, "original_dir": out_dir, "rerun_dir": rerun_dir,
              "files": {}, "identical": [], "differ": [], "missing": []}
    if not os.path.isdir(rerun_dir):
        os.makedirs(rerun_dir, exist_ok=True)
    argv = ["--case", os.path.abspath(case_path), "--out", os.path.abspath(rerun_dir)]
    # 继承原运行参数（style/dpi），确保对照公平（D12）
    rp = os.path.join(out_dir, "result.json")
    if os.path.exists(rp):
        try:
            with open(rp, "r", encoding="utf-8") as f:
                _env = (json.load(f).get("environment") or {})
            if _env.get("style"):
                argv += ["--style", str(_env["style"])]
            if _env.get("dpi") is not None:
                argv += ["--dpi", str(int(_env["dpi"]))]
        except Exception:
            pass
    if extra_args:
        argv += extra_args
    # main 的正常退出码：completed=0 / partial=2 / failed=1；重跑仅作对比，不因状态码判失败
    # main.py 会向 stdout 打印过程日志；在 --json 模式下把它们重定向到 rerun_dir/rerun_main.log，
    # 保证 stdout 只有最终 JSON 报告（--json 可被直接 json.load 消费）。
    import contextlib
    import io
    rerun_log = os.path.join(rerun_dir, "rerun_main.log")
    stdout_target = io.StringIO()
    try:
        with open(rerun_log, "w", encoding="utf-8") as _logf:
            pass  # 预建文件，便于查看
    except Exception:
        pass
    try:
        if os.environ.get("VERIFY_RERUN_QUIET") or os.environ.get("DSH_JSON_MODE"):
            with contextlib.redirect_stdout(stdout_target):
                main_mod.main(argv)
        else:
            with open(rerun_log, "a", encoding="utf-8") as _logf:
                with contextlib.redirect_stdout(_logf), contextlib.redirect_stderr(_logf):
                    main_mod.main(argv)
        report["rerun_exit"] = "completed(0)"
    except SystemExit as exc:
        report["rerun_exit"] = f"exit={exc.code}"
    except Exception as exc:
        report["rerun_error"] = f"{type(exc).__name__}: {exc}"
        report["all_pass"] = False
        return report
    names = sorted(set(_list_outputs(out_dir)) | set(_list_outputs(rerun_dir)))
    all_ok = True
    for n in names:
        p1, p2 = os.path.join(out_dir, n), os.path.join(rerun_dir, n)
        if not os.path.exists(p1) or not os.path.exists(p2):
            report["missing"].append(n)
            report["files"][n] = "missing"
            all_ok = False
            continue
        s1, s2 = sha256_of(p1), sha256_of(p2)
        if s1 == s2:
            report["identical"].append(n)
            report["files"][n] = "SAME"
            continue
        no_diff = False
        if n == "result.json":
            try:
                with open(p1, "r", encoding="utf-8") as f1, open(p2, "r", encoding="utf-8") as f2:
                    no_diff = _ts_strip(json.load(f1)) == _ts_strip(json.load(f2))
            except Exception:
                no_diff = False
            status_label = "SAME (ts/自哈希/manual 归一化后一致)" if no_diff else "DIFF"
        elif n.endswith(".pdf"):
            with open(p1, "rb") as f1, open(p2, "rb") as f2:
                no_diff = _pdf_date_strip(f1.read()) == _pdf_date_strip(f2.read())
            status_label = "SAME (PDF 仅内嵌日期差异)" if no_diff else "DIFF (非日期差异)"
        else:
            status_label = "DIFF"
        if no_diff:
            report["identical"].append(n)
            report["files"][n] = status_label
        else:
            report["differ"].append(n)
            report["files"][n] = status_label
            all_ok = False
    report["summary"] = {"identical": len(report["identical"]),
                         "differ": len(report["differ"]),
                         "missing": len(report["missing"])}
    report["all_pass"] = all_ok
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description="再跑验证与确定性检验（CP5/D18）")
    ap.add_argument("--case", default=None)
    ap.add_argument("--out", default=None, help="首次输出目录（对比基准）")
    ap.add_argument("--rerun-dir", default=None, help="重跑目标目录（缺省自动临时目录）")
    ap.add_argument("--record-only", action="store_true",
                    help="不重跑，只记录现有目录 artifacts sha256")
    ap.add_argument("--dir", default=None, help="record-only 的目标目录")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.record_only:
        d = args.dir or args.out
        if not d or not os.path.isdir(d):
            print("record-only 需要 --dir <out_dir>", file=sys.stderr)
            sys.exit(1)
        shas = record_shas(d)
        if args.json:
            print(json.dumps({"dir": d, "artifacts_sha256": shas}, ensure_ascii=False, indent=2))
        else:
            for n, s in sorted(shas.items()):
                print(f"  {n}: {s}")
        sys.exit(0)

    if not args.case or not args.out:
        print("需要 --case 与 --out", file=sys.stderr)
        sys.exit(1)
    rerun = args.rerun_dir
    if not rerun:
        import tempfile
        rerun = tempfile.mkdtemp(prefix="verify-rerun-")
    if args.json:
        # --json：main 过程日志进 rerun_main.log，stdout 只输出 JSON 报告
        os.environ.setdefault("VERIFY_RERUN_QUIET", "1")
    report = verify_rerun(args.case, args.out, rerun)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for n, st in sorted(report["files"].items()):
            print(f"  {n}: {st}")
        print(f"SUMMARY: {'DETERMINISTIC' if report['all_pass'] else 'DIFFERENCES FOUND'} "
              f"(identical={report['summary']['identical']} differ={report['summary']['differ']} "
              f"missing={report['summary']['missing']})")
    sys.exit(0 if report["all_pass"] else 1)


if __name__ == "__main__":
    main()