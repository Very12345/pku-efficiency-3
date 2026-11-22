---
name: scientific-figure-craft
description: >
  科研数据图表生成与编辑 Skill（机制与复用显性版）。当输入包含科研数据表格
  （CSV/TSV/JSON）、统计结果、实验记录或生物源材料，或需要生成/编辑示意图、
  机制图、流程图、柱状图、折线图、散点图、箱线图、热图、扇区图、通路图、
  多面板组合图（关键词：figure、chart、plot、diagram、数据图、科研绘图、
  机制图、通路图、graphical abstract、SVG、可编辑图稿、制图、出图）时使用。
  本版把支撑这条链路的四个咬合机制写成可检验的说明（references/MECHANISM.md：
  三向闭合 / 声明式规格+生成门 / 单一场景双端输出 / 契约四形态回显+确定性归一化），
  并给出可复用资产清单与三条复用路径（references/REUSE-KIT.md）。
  执行链路：读契约 → 盘点材料 → 抽取字段与实体 → 规格门 → 生成分层可编辑
  SVG + PNG/PDF 预览 → 三向核对 → 交付门 → 确定性再跑 → 契约落地。
  严格以真实文件为准，不臆造数据、不提交预制答案。
---

# 科研数据图表生成与编辑（scientific-figure-craft）· 机制与复用显性版

面向「玻尔产品周赛 · 北大专区 · 学术效率 · 第三期」 challenge-1bd90d8a。

本版只强化两个维度：**创新增益 15** 与 **生态贡献 10**。做法是把本包赖以成立的
四个机制**写清楚**（含"没有它会怎样"），并把可复用资产与复用步骤**列出来**。

> **本包形态**：全部资源均为 UTF-8 文本（`.md/.py/.json/.txt/.csv`），**零二进制**
> ——没有 `.pptx/.png/.pdf/.svg`、没有字体文件、没有 `__pycache__`。交付的图与预览
> 一律由 `scripts/main.py` 在运行时现场生成，因此包内不存在"预制答案"。
> 所有命令以 `$SKILL_DIR`（本文件所在目录的绝对路径）为前缀，cwd 不影响执行。
> 五维评分的逐条落点见 `references/RUBRIC_MAP.md`。

---

## 1. 机制主张：把"图"当可回溯的证据，而不是当输出

常规做法把图当**输出**：数据进、图出来，中间过程不留痕。
本包把图当**可回溯的证据**：每个图元都带着回到源数据的钥匙，
且这条"钥匙链"由程序闭合、由门禁判定，不靠目视确认。

这条主张落地为**四个互相咬合的机制**（详见 `references/MECHANISM.md`）：

| # | 机制 | 一句话 | 没有它会怎样（最要命的一条） |
|-|-|-|-|
| **M1** | **三向闭合** | SVG 图元的 `data-*` ↔ `data_manifest.json` ↔ **重读源表**的值，三处互为索引且由程序核对 | "这根柱子的数字来自哪一行"永远回答不了；列错位不会被发现 |
| **M2** | **声明式规格 + 生成门** | 先写可校验的图规格，过门（`spec_lint` 无 error）才进渲染 | 错误推迟到渲染阶段才爆；样式无法复用；别人无法接手你的图 |
| **M3** | **单一场景双端输出** | 一个与格式无关的 `Scene` 同时导出分层 SVG 与 PNG/PDF，逐元素同源 | 矢量与位图能画出"看起来不同"的两张图，评审不知道以哪张为准 |
| **M4** | **契约四形态回显 + 确定性归一化** | 契约四形态全兼容、禁 `null`；把渲染器注入的时间戳归一化，让 `sha256` 成为证据 | 下游拿到 `null` 要写特判；`sha256` 每次都变，于是没人拿它当证据 |

### 1.1 为什么必须一起看（咬合图）

