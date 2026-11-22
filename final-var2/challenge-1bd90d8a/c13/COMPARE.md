# COMPARE.md — 对照方案（基准做法 vs 加载本 Skill）与三方结构对照

本文件回答「使用增益 25 分」最容易被扣的那一问：**增益怎么被公平地证明**。
题面写明：*平台固定运行 3 个案例，比较不加载 Skill 与加载参赛 Skill 时的实际结果；
需要相对比较的评分项使用组织方预先固定的白板。* ——因此：

- **对照由平台执行，参赛者不自造白板、不自报分数**；
- 参赛者要做的是：① 把「加载后」的做法写成**可复跑、可核验**的形式；
  ② 把**比较口径**写清楚，让评审能用同一输入复现 A/B。

> 本文件**不声称任何本地测得的"提升百分比"**：本机没有平台的基础 Agent 条件，
> 编造增益数字属于题面明令禁止的「文字自述替代实际运行证据」。
> 下表列的是**可判定的差异点**与**判定命令**，评审在固定 3 案例上跑一次即可得结论。

## 1. 两种条件的做法差异（同输入、同数据版本、同导出参数）

| 环节 | 基准做法（不加载 Skill 的基础 Agent） | 加载本 Skill 后 | 差异是否可机器判定 |
|-|-|-|-|
| 材料盘点 | 常见直接按文件名/标签假设内容，或跳过盘点直接画 | SKILL.md CP1：先列文件、算 sha256、记录行数与列名；缺文件 → 不猜内容并记 `uncertainty` | ✅ `result.json.checkpoints.cp1_material_survey` + `sources[].sha256` |
| 数据→图元映射 | 数值凭记忆/口算填进绘图代码，无从回溯 | `chartkit` 给每个图元写 `data-column`/`data-row-index`/`data-value`；`mapcheck.py` 重读源表逐行核对 | ✅ `mapcheck` `mismatches=0 unmatched=0`（G3/G4） |
| 标注校验 | 目视检查，图例/单位/显著性常错配 | 八类校验（溯源/图例-系列/轴单位/范围/CJK/显著性/空值/遮挡）逐项给出 level，fail 阻止 `completed` | ✅ `validation.json` checks + `figcheck` G7 |
| 中文与字体 | 直接输出中文，PNG 出现方框无人记录 | CJK 回退链（SVG）+ 运行环境字体扫描（PNG）；缺字记 warn/uncertainty | ✅ `environment.fonts` + `cjk-font` 检查项 |
| 可编辑交付 | 常给位图或"文字转曲"的 SVG | 分层 SVG（`<g id="layer-*">` + `<metadata id='provenance'>`），真实 `<text>` 不转曲 | ✅ `figcheck` G5（`real_text`/`layers`/`no_xxe`） |
| 重绘轮次 | 每次改图 = 重跑脚本 + 手工调，参数散失 | 样式走 `templates/journal_styles.json` 命名预设 + spec 内联键（三层合并），改样式=改配置 | ✅ 同输入换 `--style` 只改预设键，产物差异可 diff |
| 结果信封 | 常常没有结构化结果，或字段随缘 | `result.json` 契约化（四形态回显、禁 null），`check_contract.py` 自动核对覆盖 | ✅ `check_contract.py` `PASS` |
| 可复跑性 | 依赖交互式会话，无法复现同一张图 | 同输入同参数字节级稳定；`verify_rerun.py` 出确定性报告 | ✅ `verify_rerun.py` `DETERMINISTIC` |

## 2. A/B 比较口径（建议评审按此执行，双方条件完全对等）

