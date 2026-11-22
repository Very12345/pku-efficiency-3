# RUBRIC_MAP.md — 评分五维 → 机制 → 证据（文档轴 C：机制与复用）

> 题面评分：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**
> （GitHub 公开链接另计 +5）。
>
> 本轴的强化重心是「**创新增益 15**」与「**生态贡献 10**」，因此 §3 与 §5 写得最细：
> 每个机制都要求给出"没有它会怎样"（反事实）与"什么时候不管用"（失效条件），
> 每项生态资产都要求给出"复用时必须改什么"。其余三维按同一格式简写。
> 原则不变：**能复算的写进表，不能复算的标注为叙述性证据。**

## 1. 实际效果（40 分）

| 评分点 | 机制 | 证据 | 复算 |
|-|-|-|-|
| 任务完成度 15 | M1 单页四面板流水线；同时交付可编辑源与渲染件 | 产物清单、`spec.reading_order` | `python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-out`（exit 0） |
| 结果正确性 15 | M1 逐元素 `data-src`；负向关系红色；编码↔图例受 M2 门约束 | `audit.entity_coverage` / `encoding_consistency`；负控实验（删 1 个 `src` → exit 1） | `references/MECHANISM.md` §5 的 E1 |
| 结果完整性 5 | M1+M2：单位/比例尺/面板标签/来源脚注 + 四要素必齐 | `audit.four_element_coverage.missing == []` | `python -c "import json;print(json.load(open('/tmp/ga-out/audit.json'))['four_element_coverage'])"` |
| 结果可核验性 5 | M1 的 `data-src` + M3 的 `sources[]`(sha256) + 图层契约 | SVG 属性数、`result.sources`、`audit.layer_naming` | `grep -c 'data-src=' /tmp/ga-out/*.svg`（实测 56） |

## 2. 使用增益（25 分）

| 评分点 | 机制 | 证据 | 复算 |
|-|-|-|-|
| 质量增益 15 | M2 把错误拦在绘制前；M3 保证交付态可自动复核 | 方案/规格 lint 的 exit code；契约 8/8、顶层 26 键 | `spec_lint.py --lint-plan …`；`check_contract.py …`（均 exit 0） |
| 效率增益 5 | 方案骨架一步生成；`spec.json` 微调再出图；SVG 可直接续改 | 返工步数 0（首次运行即达标） | `references/GAIN-PROTOCOL.md` §4（含"单次墙钟 A 更慢"的口径） |
| 增益可验证性 5 | 尺子（`gain_harness.py`）+ 协议（`GAIN-PROTOCOL.md`）+ 真实记录（含不利项） | A/B/B+ 三条件指标 | `python "$SKILL_DIR/scripts/gain_harness.py" --out <dir> --case <case> --material <材料>` |

## 3. 创新增益（15 分）——本轴主强化①

| 评分点 | 内容 | 反事实（没有它会怎样） | 复算/证据 |
|-|-|-|-|
| 新增能力 5 | **三个机制**：M1 逐元素来源挂接、M2 双 lint 门（方案先行 + 规格门）、M3 契约四形态 + 状态一致性 | 图不可查（M1）、错误只能成图后发现（M2）、交付态无法自动复核或出现 null/虚报（M3） | `references/MECHANISM.md` §2–§4 逐机制展开 |
| 方法改进 5 | 把"设计决策"变成可 lint 的中间产物；把"图例↔数据一致""无源不上画布"变成退出码判据；把机制写成**可被负控实验验证**的形式 | 只能靠经验与肉眼，换一次运行就可能漂移 | 负控实验 E1/E2（各删 1 处 → **exit 1**）见 `MECHANISM.md` §5 |
| 创新证据 5 | 机制级证据链：**反事实 + 失效条件 + 实测数字**，并列出 5 项"未实现/未验证" | 只有功能清单时无法判断边界与价值 | `MECHANISM.md` §6（与常规做法边界表）/§8（未实现清单） |

> 本轴与前两轴的区别：A 轴把处置写成规则、B 轴把差别写成数字，**C 轴要求解释"为什么这个机制难以被常规做法稳定复现"** ——
> 因此 `MECHANISM.md` 里既有负控实验（证明机制真的生效），也有 E3 反例（证明它并非万能）。

## 4. 可靠体验（10 分）

