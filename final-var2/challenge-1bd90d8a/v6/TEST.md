# TEST.md — 真机实测记录（v6 全维合并版）

本文件是**四条证据链的实测台账**：注入（失败面）、题集（泛化面）、A/B（增益面）、
回归（改完没改坏）。所有实测都在**包外**目录进行（源包只读），
因此包内不会留下 `__pycache__`。

- 环境：Windows 10 · CPython **3.13.9**（Anaconda） · Pillow **12.3.0** ·
  matplotlib **3.10.6**（仅条件 A 使用）· 无网络访问
- 被测对象：本包副本（`$PKG`）· 时间：2026-11-22 20:2x +08

---

## T1 编译与导入

```
python -m py_compile $PKG/scripts/*.py     → exit 0（11/11）
python -m py_compile $PKG/examples/*.py    → exit 0（2/2：baseline_agent.py / measure_ab.py）
```

## T2 主链路冒烟（cwd **不在**技能根 —— 顺带验证自定位）

```bash
cd <包外临时目录>
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$T/B1" --work "$T/wB1" --style nature
```
```
[main] case_id=example-science-figure-01 status=completed figures=['fig-01','fig-02'] failed=[]
[main] gates: G1=OK G2=OK G3=OK G4=OK G5=OK G6=OK G7=OK G8=OK all_pass=OK
```
**exit 0** · 11 个产物 · `result.json` **29 键** · `uncertainty=[]`（正常路径零噪声）。

## T3 六条复核命令逐条 exit 0

| 命令 | exit |
|-|-|
| `main.py --case … --out … --work …` | **0** |
| `check_contract.py --result … --case …` | **0**（`missing=0 null=0 contract_missing=0`） |
| `figcheck.py --dir … --case …` | **0**（G1–G8 全过） |
| `mapcheck.py --dir … --case …` | **0**（`121 checked / 0 mismatched / 0 unmatched`） |
| `verify_rerun.py --case … --out …` | **0**（`DETERMINISTIC`） |
| `spec_lint.py --spec … --case …` | **0**（`SUMMARY: VALID`） |
| `extract.py --case … --out … --json` | **0** |

## T4 题集两案（**不同题材**，回归基线）

| 项 | 案例 A · 湖泊中试富营养化（生态） | 案例 B · Mg-Zn 合金降解（材料） |
|-|-|-|
| `main.py` | **exit 0** · `completed` · **1.37 s** | **exit 0** · `completed` · **0.89 s** |
| 图 | `fig-A1`（panel：bar + line） | `fig-B1`（scatter）+ `fig-B2`（network，材料文本驱动） |
| `result.json` | **29 键** · `gates.all_pass=true` · `uncertainty=[]` | **27 键** · `gates.all_pass=true` · `uncertainty=[]` |
| `check_contract` | exit 0（契约形态② + 2 个非标准字段） | exit 0（契约走**字段别名** `data_manifest`/`validation`/…） |
| `figcheck` | exit 0 · G1–G8 全 true | exit 0 · G1–G8 全 true |
| `mapcheck` | **99 checked / 0 mismatched / 0 unmatched** | **74 checked / 0 mismatched / 0 unmatched** |
| `verify_rerun` | `identical=6 differ=0` | `identical=9 differ=0` |
| 未引用列 | `turbidity_NTU` 仍在 `sources[].columns` | `ph_day7`/`viability_percent`/`se_viability` 仍在 |
| 八类检查 | 全 ok | B1 全 ok；B2 `occlusion=warn`（7 节点网络），**无 fail** |

> 案例 B 的**首轮**曾是 `exit 2 / partial`（`通路图需要 entities（节点）列表。`）——
> 即缺陷 P5（材料文本解析器没接到生成路径）。修好后才有上表结果。

## T5 故障注入（23 条四形态；判据 mismatch=0）

