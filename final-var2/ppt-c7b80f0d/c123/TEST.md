# TEST.md — v3（机制与复用显性版）实测记录

> 记录对象：本目录（`final-var/ppt-c7b80f0d/v3`）交付版本的**真实执行结果**，
> 含命令、退出码与关键输出，供复核。
>
> **运行环境**：Windows-11-10.0.22621-SP0 / Python 3.13.9 / python-pptx 1.0.2 /
> Pillow 12.3.0 / matplotlib 3.10.6（`matplotlib_available=true`）/ PDF 后端
> `fitz=true, pypdf=true, pdfplumber=true`；**无 LibreOffice** —— 预览一律 PIL 近似渲染。
>
> **执行纪律**：除 `gain_probe.py`（见 T-C17）外，全部命令都在**包外的临时副本**上执行：
> `$SKILL_DIR` = 副本根，`$TMP` = 另一个临时目录，cwd 固定为 `$TMP`
> （用于同时验证 `$SKILL_DIR` 自定位写法）。包内不写入任何测试产物。

---

## 第一部分 · 关口与回退链（T-C1 – T-C15）

### T-C1 运行期生成模板（机制 M7）—— exit 0

| 观测项 | 实际值 |
|-|-|
| exit / `status` | `0` / `ok` |
| `bytes` | `28420` |
| `starter_slides` / 布局数 | `1` / `11` |
| 改名布局 | `Picture with Caption → Figure Slide`、`Title Only → Reference Slide` |

包内不携带任何 `.pptx`；模板一律运行期现产，这是通过"仅文本资源"硬门的前提。

### T-C2 端到端冒烟 —— exit 0

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
| `run_meta.duration_seconds` | `1.27` |
| `run_meta.checkpoints` | `{cp1_spec_lint: true, cp2_build: true, cp3_export_check: true}` |
| `run_meta.self_check.ok` | `true` |
| `deck.template.kind` | `file`（占位符级适配） |
| `deck.layouts_used` | `{Title Slide:1, Title and Content:5, Figure Slide:1, Reference Slide:1}` |
| `deck.theme_fonts.applied` | `true` |
| 产出文件数 | **13** |

### T-C3 关口 K3（两道门）—— 均 exit 0

```bash
python "$SKILL_DIR/scripts/export_check.py" --result "$TMP/out/result.json" \
  --out-dir "$TMP/out" --case "$SKILL_DIR/examples/case.json"
# exit 0 -> {"valid": true, "errors": [], "warnings": []}
python "$SKILL_DIR/scripts/check_contract.py" --result "$TMP/out/result.json" \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case "$SKILL_DIR/examples/case.json"
# exit 0 -> {"valid": true, "fields_contracted": 19, "fields_present": 19,
#            "missing": [], "present_but_null": []}
```

### T-C4 内容确定性（机制 M6 的支撑证据）—— exit 0

| 观测项 | 实际值 |
|-|-|
| 部件数 | `72 / 72` |
| `differing` | `[]`（全部 OPC 部件 sha256 逐部件一致） |

### T-C5 运行期合成夹具 + PDF 抽取（链 A）—— exit 0

```bash
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --out "$TMP/synth"
# exit 0  status=ok  skipped=[]  generated: fig-placeholder.png (32797 B, Pillow) +
#          synthetic-two-page.pdf (3062 B, pymupdf)
python "$SKILL_DIR/scripts/assetkit.py" --pdf "$TMP/synth/synthetic-two-page.pdf" --out "$TMP/extract"
# exit 0  {"status":"ok","tool":"pymupdf","pages_parsed":2,"text_chars":589,"images_extracted":0}
```

抽取文本含 `[PAGE 1]` / `[PAGE 2]`（两项断言均 true）。

### T-C6 规则 M01：输入不可读（链 A 末级）—— 均 exit 3

| 场景 | exit | 输出目录 | 产物 |
|-|-|-|-|
| 文件不存在 | `3` | **未创建** | 无 |
| 内容损坏 | `3` | 已创建 | `result.json`：`status=failed`，`error="case_unreadable: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)"` |

### T-C7 规则 M05：关口 K1 反向用例 —— exit 1

```bash
python "$SKILL_DIR/scripts/spec_lint.py" --spec "$TMP/bad-spec.json"
# exit 1  valid=false  problems=7   首条："slide #1: empty title"
```

覆盖：空标题 / 缺 claim / `layout_hint` 不在词表 / bullet 超长 / `evidence` 与
`evidence_gap` 双缺 / 缺 `takeaway` / 缺 `limitations`。

### T-C8 自定位（机制 M9）—— 两种调用风格均 exit 0

| 风格 | cwd | exit |
|-|-|-|
| A | `$TMP`（**不是**技能根） | `0` |
| B | 技能根（相对路径） | `0` |

### T-C9 控制台加固（机制 M8）—— exit 1 且 UTF-8 可解

```bash
PYTHONIOENCODING=cp936 python "$SKILL_DIR/scripts/spec_lint.py" --spec "$TMP/bad-spec.json"
# exit 1；捕获的 stdout 可被 UTF-8 严格解码（utf8_decodable=true）
```

