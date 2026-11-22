# paper-to-academic-ppt（失败注入与恢复演练版）

把论文/研究材料转成**主线清晰、证据可追溯、可编辑**的学术汇报 PPT，并且——
本版的重点——**在东西被弄坏时仍然可被信任**。

- 任务：`/input/case.json` + `/input/task.md` → `/app/output/`（可编辑 `.pptx`、
  PIL 近似预览、双形态逐页证据映射、契约完整的 `result.json`）；
- 主轴：`scripts/fault_inject.py` 对 **输入 / 模板 / 依赖 / 契约 / 状态** 五类形态
  逐条注入**真实故障**并实测"退出码 / status / uncertainty / 是否静默失败"，
  结果渲染成 `references/FAULT-MATRIX.md`（24 条注入、0 条静默失败）。

## 1. 依赖

| 依赖 | 必需性 | 缺失时的行为（已由注入验证） |
|-|-|-|
| Python ≥ 3.8（实测 3.13.9） | 必需 | — |
| `python-pptx` | **必需**（出 deck） | `deck=null` + `deck_error` + `status=failed`，**仍写出契约完整的 result.json**，退出码 1（不崩溃、不造假文件） |
| `Pillow` | 预览必需（也是 python-pptx 的依赖） | 预览栈整体不可用 ⇒ 同上一行；`previews=[]` |
| `matplotlib` | 可选（重建图） | 跳过重建图，`charts[].chart.reason` + uncertainty；主交付物不受影响 |
| `PyMuPDF` / `pypdf` / `pdfplumber` | 任一即可读 PDF | 逐级回退；全缺 ⇒ `run_meta.pdf_tools` 全 false + 按材料不可读处理 |

```bash
pip install python-pptx Pillow matplotlib pypdf
```

## 2. 快速开始（任意 cwd）

```bash
SKILL_DIR="<本包根目录>"        # 平台安装到 /skills/weekly-skill 时即该路径

# ① 端到端跑最小示例（先读 examples/README.md）
python "$SKILL_DIR/scripts/main.py" \
  --case "$SKILL_DIR/examples/case.json" \
  --spec "$SKILL_DIR/examples/deck-spec.json" \
  --out "<某个空输出目录>"

# ② 两道交付门
python "$SKILL_DIR/scripts/export_check.py" --result "<out>/result.json" \
  --out-dir "<out>" --case "$SKILL_DIR/examples/case.json"
python "$SKILL_DIR/scripts/check_contract.py" --result "<out>/result.json" \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case "$SKILL_DIR/examples/case.json"

# ③ 本版主轴：失败注入 + 恢复演练（务必在**包外副本**上跑）
cp -r "$SKILL_DIR" /tmp/skill-drill
python /tmp/skill-drill/scripts/fault_inject.py --out /tmp/drill \
  --emit-matrix /tmp/drill/matrix.md
```

健康基线应当是：`main.py` `exit 0` / `status=completed` / 顶层字段 19 个 /
`uncertainty` 0 条 / `export_check` exit 0 / `check_contract` exit 0。
不满足就别看注入结论——`fault_inject.py` 自己也会在这种情况下以 **exit 2** 拒绝出结论。

## 3. 目录

