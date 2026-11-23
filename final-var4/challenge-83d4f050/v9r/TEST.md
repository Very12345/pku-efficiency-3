# TEST.md — 自测方法、真实命令与实测输出（v9 · 缺依赖降级链实测）

> 下面每一条都是**真的跑过**的（2026-11-23，Windows / CPython 3.13.9 / matplotlib 3.10.6 / Pillow 12.3.0）。
> 输出为**原样摘录**。**绝不要在包内跑脚本**：会在 `scripts/` 里生成 `__pycache__` 导致预检 FAIL。
> 先整包复制到包外（本文用 `$SKILL_DIR` 指向那份副本）。

```bash
export SKILL_DIR=/tmp/pkgcopy/challenge-83d4f050     # 含 SKILL.md 的那一层（包外副本）
```

## T1 主流程 smoke（必须 exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" \
    --out /tmp/out-v9 --formats svg,png,pdf --verbose
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


`result.json`：**顶层键 22 个**、`gates` **8/8**、`self_check.passed=true`、`uncertainty=0`、`change_records=3`。

## T2 契约独立复查

```bash
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/out-v9/result.json \
    --case "$SKILL_DIR/examples/case.json"
```

实测 `exit=0`：`C01`–`C07` 全 pass，`contract|ok|case=example-egfr-mapk|status=success|checks=7`。

## T3 图面独立复检

```bash
python "$SKILL_DIR/scripts/validate_figure.py" --out /tmp/out-v9
```

实测 `exit=0`：`standalone-verify|ok=True|fails=0|warns=0`。

## T4 本轴脚本：缺依赖降级链探针（本版核心）

```bash
# 全部 13 行（约 40 秒）
python "$SKILL_DIR/scripts/degrade_probe.py" \
    --work /tmp/dg --report "$SKILL_DIR/degrade_report.json"
```

全矩阵实测 `exit=0`，关键输出：

```text
[ 1/13] s00-baseline             exit=0 status=success | SVG · PNG · PDF · result.json · 审计 JSON 齐全
[ 2/13] s01-no-matplotlib        exit=2 status=partial | SVG · 无 PNG · 无 PDF · result.json · 审计 JSON 齐全
        failed checks: F01_png, F01_pdf
        uncertainty: PNG/PDF 预览未生成或未请求
        interception: 生效（1 个模块确实 import 失败）
[ 4/13] s03-no-pil               exit=2 status=partial | SVG · 无 PNG · 无 PDF · result.json · 审计 JSON 齐全
[ 5/13] s04-no-yaml              exit=0 status=success | SVG · PNG · PDF · result.json · 审计 JSON 齐全
[11/13] s10-libreoffice-missing  exit=0 status=success | SVG · PNG · PDF · result.json · 审计 JSON 齐全
[12/13] s11-libreoffice-failing  exit=0 status=success | SVG · PNG · PDF · result.json · 审计 JSON 齐全
        stub invoked: no（标记文件未生成 → 主流程从未调用 LibreOffice）
dependency surface (实测):
  matplotlib    changes-deliverables-or-status   s01-no-matplotlib,s08-no-mpl-no-pil
  numpy         changes-deliverables-or-status   s02-no-numpy,s08-no-mpl-no-pil
  PIL           changes-deliverables-or-status   s03-no-pil,s08-no-mpl-no-pil,s12-pil-png-microtrace
  yaml/pptx/lxml/pypdf   none-or-minor
  LibreOffice CLI (PATH 无该命令 / 存在但退出 127)   none-or-minor
```

快跑四行（秒级，用于排障）：

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" --only s00,s01,s03,s09 \
    --work /tmp/dg --report /tmp/dg_doc.json
