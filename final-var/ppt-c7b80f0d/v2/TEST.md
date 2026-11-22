# TEST.md — v2（增益可验证版）实测记录

> 记录对象：本目录（`final-var/ppt-c7b80f0d/v2`）交付版本的**真实执行结果**，
> 含命令、退出码与关键输出，供复核。
>
> **运行环境**：Windows-11-10.0.22621-SP0 / Python 3.13.9 / python-pptx 1.0.2 /
> Pillow 12.3.0 / matplotlib 3.10.6（`matplotlib_available=true`）/ PDF 后端
> `fitz=true, pypdf=true, pdfplumber=true`；**无 LibreOffice** —— 预览一律 PIL 近似渲染。
>
> **执行纪律**：全部命令都在**包外的临时副本**上执行（`$SKILL_DIR` = 副本根，
> `$TMP` = 另一个临时目录，cwd 固定为 `$TMP`，用于同时验证 `$SKILL_DIR` 自定位写法）。
> 唯一例外是 `gain_probe.py`：它给所有子进程设 `PYTHONDONTWRITEBYTECODE=1`，
> **可以在包内原地运行而不留下 `__pycache__`**（见 T-B17 的实测）。

---

## 第一部分 · 执行链与闸门（T-B1 – T-B15）

### T-B1 运行期生成模板 —— exit 0

| 观测项 | 实际值 |
|-|-|
| exit / `status` | `0` / `ok` |
| `bytes` | `28420` |
| `starter_slides` / 布局数 | `1` / `11` |
| 改名布局 | `Picture with Caption → Figure Slide`、`Title Only → Reference Slide` |

包内不携带任何 `.pptx`（技能资源只允许 UTF-8 文本文件），模板一律运行期现产。

### T-B2 端到端冒烟（示例案例）—— exit 0

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" --spec "$SKILL_DIR/examples/deck-spec.json" \
  --out "$TMP/out"
```

| 观测项 | 实际值 |
|-|-|
| exit | `0` |
| `result.json` 顶层键数 | **19** |
| `status` / `deck.slide_count` | `completed` / `8` |
| `evidence_mapping.entries` | `6`（`gaps=[]`） |
| `uncertainty` / `change_records` | `0` 条 / `2` 条 |
| `run_meta.duration_seconds` | `1.7` |
| `run_meta.checkpoints` | `{cp1_spec_lint: true, cp2_build: true, cp3_export_check: true}` |
| `run_meta.self_check.ok` | `true` |
| `deck.template.kind` | `file`（占位符级适配） |
| `deck.layouts_used` | `{Title Slide:1, Title and Content:5, Figure Slide:1, Reference Slide:1}` |
| `deck.theme_fonts.applied` | `true` |
| 产出文件数 | **13** |

### T-B3 闸门 Q3（两道门）—— 均 exit 0

```bash
python "$SKILL_DIR/scripts/export_check.py" --result "$TMP/out/result.json" \
  --out-dir "$TMP/out" --case "$SKILL_DIR/examples/case.json"
