# RUBRIC_MAP.md — 五维评分落点（本版主轴：**可靠体验 10 + 可验证性**）

题面五维：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**。
本版把"可靠"从形容词变成**一张跑出来的表**（`references/FAULT-MATRIX.md`），
因此这里的每一行都附一条**可当场复跑**的命令——不接受"我读了文档所以我有分"。

---

## 1. 主轴：可靠体验 10（逐条落点）

| # | 题面要求 | 本包落点 | 复核命令（可当场跑） |
|-|-|-|-|
| R1 | **材料异常**有处置 | `failure-modes.md` §2.1；D03/D04/D14；`sources[].reason` + `material_status` | `fault_inject.py --only IN-03,IN-04,DP-04` → `status=failed`、`material_marked_unreadable=✓` |
| R2 | **模板缺失/损坏**有处置 | `failure-modes.md` §2.2；D07/D08；**损坏 ≠ 缺席**（前者 `partial`，后者 `completed`） | `--only TP-01,TP-02,TP-03,TP-05` → `fell_back_to_builtin=✓`；损坏三条 `status=partial` |
| R3 | **依赖缺失**有处置 | `failure-modes.md` §2.3；D12/D13/D14；缺 `python-pptx` ⇒ `deck=null` + `deck_error` + **仍写 result.json** | `--only DP-01,DP-02,DP-03` → `deck_null=✓`、`deck_error_recorded=✓`、`result_written=✓` |
| R4 | **契约四形态**全覆盖 | `OUTPUT_CONTRACT.md` §2；`apply_output_contract()`；D15 | `--only CT-01,CT-02` → `declared_fields_echoed=✓`、`no_declared_field_is_null=✓`、`check_contract_exit_0=✓` |
| R5 | **状态一致性** | D18 + 不变量（`status=completed ⇒ uncertainty=[]`）；`failure-modes.md` §5 手工三步 | `--only ST-01,ST-02` → **如实显示为已知缺口**（不假装检出） |
| R6 | 脚本有**非零退出码语义** | `failure-modes.md` §1（0/1/2/3）；`SKILL.md` §6 末 | `--only IN-01,IN-02,IN-05` → 3 / 3 / 1 |
| R7 | **不静默失败** | 判定口径写死在 `fault_inject.verdict()`：exit 0 + `completed` + 零留痕 = 静默失败 | `fault_inject.py ... --quiet; echo $?` → **exit 0**，报告 `silent_failures: 0` |
| R8 | **降级可恢复** | 19 条注入各带恢复动作（撤故障 → 同命令重跑） | 报告 `recovery.ok=true` 计数 = **19/19** |
| R9 | 边界**如实申报** | `failure-modes.md` §4（3 条检测能力边界）+ §5（人工兜底）+ `FAULT-MATRIX.md` §5 | `--only CT-05,ST-01,ST-02` → 矩阵"已知缺口"列写明**是** |

> **一句话**：R7 与 R8 是"可靠"的硬证据——**0 条静默失败**不是描述，是脚本退出码；
> **19/19 恢复**不是承诺，是子进程的 exit code 与 status。

## 2. 实际效果 40（可复现流程 + 真跑通）

| 落点 | 证据 |
|-|-|
| 单一入口 `scripts/main.py`（`--case/--spec/--out`） | `TEST.md` §2：`exit 0` / `status=completed` / 8 页 / 19 顶层字段 / 7 预览 |
| 方案先行的 **CP1** lint | `spec_lint.py`；`main.py` 内嵌执行；偏差按 D05 双写 |
| **CP3** 导出门（G1–G8） | `export_check.py` `exit 0`；G7 校验证据表行数 = `entries` |
| 契约字段全覆盖 | `check_contract.py --case` `exit 0`（19 字段 + 案例声明字段，无 null） |
| 真产物而非叙述 | `academic_deck.pptx`（可被 python-pptx 重开、对象已命名）、`preview-approx-*.png`、`evidence_mapping.md`+`evidence_map.json` |
| 页级可追溯 | 每页 `claim` + `evidence(ref/page)`；无法定位 ⇒ `evidence_gap: true`（不许假装有证据） |

