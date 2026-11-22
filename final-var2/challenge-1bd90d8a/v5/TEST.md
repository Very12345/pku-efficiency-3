# TEST.md — 真机实测记录（多案例泛化与题集版）

本文件回答两个问题：① 题集两案是否**真的跑通**（不是"应该能跑"）；
② 换题材/换图型之后，**哪里会炸**。所有实测都在**包外**进行（源包只读）。

- 环境：Windows 10 · CPython **3.13.9**（Anaconda） · Pillow **12.3.0** · 无网络访问
- 被测对象：本包副本（`$PKG`）· 时间：2026-11-22 19:5x–20:2x +08

---

## T1 编译与导入

```
python -m py_compile $PKG/scripts/*.py     → exit 0（11/11，含 fault_inject.py）
```

## T2 自带示例冒烟（回归基线）

```bash
cd <包外目录>
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$TMP/out" --work "$TMP/work" --style nature
```
→ **exit 0** · `status=completed` · `gates G1–G8 全 OK` · `result.json` **29 键** · 11 个产物 · `uncertainty=[]`。

## T3 题集案例 A · 湖泊中试富营养化（生态/环境）

```bash
python "$PKG/scripts/main.py" --case "$PKG/examples/cases/lake-eutrophication/case.json" \
       --out "$TMP/outA" --work "$TMP/workA"
```

| 项 | 实测 |
|-|-|
| `main.py` | **exit 0** · `status=completed` · `completed_figures=['fig-A1']` · **1.37 s** |
| `result.json` | **29 键** · `gates.all_pass=true` · `uncertainty=[]` |
| `check_contract.py` | **exit 0** |
| `figcheck.py` | **exit 0** · G1–G8 全 true |
| `mapcheck.py` | **exit 0** · `SUMMARY: ALL PASS (99 checked / 0 mismatched / 0 unmatched)` |
| `verify_rerun.py` | **exit 0** · `DETERMINISTIC (identical=6 differ=0 missing=0)` |
| `spec_lint.py` | **exit 0** · `SUMMARY: VALID (0 errors / 0 warnings / 1 figures)` |
| `sources[0]` | `rows=16`；`columns` **含未被引用的 `turbidity_NTU`** ✅ |
| 八类检查 | `provenance/legend-mapping/axis-units/significance/null-handling/cjk-font/occlusion` 全 **ok** |
| `environment.fonts` | `sans=book antiqua`、`sans_cjk=stfangsong`（CJK 回退链生效） |

## T4 题集案例 B · Mg-Zn 合金体外降解（材料/生物材料）

```bash
python "$PKG/scripts/main.py" --case "$PKG/examples/cases/mg-alloy-degradation/case.json" \
       --out "$TMP/outB" --work "$TMP/workB"
```

| 项 | 实测 |
|-|-|
| `main.py` | **exit 0** · `status=completed` · `completed_figures=['fig-B1','fig-B2']` · **0.89 s** |
| `result.json` | **27 键** · `gates.all_pass=true` · `uncertainty=[]` |
| `check_contract.py` | **exit 0**（契约走**字段别名**：`data_manifest`/`validation`/`editable_sources`/`renders`） |
| `figcheck.py` | **exit 0** · G1–G8 全 true |
| `mapcheck.py` | **exit 0** · `[PASS] fig-B1: 32 elements, 0 orphans` / `[PASS] fig-B2: 42 elements, 0 orphans` → `ALL PASS (74 checked / 0 mismatched / 0 unmatched)` |
| `verify_rerun.py` | **exit 0** · `DETERMINISTIC (identical=9 differ=0 missing=0)` |
| `spec_lint.py` | **exit 0** · `SUMMARY: VALID (0 errors / 0 warnings / 2 figures)` |
| `sources` | `data.csv`（rows=4，8 列全记，含未引用的 `ph_day7`/`viability_percent`/`se_viability`）+ `material.md`（`role=material_file`，含 sha256） ✅ |
| `extract.json` | `networks[0]`：**7 entities / 7 relations**，与 `material.md` 显式行一一对应 |
| `figure_meta['fig-B1'].y_range` | `[0.3895, 0.8405]` → 覆盖 0.41–0.82 且留 ~5% 余量 |
| 八类检查 | B1 全 ok；B2 `occlusion=`**`warn`**（7 节点网络标签密集），**无 fail** → G7 仍通过 |

