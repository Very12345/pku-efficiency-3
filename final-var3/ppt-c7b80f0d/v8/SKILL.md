---
name: paper-to-academic-ppt
description: 把论文/研究材料转换成主线清晰、证据可追溯、可编辑的学术汇报 PPT，并把 result.json 的 output_contract 契约做成"四形态 × 边界值"的可跑矩阵。本版新增 scripts/contract_matrix.py：对每个单元注入一份完整 case.json（① 字段→类型提示 / ② 字段→说明 / ③ 布尔开关 / ④ 字段清单，各自叠加空串、空数组、0、超长、非法类型、缺字段等边界值），跑**未经修改的**端到端流程，逐行记录实测 exit / status / 契约回显 / 是否静默通过；实测 28 个单元：28/28 写出 result.json、0 崩溃、修复前 5 条静默通过（声明 true 回显 false、声明 0 回显空串、清单非法元素被丢弃…）经 3 处纯增量修复后降为 0 条，且 5 个"声明不全"单元被内部契约门点名。Use when a task asks to turn a paper or research material into an academic slide deck (论文转PPT、学术汇报PPT、slides from paper、presentation from paper) and the output must satisfy a case-declared result contract, especially when /input/case.json carries output_contract and /app/output must contain the editable deck, previews and a field-complete result.json.
---

# 论文转学术 PPT（契约四形态 × 边界值矩阵版 · paper-to-academic-ppt）

本题的评分产物只有一个：`result.json`。它的字段不是"爱写不写"，而是案例
`case.json` 里 `output_contract` **声明**出来的四种形态之一。声明形态与边界值一旦踩到
边角（空串、空数组、0、超长、非法类型、缺字段），失败往往表现为**静默通过**——
流程 exit 0、内部自检说 OK、字段也确实在，但回显的类型或值已经与声明不是一回事。
本版把这件事做成一张**可跑的矩阵**：每种形态 × 每组边界值各注入一次，跑真实流程，逐行留证。

```
CP4 契约矩阵（本版新增） →  CP1 蓝图 lint  →  生成  →  CP3 导出检查
contract_matrix.py            spec_lint.py      main.py   export_check.py
28 个注入单元 × 一次真跑      BL-1…BL-4                     G1–G8 + 19 字段面
```

不负责：论文精读结论、科研绘图美化、学术写作润色；不使用预制答案：正式运行只依据案例
实际提供的文件，`examples/` 仅说明接口。

## 1. 触发条件与适用边界

适用：把论文/研究材料变成"主线成立、页级可追溯、模板内可编辑、有预览"的学术汇报；
以及**案例声明了 `output_contract`**、交付前需要确认"声明里的每个形态都不会静默走样"的场合。

触发词：论文转PPT、学术汇报PPT、slides from paper、presentation from paper、
"output_contract 回显"、契约字段、result.json 字段校验。

不适用：没有案例契约、只想要一份随手 PPT 的场合（此时按 `OUTPUT_CONTRACT.md` §1 的
19 个顶层字段自我约束即可，不必跑矩阵）。

## 2. 输入 / 输出 / 自定位

| 方向 | 位置（以环境实际挂载为准） | 内容 |
|-|-|-|
| 输入 | `/input/case.json` | `case_id`、**`output_contract`（本版主轴）**、材料/模板定位、受众/时长/页数 |
| 输入 | `/input/task.md` | 任务说明（存在时读取，advisory） |
| 工作 | `/app/work` | 中间件：抽取文本、图片、`deck-spec.json` |
| 输出 | `/app/output` | `result.json`（唯一评分产物）、`academic_deck.pptx`、`preview-approx-*.png`、`evidence_mapping.md`、`evidence_map.json`、可选 `chart-*.png/.svg` |
| 输出 | 任意（矩阵探针目录） | `cells/<单元>/case.json`、`cells/<单元>/out/result.json`、`contract_matrix.json`、可选 `CONTRACT-MATRIX.md` |

**自定位**：资源根 = `SKILL.md` 所在目录，记作 `$SKILL_DIR`；所有脚本用
`os.path.dirname(os.path.abspath(__file__))` 解析自身位置，**任意 cwd 都能跑**：

```bash
SKILL_DIR="<SKILL.md 所在目录>"     # 平台安装到 /skills/weekly-skill 时即该路径
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```

`/input` 不存在时先探测 `CASE_PATH` / `OUTPUT_DIR` 或 cwd 下的 `case.json`，
**以实际可读文件为准**。

## 3. 资源清单与 CLI 契约（`$SKILL_DIR`）

