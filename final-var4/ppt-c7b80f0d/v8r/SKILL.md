---
name: paper-to-academic-ppt
description: 把论文/研究材料转换成主线清晰、证据可追溯、可编辑的学术汇报 PPT。加载后按"读实际文件→抽主线与证据→蓝图规划 deck-spec→CP1 lint→模板适配生成可编辑 .pptx→渲染预览→导出检查→写带全部 output_contract 字段的 result.json"全流程执行，页级主张、图表编号引用、讲解备注分离生成，缺失证据显式标注、不编造数据，五维评分在 RUBRIC_MAP.md 中逐条自评。Use when a task asks to turn a paper or research material into an academic slide deck (论文转PPT、学术汇报PPT、slides from paper、presentation from paper), especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews. 本版另加一章增量 —— scripts/contract_matrix.py 把 output_contract 的四种形态与边界值逐个注入并真跑端到端流程，实测 28 个单元 28/28 写出 result.json、静默通过 0 条（修复前 5 条）。
---
# 论文转学术 PPT（paper-to-academic-ppt）

本 Skill 负责"论文内容 → 可讲、可核验、可编辑的学术汇报 PPT"这条链路：
先按**页面蓝图**（论文结构→页面结构）做一次结构重写，产出**页级离散表达**
（一页一个主张，主张挂论文图/表/章节定位），在组织方模板内排布，
交付可复核的 `result.json`、逐页证据映射与诚实渲染预览。

**不负责**：论文精读结论的生成、科研绘图本身的图形设计、学术写作润色。
**不使用预制答案**：正式运行只依据案例实际提供的文件，示例仅说明接口。

**执行顺序（先读契约，再规划，后生成，最后自评）**：
**① 读 `references/OUTPUT_CONTRACT.md`**（交付什么、必须回显哪些字段）→
**② 按 `references/slide-blueprint.md` 规划页面蓝图并写 deck-spec** →
**③ `spec_lint` 做 CP1 结构性 lint**（不过则按 D4 记录偏差后酌情继续）→
**④ `main.py` 生成 .pptx（assetkit→deckgen→ooxml_kit）** →
**⑤ 导出检查 `export_check`（CP3，G1–G8）+ `check_contract`（契约字段覆盖）** →
**⑥ 按 `references/RUBRIC_MAP.md` 逐条自评五维覆盖**。
出错或降级一律查 `references/failure-modes.md`（识别→处置→记录→退出码）。

---

## 1. 用途与适用条件

- 输入一份科研材料（论文 PDF / 文本文稿）＋案件约束（audience / 时长 / 页数 / 模板），
  输出一套学术汇报：
  - 主线成立、页序可讲（问题→方法→证据→结论→局限）；不是按段落顺序搬运；
  - 每页内容可回溯到论文的图/表/章节/页码（**逐页证据映射表**）；
  - 在组织方模板内排布（模板占位符约束；无模板时用内置学术版式），页脚/配色不被覆盖；
  - 讲解备注与页面文字**分离**生成（notes_slide，含封面与收尾页）；
  - 源文件可编辑（.pptx，**对象分层命名**可被后续工具按名查找），并有渲染预览
    （无 PowerPoint/LibreOffice 时为 PIL 近似预览，如实标注）。
- 触发场景：`/input/case.json` + `task.md`（平台固定案例）；或用户直接要求
  "把这篇论文做成学术 PPT / slides from this paper"。

## 2. 输入输出

| 方向 | 路径（以环境实际挂载为准） | 内容 |
|-|-|-|
| 输入 | `/input/case.json` | case_id、output_contract（期望的 result.json 字段）、材料/模板定位、audience/时长/页数约束 |
| 输入 | `/input/task.md` | 任务说明（存在时读取） |
| 工作 | `/app/work` | 中间产物：PDF 抽取文本、图片、deck-spec.json |
| 输出 | `/app/output` | `result.json`、`academic_deck.pptx`、`preview-approx-*.png`、`evidence_mapping.md`、`evidence_map.json`、`chart-*.png/.svg` 等 |

**自定位（重要）**：本 Skill 的资源以 **SKILL.md 所在目录**为根，记作 `$SKILL_DIR`；
所有脚本用 `os.path.dirname(os.path.abspath(__file__))` 解析自身位置，
**因此从任意 cwd 调用都能跑**，命令里一律写 `"$SKILL_DIR/scripts/xxx.py"`：

