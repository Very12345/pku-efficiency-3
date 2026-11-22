# RUBRIC_MAP.md — 五维评分 → 本包落点对照（逐条可点验）

本文件把本期官方评分维度**逐条映射到本包的具体文件或机制**，并给出可复跑的验证命令。
官方口径（题面 §2）：实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
生态贡献 10，另加 GitHub 公开作品链接 5（附加）。

> **证据规则**：题面明写「文字自述不能替代实际运行证据」，所以下表每一行的
> 「证据」列都指向**本包内真实存在的文件**或**可复跑的命令**，不写空话。
> 示例实测记录见 `TEST.md`；对照协议见 `COMPARE.md`。

---

## 1. 实际效果（40 分）

| 评分点 | 分 | 本包机制（落在哪个文件） | 可复跑证据 |
|-|-|-|-|
| 任务完成度 | 15 | 全链路编排 `scripts/main.py`（CP1 盘点 → CP2 `extract.py` → CP3 `spec_lint.py` → CP4 生成 SVG/PNG/PDF → CP5 `mapcheck.py`+`figcheck.py`+`verify_rerun.py` → CP6 契约落地）；八种图型 + `panel` 多面板 + `network` 机制/通路图在 `scripts/chartkit.py`；流程与判定门写在 `SKILL.md` §3（S0–S6，CP1–CP6） | `python $SKILL_DIR/scripts/main.py --case examples/case.json --out <out> --style nature` → exit 0、`status=completed`、两张图齐全（TEST.md T2） |
| 结果正确性 | 15 | 每个数据图元带 `data-column`/`data-row-index`/`data-value`/`data-role` 溯源属性（`scripts/chartkit.py`）；`scripts/mapcheck.py` **重读源文件逐行核对** `column+row_index+value`（容差 1e-9）并做 SVG↔manifest 双向闭合；轴单位/误差语义在 `templates/figure_map.schema.json` + `references/workorder-field-map.md` 显式声明；显著性只转述 p 值（SKILL.md D6）；实体名以原文为准（D4） | `mapcheck` 实测 `121 checked / 0 mismatched / 0 unmatched`；`figcheck` G1–G8 全 OK（TEST.md T4/T5） |
| 结果完整性 | 5 | 六类检查点各自有机器判据并在 `result.json.checkpoints.cp5_figcheck.six_checkpoints` 盖戳：科学实体（`data-cite` 溯源）· 空间关系（network 边 / panel 网格）· 数据编码（柱高/点位/色阶/扇区/误差线长度）· 图例标注（legend-mapping 自动对齐）· 可编辑源文件（分层 SVG + 真实 `<text>` 不转曲）· 导出格式（SVG+PNG+PDF、dpi、字体回退链） | `templates/result.template.json` 的 `checkpoints` 样例；`figcheck_report.json` 六项 `covered=true`（真实运行产物见 `examples/output/figcheck_report.example.json`） |
| 结果可核验性 | 5 | 源文件 sha256 + 行列数（`result.json.sources`）、每个产物的 sha256（`artifacts_sha256`）、人工确认与脚本流水（`change_records`）、同输入字节级稳定（`scripts/verify_rerun.py`） | `python $SKILL_DIR/scripts/verify_rerun.py --case examples/case.json --out <out>` → `DETERMINISTIC (identical=9 differ=0)`（TEST.md T5） |

## 2. 使用增益（25 分）

