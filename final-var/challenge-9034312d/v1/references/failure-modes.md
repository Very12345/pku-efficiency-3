# failure-modes.md — 失败分支矩阵与决策规则（决策显性化版 v2.1）

> 本文件的组织方式与基线不同：它**按处置动作分组**，而不是按"现象像什么"分组。
> 理由：现象的描述方式无穷多（同一个断头箭头可以被写成"连错线""漏画单元""材料没写清"），
> 但**处置动作只有几种**——丢弃、归一化、降级、拦截、记账。按动作分组，才能保证
> "看到没见过的现象"时仍然能落到某一条规则上。
>
> 三张表：§1 决策规则索引（20 条）→ §2 失败分支矩阵（27 行，含可观测证据位点）→
> §3 安静缺陷（4 条，本包会放过但必须点名）→ §4 打包门 R1–R6。
> 可执行伴生件：`references/DECISION-CASES.md`（20 个用例的期望判决 vs 实测观测值）
> 与 `scripts/decision_probe.py`（一次跑完全部用例）。

## 0. 处置动作的五种类型（先把动作定死）

| 动作 | 含义 | 会不会污染交付物 | 典型证据位点 |
|-|-|-|-|
| **丢弃** | 该元素不进图面（如断头关系） | 不污染，但要记账 | `verify.checks.no_dangling`；输入/输出条数差 |
| **归一化** | 用最近的合法值顶替非法值 | **会**（原值消失） | `verify.checks.*_vocabulary`（此时恒为 true） |
| **降级** | `status` 从 `success` 落到 `partial`/`failed`，退出码变 1/3 | 不污染内容，污染"完成度声明" | `status`；`uncertainty[].scope`；`check.py` 门号 |
| **拦截** | 退出码 3，门报失败，强制人工处置 | 同上（交付物还在，但不能当完成品） | `check.py` 的 `gates`/`issues` |
| **记账** | 只写 `uncertainty`/`change_record`/`warnings`，不改状态 | 不污染 | `uncertainty[]`；`change_record[]`；`verify.warnings[]` |

**读法**：§2 每一行右端都标了它属于哪一类动作。看到"降级/拦截"就该去修；
看到"记账"就该去人读；看到"归一化"就该回头核对原始材料。

## 1. 决策规则索引（D1–D20）

分组与 SKILL.md §6 一致：输入域 4 条、结构与连接域 7 条、导出域 3 条、契约域 4 条、
状态域 2 条。

