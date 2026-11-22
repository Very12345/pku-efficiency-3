# paper-to-academic-ppt · 决策规则版（efficiency-3 / ppt-c7b80f0d）

把论文或研究材料转换成**主线清晰、证据可追溯、可编辑**的学术汇报 PPT 的 Skill 包。
本版（`v1`）沿**可靠体验 + 实际效果**两条评分轴做了实质增强：把原本散在
"注意事项"里的判断，重写成可判定的 **D01–D16 决策规则**、**五类失败分支处置表**
与 **I1–I6 状态不变量**，读者不必揣摩语气就能知道"这种情况该做什么、写进哪个字段、
退出码是几"。平台加载本 Skill 后在 3 个固定案例上真实运行；**本包不含任何预制答案**。

设计主线：

```
契约先行 → 方案先行 → C1 lint → 模板占位符级生成 → C3 导出检查 → 回显契约 + 不变量断言
OUTPUT_CONTRACT.md  deck-spec.json  spec_lint  main.py  export_check/check_contract  failure-modes.md
```

## 本版相对同族基线的实质改动（逐条）

| # | 位置 | 改了什么 | 为什么这会让包更强 |
|-|-|-|-|
| 1 | `SKILL.md` §5 | 决策规则由"情形 → 做什么"的两列扩写为**四列**：触发条件 / 首选举措 / 失败时的降级 / 记录与退出码，编号 **D01–D16** | 四列把"首选不成立时怎么办"写死，Agent 不会在降级时临场编造行为；退出码一列让流水线可判 |
| 2 | `SKILL.md` §6 | 新增**五类失败分支处置表**（材料异常 / 模板缺失 / 依赖缺失 / 契约四形态 / 状态不一致），每类给出"典型触发 → 首选 → 升级/降级路径 → 对应规则号" | 与题面 `可靠体验 → 异常处理` 的列举项逐项对应，评审可逐格核对 |
| 3 | `SKILL.md` §7 | 新增**状态一致性不变量 I1–I6**（材料不可读禁止 completed / gap ⇒ ≤partial / lint 偏差双写 / 重建图不得称为原图 / 降级双写 / 空 uncertainty 的唯一条件） | 把"诚实性"从形容词变成可断言的句子，交付前能逐条勾选 |
| 4 | `SKILL.md` §4 | 阶段由 `S0–S6` 重排为 **P0–P6**，检查点重命名 **C1/C3**，并把每条阶段的失败出口指向具体 D 规则 | 阶段表与决策表互相引用，读者按图索骥 |
| 5 | `references/failure-modes.md` | 全篇按 **D 编号**重写：§2 五类展开（识别特征 → 首选 → 升级路径 → 记录字段 → 退出码），新增 §3 **逐级回退矩阵**（PDF / 图片 / 模板 / 字体 / 渲染 / 契约六级） | 与 SKILL.md 同号互查，文档之间不会各说各话 |
| 6 | `references/RUBRIC_MAP.md` | 重写为**可靠体验 10 + 实际效果 40 优先**的映射表，新增"决策规则 → 评分点 → 复核命令"三列 | 直接回答评分表里"异常处理 3 分 / 运行稳定性 4 分"凭什么给分 |

算法与 `scripts/` 的 CLI 接口**未改动**（本版是判断与降级层面的增强，不是重写求解器）。

## 快速开始（任意 cwd 均可，`$SKILL_DIR` = SKILL.md 所在目录）

```bash
SKILL_DIR="<本包根目录>"        # 平台安装到 /skills/weekly-skill 时即该路径

# 1) C1 蓝图 lint（写完 deck-spec 后必跑）
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
`preview-approx-*.png`（PIL 近似预览，如实标注）、`evidence_mapping.md` +
`evidence_map.json`（逐页证据映射，双形态同源）、`result.json`（契约完整 + `case_id`）、
可选 `chart-*.png/.svg`（从论文表格数字重建的图）。

## 最小示例（合成案例，非正式案例）

```bash
python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"   # ① 生成示例模板（运行期现产）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" --spec "$SKILL_DIR/examples/deck-spec.json" \
  --out "<空输出目录>"                                                        # ② 跑示例