```
   M2 声明式规格 ──spec_lint 生成门──►  M3 单一场景 Scene
                                            │
                        ┌───────────────────┴───────────────────┐
                        ▼                                       ▼
              分层 SVG（带 data-*）                    PNG / PDF 预览
                        │                                       │
                        ▼                                       └─ M4② 元数据归一化
              data_manifest.json（M1）                              → sha256 成为证据
                        │  重读源表三向核对
                        ▼
              result.json（M4① 四形态回显 / 禁 null / 覆盖可命令化自查）
```

**拿掉任何一个，其余机制的收益都会被削弱**：M1 没了，M3 的"双端同源"就失去意义
（同源但无法回溯）；M3 没了，M1 的 `data-*` 与位图脱钩；M2 没了，错误推迟到渲染阶段；
M4 没了，前三个机制的成果无法被下游消费、也无法证明"是同一份"。

---

## 2. 适用条件与边界

**适用**：平台固定 3 个案例（数据图表生成 / 样式调整 / 标注校验 / 源数据关联 /
可编辑源文件与导出）；也适用于任何「数据表或生物源材料 → 可编辑科研图」的请求。

**不适用**：统计方法选择与显著性计算（只**转述**材料给的 p 值）；实验方案设计；
替用户下科学结论。

**运行环境**：Python 3.8+ 标准库 + Pillow（渲染 PNG/PDF）。matplotlib / cairosvg /
svgwrite 非必需（`examples/baseline_agent.py` 用 matplotlib，但那是对照工具，不是主链路）。
不访问网络。

---

## 3. 自定位约定

`$SKILL_DIR` = 本 SKILL.md 所在目录的绝对路径（平台安装期为 `/skills/weekly-skill`）。
脚本用 `os.path.dirname(os.path.abspath(__file__))` 自定位 `templates/` 与 `references/`，
**cwd 与技能根不同也能跑**。

```bash
# bash
SKILL_DIR=/skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```
```powershell
# PowerShell
$SKILL_DIR = "<技能包绝对路径>"      # 平台为 /skills/weekly-skill
python "$SKILL_DIR\scripts\main.py" --case \input\case.json --out \app\output
```
自定位自查：`python -c "import sys;sys.path.insert(0,r'<SKILL_DIR>/scripts');import chartkit;print(chartkit.skill_root())"`

---

## 4. 输入与输出

### 4.1 输入

| 来源 | 内容 | 缺失时 |
|-|-|-|
| `/input/case.json` | `case_id`、`figures` 规格、`data` 引用、`output_contract`、`manual_confirmations` | **必需**；不可解析 → `status=failed` + 最小诚实信封（6 键），exit 1 |
| `/input/task.md` | 任务说明 | 自动找同目录；仍无 → 记 `uncertainty` |
| 源数据表 | CSV / TSV / JSON | 一个都没有 → **不得** `completed` |
| 生物源材料 | `entities_file` JSON 或 `material` 文本 | 机制图按 §7 降级 |

`case.json` 形态兼容：顶层 / `{"cases":[...]}` / 数组取首项；图规格可放
`figures` / `figure` / `figure_spec`；数据可放 `data` / `data_files` / `sources`。

### 4.2 输出（`/app/output`，UTF-8）—— 注意每项都标注了它服务于哪个机制

| 文件 | 服务于 | 硬要求 |
|-|-|-|
| `figure-<id>.svg` | M1 · M3 | 分层 `<g id="layer-*">`；`<metadata id='provenance'>`；图元带 `data-*`；**文字永远是真实 `<text>`，不转曲** |
| `figure-<id>.png` / `.pdf` | M3 · M4② | 与 SVG 逐元素同源；PDF 元数据时间戳已归一化 |
| `data_manifest.json` | **M1** | 每个图元登记 `column + row_index + value`（或实体 `id`/`cite`），与 SVG 的 `data-*` 同名对齐 |
| `validation.json` | M1 · M4 | 八类检查逐项 `ok/warn/fail` |
| `mapcheck_report.json` | **M1** | 三向核对报告：`mismatched=0 unmatched=0` |
| `figcheck_report.json` | M1 · M3 · M4 | G1–G8 硬门报告：`all_pass=true` |
| `result.json` | **M4①** | 契约四形态全回显（禁 null）+ `case_id` + 审计字段 |
| `/app/work/` | M2 | `extract.json`、`spec_lint.json` |

