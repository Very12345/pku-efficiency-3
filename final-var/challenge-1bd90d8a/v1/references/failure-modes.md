# failure-modes.md — 失败模式全表（FM-M / FM-D / FM-R / FM-E / FM-C / FM-X）

本文件是 `SKILL.md` §6 失败分支表的**完整版**：每条给出「症状 → 触发条件 →
检出点 → 处置 → `result.json` 落痕字段 → 复验方式」。

**为什么按 FM 族编号**：本类图题的失败大多**不可见**（图面漂亮但数值错、图例错配、
实体名拼错、单位量级错、中文乱码、导出不可编辑）。把失败按来源分族编号，才能在
`result.json` 里一眼看出"这次是材料问题、数据问题，还是导出问题"，而不是笼统一句
"有 warning"。

| 族 | 含义 | 收敛到 |
|-|-|-|
| **FM-M** | 材料异常 | `status` 降级 / `uncertainty` |
| **FM-D** | 数据异常 | `validation` / `uncertainty` |
| **FM-R** | 图面与标注异常 | `validation`（`fail` 会阻断） |
| **FM-E** | 导出与可编辑性异常 | `gates.G5/G6` / `artifacts_sha256` |
| **FM-C** | 契约四形态异常 | `output_contract_applied` |
| **FM-X** | 依赖、模板与资源缺失 | `environment` / 退出码 |

---

## 1. FM-M 材料异常

| 分支 | 症状 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|-|
| **FM-M1** | 材料缺失 | task.md / data 文件不存在 | CP1 盘点 | 不猜内容；明确列出缺失路径 | `status=partial`；`uncertainty` |
| **FM-M2** | 材料为空 | 0 行 / 空表 | `load_table` | 明示为空；该图不产出 | `failed_figures` |
| **FM-M3** | 材料受保护或为扫描件（PDF 类） | 无法直接抽取文本 | extract / 平台 `pdf-text-tool` | 先用平台工具转文本；仍不可读 → 说明工具与限制并降级 | `uncertainty`（含所用工具） |
| **FM-M4** | 生物源材料表述含糊 | 实体无法确认 | 词表扫描命中 | 候选标 `uncertain=true`，**对照原文确认后才可上图**（D4） | `extract.json.uncertain`；`uncertainty` |
| **FM-M5** | 编码异常 | CSV 乱码 / 带 BOM | `utf-8-sig` 读取 | 按 BOM 与 UTF-8 正确解码；确实乱码 → 降级 | `uncertainty` |
| **FM-M6** | `case.json` 不可解析 / `--out` 不可写 | 入口即失败 | `main.py` 顶层 try | 写**最小诚实信封**：`case_id` + `status=failed` + `error` + traceback 摘要 + `sources` + `change_records` + `uncertainty`（实测 6 键） | `status=failed`；退出码 **1** |

---

## 2. FM-D 数据异常

| 分支 | 症状 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|-|
| **FM-D1** | 缺列 | x/y/error 列在表中不存在 | CP2 列画像；**注意 `spec_lint` 不查列存在性**（见下） | 用画像修正列名；**禁止补造列**；修正不了 → 该图失败 | `failed_figures`；修正后重跑 |
| **FM-D2** | 空值 / NaN | 部分格子为空 | 画像 `n_null` + `null-handling` 校验 | 跳过该点并计数；整列无值 → 报错 | `uncertainty`（含数量与策略） |
| **FM-D3** | 量级异常 | 数值与标题语义差 > 10 倍 | 无自动判据 | `warn` 保留原值并标可疑，**不"修正"** | `uncertainty`；`warnings` |
| **FM-D4** | 单位缺失或错误 | 轴标签无单位 | `axis-units` 校验 | 从列名括号提取，或按源元数据补 unit | `validation.warnings` |
| **FM-D5** | 误差线语义不明 | 分不清 SE / SD / CI | `spec.error.semantics` | 按源元数据写 semantics；源未标 → `uncertainty`（**不猜**） | `validation.json` |
| **FM-D6** | `filter` 无匹配 | 子集为空 | `apply_row_filter` | 报错并列出该列可用取值 | `failed_figures` |
| **FM-D7** | 统计值未提供 | box / pie 需要统计量 | `presets` 直供检查 | 只用源给的最小/中位/四分位；**不代算** | 转述声明 |

> **FM-D1 的重要补充（实测发现）**：`spec_lint.py` 对"未知图型"能拦住（`E1`），
> 但对"引用了不存在的列"**实测返回 `SUMMARY: VALID`、exit 0**。因此 CP3 通过
> **不等于**列存在。两层兜底：
> ① CP3 之后核对 `extract.json` 的列画像（SKILL.md §4 S3 判定）；
> ② CP5 的 `mapcheck.py` 重读源表逐行核对，列不存在必然产生 mismatch。
> 这两层都不通过时，按 `failed_figures` 处理，**不得带病交付**。

