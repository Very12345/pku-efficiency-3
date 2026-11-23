# -*- coding: utf-8 -*-
"""Aggregated figure verifier (v2; aligns with `validate_figure`/`validate`
of 74+ packages: one entry point that fuses model integrity + traceability +
topology + legend/data audit + schema gate + export checks).

The pipeline treats any 'fail' as a blocking condition (status downgraded to
partial/failed) and requires every 'warn' to be echoed in result.json
uncertainty / self_check so nothing is silently papered over.

Also implements a compact JSON-Schema subset validator (type / required /
properties / items / enum) used for the mechanism-spec schema gate (CP2) so
the skill has zero third-party dependencies.
"""
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET

from model import NODE_TYPES, EDGE_TYPES, EVIDENCE_WIDTH, load_json

SVG_NS = "{http://www.w3.org/2000/svg}"

# ---------------------------------------------------------------------------
# compact JSON-schema subset validator ---------------------------------------
# ---------------------------------------------------------------------------
def _schema_type_ok(value, expected):
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    return True


def _validate_node(value, schema, path, problems):
    if not isinstance(schema, dict):
        return
    if "type" in schema and not _schema_type_ok(value, schema["type"]):
        problems.append("%s: 期望 %s，实际 %s" % (
            path, schema["type"], type(value).__name__))
        return
    if "enum" in schema and value not in schema["enum"]:
        problems.append("%s: 值 %r 不在枚举 %s 内" % (
            path, value, schema["enum"]))
    if isinstance(value, dict):
        if "required" in schema:
            for k in schema["required"]:
                if k not in value:
                    problems.append("%s: 缺少必需字段 %r" % (path, k))
        for k, sub in (schema.get("properties") or {}).items():
            if k in value:
                _validate_node(value[k], sub, "%s.%s" % (path, k), problems)
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            _validate_node(item, schema["items"], "%s[%d]" % (path, i), problems)


def validate_schema(data, schema):
    """Return list of human-readable problems; empty list == valid."""
    problems = []
    _validate_node(data, schema, "$", problems)
    return problems


# ---------------------------------------------------------------------------
# check helpers --------------------------------------------------------------
# ---------------------------------------------------------------------------
def sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _check(id_, name, result, detail):
    return {"id": id_, "check": name, "result": result, "detail": detail}


def run_result_checks(result_path):
    """Post-write checks on result.json (exists, parses, contract keys)."""
    checks = []
    if not (isinstance(result_path, str) and os.path.isfile(result_path)):
        checks.append(_check("F01_result_json", "result.json 存在且非空", "fail",
                             "缺失: %s" % (os.path.basename(result_path)
                                           if result_path else "N/A")))
        return _wrap(checks)
    sz = os.path.getsize(result_path)
    checks.append(_check("F01_result_json", "result.json 存在且非空", "pass",
                         "%s (%d bytes)" % (os.path.basename(result_path), sz)))
    try:
        with open(result_path, encoding="utf-8") as fh:
            rj = json.load(fh)
    except Exception as ex:
        checks.append(_check("F03_contract", "result.json 可解析", "fail", str(ex)))
        return _wrap(checks)
    need = ["case_id", "status", "deliverables", "scientific_content",
            "evidence_sources", "uncertainty", "change_records", "export_checks",
            "self_check"]
    miss = [k for k in need if k not in rj]
    checks.append(_check("F03_contract", "result.json 契约字段完整",
                         "fail" if miss else "pass",
                         ("缺字段: %s" % miss) if miss
                         else "契约字段齐全 (contract %s)" % rj.get("contract_version")))
    return _wrap(checks)


def _wrap(checks):
    return {"passed": not any(c["result"] == "fail" for c in checks),
            "checks": checks,
            "failures": [c for c in checks if c["result"] == "fail"],
            "warnings": [c for c in checks if c["result"] == "warn"]}


