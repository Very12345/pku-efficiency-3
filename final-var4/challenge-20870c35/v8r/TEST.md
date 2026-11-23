# TEST.md — academic-talk-organizer v8（契约矩阵轴）自测记录

> 本文件里出现的**每条命令都真跑过**，输出为实测摘要（不是设计稿）。
> 实测环境：Windows 11 / Git Bash（MSYS2）/ Python **3.13.9** /
> python-pptx **1.0.2** / Pillow **12.3.0** / pypdf **6.14.2**。
>
> **硬规矩：绝不在包内目录跑脚本**（会生成 `__pycache__`，合规硬门直接拒收）。
> 下面的命令一律在包外临时目录里跑；`contract_matrix.py` 会把技能**复制到沙箱**再调用。

## 0. 准备（包外沙箱）

```bash
PKG="<本包所在目录>"
SB=/tmp/atk-v8 && rm -rf "$SB" && mkdir -p "$SB"
cp -r "$PKG" "$SB/skill"
SKILL_DIR="$SB/skill"
cd "$SB"                       # cwd 故意不在技能根
```

## T1 · 主流程（最小调用）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out "$SB/out"
```

实测：

```
[plan] 12 pages, narrative=group_meeting, audience=familiar, P-gates valid=True
[deck] 12 slides, mode=built-in-theme, verify valid=True
[preview] wrote 13 preview files (PIL simulation)
[done] status=partial deck_ok=True preview_ok=True plan_gates=True evidence_audit=True validate_valid=True contract_valid=True
```

**exit code = 0**；`result.json` 顶层键 **20**；
**顶层 null 值 = 0 个**；`contract` 四个子键齐备：

```
['declared_source', 'applied', 'pipeline_produced_fields', 'echo_initialized_fields']
```

`self_check.json → contract_check` 实测：

```json
{"valid": true,
 "summary": "declared=16 missing=0 wrong_type=0 real_value_type_conflicts=0",
 "checked_against": "case.json + task.md"}
```

## T2 · 契约专项复核（含 `--contract` 显式口径）

```bash
python "$SKILL_DIR/scripts/check_contract.py" "$SB/out/result.json"
python "$SKILL_DIR/scripts/check_contract.py" "$SB/out/result.json" \
       --contract '[{"name":"case_id","type":"str"},{"name":"pages","type":"list"}]'
python "$SKILL_DIR/scripts/validate_result.py" "$SB/out/result.json"
python "$SKILL_DIR/scripts/evidence_audit.py" "$SB/out/result.json"
```

实测：`check_contract.py` 三键输出 `missing_required=[] missing_optional=[] wrong_type=[]`，
`checked_against` 分别为 `sibling self_check.json contract_applied`（无 `--contract`）
与 `--contract inline json`（显式给出）；`validate_result.py` → `checks=7 errors=0 warnings=1`；
`evidence_audit.py` 逐页条目齐全。**四个命令 exit code 全 0**。

## T3 · 全链路自检（G1–G10 + 包约束）

```bash
python "$SKILL_DIR/scripts/selftest.py" "$SB/out" --package-check "$SKILL_DIR"
```

实测：`"summary": "checks=6 errors=0"`，`no_pycache`/`symlinks=[]` 均 `ok=true`，
包约束 `"summary": "text=39 total_bytes=379354 max_file=42426"`。**exit code = 0**。

## T4 · ★ 契约矩阵（本轴的核心测试）

```bash
python "$SKILL_DIR/scripts/contract_matrix.py" \
    --sandbox "$SB/cm" \
    --report "$SB/cm/contract_matrix_report.json" \
    --emit-md "$SB/cm/matrix-table.md"
