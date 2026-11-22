# failure-modes.md — 失败模式与处置

本类图题的真实失败大多"看不见"：图面漂亮但数值错、图例错配、实体名拼错、
单位量级错、中文乱码、导出不可编辑。以下按故障模式列出**症状 → 检测点 →
处置 → 记录位置**，覆盖七类：材料异常（§1）、数据异常（§2）、渲染/图面异常（§3）、
导出/可编辑性异常（§4）、**契约四形态异常（§5）**、**模板/依赖/资源缺失（§6）**、
状态一致性（§7）。

## 1. 材料异常

| # | 故障模式 | 症状 | 检测点 | 处置 | 记录 |
|-|-|-|-|-|-|
| M1 | 材料缺失 | task.md/data 文件不存在 | CP1 盘点 | 不猜内容；明确列缺失路径 | status=partial；uncertainty |
| M2 | 材料为空 | 0 行 / 空表 | load_table | SpecError 明示 | failed_figures |
| M3 | 材料受保护/扫描件（PDF 类） | 无法直接抽取 | extract/平台 pdf-text-tool | 用平台工具转文本；仍不可读 → 说明并 partial | uncertainty：工具与限制 |
| M4 | 生物源材料含糊 | 实体无法确认 | 词表扫描 hit | 候选标 uncertain，Agent 对照原文确认后才上图 | extract.uncertain；uncertainty |
| M5 | 编码异常 | CSV 乱码/BOM | utf-8-sig 读取 | 按 BOM/UTF-8 正确解码；实在乱码 → partial | uncertainty |

## 2. 数据异常

| # | 故障模式 | 症状 | 检测点 | 处置 | 记录 |
|-|-|-|-|-|-|
| D1 | 缺列 | x/y/error 列不存在 | spec_lint E3/extract 画像 | 用画像修正列名；禁止补造列 | failed_figures 或修正后重跑 |
| D2 | 空值/NaN | 部分格子空 | 画像 n_null/校验 | 跳过该点并计数；整列无值 → 报错 | uncertainty：空值策略与数量 |
| D3 | 量级异常 | 数值 vs 标题语义差 >10x | 无自动判据（warn 记录） | warn 保留原值 + 标注可疑 | uncertainty/warnings |
| D4 | 单位缺失/错误 | 轴标签无单位 | axis-units 校验 | 从列名括号提取或按源元数据补 unit | validation warnings |
| D5 | 误差线语义不明 | 分不清 SE/SD/CI | E4/spec.error.semantics | 按源元数据写 semantics（缺则 uncertainty） | validation |
| D6 | filter 无匹配 | 子集为空 | apply_row_filter | 报错列出可用取值 | failed_figures |
| D7 | 统计值未提供 | box/pie 需要统计量 | presets 直供 | 用源给的最小/中位/四分位；不代算 | 转述声明 |

## 3. 渲染/图面异常

| # | 故障模式 | 症状 | 检测点 | 处置 | 记录 |
|-|-|-|-|-|-|
| R1 | 刻度重叠/标签过长 | 刻度文字叠在一起 | 自动旋转 30° | 记录 adjustments | validation.adjustments |
| R2 | 文本遮挡 | 图例/标注盖住数据 | occlusion 真实测量 | 图例移出绘图区；手给节点坐标 | validation occlusion warn |
| R3 | 中文缺字（PNG） | 方框/乱码 | cjk-font 校验 | SVG 回退链照常；PNG 记 warn | uncertainty + cjk-font warn |
| R4 | 图例-系列错配 | 图例对不上数据 | legend-mapping 校验 | 自动对齐；无法对齐 → 修 spec | validation fail 时阻止交付 |
| R5 | 显著性缺配对 | 只有星号无线段 | significance 校验 | 修 annotations | validation fail |
| R6 | 多边形越界/画布过小 | 图面留白后无空间 | compute_plot_area | 报错提示增大画布/减边距 | failed_figures |
| R7 | 网络边悬空 | 关系引用未知节点 | E8 + warnings | 不画该边并记录 warning | validation warnings |

## 4. 导出/可编辑性异常

| # | 故障模式 | 症状 | 检测点 | 处置 | 记录 |
|-|-|-|-|-|-|
| E1 | 文字转曲 | SVG 文字变 path | figcheck G5 real_text | chartkit 保证真实 <text>；编辑器勿转曲保存 | gates.G5 |
| E2 | 无分层/无溯源 | SVG 扁平、无 data-* | G5 layers/provenance | 用官方 pipeline 重生成 | gates.G5 |
| E3 | 外部实体/XXE | SVG 含 DOCTYPE/ENTITY | G5 no_xxe | 拒绝生成含外部实体的产物 | gates.G5 |
| E4 | PNG 损坏/缺失 | 打不开/空文件 | G6 open+verify | 查 Pillow/路径；缺失时保 SVG | gates.G6 |
| E5 | PDF 头损坏 | 无法打开 | G6 %PDF | 重渲染或跳过并警告 | gates.G6 |
| E6 | DPI/色域不符 | 投稿打回 | environment 记录 | 选对预设（nature/cell=300dpi） | environment |
| E7 | 确定性破坏 | 重跑字节不同 | verify_rerun | 查随机/时间戳入图（SVG 禁用）；如实记录 | artifacts_sha256 |

