# EDIT_OPS.md — 编辑操作目录（演示稿迭代）

> 对齐高分包 78650 的 `docs/edit_ops.md`：把"生成**与编辑**"的操作动词全集
> 写成显式目录 + 决策树，配合 `scripts/deck_tool.py apply_edits` 实现。
> 目标：回放 Agent 面对"改一页/改几页/调顺序/换图"的指令时，有确定的操作
> 选择和调用方式，而不是推倒整稿重来。

## 1. 操作动词全集

| op | 参数 | 作用 | 核验 |
|-|-|-|-|
| `update_bullet` | page, bullet_index, text, [evidence] | 替换某页某条要点 | 新文本数字再核验（D5） |
| `add_bullet` | page, text, [evidence], [level] | 追加一条要点 | 同上 |
| `remove_bullet` | page, bullet_index | 删除一条要点 | 页码/下标边界检查 |
| `add_note` | page, note | 追加一条讲稿备注 | — |
| `retitle` | page, title | 改页标题（主张式） | 长度≤60（lint） |
| `reorder_pages` | order[] (1..N 置换) | 重排页序 | 必须为完整置换，否则拒绝 |
| `set_figure` | page, ref/kind/table_id/image/note | 改图表槽（四态） | 图表四态词表校验 |

命令形态：

```bash
python scripts/main.py --case <case.json> --out <输出目录> \
    --edit edits.json --version v2
```

每次应用成功的 op 在 `changelog.jsonl` 记一条
`{version, op, page, target, reason}`；`work/deck_v2.pptx` 与 `work/deck.pptx`
并存并同步更新 `work/plan.json`。

## 2. 决策树（编辑指令 → 操作选择）

```
编辑指令来了
├─ 改一页里的文字/数字 → update_bullet（数字必须还在材料中，改坏→verified=false）
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
4. 编辑不覆盖模板约束：页数仍受 `spec.max_slides` 约束，超限走 D6。