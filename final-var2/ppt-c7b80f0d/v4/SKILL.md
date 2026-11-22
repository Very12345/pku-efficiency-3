---
name: paper-to-academic-ppt
description: 把论文/研究材料转换成主线清晰、证据可追溯、可编辑的学术汇报 PPT。本版把"可靠"做成可执行的演练：scripts/fault_inject.py 对输入/模板/依赖/契约/状态五类形态逐条注入真实故障（真删文件、真写坏 JSON、真屏蔽依赖模块），跑主流程并逐行实测"退出码 / status / uncertainty / 是否静默失败"，结果由脚本渲染成 references/FAULT-MATRIX.md（24 条注入、0 条静默失败、19 条恢复演练全部回到 completed）；执行链本身仍是 定位→抽取→方案→CP1 lint→生成→预览→CP3 导出检查，产物含可编辑 .pptx、双形态逐页证据映射、近似预览与契约完整的 result.json。Use when a task asks to turn a paper or research material into an academic slide deck (论文转PPT、学术汇报PPT、slides from paper、presentation from paper), especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews.
---

# 论文转学术 PPT（失败注入与恢复演练版 · paper-to-academic-ppt）

一份能跑的 Skill 与一份**可被信任**的 Skill 之间的差距，不在正常路径上——
正常路径谁都能演示。差距在**出事的那 20 秒**：

> 材料是空的、模板是半截的、`python-pptx` 没装、契约声明里有未知字段，
> 更要命的是——**产物看起来还挺完整**。

所以本版的组织方式是：先假定流程会坏，再证明"坏了会被看见"。
`scripts/fault_inject.py` 把这件事变成一条命令；`references/FAULT-MATRIX.md`
是它跑出来的实测账本，不是散文。

| 你要什么 | 去哪 |
|-|-|
| 马上跑一遍最小示例 | §4 S0–S6，`examples/README.md` |
| 出事时该怎么处置、退出码是几 | §6 决策表（D01–D18）+ `references/failure-modes.md` |
| **出事后怎么证明自己被看见了** | `references/FAULT-MATRIX.md` + `scripts/fault_inject.py`（§7） |
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
**cwd 不是技能根也能跑**（这条承诺本身也在演练范围内：`fault_inject.py` 的所有子进程
都以沙箱为 cwd，等于每跑一次注入就复核一次）。命令一律写 `"$SKILL_DIR/scripts/xxx.py"`：

```bash
SKILL_DIR="<SKILL.md 所在目录>"       # 平台安装到 /skills/weekly-skill 时即该路径
python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json
```

输入不在 `/input` 时，探测 `CASE_PATH` / `OUTPUT_DIR` / cwd 下的 `case.json`，
以实际可读文件为准（D14）。

## 3. 资源清单（相对 `$SKILL_DIR`）

