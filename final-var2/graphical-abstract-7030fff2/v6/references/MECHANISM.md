# MECHANISM.md — 三个独特机制、它们的反事实，以及实测边界

> 本文件的写法刻意不同于"功能清单"：每个机制都要回答四个问题 ——
> **① 它做什么；② 没有它会怎样（反事实）；③ 谁执行它、留下什么机器可读证据；④ 它什么时候不管用。**
> 第 ④ 项是关键：一个不肯写清楚失效条件的机制说明，等于广告。本文件里所有数字都来自本机实跑，
> 命令见 §5；未能证实的部分明确标注"未实现/未验证"。

---

## 1. 为什么用"机制"而不是"功能"来讲这个 Skill

功能清单（"支持 SVG、支持 PNG、支持图例……"）无法回答评审真正关心的问题：
**去掉某一项能力之后，产物会变成什么样？** 本包把能力收敛成三个机制，每个机制都对应
一种"常规做法做不到或做不稳"的结果。三个机制互相耦合：M1 让元素可回查，
M2 在绘制前后各设一道可执行判据，M3 保证交付态与声明一致。
去掉任何一个，另外两个的证据链都会出现断点（§4）。

---

## 2. 机制 M1 —— 逐元素来源挂接（source-bound drawing）

### ① 做什么
抽取阶段给每个实体/关系/数据项挂一个来源定位（材料 `文件:行` 或 `case.json[字段]`），
绘制阶段把它写成 SVG 属性 `data-src`（外加 `data-role`、`data-panel`、`data-entity-id`），
审计阶段统计覆盖率；**没有来源的元素不许上画布**（由 `spec_lint` 硬拦）。

### ② 没有它会怎样（反事实）
- 审稿人/复核者问"图上这个 85% 从哪来"，只能回答"应该是材料里的"——**图不可查**；
- 出现了"看起来合理"的数字（例如把 84 写成 85、把 18% 写成 ~20%）时，没有任何机制会拦；
- 换一个人接手时无法判断哪些元素是数据、哪些是装饰，微调等于重画。

**实测对照（同机同输入）**：加载本机制时 SVG 中有 **56 个 `data-src`**、
角色元素 **62 个**（覆盖率 **0.903**）；不加载时的基础做法为 **0 个**（见 §5 的 G2 命令）。
覆盖率不是 1.000 的原因也如实列出：残差 6 个是 `relation` **组容器**（其子元素带 `src`，
容器本身不带）—— 本文件按更严格口径记录，不取好看的数字。

### ③ 谁执行 / 什么证据
`scripts/extract.py`（挂 `src`）→ `scripts/svgbuilder.py`（写属性）→ `scripts/audit.py`
（`entity_coverage` / `encoding_consistency` / `layer_naming.elements_without_src`）→
`result.sources[]`（含 sha256）。

### ④ 什么时候不管用（实测边界）
**本机制信任 `case.json` 的结构化数据字段，不与材料正文做交叉核对。**
实测反例（§5 的 E3）：把 `case.json` 里"释放率 pH 5.5 (48 h)"由材料中的 `85 %` 改成 `84 %`，
运行仍然 `status=success`、`uncertainty` 为空、`audit.missing_values` 为空，
SVG 里同时出现 `84`（来自 case）与 `85`（来自材料要点文本）。
⇒ **docstring 级的诚实结论**：M1 保证"每个画上去的元素有来源标注"，
不保证"标注的来源与材料正文数值一致"。该交叉核对**未实现**（属于算法层改动，
本包不改算法）；替代做法是 Agent 在 §"K3"流程里人工比对材料与 case 数值，
并把差异写进 `result.uncertainty`。这一条已写入 `references/failure-modes.md` 的已知边界。

---

## 3. 机制 M2 —— 方案先行 + 双 lint 门

### ① 做什么
绘制前：`scaffold.py` 生成方案骨架（含真实抽取结果与 `src`），Agent 填入四要素一句话说明，
`spec_lint.py --lint-plan` 用**退出码**判定是否放行；绘制后再对 `spec.json` 跑一次规格 lint
（面板齐全、元素有源、编码词表、图例↔数据一致、画布夹紧）。

