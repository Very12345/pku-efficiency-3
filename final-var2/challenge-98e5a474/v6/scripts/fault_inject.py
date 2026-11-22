#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fault_inject.py -- 失败注入与恢复演练（可运行的故障矩阵执行器）。

本脚本把 SKILL.md §F 的**四形态故障**（输入 / 模板 / 依赖 / 契约）逐个
**故意弄坏**，然后真实跑一遍主流程（`scripts/main.py`），把每次注入的
"注入什么 → 期望行为 → 实测退出码 / status / uncertainty → 是否静默失败"
逐行记录下来，产出机器可读的 `fault-matrix.json` 与人读的文本表。

设计原则（这三条决定了它为什么能当证据用）：

1. **只读原包**：绝不修改技能包本身。每次注入都把整包复制到一个临时
   scratch 目录，在那里弄坏副本、跑副本。
2. **不改被测代码的行为**：注入只通过"动夹具 / 动数据 / 换环境变量 /
   在 scratch 副本里加一个包装模块"实现，不 patch 被测脚本的逻辑，
   不改它的 CLI 参数与退出码语义。
3. **不伪造数据**：记录的是子进程真实的 returncode 与真实产出的
   `result.json` 字段；拿不到 `result.json` 就记"无产物"，不做推断。

用法（建议在包外运行，产物写到包外）：

    python scripts/fault_inject.py --skill-root <技能根> --out <包外目录>
    python scripts/fault_inject.py --form dependency --skill-root . --out /tmp/fi
    python scripts/fault_inject.py --list
    python scripts/fault_inject.py --only D02,D07 --out /tmp/fi --json

退出码：0 = 全部注入都**符合期望**（含"被如实拒绝"）；1 = 至少一条注入
的实际行为与期望不符（**恢复演练失败**）；2 = 参数/环境错误。

注意：若要 `--out` 指向技能包**内部**，本脚本会直接拒绝（会把产物与
`__pycache__` 混进交付包，违反本题"包内只放文本资源"的硬约束）。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zlib

try:  # 窄编码控制台（GBK）不得让 --help / 日志崩溃
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(HERE)
PY = sys.executable or "python"


# --------------------------------------------------------------------------
# 小工具
# --------------------------------------------------------------------------
def read_text(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def write_bytes(path, blob):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(blob)


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path, obj, indent=2):
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=indent) + "\n")


def rm(path):
    """只删 scratch 里的东西；调用方负责保证 path 在 scratch 内。"""
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    elif os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def tail(text, n=6, width=200):
    lines = [l for l in (text or "").splitlines() if l.strip()]
    return [l[:width] for l in lines[-n:]]


# --------------------------------------------------------------------------
# scratch：整包复制 + 注入辅助
# --------------------------------------------------------------------------
class Scratch(object):
    """一个临时工作区：`pkg/` 是被注入的整包副本，`fx/` 放夹具与注入物。"""

    def __init__(self, skill_root, case_id):
        self.case_id = case_id
        self.root = tempfile.mkdtemp(prefix="sse-fault-%s-" % case_id)
        self.pkg = os.path.join(self.root, "pkg")
        self.fx = os.path.join(self.root, "fx")
        self.out = os.path.join(self.root, "out")
        shutil.copytree(skill_root, self.pkg,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        os.makedirs(self.fx, exist_ok=True)
        self.details = {}
        self.env_extra = {}          # setup() 可往里塞 PYTHONPATH 等

    # -- 路径 --
    def p(self, *parts):
        return os.path.join(self.pkg, *parts)

    def f(self, *parts):
        return os.path.join(self.fx, *parts)

    # -- 夹具读写 --
    def case(self, name="case.json"):
        return load_json(self.f("case.json" if name == "case.json"
                                else name))

    def save_case(self, obj, name="case.json"):
        dump_json(self.f(name), obj)
        return self.f(name)

    def base_case(self, rel="examples/case.json", with_sources=True):
        """以包内示例为模板，深拷贝一份可任意破坏的夹具。

        with_sources=True 时把示例的来源材料一并复制到夹具目录，
        这样"来源缺失"只由**被注入的那条**引起，不会被夹具噪声掩盖。
        """
        case = json.loads(json.dumps(load_json(self.p(rel))))
        if with_sources:
            cdir = os.path.dirname(self.p(rel))
            srcs = os.path.join(cdir, "sources")
            if os.path.isdir(srcs):
                shutil.copytree(srcs, self.f("sources"),
                                dirs_exist_ok=True)
        return case

    # -- 注入 --
    def break_case_json(self, text="[]"):
        write_text(self.f("case.json"), text)

    def edit_scripts(self, rel, fn):
        """**只在 scratch 副本里**包装某个脚本（模拟依赖/运行期故障）。

        交付包本身不受影响：注入物全部写在 tempdir 下的副本里。
        """
        path = os.path.join(self.pkg, rel)
        src = read_text(path)
        write_text(path, fn(src))

    def add_wrapper(self, rel, body):
        """在副本里新增一个包装模块（如坏掉的 render.py 替身）。"""
        write_text(os.path.join(self.pkg, rel), body)


# --------------------------------------------------------------------------
# 手写最小 PDF（stdlib 就够，不需要任何第三方库）
# --------------------------------------------------------------------------
def _pdf(objects):
    out = b"%PDF-1.4\n"
    offsets = []
    for num, body in objects:
        offsets.append((num, len(out)))
        out += ("%d 0 obj\n" % num).encode("ascii") + body + b"\nendobj\n"
    xref_at = len(out)
    maxnum = max(n for n, _ in objects)
    out += ("xref\n0 %d\n" % (maxnum + 1)).encode("ascii")
    out += b"0000000000 65535 f \n"
    for num in range(1, maxnum + 1):
        off = dict(offsets).get(num)
        out += (("%010d 00000 n \n" % off) if off is not None
                else "0000000000 65535 f \n").encode("ascii")
    out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (maxnum + 1, xref_at)).encode("ascii")
    return out


