# GAIN-PROTOCOL.md — 使用增益的公平对照协议与实测记录

> 本文件是 **使用增益（25 分：质量增益 15 · 效率增益 5 · 增益可验证性 5）** 的落点。
> 它做三件事：① 写清对照的公平性条件；② 把"更强"拆成可测指标并定义测量方法；
> ③ 附上**本包真实跑出**的对照记录（数字、命令、返工清单原文），可由第三方复跑。

## 0. 为什么要写成协议

题面的权威对照由平台生成：固定案例会以相同内容分别交给**基础 Agent** 和**加载参赛 Skill
的 Agent**，用同一套白板指标比较。参赛者不提供隐藏测试、不预写答案，也**不应把自测数字
冒充平台分数**。

但"等平台出结果"不构成可复核的证据。于是一个中间层次是必要的：
**把基础 Agent 的行为实现成一条可执行的朴素流水线，在完全相同的输入上跑两臂，
用同一个评审函数逐格测量。** 这就是 `scripts/gain_probe.py`，本节其余部分定义它的
口径边界——**说清它不是什么，比说它是什么更重要**。

## 1. 公平性条件（四同）

| 条件 | 本协议的做法 | 为什么这样才公平 |
|-|-|-|
| **同输入** | 两臂读**同一个** `case.json`、同一份材料、同一份 `deck-spec.json`（基线臂也读同一材料，抽取后按自然段切块） | 差异只能来自"有没有这套机制"，不能来自换了一份更容易的材料 |
| **同模板** | 记录两种条件：**条件 T**（副本内先用 `make_template.py` 现产一份模板，两臂都在模板在场时运行）、**条件 N**（无模板，考察回退分支）；两种条件的数字分开记录，不混用 | 模板在场与否会改变可比的产出面，混记录会把"条件差异"误报成"能力差异" |
| **同版本** | 两臂都跑**同一份包的同一个副本**；`run_meta.skill_version` 与 `scripts/main.py` 的 `VERSION` 一致 | 避免"用新脚本比旧脚本" |
| **同预算** | 平台的运行预算（64 次模型请求 / 900 秒 / 单响应 16384 tokens）对两臂相同；本协议额外固定 `--repeat` 次数（默认 2）以便测量确定性，并把 `wall_seconds` 逐次记录 | 效率对比必须同预算；重复次数不同会让"更稳"变成"跑得更多" |

**页码上限也相同**：两臂使用 `case.json` 的页数约束；基线臂不做裁剪，因此它的
"超限正文框"恰好成为指标之一（`over_limit_frames`），而不是被悄悄修掉。

## 2. 三臂定义与口径边界

| 臂 | 是什么 | 不是什么 |
|-|-|-|
| `baseline` | **朴素单遍流水线**：读材料 → 按自然段切块 → 每块贴一页（默认 16:9 母版，无模板适配）→ 把 `case.json` 声明的契约键名按容器给空值回显。这是"不加载本 Skill 的基础 Agent"在**可执行层面**的代理 | **不是**对某个具体 LLM 的测量；真实基础 Agent 可能比它强或更弱。它测的是**结构差异的下界** |
| `skill` | 本包 `scripts/main.py` 全链路：Q1 lint → 抽取 → 构建（模板占位符级适配 / 对象命名 / 主题字体）→ 备注分离 → 证据映射双形态 → 预览 → Q3 检查 → 契约完整 result.json | **不是**平台白板分数；不代表正式 3 个案例上的得分 |
| `ablation` | `main.py --demo`：脚本、契约、闸门都在，**只去掉 Agent 写的页级方案与 Q1 前置门**（改用自动骨架） | **不是**"删掉脚本"的对照；它专门隔离"方案先行 + 页级证据"这一项机制的贡献 |

> 关键纪律：三臂由**同一个 `_review()` 函数**测量（`gain_probe.py` 内），
> 因此不存在"给自家臂用宽松尺子"。基线的失败项同样逐条列在报告里，不做美化。

## 3. 指标定义（名字 / 怎么测 / 单位 / 判据）

