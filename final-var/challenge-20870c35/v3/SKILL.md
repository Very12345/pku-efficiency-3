---
name: academic-talk-organizer
description: >
  把已有科研材料组织成可讲、可编辑、证据可追溯的学术汇报（学术 PPT 页面组织）。
  输入：论文/研究报告/组会材料 + 听众、时长、页数、模板约束、讲稿或备注需求；
  关键词：学术汇报、答辩PPT、组会汇报、slides、deck、页码规划、讲稿、备注、问答准备、
  听众适配、叙事顺序、证据定位、evidence mapping、模板适配、计划契约、机制、可复用资产。
  本包以**机制**运行：M1 计划契约门先行 / M2 逐字证据审计 / M3 叙事配置化 /
  M4 问答预演 / M5 模板适配与自带页丢弃 / M6 契约四形态与状态可见性 /
  M7 运行时文本化资源 / M8 确定性探针；每个机制的"没有它会怎样"与可证伪判据见
  references/MECHANISM.md，可复用资产清单与复用步骤见 references/REUSE-KIT.md。
---

# 学术汇报内容组织 · v3 机制与复用版（academic-talk-organizer）

面向「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35（slides 组）。

本版把包的"独特性"讲清楚：**这条流水线由哪几个不可省略的机制组成、各自失败会怎样、
以及哪些部分别人可以整块拿走**。算法与 CLI 接口与其它版本一致。

**边界**：只做"从已有内容材料到可讲页面"的组织与交付；不做论文精读成稿、学术写作成稿、
科研绘图素材生产。页面内容取自源材料逐字引文，不改写事实、不补造数据。

## 1. 这条流水线的八个机制（一行一条）

| 机制 | 一句话 | 详细 |
|-|-|-|
| **M1 计划契约门先行** | 先出页级计划并用 schema 驱动的 P1–P8 校验，**通过门才生成 deck** | `references/MECHANISM.md` §1 |
| **M2 逐字证据审计** | 交付前逐页核对引文是否真的出现在**实际读取**的源文本中 | §2 |
| **M3 叙事配置化** | 同一份材料按听众与时长换页序（配置驱动，不改代码） | §3 |
| **M4 问答预演** | 局限/风险 + strong 结果各生成追问与回答要点，落到 `qa` 备用页与备注 | §4 |
| **M5 模板适配与自带页丢弃** | 沿用模板母版/版式，但丢弃自带示例页以保证页数 == 冻结页数 | §5 |
| **M6 契约四形态与状态可见性** | 契约字段只增不减、回调 `""/[]/{}/0`（禁 `null`）；降级三处留痕 | §6 |
| **M7 运行时文本化资源** | 包内零二进制；示例 PDF/PNG/模板运行时生成，路径写盘前净化 | §7 |
| **M8 确定性探针** | 同输入双跑的"内容投影 sha"可逐位比对 | §8 |

> 这些机制的作用不是"功能更多"，而是让结果的**每一步都能被别人独立复算**；
> 去掉任何一环的连锁后果列在 `MECHANISM.md` §9。

## 2. 运行契约（命令 / 输出 / 退出码）

```bash
SKILL_DIR="<本包根目录>"        # 平台安装后即 /skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
```

输出（`result.json` 是唯一评分产物，其余是它的证据）：

```
result.json            # 契约字段 + 主结果 + 三道审计内嵌 audit{plan_gates,evidence,deck,gates}
talk_plan.json         # 页级计划（M1 的输入、可编辑中间产物）
plan_gates.json        # 计划契约门 P1–P8
evidence_map.json      # 源文件 → {页, 图表引用} 反向映射（M2）
evidence_audit.json    # 逐页逐字引文审计（M2）
deck_audit.json        # deck 机器校验（打开/页数/备注/命名/OPC/规范化 sha）（M5/M8）
editable_deck.pptx     # 可编辑演示文件（运行期产物）
previews/              # 封面/逐页/网格 PNG + preview_manifest.json（M7）
self_check.json        # validate + contract + 门快照 + 确定性探针（M6/M8）
```

退出码：**0** = 已产出通过 `validate_result` + `check_contract` 的 `result.json`
（`status` 说明 `completed` 还是 `partial`）；**1** = 没有可用的契约结果；**2** = 用法错误。

## 3. 机制 × 阶段 × 产物 × 字段

