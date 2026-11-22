---
name: paper-to-academic-ppt
description: 把论文/研究材料转换成主线清晰、证据可追溯、可编辑的学术汇报 PPT。本版是**全维 union**：可靠层（scripts/fault_inject.py 的 24 条真实故障注入 + references/FAULT-MATRIX.md 的实测矩阵，0 条静默失败）、泛化层（examples/cases/ 两个不同题材的合成案例 + scripts/run_case_set.py 的逐案验收，3/3 在区间内）、增益层（scripts/gain_probe.py 的三臂对照 + references/GAIN-PROTOCOL.md）、机制层（references/MECHANISM.md 的 9 项机制与"没有它会怎样"）、复用层（references/REUSE-KIT.md 的五步移植）与判断层（references/DECISION-RULES.md 的 D/H/M 三套编号 + 不变量 I1–I6）；执行链 输入→执行→失败→增益→机制→复用 逐段索引到各 reference。Use when a task asks to turn a paper or research material into an academic slide deck (论文转PPT、学术汇报PPT、slides from paper、presentation from paper), especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews.
---

# 论文转学术 PPT（全维 union 版 · paper-to-academic-ppt）

一份 Skill 要在评审里站住，需要同时回答五个问题。本包把每个问题各做成**一件可执行物**，
而不是各写一段说明：

| 问题 | 可执行物 | 实测结论 |
|-|-|-|
| **怎么用**（输入 → 执行） | `scripts/main.py` + §2/§3 流程 | 三个案例全部 `exit 0 / completed` |
| **坏了会怎样**（失败） | `scripts/fault_inject.py` → `references/FAULT-MATRIX.md` | 24 条注入 · **静默失败 0 条** · 恢复 19/19 |
| **换题材还成立吗**（增益·泛化） | `scripts/run_case_set.py` → `references/CASE-SET.md` | **3/3 案例在验收区间内** |
| **为什么这样做**（机制） | `references/MECHANISM.md`（9 项机制 + "没有它会怎样"） | 消融臂可归因到 M2 |
| **别人怎么搬走**（复用） | `references/REUSE-KIT.md`（五步移植 + 检查清单） | — |

**执行顺序**：**① 输入**（读 case/材料/契约）→ **② 执行**（方案先行 → CP1 → 构建 → 预览 → CP3）
→ **③ 失败**（D01–D19 + 注入矩阵）→ **④ 增益**（GA1–GA5 三臂对照）→
**⑤ 机制**（M1–M9，每条回答"没有它会怎样"）→ **⑥ 复用**（可复用资产 + 五步流程）。

**不负责**：论文精读结论的生成、科研绘图本身的图形设计、学术写作润色。
**不使用预制答案**：正式运行只依据案例实际提供的文件；`examples/` 只演示接口。

---

## 1. 输入（读什么、以什么为准）

| 方向 | 路径（以环境实际挂载为准） | 内容 |
|-|-|-|
| 输入 | `/input/case.json` | `case_id`、`output_contract`、材料/模板定位、受众/时长/页数 |
| 输入 | `/input/task.md` | 任务说明（存在时读取；缺失不阻断） |
| 工作 | `/app/work` | 抽取文本与图片、页级方案 `deck-spec.json` |
| 输出 | `/app/output` | `result.json`、`academic_deck.pptx`、`preview-approx-*.png`、`evidence_mapping.md`、`evidence_map.json`、`chart-*.png/.svg` |

**自定位**：`$SKILL_DIR` = `SKILL.md` 所在目录；脚本用
`os.path.dirname(os.path.abspath(__file__))` 自解析 + `sys.path.insert` 本目录，
**cwd 不是技能根也能跑**（两个演练执行件的子进程都以沙箱为 cwd，等于每跑一次就复核一次）：

```bash
SKILL_DIR="<SKILL.md 所在目录>"     # 平台安装到 /skills/weekly-skill 时即该路径
python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json
```

输入不在 `/input` 时探测 `CASE_PATH` / `OUTPUT_DIR` / cwd 下的 `case.json`（D14）。

**契约先行**：动笔之前先读 `references/OUTPUT_CONTRACT.md`。它是 `result.json` 的
**唯一事实源**——`scripts/check_contract.py` 直接解析它 §1 的字段表，因此改契约=改这一处
（机制 **M1 契约同源**）。