| 指标 | 怎么测 | 判据方向 |
|-|-|-|
| `claim_coverage` | `result.json.slides[]` 中 `claim` 非空的页占比 | 越高越好；基线预期 0 |
| `substantive_claim_coverage` | 在上一条基础上排除含占位标记（`SKELETON`/`骨架`/`待补`/`TODO`/`占位`）的主张 | 加载后应为 1.0；消融臂会掉下来 |
| `placeholder_claims` | 上述占位主张的页数 | 越低越好（诚实性指标） |
| `evidence_rows` | `evidence_mapping.md` 里以 `|` 开头的表行数减去表头与分隔行 | 应等于声明 `entries` |
| `evidence_locations` | `evidence_map.json` 的 `rows[]` 中同时具备定位（`location` 或 `evidence`）且 `status != "gap"` 的行数 | 越高越好；基线为 0 |
| `contract_fields_present` | 与 `references/OUTPUT_CONTRACT.md` §1 同源的 19 个顶层字段中实际出现的个数（探针从该文档解析字段名） | 加载后应 19/19；基线预期远低 |
| `notes_pages` | 直接遍历 `.pptx`：有非空 notes 文本的页数 | 应等于总页数（备注分离且每页都有） |
| `named_shapes` | `.pptx` 内形状名命中 `layer-naming.md` 前缀（`claim-*`/`body-bullets-*`/`figure-*`…）的形状数 | 越高越可编辑；模板在场时较低是正常的（占位符被复用而非改名） |
| `over_limit_frames` | 直接遍历 `.pptx`：段落数 > 6 或单段 CJK 加权长度 > 220 的文本框数（加权规则与 `spec_lint._bullet_len` 相同） | 应为 0 |
| `deck_reopenable` / `slide_count_matches` | 用 python-pptx 重开，并比对 `deck.slide_count` | 两者都应为真 |
| `artifacts` | 输出目录内文件总数 | 参考值（反映交付面完整度） |
| `rework_points` | **同一套一致性检查**的失败计数：缺 `result.json` / status 不在词表 / 契约字段缺失 / 声明字段为 null / 无证据映射文件 / 表行数 ≠ 声明 entries / 声明预览缺文件 / deck 不可重开 / 页数不一致 / 有页无主张 / 有占位主张 / 备注未覆盖全部页 / 存在超限正文框 | 越低越好；这是"交付前还要返工几次"的代理量 |
| `wall_seconds` | 每臂端到端墙钟时间，`--repeat` 逐次记录 | 只作参考：本机数值依赖机器与案例规模，**不作绝对承诺** |
| `differing_opc_parts` | 同臂两次运行的 `.pptx` 逐 OPC 部件 sha256 比较，输出不同部件数 | 应为 0（同输入确定性） |

指标全部落在 `--out/gain-report.json`，逐臂可查；`rework` 数组里保留**失败原因原文**，
便于复核者逐条认领。

## 4. 实测记录（本机真实运行，未做人工挑选）

运行环境：Windows-11-10.0.22621-SP0 / Python 3.13.9 / python-pptx 1.0.2 / Pillow 12.3.0 /
matplotlib 3.10.6 / PyMuPDF 1.28.0；**无 LibreOffice**（预览一律 PIL 近似）。
输入：`examples/case.json`（合成示例案例 `example-ppt-c7b80f0d`，8 页上限）+
`examples/deck-spec.json`（6 页页级方案）。`--repeat 2`，契约字段核对数 19。

复跑命令（在**包外临时副本**上执行，`$PKG` = 该副本）：

```bash
export PYTHONDONTWRITEBYTECODE=1
python "$PKG/scripts/gain_probe.py" --out "<scratch>" \
       --arms baseline,skill,ablation --repeat 2
# 退出码 0；报告写在 <scratch>/gain-report.json
```

### 4.1 条件 T —— 模板在场（先跑 `make_template.py --out "$PKG/examples"`）

| 指标 | `baseline` | `skill` | `ablation` |
|-|-|-|-|
| `rework_points` | **6** | **0** | 2 |
| `claim_coverage` | 0.0 | **1.0** | 1.0 |
| `substantive_claim_coverage` | 0.0 | **1.0** | **0.0** |
| `placeholder_claims` | 0 | 0 | 1 |
| `evidence_rows` | 0 | **6** | 1 |
| `evidence_locations` | 0 | **6** | 0 |
| `contract_fields_present`（/19） | 7 | **19** | 19 |
| `notes_pages`（总页数） | 0（3） | **8（8）** | 3（6） |
| `named_shapes` | 0 | 3 | 2 |
| `over_limit_frames` | **2** | **0** | 0 |
| `artifacts` | 2 | 13 | 6 |
| `template_adapted` | false | **true** | true |
| `wall_seconds`（两次） | 0.028 / 0.022 | 2.155 / 2.508 | 1.490 / 1.109 |
| `differing_opc_parts`（两次运行） | 0（42 部件） | **0（72 部件）** | 0（57 部件） |
| 子进程退出码 | —（库内直跑） | 0 / 0 | 0 / 0 |

`baseline` 臂的 `rework` 原文（6 条，逐字保留）：

```
contract top-level fields missing: task,evidence_mapping,evidence_map_json,spec_lint,previews,charts
no slide carries a page-level claim
no evidence mapping file on disk
no machine-readable evidence map
notes not present on every slide (0/3)
2 text frame(s) exceed the overflow guard
```

`ablation` 臂的 `rework` 原文（2 条）：

```
1 slide(s) carry placeholder claims instead of real ones
notes not present on every slide (3/6)
```

`skill` 臂的 `rework` 为空数组（0 条），且两次运行的 72 个 OPC 部件逐部件一致。

### 4.2 条件 N —— 无模板（考察回退分支）

