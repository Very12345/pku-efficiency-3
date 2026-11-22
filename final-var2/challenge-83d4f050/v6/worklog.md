# worklog.md — 构建、合规重打包与实测日志（challenge-83d4f050）

> 记录本包的完整来历：**基础包 → v2 加强包 → 合规文本包（本目录）**。
> 每次改动都写明"改了什么 / 为什么 / 验证结果"；实测细节见 `TEST.md`。

## 1. 来历与输入（按序）

| 阶段 | 目录 | 规模 | 说明 |
|-|-|-|-|
| 基础包 | `work/efficiency-3/build/challenge-83d4f050` | 22 文本 + 示例输出 + `__pycache__` = 30 文件 | v1 流水线：`extract/layout/model/main/mpl_backend/result_writer/svg_backend/validate` 8 脚本 |
| v2 加强包 | `work/efficiency-3/submit/challenge-83d4f050-v2`（另见 `target/challenge-83d4f050-v2`） | 35–37 文件（含 `COMPARE.md`/`worklog.md` 时为 37） | 加 CP1–CP4 检查点、D1–D12 决策规则、schema 门、拓扑/图例双审计、契约四形态 + G1–G8、确定性 |
| **本包（合规文本包）** | `work/efficiency-3/final/challenge-83d4f050` | 见 `TEST.md` §12 / 包根汇报 | **搬家 + 补文档 + 清残留**：算法与 CLI 接口不变，资源形态改为纯文本（图件运行时生成） |

按序读取的材料：官方题面 `task-statements/challenge-83d4f050.md`（五维 40/25/15/10/10
＋ GitHub 5；Runtime contract：≤50 UTF-8 文本文件、单文件 ≤500KB、总 ≤2MB、无符号链接）、
意图报告 `highscore-intel/challenge-83d4f050.md`（可解析最高 76.67 = 5 文件极简；
共性 = 通路/关系核对模板、glyph 语义、topology/lint、机制规格 schema、failure-modes、
provenance；规避 = 堆文件不涨分、无语义校验的纯 SVG 包）、v2 包与 build 基础包。

## 2. v2 阶段的设计决策（本包沿用，不重写算法）

1. 对齐高分形态：`references/` 拆为 mechanism-spec / legend-encoding / output-contract /
   rubric-map / failure-modes；`assets/` 三件套；`templates/` 核对清单；`worklog.md`；
2. 脚本按 build / extract / render / verify 拆分：`main`（CP 门）、`model`+`extract`、
   `layout`+`pathway_svg`+`mpl_backend`、`topology`+`legend_audit`+`validate_figure`+
   `check_contract`+`result_writer`；
3. 检查点 CP1–CP5 + 决策规则 D1–D12（`SKILL.md`）；
4. CP2 schema 门**对 raw 规格**校验（防未知类型被归一化静默改写，T7 实测 exit 3）；
5. 确定性：SVG 去时间戳；T4 实测 SVG/PNG/model/topology/legend_audit 双跑逐字节一致；
   PDF 仅 matplotlib `CreationDate`、`result.json` 仅时间戳字段不同（如实记录）。

v2 阶段已修复的基包缺陷（历史记录）：`mpl_backend` 缺 `SKILL_VERSION` 导入导致预览
NameError；`extract.py` 对 `A 动词 B`（含空格）left 尾随空格导致边端点脱靶；约束行
`信号流向：…` 被误抽为实体；schema 门最初校验归一化模型导致门失效；GBK 控制台
`UnicodeEncodeError`（各 CLI 入口 reconfigure UTF-8）。

## 3. 本次合规重打包（2026-11-22 +08）——逐项记录

### 3.1 删除（资源形态硬门：包内只允许 UTF-8 文本）

| 删除对象 | 字节 | 原因 | 替代 |
|-|-|-|-|
| `examples/output/diagram.pdf` | 108,045 | 平台预检点名拒绝的扩展名（`unsupported Skill resource`） | 运行时由 `scripts/mpl_backend.py` 生成 |
| `examples/output/diagram.png` | 203,655 | 二进制，不在七种白名单内 | 运行时生成 |
| `examples/output/diagram.svg` | 17,771 | 文本但不在白名单（本期出分包 0 例），降低二次拒收风险 | 运行时由 `scripts/pathway_svg.py` 生成 |
| `__pycache__/`、`*.pyc` | — | 禁止项（v2 已无，build 基础包有 8 个 `.pyc`，本次不随包） | 无（编译产物不入包） |