| 文件 | 作用 | 独立 CLI / 退出码 |
|-|-|-|
| `scripts/main.py` | 端到端编排：CP1 lint → 抽取 → 构建 → 预览 → CP3 → result.json | `--case --out` 必填；0/1/2/3 |
| `scripts/fault_inject.py` | **本版主轴**：五类故障注入 + 恢复演练 + 矩阵渲染 | `--out` 必填；0/1/2/3 |
| `scripts/assetkit.py` | 素材层：材料定位、PDF 文本/图片抽取、表格数字重建图 | `--pdf --out`；0/2 |
| `scripts/deckgen.py` | 生成层：模板适配（**含损坏模板回退**）、页级排版、备注、证据映射页、命名 | 打印记录 |
| `scripts/ooxml_kit.py` | OOXML 层：主题字体注入、形状命名、zip/XML 健全检查 | 传 `.pptx` |
| `scripts/spec_lint.py` | **CP1**：deck-spec 结构校验（BL-1…BL-4） | `--spec`；0/1 |
| `scripts/export_check.py` | **CP3**：契约回显 + OOXML 容器 + 命名 + 证据表一致性（G1–G8） | `--result --out-dir [--case]`；0/1 |
| `scripts/check_contract.py` | 契约字段覆盖（**直接读** `OUTPUT_CONTRACT.md` §1，单一事实源） | `--result --contract [--case]`；0/1/2 |
| `scripts/preview.py` | PIL 近似预览（无 Office 引擎时的诚实渲染） | 打印记录 |
| `scripts/make_template.py` | 运行期生成回退模板（包内不携带二进制） | `--out [--name] [--no-starter]`；0/2 |
| `scripts/make_synthetic_inputs.py` | 运行期生成合成夹具 | `--out`；0/2 |
| `scripts/cli_io.py` | 控制台加固：stdout/stderr → UTF-8 + `errors="replace"` | 被各入口导入 |
| `references/FAULT-MATRIX.md` | **本版新增**：24 条注入的实测矩阵 + 判定口径 + 修复点名 + 扩展指南 | — |
| `references/OUTPUT_CONTRACT.md` | result.json 顶层字段 + 四形态回显 + 硬性门 G1–G8（**必读**） | — |
| `references/failure-modes.md` | 五类异常处置 + 退出码语义 + **§5 检测能力边界** | — |
| `references/slide-blueprint.md` | 论文→页面蓝图映射 + deck-spec schema + 证据表格式 | — |
| `references/RUBRIC_MAP.md` | 五维落点（以**可靠体验 + 可验证性**为主轴）+ 复核命令 | — |
| `references/layer-naming.md` | 分层命名规范（对象名 = 可编辑性的机器可查证据） | — |
| `examples/` | 最小示例（合成案例，标注"示例，非正式案例"） | — |

依赖：`python-pptx` 必需（缺则 `deck=null` 并降级，**不再崩溃**）；`Pillow` 预览
（同时也是 python-pptx 的依赖）；`matplotlib` 可选（重建图）；
`PyMuPDF`/`pypdf`/`pdfplumber` 任一即可读 PDF。逐级回退见 §6 与 `failure-modes.md`。

## 4. 执行步骤 S0–S6（检查点 CP1–CP3）

### S0 定位与读题
1. 读 `task.md`（存在时）与 `/input/case.json`，取 `case_id`。
2. 解析 `output_contract`（必须回显的全部字段——注意它有**四种声明形态**，见 §5.4）、
   材料路径、模板路径、`audience/duration_minutes/slide_count`。
3. 定位 `$SKILL_DIR`；脚本一律用绝对路径调用。

### S1 读实际文件（不许按标签假设内容）
4. 抽取材料：
   ```bash
   python "$SKILL_DIR/scripts/assetkit.py" --pdf "<材料路径>" --out /app/work/extract
   ```
   PDF → 页标记文本（`[PAGE n]`）+ 图片 + 抽取报告；文本/LaTeX → 直接读取。
   加密 / 扫描件 / 无 PDF 库 → 走 D02–D04，**不做 OCR 冒充**。
5. 记下真实元信息（标题/作者/venue、各章页码、页数/字数）——它们要进 `sources[]`。

### S2 蓝图规划（论文结构 → 页面骨架）
6. 按 `references/slide-blueprint.md` §1 把章节重写为 问题→方法→证据→结论→局限。
7. 抽页级证据：编号、页码、图注、数值与单位**逐字**从原文带出。
8. 标注图的性质：论文原生图 / 从表格数字重建（`reconstructed_chart`）；
   **示意图不是实验数据**。

### S3 写 deck-spec.json + CP1
9. 按 `slide-blueprint.md` §3 schema 写 `/app/work/deck-spec.json`：每页
   `claim` + 短语化 `bullets`（≤6 条、CJK 加权 ≤110 字）+ `figure`/`table`（ref 与论文一致）
   + `notes`（**不复制页面文字**）+ `evidence`（ref + page + quote）；无法定位证据 → `evidence_gap: true`。
10. **CP1**（写完必跑）：
    ```bash
    python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json
    # {"valid": true} 才算合规；有偏差按 D05 处置
    ```

