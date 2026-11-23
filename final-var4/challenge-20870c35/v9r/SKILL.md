---
name: academic-talk-organizer
description: >
  组织学术汇报内容（学术 PPT 页面组织）：从论文/研究材料到可讲、可编辑、证据可追溯的演示文件。
  当输入包含科研论文材料、研究报告、组会/答辩/评审任务、听众与时长、页数与模板约束、讲稿或备注需求，
  关键词如 学术汇报、答辩PPT、组会汇报、slides、deck、页码规划、讲稿、备注、问答准备、听众适配、
  叙事顺序、汇报内容组织、evidence mapping、模板适配、plan contract、quality gates 时使用本 Skill：
  读真实材料 → 抽取研究问题/方法/结果/局限 → 生成页级计划（scaffold_plan）并经计划契约门
  P1–P8（validate_plan + assets/plan.schema.json）校验 → python-pptx 生成可编辑 .pptx
  （模板适配或内置主题；确定性元素命名 + 讲稿/备注 + 图占位）→ verify_deck 校验
  → PIL 渲染 PNG 预览 → evidence_audit 逐字审计 → finalize_result 写含证据映射、来源、
  不确定性、审计链路的 result.json。严格以真实文件为准，不臆造数据，不提交预制答案；
  二进制示例输入（PDF/PNG）由 make_synthetic_inputs.py 在运行时生成，包内只含 UTF-8 文本资源。
  另：本版为**缺依赖可用性**增量版，包内新增 scripts/degrade_probe.py 用受控导入拦截实测 12 个缺库配置 + 5 级最小环境（实测全部 exit 0 且仍写 result.json；缺 Pillow 时产物数由 21 降到 6），逐格数据与最小可用环境清单见 references/DEGRADE-MATRIX.md。
---

# 学术汇报内容组织（academic-talk-organizer）v2 · 合规重打包版

面向「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35（slides 组）。
把**已有**的论文/研究材料组织成：结构清楚、证据可追溯、可编辑、符合听众与模板约束的学术汇报产物。
本 Skill 不负责论文精读成文、写作成稿与科研绘图本身（相邻课题负责），只负责
**从已有内容材料到可讲页面的组织与交付**。

> **本版的两条硬约束（题面 Runtime contract 原文）**：
> ① `Skill resources: at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks.`
> ② `Runtime artifacts may be binary and are retained independently of final JSON validity.`
> ⇒ 提交资源**只有文本**（`.md/.py/.json/.txt/.csv/.yaml/.yml`），`.pptx/.png/.pdf` 等**一律由脚本运行时生成**，
> 包内不含任何本机绝对路径、无 `__pycache__`、无符号链接。理由与逐类处置见 §9。

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
  `Pillow` 缺失 → 跳过预览（非致命）；`pypdf` 缺失 → PDF 记未解析。见 §6 的 D15。
- **本机实测环境**：Python 3.13.9 / python-pptx 1.0.2 / Pillow 12.3.0 / pypdf 6.14.2（记录见 `TEST.md`）。

## 2. 输入与输出

### 输入（平台运行期）

| 路径 | 内容 |
|-|-|
| `/input/case.json` | 案例标识 `case_id`、`title`、`report_goal`、`audience`、`duration_min`、`slide_count`、`report_type`、`materials`（材料清单，可为 `{path,role}`）、`template`/`start_deck`（可选模板或起始演示）、`figure_files`（可选 图表引用→图片路径 映射）、`output_contract`（可选字段声明） |
| `/input/task.md` | 任务说明；可能含 output_contract 声明（fenced JSON 或字段表） |
| 材料目录 | `case.json` 中列出的文本/PDF（缺省取 `<case 目录>/materials`），类型不限：`.md/.txt/.pdf` 与图片附件 |

**必须实际读取文件内容**（`main.py` 已按真实路径读取并逐文件解析记录），
不得根据标签/文件名预设内容。`main.py` 自动发现材料目录中的 md/txt/pdf/图片。

### 输出（--out，平台运行期即 /app/output）

