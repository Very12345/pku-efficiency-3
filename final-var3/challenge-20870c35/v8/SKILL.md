---
name: academic-talk-organizer-contract-matrix
description: >
  学术汇报内容组织（学术 PPT 页面组织）的**契约鲁棒性**版本：从论文/研究材料到可讲、可编辑、
  证据可追溯的演示文件，并且对平台声明的 `output_contract` 做**四形态 × 边界值**的逐格验证。
  当输入包含科研论文材料、研究报告、组会/答辩/评审任务、听众与时长、页数或模板约束、讲稿或备注需求，
  关键词如 学术汇报、答辩PPT、组会汇报、slides、deck、页码规划、讲稿、备注、问答准备、听众适配、
  叙事顺序、汇报内容组织、evidence mapping、模板适配、**output_contract、契约回显、字段缺失、
  类型不符、边界值、空串、空数组、非法类型、JSON-schema、静默通过** 时使用本 Skill：
  读真实材料 → 抽主线 → 页级计划过计划契约门 P1–P8 → python-pptx 生成可编辑 .pptx →
  PIL 预览 → 逐字证据审计 → 按平台声明回显契约字段（**四形态回显、禁止 null**）→
  用 scripts/contract_matrix.py 注入 31 个契约形态/边界并逐格实测 exit/status/回显/静默通过。
  严格以真实文件为准，不臆造数据；包内只含 UTF-8 文本资源，二进制产物运行时生成。
---

# academic-talk-organizer v8 · 契约四形态 × 边界值矩阵

面向「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35（slides 组）。

## 0. 这一版在赌什么

平台会在 `case.json` 或 `task.md` 里声明 `output_contract`，而且**声明形态不止一种**：
裸字段名列表、`{name,type,required}` 列表、`{"字段": "类型"}` 字典、JSON-schema
（`required` + `properties`），字段类型还可能写成 `any`、写成大小写混排、写成不认识的字符串。
"契约鲁棒"不是一句形容词 —— 它是一个**可以逐格跑出来**的问题：

> 这些形态里，哪些能让 `result.json` **照样完整且不带 null**，
> 哪些会让主流程**悄悄降级甚至以非零码收场**，哪些边界**根本没被覆盖**？

v8 把这件事做成了包内可执行物：`scripts/contract_matrix.py`（31 格），
以及把实测结果写死的 `references/CONTRACT-MATRIX.md`（逐行 + 静默通过清单 + 未覆盖声明）。

## 1. 适用与不适用

**适用**：材料齐备、需要交付可讲页面；**且**案例/任务里带 `output_contract` 声明，
或你要向评审证明"平台换一种声明写法我也能回显全字段"。

**不适用**：只想一次性出片、不关心契约字段；论文精读成文、学术写作成稿、科研绘图素材生产
（相邻课题负责）。

**硬边界**：页面内容一律取自源材料逐字引文，不改写事实、不补造数据。

## 2. ★ 契约矩阵：一条命令，31 格实测

```bash
# $SKILL_DIR = 本包根目录（含 SKILL.md；平台安装后即 /skills/weekly-skill）
SKILL_DIR=/skills/weekly-skill

python "$SKILL_DIR/scripts/contract_matrix.py" \
    --sandbox /tmp/cm \
    --report /tmp/cm/contract_matrix_report.json \
    --emit-md /tmp/cm/matrix-table.md
# 期望：cells=31 unreadable=0 expectation_unmet=0 silent_pass=0，退出码 0
```

它做的事：把每个格子写成一个**真实案例目录**（`case.json` + `task.md` + `materials`），
启动 `scripts/main.py` **真子进程**（`--skip-previews --quiet`），
再从每格的 `result.json` / `self_check.json` **读回**：

`exit_code` · `status` · 契约字段是否在顶层 · 回显值的 JSON 类型 ·
声明类型与实例类型是否吻合 · 顶层 null 值清单 · 契约相关痕迹条数 ·
`contract.declared_source` / `contract.applied` · 是否**静默通过**。

### 2.1 矩阵覆盖了什么（31 格）

| 轴 | 格数 | 内容 |
|-|-|-|
| **C 容器形态** | 7 | 字符串 / 列表 / 对象 / 数值(int) / 布尔(bool) / `any` / 嵌套 schema |
| **B 边界值** | 9 | 空串 · null 项 · 0 · false · 空数组 · 空对象 · 超长字段名（129 字符）· 非法类型串 · 缺 `name` · `container` 键 · 与真产出冲突的字段 |
| **S 声明形状** | 6 | 裸列表 / 列表 of dict / dict of type（大写）/ JSON-schema / task.md fenced 注入 / `required:false` 可选缺失 |
| **E 声明非法或缺失** | 8 | 空对象 · 字符串形态 · 非法 JSON · 有 JSON 但无契约键 · markdown 表格（<5 行与 ≥5 行两档）· 空 task.md · 完全无声明 |
| **P 平台额外字段** | 1 | 只声明 1 个额外字段时，必须与内置默认字段共存 |