| 规则 | 域 | 触发（可观测） | 动作类型 | 状态影响 | 权威定义处 |
|-|-|-|-|-|-|
| D1 | 输入 | `--case` 指到的文件不存在 | 拦截 | 无产物，退出码 2 | `main.py` 参数校验分支 |
| D2 | 输入 | JSON 语法坏 | 降级 | `failed`，退出码 1，写 `failed/result.json` | `main.py` 异常兜底 |
| D3 | 输入 | 无结构化实体但有文本 | 记账 | 不降级；`extraction=text-heuristic` | `model.text_entities` |
| D4 | 输入 | 材料被引用却读不到 | 记账 | 不降级；证据条数变少 | `gain_evidence` 的 `sources[]` |
| D5 | 结构 | 关系端点不存在 | 丢弃 | 不降级；`no_dangling=true` | `model._parse_relations` |
| D6 | 结构 | 实体无任何连接（孤儿） | 降级 | `partial` | `model.build_model` 末尾一致性自查 |
| D7 | 结构 | 实体 id 重复 | 归一化 | 不降级；改名后又触发 D6 | `model.build_model` 的 id 唯一化 |
| D8 | 结构 | 画布装不下实体 | 归一化 | 不降级；`canvas.requested` 留原值 | `layout.compute_layout` |
| D9 | 结构 | 类别/关系种类非法 | 归一化 | 不降级（**安静缺陷 #2**） | `model._norm_kind/_norm_relation_kind` |
| D10 | 结构 | warn 级规则命中 | 记账 | **永不**改 `status` | `svg_verify` 的 `warnings[]` |
| D11 | 结构 | 实体缺 `source` | 记账 | 不单独降级 | `model.build_model` 的 `missing_src` |
| D12 | 导出 | PNG 或 PDF 渲染失败 | 降级 | `partial`（两个都失败且无实体 → `failed`） | `main.run_case` 的 `png_fail/pdf_fail` |
| D13 | 导出 | SVG 非法 XML / 图层或文本不达标 | 拦截 | 修不好则 `partial` | `svg_verify` 的 `layers/editable_text` |
| D14 | 导出 | 本机无中文字体 | 记账 | 不改 `status` | `fonts.font_report` |
| D15 | 契约 | `result.json` 缺字段或类型不符 | 拦截 | 退出码 3 | `check.py` G1/G2/G5/G6 |
| D16 | 契约 | 材料内部自相矛盾 | 记账 | 不降级 | `uncertainty[scope=ambiguity]` |
| D17 | 契约 | 契约某段为空（`null`/缺键） | 归一化 | `null` 触发降级；`[]`/`""`/`{}` 合法 | `check.py` G2 |
| D18 | 契约 | error 级规则违规未解决 | 降级 + 拦截 | `partial`，退出码 3 | `svg_verify.errors[]` |
| D19 | 状态 | 未预期异常 | 降级 | `failed`，退出码 1 | `main.main` 的兜底写入 |
| D20 | 状态 | 人工改图未记录 | 记账 | 不降级（隐瞒才是问题） | `change_record[]` |

## 2. 失败分支矩阵（27 行）

列义：**现象**（你实际能看到什么）→ **规则** → **动作** → **降级后果** → **核对位点**
（照这个位点查，能在任何一次运行里复现同一结论）。

### 2.1 材料异常（输入侧）

| # | 现象 | 规则 | 动作 | 降级后果 | 核对位点 |
|-|-|-|-|-|-|
| 1 | `--case` 文件不存在 | D1 | 拦截 | 无任何产物；退出码 2 | stderr 末行 `FATAL:` |
| 2 | `case.json` JSON 语法坏 | D2/D19 | 降级 | `failed` + `failed/result.json`；退出码 1 | `failed/result.json.error` |
| 3 | 只有自由文本、无结构化实体 | D3 | 记账 | 不降级；解构仅串联相邻步骤 | `extraction=text-heuristic`；`uncertainty[scope=relations]` |
| 4 | 材料文件被引用但读不到 | D4 | 记账 | 不降级；证据条数变少 | `evidence.source_files[]` 与 `evidence.notes[]` |
| 5 | 同一实体两种类别 / 方向相反 | D16 | 记账 | 不降级；等 Agent 裁决 | `uncertainty[scope=ambiguity]` |
| 6 | 实体名重复或高度近似 | D7→D6 | 归一化→降级 | 产生一个孤儿实体 → `partial` | `entities[].id`（出现 `_2` 后缀）；`orphan_entities` |
| 7 | 材料给出的类别不是词表里的值 | D9 | 归一化 | **安静**：原值消失 | `evidence.entities[].kind` vs 原始材料 |

### 2.2 连接与顺序正确性

