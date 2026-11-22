# failure-modes.md — 失败模式全表（按"打击哪项可测能力"归类）

本文件是 `SKILL.md` §6 的完整版。与常见写法的区别：**不按错误类型排，按它打击哪一项
可测能力排** —— 因为本版的定位是"增益可验证"，每一条失败最终都要能被映射到
`references/GAIN-PROTOCOL.md` 的某个指标（Q1–Q12）上。

| 分组 | 打击的指标 | 收敛到 |
|-|-|-|
| **F-A** 可编辑矢量源 | Q1 / Q2 | `gates.G5` |
| **F-B** 图元↔源数据闭合 | Q3 / Q4 / Q5 | `mapcheck_report.json` |
| **F-C** 单位与量级 | Q6 | `validation.axis-units` |
| **F-D** 标注与图面 | Q7 / Q8 | `validation.json` / `gates.G7` |
| **F-E** 结果信封与审计 | Q9 / Q10 / Q11 | `check_contract` / `result.json` |
| **F-F** 确定性（增益可验证性的地基） | Q12 | `verify_rerun` / `artifacts_sha256` |
| **F-G** 材料、依赖与环境（横切） | 全部 | `status` / `exit code` / `uncertainty` |

每条格式：**触发条件 → 检出点 → 处置 → 落痕字段 → 复验方式**。
分组规模（实测）：**F-A 4 · F-B 7 · F-C 3 · F-D 10 · F-E 8 · F-F 5 · F-G 12 = 49 条**。

> **编号用法**：`SKILL.md` §6 的六类小标题与本节的分组**一一对应**（同名 F-A..F-G，
> 其中 §6 把 F-C 并入 F-D 一并叙述，故 §6 显示五类）；本文件的 **49 条编号条目**
> 是权威全集。反查命令：
> ```bash
> for g in A B C D E F G; do printf "F-%s: %s
" "$g" >   "$(grep -oE "F-$g[0-9]+" references/failure-modes.md | sort -u | wc -l)"; done
> ```

---

## 1. F-A 打击 Q1 / Q2（可编辑矢量源）

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| **F-A1** | SVG 未生成（渲染异常） | 文件存在性 | 保全部 JSON 落盘，写明原因；`status` 降级 | `status=partial`；`uncertainty` |
| **F-A2** | SVG 扁平、图元无 `data-*` | G5 `layers` / `provenance` | 用本包管线重生成（**不得手改 SVG 补属性**） | `gates.G5` |
| **F-A3** | 文字被转曲（变 `<path>`） | G5 `real_text` | 重新生成；编辑器保存时勿选"转曲/轮廓化" | `gates.G5` |
| **F-A4** | SVG 含 `DOCTYPE` / 外部实体 | G5 `no_xxe` | 拒绝生成含外部实体的产物 | `gates.G5` |

> Q1/Q2 判定：`*.svg` 数 ≥ 图数；`id="layer-*"` 匹配数 ≥ 2。

---

## 2. F-B 打击 Q3 / Q4 / Q5（图元 ↔ 源数据闭合）

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| **F-B1** | 图元无溯源（不知道来自哪一列哪一行） | 规则 R1 判定 | **不画该元素**；确有必要则虚线占位并在 `uncertainty` 说明原因 | `data_manifest.json` 该元素 `source`；`uncertainty` |
| **F-B2** | manifest 元素数与 SVG 数据图元数不等（应 1:1） | G3 | 修生成逻辑后重跑；**不得手改 manifest 迁就**（那会让核对失去意义） | `gates.G3` |
| **F-B3** | manifest 中的值与源表不符 | `mapcheck` **重读源表逐行核对**（容差 1e-9） | 定位列/行错位；**不得放宽容差** | `mapcheck_report.json` `mismatched` |
| **F-B4** | SVG 数据层出现 manifest 未登记的图元 | `mapcheck` 反向核对 | 补齐登记或删掉该图元 | `unmatched` |
| **F-B5** | 引用的列名在表中不存在 | 列画像；`mapcheck`（**注意 `spec_lint` 实测不查列存在性**） | 用画像修正列名；**禁止补造列** | `failed_figures` |
| **F-B6** | 数值与标题语义差 10 倍以上 | 无自动判据 | `warn` 保留原值并标可疑，**不"修正"** | `uncertainty`；`warnings` |
| **F-B7** | `filter` 条件无匹配行 | `apply_row_filter` | 报错并列出该列可用取值 | `failed_figures` |

> **F-B5 的补充（实测发现）**：`spec_lint.py` 对"未知图型"能拦住（`E1` exit 2），
> 但对"引用不存在的列"**实测返回 `SUMMARY: VALID`、exit 0**。两层兜底：
> ① 规格门之后核对 `extract.json` 的列画像；② G5 的 `mapcheck` 重读源表
> （列不存在必然 mismatch）。两层都不通过 → 按 `failed_figures` 处理。

---