> **注意 T4 的首轮记录**：同一命令在**修复前**是 `exit 2 / status=partial`，
> 失败记录 `通路图需要 entities（节点）列表。` —— 见 T6。

## T5 四形态故障注入台（23 条，回归用）

```bash
python "$PKG/scripts/fault_inject.py" --src "$PKG" --workdir "$TMP/fw" --out "$TMP/fw/report.json"
```
```
[fault] summary: cases=23 mismatch=0 families={'input': 7, 'template': 5, 'dependency': 4, 'contract': 7}
```
**exit 0**。逐行实测（含退出码、`status`、`uncertainty` 原文、是否静默失败）见
`references/FAULT-MATRIX.md`；本条说明改了 P1–P8 之后**没有把已有分支改坏**。

## T6 题集压出来的真实缺陷（修前/修后对照，**这是本版的核心证据**）

| # | 缺陷 | 暴露者 | 修前实测 | 修后实测 | 修法 |
|-|-|-|-|-|-|
| **P5** | network 只给 `material_file` 时必然失败：`extract.py` 能解析 `ENTITY:`/`REL:`（实测 7+7），但**生成路径只认 `entities_file`(JSON)** | **案例 B** | `exit 2 / partial`，`通路图需要 entities（节点）列表。` | `exit 0 / completed / 2 张图 / G1–G8 全过` | `main.py` 新增一个 `elif` 分支，复用 `extract.scan_material_text`（纯增量） |
| **P6** | `heatmap` 在任何输入下都失败：色阶插值那一行**三处**都写错（`int("#4",16)` → ValueError；井号重复 → 非法色值；浮点套 `02x`） | 图型探针 | `exit 2`，`ValueError: invalid literal for int() with base 16: '#4'` | `exit 0 / completed`；`heat_color(1..6,1,6,'viridis')` → `['#440154','#3c4180','#2b778b','#39a77b','#7dcf55','#fde725']` | `chartkit.py` 改 1 行（另：本版把 R1 阶段的 **PDF 元数据确定性归一化** 一并并入 `chartkit.py`，否则 A/B 指标的 Q12 会失败） |
| **P7** | `type: "auto"` 从来没生效：`infer_type` 把字面量 `"auto"` 原样返回 | 图型探针 | `exit 2`，`不支持的图型：auto` | `exit 0 / completed` | `chartkit.py` 改为"`auto` 视作未声明" |
| **P8** | 案例没有任何图规格时会**凭空画一张占位图**（P7 修好后暴露的编造风险） | 图型探针 | 可能报 `completed` 且画出案例没要求的图 | `exit 1 / failed` + `uncertainty`，磁盘无 `figure-*` | `main.py` 兜底改返回空列表 + 写 `uncertainty` |

## T7 九种图型探针（把"声明支持"逐个试一遍）

最小案例在包外临时生成（不入包），逐个跑 `main.py`：

| 探针 | 修前 | 修后 |
|-|-|-|
| `heatmap`（`matrix` + `colormap=viridis`） | exit 2 / **0 张图** | **exit 0 / completed / G1–G8 全过** |
| `auto`（`type:"auto"`） | exit 2 / **0 张图** | **exit 0 / completed** |
| `box`（`presets` 直供四分位） | exit 0 / completed | 同 |
| `pie`（`labels`/`values`） | exit 0 / completed | 同 |
| `network`（`entities[]` 内联） | exit 0 / completed | 同 |
| `bar` / `line` / `scatter` / `panel` | 由案例 A/B 与自带示例覆盖，均通过 | 同 |
| `filter` 无匹配行 | exit 2 / partial，报错列出该列可用取值 | 同（**行为正确**） |
| `y.column` 写错列名 | exit 2 / partial，单图失败其余继续 | 同（**行为正确**） |
| `error.semantics="IQR-ish"` | exit 0 / completed + `spec_lint E4` 警告 | 同（只 warn 不阻断） |

**结论：九种图型现在全部走通**；4 处"文档写了、实现没做"的落差已修（P5–P8）。

## T8 泛化边界实测（会失效的部分）