| 指标 | `baseline` | `skill` | `ablation` |
|-|-|-|-|
| `rework_points` | 6 | **0** | 2 |
| `substantive_claim_coverage` | 0.0 | **1.0** | 0.0 |
| `evidence_rows` / `evidence_locations` | 0 / 0 | **6 / 6** | 1 / 0 |
| `notes_pages` | 0 | **8** | 3 |
| `named_shapes` | 0 | **17** | 6 |
| `wall_seconds` | 0.024 | 1.880 | 1.745 |

条件 N 下 `named_shapes` 从 3 升到 17：模板缺失时走内置版式，标题/正文/图注/页脚等
对象全部由本包创建并按 `layer-naming.md` 命名；模板在场时大量对象是**复用组织方占位符**，
按铁律不改名，所以该数较低——这是设计使然，不是能力下降。

### 4.3 按机制读消融（v3 追加：把差值归因到具体机制）

`ablation` 臂不是"删掉脚本"，而是**只摘掉一项机制**（Agent 写的页级方案 + Q1 前置门）。
把 §4.1 的两列相减，差值就能归因到机制 **M2**（见 `references/MECHANISM.md` §2.M2）：

| 指标 | `skill`（M2 生效） | `ablation`（M2 摘除） | 差值的方向说明 |
|-|-|-|-|
| `substantive_claim_coverage` | 1.0 | **0.0** | 主张退化为 `SKELETON（示例骨架…）` 占位文本 |
| `placeholder_claims` | 0 | **1** | 该指标专门识别占位标记，避免"有 claim 就算数"的误读 |
| `evidence_rows` | 6 | **1** | 没有页级方案就没有结构化证据映射可生成 |
| `evidence_locations` | 6 | **0** | 自动骨架的映射行 `status=gap`，带定位的行数为 0 |
| `notes_pages`（总页数） | 8（8） | 3（6） | 备注分离机制仍写备注，但页数本身少了、覆盖不全 |
| `rework_points` | **0** | **2** | 返工清单原文：1 页占位主张 + 备注 3/6 页 |

读法：**M2 是可归因的**——它一变，上面六个数同时朝坏的方向动；而 M1（契约同源）
在消融臂里仍然 19/19，说明消融没有"顺带打坏别的机制"。这正是把差值归因到单一机制的
证据链；反过来，如果所有指标一起崩，就不能声称"是这一项机制在起作用"。

**边界**：本表只覆盖"页级方案 + Q1"这一项机制的消融。M4/M5/M6/M7/M9 的反事实证据是
本族代码史或平台实测记录（见 `MECHANISM.md` §2 各条），**不是**本探针产出的数字，
两者不可混为一谈。


## 5. 这些数字能推出什么、不能推出什么

**能推出（结构性事实，可逐格复核）**：

1. 在同一输入上，加载本 Skill 后每一页都有一条**非占位**的页级主张，而朴素基线一条也没有；
2. 证据映射（人读 md + 机读 json）与契约 19 字段在基线里**完全不存在**，在加载后完整存在；
3. 备注分离与溢出保护在基线里失败（0 页备注、2 个超限正文框），加载后为 8/8 与 0；
4. 交付前的"返工点"从 6 降到 0；
5. 去掉"方案先行 + Q1 前置门"后（`ablation`），主张退化为占位内容、证据行数从 6 掉到 1、
   备注只覆盖 3/6 页 ⇒ 这项机制是**可归因的**，不是"整体感觉更好"。

**不能推出（不要过度解读）**：

- 这些数字**不是**平台白板分数，也不能换算成分数；正式 3 个案例由平台评分；
- `wall_seconds` 只说明脚本开销（秒级），不构成"总耗时更短"的结论——
  真正的效率增益还包含人工修改页数，而后者需要在平台上按白板口径测量；
- 单一示例案例上的对照不能外推到所有论文类型；材料类型（PDF 扫描件、多图论文）
  的差异应由 `failure-modes.md` 的分支覆盖，而不是由本记录覆盖。

## 6. 复跑与维护

```bash
# 1) 复制包到包外临时目录（不要在包内跑其余脚本）
# 2) 条件 T：先在副本内生成示例模板
python "$PKG/scripts/make_template.py" --out "$PKG/examples"
# 3) 三臂对照
python "$PKG/scripts/gain_probe.py" --out "<scratch-T>" --arms baseline,skill,ablation --repeat 2
# 4) 条件 N：换一个没生成模板的副本，重复第 3 步
# 5) 报告在 <scratch-*>/gain-report.json —— 逐臂 metrics 与 rework 原文
```

`gain_probe.py` 只写 `--out`；它对子进程设 `PYTHONDONTWRITEBYTECODE=1`，
因此**可以在包内原地调用而不产生 `__pycache__`**。其余脚本请在包外副本上运行。

**维护规则**：任何改动若会影响 §4 的数字（脚本、模板策略、命名规则、契约字段），
必须重跑本协议并把**新数字**写回 §4，同时更新 `TEST.md` 的对应条目；
**禁止沿用旧数字**。指标定义若变化，同步更新 §3 与 `scripts/gain_probe.py` 的
`_review()`，保持文档与代码同源。
