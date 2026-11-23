# CONTRACT-MATRIX.md — OUTPUT_CONTRACT 四形态 × 边界值 逐格实测矩阵

> **本文件的数据全部来自真跑**，不是设计稿：`scripts/contract_matrix.py` 把 31 个格子逐个
> 注入到真实案例里，跑完整主流程（`scripts/main.py` 真子进程、`--skip-previews --quiet`），
> 再从每格的 `result.json` / `self_check.json` **读回**实测值。
> 表格可用同一条命令重现：
>
> ```bash
> # $SKILL_DIR = 含 SKILL.md 的包根；cwd 任意（脚本自定位）
> python "$SKILL_DIR/scripts/contract_matrix.py" >     --sandbox /tmp/cm --report /tmp/cm/contract_matrix_report.json >     --emit-md /tmp/cm/matrix-table.md
> ```
>
> 实测环境：Python 3.13.9 / Windows（win32）/ python-pptx 1.0.2 / Pillow 12.3.0 /
> pypdf 6.14.2；案例 = 包内合成示例案例 `example-synthalign-talk-01`。
> 该案例的 `materials/dataset_card.pdf` 在磁盘上不存在（示例故意如此），
> 所以每一格的 `status` 都是 `partial` —— 这是**如实降级**，与契约矩阵本身无关。

## 0. 一句话结论

31/31 格**期望全部命中**；**静默通过 = 无**（判据见 §3）；契约门 31/31 valid；
顶层 null 值 0 个；退出码集合 `[0]`。
但这是**修完 3 个真实缺陷之后**的结果 —— 修之前同一套矩阵有 8 格期望不中、
5 格出现 null、退出码里出现过 `1`。缺陷逐条见 §2，前后对照见 §1。

## 1. 前后对照（同一套矩阵、同一个案例，只换了包内脚本）

| 指标 | 打补丁前（基线脚本） | 打补丁后（本包） |
|-|-|-|
| 期望未命中的格子 | **8**（C-06、B-06、B-09、S-01、S-04、S-05、E-06、P-01） | **0** |
| 退出码集合 | `[0, 1]` —— 8 格以 **1** 收场 | `[0]` |
| 契约门 valid | 8 格 False | 31 格 True |
| 顶层出现 `null` 的格子 | **5**（C-06、B-06、S-01、E-06、P-01），合计 **13 个 null 值** | **0** |
| 声明了却不在顶层的字段 | **3** 格（S-04 的 `platform_extra_schema_opt`、S-05 的 `platform_extra_mixed`、S-06 的 `platform_extra_opt`） | 仅剩 S-06（**契约规定的**可选缺失，见 §4） |
| 静默通过 | 25（早期口径，含大量误报） | 0 |

> 「打补丁前」一列不是回忆：把本包三个被改脚本换回基线版本（其余逐字节相同）后
> 用**同一个** `contract_matrix.py` 重跑，报告落在包外
> （`<sandbox>/prefix_report.json`）。复核命令：
>
> ```bash
> cp "$SKILL_DIR/scripts/contract_matrix.py" /tmp/cm/          # 先取探针
> cp <baseline>/scripts/{common,check_contract,finalize_result}.py /tmp/pkg/scripts/   # 换回基线
> python /tmp/cm/contract_matrix.py --sandbox /tmp/cm2 --report /tmp/cm2/prefix_report.json
> ```

## 2. 修掉的三个真实缺陷（逐条点名，全部是纯增量）