| 场景 | 实测 |
|-|-|
| 材料文本只有自然语言、没有 `ENTITY:` 行 | 词表命中只记 `uncertain`，**不上图** → 机制图可能为空 |
| 网络图节点密度高（本案 7 节点已 warn） | `occlusion=warn`（不阻断），需在 spec 手给坐标 |
| `filter` 取值不存在 | `exit 2 / partial`，报错含可用取值列表 |
| 缺 Pillow | `exit 1 / failed`，只留 6 键信封，SVG 不进 `outputs`（**未修**） |
| `scripts/*.py` 缺失 | `exit 1`，**无 `result.json`** |
| 非 UTF-8 输入 / 超长文本 / 图像尺寸越界 | **未测** |

完整清单（含"不适用"的统计推断、`matrix` 长表聚合、`box` 四分位不代算等）见
`references/CASE-SET.md` §4。

## T9 能力未丢自查

| 项 | 结果 |
|-|-|
| `scripts/*.py` 入口数 | **11**（基线 10 + `fault_inject.py`；10 个原有入口全在） |
| CLI flag | **17 个既有 flag 全部保留**（`--case --out --work --task --data --style --dpi --note --lang --no-pdf --spec --dir --result --rerun-dir --record-only --json --contract`）+ 新脚本自带 `--src --workdir --only --keep --timeout` |
| 既有脚本删掉/改名 flag | **0 / 0** |
| `references/OUTPUT_CONTRACT.md` | **与基线逐字节相同** |
| `templates/*.json`、`examples/{case.json,data.csv,entities.json,material.md,task.md}` | **与基线逐字节相同** |
| 新增加密文件 | `examples/cases/**`（7）、`references/CASE-SET.md`、`references/FAULT-MATRIX.md`、`scripts/fault_inject.py` |
| 二进制 / `__pycache__` | **0** |

## T10 与既有四份的差异度（difflib.SequenceMatcher.ratio）

| 对照 | ratio |
|-|-|
| 本版 SKILL.md vs 基线 | 0.2078 |
| vs v1 | 0.3305 |
| vs v2 | 0.1992 |
| vs v3 | 0.2942 |

全部远低于 0.90 门槛（本版以"题集压出了什么"开篇，章节骨架与其余各版均不同）。

## T11 假变体自查（看形态）

- 尾部检查：`SKILL.md` 末节是"限制（如实声明，不掩饰）"、`README.md` 是"维护"、
  `TEST.md` 是本节之后的"未解决项"——**没有**任何"自检通过 / 已复核 / 特此说明"式的收尾段。
- 逐文件比对：改动集中在 `scripts/{main.py,figcheck.py,chartkit.py}`（纯增量，逐条记录在
  `references/FAULT-MATRIX.md` §5）、**新增** `scripts/fault_inject.py`、
  `references/{FAULT-MATRIX,CASE-SET}.md`、`examples/cases/**`，
  以及 `SKILL.md`/`README.md`/`TEST.md`/`references/RUBRIC_MAP.md`/`references/failure-modes.md`
  的**整章重写或补写实质章节**——**不是**尾部追加。
- 关键词扫描（五个模式，见提交回报）：包内 **0 命中**。
- 允许出现且逐条说明的两处：`change_records`（`OUTPUT_CONTRACT.md` 定义的**契约字段**）；
  `fault_inject.py` 报告里的 `cases[].injected`（**注入动作描述**，非变更记录段）。

---

## 未解决项（如实列出）

1. **D2 未修**：缺 Pillow 时 `figcheck.py` 顶层 `from PIL` 抛错 → 整次 `failed`，
   已写出的 SVG 不进入 `result.json.outputs`。修它要改校验器语义（G6 判定），越界，
   故只登记 + 给出部署前自检命令。复现：`fault_inject.py --only D2`。
2. **`spec_lint` 不核对列存在性**：引用不存在的列仍返回 `VALID`；真实兜底是 `mapcheck`
   （列不存在必然 mismatch）。本版未改这段逻辑。
3. **模块缺失时不写 `result.json`**（N3）：须同时看退出码。
4. 题集只覆盖 2 个题材 + 9 种图型；非 UTF-8、超长文本、图像尺寸越界、并发写冲突**未测**。