| 评分点 | 分 | 本包机制 | 可复跑证据 |
|-|-|-|-|
| 质量增益 | 15 | 相对「基础 Agent 直接写 matplotlib/手绘」的做法，本包把**六类常见不可见错误变成机器判据**：缺列不猜（`spec_lint.py` E3 + `extract.py` 列画像）、空值计数不补造（D9）、图例-系列一一对应（chartkit legend-mapping）、中文标注字体回退链（`scripts/cjkfont.py`）、量级异常 warn 保留原值（D2）、显著性星号缺配对直接 fail（D6/G7）、标签过长自动旋转与遮挡实测（D13） | `validation.json` 八类检查逐条 level；`figcheck` G7 六项；test 记录 TEST.md T2/T8 |
| 效率增益 | 5 | 一次 CLI 调用产出全链路（规格 → SVG/PNG/PDF → manifest → 双校验 → `result.json`）；列语义自动推断、面板递归、刻度自动、样式走预设（`templates/journal_styles.json`，加新期刊=加预设键，不改代码，D17） | `python $SKILL_DIR/scripts/main.py --case <case> --out <out>` 单命令产出 11 个产物文件（TEST.md T2 产物清单） |
| 增益可验证性 | 5 | **对照协议**（见 `COMPARE.md`）：基准做法与加载后做法使用**同一输入文件、同一数据版本、同一导出参数**；比较口径为「科学正确性（mapcheck/G7 是否通过）+ 标注完整性（六类检查点）+ 可编辑性（G5 real_text/分层）+ 重绘轮次」；确定性用 `verify_rerun.py` 保证同输入同输出，避免"看起来更好"的主观判断 | `COMPARE.md` §2 协议表；`verify_rerun.py` 退出码 0；`checkpoints.*` 结构可直接对比 |

## 3. 创新增益（15 分）

| 评分点 | 分 | 本包机制 | 可复跑证据 |
|-|-|-|-|
| 新增能力 | 5 | ① **图元↔源数据双向映射机器校验**（`mapcheck.py`：SVG `data-*` ↔ `data_manifest.json` ↔ 源表三向闭合，非人工抽查）；② 图例-系列自动对齐；③ 中文标注与字体回退（`cjkfont.py` 回退链 + PNG 缺字 warn + `svgtext.py` 编码清理/防转曲检查）；④ **手写 XML 分层 SVG**（`<g id="layer-*">` 分层 + `<metadata id='provenance'>`，文字永不转曲）；⑤ **声明式管线**：`templates/figure_map.schema.json` → lint → 绘制 → 校验；⑥ 连接规则字典 `templates/entity_glossary.json`（关系类型→颜色/线型） | `scripts/mapcheck.py`、`scripts/svgtext.py`（`check_no_text_to_path`）、`scripts/cjkfont.py`、`templates/*.json`；TEST.md T4/T5 |
| 方法改进 | 5 | **同一图元场景（Scene）双端输出**：SVG（矢量可编辑）与 PNG/PDF（Pillow 渲染）由同一个 Scene 逐元素产生，杜绝"矢量好看、位图不同"；panel 子面板复用同一引擎；网络图按关系类型自动着色线型 | `scripts/chartkit.py` 的 `Scene`/`export_figure`；示例 fig-01/fig-02 双类图型同时通过 G1–G8 |
| 创新证据 | 5 | 边界写明（SKILL.md §8 限制：不做统计推断、机制图布局为启发式、PDF 预览是光栅嵌入）；相对"通用绘图库/现成模板"的差异由示例实测证明：数据可回溯、图例不失配、中文字不乱码、产物可编辑可复跑 | `SKILL.md` §8；`TEST.md`；`examples/EXPECTED-OUTPUT.md`；`examples/output/*.json`（真实运行产物） |

## 4. 可靠体验（10 分）

