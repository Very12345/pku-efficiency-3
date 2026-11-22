# TEST.md — 本机实测、注入矩阵复跑与验收判据

> 全部命令在**包外副本**上执行（`cp -r <技能根> <临时目录>/pkg`），
> 因为任何脚本在包内跑都会生成 `__pycache__`，平台预检会因此拒收整包。
> 下文 `$PKG` = 包外副本的技能根，`$WORK` = 包外可写工作目录。
> 本机环境：Windows + Python 3.13 + python-pptx 1.0.2 + matplotlib 3.10.6 +
> Pillow 12.3.0 + reportlab 5.0.0。

## T1 编译与导入 —— 通过

```bash
python -m py_compile "$PKG"/scripts/*.py && echo OK
python -c "import sys; sys.path.insert(0,'$PKG/scripts'); import deck_common, deck_extract, slide_text, deck_tool, render_qa, evidence_check, result_tool, selftest, main, fault_inject; print('imports OK')"
```
实测输出：`OK` / `imports OK`（10 个脚本，含本版新增的 `fault_inject`）。

## T2 冒烟：示例案例端到端（**验收主命令**）—— 通过（exit 0）

```bash
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$WORK/out"
```
```
INFO material_status=ok sections=8 tables=1
INFO deck built: <WORK>/out/work/deck.pptx (6 pages)
INFO STATUS=success ok_checks=7/7 cp={'cp1_extract': True, 'cp2_plan': True, 'cp3_build': True, 'cp4_verify': True}
STATUS=success case_id=ppt-6ad93034-example-001 deck=work/deck.pptx slides=6
```
`exit=0`。`result.json` 顶层 **18 个键**：
`case_id, title, status, created_at, skill_version, deck, evidence, previews, sources,
uncertainty, change_records, log, checks, evidence_map_json, manifest, environment,
is_example, run_meta`（`is_example` 来自 `output_contract` 回显）。
产出文件 **25 个**（清单见 `examples/EXPECTED-OUTPUT.md`）。

## T3 契约门与自检 —— 均通过（exit 0）

```bash
python "$PKG/scripts/result_tool.py" --result "$WORK/out/result.json" \
    --out-dir "$WORK/out" --case "$PKG/examples/case.json" \
    --envelope "$PKG/templates/result_envelope.json"
# {"valid": true, "errors": [], "warnings": [], "gates": {G1..G8 全 true}}   exit 0

python "$PKG/scripts/selftest.py" --out "$WORK/out" --case "$PKG/examples/case.json"
# all_pass: true（7/7）                                                       exit 0
```
实测：`valid=True errors=0 warnings=0 gates={'G1'..'G8' 全 True}`；
`all_pass=True checks=7`，未通过项 `[]`。

## T4 编辑模式 + 版本归档 —— 通过（exit 0）

```bash
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$WORK/out" \
    --edit "$PKG/examples/edit_demo.json" --version v2
```
实测 `exit=0`，`$WORK/out/work/` 下 **`deck.pptx` 与 `deck_v2.pptx` 并存**；
`change_records` 由 1 条（start）增至 4 条（3 条编辑 + build）。

## T5 页数变体（`--max-slides 10`）—— 通过（exit 0）

```bash
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$WORK/out10" --max-slides 10
# slides=10
```
实测 `slides=10`、`exit=0`；角色序列按 DECK_SPEC 富余页规则插入背景/讨论/局限。

## T6 图表降级（`--no-chart`）—— 通过（exit 0）

```bash
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$WORK/outnc" --no-chart
```
实测 `exit=0`、`slides=6`；结果页 `figure.kind` 由 `chart_image` 变为
**`table`（PPTX 原生可编辑表格）+ `note`**，`uncertainty` 记一条降级原因。

## T7 负路径：三族真实降级（`FAULT-MATRIX.md` 的口径）

### T7a 材料缺失 → D1 —— 通过（exit 1）

```bash
# case 的 inputs.material 指向不存在的文件：["does-not-exist.md"]
python "$PKG/scripts/main.py" --case "$WORK/miss/case.json" --out "$WORK/miss/out"
# STATUS=partial case_id=ppt-6ad93034-missing-001 deck= slides=0     exit 1
```
实测：`status=partial`、`slide_count=0`、`evidence.material_warnings=2`、`uncertainty=1`。
**没有编造任何 deck**（D1 的诚实路径）。

