# README.md — 学术 PPT 生成与编辑 Skill（总集成版 · ppt-6ad93034）

> **一份包，六段路**：输入 → 执行 → 失败 → 增益 → 机制 → 复用。
> 每段都有随包证据，不靠自述：`SKILL.md` 是索引，下面是每段对应的文件与命令。

| 段 | 你会拿到什么 | 文件 |
|-|-|-|
| 输入 | 契约、输入格式、产物归属、包体纪律 | `SKILL.md` §1、`references/OUTPUT_CONTRACT.md` |
| 执行 | CP0–CP5 流程、D1–D14 决策规则、7 类编辑操作 | `SKILL.md` §2、`references/EDIT_OPS.md`（含页面蓝图）、`references/failure-modes.md` |
| 失败 | 28 条故障逐行实测 + 7 条静默缺口 + 17 条恢复动作 + 守卫 | `references/FAULT-MATRIX.md`、`scripts/fault_inject.py` |
| 增益 | 公平对照协议 + 指标公式 + 真实 Δ（含负面项） | `references/GAIN-PROTOCOL.md`、`references/measure_gain.py` |
| 机制 | 五个机制的可证伪判据 + 会 FAIL 的探针 | `references/MECHANISM-AND-ASSETS.md`、`references/mechanism_probe.py` |
| 复用 | 十一个可拿走资产 + 两个题材的案例题集 + 判据 | `references/MECHANISM-AND-ASSETS.md` 第二部分、`references/CASE-SET.md`、`scripts/case_check.py` |

## 1. 快速开始

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"      # 含 SKILL.md 的技能根目录
OUT=/app/output                                     # 本地跑就换成任意可写目录

# ① 前置体检（CP0）：挡掉三类"崩了却不写 result.json"
python "$SKILL_DIR/scripts/fault_inject.py" --guard --case /input/case.json \
    --template /input/template.json                  # --template 可省略

# ② 端到端（CP1–CP4）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out "$OUT"

# ③ 契约门 G1–G8（exit 0 = 通过；--case 必须传）
python "$SKILL_DIR/scripts/result_tool.py" --result "$OUT/result.json" \
    --out-dir "$OUT" --case /input/case.json \
    --envelope "$SKILL_DIR/templates/result_envelope.json"

# ④ 产物自检（all_pass=true）
python "$SKILL_DIR/scripts/selftest.py" --out "$OUT" --case /input/case.json

# ⑤ 运行后核对（CP5）：把"静默降级"找出来
python "$SKILL_DIR/scripts/fault_inject.py" --guard --out "$OUT"

# ⑥ 局部编辑 + 版本归档
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out "$OUT" \
    --edit edits.json --version v2
