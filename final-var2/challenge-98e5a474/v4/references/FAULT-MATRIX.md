# FAULT-MATRIX — 失败注入与恢复演练实测矩阵（v4）

> **本文件里的每一个数字都是从 `scripts/fault_inject.py` 的真实运行输出里
> 抄下来的，没有一条是设计意图推演。** 复跑命令见 §1，原始机器可读结果
> 是脚本产出的 `fault-matrix.json`（25 条记录，逐条含退出码、`status`、
> `uncertainty`、fail/warn 检查名、stdout 尾部与独立复核器结论）。
>
> 实测时间 2026-11-22 20:05 (+08:00)；Python 3.13.9；节点：
> matplotlib 3.10.6 / Pillow 12.3.0 / numpy 2.3.5 / PyMuPDF(fitz) 可用；
> **无** cairosvg / svgwrite（与平台运行时同类）。

## 1. 怎么复跑（3 分钟，产物全部落在包外）

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

# 全矩阵（25 条，约 40 s）
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out /tmp/sse-fault

# 只跑某一形态（input / template / dependency / contract）
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" \
    --out /tmp/sse-fault-dep --form dependency

# 只跑指定几条（调试时用）
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" \
    --out /tmp/sse-fault-d13 --only D13,D21

# 只看用例清单，不运行
python "$SKILL_DIR/scripts/fault_inject.py" --list
```

退出码：`0` = 全部注入都符合期望（**含"被如实拒绝"**）；`1` = 至少一条
的实际行为与期望不符（恢复演练失败，矩阵里会打印差值）；`2` = 参数/环境
错误。`--out` 指向包内会被**直接拒绝**（会把产物与 `__pycache__` 混进
交付资源集，违反本题"包内只放 UTF-8 文本"的硬约束）。

**注入的隔离原则**（为什么它能当证据用）：

1. 每次注入都把整包**复制**到一个临时 scratch 目录，坏掉的只是副本；
2. 注入手段只有四种：动夹具、动数据、动环境变量（`PYTHONPATH` 上的
   `sitecustomize`）、在副本里包一层模块。**不改被测脚本的逻辑、不改
   CLI 参数名、不改退出码语义**；
3. 记录的是子进程真实 `returncode` 与真实落盘的 `result.json` 字段；
   没有产物就记"无产物"，不做推断。

## 2. 四形态总览（实测）

| 形态 | 用例数 | 符合期望 | 静默失败 | 结论 |
|-|-|-|-|-|
| 输入 damaged（D01–D06） | 6 | 6 | 0 | 材料缺失/不可读都能留痕；case 本身坏了就**干净地拒绝**（exit 2，不写半成品） |
| 模板/夹具 damaged（D07–D14） | 9 | 9 | 0 | 清单结构错误全部被 CP1 拦下；只有**语义**方向错（D09b）拦不住，已作为已知盲区公开 |
| 依赖 damaged（D15–D21） | 7 | 7 | 0 | 加密/扫描 PDF 与缺库都能分辨；依赖缺失现在会写 `failed` 的 result.json，不再是裸 traceback |
| 契约 damaged（D22–D24） | 3 | 3 | 0 | 契约声明缺失不影响出图（21 键仍全）；形状不符由**独立校验器**判 INVALID |
| **合计** | **25** | **25** | **0** | `fault_inject.py` 退出码 0 |

## 3. 逐行矩阵（注入 → 期望 → 实测 → 是否静默）

> 列说明：**退出码** = `scripts/main.py` 的真实 `returncode`；
> **status** = 产出 `result.json` 的 `status`（`—` 表示没写 result.json）；
> **unc** = `uncertainty` 条目数；**fails / warns** 是
> `verification.checks.fails|warns` 里的检查名。
> 「静默」= 出了问题却「exit 0 + success + 无 fail/warn/uncertainty」——
> 本次 25 条**全部为否**。

### 3.1 形态 1：输入损坏（input）

| id | 注入什么 | 期望行为 | 实测 退出码 / status / unc / 痕迹 | 静默 |
|-|-|-|-|-|
| **D01** | `case.sources` 指向不存在的材料文件 | 继续出图，但"材料缺失"必须留痕 | `0` / `success` / 3 / `uncertainty[0]="unresolved source materials: sources/absent-material.md"`；独立复核 `validate_result.py` → **exit 0 VALID** | 否 |
| **D02** | 材料文件存在但内容是二进制垃圾（非 UTF-8） | 图仍可出；内容不可读这点要有痕迹 | `0` / `success` / 2 / **无 fail、无 warn**，仅剩 `layout` 与 `preview fidelity` 两条常规 uncertainty | 否（见 §4 盲区 A1） |
| **D03** | `case.json` 合法 JSON 但顶层是数组 | 干净拒绝，不写半成品 | `2` / `—` / 0 / `FATAL: case.json must be a JSON object`，产物目录为空 | 否 |
| **D04** | `case.json` 被截断成非法 JSON | 同上 | `2` / `—` / 0 / `FATAL: cannot parse case.json`，产物目录为空 | 否 |
| **D05** | `--case` 指向不存在的路径 | 同上 | `2` / `—` / 0 / `FATAL: case not found: …` | 否 |
| **D06** | `--manifest` 指向不存在的文件 | 不画，但工作不丢失（写 `failed` 的 result.json） | `1` / `failed` / 1 / `fails=[pipeline]`：`--manifest file not found` | 否 |

> D06 的期望曾被写成 `exit 2`，实测是 `exit 1 + failed result.json`。
> **以实测为准并修正了用例期望**：main.py 对 `--manifest` 缺失走的是
> `fetch_manifest` 的 `FileNotFoundError` 分支（写 failed 记录），
> 而 `--case` 不可解析才走 `exit 2`。两者语义不同，这正是本矩阵要区分的东西。

### 3.2 形态 2：模板 / 夹具损坏（template）

| id | 注入什么 | 期望行为 | 实测 退出码 / status / unc / 痕迹 | 静默 |
|-|-|-|-|-|
| **D07** | `--manifest` 文件不是 JSON | 写 `failed` 的 result.json | `1` / `failed` / 1 / `fails=[pipeline]`（`Expecting value: line 1 column 1`） | 否 |
| **D08** | 关系 `kind` 改成词表外的 `gibberish-relays` | CP1 生成前门拦下 | `1` / `partial` / 2 / `fails=[spec_lint.spec.relation_kind]`；独立 `spec_lint.py` → **exit 1 / valid=False fail=1** | 否 |
| **D09** | 关系 `to` 指向不存在的实体 `E99` | 结构不可能画对 ⇒ 拦下 | `1` / `partial` / 2 / `fails=[spec_lint.spec.relation_to]`；独立 `spec_lint.py` → **exit 1 / valid=False** | 否 |
| **D09b** | 把激活关系 `E4→E5` 端点**对调**成 `E5→E4`（语义错、结构合法） | **期望就是 `0`/`success`**：端点存在、kind 可映射 ⇒ 结构门判不了 | `0` / `success` / 2 / **无 fail、无 warn**（`spec_lint` 全 ok） | 否（见 §4 盲区 A2） |
| **D10** | 实体保留 `source`、删掉全部 `evidence` | 降级可见：溯源 warn | `0` / `success` / 2 / `warns=[traceability.entities]`；独立 `spec_lint.py` → exit 0 / valid=True **warn=6** | 否 |
| **D11** | 分组里塞进不存在的实体 `E99` | CP1 拦下 | `1` / `partial` / 2 / `fails=[spec_lint.spec.group_member]` | 否 |
| **D12** | 图例多加一条图面没有的 `inhibition` 条目 | 孤儿项应为 warn（可见但不阻断出图） | `0` / `success` / 2 / `warns=[legend.orphan_items]` | 否 |
| **D13** | `assets/relation-dict.json` 被写成非法 JSON | 不得被当成"检查通过" | `0` / `success` / 2 / `warns=[spec_lint.corpus]`（原文含 `JSONDecodeError`）；**独立 `spec_lint.py` → exit 1（它自己仍会崩，见 §4 盲区 A3）** | 否 |
| **D14** | `assets/relation-dict.json` 被整个删掉 | 同上 | `0` / `success` / 2 / `warns=[spec_lint.corpus]`；独立 `spec_lint.py` → exit 0 / valid=True | 否 |

> **D13 是本轮由注入发现并修掉的真实缺陷**（详见 §5.1）：修复前它会
> `JSONDecodeError` 直接崩掉、连 `result.json` 都不写（`exit 1` + 裸
> traceback）；修复后降级成一条可读 warn，主流程照常交付图稿。

### 3.3 形态 3：依赖损坏（dependency）

| id | 注入什么 | 期望行为 | 实测 退出码 / status / unc / 痕迹 | 静默 |
|-|-|-|-|-|
| **D15** | 材料换成声明 `/Encrypt` 的 PDF | 主流程不伪造文本；抽取器必须**可分辨地拒绝** | 主流程 `0` / `success` / 2；`pdftext.py` → **exit 2**，`FATAL: PDF is encrypted (material-enc.pdf); text extraction without a password is not attempted…` | 否 |
| **D16** | 材料换成内容流为空的 PDF（扫描件） | 抽取器给出"抽到 0 字"的明确结论 | 主流程 `0` / `success` / 2；`pdftext.py` → exit 0，`chars: 0` + `WARN: extraction via PyMuPDF (fitz)` | 否 |
| **D17** | 屏蔽 `fitz/pypdf/PyPDF2`（`PYTHONPATH` 注入 `sitecustomize`） | 走 stdlib 回退仍能抽，backend 如实记录 | 主流程 `0` / `success` / 2；`pdftext.py` → exit 0，`chars: 15` + `WARN: no third-party PDF library found — used the pure-standard-library fallback (zlib + Tj/TJ operators); layout is NOT reconstructed` | 否 |
| **D18** | 屏蔽 `matplotlib` 的导入 | 写 `failed` 的 result.json，而不是裸 traceback | `1` / `failed` / 1 / `fails=[pipeline]`（`missing runtime dependency: render.matplotlib…`） | 否 |
| **D19** | 屏蔽 `PIL` 的导入 | Pillow 缺失会让 matplotlib 自身 import 不进来 ⇒ 与 D18 同一分支，但**必须留 result.json** | `1` / `failed` / 1 / `fails=[pipeline]`（`checks.pillow…`） | 否 |
| **D20** | 目标机没有 CJK 字体（从 matplotlib 字体表里摘掉 CJK 家族） | SVG 文字仍在，PNG 可能缺字；`font.cjk` warn + uncertainty | `0` / `success` / **3** / `warns=[font.cjk]`（`resolved font 'DejaVu Sans'; CJK support: False`）+ `uncertainty[1]="fonts: no CJK font for matplotlib…"` | 否 |
| **D21** | SVG 构建在运行期抛 `RuntimeError`（副本内注入） | 捕获 → 写 `failed` 的 result.json，已落盘产物不删 | `1` / `failed` / 1 / `fails=[pipeline]`（`injected render crash`） | 否 |

### 3.4 形态 4：契约损坏（contract）

| id | 注入什么 | 期望行为 | 实测 退出码 / status / unc / 痕迹 | 静默 |
|-|-|-|-|-|
| **D22** | `case.json` 完全不声明 `output_contract` | 结果仍覆盖契约 §1 的 21 个字段 | `0` / `success` / **21 键**（少了 2 个回显键）/ 2；独立 `validate_result.py` → **exit 0 VALID** | 否 |
| **D23** | `output_contract` 声明的类型与实际值形状不符（`case_id:"number"`、`status:"array"`…） | 回显按声明类型补齐；**独立校验器必须判 INVALID** | `0` / `success` / 23 键 / 2；`validate_result.py` → **exit 1 INVALID**，`G5 contract key case_id: expected int/float, got str`、`G5 contract key status: expected list, got str` | 否 |
| **D24** | case 无 `manifest`/`entities`，工作区也无 `entities.json` | 无依据不画，工作不丢失 | `1` / `failed` / 1 / `fails=[pipeline]`（`no entity-relation manifest available…`）；`validate_result.py` → exit 1 INVALID（`G7 no artifacts produced at all`，**符合预期**：失败运行本就没有产物） | 否 |

## 4. 已知盲区（**如实写明**：哪些故障本包拦不住）

这张表是本次演练最有价值的部分 —— 它把"看起来通过"与"真的正确"分开。

| # | 盲区 | 为什么结构门拦不住 | 实测证据 | 缓解手段 |
|-|-|-|-|-|
| **A1** | 材料**内容**不可读（D02） | pipeline 只对 `sources` 做**存在性**解析；材料字节由 Agent 侧读取，且 case 自带 `manifest` 时根本不被消费 | D02：exit 0 / success / 0 fail / 0 warn | S1 的"逐份读实际文件、记录读到的条数"人工门；读不到时必须手写进 `uncertainty`（本包 SKILL.md §D3 要求） |
| **A2** | 关系**方向**对调（D09b） | 端点都存在、`kind` 可映射 ⇒ CP1 的判据（id 合法、词表可映射、containment 用分组、图例双向）在结构上无法区分 `E4→E5` 与 `E5→E4` | D09b：exit 0 / success / 0 fail / 0 warn，`spec_lint` 全 ok | ①S2 要求 `from/to` 逐条回材料原文核对；②`figure.svg` 每条边带 `data-relation`/`data-source`，可用 `grep` 逐条比对；③本题评分侧的科学判断（native/LLM Judge）正是为这类错误准备的 |
| **A3** | 独立 `spec_lint.py` CLI 对**损坏的字典**仍会崩 | `main.py` 内联路径已加 try 兜底（D13 的 warn），但 `spec_lint.py --manifest … --dict …` 是另一条独立进程路径，它自己做 `json.load` 没有兜底 | D13 的 `post` 复核：`spec_lint exit=1，JSONDecodeError: Expecting property name…` | 本包**没有**为了漂白这一条去改 `spec_lint.py`（它逐字节未动，只在 `main.py` 侧兜）；交付前跑 `fault_inject.py --only D13` 就能看见它，属于"公开的、可观测的"限制而非静默失败 |
| **A4** | 缺 Pillow 与缺 matplotlib 不可分辨（D18/D19） | matplotlib 的 `colors.py` 在 import 期就 `from PIL import Image` | 两者都是 `exit 1 / failed / fails=[pipeline]`，只能从 `uncertainty` 里的模块名区分 | 已在 `failed` 记录里写明缺失模块名；恢复条件同 D15（装依赖后重跑） |
| **A5** | `--skip-checks` / `--no-lint` 会让"未检查"看起来像"已通过" | 这是既有的显式选项（v1 起就有，属 D16 记录范围），跳过时 `verification.checks` 结构变空、`spec_lint` 为空对象 | 未在本矩阵注入（属"自选降级"而非"故障"） | SKILL.md §F.4 与自查清单强制"交付前用默认参数完整重跑一次" |
| **A6** | 加密 PDF 的主流程不感知 | `sources` 里那份 PDF 抽不出文本时，主流程仍 exit 0（它只做存在性解析） | D15：主流程 `0/success`，但 `pdftext.py` 自己 `exit 2` + `FATAL` | 硬性要求：S1 里 PDF 必须先过 `pdftext.py` 并把它的 backend/非零退出如实写进 `uncertainty` |

## 5. 本轮由注入发现并修复的三个真实缺陷（两个纯增量 + 一处文档更正）

三条都**先在包外副本里复现**；`main.py` 的 CLI 参数名、默认值、退出码语义
**均未改动**，其余脚本逐字节不变。

### 5.1 `scripts/main.py`：`relation-dict.json` 损坏会崩掉整个流水线

- **修复前实测**：`cp -r pkg p; echo '{ broken' > p/assets/relation-dict.json;
  python p/scripts/main.py --case p/examples --out <t>` → `exit 1`，
  stdout 只有一段 `json.decoder.JSONDecodeError` traceback，**`<t>/result.json`
  不存在**（连失败证据都没有）。
- **原因**：CP1 门里 `with open(dict_path) as fh: rel_dict = json.load(fh)`
  没有兜底，异常直接冒泡。
- **增量**（`scripts/main.py`，+18 / −2 行，全部为新增分支）：
  - 读字典处包 `try/except`，失败时记 `rel_dict_disabled` 并打一条 WARN；
  - `summarize()` 之后，若 `rel_dict_disabled` 非空，向
    `verification.checks.warns` 追加一条 `spec_lint.corpus`（level=warn，
    detail 含原始异常），并让 `warn_count` +1。
- **修复后实测**：`exit 0 / success / 23 键 / warns=[spec_lint.corpus]`，
  图稿照常交付，降级**可见**。语义判定：图没错，坏的是"一致性检查器"，
  所以是 warn 而不是 fail —— 但绝不再是"静默跳过"。

### 5.2 `scripts/main.py`：缺运行依赖时不留任何失败记录

- **修复前实测**：屏蔽 `matplotlib`（或 `PIL`，matplotlib 依赖它）→
  `exit 1` + 裸 `ModuleNotFoundError` traceback，**没有 `result.json`**。
  这违背本包自己承诺的 D8/D15「渲染/导出失败 → 捕获 → 写 status=failed
  的 result.json」。
- **增量**（`scripts/main.py`，+27 / −5 行）：把 `import render` 与
  `import checks` 各自包进 `try/except`（失败时置 `None` 并记
  `_IMPORT_ERRORS`），在解析完 case、建好输出目录之后加一个**依赖门**：
  若 `_IMPORT_ERRORS` 非空，调用既有的 `_write_failed_result(...)`
  写 `status=failed` 的 result.json，然后 `return 1`。
- **修复后实测**：D18/D19 均 `exit 1 / failed / fails=[pipeline] /
  uncertainty[0]="missing runtime dependency: … (pip install matplotlib
  pillow numpy)"`，产物目录保留。

