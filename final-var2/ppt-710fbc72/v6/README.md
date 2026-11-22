# README — Academic Slide Adapter（学术 PPT 模板与格式适配 · 全维合并版 4.0.0）

> **本包是 union 包**：v1（决策显性化）∪ v2（增益可验证）∪ v3（机制可证伪）∪
> v4（失败注入演练）∪ v5（多案例泛化题集）的全部实质内容，重排为
> **输入 → 执行 → 失败 → 增益 → 机制 → 复用** 六个部分（见 `SKILL.md` §0 的读法索引）。
> 五个入口：`scripts/main.py`（主流程）· `run_case_set.py`（题集）·
> `fault_inject.py`（演练）· `validate_result.py` / `check_contract.py`（契约门）。
> **文件数 50（上限 50）** ⇒ 同主题 reference 已合并（`batch-rules.md` 全文并入
> `checklist.md` 附章；另两份的全文并入 `failure-modes.md` 附录 A 与
> `two-phase-workflow.md` 附录 B），**内容一字未删**。

`ppt-710fbc72`（玻尔产品周赛·北大专区·学术效率）的本地可运行 Skill 包。

一句话：**把论文/研究材料变成合模板、可编辑、证据可追溯的学术汇报；并把这套做法
拆成六个可单独证伪的机制与六类可单独复用的资产。**

本版本的读法是"先机制、再资产、后流程"：`references/MECHANISM.md` 用固定四段
结构（机制 / 落点 / **没有它会怎样** / **可证伪判据**）讲清 M1–M6；
`references/REUSABLE-ASSETS.md` 把包内资产按可复用单元列出（含 `--help` 逐字一致
的参数与复用后会继承的保证）；`references/GAIN-PROTOCOL.md` 给公平对照协议与作者
真实跑过的数据。**每个机制都配一条能被第三方复跑推翻的检查**——这是它与"功能
列表"的区别。

## 六个机制一览

| # | 机制 | 落点 | 没有它会怎样（一句） |
|-|-|-|-|
| M1 | 方案先行 | `scripts/adopt_plan.py` → `adopt_plan.json` | 出错只能整册返工，无中间判据可核 |
| M2 | 契约先行 + CP3 G1–G8 | `references/OUTPUT_CONTRACT.md` · `scripts/check_contract.py` | 缺件与 `null` 占位只能靠人眼发现 |
| M3 | 证据定位绑定 | `scripts/extract.py` · `scripts/audit.py` | 页面"看起来对"，数字无法回溯 |
| M4 | 方案↔执行一致性 | `scripts/adapt_pptx.py` → `adopt_plan_deviations` | 方案与产物脱钩，M1 变装饰 |
| M5 | 二进制运行时生成 | `scripts/make_template.py` · `make_synthetic_inputs.py` | 往包里塞二进制 ⇒ 可能整包被拒收 |
| M6 | 确定性字节 | `scripts/pptx_toolkit.py` 的 `deterministic_zip()` | 哈希每次都变，"跑出来的"不可核 |

## 运行方法

环境：Python 3.9+；运行依赖 `python-pptx`、`Pillow`。
本机实测环境：Python 3.13.9 / python-pptx 1.0.2 / Pillow 12.3.0 / numpy 2.3.5。
无 LibreOffice / PowerPoint 时预览为 PIL 示意图（如实标注，**不产伪 PDF**）。

`$SKILL_DIR` = 本包根目录（平台装到 `/skills/weekly-skill`）。**下面所有命令在
任意 cwd 下都能跑**：脚本用 `os.path.dirname(__file__)` 自定位，不依赖 cwd。

一键全流程：

```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> --task <task.md> --out <out>
```

平台正式运行（材料相对路径在 `/app/work` 内解析）：

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
    --work /app/work --out /app/output