### T-C10 `--demo` 骨架路径 —— exit 0，状态如实降级

`status=partial`、`spec_source="auto-skeleton (demo / missing material)"`、
`uncertainty` 2 条、`slides=6`。（该路径同时是增益对照的 `ablation` 臂。）

### T-C11 规则 M02：材料缺失 —— exit 0，产物诚实降级

| 观测项 | 实际值 |
|-|-|
| exit | `0`（失败被如实记录，而不是伪造产物） |
| `status` / `deck` | `failed` / `null` |
| `material_status` | `unreadable` |
| 语义字段 | `title=""`、`main_claim=""`、`slides=[]` |
| `run_meta.self_check` | `{ok: true, problems: []}` |

### T-C12 规则 M07：模板不可用 → 链 C 第 4 级 —— exit 0

```bash
# 在没有生成模板的副本上跑
# exit 0  status=completed
# deck.template = {kind:"builtin", path:null, basename:null, layout_count:11,
#                  guard:"built-in 16:9 academic layout (no organizer template supplied)"}
# uncertainty 1 条：declared template 'template-example.pptx' was not usable …
```

### T-C13 规则 M08：页数超限 —— exit 0，如实标记

`status=completed`、`deck.page_budget_met=false`、`deck.slide_count=8`，
`uncertainty`：`"page budget 3 exceeded (8 slides) — trim/merge per SKILL decision rules"`。

### T-C14 OOXML 层：容器、命名与主题字体（机制 M5/M6）—— exit 0

`ooxml_kit.py <deck>` 输出含 `zip` / `naming` / `notes` 三组记录；直接读
`ppt/theme/theme1.xml`，`Microsoft YaHei` 与 `Calibri` 均存在（主题 major/minor 注入生效）。

### T-C15 备注分离与预览诚实标注

| 观测项 | 实际值 |
|-|-|
| `deck.notes_included` / `deck.notes_separated` | `true` / `true` |
| 顶层 `notes_separated` | `true` |
| `previews` | `7` 条，`kind` 集合 = `{pil-approximation}` |
| `run_meta.rendered_with` | `pil-approximation (no PowerPoint/LibreOffice attached)` |
| `deck.overflow_guard` | `{max_bullets: 6, max_chars_bullet: 110}` |
| `charts` | `1` 条（`reconstructed_from_table`，附可编辑 SVG） |

---

## 第二部分 · 机制与对照（T-C16 – T-C19）

### T-C16 机制消融实测（条件 T：模板在场，`--repeat 2`）—— exit 0

```bash
python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"
python "$SKILL_DIR/scripts/gain_probe.py" --out "$TMP/gain" \
       --arms baseline,skill,ablation --repeat 2      # exit 0
```

| 指标 | `baseline` | `skill` | `ablation`（摘除机制 M2） |
|-|-|-|-|
| `rework_points` | **6** | **0** | 2 |
| `claim_coverage` | 0.0 | **1.0** | 1.0 |
| `substantive_claim_coverage` | 0.0 | **1.0** | **0.0** |
| `placeholder_claims` | 0 | 0 | 1 |
| `evidence_rows` / `evidence_locations` | 0 / 0 | **6 / 6** | 1 / 0 |
| `contract_fields_present`（/19） | 7 | **19** | 19 |
| `notes_pages`（页数） | 0（3） | **8（8）** | 3（6） |
| `named_shapes` | 0 | 3 | 2 |
| `over_limit_frames` | 2 | **0** | 0 |
| `artifacts` | 2 | 13 | 6 |
| `wall_seconds` | 0.025 | 2.377 | 1.406 |
| `differing_opc_parts` | 0 | **0** | 0 |

差值归因见 `references/GAIN-PROTOCOL.md` §4.3：摘除 M2 后六个指标同时朝坏的方向动，
而 M1 的契约覆盖仍是 19/19 —— 说明消融**只打中一项机制**，归因成立。

### T-C17 字节码卫生（机制 M8）—— 通过

```bash
# 干净副本，不设任何环境变量，只跑 gain_probe
find "$SKILL_DIR" -name "__pycache__" -o -name "*.pyc"   # 运行前：0
python "$SKILL_DIR/scripts/gain_probe.py" --out "$TMP/run" --arms baseline,skill
# exit 0
find "$SKILL_DIR" -name "__pycache__" -o -name "*.pyc"   # 运行后：0   ← 关键
# 对照：同一副本再跑一次 make_template.py
find "$SKILL_DIR" -name "__pycache__" -o -name "*.pyc"   # 2（scripts/__pycache__/cli_io.cpython-313.pyc）
```

结论：`gain_probe.py` **可以在包内原地运行**而不污染包（它给子进程注入
`PYTHONDONTWRITEBYTECODE=1`）；**其余脚本仍必须在包外副本上运行**。

### T-C18 跨包可复现性（同一探针在 v2 与 v3 两份包上各跑一次）—— 通过

