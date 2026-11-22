# EDIT-ACTION-SCHEMA — 编辑字段的**路由说明**（权威表不在此处复制）

本变体（v3 · 机制显性版）**不重复**编辑字段表，原因有两条：

1. **单一事实源**：编辑字段名来自 `scripts/edit.py` 的 `apply_edits()` 分派分支，
   它是唯一权威。文档再抄一份，就会出现"两份文档+一份代码"三处漂移的可能；
2. **本包的任务不是再写一份表，而是说清"为什么这件事必须由人盯着"** ——
   这正是 `references/MECHANISM.md` §M2.4 所写的 **M2 已知盲区**。

## 1. 你需要的三样东西在哪

| 你要做的 | 看哪 | 为什么 |
|-|-|-|
| 知道某个 action 要写哪个字段 | `scripts/edit.py` 的 `apply_edits()` 分派分支（直接读代码，字段名就在 `ed.get("…")` 里） | 单一事实源 |
| 知道编辑是否真的生效 | 本文 §2 的**条数对拍** | `edit.*` 问题只进 stdout（M2 盲区） |
| 知道编辑后还要做什么 | `SKILL.md` §4 的 S6 与 §9 自查清单 | 编辑后必须重跑 CP2 + 契约门 |

## 2. 唯一可靠的判据：条数对拍

`edit.*` 这一族问题（未知 action、目标 id 不存在、字段名写错）**只出现在
stdout 日志里**：不进 `result.json`、不改变退出码。后果是：

- 一个"目标不存在"的编辑请求 → `change_records` 为空 → 命令仍可能 `exit 0`
  → `validate_result.py` 仍判 `VALID`；
- 而 `change_records` 为空**也可能**是"本来就没要求编辑"。

所以必须对拍**请求条数**与**记录条数**：

```bash
# 记录条数（机器读数）
python -c "import json,sys;d=json.load(open(sys.argv[1]));print(len(d.get('change_records') or []))" \
    <out>/result.json

# 请求条数（按 scripts/edit.py 的规则推算期望值，注意两条容易漏的：
#   ① add_entity 若附带 relation，会额外记一条 add_relation；
#   ② remove_entity 会级联记 cascade_remove_relation（每条被波及的关系一条），
#      并把该实体从所有分组里剔除。）
```

**判据**：期望条数 == 实际条数。不等即判为**编辑未完成**，
`SKILL.md` 的自查清单里这一项不得勾选。

## 3. 两个调用路径的字段差异（最常见的"编辑没生效"原因）

| 调用方式 | 编辑请求读哪个字段 | 说明 |
|-|-|-|
| `main.py --case X --edit-svg S` | **`edit_requests`** | 走这条路时 `edits` 字段会被忽略（本机实测：`edits` 非空 → `change_records` 为空） |
| `main.py --case X`（无 `--edit-svg`） | `edits`（也接受 `edit_requests`） | 常规路径 |
| `edit.py <figure.svg> <edits.json>` | 命令行第二个位置参数 | 独立入口 |

**编者注（为什么不把字段表抄过来）**：字段表本身很容易抄错一位，
而抄错一位的后果恰好是"静默不生效"。让读者去读 `edit.py` 里那几行
`ed.get("relation_id")` / `ed.get("entity_id")`，比读二手表格更可靠。

## 4. 与机制索引的关系

| 现象 | 属于哪个机制的盲区 | 处置 |
|-|-|-|
| 编辑请求不生效但退出码为 0 | **M2 源文件自描述**的盲区（编辑错误不进 result.json） | §2 条数对拍 |
| 编辑后旧标签残留 | M2 + M4（编辑后未重跑产物检查） | 编辑后重跑 CP2 与契约门 |
| `--edit-svg` 指向无内嵌清单的 SVG 被拒 | 这是 M2 的**正向证据**（拒绝猜），不是缺陷 | 先用本技能生成图，再编辑 |
| 图能编辑但改动的语义不对 | 任何机制的盲区（属科学判断） | 人工/LLM 复核 `change_records` 的 before→after |

> 需要**完整**的字段表与反模式清单时，请以 `scripts/edit.py` 为准；
> 若本包同时提供了该表的其它版本文档，两者冲突以代码为准，
> 并应重跑 `python "$SKILL_DIR/scripts/doccheck.py"` 检查文档是否已漂移。