## 3. F-C 打击 Q6（单位与量级）

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| **F-C1** | 轴标签无单位（源数据有单位） | `axis-units` | 从列名括号提取，或按源元数据补 unit | `validation.warnings` |
| **F-C2** | 补不到单位 | 同上 | 保留无单位标签 + 记 `warn`（**不编造单位**） | `validation` `warn` |
| **F-C3** | 刻度范围裁剪数据点 | `range-covers-data` | 重算范围并留 5% 余量 | `figure_meta.y_range` |

> Q6 判定：`case.json` 声明的每个 `unit` 都要在（SVG 文本 ∪ manifest JSON）中出现。

---

## 4. F-D 打击 Q7 / Q8（标注与图面）

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| **F-D1** | 有误差线但语义（SE/SD/CI）未记录 | 规则 R7 | 按源元数据写 semantics；源未标 → `uncertainty`（**不猜**） | `validation.json` |
| **F-D2** | 图例项与数据系列对不上 | `legend-mapping` | 自动对齐；无法对齐 → 修 spec 后重跑 | `validation` `fail` → **阻断 completed** |
| **F-D3** | 有星号没有线段（或反之） | `significance` | 修 `annotations` 使线段数 = 文字数 | `validation` `fail` |
| **F-D4** | 源未给 p 值却标了显著性 | 规则 R6 | **不画该标注**（不自行计算统计量） | `uncertainty` |
| **F-D5** | 刻度文字重叠 / 标签过长 | 字体实测 | 自动旋转 30° | `validation.adjustments` |
| **F-D6** | 图例或标注遮挡数据 | `occlusion`（真实字体包围盒测量） | 图例移出绘图区；网络图手给节点坐标；重跑后遮挡应降为 0 | `validation` `occlusion` warn |
| **F-D7** | PNG 中文出现方框 / 乱码 | `cjk-font` 校验 | SVG 回退链照常；PNG 记 `warn` | `environment.fonts`；`uncertainty` |
| **F-D8** | 网络关系引用未知节点 | `E8` + warnings | 不画该边并记录 warning | `validation.warnings` |
| **F-D9** | 留白后画布无绘图空间 | `compute_plot_area` | 报错并提示增大画布或减小边距 | `failed_figures` |
| **F-D10** | 多图中某一张失败 | 单图异常 | **不阻塞其他图**（`status=partial`） | `failed_figures` 记原因 |

> Q7/Q8 判定：误差线标记数 > 0 且语义出现在产物中；输出 SVG 数 ≥ 图数。

---

## 5. F-E 打击 Q9 / Q10 / Q11（结果信封与审计）

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| **F-E1** | 契约形态①的列表里混入非字符串项 | 逐项类型检查 | 跳过非法项，其余照常回显 | `output_contract_applied=true` + `uncertainty` |
| **F-E2** | 契约形态②/④ 声明了未知类型名 | `defaults` 查表未命中 | 按字符串容器给 `""`（**绝不 null**） | 同上 |
| **F-E3** | 契约声明了本 Skill 不产出的字段 | 别名表未命中 | **不做假映射**：给声明容器类型的空值 + 写明"该字段本 Skill 不产出" | `uncertainty` |
| **F-E4** | 完全没有 `output_contract` | `case.json` 无该键 | `output_contract_applied=false`；只写自有字段，**不臆造契约字段** | `output_contract_applied` |
| **F-E5** | 契约声明与产物不一致 | `check_contract` exit 1 | 列出 missing/null 字段；修复后重跑 | `check_contract` 报告 |
| **F-E6** | 源文件读不到 sha256 | G1 | 记 `uncertainty`；**不得留空或编造** | `sources[].sha256` |
| **F-E7** | 无人工修改记录 | 规则 R10 | 若确实无人工修改，保持空数组并说明；**不得编造记录** | `change_records` |
| **F-E8** | `status` 与产物事实不符（有 fail 却写 completed） | G8 | 强制降级为 `partial`；写明失败项 | `status`；`gates.G8` |

> Q9/Q10/Q11 判定：`result.json` 可解析且含六个核心键；`sources` 每条有非空 sha256；
> `change_records` 非空。

---

## 6. F-F 打击 Q12（确定性 —— 增益可验证性的地基）

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| **F-F1** | **PDF 两次运行字节不同** | `verify_rerun` / `artifacts_sha256` | **根因**：Pillow 写 PDF 注入当前时间戳（`/CreationDate`/`/ModDate`）→ PDF 字节变 → sha256 变 → `artifacts_sha256` 失去证据力。**处置**：`chartkit.stamp_pdf_deterministic()` 归一化这三个字段（含 `/ID`），`_adjust_xref_offsets()` 同步修正 xref 偏移。**本包已实现并实测通过** | `artifacts_sha256` 两次一致；`verify_rerun` `differ=0` |
| **F-F2** | 报告文件的 `dir` 字段不同 | 换输出目录重跑 | 属**环境变量**（两次运行目录不同）；判定时归一化（`verify_rerun` 已作此处理） | — |
| **F-F3** | 其他非时间戳差异（字典遍历序、浮点格式、把时间戳画进图） | `verify_rerun` 报差异 | 定位随机源并修掉；确实无法消除 → **如实记录差异**，不得用"看起来一样"搪塞 | `artifacts_sha256`；`change_records` |
| **F-F4** | Pillow 缺失 | `chartkit.HAS_PIL` | **保 SVG 与全部 JSON**；PNG/PDF 记缺失并写明安装方式 | `uncertainty`；`gates.G6` |
| **F-F5** | 只跑一次就宣称可复现 | 流程纪律 | **不允许**：Q12 要求每个条件各跑 2 次（`GAIN-PROTOCOL.md` §3 条件 F6） | — |

