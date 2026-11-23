# FAULT-MATRIX.md — 四形态失败注入的**实测**矩阵（v4 轴）

> 本文件不是"声称的失败矩阵"，而是**跑出来的**：`scripts/fault_inject.py` 把
> 输入 / 模板 / 依赖 / 契约四类缺陷**逐个真的制造出来**，每次都调用真实主流程
> （`scripts/main.py` 子进程），抓回 `退出码 / status / uncertainty / 相关字段`，
> 与"期望行为"逐条对照，并额外判定**是否静默失败**（进程报 success 而缺陷既没被
> 修掉也没被记录）。
>
> - 生成命令（cwd 任意；产物写到包外）：
>   `python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/fi --fail-on none`
> - 判级：`--fail-on silent`（默认，静默失败即判 1）/ `strict`（任何 mismatch 判 1）/ `none`（只出表）
> - 原始报告：`/tmp/fi/fault_report.json`（含每条用例的 argv、stdout/stderr 摘要、耗时）
> - **只读本包**：每次演练都把 `<skill>/scripts` 复制到包外沙箱再跑，包内不产生
>   `__pycache__`、不写任何文件。

## 0. 一页结论

| 项目 | 修复前（R1 同源脚本） | 修复后（本包脚本） |
|-|-|-|
| 用例数 | 23 | 23 |
| `ok`（完全符合期望） | 10 | **23** |
| `silent-failure`（报成功但缺陷无记录） | **8** | **0** |
| `mismatch`（结论/退出码不符，但未静默） | 5 | **0** |
| 退化运行仍报 `status=success` 的用例 | F04 F05 F07 F09 F11 F13 F16 F18 | 无 |
| 总耗时（含 23 次真实出图） | 27.85 s | 30.65 s |

**静默失败明细（修复前）**：材料路径缺失（F04）、二进制材料（F05）、方案文件缺失（F07）、
未定稿方案骨架（F09）、方案关系缺 src（F11）、matplotlib 缺失（F13）、pypdf 缺失 + PDF 材料（F16）、
契约字段声明为 null（F18）—— 八条全部**报 `status=success` 且 `uncertainty` 里没有对应条目**。

**非静默但结论不符（修复前）**：方案文件非法 JSON 抛未捕获栈（F08）、方案覆盖未留痕（F12）、
两级渲染后端都缺时整次运行 `status=failed`（F14/F15 —— 第三级回退是死代码）、
输出目录不可用时 exit 1 + traceback（F17）。

**另有 5 处缺陷是"题集实测"查出来的**（不在这 23 条注入里，见 §2 的 G1–G5）：材料中的合法
数值（`25.4 mA/cm2`、`3.1e11 cm-2`）被判为「数值缺失」、材料行被整批误判成"关系"、
材料与 case.json 的数值矛盾被静默丢弃、纯数字（`0.14`）被截断成 `0.1`。

## 1. 实测矩阵（逐行；数字全部来自 `fault_report.json`）

