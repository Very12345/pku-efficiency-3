# challenge-9034312d · 实验装置与技术路线图 Skill（合规重打包版）

玻尔产品周赛 · 北大专区 · 学术效率第三期（efficiency-3）· figures 组。
把「装置怎么搭、步骤怎么走、物料从哪来到哪去、技术路线分几个阶段」的科研材料，
变成一张**可编辑、可追溯、可复核**的科研图稿：分层 SVG 源文件 + PNG/PDF 预览
+ 证据链 + 结构化 `result.json`。

- 工作单：`apparatus_and_technical_route`（题面「组织方具体输入修订」）
- Skill 名（YAML frontmatter）：`apparatus-and-route-diagrams`
- `skill_version`：`2.0.0`（见 `scripts/main.py` 的 `execution.skill_version`）
- 公开作品入口：`GITHUB_URL.txt` →
  <https://github.com/Very12345/pku-efficiency-3/tree/main/challenge-9034312d>

> 本目录是**上一版 v2 的合规重打包**：算法、CLI 接口、文档实质内容保持不变，
> 只修**资源形态**（二进制/矢量文件改为运行时生成、清掉本机绝对路径、
> 补齐自定位与五维映射文档）。改造依据见 `TEST.md` 的验收记录。

## 1. 目录结构

```
SKILL.md                  Skill 本体（自定位 §0；执行步骤；决策规则 D1–D12；五维速查 §9）
README.md                 本文件（用途/依赖/调用/限制/维护）
TEST.md                   本机真实验收记录（合规、可跑、确定性、负例）
GITHUB_URL.txt            GitHub 公开链接（单行）
references/
  OUTPUT_CONTRACT.md      result.json 契约：18 个顶层字段 + G1–G10 硬性门
  RUBRIC_MAP.md           ★ 评分五维（40/25/15/10/10）逐条落点与对照方案
  failure-modes.md        失败模式 → 根因 → 处置 → 证据（D1–D12 + 打包门 R1–R6）
  figure-blueprint.md     布局蓝图（图元/模板/命名/导出/扩展）
  vocabulary.md           术语表（kind/关系/图类/命名/状态）
scripts/                  9 个自定位脚本（main 编排；证据/模型/布图/渲染/校验/契约/字体）
assets/                   connection_rules.json（连接规则字典）+ result_example.json
templates/                palette.json + 组件连接核对清单(.md) + 实体关系核对表(.csv)
examples/
  README.md               示例说明（示例，非正式案例）
  EXPECTED-OUTPUT.md      ★ 期望产物清单/契约字段/实测数值（替代随包二进制产物）
  case.json / task.md     route 示例输入（含 --merge 编辑用例）
  apparatus_spec.example.json / route_spec.example.json / route_spec.mutation.example.json
  output/                 两个示例案例的**文本类**运行产物（evidence/layout/verify_report/result）
```

**包形态（平台硬约束）**：只含 `.md/.py/.json/.txt/.csv/.yaml/.yml` 文本资源；
无 `__pycache__`、无 `.pyc`、无 `.pdf/.png/.svg/.pptx`；无符号链接；
不含任何本机绝对路径。`figure.svg`/`figure.png`/`figure.pdf` 由脚本运行时生成。

## 2. 依赖

| 依赖 | 用途 | 缺失时 |
|-|-|-|
| Python 3.10+（标准库） | 解析 / 证据 / 布局 / 写 SVG / 校验 | 必需 |
| Pillow（PIL） | `figure.png` 预览 | 仅 PNG 缺失，`status=partial`（D10） |
| reportlab | `figure.pdf` 预览 | 仅 PDF 缺失，`status=partial`（D10） |
| 本机中文字体（msyh / simhei / Noto CJK…） | PNG 中文渲染 | `fonts[].found=false` 如实记录（D9），SVG/PDF 不受影响 |

不需要 `cairosvg` / `svgwrite` / `python-pptx`：SVG 是手写 XML，预览与源文件共用同一
布局模型。字体探测候选路径写在 `scripts/fonts.py`（`%WINDIR%` 优先，正斜杠形式）；
PDF 用 reportlab 内置 CID 字体 `STSong-Light`，不需要外部字体文件。

## 3. 快速开始（cwd 不是技能根也能跑）

```bash
# 技能根 = 含 SKILL.md 的目录（平台安装到 /skills/weekly-skill）
SKILL_DIR=/skills/weekly-skill

# ① 示例案例（route；--case 给目录时自动取目录下 case.json + task.md）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/out

# ② 官方运行时形态（/input/case.json + /input/task.md → /app/output）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
  --material /app/work/material.md --out /app/output

# ③ 编辑既有图稿（同名 id 替换、新 id 追加，动作写入 change_record）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" \
  --merge "$SKILL_DIR/examples/route_spec.mutation.example.json" --out /tmp/out-merge

# ④ 交付自查（G1–G10；退出码 0 = 全过）
python "$SKILL_DIR/scripts/check.py" /tmp/out/demo-biotech-route-01/result.json
```

