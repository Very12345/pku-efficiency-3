# CHECK-INDEX — 全部检查名清单（文档 ↔ 代码 的唯一对照表）

> **本文件在 v6（全维合并版）里承担三重身份**：
> ①`scripts/doccheck.py` 的对照事实来源；②`references/MECHANISM.md` 里
> M1–M5 每条"可证伪判据"的**取值来源**（M1 用 `spec.relation_kind` /
> `spec.containment_group`；M4 用 `bitmap.dpi_print` / `svg.editable_text` /
> `artifact.<role>`；M5 用 `font.cjk` / `verification.render`）；
> ③`references/GAIN-PROTOCOL.md` 里 I1–I10 每个指标的数据来源
> （`svg.*`→I3、`bitmap.*`/`pdf.*`/`font.cjk`→I8、`legend.*`→I6、
> `data_mapping.*`→I7、`traceability.*`→I4、`spec.relation_kind`→I5，
> 而 I1 的唯一读数是外部命令 `validate_result.py` 的退出码）。
> **名称与级别以 `scripts/` 的真实实现为准**，本表与代码不一致时按代码修表。

`scripts/*.py` 在 `result.json.verification.checks`、`spec_lint` 的 issues
列表和编辑日志里，用**带点的小写标识符**（形如 `spec.relation_kind`）报出
每一项检查。本文件把这些标识符**全部列出来**，每条写清它属于哪个检查点、
能取什么级别、以及它在科学上意味着什么。

为什么要有一份完整清单：文档里少写一个检查名，复核者就少一个抓手；
文档里**多写**一个代码根本不产出的检查名，则是"承诺了做不到的事"。
两者都由 `scripts/doccheck.py` 自动对拍（`--json` 可机器读），
本文件是它的事实来源。

## 0. 级别语义

| 级别 | 含义 | 对 `status` 的影响 |
|-|-|-|
| `fail` | 硬失败：该检查点是门，必须修完重跑 | 使 `status` 降为 `partial`（若为 `success` 则违反 G2） |
| `warn` | 软提示：能力受限或需人工确认 | 不改变 `status`；应逐条在 `acknowledged_issues` 或 `uncertainty` 中交代 |
| `ok` | 通过 | 无 |
| `info` | 记录型信息（不是判定） | 无 |
| `n/a` | 不是检查名，只是在脚本里出现的同形字符串（已注明） | 无 |

> **G2 的硬语义**：`status=success` 时 `verification.checks.fail_count` 必须为 0，
> 且 CP1 的 `spec_lint.valid` 不为 false。这条由 `scripts/validate_result.py` 独立校验，
> 不依赖脚本自己的汇总。

## 1. CP1 生成前 lint（`scripts/spec_lint.py`）—— 画之前就拦（机制 M1 的判据来源）

| 检查名 | 级别 | 含义 |
|-|-|-|
| `spec.entities` | fail | schematic 缺 entities 列表（无法构成关系图） |
| `spec.entity_id` | fail | 实体缺 id 或 id 重复 |
| `spec.entity_name` | fail | 实体缺 name（图面将无标签） |
| `spec.traceability` | warn | 实体有 source 但无 evidence 摘录，或两者都缺 |
| `spec.relation_from` | fail | 关系 from 指向不存在的实体 id |
| `spec.relation_to` | fail | 关系 to 指向不存在的实体 id |
| `spec.relation_kind` | fail | 关系 kind 映射不到 7 类规范词表 |
| `spec.relation_dict` | fail | 规范类别在 relation-dict.json 里没有连接规则 |
| `spec.relation_source` | warn | 关系缺 source 定位 |
| `spec.relation_selfloop` | warn | 关系自环（from == to），需确认方向 |
| `spec.containment_arrow` | fail | containment 被画成箭头（必须用分组框） |
| `spec.containment_group` | fail | containment 关系未被任何分组框覆盖 |
| `spec.group_member` | fail | 分组成员不是已存在的实体 id |
| `spec.legend_missing_kinds` | fail | 图面画了某类箭头但图例里没有它 |
| `spec.data_rows` | fail | chart 的 data.table.rows 为空 |
| `spec.data_category` | fail | category_col 不在表列名里 |
| `spec.color_category_count` | fail | 调色板颜色数 < 唯一类别数 |
| `spec.data_unit` | warn | chart 未声明单位 |
| `spec.data_mapping` | ok | schematic 走图例一致性，无额外数据映射门 |
| `spec.canvas_bounds` | warn | 画布尺寸过小（按实体/关系数估算需求后提示） |
> `spec.*` 里 `fail` 的都是**门**：`main.py` 会把它们的明细并入
> `verification.checks.fails`（名字前缀 `spec_lint.`），并把 `status` 降为 `partial`。
> 例：`spec.relation_kind` fail → `verification.spec_lint.valid=false`，
> `fails=[{"check":"spec_lint.spec.relation_kind", ...}]`。