```
SKILL.md                    执行流程 S0–S6 + 决策表 D01–D18 + 演练用法
README.md                   本文件：依赖 / 快速开始 / 目录 / 限制 / 维护
TEST.md                     自测清单与期望输出（含注入演练的期望矩阵）
GITHUB_URL.txt              公开链接
references/
  FAULT-MATRIX.md           ★ 24 条注入的实测矩阵 + 判定口径 + 修复点名 + 扩展指南
  OUTPUT_CONTRACT.md        result.json 契约（19 字段 / 四形态 / G1–G8）★ 单一事实源
  failure-modes.md          五类异常处置 + 退出码语义 + §5 检测能力边界
  RUBRIC_MAP.md             五维（40/25/15/10/10）落点 + 复核命令
  slide-blueprint.md        论文→页面蓝图 + deck-spec schema
  layer-naming.md           分层命名规范
scripts/
  main.py                   端到端编排（--case/--task/--spec/--materials/--out/--demo/--verbose）
  fault_inject.py           ★ 注入 + 恢复演练 + 矩阵渲染（--out/--work/--skill/--only/--emit-matrix/--json/--quiet）
  assetkit.py              材料定位 / PDF 抽取 / 重建图（--pdf/--out）
  deckgen.py               模板适配（含损坏回退）/ 排版 / 备注 / 命名
  ooxml_kit.py             主题字体 / 命名 / zip+XML 健全检查
  spec_lint.py             CP1 结构校验（--spec）
  export_check.py          CP3 导出检查（--result/--out-dir/--case）
  check_contract.py        契约字段覆盖（--result/--contract/--case/--quiet）
  preview.py               PIL 近似预览
  make_template.py         运行期生成回退模板（--out/--name/--no-starter）
  make_synthetic_inputs.py 运行期生成合成夹具（--out）
  cli_io.py                控制台 UTF-8 加固
examples/                   最小示例（合成案例，非正式案例）+ 运行结果示意副本
```

## 4. 本版相对基线的实质变化

1. **新增 `scripts/fault_inject.py`**：五类形态 24 条真实故障注入 + 恢复演练 +
   Markdown 矩阵渲染；只写 `--out`/`--work`，子进程带 `PYTHONDONTWRITEBYTECODE=1`，
   破坏技能包的那条注入改的是**临时副本**。
2. **新增 `references/FAULT-MATRIX.md`**：实测账本（含"修复前 vs 修复后"的逐条点名）。
3. **`main.py` / `deckgen.py` 的 8 处纯增量修复**（见 FAULT-MATRIX §4）：模块级 import
   崩溃 ⇒ 降级；无 deck 却报成功 ⇒ 失败；契约 list 形态不落字段 ⇒ 四形态齐全；
   损坏模板丢 deck ⇒ 回退内置版式。**CLI 参数与退出码语义未变**。
4. **决策表 D01–D18**：把"模板损坏"与"模板缺席"分成两条不同状态词的分支；
   新增"方案不可解析""无方案""契约文档缺失"三条。
5. **`failure-modes.md` §5**：如实申报三格**检测能力边界**（伪造 status / 抹掉
   uncertainty / `case_id` 外联对照）与对应的人工兜底动作。

## 5. 适用范围与限制

- **适用**：单篇论文/研究报告 → 8–20 页学术汇报；材料可为 PDF/文本/LaTeX。
- **不适用**：判断论文结论真假、重画科研图、润色正文、与材料无关的通用幻灯片。
- 预览是 **PIL 近似**，不等于 PowerPoint/LibreOffice 渲染；无 Office 引擎时文件名
  带 `approx`、`previews[].kind=pil-approximation`、`run_meta.rendered_with` 三处标注。
- 模板适配是"占位符级"：SmartArt 等复杂版式不重排；模板自带形状**不改名**。
- 包内**只携带文本资源**（`.md/.py/.json/.txt/.csv/.yaml/.yml`）；模板、预览、重建图
  一律**运行时生成**（因此首次运行前需要 `python-pptx`）。
- 失败注入证明的是**可观测性**（坏了会不会被看见），不是**可用性**（坏了还能不能交出
  好 PPT）；覆盖面是 24 类故障，不是"任意环境任意故障"。

## 6. 维护

- 版本：`scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；
- 改任一降级行为 ⇒ **重跑 `fault_inject.py` 并重新渲染 `FAULT-MATRIX.md`**（旧数字作废）；
- 改 D 规则 ⇒ 同步 `references/failure-modes.md` 同号条目与 `RUBRIC_MAP.md` 复核命令；
- 新增故障形态 ⇒ 在 `fault_inject.injections()` 追加一条（模板见 FAULT-MATRIX §6）；
- 新增脚本 ⇒ 在 `SKILL.md` §3 资源清单与 `TEST.md` 自测清单各补一行。
