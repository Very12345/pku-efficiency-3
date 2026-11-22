# failure-modes.md — 回退链手册（与机制触发规则 M01–M14 同号）

本文件是 **可靠体验（10 分）· 异常处理（3 分）** 的落点，也是 `SKILL.md` §5 的同号展开。
与其他写法不同，这里**按"回退链"组织**：每一条链都有明确的第 1 级、第 2 级、……
末级是"如实降级"。原因很直接 —— 本包的机制（见 `references/MECHANISM.md`）
大多是**逐级回退**型设计，按层级写才能一眼看出"哪一级用完了会掉到哪"。

## 1. 退出码语义（进程级契约）

| 脚本 | 0 | 1 | 2 | 3 |
|-|-|-|-|-|
| `scripts/main.py` | 端到端完成且 `self_check.ok=true` | 产物已生成但 `self_check.ok=false` | 参数错误 | `case.json` 不存在/不可解析（仍写出 `status=failed`） |
| `scripts/spec_lint.py` | `{"valid": true}` | `{"valid": false}` 逐条列出 | 参数错误 | — |
| `scripts/export_check.py` | `{"valid": true}`（G1–G8 无 error） | `{"valid": false}` | 参数错误 | — |
| `scripts/check_contract.py` | 契约字段全部出现 | 有字段缺失 | 参数错误 / **契约文档解析不出字段**（绝不假通过） | — |
| `scripts/gain_probe.py` | 报告已写出 | 报告已写出但 skill 臂 `rework_points > 0` | 缺 python-pptx | 输入不可读 |
| `scripts/assetkit.py` | 抽取成功且 `text_chars > 0` | — | 抽取不完整 | — |
| `scripts/make_template.py` / `scripts/make_synthetic_inputs.py` | 生成成功 / 至少一个夹具 | — | 无法生成 / 一个都没生成 | — |
| `scripts/deckgen.py` / `scripts/preview.py` | 打印记录后退出 | — | — | — |

## 2. 六条回退链（逐级列明）

### 链 A · 材料读取（M02 / M03 / M04）

| 级 | 手段 | 失败则 |
|-|-|-|
| 1 | `PyMuPDF(fitz)` 抽取文本 + 页内嵌图 | ↓ |
| 2 | `pypdf` | ↓ |
| 3 | `pdfplumber` | ↓ |
| 4 | 外部导出的 `.txt`（`main.py --materials`），工具如实记 | ↓ |
| **末级** | **标注不可读**：`status=failed`、`material_status=unreadable`、语义字段给类型空值；**不补造内容、不构建 deck** | — |

子分支：加密（先试空口令一次）；无文本层（标注"图像型 PDF"，**不做 OCR 冒充**）；
内容与标签不符（**以实际文件为准**，差异写进 sources）。

### 链 B · 图片与图表（M09 / M10）

| 级 | 手段 | 失败则 |
|-|-|-|
| 1 | 论文原生图（页内嵌图抽取） | ↓ |
| 2 | 由表格数字**重建**图（PNG + 可编辑 SVG，`note=reconstructed_from_table`） | ↓ |
| 3 | **显式占位框** `figure-*-placeholder`（文案"需补齐，非原图"）+ `placed=null` | ↓ |
| **末级** | 空图位 + `uncertainty` 点名页；**绝不画示意图冒充数据**（机制 M4 的反面） | — |

### 链 C · 模板适配（M06 / M07 / M08）

| 级 | 手段 | 失败则 |
|-|-|-|
| 1 | 组织方模板，**占位符级填充**（只填占位符、不碰 master、不覆盖页脚/配色） | ↓ |
| 2 | 按 `layout_hint` **名匹配** → 失败则**索引回退** | ↓ |
| 3 | 缺正文占位符 → **补画文本框**（必须登记命名，否则 K3 命名审计告警） | ↓ |
| 4 | **内置 16:9 学术版式**（`ACADEMIC_THEME`）；页数超限先合并非证据页 | ↓ |
| **末级** | `deck.template.kind="builtin"` + `uncertainty[]` 留痕；**绝不静默回退** | — |

### 链 D · 字体与渲染（M12 / M13）

