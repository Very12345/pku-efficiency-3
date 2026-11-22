#!/usr/bin/env python3
"""doc-check — 文档承诺 vs 脚本事实 的一致性检查器（只读，无副作用）。

它把"文档里写的决策规则/检查名/CLI 参数"与"scripts/ 里真实存在的符号"
逐条对拍，输出三类报告：

  [OK]   文档提到的符号在脚本里真实存在
  [FAIL] 文档提到的符号在脚本里找不到（文档承诺了代码没有的东西）
  [WARN] 文档引用了尚未在本包登记的区域（如 references/ 下的扩展文档）

设计原则：**只读**。不修改任何文件、不写任何产物、不联网。
因此它可以被反复运行而不影响交付物，也不会产生 __pycache__（用 -B 或
PYTHONDONTWRITEBYTECODE=1 调用更稳妥）。

用法：
  python scripts/doccheck.py                       # 默认检查技能根
  python scripts/doccheck.py --root /skills/weekly-skill
  python scripts/doccheck.py --root . --json       # 机器可读输出
  (--root 指定技能根，--json 输出机器可读结果，--files 只检查指定文档)
  python scripts/doccheck.py --files SKILL.md README.md --json

退出码：0 = 无 FAIL；1 = 至少一条 FAIL；2 = 参数/环境错误。
"""
import argparse
import json
import os
import re
import sys

try:  # 窄编码控制台兜底，不改任何逻辑
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except Exception:
    pass

# roles whose check id is built at runtime as "artifact.%s" % role
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)

# 文档里允许出现的"带点标识符"白名单后缀：这些是文件名/版本，不是检查名
FILE_SUFFIXES = {
    "md", "py", "json", "txt", "csv", "yaml", "yml", "svg", "png", "pdf",
    "tiff", "eps", "pptx", "html", "xml", "sh", "tsv", "xlsx", "docx",
}
VERSIONISH = re.compile(r"^v?\d+([._]\d+)*$")

# 检查名族：以这些前缀开头的 "a.b" 标识符必须在脚本里能找到
CHECK_PREFIXES = ("spec.", "svg.", "bitmap.", "pdf.", "legend.", "data_mapping.",
                  "traceability.", "artifact.", "font.", "edit.", "rule.",
                  "pipeline")

# 明确豁免：这些"带点小写标识符"在本包里是**数据字段名**而不是检查名。
# 每条都要写清理由；豁免表是有意公开的，避免"静默跳过"。
EXEMPT = {
    "manifest.style.canvas": "manifest 的 style.canvas 字段路径，不是检查名",
    "data.table.rows": "manifest 的 data.table.rows 字段路径，不是检查名",
    "case.output_contract": "case.json 的 output_contract 字段路径，不是检查名",
    "verification.checks.fail_count": "result.json 的嵌套字段路径，不是检查名",
    "verification.checks.fails": "result.json 的嵌套字段路径，不是检查名",
    "verification.checks.warns": "result.json 的嵌套字段路径，不是检查名",
    "font.family": "matplotlib rcParams 属性名，不是本技能产出的检查名",
    "font.size": "matplotlib rcParams 属性名，不是本技能产出的检查名",
}

# 占位/元 token：出现在文档里是举例或讲工具本身，不是真实的 CLI 契约
FLAG_EXEMPT = {
    "--help",
    "--flag",
    "-h",
}

DOTS_RE = re.compile(r"(?<![0-9A-Za-z_.])([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+)")
FLAG_RE = re.compile(r"(?<![\w-])(--[a-z][a-z0-9-]*[a-z0-9])(?![\w-])")

TARGET_FILES = ("SKILL.md", "README.md", "TEST.md", "references/RUBRIC_MAP.md",
                "references/failure-modes.md", "references/OUTPUT_CONTRACT.md",
                "references/EDIT-ACTION-SCHEMA.md", "references/CHECK-INDEX.md",
                "examples/EXPECTED-OUTPUT.md", "examples/README.md")


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def script_corpus(root):
    """所有 scripts/*.py 的源码拼合 + 逐文件文本（用于符号存在性判定）。"""
    sdir = os.path.join(root, "scripts")
    blobs, per_file = [], {}
    if os.path.isdir(sdir):
        for name in sorted(os.listdir(sdir)):
            if name.endswith(".py"):
                txt = read_text(os.path.join(sdir, name))
                per_file[name] = txt
                blobs.append(txt)
    return "\n".join(blobs), per_file


