# failure-modes.md — 失败分支处置手册（与决策规则 D01–D16 同号）

本文件是**可靠体验（10 分）· 异常处理（3 分）**的唯一落点，也是 `SKILL.md` §5
决策规则总表的**同号展开**：SKILL.md 给"四列速查"（触发 → 首选 → 降级 → 记录），
本文件给"五类展开"（识别特征 → 首选举措 → 升级路径 → 记录字段 → 退出码 → 反例）。
**两处编号必须一致**：新增或修改任一条，必须同时改两处；只改一处视为文档漂移。

> 阅读顺序建议：先看 §1 退出码语义（进程级），再看 §2 五类分支（业务级），
> 最后看 §3 逐级回退矩阵与 §4 不变量断言（交付级）。

## 1. 退出码语义（进程级契约，可被流水线直接判断）

| 脚本 | 0 | 1 | 2 | 3 |
|-|-|-|-|-|
| `scripts/main.py` | 端到端完成且 `run_meta.self_check.ok=true` | 产物已生成但 `self_check.ok=false`（存在未处置的问题） | 参数错误（argparse） | `case.json` 不存在 / 不可解析（仍会写出 `status=failed` 的 result.json） |
| `scripts/spec_lint.py` | `{"valid": true}` | `{"valid": false}` 且 `problems` 逐条列出 | 参数错误 | — |
| `scripts/export_check.py` | `{"valid": true}`（G1–G8 无 error） | `{"valid": false}` | 参数错误 | — |
| `scripts/check_contract.py` | 契约字段全部出现 | 有字段缺失（逐个列在 `missing`） | 参数错误 / 契约文档解析不出字段清单（**绝不假通过**） | — |
| `scripts/assetkit.py` | 抽取成功且 `text_chars > 0` | — | 抽取不完整（见 JSON 的 `status`/`errors`） | — |
| `scripts/make_template.py` | 模板已生成 | — | 无法生成（缺 python-pptx / 目录不可写） | — |
| `scripts/make_synthetic_inputs.py` | 至少生成一个夹具 | — | 一个都没生成（缺绘图/PDF 后端） | — |
| `scripts/deckgen.py` / `scripts/preview.py` | 打印 JSON 记录后退出 | — | — | — |

> `deckgen.py` / `preview.py` 的 CLI 只打印记录，失败以 JSON 字段（`error`/`reason`）表达，
> 不改变退出码；正式流程一律经 `main.py`，以 `self_check` 判定成败。

## 2. 五类失败分支（与 SKILL.md §6 分类表同序）

### 2.1 材料异常 → D02 / D03 / D04 / D09 / D10

| 识别特征 | 首选举措 | 升级路径 | 记录字段 | 退出码 |
|-|-|-|-|-|
| 材料路径不存在（`sources[].reason` 命中） | 不补造内容、不构建 deck，只产出元信息 result | 状态降 `failed`；契约语义字段按类型给 `""`/`[]` | `status=failed`、`material_status=unreadable`、`sources[].reason` | main.py → 0/1（以 self_check 为准） |
| PDF 报 encrypted | 先试空口令一次 | 改用外部导出的 `.txt`（`main.py --materials`），工具如实记 | `uncertainty[]` + `sources[].tool` | assetkit → 2 |
| PDF 无文本层（`text_chars = 0`） | 标注"图像型 PDF"，仍引用可抽取的图 | **不做 OCR 冒充**；必要时请用户补文本 | `uncertainty[]` + `sources[].tool` | assetkit → 2 |
| 无任何 PDF 库 | 用运行时自带读取转 `.txt` 后传入 | 仍不可读 → 按材料缺失（上一条）处置 | `run_meta.pdf_tools` + `uncertainty[]` | assetkit → 2 |
| 图/表抽不出（`images_extracted = 0`） | 该页保留**显式占位框**（文案注明"需补齐，非原图"） | 引用与定位照留；**绝不画示意图冒充数据** | `deck.figures[].placed=null` + `placeholder=true` + `uncertainty[]` | — |
| 重建图失败（无 matplotlib / 表格数据不全） | 跳过该图，保留表引用与原文数字 | 数字逐字取自原文，**绝不估算补齐** | `charts[].chart.reason`、`run_meta.matplotlib_available` | — |
| 材料存在但内容与标签不符 | **以实际文件为准**，不按标签补造 | 差异写入 sources 供复核 | `sources[]` + `uncertainty[]` | — |

