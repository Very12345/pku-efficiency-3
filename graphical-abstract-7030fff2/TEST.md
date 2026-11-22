# TEST.md — 本地实测记录与复现判据（v2 · 合规重打包版）

> 本文件记录本包在**本机的真实执行结果**，供复核。每一次改造后都重跑并更新本表。
> 环境：Windows 10/11 · Anaconda Python **3.13.9**（命令 `python`）· matplotlib **3.10.6** ·
> Pillow **12.3.0** · 无 LibreOffice。运行目录：包外临时目录（`cwd ≠ 技能根`），
> 用于同时验证**自定位**。
>
> **重打包轮次**：2026-11-22（合规重打包，见 §R）—— 删除全部二进制/`.svg` 预置件、
> 清除绝对路径、补齐 `references/{OUTPUT_CONTRACT,RUBRIC_MAP,failure-modes}.md`、
> 新增 `scripts/check_contract.py` 与 `examples/{README,EXPECTED-OUTPUT}.md`。
> 全部命令与结果如下（原样粘贴，未美化）。

## T1 编译与导入检查 —— 通过

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py     # COMPILE OK
echo $?                                            # 0
```

`scripts/` 共 10 个 `.py`（`main/extract/figurespec/svgbuilder/preview/audit/spec_lint/
scaffold/check_contract/common`）全部通过 `py_compile`。

## T2 冒烟：示例案例默认流程 —— 通过（`status=success`）

```bash
SKILL_DIR=<包解压目录>
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <tmp>/outA
echo $?      # 0
```

`result.json` 关键字段（实测）：

```
status          : success
case_id         : example-micelle-001
plan            : {source: "none", hash: null, lint: {valid: true}}
spec_lint       : {valid: true, spec_sha16: "92a22433141dc61a",
                   counts: {elements: 113, legend_entries: 7, encoding_items: 7}}
content_summary : entities=6, relations=14, data=7,
                  panels={question:2, method:3, results:4, conclusion:3}
deliverables    : 4（editable_source/svg + layout_spec/json + preview/png + preview/pdf）
uncertainty     : []      warnings: []
four_element    : missing=[]（Q-M-R-C 全上画布）
layer_naming    : bad=[], missing=[], elements_without_src=0（7 层全绿）
entity_coverage : 6/6     encoding_consistency: 7/7    bounds.outside_count: 0
determinism     : spec_sha16=b9bcb54b29fe658d4（布局探针）
checks          : svg {ok, 7 layers} · png {ok, 2400×1600} · pdf {%PDF- ok}
```

## T3 方案先行全流程（scaffold → 方案 lint → `--plan`）—— 通过

```bash
# 1) 生成方案骨架（真实抽取实体/关系/数据并带 src）
python "$SKILL_DIR/scripts/scaffold.py" --case "$SKILL_DIR/examples/case.json" --out <tmp>/plan_skel.json
echo $?      # 0（骨架生成成功；lint.valid=false, problems=4 —— 四要素待 Agent 填充，预期行为）
#    plan_hash = 75bff8572ec6aa83

# 2) CP1 方案 lint（未定稿骨架：应 exit 1）
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan <tmp>/plan_skel.json
echo $?      # 1（problems=4：four_elements.question/method/results/conclusion missing）

# 3) CP1 方案 lint（已定稿方案：应 exit 0）
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan "$SKILL_DIR/examples/plan.example.json"
echo $?      # 0（valid=true, plan_hash=8af280bed034f42a）

# 4) 带方案出图
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
       --plan "$SKILL_DIR/examples/plan.example.json" --out <tmp>/outB
