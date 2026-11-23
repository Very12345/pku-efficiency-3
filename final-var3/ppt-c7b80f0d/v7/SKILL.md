---
name: paper-to-academic-ppt
description: 把论文/研究材料转换成主线清晰、证据可追溯、可编辑的学术汇报 PPT，并把"同输入能否得到同一份产物"做成可跑的判据。本版在原有链路（读 OUTPUT_CONTRACT → 写页级 deck-spec 并过 CP1 lint → 模板占位符级适配生成可编辑 .pptx → 重建图与近似预览 → CP3 导出检查 → 回显全部 output_contract 字段的 result.json）之上加一道 CP0：scripts/determinism.py 用独立进程、不同 cwd、不同 PYTHONHASHSEED 连跑 N 次，逐文件 sha256 比对，把差异分成"已解释"（时间戳/时长/zip 成员 mtime/matplotlib SVG 的 dc:date 与随机 id/输出目录身份）与"未解释"，后者非零退出；实测 5 次运行 13 个产物：原始字节 10/13 一致、规范化后 13/13 一致、稳定化后 13/13 字节一致、未解释差异 0。Use when a task asks to turn a paper or research material into an academic slide deck (论文转PPT、学术汇报PPT、slides from paper、presentation from paper), especially when /input/case.json and task.md are present, /app/output must contain the editable deck plus previews, and the reviewer needs to re-run the pipeline and compare bytes.
---

# 论文转学术 PPT（字节级可复现版 · paper-to-academic-ppt）

同一份论文、同一份模板、同一台机器，跑两次应该得到**同一份产物**——否则"按记录复跑出
同一版式"这句话就只能靠自述。本版把可复现性做成一条**可执行的判据**，而不是一句承诺：

```
CP0 复现判据（本版新增）  →  CP1 结构判据  →  生成  →  CP3 交付判据
scripts/determinism.py       scripts/spec_lint.py   main.py   scripts/export_check.py
跨进程/跨 cwd/跨 hashseed     BL-1…BL-4 蓝图 lint    三层生成     G1–G8 部署检查
逐文件 sha256 + 白名单分类
```

**先读契约再规划、先生成再核验、差异必须分类**——这三句话是本版的执行纪律。
不负责：论文精读结论的生成、科研绘图本身的美化、学术写作润色；
不使用预制答案：正式运行只依据案例实际提供的文件，`examples/` 仅说明接口。

## 1. 触发条件与适用边界

适用：把一份科研材料（PDF / 文本文稿）＋ 案例约束（受众 / 时长 / 页数 / 模板）变成
"主线成立、页级可追溯、模板内可编辑、有预览、可复跑"的学术汇报；以及**需要证明
"重复运行得到同一份产物"**的场合（评审复核、回归对比、平台固定案例的多次运行）。

不适用：需要论文本身正确性判断的任务；只有一句话需求、没有材料的场合。

触发词：论文转PPT、学术汇报PPT、slides from paper、presentation from paper、
"复跑一遍结果一样吗"、reproducible deck generation。

## 2. 输入 / 输出 / 自定位

| 方向 | 位置（以环境实际挂载为准） | 内容 |
|-|-|-|
| 输入 | `/input/case.json` | `case_id`、`output_contract`（必须回显的字段）、材料/模板定位、受众/时长/页数 |
| 输入 | `/input/task.md` | 任务说明（存在时读取，advisory） |
| 工作 | `/app/work` | 中间件：抽取文本、图片、`deck-spec.json` |
| 输出 | `/app/output` | `result.json`、`academic_deck.pptx`、`preview-approx-*.png`、`evidence_mapping.md`、`evidence_map.json`、可选 `chart-*.png/.svg` |
| 输出 | 任意（探针目录） | `determinism_report.json`、`run-*/`、`stabilized/`（由 `determinism.py` 写出） |

**自定位**：资源根 = `SKILL.md` 所在目录，记作 `$SKILL_DIR`。所有脚本用
`os.path.dirname(os.path.abspath(__file__))` 解析自身位置，**从任意 cwd 调用都能跑**，
所以命令一律写成：

```bash
SKILL_DIR="<SKILL.md 所在目录>"     # 平台安装到 /skills/weekly-skill 时即该路径
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```

`: /input` 不存在时先探测环境变量（`CASE_PATH` / `OUTPUT_DIR`）或 cwd 下的 `case.json`，
**以实际可读文件为准**，不要假设未实现的路径。

