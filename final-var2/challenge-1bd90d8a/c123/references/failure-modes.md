# failure-modes.md — 失败模式全表（按"破坏哪个机制"分组）

本文件是 `SKILL.md` §7 的完整版。分组依据不是错误类型，而是**它破坏四个机制中的哪一个**
（M1 三向闭合 / M2 声明式规格+生成门 / M3 单一场景双端输出 / M4 契约与确定性；
G-X 为横切）。这样分组的好处：分支表可以直接当**验收清单**用 ——
你担心哪个机制，就只看那一组。

每条格式：**触发条件 → 检出点 → 处置 → 落痕字段 → 复验命令**。

---

## 0. 分组总览

| 组 | 破坏的机制 | 条目 | 收敛到 |
|-|-|-|-|
| **G-M1** | 三向闭合（可回溯性） | 7 | `mapcheck_report.json` / `gates.G3·G4` |
| **G-M2** | 声明式规格 + 生成门 | 6 | `spec_lint.json` / `failed_figures` |
| **G-M3** | 单一场景双端输出（可编辑性） | 6 | `gates.G5·G6` / `validation.adjustments` |
| **G-M4** | 契约四形态 + 确定性 | 9 | `output_contract_applied` / `artifacts_sha256` / `status` |
| **G-X** | 横切：材料、依赖、环境 | 13 | `status` / 退出码 / `uncertainty` |

---

## 1. G-M1 破坏三向闭合（7 条）

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| **M1-F1** | 图元无溯源（不知来自哪一列哪一行） | 规则 M1-R1 判定 | **不画该元素**；确有必要则虚线占位并在 `uncertainty` 说明原因 | 该元素 `source` 字段；`uncertainty` |
| **M1-F2** | manifest 元素数与 SVG 数据图元数不等（应 1:1） | G3 | 修生成逻辑后重跑；**不得手改 manifest 迁就**（那样核对就失去意义） | `gates.G3` |
| **M1-F3** | manifest 里登记的 `svg_id` 在 SVG 中不存在 | `mapcheck` 正向核对 | 补齐 SVG 图元或删掉该登记项 | `mapcheck_report.json` |
| **M1-F4** | SVG 数据层出现 manifest 未登记的图元 | `mapcheck` 反向核对 | 补齐登记或删掉该图元 | `unmatched` 计数 |
| **M1-F5** | manifest 的值与**重读源表**得到的值不符 | `mapcheck`（容差 **1e-9**，不得放宽） | 定位列/行错位；修正生成逻辑 | `mismatched` 计数 |
| **M1-F6** | 引用的列名在源表中不存在 | 列画像；`mapcheck`（**`spec_lint` 实测不查列存在性**） | 用画像修正列名；**禁止补造列** | `failed_figures` |
| **M1-F7** | 实体/关系无来源（无 `cite`） | 规则 M1-R5 + 抽取阶段 | 候选标 `uncertain=true`，对照原文确认后才上图 | `extract.json.uncertain`；`uncertainty` |

**复验**：
```bash
python "$SKILL_DIR/scripts/mapcheck.py" --dir <out> --case <case.json>
# 期望：SUMMARY: ALL PASS (121 checked / 0 mismatched / 0 unmatched)
grep -o 'data-column="[^"]*" data-row-index="[0-9]*" data-value="[^"]*"' <out>/figure-*.svg | head -1
# 用该 column/row_index 回源表取值，应逐位相同（容差 1e-9）
```

---

## 2. G-M2 破坏声明式规格与生成门（6 条）

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| **M2-F1** | 使用了不受支持的图型 | `spec_lint` E1 | 改用受支持图型（`auto`/`bar`/`box`/`heatmap`/`line`/`network`/`panel`/`pie`/`scatter`）；**门不过不进生成** | `spec_lint.errors`；exit 2 |
| **M2-F2** | 规格缺必需字段（`id` / `type` / 数据引用） | `spec_lint` | 补齐后重跑；**不得靠渲染时兜底** | `spec_lint.errors` |
| **M2-F3** | `x`/`y` 列引用错（指向不存在的列） | 列画像（**门不拦这一项，见下**） | 用 `extract.json` 的列画像修正；`mapcheck` 会二次兜底 | `failed_figures` |
| **M2-F4** | 误差线语义未声明 | `spec_lint` E4 | 按源元数据写 `error.semantics`；源未标 → `uncertainty`（**不猜**） | `uncertainty` |
| **M2-F5** | 显著性标注缺锚点或来源 | `spec_lint` | 补 `annotations` 的 `from`/`to`/`p`/`source`；**源未给 p 值就不画** | `spec_lint.errors`；`uncertainty` |
| **M2-F6** | 网络关系引用了未知节点 | `spec_lint` E8 | 不画该边并记 warning（或补节点） | `validation.warnings` |

