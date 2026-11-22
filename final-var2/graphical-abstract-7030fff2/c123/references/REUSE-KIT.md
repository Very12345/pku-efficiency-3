# REUSE-KIT.md — 可复用资产清单、题集/金标准协议与校验清单

> 本文件回答的是「**别人能不能直接拿走用**」：
> 哪些资产可以整块复用、复用前必须改什么、怎么把自己的案例做成可复跑的题集、
> 发布前逐条勾什么。所有资产都在本包内以**纯文本**形式给出（`.md/.py/.json/.txt/.csv/.yaml/.yml`），
> 无二进制、无字体文件、无预置渲染件 —— 拉到本地即可直接用。

---

## 1. 资产清单（含"复用前必须改什么"）

| 资产 | 位置 | 直接拿去做的事 | 复用前必须改 |
|-|-|-|-|
| **SVG 图层命名契约** | `references/layer-naming.md` | 让你的图也具备"可定位、可机器校验"的分层结构（7 层 `layer:*` + `data-src/data-role/data-panel`） | 若新增图层：先在契约表登记，再同步 `scripts/audit.py` 的 `EXPECTED_LAYERS` |
| **四要素内容知识** | `references/ga-four-elements.md` | 判断"哪些内容必须上画布、哪些只能进图注"；面板容量上限表可直接抄 | 领域不同则调整"必须表达"的举例（不变式 Q-M-R-C 保留） |
| **方案 schema** | `references/plan-schema.md` | 把"设计决策"变成可 lint 的中间产物（`plan.json`） | `figure_constraints` 按你的出版要求改（尺寸/DPI/色盲/PDF） |
| **结果契约 + 硬性门** | `references/OUTPUT_CONTRACT.md` | 定义你自己的 `result.json` 字段与 G1–G8 门 | **不要改字段名**；新增字段走"契约字段"通道（四形态之一），不要塞进信封 |
| **面板模板 / 视觉通道 / 色彩与字号** | `references/TEMPLATE.md` | 直接套用四列面板布局、Okabe-Ito 色板、字号层级、负向关系红色约定 | 换期刊配色时可覆盖 `constraints.palette`；字号下限 8px 建议保留 |
| **资产三件套** | `assets/spec_template.json`、`assets/result_example.json`、`assets/example_material.txt` | 作为新案例的方案起点、结果形态示例、材料写法样例 | 三件套都是合成示例，替换成你的真实结构（`_meta` 字段说明其为示例） |
| **最小可跑案例** | `examples/`（`case.json` / `task.md` / `material.md` / `plan.example.json`） | 5 分钟内验证环境能否跑通（含 CP1 门与契约自查） | 换成你的案例（数值必须同时出现在材料里） |
| **只读测量器** | `scripts/gain_harness.py` | 量**任何**输出目录：分层数、真文字数、`data-src` 覆盖率、四要素覆盖、数值可定位率、契约覆盖、结构指纹 | 无需改；必要时在 `--case/--material` 指定你的输入 |
| **对照协议** | `references/GAIN-PROTOCOL.md` | 做一次公平对照（同输入/同约束/同判定），把"改进了多少"写成可复算的数字 | 条件 B 换成你自己的基线做法；指标口径保持一致便于横比 |
| **机制说明** | `references/MECHANISM.md` | 借用"机制 + 反事实 + 失效条件"的写法来写你自己的技术说明 | 换成你的机制；**保留"未实现/未验证"一节** |
| **决策规则与失败矩阵** | `SKILL.md` §3（K1–K16）+ `references/failure-modes.md` | 直接沿用"触发 → 动作 → 降级 → 记录位点 → 受害指标"的表结构 | 规则编号与两边保持一致；新增规则四处同号补齐 |
| **两个 exit-code 自查器** | `scripts/spec_lint.py`、`scripts/check_contract.py` | 在 CI 或提交前当门用（退出码即判据） | 契约字段变化时同步 `check_contract.py` 的信封键集合 |
| **题集/金标准协议 + 发布前校验清单** | 本文件 §2–§3 | 组织一套可复跑的绘图题集（期望结构 + 来源定位 + 可接受区间 + 不确定性声明 + 三个难度层），并按 §3 清单逐条勾 | 难度层与可接受区间按你的材料与领域调整；**金标准不要放渲染件** |

## 2. 题集与金标准协议（不提交预制答案）

平台的正式案例由组织方提供；**参赛者不自带正式案例、白板或预生成答案**。
若你想自建一套可复跑的内部题集（用于回归与对照），建议按下表组织：

| 组成 | 要求 | 为什么 |
|-|-|-|
| 案例输入 | `case.json`（结构/约束）+ `task.md`（任务）+ 材料文件（数值与机制的唯一来源） | 三者分离，才能验证"读的是真实文件而不是标签" |
| 金标准 | **期望结构 + 来源定位 + 可接受区间**，而不是一张"标准图" | 图有多种正确排版；结构、来源、区间才是可判定项 |
| 数值一致性 | 材料里必须能找到每个上画布数值（可用 `gain_harness.py` 的数值可定位率复核） | 直接把 M1 变成可测 |
| 不确定性声明 | 明确写"哪些判断是主观的、允许范围多大" | 避免把主观项当客观项判定 |
| 三个难度层 | ① 结构完整、数值齐全；② 缺 1–2 个数值；③ 材料含歧义/矛盾（考察降级路径） | 与"材料异常"分支一一对应（K1–K5） |
| 版本记录 | 材料与 case 的 `sha256` 进 `provenance.source_files` | 结论可回溯到具体字节 |

