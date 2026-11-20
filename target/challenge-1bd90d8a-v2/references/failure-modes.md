# failure-modes.md — 失败模式与处置

本类图题的真实失败大多"看不见"：图面漂亮但数值错、图例错配、实体名拼错、
单位量级错、中文乱码、导出不可编辑。以下按故障模式列出**症状 → 检测点 →
处置 → 记录位置**，覆盖材料异常/数据异常/渲染异常/导出异常四类。

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

## 5. 状态一致性（G8）

所有失败最终收敛到三态：

| result.status | 条件 | 说明 |
|-|-|-|
| `completed` | 1) 全部图导出成功 2) spec_lint 无 error 3) 校验六项无 fail 4) G1–G8 全过 | 允许 warn（uncertainty 说明） |
| `partial` | 任一条件不满足但仍产出部分图 | failed_figures/uncertainty 列全 |
| `failed` | 无任何图产出 / 运行异常 | error + traceback 摘要 |

**禁止**：把失败写成完成、把 warn 写成无、把材料缺失写成有数据（D9/D10/D16）。

## 6. 复验路径

每类失败都给出复验命令：
```bash
python scripts/main.py --case <case> --out <out> --note "修复说明"
python scripts/figcheck.py --dir <out> --case <case>     # G1–G8
python scripts/mapcheck.py --dir <out> --case <case>     # 值核对
python scripts/verify_rerun.py --case <case> --out <out> # 确定性
```