```
result.json            # 唯一评分产物：契约字段 + 主结果 + 证据定位 + status/sources/
                       #   uncertainty/change_records/environment + audit{plan_gates,evidence,deck,gates}
talk_plan.json         # 页级计划（叙事顺序、每页主张/证据/讲稿/问答）——可编辑中间产物
plan_gates.json        # 计划契约门 P1–P8 结果（assets/plan.schema.json 驱动）
evidence_map.json      # 源文件 → {用到它的页, 图表引用} 反向映射
evidence_audit.json    # 逐页逐字引文审计（含 derived/占位/数字对源说明）
deck_audit.json        # deck 机器校验（打开/页数/备注/claim 元素/OPC/规范化 sha）
editable_deck.pptx     # 可编辑演示文件（python-pptx；模板适配或内置主题；确定性元素命名）
                       #   ← 运行期产物（二进制），不进提交资源
previews/
  cover_preview.png    # 封面预览（PIL 模拟，如实标注）        ← 运行期产物
  slide_0NN.png        # 逐页缩略图（PIL 模拟）                ← 运行期产物
  preview_grid.png     # 整包缩略网格                          ← 运行期产物
  preview_manifest.json# 预览清单、渲染方法、字体探测结果与限制说明
self_check.json        # validate_result + check_contract + 门 + 确定性探针
```

> `result.json` 里的路径一律是**可移植形式**：写盘时把本机绝对路径（`X:\...`/UNC）改写成
> 相对案例目录的路径（如 `materials/fig2.png`），POSIX 运行期路径（`/input/...`、`/app/...`）原样保留。
> 因此产物里不会残留作者机器的路径痕迹，评审拿到包后不会看到作者机器的盘符路径这类调试残留。
> 产物清单与示例数量见 `examples/EXPECTED-OUTPUT.md`。

## 3. 核心方法（五个突破方向的落点）

1. **报告目标**：`report_goal` 写入封面与成功标准；缺省按汇报类型给默认成功标准
   （组会=讲清进度与风险；答辩=创新点与边界、证据链；评审=结论的证据强度与适用范围）。
2. **听众**：听众描述 → `expert`/`familiar`/`lay`，决定背景/术语页占比（10%/18%/30%）
   与术语表收录（`scaffold_plan.py::resolve_audience`）。
3. **叙事顺序**：每汇报类型一套「块+权重+顺序」（`templates/talk_config.json`，可编辑）：
   组会=问题—进度—方法—结果—风险—问答；答辩=…创新点边界后置；评审=结论先行。
   页数按时长×60/85s 推导，**校准到任务冻结页数**（P3 门），而不是跟随论文章节长度。
4. **重点信息**：一页一主张（`claim` 逐字自源材料）+ 一句话讲稿（`one_liner`）+
   证据强度分级（含数值/统计/图表引用→strong；结果动词→medium；间接概括→weak）；
   框架缺失时可概括成页但标 `derived=true`。
5. **问答准备**：每条局限/风险主张与每条 strong 结果各生成一条预判追问与回答要点
   （指向证据定位），收拢到 `qa` 备用页；讲稿备注含【本页主张】【证据】【讲解】【备答】。

## 4. 执行步骤（检查点 CP1–CP5，按序执行，别跳步）

> **自定位（重要）**：`$SKILL_DIR` = 本包根目录（含 `SKILL.md` 的那个目录；
> 平台安装后即 `/skills/weekly-skill`）。所有脚本用 `os.path.dirname(__file__)` 自定位，
> **命令与当前 cwd 无关** —— 在任意目录执行下面任何一条都能跑通。
>
> ```bash
> # 先在 shell 里定一次（把路径换成你的实际安装位置）
> SKILL_DIR=/skills/weekly-skill              # Linux / 平台容器
> SKILL_DIR="<本包所在目录>"                  # Windows（Git Bash，含盘符）
> # 下面所有命令统一写成 python "$SKILL_DIR/scripts/xxx.py"
> ```

### CP1 · 输入契约
1. 读 `case.json`（case_id/report_goal/audience/duration_min/slide_count/report_type/
   materials/template/output_contract）与 `task.md`（约束 + 可能的 output_contract）；
   缺任一关键字段按 D7/D6 处置并记录。
