# RUBRIC_MAP.md — 评分五维 → 落点 → 复算（文档轴 B：增益可验证）

> 题面评分：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**
> （GitHub 公开链接另计 +5）。
>
> 本文件的写法与前作不同：每一行都给**可以当场跑的命令或可以直接读的字段**。
> 凡是没有复算路径的自述，一律不写进本表 —— 因为题面明确"文字自述不能替代实际运行证据"。
> 本轴（B）的强化重心是「使用增益 25」，因此 §2 的每一行都指向
> `references/GAIN-PROTOCOL.md`（协议）与 `scripts/gain_harness.py`（测量器）。

## 1. 实际效果（40 分）

| 评分点 | 落点 | 复算 |
|-|-|-|
| 任务完成度 15 | 四面板单页（问题/方法/结果/结论）+ 阅读顺序 + 面板内实体/关系/数据；同时交付可编辑源与渲染件 | `python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-out`（exit 0）→ 产物清单见 `/tmp/ga-out` |
| 结果正确性 15 | 逐元素 `data-src`；数值只来自材料；负向关系（抑制）红色；数据编码与图例受 lint 约束 | `python "$SKILL_DIR/scripts/gain_harness.py" --out /tmp/ga-out --case "$SKILL_DIR/examples/case.json" --material "$SKILL_DIR/examples/material.md"` → 看 G2/G4 |
| 结果完整性 5 | 单位、比例尺、面板标签、来源脚注；四要素覆盖 | 同一命令 → 看 G3；`python -c "import json;print(json.load(open('/tmp/ga-out/audit.json'))['four_element_coverage'])"` |
| 结果可核验性 5 | `data-src` + `sources[]`(sha256) + `change_records` + 图层命名规范 | 同一命令 → `grep -c data-src= /tmp/ga-out/*.svg`；`audit.layer_naming` |

**B 轴的额外要求（已满足）**：以上每一项都必须能被**第三方**在**不看本包自述**的情况下复算 ——
因此把测量逻辑独立成 `scripts/gain_harness.py`（只读、只用标准库），而不是写在文档里让人照抄结论。

## 2. 使用增益（25 分）——本轴主强化

| 评分点 | 落点 | 复算 |
|-|-|-|
| 质量增益 15 | ①数值可追源（lint 硬门）②布局确定性（结构指纹一致）③文字可编辑（真 `<text>` + 图层契约）④四要素齐全。**并以 A/B/B+ 三种条件的实测指标呈现差距** | ①`gain_harness.py --out <A>` → G2/G4；②`--compare <run1> <run2>` → G6；③同一命令 → G1；④同一命令 → G3。原始记录见 GAIN-PROTOCOL §4 |
| 效率增益 5 | 减少返工与跨软件搬运：`scaffold.py` 一步出方案骨架；`spec.json` 微调后再出图；SVG 源可直接续改。**诚实口径：单次墙钟 A 慢 0.5–0.9 s，收益在"首次运行即达标"（E2=0）** | GAIN-PROTOCOL §4 的 E1/E2 两行；`time python "$SKILL_DIR/scripts/main.py" ...` |
| 增益可验证性 5 | 协议 + 测量器 + 原始记录三件套；指标口径写明"怎么算"，反例（对 A 不利的观测）也写进去 | [`references/GAIN-PROTOCOL.md`](GAIN-PROTOCOL.md) §3（口径）/§4（记录）/§4.3（不利项）/§7（移植步骤） |

> 为什么把不利项写进去：题面要的是"通过**公平对照**证明质量或效率改善"。
> 只报有利项的对照不是公平对照；写明"哪一项 A 不占优"反而使结论可被采信。

## 3. 创新增益（15 分）