echo $?      # 0；status=success；result.plan.lint.valid=true；result.spec_lint.valid=true
```

> 说明：`spec_lint.py --lint-plan` 在重打包前**并不存在**（旧文档写了该命令但 CLI 没有该
> 参数），本轮补齐了 `--lint-plan` / `--plan`，使 `references/plan-schema.md` 与
> `SKILL.md` 的命令**逐字可执行**。

## T4 契约自查（新增 `scripts/check_contract.py`）—— 通过

```bash
python "$SKILL_DIR/scripts/check_contract.py" --result <tmp>/outA/result.json --case "$SKILL_DIR/examples/case.json"
echo $?      # 0
python "$SKILL_DIR/scripts/check_contract.py" --result <tmp>/outB/result.json --case "$SKILL_DIR/examples/case.json"
echo $?      # 0
```

实测输出（`outB`）：

```
valid                       : true
problems                    : []
envelope_keys               : 18（envelope_missing = []）
contract_fields             : 8（全部在顶层覆盖，无 null）
contract_covered_top_level  : colorblind_safe, deliverable, layer_names, provenance_attr,
                              require_legend, require_scale_bar, resolution_dpi, target_format
status                      : success      deliverables: 4      sources: 2
```

⇒ `result.json` 顶层共 **26 键** = 信封 18 + 案例 `output_contract` 8，与
`examples/EXPECTED-OUTPUT.md` §2 一致。

## T5 规格 lint 独立复跑 —— 通过

```bash
python "$SKILL_DIR/scripts/spec_lint.py" --spec <tmp>/outA/spec.json --content <tmp>/outA/content.json
echo $?      # 0（valid=true, spec_sha16=92a22433141dc61a, elements=113）
```

## T6 确定性：同输入两次运行 —— 逐字节一致

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <tmp>/det1   # exit 0
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <tmp>/det2   # exit 0
```

实测：

```
example-micelle-001_graphical_abstract.svg : same=True  sha256=370a037e2bafb9ee…
spec.json                                  : same=True  sha256=722c493b27c6b9be…
audit.determinism_probe.spec_sha16         : det1=9bcb54b29fe658d4 = det2（一致）
```

（PNG/PDF 允许字节差异——嵌入时间戳/后端版本；几何必须一致。）

## T7 自定位：`cwd` 不是技能根目录 —— 通过

```bash
cd /                     # 完全无关的 cwd
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <tmp>/outC
echo $?                  # 0
```

脚本用 `common.SCRIPT_DIR = dirname(abspath(__file__))` 自定位技能根，
`--case/--out` 全部绝对化传入；`SKILL.md` §0 与 `README.md` 的命令均按 `$SKILL_DIR` 书写。

## T8 失败分支抽查（退出码语义）—— 符合契约

```bash
python "$SKILL_DIR/scripts/main.py" --case <tmp>/nope.json --out <tmp>/nopeout
# stdout: {"status": "failed", "error": "case.json not found: …/nope.json"}
echo $?                  # 1（硬输入错误，不留半成品）
```

覆核表（`references/failure-modes.md` §1）：`main.py` 0 = 完成（success/partial）、
1 = 输入错误、2 = 内部错误；`spec_lint.py` 0/1 = 通过/有 problems；
`check_contract.py` 0/1 = 契约完整/有缺口。

## T9 随包示例产物可复现 —— 通过

用本轮新代码重跑方案先行流程，与包内 `examples/output/**` 对照（路径归一化后）：

```
result.json 键集合差异 : 无
取值差异               : 仅 generated_utc / change_records 时间戳（预期）
spec.json              : 逐字节相同
audit.json             : 逐字节相同
determinism_probe      : b863154605758e84（与包内一致）
spec_lint.spec_sha16   : bfbbe4f67df468b0（与包内一致）
```

## T10 合规验收（`validate_pkg.py`）—— PASS，0 条 FAIL

```bash
python <efficiency-3>/validate_pkg.py final/graphical-abstract-7030fff2
```

```
[PASS] graphical-abstract-7030fff2  files=36
exit=0
```