> **反例（禁止）**：为了"看起来完整"而给缺失图补一张自绘图、或按案例标题想象论文内容。
> 这两类在本题判分中被明确列为"把示意图当实验数据 / 张冠李戴"。

### 2.2 模板缺失 / 不可用 / 占位符不足 → D06 / D07 / D08

| 识别特征 | 首选举措 | 升级路径 | 记录字段 |
|-|-|-|-|
| 案例未提供模板（`resolve_template → ("builtin", None)`） | 直接用内置 16:9 学术版式，页序与占位符规则不变 | 确实需要模板时跑 `make_template.py --out <dir>` 现场生成 | `deck.template.kind="builtin"` + `deck.template.guard` |
| 模板文件不存在（如示例模板尚未生成） | 自动回退内置版式并继续（**不是失败**） | 回退必须写 uncertainty，与 D07 承诺一致 | `deck.template.kind="builtin"` + `uncertainty[]` |
| 模板损坏 / 老式 `.ppt`（`Presentation()` 抛错） | 回退内置版式；**绝不改写 master 与页脚** | 记录原始异常串供诊断 | `deck.template.error` + `uncertainty[]` |
| 模板无 title/body/picture 占位符 | 按 `layout_hint` 名匹配 → 索引回退 → 内置版式；缺正文占位符时补画文本框并登记命名 | 补画对象必须进命名表，否则触发 C3 warnings | `deck.layouts_used` + `uncertainty[]` |
| 起始演示需替换（`template_mode="replace"`） | 移除起始页仅留版式/母版 | 默认 `"layouts"` 保留起始页 | `deck.template.starter_slides_removed` |
| 页数超限（D08） | 优先合并**非证据页**（封面/过渡/收尾） | **绝不静默丢弃证据页**；仍超限则如实标记 | `deck.page_budget_met=false` + `change_records[]` + `uncertainty[]` |

### 2.3 依赖缺失 → D10 / D11 / D12 / D13

| 依赖 | 缺失时的行为 | 升级顺序 | 记录字段 |
|-|-|-|-|
| `python-pptx` | 无法构建 deck：`deck=null`，状态 `partial`/`failed`——**不生成假文件** | 无替代；如实降级 | `deck_error` + `uncertainty[]` + `status` |
| PDF 后端 | 逐级回退 | `fitz` → `pypdf` → `pdfplumber` → 外部文本 | `run_meta.pdf_tools` + `sources[].tool` |
| `matplotlib` | 跳过重建图，保留引用与占位 | 无替代 | `run_meta.matplotlib_available=false` + `charts[].chart.reason` |
| `Pillow` | 预览渲染失败：`previews=[]`，状态降级并说明 | 无替代 | `uncertainty[]` + `run_meta.rendered_with="failed"` |
| 中文字体 | 降级到 PIL 默认字体继续预览 | `C:/Windows/Fonts` 的 msyh/simhei → `/System/Library/Fonts` → `/usr/share/fonts` 的 DejaVu/Noto → PIL 默认；可用 `SKILL_PREVIEW_FONT` 覆盖 | `run_meta.preview_font`（可为 `null`）+ `uncertainty[]` |
| PowerPoint / LibreOffice | 预览一律 `pil-approximation`，文件名带 `approx` | 检测到 `soffice` → 产真 PDF 并改写 `rendered_with` | `run_meta.rendered_with` + `previews[].kind` |

> 字体候选路径中的 `C:/Windows/Fonts` 是**跨平台探测逻辑的一部分**（不是某次运行的残留），
> 因此允许出现在包内；但**任何一次运行的真实绝对路径**不得写进示例 JSON。

