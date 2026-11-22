---
name: paper-to-academic-ppt
description: 把论文/研究材料转换成主线清晰、证据可追溯、可编辑的学术汇报 PPT。本版把"泛化能力"做成可跑的题集：examples/cases/ 下有两个**不同题材**的合成案例（实验物理·μ 子透射成像分辨电池析锂；临床流行病学·睡眠时长与代谢综合征横断面关联），配 references/CASE-SET.md 的逐案验收区间（页数/证据行/必须逐字保留的数字/禁止出现的越界表述）与 scripts/run_case_set.py 的逐案实跑表——三个案例全部实测在区间内，并**如实写明泛化到哪里会失效**。产物含可编辑 .pptx、双形态逐页证据映射、近似预览与契约完整的 result.json。Use when a task asks to turn a paper or research material into an academic slide deck (论文转PPT、学术汇报PPT、slides from paper、presentation from paper), especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews.
---

# 论文转学术 PPT（多案例泛化题集版 · paper-to-academic-ppt）

"这套流程能处理论文"这句话，只在**一个**案例上成立时几乎没有信息量。
真正的问题是：**换一个题材、换一套数值、换一种结论口径，它还成立吗？**

本版把这个问题的答案做成一份**可以逐格复核的题集**：两个与示例截然不同题材的
合成案例（一个物理、一个临床流行病学），各自的输入、期望产出结构、可接受区间、
难度层都写清楚，再用 `scripts/run_case_set.py` 逐个真跑、逐条对区间。

| 你要什么 | 去哪 |
|-|-|
| 马上跑一遍最小示例 | §4 S0–S6，`examples/README.md` |
| **换题材还成立吗 / 边界在哪** | `references/CASE-SET.md`（题集 + 逐案实测 + 失效边界）+ §7 |
| 出事时怎么处置、退出码是几 | §6 决策表 + `references/failure-modes.md` |
| 交付前逐条自查 | §8 清单 |
| 五维评分落点 | `references/RUBRIC_MAP.md` |

**不负责**：论文精读结论的生成、科研绘图本身的图形设计、学术写作润色。
**不使用预制答案**：正式运行只依据案例实际提供的文件；`examples/` 只演示接口。

---

## 1. 适用与触发

- `/input/case.json` + `/input/task.md` 存在，要求在 `/app/output` 产出演示产物；
- 或用户直接要求"把这篇论文做成学术 PPT / slides from this paper / 组会汇报"。

**适用**：单篇论文/研究报告 → 8–20 页学术汇报（页级主张 + 图表定位 + 讲解备注 +
模板适配 + 渲染记录）。**不适用**：判断论文结论真假、重画科研图、润色正文、
与材料无关的通用幻灯片——越界请求写进 `uncertainty` 并拒绝。

## 2. 输入输出与自定位

| 方向 | 路径（以环境实际挂载为准） | 内容 |
|-|-|-|
| 输入 | `/input/case.json` | `case_id`、`output_contract`、材料/模板定位、受众与页数约束 |
| 输入 | `/input/task.md` | 任务说明（存在时读取；缺失不阻断） |
| 工作 | `/app/work` | 抽取文本与图片、页级方案 `deck-spec.json` |
| 输出 | `/app/output` | `result.json`、`academic_deck.pptx`、`preview-approx-*.png`、`evidence_mapping.md`、`evidence_map.json`、`chart-*.png/.svg` |

**自定位**：`$SKILL_DIR` = `SKILL.md` 所在目录。脚本以
`os.path.dirname(os.path.abspath(__file__))` 自解析并 `sys.path.insert` 本目录，
**cwd 不是技能根也能跑**（题集执行件的子进程即以此方式运行，等于每跑一次就复核一次）：

```bash
SKILL_DIR="<SKILL.md 所在目录>"       # 平台安装到 /skills/weekly-skill 时即该路径
python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json
```

输入不在 `/input` 时，探测 `CASE_PATH` / `OUTPUT_DIR` / cwd 下的 `case.json`（D14）。

## 3. 资源清单（相对 `$SKILL_DIR`）

