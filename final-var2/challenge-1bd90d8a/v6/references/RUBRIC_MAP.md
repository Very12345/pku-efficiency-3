# RUBRIC_MAP.md — 五维评分 → 本包落点对照（逐条可点验）

本文件把本期官方评分维度**逐条映射到本包的具体文件或机制**，并给出可复跑的验证命令。

> **合并说明**：本包为 union 版（50 文件上限），四份专题文档合并为 `references/MECHANISM.md`
> （机制/增益/复用/增改四部分），两份实证文档合并为 `references/EVIDENCE.md`
> （故障矩阵/案例题集两部分）。下表按**部分**引用，内容未删。
官方口径（题面 §2）：实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
生态贡献 10，另加 GitHub 公开作品链接 5（附加）。

> **证据规则**：题面明写「文字自述不能替代实际运行证据」，所以下表每一行的
> 「证据」列都指向**本包内真实存在的文件**或**可复跑的命令**，不写空话。
> 示例实测记录见 `TEST.md`；对照协议见 `references/MECHANISM.md` 第二部分附节。

---

## 1. 实际效果（40 分）

| 评分点 | 分 | 本包机制（落在哪个文件） | 可复跑证据 |
|-|-|-|-|
| 任务完成度 | 15 | 全链路编排 `scripts/main.py`（CP1 盘点 → CP2 `extract.py` → CP3 `spec_lint.py` → CP4 生成 SVG/PNG/PDF → CP5 `mapcheck.py`+`figcheck.py`+`verify_rerun.py` → CP6 契约落地）；八种图型 + `panel` 多面板 + `network` 机制/通路图在 `scripts/chartkit.py`；流程与判定门写在 `SKILL.md` §3（S0–S6，CP1–CP6） | `python $SKILL_DIR/scripts/main.py --case examples/case.json --out <out> --style nature` → exit 0、`status=completed`、两张图齐全（TEST.md T2） |
| 结果正确性 | 15 | 每个数据图元带 `data-column`/`data-row-index`/`data-value`/`data-role` 溯源属性（`scripts/chartkit.py`）；`scripts/mapcheck.py` **重读源文件逐行核对** `column+row_index+value`（容差 1e-9）并做 SVG↔manifest 双向闭合；轴单位/误差语义在 `templates/figure_map.schema.json` + `references/workorder-field-map.md` 显式声明；显著性只转述 p 值（SKILL.md D6）；实体名以原文为准（D4） | `mapcheck` 实测 `121 checked / 0 mismatched / 0 unmatched`；`figcheck` G1–G8 全 OK（TEST.md T4/T5） |
| 结果完整性 | 5 | 六类检查点各自有机器判据并在 `result.json.checkpoints.cp5_figcheck.six_checkpoints` 盖戳：科学实体（`data-cite` 溯源）· 空间关系（network 边 / panel 网格）· 数据编码（柱高/点位/色阶/扇区/误差线长度）· 图例标注（legend-mapping 自动对齐）· 可编辑源文件（分层 SVG + 真实 `<text>` 不转曲）· 导出格式（SVG+PNG+PDF、dpi、字体回退链） | `templates/result.template.json` 的 `checkpoints` 样例；`figcheck_report.json` 六项 `covered=true`（真实运行产物见 `examples/output/figcheck_report.example.json`） |
| 结果可核验性 | 5 | 源文件 sha256 + 行列数（`result.json.sources`）、每个产物的 sha256（`artifacts_sha256`）、人工确认与脚本流水（`change_records`）、同输入字节级稳定（`scripts/verify_rerun.py`）；**并且两个不同题材的案例各自给出可接受区间与实测值** | `verify_rerun.py` → `DETERMINISTIC`；逐案实测表见 `references/EVIDENCE.md` 第二部分 §1.5 / §2.5（TEST.md T3/T4） |

## 2. 使用增益（25 分）

| 评分点 | 分 | 本包机制 | 可复跑证据 |
|-|-|-|-|
| 质量增益 | 15 | 相对「基础 Agent 直接写 matplotlib/手绘」的做法，本包把**六类常见不可见错误变成机器判据**：缺列不猜（`spec_lint.py` E3 + `extract.py` 列画像）、空值计数不补造（D9）、图例-系列一一对应（chartkit legend-mapping）、中文标注字体回退链（`scripts/cjkfont.py`）、量级异常 warn 保留原值（D2）、显著性星号缺配对直接 fail（D6/G7）、标签过长自动旋转与遮挡实测（D13） | `validation.json` 八类检查逐条 level；`figcheck` G7 六项；test 记录 TEST.md T2/T8 |
| 效率增益 | 5 | 一次 CLI 调用产出全链路（规格 → SVG/PNG/PDF → manifest → 双校验 → `result.json`）；列语义自动推断、面板递归、刻度自动、样式走预设（`templates/journal_styles.json`，加新期刊=加预设键，不改代码，D17） | `python $SKILL_DIR/scripts/main.py --case <case> --out <out>` 单命令产出 11 个产物文件（TEST.md T2 产物清单） |
| 增益可验证性 | 5 | **对照协议**（见 `references/MECHANISM.md` 第二部分附节）：基准做法与加载后做法使用**同一输入文件、同一数据版本、同一导出参数**；比较口径为「科学正确性（mapcheck/G7 是否通过）+ 标注完整性（六类检查点）+ 可编辑性（G5 real_text/分层）+ 重绘轮次」；确定性用 `verify_rerun.py` 保证同输入同输出，避免"看起来更好"的主观判断 | `references/MECHANISM.md` 第二部分附节 §2 协议表；`verify_rerun.py` 退出码 0；`checkpoints.*` 结构可直接对比 |

