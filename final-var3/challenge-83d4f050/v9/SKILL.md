---
name: biological-mechanism-pathway-diagram
description: >-
  把科研机制/通路材料转成可逐条核验的生物机制图与通路图（真实材料抽取实体与相互作用 →
  区室约束确定性布局 → 可编辑分层 SVG 源 + PNG/PDF 预览 → 拓扑与图例/数据编码双审计 →
  契约化 result.json），并且**把"缺依赖时到底会怎样"逐条测出来**：随包提供可运行的
  `scripts/degrade_probe.py`，用受控导入拦截（sys.meta_path）逐个屏蔽
  matplotlib / numpy / PIL / PyYAML / python-pptx / lxml / pypdf，并用 PATH 桩命令模拟
  LibreOffice 缺失与失败，记录每种的**实测**降级形态（退出码 / status / 剩余产物 /
  失败检查项 / 是否留痕），并给出「最小可用环境」清单 `references/MINIMAL-ENV.md`。
  Use when the task asks to draw, generate, edit, re-export or validate a biological
  mechanism map, pathway diagram, signaling cascade, regulatory network or flow
  diagram (figures group of the biology mechanism & pathway challenge), or when you
  need to know which deliverables survive in a thin or partial Python environment.
---

# biological-mechanism-pathway-diagram · v9（缺依赖降级链实测）

机制图的科学性不看图画得多复杂，而看三件事：**每个实体和每条边能否回溯到材料；图例、颜色映射与
图形本身是否自洽；别人能否打开可编辑源文件改一个标签并重新导出。** 而这三件事在**依赖不全的容器**里
还能不能做到，不能靠"我 import 了什么"来猜——本版把依赖面**逐条测出来**。

## 1. 这一版解决什么问题

Skill 常写"只需标准库 + 可选 matplotlib"。这句话要能被证实或证伪，必须回答三个问题：
**① 拿掉某个依赖，退出码/`status` 变成什么？② 还剩哪些产物？③ 降级有没有留痕？**
本版用 13 行真实场景回答，并把结论收敛成三档环境（全文见 `references/DEGRADE-MATRIX.md` 与 `references/MINIMAL-ENV.md`）：

| 档位 | 装什么 | 实测能拿到 | 实测状态 |
|-|-|-|-|
| **A 最小** | 只需 Python 3 | `diagram.svg`（可编辑分层源）· `model.json` · `topology.json` · `legend_audit.json` · `result.json` | exit **2** / `status=partial` |
| **B 完整** | `pip install matplotlib`（带 numpy + Pillow） | A 的全部 ＋ `diagram.png` ＋ `diagram.pdf` | exit **0** / `status=success` |
| **C 只要 SVG** | 同 A，显式 `--formats svg` | 同 A | exit **2** / `status=partial`（**有意降级也被记为 fail**） |

**三条反直觉的实测结论**：

1. **`PIL` 不是"只被尺寸检查用到"**：它在 `matplotlib.colors` 顶层被 `from PIL import Image`，
   所以屏蔽 PIL 的结果与屏蔽 matplotlib **完全一样**（PNG 与 PDF 都没了）。静态看 `import` 会得出错误结论——
   本版用微追溯（`s12`）拿到因果证据。
2. **PNG 失败会连带丢掉 PDF**：`scripts/mpl_backend.py` 先存 PNG 再存 PDF，PNG 抛错则 PDF 永不执行。
3. **LibreOffice 与本包无关**：桩命令（先写调用标记再退出 127）**从未被调用**（标记文件未生成），
   缺失或失败都是零影响——本包的 PDF 由 matplotlib 生成，不 shell out 到办公套件。

## 2. 用途与适用条件

- **适用**：机制图/通路图/信号级联/调控网络/流程图的生成、编辑、重导出与校验。
- **额外适用（本版新增）**：① 你要把本 Skill 放进**一个依赖不全的容器**（评测沙箱、只装标准库的环境）——
  先看 §1 的档位表，知道会拿到什么、`status` 会是什么；② 你要**排障"图出来了但没有 PNG/PDF"**——
  按 `degrade_probe.py` 的单行复现命令定位到底缺哪一个（`--only s03` 就是缺 PIL 那一格）。
