# EXPECTED-OUTPUT.md — 本 Skill 在一个案例上应产出什么（文字版清单）

> 本文件替代随包的二进制示例产物（`.pptx` / `.png` / `.pdf` 一律不随包提交：题面运行契约只允许
> UTF-8 文本资源）。这里用**文字**给出一次完整运行的文件清单、契约字段与示例案例上的真实数量，
> 便于评审在没有二进制的情况下复核"该产出什么、字段是否齐全"。
>
> 示例案例上的真实运行产物（两个契约 JSON）在 `examples/output/`：
> `result.example.json`、`self_check.example.json`（文件名带 `.example`，标明非正式案例结果）。

## 1. 一次运行的输出清单（`--out <OUT>`）

| 输出文件 | 形态 | 内容 / 复核点 |
|-|-|-|
| `result.json` | 文本 | **唯一评分产物**：契约字段 + `main_line` + `pages` + `evidence_map` + `sources` + `status` + `uncertainty` + `change_records` + `environment` + `audit{plan_gates,evidence,deck,gates}` |
| `talk_plan.json` | 文本 | 页级计划（叙事顺序、逐页 `claim`/`one_liner`/`evidence`/`qa`/`figure_ref`）——可编辑中间产物 |
| `plan_gates.json` | 文本 | 计划契约门 P1–P8 逐条结果（由 `assets/plan.schema.json` 驱动） |
| `evidence_map.json` | 文本 | 源文件 → {用到它的页, 图表引用} 反向映射 |
| `evidence_audit.json` | 文本 | 逐页逐字引文核验（含 `line_no` 越界、数字可对源、图绑定状态） |
| `deck_audit.json` | 文本 | deck 机器校验：可打开、页数、每页备注、`page-claim-NN` 元素、OPC 完整性、规范化 sha256 |
| `editable_deck.pptx` | **二进制（运行期产物）** | 可编辑演示文件：模板适配或内置主题；确定性元素命名；每页讲稿备注 |
| `previews/cover_preview.png` | **二进制（运行期产物）** | 封面预览（PIL 模拟，带水印） |
| `previews/slide_0NN.png` | **二进制（运行期产物）** | 逐页缩略图（每张带「PIL 模拟预览」水印） |
| `previews/preview_grid.png` | **二进制（运行期产物）** | 整包缩略网格 |
| `previews/preview_manifest.json` | 文本 | 预览清单、渲染方法、字体探测结果、占位图说明与限制 |
| `self_check.json` | 文本 | `validate` + `contract_check` + `contract_applied` + 门快照 + 确定性探针 |

> 二进制项是**运行期产物**：题面原文写明 "Runtime artifacts may be binary and are retained
> independently of final JSON validity"，因此它们由脚本现场生成、不进提交资源。
> 交付目录里**不出现**任何随包二进制，因此也不会触发 `unsupported Skill resource` 预检。

## 2. `result.json` 顶层字段（示例案例上实测齐全）

`case.json` + `task.md` 声明的 16 个契约字段全部出现在顶层，且类型正确（`missing=0 wrong_type=0`）：

```
case_id  status  title  report_goal  audience  duration_min  slide_count  summary
main_line  pages  evidence_map  artifacts  sources  uncertainty  change_records  contract
```

本 Skill 另外固定写出 4 个字段（契约"只增不减"）：

```
environment      # python 版本 / platform / python_pptx / pillow / pypdf / 中文字体探测结果（仅文件名）
generated_by     # 生成器标识
generated_at     # 生成时间（UTC ISO8601）
audit            # {plan_gates, evidence, deck, gates} —— 三道审计 + G1–G10 门快照随结果一起走
```

`artifacts` 子字段：
`editable_deck` / `talk_plan` / `evidence_map` / `evidence_audit` / `deck_audit` / `plan_gates` /
`previews{cover,grid,manifest,slide_pngs}` / `template_used` / `deck_mode` /
`preview_note` / `deck_limitation`。

## 3. 示例案例（`examples/case.json`）上的实测结果

命令与真实记录见 `TEST.md`；示例案例为 20 分钟 / 12 页组会汇报。

