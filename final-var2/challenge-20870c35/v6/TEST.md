# TEST.md — 本地实测记录（challenge-20870c35 · **v5 多案例泛化版**）

- 测试时间：2026-11-22 15:37–15:57 +08（Asia/Shanghai）
- 测试机：Windows（Git Bash / MSYS2），Python 3.13.9（Anaconda）
- 被测定版本：本目录全部文件（`scripts/` 14 个 Python 脚本，最后一次 `py_compile` 通过后未再改动）
- 测试方式：把包**复制到一个临时目录**（本机为系统临时盘下的 ASCII 目录）里跑，不在提交目录里跑，避免把运行产物 / `__pycache__` 混进提交资源
- 覆盖：语法编译 / 合成输入再生成 / 主流程 smoke / 独立复核四件套 / 全链路自检 / 双跑确定性 /
  模板适配 / 跳过预览 / cwd 自定位 / **六条降级与失败分支（含负例）** /
  **§13 多案例泛化复跑（两个不同题材的合成案例 + 三个边界探针）**

## 0. 环境与依赖

```
$ python --version
Python 3.13.9
$ python -c "import pptx,PIL,pypdf; print(pptx.__version__, PIL.__version__, pypdf.__version__)"
1.0.2 12.3.0 6.14.2
```

依赖策略：**必需**只有 `python-pptx` + `Pillow`；`pypdf`/`PyPDF2` 为 PDF 可选解析器；
`scripts/make_synthetic_inputs.py` 零第三方依赖（PDF 为手工构造的最小 PDF，PNG 用 Pillow）。
缺任何一个都不崩：见 §8。

## 1. 语法检查（T1）

```
$ cd <pkg>/scripts && for f in *.py; do python -m py_compile "$f" || exit 1; done
COMPILE_OK 14/14 scripts          # 退出码 0
```

## 2. 合成输入再生成（T0，对应"二进制资源改运行时生成"）

```
$ python scripts/make_synthetic_inputs.py
[synthetic-inputs] written=['dataset_card.pdf', 'fig2.png']
$ python scripts/make_synthetic_inputs.py                 # 幂等：已存在则跳过
[synthetic-inputs] skipped(existing)=['dataset_card.pdf', 'fig2.png']
$ python scripts/make_synthetic_inputs.py --force --template
[synthetic-inputs] written=['dataset_card.pdf', 'fig2.png', 'synthetic_template.pptx']
$ python -c "from pypdf import PdfReader; print(repr(PdfReader('examples/materials/dataset_card.pdf').pages[0].extract_text()[:80]))"
'SYNTHETIC EXAMPLE - generated placeholder, not real research data\nDataset card - SynthAlign ...'
```

三个退出码均为 0。生成的 PDF 可被 pypdf 正常抽取文本（12 行文本层），生成的 PNG 是纯几何示意图
（带 `SYNTHETIC EXAMPLE` 标注，不含任何测量值）。

## 3. 主流程 smoke（T2 · 验收形态）

```
$ python scripts/main.py --case examples/case.json --out <OUT>/out-A
[plan] 12 pages, narrative=group_meeting, audience=familiar, P-gates valid=True
[deck] 12 slides, mode=built-in-theme, verify valid=True
[preview] wrote 13 preview files (PIL simulation)
[done] status=completed deck_ok=True preview_ok=True plan_gates=True evidence_audit=True validate_valid=True contract_valid=True
退出码 0
```

产出（`<OUT>/out-A`，均为真实文件）：

```
deck_audit.json  editable_deck.pptx  evidence_audit.json  evidence_map.json
plan_gates.json  previews/{cover_preview.png, preview_grid.png, preview_manifest.json, slide_002..011.png}
result.json  self_check.json  talk_plan.json
```

单次运行耗时：约 1.6–3.1 秒。

## 4. 独立复核四件套 + 全链路自检（T3）