def check_schema(model, schema_path):
    """Gates the model against the mechanism-spec schema (CP2)."""
    if not (schema_path and os.path.isfile(schema_path)):
        return _check("S01_schema", "机制规格 schema 门(CP2)", "warn",
                      "未找到 %s，跳过 schema 校验（流水线仍可运行）" % (schema_path or "schema"))
    try:
        schema = load_json(schema_path)
    except Exception as ex:
        return _check("S01_schema", "机制规格 schema 门(CP2)", "fail",
                      "schema 不可读: %s" % ex)
    problems = validate_schema(model, schema)
    # the pipeline's own normalization may add derived fields (e.g. legend
    # defaults); only report schema-relevant problems about required structure
    blocking = [p for p in problems if not p.startswith("$.legend")]
    return _check("S01_schema", "机制规格 schema 门(CP2)",
                  "fail" if blocking else "pass",
                  ("schema 违规: %s" % "; ".join(blocking)) if blocking
                  else "机制规格通过 schema 校验（%s）" % os.path.basename(schema_path))


# ---------------------------------------------------------------------------
# aggregated checks ----------------------------------------------------------
# ---------------------------------------------------------------------------
def run_checks(model, layout, out_files, schema_path=None, svg_path=None):
    """out_files: dict with keys like result_json, svg, png, pdf, model_json.
    Aggregates M / T / S / L / E / F series; topology & legend audits are
    separate modules but their results are merged here as well."""
    checks = []

    # --- model integrity ---
    ids = [e["id"] for e in model["entities"]]
    checks.append(_check("M01", "实体 id 唯一",
                         "fail" if len(ids) != len(set(ids)) else "pass",
                         ("重复实体 id") if len(ids) != len(set(ids))
                         else "%d 个实体，id 唯一" % len(ids)))
    no_name = [e["id"] for e in model["entities"] if not e["name"]]
    checks.append(_check("M03", "实体命名", "fail" if no_name else "pass",
                         ("缺名称: %s" % no_name) if no_name else "全部实体有名称"))

    # --- schema gate (CP2) ---
    checks.append(check_schema(model, schema_path))

    # --- traceability ---
    no_src_e = [e["id"] for e in model["entities"] if not e.get("source")]
    checks.append(_check("T01", "实体来源标注", "fail" if no_src_e else "pass",
                         ("无来源实体: %s" % ", ".join(no_src_e)) if no_src_e
                         else "全部实体携带 source（材料行号/出处）"))
    no_src_r = [r["id"] for r in model["edges"] if not r.get("source")]
    checks.append(_check("T02", "边来源标注", "fail" if no_src_r else "pass",
                         ("无来源边: %s" % ", ".join(no_src_r)) if no_src_r
                         else "全部边携带 source"))
    assumed = [e["id"] for e in model["entities"] if any(
        s.get("kind") in ("assumption", "common_knowledge") for s in e.get("source", []))]
    assumed += [r["id"] for r in model["edges"] if any(
        s.get("kind") in ("assumption", "common_knowledge") for s in r.get("source", []))]
    checks.append(_check("T03", "假设型来源显式化",
                         "warn" if assumed else "pass",
                         ("基于假设/常识的元素: %s（须在 uncertainty 中说明）" % ", ".join(assumed))
                         if assumed else "无假设型来源元素"))

    # --- topology & legend audits (external modules) ---
    try:
        from topology import run_topology_checks
        checks += run_topology_checks(model, layout)
    except Exception as ex:
        checks.append(_check("P00", "拓扑校验模块", "fail", str(ex)))
    try:
        from legend_audit import run_legend_audit
        checks += run_legend_audit(model, layout,
                                   svg_path=svg_path or out_files.get("svg"))
    except Exception as ex:
        checks.append(_check("L00", "图例/数据编码校验模块", "fail", str(ex)))

    # --- layout warnings surfaced as warns ---
    for w in (layout or {}).get("warnings") or []:
        checks.append(_check("D02", "布局提示", "warn", w))

    # --- files & exports ---
    for key, fname in (("svg", "SVG"), ("png", "PNG预览"), ("pdf", "PDF预览")):
        p = out_files.get(key)
        if isinstance(p, str) and os.path.isfile(p):
            checks.append(_check("F01_%s" % key, "%s 存在且非空" % fname, "pass",
                                 "%s (%d bytes)" % (os.path.basename(p),
                                                    os.path.getsize(p))))
        else:
            checks.append(_check("F01_%s" % key, "%s 存在且非空" % fname, "fail",
                                 "缺失: %s" % (os.path.basename(p) if p else "N/A")))
    png = out_files.get("png")
    if png and os.path.isfile(png):
        try:
            from PIL import Image
            im = Image.open(png)
            w, h = im.size
            checks.append(_check("F02_png", "PNG 尺寸/可打开", "pass", "%dx%d px" % (w, h)))
        except Exception as ex:
            checks.append(_check("F02_png", "PNG 尺寸/可打开", "fail", str(ex)))

    # --- determinism probe ---
    det = {}
    for key in ("svg", "model_json"):
        p = out_files.get(key)
        if isinstance(p, str) and os.path.isfile(p):
            det[key] = sha16(p)
    checks.append(_check("D01_determinism", "确定性探针",
                         "pass" if det else "warn",
                         json.dumps(det, ensure_ascii=False) if det
                         else "无产物可探测"))

    return _wrap(checks)