```

显式指定模板 / 起始 deck：

```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> --template <模板.pptx> --out <out>
python "$SKILL_DIR/scripts/main.py" --case <case.json> --starting-deck <现有deck.pptx> --out <out>
```

跑通自带示例（示例图不随包 —— 这条命令本身就是 M5 的演示）：

```bash
SKILL_DIR=<本包根目录>; RUN=<任意可写目录>
cp -r "$SKILL_DIR/examples" "$RUN/examples"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"
```

## 复用入口（只拿一层也行）

三个场景的完整命令见 `references/REUSABLE-ASSETS.md` §8，这里给入口：

### 场景 1 — 只用模板适配层（自带内容管线）

```bash
RUN=<可写目录>; TPL=<你的模板.pptx>; CASE=<你的case.json>
python "$SKILL_DIR/scripts/extract.py"  --case "$CASE" --out "$RUN"
python "$SKILL_DIR/scripts/deckplan.py" --content "$RUN/content.json" --out "$RUN"
python "$SKILL_DIR/scripts/adopt_plan.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --template "$TPL" --out "$RUN/adopt_plan.json"
python "$SKILL_DIR/scripts/adapt_pptx.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --adopt-plan "$RUN/adopt_plan.json" --out "$RUN/deck.pptx"
```

### 场景 2 — 接进已有管线（只要方案与校验）

```bash
python "$SKILL_DIR/scripts/adopt_plan.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --template "$TPL" --out "$RUN/adopt_plan.json"
python "$SKILL_DIR/scripts/check_contract.py" --result "$RUN/out/result.json" \
    --out-dir "$RUN/out" --case "$CASE"      # exit 0 且 {"valid": true} 才算过
```
> `check_contract.py` 会**自己重开 pptx、自己扫产物清单**，因此对你自己的产物
> 同样有效 —— 不依赖本包的生成器。

### 场景 3 — 当作对照基线（做自己的增益实验）

```bash
cp -r "$SKILL_DIR/examples" "$RUN/input"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/input"
python "$SKILL_DIR/scripts/make_template.py" --out "$RUN/input/tpl/template.pptx"
# 令 case.json.template = "tpl/template.pptx"（两臂都从该字段解析模板 —— 关键）
python "$SKILL_DIR/scripts/main.py" --case "$RUN/input/case.json" \
    --task "$RUN/input/task.md" --out "$RUN/armB/out"
