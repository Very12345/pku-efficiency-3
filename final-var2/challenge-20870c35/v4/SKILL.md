---
name: academic-talk-organizer
description: >
  组织学术汇报内容（学术 PPT 页面组织）：从论文/研究材料到可讲、可编辑、证据可追溯的演示文件。
  当输入包含科研论文材料、研究报告、组会/答辩/评审任务、听众与时长、页数与模板约束、讲稿或备注需求，
  关键词如 学术汇报、答辩PPT、组会汇报、slides、deck、页码规划、讲稿、备注、问答准备、听众适配、
  叙事顺序、汇报内容组织、evidence mapping、模板适配、plan contract、quality gates、
  失败注入、fault injection、降级实测、静默失败、退出码语义、模板损坏、无文本层 PDF、
  依赖遮罩、契约四形态、可证伪时使用本 Skill：
  读真实材料 → 抽取研究问题/方法/结果/局限 → 页级计划并经计划契约门 P1–P8 校验 →
  python-pptx 生成可编辑 .pptx（模板适配或内置主题）→ verify_deck 校验 → PIL 渲染预览 →
  evidence_audit 逐字审计 → finalize_result 写 result.json。严格以真实文件为准，不臆造数据。
  本版（v4）的落点是**失败注入与恢复演练**：把输入/模板/依赖/契约四族的 15 种故障逐个故意弄坏
  并真跑主流程，逐行记录实测退出码 / status / uncertainty / 是否静默失败，见
  scripts/fault_inject.py 与 references/FAULT-MATRIX.md。
---

# 学术汇报内容组织 · v4 失败注入与恢复演练版

面向「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35（slides 组）。
把**已有**的论文/研究材料组织成：结构清楚、证据可追溯、可编辑、符合听众与模板约束的学术汇报产物。
本 Skill 不负责论文精读成文、写作成稿与科研绘图本身（相邻课题负责），只负责
**从已有内容材料到可讲页面的组织与交付**。

> **题面两条硬约束（Runtime contract 原文）**：
> ① `Skill resources: at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks.`
> ② `Runtime artifacts may be binary and are retained independently of final JSON validity.`
> ⇒ 提交资源**只有文本**（`.md/.py/.json/.txt/.csv/.yaml/.yml`），`.pptx/.png/.pdf` 等**一律由脚本运行时生成**；
> 包内不含任何本机绝对路径、无 `__pycache__`、无符号链接。逐类处置见 §9。

## 0. 本版的主张：正常路径跑通 ≠ 坏路径不静默

大多数 Skill 包只证明"给好输入能跑出结果"。那**不能**推出"给坏输入不会悄悄产出错东西"。
本版把这两件事**分开证明**，并且把后者做成可复算的机器判定：

1. **先立基线**：用 `make_synthetic_inputs.py` 补齐示例的二进制输入，
   让**无注入**的运行成为一条完整成功路径（`status=completed`）。
2. **再逐条弄坏**：输入形态 / 模板形态 / 依赖形态 / 契约形态**四族共 15 条**注入，
   每条在**包外一次性沙箱**里真跑一遍主流程。
3. **判"是否静默"**用四要素齐全性，不用感觉：实测**退出码** + `result.json.status`
   + ≥1 条 `uncertainty` + ≥1 条 `change_records`；缺任一即记 `silent_failure=true`。
4. **期望与实测不符时只允许两条出路**：改代码（纯增量、逐条点名），或**改期望并写明为什么原期望是错的**。
   本版实际发生 4 次（`F06`/`F07`/`F08`/`F14`），理由逐条写在实测表里。

**这套演练当场暴露并已修掉 4 类真实缺陷**（详见 §5）：

| 缺陷 | 修前实测 | 修后实测 |
|-|-|-|
| 模板在盘上但**容器损坏** → 打死整轮 | `F07`：`exit=1` / `failed` / deck 未生成 / traceback | `exit=0` / `completed` / deck 有 / 降级两处留痕 |
| **无文本层 PDF** 被记成成功解析 | `F05`：`parsed=true` / `char_count=15` / `completed` | `parsed=false` + OCR 提示 / `partial` |
| 契约块不可用时被**静默吞掉** | `F12`·`F13`：无 `contract` 步、无对应 `uncertainty`、`completed` | `contract` 步 + `uncertainty` / `partial` |
| 契约字段落 **`null`**，与契约 §1 矛盾 | `F14`：字段 `null` / `contract_check` 失败 / `exit=1` | 字段 `""` / `contract_check` 通过 / `exit=0` |