### S4 构建可编辑源
11. ```bash
    python "$SKILL_DIR/scripts/main.py" \
      --case /input/case.json --task /input/task.md \
      --spec /app/work/deck-spec.json --out /app/output
    ```
12. 模板三铁律：**只填占位符、不碰 master、不覆盖页脚/配色**；布局按名匹配 →
    索引回退 → 内置版式。**模板损坏时回退内置版式**（D07，与"模板缺席"这一正常分支
    区分开：损坏回退 ⇒ `partial`，缺席回退 ⇒ `completed`）。
13. 页数超 `slide_count` → D08：合并非证据页，**绝不静默丢弃证据页**。

### S5 渲染与 CP3
14. 无 Office 引擎 → PIL 近似（文件名 + `previews[].kind` + `rendered_with` 三处标注）；
    有 `soffice` → 真 PDF 并改写记录（D13）。
15. 用 python-pptx 重开 deck，核对页数/标题序列/备注/图表编号与 evidence 一致。
16. **CP3**（交付门）：
    ```bash
    python "$SKILL_DIR/scripts/export_check.py" --result /app/output/result.json \
      --out-dir /app/output --case /input/case.json
    ```

### S6 写 result.json + 自评
17. 字段以 `references/OUTPUT_CONTRACT.md` §1 为准（19 个顶层字段 + `case_id`）：
    ```bash
    python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
      --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case /input/case.json
    ```
18. 按 `references/RUBRIC_MAP.md` 逐条自评；测试记录进 `TEST.md`，示例进 `examples/`。
19. 诚实性硬约束：不编造科学数据；数值/单位不改写；图缺失=显式占位框；
    预览近似如实标注；每次降级进 `change_records` + `uncertainty`。

预算纪律：64 次模型请求 / 900 秒 / 单响应 16384 tokens（含推理）。先 S1–S3 落盘成
中间件再增量交付；脚本运行秒级，不占模型预算大头。

## 5. 四形态契约回显（这一步最容易静默出错）

`case.json` 的 `output_contract` 有**四种并列形态**，`apply_output_contract()` 必须全部覆盖：

| 形态 | 案例声明长什么样 | 回显规则 |
|-|-|-|
| ① 字段→类型提示 | `{"title": "字符串"}` | 有真实值写真实值，否则按容器给 `""` / `[]` / `{}` |
| ② 字段→说明 | `{"render_state": "渲染记录"}` | 同上；语义可推断时写真实值 |
| ③ 布尔开关 | `{"notes_separated": true}` | 回显真实布尔 |
| ④ 字段清单 | `["title", "slides"]` | 每个名字按类型给空值；**语义字段仍要写真值** |

再加两条：**任何声明字段禁止 `null`**；`case_id` 与 case 逐字一致（G1）。
案例**完全不声明** `output_contract` 时，按 §1 的 19 个字段输出（本包自带最小契约）。
判据不是"我读了文档"，而是 `check_contract --case` 的退出码 + `fault_inject.py` 的
CT-01/CT-02 两条注入（后者连"声明值就是 null"这种刁钻形态都覆盖）。

## 6. 决策表 D01–D18（覆盖 材料 / 模板 / 依赖 / 契约 / 状态）

四列：**触发** → **首选** → **降级** → **记录与退出码**。与 `references/failure-modes.md`
同号，改一处必须改两处。