| 文件 | 作用 | 独立 CLI |
|-|-|-|
| `scripts/main.py` | 端到端编排：CP1 → 抽取 → 构建 → 预览 → CP3 → result.json | `--case --out` 必填 |
| `scripts/run_case_set.py` | **本版主轴**：题集逐案实跑 + 验收区间 + 两道门 | `--out` 必填；`--include-example`/`--only`/`--emit-md`/`--json` |
| `scripts/assetkit.py` | 素材层：材料定位、PDF 文本/图片抽取、表格数字重建图 | `--pdf --out` |
| `scripts/deckgen.py` | 生成层：模板适配（含损坏回退）、页级排版、备注、证据映射页、命名 | 打印记录 |
| `scripts/ooxml_kit.py` | OOXML 层：主题字体注入、形状命名、zip/XML 健全检查 | 传 `.pptx` |
| `scripts/spec_lint.py` | **CP1**：deck-spec 结构校验（BL-1…BL-4） | `--spec` |
| `scripts/export_check.py` | **CP3**：契约 + 容器 + 命名 + 证据表一致性（G1–G8） | `--result --out-dir [--case]` |
| `scripts/check_contract.py` | 契约字段覆盖（直接读 `OUTPUT_CONTRACT.md` §1） | `--result --contract [--case]` |
| `scripts/preview.py` | PIL 近似预览 | 打印记录 |
| `scripts/make_template.py` | 运行期生成回退模板 | `--out [--name] [--no-starter]` |
| `scripts/make_synthetic_inputs.py` | 运行期生成合成夹具 | `--out` |
| `scripts/cli_io.py` | 控制台 UTF-8 加固 | 被各入口导入 |
| `references/CASE-SET.md` | **本版新增**：题集定义 + 逐案实测表 + 失效边界 + 加案例流程 | — |
| `references/OUTPUT_CONTRACT.md` | result.json 顶层字段 + 四形态 + G1–G8（**必读**） | — |
| `references/failure-modes.md` | 五类异常处置 + 退出码语义 + 检测能力边界 | — |
| `references/slide-blueprint.md` | 论文→页面蓝图 + deck-spec schema + 证据表格式 | — |
| `references/RUBRIC_MAP.md` | 五维落点（以**实际效果 + 生态贡献**为主轴）+ 复核命令 | — |
| `references/layer-naming.md` | 分层命名规范 | — |
| `examples/` | 最小示例（合成） | — |
| `examples/cases/` | **本版新增**：两个不同题材的合成案例（各含 case/material/deck-spec/expected） | — |

依赖：`python-pptx` 必需；`Pillow` 预览（也是 python-pptx 的依赖）；`matplotlib` 可选；
`PyMuPDF`/`pypdf`/`pdfplumber` 任一即可读 PDF。逐级回退见 §6。

## 4. 执行步骤 S0–S6（检查点 CP1–CP3）

### S0 定位与读题
1. 读 `task.md`（存在时）与 `/input/case.json`，取 `case_id`。
2. 解析 `output_contract`（**四种声明形态**，见 §5）、材料/模板路径、受众与页数约束。
3. 定位 `$SKILL_DIR`；脚本一律用绝对路径调用。

### S1 读实际文件（不许按标签假设内容）
4. ```bash
   python "$SKILL_DIR/scripts/assetkit.py" --pdf "<材料路径>" --out /app/work/extract
   ```
   加密 / 扫描件 / 无 PDF 库 → D03–D05，**不做 OCR 冒充**。
5. 记下真实元信息（标题/作者/venue、页码、页数/字数）——它们要进 `sources[]`。

### S2 蓝图规划（论文结构 → 页面骨架）
6. 按 `references/slide-blueprint.md` §1 重写为 问题→方法→证据→结论→局限。
   **不同题材的页序不同**：实验类要"装置/标定/不确定度"，临床类要"纳排/校正模型/
   因果口径"——题集里两个案例的 `expected_structure` 就是这两种范式的样本。
7. 抽页级证据：编号、页码、图注、数值与单位**逐字**从原文带出。
8. 标注图的性质：论文原生图 / 从表格数字重建（`reconstructed_chart`）。

### S3 写 deck-spec.json + CP1
9. 每页 `claim` + 短语化 `bullets`（≤6 条、CJK 加权 ≤110 字）+ `figure`/`table`
   + `notes`（不复制页面文字）+ `evidence`；无法定位证据 → `evidence_gap: true`。
   **图文同页时把 `layout_hint` 写成 `figure`**，正文会自动走左半幅（见 D19）。
10. **CP1**：`python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json`

### S4 构建可编辑源
11. ```bash
    python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
      --spec /app/work/deck-spec.json --out /app/output
    ```
12. 模板三铁律：只填占位符、不碰 master、不覆盖页脚/配色；损坏 → 回退内置版式（D08）。
13. 页数超限 → D10：合并非证据页，**绝不静默丢弃证据页**。

### S5 渲染与 CP3
14. 无 Office 引擎 → PIL 近似（文件名 + `previews[].kind` + `rendered_with` 三处标注）。
15. 重开 deck 核对页数/标题/备注/图表编号与 evidence 一致。
16. **CP3**：`export_check.py --result ... --out-dir ... --case ...`