| 测试 | 命令 | 退出码 |
|-|-|-|
| T3a 结构 + 文件在盘 + 数字提示 | `python scripts/validate_result.py out-A/result.json` | 0 |
| T3b 契约齐全 | `python scripts/check_contract.py out-A/result.json` | 0 |
| T3c 证据逐字审计 | `python scripts/evidence_audit.py out-A/result.json` | 0 |
| T3d deck 机器校验 | `python scripts/verify_deck.py out-A/editable_deck.pptx --expect-pages 12 --plan out-A/talk_plan.json` | 0 |
| T3e 全链路 + 包约束 | `python scripts/selftest.py out-A --package-check <pkg>` | 0 |

`out-A/self_check.json` 观测值：

- `validate`：checks 10/10 ok，`errors=[]`，`warnings=[]`；
- `contract_check`：`declared=16 missing=0 wrong_type=0`（`checked_against = case.json + task.md`）；
- `audit.gates`：G1–G9 = true，G10 = null（设计如此：包约束由 `selftest --package-check` 执行）；
- `audit.plan_gates`：P1–P8 全过（`P3 pages=12 target=12`）；
- `audit.evidence.summary`：`{pages_total:12, content_pages:10, ok_pages:10, errors:0, derived_pages:0, unavailable_text:0}`；
- `audit.deck`：`valid=true`，12 张幻灯片，每页 `notes_nonempty=true`、`claim_element=true`。

T3e 的 `selftest` 明细：`checks=6 errors=0`（validate_result / check_contract / evidence_audit /
verify_deck / determinism_probe / package_constraints 全 ✓）；
包约束实测（含运行期生成的二进制）：`text=37 total_bytes=322018 max_file=42297`，`errors=[]`。

## 5. 双跑确定性（T4）

同一条命令写到两个目录（`out-A` / `out-B`），逐项比对：

| 文件 | A vs B |
|-|-|
| `evidence_map.json` / `plan_gates.json` / `deck_audit.json` / `evidence_audit.json` | **逐字节相同** |
| `previews/*.png`（12 张） | **逐字节相同**（12/12） |
| `talk_plan.json` / `result.json` / `preview_manifest.json` | 内容相同，仅记录性时间戳（`generated_at` / `change_records[].at`）不同 |

确定性探针（剔除记录性时间戳后的内容投影 sha）A/B 完全一致：

```
plan_sha16      = 1dcff19cb479cba9ada62c9ddab260135bf12f5c22aa0e39a3f569b151336120
evidence_map16  = 6a5d2847678c36dcb38e1f186f00a87e90d8a19af46117b00246247941d86214
deck 规范化 sha = 6d17df3f4c09de46490fb81ddb15b2bb03dd053dac1677b76f19f7e1c6dfc27e
```

结论：**同输入 → 页内容、证据、deck、预览全部逐位一致**；唯一差异是记录性时间戳，已在探针中排除并如实记录。

## 6. 模板适配（T5，起始演示路径）

```
$ python scripts/make_synthetic_inputs.py --out <TMP>/tpl --template   # 生成带 1 张自带页的起始演示
$ python scripts/main.py --case examples/case.json --out out-T --template <TMP>/tpl/synthetic_template.pptx --quiet
退出码 0
```

`out-T/result.json` 观测值：`status=completed`；`pages=12`；`deck_audit.slides=12`；
`artifacts.template_used=synthetic_template.pptx`；
`artifacts.deck_mode={mode: template-adapt, template_slides_present: 1, template_slides_dropped: 1}`；
`change_records` 有 `adapted template synthetic_template.pptx (master/layout reused; 1 pre-existing
slide(s) dropped so the deck matches the frozen page count of 12)`。
⇒ 沿用模板母版/版式，同时保证**最终页数 == 冻结页数**。

## 7. 跳过预览 / cwd 自定位（T6 / T7）

