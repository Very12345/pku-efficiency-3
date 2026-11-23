---
name: academic-talk-organizer-deterministic
description: >
  学术汇报内容组织（学术 PPT 页面组织）的**确定性交付**版本：从论文/研究材料到可讲、可编辑、
  证据可追溯的演示文件，并且**同输入连跑 N 次可逐字节复核**。当输入包含科研论文材料、研究报告、
  组会/答辩/评审任务、听众与时长、页数与模板约束、讲稿或备注需求，关键词如 学术汇报、答辩PPT、
  组会汇报、slides、deck、页码规划、讲稿、备注、问答准备、听众适配、叙事顺序、汇报内容组织、
  evidence mapping、模板适配、plan contract、quality gates、**可复现、确定性、字节级一致、
  跨 cwd、PYTHONHASHSEED** 时使用本 Skill：读真实材料 → 抽取研究问题/方法/结果/局限 →
  生成页级计划并经计划契约门 P1–P8 校验 → python-pptx 生成可编辑 .pptx → PIL 渲染 PNG 预览
  → 逐字证据审计 → 写含证据映射与不确定性的 result.json → **用 scripts/determinism.py
  做同输入多次运行的 sha256 比对，并把"故意不稳定的字段"逐条写进 references/DETERMINISM.md**。
  严格以真实文件为准，不臆造数据，不提交预制答案；包内只含 UTF-8 文本资源，二进制产物一律运行时生成。
---

# academic-talk-organizer v7 · 确定性与字节级可复现

面向「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35（slides 组）。

本版本解决的是一个**评审会真的问出口**的问题：

> "你说这次交付是对的 —— 那我换一台机器、换一个 cwd、再跑一次，
> 拿到的还是同一份东西吗？如果不是，**差在哪几个字段、为什么差、你怎么证明其余部分没差**？"

所以 v7 的**主线**不是"再加一个功能"，而是**把可复现性做成一件可执行、可判读的事**：
包内自带 `scripts/determinism.py`，一条命令跑完**跨进程 / 跨 cwd / 跨 PYTHONHASHSEED**
的 N 次复跑，对**全部产物**做 sha256 比对，并给出
「raw 是否相同 / 内容投影是否相同 / 归一化归档是否相同」三个**互不等价**的结论。

## 1. 什么时候用它 / 什么时候不要用

**用**：需要把已有科研材料组织成可讲页面，并且**交付物要能被第三方独立复跑核对**的场合 ——
正式评审、可复现性审计、教学回放、以及任何"我要证明这份产物不是我手工拼出来的"的场景。

**不要用**：只想要一份一次性 PPT、不在意可复核性；或者需要论文精读成文、学术写作成稿、
科研绘图素材生产（相邻课题负责）。

**硬边界**：页面内容一律取自源材料逐字引文（`quote`），不改写事实、不补造数据；
不代替用户下科学结论。

## 2. 运行命令（全部自定位，cwd 任意）

```bash
# $SKILL_DIR = 本包根目录（含 SKILL.md 的那个目录；平台安装后即 /skills/weekly-skill）
SKILL_DIR=/skills/weekly-skill          # Linux / 平台容器
SKILL_DIR="<本包所在目录>"                # Windows Git Bash（含盘符）

# ① 主流程：抽取 → 页计划 → 计划门 → .pptx → deck 校验 → 预览 → 证据审计 → result.json
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output

# ② ★ v7 新增：确定性探针（同输入连跑 5 次，跨进程/跨 cwd/不同 PYTHONHASHSEED）
python "$SKILL_DIR/scripts/determinism.py" \
  --case "$SKILL_DIR/examples" \
  --out-root /tmp/det --report /tmp/det/determinism_report.json --runs 5

# ③ 独立复核产物（不改任何文件）
python "$SKILL_DIR/scripts/validate_result.py" /app/output/result.json
python "$SKILL_DIR/scripts/check_contract.py"  /app/output/result.json
python "$SKILL_DIR/scripts/evidence_audit.py"  /app/output/result.json
python "$SKILL_DIR/scripts/selftest.py" /app/output --package-check "$SKILL_DIR"
```