---

## 5. 执行链路（每一环标注它依赖哪个机制）

| 环 | 名称 | 关键动作 | 依赖机制 | 退出条件 |
|-|-|-|-|-|
| **E0** | 读契约 | 读 `references/OUTPUT_CONTRACT.md`（字段块 + G1–G8） | M4① | 已知契约形态与 `case_id` |
| **E1** | 材料盘点 | 列文件、算 sha256、记行数与列名 | — | 至少一个数据文件存在 |
| **E2** | 抽取 | 列画像 + 实体/关系抽取（`extract.py`） | M2 | 每列语义无歧义；不确定候选已记录 |
| **E3** | **规格门** | `spec_lint.py`；**exit 2 = 有 error，不得进 E4** | **M2** | `valid=true` |
| **E4** | 生成 | `main.py`：规格 → `Scene` → SVG + PNG/PDF | **M3** | 每图三形态齐全 |
| **E5** | **三向核对** | `mapcheck.py`：SVG ↔ manifest ↔ **重读源表** | **M1** | `mismatched=0 unmatched=0` |
| **E6** | 交付门 | `figcheck.py`：G1–G8 + 六项标注检查 | M1 · M3 · M4 | 无 `fail` |
| **E7** | 确定性 | `verify_rerun.py`：归一化后逐字节比较 | **M4②** | `differ=0` |
| **E8** | 契约落地 | `check_contract.py`：字段覆盖 | **M4①** | `missing=0 null=0` |

```bash
S=/skills/weekly-skill; OUT=/app/output; WORK=/app/work; CASE=/input/case.json
python "$S/scripts/extract.py"       --case "$CASE" --out "$WORK" --json      # E1+E2
python "$S/scripts/spec_lint.py"     --spec "$CASE" --case "$CASE"            # E3（门）
python "$S/scripts/main.py"          --case "$CASE" --out "$OUT" --work "$WORK" --style nature  # E4
python "$S/scripts/mapcheck.py"      --dir "$OUT" --case "$CASE"              # E5（M1）
python "$S/scripts/figcheck.py"      --dir "$OUT" --case "$CASE"              # E6
python "$S/scripts/verify_rerun.py"  --case "$CASE" --out "$OUT"              # E7（M4②）
python "$S/scripts/check_contract.py" --result "$OUT/result.json" --case "$CASE"  # E8（M4①）
```

`main.py` 参数：`--case`（必需）· `--out` · `--work` · `--task` · `--data` · `--style` ·
`--dpi` · `--note` · `--lang` · `--no-pdf`。退出码：`0`=completed / `2`=partial / `1`=failed。

---

## 6. 规则集（按"缺了它会破坏哪个机制"组织）

与常见的"遇事怎么办"列表不同，本表每条规则都标出**它保护哪个机制**——
规则的存在理由是可追溯的。

### 6.1 保护 M1（三向闭合）的规则

| # | 规则 | 保护方式 |
|-|-|-|
| **M1-R1** | 每个图元必须有溯源（文件/列/行，或实体 `id`/`cite`）；无法溯源则**不画**，必要时虚线占位并记 `uncertainty` | 保证 manifest 里没有"无主的图元"，也保证图上没有"无源的图元" |
| **M1-R2** | `data-*` 属性名与 manifest 字段名**同名对齐**（`data-column` ↔ `source.column`） | 保证双向检索不需要翻译表 |
| **M1-R3** | 值与源表比对**容差 1e-9**，**不得放宽**；不符即 mismatch | 保证"重读源表"这一步真的有判别力 |
| **M1-R4** | 源文件 sha256 + 行列数写入 `result.json.sources` | 保证"哪一版数据"可核 |
| **M1-R5** | 科学实体名取源材料原文，不翻译、不"优化"拼写；不确定的保留原文 + `uncertain` | 保证图上文字可回到材料 |

### 6.2 保护 M2（声明式规格 + 生成门）的规则

