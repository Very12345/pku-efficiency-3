# ASSET-INDEX.md — 可复用资产清单与复用步骤

> 这份清单回答：**本包里哪些东西可以原样搬到别的任务**、**搬的时候要改什么**、
> **搬完怎么验收**。每一项都注明文件、依赖、复用方式与"复用前必须替换的内容"。
> 目标读者：要做同类"材料 → 可核验图稿"任务的作者（不限于生物领域）。

## 1. 资产清单

| # | 资产 | 文件 | 依赖 | 复用方式 | 复用前必须替换 |
|---|---|---|---|---|---|
| A1 | 机制规格 schema（类型枚举 + 必需字段 + 端点引用检查） | `assets/mechanism-spec.schema.json` | 无（纯 JSON） | 直接作为"规格门"的判定表；`check_schema` 读它 | **实体/边类型枚举**与领域命名规则 |
| A2 | 调色板与 glyph 语义 | `assets/palettes.json` | 无 | 单点改色：图面与图例同步（改一处全图一致） | 颜色值、类型→形状映射、证据→线宽档位 |
| A3 | 箭头语义规范 | `references/legend-encoding.md` | 无 | 作为"图形元素=科学论断"的编码规范文档 | 语义表（激活/抑制/结合…换成新领域的语义集） |
| A4 | 关系核对清单（实体/边/图例/拓扑/导出五表） | `templates/relation-checklist-template.md` | 无 | 人工核验的执行载体（逐行填出处，作为核验证据） | 表头列（区室、证据强度等字段名） |
| A5 | 四个独立校验 CLI（各有明确退出码） | `scripts/check_contract.py`、`validate_figure.py`、`topology.py`、`legend_audit.py` | Python 标准库 | 直接拿去做"机器验收"：可作为评分脚本的客观依据 | 检查 id 与阈值（如线宽档位、图层命名约定） |
| A6 | 结果契约模板（信封 + 四形态回显 + G1–G8 门 + 状态一致性） | `references/OUTPUT_CONTRACT.md` | 无 | 抄成新任务的 `result.json` 契约；四形态回显规则可直接沿用 | 案例特有的 `output_contract` 字段与门的内容 |
| A7 | 绘制流水线骨架（规格 → 布局 → 分层 SVG → 预览 → 审计 → 契约） | `scripts/{main,model,layout,pathway_svg,mpl_backend,result_writer,extract}.py` | 标准库；PNG/PDF 需 matplotlib | 换掉布局规则与图元样式，保留流水线结构与退出码语义 | 区室定义、布局带规则、图元（节点形状） |
| A8 | 最小可运行示例 + 期望输出说明 + 实跑产物 | `examples/**`（`case.json`/`task.md`/`materials/`/`model.example.json`/`EXPECTED-OUTPUT.md`/`output/`） | 无 | 作为新任务的起步样例：改材料与规格即可跑通 | 示例材料与实体/边内容（**不得**抄进正式输出） |
| A9 | 失败分支表（F01–F22）+ 运行期决策捷径（K1–K10） | `SKILL.md` §3、`references/failure-modes.md` | 无 | 抄成本任务的失败处置清单（按五类组织：材料/资产/依赖/契约/状态） | 与领域相关的分支（如"跨膜受体区室"） |
| A10 | 机制与消融说明的写法 | `references/MECHANISM.md` | 无 | 作为"怎么论证创新点"的模板：每条机制给出"去掉它会怎样 + 可验证信号" | 机制条目本身 |
| A11 | 增益对照口径（同输入/同工具的判据组织方式） | `references/MECHANISM.md` §4 + `scripts/gain_probe.py` | 无 | 作为"怎么证明增益"的模板：指标必须与实现无关、两侧同法、缺项计 0 | 指标集 |
| A12 | 独立度量器（不 import 被测包） | `scripts/gain_probe.py` | Python 标准库 | `--dir <产物目录>` 单侧度量；`--compare A B` 出对照表与差值 | 指标定义（口径见 `MECHANISM.md` §4） |
| A13 | 基础形态复现器（反例生成器） | `scripts/baseline_emulator.py` | Python 标准库 | 给新任务造"基础条件"对照臂：平铺成环 + 统一箭头 + 无图例/无溯源/无契约 | 材料解析规则（表格首列）与画布尺寸 |

> **不建议照搬的**：`examples/` 的示例数据（合成教学数据，不是真实论文数据）、
> 本包 `result.json` 里的具体数值与 sha256（那是本机某次运行的痕迹）、
> 以及任何平台相关的分数或统计。资产可以搬，**痕迹不能搬**。