| 级 | 手段 | 失败则 |
|-|-|-|
| 1 | `soffice --headless --convert-to pdf` 产真 PDF，改写 `rendered_with` | ↓ |
| 2 | PIL 近似预览（`preview-approx-*.png`，三处标注近似） | ↓ |
| 3 | 系统 CJK 字体（`C:/Windows/Fonts` → `/System/Library/Fonts` → `/usr/share/fonts`） | ↓ |
| 4 | `SKILL_PREVIEW_FONT` 指定字体 | ↓ |
| **末级** | PIL 默认字体 / `previews=[]`；`run_meta.preview_font` 可为 `null`，**不得**把近似说成真实渲染 | — |

> `.pptx` 内的字体不依赖上述探测：主题 major/minor 注入 + run 级 latin/ea 双写
> （机制 M5）在**任何**预览字体情况下都会写。

### 链 E · 契约回显（M14）

| 级 | 手段 | 失败则 |
|-|-|-|
| 1 | 有真实值 → 写真实值（语义字段 `title/main_claim/slides/render_state/notes_separated`） | ↓ |
| 2 | 无真实值 → 按容器类型给 `""` / `[]` / `{}` | ↓ |
| 3 | 未知字段 → `setdefault` 回显，**禁止 null** | ↓ |
| **末级** | `check_contract.py` 报缺失（exit 1）或契约文档解析不出（exit 2）；**不允许假通过** | — |

四形态对应：① 字段→类型提示 ② 字段→说明文本 ③ 布尔开关 ④ 字段清单（list of 名称）。
案例同时声明 `case_id` 时，与 result 顶层 `case_id` **逐字一致**（K3 的 G1）。

### 链 F · 依赖缺失（M10 / M11 / M12）

| 依赖 | 缺失时的行为 | 记录 |
|-|-|-|
| `python-pptx` | `deck=null`、状态降级、**不生成假文件** | `deck_error` + `uncertainty[]` + `status` |
| PDF 后端 | 见链 A | `run_meta.pdf_tools` + `sources[].tool` |
| `matplotlib` | 跳过重建图 | `run_meta.matplotlib_available=false` + `charts[].chart.reason` |
| `Pillow` | `previews=[]` 并降级说明 | `uncertainty[]` + `rendered_with="failed"` |
| PowerPoint / LibreOffice | 见链 D 第 2 级 | `rendered_with` + `previews[].kind` |

## 3. 状态一致性

| 情形 | 规则 | 违反后果 |
|-|-|-|
| 材料不可读 | **禁止** `status=completed` | K3 直接判 error |
| 有 `evidence_gap` 或占位框 | `status ≤ partial`，`uncertainty` 点名页 | 视为状态不一致 |
| K1 lint 有偏差仍继续 | `status ≤ partial`，`spec_lint.problems` 与 `uncertainty` 同时保留 | 只留其一即违规 |
| 重建图被称作论文原图 | `note=reconstructed_from_table` 后**不得**如此叙述 | 违反诚实性硬约束 |
| 任一次降级 | `uncertainty[]` 与 `change_records[]` **同时**有条目 | `self_check.ok=false` → main.py exit 1 |
| `uncertainty` 为空 | 仅当整链无降级；近似预览 ⇒ `rendered_with` 必须写明 | 需能在本次日志中举证 |

## 4. 降级 ⇒ 哪项机制失效（对照 `MECHANISM.md` 的诚实口径）

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

## 5. 交付前最小自检

```bash
python "$SKILL_DIR/scripts/spec_lint.py"      --spec   <work>/deck-spec.json       # 关口 K1
python "$SKILL_DIR/scripts/main.py"           --case /input/case.json \
  --task /input/task.md --spec <work>/deck-spec.json --out /app/output             # 端到端
python "$SKILL_DIR/scripts/export_check.py"   --result /app/output/result.json \
  --out-dir /app/output --case /input/case.json                                    # 关口 K3 (G1–G8)
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md"                            # 契约全覆盖
python "$SKILL_DIR/scripts/gain_probe.py"     --out <scratch> \
  --arms baseline,skill,ablation --repeat 2                                        # 增益对照（可选）
```

四步中有任一步非 0 退出：先按 §2/§4 对应条目处置并记录（含双写），再重跑；
**不得跳过记录直接交付**。