| 入口 | 作用 | 参数（**全部保留**） |
|-|-|-|
| `scripts/main.py` | 端到端：CP1 lint → 抽取 → 生成 → 预览 → 导出检查 → result.json | `--case` `--task` `--spec` `--materials` `--out` `--demo` `--verbose` |
| **`scripts/contract_matrix.py`（本版新增）** | **CP4 契约矩阵**：四形态 × 边界值逐单元注入 + 真跑 + 逐行判定 | `--case` `--spec` `--entry` `--python` `--out` `--only` `--timeout` `--emit-md` `--json` `--before-fix` `--redact-paths` `--quiet` |
| `scripts/assetkit.py` | 素材层：材料定位、PDF 抽取、按表格数字重建图 | `--pdf` `--out` |
| `scripts/deckgen.py` | 生成层：模板适配 + 页级排版 + 备注 + 证据映射页 + 形状命名 | 库模块 |
| `scripts/ooxml_kit.py` | OOXML 层：主题字体、分层命名、容器健全检查、命名审计 | 库模块 + `__main__` 审计 |
| `scripts/spec_lint.py` | **CP1**：deck-spec 结构校验（BL-1…BL-4） | `--spec` |
| `scripts/export_check.py` | **CP3**：契约回显 + OOXML + 命名 + 证据表一致性（G1–G8） | `--result` `--out-dir` `--case` |
| `scripts/check_contract.py` | 契约顶层字段覆盖核对（矩阵复用它读 §1 的 19 个字段名） | `--result` `--contract` `--case` `--quiet` |
| `scripts/preview.py` | PIL 近似预览 | 库模块 |
| `scripts/make_template.py` | **运行期生成**回退模板 `.pptx` | `--out` `--name` `--no-starter` |
| `scripts/make_synthetic_inputs.py` | **运行期生成**合成夹具 | `--out` |
| `scripts/cli_io.py` | 控制台加固 | 库模块 |

| 文档 / 资源 | 作用 |
|-|-|
| `references/OUTPUT_CONTRACT.md` | result.json 顶层字段清单 + 四形态回显 + G1–G8（**必读**，字段块逐字未改） |
| `references/CONTRACT-MATRIX.md` | **本版主轴**：28 个单元逐行实测 + 静默通过清单 + 修复登记 + 未覆盖声明（由 `--emit-md` 现场生成） |
| `references/contract-matrix-data.json` | 矩阵实测原始记录（修复后） |
| `references/contract-matrix-before-fix.json` | 同一矩阵在**修复前**的对照记录（5 条静默通过的证据） |
| `references/slide-blueprint.md` | 论文→页面蓝图映射 + deck-spec schema + 逐页证据表格式 |
| `references/RUBRIC_MAP.md` | 五维评分 → 本包落点 + 对照协议 |
| `references/failure-modes.md` | 失败模式与降级策略 + 第五类"契约形态"细化 + 退出码语义 |
| `references/layer-naming.md` | PPTX 分层命名规范 |
| `examples/` | 最小示例（合成案例，标注"示例，非正式案例"） |

依赖：`python-pptx` 必需；`Pillow` 用预览；`matplotlib` 可选（重建图）；PDF 解析三选一。
逐级回退并如实记录（`references/failure-modes.md` §2.3）。

## 4. 执行阶段 M0–M6（检查点 CP1 / CP3 / **CP4**）

### M0 定位与读题
1. 读 `task.md`（若存在）与 `/input/case.json`，记录 `case_id`。
2. **先把 `output_contract` 抄成一张清单**：每个字段名 + 声明的形态（① 类型提示 / ② 说明 /
   ③ 布尔 / ④ 名称清单）+ 声明值本身。这张清单就是后面逐字段核对的对象。
3. 定位 `$SKILL_DIR`；所有脚本用绝对路径调用。

### M1 读实际文件（不许按标签假设内容）
4. 抽取材料：
   ```bash
   python "$SKILL_DIR/scripts/assetkit.py" --pdf "<材料路径>" --out /app/work/extract
   ```
5. 记录元信息与各章页码（M2 的证据定位要用真实页码）。

### M2 蓝图规划（论文结构 → 页面骨架）
6. 按 `references/slide-blueprint.md` §1 重写为 问题→方法→证据→结论→局限 页序。
7. 抽页级证据：图/表/公式编号、页码、图注、数值与单位**逐字**带出；区分原生图与
   可从表格重建的图（`reconstructed_chart`）。

### M3 写 deck-spec.json + **CP1**
8. 按 schema 写 `/app/work/deck-spec.json`：每页 `claim` + 短语化 `bullets`（≤6 条、
   CJK ≤110 字）+ `figure/table` + `notes` + `evidence`（ref + page + quote）；
   无法定位 → `evidence_gap: true`。
9. **CP1 检查点**：
   ```bash
   python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json
   ```

### M4 构建可编辑源
10. 端到端入口：
    ```bash
    python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
      --spec /app/work/deck-spec.json --out /app/output
    ```
