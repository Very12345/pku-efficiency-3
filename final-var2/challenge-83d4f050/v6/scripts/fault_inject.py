#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fault_inject.py — 失败注入与恢复演练器（四形态：输入 / 模板 / 依赖 / 契约）

它做什么
--------
把技能复制到**包外**临时目录，对副本只施加**一处**故障，然后运行**真实主流程**
（`scripts/main.py`）或**真实校验 CLI**（`check_contract.py`），记录：

* 退出码（0/2/3/1 …），
* `result.json` 的 `status`、`gates`、`uncertainty`、产物清单，
* 该故障是**显式暴露**（有非零退出码 / 非 success 状态 / uncertainty 留痕）
  还是被**静默吞掉**（exit 0 + status=success + 无任何失败痕迹）。

对定义了"修复动作"的场景，还会在同一临时环境里**再跑一次修复后的主流程**，
用实测证明失败可恢复（"恢复演练"）。

为什么必须这样做
----------------
可靠体验维度只靠文档承诺无法验证；本脚本把"文档说会降级"变成"跑出来确实是这个退出码、
status 与 uncertainty 字段"。`references/FAULT-MATRIX.md` 的每一行都由本脚本产出的
报告填写，**不允许手写数字**。

用法（务必在包外跑；脚本自身不会往技能目录写任何文件）
----------------------------------------------------
    export SKILL_DIR=/skills/weekly-skill
    # 1) 全量演练（约 1 分钟）→ 报告 JSON + Markdown 表格
    python3 "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/fault-out
    # 2) 只跑某几类 / 某几个场景
    python3 "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/fault-out --family 依赖
    python3 "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/fault-out --only dep-01-matplotlib-import
    # 3) 换待测技能目录（默认 = 本脚本所在技能根）
    python3 "$SKILL_DIR/scripts/fault_inject.py" --skill /path/to/copy --out /tmp/fault-out

退出码：0 = 所有场景行为与期望一致；1 = 有场景与期望不符（看报告）；
        4 = 场景自身无法运行（例如 --skill 指向的目录没有 scripts/main.py）。
本脚本只依赖标准库，不需要 matplotlib。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_REL = os.path.join("scripts", "main.py")
CHECK_REL = os.path.join("scripts", "check_contract.py")
RUN_TIMEOUT = 300

FAMILIES = ("输入", "模板", "依赖", "契约")

# --------------------------------------------------------------------------
# 运行时工具
# --------------------------------------------------------------------------


def _copy_skill(src, dst):
    """Copy the skill tree without bytecode caches (they would break H1/H2)."""
    def ignore(_d, names):
        return [n for n in names if n == "__pycache__" or n.endswith(".pyc")]
    shutil.copytree(src, dst, ignore=ignore)


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
    return path


def _write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


def _stub_dir(work, name, files):
    """Create a PYTHONPATH stub directory (used by the 依赖 family)."""
    d = os.path.join(work, "stubs", name)
    for rel, text in files.items():
        _write_text(os.path.join(d, rel), text)
    return d


def _run(script_abs, argv, cwd, env_extra=None, python=None):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"      # 绝不在副本里留 __pycache__
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("TASK_OUTPUT", None)
    if env_extra:
        env.update(env_extra)
    cmd = [python or sys.executable, script_abs] + [str(a) for a in argv]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=RUN_TIMEOUT)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        rc, out, err = None, b"", ("TIMEOUT after %ds" % RUN_TIMEOUT).encode()
    return {
        "cmd": cmd,
        "exit": rc,
        "stdout": out.decode("utf-8", "replace"),
        "stderr": err.decode("utf-8", "replace"),
        "seconds": round(time.time() - t0, 2),
    }


def _parse_summary(stdout):
    for line in stdout.splitlines():
        if line.startswith("SUMMARY "):
            try:
                return json.loads(line[len("SUMMARY "):])
            except Exception:
                return None
    return None


def _observe(res, out_dir):
    """Turn one raw run into the observation record used by the matrix."""
    obs = {
        "exit": res["exit"],
        "seconds": res["seconds"],
        "summary": _parse_summary(res.get("stdout", "")),
        "stderr_tail": "\n".join((res.get("stderr") or "").strip().splitlines()[-3:]),
        "stdout_tail": "\n".join((res.get("stdout") or "").strip().splitlines()[-3:]),
        "result": None,
        "artifacts": ([f for f in sorted(os.listdir(out_dir)) if f != "skill"]
                      if os.path.isdir(out_dir) else []),
        "status": None,
        "gates": None,
        "uncertainty": [],
        "stdout_excerpt": (res.get("stdout") or "")[:4000],
    }
    rp = os.path.join(out_dir, "result.json")
    if os.path.isfile(rp):
        try:
            with open(rp, "r", encoding="utf-8") as fh:
                rj = json.load(fh)
            obs["result"] = rj
            obs["status"] = rj.get("status")
            g = rj.get("gates") or {}
            obs["gates"] = ("%d/%d" % (sum(1 for v in g.values() if v.get("pass")), len(g))
                            if g else "{}")
            for item in rj.get("uncertainty") or []:
                if isinstance(item, dict):
                    obs["uncertainty"].append("%s | %s | %s" % (
                        item.get("item", ""), item.get("reason", ""), item.get("mitigation", "")))
                else:
                    obs["uncertainty"].append(str(item))
            obs["reason"] = rj.get("reason")
            obs["top_keys"] = sorted(rj.keys())
        except Exception as ex:                      # pragma: no cover - defensive
            obs["result_error"] = "%s: %s" % (type(ex).__name__, ex)
    return obs


def _haystack(obs):
    ds = ["exit=%s" % obs["exit"], "status=%s" % obs["status"]]
    ds += obs["uncertainty"]
    ds += [(obs["result"] or {}).get("reason") or ""]
    ds += (obs.get("stderr_tail") or "").splitlines()
    ds += (obs.get("stdout_excerpt") or "").splitlines()
    sc = (obs["result"] or {}).get("self_check") or {}
    ds += [str(w) for w in (sc.get("warnings") or [])]
    ds += [str(f) for f in (sc.get("failures") or [])]
    return chr(10).join(str(d) for d in ds)