| # | 触发 | 首选 | 降级 | 记录与退出码 |
|-|-|-|-|-|
| D01 | `case.json` 不存在 | 直接报错，不发明产物 | 不创建输出目录 | stderr 一行；**main.py → 3** |
| D02 | `case.json` 不可解析 | 写 `status=failed` 的 result 后退出 | — | `error=case_unreadable`；**→ 3** |
| D03 | 材料路径不存在 | 只产元信息 result，不建 deck | 语义字段按类型给空值 | `material_status=unreadable` + `sources[].reason`；**→ 1** |
| D04 | 材料存在但为空 / 不可读 | 同 D03 处理 | — | `status=failed`；**→ 1** |
| D05 | 页级方案缺失（无 `--spec` 且无 `--demo`） | 不建 deck，报失败 | 明示 `--demo` 只用于骨架演示 | `spec_lint.valid=false`；**→ 1** |
| D06 | 方案 JSON 不可解析 | 按"方案不可读"降级，仍写产物 | 绝不自动编造方案 | `spec_lint.problems[0]=spec unreadable`；**→ 1** |
| D07 | 模板**损坏/不可打开** | **回退内置 16:9 版式**并继续 | 记 `deck.template.error`；状态降 `partial` | `deck.template.kind=builtin` + uncertainty；→ 0 |
| D08 | 模板**缺席**（没给 / 文件不存在 / 空目录） | 内置版式（**正常分支**） | 需要真模板时 `make_template.py` 现产 | `deck.template.kind=builtin` + uncertainty；→ 0 |
| D09 | 页数超限 | 合并非证据页 | **绝不静默丢弃证据页** | `page_budget_met=false` + change_records |
| D10 | 图/表抽不出 | 显式占位框（"需补齐，非原图"） | 引用与定位照留 | `figure.placed=null` + `placeholder=true` |
| D11 | 重建图失败（无 matplotlib / 数据不全） | 跳过图，保留引用与数字 | 不估算补齐 | `charts[].chart.reason` |
| D12 | 缺 `python-pptx` | `deck=null`，如实说明 | **不生成假文件**；result.json 仍契约完整 | `deck_error` + `uncertainty`；**→ 1** |
| D13 | 缺 `Pillow` | `previews=[]` + `rendered_with=failed`，状态降 `partial` | 注意 python-pptx 也依赖 Pillow ⇒ 实际等同 D12 | `previews=[]` + uncertainty |
| D14 | 无 PDF 后端 | 逐级 fitz→pypdf→pdfplumber→外部 `.txt` | 全缺 → 按 D03 处理 | `run_meta.pdf_tools` 全 false + sources |
| D15 | 契约字段未知/无值 | 四形态回显，未知字段 `setdefault` | **禁止 null** | `result.output_contract`；check_contract → 1（缺字段）/ 2（文档解析不出） |
| D16 | 契约**文档**缺失 | 契约同源门直接失败 | 不静默放行 | `self_check.problems` 点名契约；**→ 1** |
| D17 | 有/无渲染引擎 | 有 `soffice` → 真 PDF；无 → PIL 近似 | 近似必须三处标注 | `run_meta.rendered_with` + `previews[].kind` |
| D18 | 任一降级发生后 | 同步写 `uncertainty[]`（发生了什么+影响）**与** `change_records[]`（何时+为什么） | 只写其一 ⇒ 状态不一致 | `self_check.ok=false` ⇒ main.py → 1 |

**退出码语义（全包统一，流水线可直接判断）**：
`0` = 交付完成且自检无 error；`1` = 产物不完整或自检有 error（result.json 通常仍写出）；
`2` = 参数错误 / 工具后端不可用；`3` = 输入不可读（case 缺失/损坏）。

## 7. 失败注入与恢复演练（本版新增，30 秒可复跑）

```bash
# 复制到包外再跑（包内跑会留 __pycache__，技能资源只能是文本）
cp -r "$SKILL_DIR" /tmp/skill-drill
python /tmp/skill-drill/scripts/fault_inject.py \
    --out /tmp/drill --emit-matrix /tmp/drill/matrix.md
```

它在**包外沙箱**里，对 24 条真实故障逐条跑主流程并测量：

| 形态 | 注入什么（举例） | 常被忽略的真相 |
|-|-|-|
| ① 输入 | case 缺失 / JSON 截断 / 材料为空 / **不给方案** / **陈旧 `--out` 重跑** | "没有可交付物"最容易被写成 exit 0 |
| ② 模板 | 文本改名 `.pptx` / 0 字节 / **半截 zip** | 模板坏 ≠ 模板缺席，两者状态词不同 |
| ③ 依赖 | 屏蔽 `pptx` / `PIL` / `matplotlib` / 全部 PDF 后端 | 模块级 import 会让"优雅降级"变成"直接崩溃" |
| ④ 契约 | 未知字段（含声明值 `null`）/ **形态④ list** / 契约文档缺失 / 事后删字段 | 四形态里只有 dict 形态常被实现 |
| ⑤ 状态 | 伪造 `status=completed` / 抹掉 `uncertainty` | **这一条脚本门拦不住**，必须人工兜底 |