> **重要边界（实测，不掩饰）**：`spec_lint.py` 能拦住 **M2-F1**（未知图型，exit 2），
> 但**拦不住 M2-F3**（引用了不存在的列 —— 实测返回 `SUMMARY: VALID (0 errors /
> 0 warnings / 1 figures)`、exit 0）。因此"生成门"不是唯一防线：
> 真实兜底是 **G-M1 的 `mapcheck`**（列不存在必然 mismatch）。
> 这条边界同时写在 `TEST.md` 的未解决项与 `MECHANISM.md` §2.5。

**复验**：
```bash
python "$SKILL_DIR/scripts/spec_lint.py" --spec <case> --case <case>   # exit 0 = 可进生成
echo '{"figures":[{"id":"x","type":"waterfall"}]}' > /tmp/bad.json
python "$SKILL_DIR/scripts/spec_lint.py" --spec /tmp/bad.json          # exit 2, [ERROR] E1
```

---

## 3. G-M3 破坏"单一场景双端输出"（6 条）

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| **M3-F1** | SVG 扁平、无分层 `layer-*` 组 | G5 `layers` | 用本包管线重生成（**不得手改 SVG 补层**） | `gates.G5` |
| **M3-F2** | SVG 无 `metadata` 溯源块 | G5 `provenance` | 同上 | `gates.G5` |
| **M3-F3** | 文字被转曲（变成 `<path>`） | G5 `real_text` | 重新生成；**编辑器保存时勿选"转曲/轮廓化"** | `gates.G5` |
| **M3-F4** | SVG 含 `DOCTYPE` / 外部实体（XXE） | G5 `no_xxe` | **拒绝生成含外部实体的产物** | `gates.G5` |
| **M3-F5** | PNG 打不开 / 空文件；或 PDF 不以 `%PDF` 开头 | G6 `open`+`verify` / `%PDF` 头 | 查 Pillow 与路径；缺失时**先保 SVG 与全部 JSON**；重渲染后仍失败则跳过该预览并警告 | `gates.G6`；`uncertainty` |
| **M3-F6** | 留白后画布无绘图空间；或标签过长/遮挡 | `compute_plot_area`；字体实测；`occlusion` | 报错提示增大画布/减小边距；标签自动旋转 30°；图例移出绘图区；网络图手给节点坐标 | `failed_figures`；`validation.adjustments` |

**复验**：
```bash
python "$SKILL_DIR/scripts/figcheck.py" --dir <out> --case <case.json>   # G5/G6
grep -c '<text' <out>/figure-fig-01.svg              # > 0 → 文字仍是文本
grep -o 'id="layer-[a-z]*"' <out>/figure-fig-01.svg | sort -u
```

---

## 4. G-M4 破坏契约四形态与确定性（9 条）

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| **M4-F1** | 契约形态①（字段名列表）里混入非字符串项 | 逐项类型检查 | 跳过非法项，其余照常回显 | `output_contract_applied=true` + `uncertainty` |
| **M4-F2** | 契约形态②/④ 声明了未知类型名（如 `"datetime"`） | `defaults` 查表未命中 | 按字符串容器给 `""`（**绝不 `null`**） | 同上 |
| **M4-F3** | 契约声明了本 Skill 不产出的字段（如 `regression_stats`） | 别名表未命中 | **不做假映射**：给声明容器类型的空值 + 写明"该字段本 Skill 不产出" | `uncertainty` |
| **M4-F4** | 完全没有 `output_contract` | `case.json` 无该键 | `output_contract_applied=false`；只写自有字段，**不臆造契约字段** | `output_contract_applied` |
| **M4-F5** | 契约声明与产物不一致（声明 `editable_source` 却没出 SVG） | `check_contract` | exit 1 并列出 missing/null 字段；修复后重跑 | `check_contract` 报告 |
| **M4-F6** | **PDF 两次运行字节不同** | `verify_rerun` / `artifacts_sha256` | 见下方专节 —— 元数据时间戳归一化 | `artifacts_sha256` 两次一致 |
| **M4-F7** | 报告文件的 `dir` 字段不同 | 换输出目录重跑 | 属**环境变量**（两次运行目录不同），判定时归一化；`verify_rerun` 已作此处理 | — |
| **M4-F8** | 其他非时间戳差异（字典遍历序、浮点格式、把时间戳画进图） | `verify_rerun` 报差异 | 定位随机源并修掉；确实无法消除 → **如实记录**，不得用"看起来一样"搪塞 | `artifacts_sha256`；`change_records` |
| **M4-F9** | `status` 与产物事实不符（有 `fail` 却写 `completed`） | G8 | 强制降级为 `partial`（或无图 → `failed`）并写明失败项 | `status`；`gates.G8` |

