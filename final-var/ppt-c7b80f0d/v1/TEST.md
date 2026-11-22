# TEST.md — v1（决策规则版）实测记录

> 记录对象：本目录（`final-var/ppt-c7b80f0d/v1`）交付版本的**真实执行结果**，
> 含命令、退出码与关键输出，供复核。
>
> **运行环境**（自 `result.json` 的 `run_meta` 读出）：
> Windows-11-10.0.22621-SP0 / Python 3.13.9 / python-pptx 1.0.2 / Pillow 12.3.0 /
> matplotlib 3.10.6（`matplotlib_available=true`）/ PDF 后端 `fitz=true, pypdf=true,
> pdfplumber=true`；**无 LibreOffice** —— 预览一律 PIL 近似渲染并如实标注。
>
> **执行纪律（重要）**：全部命令都在**包外的临时副本**上执行——先把本包复制到
> 临时目录（记作 `$SKILL_DIR`），输出写到另一个临时目录（记作 `$TMP`），
> 且 cwd 固定为 `$TMP`（**不是**技能根目录），用于同时验证 SKILL.md 的
> `$SKILL_DIR` 自定位写法。**包内不写入任何测试产物**：Python 会在 `scripts/` 下
> 生成 `__pycache__`，而技能资源只允许文本文件，`validate_pkg.py` 会因此判 FAIL。
>
> 下表各行的"实际结果"列全部来自一次连续执行（harness 串行跑完 15 组断言），
> 未做人工挑选。

---

## T-A1 运行期生成示例模板 —— exit 0

```bash
python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"
```

| 观测项 | 实际值 |
|-|-|
| exit | `0` |
| `status` | `ok` |
| `bytes` | `28420` |
| `starter_slides` | `1` |
| 布局数 | `11` |
| 改名布局 | `Picture with Caption → Figure Slide`、`Title Only → Reference Slide` |

模板为**运行期生成**：包内不携带任何 `.pptx`（技能资源只允许 UTF-8 文本文件）。

## T-A2 端到端冒烟（示例案例）—— exit 0

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" --spec "$SKILL_DIR/examples/deck-spec.json" \
  --out "$TMP/out"
```

| 观测项 | 实际值 |
|-|-|
| exit | `0` |
| `result.json` 顶层键数 | **19** |
| `status` | `completed` |
| `deck.slide_count` | `8` |
| `evidence_mapping.entries` | `6`（`gaps=[]`） |
| `uncertainty` 条数 | `0`（本示例无降级，符合不变量 I6） |
| `change_records` 条数 | `2` |
| `run_meta.duration_seconds` | `1.7` |
| `run_meta.checkpoints` | `{cp1_spec_lint: true, cp2_build: true, cp3_export_check: true}` |
| `run_meta.self_check` | `{ok: true, problems: []}` |
| `deck.template.kind` | `file`（组织方示例模板，占位符级适配） |
| `deck.layouts_used` | `{Title Slide:1, Title and Content:5, Figure Slide:1, Reference Slide:1}` |
| `deck.theme_fonts.applied` | `true` |
| 产出文件数 | **13** |

产出清单：`result.json`、`academic_deck.pptx`、`chart-Fig_1.png`、`chart-Fig_1.svg`、
`evidence_mapping.md`、`evidence_map.json`、`preview-approx-cover.png` +
`preview-approx-001..006.png`。

## T-A3 两道交付门 —— 均 exit 0

```bash
python "$SKILL_DIR/scripts/export_check.py" --result "$TMP/out/result.json" \
  --out-dir "$TMP/out" --case "$SKILL_DIR/examples/case.json"
# exit 0 -> {"valid": true, "errors": [], "warnings": []}

python "$SKILL_DIR/scripts/check_contract.py" --result "$TMP/out/result.json" \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case "$SKILL_DIR/examples/case.json"
# exit 0 -> {"valid": true, "fields_contracted": 19, "fields_present": 19,
#            "missing": [], "present_but_null": []}
```

C3 的 G1–G8 全过（`errors` 与 `warnings` 均为空）；契约**19/19 覆盖、零 null**。

## T-A4 内容确定性（同输入两跑）—— exit 0

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --spec "$SKILL_DIR/examples/deck-spec.json" --out "$TMP/out2"
# 对 out/academic_deck.pptx 与 out2/academic_deck.pptx 逐 OPC 部件比 sha256
```

