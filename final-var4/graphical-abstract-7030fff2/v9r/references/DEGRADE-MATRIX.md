# DEGRADE-MATRIX.md — 缺依赖降级链实测（含「最小可用环境」清单）

> 本文件回答 README 里那句"matplotlib / Pillow / pypdf 都是可选的"到底意味着什么：
> **缺了它，产物还剩什么、`status` 变成什么、还写不写 `result.json`、退出码是多少。**
> 全部数字来自 `scripts/degrade_probe.py` 在**包外临时副本**上的真实运行
> （Windows / Python 3.13.9，2026-11-23，12 个场景 × 每个一次真实出图，合计 39.6 s）；
> 机器可读原件见 [`../examples/degrade_matrix.example.json`](../examples/degrade_matrix.example.json)。

---

## 1. 拦截方法（受控、可复核、不动本机环境）

| 目标 | 手段 | 证据 |
|-|-|-|
| 缺某个 Python 库 | 在 `<out>/_shim/scn_<ID>/<mod>/__init__.py` 写一个**只做两件事**的假包：向 `GA_DEGRADE_LOG` 追加一行 `import-attempt: <mod>`，然后 `raise ImportError`；把该目录前置到子进程 `PYTHONPATH` | 报告的 `shim_hits[]`（真的被 import 过才有记录）+ 本机 `site-packages` 未被改动 |
| 缺 LibreOffice CLI | `PATH` 前置 `<out>/_shim/bin/{soffice,libreoffice}[.cmd]`，命中即落日志并 `exit 127` | 同上（本机**确实没装** LibreOffice，P10 是真实状态而非模拟） |
| 产物形态 | 每个场景独立工作目录 + 独立子进程 `python -B <sandbox>/scripts/main.py --case … --out …` | 报告 `scenarios[].stdout_head / exit` |

关键细节：**每个场景一个 shim 目录，只放它自己要拦的模块**。首版把六个模块塞进同一个目录，
结果"只拦 pptx"的场景里 matplotlib 也一起消失了 —— 这个 bug 是被 `shim_hits`
（`import-attempt: matplotlib` 出现在 P01）当场抓出来的，随后才改成逐场景隔离。

---

## 2. 判级口径

| 判定 | 含义 |
|-|-|
| `ok` | 预先写下的期望全部满足 |
| `mismatch` | 期望未满足，但降级被记录（`uncertainty`/`warnings` 有说明） |
| `silent` | 实测到**能力丢失**（后端降级 / PDF 不可用 / PDF 材料不可读），而 `status=success` 且 `uncertainty` 与 `warnings` **都为空** |
| `crash` | 没跑出 `result.json` |

另外两条硬性期望：**降级必须留痕**（`record_if_degraded`）、
**PDF 缺席必须有 `reason`**（`pdf_reason_required`，与 `failure-modes.md` D12 一致）。

---

## 3. 逐场景实测（12 个场景）

命令：`python "$SKILL_DIR/scripts/degrade_probe.py" --out /tmp/dg --fail-on strict`
（基础案例 `examples/case.json`；P07 的材料换成运行时生成的一页真实 PDF）

| # | 拦截 | PNG 后端 | status | SVG | PNG | PDF（reason） | unc/warn | 降级形态 | 判定 |
|-|-|-|-|-|-|-|-|-|-|-|
| P00 | 无（对照） | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 无 | ok |
| P01 | `pptx` | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 无（命中日志为空） | ok |
| P02 | `PIL` | **`pure-python-png`** | partial | ✅ | ✅ | ❌（有 reason） | 1 / 1 | 连带 matplotlib 失效 → 纯 Python PNG；文字变占位框 | ok |
| P03 | `matplotlib` | **`Pillow`** | partial | ✅ | ✅ | ❌（有 reason） | 1 / 11 | 回退第二级；PDF 预览不可用 | ok |
| P04 | `numpy` | **`Pillow`** | partial | ✅ | ✅ | ❌（有 reason） | 1 / 11 | numpy 是 matplotlib 的**传递**依赖 → 同样掉到第二级 | ok |
| P05 | `yaml` | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 无（命中日志为空） | ok |
| P06 | `pypdf`（材料是 `.md`） | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 无（**该路径根本没被走到**） | ok |
| P07 | `pypdf` + 材料是真实 PDF | `matplotlib` | partial | ✅ | ✅ | ✅ | 2 / 1 | **PDF 材料文本层不可读**：按二进制处理并登记 | ok |
| P08 | `PIL` + `matplotlib` | **`pure-python-png`** | partial | ✅ | ✅ | ❌（有 reason） | 1 / 1 | 两级绘图库都缺 → 保底 PNG | ok |
| P09 | `matplotlib`+`PIL`+`numpy`+`pypdf` | **`pure-python-png`** | partial | ✅ | ✅ | ❌（有 reason） | 1 / 1 | **最小可用环境**（纯标准库） | ok |
| P10 | LibreOffice CLI 不存在 | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 无（命中日志为空） | ok |
| P11 | `pptx` + `yaml` + LibreOffice | `matplotlib` | success | ✅ | ✅ | ✅ | 0 / 0 | 无（命中日志为空） | ok |

