# 论文转学术 PPT（paper-to-academic-ppt） · 整合版（决策层 + 增益层）

> 本包整合了基线 Skill 与 2 个强化层,各层对应不同的评分维度:可靠体验 10 + 实际效果 40 · 使用增益 25。
> 各层内容**不重复**:决策层给规则与失败分支;增益层给对照协议与指标口径;机制层给机制说明与可复用资产。
> 建议使用顺序:先用「决策层」跑通并处理异常,再用「增益层」证明并度量改善,最后用「机制层」复用与扩展。
> 各层的原始文件都完整保留在本包内,不是摘要 —— 下面每一层都是可以独立执行的完整规范。

## 本包文件索引

- `GITHUB_URL.txt`
- `README.md`
- `TEST.md`
- `examples/EXPECTED-OUTPUT.md`
- `examples/README.md`
- `examples/case.json`
- `examples/deck-spec.json`
- `examples/task.md`
- `references/GAIN-PROTOCOL.md`
- `references/OUTPUT_CONTRACT.md`
- `references/RUBRIC_MAP.md`
- `references/failure-modes.md`
- `references/layer-naming.md`
- `references/slide-blueprint.md`
- `scripts/assetkit.py`
- `scripts/check_contract.py`
- `scripts/cli_io.py`
- `scripts/deckgen.py`
- `scripts/export_check.py`
- `scripts/gain_probe.py`
- `scripts/main.py`
- `scripts/make_synthetic_inputs.py`
- `scripts/make_template.py`
- `scripts/ooxml_kit.py`
- `scripts/preview.py`
- `scripts/spec_lint.py`
- `examples/materials/paper-mini.txt`
- `examples/output/README-EXAMPLE.md`
- `examples/output/evidence_map.example.json`
- `examples/output/evidence_mapping.example.md`
- `examples/output/result.example.json`

---

# 【决策层】决策规则与失败分支（目标维度:可靠体验 10 + 实际效果 40）

---
name: paper-to-academic-ppt
description: 把论文/研究材料转换成主线清晰、证据可追溯、可编辑的学术汇报 PPT。本版把执行路径写成可判定的决策规则 D01–D16 与五类失败分支处置表：遇到材料异常、模板缺失、依赖缺失、契约四形态、状态不一致时，Agent 按"触发条件 → 首选举措 → 失败时的降级 → 记录字段 → 退出码"取用，不靠临场发挥。流程：读 OUTPUT_CONTRACT → 写页级 deck-spec 并过 C1 lint → 模板占位符级适配生成可编辑 .pptx → 重建图与近似预览 → C3 导出检查 → 回显全部 output_contract 字段的 result.json。Use when a task asks to turn a paper or research material into an academic slide deck (论文转PPT、学术汇报PPT、slides from paper、presentation from paper), especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews.
---

## 论文转学术 PPT（决策规则版 · paper-to-academic-ppt）

本 Skill 把"论文内容 → 可讲、可核验、可编辑的学术汇报 PPT"这条链路拆成
**六个阶段（P0–P6）+ 三道检查点（C1–C3）+ 一张决策规则总表（D01–D16）+ 五类失败分支处置表**。
阶段回答"下一步做什么"，决策规则回答"这一步出问题时改成什么"，失败分支表回答
"这一类异常怎么升格处理、写进哪个字段、退出码是几"。三者互为索引，缺一不可。

**本版新增的实质内容**：① 决策规则从"情形→做什么"扩写为四列可判定表（触发条件 /
首选举措 / 降级路径 / 记录与退出码），并由 D01–D16 覆盖到状态不变量；
② 失败分支表按**材料异常 / 模板缺失 / 依赖缺失 / 契约四形态 / 状态不一致**五类
逐条给出升级路径；③ 新增状态一致性不变量 I1–I6，把"什么情况禁止写 completed"
写成可机检的断言。算法与 `scripts/` 的 CLI 接口与本包其它版本完全一致，本版只强化
"判断与降级"的表达。

**不负责**：论文精读结论的生成、科研绘图本身的图形设计、学术写作润色。
**不使用预制答案**：正式运行只依据案例实际提供的文件；`examples/` 只演示接口。

---

### 1. 触发条件与适用边界

满足下列任一条件即加载本 Skill：

- 运行目录存在 `/input/case.json` 与 `/input/task.md`，要求在 `/app/output` 产出演示产物；
- 用户直接要求"把这篇论文做成学术 PPT / slides from this paper / 组会汇报"，
  并提供了论文文件与（可选的）模板。

**适用**：单篇论文或研究报告 → 一份 8–20 页的学术汇报，含页级主张、图表定位、
讲解备注、模板适配与渲染记录。
**不适用**（越界即拒绝并把请求写进 `uncertainty`）：替用户判断论文结论真假、
重画科研图、润色论文正文、生成与材料无关的通用幻灯片。

### 2. 输入 / 输出 / 自定位

| 方向 | 路径（以环境实际挂载为准） | 内容 |
|-|-|-|
| 输入 | `/input/case.json` | `case_id`、`output_contract`、材料/模板定位、`audience`/`duration_minutes`/`slide_count` |
| 输入 | `/input/task.md` | 任务说明（存在时读取；缺失不阻断） |
| 工作 | `/app/work` | 中间产物：抽取文本、图片、`deck-spec.json` |
| 输出 | `/app/output` | `result.json`、`academic_deck.pptx`、`preview-approx-*.png`、`evidence_mapping.md`、`evidence_map.json`、`chart-*.png/.svg` |