# exit 0 -> {"valid": true, "errors": [], "warnings": []}
python "$SKILL_DIR/scripts/check_contract.py" --result "$TMP/out/result.json" \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case "$SKILL_DIR/examples/case.json"
# exit 0 -> {"valid": true, "fields_contracted": 19, "fields_present": 19,
#            "missing": [], "present_but_null": []}
```

### T-B4 确定性（同输入两跑）—— exit 0，72/72 部件一致

| 观测项 | 实际值 |
|-|-|
| 部件数 | `72 / 72` |
| `differing` | `[]` |

### T-B5 运行期合成夹具 + PDF 抽取 —— exit 0

```bash
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --out "$TMP/synth"
# exit 0  status=ok  skipped=[]  generated: fig-placeholder.png (32797 B, Pillow) +
#          synthetic-two-page.pdf (3062 B, pymupdf)
python "$SKILL_DIR/scripts/assetkit.py" --pdf "$TMP/synth/synthetic-two-page.pdf" --out "$TMP/extract"
# exit 0  {"status":"ok","tool":"pymupdf","pages_parsed":2,"text_chars":589,"images_extracted":0}
```

抽取文本含 `[PAGE 1]` / `[PAGE 2]` 标记（两项断言均 true）。占位图为纯几何框
（边框 + 对角线 + "NOT RESEARCH DATA"），**不含坐标轴与数值**。

### T-B6 处置规则 H01：输入不可读 —— 均 exit 3

| 场景 | exit | 输出目录 | 产物 |
|-|-|-|-|
| `--case <不存在的文件>` | `3` | **未创建** | 无（没有输入就不发明产物） |
| `--case <内容损坏的 json>` | `3` | 已创建 | `result.json`：`status=failed`，`error="case_unreadable: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)"` |

### T-B7 处置规则 H05：Q1 lint 反向用例 —— exit 1

```bash
python "$SKILL_DIR/scripts/spec_lint.py" --spec "$TMP/bad-spec.json"
# exit 1  valid=false  problems=7   首条："slide #1: empty title"
```

覆盖：空标题 / 缺 claim / `layout_hint` 不在词表 / bullet 超长 / `evidence` 与
`evidence_gap` 双缺 / 缺 `takeaway` / 缺 `limitations`。

### T-B8 自定位：两种调用风格 —— 均 exit 0

| 风格 | cwd | exit |
|-|-|-|
| A（SKILL.md 推荐） | `$TMP`（**不是**技能根） | `0` |
| B（相对路径） | 技能根 | `0` |

### T-B9 控制台编码加固 —— exit 1（语义正确）且 UTF-8 可解

```bash
PYTHONIOENCODING=cp936 python "$SKILL_DIR/scripts/spec_lint.py" --spec "$TMP/bad-spec.json"
# exit 1；捕获的 stdout 可被 UTF-8 严格解码（utf8_decodable=true）
```

### T-B10 `--demo` 骨架路径 —— exit 0，状态如实降级

| 观测项 | 实际值 |
|-|-|
| exit / `status` | `0` / `partial` |
| `spec_source` | `auto-skeleton (demo / missing material)` |
| `uncertainty` 条数 / `slides` | `2` / `6` |

### T-B11 处置规则 H02：材料缺失 —— exit 0，产物诚实降级

| 观测项 | 实际值 |
|-|-|
| exit | `0`（自检无 error：失败被如实记录，而不是伪造产物） |
| `status` / `deck` | `failed` / `null` |
| `material_status` | `unreadable` |
| 语义字段 | `title=""`、`main_claim=""`、`slides=[]` |
| `run_meta.self_check` | `{ok: true, problems: []}` |

### T-B12 处置规则 H07：模板不可用时的回退 —— exit 0

```bash
# 在没有生成模板的副本上跑
# exit 0  status=completed  deck.template.kind=builtin（guard: built-in 16:9 academic layout
#          (no organizer template supplied)，layout_count=11）
# uncertainty 1 条：declared template 'template-example.pptx' was not usable — built-in 16:9
#                   academic layout used instead ...
```

### T-B13 处置规则 H08：页数超限 —— exit 0，如实标记

```bash
# spec 的 constraints.slide_count 改为 3（脚本补封面/收尾后实际 8 页）
# exit 0  status=completed  deck.page_budget_met=false  deck.slide_count=8
# uncertainty: "page budget 3 exceeded (8 slides) — trim/merge per SKILL decision rules"
```

### T-B14 OOXML 层与主题字体 —— exit 0

`ooxml_kit.py <deck>` 返回含 `zip` / `naming` / `notes` 三组记录；直接读
`ppt/theme/theme1.xml`，`Microsoft YaHei` 与 `Calibri` 均存在（major/minor 注入生效）。

### T-B15 备注分离与预览诚实标注

| 观测项 | 实际值 |
|-|-|
| `deck.notes_included` / `deck.notes_separated` | `true` / `true` |
| 顶层 `notes_separated` | `true` |
| `previews` | `7` 条，`kind` 集合 = `{pil-approximation}` |
| `run_meta.rendered_with` | `pil-approximation (no PowerPoint/LibreOffice attached)` |
| `deck.overflow_guard` | `{max_bullets: 6, max_chars_bullet: 110}` |
| `charts` | `1` 条（`reconstructed_from_table`，附可编辑 SVG） |

---

## 第二部分 · 增益对照执行件（T-B16 – T-B20）

### T-B16 `gain_probe.py` 输入不可读 —— exit 3

```bash
python "$SKILL_DIR/scripts/gain_probe.py" --case "$TMP/nope.json" --out "$TMP/bad"
# {"status": "input_unreadable", "case": "<...>/nope.json"}   exit 3
```

（另有 exit 2 = 后端不可用：缺 `python-pptx`；该分支按代码路径检查，本机装了 pptx 故未触发。）

### T-B17 字节码卫生：原地运行不留 `__pycache__` —— 通过

```bash
# 在一个刚复制出来的干净副本上，不设任何环境变量，只跑 gain_probe
python "$SKILL_DIR/scripts/gain_probe.py" --out "$TMP/run" --arms baseline,skill,ablation
# exit 0
find "$SKILL_DIR" -name "__pycache__" -o -name "*.pyc"
# 输出为空 —— 0 个 __pycache__ / 0 个 .pyc
```

机制：`gain_probe.py` 给每个子进程注入 `PYTHONDONTWRITEBYTECODE=1`，
自己作为入口脚本也不会被缓存。**对照实验**：同一副本里若直接跑
`make_template.py`，则会出现 `scripts/__pycache__/cli_io.cpython-313.pyc`
（2 个条目）—— 所以**其余脚本仍必须在包外副本上运行**，这条纪律没有放松。

### T-B18 三臂对照（条件 T：模板在场）—— exit 0

```bash
python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"   # 让模板在场
python "$SKILL_DIR/scripts/gain_probe.py" --out "$TMP/gain-T" \
       --arms baseline,skill,ablation --repeat 2                            # exit 0
