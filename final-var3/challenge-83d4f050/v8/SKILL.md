---
name: biological-mechanism-pathway-diagram
description: >-
  把科研机制/通路材料转成可逐条核验的生物机制图与通路图，并且**把 result.json 的
  "契约四形态回显"从文档承诺变成逐行实测的矩阵**：随包提供可运行的
  `scripts/contract_matrix.py`，把每种容器形态（字符串/列表/对象/数值/布尔/带 type 的类型化声明/嵌套）
  与每个边界值（空串、空数组、0、false、超长值、非法类型名、缺字段、显式 null、键名与信封或内部键重名、
  契约容器本身非法、case.json 缺失/非 JSON/非对象）逐个注入真实 case 并跑真实主流程，
  三层判定（主流程退出码+status+g2 / 独立 check_contract.py / 产物实际回显），
  给出 `references/CONTRACT-MATRIX.md` 逐行实测表与**静默通过清单**。
  Use when the task asks to draw, generate, edit, re-export or validate a biological
  mechanism map, pathway diagram, signaling cascade, regulatory network or flow
  diagram (figures group of the biology mechanism & pathway challenge), or when a
  reviewer needs evidence about how such a skill behaves at its output-contract edges.
---

# biological-mechanism-pathway-diagram · v8（契约四形态 × 边界值矩阵）

机制图的科学性不看图画得多复杂，而看三件事：**每个实体和每条边能否回溯到材料；图例、颜色映射与
图形本身是否自洽；别人能否打开可编辑源文件改一个标签并重新导出。** 这三件事最终都要落到
`result.json` 这份**唯一评分产物**上——所以本版把"契约"当成需要被**质疑**的对象，
用 40 行真实注入把它逐格测一遍，而不是引用一句"本包支持四形态回显"。

## 1. 这一版解决什么问题

**契约不是文档承诺，是行为。** 本版把 `references/OUTPUT_CONTRACT.md` §3（四形态回显）与 §7（G1–G8）
放到真实主流程上逐行验证，并明确区分四种结果：

| 分类 | 含义（与 `contract_matrix_report.json → classification_rules` 逐字一致） |
|-|-|
| `ok` | 声明键全出现 + 回显类型与声明形态一致 |
| `fill_documented` | 只是文档允许的空值填充（如空对象契约），无形态违规 |
| **`silent_gap`** | 存在**形态违规**（键丢失/类型不符/契约容器非映射/无 `result.json`）而**三层全 pass** |
| `flagged` | 同样的形态违规**被某一层抓到**（`g2` fail / `check_contract.py` 非零 / status 降级） |

**本机实测（40 行）**：`ok` **27** · `fill_documented` **1** · **`silent_gap` 8** · `flagged` **4** ·
另有 **15** 行属"文档允许但无留痕"。控制行（不注入）为 `exit=0 / success / g2=true / check_contract exit=0`，
因此每一行的差异都能归因到注入本身。

**最有价值的两条结论**：

1. **静默通过的 8 行集中在两类**：① 契约容器**本身不是映射**（`output_contract` = 数组/字符串/数值/布尔/null）
   → 整个契约被忽略，而 `main.py` 的 `g2` 门与 `check_contract.py` 的 `C05` **都报通过**；
   ② **没有任何一层校验"声明类型是否被满足"**（`{"case_id":12345}` 声明 number、实际回显 str，全绿；
   `{"type":"tuple"}` 非法类型名被静默替换为 `""`）。四形态本身的 27 行**全部 ok**。
2. **主流程自带门会漏，独立检查器能补**：`{"_echo_missing": "declared"}`（键与流水线内部临时键同名）
   时 `g2=true`，但该字段随后被 `del` 掉，最终 `result.json` 里**没有**它——只有独立
   `scripts/check_contract.py`（`C05`）抓到。⇒ 交付流程里**不能省**这一步。

完整逐行表、静默清单、被抓住的 4 行、未覆盖声明见 `references/CONTRACT-MATRIX.md`（本版轴文档）。

## 2. 用途与适用条件

- **适用**：机制图/通路图/信号级联/调控网络/流程图的生成、编辑、重导出与校验。
- **额外适用（本版新增）**：① 你要**给某个案例写 `output_contract`**——先看矩阵，知道哪些声明形态会被
  静默吞掉；② 你要**验收一份 result.json**——按本版的三层判定跑一遍，别只看键在不在。
- **不适用**：数值统计与统计结论、实验方案设计、论文写作与版式美化（相邻课题负责）。
- **运行前提**：Python 3（标准库即可；`matplotlib` 只影响 PNG/PDF 预览，缺失时按 `partial` 降级）。

## 3. 资源形态（纯文本硬约束）

`at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks`；允许扩展名仅
`.md .py .json .txt .csv .yaml .yml`；包内无二进制；图件一律运行时生成；
`contract_matrix_report.json` 是本机实跑的一次矩阵报告（不是预置答案、不是正式案例结果）。

## 4. 命令行总览（自定位，cwd 不是技能根也能跑）

```bash
export SKILL_DIR=/skills/weekly-skill
python3 "$SKILL_DIR/scripts/main.py" --help            # 自检：路径正确
```

