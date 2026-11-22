# TEST.md — 本地实测记录（challenge-20870c35 · **v4 失败注入版**）

- 测试时间：2026-11-22 15:37–15:57 +08（Asia/Shanghai）
- 测试机：Windows（Git Bash / MSYS2），Python 3.13.9（Anaconda）
- 被测定版本：本目录全部文件（`scripts/` 14 个 Python 脚本，最后一次 `py_compile` 通过后未再改动）
- 测试方式：把包**复制到一个临时目录**（本机为系统临时盘下的 ASCII 目录）里跑，不在提交目录里跑，避免把运行产物 / `__pycache__` 混进提交资源
- 覆盖：语法编译 / 合成输入再生成 / 主流程 smoke / 独立复核四件套 / 全链路自检 / 双跑确定性 /
  模板适配 / 跳过预览 / cwd 自定位 / **六条降级与失败分支（含负例）** /
  **§13 失败注入演练（15 行 = 14 条注入 + 1 条对照，0 静默失败）**

> 本版与上一版的可执行差异集中在 §13：不是新增正常路径，而是新增**故意把东西弄坏**的演练。
> 那次演练反过来暴露了 3 类真实缺陷（坏模板打死整轮 / 无文本层 PDF 假 parsed /
> 契约解析失败被静默吞掉），已在 `references/FAULT-MATRIX.md` §3 逐条点名，
> 并已按**纯增量**修好 —— 下面 §1–§12 的记录是**修复后**重跑得到的。

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
| `references/plan-contract.md` §5 | `validate_plan.py <out>/talk_plan.json --materials-dir <材料目录>` | 0 | P1–P8 全过 |
| `references/quality-gates.md` §独立复核 | `verify_deck.py … --expect-pages 12 --plan …` | 0 | 见 T3d |
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

## 13. 失败注入演练（T15，v4 新增）

**做法**：把包复制到**包外**沙箱 → 用 `fault_inject.py` 逐条注入故障 → 每条各真跑一次
`scripts/main.py` → 采集「退出码 / `status` / `uncertainty` / `change_records` / 产物落盘」。
**不做**任何"看日志觉得没问题"的判断：判定是四要素齐全性，机器给出 MATCH/MISMATCH 与静默失败标记。

```bash
# 包外目录（示例值）；脚本会拒绝 --sandbox 落在技能包内部
python "$SKILL_DIR/scripts/fault_inject.py" --sandbox "/tmp/ato-fault"
```

**实测汇总**（详细逐条证据见 `references/FAULT-MATRIX.md`）：

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

- 采集环境：Python 3.13.9 / python-pptx 1.0.2 / Pillow 12.3.0 / pypdf 6.14.2 / win32，
  UTC `2026-11-22T11:55:32Z`，模式 `full`（**未**加 `--skip-previews`）。
- 单次耗时 0.52–1.76 s（合计约 19 s）。**耗时不构成性能结论**：每行只跑 1 次。
- `references/FAULT-MATRIX.md` 与本次生成的 `<sandbox>/FAULT-MATRIX.generated.md` 可直接对拍；
  差异只应出现在"沙箱路径"与"耗时"两处。

### 13.1 演练反向暴露并已修的 3 类真实缺陷（修复后本表才是现在这样）

| 缺陷 | 修前实测 | 修后实测 | 落点 |
|-|-|-|-|
| 模板存在但容器损坏 → **打死整轮** | `F07`：`exit=1`、`status=failed`、deck 未生成、traceback 打到 stderr | `exit=0`、`completed`、deck 有、`template_load_error` 进 `change_records` + `uncertainty` | `deck_builder.py` Fix 1 + `main.py` Fix 6 |
| 无文本层 PDF 被记 **`parsed=true`** | `F05`：`parsed=true`、`char_count=15`、`status=completed`（"无文本"被当成成功解析） | `parsed=false` + note 提示先 OCR + `status=partial` | `evidence.py` Fix 2 |
| 契约块不可用时被**静默吞掉** | `F12/F13`：无 `contract` 步、无对应 `uncertainty`、`status` 仍 `completed` | `change_records`(step=`contract`) + `uncertainty` + `status=partial` | `common.py` Fix 3 + `main.py` Fix 5 |
| 契约字段落 **`null`** | `F14`：字段值 `null`、`contract_check` 失败、`exit=1` | 字段值 `""`、`contract_check` 通过、`exit=0` | `common.py` Fix 4 |

**修复属性**：全部为**纯增量**（不改 CLI 参数名/默认值、不改退出码三分语义、不删既有键与分支）；
逐条的 `+/-` 行数与理由见 `references/FAULT-MATRIX.md` §3。
`check_contract.py`、`evidence_audit.py`、`finalize_result.py`、`make_synthetic_inputs.py`、
`render.py`、`scaffold_plan.py`、`selftest.py`、`validate_plan.py`、`validate_result.py`、
`verify_deck.py` **逐字节未变**。

### 13.2 本演练**没有**证明什么（避免过度声称）

1. 注入都在输入/环境侧，**不**改主流程代码 ⇒ 不验证"脚本自身被写坏"的情形；
2. 依赖缺失用**导入遮罩**模拟（抛 `ImportError`），比真实 `ModuleNotFoundError` 更宽；
3. `F10` 的连带效应（Pillow 缺失同时让 python-pptx 不可用）是**实测观察**，
   未做"只缺 Pillow 而 python-pptx 完好"的隔离验证 ⇒ 该行 deck 缺失**不能**单独归因给 Pillow；
4. **未注入**：磁盘写满 / 只读输出目录 / 权限拒绝 / 超时 / 平台 900 秒预算打满 /
   `case.json` 合法但键类型全错 / 超大 PDF —— 这些**没有实测数据**，不作断言；
5. 每行只跑 1 次，耗时是单次观测；`status`/`exit` 是确定性输出，但未用双跑 sha 证明
   （双跑一致性由 §5 的 T4 与 `self_check.determinism` 另行覆盖）；
6. 对照组 `completed` 依赖 prime（自动补齐示例二进制输入）。`--no-prime` 会让 `F00` 回落 `partial`。
