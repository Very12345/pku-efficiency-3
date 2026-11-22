# TEST.md — 本机实测、泛化台复跑与验收判据

> 全部命令在**包外副本**上执行（`cp -r <技能根> <临时目录>/pkg`），
> 因为任何脚本在包内跑都会生成 `__pycache__`，平台预检会因此拒收整包。
> 下文 `$PKG` = 包外副本的技能根，`$WORK` = 包外可写工作目录。
> 本机环境：Windows + Python 3.13 + python-pptx 1.0.2 + matplotlib 3.10.6 +
> Pillow 12.3.0 + reportlab 5.0.0。

## T1 编译与导入 —— 通过

```bash
python -m py_compile "$PKG"/scripts/*.py && echo OK
python -c "import sys; sys.path.insert(0,'$PKG/scripts'); import deck_common, deck_extract, slide_text, deck_tool, render_qa, evidence_check, result_tool, selftest, main, case_check; print('imports OK')"
```
实测：`OK` / `imports OK`（10 个脚本，含本版新增的 `case_check`）。

## T2 冒烟：示例案例端到端（**验收主命令**）—— 通过（exit 0）

```bash
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$WORK/out"
# STATUS=success case_id=ppt-6ad93034-example-001 deck=work/deck.pptx slides=6
```
实测 `exit=0`、`status=success`、6 页、`result.json` 顶层 **18 个键**、产出 **25 个文件**。

## T3 契约门与自检 —— 均通过（exit 0）

```bash
python "$PKG/scripts/result_tool.py" --result "$WORK/out/result.json" \
    --out-dir "$WORK/out" --case "$PKG/examples/case.json" \
    --envelope "$PKG/templates/result_envelope.json"
# {"valid": true, "errors": [], "warnings": [], "gates": {G1..G8 全 true}}   exit 0
python "$PKG/scripts/selftest.py" --out "$WORK/out" --case "$PKG/examples/case.json"
# all_pass: true（7/7）                                                       exit 0
```

## T4 编辑模式 + 版本归档 —— 通过（exit 0）

```bash
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$WORK/out" \
    --edit "$PKG/examples/edit_demo.json" --version v2
```
实测 `exit=0`；`work/` 下 `deck.pptx` 与 `deck_v2.pptx` **并存**；
`change_records` 从 1 条（start）增至 4 条。

## T5 页数变体（`--max-slides 10`）—— 通过（exit 0）

```bash
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$WORK/out10" --max-slides 10
# slides=10
```

## T6 图表降级（`--no-chart`）—— 通过（exit 0）

```bash
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$WORK/outnc" --no-chart
```
实测 `exit=0`；结果页 `figure.kind` 由 `chart_image` 变为 `table`（PPTX 原生可编辑表格）+ `note`。

## T7 负路径：三族真实降级

### T7a 材料缺失 → D1 —— 通过（exit 1）

```bash
# inputs.material 指向不存在的文件：["does-not-exist.md"]
# STATUS=partial case_id=ppt-6ad93034-missing-001 deck= slides=0     exit 1
```
实测 `slide_count=0`、`material_warnings=2`、`uncertainty=1`，**没有编造 deck**。

### T7b case.json 不可读 —— 通过（exit 2）

```bash
python "$PKG/scripts/main.py" --case "$WORK/miss/nope.json" --out "$WORK/miss/out2"
# ERROR case load failed: 找不到 case 文件: <path>                    exit 2
```
实测仍写出最小 `status=failed` 的 `result.json`（`error` 字段带原因）。

### T7c 数字核验负例 → D2 —— 通过（exit 1）

```bash
python "$PKG/scripts/evidence_check.py" --claim "准确率达到 99.9%" --material "$PKG/examples/material.md"
# ok=False missing=['99.9%']                                        exit 1
```

## T8 ★ 泛化台：两个题材逐案实测（**本版核心实测之一**）

```bash
python "$PKG/scripts/case_check.py" --pkg "$PKG" --work "$WORK/cases" \
    --report-json "$WORK/cases.json" --report-md "$WORK/cases.md"
#   case-a-perovskite        exit=1 status=partial  slides=8  判定=PASS
#       已知缺口(advisory，不计入失败): unverified_claims_max[unverified=1 ≤ 0]
#   case-b-climate-text      exit=1 status=partial  slides=6  判定=PASS
#       已知缺口(advisory，不计入失败): must_mention_in_deck[缺失=['2009', '2015']]
# 案例判定: 全部 PASS（2 个案例）
```

实测数值（完整表见 `references/CASE-SET.md` §2）：

| 观测量 | 案例 A（实验科学） | 案例 B（理论文本） |
|-|-|-|
| exit / status | `1` / `partial` | `1` / `partial` |
| slide_count | 8 | 6 |
| 角色序列 | `cover→overview→background→discussion→question→method→result→takeaway` | `cover→overview→question→method→result→takeaway` |
| 图表形态 | `chart_image ×1` + `none ×7`（`table_id=jv.csv`，8 行原样重绘） | **`none ×6`**（0 张编造图） |
| unverified / material_warnings / uncertainty | 1 / 0 / 0 | 1 / 0 / 0 |
| 备注覆盖 / 脚注覆盖 | 1.0 / 1.0 | 1.0 / 1.0 |
| gate / selftest / deck 重开 | `true` / `true` / 8 | `true` / `true` / 6 |
| `result.json` 顶层键数 | 20 | 20 |
| 硬判据 | **12/12 PASS** | **11/11 PASS** |
| advisory 缺口 | `unverified_claims_max`（材料缺"背景"小节所致） | `must_mention_in_deck`（缺 `2009/2015`） |