退出码语义（**未变**）：`main.py` → `0` 已产出通过 validate+contract 的 `result.json`
（其 `status` 说明 `completed`/`partial`）、`1` 没有可用的契约结果、`2` 参数用法错误；
`determinism.py` → `0` 全部 run 通过判据、`1` 真实不一致或某 run 失败、`2` 参数用法错误。

## 3. 判据：三句话

| 判据 | 含义 | 实测（5 次 run） |
|-|-|-|
| **raw 字节级相同** | 连容器元数据都一样 | **False** —— 5 个产物不同：`editable_deck.pptx`、`result.json`、`self_check.json`、`talk_plan.json`、`previews/preview_manifest.json` |
| **内容投影相同** | 剔除记录性时间戳后逐字节相同 | **True** —— 21 个产物的稳定化哈希，产物树整体哈希 5 次同一个值 |
| **归一化归档相同** | 把 zip 容器重写成固定 `date_time` 后 raw 也相同 | **True** —— 5 个 run 的归一化产物树同一个 raw sha256 |

三句话**缺一不可**：只说第一句会得到"不可复现"的错觉；只说后两句会被怀疑在掩饰。
报告里三个布尔值并列给出，加上 `volatile_fields[]`（8 条逐字段解释）与
`observed_varying_fields[]`（实测观测到的越界差异），谁都能自己判。

**为什么 raw 会不同**（本包不藏）：`python-pptx` 通过
`zipfile.ZipFile(...).writestr()` 写 OOXML 包，而 CPython 的 `writestr` 在
`date_time` 早于 1980 时会**填入当前本地时间**（python-pptx 的 `opc/serialized.py`
只传了 `compression`）。⇒ 整包 raw sha256 每次都变，但
**87 个 zip 成员解压后的字节完全相同**。逐字段说明见 `references/DETERMINISM.md` §3。

## 4. 输入

| 路径 | 内容 |
|-|-|
| `/input/case.json` | `case_id`、`title`、`report_goal`、`audience`、`duration_min`、`slide_count`、`report_type`、`materials`（可为 `{path,role}`）、`template`/`start_deck`、`figure_files`、`output_contract`（可选声明） |
| `/input/task.md` | 任务说明；可能含 output_contract 声明（fenced JSON 或字段表） |
| 材料目录 | `case.json` 列出的文本/PDF/图片（缺省取 `<case 目录>/materials`），自动发现 |

必须**实际读取文件内容**；不得根据文件名或标签预设内容。

## 5. 输出

`--out` 目录（平台运行期即 `/app/output`）：

```
result.json              # 唯一评分产物：契约字段 + 页级主结果 + 证据定位 + status/sources/
                         #   uncertainty/change_records/environment + audit{plan_gates,evidence,deck,gates}
talk_plan.json           # 页级计划（可编辑中间产物）
plan_gates.json          # 计划契约门 P1–P8
evidence_map.json        # 源文件 → {用到它的页, 图表引用}
evidence_audit.json      # 逐页逐字引文审计
deck_audit.json          # deck 机器校验（含 normalized_sha256）
editable_deck.pptx       # 可编辑演示文件（运行期二进制产物）
previews/cover_preview.png · slide_0NN.png · preview_grid.png · preview_manifest.json
self_check.json          # validate + contract + P/G 门 + 确定性探针（plan/evidence_map 投影 sha）
```

**确定性相关的两个内建字段**（每次运行都写，便于两次运行直接对拍）：

| 位置 | 字段 | 实测值（本机 5 次 run） |
|-|-|-|
| `self_check.json → determinism` | `plan_sha16` / `evidence_map_sha16` | 5 次全同（与 `determinism.py` 的稳定化结论一致） |
| `self_check.json → determinism` | `deck_pptx_normalized_sha16` | 5 次全同 = `deck_audit.json.normalized_sha256` |
| `result.json → contract` | `pipeline_produced_fields` / `echo_initialized_fields` | 如实列出哪些字段是管线产出、哪些是契约回显补齐 |