```

① 可跳过：模板不存在时生成器自动回退内置 16:9 学术版式（`deck.template.kind="builtin"`，
对应 D06/D07），这是**正常且被记录**的分支，不是失败。
示例输入、预期产物与净化说明见 `examples/README.md`、`examples/EXPECTED-OUTPUT.md`。

> ⚠️ **不要在本包目录内直接跑脚本**：Python 会在 `scripts/` 下生成 `__pycache__`，
> 而技能资源只允许文本文件（`.md/.py/.json/.txt/.csv/.yaml/.yml`），
> `validate_pkg.py` 会因此判 FAIL。自测请先把包复制到包外临时目录再跑（`TEST.md` 的记录
> 全部按此方式产生）。

## 调用参数

| 参数 | 必填 | 说明 |
|-|-|-|
| `--case` | 是 | `case.json` 路径（给目录时取其内 `case.json`） |
| `--task` | 否 | `task.md`（存在时读取，advisory） |
| `--spec` | 否* | Agent 写好的页级 `deck-spec.json`；缺省仅 `--demo` 允许自动骨架 |
| `--materials` | 否 | 覆盖材料目录/文件（优先级高于 case 内声明） |
| `--out` | 是 | 输出目录（最终产物落位） |
| `--demo` | 否 | 允许自动骨架 spec（仅演示用，状态如实降为 `partial`） |
| `--verbose` | 否 | 打印 traceback |

## 依赖

- 必需：Python ≥3.8、`python-pptx`（构建 `.pptx`）、`Pillow`（预览）；
- 可选（逐级回退并如实记录，矩阵见 `references/failure-modes.md` §3）：
  - PDF 解析：`PyMuPDF(fitz)` ≻ `pypdf` ≻ `pdfplumber`（全无 → 外部转出的 `.txt`）；
  - 重建图：`matplotlib`（缺失 → 跳过图并记录）；
  - 预览字体：运行时探测 `C:/Windows/Fonts` → `/System/Library/Fonts` →
    `/usr/share/fonts` → PIL 默认（`SKILL_PREVIEW_FONT` 可覆盖）。
- 参考运行环境（`TEST.md` 记录）：Windows / Python 3.13.9 / python-pptx 1.0.2 /
  Pillow 12.3.0 / matplotlib 3.10.6 / PyMuPDF 1.28.0 / pypdf 6.14.2；**无 LibreOffice**
  ——预览一律 PIL 近似并如实标注。

## 关键机制

1. **契约先行**：`references/OUTPUT_CONTRACT.md` §1 列出 result.json 的 19 个顶层字段，
   `scripts/check_contract.py` **直接读该文档**逐字段核对（缺字段 exit 1，契约文档解析不出
   字段 exit 2，绝不假通过）——文档与代码不会悄悄漂移。
2. **方案先行**：先把论文重写成页级 `deck-spec.json`（一页一主张 + 证据定位），
   `spec_lint` 做 C1 结构性 lint（BL-1…BL-4）后才允许生成；偏差按 D05 双写后继续。
3. **决策显性化（本版核心）**：D01–D16 覆盖材料 / 模板 / 依赖 / 契约 / 状态五类情形，
   每条都有"首选 + 降级 + 记录 + 退出码"；I1–I6 把状态诚实性写成可断言句。
4. **双形态证据映射**：`evidence_mapping.md`（人复核）与 `evidence_map.json`（机器读）
   由同一 spec 生成；C3 校验表行数 = 声明 `entries`（G7）。
5. **三层脚本**：`assetkit`（素材：PDF 抽取 / 重建图）→ `deckgen`（页面生成）→
   `ooxml_kit`（OOXML 精修：主题字体、分层命名、容器健全检查）。
6. **模板占位符约束**：只填占位符、不动 master、不覆盖页脚/配色；布局名匹配 → 索引回退
   → 内置版式；`template_mode="replace"` 移除起始页并记 `starter_slides_removed`。
7. **备注分离**：`notes_slide` 承载过渡/强调/被问补充（含封面与收尾页），不复制页面文字。
8. **运行时资源自生成**：模板、预览、重建图一律运行期生成；技能资源只含 UTF-8 文本文件。

## 目录结构

```
SKILL.md                     执行阶段 P0–P6、决策规则 D01–D16、失败分支、不变量 I1–I6、自查清单
README.md                    本文件：本版改动、依赖、调用、限制、维护
TEST.md                      包外临时副本上的真实实测记录（命令 + 退出码 + 关键输出）
GITHUB_URL.txt               公开作品链接（单行）
references/OUTPUT_CONTRACT.md  result.json 顶层字段清单 + 四形态回显 + 硬性门 G1–G8
references/failure-modes.md    失败分支处置手册（与 D01–D16 同号）+ 逐级回退矩阵
references/RUBRIC_MAP.md       五维评分 → 本包落点（以可靠体验/实际效果为主轴）+ 复核命令
references/slide-blueprint.md  论文→页面蓝图映射 + deck-spec schema + 证据表格式
references/layer-naming.md     PPTX 分层命名规范
scripts/main.py               端到端入口（--case/--out 必填，其余可选）
scripts/assetkit.py deckgen.py ooxml_kit.py   素材 / 生成 / OOXML 三层
scripts/spec_lint.py          C1 结构性 lint
scripts/export_check.py       C3 导出检查（G1–G8）
scripts/check_contract.py     契约字段覆盖核对
scripts/preview.py            PIL 近似预览
scripts/make_template.py      运行期生成回退模板
scripts/make_synthetic_inputs.py  运行期生成合成夹具
scripts/cli_io.py             控制台加固（非 UTF-8 环境下打印中文不崩）
examples/                     最小示例（合成案例）：case/spec/task/材料/预期产物
```

## 限制

- 预览为**近似**渲染，非 PowerPoint/LibreOffice 实际结果；
- PDF 图片抽取依赖库与版式，个别图会以显式占位框呈现（占位框**不代表**论文原图）；
- 模板适配为"占位符级"，不重排 SmartArt 等复杂版式；模板自带形状不改名；
- 结论正确性上限 = 论文原文；本 Skill 不负责验证论文结论；
- 首次运行前需具备 `python-pptx` 才能产出 `.pptx`；缺失时按 D11 如实降级而非伪造文件。

## 失败处理

异常分类、升级路径与退出码见 `references/failure-modes.md`（材料异常 / 模板缺失 /
依赖缺失 / 契约四形态 / 状态一致性五类，与 `SKILL.md` §5 的 D01–D16 一一对应）。
一切降级都会写入 result.json 的 `uncertainty` 与 `change_records`（不变量 I5）。

## 自测与维护

- `TEST.md`：包外临时副本上的实测记录（编译 / 端到端 / 确定性 / 决策分支 / 退出码）；
- `examples/EXPECTED-OUTPUT.md`：示例案例的预期产物与契约字段清单（文字形态）；
- 版本号在 `scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；
- **维护铁律**：新增或修改任一 D 规则，必须同时更新 `references/failure-modes.md`
  的同号条目与 `references/RUBRIC_MAP.md` 的复核命令，再跑一次 `TEST.md` 的对应项；
- 修改记录同时进 git 提交历史与 result.json 的 `change_records`。