包体统计：**36 文件**（上限 50）· **280,456 B ≈ 274 KB**（上限 2 MB）·
最大单文件 **42,984 B**（`examples/output/spec.json`，上限 500 KB）·
扩展名集合 `{.md, .py, .json, .txt}`（全部在允许的 7 种之内）·
无 `__pycache__` / 无 `*.pyc` / 无二进制 / 无符号链接。

## T11 JSON 合法性与文本形态 —— 通过

```bash
python -c "import json,glob;[json.load(open(f,encoding='utf-8')) for f in glob.glob('**/*.json',recursive=True)]"
```

- 9 个 `.json` 全部为**合法 JSON**（`assets/spec_template.json` 原含裸占位符 `<数值>`，
  本轮改为 `"value": null` 并加 `_meta` 说明，使其可被 `json.load` 直接读取）；
- 全包**统一 LF 换行**、UTF-8（`assets/result_example.json`、`examples/plan.example.json`
  原为 CRLF，本轮归一化；归一化后 `plan.example.json` 的 `plan_hash` 仍为
  `8af280bed034f42a`，与包内示例产物记录一致 —— 该 hash 由 JSON 语义内容决定，与换行无关）。

## R 本轮重打包做了什么（诚实记录）

1. **删除**（均为非允许形态或本机残留）：
   - `examples/output/example-micelle-001_graphical_abstract.svg / .png / .pdf`
     （平台预检对 `.svg/.png/.pdf` 一类资源报 `unsupported Skill resource`）→ 改由
     `scripts/svgbuilder.py` + `scripts/preview.py` 运行时生成，期望清单落到
     `examples/EXPECTED-OUTPUT.md`；
   - v2 包内不存在 `__pycache__`（本轮在 `build/` 基包里有，未纳入 final）。
2. **清绝对路径**（逐条见回报）：`assets/result_example.json`、`examples/output/{result,content,render_log}.json`、
   `TEST.md`（旧记录里的本机临时构建目录路径）→ 归一化为 `examples/…` 与 `<out>/…`；
   **保留**的是字体探测候选路径字符串（`scripts/preview.py` 的 `C:/Windows/Fonts/...` 等，属跨平台探测逻辑，
   本轮另补 macOS/Linux 候选）。
3. **文档对齐**：`references/OUTPUT_CONTRACT.md`、`references/RUBRIC_MAP.md`（原小写文件名重命名，
   内容按新名与机制更新）、新增 `references/failure-modes.md`、`examples/README.md`、
   `examples/EXPECTED-OUTPUT.md`；`SKILL.md` 增加 §0 自定位调用与 §7 五维落点表，目录树改为真实形态；
   `README.md` 同步 `$SKILL_DIR` 命令与依赖说明。
4. **接口补齐**：`scripts/spec_lint.py` 增加 `--lint-plan` / `--plan`（与 `references/plan-schema.md`
   的命令逐字对齐）；新增 `scripts/check_contract.py`（契约自查，exit code 判据）；
   `scripts/preview.py` 补充 macOS/Linux 字体候选（候选探测，不改变 Windows 行为）。
5. **保持不变**：算法、CLI 参数名、结果契约、`SKILL_VERSION=2.0.0`、示例案例输入与材料
   （`examples/*.json|md` 内容未改，`sha256` 与旧示例一致：task.md `820241cb102c…`、
   material.md `9cde8c17a78e…`）。
6. **文本规范化**：`assets/spec_template.json` 修正为合法 JSON；两个 CRLF 文件归一化为 LF
   （见 T11）。

## 限制（如实声明）

- 渲染后端本文档实测为 matplotlib；无 matplotlib/Pillow 的环境会自动降级
  （Pillow → 纯 Python PNG，文字占位并注明），方法见 `references/failure-modes.md` §4；
- 实体抽取依赖材料文本结构；复杂表格/多图材料需要 Agent 复核抽取结果；
- 示例材料与结果均为合成（标注"示例，非正式案例"），与平台正式案例无关；
- 本轮**未做**平台提交、未联网、未改动 `submit/`、`build/`、`target/`、`publish/`、`traces/`。