```bash
SKILL_DIR="<SKILL.md 所在目录>"       # 平台安装到 /skills/weekly-skill 时即该路径
python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json
```

若运行时输入不在 `/input`，先探测环境变量（如 `CASE_PATH` / `OUTPUT_DIR`）或
cwd 中的 `case.json`，**以实际可读文件为准**，不要假设未实现的路径。

## 3. 资源清单（$SKILL_DIR）

| 文件 | 作用 |
|-|-|
| `scripts/main.py` | 端到端编排：CP1 lint → 材料抽取 → 构建 → 预览 → 导出检查 → result.json |
| `scripts/assetkit.py` | **素材层**：材料定位、PDF 文本/图片实际抽取、从表格数字重建图（PNG+SVG） |
| `scripts/deckgen.py` | **生成层**：模板适配 + 页级排版 + 备注 + 证据映射页 + 形状命名 |
| `scripts/ooxml_kit.py` | **OOXML 层**：主题字体注入、形状分层命名、OOXML zip/XML 健全检查、命名审计 |
| `scripts/spec_lint.py` | **CP1 lint**：deck-spec 结构校验（claim / evidence / BL-1…BL-4） |
| `scripts/preview.py` | PIL 近似预览（并保留 `make_chart` 兼容再导出） |
| `scripts/export_check.py` | **CP3 导出检查器**：契约回显 + OOXML 容器 + 命名 + 证据表一致性（G1–G8） |
| `scripts/check_contract.py` | 契约字段覆盖核对：从 `references/OUTPUT_CONTRACT.md` §1 读字段清单，逐条比对 result.json |
| `scripts/make_template.py` | **运行时生成**回退模板 `.pptx`（包内不携带任何二进制模板）；缺 python-pptx 时如实降级 |
| `scripts/make_synthetic_inputs.py` | **运行时生成**合成夹具（几何占位图 + 两页 ASCII PDF），供自测 PDF/嵌图链路 |
| `scripts/cli_io.py` | 控制台加固：把 stdout/stderr 切到 UTF-8 + `errors="replace"`，避免非 UTF-8 环境下打印中文日志把成功的一轮变成崩溃 |
| `references/OUTPUT_CONTRACT.md` | result.json 顶层字段清单 + 四形态回显 + 硬性门 G1–G8（**必读**） |
| `references/slide-blueprint.md` | 论文→页面蓝图映射 + deck-spec schema + 逐页证据映射表格式 |
| `references/RUBRIC_MAP.md` | 五维评分（40/25/15/10/10）→ 本包落点映射 + 对照协议（交付前逐条自评） |
| `references/failure-modes.md` | 失败模式与降级策略 + 脚本退出码语义（材料/模板/依赖/契约/状态一致性） |
| `references/layer-naming.md` | PPTX 分层命名规范（对象名 = 可编辑性的机器可查证据） |
| `examples/` | 最小示例（合成案例，标注"示例，非正式案例"）；见 `examples/README.md` |

依赖（Python）：`python-pptx` 必需；`Pillow` 用于预览；`matplotlib` 可选（重建图）；
`PyMuPDF` / `pypdf` / `pdfplumber` 任选其一即支持 PDF 解析（无则用运行时自带 PDF
读取导出文本后传入）。脚本逐级回退并如实记录（详见 `references/failure-modes.md` §2.3）。

## 4. 执行步骤（S0–S6，含检查点 CP1–CP3）

### S0 定位与读题
1. 读取 `task.md`（若存在）与 `/input/case.json`，记录 `case_id`。
2. 解析 `case.json`：`output_contract`（必须回显到 result.json 的全部字段）、
   材料路径、模板路径、`audience/duration_minutes/slide_count`。
3. 定位 `$SKILL_DIR`；所有脚本用绝对路径调用（脚本内部自定位，不依赖 cwd）。

### S1 读实际文件（不许假设内容）
4. 抽取论文材料：
   ```bash
   python "$SKILL_DIR/scripts/assetkit.py" --pdf "<材料路径>" --out /app/work/extract
   ```
   - PDF → 页标记文本（`[PAGE n]`）+ 图片（`fig-p<页>-<序号>.png`）+ 抽取报告；
   - 文本/LaTeX → 直接读取；PDF 加密/扫描件/无 PDF 库 → 用自带 PDF 读取转出
     文本（`.txt` 回退），**如实记录工具**；仍不可读 → 按 `failure-modes.md` §2.1 处理。
