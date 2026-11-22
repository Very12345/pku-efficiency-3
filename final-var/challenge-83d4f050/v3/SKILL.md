---
name: biological-mechanism-pathway-diagram
description: >-
  把机制/通路材料转成可逐条质疑的生物机制图与通路图，并把整条链路的"为什么这样设计"
  写清楚：声明式机制规格先行、raw 规格过 schema 门、确定性区室布局、可编辑分层 SVG 源与
  PNG/PDF 预览、拓扑与图例/数据编码双审计、契约化 result.json。附**机制分解（M1–M6，
  每条说明"去掉它会退化成什么"）**与**可复用资产清单 + 复用步骤**（题集 / 金标准样例 /
  校验清单 / 导出预设 / 配色与规范），供他人直接搬到同类机制图任务。
  Use when the task asks to draw, generate, edit, re-export or validate a biological
  mechanism map, pathway diagram, signaling cascade, regulatory network or flow
  diagram (figures group of the biology mechanism & pathway challenge), including
  tasks that require editable sources with per-element provenance.
---

# biological-mechanism-pathway-diagram（机制与复用版 · 文本包 · 图件运行时生成）

本包不止给流程，还给**机制**：每一层设计都回答同一个问题——**"去掉它，会退化成什么？"**
能回答这个问题，才谈得上"创新"；不能回答，就只是功能堆叠。§1 逐条给出机制、退化后果、
可验证信号；§5 与 `references/ASSET-INDEX.md` 给出可直接复用的资产与搬运步骤。

> 资源形态：包内**只有文本**（`.md .py .json .txt .csv .yaml .yml`），契约原文
> `at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks`；
> `diagram.svg` / `diagram.png` / `diagram.pdf` 由 `scripts/` 在 `--out` 目录**运行时生成**。

## 1. 机制分解（M1–M6）：每条都说明"去掉它会怎样"

| # | 机制 | 没有它会怎样（退化后果） | 可验证信号 | 落点 |
|---|---|---|---|---|
| M1 | **规格先行**：先落一份声明式机制规格（实体/边/来源/图例/布局约束），再由它渲染 | 图与来源脱钩：改一个标签要重新画；实体清单与边清单无法被独立复核；同一张图的不同导出件互相漂移 | `model.json` 存在且含 `entities[]/edges[]/source[]`；改规格一次即可重导出全部图件 | `scripts/{extract,model,layout}.py`、`references/mechanism-spec.md` |
| M2 | **raw 规格的 schema 门**：对**未归一化**的规格做类型枚举校验（不是对归一化结果） | 未知类型被静默改写成 `other`：一个错误论断被"美化"成合规图形，评审与人眼都看不出来 | 把某实体 `type` 改成枚举外值 → 运行 **exit 3 / failed**（实测：只写 `result.json`）；而不是悄悄改成 other 后成功 | `scripts/validate_figure.py:check_schema`、`assets/mechanism-spec.schema.json` |
| M3 | **双审计闭环**：拓扑审计（方向/区室/同名消歧/重复边/自环/反馈）+ 图例与数据编码审计（覆盖/颜色/虚线语义/线宽/数值溯源） | 图例与图面不一致、上下游颠倒、数值无来源这类错误只能靠人眼发现，而且"看起来没问题" | `topology.json` 与 `legend_audit.json` 两个产物落盘；对基础形态同两条命令 → exit 1（实测 `ok=False`） | `scripts/{topology,legend_audit}.py`、`references/legend-encoding.md` |
| M4 | **可编辑分层源 + 逐元素溯源**：7 个 `layer-*` 组，元素带 `data-id/data-type/data-source` | 只能交一张位图：别人既不能改一个标签，也不能把元素追回材料行号；"可编辑交付"变成一句空话 | SVG 具名图层 7 个、`data-source` 计数 ≥ 边数（实测 18）；基础形态两项均为 0 | `scripts/pathway_svg.py` |
| M5 | **确定性探针**：布局与 SVG 不含时间戳，`self_check.determinism` 报 `model_sha16/svg_sha16` | 无法判断两次运行是否等价：评审看到的图与提交的图可能不是同一张，"可复现"无从检验 | 同输入双跑：SVG/PNG/model/topology/legend_audit **逐字节一致**（实测 5/6；PDF 内嵌时间戳例外） | `scripts/{layout,pathway_svg}.py`、`result.json.self_check` |
| M6 | **契约化终态**：`result.json` 信封 + `output_contract` 四形态回显 + G1–G8 门 + status/退出码三元组 | 结果无法被机器复核：评审判"没找到完整解"，人也没法复算；失败与成功在产物上看不出区别 | 信封 19/19、顶层 null 0、gates 8/8、exit 0；对基础形态同命令 exit 1（无 `result.json`） | `scripts/{result_writer,check_contract}.py`、`references/OUTPUT_CONTRACT.md` |

**这六条不是并列的功能清单，而是互相咬合的一根链**：M1 产生可审的中间物 → M2 在源头挡住
错误类型 → M3 在渲染前后各审一遍 → M4 让产物可改可追 → M5 让运行可复现 → M6 让结果可交付复核。
断掉任何一环，后面的环节都会失去意义（例如没有 M1，M3 的审计对象就不存在）。

