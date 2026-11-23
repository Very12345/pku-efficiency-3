---
name: academic-talk-organizer-degrade-aware
description: >
  学术汇报内容组织（学术 PPT 页面组织）的**缺依赖可用性**版本：从论文/研究材料到可讲、可编辑、
  证据可追溯的演示文件，并且对"评测机上少装了哪个库"这件事给出**逐项实测的降级形态**。
  当输入包含科研论文材料、研究报告、组会/答辩/评审任务、听众与时长、页数或模板约束、讲稿或备注需求，
  关键词如 学术汇报、答辩PPT、组会汇报、slides、deck、页码规划、讲稿、备注、问答准备、听众适配、
  叙事顺序、汇报内容组织、evidence mapping、模板适配、**缺依赖、降级、python-pptx、Pillow、
  pypdf、LibreOffice、soffice、最小可用环境、导入拦截、优雅降级、partial status** 时使用本 Skill：
  读真实材料 → 抽主线 → 页级计划过计划契约门 P1–P8 → python-pptx 生成可编辑 .pptx（缺则跳过并降级）
  → PIL 预览（缺则跳过）→ 逐字证据审计 → 写含 uncertainty/change_records 的 result.json，
  并用 scripts/degrade_probe.py 以受控导入拦截逐个模拟缺库、实测"还剩什么、status 变什么、
  是否仍写 result.json、退出码是多少"，进而给出「最小可用环境」清单。
  严格以真实文件为准，不臆造数据；包内只含 UTF-8 文本资源，二进制产物运行时生成。
---

# academic-talk-organizer v9 · 缺依赖降级链实测

面向「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35（slides 组）。

## 0. 为什么"降级"要单独做一版

题面把可用性写成了硬要求（`可靠体验 10` 的"异常处理 3 分"）：

> 评价对论文缺图、图表分辨率不足、公式或符号丢失、模板与内容冲突、**字体缺失**、
> **导出失败**、**超时**等情况的识别与处置能力。

而真实评测容器里"哪个库装了、哪个没装"**不由我们决定**。所以 v9 不写"理论上会降级"，
而是给出一张**跑出来的表**：

| 问题 | v9 的答案形式 |
|-|-|
| 缺 `python-pptx` 会怎样？ | 实测：exit 0 / status=partial / **19 个产物** / deck 缺失 / 12 张预览仍在 / `uncertainty` 有专条 |
| 缺 `Pillow` 会怎样？ | 实测：exit 0 / **6 个产物** / 预览 0 张，**并且 deck 也没了**（见 §2 的关键发现） |
| 缺 `matplotlib`/`numpy`/`yaml` 会怎样？ | 实测：**完全 no-op** —— 用 `sys.modules` 证明这些模块**从未被加载** |
| 没有 LibreOffice 会怎样？ | 实测：与完整环境逐项相同（本包不调用它），预览是 PIL 模拟且已如实声明 |
| 最少要装什么？ | 见 §4「最小可用环境」三档：标准库 / +Pillow / +python-pptx（含传递依赖）+Pillow |

## 1. ★ 降级探针：一条命令，12 个配置 + 5 级最小环境

```bash
# $SKILL_DIR = 本包根目录（含 SKILL.md；平台安装后即 /skills/weekly-skill）
SKILL_DIR=/skills/weekly-skill

python "$SKILL_DIR/scripts/degrade_probe.py" \
    --sandbox /tmp/dg --report /tmp/dg/degrade_matrix_report.json
# 期望：probes=12 unreadable=0 unmet=0; ladder=5，退出码 0
```

**它怎么模拟缺库**：在**子进程**的 `sys.meta_path` 上装一个按模块名前缀拒绝导入的拦截器，
然后 `runpy.run_path()` 执行 `scripts/main.py`。拦截只作用于那个子进程，
**不改本机任何已安装包**。退出前子进程把自己加载过的模块清单写成 JSON ⇒
"拦截是否真的生效"由证据说话，不靠自述。

记录每格：`exit_code` · `status` · **产物清单**（还剩哪些文件）· `artifacts.editable_deck` ·
预览 PNG 张数 · 是否写 `result.json` · 依赖相关 `uncertainty` 与 `change_records` ·
`environment` 快照 · 被拦模块是否真的没被加载。

## 2. ★ 三个关键实测发现

### 2.1 缺 Pillow 会**连带**让可编辑 `.pptx` 也产不出来

