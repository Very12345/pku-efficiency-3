# RUBRIC_MAP.md — 五维评分落点（本版以**可靠体验 10 + 实际效果 40**为主轴）

> 交付前自评的唯一对照表。官方题面评分维度：
> **实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**（+ GitHub 附加 5）。
> 本版的强化选择是：把"判断与降级"写成可判定的规则，因此 **§1 逐条映射实际效果与可靠体验**，
> **§2 把 D01–D16 逐条挂到评分点**，§3 给出其余三维的落点，§4 是题面六类要素速查。
> 核对纪律：**文字自述不替代实际运行证据** —— 表中每条复核命令都必须能当场跑出同一结果。

## 1. 强化轴逐条映射（实际效果 40 + 可靠体验 10）

| 维度 | 分 | 评分点 | 本版落点 | 复核命令 |
|-|-|-|-|-|
| **实际效果** | 40 | 任务完成度 15 | `SKILL.md` §4 阶段 P0–P6（含 C1/C3 检查点）+ §5 决策规则 D01–D16；`scripts/main.py` 一条命令串起 lint → 抽取 → 构建 → 预览 → 导出检查 → result.json；`references/slide-blueprint.md` §1 提供"章节→页面骨架"默认蓝图 | `python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --spec "$SKILL_DIR/examples/deck-spec.json" --out <tmp>/out` → exit 0 |
| | | 结果正确性 15 | 每页 `claim`/`figure`/`table`/`evidence` 强制（`spec_lint` BL-1…BL-4）；数字/单位/方法名逐字不改写（`OUTPUT_CONTRACT.md` §4.1）；图缺失 = 显式占位框（D09，**不得**用示意图冒充原图，不变量 I4）；引用必须带论文定位（BL-3） | `python "$SKILL_DIR/scripts/spec_lint.py" --spec "$SKILL_DIR/examples/deck-spec.json"` → `{"valid": true}` exit 0 |
| | | 结果完整性 5 | 必需页自动补齐（封面 + 主线页 + 证据映射页 + 收尾）；超限按 D08 合并非证据页而**绝不静默丢弃证据页** | `python "$SKILL_DIR/scripts/export_check.py" --result <tmp>/out/result.json --out-dir <tmp>/out` → exit 0 |
| | | 结果可核验性 5 | 逐页证据映射**双形态同源**（`evidence_mapping.md` 人读 + `evidence_map.json` 机读）；C3 校验表行数 = 声明 `entries`（G7）；`previews/` 可打开；`run_meta.checkpoints` 记三关状态 | `python "$SKILL_DIR/scripts/check_contract.py" --result <tmp>/out/result.json --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md"` → 19/19 exit 0 |
| **可靠体验** | 10 | 调用与易用性 3 | SKILL.md frontmatter 中英触发词；§2 输入输出表 + §4 三步调用；README 快速开始；**脚本 `os.path.dirname(__file__)` 自定位，SKILL.md 命令一律 `$SKILL_DIR`**，cwd 不是技能根也能跑 | 在 `cd /tmp` 下执行 §4 命令（TEST.md T-A2/T-A8 两种调用风格） |
| | | 运行稳定性 4 | 六级回退矩阵（`failure-modes.md` §3）：PDF 三级、图片两级、模板三级、字体三级、渲染两级、契约三级；同输入两次运行 **72 个 OPC 部件 sha256 逐部件一致** | TEST.md T-A4（两跑部件 sha256 对比） |
| | | 异常处理 3 | **本版核心**：五类失败分支处置表（材料/模板/依赖/契约/状态）+ D01–D16 四列表 + I1–I6 不变量；统一退出码语义（0 通过 / 1 门未过 / 2 资源不可用 / 3 输入不可读） | `python "$SKILL_DIR/scripts/main.py" --case /nonexistent.json --out <tmp>/x` → **exit 3**，且不创建输出目录（TEST.md T-A6） |

## 2. 决策规则 D01–D16 × 评分点 × 复核方式

