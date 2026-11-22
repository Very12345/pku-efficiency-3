# FAULT-MATRIX.md — 四形态故障注入矩阵（逐行实测）

本文件是 `scripts/fault_inject.py` 的**对照表**。每一行都是**真跑出来的**：
注入 → 跑主流程 → 记退出码 / `result.json` 是否存在 / `status` / `uncertainty` 实际内容 /
是否**静默失败**（出了问题却报 `completed`，或出了问题却一个字都不记）。

> **为什么需要它**：`references/failure-modes.md` 写了"该怎么处置"，`references/audit-rules.md`
> 写了"该怎么查"——但那是**声明**。本文件回答的是另一件事：**这些声明到底被代码兑现了没有**。
> 口径只有一条：**声明不算证据，注入 + 重跑的输出才算。**

---

## 0. 怎么复跑（每次改包都必须重跑）

```bash
# 在被测包的**副本**上跑（本脚本自己会复制，源包只读）
python "$SKILL_DIR/scripts/fault_inject.py" \
       --src "$SKILL_DIR" \
       --workdir /tmp/fault-work \
       --out /tmp/fault-work/report.json
# 定点复核单条
python "$SKILL_DIR/scripts/fault_inject.py" --src "$SKILL_DIR" --only K1 --keep
```

- 退出码：`0` = 全部用例"实测 == 期望"；`2` = 有对不上的（`report.summary.mismatches` 会列出编号）；
  `1` = 用法错误。
- 脚本对**每一条**都新建独立包副本，注入只发生在副本里；跑完默认删副本，只留 `out/` 快照。
  因此**包内不会产生 `__pycache__`**（那是打包预检硬门）。
- 主流程一律以 `cwd = 包外临时目录` 启动 —— 这同时把 `SKILL.md` 的"自定位"声明也测了。

**本轮实测基线**（2026-11-22 19:55 +08 / CPython 3.13.9 / Pillow 12.3.0 / 无网络）：

```
[fault] cases=23 -> I1,I2,I3,I4,I5,I6,I7,T1,T2,T3,T4,T5,D1,D2,D3,D4,K1,K2,K3,K4,K5,K6,K7
[fault] summary: cases=23 mismatch=0
        families={'input': 7, 'template': 5, 'dependency': 4, 'contract': 7}
```

23 条用例、**0 条与期望不符**。但"与期望相符"不等于"包没问题"——期望本身是按**修好之后**
的行为写的；下面 §5 如实列出注入与探针**暴露出来的 8 个真实缺陷**（P1–P8）及其处置，
外加 1 个**未修**的韧性缺口（D2）与 3 条已知边界（N1–N3）。

---

## 1. I 族 · 输入形态（case.json / 源数据表）