## 2. CP2 产物检查（`scripts/checks.py`）—— 画完即核验（机制 M4/M5 的判据来源）

| 检查名 | 级别 | 含义 |
|-|-|-|
| `svg.exists` | fail | SVG 源文件未生成 |
| `svg.readable` | fail | SVG 无法按 XML 解析 |
| `svg.editable_text` | fail | 文字被 path 化（不可选中），或没有任何 <text> |
| `svg.layers` | fail | 缺少语义图层分组（layer-*） |
| `svg.manifest_embedded` | fail | SVG 里没有内嵌 ER 清单 |
| `svg.manifest_matches` | fail | 内嵌清单与本轮 manifest 不一致 |
| `svg.data_entity_attrs` | warn | 实体节点缺 data-entity 溯源属性 |
| `svg.data_relation_attrs` | warn | 关系边缺 data-relation 溯源属性 |
| `svg.data_source_attrs` | warn | 元素缺 data-source 出处属性 |
| `svg.title_exists` | warn | SVG 缺 <title> |
| `bitmap.exists` | fail | PNG 预览未生成 |
| `bitmap.readable` | fail | PNG 无法打开 |
| `bitmap.pil` | warn | 无 Pillow，无法验证像素尺寸（降级记录，不阻塞） |
| `bitmap.dimensions` | ok | PNG 像素尺寸在预期范围内 |
| `bitmap.dpi_print` | warn | 18 cm 宽下的有效 DPI 低于印刷/屏幕阈值 |
| `bitmap.colourspace` | warn | 色彩模式不是 RGB 族 |
| `pdf.exists` | fail | PDF 导出件未生成 |
| `pdf.readable` | fail | PDF 头不可读 |
| `pdf.header` | warn | PDF 文件头异常 |
| `pdf.pages` | warn | PDF 页数异常 |
| `pdf.fonts_embedded` | warn | 字体嵌入审计（尽力而为，非绝对判定） |
| `legend.missing_kinds` | fail | 图面出现的箭头类型在图例里缺项 |
| `legend.orphan_items` | warn | 图例有条目但图面没有对应箭头（孤儿项） |
| `data_mapping.color_count` | warn | 颜色数对不上类别数 |
| `data_mapping.legend_consistency` | **fail** | 渲染出的图例类别 ≠ 数据表类别（非 chart 时为 ok 并转交图例一致性检查） |
| `data_mapping.rows` | **fail** | chart 的 `data.table.rows` 为空（无数据可画） |
| `data_mapping.unit` | warn | 单位未上轴或缺失 |
| `traceability.entities` | warn | 带 source+evidence 的实体比例 |
| `traceability.relations` | warn | 带 source 的关系比例 |
| `traceability.data_table` | warn | 数据表来源定位比例 |
| `font.cjk` | warn | CJK 字体可用性（缺失时 PNG 可能缺字，SVG 文字仍在） |
| `artifact.figure` | fail | role=figure 产物缺失（可编辑源） |
| `artifact.preview` | fail | role=preview 产物缺失（预览） |
| `artifact.pdf` | fail | role=pdf 产物缺失（导出件） |
| `pipeline` | fail | 流水线级致命错误（清单缺失、渲染异常等） |
> `artifact.<role>` 中 role ∈ {figure, preview, pdf, tiff, eps}；缺哪个就报哪个。
> 未生成对应格式时该 role 不参与检查（不会凭空报 fail）。
> `pipeline` 是流水线级 fail 的专用名字（清单缺失、渲染异常），它出现即表示
> 本次没有可评审的图稿。

