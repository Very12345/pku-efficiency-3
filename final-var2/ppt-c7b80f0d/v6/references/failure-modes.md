# failure-modes.md — 失败模式、降级策略与退出码语义

本文件是**可靠体验（10 分）**与**异常处理（3 分）**的落点。它把
"识别 → 处置 → 记录位置 → 退出码"四件事写成可执行约定；SKILL.md §6 的 D01–D18
决策规则与此处逐条对应。**任何降级都必须落进 `result.json`**，不允许静默继续。

> **本表不是自我声明，而是被实测过的**：`scripts/fault_inject.py` 按"输入 / 模板 /
> 依赖 / 契约 / 状态"五类形态注入 24 条真实故障，逐条测出**退出码 / status /
> uncertainty / 是否静默失败**，渲染成 `references/FAULT-MATRIX.md`。
> 改这里的任何一行，都要重跑那份演练——否则文档就会开始说假话。

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
| 模板文件不存在 / 空目录 / 案例未给模板（例如示例模板尚未由 `make_template.py` 生成） | 自动回退内置版式并继续（**这是正常分支，不是失败**，状态保持 `completed`）；若需要模板路径，先跑 `make_template.py` | `deck.template.kind = "builtin"` + `uncertainty[]` |
| 模板**损坏 / 半截 / 0 字节 / 老式 `.ppt`**（`Presentation()` 抛错） | 回退内置版式并继续；绝不改写 master 与页脚（**没打开过**模板，所以这条承诺天然成立）；状态降 `partial` | `deck.template.kind=builtin` + `deck.template.error` + `uncertainty[]` |
| 模板无 title/body/picture 占位符 | 按 `layout_hint` 名匹配 → 索引回退 → 内置版式；缺正文占位符时补画文本框（命名登记） | `deck.layouts_used` + `uncertainty[]` |
| 起始演示需替换（`template_mode = "replace"`） | 移除起始页仅保留版式/母版，**默认 `layouts` 不动起始页** | `deck.template.starter_slides_removed` |
| 页数超限 | 优先合并非证据页，**绝不静默丢弃证据页** | `deck.page_budget_met = false` + `change_records[]` + `uncertainty[]` |

### 2.3 依赖缺失（逐级回退，绝不假装成功）

| 依赖 | 缺失时的行为 | 记录位置 |
|-|-|-|
| `python-pptx` | 无法构建 deck：`deck` 为 `null`，`status=failed`（正式运行没有可交付物），如实说明——**不生成假文件**；**仍写出契约完整的 result.json** | `deck_error` + `uncertainty[]` + `status`；main.py → 1 |
| PDF 后端（fitz → pypdf → pdfplumber） | 逐级回退；全无则要求外部文本（见 2.1） | `run_meta.pdf_tools` + `sources[].tool` |
| `matplotlib` | 跳过重建图，保留引用与占位 | `run_meta.matplotlib_available=false` + `charts[].chart.reason` |
| `Pillow` | 预览渲染失败：`previews = []`，状态降 `partial` 并说明。**注意 python-pptx 自己依赖 Pillow**，所以"只缺 Pillow"在现实中通常就是"渲染栈整体缺失" ⇒ 实际走上一行 | `uncertainty[]` + `run_meta.rendered_with = "failed"`（若 deck 尚可构建） |
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

## 4. 检测能力边界（实测，2026-11-22）

上面每一条降级"应该"被记录下来——但**"被记录"和"被机器拦住"是两件事**。
`fault_inject.py` 的 24 条注入里有 3 条，产物**自身是自洽的**，静态校验器（G1–G8 +
`check_contract` 的字段覆盖）**拦不住**。我们把这 3 条写在文件里，而不是假装覆盖了：

| 缺口 | 注入 | 为什么脚本门拦不住 | 后果 |
|-|-|-|-|
| G1 不外联对照 | `CT-05` `case_id` 被改成与案例不一致的值 | G1 的实现只断言 result.json 自己的 `case_id` **非空**；"与 case 一致"只写在 `OUTPUT_CONTRACT.md` §5 的表里 | 一个错位的 `case_id` 会顺利交付 |
| 看不见历史状态 | `ST-01` 把真实的 `partial` 手改成 `completed` | 校验器读的是**这一刻的文件**，没有上一轮运行的状态可对比 | 伪造的成功状态会通过所有门 |
| 没有"应有留痕"基线 | `ST-02` 把降级后的 `uncertainty` 清空 | 清空后产物仍然自洽（`status=partial` 与 evidence 缺口并不矛盾） | 降级不留痕也能交付 |

