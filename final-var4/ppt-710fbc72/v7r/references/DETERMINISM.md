# DETERMINISM — 确定性与字节级可复现（实测报告）

本文件回答两个问题：**同一输入重跑，产物是否一样**；**不一样的那些字段是谁、
为什么**。全部数字来自 `scripts/determinism.py` 的一次真实运行，脚本把结果同时
写成 `determinism_report.json`（机器可读）与本表（人可读），**没有手抄成分**。

复核命令（包外可写目录；包内跑会留下 `__pycache__`，资源契约拒收）：

```bash
RUN=<包外目录>
python "$SKILL_DIR/scripts/determinism.py" --skill "$SKILL_DIR" --run "$RUN"     --runs 3 --json "$RUN/determinism_report.json" --markdown "$RUN/determinism.md"
echo "exit=$?"        # 实测 exit 0
```

---

## 1. 结论（实测）

| 判据 | 结果 |
|-|-|
| 二进制交付物 **L1 逐字节一致**（16/16 次，跨进程/跨 cwd/跨 `PYTHONHASHSEED`/相对与绝对参数） | **是** |
| 全部 JSON 记录在 **L4**（去时间戳 + 归宿主锚点 + 去锚点派生摘要）后收敛为单一值 | **是** |
| **声明表之外**出现差异的字段 | **0 条** |
| 脚本退出码 | **0** |

稳定的 6 个文件及其 sha256（16 次运行共用同一值）：

| 产物 | sha256 | 说明 |
|-|-|-|
| `example-catalyst-201_deck.pptx` | `c41cb2ce6db055ce5a0cb064384bbe3ac5eaa9c1e1d57478bdc911a50621a416` | 可编辑交付物；zip 条目时间戳已被 `deterministic_zip()` 冻结 |
| `example-catalyst-201_cover_preview.png` | `588d51d9e1dfb5242c4ae8ed4aa750ad0a6cdc68217a0543f7804543a51d6882` | PIL 示意图封面 |
| `example-catalyst-201_slides_contact_schematic.png` | `2b60b2deac0042b963bdd0b97e81d161c860d82eea88d3f39bc88ccb439fafbd` | 全册联系表 |
| `_runtime/builtin.pptx` | `f75fa66e4ebf88d1069df49adf7dbf7fe748c5e2f54c83e93d9e0f3e95c82995` | 运行时回退模板 |
| `summary.txt` | `f7649354ac0cd559…` | 纯文本摘要 |
| `_PREVIEW_ARE_SCHEMATIC.txt` | `029ca2f1bae13eb9…` | 预览免责声明 |

`make_template.py` 另外在**两个不同 cwd** 下各独立跑一次，产物 sha256 亦相同
（`f75fa66e4ebf88d1…`）——即"生成器本身"也通过了跨 cwd 检查。

## 2. 判据分层：为什么要四层

| 层 | 做法 | 通过的文件 |
|-|-|-|
| **L1 原始** | 直接比 sha256 | `deck.pptx`、两张 PNG、`builtin.pptx`、`summary.txt`、`_PREVIEW_ARE_SCHEMATIC.txt` |
| **L2 去时间戳** | 去掉 `NONDETERMINISM` | —（路径记录仍在，见 L3） |
| **L3 归锚点** | 再把调用者目录/输出目录/用例目录换成 `<CWD>/<OUT>/<CASEDIR>` | `spec.json`、`adopt_plan.json`、`content.json`、`render_log.json` |
| **L4 再去派生摘要** | 最后把**锚点记录的 sha256** 换成 `<DERIVED>` | `audit.json`、`result.json`（全部 JSON 均在 L4 收敛） |

**L4 不是放宽标准，是为了问对问题。** `result.json.artifacts[].checks.sha256`
是 `spec.json` 的摘要，而 `spec.json` 里带着锚点路径：锚点一变，摘要必然变。这
是**级联**不是**不确定**。把已知原因替换成记号后再比，剩下的差异才是真缺陷——
实测剩下 **0 条**。

