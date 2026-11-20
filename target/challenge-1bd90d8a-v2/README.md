# scientific-figure-craft v2 — 科研数据图表生成与编辑（challenge-1bd90d8a 加强包）

面向「玻尔产品周赛 · 北大专区 · 学术效率 · 第三期」 challenge-1bd90d8a（figures 组，
数据图表生成与编辑）的 **v2 加强包**。v2 在 build 基础包之上按高分意图做了
「执行决策显性化」强化：**检查点 CP1–CP6 + 决策规则 D1–D18 + 双校验
（mapcheck 数据↔图元 / figcheck G1–G8）+ spec 级样式内联覆盖 + 确定性再跑验证**。

> 本包只做制作与验证，**不提交平台、不发布仓库**。投递前需按
> `work/科学挑战赛` 的 AGENTS.md 流程 dry-run + trace 验证。

## 1. 用途与适用条件

- **适用**：平台固定 3 个案例（数据图表生成 / 样式调整 / 标注校验 / 源数据关联 /
  可编辑源文件与导出），以及任何「源数据表或生物源材料 → 可编辑科研图」请求。
- **边界**：不负责统计方法选择与显著性计算本身（显著性只转述源数据给出的 p 值，
  见 SKILL.md D6）；不负责实验设计；不替用户下科学结论。
- **环境**：Python 3.8+ 标准库 + Pillow（PNG/PDF 预览）。matplotlib/cairosvg/svgwrite
  均非必需，无网络依赖。本机实测 Python 3.13.9 + Pillow 12.3.0（TEST.md T1）。
- **完整入口**：先读 `SKILL.md`（含 S0–S7 执行步骤、检查点 CP1–CP6、决策规则
  D1–D18、失败分支表），再按下面命令执行。

## 2. 目录结构

```
SKILL.md                          主文件：用途/输入输出/执行步骤/异常处理/自查清单
                                   + 决策规则 D1–D18 + 检查点 CP1–CP6
README.md                         本文件（使用说明）
TEST.md                           本地实测记录（编译/冒烟/确定性/契约/全检）
COMPARE.md                        三方对照（build 基础 vs 高分结构 vs v2）+ 增强点
GITHUB_URL.txt                    仓库链接（两行：链接 + 相对路径）
scripts/main.py                   编排入口：CP1→CP6，生成产物 + result.json
scripts/chartkit.py               渲染引擎（Scene → SVG/PNG/PDF + 八类校验）
scripts/extract.py                CP2：列画像 + 实体/关系抽取（extract.json）
scripts/spec_lint.py              CP3：figure spec 结构校验（E1–E10）
scripts/figcheck.py               CP5：G1–G8 硬门 + 六类检查点（交付审计）
scripts/mapcheck.py               CP5：数据↔图元双向映射 + 源值核对（容差 1e-9）
scripts/verify_rerun.py           D18：确定性再跑验证 / artifacts sha256
scripts/cjkfont.py                中文字体发现与回退（编码规范执行端）
scripts/svgtext.py                SVG 文本转义/清理（编码规范执行端）
templates/figure_map.schema.json  图规格声明式契约（JSON Schema 风格）
templates/result.template.json    result.json 信封模板
templates/journal_styles.json     期刊样式预设（default/nature/cell/prism/minimal/ppt）
templates/entity_glossary.json    连接规则字典 + 实体词表
references/output-contract.md     result.json / validation / manifest / spec 契约 + G1–G8
references/rubric-map.md          五维评分 → 设计覆盖对照
references/workorder-field-map.md 输入→字段→输出 映射链
references/audit-rules.md         审计规则（检查项/级别/处置）
references/encoding-spec.md       CJK/单位/实体命名/SVG 编码规范
references/typesetting-presets.md 期刊排版预设说明（三层覆盖方式）
references/failure-modes.md       失败模式与处置（M/D/R/E 四类）
examples/                         最小示例（标注"非正式案例"）
examples/case.json                示例案例：panel（bar+line）+ network（Wnt 通路）
examples/task.md                  示例任务说明
examples/data.csv                 示例源数据（8 行：剂量-时间-均值-SE-n）
examples/entities.json            示例生物源实体/关系（Wnt 信号通路）
examples/material.md              示例生物源材料（ENTITY:/REL: 行语法 + 词表扫描样例）
examples/output/                  示例输出（本机真实运行产物，*.example.* 标注示例）
```

与高分形态的对应（详见 `references/rubric-map.md` 与 `COMPARE.md`）：本包对齐
78.00/77.00/74.67 三份高分包的共性结构 —— `SKILL.md` 在根、references 规范前置、
scripts 按职责拆分（chartkit/main 生成 ↔ figcheck/mapcheck/verify_rerun 校验 ↔
cjkfont/svgtext 文字）、templates 双层 schema（figure_map.schema + result.template）、
examples 可运行示例、GITHUB_URL.txt。

## 3. 调用方式（脚本自定位，任意 cwd 均可）