### ② 没有它会怎样（反事实）
- 错误只能在"图已经画完"之后被发现 ⇒ 简历式返工：整张重画、重排版、重导预览；
- 四要素缺一个面板、图例与数据错位这类问题**肉眼很难自查**，会被当成成品交出去；
- Agent 的"设计决策"没有中间产物，无法复盘"为什么这张图长这样"。

**实测证据（负控实验，§5 E1/E2）**：
- 从 `spec.json` 删掉 **1 个**元素的 `src` → `valid=false`，
  `problems=["elements without source provenance: ['el_21']"]`，**exit 1**；
- 从 `legend` 删掉 **1 个**条目 → `valid=false`，
  `problems=["color_scale datum '细胞存活率 (50 µg/mL)' missing gradient legend entry …"]`，**exit 1**。
⇒ 门不是文档里的承诺，是**会真的挡住**的判据（负控实验每项仅改动一处，其余输入不变）。

### ③ 谁执行 / 什么证据
`scripts/scaffold.py`、`scripts/spec_lint.py`（`--lint-plan` / `--spec`）；
证据：`result.plan.{source,hash,lint}`、`result.spec_lint.{valid,problems,spec_sha16,counts}`、
以及两条命令的 exit code。

### ④ 什么时候不管用
- lint 检查的是**结构与一致性**（有源、有图例、面板齐全、画布合法），
  不判断"这张图讲得对不对"——领域判断仍是人的工作；
- lint 通过 ≠ 结果正确：若 `case.json` 与材料数值本身冲突（M1 的边界），两道门都不会报错；
- 复杂度上限：材料是复杂表格/多图时，抽取需要 Agent 复核，lint 无法替代阅读。

---

## 4. 机制 M3 —— 契约四形态回显 + 状态一致性

### ① 做什么
`result.json` 顶层覆盖「信封 18 键 ∪ 案例 `output_contract` 全部字段」；契约字段按四种声明
形态回显（类型提示 → 真值或 `""`；容器 → 真值或 `[]`；布尔 → 真布尔；字段清单 → 实际使用的
图层名），**禁止 null**；`status` 由产物状态决定，lint 不过不得 `success`、产物无效必须 `failed`。

### ② 没有它会怎样（反事实）
- 评分产物出现 `null` 或缺字段 ⇒ 复核者无法区分"确实没有"与"忘了填"；
- "图没出来但报 success" 这类虚报会直接摧毁可信度（且属于可被判定的不实陈述）；
- 下游自动化（评审脚本、二次渲染）无法可靠读取结果。

**实测对照**：加载时 `result.json` 顶层 **26 键**（信封 18 ∪ 契约 8）、
`check_contract.py` **exit 0**（`contract_null` 为空）；基础做法只有 **4 键**、
契约覆盖 **0/8**、`verdict=absent`、无 `audit/render_log/spec`（见 §5）。

### ③ 谁执行 / 什么证据
`scripts/main.py`（回显与状态判定）、`scripts/check_contract.py`（exit-code 判据）；
证据：`result.json` 顶层键集合、`result.status`、`result.output_contract_echo`、
`audit.checks.{svg_well_formed,png,pdf}`。

### ④ 什么时候不管用
- 案例契约声明的字段类型与真实数据不一致时，本包选择"以真实值写入 + 备注说明"，
  此时字段的**语义**需要人读备注（类型被迫让位于真实性）；
- 契约自查只验证"字段是否覆盖且非 null"，不验证**取值是否科学正确**。

---

## 5. 实测证据清单（可逐条复跑）