```
# T6：只渲染封面 + 网格
$ python scripts/main.py --case examples/case.json --out out-S --skip-previews --quiet   # 退出码 0
previews/ = {cover_preview.png, preview_grid.png, preview_manifest.json}；status=completed，G8=true

# T7a：cwd 不是技能根（在无关目录 <TMP> 下用绝对路径调用）
$ (cwd=<TMP>) python <TMP>/pkg/scripts/main.py --case <TMP>/pkg/examples/case.json --out out-C --quiet
退出码 0；status=completed；pages=12；sources[].path = materials/paper_extract.md, materials/figures.md,
materials/dataset_card.pdf, materials/fig2.png（**均为相对路径，无本机绝对路径**）

# T7b：自检脚本同样可在任意 cwd 运行
$ (cwd=<TMP>) python <TMP>/pkg/scripts/selftest.py out-C    # 退出码 0
```

## 8. 文档命令逐条实跑（T14：SKILL.md / README.md 里写的命令必须真能跑）

在**无关 cwd**（临时目录）下、用 `SKILL_DIR=<包目录>` 逐条执行文档里的命令（不做任何改写）：

| 文档位置 | 命令形态 | 退出码 | 观测 |
|-|-|-|-|
| `README.md` §1 步骤 0 | `make_synthetic_inputs.py` | 0 | 生成 `dataset_card.pdf` + `fig2.png`；重复执行跳过 |
| `README.md` §1 步骤 3 | `main.py --case … --out … --materials … --skip-previews`（cwd 非技能根） | 0 | `status=completed pages=12 deck=True`；`previews/` 仅封面+网格 |
| `SKILL.md` §4 CP2 命令形态 | `main.py --case … --task … --out …` | 0 | 同上（`--task` 路径被真正读取并解析 output_contract） |
| `references/OUTPUT_CONTRACT.md` §6 | `validate_result.py <out>/result.json --strict` | 0 | 无输出，strict 模式亦通过 |
| 同上 | `check_contract.py <out>/result.json --contract '<inline json>'` | 0 | `declared=8 missing=0 wrong_type=0`（内联契约生效） |
| 同上 | `evidence_audit.py <out>/result.json --sources-dir <材料目录> --out …_reread.json` | 0 | 复读报告 `valid=true`，**`unavailable_text=0`**（离开运行期仍能逐字复核） |
| `references/CONTRACT-GATES.md` §5 | `validate_plan.py <out>/talk_plan.json --materials-dir <材料目录>` | 0 | P1–P8 全过 |
| `references/CONTRACT-GATES.md` §独立复核 | `verify_deck.py … --expect-pages 12 --plan …` | 0 | 见 T3d |
| `SKILL.md` §7 | `selftest.py <out> --package-check <包目录>` | 0 | 见 T3e |

⇒ 文档里的脚本路径、参数名与 `scripts/` 实际入口**逐字对得上**，且在 cwd 不是技能根时同样可跑。

## 9. 降级与失败分支（T8–T13，**含负例**）

| 测试 | 条件 | 命令（同一入口） | 退出码 | `result.json` 观测值 |
|-|-|-|-|-|
| T8 | 案例声明的材料不存在 | `main.py --case <case-missing>/case.json --out out-M` | 0 | `status=partial`；`sources=[(paper_extract.md, md, parsed), (not_on_disk.pdf, missing, unparsed)]`；`uncertainty` 同时列出"未解析"与"声明但不存在"；`pages=8`，deck 正常生成 |
| T9 | 无 `pypdf`/`PyPDF2` | `PYTHONPATH=<shim> main.py --case examples/case.json --out out-P` | 0 | `status=partial`；`dataset_card.pdf` → `parsed=false`，`note="PDF parsing unavailable (pypdf/PyPDF2 not installed)…"`；其余材料照常出页 |
| T10 | 无 Pillow（连带 python-pptx 不可用） | `PYTHONPATH=<shim> main.py --case examples/case.json --out out-L` | 0 | `status=partial`；`artifacts.editable_deck=null`；`environment.pillow=null`、`python_pptx=null`；`uncertainty`/`change_records` 记明 |
| T11 | 无 `python-pptx` | `PYTHONPATH=<shim> main.py --case examples/case.json --out out-X` | 0 | `status=partial`；`pages=12` 页计划照常；`artifacts.deck_limitation="python-pptx 不可用(…)"`；`uncertainty` 首条即该限制；预览照常 |
| T12 | `case.json` 不可读 | `main.py --case <不存在>/case.json --out out-F` | **1** | 仍写最小 `result.json`（`status=failed` + `error`，且 error 文本里的本机路径已被净化）——**这是唯一应当非 0 退出的情形** |
| T13 | 材料为空 | `main.py --case <case-none>.json --out out-N` | 0 | `status=partial`；`pages=6`（仅结构性页面）；`sources=['(none)']`；`uncertainty` 明写"没有任何材料被解析为文本" |