PROBE_ORPHAN_EDGE = "_probe_orphan_edge.py"
PROBE_PALETTE = "_probe_palette.py"
PROBE_CP1 = "_probe_cp1.py"

PROBE_SCRIPTS = {
    PROBE_ORPHAN_EDGE: '''# -*- coding: utf-8 -*-
"""计数 normalize_model() 会丢掉的边（端点不存在）。"""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "skill", "scripts"))
from model import normalize_model, normalize_entities, load_json  # noqa: E402

raw = load_json(sys.argv[1])
ids = {e["id"] for e in normalize_entities(raw.get("entities"))}
kept = normalize_model(raw)["edges"]
want = [r for r in (raw.get("edges") or [])
        if isinstance(r, dict) and (str(r.get("from", "")) not in ids
                                    or str(r.get("to", "")) not in ids)]
print(json.dumps({"raw_edges": len(raw.get("edges") or []),
                  "kept_edges": len(kept),
                  "dropped_edges": len(want),
                  "dropped": [{"from": r.get("from"), "to": r.get("to")} for r in want]},
                 ensure_ascii=False))
''',
    PROBE_PALETTE: '''# -*- coding: utf-8 -*-
"""从包内模块读调色板是否真的加载（不依赖外部路径字符串）。"""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "skill", "scripts"))
import model  # noqa: E402

obs = {"palette_loaded": True, "detail": "assets/palettes.json 已加载"}
fn = getattr(model, "palette_load_status", None)
if callable(fn):
    obs = fn()
print(json.dumps(obs, ensure_ascii=False))
''',
    PROBE_CP1: '''# -*- coding: utf-8 -*-
"""复算 CP1.2（任务说明可用）的判定结果，用于观测"被丢弃的 warn"。"""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "skill", "scripts"))
import importlib.util  # noqa: E402
import validate_figure as vf  # noqa: E402


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


here = os.path.dirname(os.path.abspath(__file__))
main_py = os.path.join(here, "skill", "scripts", "main.py")
mod = load_module(main_py, "skill_main_probe")
case_path = sys.argv[1] if len(sys.argv) > 1 else ""
case = json.load(open(case_path, encoding="utf-8")) if case_path else {}
task_text = mod.read_task_text(None, case, os.path.dirname(os.path.abspath(case_path)))
check = vf._check("CP1.2", "task 说明可用",
                  "pass" if task_text or case.get("task") else "warn",
                  "%d chars" % len(task_text) if task_text else "无 task 文本")
print(json.dumps({"cp1_2_result": check["result"], "cp1_2_detail": check["detail"]},
                 ensure_ascii=False))
''',
}


# --------------------------------------------------------------------------
# 场景登记
# --------------------------------------------------------------------------

SCENARIOS = []


def scenario(sid, family, title, expect_text, inject, check=None,
             success_ok=False, recover=None, recover_expect=None, note="",
             probe_script=None):
    """Register one fault scenario.

    inject(ctx) -> dict(argv=[...], cwd=..., env={...}, what="...")
    check(obs, ctx) -> (bool, detail)   optional extra assertion
    recover(ctx) -> dict(argv=..., env=...)   optional repair run
    probe_script -> relative path of a probe to run *against the same copy*
                   after the main run (used to observe silent loss precisely)
    """
    SCENARIOS.append({
        "id": sid, "family": family, "title": title, "expect": expect_text,
        "inject": inject, "check": check, "success_ok": success_ok,
        "recover": recover, "recover_expect": recover_expect, "note": note,
        "probe_script": probe_script,
    })


# ---------------- 输入形态 ----------------

def _example_case(ctx):
    return os.path.join(ctx["copy"], "examples", "case.json")


def _example_model(ctx):
    return os.path.join(ctx["copy"], "examples", "model.example.json")


def _example_materials(ctx):
    return os.path.join(ctx["copy"], "examples", "materials")


def _standard(ctx, case=None, out=None, extra=None, model=True):
    argv = ["--case", case or _example_case(ctx)]
    if model:
        argv += ["--model-file", _example_model(ctx)]
    argv += ["--out", out or ctx["out"]]
    if extra:
        argv += list(extra)
    return {"argv": argv, "cwd": ctx["work"]}


def _in_missing_case(ctx):
    return {"argv": ["--case", os.path.join(ctx["work"], "no-such-case.json"),
                     "--model-file", _example_model(ctx), "--out", ctx["out"]],
            "cwd": ctx["work"]}


scenario("in-01-missing-case-file", "输入",
         "case.json 路径不存在",
         "非零退出且**不产出** result.json（入口显式拒绝，不是空图）",
         _in_missing_case,
         check=lambda o, c: (o["exit"] not in (0, None) and o["status"] is None,
                             "exit=%s；产物=%s" % (o["exit"], o["artifacts"])))


def _in_empty_material_dir(ctx):
    case = _write_json(os.path.join(ctx["work"], "case-empty-materials.json"), {
        "case_id": "fault-empty-materials",
        "title": "注入：材料目录为空",
        "task": "注入场景：材料目录为空。",
        "materials": [],
        "output_contract": {"probe_str": "x"},
    })
    empty = os.path.join(ctx["work"], "empty-materials")
    os.makedirs(empty, exist_ok=True)
    return {"argv": ["--case", case, "--materials-dir", empty, "--out", ctx["out"]],
            "cwd": ctx["work"]}


scenario("in-02-empty-material-dir", "输入",
         "材料目录为空（case 未给 materials）",
         "exit 3 / status=failed，uncertainty 写明材料缺失并给补救路径",
         _in_empty_material_dir,
         check=lambda o, c: (o["exit"] == 3 and o["status"] == "failed"
                             and any("材料" in u or "绘图流程" in u for u in o["uncertainty"]),
                             "exit=%s status=%s uncertainty=%d 条" %
                             (o["exit"], o["status"], len(o["uncertainty"]))),
         recover=lambda ctx: _standard(ctx, model=True),
         recover_expect="修好材料后：exit 0 / status=success")


