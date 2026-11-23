# TEST.md — 自测方法、真实命令与实测输出（v8 · 契约四形态 × 边界值矩阵）

> 下面每一条都是**真的跑过**的（2026-11-23，Windows / CPython 3.13.9 / matplotlib 3.10.6）。
> 输出为**原样摘录**。**绝不要在包内跑脚本**：会在 `scripts/` 里生成 `__pycache__` 导致预检 FAIL。
> 先整包复制到包外（本文用 `$SKILL_DIR` 指向那份副本）。

```bash
export SKILL_DIR=/tmp/pkgcopy/challenge-83d4f050     # 含 SKILL.md 的那一层（包外副本）
```

## T1 主流程 smoke（必须 exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" \
    --out /tmp/out-v8 --formats svg,png,pdf --verbose
```

实测 `exit=0`：

```text
[main] case_id=example-egfr-mapk status=success entities=9 edges=9 bands=4 verified=True
  produced  diagram.svg  sha256=27f344a0dfb2e90f  17771 bytes
  produced  diagram.png  sha256=9137715961238f3f  203655 bytes
  produced  diagram.pdf  sha256=40eb2b43bcfa16b1  108045 bytes
  produced  result.json  sha256=348d07e09c56f58c  28913 bytes
  produced  model.json  sha256=f93a20a283492f73  11418 bytes
  produced  topology.json  sha256=eb826fc5557fccfc  1434 bytes
  produced  legend_audit.json  sha256=efdb1805c839d648  1807 bytes
SUMMARY {"status": "success", ..., "self_check_passed": true, "failures": 0,
  "warnings": 0, "gates": "8/8", "extraction": {"method": "manual", "verified_by_agent": true}}
```
> 注意：上表里 **`diagram.pdf` 与 `result.json` 两行**会随运行变化——前者只差 `/CreationDate` 的秒位
> （1–2 字节），后者含时间戳与**随 cwd 相对化的路径字段**（这正是 T4 要测的东西）；
> 其余 **5 件**（`diagram.svg` / `diagram.png` / `model.json` / `topology.json` / `legend_audit.json`）
> 的 sha256 可与 `references/` 里的实测表和报告对拍。


`result.json`：**顶层键 22 个**、`gates` **8/8**、`self_check.passed=true`、`uncertainty=0`、`change_records=3`；
`output_contract` 的两个示例字段（`custom_demo_field` / `custom_list_field`）已回显。

## T2 契约独立复查

```bash
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/out-v8/result.json \
    --case "$SKILL_DIR/examples/case.json"
```

实测 `exit=0`：`C01`–`C07` 全 pass，`contract|ok|case=example-egfr-mapk|status=success|checks=7`。

## T3 图面独立复检

```bash
python "$SKILL_DIR/scripts/validate_figure.py" --out /tmp/out-v8
```

实测 `exit=0`：`standalone-verify|ok=True|fails=0|warns=0`。

## T4 本轴脚本：契约矩阵（本版核心）

```bash
# 全矩阵 40 行（约 2–3 分钟）
python "$SKILL_DIR/scripts/contract_matrix.py" \
    --work /tmp/cm --report "$SKILL_DIR/contract_matrix_report.json"
```

全矩阵实测 `exit=0`，摘要：

```text
rows=40  control={'exit_code': 0, 'status': 'success', 'g2': True, 'check_contract_exit': 0}
  ok               27  control-base, edge-collide-envelope, edge-many-fields, edge-nested, ...
  fill_documented  1  edge-empty-contract
  silent_gap       8  edge-collide-caseid-typed, edge-null, edge-typed-invalid, struct-oc-bool,
                      struct-oc-list, struct-oc-null, struct-oc-num, struct-oc-str
  flagged          4  edge-collide-internal, struct-case-missing, struct-case-notjson,
                      struct-case-notobject
  documented_but_untraced: 15 行
  undocumented exit codes: [1]
```

单行复现（三行，秒级）：

```bash
python "$SKILL_DIR/scripts/contract_matrix.py" \
    --only control-base,struct-oc-list,edge-collide-internal \
    --work /tmp/cm --report /tmp/cm_doc.json