| 观测项 | 实际值 |
|-|-|
| exit | `0` |
| 部件数 | `72 / 72` |
| `differing` | `[]`（全部 72 个部件 sha256 逐部件一致） |

这条同时是"运行稳定性 4 分"的可复核证据：对象命名与部件内容对同输入确定。

## T-A5 运行期合成夹具 + PDF 抽取链路 —— exit 0

```bash
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --out "$TMP/synth"
# exit 0  status=ok  skipped=[]
python "$SKILL_DIR/scripts/assetkit.py" --pdf "$TMP/synth/synthetic-two-page.pdf" --out "$TMP/extract"
# exit 0  {"status":"ok","tool":"pymupdf","pages_parsed":2,"text_chars":589,"images_extracted":0}
```

抽取文本含页标记 `[PAGE 1]` 与 `[PAGE 2]`（两项断言均为 `true`）。占位图为**纯几何框**
（边框 + 对角线 + "NOT RESEARCH DATA" 文案），**不含坐标轴与数值**，不会被误认成科研数据。

## T-A6 决策规则 D01：输入不可读的两条路径 —— 均 exit 3

```bash
python "$SKILL_DIR/scripts/main.py" --case "$TMP/nope.json" --out "$TMP/nope"
# exit 3；输出目录未创建（out_dir_created=false）——没有输入就不发明产物

# 另造一个内容损坏的 case.json（"{" 后跟非 JSON 内容）
python "$SKILL_DIR/scripts/main.py" --case "$TMP/broken-case.json" --out "$TMP/broken"
# exit 3；仍写出 result.json：
# {"status":"failed","error":"case_unreadable: Expecting property name enclosed in
#   double quotes: line 1 column 2 (char 1)"}
```

两条路径的区分正是 D01 的"首选 / 降级"两列：文件不存在 → 连输出目录都不建；
文件存在但不可解析 → 留下可诊断的 `status=failed` 记录。

## T-A7 决策规则 D05：C1 lint 反向用例 —— exit 1

```bash
# 构造一个故意违规的 spec：空标题 / 超长 bullet / 非法 layout_hint / 缺 takeaway 与 limitations
python "$SKILL_DIR/scripts/spec_lint.py" --spec "$TMP/bad-spec.json"
# exit 1  valid=false  problems=7
# 首条样本："slide #1: empty title"
```

7 条问题覆盖：空标题 / 缺 claim / `layout_hint` 不在词表 / bullet 超长 /
`evidence` 与 `evidence_gap` 双缺 / 缺 `takeaway` / 缺 `limitations`。
按 D05：先修 spec；确无法满足案例硬约束时才允许"构建继续 + 状态降 partial + 偏差双写"。

## T-A8 自定位：两种调用风格 —— 均 exit 0

```bash
# 风格 A：cwd 在别处（SKILL.md 推荐写法）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --spec "$SKILL_DIR/examples/deck-spec.json" --out "$TMP/styleA"      # exit 0
# 风格 B：cwd = 技能根，用相对路径
python scripts/main.py --case examples/case.json \
  --spec examples/deck-spec.json --out "$TMP/styleB"                    # exit 0
```

两条都通过：脚本内部用 `os.path.dirname(os.path.abspath(__file__))` 自定位并
`sys.path.insert` 自身目录，既不依赖 cwd 也不依赖相对导入。

## T-A9 控制台编码加固 —— exit 1（语义正确）且 UTF-8 可解

```bash
PYTHONIOENCODING=cp936 python "$SKILL_DIR/scripts/spec_lint.py" --spec "$TMP/bad-spec.json"
# exit 1；捕获的 stdout 可被 UTF-8 严格解码（utf8_decodable=true）
```

非 UTF-8 控制台（Windows cp936 / Linux `LC_ALL=C`）下打印中文 JSON 原本可能在
**产物已写好之后**抛 `UnicodeEncodeError`，把成功的一轮变成非零退出。现由
`scripts/cli_io.py:harden_console()` 在每个 CLI 入口把 stdout/stderr 切到 UTF-8 +
`errors="replace"`，日志不再能破坏交付。