实测结论（`references/FAULT-MATRIX.md` §3，24 条注入）：**静默失败 0 条**、
与文档口径不一致 0 条、19 条有恢复动作的全部回到 `exit 0 + completed`、
**已知检测缺口 3 条**（如实申报，不假装覆盖）。

> 这一轮演练**真的改掉了 9 个缺陷**：模块级 import 崩溃、无 deck 却报成功、
> 契约 list 形态不落字段、损坏模板导致整个 deck 丢失（以上由注入发现），
> 以及**图文同页时页级文字被插图覆盖的静默丢失**（由题集 G1 发现，见 `CASE-SET.md` §3）。
> 逐条的 文件/行数/理由 见 `references/FAULT-MATRIX.md` §4 —— 全部纯增量，CLI 与退出码语义未变。

## 8. 交付前自查清单

- [ ] 已读真实 case.json / task.md / 材料；`sources[]` 有真实工具与页数/字数；
- [ ] 每页有 `claim`；bullets 短语 ≤6 条；`evidence` 或 `evidence_gap` 二选一；
- [ ] **CP1** 通过或偏差按 D05 双写；
- [ ] 页上数字/单位/方法名/图号与原文逐字一致（抽查 ≥3 处）；页序可讲；
- [ ] 备注与页面文字分离，含封面/收尾页，`notes_separated=true`；
- [ ] 模板：占位符填充、master 未动、页脚未覆盖；损坏回退已记 `template.error`；
- [ ] `/app/output` 有 `result.json`（19 字段 + `case_id`）、`.pptx`、预览、双形态证据映射；
- [ ] **CP3** `export_check.py` exit 0；`check_contract.py --case` exit 0；
- [ ] 四形态契约全部回显、无 null（含形态④与"完全不声明"两种边界）；
- [ ] 降级双写齐全；`status` 与 `uncertainty`/`evidence` 缺口自洽；
- [ ] **已跑过 `fault_inject.py`，并知道自己的包在三格已知缺口上需要人工复核**。

## 9. 限制与口径边界

- 预览是 **PIL 近似渲染**，不等同于 PowerPoint/LibreOffice 结果；
- PDF 图片抽取依赖库与版式，个别图只以显式占位框呈现（**不代表**论文原图）；
- 模板适配为"占位符级"：SmartArt 不重排；模板自带形状不改名；
- 结论正确性上限 = 论文原文；本 Skill 不验证论文结论；
- **失败注入的边界**：`fault_inject.py` 验证的是"**本包在本机 Python 3.13 / 无 Office
  引擎**下对 24 类故障的响应"，不是"对任意环境任意故障都可靠"。它证明的是
  **可观测性**（坏了会不会被看见），不是**可用性**（坏了还能不能交得出好 PPT）。
- 三格**已知检测缺口**（见 `failure-modes.md` §5）：伪造 status、抹掉 uncertainty、
  `case_id` 与案例不一致——静态产物校验器看不到历史状态与外联对照，必须人工兜底。

## 10. 维护

- 版本：`scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；
- 分层约定：素材 → `assetkit.py`，生成 → `deckgen.py`，OOXML → `ooxml_kit.py`；
- **三处同步铁律**：改 D 规则 → 同步 `failure-modes.md` 同号条目；
  改退出码 / 状态语义 → 同步 §6 与 `failure-modes.md` §1；
  改任一"降级行为" → **重跑 `fault_inject.py` 并重新渲染 `FAULT-MATRIX.md`**，
  旧数字一律作废（不许沿用）。
- 新增故障形态 → 在 `injections()` 里加一条（模板见 `FAULT-MATRIX.md` §6）。
