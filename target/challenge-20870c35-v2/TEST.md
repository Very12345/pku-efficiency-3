# TEST.md — 本地实测记录（challenge-20870c35 v2 加强包）

- 测试时间：2026-11-21 02:00–02:10 +08（Asia/Shanghai）
- 测试机：Windows（Git Bash / MSYS2），Python 3.13.9（Anaconda）
- 代码状态：本目录全部文件，`scripts/` 13 个 Python 脚本最后一次 py_compile 通过后未再改动
- 测试类型：语法编译 / 主流程 smoke / 独立复核四件套 / 双跑确定性 / 包约束

## 1. 环境确认

```
$ python --version
Python 3.13.9
$ python -c "import pptx,PIL; print('python-pptx',pptx.__version__,'| Pillow',PIL.__version__)"
python-pptx 1.0.2 | Pillow 12.3.0
$ python -c "import pypdf; print('pypdf',pypdf.__version__)"
pypdf 6.14.2
```

## 2. 语法检查（T1）

```
$ python -m py_compile scripts/*.py
=> 无输出，退出码 0（COMPILE_OK，13/13 脚本）
```

## 3. 主流程实测（T2 · 验收 smoke）

命令（即父任务验收形态）：

```
$ python scripts/main.py --case examples/case.json --out "D:/BuildTemp/smoke-challenge-20870c35-v2"
[plan] 12 pages, narrative=group_meeting, audience=familiar, P-gates valid=True
[deck] 12 slides, mode=built-in-theme, verify valid=True
[preview] wrote 13 preview files (PIL simulation)
[done] status=completed deck_ok=True preview_ok=True plan_gates=True evidence_audit=True validate_valid=True contract_valid=True
[done] output: D:\BuildTemp\smoke-challenge-20870c35-v2
退出码 0
```

实际产出（D:/BuildTemp/smoke-challenge-20870c35-v2，均为真实文件）：

```
deck_audit.json  editable_deck.pptx  evidence_audit.json  evidence_map.json
plan_gates.json  previews/{cover_preview.png, preview_grid.png, preview_manifest.json,
                         slide_002..011.png (10 张)}  result.json  self_check.json  talk_plan.json
```

单次运行耗时实测：约 3.1 秒（`time python scripts/main.py … --quiet` → real 0m3.086s）。

## 4. 独立复核四件套（T3–T6）

| 测试 | 命令 | 退出码 |
|-|-|-|
| T3 结构+文件+数字校验 | `python scripts/validate_result.py smoke/result.json` | 0 |
| T4 契约齐全校验 | `python scripts/check_contract.py smoke/result.json` | 0 |
| T5 证据逐字审计 | `python scripts/evidence_audit.py smoke/result.json` | 0 |
| T6 deck 机器校验 | `python scripts/verify_deck.py smoke/editable_deck.pptx --expect-pages 12 --plan smoke/talk_plan.json` | 0 |

result.json 自检（smoke/self_check.json）：
- `validate.checks`：10/10 ok，errors=[]；
- `contract_check`：declared=16 missing=0 wrong_type=0（16 个契约字段全部在场且类型正确）；
- `audit.gates`：G1–G9 = true，G10 = 包约束（由 selftest --package-check 执行）；
- `audit.evidence.summary`：{pages_total=12, content_pages=10, ok_pages=10, errors=0,
  derived_pages=0, unavailable_text=0}（10 个内容页逐字引文全部命中源文本）；
- `audit.deck`：valid=true，slides=12。

## 5. selftest 全链路复核（T7）

```
$ python scripts/selftest.py "D:/BuildTemp/smoke-challenge-20870c35-v2" --package-check "$PWD"
=> checks=6 errors=0, SELFTEST_EXIT=0
  validate_result ✓  check_contract ✓  evidence_audit ✓  verify_deck ✓
  determinism_probe ✓（plan=41ba17847b52… emap=6a5d2847678c…）
  package_constraints ✓ {text=43, total_bytes=1219274, max_file=101149, symlinks=[], pycache=[]}
```

包约束（G10）同时为平台硬约束核对：**43 个 UTF-8 文本文件（≤50）、单文件最大
~101KB（≤500KB）、总约 1.22MB（≤2MB）、无符号链接、无 __pycache__**。

## 6. 确定性双跑（T8）

依次两次运行同一命令（输出到两个目录）：

```
$ python scripts/main.py --case examples/case.json --out A
$ python scripts/main.py --case examples/case.json --out B
```

| 文件 | A vs B |
|-|-|
| evidence_map.json / evidence_audit.json / plan_gates.json / deck_audit.json | 逐字节相同 |
| previews/*.png（12 张：封面+10 内容页+网格） | 逐字节相同 |
| editable_deck.pptx | 全部 zip 成员逐字节相同；整文件 sha 仅差 zip 目录时间戳 |
| talk_plan.json / result.json / preview_manifest.json | 内容相同，仅记录性时间戳（generated_at/change_records.at）不同 |

确定性探针（`self_check.determinism`，剔除记录性时间戳后的内容投影 sha）A/B 两次完全一致：

```
run1 plan_sha16=41ba17847b521bc6 emap=6a5d2847678c36dc deck=5c2dc70ae73b91f5
run2 plan_sha16=41ba17847b521bc6 emap=6a5d2847678c36dc deck=5c2dc70ae73b91f5
deck 规范化 sha256（剔除 docProps/core.xml）= 5c2dc70ae73b91f56794fb327d6f0f445ee3beecaf96909a18fd4c47a0d6c4a8
```

结论：**输入相同 → 页面内容、证据、deck、预览全部逐位一致**；唯一差异是记录性时间戳，
已在探针中显式排除并如实记录（符合"确定性双跑一致或如实记录"）。

## 7. 示例输出（T9 · examples/output）

`examples/output/` 由本机真实运行产出（与 T2 同命令不同目录），文件与 smoke 一致，
`case.json`/`task.md` 均带"示例，非正式案例"标注；`templates/slide-checklist-template.md`
供人核。已在包内随附，重新运行 `python scripts/main.py --case examples/case.json
--out examples/output` 可复现。

## 8. 边界场景自测（T10，脚本/降级路径）

- PDF 解析器缺失 → `evidence.load_material` 记 parsed=false 并降级（示例已含 PDF 且本机
  pypdf 存在，走正常解析路径）；
- 材料缺失 → sources 记 kind=missing；缺图 → 诚实占位框（示例中 Fig. 3/Table 1 无图片文件，
  evidence_audit 如实记录 figure_bound=false，不虚构）；
- 无模板 → 内置主题（示例即此路径，deck_mode=built-in-theme）。

## 9. 已知限制 / 残余说明

- 预览为 Pillow 模拟渲染（水印 + manifest），非 Office 栅格化；deck 以 .pptx 打开为准；
- `result.audit.gates.G10` 设计为 None（由 selftest --package-check 执行），非缺陷；
- 平台 3 案例 × 3 复跑由平台执行，本机仅记录可复现性的实证（T8）。