11. 模板三铁律：只填占位符、不碰 master、布局按名匹配→索引回退→内置版式；
    `template_mode="replace"` 记录 `starter_slides_removed`；页数超限按 P07 处理。

### M5 渲染与 **CP3**
12. 无 Office 引擎时预览为 PIL 近似（`preview-approx-*.png`，文件名 + `kind` +
    `rendered_with` 三处标注）。
13. **CP3 导出检查**（交付门）：
    ```bash
    python "$SKILL_DIR/scripts/export_check.py" --result /app/output/result.json \
      --out-dir /app/output --case /input/case.json
    ```

### M6 写 result.json + **CP4 契约矩阵** + 自评
14. result.json 的字段清单以 `references/OUTPUT_CONTRACT.md` §1 为准（19 个顶层字段）：
    ```bash
    python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
      --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case /input/case.json
    ```
15. **CP4 契约矩阵**（本版新增）——交付前用它替代"我觉得边界没问题"：
    ```bash
    python "$SKILL_DIR/scripts/contract_matrix.py" --out "<探针目录>" \
      --emit-md "<探针目录>/CONTRACT-MATRIX.md"
    # exit 0 = 每个单元都写出 result.json 且没有静默通过；exit 1 = 有静默通过（必须先处理）
    ```
    矩阵按 §5 的 P 规则解读：`match` / `mismatch-recorded`（被记录或被门拦住）/
    `silent-pass`（既没纠正也没记录 → 必须修或记录）。
16. 按 `references/RUBRIC_MAP.md` 五维自评，补足可复跑证据（测试记录 → TEST.md）。

预算纪律：总 64 次模型请求 / 900 秒 / 单响应 16384 tokens（含推理）；脚本运行秒级
（单次端到端实测 1.3–1.5 s；28 个单元的矩阵约 50 s），不占模型预算大头。

## 5. 决策规则 P01–P12（契约形态 / 材料 / 模板 / 依赖 / 状态）

| # | 情形 | 决策（做什么 → 记录在哪） |
|-|-|-|
| P01 | 矩阵报出 `silent-pass` | 视为**未定级契约缺陷**：按单元里的"期望 vs 实测"改代码或改成如实记录（二选一，不许放着） → 重跑矩阵 + `references/CONTRACT-MATRIX.md` §5 增一条 |
| P02 | 声明值是**布尔**且字段名不是语义字段 | 如实回显声明的布尔（true→true、false→false），不得回退成空串或取反 → `result.<field>` |
| P03 | 声明值是**数字**（含边界 0） | 如实回显数字，不塌缩成空串 → `result.<field>` |
| P04 | 声明值是 `null` / 非法类型 | 顶层**禁止出现 null**（D10 口径）：给容器空值，并在 `uncertainty` 记录"声明的值本身是 null" → `result.output_contract` + `uncertainty` |
| P05 | `output_contract` **整个容器非法**（字符串/数字）或显式 `null` | 回显空对象 + **写一条 uncertainty**（不得静默当空契约）；顶层 19 字段仍须齐全，否则自检会点名 → `uncertainty` + 门 |
| P06 | ④ 清单形态里混入非字符串元素 | 跳过该元素但**写一条 uncertainty**（不得静默丢弃） → `uncertainty` |
| P07 | 声明"不全"（只声明了少数字段） | 顶层 19 字段的完整性**不能依赖案例声明**：缺失时自检会报 `output contract fields missing` 并 exit 1，此时要么补回显、要么在 uncertainty 说明 → `run_meta.self_check.problems` |
| P08 | 声明字段与真实键同名（`status`/`deck`/`title`…） | **真实值优先**：`setdefault` 语义，声明不得覆盖运行结果 → 矩阵单元 A09/A10/D04 |
| P09 | 材料缺失 / PDF 加密 / 无文本层 | 不补造；`status=failed` 或 `partial`，并如实记录工具与原因 → `sources` + `uncertainty` |
| P10 | 模板不可用/损坏/占位符不足/文件不存在 | 内置 16:9 学术版式回退；需要模板时跑 `make_template.py`（退出码 2 = 后端不可用） → `deck.template.kind` + `uncertainty` |
| P11 | 依赖缺失（matplotlib / PDF 库 / 字体） | 逐级回退并如实记录：重建图跳过、PDF 转文本、字体回退 default；不得伪造产物 → `charts[].chart.reason` + `run_meta` |
| P12 | 状态一致性 | `completed` 只允许"材料可读 + deck 生成 + 预览生成 + 无未标注缺口 + CP1 通过 + **契约面完整**"；任一降级即 `partial`/`failed` → `status` + `uncertainty` |

被降级的任何步骤都必须把"发生了什么 + 影响"写进 `uncertainty` / `change_records`。

