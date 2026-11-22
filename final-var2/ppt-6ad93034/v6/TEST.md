# TEST.md — 本机实测、四个台复跑与验收判据（总集成版）

> 全部命令在**包外副本**上执行（`cp -r <技能根> <临时目录>/pkg`），
> 因为任何脚本在包内跑都会生成 `__pycache__`，平台预检会因此拒收整包。
> 下文 `$PKG` = 包外副本的技能根，`$WORK` = 包外可写工作目录。
> 本机环境：Windows + Python 3.13.9 + python-pptx 1.0.2 + matplotlib 3.10.6 +
> Pillow 12.3.0 + reportlab 5.0.0。

## T1 编译与导入 —— 通过

```bash
python -m py_compile "$PKG"/scripts/*.py "$PKG"/references/*.py && echo OK
python -c "import sys; sys.path.insert(0,'$PKG/scripts'); import deck_common, deck_extract, slide_text, deck_tool, render_qa, evidence_check, result_tool, selftest, main, fault_inject, case_check; print('imports OK')"
```
实测：`OK` / `imports OK`（12 个脚本：10 个主链 + `fault_inject` + `case_check`；
`references/` 下另有 `measure_gain.py`、`mechanism_probe.py` 两个包外工具）。

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

## T7 负路径：材料缺失 / case 不可读 / 数字核验负例

```bash
# T7a 材料缺失（D1）
# STATUS=partial case_id=ppt-6ad93034-missing-001 deck= slides=0     exit 1
#     实测 slide_count=0、material_warnings=2、uncertainty=1，没有编造 deck

# T7b case.json 不可读
# ERROR case load failed: 找不到 case 文件: <path>                    exit 2
#     实测仍写出最小 status=failed 的 result.json（error 字段带原因）

# T7c 数字核验负例（D2）
python "$PKG/scripts/evidence_check.py" --claim "准确率达到 99.9%" --material "$PKG/examples/material.md"
# ok=False missing=['99.9%']                                        exit 1
```

## T8 ★ 注入台：四族 28 条故障（**实测之一**）

```bash
python "$PKG/scripts/fault_inject.py" --pkg "$PKG" --work "$WORK/fw" --with-recovery \
    --report-json "$WORK/fw.json"
```

| 统计项 | 实测值 |
|-|-|
| 故障条数 / 总耗时 | 28（input 10 / template 7 / dependency 5 / contract 6）/ 约 60 秒 |
| exit 分布 | `0 × 14` / `1 × 10` / `2 × 4` |
| status 分布 | `success × 15` / `partial × 5` / `failed × 4` / 未写出 `result.json` × 4 |
| 留痕等级 | `product × 19` / `stdout-only × 4` / `none × 5` |
| **静默失败** | **7 条**：`F-IN-07` `F-TPL-03` `F-TPL-05` `F-DEP-03` `F-DEP-04` `F-DEP-05` `F-CTR-03` |
| 恢复动作 | 17 条有恢复动作，**17/17 恢复或被守卫判定** |
| 工具退出码 | `1`（有静默失败 —— **如实**：本包确实还有 7 条缺口） |

逐行矩阵见 `references/FAULT-MATRIX.md` §1；缺口清单与根因见 §2；恢复结局见 §3。

## T9 ★ 守卫：运行前体检 + 运行后核对（**实测之二**）

```bash
python "$PKG/scripts/fault_inject.py" --guard --pkg "$PKG" --case "$PKG/examples/case.json"
#   OK  未发现问题 / 守卫结论: 通过                                exit 0

python "$PKG/scripts/fault_inject.py" --guard --pkg "$PKG" --case <bad>/case.json \
    --template <bad>/list_template.json
#   BLOCKER [template] --template 的 JSON 顶层不是对象（list）…    exit 1

python "$PKG/scripts/fault_inject.py" --guard --out "$WORK/out"
#   OK  未发现问题 / 守卫结论: 通过                                exit 0

python "$PKG/scripts/fault_inject.py" --guard --out "$WORK/fw/runs/F-IN-07/out"
#   WARN [figure] 材料里有 1 张数据表，但成稿里既没有图表/表格、也没有任何 note … exit 1

python "$PKG/scripts/fault_inject.py" --guard --out "$WORK/fw/runs/F-DEP-03/out"
#   BLOCKER [result] 输出目录里没有 result.json（运行未落盘）        exit 1
```

**可信度**：28 条故障产物上 **7/7 静默被抓**；健康产物 **0 误报**。

## T10 ★ 泛化台：两个题材逐案实测（**实测之三**）

```bash
python "$PKG/scripts/case_check.py" --pkg "$PKG" --work "$WORK/cc" --report-json "$WORK/cc.json"
#   case-a-perovskite        exit=1 status=partial  slides=8  判定=PASS
#   case-b-climate-text      exit=1 status=partial  slides=6  判定=PASS
# 案例判定: 全部 PASS（2 个案例）
```