## 3. 创新增益（15 分）

| 评分点 | 分 | 本包机制 | 可复跑证据 |
|-|-|-|-|
| 新增能力 | 5 | ① **图元↔源数据双向映射机器校验**（`mapcheck.py`：SVG `data-*` ↔ `data_manifest.json` ↔ 源表三向闭合，非人工抽查）；② 图例-系列自动对齐；③ 中文标注与字体回退（`cjkfont.py` 回退链 + PNG 缺字 warn + `svgtext.py` 编码清理/防转曲检查）；④ **手写 XML 分层 SVG**（`<g id="layer-*">` 分层 + `<metadata id='provenance'>`，文字永不转曲）；⑤ **声明式管线**：`templates/figure_map.schema.json` → lint → 绘制 → 校验；⑥ 连接规则字典 `templates/entity_glossary.json`（关系类型→颜色/线型） | `scripts/mapcheck.py`、`scripts/svgtext.py`（`check_no_text_to_path`）、`scripts/cjkfont.py`、`templates/*.json`；TEST.md T4/T5 |
| 方法改进 | 5 | **同一图元场景（Scene）双端输出**：SVG（矢量可编辑）与 PNG/PDF（Pillow 渲染）由同一个 Scene 逐元素产生，杜绝"矢量好看、位图不同"；panel 子面板复用同一引擎；网络图按关系类型自动着色线型 | `scripts/chartkit.py` 的 `Scene`/`export_figure`；示例 fig-01/fig-02 双类图型同时通过 G1–G8 |
| 创新证据 | 5 | 边界写明（SKILL.md §8 限制：不做统计推断、机制图布局为启发式、PDF 预览是光栅嵌入）；相对"通用绘图库/现成模板"的差异由示例实测证明：数据可回溯、图例不失配、中文字不乱码、产物可编辑可复跑 | `SKILL.md` §8；`TEST.md`；`examples/EXPECTED-OUTPUT.md`；`examples/output/*.json`（真实运行产物） |

## 4. 可靠体验（10 分）

| 评分点 | 分 | 本包机制 | 可复跑证据 |
|-|-|-|-|
| 调用与易用性 | 3 | 单一入口 `scripts/main.py --case … --out …`；**任意 cwd 可运行**（脚本用 `os.path.dirname(__file__)` 自定位 templates/references，见 `chartkit.skill_root()`）；case.json 多形态兼容（顶层 / 数组 / `cases[]` / `figure` / `figures`）；task.md 自动发现；契约四形态自动回显 | SKILL.md §3 自定位命令；TEST.md T2（cwd 不在技能根目录仍 exit 0） |
| 运行稳定性 | 4 | 单图失败不阻塞其他图（`status=partial`，`failed_figures` 记录原因）；Pillow 缺失时**保 SVG**、PNG/PDF 缺失如实记录；模板缺失时回退内置默认（`chartkit.load_journal_styles()`）；非零退出码语义明确：`main.py` 0=completed / 2=partial / 1=failed，`figcheck.py`/`mapcheck.py` 0=通过 1=问题，`spec_lint.py` 0=valid 2=error | TEST.md T7 异常路径：缺 case.json → exit 1 + 最小诚实信封；空数据表 → exit 2 + partial（其余图仍产出） |
| 异常处理 | 3 | `references/failure-modes.md` 覆盖五类：**材料异常**（缺失/为空/扫描件/含糊/编码）· **数据异常**（缺列/空值/量级/单位/误差语义/筛选空集）· **渲染异常**（刻度重叠/遮挡/缺字/图例错配/星号缺配对/越界/悬空边）· **导出异常**（转曲/无分层/XXE/PNG/PDF 损坏/DPI 色域/确定性破坏）· **状态一致性 + 契约四形态 + 依赖与模板缺失**；SKILL.md §6 给出失败分支表与 result 记录位置 | `references/failure-modes.md` 全表；`SKILL.md` §6；实测见 TEST.md T8 |

### 4.1 本版（多案例泛化与题集版）对「实际效果 / 可靠体验」的加强

