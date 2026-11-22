# REUSABLE-ASSETS — 可复用资产清单与复用步骤

本文件面向**想拿走一部分用**的人：哪些资产可以独立复用、入口参数是什么、依赖
什么、复用时会继承哪些保证。所有参数名与本包 `scripts/*.py --help` 的输出**逐字
一致**（已逐个核对）。

一句话前提：本包全部二进制都在运行时生成（见 `references/MECHANISM.md` §5），
因此任何复用方式都**不需要**先下载 `.pptx` 或图片。

---

## 1. 资产总览

| 资产 | 路径 | 依赖 | 可独立运行？ | 适合谁用 |
|-|-|-|-|-|
| **A** 模板适配层 | `scripts/pptx_toolkit.py` + `scripts/adapt_pptx.py` | python-pptx | ✅（`adapt_pptx.py` 有完整 CLI） | 已有自己的内容管线，只想借"套模板 + 占位符继承 + contain-fit"的人 |
| **B** 阶段一方案器 | `scripts/adopt_plan.py` | python-pptx | ✅ | 想先审模板结构、再决定每页用哪个版式的人 |
| **C** 确定性页计划器 | `scripts/deckplan.py` | 无（纯标准库） | ✅ | 想要"论文章节 → 页型序列"确定性映射的人 |
| **D** 审计与契约工具 | `scripts/audit.py` · `validate_result.py` · `check_contract.py` | python-pptx | ✅（各自独立 CLI） | 想给自己的 Skill 加"独立校验 + 硬门"的人 |
| **E** 运行时资源生成器 | `scripts/make_template.py` · `make_synthetic_inputs.py` | python-pptx / Pillow | ✅ | 包体受限（只能放文本）、又需要真实模板/图件的人 |
| **F** 示例题集与页级金标准 | `examples/` | 无 | 作为输入使用 | 想快速验证自己管线、或想照抄"案例 → 契约"形态的人 |
| 公共工具 | `scripts/common.py` | 无 | 库 | 自定位、便携路径、字号阶梯、字体探测 |
| 契约定义 | `references/OUTPUT_CONTRACT.md` | 无 | 文档 | 想对齐字段契约与 G1–G8 的人 |

## 2. 资产 A：模板适配层

**一句话用途**：对**任意** pptx 做母版/版式/占位符审计，并按方案把内容写进
正确的占位符（缺占位符时手绘文本框并留痕），图表等比 contain-fit。

**入口与参数**（`adapt_pptx.py --help` 逐字）：

```text
python scripts/adapt_pptx.py --content CONTENT --spec SPEC --out OUT
       [--template TEMPLATE] [--starting-deck STARTING_DECK]
       [--builtin BUILTIN] [--adopt-plan ADOPT_PLAN]
```
- `--out` 是**文件路径**（输出 pptx），不是目录；
- `--adopt-plan` 传入阶段一方案时会按方案套版式；不传则退化为按启发式选版式。

**独立运行条件**：需要 `content.json`（`extract.py` 产出）与 `spec.json`
（`deckplan.py` 产出）作为输入；两者都是纯 JSON，可手写小样例。

**依赖**：`python-pptx`；`PIL` 仅预览阶段需要。

**复用示例**（借用别人的材料，只要一份页计划）：

```bash
RUN=<可写目录>
python "$SKILL_DIR/scripts/extract.py"  --case "$CASE" --task "$TASK" --out "$RUN"
python "$SKILL_DIR/scripts/deckplan.py" --content "$RUN/content.json" --out "$RUN"
python "$SKILL_DIR/scripts/make_template.py" --out "$RUN/builtin.pptx"
python "$SKILL_DIR/scripts/adopt_plan.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --builtin "$RUN/builtin.pptx" --out "$RUN/adopt_plan.json"
python "$SKILL_DIR/scripts/adapt_pptx.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --adopt-plan "$RUN/adopt_plan.json" \
    --builtin "$RUN/builtin.pptx" --out "$RUN/deck.pptx"
```

**继承的保证**：几何与版式选择是**纯函数**；缺占位符一定留痕
（`layout_fallback_used` / `adopt_plan_deviations`）；图表不拉伸（含
`aspect_preserved` 记录）；pptx 走 `deterministic_zip()`，同输入同字节（M6）。

## 3. 资产 B：阶段一方案器