## 3. 故意不稳定的字段（逐类说明 + 稳定化办法）

### 3.1 时间戳（1 条）

| 字段 | 为什么故意不稳定 | 怎么稳定化 |
|-|-|-|
| `result.json.generated_at`（及 `verification.render.generated_at` 的副本） | 墙钟 UTC 戳，1 秒分辨率 | **不建议**冻死时间戳：那等于在产物里写假时间。要比对就比 L2/L4；要审计"哪次跑的"，这个戳正是唯一的锚 |

### 3.2 宿主锚定（34 条）

这些值是"运行发生在哪里"的**确定性函数**：同一台机器、同一目录重跑必然相同，
换目录/换机器必然不同。它们同时是**评审用来找到文件的定位符**，删不得。

| 字段族 | 值是什么 | 为什么不能删 | 怎么稳定化 |
|-|-|-|-|
| `result.json.artifacts[].abspath` | 相对**当前运行目录**的便携路径 | `references/OUTPUT_CONTRACT.md` 明确要求这种形态；它是"这个文件在哪"的答案 | 若要把"跨 cwd 逐字节一致"升级为硬指标，需把记录锚点从 cwd 改为输出目录，**并同步改契约措辞**——本包不动契约文本，故如实列为取舍 |
| `*.detail`（`audit.json.checks[]`、`result.json.verification.checks[]`） | 审计项里引用的产物路径 | 审计的意义就是"我检查了哪个文件" | 同上 |
| `adopt_plan.json.template.source`、`result.json.template_audit.template_source` | 交给构建阶段的模板路径 | 阶段一↔阶段二一致性的证据 | 同上 |
| `render_log.json.cover.path` / `contact_sheet.path`（及 result.json 中的回声） | 预览输出路径 | 渲染后端自查的定位 | 同上 |
| `content.json.sources[].path`、`figures[].file_abs`、`spec.json.pages[].figures_on_page[].file` | 输入材料的解析路径 | 证据可追溯的根 | `--case` 用相对路径给出时记录即为相对路径（见 §3.3） |

### 3.3 调用形态（4 类）

同一次运行内稳定，但**"`--case` 给相对路径"与"给绝对路径"两种形态之间不同**：
`extract._locate()` 在路径本来就是绝对路径时原样记录，否则相对用例目录解析。

| 字段 | 相对参数 | 绝对参数 |
|-|-|-|
| `content.json.sources[].path` | 用例相对（如 `../../../input/material.md`） | 原样绝对路径 |
| `content.json.figures[].file_abs` | 同上 | 同上 |
| `spec.json.pages[].figures_on_page[].file` | 转抄 content.json 的结果 | 同上 |
| `audit.json.hashes.spec_sha256` | 随 `spec.json` 变化 | 同上 |

**稳定化办法**：固定调用形态（推荐正式运行时一律传绝对路径 `/input/case.json`）
即可让这四类在重跑间恒定。

### 3.4 锚点派生摘要（6 条）

| 字段 | 上游 |
|-|-|
| `result.json.artifacts[].checks.sha256` | `spec.json`/`adopt_plan.json`/`content.json`/`audit.json`/`render_log.json` |
| `result.json.verification.traceability.hashes.spec_sha256` / `.adopt_plan_sha256` | 同上 |
| `audit.json.hashes.spec_sha256` / `.adopt_plan_sha256` | 同上 |
| `result.json.uncertainty[].note`（内置回退模板那条） | 说明文字里引用了运行期模板路径 |

**稳定化办法**：**先稳定上游**（§3.2/§3.3），摘要自动一致。这也是本包把 L4 作为
最终判据的原因——它把"级联"和"不确定"分开。

### 3.5 宿主版本（`tool_versions.*`）

解释器与依赖版本：同一镜像内恒定。本包不为它做任何伪装。

## 4. 已知未覆盖（诚实声明）