2. 解析材料目录（含显式清单 + 自动发现）；缺失/未解析材料如实标记（F1/F2）。
3. 解析模板/起始演示（显式参数 > case 字段 > 材料目录扫描）（F5/F6）。
4. 环境预检：探测 `python-pptx`/`Pillow`/`pypdf` 与系统中文字体，写入
   `result.json.environment` 与 `change_records`（决定本次能产出哪些产物，见 D15）。

### CP2 · 计划门
5. 运行主流程（一条命令完成 抽取→规划→.pptx→校验→预览→审计→result.json→自检）：
   ```bash
   python "$SKILL_DIR/scripts/main.py" \
     --case /input/case.json \
     --task /input/task.md \
     --out /app/output
   ```
   - 内部：`scaffold_plan.build_plan` 产出页计划并写 `talk_plan.json`；
     `validate_plan.validate_plan` 按 `assets/plan.schema.json` 执行 P1–P8，
     结果写 `plan_gates.json`；未全过 → D9 降级（继续生成 honest 产物，不中断）。
   - 退出码：**0** = 已产出通过 validate+contract 的 `result.json`（其 `status` 说明
     `completed` 还是 `partial`）；**1** = 没有可用的契约结果；**2** = 参数用法错误。
6. 需要手工精修计划时：改 `talk_plan.json`/`talk_config.json` 后重跑（可直接改
   `talk_plan.json` 再被后续步骤读取——注意重跑会重新 scaffold，如需锁定请修改
   `talk_config.json` 的规则或直接跑 `--case` 前先改配置）。

### CP3 · 生成与校验门
7. 案例自带模板/起始演示 → python-pptx **打开并沿用其母版与版式**，页数按冻结计划重建
   （模板自带的示例页会被丢弃，见 D16；最终页数 == 冻结页数）；
   无模板则用包内置主题（16:9 母版+主题色+底栏）。
   每个 Skill 创建的图形元素带确定性命名（`page-claim-NN`/`page-figure-NN` …）。
   图片文件按引用号绑定（`Fig. 2 → materials/fig2.png`，运行时解析相对/绝对路径两种写法）；
   材料没有对应图片 → 页内诚实占位框（D4）。
8. `verify_deck` 校验 deck（打开、页数==计划、每页备注与 claim 元素、OPC 完整），
   结果写 `deck_audit.json`；未过 → D11。缺 `python-pptx` → D15。

### CP4 · 渲染门
9. 预览自动为 **PIL 模拟渲染**（每张 PNG 带水印，`preview_manifest.json` 说明渲染方法、
   字体探测结果与占位图清单）；`--skip-previews` 可跳过逐页缩略图只留封面+网格。

### CP5 · 审计与收口门
10. `evidence_audit` 逐页逐字核验引文（derived 页按概括语如实记录），写
    `evidence_audit.json`；未过 → D13。
11. `finalize_result` 组装 result.json（output_contract 四形态回显，禁 null）+
    `self_check.json`（validate + contract + 门快照 + 确定性探针）；`selftest.py`
    可对任意输出目录独立复核（G1–G10 + `--package-check` 包约束 G10）。
12. 人工核对自查清单（§7）后再收尾；按需精修后重跑。

## 5. 脚本与资源清单