退出码语义（与 `SKILL.md` §7 / `references/OUTPUT_CONTRACT.md` 一致）：
**0** = 已产出通过 validate + contract 的 `result.json`（其 `status` 字段说明是 `completed` 还是 `partial`）；
**1** = 没有可用的契约结果；**2** = 参数用法错误。

## 10. 图绑定与可编辑性（人工 + 机器）

```
deck: slides=12；picture shapes: [(slide 9, 'page-figure-09')]；media parts: ['/ppt/media/image1.png']
notes on all 12 slides: True
```

⇒ 示例材料里 `Fig. 2` 的引用被绑定到**运行期生成**的 `materials/fig2.png`，并真的嵌入 deck；
`Fig. 3` / `Table 1` 没有图片文件 → 页内诚实占位框，`evidence_audit.figure_bound=false` 如实记录。

## 11. 提交资源形态与包约束（G10）

在**提交目录本身**（不是包副本）上实测：

```
files = 39   (目标 20–40，上限 50)   total ≈ 339.3 KB / 347,4xx B (上限 2MB)
max single file = 42,426 B      (examples/output/result.example.json；上限 500KB)
extensions = {.md: 18, .py: 14, .json: 6, .txt: 1}   ← 全部在允许的七种之内
目录 = 根 5 + assets 2 + references 7 + scripts 14 + templates 3 + examples 4 (+materials 2, output 2)
无符号链接；无 __pycache__/*.pyc；示例二进制（pdf/png/pptx）不随包
```

`selftest.py --package-check`（在包副本上、含运行期生成的二进制时）报
`text=37 total_bytes=322018 max_file=42297`、`errors=[]`；提交目录因不含二进制，实际更小。

## 12. 已知限制 / 残余说明

- 预览为 Pillow 模拟渲染（每张带水印 + manifest 说明），**不是** Office 真实栅格化；
- `result.audit.gates.G10` 设计为 `null`（由 `selftest --package-check` 执行），非缺陷；
- 证据定位为行级/章节级近似锚点，源材料变化后需按引文复核；
- 模板适配会丢弃起始演示文件自带的示例页（记入 `change_records`），以保证页数等于冻结值；
- 平台 3 案例 × 3 复跑由平台执行，本节只记录本机可复现性证据。

## 13. 多案例泛化复跑（T15，v5 新增）

**做法**：在**包外**目录跑 `examples/cases/` 下两个合成案例，逐项对照
`references/VALIDATION-EVIDENCE.md` §2 的期望结构表；再用三个临时改造的探针**故意撞边界**，
把"泛化到哪里会失效"从推测变成实测。

```bash
SKILL_DIR="<本包根目录>"; OUT="<包外空目录>"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/case-a-muon-defense/case.json" --out "$OUT/a"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/case-b-scrna-review/case.json"   --out "$OUT/b"
```

### 13.1 两个合成案例（实测）

