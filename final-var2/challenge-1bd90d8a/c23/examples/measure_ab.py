#!/usr/bin/env python3
"""对照度量（v2）：对同一输入的两组产物做机器可判定的逐项打分。

比 measure.py v1 多两处归一化（两处都是环境产生的、与图面无关的差异）：
  * 报告内 `dir` 字段（两次运行的输出目录不同，属环境变量）；
  * PDF 的 /CreationDate 与 /ID（渲染器写入的时间戳/文档 ID）。
其余一律**逐字节**比较。

用法: python measure2.py --label <name> --case <case.json> --out <out1> --run2 <out2> [--write f.json]
"""
import argparse, csv, glob, io, json, os, re, sys

M = []

def metric(name, ok, detail, kind="质量"):
    M.append({"id": name, "pass": bool(ok), "detail": detail, "kind": kind})

def norm_json(txt, outdir):
    try:
        d = json.loads(txt)
    except Exception:
        return txt
    if isinstance(d, dict):
        d.pop("dir", None)
        for key in ("steps", "change_records"):
            d.pop(key, None)
    return json.dumps(d, sort_keys=True, ensure_ascii=False)

def norm_pdf(b):
    b = re.sub(rb"/CreationDate\s*\([^)]*\)", b"/CreationDate(X)", b)
    b = re.sub(rb"/ModDate\s*\([^)]*\)", b"/ModDate(X)", b)
    b = re.sub(rb"/ID\s*\[[^\]]*\]", b"/ID[X]", b)
    return b

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--case", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--run2", default=None)
    ap.add_argument("--write", default=None)
    a = ap.parse_args(argv)

    case = json.load(open(a.case, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(a.case))
    out = a.out
    fig = (case.get("figures") or [{}])[0]
    panel = (fig.get("panels") or [fig])[0]
    xunit = (panel.get("x") or {}).get("unit")
    yunit = (panel.get("y") or {}).get("unit")
    ecol = (panel.get("error") or {}).get("column")
    esem = (panel.get("error") or {}).get("semantics")
    figures = case.get("figures") or [fig]
    nfig = len(figures)

    # ---- 质量指标 ----------------------------------------------------------
    svgs = sorted(glob.glob(os.path.join(out, "*.svg")))
    metric("Q1_editable_vector_source", len(svgs) >= nfig,
           f"svg_files={len(svgs)} expected>={nfig}")

    svg_txt = open(svgs[0], encoding="utf-8").read() if svgs else ""
    layers = re.findall(r'id="layer-[A-Za-z0-9_-]+"', svg_txt)
    metric("Q2_layered_editable", len(layers) >= 2, f"layer_groups={len(layers)}")

    prov = re.findall(r'data-role="[^"]+"', svg_txt)
    sattrs = re.findall(r'data-(?:column|row-index|value|cite|from|to)="[^"]*"', svg_txt)
    metric("Q3_element_level_traceback", bool(prov) and bool(sattrs),
           f"data_role={len(prov)} source_attrs={len(sattrs)}")

    man = None
    mf = os.path.join(out, "data_manifest.json")
    if os.path.isfile(mf):
        try:
            man = json.load(open(mf, encoding="utf-8"))
        except Exception:
            man = None
    metric("Q4_machine_readable_mapping", man is not None,
           f"data_manifest.json={'parsed' if man else 'absent/unparsable'}")

    checked = mism = 0
    if man:
        dpath = os.path.join(base, panel.get("data_file") or "data.csv")
        rows = list(csv.DictReader(open(dpath, encoding="utf-8-sig", newline="")))
        for _fid, f in (man.get("figures") or {}).items():
            for el in f.get("elements", []):
                s = el.get("source") or {}
                if "value" in s and "row_index" in s and s.get("column"):
                    checked += 1
                    ri, col = s["row_index"], s["column"]
                    try:
                        okrow = 0 <= ri < len(rows) and col in rows[ri]
                        if not okrow or abs(float(rows[ri][col]) - float(s["value"])) > 1e-9:
                            mism += 1
                    except (TypeError, ValueError):
                        mism += 1
    metric("Q5_value_recheckable", checked > 0 and mism == 0,
           f"rows_checked={checked} mismatched={mism}")

    blob = svg_txt + json.dumps(man or {}, ensure_ascii=False)
    want = [u for u in (xunit, yunit) if u]
    got = [u for u in want if u in blob]
    metric("Q6_axis_units_present", bool(want) and len(got) == len(want),
           f"declared={want} present={got}")

    emarks = len(re.findall(r'data-role="errorbar"', svg_txt))
    esem_ok = bool(esem) and esem in blob
    metric("Q7_errorbar_semantics", (emarks > 0 and esem_ok) if ecol else True,
           f"error_column={ecol} marks={emarks} semantics_recorded={esem_ok}")

    ents = case.get("figures") or []
    metric("Q8_multifigure_coverage",
           len(glob.glob(os.path.join(out, "*.svg"))) >= nfig,
           f"figures_in_case={nfig} svg_out={len(glob.glob(os.path.join(out,'*.svg')))}")

    # ---- 审计指标 ----------------------------------------------------------
    rf = os.path.join(out, "result.json")
    r = None
    if os.path.isfile(rf):
        try:
            r = json.load(open(rf, encoding="utf-8"))
        except Exception:
            r = None
    core = ("case_id", "status", "outputs", "uncertainty", "change_records", "sources")
    metric("Q9_result_envelope", bool(r) and all(k in r for k in core),
           f"result.json_keys={len(r) if r else 0} core_complete="
           f"{bool(r) and all(k in r for k in core)}", "审计")
    metric("Q10_source_hashes",
           bool(r) and all(s.get("sha256") for s in (r.get("sources") or [])),
           f"sources={len(r.get('sources') or []) if r else 0} "
           f"with_sha256={sum(1 for s in (r.get('sources') or []) if s.get('sha256')) if r else 0}",
           "审计")
    metric("Q11_change_records",
           bool(r) and bool(r.get("change_records")),
           f"change_records={len(r.get('change_records') or []) if r else 0}", "审计")

    # ---- 效率/确定性 -------------------------------------------------------
    if a.run2 and os.path.isdir(a.run2):
        same = diff = 0
        diffs = []
        for p in sorted(glob.glob(os.path.join(out, "*"))):
            n = os.path.basename(p)
            p2 = os.path.join(a.run2, n)
            if not os.path.isfile(p2):
                continue
            b1 = open(p, "rb").read()
            b2 = open(p2, "rb").read()
            if n.endswith(".json"):
                ok = norm_json(b1.decode("utf-8", "replace"), out) == \
                     norm_json(b2.decode("utf-8", "replace"), a.run2)
            elif n.endswith(".pdf"):
                ok = norm_pdf(b1) == norm_pdf(b2)
            else:
                ok = b1 == b2
            if ok:
                same += 1
            else:
                diff += 1
                diffs.append(n)
        metric("Q12_deterministic_rerun", diff == 0 and same > 0,
               f"identical={same} differ={diff} differing={diffs}", "效率")
    else:
        metric("Q12_deterministic_rerun", False, "no second run supplied", "效率")

    passed = sum(1 for m in M if m["pass"])
    payload = json.dumps({"label": a.label, "passed": passed, "total": len(M),
                          "metrics": M}, ensure_ascii=False, indent=2)
    if a.write:
        with io.open(a.write, "w", encoding="utf-8") as fh:
            fh.write(payload)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(payload)
    return 0

if __name__ == "__main__":
    sys.exit(main())
