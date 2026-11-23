# paper-to-academic-ppt — 论文转学术 PPT（efficiency-3 / ppt-c7b80f0d · 契约矩阵版）

把论文/研究材料转换成**主线清晰、证据可追溯、可编辑**的学术汇报演示，并把案例声明的
`output_contract` 契约做成"**四形态 × 边界值**"的可跑矩阵。平台加载本 Skill 后在 3 个固定
案例上真实运行；**本包不含任何预制答案**。

设计主线（与本题五维评分逐条对应，见 `references/RUBRIC_MAP.md`）：

```
CP4 契约矩阵       →  契约先行    →  方案先行  →  生成  →  双形态校验  →  逐条自评
contract_matrix.py    OUTPUT_CONTRACT   deck-spec + spec_lint   main.py   export_check + check_contract   RUBRIC_MAP
四形态 × 边界值真跑    19 字段清单        BL-1…BL-4                          G1–G8 + 字段面
```

## 本版主轴：契约边界必须被真跑过，而不是被假设

```bash
SKILL_DIR="<本包根目录>"          # 平台安装到 /skills/weekly-skill 时即该路径
python "$SKILL_DIR/scripts/contract_matrix.py" --out "<探针目录>" \
  --emit-md "<探针目录>/CONTRACT-MATRIX.md"
```

对每个单元注入一份完整 `case.json`（只改 `output_contract`），跑**未经修改的**端到端流程，
逐行记录 `exit` / `status` / 契约回显 / 是否**静默通过**（既没纠正、也没记录）。
实测（示例案例为基座，28 个单元）：**28/28 写出 `result.json`、0 崩溃、静默通过 0 条**
（修复前 5 条，逐条见 `references/CONTRACT-MATRIX.md` §3）。

| 判据 | 实测 |
|-|-|
| 单元数 / 形态覆盖 | 28：① 字段→类型提示 ×14、② 字段→说明 ×2、③ 布尔开关 ×1、④ 字段清单 ×6、契约容器 ×5 |
| 写出 `result.json` | **28/28** |
| exit 0 的单元 | 23/28（5 个"声明不全/非法容器"单元 exit 1，被内部契约门**点名**而非静默） |
| 回显符合期望 | 修复前 21/28 → **修复后 28/28** |
| **静默通过** | 修复前 **5** → 修复后 **0** |
| 修复前那 5 条 | 声明 `0` 回显 `""`；声明 `true` 回显 `false`；声明 `false` 回显 `""`；声明 `123` 回显 `""`；清单里的 `7`/`null` 被静默丢弃 |

机器可读证据：`references/contract-matrix-data.json`（修复后）与
`references/contract-matrix-before-fix.json`（修复前对照）；说明与修复登记见
`references/CONTRACT-MATRIX.md`（由 `--emit-md` 现场生成，不是手抄表）。

## 快速开始（任意 cwd 均可）

```bash
SKILL_DIR="<本包根目录>"

# 0) 契约矩阵（本版新增，交付前跑一次；exit 0 = 无静默通过）
python "$SKILL_DIR/scripts/contract_matrix.py" --out "<探针目录>"

# 1) 蓝图 lint（CP1：写 deck-spec 后必跑）
python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json

# 2) 端到端生成（正式案例形态）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
  --spec /app/work/deck-spec.json --out /app/output

# 3) 两道交付门
python "$SKILL_DIR/scripts/export_check.py"  --result /app/output/result.json \
  --out-dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case /input/case.json
```

产出（均在 `--out` 目录）：`academic_deck.pptx`（可编辑源，对象分层命名）、
`preview-approx-*.png`（PIL 近似预览，如实标注）、`evidence_mapping.md` + `evidence_map.json`
（逐页证据映射，双形态同源）、`result.json`（19 个顶层字段 + `case_id`）、可选
`chart-*.png/.svg`（从论文表格数字重建的图）。

## 最小示例（合成案例，非正式案例）

```bash
python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"   # ① 生成示例模板（运行期现产）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --spec "$SKILL_DIR/examples/deck-spec.json" --out "<空输出目录>"          # ② 跑示例
```

① 可跳过：模板不存在时自动回退内置 16:9 学术版式（`deck.template.kind="builtin"`），
这是正常且被记录的分支，不是失败。示例输入/预期产物见 `examples/README.md`、
`examples/EXPECTED-OUTPUT.md`。