| 编号 | 缺陷（实测现象） | 触发格 | 根因 | 增量修法 |
|-|-|-|-|-|
| **D2** | 声明类型为 `any`（或**非法类型串**、或**裸列表**）的字段被填成 `null`；`check_contract` 判 `wrong_type`/缺值 → 契约门 False → **主流程退出码 1** | C-06、B-06、S-01、E-06、P-01 | `common.CONTRACT_TYPE_DEFAULTS["any"] = None`，`apply_contract` 直接把它写进 result | `common.apply_contract()` 只加 4 行：`default is None` 时回落成 `""`（对应 OUTPUT_CONTRACT.md §1「四形态回显，禁止 null」） |
| **D3** | ① JSON-schema 形态里**只在 properties、不在 required** 的字段被整条丢弃；② 同一个 `case.json.output_contract` 在 case.json 与 task.md 里都有时，task.md 的**后声明完全不生效**，`contract.applied` 里看不到它 | S-04、S-05 | ① `normalize_output_contract` 把 `name in req_set` 当 required，`apply_contract` 对 optional+缺失直接跳过；② `parse_output_contract_from_task` 遇到第一个可用块就 `return` | ① properties 里的每个名字改为「已声明 ⇒ 必须存在」，平台的强制/可选口径另存到新增的 `common.contract_annotations()` / `contract_specs()`（**只增不改**，旧调用点行为不变）；② 扫描改为「后声明覆盖先声明」并 `warnings.warn` 记录被覆盖的块号 |
| **D1** | 平台把管线**真的产出**的字段声明成另一种容器（B-09：`case_id` 声明成 list，真值是字符串 id）时，契约门 False → 主流程退出码 1；若改成「按声明覆盖」则会把真 id 换成 `[]`，更糟 | B-09 | `check_contract.check()` 只有 missing / wrong_type 两种结论，无法区分「缺字段」与「真值与声明容器不一致」 | `check()` 新增**可选**参数 `produced_names`（默认 None ⇒ 行为完全不变）；真值冲突降级为 `type_conflicts_on_real_values` 清单（记录、不让门失败），缺字段仍然硬失败；`finalize_result` 把 echo **之前**的产出字段名快照传进去，并在 `result.contract` 里新增 `pipeline_produced_fields` / `echo_initialized_fields` 两个字段 |

**没有改**：任何 CLI 参数名、默认值、退出码语义；`main.py` 一行未动；
`normalize_output_contract` / `parse_output_contract_from_task` / `check_contract.check` /
`apply_contract` 的函数名与**位置参数签名**保持不变（新增参数都有默认值）。

## 3. 静默通过的判据与实测

判据（写死在探针里，两处偏差任一方向都计一次）：

```
silent_pass := exit_code == 0
               且 contract_check_valid is True
               且 「该留痕的格子没留痕」 或 「不该留痕的格子留了痕」
```

「留痕」= `uncertainty[]` 里出现契约相关条目，或 `change_records[]` 里出现
`step=contract` / 含 `output_contract` 的记录。

**实测结果：静默通过 0 格。**

### 3.1 声明为「无留痕通道、静默容忍」的格子（3 格，单独列出，不并入"无缺陷"）

| 格子 | 注入 | 为什么静默 | 实测事实 |
|-|-|-|-|
| `B-01` | task.md 的 fenced 块声明 `output_contract` 是**字符串** | 该路径（task.md 解析失败）在 `main.py` 里没有留痕分支，而 v8 **没有改 main.py** | `contract.declared_source = case.json + task.md`；最终契约仍完整（case.json 自带 16 字段） |
| `B-02` | task.md 的 fenced 块声明**空数组** | 同上 | 同上 |
| `E-02` | case.json 的 `output_contract` 本身是字符串 | `normalize_output_contract` 返回 0 字段，该分支也没有留痕 | 顶层 20 键，全部来自内置默认契约，无缺失 |

这 3 格**没有**被算作"通过"，而是逐格声明为容忍；探针把它们汇总在报告的
`known_untraced_cells` 字段里，markdown 汇总表也单列一行。若要把它们也变成有痕，
需要动 `main.py`（本轮明确不动）。

## 4. 契约规定、因此**不算**缺陷的边界

| 现象 | 格子 | 依据 |
|-|-|-|
| `required: false` 且主流程不产出的字段**不出现在顶层** | S-06 | 契约原文：可选 + 缺失 ⇒ 跳过、不污染 result.json。实测 `platform_extra_opt` 不在顶层，且 `contract.applied` 里仍列出它（17 项） |
| 嵌套 schema **不做逐层填充** | C-07 | 本包只做顶层回显；`__n` 得到 `{}`（object），嵌套 `properties` 不生成 |
| 与真产出冲突时**不覆盖真值** | B-09 | 真值优先；冲突记入 `self_check.contract_check.type_conflicts_on_real_values` |