**这三条不是"以后再说"** —— 它们各自有明确的人工兜底动作，见 §5。

## 5. 交付前必须手工确认的三件事

脚本门通过 **不等于** 诚实。下面三件事必须在交付前真的做一遍（每条一条命令）：

```bash
# ① case_id 与案例对拍（G1 覆盖不到的那一半）
python -c "import json,sys;a=json.load(open('result.json',encoding='utf-8'));b=json.load(open('case.json',encoding='utf-8'));print('OK' if a['case_id']==b['case_id'] else 'MISMATCH')"

# ② status=completed 的合法性：completed ⇒ 无 uncertainty 且无证据缺口
python -c "import json;r=json.load(open('result.json',encoding='utf-8'));print('OK' if r['status']!='completed' or (not r['uncertainty'] and not (r.get('evidence_mapping') or {}).get('gaps')) else 'INCONSISTENT')"

# ③ 有降级 ⇒ uncertainty 与 change_records 同时非空（不变量 I5）
python -c "import json;r=json.load(open('result.json',encoding='utf-8'));print('OK' if not r['uncertainty'] or r['change_records'] else 'MISSING RECORD')"
```

任何一条打印出 `MISMATCH` / `INCONSISTENT` / `MISSING RECORD`：**不要交付**，
回到 SKILL.md §6 的 D18 把记录补齐后重跑。

> 一句话总结这份文件的定位：**§1–§3 是我们承诺的行为，§4 是我们承认的边界，
> §5 是你必须亲手做的那三步。** 三者都写出来，这份可靠性声明才算完整。

---

## 6. 六条回退链（v3 的写法：逐级列明"先试什么、再试什么"）

### 六条回退链（逐级列明）

#### 链 A · 材料读取（M02 / M03 / M04）

| 级 | 手段 | 失败则 |
|-|-|-|
| 1 | `PyMuPDF(fitz)` 抽取文本 + 页内嵌图 | ↓ |
| 2 | `pypdf` | ↓ |
| 3 | `pdfplumber` | ↓ |
| 4 | 外部导出的 `.txt`（`main.py --materials`），工具如实记 | ↓ |
| **末级** | **标注不可读**：`status=failed`、`material_status=unreadable`、语义字段给类型空值；**不补造内容、不构建 deck** | — |

子分支：加密（先试空口令一次）；无文本层（标注"图像型 PDF"，**不做 OCR 冒充**）；
内容与标签不符（**以实际文件为准**，差异写进 sources）。

#### 链 B · 图片与图表（M09 / M10）

| 级 | 手段 | 失败则 |
|-|-|-|
| 1 | 论文原生图（页内嵌图抽取） | ↓ |
| 2 | 由表格数字**重建**图（PNG + 可编辑 SVG，`note=reconstructed_from_table`） | ↓ |
| 3 | **显式占位框** `figure-*-placeholder`（文案"需补齐，非原图"）+ `placed=null` | ↓ |
| **末级** | 空图位 + `uncertainty` 点名页；**绝不画示意图冒充数据**（机制 M4 的反面） | — |

#### 链 C · 模板适配（M06 / M07 / M08）

| 级 | 手段 | 失败则 |
|-|-|-|
| 1 | 组织方模板，**占位符级填充**（只填占位符、不碰 master、不覆盖页脚/配色） | ↓ |
| 2 | 按 `layout_hint` **名匹配** → 失败则**索引回退** | ↓ |
| 3 | 缺正文占位符 → **补画文本框**（必须登记命名，否则 K3 命名审计告警） | ↓ |
| 4 | **内置 16:9 学术版式**（`ACADEMIC_THEME`）；页数超限先合并非证据页 | ↓ |
| **末级** | `deck.template.kind="builtin"` + `uncertainty[]` 留痕；**绝不静默回退** | — |

#### 链 D · 字体与渲染（M12 / M13）