## 3. 使用增益 25（对照口径）

| 落点 | 说明 |
|-|-|
| 对照协议 | 平台权威口径是"基础 Agent vs 加载本 Skill 的 Agent"；本包**不预测分数**，只给本机可复跑的结构性对照 |
| 可测量的结构差异 | 本版新增一个**很硬的对照**：同一包在"注入 24 条真实故障"下的表现 vs 一个没有注入演练的包 —— 后者会崩溃、会报假成功、会丢整个 deck（`FAULT-MATRIX.md` §4 的 8 条） |
| 效率叙事 | 演练是**一条命令**（<90 秒）而不是"人工点 24 次"；失败定位从"看产物猜"变成"读矩阵的哪一格是红的" |
| 边界 | `wall_seconds` 依赖机器；24 条注入不等于"任意故障"；平台白板对照仍是权威口径 |

## 4. 创新增益 15（相对常规做法的新机制）

| 机制 | 常规做法 | 本包做法 |
|-|-|-|
| **M-A 故障注入即交付物** | 写一节"失败处理"散文 | 注入器 + 由实测渲染的矩阵；数字不能手写 |
| **M-B 判定由代码下** | 人看日志说"应该记录了" | `verdict()`：exit 0 + completed + 零留痕 ⇒ 静默失败（布尔量） |
| **M-C 锁定"文档口径"为期望值** | 期望值随口定 | 每条注入的 `expected` 引用 `failure-modes.md`/`OUTPUT_CONTRACT.md` 的具体条款；不一致就叫文档漂移 |
| **M-D 恢复演练** | 只测"会不会失败" | 撤掉故障用**同一条命令**重跑，证明故障是局部的、包是可恢复的 |
| **M-E 依赖屏蔽而非卸载** | 真卸载依赖（污染环境/不可复现） | `sitecustomize` + `meta_path` 钩子按需屏蔽模块，环境零改动 |
| **M-F 声明式探针** | 只 grep 文本 | `probe`：从产物算出的结构化断言（如"每个声明字段都回显且非 null"） |

## 5. 生态贡献 10（可复用 + 文档完整）

| 落点 | 证据 |
|-|-|
| 可复用执行件 | `scripts/fault_inject.py`：`--skill <任意技能根>` + 换 `fixture()` 即可移植到别的 Skill（`FAULT-MATRIX.md` §6 给了加一条注入的模板） |
| 可复用判定 | "静默失败"的定义与判定函数可直接搬走；换场景只需改期望值 |
| 诚实资产 | `failure-modes.md` §4 的三条边界 + §5 的三条手工命令，是**别人能直接抄走的检查表** |
| 文档完整性 | 依赖 / 安装 / 参数 / 示例 / 限制 / 维护（`README.md` §1–§6）；退出码语义集中一处（`failure-modes.md` §1） |
| 资源可复用性 | 4 个入口脚本各自可独立调用（见 `SKILL.md` §3 的 CLI 列）；示例可离线复跑 |

## 6. 自评口径（防止把"没测"说成"通过"）

1. 引用任何数字前，先给出**产出它的命令**；给不出命令的数字不进本文件。
2. 说"已覆盖"必须有 `fault_inject.py` 里对应 ID 的**绿色格**；只有散文说明的，一律
   归到 `failure-modes.md` §4 的"边界"里。
3. `FAULT-MATRIX.md` 与本文不一致时，**以矩阵为准**（它是脚本渲染的），并当场修本文。
4. 三格已知缺口**不抵扣**本包的可靠性结论：它们被写出来，正是因为"不写出来"才是不诚实。

## 7. 维护

- 改任一降级行为 ⇒ 重跑 `fault_inject.py` + 重渲染矩阵 + 更新本文 R1–R9 的期望值；
- 改退出码语义 ⇒ 同步 `failure-modes.md` §1 与 `SKILL.md` §6；
- 新增脚本/入口 ⇒ 在 `SKILL.md` §3 与 `README.md` §3 各补一行；
- 本文第 1 节的复核命令必须**真的能跑**：合并/重命名注入 ID 时同步改这里。
