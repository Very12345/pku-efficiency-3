---
name: paper-to-academic-ppt
description: 把论文/研究材料转换成主线清晰、证据可追溯、可编辑的学术汇报 PPT。加载后按"读实际文件→抽主线与证据→蓝图规划 deck-spec→CP1 lint→模板适配生成可编辑 .pptx→渲染预览→导出检查→写带全部 output_contract 字段的 result.json"全流程执行，页级主张、图表编号引用、讲解备注分离生成，缺失证据显式标注、不编造数据，五维评分在 RUBRIC_MAP.md 中逐条自评。Use when a task asks to turn a paper or research material into an academic slide deck (论文转PPT、学术汇报PPT、slides from paper、presentation from paper), especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews. 本版另加一章增量 —— scripts/determinism.py 的 CP0 复现判据在独立进程、不同 cwd 与不同 PYTHONHASHSEED 下连跑多次并逐文件比对 sha256，实测 5 次运行规范化后 13/13 一致、未解释差异 0。
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

## 附:本版增量 —— 确定性与字节级可复现（CP0）

同一份论文、同一份模板、同一台机器，连跑两次应当得到**同一份产物**——否则「按记录复跑出同一版式」
这句话就只能靠自述。本章把可复现性做成一条**可执行判据**（CP0），并给出差异分类与稳定化办法。
前文第 1–9 章（阶段 S0–S6、决策规则 D1–D11、交付门 G1–G8、`$SKILL_DIR` 自定位、`--flag` 表）
**全部照旧执行**：本章只在写 deck-spec 之前加一道前置探测、在交付之前加一次复跑，
不改任何既有命令、参数名、默认值与退出码语义。

```
CP0 复现判据        →  CP1 结构判据     →  生成      →  CP3 交付判据
scripts/determinism.py  scripts/spec_lint.py  main.py    scripts/export_check.py
跨进程 / 跨 cwd / 跨 seed   BL-1…BL-4          三层生成    G1–G8
逐文件 sha256 + 白名单分类
```

### 附.1 增量资源（`$SKILL_DIR`）

| 入口 / 文档 | 作用 | 参数（**全部保留**） |
|-|-|-|
| **`scripts/determinism.py`（本版新增）** | **CP0 复现判据**：跨进程 / 跨 cwd / 跨 `PYTHONHASHSEED` 连跑 N 次，逐文件 sha256 比对与白名单分类 | `--case` `--spec` `--task` `--out` `--runs` `--out-mode` `--svg-hashsalt` `--python` `--entry` `--seeds` `--timeout` `--stabilize` `--no-timestamp` `--redact-paths` `--json` `--quiet` |
| `references/DETERMINISM.md` | **本轴说明文档**：逐字段说明哪些字节**故意**不稳定、如何稳定化、实测表（§3 差异分类、§4 场景 A–E） | — |
| `references/determinism_report.json` | CP0 的实测报告（默认模式，5 次运行；路径已脱敏） | — |
| `references/determinism_report-hashsalt.json` | 同一探测在固定 `svg.hashsalt` 下的对照报告（证明 SVG 随机元素 id 的来源） | — |

前文 §3 的 11 个入口**一个都没有改**（`deckgen` / `ooxml_kit` / `preview` / `cli_io` 仍是库模块
+ 各自的 `__main__`），本版唯一的可执行新增就是 `determinism.py`；它同样把脚本目录插进
`sys.path`、用 `os.path.dirname(os.path.abspath(__file__))` 自定位，因此从任意 cwd 调用都能跑。

### 附.2 运行命令与三级判定（CP0）

```bash
SKILL_DIR="<SKILL.md 所在目录>"       # 平台安装到 /skills/weekly-skill 时即该路径
python "$SKILL_DIR/scripts/determinism.py" --out "<探针目录>" --runs 5 --stabilize
# exit 0 = 规范化后 13/13 一致且未解释差异 0；exit 1 = 有未解释差异（不允许直接交付）
```

它在**独立进程**、**不同 cwd**、**不同 `PYTHONHASHSEED`**（默认三档种子轮换）下连跑主流程，
对全部产物逐文件比对 sha256，并把结论分成三级 + 一类必须处置的差异：

| 判定 | 含义 | 处置 |
|-|-|-|
| `identical`（原始字节） | 所有产物字节一致 | 直接交付 |
| `identical_canonical`（规范化后） | 把已解释字段按类别规范化后一致 | 交付，并在最终回复里说明哪些字节故意不稳定 |
| `identical_stabilized`（稳定化后） | 探针物理重写不稳定部分后的副本一致 | 需要分发稳定副本时取 `stabilized/run-0/`（R02） |
| `unexplained_diffs` 非空 | 既不在白名单里、也说不出根因 | **视为未定级缺陷**，按 R01 处理后再交付 |