## 3. CP4 编辑路径问题（`scripts/edit.py`）——编辑动作的字段级判据

| 检查名 | 级别 | 含义 |
|-|-|-|
| `edit.form` | fail | 编辑条目不是对象 |
| `edit.unknown_action` | fail | 编辑 action 不在支持列表内 |
| `edit.add_entity` | fail | add_entity 的实体 id 已存在 |
| `edit.remove_entity` | fail | remove_entity 指向不存在的实体 id（字段名 entity_id） |
| `edit.rename` | fail | rename 指向不存在的实体 id（字段名 entity_id） |
| `edit.relabel` | fail | relabel 指向不存在的关系 id（字段名 relation_id） |
| `edit.flip` | fail | flip_direction 指向不存在的关系 id（字段名 relation_id） |
| `edit.change_kind` | fail | change_kind 指向不存在的关系 id（字段名 relation_id） |
| `edit.remove_relation` | fail | remove_relation 指向不存在的关系 id |
| `edit.update_value` | fail | update_value 缺 entity_id/relation_id 或 field |
> **重要如实说明**：这些 `edit.*` 问题目前只出现在 **stdout 日志**里，
> 不会写入 `result.json`，也**不会**改变退出码。因此"编辑请求被拒"这件事
> 必须由 Agent 用 `change_records` 条数自行对拍（见 SKILL.md D10 与
> `references/EDIT-ACTION-SCHEMA.md` §3）。本文件把它写清而不是掩盖。

## 4. 规范化阶段的同形字符串（`scripts/manifest.py`）——**不是检查名**

| 检查名 | 级别 | 含义 |
|-|-|-|
| `entity.name` | n/a | manifest.py 里的 entity.name 是日志文本片段（告警/补全记录），不是可对拍的检查名 |
| `relation.from` | n/a | manifest.py 里的 relation.from 是日志文本片段（告警/补全记录），不是可对拍的检查名 |
| `relation.to` | n/a | manifest.py 里的 relation.to 是日志文本片段（告警/补全记录），不是可对拍的检查名 |
| `relation.kind` | n/a | manifest.py 里的 relation.kind 是日志文本片段（告警/补全记录），不是可对拍的检查名 |
| `relation.selfloop` | n/a | manifest.py 里的 relation.selfloop 是日志文本片段（告警/补全记录），不是可对拍的检查名 |
| `group.member` | n/a | manifest.py 里的 group.member 是日志文本片段（告警/补全记录），不是可对拍的检查名 |
## 5. 对拍命令

```bash
# 文档承诺 vs 脚本事实（默认检查技能根；只读、无副作用）
python "$SKILL_DIR/scripts/doccheck.py"
python "$SKILL_DIR/scripts/doccheck.py" --json          # 机器可读
python "$SKILL_DIR/scripts/doccheck.py" --files SKILL.md references/RUBRIC_MAP.md
# 退出码：0 = 无 FAIL；1 = 有 FAIL（文档承诺了代码没有的东西）；2 = 参数/环境错误
```

`doccheck.py` 还会校验：D 规则编号连续无缺号、每条规则至少被定义与引用各一次、
文档点名的每个 `--flag` 都在 `add_argument()` 里真实存在。