5. 通读抽取文本，记录元信息（标题/作者/venue）与各章页码。

### S2 蓝图规划（页面蓝图 → deck-spec）
6. 按 `references/slide-blueprint.md` §1 的映射表，把论文结构重写为页面骨架：
   问题（P）→ 方法（M）→ 证据（E）→ 结论（C）→ 局限（L）。
7. 抽**页级证据**：每张图/表/公式/关键结论的编号、所在页码、图注或必要说明、
   数值与单位（数字、单位、方法名**逐字**从原文带出，绝不改写）。
8. 区分：论文原生图 vs 可从表格数字重建的图（reconstructed_chart）；
   **示意图不是实验数据**，不得混称。

### S3 写 deck-spec.json（页级大纲）+ **CP1 lint**
9. 按 `references/slide-blueprint.md` §3 schema 编写 `/app/work/deck-spec.json`：
   - 每页：`claim` + 短语化 `bullets`（≤6 条、CJK 加权 ≤110 字）+ `figure/table`
     （ref 与论文一致）+ `notes`（过渡/强调/被问补充，**不复制页面文字**）
     + `evidence`（ref + page + quote）；
   - 无法定位证据的页 → `evidence_gap: true`（显式标注，不许假装有证据）；
   - `constraints.template_path` 指向组织方模板（案例材料中找到时）。
10. **CP1 检查点**（写完后、生成前必跑）：
    ```bash
    python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json
    # {"valid": true} 才视为蓝图合规；有偏差 → 按 D4 决策后继续并在 result.json 记录
    ```

### S4 构建可编辑源（.pptx，assetkit→deckgen→ooxml_kit）
11. 运行端到端入口：
    ```bash
    python "$SKILL_DIR/scripts/main.py" \
      --case /input/case.json --task /input/task.md \
      --spec /app/work/deck-spec.json --out /app/output
    ```
    `main.py` 依次：CP1 lint（内嵌执行）→ 读 case → 定位材料/模板 → assetkit 抽取
    → deckgen 构建（组织方模板 placeholder-fill-only，或内置 16:9 学术版式；
    对象按 `layer-naming.md` 命名；主题字体注入）→ 备注写入 notes_slide
    （含封面/收尾页）→ 证据映射页与双形态证据映射 → assetkit 重建图（PNG+SVG）
    → PIL 近似预览 → 组装 result.json → CP3 自检 → 打印摘要。
12. 模板适配遵守 `references/slide-blueprint.md` §4 三铁律：
    只填占位符、不碰 master、布局按名匹配→索引回退→内置版式。
    模板为起始演示时，`constraints.template_mode="replace"` 移除起始页仅留版式/母版
    （记录 `starter_slides_removed`），默认 `"layouts"` 保留。
    页数受 `slide_count` 约束：超限 `deck.page_budget_met=false` 且写 uncertainty
    （按 D7 合并/精简处置，绝不静默丢弃证据页）。
13. 案例未提供模板（或模板文件不存在）时：直接用内置版式继续，
    `deck.template.kind="builtin"`，并在 `uncertainty` 说明——这是正常分支。
    需要一份可用的示例模板时运行：
    ```bash
    python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"
    ```

### S5 导出渲染与验证（**CP3 导出检查**）
14. 无 PowerPoint/LibreOffice 时预览为 **PIL 近似**（`preview-approx-*.png`），
    文件名与 `run_meta.rendered_with` 均如实标注；若有 LibreOffice：
    `soffice --headless --convert-to pdf ...` 生成真 PDF 放进 `previews/` 并改写记录。
15. 用 python-pptx 重开 deck，核对页数、标题序列、备注存在、图表编号与 evidence 一致。
16. **CP3 导出检查**（交付门，G1–G8 见 `OUTPUT_CONTRACT.md` §5）：
    ```bash
    python "$SKILL_DIR/scripts/export_check.py" --result /app/output/result.json \
      --out-dir /app/output --case /input/case.json
    # {"valid": true} 且 exit 0 才算通过；warnings 择要处理或如实保留
    ```

