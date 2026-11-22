# paper-to-academic-ppt（全维 union 版）

把论文/研究材料转成**主线清晰、证据可追溯、可编辑**的学术汇报 PPT。
本包是 union 包：把 R1 三轮（决策规则 / 增益可验证 / 机制与复用）与 R2 两轮
（失败注入 / 多案例题集）的**实质内容全部并进来**，再用一份重排过的 SKILL.md 索引。

| 维度 | 可执行物 | 实测结论（本机，2026-11-22） |
|-|-|-|
| 执行 | `scripts/main.py` | 三个案例 `exit 0` / `completed` |
| 失败 | `scripts/fault_inject.py` → `references/FAULT-MATRIX.md` | **24 条注入 · 静默失败 0 · 恢复 19/19** |
| 泛化 | `scripts/run_case_set.py` → `references/CASE-SET.md` | **3/3 案例在验收区间内** |
| 增益 | `scripts/gain_probe.py` → `references/GAIN-PROTOCOL.md` | 三臂结构性对照（不预测平台分） |
| 机制 | `references/MECHANISM.md` | 9 项机制 + "没有它会怎样" |
| 复用 | `references/REUSE-KIT.md` | 五步移植 + 检查清单 |
| 判断 | `references/DECISION-RULES.md` | D01–D16 / H01–H14 / M01–M14 + I1–I6 |

## 1. 依赖

| 依赖 | 必需性 | 缺失时（已由注入实测） |
|-|-|-|
| Python ≥ 3.8（实测 3.13.9） | 必需 | — |
| `python-pptx` | **必需**（出 deck） | `deck=null` + `deck_error` + `status=failed`，**仍写 result.json**，退出码 1（不崩溃、不造假） |
| `Pillow` | 预览必需（也是 python-pptx 的依赖） | 渲染栈整体不可用 ⇒ 同上一行；`previews=[]` |
| `matplotlib` | 可选（重建图） | 跳过重建图，`charts[].chart.reason` + uncertainty |
| `PyMuPDF`/`pypdf`/`pdfplumber` | 任一即可读 PDF | 逐级回退；全缺 ⇒ 按材料不可读处理 |

```bash
pip install python-pptx Pillow matplotlib pypdf
```

## 2. 快速开始（任意 cwd）

```bash
SKILL_DIR="<本包根目录>"

# ① 最小示例
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --spec "$SKILL_DIR/examples/deck-spec.json" --out "<空输出目录>"

# ② 失败注入 + 恢复演练（24 条；期望 exit 0）
cp -r "$SKILL_DIR" /tmp/skill-drill
python /tmp/skill-drill/scripts/fault_inject.py --out /tmp/drill \
  --emit-matrix /tmp/drill/matrix.md

# ③ 多案例题集（3 个题材；期望 exit 0）
cp -r "$SKILL_DIR" /tmp/skill-set
python /tmp/skill-set/scripts/run_case_set.py --out /tmp/case-out \
  --include-example --emit-md /tmp/case-out/case-set.md

# ④ 三臂增益对照（写 <scratch>，不污染包）
python "$SKILL_DIR/scripts/gain_probe.py" --out "<scratch>" \
  --arms baseline,skill,ablation --repeat 2
```

## 3. 目录

```
SKILL.md                      输入→执行→失败→增益→机制→复用（逐段索引到 reference）
README.md                     本文件
TEST.md                       三层自测清单 + 期望数字
GITHUB_URL.txt                公开链接
references/
  FAULT-MATRIX.md             ★ 24 条故障注入实测矩阵 + 判定口径 + 9 处修复点名 + 扩展指南
  CASE-SET.md                 ★ 题集：3 个题材 + 逐案实测 + 泛化失效边界 + 加案例流程
  DECISION-RULES.md           ★ D01–D16 / H01–H14 / M01–M14 三套编号 union + I1–I6 + 检查点对照
  MECHANISM.md                ★ 9 项机制 + 没有它会怎样
  GAIN-PROTOCOL.md            ★ 对照协议 + 指标定义 + 真实对照记录
  REUSE-KIT.md                ★ 可复用资产 + 五步移植 + 检查清单
  OUTPUT_CONTRACT.md          result.json 契约（19 字段 / 四形态 / G1–G8）★ 单一事实源
  failure-modes.md            五类异常 + 退出码 + 检测能力边界 + 六条回退链 + 机制归因
  RUBRIC_MAP.md               五维落点 + 复核命令
  slide-blueprint.md          论文→页面蓝图 + deck-spec schema
  layer-naming.md             分层命名规范
scripts/
  main.py                     端到端编排（--case/--task/--spec/--materials/--out/--demo/--verbose）
  fault_inject.py             ★ 24 条故障注入 + 恢复演练 + 矩阵渲染（--out/--work/--skill/--only/--emit-matrix/--json/--quiet）
  run_case_set.py             ★ 题集执行件（--out/--cases/--include-example/--only/--emit-md/--json/--quiet）
  gain_probe.py               ★ 三臂增益对照（--out 必填；--arms/--repeat/--json）
  assetkit.py                 材料定位 / PDF 抽取 / 重建图（--pdf/--out）
  deckgen.py                  模板适配（含损坏回退、图文同页左半幅）/ 排版 / 备注 / 命名
  ooxml_kit.py                主题字体 / 命名 / zip+XML 健全检查
  spec_lint.py                CP1 结构校验（--spec）
  export_check.py             CP3 导出检查（--result/--out-dir/--case）
  check_contract.py           契约字段覆盖（--result/--contract/--case/--quiet）
  preview.py                  PIL 近似预览
  make_template.py            运行期生成回退模板（--out/--name/--no-starter）
  make_synthetic_inputs.py    运行期生成合成夹具（--out）
  cli_io.py                   控制台 UTF-8 加固
examples/
  case.json / task.md / deck-spec.json / materials/paper-mini.txt   最小示例
  cases/case-muon-battery/     合成案例（实验物理）：case.json / material.md / deck-spec.json / expected.json
  cases/case-sleep-cohort/     合成案例（临床流行病学）：同结构
  output/                      示例案例的运行结果副本（文本形态，已净化路径）
```

