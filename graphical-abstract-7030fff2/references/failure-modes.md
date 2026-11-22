# failure-modes.md — 失败模式、降级策略与状态一致性契约

> 本文件是「可靠体验（10 分）」的落点文档：把"材料异常 / 模板缺失 / 依赖缺失 /
> 契约四形态 / 状态一致性"五类问题**逐条绑定到本包的真实机制**（脚本、退出码、
> `result.json` 字段）。**原则：任何降级都不允许静默成功** —— 要么写进
> `uncertainty` / `warnings` / `render_log.json`，要么直接非零退出。

## 1. 退出码语义（脚本级硬契约）

| 脚本 | 退出码 | 含义 | 行为 |
|-|-|-|-|
| `scripts/main.py` | `0` | 运行完成，`status ∈ {success, partial}` | 已写出 `result.json` 与全部产物 |
| `scripts/main.py` | `1` | **硬输入错误**：`case.json` 缺失/不可解析、抽取失败 | 打印 JSON 错误到 stdout，**不留半成品冒充成功** |
| `scripts/main.py` | `2` | **内部错误**：版面构建失败、SVG 写失败、或 `status=failed` | stderr/JSON 说明类型与消息 |
| `scripts/scaffold.py` | `0` / `1` | 方案骨架生成成功 / `case.json` 缺失或抽取失败 | `1` 时不写 plan |
| `scripts/spec_lint.py` | `0` / `1` | lint 通过 / 有 problems（**退出码即判据**） | problems 逐条打印 |
| `scripts/check_contract.py` | `0` / `1` | `result.json` 覆盖契约全部字段且无 null 违规 / 有缺口 | 缺口逐条打印 |

> `status` 与退出码的关系：`partial` 仍返回 `0`（产物完整、有已知限制）；
> **只有**读不到输入或产不出关键产物才是非零。这与题面"Harbor 契约"里
> "保留执行证据与中间产物、进展增量保存"的要求一致。

## 2. 材料异常（最高频）

| 情形 | 检测点 | 处置 | 记录位置 |
|-|-|-|-|
| `case.json` 不存在 / 不是合法 JSON | `main.py` 读取阶段（`os.path.isfile` + `json.load`） | **exit 1**，打印 `{"status":"failed","error":...}` | stdout |
| `case.json` 缺 `case_id` | `extract.run()` 回退链 `case_id→id→case→文件名` | 用文件名兜底，**不伪造** | `result.case_id`（可核验） |
| `source_material` 指向的文件不存在 | `extract.list_dir_text()` 静默跳过不存在项 | 继续用其余材料；实体/数据为空如实说明 | `content.notes` → `warnings` + `uncertainty` |
| 材料为空 / 无实体 / 无数据 | `extract.run()` 末尾 `notes` 判定 | 面板只放要点文本；实体/数据计数为 0 | `notes`（进 `uncertainty`）+ `content_summary` |
| 关键数值缺失（有指标名无数值） | `audit.missing_values` | 图上用「数值缺失」占位，**绝不编造数值** | `uncertainty` + `audit.missing_values` |
| 实体重名 / 歧义 | `extract.normalize_entities()` 同 id 首见优先 | 两项都列出并说明歧义 | `uncertainty`（D5） |
| 材料相互矛盾（两处数值不同） | 首见优先规则 | 保留首见值，矛盾进备注；**不取平均、不择优** | `uncertainty` |
| 材料是非 UTF-8（GBK/Latin-1） | `common.read_text(errors="replace")` | 以替换字符读取，不中断；异常字符进备注 | `warnings` |
| 材料是二进制（PDF/图片被误挂载） | `list_dir_text()` 只收 `.md/.txt/.json/.csv/.tex/.rst` | 跳过二进制；提示需要文本材料 | `content.notes` |

**反模式（禁止）**：为了让图"好看"而给缺值数据补一个看起来合理的数字；把材料里
没有的实体画上画布。二者都会直接打掉「结果正确性 15 分」与「结果可核验性 5 分」。

## 3. 模板缺失 / 预制资源缺失

本包**不含任何二进制模板**（无 `.pptx/.png/.pdf/.svg/.ttf`）——所有"模板"都是
**代码 + 文本规格 + 运行期生成**：