```

实测 `exit=0`：

```text
[ 1/4] s00-baseline    exit=0 status=success | SVG · PNG · PDF · result.json · 审计 JSON 齐全
[ 2/4] s01-no-matplotlib exit=2 status=partial | SVG · 无 PNG · 无 PDF · result.json · 审计 JSON 齐全
[ 3/4] s03-no-pil      exit=2 status=partial | SVG · 无 PNG · 无 PDF · result.json · 审计 JSON 齐全
[ 4/4] s09-svg-only    exit=2 status=partial | SVG · 无 PNG · 无 PDF · result.json · 审计 JSON 齐全
```

**四条核心实测**（详见 `references/DEGRADE-MATRIX.md`）：

| 结论 | 实测证据 |
|-|-|
| 缺 `matplotlib`/`numpy`/`PIL` ⇒ 丢 PNG+PDF，其余全在 | `s01`/`s02`/`s03`/`s08`：`exit=2` / `partial` / 5 件产物 / `F01_png`,`F01_pdf` / `gates.g4=true` |
| `PIL` 是 matplotlib 的硬依赖（不是"只被尺寸检查用到"） | `s12` 微追溯：退出码 1、`micro.png` 未写出、traceback 含 `from PIL import Image`；`s03` 与 `s01` 表现完全一致 |
| 缺 `yaml`/`pptx`/`lxml`/`pypdf` ⇒ 零影响 | `s04`–`s07`：`exit=0` / `success` / 7 件产物 / 0 条 uncertainty |
| LibreOffice 与本包无关（从未被调用） | `s11` 桩命令**先写调用标记再退出 127**，标记文件未生成（`stub_invoked=false`）；`exit=0` / `success` |

## T5 反面用例（检查真的会失败）

| 用例 | 命令 | 实测 |
|-|-|-|
| 缺 matplotlib（受控拦截） | `--only s01` | `exit=2` / `status=partial` / 无 PNG 无 PDF / `F01_png`,`F01_pdf` fail / 1 条 uncertainty |
| 缺 PIL（受控拦截） | `--only s03` | 同 s01（**连 PDF 也丢**） |
| 有意只请求 SVG | `--only s09`（`--formats svg`） | `exit=2` / `partial` / `F01_png`,`F01_pdf` fail（有意降级被记为 fail） |
| 拦截器自证 | 每行都会 `__import__` 被拦模块 | 13 行全部 `importable=false`（拦截确实生效） |
| `--only` 没匹配 | `python "$SKILL_DIR/scripts/degrade_probe.py" --only nosuch …` | **exit=4**，`错误：--only 没匹配到任何场景` |
| `--case` 不存在 | `python "$SKILL_DIR/scripts/degrade_probe.py" --case D:/nope/case.json …` | **exit=4**，`错误：找不到 D:/nope/case.json` |
| 材料缺失（走主流程） | 案例目录只留 `case.json`（`materials: []`）后重跑 `main.py` | `status=failed` / **exit=3**，`CP1.3` fail，仍写 `result.json` |

## T6 逐项通过清单

| # | 判据 | 命令 | 期望 | 实测 |
|-|-|-|-|-|
| 1 | 主流程可跑 | T1 | exit 0 | exit 0 ✅ |
| 2 | 契约齐全 | T2 | exit 0 | exit 0（C01–C07）✅ |
| 3 | 图面/审计独立复检 | T3 | exit 0 | exit 0 ✅ |
| 4 | 依赖面被逐项实测 | T4（13 行） | 有结论 | 必需 3（matplotlib/numpy/PIL）；零影响 6 ✅ |
| 5 | 降级后有可交付物 | T4 | SVG + 审计 + result.json | 5 件全在，`g4=true` ✅ |
| 6 | 降级有留痕 | T4 | `uncertainty` / `export_checks` | 各 1 条，含真实 ImportError 文本 ✅ |
| 7 | 外部命令未被误用 | T4 `s11` | 从未调用 | `stub_invoked=false` ✅ |
| 8 | 参数错误有明确退出码 | T5 | exit 4 | exit 4 ✅ |

## T7 注意事项

1. **不要在包内运行任何脚本**（`__pycache__` 会让预检 FAIL）。
2. `degrade_probe.py` 会把技能包整包复制到 `--work` 下再跑（不会污染原包）；缺依赖是**在子进程里拦截**的，
   不影响你的真实环境。
3. 依赖面结论只对本机实测的解释器/版本组合有效（报告里带 `config.python` 与 `not_covered`）；
   换大版本后重跑一次即可刷新。
4. **档位 A（只装标准库）下 `status=partial`、退出码 2 是预期行为**，不是流水线故障；
   需要 `success` 就装 `matplotlib`（见 `references/MINIMAL-ENV.md`）。
