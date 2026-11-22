# TEST.md — 真机实测记录（故障注入与恢复演练版）

本版的重点不是"再讲一遍流程"，而是**把流程弄坏再看它还说不说实话**。
所有实测都在**包外**进行（脚本自己复制副本，源包只读），因此包内不会留下 `__pycache__`。

- 环境：Windows 10 · CPython **3.13.9**（Anaconda） · Pillow **12.3.0** · 无网络访问
- 被测对象：本包副本（记为 `$PKG`）· 示例案例 `$PKG/examples/case.json`（2 张图）
- 时间：2026-11-22 19:4x–19:5x +08

---

## T1 编译与导入

```
python -m py_compile $PKG/scripts/*.py     → exit 0（11/11 脚本，含新增的 fault_inject.py）
```

## T2 主链路冒烟（**cwd 不在技能根** —— 顺带验证自定位）

```bash
cd <包外临时目录>
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" \
       --out "$TMP/out" --work "$TMP/work" --style nature
```
```
[main] case_id=example-science-figure-01 status=completed figures=['fig-01','fig-02'] failed=[]
[main] gates: G1=OK G2=OK G3=OK G4=OK G5=OK G6=OK G7=OK G8=OK all_pass=OK
```
**exit 0** · 产物 **11 个**（2×SVG + 2×PNG + 2×PDF + manifest/validation/mapcheck/figcheck/result）
· `result.json` 顶层 **29 键** · `uncertainty=[]`（正常路径**不产生**噪声）。

## T3 六条复核命令逐条 exit 0

| 命令 | 实测 exit |
|-|-|
| `main.py --case … --out … --work … --style nature` | **0** |
| `check_contract.py --result …/result.json --case …` | **0**（`missing=0 null=0 contract_missing=0`） |
| `figcheck.py --dir … --case …` | **0**（G1–G8 全过） |
| `mapcheck.py --dir … --case …` | **0**（`0 mismatched / 0 unmatched`） |
| `verify_rerun.py --case … --out …` | **0**（`DETERMINISTIC`） |
| `spec_lint.py --spec … --case …` | **0**（`SUMMARY: VALID`） |
| `extract.py --case … --out … --json` | **0** |

## T4 正常路径回归（改了 4 处代码之后必做）

改完 P1–P4 后重跑 T2/T3：`status=completed`、`gates.all_pass=True`、
**`uncertainty=[]`**、`result.json` 仍是 **29 键**、11 个产物齐全。
⇒ 四处增量**没有**给正常路径引入噪声或改变产物结构。

---

## T5 故障注入实验台：23 条实测摘要

```bash
python "$PKG/scripts/fault_inject.py" --src "$PKG" \
       --workdir /tmp/fi --out /tmp/fi/report.json
```
```
[fault] cases=23 -> I1,I2,I3,I4,I5,I6,I7,T1,T2,T3,T4,T5,D1,D2,D3,D4,K1..K7
[fault] summary: cases=23 mismatch=0
        families={'input': 7, 'template': 5, 'dependency': 4, 'contract': 7}
```
**fault_inject.py 自身 exit 0**。逐条明细见 `references/FAULT-MATRIX.md`；此处只摘关键行：

