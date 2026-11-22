---
name: paper-to-academic-ppt
description: 把论文/研究材料转换成主线清晰、证据可追溯、可编辑的学术汇报 PPT。加载后按"读实际文件→抽主线与证据→蓝图规划 deck-spec→CP1 lint→模板适配生成可编辑 .pptx→渲染预览→导出检查→写带全部 output_contract 字段的 result.json"全流程执行，页级主张、图表编号引用、讲解备注分离生成，缺失证据显式标注、不编造数据，五维评分在 RUBRIC_MAP.md 中逐条自评。Use when a task asks to turn a paper or research material into an academic slide deck (论文转PPT、学术汇报PPT、slides from paper、presentation from paper), especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews.
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