def _in_malformed_case(ctx):
    case = _write_text(os.path.join(ctx["work"], "case-broken.json"),
                       '{"case_id": "fault-malformed", "materials": [,,, }\n')
    return {"argv": ["--case", case, "--model-file", _example_model(ctx),
                     "--out", ctx["out"]], "cwd": ctx["work"]}


scenario("in-03-malformed-case-json", "输入",
         "case.json 不是合法 JSON",
         "非零退出（入口解析失败即停止）",
         _in_malformed_case,
         check=lambda o, c: (o["exit"] not in (0, None) and o["status"] is None,
                             "exit=%s；stderr=%r" % (o["exit"], o["stderr_tail"][:80])),
         note="实测为**非优雅退出**（JSONDecodeError 栈），不留 result.json；"
              "属可接受但可改进项，见 FAULT-MATRIX.md §4")


def _in_no_relations(ctx):
    mat = _write_text(os.path.join(ctx["work"], "material-entities-only.md"), NO_RELATION_MATERIAL)
    case = _write_json(os.path.join(ctx["work"], "case-entities-only.json"), {
        "case_id": "fault-entities-only",
        "title": "注入：材料只有实体、没有关系",
        "task": "注入场景：材料只有实体表、没有关系节。",
        "materials": [],
        "output_contract": {"probe_str": "x"},
    })
    return {"argv": ["--case", case, "--materials-dir", os.path.dirname(mat),
                     "--out", ctx["out"]], "cwd": ctx["work"]}


scenario("in-04-material-without-relations", "输入",
         "材料只有实体表、没有关系节（草稿路径）",
         "不报成功：草稿未人工核验 ⇒ exit 2 / status=partial，且 edges 为空要留痕",
         _in_no_relations,
         check=lambda o, c: (o["exit"] == 2 and o["status"] == "partial"
                             and o["uncertainty"],
                             "exit=%s status=%s uncertainty=%d 条 edges=%s" % (
                                 o["exit"], o["status"], len(o["uncertainty"]),
                                 (o["result"] or {}).get("scientific_content", {})
                                 .get("counts", {}).get("edges"))),
         recover=lambda ctx: _standard(ctx),
         recover_expect="改走已核验规格：exit 0 / status=success")


def _in_unknown_type(ctx):
    model = _write_json(os.path.join(ctx["work"], "model-banana.json"), {
        "case_id": "fault-banana-type",
        "title": "注入：枚举外实体类型",
        "entities": [
            {"id": "e1", "name": "X", "type": "banana", "compartment": "cytoplasm",
             "source": [{"ref": "m", "kind": "material", "line": 1}]},
            {"id": "e2", "name": "Y", "type": "protein", "compartment": "cytoplasm",
             "source": [{"ref": "m", "kind": "material", "line": 2}]},
        ],
        "edges": [{"id": "r1", "from": "e1", "to": "e2", "type": "activation",
                   "evidence": "strong",
                   "source": [{"ref": "m", "kind": "material", "line": 3}]}],
        "extraction": {"method": "manual", "verified_by_agent": True},
    })
    return {"argv": ["--case", _example_case(ctx), "--model-file", model,
                     "--out", ctx["out"]], "cwd": ctx["work"]}


scenario("in-05-unknown-entity-type", "输入",
         "机制规格里出现枚举外类型（type=banana，规格其余部分完好）",
         "schema 门阻断：exit 3 / status=failed / reason 指向 schema（**不得**被静默改写成 other）",
         _in_unknown_type,
         check=lambda o, c: (o["exit"] == 3 and o["status"] == "failed"
                             and "schema" in _haystack(o),
                             "exit=%s status=%s reason=%r" %
                             (o["exit"], o["status"], (o["result"] or {}).get("reason"))),
         note="规格本身可渲染（2 实体 1 边），所以 failed 只可能来自类型枚举 —— "
              "用来验证'raw 规格校验'不是空转",
         recover=lambda ctx: _standard(ctx),
         recover_expect="把类型改回枚举内：exit 0 / status=success")


def _in_binary_material(ctx):
    d = os.path.join(ctx["work"], "binary-material")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "material.md"), "wb") as fh:
        fh.write(b"\xff\xfe\x00\x01 \x80\x81 not utf-8 \x00\x02" * 8)
    case = _write_json(os.path.join(ctx["work"], "case-binary.json"), {
        "case_id": "fault-binary-material", "title": "注入：材料不是合法 UTF-8",
        "task": "注入场景：材料不是合法 UTF-8。",
        "materials": [], "output_contract": {"probe_str": "x"},
    })
    return {"argv": ["--case", case, "--materials-dir", d, "--out", ctx["out"]],
            "cwd": ctx["work"]}


scenario("in-06-non-utf8-material", "输入",
         "材料文件不是合法 UTF-8（模拟乱码/二进制混入）",
         "不崩溃：解码失败要被替换处理并继续，若有降级必须留痕",
         _in_binary_material,
         check=lambda o, c: (o["exit"] != 1 or o["status"] is not None,
                             "exit=%s status=%s" % (o["exit"], o["status"])),
         note="草稿路径 exit 2 / partial（未核验）为正确行为；只要不是未捕获异常即可")


def _in_missing_task(ctx):
    case = _write_json(os.path.join(ctx["work"], "case-no-task.json"), {
        "case_id": "fault-no-task",
        "title": "注入：没有任务说明",
        "materials": [],
        "output_contract": {"probe_str": "x"},
    })
    ctx["probe_arg"] = case
    return {"argv": ["--case", case, "--materials-dir", _example_materials(ctx),
                     "--model-file", _example_model(ctx), "--out", ctx["out"]],
            "cwd": ctx["work"]}