| # | 注入什么（确实弄坏的操作） | 期望行为 | 实测 exit | result.json | status | uncertainty / error（实测原文节选） | 静默失败？ |
|-|-|-|-|-|-|-|-|
| **I1** | 删除 `examples/case.json` | 写最小诚实信封，退出 1 | **1** | 有（**6 键**） | `failed` | `error=FileNotFoundError: [Errno 2] No such file or directory: '.../case.json'`；`uncertainty=["运行异常，产物不完整。","traceback: ..."]` | **否** ✅ |
| **I2** | 把 case.json 重写成非法 JSON（尾随逗号） | 同上，错误信息要指明解析失败 | **1** | 有（6 键） | `failed` | `error=JSONDecodeError: Illegal trailing comma before end of object: line 1 column 63 (char 62)` | **否** ✅ |
| **I3** | 删除源数据表 `examples/data.csv` | 数值图失败、机制图照常；退出 2 | **2** | 有（**30 键**） | `partial` | `"未发现任何可用源数据文件（data_files/显式 --data/案例同目录表格均缺失）。无法生成数据图。"` + `"以下图未能生成：[{"figure_id": "fig-01", "error": "图 fig-01：源数据为空。"}]"`；产出 3 个图文件（仅 fig-02 的 svg/png/pdf） | **否** ✅ |
| **I4** | 把 data.csv 清空成 0 字节 | 同上（存在但无表头） | **2** | 有（30 键） | `partial` | `"以下图未能生成：[{"figure_id": "fig-01", "error": "数据文件无表头：<abspath>/data.csv"}]"` | **否** ✅ |
| **I5** | 把 case.json 改成 `[原案例, {"case_id":"should-be-ignored","figures":[]}]` | 取第一项，正常完成 | **0** | 有（29 键） | `completed` | `uncertainty=[]` | 否（**正确**）✅ |
| **I6** | 删掉 case.json 里的 `figures`/`figure`/`figure_spec` 三个键（JSON 仍合法） | **不得** completed；也**不得凭空画一张图**；要说清"没有图规格" | **1** | 有（29 键） | `failed` | `uncertainty=["案例未提供任何图规格（figures / figure / figure_spec 均缺）：没有可执行的图规格，按 failed 处理，不臆造图稿。"]`；`completed_figures=[]`、`gates all_pass=false` | **否** ✅（修正 P2/P8 后） |
| **I7** | 把 panel 子图的 `x.column` 改成不存在的 `dose_typo_column` | 该图失败、其余继续；退出 2 | **2** | 有（30 键） | `partial` | `"…折线图 x 列 'dose_typo_column' 无可用数值点。"` | **否** ✅ |

**I 族小结**：7 条里 0 条静默失败。关键两条是 I1/I2（`result.json` **仍然存在**，只是缩成 6 键最小
诚实信封 —— 这比"什么都不写"更有用：下游至少能读到 `status=failed` 与 `error`），以及 I6
（"没有图"必须走到 `partial` 而不是 `completed`）。

---

## 2. T 族 · 模板形态（templates/*.json、样式预设名）

| # | 注入什么 | 期望行为 | 实测 exit | result.json | status | uncertainty（实测原文） | 静默失败？ |
|-|-|-|-|-|-|-|-|
| **T1** | 删除 `templates/journal_styles.json` | 回退内置默认样式，继续出图；**但要留痕** | **0** | 有（29 键） | `completed` | `"templates/journal_styles.json 缺失：样式预设回退内置默认（FM-X1）。自定义期刊预设不可用，已按 default 出图。"` | **否** ✅（修正后） |
| **T2** | 把 journal_styles.json 写成 `{ this is not json `（语法坏） | 同上 | **0** | 有（29 键） | `completed` | `"templates/journal_styles.json 无法解析或只有 default 键：样式预设回退内置默认（FM-X1）。当前样式设置可能不是投稿目标期刊的真实预设。"` | **否** ✅（修正后） |
| **T3** | 删除 `templates/entity_glossary.json` | 回退内置关系规则表，机制图照出 | **0** | 有（29 键） | `completed` | `[]`（**无痕**） | **是（有意）**⚠️ 见 §5-N1 |
| **T4** | 删除 `templates/figure_map.schema.json` | 运行期不读它 → 无影响 | **0** | 有（29 键） | `completed` | `[]` | **是，但无害**✅ 见 §5-N2 |
| **T5** | `--style nonexistent-journal`（拼错期刊名） | 回退 default；**要留痕**并列出可用预设 | **0** | 有（29 键） | `completed` | `"--style 'nonexistent-journal' 不是已知预设（可用：['cell','default','minimal','nature','ppt','prism']）：已回退 default。…"` | **否** ✅（修正后） |

**T 族小结**：模板缺失/损坏**都不阻断交付**（这是设计意图：样式是可降级的装饰层，不是科学内容）。
但"不阻断"不等于"可以不说"——注入暴露了两个**全静默**回退（T1/T2/T5），见 §5 P3。

---

## 3. D 族 · 依赖形态（模块 / Pillow / 字体）