### S6 写 result.json + 按 RUBRIC_MAP 自评
17. 结果含：`case_id`（与 case.json 逐字一致）、`status`（completed/partial/failed
    诚实词汇）、`output_contract` 四形态回显（禁止 null）、`deck`（含 template
    guard / overflow_guard / auto_slides / theme_fonts）、`spec_lint`、双形态
    `evidence_mapping`、`previews`、`charts`、`sources`、`uncertainty`、
    `change_records`、`run_meta`（含 rendered_with / skill_version / checkpoints /
    self_check）。字段清单以 `references/OUTPUT_CONTRACT.md` §1 为准，并跑：
    ```bash
    python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
      --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case /input/case.json
    ```
18. 交付前按 `references/RUBRIC_MAP.md` 自评五维覆盖，补足可复跑证据
    （测试记录 → TEST.md，示例 → examples/）。
19. 诚实性硬约束：不编造科学数据；数值/单位不改写；图缺失=显式占位框；
    预览近似如实标注；每步改动进 change_records。

预算纪律：总 64 次模型请求 / 900 秒 / 单响应 16384 tokens（含推理）。先 S1–S3
产出中间件，再逐段增量交付；脚本运行本身秒级，不消耗模型预算大头。

## 5. 决策规则（D1–D11；覆盖材料异常 / 模板异常 / 契约形态 / 状态一致性）

| # | 情形 | 决策（做什么 → 记录在哪） |
|-|-|-|
| D1 | 材料缺失/路径不存在 | 不补造；仅产出元信息 result，deck 不构建 → status=failed；`sources.reason` |
| D2 | PDF 加密 | 空口令试一次；失败用自带读取/用户补充，如实说明 → status=partial/failed；uncertainty+sources.tool |
| D3 | PDF 无文本层（扫描件） | 不 OCR 冒充；标注"图像型 PDF"，有图仍可引用 → uncertainty + sources.tool |
| D4 | **CP1 lint 有偏差**（如 bullet 超限、evidence 缺失未标 gap） | 先修正 spec；确属案例硬性约束无法满足 → 构建继续但**显式记录偏差**，状态降 partial → result.spec_lint + uncertainty |
| D5 | 图/表抽不出 | 页面保留**显式占位框**（标注"需补齐，非原图"），不伪造 → figure.placed=placeholder + uncertainty |
| D6 | 模板不可用/损坏/占位符不足 | 内置学术版式回退；模板模式下绝不添加冲突对象 → deck.template.guard + layouts_used + uncertainty |
| D7 | 页数超限 | 合并/精简并记录；绝不静默丢弃证据页（优先合并非证据页）→ change_records + uncertainty + page_budget_met=false |
| D8 | 字体缺失 | PIL default 字体继续预览，字体来源如实记录；.pptx 内 latin+ea 双写缓解换机替换 → run_meta.preview_font + uncertainty |
| D9 | 重建图失败（无 matplotlib 等） | 跳过图，保留引用与占位 → charts[].chart.reason + uncertainty |
| D10 | 契约字段未知/无值 | 按四形态给类型对应空值 `""/[]/{}`，**禁止 null**；语义字段取本次运行真实值 → result 顶层回显 |
| D11 | 模板文件不存在 / 需现场生成资源 | 不阻断：先回退内置版式继续；确实需要模板或合成夹具时跑 `make_template.py` / `make_synthetic_inputs.py`（均为运行时生成，退出码 2=后端不可用） → deck.template.kind + uncertainty |

## 6. 异常处理表（与 D 规则、`references/failure-modes.md` 配套）

| 异常 | 识别 | 处置 | 记录 |
|-|-|-|-|
| 材料缺失 | case 指向的文件不存在 | D1 | status=failed，sources.reason |
| PDF 加密 | 抽取失败且报 encrypted | D2 | status=partial/failed，uncertainty |
| PDF 无文本层 | 文本抽取为空 | D3 | uncertainty + sources.tool |
| 图/表抽不出 | images 为空或损坏 | D5 | figure.placed=placeholder |
| 模板不可用/损坏 | open 失败 | D6 | deck.template.guard |
| 模板占位符不足 | 无 title/body/picture 占位符 | D6 | layouts_used + uncertainty |
| 模板文件不存在 | 需要模板但未生成 | D11 | deck.template.kind=builtin + uncertainty |
| 字体缺失 | 预览字体回退 default | D8 | run_meta.preview_font |
| 页数超限 | spec.slides > 约束 | D7 | change_records + uncertainty |
| 重建图失败 | chart reason 字段 | D9 | charts[].chart.reason |
| spec 缺失 | `--spec` 无可读文件 | 仅 `--demo` 允许骨架（标 skeleton）；正式运行必须由 Agent 写真实 spec | spec_source |
| 契约字段缺失 | check_contract 退出码 1 | 按 D10 补回显后重跑 | check_contract.missing |