### 2.2 实测结论（31/31 命中，静默通过 0）

| 项 | 实测 |
|-|-|
| 格子数 / 未命中 / 无法判读 | **31 / 0 / 0** |
| 退出码集合 | **`[0]`** |
| 契约门 `valid` | **31/31 True** |
| 顶层 `null` 值 | **0 个** |
| 静默通过 | **0**（另逐格声明 3 个"无留痕通道、静默容忍"格：B-01/B-02/E-02） |

> 这组数字是**修完三个真实缺陷之后**的结果。修之前同一套矩阵有 **8 格期望不中**、
> **5 格出现 null（合计 13 个 null 值）**、退出码里出现过 **1**。
> 前后对照与缺陷逐条点名见 `references/CONTRACT-MATRIX.md` §1/§2。

### 2.3 矩阵替我抓到的三个缺陷（已修，全部纯增量）

| 缺陷 | 现象 | 修法（点名到函数，位置参数签名不变） |
|-|-|-|
| **D2** | `type:"any"`、非法类型串、裸列表字段被填成 `null` → 契约门 False → **主流程退出码 1** | `common.apply_contract()`：`default is None` 时回落 `""`（+4 行） |
| **D3** | ① JSON-schema 里"只在 properties、不在 required"的字段被整条丢弃；② task.md 里**后声明的契约块完全不生效** | ① `common.normalize_output_contract()`：properties 里每个名字都按"已声明⇒必须存在"；平台强制/可选口径另存进**新增**的 `common.contract_annotations()` / `contract_specs()`；② 同函数改为"后声明覆盖先声明"并 `warnings.warn` 记录被覆盖的块号 |
| **D1** | 平台把管线**真产出**的字段声明成别的容器（如 `case_id` 声明为 list）→ 契约门 False → 退出码 1；若按声明覆盖真值又更糟 | `check_contract.check()` 新增**可选**参数 `produced_names`（默认 None ⇒ 旧行为不变）：真值冲突降级为 `type_conflicts_on_real_values` 记录、**不再让门失败**；缺字段仍然硬失败。`finalize_result` 在契约回显**之前**快照产出字段名传入，并在 `result.contract` 增写 `pipeline_produced_fields` / `echo_initialized_fields` |

## 3. 主流程怎么跑（与基线一致）

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
```

退出码：`0` 已产出通过 validate+contract 的 `result.json`（`status` 说明 `completed`/`partial`）；
`1` 没有可用的契约结果；`2` 参数用法错误。**契约矩阵不改 CLI、不改退出码语义**。

契约回显的权威说明在 `references/OUTPUT_CONTRACT.md`：字段块**逐字保留**；
`apply_contract` 保证声明字段存在，缺失字段按声明容器类型填 `""` / `[]` / `{}` / `0`
（**四形态回显、禁止 null**），并把结果写进 `self_check.json → contract_check`
与 `result.json → contract.{declared_source,applied,pipeline_produced_fields,echo_initialized_fields}`。

## 4. 输入与输出

**输入**：`/input/case.json`（`case_id`/`title`/`report_goal`/`audience`/`duration_min`/
`slide_count`/`report_type`/`materials`/`template`/`figure_files`/`output_contract`）+
`/input/task.md`（约束 + 可能的 `output_contract` 声明）+ 材料目录。
必须实际读取文件；不得按文件名预设内容。

**输出**（`--out`，平台运行期即 `/app/output`）：

```
result.json         # 唯一评分产物：契约字段 + 页级主结果 + 证据定位 + status/sources/
                    #   uncertainty/change_records/environment + audit{...} + contract{...}