**自定位**：本 Skill 的资源根 = `SKILL.md` 所在目录，记作 `$SKILL_DIR`。所有脚本用
`os.path.dirname(os.path.abspath(__file__))` 解析自身位置并 `sys.path.insert` 本目录，
**因此 cwd 不是技能根也能跑**。命令里一律写 `"$SKILL_DIR/scripts/xxx.py"`：

```bash
SKILL_DIR="<SKILL.md 所在目录>"        # 平台安装到 /skills/weekly-skill 时即该路径
python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json
```

运行时若输入不在 `/input`，先探测环境变量（`CASE_PATH` / `OUTPUT_DIR`）或 cwd 下的
`case.json`；**以实际可读文件为准**，不要假设未实现的路径（D14）。

### 3. 资源清单（相对 `$SKILL_DIR`）

| 文件 | 作用 | 独立 CLI |
|-|-|-|
| `scripts/main.py` | 端到端编排：C1 lint → 材料抽取 → 构建 → 预览 → C3 检查 → 写 result.json | `--case --out`（必填） |
| `scripts/assetkit.py` | 素材层：材料定位、PDF 文本/图片抽取、从表格数字重建图（PNG + 可编辑 SVG） | `--pdf --out` |
| `scripts/deckgen.py` | 生成层：模板适配、页级排版、备注、证据映射页、形状命名 | 打印记录 |
| `scripts/ooxml_kit.py` | OOXML 层：主题字体注入、形状命名、zip/XML 健全检查、命名审计 | 传 `.pptx` 打印记录 |
| `scripts/spec_lint.py` | **C1**：deck-spec 结构校验（BL-1…BL-4） | `--spec` |
| `scripts/export_check.py` | **C3**：契约回显 + OOXML 容器 + 命名 + 证据表一致性（G1–G8） | `--result --out-dir [--case]` |
| `scripts/check_contract.py` | 契约字段覆盖核对（直接读 `references/OUTPUT_CONTRACT.md` §1） | `--result --contract [--case]` |
| `scripts/preview.py` | PIL 近似预览（无 Office 引擎时的诚实渲染） | 打印记录 |
| `scripts/make_template.py` | 运行期生成回退模板 `.pptx`（包内不携带二进制模板） | `--out [--name] [--no-starter]` |
| `scripts/make_synthetic_inputs.py` | 运行期生成合成夹具（几何占位图 + 两页 ASCII PDF） | `--out` |
| `scripts/cli_io.py` | 控制台加固：stdout/stderr 切 UTF-8 + `errors="replace"` | 被各入口导入 |
| `references/OUTPUT_CONTRACT.md` | result.json 顶层字段清单 + 四形态回显 + 硬性门 G1–G8（**必读**） | — |
| `references/failure-modes.md` | **本版配套**：五类失败分支的识别/首选/降级/记录/退出码，与 D01–D16 逐条对应 | — |
| `references/slide-blueprint.md` | 论文→页面蓝图映射 + deck-spec schema + 逐页证据表格式 | — |
| `references/RUBRIC_MAP.md` | 五维评分落点 + 可靠体验与决策规则的对应表 | — |
| `references/layer-naming.md` | 分层命名规范（对象名 = 可编辑性的机器可查证据） | — |
| `examples/` | 最小示例（合成案例，标注"示例，非正式案例"） | — |

依赖：`python-pptx` **必需**（否则 `deck=null` 并如实降级）；`Pillow` 用于预览；
`matplotlib` 可选（重建图）；`PyMuPDF`/`pypdf`/`pdfplumber` 任一即可解析 PDF。
逐级回退路径见 §6 与 `references/failure-modes.md` §3。

### 4. 执行阶段 P0–P6（含检查点 C1–C3）

#### P0 定位与读题
1. 读 `task.md`（存在时）与 `/input/case.json`，取出 `case_id`。
2. 解析 `output_contract`（必须回显的全部字段）、材料路径、模板路径、
   `audience/duration_minutes/slide_count`；写进 P3 的 `deck-spec.meta` 与 `constraints`。
3. 定位 `$SKILL_DIR`；所有脚本以绝对路径调用（脚本自定位，不依赖 cwd）。

#### P1 读实际文件（禁止按标签假设内容）
4. 抽取论文材料：
   ```bash
   python "$SKILL_DIR/scripts/assetkit.py" --pdf "<材料路径>" --out /app/work/extract
   ```
   PDF → 页标记文本（`[PAGE n]`）+ 图片（`fig-p<页>-<序号>.png`）+ 抽取报告；
   文本/LaTeX → 直接读取。加密/扫描件/无 PDF 库走 §5 的 D02–D04。
5. 通读抽取文本，记录元信息（标题/作者/venue）与各章页码，供 P2 定位引用。

#### P2 蓝图规划（论文结构 → 页面骨架）
6. 按 `references/slide-blueprint.md` §1 的映射表把章节重写为
   问题（P）→ 方法（M）→ 证据（E）→ 结论（C）→ 局限（L）的可讲页序。
7. 抽**页级证据**：每张图/表/公式/关键结论的编号、页码、图注、数值与单位；
   数字、单位、方法名**逐字**从原文带出，不做同义改写。
8. 标注图的性质：论文原生图 / 从表格数字重建（`reconstructed_chart`）；
   **示意图绝不是实验数据**，两者不得混称（不变量 I4）。