**反模式**：把渲染件（`.png/.pdf/.svg`）当金标准塞回包里 —— 既是平台硬门禁止的资源形态
（只允许 7 种文本扩展名），也会让回放 Agent 直接抄图而不去读材料。

## 3. 发布前校验清单（逐条可勾）

**A. 资源形态与合规**
- [ ] 文件数 ≤ 50；单文件 ≤ 500KB；合计 ≤ 2MB
- [ ] 扩展名只出现 `.md .py .json .txt .csv .yaml .yml`
- [ ] 无 `__pycache__` / `*.pyc` / 二进制 / 符号链接
- [ ] 包内无本机绝对路径（**例外**：字体探测的候选路径字符串，如 `C:/Windows/Fonts`，属探测逻辑）
- [ ] **不在包内跑脚本**（会在包内生成 `__pycache__`）；一切实跑在包外副本里做

**B. 自定位与接口**
- [ ] `SKILL.md` / `README.md` 的命令以 `$SKILL_DIR` 书写，在 `cwd ≠ 技能根` 时能跑通
- [ ] 文档里写的每个参数名与 `scripts/*.py` 的 `argparse` 逐字一致
- [ ] `python -m py_compile "$SKILL_DIR"/scripts/*.py` 通过

**C. 结构与契约**
- [ ] `main.py` 在示例案例上 exit 0，产出 SVG/PNG/PDF/`result.json`/`spec/content/audit/render_log`
- [ ] `check_contract.py` exit 0（顶层覆盖「信封 ∪ 案例契约」且无 null）
- [ ] `audit.four_element_coverage.missing`、`layer_naming.bad`、`encoding_consistency.missing_from_canvas` 均为空
- [ ] 同输入重跑结构指纹一致（`gain_harness.py --compare`）

**D. 诚实性**
- [ ] `uncertainty` / `warnings` 与真实降级一致；`status` 未虚报
- [ ] 增益/对照数字都来自实跑，且**包含对自己不利的观测**
- [ ] "未实现/未验证"清单存在且是最新的

## 4. 三步移植（把本包用到你的图上）

1. **换案例**：复制 `examples/case.json` → 替换 `entities/relations/data/figure_constraints`；
   把每个数值写进你的材料文件（这是 M1 的前置条件）；
2. **跑通四步**：`scaffold.py` → `spec_lint.py --lint-plan` → `main.py --plan` → `check_contract.py`；
   门不过就改 plan/spec 再跑，别绕过；
3. **复核**：`gain_harness.py --out <你的产物> --case <你的 case> --material <你的材料>`，
   记录 G1–G8；需要证明改进时，用同一把尺子量一遍你原来的做法（见 `GAIN-PROTOCOL.md` §7）。

## 5. 扩展点（改哪里、别改哪里）

| 想做的事 | 改哪里 | 不要动 |
|-|-|-|
| 新增图层（如 `timeline`） | `references/layer-naming.md` 登记 → `scripts/audit.py` 的 `EXPECTED_LAYERS` → 跑 audit 验证 | 不要只改 SVG 生成器，否则 audit 会判 `bad` |
| 新增视觉通道（如亮度） | `references/TEMPLATE.md` 的通道表 + `references/OUTPUT_CONTRACT.md` 的编码词表 → 再改 `figurespec.py` | 不要改已有通道名（历史产物会失联） |
| 新增指标 | `references/GAIN-PROTOCOL.md` §3 登记口径 → `scripts/gain_harness.py` 实现 → `TEST.md` 记一条真实数字 | 三处不齐不算加好指标（K16） |
| 新增面板类型 | `references/ga-four-elements.md` 的面板职责表 → `figurespec.py` 的 `_panel_content` | 不要破坏 Q-M-R-C 必齐不变式 |
| 换交付格式 | 只在 `deliverables[]` 增加条目并保证 `path` 相对且文件真实存在 | 不要把二进制塞进 Skill 资源目录（平台硬门） |

## 6. 复用时的常见错误（踩过的坑）

| 错误 | 后果 | 正确做法 |
|-|-|-|
| 数值只写在 `case.json`、材料里没有 | 图能出，但"可核验性"归零；对照时数值可定位率骤降 | 数值同时写进材料，或用 `case.json[字段]` 明确标注为来源 |
| 在包内直接跑 `scripts/main.py` | 生成 `__pycache__` → 平台预检/校验器 FAIL | 复制到包外目录再跑 |
| 把渲染件当示例放进包 | 平台只接受文本资源；`.png/.pdf/.svg` 会被拒 | 用 `examples/EXPECTED-OUTPUT.md` 以文字列清单 |
| 改 `OUTPUT_CONTRACT.md` 的字段名 | 契约自查失效、下游读取失败 | 只补说明，不改字段名与结构 |
| 只给自己有利的对照数字 | 评审视为自述、不予采信 | 连同不利项一起写（本包 GAIN-PROTOCOL §4.3 即为此） |
| 绕过 lint 门出货 | 结构问题进入交付，返工成本更高 | 门不过就改 plan/spec；确属硬限时降 `partial` 并写明 |