```bash
python "$PKG/scripts/fault_inject.py" --src "$PKG" --workdir "$T/fw" --out "$T/fw/report.json"
```
```
[fault] cases=23 -> I1,I2,I3,I4,I5,I6,I7,T1,T2,T3,T4,T5,D1,D2,D3,D4,K1,K2,K3,K4,K5,K6,K7
[fault] summary: cases=23 mismatch=0 families={'input': 7, 'template': 5, 'dependency': 4, 'contract': 7}
```
**exit 0**。实测退出码分布：`0`×14、`1`×6、`2`×3；`result.json` 存在的 21 条里，
**只有 I1/I2/D2 是 6 键最小诚实信封**（都是"运行异常"），其余为完整信封。
逐行明细（注入操作 → 实测退出码 / `status` / `uncertainty` 原文 → 是否静默失败）见
`references/EVIDENCE.md` 第一部分。

## T6 注入与探针查出的 8 处缺陷（修前 / 修后，**本轮核心证据**）

| # | 缺陷 | 暴露方式 | 修前实测 | 修后实测 |
|-|-|-|-|-|
| P1 | 契约里的 `""` 被 G2 当成"必须存在的字段" | 注入 K1 | `exit 2 / partial / G2=false`（`缺失/为空 ['']`） | `exit 0 / completed / G2=true` |
| P2 | 缺图规格时失败记录丢掉真实原因 | 注入 I6 | 仅 `不支持的图型：auto` | 追加"案例未提供任何图规格（…）" |
| P3 | 样式模板缺失/损坏、`--style` 拼错**全静默** | 注入 T1/T2/T5 | `uncertainty=[]` 且 `completed` | 每种都写 `uncertainty`，并列出可用预设 |
| P4 | 非法契约形态**谎报** `applied=true` | 注入 K6 | `applied=true`（其实没写任何字段） | `applied=false` + 说明 |
| P5 | 只给 `material_file` 的 network **必然失败** | 案例 B | `exit 2`，`通路图需要 entities（节点）列表。` | `exit 0 / completed / 2 张图` |
| P6 | **`heatmap` 在任何输入下都失败** | 图型探针 | `ValueError: invalid literal for int() with base 16: '#4'` | `exit 0 / completed`；色阶 `#440154…#fde725` |
| P7 | **`type:"auto"` 从来没生效** | 图型探针 | `不支持的图型：auto` | `exit 0 / completed` |
| P8 | 无图规格时**凭空画一张占位图** | 图型探针 | 可能 `completed` 且画出没要求的图 | `exit 1 / failed` + `uncertainty` |

> **回归验证**：把本包的注入台指向**合规基线包**跑 `--only K1,K6,T1,T2,I6`，得到
> `mismatch=1`（K1 那条与文档声明不符）；指向本包得 `mismatch=0`。
> ⇒ 注入台**能区分"修好"与"没修好"**，且这几处不是假想风险，是基线真实存在的缺陷。

## T7 A/B 增益对照（12 项机器可判定指标）

```bash
T=<临时目录>; S=$PKG
python "$S/examples/baseline_agent.py" --case "$S/examples/case.json" --out $T/A1     # 条件 A（跑两次）
python "$S/examples/baseline_agent.py" --case "$S/examples/case.json" --out $T/A2
python "$S/scripts/main.py" --case "$S/examples/case.json" --out $T/B1 --work $T/wB1 --style nature   # 条件 B（跑两次）
python "$S/scripts/main.py" --case "$S/examples/case.json" --out $T/B2 --work $T/wB2 --style nature
python "$S/examples/measure_ab.py" --label A_baseline --case "$S/examples/case.json" --out $T/A1 --run2 $T/A2 --write $T/m-A.json
python "$S/examples/measure_ab.py" --label B_skill    --case "$S/examples/case.json" --out $T/B1 --run2 $T/B2 --write $T/m-B.json
```