## 2. 执行（S0–S6，检查点 CP1/CP3）

| 阶段 | 动作 | 出口条件 |
|-|-|-|
| **S0 定位** | 读 `task.md` + `case.json`：取 `case_id`、`output_contract`、材料/模板、受众/页数；解析 `$SKILL_DIR` | 能说出"必须回显哪些字段" |
| **S1 读实际文件** | `python "$SKILL_DIR/scripts/assetkit.py" --pdf "<材料>" --out /app/work/extract`；PDF 走三级回退 | `sources[]` 有真实工具与页数/字数 |
| **S2 蓝图** | 按 `slide-blueprint.md` §1 重写为 问题→方法→证据→结论→局限；抽页级证据（编号/页码/图注/数值单位**逐字**） | 每张拟上页的图/表都有定位 |
| **S3 方案 + CP1** | 写 `/app/work/deck-spec.json`，跑 `spec_lint.py --spec ...` | `{"valid": true}`；偏差按 D06 处置 |
| **S4 构建** | `python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --spec <work>/deck-spec.json --out /app/output` | `.pptx` 存在（或按 D13 如实降级） |
| **S5 渲染 + CP3** | 无 Office ⇒ PIL 近似（三处标注）；有 `soffice` ⇒ 真 PDF；再跑 `export_check.py --result ... --out-dir ... --case ...` | 两道门 exit 0 |
| **S6 结果 + 自评** | 写 result.json（19 字段 + `case_id`），跑 `check_contract.py --case ...`，按 `RUBRIC_MAP.md` 自评 | 字段全覆盖、无 null |

模板三铁律：**只填占位符、不碰 master、不覆盖页脚/配色**；布局按名匹配 → 索引回退 →
内置版式；`template_mode="replace"` 移除起始页并记 `starter_slides_removed`。
**页数超限**按 D10 合并非证据页，**绝不静默丢弃证据页**。
**图文同页**按 D19：正文走左半幅，避免被插图覆盖（这是题集抓出来的静默丢失，见 §4）。

预算纪律：64 次模型请求 / 900 秒 / 单响应 16384 tokens（含推理）。先把 S1–S3 落盘成
中间件再增量交付；脚本本身秒级，不占模型预算大头。

## 3. 失败（先假定会坏，再证明坏了会被看见）

**决策表**：`SKILL.md` §4 是 D01–D19 精编版；**三套编号的完整表**（v1 的 D01–D16、
v2 的 H01–H14、v3 的 M01–M14 + 编号对照 + 不变量 I1–I6 + 检查点叫法对照）在
`references/DECISION-RULES.md`。

**演练一 · 故障形态**（可靠体验的硬证据）：

```bash
cp -r "$SKILL_DIR" /tmp/skill-drill
python /tmp/skill-drill/scripts/fault_inject.py --out /tmp/drill \
    --emit-matrix /tmp/drill/matrix.md; echo "exit=$?"     # 期望 0
```

对 **输入 / 模板 / 依赖 / 契约 / 状态** 五类形态注入 **24 条真实故障**——
真删文件、真写坏 JSON、真用 `meta_path` 钩子屏蔽 `pptx`/`PIL`/`matplotlib`/PDF 后端——
逐条实测 **退出码 / status / uncertainty·审计字段 / 是否静默失败**，并撤掉故障重跑一遍。
判定写死在代码里：**exit 0 + `status=completed` + 零留痕 = 静默失败**。
实测结论（`references/FAULT-MATRIX.md` §3）：**静默失败 0 条 · 与文档口径不一致 0 条 ·
恢复 19/19 回到 `exit 0 + completed` · 已知检测缺口 3 条（如实申报）**。

**这一轮演练改掉了 9 个真实缺陷**（4 类根因 + 1 个题集发现的静默丢失），逐条的文件 /
增删行数 / 理由见 `references/FAULT-MATRIX.md` §4，**全部纯增量**：
CLI 参数名、默认值、退出码语义一个都没改。

