# failure-modes.md — 失败模式、降级策略与退出码语义

本文件是**可靠体验（10 分）**与**异常处理（3 分）**的落点。它把
"识别 → 处置 → 记录位置 → 退出码"四件事写成可执行约定；SKILL.md §5 的 D1–D11
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

### 2.3 依赖缺失（逐级回退，绝不假装成功）

| 依赖 | 缺失时的行为 | 记录位置 |
|-|-|-|
| `python-pptx` | 无法构建 deck：`deck` 为 `null`，状态 `partial`/`failed`，如实说明——**不生成假文件** | `deck_error` + `uncertainty[]` + `status` |
| PDF 后端（fitz → pypdf → pdfplumber） | 逐级回退；全无则要求外部文本（见 2.1） | `run_meta.pdf_tools` + `sources[].tool` |
| `matplotlib` | 跳过重建图，保留引用与占位 | `run_meta.matplotlib_available=false` + `charts[].chart.reason` |
| `Pillow` | 预览渲染失败：`previews = []`，状态降级并说明 | `uncertainty[]` + `run_meta.rendered_with = "failed"` |
| 中文字体（Windows msyh/simhei ≻ Linux DejaVu/Noto ≻ PIL 默认） | 降级到 PIL 默认字体继续预览；deck 内仍写主题字体 + run 级 latin/ea 双写以缓解换机替换 | `run_meta.preview_font`（可能是 `null`）+ `uncertainty[]` |
| PowerPoint / LibreOffice | 预览一律 `pil-approximation`，文件名带 `approx`，从不冒充真实渲染 | `run_meta.rendered_with` + 每条 `previews[].kind` |

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
```

四步中有任一步非 0 退出：先按 §2 对应条目处置并记录，再重跑；**不得跳过记录直接交付**。

---

## 4. 题集演练：另一类失败（产物结构正确，但内容悄悄没了）

`references/CASE-SET.md` 记录了一类**注入覆盖不到**的失败：产物能被正常打开、
`export_check` 全绿、`status=completed`，**但某一页的文字根本不在幻灯片里**。

| 现象（实测） | 根因 | 现在的行为 |
|-|-|-|
| μ 子案例第一轮：`90.8`、`88.6` 两个透射率在产物里**搜不到** | `layout_hint="figure"` → `Picture with Caption` 的 idx 1 是**图片框**；bullets 先写进它、插图像再覆盖它 | 跳过图片占位符；图文同页时正文走左半幅（D19）；自查清单要求"能在 deck XML 里搜到该页数字" |

**为什么它值得单列**：这类失败**不会**触发任何退出码、也不会写 uncertainty——
它只会在"逐字一致性检查"面前现形。因此本包的验收区间里
`must_keep_verbatim` 用的是**产物文字**（deck 全部文本框 + 备注 + 证据表），
而不是 spec、也不是 `result.json`。

## 5. 检测能力边界与人工兜底

脚本门（G1–G8 + 字段覆盖）是**静态产物校验器**：它看不到历史状态、不外联案例文件。
以下三件事必须由交付者手工确认（每件一条命令）：

```bash
python -c "import json;a=json.load(open('result.json',encoding='utf-8'));b=json.load(open('case.json',encoding='utf-8'));print('OK' if a['case_id']==b['case_id'] else 'MISMATCH')"
python -c "import json;r=json.load(open('result.json',encoding='utf-8'));print('OK' if r['status']!='completed' or (not r['uncertainty'] and not (r.get('evidence_mapping') or {}).get('gaps')) else 'INCONSISTENT')"
python -c "import json;r=json.load(open('result.json',encoding='utf-8'));print('OK' if not r['uncertainty'] or r['change_records'] else 'MISSING RECORD')"
```

三件分别是：`case_id` 与案例对拍（G1 只查非空）、`status=completed` 的合法性
（伪造状态拦不住）、降级必有留痕（清空 uncertainty 拦不住）。
打印出 `MISMATCH`/`INCONSISTENT`/`MISSING RECORD` 时**不要交付**。