| 文件 | 角色 | 作用 |
|-|-|-|
| `scripts/main.py` | build 编排 | 编排器：CP1–CP5 门控；环境预检→材料解析→计划→校验→deck→预览→审计→result→自检（唯一入口） |
| `scripts/evidence.py` | extract | 材料加载（md/txt/PDF-pypdf）与主张/证据锚点抽取 |
| `scripts/scaffold_plan.py` | build | 页级规划：听众→背景比例、叙事顺序、一页一主张、问答预演、图绑定（v1 planner 拆分对齐） |
| `scripts/validate_plan.py` | verify | 计划契约门 P1–P8（schema 驱动）；独立 CLI |
| `scripts/evidence_audit.py` | verify | 逐页逐字引文审计 + 定位/数字/图绑定；独立 CLI（对齐高分 evidence_audit） |
| `scripts/deck_builder.py` | render | python-pptx 生成/模板适配可编辑 .pptx（母版/版式复用、自带页丢弃、确定性命名、讲稿备注、图占位）；缺依赖时明确抛错交编排器降级 |
| `scripts/verify_deck.py` | verify | deck 打开/页数/备注/命名/OPC/规范化 sha 校验；独立 CLI |
| `scripts/render.py` | render | PIL 模拟预览（封面/逐页/网格 + manifest + 字体探测 `font_status()`） |
| `scripts/validate_result.py` | verify | result.json 结构+文件+数字可对源校验（可独立 CLI） |
| `scripts/check_contract.py` | verify | output_contract 字段齐全性校验（可独立 CLI） |
| `scripts/finalize_result.py` | verify/build | result 信封组装：契约回显 + 审计嵌入 + environment + self_check + 确定性探针 |
| `scripts/selftest.py` | verify | 全链路复核（G1–G10）+ 包约束审计；独立 CLI |
| `scripts/common.py` | shared | 自定位、JSON IO、契约工具、确定性投影 hash、**本机绝对路径净化**（`portable_path`/`sanitize_output`）+ 输入路径解析 |
| `scripts/make_synthetic_inputs.py` | assets | **运行时生成示例二进制输入**：`dataset_card.pdf`（零依赖手工 PDF）、`fig2.png`（纯几何示意图）、`--template` 时的 `synthetic_template.pptx` |
| `templates/talk_config.json` | assets | 可编辑叙事规则：每类型页权重/顺序/问答模板 + deck_rules |
| `templates/narrative_template.md` | assets | 叙事模板人类可读版（与 talk_config 同一套 block） |
| `templates/slide-checklist-template.md` | assets | 逐页上台前核对清单（人核） |
| `assets/plan.schema.json` | assets | 计划契约模式（P1–P8 驱动源，单点真相） |
| `assets/result.template.json` | assets | result 信封模板（示例） |
| `references/OUTPUT_CONTRACT.md` | docs | result.json 契约（字段/类型/status 语义/路径可移植性/退出码/复核命令） |
| `references/RUBRIC_MAP.md` | docs | **五维评分（40/25/15/10/10）→ 本包文件与机制逐条对照** |
| `references/plan-contract.md` | docs | 计划契约（P1–P8 条款 + schema 说明） |
| `references/quality-gates.md` | docs | 质量门 G1–G10（全链路收口，含 G10 包约束） |
| `references/failure-modes.md` | docs | 失败模式处置表（F1–F26 + 决策规则 D1–D17 + 状态一致性） |
| `references/evidence-audit.md` | docs | 证据审计规范 |
| `references/deck-rules.md` | docs | 页面/版式/命名规则 |
| `COMPARE.md` | docs | 对照方案（基础做法 vs 加载本 Skill）+ A/B 口径 + 不利对照结果 |
| `examples/README.md` | demo | 合成示例说明与运行步骤（二进制输入运行时生成） |
| `examples/EXPECTED-OUTPUT.md` | demo | 应产出文件清单 + 契约字段 + 实测数量（替代随包二进制示例产物） |
| `examples/output/*.example.json` | demo | 示例案例上的真实运行产物（带 `.example` 标明非正式案例结果） |

## 6. 异常处理（决策规则 D1–D17，全表见 references/failure-modes.md）

