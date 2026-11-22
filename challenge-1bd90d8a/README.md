# README.md — scientific-figure-craft（科研数据图表生成与编辑 Skill）

面向「玻尔产品周赛 · 北大专区 · 学术效率 · 第三期」challenge-1bd90d8a
（科研数据图表生成与编辑）的可运行 Skill 包。

它把「科研材料 → 可投稿、可复核、可继续编辑的图」这条链路做成**可判定的流水线**：
读实际文件（不猜内容）→ 抽字段与实体 → 生成**可编辑分层 SVG**（每个图元带溯源属性）
+ PNG/PDF 预览 → 双校验（数据↔图元逐值核对 + G1–G8 硬门 + 确定性再跑）→ 按契约写
`result.json`（字段四形态回显，禁止 null）。

> 入口是 `SKILL.md`：先读它（S0–S6 执行步骤、检查点 CP1–CP6、决策规则 D1–D18、
> 失败分支表），再照下面的命令跑。

## 1. 适用条件与边界

- **适用**：从表格/统计结果/实验记录出图（柱状/折线/散点/箱线/热图/扇区/多面板组合），
  或按生物源材料出机制图/通路图；也适用于任何「数据表或材料 → 可编辑科研图」的请求。
- **边界**：不做统计方法选择与显著性计算（只转述材料给的 p 值，D6）；不做实验设计；
  不替用户下科学结论。
- **正式案例由平台提供**：平台固定 3 个案例并比较「不加载 Skill / 加载本 Skill」，
  本包自带的 `examples/` 只是接口示例，与正式案例无关。

## 2. 环境与依赖

| 项 | 要求 |
|-|-|
| Python | 3.8+（实测 3.13.9） |
| 必需依赖 | **仅 Pillow**（渲染 PNG/PDF 预览）：`python -m pip install Pillow`（实测 12.3.0） |
| 非必需 | matplotlib / cairosvg / svgwrite / numpy **都不需要**；核心渲染是自己写的 XML + Pillow |
| 字体 | 不打包字体文件；运行时按候选目录探测（Linux `/usr/share/fonts`、macOS `/System/Library/Fonts`、Windows 系统字体目录），可用环境变量 `FONT_PATHS` 追加（`;` 或 `:` 分隔）。探测结果写入 `result.json.environment.fonts` |
| 网络 | **无网络依赖**（`environment.no_network = true`），不使用任何在线服务 |
| 素材来源 | 全部资源（模板/词表/样式预设/示例数据）为本包自研，无第三方版权素材 |

**缺依赖的行为**：没有 Pillow 时仍产出 SVG 与 `data_manifest`/`validation`/`result.json`，
PNG/PDF 缺失并在 `uncertainty`/`warnings` 中如实记录（降级不静默）。

## 3. 目录结构（38 个文件，全部 UTF-8 文本）