## 3. 资源清单与 CLI 契约（`$SKILL_DIR`）

| 入口 | 作用 | 参数（**全部保留**） |
|-|-|-|
| `scripts/main.py` | 端到端：CP1 lint → 抽取 → 生成 → 预览 → 导出检查 → result.json | `--case` `--task` `--spec` `--materials` `--out` `--demo` `--verbose` |
| `scripts/assetkit.py` | 素材层：材料定位、PDF 文本/图片抽取、按表格数字重建图（PNG+SVG） | `--pdf` `--out` |
| `scripts/deckgen.py` | 生成层：模板适配 + 页级排版 + 备注 + 证据映射页 + 形状命名 | 库模块（无 CLI） |
| `scripts/ooxml_kit.py` | OOXML 层：主题字体、分层命名、zip/XML 健全检查、命名审计 | 库模块 + `__main__` 审计 |
| `scripts/spec_lint.py` | **CP1**：deck-spec 结构校验（claim / evidence / BL-1…BL-4） | `--spec` |
| `scripts/export_check.py` | **CP3**：契约回显 + OOXML 容器 + 命名 + 证据表一致性（G1–G8） | `--result` `--out-dir` `--case` |
| `scripts/check_contract.py` | 契约字段覆盖核对（读 `OUTPUT_CONTRACT.md` §1 逐条比对） | `--result` `--contract` `--case` `--quiet` |
| `scripts/preview.py` | PIL 近似预览（保留 `make_chart` 兼容再导出） | 库模块 |
| `scripts/make_template.py` | **运行期生成**回退模板 `.pptx` | `--out` `--name` `--no-starter` |
| `scripts/make_synthetic_inputs.py` | **运行期生成**合成夹具（几何占位图 + 两页 ASCII PDF） | `--out` |
| `scripts/cli_io.py` | 控制台加固（非 UTF-8 环境打印中文不崩） | 库模块 |
| **`scripts/determinism.py`（本版新增）** | **CP0 复现判据**：跨进程/跨 cwd/跨 `PYTHONHASHSEED` 连跑 N 次，逐文件 sha256 比对与白名单分类 | `--case` `--spec` `--task` `--out` `--runs` `--out-mode` `--svg-hashsalt` `--python` `--entry` `--seeds` `--timeout` `--stabilize` `--no-timestamp` `--redact-paths` `--json` `--quiet` |

| 文档 / 资源 | 作用 |
|-|-|
| `references/OUTPUT_CONTRACT.md` | result.json 顶层字段清单 + 四形态回显 + G1–G8（**必读**） |
| `references/DETERMINISM.md` | **本版主轴**：逐字段说明哪些字节故意不稳定、如何稳定化、实测表 |
| `references/determinism_report.json` | CP0 的实测报告（默认模式，5 次运行；路径已脱敏） |
| `references/determinism_report-hashsalt.json` | 同上，固定 `svg.hashsalt` 的对照实测（证明随机 id 的来源） |
| `references/slide-blueprint.md` | 论文→页面蓝图映射 + deck-spec schema + 逐页证据表格式 |
| `references/RUBRIC_MAP.md` | 五维评分（40/25/15/10/10）→ 本包落点 + 对照协议 |
| `references/failure-modes.md` | 失败模式与降级策略 + 脚本退出码语义 |
| `references/layer-naming.md` | PPTX 分层命名规范（对象名 = 可编辑性的机器可查证据） |
| `examples/` | 最小示例（合成案例，标注"示例，非正式案例"） |

依赖：`python-pptx` 必需；`Pillow` 用于预览；`matplotlib` 可选（重建图，**其 SVG 元素 id
默认随机，见 DETERMINISM.md §3.3**）；`PyMuPDF`/`pypdf`/`pdfplumber` 任选其一支持 PDF。
逐级回退并如实记录（`references/failure-modes.md` §2.3）。

## 4. 执行阶段 W0–W6（检查点 CP0 / CP1 / CP3）

### W0 定位与读题
1. 读 `task.md`（若存在）与 `/input/case.json`，记录 `case_id`。
2. 解析 `output_contract`（必须回显到 result.json 的全部字段）、材料路径、模板路径、
   `audience` / `duration_minutes` / `slide_count`。
3. 定位 `$SKILL_DIR`；所有脚本用绝对路径调用。