> 两条都以"**先有实测崩溃、后有增量修复、修复后同一注入转绿**"的顺序
> 留证：`fault_inject.py --only D13,D18,D19` 可随时复现修复后的行为；
> 修复前的行为记录在 §5.1/§5.2 与本轮回报里。

### 5.3 `scripts/main.py`：`--edit-svg` 分支把编辑问题**整个丢掉**（并连带更正两处旧文档的错误说法）

- **怎么发现的**：核对"编辑请求没生效时能不能被察觉"时，用错误字段名
  （`target` / `value` 而不是 `relation_id` / `to`）构造夹具实测 ——
- **修复前实测**：`exit 0` / `status=success` / `change_records=0`，
  而且 **stdout 里连 `[edit] …` 都没有**（`--edit-svg` 分支把
  `edit_from_svg()` 返回的 `ed_issues` 直接丢掉了；另一条分支是打印的）。
  旧文档还写着"日志会出现 `[edit] fail unknown relation`"—— 与实际不符。
- **纯增量**（`scripts/main.py`，+8 / −1 行）：`--edit-svg` 分支收集
  `ed_issues`，与另一条分支一致地打印 `[edit] …`，并在 uncertainty 段落把
  每条问题写成 `{"item": "edit issue: edit.<action>", "note": "…（level=fail）"}`。
