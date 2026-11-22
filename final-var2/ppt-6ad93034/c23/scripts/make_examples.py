# -*- coding: utf-8 -*-
"""make_examples.py — 维护脚本：用一次**真实运行**重建 examples/output/ 的文本产物。

为什么需要它
------------
本 Skill 包只允许 **UTF-8 文本资源**（`.md/.py/.json/.txt/.csv/.yaml/.yml`，
≤50 文件 / 单文件 ≤500KB / 合计 ≤2MB）。所以演示产物中的**二进制部分**
（`deck.pptx`、预览 `*.png`、预览 `*.pdf`）**不入包**，一律由运行时生成；
它们的清单与契约字段写在 `examples/EXPECTED-OUTPUT.md` 里。

而入包的 `examples/output/*.example.{json,md}` 必须是**真实跑出来的**、且
**不能带本机绝对路径**。本脚本就是这两件事的可复跑实现：

  1. 就地跑 `scripts/main.py --case examples/case.json --out <临时目录>`；
  2. 只回抄文本产物到 `examples/output/`（文件名插入 `.example.`）；
  3. 把机器本机绝对路径（运行输出目录 / 技能包目录）改写成**包内相对路径**。

用法（自定位，任意 cwd 均可）：

```bash
python "$SKILL_DIR/scripts/make_examples.py"                # 真跑并回抄
python "$SKILL_DIR/scripts/make_examples.py" --dry-run      # 只跑不回抄
python "$SKILL_DIR/scripts/make_examples.py" --work-dir /tmp/e3-examples
```

退出码：0 = 生成成功；2 = 流水线本身失败（此时不覆盖 examples/output）。

本脚本只在 `<work-dir>`（默认系统临时目录）与 `examples/output/` 下写入，
不改动 `scripts/`、`references/`、`templates/` 与 `examples/` 的输入文件。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck_common import ensure_dir, package_root, scripts_dir  # noqa: E402

# 回抄映射：运行输出里的文件 → examples/output/ 下的示例文件名
COPY_MAP = [
    ("result.json", "result.example.json", "json"),
    ("evidence_map.md", "evidence_map.example.md", "text"),
    ("evidence_map.json", "evidence_map.example.json", "json"),
    ("manifest.json", "manifest.example.json", "json"),
    (os.path.join("work", "plan.json"), "plan.example.json", "json"),
    (os.path.join("work", "material_view.json"), "material_view.example.json", "json"),
]


def _prefix_forms(prefix):
    """同一路径的三种写法（原生 / 全正斜杠 / 全反斜杠），避免分隔符不一致漏配。"""
    p = os.path.abspath(prefix)
    return {f for f in (p, p.replace("\\", "/"), p.replace("/", "\\")) if f}


def _sanitize_str(value, prefixes):
    """把本机绝对路径前缀换成包内相对路径（仅动被命中的字符串）。"""
    if not isinstance(value, str) or not value:
        return value
    touched = False
    for forms in prefixes:
        for form in forms:
            if form in value:
                value = value.replace(form, "")
                touched = True
    if touched:
        value = value.replace("\\", "/").lstrip("/")
    return value


def _sanitize_json(obj, prefixes):
    if isinstance(obj, dict):
        return {k: _sanitize_json(v, prefixes) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_json(v, prefixes) for v in obj]
    return _sanitize_str(obj, prefixes)


def run_pipeline(case_path, out_dir):
    """Run main.py as a subprocess (same entry point SKILL.md documents)."""
    cmd = [sys.executable, os.path.join(scripts_dir(), "main.py"),
           "--case", case_path, "--out", out_dir]
    print("[run] " + " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


def main(argv=None):
    ap = argparse.ArgumentParser(description="rebuild examples/output from a real run")
    ap.add_argument("--work-dir", default=None,
                    help="临时运行目录（默认：系统临时目录下的 e3-examples-*）")
    ap.add_argument("--dry-run", action="store_true",
                    help="只跑流水线，不回抄 examples/output/")
    args = ap.parse_args(argv)

    pkg = package_root()
    case_path = os.path.join(pkg, "examples", "case.json")
    dest_dir = ensure_dir(os.path.join(pkg, "examples", "output"))
    if not os.path.isfile(case_path):
        print("FAIL: case.json not found: %s" % case_path)
        return 2

    work_dir = args.work_dir or tempfile.mkdtemp(prefix="e3-examples-")
    out_dir = os.path.join(work_dir, "run")
    ensure_dir(work_dir)

    rc = run_pipeline(case_path, out_dir)
    if rc != 0:
        print("FAIL: pipeline exit=%s — examples/output/ 未改动" % rc)
        return 2

    prefixes = [_prefix_forms(out_dir), _prefix_forms(pkg)]
    written = []
    for rel_src, name_dst, kind in COPY_MAP:
        src = os.path.join(out_dir, rel_src)
        dst = os.path.join(dest_dir, name_dst)
        if not os.path.isfile(src):
            print("skip (missing in run): %s" % rel_src)
            continue
        if kind == "json":
            with open(src, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            data = _sanitize_json(data, prefixes)
            if args.dry_run:
                print("[dry-run] would write %s" % name_dst)
                continue
            with open(dst, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
        else:
            if args.dry_run:
                print("[dry-run] would write %s" % name_dst)
                continue
            shutil.copyfile(src, dst)
        written.append(name_dst)

    print("OK  run=%s  wrote %d file(s) into examples/output/" % (out_dir, len(written)))
    print("    二进制产物（deck.pptx / preview *.png / preview.pdf）不入包，"
          "运行时生成——清单见 examples/EXPECTED-OUTPUT.md")
    for n in written:
        print("    - %s" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