- **不适用**：数值统计与统计结论、实验方案设计、论文写作与版式美化（相邻课题负责）。

## 3. 资源形态（纯文本硬约束）

`at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks`；允许扩展名仅
`.md .py .json .txt .csv .yaml .yml`；包内无二进制；图件一律运行时生成；
`degrade_report.json` 是本机实跑的一次降级测量报告（不是预置答案、不是正式案例结果）。

## 4. 命令行总览（自定位，cwd 不是技能根也能跑）

```bash
export SKILL_DIR=/skills/weekly-skill
python3 "$SKILL_DIR/scripts/main.py" --help           # 自检：路径正确
```

| 入口 | 参数 | 说明 |
|-|-|-|
| `scripts/main.py` | `--case --task --out --materials-dir --model-file --formats --dpi --verbose` | 单一主入口；`--formats` 默认 `svg,png,pdf`；`--dpi` 默认 150 |
| `scripts/check_contract.py` | `--result --case` | 独立契约复查（信封 / 禁止 null / 契约回显 / G1–G8） |
| `scripts/validate_figure.py` | `--out --case` | 对输出目录做独立复检（`model.json` 权威） |
| `scripts/degrade_probe.py` | `--skill --case --model-file --work --report --formats --dpi --python --timeout --only --json` | **本版新增**：缺依赖降级链测量器 |

```bash
# 标准一次运行
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /app/output --formats svg,png,pdf --verbose

# 本版新增：降级矩阵（13 行；应退出 0）
python3 "$SKILL_DIR/scripts/degrade_probe.py" \
    --work /tmp/dg --report "$SKILL_DIR/degrade_report.json"
python3 "$SKILL_DIR/scripts/degrade_probe.py" --only s03     # 单行复现「缺 PIL」这一格
```

**退出码**：`main.py` `0=success / 2=partial / 3=failed`；`check_contract.py` `0=通过 / 1=失败`；
`validate_figure.py` `0=全过 / 1=有 fail`；`degrade_probe.py` `0=全部场景跑完 / 2=控制行（全依赖）不通 / 4=参数错误`。

## 5. 降级矩阵实测（13 行摘要）

| 拿掉的东西 | exit | status | 产物数 | 剩余关键件 | 失败检查项 | 留痕 | 判定 |
|-|-|-|-|-|-|-|-|
| 无（对照 `s00`） | 0 | success | 7 | SVG·PNG·PDF·result.json·审计×2 | — | 0 条 uncertainty | 全能力 |
| `matplotlib`（`s01`） | **2** | **partial** | 5 | SVG·result.json·model·审计×2 | `F01_png` `F01_pdf` | 1 条（真实 ImportError 文本） | 预览全失，源件与审计不受影响 |
| `numpy`（`s02`） | 2 | partial | 5 | 同上 | `F01_png` `F01_pdf` | 1 条 | 同 s01 |
| `PIL`（`s03`） | 2 | partial | 5 | 同上 | `F01_png` `F01_pdf` | 1 条 | **PNG 与 PDF 一起丢**（见 §1 结论 1/2） |
| `yaml`（`s04`） | **0** | **success** | 7 | 全部 | — | 0 条 | 无影响（本包不 import） |
| `pptx`（`s05`） | 0 | success | 7 | 全部 | — | 0 条 | 无影响 |
| `lxml`（`s06`） | 0 | success | 7 | 全部 | — | 0 条 | 无影响（用标准库 `xml.etree`） |
| `pypdf`（`s07`） | 0 | success | 7 | 全部 | — | 0 条 | 无影响（不解析 PDF） |
| `matplotlib+numpy+PIL`（`s08`） | 2 | partial | 5 | 同 s01 | `F01_png` `F01_pdf` | 1 条 | 最坏情况仍交付 SVG+审计 |
| `--formats svg`（`s09`，有意） | 2 | partial | 5 | 同 s01 | `F01_png` `F01_pdf` | 1 条（"本次未请求 PNG/PDF 预览"） | 有意降级被记为 fail |
| LibreOffice 缺失（`s10`，PATH 清空） | 0 | success | 7 | 全部 | — | 0 条 | 无影响 |
| LibreOffice 存在但退出 127（`s11`，桩） | 0 | success | 7 | 全部 | — | 0 条 | 无影响；**桩未被调用** |
| `PIL` 微追溯（`s12`，不经主流程） | 1 | — | — | `micro.png` 未写出 | — | — | 机制证据：`matplotlib.colors` → `from PIL import Image` |