## 4. union 了什么（相对基线）

| 来源 | 并进来的实质内容 | 落点 |
|-|-|-|
| **v4**（R2） | 24 条故障注入执行件 + 实测矩阵 + 9 处纯增量修复 | `scripts/fault_inject.py`、`references/FAULT-MATRIX.md` |
| **v5**（R2） | 两个不同题材的合成案例 + 题集执行件 + 验收区间 + 失效边界 | `examples/cases/`、`scripts/run_case_set.py`、`references/CASE-SET.md` |
| **v1**（R1） | 决策规则四列版 D01–D16、状态不变量 I1–I6、五类失败分支表 | `references/DECISION-RULES.md` §1/§4；`SKILL.md` §3 |
| **v2**（R1） | 增益断言 GA1–GA5、三臂对照协议、H01–H14 处置 | `references/GAIN-PROTOCOL.md`、`scripts/gain_probe.py`、`DECISION-RULES.md` §2 |
| **v3**（R1） | 9 项机制与"没有它会怎样"、六条回退链、M01–M14、可复用资产与五步移植 | `references/MECHANISM.md`、`REUSE-KIT.md`、`DECISION-RULES.md` §3、`failure-modes.md` §6–§7 |
| 基线 | 三层脚本骨架、契约、蓝图、命名、示例 | 原样保留（`scripts/*.py` 除两处纯增量修复外逐字节不变） |

## 5. 适用范围与限制

- **适用**：单篇论文/研究报告 → 8–20 页学术汇报；材料可为 PDF/文本/LaTeX。
- **不适用**：判断论文结论真假、重画科研图、润色正文、与材料无关的通用幻灯片。
- **已实测的题材**：计算机（示例）、实验物理（μ 子成像）、临床流行病学（队列）。
- **未验证、不得声称支持**（`CASE-SET.md` §4）：扫描件/图像型 PDF、>20 页大汇报、
  非中英文材料、真正的组织方模板、多篇材料合并。
- 预览是 **PIL 近似**；无 Office 引擎时三处标注（文件名 / `previews[].kind` / `rendered_with`）。
- 模板适配是"占位符级"：SmartArt 不重排；模板自带形状**不改名**。
- **三格检测缺口**（伪造 status / 抹掉 uncertainty / `case_id` 外联对照）：脚本门拦不住，
  必须按 `failure-modes.md` §5 的三条命令人工兜底。
- 包内只携带文本资源（`.md/.py/.json/.txt/.csv/.yaml/.yml`）；模板、预览、重建图运行时生成。

## 6. 维护（改什么就要重跑什么）

- 版本：`scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；
- 改降级行为 ⇒ **重跑 `fault_inject.py` 并重渲染 `FAULT-MATRIX.md`**（旧数字作废）；
- 改页级版式 ⇒ **重跑 `run_case_set.py` 并重渲染 `CASE-SET.md` §2**；
- 改机制 ⇒ 同步 `MECHANISM.md`；改 GA 指标 ⇒ 同步 `GAIN-PROTOCOL.md` §3 + `TEST.md` 新数字；
- 改 D/H/M 任一套规则 ⇒ 同步 `DECISION-RULES.md` 编号对照 + `failure-modes.md` 同号条目；
- 新增脚本/资产 ⇒ 在 `SKILL.md` §5/§6 与本文 §3 各补一行。