| 决策规则 | 情形 | 处置（全部如实记录到 result.json 的 uncertainty/change_records） |
|-|-|-|
| D1 | 材料缺失 | `sources` 中 kind=missing；status 视影响降 `partial`；不编造其内容 |
| D2 | 材料是 PDF 且无 pypdf / 解析失败 | 记录 parsed=false + 原因；其余材料照常，相关页证据弱化或缺失 |
| D3 | PDF 抽取丢公式/符号 | quote 以抽取文本为准并注明抽取代理方式 |
| D4 | 论文缺图/图分辨率低/图损坏 | 页内**诚实占位框**（标注"材料未提供图片文件"），notes 提示对照原文；坏图跳过 |
| D5 | 无模板/模板路径失效/模板打不开 | 采用内置主题并在 artifacts.template_used/deck_mode 注明 |
| D6 | 页数与时长推导冲突 | 以任务冻结页数为准（P3），plan_gates 记录说明 |
| D7 | 听众信息缺失 | familiar + 中等证据深度保守处理，audience.notes 注明可覆写 |
| D8 | 材料中某块无直接主张 | 用该块章节概括成页（derived=true、weak），framing 记 change_records |
| D9 | 计划门 P1–P8 未全过 | 记录 errors；仍生成 honest 产物；status→partial；uncertainty 列出 |
| D10 | 导出/生成抛错、超时 | 非致命：仍写 result.json；中间产物尽早落盘；异常写入 change_records；保存部分结果并说明限制 |
| D11 | verify_deck 发现问题 | 记录 entries；status→partial；不宣称"校验通过" |
| D12 | 预览失败/超时 | 非致命：仍写 result.json（status 视情况 partial）；`--skip-previews` 可跳过 |
| D13 | 证据审计发现引文未逐字命中 | 记录条目（derived 页按概括语）；可修则修，不能修则如实保留 |
| D14 | 页面数字与源不一致 | validate_result 给警告；人工核对，误报（合理换算）可忽略但需说明 |
| D15 | **缺 `python-pptx`（或连带 Pillow）** | **不崩**：跳过 deck，`status→partial`，`artifacts.editable_deck=null` + `deck_limitation` + uncertainty 记明；页计划/计划门/预览/result.json 照常落盘，命令仍返回 0；补齐依赖后重跑同一命令即可 |
| D16 | **模板/起始演示自带示例页** | 保留其母版/版式，**丢弃自带页**后按冻结计划重建整份 deck（`deck_mode.template_slides_present/dropped` + change_records 记明），保证最终页数 == 冻结页数 |
| D17 | **材料为空 / 全部不可解析** | 只产出结构性页面；`status→partial` + uncertainty 明写"没有任何材料被解析为文本"；不据标签补造内容 |

## 7. 自查清单（收尾前逐项确认）

- [ ] `result.json` 存在；`case_id` 与输入一致；`status` ∈ {completed, partial, failed}
- [ ] `output_contract` 声明字段全部出现在 result.json 顶层（`self_check.json → contract_check.valid == true`；四形态回显、无 null）
- [ ] `plan_gates.json` 与 `result.audit.plan_gates` 存在；P1–P8 未全过时 uncertainty 有对应条目
- [ ] 每一页（除封面/目录/问答备用页）都有 `evidence[0].locator`（L行号 · §章节）+ `quote` 原句
- [ ] `evidence_audit.json` 逐页核对过：逐字命中或 derived 概括语如实标注；所有 `evidence.source_file` 都能在 `sources[]` 中找到
- [ ] `editable_deck.pptx` 存在且能被打开（verify_deck 复核）；每页有讲稿备注；页数 == 计划
- [ ] 预览 PNG 存在且每张带「PIL 模拟预览」水印；`preview_manifest.json` 已说明限制与字体探测结果
- [ ] 数字可信：页面上的数字在源材料中可定位（warnings 已审查）
- [ ] 没有预置正式答案：`examples/` 仅为合成的接口示例（`case_id` 形如 `example-*`），平台案例从 `/input` 实际读取
- [ ] 依赖缺失/材料异常时**如实降级**：`status=partial` + `uncertainty` + `change_records`（跑 `TEST.md` §8 的六个分支复核）
- [ ] **资源形态硬门**（题面 Runtime contract）：只含 `.md/.py/.json/.txt/.csv/.yaml/.yml`；≤50 个 UTF-8 文本文件；
      单文件 ≤500KB；合计 ≤2MB；无符号链接；无 `__pycache__`/`.pyc`；**无本机绝对路径残留**
      （`python "$SKILL_DIR/scripts/selftest.py" <out> --package-check "$SKILL_DIR"` 机器查 + 人工 grep 盘符绝对路径）
- [ ] 包内**不存在任何**该七种扩展名（`.md/.py/.json/.txt/.csv/.yaml/.yml`）之外的文件（含二进制、含 `__pycache__`）；
      二进制示例输入由 `make_synthetic_inputs.py` 运行时生成（见 §9）