### T7b case.json 不可读 —— 通过（exit 2）

```bash
python "$PKG/scripts/main.py" --case "$WORK/miss/nope.json" --out "$WORK/miss/out2"
# ERROR case load failed: 找不到 case 文件: <path>                    exit 2
```
实测 `exit=2`，仍写出了最小 `status=failed` 的 `result.json`（`error` 字段带原因）。

### T7c 数字核验负例 → D2 —— 通过（exit 1）

```bash
python "$PKG/scripts/evidence_check.py" --claim "准确率达到 99.9%" --material "$PKG/examples/material.md"
# ok=False missing=['99.9%']                                        exit 1

python "$PKG/scripts/evidence_check.py" --claim "S2-Attn 在三态精度上达到 82.4%" --material "$PKG/examples/material.md"
# ok=True missing=[]                                                exit 0
```
实测：材料里没有的数字报 `missing`（exit 1）；材料里有的数字 exit 0。

## T8 失败注入矩阵：28 条故障（**本版核心实测**）

```bash
python "$PKG/scripts/fault_inject.py" --pkg "$PKG" --work "$WORK/fw" --with-recovery \
    --report-json "$WORK/fw.json"
```

实测（完整逐行矩阵见 `references/FAULT-MATRIX.md` §1）：

| 统计项 | 实测值 |
|-|-|
| 故障条数 | 28（input 10 / template 7 / dependency 5 / contract 6） |
| 总耗时 | 约 60 秒（每条 1–3 秒） |
| exit 分布 | `0 × 14` / `1 × 10` / `2 × 4` |
| status 分布 | `success × 15` / `partial × 5` / `failed × 4` / 未写出 result.json × 4 |
| 留痕等级 | `product × 19` / `stdout-only × 4` / `none × 5` |
| **静默失败** | **7 条**：`F-IN-07` `F-TPL-03` `F-TPL-05` `F-DEP-03` `F-DEP-04` `F-DEP-05` `F-CTR-03` |
| 与设计期望偏离 | 4 条：`F-IN-07` `F-TPL-03` `F-TPL-06` `F-DEP-03` |
| deck 可重开 | 建了 deck 的 14 条 **14/14 可重开且页数=result** |
| 恢复动作 | 17 条有恢复动作，**17/17 恢复或被守卫判定** |

工具退出码：`exit=1`（有静默失败/偏离 —— 这是**如实的**：本包确实还有 7 条缺口，
本版选择"测出来 + 给守卫"，而不是假装 0 条）。

## T9 守卫：运行前体检 + 运行后核对（**本版核心实测之二**）

```bash
# 运行前（健康输入）
python "$PKG/scripts/fault_inject.py" --guard --pkg "$PKG" --case "$PKG/examples/case.json"
#   OK  未发现问题 / 守卫结论: 通过                                exit 0

# 运行前（坏模板形态：--template 是数组）
python "$PKG/scripts/fault_inject.py" --guard --pkg "$PKG" --case <bad>/case.json \
    --template <bad>/list_template.json
#   BLOCKER [template] --template 的 JSON 顶层不是对象（list）…    exit 1

# 运行后（健康产物）
python "$PKG/scripts/fault_inject.py" --guard --out "$WORK/out"
#   OK  未发现问题 / 守卫结论: 通过                                exit 0

# 运行后（图表静默消失的产物：材料有数据表但成稿无图表、无 note）
python "$PKG/scripts/fault_inject.py" --guard --out "$WORK/fw/runs/F-IN-07/out"
#   WARN [figure] 材料里有 1 张数据表，但成稿里既没有图表/表格、也没有任何 note … exit 1

# 运行后（硬崩、没有 result.json）
python "$PKG/scripts/fault_inject.py" --guard --out "$WORK/fw/runs/F-DEP-03/out"
#   BLOCKER [result] 输出目录里没有 result.json（运行未落盘）        exit 1
```