#### P3 写 deck-spec.json + 检查点 C1
9. 按 `references/slide-blueprint.md` §3 schema 写 `/app/work/deck-spec.json`：
   每页 `claim` + 短语化 `bullets`（≤6 条、CJK 加权 ≤110 字）+ `figure`/`table`
   （`ref` 与论文一致）+ `notes`（过渡/强调/被问补充，**不复制页面文字**）
   + `evidence`（`ref` + `page` + `quote`）；无法定位证据的页写 `evidence_gap: true`。
10. **C1（写完后、生成前必跑）**：
    ```bash
    python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json
    # {"valid": true} 才视为蓝图合规；有偏差按 D05 处置
    ```

#### P4 构建可编辑源（assetkit → deckgen → ooxml_kit）
11. 端到端入口：
    ```bash
    python "$SKILL_DIR/scripts/main.py" \
      --case /input/case.json --task /input/task.md \
      --spec /app/work/deck-spec.json --out /app/output
    ```
12. 模板适配遵守三铁律：**只填占位符、不碰 master、不覆盖页脚/配色**；
    布局按名匹配 → 索引回退 → 内置版式。`constraints.template_mode="replace"` 时
    移除起始页仅留版式/母版并记录 `starter_slides_removed`；默认 `"layouts"` 保留。
13. 页数受 `slide_count` 约束；超限按 D08 处置（合并非证据页，**绝不静默丢弃证据页**）。
14. 案例未提供模板或模板不可用时按 D06/D07 回退内置 16:9 学术版式——**这是正常分支**，
    需在 `uncertainty` 留痕。需要一份可用示例模板时：
    ```bash
    python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"
    ```

#### P5 渲染与检查点 C3
15. 无 PowerPoint/LibreOffice 时预览为 PIL 近似（`preview-approx-*.png`），
    文件名、`previews[].kind`、`run_meta.rendered_with` 三处同时标注；有 LibreOffice 时
    用 `soffice --headless --convert-to pdf` 产出真 PDF 并改写记录（D13）。
16. 用 python-pptx 重开 deck，核对页数、标题序列、备注存在、图表编号与 evidence 一致。
17. **C3（交付门）**：
    ```bash
    python "$SKILL_DIR/scripts/export_check.py" --result /app/output/result.json \
      --out-dir /app/output --case /input/case.json
    # {"valid": true} 且 exit 0 才算通过；warnings 择要处理或如实保留
    ```

#### P6 写 result.json + 自评
18. result.json 含：`case_id`（与 case.json 逐字一致）、`status`、`output_contract`
    四形态回显（**禁止 null**）、`deck`（template guard / overflow_guard / auto_slides /
    theme_fonts）、`spec_lint`、双形态 `evidence_mapping`、`previews`、`charts`、
    `sources`、`uncertainty`、`change_records`、`run_meta`（rendered_with / skill_version /
    checkpoints / self_check）。字段以 `references/OUTPUT_CONTRACT.md` §1 为准：
    ```bash
    python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
      --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case /input/case.json
    ```
19. 按 `references/RUBRIC_MAP.md` 逐条自评；测试记录进 `TEST.md`，示例进 `examples/`。
20. 诚实性硬约束（违反即 C3 失败）：不编造科学数据；数值/单位不改写；
    图缺失 = 显式占位框；预览近似必须标注；每步改动进 `change_records`。

预算纪律：总 64 次模型请求 / 900 秒 / 单响应 16384 tokens（含推理）。先把 P1–P3
落盘成中间件，再逐段增量交付；脚本运行秒级，不占模型预算大头。

### 5. 决策规则总表 D01–D16

四列含义：**触发条件**（怎么认出这个情形）→ **首选举措**（先做什么）→
**失败时的降级**（首选不成立时改做什么）→ **记录与退出码**（写进哪个字段、进程怎么退出）。
每条规则在 `references/failure-modes.md` 有同号条目，两处不得只改一处。