### S6 写 result.json + 自评
17. 19 个顶层字段 + `case_id`，再跑 `check_contract.py --case`。
18. 按 `references/RUBRIC_MAP.md` 自评；测试记录进 `TEST.md`，示例进 `examples/`。
19. 诚实性硬约束：不编造数据；数值/单位不改写；图缺失=显式占位框；
    预览近似如实标注；每次降级进 `uncertainty` + `change_records`。

预算纪律：64 次模型请求 / 900 秒 / 单响应 16384 tokens（含推理）。

## 5. 四形态契约回显

| 形态 | 声明长相 | 回显规则 |
|-|-|-|
| ① 字段→类型提示 | `{"title": "字符串"}` | 有真值写真值，否则按容器给 `""`/`[]`/`{}` |
| ② 字段→说明 | `{"render_state": "渲染记录"}` | 同上 |
| ③ 布尔开关 | `{"notes_separated": true}` | 回显真实布尔 |
| ④ 字段清单 | `["title","slides"]` | 每个名字按类型给空值 |

**任何声明字段禁止 null**；`case_id` 与 case 逐字一致。案例不声明时按 §1 的 19 字段输出。
题集里的两个案例都用**形态①+③混合**，示例用的是同一形态——若要测形态④，
把某个案例的 `output_contract` 改成 list 即可（`run_case_set.py` 会自动复核回显完整性）。

## 6. 决策表 D01–D18

| # | 触发 | 首选 | 降级 | 记录与退出码 |
|-|-|-|-|-|
| D01 | `case.json` 不存在 | 报错，不发明产物 | 不建输出目录 | stderr；**main → 3** |
| D02 | `case.json` 不可解析 | 写 `status=failed` 再退出 | — | `case_unreadable`；**→ 3** |
| D03 | 材料路径不存在 | 只产元信息 result | 语义字段给空值 | `material_status=unreadable`；**→ 1** |
| D04 | 材料为空/不可读 | 同 D03 | — | `status=failed`；**→ 1** |
| D05 | 无 PDF 后端 | 逐级 fitz→pypdf→pdfplumber→外部 `.txt` | 全缺按 D03 | `run_meta.pdf_tools` |
| D06 | 页级方案缺失 | 不建 deck，报失败 | `--demo` 仅用于骨架 | `spec_lint.valid=false`；**→ 1** |
| D07 | 方案 JSON 不可解析 | 按"方案不可读"降级，仍写产物 | 不自动编造方案 | `spec_lint.problems`；**→ 1** |
| D08 | 模板**损坏** | 回退内置版式并继续 | 记 `template.error`，状态降 `partial` | `template.kind=builtin`；→ 0 |
| D09 | 模板**缺席** | 内置版式（**正常分支**） | 需要时 `make_template.py` | `template.kind=builtin`；→ 0 |
| D10 | 页数超限 | 合并非证据页 | 绝不丢弃证据页 | `page_budget_met=false` |
| D11 | 图/表抽不出 | 显式占位框 | 引用与定位照留 | `figure.placed=null` |
| D12 | 重建图失败 | 跳过，保留引用与数字 | 不估算补齐 | `charts[].chart.reason` |
| D13 | 缺 `python-pptx` | `deck=null`，不造假文件 | result.json 仍完整 | `deck_error`；**→ 1** |
| D14 | 缺 `Pillow` | `previews=[]` + 状态降级 | 实际等同 D13 | `rendered_with=failed` |
| D15 | 契约字段未知/无值 | 四形态回显 | 禁止 null | `output_contract`；check_contract → 1/2 |
| D16 | 契约文档缺失 | 契约同源门失败 | 不静默放行 | `self_check.problems`；**→ 1** |
| D17 | 有无渲染引擎 | 有 `soffice` → 真 PDF；无 → PIL 近似 | 三处标注 | `rendered_with` + `previews[].kind` |
| D18 | 任一降级 | `uncertainty` + `change_records` **都写** | 只写其一 ⇒ 状态不一致 | `self_check.ok=false` ⇒ **→ 1** |
| D19 | **图文同页** | 正文走左半幅文本框，图放右半幅 | 组织方模板下按占位符填充 | `deck.layouts_used` + `figures[].placed` |

> **D19 是题集抓出来的**：曾经把 bullets 写进 `Picture with Caption` 的图片占位符、
> 随后被插图覆盖 ⇒ 该页文字从 XML 里消失（产物能打开、导出检查全绿）。
> 详见 `references/CASE-SET.md` §3 的 G1。