## 6. 确定性探针怎么用（三种典型场景）

```bash
# A. 日常自证：5 次复跑，期望 exit 0
python "$SKILL_DIR/scripts/determinism.py" --case <case> --out-root /tmp/det --runs 5

# B. 只做内容投影（不写归一化归档，省磁盘）
python "$SKILL_DIR/scripts/determinism.py" --case <case> --out-root /tmp/det --runs 3 --no-normalize

# C. 把探针当"变更审计"：改完脚本后跑一次，差异文件清单必须与
#    references/DETERMINISM.md §2 的表一致；若多出任何一个文件，
#    说明这次改动引入了新的不确定性 —— 必须解释到源码行为，否则不算通过
```

报告里最该看的两行（机器可读）：

```json
"files_varying_raw":    ["editable_deck.pptx", "previews/preview_manifest.json",
                         "result.json", "self_check.json", "talk_plan.json"],
"files_varying_stable": [],
"zip_metadata_only_files": ["editable_deck.pptx"],
"volatile_fields": [ ... 8 条，逐条给"为什么不稳定 / 怎么稳定化" ... ],
"gate": {"all_runs_exit_0": true, "content_projection_identical": true,
         "no_machine_path_leak": true, "overall_pass": true}
```

## 7. 脚本清单（v7：基线全包 14 个入口一个不少，另加 1 个）

| 文件 | 角色 | 作用 |
|-|-|-|
| `scripts/main.py` | build 编排 | 唯一入口：CP1–CP5 门控编排（环境预检→材料解析→计划→deck→预览→审计→result→自检） |
| **`scripts/determinism.py`** | **verify（v7 新增）** | **同输入 N 次复跑（跨进程/跨 cwd/不同 PYTHONHASHSEED），全产物 sha256 比对 + 稳定化 + 路径泄漏扫描 + 机器可读报告** |
| `scripts/evidence.py` | extract | 材料加载（md/txt/PDF-pypdf）与主张/证据锚点抽取 |
| `scripts/scaffold_plan.py` | build | 页级规划：听众→背景比例、叙事顺序、一页一主张、问答预演、图绑定 |
| `scripts/validate_plan.py` | verify | 计划契约门 P1–P8（`assets/plan.schema.json` 驱动） |
| `scripts/evidence_audit.py` | verify | 逐页逐字引文审计 + 定位/数字/图绑定 |
| `scripts/deck_builder.py` | render | python-pptx 生成/模板适配可编辑 .pptx（确定性元素命名） |
| `scripts/verify_deck.py` | verify | deck 打开/页数/备注/命名/OPC/规范化 sha 校验 |
| `scripts/render.py` | render | PIL 模拟预览 + manifest + 字体探测 `font_status()` |
| `scripts/validate_result.py` | verify | result.json 结构+文件+数字可对源校验 |
| `scripts/check_contract.py` | verify | output_contract 字段齐全性校验 |
| `scripts/finalize_result.py` | verify/build | result 信封组装 + 契约回显 + 审计嵌入 + 确定性探针 |
| `scripts/selftest.py` | verify | 全链路复核 G1–G10 + 包约束审计 |
| `scripts/common.py` | shared | 自定位、JSON IO、契约工具、**确定性投影 hash**、本机路径净化 |
| `scripts/make_synthetic_inputs.py` | assets | 运行时生成示例二进制输入（PDF/PNG/可选模板） |
| `templates/*` · `assets/*` | assets | 叙事规则、页计划 schema、result 信封模板 |
| `references/DETERMINISM.md` | docs | **v7 轴**：逐字段不稳定清单 + 稳定化算法 + 实测表 |
| `references/OUTPUT_CONTRACT.md` | docs | result.json 契约（唯一评分产物） |
| `references/RUBRIC_MAP.md` | docs | 五维评分（40/25/15/10/10）逐条落点 |
| `references/failure-modes.md` | docs | 失败模式 F1–F26 + 决策规则 D1–D17 |

