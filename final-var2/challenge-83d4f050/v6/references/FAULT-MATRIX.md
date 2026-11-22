# FAULT-MATRIX.md — 失败注入矩阵（四形态 × 实测退出码/status/留痕）

> **本文件不是设计承诺，而是实测台账。** 表里每一个数字都来自
> `scripts/fault_inject.py` 在**包外临时副本**上的真实运行（2026-11-22 +08 本机实测，
> Python 3.13，matplotlib/Pillow 齐备）。
> 复跑命令（任何人在任何机器上都能复算）：
>
> ```bash
> export SKILL_DIR=/path/to/<package>          # 含 SKILL.md 的那一层
> cp -r "$SKILL_DIR" /tmp/fault-skill          # 绝不在包内跑（会生成 __pycache__）
> python3 /tmp/fault-skill/scripts/fault_inject.py --skill /tmp/fault-skill --out /tmp/fault-out
> # 产物：/tmp/fault-out/fault-report.json（机器可读）+ FAULT-MATRIX.generated.md（同表）
> ```

## 1. 口径（先读，否则表看不懂）

| 概念 | 定义 |
|---|---|
| **四形态** | **输入**（case/材料/规格本身坏）、**模板**（包内资产缺失或损坏）、**依赖**（matplotlib/Pillow/格式请求）、**契约**（`output_contract` 四形态与校验 CLI） |
| 判定对象 | 真实主流程 `scripts/main.py`（退出码 0/2/3）或真实校验 CLI `check_contract.py`（0/1） |
| **留痕位点** | `uncertainty[]` / `reason` / `self_check.warnings` / `self_check.failures` 中出现与该故障对应的记录 |
| **静默失败** | `exit=0` **且** `status=success` **且** 四个留痕位点**全空** —— 即"故障发生了，但结果里完全看不出来" |
| 单故障原则 | 每个场景只注入**一处**故障，其余输入保持健康值（`in-07` 除外，它注入的就是"任务说明缺失"） |

## 2. 主表（24 场景 · 实测）