### W1 读实际文件（不许按标签假设内容）
4. 抽取材料：
   ```bash
   python "$SKILL_DIR/scripts/assetkit.py" --pdf "<材料路径>" --out /app/work/extract
   ```
   PDF → 页标记文本 + 图片 + 抽取报告；文本 → 直接读；加密/扫描件/无库 → 转出文本并**如实记录工具**。
5. 通读抽取文本，记录元信息与各章页码（W2 的证据定位要用真实页码）。

### W2 蓝图规划（论文结构 → 页面骨架）
6. 按 `references/slide-blueprint.md` §1 把论文重写为 **问题→方法→证据→结论→局限** 的页序。
7. 抽页级证据：图/表/公式编号、页码、图注、数值与单位**逐字**带出。
8. 区分论文原生图与可从表格数字重建的图（`reconstructed_chart`）；示意图不是实验数据。

### W3 写 deck-spec.json + **CP1**
9. 按 `slide-blueprint.md` §3 schema 写 `/app/work/deck-spec.json`：每页 `claim` +
   短语化 `bullets`（≤6 条、CJK ≤110 字）+ `figure/table` + `notes`（不复制页面文字）
   + `evidence`（ref + page + quote）；无法定位 → `evidence_gap: true`。
10. **CP1 检查点**：
    ```bash
    python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json
    # {"valid": true} 才算蓝图合规；有偏差按 R04 记录后继续
    ```

### W4 构建可编辑源
11. 端到端入口：
    ```bash
    python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
      --spec /app/work/deck-spec.json --out /app/output
    ```
    `main.py` 依次：内嵌 CP1 → 读 case → 定位材料/模板 → assetkit 抽取 → deckgen 构建
    （模板 placeholder-fill-only 或内置 16:9 学术版式；对象按 `layer-naming.md` 命名；
    主题字体注入）→ 备注写入 `notes_slide`（含封面/收尾）→ 证据映射页与双形态证据映射
    → 重建图（PNG+SVG）→ PIL 近似预览 → 组装 result.json → CP3 自检 → 打印摘要。
12. 模板三铁律：只填占位符、不碰 master、布局按名匹配→索引回退→内置版式。
    `template_mode="replace"` 时移除起始页并记录 `starter_slides_removed`。
    页数超限 → `page_budget_met=false` + uncertainty（按 R07 合并/精简，绝不静默丢证据页）。
13. 无模板是正常分支：`deck.template.kind="builtin"` + uncertainty；需要示例模板时：
    ```bash
    python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"
    ```

### W5 渲染与 **CP3**
14. 无 Office 引擎时预览为 PIL 近似（`preview-approx-*.png`，文件名 + `kind` +
    `rendered_with` 三处标注）；有 LibreOffice 时可转真 PDF 并改写记录。
15. 用 python-pptx 重开 deck，核对页数、标题序列、备注、图表编号与 evidence 一致。
16. **CP3 导出检查**（交付门）：
    ```bash
    python "$SKILL_DIR/scripts/export_check.py" --result /app/output/result.json \
      --out-dir /app/output --case /input/case.json
    # valid=true 且 exit 0 才算通过
    ```

### W6 写 result.json + **CP0 复现判据** + 自评
17. result.json 含：`case_id`（与 case 逐字一致）、诚实 `status`、`output_contract` 四形态回显
    （禁止 null）、`deck`、`spec_lint`、双形态 `evidence_mapping`、`previews`、`charts`、
    `sources`、`uncertainty`、`change_records`、`run_meta`（rendered_with / skill_version /
    checkpoints / self_check）；字段清单以 `references/OUTPUT_CONTRACT.md` §1 为准：
    ```bash
    python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
      --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case /input/case.json
    ```
18. **CP0 复现判据**（本版新增，交付前跑一次）：
    ```bash
    python "$SKILL_DIR/scripts/determinism.py" --out "<探针目录>" --runs 5 --stabilize
    # exit 0 = 规范化后 13/13 一致且未解释差异 0；exit 1 = 有未解释差异（不允许直接交付）
    ```
    差异分类与稳定化手段见 `references/DETERMINISM.md`；报告中出现的每个不稳定字段都必须能
    在 §3 的实测表里找到对应行，**不允许"发现了但没解释"**。
19. 按 `references/RUBRIC_MAP.md` 五维自评，补足可复跑证据（测试记录 → TEST.md）。