| # | 规则 | 保护方式 |
|-|-|-|
| **M2-R1** | 图必须由规格（`figures[]` / `figure_spec.json`）驱动，不写一次性绘图代码 | 保证"换图型/换样式"不改代码 |
| **M2-R2** | `spec_lint` 有 error **不得进入生成** | 让门真的成为门 |
| **M2-R3** | 样式三层合并（内置默认 → 预设 → spec 内联）；加期刊 = 加预设键 | 保证样式是配置而非代码 |
| **M2-R4** | 误差线语义（SE/SD/CI）以源元数据为准，源未标则记 `uncertainty`（**不猜**） | 保证规格里的语义字段有真实来源 |

### 6.3 保护 M3（单一场景双端输出）的规则

| # | 规则 | 保护方式 |
|-|-|-|
| **M3-R1** | 渲染必须先构造与格式无关的 `Scene`，再由它导出各端 | 这是"逐元素同源"的前提 |
| **M3-R2** | SVG 必须分层（背景/坐标/数据/标注/图例）、元素 id 稳定、含 `metadata` 溯源块 | 保证可编辑性与可定位性 |
| **M3-R3** | **文字永不允许转曲**（G5 `real_text` 机器检查） | 保证交付件可再编辑 |
| **M3-R4** | 单图失败不阻塞其他图（`status=partial`）；Pillow 缺失时**保 SVG 与全部 JSON** | 保证降级不丢源 |

### 6.4 保护 M4（契约回显 + 确定性归一化）的规则

| # | 规则 | 保护方式 |
|-|-|-|
| **M4-R1** | 契约四形态全部完整回显；缺失字段按**声明容器类型**给 `""`/`[]`/`{}`/`false`/`0`，**绝不 `null`** | 让下游不用写特判 |
| **M4-R2** | 已知别名映射到**真实产物**（`editable_source` → `editable_sources`、`field_mapping` → `"data_manifest.json"` 等），不打空 | 保证回显是"有内容"的回显 |
| **M4-R3** | 契约声明了本 Skill 不产出的字段 → **不做假映射**，给容器类型空值 + 写明原因 | 保证回显不变成编造 |
| **M4-R4** | PDF 落盘后归一化 `/CreationDate`、`/ModDate`、`/ID`，并同步修正 xref 偏移 | 让"同输入 → 同字节 → 同 sha256"成立 |
| **M4-R5** | 确定性判定只归一化**真正无法消除的环境变量**（输出目录路径、运行时间戳）；其余逐字节 | 保证归一化不是掩盖缺陷的手段 |
| **M4-R6** | `status` 与产物事实严格自洽：有 `fail`/缺口 → 不得 `completed`；无图 → `failed` | 保证信封本身不撒谎 |

### 6.5 规则冲突优先级

1. **诚实 > 完整**：M4-R6 压过"把字段填满"；M4-R1 的禁 null 与它不冲突。
2. **可核验 > 好看**：M1-R1 · M1-R3 · M3-R3 优先于图面美观。
3. **保源 > 保预览**：M3-R4 在能力不足时先保 SVG 与全部 JSON。
4. **阻断 > 带病交付**：图例错配、显著性缺配对的 `fail` 阻止 `completed`。

---

## 7. 失败分支（按"它破坏哪个机制"分组）

完整版（含触发条件、检出点、落痕字段、复验命令）见 `references/failure-modes.md`。