被降级的任何步骤都必须把"发生了什么 + 影响"写进 result.json 的
`uncertainty` / `change_records`，并在最终回复中说明限制。

## 7. 自查清单（交付前逐条）

- [ ] 已读取真实 case.json / task.md / 论文文件，无内容来自标签假设；
- [ ] deck-spec 按蓝图规划（slide-blueprint §1），每页有 claim；bullets 短语且
      ≤6 条；evidence 或 evidence_gap 二选一；**cp1_spec_lint 通过或偏差已记录**；
- [ ] 页上数字/单位/方法名/图号与论文逐字一致（抽查 3 处以上）；
- [ ] 页序可讲：问题→方法→证据→结论→局限；无"段落切片"页；
- [ ] notes 与页面文字分离，notes_slide 已写入（含封面/收尾页，notes_separated=true）；
- [ ] 组织方模板：占位符填充、master 未动、页脚未覆盖；否则 template.guard 注明回退；
- [ ] /app/output 内存在：result.json（全部 output_contract 字段 + case_id）、
      academic_deck.pptx（可编辑、对象已命名）、preview-approx-*.png（或 PDF）、
      evidence_mapping.md + evidence_map.json；
- [ ] `export_check.py` 输出 valid=true 且 exit 0（G1–G8 全过）；
- [ ] `check_contract.py` exit 0（契约顶层字段全覆盖，无 null）；
- [ ] status/uncertainty/change_records 诚实，无编造软件状态或科学数据；
- [ ] 已按 RUBRIC_MAP 五维逐条自评并补足可复跑证据。

## 8. 限制（如实声明）

- 预览默认是 PIL 近似渲染，不等同于 PowerPoint/LibreOffice 渲染结果；
- PDF 图片抽取依赖 pdf 库可用性与版式，个别图可能只以占位框呈现；
- 模板为"占位符级"适配：复杂智慧型占位符（SmartArt 等）不重排；
- 本 Skill 生成内容与结构，不保证论文结论本身正确（结论以论文为准）；
- 形状命名为"我们添加的对象"级保证：组织方模板自带形状不改名（铁律）；
- 包内**只携带文本资源**（.md/.py/.json/.txt/.csv/.yaml/.yml）；模板、预览、
  示意图等二进制一律**运行时生成**或由案例提供，因此首次运行前需要
  `python-pptx` 才能产出 `.pptx`（缺失时如实降级，见 `failure-modes.md` §2.3）。

## 9. 维护

- 版本：`scripts/main.py` 内 `VERSION`（当前 `2.1.0`）；
- 分层约定：新增素材能力加在 `assetkit.py`，生成逻辑在 `deckgen.py`，OOXML 细节
  在 `ooxml_kit.py`（新对象种类先在 `ooxml_kit.PREFIX_BY_KIND` 注册命名前缀）；
- 新增失败分支必须同时更新 `references/failure-modes.md`（识别/处置/记录/退出码）；
- 修改记录维护在 result.json `change_records` 与 git 提交历史；
- 新案例可新增 `examples/` 下的最小示例（标注"示例，非正式案例"）验证接口。

---

## 附:本版增量 —— 契约四形态 × 边界值矩阵（CP4）

本题的评分产物只有一个：`result.json`。它的字段不是「爱写不写」，而是案例 `case.json` 里
`output_contract` **声明**出来的四种形态之一（① 字段→类型提示 / ② 字段→说明 / ③ 布尔开关 /
④ 字段名称清单，外加「整个容器非法」这一情形）。声明形态与边界值一旦踩到边角（空串、空数组、`0`、
超长、非法类型、缺字段），失败往往表现为**静默通过**——流程 exit 0、内部自检说 OK、字段也确实在，
但回显的类型或值已经与声明不是一回事。本章把这件事做成一张**可跑的矩阵**：每种形态 × 每组边界值
各注入一次，跑真实流程，逐行留证。