| # | 注入什么 | 期望行为 | 实测 exit | result.json | status | 关键证据（实测原文） | 静默失败？ |
|-|-|-|-|-|-|-|-|
| **D1** | 删除 `scripts/chartkit.py` | import 阶段失败，**不产出半成品** | **1** | **不存在** | —（无信封） | stderr `Traceback … import chartkit as fe … ModuleNotFoundError` | **否** ✅（但见 §5-N3） |
| **D2** | 放 `_stubs/PIL/__init__.py` 并置 `PYTHONPATH`，使 `import PIL` 抛 ImportError | 应降级：保 SVG 与全部 JSON，PNG/PDF 记缺失 | **1** | 有（6 键） | `failed` | `error=ImportError: fault_inject: PIL blocked on purpose`；traceback 落在 `figcheck.py: from PIL import Image` | **否，但降级路径没生效** ❌ 见 §5-D2 |
| **D3** | `FONT_PATHS=<空目录>`，使字体探测没有可用目录 | SVG 走回退字体族照常；PNG 若缺 CJK 记 warn | **0** | 有（29 键） | `completed` | `uncertainty=[]`；`environment.fonts` 记录实际发现结果 | 否（系统字体仍在，**这是正确结果**）✅ |
| **D4** | 删除 `scripts/extract.py` | 同 D1 | **1** | **不存在** | —（无信封） | stderr `ModuleNotFoundError`（`import extract as ext_mod`） | **否** ✅（见 §5-N3） |

**D 族小结**：这一族**发现了本轮最重要的一个真缺陷**（D2）。`chartkit` 有 `HAS_PIL` 优雅降级，
但 `figcheck.py` 顶层 `from PIL import Image` 没有保护 —— 于是在"没有 Pillow"的环境里，
链路能画完 SVG/PNG（其实 PNG 也画不了，但 SVG 与全部 JSON 都写出来了），却在**最后一道校验**
抛异常，被 `main.py` 的最外层 `except` 接住，退化成 6 键最小信封：
**已经产出的 2 个 SVG 产物在 `result.json` 里彻底消失**。见 §5-D2 的处置与残留风险。

---

## 4. K 族 · 契约形态（output_contract 四形态 + 无契约 + 非法形态）

| # | 注入什么 | 期望行为 | 实测 exit | result.json | status | 契约相关实测值 | 静默失败？ |
|-|-|-|-|-|-|-|-|
| **K1** | 形态① 列表，混入 `12345` 与 `""` 两个非法项：`["case_id","status",12345,"","uncertainty"]` | 跳过非法项，其余照常回显；G2 仍应通过 | **0** | 有（25 键） | `completed` | `gates.G2=true`；`output_contract_applied=true`；`uncertainty=[]` | **否** ✅（修正后，见 §5 P1） |
| **K2** | 形态② 名称→类型，含未知类型名 `weirdtype` 与 array/object/number/boolean | 未知类型退化为字符串容器；禁 null | **0** | 有（**30 键**） | `completed` | `extra_note=""`、`extra_list=[]`、`extra_obj={}`、`extra_num=0`、`extra_flag=false` | 否 ✅ |
| **K3** | 形态③ 嵌套 `fields` 列表，含非字符串项 `{"oops":1}` | 非字符串项跳过；合法项回显 | **0** | 有（25 键） | `completed` | `sources` 回显为**真实**的 2 条源记录（含 `sha256`/`rows`/`columns`） | 否 ✅ |
| **K4** | 形态④ 嵌套 `fields` 映射，含未知类型 | 四种容器默认值各就各位；禁 null | **0** | 有（29 键） | `completed` | `custom_block={}`、`custom_rows=[]`、`custom_flag=false`、`custom_label=""` | 否 ✅ |
| **K5** | 完全删除 `output_contract` 键（合法输入） | `output_contract_applied=false`，**不臆造**契约字段 | **0** | 有（25 键） | `completed` | `output_contract_applied=false`；键数从 29 降到 25（少 4 个契约专用键） | 否 ✅ |
| **K6** | 把 output_contract 写成**裸字符串** `"case_id,status,outputs"`（四形态之外） | 不参与回显，且**不得谎称已应用** | **0** | 有（25 键） | `completed` | `output_contract_applied=`**`false`**；`uncertainty` 明确写"形态无法解释（str）…" | **否** ✅（修正后，见 §5 P4；修正前**谎报 true**） |
| **K7** | 契约声明本 Skill 不产出的字段 `raw_readme_text` / `video_preview` | 给容器类型空值 + 不编造内容；字段必须存在且非 null | **0** | 有（27 键） | `completed` | `raw_readme_text=""`、`video_preview=[]`（**空而非 null**，也**没有**假造内容） | 否 ✅ |