1. **未做跨机器比对**：本报告的所有 run 都在同一台机器、同一 Python（3.13.9）上。
   跨机器差异（字体集、`pptx` 版本、区域设置）**未被本实验覆盖**；`tool_versions`
   与字体探测字段就是为让这种差异**可见**而保留的。
2. **未覆盖并发**：两次 `main.py` 同时写同一个 `--out` 未测试（本包不声称支持）。
3. **未覆盖 `--starting-deck`/`--template` 分支的确定性**：本实验跑的是"案例未给
   模板"的回退路径（`opened_from=builtin`）。给模板时 `template.source` 会指向该
   模板，其余字段族相同，但未逐条实测。
4. **`--runs` 默认 3**：`c1`/`c2` 的次数受参数控制，`c3`/`c4`/`c5` 固定 3/4/3 次。
   总次数 16 是本报告的实测规模，不是上限。
5. **`INVOCATION_FORM` 只在本实验的两种形态上验证**（相对 vs 绝对）；其它形态
   （如 `--case` 给符号链接）未测。

## 5. 与基线的差异（脚本层）

**`scripts/` 下既有脚本逐字节未改**（与基线同源，`cmp` 全等）。本轴只新增
`scripts/determinism.py` 一个入口与 `references/DETERMINISM.md` 一个参考文件；
CLI 参数、退出码语义一律未动。

---

# 附：实测报告原文

以下为 `determinism.py --runs 3` 的真实渲染输出（节），未做任何人工修改。

## 2. 逐次实测

| run | 条件 | cwd 形态 | 参数形态 | PYTHONHASHSEED | exit | 耗时 s | 产物数 | status |
|-|-|-|-|-|-|-|-|-|
| `c1-1` | c1 | `cwdA` | absolute | `(unset)` | 0 | 1.594 | 12 | `success` |
| `c1-2` | c1 | `cwdA` | absolute | `(unset)` | 0 | 1.501 | 12 | `success` |
| `c1-3` | c1 | `cwdA` | absolute | `(unset)` | 0 | 1.426 | 12 | `success` |
| `c2-1` | c2 | `cwdA` | absolute | `(unset)` | 0 | 1.562 | 12 | `success` |
| `c2-2` | c2 | `cwdA` | absolute | `(unset)` | 0 | 1.57 | 12 | `success` |
| `c2-3` | c2 | `cwdA` | absolute | `(unset)` | 0 | 1.84 | 12 | `success` |
| `c3-1` | c3 | `cwdB/nest1` | absolute | `(unset)` | 0 | 1.544 | 12 | `success` |
| `c3-2` | c3 | `cwdB/nest1/nest2` | absolute | `(unset)` | 0 | 1.441 | 12 | `success` |
| `c3-3` | c3 | `cwdB` | absolute | `(unset)` | 0 | 1.416 | 12 | `success` |
| `c4-1` | c4 | `cwdA` | absolute | `0` | 0 | 1.531 | 12 | `success` |
| `c4-2` | c4 | `cwdA` | absolute | `1` | 0 | 1.562 | 12 | `success` |
| `c4-3` | c4 | `cwdA` | absolute | `12345` | 0 | 1.55 | 12 | `success` |
| `c4-4` | c4 | `cwdA` | absolute | `(unset)` | 0 | 1.527 | 12 | `success` |
| `c5-1` | c5 | `cwdC` | relative | `(unset)` | 0 | 2.193 | 12 | `success` |
| `c5-2` | c5 | `cwdC` | relative | `(unset)` | 0 | 1.947 | 12 | `success` |
| `c5-3` | c5 | `cwdC` | relative | `(unset)` | 0 | 1.74 | 12 | `success` |

## 3. 逐文件 sha256（全条件合并）