| 观测量 | 案例 A（实验科学） | 案例 B（理论文本） |
|-|-|-|
| exit / status | `1` / `partial` | `1` / `partial` |
| slide_count | 8 | 6 |
| 图表形态 | `chart_image ×1` + `none ×7`（`table_id=jv.csv`，8 行原样重绘） | **`none ×6`**（0 张编造图） |
| unverified / material_warnings / uncertainty | 1 / 0 / 0 | 1 / 0 / 0 |
| 备注覆盖 / 脚注覆盖 | 1.0 / 1.0 | 1.0 / 1.0 |
| gate / selftest / deck 重开 | `true` / `true` / 8 | `true` / `true` / 6 |
| 硬判据 | **12/12 PASS** | **11/11 PASS** |
| advisory 缺口 | `unverified_claims_max`（材料缺"背景"小节） | `must_mention_in_deck`（缺 `2009/2015`） |

## T11 ★ 四种边界探针（**实测之四**）

```bash
python "$PKG/scripts/case_check.py" --pkg "$PKG" --work "$WORK/cc" --probes
#  P1 两张数据表（材料给了两个 CSV）   exit=1 partial slides=8 fig=chart_image,none unv=1
#  P2 材料没有任何章节标题（纯段落）   exit=1 partial slides=8 fig=chart_image,none unv=3
#  P3 页数上限压到 3（材料内容远超）   exit=0 success slides=3 fig=chart_image,none unv=0
#  P4 用 --edit 塞入材料里没有的数字   exit=1 partial slides=8 fig=chart_image,none unv=2
```

| # | 变形 | 关键实测细节 | 结论 |
|-|-|-|-|
| P1 | 两张 CSV | `material_view` 登记两张，页面**只用第一张**，第二张静默忽略 | ❌ GAP-P1 |
| P2 | 删掉所有章节标题 | 占位主张 1→3；`uncertainty` 记 `page 2 bullet too long (CJK-weighted=162 vs 90)` | ⚠️ 降级**有留痕**（D4 生效） |
| P3 | `max_slides=3` | 角色压成 `cover→overview→result`，`change_records` 只有 `start` | ⚠️ 压缩不留痕（GAP-P3） |
| P4 | `--edit` 塞入 `31.7%` | `unverified_claims` 1→2（`missing_numbers=["31.7%"]`） | ✅ 编辑链路仍过 D2 |

## T12 ★ 机制判据探针（M1–M5）

```bash
python "$PKG/references/mechanism_probe.py" --out "$WORK/out"
# == out  status=success
#    M1_page_units      PASS
#    M2_anchors         PASS
#    M3_figure_states   PASS
#    M4_versioning      PASS
#    M5_contract        PASS
# 报告已写入: mechanism-probe-report.json                                 exit 0
```
实测：示例案例 **5/5 PASS**、`exit=0`（探针只读产物，不看文档）。
负例控制（人为破坏三处痕迹 → 立刻 FAIL）见 `references/MECHANISM-AND-ASSETS.md` 第一部分 §5。

## T13 ★ 增益测量台（公平对照，两案例）

```bash
cp "$PKG/references/measure_gain.py" "$WORK/" && cd "$WORK"
python measure_gain.py --skill-dir "$PKG" \
    --case "$PKG/examples/case.json" \
    --case "$PKG/examples/cases/case-a-perovskite/case.json" \
    --work "$WORK/gwork" --out "$WORK/gain.json"                        # exit 0
```

**实测（2026-11-23，2 个案例）**：

| 指标 | 基线形态均值 | 本 Skill 均值 | Δ |
|-|-|-|-|
| Q1 页级角色覆盖 | 0.0000 | 1.0000 | **+1.0000** |
| Q3 数字主张可追溯 | 0.0000 | 1.0000 | **+1.0000** |
| Q4 备注覆盖 | 0.0000 | 1.0000 | **+1.0000** |
| Q5 证据脚注覆盖 | 0.0000 | 1.0000 | **+1.0000** |
| Q6 可复核产物齐全度 | 0.1429 | 1.0000 | **+0.8571** |
| 脚本墙钟（两案例合计） | 0.237 s | 2.851 s | +2.614 s（**成本，不是收益**） |
| 本 Skill 侧 exit / status | — | `0`+`1` / `success`+`partial` | 第二个案例是 `partial`，**未被粉饰** |

`gate_valid` 两案例均为 `true`。

