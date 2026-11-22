# academic-talk-organizer · v1 决策显性化版　（challenge-20870c35 · 学术汇报内容组织）

把**已有**科研材料组织成"可讲、可编辑、证据可追溯"的学术汇报产物；本版的重点不在多加功能，
而在把**遇到什么情况该怎么办**写成可执行、可对照、可机器复核的规则。

- Skill 本体：[SKILL.md](SKILL.md)（触发判据 / 执行顺序 / 决策规则 / 失败分支 / 状态矩阵）
- 决策规则全文：[references/decision-rules.md](references/decision-rules.md)（D1–D20 + 优先级裁决 + 代码位置）
- 失败模式手册：[references/failure-modes.md](references/failure-modes.md)（五族分支 B-M/B-T/B-D/B-C/B-S）
- 字段契约：[references/OUTPUT_CONTRACT.md](references/OUTPUT_CONTRACT.md)
- 五维评分落点：[references/RUBRIC_MAP.md](references/RUBRIC_MAP.md)
- 实测记录：[TEST.md](TEST.md)　·　对照口径：[COMPARE.md](COMPARE.md)

> **资源形态**（题面 Runtime contract：*at most 50 UTF-8 text files, 500KB each and 2MB total,
> no symlinks*）：本包**只含 UTF-8 文本资源**（`.md/.py/.json/.txt/.csv/.yaml/.yml`）；
> `.pptx`/`.png`/`.pdf` 全部由脚本在运行期生成（runtime artifacts），包内无本机绝对路径、
> 无 `__pycache__`、无符号链接。

## 一、快速开始

`$SKILL_DIR` = 含 `SKILL.md` 的目录（平台安装后即 `/skills/weekly-skill`）。
所有脚本用 `os.path.dirname(__file__)` 自定位，**命令与当前 cwd 无关**。

```bash
# 0) 只为示例准备运行时二进制输入（正式案例的材料由平台提供，不需要这一步）
python "$SKILL_DIR/scripts/make_synthetic_inputs.py"

# 1) 最小调用：示例案例 → 输出目录
python "$SKILL_DIR/scripts/main.py" \
  --case "$SKILL_DIR/examples/case.json" --out "$OUT"

# 2) 平台运行期形态
python "$SKILL_DIR/scripts/main.py" \
  --case /input/case.json --task /input/task.md --out /app/output

# 3) 复核：结构 / 契约 / 证据 / deck / 计划 / 状态自洽 / 全链路
python "$SKILL_DIR/scripts/validate_result.py" "$OUT/result.json"
python "$SKILL_DIR/scripts/check_contract.py"  "$OUT/result.json"
python "$SKILL_DIR/scripts/evidence_audit.py"  "$OUT/result.json"
python "$SKILL_DIR/scripts/verify_deck.py" "$OUT/editable_deck.pptx" \
       --expect-pages <N> --plan "$OUT/talk_plan.json"
python "$SKILL_DIR/scripts/check_status_matrix.py" "$OUT"          # 本版新增：状态与内容是否自洽
python "$SKILL_DIR/scripts/selftest.py" "$OUT" --package-check "$SKILL_DIR"
```

**退出码**：`main.py` 的 `0` = 已产出通过 validate + contract 的 `result.json`
（`status` 说明是 `completed` 还是 `partial`——诚实降级不算崩溃）；`1` = 没有可用的契约结果；
`2` = 用法错误。复核脚本统一 `0 = 通过`。

## 二、这一版比"只给流程"多做了什么

| 多出来的东西 | 在哪 | 为什么它值分 |
|-|-|-|
| 触发判据表（用/不用，命中几条即触发） | `SKILL.md` §1 | 让 Agent 在"该不该用"这一步就做对，而不是生成完才发现不该做 |
| 执行顺序表（进入条件 / 动作 / 出口条件 / 失败分支） | `SKILL.md` §3 | 每个检查点都有可判定的出口，不靠"感觉做完了" |
| 决策规则 D1–D20（触发条件 → 动作 → 失败降级 → 落点字段） | `SKILL.md` §4、`references/decision-rules.md` | 规则可对照源码复核；每条都指名它写在哪个字段里 |
| **决策优先级裁决表**（D20：材料事实 > 依赖 > 冻结约束 > 模板渲染 > 契约记录） | `SKILL.md` §5 | 多规则同时命中时不再"看运气"，且被覆盖的规则也要留痕 |
| 状态判定矩阵 + 反向约束 | `SKILL.md` §6 | 防止"把失败写成成功"，也防止"把成功写成降级" |
| 失败分支表（五族） | `SKILL.md` §7、`references/failure-modes.md` | 材料/模板/依赖/契约/状态五类各有编号与处置 |
| `scripts/check_status_matrix.py` | `scripts/` | 把状态一致性变成**退出码**：12 条规则逐条打印字段与值 |

