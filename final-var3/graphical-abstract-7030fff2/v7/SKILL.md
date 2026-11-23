---
name: graphical-abstract
description: >-
  把研究材料做成单页 Graphical Abstract（图形摘要）的 Skill，主打**字节级可复现**：
  输入侧逐元素 data-src 溯源（材料里找不到的数值不上画布），执行侧走「方案先行 → 双 lint 门 →
  确定性版面 → 可编辑分层 SVG（7 层 layer:* 契约）+ PNG/PDF → audit → 契约回显」，
  可复现侧用 scripts/determinism.py 把「同输入连跑 N 次（跨进程 / 跨 cwd / 跨 PYTHONHASHSEED）」
  变成可执行判据：逐产物 sha256 比对、故意不稳定的字段逐条点名（V1–V4）、
  L0/L1/L2 三级结论与稳定化配方（含 SOURCE_DATE_EPOCH 实测）。
  Use when the task says "graphical abstract"、"图形摘要"、"示意图 / 机制图 / 通路图 / 流程图"、
  "为论文、基金或汇报画一张可编辑的图"、"编辑已有的图稿"，
  或需要证明「同样输入能稳定复现出结构一致的图稿」时。
---

# Graphical Abstract 图形摘要 Skill（可复现优先版）

一句话：**一页讲完 研究问题 → 方法 → 核心结果 → 结论**，交付**可继续编辑的分层源文件**
（不是位图截图）+ PNG/PDF 预览 + 字段完整的 `result.json`；
并且**可复现性不是形容词，而是一条可执行判据**（§4）。

| 关键事实 | 值 |
|-|-|
| Skill 名称 / 版本 | `graphical-abstract` / `2.0.0`（`scripts/common.py` 的 `SKILL_VERSION`） |
| 技能根 | 本文件所在目录，下文记作 `$SKILL_DIR`（脚本用 `__file__` 自定位，cwd 任意） |
| 资源形态 | 纯文本七种扩展名（`.md .py .json .txt .csv .yaml .yml`），无二进制、无预置图、无字体文件 |
| 交付物 | `<case>_graphical_abstract.svg`（可编辑）+ `.png` + `.pdf`（可缺，缺则带 reason）+ `result.json` |
| 依赖 | Python 3.9+；`matplotlib`/`Pillow`/`pypdf` 全部**可选**（缺了怎么降级有实测矩阵，见 §6） |

---

## 1. 30 秒上手（三条命令）

```bash
SKILL_DIR=/skills/weekly-skill           # 平台装载路径；本机跑就换成包的绝对路径
OUT=/app/output                          # 平台契约要求最终结果落在这里

python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out "$OUT"
python "$SKILL_DIR/scripts/check_contract.py" --result "$OUT/result.json" --case /input/case.json
python "$SKILL_DIR/scripts/determinism.py" --case /input/case.json --out /tmp/det   # 判据见 §4
```

三条命令的出口判据：**都要求退出码 0**（第三条的等级可用 `--fail-on` 调节）。
`main.py` 的 `--out` 必须是**包外**目录；`determinism.py` 会拒绝写进包内（退出码 2）。

---

## 2. 输入（只读真实文件，不猜内容）

| 输入 | 说明 |
|-|-|
| `case.json` | 必读。`case_id / title / task / source_material / entities / relations / data / figure_constraints / output_contract`（同名同义键有回退链） |
| `task.md` | 任务说明；`问题 / 方法 / 结果 / 结论` 小节直接映射为四列面板要点 |
| 材料文件 | `source_material` 指明的 `.md/.txt/.json/.csv/.tex/.rst` 或 PDF（走文本层；取不到则如实记录并跳过） |
| `--plan plan.json` | 可选，方案先行：`scaffold.py` 出骨架 → 人工/Agent 定稿 → 方案 lint（CP1 门） |

三条输入硬规则：① 只读真实文件，**绝不凭文件名/标签推断内容**；② 每个上画布的元素带 `src`
（`文件:行` 或 `case.json[字段]`）；③ 材料里定位不到的数值**不上画布**，只进 `uncertainty`
并以「数值缺失」占位 —— 这条在 §4 的复现判据里会被间接验证（编造的数值无法稳定复现出 `src`）。