| 评分点 | 落点 | 复算 |
|-|-|-|
| 新增能力 5 | 四元抽取（实体—关系—数据—面板）+ 统一图面规格；方案先行（可 lint 的中间产物）；四要素不变式；图层命名契约可执行化 | `spec_lint.py --lint-plan --plan "$SKILL_DIR/examples/plan.example.json"`（exit 0） |
| 方法改进 5 | **把"增益"本身产品化**：固定条件的对照协议 + 只读测量器 + 可复算指标（G1–G8），使"用了有没有变好"不再靠自述；另有确定性布局、图例↔数据一致性校验、导出检查固定为流水线环节 | `gain_harness.py` 的 `--help` 与 GAIN-PROTOCOL §3 对照；`--compare` 验证 G6 |
| 创新证据 5 | 与常规方案的边界：常规单页信息图工具既不保留可编辑源与逐元素溯源，也不提供可复算的增益口径；本包让"哪一项改善、改善多少"可被第三方重跑 | 详见 [`references/GAIN-PROTOCOL.md`](GAIN-PROTOCOL.md) §4/§5 |

## 4. 可靠体验（10 分）

| 评分点 | 落点 | 复算 |
|-|-|-|
| 调用与易用性 3 | 单入口 + 可选 `--plan`；`$SKILL_DIR` 自定位；测量器与出图分离（测量器不会污染产物目录） | `cd / && python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-cwd`（exit 0） |
| 运行稳定性 4 | 后端/字体回退链并如实记录；同输入结构一致；方案/规格 lint 前后双门 | `python -c "import json;print(json.load(open('/tmp/ga-out/render_log.json'))['backend'])"`；`--compare` |
| 异常处理 3 | R1–R14（`SKILL.md` §5）+ 每行的**受害指标**（`references/failure-modes.md` §2），故"兜底没做"能直接对应到"哪一项指标掉"；退出码 0/1/2 语义明确 | `references/failure-modes.md` §7 的复现片段（缺输入→1、未定稿骨架→1、定稿→0、契约→0） |

## 5. 生态贡献（10 分）

| 评分点 | 落点 | 复算 |
|-|-|-|
| 文档完整性 3 | SKILL / README / TEST / OUTPUT_CONTRACT（字段名不改）/ RUBRIC_MAP / GAIN-PROTOCOL / failure-modes / plan-schema / ga-four-elements / layer-naming / TEMPLATE / examples 文档 | `find "$SKILL_DIR" -name '*.md' | sort` |
| 资源可复用性 4 | **测量器可被任何项目直接复用**（不依赖本包的图）；图层命名规约、面板模板、`spec.json` 中间规格、资产三件套、最小示例、两个 exit-code 自查器 | `python "$SKILL_DIR/scripts/gain_harness.py" --out <任意输出目录> --label mine` |
| 分享推广价值 3 | 对照协议与指标口径本身可分享（团队内可用来评审任何绘图流程）；纯文本包便于 fork/PR | GAIN-PROTOCOL §7「把本协议用到你自己的项目（三步）」；`GITHUB_URL.txt` |

## 6. GitHub 公开作品链接（+5）

`GITHUB_URL.txt` 第一行为本作品在该仓库中的精确链接（`final-var/graphical-abstract-7030fff2/v2`），
第二行为本作品在提交目录中的相对路径。

## 7. 本轴相对基线的增改

| 文件 | 性质 | 落到哪一评分点 |
|-|-|-|
| `references/GAIN-PROTOCOL.md` | **新增**：可比条件、指标 G1–G8 口径、A/B/B+ 实测记录、不利观测、条件 B 最小复现、移植步骤、可追溯性清单 | 使用增益 25（全部三点） |
| `scripts/gain_harness.py` | **新增**：只读测量器（标准库；`--compare` 结构指纹） | 增益可验证性 5 / 资源可复用性 4 |
| `SKILL.md` | 重写：可比性设计表、指标表、步骤→证据映射、决策速查 R1–R14、增益摘要 | 使用增益 / 可靠体验 |
| `references/failure-modes.md` | 重写：R1–R14 矩阵新增「打掉哪个指标」列 + 受害指标优先级排序 | 可靠体验 3 |
| `README.md` | 重写：出图四步 + **复算增益三步** + 维护规则（加指标需三处齐） | 调用易用性 / 生态 |
| `TEST.md` | 重写：出图链与对照链的真实数字（含 A/B/B+ 指标与退出码） | 增益可验证性 5 |
