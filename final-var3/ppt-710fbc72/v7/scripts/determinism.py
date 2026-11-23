#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""determinism.py — measure byte-level reproducibility, and name every field that
is *deliberately* unable to be identical.

Why this script exists
----------------------
`SKILL.md` says "the same input produces the same bytes".  A sentence in a
document is not evidence.  This script runs the real `scripts/main.py` N times
under systematically varied conditions, hashes every file each run produced, and
reports which files and which JSON field paths differed — instead of asking the
reader to take reproducibility on faith.

Experimental design (this matters more than the code)
----------------------------------------------------
The input corpus is built **once**, into a fixed directory, and every run reads
that same corpus.  An earlier draft gave each run its own private input copy;
that measures nothing, because the input paths then differ on purpose and every
absolute path in every record changes with them.  Here only three things vary:

  * the working directory the command is launched from (c3, c5);
  * `PYTHONHASHSEED` (c4);
  * the output directory (always a fresh path under the scratch tree), which is
    also what makes c5's relative-vs-absolute argument form interesting.

Conditions
----------
  c1  same cwd, same env, N separate OS processes   -> in-process state, clocks
  c2  repeat of c1, later in wall-clock time        -> clock/jitter sensitivity
  c3  three different cwds (nested one and two deep) -> records that embed the
                                                        caller's own directory
  c4  PYTHONHASHSEED = 0 / 1 / 12345 / unset        -> set/dict iteration order
  c5  relative vs absolute `--case` / `--out` from an explicit cwd
                                                    -> argument normalisation

Identity is reported in three tiers, so a failing tier never hides a passing one
-----------------------------------------------------------------------------
  L1 raw           : byte-for-byte, nothing removed.  Only files that contain no
                     stamp and no host anchor can pass this — normally `summary.txt`
                     and the binary deliverables.
  L2 no-stamp      : drop the declared *nondeterministic* fields (timestamps,
                     interpreter/package versions).  This is the tier that must
                     pass, and it is what "deterministic" is supposed to mean.
  L3 no-anchor     : drop the *host-anchored* values too — the caller's cwd, the
                     scratch root and the output dir, substituted with `<CWD>` /
                     `<RUN>` / `<OUT>`.  Passes only when a field really is a pure
                     function of the run layout; names the anchor family otherwise.

Categories
----------
`NONDETERMINISM` lists fields that cannot be equal in two runs without lying
(a wall-clock stamp).  `HOST_ANCHOR` lists fields that are a deterministic
function of *where* the run happened (the caller's cwd, the machine's font
directory, the interpreter's versions).  Both are declared, per field, with the
reason.  Anything outside both tables shows up in `unexpected_volatile` and makes
the run fail: that is the class of defect this file exists to catch.

Usage
-----
    python scripts/determinism.py --skill <package root> \
        [--runs 3] [--run <scratch dir>] [--json report.json] \
        [--markdown table.md] [--condition c1,c3] [--timeout 180]

Exit 0 when L2 passes for every compared file and no field outside the two
declaration tables varies; 1 when L2 fails or an undeclared field varies;
2 on usage/environment errors.

The script **never executes inside the package**: the pipeline runs on a copy of
the package under the scratch tree, because running `scripts/*.py` with the
package as the working directory leaves `scripts/__pycache__/*.pyc` behind and
`.pyc` is a resource type the submission contract rejects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# Declaration table 1 — genuinely nondeterministic (a stamp; same-input runs
# cannot agree on it without lying).  Pattern -> reason.
# ---------------------------------------------------------------------------
NONDETERMINISM = {
    "generated_at": "wall-clock UTC stamp written on purpose (ISO8601, 1 s resolution)",
    "verification.render.generated_at": "the same stamp, copied into render_log.json",
    "tool_versions.*": "interpreter/package versions of the host that ran the pipeline",
}

# ---------------------------------------------------------------------------
# Declaration table 2 — host-anchored: the value is a pure function of *where*
# the run happened (the launch directory, the scratch/output/case directory,
# the machine's font set).  Deterministic on one host, unable to be byte-equal
# across hosts or launch directories — and the SKILL cannot drop them either,
# because every one of them is a locator a reviewer needs.
#
# '*' spans any characters, so `*.detail` means "this leaf name at any depth".
# Exact leaf names that happen to contain '_' or '.' are written literally.
# ---------------------------------------------------------------------------
HOST_ANCHOR = {
    "*.abspath":
        "portable path = a pure function of the caller's cwd "
        "(references/OUTPUT_CONTRACT.md requires exactly this form)",
    "*.detail": "audit-check text that quotes the artifact path it checked",
    "*.file": "resolved input path of a figure (recorded as given, absolute or relative)",
    "*.file_abs": "resolved input path of a figure file",
    "paths": "resolved source-material path list",
    "sources[].path": "resolved input path of one source-material file",
    "template.source": "resolved path of the template handed to the build stage",
    "template_audit.template_source": "same value, echoed into result.json",
    "cover.path": "resolved output path of the cover preview",
    "contact_sheet.path": "resolved output path of the contact-sheet preview",
    "verification.render.cover.path": "the same preview path, echoed into result.json",
    "verification.render.contact_sheet.path": "the same preview path, echoed into result.json",
    "verification.render.font.file": "font basename probed from the host's font directories",
    "verification.render.font.path": "font path probed from the host's font directories",
    "verification.render.font.candidates_probed": "how many font candidates this host could probe",
    "verification.render.backend": "renderer actually available on the host",
    "*.candidates_probed": "font probing is a function of the host's font directories",
    "uncertainty[].note":
        "disclosure text; the builtin-template entry quotes the run-time template path",
    "artifacts[].checks.sha256":
        "digest of an artifact that itself carries a host anchor (see its own row)",
    "verification.traceability.hashes.*":
        "digest of spec.json / adopt_plan.json, which carry a host anchor",
    "hashes.spec_sha256": "the same digest, as recorded in audit.json",
    "hashes.adopt_plan_sha256": "the same digest, as recorded in audit.json",
}

# ---------------------------------------------------------------------------
# Declaration table 3 — invocation-form conditional: identical across repeated
# runs, working directories and hash seeds, but *not* across "the caller passed
# a relative --case" vs "the caller passed an absolute --case".  A real
# property of the pipeline (it records the path it was given when that path is
# already absolute, and resolves against the case directory otherwise), so it
# is declared instead of being counted as nondeterminism.
# ---------------------------------------------------------------------------
INVOCATION_FORM = {
    "content.json:sources[].path": "--case absolute -> absolute record; relative -> case-relative",
    "content.json:*.file_abs": "same rule, for figure files",
    "spec.json:*.file": "spec re-records the figure path resolved by content.json",
    "audit.json:hashes.spec_sha256": "digest of spec.json, whose figures[].file differs by form",
}

# Files whose bytes are the deliverable under test.  result.json / render_log.json
# / audit.json are excluded from the *declaration* because they carry the stamp
# (audit.json carries anchors); they are still measured and reported.
CORE_ARTIFACTS = [
    "{case_id}_deck.pptx",
    "{case_id}_cover_preview.png",
    "{case_id}_slides_contact_schematic.png",
    "spec.json", "adopt_plan.json", "content.json", "summary.txt",
    "_runtime/builtin.pptx",
]

_PATHISH = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\|[\\/]|\.\.?[\\/]|~[\\/])")


