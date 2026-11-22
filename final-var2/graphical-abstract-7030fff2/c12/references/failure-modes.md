# failure-modes.md — 失败模式的检测、处置与「它毁掉哪个指标」（R1–R14）

> 本文件的规则编号（R1–R14）与 `SKILL.md` §5 的速查表**同号**。写法与前作不同之处在于
> 每一行都标注**该失败会打掉哪个可测指标**（G1–G8，口径见 `references/GAIN-PROTOCOL.md` §3）：
> 这样"异常处理"不再是笼统的"要有兜底"，而是能指出"兜底没做，哪一项指标会掉"。
>
> 总原则：**降级必须留痕**。留痕位置只有四个：`result.json.uncertainty` /
> `result.json.warnings` / `render_log.json` / 非零退出码。四处都没有 = 静默成功 = 违规。

## 1. 退出码 → 阶段 → 规则

| 退出码 | 出处 | 含义 | 首查规则 |
|-|-|-|-|
| `0` | `main.py` | 完成，`status ∈ {success, partial}` | R13（partial 的成因） |
| `1` | `main.py` | 输入不可用（`case.json` 缺失/不可解析/抽取失败） | R1 |
| `2` | `main.py` | 内部错误或 `status=failed`（版面/SVG/PNG 未产出） | R11 / 产物链 |
| `0/1` | `spec_lint.py` | lint 通过 / 有 problems（**退出码即判据**） | R13 |
| `0/1` | `check_contract.py` | 契约完整且无 null / 有缺口 | R14 |
| `0/1` | `scaffold.py` | 方案骨架成功 / 输入不可用 | R1 |

## 2. 规则矩阵：触发 → 检测 → 处置 → 受害指标 → 证据

| # | 触发条件 | 检测点（谁发现） | 处置与降级 | 打掉哪个指标 | 证据字段 |
|-|-|-|-|-|-|
| R1 | `case.json` 不存在/非法 JSON | `main.py` 的 `isfile` + `json.load` | **exit 1**，打印失败 JSON，不留半成品 | 全部（无法产出） | stdout `error` |
| R2 | `case_id` 缺失 | `extract.run()` 回退链 | 用文件名兜底并标注 | G5（契约回显） | `result.case_id` / `uncertainty` |
| R3 | `task.md` 缺失 | 定位 `<case_dir>/task.md` 失败 | 面板要点改由材料小节映射；不填填充句 | G3（四要素内容） | `warnings` |
| R4 | 材料缺失/为空 | `extract.list_dir_text()` 跳过缺失项 | 用可用材料继续；计数如实为 0 | G3 / G4 | `content_summary` / `uncertainty` |
| R5 | 有指标名无数值 | `audit.missing_values` | 「数值缺失」占位；该点移出编码子图 | G4（可定位率分母变化） | `audit.missing_values` |
| R6 | 实体重名/歧义 | `normalize_entities()` 首见优先 | 两项并列；歧义未解不画该关系箭头 | G2（该元素无可靠 `src`） | `uncertainty` |
| R7 | 材料两处数值矛盾 | 抽取阶段双源比对 | 首见优先，双 `src` 并列；**不平均不择优** | G4（若静默改写则彻底失效） | `uncertainty` |
| R8 | 材料非 UTF-8 | `common.read_text(errors="replace")` | 替换字符读取；乱码段仅作背景 | G4 | `warnings` |
| R9 | 二进制材料误挂载 | `list_dir_text()` 扩展名白名单 | 跳过并提示需要文本材料 | G3 / G4 | `content.notes` |
| R10 | 字体缺失（CJK） | `preview.py` 候选路径探测结果 | 逐级降级到默认字体；SVG `<text>` 仍为真文字 | G1b（PNG 侧文字缺失） | `render_log.font` |
| R11 | matplotlib/Pillow 不可用 | `preview.py` 导入/渲染异常 | 后端链回退；最终纯 Python PNG（文字占位） | G7（后端降级需留痕） | `render_log.backend` |
| R12 | 文字溢出/元素越界 | `audit.layout_log` / `audit.bounds` | 缩字号（下限 8px）+ 坐标夹紧；仍溢出进清单 | G3（内容被截断） | `audit.layout_log` / `bounds` |
| R13 | 方案或规格 lint 不过 | `spec_lint.lint_plan()` / `lint(spec, content)` | 先修；修不动则记录后继续并降 `partial` | G5 与验收（不得 success） | `result.plan.lint` / `result.spec_lint` |
| R14 | 契约字段无真实值 / 键与信封冲突 | `main.py` 回显 + `check_contract.py` | 按 `""`/`[]`/`false`/`{}` 回显；冲突值进 `output_contract_echo` | G5（禁 null） | `check_contract.py` exit 0 |

补充：**PDF 不可用**（`--pdf` 时）→ PNG 照常交付，PDF 标 `present:false` + `reason`；
不允许空路径假装成功（受害项：交付完整性；证据：`deliverables[format=pdf]`）。

## 3. 「受害指标」视角的排序（先修哪个）