### 4.1 M4-F6 专节：PDF 时间戳（本包最有说服力的一条实测）

**症状**：同一输入两次运行，`figure-*.pdf` 的 `sha256` 不同 →
`result.json.artifacts_sha256` 的 pdf 条目跟着变 → `verify_rerun` 报差异。

**根因（实测定位，不是推测）**：Pillow 写 PDF 时注入当前时间戳 ——
`/CreationDate (D:20261122095608Z)`、`/ModDate (D:20261122095608Z)`。
用 `cmp -l` 比较两份 PDF，**仅差 4 个字节**，全部落在时间戳上：

```
VAL /artifacts_sha256/figure-fig-01.pdf  bf7470b4…6ce  !=  a2174efe…110
VAL /artifacts_sha256/figure-fig-02.pdf  376fb81f…c3d  !=  3b6c3420…e9d
# cmp -l condB/figure-fig-01.pdf condB2/figure-fig-01.pdf | wc -l   → 4
```

**处置**：

| 函数 | 作用 |
|-|-|
| `chartkit.stamp_pdf_deterministic(pdf_path)` | 把 `/CreationDate`、`/ModDate`、`/ID` 就地替换为固定值；**只改元数据字节，不改页面内容** |
| `chartkit._adjust_xref_offsets(b, old_len, new_len)` | 元数据长度变化时，同步修正交叉引用表中指向新位置的对象字节偏移 |

调用点：`png_to_pdf()` 在 `page.save(...)` 之后调用 `stamp_pdf_deterministic(pdf_path)`。

**修复前后对照（逐文件实测）**：

| 产物 | 修复前 | 修复后 |
|-|-|-|
| `figure-fig-01.pdf` / `figure-fig-02.pdf` | DIFF（4 字节） | **SAME** |
| `figure-fig-01/02.svg` / `.png` | SAME | SAME |
| `data_manifest.json` / `validation.json` | SAME | SAME |
| `figcheck_report.json` / `mapcheck_report.json` | DIFF（仅 `dir`） | DIFF（仅 `dir`，属环境变量） |
| `result.json` | DIFF（`dir`/`steps`/`change_records` + 两个 pdf sha） | DIFF（仅 `dir`/`steps`/`change_records`） |

**独立复核**：

| 检查 | 结果 |
|-|-|
| `verify_rerun.py` | `SUMMARY: DETERMINISTIC (identical=9 differ=0 missing=0)`，exit 0 |
| 两次运行 PDF 的 sha256 | `figure-fig-01.pdf` = `079e25da602210c5…`；`figure-fig-02.pdf` = `0dad9ca7ab18c094…` |
| PDF 文件大小 | 343392 B → **343392 B**（新旧时间戳等长） |
| `pypdf` 解析 | 1 页；`/CreationDate = D:20000101000000Z`、`/ModDate` 同值 |
| `PIL.Image.open()` | 修复前**与**修复后均 `cannot identify image file`（Pillow 栅格化 PDF 需 Ghostscript）⇒ **既有行为，未引入退化** |

**为什么这条必须归到 M4**：它直接决定 `sha256` 能不能当证据 ——
这正是机制四存在的全部理由。没有归一化，"同输入可复现"就只是一句承诺。

---

