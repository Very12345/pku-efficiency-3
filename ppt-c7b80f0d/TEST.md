# TEST.md — 本机实测记录（运行者：重打包子代理 agent-66，2026-11-22 +08）

> 本文件记录**本包交付版本**的真实执行结果，含命令、退出码与关键输出，供复核。
> 环境：Windows 11 / Anaconda Python 3.13.9（命令 `python`）/
> python-pptx 1.0.2、Pillow 12.3.0、matplotlib 3.10.6、PyMuPDF(fitz) 1.28.0、
> pypdf 6.14.2；**无 LibreOffice** —— 预览一律 PIL 近似渲染并如实标注。
>
> 全部命令都在**包外的临时副本**上执行（把本包复制到临时目录后，以该副本为
> `$SKILL_DIR`，输出写到另一个临时目录 `$TMP/...`），
> 且 cwd 固定为 `/tmp`（**不是**技能根目录），用于同时验证 SKILL.md 的
> `$SKILL_DIR` 自定位写法。包内不写入任何测试产物。

## T1 运行期生成示例模板 —— 通过（exit 0）

```bash
cd /tmp
python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"
# status=ok  bytes=28420  starter_slides=1
# renamed_layouts=[{8: "Picture with Caption" -> "Figure Slide"},
#                  {5: "Title Only"          -> "Reference Slide"}]
# layouts=11 个（含上面两个改名后的布局）
```

模板为**运行期生成**：包内不携带任何 `.pptx`（技能资源只允许 UTF-8 文本文件）。

## T2 端到端冒烟（示例案例）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" --spec "$SKILL_DIR/examples/deck-spec.json" \
  --out "$TMP/out"
```

输出摘要：

```
case_id      : example-ppt-c7b80f0d
status       : completed
deck         : academic_deck.pptx (8 slides)
previews     : 7 files
evidence_map : evidence_mapping.md (entries=6, gaps=0)
spec_lint    : OK
sources      : 1  uncertainty: 0  changes: 2
self_check   : OK
```

产出文件 13 个：`result.json`、`academic_deck.pptx`、`chart-Fig_1.png`、
`chart-Fig_1.svg`、`evidence_mapping.md`、`evidence_map.json`、
`preview-approx-cover.png` + `preview-approx-001..006.png`。

模板适配复核：`template.kind=file`、`starter_slides_removed=1`（`template_mode=replace`）、
`layouts_used={"Title Slide":1,"Title and Content":5,"Figure Slide":1,"Reference Slide":1}`；
备注 8/8 页（含封面/收尾）；`theme_fonts.applied=true`。

## T3 两道交付门 —— 通过（均 exit 0）

```bash
python "$SKILL_DIR/scripts/export_check.py" --result "$TMP/out/result.json" \
  --out-dir "$TMP/out" --case "$SKILL_DIR/examples/case.json"
# exit 0 -> {"valid": true, "errors": [], "warnings": [], "status": "completed"}

python "$SKILL_DIR/scripts/check_contract.py" --result "$TMP/out/result.json" \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case "$SKILL_DIR/examples/case.json"
# exit 0 -> {"valid": true, "fields_contracted": 19, "fields_present": 19, "missing": [],
#            "case_contract_missing": []}
```

`result.json` 顶层 19 个键与 `references/OUTPUT_CONTRACT.md` §1 清单**逐条对齐**：
`case_id, task, status, output_contract, deck, evidence_mapping, evidence_map_json,
spec_lint, previews, charts, sources, uncertainty, change_records, run_meta,
title, main_claim, slides, render_state, notes_separated`。

## T4 内容确定性（同输入两次运行）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case .../case.json --spec .../deck-spec.json --out "$TMP/out2"
# 对比 out/ 与 out2/ 的 academic_deck.pptx：
# parts=72/72  differing=[]   -> 全部 72 个 OPC 部件 sha256 逐部件一致
```

（比 v2 记录更强：v2 需把 zip 时间戳归一再比哈希；本次部件内容已完全一致。）