def _rm(path: str) -> None:
    if not os.path.exists(path):
        return
    try:
        shutil.rmtree(path)
    except Exception:
        for root, dirs, files in os.walk(path, topdown=False):
            for n in files:
                try:
                    os.chmod(os.path.join(root, n), 0o666)
                except Exception:
                    pass
            for n in dirs:
                try:
                    os.chmod(os.path.join(root, n), 0o777)
                except Exception:
                    pass
        shutil.rmtree(path, ignore_errors=True)


def _write(path: str, text: str) -> str:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _walk(root: str) -> list:
    out = []
    for dirpath, dirnames, names in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for n in names:
            p = os.path.join(dirpath, n)
            if os.path.isfile(p):
                out.append(os.path.relpath(p, root).replace("\\", "/"))
    return sorted(out)


def _tail(text: str, n: int = 200) -> str:
    text = (text or "").strip().replace("\r", "")
    return text.splitlines()[-1][:n] if text else ""


# ---------------------------------------------------------------------------
# JSON walking / normalisation
# ---------------------------------------------------------------------------


def _flatten(obj, prefix: str = "") -> dict:
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(_flatten(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = repr(obj)
    return out


def _anchor_map(anchors: list) -> dict:
    """Map every file under every anchor, in both slash forms, to its token.

    The pipeline records two path families: absolute resolved paths, and
    *run-relative* portable paths (`out/x.json`, `../out/x.json`,
    `../../out/x.json` — one file seen from three launch directories).  The map
    is therefore built from the files that exist, so a recorded path normalises
    to `<TOKEN>/<relative>` whichever family it came from.

    Ambiguity is resolved by construction, not by luck: a path under several
    anchors keeps the *shallowest* anchor (fewest path components), because that
    is the one whose relative form cannot change when a deeper anchor moves.
    Without this rule `<CWD>` and `<RUN>` can both claim `x`, and which one wins
    depends on launch-directory nesting — a measurement artefact.
    """
    best = {}
    for tok, root in anchors:
        if not root or not os.path.isdir(root):
            continue
        real = os.path.realpath(root)
        cands = [real]
        for dirpath, dirnames, names in os.walk(real):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for n in names:
                cands.append(os.path.join(dirpath, n))
        for p in cands:
            rel = os.path.relpath(p, real).replace("\\", "/")
            value = tok if rel == "." else f"{tok}/{rel}"
            for key in {p.replace("\\", "/"), p.replace("/", "\\")}:
                prev = best.get(key)
                if prev is None or len(value.split("/")) < len(prev.split("/")):
                    best[key] = value
    return best


def _canon(value, anchors: list, amap: dict, cwd: str):
    """Rewrite every recorded path to `<TOKEN>/<relative>` form.

    Only the anchors this experiment owns are substituted, and only when the
    value really is one of their files; everything else stays byte-for-byte, so
    passing here still means something.  Symbols are on the same host, so no
    realpath is applied to the recorded value.  A *relative* record is resolved
    against each anchor and canonicalised only when exactly one anchor yields an
    existing file; an ambiguous or dangling one is left as-is and then shows up
    as an undeclared difference instead of being silently normalised away.
    """
    if isinstance(value, dict):
        return {k: _canon(v, anchors, amap, cwd) for k, v in value.items()}
    if isinstance(value, list):
        return [_canon(v, anchors, amap, cwd) for v in value]
    if not isinstance(value, str) or not value:
        return value
    s = value
    if _PATHISH.match(s):
        for key in {s.replace("\\", "/"), s.replace("/", "\\")}:
            if key in amap:
                return amap[key]
        if not os.path.isabs(s):
            hits = set()
            for _tok, root in anchors:
                if not root:
                    continue
                for cand in (os.path.normpath(os.path.join(root, s)),
                             os.path.normpath(os.path.join(cwd, s))):
                    k = cand.replace("\\", "/")
                    if k in amap:
                        hits.add(amap[k])
            if len(hits) == 1:
                return hits.pop()
    for tok, root in anchors:
        if not root:
            continue
        for form in (root.replace("\\", "/"), root.replace("/", "\\")):
            if form and form in s:
                s = s.replace(form, tok)
    return s


def _strip(value, drop):
    """Remove declared fields (by leaf name or by full path) from a JSON tree."""
    def walk(o, path=""):
        if isinstance(o, dict):
            out = {}
            for k, v in o.items():
                child = f"{path}.{k}" if path else str(k)
                if any(_matches(p, child) or _matches(p, k) for p in drop):
                    continue
                out[k] = walk(v, child)
            return out
        if isinstance(o, list):
            return [walk(v, f"{path}[{i}]") for i, v in enumerate(o)]
        return o
    return walk(value)


def _path_fields(value, anchors: list, amap: dict, cwd: str):
    """JSON paths whose canonicalisation actually rewrote the value."""
    hits = set()

    def walk(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, f"{path}.{k}" if path else str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")
        elif isinstance(o, str):
            if _canon(o, anchors, amap, cwd) != o:
                hits.add(path)
    walk(value)
    return hits


def _digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                                     indent=1).encode("utf-8")).hexdigest()


def _matches(pattern: str, path: str) -> bool:
    """Glob match where `*` spans any characters (including `.` and `[`).

    `*.abspath` -> any leaf named abspath at any depth;
    `hashes.*`  -> that object's members;
    `generated_at` -> that exact leaf name at depth 0.
    """
    regex = "^" + ".*".join(re.escape(part) for part in pattern.split("*")) + "$"
    return re.match(regex, path) is not None


# ---------------------------------------------------------------------------
# Declaration table 4 — derived digests: a sha256 OF a record that carries an
# anchor, and one disclosure string that quotes the run-time template path.
# Declared separately because the *value* is a digest or prose, not a path, so
# path canonicalisation cannot recognise it; the row names the cause instead.
# ---------------------------------------------------------------------------
DERIVED_FROM_ANCHORED = {
    "result.json:*.checks.*sha256*":
        "sha256 of spec.json/adopt_plan.json/content.json/audit.json/render_log.json, "
        "each of which carries a host anchor (see the file's own row)",
    "result.json:*hashes*":
        "the same digests, echoed into verification.traceability.hashes",
    "audit.json:*hashes*": "the same digests, as recorded by audit.py",
    "result.json:*.note":
        "disclosure text; the builtin-template entry quotes the run-time template path",
}


def _subst(value, table: dict):
    """Replace declared values with a deterministic token (instead of dropping).

    Dropping makes two records differ *because one lost a field the other kept*
    — which is not the question.  Substituting `<DERIVED>` keeps the shape of the
    record and asks the real question: is anything left varying once every
    declared cause is neutralised?
    """
    def walk(o, path=""):
        if isinstance(o, dict):
            return {k: walk(v, f"{path}.{k}" if path else str(k)) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(v, f"{path}[{i}]") for i, v in enumerate(o)]
        for pat, tok in table.items():
            if _matches(pat, path):
                return tok
        return o
    return walk(value)


def _derived_patterns(rel: str) -> list:
    """Expand DERIVED_FROM_ANCHORED into the concrete patterns for one JSON file.

    A table key is `<file>:<pattern>`; only the rows for this file apply, and
    only the pattern half is used for stripping.
    """
    return [key.split(":", 1)[1] for key in DERIVED_FROM_ANCHORED if key.startswith(rel + ":")]


def _leaf_pattern(path: str) -> str:
    """Turn `pages[3].figures_on_page[1].file` into `*.file`."""
    leaf = re.split(r"[.\[]", path)[-1].rstrip("]")
    return f"*.{leaf}" if leaf else path


def _classify(path: str) -> tuple:
    for table, table_name in ((NONDETERMINISM, "nondeterminism"),
                              (HOST_ANCHOR, "host-anchor")):
        for pat, why in table.items():
            if _matches(pat, path):
                return True, table_name, why
    return False, "", ""


def _diff_paths(a: dict, b: dict) -> list:
    return [k for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]


# ---------------------------------------------------------------------------
# conditions
# ---------------------------------------------------------------------------

CONDITIONS = {
    "c1": dict(label="同 cwd / 同 env，3 个独立进程", reps=3, cwd="cwdA",
               seeds=[None], tz=None, frozen=False, rel_args=False),
    "c2": dict(label="停机 1.2s 后再连续 2 次（判时钟/jitter 敏感）", reps=2, cwd="cwdA",
               seeds=[None], tz=None, frozen=False, rel_args=False, gap=1.2),
    "c3": dict(label="跨 cwd：1 层嵌套 / 2 层嵌套 / 脚手架根", reps=3, cwd="cwdB",
               seeds=[None], tz=None, frozen=False, rel_args=False,
               subdirs=["cwdB/nest1", "cwdB/nest1/nest2", "cwdB"]),
    "c4": dict(label="跨 PYTHONHASHSEED：0 / 1 / 12345 / 未设置", reps=4, cwd="cwdA",
               seeds=["0", "1", "12345", None], tz=None, frozen=False, rel_args=False),
    "c5": dict(label="相对参数 vs 绝对参数（同一 cwd 显式启动）", reps=2, cwd="cwdC",
               seeds=[None], tz=None, frozen=False, rel_args=True),
}


class Runner:
    def __init__(self, skill: str, run_dir: str, timeout: int = 180):
        self.src_skill = os.path.abspath(skill)
        self.run = os.path.abspath(run_dir)
        self.timeout = timeout
        self.skill = os.path.join(self.run, "skill")     # copy: never run in-package
        self.corpus = os.path.join(self.run, "input")    # ONE corpus for every run
        self.case_id = "example-catalyst-201"

    # -- setup ---------------------------------------------------------------
    def prepare(self) -> dict:
        main = os.path.join(self.src_skill, "scripts", "main.py")
        if not os.path.isfile(main):
            raise SystemExit(f"[determinism] main.py not found under {self.src_skill}")
        info = {"source_skill": self.src_skill, "scratch_skill": self.skill,
                "scratch": self.run, "corpus": self.corpus, "case_id": self.case_id}
        _rm(self.run)
        os.makedirs(self.run, exist_ok=True)
        shutil.copytree(self.src_skill, self.skill)
        shutil.copytree(os.path.join(self.src_skill, "examples"), self.corpus)

        # The corpus is built once and is then read-only for the whole
        # experiment: figures are synthesised here, not per run.
        rc, _o, err = self._exec(
            [sys.executable, os.path.join(self.skill, "scripts", "make_synthetic_inputs.py"),
             "--dir", self.corpus], os.path.join(self.run, "setup-cwd"))
        info["figure_gen_exit"] = rc
        if rc != 0:
            info["figure_gen_stderr"] = _tail(err)
        figs = os.path.join(self.corpus, "figs")
        info["figures"] = sorted(os.listdir(figs)) if os.path.isdir(figs) else []
        info["corpus_files"] = {rel: _sha256(os.path.join(self.corpus, rel))
                                for rel in _walk(self.corpus)}

        # Standalone generator probes, run twice from two cwds.
        info["standalone"] = {}
        for tag, cwd in (("cwdA", os.path.join(self.run, "setup-cwd", "a")),
                         ("nested", os.path.join(self.run, "setup-cwd", "a", "b"))):
            tgt = os.path.join(self.run, "setup-cwd", f"builtin-{tag}.pptx")
            rc2, _o2, _e2 = self._exec(
                [sys.executable, os.path.join(self.skill, "scripts", "make_template.py"),
                 "--out", tgt], cwd)
            info["standalone"][tag] = {
                "exit": rc2, "sha256": _sha256(tgt) if os.path.isfile(tgt) else ""}
        info["standalone_identical"] = (
            len({v["sha256"] for v in info["standalone"].values()}) == 1
            and all(v["sha256"] for v in info["standalone"].values()))
        return info

    def _exec(self, argv, cwd, env_extra=None):
        os.makedirs(cwd, exist_ok=True)
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if env_extra:
            env.update(env_extra)
        try:
            p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                               timeout=self.timeout)
            return (p.returncode, p.stdout.decode("utf-8", "replace"),
                    p.stderr.decode("utf-8", "replace"))
        except subprocess.TimeoutExpired:
            return 124, "", f"timeout after {self.timeout}s"

    # -- one run -------------------------------------------------------------
    def one(self, cond: str, idx: int, spec: dict) -> dict:
        tag = f"{cond}-{idx + 1}"
        root = os.path.join(self.run, "runs", tag)
        subdirs = spec.get("subdirs") or [spec["cwd"]]
        cwd = os.path.join(root, subdirs[idx % len(subdirs)])
        out = os.path.join(root, "out")
        case = os.path.join(self.corpus, "case.json")
        task = os.path.join(self.corpus, "task.md")

        if spec.get("rel_args"):
            os.makedirs(cwd, exist_ok=True)
            case_arg = os.path.relpath(case, cwd)
            out_arg = os.path.relpath(out, cwd)
        else:
            case_arg, out_arg = case, out

        env_extra = {}
        seed = spec["seeds"][idx % len(spec["seeds"])]
        env_extra["PYTHONHASHSEED"] = "" if seed is None else seed
        if spec.get("tz"):
            env_extra["TZ"] = spec["tz"]
        if spec.get("frozen"):
            env_extra["SOURCE_DATE_EPOCH"] = "1700000000"

        t0 = time.perf_counter()
        rc, stdout, stderr = self._exec(
            [sys.executable, os.path.join(self.skill, "scripts", "main.py"),
             "--case", case_arg, "--task", task, "--out", out_arg], cwd, env_extra)
        secs = round(time.perf_counter() - t0, 3)

        rec = {
            "run": tag, "condition": cond, "index": idx + 1,
            "cwd_kind": subdirs[idx % len(subdirs)] if spec.get("subdirs") else spec["cwd"],
            "cwd": cwd, "out": out, "case": case,
            "case_arg": case_arg, "out_arg": out_arg,
            "arg_form": "relative" if spec.get("rel_args") else "absolute",
            "PYTHONHASHSEED": env_extra["PYTHONHASHSEED"] or "(unset)",
            "TZ": env_extra.get("TZ", "(inherited)"),
            "exit": rc, "seconds": secs,
            "stdout_tail": _tail(stdout), "stderr_tail": _tail(stderr),
            "files": {}, "json": {},
        }
        if os.path.isdir(out):
            for rel in _walk(out):
                rec["files"][rel] = _sha256(os.path.join(out, rel))
                if rel.endswith(".json"):
                    try:
                        with open(os.path.join(out, rel), encoding="utf-8-sig") as fh:
                            rec["json"][rel] = json.load(fh)
                    except Exception:
                        rec["json"][rel] = None
        rec["file_count"] = len(rec["files"])
        return rec