| 优先级 | 失败类型 | 理由 |
|-|-|-|
| P0 | R1（读不到输入） | 无产物，所有指标归零 |
| P0 | 产物链断裂（SVG 不良构 / PNG 无效） | 实际效果整块失效，且不得报 success |
| P1 | R5 / R7（数值缺源 / 静默改写矛盾值） | 直接摧毁"可核验性"，且属于**科学诚实性**问题 |
| P1 | R13 / R14（lint 不过 / 契约缺口） | 交付物不可复核；契约缺口会直接反映在评分侧 |
| P2 | R6 / R8 / R9（歧义/编码/二进制） | 影响个别元素或个别面板，可局部降级 |
| P2 | R10 / R11 / R12（渲染侧） | 影响预览观感，SVG 可编辑性与结构证据仍在 |
| P3 | R2 / R3（元信息与要点来源） | 影响回显字段与面板丰富度，不影响主线 |

## 4. 契约四种声明形态的失败边界（R14 细化）

| 形态 | 案例声明 | 缺真实值时 | 常见错误写法 |
|-|-|-|-|
| ① 字段→类型提示 | `"resolution_dpi": 300` | `""` | 写 `null`（契约缺口） |
| ② 字段→容器 | `"target_format": ["svg","png","pdf"]` | `[]` | 写 `"svg,png"`（类型不符） |
| ③ 布尔开关 | `"colorblind_safe": true` | `false`（真布尔） | 写 `"false"` 字符串 / `0` |
| ④ 字段清单 | `"layer_names": [...]` | `[]`；有值时回显实际图层名 | 回显期望图层名而非实际 |

保留键冲突（`case_id/status/audit/…` 等信封键）→ 顶层留信封值，原值进
`result.output_contract_echo[<key>]`（正常为 `{}`）。判定命令：

```bash
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>
# exit 0 = 顶层覆盖「信封 18 键 ∪ 案例 output_contract 全部字段」且无 null
```

## 5. 状态一致性不变式（谁保证、怎么验）

| 不变式 | 保证者 | 验证 |
|-|-|-|
| `deliverables[].path` 必为相对输出目录且文件真实存在 | `main.py` 写产物后回填 | `ls <out>` 与 `result.deliverables` 对照 |
| PNG 无效 ⇒ `status=failed` | `audit.checks.png` + `main.py` 状态判定 | `python -c "import json;a=json.load(open('<out>/audit.json'));print(a['checks']['png'])"` |
| `spec_lint.valid=false` ⇒ 不允许 `success` | `main.py` 显式降级 | `result.spec_lint` 与 `result.status` 同看 |
| `change_records` / `provenance.source_files` 对应真实读过的文件（含 sha256） | 抽取阶段记录 | `result.provenance.source_files` |
| 同输入重跑结构一致 | 纯函数版面 + 探针 | `audit.determinism_probe.spec_sha16`；或 `gain_harness.py --compare` |

## 6. 环境适配坑（跨平台）

| 坑 | 处理 |
|-|-|
| Windows 控制台 GBK 打不出 `µ` 等字符 | CLI 入口 `sys.stdout.reconfigure(encoding="utf-8")` |
| Windows 默认 CRLF | 统一 `common.write_json/write_text`（`newline="\n"`, UTF-8） |
| cwd 不是技能根 | `common.SCRIPT_DIR` 自定位；命令用 `$SKILL_DIR` 绝对化 |
| 官方容器路径 | 输入 `/input/case.json`、工作区 `/app/work`、产物 `/app/output` |
| 画布尺寸超限 | `spec_lint` 夹紧 `[600, 4000]`，越界即 problems（R13） |
| 中文标签渲染缺失 | 字体候选探测链（R10）；SVG 文字始终可编辑 |

## 7. 复现片段（把本文件的处置逐条跑一遍）

```bash
SKILL_DIR=<技能根>
python "$SKILL_DIR/scripts/main.py" --case /tmp/absent.json --out /tmp/x; echo $?   # 1 → R1
python "$SKILL_DIR/scripts/scaffold.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/plan_skel.json
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan /tmp/plan_skel.json; echo $?  # 1 → R13（骨架未定稿）
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan "$SKILL_DIR/examples/plan.example.json"; echo $?  # 0
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-out; echo $?  # 0
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/ga-out/result.json --case "$SKILL_DIR/examples/case.json"; echo $?  # 0 → R14
python "$SKILL_DIR/scripts/gain_harness.py" --out /tmp/ga-out --case "$SKILL_DIR/examples/case.json" \
       --material "$SKILL_DIR/examples/material.md" --label A     # 看 G1–G7 是否达标
```

实测结果见 `TEST.md`。

## 8. 表外情形：三条不可协商的底线

1. **不编造**：材料里没有的数值/实体/结论，一律不上画布（R5/R7 的延伸）；
2. **不静默**：任何降级都要落到 §开头列出的四个留痕位置之一；
3. **不虚报**：`status` 只能是实际状态；拿不准时选 `partial` 并把不确定项写清楚 ——
   `partial` 加完整证据，比 `success` 加空洞自述更可用。
