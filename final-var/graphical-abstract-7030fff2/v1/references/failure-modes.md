# failure-modes.md — 失败模式 ↔ 决策规则 D1–D20 对照矩阵

> **本文件与 `SKILL.md` §4 使用同一套编号**：SKILL.md 给规则，本文件给"怎么检测、
> 怎么验证、留了什么证据"。出问题时先在 `SKILL.md` §6 分诊，再回到本文件的对应行。
>
> 一律原则：**任何降级都不允许静默成功** —— 要么写进 `uncertainty` / `warnings` /
> `render_log.json`，要么直接非零退出。**没有记录位点的"处置"等同于没处置。**

## 1. 退出码语义（脚本级硬契约，与 D1/D18/D19 绑定）

| 脚本 | 退出码 | 含义 | 关联规则 | 行为 |
|-|-|-|-|-|
| `scripts/main.py` | `0` | 运行完成，`status ∈ {success, partial}` | D18（partial 也算完成） | 已写出 `result.json` 与全部产物 |
| `scripts/main.py` | `1` | 硬输入错误：`case.json` 缺失/不可解析、抽取失败 | **D1** | 打印 `{"status":"failed","error":…}`，不留半成品 |
| `scripts/main.py` | `2` | 内部错误：版面/SVG/PNG 产出失败，或 `status=failed` | **D19** | stderr/JSON 说明类型与消息 |
| `scripts/scaffold.py` | `0` / `1` | 方案骨架生成成功 / 输入不可用 | D1/D14 | `1` 时不写 plan |
| `scripts/spec_lint.py` | `0` / `1` | lint 通过 / 有 problems（**退出码即判据**） | **D14/D18** | problems 逐条打印 |
| `scripts/check_contract.py` | `0` / `1` | 契约全覆盖且无 null / 有缺口 | **D15/D16/D17** | 缺口逐条打印 |

判读顺序：**先看退出码定位阶段，再看 `result.json.status` 定位严重度。**

## 2. 逐条对照矩阵（D1–D20）

| # | 失败模式（触发条件） | 检测点（谁发现） | 处置与降级 | 验证命令 / 证据字段 |
|-|-|-|-|-|
| D1 | `case.json` 不存在或非法 JSON | `main.py` 读取阶段 `isfile` + `json.load` | exit 1，打印失败 JSON，**不留半成品** | `echo $?` → 1；stdout 的 `error` |
| D2 | `case.json` 缺 `case_id` | `extract.run()` 回退链 | 用文件名兜底，标注来源 | `result.case_id` + `uncertainty` |
| D3 | `task.md` 缺失 | `main.py` 定位 `<case_dir>/task.md` 失败 | 只用 case + 材料；要点由材料小节映射 | `warnings` / `content.notes` |
| D4 | `source_material` 文件/目录缺失或为空 | `extract.list_dir_text()` 跳过不存在项 | 用其余材料继续，计数如实为 0 | `content_summary` + `uncertainty` |
| D5 | 指标名在材料中无数值 | `audit.missing_values` | 图上「数值缺失」占位；数值只进备注 | `audit.missing_values`；`uncertainty` |
| D6 | 实体重名 / 同名不同物 | `extract.normalize_entities()` 同 id 首见优先 | 两项并列并标注歧义；歧义未解不画该关系箭头 | `uncertainty`（含两处 `src`） |
| D7 | 材料两处数值矛盾 | 抽取阶段双源比对 | 保留首见值，矛盾处写两个 `src`；**不平均、不择优** | `uncertainty` |
| D8 | 材料非 UTF-8（GBK/Latin-1） | `common.read_text(errors="replace")` | 以替换字符读取，不中断；异常字符进备注 | `warnings` |
| D9 | 材料为二进制（PDF/图片误挂载） | `list_dir_text()` 扩展名白名单 | 跳过二进制，提示需要文本材料 | `content.notes` |
| D10 | CJK 字体缺失（中文渲染异常） | `preview.py::PIXEL_FONT_CANDIDATES` 探测结果 | 逐级降级到默认字体；**SVG `<text>` 仍为真文字** | `render_log.font`；`uncertainty` |
| D11 | matplotlib 不可用/抛错 | `preview.py` 导入与渲染异常捕获 | 切 Pillow；再失败走纯 Python PNG（文字占位并注明） | `render_log.backend`；`deliverables[format=png].backend` |
| D12 | PDF 导出失败/后端不支持 | `preview.py` PDF 分支 | PNG 照常；PDF 标 `present:false` + `reason` | `deliverables[format=pdf]` |
| D13 | 文字溢出面板 / 元素越界 | `audit.layout_log` / `audit.bounds` | 自动缩字号（下限 8px）与坐标夹紧，仍溢出进清单 | `audit.layout_log`；`audit.bounds.outside_count` |
| D14 | 方案/规格 lint 不过 | `spec_lint.lint_plan()` / `lint(spec, content)` | 先修 plan/spec；修不动则记录后继续并降 `partial` | `python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan plan.json` → exit 0 |
| D15 | 契约字段无真实值 | `main.py` 契约回显阶段 | 按声明类型给 `""`/`[]`/`false`/`{}`；**禁 null** | `check_contract.py` 的 `contract_null` 必须为空 |
| D16 | 契约键与信封保留键冲突 | 保留键集合比对 | 顶层留信封值，原值进 `output_contract_echo[<key>]` | `result.output_contract_echo`（正常为 `{}`） |
| D17 | 契约声明类型与实际不符 | `check_contract.py` 类型观察 | 以真实值写入并在备注说明偏差 | `uncertainty` + 自查输出 |
| D18 | `spec_lint.valid=false` | `main.py` 状态判定 | `status` 判 `partial`，**不可能是 success** | `result.spec_lint` + `uncertainty` |
| D19 | 关键产物缺失/无效（SVG 不良构、PNG 无效） | `audit.checks.svg_well_formed` / `checks.png` | `status=failed` 且 exit 2；已写产物保留并列出 | `audit.checks`；stderr |
| D20 | 同输入重跑结构不一致 | `audit.determinism_probe.spec_sha16` 两次比对 | 排查时间戳/随机数；未修正前声明不稳定 | `audit.determinism_probe` |