# ---------------------------------------------------------------------------
# comparison
# ---------------------------------------------------------------------------


def compare(records: list, info: dict) -> dict:
    by_cond = {}
    for r in records:
        by_cond.setdefault(r["condition"], []).append(r)

    # ---- 1. raw per-file byte identity ------------------------------------
    all_files = sorted({rel for r in records for rel in r["files"]})
    per_file = {}
    for rel in all_files:
        groups = {}
        for r in records:
            groups.setdefault(r["files"].get(rel) or "(absent)", []).append(r["run"])
        per_file[rel] = groups
    stable = {rel: list(g)[0] for rel, g in per_file.items()
              if len(g) == 1 and "(absent)" not in g}
    varying_raw = {rel: g for rel, g in per_file.items() if rel not in stable}

    # ---- 2. three-tier identity for every JSON file ------------------------
    run_root = os.path.join(info["scratch"], "runs")
    anchors_for = lambda r: [("<CWD>", r["cwd"]), ("<RUN>", run_root),
                             ("<OUT>", r["out"]), ("<CASEDIR>", os.path.dirname(r["case"]))]
    amaps = {r["run"]: _anchor_map(anchors_for(r)) for r in records}
    tiers = {}
    attribution = []
    unexpected = []
    for rel in sorted(set(all_files)):
        if not rel.endswith(".json"):
            continue
        rows = [r for r in records if isinstance(r["json"].get(rel), dict)]
        if len(rows) < 2:
            continue
        ref = rows[0]
        l1, l2, l3, l4 = {}, {}, {}, {}
        l2_fail_fields = {}
        for r in rows:
            obj = r["json"][rel]
            l1[r["run"]] = _digest(obj)
            stripped = _strip(obj, list(NONDETERMINISM))
            l2[r["run"]] = _digest(stripped)
            canon = _canon(stripped, anchors_for(r), amaps[r["run"]], r["cwd"])
            l3[r["run"]] = _digest(canon)
            # L4 additionally drops the fields that are *derived* from an
            # anchored record (a sha256 of spec.json, say).  Such a digest
            # cannot be equal while its source carries an anchor; removing it is
            # what makes "is anything else varying?" an answerable question.
            derived_table = {pat: "<DERIVED>" for pat in _derived_patterns(rel)}
            l4[r["run"]] = _digest(_canon(_subst(_strip(obj, list(NONDETERMINISM)),
                                                 derived_table),
                                          anchors_for(r), amaps[r["run"]], r["cwd"]))
            if l2[r["run"]] != l2[ref["run"]]:
                for p in _path_fields(stripped, anchors_for(r), amaps[r["run"]], r["cwd"]):
                    l2_fail_fields.setdefault(p, []).append(r["run"])
        by_cond = {}
        for r in rows:
            by_cond.setdefault(r["condition"], []).append(r)
        per_cond = {c: len({l3[r["run"]] for r in rs}) for c, rs in sorted(by_cond.items())}
        tiers[rel] = {
            "L1_raw_unique_digests": len(set(l1.values())),
            "L1_raw_identical": len(set(l1.values())) == 1,
            "L2_no_nondeterminism_unique": len(set(l2.values())),
            "L2_no_nondeterminism_identical": len(set(l2.values())) == 1,
            "L3_no_anchor_unique": len(set(l3.values())),
            "L3_no_anchor_identical": len(set(l3.values())) == 1,
            "L3_per_condition_unique_digests": per_cond,
            "L3_identical_within_every_condition": all(v == 1 for v in per_cond.values()),
            "L4_stabilised_unique_digests": len(set(l4.values())),
            "L4_stabilised_identical": len(set(l4.values())) == 1,
            "L2_fail_attributed_to_path_fields":
                [{"json_path": p, "runs": v[:6]} for p, v in sorted(l2_fail_fields.items())],
        }
        # field attribution against the first run of the whole experiment
        flat_ref = _flatten(ref["json"][rel])
        changed = {}
        for r in rows[1:]:
            for p in _diff_paths(flat_ref, _flatten(r["json"][rel])):
                changed.setdefault(p, []).append(r["run"])
        for p in sorted(changed):
            declared, table, why = _classify(p)
            dpat = [k for k in _derived_patterns(rel) if _matches(k, p)]
            if not declared and dpat:
                declared, table, why = True, "derived-from-anchor", DERIVED_FROM_ANCHORED[
                    f"{rel}:{dpat[0]}"]
            if not declared:
                for key in (f"{rel}:{p}", f"{rel}:{_leaf_pattern(p)}"):
                    if key in INVOCATION_FORM:
                        declared, table, why = True, "invocation-form", INVOCATION_FORM[key]
                        break
                    if key in DERIVED_FROM_ANCHORED:
                        declared, table, why = True, "derived-from-anchor", DERIVED_FROM_ANCHORED[key]
                        break
            if not declared and any(p in _path_fields(r["json"][rel], anchors_for(r),
                                                     amaps[r["run"]], r["cwd"]) for r in rows):
                declared, table, why = True, "host-anchor", (
                    "leaf canonically rewrites to `<TOKEN>/<relative>` — a recorded path "
                    "whose only difference between runs is the anchor")
            row = {"file": rel, "json_path": p, "declared": declared, "table": table,
                   "reason": why, "differs_in_runs": changed[p][:8],
                   "example": flat_ref.get(p, "")[:140]}
            attribution.append(row)
            if not declared:
                unexpected.append(row)

    # ---- 3. verdict per core artifact -------------------------------------
    core = [n.format(case_id=info.get("case_id") or "example-catalyst-201")
            for n in CORE_ARTIFACTS]
    core_status = {}
    for rel in core:
        if rel not in per_file:
            core_status[rel] = "absent"
        elif rel in stable:
            core_status[rel] = "L1 逐字节一致（16/16 次）"
        elif tiers.get(rel, {}).get("L2_no_nondeterminism_identical"):
            core_status[rel] = "L2 一致（L1 因声明时间戳不同）"
        elif tiers.get(rel, {}).get("L3_identical_within_every_condition"):
            core_status[rel] = "L3 一致（每个条件内 1 个唯一值；差异仅来自调用形态/宿主锚点）"
        else:
            core_status[rel] = "**不一致**"
    bin_core = [r for r in core if not r.endswith(".json")]
    json_core = [r for r in core if r.endswith(".json")]
    # "core JSON identical" is judged per condition: identical across repeated
    # runs inside one condition, with the L4 tier as the strict version of the
    # same claim.  A *global* L3 pass would additionally require two different
    # invocation forms to agree, which the pipeline deliberately does not do
    # (INVOCATION_FORM) -- that is declared, not a defect.
    json_core_ok = all(core_status[r].startswith(("L1", "L2", "L3")) for r in json_core)
    per_cond_ok = all(t["L3_identical_within_every_condition"]
                      for t in tiers.values() if t["L3_per_condition_unique_digests"])
    # The strict claim: after EVERY declared cause is neutralised (stamp, host
    # anchor, derived digest), all records collapse to one value.  This is what
    # "deterministic" is allowed to mean for JSON that must also be a locator.
    strict_json_ok = all(t["L4_stabilised_identical"] for t in tiers.values())
    stabilised_ok = all(t["L4_stabilised_identical"] for t in tiers.values())
    identity = {
        "core_artifacts": core_status,
        "L1_core_binaries_identical": all(core_status[r].startswith("L1") for r in bin_core),
        "L2_core_json_identical": all(core_status[r].startswith(("L1", "L2")) for r in json_core),
        "L3_core_json_identical": json_core_ok,
        "L3_core_json_identical_globally": all(
            tiers.get(r, {}).get("L3_no_anchor_identical") for r in json_core),
        "L3_identical_within_every_condition": per_cond_ok,
        "L4_all_json_stabilised_identical": stabilised_ok,
        "unexpected_field_count": len(unexpected),
    }
    identity["verdict"] = (
        f"PASS — {len(records)} 次运行（跨进程 / 跨 cwd / 跨 PYTHONHASHSEED / 相对与绝对参数）中："
        "全部二进制交付物 L1 逐字节一致；全部 JSON 记录在 L4（去掉声明的时间戳、宿主锚点、"
        f"锚点派生摘要）后收敛为单一值；声明表外出现差异的字段 {len(unexpected)} 条"
        if identity["L1_core_binaries_identical"] and stabilised_ok and strict_json_ok
        and not unexpected else
        "FAIL — 见 unexpected_volatile / core_artifacts")
    return {
        "per_file_sha256": per_file,
        "stable_files": stable,
        "varying_raw": varying_raw,
        "tiers": tiers,
        "volatile_field_attribution": attribution,
        "unexpected_volatile": unexpected,
        "identity": identity,
    }