**13 行的 `gates.g4_svg_layers` 全部为 `true`** —— 无论缺哪个依赖，可编辑 SVG 源都还在。

**拦截器自证**：每个屏蔽行先在子进程里 `__import__` 被屏蔽模块并记录结果，13 行全部 `importable=false`；
只有确实 `ImportError` 的行才被采信（否则报告标注"该行结论不可用"）。
`s12` 的 traceback 已剔除主机路径行（省略 3 行），保留下来的关键行是
`from PIL import Image` 与 `ImportError: degrade_probe: import of 'PIL' is blocked in this environment`。

## 6. 主流程 CP1–CP5

- **CP1 先读真实文件**：读 `case.json` / `task.md` / 材料目录里每个文件，事实逐条记出处（文件+行号）；
  材料缺失 ⇒ `failed`（退出码 3）。
- **CP2 机制规格 + schema 门**：`extract.py` 出草稿；对**原始未归一化**规格过
  `assets/mechanism-spec.schema.json`（未知类型 → `failed`，不静默改写）。散文/PDF 走 **CP2b**：
  Agent 读材料后手写 `model.json`，用 `--model-file` 重跑。
- **CP3 人工核验**：逐条对照材料原文；`extraction.verified_by_agent=true` + `change_records` 记录改动；
  未核验的自动草稿只能 `partial`（`templates/relation-checklist-template.md` 五表为核验载体）。
- **CP4 布局、渲染与双审计**：`layout.py`（区室带确定性布局）/ `pathway_svg.py`（7 层可编辑 SVG，
  **零第三方依赖**）/ `mpl_backend.py`（**可选的** PNG/PDF 渲染，异常被捕获后写 `uncertainty`）/
  `topology.py`（P01–P08）/ `legend_audit.py`（L01–L08、E01–E02）/ `validate_figure.py`（聚合 M/T/P/L/E/S/F/D）。
- **CP5 写 `result.json` 并自查**：字段与门以 `references/OUTPUT_CONTRACT.md` 为唯一权威；
  `status` 只在"阻断检查全过 + 提取已人工核验 + G1–G8 全过"时为 `success`，缺 PNG/PDF 时必须是 `partial`
  （本版实测：这正是档位 A 的表现，**不要把它当成流水线坏了**）。

## 7. 决策规则（依赖与降级相关，遇情况先查表）

| # | 情形 | 决策 |
|-|-|-|
| D1 | 目标环境依赖不明 | 先跑 `degrade_probe.py` 的对照行与可疑行（`--only s00,s01`）；**不要**只读 `import` 语句猜依赖 |
| D2 | 图出来了但没有 PNG/PDF | 按 `F01_png/F01_pdf` + `uncertainty` 定位：缺 `matplotlib`/`numpy`/`PIL` 三者之一表现**完全一致**（都无 PNG 无 PDF） |
| D3 | 只装了 matplotlib 但缺 Pillow | 视为**没有** matplotlib（实测掉到档位 A）；主张"我们有 matplotlib"前先跑 `s03` 那一格 |
| D4 | 需要 `status=success` | 必须始终请求 `--formats svg,png,pdf`；只请求 `svg` 会有意降级为 `partial`（`s09` 实测） |
| D5 | 容器没有 LibreOffice / PyYAML / python-pptx / lxml / pypdf | 无需处理：实测零影响（`s04`–`s07`、`s10`、`s11`），不要为此加装依赖 |
| D6 | 只能交付 `partial` | 允许，但必须：源文件 + 审计产物齐全、`uncertainty` 写明缺什么、`export_checks` 记录预览缺失原因 |
| D7 | 材料未写上下游方向 | 不臆造：结合类无向边 + `uncertain` |
| D8 | 同名基因/蛋白、同一蛋白多区室 | 拆实体（基因斜体/蛋白正体；按区室拆） |
| D9 | 数据值缺来源 | 阻断：补 `source` 或降为 `assumption` 并进 `uncertainty`（E01/T03） |
| D10 | 机制规格不过 schema 门 | 阻断渲染（`failed`），修正后重跑 |
| D11 | 材料里没有实体/关系 | 明确 `failed`，不画空图凑数 |

