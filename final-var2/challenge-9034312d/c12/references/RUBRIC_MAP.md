# RUBRIC_MAP.md — 评分五维落点（v2 增益可验证化版）

题面评分维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10
· GitHub 链接 +5**。本文件的编排与基线不同：**按"分值从高到低"排，并把"使用增益"
这一列写到最细**——因为题面把 25 分给它，而其中 5 分明确要求"通过公平对照证明"。

**一句话定位**：基线的 25 分那一栏只有一段"对照维度"说明；本版把它升级为
**可复跑的协议 + 真跑过的记录 + 独立复算脚本**三件套，并且**主动记录了一条负面结果**
（运行效率没有增益）。这里的每一行都指向一个能算出来的量，不是一个形容词。

## 0. 五维速查

| # | 维度 | 分 | 落点 | 可复跑验证 |
|-|-|-|-|-|
| 1 | 实际效果 | 40 | `main.py` 一键出图 + 可编辑分层 SVG + 真实 PNG/PDF + 四份 JSON | 四形态实测 `exit 0`（0.49–0.55 s）；契约 **18/18**；`check.py` `ok:true` |
| 2 | **使用增益** | **25** | **`GAIN-PROTOCOL.md`（协议）+ `COMPARISON-RECORD-20261122.md`（真跑记录）+ `comparison-data.json`（原始数据）+ `gain_probe.py`（独立复算器）+ `bare_baseline.py`（C0 下界）** | §2 的三段式：条件 → 指标 → 数字 |
| 3 | 创新增益 | 15 | SIR → 确定性布图 → 三后端共享布局 + **把"增益"本身做成可复算协议** | `spec_sha16` 跨运行恒定；C1/C2 的 SVG sha 相同（audit 差可归因） |
| 4 | 可靠体验 | 10 | D1–D14 + 状态聚合优先级 + `check.py` 退出码 0/1/2/3 + `failure-modes.md`（含 R1–R6） | 负例 `exit 3`；`decision` 类异常见 `failure-modes.md` |
| 5 | 生态贡献 | 10 | 文档 + 可复用资产（规则字典/配色/核对清单/**对照协议与复算脚本**） | 改 `connection_rules.json` 或 `palette.json` 后重跑即生效 |
| +5 | GitHub | 5 | `GITHUB_URL.txt` | 未登录浏览器可打开 |

## 1. 实际效果（40）= 完成度15 + 正确性15 + 完整性5 + 可核验性5

| 评分点 | 覆盖 | 证据 |
|-|-|-|
| 完成度 15 | 材料 → 可编辑分层 SVG（5 层 `layer:*`、真实 `<text>`、实体组带 `data-*`）+ 真实 PNG（39–47 KB @200 DPI）+ 矢量 PDF + `evidence/layout/verify_report/result.json`；四图类自动选模板 | `scripts/main.py`；`TEST.md` T2（四形态 exit 0，各产出 7 文件） |
| 正确性 15 | 证据先行（逐条 `locator`+`quote`）+ 连接规则机器审计 + 断头关系丢弃 + 编号 1..N + 图例 kind == 图面 kind | `gain_evidence.py`；`svg_verify.py`；对照记录 §2.2（Q2：1 → 0） |
| 完整性 5 | 题面六类要素全覆盖：实体 / 空间关系（`layout.json` 的 x,y,w,h）/ 数据编码（kind→形状配色）/ 图例 / 可编辑源文件 / 导出格式 | `layout.json`；`figure.svg` 五层；`templates/palette.json` |
| **可核验性 5** | 除常规（四份 JSON 落盘 + 确定性探针）之外，本版把**"增益本身"也做成可核验**：`gain_probe.py` 只读公开字段即可复算 Q1–Q6 | `cmp` 记录 §2；`gain_probe.py`；`comparison-data.json` |

## 2. 使用增益（25）= 质量15 + 效率5 + 增益可验证性5

### 2.1 质量增益（15）

对照条件、固定项与指标定义见 `references/GAIN-PROTOCOL.md §1–§3`；
数字全部来自 `references/COMPARISON-RECORD-20261122.md §2`（单轮实测，非估计）。

| 质量指标 | C0 下界 | C1 本包 | 判定 |
|-|-|-|-|
| Q1 来源绑定率 | 0.00 | **1.00** | 达标（每个图面元素都有 `locator`） |
| Q2 断头端点外露数 | **1**（缺陷案例） | **0** | 达标（不画不存在的连接） |
| Q3 违规暴露数（缺陷案例） | 0（无审计） | **3**（2 error + 1 warn） | 与预注入缺陷对得上 |
| Q3 违规暴露数（干净案例） | 0 | **0** | **与 C2 同为 0 —— 负面观察，如实记录** |
| Q4 可编辑源文件 | `<text>` 0 个 / 无 `data-*` | true / true | 达标 |
| Q5 真实导出件 | PNG 0 B / PDF 0 B | PNG 39–47 KB / PDF 4.0–4.5 KB | 达标 |
| Q6 状态诚实性 | 无 `status` 字段 | `partial` + 退出码 3（缺陷）/ `success`（干净） | 达标 |

### 2.2 效率增益（5）—— 本版的诚实结论

| 效率指标 | C0 | C1 | 结论 |
|-|-|-|-|
| E1 单轮耗时 | 0.100–0.112 s | **0.497–0.593 s** | **慢 4.4–5.3 倍：运行效率无增益** |
| E2 产物字节 | 2.5–3.8 KB | 78–105 KB | 大 27.6–31.5 倍（产出真 PNG/PDF 所致） |
| E3 人工干预步骤 | ≥ 3 步（补溯源 / 查连接 / 真渲染） | **0 步** | 有增益 |
| E4 返工轮次 | 1 轮（重画） | **0 轮**（`--merge` 增量） | 有增益 |

⇒ 本包**不声称"运行更快"**；效率增益落在"人工少做几步、少重画几轮"。
把 E1/E2 与 E3/E4 混在一起说"效率提升"，本包不做。

### 2.3 增益可验证性（5）—— 本版的重点

| 要求 | 本包怎么满足 | 证据 |
|-|-|-|
| 公平对照 | 三个条件（C0 下界 / C1 本包 / **C2 同代码关掉门禁**）+ 四个固定项（同输入 sha、同任务书、同环境、同预算单轮） | `GAIN-PROTOCOL.md §1–§2` |
| 指标可测 | 6 个质量指标 + 4 个效率指标，每个给算式、判定规则、测量对象 | `GAIN-PROTOCOL.md §3.2–§3.3` |
| 有真实记录 | 2 案例 × 3 条件 × 1 轮 + 2 轮确定性对拍，逐项原始值 + sha16 | `COMPARISON-RECORD-20261122.md §2`；`comparison-data.json` |
| 第三方能重跑 | 三条命令即可复现；`gain_probe.py` **不 import 包内模块**，也能用来核别人的同类包 | `GAIN-PROTOCOL.md §4.1/§5` |
| 不作断言 | 明确写出"不能支撑什么"（不能论证比某模型高 X 分、不能论证更快） | `COMPARISON-RECORD-20261122.md §4` |

## 3. 创新增益（15）= 新增能力5 + 方法改进5 + 创新证据5

| 评分点 | 覆盖 | 证据 |
|-|-|-|
| 新增能力 5 | ①SIR 结构化中间表示 → 据其布图与自检；②证据先行；③规则资产驱动审计；④**增益协议化**（把"我更强"变成条件×固定项×预注册指标×可复算脚本） | `model.py`；`gain_evidence.py`；`connection_rules.json`；`GAIN-PROTOCOL.md` |
| 方法改进 5 | ①三后端共享同一布局模型；②校验内建于流水线；③确定性探针；④`--merge` 编辑闭环；⑤**C2 条件的引入**让"算法输出"与"审计增益"可以被分离归因（实测两臂 SVG sha 相同） | `layout.py`/`render_svg.py`/`export_preview.py`；`COMPARISON-RECORD §2.4` |
| 创新证据 5 | 边界与价值文档化：与既有方案差异、适用条件、限制、**两条负面结果**（干净输入上门禁无差异；运行效率无增益） | `README.md`；`SKILL.md §8`；`GAIN-PROTOCOL.md §6` |

## 4. 可靠体验（10）= 调用易用3 + 运行稳定4 + 异常处理3

| 评分点 | 覆盖 | 证据 |
|-|-|-|
| 调用易用性 3 | 单命令从输入到导出；`SKILL.md §2` 给接口与三种形态；脚本自定位、任何 cwd 可运行 | `SKILL.md §2`；`TEST.md` T2/T5 |
| 运行稳定性 4 | 结构化/文本解构双路径；布局无随机；四形态实测 `exit 0`；**对照实验证明同输入两轮逐字节一致** | `TEST.md` T2/T3；`COMPARISON-RECORD §2.4` |
| 异常处理 3 | 材料异常 / 模板缺失（含 `--rules` 空与缺失）/ 依赖缺失 / 契约四形态 / 状态一致性；退出码 0/1/2/3 语义明确 | `SKILL.md §6`；`references/failure-modes.md`；负例 `exit 3` |

## 5. 生态贡献（10）= 文档3 + 复用4 + 分享3

| 评分点 | 覆盖 | 证据 |
|-|-|-|
| 文档完整性 3 | 使用说明、输入约定、图元规范、导出参数、示例与期望产物、限制、维护；**新增协议与记录两份文档** | `SKILL.md`/`README.md`/`TEST.md`/7 份 `references/`/2 份 `templates/` |
| 资源可复用性 4 | 规则字典、配色模板、两份核对清单、结果形态示例、SIR 与导出脚本，**外加：对照协议 + 指标复算器 + C0 下界实现**（可直接搬到同类题） | `assets/`、`templates/`、`scripts/gain_probe.py`、`scripts/bare_baseline.py`、`references/GAIN-PROTOCOL.md` |
| 分享推广价值 3 | 沉淀图例规范、布局经验、连接规则字典、失败清单与打包门 R1–R6；**以及一套"如何证明自己更强"的协议模板** | `references/`（7 份）；`GITHUB_URL.txt` |

## 6. GitHub 公开作品链接（+5）

- `GITHUB_URL.txt` 第一行：公开仓库中本作品位置的直链；可选第二行写相对文件路径；
- 题面要求"提交前用未登录 GitHub 的浏览器窗口打开一次"，本包不含需登录的地址。

## 7. 改包后的自检顺序

```bash
SKILL_DIR=/skills/weekly-skill

# 1) 功能没坏
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/out      # exit 0
python "$SKILL_DIR/scripts/check.py" /tmp/out/demo-biotech-route-01/result.json      # exit 0, ok:true

# 2) 增益协议仍可复算（本版新增的核心自检）
printf '{}' > /tmp/empty-rules.json
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --rules /tmp/empty-rules.json --out /tmp/c2
python "$SKILL_DIR/scripts/gain_probe.py" --result /tmp/out/demo-biotech-route-01/result.json \
       --baseline /tmp/c0 --json /tmp/q.json
python "$SKILL_DIR/scripts/bare_baseline.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/c0

# 3) 确定性（增益可验证性的前提）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/det-B
#   figure.svg / layout.json / verify_report.json 的 sha 应与上次一致

# 4) 负例（异常必须被暴露，且状态诚实）
python "$SKILL_DIR/scripts/main.py" --case <违例案例> --out /tmp/neg              # 期望 exit 3, status=partial
```

## 8. 覆盖缺口（诚实声明）

- **没有跑过任何真实模型**：C0 是"可执行下界"，不是"基础 Agent 的行为录像"；
  平台白板才是正式相对比较的依据，本包不据此宣称任何分数或倍数；
- **样本量小**：2 个合成案例 × 3 条件 × 1 轮；不做统计显著性结论；
- **干净输入上门禁无差异**（Q3 两侧都是 0）：门禁的价值只能在带缺陷输入上被量出来，
  这条限制写进了 `GAIN-PROTOCOL.md §6`；
- **`evidence.json` 的 sha 随运行目录变化**（`sources[].path` 记运行时真实路径）：
  对拍内容请用 `figure.svg`/`layout.json`/`verify_report.json`；
- 图内数值注记不强制渲染；局部放大视图未内置；装置图为单层装配（三桶布局）；
- `examples/` 是**合成**示例（标注「示例，非正式案例」），不含预制答案，不冒充正式结果；
  包内冻结的 `examples/output/**/result.json` 因不含运行期图稿，对它跑 `check.py`
  会如实报 G3/G4——正确自查对象是新跑出来的那份。
