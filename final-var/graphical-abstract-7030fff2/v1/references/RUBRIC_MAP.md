# RUBRIC_MAP.md — 评分五维 → 本包机制 → **复算命令**（文档轴 A）

> 题面评分：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**
> （GitHub 公开链接另计 +5，共 105）。本文件逐评分点给出三样东西：
> ① 本包的落点机制；② 证据字段/文件；③ **第三人可复算的命令**。
> 高于一切的原则：**文字自述不替代实际运行证据** —— 因此每一行都尽量给出命令或字段，
> 不能复算的行会被标注为"叙述性证据"。
>
> 本包（文档轴 A）的强化重心是「可靠体验 10」与「实际效果 40 的可核验性」：
> 把异常处置写成 20 条带降级路径的规则（`SKILL.md` §4/§5 + `references/failure-modes.md`），
> 使"出问题怎么办"不再依赖临场判断。

## 1. 实际效果（40 分）

| 评分点 | 落点机制 | 证据 | 复算命令 |
|-|-|-|-|
| 任务完成度 15 | 单页四面板（问题/方法/结果/结论）+ 阅读顺序 + 面板内实体卡片/关系箭头/数据子图；同时交付可编辑源与渲染件 | 运行产出清单；`spec.reading_order`；`examples/EXPECTED-OUTPUT.md` | `python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-out`（exit 0）→ `ls /tmp/ga-out` |
| 结果正确性 15 | 实体/关系/数据逐项 `src`；数值只来自材料；负向关系（抑制）自动红色；数据编码进 `legend` 且经 lint 一致性检查 | `audit.entity_coverage`、`audit.encoding_consistency`、`result.spec_lint` | `python -c "import json;a=json.load(open('/tmp/ga-out/audit.json'));print(a['entity_coverage'],a['encoding_consistency'])"` |
| 结果完整性 5 | 单位、比例尺、面板标签、来源脚注；四要素覆盖检查（Q-M-R-C 必齐） | `spec.legend/scale_bar`；`audit.four_element_coverage.missing == []` | `python -c "import json;s=json.load(open('/tmp/ga-out/spec.json'));print(len(s['legend']),len(s['data_encoding']))"` |
| 结果可核验性 5 | 元素级 `data-src` + `sources[]`(路径 + sha256) + `change_records` + 图层命名规范可机器校验 | SVG 属性；`result.provenance/sources`；`audit.layer_naming` | `grep -c 'data-src=' /tmp/ga-out/*.svg`；`python -c "import json;r=json.load(open('/tmp/ga-out/result.json'));print(r['sources'])"` |

**可靠体验维度对本项的加成**：D5（缺值占位）/D7（矛盾不平均）两条规则直接保护
"结果正确性"与"可核验性"不被"补数据"这类看似合理的动作破坏。

## 2. 使用增益（25 分）

| 评分点 | 落点机制 | 证据 | 复算命令 |
|-|-|-|-|
| 质量增益 15 | ①数值可追源为硬门；②布局确定性（同输入同 `spec`）；③文字可编辑（真 `<text>` + 图层契约）；④四要素齐全 | `audit` 数值化字段；`spec_lint.spec_sha16` | 同 §1 的两条命令 + `audit.determinism_probe` |
| 效率增益 5 | `scaffold.py` 一步出方案骨架；`spec.json` 微调后再出图；免跨软件搬运（SVG 源可直接续改）；异常处置有规则表，减少"试错式重绘" | `scripts/scaffold.py`；规则表 D1–D20 | `python "$SKILL_DIR/scripts/scaffold.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/plan.json`（exit 0） |
| 增益可验证性 5 | 增益全部落在**可执行判据**上：覆盖率/一致率/越界数/缺值清单/四要素/图层命名 + 两个 exit-code 自查器 | `audit.json`、`spec_lint.py`、`check_contract.py` | `python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/ga-out/result.json --case "$SKILL_DIR/examples/case.json"`（exit 0） |

> 说明（诚实边界）：本包**不与"基础 Agent"做同台实跑对照**，A 轴不声称对照数据；
> 上述增益均以"本包自身的可复算判据"呈现。需要 A/B 对照协议与实测记录的包，
> 见同题的增益可验证化变体（`references/GAIN-PROTOCOL.md` 形态）。

## 3. 创新增益（15 分）

| 评分点 | 落点机制 | 证据 | 复算命令 |
|-|-|-|-|
| 新增能力 5 | 「实体—关系—数据—面板」四元抽取 + 统一图面规格；方案先行（可 lint 的中间产物）；四要素不变式；图层命名契约可执行化 | `scripts/{extract,scaffold,spec_lint}.py`；三份 references 知识文档 | `python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan "$SKILL_DIR/examples/plan.example.json"`（exit 0） |
| 方法改进 5 | **决策规则表 + 失败分支表 + 同号对照矩阵**：把"异常处置"从经验变成可审计的规则（本轴新增）；确定性布局；图例↔数据一致性校验；导出检查固定为流水线环节 | `SKILL.md` §4/§5；`references/failure-modes.md` §2/§3 | 抽查任一条规则：`grep -n 'D1[0-9]' "$SKILL_DIR/SKILL.md" "$SKILL_DIR/references/failure-modes.md"`（两边同号命中） |
| 创新证据 5 | 与常规方案的边界：单页信息图工具通常不保留可编辑源与逐元素溯源，也不声明降级路径；本包用 `data-src` + hash + 图层契约 + lint 门把"结构与来源"变成可检查项 | `references/layer-naming.md`、`references/OUTPUT_CONTRACT.md`、`TEST.md` 的退出码实测 | `references/failure-modes.md` §6 的六条命令（可整段复跑） |