| # | 形态 | 注入什么 | 期望行为 | 实测 exit | 实测 status | gates | uncertainty 条数 | 实测留痕位点 | 静默失败 | 判定 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 输入 | case.json 路径不存在 | 非零退出且**不产出** result.json（入口显式拒绝，不是空图） | `1` | `—（CLI 直调，无 result.json）` | `—` | 0 | 无痕迹 | 否 | 符合期望 |
| 2 | 输入 | 材料目录为空（case 未给 materials） | exit 3 / status=failed，uncertainty 写明材料缺失并给补救路径 | `3` | `failed` | `{}` | 1 | uncertainty×1,reason | 否 | 符合期望 |
| 3 | 输入 | case.json 不是合法 JSON | 非零退出（入口解析失败即停止） | `1` | `—（CLI 直调，无 result.json）` | `—` | 0 | 无痕迹 | 否 | 符合期望 |
| 4 | 输入 | 材料只有实体表、没有关系节（草稿路径） | 不报成功：草稿未人工核验 ⇒ exit 2 / status=partial，且 edges 为空要留痕 | `2` | `partial` | `8/8` | 1 | uncertainty×1 | 否 | 符合期望 |
| 5 | 输入 | 机制规格里出现枚举外类型（type=banana，规格其余部分完好） | schema 门阻断：exit 3 / status=failed / reason 指向 schema（**不得**被静默改写成 other） | `3` | `failed` | `{}` | 1 | uncertainty×1,reason | 否 | 符合期望 |
| 6 | 输入 | 材料文件不是合法 UTF-8（模拟乱码/二进制混入） | 不崩溃：解码失败要被替换处理并继续，若有降级必须留痕 | `3` | `failed` | `{}` | 1 | uncertainty×1,reason | 否 | 符合期望 |
| 7 | 输入 | case.json 没有 task、也没有 task.md（CP1.2 判 warn） | 降级必须留痕：uncertainty / self_check 要有记录（**实测见 §4 G3**） | `0` | `success` | `8/8` | 1 | uncertainty×1 | 否 | 符合期望 |
| 8 | 输入 | 边指向不存在的实体 id（e999） | 不得静默丢边：丢弃的边必须留痕（uncertainty / reason / self_check），**实测见 §4 G1** | `0` | `success` | `8/8` | 1 | uncertainty×1,self_check.warnings×1 | 否 | 符合期望 |
| 9 | 模板 | 删掉 assets/palettes.json（配色资产缺失） | 回退到内置默认调色板**并留痕**（SKILL.md D18 / failure-modes F07 的承诺，实测见 §4 G2） | `0` | `success` | `8/8` | 1 | uncertainty×1 | 否 | 符合期望 |
| 10 | 模板 | 删掉 assets/mechanism-spec.schema.json（CP2 门失效） | S01 降级为 warn 并写进 uncertainty（不阻断渲染，但不得无痕） | `0` | `success` | `8/8` | 1 | uncertainty×1,self_check.warnings×1 | 否 | 符合期望 |
| 11 | 模板 | 删掉 templates/relation-checklist-template.md（人工核对清单） | 运行期无消费者 ⇒ 行为不变；属**文档资产**而非运行时依赖（如实标注 N/A） | `0` | `success` | `8/8` | 0 | 无痕迹 | N/A（无运行时消费者） | 符合期望 |
| 12 | 模板 | 删掉 assets/result.template.json（结构模板） | 运行期无消费者 ⇒ 行为不变（N/A） | `0` | `success` | `8/8` | 0 | 无痕迹 | N/A（无运行时消费者） | 符合期望 |
| 13 | 模板 | 把 assets/palettes.json 改成非法 JSON（资产存在但损坏） | 读资产失败必须回退内置默认**并留痕**，不得静默用坏值（实测见 §4 G2） | `0` | `success` | `8/8` | 1 | uncertainty×1 | 否 | 符合期望 |
| 14 | 依赖 | matplotlib 不可导入（ImportError） | 只交付可编辑 SVG：exit 2 / status=partial / gates.g5_png=false / previews 为空 / 原因入 uncertainty | `2` | `partial` | `7/8` | 1 | uncertainty×1,self_check.failures×2 | 否 | 符合期望 |
| 15 | 依赖 | matplotlib 能 import，但 matplotlib.pyplot 抛 RuntimeError | 走 except Exception 分支同样降级：exit 2 / partial / 原因入 uncertainty（**不得**崩溃） | `2` | `partial` | `7/8` | 1 | uncertainty×1,self_check.failures×2 | 否 | 符合期望 |
| 16 | 依赖 | --formats svg（明确只要可编辑源，不请求预览） | exit 2 / partial：未请求 ≠ 失败，但要说明'本次未请求预览'（可恢复：加回格式即成功） | `2` | `partial` | `7/8` | 1 | uncertainty×1,self_check.failures×2 | 否 | 符合期望 |
| 17 | 依赖 | Pillow 不可导入（PNG 写出依赖它） | PNG 写不出时降级为 SVG-only 并留痕；不得伪造成'已导出' | `2` | `partial` | `7/8` | 1 | uncertainty×1,self_check.failures×2 | 否 | 符合期望 |
| 18 | 契约 | output_contract 声明标量字段（无真实值） | 顶层出现该字段且为空串 ""（不是 null） | `0` | `success` | `8/8` | 0 | 无痕迹 | N/A（无运行时消费者） | 符合期望 |
| 19 | 契约 | output_contract 声明列表字段（无真实值） | 顶层出现该字段且为 []（不是 null） | `0` | `success` | `8/8` | 0 | 无痕迹 | N/A（无运行时消费者） | 符合期望 |
| 20 | 契约 | output_contract 声明布尔字段（无真实值） | 顶层出现该字段且为 false（不是 null） | `0` | `success` | `8/8` | 0 | 无痕迹 | N/A（无运行时消费者） | 符合期望 |
| 21 | 契约 | output_contract 声明数值与字典字段（无真实值） | 顶层分别为 0 与 {}（不是 null） | `0` | `success` | `8/8` | 0 | 无痕迹 | N/A（无运行时消费者） | 符合期望 |
| 22 | 契约 | output_contract 声明值本身就是 null | 按标量形态填 ""，**顶层仍然不得出现 null**（D19 第 3 条） | `0` | `success` | `8/8` | 0 | 无痕迹 | N/A（无运行时消费者） | 符合期望 |
| 23 | 契约 | 主流程跑完后往 result.json 顶层塞一个 null，再跑 check_contract.py | 校验器必须报 C04 fail 且 exit 1（证明契约校验不是空转） | `1` | `—（CLI 直调，无 result.json）` | `—` | 0 | 无痕迹 | 否 | 符合期望 |
| 24 | 契约 | check_contract.py 指向不存在的 result.json | exit 1 且报 C01（缺产物必须是可判定的失败，不是 0） | `1` | `—（CLI 直调，无 result.json）` | `—` | 0 | 无痕迹 | 否 | 符合期望 |

### 2.1 读表要点

- **拒绝类故障（in-01/03、tpl 缺 schema 之外的资产）不是靠"崩"来拒绝**：入口用非零退出码 +
  明确的 `reason` 表达，未见"退出 0 却什么都没有"的情形（`in-01`/`in-03` 实测 exit=1 且**不写** `result.json`，
  因为它们连流水线都没进去 —— 这属于"入口拒绝"，不是"静默"）。