**可信度实测**：守卫跑 28 条故障产物 → **7 条静默失败 7/7 被抓到**；
跑健康产物 → **0 误报**。两者都能用上面的命令复现。

## T10 确定性：同输入双跑 —— 内容级一致

```bash
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$WORK/d1"
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$WORK/d2"
# 逐字段对比 result.json（忽略时间戳/日志名/sha/路径）
```
实测：**只有 2 处差异** —— `log`（日志文件名带时间戳）与 `run_meta.timestamp`；
页序、角色、主张、证据、图表、备注、契约回显**逐字段一致**。
（`--edit` 的版本号与 `edit_mode` 会随参数变化，那是输入差异，不是不确定性。）

## T11 包体自检（提交前必跑）

```bash
# 1) 合规验收器：期望 PASS，0 条 FAIL
python validate_pkg.py <技能根>

# 2) 本机绝对路径残留（任意盘符 + 分隔符）：期望只命中"无"
#    （fault_inject.py 生成的报告已自动净化绝对路径，可放心落盘分发）

# 3) 无 __pycache__ / *.pyc：
find <技能根> -name __pycache__ -o -name '*.pyc'      # 期望空输出

# 4) 文件数 / 体积：
find <技能根> -type f | wc -l                          # 期望 ≤50
```

## T12 SKILL.md frontmatter（平台预检硬门）

```bash
head -3 "$PKG/SKILL.md"     # 第一行必须是 ---，且在 frontmatter 内有 name: 与 description:
```
实测：首行 `---`、含 `name: academic-ppt-builder-fault-hardened` 与 `description: …`。
（平台预检实测口径：**缺合法 YAML frontmatter 直接拒收、不进沙箱**。）

## 验收对照

| 项 | 判据 | 本机实测 |
|-|-|-|
| 主流程 | `main.py` exit 0 且 `status=success` | ✅ exit 0 / success / 6 页 |
| 契约门 | `result_tool.py` `valid=true` 且 exit 0 | ✅ G1–G8 全 True |
| 产物自检 | `selftest.py` `all_pass=true` | ✅ 7/7 |
| 契约覆盖 | `result.json` 顶层含 `OUTPUT_CONTRACT.md` 的全部字段且无 null | ✅ 18 个顶层键 |
| 自定位 | cwd 不是技能根也能跑（命令全用 `$SKILL_DIR`） | ✅ 全部命令均以包外 cwd 执行 |
| 编辑/回退 | `--edit --version v2` 产生 `deck_v2.pptx` 且 changelog 有记录 | ✅ 4 条 change_records |
| 降级留痕 | 图表降级/预览缺失/材料问题分别落到 `figure.note`/`previews.warnings`/`material_warnings` | ✅ T6/T7a |
| **注入矩阵** | 28 条故障逐行有 exit/status/留痕/静默 判定 | ✅ 见 `FAULT-MATRIX.md` §1 |
| **恢复演练** | 有恢复动作的故障都跑出恢复后状态 | ✅ 17/17 |
| **静默可发现** | 守卫能抓到全部静默失败且健康产物 0 误报 | ✅ 7/7 抓到、0 误报 |
| 包体 | ≤50 文件 / ≤2MB / 7 种文本扩展名 / 无 `__pycache__` / 无绝对路径 | 见 T11 |

## 已知限制（本机验证结论）

1. 注入台**只覆盖上游输入面**（输入/模板/依赖/契约四族）；并发与中断、畸形但合法的 PPTX、
   GB 级材料、真机 Office 渲染、平台预检都**没有注入**（`FAULT-MATRIX.md` §5 逐条列明）。
2. `fault_inject.py` 的依赖屏蔽用的是 `sitecustomize.py` + `sys.meta_path`，
   只能屏蔽**Python 层 import**；C 扩展已加载时（同进程内先 import 过）无法再屏蔽。
   本台的每条故障都在**新进程**里跑，因此不受影响。
3. 7 条静默缺口仍在（`FAULT-MATRIX.md` §2）。本版给的是**可发现性**，不是根治。
4. 注入台整套 28 条约 60 秒，**属于开发期工具**；不要放进平台的 900 秒评测预算里跑。