## 5. 逐格实测表

（下表由 `--emit-md` 直接从报告渲染，未手工编辑）

### 逐格实测表（由 `scripts/contract_matrix.py --emit-md` 自动渲染）

| id | 轴 | 注入点 | 注入内容 | exit | status | 契约门 valid | 顶层键数 | 声明字段回显（名:类型） | 契约痕迹条数 | 期望 |
|-|-|-|-|-|-|-|-|-|-|-|
| `C-01` | C 容器形态 | case.json | case.json.output_contract | 0 | partial | True | 21 | platform_extra_str:string | 0 | 命中 |
| `C-02` | C 容器形态 | case.json | case.json.output_contract | 0 | partial | True | 21 | platform_extra_list:array | 0 | 命中 |
| `C-03` | C 容器形态 | case.json | case.json.output_contract | 0 | partial | True | 21 | platform_extra_dict:object | 0 | 命中 |
| `C-04` | C 容器形态 | case.json | case.json.output_contract | 0 | partial | True | 21 | platform_extra_int:number | 0 | 命中 |
| `C-05` | C 容器形态 | case.json | case.json.output_contract | 0 | partial | True | 21 | platform_extra_bool:boolean | 0 | 命中 |
| `C-06` | C 容器形态 | case.json | case.json.output_contract | 0 | partial | True | 21 | platform_extra_any:string | 0 | 命中 |
| `C-07` | C 容器形态 | case.json | case.json.output_contract | 0 | partial | True | 21 | __n:object | 0 | 命中 |
| `B-01` | B 边界值 | task.md | task.md fenced block | 0 | partial | True | 20 | — | 0 | 命中 |
| `B-02` | B 边界值 | task.md | task.md fenced block | 0 | partial | True | 20 | — | 0 | 命中 |
| `B-03` | B 边界值 | case.json | case.json.output_contract | 0 | partial | True | 20 | — | 0 | 命中 |
| `B-04` | B 边界值 | case.json | case.json.output_contract | 0 | partial | True | 21 | ok_field_1:string | 0 | 命中 |
| `B-05` | B 边界值 | case.json | case.json.output_contract | 0 | partial | True | 21 | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx:string | 0 | 命中 |
| `B-06` | B 边界值 | case.json | case.json.output_contract | 0 | partial | True | 21 | platform_extra_badtype:string | 0 | 命中 |
| `B-07` | B 边界值 | case.json | case.json.output_contract | 0 | partial | True | 21 | platform_extra_container:array | 0 | 命中 |
| `B-08` | B 边界值 | case.json | case.json.output_contract | 0 | partial | True | 22 | platform_extra_false:boolean；platform_extra_zero:number | 0 | 命中 |
| `B-09` | B 边界值 | case.json | case.json.output_contract | 0 | partial | True | 20 | case_id:string | 0 | 命中 |
| `S-01` | S 声明形状 | case.json | case.json.output_contract | 0 | partial | True | 22 | platform_extra_bare_a:string；platform_extra_bare_b:string | 0 | 命中 |
| `S-02` | S 声明形状 | case.json | case.json.output_contract | 0 | partial | True | 21 | platform_extra_listdict:array | 0 | 命中 |
| `S-03` | S 声明形状 | case.json | case.json.output_contract | 0 | partial | True | 22 | platform_extra_dictlist:array；platform_extra_dictoftype:object | 0 | 命中 |
| `S-04` | S 声明形状 | case.json | case.json.output_contract | 0 | partial | True | 22 | platform_extra_schema_opt:string；platform_extra_schema_req:number | 0 | 命中 |
| `S-05` | S 声明形状 | task.md | task.md fenced block | 0 | partial | True | 21 | platform_extra_mixed:array | 0 | 命中 |
| `S-06` | S 声明形状 | case.json | case.json.output_contract | 0 | partial | True | 20 | platform_extra_opt:缺失(不在顶层) | 0 | 命中 |
| `E-01` | E 声明非法或缺失 | task.md | task.md fenced block | 0 | partial | True | 20 | — | 0 | 命中 |
| `E-02` | E 声明非法或缺失 | case.json | case.json.output_contract | 0 | partial | True | 20 | — | 0 | 命中 |
| `E-03` | E 声明非法或缺失 | task.md | task.md raw text (broken JSON block) | 0 | partial | True | 20 | — | 0 | 命中 |
| `E-04` | E 声明非法或缺失 | task.md | task.md raw text (contract key absent) | 0 | partial | True | 20 | — | 0 | 命中 |
| `E-05` | E 声明非法或缺失 | task.md | task.md raw text (markdown table, 3 rows) | 0 | partial | True | 20 | — | 0 | 命中 |
| `E-06` | E 声明非法或缺失 | task.md | task.md raw text (markdown table, 6 rows) | 0 | partial | True | 26 | platform_extra_t1:string；platform_extra_t6:string | 0 | 命中 |
| `E-07` | E 声明非法或缺失 | task.md | task.md empty (0 byte) | 0 | partial | True | 20 | — | 0 | 命中 |
| `E-08` | E 声明非法或缺失 | none | no declaration anywhere | 0 | partial | True | 20 | — | 0 | 命中 |
| `P-01` | P 平台额外字段 | case.json | case.json.output_contract | 0 | partial | True | 21 | platform_extra_only:string | 0 | 命中 |