def make_text_pdf(text="sample material\n", compress=False):
    """最小可抽取文本 PDF：内容流用 Tj 之外还额外塞一个 TJ 数组。"""
    content = ("BT /F1 12 Tf 40 700 Td (%s) Tj ET\n"
               % text.replace("(", "\\(").replace(")", "\\)")).encode("ascii")
    if compress:
        content = zlib.compress(content)
        filter_entry = b" /Filter /FlateDecode"
    else:
        filter_entry = b""
    objs = [
        (1, b"<< /Type /Catalog /Pages 2 0 R >>"),
        (2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"),
        (3, b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"),
        (4, ("<< /Length %d" % len(content)).encode("ascii") + filter_entry
            + b" >>\nstream\n" + content + b"\nendstream"),
        (5, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
    ]
    return _pdf(objs)


def make_empty_pdf():
    """只有空白内容流的 PDF：模拟"扫描件/抽不出文本"。"""
    content = b"BT ET\n"
    objs = [
        (1, b"<< /Type /Catalog /Pages 2 0 R >>"),
        (2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"),
        (3, b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Contents 4 0 R >>"),
        (4, b"<< /Length %d >>\nstream\n" % len(content) + content
            + b"\nendstream"),
    ]
    return _pdf(objs)


def make_encrypted_pdf():
    """声明 /Encrypt 的 PDF：抽取器必须**如实拒绝**，不得静默出空文本。"""
    objs = [
        (1, b"<< /Type /Catalog /Pages 2 0 R >>"),
        (2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"),
        (3, b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Contents 4 0 R >>"),
        (4, b"<< /Length 0 >>\nstream\n\nendstream"),
        (5, b"<< /Filter /Standard /V 1 /R 2 /O <00> /U <00> /P -1 >>"),
    ]
    blob = _pdf(objs)
    return blob.replace(b"/Root 1 0 R >>",
                        b"/Root 1 0 R /Encrypt 5 0 R /ID [<00> <00>] >>")


class ImportBlocker(object):
    """生成一个 sitecustomize.py：在解释器启动时屏蔽某些第三方导入。

    这是「依赖缺失」最忠实的注入方式 —— 不 patch 被测代码，只改变
    `import` 的可达性，等价于目标机没装该库。用 `sys.meta_path` 上的
    MetaPathFinder.find_spec（Python 3.12+ 已移除旧的 find_module 协议），
    并把已加载的同族模块从 sys.modules 摘掉。
    """

    def __init__(self, names, exc="injected absence"):
        self.names = list(names)
        self.exc = exc

    def source(self):
        return _BLOCKER_TEMPLATE.format(block=self.names, msg=self.exc)


_BLOCKER_TEMPLATE = """# generated by fault_inject.py -- simulate absent dependencies
import sys
import importlib.abc as _abc
_BLOCK = set({block!r})
_MSG = {msg!r}
class _Blocker(_abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in _BLOCK:
            raise ModuleNotFoundError(_MSG + ": " + name)
        return None
sys.meta_path.insert(0, _Blocker())
for _n in list(sys.modules):
    if _n.split(".")[0] in _BLOCK:
        del sys.modules[_n]
"""


# --------------------------------------------------------------------------
# 注入用例
# --------------------------------------------------------------------------
class Fault(object):
    """一条注入用例：注入 → 期望 → 实测记录。"""

    def __init__(self, fid, form, name, what, expect_exit, expect_status,
                 expect_note, setup=None, argv=None, env=None, cwd="scratch",
                 silent_note="", conforms=True, must_trace=()):
        self.fid = fid
        self.form = form
        self.name = name
        self.what = what
        self.expect_exit = expect_exit
        self.expect_status = expect_status     # "success"/"partial"/"failed"/"none"/"any"
        self.expect_note = expect_note         # 人读的"期望行为"
        self.setup = setup                     # fn(scratch) -> argv 覆盖/None
        self.argv = argv or []
        self.env = env or {}
        self.cwd = cwd
        self.silent_note = silent_note         # 已知盲区/留痕强度不足的说明
        # conforms=False：该注入**故意**不满足上面那对 (exit, status)，
        # 因为实测语义比文档更细；它仍然必须"不静默"，由 audit_pass 兜底。
        self.conforms_by_default = conforms
        # must_trace：该行必须出现的机器可读痕迹（检查名 / "uncertainty"）
        self.must_trace = tuple(must_trace or ())

    def run(self, skill_root, keep):
        sc = Scratch(skill_root, self.fid)
        record = {
            "id": self.fid, "form": self.form, "name": self.name,
            "injected": self.what, "expected": self.expect_note,
            "expect_exit": self.expect_exit, "expect_status": self.expect_status,
        }
        try:
            argv = list(self.argv)
            if self.setup:
                extra = self.setup(sc)
                if extra:
                    argv = list(extra) + argv
            cmd = [PY, sc.p("scripts", "main.py")] + argv
            env = dict(os.environ)
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            env.update(getattr(sc, "env_extra", {}) or {})
            env.update(self.env)
            cwd = sc.root if self.cwd == "scratch" else self.cwd
            t0 = time.time()
            proc = subprocess.run(cmd, cwd=cwd, env=env,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
            dt = time.time() - t0
            out = proc.stdout.decode("utf-8", "replace")
            record["command"] = " ".join(
                '"%s"' % c if " " in c else c for c in
                ["python", "scripts/main.py"] + argv)
            record["exit_code"] = proc.returncode
            record["seconds"] = round(dt, 2)
            record["stdout_tail"] = tail(out)
            record["artifact_dir"] = "<scratch>/out"
            if sc.details:
                record["probes"] = sc.details
            rp = os.path.join(sc.out, "result.json")
            if os.path.isfile(rp):
                res = load_json(rp)
                record["result_json"] = True
                record["status"] = res.get("status")
                record["top_level_keys"] = len(res)
                record["uncertainty"] = []
                for u in (res.get("uncertainty") or []):
                    if isinstance(u, dict):
                        record["uncertainty"].append(
                            (u.get("item"),
                             str(u.get("note") or "")[:180]))
                    else:
                        record["uncertainty"].append(("(string)", str(u)[:180]))
                record["uncertainty_count"] = len(record["uncertainty"])
                checks = (res.get("verification") or {}).get("checks")
                # 形态 1：summarize() 的卷总（dict，fails/warns 为列表）
                fails, warns = [], []
                if isinstance(checks, dict):
                    fails = [c for c in (checks.get("fails") or [])
                             if isinstance(c, dict)]
                    warns = [c for c in (checks.get("warns") or [])
                             if isinstance(c, dict)]
                # 形态 2：扁平检查列表（兼容未来形态）
                elif isinstance(checks, list):
                    rows = [c for c in checks if isinstance(c, dict)]
                    fails = [c for c in rows if c.get("level") == "fail"]
                    warns = [c for c in rows if c.get("level") == "warn"]
                record["fail_checks"] = sorted({c.get("check") for c in fails})
                record["warn_checks"] = sorted({c.get("check") for c in warns})
                record["check_count"] = len(fails) + len(warns)
                # 每条痕迹的原文（截断），供 FAULT-MATRIX 逐行引用
                record["fail_details"] = [
                    "%s: %s" % (c.get("check"), str(c.get("detail"))[:150])
                    for c in fails]
                record["warn_details"] = [
                    "%s: %s" % (c.get("check"), str(c.get("detail"))[:150])
                    for c in warns]
                sl = (res.get("verification") or {}).get("spec_lint")
                record["spec_lint_valid"] = (sl or {}).get("valid") \
                    if isinstance(sl, dict) else None
                record["sources"] = res.get("sources")
                record["artifact_roles"] = [a.get("role")
                                           for a in (res.get("artifacts") or [])]
            else:
                record["result_json"] = False
                record["status"] = None
                record["top_level_keys"] = 0
                record["uncertainty"] = []
                record["uncertainty_count"] = 0
                record["fail_checks"] = []
                record["warn_checks"] = []
                record["spec_lint_valid"] = None
                record["sources"] = None
                record["artifact_roles"] = []
        except Exception as exc:                      # pragma: no cover
            import traceback
            record["exit_code"] = None
            record["status"] = None
            record["harness_error"] = repr(exc)
            record["harness_traceback"] = traceback.format_exc()[-1200:]
        finally:
            if keep:
                record["scratch_kept"] = sc.root
            else:
                rm(sc.root)

        # ---- 判定：退出码 / status 是否落在期望内 ----
        ok_exit = (self.expect_exit == "any"
                   or record.get("exit_code") == self.expect_exit)
        got = record.get("status")
        if self.expect_status == "any":
            ok_status = True
        elif self.expect_status == "none":
            ok_status = (record.get("result_json") is False)
        else:
            ok_status = (got == self.expect_status)
        record["conforms"] = bool(ok_exit and ok_status)
        record["deviation"] = ""
        if not record["conforms"]:
            record["deviation"] = ("exit %r (expected %r); status %r "
                                   "(expected %r)"
                                   % (record.get("exit_code"), self.expect_exit,
                                      got, self.expect_status))
        # ---- 静默失败判据：期望是"出问题"，但退出码 0 + status success +
        #      没有任何 fail/warn/uncertainty 痕迹 ⇒ 静默 ----
        trace = ((record.get("fail_checks") or [])
                 + (record.get("warn_checks") or []))
        looks_clean = (record.get("exit_code") == 0
                       and got == "success"
                       and not trace
                       and record.get("uncertainty_count", 0) == 0)
        record["silent"] = bool(looks_clean)
        if self.silent_note:
            record["silent_note"] = self.silent_note
        # ---- 指定痕迹审计：must_trace 里的每一项都必须能被读到 ----
        if self.must_trace:
            seen = set(trace)
            unc = record.get("uncertainty") or []
            missing = []
            for want in self.must_trace:
                if want == "uncertainty":
                    if not unc:
                        missing.append("uncertainty")
                elif want not in seen:
                    missing.append(want)
            record["must_trace"] = list(self.must_trace)
            record["trace_missing"] = missing
            if missing:
                record["conforms"] = False
                record["deviation"] = ((record["deviation"] + " | ")
                                       if record["deviation"] else "") +                     "required trace absent: %s" % ", ".join(missing)
        # 故意偏离（conforms=False）的用例：判据是"必须留下机器可读痕迹"，
        # 否则才是真失败。
        if not self.conforms_by_default:
            left_trace = bool(trace
                              or record.get("uncertainty_count", 0)
                              or record.get("result_json") is False)
            record["audit_pass"] = left_trace and not looks_clean
            record["conforms"] = record["audit_pass"]
            if not record["conforms"]:
                record["deviation"] += (" | [audit] expected a non-silent "
                                        "trace; none found")
            else:
                record["deviation"] = ("[audit] documented exit/status pair "
                                       "differs by design; verdict is taken "
                                       "from the non-silent trace")
        return record


# ---- 各形态的 setup 函数 -------------------------------------------------
def _s_case_only(sc):
    return ["--case", sc.f("case.json"), "--out", sc.out]


def _s_case_out(sc):
    return ["--case", sc.f("case.json"), "--out", sc.out]


def setup_missing_source(sc):
    case = sc.base_case()
    case["sources"] = ["sources/absent-material.md"]
    return ["--case", sc.save_case(case), "--out", sc.out]


def setup_unreadable_source(sc):
    """来源文件存在但内容不是 UTF-8 文本：读取应失败并如实记录。"""
    write_bytes(sc.f("sources/binary-blob.md"), b"\xff\xfe\x00\x01rubbish")
    case = sc.base_case()
    case["sources"] = ["sources/binary-blob.md"]
    return ["--case", sc.save_case(case), "--out", sc.out]


def setup_case_not_object(sc):
    sc.break_case_json("[]\n")
    return ["--case", sc.f("case.json"), "--out", sc.out]


def setup_case_parse_error(sc):
    sc.break_case_json('{"case_id": "broken", "workorder": "x",\n')
    return ["--case", sc.f("case.json"), "--out", sc.out]


def setup_manifest_ghost(sc):
    return ["--case", sc.p("examples/case.json"),
            "--manifest", sc.f("ghost-entities.json"), "--out", sc.out]


def setup_manifest_parse_error(sc):
    write_text(sc.f("entities.json"), "not json at all\n")
    return ["--case", sc.p("examples/case.json"),
            "--manifest", sc.f("entities.json"), "--out", sc.out]


def setup_manifest_unknown_kind(sc):
    case = sc.base_case()
    case["manifest"]["relations"][0]["kind"] = "gibberish-relays"
    return ["--case", sc.save_case(case), "--out", sc.out]


def setup_manifest_dangling_endpoint(sc):
    """关系指向一个不存在的实体：结构上就不可能画对，必须被拦下。"""
    case = sc.base_case()
    case["manifest"]["relations"][3]["to"] = "E99"
    return ["--case", sc.save_case(case), "--out", sc.out]


def setup_manifest_direction_swapped(sc):
    """**语义**类注入：把激活关系 E4→E5 端点对调（E5→E4）。

    端点都存在、kind 也可映射 ⇒ CP1 结构门**结构上无法**判它错。
    本条用于把"结构可判 / 语义不可判"的边界摆到台面上：
    期望行为是**主流程仍然成功**，但本包必须诚实地把它归到
    ≠ "检查通过"（见 FAULT-MATRIX §4 的盲区表与 S1/S2 人工门）。
    """
    case = sc.base_case()
    case["manifest"]["relations"][3]["from"] = "E5"
    case["manifest"]["relations"][3]["to"] = "E4"
    return ["--case", sc.save_case(case), "--out", sc.out]


def setup_manifest_no_evidence(sc):
    """实体保留 source 但删掉 evidence：应降到 warn 级并仍可出图。"""
    case = sc.base_case()
    for e in case["manifest"]["entities"]:
        e.pop("evidence", None)
    return ["--case", sc.save_case(case), "--out", sc.out]


def setup_group_member_ghost(sc):
    case = sc.base_case()
    case["manifest"]["groups"][0]["members"].append("E99")
    return ["--case", sc.save_case(case), "--out", sc.out]


def setup_legend_orphan(sc):
    case = sc.base_case()
    case["manifest"]["legend"].append(
        {"id": "L9", "key": "inhibition",
         "label": "inhibition (orphan)", "arrow": "inhibition",
         "line": "solid", "source": "synthetic fault"})
    return ["--case", sc.save_case(case), "--out", sc.out]


def setup_template_parse_error(sc):
    case = sc.base_case()
    write_text(sc.p("assets", "relation-dict.json"), "{ broken json\n")
    return ["--case", sc.p("examples/case.json"), "--out", sc.out]


def setup_template_missing(sc):
    rm(sc.p("assets", "relation-dict.json"))
    return ["--case", sc.p("examples/case.json"), "--out", sc.out]


def _pdf_argv(sc, pdf_rel):
    case = sc.base_case()
    case["sources"] = [pdf_rel]
    return ["--case", sc.save_case(case),
            "--manifest", sc.f("entities.json"), "--out", sc.out]


def setup_pdf_encrypted(sc):
    """先断言"能抽"的基线，再注入加密件：拒绝必须是可分辨的降级。"""
    pdf_dir = os.path.join(sc.pkg, "examples", "sources")
    write_bytes(os.path.join(pdf_dir, "material-text.pdf"), make_text_pdf())
    write_bytes(os.path.join(pdf_dir, "material-enc.pdf"),
                make_encrypted_pdf())
    case = sc.base_case()
    case["sources"] = ["sources/material-text.pdf"]
    sc.save_case(case, "case.json")
    dump_json(sc.f("entities.json"), sc.base_case()["manifest"])
    r = subprocess.run([PY, sc.p("scripts", "pdftext.py"),
                        "--pdf", os.path.join(pdf_dir, "material-enc.pdf"),
                        "--out", sc.f("pdftext-out")],
                       cwd=sc.root, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    sc.details["pdftext_encrypted"] = {
        "exit": r.returncode,
        "tail": tail(r.stdout.decode("utf-8", "replace"), 4)}
    return _pdf_argv(sc, "sources/material-text.pdf")


def setup_pdf_scanned(sc):
    pdf_dir = os.path.join(sc.pkg, "examples", "sources")
    write_bytes(os.path.join(pdf_dir, "scan-empty.pdf"), make_empty_pdf())
    dump_json(sc.f("entities.json"), sc.base_case()["manifest"])
    case = sc.base_case()
    case["sources"] = ["sources/scan-empty.pdf"]
    sc.save_case(case)
    r = subprocess.run([PY, sc.p("scripts", "pdftext.py"),
                        "--pdf", os.path.join(pdf_dir, "scan-empty.pdf"),
                        "--out", sc.f("pdftext-scan")],
                       cwd=sc.root, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    sc.details["pdftext_scanned"] = {
        "exit": r.returncode,
        "tail": tail(r.stdout.decode("utf-8", "replace"), 4)}
    return ["--case", sc.f("case.json"),
            "--manifest", sc.f("entities.json"), "--out", sc.out]


def setup_no_pdf_lib(sc):
    pdf_dir = os.path.join(sc.pkg, "examples", "sources")
    write_bytes(os.path.join(pdf_dir, "material-flate.pdf"),
                make_text_pdf(compress=True))
    blocker = ImportBlocker(["fitz", "pypdf", "PyPDF2"])
    write_text(sc.f("sitecustomize.py"), blocker.source())
    dump_json(sc.f("entities.json"), sc.base_case()["manifest"])
    case = sc.base_case()
    case["sources"] = ["sources/material-flate.pdf"]
    sc.save_case(case)
    out = sc.f("pdftext-nolib")
    r = subprocess.run([PY, sc.p("scripts", "pdftext.py"),
                        "--pdf", os.path.join(pdf_dir, "material-flate.pdf"),
                        "--out", out],
                       cwd=sc.root,
                       env=dict(os.environ, PYTHONPATH=sc.fx,
                                PYTHONDONTWRITEBYTECODE="1"),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    sc.details["pdftext_no_thirdparty"] = {
        "exit": r.returncode,
        "tail": tail(r.stdout.decode("utf-8", "replace"), 4),
        "extracted": os.path.isfile(
            os.path.join(out, "material-flate.txt"))}
    return ["--case", sc.f("case.json"),
            "--manifest", sc.f("entities.json"), "--out", sc.out]


def setup_no_matplotlib(sc):
    blocker = ImportBlocker(["matplotlib"])
    write_text(sc.f("sitecustomize.py"), blocker.source())
    sc.env_extra["PYTHONPATH"] = sc.fx
    case = sc.base_case()
    return ["--case", sc.save_case(case), "--out", sc.out]


def setup_no_pil(sc):
    blocker = ImportBlocker(["PIL"])
    write_text(sc.f("sitecustomize.py"), blocker.source())
    sc.env_extra["PYTHONPATH"] = sc.fx
    case = sc.base_case()
    return ["--case", sc.save_case(case), "--out", sc.out]


def setup_cjk_font_absent(sc):
    """把 matplotlib 字体表压成"只有 DejaVu Sans"。

    这样 `textfont.resolve_font_stack()` 会走它自己的 Latin 回退分支
    （返回 cjk_ok=False），**不改被测代码**，却能真实复现"目标机没装
    CJK 字体"。注入物是一个 sitecustomize 包装，只在 scratch 副本里。
    """
    write_text(sc.f("sitecustomize.py"), _NO_CJK_FONT_SITE)
    sc.env_extra["PYTHONPATH"] = sc.fx
    case = sc.base_case()
    return ["--case", sc.save_case(case), "--out", sc.out]


def setup_render_crash(sc):
    """让 SVG 构建在运行期抛异常：必须写 failed 的 result.json，不丢工作。"""
    sc.edit_scripts(
        "scripts/svgbuilder.py",
        lambda s: s.replace(
            "def build_schematic_svg(",
            "def _injected_crash(*a, **k):\n"
            "    raise RuntimeError('injected render crash (fault-inject)')\n\n\n"
            "def build_schematic_svg(", 1) + _CRASH_SHIM)
    case = sc.base_case()
    return ["--case", sc.save_case(case), "--out", sc.out]


def setup_contract_missing_key(sc):
    case = sc.base_case()
    case["output_contract"] = {}
    return ["--case", sc.save_case(case), "--out", sc.out]


def setup_contract_shape_mismatch(sc):
    case = sc.base_case()
    case["output_contract"] = {
        "case_id": "number",           # 声明 number，实际是字符串 case_id
        "status": "array",             # 声明 array，实际是字符串
        "entities_relations": "string",  # 声明 string，实际给列表
        "deliverables": "array",
    }
    return ["--case", sc.save_case(case), "--out", sc.out]


def setup_contract_no_manifest(sc):
    """case 里没有 manifest/entities，工作区也没有 entities.json。"""
    case = sc.base_case()
    case.pop("manifest", None)
    case.pop("entities", None)
    case.pop("relations", None)
    return ["--case", sc.save_case(case), "--out", sc.out]


# 无 CJK 字体的注入：把 matplotlib 的字体表压成只有 DejaVu Sans。
# 只改"目标机的字体事实"，不碰被测脚本 —— textfont.py 会走它自己的
# Latin 回退分支并如实报 cjk_ok=False。
_NO_CJK_FONT_SITE = """# generated by fault_inject.py -- simulate a machine without CJK fonts
# 只把 CJK 家族从 matplotlib 的字体表里摘掉（保留真实 FontEntry 对象，
# 因此 matplotlib 自身仍能正常工作），等价于目标机没装中文字体。
try:
    from matplotlib import font_manager as _fm
    _CJK = ("yahei", "simhei", "simsun", "songti", "song", "kai", "ming",
            "hei", "noto sans cjk", "noto sans sc", "wenquanyi", "pingfang")
    _keep = []
    for _f in _fm.fontManager.ttflist:
        _n = (_f.name or "").lower()
        if any(_k in _n for _k in _CJK):
            continue
        _keep.append(_f)
    _fm.fontManager.ttflist = _keep
except Exception:
    pass
"""


# 注入后强制 build_schematic_svg 走坏路径（纯副本内改动，交付包不动）
_CRASH_SHIM = '''


_ORIG_BUILD = build_schematic_svg


def build_schematic_svg(manifest, layout, *a, **k):
    raise RuntimeError('injected render crash (fault-inject)')
'''


# --------------------------------------------------------------------------
# 用例注册表
# --------------------------------------------------------------------------
def registry():
    F = Fault
    return [
        # ---------------- 形态 1：输入损坏 ----------------
        F("D01", "input", "declared-source-missing",
          "case.sources 指向不存在的材料文件",
          0, "success",
          "exit 0 / success，但 sources 少一项、uncertainty 出现 'unresolved "
          "source materials'（降级必须留痕，不是静默）",
          setup=setup_missing_source, must_trace=("uncertainty",)),
        F("D02", "input", "declared-source-unreadable",
          "材料文件存在但内容非 UTF-8（二进制垃圾）",
          0, "success",
          "exit 0；图仍能出。**实测语义比「读不到就降级」更细**：pipeline "
          "只对 sources 做存在性解析，材料字节由 Agent 侧读取，且在 case "
          "已内嵌 manifest 时并不被消费 ⇒ 本注入必须「非静默」才算合格，"
          "判据取 audit 分支",
          setup=setup_unreadable_source, conforms=False,
          silent_note="留痕强度不足：材料内容不可读时 pipeline 自身没有痕迹"
                      "（不 fail/warn/uncertainty），只有 Agent 侧真的去读"
                      "才会发现 ⇒ 已列入 FAULT-MATRIX §4 盲区表，缓解手段是 "
                      "S1 的「逐份读实际文件」人工门"),
        F("D03", "input", "case-not-a-json-object",
          "case.json 是合法 JSON 但顶层是数组",
          2, "none",
          "exit 2 + FATAL，且**不写产物**（宁缺毋滥）",
          setup=setup_case_not_object),
        F("D04", "input", "case-json-parse-error",
          "case.json 被截断成非法 JSON",
          2, "none",
          "exit 2 + FATAL cannot parse，不写产物",
          setup=setup_case_parse_error),
        F("D05", "input", "case-path-missing",
          "--case 指向不存在的路径",
          2, "none",
          "exit 2 + FATAL case not found，不写产物",
          setup=lambda sc: ["--case", sc.f("no-such-case.json"),
                            "--out", sc.out]),
        F("D06", "input", "manifest-ghost-file",
          "--manifest 指向不存在的文件",
          1, "failed",
          "exit 1 + status=failed + fails=[pipeline] + uncertainty "
          "记明原因（清单是绘图唯一依据：缺了就不画，但工作不丢失）",
          setup=setup_manifest_ghost, must_trace=("pipeline",)),

        # ---------------- 形态 2：模板 / 夹具损坏 ----------------
        F("D07", "template", "manifest-unparseable",
          "--manifest 文件不是 JSON",
          1, "failed",
          "exit 1 + status=failed + fails=[pipeline]，result.json 仍写出",
          setup=setup_manifest_parse_error, must_trace=("pipeline",)),
        F("D08", "template", "manifest-unknown-relation-kind",
          "关系 kind 改成不在词表里的 'gibberish-relays'",
          1, "partial",
          "exit 1 + partial + spec_lint.valid=false + fail 明细可查（不静默）",
          setup=setup_manifest_unknown_kind,
          must_trace=("spec_lint.spec.relation_kind",)),
        F("D09", "template", "manifest-dangling-endpoint",
          "关系 to 指向不存在的实体 E99（结构不可能画对）",
          1, "partial",
          "exit 1 + partial + spec.relation_to fail（结构错误必须被拦下）",
          setup=setup_manifest_dangling_endpoint,
          must_trace=("spec_lint.spec.relation_to",)),
        F("D09b", "template", "manifest-direction-swapped",
          "把激活关系 E4→E5 的端点对调成 E5→E4（语义错，结构合法）",
          0, "success",
          "**期望就是 exit 0 / success**：端点存在、kind 可映射 ⇒ CP1 结构"
          "门无法判它错。本条属于「结构可判 / 语义不可判」的边界，"
          "其合格判据是 audit 分支（必须留下可复核的非静默痕迹）",
          setup=setup_manifest_direction_swapped, conforms=False,
          silent_note="语义盲区（已知且不可用结构门消除）：方向对调后 "
                      "spec_lint 全 ok，机器痕迹为 0 ⇒ 只能靠 S1/S2 的"
                      "「回材料核对 from/to」人工门 + data-* 溯源属性复核"),
        F("D10", "template", "manifest-evidence-stripped",
          "实体保留 source、删掉全部 evidence",
          0, "success",
          "exit 0 + success，但 spec.traceability 必须出现 warn（降级可见）",
          setup=setup_manifest_no_evidence,
          must_trace=("traceability.entities",)),
        F("D11", "template", "group-member-ghost",
          "分组里塞进不存在的实体 E99",
          1, "partial",
          "exit 1 + partial，spec.group_member fail 可查",
          setup=setup_group_member_ghost,
          must_trace=("spec_lint.spec.group_member",)),
        F("D12", "template", "legend-orphan-item",
          "图例多加一条图面没有的 inhibition 条目",
          0, "success",
          "exit 0；孤儿项应为 warn（可见但不阻断），明细可查",
          setup=setup_legend_orphan),
        F("D13", "template", "relation-dict-corrupted",
          "assets/relation-dict.json 被写成非法 JSON",
          0, "success",
          "字典损坏必须**不能**被当成「检查通过」：实测走 main.py 内联 "
          "lint 的读取路径会抛异常并被 try 兜住（见实测 stdout）⇒ "
          "判据取 audit 分支：要么非零退出，要么至少留下一条非静默痕迹",
          setup=setup_template_parse_error, must_trace=("spec_lint.corpus",),
          silent_note="已修（纯增量）：原先字典损坏会让 json.load 抛 "
                      "JSONDecodeError 直接崩掉、连 result.json 都不写，"
                      "现在被 try 兜住并落成 spec_lint.corpus 的 warn；"
                      "注意它仍是 warn 而不是 fail —— 图本身没画错，"
                      "失效的是「一致性检查器」而不是「产物」"),
        F("D14", "template", "relation-dict-missing",
          "assets/relation-dict.json 被整个删掉",
          0, "success",
          "exit 0；同上，字典缺失不阻断主流程 ⇒ 与 D13 同一条盲区",
          setup=setup_template_missing, must_trace=("spec_lint.corpus",),
          silent_note="与 D13 同一处置路径（字典不存在 ⇒ 同一条 warn），"
                      "区别是这里没有异常可吞，纯走「文件缺失」分支"),

        # ---------------- 形态 3：依赖损坏 ----------------
        F("D15", "dependency", "pdf-encrypted",
          "材料换成声明 /Encrypt 的 PDF",
          0, "success",
          "主流程仍 exit 0（材料不可用要如实报告而非伪造）；"
          "pdftext.py 对加密件必须给出**可分辨的非零/明确提示**",
          setup=setup_pdf_encrypted),
        F("D16", "dependency", "pdf-scanned-no-text",
          "材料换成内容流为空的 PDF（扫描件）",
          0, "success",
          "同上：主流程 exit 0，抽取器给出明确空文本结论，不伪造",
          setup=setup_pdf_scanned),
        F("D17", "dependency", "pdf-libs-absent",
          "屏蔽 fitz/pypdf/PyPDF2（PYTHONPATH 注入 ImportBlocker）",
          0, "success",
          "pdftext.py 走 stdlib 回退仍能抽出文本；backend 如实记录",
          setup=setup_no_pdf_lib),
        F("D18", "dependency", "matplotlib-absent",
          "屏蔽 matplotlib 的导入",
          1, "failed",
          "exit 1 + status=failed + fails=[pipeline]，产物目录保留已有文件",
          setup=setup_no_matplotlib, must_trace=("pipeline",)),
        F("D19", "dependency", "pillow-absent",
          "屏蔽 PIL 的导入（matplotlib 的 colors 模块在 import 期就要 PIL）",
          1, "failed",
          "exit 1 + status=failed + fails=[pipeline]：Pillow 缺失会让 "
          "matplotlib 本身 import 不进来，所以它与 D18 同一条分支；"
          "关键是**必须留下 result.json**，而不是裸 traceback",
          setup=setup_no_pil, must_trace=("pipeline",)),
        F("D20", "dependency", "cjk-font-absent",
          "字体探针替身：候选 CJK 族全部解析不到",
          0, "success",
          "exit 0；font.cjk 记为 warn/False 并进 uncertainty（PNG 可能缺字，"
          "SVG 文字仍在）",
          setup=setup_cjk_font_absent),
        F("D21", "dependency", "render-crash",
          "SVG 构建在运行期抛 RuntimeError（副本内注入）",
          1, "failed",
          "exit 1 + status=failed + fails=[pipeline]，且 result.json 必须写出",
          setup=setup_render_crash, must_trace=("pipeline",)),

        # ---------------- 形态 4：契约损坏 ----------------
        F("D22", "contract", "contract-keys-absent",
          "case.json 完全不声明 output_contract",
          0, "success",
          "exit 0；result.json 顶层仍覆盖 OUTPUT_CONTRACT §1 的 21 个字段",
          setup=setup_contract_missing_key),
        F("D23", "contract", "contract-shape-mismatch",
          "output_contract 声明的类型与实际值形状不符",
          0, "any",
          "回显按**声明类型**补齐（四形态），G5 校验器对形状错误应报 INVALID；"
          "主流程不因契约瑕疵丢产物",
          setup=setup_contract_shape_mismatch),
        F("D24", "contract", "no-manifest-anywhere",
          "case 无 manifest/entities，工作区也无 entities.json",
          1, "failed",
          "exit 1 + status=failed + fails=[pipeline]（无依据不画）",
          setup=setup_contract_no_manifest, must_trace=("pipeline",)),
    ]


# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------
def in_package(path, skill_root):
    """True if `path` 落在技能包内部（用于拒绝把产物写进交付包）。"""
    p = os.path.abspath(path)
    r = os.path.abspath(skill_root)
    return p == r or p.startswith(r + os.sep)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="fault_inject",
        description="失败注入与恢复演练：把四形态故障逐个注入并真实跑主流程")
    ap.add_argument("--skill-root", default=DEFAULT_ROOT,
                    help="技能根目录（默认：本脚本的上一级）")
    ap.add_argument("--out", default=None,
                    help="产物目录（默认：系统临时目录下的新目录；"
                         "**不得**指向技能包内部）")
    ap.add_argument("--form", default="all",
                    choices=["all", "input", "template", "dependency",
                             "contract"],
                    help="只跑某一形态（默认 all）")
    ap.add_argument("--only", default=None,
                    help="逗号分隔的用例 id，例如 D07,D21")
    ap.add_argument("--json", action="store_true",
                    help="把矩阵同时写成 JSON（默认总是写 fault-matrix.json）")
    ap.add_argument("--quiet", action="store_true", help="不打文本表")
    ap.add_argument("--keep", action="store_true",
                    help="保留每个用例的 scratch 目录（调试用）")
    ap.add_argument("--list", action="store_true", help="只列用例，不运行")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.skill_root)
    if not os.path.isdir(root) or not os.path.isfile(
            os.path.join(root, "scripts", "main.py")):
        print("FATAL: %s is not a skill root (scripts/main.py missing)" % root)
        return 2

    faults = registry()
    if args.list:
        for f in faults:
            print("%-4s %-11s %-30s exit=%s status=%s"
                  % (f.fid, f.form, f.name, f.expect_exit, f.expect_status))
        return 0

    if args.form != "all":
        faults = [f for f in faults if f.form == args.form]
    if args.only:
        want = {x.strip() for x in args.only.split(",") if x.strip()}
        faults = [f for f in faults if f.fid in want]
    if not faults:
        print("FATAL: no fault selected")
        return 2

    out_dir = os.path.abspath(args.out) if args.out else tempfile.mkdtemp(
        prefix="sse-fault-matrix-")
    if in_package(out_dir, root):
        print("FATAL: --out must not be inside the skill package (%s); "
              "artifacts and __pycache__ would pollute the delivered resource "
              "set" % root)
        return 2
    os.makedirs(out_dir, exist_ok=True)

    print("fault-inject: skill-root=%s" % root)
    print("fault-inject: out=%s" % out_dir)
    print("fault-inject: %d case(s)\n" % len(faults))

    records = []
    for f in faults:
        print("=== [%s] %s (%s) ===" % (f.fid, f.name, f.form), flush=True)
        print("    inject : %s" % f.what)
        rec = f.run(root, keep=args.keep)
        records.append(rec)
        if rec.get("command"):
            print("    command: %s" % rec["command"])
        print("    expect : exit=%s status=%s | %s"
              % (f.expect_exit, f.expect_status, f.expect_note))
        print("    actual : exit=%s status=%s result.json=%s keys=%s "
              "uncertainty=%s" % (rec.get("exit_code"), rec.get("status"),
                                  rec.get("result_json"),
                                  rec.get("top_level_keys"),
                                  rec.get("uncertainty_count")))
        if rec.get("fail_checks"):
            print("    fails  : %s" % ", ".join(rec["fail_checks"]))
        if rec.get("warn_checks"):
            print("    warns  : %s" % ", ".join(rec["warn_checks"]))
        if rec.get("uncertainty"):
            for item, note in rec["uncertainty"][:3]:
                print("    uncert : %s -- %s" % (item, note))
        print("    verdict: %s%s"
              % ("CONFORMS" if rec.get("conforms") else "DEVIATES",
                 "  [silent]" if rec.get("silent") else ""))
        if rec.get("deviation"):
            print("    detail : %s" % rec["deviation"])
        if rec.get("stdout_tail"):
            print("    stdout : %s" % " | ".join(rec["stdout_tail"][-3:]))
        print("")

    bad = [r for r in records if not r.get("conforms")]
    silent = [r for r in records if r.get("silent")]
    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "skill_root": root,
        "python": sys.version.split()[0],
        "total": len(records),
        "conforming": len(records) - len(bad),
        "deviating": [r["id"] for r in bad],
        "silent_failures": [r["id"] for r in silent],
        "forms": {form: sum(1 for r in records if r["form"] == form)
                  for form in sorted({r["form"] for r in records})},
        "records": records,
    }
    jp = os.path.join(out_dir, "fault-matrix.json")
    dump_json(jp, summary)
    print("=" * 72)
    print("fault-inject: %d/%d conform to the documented expectation"
          % (summary["conforming"], summary["total"]))
    if bad:
        print("fault-inject: DEVIATIONS: %s"
              % ", ".join("%s(%s)" % (r["id"], r.get("deviation") or "")
                          for r in bad))
    if silent:
        print("fault-inject: silent-failure candidates: %s"
              % ", ".join(r["id"] for r in silent))
    print("fault-inject: matrix written to %s" % jp)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