## 8. 平台约束（Runtime contract 要点）

- 平台把本 Skill 安装到 `/skills/weekly-skill` 后在**固定 3 个案例 × 3 次复跑**上运行；
- 输入 `/input/case.json` + `task.md`；在 `/app/work` 干中间活；最终产物 `result.json` +
  可编辑源 + 渲染预览放 `/app/output`；`result.json` 必须含 output_contract 全部字段与 `case_id`；
- **提交资源**：≤50 个 UTF-8 文本文件、单文件 ≤500KB、合计 ≤2MB、无符号链接（§9 逐条处置）；
- **运行期产物可以是二进制**，且不因 `result.json` 的最终有效性而被丢弃（预览/`.pptx` 属此类）；
- 诚实记录 `status/sources/uncertainty/change_records`；不编造缺失软件状态与科学数据；
- 执行预算：64 个模型请求 / 900 秒 / 每响应 16384 token（含推理）；尽早保存部分成果，渐进改进。

## 9. 资源形态：为什么包内没有二进制，以及逐类处置

题面只允许 UTF-8 文本资源作为 Skill 资源（runtime artifacts 不在此列），因此本包**只用文本**表达规则、
脚本与示例；所有二进制一律改由脚本现场生成：

| 原本常见的二进制资源 | 本包的做法 |
|-|-|
| 内置模板 `*.pptx` | **不随包**：`deck_builder._new_deck()` 用 python-pptx 现场构建 16:9 母版/主题；案例自带模板时直接读取平台提供的模板 |
| 示例图 `*.png` | **不随包**：`scripts/make_synthetic_inputs.py` 用 Pillow 画纯几何示意图（带 `SYNTHETIC` 标注，不含测量值） |
| 示例 PDF | **不随包**：同一脚本手工构造最小 PDF（零第三方依赖、字节确定、pypdf 可解析） |
| 示例输出 `*.pptx/*.png/*.svg` | **不随包**：改为 `examples/EXPECTED-OUTPUT.md` 用**文字**列出应产出文件清单与实测数量 |
| 示例输出 `*.json` | **随包但净化**：只保留 `result.example.json` / `self_check.example.json`，且其中路径全部为相对形式 |
| 字体 `*.ttf/*.otf` | **不随包**：运行时按候选路径探测系统字体（`/usr/share/fonts`、`/System/Library/Fonts`、`C:/Windows/Fonts`），探测结果记入 `result.json.environment.cjk_font` 与 `preview_manifest.json`；找不到则用 Pillow 内置位图字体并在 manifest 记明 |
| `scripts/__pycache__`、`*.pyc` | **不随包**：提交前删除（`selftest.py --package-check` 的 G10 会检查） |

## 附:本版增量 —— 缺依赖降级链实测

> 上面第 1–9 章是基线正文，**一字未改**；本章只补一条**可执行、有实测数字**的增量 ——
> 题面把可用性写成硬要求（`可靠体验 10` 的"异常处理 3 分"：识别与处置**字体缺失**、**导出失败**、
> **超时**等情况），而真实评测容器里"哪个库装了、哪个没装"**不由我们决定**。
> 所以这一版不写"理论上会降级"，而是给出一张**跑出来的表**：
> 缺哪个库、还剩什么、`status` 变什么、是否仍写 `result.json`、退出码是多少。
> 逐格数据见 `references/DEGRADE-MATRIX.md`（本轴核心文档），本节给的是命令、判据与实测数字。

### C1. 一条命令：12 个缺库配置 + 5 级最小环境

```bash
# $SKILL_DIR = 本包根目录（含 SKILL.md；平台安装后即 /skills/weekly-skill）
python "$SKILL_DIR/scripts/degrade_probe.py" \
    --sandbox /tmp/dg --report /tmp/dg/degrade_matrix_report.json
# 期望：probes=12 unreadable=0 unmet=0; ladder=5，退出码 0
```

**它怎么模拟缺库**：在**子进程**的 `sys.meta_path` 上装一个按模块名前缀拒绝导入的拦截器，
然后 `runpy.run_path()` 执行 `scripts/main.py`。拦截只作用于被启动的那个子进程，
**不改本机任何已安装包**。退出前子进程把自己加载过的模块清单写成 JSON ⇒
"拦截是否真的生效"由证据说话，不靠自述。