预算纪律：总 64 次模型请求 / 900 秒 / 单响应 16384 tokens（含推理）；脚本运行秒级
（示例案例每次端到端实测 1.32–1.48 s，5 次探测合计约 10 s），不占模型预算大头。

## 5. 决策规则 R01–R12（覆盖**可复现 / 材料 / 模板 / 依赖 / 契约 / 状态**六类）

| # | 情形 | 决策（做什么 → 记录在哪） |
|-|-|-|
| R01 | CP0 报出 `unexplained_diffs` 非空 | 视为**未定级缺陷**：先定位差异文件与字段（报告里已给 pointer/观测值），修掉或给出白名单证据后再交付；绝不改判为"已解释" → `references/DETERMINISM.md` §3 新增一行 + TEST.md |
| R02 | 交付物需要跨机对拍 | 用同一个 `--out` 复跑；需要分发稳定副本时取 `--stabilize` 产出的 `stabilized/run-0/`（实测稳定化后 13/13 字节一致） → 报告 `stabilized.dir` |
| R03 | `result.json` 里出现本机输出路径（`charts[].chart.file`） | 已知限制：它是 `out-dir identity`（值随 `--out` 变）；跨机对比时按 R02 用同一 `--out`，或在报告里按类别接受 → `volatile_fields[]` 的 `out-dir-identity` 行 |
| R04 | **CP1 lint 有偏差** | 先修 spec；确属案例硬约束无法满足 → 继续构建但显式记录偏差、status 降 `partial` → `result.spec_lint` + `uncertainty` |
| R05 | 材料缺失/路径不存在 | 不补造；仅产出元信息 result，deck 不构建 → `status=failed`；`sources.reason` |
| R06 | PDF 加密 / 无文本层（扫描件） | 空口令试一次；不 OCR 冒充；标注"图像型 PDF"，有图仍可引用 → `uncertainty` + `sources.tool` |
| R07 | 图/表抽不出；页数超限 | 保留**显式占位框**（标注"需补齐，非原图"）；超限先合并非证据页并记录，绝不静默丢证据页 → `figure.placed=placeholder` / `page_budget_met=false` + `change_records` |
| R08 | 模板不可用/损坏/占位符不足/文件不存在 | 内置学术版式回退，不添加冲突对象；需要模板或夹具时跑 `make_template.py` / `make_synthetic_inputs.py`（退出码 2 = 后端不可用） → `deck.template.guard` / `kind` + `uncertainty` |
| R09 | 依赖缺失（matplotlib / PDF 库 / 字体 / PIL） | 逐级回退并如实记录：重建图跳过（`charts[].chart.reason`）、PDF 转文本、预览字体回退 default；**不得伪造产物** → `uncertainty` + `run_meta` |
| R10 | 契约字段未知/无值 | 四形态按类型给 `""`/`[]`/`{}`，**禁止 null**；语义字段取本次运行真实值 → result 顶层回显（`check_contract.py` exit 0） |
| R11 | 状态一致性（status 与产物不符） | `completed` 只允许"材料可读 + deck 生成 + 预览生成 + 无未标注缺口 + CP1 通过"；任一降级即 `partial`/`failed`，**不允许把 partial 说成 completed** → `status` + `uncertainty` |
| R12 | 探针本身可疑（怀疑"永远说 OK"） | 换一个会写随机数的 `--entry` 跑阴性对照：应报 `unexplained_diffs` 且退出码 1（实测见 DETERMINISM.md §4 场景 E） → `determinism_report.json` |

被降级的任何步骤都必须把"发生了什么 + 影响"写进 `uncertainty` / `change_records`，
并在最终回复里说明限制。

**与基线 D 编号的对应**（`references/failure-modes.md`、`references/slide-blueprint.md`
里出现的 D 编号按此行解读，脚本与参数语义未变）：
R04 = D4（CP1 偏差处置）、R05 = D1、R06 = D2/D3、R07 = D5/D7、R08 = D6/D11、R09 = D8/D9、
R10 = D10、R11 = 状态一致性约束（基线 §7 自查清单中的同一条）、
**R01/R02/R03/R12 为本版新增**（分别对应未解释差异、稳定副本、输出目录身份、探针阴性对照）。

## 6. 本版实测数字（CP0，可复核）