`python-pptx` 自己声明依赖 `Pillow >=3.3.2`（`importlib.metadata` 实测：
`['Pillow >=3.3.2', 'XlsxWriter >=0.5.7', 'lxml >=3.1.0', 'typing-extensions >=4.9.0']`），
`deck_builder.py` 的顶层 `try: from pptx import ...` 因此失败，整条 deck 路径被判为
"python-pptx 不可用"。

| 格 | 被拦 | `environment` | 产物数 | deck | 预览 PNG |
|-|-|-|-|-|-|
| D-00 对照 | 无 | pptx=1.0.2 / pillow=12.3.0 / pypdf=6.14.2 | **21** | 有 | 12 |
| D-01 | `pptx` | pptx=null | 19 | 无 | 12 |
| D-02 | `PIL` | **pptx=null / pillow=null** | **6** | 无 | **0** |

⇒ 只报"缺 Pillow 则没有预览"是**不完整的**：真正的事实是**可视化产物全线消失**。

### 2.2 只放行顶层模块 `pptx` 不够，传递依赖必须一起在

最小环境阶梯 M-02（只放行 `pptx`）实测 deck 仍无，原因是
`non-whitelisted third-party module lxml blocked`；把传递依赖一起放行（M-04）后立即恢复。
⇒ **"装了 python-pptx" ≠ "能 import python-pptx"**，安装清单必须写全（§4.3）。

### 2.3 `matplotlib` / `numpy` / `yaml` 的降级格子是**纯 no-op**，而且可证

三格的 `sys.modules` 清单里对应模块均为"从未出现"，产物与对照格逐项相同。
把它们记成"降级通过"是错的 —— 正确说法是**本包不依赖它们**。
（这也解释了为什么 `README.md` 的依赖表里它们标着"不需要"。）

## 3. 降级全景（12 个配置实测，全部 exit 0）

| 形态 | 出现于 | 产物数 | 还剩什么 |
|-|-|-|-|
| 完整 | D-00、D-03…D-06、C-01、O-01 | **21 / 19** | `result.json`、`self_check.json`、`talk_plan.json`、`evidence_map.json`、`plan_gates.json`、`evidence_audit.json`、`deck_audit.json`、`editable_deck.pptx`、`previews/`（cover + grid + 12 张 slide PNG + manifest） |
| 缺 pptx（有预览） | D-01、C-01 | 19 | 同上减去 `editable_deck.pptx` 与 `deck_audit.json` |
| 缺 Pillow | D-02、C-02、C-03、O-02 | **6** | 只剩 `result.json`、`self_check.json`、`talk_plan.json`、`evidence_map.json`、`plan_gates.json`、`evidence_audit.json` |

**下界结论**：没有任何一种缺依赖形态能让 `result.json` 消失，也没有任何一格返回非零退出码。
逐配置表与逐格判读见 `references/DEGRADE-MATRIX.md` §2。

## 4. 最小可用环境（三档，均有实测对应格）

### 4.1 只要契约结果

```bash
python "$SKILL_DIR/scripts/main.py" --case <case> --out <out> --quiet
# 实测 M-01（只有标准库）：exit 0；6 个产物；result.json 契约字段齐全；status=partial
```

### 4.2 要预览

```bash
python -m pip install "Pillow>=10"
# 实测 M-03：exit 0；19 个产物；12 张 PNG 预览
```

### 4.3 要完整形态（可编辑 deck + 预览 + PDF 解析）

```bash
python -m pip install "python-pptx>=1.0" "Pillow>=10" "pypdf>=6"
# 实测 M-04/M-05：exit 0；21 个产物；deck + 12 张预览
# 「python-pptx」的传递依赖（缺一就 import 失败）：Pillow / lxml / XlsxWriter / typing-extensions
# 可选且实测为 no-op（不必安装）：matplotlib / numpy / PyYAML
# 可选且本机没有（本包不调用，仅用于人工核对视觉）：LibreOffice / PowerPoint
```