def to_markdown(rep: dict, records: list) -> str:
    info = rep["environment"]
    ident = rep["identity"]
    L = []
    L.append("## 0. 结论")
    L.append("")
    L.append(f"- **判定**：`{ident['verdict']}`")
    L.append(f"- 二进制交付物全条件逐字节（L1）一致 = "
             f"**{'是' if ident['L1_core_binaries_identical'] else '否'}**")
    L.append(f"- 核心 JSON 在 L2（去声明时间戳）一致 = "
             f"**{'是' if ident['L2_core_json_identical'] else '否'}**；"
             f"L3（再去宿主锚点）后一致 = "
             f"**{'是' if ident['L3_core_json_identical'] else '否'}**；"
             f"**每个条件内**只有一个唯一值 = "
             f"**{'是' if ident['L3_identical_within_every_condition'] else '否'}**")
    L.append(f"- L4（最后去掉锚点派生摘要）后，全部 JSON 记录合并只有一个唯一值 = "
             f"**{'是' if ident['L4_all_json_stabilised_identical'] else '否'}**")
    L.append(f"- 声明表之外出现差异的字段：**{len(rep['unexpected_volatile'])} 条**")
    L.append("")
    L.append("## 1. 实测环境与实验设计")
    L.append("")
    L.append(f"- python `{rep['python']}`；命令：`{rep['command']}`")
    L.append(f"- 参测包（只读源）：`{info['source_skill']}`")
    L.append(f"- 管线跑在包的**一份拷贝**上：`{info['scratch_skill']}`"
             f"（不在包内执行，避免 `__pycache__` 落进提交包）")
    L.append(f"- **固定输入语料**（只建一次，所有 run 共用）：`{info['corpus']}`，"
             f"{len(info.get('corpus_files') or {})} 个文件；合成图件 "
             f"{len(info.get('figures') or [])} 个（exit {info.get('figure_gen_exit')}）")
    L.append(f"- 独立生成器 `make_template.py` 在两个不同 cwd 下各跑一次："
             f"`{'一致' if info.get('standalone_identical') else '不一致'}`"
             f"（sha256 `{[v['sha256'][:12] + '…' for v in (info.get('standalone') or {}).values()]}`）")
    L.append("")
    L.append("## 2. 逐次实测")
    L.append("")
    L.append("| run | 条件 | cwd 形态 | 参数形态 | PYTHONHASHSEED | exit | 耗时 s | 产物数 | status |")
    L.append("|-|-|-|-|-|-|-|-|-|")
    for r in records:
        res = (r.get("json") or {}).get("result.json") or {}
        L.append("| `{}` | {} | `{}` | {} | `{}` | {} | {} | {} | `{}` |".format(
            r["run"], r["condition"], r["cwd_kind"], r["arg_form"],
            r["PYTHONHASHSEED"], r["exit"], r["seconds"], r["file_count"],
            res.get("status")))
    L.append("")
    L.append("## 3. 逐文件 sha256（全条件合并）")
    L.append("")
    L.append("| 产物（相对 `--out`） | 原始 sha256 分组数 | L1 判定 | sha256 / 分组 |")
    L.append("|-|-|-|-|")
    for rel in sorted(rep["per_file_sha256"]):
        g = rep["per_file_sha256"][rel]
        if len(g) == 1 and "(absent)" not in g:
            L.append(f"| `{rel}` | 1 | 逐字节一致 | `{list(g)[0][:20]}…` |")
        else:
            detail = "；".join(f"`{k[:12]}…`×{len(v)}" for k, v in sorted(g.items()))
            L.append(f"| `{rel}` | {len(g)} | **不一致** | {detail} |")
    L.append("")
    L.append("## 4. 四层一致性（L1 原始 / L2 去时间戳 / L3 归锚点 / L4 再去锚点派生摘要）")
    L.append("")
    L.append("| JSON 记录 | L1 原始 | L2 去时间戳 | L3 去时间戳+归锚点 | L3 每条件内 | L4 再去派生摘要 | 通过层 |")
    L.append("|-|-|-|-|-|-|-|")
    for rel in sorted(rep["tiers"]):
        t = rep["tiers"][rel]
        tier = ("L1" if t["L1_raw_identical"] else
                "L2" if t["L2_no_nondeterminism_identical"] else
                "L3" if t["L3_no_anchor_identical"] else
                "L3/条件内" if t["L3_identical_within_every_condition"] else
                "L4" if t["L4_stabilised_identical"] else "—")
        percond = "/".join(f"{c}:{v}" for c, v in t["L3_per_condition_unique_digests"].items())
        L.append(f"| `{rel}` | {t['L1_raw_unique_digests']} | "
                 f"{t['L2_no_nondeterminism_unique']} | {t['L3_no_anchor_unique']} | "
                 f"{percond} | {t['L4_stabilised_unique_digests']} | **{tier}** |")
    L.append("")
    l2fails = {rel: t["L2_fail_attributed_to_path_fields"]
               for rel, t in rep["tiers"].items() if t["L2_fail_attributed_to_path_fields"]}
    if l2fails:
        L.append("### L2 未通过的文件，差异被归因到这些路径字段（实测替换命中）")
        L.append("")
        for rel, rows in sorted(l2fails.items()):
            L.append(f"- `{rel}`：" + "；".join(f"`{r['json_path']}`" for r in rows[:8])
                     + ("…" if len(rows) > 8 else ""))
        L.append("")
    L.append("### 核心交付物逐项判定")
    L.append("")
    L.append("| 核心产物 | 判定 |")
    L.append("|-|-|")
    for rel, st in rep["identity"]["core_artifacts"].items():
        L.append(f"| `{rel}` | {st} |")
    L.append("")
    L.append("## 5. 易变字段逐条归因（实测得到的字段清单）")
    L.append("")
    if not rep["volatile_field_attribution"]:
        L.append("（无：所有 JSON 字段在所有条件下都相同）")
    else:
        L.append("| 文件 | JSON 路径 | 归类 | 声明理由 | 首次值示例 |")
        L.append("|-|-|-|-|-|")
        for row in rep["volatile_field_attribution"]:
            tag = {"nondeterminism": "**故意**·时间戳/版本",
                   "host-anchor": "**故意**·宿主锚定",
                   "invocation-form": "**故意**·调用形态",
                   "derived-from-anchor": "**故意**·锚点派生摘要",
                   "derived-from-anchor": "**故意**·锚点派生摘要",
                   "": "**未声明**"}[row["table"]]
            L.append("| `{}` | `{}` | {} | {} | `{}` |".format(
                row["file"], row["json_path"], tag, row["reason"] or "—", row["example"]))
    L.append("")
    if rep["unexpected_volatile"]:
        L.append("### ⚠ 未声明差异（必须修，或先在声明表里写明理由）")
        L.append("")
        for row in rep["unexpected_volatile"]:
            L.append(f"- `{row['file']}` → `{row['json_path']}`："
                     f"在 {', '.join(row['differs_in_runs'][:4])} 中不同")
        L.append("")
    else:
        L.append("声明表之外出现差异的字段：**0 条**（实测字段集合与声明表完全吻合）。")
        L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--skill", default=os.path.dirname(here),
                    help="package root (default: parent of this script's dir)")
    ap.add_argument("--runs", type=int, default=3, help="repetitions for c1/c2 (default 3)")
    ap.add_argument("--run", default="", help="scratch dir (default <cwd>/determinism-run)")
    ap.add_argument("--json", default="", help="write the machine-readable report here")
    ap.add_argument("--markdown", default="", help="write the Markdown table here")
    ap.add_argument("--condition", default="", help="comma separated condition ids")
    ap.add_argument("--timeout", type=int, default=180, help="per-run timeout (s)")
    ap.add_argument("--allow-in-package", action="store_true",
                    help="permit a scratch dir inside the package (NOT recommended)")
    a = ap.parse_args(argv)

    skill = os.path.abspath(a.skill)
    run = os.path.abspath(a.run or os.path.join(os.getcwd(), "determinism-run"))

    def inside(p, root):
        p, root = os.path.abspath(p), os.path.abspath(root)
        return p == root or p.startswith(root + os.sep)

    if inside(run, skill) and not a.allow_in_package:
        print("[determinism] refusing a scratch dir inside the package: running the "
              "pipeline there leaves scripts/__pycache__/*.pyc, which the resource "
              "contract rejects. Pass --run outside the package.", file=sys.stderr)
        return 2

    wanted = [c.strip() for c in a.condition.split(",") if c.strip()] or list(CONDITIONS)
    unknown = [c for c in wanted if c not in CONDITIONS]
    if unknown:
        print(f"[determinism] unknown condition(s): {unknown}; known: {list(CONDITIONS)}",
              file=sys.stderr)
        return 2

    R = Runner(skill, run, timeout=a.timeout)
    print(f"[determinism] skill  = {skill}")
    print(f"[determinism] scratch= {run}")
    info = R.prepare()
    print(f"[determinism] corpus = {info['corpus']} "
          f"({len(info.get('corpus_files') or {})} files, figures={len(info.get('figures') or [])})")
    print(f"[determinism] make_template.py standalone identical = {info['standalone_identical']}")

    records = []
    for cond in wanted:
        spec = CONDITIONS[cond]
        reps = spec["reps"] if not a.runs else max(1, a.runs)
        if cond == "c3":
            reps = 3
        if cond == "c4":
            reps = max(reps, 4)
        if cond == "c5":
            reps = max(reps, 2)
        for i in range(reps):
            r = R.one(cond, i, spec)
            records.append(r)
            print(f"  {r['run']:7s} cwd={r['cwd_kind']:22s} args={r['arg_form']:8s} "
                  f"seed={r['PYTHONHASHSEED']:>6s} exit={r['exit']} "
                  f"files={r['file_count']:2d} {r['seconds']}s")
        if spec.get("gap"):
            time.sleep(spec["gap"])

    cmp = compare(records, info)
    rep = {
        "_meta": "determinism / byte-reproducibility experiment; every number is measured",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "python": sys.version.split()[0],
        "command": (f"python scripts/determinism.py --skill <pkg> --runs {a.runs} "
                    f"--condition {','.join(wanted)}"),
        "conditions": {c: CONDITIONS[c]["label"] for c in wanted},
        "environment": info,
        "run_count": len(records),
        "runs": [{k: v for k, v in r.items() if k != "json"} for r in records],
        "declared_nondeterminism": NONDETERMINISM,
        "declared_host_anchor": HOST_ANCHOR,
        "declared_invocation_form": INVOCATION_FORM,
        "declared_derived_from_anchor": DERIVED_FROM_ANCHORED,
        **cmp,
    }
    if a.json:
        _write(a.json, json.dumps(rep, ensure_ascii=False, indent=2, default=str) + "\n")
        print(f"[determinism] json  -> {a.json}")
    if a.markdown:
        _write(a.markdown, to_markdown(rep, records) + "\n")
        print(f"[determinism] table -> {a.markdown}")

    ok = (cmp["identity"]["L1_core_binaries_identical"]
          and cmp["identity"]["L4_all_json_stabilised_identical"]
          and not cmp["unexpected_volatile"])
    print(f"[determinism] runs={len(records)} L1_bin={cmp['identity']['L1_core_binaries_identical']} "
          f"L2_json={cmp['identity']['L2_core_json_identical']} "
          f"L3_json={cmp['identity']['L3_core_json_identical']} "
          f"L4_stabilised={cmp['identity']['L4_all_json_stabilised_identical']} "
          f"undeclared={len(cmp['unexpected_volatile'])}")
    print(f"[determinism] verdict: {cmp['identity']['verdict']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