| # | 类 | 注入什么（真实动作） | 期望行为 | 修复前 exit / status | 修复前判定 | 修复后 exit / status | 修复后 uncertainty 首条 | 是否静默失败 |
|-|-|-|-|-|-|-|-|-|
| F00 | 输入 | （无）原样跑一遍主流程 | 对照基线：夹具本身必须是干净 success，否则其它用例的 partial 就分不清是注入造成的还是夹具造成的 | 0 / success | ok | 0 / success | — | 否 |
| F01 | 输入 | argv --case 指向不存在文件（不创建任何输入） | D1：读不到输入必须立即失败，不得凭文件名猜内容 | 1 / None | ok | 1 / None | — | 否 |
| F02 | 输入 | case.json 内容截断为 `{"case_id": "broken",`（未闭合） | D1：解析失败必须失败，不得半成品冒充成功 | 1 / None | ok | 1 / None | — | 否 |
| F03 | 输入 | case.json = {}（无 case_id / 无 entities） | D2：缺 case_id 走回退链（文件名），不得崩；实体为空要如实计数 | 0 / partial | ok | 0 / partial | — | 否 |
| F04 | 输入 | case.json.source_material 指向 missing_material.md（不创建该文件） | D4：用其余材料继续，但必须在 uncertainty 里点名缺失路径 | 0 / success | **silent** | 0 / partial | case.json 声明的材料路径不存在：missing_material.md（已用其余可用材料继续，未虚构内容） | **是（已修）** |
| F05 | 输入 | source_material 指向 content.pdf（真实 %PDF 头 + 二进制字节） | D9：二进制材料不得被当 UTF-8 解码成乱码实体 | 0 / success | **silent** | 0 / success | 以下材料是二进制文件（未按文本解析）：content.pdf；已改用 PDF 文本层：content.pdf | **是（已修）** |
| F06 | 输入 | case.json.entities = "DOX, micelle"（字符串） | 契约 D17：类型不符以真实值为准并继续，不得崩 | 0 / success | ok | 0 / success | — | 否 |
| F07 | 模板 | --plan 指向不存在的 plan.json | D14：方案不可读 → plan.lint.valid=false，status 不得 success | 0 / success | **silent** | 0 / partial | plan lint problems: plan file not found: <work> | **是（已修）** |
| F08 | 模板 | plan.json 内容为 `{"four_elements": {` | D14：方案不可解析必须干净失败（exit 1 + 机器可读错误），不得抛栈 | 1 / None | mismatch | 1 / None | — | 否（错误不干净/结论不符） |
| F09 | 模板 | plan.json 由 scaffold 原样生成、四个面板说明留空 | D14/CP1：骨架未定稿 → 方案门不过 → status 必须降到 partial | 0 / success | **silent** | 0 / partial | plan lint problems: plan.four_elements.question missing (一句话说明本面板表达什么); pla… | **是（已修）** |
| F10 | 模板 | plan.figure_constraints = {width: 8000, height: 8000} | D14：画布超出 clamp [600,4000] 必须被方案门拦下并记 partial | 0 / partial | ok | 0 / partial | spec_lint: canvas width=8000.0 outside clamp [600, 4000] | 否 |
| F11 | 模板 | plan.relations[0] = {from:『不存在的实体X』, to:…}（无 src） | D14：缺 src 的关系项必须被方案门报出，不得静默上画布 | 0 / success | **silent** | 0 / partial | plan lint problems: plan.relations item '无源关系' missing source provenance (src) | **是（已修）** |
| F12 | 模板 | plan 指定 pdf=false、raster_scale=1（案例原本 pdf=true、scale=2） | 方案先行：设计决策以 plan 为准，且必须留下 override 记录 | 0 / success | mismatch | 0 / success | — | 否（错误不干净/结论不符） |
| F13 | 依赖 | PYTHONPATH 前置 matplotlib.py（模块体 raise ImportError） | D9/D11：回退到 Pillow 并记 partial；不得报 success | 0 / success | **silent** | 0 / partial | matplotlib 渲染不可用，已回退到备用渲染器：ImportError: injected: matplotlib unavailable | **是（已修）** |
| F14 | 依赖 | PYTHONPATH 前置 PIL.py（模块体 raise ImportError） | 本演练查出真实耦合：matplotlib 自身 import PIL，屏蔽 Pillow 会连带 matplotlib 失效 ⇒ 只能走第三级纯 Python PNG | 2 / failed | mismatch | 0 / partial | matplotlib 渲染不可用，已回退到备用渲染器：ImportError: injected: Pillow unavailable | 否（错误不干净/结论不符） |
| F15 | 依赖 | 同时前置 matplotlib.py 与 PIL.py（均 raise ImportError） | D11：最后一级纯 Python PNG 仍要出图，并把降级写进 uncertainty | 2 / failed | mismatch | 0 / partial | matplotlib 渲染不可用，已回退到备用渲染器：ImportError: injected: matplotlib unavailable | 否（错误不干净/结论不符） |
| F16 | 依赖 | PYTHONPATH 前置 pypdf.py（raise ImportError），材料为真实 PDF 字节 | 可选依赖缺失必须优雅降级：不取 PDF 文本层，也不得产出乱码实体 | 0 / success | **silent** | 0 / partial | 以下材料是二进制文件（未按文本解析）：content.pdf；未取得可用文本层，相关数值一律不上画布 | **是（已修）** |
| F17 | 依赖 | --out 指向已存在的普通文件（os.makedirs 必然失败） | 保存失败不得静默：要么干净非零退出，要么明确报错 | 1 / None | mismatch | 2 / None | — | 否（错误不干净/结论不符） |
| F18 | 契约 | output_contract.resolution_dpi = null | D15：禁 null —— 必须归一化为空值并记录，不得原样回显 null | 0 / success | **silent** | 0 / success | 案例 output_contract 声明为 null 的字段已归一化为空值：resolution_dpi | **是（已修）** |
| F19 | 契约 | output_contract.summary = "案例给的摘要"（与信封 summary 同名） | D16：冲突键的案例值移入 output_contract_echo，顶层保留信封值 | 0 / success | ok | 0 / success | — | 否 |
| F20 | 契约 | output_contract.resolution_dpi = "300"（字符串） | D17：以真实值为准写入，类型偏差要能被复核方看到 | 0 / success | ok | 0 / success | — | 否 |
| F21 | 契约 | 删除 case.json.output_contract 键 | 无案例契约时信封 18 键仍须齐全 | 0 / success | ok | 0 / success | — | 否 |
| F22 | 契约 | output_contract.layer_names = []（空列表） | ②容器形态：空列表是合法值，不得被 null/"" 替换 | 0 / success | ok | 0 / success | — | 否 |