```

> **必须在包外跑**：任何脚本都会让 Python 在包内写 `__pycache__`，平台预检会因此拒收整包。
> 把技能包 `cp -r` 到包外再跑；本包的三个台（注入/泛化/测量）都自己做了这件事。

## 2. 四个台（本包的工具箱）

| 台 | 命令 | 作用 | 退出码 | 耗时 |
|-|-|-|-|-|
| **注入台** | `python "$SKILL_DIR/scripts/fault_inject.py" --pkg "$SKILL_DIR" --work <包外> --with-recovery` | 四族 28 条故障逐个弄坏并跑主流程；17 条恢复动作 | 0 一致 / 1 有偏差或静默 / 2 环境不可用 | ~60 s |
| **守卫** | 同上 `--guard --case C [--template T]` / `--guard --out O` | 运行前体检 + 运行后核对（抓静默降级） | 0 干净 / 1 有 BLOCKER 或 WARN | <1 s |
| **泛化台** | `python "$SKILL_DIR/scripts/case_check.py" --pkg "$SKILL_DIR" --work <包外> --probes` | 两个题材的案例逐案判定 + 四种边界探针 | 0 全过 / 1 有 FAIL / 2 环境不可用 | ~12 s |
| **测量台** | `cp references/measure_gain.py <包外>/ && python <包外>/measure_gain.py --skill-dir "$SKILL_DIR" --case A --case B --work <包外>/work --out <包外>/gain.json` | 与"不加载 Skill 的基础 Agent"的公平对照 | 0 / 1 | 数秒 |

**实测摘要**：注入台 28 条 → `exit 0×14 / 1×10 / 2×4`，**7 条静默失败**，
17/17 恢复动作有结局；守卫 **7/7 抓到静默、健康产物 0 误报**；
泛化台两案例 **12/12 与 11/11 PASS**（案例 B 无表 → `figure_kinds={none:6}`，0 张编造图）；
测量台 Δ = Q1/Q3/Q4/Q5 `+1.0000`、Q6 `+0.8571`，脚本耗时 `+4.75 s`（**成本，非收益**）。

## 3. 目录结构

```
<技能根>/
├── SKILL.md                      # 索引：输入→执行→失败→增益→机制→复用（§1–§9）
├── README.md                     # 本文件
├── TEST.md                       # 16 组实测（含三个台与两案例）
├── GITHUB_URL.txt                # 公开作品链接（单行）
├── references/
│   ├── OUTPUT_CONTRACT.md        # result.json 字段契约 + G1–G8（**字段块逐字保留**）
│   ├── RUBRIC_MAP.md             # 五维评分（40/25/15/10/10）逐条落点
│   ├── failure-modes.md          # 判读约定 + F1–F5 五族 + 增益侵蚀/机制受损 + 实测 + 跨题材
│   ├── EDIT_OPS.md               # ★ 7 类编辑操作目录 + 决策树 + **页面蓝图与模板槽位**（合并）
│   ├── FAULT-MATRIX.md           # ★ 28 条注入 × 17 条恢复的逐行实测矩阵 + 守卫
│   ├── GAIN-PROTOCOL.md          # ★ 公平对照协议、指标公式、可证伪判据、局限
│   ├── MECHANISM-AND-ASSETS.md   # ★ 五个机制（判据/探针）+ 十一个可复用资产（合并）
│   ├── CASE-SET.md               # ★ 两个题材的题集：输入/期望/可接受区间/失效边界
│   ├── VARIANT-SKILL-APPENDIX.md # v4/v5 的 SKILL 正文原文（union 溯源用）
│   ├── measure_gain.py           # 对照测量台（包外跑）
│   └── mechanism_probe.py        # M1–M5 机制判据探针（包外跑）
├── scripts/
│   ├── main.py                   # 单一入口（CP1–CP4 编排）
│   ├── deck_extract.py           # extract：读实际材料 → material_view.json
│   ├── slide_text.py             # build：页序/角色/主张/备注文案
│   ├── deck_tool.py              # build：图表四态绑定 + 模板槽位建稿 + 编辑 op
│   ├── render_qa.py              # render：PIL PNG + reportlab PDF + 渲染 QA
│   ├── evidence_check.py         # verify：数字核验 + plan_lint + 证据脚注
│   ├── result_tool.py            # verify：result.json + G1–G8 契约门
│   ├── selftest.py               # verify：产物自检
│   ├── make_examples.py          # 维护：重建 examples/output/ 并净化绝对路径
│   ├── deck_common.py            # 公共：路径自定位/原子写/sha256/日志/CJK 字体
│   ├── fault_inject.py           # ★ 注入台 + 恢复演练 + 守卫（--guard）
│   └── case_check.py             # ★ 泛化台：逐案判定 + 边界探针
├── templates/
│   ├── default.json              # 模板参数（配色/字号/页脚/版式槽位）
│   └── result_envelope.json      # 结果信封（G8 用）
└── examples/                     # 全部为虚构材料（非正式案例）
    ├── EXPECTED-OUTPUT.md        # 应产出的文件清单 + 契约字段 + **examples/ 目录说明**（合并）
    ├── case.json  task.md  material.md  results.csv  edit_demo.json
    ├── output/                   # 一次真实运行的文本副本（已净化路径）
    └── cases/                    # 两个不同题材的合成案例
        ├── case-a-perovskite/{case.json, material.md, jv.csv, task.md}
        └── case-b-climate-text/{case.json, material.md, task.md}