前文第 1–9 章（阶段 S0–S6、D1–D11、G1–G8、`$SKILL_DIR` 自定位、`--flag` 表）**全部照旧执行**；
本章只把「读契约」这一步做实（M0 抄清单）、并在交付前加一道 CP4 回归网。

```
CP4 契约矩阵            →  CP1 蓝图 lint   →  生成      →  CP3 交付检查
scripts/contract_matrix.py  scripts/spec_lint.py  main.py   scripts/export_check.py
28 个注入单元 × 一次真跑     BL-1…BL-4         三层生成    G1–G8 + 19 字段面
```

### 附.1 增量资源（`$SKILL_DIR`）

| 入口 / 文档 | 作用 | 参数（**全部保留**） |
|-|-|-|
| **`scripts/contract_matrix.py`（本版新增）** | **CP4 契约矩阵**：四形态 × 边界值逐单元注入一份完整 `case.json`，跑真实端到端流程并逐行判定 | `--case` `--spec` `--entry` `--python` `--out` `--only` `--timeout` `--emit-md` `--json` `--before-fix` `--redact-paths` `--quiet` |
| `references/CONTRACT-MATRIX.md` | **本轴说明文档**：28 个单元逐行实测 + 静默通过清单 + 修复登记 + 未覆盖声明（由 `--emit-md` 现场生成，不是手抄表） | — |
| `references/contract-matrix-data.json` | 矩阵实测原始记录（修复后） | — |
| `references/contract-matrix-before-fix.json` | 同一矩阵在**修复前**的对照记录（5 条静默通过的证据） | — |

前文 §3 的 11 个入口**参数表全部保留**；本版新增 1 个可执行入口，并在
`scripts/main.py` 的 `apply_output_contract()` 内做 3 处**纯增量**修复（逐条见附.4 / 附.5），
**CLI 参数名、默认值与退出码语义均未改动**，其余 10 个脚本逐字节不变。
矩阵本身是纯标准库实现（复用 `scripts/check_contract.py` 读契约字段清单，文档改了矩阵跟着改）。

### 附.2 运行命令与判定三分（CP4）

```bash
SKILL_DIR="<SKILL.md 所在目录>"       # 平台安装到 /skills/weekly-skill 时即该路径
python "$SKILL_DIR/scripts/contract_matrix.py" --out "<探针目录>" \
  --emit-md "<探针目录>/CONTRACT-MATRIX.md"
# exit 0 = 每个单元都写出 result.json 且没有静默通过；exit 1 = 有静默通过（必须先处理）
```

每个单元 = 一份完整的 `case.json`（只改 `output_contract`）+ 一次**未经修改的**端到端真跑；
逐行记录 `exit` / `status` / 契约回显 / 是否被记录。判定只有三档：

| 判定 | 含义 | 处置 |
|-|-|-|
| `match` | 回显与声明的形态、值一致 | 交付 |
| `mismatch-recorded` | 不一致但**被记录**（写进 `uncertainty`）或**被门拦住**（`check_contract` / 内置自检报问题） | 交付，并在说明里点出是「记录」还是「拦下」 |
| `silent-pass` | 既没纠正、也没记录 | **未定级契约缺陷**，必须先修或先记录（P01） |

回归时用 `--only A04,A11` 只跑指定单元；随包入库时用 `--redact-paths` 把本机绝对路径换成占位符。

### 附.3 本轴决策规则 P01–P12（契约形态 / 材料 / 模板 / 依赖 / 状态）

