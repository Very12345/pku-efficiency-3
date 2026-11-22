# README.md — 学术 PPT 生成与编辑 Skill（多案例泛化版 · ppt-6ad93034）

> 本包除了"能把材料变成可编辑 PPT"，还把**"换个题材还行不行"**做成了可复跑的东西：
> 两个不同题材的合成案例 + 每个案例的可接受区间 + 一个逐案判定台
> （`scripts/case_check.py`），外加四种边界变形的实测结论。
> 全部数字在 `references/CASE-SET.md`。

## 1. 快速开始

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"      # 含 SKILL.md 的技能根目录
OUT=/app/output                                     # 本地跑就换成任意可写目录

# ① 主流程：建稿 + 预览 + result.json + 证据映射 + manifest
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out "$OUT"

# ② 契约门 G1–G8（exit 0 = 通过；--case 必须传，否则无法核对契约回显）
python "$SKILL_DIR/scripts/result_tool.py" --result "$OUT/result.json" \
    --out-dir "$OUT" --case /input/case.json \
    --envelope "$SKILL_DIR/templates/result_envelope.json"

# ③ 产物自检（all_pass=true 为通过）
python "$SKILL_DIR/scripts/selftest.py" --out "$OUT" --case /input/case.json

# ④ 局部编辑 + 版本归档（演示稿迭代）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out "$OUT" \
    --edit edits.json --version v2
```

> **必须在包外跑**：任何脚本都会让 Python 在包内写 `__pycache__`，平台预检会因此拒收整包。
> 把技能包 `cp -r` 到包外再跑；`case_check.py` 自己就是这么做的。

## 2. 题集与泛化台（本版特有）

```bash
python "$SKILL_DIR/scripts/case_check.py" --list        # 看两个案例与各自的期望区间
python "$SKILL_DIR/scripts/case_check.py" --pkg "$SKILL_DIR" --work <包外目录>
python "$SKILL_DIR/scripts/case_check.py" --pkg "$SKILL_DIR" --work <包外目录> --probes
python "$SKILL_DIR/scripts/case_check.py" --pkg "$SKILL_DIR" --work <包外目录> --only case-b-climate-text
```

| 案例 | 题材 | 难度层 | 关键检验 |
|-|-|-|-|
| `examples/cases/case-a-perovskite/` | 实验科学（材料器件） | 基础层：有 CSV 数值表 | 数值表**原样重绘**；结论数字不走样 |
| `examples/cases/case-b-climate-text/` | 理论 / 文献计量 | 困难层：**无任何数值表** | **不许凭空画曲线**（禁 `chart_image`）；引用可回指 |

**本机实测（2026-11-23）**：

| 案例 | exit | status | slides | 图表形态 | unverified | 备注/脚注覆盖 | 判定 |
|-|-|-|-|-|-|-|-|
| A | 1 | `partial` | 8 | `chart_image ×1` + `none ×7` | 1 | 1.0 / 1.0 | **12/12 PASS** |
| B | 1 | `partial` | 6 | **`none ×6`（0 张编造图）** | 1 | 1.0 / 1.0 | **11/11 PASS** |

四种边界探针（`--probes`，同一案例 A 变形）：

| # | 变形 | 实测结论 |
|-|-|-|
| P1 | 材料给两张 CSV | 只绑定**第一张**，第二张静默忽略 → **GAP-P1** |
| P2 | 材料没有任何章节标题 | 占位主张 1→3 条，`plan_lint` 偏差进 `uncertainty`（D4 生效） |
| P3 | `max_slides` 压到 3 | 角色被压成 `cover→overview→result`，`change_records` 无压缩记录 → **GAP-P3** |
| P4 | `--edit` 塞入材料里没有的数字 | 该主张立刻进 `unverified_claims`（D2 生效） ✅ |

## 3. 目录结构

```
<技能根>/
├── SKILL.md                      # 主文档：题集 + 判定判据 + D1–D12 + 失效边界
├── README.md                     # 本文件
├── TEST.md                       # 12 组实测（含泛化台与边界探针）
├── GITHUB_URL.txt                # 公开作品链接（单行）
├── references/
│   ├── OUTPUT_CONTRACT.md        # result.json 字段契约 + G1–G8（**字段块逐字保留**）
│   ├── RUBRIC_MAP.md             # 五维评分（40/25/15/10/10）逐条落点
│   ├── failure-modes.md          # 五族失败模式 + 退出码语义 + 状态一致性
│   ├── CASE-SET.md               # ★本版核心：题集、可接受区间、逐案实测、失效边界
│   ├── DECK_SPEC.md              # 页面蓝图 + 模板槽位
│   └── EDIT_OPS.md               # 7 类编辑操作目录 + 决策树
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
│   └── case_check.py             # ★本版新增：逐案实测 + 区间判定 + 边界探针
├── templates/
│   ├── default.json              # 模板参数（配色/字号/页脚/版式槽位）
│   └── result_envelope.json      # 结果信封（G8 用）
└── examples/                     # 最小示例（虚构材料，非正式案例）
    ├── README.md  EXPECTED-OUTPUT.md
    ├── case.json  task.md  material.md  results.csv  edit_demo.json
    ├── output/                   # 一次真实运行的文本副本（已净化路径）
    └── cases/                    # ★本版新增：两个不同题材的合成案例
        ├── case-a-perovskite/{case.json, material.md, jv.csv, task.md}
        └── case-b-climate-text/{case.json, material.md, task.md}