| 项 | case A（物理·答辩） | case B（生物·评审） |
|-|-|-|
| `exit` | **0** | **0** |
| `status` | `completed` | `completed` |
| 页数 / 冻结页数 | 15 / 15 | 8 / 8 |
| 叙事顺序 | `title, agenda, motivation, background, method, results, innovation_limits, conclusion, qa` | `title, agenda, **conclusion**, method, results, innovation_limits, qa` |
| 听众判定 | `expert`（背景占比 0.10） | `expert`（背景占比 0.10） |
| P-gates | `gates=8 ok=8`，`P3: pages=15 target=15` | `gates=8 ok=8`，`P3: pages=8 target=8` |
| `evidence_audit` | `content=11 ok=11 errors=0 derived=3` | `content=5 ok=5 errors=0 derived=1` |
| `deck_audit` | `valid=true`，15 页 | `valid=true`，8 页 |
| `result.json` 顶层键 | 20 | 20 |
| 问答条数 / `qa` 备用页 | 3 / 2 页 | 2 / 1 页 |
| 图引用绑定 | `Fig. 1` → 页 7（**无图片文件 ⇒ 诚实占位**） | `Table 1` → 页 4、`Fig. 1` → 页 6（同样占位） |
| 预览文件 | 14 | 8 |
| `uncertainty` | 4 条 | 4 条 |

**结论（可判定）**：同一套脚本在**两个学科、两种汇报类型、两种页数/时长量级**上都产出契约完整、
门全过、可复核的结果；块顺序随 `report_type` **真的变了**（B 里 `conclusion` 提到 `method` 之前），
说明叙事是配置驱动而非硬编码。

### 13.2 边界探针（三个，均为实测；输入不随包提交）

| 探针 | 注入 | 实测 |
|-|-|-|
| P1 未知类型 | `report_type="workshop_retreat"` | `status=completed`、15 页、P-gates 8/8；`talk_plan.narrative.report_type` 变成 **`group_meeting`**，**`agenda` 页消失**，`uncertainty` **无**相关条目 ⇒ **静默替换（已知边界，未修）** |
| P2 页数越界 | `duration_min=5, slide_count=40` | 产出 **30** 页；`result.slide_count=30`；`timing.seconds_per_slide=10.0`；`P3: pages=30 target=30` **门仍通过**；`uncertainty` 无钳制说明 ⇒ **静默钳制（已知边界，未修）** |
| P3 无听众 | `case.json` 去掉 `audience` | `expertise=familiar`、`background_ratio=0.18`、`audience.notes` 写明"听众信息缺失…可覆写" ⇒ **按 D7 诚实降级**（无 status 降级，符合设计） |
| P4 纯英文材料 | 材料换成英文论文体（876 字符） | **修前**：`status=completed` 但 `derived_pages=11 / content_pages=11`（11 个内容页全部无逐字引文）⇒ **静默质量损失**；**修后**（Fix 7）：`status=partial`，`uncertainty` 由 4 条增至 5 条，新增条目写明"共抽出 6 条候选主张，但它们一条都没有被逐字引用到页面上" |

### 13.3 本版的脚本改动（逐条点名；**全部为纯增量**）

本版（v5）携带与 v4/v6 相同的那组修复（同一作者、同一来源：失败注入演练暴露的真实缺陷），
外加**本版独有的 Fix 7**。**没有**任何改动删除既有键、改 CLI 参数名/默认值或改退出码三分语义。