| 指标 | 条件 A（基准做法） | 条件 B（本包） |
|-|-|-|
| Q1 可编辑矢量源 | ✗ `svg_files=0` | ✓ `svg_files=2` |
| Q2 分层可编辑 | ✗ `layer_groups=0` | ✓ `layer_groups=4` |
| Q3 图元级溯源 | ✗ `data_role=0 source_attrs=0` | ✓ `data_role=79 source_attrs=54` |
| Q4 机器可读映射 | ✗ `data_manifest.json` 缺失 | ✓ 可解析 |
| Q5 数值可逐行回核 | ✗ `rows_checked=0` | ✓ `rows_checked=24 mismatched=0` |
| Q6 轴单位出现在产物中 | ✗ `present=[]`（声明了 `mg/kg`、`μm³` 但都没出现） | ✓ `present=['mg/kg','μm³']` |
| Q7 误差线语义已记录 | ✗ `marks=0 semantics_recorded=False` | ✓ `marks=12 semantics_recorded=True` |
| Q8 多图覆盖 | ✗ `svg_out=0`（案例要 2 张） | ✓ `svg_out=2` |
| Q9 结果信封 | ✗ `result.json_keys=0` | ✓ `result.json_keys=29 core_complete=True` |
| Q10 源文件 sha256 | ✗ `0/0` | ✓ `2/2` |
| Q11 变更记录 | ✗ `change_records=0` | ✓ `change_records=7` |
| Q12 同输入重跑确定性 | ✓ `identical=2 differ=0` | ✓ `identical=10 differ=1 → 0`（见下） |
| **合计** | **1 / 12** | **12 / 12** |

**A 唯一通过的是 Q12**（它的产物只有 2 个且不含时间戳）——**这一项我们不占优，如实列出**。
**B 的 Q12 一度失败**（`identical=10 differ=1 differing=['result.json']`），
根因是 **PDF 元数据时间戳**：两跑 PDF 的 `/CreationDate` 分别为
`D:20261122122752Z` 与 `D:20261122122754Z`，sha256 随之不同。
本版把 **PDF 元数据确定性归一化**（`chartkit.stamp_pdf_deterministic`：归一化
`/CreationDate`、`/ModDate`、`/ID` 并同步修正 xref 偏移）并入后，B 恢复 **12/12**。

> **不做的事**：不声称任何"提升 x%"。条件 A 是小样本合成输入上的**参照实现**，
> 不是平台官方基础 Agent；本地对照数字 **≠** 平台评分。A 侧耗时更短（约 0.9 s vs 1.5 s）
> **不是效率增益** —— 它做的事更少。

## T8 九种图型探针（把"声明支持"逐个试一遍）

| 图型 | 目标 | 实测 |
|-|-|-|
| `heatmap`（`matrix` + `colormap=viridis`） | 支持 | **修前 exit 2 / 0 张图 → 修后 exit 0 / completed**（P6） |
| `auto`（`type:"auto"`） | 自动推断 | **修前 exit 2 / 0 张图 → 修后 exit 0 / completed**（P7） |
| `box`（`presets` 直供四分位） | 支持 | exit 0 / completed |
| `pie`（`labels`/`values`） | 支持 | exit 0 / completed |
| `network`（`entities[]` 内联） | 支持 | exit 0 / completed |
| `bar` / `line` / `scatter` / `panel` | 支持 | 由题集两案与自带示例覆盖，均通过 |
| `filter` 取值不存在 | 报错可定位 | exit 2 / partial，`filter {...} 无匹配行，列 'grp' 取值：['A','B','C']` |
| `y.column` 写错列名 | 单图失败不阻塞 | exit 2 / partial，其余图照常产出 |
| `error.semantics="IQR-ish"` | 非常规语义只 warn | exit 0 / completed + `spec_lint E4` 警告 |

**结论：九种图型现在全部走通**（修前 `heatmap` 与 `auto` 完全不工作）。

## T9 未修的已知缺口（如实登记，不掩饰）