| # | 触发条件 | 首选举措 | 失败时的降级 | 记录与退出码 |
|-|-|-|-|-|
| D01 | `case.json` 不存在或 JSON 不可解析 | 直接以 `status=failed` 收尾，不发明产物 | 输入完全不可读时不创建输出目录 | `case_unreadable`；**main.py → 3** |
| D02 | 材料路径不存在 / 不可读 | 只产出含元信息的 result，不构建 deck | 状态降 `failed`，语义字段按类型给空值 | `status=failed`、`material_status=unreadable`、`sources[].reason`；main.py → 0/1（以 self_check 为准） |
| D03 | PDF 报 encrypted | 先试空口令一次 | 改用外部导出的 `.txt`（`--materials`）并如实说明工具 | `uncertainty[]` + `sources[].tool`；assetkit → 2 |
| D04 | PDF 无文本层（`text_chars = 0`，扫描件） | 标注"图像型 PDF"，仍引用可抽取的图 | **不做 OCR 冒充**；必要时请用户补文本 | `uncertainty[]` + `sources[].tool`；assetkit → 2 |
| D05 | C1 lint 报偏差（bullet 超限 / 缺 evidence 且未标 gap / 缺 claim） | 先按报错逐条修 spec 再跑 C1 | 确属案例硬约束无法满足 → 构建继续但状态降 `partial`，偏差双写 | `spec_lint.problems` + `uncertainty[]` + `change_records[]`；spec_lint → 1 |
| D06 | 案例未提供模板（`resolve_template → builtin`） | 直接使用内置 16:9 学术版式 | 需要真实模板时跑 `make_template.py` 现场生成 | `deck.template.kind="builtin"`；make_template → 2（缺 python-pptx） |
| D07 | 声明了模板但文件不存在 / 打不开 / 占位符不足 | 回退内置版式并继续（**不是失败**） | 无 title/body/picture 占位符 → 名匹配→索引回退→补画文本框（登记命名） | `deck.template.kind/guard/error` + `layouts_used` + `uncertainty[]` |
| D08 | 页数超过 `slide_count` | 合并非证据页（封面/过渡/收尾优先） | **绝不静默丢弃证据页**；仍超限则如实标记 | `deck.page_budget_met=false` + `change_records[]` + `uncertainty[]` |
| D09 | 图/表抽不出（`images_extracted=0` 或损坏） | 该页保留显式占位框，文案注明"需补齐，非原图" | 引用与定位照留，图位空缺但不伪造 | `figure.placed=null` + `placeholder=true` + `uncertainty[]` |
| D10 | 重建图失败（无 matplotlib / 表格数据不全） | 跳过该图，保留表引用与数字 | 数字仍逐字来自原文，绝不估算补齐 | `charts[].chart.reason` + `run_meta.matplotlib_available=false` |
| D11 | `python-pptx` 缺失 | `deck=null`、状态降级，如实说明——**不生成假文件** | 仍写出契约完整的 result.json（含语义字段空值规则） | `deck_error` + `uncertainty[]` + `status` |
| D12 | 预览字体探测失败 / `Pillow` 缺失 | 降级 PIL 默认字体继续；deck 内仍写主题字体 + latin/ea 双写 | Pillow 完全缺失 → `previews=[]` 并降级说明 | `run_meta.preview_font`（可 null）+ `run_meta.rendered_with` + `uncertainty[]` |
| D13 | 检测到 LibreOffice / PowerPoint | `soffice --headless --convert-to pdf` 产出真 PDF 并改写记录 | 无引擎 → PIL 近似，三处标注 | `run_meta.rendered_with` + `previews[].kind=pil-approximation`；G8 为 warning |
| D14 | 输入不在 `/input`（环境变量/自定义路径） | 探测 `CASE_PATH`/`OUTPUT_DIR`/cwd 下 `case.json`，以可读文件为准 | 都不可读 → 按 D01 处置 | `run_meta.case_file` + `uncertainty[]` |
| D15 | `output_contract` 出现未知/无值字段（四形态任一） | 有真实值写真实值；否则按容器给 `""`/`[]`/`{}`，**禁止 null** | 形态无法判断（既非 dict 也非 list）→ 原样回显并记 uncertainty | `result.output_contract`；check_contract → 1（缺字段）/ 2（契约文档解析不出） |
| D16 | 任一降级发生后 | 同步写 `uncertainty[]`（发生了什么+影响）与 `change_records[]`（何时+为什么） | 两者只写其一会触发不变量 I5 违规 | `run_meta.self_check.ok=false` 时 **main.py → 1** |

> **D16 是全表的兜底规则**：只要走过 D02–D15 中任何一条降级分支，就必须回到 D16 补记录。
> `references/failure-modes.md` §2 按五类异常给出同号条目与更多子情形。

### 6. 失败分支处置表（五类 × 升级路径）

| 类别 | 典型触发 | 首选举措 | 升级/降级路径 | 对应规则 |
|-|-|-|-|-|
| **① 材料异常** | 文件不存在 / PDF 加密 / 无文本层 / 无 PDF 库 / 图文不符 / 图片抽不出 | 先"读实际文件"并记录真实工具与页数字数 | 逐级：空口令 → 外部 `.txt` → 标注不可读；图片 → 占位框；**始终以实际文件为准，不按标签补造** | D02–D04、D09、D10 |
| **② 模板缺失** | 未提供模板 / 文件不存在 / 损坏 / 占位符不足 / starter 需替换 / 页数超限 | 回退内置 16:9 学术版式并继续（正常分支） | 逐级：布局名匹配 → 索引回退 → 补画文本框（登记命名）；超限先合并非证据页 | D06–D08 |
| **③ 依赖缺失** | 无 python-pptx / 无 Pillow / 无 matplotlib / 无 PDF 后端 / 无中文字体 / 无 Office 引擎 | 探测真实可用性，写进 `run_meta` | 逐级：PyMuPDF → pypdf → pdfplumber → 外部文本；字体 msyh/simhei → DejaVu/Noto → PIL 默认；渲染 Office → PIL 近似 | D10–D13 |
| **④ 契约四形态** | ①字段→类型提示 ②字段→说明 ③布尔开关 ④字段清单 | 语义字段（title/main_claim/slides/render_state/notes_separated）写真实值 | 未知字段 `setdefault`；**任何声明字段禁止 null**；`case_id` 与 case 逐字一致 | D15（+ `OUTPUT_CONTRACT.md` §2） |
| **⑤ 状态不一致** | status 与 uncertainty/change_records 互相矛盾 | 按不变量 I1–I6 逐条自检后再交付 | 矛盾即降级重写；`completed` 只在不变量全成立时使用 | I1–I6、D05、D16 |

### 7. 状态一致性不变量 I1–I6（交付前逐条断言）