**汇总（实测）**：`scenarios 12 / ok 12 / mismatch 0 / silent 0 / crash 0`；
`result_json_written 12 / 12`、`exit_zero 12 / 12`；零影响场景
`P00 P01 P05 P06 P10 P11`。**没有任何一个场景让主链崩掉或丢掉 `result.json`。**

### 3.1 降级时留下的原文（节选，摘自报告 `uncertainty_sample`）

```
P02/P03/P08/P09  matplotlib 渲染不可用，已回退到备用渲染器：ImportError: degrade-probe: <mod> is blocked on purpose
P02/P08/P09      text drawn as placeholder boxes: no imaging library            （render_log.warnings）
P03/P04          element canvas skipped: unknown color specifier: 'none'        （Pillow 后端逐元素告警，11 条）
P07              以下材料文件不是合法 UTF-8，已按替换字符读取（内容可能失真）：material.pdf
P07              材料是二进制文件，未发现文本层或不可读：material.pdf（未取得可读文本层，相关数值一律不上画布）
```

PDF 缺席时 `deliverables[format=pdf].reason` 的实测值：

```
renderer backend 'Pillow' provides no vector PDF preview
renderer backend 'pure-python-png' provides no vector PDF preview
```

---

## 4. 发现并修好的 1 处"不可见降级"

首轮实测里 P03 / P08 / P09 判 `mismatch`，原因完全相同：

| 项目 | 修复前 | 修复后 |
|-|-|-|
| `deliverables[format=pdf]` | `{"path": null, "present": false, "reason": null}` | `{"path": null, "present": false, "reason": "renderer backend 'Pillow' provides no vector PDF preview"}` |
| `failure-modes.md` D12 的承诺 | 写了"PDF 不可用 → `present:false` + reason" | 与实现一致 |
| 受影响场景 | P02 / P03 / P04 / P08 / P09（凡是没用上 matplotlib 的） | 全部 ok |

**修复（纯增量，`scripts/main.py` **净 +6 行**（在既有 `if/elif` 链上新增 1 个 `elif` 分支：4 行代码 + 2 行注释；无删改））**：在"PDF 路径已请求但没有渲染报告"的
分支上补一个 `reason`，把当时实际使用的后端名写进去。CLI 参数、退出码、其余语义未动。
回归：`fault_inject.py --fail-on strict` 仍 **exit 0 / 0 静默**，`contract_matrix.py` 仍 **26/26 ok**。

---

## 5. 「最小可用环境」清单（由 P09 实测得出）

| 能力 | 纯标准库（无第三方包） | 需要什么才能更好 |
|-|-|-|
| 可编辑分层 SVG（7 层 `layer:*`、真 `<text>`、`data-src`） | ✅ 产出 | —— |
| PNG 预览 | ✅ 产出（后端 `pure-python-png`，zlib+struct 手写） | `Pillow`：位图文字；`matplotlib`：抗锯齿 + 真字形 |
| 文字可读性 | ⚠️ **退化为占位框**（`render_log.warnings` 明说） | 系统字体 + Pillow 或 matplotlib |
| PDF 矢量预览 | ❌ 不产出（`present:false` + **reason**） | `matplotlib` 的 PDF 后端 |
| `result.json`（契约全字段 + 审计） | ✅ 产出（顶层 **26 键**） | —— |
| PDF **材料**的文本层 | ❌ 不可读（登记为二进制材料） | `pypdf` |
| 退出码 / `status` | `0` / `partial`（限制已列明） | 完整环境下是 `success` |

