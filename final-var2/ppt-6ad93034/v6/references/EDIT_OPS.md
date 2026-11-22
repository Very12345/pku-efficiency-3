# EDIT_OPS.md — 编辑操作目录（演示稿迭代）

> 目的：把"生成**与编辑**"的操作动词全集写成显式目录 + 决策树，配合
> `scripts/deck_tool.py` 的 `apply_edits` 实现。
> 目标：回放 Agent 面对"改一页/改几页/调顺序/换图"的指令时，有确定的操作
> 选择和调用方式，而不是推倒整稿重来。

## 1. 操作动词全集

| op | 参数 | 作用 | 核验 |
|-|-|-|-|
| `update_bullet` | page, bullet_index, text, [evidence] | 替换某页某条要点 | 新文本数字再核验（D2） |
| `add_bullet` | page, text, [evidence], [level] | 追加一条要点 | 同上 |
| `remove_bullet` | page, bullet_index | 删除一条要点 | 页码/下标边界检查 |
| `add_note` | page, note | 追加一条讲稿备注 | — |
| `retitle` | page, title | 改页标题（主张式） | 长度≤60（lint） |
| `reorder_pages` | order[] (1..N 置换) | 重排页序 | 必须为完整置换，否则拒绝 |
| `set_figure` | page, ref/kind/table_id/image/note | 改图表槽（四态） | 图表四态词表校验 |

命令形态（`$SKILL_DIR` = 含 SKILL.md 的技能根目录，cwd 不是它也能跑）：

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
python "$SKILL_DIR/scripts/main.py" --case <case.json> --out <输出目录> \
    --edit <edits.json> --version v2