**承认的边界**（`references/failure-modes.md` §4–§5）：伪造 `status`、抹掉 `uncertainty`、
`case_id` 与案例不一致——静态产物校验器**拦不住**，必须人工兜底（三条命令写在 §5）。

## 4. 增益与泛化（"更强"必须能被测）

**演练二 · 题材与产物结构**：

```bash
cp -r "$SKILL_DIR" /tmp/skill-set
python /tmp/skill-set/scripts/run_case_set.py --out /tmp/case-out \
    --include-example --emit-md /tmp/case-out/case-set.md; echo "exit=$?"   # 期望 0
```

`examples/cases/` 下两个**不同题材**的合成案例（实验物理·μ 子透射成像分辨电池析锂；
临床流行病学·睡眠时长与代谢综合征横断面关联），连同最小示例一起逐案真跑，
对五类**可机检**的验收区间打分：`status` 词表 / 页数区间 / 证据行下限 /
`must_keep_verbatim` 的每个数字是否**逐字出现在产物文字里**（deck 全部文本框 + 备注 +
证据表）/ `must_not_claim` 的越界表述是否**不**出现。
实测（`references/CASE-SET.md` §2）：**3/3 案例在区间内**，两道门全 0-0，数字 8/8 命中。

**题集抓到的两个问题**（说明两种演练互为盲区补集）：
G1 图文同页时页级 bullets 被插图覆盖 ⇒ 该页文字从幻灯片 XML 里**静默消失**；
G2 页数预算只数内容页，而产物另加封面与收尾。

**演练三 · 三臂对照（使用增益）**：

```bash
python "$SKILL_DIR/scripts/gain_probe.py" --out <scratch> --arms baseline,skill,ablation --repeat 2
```

`baseline`＝"不加载本 Skill"的可执行代理（朴素单遍流水线），`skill`＝本包全链路，
`ablation`＝只摘掉"Agent 写的页级方案 + CP1 前置门"这一项机制。
指标定义与真实对照记录见 `references/GAIN-PROTOCOL.md`；**口径边界**写在 §6。

## 5. 机制（为什么这样做、拿掉会怎样）

`references/MECHANISM.md` 对 9 项机制各给四段：**常规做法 / 本包做法 / 没有它会怎样 / 边界**，
其中"没有它会怎样"要么是本机实测数字，要么是本族代码史或平台上有据可查的真实故障：

| 机制 | 一句话 | 证据 |
|-|-|-|
| **M1 契约同源** | 字段清单只在 `OUTPUT_CONTRACT.md` 里写一次，`check_contract.py` 直接读它 | 19/19 字段、`missing=[]` |
| **M2 方案先行 + CP1 前置门** | Agent 先写页级方案并过 lint，才允许生成 | 消融臂 `substantive_claim_coverage` 1.0 → 0.0 |
| **M3 双形态证据映射** | `evidence_mapping.md`（人读）+ `evidence_map.json`（机读）同源 | `evidence_rows = entries`，G7 校验 |
| **M4 占位诚实语义** | 图缺失 ⇒ 显式占位框，绝不画示意图冒充数据 | `figure.placed=null` + `placeholder=true` |
| **M5 主题字体注入** | latin + ea 双写，缓解换机字体替换 | `theme1.xml` 含 `Microsoft YaHei` + `Calibri` |
| **M6 对象分层命名** | 我们添加的每个形状按 `layer-naming.md` 命名 | `ooxml_kit.py` 命名审计 |
| **M7 仅文本资源 + 运行时生成** | 模板/预览/图一律运行时生成 ⇒ 包内无二进制 | 合规验收器：只有 7 种扩展名 |
| **M8 控制台与字节码卫生** | 非 UTF-8 控制台仍能打印中文日志；演练不产生 `__pycache__` | `cli_io.harden_console()`；`PYTHONDONTWRITEBYTECODE=1` |
| **M9 自定位** | 脚本按 `__file__` 自解析 ⇒ 任意 cwd 可跑 | 两个演练的子进程 cwd 都不是技能根 |

## 6. 复用（别人怎么搬走）

