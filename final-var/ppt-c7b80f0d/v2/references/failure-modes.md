# failure-modes.md — 异常处置与其对增益断言的影响

本文件是 **可靠体验（10 分）· 异常处理（3 分）** 的落点，也是 `SKILL.md` §5 处置规则
**H01–H14** 的同号展开。与只列"怎么办"的写法相比，本版多一列：
**该降级会不会让 `GAIN-PROTOCOL.md` 的某条增益断言不再成立**——如果会，
必须在该次运行的 `uncertainty[]` 里明说，不能一边降级一边宣称满额增益。

## 1. 退出码语义

| 脚本 | 0 | 1 | 2 | 3 |
|-|-|-|-|-|
| `scripts/main.py` | 端到端完成且 `run_meta.self_check.ok=true` | 产物已生成但 `self_check.ok=false` | 参数错误 | `case.json` 不存在/不可解析（仍写出 `status=failed` 的 result.json） |
| `scripts/spec_lint.py` | `{"valid": true}` | `{"valid": false}`，`problems` 逐条列出 | 参数错误 | — |
| `scripts/export_check.py` | `{"valid": true}`（G1–G8 无 error） | `{"valid": false}` | 参数错误 | — |
| `scripts/check_contract.py` | 契约字段全部出现 | 有字段缺失 | 参数错误 / 契约文档解析不出字段 | — |
| `scripts/gain_probe.py` | 报告已写出（`gain-report.json`） | 报告已写出但 skill 臂的 `rework_points > 0` | 后端不可用（缺 python-pptx） | 输入不可读（case 缺失/不可解析） |
| `scripts/assetkit.py` | 抽取成功且 `text_chars > 0` | — | 抽取不完整 | — |
| `scripts/make_template.py` | 模板已生成 | — | 无法生成 | — |
| `scripts/make_synthetic_inputs.py` | 至少生成一个夹具 | — | 一个都没生成 | — |
| `scripts/deckgen.py` / `scripts/preview.py` | 打印记录后退出 | — | — | — |

> `deckgen.py` / `preview.py` 只打印记录，失败以 JSON 字段表达，不改退出码；
> 正式流程一律经 `main.py`，以 `self_check` 判定成败。

## 2. 五类异常逐条处置（含"对增益断言的影响"）

### 2.1 材料异常（H02 / H03 / H04 / H09 / H10）

| 识别 | 首选 | 降级 | 记录字段 | 退出码 | 对 GA 断言的影响 |
|-|-|-|-|-|-|
| 材料路径不存在 | 只产元信息 result，不构建 deck | 状态降 `failed`，语义字段给类型空值 | `material_status=unreadable`、`sources[].reason` | main.py → 0/1 | **GA1/GA2/GA4 全部不成立**（没有 deck，也没有表现可言）——必须在 uncertainty 里说明"本案例未产出可评估产物" |
| PDF 加密 | 试空口令一次 | 改用外部 `.txt`（`--materials`），如实记工具 | `uncertainty[]` + `sources[].tool` | assetkit → 2 | 文本来自外部转换时，`sources[]` 必须写清工具；否则 GA2 的"可追溯"只追溯到一层转换 |
| PDF 无文本层（扫描件） | 标注"图像型 PDF"，仍引用可抽取的图 | **不做 OCR 冒充** | `uncertainty[]` + `sources[].tool` | assetkit → 2 | 页级主张只能建立在图与题注上 ⇒ GA1 仍成立，但需在 uncertainty 说明证据层薄弱 |
| 无 PDF 库 | 用自带读取转 `.txt` 传入 | 仍不可读 → 按材料缺失处置 | `run_meta.pdf_tools` | assetkit → 2 | 同加密分支 |
| 图/表抽不出 | 保留显式占位框（"需补齐，非原图"） | 引用与定位照留，不伪造图 | `figure.placed=null` + `placeholder=true` | — | **GA2 仍成立但需标注**：定位存在、图像缺失，两者不可混为一谈 |
| 重建图失败 | 跳过图，保留表引用与原文数字 | 不估算补齐数字 | `charts[].chart.reason` | — | GA2 中该页的证据类型退回"表格数字 + 引用" |
| 材料内容与标签不符 | 以实际文件为准 | 差异写入 sources | `sources[]` + `uncertainty[]` | — | 不按标签补造是 GA1 的前提：占位/臆测主张会让 `placeholder_claims > 0` |

### 2.2 模板问题（H06 / H07 / H08）

| 识别 | 首选 | 降级 | 记录字段 | 对 GA 断言的影响 |
|-|-|-|-|-|
| 未提供模板 | 内置 16:9 学术版式（正常分支） | 需要真模板时 `make_template.py` 现产 | `deck.template.kind="builtin"` + `uncertainty[]` | 无负面影响；条件是**条件 N**，应与**条件 T** 分开记录（见 GAIN-PROTOCOL §1/§4.2） |
| 模板文件不存在 / 打不开 | 回退内置版式并继续 | 记录原始异常串 | `deck.template.kind/error` + `uncertainty[]` | 同上；`template_adapted` 会计为 `false`，报告里必须与"能力下降"区分 |
| 占位符不足 | 名匹配 → 索引回退 → 补画文本框（登记命名） | 补画对象必须进命名表 | `deck.layouts_used` + `uncertainty[]` | `named_shapes` 会升高（自建对象变多），这是记录项而非缺陷 |
| 起始演示需替换 | `template_mode="replace"` 移除起始页 | 默认 `"layouts"` 保留 | `starter_slides_removed` | 页数会变化 ⇒ 与 `slide_count` 的比对要看最终值 |
| 页数超限 | 合并非证据页（封面/过渡/收尾优先） | **绝不静默丢弃证据页** | `page_budget_met=false` + `change_records[]` | 合并会减少 `evidence_rows`；**此时 GA2 的判据改为"表行数 = 合并后的 entries"**，并在 uncertainty 说明合并了哪些页 |