**K 族小结**：四形态全部被正确解析，**7 条无一产生 `null`**，`case_id` 恒在顶层。
真正的问题不是"没解析"，而是"解析失败时**是否诚实**"——K1 会误判 G2、K6 会谎报 `applied=true`，
两条都在 §5 里改掉了。

---

## 5. 注入暴露出的真实缺陷（8 条已修 + 1 条未修，逐条点名）

> 排序：先 P* 代码增量（已修，附文件/行数/理由），再 D2（未修，只登记），最后 N*（已知边界）。
> P1–P4 由 23 条注入查出；**P5–P8 由图型/材料探针查出**（探针与实测见 `TEST.md` T10；案例见 `references/CASE-SET.md`）。

### P1 · `""` 在契约字段表里被当成"必须存在的字段" → G2 误判失败（**已修**）

- **实测症状**（K1，修正前）：`gates.G2=false`，`figcheck` 明细
  `声明 4 字段，缺失/为空 ['']` → `status` 被 G8 自洽性规则降级为 `partial`、`exit 2`。
- **根因**：`main.apply_output_contract` 在循环里 `continue` 跳过 `""`（不写字段），
  而 `figcheck._contract_fields` 用 `isinstance(f, str)` 判定，`""` **算字符串** →
  被带进"必须存在"清单 → 必然缺。**两处对"什么算契约字段"的定义不一致。**
- **处置**：统一为"**非空字符串才算字段**"。
  - `scripts/main.py` `apply_output_contract`：+7 / −0 行（含注释块），核心是一行归一化
    `fields = [f for f in fields if isinstance(f, str) and f]`
  - `scripts/figcheck.py` `_contract_fields`：+8 / −4 行（docstring + 三处 `and f`）
- **复验**：K1 从 `exit 2 / partial / G2=false` → `exit 0 / completed / G2=true`。

### P2 · 缺图规格时失败记录丢掉真实原因（**已修**）

- **实测症状**（I6，修正前）：`failed_figures[0].error` 只有
  `"不支持的图型：auto"` —— 看这条记录的人会以为"图型写错了"，而**真实原因是案例根本没给图规格**。
- **处置**：`scripts/main.py`
  - `collect_figure_specs`：兜底分支改为"案例本身带图字段时才当单图规格"，否则返回带 `error` 说明的规格；
  - CP4 循环：把 `spec["error"]` 拼进 `failed_figures[].error`（**只追加**，不改既有文案）。
  - 合计 +23 / −2 行（纯增量性质：返回结构、id/type 不变，`status` 与退出码语义不变）。
  - **全包增量总计**（相对基线 `final/challenge-1bd90d8a`，逐文件逐行）：
    `scripts/main.py` **+109 / −7**（P1/P2/P4/P5/P8）、
    `scripts/figcheck.py` **+8 / −4**（P1）、
    `scripts/chartkit.py` **+60 / −4**（P6/P7 + **PDF 元数据确定性归一化**——后者是 R1 阶段
    的增量，本版已并入；没有它 `measure_ab` 的 Q12 会失败：实测两跑 PDF 的
    `/CreationDate` 分别为 `D:20261122122752Z` 与 `D:…54Z`，sha256 随之不同）。
    **新增**两个文件：`scripts/fault_inject.py`、`references/FAULT-MATRIX.md`。
    CLI 参数名、默认值、退出码语义**全部未变**。