> **可复现性说明**：上表的墙钟数字取自"示例案例 + 案例 A"这一组配对（`0.237 s / 2.851 s`）。
> 换成"示例案例 + 案例 B"再跑一次，实测为 `0.214 s / 2.438 s`——
> **Δ 五项完全相同**（Q1/Q3/Q4/Q5 `+1.0`、Q6 `+0.8571`），说明结论不依赖具体配对；
> 差异只在墙钟（机器负载相关），所以墙钟只作**成本**参考，不作收益主张。

## T14 确定性：同输入双跑 —— 内容级一致

```bash
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$WORK/d1"
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$WORK/d2"
# 逐字段对比 result.json（忽略时间戳/日志名/sha/路径）
```
实测：**只有 2 处差异** —— `log`（日志文件名带时间戳）与 `run_meta.timestamp`；
页序、角色、主张、证据、图表、备注、契约回显逐字段一致。

## T15 契约形态负路径（已知缺口 S2 的复现）

```bash
# output_contract 写成字符串
python "$PKG/scripts/main.py" --case <bad-case>/case.json --out "$WORK/out-bad-ctr"
# 实测 exit=0、status=success、uncertainty=[]，契约字段一个都没回显，G2 也不报错
python "$PKG/scripts/fault_inject.py" --guard --pkg "$PKG" --case <bad-case>/case.json
#   DEGRADE [contract] output_contract 不是对象（str）——契约回显会被整体跳过   exit 1
```
⇒ 缺口存在（S2），但**守卫能提前报出来**：这就是"如实记录 + 给补救"的形态。

## T16 包体自检与 frontmatter（提交前必跑）

```bash
python validate_pkg.py <技能根>                        # 期望 PASS，0 条 FAIL
find <技能根> -name __pycache__ -o -name '*.pyc'        # 期望空输出
find <技能根> -type f | wc -l                           # 期望 ≤50
head -3 "$PKG/SKILL.md"                                 # 首行 ---，含 name: 与 description:
```
实测：`PASS`（**48 个文件** ≤ 50）；无 `__pycache__`；首行 `---`、
含 `name: academic-ppt-builder-union` 与 `description: …`。

## 验收对照

| 项 | 判据 | 本机实测 |
|-|-|-|
| 主流程 | `main.py` exit 0 且 `status=success` | ✅ exit 0 / success / 6 页（示例案例） |
| 契约门 | `result_tool.py` `valid=true` 且 exit 0 | ✅ G1–G8 全 True |
| 产物自检 | `selftest.py` `all_pass=true` | ✅ 7/7 |
| 契约覆盖 | 顶层含 `OUTPUT_CONTRACT.md` 全部字段且无 null | ✅ 18 键（示例）/ 20 键（两案例） |
| 自定位 | cwd 不是技能根也能跑 | ✅ 所有命令都在包外 cwd 执行 |
| 编辑/回退 | `--edit --version v2` 产生 `deck_v2.pptx` 且留记录 | ✅ 4 条 change_records |
| **注入矩阵** | 28 条逐行有 exit/status/留痕/静默判定；恢复动作有结局 | ✅ `FAULT-MATRIX.md` §1/§3 |
| **静默可发现** | 守卫抓到全部静默失败且健康产物 0 误报 | ✅ 7/7 抓到、0 误报 |
| **逐案判定** | 两个题材都过 `_case_set.expect` | ✅ 12/12 与 11/11 |
| **边界可见** | 四种探针都跑出结论，7 条 GAP 被记录而非隐藏 | ✅ P1–P4 + GAP-A/B/P |
| **机制判据** | 探针 M1–M5 全 PASS，且负例会 FAIL | ✅ 5/5 PASS |
| **增益复算** | Δ 可用随包脚本重算出来（含负面项） | ✅ Q1/Q3/Q4/Q5 +1.0、Q6 +0.8571、耗时 +2.614 s |
| 包体 | ≤50 文件 / ≤2MB / 7 种文本扩展名 / 无 `__pycache__` / 无绝对路径 | ✅ 48 文件，见 T16 |

## 已知限制（本机验证结论）

1. **7 条静默缺口 + 7 条跨题材边界仍在**（`FAULT-MATRIX.md` §2、`CASE-SET.md` §3）：
   本包给的是"测出来 + 写清楚 + 补救"，**不是根治**。
2. **注入台覆盖不到**：并发/中断、畸形但合法的 PPTX、GB 级材料、真机 Office 渲染、平台预检
   （`FAULT-MATRIX.md` §5 逐条列明）。
3. **对照是脚本级**：测量台的基线是"题面点名失败形态的确定性代理实现"，
   不是平台官方 Agent 对照。
4. **判定是结构+覆盖判据**，不是质量判据。
5. **三个台都属开发期工具**（注入台 ~60 s / 泛化台 ~12 s / 测量台数秒），
   不要放进平台 900 秒评测预算里跑。
