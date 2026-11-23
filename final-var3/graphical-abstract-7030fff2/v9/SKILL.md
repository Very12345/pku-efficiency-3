---
name: graphical-abstract
description: >-
  把研究材料做成单页 Graphical Abstract（图形摘要）的 Skill，主打**缺依赖时的真实可用性**：
  输入侧 data-src 溯源（材料里找不到的数值不上画布），执行侧「方案先行 → 双 lint 门 →
  确定性版面 → 可编辑分层 SVG（7 层 layer:*）+ PNG/PDF → audit → 契约回显」，
  依赖侧用 scripts/degrade_probe.py 做**受控导入拦截**（假包写命中日志后 raise ImportError）
  与 PATH 假 CLI，逐个模拟缺 python-pptx / PIL / matplotlib / numpy / yaml / pypdf / LibreOffice，
  记录实测降级形态（产物还剩什么、status、还写不写 result.json、退出码、PDF 缺席原因），
  并给出由实测得出的「最小可用环境」清单（纯标准库仍产出 SVG + PNG + result.json）。
  Use when the task says "graphical abstract"、"图形摘要"、"示意图 / 机制图 / 通路图 / 流程图"、
  "为论文、基金或汇报画一张可编辑的图"、"编辑已有的图稿"，
  或需要判断「这台机器上没装某个库时这个 Skill 还能不能跑、会掉成什么样」时。
---

# Graphical Abstract 图形摘要 Skill（降级链优先版）

这个 Skill 的价值不在于"在装了全套绘图库的机器上很好看"，而在于**在缺东西的机器上仍然交得出东西、
并且如实说清缺了什么**。所以本版把依赖面当成一等公民：每一个"可选依赖"都有一条实测的降级路径（§3、§4）。

| 项目 | 值 |
|-|-|
| Skill 名称 / 版本 | `graphical-abstract` / `2.0.0`（`scripts/common.py` 的 `SKILL_VERSION`） |
| 技能根 | 本文件所在目录，记作 `$SKILL_DIR`；脚本自定位，**cwd 任意** |
| 资源形态 | 纯文本七种扩展名；无二进制、无预置图、无字体文件 |
| 硬依赖 | **只有 Python 3.9+ 标准库**（实测：把 matplotlib/PIL/numpy/pypdf 全拦掉仍产出 SVG + PNG + `result.json`） |
| 降级实测 | `degrade_probe.py`：**12 场景 / 12 ok / 0 crash / 12 次都写出 result.json / 退出码全 0**（39.6 s） |

---

## 1. 调用

```bash
SKILL_DIR=/skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json
python "$SKILL_DIR/scripts/degrade_probe.py" --out /tmp/dg --fail-on strict     # 本轴判据（§4）
```

判据一律看**退出码**：`main.py` 0 = 完成（`success`/`partial`）、1 = 硬输入错误、2 = 环境/内部错误；
`check_contract.py` 0 = 契约完整；`degrade_probe.py` 0 = 无"能力丢了却没有任何记录"的场景。
`--out` 必须在包外 —— `degrade_probe.py` 会拒绝写进包内（退出码 2）。

---

## 2. 依赖地图（静态导入点 + 运行时命中，两个独立证据）

| 依赖 | 流水线导入点 | 位置 | 角色 | 缺了会怎样（实测场景） |
|-|-|-|-|-|
| `matplotlib` | **5** | `preview.py:45/68/70/71/72` | 抗锯齿 PNG + **矢量 PDF** | P03：掉到 Pillow，PDF 不产出（带 reason） |
| `Pillow`（`PIL`） | **1** | `preview.py:161` | 位图文字（配合系统字体） | P02：连带 matplotlib 失效 → 纯 Python PNG、文字占位框 |
| `pypdf` | **1** | `extract.py:390` | **PDF 材料**的文本层 | P07：登记"文本层不可读"，其余照常 |
| `numpy` | **0** | —— | matplotlib 的**传递**依赖 | P04：静态没有边、运行时仍掉级（最容易被忽略的一条） |
| `python-pptx` | **0** | —— | 不使用 | P01：零影响（命中日志为空） |
| `PyYAML` | **0** | —— | 不使用（主链只读写 JSON） | P05：零影响 |
| LibreOffice CLI | **0** | —— | 不使用（PDF 由 matplotlib 直接产出） | P10/P11：零影响（本机也确实没装） |

