# failure-modes.md — 失败模式、降级策略与退出码语义

本文件是**可靠体验（10 分）**与**异常处理（3 分）**的落点。它把
"识别 → 处置 → 记录位置 → 退出码"四件事写成可执行约定；SKILL.md §5 的 L01–L12
（其中 L06/L07/L08/L10/L11 与本文档沿用的 D 编号一一对应，见 SKILL.md §5 末注）
决策规则与此处逐条对应。**任何降级都必须落进 `result.json`**，不允许静默继续。

## 1. 退出码语义（统一约定，脚本可被流水线判断）

| 脚本 | 0 | 1 | 2 | 3 |
|-|-|-|-|-|
| `scripts/main.py` | 端到端完成且自检无 error | 产物已生成但 `run_meta.self_check.ok=false`（errors 非空） | 参数错误（argparse） | `case.json` 不存在或不可解析（后者仍会写出 `status=failed` 的 result.json） |
| `scripts/spec_lint.py` | `{"valid": true}` | `{"valid": false}` 且 problems 列出 | 参数错误 | — |
| `scripts/export_check.py` | `{"valid": true}`（G1–G8 无 error） | `{"valid": false}` | 参数错误 | — |
| `scripts/check_contract.py` | 契约字段全部出现 | 有字段缺失（逐个列出） | 参数错误 / 契约文档解析不出字段清单 | — |
| `scripts/assetkit.py` | 抽取成功且 `text_chars > 0` | — | 抽取不完整（见 JSON 的 `status`/`errors`） | — |
| `scripts/make_template.py` | 模板已生成 | — | 无法生成（缺 python-pptx 或目录不可写） | — |
| `scripts/make_synthetic_inputs.py` | 至少生成一个夹具 | — | 一个都没能生成（缺绘图/PDF 后端） | — |
| `scripts/deckgen.py` / `scripts/preview.py` | 打印 JSON 记录后退出 | — | — | — |

> `deckgen.py` / `preview.py` 的 CLI 只做"打印记录"，其失败以 JSON 字段
> （`error` / `reason`）表达而不改变退出码；正式流程一律经 `main.py`（用 `self_check` 判定）。

## 2. 五类失败模式逐条处置

### 2.1 材料异常（材料缺失 / 加密 / 扫描件 / 图片抽不出）

| 识别 | 处置 | 记录位置 | 退出码 |
|-|-|-|-|
| case 指向的文件不存在（`sources[].path = null`） | 不补造内容；不构建 deck；产出仅含元信息的 result | `status=failed`、`material_status=unreadable`、`sources[].reason` | main.py → 0 或 1（以 self_check 为准），**绝不写 completed** |
| PDF 加密（`failed_pdf_encrypted`） | 先试空口令一次；失败则改用外部读取的 `.txt`，如实说明 | `uncertainty[]` + `sources[].tool`；状态降 `partial`/`failed` | assetkit → 2 |
| PDF 无文本层（扫描件，`text_chars = 0`） | **不做 OCR 冒充**；标注"图像型 PDF"；有图仍可引用；必要时请用户补文本 | `uncertainty[]`（含 `sources[].tool`） | assetkit → 2 |
| 无任何 PDF 库（`failed_no_pdf_library`） | 用运行时自带 PDF 读取转 `.txt` 后传入（`--materials`）；仍不可读 → 按材料缺失处理 | `run_meta.pdf_tools` + `uncertainty[]` | assetkit → 2 |
| 图/表抽不出（`images_extracted = 0`） | 该页保留**显式占位框**（文案注明"需补齐，非原图"），绝不画示意图冒充数据 | `deck.figures[].placed = null` + `placeholder = true` + `uncertainty[]` | — |
| 重建图失败（无 matplotlib / 数据不全） | 跳过图，保留引用与占位 | `charts[].chart.reason` + `uncertainty[]` | — |
| 材料存在但内容与标签不符 | **以实际文件为准**，不按标签补造；差异写入 sources | `sources[]` + `uncertainty[]` | — |

