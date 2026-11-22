# README.md — 学术 PPT 生成与编辑 Skill（抗故障 / 可判读版 · ppt-6ad93034）

> 本包在"能生成可编辑学术 PPT"之外，多做了一件容易被跳过的事：
> **把上游输入逐个弄坏，真跑一遍，然后把 `exit/status/uncertainty/留痕/是否静默` 记下来。**
> 结果在 `references/FAULT-MATRIX.md`（28 条故障 + 17 条恢复动作，全部实测）。

## 1. 快速开始

```bash
# 0) 约定：$SKILL_DIR = 含 SKILL.md 的技能根目录（平台容器内为 /skills/weekly-skill）
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
OUT=/app/output                     # 本地跑就换成任意可写目录

# ① 前置体检（CP0）——能挡掉三类"崩了却不写 result.json"的情形
python "$SKILL_DIR/scripts/fault_inject.py" --guard --case /input/case.json \
    --template /input/template.json          # --template 可省略

# ② 端到端：建稿 + 预览 + result.json + 证据映射 + manifest
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out "$OUT"

# ③ 契约门 G1–G8（exit 0 = 通过；--case 必须传，否则无法核对契约回显）
python "$SKILL_DIR/scripts/result_tool.py" --result "$OUT/result.json" \
    --out-dir "$OUT" --case /input/case.json \
    --envelope "$SKILL_DIR/templates/result_envelope.json"

# ④ 产物自检（all_pass=true 为通过）
python "$SKILL_DIR/scripts/selftest.py" --out "$OUT" --case /input/case.json

# ⑤ 运行后核对（CP5）——把"静默降级"找出来
python "$SKILL_DIR/scripts/fault_inject.py" --guard --out "$OUT"

# ⑥ 局部编辑 + 版本归档（演示稿迭代）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out "$OUT" \
    --edit edits.json --version v2
```

> **必须在包外跑**：任何脚本都会让 Python 在包内写 `__pycache__`，而平台预检会因此拒收整包。
> 把技能包 `cp -r` 到包外再跑；`fault_inject.py` 自己就是这么做的（它默认把被测包复制到
> `<work>/pkgs/<id>/` 再执行）。

## 2. 失败注入与恢复演练（本版特有）

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --list          # 看 28 条故障清单（不执行）
python "$SKILL_DIR/scripts/fault_inject.py" --pkg "$SKILL_DIR" --work <包外目录>
python "$SKILL_DIR/scripts/fault_inject.py" --pkg "$SKILL_DIR" --work <包外目录> --with-recovery
python "$SKILL_DIR/scripts/fault_inject.py" --pkg "$SKILL_DIR" --work <包外目录> --shape contract
python "$SKILL_DIR/scripts/fault_inject.py" --pkg "$SKILL_DIR" --work <包外目录> --only F-IN-07,F-DEP-03
```

- 四族故障：**input / template / dependency / contract**，共 28 条（每族 5–10 条）；
- 每条都在包外副本上跑**完整 `main.py`**，再回读 `result.json` / `changelog.jsonl` / `logs/`；
- `--with-recovery` 会对每条再跑一次**真实恢复动作**并记录恢复后的 exit/status；
- `--report-json/--report-md/--report-csv` 可把结果落盘（报告里的绝对路径会被自动净化）。
- **退出码**：`0` = 全部与期望一致且无静默失败；`1` = 有偏差或有静默失败；`2` = 环境不可用。

**本机实测结论（2026-11-23，Windows + Python 3.13）**：
28 条全部执行、总耗时约 60 秒；`exit 分布 0×14 / 1×10 / 2×4`；
**7 条静默失败**（`F-IN-07` `F-TPL-03` `F-TPL-05` `F-DEP-03` `F-DEP-04` `F-DEP-05` `F-CTR-03`）；
17 条有恢复动作的故障 **17/17 被恢复或被守卫判定**。逐条证据见 `references/FAULT-MATRIX.md`。

## 3. 目录结构

```
<技能根>/
├── SKILL.md                      # 主文档：CP0–CP5 流程 + D1–D12 + 恢复动作 + 已知缺口
├── README.md                     # 本文件：安装/用法/依赖/限制/维护
├── TEST.md                       # 怎么自测：12 组实测（含注入台与守卫）
├── GITHUB_URL.txt                # 公开作品链接（单行）
├── references/
│   ├── OUTPUT_CONTRACT.md        # result.json 字段契约 + G1–G8（**字段块逐字保留**）
│   ├── RUBRIC_MAP.md             # 五维评分（40/25/15/10/10）逐条落点
│   ├── failure-modes.md          # 五族失败模式 + 退出码语义 + 状态一致性
│   ├── FAULT-MATRIX.md           # ★本版核心：28 条注入 × 17 条恢复的逐行实测矩阵
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
│   └── fault_inject.py           # ★本版新增：注入台 + 恢复演练 + 守卫（--guard）
├── templates/
│   ├── default.json              # 模板参数（配色/字号/页脚/版式槽位）
│   └── result_envelope.json      # 结果信封（G8 用）
└── examples/                     # 最小示例（虚构材料，非正式案例）
    ├── README.md  EXPECTED-OUTPUT.md
    ├── case.json  task.md  material.md  results.csv  edit_demo.json
    └── output/                   # 一次真实运行的文本副本（已净化路径）
