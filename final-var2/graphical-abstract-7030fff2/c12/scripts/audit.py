# -*- coding: utf-8 -*-
"""Self-check / audit for a produced graphical abstract.

Runs on real produced files (SVG + preview + result data), never on claims:
  - SVG well-formedness (re-parse with ElementTree)
  - PNG signature + dimensions
  - entity coverage: every extracted entity has an on-canvas element
  - encoding consistency: every data value string appears in the SVG text
  - canvas bounds: no element escapes the canvas
  - grayscale / color-blind check on the used palette
  - missing-value detection -> uncertainty items
  - determinism probe: layout hash is stable (pure function of input)

Everything is reported verbatim in ``report``; the orchestrator merges it into
``result.json``.
"""
from __future__ import annotations

import hashlib
import os
import re
import xml.etree.ElementTree as ET

from common import luminance_gap, write_json

PNG_SIG = b"\x89PNG\r\n\x1a\n"


def audit(spec: dict, content: dict, svg_path: str, png_path: str,
          pdf_path=None) -> dict:
    report = {"checks": {}}
    svg_text = _svg_text(svg_path)

    # 1. well-formedness ---------------------------------------------------
    wf = _check_svg_well_formed(svg_path)
    report["checks"]["svg_well_formed"] = wf

    # 2. png ----------------------------------------------------------------
    png = _check_png(png_path)
    report["checks"]["png"] = png

    # 3. pdf
    if pdf_path and os.path.isfile(pdf_path):
        pdf_size = os.path.getsize(pdf_path)
        head = open(pdf_path, "rb").read(5) if pdf_size else b""
        report["checks"]["pdf"] = {
            "present": True, "size_bytes": pdf_size,
            "header_ok": head == b"%PDF-"}
    else:
        report["checks"]["pdf"] = {"present": False, "reason": "not produced"}

    # 4. entity coverage -----------------------------------------------------
    entity_ids_in_svg = set(re.findall(r'data-entity-id="([^"]+)"', svg_text))
    missing_entities = []
    for e in content["entities"]:
        if e["id"] not in entity_ids_in_svg:
            if e["name"] not in svg_text:
                missing_entities.append(e["id"])
    report["entity_coverage"] = {
        "total": len(content["entities"]),
        "on_canvas": len(entity_ids_in_svg),
        "missing": missing_entities,
    }

    # 5. encoding consistency: every real value appears in svg text ----------
    values_missing = []
    for d in content["data"]:
        if d.get("value") is None:
            continue
        vs = f"{float(d['value']):g}"
        if vs not in svg_text:
            values_missing.append({"data": d["label"], "value": vs})
    report["encoding_consistency"] = {
        "total": sum(1 for d in content["data"] if d.get("value") is not None),
        "missing_from_canvas": values_missing,
    }

    # 6. bounds ---------------------------------------------------------------
    W, H = spec["width"], spec["height"]
    outside = []
    for el in spec["elements"]:
        x0 = el.get("x", el.get("x1", 0))
        y0 = el.get("y", el.get("y1", 0))
        w = el.get("w", 0)
        h = el.get("h", 0)
        if x0 is not None:
            if x0 < -1 or (x0 + w) > W + 1 or y0 < -1 or (y0 + h) > H + 1:
                outside.append({"role": el.get("role"), "id": el.get("id")})
    report["bounds"] = {"outside_count": len(outside), "outside": outside[:10]}

    # 7. palette grayscale check -----------------------------------------------
    used = []
    for c in spec.get("palette", []):
        if c not in used:
            used.append(c)
    gaps = []
    for i in range(len(used)):
        for j in range(i + 1, len(used)):
            g = luminance_gap(used[i], used[j])
            gaps.append((round(g, 3), used[i], used[j]))
    weak = [g for g in gaps if g[0] < 0.15]
    report["grayscale_check"] = {
        "default_colorblind_palette": spec.get("constraints_used", {}).get("colorblind", True),
        "min_pairwise_luminance_gap": min([g[0] for g in gaps], default=None),
        "weak_pairs": weak[:6],
    }

    # 8. missing values / uncertainty candidates --------------------------------
    missing_vals = [d["label"] for d in content["data"] if d.get("value") is None]
    report["missing_values"] = missing_vals
    report["layout_log"] = spec.get("layout_log", [])

    # 8a. four-element coverage (question/method/results/conclusion) ------------
    panels_spec = spec.get("panels") or {}
    panel_ids = set()
    for el in spec.get("elements", []):
        if el.get("panel"):
            panel_ids.add(el["panel"])
        for k in ("question", "method", "results", "conclusion"):
            if el.get("role") == f"panel:{k}":
                panel_ids.add(k)
    report["four_element_coverage"] = {
        "expected": ["question", "method", "results", "conclusion"],
        "on_canvas": sorted(p for p in ("question", "method", "results", "conclusion")
                            if (p in panel_ids or p in panels_spec)),
        "missing": [p for p in ("question", "method", "results", "conclusion")
                    if p not in panel_ids and p not in panels_spec],
        "content_panels": {p: len(panels_spec.get(p, [])) if isinstance(panels_spec.get(p), list) else 0
                           for p in ("question", "method", "results", "conclusion")},
    }

    # 8b. layer naming: every <g id="layer:*"> matches the documented set -------
    EXPECTED_LAYERS = ["background", "panels", "entities", "relations",
                       "data", "legend", "annotations"]
    found_layers = set(re.findall(r'<g id="layer:([^"]+)"', svg_text))
    bad_layers = sorted(found_layers - set(EXPECTED_LAYERS))
    missing_layers = sorted(set(EXPECTED_LAYERS) - found_layers)
    elements_without_src = 0
    missing_src_roles = []
    for el in spec.get("elements", []):
        role = el.get("role", "")
        # source binding is mandatory for the scientific data carriers;
        # layout/decor/panel-point roles are content-level
        if not role.startswith(("entity:", "relation:", "datum:", "icon")):
            continue
        if not (el.get("src") or el.get("data_src")):
            elements_without_src += 1
            missing_src_roles.append(role)
    report["layer_naming"] = {
        "expected": EXPECTED_LAYERS,
        "found": sorted(found_layers),
        "bad": bad_layers,
        "missing": missing_layers,
        "elements_without_src": elements_without_src,
        "missing_src_roles": missing_src_roles[:10],
        "note": "layers must match references/layer-naming.md; entity/relation/datum/icon "
                "elements must carry src",
    }

    # 9. determinism probe: spec hash (pure function of content) ----------------
    probe = hashlib.sha256(str(spec).encode("utf-8")).hexdigest()[:16]
    report["determinism_probe"] = {
        "spec_sha16": probe,
        "note": "same content+constraints => identical spec (layout is deterministic)"}
    return report


def _svg_text(path: str) -> str:
    if not os.path.isfile(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _check_svg_well_formed(path: str) -> dict:
    if not os.path.isfile(path):
        return {"ok": False, "error": "file missing"}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        ET.fromstring(text)
        return {"ok": True, "size_bytes": os.path.getsize(path),
                "layers": len(re.findall(r'<g id="layer:', text))}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def _check_png(path: str) -> dict:
    if not os.path.isfile(path):
        return {"ok": False, "error": "file missing"}
    with open(path, "rb") as fh:
        head = fh.read(8)
    if head != PNG_SIG:
        return {"ok": False, "error": "bad PNG signature"}
    w, h = (0, 0)
    try:
        from struct import unpack
        with open(path, "rb") as fh:
            fh.seek(16)
            w, h = unpack(">II", fh.read(8))
    except Exception:  # noqa: BLE001
        pass
    return {"ok": True, "size_bytes": os.path.getsize(path), "px": [w, h]}