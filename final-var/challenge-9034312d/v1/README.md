# challenge-9034312d · 实验装置与技术路线图 Skill（决策显性化版）

玻尔产品周赛 · 北大专区 · 学术效率第三期（efficiency-3）· figures 组。
输入是「装置怎么搭、步骤怎么走、物料从哪来到哪去、技术路线分几个阶段」的科研材料，
输出是**可编辑、可追溯、可复核**的科研图稿：分层 SVG 源文件 + PNG/PDF 预览 + 证据链
+ 结构化 `result.json`。

- 工作单：`apparatus_and_technical_route`（题面「组织方具体输入修订」）
- Skill 名（YAML frontmatter）：`apparatus-and-route-diagrams`
- `skill_version`：`2.1.0`（见 `scripts/main.py` 的 `execution.skill_version`）
- 公开作品入口：`GITHUB_URL.txt`

## 0. 这一版改了什么（相对合规基线）

| 改动 | 内容 | 为什么值得改 |
|-|-|-|
| 决策规则 12 → **20 条** | 按**失败域**分组（输入 / 结构与连接 / 导出 / 契约 / 状态），每条给全「触发 → 动作 → 失败时的降级 → **证据位点**」 | 缺"证据位点"的规则只是建议；补上之后每条规则都能被第三方在某次运行里复现 |
| 新增**状态聚合优先级** | 6 条有序判定，明写谁压谁 | 同一份结果可能出现多个缺陷，`status` 只有一个取值；不写死就会"看心情" |
| 新增 **27 行失败分支矩阵** | 见 `references/failure-modes.md §2`，按**处置动作**（丢弃/归一化/降级/拦截/记账）分组 | 现象的描述无穷多，动作只有五种；按动作分组才能覆盖没见过的新现象 |
| 新增 **4 条安静缺陷清单** | 本包会放过但不报错的缺陷，逐条给复核办法 | 把"看起来全绿"的地方点名，比假装满分有用 |
| 新增 `references/DECISION-CASES.md` | 20 个决策用例的**期望判决 vs 实测观测值** | 判决行为从此可验收，不靠读代码推断 |
| 新增 `scripts/decision_probe.py` | 一次跑完 20 个用例，输出观测表 | 回归用：改一行算法就能看出哪条判决被改坏 |
| 新增 `scripts/bare_baseline.py` | 不加载 Skill 的可执行下界（对照实验用） | 让"没有 Skill 会怎样"可被测量，而不是靠形容词 |

算法、CLI 参数、产物文件名与 `references/OUTPUT_CONTRACT.md` 的字段块均未改动
（契约只补说明，不改字段名）。

## 1. 目录结构

```
SKILL.md                  决策显性化本体（§4 状态聚合；§6 D1–D20；§7 失败分支速查；§10 已知边界）
README.md                 本文件（改动说明 / 依赖 / 调用 / 限制 / 维护）
TEST.md                   本机真实验收记录（形态、冒烟、确定性、决策用例、负例）
GITHUB_URL.txt            公开链接（单行）
references/
  OUTPUT_CONTRACT.md      result.json 契约：18 个顶层字段 + G1–G10 硬性门（字段块逐字保留）
  RUBRIC_MAP.md           评分五维（40/25/15/10/10）逐条落点
  failure-modes.md        ★ 决策规则索引 + 27 行失败分支矩阵 + 4 条安静缺陷 + 打包门 R1–R6
  DECISION-CASES.md       ★ 20 个决策用例（期望判决 vs 实测观测值）
  figure-blueprint.md     布局蓝图（图元/模板/命名/导出/扩展）
  vocabulary.md           术语表（kind/关系/图类/命名/状态）
scripts/                  11 个自定位脚本（含 decision_probe.py 与 bare_baseline.py）
assets/                   connection_rules.json（连接规则字典）+ result_example.json
templates/                palette.json + 组件连接核对清单(.md) + 实体关系核对表(.csv)
examples/                 最小调用示例 + 两个合成案例的文本类运行产物
```

**包形态（平台硬约束）**：只含 Markdown / Python / JSON / 纯文本 / CSV / YAML 六类文本扩展名；无 `__pycache__`、
无 `.pyc`、无 `.pdf/.png/.svg/.pptx`；无符号链接；无本机绝对路径。
`figure.svg`/`figure.png`/`figure.pdf` 由脚本运行时生成。

## 2. 依赖

| 依赖 | 用途 | 缺失时 |
|-|-|-|
| Python 3.10+（标准库） | 解析 / 证据 / 布局 / 写 SVG / 校验 | 必需 |
| Pillow（PIL） | `figure.png` 预览 | 无 PNG，`status=partial`（D12） |
| reportlab | `figure.pdf` 预览 | 无 PDF，`status=partial`（D12） |
| 本机中文字体 | PNG 中文渲染 | `fonts[].found=false` 如实记录（D14），SVG/PDF 不受影响 |

不需要 `cairosvg`/`svgwrite`/`python-pptx`：SVG 是手写 XML，预览与源文件共用同一布局模型。
PDF 用 reportlab 内置 CID 字体 `STSong-Light`，不需要外部字体文件。
字体探测候选路径在 `scripts/fonts.py`（`%WINDIR%` 优先、正斜杠形式）。

## 3. 快速开始（cwd 不是技能根也能跑）