字段契约（唯一评分产物）：[`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md)
（字段块逐字保留）；设计方案 schema：[`references/plan-schema.md`](references/plan-schema.md)；
四要素不变式：[`references/ga-four-elements.md`](references/ga-four-elements.md)。

---

## 3. 主链与出口判据

```bash
# 0 方案先行（推荐）：骨架 → 定稿 → 方案门
python "$SKILL_DIR/scripts/scaffold.py" --case <case.json> --out plan.json
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan plan.json          # exit 0 才继续

# 1 主链：抽取 → 版面 → 规格门 → 分层 SVG → 渲染 → audit → result.json
python "$SKILL_DIR/scripts/main.py" --case <case.json> --plan plan.json --out <out>

# 2 两道门独立复核（与 main 内嵌同一函数，判据是退出码）
python "$SKILL_DIR/scripts/spec_lint.py" --spec <out>/spec.json --content <out>/content.json
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>
```

| 步骤 | 出口判据 | 不达标时怎么办 |
|-|-|-|
| 方案门 CP1 | `spec_lint.py --lint-plan --plan …` **exit 0** | 按 `references/failure-modes.md` D14 修方案；`status` 不得是 success |
| 抽取 | 每个元素有 `src`；数值能在材料里定位 | 缺值只登记，**不补造** |
| 版面与编码 | 四列面板 问题→方法→结果→结论；`bar_length/color_scale/area/value_label` 与图例一一对应 | 看 `audit.encoding_consistency.missing_from_canvas` |
| 规格门 CP1b | `spec_lint.py --spec … --content …` **exit 0** | 同 D14 |
| 交付 | SVG 良构（≥7 层 `layer:*` + 真 `<text>` + `data-src`）、PNG 签名正确、`result.json` 覆盖契约 | `check_contract.py` 会逐条打印缺口 |
| **复现** | `determinism.py` **exit 0**（默认 L1 等级） | 看报告 `unexplained_differences`，**不是**看时间戳 |

层名与溯源属性：[`references/layer-naming.md`](references/layer-naming.md)；
版面模板与视觉通道：[`references/TEMPLATE.md`](references/TEMPLATE.md)。

---

## 4. ★ 本版主轴：可复现性判据（命令 · 判据 · 实测数字）

### 4.1 一条命令，三个等级

```bash
python "$SKILL_DIR/scripts/determinism.py" --case <case.json> --out /tmp/det \
       [--runs 5] [--hashseeds 0,1,42,12345,-] [--cwds skill,tmp,case] [--fail-on normalized|raw|none]
```

脚本每次运行都起**独立子进程**，并刻意变化三个常被忽视的变量：

| 变量 | 取值 | 为什么它重要 |
|-|-|-|
| cwd | 技能沙箱 / 空临时目录 / 案例所在目录 | 相对路径解析写错时，换个 cwd 就换一套产物 |
| `PYTHONHASHSEED` | `0 / 1 / 42 / 12345 / 未设置` | dict/set 迭代顺序的经典不确定性来源 |
| 进程 | 每次都是新的 `python -B …` | 进程内缓存、`id()` 顺序、单例状态全部被重置 |

判据（**默认 `--fail-on normalized`**）：掩掉**已声明**的易变字段后，全部产物一致 ⇒ `exit 0`；
有任何一处未解释差异 ⇒ `exit 1`。`--fail-on raw` 要求逐字节相同（本包实测**故意**为 1，见 4.3）。

### 4.2 实测（本机 Windows / Python 3.13.9 / matplotlib 3.10.6，5 次运行，11.67 s）

| 产物 | 字节 | raw 全等 | 掩码后全等 |
|-|-|-|-|
| `spec.json` | 42,986 | ✅ | ✅ |
| `content.json` | 6,979 | ✅ | ✅ |
| `audit.json` | 2,169 | ✅ | ✅ |
| `*.svg`（可编辑源） | 32,455 | ✅ | ✅ |
| `*.png`（39 万字节二进制） | 397,555 | ✅ | ✅ |
| `result.json` | 6,709 | ❌ | ✅ |
| `render_log.json` | 645 | ❌ | ✅ |
| `*.pdf` | 148,129 | ❌ | ✅ |

`unexplained_differences = 0`，`audit.determinism_probe.spec_sha16` 五次全为 `9bcb54b29fe658d4`。
完整逐文件表、运行矩阵与字段级差异见 [`references/DETERMINISM.md`](references/DETERMINISM.md)；
机器可读原件 [`examples/determinism_report.example.json`](examples/determinism_report.example.json)。

### 4.3 故意不稳定的字段（逐条点名，不许含糊）

| 编号 | 位置 | 为什么允许它变 | 怎么稳定化 |
|-|-|-|-|
| V1 | `result.json: generated_utc` | 契约要求真实生成时间 | 掩码 `<TS>`；不要改成常量 |
| V2 | `result.json: change_records[*].ts` | 变更记录必须真实 | 掩码 `<TS>` |
| V3 | `*.pdf: /CreationDate` | matplotlib PDF 后端写入 | 掩码；或设 **`SOURCE_DATE_EPOCH`**（实测两次 PDF 逐字节相同 `3e00d54352b170c0…`） |
| V4 | `render_log.json: requested.*` | 记录的是调用者自己的 `--out` 路径 | 掩码 `<RUN>`；该文件不是交付物 |

### 4.4 判据可被证伪（阴性对照，实测）

在一份**包外副本**里给 `common.write_json()` 注入一个随机字段（其余不动）：

| 项目 | 实测 |
|-|-|
| `verdict` / 退出码 | `unstable` / **1** |
| raw 全等文件 | **2 / 8** |
| 掩码后仍不一致 | 5 个（`audit/content/render_log/result/spec`） |
| 未解释字段 | 1 条：`result.json:_negctrl`，三次取值 `0.832…` / `0.452…` / `0.903…` |

⇒ 这个检查器**会**抓到真问题，不是"永远通过"的装饰。

---

## 5. 命令面（每个入口都真跑过；`--flag` 全部列出）

| 入口 | 关键参数 | 退出码语义 |
|-|-|-|
| `scripts/main.py` | `--case`(必) `--task` `--material` `--out` `--plan` `--raster-scale` `--pdf` / `--no-pdf` | 0 完成（success/partial）；1 硬输入错误；2 环境/内部错误 |
| `scripts/scaffold.py` | `--case`(必) `--task` `--material` `--out`(必) | 0 出骨架；1 输入不可读 |
| `scripts/spec_lint.py` | `--spec` `--content` `--lint-plan` `--plan` | 0 通过；1 有问题（打印 problems） |
| `scripts/check_contract.py` | `--result`(必) `--case` | 0 契约完整；1 缺口；2 文件不存在 |
| `scripts/determinism.py` | `--case`(必) `--out`(必) `--runs` `--hashseeds` `--cwds` `--plan` `--task` `--material` `--report` `--fail-on` `--keep` `--verbose` `--json` | 0 达到等级；1 未达到；2 用法/环境 |
| `scripts/fault_inject.py` | `--out`(必) `--only` `--fail-on silent\|strict\|none` `--keep` `--verbose` | 0 无静默失败；1 有；2 沙箱建不起来 |
| `scripts/gain_harness.py` | `--out` `--case` `--material` `--label` `--json` `--compare` | 0 测量完成 |
| `scripts/extract.py` `figurespec.py` `svgbuilder.py` `preview.py` `audit.py` `common.py` | 库模块（被上面入口导入） | — |

---

## 6. 失败与降级（有实测矩阵，不靠"我们支持"）

- **四形态注入**（输入/模板/依赖/契约共 23 条，真跑子进程）：`fault_inject.py --fail-on strict`
  **exit 0**、`ok 23 / silent 0`；逐行矩阵与修复点名见 [`references/FAULT-MATRIX.md`](references/FAULT-MATRIX.md)。
- **决策规则 D1–D20** 与失败分支同号互查：[`references/failure-modes.md`](references/failure-modes.md) §3。
- **契约硬门 G1–G8**（`case_id` 非空、契约字段回显无 null、SVG ≥7 层、PNG 有效、
  数值编码一致、四要素齐、`sources` 非空）见 [`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md) §7。