**退出码**：`0` 完成且自检无 error；`1` 产物不完整/自检有 error；`2` 参数或后端不可用；
`3` 输入不可读。

## 7. 多案例泛化：题集怎么用、边界在哪（本版主轴）

```bash
cp -r "$SKILL_DIR" /tmp/skill-set            # 务必在包外跑
python /tmp/skill-set/scripts/run_case_set.py \
    --out /tmp/case-out --include-example --emit-md /tmp/case-out/case-set.md
# 退出码：0 = 全部在区间内；1 = 有案例越界（点名）；2 = 全部没产物；3 = 参数错
```

三个案例（实测见 `references/CASE-SET.md` §2）：

| 案例 | 题材 | 难度层 | 实测 |
|-|-|-|-|
| `example-*` | 计算机（检索增强代码评审） | 容易 | `completed` / 8 页 / 证据 6 行 / 两道门 0-0 |
| `case-muon-battery` | **实验物理·无损检测** | 中等 | `completed` / 11 页 / 证据 9 行 / 8/8 数字逐字命中 |
| `case-sleep-cohort` | **临床流行病学** | 中等偏难（语言纪律） | `completed` / 11 页 / 证据 9 行 / 8/8 数字逐字命中 |

**验收区间不是"看起来对"，而是可机检的四条**：`status` 词表、页数区间、
证据映射行数下限、`must_keep_verbatim` 的每个数字是否**逐字出现在产物文字里**
（deck 全部文本框 + 备注 + 证据表），外加 `must_not_claim` 的越界表述是否**不**出现。

**泛化失效边界（如实，见 `CASE-SET.md` §4）**：扫描件/图像型 PDF（不做 OCR，未测）、
>20 页的大汇报（未测）、非中英文材料（未测）、真正的组织方模板（题集全走内置版式）、
多篇材料合并（本包按单篇设计）。**不要**把这些说成"支持"。

## 8. 交付前自查清单

- [ ] 已读真实 case.json / task.md / 材料；`sources[]` 有真实工具与页数/字数；
- [ ] 每页有 `claim`；bullets ≤6 条；`evidence` 或 `evidence_gap` 二选一；
- [ ] **CP1** 通过或偏差按 D06 双写；
- [ ] 页上数字/单位/方法名/图号与原文逐字一致（抽查 ≥3 处）；
- [ ] 备注与页面文字分离，含封面/收尾页，`notes_separated=true`；
- [ ] **图文同页**按 D19 处理：正文未被图片覆盖（可在 deck XML 里搜到该页数字）；
- [ ] 模板：占位符填充、master 未动；损坏回退已记 `template.error`；
- [ ] `/app/output` 有 `result.json`（19 字段 + `case_id`）、`.pptx`、预览、双形态证据映射；
- [ ] **CP3** `export_check` exit 0；`check_contract --case` exit 0；
- [ ] 四形态契约全部回显、无 null；
- [ ] 降级双写齐全；`status` 与 `uncertainty`/证据缺口自洽；
- [ ] 若声称"换题材也成立"：**给出 `run_case_set.py` 的退出码**，而不是形容词。

## 9. 限制与口径边界

- 预览是 **PIL 近似渲染**，不等同于 PowerPoint/LibreOffice 结果；
- PDF 图片抽取依赖库与版式，个别图只以显式占位框呈现（**不代表**论文原图）；
- 模板适配为"占位符级"：SmartArt 不重排；模板自带形状不改名；
- 结论正确性上限 = 论文原文；本 Skill 不验证论文结论；
- **题集口径**：三个案例都是合成材料（虚构作者/机构/数值），证明的是"**这条链路在
  不同题材与不同数值结构下仍产出可验收的产物**"，不是"在这些题材上做出了好汇报"；
  更不是对平台评分的预测。题集外推边界见 `references/CASE-SET.md` §4。

## 10. 维护

- 版本：`scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；
- 分层约定：素材 → `assetkit.py`，生成 → `deckgen.py`，OOXML → `ooxml_kit.py`；
- **改任一页级版式行为 ⇒ 重跑 `run_case_set.py` 并重新渲染 `CASE-SET.md` §2**
  （数字会变，旧数字一律作废）；
- 改 D 规则 ⇒ 同步 `references/failure-modes.md` 同号条目；
- 新增案例 ⇒ 四文件（`case.json`/材料/`deck-spec.json`/`expected.json`），
  `run_case_set.py` 自动发现，无需改脚本（流程见 `CASE-SET.md` §5）。