```

实测输出（31 格逐行）与汇总：

```
[OK] C-01 … C-07   exit=0 status=partial  期望全部命中
[OK] B-01 … B-09   exit=0 status=partial  期望全部命中
[OK] S-01 … S-06   exit=0 status=partial  期望全部命中
[OK] E-01 … E-08   exit=0 status=partial  期望全部命中
[OK] P-01          exit=0 status=partial  期望全部命中
[contract-matrix] cells=31 unreadable=0 expectation_unmet=0 silent_pass=0
```

**exit code = 0**。实测汇总（墙钟约 35 秒）：

| 项 | 实测 |
|-|-|
| 格子数 / 无法判读 / 期望未命中 | **31 / 0 / 0** |
| 退出码集合 | **`[0]`** |
| status 集合 | `['partial']`（合成案例缺 `dataset_card.pdf` 的如实降级） |
| 契约门 `contract_check.valid` | **31/31 True** |
| 顶层 `null` 值总数 | **0** |
| 静默通过 | **0** |
| 声明为「无留痕通道、静默容忍」的格子 | **3**（`B-01`、`B-02`、`E-02`） |
| 各轴命中 | C 7/7 · B 9/9 · S 6/6 · E 8/8 · P 1/1 |

### T4.1 逐格回显类型（抽查，全部来自报告 JSON）

| 格子 | 声明 | 实测回显类型 | 顶层键数 |
|-|-|-|-|
| C-01 / C-02 / C-03 / C-04 / C-05 | str / list / dict / int / bool | string / array / object / number / boolean | 21 |
| C-06 | `any` | **string**（不是 null） | 21 |
| C-07 | 嵌套 schema（object） | object（嵌套不逐层填充，已声明） | 21 |
| B-05 | 129 字符字段名 | string（照常回显） | 21 |
| B-06 | 非法类型 `WeirdType!!` | **string** | 21 |
| B-07 | `container: "list"` | array | 21 |
| B-08 | int + bool | number + boolean（**0/false 是真值**） | 22 |
| B-09 | `case_id` 声明为 list | **string（真值未被覆盖）** | 20 |
| S-03 | dict of type（大写 `Object`/`ARRAY`） | object + array（大小写不敏感） | 22 |
| S-04 | JSON-schema（1 required + 1 optional） | number + **string（optional 也回显）** | 22 |
| S-05 | task.md 后声明的契约块 | array（**后声明生效**） | 21 |
| S-06 | `required:false` 且不产出 | **不在顶层**（契约规定行为） | 20 |
| E-06 | markdown 表格 6 行 | string + string | 26 |
| P-01 | 只声明 1 个额外字段 | string，且与内置默认字段共存 | 21 |

### T4.2 静默通过的判据与实测

```
silent_pass := exit_code == 0
               且 contract_check_valid is True
               且 「该留痕的格子没留痕」 或 「不该留痕的格子留了痕」
```

实测 **0 格**。三个"无留痕通道"的格子（`B-01`/`B-02`/`E-02`）单独列在报告的
`known_untraced_cells` 里，并在 `references/CONTRACT-MATRIX.md` §3.1 逐格说明原因
（该解析路径在 `main.py` 里没有留痕分支，而 v8 不动 `main.py`）。

### T4.3 修缺陷前后的对照（同一套矩阵）

```bash
# 「打补丁前」= 把三个被改脚本换回基线版本，其余逐字节相同，用同一个探针跑
cp "$PKG/scripts/contract_matrix.py" "$SB/cm/"
cp "<baseline>/scripts/common.py" "<baseline>/scripts/check_contract.py" \
   "<baseline>/scripts/finalize_result.py" "$SB/skill-prefix/scripts/"
python "$SB/cm/contract_matrix.py" --sandbox "$SB/cm2" --report "$SB/cm2/prefix_report.json"
```

| 指标 | 打补丁前（基线脚本） | 打补丁后（本包） |
|-|-|-|
| 期望未命中 | **8**（C-06、B-06、B-09、S-01、S-04、S-05、E-06、P-01） | **0** |
| 退出码集合 | **`[0, 1]`** | **`[0]`** |
| 出现顶层 `null` 的格子 | **5**（合计 **13** 个 null 值） | **0** |
| 声明了却不在顶层的字段 | **3** 格（S-04/S-05/S-06） | 仅 S-06（契约规定行为） |

## T5 · 负例（必须非 0 退出）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SB/nope.json" --out "$SB/out-fail"   # → exit 1
python "$SKILL_DIR/scripts/main.py" --out "$SB/x"                                 # → exit 2
```

实测：`exit=1`（写出最小失败信封，`status=failed`）、`exit=2`（argparse 用法错误，
不写产物）。`contract_matrix.py --only B-09` 可单格复跑，便于定位。

## 6. 汇总

| 测试 | 命令要点 | 期望 | 实测 |
|-|-|-|-|
| T1 | `main.py --case examples --out out` | exit 0；顶层无 null | ✅ exit 0；20 键；null 0 个 |
| T2 | `check_contract` / `validate_result` / `evidence_audit` | 全 exit 0 | ✅ 4/4 exit 0 |
| T3 | `selftest.py <out> --package-check` | exit 0，无 error | ✅ `checks=6 errors=0` |
| T4 | `contract_matrix.py`（31 格） | exit 0、`unmet=0`、`silent_pass=0` | ✅ 31/31 命中、无静默通过 |
| T4.3 | 打补丁前同源对照 | 复现 8 格不中 | ✅ 8 格不中 / 5 格有 null / 退出码含 1 |
| T5 | 负例 | exit 1 / exit 2 | ✅ |

**判据一句话**：`contract_matrix.py` 必须在 **exit 0** 下给出
`expectation_unmet=0` 与 `silent_pass=0`，且 31 格顶层 null 值总数为 0；
若某次改动让任何一格回退（例如又出现 null 或退出码 1），
必须先在 `references/CONTRACT-MATRIX.md` 里登记，不能只改数字。