- **复验**：I6 的 error 现在同时给出渲染层原因与"案例未提供任何图规格（figures / figure / figure_spec 均缺）"。

### P3 · 样式回退完全静默（**已修**）

- **实测症状**（T1/T2/T5，修正前）：三种情况下 `uncertainty=[]`，`exit 0`、`completed`。
  即"期刊样式没生效"这件事**在任何产物里都查不到** —— 而题面明确要求"留下失败处理记录"。
- **处置**：`scripts/main.py` CP3 段 +21 行：在读样式前探测
  ① 文件是否存在 ② 是否能解析出 `default` 以外的键 ③ `--style` 是否为已知预设；
  任一不满足则追加一条 `uncertainty`（**只追加说明**，样式值、菜单元数据、退出码全不动）。
- **复验**：T1/T2/T5 现在是 `exit 0 / completed / uncertainty=1`，且文案点名了缺失物与可用预设表。
- **注意**：修正后**正常路径仍然是 `uncertainty=[]`**（已实测，见 `TEST.md` T4）。

### P4 · 非法契约形态谎报 `output_contract_applied=true`（**已修**）

- **实测症状**（K6，修正前）：契约是裸字符串 → `apply_output_contract` 一个字段都没写，
  但 `result.json` 里 `output_contract_applied=true`。**这是对下游的直接误导**。
- **处置**：`scripts/main.py` +11 行 / −3 行：只有 `dict` / `list` 且非空才算"已应用"；
  其余如实置 `false` 并写一条 `uncertainty`。
- **复验**：K6 → `output_contract_applied=false` + 明确说明；K1–K4、K7 仍为 `true`（真应用）。

### P5 · 只给 `material_file` 的机制图必然失败（**已修**）

- **实测症状**（由案例集案例 B 暴露，非本轮 23 条之一）：案例 B 的 `fig-B2` 只声明
  `material_file`（材料文本里写 `ENTITY:` / `REL:` 显式行），实测
  `exit 2 / partial`，失败记录 `"通路图需要 entities（节点）列表。"`。
  而 `extract.py`（CP2）**能**正确解析这些行（`extract.json.networks[0].entities` 有 7 个实体、
  7 条关系），`spec_lint` 也放行 —— 卡在**生成路径只认 `entities_file`（JSON）**。
- **根因**：`SKILL.md` S2 与 `references/workorder-field-map.md` 都写明材料文本支持两种显式行，
  但 `main.py` 的 CP4 只实现了 `entities_file` 分支，`material_file` 从未接到渲染路径。
- **处置**：`scripts/main.py` **新增** `elif … spec.get("material_file")` 分支，
  复用 `extract.scan_material_text`（既有解析器）+ `extract._load_glossary`，
  并把 `material.md` 记入 `sources`（含 sha256、`role=material_file`）；词表候选命中时写 `uncertainty`。
  **纯增量**：原 `entities_file` 与 `spec.entities` 两个分支一字未改。
- **复验**：案例 B 从 `exit 2 / partial / 1 张图` → `exit 0 / completed / 2 张图 / G1–G8 全过`。

### P6 · `heatmap` 在任何输入下都必然失败（**已修**）

- **实测症状**（由图型探针暴露）：`{"type":"heatmap","matrix":[[1,2,3],[4,5,6]],"colormap":"viridis"}`
  → `exit 2`，失败记录 `ValueError: invalid literal for int() with base 16: '#4'`。
- **根因**：`chartkit.heat_color()` 插值那一行**三处**同时写错：
  ① 通道切片 `c0[j:j+2]`（j=0,2,4）在 j=0 时取到**带井号**的 `"#4"` → `int("#4",16)` 直接 ValueError；
  ② 井号被写在**每次迭代**的 f-string 里 → 即使修好①也会拼出 `"#44#01#54"` 这种非法色值
  （PIL 报 `unknown color specifier`）；
  ③ 插值结果 `f` 是浮点，`format(…,"02x")` 只接受整数 → `Unknown format code 'x' for object of type 'float'`。