| 判据 | 实测（示例案例，5 次运行） | 复核命令 |
|-|-|-|
| 原始字节一致 | `identical = False`；13 个产物中 10 个字节一致，3 个含故意不稳定字节（`.pptx` / `.svg` / `result.json`） | `--runs 5 --stabilize` 报告的 `byte_identical_per_file` |
| 规范化后一致 | `identical_canonical = True`（13/13） | 同上 `canonical_identical_per_file` |
| 稳定化后字节一致 | `identical_stabilized = True`（13/13，稳定化副本 5/5 相同） | 同上 `stabilized.identical` |
| 未解释差异 | `0` | 同上 `unexplained_diffs` |
| 已解释字段 | 5 条 JSON 指针（2×`change_records[].time`、`run_meta.timestamp`、`run_meta.duration_seconds`、`charts[0].chart.file`） | 同上 `volatile_fields[]` |
| zip 成员载荷 | 一致（差异只在成员 mtime） | 同上 `volatile_files[]` 的 `member_payloads_identical` |
| SVG 元素 id | 默认 83 个 id、12 个位置逐次不同；`--svg-hashsalt v7-fixed` 后 **0 个位置不同** | `references/determinism_report-hashsalt.json` 的 `svg_id_sequences_stable` |
| 探针自证 | 两次独立探测的 `per_file_canonical_sha256` 完全相同 | §DETERMINISM.md §4 场景 D |
| 阴性对照 | 换成写随机数的入口 → 退出码 1 + `/roll` 入 `unexplained_diffs` | §4 场景 E |

## 7. 交付前自查清单（逐条）

- [ ] 已读真实 `case.json` / `task.md` / 论文文件，无内容来自标签假设；
- [ ] deck-spec 按蓝图规划，每页有 `claim`；bullets ≤6 条；`evidence` 或 `evidence_gap` 二选一；
- [ ] 页上数字/单位/方法名/图号与论文逐字一致（抽查 3 处以上）；页序可讲（问题→方法→证据→结论→局限）；
- [ ] notes 与页面文字分离，`notes_separated=true`（含封面/收尾页）；
- [ ] 模板：占位符填充、master 未动、页脚未覆盖；否则 `template.guard` 注明回退；
- [ ] `/app/output` 内存在：`result.json`（全部 `output_contract` 字段 + `case_id`）、
      `academic_deck.pptx`（可编辑、对象已命名）、`preview-approx-*.png`、
      `evidence_mapping.md` + `evidence_map.json`；
- [ ] `export_check.py` → `valid=true` 且 exit 0（G1–G8）；`check_contract.py` → exit 0（无 null）；
- [ ] **`determinism.py --runs 5 --stabilize` → exit 0，`unexplained_diffs` 为空**；
      若不为空，按 R01 处理后再交付；
- [ ] status / uncertainty / change_records 诚实，无编造软件状态或科学数据；
- [ ] 已按 RUBRIC_MAP 五维逐条自评并补足可复跑证据。

## 8. 限制与口径边界

- 预览默认是 PIL 近似渲染，**不等同于** PowerPoint/LibreOffice 渲染结果；
- 可复现性的结论限定在"同一解释器 + 同一压缩库 + 同一平台"；跨环境只承诺
  "zip 成员载荷一致"这一级（`DETERMINISM.md` §3.2 / §6）；
- `result.json` 的 `charts[].chart.file` 携带输出目录绝对路径（已知限制，R03）；
- PDF 图片抽取依赖库与版式，个别图只以显式占位框呈现；模板适配为"占位符级"，不重排 SmartArt；
- 本 Skill 生成内容与结构，不保证论文结论本身正确（结论以论文为准）；
- 包内**只携带文本资源**（`.md/.py/.json/.txt/.csv/.yaml/.yml`）；模板、预览、示意图等二进制
  一律**运行时生成**或由案例提供。

## 9. 维护（改什么就重跑什么）

| 改动 | 必须重跑 |
|-|-|
| 任何 `scripts/*.py` | `spec_lint` → `main.py` → `export_check` → `check_contract`，然后 **`determinism.py --runs 5 --stabilize`**（产物字节会变） |
| 新增会写时间戳/随机值的产物 | 同步更新 `DETERMINISM.md` §3 与 `determinism.py` 的白名单（白名单是代码常量，不在文档里） |
| 新增失败分支 | 同步更新 `references/failure-modes.md` 与 SKILL.md §5 的 R 规则 |
| 版本 | `scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；本版仅新增 `scripts/determinism.py`，既有脚本逐字节未改 |