| # | 情形 | 决策（做什么 → 记录在哪） |
|-|-|-|
| P01 | 矩阵报出 `silent-pass` | 视为**未定级契约缺陷**：按单元里的「期望 vs 实测」改代码或改成如实记录（二选一，不许放着） → 重跑矩阵 + `references/CONTRACT-MATRIX.md` §5 增一条 |
| P02 | 声明值是**布尔**且字段名不是语义字段 | 如实回显声明的布尔（true→true、false→false），不得回退成空串或取反 → `result.<field>` |
| P03 | 声明值是**数字**（含边界 0） | 如实回显数字，不塌缩成空串 → `result.<field>` |
| P04 | 声明值是 `null` / 非法类型 | 顶层**禁止出现 null**（D10 口径）：给容器空值，并在 `uncertainty` 记录「声明的值本身是 null」 → `result.output_contract` + `uncertainty` |
| P05 | `output_contract` **整个容器非法**（字符串/数字）或显式 `null` | 回显空对象 + **写一条 uncertainty**（不得静默当空契约）；顶层 19 字段仍须齐全，否则自检会点名 → `uncertainty` + 门 |
| P06 | ④ 清单形态里混入非字符串元素 | 跳过该元素但**写一条 uncertainty**（不得静默丢弃） → `uncertainty` |
| P07 | 声明「不全」（只声明了少数字段） | 顶层 19 字段的完整性**不能依赖案例声明**：缺失时自检会报 `output contract fields missing` 并 exit 1，此时要么补回显、要么在 uncertainty 说明 → `run_meta.self_check.problems` |
| P08 | 声明字段与真实键同名（`status`/`deck`/`title`…） | **真实值优先**：`setdefault` 语义，声明不得覆盖运行结果 → 矩阵单元 A09/A10/D04 |
| P09 | 材料缺失 / PDF 加密 / 无文本层 | 不补造；`status=failed` 或 `partial`，并如实记录工具与原因 → `sources` + `uncertainty` |
| P10 | 模板不可用/损坏/占位符不足/文件不存在 | 内置 16:9 学术版式回退；需要模板时跑 `make_template.py`（退出码 2 = 后端不可用） → `deck.template.kind` + `uncertainty` |
| P11 | 依赖缺失（matplotlib / PDF 库 / 字体） | 逐级回退并如实记录：重建图跳过、PDF 转文本、字体回退 default；不得伪造产物 → `charts[].chart.reason` + `run_meta` |
| P12 | 状态一致性 | `completed` 只允许「材料可读 + deck 生成 + 预览生成 + 无未标注缺口 + CP1 通过 + **契约面完整**」；任一降级即 `partial`/`failed` → `status` + `uncertainty` |

被降级的任何步骤都必须把「发生了什么 + 影响」写进 `uncertainty` / `change_records`。

### 附.4 本版实测数字（CP4，可复核）

| 判据 | 实测（28 个注入单元，示例案例为基座） | 复核命令 |
|-|-|-|
| 单元数 / 形态覆盖 | 28 个：① ×14、② ×2、③ ×1、④ ×6、契约容器 ×5 | `contract_matrix.py --out <dir>` |
| 写出 `result.json` | **28/28**（0 崩溃） | 同上报告 `summary.result_written` |
| exit 0 的单元 | **23/28**；5 个「声明不全/非法容器」单元 exit 1，被内部契约门点名 | 同上 `summary.exit_zero` / `caught_by_gate` |
| 契约回显符合期望 | 修复前 21/28 → **修复后 28/28** | `contract-matrix-data.json` vs `contract-matrix-before-fix.json` |
| **静默通过** | 修复前 **5 条** → 修复后 **0 条** | 两份报告的 `summary.silent_pass` |
| 修复前 5 条是什么 | A04 声明 `0` 回显 `""`；A11 声明 `true` 回显 `false`；A12 声明 `false` 回显 `""`；B02 声明 `123` 回显 `""`；D03 清单里的 `7`/`null` 被静默丢弃 | `CONTRACT-MATRIX.md` §3 |
| 顶层契约面（19 字段） | 23/28 完整；5 个「声明不全」单元不完整**且被门点名**（不是静默） | 报告 `contract_surface_complete` |
| ④ 清单形态对语义字段的影响 | `title`/`slides` 等回显为 `[]`（清单形态无法表达语义值），逐单元记录 | 报告 `semantic_echo_in_list_form` |
| 矩阵耗时 | 28 个单元约 **50 s**（每单元一次真跑） | 命令自带计时 |

数字来源即本包内的两份机器可读报告 `references/contract-matrix-data.json`（修复后）与
`references/contract-matrix-before-fix.json`（修复前对照），逐单元可复核。

### 附.5 静默通过清单与修复登记要点