产物写入 `<out>/<case_id>/`：`evidence.json`、`layout.json`、`figure.svg`、
`figure.png`、`figure.pdf`、`verify_report.json`、`result.json`（7 个文件）。
`main.py` 退出码语义：`0` 成功且契约门全过；`3` 已产出但契约门不过（诚实降级）；
`2` 输入缺失；`1` 流水线异常（仍会落盘 `failed/result.json`）。

## 4. 关键机制（为什么比「让 Agent 直接画」更可靠）

1. **证据先行（CP1）**：`scripts/gain_evidence.py` 从真实材料抽取实体/关系，逐条带
   `locator`（材料定位）与 `quote`（原文引用）及材料 `sha256`，落盘 `evidence.json`
   并回显进 `result.json.evidence`——「每个实体可追溯」从自述变成证据。
2. **连接规则资产（CP2）**：`assets/connection_rules.json` 把类别词表与连接语义
   （sequence / connect / 流向 / 自环 / 回流 / 装置图物料不作终点）做成**可扩展**规则，
   由 `scripts/svg_verify.py` 机器审计；error 级违规强制 `status=partial`（D11）。
3. **校验闭环（CP3）**：`svg_verify.py` 检查 SVG 合法 XML、5 层图层、可编辑 `<text>`、
   箭头与关系一一对应、无断头箭头、编号 1..N 连续、图例 kind 集合 == 图面 kind 集合，
   并给出确定性探针 `spec_sha16`（同输入同布局的机器证据）。
4. **契约门（CP4）**：`scripts/check.py` 执行 G1–G10（含 status 诚实性检查），
   与 `references/OUTPUT_CONTRACT.md` 一一对应。
5. **确定性**：布局是纯函数（无随机、无时间依赖）；同输入下 `figure.svg`、`layout.json`、
   `evidence.json`、`verify_report.json` **逐字节一致**（`TEST.md` T3 有 sha256 记录）。
6. **可编辑性**：SVG 文字是真实 `<text>`（不是路径描边），实体组带
   `data-entity/data-source/data-kind/data-stage/data-step-no`，可在 Inkscape 或文本
   编辑器里直接改；改完把改动补进 `change_record`（`action: manual-edit`）。

## 5. 限制（如实声明）

- 只负责**绘图表达**与**可编辑交付**：不做数值拟合、不判断实验方案科学性、
  不做论文排版与期刊投稿格式适配；
- 材料无结构化实体时走**文本解构**（`extraction=text-heuristic`，朴素串联步骤），
  设备连接需 Agent 复核（D2）；
- 复杂装配图的**局部放大视图**未内置：可在 Inkscape 微调源文件并如实记录 `manual-edit`；
- 装置图深度为**单层装配**（三桶布局：输入物料 → 装置 → 产物/废料）：深层嵌套结构需
  Agent 拆画布或增补 `stage` 列；
- 图内数值注记：材料给出可标注原值时可放入实体 `props`，当前渲染端不强标数值
  （本 Skill 聚焦装置/流程/路线表达）；
- 正式案例、白板与评分由平台提供/执行；`examples/` 仅为接口演示（**示例，非正式案例**），
  不冒充正式结果、不含预制答案。

## 6. 失败处理

管线异常或输入缺失 → `main.py` 兜底写出 `status=failed` 的 `result.json`（含 error 与
traceback 摘要）；单个预览失败 → 保留已有产物并 `status=partial`（D10）；`svg_verify`
存在 error 级规则违规 → `status=partial` 且 `check.py` 退出码 3（D11）；所有不确定性写入
`result.json.uncertainty`（`scope+issue+action`），修改历史写入 `change_record`。
完整表见 `references/failure-modes.md`（含打包资源形态门 R1–R6）。

## 7. 维护

- 图元/配色：`scripts/model.py` 顶部 `KINDS`/`RELATION_KINDS` + `templates/palette.json`
  + `assets/connection_rules.json` + `references/vocabulary.md`（四处同步）；
- 布局规则：`references/figure-blueprint.md` + `scripts/layout.py`；
- 校验规则：`assets/connection_rules.json` + `scripts/svg_verify.py`；
- 契约与自查：`references/OUTPUT_CONTRACT.md` + `scripts/check.py`（G1–G10）；
- 评分覆盖：`references/RUBRIC_MAP.md`（改动后逐维复核落点是否仍成立）；
- 本地实测：`TEST.md`；示例期望产物：`examples/EXPECTED-OUTPUT.md`；
- 打包门：改包后重跑 §8 的两条自检。

## 8. 打包自检（提交前）

```bash
# 形态：扩展名白名单 / 文件数 ≤50 / 单文件 ≤500KB / 合计 ≤2MB / 无符号链接 / 无 pyc
python validate_pkg.py <本包目录>          # 期望 [PASS] ... （0 条 FAIL）

# 残留：包内不应出现任何本机绝对路径。用「前缀非字母」的字符类写法检索
# 「盘符 + 反斜杠/斜杠」形态，这样 URL 里的 https:// 不会被误报，
# 也免得把路径字面量本身写进文档（字体探测候选路径已全部改写为正斜杠形式，
# 且 Windows 根优先取 %WINDIR%）。
grep -rnE '(^|[^A-Za-z])[A-Za-z]:[\\/]' <本包目录>       # 期望无输出
```