| 评分点 | 机制 | 证据 | 复算 |
|-|-|-|-|
| 调用与易用性 3 | 单入口 + 可选 `--plan`；`$SKILL_DIR` 自定位；README 给出"资产清单 + 复用三步" | `README.md` §0/§1/§5 | `cd / && python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-cwd`（exit 0） |
| 运行稳定性 4 | K15 的字体/后端回退链并如实记录；同输入结构一致；双门在绘制前后拦截 | `render_log.json`；`determinism_probe` | `gain_harness.py --compare <run1> <run2>` → `structure_identical: true` |
| 异常处理 3 | K1–K16 按机制归组；每行给检测点、降级与证据；§5 明写机制管不到的地方 | `references/failure-modes.md` §2/§5 | `references/failure-modes.md` §7 的复现片段（含 K6/K9 负控） |

## 5. 生态贡献（10 分）——本轴主强化②

| 评分点 | 资产/做法 | 复用时必须改什么 | 复算 |
|-|-|-|-|
| 文档完整性 3 | 12 份文档：SKILL / README / TEST / OUTPUT_CONTRACT / RUBRIC_MAP / MECHANISM / REUSE-KIT / GAIN-PROTOCOL / failure-modes / plan-schema / ga-four-elements / layer-naming / TEMPLATE + examples 两份 | 各自换成你的领域内容；**契约字段名不改** | `find "$SKILL_DIR" -name '*.md' | sort` |
| 资源可复用性 4 | **可复用资产清单**（13 项，逐项给出"能做什么 / 复用前必须改什么"）：图层契约、四要素知识、方案 schema、契约与硬性门、面板模板、资产三件套、最小案例、测量器、对照协议、机制说明、决策矩阵、两个 exit-code 自查器 | 见 `references/REUSE-KIT.md` §1 表右列 | `references/REUSE-KIT.md` §1 + §4 三步移植 |
| 分享推广价值 3 | 题集/金标准协议（期望结构 + 来源定位 + 可接受区间 + 不确定性声明 + 三个难度层 + 版本记录）与"复用常见错误"6 条，可整块拿去组织团队内部的绘图评审 | 难度层按你的材料调整 | `references/REUSE-KIT.md` §2/§6 |

**生态角度的自证**：本轴的资产不是"再多写几份文档"，而是**每项资产都写明复用边界**
（例如：字体探测候选路径为什么可以留在包里、为什么渲染件不能进包、为什么金标准不能是图）。
这些边界来自真实的平台硬门（只允许 7 种文本扩展名、≤50 文件、无绝对路径），踩过才算资产。

## 6. GitHub 公开作品链接（+5）

`GITHUB_URL.txt` 第一行为本作品在该仓库中的精确链接（`final-var/graphical-abstract-7030fff2/v3`），
第二行为本作品在提交目录中的相对路径。

## 7. 本轴相对基线的增改

| 文件 | 性质 | 落到哪一评分点 |
|-|-|-|
| `references/MECHANISM.md` | **新增**：三个机制的"做什么 / 没有它会怎样 / 谁执行 / 什么时候不管用" + 与常规做法边界表 + 机制耦合 + 未实现清单 | 创新增益 15（全部三点） |
| `references/REUSE-KIT.md` | **新增**：13 项资产清单（含复用前必须改什么）、题集/金标准协议、发布前校验清单、三步移植、扩展点、常见错误 | 生态贡献 10（全部三点） |
| `references/GAIN-PROTOCOL.md` | **新增**（本轴写法）：以"五个问题"组织（能不能改/能不能查/讲全了吗/能自动复核吗/值不值得）+ 公平自检表 + 不利项 + 边界 | 使用增益 25 |
| `scripts/gain_harness.py` | **新增**：只读测量器（标准库） | 增益可验证性 / 资源可复用性 |
| `SKILL.md` | 重写：机制总览表（含反事实列）、机制→脚本→证据链、K1–K16 按机制分组、复用三步 | 创新增益 / 可靠体验 |
| `references/failure-modes.md` | 重写：按机制归组的 K 矩阵 + 机制管不到的 5 条边界（含 E3 反例）+ 复用/环境坑 | 可靠体验 / 创新证据 |
| `README.md` | 重写：新增"可复用资产清单"与"复用步骤"两节（本轴硬要求） | 生态贡献 |
| `TEST.md` | 重写：记录机制验证（负控实验 E1/E2/E3）与对照链真实数字 | 增益可验证性 / 创新证据 |
