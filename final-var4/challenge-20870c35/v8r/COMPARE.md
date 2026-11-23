# COMPARE.md — v8（契约矩阵轴）对照口径：基础 Agent 直接做 vs 加载本 Skill

> 只写**可判定**差异，并列出**不利于本包**的对照结果。
> 数字来自 `TEST.md` 真跑过的命令；平台白板与正式分数由组织方生成，本包不预置、不冒充。

## 1. 对照臂定义

| 臂 | 做法 |
|-|-|
| **A 臂**：基础 Agent 直接做 | 把材料交给基础 Agent，要求"按 `output_contract` 声明输出结构化结果"。它通常**按自己理解的字段**写 JSON，不校验字段齐全性、不区分声明容器、不留契约痕迹 |
| **B 臂**：加载本 Skill | `python "$SKILL_DIR/scripts/main.py" --case <case> --out <out>` + `check_contract.py` 独立复核 |

同输入、同机器、同会话。

## 2. 可判定差异

| # | 差异点 | A 臂 | B 臂（本包） | 怎么判 |
|-|-|-|-|-|
| Q1 | 声明字段是否全在顶层 | 常缺（漏 `change_records`/`environment` 之类） | **16/16**，且 `contract.applied` 列出全部 | `check_contract.py` → `declared=16 missing=0` |
| Q2 | 缺失字段填什么 | 常写 `null` | 按声明容器填 `""`/`[]`/`{}`/`0`，**null 0 个** | 31 格矩阵实测 null 总数 = 0 |
| Q3 | 未知类型/`any`/裸列表 | 依模型心情，常见 `null` | 一律回落 `""` | C-06 / B-06 / S-01 / P-01 四格实测 `string` |
| Q4 | 声明与真值冲突时怎么办 | 常按声明覆盖（把真 id 换成 `[]`）或崩 | **真值优先**，冲突记入 `type_conflicts_on_real_values`，门不失败 | B-09 实测 `case_id:string` |
| Q5 | task.md 里多个契约块 | 通常只看第一块 | **后声明覆盖先声明**并 `warnings.warn` | S-05 实测 `platform_extra_mixed:array` |
| Q6 | JSON-schema 的 optional 属性 | 常被丢弃 | **一并回显** | S-04 实测 `platform_extra_schema_opt:string` |
| Q7 | 声明无法使用时 | 静默按自己的字段输出 | 回落内置默认契约，并把原因写进 note / 痕迹（3 个无留痕通道的格子逐格声明） | E-01…E-07 七格逐格实测 |
| Q8 | 契约结论是否可复核 | 无 | `self_check.json → contract_check` 含 `declared/missing_required/wrong_type/type_conflicts_on_real_values` | 该文件可直接读 |

## 3. ★ 本轴独有的增益：**契约鲁棒性有回归测试**

```bash
python "$SKILL_DIR/scripts/contract_matrix.py" --sandbox /tmp/cm --report /tmp/cm/r.json --emit-md /tmp/cm/t.md
```

任何一次改动契约逻辑（`common.py` / `check_contract.py` / `finalize_result.py`）之后，
重跑 31 格即可知道**哪一格回退了**。实测基线：

| 判据 | 含义 | 实测 |
|-|-|-|
| `cells_total` | 覆盖的形态/边界格数 | **31** |
| `cells_expectation_unmet` | 回退的格子 | **空** |
| `silent_pass_cells` | 该留痕没留痕 / 不该留痕却留痕 | **空** |
| `known_untraced_cells` | 声明为"无留痕通道"的格子（逐格给原因） | **3**（B-01/B-02/E-02） |
| 各格顶层 null 值总数 | 禁止 null 的硬条款 | **0** |
| 退出码集合 | 契约问题不得把主流程打成非 0 | **`[0]`** |

修 D1/D2/D3 前的同源实测：**8 格不中 / 5 格有 null（13 个）/ 退出码含 1**。
这正是"有回归测试"与"没有"的差别 —— 差别不是形容词，是 8 与 0。

## 4. 不利对照（照实写）

1. **3 个格子没有留痕通道**：`B-01`/`B-02`/`E-02` 所在的解析路径（`task.md` 契约块用不起来）
   在 `main.py` 里没有留痕分支，而 v8 **不动 `main.py`**。这三格是"静默容忍"，
   不是"通过" —— 已在报告 `known_untraced_cells` 与 `CONTRACT-MATRIX.md` §3.1 逐格声明。
2. **嵌套契约不逐层填充**：C-07 只验证顶层 `object` 回显；嵌套 `properties` 的内容不生成。
3. **S-06 的可选字段确实不在顶层**：这是契约规定的行为（可选 + 缺失 ⇒ 跳过），
   但如果组织方期望"声明即回显"，这一格会被判为缺失 —— 本包选择遵循契约原文并把它写进文档。
4. **矩阵只覆盖合成案例**：组织方三案例的 `output_contract` 实文运行期才可见，未进入矩阵。
5. **未测并发写同一 `--out`**；未测非法 UTF-8 / BOM 的 `case.json`/`task.md`。

## 5. 结论边界

本对照证明的是**机制差异与可判定性**，不是平台分数。
平台的三案例 × 三重复公平对照由组织方执行；本包不预置白板、不提交预制答案。
