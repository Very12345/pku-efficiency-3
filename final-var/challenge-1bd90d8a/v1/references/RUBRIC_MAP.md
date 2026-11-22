# RUBRIC_MAP.md — 五维评分 → 决策显性化版的落点对照

官方口径（题面 §2）：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
生态贡献 10**，另加 GitHub 公开作品链接 5（附加）。

> **证据规则**：题面明写「文字自述不能替代实际运行证据」。下表每一行的「证据」列
> 都指向**本包内真实存在的文件**或**可复跑的命令**。真机实测记录见 `TEST.md`；
> 本版相对基线的逐条增改见 `REFINEMENT-NOTES.md`。

**本版的强化定位**：沿「**可靠体验 10**」与「**实际效果 40**」两个维度做实质增改，
手段是把执行决策显性化 —— 决策规则表（触发条件 → 动作 → 失败降级 → 落痕字段）
与失败分支表（FM-M/D/R/E/C/X 六族）。**该强化的收益不靠自述，靠两件事成立**：
① 每个岔路的默认选择被写死，避免"顺手补一个/顺手改一下"；
② 每条失败都有固定的落痕字段，使 `result.json` 自证其诚实性。

---

## 1. 实际效果（40 分）

| 评分点 | 分 | 本版机制（落在哪个文件） | 可复跑证据 |
|-|-|-|-|
| 任务完成度 | 15 | 全链路编排 `scripts/main.py`（CP1 盘点 → CP2 `extract.py` → CP3 `spec_lint.py` → CP4 生成 SVG/PNG/PDF → CP5 `mapcheck.py`+`figcheck.py`+`verify_rerun.py` → CP6 契约落地）；八种图型 + `panel` 多面板 + `network` 机制/通路图在 `scripts/chartkit.py`；**执行链路与六个判定门写在 `SKILL.md` §4（S0–S7）** | `python $SKILL_DIR/scripts/main.py --case examples/case.json --out <out> --style nature` → **exit 0**、`status=completed`、11 个产物齐全（`TEST.md` T2） |
| 结果正确性 | 15 | 每个数据图元带 `data-column`/`data-row-index`/`data-value`/`data-role` 溯源属性（`chartkit.py`）；`scripts/mapcheck.py` **重读源文件逐行核对** `column+row_index+value`（容差 1e-9）并做 SVG↔manifest 双向闭合；轴单位与误差语义在 `templates/figure_map.schema.json` + `references/workorder-field-map.md` 显式声明；显著性只转述 p 值（**D6**）；实体名以原文为准（**D4**） | `mapcheck` 实测 `121 checked / 0 mismatched / 0 unmatched`（T3）；`figcheck` G1–G8 全 OK |
| 结果完整性 | 5 | 六类检查点各自有机器判据，并在 `result.json.checkpoints.cp5_figcheck.six_checkpoints` 盖戳：科学实体（`data-cite` 溯源）· 空间关系（network 边 / panel 网格）· 数据编码（柱高/点位/色阶/扇区/误差线长度）· 图例标注（legend-mapping 自动对齐）· 可编辑源文件（分层 SVG + 真实 `<text>` 不转曲）· 导出格式（SVG+PNG+PDF、dpi、字体回退链） | `templates/result.template.json` 的 `checkpoints` 样例；`figcheck_report.json` 六项 `covered=true` |
| 结果可核验性 | 5 | 源文件 sha256 + 行列数（`result.json.sources`）、每个产物的 sha256（`artifacts_sha256`）、人工确认与脚本流水（`change_records`）、**同输入字节级稳定（本版已把 PDF 的时间戳归一化，使 `artifacts_sha256` 真正可复现）** | `python $SKILL_DIR/scripts/verify_rerun.py --case examples/case.json --out <out>` → `SUMMARY: DETERMINISTIC (identical=9 differ=0)`（T3/T4） |

## 2. 使用增益（25 分）

| 评分点 | 分 | 本版机制 | 可复跑证据 |
|-|-|-|-|
| 质量增益 | 15 | 把**六类常见不可见错误变成机器判据**：缺列不猜（**FM-D1** + 列画像）、空值计数不补造（**D9**）、图例-系列一一对应（**D3**，`fail` 阻断 `completed`）、中文标注字体回退链（**D5**）、量级异常只 warn 不"修正"（**D2**/FM-D3）、显著性星号缺配对直接 `fail`（**D6**/FM-R5）、标签过长自动旋转与遮挡实测（**D13**） | `validation.json` 八类检查逐条 `level`；`figcheck` G7 六项；`TEST.md` T2/T7 |
| 效率增益 | 5 | 一次 CLI 调用产出全链路（规格 → SVG/PNG/PDF → manifest → 双校验 → `result.json`）；列语义自动推断、面板递归、刻度自动、样式走预设（加新期刊 = 加预设键，不改代码） | 单命令产出 **11 个产物文件**；示例案例 3 次连跑平均 **1.51 秒**（T5） |
| 增益可验证性 | 5 | 对照口径写在 `SKILL.md` **D12**（同输入文件、同数据版本、同导出参数；本包侧必须字节级稳定）；**比较所需的机器报告本包全部自带**（`mapcheck_report.json` / `figcheck_report.json` / `validation.json`），评审无需人工重算 | D12 的判定命令 = `verify_rerun.py`；口径表见 `SKILL.md` §5 的 D12 行 |