| # | 现象 | 规则 | 动作 | 降级后果 | 核对位点 |
|-|-|-|-|-|-|
| 8 | 单条关系端点不存在 | D5 | 丢弃 | 不降级；若因此产生孤儿 → D6 | `verify.checks.no_dangling=true`；条数差 |
| 9 | **全部**关系端点都不存在 | D5→顺序兜底 | 丢弃 + 归一化 | **安静**：退化成顺序链，报 `success` | `relations[].source` 是否全为 `text:order` |
| 10 | 有实体没有任何连接 | D6 | 降级 | `partial` | `uncertainty[scope=orphan_entities]` |
| 11 | `sequence` 连到非步骤实体 | D18 | 降级 + 拦截 | `partial`；退出码 3 | `verify.errors[].rule=sequence-step-only` |
| 12 | `connect` 两端都不是结构件 | D18 | 降级 + 拦截 | `partial`；退出码 3 | `verify.errors[].rule=connect-structural` |
| 13 | 装置图里物料成为流向终点 | D18 | 降级 + 拦截 | `partial`；退出码 3 | `verify.errors[].rule=apparatus-flow-into-material` |
| 14 | 装置图产物继续流出 | D10 | 记账 | **不降级** | `verify.warnings[].rule=product-terminal` |
| 15 | 自环关系 | D18 | 降级 + 拦截 | `partial`；退出码 3 | `verify.errors[].rule=no-self-loop` |
| 16 | `recycle` 回流存在 | D10 | 记账 | **不降级** | `verify.warnings[].rule=recycle-review` |
| 17 | route/flow 步骤编号断号 | D13/D18 | 拦截 | `partial`；退出码 3 | `verify.checks.numbering_continuous=false` |
| 18 | 图例 kind 集合与图面不一致 | D13/D18 | 拦截 | `partial`；退出码 3 | `verify.checks.legend_kinds=false` |
| 19 | 箭头与关系不是一一对应 | D13/D18 | 拦截 | `partial`；退出码 3 | `verify.checks.arrows=false` |

### 2.3 模板与依赖

| # | 现象 | 规则 | 动作 | 降级后果 | 核对位点 |
|-|-|-|-|-|-|
| 20 | 自定义 `--rules` 是空对象 | D9/D10 | 归一化 | **安静**：审计空转，退出码仍 0 | `verify.checks.connection_rules=true` 但规则数为 0 |
| 21 | 自定义 `--rules` 路径不存在 | D9/D10 | 归一化 | **安静**：同上（读取异常被吞） | 你传给 `--rules` 的路径是否存在 |
| 22 | 无 Pillow | D12 | 降级 | 无 `figure.png`；`partial` | `uncertainty[scope=png]`；`exports[]` 缺 png |
| 23 | 无 reportlab | D12 | 降级 | 无 `figure.pdf`；`partial` | `uncertainty[scope=pdf]`；`exports[]` 缺 pdf |
| 24 | 无中文字体 | D14 | 记账 | 不改 `status`；PNG 可能缺字 | `fonts[role=png].found=false` |
| 25 | `templates/palette.json` 不可读 | D9 | 归一化 | 回落到内置默认配色 | `templates/palette.json` 是否可解析 |

### 2.4 契约四形态与状态一致性

| # | 现象 | 规则 | 动作 | 降级后果 | 核对位点 |
|-|-|-|-|-|-|
| 26 | 契约某段为 `null` 或缺键 | D17 | 拦截 | 退出码 3；不得 `success` | `check.py` G2/G5/G6 的 `issues[]` |
| 27 | 契约四段是列表但内容为空 | D17 | 记账 | **不降级**：空列表合法 | `check.py` `issues=[]` |
| 28 | `verify.ok=false` 却报 `success` | D18 | 拦截 | 被 G10 拦下，退出码 3 | `check.py` G10 |
| 29 | `--merge` 引入不存在的端点 | D5/D15 | 拦截 | G6/G7/G9 报失败，退出码 3 | `check.py` G6/G7/G9 |
| 30 | 人工改了 `figure.svg` 未记录 | D20 | 记账 | 不降级；但 `checksum` 与记录对不上 | `change_record[]`；`checksum` |
| 31 | 未预期异常 | D19 | 降级 | `failed`；退出码 1 | `failed/result.json`；stderr traceback |

> 行号 1–31 是**分支**编号（不是规则编号）；SKILL.md §7 用的是同一批分支的精简视图。
> 本矩阵按动作分组，SKILL.md §7 按"你看到什么"排序，两份互为索引。

## 3. 安静缺陷清单（本包会放过、但必须点名的 4 条）

这四条**不会报错、不会降级、不会进 `warnings`**。把它们写在这里，是为了让复核者知道
往哪里看，而不是让它们藏起来。