## T-A10 `--demo` 骨架路径（无 `--spec`）—— exit 0，状态如实降级

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out "$TMP/demo" --demo
# exit 0  status=partial  spec_source="auto-skeleton (demo / missing material)"
# uncertainty=2 条  slides=6  deck.template.kind=file
```

对应不变量 I3 的精神：一旦走了骨架路径，状态就不允许写成 `completed`。

## T-A11 决策规则 D02：材料缺失 —— exit 0，产物诚实降级

```bash
# 把 case 的 material 指向不存在的文件
python "$SKILL_DIR/scripts/main.py" --case "$TMP/missing-case.json" --out "$TMP/fail"
```

| 观测项 | 实际值 |
|-|-|
| exit | `0`（自检无 error：失败被如实记录，而不是伪造产物） |
| `status` | `failed` |
| `deck` | `null` |
| `material_status` | `unreadable` |
| 语义字段 | `title=""`、`main_claim=""`、`slides=[]`（**不把骨架文案冒充真实主张**） |
| `run_meta.self_check` | `{ok: true, problems: []}` |

这条同时验证不变量 I1：材料不可读时**没有**写成 `completed`。

## T-A12 决策规则 D06/D07：模板不可用时的回退 —— exit 0

```bash
# 在一个 examples/ 下没有生成模板的副本上直接跑（模拟"案例给了模板路径但文件不存在/不可读"）
python "$SKILL_DIR2/scripts/main.py" --case "$SKILL_DIR2/examples/case.json" \
  --spec "$SKILL_DIR2/examples/deck-spec.json" --out "$TMP/notpl"
# exit 0  status=completed
# deck.template = {kind:"builtin", path:null, basename:null, layout_count:11,
#                  guard:"built-in 16:9 academic layout (no organizer template supplied)"}
# uncertainty 1 条：declared template 'template-example.pptx' was not usable — built-in
#                   16:9 academic layout used instead ...
```

回退**写进了 uncertainty**（不只是藏在 `deck.template.kind` 里），与 D07 的承诺一致。

## T-A13 决策规则 D08：页数超限 —— exit 0，如实标记

```bash
# 把 spec 的 constraints.slide_count 改成 3（spec 实际 6 页，脚本补封面/收尾后 8 页）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --spec "$TMP/overbudget-spec.json" --out "$TMP/budget"
# exit 0  status=completed  deck.page_budget_met=false  deck.slide_count=8
# uncertainty: "page budget 3 exceeded (8 slides) — trim/merge per SKILL decision rules"
```

按 D08，Agent 的下一步是合并**非证据页**并写入 `change_records`；脚本负责把
"没做到"这件事显式标出来，**绝不静默丢弃证据页**。

## T-A14 OOXML 层与主题字体 —— exit 0

```bash
python "$SKILL_DIR/scripts/ooxml_kit.py" "$TMP/out/academic_deck.pptx"
# exit 0，输出含 zip / naming / notes 三组记录
```

直接读 `ppt/theme/theme1.xml`：`Microsoft YaHei` 与 `Calibri` 均出现（两项断言均为 `true`），
即主题 major/minor 字体注入生效（换机时不丢中文字体）。

## T-A15 备注分离与预览诚实标注

| 观测项 | 实际值 |
|-|-|
| `deck.notes_included` | `true` |
| `deck.notes_separated` | `true` |
| 顶层契约字段 `notes_separated` | `true` |
| `previews` 条数 | `7`，`kind` 集合 = `{pil-approximation}` |
| `run_meta.rendered_with` | `pil-approximation (no PowerPoint/LibreOffice attached)` |
| `deck.overflow_guard` | `{max_bullets: 6, max_chars_bullet: 110}` |
| `charts` 条数 | `1`（`reconstructed_from_table`，附 SVG 可编辑源） |

## 限制（如实声明）

- 预览为 **PIL 近似渲染**，不是 PowerPoint/LibreOffice 渲染引擎结果；换机后字体可能
  被替换 —— `.pptx` 内已写主题字体（major/minor）+ run 级 latin/ea 双写缓解；
- 本机**没有 LibreOffice**，因此本次未产出真 PDF 预览（SKILL 支持检测到 `soffice` 时
  转换并改写 `run_meta.rendered_with`，对应 D13）；
- `examples/` 的论文材料是**合成示例**（ExampleNet，人物/机构/数值均虚构），
  仅验证管道正确性，与正式 3 个案例无关；
- 本记录**不含任何正式案例答案与分数声明**。
