#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""determinism.py — byte-level reproducibility probe for the paper-to-ppt Skill.

Axis of this package (v7): **same input -> same bytes**. The probe runs the real
end-to-end entry (``scripts/main.py``) N times **in separate processes**, with
**different working directories** and **different ``PYTHONHASHSEED`` values**,
hashes every produced artifact, and classifies every difference it finds.

Why one process per run: an in-process loop shares import state, ``sys.path``
and the hash seed, so it could not tell "the pipeline is deterministic" from
"the interpreter reused one warm process". Cross-process, cross-cwd and
cross-seed are exactly the three conditions under which a reviewer or the
platform regenerates the delivered artifact set.

Classification model (the important part)
-----------------------------------------
Differences are never silently normalised. Each one is either **explained** by
a rule fixed in code, or reported as a failure:

* ``timestamp`` / ``duration`` — wall-clock fields (``change_records[].time``,
  ``run_meta.timestamp``, ``run_meta.duration_seconds``).
* ``out-dir-identity`` — a field whose value is the *output location*, e.g.
  ``/charts/<i>/chart/file`` records the absolute path of the chart this run
  wrote into ``--out``. The probe verifies this by rewriting each run's own
  ``--out`` prefix and re-comparing; if the values differ by anything else,
  the pointer stays unexplained. (``--out-mode same-dir`` removes this class
  entirely: it is output-location identity, not nondeterminism.)
* ``zip-member-mtime`` — ``zipfile.ZipFile.writestr(<str name>)`` stamps each
  container member with the current local time (hence the .pptx bytes differ).
* ``svg-dc-date`` — matplotlib's SVG backend writes the render time into
  ``<dc:date>``.
* ``svg-generated-id`` — matplotlib's SVG backend derives element ids
  (``id="m5485b5e622"``) from ``rcParams['svg.hashsalt']``, which defaults to a
  **fresh uuid per render**, so every id differs per process. The probe
  measures the ids and offers two ways out: canonical renaming (order-based) and
  the root-cause knob ``--svg-hashsalt`` (fixes the salt in the child process).

Answers the report gives
------------------------
1. ``identical``            — raw bytes equal across runs? (expected False)
2. ``identical_canonical``  — equal after the *documented* normalisation only?
3. ``identical_stabilized`` — with ``--stabilize``: the probe physically
   rewrites the volatile parts (fixed zip date_time, dropped ``<dc:date>``,
   renamed SVG ids, dropped PNG ``tIME``, canonical JSON with explained
   pointers replaced) and compares the rewritten bytes. This is the strong
   claim: the delivered set can be *made* byte-identical.

Usage
-----
    python "$SKILL_DIR/scripts/determinism.py" --out <dir> [--runs 5] \\
        [--case <case.json>] [--spec <deck-spec.json>] [--task <task.md>] \\
        [--out-mode per-run|same-dir] [--stabilize] [--svg-hashsalt <salt>] \\
        [--no-timestamp] [--json <report.json>] [--quiet]

Defaults: ``--case`` / ``--spec`` / ``--task`` fall back to the packaged
``examples/`` case, so the probe runs standalone. Children are started with
``PYTHONDONTWRITEBYTECODE=1``, so probing never leaves ``__pycache__`` inside
the Skill directory.

Exit codes
----------
    0  every run exited 0 and the canonical artifact sets are identical
       (with ``--stabilize``: the stabilized sets are byte-identical too)
    1  non-determinism: unexplained differences, or canonical sets differ,
       or stabilized sets differ
    2  parameter/input error (bad --runs/--seeds/--out-mode, unreadable case)
    3  at least one child run failed (non-zero exit, or no result.json)
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
DEFAULT_ENTRY = os.path.join(HERE, "main.py")

SCHEMA = "determinism-report/1"
FIXED_ZIP_DT = (1980, 1, 1, 0, 0, 0)
JSON_PLACEHOLDERS = {"timestamp": "<volatile:timestamp>",
                     "duration": "<volatile:duration>",
                     "out-dir-identity": "<OUT>"}