- **修复前 5 条静默通过**（每一条都是「声明了一种形态，回显成了另一种」）：
  ① A04 声明 `0`（数字）→ 回显 `""`；② A11 声明 `true` → 回显 `false`（取反）；
  ③ A12 声明 `false` → 回显 `""`；④ B02 声明 `123` → 回显 `""`；
  ⑤ D03 ④ 清单里的非法元素 `7` / `null` 被**静默丢弃**（既没跳过说明，也没写 uncertainty）。
- **3 处纯增量修复**（都在 `main.py: apply_output_contract()` 内，不改参数与退出码）：
  ① 未知布尔字段如实回显声明值；② 数值型声明如实回显（不塌缩成空串）；
  ③ 非法元素与非法容器写入 `uncertainty`（而不是静默忽略）。逐条含风险说明见
  `references/CONTRACT-MATRIX.md` §5 与 `TEST.md` T5。
- **「期望」的两个来源**：文档明文（`OUTPUT_CONTRACT.md` §1/§5）+ 文档未明文时的「类型忠实」推定；
  推定项在 `CONTRACT-MATRIX.md` §0 与逐行 note 里标注，**不把推定当明文**。
- **不完整但不是静默**：5 个「声明不全 / 容器非法」单元的顶层契约面不完整，但被内部契约门
  **点名**（exit 1 + `run_meta.self_check.problems`），因此归入 `mismatch-recorded` 而不是 `silent-pass`。

### 附.6 与基线各章、各编号的对应（照此行解读包内引用）

- 前文 §4 的阶段 S0–S6 与检查点 CP1 / CP3 顺序未变；CP4 是「交付前的契约回归网」，
  不替代 CP1 / CP3，也不改变生成逻辑。
- 前文 §5 的 D1–D11 语义未变，本章 P 编号与之对应：**P04 = D10**、**P09 = D1/D2/D3**、
  **P10 = D6/D11**、**P11 = D8/D9**；**P01 / P02 / P03 / P05 / P06 / P07 / P08 / P12
  为本轴新增或细化**（契约边界值、契约容器非法、声明不全、语义键优先、契约面完整性）。
- 包内 `README.md` / `TEST.md` / `references/*.md` 中提到的「`SKILL.md` §4（M0–M6，CP1 / CP3 / CP4）」
  与「§5（决策规则 P01–P12）」，在本版中分别指前文 §4 的阶段划分与**本章附.3 的 P 规则表**；
  提到的「§3 参数表」中 `contract_matrix.py` 一行即本章附.1 的表格。
- 前文 §4 的 S0「定位与读题」在本轴下应多做一步：**先把 `output_contract` 抄成一张清单**
  （字段名 + 声明形态 + 声明值本身），后面逐字段核对的对象就是它——这一步不做，矩阵就没有比对基准。

### 附.7 限制与口径边界（本轴）

- 矩阵只覆盖 `output_contract` **一个契约面**；页级结构、模板、字体、页数上限分别由
  `spec_lint` / `export_check` 负责，**未覆盖项逐条列在 `CONTRACT-MATRIX.md` §6**。
- 矩阵的期望值不是凭空写的：文档明文 + 类型忠实推定，推定项已逐行标注（附.5 第三条）。
- 契约矩阵是**回归网**：改 `apply_output_contract()` 或新增形态时必须重跑，否则它的结论会过期。
- 预览为 PIL 近似渲染，`charts[].chart.file` 携带输出目录绝对路径（已知限制）；
  模板适配为「占位符级」，不重排 SmartArt。

### 附.8 维护（改什么就重跑什么）

| 改动 | 必须重跑 |
|-|-|
| `main.py: apply_output_contract()`（或任何影响 result.json 的改动） | `contract_matrix.py`（矩阵是本轴的回归网）+ `export_check` + `check_contract` |
| 新增 `output_contract` 形态或边界值 | 在 `contract_matrix.py` 的 `CELLS` 加一行（含 `expect`），重跑并把新结果写回 `CONTRACT-MATRIX.md` |
| 新增失败分支 | 同步更新 `references/failure-modes.md` 与前文 §5 的 D 规则，并登记到本章附.3 的 P 规则 |
| 版本 | `scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；本版新增 `scripts/contract_matrix.py`，并在 `apply_output_contract()` 内做 3 处纯增量修复（逐条见 `CONTRACT-MATRIX.md` §5） |
