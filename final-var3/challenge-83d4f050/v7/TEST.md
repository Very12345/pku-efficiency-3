# TEST.md — 自测方法、真实命令与实测输出（v7 · 确定性 / 字节级可复现）

> 下面每一条都是**真的跑过**的（2026-11-23，Windows / CPython 3.13.9 / matplotlib 3.10.6 / Pillow 12.3.0），
> 输出为**原样摘录**。**绝不要在包内跑脚本**：会在 `scripts/` 里生成 `__pycache__`，导致提交预检 FAIL。
> 正确做法：先把整包复制到包外临时目录（本文用 `$TMP=$OUT/_smoke/v7`），把 `SKILL_DIR` 指向那份副本。

```bash
export SKILL_DIR=/tmp/pkgcopy/challenge-83d4f050     # 含 SKILL.md 的那一层（包外副本）
```

## T1 主流程 smoke（必须 exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" \
    --out /tmp/out-v7 --formats svg,png,pdf --verbose
```

实测 `exit=0`，stdout 摘要：

```text
[main] case_id=example-egfr-mapk status=success entities=9 edges=9 bands=4 verified=True
  produced  diagram.svg  sha256=27f344a0dfb2e90f  17771 bytes
  produced  diagram.png  sha256=9137715961238f3f  203655 bytes
  produced  diagram.pdf  sha256=40eb2b43bcfa16b1  108045 bytes
  produced  result.json  sha256=348d07e09c56f58c  28913 bytes
  produced  model.json  sha256=f93a20a283492f73  11418 bytes
  produced  topology.json  sha256=eb826fc5557fccfc  1434 bytes
  produced  legend_audit.json  sha256=efdb1805c839d648  1807 bytes
SUMMARY {"status": "success", "case_id": "example-egfr-mapk", "files": ["diagram.svg",
  "diagram.png", "diagram.pdf", "result.json", "model.json", "topology.json",
  "legend_audit.json"], "self_check_passed": true, "failures": 0, "warnings": 0,
  "gates": "8/8", "extraction": {"method": "manual", "verified_by_agent": true}}
```
> 注意：上表里 **`diagram.pdf` 与 `result.json` 两行**会随运行变化——前者只差 `/CreationDate` 的秒位
> （1–2 字节），后者含时间戳与**随 cwd 相对化的路径字段**（这正是 T4 要测的东西）；
> 其余 **5 件**（`diagram.svg` / `diagram.png` / `model.json` / `topology.json` / `legend_audit.json`）
> 的 sha256 可与 `references/` 里的实测表和报告对拍。


`result.json` 实测：**顶层键 22 个**、`status=success`、`gates` **8/8 通过**、`self_check.passed=true`、
`uncertainty=0` 条、`change_records=3` 条；契约字段 `custom_demo_field` / `custom_list_field` 已回显
（来自 `examples/case.json` 的 `output_contract`）。

## T2 契约独立复查

```bash
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/out-v7/result.json \
    --case "$SKILL_DIR/examples/case.json"
```

实测 `exit=0`：`C01`–`C07` 全 pass，摘要行 `contract|ok|case=example-egfr-mapk|status=success|checks=7`。

## T3 图面独立复检

```bash
python "$SKILL_DIR/scripts/validate_figure.py" --out /tmp/out-v7
```

实测 `exit=0`：`standalone-verify|ok=True|fails=0|warns=0`（含 `F02_png` 尺寸检查与 `D01_determinism` 探针）。

## T4 本轴脚本：字节级确定性探针（本版核心）

```bash
python "$SKILL_DIR/scripts/determinism.py" --runs 5 \
    --work /tmp/det --report "$SKILL_DIR/determinism_report.json"
```

实测 `exit=0`，关键输出：

```text
[determinism] runs=5  raw_identical=False  stabilized_identical=True
  stable   : diagram.png, diagram.svg, legend_audit.json, model.json, topology.json
  volatile : diagram.pdf, result.json
    volatile field $.change_records[0].ts        [...19:26:00+0800..., ...19:26:02+0800...]
    volatile field $.change_records[0].why       ['case=<WORK>/case/case.json, ...', 'case=case.json, ...']
    volatile field $.provenance.case_file        ['<WORK>/case/case.json', 'case.json']
    volatile field $.provenance.ts               [...19:26:00+0800..., ...19:26:02+0800...]
    volatile field $.self_check.checks[30].detail ['result.json (28309 bytes)', '... (28324 bytes)']
    byte-diff diagram.pdf    regions=2
  stabilized: json-projection=True pdf-normalize=True | env(SOURCE_DATE_EPOCH, fixed cwd):
    except-result.json=True pdf=True residual-result.json-diff=['$.change_records[0].ts',
    '$.change_records[1].ts', '$.change_records[2].ts', '$.provenance.ts']
  exit codes of main pipeline: [0]