| 规则 | 覆盖的评分点 | 复核方式（可当场执行） |
|-|-|-|
| D01 输入不可读 | 异常处理 3 | `main.py --case /nonexistent.json` → exit 3；`--case <损坏 json>` → exit 3 且写出 `status=failed` 的 result.json |
| D02 材料缺失 | 异常处理 3 + 结果正确性 15 | 构造指向不存在材料的 case → `status=failed`、`material_status=unreadable`、语义字段为空（**不写骨架文案冒充主张**） |
| D03 PDF 加密 | 异常处理 3 | `assetkit.py --pdf <加密 PDF>` → exit 2、JSON 内 `status`/`errors` 说明 |
| D04 扫描件（无文本层） | 结果正确性 15 | `text_chars=0` 时 `uncertainty[]` 出现"图像型 PDF"字样，且**不出现 OCR 编造文本** |
| D05 C1 lint 偏差 | 结果可核验性 5 + 异常处理 3 | 用一个缺 claim 的 spec 跑 `spec_lint.py` → exit 1 并逐条列出 `problems`（TEST.md T-A7） |
| D06 无模板 | 运行稳定性 4 | 不生成模板直接跑 `main.py` → exit 0、`deck.template.kind="builtin"`、`uncertainty` 留痕（TEST.md T-A3） |
| D07 模板损坏/占位符不足 | 运行稳定性 4 | `deck.template.error` / `layouts_used` 有记录；master 与页脚未被改写 |
| D08 页数超限 | 结果完整性 5 | 令 spec 页数 > `slide_count` → `page_budget_met=false` 且 `change_records` 记合并了哪些页 |
| D09 图抽不出 | 结果正确性 15 | `figures[].placed=null` + `placeholder=true` + uncertainty 点名页 |
| D10 重建图失败 | 结果完整性 5 | `charts[].chart.reason` 非空，且页面仍保留表引用与原文数字 |
| D11 缺 python-pptx | 异常处理 3 | `deck=null`、`status=partial/failed`、**输出目录里没有假 `.pptx`** |
| D12 字体缺失 | 运行稳定性 4 | `run_meta.preview_font` 记录实际来源；`.pptx` 内 latin+ea 双写存在 |
| D13 渲染引擎缺失 | 调用与易用性 3 | `previews[].kind="pil-approximation"` 与 `rendered_with` 三处一致（TEST.md T-A2 摘要） |
| D14 输入不在 `/input` | 调用与易用性 3 | 用 `CASE_PATH`/cwd 下的 case.json 跑通；`run_meta.case_file` 记录实际路径 |
| D15 契约四形态 | 结果可核验性 5 | 示例 case 声明 6 个字段（含布尔与清单形态）→ 全部回显、无 null（TEST.md T-A2/T-A3） |
| D16 降级双写 | 异常处理 3 + 状态诚实性 | 任一降级后 `uncertainty[]` 与 `change_records[]` 同时有对应条目；否则 `self_check.ok=false` → main.py exit 1 |

## 3. 其余三维落点（本版不主攻，但保持可复核）

| 维度 | 分 | 落点 |
|-|-|-|
| 使用增益 | 25 | 与"不加载 Skill 的基础 Agent"的差异是结构性的：基础 Agent 按段落顺序搬内容且无页级证据；本包强制"一页一主张 + 证据或显式 gap"（BL-1/BL-3）、短语化（BL-2 + `overflow_guard` max_bullets=6/max_chars_bullet=110）、备注分离（`notes_separated=true`）、模板占位符约束。同输入重复运行部件级一致（TEST.md T-A4）。对照流程见 `references/failure-modes.md` §3 与本节表格 |
| 创新增益 | 15 | ① 契约先行且**文档-代码同源核对**（`check_contract.py` 直接读 `.md` 字段表）；② 方案先行 + C1 前置门；③ **决策规则显性化**：D01–D16 四列表 + I1–I6 不变量（本版新增）；④ OOXML 分层命名（对象名 = 可编辑性的机器可查证据）；⑤ 运行时资源自生成以符合"仅文本资源"硬门 |
| 生态贡献 | 10 | 每个脚本都有独立 CLI；`deck-spec` schema 可直接当页级大纲模板；蓝图映射表与证据表格式可平移；`make_synthetic_inputs.py` 产出的合成夹具可作任何 PDF 管道的回归样本；`GITHUB_URL.txt` 提供公开链接 |

## 4. 题面六类要素覆盖速查

| 题面要素 | 本包实现位置 |
|-|-|
| 1 主线提取 | `slide-blueprint.md` §1 蓝图映射表；`deck-spec.slides` 即叙事骨架（问题→方法→证据→结论→局限） |
| 2 页结构与信息分层 | `spec_lint` BL-1/BL-2（claim 必填、bullets ≤6 条且 CJK 加权 ≤110）；生成期 `MAX_BULLETS/MAX_CHARS_BULLET` 再截断 |
| 3 图表引用与证据保留 | 每页 `figure`/`table`/`evidence` 带 `ref` + `page`；缺失走 D09；双形态证据映射；数值取自原文 |
| 4 讲解逻辑与备注 | `deckgen._add_notes` 写 `notes_slide`（主张 + 过渡/强调 + 被问证据），含封面与收尾页；`notes_separated=true` |
| 5 模板约束与版面适配 | `deckgen.open_adapted_presentation`/`_match_layout_index`/`_place_figure`：只填占位符、master 不动、名匹配→索引回退→内置版式；D06–D08 覆盖异常 |
| 6 导出渲染与可编辑性 | 可编辑 `.pptx`（对象按 `layer-naming.md` 命名）+ PIL 近似预览（诚实标注）+ 重建图 PNG/SVG + C3 的容器/命名/证据表校验；D13 覆盖引擎缺失 |

## 5. 维护

- 版本：`scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；本表随能力变更同步更新；
- **一致性铁律**：修改任一 D 规则必须同时改 `references/failure-modes.md` 的同号条目、
  `SKILL.md` §5 的四列表、以及本表 §2 的复核方式；三者不一致即视为文档漂移；
- 新增能力必须给出：落点文件、复核命令、失败时的记录字段；
- 评分维度若由题面更新，先改本表再改实现，避免"文档承诺 > 代码事实"。
