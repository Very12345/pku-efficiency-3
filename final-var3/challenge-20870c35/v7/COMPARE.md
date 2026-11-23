# COMPARE.md — v7（确定性轴）对照口径：基础 Agent 直接做 vs 加载本 Skill

> 本文件只写**可判定**的差异，并明确列出**不利于本包**的对照结果。
> 所有数字来自 `TEST.md` 里真跑过的命令；平台白板与正式分数由组织方生成，本包不预置、不冒充。

## 1. 对照臂定义（同输入 / 同机器 / 同会话）

| 臂 | 做法 |
|-|-|
| **A 臂**：基础 Agent 直接做 | 把材料交给基础 Agent，让它"做一份 20 分钟组会汇报的 slides"；它输出若干页面文字，**不做**双跑对拍、不做中间产物落盘、不做依赖降级说明 |
| **B 臂**：加载本 Skill | `python "$SKILL_DIR/scripts/main.py" --case <case> --out <out>`（一条命令跑完 CP1–CP5） |

两臂的输入完全相同（`case.json` + `task.md` + 材料目录），差别只在流程。

## 2. 可判定差异（本轴视角）

| # | 差异点 | A 臂 | B 臂（本包） | 怎么判 |
|-|-|-|-|-|
| Q1 | 产物是否落盘 | 只有对话里的文字 | **21 个文件**（含 `result.json`、`talk_plan.json`、`evidence_audit.json`、`deck_audit.json`、`self_check.json`、`.pptx`、13 张预览） | `find <out> -type f \| wc -l` |
| Q2 | 同输入复跑是否一致 | 不可判（无产物、无记录） | `determinism.py` 给出三个布尔 + 逐文件 sha 表 | `content_identical` / `files_varying_stable` |
| Q3 | 页面论断是否可溯源 | 无定位 | 每页 `evidence[0]` 带 `source_file/section/line_no/locator/quote` | `evidence_audit.py` exit 0 |
| Q4 | 契约字段是否齐全 | 无 `result.json` | 16 个声明字段全在顶层，**null 0 个** | `check_contract.py` → `declared=16 missing=0 wrong_type=0` |
| Q5 | 页数是否与冻结值一致 | 常见偏离 | `slide_count=12` 与计划一致，P3 门校准 | `verify_deck.py --expect-pages 12` → `checks=8 errors=0` |
| Q6 | 缺依赖是否可见 | 通常静默失败（无产物也无说明） | 跳过对应产物 + `status=partial` + `uncertainty`/`change_records` 记明 + **仍 exit 0** | 见 `TEST.md` T5（遮蔽 `pptx`：产物 19、`varying_raw` 4 个、探针仍 exit 0） |
| Q7 | 包约束是否自证 | 不适用 | `selftest.py --package-check` → `text=39 total_bytes=362375 max_file=42426` | 该命令 exit 0 |

## 3. ★ 本轴独有的增益：**"改了什么"变成可判定的**

基础 Agent 无法回答"这次改动有没有引入不确定性"。加载本包后：

```bash
# 改动前后各跑一次，差异文件清单必须与 references/DETERMINISM.md §2 完全一致
python "$SKILL_DIR/scripts/determinism.py" --case <case> --out-root /tmp/det --runs 5
```

| 判据 | 含义 | 实测基线 |
|-|-|-|
| `files_varying_raw` | raw 字节会变的产物名单 | 恰好 5 个：`editable_deck.pptx`、`previews/preview_manifest.json`、`result.json`、`self_check.json`、`talk_plan.json` |
| `files_varying_stable` | **稳定化后仍会变**的产物 | **空**（这是真正的"不确定性告警线"） |
| `zip_metadata_only_files` | 差异只在容器元数据的产物 | `['editable_deck.pptx']` |
| `path_leak_scan.hit_count` | 产物里的本机绝对路径 | **0** |

⇒ 多出任何一个文件名，或 `varying_stable` 非空，就是**新的不确定性**，必须解释到源码行为。

## 4. 不利对照（照实写）

1. **raw 字节并不相同**：`.pptx` 的 zip 成员时间戳由 CPython `zipfile.writestr` 决定
   （`date_time < 1980` 时填当前本地时间），本包**没有**改 `deck_builder.py`，因此
   `identical=False`。本包给的是"内容投影 + 归一化归档"两个等价物，不是 raw 全同。
2. **跨机器不可比**：`result.json.environment`（python/platform/库版本/字体）必然随机器变化，
   这是**设计内**的不稳定字段，已在 `volatile_fields[]` 第 3 条登记。
3. **探针耗时**：5 次 run 约 5.5 秒墙钟（单次约 1.06–1.16 秒），
   是主流程本身耗时 ×5；对 900 秒预算可接受，但不能无限加大 `--runs`。
4. **未做并发对照**：5 个 run 串行；两个进程同时写同一个 `--out` 未测。
5. **未测跨时区/跨天**：`generated_at` 为 ISO8601 UTC，格式稳定，但没有跨时区实跑。

## 5. 结论边界

本对照证明的是**机制差异与可判定性**，不是平台分数。
平台的三案例 × 三重复公平对照由组织方执行；本包不预置白板、不提交预制答案。
