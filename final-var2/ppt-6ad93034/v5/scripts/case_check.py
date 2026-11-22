# -*- coding: utf-8 -*-
"""case_check.py — 多案例泛化台：逐案实测 + 可接受区间判定 + 边界探针（generalization 轴）。

做三件事：

  1) **逐案实测**：对 `examples/cases/<case>/case.json` 各跑一次完整 `scripts/main.py`
     （在**包外**副本上跑），把 `status / slide_count / 角色序列 / 图表形态 /
     unverified / 备注覆盖 / 脚注覆盖 / 关键数字是否入页 / 是否出现禁列数字` 全部读出来。

  2) **可接受区间判定**：期望写在每个 `case.json` 的 `_case_set.expect` 里
     （例如 `status_any_of`、`slide_count`、`must_have_figure_kind`、
     `unverified_claims_max`、`must_mention_in_deck`、`forbid_in_deck`）。
     本台逐条对照并给出 PASS/FAIL——**期望写的是"诚实行为"，不是"理想行为"**：
     例如"无数据表的案例不许出现 chart_image"是硬判据，
     而"status 允许 partial"也是写在期望里的（材料有缺口时 partial 才是正确结果）。

  3) **边界探针**（`--probes`）：把同一份案例做四种变形，实测**泛化在哪里失效**：
     多表、无章节标题、页数上限过紧、材料数字与主张不一致。

用法:
  python case_check.py --pkg "$SKILL_DIR" --work <包外目录>
  python case_check.py --pkg "$SKILL_DIR" --work <包外目录> --probes
  python case_check.py --list                     # 只列案例与期望，不跑

退出码: 0 = 全部案例通过判定且探针跑完；1 = 有 FAIL；
        2 = 环境不可用（找不到 SKILL.md / 找不到案例 / --work 落在包内）。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PKG = os.path.dirname(HERE)
CASES_REL = os.path.join("examples", "cases")


# ---------------------------------------------------------------------------
# 基础
# ---------------------------------------------------------------------------

def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path, obj):
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def copy_pkg(src, dst):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return dst


def list_cases(pkg):
    root = os.path.join(pkg, CASES_REL)
    if not os.path.isdir(root):
        return []
    out = []
    for name in sorted(os.listdir(root)):
        cj = os.path.join(root, name, "case.json")
        if os.path.isfile(cj):
            out.append((name, cj))
    return out


# ---------------------------------------------------------------------------
# 跑一个案例并采集可观测量
# ---------------------------------------------------------------------------

def normalize_text(s):
    """去掉空白与句读，便于"关键数字是否入页"这类判定不受断句影响。"""
    for ch in (" ", "\u3000", "\n", "\t", "\"", "'", "`", "*", "（", "）", "(", ")"):
        s = s.replace(ch, "")
    return s


def collect(out_dir):
    """从一次运行读出所有用于判定泛化行为的量。"""
    obs = {"has_result": False, "status": None, "slide_count": 0, "roles": [],
           "figure_kinds": {}, "degraded_figures": 0, "figures_with_note": 0,
           "unverified": 0, "material_warnings": 0, "uncertainty": 0,
           "notes_coverage": 0.0, "footer_coverage": 0.0,
           "text": "", "norm_text": "", "contract_keys": [], "gate_valid": None,
           "checks_all_pass": None, "top_keys": 0, "reopenable": None, "notes": []}
    rp = os.path.join(out_dir, "result.json")
    if not os.path.isfile(rp):
        obs["notes"].append("没有 result.json")
        return obs
    obs["has_result"] = True
    try:
        r = load_json(rp)
    except Exception as e:  # noqa: BLE001
        obs["notes"].append("result.json 无法解析: %s" % e)
        return obs
    obs["top_keys"] = len(r)
    obs["status"] = r.get("status")
    deck = r.get("deck") or {}
    slides = deck.get("slides") or []
    obs["slide_count"] = deck.get("slide_count") or len(slides)
    obs["roles"] = [s.get("role") for s in slides]
    for sl in slides:
        fig = sl.get("figure") or {}
        k = fig.get("kind") or "none"
        obs["figure_kinds"][k] = obs["figure_kinds"].get(k, 0) + 1
        if k == "table" and fig.get("note"):
            obs["degraded_figures"] += 1
        if fig.get("note"):
            obs["figures_with_note"] += 1
    n = len(slides) or 1
    obs["notes_coverage"] = round(sum(1 for s in slides if s.get("notes")) / n, 4)
    obs["footer_coverage"] = round(
        sum(1 for s in slides if s.get("evidence_footer")) / n, 4)
    ev = r.get("evidence") or {}
    obs["unverified"] = len(ev.get("unverified_claims") or [])
    obs["material_warnings"] = len(ev.get("material_warnings") or [])
    obs["uncertainty"] = len(r.get("uncertainty") or [])
    obs["checks_all_pass"] = (r.get("checks") or {}).get("all_pass")
    obs["gate_valid"] = ((r.get("run_meta") or {}).get("gate") or {}).get("valid")
    base = set(json.load(open(os.path.join(os.path.dirname(rp), "..", "..",
                                           "..", "..", "nope"), "r"))) \
        if False else None  # placeholder never executed
    parts = []
    for sl in slides:
        parts.append(str(sl.get("title") or ""))
        for c in (sl.get("claims") or []):
            parts.append(str(c.get("text") or ""))
        parts.append(str(sl.get("evidence_footer") or ""))
    obs["text"] = "\n".join(parts)
    obs["norm_text"] = normalize_text(obs["text"])
    editable = deck.get("editable") or ""
    if editable:
        dp = editable if os.path.isabs(editable) else os.path.join(out_dir, editable)
        try:
            from pptx import Presentation
            obs["reopenable"] = len(Presentation(dp).slides._sldIdLst)
        except Exception as e:  # noqa: BLE001
            obs["reopenable"] = "FAILED: %s" % e
    return obs


def run_case(pkg, case_json, out_dir, extra=None, cwd=None):
    os.makedirs(out_dir, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [sys.executable, os.path.join(pkg, "scripts", "main.py"),
           "--case", case_json, "--out", out_dir] + list(extra or ())
    t0 = time.time()
    p = subprocess.run(cmd, env=env, cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    out = p.stdout.decode("utf-8", errors="replace")
    return p.returncode, out, round(time.time() - t0, 2)


# ---------------------------------------------------------------------------
# 期望判定
# ---------------------------------------------------------------------------

def judge(obs, expect, advisory=None):
    """逐条对照 _case_set.expect；advisory 里的项只记录、不计入通过判定。

    返回 (checks, failed_names, advisory_checks)。
    """
    checks = []

    def add(name, ok, detail):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    allowed = expect.get("status_any_of")
    if allowed:
        add("status_any_of", obs["status"] in allowed,
            "status=%s ∈ %s" % (obs["status"], allowed))

    sc = expect.get("slide_count")
    if sc is not None:
        add("slide_count", obs["slide_count"] == sc,
            "slides=%s expect=%s" % (obs["slide_count"], sc))

    if expect.get("roles_head"):
        add("roles_head", obs["roles"][:1] == [expect["roles_head"]],
            "first role=%s" % (obs["roles"][:1]))
    if expect.get("roles_tail"):
        add("roles_tail", obs["roles"][-1:] == [expect["roles_tail"]],
            "last role=%s" % (obs["roles"][-1:]))

    mustk = expect.get("must_have_figure_kind")
    if mustk:
        hit = [k for k in mustk if obs["figure_kinds"].get(k)]
        add("must_have_figure_kind", bool(hit),
            "figure_kinds=%s 需要其中之一=%s" % (obs["figure_kinds"], mustk))

    forbk = expect.get("forbid_figure_kind") or []
    bad = [k for k in forbk if obs["figure_kinds"].get(k)]
    if forbk:
        add("forbid_figure_kind", not bad,
            "出现被禁图表形态=%s" % (bad or "无"))

    uvm = expect.get("unverified_claims_max")
    if uvm is not None:
        add("unverified_claims_max", obs["unverified"] <= uvm,
            "unverified=%s ≤ %s" % (obs["unverified"], uvm))

    cov = expect.get("min_notes_coverage")
    if cov is not None:
        add("min_notes_coverage", obs["notes_coverage"] >= cov,
            "notes_coverage=%s ≥ %s" % (obs["notes_coverage"], cov))

    cov2 = expect.get("min_evidence_footer_coverage")
    if cov2 is not None:
        add("min_evidence_footer_coverage", obs["footer_coverage"] >= cov2,
            "footer_coverage=%s ≥ %s" % (obs["footer_coverage"], cov2))

    must = expect.get("must_mention_in_deck") or []
    missing = [t for t in must if normalize_text(t) not in obs["norm_text"]]
    if must:
        add("must_mention_in_deck", not missing,
            "缺失=%s" % (missing or "无"))

    forb = expect.get("forbid_in_deck") or []
    present = [t for t in forb if normalize_text(t) in obs["norm_text"]]
    if forb:
        add("forbid_in_deck", not present, "出现禁列内容=%s" % (present or "无"))

    add("gate_valid", obs["gate_valid"] is True,
        "G1–G8 gate=%s" % obs["gate_valid"])
    add("deck_reopenable", obs["reopenable"] == obs["slide_count"],
        "deck 重开页数=%s，result.slide_count=%s"
        % (obs["reopenable"], obs["slide_count"]))

    failed = [c["name"] for c in checks if not c["ok"]]

    adv = []
    if advisory:
        adv_chk, _, _ = judge(obs, advisory)       # 复用同一套判据，但不计入失败
        skip = ("gate_valid", "deck_reopenable")
        adv = [c for c in adv_chk if not c["ok"] and c["name"] not in skip]
    return checks, failed, adv


# ---------------------------------------------------------------------------
# 边界探针：泛化在哪里失效
# ---------------------------------------------------------------------------

PROBES = [
    dict(id="P1", title="两张数据表（材料给了两个 CSV）",
         why="看图表绑定是否只认第一张、第二张会不会被静默丢掉"),
    dict(id="P2", title="材料没有任何章节标题（纯段落）",
         why="看 sction 抽取失效后是降级留痕还是静默兜底"),
    dict(id="P3", title="页数上限压到 3（材料内容远超）",
         why="看压缩是否丢证据页、是否有记录"),
    dict(id="P4", title="用 --edit 往页面塞一个材料里没有的数字",
         why="看编辑链路是否仍过 D2 数字核验（不因用户要求就放行）"),
]


def build_probe(pkg, case_name, probe_id, probe_dir):
    """把案例 A 变形出四种边界输入（全部在包外临时目录里做）。"""
    src = os.path.join(pkg, CASES_REL, case_name)
    if os.path.isdir(probe_dir):
        shutil.rmtree(probe_dir)
    shutil.copytree(src, probe_dir)
    case = load_json(os.path.join(probe_dir, "case.json"))
    case.pop("_case_set", None)
    case["case_id"] = "%s-probe-%s" % (case.get("case_id", "case"), probe_id)

    if probe_id == "P1":
        # 复制出一份第二张表（同一份数据换个名字），并把它也列进 material
        rows = read_text(os.path.join(probe_dir, "jv.csv"))
        write_text(os.path.join(probe_dir, "jv_second.csv"),
                   rows.replace("current_mA_cm2", "current_density"))
        case["inputs"]["material"] = ["material.md", "jv.csv", "jv_second.csv"]
    elif probe_id == "P2":
        txt = read_text(os.path.join(probe_dir, "material.md"))
        stripped = "\n".join(
            (ln if not ln.startswith("#") else ln.lstrip("# ").strip())
            for ln in txt.split("\n"))
        write_text(os.path.join(probe_dir, "material.md"), stripped)
    elif probe_id == "P3":
        case["spec"]["max_slides"] = 3
    elif probe_id == "P4":
        dump_json(os.path.join(probe_dir, "edits.json"), {
            "reason": "探针：故意引入一个材料里没有的数字",
            "ops": [{"op": "update_bullet", "page": 8, "bullet_index": 0,
                     "text": "PABr 界面钝化把器件效率推到 31.7%，是本文最大的贡献。",
                     "evidence": ["§5 结论"],
                     "reason": "探针：材料里没有 31.7%"}]})

    dump_json(os.path.join(probe_dir, "case.json"), case)
    return os.path.join(probe_dir, "case.json")


def run_probe(pkg, case_name, probe, work_root):
    pdir = os.path.join(work_root, "probes", probe["id"])
    case_json = build_probe(pkg, case_name, probe["id"], os.path.join(pdir, "case"))
    out_dir = os.path.join(pdir, "out")
    extra = []
    edits = os.path.join(os.path.dirname(case_json), "edits.json")
    if os.path.isfile(edits):
        extra = ["--edit", edits, "--version", "probe"]
    rc, out, secs = run_case(pkg, case_json, out_dir, extra=extra)
    obs = collect(out_dir)
    return {"id": probe["id"], "title": probe["title"], "why": probe["why"],
            "exit": rc, "seconds": secs, "obs": obs,
            "tail": out.strip().splitlines()[-2:]}


# ---------------------------------------------------------------------------
# 渲染
# ---------------------------------------------------------------------------

def render_md(cases, probes):
    L = ["# CASE-SET 实测输出（由 `scripts/case_check.py --report-md` 现场生成）\n",
         "## 逐案实测\n"]
    for c in cases:
        L.append("### %s — `%s`\n" % (c["case_id"], c["name"]))
        o = c["obs"]
        L.append("| 观测量 | 实测 |")
        L.append("|-|-|")
        L.append("| status | `%s` |" % o["status"])
        L.append("| slide_count | %s |" % o["slide_count"])
        L.append("| 角色序列 | %s |" % " → ".join(str(x) for x in o["roles"]))
        L.append("| 图表形态 | %s |" % o["figure_kinds"])
        L.append("| unverified / material_warnings / uncertainty | %s / %s / %s |"
                 % (o["unverified"], o["material_warnings"], o["uncertainty"]))
        L.append("| 备注覆盖 / 脚注覆盖 | %s / %s |" % (o["notes_coverage"],
                                                        o["footer_coverage"]))
        L.append("| 契约门 / 自检 / deck 重开 | %s / %s / %s |"
                 % (o["gate_valid"], o["checks_all_pass"], o["reopenable"]))
        L.append("| exit | %s |" % c["exit"])
        L.append("")
        L.append("| 判定项 | 结果 | 细节 |")
        L.append("|-|-|-|")
        for chk in c["checks"]:
            L.append("| %s | %s | %s |" % (chk["name"],
                                           "PASS" if chk["ok"] else "**FAIL**",
                                           chk["detail"]))
        L.append("")
    if probes:
        L.append("## 边界探针\n")
        L.append("| # | 变形 | exit | status | slides | 图表形态 | unverified | unc | 结论 |")
        L.append("|-|-|-|-|-|-|-|-|-|")
        for p in probes:
            o = p["obs"]
            L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |"
                     % (p["id"], p["title"], p["exit"], o["status"], o["slide_count"],
                        o["figure_kinds"], o["unverified"], o["uncertainty"],
                        p.get("conclusion", "")))
        L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="多案例泛化台：逐案实测 + 可接受区间 + 边界探针")
    ap.add_argument("--pkg", default=DEFAULT_PKG, help="技能根目录（含 SKILL.md）")
    ap.add_argument("--work", default=None, help="**包外**可写工作目录")
    ap.add_argument("--only", default=None, help="逗号分隔的案例目录名")
    ap.add_argument("--probes", action="store_true", help="额外跑四种边界探针")
    ap.add_argument("--probe-case", default="case-a-perovskite",
                    help="探针用哪个案例作底（默认 case-a-perovskite）")
    ap.add_argument("--report-json", default=None)
    ap.add_argument("--report-md", default=None)
    ap.add_argument("--verbose", action="store_true", help="失败时打印运行尾部")
    ap.add_argument("--list", action="store_true", help="只列案例与期望")
    args = ap.parse_args(argv)

    pkg = os.path.abspath(args.pkg)
    if not os.path.isfile(os.path.join(pkg, "SKILL.md")):
        print("ERROR: %s 下没有 SKILL.md，--pkg 应指向技能根目录" % pkg)
        return 2

    cases = list_cases(pkg)
    if args.only:
        want = [x.strip() for x in args.only.split(",") if x.strip()]
        cases = [(n, p) for n, p in cases if n in want]
    if not cases:
        print("ERROR: 没找到案例（期望 %s/<case>/case.json）" % CASES_REL)
        return 2

    if args.list:
        print("共 %d 个案例：\n" % len(cases))
        for name, cj in cases:
            meta = (load_json(cj).get("_case_set") or {})
            print("  %-24s %s" % (name, meta.get("topic", "")))
            print("      难度层: %s" % meta.get("difficulty", "-"))
            for k, v in (meta.get("expect") or {}).items():
                print("      %-28s %s" % (k, v))
            print()
        print("跑法: python case_check.py --pkg <SKILL_DIR> --work <包外目录> [--probes]")
        return 0

    work = os.path.abspath(args.work or os.path.join(os.path.dirname(pkg), "case-work"))
    try:
        inside = os.path.commonpath([work, pkg]) == pkg
    except ValueError:
        inside = False
    if inside:
        print("ERROR: --work 不能落在被测技能包内部: %s" % work)
        return 2
    os.makedirs(work, exist_ok=True)

    run_pkg = copy_pkg(pkg, os.path.join(work, "pkg"))
    print("被测包: %s" % pkg)
    print("运行副本: %s（包外）" % run_pkg)
    print("工作区: %s\n" % work)

    results = []
    failed_all = []
    for name, cj in cases:
        local_cj = os.path.join(run_pkg, CASES_REL, name, "case.json")
        raw = load_json(local_cj)
        expect = (raw.get("_case_set") or {}).get("expect") or {}
        # 复制案例输入到包外（保持"绝不写回包内"的纪律）
        cdir = os.path.join(work, "cases", name)
        if os.path.isdir(cdir):
            shutil.rmtree(cdir)
        shutil.copytree(os.path.dirname(local_cj), cdir)
        case_json = os.path.join(cdir, "case.json")
        out_dir = os.path.join(work, "out", name)
        rc, out, secs = run_case(run_pkg, case_json, out_dir)
        obs = collect(out_dir)
        gaps = (raw.get("_case_set") or {}).get("known_gaps") or {}
        gaps = {k: v for k, v in gaps.items() if k not in ("note", "why")}
        checks, failed, advisory = judge(obs, expect, gaps)
        failed_all.extend("%s/%s" % (name, f) for f in failed)
        rec = {"name": name, "case_id": raw.get("case_id"),
               "expect": expect, "exit": rc, "seconds": secs, "obs": obs,
               "checks": checks, "failed": failed, "advisory_gaps": advisory}
        results.append(rec)
        print("  %-24s exit=%s status=%-8s slides=%-2s 判定=%s"
              % (name, rc, obs["status"], obs["slide_count"],
                 "PASS" if not failed else "FAIL(%d): %s" % (len(failed), ",".join(failed))))
        if advisory:
            print("      已知缺口(advisory，不计入失败): %s"
                  % ", ".join("%s[%s]" % (c["name"], c["detail"]) for c in advisory))
        if args.verbose and failed:
            print(out[-800:])
        sys.stdout.flush()

    probes = []
    if args.probes:
        print("\n边界探针（同一案例的四种变形）：")
        for probe in PROBES:
            p = run_probe(run_pkg, args.probe_case, probe, work)
            o = p["obs"]
            p["conclusion"] = ("无 result.json" if not o["has_result"] else
                               "status=%s / slides=%s / fig=%s / unverified=%s"
                               % (o["status"], o["slide_count"],
                                  ",".join(sorted(o["figure_kinds"])), o["unverified"]))
            probes.append(p)
            print("  %s %-34s exit=%s status=%-8s slides=%-2s fig=%-22s unv=%s"
                  % (p["id"], p["title"], p["exit"], o["status"], o["slide_count"],
                     ",".join(sorted(o["figure_kinds"])) or "-", o["unverified"]))
            sys.stdout.flush()

    if args.report_json:
        dump_json(os.path.abspath(args.report_json),
                  {"package": os.path.basename(pkg),
                   "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "cases": results, "probes": probes})
    if args.report_md:
        write_text(os.path.abspath(args.report_md), render_md(results, probes))

    print("\n案例判定: %s" % ("全部 PASS（%d 个案例）" % len(results)
                              if not failed_all else "FAIL: %s" % ", ".join(failed_all)))
    return 1 if failed_all else 0


if __name__ == "__main__":
    sys.exit(main())