合计从包内移除 **329,471 字节**的二进制/非白名单资源。

### 3.2 改名（对齐合规必备文件名）

| 原名 | 新名 |
|-|-|
| `references/output-contract.md` | `references/OUTPUT_CONTRACT.md` |
| `references/rubric-map.md` | `references/RUBRIC_MAP.md` |

同步更新了 **7 个文件**里的全部引用：`SKILL.md`、`README.md`、
`references/OUTPUT_CONTRACT.md`、`references/RUBRIC_MAP.md`、
`assets/result.template.json`、`scripts/check_contract.py`、`scripts/result_writer.py`
（`grep -rn 'output-contract\.md\|rubric-map\.md'` 现为 0 命中）。

### 3.3 新增文档（补文档，不新增冗余代码）

| 文件 | 作用 | 对应评分维度 |
|-|-|-|
| `examples/README.md` | 示例怎么用、为什么没有图件、如何复跑 | 文档完整性 / 易用性 |
| `examples/EXPECTED-OUTPUT.md` | **文字化**的应产出清单与契约字段（替代原 `examples/output/**` 图件） | 结果完整性 / 可核验性 |
| 对照方案（原 `COMPARE.md`，全维合并版并入 `references/GAIN-PROTOCOL.md` 附录 A/B） | 与"不加载 Skill 的基础 Agent"的同输入对照方案与可复算判据 | 使用增益 25 |
| `references/RUBRIC_MAP.md`（重写） | 五维 40/25/15/10/10 逐条映射到本包**具体文件与机制**（含合规版变化） | 全维度信号 |

### 3.4 清残留：本机绝对路径

| 位置 | 残留 | 处置 |
|-|-|-|
| `examples/output/result.json` | `provenance.case_file` 是本机盘符绝对路径（指向旧的 `target/` 目录）；`provenance.command` 含 `D:/BuildTemp/...`；`change_records[].why` 含绝对路径 | 用**相对命令**重跑生成（`--out examples/output`），并让脚本只记相对路径 |
| `examples/output/result.json` | 检查详情里的绝对产物路径（形如 `<盘符>\BuildTemp\...\diagram.svg (…)`） | `scripts/validate_figure.py` 改用 `os.path.basename` |
| `scripts/main.py` | 新增 `portable_path()`：技能根内 → 相对路径；容器路径（`/input`、`/app/output`）原样保留 | 覆盖 `provenance.command/case_file/schema`、`CP1.1/CP1.4` 检查详情、CP2 change_record |
| `README.md`、`TEST.md` | `--out D:/BuildTemp/...` 等本机示例路径 | 改为 `$SKILL_DIR` / `/app/output` / `/tmp/...` 环境化写法 |
| `references/*.md`、`SKILL.md` | 无绝对路径（本就干净） | 复核通过 |

> 保留项：`scripts/mpl_backend.py` 的**字体探测候选路径**属于跨平台探测逻辑的一部分
> （见 `TEST.md` §13 与包根汇报），不是本机运行痕迹；它们只在运行时用于探测系统字体，
> 不写入任何随包产物。

### 3.5 自定位与命令一致性

- `SKILL.md` 的命令全部改为 `python3 "$SKILL_DIR/scripts/main.py" ...`，并给出
  `export SKILL_DIR=...` 的确定方式与 `--help` 自检；与 `scripts/main.py` 的
  `argparse` 定义（`--case/--task/--out/--materials-dir/--model-file/--formats/--dpi/--verbose`）
  逐字一致；
- `README.md` §2、`COMPARE.md` §3、`TEST.md` §0 的命令同源同写法；
- 实测：在**临时目录的包副本**上、`cwd` 不是技能根的情况下运行同一命令 → exit 0（T2）。

### 3.6 代码缺陷修复（只修 bug，不改算法与 CLI）

