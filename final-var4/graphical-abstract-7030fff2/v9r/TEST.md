# TEST.md — 本机实测记录（降级链优先版）

> 全部数字来自**包外临时副本**上的真实运行。环境：Windows / Python **3.13.9**（2026-11-23）；
> 本机装了 matplotlib 3.10.6 / Pillow 12.3.0 / pypdf 6.14.2，**没有装 LibreOffice**（P10 因此是真实状态）。
> **绝不在包内跑脚本**：入口会在 `scripts/` 下留 `__pycache__`，直接导致合规验收 FAIL。

```bash
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2
PKG=/tmp/ga-pkg && rm -rf "$PKG" && cp -r "$SKILL_DIR" "$PKG" && cd "$PKG"
```

---

## 1. 主链冒烟（完整环境）

```bash
python scripts/main.py --case examples/case.json --out /tmp/ga-l1
```

| 项目 | 实测值 |
|-|-|
| exit code | **0** |
| `status` | **success** |
| 顶层键数 | **26** |
| `render_log.backend` | **`matplotlib`** |
| `render_log.font` | `Microsoft YaHei, SimHei, Arial, Segoe UI`（运行时探测到的候选字体） |
| `deliverables` | svg / json / png / pdf（PDF `present`） |
| `uncertainty` / `warnings` | `[]` / `[]` |

## 2. 契约门

```bash
python scripts/check_contract.py --result /tmp/ga-l1/result.json --case examples/case.json
```

| 项目 | 实测值 |
|-|-|
| exit code | **0**；`valid=true` |
| 信封 / 案例契约 | **18 / 18** · **8 / 8**；null 违规 0 |

## 3. ★ 缺依赖降级链（本轴主判据）

```bash
python scripts/degrade_probe.py --out /tmp/dg --fail-on strict      # 12 场景，约 40 s
python scripts/degrade_probe.py --out /tmp/dg --only P09 --keep --verbose
```

| 项目 | 实测值 |
|-|-|
| exit code | **0**（`--fail-on strict`） |
| `scenarios_run` / `ok` / `mismatch` / `silent` / `crash` | **12 / 12 / 0 / 0 / 0** |
| `result_json_written` | **12 / 12** |
| `exit_zero` | **12 / 12** |
| `zero_impact_scenarios` | `P00 P01 P05 P06 P10 P11` |
| `seconds_total` | **39.6 s** |

逐场景（`--fail-on strict` 下全 `ok`）：

| # | 拦截 | PNG 后端 | status | SVG | PNG | PDF | unc/warn | 命中日志 |
|-|-|-|-|-|-|-|-|-|
| P00 | 无（对照） | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | —— |
| P01 | `pptx` | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 空 |
| P02 | `PIL` | `pure-python-png` | partial | ✅ | ✅ | ❌ | 1 / 1 | `PIL, PIL` |
| P03 | `matplotlib` | `Pillow` | partial | ✅ | ✅ | ❌ | 1 / 11 | `matplotlib` |
| P04 | `numpy` | `Pillow` | partial | ✅ | ✅ | ❌ | 1 / 11 | `numpy` |
| P05 | `yaml` | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 空 |
| P06 | `pypdf`（材料 .md） | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 空 |
| P07 | `pypdf` + 材料是 PDF | `matplotlib` | partial | ✅ | ✅ | ✅ | 2 / 1 | `pypdf` |
| P08 | `PIL`+`matplotlib` | `pure-python-png` | partial | ✅ | ✅ | ❌ | 1 / 1 | 两个 |
| P09 | 四个全拦 | `pure-python-png` | partial | ✅ | ✅ | ❌ | 1 / 1 | `matplotlib, PIL` |
| P10 | LibreOffice 不存在 | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 空 |
| P11 | `pptx`+`yaml`+LibreOffice | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 空 |

降级原文（摘自报告，逐字）：

```
matplotlib 渲染不可用，已回退到备用渲染器：ImportError: degrade-probe: matplotlib is blocked on purpose
text drawn as placeholder boxes: no imaging library
材料是二进制文件，未发现文本层或不可读：material.pdf（未取得可读文本层，相关数值一律不上画布）
renderer backend 'Pillow' provides no vector PDF preview
```

## 4. 发现并修好的 1 处"不可见降级"