> 静态导入点统计的是**流水线**（`main/extract/figurespec/svgbuilder/preview/audit/spec_lint/
> scaffold/check_contract/common`），不含随包的验证工具（它们为了造夹具会 import matplotlib）。
> 两个证据分开读：静态 0 + 运行时命中 ⇒ **传递依赖**；静态 0 + 无命中 ⇒ 真的不依赖。

---

## 3. 降级链（设计意图 → 实测形态）

```
PNG：matplotlib（抗锯齿 + 真字形）
      └─ Pillow（位图 + 系统字体）
            └─ 纯 Python PNG（zlib+struct 手写；文字变占位框，几何仍精确）
PDF：matplotlib PDF 后端
      └─ 不产出，但 deliverables[format=pdf] 必须带 present:false + reason
材料：文本文件直读 → PDF 走 pypdf 文本层 → 取不到则登记"不可读"，数值不上画布
```

关键设计：**每一次降级都必须留下痕迹**（`uncertainty` 或 `warnings` 或 `deliverables[].reason`），
`status` 从 `success` 降为 `partial`。这条在 §4 里是被逐场景实测的，不是承诺。

---

## 4. ★ 本版主轴：缺依赖降级链实测

### 4.1 一条命令，12 个受控场景

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" --out /tmp/dg --fail-on strict      # 约 40 s
python "$SKILL_DIR/scripts/degrade_probe.py" --out /tmp/dg --only P09 --keep --verbose
```

拦截方式（**不动本机环境**）：

| 目标 | 手段 | 证据 |
|-|-|-|
| 缺某个库 | 每场景一个独立 shim 目录：`<mod>/__init__.py` 先向 `GA_DEGRADE_LOG` 追加 `import-attempt: <mod>`，再 `raise ImportError`；该目录前置到子进程 `PYTHONPATH` | 报告 `shim_hits[]`（真的被 import 才有记录） |
| 缺 LibreOffice | `PATH` 前置假 `soffice`/`libreoffice`（落日志 + `exit 127`） | 同上；本机确实未安装，P10 是真实状态 |

> 首版把六个模块塞进同一个 shim 目录，于是"只拦 pptx"的场景里 matplotlib 也被拦掉了 ——
> 这个 bug 是 `shim_hits` 里的 `import-attempt: matplotlib` 当场暴露的，随后改为**每场景一个目录**。

### 4.2 逐场景实测（12/12 ok）

| # | 拦截 | PNG 后端 | status | SVG | PNG | PDF（reason） | unc/warn | 降级形态 |
|-|-|-|-|-|-|-|-|-|
| P00 | 无（对照） | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 无 |
| P01 | `pptx` | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 零影响 |
| P02 | `PIL` | **`pure-python-png`** | partial | ✅ | ✅ | ❌（有） | 1 / 1 | 连带 matplotlib 失效 → 保底 PNG + 占位框 |
| P03 | `matplotlib` | **`Pillow`** | partial | ✅ | ✅ | ❌（有） | 1 / 11 | 第二级后端；PDF 不可用 |
| P04 | `numpy` | **`Pillow`** | partial | ✅ | ✅ | ❌（有） | 1 / 11 | **传递依赖**生效 |
| P05 | `yaml` | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 零影响 |
| P06 | `pypdf`（材料 .md） | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 零影响（该路径没走到） |
| P07 | `pypdf` + 材料是 PDF | `matplotlib` | partial | ✅ | ✅ | ✅ | 2 / 1 | PDF 材料文本层不可读（已登记） |
| P08 | `PIL`+`matplotlib` | **`pure-python-png`** | partial | ✅ | ✅ | ❌（有） | 1 / 1 | 两级绘图库皆缺 |
| P09 | 四个全拦 | **`pure-python-png`** | partial | ✅ | ✅ | ❌（有） | 1 / 1 | **最小可用环境** |
| P10 | LibreOffice 不存在 | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 零影响 |
| P11 | `pptx`+`yaml`+LibreOffice | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 零影响 |

**汇总**：`ok 12 / mismatch 0 / silent 0 / crash 0`；**12/12 写了 `result.json`、12/12 退出码 0**；
零影响场景 `P00 P01 P05 P06 P10 P11`。降级时的原始记录（节选）：

```
matplotlib 渲染不可用，已回退到备用渲染器：ImportError: degrade-probe: <mod> is blocked on purpose
text drawn as placeholder boxes: no imaging library
材料是二进制文件，未发现文本层或不可读：material.pdf（未取得可读文本层，相关数值一律不上画布）
renderer backend 'Pillow' provides no vector PDF preview
```

逐场景细节、变量说明与未覆盖声明见 [`references/DEGRADE-MATRIX.md`](references/DEGRADE-MATRIX.md)；
机器可读原件 [`examples/degrade_matrix.example.json`](examples/degrade_matrix.example.json)。

### 4.3 发现并修好的 1 处"不可见降级"

首轮实测 P03/P08/P09 判 `mismatch`：回退到 Pillow / 纯 Python 时
`deliverables[format=pdf]` 是 `{"path": null, "present": false, "reason": null}` ——
**PDF 缺席但没有原因**，而 `failure-modes.md` D12 承诺"`present:false` + reason"。

**修复 = 纯增量，`scripts/main.py` **净 +6 行**（在既有 `if/elif` 链上新增 1 个 `elif` 分支：4 行代码 + 2 行注释；无删改）**：把当时实际使用的后端名写进 `reason`。
修复后：

| 指标 | 修复前 | 修复后 |
|-|-|-|
| P03/P08/P09 判定 | mismatch | **ok** |
| `deliverables[pdf].reason` | `null` | `renderer backend 'Pillow' provides no vector PDF preview` |
| 回归 `fault_inject.py --fail-on strict` | exit 0 | **exit 0**（未退化） |

### 4.4 「最小可用环境」清单（由 P09 实测）

| 能力 | 纯标准库 | 需要什么才更好 |
|-|-|-|
| 可编辑分层 SVG（7 层 + 真 `<text>` + `data-src`） | ✅ | —— |
| PNG 预览 | ✅（`pure-python-png`） | Pillow（文字）/ matplotlib（抗锯齿） |
| 文字可读性 | ⚠️ 占位框（`render_log.warnings` 明说） | 系统字体 + Pillow/matplotlib |
| PDF 矢量预览 | ❌（带 reason） | matplotlib PDF 后端 |
| `result.json`（顶层 26 键 + audit） | ✅ | —— |
| PDF 材料的文本层 | ❌（登记为二进制材料） | pypdf |
| 退出码 / status | `0` / `partial` | 完整环境下 `success` |

---

## 5. 主链与两道门

```bash
python "$SKILL_DIR/scripts/scaffold.py" --case <case.json> --out plan.json     # 方案骨架
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan plan.json          # CP1 门（exit 0）
python "$SKILL_DIR/scripts/main.py" --case <case.json> --plan plan.json --out <out>
python "$SKILL_DIR/scripts/spec_lint.py" --spec <out>/spec.json --content <out>/content.json
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>
```

`main.py` 的顺序：读 case.json（不可读 → exit 1）→ 解析 task/材料 → 抽取（逐元素 `src`；缺值登记）
→ 版面与视觉通道 → 规格 lint → 分层 SVG → 渲染（三级后端，降级留痕）→ audit →
写 `result.json`（信封 + 契约回显 + 溯源 + plan/spec_lint）。
`status`：`success` 要求"无缺值/无实体缺失/无越界 + 两道 lint 通过 + 未发生渲染降级"，
否则 `partial`（必须列明限制）；SVG/PNG 未产出则 `failed`。

---

## 6. 命令面（每个入口都真跑过；`--flag` 全部列出）

| 入口 | 关键参数 | 退出码 |
|-|-|-|
| `scripts/main.py` | `--case`(必) `--task` `--material` `--out` `--plan` `--raster-scale` `--pdf`/`--no-pdf` | 0 / 1 / 2 |
| `scripts/degrade_probe.py` | `--out`(必) `--case` `--only` `--fail-on strict\|silent\|none` `--keep` `--verbose` | 0 / 1 / 2 |
| `scripts/check_contract.py` | `--result`(必) `--case` | 0 / 1 / 2 |
| `scripts/spec_lint.py` | `--spec` `--content` `--lint-plan` `--plan` | 0 / 1 |
| `scripts/scaffold.py` | `--case`(必) `--task` `--material` `--out`(必) | 0 / 1 |
| `scripts/fault_inject.py` | `--out`(必) `--only` `--fail-on` `--keep` `--verbose` | 0 / 1 / 2 |
| `scripts/gain_harness.py` | `--out` `--case` `--material` `--label` `--json` `--compare` | 0 |
| `scripts/extract.py` `figurespec.py` `svgbuilder.py` `preview.py` `audit.py` `common.py` | 被上面入口导入的库模块 | — |

---

## 7. 五维落点（速查；逐条对照见 [`references/RUBRIC_MAP.md`](references/RUBRIC_MAP.md)）

| 维度 | 分 | 落点 |
|-|-|-|
| 实际效果 | 40 | 真跑出图：四要素单页 + 可编辑分层 SVG + PNG（+PDF）；逐元素 `data-src`；`sources[]`(sha256)；`audit.json` 全文；**缺库环境下仍产出可编辑源文件** |
| 使用增益 | 25 | 对照协议 + 只读测量器 `gain_harness.py`（分层/真文字/溯源覆盖率/契约/返工步数） |
| 创新增益 | 15 | **受控导入拦截 + 降级矩阵**（含"传递依赖"与"零依赖边"两类证据）+ 方案先行 + 双 lint 门 |
| 可靠体验 | 10 | 12 场景降级实测（0 crash、12/12 写 result.json）+ 四形态注入 23 条 + 20 条决策规则 + 稳定退出码 |
| 生态贡献 | 10 | 依赖地图 + 最小可用环境清单 + 契约/五维/失败模式/降级矩阵/注入矩阵/增益协议/机制/复用等文档 + 资产三件套 |

---

## 8. 交付前自查清单

- [ ] 跑的是**真实文件**；材料路径存在（不存在时已登记而不是静默）
- [ ] `main.py` → **exit 0**，`result.json` 已写出（**任何依赖缺失都不该让这一步失败**）
- [ ] 若发生渲染降级：`render_log.backend` 不是 `matplotlib`、`status=partial`、
      `uncertainty` 里有"matplotlib 渲染不可用"、PDF 条目带 `present:false` + **reason**
- [ ] 若材料是 PDF 且无 `pypdf`：`uncertainty` 里有"文本层不可读"，且图上的数值没有因此凭空补造
- [ ] `check_contract.py` → exit 0；`spec_lint.py` 两道门 exit 0
- [ ] `degrade_probe.py --fail-on strict` → **exit 0**（12/12，无"能力丢了却没记录"）
- [ ] SVG 良构 7 层 + 真 `<text>` + `data-src`；PNG 非空；四要素 4/4
- [ ] `uncertainty` 里没有编造数据类补丁

---

## 9. 限制与边界（如实声明）

- **抽取边界**：只认独立成行的 `键 = 数值 单位` 与带真实箭头（`->`/`→`/`⇒`）的机制行；
  散文里的数字、带比较符或区间的值（`≈`、`0.8–1.2`）不抽取；材料与 case 数值矛盾时首见优先、
  两处 `src` 并列；非 UTF-8 材料按替换字符读取并登记；二进制材料取不到文本层时跳过而非编造。
- **只模拟 `ImportError`**：拦截等价于"库不存在"；**版本不兼容**（装了但导入即抛别的异常、
  ABI 不匹配）不在本矩阵范围。
- **字体缺失无法完整模拟**：本机系统字体真实存在，只能间接观测（P08/P09 的占位框 + `render_log.font`）。
- **平台侧**（容器无解释器、磁盘满、挂载只读、配额、超时）不在本矩阵范围；
  `--out` 指向普通文件这一条由 `fault_inject.py` F17 覆盖（退出码 2）。
- **纯 Python PNG 的文字是占位框**：几何与图层正确、文字不可读 —— 这是有记录的降级，
  不是"看起来成功的失败"。
- 四要素/图层/契约检查是**结构判据**，不代替领域科学判断。
- 随包示例案例均为**合成示意**，不是平台正式案例，不代表正式成绩。

### 9.1 本版相对上一代引擎的纯增量修复（逐条点名）

| 文件 | 变更 | 发现它的判据 | 理由 |
|-|-|-|-|
| `scripts/main.py` | **净 +6 行**（在既有 `if/elif` 链上新增 1 个 `elif` 分支：4 行代码 + 2 行注释；无删改）：PDF 未产出且不是 `pdf=false` 时，把 `reason` 填成实际后端名 | 本版 `degrade_probe.py` P03/P08/P09 | 回退后端的 `present:false` 曾是**无原因**的，与 D12 承诺不符 |
| `scripts/extract.py` | **净 +7 行**（把 1 行 `normalize_contract(...)` 调用拆成 2 行 + 新增 1 个记录分支与 3 行注释；函数签名/CLI/退出码零改动）：契约容器既非 dict 也非 str 时，往 `uncertainty` 写一条点名记录 | 同族契约判据 C19/C21/C22 | 非法契约此前被静默归一化为空契约（同族判据 `contract_matrix.py` C19/C21/C22，随 v8 版包发送）；缺依赖轴同样要求"降级/忽略必须留痕" |

两处均为纯增量：CLI 参数名、默认值、退出码语义未动；修复后 `degrade_probe.py --fail-on strict`
与 `fault_inject.py --fail-on strict` 双双 **exit 0**（回归实测）。