STATIC_JSON_VOLATILE = [
    (re.compile(r"^/change_records/\d+/time$"), "timestamp",
     "wall-clock written by time.strftime in main.run()"),
    (re.compile(r"^/run_meta/timestamp$"), "timestamp",
     "wall-clock written by main._run_meta()"),
    (re.compile(r"^/run_meta/duration_seconds$"), "duration",
     "wall-clock duration of the run"),
]

# Pointers that identify the *inputs*; a difference here means the runs did not
# share inputs, which is a probe error rather than a property of the Skill.
INPUT_IDENTITY_JSON_POINTERS = [
    re.compile(r"^/run_meta/case_file$"),
    re.compile(r"^/spec_source$"),
    re.compile(r"^/sources/\d+/path$"),
    re.compile(r"^/run_meta/preview_font$"),
]

ARTIFACT_CLASSES = [
    (re.compile(r"\.zip$|\.pptx$|\.docx$|\.xlsx$"), "zip-container"),
    (re.compile(r"\.svg$"), "svg-xml"),
    (re.compile(r"\.png$"), "png"),
    (re.compile(r"\.json$"), "json"),
    (re.compile(r"\.md$|\.txt$|\.csv$|\.ya?ml$"), "text"),
]

BOOTSTRAP_SRC = """
import os, runpy, sys
salt = os.environ.get("SKILL_SVG_HASHSALT")
if salt:
    try:
        import matplotlib
        matplotlib.rcParams["svg.hashsalt"] = salt
    except Exception:
        pass
entry = sys.argv[1]
sys.argv = sys.argv[1:]
runpy.run_path(entry, run_name="__main__")
"""


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def artifact_class(rel):
    for rx, name in ARTIFACT_CLASSES:
        if rx.search(rel):
            return name
    return "other"


# --------------------------------------------------------------------------- #
# JSON helpers
# --------------------------------------------------------------------------- #
def json_pointer_diff(a, b, prefix=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = "%s/%s" % (prefix, str(k).replace("~", "~0").replace("/", "~1"))
            if k not in a or k not in b:
                out.append(p)
            else:
                out.extend(json_pointer_diff(a[k], b[k], p))
    elif isinstance(a, list) and isinstance(b, list):
        for i in range(max(len(a), len(b))):
            p = "%s/%d" % (prefix, i)
            if i >= len(a) or i >= len(b):
                out.append(p)
            else:
                out.extend(json_pointer_diff(a[i], b[i], p))
    else:
        if a != b:
            out.append(prefix or "/")
    return out


def json_pointer_get(doc, pointer):
    cur = doc
    for token in pointer.strip("/").split("/"):
        if token == "":
            continue
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, list):
            if not token.isdigit() or int(token) >= len(cur):
                return None
            cur = cur[int(token)]
        elif isinstance(cur, dict):
            if token not in cur:
                return None
            cur = cur[token]
        else:
            return None
    return cur


def json_pointer_set(doc, pointer, value):
    tokens = [t.replace("~1", "/").replace("~0", "~")
              for t in pointer.strip("/").split("/") if t != ""]
    cur = doc
    for token in tokens[:-1]:
        cur = cur[int(token)] if isinstance(cur, list) else cur[token]
    last = tokens[-1]
    if isinstance(cur, list):
        cur[int(last)] = value
    else:
        cur[last] = value