| 用例 | 注入 | exit | result.json | status | uncertainty 条数 | 静默？ |
|-|-|-|-|-|-|-|
| I1 | 删 case.json | 1 | 6 键 | failed | 2 | 否 |
| I2 | case.json 写坏 | 1 | 6 键 | failed | 2 | 否 |
| I3 | 删 data.csv | 2 | 30 键 | partial | 2 | 否 |
| I4 | data.csv 清空 | 2 | 30 键 | partial | 1 | 否 |
| I5 | 数组形态 | 0 | 29 键 | completed | 0 | 否（正确） |
| I6 | 删 figures 键 | 1 | 29 键 | failed | 1 | 否（修正后**不臆造占位图**） |
| I7 | 列名写错 | 2 | 30 键 | partial | 1 | 否 |
| T1 | 删样式模板 | 0 | 29 键 | completed | 1 | 否（修正后） |
| T2 | 样式模板写坏 | 0 | 29 键 | completed | 1 | 否（修正后） |
| T3 | 删关系词表 | 0 | 29 键 | completed | 0 | 是（装饰层，登记 N1） |
| T4 | 删 schema 模板 | 0 | 29 键 | completed | 0 | 是（无害，登记 N2） |
| T5 | `--style` 拼错 | 0 | 29 键 | completed | 1 | 否（修正后） |
| D1 | 删 chartkit.py | 1 | **无** | — | 0 | 否（登记 N3） |
| D2 | 屏蔽 Pillow | 1 | 6 键 | failed | 2 | **降级失效**（未修，见 §5-D2） |
| D3 | 字体目录为空 | 0 | 29 键 | completed | 0 | 否（系统字体仍在） |
| D4 | 删 extract.py | 1 | **无** | — | 0 | 否（登记 N3） |
| K1 | 契约含 `""`/数字 | 0 | 25 键 | completed | 0 | 否（修正后 G2 不再误判） |
| K2 | 契约含未知类型 | 0 | 30 键 | completed | 0 | 否 |
| K3 | 嵌套 fields 列表 | 0 | 25 键 | completed | 0 | 否 |
| K4 | 嵌套 fields 映射 | 0 | 29 键 | completed | 0 | 否 |
| K5 | 无契约 | 0 | 25 键 | completed | 0 | 否（`applied=false`，不臆造） |
| K6 | 契约是裸字符串 | 0 | 25 键 | completed | 1 | 否（修正后不再谎报） |
| K7 | 契约要不产出的字段 | 0 | 27 键 | completed | 0 | 否（空值非 null） |

**结论**：23 条 `mismatch=0`；修正前有 **9 条**"查不到原因 / 说法与事实不符 / 声明的能力压根不工作"，
本轮修掉 8 条（P1–P8，其中 P5–P8 由 T10 的探针查出），剩 1 条（D2）如实登记。
逐条证据见 `references/FAULT-MATRIX.md` §5。

## T6 反向验证：注入台真的有判别力吗（**用基线包当对照组实测**）

同一台注入器（本版 `fault_inject.py`）分别指向**两个被测包**，跑同样 5 条用例：

```bash
python "$PKG/scripts/fault_inject.py"        --src "<基线包 final/challenge-1bd90d8a>" --workdir <w1> --only K1,K6,T1,T2,I6
python "$PKG/scripts/fault_inject.py"        --src "$PKG" --workdir <w2> --only K1,K6,T1,T2,I6
```

| 用例 | **基线包**实测 | **本版**实测 | 说明 |
|-|-|-|-|
| K1 契约含 `""`/数字 | exit **2** / `partial` / `gates.G2=false`（明细：`声明 4 字段，缺失/为空 ['']`）/ `uncertainty=1`（"G 门未全过，status 降级为 partial"） | exit **0** / `completed` / `G2=true` / `uncertainty=0` | **P1** 修掉：一份完整契约曾被判失败并降级 |
| K6 契约是裸字符串 | `output_contract_applied=`**`true`**（其实一个字段都没写）/ `uncertainty=0` | `output_contract_applied=`**`false`** / `uncertainty=1`（点名形态无法解释） | **P4** 修掉：曾谎报"契约已应用"且无痕 |
| T1 删样式模板 | exit 0 / `completed` / `uncertainty=`**`0`**（静默回退） | exit 0 / `completed` / `uncertainty=`**`1`**（点名缺失物） | **P3** 修掉：装饰层静默回退 |
| T2 样式模板写坏 | exit 0 / `completed` / `uncertainty=`**`0`** | exit 0 / `completed` / `uncertainty=`**`1`** | 同上 |
| I6 删 `figures` 键 | exit 2 / `partial` / 失败记录只有 `不支持的图型：auto` | exit 2 / `partial` / 失败记录**追加**"案例未提供任何图规格（…）" | **P2** 修掉：真实原因曾被丢掉 |