每格记录：`exit_code` · `status` · **产物清单**（还剩哪些文件）· `artifacts.editable_deck` ·
预览 PNG 张数 · 是否写 `result.json` · 依赖相关 `uncertainty` 与 `change_records` ·
`environment` 快照 · 被拦模块是否真的没被加载。报告里另含 `host_dependency_snapshot`
与 `cli_availability`（照实记录本机有没有 `soffice` / `libreoffice`）。

### C2. 三个关键实测发现

**① 缺 Pillow 会连带让可编辑 `.pptx` 也产不出来。**
`python-pptx` 自己声明依赖 `Pillow >=3.3.2`（`importlib.metadata` 实测输出：
`['Pillow >=3.3.2', 'XlsxWriter >=0.5.7', 'lxml >=3.1.0', 'typing-extensions >=4.9.0']`），
`deck_builder.py` 的顶层 `try: from pptx import ...` 因此失败，整条 deck 路径被判为
"python-pptx 不可用"。

| 格 | 被拦 | `result.json.environment` | 产物数 | deck | 预览 PNG |
|-|-|-|-|-|-|
| D-00 对照 | 无 | pptx=1.0.2 / pillow=12.3.0 / pypdf=6.14.2 | **21** | 有 | 12 |
| D-01 | `pptx` | **pptx=null** / pillow=12.3.0 / pypdf=6.14.2 | 19 | 无 | 12 |
| D-02 | `PIL` | **pptx=null / pillow=null** / pypdf=6.14.2 | **6** | 无 | **0** |
| C-02 | `pptx` + `PIL` | pptx=null / pillow=null | 6 | 无 | 0 |

⇒ 只报"缺 Pillow 则没有预览"是**不完整的**：真正的事实是**可视化产物全线消失**。

**② 只放行顶层模块 `pptx` 不够，传递依赖必须一起在。**
最小环境阶梯 M-02（只放行 `pptx`）实测 deck 仍为"无"，原因是子进程报
`[degrade_probe] non-whitelisted third-party module lxml blocked`；
把传递依赖一起放行（M-04）后 deck 立刻恢复。
⇒ **"装了 python-pptx" ≠ "能 import python-pptx"**，安装清单必须写全。

**③ `matplotlib` / `numpy` / `yaml` 的降级格子是纯 no-op，而且可证。**
三格的 `sys.modules` 清单里对应模块均为"从未出现"，产物与对照格逐项相同。
把它们记成"降级通过"是错的 —— 正确说法是**本包不依赖它们**
（这也解释了为什么 `README.md` 的依赖表里它们标着"不需要"）。

### C3. 降级全景（12 个配置，全部 exit 0、全部写出 `result.json`）

| 形态 | 实测格 | 产物数 | 还剩什么 |
|-|-|-|-|
| 完整 | D-00、D-03、D-04、D-05、D-06、O-01 | **21** | `result.json`、`self_check.json`、`talk_plan.json`、`evidence_map.json`、`plan_gates.json`、`evidence_audit.json`、`deck_audit.json`、`editable_deck.pptx`、`previews/`（cover + grid + 12 张 slide PNG + manifest） |
| 缺 pptx（有预览） | D-01、C-01 | 19 | 同上**减去** `editable_deck.pptx` 与 `deck_audit.json` |
| 缺 Pillow（预览与 deck 都没） | D-02、C-02、C-03、O-02 | **6** | 只剩 `result.json`、`self_check.json`、`talk_plan.json`、`evidence_map.json`、`plan_gates.json`、`evidence_audit.json` |

**下界结论**：没有任何一种缺依赖形态能让 `result.json` 消失，也没有任何一格返回非零退出码；
最坏情况下仍交付页级计划、计划门、证据映射、证据审计、自检，以及**含全部契约字段的 `result.json`**。

### C4. 最小可用环境（三档，均有实测对应格）

