# paper-to-academic-ppt — 论文转学术 PPT（efficiency-3 / ppt-c7b80f0d · 字节级可复现版）

把论文/研究材料转换成**主线清晰、证据可追溯、可编辑**的学术汇报演示，并且**能证明
"同输入再跑一次得到同一份产物"**的 Skill 包。平台加载本 Skill 后在 3 个固定案例上真实运行；
**本包不含任何预制答案**。

设计主线（与本题五维评分逐条对应，见 `references/RUBRIC_MAP.md`）：

```
CP0 复现判据       →  契约先行   →  方案先行  →  生成  →  双形态校验  →  逐条自评
determinism.py        OUTPUT_CONTRACT   deck-spec + spec_lint   main.py   export_check + check_contract   RUBRIC_MAP
（跨进程/cwd/seed，逐文件 sha256 + 白名单分类）
```

## 本版主轴：可复现性是可跑的判据，不是一句承诺

```bash
SKILL_DIR="<本包根目录>"          # 平台安装到 /skills/weekly-skill 时即该路径
python "$SKILL_DIR/scripts/determinism.py" --out "<探针目录>" --runs 5 --stabilize
```

它在**独立进程**、**不同 cwd**、**不同 `PYTHONHASHSEED`** 下连跑主流程 N 次，
对全部产物做 sha256 比对，并把差异分成两类：**已解释**（写死在代码里的白名单）与
**未解释**（会让退出码变 1）。实测（示例案例，5 次运行，13 个产物）：

| 判据 | 实测 |
|-|-|
| 原始字节一致 | `False` —— 10/13 一致；`.pptx` / `.svg` / `result.json` 含**故意**不稳定的字节 |
| 规范化后一致 | **`True`（13/13）** |
| 稳定化后字节一致 | **`True`（13/13）**，稳定化副本 5/5 相同 |
| 未解释差异 | **0** |
| 已解释的不稳定项 | 5 条 JSON 指针 + 3 类容器证据（zip 成员 mtime、SVG `<dc:date>` 与随机元素 id、输出目录身份） |
| 根因验证 | `--svg-hashsalt v7-fixed` 后 SVG 元素 id **0 处不同**（默认 83 个 id 里 12 处不同） |

逐字段说明（为什么不稳定、如何稳定化、观测值）见 **`references/DETERMINISM.md`**，
机器可读证据见 `references/determinism_report.json` 与 `references/determinism_report-hashsalt.json`。

## 快速开始（任意 cwd 均可）