### 2.3 依赖缺失（H10 / H11 / H12 / H13）

| 依赖 | 缺失时的行为 | 记录字段 | 对 GA 断言的影响 |
|-|-|-|-|
| `python-pptx` | `deck=null`、状态降级、**不生成假文件** | `deck_error` + `uncertainty[]` + `status` | **GA1/GA4/GA5 无法评估**；GA3 仍可成立（result.json 契约完整） |
| PDF 后端 | 逐级 `fitz → pypdf → pdfplumber → 外部文本` | `run_meta.pdf_tools` + `sources[].tool` | 影响证据来源层级，需在 sources 里点明 |
| `matplotlib` | 跳过重建图 | `matplotlib_available=false` + `charts[].chart.reason` | 同"重建图失败" |
| `Pillow` | `previews=[]`，状态降级 | `uncertainty[]` + `rendered_with="failed"` | 不影响 GA1–GA3；`artifacts` 计数下降 |
| 中文字体 | 降级 PIL 默认字体继续预览 | `run_meta.preview_font`（可 `null`）+ `uncertainty[]` | 不影响 GA1–GA3；预览可读性下降要如实说明 |
| PowerPoint / LibreOffice | `pil-approximation`，文件名带 `approx` | `rendered_with` + `previews[].kind` | 不影响 GA 判据；**但不得把近似说成真实渲染**（诚实性硬约束） |

### 2.4 契约四形态（H14）

| 形态 | 处理 | 校验 | 对 GA 断言的影响 |
|-|-|-|-|
| ① 字段→类型提示 | 有真实值写真实值；否则按容器 `""`/`[]`/`{}` | G2；`check_contract` | GA3 = `contract_fields_present` 直接由此决定 |
| ② 字段→说明 | 语义可推断时写真实值 | 同上 | 同上 |
| ③ 布尔开关 | 回显真实布尔 | 同上 | 同上 |
| ④ 字段清单（list） | 每个名称按 `""` 回显 | 同上 | 同上 |
| 未知字段 | `setdefault`，**禁止 null** | `result.output_contract` | 出现 null 会让 GA3 判据不成立（"19/19 且无 null"） |
| 案例声明 `case_id` | 与顶层 `case_id` 逐字一致 | G1 | 不一致 → Q3 直接 error |

### 2.5 状态一致性

| 情形 | 规则 | 对 GA 断言的影响 |
|-|-|-|
| 材料不可读 | **禁止** `status=completed` | GA1–GA5 均不适用；报告须写"本案例无可评估产物" |
| 有 `evidence_gap` 或占位框 | `status ≤ partial`，uncertainty 点名页 | GA2 判据改为"表行数 = entries 且 gap 有独立行" |
| Q1 lint 有偏差仍继续 | `status ≤ partial`，`spec_lint.problems` 与 uncertainty 同时保留 | GA5 的 `rework_points` 会 >0，**不许宣称 0 返工** |
| 任一次降级 | `uncertainty[]` 与 `change_records[]` **同时**有条目 | 缺一 → `self_check.ok=false` → main.py exit 1 |
| `uncertainty` 为空 | 仅当整链无降级；近似预览 ⇒ `rendered_with` 必须写明 | 空 uncertainty 与 GA5=0 同时出现才自洽 |

## 3. 降级与增益声明的相容性（一句话判据）

> **凡是会让 GA1–GA5 中任一条不成立的降级，都必须在同一次运行的 `uncertainty[]` 里
> 写明"该断言本次不适用/降级成立"，并且在引用对照数字时不得把它算进"加载后的优势"。**

反例（禁止）：某次运行因缺 `python-pptx` 没有产出 deck，却仍在汇报里写
"本次 `rework_points = 0`" —— 没有 deck 的目录根本不会产生那份报告，
这种引用是把"没测"说成"通过"。

## 4. 交付前最小自检

```bash
python "$SKILL_DIR/scripts/spec_lint.py"     --spec   <work>/deck-spec.json        # Q1
python "$SKILL_DIR/scripts/main.py"          --case /input/case.json \
  --task /input/task.md --spec <work>/deck-spec.json --out /app/output             # 端到端
python "$SKILL_DIR/scripts/export_check.py"  --result /app/output/result.json \
  --out-dir /app/output --case /input/case.json                                    # Q3 (G1–G8)
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md"                            # 契约字段全覆盖
# 可选：增益对照（只写 --out，不污染包）
python "$SKILL_DIR/scripts/gain_probe.py" --out <scratch> --arms baseline,skill --repeat 2
```

四步中有任一步非 0 退出：先按 §2 对应条目处置并记录（含双写），再重跑；
**不得跳过记录直接交付**。