def run_standalone(out_dir, case_path=None):
    """Re-audit a produced output directory (verify after build)."""
    result = {"out_dir": os.path.basename(os.path.normpath(out_dir)) or out_dir,
              "ok": False, "checks": [], "failures": [], "warnings": []}
    model_p = os.path.join(out_dir, "model.json")
    svg_p = os.path.join(out_dir, "diagram.svg")
    if not os.path.isfile(model_p):
        result["checks"].append(_check("S09", "model.json 存在", "fail", "缺失"))
        return _finalize_standalone(result)
    model = None
    try:
        from model import normalize_model
        model = normalize_model(load_json(model_p))
    except Exception as ex:
        result["checks"].append(_check("S09", "model.json 可读", "fail", str(ex)))
        return _finalize_standalone(result)
    try:
        from layout import compute_layout
        layout = compute_layout(model)
    except Exception as ex:
        layout = {"warnings": ["standalone 重算布局失败: %s" % ex]}
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(root, "assets", "mechanism-spec.schema.json")
    out_files = {
        "svg": svg_p,
        "png": os.path.join(out_dir, "diagram.png"),
        "pdf": os.path.join(out_dir, "diagram.pdf"),
        "result_json": os.path.join(out_dir, "result.json"),
        "model_json": model_p,
    }
    wr = run_checks(model, layout, out_files, schema_path=schema_path,
                    svg_path=svg_p)
    result["checks"] = wr["checks"]
    result["failures"] = wr["failures"]
    result["warnings"] = wr["warnings"]
    result["ok"] = not wr["failures"]
    return _finalize_standalone(result)


def _finalize_standalone(result):
    result["fail_count"] = len(result["failures"])
    result["warn_count"] = len(result["warnings"])
    return result


def _main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    import argparse
    ap = argparse.ArgumentParser(description="verify a produced pathway-figure output dir")
    ap.add_argument("--out", required=True, help="output directory to audit")
    ap.add_argument("--case", help="optional case.json (not required; model.json is authoritative)")
    args = ap.parse_args(argv)
    r = run_standalone(args.out, args.case)
    for c in r["checks"]:
        print("%-6s %-28s %s" % (c["result"], c["id"], c["check"]))
        if c["result"] != "pass":
            print("        detail: %s" % c["detail"])
    print("standalone-verify|ok=%s|fails=%d|warns=%d|out=%s" % (
        r["ok"], r["fail_count"], r["warn_count"], args.out))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(_main())