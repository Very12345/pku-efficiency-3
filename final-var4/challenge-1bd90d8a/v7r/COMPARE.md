# COMPARE.md — 对照方案（v7 字节级可复现轴）

题面要求「使用增益」可验证，并明确写了「需要相对比较的评分项使用组织方预先固定的白板」。
本文件说明**本包自己能提供什么对照证据**，以及**哪些必须由平台/组织方提供**。

## 1. 本包能提供的对照：同输入同参数的重复运行

| 条件 | 做法 | 判定 |
|-|-|-|
| A：单次运行 | `main.py --case <case> --out <out>` | 产出是否完整（G1–G8） |
| B：重复运行（跨进程/跨 cwd/跨哈希种子） | `determinism.py --runs 5 --seeds 0,1,12345,7,99` | 全部产物 sha256 是否一致（阶梯 0/2/3/1） |

这不是「加载 Skill vs 不加载」的对照，而是**加载本 Skill 之后，结果本身稳不稳**的对照。
它是「增益可验证性」的前提：如果同一个 Skill 两次跑出不同字节，任何 A/B 对比都无法结论。

实测（本机）：阶梯 **2** —— 可编辑源与数据产物逐字节一致，`result.json`/两份报告的差异
100% 落在时间戳、运行根路径、自引用哈希、PDF 内嵌日期四类上（逐字段见
`references/DETERMINISM.md` §6）。

## 2. 与「不加载 Skill 的基础 Agent」的对照口径（供组织方白板使用）

本包**不提供**自己的白板结果（题面禁止参赛者提交预制答案或正式案例结果）。
但本包把对照所需的**同一把尺子**交给复核者：

| 比较维度 | 可机器判定的量 | 来自 |
|-|-|-|
| 图元 → 源数据闭合 | `mapcheck` 的 `checked/mismatches/unmatched`（实测 121/0/0） | `mapcheck.py --json` |
| 标注六项 + 契约 + 可编辑性 | `figcheck` 的 G1–G8 | `figcheck.py --json` |
| 契约字段覆盖 | `check_contract` 的 `missing/null/contract_missing`（实测 0/0/0） | `check_contract.py --json` |
| 可编辑矢量源 | SVG 分层 `<g id="layer-*">`、`<metadata id='provenance'>`、真实 `<text>` 未转曲 | `figcheck` G5 + `svgtext.check_no_text_to_path` |
| 重复运行一致性 | `determinism` 的阶梯与 `volatile_fields` | `determinism.py` |
| 产物指纹 | `result.json.artifacts_sha256` | 每次运行都写 |

这五个量对**任何**做法都成立 —— 基础 Agent 手写 matplotlib 也好、用别的工具也好，
都可以用同一组命令量一遍，因此对照是公平的（同输入、同数据版本、同导出参数）。

## 3. 本包内部的三方对照（结构层面）

| 文件 | 角色 | 本版是否改动 |
|-|-|-|
| `scripts/*.py`（10 个既有入口） | 算法与 CLI 接口 | **逐字节不变** |
| `scripts/determinism.py` | 本版新增的确定性实测台 | 新增 |
| `references/*.md`（既有 6 份） | 契约、评分映射、失败模式、编码规范、排版预设、字段映射 | 逐字节不变 |
| `references/DETERMINISM.md` | 本版新增：逐字段实测 + 稳定化配方 | 新增 |
| `determinism_report.json` / `determinism_inplace_report.json` | 本版新增：机器可读实测证据 | 新增 |

## 4. 诚实的边界

- 本包没有「不加载 Skill 的基础 Agent」的运行记录，也不会伪造一份 —— 那需要平台在同一输入上跑两侧。
- 本包的对照结论只覆盖**确定性维度**；「图的科学正确性是否提升」这类问题由
  `mapcheck`/`figcheck`/`check_contract` 三个机器判据回答，不靠自述。
- 阶梯 0 未在本机达到（原因见 `references/DETERMINISM.md` §8），本文件不把它写成"已通过"。
