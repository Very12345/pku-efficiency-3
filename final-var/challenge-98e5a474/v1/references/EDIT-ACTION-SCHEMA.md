# EDIT-ACTION-SCHEMA — 编辑动作的字段级契约（D10 的唯一依据）

编辑是本题最容易"看起来做了、其实没做"的地方。本文件把
`scripts/edit.py` 的**实际字段要求**逐条写清，并给出一张
"调用路径 × 编辑来源字段"的矩阵，最后列出反模式与对拍方法。

> 本文件的所有字段名都取自 `scripts/edit.py` 的真实实现
> （`apply_edits()` 的分派分支），可逐行核对。

## 1. 动作 → 字段 → 记录

| action | 目标 ID 字段 | 新值字段 | 记录到的 action |
|-|-|-|-|
| `add_entity` | —（`entity.id` 可省，自动补） | `entity{...}` / 可选 `relation{...}` | `add_entity`（+`add_relation`） |
| `remove_entity` | `entity_id` | — | `remove_entity` + 每条被波及关系的 `cascade_remove_relation` |
| `rename` | `entity_id` | `to` | `rename` |
| `relabel` | `relation_id` | `to` | `relabel` |
| `flip_direction` | `relation_id` | — | `flip_direction`（before/after 记 `from→to`） |
| `change_kind` | `relation_id` | `to` | `change_kind` |
| `remove_relation` | `relation_id` | — | `remove_relation` |
| `add_group` | —（`group.id` 可省，自动补） | `group{...}` | `add_group` |
| `update_value` | `entity_id` 或 `relation_id` + `field` | `value` | `update_value` |
| `note` | — | `text` | `note` |

**通用规则**

- `reason` 可选；缺省时脚本记为 `from <origin>`；`note` 动作的文本字段是 `text`
  （`reason`/`note` 会被当作原因文本）。
- `add_entity` 可同时携带 `relation{from,to,...}`，脚本会额外记一条
  `add_relation`。
- `remove_entity` 会**级联**：每条被删关系的记录是 `cascade_remove_relation`，
  并从所有分组里剔除该成员。
- `update_value` 必须同时给 `entity_id`（或 `relation_id`）与 `field`，否则记
  `edit.update_value` fail。

## 2. 调用路径 × 编辑来源（本包点名的一处易错点）

| 调用方式 | 编辑从哪来 | `edits` 字段 | `edit_requests` 字段 | 说明 |
|-|-|-|-|-|
| `main.py --case X --edit-svg S` | SVG 内嵌清单为基准 | **被忽略** | **生效** | 走这条路时编辑必须写在 `edit_requests` 里 |
| `main.py --case X`（无 `--edit-svg`） | case.json / `--manifest` 的清单 | **生效** | 也生效 | 常规路径；`manifest` 内嵌 `edits` 亦可 |
| `edit.py <figure.svg> <edits.json>` | SVG 内嵌清单 | — | — | 独立入口，位置参数；编辑文件即第二个参数 |

**实测证据**（详见 `TEST.md` §T7）：

- `--edit-svg` + `edits: []` → `change_records` 为空（符合预期）；
- `--edit-svg` + `edit_requests: [relabel R5]` → `change_records` 出现 `relabel`，
  且 SVG 里能看到新标签 ⇒ **`edit_requests` 是这条路径的正确字段**；
- `--edit-svg` + `edits: [relabel R5]` → `change_records` 为空 ⇒ `edits` 在该路径下确实不生效。

## 3. 反模式表（会导致"请求了但没记下来"）

| 写法 | 实际后果 | 正确写法 |
|-|-|-|
| `{"action":"relabel","target":"R5","value":"…"}` | 目标解析不到 → 日志 `[edit] fail unknown relation`；**不落 `change_records`；退出码仍为 0；`validate_result.py` 仍 VALID** | `{"action":"relabel","relation_id":"R5","to":"…"}` |
| `{"action":"remove_entity","target":"E3"}` | 同上（实体目标必须是 `entity_id`） | `{"action":"remove_entity","entity_id":"E3"}` |
| `{"action":"flip_direction","target":"R4"}` | 同上（关系目标必须是 `relation_id`） | `{"action":"flip_direction","relation_id":"R4"}` |
| 把编辑写在 `edits` 却用 `--edit-svg` 调用 | 该字段被忽略，`change_records` 为空 | 改用 `edit_requests`，或去掉 `--edit-svg` |
| 编辑后不重跑检查 | 旧标签/旧方向可能残留 | 编辑后重跑 CP2 + CP3（SKILL.md §S6） |

## 4. 为什么必须有这份文件（D10 的由来）

`edit.*` 这一族问题**只出现在 stdout 日志**里：它们不进 `result.json`，
也不改变退出码。这意味着**契约门（G1–G8）对"编辑是否真的生效"是盲的**：

- `validate_result.py` 在编辑全失败时仍会输出 `VALID`；
- `main.py` 在编辑全失败时仍可能输出 `exit 0` + `status=success`；
- `change_records` 为空**也可能**是"本来就没要求编辑"。

所以唯一的机器可读判据是**对拍条数**。请把下面这条当成硬性自查：

```bash
# 交付前：把请求条数（case.json 里 edits/edit_requests 的条目数，含 add_entity
# 附带的 relation 与 remove_entity 的级联，按上表推算期望条数）
# 与 result.json 的 change_records 条数逐条对上；对不上就必须查明原因。
python -c "import json,sys;d=json.load(open(sys.argv[1]));print(len(d.get('change_records') or []))" \
    <out>/result.json
```

## 5. 来源与修订

- 字段名来源：`scripts/edit.py` 的 `apply_edits()` 分派分支（逐条可核对）；
- 行为来源：本机实测（见 `TEST.md` §T7），含正向 7 条 `change_records` 的完整样例；
- 若上游修改了 `edit.py` 的字段名或分派逻辑，**必须同步本文件与 SKILL.md §8**，
  并重跑 `scripts/doccheck.py` 确认检查名仍然对得上。