## 1. 用途与适用条件

- **适用**：平台固定 3 个案例（组会 / 答辩 / 评审类型的学术汇报内容组织），要求：
  提取研究问题-方法-结果-局限主线 → 页级主张+图表引用+讲解顺序 → 按模板生成可编辑演示文件
  与讲稿/备注 → 每页保留源材料定位并检查导出渲染。
- **不适用/边界**：不承接论文精读成稿、学术写作、科研绘图素材生产；不代替用户下科学结论；
  页面内容一律取自源材料逐字引文（`quote`），不改写事实、不补造数据。
- **运行环境**：Python 3.8+，必需第三方库仅 `python-pptx` 与 `Pillow`；
  `pypdf`（或 PyPDF2）为 PDF 可选解析器，缺失时按「未解析」如实降级，不影响其余链路。
  全包无网络依赖、无 cwd 依赖（脚本全部用 `os.path.dirname(__file__)` 自定位）。
  **缺任何依赖都不崩**：`python-pptx` 缺失 → 跳过 deck 并降级为 `partial`（其余产物照常）；
  `Pillow` 缺失 → 跳过预览（非致命）；`pypdf` 缺失 → PDF 记未解析。见 §4 的 D15。
- **本机实测环境**：Python 3.13.9 / python-pptx 1.0.2 / Pillow 12.3.0 / pypdf 6.14.2（记录见 `TEST.md`）。

## 2. 四族注入总表（本版的核心交付物之一）

**完整实测表**（逐条 uncertainty 原文、耗时、产物落盘、期望修订说明）见
[`references/FAULT-MATRIX.md`](references/FAULT-MATRIX.md)。这里给族与判据：