def canonical_json_bytes(doc):
    return json.dumps(doc, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def strip_out_dir(value, out_dir):
    """Rewrite one run's own output-directory prefix; used to *verify* that a
    differing value is output-location identity and nothing else.

    Windows mixes separators here (``os.path.join`` on a forward-slash ``--out``
    yields ``a/b\\run-0``), so both sides are normalised to ``/`` before the
    prefix test — otherwise a genuine out-dir field would look unexplained.
    """
    if not isinstance(value, str) or not out_dir:
        return value
    norm = value.replace("\\", "/")
    for variant in {out_dir, out_dir.replace("\\", "/"), out_dir.replace("/", "\\")}:
        nvar = variant.replace("\\", "/")
        if nvar and nvar in norm:
            norm = norm.replace(nvar, "<OUT>")
    return norm


def normalise_json(doc, explained, rules, out_dir):
    """Return a copy with *explained* volatile pointers replaced. Unexplained
    differences are deliberately left untouched so they still show up."""
    out = json.loads(json.dumps(doc))
    for ptr, kind in explained:
        if kind == "out-dir-identity":
            cur = json_pointer_get(out, ptr)
            if isinstance(cur, str):
                json_pointer_set(out, ptr, strip_out_dir(cur, out_dir))
        else:
            json_pointer_set(out, ptr, JSON_PLACEHOLDERS.get(kind, "<volatile>"))
    return out


# --------------------------------------------------------------------------- #
# container canonicalisation / stabilisation
# --------------------------------------------------------------------------- #
def zip_canonical(raw):
    members, dates = {}, {}
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        for info in zf.infolist():
            members[info.filename] = sha256_bytes(zf.read(info.filename))
            dates[info.filename] = "%04d-%02d-%02dT%02d:%02d:%02d" % info.date_time
    digest = sha256_bytes(json.dumps({"members": members, "order": list(members)},
                                     sort_keys=True).encode("utf-8"))
    return digest, members, dates


def zip_stabilized_bytes(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        items = [(i, zf.read(i.filename)) for i in zf.infolist()]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for info, data in items:
            zi = zipfile.ZipInfo(info.filename, date_time=FIXED_ZIP_DT)
            zi.compress_type = info.compress_type
            zi.external_attr = info.external_attr
            zi.internal_attr = info.internal_attr
            zi.create_system = info.create_system
            zout.writestr(zi, data)
    return buf.getvalue()


SVG_DATE_RX = re.compile(r"(<dc:date[^>]*>)([^<]*)(</dc:date>)")
SVG_ID_RX = re.compile(r'(\bid=")([^"]+)(")')
SVG_REF_RX = re.compile(r"#([A-Za-z][A-Za-z0-9_\-]{2,})")


def svg_normalise(raw):
    """Drop <dc:date> content and rename generated element ids in document
    order (ids are opaque labels produced per render; the *sequence* of ids is
    stable, so order-based renaming is a lossless canonical form)."""
    txt = raw.decode("utf-8", "replace")
    dates = [m.group(2) for m in SVG_DATE_RX.finditer(txt)]
    txt = SVG_DATE_RX.sub(lambda m: m.group(1) + "<volatile:date>" + m.group(3), txt)
    ids = []

    def _grab(m):
        ids.append(m.group(2))
        return m.group(1) + "L%d" % (len(ids) - 1) + m.group(3)

    txt = SVG_ID_RX.sub(_grab, txt)
    for i, old in sorted(enumerate(ids), key=lambda kv: -len(kv[1])):
        txt = txt.replace("#" + old, "#L%d" % i)
    return txt.encode("utf-8"), dates, ids


def png_split_chunks(raw):
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    chunks, pos = [], 8
    while pos + 8 <= len(raw):
        ln = int.from_bytes(raw[pos:pos + 4], "big")
        typ = raw[pos + 4:pos + 8]
        end = pos + 8 + ln + 4
        if end > len(raw):
            return None
        chunks.append((typ, raw[pos:pos + 8 + ln], raw[pos + 8 + ln:end]))
        pos = end
        if typ == b"IEND":
            break
    return chunks


def png_canonical_bytes(raw):
    """Canonical PNG bytes: identical to the input unless a tIME chunk exists."""
    chunks = png_split_chunks(raw)
    if chunks is None:
        return raw, False
    had = any(t == b"tIME" for t, _b, _c in chunks)
    if not had:
        return raw, False
    out = bytearray(raw[:8])
    for typ, body, crc in chunks:
        if typ == b"tIME":
            continue
        out += body + crc
    return bytes(out), True


# --------------------------------------------------------------------------- #
# child runs
# --------------------------------------------------------------------------- #
def run_once(python, entry, argv, cwd, seed, hashsalt, timeout):
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = str(seed)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if hashsalt:
        env["SKILL_SVG_HASHSALT"] = hashsalt
    else:
        env.pop("SKILL_SVG_HASHSALT", None)
    os.makedirs(cwd, exist_ok=True)
    if hashsalt:
        cmd = [python, "-c", BOOTSTRAP_SRC, entry] + list(argv)
    else:
        cmd = [python, entry] + list(argv)
    proc = subprocess.run(cmd, cwd=cwd, env=env, timeout=timeout,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    tail = proc.stdout.decode("utf-8", "replace").strip().splitlines()[-6:]
    return proc.returncode, tail


def snapshot(run_dir):
    """Read every artifact of one run into memory (bytes) before the next run
    may overwrite the directory (same-dir mode)."""
    files = {}
    for root, dirs, names in os.walk(run_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for n in sorted(names):
            p = os.path.join(root, n)
            rel = os.path.relpath(p, run_dir).replace("\\", "/")
            with open(p, "rb") as fh:
                files[rel] = fh.read()
    return files


# --------------------------------------------------------------------------- #
# probe
# --------------------------------------------------------------------------- #
def classify_pointers(docs, out_dirs):
    """Split differing JSON pointers into (explained, unexplained)."""
    explained, unexplained, observed_all = [], [], {}
    if not all(d is not None for d in docs):
        return explained, unexplained, observed_all
    base = docs[0]
    seen = set()
    for d in docs[1:]:
        seen.update(json_pointer_diff(base, d))
    for ptr in sorted(seen):
        values = [json_pointer_get(d, ptr) for d in docs]
        observed_all[ptr] = values
        rule = next(((k, why) for rx, k, why in STATIC_JSON_VOLATILE if rx.match(ptr)),
                    None)
        if rule:
            explained.append((ptr, rule[0], rule[1]))
            continue
        if any(rx.match(ptr) for rx in INPUT_IDENTITY_JSON_POINTERS):
            unexplained.append({"pointer": ptr, "kind": "input-identity",
                                "reason": "runs did not share identical inputs — "
                                          "probe error, not Skill nondeterminism",
                                "observed": values})
            continue
        if all(isinstance(v, str) for v in values):
            stripped = {strip_out_dir(v, out_dirs[i]) for i, v in enumerate(values)}
            if len(stripped) == 1:
                explained.append((ptr, "out-dir-identity",
                                  "value is this run's own output location "
                                  "(verified: equal after rewriting the --out prefix)"))
                continue
        unexplained.append({"pointer": ptr, "kind": "unclassified",
                            "reason": "differs between runs and matches no fixed rule",
                            "observed": values})
    return explained, unexplained, observed_all


def redact_paths(obj, pairs):
    """Replace machine-specific absolute paths in the report with placeholders.

    The Skill package itself must not carry local absolute paths, so the copy of
    the report that ships as evidence is redacted. Only path *strings* change:
    every hash, count, boolean and observed value stays exactly as measured.
    """
    if isinstance(obj, dict):
        return {k: redact_paths(v, pairs) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_paths(v, pairs) for v in obj]
    if isinstance(obj, str):
        out = obj
        for needle, token in pairs:
            if not needle:
                continue
            for variant in {needle, needle.replace("\\", "/"),
                            needle.replace("/", "\\")}:
                if variant:
                    out = out.replace(variant, token)
        out = re.sub(r"[A-Za-z]:[\\/]", "<ABS>/", out)
        return out
    return obj


def probe(args, case, spec, task, report_path):
    os.makedirs(args.out, exist_ok=True)
    runs, raw_sets, out_dirs, failures = [], [], [], []
    for i in range(args.runs):
        if args.out_mode == "same-dir":
            run_dir = os.path.join(args.out, "shared-out")
        else:
            run_dir = os.path.join(args.out, "run-%d" % i)
        cwd = run_dir if i % 2 == 0 else os.path.join(args.out, "cwd-alt-%d" % i)
        argv = ["--case", case, "--out", run_dir]
        if task:
            argv += ["--task", task]
        if spec:
            argv += ["--spec", spec]
        rc, tail = run_once(args.python, args.entry, argv, cwd,
                            args.seed_list[i % len(args.seed_list)],
                            args.svg_hashsalt, args.timeout)
        raw = snapshot(run_dir)
        raw_sets.append(raw)
        out_dirs.append(os.path.abspath(run_dir))
        status = None
        if "result.json" in raw:
            try:
                status = json.loads(raw["result.json"].decode("utf-8")).get("status")
            except Exception:
                status = "unreadable"
        else:
            failures.append("run-%d: no result.json" % i)
        if rc != 0:
            failures.append("run-%d: exit %d" % (i, rc))
        runs.append({"index": i, "run_dir": run_dir, "cwd": cwd,
                     "pyhashseed": str(args.seed_list[i % len(args.seed_list)]),
                     "svg_hashsalt": args.svg_hashsalt,
                     "argv": argv, "exit_code": rc, "result_status": status,
                     "files": sorted(raw)})
        if not args.quiet:
            print("[run %d] exit=%d status=%s files=%d cwd=%s seed=%s%s"
                  % (i, rc, status, len(raw), cwd,
                     args.seed_list[i % len(args.seed_list)],
                     " hashsalt=%s" % args.svg_hashsalt if args.svg_hashsalt else ""))

    rels = sorted({rel for raw in raw_sets for rel in raw})
    per_file_sha = {rel: [sha256_bytes(raw[rel]) if rel in raw else None
                          for raw in raw_sets] for rel in rels}
    byte_identical = {rel: len(set(v)) == 1 and None not in v
                      for rel, v in per_file_sha.items()}

    # ---- JSON pointer classification ---------------------------------------
    docs = []
    for raw in raw_sets:
        try:
            docs.append(json.loads(raw.get("result.json", b"null").decode("utf-8")))
        except Exception:
            docs.append(None)
    explained, unexplained, observed = classify_pointers(docs, out_dirs)
    volatile_fields = [{
        "pointer": ptr, "kind": kind, "reason": reason,
        "observed": observed.get(ptr),
        "stabilization": ("output-directory prefix rewritten to <OUT>"
                          if kind == "out-dir-identity" else
                          "replaced by %r" % JSON_PLACEHOLDERS.get(kind)),
    } for ptr, kind, reason in explained]

    # ---- canonical forms ----------------------------------------------------
    per_file_canonical, container_evidence = {}, {"zip": {}, "svg": {}, "png": {}}
    for rel in rels:
        canon = []
        for i, raw in enumerate(raw_sets):
            if rel not in raw:
                canon.append(None)
                continue
            cls = artifact_class(rel)
            data = raw[rel]
            if cls == "zip-container":
                digest, members, dates = zip_canonical(data)
                container_evidence["zip"].setdefault(rel, []).append(
                    {"members": members, "date_time": dates})
                canon.append(digest)
            elif cls == "svg-xml":
                stable, dates, ids = svg_normalise(data)
                container_evidence["svg"].setdefault(rel, []).append(
                    {"dc_date": dates, "ids": ids})
                canon.append(sha256_bytes(stable))
            elif cls == "png":
                stable, had = png_canonical_bytes(data)
                container_evidence["png"].setdefault(rel, []).append({"tIME": had})
                canon.append(sha256_bytes(stable))
            elif cls == "json" and rel == "result.json" and docs[i] is not None:
                norm = normalise_json(docs[i], [(p, k) for p, k, _r in explained],
                                      STATIC_JSON_VOLATILE, out_dirs[i])
                canon.append(sha256_bytes(canonical_json_bytes(norm)))
            else:
                canon.append(sha256_bytes(data))
        per_file_canonical[rel] = canon
    canonical_identical = {rel: len(set(v)) == 1 and None not in v
                           for rel, v in per_file_canonical.items()}

    # ---- per-file volatility evidence --------------------------------------
    volatile_files = []
    for rel in rels:
        if byte_identical.get(rel):
            continue
        cls = artifact_class(rel)
        if cls == "zip-container":
            ev = container_evidence["zip"].get(rel, [])
            distinct = sorted({d for e in ev for d in e["date_time"].values()})
            same_members = all(e["members"] == ev[0]["members"] for e in ev) if ev else None
            volatile_files.append({
                "path": rel, "kind": "zip-member-mtime",
                "reason": "zipfile.ZipFile.writestr(<str name>) stamps every member "
                          "with the current local time",
                "observed_date_time": distinct[:8],
                "member_payloads_identical": same_members,
                "stabilization": "rewrite the container with date_time fixed to %s"
                                 % (FIXED_ZIP_DT,)})
        elif cls == "svg-xml":
            ev = container_evidence["svg"].get(rel, [])
            dates = sorted({d for e in ev for d in e["dc_date"]})
            id_seqs = [e["ids"] for e in ev]
            unstable = 0
            samples = []
            if id_seqs:
                base_ids = id_seqs[0]
                for other in id_seqs[1:]:
                    for k in range(min(len(base_ids), len(other))):
                        if base_ids[k] != other[k]:
                            unstable += 1
                            if len(samples) < 4 and base_ids[k] not in samples:
                                samples.append(base_ids[k])
                    unstable += abs(len(base_ids) - len(other))
            volatile_files.append({
                "path": rel, "kind": "svg-dc-date+svg-generated-id",
                "reason": "matplotlib writes the render time into <dc:date> and "
                          "derives element ids from rcParams['svg.hashsalt'], which "
                          "defaults to str(uuid.uuid4()) per renderer",
                "observed_date_time": dates[:8],
                "ids_per_run": [len(s) for s in id_seqs],
                "id_positions_differing": unstable,
                "identical_id_sequences": unstable == 0 and len(set(map(tuple, id_seqs))) == 1,
                "unstable_id_samples": samples,
                "stabilization": "drop <dc:date> content; rename ids in document "
                                 "order (--svg-hashsalt pins the root cause instead, "
                                 "then only <dc:date> is left)"})
        elif cls == "png":
            had = any(e.get("tIME") for e in container_evidence["png"].get(rel, []))
            volatile_files.append({
                "path": rel, "kind": "png-tIME" if had else "png-byte-diff",
                "reason": "PNG payload differs between runs",
                "observed_date_time": [],
                "stabilization": "drop tIME chunk" if had else
                                 "not stabilizable by the probe — reported, not hidden"})
        elif rel == "result.json":
            volatile_files.append({
                "path": rel, "kind": "json-explained-pointers",
                "reason": "result.json carries the explained pointers listed in "
                          "volatile_fields (and nothing else)",
                "observed_date_time": [],
                "pointers": [v["pointer"] for v in volatile_fields],
                "stabilization": "canonical JSON with the explained pointers replaced"})
        else:
            volatile_files.append({
                "path": rel, "kind": "unclassified-bytes",
                "reason": "text artifact differs between runs",
                "observed_date_time": [],
                "stabilization": "not stabilizable by the probe — reported, not hidden"})

    # ---- stabilized comparison ---------------------------------------------
    stabilized = None
    if args.stabilize:
        stab_dir = os.path.join(args.out, "stabilized")
        per_file, written = {}, 0
        for i, raw in enumerate(raw_sets):
            d = os.path.join(stab_dir, "run-%d" % i)
            for rel, data in raw.items():
                cls = artifact_class(rel)
                if cls == "zip-container":
                    out = zip_stabilized_bytes(data)
                elif cls == "svg-xml":
                    out = svg_normalise(data)[0]
                elif cls == "png":
                    out = png_canonical_bytes(data)[0]
                elif cls == "json" and rel == "result.json" and docs[i] is not None:
                    norm = normalise_json(docs[i], [(p, k) for p, k, _r in explained],
                                          STATIC_JSON_VOLATILE, out_dirs[i])
                    out = (json.dumps(norm, ensure_ascii=False, indent=2)
                           + "\n").encode("utf-8")
                else:
                    out = data
                p = os.path.join(d, rel.replace("/", os.sep))
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "wb") as fh:
                    fh.write(out)
                written += 1
                per_file.setdefault(rel, []).append(sha256_bytes(out))
        identical_stab = {rel: len(set(v)) == 1 for rel, v in per_file.items()}
        stabilized = {"dir": stab_dir, "files_written": written,
                      "per_file_sha256": per_file,
                      "identical_per_file": identical_stab,
                      "identical": all(identical_stab.values()) and bool(identical_stab)}

    identical = all(byte_identical.values()) and bool(byte_identical)
    identical_canonical = (all(canonical_identical.values())
                           and bool(canonical_identical) and not unexplained)
    svg_entries = [v for v in volatile_files if str(v["kind"]).startswith("svg")]
    svg_id_stable = (all(v.get("identical_id_sequences") for v in svg_entries)
                     if svg_entries else None)
    if stabilized:
        verdict_ok = stabilized["identical"] and not unexplained
    else:
        verdict_ok = identical_canonical

    report = {
        "schema": SCHEMA,
        "tool": "scripts/determinism.py",
        "entry": args.entry,
        "case": case,
        "spec": spec,
        "task": task,
        "python": args.python,
        "runs_requested": args.runs,
        "out_mode": args.out_mode,
        "svg_hashsalt": args.svg_hashsalt,
        "conditions": {
            "separate_processes": True,
            "cwd_per_run": [r["cwd"] for r in runs],
            "pyhashseed_per_run": [r["pyhashseed"] for r in runs],
            "child_env": {"PYTHONDONTWRITEBYTECODE": "1",
                          "SKILL_SVG_HASHSALT": args.svg_hashsalt},
        },
        "runs": runs,
        "per_file_sha256": per_file_sha,
        "per_file_canonical_sha256": per_file_canonical,
        "byte_identical_per_file": byte_identical,
        "canonical_identical_per_file": canonical_identical,
        "identical": identical,
        "identical_canonical": identical_canonical,
        "identical_stabilized": (stabilized["identical"] if stabilized else None),
        "svg_id_sequences_stable": svg_id_stable,
        "stabilized": stabilized,
        "volatile_fields": volatile_fields,
        "volatile_files": volatile_files,
        "unexplained_diffs": unexplained,
        "failures": failures,
        "verdict": ("deterministic (canonical)"
                    if verdict_ok else
                    "NON-DETERMINISTIC or unexplained difference — see "
                    "unexplained_diffs / stabilized"),
    }
    if not args.no_timestamp:
        import time
        report["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    if args.redact_paths:
        pairs = [(os.path.abspath(args.out), "<PROBE_DIR>"),
                 (os.path.abspath(SKILL_DIR), "<SKILL_DIR>"),
                 (os.path.dirname(os.path.abspath(case)), "<CASE_DIR>"),
                 (args.python, "<PYTHON>")]
        report["_redaction"] = {
            "applied": True,
            "replaced": ["<PROBE_DIR>", "<SKILL_DIR>", "<CASE_DIR>", "<PYTHON>",
                         "<ABS> (any remaining drive-letter path)"],
            "note": "only path strings were replaced; every hash, count, boolean "
                    "and observed value is the measured one",
        }
        report = redact_paths(report, pairs)
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    if not args.quiet:
        print("-" * 64)
        print("report       : %s" % report_path)
        print("identical    : %s (raw bytes) | canonical: %s%s"
              % (identical, identical_canonical,
                 " | stabilized: %s" % stabilized["identical"] if stabilized else ""))
        print("volatile     : %d explained json pointer(s), %d file(s), %d unexplained"
              % (len(volatile_fields), len(volatile_files), len(unexplained)))
        print("verdict      : %s" % report["verdict"])
    if failures:
        return 3
    return 0 if verdict_ok else 1


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(
        description="byte-level reproducibility probe (same input -> same bytes?)")
    ap.add_argument("--case", default=None, help="case.json (default: packaged examples)")
    ap.add_argument("--spec", default=None, help="deck-spec.json (default: packaged examples)")
    ap.add_argument("--task", default=None, help="task.md (optional)")
    ap.add_argument("--out", required=True, help="probe dir (report + run-*/ + stabilized/)")
    ap.add_argument("--runs", type=int, default=3, help="number of runs (default 3)")
    ap.add_argument("--out-mode", choices=("per-run", "same-dir"), default="per-run",
                    help="one output dir per run (exercises out-dir identity) or a "
                         "single shared dir (default per-run)")
    ap.add_argument("--svg-hashsalt", default=None,
                    help="fix matplotlib's svg.hashsalt in the children (root-cause "
                         "knob for the random SVG element ids)")
    ap.add_argument("--python", default=sys.executable, help="interpreter for the child runs")
    ap.add_argument("--entry", default=DEFAULT_ENTRY, help="entry (default scripts/main.py)")
    ap.add_argument("--seeds", default="0,1,2", help="comma-separated PYTHONHASHSEED values")
    ap.add_argument("--timeout", type=int, default=900, help="per-run timeout in seconds")
    ap.add_argument("--stabilize", action="store_true",
                    help="also write stabilized copies and compare them byte-wise")
    ap.add_argument("--no-timestamp", action="store_true",
                    help="omit generated_at so two reports are comparable")
    ap.add_argument("--redact-paths", action="store_true",
                    help="replace machine-specific absolute paths in the report "
                         "with <PROBE_DIR>/<SKILL_DIR>/<CASE_DIR>/<PYTHON>/<ABS> "
                         "placeholders (hashes and counts are untouched) — use this "
                         "when the report is shipped inside the Skill package")
    ap.add_argument("--json", default=None,
                    help="report path (default <out>/determinism_report.json)")
    ap.add_argument("--quiet", action="store_true", help="only write the report")
    args = ap.parse_args(argv)

    if args.runs < 2:
        print("--runs must be >= 2 (a single run cannot show reproducibility)",
              file=sys.stderr)
        return 2
    try:
        args.seed_list = [int(s) for s in str(args.seeds).split(",") if s.strip() != ""]
    except ValueError:
        print("--seeds must be a comma-separated list of integers", file=sys.stderr)
        return 2
    if not args.seed_list:
        args.seed_list = [0]
    if not os.path.isfile(args.entry):
        print("entry not found: %s" % args.entry, file=sys.stderr)
        return 2
    case = args.case or os.path.join(SKILL_DIR, "examples", "case.json")
    spec = args.spec or os.path.join(SKILL_DIR, "examples", "deck-spec.json")
    task = args.task or os.path.join(SKILL_DIR, "examples", "task.md")
    for label, p in (("--case", case), ("--spec", spec)):
        if not os.path.isfile(p):
            print("%s not readable: %s" % (label, p), file=sys.stderr)
            return 2
    if not os.path.isfile(task):
        task = None
    report_path = args.json or os.path.join(args.out, "determinism_report.json")
    try:
        return probe(args, case, spec, task, report_path)
    except subprocess.TimeoutExpired as exc:
        print("a child run exceeded the timeout: %s" % exc, file=sys.stderr)
        return 3


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    sys.exit(main())