scenario("in-07-missing-task-text", "输入",
         "case.json 没有 task、也没有 task.md（CP1.2 判 warn）",
         "降级必须留痕：uncertainty / self_check 要有记录（**实测见 §4 G3**）",
         _in_missing_task,
         check=lambda o, c: (_has_any(o, ("task", "任务", "说明")) or _cp1_traced(o),
                             "exit=%s status=%s 痕迹=%s；CP1.2 复算=%s" % (
                                 o["exit"], o["status"], _signal_names(o),
                                 _cp1_result(o))),
         probe_script=PROBE_CP1,
         note="未修复前实测为**静默降级**（CP1.2 判 warn 但成功路径不落痕）；G3 修复后必须留痕")


def _in_orphan_edge(ctx):
    model = _write_json(os.path.join(ctx["work"], "model-orphan-edge.json"), {
        "case_id": "fault-orphan-edge",
        "title": "注入：边的端点不存在",
        "entities": [
            {"id": "e1", "name": "A", "type": "protein", "compartment": "cytoplasm",
             "source": [{"ref": "m", "kind": "material", "line": 1}]},
            {"id": "e2", "name": "B", "type": "protein", "compartment": "cytoplasm",
             "source": [{"ref": "m", "kind": "material", "line": 2}]},
        ],
        "edges": [
            {"id": "r1", "from": "e1", "to": "e2", "type": "activation",
             "evidence": "strong",
             "source": [{"ref": "m", "kind": "material", "line": 3}]},
            {"id": "r2", "from": "e2", "to": "e999", "type": "activation",
             "evidence": "strong",
             "source": [{"ref": "m", "kind": "material", "line": 4}]},
        ],
        "extraction": {"method": "manual", "verified_by_agent": True},
    })
    ctx["probe_arg"] = model
    return {"argv": ["--case", _example_case(ctx), "--model-file", model,
                     "--out", ctx["out"]], "cwd": ctx["work"]}


scenario("in-08-orphan-edge-endpoint", "输入",
         "边指向不存在的实体 id（e999）",
         "不得静默丢边：丢弃的边必须留痕（uncertainty / reason / self_check），**实测见 §4 G1**",
         _in_orphan_edge,
         check=lambda o, c: (_orphan_traced(o),
                             "exit=%s status=%s 痕迹=%s reason=%r" % (
                                 o["exit"], o["status"], _signal_names(o),
                                 (o["result"] or {}).get("reason"))),
         note="未修复前实测为**静默丢边**（exit 0 / success / 无痕）；G1 修复后必须留痕",
         probe_script=PROBE_ORPHAN_EDGE)


# ---------------- 模板 / 资产形态 ----------------

def _tpl_delete(ctx, rel):
    p = os.path.join(ctx["copy"], rel)
    if os.path.isfile(p):
        os.remove(p)
    return p


def _tpl_palettes(ctx):
    _tpl_delete(ctx, os.path.join("assets", "palettes.json"))
    return _standard(ctx)


scenario("tpl-01-palettes-missing", "模板",
         "删掉 assets/palettes.json（配色资产缺失）",
         "回退到内置默认调色板**并留痕**（SKILL.md D18 / failure-modes F07 的承诺，实测见 §4 G2）",
         _tpl_palettes,
         check=lambda o, c: (_palette_traced(o),
                             "exit=%s status=%s 痕迹=%s；调色板探针=%s" % (
                                 o["exit"], o["status"], _signal_names(o),
                                 _palette_probe(o))),
         probe_script=PROBE_PALETTE,
         recover=lambda ctx: _standard(ctx),
         recover_expect="把 assets/palettes.json 放回：exit 0 / status=success")


def _tpl_schema(ctx):
    _tpl_delete(ctx, os.path.join("assets", "mechanism-spec.schema.json"))
    return _standard(ctx)


scenario("tpl-02-schema-missing", "模板",
         "删掉 assets/mechanism-spec.schema.json（CP2 门失效）",
         "S01 降级为 warn 并写进 uncertainty（不阻断渲染，但不得无痕）",
         _tpl_schema,
         check=lambda o, c: (_has_any(o, ("schema", "S01")),
                             "exit=%s status=%s 痕迹=%s" % (
                                 o["exit"], o["status"], _signal_names(o))))


def _tpl_checklist(ctx):
    _tpl_delete(ctx, os.path.join("templates", "relation-checklist-template.md"))
    return _standard(ctx)


scenario("tpl-03-checklist-template-missing", "模板",
         "删掉 templates/relation-checklist-template.md（人工核对清单）",
         "运行期无消费者 ⇒ 行为不变；属**文档资产**而非运行时依赖（如实标注 N/A）",
         _tpl_checklist,
         check=lambda o, c: (o["exit"] == 0 and o["status"] == "success",
                             "exit=%s status=%s（与健康基线一致）" % (o["exit"], o["status"])),
         success_ok=True,
         note="该模板由 Agent 在 CP3 使用，脚本不读取；删掉不改变退出码是**预期**结果")


def _tpl_result_template(ctx):
    _tpl_delete(ctx, os.path.join("assets", "result.template.json"))
    return _standard(ctx)


scenario("tpl-04-result-template-missing", "模板",
         "删掉 assets/result.template.json（结构模板）",
         "运行期无消费者 ⇒ 行为不变（N/A）",
         _tpl_result_template,
         check=lambda o, c: (o["exit"] == 0 and o["status"] == "success",
                             "exit=%s status=%s（与健康基线一致）" % (o["exit"], o["status"])),
         success_ok=True,
         note="result.template.json 是给人与 Agent 看的结构模板，主流程不读取")


def _tpl_broken_palettes(ctx):
    _write_text(os.path.join(ctx["copy"], "assets", "palettes.json"), "{ this is not json\n")
    return _standard(ctx)


scenario("tpl-05-palettes-corrupted", "模板",
         "把 assets/palettes.json 改成非法 JSON（资产存在但损坏）",
         "读资产失败必须回退内置默认**并留痕**，不得静默用坏值（实测见 §4 G2）",
         _tpl_broken_palettes,
         check=lambda o, c: (_palette_traced(o),
                             "exit=%s status=%s 痕迹=%s；调色板探针=%s" % (
                                 o["exit"], o["status"], _signal_names(o),
                                 _palette_probe(o))),
         probe_script=PROBE_PALETTE,
         note="损坏与缺失走同一条回退路径（_load_palettes 的 except 分支）")