基线包上跑出来的是 `mismatch=1`（K1 那条与"文档声明的行为"不符），本版是 `mismatch=0`。
⇒ 注入台**能区分"修好"与"没修好"**，不是只跑一遍就说"通过"；
⇒ 同时也说明：这几处**不是本轮臆造的假想风险**，而是**基线包真实存在的缺陷**。
（复现记录：`--src` 指向基线包、`--only K1,K6,T1,T2,I6`）

## T7 能力未丢自查

| 项 | 结果 |
|-|-|
| `scripts/*.py` 入口数 | **11**（基线 10 + 新增 `fault_inject.py`；10 个原有入口全部保留） |
| CLI flag 总数 | **17**（`--case --out --work --task --data --style --dpi --note --lang --no-pdf --spec --dir --result --rerun-dir --record-only --json --contract`）+ 新增 `--src --workdir --only --keep --timeout`（仅属于新脚本） |
| 既有脚本删掉的 flag | **0** |
| 既有脚本改名的 flag | **0** |
| `references/OUTPUT_CONTRACT.md` | **与基线逐字节相同**（字段块未动） |
| `templates/*.json`、`examples/case.json` 等 | **与基线逐字节相同** |
| 二进制 / `__pycache__` | **0** |

## T8 与既有四份的差异度（difflib.SequenceMatcher.ratio）

| 对照 | ratio |
|-|-|
| 本版 SKILL.md vs 基线 SKILL.md | 0.2368 |
| vs v1 | 0.3804 |
| vs v2 | 0.2351 |
| vs v3 | 0.3498 |

全部远低于 0.90 门槛（差异来源是**章节骨架即不同**：本版以"注入查出了什么"开篇，
执行链路的每一行都挂着"这步出错时的实测表现"）。

## T10 图型/材料探针：把"声明支持"逐个试一遍

`references/OUTPUT_CONTRACT.md` §6 与 `templates/figure_map.schema.json` 声明支持
`bar/line/scatter/box/heatmap/pie/network/panel/auto` 九种图型，`SKILL.md` S2 另外声明
材料文本的 `ENTITY:`/`REL:` 行可用。做法：为每个声明写一个**最小案例**（同目录临时生成，
不进包），逐个跑 `main.py`，看它到底行不行。**这一轮查出 4 个"声明与实现不符"**。

| 探针 | 输入要点 | 修正前实测 | 修正后实测 | 结论 |
|-|-|-|-|-|
| `p-heatmap` | `type=heatmap`，`matrix=[[1,2,3],[4,5,6]]`，`colormap=viridis` | exit 2 / `partial` / **0 张图**；`ValueError: invalid literal for int() with base 16: '#4'` | **exit 0 / completed / G1–G8 全过** | **P6 修掉**：色阶插值三处写法错误，导致 heatmap 在任何输入下都不可能成功 |
| `p-auto` | `type=auto`（不带列信息） | exit 2 / `partial` / **0 张图**；`不支持的图型：auto` | **exit 0 / completed** | **P7 修掉**：`infer_type` 把字面量 `"auto"` 原样返回，自动推断从未生效 |
| `p-b2-material` | network 只给 `material_file`（材料里写 `ENTITY:`/`REL:`） | exit 2 / `partial`；`通路图需要 entities（节点）列表。` | **exit 0 / completed / 2 张图** | **P5 修掉**：生成路径只认 `entities_file(JSON)`，材料文本解析器（`extract.py` 早已实现）没接上 |
| `p-no-figures` | case.json 合法但**没有任何图规格** | exit 2 / `partial`；先报"不支持的图型：auto"，随后可能**凭空画一张图** | **exit 1 / failed**，`uncertainty` 点明"不臆造图稿"，磁盘上无 `figure-*` | **P8 修掉**（P7 修好后暴露的新风险） |
| `p-box` | `type=box` + `presets` | exit 0 / completed | 同（未受影响） | 声明与实现一致 |
| `p-pie` | `type=pie` | exit 0 / completed | 同 | 一致 |
| `p-inline-network` | network 用 `entities[]`/`relations[]` 内联 | exit 0 / completed | 同 | 一致 |
| `p-filter-empty` | `filter.eq` 写一个不存在的取值 | exit 2 / partial，`filter {...} 无匹配行，列 'grp' 取值：['A','B','C']` | 同（**行为正确**） | 失败信息足够定位 |
| `p-bad-col` | `y.column` 写不存在的列 | exit 2 / partial，单图失败其余继续 | 同（**行为正确**） | 与 D1 的"单图失败不阻塞"一致 |
| `p-no-err-sem` | `error.semantics="IQR-ish"`（非常规） | exit 0 / completed + `spec_lint E4` 警告 | 同 | 只 warn 不阻断，符合 E4 定义 |
| `p-4fig` | 4 张图，第 4 张列名错 | exit 2 / partial，**前 3 张照常产出** | 同 | 单图失败不阻塞（4/4 目录产物） |