---

## 3. FM-R 图面与标注异常

| 分支 | 症状 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|-|
| **FM-R1** | 刻度重叠 / 标签过长 | 刻度文字互相叠压 | 字体实测 | 自动旋转 30°；记录该次调整 | `validation.adjustments` |
| **FM-R2** | 文本遮挡数据 | 图例或标注盖住数据 | `occlusion`（真实字体包围盒测量） | 图例移出绘图区；网络图手给节点坐标；复跑后遮挡应降为 0 | `validation` `occlusion` warn |
| **FM-R3** | 中文缺字（PNG） | 方框 / 乱码 | `cjk-font` 校验 | SVG 回退链照常产出；PNG 记 `warn` | `uncertainty`；`environment.fonts` |
| **FM-R4** | 图例与系列错配 | 图例对不上数据 | `legend-mapping` 校验 | 自动对齐；无法对齐 → **修 spec 后重跑** | `validation` `fail` → **阻止 `completed`** |
| **FM-R5** | 显著性缺配对 | 只有星号没有线段（或反之） | `significance` 校验 | 修 `annotations`，使线段数 = 文字数 | `validation` `fail` |
| **FM-R6** | 画布空间不足 | 留白后无绘图区 | `compute_plot_area` | 报错并提示增大画布或减小边距 | `failed_figures` |
| **FM-R7** | 网络边悬空 | 关系引用了未知节点 | `E8` + warnings | 不画该边并记录 warning | `validation.warnings` |

---

## 4. FM-E 导出与可编辑性异常

| 分支 | 症状 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|-|
| **FM-E1** | 文字转曲 | SVG 文字变成 `<path>` | `figcheck` G5 `real_text` | 用本包管线重生成；编辑器保存时**勿选"转曲/轮廓化"** | `gates.G5` |
| **FM-E2** | 无分层 / 无溯源 | SVG 扁平、图元无 `data-*` | G5 `layers` / `provenance` | 用官方管线重生成 | `gates.G5` |
| **FM-E3** | 外部实体（XXE） | SVG 含 `DOCTYPE` / `ENTITY` | G5 `no_xxe` | 拒绝生成含外部实体的产物 | `gates.G5` |
| **FM-E4** | PNG 损坏或缺失 | 打不开 / 空文件 | G6 `open` + `verify` | 查 Pillow 与路径；缺失时**先保 SVG** | `gates.G6` |
| **FM-E5** | PDF 头损坏 | 不以 `%PDF` 开头 | G6 | 重渲染；仍失败则跳过该预览并警告 | `gates.G6` |
| **FM-E6** | 同输入两次运行的 PDF 字节不同 | 重跑对拍发现 pdf sha256 变化 | `verify_rerun` / `artifacts_sha256` | **根因**：Pillow 写 PDF 会写入当前时间戳（`/CreationDate`、`/ModDate`）。**处置**：PDF 落盘后调用 `chartkit.stamp_pdf_deterministic()` 把这两个字段（以及 `/ID`）归一化为固定值，并同步修正 xref 中的对象字节偏移。PDF 是预览件，时间戳无信息量 | `artifacts_sha256` 两次一致；`verify_rerun` 报 `differ=0` |
| **FM-E7** | 重跑后 SVG/JSON 字节不同（非时间戳） | 上述两类之外仍有差异 | `verify_rerun` | 定位随机源（字典遍历序、浮点格式、把时间戳画进图）并修掉；确实无法消除 → **如实记录差异**，不得用"看起来一样"搪塞 | `artifacts_sha256`；`change_records` |
| **FM-E8** | Pillow 缺失 | PNG/PDF 渲染失败 | `chartkit.HAS_PIL` | **保 SVG 与全部 JSON**，PNG/PDF 记为缺失并写明安装方式（`pip install Pillow`） | `uncertainty`；`warnings`；G6 |
| **FM-E9** | DPI / 色彩空间不符投稿要求 | 投稿被打回 | `environment` 记录 | 选对应预设（`nature`/`cell` = 300 dpi）；记录实际导出参数 | `environment.dpi` / `style` |

---

## 5. FM-C 契约四形态异常（对应 G2）

`output_contract` 允许四种写法（见 `OUTPUT_CONTRACT.md` §2）。任何形态写坏，
都必须在**不编造字段值**的前提下给出可解释的结果：