> Q12 判定：两次运行的产物逐个比较（`.json` 归一化、`.pdf` 抹时间戳、其余逐字节），
> 要求 `differ=0` 且 `identical>0`。

---

## 7. F-G 横切：材料、依赖与环境

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| **F-G1** | 材料文件不存在 | G1 盘点 | 不猜内容，明确列出缺失路径 | `status=partial`；`uncertainty` |
| **F-G2** | 材料存在但 0 行 / 空表 | `load_table` | 明示为空；该图不产出 | `failed_figures` |
| **F-G3** | 材料是扫描件 / 受保护 PDF | extract / 平台 pdf-text-tool | 先用平台工具转文本；仍不可读 → 说明工具与限制 | `uncertainty` |
| **F-G4** | 生物源材料表述含糊，实体无法确认 | 词表扫描命中 | 候选标 `uncertain=true`，对照原文确认后才上图 | `extract.json`；`uncertainty` |
| **F-G5** | 编码异常（CSV 乱码 / BOM） | `utf-8-sig` 读取 | 按 BOM 与 UTF-8 正确解码；确实乱码 → 降级 | `uncertainty` |
| **F-G6** | `case.json` 不可解析 / `--out` 不可写 | 入口 | 写**最小诚实信封**（实测 6 键） | `status=failed`；exit 1 |
| **F-G7** | `templates/journal_styles.json` 缺失或坏 JSON | `load_journal_styles()` | **回退内置默认样式**继续出图，不中断 | `environment.style`；`uncertainty` |
| **F-G8** | `templates/entity_glossary.json` 缺失 | `chartkit` 读取处 | 回退内置"关系类型→颜色/线型"默认表；词表扫描跳过 | `uncertainty` |
| **F-G9** | 字体目录不可读 / 无 CJK 字体 | `FontMap._scan` + `cjk-font` | SVG 回退链照常；PNG 记 warn；可用 `FONT_PATHS` 指定 | `environment.fonts` |
| **F-G10** | `scripts/` 不完整（被单独复制走） | `import` | 非零退出并打印缺失模块，**不产出半成品 result** | exit 1 |
| **F-G11** | 案例要求联网而环境无网络 | — | 本包零网络依赖；按 F-G1 记为材料缺失并降级，**不伪造数据** | `uncertainty` |
| **F-G12** | `task.md` 缺失，或与 `case.json` 冲突 | G1 | 以 `case.json` 的 `figures[]` 为执行依据；缺失记 `uncertainty`；冲突则记冲突并以 case 为准 | `uncertainty`；`change_records` |

---

## 8. 状态三态收敛（G8）

| `result.status` | 条件 | 说明 |
|-|-|-|
| `completed` | 全部图导出成功 ∧ 规格门无 error ∧ 校验六项无 `fail` ∧ G1–G8 全过 | 允许 `warn`，须在 `uncertainty` 说明 |
| `partial` | 任一条件不满足但仍有部分图 | `failed_figures` / `uncertainty` 写全 |
| `failed` | 无任何图产出 / 运行异常 | `error` + traceback 摘要；最小诚实信封 |

**四条禁止**：① 把失败写成完成；② 把 `warn` 写成"无问题"；③ 把材料缺失写成"有数据"；
④ 把契约字段缺失写成 `null`。

---

## 9. 复验路径（每条失败都有命令）

```bash
python "$SKILL_DIR/scripts/spec_lint.py"     --spec <case> --case <case>   # 规格门（F-B5 第一层）
python "$SKILL_DIR/scripts/extract.py"       --case <case> --out <work> --json  # 列画像（F-B5 第二层）
python "$SKILL_DIR/scripts/main.py"          --case <case> --out <out> --note "修复说明"
python "$SKILL_DIR/scripts/mapcheck.py"      --dir <out> --case <case>     # F-B
python "$SKILL_DIR/scripts/figcheck.py"      --dir <out> --case <case>     # F-A / F-D
python "$SKILL_DIR/scripts/verify_rerun.py"  --case <case> --out <out>     # F-F
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case>  # F-E
```

对照实验侧（F-F1 的原始证据）：
```bash
python "$SKILL_DIR/examples/measure_ab.py" --label B --case <case> --out $T/condB --run2 $T/condB2
```
