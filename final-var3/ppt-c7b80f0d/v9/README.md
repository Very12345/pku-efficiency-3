# paper-to-academic-ppt — 论文转学术 PPT（efficiency-3 / ppt-c7b80f0d · 降级链实测版）

把论文/研究材料转换成**主线清晰、证据可追溯、可编辑**的学术汇报演示，并把"**缺依赖时到底
还剩什么**"做成逐项实测。平台加载本 Skill 后在 3 个固定案例上真实运行；**本包不含任何预制答案**。

设计主线（与本题五维评分逐条对应，见 `references/RUBRIC_MAP.md`）：

```
CP5 环境前置       →  契约先行    →  方案先行  →  生成  →  双形态校验  →  逐条自评
degrade_probe.py      OUTPUT_CONTRACT   deck-spec + spec_lint   main.py   export_check + check_contract   RUBRIC_MAP
缺库/无引擎真跑        19 字段清单        BL-1…BL-4                          G1–G8 + 字段面
```

## 本版主轴：降级链是测出来的，不是承诺出来的

```bash
SKILL_DIR="<本包根目录>"          # 平台安装到 /skills/weekly-skill 时即该路径
python "$SKILL_DIR/scripts/degrade_probe.py" --out "<探针目录>" \
  --emit-md "<探针目录>/DEGRADE-MATRIX.md"
```

在子进程里用**受控导入拦截**（`sys.meta_path` finder 抛 `ModuleNotFoundError`）分别去掉
python-pptx / Pillow / matplotlib / numpy / PyYAML，再把 LibreOffice 从 `PATH` 剥离，
逐场景跑**未经修改的**端到端入口，记录实测：产物还剩什么、`status` 变什么、是否写出
`result.json`、退出码、以及**是否存在静默降级**（自称完成但产物残缺）。

| 场景 | 屏蔽 | exit | `result.json` | status | 产物数 | 判定 |
|-|-|-|-|-|-|-|
| S0 基线对照 | （无） | 0 | 是 | completed | 13 | full success |
| S1 缺 python-pptx | `pptx` | 1 | **否** | — | **0** | crash（导入期失败） |
| S2 缺 Pillow | `PIL` | 1 | **否** | — | **0** | crash（pptx 内部依赖 PIL） |
| S3 缺 matplotlib | `matplotlib` | 0 | 是 | completed | 11 | 重建图不落盘，`uncertainty` 如实记录 |
| S4 缺 numpy | `numpy` | 0 | 是 | completed | 11 | 同上（matplotlib 因 numpy 失效） |
| S5 缺 PyYAML | `yaml` | 0 | 是 | completed | 13 | 与基线一致（管线不使用 yaml） |
| S6 缺 pptx+Pillow | `pptx,PIL` | 1 | **否** | — | **0** | crash |
| S7 无 LibreOffice | （PATH 剥离） | 0 | 是 | completed | 13 | 与基线一致（管线不调用它） |

汇总：**静默降级 0 条**；崩溃 3 条（都是"无产物"的**响亮失败**）；缺 pptx/Pillow 时 12 个模块
只剩 7 个可导入；依赖关系实测 `pptx → PIL`、`matplotlib → numpy/Pillow`、`PIL ↛ pptx`。
机器可读证据：`references/degrade-matrix-data.json`；说明与最小可用环境清单：
`references/DEGRADE-MATRIX.md`（由 `--emit-md` 现场生成）。

## 快速开始（任意 cwd 均可）