**白名单是写死在代码里的常量**（会自动吸收差异的探针等于没有判据）：报告里出现的每一个不稳定字段
都必须能在 `references/DETERMINISM.md` §3 的实测表里找到对应行，**不允许「发现了但没解释」**。
探针子进程带 `PYTHONDONTWRITEBYTECODE=1`，探测过程不会在包内留下 `__pycache__`。

### 附.3 本轴决策规则 R01–R12（覆盖**可复现 / 材料 / 模板 / 依赖 / 契约 / 状态**六类）

| # | 情形 | 决策（做什么 → 记录在哪） |
|-|-|-|
| R01 | CP0 报出 `unexplained_diffs` 非空 | 视为**未定级缺陷**：先定位差异文件与字段（报告里已给 pointer/观测值），修掉或给出白名单证据后再交付；绝不改判为「已解释」 → `references/DETERMINISM.md` §3 新增一行 + TEST.md |
| R02 | 交付物需要跨机对拍 | 用同一个 `--out` 复跑；需要分发稳定副本时取 `--stabilize` 产出的 `stabilized/run-0/`（实测稳定化后 13/13 字节一致） → 报告 `stabilized.dir` |
| R03 | `result.json` 里出现本机输出路径（`charts[].chart.file`） | 已知限制：它是 `out-dir identity`（值随 `--out` 变）；跨机对比时按 R02 用同一 `--out`，或在报告里按类别接受 → `volatile_fields[]` 的 `out-dir-identity` 行 |
| R04 | **CP1 lint 有偏差** | 先修 spec；确属案例硬约束无法满足 → 继续构建但显式记录偏差、status 降 `partial` → `result.spec_lint` + `uncertainty` |
| R05 | 材料缺失/路径不存在 | 不补造；仅产出元信息 result，deck 不构建 → `status=failed`；`sources.reason` |
| R06 | PDF 加密 / 无文本层（扫描件） | 空口令试一次；不 OCR 冒充；标注「图像型 PDF」，有图仍可引用 → `uncertainty` + `sources.tool` |
| R07 | 图/表抽不出；页数超限 | 保留**显式占位框**（标注「需补齐，非原图」）；超限先合并非证据页并记录，绝不静默丢证据页 → `figure.placed=placeholder` / `page_budget_met=false` + `change_records` |
| R08 | 模板不可用/损坏/占位符不足/文件不存在 | 内置学术版式回退，不添加冲突对象；需要模板或夹具时跑 `make_template.py` / `make_synthetic_inputs.py`（退出码 2 = 后端不可用） → `deck.template.guard` / `kind` + `uncertainty` |
| R09 | 依赖缺失（matplotlib / PDF 库 / 字体 / PIL） | 逐级回退并如实记录：重建图跳过（`charts[].chart.reason`）、PDF 转文本、预览字体回退 default；**不得伪造产物** → `uncertainty` + `run_meta` |
| R10 | 契约字段未知/无值 | 四形态按类型给 `""`/`[]`/`{}`，**禁止 null**；语义字段取本次运行真实值 → result 顶层回显（`check_contract.py` exit 0） |
| R11 | 状态一致性（status 与产物不符） | `completed` 只允许「材料可读 + deck 生成 + 预览生成 + 无未标注缺口 + CP1 通过」；任一降级即 `partial`/`failed`，**不允许把 partial 说成 completed** → `status` + `uncertainty` |
| R12 | 探针本身可疑（怀疑「永远说 OK」） | 换一个会写随机数的 `--entry` 跑阴性对照：应报 `unexplained_diffs` 且退出码 1（实测见 `DETERMINISM.md` §4 场景 E） → `determinism_report.json` |

被降级的任何步骤都必须把「发生了什么 + 影响」写进 `uncertainty` / `change_records`，
并在最终回复里说明限制。

### 附.4 本版实测数字（CP0，可复核）

| 判据 | 实测（示例案例，5 次运行） | 复核命令 |
|-|-|-|
| 原始字节一致 | `identical = False`；13 个产物中 10 个字节一致，3 个含故意不稳定字节（`.pptx` / `.svg` / `result.json`） | `--runs 5 --stabilize` 报告的 `byte_identical_per_file` |
| 规范化后一致 | `identical_canonical = True`（13/13） | 同上 `canonical_identical_per_file` |
| 稳定化后字节一致 | `identical_stabilized = True`（13/13，稳定化副本 5/5 相同） | 同上 `stabilized.identical` |
| 未解释差异 | `0` | 同上 `unexplained_diffs` |
| 已解释字段 | 5 条 JSON 指针（2×`change_records[].time`、`run_meta.timestamp`、`run_meta.duration_seconds`、`charts[0].chart.file`） | 同上 `volatile_fields[]` |
| zip 成员载荷 | 一致（差异只在成员 mtime） | 同上 `volatile_files[]` 的 `member_payloads_identical` |
| SVG 元素 id | 默认 83 个 id、12 个位置逐次不同；`--svg-hashsalt v7-fixed` 后 **0 个位置不同** | `references/determinism_report-hashsalt.json` 的 `svg_id_sequences_stable` |
| 探针自证 | 两次独立探测的 `per_file_canonical_sha256` 完全相同 | `DETERMINISM.md` §4 场景 D |
| 阴性对照 | 换成写随机数的入口 → 退出码 1 + `/roll` 入 `unexplained_diffs` | `DETERMINISM.md` §4 场景 E |