## 5. 契约四形态异常（G2）

`output_contract` 允许四种写法（见 `OUTPUT_CONTRACT.md` §2），任何一种写坏都必须在
**不编造字段值**的前提下给出可解释的结果：

| # | 故障模式 | 症状 | 检测点 | 处置 | 记录 |
|-|-|-|-|-|-|
| C1 | 契约形态①字段名列表 混入非字符串 | 列表中混入对象/数字 | `apply_output_contract` 逐项类型检查 | 跳过非法项，其余照常回显 | `output_contract_applied=true` + uncertainty |
| C2 | 契约形态②/④ 声明了未知类型名 | `"foo": "datetime"` | `defaults` 查表未命中 | 按字符串容器给 `""`（绝不 `null`） | 同上 |
| C3 | 契约声明的字段脚本无法产出 | 例如要求 `regression_stats` | 别名表未命中 | **不做假的映射**：给声明容器类型的空值，并在 `uncertainty` 写明"该字段本 Skill 不产出" | uncertainty |
| C4 | 完全没给 `output_contract` | case.json 无该键 | `main.py` CP6 | `output_contract_applied=false`，只写本 Skill 自有字段（不臆造契约字段） | `output_contract_applied` |
| C5 | 契约声明与产物不一致 | 声明 `editable_source` 但没出 SVG | `check_contract.py` | 命令返回 1，列出 missing/null 字段；修复后重跑 | `check_contract` 报告 |

> 自查命令：`python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>`
> （退出码 1 = 有缺口；2 = 契约文档/result.json 读不了）。

## 6. 模板、依赖与资源缺失（降级不静默）

| # | 故障模式 | 症状 | 检测点 | 处置 | 记录 |
|-|-|-|-|-|-|
| X1 | `templates/journal_styles.json` 缺失/坏 JSON | 样式预设读不到 | `chartkit.load_journal_styles()` | **回退内置默认样式**继续出图，不中断 | `environment.style` + uncertainty |
| X2 | `templates/entity_glossary.json` 缺失 | 关系类型着色/词表扫不到 | `chartkit` 读取处 | 回退内置"关系类型→颜色/线型"默认表；词表扫描跳过 | uncertainty |
| X3 | `templates/figure_map.schema.json` 缺失 | 无 schema 可对照 | 仅文档/人读用途 | 脚本不依赖该文件；lint 仍按内置规则跑 | —（不属于运行故障） |
| X4 | Pillow 缺失 | PNG/PDF 渲染失败 | `chartkit.HAS_PIL` | **保 SVG 与全部 JSON**，PNG/PDF 记为缺失并写明安装方式 | `uncertainty`/`warnings`，G6 |
| X5 | 字体目录不可读/无 CJK 字体 | PNG 中文可能缺字 | `FontMap._scan` try/except + `cjk-font` 检查 | SVG 回退链照常；PNG 记 warn；可用 `FONT_PATHS` 指定 | `environment.fonts`、uncertainty |
| X6 | `--out`/`--work` 目录不可写 | 写文件异常 | `os.makedirs` / `_write_json` | `failed` + `error` 与 traceback 摘要（最小诚实信封） | `result.json.status=failed` |
| X7 | 脚本被从别处复制后缺文件 | 例如 `scripts/` 不完整 | `import` 立即报错 | 命令非零退出并打印缺失模块，不产出半成品 result | 退出码 1 |

## 7. 状态一致性（G8）

所有失败最终收敛到三态：

| result.status | 条件 | 说明 |
|-|-|-|
| `completed` | 1) 全部图导出成功 2) spec_lint 无 error 3) 校验六项无 fail 4) G1–G8 全过 | 允许 warn（uncertainty 说明） |
| `partial` | 任一条件不满足但仍产出部分图 | failed_figures/uncertainty 列全 |
| `failed` | 无任何图产出 / 运行异常 | error + traceback 摘要（最小诚实信封：case_id/status/error/uncertainty/sources/change_records） |

**禁止**：把失败写成完成、把 warn 写成无、把材料缺失写成有数据（D9/D10/D16）。

## 8. 复验路径

每类失败都给出复验命令（`$SKILL_DIR` = 本包绝对路径；任意 cwd 可跑）：

```bash
python "$SKILL_DIR/scripts/main.py" --case <case> --out <out> --note "修复说明"
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case>  # 字段覆盖
python "$SKILL_DIR/scripts/figcheck.py" --dir <out> --case <case>                       # G1–G8
python "$SKILL_DIR/scripts/mapcheck.py" --dir <out> --case <case>                       # 值核对
python "$SKILL_DIR/scripts/verify_rerun.py" --case <case> --out <out>                   # 确定性
```