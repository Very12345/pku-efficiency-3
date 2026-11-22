# graphical-abstract — 图形摘要 Skill（文档轴 A：决策显性化）

依据固定科研材料生成或编辑可复用的单页科研图稿：实体/关系/数据**逐元素可溯源**
（`data-src`）、四要素（研究问题 → 方法 → 核心结果 → 结论）单页可读、同输入同布局，
交付**可编辑分层 SVG 源** + PNG/PDF 预览 + 可复核的 `result.json`。

本包相对通用做法的主要差别不在"画得更好看"，而在**异常处置是可预期的**：
`SKILL.md` §4 给出 20 条决策规则 D1–D20（触发条件 → 动作 → 失败时的降级 → 记录位点），
§5 按五类给出失败分支表（材料异常 / 模板缺失 / 依赖缺失 / 契约四形态 / 状态不一致），
`references/failure-modes.md` 用同一套编号给出**检测点、验证命令与证据字段**。
三者可直接互查：从退出码或某个字段就能反查到"本该走哪条规则"。

**包内只有文本资源**（`.md/.py/.json/.txt`）：无二进制、无预置 `.svg/.png/.pdf`、无字体文件、
无 `__pycache__`、无本机绝对路径。SVG 与渲染件一律**运行期生成**；模板 = 代码 + 文本规格。

## 0. 自定位（写作前提）

所有命令以 `$SKILL_DIR`（本文件所在目录）为基准，**不要求 cwd = 技能根**：

```bash
SKILL_DIR=/skills/weekly-skill        # 官方评测容器
SKILL_DIR=/abs/path/to/<skill-root>   # 本机解压位置
# 不确定时向上探测
SKILL_DIR="$(pwd)"; while [ ! -f "$SKILL_DIR/SKILL.md" ] && [ "$SKILL_DIR" != "/" ]; do SKILL_DIR="$(dirname "$SKILL_DIR")"; done
```

## 1. 五步跑通

```bash
# ① 方案先行（推荐）：生成方案骨架（已带真实抽取的实体/关系/数据与来源定位）
python "$SKILL_DIR/scripts/scaffold.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/plan.json
#    → 读材料后填 plan.four_elements（四句"一句话说明"），必要时删减上画布元素

# ② CP1：方案 lint（绘制前门；exit 0 才继续）
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan /tmp/plan.json

# ③ 出图（带定稿方案；不带 --plan 则走默认流程）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
       --plan /tmp/plan.json --out /tmp/ga-out

# ④ 契约自查（exit 0 = 顶层覆盖信封 ∪ 案例契约且无 null）
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/ga-out/result.json \
       --case "$SKILL_DIR/examples/case.json"

# ⑤ 规格 lint 独立复跑（已由 main.py 内嵌执行过一遍）
python "$SKILL_DIR/scripts/spec_lint.py" --spec /tmp/ga-out/spec.json --content /tmp/ga-out/content.json
```