| 评分点 | 分 | 本包机制 | 可复跑证据 |
|-|-|-|-|
| 调用与易用性 | 3 | 单一入口 `scripts/main.py --case … --out …`；**任意 cwd 可运行**（脚本用 `os.path.dirname(__file__)` 自定位 templates/references，见 `chartkit.skill_root()`）；case.json 多形态兼容（顶层 / 数组 / `cases[]` / `figure` / `figures`）；task.md 自动发现；契约四形态自动回显；**部署前有一条自检命令**（`python -c "import PIL"`）与明确的退出码表（README §3） | SKILL.md §3 自定位命令；TEST.md T2（cwd 不在技能根目录仍 exit 0）；注入台 23 次主流程**全部**从包外 cwd 启动 |
| 运行稳定性 | 4 | 单图失败不阻塞其他图（`status=partial`，`failed_figures` 记录原因）；模板缺失时回退内置默认并**留痕**（`chartkit.load_journal_styles()` + D13）；非零退出码语义明确：`main.py` 0=completed / 2=partial / 1=failed，`figcheck.py`/`mapcheck.py` 0=通过 1=问题，`spec_lint.py` 0=valid 2=error | `references/FAULT-MATRIX.md` I3/I4/I6/I7：材料坏 → `partial` + exit 2 且逐条点名原因；`--only I3,I4,I6,I7` 可定点复跑 |
| 异常处理 | 3 | **三件套**：① 声明层 `references/failure-modes.md`（材料/数据/渲染/导出/契约/依赖六族）；② 决策层 `SKILL.md` §7 的 D1–D18（每条给触发→动作→降级）；③ **实证层 `scripts/fault_inject.py` + `references/FAULT-MATRIX.md`** —— 把输入/模板/依赖/契约四形态**逐个故意弄坏并重跑**，逐行记录实测退出码、`status`、`uncertainty` 原文与**是否静默失败**（23 条；含 5 条据此修掉的真实缺陷与 1 条未修缺口） | `python $SKILL_DIR/scripts/fault_inject.py --src $SKILL_DIR --workdir <tmp>` → `cases=23 mismatch=0`，exit 0；逐行证据 `references/FAULT-MATRIX.md` §1–§5；`--only K1,K6,T2` 可定点复跑 |

### 4.1 本版（故障注入与恢复演练版）对「可靠体验」的加强

| 做法 | 为什么它比"写一段异常处理说明"更强 | 可复跑证据 |
|-|-|-|
| 四形态故障注入台（23 条） | 异常处理**从声明变成实验**：每条注入都真删文件/真写坏 JSON/真屏蔽模块，然后重跑主流程看输出 | `scripts/fault_inject.py`（`--only` 可定点复跑） |
| 逐行记录"期望 vs 实测" | 期望由文档给出、实测由运行给出，**两者不一致就报 `mismatch`**（注入台退出码 2） | `FAULT-MATRIX.md` §1–§4 四张表 |
| 专门的「静默失败总账」 | 定义并逐条排查"出错了却报 completed、且一个字都不记"的形态 | `FAULT-MATRIX.md` §6 |
| 自查出的缺陷照样登记 | 23 条注入查出 6 处问题：**5 处修掉**（P1–P4 + I6 信息丢失），**1 处未修**（D2 缺 Pillow 时降级路径失效）并给出复现方法与部署前自检 | `FAULT-MATRIX.md` §5（含 D2 的实测表：exit 1 / `failed` / 6 键 / traceback 落点 `figcheck.py:162`） |
| 装饰层回退必须留痕 | 样式模板缺失/损坏/预设名拼错，过去三种情况**全静默**；现在一律写 `uncertainty` 并点名缺什么、有哪些可用 | `FAULT-MATRIX.md` T1/T2/T5 |
| 契约形态非法不得谎报 | 过去裸字符串契约会报 `output_contract_applied=true`（一个字段都没写）；现在如实置 `false` + 说明 | `FAULT-MATRIX.md` K6 |
| 本版新增规则 D13/D15/D17 | 把上述三条结论写回决策规则表，避免以后改代码时又退化 | `SKILL.md` §7 |

**证据边界（同时读）**：注入只覆盖 23 种故障（并发、磁盘满、超长文本、非 UTF-8 输入**未测**）；
注入台只测"能否如实报告"，**不**测"图画得对不对"（后者由 `mapcheck`/`figcheck` 负责）。
这 23 条的数字全部来自本机真跑，见 `TEST.md` T5。

## 5. 生态贡献（10 分）