def doc_corpus(root, files=None):
    """Documents whose promises are checked. The checker's own docstring is
    included so that its own CLI options are covered by the same flag check."""
    out = {}
    for rel in (files or TARGET_FILES):
        p = os.path.join(root, rel)
        if os.path.isfile(p):
            out[rel] = read_text(p)
    return out


def collect_dotted(text):
    found = {}
    for m in DOTS_RE.finditer(text):
        tok = m.group(1)
        parts = tok.split(".")
        if parts[-1] in FILE_SUFFIXES:
            continue
        if any(VERSIONISH.match(p) for p in parts):
            continue
        if tok in EXEMPT:
            continue
        if tok.startswith(CHECK_PREFIXES):
            found.setdefault(tok, 0)
            found[tok] += 1
    return found


# 规则词汇表的表头关键词：只有出现在表头里的编号才被当作"声明的规则编号"。
# 正文里会合法地出现大量同形的短标识（实体 id `E3`、关系 id `R5`、阶段名 `S4`、
# 示例记录 `R12` 这类夹具 id），把它们当规则编号会产生整屏假阳性。因此本检查
# **只认"包自己声明的规则表"**。
VOCAB_HEADER_HINTS = ("规则", "条款", "指标", "阶段", "检查点", "决策", "机制")
RULE_TOKEN_RE = re.compile(r"^[A-Z]\d{1,2}$")


def collect_declared_rules(text):
    """从 markdown 表格里抽取"声明的规则编号"。

    判定方式：表头行（`| a | b |`，且下一行是 `|---|` 分隔行）中出现任一表头
    关键词（规则/条款/指标/阶段/检查点/决策），则把该表后续每行的**第一格**中
    形如 `A1` / `G4` 的编号视为一条声明。
    """
    declared = {}
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        if not any(h in line for h in VOCAB_HEADER_HINTS):
            continue
        if i + 1 >= len(lines) or not set(lines[i + 1].strip()) <= set("|-: 	"):
            continue
        for row in lines[i + 2:]:
            if not row.lstrip().startswith("|"):
                break
            first = row.strip().strip("|").split("|")[0].strip().strip("`* ")
            if RULE_TOKEN_RE.match(first):
                declared[first] = declared.get(first, 0) + 1
    return declared


def collect_rules(text):
    """规则编号 → {定义次数, 被引用次数}（对全文统计，不做过滤）。"""
    out = {}
    for m in re.finditer(r"(?<![0-9A-Za-z])([A-Z])(\d{1,2})(?![0-9A-Za-z])", text):
        key = m.group(1) + m.group(2)
        tail = text[m.end():m.end() + 1]
        slot = out.setdefault(key, {"defined": 0, "used": 0})
        if tail in ("、", ":", "："):
            slot["defined"] += 1
        else:
            slot["used"] += 1
    return out



def collect_flags(text):
    found = {}
    for m in FLAG_RE.finditer(text):
        found.setdefault(m.group(1), 0)
        found[m.group(1)] += 1
    return found


def code_flags(per_file):
    """从 argparse 的 add_argument 调用里抽出脚本真实支持的 flag。"""
    flags = {}
    for name, txt in per_file.items():
        for m in re.finditer(r"add_argument\(\s*[\"'](--[a-z][a-z0-9-]*)[\"']", txt):
            flags.setdefault(m.group(1), set()).add(name)
    return flags


def code_check_ids(corpus):
    """脚本里真实出现的检查名（字符串字面量形式）。"""
    ids = set()
    for m in re.finditer(r"[\"']([a-z][a-z0-9_]*\.[a-z][a-z0-9_]*)[\"']", corpus):
        tok = m.group(1)
        if tok in EXEMPT:
            continue
        ids.add(tok)
    return ids