# ---------------- 依赖形态 ----------------

def _dep_import_error(ctx, module):
    stubs = _stub_dir(ctx["work"], module + "-gone", {
        module + ".py": 'raise ImportError("fault_inject: simulated missing %s")\n' % module,
    })
    env = {"PYTHONPATH": stubs + os.pathsep + os.environ.get("PYTHONPATH", "")}
    r = _standard(ctx)
    r["env"] = env
    return r


def _dep_01(ctx):
    return _dep_import_error(ctx, "matplotlib")


scenario("dep-01-matplotlib-import-error", "依赖",
         "matplotlib 不可导入（ImportError）",
         "只交付可编辑 SVG：exit 2 / status=partial / gates.g5_png=false / previews 为空 / 原因入 uncertainty",
         _dep_01,
         check=lambda o, c: (o["exit"] == 2 and o["status"] == "partial"
                             and _has_any(o, ("预览", "matplotlib", "PNG")),
                             "exit=%s status=%s gates=%s 痕迹=%s" % (
                                 o["exit"], o["status"], o["gates"], _signal_names(o))),
         recover=lambda ctx: _standard(ctx),
         recover_expect="移除 PYTHONPATH 上的 stub：exit 0 / status=success（可恢复）")


def _dep_02(ctx):
    stubs = _stub_dir(ctx["work"], "matplotlib-broken", {
        "matplotlib/__init__.py": '__version__ = "0.0.0-fault-inject-stub"\n',
        "matplotlib/pyplot.py": 'raise RuntimeError("fault_inject: simulated broken pyplot")\n',
        "matplotlib/patches.py": "class Rectangle: pass\nclass FancyBboxPatch: pass\nclass Circle: pass\n",
        "matplotlib/colors.py": "def LinearSegmentedColormap(*a, **k):\n    raise RuntimeError('stub')\n",
        "matplotlib/font_manager.py": "class FontProperties:\n    pass\ndef findfont(*a, **k):\n    raise RuntimeError('stub')\n",
    })
    env = {"PYTHONPATH": stubs + os.pathsep + os.environ.get("PYTHONPATH", "")}
    r = _standard(ctx)
    r["env"] = env
    return r


scenario("dep-02-matplotlib-partially-broken", "依赖",
         "matplotlib 能 import，但 matplotlib.pyplot 抛 RuntimeError",
         "走 except Exception 分支同样降级：exit 2 / partial / 原因入 uncertainty（**不得**崩溃）",
         _dep_02,
         check=lambda o, c: (o["exit"] == 2 and o["status"] == "partial"
                             and _has_any(o, ("预览", "RuntimeError", "matplotlib")),
                             "exit=%s status=%s 痕迹=%s" % (
                                 o["exit"], o["status"], _signal_names(o))))


def _dep_03(ctx):
    return _standard(ctx, extra=["--formats", "svg"])


scenario("dep-03-formats-svg-only", "依赖",
         "--formats svg（明确只要可编辑源，不请求预览）",
         "exit 2 / partial：未请求 ≠ 失败，但要说明'本次未请求预览'（可恢复：加回格式即成功）",
         _dep_03,
         check=lambda o, c: (o["exit"] == 2 and o["status"] == "partial"
                             and _has_any(o, ("未请求", "预览")),
                             "exit=%s status=%s 痕迹=%s" % (
                                 o["exit"], o["status"], _signal_names(o))),
         recover=lambda ctx: _standard(ctx),
         recover_expect="--formats svg,png,pdf：exit 0 / status=success")


def _dep_04(ctx):
    return _dep_import_error(ctx, "PIL")


scenario("dep-04-pillow-missing", "依赖",
         "Pillow 不可导入（PNG 写出依赖它）",
         "PNG 写不出时降级为 SVG-only 并留痕；不得伪造成'已导出'",
         _dep_04,
         check=lambda o, c: (o["status"] != "success" and _has_any(o, ("预览", "PNG", "PIL", "Pillow")),
                             "exit=%s status=%s 痕迹=%s" % (
                                 o["exit"], o["status"], _signal_names(o))))


# ---------------- 契约形态 ----------------

def _contract_case(ctx, name, oc):
    case = _write_json(os.path.join(ctx["work"], name), {
        "case_id": "fault-contract-" + name.replace(".json", ""),
        "title": "注入：契约形态 " + name,
        "task": "契约探针：本场景只注入 output_contract 形态，其余输入均为健康值。",
        "materials": [],
        "output_contract": oc,
    })
    return {"argv": ["--case", case, "--materials-dir", _example_materials(ctx),
                     "--model-file", _example_model(ctx), "--out", ctx["out"]],
            "cwd": ctx["work"]}


def _ctr_probe(ctx, name, oc, probes):
    r = _contract_case(ctx, name, oc)
    r["probes"] = probes
    return r


scenario("ctr-01-scalar-form", "契约",
         "output_contract 声明标量字段（无真实值）",
         "顶层出现该字段且为空串 \"\"（不是 null）",
         lambda ctx: _ctr_probe(ctx, "case-ctr-scalar.json", {"probe_str": "声明值"},
                                {"probe_str": ""}),
         check=lambda o, c: _probe_check(o, c, "ctr-01-scalar-form"),
         success_ok=True, note="契约探针：成功是正确结果，检查的是回显形态")


scenario("ctr-02-list-form", "契约",
         "output_contract 声明列表字段（无真实值）",
         "顶层出现该字段且为 []（不是 null）",
         lambda ctx: _ctr_probe(ctx, "case-ctr-list.json", {"probe_list": ["a"]},
                                {"probe_list": []}),
         check=lambda o, c: _probe_check(o, c, "ctr-02-list-form"),
         success_ok=True, note="同上")