```
SKILL.md                          主文件：用途 / 输入输出 / S0–S6 / CP1–CP6 / D1–D18 / 自查清单 / 限制
README.md                         本文件
TEST.md                           真机实测记录（编译/冒烟/确定性/契约/异常路径/合规自检）
COMPARE.md                        对照方案（基准做法 vs 加载后）+ 结构三方对照
GITHUB_URL.txt                    公开作品链接（单行）
scripts/main.py                   编排入口：CP1→CP6，产出全部图与 result.json
scripts/chartkit.py               渲染引擎（Scene → SVG/PNG/PDF + 八类校验），可 import 复用
scripts/extract.py                CP2：列画像 + 实体/关系抽取（extract.json）
scripts/spec_lint.py              CP3：figure spec 结构校验（E1–E10）
scripts/figcheck.py               CP5：G1–G8 硬门 + 六类检查点
scripts/mapcheck.py               CP5：数据↔图元双向映射 + 源值逐行核对
scripts/verify_rerun.py           D18：确定性再跑验证 / artifacts sha256
scripts/check_contract.py         CP6：result.json 字段覆盖自查（解析契约文档）
scripts/cjkfont.py                中文字体发现与回退（CJK 渲染）
scripts/svgtext.py                SVG 文本转义/清理 + 防转曲检查
templates/figure_map.schema.json  图规格声明式契约（JSON Schema 风格）
templates/result.template.json    result.json 信封模板
templates/journal_styles.json     期刊样式预设（default/nature/cell/prism/minimal/ppt）
templates/entity_glossary.json    连接规则字典 + 实体词表
references/OUTPUT_CONTRACT.md     结果契约（§0 机器可读必需字段 + G1–G8 + 契约四形态规则）
references/RUBRIC_MAP.md          五维评分（40/25/15/10/10）→ 本包文件与机制逐条对照
references/workorder-field-map.md 输入→字段→输出 映射链
references/audit-rules.md         审计规则（检查项 / 级别 / 处置）
references/encoding-spec.md       CJK、单位、实体命名、SVG 编码规范
references/typesetting-presets.md 期刊排版预设说明（三层覆盖方式）
references/failure-modes.md       失败模式与处置（材料/数据/渲染/导出/契约/依赖/状态）
examples/README.md                示例怎么用（合成输入，非正式案例）
examples/EXPECTED-OUTPUT.md        示例预期产物的文字清单（替代预置的图/预览）
examples/case.json                示例案例（panel: bar+line；network: Wnt 通路）
examples/task.md                  示例任务说明
examples/data.csv                 示例源数据（8 行合成数值）
examples/entities.json            示例实体/关系（7 节点 7 关系，含 cite 与手工坐标）
examples/material.md              示例生物源材料（ENTITY:/REL: 行语法 + 词表扫描样例）
examples/output/*.json            示例案例上**真实运行产生**的 5 个契约 JSON（已净化路径）
```

**资源形态**：本包不含任何二进制文件（无 `.png/.pdf/.svg/.pptx/字体/pyc`）。
图与预览一律在运行时生成——这既是平台对 Skill 资源的硬性要求，也保证包内没有
可被误当"预制答案"的成品图。

## 4. 安装与调用（`$SKILL_DIR` = 本包绝对路径；平台为 `/skills/weekly-skill`）

```bash
# 主流程（CP1→CP6）：一条命令产出全部图与 result.json
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output \
       [--work /app/work] [--task /input/task.md] [--data a.csv;b.csv] \
       [--style nature] [--dpi 300] [--note "人工调整说明"] [--no-pdf] [--lang zh|en]

# 独立复核（可与生成分开跑；全部脚本都有独立 CLI）
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json
python "$SKILL_DIR/scripts/figcheck.py"  --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/mapcheck.py"  --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/verify_rerun.py" --case /input/case.json --out /app/output

# 中间步骤单独用
python "$SKILL_DIR/scripts/extract.py"   --case /input/case.json --out /app/work
python "$SKILL_DIR/scripts/spec_lint.py" --spec /input/case.json --case /input/case.json
python "$SKILL_DIR/scripts/cjkfont.py"                     # 盘点当前环境字体
```

脚本内部用 `os.path.dirname(os.path.abspath(__file__))` 定位 `templates/`、`references/`，
所以**当前工作目录不必是技能根目录**（`SKILL.md` 顶部给出 bash/PowerShell 两种自定位写法）。