- **处置**：`scripts/chartkit.py` 改 1 行（含注释），正确写法 = 井号只加一次 + 跳过井号取 6 位十六进制 + 整体取整。
- **复验**：`heat_color(1..6, 1, 6, "viridis")` → `['#440154','#3c4180','#2b778b','#39a77b','#7dcf55','#fde725']`；
  探针用例 `p-heatmap` 从 `exit 2 / partial / 0 张图` → `exit 0 / completed / G1–G8 全过`。

### P7 · `type: "auto"` 从来没生效过（**已修**）

- **实测症状**：`{"type":"auto"}` → `exit 2`，`"不支持的图型：auto（支持 bar/line/…）"`。
  即 `OUTPUT_CONTRACT.md` §6 与 `templates/figure_map.schema.json` 都写明支持的自动推断**不可用**。
- **根因**：`chartkit.infer_type()` 第一行 `t = spec.get("type"); if t: return t` ——
  把显式声明的 `"auto"` **原样返回**，于是 `build_figure_into` 里
  `t = infer_type(spec, rows)` 又拿回 `"auto"`，最终落到"不支持的图型"。
- **处置**：`scripts/chartkit.py` 改为 `if t and str(t).lower() != "auto": return t`（字面量 `auto` 视作未声明）。
- **复验**：探针 `p-auto` 从 `exit 2 / partial / 0 张图` → `exit 0 / completed`。

### P8 · 没有任何图规格时**臆造一张图**（**已修**）

- **实测症状**（I6，在 P7 修好之后暴露）：案例连 `figures` 键都没有时，兜底分支会造一张
  `{"id":"fig","type":"auto"}` 的占位图；P7 让 `auto` 真的会推断，于是这张**案例从未要求的图**
  会被画出来并可能报 `completed` —— 这是**编造产物**，比失败更糟。
- **处置**：`scripts/main.py` 的 `collect_figure_specs` 在"案例完全没有任何图规格"时返回
  **空列表**，并在 CP4 前写一条 `uncertainty`；最终 `status=failed / exit 1`
  （"没有任何图产出"正是 `failed` 的定义，**退出码语义不变**）。
- **复验**：I6 → `exit 1 / failed`，`uncertainty` 点明"案例未提供任何图规格……不臆造图稿"，
  `completed_figures=[]`，磁盘上没有 `figure-*` 文件。

### D2 · Pillow 缺失时**降级路径失效**（**未修，如实登记**）

| 项 | 实测 |
|-|-|
| 注入 | `_stubs/PIL/__init__.py` 抛 `ImportError` + `PYTHONPATH` 指向 `_stubs` |
| 实测 exit | **1**（不是 0） |
| 实测 status | `failed` |
| 实测 result.json | 存在，但只有 **6 键**（`case_id/status/error/uncertainty/sources/change_records`） |
| 实测 stderr | `[main] FATAL ImportError: fault_inject: PIL blocked on purpose` |
| 实测 traceback 落点 | `figcheck.py:162  from PIL import Image` ← **就是这里没保护** |
| 磁盘上实际产物 | **2 个**（两份 SVG 已写出），但 `result.json.outputs=[]`，**映射丢了** |

- **为什么没修**：修它要给 `figcheck.py` 加 PIL 条件导入 + G6 降级分支，属于**改动校验器语义**
  （G6 从"PNG 可打开"变成"PNG 缺失时也算过"）。这与"既有脚本尽量逐字节不变、只修真实缺陷且
  不改退出码语义"的边界相比**越界了**，所以本轮**只登记不修**。
- **已在文档侧兜住**：`references/failure-modes.md` 的 FM-E8 已写明"Pillow 缺失 → 保 SVG 与全部 JSON"，
  **本矩阵明确指出该声明在当前实现下不成立**（只在 `chartkit` 内成立，`figcheck` 处会打断）。
  这是本包**已知且公开的韧性缺口**，不是隐瞒项。