- **三类降级各自有专属退出码与 status**：`3/failed`（输入不可用）、`2/partial`（能出图但有降级）、
  `0/success`（无阻断）。契约探针 `ctr-01..05` 的 `exit=0/success` 是**正确**结果 ——
  它们注入的是"声明形态"，不是错误。
- **契约校验器不是空转**：`ctr-06` 往成功产物里塞一个顶层 `null` 再跑 `check_contract.py`，
  实测 `exit=1` 且报 `C04`；`ctr-07` 指向不存在的 `result.json`，实测 `exit=1` 且报 `C01`。
- **`tpl-03`/`tpl-04` 的 `exit=0` 是预期**：`templates/relation-checklist-template.md` 与
  `assets/result.template.json` 是**文档资产**（供 Agent 人工核验时使用），主流程不读取它们；
  删掉不改变行为，因此表里标 `N/A（无运行时消费者）` 而不是"静默失败"。
  这是**如实标注**：不要把它读成"包对资产缺失不敏感"。

## 3. 恢复演练（注入 → 修复 → 复跑）

对定义了修复动作的场景，`fault_inject.py` 会在**干净副本**上再跑一次：修复动作 = 去掉注入源，
其余输入不变。表内"恢复"列若为 `exit 0 / success`，即证明该失败是**可恢复的**，而不是把包跑坏。

| 场景 | 修复动作（= 去掉注入源后复跑） | 修复后实测 exit | 修复后实测 status | gates | 恢复判定 |
|---|---|---|---|---|---|
| `in-02-empty-material-dir` | 修好材料后：exit 0 / status=success | `0` | `success` | `8/8` | ✅ 已恢复 |
| `in-04-material-without-relations` | 改走已核验规格：exit 0 / status=success | `0` | `success` | `8/8` | ✅ 已恢复 |
| `in-05-unknown-entity-type` | 把类型改回枚举内：exit 0 / status=success | `0` | `success` | `8/8` | ✅ 已恢复 |
| `tpl-01-palettes-missing` | 把 assets/palettes.json 放回：exit 0 / status=success | `0` | `success` | `8/8` | ✅ 已恢复 |
| `dep-01-matplotlib-import-error` | 移除 PYTHONPATH 上的 stub：exit 0 / status=success（可恢复） | `0` | `success` | `8/8` | ✅ 已恢复 |
| `dep-03-formats-svg-only` | --formats svg,png,pdf：exit 0 / status=success | `0` | `success` | `8/8` | ✅ 已恢复 |

## 4. 演练发现的三处静默失败 + 纯增量修复（本版最重要的产出）

首轮演练（修复前）实测到 **3 处静默失败**：故障发生了，`exit=0`、`status=success`、
四个留痕位点全空。逐条给出"注入 → 修复前实测 → 根因（代码位置）→ 修复动作 → 修复后实测"。

### G1 · 端点不存在的边被静默丢弃（`in-08`）

| 项 | 内容 |
|---|---|
| 注入 | `--model-file` 里有一条边 `e2 → e999`，而实体清单里没有 `e999` |
| **修复前实测** | `exit=0` / `status=success` / `gates=8/8` / `uncertainty=0` / `self_check.warnings=0` —— 图面上**少了一条边，没有任何记录** |
| 根因 | `scripts/model.py: normalize_edges()` 对"端点 id 不在实体清单"的边直接 `continue`（原样保留，行为未改） |
| 为什么严重 | 机制图的每一条边都是一个**科学论断**；静默丢边 = 悄悄删掉一个论断，而 `result.json` 仍报 success |
| 修复（纯增量） | `scripts/model.py` **新增** `dropped_edges(raw)` 探针（+36 行，无删改）；`scripts/main.py` **新增** 一段把丢弃清单写进 `uncertainty`（+18 行，无删改） |
| **修复后实测** | `exit=0` / `status=success` / `uncertainty=1`：`"机制规格中有边被丢弃（未进入图面）"`，`reason` 精确到 `第 1 条边 e2→e999：端点 id 不在实体清单中`；`silent=False` |

### G2 · 调色板资产缺失/损坏被静默回退（`tpl-01`、`tpl-05`）

| 项 | 内容 |
|---|---|
| 注入 | ① 删掉 `assets/palettes.json`；② 把它改成非法 JSON |
| **修复前实测** | 两种注入都是 `exit=0` / `status=success` / `uncertainty=0` / `warnings=0`；探针显示"无从判断用没用上规范色板" |
| 根因 | `scripts/model.py: _load_palettes()` 用 `except Exception: return {}` 吞掉一切（原样保留，行为未改） |
| 为什么严重 | `SKILL.md` D18 与 `failure-modes.md` F07 **承诺**"回退内置默认调色板并记 uncertainty"；承诺与实现不一致 —— 是**文档骗人**，不是代码难看 |
| 修复（纯增量） | `scripts/model.py` **新增** `palette_load_status()` 探针（+20 行，无删改）；`scripts/main.py` **新增** 一段把回退写进 `uncertainty`（+7 行，无删改） |
| **修复后实测** | 两种注入均 `uncertainty=1`：`"调色板资产未加载，已回退内置默认"`，`reason` 区分 `FileNotFoundError` 与 `JSONDecodeError`；`silent=False`；正常运行（资产健康）实测 `uncertainty=0`，**不产生噪音** |