## T9 ★ 四种边界探针（**本版核心实测之二**）

```bash
python "$PKG/scripts/case_check.py" --pkg "$PKG" --work "$WORK/cases" --probes
#  P1 两张数据表（材料给了两个 CSV）        exit=1 status=partial slides=8  fig=chart_image,none unv=1
#  P2 材料没有任何章节标题（纯段落）        exit=1 status=partial slides=8  fig=chart_image,none unv=3
#  P3 页数上限压到 3（材料内容远超）        exit=0 status=success slides=3  fig=chart_image,none unv=0
#  P4 用 --edit 往页面塞材料里没有的数字    exit=1 status=partial slides=8  fig=chart_image,none unv=2
```

| # | 变形 | 关键实测细节 | 结论 |
|-|-|-|-|
| P1 | 材料给两张 CSV | `material_view` 登记两张（`jv.csv` 8 行、`jv_second.csv` 8 行），页面**只用 `jv.csv`**，第二张被忽略且无 `uncertainty` | ❌ 多表只认第一张（GAP-P1） |
| P2 | 删掉所有章节标题 | 占位主张 1→3 条；`uncertainty` 记 `page 2 bullet too long (CJK-weighted=162 vs limit=90)` | ⚠️ 降级路径**有留痕**（D4 生效） |
| P3 | `max_slides=3` | 角色压成 `cover→overview→result`，`change_records` 只有 `start` | ⚠️ 压缩不留痕（GAP-P3） |
| P4 | `--edit` 塞入 `31.7%` | `unverified_claims` 1→2，含 `missing_numbers=["31.7%"]`；`change_records` 记 `{version: probe, op: update_bullet, page: 8}` | ✅ 编辑链路仍过 D2 |

## T10 确定性：同输入双跑 —— 内容级一致

```bash
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$WORK/d1"
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$WORK/d2"
# 逐字段对比 result.json（忽略时间戳/日志名/sha/路径）
```
实测：**只有 2 处差异** —— `log`（日志文件名带时间戳）与 `run_meta.timestamp`；
页序、角色、主张、证据、图表、备注、契约回显逐字段一致。

## T11 契约形态负路径与静默跳过（**与泛化台互补的诚实实测**）

```bash
# 把 output_contract 写成字符串（形态错误）
python "$PKG/scripts/main.py" --case <bad-case>/case.json --out "$WORK/out-bad-ctr"
```
实测：`exit=0`、`status=success`、`uncertainty=[]`，
`result.json` 里**契约字段一个都没回显**，而 G2 也不报错
（`validate()` 只在 `isinstance(oc, dict)` 时逐字段核）。
⇒ **这是本包的已知缺口**，与 `FAULT-MATRIX` 家族的 S2 同源；
写案例时务必把 `output_contract` 写成对象或字段名列表。

## T12 包体自检与 frontmatter（提交前必跑）

```bash
python validate_pkg.py <技能根>                        # 期望 PASS，0 条 FAIL
find <技能根> -name __pycache__ -o -name '*.pyc'        # 期望空输出
find <技能根> -type f | wc -l                           # 期望 ≤50
head -3 "$PKG/SKILL.md"                                 # 首行 ---，含 name: 与 description:
```
实测：`PASS`；无 `__pycache__`；首行 `---`、含
`name: academic-ppt-builder-case-generalized` 与 `description: …`。

## 验收对照

| 项 | 判据 | 本机实测 |
|-|-|-|
| 主流程 | `main.py` exit 0 且 `status=success` | ✅ exit 0 / success / 6 页（示例案例） |
| 契约门 | `result_tool.py` `valid=true` 且 exit 0 | ✅ G1–G8 全 True |
| 产物自检 | `selftest.py` `all_pass=true` | ✅ 7/7 |
| 契约覆盖 | 顶层含 `OUTPUT_CONTRACT.md` 全部字段且无 null | ✅ 18 键（示例）/ 20 键（两案例） |
| 自定位 | cwd 不是技能根也能跑 | ✅ 所有命令都在包外 cwd 执行 |
| 编辑/回退 | `--edit --version v2` 产生 `deck_v2.pptx` 且留记录 | ✅ 4 条 change_records |
| **逐案判定** | 两个题材都过 `_case_set.expect` | ✅ 12/12 与 11/11 |
| **诚实降级** | 无表题材不出现 `chart_image`；缺小节时允许 `partial` | ✅ `none ×6`；两案 `partial` 且原因可查 |
| **边界可见** | 四种探针都能跑出结论，缺口被记录而非被隐藏 | ✅ P1–P4 + 7 条 GAP |
| 包体 | ≤50 文件 / ≤2MB / 7 种文本扩展名 / 无 `__pycache__` / 无绝对路径 | 见 T12 |

## 已知限制（本机验证结论）

1. **案例只有 2 个题材**：实验科学（有表）与理论文本（无表）；
   医学统计、工程图纸、教学课件等形态**没有覆盖**。
2. **判定是结构+覆盖判据**：能证明"页数对、角色在、备注全、没编造"，
   **不能证明讲得好**——那需要人工评审。
3. **7 条泛化失效边界仍在**（`CASE-SET.md` §3）：本版给的是"测出来 + 写清楚 + 规避做法"，
   不是根治。
4. 泛化台跑 2 个案例约 5 秒、加探针约 12 秒，**属开发期工具**，
   不要放进平台 900 秒评测预算里跑。