| 阶段 | 主要机制 | 产物/证据 | 机器可读落点 |
|-|-|-|-|
| P1 输入契约 | M7 | 材料实读结果、环境预检 | `sources[].{kind,parsed,char_count,sections[]}`、`environment` |
| P2 计划 | M1 + M3 | 页级计划 | `talk_plan.json`、`summary.pages_total`、`audience`、`narrative.order_blocks` |
| P3 门 | M1 | 计划契约门 | `plan_gates.json`、`audit.plan_gates`（P1–P8） |
| P4 生成 | M5 | 可编辑 deck | `artifacts.deck_mode`、`deck_audit.slides[].{claim_element,notes_nonempty}` |
| P5 渲染 | M7 | 预览与限制说明 | `artifacts.previews`、`preview_manifest.json`、`environment.cjk_font` |
| P6 审计 | M2 + M4 | 逐字证据、问答 | `evidence_audit.json`、`pages[].qa`、`evidence_map.json` |
| P7 收口 | M6 + M8 | 契约回显、自检、确定性 | `contract.{declared_source,applied}`、`self_check.determinism` |

## 4. "没有它会怎样"（摘要；完整版见 MECHANISM.md，含实测数字与可证伪判据）

| 机制 | 去掉后的退化现象（本包实测证据） |
|-|-|
| M1 | 页数随材料长度漂移：基础形态臂首轮只排 **3 页**（冻结 12 页），需 1 轮返工 |
| M2 | 页面论断无法回溯；对照臂**没有任何定位字段** |
| M3 | 所有场合同一套页序，"听众适配"只停留在提示词里、不落字段 |
| M4 | 讲稿覆盖率 **1.0 → 0.0**、问答条目 **4 → 0** |
| M5 | 模板自带页顶破冻结页数；或干脆丢掉组织方模板约束 |
| M6 | 字段缺失→下游解析崩；`null` 冒充空值；静默降级被当成成功 |
| M7 | 二进制/超限触发平台预检拒收（与算法质量无关） |
| M8 | "可复跑"无法证明：分不清内容变了还是时间戳变了 |

## 5. 复用（谁能拿走哪一层）

完整清单、参数与步骤见 `references/REUSE-KIT.md`；**README 的"复用步骤"节给出三条逐步命令**。

| 你想做什么 | 拿走哪一块 | 入口 |
|-|-|-|
| 只想要"按听众与时长排页序" | 叙事配置 + 计划模式 | `templates/talk_config.json`、`assets/plan.schema.json` |
| 想要题集/金标准做对照或回归 | 题集骨架 + 页级金标准 | `assets/case-set.json`、`assets/page-gold-standard.json` |
| 想给已有产物加"证据可追溯" | 证据审计器 | `scripts/evidence_audit.py` |
| 想做公平对照（量别人/让别人量你） | 对照装置 + 指标口径 | `scripts/gain_ab.py`、`references/GAIN-PROTOCOL.md` |
| 想要提交前/上台前清单 | 三份清单 | `SKILL.md` §7、`references/quality-gates.md`、`templates/slide-checklist-template.md` |
| 想要配色与导出预设 | 色值与参数表 | `references/REUSE-KIT.md` §6/§7、`references/deck-rules.md` |

## 6. 机制失效时的降级（按"哪一环坏了"组织）

| 坏掉的环 | 处置 | 仍然产出 | 记录落点 |
|-|-|-|-|
| M7 依赖缺失（缺 `python-pptx`） | 跳过 deck，**命令仍返回 0** | 计划/门/预览/`result.json`/自检 | `artifacts.editable_deck=null` + `deck_limitation` + `uncertainty` |
| M7 材料缺失/材料为空 | 只出结构性页面或跳过该材料 | 其余材料照常 | `sources[].kind=missing/none` |
| M5 无模板/模板打不开 | 内置 16:9 主题 | deck 照常 | `artifacts.deck_mode.mode`、`template_used` |
| M5 模板自带页 | 丢弃自带页后重建 | 页数 == 冻结页数 | `template_slides_present/dropped` |
| M1 计划门未过 | 记全部 errors，继续产出 | 全部产物 + 降级状态 | `plan_gates.errors` + `uncertainty` |
| M2 引文未逐字命中 | 能修则修，否则如实保留 | 审计条目逐条可查 | `evidence_audit.entries[]` |
| M4 预览失败 | 非致命；可 `--skip-previews` | 其余产物照常 | `artifacts.preview_note` |
| M6 契约字段被声明但未产出 | 按容器类型初始化（禁 `null`） | 契约齐全 | `contract.applied`、`self_check.contract_check` |
| 输入不可读（`case.json`） | 最小失败信封 | `result.json`（`status=failed` + `error`） | 退出码 1 |

统一纪律：**降级必须三处留痕** —— `status` 跟着降、`uncertainty` 有
`{item,impact,mitigation}`、`change_records` 有 `{at,step,action}`；缺一即缺陷。

## 7. 收尾核对清单（逐条可机器验证）