| # | 不变量 | 违反后果 |
|-|-|-|
| I1 | 材料不可读 ⇒ **禁止** `status=completed` | `export_check` 判 error；必须降 `failed` |
| I2 | 存在显式 `evidence_gap` 或图片只有占位框 ⇒ `status ≤ partial`，且 `uncertainty` 点名页号 | C3 视为状态不一致 |
| I3 | C1 lint 有偏差且继续构建 ⇒ `status ≤ partial`，`spec_lint.problems` 与 `uncertainty` 同时保留 | 只留其一即违规 |
| I4 | `charts[].chart.note` 出现 `reconstructed_from_table` ⇒ 该图不得在页面或备注里被称为论文原图 | 触发诚实性硬约束（`OUTPUT_CONTRACT.md` §4.1） |
| I5 | 任一次降级 ⇒ `uncertainty[]` 与 `change_records[]` 同时有对应条目 | `run_meta.self_check.ok=false`，main.py → 1 |
| I6 | `uncertainty` 为空 ⇒ 仅当整条链路无任何降级；`previews[].kind` 为近似 ⇒ `rendered_with` 必须写明 | 空 uncertainty 需能在本次日志中举证 |

### 8. 交付前自查清单

- [ ] 已读真实 case.json / task.md / 论文文件；`sources[]` 里有真实工具与页数/字数；
- [ ] deck-spec 按蓝图规划，每页有 `claim`；bullets 短语且 ≤6 条；evidence 或 evidence_gap 二选一；
- [ ] **C1 通过或偏差已按 D05 双写**；
- [ ] 页上数字/单位/方法名/图号与原文逐字一致（抽查 ≥3 处）；
- [ ] 页序可讲（问题→方法→证据→结论→局限），无"段落切片页"；
- [ ] notes 与页面文字分离，`notes_slide` 已写入（含封面/收尾页），`notes_separated=true`；
- [ ] 模板：占位符填充、master 未动、页脚未覆盖；否则 `template.guard` 已注明回退；
- [ ] `/app/output` 内存在：`result.json`（全部 output_contract 字段 + `case_id`）、
      `academic_deck.pptx`（可编辑、对象已命名）、`preview-approx-*.png`（或真 PDF）、
      `evidence_mapping.md` + `evidence_map.json`；
- [ ] **C3** `export_check.py` exit 0（G1–G8 无 error）；
- [ ] `check_contract.py` exit 0（顶层字段全覆盖、无 null）；
- [ ] 不变量 I1–I6 逐条成立；
- [ ] 已按 RUBRIC_MAP 五维自评并补足可复跑证据。

### 9. 限制（如实声明）

- 预览默认是 **PIL 近似渲染**，不等同于 PowerPoint/LibreOffice 结果；
- PDF 图片抽取依赖库与版式，个别图只以显式占位框呈现（占位框**不代表**论文原图）；
- 模板适配是"占位符级"：SmartArt 等复杂版式不重排；组织方模板自带形状不改名；
- 本 Skill 保证"内容 ↔ 证据定位"的一致性，**不保证论文结论本身正确**；
- 包内只携带文本资源（`.md/.py/.json/.txt/.csv/.yaml/.yml`）；模板、预览、重建图一律
  运行时生成，因此首次运行前需 `python-pptx` 才能产出 `.pptx`（缺失按 D11 降级）。

### 10. 维护