### 2.4 契约四形态 → D15

| 形态 | case 声明示例 | result.json 处理 | 校验 |
|-|-|-|-|
| ① 字段 → 类型提示（dict） | `"title": "字符串"` | 有真实值写真实值；否则按容器给 `""`/`[]`/`{}` | G2（缺字段 = error，null = error）；`check_contract` 逐字段 |
| ② 字段 → 说明文本（dict） | `"render_state": "渲染记录"` | 语义可推断时写真实值，否则 `""` | 同上 |
| ③ 布尔开关 | `"notes_separated": true` | 回显真实布尔 | 同上 |
| ④ 字段清单（list） | `["title","slides"]` | 每个名称按 `""` 回显（可推断容器给 `[]`） | 同上 |
| 自定义 / 未知字段 | 任意 | 一律 `setdefault`，**禁止 null** | `result.output_contract` |
| 案例同时声明 `case_id` | `"case_id": "..."` | 与 result 顶层 `case_id` 逐字一致 | G1 |

### 2.5 状态一致性 → I1–I6 + D05 + D16

| 情形 | 规则（不变量） | 违反后果 |
|-|-|-|
| 材料不可读 | **I1**：禁止 `status=completed` | `export_check` 直接判 error |
| 有显式 `evidence_gap` 或图片仅占位框 | **I2**：`status ≤ partial`，`uncertainty` 点名页号 | C3 视为状态不一致 |
| C1 lint 有偏差仍继续构建 | **I3**：`status ≤ partial`，`spec_lint.problems` 与 `uncertainty` 同时保留 | 只留其一即违规 |
| 重建图被当作论文原图叙述 | **I4**：`charts[].chart.note` 声明 `reconstructed_from_table` 后不得称为原图 | 触发诚实性硬约束（`OUTPUT_CONTRACT.md` §4.1） |
| 任何一次降级 | **I5**：`uncertainty[]` 与 `change_records[]` 必须**同时**有对应条目 | `self_check.ok=false`，main.py → 1 |
| `uncertainty` 为空 | **I6**：仅当整链无降级；近似预览 ⇒ `rendered_with` 必须写明 | 需能在本次日志中举证 |

## 3. 逐级回退矩阵（一览）

| 能力 | 第 1 级 | 第 2 级 | 第 3 级 | 末级（如实降级） |
|-|-|-|-|-|
| PDF 文本 | PyMuPDF | pypdf | pdfplumber | 外部 `.txt` → 标注不可读 |
| PDF 图片 | 页内嵌图抽取 | 表格数字重建图 | 显式占位框 | 空图位 + uncertainty |
| 模板 | 组织方模板占位符填充 | 布局名 → 索引回退 | 补画文本框（登记命名） | 内置 16:9 学术版式 |
| 字体 | 系统 CJK 字体 | 系统拉丁字体 | `SKILL_PREVIEW_FONT` 指定 | PIL 默认字体 |
| 渲染 | LibreOffice → 真 PDF | — | — | PIL 近似预览（三处标注） |
| 契约字段 | 真实值 | 容器空值 | `setdefault` 回显 | `check_contract` 报缺失 |

## 4. 交付前最小自检（与 SKILL.md §8 清单一致）

```bash
python "$SKILL_DIR/scripts/spec_lint.py"    --spec   <work>/deck-spec.json          # C1
python "$SKILL_DIR/scripts/main.py"         --case /input/case.json \
  --task /input/task.md --spec <work>/deck-spec.json --out /app/output              # 端到端
python "$SKILL_DIR/scripts/export_check.py" --result /app/output/result.json \
  --out-dir /app/output --case /input/case.json                                     # C3 (G1–G8)
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md"                             # 契约字段全覆盖
```

四步中有任一步非 0 退出：先按 §2 对应条目处置并记录（含 D16 双写），再重跑；
**不得跳过记录直接交付**。