- [ ] `result.json` 存在、`case_id` 一致、`status ∈ {completed,partial,failed}`
- [ ] 契约字段齐全且顶层无 `null`（`self_check.contract_check.missing_required == []`）
- [ ] 计划门 P1–P8 全过，或 `uncertainty` 有对应条目（`plan_gates.gates[P3] pages==target`）
- [ ] 每个内容页有 `locator` + 逐字 `quote`，且 `evidence.source_file` 都在 `sources[]` 中
- [ ] `editable_deck.pptx` 可打开、页数 == 冻结页数、每页有备注（`verify_deck.py` 退出码 0）
- [ ] 预览 PNG 有效且带水印；manifest 说明渲染限制与字体探测结果
- [ ] 双跑确定性：`self_check.determinism` 三个 sha 逐位相同
- [ ] 复用/对照若跑过：`gain_ab.py` 结果与 `GAIN-PROTOCOL.md` §6 数字一致
- [ ] 包内只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`；≤50 文件；单文件 ≤500KB；合计 ≤2MB；
      无符号链接、无 `__pycache__`、无本机绝对路径（字体探测候选路径除外）

## 8. 资源形态与平台约束

题面运行契约原文：*at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks* /
*runtime artifacts may be binary and are retained independently of final JSON validity*。

| 常见二进制 | 本包做法（对应机制） |
|-|-|
| 模板 `.pptx` | 不随包：运行时构建 16:9 母版；案例模板直接读取（M5/M7） |
| 示例图/PDF | 不随包：`scripts/make_synthetic_inputs.py` 运行期生成（M7） |
| 示例输出 `.pptx/.png` | 不随包：`examples/EXPECTED-OUTPUT.md` 文字清单（M7） |
| 字体 | 不随包：运行时探测（`/usr/share/fonts`、`/System/Library/Fonts`、`C:/Windows/Fonts`）（M7） |
| `__pycache__`/`.pyc` | 不随包：提交前删除；`selftest.py --package-check` 的 G10 拦截 |

平台把本包装到 `/skills/weekly-skill`，固定 3 案例 × 3 复跑；输入 `/input/case.json` + `/input/task.md`；
中间产物 `/app/work`，最终产物与 `result.json` 放 `/app/output`；预算 64 请求 / 900 秒 / 16384 token —
**尽早落盘**，预算耗尽时已落盘部分仍可复核。

## 9. 依赖

Python ≥ 3.8（本机 3.13.9）；必需 `python-pptx` + `Pillow`；可选 `pypdf`/`PyPDF2`。
无网络依赖、无 cwd 依赖（所有脚本用 `os.path.dirname(__file__)` 自定位）。
字体探测结果（仅文件名）写入 `environment.cjk_font` 与 `preview_manifest.json`。

## 10. 文件地图

| 文件 | 作用 |
|-|-|
| `scripts/main.py` | 唯一入口（P1–P7 编排） |
| `scripts/scaffold_plan.py` / `validate_plan.py` | 计划（M1/M3/M4） / 计划门 P1–P8（M1） |
| `scripts/deck_builder.py` / `verify_deck.py` | 生成与模板适配（M5） / deck 机器校验（M5/M8） |
| `scripts/evidence.py` / `evidence_audit.py` / `render.py` | 材料与主张（M2） / 逐字审计（M2） / 预览（M7） |
| `scripts/validate_result.py` / `check_contract.py` / `finalize_result.py` / `selftest.py` | 结构 / 契约（M6） / 收口（M6/M8） / 全链路自检 |
| `scripts/make_synthetic_inputs.py` / `common.py` | 运行时资源生成（M7） / 共享工具与路径净化（M7） |
| **`references/MECHANISM.md`** | **本版新增**：M1–M8 的机制/落点/没有它会怎样/可证伪判据 + 连锁效应 |
| **`references/REUSE-KIT.md`** | **本版新增**：可复用资产清单（题集/金标准/清单/导出预设/配色）+ 三个复用场景步骤 |
| **`references/GAIN-PROTOCOL.md`** / **`references/gain-run-record.json`** / **`scripts/gain_ab.py`** | **本版并入**：A/B 对照协议、原始实测记录、对照装置（与 v2 逐字节相同） |
| **`assets/case-set.json`** / **`assets/page-gold-standard.json`** | **本版新增**：题集骨架（三种汇报输入模板） / 页级金标准（结构版 + 机器判定命令） |
| `references/OUTPUT_CONTRACT.md` / `RUBRIC_MAP.md` / `failure-modes.md` / `plan-contract.md` / `quality-gates.md` / `deck-rules.md` / `evidence-audit.md` | 字段契约（含 §7 机制↔字段对照） / 五维映射 / 失败模式 / 计划条款 / G1–G10 / 版式命名 / 审计规范 |
| `templates/` · `examples/` | 叙事规则与上台前清单 / 合成示例与预期输出清单 |