| 原形态（已删除） | 替代机制 | 缺失时的行为 |
|-|-|-|
| 预置示例图 `examples/output/*.svg/.png/.pdf` | `scripts/svgbuilder.py` + `scripts/preview.py` 运行时生成 | 生成失败即 `status=failed`（exit 2），并说明后端错误 |
| 预置图面规格 `examples/output/spec.json` | `scripts/figurespec.py` 纯函数确定性生成 | 版面异常 → `audit.bounds/layout_log` 记录 |
| 预置方案模板 | `assets/spec_template.json`（纯 JSON 文本，可复制） | 缺失则 `scaffold.py` 仍可从材料直接抽骨架 |
| 字体文件 `.ttf/.otf` | `preview.py::PIXEL_FONT_CANDIDATES` 运行期探测系统字体（`C:/Windows/Fonts`、`/usr/share/fonts`、`/System/Library/Fonts`） | 找不到就用默认字体；再不行走 Pillow 默认；如实记录字体名 |

**判定法**：如果某文件缺失会导致"必须由作者本机补一份二进制"，那它就不该进包。
本包内任何文件都可被删除后用脚本重新生成（`examples/output/**` 亦由本包实跑产出）。

## 4. 依赖缺失（逐级降级，禁止静默）

`scripts/preview.py` 的渲染后端链（第一条导入成功者胜出，选择结果**如实写入**
`render_log.json` 与 `result.deliverables[format=png].backend`）：

| 优先级 | 后端 | 产物 | 缺失时的表现 | 记录 |
|-|-|-|-|-|
| 1 | `matplotlib` | 抗锯齿 PNG + 矢量 PDF 预览 | 导入/渲染异常 → 自动降级 | `render_log.matplotlib_failed` → `uncertainty` |
| 2 | `Pillow` | PNG（ImageDraw + TrueType） | 异常 → 走纯 Python | `render_log.pil_failed` → `uncertainty` |
| 3 | 纯 Python（`zlib`+`struct`） | 几何精确的 PNG，文字为占位框 | 无 | `render_log.warnings` + `uncertainty`（文字为占位） |

其它依赖：

- **Python 版本**：≥3.8（`from __future__ import annotations`；类型注解 `dict | None` 需 3.10+，仅在
  `spec_lint.lint` 签名中出现，3.8 下运行时不受影响）。全部核心流程**只用标准库**；
- **第三方库**：仅 `matplotlib`（可选）、`Pillow`（可选）——`python-pptx`/`fontTools` 等**不需要**；
- **字体**：CJK 字体缺失时 PNG 里的中文会退化（matplotlib 会告警、Pillow 会走默认字体），
  但 **SVG 源文件里的 `<text>` 始终是真文字、可编辑**，这是"可编辑性"不受渲染降级影响的保证；
- **网络**：本 Skill **不联网**，不下载模板/字体/数据。

## 5. 契约四形态（`output_contract` 回显）

`extract.normalize_contract()` 接受 `dict`（正常）或 `str`（降级为 `{"note": <str>}`），
`main.py` 末尾按下列规则回显（**禁止 null**）：

| 形态 | 案例声明示例 | 回显规则 | 缺失时 |
|-|-|-|-|
| ① 字段→类型提示 | `"resolution_dpi": 300` | 顶层同名同值 | 写 `""`（空字符串，不写 null） |
| ② 字段→容器 | `"target_format": ["svg","png","pdf"]` | 顶层同名同值 | 写 `[]` |
| ③ 布尔开关 | `"colorblind_safe": true` | 顶层同名同值（真布尔） | 写 `false` |
| ④ 字段清单 | `"layer_names": [...]` | 回显实际使用的图层名 | 写 `[]` |

**保留键冲突**：若案例契约字段名与信封保留键（`schema_version/skill/case_id/status/
summary/task/deliverables/content_summary/provenance/sources/uncertainty/warnings/
change_records/audit/generated_utc/output_contract_echo/plan/spec_lint`）冲突，
顶层保留信封值，原值移到 `output_contract_echo[<key>]`（正常为空对象 `{}`）。

**自检命令**（本包提供，退出码即判据）：

```bash
python "$SKILL_DIR/scripts/check_contract.py" --result "$OUT/result.json" \
  --case "$SKILL_DIR/examples/case.json"
# exit 0 = 顶层已覆盖（信封 ∪ 案例 output_contract）全部字段；exit 1 = 有缺口（逐条打印）
```

## 6. 状态一致性（`status` 不得虚报）

