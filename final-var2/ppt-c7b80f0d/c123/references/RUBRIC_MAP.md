# RUBRIC_MAP.md — 五维评分落点（本版以**创新增益 15 + 生态贡献 10**为主轴）

> 交付前自评的唯一对照表。官方题面维度：
> **实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**（+ GitHub 附加 5）。
> 本版的强化选择是"把机制与复用讲清楚"，因此 §1/§2 展开创新增益与生态贡献，
> §3 给出其余三维的落点，§4 是题面六类要素速查，§5 是自评口径。
> 纪律：**表中每条复核命令都必须能当场跑出同一结果。**

## 1. 创新增益 15 分逐条落点

| 评分点 | 分 | 题面要求（原意） | 本版落点 | 复核方式 |
|-|-|-|-|-|
| **新增能力** | 5 | "基础 Agent 或现有方案不具备、或难以稳定实现的能力" | ① **契约同源核对**：`check_contract.py` 打开 `OUTPUT_CONTRACT.md` 解析字段名再逐字段比对（解析不出即 exit 2）② **页级证据映射双形态**（md 人读 + json 机读，同源生成 + 行数守恒门 G7）③ **对象分层命名**（把"可编辑"变成可机检量 `named_shapes`）④ **运行时资源自生成**（模板/预览/重建图/夹具全部现产，包内只有 7 种文本扩展名） | `check_contract.py` → 19/19；`gain_probe.py` 报告里的 `named_shapes`（基线 0 vs 全链路 3/17）；`validate_pkg.py` → PASS |
| **方法改进** | 5 | "主线抽取、页结构映射、图表对齐、备注生成等方法是否带来实质改进，而非包装" | **方案先行 + 前置 lint 门（K1）**：先把论文重写成页级 `deck-spec.json`（每页一主张 + 证据或显式 gap），过 BL-1…BL-4 才允许生成；配合蓝图映射（问题→方法→证据→结论→局限）替代段落切片 | **消融实测**：摘除该机制后 `substantive_claim_coverage` 1.0→0.0、`evidence_rows` 6→1、`notes_pages` 8/8→3/6、`rework_points` 0→2。命令：`python "$SKILL_DIR/scripts/gain_probe.py" --out <scratch> --arms baseline,skill,ablation --repeat 2` |
| **创新证据** | 5 | "证明创新点相对已有方案（通用 PPT 生成工具、手工排版流程、其他课题产出）的边界与价值" | `references/MECHANISM.md`：9 项机制，每项四段（常规做法 / 本包做法 / **没有它会怎样** / 边界），反事实要么是本机实测数字、要么是有据可查的真实故障；§4 给出与通用工具 / 手工排版 / 其他课题 / 不加载 Skill 的边界表 | 读 `MECHANISM.md` §2 各条的"证据与复核"；每条都能落回 `TEST.md` 的某一项或一次探针运行 |

## 2. 生态贡献 10 分逐条落点

| 评分点 | 分 | 本版落点 | 复核方式 |
|-|-|-|-|
| **文档完整性** | 3 | `README.md`（依赖/安装/用法/限制/维护 + 复用步骤）+ `SKILL.md`（三层结构：机制/执行/证据）+ `references/` 六份（`MECHANISM` / `REUSE-KIT` / `GAIN-PROTOCOL` / `OUTPUT_CONTRACT` / `RUBRIC_MAP` / `failure-modes` / `slide-blueprint` / `layer-naming`）+ `TEST.md`（实测）+ `GITHUB_URL.txt` | `find "$SKILL_DIR" -type f`；`README.md` 与 `SKILL.md` §3 的资源清单逐行对应 |
| **资源可复用性** | 4 | `references/REUSE-KIT.md` §1 明列五类资产：**题集**（`examples/` 三件套 + 合成材料）、**金标准**（`EXPECTED-OUTPUT.md` 的文字清单 + 6 条验收阈值）、**校验清单**（5 条命令 + 判据）、**导出预设**（deck-spec schema / 蓝图映射表 / 证据表格式 / 四形态规则 / 退出码语义 / 14 个对照指标）、**配色与规范**（`ACADEMIC_THEME` 七个色值 + 字体策略 + 诚实标注规范 + 命名规范）；§2 给出五步移植流程、§3 移植检查清单、§4 诚实列出"不可直接复用"的部分 | 打开 `REUSE-KIT.md` §1 逐表核对文件是否存在；按 §2 的 R1–R5 在另一题上走一遍 |
| **分享推广价值** | 3 | ① 把演示类交付物的验收从主观判断变成 **5 条命令 + G1–G8 硬门**；② 把"更强"变成**三臂可复跑对照**；③ 把"可编辑"变成 `named_shapes` 这一可机检量；④ `REUSE-KIT.md` §5 明确可迁移的题面类型（任何"长文档 → 离散页级表达 + 保留溯源 + 适配给定模板"）与公开入口 | `REUSE-KIT.md` §5 + `GITHUB_URL.txt` 第一行（提交前用未登录窗口打开确认） |