talk_plan.json      plan_gates.json      evidence_map.json
evidence_audit.json deck_audit.json      self_check.json
editable_deck.pptx  previews/{cover,slide_0NN,grid}.png  previews/preview_manifest.json
```

## 5. 脚本清单（基线 14 个入口逐一保留，另加 1 个）

| 文件 | 角色 | 作用 |
|-|-|-|
| `scripts/main.py` | build 编排 | 唯一入口；CP1–CP5 门控 |
| **`scripts/contract_matrix.py`** | **verify（v8 新增）** | **31 格契约形态/边界注入 → 真跑主流程 → 逐格实测 exit/status/回显/静默通过；`--emit-md` 输出可入库的表格** |
| `scripts/common.py` | shared | 自定位、JSON IO、**契约解析与回显（含 v8 的 D2/D3 增量）**、确定性投影、路径净化 |
| `scripts/check_contract.py` | verify | 契约齐全性校验（含 v8 的 D1：`type_conflicts_on_real_values`） |
| `scripts/finalize_result.py` | verify/build | result 信封 + 契约回显快照 + 审计嵌入 + 自检 |
| `scripts/evidence.py` · `scaffold_plan.py` · `validate_plan.py` | extract/build/verify | 材料解析 · 页级规划 · 计划契约门 P1–P8 |
| `scripts/deck_builder.py` · `verify_deck.py` · `render.py` | render/verify | 可编辑 .pptx · deck 校验 · PIL 预览 |
| `scripts/validate_result.py` · `selftest.py` | verify | 结构校验 · 全链路 G1–G10 + 包约束 |
| `scripts/make_synthetic_inputs.py` | assets | 运行时生成示例二进制输入 |
| `templates/*` · `assets/*` | assets | 叙事规则 · 计划 schema · result 信封模板 |
| `references/CONTRACT-MATRIX.md` | docs | **v8 轴**：31 格逐行实测 + 静默通过清单 + 前后对照 + 未覆盖声明 |
| `references/OUTPUT_CONTRACT.md` | docs | result.json 契约（字段块逐字保留） |
| `references/RUBRIC_MAP.md` · `failure-modes.md` | docs | 五维落点 · 失败模式与决策规则 |

**改脚本点名（v8 是三个包中唯一改了既有脚本的一份，全部纯增量、逐条在此）**：

1. `scripts/common.py` — `apply_contract()` 加 4 行（D2）；`normalize_output_contract()` 改 1 行
   （properties 一律"已声明"）并重写 `parse_output_contract_from_task()` 的块扫描（D3 后半）；
   新增函数 `contract_annotations()` / `contract_specs()`（不改任何既有函数名与签名）。
2. `scripts/check_contract.py` — `check()` 增加**带默认值**的可选参数 `produced_names`，
   返回值增加两个键（D1）；`main()` 未动。
3. `scripts/finalize_result.py` — 在契约回显前快照产出字段名并传入 `check()`；
   `result["contract"]` 增写两个字段。其余脚本**逐字节未变**。

## 6. 异常与边界处置

| 情形 | 处置 |
|-|-|
| 声明形态无法解析出字段（空对象 / 字符串 / 非法 JSON / 无契约键 / 表格不足 5 行） | 回落内置默认契约；**已知 3 格无留痕通道**（B-01/B-02/E-02）在 `references/CONTRACT-MATRIX.md` §3.1 逐格声明为"静默容忍"，不并入"无缺陷" |
| 声明类型与真产出容器冲突 | **真值优先**，冲突记入 `type_conflicts_on_real_values`，契约门不因此失败 |
| 声明字段管线不产出 | 按声明容器类型填 `""` / `[]` / `{}` / `0`；**禁止 null** |
| `required:false` 且不产出 | 跳过、不污染 `result.json`（契约规定行为，不算缺陷） |
| 嵌套 schema | 只做顶层回显；嵌套 `properties` 不逐层填充（已声明边界） |
| 缺 `python-pptx`/`Pillow`/`pypdf` | 不崩：跳过对应产物 + 如实降级为 `partial` + `uncertainty`/`change_records` 记明，命令仍返回 0 |

其余失败模式（材料缺失、PDF 抽取失败、无模板、页数冲突、图缺失…）见 `references/failure-modes.md`。

## 7. 自查清单

- [ ] `result.json` 顶层**没有 null 值**；`contract.applied` 与声明集合一致
- [ ] `self_check.json → contract_check.valid == true`；`wrong_type` 为空
- [ ] 与真产出冲突的字段出现在 `type_conflicts_on_real_values`，且其真值**未被覆盖**
- [ ] `contract_matrix.py` 跑过且 exit 0：`expectation_unmet=0`、`silent_pass=0`
- [ ] 逐格表与 `references/CONTRACT-MATRIX.md` §5 一致（若不一致，说明本次改动动了契约逻辑，必须解释）
- [ ] 每页（除封面/目录/问答备用页）有 `evidence[0].locator` + 逐字 `quote`
- [ ] 资源形态硬门：只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`；≤50 文件；单文件 ≤500KB；合计 ≤2MB；无符号链接；无 `__pycache__`；无本机绝对路径

## 8. 平台约束（Runtime contract 要点）

平台把 Skill 装到 `/skills/weekly-skill`，在固定 3 案例 × 3 次复跑上运行；
输入 `/input/case.json` + `task.md`，最终产物在 `/app/output`，`result.json` 必须含
output_contract 全部字段与 `case_id`；提交资源 ≤50 个 UTF-8 文本文件、单文件 ≤500KB、
合计 ≤2MB、无符号链接；运行期产物可以是二进制；
执行预算 64 个模型请求 / 900 秒 / 每响应 16384 token。

> **不要在包内目录里跑脚本**（会生成 `__pycache__`，合规硬门直接拒收）。
> `contract_matrix.py` 会把技能复制到沙箱里再调用。
