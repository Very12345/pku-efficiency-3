# challenge-9034312d · 实验装置与技术路线图 Skill（多案例泛化与题集版）

玻尔产品周赛 · 北大专区 · 学术效率第三期（efficiency-3）· figures 组。
把「装置怎么搭、步骤怎么走、物料从哪来到哪去、技术路线分几个阶段」的科研材料，
变成一张**可编辑、可追溯、可复核**的科研图稿：分层 SVG 源文件 + PNG/PDF 预览
+ 证据链 + 结构化 `result.json`。

- 工作单：`apparatus_and_technical_route`（题面「组织方具体输入修订」）
- Skill 名（YAML frontmatter）：`apparatus-and-route-diagrams`
- 公开作品入口：`GITHUB_URL.txt`（单行）
- 本版主题：**它在几个不同题材上都成立吗？换了题材会从哪里开始坏？**

## 0. 本版与基线的差别

| | 基线 | 本版 |
|-|-|-|
| 主流程 `scripts/main.py` | 9 个脚本 | **逐字节不变**（CLI、默认值、退出码语义一致） |
| 案例 | 2 个示例（route / apparatus） | **4 个案例**：新增环境工程（flow）与分子生物四阶段（route）两个不同题材 |
| 期望值 | 散在文档里 | **`references/case-set.json`**：区间 + 不变量 + 允许告警，跑批自动比对 |
| 跑批 | 手工逐案跑 | **`scripts/case_set_run.py`**：一次跑完并给出 PASS/FAIL 与偏差明细 |
| 泛化边界 | 靠推测 | **`--text-only` 探针量化**：实体保留率 0.20–0.67、关系保留率 0.00–0.36 |

## 1. 目录结构

```
SKILL.md                   Skill 本体（自定位 §0；题集 §1；执行五步；D1–D14；泛化结论 §5）
README.md                  本文件（用途/依赖/调用/限制/维护）
TEST.md                    本机真实验收记录（合规、可跑、4 案跑批、泛化探针、负例）
GITHUB_URL.txt             GitHub 公开链接（单行）
references/
  CASE-SET.md              ★★ 本版核心：题集逐案说明（输入/期望结构/可接受区间/难度/实测/失效边界）
  case-set.json            ★ 题集期望表（机器可读；case_set_run.py 的判据来源）
  OUTPUT_CONTRACT.md       result.json 契约：18 个顶层字段 + G1–G10（字段块逐字保留）
  RUBRIC_MAP.md            评分五维（40/25/15/10/10）逐条落点（本版按"案例集"重排）
  failure-modes.md         失败模式与决策规则、打包门 R1–R6
  figure-blueprint.md      布局蓝图 / vocabulary.md 术语表
scripts/
  main.py                  一键流水线            ← 与基线逐字节相同
  case_set_run.py          ★ 本版新增：题集跑批 + 期望比对 + 泛化损失测量
  gain_evidence.py / model.py / layout.py / render_svg.py / export_preview.py
  svg_verify.py / check.py / fonts.py
assets/                    connection_rules.json + result_example.json
templates/                 palette.json + 组件连接核对清单 + 实体关系核对表
examples/
  cases/mbr-wastewater-flow-01/     ★ 新增案例 C-1（环境工程 · flow）
  cases/dtms-stage-route-01/        ★ 新增案例 C-2（分子生物学 · route）
  case.json / task.md / apparatus_spec.example.json / route_spec*.example.json
  output/                   两个示例案例的文本类运行产物
```

**包形态（平台硬约束）**：只含 `.md/.py/.json/.txt/.csv/.yaml/.yml`；无 `__pycache__`、
无 `.pyc`、无 `.pdf/.png/.svg/.pptx`；无符号链接、无本机绝对路径；
`figure.svg/png/pdf` 由脚本运行时生成。

## 2. 依赖