```

## 4. 依赖

| 依赖 | 版本 | 必需性 | 缺失时行为 |
|-|-|-|-|
| Python | 3.8+ | 必需 | — |
| `python-pptx` | ≥0.6.21 | **建稿必需** | 无法建稿 → 如实报 partial/failed（实测会硬崩且不写 result.json，见 `failure-modes.md` §10） |
| `Pillow` | ≥9 | **预览必需** | 预览 PNG 不产出 → G5 error、`partial` |
| `matplotlib` | ≥3.5 | 可选 | 结果页降级为 PPTX 原生可编辑表格（`figure.note` 有记录） |
| `numpy` | 随 matplotlib | 可选 | 同上 |
| `reportlab` | 任意 | 可选 | 跳过 PDF 预览（`previews.warnings` + `uncertainty` 各一条） |
| PDF 抽取（`fitz`/`pypdf`/`PyPDF2`/`pdfplumber`） | 任一 | 材料是 PDF 时必需 | 全缺时按 D3：由 Agent 抽文本后重跑 |

安装：`pip install python-pptx matplotlib pillow numpy reportlab`
（**包内不带任何二进制**：模板由 `templates/*.json` 参数化，图表/预览全部运行时生成。）

## 5. 输入格式（`case.json`）

```json
{
  "case_id": "case-xxx",
  "title": "案例标题",
  "inputs": {"task_md": "task.md", "material": ["paper.md", "data.csv"]},
  "spec": {"audience": "答辩", "duration_minutes": 12, "max_slides": 8,
           "template": "default", "style": {"colors": {"accent": "#1565C0"}}},
  "output_contract": {"case_id": "string", "deck": "dict"}
}
```

- `material[]` 里是**相对 `case.json` 的路径**（也接受绝对路径）；`--input-dir` 可改基准目录；
- **`material[]` 的顺序就是数据源优先级**：多张表时只绑定第一张（实测 GAP-P1），
  所以要把"要进结果页的那张表"放第一位；
- `output_contract` 声明字段会逐项回显到 `result.json` 顶层（四形态空值，禁 `null`）；
  其形态必须是**对象或字段名列表**——写成字符串会让回显整体静默跳过
  （见 `failure-modes.md` §10 与本包 TEST §T11）。

## 6. 命令索引与退出码

| 入口 | 关键参数 | 用途 | 退出码 |
|-|-|-|-|
| `main.py` | `--case --out [--input-dir --template --max-slides --edit --no-chart --version --draft --verbose]` | 端到端 CP1–CP4 | 0 success / 1 partial / 2 输入不可读 |
| `result_tool.py` | `--result --out-dir [--case --envelope]` | G1–G8 契约门 | 0 / 1 / 2 |
| `selftest.py` | `--out [--case --pptx --slides]` | 产物自检 | 0 / 1 |
| `evidence_check.py` | `--claim --material` | 单条主张数字核验 | 0 / 1 |
| `make_examples.py` | `[--work-dir --dry-run]` | 重建示例产物 | 0 / 1 |
| `case_check.py` | `--pkg --work [--only --probes --probe-case --report-json --report-md]` | 泛化台：逐案判定 + 边界探针 | 0 全过 / 1 有 FAIL / 2 环境不可用 |

## 7. 输出与验收

一次成功运行（示例案例，`max_slides=6`）实测产出 **25 个文件**：
`result.json`（18 个顶层键）、`evidence_map.md`、`evidence_map.json`、`changelog.jsonl`、
`manifest.json`、`logs/run_*.log`、`work/deck.pptx`（6 页）、`work/plan.json`、
`work/material_view.json`、`work/chart_results.csv.png`、`work/table_cache/results.csv`、
`work/preview/slide_01..06.png` + `preview.pdf`、输出根 `preview/` 同名副本。

验收四层（**互不顶替**）：

| 层 | 命令 | 查什么 |
|-|-|-|
| 产物层 | `selftest.py` | 文件在不在、deck 能不能重开、页数对不对、预览有没有 |
| 契约层 | `result_tool.py` | G1–G8：字段齐不齐、契约回显、禁 null、证据行数=页数、备注非空、sha256 |
| 内容层 | `evidence_check` + `plan_lint` | 页面数字能否回指材料、页面纪律（角色/要点数/长度） |
| **泛化层（本版）** | `case_check.py` | 换题材/换结构后：页数、角色、图表形态、待核验上限、备注与脚注覆盖、禁列内容 |

## 8. 限制与已知问题（诚实声明）

1. **7 条泛化失效边界**（`references/CASE-SET.md` §3 逐条给实测证据）：
   GAP-A1 缺标准小节 → 占位主张；GAP-A2 markdown 表不如 CSV 优先；
   GAP-B1 编号小标题被切成退化要点；GAP-B2 关键年份可能整体不进页面；
   GAP-B3 结果页可能取到摘要；GAP-P1 多表只认第一张；GAP-P3 页数压缩不留痕。
2. **案例只有 2 个题材**（实验科学 / 理论文本），不覆盖医学统计、工程图纸、教学课件等形态。
3. **判定是结构+覆盖判据，不是质量判据**：不证明"这一版讲得好"。
4. **预览 ≠ Office 导出**：无 PowerPoint/LibreOffice 时预览为 PIL/reportlab 近似渲染。
5. **`--draft` 只跳过 PDF 预览**，PNG 仍需要 Pillow。

## 9. 失败处理（一页速查）

| 症状 | 先看哪 | 处置 |
|---|---|---|
| 页数不对 | `spec.max_slides` vs `deck.slide_count` | 检查 `--max-slides` 是否覆盖；过小时角色会被压缩（GAP-P3） |
| 结果页没图 | `figure.kind` / `figure.note` | 无 note 且材料有表 = 数据源没选对（把 CSV 放 `material[]` 第一位） |
| `status=partial` | `result.json.uncertainty` | 逐条看：缺小节 → 占位主张；`plan_lint` 偏差；渲染降级 |
| 契约字段没回显 | **先确认传了 `--case`** | 再确认 `output_contract` 是对象/列表形态 |
| 关键数字没上页 | 人工看 `deck.slides[].claims` | 角色→章节映射可能错位（GAP-B2/B3），用 `--edit` 修或补材料小节 |
| deck 打不开 | `selftest` 的 `pptx_reopen` | 复制 `work/deck_<v>.pptx` 回退后重跑 |

## 10. 生态与复用

- **题集可扩展**：在 `examples/cases/` 下加一个目录 + `case.json`（含 `_case_set.expect`）即可，
  判定台自动发现（`--list` 可见）。加案例的四步法见 `references/CASE-SET.md` §4。
- **判据写法小抄**：`status_any_of` / `slide_count` / `roles_head|tail` /
  `must_have_figure_kind` / `forbid_figure_kind` / `unverified_claims_max` /
  `min_notes_coverage` / `min_evidence_footer_coverage` / `must_mention_in_deck` /
  `forbid_in_deck`（`CASE-SET.md` §4 有完整表）。
- **`case_check.py` 可脱离本包复用**：它只调用 `scripts/main.py` 并读公开产物
  （`result.json` 与 `work/material_view.json`），不 import 本包任何模块——
  把 `--pkg` 指向别的 Skill 也能当"逐案回归台"用（判据换掉即可）。
- **两个合成案例可直接当回归用例**：改完脚本先跑 `case_check.py --probes`，
  再谈"这次改动有没有让别处退步"。

## 11. 维护

1. 改了脚本/模板 → `python "$SKILL_DIR/scripts/make_examples.py"` 重建 `examples/output/`；
2. 改了案例或判据 → `python "$SKILL_DIR/scripts/case_check.py" --pkg "$SKILL_DIR" --work <包外> --probes`
   并把**实测值**更新进 `references/CASE-SET.md`（只写实测，不写期望）；
3. 提交前：`python validate_pkg.py <包>`（≤50 文件 / ≤2MB / 扩展名白名单 / UTF-8 /
   无绝对路径 / frontmatter），再按 `TEST.md` 跑一遍。
