# scientific-figure-craft — 科研数据图表生成与编辑 Skill

面向「玻尔产品周赛 · 北大专区 · 学术效率 · 第三期」 challenge-1bd90d8a（figures 组）。
从科研数据表格 / 生物源材料生成**可投稿、可编辑、可核验**的图稿：
分层可编辑 SVG（每个图元带 data-* 溯源）+ PNG/PDF 预览 + 数据图元双向映射 + 标注校验 + 契约化 result.json。

## 快速开始

```bash
# 最小示例（含任务说明与两类数据；产出全部在 <out> 下）
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-1bd90d8a

# 独立复核输出目录（契约/文件/SVG 结构/PNG/PDF）
python scripts/validate_result.py --dir D:/BuildTemp/smoke-1bd90d8a --case examples/case.json
```

运行后 `<out>/` 下应有：

```
figure-fig-01.svg / .png / .pdf   图 1：柱状+折线多面板（含误差线与显著性标注）
figure-fig-02.svg / .png / .pdf   图 2：Wnt 机制通路图（实体关系逐元素带 cite）
data_manifest.json                图元 ↔ 源数据（文件/列/行/值）双向映射
validation.json                   标注校验清单（8 类检查）
result.json                       契约化结果（case_id + 全部契约字段）
```

> examples/ 内的输入与 `task.md` 均标注为**示例，非正式案例**；
> 正式评分为平台固定 3 案例，与示例无关。

## 运行方法（正式案例）

```bash
# 运行期输入在 /input/case.json 与 /input/task.md；产物写 /app/output
python /skills/weekly-skill/scripts/main.py --case /input/case.json --out /app/output
python /skills/weekly-skill/scripts/validate_result.py --dir /app/output --case /input/case.json
```

- 命令不依赖当前工作目录：脚本内用 `os.path.dirname(__file__)` 自定位到技能根。
- 图规格写进 case.json 的 `figures[]`（或 `figure`/`figure_spec`），契约见
  [references/OUTPUT_CONTRACT.md](references/OUTPUT_CONTRACT.md) §5；缺省按列名自动推断。

### 常用参数

| 参数 | 说明 |
|-|-|
| `--case <path>` | case.json（必填；兼容顶层对象/`cases[]`/数组） |
| `--out <dir>` | 输出目录（默认 `./out`） |
| `--task <path>` | 显式 task.md（缺省自动发现同目录 task.md / task_file 字段） |
| `--data <f>[;<f>]` | 显式源数据（缺省自动发现案例同目录表格） |
| `--style <name>` | default/nature/cell/prism/minimal/ppt（styles/presets.json 可扩展） |
| `--dpi <n>` | PNG 渲染分辨率（默认 150；nature/cell 预设为 300） |
| `--note "..."` | 追加一条人工变更记录（change record，带时间戳） |
| `--no-pdf` | 跳过 PDF 预览 |

## 支持能力

- **图型 8 类**：bar（分组柱状+误差线+显著性标注）、line、scatter、box（原始值或直供统计值）、
  heatmap（多色阶+色标）、pie（扇区角度映射）、network（机制/通路图：节点-边、激活/抑制/磷酸化/转录
  自动着色、逐元素 cite 溯源、分层自动布局）、panel（多面板组合，子面板可独立数据文件与 filter）。
- **数据溯源**：SVG 每个数据图元带 `data-*` 属性（列/行/值/系列/类别），
  `data_manifest.json` 以 svg_id 对齐实现双向检索。
- **标注校验 8 类**：溯源覆盖、图例-系列对应、轴单位、范围覆盖、CJK 字体、显著性配对、
  空值处理、文本遮挡（真实字体测量）。校验结果写 validation.json，失败列表逐条处置。
- **样式预设**：default/nature/cell/prism/minimal/ppt，字号/线宽/配色/边距/DPI 统一；
  `styles/presets.json` 可直接扩展新期刊。
- **字体自适应**：自动扫描 Windows/Linux/macOS 字体目录（可用 `FONT_PATHS` 追加）；CJK 标签
  使用回退链（YaHei/Noto CJK/思源/文泉驿/SimHei），PNG 缺字时 bug 记 warn 而非静默乱码。

## 依赖

| 依赖 | 版本要求 | 用途 | 缺省情况 |
|-|-|-|-|
| Python | 3.8+ | 全部逻辑 | — |
| Pillow | ≥9 (实测 12.3) | PNG/PDF 渲染、字体发现 | 缺失时仍产出 SVG，PNG/PDF 记为警告 |
| （可选）matplotlib / numpy | 不必须 | 未使用；仅环境自带 | — |

无 cairosvg / svgwrite 依赖：SVG 为**手写 XML**（标准库生成），PNG/PDF 用 Pillow 从
**同一图元场景**渲染，保证矢量与位图逐元素一致。无网络依赖。

## 目录结构

```
SKILL.md                        可执行 Skill 本体（用途/流程/决策规则 D1–D12/失败分支/自查）
README.md                       本文件
GITHUB_URL.txt                  公开作品链接（发布代理覆写精确链接）
TEST.md                         本地实测记录
scripts/
  main.py                       主入口 CLI
  figure_engine.py              渲染引擎（Scene → SVG/PNG/PDF + 校验）
  validate_result.py            独立复核脚本
styles/presets.json             期刊样式预设
references/
  OUTPUT_CONTRACT.md            result.json / validation / manifest / figure spec 契约
  RUBRIC_MAP.md                 五维评分 → 设计覆盖对照
examples/
  case.json / task.md / data.csv / entities.json / OUTPUT.md   最小示例（标注非正式案例）
```

## 限制（如实声明）

1. 统计方法选择与显著性计算**不在**本 Skill 范围：显著性标注只转述源材料给出的 p 值
   并在图注写明来源与检验方法；不代算拟合/检验。
2. 通路图自动布局为启发式（按 group 分层 + 行内分布）；复杂图建议在 spec 中手给节点
   `x/y` 坐标以获得理想版面。
3. PDF 预览为光栅预览嵌入 PDF（检查用）；投稿所需的**矢量可编辑源以 SVG 为准**。
4. 中文渲染依赖运行环境字体；容器缺字体时 SVG 仍可正常打开（回退链），PNG 会记录警告。
5. `case.json` 若缺失 `output_contract`，result.json 仍输出完整默认契约字段
   （`output_contract_applied: false`），不臆造正式案例的契约。

## 失败处理

| 场景 | 行为 |
|-|-|
| 数据文件缺失/为空 | 明确报错列出缺失路径；status=partial + uncertainty，不猜内容 |
| 缺列 | 自动按列名推断（time/dose/se/sem/…）；推断失败→报错并列出可用列 |
| 空值/NaN | 跳过并计数记录；整列无值→该字段报错 |
| 量级异常 | warn 保留原值并标注可疑，不"修正"数据 |
| 标签过长/遮挡 | 自动旋转 30° / 图例移出绘图区，记录 adjustments |
| CJK 字体缺失 | SVG 回退链照常；PNG warn + uncertainty |
| 单图失败 | 不阻塞其他图，failed_figures 列明，status=partial |
| Pillow 缺失 | 保产出 SVG，PNG/PDF 警告 |

完整决策规则与失败分支表见 [SKILL.md](SKILL.md) §4/§5。