| 产物（相对 `--out`） | 原始 sha256 分组数 | L1 判定 | sha256 / 分组 |
|-|-|-|-|
| `_PREVIEW_ARE_SCHEMATIC.txt` | 1 | 逐字节一致 | `029ca2f1bae13eb93804…` |
| `_runtime/builtin.pptx` | 1 | 逐字节一致 | `f75fa66e4ebf88d1069d…` |
| `adopt_plan.json` | 3 | **不一致** | `40656e7c9a23…`×1；`43d836e723b6…`×14；`86ae2456fb5c…`×1 |
| `audit.json` | 4 | **不一致** | `3ff00e87c877…`×11；`88174664fdd9…`×3；`9b345608f9e9…`×1；`f176be053a96…`×1 |
| `content.json` | 2 | **不一致** | `246d71037dd0…`×3；`994c3e3c38f6…`×13 |
| `example-catalyst-201_cover_preview.png` | 1 | 逐字节一致 | `588d51d9e1dfb5242c4a…` |
| `example-catalyst-201_deck.pptx` | 1 | 逐字节一致 | `c41cb2ce6db055ce5a0c…` |
| `example-catalyst-201_slides_contact_schematic.png` | 1 | 逐字节一致 | `2b60b2deac0042b963bd…` |
| `render_log.json` | 14 | **不一致** | `04df0aca79a7…`×1；`1061257afffe…`×1；`129857165901…`×1；`35cae467e6c9…`×1；`5b67b00bf8e6…`×1；`66463ec7a506…`×1；`7874861a72db…`×1；`7c299b0fe652…`×1；`7fea65bb6660…`×1；`9893eeba5342…`×1；`a22b3cc74e88…`×1；`b50e5eaec20c…`×3；`d2409beee6da…`×1；`d7090b1170d6…`×1 |
| `result.json` | 16 | **不一致** | `0f9179fc4935…`×1；`15d62b4c1d36…`×1；`1a9ffe8d881e…`×1；`2e19eea3ca89…`×1；`43d8503f49a2…`×1；`4e29d0526385…`×1；`894446ced5c0…`×1；`8a55bd4eefd8…`×1；`94bc59d9e338…`×1；`9bedccbd13c9…`×1；`b2f8735f1f7d…`×1；`bbb7eeef6ff6…`×1；`c3bffd440ecd…`×1；`c9cc03908754…`×1；`e9215539a9ec…`×1；`fbe0d34afebc…`×1 |
| `spec.json` | 2 | **不一致** | `15a9d8547326…`×13；`4143d988faf2…`×3 |
| `summary.txt` | 1 | 逐字节一致 | `f7649354ac0cd5595c50…` |

## 4. 四层一致性（L1 原始 / L2 去时间戳 / L3 归锚点 / L4 再去锚点派生摘要）

| JSON 记录 | L1 原始 | L2 去时间戳 | L3 去时间戳+归锚点 | L3 每条件内 | L4 再去派生摘要 | 通过层 |
|-|-|-|-|-|-|-|
| `adopt_plan.json` | 3 | 3 | 1 | c1:1/c2:1/c3:1/c4:1/c5:1 | 1 | **L3** |
| `audit.json` | 4 | 4 | 4 | c1:1/c2:1/c3:3/c4:1/c5:1 | 1 | **L4** |
| `content.json` | 2 | 2 | 1 | c1:1/c2:1/c3:1/c4:1/c5:1 | 1 | **L3** |
| `render_log.json` | 14 | 14 | 1 | c1:1/c2:1/c3:1/c4:1/c5:1 | 1 | **L3** |
| `result.json` | 16 | 14 | 14 | c1:3/c2:3/c3:3/c4:4/c5:1 | 1 | **L4** |
| `spec.json` | 2 | 2 | 1 | c1:1/c2:1/c3:1/c4:1/c5:1 | 1 | **L3** |

### L2 未通过的文件，差异被归因到这些路径字段（实测替换命中）