```bash
SKILL_DIR="<本包根目录>"

# 0) 复现判据（本版新增，交付前跑一次；exit 0 = 规范化后一致且无未解释差异）
python "$SKILL_DIR/scripts/determinism.py" --out "<探针目录>" --runs 5 --stabilize

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
（逐页证据映射，双形态同源）、`result.json`（契约完整 + `case_id`）、可选 `chart-*.png/.svg`
（从论文表格数字重建的图）。

## 最小示例（合成案例，非正式案例）

```bash
python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"   # ① 生成示例模板（二进制，运行期现产）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --spec "$SKILL_DIR/examples/deck-spec.json" --out "<空输出目录>"          # ② 跑示例
```

① 可跳过：模板不存在时自动回退内置 16:9 学术版式（`deck.template.kind="builtin"`），
这是正常且被记录的分支，不是失败。示例输入/预期产物见 `examples/README.md`、
`examples/EXPECTED-OUTPUT.md`。

## 用法与调用方式

完整阶段与检查点见 `SKILL.md` §4（W0–W6，CP0 / CP1 / CP3）与 §5（决策规则 R01–R12）：

| 参数（`main.py`） | 必填 | 说明 |
|-|-|-|
| `--case` | 是 | case.json 路径（给目录时取其内 case.json） |
| `--task` | 否 | task.md（存在时读取，advisory） |
| `--spec` | 否* | Agent 写好的页级 deck-spec.json；缺省仅 `--demo` 允许自动骨架 |
| `--materials` | 否 | 覆盖材料目录/文件（优先级高于 case 内声明） |
| `--out` | 是 | 输出目录（最终产物落位） |
| `--demo` | 否 | 允许自动骨架 spec（仅演示用，状态如实降为 partial） |
| `--verbose` | 否 | 打印 traceback |

其余入口的参数清单见 `SKILL.md` §3（`assetkit` / `spec_lint` / `export_check` /
`check_contract` / `make_template` / `make_synthetic_inputs` / `determinism`），
以及各脚本的 `--help`。

## 依赖

- 必需：Python ≥3.8，`python-pptx`（构建 .pptx），`Pillow`（预览渲染）；
- 可选（逐级回退并如实记录，见 `references/failure-modes.md` §2.3）：
  - PDF 解析：`PyMuPDF(fitz)` ≻ `pypdf` ≻ `pdfplumber`（全无 → 用自带 PDF 读取转 `.txt` 传入）；
  - 重建图：`matplotlib`（缺失 → 跳过图并记录；**其 SVG 元素 id 默认每次渲染随机**，见
    `references/DETERMINISM.md` §3.3）；
  - 预览字体：运行时探测 `C:/Windows/Fonts` ≻ `/System/Library/Fonts` ≻ `/usr/share/fonts`
    ≻ PIL 默认（可用环境变量 `SKILL_PREVIEW_FONT` 覆盖）。
- 参考运行环境（`TEST.md` 记录）：Windows 11 / Python 3.13.9 / python-pptx 1.0.2 /
  Pillow 12.3.0 / matplotlib 3.10.6 / PyMuPDF 1.28.0，**无 LibreOffice**（预览一律 PIL 近似）。

## 关键方法与机制

1. **CP0 复现判据（本版新增）**：`determinism.py` 把"同输入→同字节"做成三级判定，
   白名单写死在代码里（自动吸收差异的探针等于没有判据）；未解释差异 → 退出码 1。
2. **稳定化而非"相信"**：探针物理重写不稳定部分（固定 zip 成员 `date_time`、
   去 `<dc:date>`、按文档顺序重命名 SVG id、规范化 JSON 中已解释字段），并**比对重写后的字节**。
3. **契约先行**：`OUTPUT_CONTRACT.md` 列出 result.json 的 19 个顶层字段，`check_contract.py`
   直接读该文档逐字段核对 → 文档与代码不会悄悄漂移（`main.py` 内置同一道自检）。
4. **方案先行**：先把论文重写成页级 `deck-spec.json`（一页一主张 + 证据定位），
   `spec_lint.py` 做 CP1 结构性 lint（BL-1…BL-4）后才允许生成。
5. **蓝图映射**：论文结构 → 页面骨架（问题→方法→证据→结论→局限），杜绝"把段落切成行"。
6. **双形态证据映射**：`evidence_mapping.md`（人复核）+ `evidence_map.json`（机器读）同一 spec
   生成，导出检查器校验行数 = 声明 entries。
7. **三层脚本**：assetkit（素材）→ deckgen（页面生成）→ ooxml_kit（OOXML 精修：主题字体、
   分层命名、容器健全检查）。
8. **模板占位符约束**：只填占位符、不动 master、不覆盖页脚/配色；布局名匹配 → 索引回退 →
   内置版式；`template_mode="replace"` 时移除起始页并记录 `starter_slides_removed`。
9. **诚实渲染与运行时资源**：无 Office 引擎时预览为 PIL 近似（文件名 + `kind` +
   `rendered_with` 三处标注）；模板、预览、重建图等二进制**一律运行时生成**，
   技能资源只含 UTF-8 文本文件；探针子进程带 `PYTHONDONTWRITEBYTECODE=1`，探测不留 `__pycache__`。

## 目录结构

```
SKILL.md                      阶段 W0–W6（CP0/CP1/CP3）、决策规则 R01–R12、自查清单
README.md                     本文件：依赖/安装/用法/限制/维护
TEST.md                       本机真实实测记录（命令 + 退出码 + 结果摘要）
GITHUB_URL.txt                公开作品链接（单行）
references/OUTPUT_CONTRACT.md result.json 顶层字段清单 + 四形态 + G1–G8
references/DETERMINISM.md     ★本版主轴：哪些字节故意不稳定、如何稳定化、实测表
references/determinism_report.json             CP0 实测报告（默认模式，5 次运行）
references/determinism_report-hashsalt.json    CP0 对照实测（固定 svg.hashsalt）
references/RUBRIC_MAP.md      五维评分 → 本包落点 + 对照协议
references/failure-modes.md   失败模式 / 降级策略 / 退出码语义
references/slide-blueprint.md 蓝图映射 + deck-spec schema + 证据表格式
references/layer-naming.md    PPTX 分层命名规范
scripts/main.py               端到端入口（--case/--spec/--out，其余可选）
scripts/assetkit.py / deckgen.py / ooxml_kit.py   素材 / 生成 / OOXML 三层
scripts/spec_lint.py          CP1 结构性 lint
scripts/export_check.py       CP3 导出检查（G1–G8）
scripts/check_contract.py     契约字段覆盖核对
scripts/preview.py            PIL 近似预览
scripts/make_template.py      运行期生成回退模板（不随包携带二进制）
scripts/make_synthetic_inputs.py  运行期生成合成夹具（占位图 + 两页 PDF）
scripts/cli_io.py             控制台加固（非 UTF-8 环境下打印中文不崩）
scripts/determinism.py        ★CP0 复现判据（跨进程/cwd/seed 探测 + 稳定化）
examples/                     最小示例（合成案例）：case/spec/task/材料/预期产物
```

> 既有 11 个脚本与本版基线**逐字节相同**；本版只**新增** `scripts/determinism.py`
> 与 3 个 `references/` 文件（另在 `RUBRIC_MAP.md` 的"可靠体验/资源可复用性"两行内
> 补入本版落点），未改动任何 CLI 参数名、默认值与退出码语义。

## 限制

- 预览为**近似**渲染，非 PowerPoint/LibreOffice 实际渲染结果；
- 可复现性结论限定"同解释器 + 同压缩库 + 同平台"；跨环境只承诺 zip 成员载荷一致；
- `result.json` 的 `charts[].chart.file` 携带输出目录绝对路径（已知限制，决策规则 R03）；
- PDF 图片抽取依赖库与版式，个别图会以显式占位框呈现（占位框**不代表**论文原图）；
- 模板适配为"占位符级"，不重排 SmartArt 等复杂版式；
- 结果正确性上限 = 论文原文；本 Skill 不负责验证论文结论；
- 首次运行前需具备 `python-pptx` 才能产出 `.pptx`；缺失时如实降级而非伪造文件。

## 失败处理

异常分类与处置见 `references/failure-modes.md`（材料异常 / 模板缺失 / 依赖缺失 /
契约四形态 / 状态一致性，逐类给出识别→处置→记录位置→退出码），与 `SKILL.md` §5 的
R01–R12 一一对应。一切降级都会写入 result.json 的 `uncertainty` 与 `change_records`；
**复现判据不过（退出码 1）时不得直接交付**，必须先按 R01 定位并解释或修掉。

## 自测与维护

- `TEST.md`：本机实测记录（编译 / 端到端 / CP0 五场景 / 阴性对照 / 交付门 + 退出码）；
- `examples/EXPECTED-OUTPUT.md`：示例案例的预期产物与契约字段清单（文字形态）；
- 版本号在 `scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；
- 新增能力：素材能力进 `assetkit.py`，生成逻辑进 `deckgen.py`，OOXML 细节进 `ooxml_kit.py`
  （新对象种类先在 `PREFIX_BY_KIND` 注册命名前缀）；**会写时间戳/随机值的产物必须同步登记到
  `determinism.py` 的白名单与 `DETERMINISM.md` §3**；
- 新增失败分支必须同时更新 `references/failure-modes.md`；修改记录见 git 与 result.json 的
  `change_records`。