def ok(msg):
    return {"level": "ok", "detail": msg}


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="doc-check: 文档承诺(D 规则/检查名/CLI 参数) vs scripts/ 事实 对拍")
    ap.add_argument("--root", default=SKILL_ROOT,
                    help="技能根目录（默认为本脚本上一级）")
    ap.add_argument("--files", nargs="+", default=None,
                    help="要检查的文档（相对技能根的路径）")
    ap.add_argument("--json", action="store_true", help="输出 JSON 而不是文本")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("doccheck: FATAL: not a directory: %s" % root)
        return 2
    corpus, per_file = script_corpus(root)
    if not per_file:
        print("doccheck: FATAL: no scripts/*.py under %s" % root)
        return 2
    docs = doc_corpus(root, args.files)
    docs["scripts/doccheck.py"] = read_text(os.path.join(root, "scripts",
                                                         "doccheck.py"))
    if not docs:
        print("doccheck: FATAL: none of the target documents found under %s" % root)
        return 2

    known_ids = code_check_ids(corpus)
    real_flags = code_flags(per_file)

    issues, info = [], {}

    # ---- 1) 检查名对拍 ----
    doc_ids = {}
    for rel, txt in docs.items():
        for tok, n in collect_dotted(txt).items():
            doc_ids.setdefault(tok, {})[rel] = n
    info["check_ids_documented"] = len(doc_ids)
    info["check_ids_in_code"] = len(known_ids)
    def is_covered(tok):
        """True when the documented id is really emitted by the scripts.

        Three ways an id counts as real:
          a) it appears verbatim as a string literal in scripts/;
          b) it is a documented template `family.<role>` and some concrete
             `family.<role>` id is emitted;
          c) its family is emitted dynamically, i.e. the source contains the
             printf-style prefix `family.%s` (the concrete suffix is a role,
             a format name or an action name chosen at runtime).
        """
        if tok in known_ids:
            return True
        family, _, tail = tok.partition(".")
        if tail.startswith("<") and tail.endswith(">"):
            tail = tail[1:-1]
            if (family + "." + tail) in known_ids:
                return True
        return (family + ".%s") in corpus

    missing_ids = sorted(t for t in doc_ids if not is_covered(t))
    for tok in missing_ids:
        where = ", ".join(sorted(doc_ids[tok]))
        issues.append({"level": "fail",
                       "detail": "check id %r documented in [%s] but absent from scripts/ "
                                 "(doc promises something the code does not emit)"
                                 % (tok, where)})
    unused_ids = sorted(i for i in known_ids
                        if i.startswith(CHECK_PREFIXES) and i not in doc_ids)
    for tok in unused_ids:
        issues.append({"level": "warn",
                       "detail": "check id %r exists in scripts/ but is not documented "
                                 "in the checked documents" % tok})

    # ---- 2) 规则编号对拍 ----
    # 只检查"包自己声明的规则表"里的编号（见 collect_declared_rules）：
    #   a) 每条声明过的规则必须在别处被引用（不能定义完就没人用）；
    #   b) 编号在族内必须连续（缺号 = 删了规则却留着引用）；
    #   c) 每条都必须在 SKILL.md 里被引入，否则 Agent 读不到它。
    declared = {}
    for rel, txt in docs.items():
        for rid, n in collect_declared_rules(txt).items():
            declared.setdefault(rid, {})[rel] = n
    rules = {}
    for rel, txt in docs.items():
        for rid, slot in collect_rules(txt).items():
            agg = rules.setdefault(rid, {"defined": 0, "used": 0})
            agg["defined"] += slot["defined"]
            agg["used"] += slot["used"]
    families = {}
    for rid in declared:
        families.setdefault(rid[0], []).append(rid)
    info["families"] = {f: len(v) for f, v in sorted(families.items())}
    info["rules_documented"] = len(declared)
    skill = docs.get("SKILL.md", "")
    for fam, ids in sorted(families.items()):
        numeric = sorted(int(i[1:]) for i in ids)
        for g in sorted(set(range(1, max(numeric) + 1)) - set(numeric)):
            issues.append({"level": "fail",
                           "detail": "declared rule %s%d is missing: family %s%d..%s%d "
                                     "must be gap-free" % (fam, g, fam, min(numeric),
                                                           fam, max(numeric))})
        for r in sorted(x for x in ids if rules.get(x, {}).get("used", 0) == 0):
            issues.append({"level": "fail",
                           "detail": "declared rule %s is never referenced outside its "
                                     "definition table; a rule must have a consumer" % r})
        # 覆盖性只作 WARN：一个"规则族"可以住在参考文档里（例如失败形态表
        # F1..F12 的权威描述在 references/failure-modes.md），只要 SKILL.md
        # 指向了那份文档，Agent 就能读到。硬 FAIL 只留给"跳号"与"无人引用"。
        if skill and not any(r in skill for r in ids):
            hinted = [d for d in docs if d != "SKILL.md"
                      and any(r in docs[d] for r in ids)]
            if hinted and not any(os.path.basename(h).split(".")[0] in skill
                                  for h in hinted):
                issues.append({"level": "warn",
                               "detail": "rule family %s lives in [%s] but SKILL.md does "
                                         "not name that document; the agent may never read "
                                         "it" % (fam, ", ".join(sorted(hinted)))})
    if families:
        f0 = sorted(families)[0]
        n0 = sorted(int(i[1:]) for i in families[f0])
        info["rule_range"] = "%s%d..%s%d" % (f0, n0[0], f0, n0[-1])
        info["rules_in_skill"] = sum(1 for r in declared if r in skill)

    # ---- 3) CLI 参数对拍（文档里点名的 flag 必须真实存在） ----
    doc_flags = {}
    for rel, txt in docs.items():
        for f, n in collect_flags(txt).items():
            doc_flags.setdefault(f, {})[rel] = n
    info["flags_documented"] = len(doc_flags)
    info["flags_in_code"] = len(real_flags)
    for f, where in sorted(doc_flags.items()):
        if f in FLAG_EXEMPT:
            continue
        if f not in real_flags:
            issues.append({"level": "fail",
                           "detail": "flag %r documented in [%s] but no add_argument() "
                                     "declares it" % (f, ", ".join(sorted(where)))})
    for f in sorted(real_flags):
        if f in FLAG_EXEMPT:
            continue
        if f not in doc_flags:
            issues.append({"level": "warn",
                           "detail": "flag %r exists in %s but is not documented in the "
                                     "checked documents"
                                     % (f, ", ".join(sorted(real_flags[f])))})

    # ---- 4) 必备件存在性 ----
    required = ["SKILL.md", "README.md", "TEST.md", "GITHUB_URL.txt",
                "references/OUTPUT_CONTRACT.md", "references/RUBRIC_MAP.md",
                "references/failure-modes.md", "scripts/main.py"]
    for rel in required:
        if not os.path.isfile(os.path.join(root, rel)):
            issues.append({"level": "fail", "detail": "required file missing: %s" % rel})

    fails = [i for i in issues if i["level"] == "fail"]
    warns = [i for i in issues if i["level"] == "warn"]

    if args.json:
        print(json.dumps({"root": root, "fails": fails, "warns": warns,
                          "info": info, "valid": not fails},
                         ensure_ascii=False, indent=1))
        return 1 if fails else 0

    print("doc-check: root=%s" % root)
    print("  documents: %s" % ", ".join(sorted(docs)))
    print("  check ids: %d documented / %d present in scripts"
          % (info["check_ids_documented"], info["check_ids_in_code"]))
    if info.get("rule_range"):
        print("  rule families: %s  (declared %d ids; %d of them also named in SKILL.md)"
              % (", ".join("%s[%d]" % (f, n) for f, n in info["families"].items()),
                 info["rules_documented"], info.get("rules_in_skill", 0)))

    print("  cli flags: %d documented / %d declared in scripts"
          % (info["flags_documented"], info["flags_in_code"]))
    for i in fails:
        print("  [FAIL] %s" % i["detail"])
    for i in warns:
        print("  [WARN] %s" % i["detail"])
    print("doc-check: %s (%d fails, %d warns)"
          % ("CONSISTENT" if not fails else "INCONSISTENT", len(fails), len(warns)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
