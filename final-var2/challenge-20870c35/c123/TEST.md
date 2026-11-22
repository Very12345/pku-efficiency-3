# TEST.md — 本地实测记录（challenge-20870c35 · v3 机制与复用版）

- 测试时间：2026-11-22 18:20–18:26 +08（Asia/Shanghai）
- 测试机：Windows（Git Bash / MSYS2），Python 3.13.9（Anaconda），python-pptx 1.0.2 / Pillow 12.3.0 / pypdf 6.14.2
- 被测对象：本目录全部文件（14 个既有脚本 + `scripts/gain_ab.py`，以及本版新增的
  `references/MECHANISM.md`、`references/REUSE-KIT.md`、`assets/case-set.json`、`assets/page-gold-standard.json`）
- 测试方式：把包**复制到包外临时目录**（本机为系统临时盘下的纯 ASCII 目录）再跑，
  **绝不在提交目录里跑脚本**（否则生成 `__pycache__`，平台预检直接拒收）
- 覆盖：语法编译 / 新增资产可用性 / 主流程 smoke / **对照装置复跑并与随包记录对拍** /
  降级用例（沿用同一批脚本路径）/ 全链路自检 / 包约束

## 1. 语法与新增资产（T1）

```
$ for f in scripts/*.py; do python -m py_compile "$f" || exit 1; done     # 15/15 通过
$ python -c "import json; json.load(open('assets/case-set.json',encoding='utf-8'))"
$ python -c "import json; json.load(open('assets/page-gold-standard.json',encoding='utf-8'))"
两个资产 JSON 均可解析：case-set 含 3 个输入骨架 + output_contract 16 字段；
page-gold-standard 含 3 类汇报的块顺序 + 每页必填字段 + 4 条机器判定命令。
```

## 2. 主流程 smoke（T2）

```
$ python scripts/make_synthetic_inputs.py            # 运行时生成示例 PDF/PNG
$ python scripts/main.py --case examples/case.json --out <W>/out-A --quiet
status=completed pages=12 deck=True validate_valid=True contract_valid=True
exit=0
```

## 3. ★ 对照装置复跑并与随包记录对拍（T3）

```
$ python scripts/gain_ab.py --case examples/case.json --work <W>/gain --skill-dir <pkg>
arm A (baseline emulator): slides=12 notes=0.00 max_paras=2 pics=0 rounds=2 0.19s
arm B (this Skill):        slides=12 notes=1.00 locators=1.0 qa=4 result_keys=20 exit=0 1.50s
exit=0
```

把本次实测结果与随包记录 `references/gain-run-record.json` 逐项对拍（同一台机器、同一输入）：

| 对比项 | 结果 |
|-|-|
| A 臂 D 组指标（slides / notes_coverage / max_body_paragraphs / mean_paragraph_chars / verbatim_grounded_ratio / numbers_in_source_ratio / embedded_pictures） | **逐项相同** |
| B 臂 D 组指标 | **逐项相同** |
| B 臂 C 组指标（顶层键数 / 定位覆盖率 / 证据行 / 问答 / 门与审计 / 预览数） | **逐项相同** |

⇒ 对照装置与记录**互相印证**：记录不是手写表格，装置可在任何机器上复跑出同一组结构性数字
（墙钟时间 E1 会有机器噪声：本次 1.50 s vs 记录中的 1.67 s）。
完整数字与解释（含**两项 A 臂更优**的指标）见 `references/GAIN-PROTOCOL.md` §6/§7。

## 4. 降级用例（T4，沿用同一批脚本）

```
# 遮蔽 python-pptx
$ PYTHONPATH=<W>/shim python scripts/main.py --case examples/case.json --out <W>/out-X --quiet
[deck] SKIPPED (dependency missing): python-pptx 不可用（blocked）
status=partial pages=12 deck=False validate_valid=True contract_valid=True     # exit=0
editable_deck=None  deck_limitation=python-pptx 不可用（blocked）  uncertainty=4 条
```

⇒ 对应 `MECHANISM.md` M6/M7 的降级纪律：`status` 降级 + `uncertainty` 三要素 +
`change_records` 留痕，且**命令仍返回 0**。

## 5. 全链路自检与包约束（T5）

```
$ python scripts/selftest.py <W>/out-A --package-check <pkg>
"summary": "checks=6 errors=0"        # validate / contract / evidence / deck / determinism / package
exit=0
```

- `validate`：10/10 checks ok、`errors=[]`
- `contract_check`：`declared=16 missing=0 wrong_type=0`
- `audit.plan_gates`：P1–P8 全过（`P3 pages=12 target=12`）
- `audit.evidence.summary`：`content_pages=10, ok_pages=10, errors=0`
- `audit.deck`：`valid=true`，12 页，每页 `notes_nonempty=true`

## 6. 提交资源形态

```
提交目录: 46 个文件（上限 50）；扩展名 = .md / .py / .json / .txt（全部在允许的七种内）
总字节 407,281 B（上限 2MB）；最大单文件 42,426 B（上限 500KB）
无符号链接、无 __pycache__/*.pyc（所有脚本都在包外副本上运行）
```

## 7. 已知限制

- 对照是**单案例、单机**的机制与可测性证据，**不是**平台白板、**不是**平台分数；
- A 臂是作者按题面描述忠实实现的**代理臂**，不是平台真实基础 Agent；
- `assets/case-set.json` 与 `assets/page-gold-standard.json` 只给输入骨架与结构标准，
  **不含内容答案**；
- 预览为 PIL 示意；证据定位是行级/章节级近似锚点；
- 平台 3 案例 × 3 复跑由平台执行，本节只给出本机可复现性证据。