## 5. G-X 横切：材料、依赖与环境（13 条）

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| **X-F1** | 材料文件不存在 | E1 盘点 | 不猜内容；明确列出缺失路径 | `status=partial`；`uncertainty` |
| **X-F2** | 材料存在但 0 行 / 空表 | `load_table` | 明示为空；该图不产出 | `failed_figures` |
| **X-F3** | 材料是扫描件 / 受保护 PDF，无法直接抽取 | extract / 平台 pdf-text-tool | 先用平台工具转文本；仍不可读 → 说明工具与限制 | `uncertainty`（含所用工具） |
| **X-F4** | 生物源材料表述含糊，实体无法确认 | 词表扫描命中 | 候选标 `uncertain=true`，对照原文确认后才上图 | `extract.json`；`uncertainty` |
| **X-F5** | 编码异常（CSV 乱码 / BOM） | `utf-8-sig` 读取 | 按 BOM 与 UTF-8 正确解码；确实乱码 → 降级 | `uncertainty` |
| **X-F6** | `case.json` 不可解析 / `--out` 不可写 | 入口 | 写**最小诚实信封**（实测 6 键：`case_id`/`status`/`error`/`uncertainty`/`sources`/`change_records`） | `status=failed`；exit 1 |
| **X-F7** | `templates/journal_styles.json` 缺失或坏 JSON | `chartkit.load_journal_styles()` | **回退内置默认样式**继续出图，不中断 | `environment.style`；`uncertainty` |
| **X-F8** | `templates/entity_glossary.json` 缺失 | `chartkit` 读取处 | 回退内置"关系类型→颜色/线型"默认表；词表扫描跳过 | `uncertainty` |
| **X-F9** | `templates/figure_map.schema.json` 缺失 | 仅文档/人读用途 | 脚本不依赖该文件；lint 仍按内置规则跑 | —（非运行故障） |
| **X-F10** | 字体目录不可读 / 无 CJK 字体 | `FontMap._scan` + `cjk-font` 检查 | SVG 回退链照常；PNG 记 warn；可用 `FONT_PATHS` 指定 | `environment.fonts`；`uncertainty` |
| **X-F11** | Pillow 缺失 | `chartkit.HAS_PIL` | **保 SVG 与全部 JSON**；PNG/PDF 记缺失并写明 `pip install Pillow` | `uncertainty`；`gates.G6` |
| **X-F12** | `scripts/` 不完整（被单独复制走） | `import` | 非零退出并打印缺失模块，**不产出半成品 result** | exit 1 |
| **X-F13** | `task.md` 缺失，或与 `case.json` 冲突；或案例要求联网而环境无网络 | E1 | 以 `case.json` 的 `figures[]` 为执行依据；缺失记 `uncertainty`；冲突记冲突并以 case 为准；无网络则按 X-F1 处理，**不伪造数据** | `uncertainty`；`change_records` |

---

## 6. 状态三态收敛（G8）

| `result.status` | 条件 | 说明 |
|-|-|-|
| `completed` | 全部图导出成功 ∧ 生成门无 error ∧ 校验六项无 `fail` ∧ G1–G8 全过 | 允许 `warn`，须在 `uncertainty` 说明 |
| `partial` | 任一条件不满足但仍有部分图 | `failed_figures` / `uncertainty` 写全 |
| `failed` | 无任何图产出 / 运行异常 | `error` + traceback 摘要；最小诚实信封 |

**四条禁止**：① 把失败写成完成；② 把 `warn` 写成"无问题"；③ 把材料缺失写成"有数据"；
④ 把契约字段缺失写成 `null`（应给声明容器类型的空值）。

---

## 7. 复验路径（按机制分组）

```bash
S="$SKILL_DIR"
# 机制 M2（生成门）
python "$S/scripts/spec_lint.py"     --spec <case> --case <case>
# 机制 M1（三向闭合；也是 M2-F3 的兜底）
python "$S/scripts/extract.py"       --case <case> --out <work> --json
python "$S/scripts/mapcheck.py"      --dir <out> --case <case>
# 机制 M3（可编辑性）
python "$S/scripts/figcheck.py"      --dir <out> --case <case>
# 机制 M4②（确定性）
python "$S/scripts/verify_rerun.py"  --case <case> --out <out>
# 机制 M4①（契约落地）
python "$S/scripts/check_contract.py" --result <out>/result.json --case <case>
# 修复后重跑
python "$S/scripts/main.py"          --case <case> --out <out> --note "修复说明"
```
