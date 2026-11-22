# failure-modes.md — 失败模式手册（按五个分支族组织）

> 本文件是 `SKILL.md` §7 分支表的展开版，与 `references/decision-rules.md`（D1–D20）一一对应。
> 组织方式从"平铺编号"改成了**五族**：材料异常（B-M）/ 模板缺失与冲突（B-T）/ 依赖缺失（B-D）/
> 契约四形态（B-C）/ 状态不一致（B-S）。每族先给分支表，再给该族的失败现象编号（F），
> 最后是状态一致性规则与实测证据。
>
> 统一纪律：**触发即记录**。命中任一 F，必须在 `change_records` 留 `{at, step, action}`；
> 导致能力缺失或结果不完整时，还必须在 `uncertainty` 留 `{item, impact, mitigation}`（皆非空）。

## 1. B-M 材料异常族

| 分支 | 情形 | 决策 | 处置 | 落点字段 | status |
|-|-|-|-|-|-|
| B-M1 | 声明材料不在盘 | D1 | 保留条目、`kind=missing`、相关页不规划 | `sources[]`、`uncertainty` | partial |
| B-M2 | PDF 无解析器 / 解析失败 | D2 | `parsed=false` + 原因；其余材料照常 | `sources[].note` | partial |
| B-M3 | 抽取丢公式/符号 | D3 | 以抽取文本为准并注明代理方式 | `evidence_audit.entries[].notes` | 记录 |
| B-M4 | 缺图 / 图损坏 | D4 | 页内诚实占位框；坏图跳过 | `pages[].figure_file`、`figure_bound` | 记录 |
| B-M5 | 材料为空 / 全不可解析 | D17 | 只出结构性页面 | `sources[].kind=none` | partial |
| B-M6 | 材料目录存在但为空目录 | D17 | 同 B-M5；并在记录里区分"空目录"与"无 materials 字段" | `change_records[step=material]` | partial |

对应现象（F）：**F1** 声明材料不存在（→B-M1）；**F2** 解析失败/无 pypdf（→B-M2）；
**F3** 抽取丢公式（→B-M3）；**F4** 缺图/坏图（→B-M4）；**F5** 材料为空（→B-M5）。

## 2. B-T 模板缺失与冲突族

| 分支 | 情形 | 决策 | 处置 | 落点字段 | status |
|-|-|-|-|-|-|
| B-T1 | 无模板字段 / 路径失效 / 打不开 | D5 | 内置 16:9 主题；如实记录模式 | `artifacts.deck_mode.mode`、`template_used` | 记录 |
| B-T2 | 模板自带示例页 | D16 | 保留母版/版式，丢弃自带页重建 | `deck_mode.template_slides_present/dropped` | 记录 |
| B-T3 | 个别版式不兼容 | D5 | 只用可用版式；异常入记录 | `change_records[step=deck]` | partial（核心页建不出时） |
| B-T4 | 模板自带页数 ≠ 冻结页数 | D6+D16 | **冻结页数优先** | `plan_gates.gates[P3]` | 记录 |

对应现象（F）：**F6** 无模板/模板失效（→B-T1）；**F7** 模板自带页（→B-T2）；
**F8** 版式不兼容（→B-T3）；**F9** 页数与时长推导冲突（→B-T4，B-T4 与 F9 是同一约束的两个方向）。

## 3. B-D 依赖缺失与渲染不可用族

| 分支 | 情形 | 决策 | 处置 | 落点字段 | status |
|-|-|-|-|-|-|
| B-D1 | 缺 `python-pptx` | D15 | 跳过 deck，其余照常；**命令仍返回 0** | `artifacts.editable_deck=null`、`deck_limitation` | partial |
| B-D2 | 预览失败/超时 | D12 | 非致命；可用 `--skip-previews` | `artifacts.preview_note` | partial（预览维度） |
| B-D3 | 缺 `pypdf`/`PyPDF2` | D2 | PDF 记未解析 | `sources[].parsed` | partial |
| B-D4 | 中文字体缺失 | — | Pillow 内置位图字体 + manifest 记明字形可能缺失 | `environment.cjk_font` | 记录 |
| B-D5 | 无 LibreOffice/PowerPoint | — | 预览为 PIL 模拟（带水印），以 `.pptx` 打开为准 | `preview_manifest.json` | 记录 |

对应现象（F）：**F10** 缺 python-pptx / Pillow（→B-D1/B-D2）；**F11** 预览失败（→B-D2）；
**F12** 字体缺失（→B-D4）；**F13** 无 Office 可用于栅格化（→B-D5）。

## 4. B-C 契约四形态族（output_contract）

| 分支 | 情形 | 决策 | 处置（**禁 `null`**） | 落点字段 |
|-|-|-|-|-|
| B-C1 | 声明字段流水线未产出 | D18 | `str→""`、`list→[]`、`dict→{}`、`number→0`、`bool→False` | `result.json` 顶层、`self_check.contract_check` |
| B-C2 | case.json 与 task.md 都声明 | D18 | 合并去重；来源同时记录 | `contract.declared_source` |
| B-C3 | 两处都未声明 | D18 | 回落内置默认契约并注明 | `contract.declared_source="built-in default"` |
| B-C4 | 平台/题面要求额外字段 | D18 | 契约只增不减 | `contract.applied` |
| B-C5 | 类型声明模糊 | D18 | 按 `any` 处理，不臆造结构 | `check_contract.py` 报告 |