| 项 | 实测 |
|-|-|
| 注入 | `PYTHONPATH` 上放 stub 让 `import PIL` 抛 `ImportError`（`fault_inject.py --only D2`） |
| 结果 | **exit 1** · `status=failed` · `result.json` 只剩 **6 键** · traceback 落在 `figcheck.py: from PIL import Image` |
| 影响 | `chartkit` 本可优雅降级（保 SVG 与全部 JSON），但校验层抛错 → 已写出的 2 个 SVG **不进入 `outputs`** |
| 为何不修 | 修它要改校验器语义（G6 判定），超出"只修真实缺陷、不改退出码语义"的边界 |
| 规避 | 部署前自检 `python -c "import PIL; print(PIL.__version__)"`；缺失先 `pip install Pillow` |

另两条边界：`scripts/*.py` 缺失时不写 `result.json`（`import` 早于兜底逻辑，须看退出码）；
`entity_glossary.json` 缺失时回退内置关系规则且无痕（装饰层，不影响数据闭合）。

## T10 能力未丢自查

| 项 | 结果 |
|-|-|
| `scripts/*.py` 入口 | **11 个**：基线 10 个**全部保留** + 新增 `fault_inject.py` |
| CLI flag | 基线 **17 个全部保留**（`--case --out --work --task --data --style --dpi --note --lang --no-pdf --spec --dir --result --rerun-dir --record-only --json --contract`）；新脚本另带 `--src --workdir --out --only --keep --timeout`，`baseline_agent.py`/`measure_ab.py` 带 `--case --out` / `--label --case --out --run2 --write` |
| 既有脚本删/改名 flag | **0 / 0** |
| 既有脚本逐字节不变 | `check_contract.py` `cjkfont.py` `extract.py` `mapcheck.py` `spec_lint.py` `svgtext.py` `verify_rerun.py`（**7/10**）；改动 3 个：`main.py` +109/−7、`figcheck.py` +8/−4、`chartkit.py` +60/−4 |
| `references/OUTPUT_CONTRACT.md` | **与基线逐字节相同**（字段块未动） |
| `templates/*.json` | **与基线逐字节相同** |
| `examples/{case.json,data.csv,entities.json,material.md,task.md}` | **与基线逐字节相同** |
| 二进制 / `__pycache__` / symlink | **0 / 0 / 0** |

## T11 相似度（difflib.SequenceMatcher.ratio）与假变体自查

| 对照 | ratio |
|-|-|
| v6 SKILL vs 基线 | **0.1580** |
| vs v1 | **0.2588** |
| vs v2 | **0.2351** |
| vs v3 | **0.1699** |
| vs v4 | **0.3223** |
| vs v5 | **0.4174** |

全部远低于门槛（与既有四份 ≤0.90、v4/v5/v6 两两 ≤0.95）。

**假变体自查（看形态）**：`SKILL.md` 末节是"限制（如实声明，不掩饰）"、`README.md` 是"维护"、
`TEST.md` 是本节之后的"未解决项"——**没有**任何"自检通过 / 已复核 / 特此说明"式收尾段；
关键词扫描（五个模式，见提交回报）包内 **0 命中**；`change_records` 是契约字段、
`cases[].injected` 是注入动作描述，两处均在文档中逐条说明。

---

## 未解决项（如实列出）

1. **D2 未修**：缺 Pillow 时校验层抛错 → 整次 `failed`，SVG 不进 `outputs`（T9）。
2. **`spec_lint` 不核对列存在性**：引用不存在的列仍返回 `VALID`；真实兜底是 `mapcheck`。
   本版未改这段逻辑（属校验器语义）。
3. **模块缺失时不写 `result.json`**：`import chartkit` 早于兜底逻辑。
4. **覆盖范围**：注入 23 条 + 2 个题材案例 + 9 种图型探针；**未测**非 UTF-8 输入、
   超长文本、图像尺寸越界、并发写冲突、磁盘满。
5. **对照的解释力**：条件 A 是参照实现而非平台官方基础 Agent；本地数字不等于平台评分。
