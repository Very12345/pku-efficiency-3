# RUBRIC_MAP.md — 五维评分 → 本包设计覆盖（逐条落点）

> 本文件是**交付前自评的唯一对照表**。官方题面评分维度
> **实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**（+ GitHub 附加 5）
> 与题面交付要求（可编辑演示文件 / 页级证据映射 / 渲染与版本记录）逐项映射到本包
> **可运行脚本或已落盘文档**。核对纪律：**文字自述不替代实际运行证据** ——
> 表中每行末尾的"复核命令"都必须能当场跑出同一结果。

## 1. 五维逐条映射

| 维度 | 分 | 评分点 | 本包落点（文件 / 机制） | 复核命令 |
|-|-|-|-|-|
| **实际效果** | 40 | 任务完成度 15 | `SKILL.md` §4 执行流程 S0–S6 + §5 决策规则 D1–D11；`scripts/main.py` 端到端编排（CP1 lint → assetkit 抽取 → deckgen 构建 → preview → 导出检查 → result.json）；`references/slide-blueprint.md` §1 给出"论文结构→页面骨架"默认蓝图 | `python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --spec "$SKILL_DIR/examples/deck-spec.json" --out <tmp>/out` |
| | | 结果正确性 15 | 每页 `claim`/`figure`/`table`/`evidence` 强制（`spec_lint` BL-1…BL-4）；数字/单位/方法名不改写（`OUTPUT_CONTRACT.md` §4.1）；图缺失 = 显式占位框（`deckgen._place_figure`，绝不冒充原图）；引用必须带论文定位（BL-3）；`export_check.py` G1–G8 反查 | `python "$SKILL_DIR/scripts/spec_lint.py" --spec "$SKILL_DIR/examples/deck-spec.json"` |
| | | 结果完整性 5 | 必需页自动补齐：封面 + 主线页（`auto_outline`）+ 证据映射页（`auto_evidence_slide`）+ 收尾；六要素覆盖见 §2 速查表 | `python "$SKILL_DIR/scripts/export_check.py" --result <out>/result.json --out-dir <out>` |
| | | 结果可核验性 5 | **逐页证据映射双形态**：`evidence_mapping.md`（人复核）+ `evidence_map.json`（机器读）同源；导出检查器 G7 校验表行数 = 声明 entries；`previews/` 提供可打开预览；`run_meta.checkpoints` 记录三道门状态 | `python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md"` |
| **使用增益** | 25 | 质量增益 15 | 与**不加载 Skill 的基础 Agent**的差异是结构性的（见 §3 对照协议）：基础 Agent 按段落顺序搬内容；本包强制"一页一主张 + 证据或显式 gap"（`spec_lint` BL-1/BL-3，不过 lint 不得静默构建）、短语化（BL-2 + `overflow_guard` max_bullets=6/max_chars_bullet=110）、备注与页面文字分离（`notes_separated=true`，含封面/收尾）、模板占位符约束（`deckgen.build_deck` placeholder-fill-only，master 不动） | `python "$SKILL_DIR/scripts/spec_lint.py" --spec <一个缺 claim 的 spec>` → 非零退出并列出问题 |
| | | 效率增益 5 | 一条命令端到端（`main.py --case --spec --out`）；`--demo` 可先出骨架验证管道；脚本总时长秒级（示例案例 <5s）；人工返工点被前置消灭（lint 先于生成、模板自动回退、对象按名可寻 → `references/layer-naming.md`） | `python "$SKILL_DIR/scripts/main.py" ... ` 打印的 `run_meta.duration_seconds` |
| | | 增益可验证性 5 | TEST.md 记录同输入重复运行（T3 内容确定性）；`export_check.py --case` 做契约回显核验；预览 + 双形态证据映射均落盘；§3 给出与基础 Agent 的**同输入/同模板/同版本**对照协议 | TEST.md T2/T3 命令行 + `examples/EXPECTED-OUTPUT.md` 清单 |
| **创新增益** | 15 | 新增能力 5 | ① **契约先行**：`OUTPUT_CONTRACT.md` §1 顶层字段清单可被 `check_contract.py` 逐条机器核对（四形态回显，禁止 null）② **方案先行**：`deck-spec.json` 页级方案先落盘再生成，`spec_lint` CP1 前置门 ③ **双形态校验**：证据映射 md+json 同源、deck 既用 python-pptx 重开又做 OOXML zip/XML 健全检查（`ooxml_kit.zip_sanity`）④ **OOXML 分层命名**（`layer-naming.md`：对象名 = 可编辑性的机器可查证据）⑤ PDF 三级抽取回退（fitz→pypdf→pdfplumber）⑥ 从论文表格数字重建图（PNG + 可编辑 SVG，`reconstructed_from_table`）⑦ CJK 安全字体注入（主题 major/minor + run 级 latin/ea 双写，`ooxml_kit.set_theme_fonts`）⑧ **运行时资源自生成**（`make_template.py` / `make_synthetic_inputs.py`：模板与合成素材不随包携带，运行时现产，符合"仅文本资源"硬门） | `python "$SKILL_DIR/scripts/ooxml_kit.py" <out>/academic_deck.pptx` |
| | | 方法改进 5 | 主线五段式蓝图（问题→方法→证据→结论→局限，`slide-blueprint.md` §1）替代段落切片；正确性由"引用必须带论文定位"结构性强制，而非事后自述；证据映射页由 spec 自动生成，避免"讲第三页引用不存在的图" | `references/slide-blueprint.md` §1/§3 + `spec_lint` BL 规则输出 |
| | | 创新证据 5 | 本表 + `references/layer-naming.md` + `references/failure-modes.md` + TEST.md 实测记录 + `examples/` 最小案例（合成、明确标注）同包可复核；对照协议 §3 说明与通用 PPT 生成工具的边界 | 见各文件"复核命令"列 |
| **可靠体验** | 10 | 调用与易用性 3 | SKILL.md YAML frontmatter 触发词（中英）+ §2 输入输出表 + §4 三步调用（读案例→写 spec→跑 main.py）；README.md 快速开始；**脚本以 `os.path.dirname(__file__)` 自定位，SKILL.md 命令一律用 `$SKILL_DIR`**，cwd 不是技能根也能跑 | 在任意 cwd（如 `cd /tmp`）执行 SKILL.md §4 的命令 |
| | | 运行稳定性 4 | 三级库回退（PDF / 字体 / 重建图）；模板不可读 → 内置 16:9 学术版式回退并记录；输入缺失 → 诚实 `failed`/`partial`；CP1 lint 偏差按 D4 记录后继续；同输入两次运行对象名与部件内容一致（layer-naming §1 + TEST.md T3） | TEST.md T3（两跑部件 sha256 对比） |
| | | 异常处理 3 | `references/failure-modes.md` 覆盖 **材料异常 / 模板缺失 / 依赖缺失 / 契约四形态 / 状态一致性** 五类，逐类给出"识别→处置→记录位置→退出码"；SKILL.md §5 D 规则表与之一一对应；**脚本退出码语义**统一（0 通过 / 1 门未过 / 2 资源不可用 / 3 输入不可读） | `python "$SKILL_DIR/scripts/main.py" --case /nonexistent.json --out <tmp>/x` → exit 3，result.json 记 `status=failed` |
| **生态贡献** | 10 | 文档完整性 3 | README.md（依赖/安装/适用范围/限制/维护）+ SKILL.md（用途/调用/异常/自查）+ references 五份（`OUTPUT_CONTRACT` / `RUBRIC_MAP` / `failure-modes` / `slide-blueprint` / `layer-naming`）+ TEST.md（实测）+ GITHUB_URL.txt | `find "$SKILL_DIR" -type f` 清单 |
| | | 资源可复用性 4 | 脚本各自有 CLI 可独立运行（`assetkit` / `spec_lint` / `export_check` / `check_contract` / `make_template` / `make_synthetic_inputs`）；`deck-spec` schema = 页级大纲模板可直接复用（slide-blueprint §3）；蓝图映射表（§1）与逐页证据表格式（§2）可平移到其他"文档→演示"题；`ACADEMIC_THEME` 与 `ooxml_kit` 可复用于 PPT 生成/模板适配题；`make_synthetic_inputs.py` 产出的合成 PDF/占位图可当任何 PDF 管道的回归夹具 | `python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --out <tmp>/synth` |
| | | 分享推广价值 3 | 最小案例（`examples/`：case + spec + task + 合成论文 + 预期产物文字清单）+ `GITHUB_URL.txt` 公开链接；案例只演示接口，**不含正式案例答案** | `examples/README.md` + `examples/EXPECTED-OUTPUT.md` |
| **GitHub 附加** | 5 | 公开作品链接 | `GITHUB_URL.txt` 第一行即本作品目录链接；提交前用未登录窗口确认可打开 | 第一行 URL |