```

实测 `exit=0`：

```text
[ 1/3] control-base                 exit=0 status=success  g2=True  cc=0     -> ok  (无留痕)
[ 2/3] edge-collide-internal        exit=0 status=success  g2=True  cc=1     -> flagged
[ 3/3] struct-oc-list               exit=0 status=success  g2=True  cc=0     -> silent_gap
  ok               1  control-base
  silent_gap       1  struct-oc-list
  flagged          1  edge-collide-internal
```

**三条核心实测**（详见 `references/CONTRACT-MATRIX.md`）：

| 结论 | 实测证据 |
|-|-|
| 契约容器非映射 ⇒ 整个契约被忽略，**三层全绿** | `struct-oc-list/str/num/bool/null`：`exit=0` / `success` / `g2=True` / `cc=0` |
| 主流程自带门会漏，独立检查器能补 | `edge-collide-internal`：`g2=True` 但最终 `result.json` 无该字段；`check_contract.py` `exit=1`、失败项 `C05` |
| 没有一层校验"声明类型" | `edge-collide-caseid-typed`（声明 number、回显 `str("example-egfr-mapk")`）：`exit=0` / `success` / `g2=True` / `cc=0` |

## T5 反面用例（检查真的会失败）

| 用例 | 命令 | 实测 |
|-|-|-|
| 契约容器非法（数组） | `--only struct-oc-list`（见 T4） | 三层全 pass 但契约被忽略 → 标为 **silent_gap**（不是 exit≠0） |
| 键与内部临时键同名 | `--only edge-collide-internal` | `check_contract.py` **exit=1**（`C05` 缺回显） |
| `--case` 不存在 | `python "$SKILL_DIR/scripts/contract_matrix.py" --case D:/nope/case.json …` | **exit=4**，`错误：找不到 D:/nope/case.json` |
| `--only` 没匹配 | `python "$SKILL_DIR/scripts/contract_matrix.py" --only nosuchrow …` | **exit=4**，`错误：--only 没匹配到任何行` |
| `case.json` 非法 JSON / 是数组（走主流程） | 见 T4 的 `struct-case-notjson` / `struct-case-notobject` | 主流程 **exit=1**、无 `result.json`、stderr 是 `JSONDecodeError` / `AttributeError: 'list' object has no attribute 'get'` |
| 材料缺失（走主流程） | 把案例目录里只留 `case.json`（`materials: []`）后重跑 `main.py` | `status=failed` / **exit=3**，`CP1.3` 为 fail，仍写出 `result.json`（1 条 uncertainty） |

## T6 逐项通过清单

| # | 判据 | 命令 | 期望 | 实测 |
|-|-|-|-|-|
| 1 | 主流程可跑 | T1 | exit 0 | exit 0 ✅ |
| 2 | 契约齐全（四形态回显、无 null） | T2 | exit 0 | exit 0（C01–C07）✅ |
| 3 | 图面/审计独立复检 | T3 | exit 0 | exit 0 ✅ |
| 4 | 四形态 × 边界值被逐行覆盖 | T4（40 行） | 有结论 | 40 行；ok 27 / fill 1 / silent 8 / flagged 4 ✅ |
| 5 | 静默通过有明确清单 | T4 | 是 | 8 行（见 `references/CONTRACT-MATRIX.md §5`）✅ |
| 6 | 主流程门漏检能被独立检查器补 | T5 | cc=1 | `C05` ✅ |
| 7 | 参数错误有明确退出码 | T5 | exit 4 | exit 4 ✅ |

## T7 注意事项

1. **不要在包内运行任何脚本**（`__pycache__` 会让预检 FAIL）。
2. `contract_matrix.py` 会为每一行**实拷贝**案例目录并跑一次主流程（40 行 × 2 个进程），全矩阵约 2–3 分钟；
   只想复现单一结论时用 `--only <子串>`。
3. 报告里的 `case_id` 是示例案例的 `example-egfr-mapk`；注入的契约字段（`c_str`/`c_null`/… ）是**实验构造物**，
   不是正式案例的契约，也不是分数。
4. 矩阵只覆盖契约轴；CLI 参数边界、并发、磁盘满等见 `references/CONTRACT-MATRIX.md §8` 未覆盖声明。