> 读法：`期望行为` 是对该条注入**唯一的合格判定**；`修复前判定` 的 `**silent**`
> 表示"进程 exit 0 且 status=success，而注入的缺陷没有任何字段记录它"；
> `修复后 uncertainty 首条` 是 `result.json["uncertainty"][0]` 的原文（截断到 72 字），
> 可直接在报告里核对。

## 2. 演练查出的真实缺陷与修复（纯增量，逐条点名）

八条静默失败 + 三条不干净失败都定位到了具体代码位置。修复一律采取**纯增量**：
只新增行、不改既有行、不删任何行；CLI 参数名/默认值/退出码语义保持不变。

| # | 文件 | 增/删行 | 触发用例 | 缺陷（实测证据） | 修复 |
|-|-|-|-|-|-|
| F1 | `scripts/extract.py` | **+100 / -0**（含 F1–F3、G1–G3、G5） | F04 F05 F16 | `extract.run()` 对"声明了但不存在"的材料路径直接 `continue`，不记录；非 UTF-8 与二进制材料被当文本读，**既不跳过也不记录**（`status=success`, `uncertainty=[]`） | 新增材料预检：记录缺失路径、非 UTF-8 文件、二进制文件（NUL 或 `%PDF-` 魔数），并把记录写进新增的 `uncertainty` 键（`main.py` 早已读取该键，只是从来没人填过） |
| F2 | `scripts/extract.py` | （含在 F1 内） | F05 F16 | 二进制材料（平台可能按运行契约挂载 PDF）会被 `read_text(errors="replace")` 变成乱码文本 | 新增 `_binary_material_text()`：可选依赖 `pypdf` 存在时抽取 PDF 文本层并标注 `material(pdf-text)`；不存在或抽不出文本层时**跳过并在 `uncertainty` 写明"未取得可用文本层，数值不上画布"** |
| F3 | `scripts/extract.py` | （含在 F1 内） | F04 F16 | 一条材料都没读到时不产生任何 note，`status` 仍可为 success | 材料为空/不可用时写入 `notes`（→ `warnings`，并使 `status` 降为 `partial`） |
| F4 | `scripts/main.py` | **+41 / -0**（含 F5–F9） | F08 | `--plan` 指向非法 JSON → `json.load` 未捕获 → **Python traceback**，无机器可读错误 | 读取前先探针解析：失败则 `exit 1` + `{"status":"failed","error":"plan.json unreadable: …"}` |
| F5 | `scripts/main.py` | （含 F4 行数） | F07 F09 F11 | `plan.lint.valid=false` 只进 `uncertainty`，**`status` 仍是 success**（与 D14 明文相矛盾） | `status` 降级条件补上 plan lint：任一 lint 不过即 `partial` |
| F6 | `scripts/main.py` | （含 F4 行数） | F18 | 案例把契约字段声明为 `null` 时被**原样回显成 null**，直接违反"D15 禁 null" | 对 `null` 声明做归一化（写空值）并记进 `uncertainty` |
| F7 | `scripts/main.py` | （含 F4 行数） | F13 F14 F15 | 渲染后端降级（matplotlib → Pillow → 纯 Python）已写进 `render_log.json`，但 `status` 仍报 success（契约 §4 要求 partial） | `_status()` 计入 `matplotlib_failed` / `pil_failed` |
| F8 | `scripts/main.py` | （含 F4 行数） | F17 | `--out` 指向一个普通文件时 `os.makedirs` 抛 `FileExistsError` traceback（exit 1、无 JSON） | 包一层 `try`：`exit 2` + `{"error":"output directory not usable: …"}` |
| F9 | `scripts/main.py` | （含 F4 行数） | F12 | `change_notes`（方案覆盖 constraints 的记录）被收集后**从未写进 `change_records`** | 循环追加进 `change_records`，方案先行决策可被复核 |
| P1 | `scripts/preview.py` | **+7 / -0** | F14 F15 | **最后一级"纯 Python PNG"渲染器是死代码**：像素缓冲里部分单元格是 `(r,g,b)` 元组，序列化时却调用 `hexc()` 解析字符串 → `AttributeError: 'tuple' object has no attribute 'lstrip'`；实测两者都缺时 `exit 2 / status=failed`，第三级回退从来没成功过 | 序列化前把元组单元格归一化为十六进制字符串（新增 7 行，不动原逻辑；几何与像素不变） |
| G1 | `scripts/extract.py` | （含在 F1 内） | **v5 案例 A**（`calab-perovskite-001`） | `_parse_value` 的单位字符类不含数字与 `-` `/`，于是材料里**确实存在**的 `25.4 mA/cm2`、`3.1e11 cm-2` 被判为「数值缺失」并**被排除出画布**（`missing_values` 列出两条并不缺的值） | 增加一次更宽松的二次解析（数字 + 自由单位），`0.14` 这类纯数字仍走原路径，不误切 |
| G2 | `scripts/extract.py` | （含在 F1 内） | **v5 案例 B**（`urban-heat-001`） | 材料里同一指标给了两个不同数值（0.14 / 0.19）时，第二个被**静默丢弃**、`uncertainty` 里没有任何记录（与 D7 明文"双来源并列"不符） | 保留首见值，但把冲突连同两处 `src` 写进 `uncertainty` |
| G3 | `scripts/extract.py` | （含在 F1 内） | **v5 案例 A/B** | `parse_fact_lines` 的单位字符类同样过窄，`cm-2` 这类材料行永远进不了事实流 | 在严格分支之后追加一次宽松二次解析（单位长度受限，仍拒绝带括号的散文行） |
| G4 | `scripts/figurespec.py` | **+6 / -0** | **v5 案例 A** | `_simple_datum` 用原始 float 渲染说明文字（`310000000000.0`），而 `audit.encoding_consistency` 按 `:g` 查找（`3.1e+11`）→ **G6 硬门报"数值未上画布"，但 `status` 仍是 success** | 说明文字改用与其它通道一致的 `:g` 形式 |
| G5 | `scripts/extract.py` | （含在 F1 内） | **v5 案例 A/B** | `RE_ARROW` 的分隔符组写成 `⇒?`（可选），于是**几乎任何一行**都能匹配成"关系"；关系分支先命中并 `continue`，导致①产生垃圾关系（`("-", "载药量 = 14.2 %")`）②**材料里的数值永远进不了数据通道**（案例 A 的 `relations` 计数被灌到 25，实际声明只有 5 条） | 要求行内必须出现真实箭头记号；同时剥掉行首的项目符号，使清理后的 key 与 case 声明的 id 一致（案例 A 灌水关系降到 9 条、案例 B 的数字冲突因此可被 G2 检出） |