## 2. 六类要素覆盖速查（题面交付要求）

| 题面要素 | 本包实现位置 |
|-|-|
| 1 主线提取 | `slide-blueprint.md` §1 蓝图映射表；`deck-spec.slides` 即叙事骨架（问题→方法→证据→结论→局限）；`deckgen.spec_from_case_meta` 仅用于 `--demo` 骨架 |
| 2 页结构与信息分层 | `spec_lint` BL-1/BL-2（claim 必填、bullets ≤6 条且 CJK 加权 ≤110）；`deckgen.MAX_BULLETS/MAX_CHARS_BULLET` 生成期再截断；`layout_hint` 词表 |
| 3 图表引用与证据保留 | 每页 `figure`/`table`/`evidence` 带 `ref` + `page`；缺失 → `evidence_gap: true`；**逐页证据映射 md+json 双形态**；数值取自原文（脚本不造数据） |
| 4 讲解逻辑与备注 | `deckgen._add_notes` 写 `notes_slide`（主张 + 过渡/强调 + 被问证据），含封面与收尾页；`notes_separated=true` |
| 5 模板约束与版面适配 | `deckgen.open_adapted_presentation` / `_match_layout_index` / `_place_figure`：只填占位符、master 不动、布局名匹配→索引回退→内置版式；`template_mode="replace"` 移除起始页并记 `starter_slides_removed` |
| 6 导出渲染与可编辑性 | 可编辑 `.pptx`（全对象按 `layer-naming.md` 命名）+ PIL 近似预览（诚实标注 `preview-approx-*`）+ 重建图 PNG/SVG + `export_check` 的 OOXML/容器/命名/证据表校验 |