> 说明：本版**不声称任何本地测得的"提升百分比"**——本机没有平台的基础 Agent
> 条件，编造增益数字属题面明令禁止。实测 A/B 记录放在 v2/v3 两个版本里。

## 3. 创新增益（15 分）

| 评分点 | 分 | 本版机制 | 可复跑证据 |
|-|-|-|-|
| 新增能力 | 5 | ① **图元↔源数据双向映射机器校验**（`mapcheck.py`：SVG `data-*` ↔ `data_manifest.json` ↔ 源表三向闭合）；② 图例-系列自动对齐；③ 中文标注与字体回退（`cjkfont.py` 回退链 + PNG 缺字 warn + `svgtext.py` 编码清理与防转曲检查）；④ **手写 XML 分层 SVG**（`<g id="layer-*">` + `<metadata id='provenance'>`，文字永不转曲）；⑤ **声明式管线**（`figure_map.schema.json` → lint → 绘制 → 校验）；⑥ **PDF 确定性归一化**（`stamp_pdf_deterministic`，本版新增，见下） | `scripts/mapcheck.py`、`scripts/svgtext.py`（`check_no_text_to_path`）、`scripts/cjkfont.py`、`templates/*.json`；T4 |
| 方法改进 | 5 | **同一图元场景（`Scene`）双端输出**：SVG（矢量可编辑）与 PNG/PDF（Pillow 渲染）由同一个 `Scene` 逐元素产生，杜绝"矢量好看、位图不同"；panel 子面板复用同一引擎；网络图按关系类型自动着色与线型 | `scripts/chartkit.py` 的 `Scene` / `export_figure`；示例 fig-01（panel）/ fig-02（network）两类图型同时通过 G1–G8 |
| 创新证据 | 5 | 边界写明（`SKILL.md` §10 限制 + `TEST.md` 未解决项 5 条，含**实测发现的 `spec_lint` 不查列存在性缺口**）；相对"通用绘图库 / 现成模板"的差异由示例实测证明：数据可回溯、图例不失配、中文字不乱码、产物可编辑、**可字节级复跑** | `SKILL.md` §10；`TEST.md`；`examples/EXPECTED-OUTPUT.md` |

## 4. 可靠体验（10 分）— 本版主攻维度

| 评分点 | 分 | 本版机制（逐条对应官方考察内容） | 可复跑证据 |
|-|-|-|-|
| 调用与易用性 | 3 | **单一入口** `scripts/main.py --case … --out …`；**任意 cwd 可运行**（脚本用 `os.path.dirname(__file__)` 自定位，`SKILL.md` §2 给出 bash + PowerShell 两种写法）；`case.json` 多形态兼容（顶层 / 数组 / `cases[]` / `figure` / `figures`）；`task.md` 自动发现；契约四形态自动回显；**全部 10 个参数有表可查**（`README.md` §2.1） | `SKILL.md` §2；`README.md` §2；`TEST.md` T2（cwd 不在技能根仍 exit 0） |
| 运行稳定性 | 4 | 单图失败不阻塞其他图（`status=partial` + `failed_figures` 记录原因）；Pillow 缺失时**保 SVG 与全部 JSON**（**FM-E8**）；模板缺失时回退内置默认（**FM-X1**）；**退出码语义成表**（`README.md` §2.2：`main.py` 0/2/1、`figcheck` 0/1、`mapcheck` 0/1、`spec_lint` 0/2/1、`check_contract` 0/1/2、`verify_rerun` 0/1）；**确定性经修复后真正成立**（PDF 时间戳归一化） | `TEST.md` T7 异常路径；T4 确定性表；`README.md` §2.2 |
| 异常处理 | 3 | `references/failure-modes.md` 与 `SKILL.md` §6 **一一对应**，共 **6 族 38 条分支**（FM-M 6 条 / FM-D 7 条 / FM-R 7 条 / FM-E 9 条 / FM-C 5 条 / FM-X 7 条），每条给出症状、触发条件、检出点、处置、落痕字段、复验命令；官方点名的五类情形**逐类有落点**：材料异常（FM-M1..M6）· 模板缺失（FM-X1..X3）· 依赖缺失（FM-E8 / FM-X4..X6）· **契约四形态（FM-C1..C5）** · 状态一致性（§7 三态收敛 + 四条禁止） | `references/failure-modes.md` 全表；`SKILL.md` §6；`TEST.md` T7 |