> 逐条复核命令：`python -m py_compile scripts/*.py`；`python scripts/fault_inject.py --only F15`。
> 行数复核：`git diff --numstat` 或
> `diff <基线包>/scripts/main.py scripts/main.py | grep -c '^>'` / `grep -c '^<'`。

## 3. 演练顺带查出的**环境耦合**（不是缺陷，但改变结论）

- **F14：matplotlib 自身 `import PIL`**。把 Pillow 从 `PYTHONPATH` 屏蔽掉，matplotlib
  会连带导入失败 —— 也就是说渲染链的"第 2 级 Pillow"在安装了 matplotlib 的环境里
  **不是独立可达的**，屏蔽 Pillow 实际等于同时失去前两级。修复 P1 之后，这种情形会
  正确落到第 3 级纯 Python PNG，`status=partial` 并记录 `matplotlib_failed` 原文。
- **F17：输出目录语义**。`--out` 是一个已存在的普通文件时，原先视为"内部错误 + traceback"，
  现在统一为 `exit 2` + 机器可读 JSON（与 `failure-modes.md` §1 的退出码表一致）。

## 4. 复现与自证（全部命令在**包外**执行）

```bash
# ① 四形态全量演练（23 条；约 22 秒）
python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/fi --fail-on none

# ② 只跑某一类 / 某一条（排查用）
python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/fi2 --only dependency
python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/fi3 --only F15 --verbose

# ③ 严格模式：任何不符合期望的用例都让脚本非零退出（适合接进 CI）
python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/fi4 --fail-on strict

# ④ 与"未修复的同源脚本"对比（把基线包脚本复制到临时目录再指过去）
#    cd /tmp && cp -r "$SKILL_DIR" base && cp "$SKILL_DIR/scripts/fault_inject.py" base/scripts/
#    python base/scripts/fault_inject.py --out /tmp/fi-base --fail-on none
```

