# TEST.md — 本地实测记录与复现判据（文档轴 A：决策显性化）

> 本文件记录本包在**本机的真实执行结果**（原样粘贴，未美化）。命令与 `SKILL.md` /
> `README.md` 里写的调用方式逐字一致，全部在**包外临时目录**执行（`<tmp>` 为包外目录，
> `SKILL_DIR` 指向包副本），因此同时验证了**自定位**与"包内不留运行残留"。
>
> 环境：Windows 10/11 · Anaconda Python **3.13.9** · matplotlib **3.10.6** ·
> Pillow **12.3.0** · 无 LibreOffice。
>
> 本轮改动性质：**文档轴 A（决策显性化）** —— SKILL.md 重写为决策规则 D1–D20 +
> 失败分支五类表；`references/failure-modes.md` 重写为同号对照矩阵；
> README.md / RUBRIC_MAP.md 重写。**脚本、CLI 参数名、结果契约与示例输入均未改动**
> （算法层不变 ⇒ 本文记录的结构性数值与基包一致，属预期）。

## T1 编译检查 —— 通过

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py
echo $?                                            # 0
```

`scripts/` 共 10 个 `.py`（main / extract / figurespec / svgbuilder / preview / audit /
spec_lint / scaffold / check_contract / common）全部通过。

## T2 默认流程（无 `--plan`）—— 通过，`status=success`

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <tmp>/outA
echo $?                                            # 0
```

实测（读 `<tmp>/outA/result.json` 与 `audit.json`）：

```
result.json 顶层键数 : 26
status               : success
spec_lint.valid      : True
plan                 : {source: "none", hash: null, lint: {valid: true, problems: []}}
four_element.missing : []
layer_naming.bad     : []
determinism_probe    : 9bcb54b29fe658d4
```

## T3 方案先行链（scaffold → CP1 门 → `--plan` 出图）—— 通过

```bash
python "$SKILL_DIR/scripts/scaffold.py"  --case "$SKILL_DIR/examples/case.json" --out <tmp>/plan_skel.json
echo $?      # 0    （骨架生成成功；四要素待 Agent 填充，属预期）
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan <tmp>/plan_skel.json
echo $?      # 1    （D14：four_elements 四项未填 → problems 非空，**CP1 门按设计拦住**）
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan "$SKILL_DIR/examples/plan.example.json"
echo $?      # 0    （已定稿方案）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
       --plan "$SKILL_DIR/examples/plan.example.json" --out <tmp>/outB
echo $?      # 0
```

`outB` 实测：`result.plan.lint.valid=true` · `plan.hash=8af280bed034f42a`（前 16 位）·
`spec_lint.valid=true`。

## T4 契约自查（exit code 判据）—— 通过

```bash
python "$SKILL_DIR/scripts/check_contract.py" --result <tmp>/outA/result.json \
       --case "$SKILL_DIR/examples/case.json"
echo $?      # 0
```

```
valid=true · 信封键 18（缺失 0）· 案例契约字段 8（顶层覆盖 8）· null 违规 0
```

⇒ 顶层 26 键 = 信封 18 ∪ 案例 `output_contract` 8，与 `examples/EXPECTED-OUTPUT.md` 一致。

## T5 规格 lint 独立复跑 —— 通过

```bash
python "$SKILL_DIR/scripts/spec_lint.py" --spec <tmp>/outA/spec.json --content <tmp>/outA/content.json
echo $?      # 0
```

## T6 确定性（D20 的正面证据）—— 两次运行同哈希

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <tmp>/det1
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <tmp>/det2
```

```
audit.determinism_probe.spec_sha16 : det1 = 9bcb54b29fe658d4 = det2   （一致）
<case_id>_graphical_abstract.svg   : sha256 前 16 位 det1 = 370a037e2bafb9ee = det2
```

（PNG/PDF 允许字节差异 —— 后端版本/嵌入信息；**几何与 spec 必须一致**。）

## T7 自定位：`cwd` 与技能根无关 —— 通过

```bash
cd /                                       # 完全无关的 cwd
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <tmp>/outC
echo $?                                    # 0
```

## T8 失败分支抽查（真实退出码，对照 D1 / D14 / D15）—— 符合契约

```bash
python "$SKILL_DIR/scripts/main.py" --case <tmp>/nope.json --out <tmp>/nopeout
# stdout: {"status": "failed", "error": "case.json not found: <tmp>/nope.json"}
echo $?      # 1     → D1（硬输入错误，不留半成品）
```

| 抽查项 | 命令 | 实测退出码 | 对应规则 | 结论 |
|-|-|-|-|-|
| 缺 `case.json` | `main.py --case <不存在>` | **1** | D1 | 符合 |
| 未定稿骨架过 CP1 门 | `spec_lint.py --lint-plan`（骨架） | **1** | D14 | 符合（按设计拦住） |
| 定稿方案过 CP1 门 | `spec_lint.py --lint-plan`（示例方案） | **0** | D14 | 符合 |
| 契约完整且无 null | `check_contract.py` | **0** | D15–D17 | 符合 |
| 正常运行 | `main.py`（示例案例） | **0** | D18 | 符合（`status=success`） |

`references/failure-modes.md` §6 给出了同一组命令的完整复现片段。

## T9 合规验收（`validate_pkg.py`）—— 见回报栏（本轮最终 PASS 原文）

包体统计：**36 文件**（上限 50）· 全包 `.md/.py/.json/.txt` 四类，
无 `__pycache__` / `*.pyc` / 二进制 / 符号链接；无本机绝对路径
（唯一保留的 `C:/Windows/Fonts` 等字符串是**跨平台字体探测候选路径**，
判别法：删掉它只是少一条候选路径，不会让任何一张图找不到文件）。

## 10. 本轴未做的事（诚实边界）

- **未做**与"不加载 Skill 的基础 Agent"的同台 A/B 对照：本轴聚焦"异常处置可否被审计"，
  对照协议与实测记录属于增益可验证化轴的内容，本包不做该声明；
- **未改**脚本算法与 CLI 参数名，也未改 `examples/` 的输入材料与既有实跑产物
  （因此 T2–T6 的结构性数值与基包一致是预期结果，不是"未改动却声称改动"）；
- **未做**平台提交、未联网、未改动 `submit/`、`build/`、`target/`、`publish/`、`traces/`。
