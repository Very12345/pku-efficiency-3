# TEST.md — 本地实测记录（challenge-20870c35 · v2 增益可验证版）

- 测试时间：2026-11-22 18:10–18:22 +08（Asia/Shanghai）
- 测试机：Windows（Git Bash / MSYS2），Python 3.13.9（Anaconda），python-pptx 1.0.2 / Pillow 12.3.0 / pypdf 6.14.2
- 被测对象：本目录全部文件（14 个既有脚本 + **本版新增 `scripts/gain_ab.py`**）
- 测试方式：把包**复制到包外临时目录**（本机为系统临时盘下的纯 ASCII 目录）再跑，
  **绝不在提交目录里跑脚本**（否则生成 `__pycache__`，平台预检直接拒收）
- 覆盖：语法编译 / 主流程 smoke / **对照装置两次复跑** / 两条降级用例 / 全链路自检 / 包约束

## 1. 语法与 smoke（T1）

```
$ for f in scripts/*.py; do python -m py_compile "$f" || exit 1; done     # 15/15 通过（含 gain_ab.py）
$ python scripts/main.py --case examples/case.json --out <W>/out-A --quiet
status=completed pages=12 deck=True validate_valid=True contract_valid=True
exit=0
```

## 2. ★ 对照装置复跑（T2：本版的核心测试）

```
$ python scripts/gain_ab.py --case examples/case.json --work <W>/gain1 --skill-dir <pkg>
arm A (baseline emulator): slides=12 notes=0.00 max_paras=2 pics=0 rounds=2 0.26s
arm B (this Skill):        slides=12 notes=1.00 locators=1.0 qa=4 result_keys=20 exit=0 1.67s
exit=0
$ python scripts/gain_ab.py --case examples/case.json --work <W>/gain2 --skill-dir <pkg>
arm B: … exit=0 1.78s          # 第二次复跑
```

两次复跑的 D 组（deck 级）指标**逐项相等**（度量器本身确定性）：
唯一差异是 E1 墙钟时间（1.67 s vs 1.78 s，机器噪声）。

**A 臂的关键过程量**：`pages_before_rework = 3`（首轮按材料长度只排出 3 页）
→ `rerun_rounds_to_frozen = 2`（返工 1 轮后才对齐冻结 12 页）。
**B 臂**：`rerun_rounds_to_frozen = 1`，`contract.page_count_delta_vs_frozen = 0`。

实测数字全表与解释（含**两项 A 臂更优**的指标）见 `references/GAIN-PROTOCOL.md` §6/§7；
原始 JSON 见 `references/gain-run-record.json`（由装置直出，未手工编辑）。

## 3. 降级用例（T3 / T4）

```
# T3 遮蔽 python-pptx
$ PYTHONPATH=<W>/shim python scripts/main.py --case examples/case.json --out <W>/out-X --quiet
[deck] SKIPPED (dependency missing): python-pptx 不可用（blocked）
status=partial pages=12 deck=False validate_valid=True contract_valid=True     # exit=0
editable_deck=None  deck_limitation=python-pptx 不可用（blocked）  uncertainty=4 条

# T4 材料缺失（case.json 移到材料目录之外 → 4 个材料全部找不到）
$ python scripts/main.py --case <W>/case-missing.json --out <W>/out-M --quiet
status=partial pages=12 deck=True validate_valid=True contract_valid=True     # exit=0
sources = [(paper_extract.md, missing), (figures.md, missing),
           (dataset_card.pdf, missing), (absent.pdf, missing)]
```

两条降级路径都满足"三处记录"纪律：`status` 降级 + `uncertainty`（含 item/impact/mitigation）
+ `change_records`（含 at/step/action），且**命令仍返回 0**。

## 4. 全链路自检与包约束（T5）

```
$ python scripts/selftest.py <W>/out-A --package-check <pkg>
"summary": "checks=6 errors=0"
exit=0
```

- `validate`：10/10 checks ok、`errors=[]`
- `contract_check`：`declared=16 missing=0 wrong_type=0`
- `audit.gates`：G1–G9 true（G10 由 `--package-check` 执行）
- `audit.plan_gates`：P1–P8 全过（`P3 pages=12 target=12`）
- `audit.evidence.summary`：`content_pages=10, ok_pages=10, errors=0`
- `audit.deck`：`valid=true`，12 页，每页 `notes_nonempty=true`

## 5. 提交资源形态

```
提交目录: 42 个文件；扩展名 = .md / .py / .json / .txt（全部在允许的七种内）
总字节 379,320 B（上限 2MB）；最大单文件 42,426 B（上限 500KB）
无符号链接、无 __pycache__/*.pyc（所有脚本都在包外副本上运行）
```

## 6. 已知限制

- 对照是**单案例、单机**的机制与可测性证据，**不是**平台白板、**不是**平台分数；
- A 臂是作者按题面描述忠实实现的**代理臂**，不是平台真实基础 Agent 的运行；
- 预览为 PIL 示意（带水印），只证明"布局可检查"；
- `gain_ab.py` 的 D6/D7 两项在 A 臂上更好，原因与不可比性写在 `GAIN-PROTOCOL.md` §7.1；
- 平台 3 案例 × 3 复跑由平台执行，本节只给出本机可复现性证据。