- `adopt_plan.json`：`template.source`
- `audit.json`：`checks[0].detail`；`checks[1].detail`；`checks[2].detail`；`checks[3].detail`；`checks[4].detail`
- `content.json`：`figures[0].file_abs`；`figures[1].file_abs`；`sources[0].path`
- `render_log.json`：`contact_sheet.path`；`cover.path`
- `result.json`：`artifacts[0].abspath`；`artifacts[1].abspath`；`artifacts[2].abspath`；`artifacts[3].abspath`；`artifacts[4].abspath`；`artifacts[5].abspath`；`artifacts[6].abspath`；`artifacts[7].abspath`…
- `spec.json`：`pages[3].figures_on_page[0].file`；`pages[3].figures_on_page[1].file`；`pages[4].figures_on_page[0].file`

### 核心交付物逐项判定

| 核心产物 | 判定 |
|-|-|
| `example-catalyst-201_deck.pptx` | L1 逐字节一致（16/16 次） |
| `example-catalyst-201_cover_preview.png` | L1 逐字节一致（16/16 次） |
| `example-catalyst-201_slides_contact_schematic.png` | L1 逐字节一致（16/16 次） |
| `spec.json` | L3 一致（每个条件内 1 个唯一值；差异仅来自调用形态/宿主锚点） |
| `adopt_plan.json` | L3 一致（每个条件内 1 个唯一值；差异仅来自调用形态/宿主锚点） |
| `content.json` | L3 一致（每个条件内 1 个唯一值；差异仅来自调用形态/宿主锚点） |
| `summary.txt` | L1 逐字节一致（16/16 次） |
| `_runtime/builtin.pptx` | L1 逐字节一致（16/16 次） |

## 5. 易变字段逐条归因（实测得到的字段清单）