**一句话用途**：打开真实模板，枚举母版/版式/占位符/画布/主题，为每一页挑版式，
评估批量规则并给出图表放置计划 —— 产出**可核对的** `adopt_plan.json`。

**入口与参数**（`adopt_plan.py --help` 逐字）：

```text
python scripts/adopt_plan.py --content CONTENT --spec SPEC
       [--template TEMPLATE] [--starting-deck STARTING_DECK] [--builtin BUILTIN]
       [--limit LIMIT] [--meta META] --out OUT
```
- `--out` 是**文件路径**（`adopt_plan.json`）；
- `--limit` 限定模板来源链：`case_template|starting_deck|builtin`；
- `--meta` 可写入一个 `_meta` 标签（示例运行时用来标注"这是示例产物"）。

**独立运行条件**：只要 `content.json` + `spec.json` + 一个模板（三者之一：
`--template` / `--starting-deck` / `--builtin`）。

**依赖**：`python-pptx`（读模板与 `theme1.xml`）。

**复用示例**（只想要"某模板有哪些版式、每页该用哪个"）：

```bash
python "$SKILL_DIR/scripts/adopt_plan.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --template "$TPL" --out "$RUN/adopt_plan.json"
# 读 adopt_plan.json：layouts / pages[].recommended_layout_idx / batch / figure_plan
```

**继承的保证**：**无时间戳的纯函数** —— 同一 (content, spec, template) 两次运行
产出**逐字节相同**的方案（这使得"方案是否被改动过"可以用哈希核对）；偏差一律写进
`batch.deviations` 而非静默修正。

## 4. 资产 C：确定性页计划器

**一句话用途**：把抽取到的内容映射成确定的页型序列（cover → background →
methods → results×N → discussion → limitations → conclusion → evidence_map →
thankyou），并在超页时按固定顺序裁剪。

**入口与参数**（`deckplan.py --help` 逐字）：

```text
python scripts/deckplan.py --content CONTENT --out OUT
```
- `--out` 是**目录**；产出 `spec.json`。

**独立运行条件**：只需 `content.json`。**依赖：无**（纯标准库），因此非常适合
嵌进别的管线。

**复用示例**：

```bash
python "$SKILL_DIR/scripts/deckplan.py" --content "$RUN/content.json" --out "$RUN"
# spec.json: pages[] 每条含 page_type / title / claims / figure_refs / notes / evidence
```

**继承的保证**：**完全确定**（无随机、无时间戳）；裁剪顺序固定，且**证据页最后
才动**，任何裁剪写入 `change_records`。

## 5. 资产 D：审计与契约工具

**一句话用途**：三个分工明确的验证器 —— 产物自查、字段级契约校验、**独立于
自述**的交付硬门。

**入口与参数**（逐个 `--help` 逐字）：

```text
python scripts/audit.py --content CONTENT --spec SPEC --out OUT
       [--build-audit BUILD_AUDIT] [--adopt-plan ADOPT_PLAN]

python scripts/validate_result.py [--case CASE] --result RESULT

python scripts/check_contract.py --result RESULT --out-dir OUT_DIR [--case CASE]
```
- `audit.py --out` 是**产物目录**；`--build-audit` 指 `adapt_pptx.py` 产出的
  `.build_audit.json`；`--adopt-plan` 用于对照"方案↔执行一致性"；
- `validate_result.py` 只做字段级校验，**不打门**；
- `check_contract.py` 会**自己重开 pptx、自己扫产物清单**，不信任 result.json 的
  自述；`--case` 可选，提供后启用 G1/G3/G8。

**独立运行条件**：只要有产物目录。`check_contract.py` 需要 `result.json` +
产物目录（+ 可选 case）。

**复用示例**（把硬门接到自己的 Skill 上）：

```bash
python "$SKILL_DIR/scripts/validate_result.py" --case "$CASE" --result "$RUN/out/result.json"
python "$SKILL_DIR/scripts/check_contract.py"  --result "$RUN/out/result.json" \
    --out-dir "$RUN/out" --case "$CASE"
```

**继承的保证**：**退出码语义稳定** —— `validate_result.py` 通过时 `exit 0` 并打
`VALID`；`check_contract.py` 通过时 `exit 0` 且输出 `{"valid": true}`，否则
`exit 1` 并列出每个失败门。因此可以直接写进 CI 或 shell 的 `&&` 链。

## 6. 资产 E：运行时资源生成器

**一句话用途**：在**不往包里放二进制**的前提下，现场造出真实可用的模板与占位图。