> 基线的每个 `scripts/*.py` 与每个 `--flag` 在本包里**逐一保留、逐字节不变**
> （`main.py` 的 `--case/--out/--task/--materials/--template/--skip-previews/--quiet`，
> `make_synthetic_inputs.py` 的 `--out/--force/--template/--quiet`，
> `selftest.py` 的 `--package-check`，`evidence_audit.py` 的 `--sources-dir/--out`，
> `validate_plan.py` 的 `--materials-dir/--schema`，`verify_deck.py` 的 `--expect-pages/--plan`，
> `check_contract.py` 的 `--contract`）。v7 只**新增** `determinism.py`，不改任何既有脚本。

## 8. 异常处理（与确定性有关的四条，其余见 references/failure-modes.md）

| 编号 | 情形 | 处置 |
|-|-|-|
| DV7-1 | 某次 run 退出码非 0 | 报告 `gate.all_runs_exit_0=false`、`overall_pass=false`，**不掩盖**；探针自身也返回 1 |
| DV7-2 | 稳定化后仍有文件不一致（真实不确定性） | 出现在 `files_varying_stable`；必须定位到源码行为并登记进 `volatile_fields`，否则视为缺陷 |
| DV7-3 | 产物里出现本机绝对路径 | `path_leak_scan()` 命中即 `overall_pass=false`；修法是让该路径经过 `common.sanitize_output()` |
| DV7-4 | 某产物只在部分 run 存在 | 出现在 `files_missing_in_some_run`，同样判 `overall_pass=false`（不存在"偶尔少写一个文件"这种可接受形态） |

与依赖相关（D15）：缺 `python-pptx`/`Pillow`/`pypdf` 都**不崩**，
跳过对应产物并把原因写进 `uncertainty`/`change_records`，`status→partial`，命令仍返回 0。
注意：**缺 Pillow 会连带让 `.pptx` 也产不出来**（python-pptx 声明依赖 `Pillow`），
逐项实测见 v9 轴的 `references/DEGRADE-MATRIX.md`（若同目录存在）。

## 9. 自查清单（收尾前逐项确认）

- [ ] `result.json` 存在；`case_id` 与输入一致；`status` ∈ {completed, partial, failed}
- [ ] `output_contract` 声明字段全部出现在 `result.json` 顶层，且**无 null 值**
- [ ] `plan_gates.json` / `evidence_audit.json` / `deck_audit.json` 存在，未过时 `uncertainty` 有对应条目
- [ ] 每页（除封面/目录/问答备用页）都有 `evidence[0].locator` + `quote` 逐字原句
- [ ] **`determinism.py` 跑过且 exit 0**：`content_identical=true`、`files_varying_stable=[]`、`leaks=0`
- [ ] **差异文件清单与 `references/DETERMINISM.md` §2 完全一致**（多一个就要解释到源码行为）
- [ ] `self_check.json → determinism` 的三个 sha 两次运行相同（除 deck 的 normalized_sha 已确认同口径）
- [ ] 资源形态硬门：只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`；≤50 文件；单文件 ≤500KB；合计 ≤2MB；无符号链接；无 `__pycache__`；无本机绝对路径

## 10. 平台约束（Runtime contract 要点）

- 平台把本 Skill 安装到 `/skills/weekly-skill`，在固定 3 案例 × 3 次复跑上运行 ⇒
  **"同输入复跑"正是评测方也在做的事**，本版本的探针与该口径对齐。
- 输入 `/input/case.json` + `task.md`；中间产物在 `/app/work`；最终产物在 `/app/output`。
- 提交资源：≤50 个 UTF-8 文本文件、单文件 ≤500KB、合计 ≤2MB、无符号链接；
  运行期产物可以是二进制。
- 执行预算：64 个模型请求 / 900 秒 / 每响应 16384 token（含推理）；尽早保存部分成果。

> **不要在包内目录里跑脚本**：那会生成 `__pycache__`（合规硬门直接拒收）。
> 本包所有示例命令都假设工作目录在包外；`determinism.py` 会把技能复制到沙箱里再调用。