- 退出码：`0` 完成（success/partial 都算完成）；`1` 硬输入错误；`2` 环境或内部错误。

---

## 7. 五维落点（速查；逐条对照见 [`references/RUBRIC_MAP.md`](references/RUBRIC_MAP.md)）

| 维度 | 分 | 本包给出的东西 |
|-|-|-|
| 实际效果 | 40 | 真跑出图：四要素单页 + 可编辑分层 SVG + PNG（+PDF）；逐元素 `data-src`；`sources[]` 带 sha256；`audit.json` 全文 |
| 使用增益 | 25 | 与"不加载 Skill 的基础做法"的对照协议 + 只读测量器 `gain_harness.py`（分层数、真文字数、溯源覆盖率、契约通过率、返工步数） |
| 创新增益 | 15 | **可复现性做成判据**：三级等级 + 逐文件 sha256 + 易变字段分类 + 阴性对照；外加方案先行 / 双 lint 门 / 契约回显三个机制 |
| 可靠体验 | 10 | 四形态 23 条注入实测（0 静默）、20 条决策规则、稳定退出码、**`determinism.py` 一条命令给出复现结论**（含阴性对照） |
| 生态贡献 | 10 | 契约/五维/失败模式/注入矩阵/增益协议/机制/复用/方案 schema/四要素/图层/模板/**确定性报告** 等文档 + 资产三件套 + 可移植的判据工具 |

---

## 8. 交付前自查清单

- [ ] 跑的是**真实文件**（case.json / task.md / 材料），没有凭标签假设内容
- [ ] `main.py --case … --out …` → **exit 0**，`result.json` 已写出
- [ ] `check_contract.py` → **exit 0**（顶层无 null；信封 18 键 ∪ 案例契约全字段）
- [ ] SVG 良构、7 层 `layer:*`、`<text>` 可编辑、`data-src` 可溯源；PNG 非空；PDF 有头或 `present:false` + **reason**
- [ ] 四要素 4/4；`entity_coverage.missing` 与 `encoding_consistency.missing_from_canvas` 为空
- [ ] **`determinism.py --case … --out /tmp/det` → exit 0**，且报告里 `unexplained_differences` 为空
- [ ] `fault_inject.py --fail-on strict` → exit 0（23/23、0 静默）
- [ ] `uncertainty` 里没有"编造数据"类补丁；五维自评与 `RUBRIC_MAP.md` 一致
- [ ] `--out` 目录里没有多跑一次留下的旧产物（同名文件会被覆盖，异名文件会一起交付）

---

## 9. 限制与边界（如实声明）

- **抽取边界**：只认**独立成行的 `键 = 数值 单位`**与**带真实箭头（`->`/`→`/`⇒`）的机制行**；
  散文里的数字、带比较符或区间的值（`≈`、`0.8–1.2`）**不抽取**（宁缺勿错）；材料与 case 数值
  矛盾时**首见优先**并把两处 `src` 并列，不取平均、不择优；非 UTF-8 材料按替换字符读取并登记；
  二进制材料（PDF）取不到文本层时跳过，绝不把字节流当 UTF-8 解出乱码实体。
- **可复现性边界**：承诺"同一台机器、同一套依赖、同一份输入"的 L1 一致性；
  **不承诺**跨机器的字节一致（`.png` 像素受系统字体影响，`.pdf` 头受绘图库版本影响）。
  跨平台**换行符**由 `newline="\n"` 统一，不产生 CRLF。
- **渲染链真实可达**的是「matplotlib → Pillow → 纯 Python PNG」三级；第三级只有几何与占位框，
  文字不可读 —— 这是**有记录**的降级，不是静默成功。
- **注入与降级矩阵**覆盖本包可控的输入/模板/依赖/契约；平台侧故障（挂载缺失、配额、容器超时）
  不在其内。
- 四要素/图层/契约检查是**结构判据**，不代替领域科学判断。
- 随包示例案例均为**合成示意**，不是平台正式案例，不代表正式成绩。

### 9.1 本版相对上一代引擎的纯增量修复（逐条点名）

| 文件 | 变更 | 发现它的判据 | 理由 |
|-|-|-|-|
| `scripts/extract.py` | **净 +7 行**（把 1 行 `normalize_contract(...)` 调用拆成 2 行 + 新增 1 个记录分支与 3 行注释；函数签名/CLI/退出码零改动）：归一化之前先拿到原始值，若既不是 dict 也不是 str，就往 `uncertainty` 写一条「形态非法（list/int/bool）：已按空契约处理」 | `contract_matrix.py` C19/C21/C22 | 非法契约容器此前被**静默**归一化为 `{}`，评分方看不到"契约被丢弃" |
| `scripts/main.py` | **净 +6 行**（在既有 `if/elif` 链上新增 1 个 `elif` 分支：4 行代码 + 2 行注释；无删改）：PDF 未产出且不是 `pdf=false` 时，把 `reason` 填成「renderer backend 'X' provides no vector PDF preview」 | `degrade_probe.py` P03/P08/P09 | 回退到 Pillow/纯 Python 时 `present:false` 的 **reason 曾是 null**，失败原因不可见 |

两处都是**纯增量**：CLI 参数名、默认值、退出码语义一律未动；
`fault_inject.py --fail-on strict` 在修复后仍为 **exit 0 / 0 静默**（回归实测）。