| 依赖 | 用途 | 缺失时（实测） |
|-|-|-|
| Python 3.10+（标准库） | 解析 / 证据 / 布局 / 写 SVG / 校验 | 必需 |
| Pillow（PIL） | `figure.png` 预览 | ⚠ PNG **与 PDF 一起失败**（reportlab 内部也 import PIL）⇒ 两个导出件都缺 ⇒ 契约门 G4 失败、退出码 3 |
| reportlab | `figure.pdf` 预览 | 只 PDF 缺失 ⇒ `status=partial` + `uncertainty[scope=pdf]`，退出码 0 |
| 本机中文字体 | PNG 中文渲染 | `fonts[].found=false` + `uncertainty[scope=fonts]`；SVG/PDF 不受影响 |

不需要 `cairosvg` / `svgwrite` / `python-pptx`。字体探测候选路径在 `scripts/fonts.py`
（`%WINDIR%` 优先、正斜杠形式）；PDF 用 reportlab 内置 CID 字体 `STSong-Light`。

## 3. 快速开始

```bash
SKILL_DIR=/skills/weekly-skill      # 技能根 = 含 SKILL.md 的目录

# ① 跑一个案例（案例目录形态：自动取 case.json + task.md）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/dtms-stage-route-01" \
  --out /tmp/out

# ② 官方运行时形态（/input/* → /app/output）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
  --out /app/output

# ③ 交付自查
python "$SKILL_DIR/scripts/check.py" /tmp/out/dtms-stage-route-01/result.json

# ④ 题集跑批（本版新增；退出码 0 = 全 PASS）
python "$SKILL_DIR/scripts/case_set_run.py" --out /tmp/run --json /tmp/run/report.json

# ⑤ 泛化探针：把每个案例压扁成"只留 text 字段"再跑，测结构化信息消失后的损失
python "$SKILL_DIR/scripts/case_set_run.py" --text-only --out /tmp/run-flat

# ⑥ 只看题集与期望，不执行
python "$SKILL_DIR/scripts/case_set_run.py" --list
```

产物写入 `<out>/<case_id>/`：`evidence.json`、`layout.json`、`figure.svg`、
`figure.png`、`figure.pdf`、`verify_report.json`、`result.json`（7 个文件）。

**退出码**：`main.py` → 0 全过 / 3 已出图但契约门不过 / 2 输入缺失 / 1 流水线异常；
`check.py` → 0 全过 / 1 有 issue；`case_set_run.py` → 0 全 PASS / 1 有 FAIL / 2 用法错误。

## 4. 题集与实测结果（一次运行的数据，明细见 `references/CASE-SET.md`）

| case_id | 题材 | 图类 | 难度 | 实体/关系 | 退出码 | `status` | `verify.ok` | 告警 |
|-|-|-|-|-|-|-|-|-|
| `mbr-wastewater-flow-01` | 环境工程 · 市政污水 MBR | flow | 中 | 14 / 14 | 0 | success | true | `recycle-review` |
| `dtms-stage-route-01` | 分子生物学 · CRISPRi 筛选 | route | 高 | 18 / 18 | 0 | success | true | `recycle-review` |
| `demo-biotech-route-01` | 分子生物学 · 文库药筛 | route | 低 | 10 / 9 | 0 | success | true | — |
| `apparatus-spec-01` | 实验装置 · 冷冻干燥机 | apparatus | 低 | 6 / 5 | 0 | success | true | — |

`cases=4 · passed=4 · failed=0`；契约门 G1–G10 四次运行全部通过。

**泛化损失（`--text-only` 实测）**：实体保留率 0.20–0.67、关系保留率 **0.00**–0.36；
装置图（C-4）关系全丢并降级 `partial`；两案的回流告警在文本形态下消失 ⇒
**回流/分流/依赖在纯文本输入下会整体丢失，且不一定报错**。这条边界写进了
`SKILL.md §5` 与 `references/CASE-SET.md §6`，是本版最值得先读的一页。

## 5. 关键机制

1. **证据先行（CP1）**：`gain_evidence.py` 逐条给 `locator`+`quote` 与材料 `sha256`，
   落盘 `evidence.json` 并回显进 `result.json.evidence`。