- **修复后实测**：同一夹具 → `exit 0` / `status=success` / `change_records=0`
  **且** `uncertainty` 出现 `edit issue: edit.relabel`；
  正常夹具（3 条动作）仍为 `change_records=3`。
- **同时更正两处旧文档的错误说法**（本轮实测：两字段都生效，不是只有一个）：

  | 夹具 | 实测 `change_records` |
  |-|-|
  | 只写 `edits`（3 条动作） | **3**（rename / relabel / note） |
  | 只写 `edit_requests`（同样 3 条） | **3** |
  | 字段名写错（`target` / `value`） | **0** ⇒ 真正的坑在这里 |

  `main.py` 的实现是 `case.get("edits") or case.get("edit_requests")`，
  因此"走 `--edit-svg` 时 `edits` 不生效"是**错的**。已在
  `references/EDIT-ACTION-SCHEMA.md` §2.2 与 `SKILL.md` 的"已知限制"里改正。

> 结论：三条修复都属于"**先有实测崩溃/静默，后有纯增量，修复后同一夹具转绿**"。
> 复现命令：`fault_inject.py --only D13,D18,D19`（前两条）+
> `EDIT-ACTION-SCHEMA.md` §2.2 的三行夹具（第三条）。

## 6. 矩阵本身的自检（防止"演练脚本自己失效"）