```bash
SKILL_DIR="<本包根目录>"

# 0) 环境前置（本版新增）：先确认硬依赖在不在，再看缺 matplotlib 的影响
python "$SKILL_DIR/scripts/degrade_probe.py" --out "<探针目录>" --only S0-baseline,S2-no-PIL,S3-no-matplotlib

# 1) 蓝图 lint（CP1：写 deck-spec 后必跑；纯标准库，任何缺库环境都能跑）
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
`chart-*.png/.svg`（从论文表格数字重建的图，**只有 matplotlib 可用时才落盘**）。

## 最小示例（合成案例，非正式案例）

```bash
python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"   # ① 生成示例模板（运行期现产）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --spec "$SKILL_DIR/examples/deck-spec.json" --out "<空输出目录>"          # ② 跑示例
```

① 可跳过：模板不存在时自动回退内置 16:9 学术版式（`deck.template.kind="builtin"`），
这是正常且被记录的分支；缺 `python-pptx` 时 `make_template.py` 会以**退出码 2** 如实失败。
示例输入/预期产物见 `examples/README.md`、`examples/EXPECTED-OUTPUT.md`。

## 用法与调用方式

完整阶段与检查点见 `SKILL.md` §4（G0–G6，CP1 / CP3 / **CP5 环境前置**）与 §5（决策规则 L01–L12）。

| 参数（`main.py`） | 必填 | 说明 |
|-|-|-|
| `--case` | 是 | case.json 路径（给目录时取其内 case.json） |
| `--task` | 否 | task.md（存在时读取，advisory） |
| `--spec` | 否* | Agent 写好的页级 deck-spec.json；缺省仅 `--demo` 允许自动骨架 |
| `--materials` | 否 | 覆盖材料目录/文件（优先级高于 case 内声明） |
| `--out` | 是 | 输出目录（最终产物落位） |
| `--demo` | 否 | 允许自动骨架 spec（仅演示用，状态如实降为 partial） |
| `--verbose` | 否 | 打印 traceback |

| 参数（`degrade_probe.py`） | 说明 |
|-|-|
| `--out` | 探针目录（`scenarios/<场景>/out/` 与报告落位） |
| `--only S1-no-pptx,S3-no-matplotlib` | 只跑指定场景（环境前置时只跑 2–3 个，约 10 s） |
| `--emit-md <path>` | 把矩阵渲染成 Markdown（`DEGRADE-MATRIX.md` 就是这么来的） |
| `--redact-paths` | 报告与 Markdown 中的本机绝对路径替换为占位符（随包入库时用） |
| `--entry` / `--python` / `--timeout` / `--json` / `--quiet` | 入口、解释器、场景超时、报告路径、静默模式 |

其余入口（`assetkit` / `spec_lint` / `export_check` / `check_contract` / `make_template` /
`make_synthetic_inputs`）的参数清单见 `SKILL.md` §3 与各脚本 `--help`。

## 依赖（本版把"必需/可选"从文档承诺变成实测结论）

- **硬依赖（实测：缺则连 `result.json` 都写不出）**：`python-pptx` **及其 Pillow 依赖**
  （实测 `import pptx` 在屏蔽 PIL 时同样失败）；`scripts/deckgen.py`、`scripts/ooxml_kit.py`、
  `scripts/preview.py` 是模块级导入链；
- **软依赖（实测：缺则降级且被记录）**：`matplotlib`（重建图跳过 → `chart-*.png/svg` 不落盘，
  `charts[].chart.reason` 与 `uncertainty` 记明）；`numpy` 只通过 matplotlib 影响本管线；
- **未被主流程使用（实测：屏蔽后与基线一致）**：`PyYAML`；
- **PDF 解析**：`PyMuPDF(fitz)` ≻ `pypdf` ≻ `pdfplumber`，三选一（未在矩阵中覆盖，见
  `DEGRADE-MATRIX.md` §6）；
- **外部引擎**：LibreOffice 从未被调用（静态扫描 0 处调用），有无都不影响产物；
- **最低可用组合**：Python ≥3.8 + `python-pptx` + `Pillow`（要重建图再加 `matplotlib`）。
- 参考运行环境（`TEST.md` 记录）：Windows 11 / Python 3.13.9 / python-pptx 1.0.2 /
  Pillow 12.3.0 / matplotlib 3.10.6 / PyMuPDF 1.28.0，**无 LibreOffice**。

## 关键方法与机制

1. **受控导入拦截（本版新增）**：子进程里 `sys.meta_path.insert(0, finder)`，命中屏蔽名单就把
   `ModuleNotFoundError` 抛出去——被模拟的是"这个库真的不存在"，因此 `try/except ImportError`
   的降级分支会被真实走到；
2. **降级形态四分类**：`full success` / `honest partial/failed` / `crash (no result.json)` /
   **`silent degradation`**（自称完成但 deck 或预览已残缺）——最后一类单独列出并让退出码变 1；
3. **产物现场留证**：每个场景的输出目录原样保留（`scenarios/<场景>/out/`），报告里逐项列出
   剩余产物清单，不靠"应该还行"来判断；
4. **依赖关系实测**：除了单缺，还测"屏蔽 A 时 B 还能不能导入"，把传递依赖写清楚；
5. **模块可导入性矩阵**：同一屏蔽下逐个 `importlib.import_module`，得出"缺什么会连带废掉哪些入口"；
6. **静态与动态互证**：LibreOffice 的结论由"静态扫描 0 处调用 + PATH 剥离后行为一致"两条证据支撑；
7. **契约先行 / 方案先行 / 蓝图映射 / 双形态证据映射 / 三层脚本 / 运行时资源自生成**：与基线一致
   （细节见 `SKILL.md` §4 与 `references/slide-blueprint.md`）。

## 目录结构

```
SKILL.md                       阶段 G0–G6（CP1/CP3/CP5）、决策规则 L01–L12、自查清单
README.md                      本文件：依赖（实测）/安装/用法/范围/限制/维护
TEST.md                        本机真实实测记录（命令 + 退出码 + 结果摘要）
GITHUB_URL.txt                 公开作品链接（单行）
references/OUTPUT_CONTRACT.md  result.json 顶层字段清单 + 四形态 + G1–G8
references/DEGRADE-MATRIX.md   ★本版主轴：8 场景逐项实测 + 可导入性矩阵 + 依赖关系 + 最小可用环境
references/degrade-matrix-data.json   降级矩阵原始记录
references/RUBRIC_MAP.md       五维评分 → 本包落点 + 对照协议
references/failure-modes.md    失败模式 / 降级策略 / 依赖缺失逐库对照 / 退出码语义
references/slide-blueprint.md  蓝图映射 + deck-spec schema + 证据表格式
references/layer-naming.md     PPTX 分层命名规范
scripts/main.py                端到端入口（--case/--spec/--out，其余可选）
scripts/degrade_probe.py       ★受控导入拦截 + 场景真跑 + 降级形态判定
scripts/assetkit.py / deckgen.py / ooxml_kit.py   素材 / 生成 / OOXML 三层
scripts/spec_lint.py           CP1 结构性 lint（纯标准库）
scripts/export_check.py        CP3 导出检查（G1–G8）
scripts/check_contract.py      契约字段覆盖核对
scripts/preview.py             PIL 近似预览
scripts/make_template.py       运行期生成回退模板（缺 pptx → 退出码 2）
scripts/make_synthetic_inputs.py  运行期生成合成夹具
scripts/cli_io.py              控制台加固
examples/                      最小示例（合成案例）：case/spec/task/材料/预期产物
```

> 既有 11 个脚本与基线包**逐字节相同**；本版只**新增** `scripts/degrade_probe.py`
> 与 3 个 `references/` 文件（另在 `RUBRIC_MAP.md` / `failure-modes.md` 的既有表格对应行内
> 补入本版落点），未改动任何 CLI 参数名、默认值与退出码语义。

## 限制

- 拦截是**模块级**的：模拟"库不存在"，不模拟"库在但 API 行为不同"；
- 未覆盖 PDF 解析库缺失、三缺以上组合、系统级故障（字体目录为空/只读目录/磁盘满）——
  逐条列在 `DEGRADE-MATRIX.md` §6；
- 预览为近似渲染，非 PowerPoint/LibreOffice 实际结果；
- `charts[].chart.file` 携带输出目录绝对路径（已知限制）；模板适配为"占位符级"；
- 结果正确性上限 = 论文原文；本 Skill 不负责验证论文结论。

## 失败处理

异常分类与处置见 `references/failure-modes.md`（依赖缺失 / 材料异常 / 模板缺失 /
契约四形态 / 状态一致性，逐类给出识别→处置→记录位置→退出码），与 `SKILL.md` §5 的
L01–L12 一一对应。**依赖缺失的处置以实测为准**：缺 pptx/Pillow 属于"端到端不可用"，
必须先把环境补齐；缺 matplotlib 属于"可继续但必须记录"。

## 自测与维护

- `TEST.md`：本机实测记录（编译 / 端到端 / 8 场景降级矩阵 / 依赖关系 / 负路径 / 交付门 + 退出码）；
- `examples/EXPECTED-OUTPUT.md`：示例案例的预期产物与契约字段清单（文字形态）；
- 版本号在 `scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；
- **导入链或依赖集变化 → 重跑 `degrade_probe.py` 并更新 `DEGRADE-MATRIX.md` 的
  `DEP_PROBES`/最小可用环境清单**；
- 新增降级分支必须同时写进 `uncertainty` 并更新 `references/failure-modes.md`。
