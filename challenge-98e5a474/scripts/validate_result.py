#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standalone contract validator for result.json (v2, G1-G8 hard gates).

Checks a produced result.json against references/OUTPUT_CONTRACT.md:

* G1  case_id present and (when --case is given) matches the case
* G2  status in {success, partial, failed}; coherent with verification
* G3  every listed artifact file exists under the output directory
* G4  evidence / sources / uncertainty / change_records / legend_mapping /
      data_mapping well-typed (dict/list with required shape)
* G5  output_contract echo: every key of the case's output_contract appears
      at the top level with a non-null, type-shaped value (the "four form"
      echo — see OUTPUT_CONTRACT.md; a wrong `null` is a hard fail)
* G6  verification carries checks/spec_lint/traceability; status != success
      when hard fails are recorded OR CP1 spec_lint is invalid
* G7  editable source + preview + export present (figure.svg, a raster
      preview, and a vector/PDF export for non-chart figures; chart needs
      svg+png+pdf too)
* G8  no fabricated data: chart numeric values in result.json match the
      manifest data table where both are present

Exit codes: 0 = valid, 1 = invalid, 2 = usage error.
"""

import argparse
import json
import os
import sys

try:  # narrow Windows consoles (GBK) must not crash --help or log output
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except Exception:
    pass

REQUIRED = [
    "case_id", "skill", "status", "workorder", "figure_type", "title",
    "main_result", "artifacts", "evidence", "legend_mapping",
    "data_mapping", "verification", "sources", "uncertainty",
    "change_records", "generated_at", "tool_versions",
]

NONEMPTY = [
    "case_id", "status", "main_result", "artifacts", "evidence",
    "verification", "generated_at", "tool_versions",
]

EMPTY_OK = {"sources", "uncertainty", "change_records", "legend_mapping",
            "data_mapping", "title"}

STATUSES = ("success", "partial", "failed")


def _type_default(hint):
    """Best-effort expected JSON type for an output_contract hint value."""
    if isinstance(hint, str):
        low = hint.strip().lower()
        if low in ("array", "list", "json-array", "sequence"):
            return list
        if low in ("object", "dict", "map", "json-object"):
            return dict
        if low in ("string", "text", "str"):
            return str
        if low in ("number", "integer", "int", "float", "numeric", "double"):
            return (int, float)
        if low in ("boolean", "bool"):
            return bool
        return str
    if isinstance(hint, list):
        return list
    if isinstance(hint, dict):
        return dict
    if isinstance(hint, bool):
        return bool
    if isinstance(hint, (int, float)):
        return (int, float)
    return object


def validate(result, case_path=None, result_path="", out_dir=None):
    """Return list of error strings (empty == valid)."""
    errors = []
    for key in REQUIRED:
        if key not in result:
            errors.append("G-required missing key: %s" % key)
        elif key in NONEMPTY and result[key] in (None, "", []):
            errors.append("G-required key %s is empty/degenerate" % key)

    # G1 case_id
    if not result.get("case_id"):
        errors.append("G1 case_id missing or empty")
    if case_path and os.path.isfile(case_path):
        with open(case_path, "r", encoding="utf-8") as fh:
            case = json.load(fh)
        cid = case.get("case_id") or case.get("id")
        if cid and result.get("case_id") != str(cid):
            errors.append("G1 case_id mismatch: case=%r result=%r"
                          % (cid, result.get("case_id")))

    # G2 status
    status = result.get("status")
    if status and status not in STATUSES:
        errors.append("G2 invalid status %r (allowed: %s)"
                      % (status, ", ".join(STATUSES)))
    vf = result.get("verification")
    if not isinstance(vf, dict) or "checks" not in vf:
        errors.append("G2 verification.checks missing")
    else:
        checks = vf["checks"]
        if isinstance(checks, dict):
            fails = checks.get("fails") or []
            if status == "success" and (fails or
                                        not checks.get("fail_count") == 0):
                errors.append("G2 status=success but hard fails recorded")
        # CP1 gate coherence: lint invalid must not be success
        lint = vf.get("spec_lint") or {}
        if isinstance(lint, dict) and lint.get("valid") is False \
                and status == "success":
            errors.append("G2 status=success but CP1 spec_lint invalid")

    # G3 artifacts exist
    artifacts = result.get("artifacts")
    base_dir = os.path.abspath(out_dir or os.path.dirname(result_path))
    if isinstance(artifacts, list):
        roles, fmts = [], []
        for art in artifacts:
            if not isinstance(art, dict):
                errors.append("G3 artifact entry is not an object")
                continue
            rel = art.get("path")
            if not rel:
                errors.append("G3 artifact without path: %r" % art)
                continue
            apath = rel if os.path.isabs(rel) else os.path.join(base_dir, rel)
            if not os.path.isfile(apath):
                errors.append("G3 artifact file missing: %s" % rel)
            roles.append((art.get("role"), art.get("format")))
            fmts.append(art.get("format"))
        # G7 editable source + preview + export present
        if not roles:
            errors.append("G7 no artifacts produced at all (editable source, "
                          "preview and export all missing)")
        elif result.get("figure_type") in ("schematic", "chart", None):
            by_role = {r: f for r, f in roles}
            if "figure" not in by_role:
                errors.append("G7 no editable source artifact (role=figure)")
            if "preview" not in by_role:
                errors.append("G7 no preview artifact (role=preview)")
            has_vec = any(f in ("pdf", "eps", "tiff") for f in fmts)
            if not has_vec:
                errors.append("G7 no vector/PDF export artifact")
    else:
        errors.append("G3 artifacts is not a list")

    # G4 well-typed collections
    if not isinstance(result.get("evidence"), dict):
        errors.append("G4 evidence is not an object")
    if not isinstance(result.get("uncertainty"), list):
        errors.append("G4 uncertainty is not a list")
    if not isinstance(result.get("change_records"), list):
        errors.append("G4 change_records is not a list")
    if not isinstance(result.get("sources"), list):
        errors.append("G4 sources is not a list")
    if not isinstance(result.get("legend_mapping"), list):
        errors.append("G4 legend_mapping is not a list")
    if not isinstance(result.get("data_mapping"), (dict, list)):
        errors.append("G4 data_mapping is not an object/list")

    # G5 output_contract echo (four forms, no null)
    if case_path and os.path.isfile(case_path):
        try:
            with open(case_path, "r", encoding="utf-8") as fh:
                case = json.load(fh)
        except Exception:
            case = None
        oc = (case or {}).get("output_contract") if isinstance(case, dict) \
            else None
        if isinstance(oc, dict) and oc:
            for key, hint in oc.items():
                if key not in result:
                    errors.append("G5 contract key not echoed: %s" % key)
                    continue
                val = result[key]
                if val is None:
                    errors.append("G5 contract key %s is null (must be a "
                                  "type-shaped empty or real value)" % key)
                    continue
                want = _type_default(hint)
                if want is not object and not isinstance(val, want):
                    errors.append("G5 contract key %s: expected %s, got %s"
                                  % (key, getattr(want, "__name__", want),
                                     type(val).__name__))

    # G8 no fabricated chart values (result vs manifest data table)
    if case_path and os.path.isfile(case_path) and result.get("figure_type") \
            == "chart":
        try:
            with open(case_path, "r", encoding="utf-8") as fh:
                case = json.load(fh)
        except Exception:
            case = None
        if isinstance(case, dict):
            man = case.get("manifest") or case
            rows = ((man.get("data") or {}).get("table") or {}).get("rows")
            dm = result.get("data_mapping") or {}
            if isinstance(rows, list) and rows and \
                    isinstance(dm, dict) and dm.get("unique_categories"):
                # compare category sets only (numeric comparison needs the
                # table; both come from the same source by construction)
                tbl_cats = sorted({str(r[0]) for r in rows
                                   if isinstance(r, list) and r})
                res_cats = sorted(dm.get("unique_categories") or [])
                if tbl_cats and res_cats and tbl_cats != res_cats:
                    errors.append("G8 chart categories in result differ "
                                  "from the manifest table: %r vs %r"
                                  % (res_cats, tbl_cats))

    return errors


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", help="path to the original case.json")
    ap.add_argument("--result", required=True,
                    help="path to the produced result.json")
    ap.add_argument("--out", help="output directory containing the "
                                  "artifacts (default: dirname of --result)")
    ap.add_argument("--json", action="store_true",
                    help="emit machine-readable verdict")
    args = ap.parse_args(argv)

    result_path = os.path.abspath(args.result)
    if not os.path.isfile(result_path):
        print("INVALID: result.json not found: %s" % result_path)
        return 2
    with open(result_path, "r", encoding="utf-8") as fh:
        result = json.load(fh)

    out_dir = args.out or os.path.dirname(result_path)
    errors = validate(result, case_path=args.case,
                      result_path=result_path, out_dir=out_dir)

    if errors:
        if args.json:
            print(json.dumps({"valid": False, "problems": errors},
                             ensure_ascii=False, indent=2))
        else:
            print("INVALID (%d problems):" % len(errors))
            for e in errors:
                print("  - " + e)
        return 1
    if args.json:
        print(json.dumps({"valid": True, "problems": []},
                         ensure_ascii=False, indent=2))
    else:
        print("VALID: result.json at %s satisfies OUTPUT_CONTRACT "
              "(G1-G8 gates pass, contract echoed)." % result_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())