**入口与参数**（逐个 `--help` 逐字）：

```text
python scripts/make_template.py [--out OUT] [--cache-dir CACHE_DIR] [--force]

python scripts/make_synthetic_inputs.py [--dir DIR] [--out-dir OUT_DIR] [--force]
```
- `make_template.py --out` 是 **`.pptx` 文件路径**（默认写到临时目录）；
  `--cache-dir` 走 `ensure_builtin()` 的复用逻辑；`--force` 强制重生成；
- `make_synthetic_inputs.py --dir` 指示例目录（图写到 `<dir>/figs`）；
  `--out-dir` 直接指定图目录。

**独立运行条件**：`make_template.py` 需 `python-pptx`；
`make_synthetic_inputs.py` 需 `Pillow`。两者都不需要案例文件。

**复用示例**：

```bash
python "$SKILL_DIR/scripts/make_template.py" --out "$RUN/template.pptx"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
```

**继承的保证**：两者都是**确定性**的（同参数同字节），且回退模板带**真实**
母版/版式/占位符（不是空白 pptx）；占位图是**纯几何 + SCHEMATIC 水印**，
**不含任何伪造的测量数值**——这一点是刻意的：参考图不该被误认成真实数据。

> 缺依赖时的行为：`ensure_builtin()` **返回原因字符串而不是抛异常**，由调用方
> 决定降级（见 `references/MECHANISM.md` §5 与 `SKILL.md` 的 D5/D16）。

## 7. 资产 F：示例题集与页级金标准

**一句话用途**：一组**最小但完整**的输入（案例 + 任务 + 材料 + 契约）与页级金
标准字段，用来快速验证任何"论文 → PPT"管线。

**内容**：

| 文件 | 说明 |
|-|-|
| `examples/case.json` | 合成示例案例（`example-catalyst-201`，**虚指数值**），含 10 页目标、受众、时长、图表清单与 `output_contract`（7 个键） |
| `examples/task.md` | 任务说明（受众/时长/页数/交付要求） |
| `examples/material.md` | 示例"论文材料"正文（38 行，带 `# 背景/方法/结果/讨论/限制/结论` 小节），供抽取与 `文件:行` 定位 |
| `examples/plan.sample.json` | **页结构方案样例**（`deckplan` 的真实运行结果，标注为示例） |
| `examples/adopt_plan.sample.json` | **适配方案样例**（阶段一 `adopt_plan` 的真实运行结果，标注为示例） |
| `examples/EXPECTED-OUTPUT.md` | 该 Skill 在示例案例上**应产出的文件清单与契约字段** |
| `examples/output/` | 示例运行的**文本**产物（`result.json` / `summary.txt` / `render_log.json` + 说明文件）；二进制产物按硬门不随包 |

**独立运行条件**：作为**输入**使用即可；先合成图件：

```bash
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
```

**复用示例**（当作"空白对照题集"检验自己的管线）：

```bash
cp -r "$SKILL_DIR/examples" "$RUN/examples"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"
```

**继承的保证 / 页级金标准**：运行后可用这些字段逐页核对你的管线 ——
`slide_evidence` 每页一条（含 claim / 图号引用 / 证据定位）、
`template_audit.layout_used` 每页一条版式记录、`verification.checks` 21 条审计
结果、`verification.contract_gates` 8 条门。**示例产物一律标注为示例**，不得冒充
正式案例结果（`examples/output/_LABEL_example.txt`）。

## 8. 复用步骤（三个场景）

### 场景 1：只用模板适配层（自带内容管线）

```bash
RUN=<可写目录>; TPL=<你的模板.pptx>; CASE=<你的case.json>
python "$SKILL_DIR/scripts/extract.py"  --case "$CASE" --out "$RUN"       # -> content.json
python "$SKILL_DIR/scripts/deckplan.py" --content "$RUN/content.json" --out "$RUN"
python "$SKILL_DIR/scripts/adopt_plan.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --template "$TPL" --out "$RUN/adopt_plan.json"
python "$SKILL_DIR/scripts/adapt_pptx.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --adopt-plan "$RUN/adopt_plan.json" \
    --out "$RUN/deck.pptx"
python "$SKILL_DIR/scripts/preview.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --out "$RUN"
```
产出：`deck.pptx` + 两张预览。**这一步不产 `result.json`**（那是 `main.py` 的
职责），所以不构成一次可提交交付。

### 场景 2：接进已有管线（只要方案与校验）

