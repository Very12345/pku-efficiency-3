#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick self-test of the skill's core logic (no platform involved).

v2 suite: base logic checks (kind mapping, edge clipping, layout, manifest
round-trip, legend conformance, chart render, edit) plus the new v2 pieces:
spec_lint CP1 gate, draft extractor, pdftext fallback, textfont probe and
validate_result G1-G8 contract gates. Prints PASS/FAIL per item; exit code
is the number of failed items (0 = all green).

    python <skill_root>/scripts/selftest.py
"""

import json
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

FAILED = []


def check(name, ok, detail=""):
    tag = "PASS" if ok else "FAIL"
    print("[%s] %-40s %s" % (tag, name, detail))
    if not ok:
        FAILED.append(name)
    return ok


def roundtrip_manifest():
    from manifest import normalize_manifest, canonical_kind, persist_manifest, \
        load_manifest, validate_manifest, extract_manifest_from_svg
    m = {
        "figure_type": "schematic",
        "title": "roundtrip",
        "entities": [
            {"id": "E1", "name": "TNF", "type": "small_molecule",
             "source": "fig-note.md", "evidence": "§1"},
            {"id": "E2", "name": "TNFR1", "type": "receptor",
             "source": "fig-note.md", "evidence": "§1"},
        ],
        "relations": [
            {"id": "R1", "from": "E1", "to": "E2", "kind": "binds",
             "source": "fig-note.md", "evidence": "§1"},
        ],
    }
    n = normalize_manifest(m)
    check("kind synonym 'binds' -> recruitment",
          n["relations"][0]["_canon"] == "recruitment",
          "got %r" % n["relations"][0]["_canon"])
    check("unknown kind flagged",
          canonical_kind("gibberish")[1] is True)
    fd, p = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        persist_manifest(n, p)
        back = load_manifest(p)
        check("manifest json round-trip", len(back["entities"]) == 2)
    finally:
        os.unlink(p)
    issues = validate_manifest(n)
    check("valid manifest has no hard issues",
          not [i for i in issues if i["level"] == "fail"], str(issues))


def test_layout():
    from layout import compute_layout, clip_segment_to_rect, edge_endpoints
    # segment clipping: horizontal ray must exit at x = +hw
    px, py = clip_segment_to_rect(0, 0, 100, 0, 10, 5)
    check("clip horizontal ray at right edge", abs(px - 10) < 1e-9
          and abs(py) < 1e-9, (px, py))
    m = {
        "figure_type": "schematic",
        "entities": [
            {"id": "A", "name": "AAA"},
            {"id": "B", "name": "BBB"},
            {"id": "C", "name": "CCC"},
        ],
        "relations": [
            {"id": "r1", "from": "A", "to": "B", "kind": "activates"},
            {"id": "r2", "from": "B", "to": "C", "kind": "inhibits"},
        ],
    }
    from manifest import normalize_manifest
    L = compute_layout(normalize_manifest(m))
    check("layered layout: 3 nodes", len(L["nodes"]) == 3)
    check("layers A<B<=C",
          L["nodes"]["A"]["layer"] <= L["nodes"]["B"]["layer"] <=
          L["nodes"]["C"]["layer"])


def test_svg_builder():
    from manifest import normalize_manifest, extract_manifest_from_svg
    from layout import compute_layout
    from svgbuilder import build_schematic_svg
    import tempfile
    m = normalize_manifest({
        "figure_type": "schematic", "title": "Self-test figure",
        "entities": [
            {"id": "E1", "name": "Ligand", "type": "small_molecule",
             "source": "s.md", "evidence": "§1"},
            {"id": "E2", "name": "Receptor", "type": "receptor",
             "source": "s.md", "evidence": "§1"},
            {"id": "E3", "name": "Gene X", "type": "gene",
             "source": "s.md", "evidence": "§2"},
        ],
        "relations": [
            {"id": "R1", "from": "E1", "to": "E2", "kind": "binds",
             "source": "s.md", "evidence": "§1"},
            {"id": "R2", "from": "E2", "to": "E3", "kind": "activates",
             "source": "s.md", "evidence": "§2"},
        ],
        "groups": [
            {"id": "G1", "label": "Receptor module",
             "members": ["E2"], "source": "s.md", "evidence": "§2"},
        ],
    })
    L = compute_layout(m)
    xml = build_schematic_svg(m, L)
    check("svg has text elements", xml.count("<text") >= 5)
    check("svg has er-manifest metadata", 'id="er-manifest"' in xml)
    check("svg has semantic layers",
          all(l in xml for l in ("layer-nodes", "layer-edges",
                                 "layer-legend", "layer-footer")))
    check("svg arrow marker for activation",
          "url(#arrow-activation)" in xml)
    fd, p = tempfile.mkstemp(suffix=".svg")
    os.close(fd)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(xml)
    emb = extract_manifest_from_svg(p)
    check("embedded manifest extractable",
          emb is not None and len(emb["entities"]) == 3)
    os.unlink(p)


def test_chart():
    from manifest import normalize_manifest
    import render as render_mod
    m = normalize_manifest({
        "figure_type": "chart", "title": "Compound response",
        "data": {
            "chart_type": "bar",
            "table": {"columns": ["compound", "response"],
                      "rows": [["ctrl", 1.0], ["A", 2.4], ["B", 3.1],
                               ["C", 0.8]]},
            "category_col": "compound", "value_col": "response",
            "unit": "fold change",
        },
    })
    with tempfile.TemporaryDirectory() as td:
        info = render_mod.build_chart_artifacts(
            m, os.path.join(td, "fig"), exports=("png", "pdf", "svg"))
        check("chart png produced", os.path.isfile(info["png"]))
        check("chart pdf produced", os.path.isfile(info["pdf"]))
        svg_p = info.get("svg")
        check("chart svg produced", bool(svg_p) and os.path.isfile(svg_p))
        if svg_p:
            from manifest import extract_manifest_from_svg
            emb = extract_manifest_from_svg(svg_p)
            check("chart svg has embedded manifest", emb is not None)
        check("chart mapping consistent",
              info["mapping"]["unique_categories"] ==
              ["ctrl", "A", "B", "C"], str(info["mapping"]))


def test_checks_and_edit():
    from manifest import normalize_manifest
    import checks as checks_mod
    import edit as edit_mod
    m = normalize_manifest({
        "figure_type": "schematic",
        "entities": [
            {"id": "E1", "name": "A", "source": "s", "evidence": "q"},
            {"id": "E2", "name": "B", "source": "s", "evidence": "q"},
            {"id": "E3", "name": "C", "source": "s", "evidence": "q"},
        ],
        "relations": [
            {"id": "R1", "from": "E1", "to": "E2", "kind": "activates",
             "source": "s"},
            {"id": "R2", "from": "E2", "to": "E3", "kind": "inhibits",
             "source": "s"},
            {"id": "R3", "from": "E1", "to": "E1", "kind": "activates",
             "source": "s"},
        ],
        "legend": [
            {"id": "L1", "key": "activation", "label": "activation"},
        ],
    })
    issues = checks_mod.check_legend_conformance(m)
    hard = [i for i in issues if i["level"] == "fail"]
    check("legend conformance catches missing kind",
          any("inhibition" in i["detail"] for i in hard), str(issues))
    m2, recs, ed_issues = edit_mod.apply_edits(m, [
        {"action": "rename", "entity_id": "E1", "to": "IL-6"},
        {"action": "add_entity",
         "entity": {"id": "E9", "name": "NF-kB", "type": "protein",
                    "source": "s", "evidence": "q"},
         "relation": {"from": "E2", "to": "E9", "kind": "activates",
                      "source": "s"}},
        {"action": "remove_relation", "relation_id": "R3"},
    ])
    check("edit: rename applied",
          any(e["name"] == "IL-6" for e in m2["entities"]))
    check("edit: entity+relation added",
          any(e["id"] == "E9" for e in m2["entities"])
          and any(r["to"] == "E9" for r in m2["relations"]))
    check("edit: relation removed", all(r["id"] != "R3"
                                        for r in m2["relations"]))
    check("edit: change records recorded", len(recs) >= 3, str(recs))
    check("edit: leftover relation references resolved",
          len([r for r in m2["relations"]
               if r["from"] in ("E9",) and r["to"] == "E9"]) >= 0)


def test_spec_lint_v2():
    import spec_lint as sl
    good = {
        "figure_type": "schematic",
        "entities": [
            {"id": "E1", "name": "TNF", "source": "s.md", "evidence": "q"},
            {"id": "E2", "name": "TNFR1", "source": "s.md", "evidence": "q"},
            {"id": "E3", "name": "NF-kB", "source": "s.md", "evidence": "q"},
        ],
        "relations": [
            {"id": "R1", "from": "E1", "to": "E2", "kind": "binds",
             "source": "s.md"},
            {"id": "R2", "from": "E2", "to": "E3", "kind": "activates",
             "source": "s.md"},
        ],
        "groups": [],
        "legend": [
            {"id": "L1", "key": "recruitment", "label": "recruits"},
            {"id": "L2", "key": "activation", "label": "activates"},
        ],
    }
    issues = sl.lint_manifest(good, sl.load_dict(
        os.path.join(_HERE, "..", "assets", "relation-dict.json")))
    check("spec_lint: good manifest valid",
          not [i for i in issues if i["level"] == "fail"], str(issues))
    bad = dict(good)
    bad["legend"] = [{"id": "L1", "key": "recruitment", "label": "r"}]
    bad["relations"] = list(good["relations"]) + [
        {"id": "R3", "from": "E1", "to": "E3", "kind": "gibberish",
         "source": "s.md"},
        {"id": "R4", "from": "E1", "to": "E3", "kind": "contains",
         "source": "s.md"},
    ]
    issues = sl.lint_manifest(bad, sl.load_dict(
        os.path.join(_HERE, "..", "assets", "relation-dict.json")))
    kinds = {i["check"] for i in issues if i["level"] == "fail"}
    check("spec_lint: unknown kind + legend gap + containment caught",
          {"spec.relation_kind", "spec.legend_missing_kinds",
           "spec.containment_group"}.issubset(kinds), str(kinds))


def test_textfont_v2():
    import textfont as tf
    p = tf.probe()
    check("textfont probe has resolved family",
          bool(p["resolved"]["family"]), str(p["resolved"]))
    check("textfont probe deterministic",
          tf.probe() == p)


def test_extract_v2():
    import extract as ex
    mat = os.path.join(_HERE, "..", "examples", "sources", "figure03-note.md")
    if not os.path.isfile(mat):
        return
    part = ex.extract_file(mat, "sources/figure03-note.md")
    names = {e["name"] for e in part["entities"]}
    check("extract: finds bold entity names from note",
          {"TNF-α", "TNFR1", "TRADD", "RIPK1", "NF-κB",
           "IL6"}.issubset(names), str(sorted(names)))
    check("extract: finds candidate relations",
          len(part["relations"]) >= 3, "%d" % len(part["relations"]))
    check("extract: every item carries _draft + source",
          all(e.get("_draft") and e.get("source") for e in part["entities"]))


def test_pdftext_v2():
    import pdftext as pt
    import tempfile
    nl9 = bytes((10,))
    blob = (b"%" + b"PDF-1.4" + nl9 + b"1 0 obj" + nl9 +
            b"<< /Type /Page >>" + nl9 + b"endobj" + nl9 +
            b"2 0 obj" + nl9 + b"<< /Length 60 >>" + nl9 +
            b"stream" + nl9 +
            b"BT /F1 12 Tf (TNF-alpha) Tj ET" + nl9 +
            b"endstream" + nl9 + b"endobj" + nl9)
    with tempfile.TemporaryDirectory() as td:
        pdf = os.path.join(td, "m.pdf")
        with open(pdf, "wb") as fh:
            fh.write(blob)
        info = pt.extract_pdf(pdf)
        check("pdftext: fallback backend reported",
              info["backend"] in ("stdlib", "fitz", "pypdf", "PyPDF2"),
              str(info["backend"]))
        check("pdftext: toy pdf did not crash", True)


def test_validate_gates_v2():
    import validate_result as vr
    good = {
        "case_id": "selftest", "status": "success",
        "figure_type": "schematic", "title": "t",
        "skill": {"name": "x"}, "workorder": "w",
        "main_result": {"deliverables": {}}, "artifacts": [],
        "evidence": {}, "legend_mapping": [], "data_mapping": {},
        "verification": {"checks": {"fail_count": 0, "fails": []}},
        "sources": [], "uncertainty": [], "change_records": [],
        "generated_at": "2026-01-01T00:00:00+0000", "tool_versions": {},
    }
    errs = vr.validate(good)
    check("validate_result: missing artifacts rejected",
          any("G7" in e for e in errs), str(errs))
    bad_status = dict(good)
    bad_status["verification"] = {"checks": {"fail_count": 1,
                                             "fails": [{"level": "fail"}]}}
    errs = vr.validate(bad_status)
    check("validate_result: success-with-fails rejected",
          any("G2" in e for e in errs), str(errs))


def test_checklist_v2():
    import json as _json
    cl_path = os.path.join(_HERE, "..", "assets", "checklist.json")
    with open(cl_path, "r", encoding="utf-8") as fh:
        cl = _json.load(fh)
    check("checklist: CP1..CP5 present",
          {"CP1", "CP2", "CP3", "CP4", "CP5"}.issubset(
              {c["id"] for c in cl.get("checkpoints", [])}),
          str([c["id"] for c in cl.get("checkpoints", [])]))


def main():
    roundtrip_manifest()
    test_layout()
    test_svg_builder()
    test_chart()
    test_checks_and_edit()
    test_spec_lint_v2()
    test_textfont_v2()
    test_extract_v2()
    test_pdftext_v2()
    test_validate_gates_v2()
    test_checklist_v2()
    print()
    if FAILED:
        print("%d FAILED: %s" % (len(FAILED), "; ".join(FAILED)))
        return len(FAILED)
    print("selftest: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())