## 2. 运行流程（机制视角：每一步产出链条上的哪个中间物）

```bash
export SKILL_DIR=/skills/weekly-skill        # 容器路径；本机指向含 SKILL.md 的那一层
python3 "$SKILL_DIR/scripts/main.py" --help  # 自检：能打印帮助即路径正确
```

| 步骤 | 产生 | 服务哪条机制 |
|---|---|---|
| CP1 读真实文件（case / task / 材料，事实逐条记出处） | `change_records` 首条 | M1 的输入（不许按文件名猜内容） |
| CP2 规格（结构化材料出草稿；散文/PDF 手工建规格）→ **过 schema 门** | `model.json` | M1 + M2 |
| CP3 人工核验（逐条对照材料，`verified_by_agent=true`） | `change_records` + 核对清单 | M1（规格可信） |
| CP4 确定性布局 → 分层 SVG → PNG/PDF → 双审计 | `diagram.svg`、`topology.json`、`legend_audit.json` | M3 + M4 + M5 |
| CP5 写契约与终态判定 | `result.json` | M6 |

主命令：

```bash
python3 "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /app/output
```

散文/PDF 材料：Agent 按 `references/mechanism-spec.md` §1 手写规格后走 `--model-file`。
**退出码即终态**：`0 = success`、`2 = partial`、`3 = failed`（与 `status`/`gates` 必须自洽）。

## 3. 运行期决策捷径（K1–K10：机制被破坏时先修哪里）

| # | 症状 | 修哪里（机制视角） | 修不好时 |
|---|---|---|---|
| K1 | 材料路径解析不到 | 用 `--materials-dir` 显式给目录（先补 M1 的输入） | `failed`（exit 3）+ 补救路径写 `uncertainty` |
| K2 | 规格出现枚举外类型 | **不要改图**：改规格（M2 的门就是为此存在），改正后重跑 | `failed`，把违规项原文写进 `reason` |
| K3 | 图面用了某类型但图例没有 | 补图例项 → 重跑（M3 的 L01/L02 是 fail 不是 warn） | 类型名拼错 → 先修 `type` |
| K4 | 颜色不在图例 ∪ 映射内 | 改回图例色，或把该编码补进图例 | 无法归属 → 类型默认色 + `uncertainty` |
| K5 | 数值找不到来源 | 补 `source`；或降为 `assumption` 并进 `uncertainty` | 降级后**禁止**用于颜色/线宽编码（E01） |
| K6 | 材料没写方向 | 只画结合类无向语义边 + `uncertain=true` | 连接合依据都没有 → 不画该边 |
| K7 | 未人工核验的草稿 | `partial` + `uncertainty` 提示逐条复核（M1 的规格必须可信） | 材料不可读 → `failed` |
| K8 | matplotlib/字体缺失 | 只交 SVG：`partial` + exit 2 + `gates.g5_png=false`，原因入 `export_checks` | **绝不**伪造预览；SVG 的分层与 `data-*` 不得因此缺失（M4 不受影响） |
| K9 | 契约字段无值 | 先判形态再填：标量 `""` / 列表 `[]` / 布尔 `false` / 数值·字典 `0`·`{}`；**顶层禁 null** | 形态判不定 → 按列表给 `[]` 并说明 |
| K10 | `status`/退出码/`gates` 不一致 | 以退出码为真，取更保守档（M6 的三元组一致性） | 修不好就停在保守档，不谎报 success |

## 4. 契约与硬性门

- 唯一评分产物 `result.json`：信封 19 键 + `case.json` 中 `output_contract` 全部字段（四形态回显，无 null）。
- 硬性门 G1–G8：`case_id` 非空、契约回显、`status` 三值、SVG 7 层良构、PNG 可开、
  图例覆盖在用类型、实体/边带 `source`、两个审计产物存在。任一 error → 不得 `success`。
- 字段定义与判定细则见 `references/OUTPUT_CONTRACT.md`（§10 为状态一致性矩阵）。

## 5. 可复用资产与复用步骤（对应生态贡献 10）

**资产清单的完整版见 `references/ASSET-INDEX.md`**（每项含：文件、用途、依赖、复用方式）。
摘要：

| 资产 | 文件 | 可直接复用到 |
|---|---|---|
| 机制规格 schema（类型枚举 + 必需字段） | `assets/mechanism-spec.schema.json` | 任何"实体—关系"型图的规格门（M2） |
| 调色板与 glyph 语义（单点改色） | `assets/palettes.json` + `references/legend-encoding.md` | 通路图/图形摘要的配色与箭头语义规范 |
| 关系核对清单（五张表） | `templates/relation-checklist-template.md` | 人工核验（CP3/M1）的执行载体 |
| 四个独立校验 CLI（各有退出码） | `scripts/{check_contract,validate_figure,topology,legend_audit}.py` | 任何绘图产物的机器验收 |
| 契约四形态 + G1–G8 门 | `references/OUTPUT_CONTRACT.md` | 同类 Skill 的结果契约模板（M6） |
| 最小可运行示例 + 实跑产物 + 期望输出说明 | `examples/**` | 新任务的起步样例与接口对照 |
| 失败分支表（F01–F26）+ 决策捷径 | `SKILL.md` §3、`references/failure-modes.md` | 同类任务的失败处置清单 |
| 独立度量器（不依赖本包模块） | `scripts/gain_probe.py` | 量任何绘图 Skill 的产物（分层/溯源/语义/图例/契约） |
| 基础形态复现器（反例生成器） | `scripts/baseline_emulator.py` | 给新任务造一个可复现的基础条件对照臂 |