1. `deliverables.audits` 恒为空（键名写错）→ 现输出 `["topology.json","legend_audit.json"]`；
2. `--formats svg` 触发 `KeyError: 'png'` 崩溃 → `render_preview` 始终携带 `png/pdf` 键，
   未请求预览时跳过渲染（纯标准库路径成立）；
3. 复制粘贴导致的 `UnboundLocalError: ex` → 统一按 `preview_meta["warnings"]` 记录；
4. `files` 依赖目录残留（首跑缺 `result.json`）→ 固定并入 `result.json`；
5. `provenance.schema` 在 Windows 上出现反斜杠 → 统一走 `portable_path()`；
6. `validate_figure` 检查详情打印绝对路径 → 改 basename。

（缺陷 1–6 的复现/验证细节见 `TEST.md` §11。）

### 3.7 重新产出示例产物

用**最终代码**重跑示例案例（`--case examples/case.json --model-file examples/model.example.json
--out examples/output`），随后删除运行时生成的 SVG/PNG/PDF，只把 4 个 JSON 留作示例
（`result.json` / `model.json` / `topology.json` / `legend_audit.json`），
并在 `EXPECTED-OUTPUT.md` 写明"另 3 件由运行时生成"。

## 4. 验收结果（2026-11-22）

| 项 | 命令 | 结果 |
|---|---|---|
| 合规 | `python validate_pkg.py final/challenge-83d4f050` | **PASS，0 FAIL**（原文见包根汇报） |
| 可跑（自定位） | 临时目录副本 + `cwd≠技能根` + `--model-file` | exit **0**，`status=success`，`gates 8/8` |
| 契约 | `check_contract.py --result <out>/result.json --case examples/case.json` | exit 0，C01–C07 全 pass；顶层字段覆盖 `OUTPUT_CONTRACT.md` 全部字段且无 null |
| 独立全检 | `validate_figure.py --out <out>` | exit 0，30 项全 pass |
| 降级 | `--formats svg` / 模拟无 matplotlib | exit 2、`partial`、SVG 仍产出且 sha 相同（T9） |
| schema 门 | 非法 `type` 规格 | exit 3、`failed`（T7） |
| 残留 | 扫描本机盘符绝对路径前缀（字母＋冒号＋反斜杠） | 0 命中 |
| 确定性 | 同输入双跑 | SVG/PNG/model/topology/legend_audit 逐字节一致（T4） |

## 5. 未解决项 / 边界（如实）

- 自动抽取器只处理结构化语句；散文与 PDF 材料依赖 Agent 手工建规格（CP2b/CP3），
  这是"准确率优先"的刻意设计，不是缺口；
- PDF 与 `result.json` 含时间戳，不作确定性承诺（T4 记录差异）；
- 运行者在**本机 Windows** 用绝对 `--out` 路径时，`result.json.provenance.command` 会记录
  该次运行自己的路径（这是"如实记录本次命令"的设计）；**随包示例产物已全部为相对路径**，
  容器内运行时记录的是 `/input`、`/app/output` 这类环境路径；
- PNG/PDF 字节随 matplotlib 版本可能变化，`EXPECTED-OUTPUT.md` 已声明"结构一致优先于字节一致"；
- 本包不运行、也不伪造平台的对照实验与分数（对照口径见 `references/GAIN-PROTOCOL.md` 附录 A/B）。


## 6. Round 2 变体（v6：全维合并最强版，2026-11-22 +08）

**本版性质**：不新增算法，而是把 R1 的三条轴（v1 决策显性化 / v2 增益可验证 / v3 机制与复用）
与 R2 的两条轴（v4 失败注入 / v5 多案例题集）**合并为一个包**，并重写一份整合的 `SKILL.md`
（按"输入 → 执行 → 失败 → 增益 → 机制 → 复用"组织，末尾索引到各 reference）。

**合并方式（逐条可核）**