- 版本号：`scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；
- 分层约定：素材能力进 `assetkit.py`，生成逻辑进 `deckgen.py`，OOXML 细节进
  `ooxml_kit.py`（新对象类型先在 `ooxml_kit.PREFIX_BY_KIND` 注册命名前缀）；
- **新增/修改任一 D 规则，必须同步改 `references/failure-modes.md` 的同号条目**，
  并在 `references/RUBRIC_MAP.md` 的可靠体验行补复核命令；
- 不变量 I1–I6 若被修改，先改本表再改实现，避免"文档承诺 > 代码事实"；
- 修改记录同时进 result.json 的 `change_records` 与 git 提交历史。

---

# 【增益层】公平对照协议与可测指标（目标维度:使用增益 25）

---
name: paper-to-academic-ppt
description: 把论文/研究材料转换成主线清晰、证据可追溯、可编辑的学术汇报 PPT。本版把"加载它到底强在哪"写成可测量的断言（GA1–GA5）与一条可复跑的命令（scripts/gain_probe.py），并用同一套评审函数对"朴素单遍流水线 / 本 Skill / 去掉页级方案的消融臂"三臂逐格测量；执行链为 Step 0–Step 6 + 闸门 Q1–Q3，异常按 H01–H14 处置。产物含可编辑 .pptx、逐页证据映射（md + json 同源）、近似预览与契约完整的 result.json。Use when a task asks to turn a paper or research material into an academic slide deck (论文转PPT、学术汇报PPT、slides from paper、presentation from paper), especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews.
---

## 论文转学术 PPT（增益可验证版 · paper-to-academic-ppt）

学术汇报 PPT 这类任务最容易出现的一种失败是："看起来做完了，但说不出比不做强在哪里"。
本版本把这件事反过来做：**先写下要证明的增益断言，再给出测量它的命令，最后才谈流程**。

三个部件：

1. **执行链**（§4 Step 0–Step 6，含闸门 Q1/Q2/Q3）——保证每次运行都产出可交付物；
2. **处置规则**（§5 H01–H14）——保证出问题时行为可判定、降级有记录；
3. **增益测量**（§6 GA1–GA5 + `scripts/gain_probe.py`）——保证"更强"这句话可以被第三方在
   本机重跑出来，而不是靠叙述。

**不负责**：论文精读结论的生成、科研绘图本身的图形设计、学术写作润色。
**不使用预制答案**：正式运行只依据案例实际提供的文件；`examples/` 只演示接口。

---

### 1. 适用与触发

- `/input/case.json` + `/input/task.md` 存在，要求在 `/app/output` 产出演示产物；
- 或用户直接要求"把这篇论文做成学术 PPT / slides from this paper / 组会汇报"。

**适用**：单篇论文或研究报告 → 8–20 页学术汇报（页级主张 + 图表定位 + 讲解备注 +
模板适配 + 渲染记录）。**不适用**：判断论文结论真假、重画科研图、润色正文、
与材料无关的通用幻灯片——越界请求写进 `uncertainty` 并拒绝。

**与其他版本的关系**：本版包含"决策显性化"的全部内容（H01–H14 与五类异常一一对应），
并额外提供 §6 的可测断言与对照执行件。若只想看判断规则，读 §5 即可。

### 2. 输入输出与自定位

| 方向 | 路径（以环境实际挂载为准） | 内容 |
|-|-|-|
| 输入 | `/input/case.json` | `case_id`、`output_contract`、材料/模板定位、受众与页数约束 |
| 输入 | `/input/task.md` | 任务说明（存在时读取；缺失不阻断） |
| 工作 | `/app/work` | 抽取文本与图片、页级方案 `deck-spec.json` |
| 输出 | `/app/output` | `result.json`、`academic_deck.pptx`、`preview-approx-*.png`、`evidence_mapping.md`、`evidence_map.json`、`chart-*.png/.svg` |

**自定位**：`$SKILL_DIR` = `SKILL.md` 所在目录。脚本以
`os.path.dirname(os.path.abspath(__file__))` 自解析并 `sys.path.insert` 本目录，
**cwd 不是技能根也能跑**；因此所有命令统一写成：

```bash
SKILL_DIR="<SKILL.md 所在目录>"      # 平台安装到 /skills/weekly-skill 时即该路径
python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json
```

输入不在 `/input` 时，先探测 `CASE_PATH` / `OUTPUT_DIR` / cwd 下的 `case.json`，
**以实际可读文件为准**（H14）。

### 3. 资源清单（相对 `$SKILL_DIR`）

| 文件 | 作用 | 独立 CLI |
|-|-|-|
| `scripts/main.py` | 端到端编排（Q1 → 抽取 → 构建 → 预览 → Q3 → result.json） | `--case --out` 必填 |
| `scripts/gain_probe.py` | **本版新增**：三臂公平对照执行件（§6），产物只写 `--out` | `--out` 必填；`--arms`、`--repeat`、`--json` 可选 |
| `scripts/assetkit.py` | 素材层：材料定位、PDF 文本/图片抽取、表格数字重建图 | `--pdf --out` |
| `scripts/deckgen.py` | 生成层：模板适配、页级排版、备注、证据映射页、形状命名 | 打印记录 |
| `scripts/ooxml_kit.py` | OOXML 层：主题字体注入、命名、zip/XML 健全检查、命名审计 | 传 `.pptx` |
| `scripts/spec_lint.py` | **闸门 Q1**：deck-spec 结构校验（BL-1…BL-4） | `--spec` |
| `scripts/export_check.py` | **闸门 Q3**：契约 + 容器 + 命名 + 证据表一致性（G1–G8） | `--result --out-dir [--case]` |
| `scripts/check_contract.py` | 契约字段覆盖核对（读 `references/OUTPUT_CONTRACT.md` §1） | `--result --contract [--case]` |
| `scripts/preview.py` | PIL 近似预览（无 Office 引擎时的诚实渲染） | 打印记录 |
| `scripts/make_template.py` | 运行期生成回退模板（包内不携带二进制模板） | `--out [--name] [--no-starter]` |
| `scripts/make_synthetic_inputs.py` | 运行期生成合成夹具（几何占位图 + 两页 ASCII PDF） | `--out` |
| `scripts/cli_io.py` | 控制台加固（UTF-8 + `errors="replace"`） | 被各入口导入 |
| `references/OUTPUT_CONTRACT.md` | result.json 顶层字段 + 四形态回显 + G1–G8（**必读**） | — |
| `references/GAIN-PROTOCOL.md` | **本版新增**：公平对照协议 + 指标定义 + 真实对照记录 | — |
| `references/failure-modes.md` | 五类失败分支的处置与退出码（与 H01–H14 同号） | — |
| `references/slide-blueprint.md` | 论文→页面蓝图映射 + deck-spec schema + 证据表格式 | — |
| `references/RUBRIC_MAP.md` | 五维评分落点（以使用增益为主轴）+ 复核命令 | — |
| `references/layer-naming.md` | 分层命名规范（对象名 = 可编辑性的机器可查证据） | — |
| `examples/` | 最小示例（合成案例，明确标注"示例，非正式案例"） | — |

依赖：`python-pptx` 必需；`Pillow` 预览；`matplotlib` 可选（重建图）；
`PyMuPDF`/`pypdf`/`pdfplumber` 任一即可读 PDF。逐级回退见 §5 与 `failure-modes.md`。

### 4. 执行链 Step 0 – Step 6（闸门 Q1–Q3）

| Step | 动作 | 出口条件 |
|-|-|-|
| **0** | 读 `task.md` 与 `/input/case.json`：取 `case_id`、`output_contract`、材料/模板、受众与页数约束；解析 `$SKILL_DIR` | 已能说出"必须回显哪些字段" |
| **1** | **读实际文件**（不许按标签假设内容）：`python "$SKILL_DIR/scripts/assetkit.py" --pdf "<材料路径>" --out /app/work/extract` | `sources[]` 里有真实工具与页数/字数 |
| **2** | 按 `slide-blueprint.md` §1 把章节重写为 问题→方法→证据→结论→局限 的可讲页序，并抽页级证据（编号/页码/图注/数值单位**逐字**） | 每张拟上页的图/表都有定位 |
| **3** | 写 `/app/work/deck-spec.json`（schema 见 `slide-blueprint.md` §3），然后跑 **闸门 Q1**：`python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json` | `{"valid": true}`；有偏差按 H05 处置 |
| **4** | **闸门 Q2**（构建）：`python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --spec /app/work/deck-spec.json --out /app/output` | 进程结束且 `./out/academic_deck.pptx` 存在（或按 H11 如实降级） |
| **5** | 预览与渲染记录：无 Office 引擎时 PIL 近似（文件名 + `previews[].kind` + `rendered_with` 三处标注）；检测到 `soffice` 则产真 PDF 并改写（H13） | 预览文件真实落盘 |
| **6** | 写 result.json 并跑 **闸门 Q3**：`python "$SKILL_DIR/scripts/export_check.py" --result /app/output/result.json --out-dir /app/output --case /input/case.json`，再跑 `check_contract.py` 核对 19 个顶层字段 | 两道门 exit 0；随后按 `RUBRIC_MAP.md` 自评 |

模板适配的三条铁律（Step 4 内）：**只填占位符、不碰 master、不覆盖页脚/配色**；
布局按名匹配 → 索引回退 → 内置版式；`template_mode="replace"` 时移除起始页并记
`starter_slides_removed`。页数超限按 H08 合并非证据页，**绝不静默丢弃证据页**。

预算纪律：64 次模型请求 / 900 秒 / 单响应 16384 tokens（含推理）。先把 Step 1–3
落盘成中间件再增量交付；脚本本身秒级，不占模型预算大头。

### 5. 处置规则 H01–H14

每条四段：**触发**（怎么认出）→ **首选**（先做什么）→ **降级**（首选不成立时）→
**记录**（写进哪个字段）。退出码语义统一见 `references/failure-modes.md` §1。

| # | 触发 | 首选 | 降级 | 记录 |
|-|-|-|-|-|
| H01 | `case.json` 缺失/不可解析 | 以 `status=failed` 收尾，不发明产物 | 完全不可读时不创建输出目录 | `case_unreadable`；`main.py` → 3 |
| H02 | 材料路径不存在 | 只产出元信息 result，不构建 deck | 状态降 `failed`，语义字段给类型空值 | `material_status=unreadable`、`sources[].reason` |
| H03 | PDF 加密 | 试空口令一次 | 改用外部 `.txt`（`--materials`），工具如实记 | `uncertainty[]` + `sources[].tool`；assetkit → 2 |
| H04 | PDF 无文本层（扫描件） | 标注"图像型 PDF"，仍引用可抽取的图 | **不做 OCR 冒充** | `uncertainty[]` + `sources[].tool` |
| H05 | Q1 lint 报偏差 | 按报错逐条修 spec 再跑 | 案例硬约束确实无法满足 → 继续构建但状态降 `partial`，偏差双写 | `spec_lint.problems` + `uncertainty[]` + `change_records[]` |
| H06 | 未提供模板 | 用内置 16:9 学术版式（正常分支） | 需要真模板时 `make_template.py` 现产 | `deck.template.kind="builtin"` + `uncertainty[]` |
| H07 | 模板不存在/损坏/占位符不足 | 回退内置版式并继续 | 名匹配 → 索引回退 → 补画文本框（登记命名） | `deck.template.kind/guard/error` + `layouts_used` |
| H08 | 页数超 `slide_count` | 合并非证据页（封面/过渡/收尾优先） | **绝不静默丢弃证据页**；仍超限如实标记 | `page_budget_met=false` + `change_records[]` |
| H09 | 图/表抽不出 | 保留显式占位框（注明"需补齐，非原图"） | 引用与定位照留，不伪造图片 | `figure.placed=null` + `placeholder=true` |
| H10 | 重建图失败 | 跳过图，保留表引用与原文数字 | **不估算补齐数字** | `charts[].chart.reason` + `run_meta.matplotlib_available` |
| H11 | 缺 `python-pptx` | `deck=null`、状态降级、如实说明 | **不生成假文件**；result.json 仍契约完整 | `deck_error` + `uncertainty[]` + `status` |
| H12 | 字体/Pillow 缺失 | 降级 PIL 默认字体继续；deck 内 latin+ea 双写 | Pillow 完全缺失 → `previews=[]` 并说明 | `run_meta.preview_font`（可 null）+ `rendered_with` |
| H13 | 有/无渲染引擎 | 有 `soffice` → 真 PDF；无 → PIL 近似 | 近似必须三处标注，不得称为真实渲染 | `run_meta.rendered_with` + `previews[].kind` |
| H14 | 输入不在 `/input`／契约出现未知字段 | 探测 `CASE_PATH`/`OUTPUT_DIR`/cwd；四形态回显，未知字段 `setdefault` | 都不可读 → H01；**任何声明字段禁止 null** | `run_meta.case_file` + `result.output_contract` |

> 兜底：**任何一条降级发生后**，`uncertainty[]`（发生了什么 + 影响）与
> `change_records[]`（何时 + 为什么）必须**同时**有对应条目；否则
> `run_meta.self_check.ok=false`，`main.py` 退出码 1。

### 6. 增益可验证化：断言 GA1–GA5 与测量方式

**口径先讲清楚**：题面的权威对照是平台用"基础 Agent vs 加载本 Skill 的 Agent"跑出的
白板结果，参赛者不提供隐藏测试。本节给的是**可以在本机复跑的结构性对照**——
它把"基础 Agent 会怎么做"实现成一条朴素单遍流水线（`gain_probe.py` 的 `baseline` 臂），
因此差异是**可逐格复核的事实**，而不是分数预测。完整协议与边界见
`references/GAIN-PROTOCOL.md`。

| 断言 | 指标（同 `_review` 测量） | 判据 | 复核命令 |
|-|-|-|-|
| **GA1 页级主张** | `claim_coverage`（带非空 claim 的页占比）、`placeholder_claims` | 加载后 `substantive_claim_coverage = 1.0` 且 `placeholder_claims = 0`；基线为 `0.0` | `python "$SKILL_DIR/scripts/gain_probe.py" --out <scratch> --arms baseline,skill,ablation --repeat 2` |
| **GA2 证据可追溯** | `evidence_rows`（md 表行数）、`evidence_locations`（json 中带定位且 `status≠gap` 的行数） | 加载后两数与声明 `entries` 一致且 > 0；基线为 `0` | 同上；报告见 `<scratch>/gain-report.json` |
| **GA3 契约完整性** | `contract_fields_present`（/19） | 加载后 `19/19` 且无 null；基线仅 7 | 同上 + `check_contract.py` |
| **GA4 备注分离与溢出保护** | `notes_pages`、`over_limit_frames` | 加载后备注页数 = 总页数且超限框 = 0；基线备注 0 页且存在超限框 | 同上 |
| **GA5 交付返工点** | `rework_points`（同一套一致性检查的失败计数） | 加载后 `0`；基线 6；去掉页级方案的消融臂 ≥ 1 | 同上 |

**三臂的定位**（`--arms baseline,skill,ablation`）：

- `baseline` = 朴素单遍流水线（段落切块贴页、无证据映射、无 lint、无模板适配、
  不分离备注、不按契约产出）——"不加载本 Skill"的可执行代理；
- `skill` = 本包 `main.py` 全链路，输入与基线完全相同（同 case、同材料、同页数上限）；
- `ablation` = `main.py --demo`：脚本与契约机制都在，**只去掉 Agent 写的页级方案**
  与 Q1 前置门，用来隔离"方案先行"这一项机制的贡献。

`gain_probe.py` 只写 `--out` 指定目录，且给所有子进程设 `PYTHONDONTWRITEBYTECODE=1`，
**因此可以在包内原地运行而不产生 `__pycache__`**。其余脚本请在包外副本上运行
（Python 会在 `scripts/` 下写字节码缓存，而技能资源只允许文本文件）。

### 7. 交付自查（逐条）

- [ ] 已读真实 case.json / task.md / 材料；`sources[]` 有真实工具与页数/字数；
- [ ] 每页有 `claim`；bullets 短语 ≤6 条；`evidence` 或 `evidence_gap` 二选一；
- [ ] **Q1** 通过或偏差按 H05 双写；
- [ ] 页上数字/单位/方法名/图号与原文逐字一致（抽查 ≥3 处）；
- [ ] 页序可讲，无"段落切片页"；
- [ ] 备注与页面文字分离，含封面/收尾页，`notes_separated=true`；
- [ ] 模板：占位符填充、master 未动、页脚未覆盖；否则 `template.guard` 注明回退；
- [ ] `/app/output` 有 `result.json`（19 字段 + `case_id`）、`.pptx`、预览、
      `evidence_mapping.md` + `evidence_map.json`；
- [ ] **Q3** `export_check.py` exit 0（G1–G8 无 error）；`check_contract.py` exit 0；
- [ ] 降级双写（`uncertainty` + `change_records`）齐全，无编造软件状态或科学数据；
- [ ] 如引用增益数据，**必须写明它是本机结构性对照（GA1–GA5）而非平台白板分数**。

### 8. 限制与口径边界

- 预览是 **PIL 近似渲染**，不等于 PowerPoint/LibreOffice 结果；
- PDF 图片抽取依赖库与版式，个别图只以显式占位框呈现（**不代表**论文原图）；
- 模板适配为"占位符级"，SmartArt 不重排；模板自带形状不改名；
- 结论正确性上限 = 论文原文；本 Skill 不验证论文结论；
- **对照口径**：`gain_probe.py` 的 `baseline` 是"基础 Agent 行为"的可执行代理，
  不是对某个具体 LLM 的测量；它测的是**结构差异**（有无页级主张/证据映射/契约/备注分离/
  溢出保护），不预测平台分数。`wall_seconds` 依赖机器与案例规模，只作效率参考。
- 包内只携带文本资源（`.md/.py/.json/.txt/.csv/.yaml/.yml`）；模板、预览、重建图一律
  运行时生成，首次运行前需 `python-pptx`（缺失按 H11 降级）。

### 9. 维护

- 版本号：`scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；
- 分层约定：素材进 `assetkit.py`，生成进 `deckgen.py`，OOXML 细节进 `ooxml_kit.py`
  （新对象类型先在 `ooxml_kit.PREFIX_BY_KIND` 注册命名前缀）；
- **改任一条 H 规则** → 同步改 `references/failure-modes.md` 同号条目与
  `references/RUBRIC_MAP.md` 复核命令；
- **改任一 GA 指标或判据** → 同步改 `references/GAIN-PROTOCOL.md` §3 的指标定义，
  并在 `TEST.md` 追加一次新跑出的对照数字（不许沿用旧数字）；
- 修改记录同时进 result.json 的 `change_records` 与 git 提交历史。