| 分支 | 症状 | 触发条件 | 处置 | 落痕 |
|-|-|-|-|-|
| **FM-C1** | 形态①的列表里混入非字符串项 | 逐项类型检查 | 跳过非法项，其余照常回显 | `output_contract_applied=true` + `uncertainty` |
| **FM-C2** | 形态②/④ 声明了未知类型名（如 `"datetime"`） | `defaults` 查表未命中 | 按字符串容器给 `""`（**绝不 `null`**） | 同上 |
| **FM-C3** | 契约声明了本 Skill 不产出的字段（如 `regression_stats`） | 别名表未命中 | **不做假映射**：给声明容器类型的空值 + 写明"该字段本 Skill 不产出" | `uncertainty` |
| **FM-C4** | 完全没有 `output_contract` | `case.json` 无该键 | `output_contract_applied=false`；只写本 Skill 自有字段，**不臆造契约字段** | `output_contract_applied` |
| **FM-C5** | 契约声明与产物不一致（声明了 `editable_source` 却没出 SVG） | `check_contract.py` | 返回 **exit 1** 并列出 missing/null 字段；修复后重跑 | `check_contract` 报告 |

```bash
# 复验命令（$SKILL_DIR = 本包绝对路径；任意 cwd 可跑）
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>
# 退出码 0 = PASS；1 = 有缺口（列出 missing/null）；2 = 契约文档或 result 不可读
```

---

## 6. FM-X 依赖、模板与资源缺失（降级但不静默）

| 分支 | 症状 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|-|
| **FM-X1** | `templates/journal_styles.json` 缺失或 JSON 损坏 | 样式预设读不到 | `chartkit.load_journal_styles()` | **回退内置默认样式**继续出图，不中断 | `environment.style`；`uncertainty` |
| **FM-X2** | `templates/entity_glossary.json` 缺失 | 关系着色 / 词表扫描不可用 | `chartkit` 读取处 | 回退内置"关系类型 → 颜色/线型"默认表；词表扫描跳过 | `uncertainty` |
| **FM-X3** | `templates/figure_map.schema.json` 缺失 | 无 schema 可对照 | 仅文档/人读用途 | 脚本不依赖该文件；lint 仍按内置规则跑 | —（非运行故障） |
| **FM-X4** | 字体目录不可读 / 无 CJK 字体 | PNG 中文可能缺字 | `FontMap._scan` 的 try/except + `cjk-font` 检查 | SVG 回退链照常；PNG 记 warn；可用 `FONT_PATHS` 指定 | `environment.fonts`；`uncertainty` |
| **FM-X5** | `--out` / `--work` 目录不可写 | 写文件异常 | `os.makedirs` / `_write_json` | `failed` + `error` 与 traceback 摘要（最小诚实信封） | `status=failed` |
| **FM-X6** | 脚本被单独复制走导致 `scripts/` 不完整 | 例如缺 `chartkit.py` | `import` 立即报错 | 命令非零退出并打印缺失模块，**不产出半成品 result** | 退出码 1 |
| **FM-X7** | 环境无网络但需要外部资源 | 本包不访问网络 | — | 本包零网络依赖；若案例材料要求联网，按 FM-M1 记为缺失并降级 | `uncertainty` |

---

## 7. 状态一致性（G8）：所有失败最终收敛到三态

| `result.status` | 条件 | 说明 |
|-|-|-|
| `completed` | ① 全部图导出成功 ② `spec_lint` 无 error ③ 校验六项无 `fail` ④ G1–G8 全过 | 允许 `warn`，但须在 `uncertainty` 说明 |
| `partial` | 任一条件不满足，但仍产出部分图 | `failed_figures` / `uncertainty` 写全 |
| `failed` | 无任何图产出，或运行异常 | `error` + traceback 摘要；最小诚实信封（`case_id`/`status`/`error`/`uncertainty`/`sources`/`change_records`） |

**四条禁止**（对应 SKILL.md D10 / D16）：
1. 把失败写成完成；
2. 把 `warn` 写成"无问题"；
3. 把材料缺失写成"有数据"；
4. 把契约字段缺失写成 `null`（应给声明容器类型的空值）。

---

## 8. 复验路径（每条失败都有命令）

`$SKILL_DIR` = 本包绝对路径；脚本自定位，任意 cwd 可跑：

```bash
python "$SKILL_DIR/scripts/main.py" --case <case> --out <out> --note "修复说明"
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case>  # 字段覆盖（本文件 §5）
python "$SKILL_DIR/scripts/figcheck.py" --dir <out> --case <case>                       # G1–G8（§4 的导出类）
python "$SKILL_DIR/scripts/mapcheck.py" --dir <out> --case <case>                       # 值核对（§2 的 FM-D1 兜底）
python "$SKILL_DIR/scripts/verify_rerun.py" --case <case> --out <out>                   # 确定性（§4 的 FM-E6/E7）
python "$SKILL_DIR/scripts/spec_lint.py" --spec <case> --case <case>                    # 规格门（§2 的 FM-D1 第一层）
```