| 文件 | JSON 路径 | 归类 | 声明理由 | 首次值示例 |
|-|-|-|-|-|
| `adopt_plan.json` | `template.source` | **故意**·宿主锚定 | resolved path of the template handed to the build stage | `'../out/_runtime/builtin.pptx'` |
| `audit.json` | `checks[0].detail` | **故意**·宿主锚定 | audit-check text that quotes the artifact path it checked | `'../out/example-catalyst-201_deck.pptx'` |
| `audit.json` | `checks[1].detail` | **故意**·宿主锚定 | audit-check text that quotes the artifact path it checked | `'../out/example-catalyst-201_cover_preview.png'` |
| `audit.json` | `checks[2].detail` | **故意**·宿主锚定 | audit-check text that quotes the artifact path it checked | `'../out/example-catalyst-201_slides_contact_schematic.png'` |
| `audit.json` | `checks[3].detail` | **故意**·宿主锚定 | audit-check text that quotes the artifact path it checked | `'../out/spec.json'` |
| `audit.json` | `checks[4].detail` | **故意**·宿主锚定 | audit-check text that quotes the artifact path it checked | `'../out/adopt_plan.json'` |
| `audit.json` | `hashes.adopt_plan_sha256` | **故意**·宿主锚定 | the same digest, as recorded in audit.json | `'43d836e723b65c5201daaedcd9a7e9b6a0f1584c27b2d032e7a56faa7571a778'` |
| `audit.json` | `hashes.spec_sha256` | **故意**·宿主锚定 | the same digest, as recorded in audit.json | `'15a9d8547326ea4abc42d36b56536d2502c98050ae218b7863998d89268b84ce'` |
| `content.json` | `figures[0].file_abs` | **故意**·宿主锚定 | resolved input path of a figure file | `'D:/BuildTemp/e3var-out3/ppt-710fbc72/_probe/detrun/input/figs/fig1.png'` |
| `content.json` | `figures[1].file_abs` | **故意**·宿主锚定 | resolved input path of a figure file | `'D:/BuildTemp/e3var-out3/ppt-710fbc72/_probe/detrun/input/figs/fig2.png'` |
| `content.json` | `sources[0].path` | **故意**·宿主锚定 | leaf canonically rewrites to `<TOKEN>/<relative>` — a recorded path whose only difference between runs is the anchor | `'D:/BuildTemp/e3var-out3/ppt-710fbc72/_probe/detrun/input/material.md'` |
| `render_log.json` | `contact_sheet.path` | **故意**·宿主锚定 | resolved output path of the contact-sheet preview | `'D:/BuildTemp/e3var-out3/ppt-710fbc72/_probe/detrun/runs/c1-1/out/example-catalyst-201_slides_contact_schematic.png'` |
| `render_log.json` | `cover.path` | **故意**·宿主锚定 | resolved output path of the cover preview | `'D:/BuildTemp/e3var-out3/ppt-710fbc72/_probe/detrun/runs/c1-1/out/example-catalyst-201_cover_preview.png'` |
| `result.json` | `artifacts[0].abspath` | **故意**·宿主锚定 | portable path = a pure function of the caller's cwd (references/OUTPUT_CONTRACT.md requires exactly this form) | `'../out/example-catalyst-201_deck.pptx'` |
| `result.json` | `artifacts[1].abspath` | **故意**·宿主锚定 | portable path = a pure function of the caller's cwd (references/OUTPUT_CONTRACT.md requires exactly this form) | `'../out/example-catalyst-201_cover_preview.png'` |
| `result.json` | `artifacts[2].abspath` | **故意**·宿主锚定 | portable path = a pure function of the caller's cwd (references/OUTPUT_CONTRACT.md requires exactly this form) | `'../out/example-catalyst-201_slides_contact_schematic.png'` |
| `result.json` | `artifacts[3].abspath` | **故意**·宿主锚定 | portable path = a pure function of the caller's cwd (references/OUTPUT_CONTRACT.md requires exactly this form) | `'../out/spec.json'` |
| `result.json` | `artifacts[3].checks.sha256` | **故意**·锚点派生摘要 | sha256 of spec.json/adopt_plan.json/content.json/audit.json/render_log.json, each of which carries a host anchor (see the file's own row) | `'15a9d8547326ea4abc42d36b56536d2502c98050ae218b7863998d89268b84ce'` |
| `result.json` | `artifacts[4].abspath` | **故意**·宿主锚定 | portable path = a pure function of the caller's cwd (references/OUTPUT_CONTRACT.md requires exactly this form) | `'../out/adopt_plan.json'` |
| `result.json` | `artifacts[4].checks.sha256` | **故意**·锚点派生摘要 | sha256 of spec.json/adopt_plan.json/content.json/audit.json/render_log.json, each of which carries a host anchor (see the file's own row) | `'43d836e723b65c5201daaedcd9a7e9b6a0f1584c27b2d032e7a56faa7571a778'` |
| `result.json` | `artifacts[5].abspath` | **故意**·宿主锚定 | portable path = a pure function of the caller's cwd (references/OUTPUT_CONTRACT.md requires exactly this form) | `'../out/content.json'` |
| `result.json` | `artifacts[5].checks.sha256` | **故意**·锚点派生摘要 | sha256 of spec.json/adopt_plan.json/content.json/audit.json/render_log.json, each of which carries a host anchor (see the file's own row) | `'994c3e3c38f62d741f3da9cd954029ab8b8e6de352a085e56c6e820278b6075a'` |
| `result.json` | `artifacts[6].abspath` | **故意**·宿主锚定 | portable path = a pure function of the caller's cwd (references/OUTPUT_CONTRACT.md requires exactly this form) | `'../out/audit.json'` |
| `result.json` | `artifacts[6].checks.sha256` | **故意**·锚点派生摘要 | sha256 of spec.json/adopt_plan.json/content.json/audit.json/render_log.json, each of which carries a host anchor (see the file's own row) | `'054fbc687f573df8587944f31129f21493e1dc761fb4728b45b5e202d500f010'` |
| `result.json` | `artifacts[7].abspath` | **故意**·宿主锚定 | portable path = a pure function of the caller's cwd (references/OUTPUT_CONTRACT.md requires exactly this form) | `'../out/render_log.json'` |
| `result.json` | `artifacts[7].checks.sha256` | **故意**·锚点派生摘要 | sha256 of spec.json/adopt_plan.json/content.json/audit.json/render_log.json, each of which carries a host anchor (see the file's own row) | `'12985716590140821d1a03315826a8cad74b6002b22bf263a380801ad4fe6c90'` |
| `result.json` | `generated_at` | **故意**·时间戳/版本 | wall-clock UTC stamp written on purpose (ISO8601, 1 s resolution) | `'2026-11-23T11:26:36Z'` |
| `result.json` | `template_audit.template_source` | **故意**·宿主锚定 | same value, echoed into result.json | `'../out/_runtime/builtin.pptx'` |
| `result.json` | `uncertainty[0].note` | **故意**·锚点派生摘要 | disclosure text; the builtin-template entry quotes the run-time template path | `'no usable case template/starting deck: the 16:9 fallback template was regenerated at run time (generated-at-runtime:../out/_runtime/builtin` |
| `result.json` | `verification.checks[0].detail` | **故意**·宿主锚定 | audit-check text that quotes the artifact path it checked | `'../out/example-catalyst-201_deck.pptx'` |
| `result.json` | `verification.checks[1].detail` | **故意**·宿主锚定 | audit-check text that quotes the artifact path it checked | `'../out/example-catalyst-201_cover_preview.png'` |
| `result.json` | `verification.checks[2].detail` | **故意**·宿主锚定 | audit-check text that quotes the artifact path it checked | `'../out/example-catalyst-201_slides_contact_schematic.png'` |
| `result.json` | `verification.checks[3].detail` | **故意**·宿主锚定 | audit-check text that quotes the artifact path it checked | `'../out/spec.json'` |
| `result.json` | `verification.checks[4].detail` | **故意**·宿主锚定 | audit-check text that quotes the artifact path it checked | `'../out/adopt_plan.json'` |
| `result.json` | `verification.render.contact_sheet.path` | **故意**·宿主锚定 | the same preview path, echoed into result.json | `'D:/BuildTemp/e3var-out3/ppt-710fbc72/_probe/detrun/runs/c1-1/out/example-catalyst-201_slides_contact_schematic.png'` |
| `result.json` | `verification.render.cover.path` | **故意**·宿主锚定 | the same preview path, echoed into result.json | `'D:/BuildTemp/e3var-out3/ppt-710fbc72/_probe/detrun/runs/c1-1/out/example-catalyst-201_cover_preview.png'` |
| `result.json` | `verification.traceability.hashes.adopt_plan_sha256` | **故意**·宿主锚定 | digest of spec.json / adopt_plan.json, which carry a host anchor | `'43d836e723b65c5201daaedcd9a7e9b6a0f1584c27b2d032e7a56faa7571a778'` |
| `result.json` | `verification.traceability.hashes.spec_sha256` | **故意**·宿主锚定 | digest of spec.json / adopt_plan.json, which carry a host anchor | `'15a9d8547326ea4abc42d36b56536d2502c98050ae218b7863998d89268b84ce'` |
| `spec.json` | `pages[3].figures_on_page[0].file` | **故意**·宿主锚定 | resolved input path of a figure (recorded as given, absolute or relative) | `'D:/BuildTemp/e3var-out3/ppt-710fbc72/_probe/detrun/input/figs/fig1.png'` |
| `spec.json` | `pages[3].figures_on_page[1].file` | **故意**·宿主锚定 | resolved input path of a figure (recorded as given, absolute or relative) | `'D:/BuildTemp/e3var-out3/ppt-710fbc72/_probe/detrun/input/figs/fig2.png'` |
| `spec.json` | `pages[4].figures_on_page[0].file` | **故意**·宿主锚定 | resolved input path of a figure (recorded as given, absolute or relative) | `'D:/BuildTemp/e3var-out3/ppt-710fbc72/_probe/detrun/input/figs/fig2.png'` |

声明表之外出现差异的字段：**0 条**（实测字段集合与声明表完全吻合）。