数字来源即本包内的机器可读报告 `references/determinism_report.json` 与
`references/determinism_report-hashsalt.json`（逐条可复核，未做任何人工改写）。

### 附.5 易变字段与差异分类要点（照此登记，不要临时改判）

- **5 条 JSON 指针**：`change_records[].time`（2 条）、`run_meta.timestamp`、
  `run_meta.duration_seconds`、`charts[0].chart.file`——前四条是时间/时长，最后一条是
  输出目录身份（`out-dir-identity`，值随 `--out` 变）。
- **`.pptx` 容器**：zip 成员 mtime 每次不同，但**成员载荷逐个一致**
  （`member_payloads_identical = true`）；稳定化时把成员 `date_time` 固定即可。
- **`.svg`（重建图）**：`<dc:date>` 写入渲染时刻；**元素 id 默认随机**——`matplotlib` 的 SVG
  id 由 `svg.hashsalt` 派生，默认每次渲染都不同（实测默认 83 个 id、12 个位置逐次不同；
  固定 `--svg-hashsalt` 后 0 个位置不同）。稳定化按文档顺序重命名 id。
- **输出目录身份**：`charts[].chart.file` 携带 `--out` 的绝对路径；跨机对拍用同一个 `--out`（R02/R03）。
- **分类只有两类**：已解释（写死在 `determinism.py` 白名单里的类别 + 观测值）/ 未解释（退出码 1）。
  新增会写时间戳、时长或随机值的产物时，必须**同时**更新白名单与 `DETERMINISM.md` §3，
  否则下一次 CP0 会以「未解释差异」正确地把它拦下来。

### 附.6 与基线各章、各编号的对应（照此行解读包内引用）

- 前文 §4 的阶段 S0–S6 与检查点 CP1 / CP3 顺序未变；CP0 是「生成之前的前置探测 + 交付之前的复跑」，
  不替代 CP1 / CP3。
- 前文 §5 的 D1–D11 语义未变，本章 R 编号与之对应：**R04 = D4**、**R05 = D1**、**R06 = D2/D3**、
  **R07 = D5/D7**、**R08 = D6/D11**、**R09 = D8/D9**、**R10 = D10**、
  **R11 = 状态一致性约束**（前文 §7 自查清单里的同一条）；**R01 / R02 / R03 / R12 为本轴新增**
  （分别对应未解释差异、稳定副本、输出目录身份、探针阴性对照）。
- 包内 `README.md` / `TEST.md` / `references/*.md` 中提到的「`SKILL.md` §4（W0–W6，CP0 / CP1 / CP3）」
  与「§5（决策规则 R01–R12）」，在本版中分别指前文 §4 的阶段划分与**本章附.3 的 R 规则表**；
  提到的「§3 参数表」中 `determinism.py` 一行即本章附.1 的表格。
- 既有 11 个脚本逐字节未改，CLI 参数名、默认值与退出码语义均未变；本版只新增一个可执行入口
  与 3 个 `references/` 文件。

### 附.7 限制与口径边界（本轴）

- 可复现性的结论限定在「**同一解释器 + 同一压缩库 + 同一平台**」；跨环境只承诺
  「zip 成员载荷一致」这一级（`DETERMINISM.md` §3.2 / §6），不要把它说成「任意机器逐字节相同」。
- 白名单是代码常量而非文档：改代码必须同步改文档，反之亦然（二者漂移会立刻表现为 CP0 失败）。
- 探针测量的是**产物字节**，不判断产物内容是否正确（内容质量由 CP1 / CP3 与 RUBRIC_MAP 负责）。
- `result.json` 的 `charts[].chart.file` 携带输出目录绝对路径，这是已知限制而不是缺陷（R03）。

### 附.8 维护（改什么就重跑什么）

| 改动 | 必须重跑 |
|-|-|
| 任何 `scripts/*.py` | `spec_lint` → `main.py` → `export_check` → `check_contract`，然后 **`determinism.py --runs 5 --stabilize`**（产物字节会变） |
| 新增会写时间戳/随机值的产物 | 同步更新 `DETERMINISM.md` §3 与 `determinism.py` 的白名单（白名单是代码常量，不在文档里） |
| 新增失败分支 | 同步更新 `references/failure-modes.md` 与前文 §5 的 D 规则，并登记到本章附.3 的 R 规则 |
| 版本 | `scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；本版仅新增 `scripts/determinism.py`，既有脚本逐字节未改 |