| 级 | 手段 | 失败则 |
|-|-|-|
| 1 | `soffice --headless --convert-to pdf` 产真 PDF，改写 `rendered_with` | ↓ |
| 2 | PIL 近似预览（`preview-approx-*.png`，三处标注近似） | ↓ |
| 3 | 系统 CJK 字体（`C:/Windows/Fonts` → `/System/Library/Fonts` → `/usr/share/fonts`） | ↓ |
| 4 | `SKILL_PREVIEW_FONT` 指定字体 | ↓ |
| **末级** | PIL 默认字体 / `previews=[]`；`run_meta.preview_font` 可为 `null`，**不得**把近似说成真实渲染 | — |

> `.pptx` 内的字体不依赖上述探测：主题 major/minor 注入 + run 级 latin/ea 双写
> （机制 M5）在**任何**预览字体情况下都会写。

#### 链 E · 契约回显（M14）

| 级 | 手段 | 失败则 |
|-|-|-|
| 1 | 有真实值 → 写真实值（语义字段 `title/main_claim/slides/render_state/notes_separated`） | ↓ |
| 2 | 无真实值 → 按容器类型给 `""` / `[]` / `{}` | ↓ |
| 3 | 未知字段 → `setdefault` 回显，**禁止 null** | ↓ |
| **末级** | `check_contract.py` 报缺失（exit 1）或契约文档解析不出（exit 2）；**不允许假通过** | — |

四形态对应：① 字段→类型提示 ② 字段→说明文本 ③ 布尔开关 ④ 字段清单（list of 名称）。
案例同时声明 `case_id` 时，与 result 顶层 `case_id` **逐字一致**（K3 的 G1）。

#### 链 F · 依赖缺失（M10 / M11 / M12）

| 依赖 | 缺失时的行为 | 记录 |
|-|-|-|
| `python-pptx` | `deck=null`、状态降级、**不生成假文件** | `deck_error` + `uncertainty[]` + `status` |
| PDF 后端 | 见链 A | `run_meta.pdf_tools` + `sources[].tool` |
| `matplotlib` | 跳过重建图 | `run_meta.matplotlib_available=false` + `charts[].chart.reason` |
| `Pillow` | `previews=[]` 并降级说明 | `uncertainty[]` + `rendered_with="failed"` |
| PowerPoint / LibreOffice | 见链 D 第 2 级 | `rendered_with` + `previews[].kind` |

## 7. 降级 ⇒ 哪项机制失效（v3 的诚实口径）

### 降级 ⇒ 哪项机制失效（对照 `MECHANISM.md` 的诚实口径）

引用增益数据时必须先看这张表：**某次运行降级了，就不该把该次算进"加载后的优势"。**

| 降级 | 失效的机制 / 断言 | 该在 `uncertainty[]` 里说什么 |
|-|-|-|
| 走链 A 末级（材料不可读） | M2/M3/M4/M6 全部无产物 | "本案例未产出可评估产物"——不得引用任何 GA 数字 |
| 走链 B 第 3 级（占位框） | M4 生效但内容缺失 | "第 N 页图位为占位框（非原图），证据定位仍保留" |
| 走链 C 第 4 级（内置版式） | M6 的 `named_shapes` 会升高（自建对象变多） | "模板不可用，回退内置版式"——这是记录项，**不是能力下降** |
| 页数超限合并 | M3 的 `evidence_rows` 会减少 | "为满足页数上限合并了 X 页，证据映射行数相应调整为 Y" |
| 链 F 缺 `python-pptx` | M2/M3/M4/M6 无法评估；M1 仍可成立 | "未产出 deck，仅契约完整" |
| 链 D 第 2 级（PIL 近似） | 不影响 M1–M6 | "预览为近似渲染，非 PowerPoint/LibreOffice 结果" |

**反例（禁止）**：某次因缺 `python-pptx` 没有产出 deck，却仍写"本次返工点 = 0" ——
没有 deck 的目录根本不会产生那份报告；这种引用是把"没测"说成"通过"。

---

> 三节的读法：§1–§3 是**承诺**，§4 是**承认的边界**，§5 是**你必须亲手做的三步**，
> §6–§7 是 union 进来的**机制视角**（哪一级回退失败时，坏掉的是哪项机制）。
> 完整机制清单见 `references/MECHANISM.md`，对照协议见 `references/GAIN-PROTOCOL.md`。