### 汇总

| 项 | 实测 |
|-|-|
| 格子数 | 31 |
| 退出码集合 | [0] |
| status 集合 | ['partial'] |
| 期望全部命中 | 31 / 31 |
| 无法判读（没写出 result.json） | 无 |
| 静默通过（该留痕却没留 / 不该留痕却留了） | 无 |
| 声明为「无留痕通道、静默容忍」的格子 | ['B-01', 'B-02', 'E-02'] |

### 各轴覆盖

| 轴 | 格子数 | 期望命中 |
|-|-|-|
| B 边界值 | 9 | 9 |
| C 容器形态 | 7 | 7 |
| E 声明非法或缺失 | 8 | 8 |
| P 平台额外字段 | 1 | 1 |
| S 声明形状 | 6 | 6 |

## 6. 未覆盖声明（不假装覆盖了什么）

- **多案例并发**：每格都是单案例串行子进程；未测两个案例同时写同一个 `--out`。
- **真实平台案例**：只用包内合成示例案例；组织方三案例的 `output_contract` 实文运行期才可见。
- **超长载荷整体规模**：只测了超长**字段名**（129 字符），未测"上万字段的巨契约"。
- **嵌套契约的深层回显**：C-07 只验证顶层 object；嵌套 `properties` 的逐层填充不是本包行为。
- **非法 UTF-8 / BOM**：`case.json`、`task.md` 均按 UTF-8 读取，未测 GBK 或带 BOM 变体。
- **Windows 保留字字段名**：如 `CON`/`PRN` 未测（与内置键同名已由 B-09 覆盖一类）。
- **退出码 2 的路径**：矩阵只注入契约、不改 CLI，因此 argparse 用法错误不在矩阵内。

## 7. 复核清单（第三方可逐步重跑）

1. `python "$SKILL_DIR/scripts/contract_matrix.py" --sandbox /tmp/cm --report /tmp/cm/r.json --emit-md /tmp/cm/t.md`
   → 期望 `cells=31 unreadable=0 expectation_unmet=0 silent_pass=0`，退出码 0。
2. 打开 `/tmp/cm/r.json`，核对 `cells_total=31`、`exit_codes=[0]`、
   `silent_pass_cells=[]`、`known_untraced_cells` 恰为 B-01/B-02/E-02。
3. 任取一格（例如 `B-09`）读 `/tmp/cm/sandbox/cells/B-09/out/result.json`：
   `case_id` 仍是字符串、`self_check.json → contract_check.type_conflicts_on_real_values`
   列出该冲突、`contract.pipeline_produced_fields` 含 `case_id`。
4. 抽查 5 格，确认 `result.json` 顶层 **null 值个数 = 0**。