```
**最容易出错的一步**：让两臂共用同一份模板。若 B 臂的
`template_audit.opened_from` 是 `builtin` 而非 `case_template`，说明"同模板"没
落实，对照无效（见 `references/GAIN-PROTOCOL.md` §3 C2 与 §8 清单）。

## 参数语义（容易踩的两个坑）

- **`--out` 语义不同**：`extract / deckplan / preview / audit` 收**目录**；
  `adopt_plan / adapt_pptx / make_template` 收**文件**（与各脚本 `--help` 一致）。
- **`audit.py` 的 `--out` 是产物目录**（里面应有 deck 与 result.json），不是报告
  文件路径。

## 退出码语义

| 退出码 | 含义 | 典型触发 |
|-|-|-|
| **0** | 流程完成（**不等于**全绿：`status` 可能是 `partial`） | 正常结束；`validate_result.py` 打 `VALID`；`check_contract.py` 打 `{"valid": true}` |
| **1** | 流水线失败 | case 不可解析、无可用模板、依赖缺失导致构建失败、保存失败 |
| **2** | `--out` 不可写 / 参数错误 | 输出路径是普通文件或无权限 |

退出码 0 时**仍必须**读 `result.json.status`。

## 输入说明（case.json 主要字段）

| 字段 | 说明 |
|-|-|
| `case_id / title / subtitle` | 案例标识 / 讲稿标题 / 副标题 |
| `research_question / methods / results / discussion / limitations / conclusion` | 各环节主张数组；每项可带 `text`+`source`（`文件:行`）或 `figure_refs`/`table_refs` |
| `figures` | `[{id, file, caption, source}]`；`file` 相对 case 目录解析 |
| `tables` | `[{id, caption, source, rows}]`（rows 为二维数组或 CSV 路径） |
| `audience / duration_minutes / slide_count / language` | 固定受众/时长/页数/语言（zh\|en） |
| `template / starting_deck / source_material` | 模板 / 起始 deck / 材料文件（可为数组） |
| `output_contract` | 交付契约对象（自动镜像进 result.json 顶层，四形态回显，**禁止 null**） |

## 输出说明

`<case_id>_deck.pptx`（可编辑源，含逐页笔记）· `<case_id>_cover_preview.png` +
`<case_id>_slides_contact_schematic.png`（PIL 示意图，**非像素级导出**）·
`adopt_plan.json`（阶段一方案，M1）· `result.json`（契约见
`references/OUTPUT_CONTRACT.md`）· `spec.json` / `content.json` / `audit.json` /
`render_log.json` / `summary.txt`；案例未给模板时另有 `_runtime/builtin.pptx`
（**运行时生成**，M5）。

`result.json` 顶层除信封字段外会把案例 `output_contract` 的**每个键**回显上去
（**禁止 null**）：已知语义的键取**本次运行真实值**，派生明细记在
`verification.contract_echo_derived`；PDF 导出类键恒 `false` —— 无
PowerPoint/LibreOffice 时不产伪 PDF。

## 限制与已知边界

- 预览是 **PIL 示意图**（`preview_is_schematic=true`），不是像素级导出；PDF 导出
  需 PowerPoint/LibreOffice，本机无。**因此"导出渲染一致性"测不到像素差异**；
- CJK 行高为估算，极端字体环境可能与 PowerPoint 实际排版有偏差（有溢出报告兜底）；
- 主题色/主题字体是**只读记录**（读 `theme1.xml`），不改写主题 XML；
- 内置回退模板主题的 ea（CJK）字体为空（python-pptx 默认模板特性）；
- 复杂 SmartArt / 艺术字 / 动画 / 切换不在范围；
- **确定性不等于"全文件逐字节"**：`result.json` 含 `generated_at`，且回退模板的
  来源措辞会从 `generated-at-runtime` 变为 `reused-generated`；本次实测 11/12
  （`TEST.md` §2）。核对一致性请看 **deck 与 PNG 的哈希**；
- **不代写科学内容**：材料里没有的数值、结论、图件绝不补造；
- 包内**无二进制资源**：模板与示例图由脚本运行时生成；
- **故障演练是伪造注入**（幽灵文件 / 半截 JSON / 假 `pptx`、`PIL` 包 / 篡改产物），
  不是真实生产故障；覆盖范围限 Windows 本机（`--out` 只读目录这一条在本机
  **无法验证**，已在 `references/FAULT-MATRIX.md` 标记 `HOST-DIFF`）；
- **题集是合成案例**，不是平台正式案例、不是白板、不能当分数预测；三案全部落在
  `opened_from=builtin`，**跨模板族未测**；案例 B 存在一处**已声明边界**（声明 12 页 /
  实测 13 页，根因见 `references/CASE-SET.md` §4.1）；
- **已知粗糙点 3 条**（缺图不改 status、`--task` 缺失无专属记录、内容侧降级不改
  status）如实列在 `references/FAULT-MATRIX.md` §4 与 `SKILL.md` §3.5，**未修复**。

## 目录

`SKILL.md` 主文档（输入→执行→失败→增益→机制→复用）· `scripts/`（**15 个**：
main / **run_case_set** / **fault_inject** / extract / deckplan / adopt_plan /
adapt_pptx / preview / audit / validate_result / check_contract / pptx_toolkit /
make_template / make_synthetic_inputs / common）· `references/`（**11 篇**：
OUTPUT_CONTRACT · RUBRIC_MAP · MECHANISM · REUSABLE-ASSETS · GAIN-PROTOCOL ·
**FAULT-MATRIX** · **CASE-SET** · failure-modes（含附录 A：B01–B24 全表）·
template_guide · checklist（含批量规则 R1–R8 附章）· two-phase-workflow
（含附录 B：命令↔规则对照））· `examples/`（最小示例 + `cases/` 三案例题集）·
`TEST.md` 实测记录（§0–§13）· `GITHUB_URL.txt`。

## 维护

- 版本：Skill `4.0.0`（union；`scripts/common.py` 的 `SKILL_VERSION` 仍记录脚本层的版本常量）。
- **新增机制时同步做三件事**：① `SKILL.md` §1 加行；②
  `references/MECHANISM.md` 加同号小节（机制 / 落点 / 没有它会怎样 / 可证伪判据）；
  ③ 若引入新的可复用单元，在 `references/REUSABLE-ASSETS.md` 加资产条目。
  **没有可证伪判据的机制不算机制。**
- 若改动了影响产出或字段的行为，须重跑 `references/GAIN-PROTOCOL.md` §5 的对照
  步骤并更新其 §6 实测记录，同时复核 `MECHANISM.md` 里引用的数字。
- 改动后至少复跑 `TEST.md` §1 冒烟与 §2 确定性；交付前用包外验收器
  `validate_pkg.py` 复核扩展名白名单、文件数、体积、无绝对路径。
- **永远不要在包内跑脚本**：会生成 `scripts/__pycache__`，触发合规硬门失败。