| 组 | 破坏的机制 | 典型分支 | 处置要点 |
|-|-|-|-|
| **G-M1** | 三向闭合 | 图元无溯源 · manifest 与 SVG 图元数不等 · 值与源表不符 · 列名不存在 · SVG 有未登记图元 | 不画无源图元；**不得手改 manifest 迁就**；**不得放宽容差**；列不存在 → `failed_figures` |
| **G-M2** | 声明式规格 | 未知图型 · 缺必需字段 · 列引用错 · 误差语义不明 · 显著性无锚点/来源 · 网络边悬空 | 门不过不进生成；误差语义不猜；显著性无来源就不画 |
| **G-M3** | 单场景双端输出 | SVG 扁平 · 文字转曲 · 含外部实体（XXE）· PNG 损坏 · PDF 头损坏 · 画布空间不足 | 用本包管线重生成；**拒绝生成含外部实体的产物**；缺失时先保 SVG |
| **G-M4** | 契约与确定性 | 契约形态写坏 · 声明了不产出的字段 · **PDF 两次运行字节不同** · 报告 `dir` 字段不同 · `status` 与事实不符 | 契约按容器类型给空值；**PDF 元数据归一化**（见下）；`dir` 属环境变量；状态强制降级 |
| **G-X** | 横切（材料/依赖/环境） | 材料缺失/为空/扫描件/含糊 · 编码异常 · `case.json` 不可解析 · 模板缺失 · 字体缺失 · `scripts/` 不完整 · task.md 缺失或冲突 | 不猜内容；回退内置默认；保 SVG；写最小诚实信封；**不伪造数据** |

### 7.1 G-M4 里那条最值得单独说的：PDF 时间戳

**症状**：同一输入两次运行，`figure-*.pdf` 的 `sha256` 不同 → `result.json.artifacts_sha256`
的 pdf 条目跟着变 → `verify_rerun` 报差异。

**根因（实测定位）**：Pillow 写 PDF 时注入当前时间戳 ——
`/CreationDate (D:…Z)`、`/ModDate (D:…Z)`。`cmp -l` 显示两份 PDF 仅差 **4 个字节**，
全部落在时间戳上。

**处置**：`chartkit.stamp_pdf_deterministic()` 把这三个字段（含 `/ID`）就地归一化为固定值，
`_adjust_xref_offsets()` 同步修正交叉引用表中指向新位置的对象字节偏移。
**只改元数据字节、不改页面内容。**

**实测效果**：修复前 5 个产物字节不同（两份 PDF + 两份报告 + `result.json`），
修复后分辨率的产物**全部一致**，`verify_rerun` 报 `DETERMINISTIC (identical=9 differ=0)`，
PDF 大小不变（343392 B，新旧时间戳等长），`pypdf` 仍能解析（1 页）。

**为什么归到 M4**：它直接决定 `sha256` 能不能当证据 ——
这是机制四存在的全部理由。

---

## 8. 复用（生态贡献的实质：别人能拿走什么）

**资产清单与三条复用路径见 `references/REUSE-KIT.md`**；此处只给索引：

| 想拿走多少 | 路径 | 拿走什么 | 验证标准 |
|-|-|-|-|
| 只想要可编辑科研图 | 路径一（约 10 分钟） | `chartkit` + `cjkfont` + `svgtext` + 两份模板 | SVG 存在、分层、含 `<text>`、图元带 `data-*` |
| 想要可核验的交付链路 | 路径二（约 30 分钟） | 再加 `mapcheck`/`figcheck`/`verify_rerun`/`check_contract` + 契约文档 | 四个校验器全 exit 0 |
| 想要"证明增益 + 说明机制" | 路径三（约 1 小时） | 再加 `baseline_agent`/`measure_ab` + 协议与机制模板 | 两侧都有对照报告；协议写了"不做的事" |

**复用时的十条验收清单**见 `REUSE-KIT.md` §3；
**不要带走的五项**（本包特有，带了会误导）见 `REUSE-KIT.md` §4。

---

## 9. 交付前自查

- [ ] `mapcheck` 0 mismatch（M1）
- [ ] 任取一个 `data-column`/`data-row-index` 回源表能对上（M1）
- [ ] `spec_lint` exit 0（M2）
- [ ] `figcheck` G1–G8 全过、六项标注检查无 `fail`（M1/M3/M4）
- [ ] SVG 分层、含 `metadata`、真实 `<text>` 不转曲（M3）
- [ ] `verify_rerun` 归一化后 `differ=0`（M4②）
- [ ] `check_contract` `missing=0 null=0`（M4①）
- [ ] 实体名与源材料原文一致，未"修正"拼写（M1-R5）
- [ ] 中文标签字体回退生效或已记 `uncertainty`（G-X）
- [ ] 无编造数据、无网络访问、无凭据写入

---

## 10. 限制（如实声明）