最小示例（包内自带，与正式案例无关）：

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <OUT> --style nature
```

退出码语义：`main.py` 0 = completed 且 G1–G8 全过 / 2 = partial / 1 = failed；
`figcheck.py`、`mapcheck.py`、`check_contract.py`、`verify_rerun.py` 0 = 通过 1 = 有问题；
`spec_lint.py` 0 = valid / 2 = 有 error。

## 5. 输入与输出

**输入**：`/input/case.json`（`case_id`、`figures[]`、`output_contract`、`manual_confirmations`；
四种 contract 写法都支持）、`/input/task.md`、源数据表（CSV/TSV/JSON）、
生物源材料（`entities_file` JSON 或 `ENTITY:`/`REL:` 行语法文本；PDF 材料用平台
pdf-text-tool 提取）。

**输出**（`--out`，平台为 `/app/output`，一律 UTF-8）：

| 文件 | 内容 |
|-|-|
| `figure-<id>.svg` | **可编辑分层矢量源**：`<g id="layer-*">` 分层、`<metadata id='provenance'>` 溯源、每个数据图元带 `data-*`，文字是真实 `<text>`（永不转曲） |
| `figure-<id>.png` / `.pdf` | 同一图元场景的预览（Pillow 渲染） |
| `data_manifest.json` | 图元 ↔ 源数据映射（文件/列/行/值；`svg_id` 与 SVG `id` 对齐） |
| `validation.json` | 八类标注校验结果 + `adjustments` + `warnings` |
| `mapcheck_report.json` / `figcheck_report.json` | 双校验报告（值核对明细 / G1–G8 与六类检查点） |
| `result.json` | **唯一评分产物**：契约字段（四形态回显）+ `case_id` + `status`/`sources`/`uncertainty`/`change_records` 等，契约见 `references/OUTPUT_CONTRACT.md` |

## 6. 关键设计

1. **检查点流水线 CP1–CP6**：材料盘点 → 抽取 → spec lint 生成门 → 导出 → 双校验 →
   契约落地。每步都有机器判定（`result.json.checkpoints` 可查），未过不进入下一步。
2. **双校验**：`mapcheck` 做数据↔图元**双向**核对（重读源文件逐行比 `column+row_index+value`，
   容差 1e-9）；`figcheck` 以 G1–G8 收口（契约 → 文件 → SVG 可编辑性 → 预览 → 六项标注 → status 自洽）。
3. **契约先行且可执行**：`references/OUTPUT_CONTRACT.md` 内含机器可读必需字段块，
   `check_contract.py` 直接解析它做覆盖自查（文档与脚本同源，改契约两处一起改）。
4. **样式规则化（D17）**：期刊样式 = `templates/journal_styles.json` 命名预设，
   三层优先级「CLI 基样式 → `spec["style"]` 预设 → spec 内联键」；加新期刊 = 加预设键。
5. **确定性（D18）**：SVG/PNG/manifest/validation 同输入同参数**字节级稳定**（无随机、无时间戳入图）；
   PDF 与 `result.json` 的时间戳差异如实记录，不掩盖。
6. **中文与字体**：SVG 用字体族回退链（跨平台可用），PNG 用运行时探测到的实际字体文件；
   缺字记 warn + `uncertainty`，不影响可编辑源。

## 7. 验证与自测

- 真机实测记录（命令 + 退出码 + 产物 sha256 + 结论）：`TEST.md`。
- 五维评分逐条落点：`references/RUBRIC_MAP.md`；对照协议：`COMPARE.md`。
- 失败处置与降级策略：`references/failure-modes.md`（含模板缺失、依赖缺失、契约四形态、
  状态一致性）；`SKILL.md` §6 是速查失败分支表。
- 提交前自查命令：`references/RUBRIC_MAP.md` §7。

## 8. 限制（如实声明）

- 统计（显著性计算、拟合、检验）不在本 Skill 范围：只转述材料已给的 p 值/统计量。
- 机制/通路图自动布局为启发式（按 group 分层 + 行内分布）；复杂通路建议在 spec 手给节点 `x/y`（D13）。
- PDF 预览 = 光栅预览嵌入 PDF（便于快速查看）；投稿用的矢量可编辑源以 SVG 为准。
- 中文字体依赖运行环境：缺字体时 SVG 走回退链、PNG 记 warn（D5）。
- 词表扫描只做候选提示，不替代 Agent 对源材料的确认（D4）。
- 包内示例全部标注「示例，非正式案例」，正式运行禁止照抄示例内容。

## 9. 维护

- **改契约**：同时改 `references/OUTPUT_CONTRACT.md`（含 §0 字段块）与 `scripts/main.py`
  的 `apply_output_contract`，然后跑 `check_contract.py` 确认一致。
- **加图型/样式**：图型在 `scripts/chartkit.py`（并在 `templates/figure_map.schema.json`
  与 `references/OUTPUT_CONTRACT.md` §6 登记）；样式只加 `templates/journal_styles.json` 键。
- **改版后必跑**：`TEST.md` 里的命令序列（编译 → 示例全链路 → 契约 → 双校验 → 确定性 → 异常路径），
  并把新结果追加进 `TEST.md`，不要只留在会话里。
- **资源形态保持**：新增文件只用 `.md/.py/.json/.txt/.csv/.yaml/.yml`，单文件 ≤500KB，
  总计 ≤2MB，文件数 ≤50，不引入符号链接与本机绝对路径。