## T5 运行期合成夹具 + PDF 抽取链路 —— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --out "$TMP/synth"
# exit 0  status=ok
# generated=[("placeholder_png","Pillow",32797), ("synthetic_pdf","pymupdf",3062)]  skipped=[]

python "$SKILL_DIR/scripts/assetkit.py" --pdf "$TMP/synth/synthetic-two-page.pdf" --out "$TMP/extract"
# exit 0  {"status":"ok","tool":"pymupdf","pages_parsed":2,"text_chars":589,
#          "images_extracted":0,"text_file":"text\\synthetic-two-page.txt"}
```

抽取文本含页标记 `[PAGE 1]` / `[PAGE 2]`。占位图为**纯几何框**（边框 + 对角线 +
"NOT RESEARCH DATA" 文案），**不含坐标轴/数值**，不会被误认成科研数据。

## T6 `--demo` 骨架路径（无 `--spec`）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out "$TMP/demo" --demo
# exit 0  status=partial  template.kind=file  slide_count=6
# spec_source="auto-skeleton (demo / missing material)"
# uncertainty=["this run is a DEMO skeleton; not a formal case result",
#              "some slides carry explicit evidence gaps: SPINE 问题→方法→证据→结论"]
```

**本项修掉一个真实崩溃**：`--demo` 未传 `--spec` 时，`_resolve_template_path` 会对
`None` 基目录调用 `os.path.join` → `TypeError`，整轮直接中断（见 T11 第 1 条）。

## T7 材料缺失的诚实失败路径 —— 通过（exit 0，状态如实降级）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$TMP/missing-case.json" --out "$TMP/fail"
# exit 0（自检无 error：失败被如实记录，而不是伪造产物）
# status=failed  deck=None  material_status=unreadable
# 契约语义字段= {title:"", main_claim:"", slides:[]}（不把骨架文案冒充真实主张）
# 允许为 null 的仅 deck / evidence_map_json
```

## T8 输入不可用的两种情形 —— 通过（exit 3）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$TMP/broken-case.json" --out "$TMP/broken"
# exit 3；仍写出 result.json：{"status":"failed","error":"case_unreadable: ..."}

python "$SKILL_DIR/scripts/main.py" --case "$TMP/nope.json" --out "$TMP/nope"
# exit 3；不创建输出目录、不产出任何文件（没有输入就不发明产物）
```

## T9 `spec_lint` 反向用例 —— 通过（exit 1）

```bash
python "$SKILL_DIR/scripts/spec_lint.py" --spec "$TMP/bad-spec.json"
# exit 1  valid=false  problems=7
# 覆盖：空标题 / 缺 claim / layout_hint 不在词表 / bullet 超长 /
#       evidence 与 evidence_gap 双缺 / 缺 takeaway / 缺 limitations
```

## T10 主题字体注入（CJK 安全）—— 通过（实际写进了 .pptx）

```bash
python -X utf8 -c "..."   # 直接读 out/academic_deck.pptx 内 ppt/theme/theme1.xml
# [('majorFont','Calibri','Microsoft YaHei'), ('minorFont','Calibri','Microsoft YaHei')]
```

**本项修掉一个真实缺陷**：python-pptx 把 `theme1.xml` 载入为**泛型 Part**（无 `.element`），
旧写法取到该 Part 后访问 `.element` 抛异常，导致字体注入静默失败、只留下一句
uncertainty。现改为「定位主题 Part → 按 XmlPart/泛型 Part 两种形态读写」，
注入结果同时写入 `deck.theme_fonts`（`applied=true`、`part=/ppt/theme/theme1.xml`）。

## T11 控制台编码加固 —— 通过

```bash
PYTHONIOENCODING=cp936 python "$SKILL_DIR/scripts/spec_lint.py" --spec bad-spec.json
# exit 1；捕获的 stdout 可被 UTF-8 严格解码（utf8-ok: True）
```