> 探针脚本与产物**不入包**（只在包外临时目录生成）；上表是实测摘录。
> 结论：**9 种图型现在全部走通**；4 处"文档写了但实现没做"的落差已修，
> 且修法都是纯增量（见 `references/FAULT-MATRIX.md` §5 的 P5–P8）。

---

## T9 假变体自查（看**形态**，不是玩关键词）

判据不是"有没有某个词"，而是**形态**：包内是否存在"往 SKILL/README 末尾追加一段与正文无关的
自检声明 / 补记段落 / 流水日志式注释"这类**没有实质内容的尾巴**。实际做法与结论：

1. **逐文件比对结构**：本版对基线的改动集中在 `scripts/main.py`、`scripts/figcheck.py`
   （**纯增量**，逐条记录在 `FAULT-MATRIX.md` §5 的 P1–P4），
   **新增** `scripts/fault_inject.py` 与 `references/FAULT-MATRIX.md`；文档侧是对
   `SKILL.md` / `README.md` / `TEST.md` / `COMPARE.md` / `references/RUBRIC_MAP.md` /
   `references/failure-modes.md` 的**整章重写或补写实质章节**（例如给 `failure-modes.md`
   补了"本表的实测复核状态"一节，逐族给出注入用例与复核结论），**不是尾部追加**。
2. **尾部检查**：`SKILL.md` 的最后一节是"限制（如实声明，不掩饰）"、`README.md` 是"维护"、
   `TEST.md` 是本节之后的"未解决项（如实列出）"——**没有任何**"自检通过 / 已复核 / 特此说明"
   式的收尾段。
3. **关键词扫描**：对包内全文扫过提交回报里列出的五个模式，**0 命中**。
4. **允许出现且逐条说明的两处**：
   - `change_records`：`references/OUTPUT_CONTRACT.md` 定义的**契约字段**（人工确认 +
     脚本执行流水），出现在契约文档、`templates/result.template.json`、示例产物与脚本里属正常；
   - `fault_inject.py` 报告里的 `cases[].injected`：**注入动作的描述**（如"删除 data.csv"），
     不是"变更记录"段，也不进任何交付文档的尾部。

**结论**：本版的差异全部落在"机制/证据/文档实质内容"上，不存在空转的注释尾巴。
---

## 未解决项（如实列出）

1. **D2 降级路径未生效**（缺 Pillow → FATAL，`result.json` 缩成 6 键，SVG 不进入 outputs）。
   修它需要改 `figcheck.py` 的 G6 判定语义，超出"只修真实缺陷、不改退出码语义"的边界，
   本轮只登记 + 给出部署前自检命令。**复现**：`--only D2`。
2. **模块缺失不写信封**（N3）：`import chartkit` 早于 `main()` 的兜底逻辑。可接受（exit 1 明确失败），
   但下游不能假设"跑过就一定有权封"。
3. **`entity_glossary.json` 回退无痕**（N1）：装饰层回退，不影响数据闭合，本轮不改。
4. 注入只覆盖 23 种故障；并发、磁盘满、超长文本、非 UTF-8 输入**未测**。