2. **连接规则资产（CP2）**：`assets/connection_rules.json` 把类别词表与连接语义
   （sequence / connect / 流向 / 自环 / 回流 / 装置图物料不作终点）做成可扩展规则，
   `svg_verify.py` 机器审计；error 级强制 `status=partial`。
   ⚠ `--rules` 写错时审计会静默空转，交付前请确认规则集非空。
3. **校验闭环（CP3）**：SVG 合法性 / 图层 / 可编辑文本 / 箭头一一对应 / 编号连续 /
   图例一致 + 确定性探针 `spec_sha16`。
4. **契约门（CP4）**：`check.py` 的 G1–G10 与 `references/OUTPUT_CONTRACT.md` 一一对应。
5. **题集可执行（本版新增）**：案例 + 期望表 + 跑批脚本三者构成**可执行的判据**；
   期望写成区间与不变量，所以"按材料补一条真实连接"不会被误判，
   而"少一条回流/少一个终点"会被 `forbidden_errors` 抓到。

## 6. 限制（如实声明）

- 只负责**绘图表达**与**可编辑交付**：不做数值拟合、不判断实验方案科学性、不做排版适配；
- 材料无结构化实体时走**文本解构**，只串联相邻步骤 —— 实测关系保留率最低为 **0**，
  且不一定会让 `status` 降级；需要 Agent 先补结构化实体再用本包；
- 装置图为**单层装配**（三桶布局）；多级嵌套与局部放大视图**不支持**；
- 实体数 > 24 或阶段数 > 5 **未测**（布局会变拥挤，可用 `--width-mm/--height-mm` 调画布）；
- 图内数值注记不强制渲染（可放进实体 `props`）；
- 题集是**合成案例**（示例，非正式案例），不等同于平台固定案例；
  正式案例、白板与评分由平台提供/执行，本包不宣称任何分数。

## 7. 失败处理

管线异常或输入缺失 → `main.py` 兜底写 `status=failed` 的 `result.json`；单个预览失败 →
保留已有产物并 `status=partial`；`svg_verify` 有 error 级违规 → `status=partial` 且
`check.py` 退出码 3；所有不确定性写进 `result.json.uncertainty`（`scope+issue+action`），
修改历史写进 `change_record`。逐条现象 → 处置 → 位点见 `references/failure-modes.md`。

## 8. 维护（加案例 / 加判据）

1. **加案例**：在 `examples/cases/` 下建一个目录，放 `case.json`（结构化实体+关系，
   每个实体带 `source`）与 `task.md`（材料小节号要与 `source` 对得上）；
2. **登记期望**：在 `references/case-set.json` 里加一条：`case_path`、`figure_type`、
   `difficulty`、`entities/relations` 区间、`allowed_warnings`、`forbidden_errors`、
   `invariants`（给人读的设计意图）；
3. **跑批验收**：`python "$SKILL_DIR/scripts/case_set_run.py" --text-only`，
   退出码 0 且没有 `without_expectation` 的案子才算加完；
4. **让判据变机器门**：把 `invariants` 里最要紧的那条翻译成 `forbidden_errors` 里的
   规则名（例如"物料不得成为流向终点"→ `apparatus-flow-into-material`），
   否则它只是注释（见 SKILL.md 的 D13/D14）；
5. 其它维护入口：图元/配色四处同步（`model.py` 的 `KINDS`/`RELATION_KINDS`、
   `templates/palette.json`、`assets/connection_rules.json`、`references/vocabulary.md`）；
   契约改动同步 `check.py` 与 `OUTPUT_CONTRACT.md`。

## 9. 打包自检（提交前）

```bash
python validate_pkg.py <本包目录>                          # 期望 [PASS]
grep -rnE '(^|[^A-Za-z])[A-Za-z]:[\\/]' <本包目录>         # 期望无输出（https:// 不误报）
find <本包目录> -name '__pycache__' -o -name '*.pyc'       # 期望无输出（跑批只在临时目录里写）
```