在非 UTF-8 控制台（Windows cp936 / Linux `LC_ALL=C`）下，打印中文 JSON 原本可能在
**产物已写好之后**抛 `UnicodeEncodeError`，把成功的一轮变成非零退出；现由
`scripts/cli_io.py:harden_console()` 在每个 CLI 入口把 stdout/stderr 切到 UTF-8 +
`errors="replace"`，日志不再能破坏交付。

## T12 本次重打包修掉的缺陷（诚实记录）

| # | 现象 | 处置 |
|-|-|-|
| 1 | `--demo` 无 `--spec` 时 `os.path.join(None, ...)` → TypeError，整轮崩溃 | `_resolve_template_path` 跳过空基目录 |
| 2 | `result.json` 缺顶层 `output_contract` 容器（文档要求 19 字段，代码只回显语义字段） | `apply_output_contract` 先回显声明容器；`main.py` 自检引入 `check_contract` 后**当场发现该漂移** |
| 3 | 主题字体注入必然失败（泛型 Part 无 `.element`） | `ooxml_kit` 增加 `_find_theme_part/_theme_root/_store_root`，并对泛型 Part 写回 blob |
| 4 | `run_meta.checkpoints.cp3_export_check` 永远为 `null` | 自检结束后写回真实布尔 |
| 5 | 材料不可读时，契约语义字段回显骨架文案（`main_claim="SKELETON"`） | 失败且非 demo 的运行传 `spec=None`，语义字段按类型给空值 |
| 6 | 非 UTF-8 控制台下打印中文可能崩 | 新增 `scripts/cli_io.py`，各 CLI 入口调用（T11） |
| 7 | `check_contract` 的契约文档读取失败会“静默通过” | 解析不到字段即 exit 2 并报错，绝不假通过 |
| 8 | 声明了模板但模板不可用时，静默回退内置版式（只在 `deck.template.kind` 里体现，`uncertainty` 不记） | 回退时显式写入 `uncertainty`，与 SKILL.md D11 / `failure-modes.md` §2.2 的承诺一致 |

## T13 模板不可用时的回退（声明了模板但未生成）—— 通过（exit 0）

```bash
# 先不生成模板，直接跑（模拟"案例给了模板路径但文件不存在/不可读"）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --spec "$SKILL_DIR/examples/deck-spec.json" --out "$TMP/notpl"
# exit 0  status=completed  deck.template.kind=builtin
# uncertainty=["declared template 'template-example.pptx' was not usable — built-in 16:9
#              academic layout used instead (deck.template.kind=builtin); run
#              make_template.py if a real .pptx template is needed"]
# 两道门仍全过：export_check exit 0 / check_contract 19-19 exit 0
```

## T14 两种调用风格都能跑（自定位验证）—— 通过

```bash
# 风格 A：cwd 不是技能根（推荐，SKILL.md 用这种写法）
cd /tmp && python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" ...
# exit 0

# 风格 B：cwd = 技能根，用相对路径
cd "$SKILL_DIR" && python scripts/main.py --case examples/case.json --spec examples/deck-spec.json --out <tmp>
# exit 0；spec_lint / export_check 同样 exit 0
```

两种风格都可用：脚本内部用 `os.path.dirname(os.path.abspath(__file__))` 自定位并
`sys.path.insert` 自身目录，因此既不依赖 cwd，也不依赖相对导入。

## 限制（如实声明）

- 预览为 **PIL 近似渲染**，不是 PowerPoint/LibreOffice 渲染引擎结果；换机后字体可能
  被替换 —— `.pptx` 内已写主题字体（major/minor）+ run 级 latin/ea 双写缓解；
- 本机无 LibreOffice，未能在本机生成真 PDF（SKILL 支持检测到 `soffice` 时转换并改写
  `run_meta.rendered_with`）；
- `examples/` 的论文材料为**合成示例**（ExampleNet，人物/机构/数值均虚构），
  仅验证管道正确性，与正式 3 个案例无关；
- 本记录不含任何正式案例答案与分数声明。