- **不做统计推断**：显著性计算、拟合、检验不在范围内，只转述材料给的数值。
- **机制/通路图自动布局是启发式的**；复杂通路建议在 spec 手给节点坐标。
- **PDF 预览是光栅预览嵌入 PDF**；矢量可编辑源以 SVG 为准。
- **中文字体依赖运行环境**；缺字体时 SVG 走回退链、PNG 记 warn。
- **`spec_lint.py` 不核对列存在性**（实测：引用不存在的列仍返回 `SUMMARY: VALID`、exit 0）。
  即"生成门"（M2）不是唯一防线；真实兜底是 M1 的三向核对（列不存在必然 mismatch）。
  本版**未改代码**（CLI 与算法接口不得变动）。
- **四个机制都有边界**：M1 只保证"可回溯"，不保证"数据本身正确"；
  M3 只保证"双端同源"，不保证"图面美观"；M4 只保证"可被机器接手且可复现"，
  不保证"契约字段的业务含义正确"。`references/MECHANISM.md` §6 给出相对
  通用绘图库 / 现成模板 / 一次性脚本的**边界对照表**。
- **包内零二进制**；所有图与预览运行时生成。

---

## 11. 资源清单（相对 `$SKILL_DIR`）

```
SKILL.md                            本文件（机制主张 + M1–M4 + 链路 E0–E8 + 规则 + 分支 + 复用索引）
README.md                           使用说明 + §6 复用步骤（三条路径的可操作版本）
TEST.md                             真机实测记录（机制逐条实测 + 复用验收实测 + 未解决项）
REFINEMENT-NOTES.md                 本版相对基线的逐条增改与 diff 定位
GITHUB_URL.txt                      公开作品链接（单行）
scripts/main.py                     主入口（E1→E8）
scripts/chartkit.py                 渲染引擎（Scene → SVG/PNG/PDF + 八类校验 + PDF 确定性归一化）
scripts/extract.py                  列画像 + 实体/关系抽取
scripts/spec_lint.py                生成门（E1–E10；exit 2 = 有 error）
scripts/figcheck.py                 G1–G8 硬门 + 六类检查点
scripts/mapcheck.py                 三向核对（SVG ↔ manifest ↔ 重读源表）
scripts/verify_rerun.py             确定性再跑 / artifacts sha256
scripts/check_contract.py           字段覆盖自查（解析 OUTPUT_CONTRACT.md）
scripts/cjkfont.py                  中文字体发现与回退
scripts/svgtext.py                  SVG 文本转义/清理 + 防转曲检查
examples/baseline_agent.py          条件 A（基准做法）的可复跑参照实现
examples/measure_ab.py              12 项机器可判定指标的 A/B 度量器
examples/case.json / data.csv / …   合成示例输入（非平台案例）
templates/*.json                    图规格 schema / 结果信封模板 / 期刊样式预设 / 实体词表
references/MECHANISM.md             ★ 本版主件：四个机制 + "没有它会怎样" + 咬合图 + 边界对照表
references/REUSE-KIT.md             ★ 本版主件：资产清单（A/B/C 分级）+ 三条复用路径 + 验收清单 + 不要带走的东西
references/GAIN-PROTOCOL.md         公平对照协议 + 指标定义 + 实测记录（B 轴资产，本版一并保留）
references/RUBRIC_MAP.md            五维评分 → 本包落点（创新与生态两节指向本版的机制/复用文件）
references/failure-modes.md         失败模式全表（按"破坏哪个机制"分组）
references/workorder-field-map.md   输入 → 字段 → 输出 映射链
references/audit-rules.md           审计规则（检查项 / 级别 / 处置）
references/encoding-spec.md         CJK / 单位 / 实体命名 / SVG 编码规范
references/typesetting-presets.md   期刊排版预设说明
```

**本版独有的三份文件**：`references/MECHANISM.md`、`references/REUSE-KIT.md`，
以及 `examples/measure_ab.py`（与 `baseline_agent.py` 配对的度量器）。
它们分别对应「创新增益 15」与「生态贡献 10」两个维度。