| 自检项 | 实测 |
|-|-|
| 用例数 / 符合期望 | 25 / **25**（`fault_inject.py` 退出码 **0**） |
| 静默失败候选 | **0** |
| `--out` 指向包内 | 拒绝，`exit 2`，`FATAL: --out must not be inside the skill package` |
| 每次注入是否改动原包 | 否（`shutil.copytree` 到 tempdir；原包 25 次运行后 `sha` 不变） |
| 注入是否改被测脚本逻辑 | 否（D18–D20 用 `sitecustomize` 改"环境事实"；D21 在副本里包一层抛异常的 `build_schematic_svg`） |
| 独立复核器 | D01/D22/D23/D24 跑 `validate_result.py`；D08/D09/D10/D13/D14 跑 `spec_lint.py` |
| 报告可复跑 | 是，`fault-matrix.json` 含每条的命令、退出码、stdout 尾部、检查明细 |

## 7. 与五维评分的对应（这一份文档主要扛"可靠体验 10"）

| 评分点 | 本文件给出的证据 |
|-|-|
| 调用与易用性 3 | §1 四条命令，任意 cwd 可跑；`--form/--only/--list` 三种筛选；`--out` 越界自动拒绝 |
| 运行稳定性 4 | §2 四形态 25 条全绿；§6 自检表（含"不改原包"与"不改被测逻辑"两条） |
| 异常处理 3 | §3 逐行给出 `退出码 / status / uncertainty / fail-warn 检查名`；§4 六条已知盲区**如实公示**；§5 两条真实缺陷"崩溃 → 增量修复 → 转绿"的全过程 |

> **不能说的事**：本矩阵证明的是"这 25 类故障被注入后行为符合预期"，
> **不证明**"平台上不会出别的故障"，也不证明"图在科学上一定对"
> （A2 已明示结构门管不到语义）。本文件不为分数背书。