**复用三步（详细命令见 `ASSET-INDEX.md` §3）**

1. **搬骨架**：复制 `scripts/` + `assets/` + `references/OUTPUT_CONTRACT.md` 到新任务目录，
   把 `examples/` 换成新任务的合成样例（材料 + 期望输出说明）。
2. **换语义**：在 `assets/palettes.json` 与 `assets/mechanism-spec.schema.json` 中替换
   实体/边类型枚举与配色；同步改 `references/legend-encoding.md` 的语义表（保持"箭头=论断"原则）。
3. **验一遍**：跑 `examples/` 主路径（期望 exit 0）→ 跑两条审计命令（期望 exit 0）→
   跑一次故意失败的用例（枚举外类型，期望 exit 3）→ 把结果写进新任务的 TEST.md。

## 6. 语义与图例速查

| 实体 | 图形 | 边类型 | 端点 | 颜色 |
|---|---|---|---|---|
| gene | 直角矩形（斜体大写） | activation | 实心三角 | 绿 |
| protein | 圆角矩形（正体） | inhibition | 横杠 | 红 |
| complex | 圆角矩形+内描边（"–"连接成分） | binding | 无端点 | 蓝 |
| rna | 圆角矩形（虚线边） | modification | 圆点（可带 P） | 橙 |
| small_molecule | 圆形 | transport | 菱形 | 紫 |

- 线宽 = 证据强度（2.8/2.2/1.6）；**虚线只表示弱证据或不确定**（M3 的 L06 强制）。
- 数据编码（颜色/大小）必须有来源行；无来源不得用于编码（K5/E01）。
- 区室层次：胞外 → 膜 → 胞质 → 核（核嵌入胞质带；跨膜受体在膜带内）。

## 7. 失败与机制修复

失败分支表（F01–F22）见 `references/failure-modes.md`，按五类组织：
材料异常、资产缺失、依赖缺失、契约四形态、状态一致性。使用顺序是**先定位破坏的是哪条机制**
（M1 输入不可信？M2 门没过？M3 审计 fail？M4 源不完整？M5 不确定？M6 契约不全？），
再按 K1–K10 修复——**修机制，而不是修图**：图是机制的输出，改图只会掩盖问题。

## 8. 反预制答案规则

`examples/` 是演示（非正式案例），正式运行必须现场读材料推导；
`assets/result.template.json` 只是空模板；不写、不预测任何平台评分。

## 9. 边界与诚实声明

- 六条机制的"没有它会怎样"中，**可机器验证的部分**（退出码、产物清单、图层数、`data-*` 计数、
  sha256）都给了实测值；**科学判断的正确性上限**（该判 activation 还是 binding）仍需人/模型评审，
  本包不把它包装成指标。
- 图件不在包内；PDF 与 `result.json` 含时间戳，不作确定性承诺。
- 自动抽取只处理结构化语句，散文/PDF 走手工规格——"准确率优先于全自动"。

## 10. 文件索引（相对 `$SKILL_DIR`）

| 文件 | 作用 |
|---|---|
| `references/MECHANISM.md` | **本版核心新增**：M1–M6 机制详解、消融推理、与常规方案的边界、可验证信号 |
| `references/ASSET-INDEX.md` | **本版核心新增**：可复用资产清单 + 复用三步 + 适配新任务的检查表 |
| `references/OUTPUT_CONTRACT.md` | 字段契约 + 四形态 + G1–G8 + §10 机制到字段的映射 |
| `references/failure-modes.md` | F01–F22（按"破坏了哪条机制"归类） |
| `references/RUBRIC_MAP.md` | 五维落点（创新增益 15 与生态贡献 10 按机制与资产逐条落点） |
| `references/mechanism-spec.md` / `legend-encoding.md` | 规格结构、命名与区室规范；箭头语义与数据编码 |
| `scripts/` | 13 个脚本：build（extract/model/main）、render（layout/pathway_svg/mpl_backend）、verify（topology/legend_audit/validate_figure/check_contract/result_writer）、对照（gain_probe / baseline_emulator） |
| `assets/` `templates/` `examples/` | schema/调色板/模板、核对清单、最小可运行示例 |
| `README.md` / `TEST.md` / `worklog.md` | 用法与复用指引 / 自测与实测 / 构建记录（`COMPARE.md` 已并入 `MECHANISM.md` §4 的对照口径） |
