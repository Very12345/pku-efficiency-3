# paper-to-academic-ppt · 增益可验证版（efficiency-3 / ppt-c7b80f0d）

把论文或研究材料转换成**主线清晰、证据可追溯、可编辑**的学术汇报 PPT 的 Skill 包。
本版（`v2`）沿 **使用增益（25 分）** 这条轴做了实质增强：不再只是"声称更完整"，
而是给出**可执行的三臂对照**（`scripts/gain_probe.py`）、**指标定义**
（`references/GAIN-PROTOCOL.md`）与**本机真实跑出的数字**。平台加载本 Skill 后
在 3 个固定案例上真实运行；**本包不含任何预制答案**。

## 一、这一版能证明什么（一条命令 + 三个臂）

```bash
export PYTHONDONTWRITEBYTECODE=1
python "<包外副本>/scripts/gain_probe.py" --out "<scratch>" \
       --arms baseline,skill,ablation --repeat 2
# exit 0；报告写在 <scratch>/gain-report.json
```

同一份 case、同一份材料、同一份页级方案、同一套评审函数，测三个臂：

| | `baseline` | `skill` | `ablation` |
|-|-|-|-|
| 是什么 | 朴素单遍流水线（段落切块贴页） | 本包全链路 | `main.py --demo`：去掉页级方案与 Q1 前置门 |
| `rework_points` ↓ | **6** | **0** | 2 |
| `substantive_claim_coverage` ↑ | 0.0 | **1.0** | 0.0 |
| `evidence_rows` / `evidence_locations` ↑ | 0 / 0 | **6 / 6** | 1 / 0 |
| `contract_fields_present`（/19）↑ | 7 | **19** | 19 |
| `notes_pages`（总页数）↑ | 0（3） | **8（8）** | 3（6） |
| `over_limit_frames` ↓ | 2 | **0** | 0 |
| 两次运行 OPC 部件差异 ↓ | 0 | **0（72 部件）** | 0 |

> 数字来自本机真实运行（条件 T：模板在场；`--repeat 2`），完整记录见
> `references/GAIN-PROTOCOL.md` §4。**它们不是平台白板分数，也不能换算成分数**；
> `baseline` 是"基础 Agent 行为"的可执行代理，不是对某个具体 LLM 的测量。

## 二、本版相对同族基线的实质改动（逐条）

| # | 位置 | 改了什么 | 为什么这会让包更强 |
|-|-|-|-|
| 1 | `scripts/gain_probe.py`（**新增**） | 三臂对照执行件：内置一条朴素单遍流水线作为基线；三臂共用同一个 `_review()` 评审函数；输出 `gain-report.json`（逐臂 metrics + `rework` 原文） | 把"更强"从形容词变成可复跑的命令；基线也接受同一把尺子 |
| 2 | `references/GAIN-PROTOCOL.md`（**新增**） | 公平对照协议：四同条件（同输入/同模板/同版本/同预算）、三臂定义与口径边界、14 个指标的定义与判据、**两组真实对照记录**（含 `rework` 原文）、复跑步骤、可信边界 | 直接回应题面"通过同输入、同模板、同版本的公平对照证明质量或效率改善" |
| 3 | `SKILL.md` §6 | 新增**增益断言 GA1–GA5**，每条绑定"指标 + 判据 + 复核命令" | 评审可逐条验证断言，而不是读结论 |
| 4 | `SKILL.md` §4 | 执行链改写为 **Step 0–Step 6 + 闸门 Q1/Q2/Q3**，每步给出"出口条件" | 流程从"步骤清单"变成"每步有可判定的完成标准" |
| 5 | `SKILL.md` §5 | 处置规则重排为 **H01–H14**（触发 / 首选 / 降级 / 记录），兜底双写规则单列 | 与可靠体验的异常处理项一一对应 |
| 6 | `references/failure-modes.md` | 每类异常新增一列 **"对 GA 断言的影响"**：哪些降级会让哪条增益断言不再成立 | 防止"一边降级一边宣称满额增益" |
| 7 | `references/RUBRIC_MAP.md` | 重写为**使用增益为主轴**：15/5/5 三个评分点逐条绑到可跑命令与实测数字；新增 §3 口径边界四条 | 自评表不再只列功能，而是列可验证的证据 |

算法与既有 `scripts/*.py` 的 CLI 接口**未改动**（本版是"可测量性"层面的增强；
新增脚本是追加件，不改变任何既有入口）。

## 三、快速开始（任意 cwd 均可，`$SKILL_DIR` = SKILL.md 所在目录）

```bash
SKILL_DIR="<本包根目录>"        # 平台安装到 /skills/weekly-skill 时即该路径

# 1) 闸门 Q1：写完 deck-spec 后必跑
python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json

# 2) 闸门 Q2：端到端生成
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
  --spec /app/work/deck-spec.json --out /app/output

# 3) 闸门 Q3：两道交付门
python "$SKILL_DIR/scripts/export_check.py"  --result /app/output/result.json \
  --out-dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case /input/case.json
```

产出（均在 `--out`）：`academic_deck.pptx`（可编辑、对象分层命名）、
`preview-approx-*.png`（PIL 近似，如实标注）、`evidence_mapping.md` +
`evidence_map.json`（双形态同源）、`result.json`（19 字段 + `case_id`）、
可选 `chart-*.png/.svg`（由论文表格数字重建）。

> ⚠️ **除 `gain_probe.py` 外，不要在包内直接跑脚本**：Python 会在 `scripts/` 下写
> `__pycache__`，而技能资源只允许文本文件，`validate_pkg.py` 会判 FAIL。
> 自测请先把包复制到包外临时目录（`TEST.md` 的记录全部按此方式产生；
> `gain_probe.py` 是个例外，因为它给子进程注入了 `PYTHONDONTWRITEBYTECODE=1`，
> 实测原地运行后 `__pycache__` 计数为 0）。