| 评分点 | 分 | 本包机制 | 可复跑证据 |
|-|-|-|-|
| 文档完整性 | 3 | `SKILL.md`（用途/输入输出/执行步骤 CP1–CP6/决策规则 D1–D18/自查清单/限制）· `README.md`（依赖/安装/调用/设计/限制/维护）· `TEST.md`（真机实测记录）· `COMPARE.md`（对照协议与三方对照）· `references/OUTPUT_CONTRACT.md`（字段契约 + G1–G8 + 机器可读字段表）· `RUBRIC_MAP.md`（本文件）· `workorder-field-map.md`（输入→字段→输出映射链）· `audit-rules.md`（审计规则）· `encoding-spec.md`（编码/单位/实体命名规范）· `typesetting-presets.md`（期刊排版预设）· `failure-modes.md`（失败模式）· `templates/result.template.json`（信封模板） | 包内文件清单（**40 个文件**，全部 UTF-8 文本，无二进制）；`scripts/check_contract.py` 用 `OUTPUT_CONTRACT.md` 的机器可读块做自动化契约自查 |
| 资源可复用性 | 4 | 引擎库化（`import chartkit` 即可复用渲染）；四个校验/生成脚本都有独立 CLI（`extract`/`spec_lint`/`figcheck`/`mapcheck`/`verify_rerun`/`check_contract`）；样式预设可扩展（`templates/journal_styles.json`）；规格契约开放（`templates/figure_map.schema.json`，任何人可写 spec 出图）；连接规则字典可扩展（`templates/entity_glossary.json`）；六类检查点 + 八类校验沉淀为可复用检查清单 | `python $SKILL_DIR/scripts/figcheck.py --dir <out> --case <case>`、`mapcheck`、`spec_lint` 均可单独跑；`python $SKILL_DIR/scripts/cjkfont.py` 可独立盘点运行环境字体 |
| 分享推广价值 | 3 | 直接适用于「数据表/生物源材料 → 投稿级可编辑图」的一般场景；示例覆盖 panel（bar+line）与 network 两类图，可直接改数据复用；「契约先行（先读 OUTPUT_CONTRACT）+ 双校验 + 确定性」的做法可迁移到其他交付型 Skill；正式案例运行不依赖示例内容 | `examples/README.md`（怎么用示例）；`examples/case.json`（可改即用）；TEST.md 的复跑命令 |

## 6. GitHub 公开作品链接（5 分，附加）

- 根路径 `GITHUB_URL.txt`：第一行是公开仓库中本题作品的目录链接（无登录可打开），
  第二行是本提交目录内的相对入口文件。
- 提交材料中的链接与 `GITHUB_URL.txt` 保持一致；发布后须用未登录窗口打开复核一次。

## 7. 提交前自查（命令级，五维逐条过一遍）

```bash
SKILL_DIR=/skills/weekly-skill          # 本地复跑时改成包所在绝对路径
OUT=<临时输出目录>; TMP=<临时工作目录>

python $SKILL_DIR/scripts/main.py     --case $SKILL_DIR/examples/case.json --out $OUT --style nature
python $SKILL_DIR/scripts/check_contract.py --result $OUT/result.json --case $SKILL_DIR/examples/case.json
python $SKILL_DIR/scripts/figcheck.py --dir $OUT --case $SKILL_DIR/examples/case.json
python $SKILL_DIR/scripts/mapcheck.py --dir $OUT --case $SKILL_DIR/examples/case.json
python $SKILL_DIR/scripts/verify_rerun.py --case $SKILL_DIR/examples/case.json --out $OUT
```

| # | 检查 | 对应维度 | 期望 |
|-|-|-|-|
| 1 | `main.py` 退出码与 `result.json.status` | 实际效果 | `0` + `completed`（材料缺失时 `2` + `partial`，且 `failed_figures`/`uncertainty` 写明原因） |
| 2 | `check_contract.py` | 实际效果 / 可靠体验 | `PASS`，`missing=0 null=0 contract_missing=0` |
| 3 | `figcheck.py` G1–G8 与六类检查点 | 实际效果 / 创新 | 全 `OK`，exit 0 |
| 4 | `mapcheck.py` 值核对 | 实际效果 / 创新 | `mismatches=0 unmatched=0`，exit 0 |
| 5 | `verify_rerun.py` | 使用增益 | `DETERMINISTIC`，exit 0 |
| 6 | `result.json` 的 `sources.sha256` / `change_records` / `uncertainty` | 结果可核验性 | 与真实源文件一致；未做/未通过项如实写明 |
| 7 | `fault_inject.py` 全套注入 | 可靠体验 | `cases=23 mismatch=0`，exit 0；mismatch 必须为 0 或已登记在 `FAULT-MATRIX.md` |
| 8 | `GITHUB_URL.txt` 链接 | 附加 5 分 | 未登录可访问，且指向本题作品 |