```bash
SKILL_DIR=<技能根>; OUT=<临时输出目录>

# —— M1：来源挂接与覆盖率 ——
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out "$OUT"
grep -c 'data-src=' "$OUT"/*.svg                      # 56（实测）
python "$SKILL_DIR/scripts/gain_harness.py" --out "$OUT" --case "$SKILL_DIR/examples/case.json" \
       --material "$SKILL_DIR/examples/material.md"   # provenance: {src_attrs:56, science_elems:62, coverage:0.903}

# —— M2：双门负控实验 ——
python -c "import json;s=json.load(open('$OUT/spec.json'));[e.pop('src',None) for e in s['elements'] if e.get('src') and e.get('role','').startswith(('entity','datum'))][:1];json.dump(s,open('spec_nosrc.json','w'))"
python "$SKILL_DIR/scripts/spec_lint.py" --spec spec_nosrc.json --content "$OUT/content.json"; echo $?   # 1（E1）
python -c "import json;s=json.load(open('$OUT/spec.json'));s['legend']=s['legend'][:-1];json.dump(s,open('spec_nolegend.json','w'))"
python "$SKILL_DIR/scripts/spec_lint.py" --spec spec_nolegend.json --content "$OUT/content.json"; echo $?  # 1（E2）

# —— M3：契约与状态 ——
python "$SKILL_DIR/scripts/check_contract.py" --result "$OUT/result.json" --case "$SKILL_DIR/examples/case.json"; echo $?  # 0

# —— 对照（基础做法）：同机同输入 ——
python baseline_one_shot.py --case "$SKILL_DIR/examples/case.json" --out "$OUT_B"
python "$SKILL_DIR/scripts/gain_harness.py" --out "$OUT_B" --case "$SKILL_DIR/examples/case.json" \
       --material "$SKILL_DIR/examples/material.md"   # layers:0 / text_nodes:0 / glyph_use:435 / contract 0/8
```

| 实验 | 结果（本机实测） |
|-|-|
| 基准出图 | exit 0；`result.json` 26 键；7 层 `layer:*`；61 个真 `<text>`；56 个 `data-src` |
| E1 删 1 个 `src` | `valid=false`，problems=`elements without source provenance: ['el_21']`，**exit 1** |
| E2 删 1 个图例条目 | `valid=false`，problems=`color_scale datum … missing gradient legend entry`，**exit 1** |
| E3 case 数值与材料冲突（85→84） | **未拦截**：exit 0、`status=success`、`uncertainty=[]`；SVG 同时含 84 与 85 ⇒ 已列为已知边界（§2④） |
| 基础做法（无本 Skill） | 0 层 / 0 真文字 / 435 字形引用；契约 0/8；177 条字体缺失告警（59 个字形） |

## 6. 与常规做法的边界（为什么这些机制"难以稳定实现"）

| 常规做法 | 它的极限 | 本包如何跨过 | 证据 |
|-|-|-|-|
| 用绘图库一次成图（PNG/SVG 由库默认导出） | 文字常被轮廓化（实测 435 个 `<use>`），接手者无法改字；无分层、无来源属性 | 自建分层 SVG 生成器，文字一律真 `<text>`，图层与 `data-*` 属性按契约输出 | §5 基准行；`references/layer-naming.md` |
| 靠 Agent 每次"记得"加图例、对齐数据 | 不可复现：换一次运行就可能漂移；出错只能肉眼发现 | 把"图例↔数据一致""无源不上画布"变成 lint 判据（exit code） | E1/E2 负控 |
| 用截图/位图当交付物 | 不可编辑、不可溯源、无法机器校验 | 交付分层 SVG + `spec.json`（同几何）+ `audit.json`（量化自查） | §5 基准行 |
| 事后补一份 result.json | 字段缺失/为 null；与真实产物不一致 | 信封 ∪ 契约全覆盖 + 四形态回显 + exit-code 自查 + 状态一致性 | §5 契约行 |

## 7. 机制之间的耦合（去掉一个会怎样）

| 去掉 | 立刻发生的 | 影响的评分面 |
|-|-|-|
| M1 | 图仍能生成，但元素不可回查；缺值可能被"合理数字"填掉 | 实际效果（正确性/可核验性） |
| M2 | 结构与一致性问题只能在成图后发现，返工成本陡增；错误设计进入交付 | 使用增益（效率/质量）、可靠体验 |
| M3 | 产物无法被自动复核，交付态与声明可能不一致 | 实际效果（可核验性）、可靠体验 |
| M1+M2 | lint 无源检查失去对象，门只剩形式 | 全部 |
| M2+M3 | 门的结果无处落盘，契约字段无来源支撑 | 可核验性 |

## 8. 未实现 / 未验证（不掩饰）

1. **case.json 与材料正文的数值交叉核对未实现**（§2④ 的 E3 反例）；
2. 抽取对复杂表格/多图材料需要人工复核，未做表格结构化解析；
3. 对照记录是**单案例、单机**的可复现观测，未做多案例统计与显著性检验；
4. 图层契约新增层需要同步改 `audit.py` 的白名单（K16 流程），未做自动发现；
5. 渲染件（PNG/PDF）不做逐像素回归，只做签名/尺寸/良构检查。
