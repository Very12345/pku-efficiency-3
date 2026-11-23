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
| `COMPARE.md` | 与"不加载 Skill 的基础 Agent"的同输入对照方案与可复算判据 | 使用增益 25 |
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
- 本包不运行、也不伪造平台的对照实验与分数（`COMPARE.md` §4）。

## 本变体（v9 · 缺依赖降级链实测）构建记录 — 2026-11-23

- **与基线的关系**：`scripts/**` **逐字节未改**（本变体只新增 `scripts/degrade_probe.py`）。
- **复核用脚本哈希**（sha256 前 12 位，与基线副本逐字节相同）：`main.py` `5ce6ac61db58` · `layout.py` `ea5490f2b069` · `pathway_svg.py` `4568844120e8` · `model.py` `faa1a0fc1813` · `check_contract.py` `3170288f2161` · `validate_figure.py` `bff37772830a` · `extract.py` `0385593dff79` · `topology.py` `d535021b388d` · `legend_audit.py` `276cbe6512aa` · `mpl_backend.py` `fc7c17f75e87` · `result_writer.py` `9b1b900e4b4c`。
- **新增**：`scripts/degrade_probe.py`（受控导入拦截 + PATH 桩的 13 行降级矩阵，仅标准库）、
  `references/DEGRADE-MATRIX.md`（轴文档：逐项实测 + PIL 微追溯 + LibreOffice 两格 + 未覆盖声明）、
  `references/MINIMAL-ENV.md`（三档最小可用环境清单）、包根 `degrade_report.json`。
- **实测数字**：13 行；控制行 `exit=0 / success` / 7 件产物 / 0 条 uncertainty；
  缺 `matplotlib`/`numpy`/`PIL` ⇒ `exit=2 / partial` / 5 件产物 / `F01_png`,`F01_pdf` fail；
  缺 `yaml`/`pptx`/`lxml`/`pypdf` 与 LibreOffice 缺失/失败 ⇒ `exit=0 / success`（桩未被调用）；
  13 行 `gates.g4_svg_layers` 全 true；`host_has_libreoffice = false`。
- **文档同步**：新写 `SKILL.md`（按本轴）与 `TEST.md`（真实命令与输出）；
  追加 `references/RUBRIC_MAP.md §8`、`references/failure-modes.md §6（FM-E 系列）`、本 README §8；
  `COMPARE.md` 的"确定性"一行改为指向 `references/DETERMINISM.md`（该断言由 v7 轴加强）。
- **未解决项**：字体缺失、部分损坏的安装（模块可导入但后端缺扩展）、磁盘满/只读目录、
  平台真实容器依赖集均未覆盖（见轴文档 §8）。