## 4. 可靠体验（10 分）——本轴主强化项

| 评分点 | 落点机制 | 证据 | 复算命令 |
|-|-|-|-|
| 调用与易用性 3 | 单命令入口 + 可选 `--plan`；`$SKILL_DIR` 自定位（cwd 任意）；README 给"五步跑通"与"异常处置索引" | `README.md` §0/§1/§4 | `cd / && python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-cwd`（exit 0） |
| 运行稳定性 4 | 后端/字体回退链；异常不静默；同输入结构一致；双 lint 门在绘制前后拦截 | `render_log.json`；`audit.determinism_probe` | `python -c "import json;print(json.load(open('/tmp/ga-out/render_log.json'))['backend'])"` |
| 异常处理 3 | **五类分支 21 支全覆盖**，每支给出规则号、判据、降级、证据字段；退出码语义 0/1/2 明确；表外情形走"先记后判" | `SKILL.md` §4/§5/§6；`references/failure-modes.md` 全篇 | `references/failure-modes.md` §6（D1 应得 1、未定稿骨架应得 1、定稿方案应得 0、契约自查应得 0） |

**本轴的量化自检**：五类分支在 `SKILL.md` §5 表中出现 **21 行**，每行都带规则号与证据字段；
`references/failure-modes.md` §2 的矩阵覆盖 **20 条规则**（D1–D20），无"有处置无记录位点"的条目。

## 5. 生态贡献（10 分）

| 评分点 | 落点机制 | 证据 | 复算命令 |
|-|-|-|-|
| 文档完整性 3 | SKILL / README / TEST / OUTPUT_CONTRACT / RUBRIC_MAP（本文件）/ failure-modes / plan-schema / ga-four-elements / layer-naming / TEMPLATE / examples 的 README 与 EXPECTED-OUTPUT：用途、依赖、参数、路径、来源、限制、失败处理、自查、维护齐备 | 根目录与 `references/`、`examples/` | `find "$SKILL_DIR" -name '*.md' \| wc -l`；`find "$SKILL_DIR" -type f \| wc -l`（≤50） |
| 资源可复用性 4 | 图层命名规约、面板模板、`spec.json` 中间规格、资产三件套（方案模板/结果示例/材料样例）、可复制的最小示例、两个 exit-code 自查器；脚本零第三方强依赖 | `references/layer-naming.md`、`references/TEMPLATE.md`、`assets/`、`examples/` | `python "$SKILL_DIR/scripts/check_contract.py" --result "$SKILL_DIR/examples/output/result.json" --case "$SKILL_DIR/examples/case.json"`（exit 0） |
| 分享推广价值 3 | 四要素面板映射、视觉通道映射、色盲安全色板、导出检查项、**决策规则/失败分支写法**沉成可复用规则；纯文本包便于 fork/PR | `references/{ga-four-elements,TEMPLATE,failure-modes}.md`；`GITHUB_URL.txt` | `cat "$SKILL_DIR/GITHUB_URL.txt"` |

## 6. GitHub 公开作品链接（+5）

`GITHUB_URL.txt` 第一行为本作品在该仓库中的精确链接（`final-var/graphical-abstract-7030fff2/v1`），
第二行为本作品在提交目录中的相对路径；评审无需登录即可打开定位。

## 7. 本轴相对基线的增改（自查用）

| 文件 | 增改性质 | 落到哪个评分点 |
|-|-|-|
| `SKILL.md` | 重写：新增决策规则 D1–D20（五组、四列含降级）、失败分支五类 21 支行表、三分钟分诊、出口判据列 | 可靠体验 3 / 实际效果 可核验性 |
| `references/failure-modes.md` | 重写：与 D1–D20 同号对照矩阵（检测点/处置/验证命令/证据字段）、五类速查、科学诚实性红线、表外情形流程 | 可靠体验 3 |
| `README.md` | 重写：决策索引、"五步跑通"含 CP1 门、维护规则（新增规则四处同号补齐） | 调用易用性 3 / 生态 文档 |
| `TEST.md` | 重写：批 A 全链实测 + 失败分支抽查（真实退出码）+ 合规验收 | 可靠体验 4 / 增益可验证性 |
| `references/RUBRIC_MAP.md` | 重写：每行增加**复算命令**列；显式声明本轴不做 A/B 对照（诚实边界） | 增益可验证性 |