| 族 | 注入几条 | 覆盖的形态 | 设计上的降级路径 |
|-|-|-|-|
| `I*` 输入形态 | 5 | `case.json` 非法 JSON / 缺 `case_id` / 声明材料不存在 / 零材料 / **无文本层 PDF** | D1/D2/D3/D7/D17 |
| `T*` 模板形态 | 3 | 模板路径失效 / **模板容器损坏** / 合法模板自带示例页 | D5/**D18**/D16 |
| `D*` 依赖形态 | 3 | `import pptx` / `import PIL` / `import pypdf` 被遮罩 | D15/D12/D2 |
| `C*` 契约形态 | 3 | 契约块非法 JSON / 空契约 `{}` / 多声明一个产不出的字段 | **D19**/**D20** |
| 对照组 | 1 | **不做任何注入** | 基线应为 `completed`（否则归因不成立） |

**依赖缺失怎么注入**：在沙箱里放一个同名的**导入遮罩**模块（抛 `ImportError`），
用 `PYTHONPATH` 前置。脚本目录（`sys.path[0]`）先于 `PYTHONPATH`，`PYTHONPATH` 先于 `site-packages`，
因此**无需卸载真包**即可让主流程观察到"依赖缺失"。遮罩抛的是 `ImportError`（比真实的
`ModuleNotFoundError` 更宽），这本身也是对降级分支健壮性的额外检验。

**实测到的连带效应（非设计预设，如实记录）**：遮罩 `PIL` 会**同时**让 python-pptx 不可用
—— 因为 python-pptx 自身依赖 PIL —— 所以 `F10` 会同时丢 deck 与预览，两者各有独立 `uncertainty` 条目，
退出码仍为 `0`。

## 3. 输入与输出

### 3.1 输入（平台运行期）

| 路径 | 内容 |
|-|-|
| `/input/case.json` | `case_id`、`title`、`report_goal`、`audience`、`duration_min`、`slide_count`、`report_type`、`materials`（可为 `{path,role}`）、`template`/`start_deck`（可选）、`figure_files`（可选映射）、`output_contract`（可选字段声明） |
| `/input/task.md` | 任务说明；可能含 output_contract 声明（fenced JSON 或字段表） |
| 材料目录 | `case.json` 中列出的文本/PDF（缺省取 `<case 目录>/materials`）：`.md/.txt/.pdf` 与图片附件 |

**必须实际读取文件内容**，不得根据标签/文件名预设内容。`main.py` 自动发现材料目录中的 md/txt/pdf/图片。

### 3.2 输出（`--out`，平台运行期即 `/app/output`）

```
result.json            # 唯一评分产物：契约字段 + 主结果 + 证据定位 + status/sources/
                       #   uncertainty/change_records/environment + audit{plan_gates,evidence,deck,gates}
talk_plan.json         # 页级计划（可编辑中间产物）
plan_gates.json        # 计划契约门 P1–P8 结果（assets/plan.schema.json 驱动）
evidence_map.json      # 源文件 → {用到它的页, 图表引用} 反向映射
evidence_audit.json    # 逐页逐字引文审计
deck_audit.json        # deck 机器校验（打开/页数/备注/claim 元素/OPC/规范化 sha）
editable_deck.pptx     # 可编辑演示文件 ← 运行期产物（二进制），不进提交资源
previews/              # cover_preview.png · slide_0NN.png · preview_grid.png · preview_manifest.json
self_check.json        # validate_result + check_contract + 门 + 确定性探针
```

`result.json` 里的路径一律是**可移植形式**：本机绝对路径写盘前改写成相对案例目录的路径，
POSIX 运行期路径（`/input/...`、`/app/output/...`）原样保留。字段契约全文见
[`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md)（该文件的字段块在本版中**逐字未改**）。

## 4. 执行（CP1–CP6）与异常处理

> **自定位**：`$SKILL_DIR` = 本包根目录（含 `SKILL.md`；平台安装后即 `/skills/weekly-skill`）。
> 所有脚本用 `os.path.dirname(__file__)` 自定位，**命令与当前 cwd 无关**。

### 4.1 检查点

| 检查点 | 做什么 | 出口条件 |
|-|-|-|
| **CP1 输入契约** | 读 `case.json`/`task.md`；解析材料（显式清单 + 自动发现）；解析模板（显式参数 > case 字段 > 材料目录扫描）；环境预检（`python-pptx`/`Pillow`/`pypdf`/中文字体） | 缺失项已按 D 规则记录；`environment` 与 `change_records` 已写入 |
| **CP2 计划门** | 一条命令跑主流程（见下）；产出 `talk_plan.json` 并跑 P1–P8 写 `plan_gates.json` | 未全过 → D9 降级但**不中断** |
| **CP3 生成与校验门** | 模板适配（沿用母版/版式、丢弃自带页）或内置主题；确定性元素命名；图绑定或诚实占位；`verify_deck` 写 `deck_audit.json` | deck 页数 == 计划页数 |
| **CP4 渲染门** | PIL 模拟渲染封面/逐页/网格 + `preview_manifest.json`（含字体探测） | 失败非致命（D12） |
| **CP5 审计与收口门** | `evidence_audit` 逐页逐字核验；`finalize_result` 组装 result.json（契约四形态回显、禁 null）+ `self_check.json` | `contract_check.valid == true` |
| **CP6 失败注入演练** | 在**包外**沙箱注入四族 14 条注入 + 1 条对照并真跑（见 §2） | 脚本退出码 `0` 且 **0 静默失败** |

```bash
# CP2：主流程（一条命令完成 抽取→规划→.pptx→校验→预览→审计→result.json→自检）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output

# CP6：失败注入演练（必须在包外目录；脚本会主动拒绝 --sandbox 落在技能包内部）
python "$SKILL_DIR/scripts/fault_inject.py" --sandbox "<包外空目录>"           # 15 行全跑
python "$SKILL_DIR/scripts/fault_inject.py" --sandbox "<包外空目录>" --inject F07,F12
python "$SKILL_DIR/scripts/fault_inject.py" --list                          # 只看注入清单
```

**退出码（`main.py`）**：`0` = 已产出通过 validate+contract 的 `result.json`
（其 `status` 说明 `completed` 还是 `partial` —— 诚实降级不会被报成崩溃）；
`1` = 没有可用的契约结果；`2` = 参数用法错误。
**退出码（`fault_inject.py`）**：`0` = 全 MATCH 且无静默失败；`1` = 有 MISMATCH；
`2` = 用法错误 / **沙箱落在技能包内部**（在包内跑会生成 `__pycache__` 使提交包不合规）。

### 4.2 决策规则（D1–D20；全表含优先级裁决见 `references/failure-modes.md`）

| 规则 | 情形 | 处置（全部如实记录到 `uncertainty` / `change_records`） |
|-|-|-|
| D1 | 材料缺失 | `sources` 中 `kind=missing`；status 视影响降 `partial`；不编造内容 |
| D2 | 材料是 PDF 且无 pypdf / 解析失败 | 记 `parsed=false` + 原因；其余材料照常 |
| D3 | PDF 丢公式/符号；**或抽取到 0 个非空文本行** | 前者 quote 以抽取文本为准并注明代理方式；后者**记未解析**（本版修正） |
| D4 | 论文缺图/图分辨率低/图损坏 | 页内**诚实占位框**；坏图跳过 |
| D5 | 无模板 / 模板路径失效 | 内置主题；`artifacts.template_used`/`deck_mode` 注明 + `uncertainty` 记明 |
| D6 | 页数与时长推导冲突 | 以任务冻结页数为准（P3），`plan_gates` 记录说明 |
| D7 | 听众信息缺失 | `familiar` + 中等证据深度保守处理，`audience.notes` 注明可覆写 |
| D8 | 材料中某块无直接主张 | 用该块章节概括成页（`derived=true`、`weak`），framing 记 `change_records` |
| D9 | 计划门 P1–P8 未全过 | 记 errors；仍生成 honest 产物；`status→partial`；uncertainty 列出 |
| D10 | 导出/生成抛错、超时 | 非致命：仍写 `result.json`；中间产物尽早落盘；异常写 `change_records` |
| D11 | `verify_deck` 发现问题 | 记 entries；`status→partial`；不宣称"校验通过" |
| D12 | 预览失败/超时 | 非致命：仍写 `result.json`；`--skip-previews` 可跳过 |
| D13 | 证据审计引文未逐字命中 | 记录条目（derived 页按概括语）；可修则修，不能修如实保留 |
| D14 | 页面数字与源不一致 | `validate_result` 给警告；人工核对；合理换算需说明 |
| D15 | 缺 `python-pptx`（或连带 Pillow） | **不崩**：跳过 deck，`status→partial`，`editable_deck=null` + `deck_limitation`；其余照常，命令仍返回 **0** |
| D16 | 模板自带示例页 | 保留母版/版式，**丢弃自带页**后按冻结计划重建；最终页数 == 冻结页数 |
| D17 | 材料为空 / 全部不可解析 | 只产出结构性页面；`status→partial` + uncertainty 明写；不据标签补造内容 |
| **D18** | **模板存在但不是合法 OOXML** | `try` 打开失败 → 记 `template_load_error` → **回落内置主题**；异常进 `change_records`(step=`deck-source`) 与 `uncertainty`；**不得**把整轮记成 `failed` |
| **D19** | **`task.md` 声明了 output_contract 却用不起来** | 解析器带回**具体原因**；写 `change_records`(step=`contract`) + `uncertainty`，`status→partial` |
| **D20** | **契约声明了本包产不出的字段** | 按声明容器类型回落 `""`/`[]`/`{}`/`0`，**禁止 `null`**；`contract.applied` 记录全部已回显字段 |

### 4.3 三处留痕：降级必须"看得见"

`status` 只是结论；要能独立复核，原因必须在**三处**同时对得上（§2 的"非静默"判定就用这张表）：

| 落点 | 字段 | 复核方式 |
|-|-|-|
| ① 状态 | `status`（`completed`/`partial`/`failed`） | 读 `result.json.status`；`failed` 时再看 `error` |
| ② 声明 | `uncertainty[]`（每条 `{item, impact, mitigation}`） | **≥1 条**才算这条降级被声明过 |
| ③ 过程 | `change_records[]`（每条 `{at, step, action}`） | 按 `step` 过滤：`material`/`deck`/`deck-source`/`preview`/`plan-gate`/`contract`/`audit` |

细粒度补充落点（不替代上表，只是更细的机读位置）：`artifacts.editable_deck=null` + `deck_limitation`（缺 pptx）·
`artifacts.deck_mode.template_load_error`（模板打不开）· `sources[].parsed/kind/note`（材料）·
`audit.plan_gates.valid`（计划门）· `contract.declared_source` / `contract.applied[]`（契约）。

> **注意 `F01` 这条边界**：`case.json` 完全不可读时走 CP1 的 fatal 分支，
> 此时 `uncertainty` 为**空**（它由 CP5 组装）——"失败原因"由 `result.error` +
> `change_records` 承担。读 `uncertainty` 拿不到原因的人会误判，故在此点名。

## 5. 由演练暴露、并已修复的真实缺陷（逐条点名）

> 口径：**只做纯增量**。不改任何 CLI 参数名 / 默认值 / 退出码语义；不改任何既有键名与容器类型；
> 不删任何既有逻辑分支。`+/-` 为 `diff -u` 统计的改动行数（含新增注释行）。

| # | 文件 | +/- 行 | 触发 | 修的是什么 | 修后行为 |
|-|-|-|-|-|-|
| Fix 1 | `scripts/deck_builder.py` | +24 / -1 | `F07` | `build_deck` 直接 `Presentation(template_path)`；容器损坏时异常穿透到编排器 | 先 `try` 打开；失败记 `template_load_error` 并回落 `_new_deck()`；新增键 `template_expected`/`template_load_error`（`None`，不删旧键） |
| Fix 2 | `scripts/evidence.py` | +12 / -0 | `F05` | 无文本层 PDF 被记 `parsed=true`（`char_count=15`，只含页分隔行） | 无任何非空贯通文本行时记 `parsed=false` + OCR 提示并 `return`；不影响有文本层的 PDF |
| Fix 3 | `scripts/common.py` | +27 / -2（与 Fix 4 合计） | `F12`·`F13` | 契约块"存在但不可用"只 `continue`，调用方拿不到原因 | 新增 `failed` 原因列表（非法 JSON / 空契约 / 表格字段 <5 / 无契约键）落到返回 `note`；`specs` 语义不变 |
| Fix 4 | `scripts/common.py` | +5 / -0（含在上面 27 行内） | `F14` | `CONTRACT_TYPE_DEFAULTS["any"]=None` 使类型未声明的字段落 **`null`**，违反契约 §1「禁止 null」 | `apply_contract` 里 `default is None → ""`；仍保留 `"null"` 映射用于**显式**声明 `"type":"null"` 的场景 |
| Fix 5 | `scripts/main.py` | +29 / -0（与 Fix 6 合计） | `F12`·`F13` | 契约解析失败的 `note` 被丢弃，既不进 `change_records` 也不进 `uncertainty` | 捕获 `note`；契约块存在却不可用时写 `change_records`(step=`contract`) + `uncertainty`，并按"无法判断"把 `status` 降为 `partial` |
| Fix 6 | `scripts/main.py` | +12 / -0（含在上面 29 行内） | `F07` | 模板回落后降级原因只在 `artifacts.deck_mode`，只读 `uncertainty` 的复核者看不到 | `deck_mode.template_load_error` 非空时追加 `uncertainty`（异常类型 + 原因 + 修复建议）；`status` 不改 |

**逐字节未变的脚本**：`check_contract.py`、`evidence_audit.py`、`finalize_result.py`、
`make_synthetic_inputs.py`、`render.py`、`scaffold_plan.py`、`selftest.py`、`validate_plan.py`、
`validate_result.py`、`verify_deck.py`。

## 6. 脚本与资源清单

| 文件 | 角色 | 作用 |
|-|-|-|
| `scripts/main.py` | build 编排 | 唯一入口：CP1–CP5 门控（环境预检→材料解析→计划→校验→deck→预览→审计→result→自检） |
| `scripts/fault_inject.py` | verify | **失败注入演练**（本版新增）：四族 14 条注入 + 1 条对照在包外沙箱逐个真跑，判「退出码 + status + uncertainty + change_records」四要素齐全性以识别静默失败；写 `fault_matrix.json` + 生成版矩阵。CLI：`--skill --sandbox --case --inject --list --skip-previews --no-prime --json-out --md-out --quiet` |
| `scripts/evidence.py` | extract | 材料加载（md/txt/PDF-pypdf）与主张/证据锚点抽取 |
| `scripts/scaffold_plan.py` | build | 页级规划：听众→背景比例、叙事顺序、一页一主张、问答预演、图绑定 |
| `scripts/validate_plan.py` | verify | 计划契约门 P1–P8（schema 驱动）；独立 CLI |
| `scripts/evidence_audit.py` | verify | 逐页逐字引文审计 + 定位/数字/图绑定；独立 CLI |
| `scripts/deck_builder.py` | render | python-pptx 生成/模板适配可编辑 `.pptx`（母版复用、自带页丢弃、确定性命名、讲稿备注、图占位） |
| `scripts/verify_deck.py` | verify | deck 打开/页数/备注/命名/OPC/规范化 sha 校验；独立 CLI |
| `scripts/render.py` | render | PIL 模拟预览（封面/逐页/网格 + manifest + 字体探测） |
| `scripts/validate_result.py` | verify | result.json 结构+文件+数字可对源校验；独立 CLI |
| `scripts/check_contract.py` | verify | output_contract 字段齐全性校验；独立 CLI |
| `scripts/finalize_result.py` | verify/build | result 信封组装：契约回显 + 审计嵌入 + environment + self_check + 确定性探针 |
| `scripts/selftest.py` | verify | 全链路复核（G1–G10）+ 包约束审计；独立 CLI |
| `scripts/common.py` | shared | 自定位、JSON IO、契约工具、确定性投影 hash、绝对路径净化、输入解析 |
| `scripts/make_synthetic_inputs.py` | assets | **运行时生成示例二进制输入**：`dataset_card.pdf`、`fig2.png`、`--template` 时的 `synthetic_template.pptx` |
| `references/FAULT-MATRIX.md` | docs | **失败注入矩阵**（本版新增）：15 行（14 条注入 + 1 条对照组）的实测退出码/status/uncertainty/静默失败判定 + 6 条修复点名 + 7 条覆盖边界 |
| `references/OUTPUT_CONTRACT.md` | docs | result.json 契约（字段块逐字保留；本版追加"降级在三处留痕"与"契约在故障注入下的实测行为"两节） |
| `references/RUBRIC_MAP.md` | docs | 五维评分（40/25/15/10/10）→ 本包文件与机制逐条对照 |
| `references/failure-modes.md` | docs | 失败模式处置表（F1–F26 + 决策规则 D1–D20 + 状态一致性 + 注入演练实测对照） |
| `references/plan-contract.md` · `references/quality-gates.md` · `references/deck-rules.md` · `references/evidence-audit.md` | docs | 计划契约 / 质量门 / 页面规则 / 证据审计规范 |
| `templates/talk_config.json` · `templates/narrative_template.md` · `templates/slide-checklist-template.md` | assets | 叙事规则（可编辑）+ 人类可读模板 + 上台前核对清单 |
| `assets/plan.schema.json` · `assets/result.template.json` | assets | 计划契约模式（P1–P8 驱动源）+ result 信封示例 |
| `COMPARE.md` · `examples/README.md` · `examples/EXPECTED-OUTPUT.md` · `examples/output/*.example.json` | docs/demo | 对照方案 / 示例说明 / 应产出清单 / 示例运行产物 |

## 7. 自查清单（收尾前逐项确认）

- [ ] `result.json` 存在；`case_id` 与输入一致；`status` ∈ {completed, partial, failed}
- [ ] `output_contract` 声明字段全部出现在顶层（`self_check.json → contract_check.valid == true`；四形态回显、无 null）
- [ ] `plan_gates.json` 与 `result.audit.plan_gates` 存在；P1–P8 未全过时 uncertainty 有对应条目
- [ ] 每一页（除封面/目录/问答备用页）都有 `evidence[0].locator`（L行号 · §章节）+ `quote` 原句
- [ ] `evidence_audit.json` 逐页核对过；所有 `evidence.source_file` 都能在 `sources[]` 中找到
- [ ] `editable_deck.pptx` 存在且能被打开（verify_deck 复核）；每页有讲稿备注；页数 == 计划
- [ ] 预览 PNG 存在且每张带「PIL 模拟预览」水印；`preview_manifest.json` 已说明限制与字体探测结果
- [ ] 数字可信：页面上的数字在源材料中可定位（warnings 已审查）
- [ ] 没有预置正式答案：`examples/` 仅为合成的接口示例（`case_id` 形如 `example-*`）
- [ ] **失败注入演练跑过且为 0 静默失败**：`fault_inject.py --sandbox <包外目录>` 退出码 0；
      矩阵里没有 `silent_failure=true` 的行
- [ ] **期望与实测一致**：矩阵每行要么 MATCH，要么写着"期望修订说明"并给出为什么原期望是错的
- [ ] **演练没在包内留下痕迹**：跑完后 `selftest.py --package-check "$SKILL_DIR"` 仍报无 `__pycache__`（G10）
- [ ] **资源形态硬门**：只含七种扩展名；≤50 个 UTF-8 文本文件；单文件 ≤500KB；合计 ≤2MB；
      无符号链接；无 `__pycache__`/`.pyc`；**无本机绝对路径残留**
- [ ] 包内**不存在任何**该七种扩展名之外的文件；二进制示例输入由 `make_synthetic_inputs.py` 运行时生成

## 8. 平台约束（Runtime contract 要点）

- 平台把本 Skill 安装到 `/skills/weekly-skill` 后在**固定 3 个案例 × 3 次复跑**上运行；
- 输入 `/input/case.json` + `task.md`；在 `/app/work` 干中间活；最终产物 `result.json` +
  可编辑源 + 渲染预览放 `/app/output`；`result.json` 必须含 output_contract 全部字段与 `case_id`；
- **提交资源**：≤50 个 UTF-8 文本文件、单文件 ≤500KB、合计 ≤2MB、无符号链接（§9 逐条处置）；
- **运行期产物可以是二进制**，且不因 `result.json` 的最终有效性而被丢弃；
- 诚实记录 `status/sources/uncertainty/change_records`；不编造缺失软件状态与科学数据；
- 执行预算：64 个模型请求 / 900 秒 / 每响应 16384 token（含推理）；尽早保存部分成果，渐进改进。

## 9. 资源形态：为什么包内没有二进制，以及逐类处置

题面只允许 UTF-8 文本资源作为 Skill 资源（runtime artifacts 不在此列），因此本包**只用文本**表达规则、
脚本与示例；所有二进制一律改由脚本现场生成：

| 原本常见的二进制资源 | 本包的做法 |
|-|-|
| 内置模板 `*.pptx` | **不随包**：`deck_builder._new_deck()` 用 python-pptx 现场构建 16:9 母版/主题；案例自带模板时直接读取平台提供的模板 |
| 示例图 `*.png` | **不随包**：`make_synthetic_inputs.py` 用 Pillow 画纯几何示意图（带 `SYNTHETIC` 标注，不含测量值） |
| 示例 PDF | **不随包**：同一脚本手工构造最小 PDF（零第三方依赖、字节确定、pypdf 可解析） |
| 示例输出 `*.pptx/*.png/*.svg` | **不随包**：改为 `examples/EXPECTED-OUTPUT.md` 用**文字**列出应产出文件清单与实测数量 |
| 示例输出 `*.json` | **随包但净化**：只保留 `result.example.json` / `self_check.example.json`，路径全部为相对形式 |
| 字体 `*.ttf/*.otf` | **不随包**：运行时按候选路径探测系统字体（`/usr/share/fonts`、`/System/Library/Fonts`、`C:/Windows/Fonts`），结果记入 `result.json.environment.cjk_font` 与 `preview_manifest.json`；找不到则用 Pillow 内置位图字体并在 manifest 记明 |
| `scripts/__pycache__`、`*.pyc` | **不随包**：提交前删除（`selftest.py --package-check` 的 G10 会检查） |