## 3. 其余三维落点

| 维度 | 分 | 本版落点 | 复核命令 |
|-|-|-|-|
| **实际效果** | 40 | `SKILL.md` §4 阶段 1–7（关口 K1/K3）；`main.py` 串起抽取→构建→预览→检查→契约；正确性由 BL-1…BL-4 + G1–G8 反查；完整性靠必需页自动补齐 + M08 合并规则；可核验性靠双形态证据映射 + `run_meta.checkpoints` | `main.py --case "$SKILL_DIR/examples/case.json" --spec "$SKILL_DIR/examples/deck-spec.json" --out <tmp>/out` → exit 0；两道门 exit 0 |
| **使用增益** | 25 | `references/GAIN-PROTOCOL.md` + `scripts/gain_probe.py`：三臂（baseline/skill/ablation）同输入对照，14 个指标，两组真实记录（条件 T / 条件 N），口径边界四条；`SKILL.md` §6 的机制→证据矩阵 | `python "$SKILL_DIR/scripts/gain_probe.py" --out <scratch> --arms baseline,skill,ablation --repeat 2` → `skill.rework_points = 0`，`baseline.rework_points = 6` |
| **可靠体验** | 10 | 触发词 + §2 输入输出 + §4 三步调用；脚本 `__file__` 自定位（两种调用风格均 exit 0）；**六条回退链**（材料/图片/模板/字体渲染/契约/依赖）见 `failure-modes.md` §2；M01–M14 每条给出触发/首选/降级/记录；退出码 0/1/2/3 统一 | `TEST.md` 的 T-C2/T-C8/T-C11；`main.py --case <不存在> --out <tmp>` → exit 3 |

## 4. 题面六类要素覆盖速查

| 题面要素 | 本包实现位置 |
|-|-|
| 1 主线提取 | `slide-blueprint.md` §1 蓝图映射表；`deck-spec.slides` 即叙事骨架（问题→方法→证据→结论→局限） |
| 2 页结构与信息分层 | `spec_lint` BL-1/BL-2（claim 必填、bullets ≤6 条且 CJK 加权 ≤110）；生成期 `MAX_BULLETS/MAX_CHARS_BULLET` 再截断 |
| 3 图表引用与证据保留 | 每页 `figure`/`table`/`evidence` 带 `ref` + `page`；缺失走链 B（占位框 + `placed=null`）；双形态证据映射 + G7 行数守恒 |
| 4 讲解逻辑与备注 | `deckgen._add_notes` 写 `notes_slide`（主张 + 过渡/强调 + 被问证据），含封面与收尾页；`notes_separated=true` |
| 5 模板约束与版面适配 | 链 C 四级回退：占位符填充 → 名匹配/索引回退 → 补画文本框（登记命名）→ 内置版式；master 与页脚不动 |
| 6 导出渲染与可编辑性 | 可编辑 `.pptx`（对象按 `layer-naming.md` 命名）+ PIL 近似预览（诚实标注）+ 重建图 PNG/SVG + K3 的容器/命名/证据表校验 |

## 5. 自评口径（防止把"没测"说成"通过"）

1. **数字来源**：引用任何增益数字前，先确认它有对应的运行目录与 `gain-report.json`；
   降级运行（见 `failure-modes.md` §4）不得计入"加载后的优势"。
2. **口径边界**：`gain_probe.py` 的 `baseline` 是结构性代理而非具体 LLM 的测量；
   `wall_seconds` 只反映脚本开销；平台白板对照仍是权威口径。
3. **条件隔离**：条件 T（模板在场）与条件 N（无模板）的数字分开引用，不混用。
4. **单案例限制**：所有对照建立在合成示例案例上，不能外推到所有论文类型。

## 6. 维护

- 版本：`scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；本表随能力/机制变更同步更新；
- **三处同步**：改机制 → `MECHANISM.md`；改规则 → `failure-modes.md` 同号条目；
  改指标/数字 → `GAIN-PROTOCOL.md` §3–§4 与 `TEST.md`（**禁止沿用旧数字**）；
- 新增可复用资产 → `REUSE-KIT.md` §1 追加一行，写清"位置 / 形态 / 怎么用"；
- 题面评分维度若更新，先改本表再改实现，避免"文档承诺 > 代码事实"。