**结论**：这个 Skill 的**最小可用环境 = Python 3.9+ 标准库**；
`matplotlib` 只影响"抗锯齿位图 + 矢量 PDF"，`Pillow` 只影响文字渲染质量，
`pypdf` 只在材料是 PDF 时才被用到。

---

## 6. 静态依赖面 vs 运行时命中（两个独立证据）

报告 `import_sites` 给出**流水线**（不含本包自带的验证工具）的导入点统计：

| 依赖 | 流水线导入点 | 命中位置 | 工具脚本导入点 | 本次实测命中日志 |
|-|-|-|-|-|
| `matplotlib` | **5** | `preview.py:45/68/70/71/72` | 3 | P02/P03/P04/P08/P09 有 |
| `PIL` | **1** | `preview.py:161` | 0 | P02/P08/P09 有 |
| `pypdf` | **1** | `extract.py:390` | 0 | P06/P07 有（P06 是"没走到"） |
| `numpy` | **0** | —— | 0 | P04 有（**传递依赖**：matplotlib 内部 import numpy） |
| `yaml` | **0** | —— | 0 | 无 |
| `pptx` | **0** | —— | 0 | 无 |
| LibreOffice CLI | **0** | —— | 7（只在本探测脚本自己的文案里） | 无 |

两个证据分开读才有意义：**静态 0 导入点**说明代码里没有这条边（`pptx`/`yaml`/LibreOffice）；
**静态 0 但运行时命中**说明它是传递依赖（`numpy` → matplotlib），
"我的代码没 import 它"并不等于"缺了它没影响"。这正是本轴要暴露的东西。

---

## 7. 可用性结论（哪些功能彻底不可用）

| 缺什么 | 彻底不可用的功能 | 仍然可用的部分 |
|-|-|-|
| `matplotlib` | 矢量 **PDF** 预览；抗锯齿位图 | SVG、PNG（Pillow 或纯 Python）、`result.json`、审计 |
| `Pillow` **且** `matplotlib` | 真实字形渲染（文字变占位框） | 几何、SVG 文本仍可编辑、PNG（纯 Python）、`result.json` |
| `numpy` | 同 `matplotlib`（传递依赖） | 同上 |
| `pypdf` | PDF **材料**的文本层 | 材料为非 PDF 时无影响；PDF 材料会被登记为不可读 |
| `python-pptx` / `yaml` / LibreOffice CLI | **无**（本 Skill 不使用） | 一切照常（三个场景实测零影响） |

---

## 8. 未覆盖声明

1. **字体文件缺失**：本机系统字体真实存在，无法用导入拦截模拟"字体全没了"；
   只能间接观测（P08/P09 的占位框 + `render_log.font`）。
2. **版本不兼容**：只模拟 `ImportError`；"装了但导入时抛别的异常 / ABI 不匹配"未测。
3. **平台侧**：容器里没有 Python 解释器、磁盘满、`--out` 只读挂载等不在本矩阵
   （`--out` 指向普通文件这一条由 `fault_inject.py` F17 覆盖，退出码 2）。
4. **并发**：场景串行执行；并发缺库/并发写同一目录未测。
5. **网络型依赖**：本 Skill 不访问网络，故无此项。

---

## 9. 怎么复跑

```bash
# 全量（约 40 s，12 次真实出图）
python "$SKILL_DIR/scripts/degrade_probe.py" --out /tmp/dg --fail-on strict

# 单场景 + 保留沙箱（可直接进去看 shim 与实际产物）
python "$SKILL_DIR/scripts/degrade_probe.py" --out /tmp/dg --only P09 --keep --verbose

# 只采数据（永远 exit 0）
python "$SKILL_DIR/scripts/degrade_probe.py" --out /tmp/dg --fail-on none
```

退出码：`0` = 达到等级；`1` = 未达到；`2` = 用法/环境错误。
`--out` 必须在包外；脚本先把 `scripts/` 复制到 `<out>/_skill/`，**包内不落任何文件**。