```bash
# ① 只要契约结果（无任何第三方依赖：Python 3.8+ 标准库即可）
python "$SKILL_DIR/scripts/main.py" --case <case> --out <out> --quiet
# 实测 M-01：exit 0；6 个产物；result.json 契约字段齐全；status=partial

# ② 要预览
python -m pip install "Pillow>=10"
# 实测 M-03：exit 0；19 个产物；12 张 PNG 预览

# ③ 要完整形态（可编辑 deck + 预览 + PDF 解析）
python -m pip install "python-pptx>=1.0" "Pillow>=10" "pypdf>=6"
# 实测 M-04 / M-05：exit 0；21 个产物；deck + 12 张预览
# python-pptx 的传递依赖（缺一就 import 失败）：Pillow / lxml / XlsxWriter / typing-extensions
# 可选且实测为 no-op（不必安装）：matplotlib / numpy / PyYAML
# 可选且本机没有（本包不调用，仅用于人工核对视觉）：LibreOffice / PowerPoint
```

按实测，**`python-pptx` + `Pillow` + `lxml` 三者齐备**即可拿到完整形态；
`pypdf` 只在材料是 PDF 时才需要（缺了按"未解析"如实记录）。
本机 `shutil.which("soffice")` 与 `"libreoffice"` **均为 None** ——
Office 真实栅格化本机就不可用，本包不调用它，O-01 格与对照格逐项相同，
预览是 PIL 模拟且已在 `preview_manifest.json` 与 `uncertainty` 里如实声明。

### C5. 哪些功能彻底不可用（照实说）

| 功能 | 何时彻底不可用 | 实测格 |
|-|-|-|
| 可编辑 `.pptx` | 缺 `python-pptx`；**或**缺 `Pillow`（连带）；**或**缺 `lxml` 等传递依赖 | D-01 / D-02 / M-02 |
| PNG 预览（含逐页缩略图） | 缺 `Pillow` | D-02、C-02、C-03、O-02 |
| Office 真实栅格化（导出保真） | **本机就是不可用**（`soffice` 与 `libreoffice` 都不在 PATH）；本包不调用它 | O-01（与对照格逐项相同） |
| PDF 材料文本解析 | 缺 `pypdf`：退化为"按未解析如实记录" | D-03、C-03 |
| 页计划 / 证据链 / 计划门 / 证据审计 / `result.json` | **没有任何缺依赖形态能让它消失** | M-01（只剩标准库，6 个产物里仍有 `result.json`） |

### C6. 本轴落在哪些文件（与既有能力的关系）

- **新增**：`scripts/degrade_probe.py` —— 基线 §5 的脚本清单与既有 14 个入口 **逐字保留不动**，本轴只在此之外新增这一个入口。
- **保持不变**：**这一版不改任何既有脚本**（v7/v8/v9 三个包里，v8 是唯一改了既有脚本的一份）；
  基线的全部 `scripts/*.py` 与全部 `--flag` 逐一保留；`main.py` 的退出码语义
  （`0` = 已产出通过 validate+contract 的 `result.json`、`1` = 没有可用的契约结果、
  `2` = 参数用法错误）不变 —— **缺依赖属于"诚实降级"，走的是 0 + `status=partial`，不是崩溃。**
  相关既有机制原样承担降级：`deck_builder.dependency_status()` 探 pptx/PIL/pypdf、
  `render.font_status()` 运行时探测系统字体、`evidence.py` 缺 pypdf 时 PDF 记 `parsed=false` + 原因。
- 收尾自查在上述 §7 清单之外再加三项：① `degrade_probe.py` 跑过且 exit 0
  （`probes=12 unreadable=0 unmet=0`、`ladder=5`）；② 报告 `host_dependency_snapshot`
  与本机实际一致、`cli_availability.soffice/libreoffice` 照实（本机为 null）；
  ③ `result.json` 的 `status` 与 `artifacts.editable_deck` 一致：deck 为 null 时必须有一条
  `deck_limitation` 与一条 `uncertainty`。

> **不要在包内目录里跑脚本**（会生成 `__pycache__`，合规硬门直接拒收）。
> `degrade_probe.py` 会把技能复制到沙箱里、并让被调用的入口也指向沙箱副本。