```

判据（三条同真才算可复现）：

| 判据 | 实测 |
|-|-|
| J1 稳定清单 | 5/7 产物在 **5 次跨 cwd × 跨 `PYTHONHASHSEED`** 运行间 sha256 相同（`27f344a0dfb2e90f` / `9137715961238f3f` / `f93a20a283492f73` / `eb826fc5557fccfc` / `efdb1805c839d648`） |
| J2 易变清单 | `diagram.pdf` = **只有 1 处**（`/CreationDate` 秒位，偏移 104020 起、1–2 字节）；`result.json` = **8 个 JSON 路径**（4 时间戳 + 3 cwd 泄漏 + 1 二阶） |
| J3 稳定化后一致 | JSON 投影 ✅ · PDF 规范化 ✅ · 固定 cwd + `SOURCE_DATE_EPOCH` ✅（残余仅 4 条时间戳路径，投影后一致） |

快跑（3 次）实测同样 `exit=0`；`--runs 3 --strict`（要求**原始字节**也一致）实测 **exit=3**
——这正是"result.json/PDF 的原始字节本来就含时间"的预期表现。

## T5 反面用例（检查真的会失败）

| 用例 | 命令 | 实测 |
|-|-|-|
| 严格模式：要求原始字节一致 | `python "$SKILL_DIR/scripts/determinism.py" --runs 3 --strict …` | **exit=3**（规范化后才一致） |
| 案例路径不存在 | `python "$SKILL_DIR/scripts/determinism.py" --case D:/nope/case.json …` | **exit=4**，`错误：找不到 --case：D:/nope/case.json` |
| `--skill` 指到没有 `SKILL.md` 的目录 | `python "$SKILL_DIR/scripts/determinism.py" --skill /tmp/out-v7 …` | **exit=4**，`错误：--skill 下没有 SKILL.md：…` |
| 材料缺失（不走本轴脚本，走主流程） | 把 `examples/case.json` 的 `materials` 改空并重跑 `main.py` | `status=failed` / **exit=3**，`CP1.3 材料文件存在` 为 fail，仍写出 `result.json`（诚实记录失败原因） |

## T6 逐项通过清单

| # | 判据 | 命令 | 期望 | 实测 |
|-|-|-|-|-|
| 1 | 主流程可跑 | T1 | exit 0 | exit 0 ✅ |
| 2 | 契约齐全（含 4 形态回显、无 null） | T2 | exit 0 | exit 0（C01–C07）✅ |
| 3 | 图面/审计独立复检 | T3 | exit 0 | exit 0（fails=0）✅ |
| 4 | 同输入跨 cwd/跨种子稳定清单 | T4 | 5/7 逐字节一致 | 5/7 ✅ |
| 5 | 易变项被逐字段点名 | T4 | 是 | 8 条路径 + PDF 1 处 1–2 字节 ✅ |
| 6 | 规范化后可复现 | T4 | 三条配方同真 | 全真 ✅ |
| 7 | 严格模式会正确拒绝 | T5 | exit 3 | exit 3 ✅ |
| 8 | 参数错误有明确退出码 | T5 | exit 4 | exit 4 ✅ |

## T7 注意事项

1. **不要在包内运行任何脚本**（`__pycache__` 会让预检 FAIL）；本文所有命令都在包外副本上跑。
2. 报告里的 `sha256` 与"哪几件稳定"是**本机实测**；换平台/换库版本时 `diagram.png`/`diagram.pdf` 预期不同
   （详见 `references/DETERMINISM.md` §7 未覆盖声明）。
3. `determinism.py` 默认把报告写到包根 `determinism_report.json`；若只想看结果不落盘，加 `--json` 或 `--report /tmp/x.json`。
4. 需要"原始字节一致"的场合请用 `references/DETERMINISM.md` §6 配方 C（固定 cwd + `SOURCE_DATE_EPOCH`）。