### 2.2 模板缺失 / 不可用 / 占位符不足

| 识别 | 处置 | 记录位置 |
|-|-|-|
| 案例未提供模板（`resolve_template → ("builtin", None)`） | 使用内置 16:9 学术版式（`ACADEMIC_THEME`），页面顺序与占位符规则不变 | `deck.template.kind = "builtin"` + `deck.template.guard` |
| 模板文件不存在（例如示例模板尚未由 `make_template.py` 生成） | 自动回退内置版式并继续（**不是失败**）；若需要模板路径，先跑 `make_template.py` | `deck.template.kind = "builtin"` + `uncertainty[]` |
| 模板损坏 / 老式 `.ppt`（`Presentation()` 抛错） | 回退内置版式；绝不改写 master 与页脚 | `deck.template.error` + `uncertainty[]` |
| 模板无 title/body/picture 占位符 | 按 `layout_hint` 名匹配 → 索引回退 → 内置版式；缺正文占位符时补画文本框（命名登记） | `deck.layouts_used` + `uncertainty[]` |
| 起始演示需替换（`template_mode = "replace"`） | 移除起始页仅保留版式/母版，**默认 `layouts` 不动起始页** | `deck.template.starter_slides_removed` |
| 页数超限 | 优先合并非证据页，**绝不静默丢弃证据页** | `deck.page_budget_met = false` + `change_records[]` + `uncertainty[]` |

### 2.3 依赖缺失（**逐库实测**，绝不假装成功）

> 本节在 v9 中按 `scripts/degrade_probe.py` 的实测结果**重写**（8 个场景，原始记录见
> `references/degrade-matrix-data.json`，报告见 `references/DEGRADE-MATRIX.md`）。
> **两处原文档承诺与实测不符，已更正**：
> ① 原文写 `python-pptx` 缺失时"`deck` 为 null、状态 `partial`/`failed`"，
> ② 原文写 `Pillow` 缺失时"`previews = []`、状态降级" ——
> 实测两者都**在导入期就失败**（`scripts/deckgen.py` / `scripts/ooxml_kit.py` / `scripts/preview.py`
> 是模块级导入），进程连 `result.json` 都写不出来，因此**根本走不到"记录降级"的那段代码**。
> 把这两条写成"优雅降级"是不准确的；准确说法是"端到端不可用"。

| 依赖 | **实测**行为（`degrade_probe.py` 场景） | 产物还剩什么 | 记录位置 |
|-|-|-|-|
| `python-pptx`（含其 Pillow 依赖） | **导入期 `ModuleNotFoundError`，exit 1，0 个产物、无 `result.json`**（S1；屏蔽 PIL 时 S2 同样如此，因为 pptx 内部导入 PIL） | **什么都没有** | 无（进程在产出任何评分产物前结束）；工具级入口 `make_template.py` 例外：exit 2 + `status=unavailable` |
| `matplotlib`（或它依赖的 `numpy`） | 继续跑完：**exit 0、11 个产物**，重建图跳过（`charts` 记录仍在但 `chart-*.png/svg` 不落盘） | `result.json` + deck + 7 张预览 + 证据映射，**少 2 个 chart 文件** | `uncertainty[]`（`reconstructed chart skipped: matplotlib missing: …`）+ `charts[].chart.reason` |
| `PyYAML` | **无影响**：实测与基线逐项一致（13 个产物）——管线里没有任何 `yaml` 导入 | 全部 13 个 | 无需记录（它不是本 Skill 的依赖） |
| PDF 后端（fitz → pypdf → pdfplumber） | 逐级回退；全无则要求外部文本（见 2.1）。**未纳入矩阵实测**（示例材料是纯文本） | 取决于案例材料 | `run_meta.pdf_tools` + `sources[].tool` |
| 中文字体（Windows msyh/simhei ≻ Linux DejaVu/Noto ≻ PIL 默认） | 降级到 PIL 默认字体继续预览；deck 内仍写主题字体 + run 级 latin/ea 双写以缓解换机替换 | 全部（预览字形变化） | `run_meta.preview_font`（可能是 `null`）+ `uncertainty[]` |
| PowerPoint / LibreOffice | **实测无影响**（S7）：把 `soffice` 从 PATH 剥离后 exit/status/产物与基线一致；静态扫描 11 个管线脚本 **0 处调用** `soffice` | 全部 13 个 | `run_meta.rendered_with` + 每条 `previews[].kind`（恒为 `pil-approximation`） |