官方案例形态（平台挂载输入、产物写 `/app/output`）：

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
```

`/tmp/ga-out` 下应有：`<case_id>_graphical_abstract.svg`（可编辑分层源）、
同名 `.png` / `.pdf`（预览，后端如实记录）、`spec.json`、`content.json`、
`audit.json`、`render_log.json`、`result.json`。

## 2. 参数

| 参数 | 说明 |
|-|-|
| `--case` | `case.json` 路径（必填） |
| `--task` | `task.md`（缺省自动找 `<case_dir>/task.md`） |
| `--material` | 材料文件或目录（缺省用 `case.source_material`） |
| `--plan` | 设计方案 `plan.json`（`scaffold.py` 生成、Agent 定稿；可选） |
| `--raster-scale` | PNG 分辨率倍率（默认取 `figure_constraints`） |
| `--pdf` / `--no-pdf` | PDF 预览开关（默认取 `figure_constraints`） |
| `--out` | 输出目录（默认 `<skill>/out`） |

## 3. 依赖

- **必需**：Python ≥ 3.8；核心流程只用标准库（可出纯 Python PNG）；
- **可选（逐级回退并如实记录）**：`matplotlib`（默认渲染 + PDF）、`Pillow`（二级渲染）；
- **字体**：运行期按候选路径探测系统字体（`C:/Windows/Fonts`、`/usr/share/fonts`、
  `/System/Library/Fonts`），找不到就降级并把字体名写进 `render_log.json`；**SVG 内 `<text>`
  始终是真文字**，因此可编辑性不随渲染降级而丢失；
- **不联网**：不下载模板/字体/数据；
- 本机实测环境与结果见 `TEST.md`（Python 3.13.9 / matplotlib 3.10.6 / Pillow 12.3.0）。

## 4. 异常处置索引（本包的核心）

| 你想知道 | 去哪里看 |
|-|-|
| 某条规则完整定义（触发条件/动作/降级/记录位点） | `SKILL.md` §4（D1–D20，按输入/材料/依赖/契约/状态分组） |
| 五类失败分支的处置与证据字段 | `SKILL.md` §5 |
| 怎么检测、怎么验证、留了什么证据 | `references/failure-modes.md` §2（同号对照矩阵） |
| 退出码到底代表哪个阶段 | `references/failure-modes.md` §1 |
| 出问题了先看什么 | `SKILL.md` §6「三分钟分诊」 |
| 表外情形怎么办 | `references/failure-modes.md` §7「先记后判」 |

三条与科学诚实性相关的红线（优先于任何版面优化）：**缺数值只占位不编造**（D5）、
**材料矛盾的数值不平均不择优**（D7）、**结论必须能在材料中找到对应表述**
（`references/ga-four-elements.md` §2）。

## 5. 关键机制

1. **方案先行**：`scaffold.py` 出骨架（含 `src` 定位）→ Agent 填 `four_elements` →
   `spec_lint --lint-plan` 通过后才绘制；把"画什么、证据在哪"变成可 lint 的中间产物；
2. **四要素不变式**：Q-M-R-C 必齐 + 阅读顺序 + 面板要点按语义归位
   （`references/ga-four-elements.md`；`audit.four_element_coverage` 执行检查）；
3. **图层命名契约**：7 层 `layer:*` + `data-src/data-role/data-panel`
   （`references/layer-naming.md`；`audit.layer_naming` 执行检查）；
4. **双 lint 门**：绘制前方案 lint + 绘制后规格 lint，两边结果都进 `result.json`；
5. **契约四形态回显**：`""`/`[]`/`false`/`{}`，禁 null；`check_contract.py` 提供 exit-code 判据；
6. **确定性布局**：同输入同 `spec`（`audit.determinism_probe`），排版不漂移；
7. **资产三件套**：`assets/spec_template.json`（方案起点）、`assets/result_example.json`
   （结果示例）、`assets/example_material.txt`（材料写法样例）。

## 6. 限制

- 渲染后端可能降级为 Pillow 或纯 Python PNG（文字占位），降级一律记录但会影响预览观感；
- 实体抽取依赖材料文本结构，复杂表格/多图材料需人工复核；
- 四要素/图层/覆盖率是结构判据，不代替领域科学判断；
- `examples/` 为合成示例（标注"示例，非正式案例"），与平台正式案例无关。

## 7. 维护

- 版本号在 `scripts/common.py` 的 `SKILL_VERSION`；变更记录见 git 与 `result.json.change_records`；
- 新增图层/新元素类型：先登记 `references/layer-naming.md` §1/§2，再同步 `scripts/audit.py`
  的 `EXPECTED_LAYERS` 与角色前缀，最后跑 audit 确认 `layer_naming` 全绿；
- 新增决策规则：在 `SKILL.md` §4、§5 与 `references/failure-modes.md` §2、§3 **四处同号补齐**，
  编号连续；只补一处视为未完成。