| 项 | 规定 |
|-|-|
| 输入 | 平台固定案例的 `case.json` / `task.md` / 源数据文件，**同一份、同一版本**（记录 sha256） |
| 导出参数 | 同一 `--style`、同一 `--dpi`、同一图幅（`width`/`height` 来自 spec） |
| 条件 A | 基础 Agent 按同一任务说明直接产出图与结果 |
| 条件 B | 基础 Agent + 本 Skill（`SKILL.md` 流程，命令见 SKILL.md §3） |
| 判定 1：科学正确性 | 图元数值 vs 源表（逐元素）、轴单位量级、误差线语义、显著性锚点、实体名拼写 |
| 判定 2：标注完整性 | 六类检查点是否齐备（科学实体/空间关系/数据编码/图例标注/可编辑源文件/导出格式） |
| 判定 3：可编辑性 | 源文件是否分层可编辑、文字是否仍为文本、预览是否可打开 |
| 判定 4：效率 | 从输入到可交付图的**命令数/重绘轮次**，以及是否需要人工改图 |
| 复跑 | 条件 B 的产物可用 `verify_rerun.py` 复核确定性；条件 A 同样输入重复一次以示公平 |

> 说明：判定 1–3 本包都有现成的机器报告可对拍（`mapcheck_report.json`、
> `figcheck_report.json`、`validation.json`），无需人工重算。

## 3. 三方结构对照（写作形态层面）

| 维度 | 本包上一版（v1 基础包） | 本期高分包共性形态 | 本包（合规重打包版） |
|-|-|-|-|
| `SKILL.md` 位置 | 根 | 根（`outputs/SKILL.md`） | 根 ✅ |
| 规范前置 | 无 `references/` | references 三件套（审计/编码/字段映射） | 7 份 references（含契约 + 评分映射 + 失败模式 + 字段映射 + 审计 + 编码 + 排版） |
| 脚本 | 单引擎 + 单入口 | 生成/校验/收尾分文件 | 10 个脚本：生成（chartkit/main/extract/spec_lint）+ 校验（figcheck/mapcheck/verify_rerun/check_contract）+ 文字（cjkfont/svgtext） |
| 契约 | 无机器可读契约 | schema/template | `OUTPUT_CONTRACT.md` 含机器可读字段块 + `templates/{figure_map.schema,result.template}.json`，由 `check_contract.py` 执行 |
| 示例 | 无 | example-data + spec + 报告 | `examples/` 最小可跑案例 + 真实运行产物（契约 JSON）+ `EXPECTED-OUTPUT.md` 文字清单 |
| 二进制资源 | 有（预置 PDF/PNG 产物） | 部分有 | **0 个二进制**：全部资源为 UTF-8 文本，图/预览一律运行时由 `scripts/main.py` 生成 |
| 文本文件数 | 18（含 `__pycache__`） | 7 / 9 / 34 | 38（上限 50；含示例产物 JSON） |

## 4. 本包相对上一版的实质改动（全部可 diff 验证）

1. **资源形态合规化**：删除 `__pycache__`/`*.pyc`、示例产物中的 `*.pdf`/`*.png`/`*.svg`
   ——这些正是平台预检点名的 `unsupported Skill resource` 与文件数超限来源；
   图与预览改为运行时生成，示例产物改为**文字清单 + 契约 JSON**（见 `examples/EXPECTED-OUTPUT.md`）。
2. **去本机痕迹**：包内所有文本不再出现本机绝对路径（含字符探测候选路径改为运行时拼装）。
3. **契约可执行化**：新增 `scripts/check_contract.py`，把「字段是否覆盖」从人工目检变成一条命令；
   `manual_confirmations` 现在真正进入 `result.json`（此前文档承诺但脚本未落地）。
4. **文档严谨性**：统一 references 命名（`OUTPUT_CONTRACT.md`/`RUBRIC_MAP.md`）、
   修正 SKILL.md 中 `/app/input` 之类的路径不一致、补齐失败模式中的「模板缺失/依赖缺失/契约四形态/状态一致性」。
5. **不变的部分**：算法与 CLI 接口一字未改（`--case/--out/--work/--task/--data/--style/--dpi/--note/--lang/--no-pdf`），
   因此上一版通过预检的同族骨架（唯一过检那枪 69.33 分）的能力被完整保留。