**探针怎么复跑**（约 32 s；只想看硬依赖时用 `--only`，约 10 s）：

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" --out <dir> --emit-md <dir>/DEGRADE-MATRIX.md
python "$SKILL_DIR/scripts/degrade_probe.py" --out <dir> --only S0-baseline,S1-no-pptx,S2-no-PIL
```

**判定口径**：`full success` / `honest partial/failed` / `crash (no result.json)` /
**`silent degradation`**（自称 `completed` 但 deck 或预览已残缺 → 探针退出码 1，必须处理）。
实测本包 **0 条静默降级**、3 条 crash（都是"无产物"的响亮失败）。

### 2.4 契约四形态（`output_contract` 回显）

| 形态 | 处理 | 记录/校验 |
|-|-|-|
| ① 字段 → 类型提示 | 有真实值写真实值；否则按容器类型给 `""` / `[]` / `{}` | `export_check` G2（缺字段=error，null=error）；`check_contract` 逐字段核对 |
| ② 字段 → 说明文本 | 同上，语义可推断时写真实值 | 同上 |
| ③ 布尔开关 | 回显真实布尔（如 `notes_separated`） | 同上 |
| ④ 字段清单（list） | 每个名称按 `""`（可推断容器给 `[]`）回显 | 同上 |
| 自定义/未知字段 | 一律 `setdefault`，**禁止 null** | `result.output_contract` |
| 案例同时声明 `case_id` | 与 result 顶层 `case_id` 逐字一致 | `export_check` G1 |

### 2.5 状态一致性（status / uncertainty / change_records 三者不得互相矛盾）

| 情形 | 规则 |
|-|-|
| 材料不可读 | **禁止** `status=completed`（`export_check` 直接判 error） |
| 有显式 `evidence_gap` 或图片只有占位框 | 状态必须 ≤ `partial`，并在 `uncertainty[]` 点名页 |
| CP1 lint 有偏差 | 先修 spec；确无法满足案例硬约束时按 D4 继续构建，状态降 `partial` 且 `spec_lint.problems` 与 `uncertainty` 同时保留 |
| 任何一次降级 | 必须同时出现在 `uncertainty[]`（发生了什么+影响）与 `change_records[]`（何时+为什么） |
| `uncertainty` 为空 | 只有当整条链路无任何降级时才允许；不得"为好看"清空 |
| 预览为近似 | `previews[].kind` 必须为 `pil-approximation`，`run_meta.rendered_with` 必须写明 |
| 脚本自检 | `run_meta.self_check = {ok, problems}`；`ok=false` 时 main.py 退出码为 1 |

## 3. 交付前最小自检（与 SKILL.md §7 清单一致）

```bash
python "$SKILL_DIR/scripts/spec_lint.py"   --spec   <work>/deck-spec.json          # CP1
python "$SKILL_DIR/scripts/main.py"        --case /input/case.json \
  --task /input/task.md --spec <work>/deck-spec.json --out /app/output             # 端到端
python "$SKILL_DIR/scripts/export_check.py" --result /app/output/result.json \
  --out-dir /app/output --case /input/case.json                                     # CP3 (G1–G8)
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md"                             # 契约字段全覆盖
python "$SKILL_DIR/scripts/degrade_probe.py" --out <tmp>/dg   # 依赖降级矩阵：静默降级 0 条才 exit 0
```

五步中有任一步非 0 退出：先按 §2 对应条目处置并记录，再重跑；**不得跳过记录直接交付**。