| # | 安静缺陷 | 为什么会安静 | 危害 | 复核办法 | 打算怎么修（未在本版实施） |
|-|-|-|-|-|-|
| A1 | 全部关系被丢弃后退化成顺序链 | 关系集合为空是"合法的空"，模型按设计走文本顺序兜底 | 非法输入被静默"修好"，评分者看到的是自洽但不真实的图 | 看 `relations[].source` 是否全为 `text:order`；对比输入关系条数 | 在 `result.json` 增加"被丢弃关系计数"并在 >0 且输出为空时强制 `partial` |
| A2 | 非法类别/关系被静默归一化 | 容错归一化是刻意的（宁可画出图也不崩） | 材料里的类别错误不再可见 | 对比 `evidence.entities[].kind` 与原始材料取值 | 归一化时把原值写进 `entities[].props.raw_kind` 并记 `uncertainty` |
| A3 | `--rules` 空/缺失使审计空转 | 读规则失败被 `except` 吞掉，规则集为空即"无违规" | 看起来全绿、实际没审 | 核对你自己传的 `--rules` 路径是否存在、内容是否非空 | 读规则失败时在 `verify.checks` 里单独记 `rules_loaded=false` 并降级 |
| A4 | 缺 `source` 不单独降级 | D11 的记账语义（缺出处不等于交付不可用） | 若同时无其它缺陷，交付可核验性被高估 | `verify.checks.entity_source_coverage` | 保持现状（这是设计选择），但在 SKILL.md 里明确提示复核者看这一项 |

> 处理原则：**先记录，再改进**。本版选择把四条的复核方法写清楚，而不是偷偷加一个
> "自动降级"把所有包都打成 `partial`（那会让状态失去区分度）。

## 4. 资源形态与打包门（R1–R6）

依据题面英文契约原文：*Skill resources: at most 50 UTF-8 text files, 500KB each and
2MB total, no symlinks. Runtime artifacts may be binary and are retained independently
of final JSON validity.* 违反形态门的包在预检阶段就会被拒（"不支持的文件类型"/"文件数量超限"），
**与算法质量无关**，所以形态也做成可自查的门。

| 门 | 规则 | 违反后果 | 检查方式 |
|-|-|-|-|
| R1 文本白名单 | 只允许 `.md .py .json .txt .csv .yaml .yml`（小写） | 预检报"不支持的文件类型" | 按扩展名扫描 |
| R2 文件数 | ≤ **50** 个（按 `outputs/` 计；平台还会复制一份到 `results/`） | 预检报"文件数量超限" | 数文件（本包：见 `TEST.md` T0） |
| R3 体积 | 单文件 ≤ **500KB**，合计 ≤ **2MB** | 预检拒绝 | 统计字节 |
| R4 符号链接 | 不允许 | 预检拒绝 | `os.path.islink` |
| R5 无 `__pycache__` | 不得有 `__pycache__/`、`*.pyc` | 形态门 FAIL | 扫描（所有脚本首部已置 `sys.dont_write_bytecode = True`） |
| R6 无本机绝对路径 | 不得出现「盘符+反斜杠」形态、`/Users/…`、以及 Windows 长路径（UNC 扩展）前缀 | 形态门 FAIL，且误导回放 Agent | `grep -rnE '(^|[^A-Za-z])[A-Za-z]:[\/]' <包目录>` 应无输出；`python validate_pkg.py <包目录>` 应 PASS |

**本包自检命令**（与 `README.md §8` 一致）：

```bash
python validate_pkg.py <本包目录>                      # 期望 [PASS]，0 条 FAIL
grep -rnE '(^|[^A-Za-z])[A-Za-z]:[\\/]' <本包目录>      # 期望无输出
```

字体探测候选路径属跨平台探测逻辑（`scripts/fonts.py`，Windows 根优先取 `%WINDIR%`，
全部写作正斜杠形式），**在交付说明里点名**，不属于 R6 违规。