| 观测项 | 实测值 |
|-|-|
| `status` | `completed` |
| 页数 | 12 页（标题 / 目录 / 8 内容页 / 局限风险 / 问答备用页；`P3 pages=12 target=12`） |
| 内容页证据 | `evidence_audit.summary`：`content_pages=10, ok_pages=10, errors=0, derived_pages=0` |
| 计划门 | P1–P8 全过（`plan_gates.valid=true`，`errors=[]`） |
| deck | 12 张幻灯片；每张都有备注；`page-claim-NN` 元素齐备；OPC 完整；`deck_audit.valid=true` |
| 图绑定 | `Fig. 2 → materials/fig2.png`（运行期生成的示意图**真的被嵌入** deck：`page-figure-09` + `ppt/media/image1.png`）；`Fig. 3` / `Table 1` 无图片文件 → 页内诚实占位框并记录 |
| 预览 | 12 张 PNG（封面 + 10 内容页 + 网格，逐页缩略图另有 `preview_manifest.json`） |
| 自检 | `validate` 10/10 checks ok、`errors=[]`；`contract_check declared=16 missing=0 wrong_type=0`；G1–G9 全 true（G10 由 `selftest.py --package-check` 执行） |
| 运行时间 | 约 1.6–3.1 秒（本机 Python 3.13 + python-pptx 1.0.2 + Pillow 12.3.0） |
| 确定性 | 同输入双跑：`evidence_map/plan_gates/deck_audit/evidence_audit` 逐字节相同、12 张 PNG 逐字节相同、内容投影 sha 相同（仅记录性时间戳不同） |

## 4. 降级形态（缺依赖/缺材料时"应产出什么"）

| 触发 | 仍然产出 | `result.json` 里的如实记录 |
|-|-|-|
| 缺 `python-pptx` | `talk_plan/plan_gates/evidence_map/evidence_audit/previews/result.json/self_check.json` | `status=partial`、`artifacts.editable_deck=null`、`artifacts.deck_limitation`、`uncertainty` 一条、`change_records` 记明；命令仍返回 0 |
| 缺 Pillow | 除预览与 deck 外的全部（python-pptx 依赖 Pillow） | `status=partial` + `uncertainty`（预览失败）；单跑 `--skip-previews` 亦可 |
| 缺 `pypdf`/`PyPDF2` | 其余材料照常，PDF 记为未解析 | `sources[].parsed=false` + `note` + `uncertainty` + `status=partial` |
| 案例声明的材料不存在 | 其余材料照常 | `sources[]` 中 `kind=missing`、`evidence_map` 保留该条目、`uncertainty` 列出路径、`status=partial` |
| 材料为空/全部不可解析 | 仅结构性页面 | `status=partial` + `uncertainty` 说明"没有任何材料被解析为文本" |
| 案例未提供模板 | 用包内置主题母版 | `artifacts.deck_mode.mode=built-in-theme`、`template_used=null`、`uncertainty` 一条 |
| 模板自带示例页 | 保留其母版/版式，丢弃自带页后按冻结计划重建 | `deck_mode.template_slides_present/dropped` + `change_records` 记明；最终页数 == 冻结页数 |
| `case.json` 不可读 | 仍写一个最小 `result.json`（`status=failed` + `error`） | 命令返回 1（没有可用的契约结果） |

## 5. 复核命令（评审可独立执行）

```bash
python "$SKILL_DIR/scripts/validate_result.py" "$OUT/result.json"      # 结构 + 文件在盘 + 数字提示
python "$SKILL_DIR/scripts/check_contract.py"  "$OUT/result.json"      # 契约字段齐全/类型正确
python "$SKILL_DIR/scripts/evidence_audit.py"  "$OUT/result.json"      # 逐页逐字引文核验
python "$SKILL_DIR/scripts/verify_deck.py" "$OUT/editable_deck.pptx" \
       --expect-pages <N> --plan "$OUT/talk_plan.json"                 # deck 机器校验
python "$SKILL_DIR/scripts/selftest.py" "$OUT" --package-check "$SKILL_DIR"  # G1–G10 全链路 + 包约束
```

以上命令退出码 0 = 通过；`selftest.py --package-check` 会同时核对题面资源硬门
（≤50 个 UTF-8 文本文件、单文件 ≤500KB、合计 ≤2MB、无符号链接、无 `__pycache__`）。