```

## 4. 依赖

| 依赖 | 版本 | 必需性 | 缺失时实测行为（`FAULT-MATRIX.md` §2） |
|-|-|-|-|
| Python | 3.8+ | 必需 | — |
| `python-pptx` | ≥0.6.21 | **建稿必需** | `F-DEP-03`：硬崩、**不写 result.json** → 用 CP0 守卫先拦 |
| `Pillow` | ≥9 | **预览必需** | `F-DEP-04/05`：硬崩、不写 result.json → 用 CP0 守卫先拦 |
| `matplotlib` | ≥3.5 | 可选 | `F-DEP-01`：结果页降级原生表格，`figure.note` 有记录，`exit=0` |
| `numpy` | 随 matplotlib | 可选 | 同上 |
| `reportlab` | 任意 | 可选 | `F-DEP-02`：跳过 PDF 预览，`uncertainty` + `previews.warnings` 各一条 |
| PDF 抽取（`fitz`/`pypdf`/`PyPDF2`/`pdfplumber`） | 任一 | 材料是 PDF 时必需 | 全缺时按 D3：由 Agent 抽文本后重跑 |

安装：`pip install python-pptx matplotlib pillow numpy reportlab`
（**包内不带任何二进制资源**：模板由 `templates/*.json` 参数化，图表/预览全部运行时生成。）

## 5. 输入格式（`case.json`）

```json
{
  "case_id": "case-xxx",
  "title": "案例标题",
  "inputs": {"task_md": "task.md", "material": ["paper.md", "results.csv"]},
  "spec": {
    "audience": "组会|答辩|评审|同行",
    "duration_minutes": 15,
    "max_slides": 8,
    "template": "default",
    "template_pptx": "可选的母版.pptx",
    "starting_deck": "可选的起始稿.pptx",
    "style": {"colors": {"accent": "#2E7D32"}, "footer": {"text": "页脚"}}
  },
  "output_contract": {"case_id": "string", "deck": "dict"}
}
```

- `material[]` 里是**相对 case.json 的路径**（也接受绝对路径）；`--input-dir` 可改基准目录；
- `output_contract` 声明的字段会被**逐项回显到 `result.json` 顶层**（四形态空值，禁 `null`）；
  其**形态**必须是对象或字段名列表——**写成字符串会让回显被整体静默跳过**
  （实测缺口 S2，见 `references/FAULT-MATRIX.md` §2，CP0 守卫会提前报警）。

## 6. 命令索引与退出码

| 入口 | 关键参数 | 用途 | 退出码 |
|-|-|-|-|
| `main.py` | `--case --out [--input-dir --template --max-slides --edit --no-chart --version --draft --verbose]` | 端到端 CP1–CP4 | 0 success / 1 partial / 2 输入不可读 |
| `result_tool.py` | `--result --out-dir [--case --envelope]` | G1–G8 契约门 | 0 通过 / 1 有未过项 / 2 不可解析 |
| `selftest.py` | `--out [--case --pptx --slides]` | 产物自检 | 0 全过 / 1 有未过项 |
| `evidence_check.py` | `--claim --material` | 单条主张数字核验 | 0 全找到 / 1 有缺失 |
| `make_examples.py` | `[--work-dir --dry-run]` | 重建示例产物 | 0 / 1 |
| `fault_inject.py` | `--list / --pkg --work [--only --shape --with-recovery --report-*]` | 注入台 + 恢复演练 | 0 一致 / 1 有偏差或静默 / 2 环境不可用 |
| `fault_inject.py --guard` | `--pkg --case [--template]` / `--out` | 运行前体检 / 运行后核对 | 0 干净 / 1 有 BLOCKER 或 WARN |

> **只有 exit 0 才算这次运行"干净"**。exit 1 必须读 `result.json.uncertainty` 再决定是否补件重跑；
> exit 2 表示输入侧问题，重跑无用。

## 7. 输出与验收

一次成功运行（示例案例，`max_slides=6`）实测产出 **25 个文件**：
`result.json`（18 个顶层键）、`evidence_map.md`、`evidence_map.json`、`changelog.jsonl`、
`manifest.json`、`logs/run_*.log`、`work/deck.pptx`（6 页）、`work/plan.json`、
`work/material_view.json`、`work/chart_results.csv.png`、`work/table_cache/results.csv`、
`work/preview/slide_01..06.png` + `preview.pdf`、输出根 `preview/` 的同名副本。

验收三层（**互不顶替**）：

| 层 | 命令 | 查什么 |
|-|-|-|
| 产物层 | `selftest.py` | 文件在不在、deck 能不能重开、页数对不对、预览有没有 |
| 契约层 | `result_tool.py` | G1–G8：字段齐不齐、契约回显、禁 null、证据行数=页数、备注非空、sha256 |
| 内容层 | `evidence_check` + `plan_lint` | 页面数字能否回指材料、页面纪律（角色/要点数/长度） |
| **留痕层（本版）** | `fault_inject.py --guard --out` | 降级有没有逐条留痕、图表有没有静默消失、状态与产物是否自洽 |

## 8. 限制与已知问题（诚实声明）

1. **7 条静默缺口未根治**（本版测出来并给了补救，但没改 `main.py`）：
   S1 表解析不出时图表静默消失；S2 契约非对象时回显整体跳过；S3 母版不存在时静默换内置；
   S4–S7 参数形态错误 / 缺 `python-pptx` / 缺 `Pillow` 时硬崩且不写 `result.json`。
   逐条见 `references/FAULT-MATRIX.md` §2。
2. **注入台覆盖不到**：并发/中断、畸形但合法的 PPTX、GB 级材料、真机 Office 渲染、平台预检。
   见 `FAULT-MATRIX.md` §5，**没有实测证据的不要当结论引用**。
3. **预览 ≠ Office 导出**：无 PowerPoint/LibreOffice 时预览由 PIL/reportlab 近似渲染，
   文件名与 `previews.method` 均已如实标注。
4. **`--draft` 只跳过 PDF 预览**，不跳过 PNG（Pillow 仍必需）。
5. **页数与角色分配是确定性的**：同输入同 spec 下页序/角色不变（实测双跑仅时间戳不同）；
   换来的是"可复现"，代价是不会自动做审美层面的再平衡。

## 9. 失败处理（一页速查）

| 症状 | 先看哪 | 处置 |
|-|-|-|
| 没有 `result.json` | `--guard --out` 报 BLOCKER | 多半是 CP0 该拦的：坏参数/缺库（`FAULT-MATRIX.md` §2 S4–S7） |
| `status=partial` | `result.json.uncertainty` | 逐条看降级原因；补件或换参数后重跑 |
| `status=failed` + `exit=2` | `result.json.error` | 输入侧问题，重跑无用，先修 `case.json`/材料 |
| 契约字段没回显 | 先确认**传了 `--case`** | 再确认 `output_contract` 是对象/列表形态（S2） |
| 结果页没图 | `figure.kind` 与 `figure.note` | 有 note = 正常降级；无 note = 静默丢图（S1），用 `--no-chart` 显式化 |
| deck 打不开 | `selftest` 的 `pptx_reopen` | 复制 `work/deck_<v>.pptx` 回退后重跑 |
| 改了模板母版 | 不该发生 | 母版只读；需要换样式改 `templates/*.json` 或 `spec.style` |

## 10. 生态与复用

- `scripts/fault_inject.py` 可以**脱离本包复用**：它只依赖两个公开产物
  （`result.json` 的 `status/uncertainty/change_records/evidence/deck`，
  以及 `work/material_view.json` 的 `tables/sections`），不 import 本包任何模块；
  把它复制到别的 Skill 仓库，改 `IMPORT_NEEDS` 与 `FAULTS` 即可复用同一套判据。
- `references/FAULT-MATRIX.md` 的判读口径（product / stdout-only / none 三级留痕）
  可以当"可靠性自证模板"直接套用。
- `templates/*.json` 与 `result_envelope.json` 参数化，换模板不改代码。
- 示例案例（`examples/`）是虚构材料，明确标注"示例，非正式案例"，**不含任何正式案例答案**。

## 11. 维护

1. 改了脚本或模板 → 跑 `python "$SKILL_DIR/scripts/make_examples.py"` 重建 `examples/output/`
   （它会自动把机器绝对路径净化成相对路径）；
2. 改了失败分支 → 跑
   `python "$SKILL_DIR/scripts/fault_inject.py" --pkg "$SKILL_DIR" --work <包外> --with-recovery`
   并更新 `references/FAULT-MATRIX.md` 的矩阵（**只写实测值，不写预期值**）；
3. 每次提交前：`python validate_pkg.py <包>`（≤50 文件 / ≤2MB / 扩展名白名单 / UTF-8 /
   无绝对路径 / frontmatter），再按 `TEST.md` 的 12 组跑一遍。