## 四、最小示例（合成案例，非正式案例）

```bash
python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"   # ① 生成示例模板（运行期现产）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" --spec "$SKILL_DIR/examples/deck-spec.json" \
  --out "<空输出目录>"                                                        # ② 跑示例
```

① 可跳过：模板不存在时自动回退内置 16:9 学术版式（`deck.template.kind="builtin"`，
对应 H06/H07），这是**正常且被记录**的分支。示例输入、预期产物与净化说明见
`examples/README.md`、`examples/EXPECTED-OUTPUT.md`。

## 五、调用参数

| 参数 | 必填 | 说明 |
|-|-|-|
| `--case` | 是 | `case.json` 路径（给目录时取其内 `case.json`） |
| `--task` | 否 | `task.md`（存在时读取，advisory） |
| `--spec` | 否* | Agent 写好的页级 `deck-spec.json`；缺省仅 `--demo` 允许自动骨架 |
| `--materials` | 否 | 覆盖材料目录/文件（优先级高于 case 内声明） |
| `--out` | 是 | 输出目录（最终产物落位） |
| `--demo` | 否 | 允许自动骨架 spec（状态如实降 `partial`；也是消融臂） |
| `--verbose` | 否 | 打印 traceback |

`gain_probe.py` 的参数：`--case`（默认 `examples/case.json`）、`--spec`
（默认 `examples/deck-spec.json`）、`--out`（**必填**）、`--arms`
（默认 `baseline,skill`；可选 `ablation`）、`--repeat`（默认 1）、`--json`、`--quiet`。

## 六、依赖

- 必需：Python ≥3.8、`python-pptx`、`Pillow`；
- 可选（逐级回退并如实记录，见 `references/failure-modes.md` §2.3）：
  PDF 解析 `PyMuPDF ≻ pypdf ≻ pdfplumber ≻ 外部 .txt`；重建图 `matplotlib`；
  预览字体 `C:/Windows/Fonts` → `/System/Library/Fonts` → `/usr/share/fonts` → PIL 默认
  （`SKILL_PREVIEW_FONT` 可覆盖）。
- 参考运行环境（见 `TEST.md`）：Windows 11 / Python 3.13.9 / python-pptx 1.0.2 /
  Pillow 12.3.0 / matplotlib 3.10.6 / PyMuPDF 1.28.0 / pypdf 6.14.2；**无 LibreOffice**。

## 七、目录结构

```
SKILL.md                        执行链 Step 0–6、处置规则 H01–H14、增益断言 GA1–GA5、自查
README.md                       本文件：本版改动、对照一览、依赖、调用、维护
TEST.md                         包外副本上的实测记录（15 条执行链 + 5 条对照执行件）
GITHUB_URL.txt                  公开作品链接（单行）
references/OUTPUT_CONTRACT.md   result.json 顶层字段 + 四形态回显 + 硬性门 G1–G8
references/GAIN-PROTOCOL.md     ★公平对照协议 + 指标定义 + 真实对照记录 + 复跑步骤
references/failure-modes.md     异常处置（与 H01–H14 同号）+ 对增益断言的影响
references/RUBRIC_MAP.md        五维落点（以使用增益为主轴）+ 复核命令 + 口径边界
references/slide-blueprint.md   论文→页面蓝图映射 + deck-spec schema + 证据表格式
references/layer-naming.md      PPTX 分层命名规范
scripts/main.py                 端到端入口（--case/--out 必填）
scripts/gain_probe.py           ★三臂对照执行件（只写 --out）
scripts/assetkit.py deckgen.py ooxml_kit.py   素材 / 生成 / OOXML 三层
scripts/spec_lint.py            Q1 结构 lint
scripts/export_check.py         Q3 导出检查（G1–G8）
scripts/check_contract.py       契约字段覆盖核对
scripts/preview.py              PIL 近似预览
scripts/make_template.py        运行期生成回退模板
scripts/make_synthetic_inputs.py  运行期生成合成夹具
scripts/cli_io.py               控制台加固
examples/                       最小示例（合成案例）：case/spec/task/材料/预期产物
```

## 八、限制

- 预览为**近似**渲染，非 PowerPoint/LibreOffice 实际结果；
- PDF 图片抽取依赖库与版式，个别图以显式占位框呈现（**不代表**论文原图）；
- 模板适配为"占位符级"，SmartArt 不重排；模板自带形状不改名；
- **对照口径**：`baseline` 是结构性代理而非具体 LLM 的测量；`wall_seconds` 只反映
  脚本开销，不等于端到端总耗时更短；权威口径仍是平台白板对照；
- 结论正确性上限 = 论文原文；本 Skill 不验证论文结论。

## 九、失败处理与维护

- 异常分类、退出码与"对增益断言的影响"见 `references/failure-modes.md`
  （材料异常 / 模板问题 / 依赖缺失 / 契约四形态 / 状态一致性，与 `SKILL.md` §5 的
  H01–H14 一一对应）；一切降级同时写入 result.json 的 `uncertainty` 与 `change_records`。
- 版本号在 `scripts/main.py` 的 `VERSION`（当前 `2.1.0`）。
- **维护铁律**：改任一条 H 规则 → 同步改 `failure-modes.md` 同号条目与 `RUBRIC_MAP.md`；
  改任一 GA 指标或判据 → 同步改 `GAIN-PROTOCOL.md` §3 并在 `TEST.md` 追加一次新跑出的
  对照数字（**不许沿用旧数字**）；修改记录同时进 git 与 result.json 的 `change_records`。
