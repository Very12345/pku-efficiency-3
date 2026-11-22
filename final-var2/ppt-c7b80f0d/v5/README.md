# paper-to-academic-ppt（多案例泛化题集版）

把论文/研究材料转成**主线清晰、证据可追溯、可编辑**的学术汇报 PPT，并且——
本版的重点——**换一个题材仍然成立，而且这件事可以被逐格复核**。

- 任务：`/input/case.json` + `/input/task.md` → `/app/output/`（可编辑 `.pptx`、
  PIL 近似预览、双形态逐页证据映射、契约完整的 `result.json`）；
- 主轴：`examples/cases/` 下两个**不同题材**的合成案例（实验物理 / 临床流行病学）
  + `scripts/run_case_set.py` 逐案真跑 + `references/CASE-SET.md` 的验收区间与失效边界。

## 1. 依赖

| 依赖 | 必需性 | 缺失时的行为 |
|-|-|-|
| Python ≥ 3.8（实测 3.13.9） | 必需 | — |
| `python-pptx` | **必需**（出 deck） | `deck=null` + `deck_error` + `status=failed`，**仍写出契约完整的 result.json**，退出码 1（不崩溃、不造假文件） |
| `Pillow` | 预览必需（也是 python-pptx 的依赖） | 预览栈整体不可用 ⇒ 同上一行；`previews=[]` |
| `matplotlib` | 可选（重建图） | 跳过重建图，`charts[].chart.reason` + uncertainty |
| `PyMuPDF` / `pypdf` / `pdfplumber` | 任一即可读 PDF | 逐级回退；全缺 ⇒ `run_meta.pdf_tools` 全 false + 按材料不可读处理 |

```bash
pip install python-pptx Pillow matplotlib pypdf
```

## 2. 快速开始（任意 cwd）

```bash
SKILL_DIR="<本包根目录>"

# ① 跑最小示例
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --spec "$SKILL_DIR/examples/deck-spec.json" --out "<某个空输出目录>"

# ② 本版主轴：跑整个题集（三个案例，逐条对验收区间）
cp -r "$SKILL_DIR" /tmp/skill-set
python /tmp/skill-set/scripts/run_case_set.py \
  --out /tmp/case-out --include-example --emit-md /tmp/case-out/case-set.md
#   退出码 0 = 全部在区间内；1 = 有案例越界（点名）；2 = 全部没产物；3 = 参数错

# ③ 两道交付门（对任意一次运行）
python "$SKILL_DIR/scripts/export_check.py" --result "<out>/result.json" \
  --out-dir "<out>" --case "<case.json>"
python "$SKILL_DIR/scripts/check_contract.py" --result "<out>/result.json" \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case "<case.json>"
```

## 3. 目录

```
SKILL.md                    执行流程 S0–S6 + 决策表 D01–D19 + 题集用法
README.md                   本文件
TEST.md                     自测清单与期望输出（含题集的期望数字）
GITHUB_URL.txt              公开链接
references/
  CASE-SET.md               ★ 题集定义 + 逐案实测表 + 失效边界 + 加案例流程
  OUTPUT_CONTRACT.md        result.json 契约（19 字段 / 四形态 / G1–G8）★ 单一事实源
  failure-modes.md          五类异常处置 + 退出码语义 + 检测能力边界
  RUBRIC_MAP.md             五维落点（实际效果 + 生态贡献为主轴）+ 复核命令
  slide-blueprint.md        论文→页面蓝图 + deck-spec schema
  layer-naming.md           分层命名规范
scripts/
  main.py                   端到端编排（--case/--task/--spec/--materials/--out/--demo/--verbose）
  run_case_set.py           ★ 题集执行件（--out/--cases/--include-example/--only/--emit-md/--json/--quiet）
  assetkit.py              材料定位 / PDF 抽取 / 重建图（--pdf/--out）
  deckgen.py               模板适配 / 排版 / 备注 / 命名（含图文同页的左半幅规则）
  ooxml_kit.py             主题字体 / 命名 / zip+XML 健全检查
  spec_lint.py             CP1 结构校验（--spec）
  export_check.py          CP3 导出检查（--result/--out-dir/--case）
  check_contract.py        契约字段覆盖（--result/--contract/--case/--quiet）
  preview.py               PIL 近似预览
  make_template.py         运行期生成回退模板（--out/--name/--no-starter）
  make_synthetic_inputs.py 运行期生成合成夹具（--out）
  cli_io.py                控制台 UTF-8 加固
examples/
  case.json / task.md / deck-spec.json / materials/paper-mini.txt   最小示例
  cases/case-muon-battery/    合成案例（实验物理）：case.json / material.md / deck-spec.json / expected.json
  cases/case-sleep-cohort/    合成案例（临床流行病学）：同结构
```

## 4. 本版相对基线的实质变化

1. **新增两个不同题材的合成案例**（`examples/cases/`），每个含输入材料、页级方案、
   验收区间（页数 / 证据行下限 / 必须逐字保留的数字 / 禁止出现的越界表述）与失效点。
2. **新增 `scripts/run_case_set.py`**：逐案真跑 + 机检验收区间 + 两道交付门，
   渲染出可复核的表与 JSON；退出码给出总体结论。
3. **新增 `references/CASE-SET.md`**：题集定义、逐案实测、**泛化失效边界**、加案例流程。
4. **`deckgen.py` 的图文同页修复**（题集 G1 发现）：页级 bullets 曾被写进
   `Picture with Caption` 的图片占位符并被插图覆盖 ⇒ 该页文字静默消失。
   现在跳过图片占位符，图文同页时正文走左半幅。
5. **决策表新增 D19（图文同页）**，并在自查清单加了一条"能在 deck XML 里搜到该页数字"。

## 5. 适用范围与限制

- **适用**：单篇论文/研究报告 → 8–20 页学术汇报；材料可为 PDF/文本/LaTeX。
- **不适用**：判断论文结论真假、重画科研图、润色正文、与材料无关的通用幻灯片。
- **已有实测的题材**：计算机（示例）、实验物理（μ 子成像）、临床流行病学（队列）。
- **未验证、不得声称支持**（详见 `references/CASE-SET.md` §4）：扫描件/图像型 PDF、
  >20 页大汇报、非中英文材料、真正的组织方模板、多篇材料合并。
- 预览是 **PIL 近似**，不等于 PowerPoint/LibreOffice 渲染；无 Office 引擎时三处标注。
- 模板适配是"占位符级"：SmartArt 不重排；模板自带形状**不改名**。
- 包内**只携带文本资源**（`.md/.py/.json/.txt/.csv/.yaml/.yml`）；模板、预览、重建图
  一律运行时生成。

## 6. 维护

- 版本：`scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；
- 改任一页级版式行为 ⇒ **重跑 `run_case_set.py` 并重渲染 `CASE-SET.md` §2**（旧数字作废）；
- 改 D 规则 ⇒ 同步 `references/failure-modes.md` 同号条目与 `RUBRIC_MAP.md` 复核命令；
- 新增案例 ⇒ 四个文件即可，脚本自动发现；
- 新增脚本 ⇒ 在 `SKILL.md` §3 与 `TEST.md` 各补一行。