```

每次应用成功的 op 在 `changelog.jsonl` 记一条
`{version, op, page, target, reason}`；`work/deck_v2.pptx` 与 `work/deck.pptx`
并存并同步更新 `work/plan.json`。

## 2. 决策树（编辑指令 → 操作选择）

```
编辑指令来了
├─ 改一页里的文字/数字 → update_bullet（数字必须还在材料中，找不到→verified=false，见 D2）
├─ 页上要点太少/太多   → add_bullet / remove_bullet
├─ 补充讲解/过渡话术   → add_note（与页面文字分开，不复制页面内容）
├─ 改页面标题         → retitle（保持主张式，≤60 字）
├─ 换页序             → reorder_pages（给完整置换；只给两页对调也拆成置换）
├─ 换/插/删图表       → set_figure（kind ∈ chart_image|table|embedded|placeholder）
├─ 改配色/字体/页脚   → 不逐页改！改 templates/default.json 或 case spec.style
│                      后重跑（模板是数据，不是埋在代码里）
└─ 无法识别的操作     → 跳过并记 uncertainty（本次其余 op 照常应用）
```

## 3. 版本与回退

- 每个 `--version <v>` 在 `work/deck_<v>.pptx` 归档（`--edit` 时）；
- 改坏回退 = 复制上一版 deck 重跑（`deck.pptx` 与 `deck_v1/2/….pptx` 并存，
  `plan.json` 每轮更新），并写一条 change_record 说明回退；
- 版本现场：`changelog.jsonl` + result.json `change_records` + `manifest.json`
  足以重建"哪一版是交付版"。

## 4. 编辑的诚实红线（编辑链路同样生效）

1. 编辑引入的新数字必须能在材料中找到（`check_claim_numbers` 再核验）；
2. 找不到的数字 → 该主张 `verified=false` 进 `unverified_claims`，不回填；
3. 未知 op / 非法页码 / 非置换页序 → 跳过 + 记录，绝不静默忽略或猜一个；
4. 编辑不覆盖模板约束：页数仍受 `spec.max_slides` 约束，超限走 D7。

---

# 附：页面蓝图与模板槽位（原 DECK_SPEC 文档）

> 与上半部分同属"页面骨架与操作"主题，由原 DECK_SPEC 文档合并进本文件，**内容一字未删**（原文件名见本包 README §3 的合并说明）。

> 说明模板从哪来、槽位如何填、页面模型（plan.json）长什么样、哪些约束
> 绝不能越界。模板是**数据**，不是写死在代码里的样式；页面蓝图是
> deck_tool/slide_text 的确定性映射规则。

## 1. 页面蓝图（论文结构 → 页面结构）

页级叙事角色（`slide_text.ROLE_LABELS`）与收纳规则：

| 角色 | 收纳内容 | 页码常态 | 证据要求 |
|-|-|-|-|
| cover | 标题 + 副题（受众/时长/页数） | 1 | 无（封面页） |
| overview | 主线：研究问题一句 + 摘要/结论首句 | 2 | 摘要/引言/结论 |
| background | 背景/动机 ≤3 条 | 富余页 | §背景/§引言 |
| question | 研究问题 ≤2 条（一页一个问题） | 3–4 | 引言 |
| method | 方法 ≤4 条：核心思路>步骤>差异 | 4–5 | §方法 |
| result | 表驱动量化主张（每表页 2 条）+ 图/表槽 | N | 表/图/§结果 |
| discussion | 解释性结论 ≤3 条 | 富余页 | §讨论 |
| limitation | 局限与边界 ≤3 条 | 富余页 | §局限/展望 |
| takeaway | 带走的一句话 + 下一步 | 末页 | §结论 |

页数分配（`alloc_roles`，确定性）：3–20 页自动展开；5 页起主干
cover→overview→question→method→result→takeaway，富余页先插
background/discussion/limitation，再在收束前增加 result 页。

## 2. 模板来源（三级优先）

| 优先级 | 来源 | 行为 |
|-|-|-|
| 1 | case.json `spec.template_pptx` | 打开组织方 PPTX，沿用其母版/版式字体配色页脚；**只填内容槽位，不修改母版** |
| 2 | case.json `spec.starting_deck` | 同 1 外还要"适配起始稿"：原稿备份到 `work/original_inputs/`，用其版式重排页面，改动记入 change_records |
| 3 | `templates/default.json` | 内置 16:9 学术模板，颜色/字体/页脚/槽位全部参数化（case `spec.style` 可覆盖任意键） |

## 3. 槽位（templates/default.json `slots`）

| 槽位 | 坐标(英寸) | 用途 | 约束 |
|-|-|-|-|
| title | (0.55, 0.30) 12.2×0.95 | 页标题（主张式） | ≤60 字，28pt 粗体，主色 |
| subtitle | (0.55, 1.15) | 封面副题 | 可由 spec.subtitle 覆盖 |
| body | (0.60, 1.85) 12.1×4.9 | 正文要点 | ≤7 条；字号自动收敛 ≥12pt；单条 ≤90 字 |
| body_with_figure | (0.60, 1.85) 7.0×4.9 | 有图/表时正文 | 压缩列宽，字号 15pt 起 |
| figure | (7.95, 1.95) 4.85×4.4 | 图/表/占位 | 见 §4 |
| evidence | (0.60, 6.75) 9.5×0.3 | 页级证据脚注 | 9pt 灰字；每页必填（G6 配套） |
| footer | (0.40, 7.05) 12.5×0.3 | 模板页脚 | 9pt 灰字 + 页码 |

页面蓝图落盘为 `work/plan.json`（**可编辑源**）：`{generated_at, schema,
pages:[{index, role, role_label, title, claims[], figure{}, notes[],
agenda_item}]}`；`--edit` 修改的就是它，再据此重建 deck。

## 4. 图表槽位规则（诚实优先四态）

| figure.kind | 何时用 | 来源 |
|-|-|-|
| `chart_image` | 材料给出数值型数据表 | matplotlib 按表头/数值**原样重绘**，未修改数据 |
| `table` | 图表重绘不可用（无 matplotlib / 数据非数值列 / --no-chart） | PPTX **原生可编辑表格**，数据逐格可改 |
| `embedded` | 材料直接提供图片文件 | 原样嵌入，不改动 |
| `placeholder` | 论文图是位图且无取数数据 | 灰框"诚实占位"，绝不凭空生成曲线 |

## 5. 字体与溢出

- 中文字体：首选 Microsoft YaHei（拉丁+东亚+复杂文种三处 typeface 均设置），
  缺失时回落并记入 `uncertainty`；PPTX 只记字体名，由打开端替换（换机防御）。
- 溢出防护：`_fit_size()` 按字符宽度估算行数，字号逐级下调至 ≥12pt；仍放
  不下的要点降级进演讲者备注并注明。
- 预览渲染（PIL/reportlab）找不到 CJK 字体时只影响预览画质，不影响 PPTX；
  该事实写入 `previews.warnings`（render_qa.qa_report 的 cjk_font_available 检查）。

## 6. 模板约束自查（SKILL.md §7 自查清单第 7 条）

- [ ] 外部模板：母版/版式未被修改（仅新增内容对象）
- [ ] 全部正文处于槽位矩形内（预览核对）
- [ ] 字号 ≥ limits.min_body_pt；标题 ≤ title_max_chars
- [ ] 页脚/页码来源唯一（模板或 spec，不混用）
- [ ] 证据脚注每页存在，与演讲备注一致