```bash
# 2a. 先审模板：拿到版式清单与页→版式建议，人工过一遍
python "$SKILL_DIR/scripts/adopt_plan.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --template "$TPL" --out "$RUN/adopt_plan.json"
# 2b. 你自己的生成器产出 deck + result.json 之后，用独立校验器把门
python "$SKILL_DIR/scripts/check_contract.py" --result "$RUN/out/result.json" \
    --out-dir "$RUN/out" --case "$CASE"     # exit 0 且 {"valid": true} 才算过
```
注意：`check_contract.py` 的 G4 会**自己重开** pptx、G7 会**逐文件扫**产物，
因此它对你自己的产物同样有效——不依赖本包的生成器。

### 场景 3：当作对照基线（做自己的增益实验）

```bash
# 用本包当 B 臂、用你自己的做法当 A 臂，按 GAIN-PROTOCOL.md §3 的六条约束执行
cp -r "$SKILL_DIR/examples" "$RUN/input"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/input"
python "$SKILL_DIR/scripts/make_template.py" --out "$RUN/input/tpl/template.pptx"
# 令 case.json.template = "tpl/template.pptx"，两臂都从该字段解析模板（关键！）
python "$SKILL_DIR/scripts/main.py" --case "$RUN/input/case.json" \
    --task "$RUN/input/task.md" --out "$RUN/armB/out"
# 再用 GAIN-PROTOCOL.md §4 的 Q1–Q8 / E1–E4 口径测量两臂
```
**最容易出错的一步**：让两臂共用同一份模板。若 B 臂的
`template_audit.opened_from` 是 `builtin`（而非 `case_template`），说明"同模板"
没落实，整个对照无效（见 `GAIN-PROTOCOL.md` §3 C2 与 §8 清单）。

## 9. 复用时的注意事项与已知坑

| 坑 | 现象 | 处置 |
|-|-|-|
| **在包内跑脚本** | 生成 `scripts/__pycache__/*.pyc` | 交付前 `find <包目录> \( -name '__pycache__' -o -name '*.pyc' \) -delete`；**永远在包外副本上跑**（`.pyc` 属平台拒绝的资源类型） |
| `--out` 语义混用 | `extract/deckplan/preview/audit` 收**目录**，`adopt_plan/adapt_pptx/make_template` 收**文件** | 传错会得到 `IsADirectoryError` 一类错误；按 §2–§6 的参数说明传 |
| 案例未给模板就以为会失败 | 走的是回退模板路径 | 这是设计行为（D5）：`opened_from=builtin`，来源进 `uncertainty`；**不要**据此判失败 |
| 把"预览"当"导出" | 预览是 PIL 示意图（`preview_is_schematic=true`） | 需要像素级/PDF 时须自备 LibreOffice/PowerPoint；本包**不产伪 PDF** |
| 认为重跑一定全字节一致 | `result.json` 有 `generated_at`，且回退模板来源措辞会变 | 见 `TEST.md` §2：本次为 11/12；**核对 deck 与 PNG 的哈希**，不要拿 result.json 当一致性判据 |
| 主题字体/色当可写 | 它们只是**只读记录** | 需要改主题请改模板本体，本包不代改（D8） |
| 依赖缺失静默失败 | 不会：写 `status=failed` 的 result.json | 读 `uncertainty[0].note` 拿到原始 `ImportError` 文本 |

## 10. 复用产出如何自证

拿走任何资产后，用同一套判据检查你的产物：

1. **结构完整**：`check_contract.py --result ... --out-dir ... --case ...`
   → `exit 0` 且 `{"valid": true}`（它对**任意**产物都有效，不看是谁生成的）；
2. **字段契约**：`validate_result.py --case ... --result ...` → `VALID`；
3. **模板继承可查**：`result.json.template_audit.layout_used` 每页一条，
   含版式名 / master / 来源；
4. **内容可追溯**：抽查 ≥3 条 `slide_evidence[].evidence[].loc` 能在材料中命中；
5. **方案可信**：`adopt_plan_applied` == 计划页数，`adopt_plan_deviations` 可读；
6. **过程可复跑**：同输出目录连跑两次，deck 与 PNG 的 sha256 相同；
7. **诚实披露**：非 `success` 状态必须带 `uncertainty`（G8 会查这一点）。

七条里有任何一条不成立，就说明该资产在被复用后**退化**了——先按 §9 的坑表排查。