## 用法与调用方式

完整阶段与检查点见 `SKILL.md` §4（M0–M6，CP1 / CP3 / CP4）与 §5（决策规则 P01–P12）。

| 参数（`main.py`） | 必填 | 说明 |
|-|-|-|
| `--case` | 是 | case.json 路径（给目录时取其内 case.json） |
| `--task` | 否 | task.md（存在时读取，advisory） |
| `--spec` | 否* | Agent 写好的页级 deck-spec.json；缺省仅 `--demo` 允许自动骨架 |
| `--materials` | 否 | 覆盖材料目录/文件（优先级高于 case 内声明） |
| `--out` | 是 | 输出目录（最终产物落位） |
| `--demo` | 否 | 允许自动骨架 spec（仅演示用，状态如实降为 partial） |
| `--verbose` | 否 | 打印 traceback |

| 参数（`contract_matrix.py`） | 说明 |
|-|-|
| `--out` | 探针目录（`cells/<单元>/` 与报告落位） |
| `--only A04,A11` | 只跑指定单元（回归时用） |
| `--emit-md <path>` | 把矩阵渲染成 Markdown（`CONTRACT-MATRIX.md` 就是这么来的） |
| `--before-fix <json>` | 传入修复前的报告，用于在 §3 列出"修复前的静默通过" |
| `--redact-paths` | 报告与 Markdown 中的本机绝对路径替换为占位符（随包入库时用） |
| `--entry` / `--python` / `--timeout` / `--json` / `--quiet` | 入口、解释器、单元超时、报告路径、静默模式 |

其余入口（`assetkit` / `spec_lint` / `export_check` / `check_contract` / `make_template` /
`make_synthetic_inputs`）的参数清单见 `SKILL.md` §3 与各脚本 `--help`。

## 依赖

- 必需：Python ≥3.8，`python-pptx`（构建 .pptx），`Pillow`（预览渲染）；
- 可选（逐级回退并如实记录，见 `references/failure-modes.md` §2.3）：
  - PDF 解析：`PyMuPDF(fitz)` ≻ `pypdf` ≻ `pdfplumber`；
  - 重建图：`matplotlib`（缺失 → 跳过图并记录）；
  - 预览字体：运行时探测 `C:/Windows/Fonts` ≻ `/System/Library/Fonts` ≻ `/usr/share/fonts`
    ≻ PIL 默认（可用 `SKILL_PREVIEW_FONT` 覆盖）。
- 矩阵不需要任何额外依赖（纯标准库；它复用 `scripts/check_contract.py` 读契约字段清单）。
- 参考运行环境（`TEST.md` 记录）：Windows 11 / Python 3.13.9 / python-pptx 1.0.2 /
  Pillow 12.3.0 / matplotlib 3.10.6 / PyMuPDF 1.28.0，**无 LibreOffice**。

## 关键方法与机制

1. **CP4 契约矩阵（本版新增）**：四形态 × 边界值逐单元注入 + 真跑 + 逐行判定；
   "静默通过"是独立列而不是被平均掉的细节。
2. **判定三分**：`match` / `mismatch-recorded`（被 `uncertainty` 记录或被内部契约门拦住）/
   `silent-pass`（既没纠正也没记录 → 必须先处理）。
3. **契约面完整性用文档驱动**：矩阵复用 `check_contract.fields_from_contract()` 读
   `OUTPUT_CONTRACT.md` §1 的 19 个字段名，逐单元核对——文档改了，矩阵跟着改。
4. **契约先行**：`OUTPUT_CONTRACT.md` 的四形态回显规则 + G1–G8 是唯一判据来源，
   矩阵的"期望"列标注了哪些来自文档明文、哪些是"类型忠实"推定。
5. **方案先行**：先把论文重写成页级 `deck-spec.json`，`spec_lint.py` 过 CP1 才允许生成。
6. **蓝图映射**：论文结构 → 页面骨架（问题→方法→证据→结论→局限），杜绝段落切片。
7. **双形态证据映射**：`evidence_mapping.md` + `evidence_map.json` 同一 spec 生成，
   导出检查器校验行数 = 声明 entries。
8. **三层脚本**：assetkit（素材）→ deckgen（生成）→ ooxml_kit（OOXML 精修）。
9. **运行时资源自生成**：模板、预览、重建图等二进制一律运行时生成，技能资源只含文本。