```

> **合并说明（为守 ≤50 文件上限，内容一字未删）**：
> ① `EDIT_OPS.md` = 原 EDIT_OPS + 原 DECK_SPEC；② `EXPECTED-OUTPUT.md` = 原 EXPECTED-OUTPUT + 原 examples/README；
> ③ `MECHANISM-AND-ASSETS.md` = 原 MECHANISM + 原 REUSABLE-ASSETS。
> 合并处都有"原 …"标注与过渡说明。

## 4. 依赖

| 依赖 | 版本 | 必需性 | 缺失时行为（实测） |
|-|-|-|-|
| Python | 3.8+ | 必需 | — |
| `python-pptx` | ≥0.6.21 | **建稿必需** | 硬崩、不写 `result.json` → 用 CP0 守卫先拦（`FAULT-MATRIX.md` §2 S4） |
| `Pillow` | ≥9 | **预览必需** | 同上（S5） |
| `matplotlib` | ≥3.5 | 可选 | 结果页降级原生表格，`figure.note` 有记录，`exit=0` |
| `numpy` | 随 matplotlib | 可选 | 同上 |
| `reportlab` | 任意 | 可选 | 跳过 PDF 预览（`uncertainty` + `previews.warnings` 各一条） |
| PDF 抽取（`fitz`/`pypdf`/`PyPDF2`/`pdfplumber`） | 任一 | 材料是 PDF 时必需 | 全缺时按 D3：Agent 抽文本后重跑 |

安装：`pip install python-pptx matplotlib pillow numpy reportlab`
（**包内不带任何二进制**：模板由 `templates/*.json` 参数化，图表/预览全部运行时生成。）

## 5. 输入格式（`case.json`）

```json
{
  "case_id": "case-xxx",
  "title": "案例标题",
  "inputs": {"task_md": "task.md", "material": ["paper.md", "data.csv"]},
  "spec": {"audience": "答辩", "duration_minutes": 12, "max_slides": 8,
           "template": "default",
           "template_pptx": "可选母版.pptx", "starting_deck": "可选起始稿.pptx",
           "style": {"colors": {"accent": "#1565C0"}, "footer": {"text": "页脚"}}},
  "output_contract": {"case_id": "string", "deck": "dict"}
}
```

- `material[]` 是相对 `case.json` 的路径（也接受绝对路径）；`--input-dir` 可改基准目录；
- **`material[]` 顺序 = 数据源优先级**：多张表时只绑定第一张（实测 GAP-P1），
  要进结果页的表请放第一位；
- `output_contract` 必须是**对象或字段名列表**；写成字符串会让回显**整体静默跳过**
  （实测缺口 S2，CP0 守卫会提前报警）。

## 6. 输出与验收

一次成功运行（示例案例，`max_slides=6`）实测产出 **25 个文件**、
`result.json` 顶层 **18 个键**；两个合成案例各 **20 个键**
（18 基键 + 3 个契约回显，其中 1 个与基键重合）。

验收五层（**互不顶替**）：

| 层 | 命令 | 查什么 |
|-|-|-|
| 产物层 | `selftest.py` | 文件在不在、deck 能否重开、页数对不对、预览有没有 |
| 契约层 | `result_tool.py` | G1–G8：字段齐不齐、契约回显、禁 null、证据行数=页数、备注非空、sha256 |
| 内容层 | `evidence_check` + `plan_lint` | 数字能否回指材料、页面纪律 |
| **机制层** | `mechanism_probe.py --out O` | M1–M5 的痕迹是否真在产物里（5/5 PASS，负例会 FAIL） |
| **留痕 / 泛化层** | `fault_inject.py --guard --out O`、`case_check.py` | 降级有没有留痕、图表有没有静默消失、跨题材是否仍在区间内 |

## 7. 限制与已知问题（诚实声明）

1. **7 条静默缺口**（`FAULT-MATRIX.md` §2）：S1 表解析不出时图表静默消失；
   S2 契约非对象时回显整体跳过；S3 母版不存在时静默换内置；
   S4–S7 参数形态错误 / 缺 `python-pptx` / 缺 `Pillow` 时硬崩且不写 `result.json`。
2. **7 条跨题材失效边界**（`CASE-SET.md` §3）：缺小节→占位主张；markdown 表不如 CSV 优先；
   编号小标题被切成退化要点；关键年份可能不进页面；结果页可能取到摘要；
   多表只认第一张；页数压缩不留痕。**其中 6 条不留痕**，契约门与自检都抓不到。
3. **判定是结构+覆盖判据**，不是质量判据：不证明"这一版讲得好"。
4. **对照是脚本级**：测量台的基线是"题面点名失败形态的确定性代理实现"，
   不是平台官方 Agent 对照（平台对照由平台生成）。
5. **预览 ≠ Office 导出**；`--draft` 只跳过 PDF，PNG 仍需要 Pillow。
6. **注入台覆盖不到**：并发/中断、畸形但合法的 PPTX、GB 级材料、真机 Office 渲染、平台预检
   （`FAULT-MATRIX.md` §5 逐条列明）。

## 8. 失败处理（一页速查）

| 症状 | 先看哪 | 处置 |
|-|-|-|
| 没有 `result.json` | `--guard --out` 报 BLOCKER | 多半是 CP0 该拦的：坏参数 / 缺库（S4–S7） |
| `status=partial` | `result.json.uncertainty` | 逐条看降级原因；补件或换参数后重跑 |
| 契约字段没回显 | 先确认**传了 `--case`** | 再确认 `output_contract` 是对象/列表形态（S2） |
| 结果页没图 | `figure.kind` / `figure.note` | 有 note = 正常降级；无 note = 静默丢图（S1）或数据源没选对（GAP-P1/A2） |
| 关键数字没上页 | 人工看 `deck.slides[].claims` | 角色→章节可能错位（GAP-B2/B3），用 `--edit` 修或补材料小节 |
| 页数不对 | `spec.max_slides` vs `slide_count` | 过小时角色会被压缩且不留痕（GAP-P3） |
| 机制探针 FAIL | 探针打印的具体缺陷 | 对应 M1–M5 的哪条痕迹丢了（`MECHANISM-AND-ASSETS.md` 第一部分） |
| deck 打不开 | `selftest` 的 `pptx_reopen` | 复制 `work/deck_<v>.pptx` 回退后重跑 |

## 9. 生态与复用

- **十一个资产**（位置 / 拿走它 / 怎么用 / 依赖 / 不适用处）见
  `references/MECHANISM-AND-ASSETS.md` 第二部分；其中三个台（测量/注入/泛化）
  **不 import 本包任何模块**，只读公开产物，可直接搬到别的 Skill 仓库复用。
- **题集可扩展**：`examples/cases/` 下加一个目录 + `case.json`（含 `_case_set.expect`）
  即可，`case_check.py --list` 自动发现；加案例四步法见 `CASE-SET.md` §4。
- **模板与信封参数化**：换模板不改代码（改 `templates/*.json` 或给 `template_pptx`）。
- 两个合成案例可直接当**回归用例**：改完脚本先跑 `case_check.py --probes`
  与 `fault_inject.py --with-recovery`，再谈"这次改动有没有让别处退步"。

## 10. 维护

1. 改了脚本/模板 → `python "$SKILL_DIR/scripts/make_examples.py"` 重建 `examples/output/`；
2. 改了失败分支 → 跑注入台 `--with-recovery`，把**实测值**更新进 `references/FAULT-MATRIX.md`；
3. 改了案例或判据 → 跑泛化台 `--probes`，把**实测值**更新进 `references/CASE-SET.md`；
4. 改了与增益有关的行为 → 重跑测量台，更新 `references/GAIN-PROTOCOL.md` 的 Δ 表
   （**负面结果照原样报**）；
5. 提交前：`python validate_pkg.py <包>`（≤50 文件 / ≤2MB / 扩展名白名单 / UTF-8 /
   无绝对路径 / frontmatter），再按 `TEST.md` 跑一遍。