**与基线 D 编号的对应**（`references/failure-modes.md`、`slide-blueprint.md` 里出现的
D 编号按此行解读，CLI 与退出码语义未变）：P04 = D10、P09 = D1/D2/D3、P10 = D6/D11、
P11 = D8/D9、**P01/P02/P03/P05/P06/P07/P08/P12 为本版新增或细化**。

## 6. 本版实测数字（CP4，可复核）

| 判据 | 实测（28 个注入单元，示例案例为基座） | 复核命令 |
|-|-|-|
| 单元数 / 形态覆盖 | 28 个：① ×14、② ×2、③ ×1、④ ×6、契约容器 ×5 | `contract_matrix.py --out <dir>` |
| 写出 `result.json` | **28/28**（0 崩溃） | 同上报告 `summary.result_written` |
| exit 0 的单元 | **23/28**；5 个"声明不全/非法容器"单元 exit 1，被内部契约门点名 | 同上 `summary.exit_zero` / `caught_by_gate` |
| 契约回显符合期望 | 修复前 21/28 → **修复后 28/28** | `contract-matrix-data.json` vs `contract-matrix-before-fix.json` |
| **静默通过** | 修复前 **5 条** → 修复后 **0 条** | 两份报告的 `summary.silent_pass` |
| 修复前 5 条是什么 | A04 声明 `0` 回显 `""`；A11 声明 `true` 回显 `false`；A12 声明 `false` 回显 `""`；B02 声明 `123` 回显 `""`；D03 清单里的 `7`/`null` 被静默丢弃 | `CONTRACT-MATRIX.md` §3 |
| 顶层契约面（19 字段） | 23/28 完整；5 个"声明不全"单元不完整**且被门点名**（不是静默） | 报告 `contract_surface_complete` |
| ④ 清单形态对语义字段的影响 | `title`/`slides` 等回显为 `[]`（清单形态无法表达语义值），逐单元记录 | 报告 `semantic_echo_in_list_form` |
| 矩阵耗时 | 28 个单元约 **50 s**（每单元一次真跑） | 命令自带计时 |

## 7. 交付前自查清单（逐条）

- [ ] 已读真实 `case.json` / `task.md` / 论文文件；**已把 `output_contract` 抄成字段清单**；
- [ ] deck-spec 按蓝图规划，每页有 `claim`；bullets ≤6 条；`evidence` 或 `evidence_gap` 二选一；
- [ ] 页上数字/单位/方法名/图号与论文逐字一致（抽查 3 处以上）；
- [ ] notes 与页面文字分离，`notes_separated=true`（含封面/收尾页）；
- [ ] `/app/output` 内存在：`result.json`（19 字段 + `case_id`）、`academic_deck.pptx`、
      `preview-approx-*.png`、`evidence_mapping.md` + `evidence_map.json`；
- [ ] `export_check.py` → `valid=true` 且 exit 0；`check_contract.py` → exit 0（无 null）；
- [ ] **`contract_matrix.py` → exit 0，静默通过 0 条**；若有，按 P01 处理后再交付；
- [ ] 案例声明的每个字段都能在 result.json 顶层找到，且类型与声明形态一致（矩阵已逐格覆盖）；
- [ ] status / uncertainty / change_records 诚实；已按 RUBRIC_MAP 五维自评。

## 8. 限制与口径边界

- 矩阵只覆盖 `output_contract` 一个契约面（页级结构、模板、字体、页数上限由
  `spec_lint` / `export_check` 负责）；**未覆盖项逐条列在 `CONTRACT-MATRIX.md` §6**；
- 矩阵的"期望"有两个来源：文档明文 + 文档未明文时的"类型忠实"推定，
  推定项在 `CONTRACT-MATRIX.md` §0 与逐行 note 中标注，不把推定当明文；
- 预览为 PIL 近似渲染，不等同于 PowerPoint/LibreOffice 结果；
- `charts[].chart.file` 携带输出目录绝对路径（已知限制）；模板适配为"占位符级"；
- 包内**只携带文本资源**；模板、预览、示意图等二进制一律运行时生成或由案例提供。

## 9. 维护（改什么就重跑什么）

| 改动 | 必须重跑 |
|-|-|
| `main.py: apply_output_contract()`（或任何影响 result.json 的改动） | `contract_matrix.py`（矩阵是本版回归网）+ `export_check` + `check_contract` |
| 新增 `output_contract` 形态或边界值 | 在 `contract_matrix.py` 的 `CELLS` 加一行（含 `expect`），重跑并把新结果写回 `CONTRACT-MATRIX.md` |
| 新增失败分支 | 同步更新 `references/failure-modes.md` 与 SKILL.md §5 的 P 规则 |
| 版本 | `scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；本版新增 `scripts/contract_matrix.py`，并在 `main.py` 的 `apply_output_contract()` 内做 3 处**纯增量**修复（逐条见 `CONTRACT-MATRIX.md` §5） |