## 目录结构

```
SKILL.md                       阶段 M0–M6（CP1/CP3/CP4）、决策规则 P01–P12、自查清单
README.md                      本文件：依赖/安装/用法/范围/限制/维护
TEST.md                        本机真实实测记录（命令 + 退出码 + 结果摘要）
GITHUB_URL.txt                 公开作品链接（单行）
references/OUTPUT_CONTRACT.md  result.json 顶层字段清单 + 四形态 + G1–G8（字段块逐字未改）
references/CONTRACT-MATRIX.md  ★本版主轴：28 单元逐行实测 + 静默通过清单 + 修复登记 + 未覆盖声明
references/contract-matrix-data.json            矩阵实测原始记录（修复后）
references/contract-matrix-before-fix.json      同一矩阵修复前的对照记录（5 条静默通过）
references/RUBRIC_MAP.md       五维评分 → 本包落点 + 对照协议
references/failure-modes.md    失败模式 / 降级策略 / 契约形态细化 / 退出码语义
references/slide-blueprint.md  蓝图映射 + deck-spec schema + 证据表格式
references/layer-naming.md     PPTX 分层命名规范
scripts/main.py                端到端入口（--case/--spec/--out，其余可选）
scripts/contract_matrix.py     ★CP4 契约矩阵（四形态 × 边界值注入 + 真跑 + 判定）
scripts/assetkit.py / deckgen.py / ooxml_kit.py   素材 / 生成 / OOXML 三层
scripts/spec_lint.py           CP1 结构性 lint
scripts/export_check.py        CP3 导出检查（G1–G8）
scripts/check_contract.py      契约字段覆盖核对（矩阵也复用它）
scripts/preview.py             PIL 近似预览
scripts/make_template.py       运行期生成回退模板（不随包携带二进制）
scripts/make_synthetic_inputs.py  运行期生成合成夹具
scripts/cli_io.py              控制台加固
examples/                      最小示例（合成案例）：case/spec/task/材料/预期产物
```

> **脚本改动登记（逐条点名）**：新增 `scripts/contract_matrix.py`（新入口，不改既有语义）；
> `scripts/main.py` 的 `apply_output_contract()` 内做 3 处**纯增量**修复
> （未知布尔字段如实回显 / 数值型声明如实回显 / 非法元素与非法容器写入 `uncertainty`），
> 逐条含风险说明见 `references/CONTRACT-MATRIX.md` §5 与 `TEST.md` T5。
> **CLI 参数名、默认值与退出码语义均未改动**；其余 10 个脚本逐字节不变。

## 限制

- 矩阵只覆盖 `output_contract` 一个契约面，未覆盖项逐条列在 `CONTRACT-MATRIX.md` §6；
- 矩阵中"文档未明文覆盖时按类型忠实推定"的 4 个单元已在 §0/逐行 note 标注，不当作明文；
- 预览为近似渲染，非 PowerPoint/LibreOffice 实际结果；
- `charts[].chart.file` 携带输出目录绝对路径（已知限制）；模板适配为"占位符级"；
- 结果正确性上限 = 论文原文；本 Skill 不负责验证论文结论。

## 失败处理

异常分类与处置见 `references/failure-modes.md`（材料异常 / 模板缺失 / 依赖缺失 /
**契约四形态与边界值** / 状态一致性，逐类给出识别→处置→记录位置→退出码），与
`SKILL.md` §5 的 P01–P12 一一对应。一切降级都会写进 `uncertainty` / `change_records`；
**矩阵报出静默通过（exit 1）时不得直接交付**，必须先按 P01 处理。

## 自测与维护

- `TEST.md`：本机实测记录（编译 / 端到端 / 矩阵前后对照 / 负路径 / 交付门 + 退出码）；
- `examples/EXPECTED-OUTPUT.md`：示例案例的预期产物与契约字段清单（文字形态）；
- 版本号在 `scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；
- **新增 `output_contract` 形态或边界值 → 在 `contract_matrix.py` 的 `CELLS` 加一行
  （含 `expect`），重跑矩阵并更新 `references/CONTRACT-MATRIX.md`**；
- 新增失败分支必须同时更新 `references/failure-modes.md`；修改记录见 git 与 result.json 的
  `change_records`。