## 2. 三类典型复用场景

| 场景 | 搬什么 | 改什么 | 验收 |
|---|---|---|---|
| **同类机制图新题**（换材料、换通路） | A1–A9 全套 | 只换材料与规格；枚举与配色按新题微调 | 主路径 exit 0 + 两条审计 exit 0 + 故意失败用例 exit 3 |
| **其他领域的关系图/流程图**（非生物） | A2、A4、A5、A6、A7、A9 | **必须重定义**：实体/边类型枚举、区室等价物（分层带）、配色语义 | 同上，且要重跑"图例覆盖"与"端点引用"检查 |
| **只借校验能力**（已有自己的绘图实现） | A5（四个 CLI）+ A6（契约模板） | 让新实现输出同样的 `result.json` 字段与 SVG `data-*` 约定 | 用本包的两条审计命令跑新实现产物，看是否 exit 0 |

## 3. 复用三步（命令级）

```bash
# 步骤 1：搬骨架（把 scripts/ assets/ references/OUTPUT_CONTRACT.md 复制到新任务目录）
NEW=/path/to/new-task
cp -r "$SKILL_DIR/scripts" "$NEW/scripts"
cp -r "$SKILL_DIR/assets"  "$NEW/assets"
cp    "$SKILL_DIR/references/OUTPUT_CONTRACT.md" "$NEW/references/"

# 步骤 2：换语义（三个文件必须同步改，否则图例与图面会不一致）
#   assets/mechanism-spec.schema.json   ← 实体/边类型枚举
#   assets/palettes.json                ← 类型→颜色/形状、证据→线宽
#   references/legend-encoding.md       ← 语义表（保持"箭头=科学论断"原则）
#   另外把 examples/ 换成新任务的合成样例（材料 + case.json + model.example.json）

# 步骤 3：验一遍（四条命令，期望 0 / 0 / 0 / 3）
python3 "$NEW/scripts/main.py" --case "$NEW/examples/case.json" \
    --model-file "$NEW/examples/model.example.json" --out "$NEW/out"     # 期望 exit 0
python3 "$NEW/scripts/check_contract.py" --result "$NEW/out/result.json" \
    --case "$NEW/examples/case.json"                                     # 期望 exit 0
python3 "$NEW/scripts/validate_figure.py" --out "$NEW/out"                # 期望 exit 0
python3 "$NEW/scripts/main.py" --case "$NEW/examples/case.json" \
    --model-file "$NEW/bad-model.json" --out "$NEW/out-bad"              # 期望 exit 3（枚举外类型）
```

> 第 4 条是**故意失败用例**：它验证"门还活着"。如果它也返回 0，说明 schema 门被绕过
> （典型原因是先归一化再校验），必须修回来。

## 4. 迁移后的适配检查表

- [ ] 实体/边类型枚举已替换，且 `references/legend-encoding.md` 的语义表与之逐条对应；
- [ ] 调色板里的每个类型都能在图例里找到声明（图例覆盖是 fail 级检查）；
- [ ] 分层带的命名与语义已按新领域重定义（如"区室"换成"子系统/阶段"）；
- [ ] `examples/` 的样例已替换，且 `EXPECTED-OUTPUT.md` 的字段清单与新契约一致；
- [ ] 三条成功命令 + 一条故意失败命令的退出码符合期望（0/0/0/3）；
- [ ] 新任务的 TEST.md 记录了本次运行的环境、时间与读数（不要沿用本包的实测数字）；
- [ ] 契约里的 `output_contract` 字段名按新题面改写，四形态回显规则保持不变；
- [ ] 包里没有二进制、没有 `__pycache__`、没有本机绝对路径（合规硬门）；
- [ ] 若对外分享，删除本包示例数据与任何本机运行痕迹（sha256、路径、时间戳）。

## 5. 复用时的常见坑（来自本包的实测教训）

1. **把 `--materials-dir` 当成字符串参数**：argparse 的 `action="append"` 给的是 list；
   本包已做入参归一化（见 `worklog.md` §4）。搬脚本时不要把这个修复丢掉。
2. **先归一化再校验**：会让 schema 门形同虚设（M2 的整个价值就在这里）。校验必须在**原始规格**上做。
3. **图例与图面各改一半**：调色板、schema、语义表三处必须同步；否则 L01/L02/L05 会 fail。
4. **只搬到一半的流水线**：只搬渲染不搬审计，`success` 就退化成自我声明（M3/M6 的意义消失）。
5. **复用示例数据**：`examples/` 是合成教学数据，搬进正式输出等于伪造来源（反预制答案规则）。