scenario("ctr-03-bool-form", "契约",
         "output_contract 声明布尔字段（无真实值）",
         "顶层出现该字段且为 false（不是 null）",
         lambda ctx: _ctr_probe(ctx, "case-ctr-bool.json", {"probe_bool": True},
                                {"probe_bool": False}),
         check=lambda o, c: _probe_check(o, c, "ctr-03-bool-form"),
         success_ok=True, note="同上")


scenario("ctr-04-number-dict-form", "契约",
         "output_contract 声明数值与字典字段（无真实值）",
         "顶层分别为 0 与 {}（不是 null）",
         lambda ctx: _ctr_probe(ctx, "case-ctr-numdict.json",
                                {"probe_num": 150, "probe_dict": {"k": 1}},
                                {"probe_num": 0, "probe_dict": {}}),
         check=lambda o, c: _probe_check(o, c, "ctr-04-number-dict-form"),
         success_ok=True, note="同上")


scenario("ctr-05-null-declared", "契约",
         "output_contract 声明值本身就是 null",
         "按标量形态填 \"\"，**顶层仍然不得出现 null**（D19 第 3 条）",
         lambda ctx: _ctr_probe(ctx, "case-ctr-null.json", {"probe_null": None},
                                {"probe_null": ""}),
         check=lambda o, c: _probe_check(o, c, "ctr-05-null-declared"),
         success_ok=True, note="同上")


def _ctr_06(ctx):
    r = _standard(ctx)
    r["_post"] = "inject-null-then-check"
    return r


def _post_inject_null_and_check(ctx, obs):
    """Post-process: put a top-level null into result.json, then run the real
    contract CLI.  Proves the checker is not vacuous."""
    rp = os.path.join(ctx["out"], "result.json")
    if not os.path.isfile(rp):
        return {"exit": None, "stdout": "", "stderr": "no result.json to corrupt",
                "seconds": 0.0}
    with open(rp, "r", encoding="utf-8") as fh:
        rj = json.load(fh)
    rj["probe_injected_null"] = None
    _write_json(rp, rj)
    res = _run(os.path.join(ctx["copy"], CHECK_REL),
               ["--result", rp, "--case", _example_case(ctx)],
               cwd=ctx["work"])
    res["_corrupted"] = True
    return res


scenario("ctr-06-top-level-null-caught", "契约",
         "主流程跑完后往 result.json 顶层塞一个 null，再跑 check_contract.py",
         "校验器必须报 C04 fail 且 exit 1（证明契约校验不是空转）",
         _ctr_06,
         check=lambda o, c: (o["exit"] == 1 and "C04" in _haystack(o),
                             "check_contract exit=%s；C04 命中=%s；tail=%r" % (
                                 o["exit"], "C04" in _haystack(o), o["stdout_tail"][:60])),
         success_ok=True, note="第二次运行的 exit 码才是被判定的对象（校验器退出码语义）")


def _ctr_07(ctx):
    return {"argv": ["--result", os.path.join(ctx["work"], "no-result.json")],
            "cwd": ctx["work"], "entry": "check_contract"}


scenario("ctr-07-missing-result-json", "契约",
         "check_contract.py 指向不存在的 result.json",
         "exit 1 且报 C01（缺产物必须是可判定的失败，不是 0）",
         _ctr_07,
         check=lambda o, c: (o["exit"] == 1 and "C01" in _haystack(o),
                             "check_contract exit=%s；C01 命中=%s；tail=%r" % (
                                 o["exit"], "C01" in _haystack(o), o["stdout_tail"][:60])),
         success_ok=True, note="直接调用校验 CLI，不跑主流程")


def _write_probe_scripts(ctx):
    for name, text in PROBE_SCRIPTS.items():
        _write_text(os.path.join(ctx["work"], name), text)