## 5. 未覆盖 / 未验证（如实声明）

- **不注入真实网络/平台级故障**（平台挂载缺失、配额超限、评测容器超时）：本演练只覆盖
  本包可控的输入/模板/依赖/契约四类，平台侧故障不在本包职责内。
- **不注入"材料内容错误"的真伪判断**（数值与结论相矛盾、单位错、口径不同）：D7 保证的是
  "**首见优先 + 冲突必须留痕（G2 修复）**"，即把两处数值与各自 `src` 并列写进 `uncertainty`；
  哪个才是对的仍必须由人判断。判据：`uncertainty` 出现
  `材料与 case.json 数值不一致（首见优先，未取平均）：…`（v5 案例 B 实测）。
- **F10（画布超界）修复前后都判 `ok`**：它走的是 spec_lint（绘制前规格门）而不是 plan lint，
  两个版本都会把 `status` 降为 `partial`；保留该行是为了证明规格门的判据在注入下仍然成立。
- **依赖注入用 `PYTHONPATH` 假模块**，与"真的卸载该库"在 `sys.modules` 层面等价，
  但不覆盖"库存在却 ABI 损坏"这类情形。
- 演练耗时与失败用例数会随平台/机器变化（本表为 2026-11-22 本机 python 3.13 实测），
  **结论性列（判定 / 静默与否）不随机器变化**。