```bash
SKILL_DIR=/skills/weekly-skill      # 技能根 = 含 SKILL.md 的目录

# ① 示例案例（--case 给目录时自动取目录下 case.json + task.md）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/out

# ② 官方运行时形态
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
  --material /app/work/material.md --out /app/output

# ③ 编辑既有图稿（同名 id 替换、新 id 追加，动作写入 change_record）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" \
  --merge "$SKILL_DIR/examples/route_spec.mutation.example.json" --out /tmp/out-merge

# ④ 契约自查（G1–G10；退出码 0 = 全过）
python "$SKILL_DIR/scripts/check.py" /tmp/out/demo-biotech-route-01/result.json

# ⑤ 决策行为自测：20 个用例一次跑完，输出"期望 vs 实测"观测表
python "$SKILL_DIR/scripts/decision_probe.py" --out /tmp/decisions --json /tmp/decisions/obs.json
```

产物写入 `<out>/<case_id>/`：`evidence.json`、`layout.json`、`figure.svg`、`figure.png`、
`figure.pdf`、`verify_report.json`、`result.json`（7 个文件）。
`main.py` 退出码语义：**0** 成功且契约门全过；**3** 已产出但契约门不过（诚实降级）；
**2** 输入缺失；**1** 流水线异常（仍会落盘 `failed/result.json`）。

## 4. 一次运行里会发生什么（含三处判决点）

1. **证据先行（CP1）**：`gain_evidence.py` 为每条实体/关系抽 `locator` + `quote`，
   并为每个输入文件记 `sha256`/`size`/`role`。→ **判决点 1**：没有出处的条目按 D11
   记账，不编造。
2. **SIR 与一致性自查**：`model.build_model` 做 id 唯一化、丢弃断头关系、统计孤儿实体。
   → **判决点 2**：孤儿实体按 D6 降级；断头关系按 D5 丢弃并留痕。
3. **确定性布图 + 分层 SVG**：`layout.py` 是纯函数（无随机、无时间依赖）。
4. **机器校验与规则审计（CP2/CP3）**：`svg_verify.py` 检查图层/文本/箭头/编号/图例
   与连接语义。→ **判决点 3**：error 级违规按 D18 降级并让退出码变 3；warn 级按 D10
   只记账（**warn 永不降级**）。
5. **导出与契约（CP4）**：PNG/PDF，然后 `result.json` 回显 18 个顶层字段；
   `check.py` 跑 G1–G10。

## 5. 限制（如实声明）

- 只负责绘图表达与可编辑交付；不做数值拟合、不判断实验方案科学性、不做投稿格式适配；
- 材料无结构化实体时走文本解构（`extraction=text-heuristic`），设备连接需 Agent 复核（D3）；
- **4 条安静缺陷**（全部关系断头后顺序兜底 / 非法类别静默归一化 / 规则资产缺失时审计空转 /
  缺 source 不单独降级）见 `references/failure-modes.md §3` —— 它们不报错，靠人读位点发现；
- 局部放大视图未内置；装置图深度为单层装配（三桶布局）；
- 图内数值注记不强制渲染（材料给出原值时可放实体 `props`）；
- `examples/` 是**合成**示例（标注「示例，非正式案例」），不含预制答案、不冒充正式结果；
  正式案例、白板与评分由平台提供/执行，本包不宣称任何具体分数。

## 6. 失败处理

| 情况 | 行为 |
|-|-|
| 输入缺失 | 打印 `FATAL:`，退出码 2，不写产物（D1） |
| 输入不可解析 / 未预期异常 | 写 `<out>/failed/result.json`（含 error），退出码 1（D2/D19） |
| 单个预览失败 | 保留已有产物 + SVG 源文件，`status=partial`，原因进 `uncertainty`（D12） |
| error 级规则违规 | `status=partial` 且 `check.py` 退出码 3（D18） |
| 有孤儿实体 | `status=partial`（D6） |
| 缺出处 / 材料歧义 / 人工改图 | 只记账不改状态（D11/D16/D20） |

完整规则见 `SKILL.md §6`；完整分支见 `references/failure-modes.md §2`；
逐用例实测见 `references/DECISION-CASES.md`。

## 7. 维护

- **图元/配色**：`scripts/model.py` 顶部 `KINDS`/`RELATION_KINDS` + `templates/palette.json`
  + `assets/connection_rules.json` + `references/vocabulary.md`（**四处同步**）；
- **布局规则**：`references/figure-blueprint.md` + `scripts/layout.py`；
- **校验规则**：`assets/connection_rules.json` + `scripts/svg_verify.py`；
- **契约与自查**：`references/OUTPUT_CONTRACT.md` + `scripts/check.py`（G1–G10）；
- **判决行为**：改完任何算法后跑 `scripts/decision_probe.py`，
  `summary.deviations` 必须为空；若确实要改判决，先改 `references/DECISION-CASES.md`
  的期望列，再改代码（**先改规范再改实现**）；
- **评分覆盖**：`references/RUBRIC_MAP.md`；
- **本地实测**：`TEST.md`；示例期望产物：`examples/EXPECTED-OUTPUT.md`。

## 8. 打包自检（提交前）

```bash
# 形态：扩展名白名单 / 文件数 ≤50 / 单文件 ≤500KB / 合计 ≤2MB / 无符号链接 / 无 pyc
python validate_pkg.py <本包目录>            # 期望 [PASS]

# 残留：不应出现「盘符 + 反斜杠/斜杠」形态（URL 里的 https:// 不会被该式命中）
grep -rnE '(^|[^A-Za-z])[A-Za-z]:[\\/]' <本包目录>   # 期望无输出

# 跑过脚本后确认没有生成 __pycache__（本包脚本已置 dont_write_bytecode，仍建议复查）
find <本包目录> -name '__pycache__' -o -name '*.pyc'   # 期望无输出
```
