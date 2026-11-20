# -*- coding: utf-8 -*-
"""spec_lint.py — lint a figure spec (spec.json / planned figure plan).

Part of the "graphical-abstract" Skill v2 (graphical-abstract-7030fff2,
efficiency-3).

This is the CP1 gate of the "方案先行" workflow: after the figure plan is
scaffolded (scripts/scaffold.py) or written by the agent, lint it *before*
drawing. Rules enforced:

* four-element story: question / method / results / conclusion must all be
  present (either as panel content or as canvas elements);
* reading order is declared and covers the four panels;
* every entity / relation / data point on the plan has a source-bound
  provenance marker (src / data_src) — nothing without a source may be drawn;
* every data point declares an encoding kind in the documented vocabulary
  (bar_length / color_scale / area / value_label) and every encoding kind has a
  legend entry (legend values ↔ data values consistency);
* canvas dimensions are within the allowed clamp range;
* determinism: the spec hash excludes layout_log so reruns are comparable.

The linter is advisory-for-the-agent but hard for the pipeline: problems are
recorded in result.json (spec_lint) and status must not be "success" while
lint problems exist.
"""
from __future__ import annotations

import hashlib
import json
import sys

ENCODING_KINDS = ("bar_length", "color_scale", "area", "value_label")
FOUR_PANELS = ("question", "method", "results", "conclusion")
CANVAS_MIN = 600
CANVAS_MAX = 4000


def spec_hash(spec: dict) -> str:
    """Deterministic hash of the plan excluding layout_log (rerun-stable)."""
    s = dict(spec)
    s.pop("layout_log", None)
    return hashlib.sha256(json.dumps(s, sort_keys=True, ensure_ascii=False,
                                     default=str).encode("utf-8")).hexdigest()[:16]


def lint(spec: dict, content: dict | None = None) -> dict:
    problems = []
    spec = spec or {}

    # 1. canvas bounds ------------------------------------------------------
    W, H = spec.get("width", 0), spec.get("height", 0)
    for name, v in (("width", W), ("height", H)):
        if not (CANVAS_MIN <= v <= CANVAS_MAX):
            problems.append("canvas %s=%s outside clamp [%d, %d]"
                            % (name, v, CANVAS_MIN, CANVAS_MAX))

    # 2. four-element story -------------------------------------------------
    content = content or {}
    panels = spec.get("panels") or {}
    panel_roles = {el.get("panel") for el in spec.get("elements", [])}
    for p in FOUR_PANELS:
        has_content = bool(panels.get(p)) if isinstance(panels.get(p), list) else False
        has_canvas = p in panel_roles
        if not has_content and not has_canvas:
            problems.append("four-element story missing panel: %s" % p)

    # 3. reading order --------------------------------------------------------
    ro = spec.get("reading_order") or []
    if not ro:
        problems.append("reading_order not declared")
    else:
        for p in FOUR_PANELS:
            if p not in ro:
                problems.append("reading_order missing panel: %s" % p)

    # 4. source-bound provenance ----------------------------------------------
    # Layout/decor/panel-point elements are content-level (panel points come from
    # the material via parse_panel_text); source-binding is mandatory for the
    # scientific data carriers: entities, relations, datum, icons.
    no_src = [e.get("id") or e.get("role") for e in spec.get("elements", [])
              if not (e.get("src") or e.get("data_src")) and e.get("role", "")
              .startswith(("entity:", "relation:", "datum:", "icon"))]
    if no_src:
        problems.append("elements without source provenance: %s" % no_src[:8])

    # 5. data encoding + legend consistency -------------------------------------
    enc = spec.get("data_encoding") or []
    for item in enc:
        kind = item.get("channel") or item.get("kind")
        if kind not in ENCODING_KINDS:
            problems.append("unknown encoding kind %r (vocabulary: %s)"
                            % (kind, ", ".join(ENCODING_KINDS)))
    legend = spec.get("legend") or []
    legend_labels = {str(x.get("label") or x.get("key")) for x in legend}
    has_gradient = any(str(x.get("symbol")) == "gradient" for x in legend)
    for item in enc:
        kind = item.get("channel") or item.get("kind")
        label = item.get("label")
        if not label:
            continue
        if kind == "color_scale":
            # gradient legend is labeled by range, not by the datum label
            if legend and not has_gradient:
                problems.append("color_scale datum %r missing gradient legend entry "
                                "(legend values must match data labels)" % label)
        elif label not in legend_labels:
            problems.append("encoded datum %r missing legend entry (legend values must "
                            "match data labels)" % label)

    # 6. determinism -------------------------------------------------------------
    probe = spec_hash(spec)
    return {
        "valid": not problems,
        "problems": problems,
        "spec_sha16": probe,
        "counts": {"elements": len(spec.get("elements", [])),
                   "legend_entries": len(legend),
                   "encoding_items": len(enc)},
    }


def lint_plan(plan: dict) -> dict:
    """Validate a *design plan* (方案先行 input, see references/plan-schema.md)
    before drawing: four elements articulated, entities/relations/data carry
    source provenance, constraints present."""
    problems = []
    plan = plan or {}
    fe = plan.get("four_elements") or {}
    for p in FOUR_PANELS:
        if not str(fe.get(p) or "").strip():
            problems.append("plan.four_elements.%s missing (一句话说明本面板表达什么)" % p)
    for group in ("entities", "relations", "data"):
        items = plan.get(group)
        if not isinstance(items, list):
            continue
        for it in items:
            if isinstance(it, dict) and not (it.get("src") or it.get("data_src")):
                problems.append("plan.%s item %r missing source provenance (src)"
                                % (group, (it.get("name") or it.get("label") or it.get("id"))))
    cons = plan.get("figure_constraints") or plan.get("constraints") or {}
    w, h = cons.get("width"), cons.get("height")
    if w is None or h is None:
        problems.append("plan constraints missing width/height")
    elif not (CANVAS_MIN <= w <= CANVAS_MAX and CANVAS_MIN <= h <= CANVAS_MAX):
        problems.append("plan canvas %sx%s outside clamp" % (w, h))
    return {"valid": not problems, "problems": problems,
            "plan_hash": spec_hash(plan)}


def main(argv=None):
    import argparse
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="lint a figure spec (spec.json)")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--content", default=None, help="optional content.json (extraction)")
    args = ap.parse_args(argv)
    with open(args.spec, encoding="utf-8") as fh:
        spec = json.load(fh)
    content = None
    if args.content and __import__("os").path.isfile(args.content):
        with open(args.content, encoding="utf-8") as fh:
            content = json.load(fh)
    rep = lint(spec, content)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0 if rep["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())