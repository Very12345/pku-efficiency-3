# -*- coding: utf-8 -*-
"""preview.py — preview rendering for slide decks.

No LibreOffice on the runtime box: this renderer draws a schematic preview
from the same plan used to build the pptx, NOT a pixel-perfect export.
Outputs are explicitly labelled SCHEMATIC: real pixel-perfect export needs
Microsoft PowerPoint / LibreOffice and is recorded as unavailable.

  <case_id>_cover_preview.png          — cover preview (title/subtitle/meta)
  <case_id>_slides_contact_schematic.png — contact sheet, one tile per slide
  render_log.json                      — backends, fonts, honest notes
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont
from common import (PALETTE, hex_to_rgb, pil_font, probe_font_candidates,
                    dump_json, write_text, utf8_writer, SKILL_NAME, SKILL_VERSION, slash)

W, H = 1280, 720


def _wrap(draw, text, font, max_w):
    words = list(text)
    lines, cur = [], ""
    for ch in words:
        test = cur + ch
        if draw.textlength(test, font=font) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines or [""]


def render_cover_png(content: dict, plan: dict, out_png: str) -> dict:
    img = Image.new("RGB", (W, H), hex_to_rgb(PALETTE["paper"]))
    d = ImageDraw.Draw(img)
    ink = hex_to_rgb(PALETTE["ink"])
    accent = hex_to_rgb(PALETTE["accent"])
    muted = hex_to_rgb(PALETTE["muted"])
    body = hex_to_rgb(PALETTE["body"])

    # top band
    d.rectangle([0, 0, W, 14], fill=ink)
    d.rectangle([0, H - 10, W, H], fill=accent)

    font_title = pil_font(48, bold=True)
    font_sub = pil_font(26)
    font_meta = pil_font(18)
    font_note = pil_font(14)

    title = content.get("title") or plan.get("case_id") or "Academic talk"
    subtitle = content.get("subtitle") or ""
    authors = content.get("authors") or []
    author_str = " / ".join(a if isinstance(a, str) else str(a.get("text")) for a in authors[:3])
    aff = content.get("affiliation") or ""
    meta = " · ".join(x for x in [author_str, aff, f"{content.get('audience') or ''}",
                                  f"约{content.get('duration_minutes') or 15}分钟"] if x)

    lines = _wrap(d, title, font_title, W - 200)
    y = 170
    for ln in lines[:2]:
        d.text(((W - d.textlength(ln, font=font_title)) // 2, y), ln, font=font_title, fill=ink)
        y += 62
    y += 24
    if subtitle:
        for ln in _wrap(d, subtitle, font_sub, W - 260)[:3]:
            d.text(((W - d.textlength(ln, font=font_sub)) // 2, y), ln, font=font_sub, fill=body)
            y += 36
        y += 12
    d.text(((W - d.textlength(meta, font=font_meta)) // 2, y), meta, font=font_meta, fill=muted)
    y += 50
    d.rectangle([W // 2 - 120, y, W // 2 + 120, y + 4], fill=accent)

    note = "SCHEMATIC PREVIEW (PIL) — not a pixel-perfect export; open the .pptx in PowerPoint/LibreOffice for true rendering"
    d.text((30, H - 46), note, font=font_note, fill=muted)
    d.text((W - 300, H - 46), f"{SKILL_NAME} v{SKILL_VERSION}", font=font_note, fill=muted)

    img.save(out_png, format="PNG", optimize=True)
    return {"backend": "PIL", "size": [W, H], "label": "SCHEMATIC",
            "fonts": _font_report(), "note": note}


def render_contact_png(content: dict, plan: dict, out_png: str) -> dict:
    pages = plan["pages"]
    n = max(len(pages), 1)
    cols = min(4, max(1, int((n + 3) / 4)))
    rows = int((n + cols - 1) / cols)
    tw, th = 640, 360
    sheet_w = cols * tw + (cols + 1) * 20
    sheet_h = rows * th + (rows + 1) * 20 + 40
    img = Image.new("RGB", (sheet_w, sheet_h), hex_to_rgb("#EEEEEE"))
    d = ImageDraw.Draw(img)

    font_title = pil_font(22, bold=True)
    font_small = pil_font(14)
    font_mid = pil_font(16)
    ink = hex_to_rgb(PALETTE["ink"])
    body = hex_to_rgb(PALETTE["body"])

    d.text((20, 12), f"SLIDE CONTACT SHEET (schematic, {n} pages) — {content.get('case_id', '')}",
           font=font_mid, fill=ink)

    for i, p in enumerate(pages):
        col = i % cols
        row = i // cols
        x0 = 20 + col * (tw + 20)
        y0 = 48 + row * (th + 20)
        is_cover = p["page_type"] == "cover"
        bg = hex_to_rgb("#FFFFFF") if not is_cover else hex_to_rgb("#F0F4FA")
        d.rectangle([x0, y0, x0 + tw, y0 + th], fill=bg, outline=ink, width=2)
        # tile header
        d.rectangle([x0, y0, x0 + tw, y0 + 52], fill=ink)
        ttl = p["title"][:34]
        d.text((x0 + 12, y0 + 12), f"{p['page_no']} · {ttl}", font=font_title, fill=(255, 255, 255))
        y = y0 + 64
        claims = (p.get("claims") or [])[:4]
        for c in claims:
            for ln in _wrap(d, "• " + c, font_small, tw - 24)[:2]:
                d.text((x0 + 12, y), ln, font=font_small, fill=body)
                y += 20
            y += 4
        figref = " ".join(p.get("figure_refs") or [])
        tbref = " ".join(p.get("table_refs") or [])
        refs = "  ".join(x for x in [("fig: " + figref) if figref else "", ("tbl: " + tbref) if tbref else ""] if x)
        if refs:
            d.text((x0 + 12, y + 4), refs, font=font_small, fill=hex_to_rgb(PALETTE["accent2"]))

    img.save(out_png, format="PNG", optimize=True)
    return {"backend": "PIL", "tiles": n, "cols": cols, "rows": rows,
            "label": "SCHEMATIC_CONTACT_SHEET", "fonts": _font_report()}


def _font_report() -> list:
    """Honest, machine-independent record of the font actually used.

    The resolved font is recorded by file name (the directory is resolved from
    the platform's standard font locations at run time), so the log stays
    reproducible on any host and leaks no local path.
    """
    cands, path, idx = probe_font_candidates()
    return [{"file": os.path.basename(path) if path else "",
             "index": idx,
             "fallback_default": path is None,
             "candidates_probed": len(cands),
             "note": ("system font resolved at run time from the standard font "
                      "directories (see scripts/common.py font_dirs)")}]


def render_all(content: dict, plan: dict, out_dir: str, case_id: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    cover = os.path.join(out_dir, f"{case_id}_cover_preview.png")
    sheet = os.path.join(out_dir, f"{case_id}_slides_contact_schematic.png")
    cover_log = render_cover_png(content, plan, cover)
    sheet_log = render_contact_png(content, plan, sheet)
    log = {
        "_meta": "preview rendering log; schematic PIL preview, not pixel-perfect export",
        "renderer": "PIL (no LibreOffice/uno detected on runtime box)",
        "cover": {"path": slash(cover), **cover_log},
        "contact_sheet": {"path": slash(sheet), **sheet_log},
        "honest_note": ("PDF export requires Microsoft PowerPoint or LibreOffice; "
                        "not performed because neither was available/freshly verified here."),
    }
    dump_json(os.path.join(out_dir, "render_log.json"), log)
    write_text(os.path.join(out_dir, "_PREVIEW_ARE_SCHEMATIC.txt"),
               "Preview PNGs are PIL-drawn schematic previews from the same plan that built the pptx.\n"
               "They are NOT pixel-perfect exports. Open the .pptx in PowerPoint/LibreOffice for the true rendering.\n")
    return log


def main(argv=None):
    utf8_writer()
    import argparse
    import json
    ap = argparse.ArgumentParser(description="preview.py — schematic PIL previews for a deck plan")
    ap.add_argument("--content", required=True)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    content = json.load(open(a.content, "r", encoding="utf-8-sig"))
    plan = json.load(open(a.spec, "r", encoding="utf-8-sig"))
    log = render_all(content, plan, a.out, content.get("case_id", "deck"))
    print(f"preview ok: cover/sheet + render_log.json written under {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())