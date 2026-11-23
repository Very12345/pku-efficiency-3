# TEST.md — 本机实测记录（可复现优先版）

> 所有数字都是本机在**包外临时副本**上真跑得到，没有任何估计值。
> 环境：Windows / Python **3.13.9** / matplotlib 3.10.6 / Pillow 12.3.0 / pypdf 6.14.2（2026-11-23）。
> **绝不在包内跑脚本**：`main.py` 等入口会在 `scripts/` 下生成 `__pycache__`，
> 直接导致合规验收 FAIL。所有命令都先复制到包外：

```bash
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2
PKG=/tmp/ga-pkg && rm -rf "$PKG" && cp -r "$SKILL_DIR" "$PKG" && cd "$PKG"
```

---

## 1. 主链冒烟（L1 最小示例）

```bash
python scripts/main.py --case examples/case.json --out /tmp/ga-l1
```

| 项目 | 实测值 |
|-|-|
| exit code | **0** |
| `status` | **success** |
| `result.json` 顶层键数 | **26**（信封 18 + 案例契约 8） |
| `deliverables` | `svg, json(layout_spec), png, pdf` 四件 |
| `audit.four_element_coverage` | 4/4，`missing=[]` |
| `audit.layer_naming` | `bad=[]`、`elements_without_src=0` |
| `audit.determinism_probe.spec_sha16` | `9bcb54b29fe658d4` |
| `spec_lint` | `valid=true`，`spec_sha16=92a22433141dc61a` |
| `uncertainty` / `warnings` | `[]` / `[]` |

## 2. 契约门

```bash
python scripts/check_contract.py --result /tmp/ga-l1/result.json --case examples/case.json
```

| 项目 | 实测值 |
|-|-|
| exit code | **0** |
| `valid` | **true** |
| 信封键 | **18/18** |
| 案例契约字段 | **8/8**（`target_format, resolution_dpi, colorblind_safe, require_legend, require_scale_bar, layer_names, provenance_attr, deliverable`） |
| null 违规 | 0 |

## 3. ★ 复现判据（本轴主判据）

```bash
python scripts/determinism.py --case "$PWD/examples/case.json" --out /tmp/det --runs 3
python scripts/determinism.py --case "$PWD/examples/case.json" --out /tmp/det5 --runs 5 \
       --hashseeds 0,1,42,12345,-
```

| 项目 | 3 次 | 5 次 |
|-|-|-|
| exit code | **0** | **0** |
| `verdict` | `canonical-stable` | `canonical-stable` |
| `checks.files_compared` | 8 | 8 |
| `raw_identical_files` | 5 | 5 |
| `normalized_identical_files` | **8** | **8** |
| `raw_diff_files` | `*.pdf`、`render_log.json`、`result.json` | 同左 |
| `declared_volatile_fields` | 2 | 2 |
| `unexplained_differences` | **0** | **0** |
| `structure_probe.spec_sha16` | 3 次全 `9bcb54b29fe658d4` | 5 次全同 |
| `seconds_total` | 3.92 s | 11.67 s |

逐产物（5 次运行，`raw` / `normalized`）：

| 产物 | 字节 | raw | normalized |
|-|-|-|-|
| `spec.json` | 42,986 | ✅ | ✅ |
| `content.json` | 6,979 | ✅ | ✅ |
| `audit.json` | 2,169 | ✅ | ✅ |
| `*.svg` | 32,455 | ✅ | ✅ |
| `*.png` | 397,555 | ✅ | ✅ |
| `result.json` | 6,709 | ❌（时间戳） | ✅ |
| `render_log.json` | 645 | ❌（run 路径） | ✅ |
| `*.pdf` | 148,129 | ❌（CreationDate） | ✅ |

运行矩阵（5 次）：cwd = `<skill-root>` / 空目录 / `<case-dir>` / `<skill-root>` / 空目录；
`PYTHONHASHSEED` = `0 / 1 / 42 / 12345 / 未设置`；**5 次 exit 均为 0**，墙钟 2.04–2.56 s。

判据两端都测过：

| 命令 | exit | 说明 |
|-|-|-|
| `--fail-on normalized`（默认） | **0** | 掩码后 8/8 一致 |
| `--fail-on raw` | **1** | **故意**为 1：`result.json`/`render_log.json`/`*.pdf` 含真实时间或调用路径 |
| `--fail-on none` | **0** | 只采数据 |