## 三、输入输出

**输入**：`case.json`（`case_id`/`report_goal`/`audience`/`duration_min`/`slide_count`/`report_type`/
`materials`/`template`·`start_deck`/`figure_files`/`output_contract`）+ `task.md` + 材料
（md/txt/PDF/图片）。脚本**实际读取文件内容**，不按标签或文件名假设；材料目录缺省 `<case 目录>/materials`。

**输出**（路径一律可移植：本机绝对路径写盘前改写为相对案例目录形式，`/input`、`/app` 原样保留）：

```
result.json         talk_plan.json      plan_gates.json     evidence_map.json
evidence_audit.json deck_audit.json     editable_deck.pptx  previews/
self_check.json
```

完整清单与示例实测数量见 [examples/EXPECTED-OUTPUT.md](examples/EXPECTED-OUTPUT.md)。

## 四、依赖

| 依赖 | 用途 | 缺失时（决策规则） |
|-|-|-|
| Python ≥ 3.8（本机 3.13.9 实测） | 解释器 | — |
| `python-pptx`（1.0.2 实测） | 生成/适配可编辑 `.pptx` | 跳过 deck，`status=partial`，其余产物照常，命令仍返回 0（**D15**） |
| `Pillow`（12.3.0 实测） | PNG 预览、图片校验（python-pptx 亦依赖） | 跳过预览（非致命）；（**D12**） |
| `pypdf` / `PyPDF2`（6.14.2 实测，可选） | PDF 文本抽取 | PDF 记 `parsed=false` 并降级（**D2**） |

无网络依赖、无 cwd 依赖、不调用 LibreOffice/PowerPoint（预览为 PIL 模拟并如实标注）。

## 五、决策规则速查（全文见 SKILL.md §4）

| 规则 | 一句话 |
|-|-|
| D1 / D17 | 材料缺失 / 材料为空 → 如实标记，不补造 |
| D2 / D3 | PDF 无解析器 / 抽取丢公式 → 记 `parsed=false`，以抽取文本为准 |
| D4 | 缺图或坏图 → 页内诚实占位框，`figure_bound=false` |
| D5 / D16 | 无模板→内置主题；模板自带页→保留母版版式、丢弃自带页 |
| D6 | 页数与时长冲突 → **冻结页数优先** |
| D7 / D8 | 听众缺失→`familiar`；某块无直接主张→`derived=true, weak` |
| D9 / D11 / D10 | 计划门未过 / deck 校验未过 / deck 抛错 → `partial` / `partial` / `failed` |
| D12 / D15 | 预览失败 / 缺 python-pptx → 不崩，降级并记录 |
| D13 / D14 | 引文未逐字命中 / 数字对不上源 → 逐条列出，警告级提示 |
| D18 / D19 | 契约四形态回显（禁 null）/ 确定性探针剔除记录性时间戳 |
| D20 | 多规则同时命中 → 按优先级族裁决，全部留痕 |

## 六、限制与边界

- 不负责论文精读成稿、写作成稿、科研绘图素材生产（相邻课题承担）；
- PDF 无解析器时按"未解析"降级，相关证据弱化但不编造；
- 预览是 Pillow 模拟渲染（带水印），不是 Office 栅格化；
- 证据定位是行级/章节级近似锚点，源材料更新后需按引文复核；
- 模板适配会丢弃起始演示文件自带的示例页，以保证页数等于冻结值（记入 `change_records`）；
- 决策规则是**保守**的：宁可 `partial` 且说明清楚，也不把不确定包装成完成。

## 七、维护

- 改行为：`templates/talk_config.json`（页权重/顺序/问答模板）、`assets/plan.schema.json`（计划门条款）——
  **改配置即改行为，不必改代码**；
- 改规则文字：`SKILL.md` §4–§7 与 `references/decision-rules.md`（两份必须同步；
  D 编号不重排，新增用 D21、D22…，避免历史记录失效）；
- 回归自测：按 [TEST.md](TEST.md) 的用例顺序跑一遍（含六条降级/负例与状态矩阵正反例）；
- 提交前：`selftest.py <out> --package-check "$SKILL_DIR"` 全 ✓，并确认包内无 `__pycache__`、无二进制残留。

## 八、GitHub

见 `GITHUB_URL.txt`（第一行为本作品在仓库中的目录链接）。