- **运行期规避建议**（写进 `SKILL.md` §6）：部署前先 `python -c "import PIL"` 自检；
  若不可用，先 `pip install Pillow`，或接受 `status=failed` 并在外层记录——**不要**以为会优雅降级。

### N1 · `entity_glossary.json` 缺失时回退无痕（已知边界）

关系规则表缺失 → `chartkit.load_relation_rules()` 回退内置 `_DEFAULT_RELATION_RULES`，
图的**颜色/线型语义**可能与模板预期不同，但 `uncertainty` 为空。
判断：**装饰层回退，不影响"图元↔源数据"闭合**（M1 级证据），且不会产生错误数据，故本轮不改代码，
只在此登记。若下游依赖模板定制的颜色语义，应当把该文件一起带上。

### N2 · `figure_map.schema.json` 缺失完全无影响（已知无害）

该文件**从不被运行时读取**（只作文档/人读），所以删掉它跑出来逐字节一样。
这既是"模板不参与运行"的证据，也提醒：**不要把它当作运行期校验器**（真正的校验器是 `spec_lint`，
而列存在性最终由 `mapcheck` 兜住）。

### N3 · 模块缺失时**不写**最小诚实信封（已知边界）

D1/D4 实测 `result.json` **不存在**。因为 `import chartkit` 发生在 `main.py` 模块顶层，
早于 `main()` 里的 `try/except`，所以最外层兜底逻辑根本没机会执行。
判断：**可以被接受**（进程以 exit 1 明确失败，不会让人误以为成功），但下游不能假设
"只要跑了 main.py 就一定有 result.json"。已在 `README.md` 的"退出码"一节写明。

---

## 6. 静默失败总账（本轮口径）

"静默失败"定义：**出了问题，但 `result.json` 里既没有非空 `error`，也没有相关 `uncertainty`，
且 `status` 仍是 `completed`。**

| 类别 | 修正前 | 修正后 |
|-|-|-|
| 契约（K 族） | K1 误判 G2（降级 partial）、K6 谎报 applied（**1 条静默 + 1 条谎报**） | **0** |
| 模板（T 族） | T1/T2/T5 三条全静默（**3 条**） | **0**（T3/T4 属装饰层或无读取，非缺陷） |
| 输入（I 族） | I6 真实原因丢失 + 可能臆造占位图（**1 条信息丢失 + 1 条编造风险**） | **0**（P2 + P8） |
| 依赖（D 族） | D2 降级路径失效（**1 条，未修**，见上） | **1（登记在案）** |
| 图型（case 探针） | `heatmap` 必然失败、`type:"auto"` 从不生效、`material_file` 机制图必然失败（**3 条能力声明与实现不符**） | **0**（P5/P6/P7） |

⇒ 归纳：**23 条注入 + 3 条图型探针里，修正前有 9 条"查不到原因""说法与事实不符"或"声明的能力压根不工作"；
本轮修掉 8 条（P1–P8），剩 1 条（D2）如实登记为已知缺陷。**

---

## 7. 这张表的边界（不夸大）

1. **只覆盖 23 种注入**，不是全部故障空间：并发写冲突、磁盘满、超长文本、编码非 UTF-8、
   图像尺寸越界等**没有测**。
2. **只测"能否如实报告"，不测"图画得对不对"**（后者另由图型探针覆盖：heatmap/box/pie/auto/inline-network 五个用例） —— 后者由 `mapcheck`/`figcheck` 与
   `references/audit-rules.md` 负责，见 `TEST.md`。
3. **D2 那条说明了一个更普遍的风险**：本包的多处降级（PNG/PDF 缺失、字体缺失）都由
   `chartkit` 兜，但**校验器本身**（`figcheck`）对 Pillow 是硬依赖。凡"校验器依赖某个可选件"
   的地方，都可能出现"产物写出来了、但因为校验器挂了而没被登记"的同类问题。