**稳定化配方实测**：`SOURCE_DATE_EPOCH=1700000000` 下两次运行产出的 PDF **逐字节相同**
（`sha256 3e00d54352b170c0…`，148,123 B，头内 `D:20231114221320Z`）；不设该变量时两次不同。

**阴性对照（判据可被证伪）**：在包外副本里给 `common.write_json()` 注入一个随机字段后：

| 项目 | 实测 |
|-|-|
| exit / `verdict` | **1** / `unstable` |
| `raw_identical_files` | **2 / 8** |
| `normalized_diff_files` | 5 个（`audit/content/render_log/result/spec`） |
| `unexplained_differences` | **1**：`result.json:_negctrl`（`0.832…` / `0.452…` / `0.903…`） |

**守卫（用法错误必须干净退出）**：

| 命令 | exit |
|-|-|
| `--out` 指向包内目录 | **2** |
| `--case` 指向不存在的文件 | **2** |
| `--runs 1`（越界） | **2** |

## 4. 失败注入（四形态，23 条，真跑子进程）

```bash
python scripts/fault_inject.py --out /tmp/fi --fail-on strict
```

| 项目 | 实测值 |
|-|-|
| exit code | **0**（`--fail-on strict`） |
| `cases_run` / `ok` / `mismatch` / `silent_failure` | **23 / 23 / 0 / 0** |
| 分类 | input 7 · template 6 · dependency 5 · contract 5 |
| 耗时 | 约 30–60 s |

## 5. 对照测量（只读，本轴不改图）

```bash
python scripts/gain_harness.py --out /tmp/ga-l1 --case examples/case.json \
       --material examples/material.md --label A-skill
```

| 指标 | 实测值 |
|-|-|
| exit code | **0** |
| 分层 / 真文字节点 | **7 层** `layer:*` / **61** 个真 `<text>`（`glyph_use` 0） |
| 溯源覆盖（`data-src`） | **56 / 62 = 0.903** |
| 四要素覆盖 | **4/4** |
| 数值可定位 | **14 / 16**（未定位：`001`、`6.5`，按严格口径记录） |
| 契约 | **8/8，verdict=complete**，顶层 **26** 键 |
| 证据文件 | `result.json` / `audit.json` / `render_log.json` / `spec.json` 齐备 |

## 6. 合规与体积

| 项目 | 实测值 | 上限 |
|-|-|-|
| 文件数 | **45** | 50 |
| 总字节 | **444,249** | 2 MB |
| 最大单文件 | `examples/output/spec.json` **42,984 B** | 500 KB |
| 扩展名 | `.md .py .json .txt` | 七种白名单 |
| 符号链接 / `__pycache__` / `.pyc` | 0 / 0 / 0 | 0 |
| 本机绝对路径 | **0 命中**（`C:/Windows/Fonts` 等为跨平台字体探测候选路径，属运行时探测逻辑） | 0 |

## 7. 复现判据清单（照这个顺序跑）

1. `main.py` → exit 0，`result.json` 26 键、`status ∈ {success, partial}`。
2. `check_contract.py` → exit 0（信封 18 + 案例契约 8，无 null）。
3. **`determinism.py --runs 3` → exit 0，`unexplained_differences` 为空**；`spec_sha16` 逐次相同。
4. `fault_inject.py --fail-on strict` → exit 0，`silent_failure == 0`。
5. `gain_harness.py` → exit 0，输出含 `editable/provenance/four_elements/numbers/contract/evidence`。
6. 包内无 `__pycache__`、无本机绝对路径；45 文件 / 444,249 B。

## 8. 未验证 / 边界（如实声明）

- **不测跨机器**：本报告只证明"同一台机器、同一套依赖、同一份输入"下的 L1 一致性；
  `.png` 像素与系统字体绑定、`.pdf` 头与绘图库版本绑定，换机器可能变字节（见 `references/DETERMINISM.md` §7）。
- **不测并发**：`determinism.py` 串行跑 N 次；两个进程同时写同一 `--out` 未测。
- **平台侧故障**（挂载缺失、配额、容器超时）不在任何矩阵范围内。
- **渲染链真实可达**的是「matplotlib → Pillow → 纯 Python PNG」：matplotlib 自身 `import PIL`，
  屏蔽 Pillow 会连带 matplotlib 失效（`references/FAULT-MATRIX.md` §3 记录；本题姊妹版本 v9 的降级矩阵 P02 亦同）。
- 随包示例案例均为**合成示意**，不是平台正式案例，不代表正式成绩。