首轮实测 P03 / P08 / P09 判 `mismatch`：回退到 Pillow / 纯 Python 时，
`deliverables[format=pdf]` 为 `{"path": null, "present": false, "reason": null}` ——
**PDF 没了但没有原因**，与 `failure-modes.md` D12 的承诺不符。

修复（纯增量，`scripts/main.py` **净 +6 行**（在既有 `if/elif` 链上新增 1 个 `elif` 分支：4 行代码 + 2 行注释；无删改））后：

| 项目 | 修复前 | 修复后 |
|-|-|-|
| P02/P03/P04/P08/P09 判定 | mismatch | **ok** |
| `reason` | `null` | `renderer backend 'Pillow' provides no vector PDF preview` |

## 5. 最小可用环境（P09 实测）

| 能力 | 纯标准库 | 实测值 |
|-|-|-|
| 可编辑分层 SVG | ✅ | 产出（7 层 `layer:*`、真 `<text>`、`data-src`） |
| PNG | ✅ | `backend=pure-python-png` |
| `result.json` | ✅ | **26 键** |
| 退出码 / status | `0` / `partial` | 限制已列明 |
| PDF 预览 | ❌ | `present:false` + reason |
| 文字可读性 | ⚠️ | `render_log.warnings`：`text drawn as placeholder boxes` |

静态依赖面（`import_sites.pipeline`）：`matplotlib 5 · PIL 1 · pypdf 1 · numpy 0 · yaml 0 · pptx 0 · LibreOffice 0`。

## 6. 回归（不许因为修复而退化）

```bash
python scripts/fault_inject.py --out /tmp/fi --fail-on strict
```

| 项目 | 实测值 |
|-|-|
| exit code | **0** |
| `cases_run` / `ok` / `silent_failure` | **23 / 23 / 0** |

另外复核：`main.py` 冒烟 exit 0 / 26 键；`check_contract.py` exit 0；`spec_lint.py` 两道门 exit 0。

## 7. 对照测量（只读）

```bash
python scripts/gain_harness.py --out /tmp/ga-l1 --case examples/case.json \
       --material examples/material.md --label A-skill
```

| 指标 | 实测值 |
|-|-|
| exit code | **0** |
| 分层 / 真文字节点 | 7 层 / 61 个真 `<text>` |
| 溯源覆盖 | **56 / 62 = 0.903** |
| 四要素 / 数值可定位 | 4/4 / 14-16 |
| 契约 | 8/8，顶层 26 键 |

## 8. 合规与体积

| 项目 | 实测值 | 上限 |
|-|-|-|
| 文件数 | **45** | 50 |
| 总字节 | **452,345** | 2 MB |
| 最大单文件 | `examples/output/spec.json` **42,984 B** | 500 KB |
| 扩展名 | `.md .py .json .txt` | 七种白名单 |
| 符号链接 / `__pycache__` / `.pyc` | 0 / 0 / 0 | 0 |
| 本机绝对路径 | **0 命中**（字体探测候选路径除外） | 0 |

## 9. 复现判据清单

1. `main.py` → exit 0，`result.json` 26 键、`backend=matplotlib`。
2. `check_contract.py` → exit 0。
3. **`degrade_probe.py --fail-on strict` → exit 0**：12/12 `ok`、0 `crash`、12/12 写出 `result.json`。
4. `fault_inject.py --fail-on strict` → exit 0（23/23）。
5. `gain_harness.py` → exit 0。
6. 包内无 `__pycache__`、无本机绝对路径；45 文件 / 452,345 B。

## 10. 未验证 / 边界（如实声明）

- 只模拟 **`ImportError`**：库里装了但导入时抛别的异常、ABI 不匹配等未测。
- **字体缺失无法完整模拟**（本机系统字体真实存在），只能间接观测占位框与 `render_log.font`。
- **平台侧**（容器无解释器、磁盘满、挂载只读、配额、超时）不在本矩阵；`--out` 指向普通文件
  由 `fault_inject.py` F17 覆盖（exit 2）。
- 并发场景未测；场景均为串行。
- 降级是**有记录的降级**：纯 Python PNG 的文字是占位框，几何与图层仍正确。
- 随包示例案例均为**合成示意**，不是平台正式案例，不代表正式成绩。