```

| 指标 | `baseline` | `skill` | `ablation` |
|-|-|-|-|
| `rework_points` | **6** | **0** | 2 |
| `claim_coverage` | 0.0 | **1.0** | 1.0 |
| `substantive_claim_coverage` | 0.0 | **1.0** | 0.0 |
| `placeholder_claims` | 0 | 0 | 1 |
| `evidence_rows` / `evidence_locations` | 0 / 0 | **6 / 6** | 1 / 0 |
| `contract_fields_present`（/19） | 7 | **19** | 19 |
| `notes_pages`（页数） | 0（3） | **8（8）** | 3（6） |
| `named_shapes` | 0 | 3 | 2 |
| `over_limit_frames` | 2 | **0** | 0 |
| `artifacts` | 2 | 13 | 6 |
| `template_adapted` | false | true | true |
| `wall_seconds` | 0.028 / 0.022 | 2.155 / 2.508 | 1.490 / 1.109 |
| `differing_opc_parts` | 0 | **0** | 0 |

`baseline` 的 `rework` 原文（6 条）：契约顶层字段缺 6 个 / 无页级主张 / 无证据映射文件 /
无机器可读证据图 / 备注 0/3 页 / 2 个正文框超限。`ablation` 的 `rework`（2 条）：
1 页为占位主张 / 备注 3/6 页。`skill` 的 `rework` 为空数组。

### T-B19 三臂对照（条件 N：无模板）—— exit 0

| 指标 | `baseline` | `skill` | `ablation` |
|-|-|-|-|
| `rework_points` | 6 | **0** | 2 |
| `substantive_claim_coverage` | 0.0 | **1.0** | 0.0 |
| `evidence_rows` / `evidence_locations` | 0 / 0 | **6 / 6** | 1 / 0 |
| `notes_pages` | 0 | **8** | 3 |
| `named_shapes` | 0 | **17** | 6 |
| `wall_seconds` | 0.024 | 1.880 | 1.745 |

条件 N 下 `named_shapes` 由 3 升到 17：模板缺失时走内置版式，标题/正文/图注/页脚
全部由本包创建并命名；模板在场时大量对象是**复用组织方占位符**（按铁律不改名），
所以该数较低 —— 这是设计使然，**不是能力下降**。

### T-B20 报告结构自检 —— 通过

`gain-report.json` 顶层含：`protocol_version`（`gain-probe/1.0`）、`case_id`、
`case_file`、`arms_requested`、`contract_fields_checked`（`19`，从
`references/OUTPUT_CONTRACT.md` §1 解析）、`repeat`、`arms`（逐臂 `metrics` + `runs`）、
`notes`（三条口径声明）。默认 `--arms baseline,skill`；`--json` 可改报告路径。

---

## 限制（如实声明）

- 预览为 **PIL 近似渲染**，不是 PowerPoint/LibreOffice 结果；本机无 LibreOffice，
  未产出真 PDF 预览（SKILL 支持检测到 `soffice` 时转换并改写记录）；
- 对照的 `baseline` 臂是"基础 Agent 行为"的**可执行代理**，不是对某个具体 LLM 的测量；
  `wall_seconds` 只反映脚本开销，**不等于**端到端总耗时更短；
- 所有对照建立在**合成示例案例**上（ExampleNet，人物/机构/数值均虚构）；
  正式 3 个案例由平台提供；
- 本记录**不含任何正式案例答案、也不含平台分数声明**。