对应现象（F）：**F14** 契约字段缺失（→B-C1/C4）；**F15** 字段被写成 `null`（→B-C1 的反例）；
**F16** 契约来源不明（→B-C2/C3）；**F17** 额外字段被丢弃（→B-C4）。

**四形态的判定口径**（`common.py::apply_contract` 的容器默认值）：

| 声明类型 | 默认值 | 反面（禁止） |
|-|-|-|
| `str` / `string` / `text` | `""` | `null` |
| `list` / `array` | `[]` | `null` 或 `{}` |
| `dict` / `object` | `{}` | `null` 或 `[]` |
| `int` / `number` / `float` | `0` / `0.0` | `null` 或 `""` |
| `bool` | `False` | `null` |

## 5. B-S 状态不一致与门未过族

| 分支 | 情形 | 决策 | 处置 | 落点字段 | status |
|-|-|-|-|-|-|
| B-S1 | 计划门或 deck 校验未过 | D9/D11 | 继续产出诚实产物 + 状态降级 | `plan_gates.errors`、`deck_audit.errors` | partial |
| B-S2 | 自检发现结构问题 | D9 | 自动降 `partial` 并重写 `result.json` | `self_check.validate_after_downgrade` | partial |
| B-S3 | 状态与内容矛盾 | §6 矩阵 | 机器判定不一致 → 检查器退出码 1 | `check_status_matrix.py` 报告 | — |
| B-S4 | 证据引用指向不存在的源文件 | D13 | 逐条列出（`source_file` 必须 ∈ `sources[].file`） | `evidence_audit`、`C5` 规则 | partial |
| B-S5 | 数字与源材料不一致 | D14 | 警告级提示 + 人工核对说明 | `validate_result` warnings | 记录 |
| B-S6 | 多条规则同时命中 | D20 | 按优先级族裁决，全部命中项留痕 | `change_records`（全量） | 取最严 |

对应现象（F）：**F18** 计划门未全过（→B-S1）；**F19** deck 校验未过（→B-S1）；
**F20** 虚报通过（→B-S3）；**F21** 静默降级（→B-S3）；**F22** 证据引用孤儿（→B-S4）；
**F23** 数字对不上源（→B-S5）；**F24** 规则冲突无裁决（→B-S6）；
**F25** 记录性时间戳被当成不一致（→D19，见下）；**F26** 包约束超限（→打包阻断，见 §7）。

## 6. 状态一致性规则（可机器判定）

1. `status` 只取 `{completed, partial, failed}`；任何降级都必须有对应 `uncertainty` 条目；
2. **不允许静默降级**：deck/预览/某材料的缺失，必须在 `artifacts`/`sources`/`uncertainty` 三处之一可见；
3. **不允许虚报通过**：门或审计未过时，不得写"已校验通过"；
4. **不允许伪降级**：`status=partial` 但检查器找不到任何机器可见缺陷 → 同样判为不一致
   （说明状态没有跟着实际情况走）；
5. `failed` 必须能指出 `error` 字段或 `change_records` 里的 deck 失败记录；
6. 退出码与状态一致：`0` = 已有契约结果的诚实产出（可能 `partial`）；`1` = 没有可用的契约结果。

上述 6 条已被固化成 12 条可执行规则（`C1–C6`、`S1–S7`、`P1–P2`、`F1`、`X1`），
由 `scripts/check_status_matrix.py` 执行：**退出码 0 = 自洽，1 = 不一致（逐条打印字段与值）**。

## 7. 打包形态的失败（不进运行期，属于提交阻断）

| 现象 | 判定 | 处置 |
|-|-|-|
| 包内出现七种文本扩展名之外的文件（`.pptx/.png/.pdf/.svg/…`） | 平台预检直接拒收 | 打包前 `selftest.py --package-check` + 提交验收脚本双层拦截 |
| 文件数 >50 / 单文件 >500KB / 合计 >2MB | 同上 | 同上 |
| 包内出现本机绝对路径（盘符 / UNC / `/Users/`） | 既像调试残留又会误导回放 Agent | `common.portable_path/sanitize_output` 写盘前净化 + 打包前 grep |
| `__pycache__` / `*.pyc` | 非法二进制 | 提交前删除；**绝不在包内直接跑脚本**，一律复制到包外临时目录再跑 |

## 8. 实测证据（本机真实运行，命令与观测见 TEST.md）

| 分支 | 实测用例 | 观测值 |
|-|-|-|
| B-M1 + B-M5 | T8（声明材料不存在）、T13（材料为空） | `status=partial`；`sources` 分别出现 `kind=missing` 与 `kind=none`；uncertainty 各 1 条 |
| B-M2 | T9（遮蔽 pypdf/PyPDF2） | PDF `parsed=false` + 原因；其余材料照常出页；状态 `partial` |
| B-D1 | T11（遮蔽 python-pptx） | `status=partial`；`editable_deck=null`；`deck_limitation` 有值；12 页计划与预览照常；**退出码 0** |
| B-D2 | T10（遮蔽 Pillow） | 预览与 deck 均跳过；`status=partial`；命令**退出码 0** |
| B-T2 | T5（带 1 张自带页的模板） | `template_slides_present=1 / dropped=1`；最终 12 张幻灯片 == 冻结页数 |
| B-S3 | 本版新增负例（把 `completed` 的 result.json 篡改出矛盾） | `check_status_matrix.py` 退出码 1，逐条打印矛盾字段；未篡改时退出码 0 |
| B-S4 | 全部产物扫描 | `evidence[].source_file` 全部 ∈ `sources[].file`（规则 C5 通过） |
