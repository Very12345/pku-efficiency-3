# TEST.md — 本机实测记录（v6 全维合并版）

> 所有数字都是本机在**包外临时副本**上真跑得到，没有估计值。
> 环境：Windows / Python **3.13.9** / matplotlib 3.10.6 / Pillow 12.3.0 / pypdf 6.14.2（2026-11-22）。
> **绝不在包内跑脚本**（会生成 `__pycache__`，直接导致合规验收 FAIL）。

```bash
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2
PKG=/tmp/ga-pkg && cp -r "$SKILL_DIR" "$PKG" && cd "$PKG"
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
| `result.json` 顶层键数 | **26** |
| entities / relations / data | 6 / 5 / 7 |
| `audit.entity_coverage` | 6/6，`missing=[]` |
| `audit.missing_values` | `[]` |
| `audit.four_element_coverage` | 4/4 |
| `audit.layer_naming` | `bad=[]`、`elements_without_src=0` |
| `audit.bounds.outside_count` | 0 |
| `audit.determinism_probe.spec_sha16` | `9bcb54b29fe658d4`（两次运行一致） |
| `spec_lint` | `valid=true`，`spec_sha16=92a22433141dc61a` |
| PNG 后端 | `matplotlib` |
| `uncertainty` / `warnings` | `[]` / `[]` |

## 2. 契约门

```bash
python scripts/check_contract.py --result /tmp/ga-l1/result.json --case examples/case.json
```

| 项目 | 实测值 |
|-|-|
| exit code | **0** |
| 信封键 / 案例契约字段 | **18/18** · **8/8** |
| null 违规 | 0 |

## 3. 失败注入（23 条，真跑子进程）

```bash
python scripts/fault_inject.py --out /tmp/ga-fi --fail-on strict
```

| 项目 | 实测值 |
|-|-|
| exit code | **0**（`--fail-on strict`） |
| `cases_run` / `ok` / `mismatch` / `silent_failure` | **23 / 23 / 0 / 0** |
| 总耗时 | **30.7 s** |
| 分类 | input 7 · template 6 · dependency 5 · contract 5 |
| 对照（未修复的同源脚本，同一套用例） | `ok 10 / mismatch 5 / silent 8` |

修复前 8 条静默失败：F04 材料路径缺失、F05 二进制材料、F07 方案文件缺失、F09 未定稿骨架、
F11 关系缺 `src`、F13 matplotlib 缺失、F16 pypdf 缺失、F18 契约字段为 `null` ——
全部是"进程 exit 0 且 `status=success`，而缺陷在 `uncertainty` 里没有记录"。
逐行对照与修复点名（F1–F9 / G1–G5 / P1，含增删行数）见 `references/FAULT-MATRIX.md` §2。

## 4. 增益测量（只读测量器）

```bash
python scripts/gain_harness.py --out /tmp/ga-l1 --case examples/case.json \
       --material examples/material.md --label A-skill
```

| 指标 | 实测值（本机 `A-skill`） |
|-|-|
| exit code | **0** |
| 分层 / 真文字节点 | 7 层 `layer:*` / **61** 个真 `<text>` |
| 溯源覆盖（`data-src`） | **56 / 62 = 0.903** |
| 四要素覆盖 | **4/4**（conclusion/method/question/results） |
| 数值可定位 | **14 / 16**（未定位：`001`、`6.5` —— 见 GAIN-PROTOCOL §4.3 的诚实口径） |
| 契约 | **8/8，`verdict=complete`**，顶层 **26** 键 |
| 证据文件 | `result.json` / `audit.json` / `render_log.json` / `spec.json` 齐备 |
| 单次墙钟 | 2.441 s / 2.156 s（B 条件为 1.707 / 1.514 s，**A 更慢**，见下） |

**必须一起读的对照事实**（来自 `references/GAIN-PROTOCOL.md` §4.1/§4.3）：
A 单次更慢；确定性 B 也两次一致（A 的贡献是把复现性做成可检查字段）；
A 的溯源覆盖率是 0.903 而不是 1.000（残差是关系组容器）。**不取好看的数字。**

## 5. 题集三案

| 案例 | 题材 | 难度层 | exit | `status` | 键数 | relations | `missing_values` | `uncertainty` | `check_contract` | 两次 `spec_sha16` |
|-|-|-|-|-|-|-|-|-|-|-|
| `example-micelle-001` | 纳米医学 | L1 | 0 | success | 26 | 5 | `[]` | 0 条 | 0 | `9bcb54b29fe658d4` 一致 |
| `calab-perovskite-001` | 材料/能源 | L2 | 0 | success | 26 | **9** | `[]` | 0 条 | 0 | `8b1b2a88fc72eff3` 一致 |
| `urban-heat-001` | 地球/环境 | L3 | 0 | **partial** | 26 | 8 | `['夜间地表温度差']` | **2 条** | 0 | `d12251c822cf4141` 一致 |

L3 的 `uncertainty` 原文（两条都必须出现）：

```
以下数据点缺少可核验数值：夜间地表温度差（已在图上以“数值缺失”占位标记，未编造数值）
材料与 case.json 数值不一致（首见优先，未取平均）：夏季平均反照率：case.json 取 0.14，材料另给 0.19（两处 src=case.json[data] / material:35）
```

三案共同判据：`entity_coverage.missing=[]`、`encoding_consistency.missing_from_canvas=[]`、
`four_element_coverage` 4/4、`layer_naming.bad=[]` 且 `elements_without_src=0`、
`bounds.outside_count=0`。逐案输入 / 期望结构 / 可接受区间见 `references/CASE-SET.md`。

## 6. 合规与体积

| 项目 | 实测值 | 上限 |
|-|-|-|
| 文件数 | **49** | 50 |
| 总字节 | **422,939** | 2 MB |
| 最大单文件 | `examples/output/spec.json` **42,984 B** | 500 KB |
| 扩展名 | 仅 `.md .py .json .txt` | 七种白名单 |
| 符号链接 / `__pycache__` / `.pyc` | 0 / 0 / 0 | 0 |
| 本机绝对路径 | 0 命中（`C:/Windows/Fonts` 等为跨平台字体探测候选路径） | 0 |

## 7. 复现判据

1. 主链 `exit 0`，`result.json` 26 键，`status ∈ {success, partial}`。
2. `check_contract.py` **exit 0**（三案均如此）。
3. `fault_inject.py --fail-on strict` **exit 0**，`silent_failure == 0`。
4. `gain_harness.py` **exit 0**，输出含 `provenance/four_elements/numbers/contract/evidence` 五组指标。
5. 三案各自两次运行 `determinism_probe.spec_sha16` 一致。
6. 包内无 `__pycache__`、无绝对路径；49 文件 / 422,939 B。

## 8. 未验证 / 边界（如实声明）

- 注入不覆盖**平台侧故障**（挂载缺失、配额、容器超时）与**材料内容真伪判断**。
- 增益对照只做了本机一次连续会话（A/B/B+ 六次出图），**没有跨机器或跨模型复测**；
  单次墙钟会随机器变化，结论性列（覆盖是否为空、契约是否通过、缺值是否留痕）不随机器变化。
- 渲染链真实可达的是「matplotlib → 纯 Python PNG」：matplotlib 自身 `import PIL`，
  屏蔽 Pillow 会连带 matplotlib 失效（FAULT-MATRIX §3）。
- 三案均为合成示意，不是平台正式案例，不代表正式成绩。
- 未覆盖扫描件 PDF（无文本层）真实样本的文本层质量。
