# -*- coding: utf-8 -*-
"""cli_io.py — console hardening shared by this Skill's CLI entry points.

Why: every CLI here prints JSON with `ensure_ascii=False` (readable Chinese in
logs). On a host whose stdout encoding is not UTF-8 — a Windows cp936 console or
a Linux container started with LC_ALL=C — that print can raise
UnicodeEncodeError *after* the artifacts were written, turning a successful run
into a traceback and a non-zero exit code. `harden_console()` switches the
streams to UTF-8 with errors="replace" so logging can never break a delivery.

It is deliberately tiny and side-effect free: it only touches sys.stdout /
sys.stderr, never the files we write (those already pass encoding="utf-8"
explicitly), and it never raises.

Usage (first line of any CLI main):
    import cli_io; cli_io.harden_console()
"""
from __future__ import annotations

import sys


def harden_console():
    """Best-effort: make stdout/stderr UTF-8 and never raise on encode errors.

    Returns a small record ({"stdout": enc, "stderr": enc, "changed": bool})
    that callers may ignore; failures are swallowed by design.
    """
    rec = {"changed": False, "stdout": None, "stderr": None}
    for name, stream in (("stdout", sys.stdout), ("stderr", sys.stderr)):
        try:
            enc = (getattr(stream, "encoding", None) or "").lower()
            rec[name] = enc
            if enc.replace("-", "") not in ("utf8", "utf8mb4", "cp65001"):
                stream.reconfigure(encoding="utf-8", errors="replace")
                rec[name] = "utf-8 (reconfigured)"
                rec["changed"] = True
        except Exception:
            pass
    return rec


if __name__ == "__main__":
    import json
    print(json.dumps(harden_console(), ensure_ascii=False))
