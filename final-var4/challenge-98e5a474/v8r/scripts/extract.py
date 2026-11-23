#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Material → candidate ER manifest extractor (draft generator).

High-score pipeline role `extract`: turn source text (md/txt) and data
tables (csv) into a DRAFT entity-relation manifest that the agent then
reviews and confirms. The extractor NEVER invents material: every
candidate is anchored to a real file + line, and every item is tagged
`_draft:true` + `confidence` so nothing can be mistaken for a final
answer (the final manifest is written by the agent and validated by
scripts/spec_lint.py at CP1).

What it extracts (deterministic, stdlib-only):
* entities   — **bold** tokens in Markdown and tabular entity rows,
                each with source + evidence(quote of the line) + _line;
* relations  — sentences that join two entity-name candidates with a
                verb from the canonical vocabulary (activation /
                inhibition / recruitment / process / transcriptional /
                causal / containment), direction taken from the verb;
* groups     — Markdown section headers (## / ###) as group hints;
* data       — CSV tables → {columns, rows} + unit/axis hints.

Usage:
    python scripts/extract.py --inputs <material...> --out draft.json
    python scripts/extract.py --inputs examples/sources/figure03-note.md \
        --out /tmp/draft.json     # example (draft, review required)

Only the Python standard library is required.
"""

import argparse
import csv
import io
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from manifest import canonical_kind, CANONICAL_KINDS  # noqa: E402

try:  # narrow Windows consoles (GBK) must not crash --help or log output
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except Exception:
    pass


BOLD = re.compile(r"\*\*([^*]{1,60}?)\*\*")
SECTION = re.compile(r"^(#{1,4})\s+(.*)$")
TABLE_ROW = re.compile(r"^\s*\|")
WORDY = re.compile(r"^[\w\u4e00-\u9fff][\w\s\u4e00-\u9fff\-\.\+/()（）:：μµ××→]*$")


def _split_sentences(text):
    return re.split(r"(?<=[。！？.!?])\s*", text)


def _token_ok(tok):
    return bool(tok) and len(tok) >= 2 and WORDY.match(tok) and \
        not re.match(r"^[\d\s\.,-]+$", tok)


def _read_lines(path):
    """Read a file as UTF-8 text lines; tolerate common encodings."""
    for enc in ("utf-8-sig", "utf-8", "gb18030", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as fh:
                return fh.read().splitlines()
        except UnicodeDecodeError:
            continue
    with open(path, "r", encoding="latin-1") as fh:
        return fh.read().splitlines()


def _parse_table(lines, start):
    """Parse a markdown table starting at `start`; returns (dict_header,
    rows, end_index) or None."""
    rows = []
    for i in range(start, len(lines)):
        ln = lines[i]
        if not TABLE_ROW.match(ln):
            break
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        rows.append(cells)
    if len(rows) >= 2 and re.match(r"^[\s:\-|]+$", lines[start + 1].strip()
                                   if start + 1 < len(lines) else ""):
        header = [h.strip().lstrip("|").strip() for h in
                  lines[start].strip().strip("|").split("|")]
        data = rows[2:]
        return header, data, start + len(rows)
    return None


def _parse_csv_text(text, path_rel):
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(text[:4096])
    except Exception:
        dialect = csv.excel
    reader = csv.reader(io.StringIO(text), dialect)
    rows = [list(r) for r in reader]
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        return None
    header = [c.strip() for c in rows[0]]
    data = rows[1:]
    return {"header": header, "rows": [
        [c.strip() for c in row] for row in data], "source": path_rel}


def extract_file(path, path_rel):
    """Return a dict of draft items for one material file."""
    lines = _read_lines(path)
    text = "\n".join(lines)
    out = {"entities": [], "relations": [], "groups": [], "data": [],
           "notes": []}
    ents_by_line = {}

    # --- entities from **bold** tokens (Markdown emphasis = key terms) ---
    for ln_no, ln in enumerate(lines, 1):
        for tok in BOLD.findall(ln):
            tok = tok.strip()
            if not _token_ok(tok):
                continue
            oid = "E%d" % (len(out["entities"]) + 1)
            out["entities"].append({
                "id": oid, "name": tok, "type": "entity",
                "source": path_rel, "evidence": ln.strip()[:160],
                "_line": ln_no, "_draft": True, "confidence": "strong",
            })
            ents_by_line.setdefault(ln_no, []).append((oid, tok))

    # --- entities / data from Markdown tables ---
    i = 0
    while i < len(lines):
        t = _parse_table(lines, i)
        if t is None:
            i += 1
            continue
        header, data, end = t
        joined_h = " ".join(header).lower()
        if any(k in joined_h for k in ("实体", "entity", "名称", "name")) \
                and not any(any(c.replace(".", "").replace("%", "").
                                replace(",", "").isdigit() for c in row)
                            for row in data[:3] if row):
            # entity checklist table: 实体 | 类型 | 来源行
            for row in data:
                if not row:
                    continue
                name = row[0].strip()
                if not _token_ok(name):
                    continue
                oid = "E%d" % (len(out["entities"]) + 1)
                out["entities"].append({
                    "id": oid, "name": name,
                    "type": (row[1].strip() if len(row) > 1
                             and row[1].strip() else "entity"),
                    "source": path_rel,
                    "evidence": " | ".join(row)[:160],
                    "_line": i + 1, "_draft": True, "confidence": "strong",
                })
        if any(any(c.replace(".", "").replace("-", "").isdigit()
                   for c in row) for row in data[:5] if row):
            out["data"].append({
                "table": {"columns": header, "rows": data},
                "source": path_rel, "_line": i + 1, "_draft": True,
            })
        i = end

    # --- CSV files ---
    if path.lower().endswith(".csv"):
        parsed = _parse_csv_text(text, path_rel)
        if parsed:
            out["data"].append({
                "table": parsed, "source": path_rel, "_line": 1,
                "_draft": True,
            })

    # --- groups from section headers ---
    for ln_no, ln in enumerate(lines, 1):
        m = SECTION.match(ln)
        if m and m.group(2).strip():
            label = m.group(2).strip()
            if "省略" in label or "目录" in label:
                continue
            out["groups"].append({
                "id": "G%d" % (len(out["groups"]) + 1), "label": label,
                "members": [], "source": path_rel,
                "evidence": ln[:120], "_line": ln_no, "_draft": True,
                "_level": len(m.group(1)),
            })

    # --- relations: sentence with two entity names + canonical verb ---
    if not ents_by_line:
        ents_by_line = {}
        for e in out["entities"]:
            ents_by_line.setdefault(e["_line"], []).append((e["id"], e["name"]))
    for ln_no, ln in enumerate(lines, 1):
        for sent in _split_sentences(ln):
            s = sent.strip()
            if not s:
                continue
            hits = [(oid, tok) for oid, tok in ents_by_line.get(ln_no, [])
                    if tok in s]
            # also search global entity names in this sentence
            names = [mm.group(0) for mm in
                     re.finditer(r"[A-Za-z][\w\-\.]*|\*\*([^*]+)\*\*", s)]
            if not hits:
                hits = []
                for e in out["entities"]:
                    nm = e["name"]
                    if re.search(r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])"
                                 % re.escape(nm), s):
                        hits.append((e["id"], nm))
            if len(hits) < 2:
                continue
            for verb in CANONICAL_KINDS:
                canon, unknown = canonical_kind(verb)
                for syn in CANONICAL_KINDS[verb]["synonyms"]:
                    pat = re.escape(syn)
                    m2 = re.search(pat, s, flags=re.IGNORECASE)
                    if not m2:
                        continue
                    # from = before verb, to = after verb (best effort)
                    before, after = s[:m2.start()], s[m2.end():]
                    lhs = [(oid, nm) for oid, nm in hits if nm and nm in before]
                    rhs = [(oid, nm) for oid, nm in hits if nm and nm in after]
                    pair = None
                    if lhs and rhs:
                        pair = (lhs[-1], rhs[0])   # nearest around the verb
                    else:
                        pair = (hits[0], hits[1])
                    out["relations"].append({
                        "id": "R%d" % (len(out["relations"]) + 1),
                        "from": pair[0][0], "to": pair[1][0],
                        "kind": verb, "source": path_rel,
                        "evidence": s[:180], "_line": ln_no,
                        "_draft": True, "confidence": "candidate",
                    })
                    break
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inputs", nargs="+", required=True,
                    help="material files (md/txt/csv) to extract from")
    ap.add_argument("--out", required=True,
                    help="output draft manifest path (e.g. draft-entities.json)")
    ap.add_argument("--base-dir", default=None,
                    help="base directory for relative source paths "
                         "(default: cwd with the first input)")
    args = ap.parse_args(argv)

    base = args.base_dir or os.path.dirname(os.path.abspath(
        os.path.commonprefix([os.path.abspath(p) for p in args.inputs]))) \
        if len(args.inputs) > 1 else os.path.abspath(args.inputs[0])
    base = base if os.path.isdir(base) else os.path.dirname(base)

    merged = {"entities": [], "relations": [], "groups": [], "data": [],
              "notes": []}
    for p in args.inputs:
        apath = os.path.abspath(p)
        if not os.path.isfile(apath):
            print("WARN: material file not found (skipped): %s" % apath)
            continue
        rel = os.path.relpath(apath, base).replace("\\", "/")
        part = extract_file(apath, rel)
        for k in ("entities", "relations", "groups", "data"):
            merged[k].extend(part[k])
        for insp in ("notes",):
            merged[insp].extend(part[insp])

    draft = {
        "schema_version": "1.0",
        "figure_type": ("chart" if len(merged["data"]) >= len(merged["entities"])
                        and merged["data"] else "schematic"),
        "title": "",
        "_draft": True,
        "_extractor_note": (
            "DRAFT manifest generated by scripts/extract.py. Every item is "
            "anchored to a file+line and tagged _draft / confidence — the "
            "agent MUST review, correct directions/kinds, fill title/groups/"
            "legend, merge duplicates, then write the final manifest and "
            "run scripts/spec_lint.py (CP1) before drawing. The draft is "
            "NOT a final answer and is never submitted as one."),
        "entities": merged["entities"],
        "relations": merged["relations"],
        "groups": merged["groups"],
        "data": merged["data"],
        "legend": [],
        "style": {},
        "acknowledged_issues": [],
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".",
                exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(draft, ensure_ascii=False, indent=2) + "\n")

    print("extract: %d entities, %d relations, %d groups, %d data tables"
          % (len(merged["entities"]), len(merged["relations"]),
             len(merged["groups"]), len(merged["data"])))
    print("wrote draft: %s  (REVIEW REQUIRED before drawing)" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())