| # | 文件 | +/- 行 | 来源 | 修的是什么 |
|-|-|-|-|-|
| Fix 1 | `scripts/deck_builder.py` | +24 / -1 | v4 注入 `F07` | 模板容器损坏时异常穿透编排器（`status=failed`、退出码 1）→ 改为 `try` 打开、失败即记 `template_load_error` 并回落内置主题 |
| Fix 2 | `scripts/evidence.py` | +12 / -0 | v4 注入 `F05` | 无文本层 PDF 被记 `parsed=true`（假成功）→ 改为记 `parsed=false` + OCR 提示 |
| Fix 3 | `scripts/common.py` | +27 / -2（与 Fix 4 合计） | v4 注入 `F12`·`F13` | 契约块"存在但不可用"时调用方拿不到原因 → 新增原因列表落到返回 `note` |
| Fix 4 | `scripts/common.py` | +5 / -0（含在上面 27 行内） | v4 注入 `F14` | 类型未声明的契约字段落 `null`，违反契约 §1「禁止 null」→ `default is None → ""` |
| Fix 5 | `scripts/main.py` | +29 / -0（与 Fix 6 合计） | v4 注入 `F12`·`F13` | 契约解析失败的 `note` 被丢弃 → 写 `change_records`(step=`contract`) + `uncertainty`，`status→partial` |
| Fix 6 | `scripts/main.py` | +12 / -0（含在上面 29 行内） | v4 注入 `F07` | 模板回落的降级原因只在 `artifacts.deck_mode` → 追加一条 `uncertainty` |
| **Fix 7** | `scripts/main.py` | +12 / -0（`main.py` 合计 +53） | **本版** §4.3 探针 | 抽出主张却全部退化成概括页时 `status` 仍 `completed`（静默质量损失）→ 判据「主张 ≥3 且 内容页 >0 且 `derived_pages >= content_pages`」⇒ `change_records`(step=`audit`) + `uncertainty` + `status→partial` |

**逐字节未变的脚本**（10 个）：`check_contract.py`、`evidence_audit.py`、`finalize_result.py`、
`make_synthetic_inputs.py`、`render.py`、`scaffold_plan.py`、`selftest.py`、`validate_plan.py`、
`validate_result.py`、`verify_deck.py`。

> **回归证据**：Fix 7 生效后重跑两案，L2/L3 仍为 `status=completed`（`derived_pages` 分别 3/11 与 1/5，
> 均未触发判据）⇒ 修复**没有**误伤正常中文案例；纯英文探针则由 `completed` 变 `partial`。

### 13.4 本节的边界（没有证明什么）

1. 每案只跑 **1** 次；平台是 3 案例 × 3 复跑，**重复性不在本节结论内**（双跑一致性见 §5 的 T4）。
2. 三个探针的输入是**临时改造**的副本，不随包提交 ⇒ 复现需按 §13.2 自己改一个字段。
3. 两个案例**都不含 PDF**、都走 `built-in-theme`（无模板），
   ⇒ 本节的结论**不覆盖** PDF 解析与模板适配两条路径。
4. §4 列出的其余未验证方向（超长材料 / 非中非英材料 / 跨材料矛盾数字 / 材料数 >2）
   **没有实测数据**，不作任何断言。

## 14. union 包的两项额外核验（v6 专属）

### 14.1 契约字段块逐字保留

`references/OUTPUT_CONTRACT.md` 的 §1–§5（字段表 / 证据字段 / `status` 语义与退出码 /
`audit` 结构 / `self_check` 结构）必须与基线**逐字节相同**。核验方式不是肉眼比对，而是
**按小节切段后做字符串相等比较**：

```bash
python - <<'EOF'
import io
B = "<基线>/references/OUTPUT_CONTRACT.md"
P = "<本包>/references/OUTPUT_CONTRACT.md"
base, t = io.open(B, encoding="utf-8").read(), io.open(P, encoding="utf-8").read()
for name, a, b in (("§1","## 1. 必填字段","## 2. 证据与页级结构"),
                   ("§2","## 2. 证据与页级结构","## 3. status 语义"),
                   ("§3","## 3. status 语义","## 4. audit 与 G 门快照"),
                   ("§4","## 4. audit 与 G 门快照","## 5. 自检文件"),
                   ("§5","## 5. 自检文件","## 6. 独立复核命令")):
    print(name, base[base.index(a):base.index(b)] == t[t.index(a):t.index(b)])
EOF
```

**实测结果**：`§1 True · §2 True · §3 True · §4 True · §5 True`（五段全 Identical）。

> 代价与取舍：契约正文里提到的 `references/evidence-audit.md` 与 `references/quality-gates.md`
> 在 v6 里已被合并（见 `SKILL.md` §11）。为了保持**可逐字比对**，正文里的名字**没有就地改**，
> 而是在文件末尾新增 `§9 v6 文件合并对本契约正文引用的影响` 一张映射表。
> 这样"字段块逐字保留"这条硬门是可机器验证的，而不是靠承诺。