```bash
# 主流程（CP1→CP6，缺省样式 default；--style 可选覆盖，spec 内 style 字段优先合并）
python scripts/main.py --case <case.json> --out <out_dir> [--work <work_dir>]
                      [--task <task.md>] [--style nature] [--dpi 300] [--note "人工调整"]

# 独立复核（build 后 verify 成对）
python scripts/figcheck.py --dir <out_dir> --case <case.json>      # G1–G8 + 六类检查点
python scripts/mapcheck.py --dir <out_dir> --case <case.json>      # 数据↔图元双向
python scripts/verify_rerun.py --case <case.json> --out <out_dir>  # 确定性再跑（D18）

# 中间产物
python scripts/extract.py --case <case.json> --out <work_dir>      # CP2 抽取
python scripts/spec_lint.py --spec <case.json> --case <case.json>  # CP3 生成门
```

最小示例（真实跑通，产物见 examples/output）：
```bash
python scripts/main.py --case examples/case.json --out examples/output --style nature
```

投产装到平台后为 `/skills/weekly-skill`，命令即
`python /skills/weekly-skill/scripts/main.py --case /input/case.json --out /app/output`。
脚本一律用 `os.path.dirname(__file__)` 自定位资源（templates/references），
不依赖当前工作目录（SKILL.md S0-4）。

## 4. 输入与输出

**输入**：`/input/case.json`（case_id、figures[]、output_contract，四种形态均可）、
`/input/task.md`、源数据表（CSV/TSV/JSON）、生物源材料（entities_file JSON /
material 文本；含 PDF 时用平台 pdf-text-tool 提取）。

**输出（/app/output，UTF-8）**：

| 文件 | 内容 |
|-|-|
| `figure-<id>.svg` | 可编辑分层矢量源（`<g id="layer-*">` 分层、`<metadata id='provenance'>` 溯源、每个数据图元带 `data-*` 属性、真实 `<text>` 永不转曲） |
| `figure-<id>.png` / `.pdf` | 同一图元场景预览 |
| `data_manifest.json` | 图元 ↔ 源数据映射（文件/列/行/值；svg_id 对齐） |
| `validation.json` | 八类标注校验清单 |
| `mapcheck_report.json` / `figcheck_report.json` | CP5 双校验报告（含 G1–G8） |
| `result.json` | 结构化结果（契约见 `references/output-contract.md`） |

## 5. 关键方法与设计

1. **检查点流水线 CP1–CP6**：材料盘点 → 抽取 → spec lint 生成门 → 导出 →
   双校验 → 契约落地。每步有机器判定，未过不得进入下一步（SKILL.md §3/§5）。
2. **双校验**：`mapcheck` 做数据↔图元**双向**核对（manifest 元素必须在 SVG 存在、
   SVG 数据层图元必须登记、`column+row_index+value` 重读源文件逐行核对，容差 1e-9）；
   `figcheck` 以 G1–G8 硬门收口（契约 → 文件 → SVG 可编辑性 → 预览 → 六项标注 →
   status 自洽）。
3. **数据到图元可解释**：每个图元带 `data-*` 属性（文件/列/行/值），manifest 与
   mapcheck 保障「从图回溯到数据、从数据定位到图元」。
4. **样式规则化（D17）**：期刊样式 = `templates/journal_styles.json` 命名预设；
   优先级 基样式（CLI/默认）→ `spec["style"]` 命名预设 → spec 内联键（title_size/
   tick_size/…）。加新期刊 = 加预设键，不改代码。
5. **确定性（D18）**：同输入同参数重跑，SVG/PNG/manifest/validation 字节级稳定；
   PDF/result.json 仅时间戳/自哈希差异，`verify_rerun` 归一化后判定。
6. **中文渲染**：CJK 字体族回退链（SVG）+ FontMap 扫描（PNG），缺字如实记录。

## 6. 复盘与验证

- 实测记录：`TEST.md`（T1–T9，含命令/产物 sha256/结论）。
- 三方对照与增强点清单：`COMPARE.md`。
- 五维评分覆盖自评：`references/rubric-map.md`。
- 契约与硬门：`references/output-contract.md`（G1–G8）。
- 失败处置：`references/failure-modes.md`（M/D/R/E 四类 18+ 项）。

## 7. 限制（如实声明）

- 统计（显著性计算、拟合、检验）不在本 Skill 范围：只转述材料已给的 p 值/统计量。
- 机制/通路图自动布局为启发式（按 group 分层 + 行内分布）；复杂图建议在 spec 手给
  节点 x/y（D13，示例 entities.json 即手工坐标）。
- PDF 预览 = 光栅预览嵌入 PDF（检查用）；投稿要求的矢量可编辑源以 SVG 为准。
- 中文字体依赖运行环境字体；缺字体时 SVG 靠回退链、PNG 记 warn（D5）。
- 词表扫描只做候选提示，不替代 Agent 对源材料的确认（D4）。
- examples/ 全部标注「示例，非正式案例」，与平台正式 3 案例无关；正式运行禁止照抄
  示例内容。