| 做法 | 为什么它比"在自带示例上跑通"更强 | 可复跑证据 |
|-|-|-|
| **两个题材不同的合成案例**（生态 panel / 材料 scatter+network） | 换图型、换列名、换数据源类型、换误差语义、换契约形态 —— 用同一套代码跑，看假设是否只在原示例上成立 | `examples/cases/lake-eutrophication/`、`examples/cases/mg-alloy-degradation/`；逐案实测 `TEST.md` T3/T4 |
| 每案给出**可接受区间**（不是"看起来对"） | 把"正确"变成可判定数字：退出码、键数、`mismatched=0`、`sources[].rows`、误差语义、图元计数范围、耗时上限 | `references/EVIDENCE.md` 第二部分 §1.3 / §2.3 |
| 每案给出**难度层**与考察点清单 | 让评审知道这两案**想压什么**（未引用列、SD/SE 混用、材料文本抽取…） | `references/EVIDENCE.md` 第二部分 §1.4 / §2.4 |
| **九种图型探针** | `bar/line/scatter/box/heatmap/pie/network/panel/auto` 逐型最小案例实测 —— 结果查出 3 处"声明支持但不工作" | `TEST.md` T7；缺陷登记 `references/EVIDENCE.md` 第一部分 §5（P6/P7） |
| **案例 B 首轮就失败** | 它不是"跑通就贴图"：首轮 `exit 2`，暴露出"材料文本解析器没接到生成路径"这个真实缺口 | `TEST.md` T6（P5）；修前/修后对照 |
| 无图规格时**不臆造**（P8） | 宁可 `failed`，也不画出案例从未要求的图 | `TEST.md` T6 |
| **如实写明泛化边界** | §4 分成"已经不会失效（附修前/修后）"与"仍然会失效/不适用（附实测或依据）"，并列出**未测项** | `references/EVIDENCE.md` 第二部分 §4 |

**证据边界（同时读）**：两案都是**合成案例**，不是平台正式案例；数值与机制文本自拟。
题集只覆盖 2 个题材 + 9 种图型，不等于覆盖全部科研图场景；未测项已逐条列出。

## 5. 生态贡献（10 分）

| 评分点 | 分 | 本包机制 | 可复跑证据 |
|-|-|-|-|
| 文档完整性 | 3 | `SKILL.md`（用途/输入输出/执行步骤 CP1–CP6/决策规则 D1–D18/自查清单/限制）· `README.md`（依赖/安装/调用/设计/限制/维护）· `TEST.md`（真机实测记录）· `references/MECHANISM.md` 第二部分附节（对照协议与三方对照）· `references/OUTPUT_CONTRACT.md`（字段契约 + G1–G8 + 机器可读字段表）· `RUBRIC_MAP.md`（本文件）· `workorder-field-map.md`（输入→字段→输出映射链）· `audit-rules.md`（审计规则）· `encoding-spec.md`（编码/单位/实体命名规范）· `typesetting-presets.md`（期刊排版预设）· `failure-modes.md`（失败模式）· `templates/result.template.json`（信封模板） | 包内文件清单（**49 个文件**，全部 UTF-8 文本，无二进制）；`scripts/check_contract.py` 用 `OUTPUT_CONTRACT.md` 的机器可读块做自动化契约自查 |
| 资源可复用性 | 4 | **可直接改用的题集**（两案：换数据即用，含可接受区间与复跑命令）；引擎库化（`import chartkit`）；六个校验/生成脚本都有独立 CLI；**四形态故障注入台**（`scripts/fault_inject.py`，把异常处理变成可复跑的 23 条实验）；样式预设与连接规则字典可扩展；六类检查点 + 八类校验沉淀为可复用检查清单 | `python $SKILL_DIR/scripts/figcheck.py --dir <out> --case <case>`、`mapcheck`、`spec_lint` 均可单独跑；`python $SKILL_DIR/scripts/cjkfont.py` 可独立盘点运行环境字体 |
| 分享推广价值 | 3 | 直接适用于「数据表/生物源材料 → 投稿级可编辑图」的一般场景；**题集本身就是可分享的"图型案例 + 校验经验"**（含两个不同学科题材、逐案可接受区间、以及 4 处真实缺陷的修前/修后记录）；「契约先行 + 双校验 + 确定性 + 题集回归」的做法可迁移到其他交付型 Skill | `references/EVIDENCE.md` 第二部分（题集与边界）；`TEST.md` T3/T4/T6/T7（实测）；`examples/cases/**`（可改即用） |

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
| 7 | **题集两案**逐个跑 | 实际效果 / 生态贡献 | 都 `exit 0` / `completed` / G1–G8 全过 / mapcheck `0 mismatched` |
| 8 | `fault_inject.py` 全套注入 | 可靠体验 | `cases=23 mismatch=0`，exit 0 |
| 9 | `GITHUB_URL.txt` 链接 | 附加 5 分 | 未登录可访问，且指向本题作品 |