`references/REUSE-KIT.md`：**R1 搬骨架**（`scripts/` + 契约 + 命名规范）→
**R2 换题面与输入契约**（改 `OUTPUT_CONTRACT.md` §1 的字段表，`check_contract.py` 读的就是它）→
**R3 换蓝图映射**（`slide-blueprint.md` §1/§3）→ **R4 换配色与命名前缀**
（`ACADEMIC_THEME`、`PREFIX_BY_KIND`）→ **R5 跑校验命令并写回新数字**。

两件执行件是**为移植而写**的：

- `fault_inject.py --skill <任意技能根>`：换 `fixture()` 即可给别的 Skill 做失败注入
  （加一条注入的模板见 `FAULT-MATRIX.md` §6）；
- `run_case_set.py --cases <目录>`：只要四个文件（`case.json`/材料/`deck-spec.json`/
  `expected.json`）就能把新案例纳入题集（流程见 `CASE-SET.md` §5）。

## 7. 交付前自查清单（逐条）

- [ ] 已读真实 case.json / task.md / 材料；`sources[]` 有真实工具与页数/字数；
- [ ] 每页有 `claim`；bullets ≤6 条；`evidence` 或 `evidence_gap` 二选一；**CP1 通过**或偏差双写；
- [ ] 页上数字/单位/方法名/图号与原文逐字一致（抽查 ≥3 处）；**图文同页按 D19** 未被覆盖；
- [ ] 备注与页面文字分离（含封面/收尾页），`notes_separated=true`；
- [ ] 模板：占位符填充、master 未动；损坏回退已记 `template.error`；
- [ ] `/app/output` 有 `result.json`（19 字段 + `case_id`）、`.pptx`、预览、双形态证据映射；
- [ ] **CP3** `export_check` exit 0；`check_contract --case` exit 0；四形态回显无 null；
- [ ] 降级双写齐全；`status` 与 `uncertainty`/证据缺口自洽；
- [ ] 引用增益/可靠性数字时写明**命令**，并写明它是本机结构性对照而非平台分数；
- [ ] 三格检测缺口按 `failure-modes.md` §5 人工兜底过（不是"知道有这回事"）。

## 8. 限制与口径边界

- 预览是 **PIL 近似渲染**，不等于 PowerPoint/LibreOffice 结果；本机无 LibreOffice；
- PDF 图片抽取依赖库与版式，个别图只以显式占位框呈现（**不代表**论文原图）；
- 模板适配为"占位符级"：SmartArt 不重排；模板自带形状不改名；
- 结论正确性上限 = 论文原文；本 Skill 不验证论文结论；
- **对照口径**：`gain_probe.py` 的 `baseline` 是"基础 Agent 行为"的可执行代理，
  不是对某个具体 LLM 的测量；`wall_seconds` 只反映脚本开销；**平台白板对照仍是权威口径**；
- **演练口径**：24 条注入证明**可观测性**（坏了会不会被看见），不证明**可用性**；
  三个案例证明"不同题材下仍产出可验收产物"，不预测平台分数；
- **未验证、不得声称支持**（`CASE-SET.md` §4）：扫描件/图像型 PDF、>20 页大汇报、
  非中英文材料、真正的组织方模板、多篇材料合并；
- 包内只携带文本资源（`.md/.py/.json/.txt/.csv/.yaml/.yml`），首次运行前需 `python-pptx`。

## 9. 维护（改什么就要重跑什么）

- 版本：`scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；
- **改任一降级行为 ⇒ 重跑 `fault_inject.py` 并重渲染 `FAULT-MATRIX.md`**（旧数字作废）；
- **改任一页级版式行为 ⇒ 重跑 `run_case_set.py` 并重渲染 `CASE-SET.md` §2**；
- 改机制 ⇒ 同步 `MECHANISM.md`（必须仍能回答"没有它会怎样"）；
- 改 D/H/M 任一套规则 ⇒ 同步 `references/DECISION-RULES.md` 的编号对照与
  `references/failure-modes.md` 的同号条目（三处一致才算改完）；
- 改 GA 指标 ⇒ 同步 `GAIN-PROTOCOL.md` §3 并在 `TEST.md` 追加**新跑出的**数字；
- 新增可复用资产 ⇒ 追加到 `REUSE-KIT.md` §1，写清"位置 / 形态 / 怎么用"；
- 修改记录同时进 result.json 的 `change_records` 与 git 提交历史。