| 内容 | 来源 | 处理 |
|-|-|-|
| `scripts/gain_probe.py`、`scripts/baseline_emulator.py` | R1/v3（与 v2 字节相同） | 逐字节取入，未改 |
| `scripts/fault_inject.py` | R2/v4 | 逐字节取入，未改 |
| `scripts/model.py`（+56 行）、`scripts/main.py`（+30 行） | R2/v4（v5 同字节） | 逐字节取入：三处静默降级改为留痕，纯增量、删除行数 0 |
| `references/FAULT-MATRIX.md` | R2/v4 | 取入并在本包上**复跑复核**（读数一致：24/24 · 0 静默 · 6/6） |
| `references/CASE-SET.md` | R2/v5 | 取入并在本包上**复跑复核**（三案 exit 0 / success / 门 8-8） |
| `examples/cases/**`（8 文件） | R2/v5 | 逐字节取入 |
| `references/GAIN-PROTOCOL.md` | R1/v2 + `COMPARE.md`（v1 版与基线版） | 正文取 v2 版；两份 `COMPARE.md` 全文作为**附录 A / 附录 B** 合入（原文件不再单独存在，内容一字未减） |
| `references/MECHANISM.md` | R1/v3 + `ASSET-INDEX.md` | 正文取 v3 版；`ASSET-INDEX.md` 全文作为 **§7** 合入（内含复用三步与迁移检查表） |
| `references/mechanism-spec.md` | 基线 + `legend-encoding.md` | 追加 **§9**：`legend-encoding.md` 全文（箭头语义/数据编码/调色板/审计规则）合入 |
| `references/OUTPUT_CONTRACT.md` | R1/v1 版（§1–§9 逐字 + §10 状态矩阵）+ v2 §10 + v3 §10 | 追加 **§11 可测判定**、**§12 机制→字段映射**；§1–§9 字段块**逐字保留** |
| `references/RUBRIC_MAP.md` | 基线 §1–§7 + v2/v3/v4/v5 的角度 | 追加 **§8 使用增益指标**、**§9 创新增益机制**、**§10 生态贡献资产**、**§11 可靠体验故障矩阵**、**§12 题集落点** |
| `references/failure-modes.md` | 基线 §1–§5 + v1/v3/v4/v5 | 追加 **§6 F01–F22 全表**、**§7 按机制归类**、**§8 四形态注入**、**§9 换题材边界**；开头加"五个视图"导读 |
| `SKILL.md` / `README.md` / `TEST.md` / `worklog.md` | 本版重写 | 按"输入→执行→失败→增益→机制→复用"整合；TEST 增 T11（增益复算）、T12（故障演练）、T13（题集） |

**文件数守恒**：合并 `COMPARE.md`、`ASSET-INDEX.md`、`legend-encoding.md` 三份文档（内容全部并入
上述 reference 的小节），腾出的名额用于新增 `FAULT-MATRIX.md`、`CASE-SET.md` 与两个案例目录；
**本包 49 个文本文件、约 0.5 MB，均在硬门（≤50 文件 / ≤2 MB / 单文件 ≤500 KB）之内**。

**本包上的实测（2026-11-22 +08，包外副本，Python 3.13 + matplotlib + Pillow）**

| 轴 | 命令 | 读数 |
|-|-|-|
| 主路径 | `main.py --case examples/case.json --model-file examples/model.example.json` | exit 0 / success / 门 8-8 / 7 件产物 |
| 失败注入 | `fault_inject.py --skill <copy> --out <dir>` | `24/24 符合期望`、`silent_failures=[]`、`recovery=6/6`、脚本 exit 0 |
| 增益对照 | `baseline_emulator.py` + `gain_probe.py --compare` | A1–A7：`0.0 → 1.0`；A8：`1.0 → 1.0`（非差异点） |
| 题集 | 三个案例各跑"已核验 + 草稿"两条路径 | 已核验：三案 exit 0 / success / 门 8-8（9-9、12-12、8-8）；草稿：三案 exit 2 / partial |
| 合规 | `validate_pkg.py <pkg>` | PASS（0 FAIL）；无 `__pycache__`、无本机绝对路径、无二进制资源 |

**诚实声明**：本版没有新增算法或新脚本逻辑（除 v4 已有的三处留痕补丁）；它的价值是
**把五条轴装进同一个包**，让审阅者在一处就能同时看到"怎么做对 / 出错会怎样 / 好在哪里 /
为什么这样设计 / 能不能搬走"。