## 5. 主流程与退出码（未变）

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
```

`0` = 已产出通过 validate+contract 的 `result.json`（其 `status` 说明 `completed`/`partial`）；
`1` = 没有可用的契约结果；`2` = 参数用法错误。
**缺依赖属于"诚实降级"，走的是 0 + `status=partial`，不是崩溃。**

## 6. 脚本清单（基线 14 个入口逐一保留，另加 1 个）

| 文件 | 角色 | 作用 |
|-|-|-|
| `scripts/main.py` | build 编排 | 唯一入口；环境预检决定本次能产出哪些产物；CP1–CP5 门控 |
| **`scripts/degrade_probe.py`** | **verify（v9 新增）** | **受控导入拦截 → 12 个缺依赖配置 + 5 级最小环境逐格真跑主流程 → 记录实测降级形态与最小可用环境** |
| `scripts/deck_builder.py` | render | `dependency_status()` 探测 pptx/PIL/pypdf；缺 `python-pptx` 时明确抛错交编排器降级 |
| `scripts/render.py` | render | PIL 模拟预览；`font_status()` 运行时探测系统字体；缺 Pillow 时抛错交编排器降级 |
| `scripts/evidence.py` | extract | 材料加载；缺 `pypdf` 时 PDF 记 `parsed=false` + 原因 |
| `scripts/common.py` · `scaffold_plan.py` · `validate_plan.py` | shared/build/verify | 自定位与 IO · 页级规划 · 计划契约门 P1–P8 |
| `scripts/verify_deck.py` · `validate_result.py` · `check_contract.py` · `evidence_audit.py` · `finalize_result.py` · `selftest.py` | verify | deck 校验 · 结构校验 · 契约校验 · 证据审计 · 结果收口 · 全链路 G1–G10 |
| `scripts/make_synthetic_inputs.py` | assets | 运行时生成示例二进制输入（缺依赖时也会如实报错，不静默） |
| `templates/*` · `assets/*` | assets | 叙事规则 · 计划 schema · result 信封模板 |
| `references/DEGRADE-MATRIX.md` | docs | **v9 轴**：12+5 格逐项实测 + 可用性结论 + 彻底不可用清单 + 最小可用环境 + 未覆盖声明 |
| `references/OUTPUT_CONTRACT.md` · `RUBRIC_MAP.md` · `failure-modes.md` | docs | 契约 · 五维落点 · 失败模式与决策规则 |

**v9 不改任何既有脚本**（三个包中 v8 是唯一改了既有脚本的）。

## 7. 哪些功能彻底不可用（照实说）

| 功能 | 何时彻底不可用 | 实测格 |
|-|-|-|
| 可编辑 `.pptx` | 缺 `python-pptx`；**或**缺 `Pillow`（连带）；**或**缺 `lxml` 等传递依赖 | D-01 / D-02 / M-02 |
| PNG 预览（含逐页缩略图） | 缺 `Pillow` | D-02、C-02、C-03、O-02 |
| Office 真实栅格化（导出保真） | **本机就是不可用**（`shutil.which("soffice")` 与 `"libreoffice"` 均为 None）；本包不调用它 | O-01（与对照格逐项相同） |
| PDF 材料文本解析 | 缺 `pypdf`：退化为"按未解析如实记录" | D-03、C-03 |
| 页计划 / 证据链 / 计划门 / 证据审计 / `result.json` | **没有任何缺依赖形态能让它消失** | M-01（只剩标准库，6 个产物里仍有 `result.json`） |

## 8. 自查清单

- [ ] `degrade_probe.py` 跑过且 exit 0：`probes=12 unreadable=0 unmet=0`、`ladder=5`
- [ ] 报告 `host_dependency_snapshot` 与本机实际一致；`cli_availability.soffice/libreoffice` 照实（本机为 null）
- [ ] `result.json` 里 `status` 与 `artifacts.editable_deck` 一致：deck 为 null 时必须有一条 `deck_limitation` 与一条 `uncertainty`
- [ ] `environment` 如实记录 `python_pptx`/`pillow`/`pypdf`（缺失记 null），`cjk_font` 记录字体探测结果
- [ ] 缺依赖时命令仍返回 0，**没有**把降级报成崩溃
- [ ] 每页（除封面/目录/问答备用页）有 `evidence[0].locator` + 逐字 `quote`
- [ ] 资源形态硬门：只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`；≤50 文件；单文件 ≤500KB；合计 ≤2MB；无符号链接；无 `__pycache__`；无本机绝对路径

## 9. 平台约束（Runtime contract 要点）

平台把 Skill 装到 `/skills/weekly-skill`，在固定 3 案例 × 3 次复跑上运行；
输入 `/input/case.json` + `task.md`，最终产物在 `/app/output`；运行期产物可以是二进制且
**不因 `result.json` 的最终有效性而被丢弃**（本包正是按这条设计的：deck 与预览缺失时
`result.json` 仍然完整有效）；提交资源 ≤50 个 UTF-8 文本文件、单文件 ≤500KB、合计 ≤2MB、
无符号链接；执行预算 64 个模型请求 / 900 秒 / 每响应 16384 token。

> **不要在包内目录里跑脚本**（会生成 `__pycache__`，合规硬门直接拒收）。
> `degrade_probe.py` 会把技能复制到沙箱里、并让被调用的入口也指向沙箱副本。