## 3. 使用增益的对照协议（同输入 / 同模板 / 同版本）

平台负责生成白板对照（基础 Agent vs 加载 Skill 的 Agent）。本包不做隐藏测试、
不预写答案，但把**可复现的对照流程**写明，供评审或他人复核：

| 步骤 | 基础 Agent（不加载） | 本包（加载 Skill） | 观察指标 |
|-|-|-|-|
| S1 读输入 | 直接按 task.md 标题假设内容 | S0/S1：读 `/input/case.json` + `/input/task.md` + 实际论文文件（PDF 走 `assetkit.extract_pdf`） | `sources[]` 是否有真实工具与页数/字数 |
| S2 规划 | 无显式方案，边写边排 | S2/S3：先写 `deck-spec.json` 并跑 `spec_lint`（BL-1…BL-4） | lint `valid` 与实际偏差记录 |
| S3 生成 | 段落切块贴页 | S4：`main.py` 按 spec 生成，模板占位符级适配 + 溢出保护 + 对象命名 | `overflow_guard` / `template.guard` / 命名审计 |
| S4 可追溯 | 无逐页映射 | S5/S6：`evidence_mapping.md` + `evidence_map.json` + result.json `evidence_mapping` | 表行数 = entries；gap 显式标注 |
| S5 交付自检 | 无 | CP3：`export_check.py`（G1–G8）+ `check_contract.py`（契约字段覆盖） | exit 0/1 与 errors/warnings |

**边界（不夸大）**：本包不保证论文结论本身正确、不做科研绘图美化、不做写作润色；
模板适配是"占位符级"（SmartArt 等不重排）；无 Office 引擎时预览是 PIL 近似而非真实渲染。
效率增益的绝对秒数依赖机器与案例规模，本包只保证流程确定、日志可复核。

## 4. 维护

- 版本：`scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；本表随能力变更同步更新；
- 新增能力必须同时给出：落点文件、复核命令、失败时的记录字段（写入 `failure-modes.md`）；
- 评分维度若由题面更新，先改本表再改实现，避免"文档承诺 > 代码事实"。