def _run_probe(ctx, name, args):
    path = os.path.join(ctx["work"], name)
    if not os.path.isfile(path):
        return None
    res = _run(path, args, cwd=ctx["work"])
    if res["exit"] != 0:
        return {"probe_error": (res["stderr"] or "").strip().splitlines()[-1:] or res["exit"]}
    for line in reversed(res["stdout"].splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except Exception:
                continue
    return {"probe_error": "no JSON"}


# --------------------------------------------------------------------------
# 探针 / 信号工具
# --------------------------------------------------------------------------

NO_RELATION_MATERIAL = """# 合成材料（fault_inject）：只有实体、没有关系

| 名称 | 类型 | 区室 | 数据 | 备注 |
| ALPHA | 蛋白质 | 细胞质 | 表达量=0.40 | 注入用实体 |
| BETA | 蛋白质 | 细胞核 | 表达量=0.60 | 注入用实体 |

## 数据映射

数据映射：field=表达量；低 #FFF7E0 → 高 #1F4E79。

## 图面约束

- 信号流向：胞外 → 膜 → 胞质 → 核。
"""

PROBE_RESULTS = {}


CURRENT_PROBE = {}


def _orphan_traced(obs):
    """True when the dropped-edge fault left a trace anywhere in result.json."""
    return _has_any(obs, ("e999", "丢弃", "端点", "dropped", "边被"))


def _cp1_result(obs):
    p = CURRENT_PROBE or {}
    return p.get("cp1_2_result", "-")


def _cp1_traced(obs):
    """CP1.2 really degraded to warn AND that warn is visible in the result."""
    p = CURRENT_PROBE or {}
    return (p.get("cp1_2_result") == "warn"
            and _has_any(obs, ("CP1", "CP1.2", "task 说明", "任务说明", "任务文本")))


def _palette_probe(obs):
    p = CURRENT_PROBE or {}
    if "loaded" in p:
        return "loaded=%s (%s)" % (p.get("loaded"), p.get("error_type") or "ok")
    return "旧版无 palette_load_status()（探针=%s）" % p.get("palette_loaded")


def _palette_traced(obs):
    """The asset really failed to load AND the fallback is visible in the result."""
    p = CURRENT_PROBE or {}
    loaded = p.get("loaded", p.get("palette_loaded", True))
    return (loaded is False) and _has_any(obs, ("调色", "palette", "资产", "回退"))


def _probe_check(obs, ctx, sid):
    """Check that contract fields were echoed with the declared empty shape."""
    want = ctx.get("probes") or {}
    got = obs["result"] or {}
    bad = []
    for k, v in want.items():
        if k not in got:
            bad.append("%s 缺失" % k)
        elif got[k] != v:
            bad.append("%s=%r≠%r" % (k, got[k], v))
    nulls = [k for k, v in got.items() if v is None]
    if nulls:
        bad.append("顶层 null: %s" % ",".join(nulls))
    PROBE_RESULTS[sid] = {"want": want, "got": {k: got.get(k) for k in want},
                          "nulls": nulls}
    detail = "回显=%s；顶层 null=%s" % (
        {k: got.get(k) for k in want}, nulls or "无")
    return (not bad), detail


def _has_any(obs, needles):
    hay = _haystack(obs)
    return any(n and n in hay for n in needles)


def _signal_names(obs):
    """Which record sites carry a trace of the fault (for the matrix)."""
    names = []
    if obs["uncertainty"]:
        names.append("uncertainty×%d" % len(obs["uncertainty"]))
    if (obs["result"] or {}).get("reason"):
        names.append("reason")
    sc = (obs["result"] or {}).get("self_check") or {}
    if sc.get("warnings"):
        names.append("self_check.warnings×%d" % len(sc["warnings"]))
    if sc.get("failures"):
        names.append("self_check.failures×%d" % len(sc["failures"]))
    return ",".join(names) or "无痕迹"


# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------

def run_one(sc, skill_src, base_work, verbose=False):
    work = os.path.join(base_work, sc["id"])
    os.makedirs(work, exist_ok=True)
    copy = os.path.join(work, "skill")
    _copy_skill(skill_src, copy)
    out = os.path.join(work, "out")
    ctx = {"copy": copy, "work": work, "out": out, "skill": skill_src,
           "out_parent": base_work}
    _write_probe_scripts(ctx)

    spec = sc["inject"](ctx) or {}
    entry = spec.get("entry", "main")
    argv = list(spec.get("argv") or [])
    cwd = spec.get("cwd") or work
    env = spec.get("env")
    exe = (os.path.join(copy, CHECK_REL) if entry == "check_contract"
           else os.path.join(copy, MAIN_REL))
    res = _run(exe, argv, cwd=cwd, env_extra=env)
    if spec.get("_post") == "inject-null-then-check":
        obs_pre = _observe(res, out)
        if verbose:
            print("    [post] corruption step on %s" % obs_pre["status"])
        res = _post_inject_null_and_check(ctx, obs_pre)
        out_for_obs = ctx["work"]
    else:
        out_for_obs = out
    obs = _observe(res, out_for_obs)
    obs["entry"] = entry
    obs["argv_display"] = " ".join(os.path.basename(a) if os.path.isabs(a) else a
                                   for a in argv)

    probe = None
    if sc["probe_script"]:
        probe = _run_probe(ctx, sc["probe_script"], [ctx.get("probe_arg") or ""]
                           if ctx.get("probe_arg") else [])
    CURRENT_PROBE.clear()
    if isinstance(probe, dict):
        CURRENT_PROBE.update(probe)
    PROBE_RESULTS[sc["id"]] = probe

    ok, detail = True, ""
    if sc["check"]:
        ok, detail = sc["check"](obs, ctx)

    # 静默失败判定：exit 0 + status=success 且**没有任何记录位点留痕**
    if sc["success_ok"]:
        silent = False if ok else None
    else:
        silent = bool(obs["exit"] == 0 and obs["status"] == "success"
                      and len(obs["uncertainty"]) == 0
                      and not (obs["result"] or {}).get("reason")
                      and not ((obs["result"] or {}).get("self_check") or {}).get("warnings"))

    rec = None
    if sc["recover"]:
        rspec = sc["recover"](ctx) or {}
        rwork = os.path.join(work, "recover")
        os.makedirs(rwork, exist_ok=True)
        rcopy = os.path.join(rwork, "skill")
        _copy_skill(skill_src, rcopy)         # 干净副本 = 修复动作
        rout = os.path.join(rwork, "out")
        rctx = {"copy": rcopy, "work": rwork, "out": rout, "skill": skill_src}
        rspec2 = sc["recover"](rctx) or {}
        rres = _run(os.path.join(rcopy, MAIN_REL), list(rspec2.get("argv") or []),
                    cwd=rctx["work"], env_extra=rspec2.get("env"))
        robs = _observe(rres, rout)
        rec = {"expect": sc["recover_expect"], "exit": robs["exit"],
               "status": robs["status"], "gates": robs["gates"],
               "ok": robs["exit"] == 0 and robs["status"] == "success"}

    return {
        "id": sc["id"], "family": sc["family"], "title": sc["title"],
        "expect": sc["expect"], "note": sc["note"],
        "entry": entry,
        "command": " ".join([os.path.basename(exe)] + [str(a) for a in argv]),
        "injection": spec.get("what") or sc["title"],
        "observed": {
            "exit": obs["exit"], "status": obs["status"], "gates": obs["gates"],
            "seconds": obs["seconds"], "artifacts": obs["artifacts"],
            "uncertainty_count": len(obs["uncertainty"]),
            "uncertainty": obs["uncertainty"][:6],
            "reason": obs.get("reason"),
            "signal_sites": _signal_names(obs),
            "stderr_tail": obs["stderr_tail"],
            "top_keys": obs.get("top_keys"),
        },
        "check_ok": ok, "check_detail": detail,
        "silent": silent,
        "recovery": rec,
        "probe": probe,
    }


def render_markdown(results, meta):
    lines = []
    lines.append("| # | 形态 | 注入什么 | 期望行为 | 实测 exit | 实测 status | gates | uncertainty 条数 | 实测留痕位点 | 静默失败 | 判定 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(results, 1):
        o = r["observed"]
        sig = o["signal_sites"]
        if r["silent"]:
            silent = "**是**"
        elif r["silent"] is None:
            silent = "不确定"
        elif (r["check_ok"] and o["exit"] == 0 and o["status"] == "success"
              and o["uncertainty_count"] == 0):
            silent = "N/A（无运行时消费者）"
        else:
            silent = "否"
        verdict = "符合期望" if r["check_ok"] else "**与期望不符**"
        lines.append("| %d | %s | %s | %s | `%s` | `%s` | `%s` | %d | %s | %s | %s |" % (
            i, r["family"], r["title"], r["expect"], o["exit"], o["status"],
            o["gates"], o["uncertainty_count"], sig, silent, verdict))
    lines.append("")
    lines.append("复跑命令：`python3 scripts/fault_inject.py --out <包外目录>`（本表由该命令实跑生成，"
                 "无手写数字）。生成时间 %s；Python %s。" % (meta["ts"], meta["python"]))
    lines.append("")
    for r in results:
        if r["probe"]:
            lines.append("- `%s` 探针读数：`%s`" % (r["id"], json.dumps(r["probe"], ensure_ascii=False)))
        if r["recovery"]:
            lines.append("- `%s` 恢复演练：%s → exit=`%s` status=`%s`（%s）" % (
                r["id"], r["recovery"]["expect"], r["recovery"]["exit"],
                r["recovery"]["status"], "可恢复" if r["recovery"]["ok"] else "**未恢复**"))
    lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(
        description="失败注入与恢复演练（四形态：输入/模板/依赖/契约）")
    ap.add_argument("--skill", default=SKILL_ROOT,
                    help="待测技能根目录（默认 = 本脚本所在技能）")
    ap.add_argument("--out", required=True, help="报告输出目录（包外）")
    ap.add_argument("--family", action="append", default=[],
                    help="只跑某形态（可重复：输入/模板/依赖/契约）")
    ap.add_argument("--only", default="",
                    help="只跑指定 id（逗号分隔，支持前缀匹配）")
    ap.add_argument("--json", default="fault-report.json", help="报告 JSON 文件名")
    ap.add_argument("--md", default="FAULT-MATRIX.generated.md", help="报告 Markdown 文件名")
    ap.add_argument("--keep", action="store_true", help="保留临时技能副本（调试用）")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    skill = os.path.abspath(args.skill)
    if not os.path.isfile(os.path.join(skill, MAIN_REL)):
        print("FATAL 找不到 %s（--skill 是否指向技能根目录？）" % MAIN_REL)
        return 4
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    only = [s.strip() for s in args.only.split(",") if s.strip()]
    picked = []
    for sc in SCENARIOS:
        if args.family and sc["family"] not in args.family:
            continue
        if only and not any(sc["id"] == o or sc["id"].startswith(o) for o in only):
            continue
        picked.append(sc)

    base_work = tempfile.mkdtemp(prefix="fault-inject-")
    print("[fault_inject] skill=%s" % skill)
    print("[fault_inject] 场景 %d 个；临时工作目录=%s" % (len(picked), base_work))
    results = []
    try:
        for i, sc in enumerate(picked, 1):
            t0 = time.time()
            print("[%2d/%2d] %-32s %s" % (i, len(picked), sc["id"], sc["title"]))
            try:
                r = run_one(sc, skill, base_work, verbose=args.verbose)
            except Exception as ex:                       # pragma: no cover
                r = {"id": sc["id"], "family": sc["family"], "title": sc["title"],
                     "expect": sc["expect"], "note": sc["note"],
                     "command": "-", "injection": sc["title"],
                     "observed": {"exit": None, "status": None, "gates": None,
                                  "seconds": 0.0, "artifacts": [],
                                  "uncertainty_count": 0, "uncertainty": [],
                                  "signal_sites": "runner-error",
                                  "stderr_tail": "%s: %s" % (type(ex).__name__, ex)},
                     "check_ok": False, "check_detail": "runner error: %s" % ex,
                     "silent": None, "recovery": None, "probe": None}
            o = r["observed"]
            flag = "OK " if r["check_ok"] else "!! "
            silent_flag = " SILENT" if r["silent"] else ""
            print("        %sexit=%s status=%s unc=%d gates=%s%s  (%.1fs)" % (
                flag, o["exit"], o["status"], o["uncertainty_count"], o["gates"],
                silent_flag, time.time() - t0))
            if r["recovery"]:
                print("        recover: exit=%s status=%s %s" % (
                    r["recovery"]["exit"], r["recovery"]["status"],
                    "OK" if r["recovery"]["ok"] else "!!"))
            results.append(r)
        meta = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "skill": os.path.basename(skill),
                "python": sys.version.split()[0],
                "scenario_count": len(results),
                "family_order": list(FAMILIES)}
        report = {"meta": meta, "scenarios": results,
                  "summary": {
                      "total": len(results),
                      "expect_ok": sum(1 for r in results if r["check_ok"]),
                      "silent_failures": [r["id"] for r in results if r["silent"]],
                      "mismatch": [r["id"] for r in results if not r["check_ok"]],
                      "recovery_ok": sum(1 for r in results
                                         if r["recovery"] and r["recovery"]["ok"]),
                      "recovery_total": sum(1 for r in results if r["recovery"]),
                  }}
        jp = os.path.join(out, args.json)
        _write_json(jp, report)
        mp = os.path.join(out, args.md)
        _write_text(mp, render_markdown(results, meta))
        s = report["summary"]
        print("[fault_inject] 写入 %s" % jp)
        print("[fault_inject] 写入 %s" % mp)
        print("SUMMARY " + json.dumps({
            "scenarios": s["total"], "expect_ok": s["expect_ok"],
            "mismatch": s["mismatch"], "silent_failures": s["silent_failures"],
            "recovery": "%d/%d" % (s["recovery_ok"], s["recovery_total"]),
        }, ensure_ascii=False))
        return 0 if s["expect_ok"] == s["total"] else 1
    finally:
        if args.keep:
            print("[fault_inject] 保留临时目录 %s" % base_work)
        else:
            shutil.rmtree(base_work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