| 入口 | 参数 | 说明 |
|-|-|-|
| `scripts/main.py` | `--case --task --out --materials-dir --model-file --formats --dpi --verbose` | 单一主入口；`--formats` 默认 `svg,png,pdf`；`--dpi` 默认 150 |
| `scripts/check_contract.py` | `--result --case` | 独立契约复查（C01–C07：信封 / 禁止 null / 契约回显 / G1–G8 / 产物路径） |
| `scripts/validate_figure.py` | `--out --case` | 对输出目录做独立复检（`model.json` 权威） |
| `scripts/contract_matrix.py` | `--skill --case --model-file --work --report --formats --dpi --python --only --json` | **本版新增**：契约矩阵测量器 |

```bash
# 标准一次运行
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /app/output --formats svg,png,pdf

# 本版新增：契约矩阵（40 行；应退出 0）
python3 "$SKILL_DIR/scripts/contract_matrix.py" \
    --work /tmp/cm --report "$SKILL_DIR/contract_matrix_report.json"
python3 "$SKILL_DIR/scripts/contract_matrix.py" --only struct-oc-list   # 单行复现某条结论
```

**退出码**：`main.py` `0=success / 2=partial / 3=failed`；`check_contract.py` `0=通过 / 1=失败`；
`validate_figure.py` `0=全过 / 1=有 fail`；`contract_matrix.py` `0=矩阵跑完 / 2=控制行不通 / 4=参数错误`。
⚠ **实测补充**：`main.py` 在"输入层"问题上会返回 **1**（`--case` 不存在、`case.json` 非 JSON、`case.json` 是数组），
而它的 docstring 只声明了 `0/2/3`（见 `references/CONTRACT-MATRIX.md §7`）⇒ **判别输入缺失不能只看退出码**，
必须同时看有没有 `result.json` 与 stderr。

## 5. 三层判定：怎么验一份 result.json

| 层 | 命令 / 位置 | �    看什么 |
|-|-|-|
| L1 主流程 | `main.py` 退出码、`result.json.status`、`result.json.gates.g2_contract_echo.pass` | 流水线自己认为成功了吗 |
| L2 独立检查器 | `python3 "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>` | 退出码与失败项 id（C01–C07） |
| L3 产物本身 | `result.json` 实际键与值 | 声明字段在不在、类型对不对、顶层有没有 null、有没有留痕 |

**分类规则**（照抄即协议）：只有"空对象契约"算 `fill_documented`；其余形态违规若三层全 pass ⇒ `silent_gap`；
若被任一层抓到 ⇒ `flagged`。附加列 `documented_but_untraced` 记录"声明值被按文档替换为空值但没留痕"。

## 6. 实测摘要：四形态与硬门

- **四形态回显（27 行全 `ok`）**：`①标量 str`、`②容器 list`、`③布尔`、`④数值/字典`、以及带 `type` 的
  类型化声明（`{"type":"str"|"list"|"dict"|"bool"|"number"}`）。实测回显值为**该形态的空值**
  （`""` / `[]` / `{}` / `0` / `false`），**不是** `case.json` 里写的字面量——这是 §3 的文档行为：
  **把 `output_contract` 里的字面量当类型声明用，不要期望它成为值**（否则会踩 `documented_but_untraced` 的 15 行）。
- **边界值**：空串 / 空数组 / `0` / `false` / 4096 字符超长值 / 200 字符键名 / 含 `.` 与 `[0]` 的键名 /
  60 个字段 / 200 项数组 —— 全部按声明形态回显，`g2` 与 `C05` 全过。
- **顶层 null**：`null_at_top_level_rows = []`（40 行里没有任何一行产出顶层 null）。
- **`edge-collide-envelope`**（声明 `{"status":"CASE_WANTS_THIS"}`）：回显 `success`（真实值优先，文档行为）。
- **`edge-nested`**（`{"a":{"b":1}}`）：回显 `{}`——嵌套结构被**压平**，无留痕（半静默，见轴文档 §6）。
- **`struct-oc-missing`**（`case.json` 没有 `output_contract` 键）：无回显要求，`ok`。

## 7. 主流程 CP1–CP5

- **CP1 先读真实文件**：读 `case.json` / `task.md` / 材料目录里每个文件，事实逐条记出处（文件+行号）；
  材料缺失 ⇒ `failed`（退出码 3）。
- **CP2 机制规格 + schema 门**：`extract.py` 出草稿；草稿/手工规格对**原始未归一化**规格过
  `assets/mechanism-spec.schema.json`（未知类型不静默改写，直接 `failed`）。散文/PDF 材料走
  **CP2b**：Agent 读材料后手写 `model.json` 并用 `--model-file` 重跑。
- **CP3 人工核验**：逐条对照材料原文；`extraction.verified_by_agent=true` + `change_records` 记录改动；
  未核验的自动草稿只能 `partial`。
- **CP4 布局渲染与双审计**：`layout.py` / `pathway_svg.py`（7 层可编辑 SVG）/ `mpl_backend.py`（PNG、PDF）/
  `topology.py`（P01–P08）/ `legend_audit.py`（L01–L08、E01–E02）/ `validate_figure.py` 聚合检查。
