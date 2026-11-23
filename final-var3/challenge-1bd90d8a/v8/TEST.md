# TEST.md — v8（契约四形态 × 边界值矩阵轴）真机实测记录

> 所有命令都在**包外**的临时副本上跑（复制到系统临时目录后再执行）；包内不产生 `__pycache__`。
> 每条都给出命令与**真实输出摘要**（数字来自 `contract_matrix_report.json`）。

环境：Windows / Python 3.13.9 / Pillow 12.3.0。

---

## T1 语法编译

```bash
python -m py_compile scripts/*.py
```

结果：**exit 0，11/11 通过**（10 个既有入口 + `contract_matrix.py`）。

## T2 端到端冒烟（包外副本）

```bash
cp -r v8 /tmp/v8 && cd /tmp/v8
python scripts/main.py --case examples/case.json --out /tmp/out --work /tmp/work
```

```
[main] case_id=example-science-figure-01 status=completed figures=['fig-01', 'fig-02'] failed=[]
[main] gates: G1=OK G2=OK G3=OK G4=OK G5=OK G6=OK G7=OK G8=OK all_pass=OK
EXIT=0
```

`result.json` 顶层 **29 键**，`status=completed`，`outputs` 6 项。

## T3 既有入口逐个跑（能力未丢）

| 命令 | 实测 |
|-|-|
| `check_contract.py --result /tmp/out/result.json --case examples/case.json` | `SUMMARY: PASS (required=18 missing=0 null=0 contract_missing=0)`，exit 0 |
| `figcheck.py --dir /tmp/out --case examples/case.json --json` | `all_pass=True`，G1–G8 全 True，exit 0 |
| `mapcheck.py --dir /tmp/out --case examples/case.json --json` | `summary={'checked': 121, 'mismatches': 0, 'unmatched': 0}`，exit 0 |
| `spec_lint.py --spec examples/case.json --case examples/case.json --json` | `{"valid": true, "counts": {"figures": 2, "errors": 0, "warnings": 0}}`，exit 0 |
| `extract.py --case examples/case.json --out /tmp/extract --json` | 输出 `tables[]` 列画像，exit 0 |
| `verify_rerun.py --record-only --dir /tmp/out` | 逐文件 sha256，exit 0 |

## T4 ★ 本版新增：契约矩阵全量实测（38 行）

```bash
python scripts/contract_matrix.py --case examples/case.json \
    --workspace /tmp/cm --out /tmp/cm/contract_matrix_report.json
```

真实输出（尾部）：

```
[contract_matrix] 行数=38 判定={'echo_complete': 14, 'silent_pass': 11, 'caught': 5, 'no_contract': 8}
[contract_matrix] 静默通过=['F5', 'F6', 'B4', 'B5', 'B6', 'B8', 'D5', 'D6', 'D8', 'D11', 'D12']
EXIT=2
```

- **exit 2 = 存在静默通过**（本脚本的语义：0=无静默通过，2=有，1=用法/环境错误）。
- 耗时 **70.5 秒**（38 行 × 每行 3 个子进程）；矩阵指纹
  `matrix_digest = f4d21e46fff51c7e73886c42c0c5166965e9fc8beff2f897a13d58ff4faea2f0`。
- 静默通过分型：`illegal_shape_tolerated` 7 行（F5/F6/B4/B5/B6/B8/D11）、
  `illegal_shape_applied_true` 4 行（D5/D6/D8/D12）。
- 被抓住 5 行：A2/A3/A4/A5（内部瞬态键被 `pop`，G2=false、status=partial、exit 2、
  check_contract exit 1）与 B1（空字段名，`parser_disagreement=true`）。

## T5 定点复核（`--only`）

```bash
python scripts/contract_matrix.py --only A2,B1,D5 --json
```

实测：3 行全部按预期判定（A2 `caught`、B1 `caught`、D5 `silent_pass`），
说明编号可独立复核；配合 `references/CONTRACT-MATRIX.md` 的逐行表，
任何人可以只挑一行验证本轴的结论。

## T6 四形态等价性（矩阵里的 F 族）

| 行 | 注入 | 实测 |
|-|-|-|
| F1 | `["case_id","status","outputs","editable_source"]` | 4 字段全回显（`editable_source` 走别名给 SVG 名列表） |
| F2 | `{"alpha_s":"string","beta_a":"array","gamma_o":"object","delta_n":"number","eps_b":"boolean"}` | 5 字段按声明类型给 `""`/`[]`/`{}`/`0`/`false`，**无 null** |
| F3 | `{"fields":["case_id","sources","field_mapping"]}` | 与形态①等价，`field_mapping` 给 `"data_manifest.json"` |
| F4 | `{"fields":{"title":"string","sources":"array","gates":"object"}}` | 3 字段回显；`gates` 最终被真实门值覆盖 |
| A1 | 22 个别名一次性声明 | 22 个全部回显且非空（`echo_complete`） |

## T7 边界与异常

| 用例 | 命令 | 实测 |
|-|-|-|
| `--only` 写错编号 | `contract_matrix.py --only Z9` | 报错并列出可用编号，exit 1 |
| 基准案例不存在 | `contract_matrix.py --case nope.json` | 报错，exit 1 |
| `--workspace` 落在案例目录内 | `contract_matrix.py --workspace examples/w --only D5` | 启动即拒绝（会把案例目录复制进自己的子目录），exit 1 |
| 跳过交叉校验器 | `contract_matrix.py --no-cross` | 只跑主流程，`figcheck_g2`/`check_contract_exit` 为 null |
| 保留行副本 | `contract_matrix.py --keep` | 各行的隔离副本保留在 `<workspace>/<编号>/` |
| 报告可移植 | 见 T8 | —— |

## T8 报告合规

```bash
# validate_pkg.py 用的就是同一组本机路径标记（盘符前缀 / 用户目录 / UNC 前缀），
# 把包与报告一起扫一遍：
python validate_pkg.py .
```

实测：报告与文档在**同一组标记**下 0 命中。矩阵报告里的 `<WORKSPACE>` / `<CASEDIR>` / `<SKILL_DIR>` 占位符替代了本机路径。

```bash
python validate_pkg.py <本包目录>
```

见提交前的合规验收记录（`[PASS]`，0 条 FAIL）。