### 14.2 能力未丢（入口 + flag 双口径）

```bash
# 入口：基线 14 个 scripts/*.py 在本包里必须都还在，且都能 import
# flag：基线 main.py 的 7 个 + make_synthetic_inputs.py 的 4 个（合计 11 处）必须都还在
```

**实测结果**：

| 口径 | 基线 | v6 |
|-|-|-|
| `scripts/*.py` 入口 | 14 | **17**（多出 `fault_inject.py` / `check_status_matrix.py` / `gain_ab.py`，无缺失） |
| 基线 flag | `main.py` 7 个 + `make_synthetic_inputs.py` 4 个 | **11/11 全在**，参数名与默认值未改 |
| 14 个基线入口可 import | — | **14/14 OK**（用 `-B` 与 `PYTHONDONTWRITEBYTECODE=1` 跑，避免污染包内产生 `__pycache__`） |

### 14.3 本节的边界

- 只验证**存在性、可导入性与契约逐字性**，不验证行为等价（行为由 §3–§13 的实跑记录覆盖）；
- `import` 检查若忘记加 `-B`，会在包内生成 `__pycache__` 而使提交包 FAIL —— 本包已因此踩过一次，
  记录在此以免重犯（`selftest.py --package-check` 的 G10 与 `validate_pkg.py` 都能查出来）。

## 15. 失败注入演练（v4 并入 v6；完整矩阵见 `references/VALIDATION-EVIDENCE.md` 第 I 部）

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --sandbox "<包外空目录>"      # 15 行全跑
python "$SKILL_DIR/scripts/fault_inject.py" --list                      # 只看注入清单
```

**实测 transcript（v6 最终字节，包外沙箱）**：

```
[F00] baseline  无注入（对照组）             exit=0  completed  unc=3  MATCH
[F01] input     case.json 非法 JSON          exit=1  failed     unc=0  MATCH
[F02] input     缺 case_id                   exit=0  partial    unc=4  MATCH
[F03] input     声明材料不在盘上             exit=0  partial    unc=5  MATCH
[F04] input     零材料                       exit=0  partial    unc=5  MATCH
[F05] input     无文本层 PDF（扫描件）       exit=0  partial    unc=4  MATCH
[F06] template  模板路径不存在               exit=0  completed  unc=3  MATCH
[F07] template  模板容器损坏                 exit=0  completed  unc=3  MATCH
[F08] template  模板自带 3 张示例页          exit=0  completed  unc=2  MATCH
[F09] dep       python-pptx 缺失             exit=0  partial    unc=4  MATCH
[F10] dep       Pillow 缺失                  exit=0  partial    unc=5  MATCH
[F11] dep       pypdf 缺失                   exit=0  partial    unc=4  MATCH
[F12] contract  契约块非法 JSON              exit=0  partial    unc=4  MATCH
[F13] contract  空契约 {}                    exit=0  partial    unc=4  MATCH
[F14] contract  多声明 1 个产不出的字段      exit=0  completed  unc=3  MATCH
summary: 15 scenario(s) = 14 injection(s) + 1 control, 15 MATCH, 0 MISMATCH, 0 silent failure
```

- 采集环境同 §13；模式 `full`（**未**加 `--skip-previews`）；单次耗时 0.52–1.76 s，合计约 19 s。
- **每个数字都是路径无关的**：`unc` 是 `result.json.uncertainty` 的条数，`MATCH` 由四要素齐全性判定，
  因此换一台机器重跑应当一致（差异只应出现在沙箱路径与耗时两处）。
- **v6 与 v4 的这张表逐格相同**（同一脚本、同一判据、同一示例输入）；
  差异仅在 v6 的 `main.py` 另含 Fix 7（本表 15 行都没有触发它 —— 触发条件是
  `derived_pages >= content_pages` 且主张 ≥3，示例案例不满足）。