## 8. 异常处理与留痕

完整清单见 `references/failure-modes.md`（本版新增 **FM-E1–FM-E6**：缺渲染器的连带效应、
依赖误判、有意降级被记为 fail、partial 被误读为失败、桩/外部命令假设、把"能 import"当"能用"）。
三条通则：**① 任何降级都要有留痕位置**（`uncertainty` / `export_checks` / 检查项 id）；
**② 任何 `fail` 都要落到 `status`**；**③ 不要补造软件状态**（缺就说缺，退出码与 `status` 如实）。

## 9. 反预制答案

`examples/` 里的一切都是**演示**（图内与 `result.json` 带示例标记）。正式运行**禁止**抄示例的实体/边/数值；
`degrade_report.json` 描述的是**本机依赖屏蔽实验**，既不是正式案例结果，也不是分数。
不给自己编造 benchmark 分数，也不声称"在某容器上通过"——除非你**在该容器里**真跑过本版的探针。

## 10. 限制与维护

- **未覆盖**：字体真的缺失（无中文字体）时的渲染、部分损坏的安装（模块可导入但后端缺扩展）、
  磁盘满/只读目录、平台真实评测容器的依赖集（不可见）。全文见轴文档 §8 未覆盖声明。
- 依赖面结论**只对本机实测的解释器/版本组合有效**（CPython 3.13.9 / matplotlib 3.10.6 / Pillow 12.3.0）；
  换大版本后重跑一次探针即可刷新（报告里带 `config.python` / 版本与 `not_covered`）。
- 风格常量集中 `assets/palettes.json`；契约与门集中 `references/OUTPUT_CONTRACT.md`；
  改动后同步更新 `TEST.md` 实测记录并在 `worklog.md` 追加带时间的记录。

## 11. 文件索引

- `references/DEGRADE-MATRIX.md`——**本版轴文档**：13 行逐项实测、PIL 微追溯机制、LibreOffice 两格、未覆盖声明。
- `references/MINIMAL-ENV.md`——**「最小可用环境」清单**：三档位 + 逐依赖判定 + 评测容器里的实际含义。
- `degrade_report.json`——本机实跑的机器可读降级报告（`rows[] / dependency_surface / minimal_environment / not_covered`）。
- `references/OUTPUT_CONTRACT.md`——`result.json` 字段契约 + G1–G8（唯一权威）。
- `references/RUBRIC_MAP.md`——五维评分 → 本包文件与机制；`references/failure-modes.md`——失败模式（含 FM-E 系列）。
- `references/mechanism-spec.md` / `references/legend-encoding.md`——机制规格、命名、区室、箭头语义与数据编码。
- `scripts/`：`main.py`（主入口）、`check_contract.py`、`validate_figure.py`、**`degrade_probe.py`（本版新增）**、
  `extract.py`、`layout.py`、`pathway_svg.py`、`mpl_backend.py`、`topology.py`、`legend_audit.py`、
  `result_writer.py`、`model.py`。
- `assets/`（schema / 调色板 / result 模板）、`templates/relation-checklist-template.md`（CP3 核验载体）、
  `examples/`（最小可运行示例）、`README.md` / `TEST.md` / `COMPARE.md` / `worklog.md`。