## 5. 生态贡献（10 分）

| 评分点 | 分 | 本版机制 | 可复跑证据 |
|-|-|-|-|
| 文档完整性 | 3 | `SKILL.md`（用途与边界 / 自定位 / 输入输出 / 执行链路 S0–S7 / **决策规则 D1–D16 + 决策优先级** / **失败分支 FM 六族** / 检查点速查 / 自查清单 / 脚本清单 / 限制）· `README.md`（依赖 / 安装 / 参数表 / 退出码表 / 设计三不变量 / 适用与限制 / **维护表**）· `TEST.md`（8 组真机实测 + 5 条未解决项）· `REFINEMENT-NOTES.md`（本版逐条增改与 diff 定位）· `references/` 七份（含机器可读契约 + 评分映射 + 失败模式全表 + 字段映射 + 审计规则 + 编码规范 + 排版预设）· `templates/result.template.json` | 包内文件清单（全部 UTF-8 文本）；`scripts/check_contract.py` 用 `OUTPUT_CONTRACT.md` 的机器可读块做自动化契约自查 |
| 资源可复用性 | 4 | 引擎库化（`import chartkit` 即可复用渲染）；六个校验/生成脚本各有独立 CLI（`extract`/`spec_lint`/`figcheck`/`mapcheck`/`verify_rerun`/`check_contract`）；样式预设可扩展（加键即可）；规格契约开放（任何人可写 spec 出图）；连接规则字典可扩展；**六类检查点 + 八类校验 + 六族失败分支沉淀为可复用检查清单** | `README.md` §5 维护表；`figcheck.py`/`mapcheck.py`/`spec_lint.py` 均可单独跑；`python $SKILL_DIR/scripts/cjkfont.py` 可独立盘点运行环境字体 |
| 分享推广价值 | 3 | 直接适用于「数据表 / 生物源材料 → 投稿级可编辑图」的一般场景；示例覆盖 panel（bar+line）与 network 两类图，改数据即可复用；**"决策表 + 失败分支表 + 契约先行 + 双校验 + 确定性"这套做法可整段迁移到其他交付型 Skill** —— 本版的真正可分享产物是这套**决策显性化写法**，而不是某张图 | `examples/README.md`；`examples/case.json`（可改即用）；`TEST.md` 的复跑命令；`REFINEMENT-NOTES.md` 的迁移建议 |

## 6. GitHub 公开作品链接（5 分，附加）

- 根路径 `GITHUB_URL.txt` 第一行是**公开仓库中本题作品的目录链接**（无需登录即可打开），
  第二行是本提交目录内的相对入口文件。
- 评审无需登录即可打开链接并找到本次提交的作品 → 得 5 分；缺交或链接无效 → 0 分。

## 7. 提交前自查（命令级）

```bash
SKILL_DIR=/skills/weekly-skill          # 本地复跑时改成包所在绝对路径
OUT=<临时输出目录>

python "$SKILL_DIR/scripts/main.py"          --case "$SKILL_DIR/examples/case.json" --out "$OUT" --style nature
python "$SKILL_DIR/scripts/check_contract.py" --result "$OUT/result.json" --case "$SKILL_DIR/examples/case.json"
python "$SKILL_DIR/scripts/figcheck.py"      --dir "$OUT" --case "$SKILL_DIR/examples/case.json"
python "$SKILL_DIR/scripts/mapcheck.py"      --dir "$OUT" --case "$SKILL_DIR/examples/case.json"
python "$SKILL_DIR/scripts/verify_rerun.py"  --case "$SKILL_DIR/examples/case.json" --out "$OUT"
```

| # | 检查 | 对应维度 | 期望 |
|-|-|-|-|
| 1 | `main.py` 退出码与 `result.json.status` | 实际效果 | `0` + `completed`（材料缺失时 `2` + `partial`，且 `failed_figures`/`uncertainty` 写明原因） |
| 2 | `check_contract.py` | 实际效果 / 可靠体验 | `PASS`，`missing=0 null=0 contract_missing=0` |
| 3 | `figcheck.py` G1–G8 与六类检查点 | 实际效果 / 创新 | 全 `OK`，exit 0 |
| 4 | `mapcheck.py` 值核对 | 实际效果 / 创新 | `mismatched=0 unmatched=0`，exit 0 |
| 5 | `verify_rerun.py` | 使用增益 / 可靠体验 | `DETERMINISTIC`，exit 0 |
| 6 | `result.json` 的 `sources.sha256` / `change_records` / `uncertainty` | 结果可核验性 | 与真实源文件一致；未做/未通过项如实写明 |
| 7 | `references/failure-modes.md` 与 `SKILL.md` §6 的对应关系 | 可靠体验 | 六族编号一致，无"文档有、表里无"的分支 |
| 8 | `GITHUB_URL.txt` 链接 | 附加 5 分 | 未登录可访问，且指向本题作品 |