| status | 成立条件（全部满足） | 违反时的处理 |
|-|-|-|
| `success` | SVG 良构 + PNG 有效 + 无缺值 + 无实体缺失 + 无越界 + 无输入 `notes` + **`spec_lint.valid=true`** | 任一不满足 → 降级为 `partial` |
| `partial` | 产物完整，但有：缺数值 / 实体未上画布 / 元素越界 / 渲染或字体降级 / 输入 notes / **plan 或 spec lint 有问题** | 必须在 `uncertainty` 逐条列明限制 |
| `failed` | SVG 未产出或不良构，或 PNG 无效，或 `case.json` 不可读 | exit 1（输入错误）或 exit 2（内部错误） |

一致性不变式（`audit.py` + `main.py` 共同保证）：

1. `deliverables[].path` 一定是**相对输出目录**的路径，且文件真实存在（PDF 未产出时必须
   `present:false` + `reason`，不得留空路径假装成功）；
2. `audit.checks.png.ok=false` ⇒ `status=failed`（不允许"图没出来但报 success"）；
3. `spec_lint.valid=false` ⇒ `status` 不可能是 `success`（`main.py` 显式降级为 `partial`）；
4. `change_records` 与 `provenance.source_files` 必须对应真实读取过的文件（含 sha256）；
5. 同输入重跑：`audit.determinism_probe.spec_sha16` 必须一致（布局是纯函数）。

## 7. 决策规则 D1–D10（与 `SKILL.md` §4 同一张表）

| # | 情形 | 决策 | 记录 |
|-|-|-|-|
| D1 | `case.json` 缺失/不可解析 | **exit 1**，不留半成品 | stdout |
| D2 | 材料文件缺失 | 以已有材料继续；实体/数据为空如实说明 | `uncertainty` + `content.notes` |
| D3 | 关键数值缺失 | 图上「数值缺失」占位，值进 uncertainty，**绝不编造** | `audit.missing_values` |
| D4 | 方案/规格 lint 不过 | 先修正；确属硬性限制则记录后继续并降 `partial` | `result.plan.lint` / `result.spec_lint` |
| D5 | 实体重名/歧义 | 取首次定义，两项都列出 | `uncertainty` |
| D6 | 文字溢出面板 | 自动缩字号（下限 8px）+ 截断提示 | `audit.layout_log` |
| D7 | 元素越界画布 | 自动收缩；无法收缩进越界清单 | `audit.bounds` |
| D8 | 字体缺失（CJK/西文） | 探测候选路径逐级降级，字体名如实记录 | `render_log.json` + `uncertainty` |
| D9 | 导出失败（PNG/PDF） | 换后端重试（matplotlib→Pillow→纯 Python）；PDF 不可用如实标注 | `render_log.json` |
| D10 | 四要素缺面板 / 图层命名违规 | 绘制前被 plan/spec lint 拦截；补救=补面板内容或归入契约层 | `audit.four_element_coverage` / `audit.layer_naming` |

## 8. 运行环境适配（已知跨平台坑）

| 坑 | 处理 |
|-|-|
| Windows 控制台 GBK 打不出 `µ`（µg/mL）等字符 | `main.py` / `scaffold.py` / `spec_lint.py` CLI 入口先 `sys.stdout.reconfigure(encoding="utf-8")` |
| Windows 默认换行 CRLF | 所有写文件走 `common.write_json/write_text`（`newline="\n"`，UTF-8） |
| cwd 不是技能根目录 | 脚本用 `common.SCRIPT_DIR = dirname(abspath(__file__))` 自定位；命令用 `$SKILL_DIR` 绝对化 |
| 官方容器路径 | 输入 `/input/case.json`、工作区 `/app/work`、产物 `/app/output`（`--case/--out` 显式传入） |
| 画布尺寸超限 | `spec_lint` 夹紧区间 `[600, 4000]`，越界即 problems |

## 9. 快速自查清单（出问题先看这里）

1. 退出码是 0/1/2 中的哪个？→ 对第 1 节定位到具体阶段；
2. `result.json.status` 是 `partial` 时，`uncertainty` 里有哪几条？→ 对第 6 节判定是否可接受；
3. `audit.json` 里 `entity_coverage.missing` / `encoding_consistency.missing_from_canvas` /
   `bounds.outside_count` / `missing_values` / `four_element_coverage.missing` /
   `layer_naming.bad` 是否为空？→ 非空即对应第 2、6 节的处置路径；
4. `render_log.json.backend` 实际是哪个？→ 对第 4 节确认降级是否被如实记录；
5. `python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>`
   是否 exit 0？→ 契约四形态的最终判据。