### G3 · CP1 的 warn 级降级在成功路径被丢掉（`in-07`）

| 项 | 内容 |
|---|---|
| 注入 | `case.json` 既没有 `task` 字段，目录里也没有 `task.md` |
| **修复前实测** | CP1.2 判定为 `warn`（探针复算确认），但成功路径只把 `cp1` 用于"是否 failed"判定，`warn` 被丢弃 ⇒ `exit=0` / `success` / 零留痕 |
| 根因 | `scripts/main.py` 的 CP1 段落只检查 `fail`（原样保留，行为未改） |
| 修复（纯增量） | `scripts/main.py` **新增** 一段把 `cp1` 中所有 `warn` 写进 `uncertainty`（+11 行，无删改） |
| **修复后实测** | `uncertainty=1`：`"CP1 前置检查降级：task 说明可用"`；`silent=False`；正常运行（有 `task.md`）实测 `uncertainty=0` |

### 4.1 修改清单（逐条点名，全部为纯增量）

| 文件 | 行数变化 | 性质 | 理由 |
|---|---|---|---|
| `scripts/model.py` | 381 → 437（**+56，−0**） | 纯增量：追加 `palette_load_status()`、`dropped_edges(raw)` 两个只读探针 | G1/G2 的"可观测性挂钩"；不改变任何既有函数行为 |
| `scripts/main.py` | 482 → 512（**+30，−0**） | 纯增量：1 行新 `import model as model_observability`，两段 `uncertainty.append` | 把 G1/G2/G3 三处静默写进结果（`uncertainty` 只增不减） |

- **CLI 参数名、默认值、退出码语义全部未改**：`--case/--task/--out/--materials-dir/--model-file/--formats/--dpi/--verbose` 原样；
  `0/2/3` 与 `partial/failed/success` 的对应关系不变（修复只增加 `uncertainty` 条目，不改变 status 判定）。
- 其余 9 个脚本与 `assets/`、`templates/` **逐字节未改**（可用 `sha256sum` 与基线包对拍）。

## 5. 复跑结果（一键判据）

```text
SUMMARY {"scenarios": 24, "expect_ok": 24, "mismatch": [],
         "silent_failures": [], "recovery": "6/6"}
```

- `expect_ok = 24/24`：每个场景的实测行为与"期望行为"一致（修复前是 21/24）；
- `silent_failures = []`：**没有**任何"错了但看不出来"的路径（修复前是 3 条）；
- `recovery = 6/6`：定义了修复动作的场景全部恢复到 `exit 0 / success`。

`fault_inject.py` 的退出码即判据：**0 = 全部符合期望；1 = 有场景不符（必须人看报告）**。

## 6. 边界与未覆盖（如实声明）

1. **`in-03`（case.json 不是合法 JSON）是非优雅退出**：实测 `exit=1` + `JSONDecodeError` 栈，
   **不写** `result.json`。入口拒绝是显式的（非静默），但没有把错误包装成结果信封 ——
   属**已知粗糙点**，未修复（修复需要改动 `resolve_paths` 的异常面，风险大于收益）。
2. **契约探针只覆盖四种声明形态 + 两个 CLI 负例**，未覆盖"平台自定义容器类型"（本次实测未遇到）。
3. **依赖形态用 stub 模拟**（`PYTHONPATH` 上放同名模块），不是真的卸载 matplotlib/Pillow；
   这能覆盖 `ImportError` 与 `RuntimeError` 两条分支，但**不能**模拟"matplotlib 装了一半/字体缓存损坏"这类半坏状态。
4. **`in-04`/`in-06` 走的是草稿路径**，因此 `exit=2` 里同时含"未人工核验"这一条 ——
   退出码无法区分"因为未核验"还是"因为材料只有实体"；`uncertainty` 逐条列出，**但退出码本身是粗粒度的**。
5. **G1 的修复只留痕、不阻断**：丢弃的边会写进 `uncertainty`，`status` 仍可能是 `success`。
   选择不阻断的理由：规格里有一条陈旧边 id 是**常见且可自行修正**的输入瑕疵，硬阻断会让
   合法但有瑕疵的材料直接失败；如需更严格，把该条目升级为 `fail` 即可（`self_check.failures` 会同步降级 status）。