## 3. 五类分支 → 规则号速查（与 `SKILL.md` §5 同序）

| 类 | 分支 | 规则 |
|-|-|-|
| 材料异常 | case 缺失/不可解析 | D1 |
| | 材料缺失/为空 | D4 |
| | 关键数值缺失 | D5 |
| | 实体重名/歧义 | D6 |
| | 材料数值矛盾 | D7 |
| | 非 UTF-8 / 二进制误挂载 | D8 / D9 |
| 模板缺失 | 预置渲染件（本包不带） | 结构上不触发（运行时生成） |
| | `assets/spec_template.json` 缺失 | D14（`scaffold.py` 仍可抽骨架） |
| 依赖缺失 | matplotlib / Pillow | D11 |
| | CJK 字体 | D10 |
| | PDF 后端 | D12 |
| 契约四形态 | ①类型提示 / ②容器 / ③布尔 / ④字段清单 | D15（四种形态同一规则，空值形态不同） |
| | 保留键冲突 | D16 |
| | 类型不符 | D17 |
| 状态不一致 | lint 不过 | D14 / D18 |
| | 产物缺失/无效 | D19 |
| | 重跑漂移 | D20 |
| | 路径绝对化或指向不存在文件 | D19 |

## 4. 科学诚实性红线（比任何降级都优先）

| 反模式 | 后果 | 本包如何拦住 |
|-|-|-|
| 给缺值数据补一个"看起来合理"的数字 | 直接打掉「结果正确性 15 分」+「结果可核验性 5 分」 | D5：缺值只占位；`audit.missing_values` 留证 |
| 把材料里没有的实体画上画布 | 同上 | 抽取阶段要求逐项 `src`；无源不上画布 |
| 为了让图"平衡"而平均两个矛盾数值 | 断掉可核验链 | D7：双 `src` 并列，不平均不择优 |
| 用自造结论填充结论面板 | 结论不可核验 | `ga-four-elements.md` §2 第 4 条：结论必须能在材料中找到对应表述 |

## 5. 运行环境适配（已知跨平台坑 → 对应规则）

| 坑 | 处理 | 规则 |
|-|-|-|
| Windows 控制台 GBK 打不出 `µ` 等字符 | CLI 入口先 `sys.stdout.reconfigure(encoding="utf-8")` | 环境适配 |
| Windows 默认 CRLF | 写文件统一走 `common.write_json/write_text`（`newline="\n"`, UTF-8） | 环境适配 |
| cwd 不是技能根 | 脚本用 `common.SCRIPT_DIR` 自定位；命令以 `$SKILL_DIR` 绝对化 | SKILL.md §0 |
| 官方容器路径 | 输入 `/input/case.json`、工作区 `/app/work`、产物 `/app/output` | 运行契约 |
| 画布尺寸超限 | `spec_lint` 夹紧区间 `[600, 4000]`，越界即 problems | D14 |

## 6. 复现本文件结论的最小命令集

```bash
SKILL_DIR=<技能根>
# D1：缺输入 → 1
python "$SKILL_DIR/scripts/main.py" --case /tmp/nope.json --out /tmp/nope-out;  echo $?   # 1
# D14：未定稿骨架 → 1；已定稿方案 → 0
python "$SKILL_DIR/scripts/scaffold.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/plan_skel.json; echo $?   # 0
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan /tmp/plan_skel.json; echo $?   # 1（四要素待填）
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan "$SKILL_DIR/examples/plan.example.json"; echo $?  # 0
# D15–D17 / D18：契约与状态
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-out; echo $?   # 0
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/ga-out/result.json --case "$SKILL_DIR/examples/case.json"; echo $?  # 0
# D20：确定性（两次结构指纹一致）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-det1 >/dev/null
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-det2 >/dev/null
python -c "import json;a=json.load(open('/tmp/ga-det1/audit.json'));b=json.load(open('/tmp/ga-det2/audit.json'));print(a['determinism_probe']['spec_sha16']==b['determinism_probe']['spec_sha16'])"
```

实测结果（本机 Python 3.13.9 / matplotlib 3.10.6 / Pillow 12.3.0）见 `TEST.md` 的 T2–T8。

## 7. 表外情形怎么办（"先记后判"）

1. **先记**：立刻把现象写进 `uncertainty`（现象 + 影响面 + 已尝试的动作）；
2. **再判**：判断它属于 §2 的哪一类；能归入就走那条规则的处置与降级；
3. **归类不了**：按"保守优先"处理 —— 宁可 `status=partial` 并写明限制，也不冒 `success`；
4. **回头补表**：若该情形值得长期处理，把它补进本文件与 `SKILL.md` §4（两边同时补，编号连续）。