| 指标 | v2 包上的运行 | v3 包上的运行 | 是否一致 |
|-|-|-|-|
| `baseline.rework_points` | 6 | 6 | ✅ |
| `skill.rework_points` | 0 | 0 | ✅ |
| `ablation.rework_points` | 2 | 2 | ✅ |
| `substantive_claim_coverage`（三臂） | 0.0 / 1.0 / 0.0 | 0.0 / 1.0 / 0.0 | ✅ |
| `evidence_rows`（三臂） | 0 / 6 / 1 | 0 / 6 / 1 | ✅ |
| `notes_pages`（三臂） | 0 / 8 / 3 | 0 / 8 / 3 | ✅ |
| `wall_seconds`（三臂） | 0.028 / 2.155 / 1.490（另一次 2.245） | 0.025 / 2.377 / 1.406 | ❌ 时间不同（机器负载） |

结论：结构指标**跨包复现完全一致**，只有墙钟时间波动 —— 这正是
`GAIN-PROTOCOL.md` §3 把 `wall_seconds` 标为"只作参考、不作绝对承诺"的理由。

### T-C19 复用清单自检（`REUSE-KIT.md` 的可验证性）—— 通过

```bash
# 1) REUSE-KIT.md 里以反引号引用的文件是否都真实存在（解析 scripts/ references/ examples/ 前缀）
#    referenced = 25, unresolved = ['validate_pkg.py']
#    —— validate_pkg.py 是仓库级合规验收器，本就不在包内（文档已点明"包外跑一次"）
# 2) REUSE-KIT §1.5 列的 7 个色值是否与 scripts/deckgen.py 的 ACADEMIC_THEME 一致
#    kit hexes = {1F4E79, 2E74B5, F2F7FC, 262626, 595959, C0504D, FFFFFF}
#    deckgen    = {primary 1F4E79, accent 2E74B5, light F2F7FC, ink 262626,
#                  muted 595959, warn C0504D, white FFFFFF}     → theme match: True
# 3) 命名前缀表（layer-naming.md §2）与 scripts/ooxml_kit.py 的 PREFIX_BY_KIND 一致
#    → 10 个前缀：claim-title- claim-strip- body-bullets- figure- table-
#      footer-page- outline- evidence-map- closing- cover-
```

---

## 第三部分 · 沿革：本包所用脚本在重打包时修掉的真实缺陷

这些缺陷发生在**本包所用脚本的这一血脉**上（v2.1.0 之前的实现），
修好后才有今天的 `TEST.md` 各项通过；记录在此是为了让
`references/MECHANISM.md` 的"没有它会怎样"可被追溯，而不是当作宣传。

| # | 现象 | 处置 | 与哪项机制相关 |
|-|-|-|-|
| 1 | `--demo` 无 `--spec` 时 `os.path.join(None, …)` → `TypeError`，整轮崩溃 | `_resolve_template_path` 跳过空基目录 | M8（关口不完整） |
| 2 | `result.json` 缺顶层 `output_contract` 容器（文档要 19 字段，代码只回显语义字段） | `apply_output_contract` 先回显声明容器；引入 `check_contract` 后**当场发现该漂移** | **M1** |
| 3 | 主题字体注入**必然失败**（python-pptx 把 theme 载为泛型 Part，无 `.element`），且只留一句 uncertainty | `ooxml_kit` 增加 `_find_theme_part/_theme_root/_store_root`，对泛型 Part 写回 blob | **M5** |
| 4 | `run_meta.checkpoints.cp3_export_check` 永远是 `null` | 自检结束后写回真实布尔 | M8 |
| 5 | 材料不可读时契约语义字段回显骨架文案（`main_claim="SKELETON"`） | 失败且非 demo 的运行传 `spec=None`，语义字段按类型给空值 | M2+M14 |
| 6 | 非 UTF-8 控制台下打印中文可能在**产物写好之后**崩溃 | 新增 `scripts/cli_io.py`，各 CLI 入口调用 | **M8** |
| 7 | `check_contract` 读契约文档失败会"静默通过" | 解析不到字段即 exit 2 并报错，**绝不假通过** | **M1** |
| 8 | 声明了模板但模板不可用时静默回退（只在 `deck.template.kind` 里体现） | 回退显式写入 `uncertainty`，与链 C 的承诺一致 | **M4/M7** |

---

## 限制（如实声明）

- 预览为 **PIL 近似渲染**，不是 PowerPoint/LibreOffice 结果；本机无 LibreOffice，
  未产出真 PDF 预览（检测到 `soffice` 时会转换并改写记录）；
- 对照的 `baseline` 臂是"基础 Agent 行为"的**可执行代理**，不是对某个具体 LLM 的测量；
  `wall_seconds` 只反映脚本开销，**不等于**端到端总耗时更短；
- 所有对照建立在**合成示例案例**上（ExampleNet，人物/机构/数值均虚构）；
  正式 3 个案例由平台提供；
- 沿革表是**本血脉的历史记录**，用于追溯机制来源；它不代表当前版本仍存在这些缺陷；
- 本记录**不含任何正式案例答案、也不含平台分数声明**。