- **CP5 写 `result.json` 并自查**：字段、四形态回显与 G1–G8 以 `references/OUTPUT_CONTRACT.md` 为**唯一权威**；
  **交付前必须再跑一次 `check_contract.py`**（本版实测证明 `g2` 会漏 `_echo_missing` 这类内部键同名场景）。

## 8. 决策规则（契约相关，遇情况先查表）

| # | 情形 | 决策 |
|-|-|-|
| D1 | 收到的 `case.json` 里 `output_contract` 不是对象 | 视为**契约未声明**（实测被整体忽略且各检查全绿）；在 `uncertainty` 里如实写明「契约容器非法、已按无契约处理」，**不要假装回显成功** |
| D2 | 契约字段与流水线内部/信封字段同名 | 先跑 `check_contract.py`；`g2` 通过**不代表**字段最终在（`_echo_missing` 实测丢失）。必要时改名 |
| D3 | 声明了 `type` 但名字不在已知 5 类内 | 不会报错，会被静默填成 `""`；改为已知类型名或改为字面量声明 |
| D4 | 需要"声明即默认值" | 不要依赖回显（回显的是空值）；让 Skill 自己在 `result.json` 里写真实值 |
| D5 | 声明了 `null` / 嵌套对象 | 顶层 null 被替换为空串（文档允许）、嵌套被压平为 `{}`；在 `uncertainty` 里说明 |
| D6 | `--case` 不存在 / 非 JSON / 非对象 | 实测退出码 **1**、无 `result.json`；按"输入层错误"处理（不是 `partial`） |
| D7 | 材料未写上下游方向 | 不臆造：结合类无向边 + `uncertain=true` |
| D8 | 同名基因/蛋白、同一蛋白多区室 | 拆实体（基因斜体/蛋白正体；按区室拆），note 写依据 |
| D9 | 数据值缺来源 | 阻断：补 `source` 或降为 `assumption` 并进 `uncertainty`（E01/T03） |
| D10 | 机制规格不过 schema 门 | 阻断渲染（`failed`），修正后重跑 |
| D11 | `matplotlib` / 字体缺失 | 保留可编辑 SVG；PNG/PDF 缺失如实记录；`status=partial` |
| D12 | 材料里没有实体/关系 | 明确 `failed`，不画空图凑数 |

## 9. 异常处理与留痕

完整清单见 `references/failure-modes.md`（本版新增 **FM-C1–FM-C7**：契约容器非法、内部键同名、
非法类型名、类型冲突、null/嵌套压平、输入层退出码 1、只验键不验类型）。
三条通则：**① 任何降级都要有留痕位置；② 任何 `fail` 都要落到 `status`；③ 不确定就写不确定。**

## 10. 反预制答案

`examples/` 里的一切都是**演示**（图内与 `result.json` 带示例标记）。正式运行**禁止**抄示例的实体/边/数值；
`contract_matrix_report.json` 描述的是**注入实验**（构造的边界契约），不是正式案例结果，也不是分数。
不给自己编造 benchmark 分数；矩阵里出现的 `case_id`（`example-egfr-mapk`）来自示例案例。

## 11. 限制与维护

- 矩阵只覆盖"契约轴"：**CLI 参数边界、并发写同一目录、磁盘满、只读目录**不在本版范围内（见轴文档 §8 未覆盖声明）。
- 三层检查都只校验"键是否存在"，**不校验声明类型**——这是本版实测出的边界，若上游要求类型级校验，
  需要扩展 `check_contract.py`（本版不改既有脚本，只在文档中记录该边界）。
- 契约与门集中 `references/OUTPUT_CONTRACT.md`（字段块逐字保留，本版不改契约）；
  改动后同步更新 `TEST.md` 实测记录并在 `worklog.md` 追加带时间的记录。

## 12. 文件索引

- `references/CONTRACT-MATRIX.md`——**本版轴文档**：40 行逐行实测、静默通过清单、被抓住的 4 行、未覆盖声明。
- `contract_matrix_report.json`——本机实跑的机器可读矩阵报告（`rows[] / summary / classification_rules / not_covered`）。
- `references/OUTPUT_CONTRACT.md`——`result.json` 字段契约 + G1–G8（唯一权威，本版逐字保留）。
- `references/RUBRIC_MAP.md`——五维评分 → 本包文件与机制；`references/failure-modes.md`——失败模式（含 FM-C 系列）。
- `references/mechanism-spec.md` / `references/legend-encoding.md`——机制规格、命名、区室、箭头语义与数据编码。
- `scripts/`：`main.py`（主入口）、`check_contract.py`、`validate_figure.py`、**`contract_matrix.py`（本版新增）**、
  `extract.py`、`layout.py`、`pathway_svg.py`、`mpl_backend.py`、`topology.py`、`legend_audit.py`、
  `result_writer.py`、`model.py`。
- `assets/`（schema / 调色板 / result 模板）、`templates/relation-checklist-template.md`（CP3 核验载体）、
  `examples/`（最小可运行示例）、`README.md` / `TEST.md` / `COMPARE.md` / `worklog.md`。
