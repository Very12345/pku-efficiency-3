# failure-modes.md — 按机制归组的失败矩阵（K1–K16）与已知边界

> 编号与 `SKILL.md` §3 的决策规则**同号**（K1–K16）。与前作的差别：这里按**机制归属**
> （M1 来源 / M2 门 / M3 交付态 / 复用与环境）组织，每一行给：
> 触发 → 检测点 → 处置与降级 → 证据字段；并在 §5 明确写出**机制管不到的地方**。
>
> 唯一硬原则：**降级必须留痕**。留痕位置只有四个 —— `result.uncertainty`、
> `result.warnings`、`render_log.json`、非零退出码。四处都没有 = 静默成功 = 违规。

## 1. 退出码语义（脚本级硬契约）

| 脚本 | 退出码 | 含义 | 关联规则 |
|-|-|-|-|
| `main.py` | `0` | 完成；`status ∈ {success, partial}` | K8（partial 成因） |
| `main.py` | `1` | 输入不可用：`case.json` 缺失/不可解析、抽取失败 | 输入组（见 §2.0） |
| `main.py` | `2` | 内部错误或 `status=failed`（版面/SVG/PNG 未产出） | K13 |
| `spec_lint.py` | `0` / `1` | lint 通过 / 有 problems（**退出码即判据**） | K7–K10 |
| `check_contract.py` | `0` / `1` | 契约全覆盖且无 null / 有缺口 | K11–K12 |
| `scaffold.py` | `0` / `1` | 方案骨架成功 / 输入不可用 | 输入组 |

## 2. 矩阵

### 2.0 输入组（所有机制的前置）

| 触发 | 检测点 | 处置与降级 | 证据 |
|-|-|-|-|
| `case.json` 不存在/非法 JSON | `main.py` 的 `isfile` + `json.load` | **exit 1**，打印失败 JSON，不留半成品 | stdout `error` |
| `case_id` 缺失 | 抽取回退链 | 用文件名兜底并标注 | `result.case_id` / `uncertainty` |
| `task.md` 缺失 | 定位 `<case_dir>/task.md` 失败 | 面板要点改由材料小节映射 | `warnings` |

### 2.1 M1 组：来源挂接与科学诚实（K1–K6）

| # | 触发 | 检测点 | 处置与降级 | 证据 |
|-|-|-|-|-|
| K1 | 材料里找不到某数值 | `audit.missing_values` | 「数值缺失」占位；该点移出编码子图 | `audit.missing_values` |
| K2 | 实体重名/歧义 | `normalize_entities()` 首见优先 | 两项并列；歧义未解不画该实体关系箭头 | `uncertainty` |
| K3 | 材料两处数值矛盾 | 抽取阶段双源比对 | 首见优先、双 `src` 并列；**不平均不择优** | `uncertainty` |
| K4 | 材料为空/缺实体/缺数据 | `extract.run()` 末尾 notes 判定 | 计数如实为 0；面板不填填充句 | `content_summary` / `uncertainty` |
| K5 | 材料非 UTF-8 / 二进制误挂载 | `read_text(errors="replace")` / 扩展名白名单 | 替换字符读取 / 跳过并提示 | `warnings` / `content.notes` |
| K6 | 元素无 `src` 想上画布 | `spec_lint` 的 `no_src` 检查 | **拒绝上画布**（实测：删 1 个 `src` → exit 1） | `result.spec_lint.problems` |

### 2.2 M2 组：两道 lint 门（K7–K10）

| # | 触发 | 检测点 | 处置与降级 | 证据 |
|-|-|-|-|-|
| K7 | 方案 `four_elements` 有空项 | `lint_plan()` 逐面板检查 | 补一句话说明后重跑；补不出则该面板只放结构 | `result.plan.lint` |
| K8 | 方案/规格 lint 报 problems | `lint_plan()` / `lint(spec, content)` | 先修；确属硬限则记录后继续并降 `partial`，**不得 success** | `result.spec_lint` |
| K9 | 图例值与画面数值不一致 | 编码词表 + legend↔data 比对 | 重算编码；无法一致则撤下该编码项（实测：删 1 个图例条目 → exit 1） | `result.spec_lint.problems` |
| K10 | 画布尺寸超限（<600 / >4000） | 夹紧区间检查 | 夹紧并记录；仍溢出则缩减面板内容 | `spec_lint` problems / `audit.layout_log` |

### 2.3 M3 组：交付态一致性（K11–K14）

| # | 触发 | 检测点 | 处置与降级 | 证据 |
|-|-|-|-|-|
| K11 | 契约字段缺真实值 | 回显阶段按声明类型判定 | `""` / `[]` / `false` / `{}`；**禁 null** | `check_contract.py` 的 `contract_null` |
| K12 | 契约键与信封保留键冲突 | 保留键集合比对 | 顶层留信封值，原值进 `output_contract_echo[<key>]` | `result.output_contract_echo` |
| K13 | 产物缺失/无效（SVG 不良构、PNG 无效） | `audit.checks.svg_well_formed` / `checks.png` | `status=failed` + **exit 2**；已写产物保留并列出 | `audit.checks` / stderr |
| K14 | 同输入重跑结构漂移 | `determinism_probe.spec_sha16` 两次比对 | 排查时间戳/随机数；未修正前声明不稳定 | `audit.determinism_probe` |

### 2.4 复用与环境组（K15–K16）

| # | 触发 | 检测点 | 处置与降级 | 证据 |
|-|-|-|-|-|
| K15 | 字体缺失 / 后端缺失 / PDF 不可用 | `preview.py` 探测与异常捕获 | 字体候选探测；后端链 matplotlib→Pillow→纯 Python PNG；PDF 标 `present:false` + `reason` | `render_log.json` / `deliverables` |
| K16 | 想改图层/编码/指标 | 三处一致性检查（规范 / 脚本 / TEST.md） | 补齐三处才算完成；只改一处视为未完成 | 相关规范与 `TEST.md` |

## 3. 优先级（先修哪个）

| 级别 | 类型 | 理由 |
|-|-|-|
| P0 | 输入不可用；产物链断裂（K13） | 无产物或不可复核，其余全部无意义 |
| P1 | K1 / K3（缺源 / 静默改写矛盾值） | 属科学诚实性；直接击穿可核验性 |
| P1 | K6 / K8 / K9 / K11（门与契约） | 结构与交付态的可判定性 |
| P2 | K2 / K4 / K5（局部材料问题） | 影响个别元素/面板，可局部降级 |
| P2 | K15（渲染侧） | 影响预览观感；SVG 可编辑性与结构证据仍在 |
| P3 | 输入组的元信息项 | 影响回显丰富度，不影响主线 |

## 4. 契约四形态的失败边界（K11–K12 细化）

| 形态 | 声明示例 | 缺真实值时 | 常见错误 |
|-|-|-|-|
| ① 类型提示 | `"resolution_dpi": 300` | `""` | 写 `null` |
| ② 容器 | `"target_format": ["svg","png","pdf"]` | `[]` | 写 `"svg,png"` |
| ③ 布尔 | `"colorblind_safe": true` | `false`（真布尔） | 写 `"false"` / `0` |
| ④ 字段清单 | `"layer_names": [...]` | `[]`；有值时回显**实际**图层名 | 回显期望图层名 |

判定：`python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>`
→ **exit 0** 表示顶层已覆盖「信封 18 键 ∪ 案例契约全部字段」且无 null。

## 5. 机制管不到的地方（已知边界，含实测反例）

| 边界 | 实测/说明 | 当前替代做法 |
|-|-|-|
| `case.json` 数值与材料正文冲突 | **不拦**：把材料里的 `85 %` 改成 case 里的 `84 %`，运行仍 `status=success`、`uncertainty=[]`、`missing_values=[]`，SVG 同时含 84 与 85 | Agent 按 K3 的精神人工比对材料与 case 数值，差异写入 `uncertainty`（未实现自动交叉核对） |
| 图"讲得对不对" | lint 只查结构（有源、有图例、面板齐、画布合法） | 领域判断由人负责；`references/ga-four-elements.md` 给内容不变式 |
| 复杂表格 / 多图材料 | 抽取依赖文本结构 | Agent 复核抽取结果并在 `change_records` 留痕 |
| 渲染件逐像素回归 | 未实现（只做签名/尺寸/良构检查） | 需要时用 `gain_harness.py --compare` 比结构指纹 |
| 主观排版偏好 | 不属于判据 | 用 `TEMPLATE.md` 的版式与字号约定减少随意性 |

## 6. 环境与跨平台坑

| 坑 | 处理 |
|-|-|
| Windows 控制台 GBK 打不出 `µ` 等字符 | CLI 入口 `sys.stdout.reconfigure(encoding="utf-8")` |
| Windows 默认 CRLF | 统一 `common.write_json/write_text`（`newline="\n"`, UTF-8） |
| cwd 不是技能根 | `common.SCRIPT_DIR` 自定位；命令用 `$SKILL_DIR` |
| 官方容器路径 | 输入 `/input/case.json`、工作区 `/app/work`、产物 `/app/output` |
| 中文标签缺字形 | 字体候选探测（K15）；实测基础做法出现 177 条缺字告警 |
| 在包内跑脚本 | 会生成 `__pycache__` 触发预检失败 → **一律在包外副本运行** |

## 7. 复现片段

```bash
SKILL_DIR=<技能根>; OUT=<临时输出目录>
python "$SKILL_DIR/scripts/main.py" --case /tmp/absent.json --out /tmp/x; echo $?          # 1（输入组）
python "$SKILL_DIR/scripts/scaffold.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/plan_skel.json
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan /tmp/plan_skel.json; echo $?   # 1（K7：四要素待填）
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan "$SKILL_DIR/examples/plan.example.json"; echo $?  # 0
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out "$OUT"; echo $?              # 0
python "$SKILL_DIR/scripts/check_contract.py" --result "$OUT/result.json" --case "$SKILL_DIR/examples/case.json"; echo $?  # 0（K11）
# K6 / K9 的负控（各只改一处）：
python -c "import json;s=json.load(open('$OUT/spec.json'));e=[x for x in s['elements'] if x.get('src') and x.get('role','').startswith(('entity','datum'))][0];e.pop('src');json.dump(s,open('/tmp/spec_nosrc.json','w'))"
python "$SKILL_DIR/scripts/spec_lint.py" --spec /tmp/spec_nosrc.json --content "$OUT/content.json"; echo $?   # 1（K6）
python -c "import json;s=json.load(open('$OUT/spec.json'));s['legend']=s['legend'][:-1];json.dump(s,open('/tmp/spec_nolegend.json','w'))"
python "$SKILL_DIR/scripts/spec_lint.py" --spec /tmp/spec_nolegend.json --content "$OUT/content.json"; echo $? # 1（K9）
```

实测退出码见 `TEST.md` 的 T3–T5。

## 8. 三条不可协商的底线

1. **不编造**：材料里没有的数值/实体/结论不上画布（K1/K3/K4 的延伸）；
2. **不静默**：任何降级都要落到本文开头列的四个留痕位置之一；
3. **不虚报**：`status` 只能是实际状态；拿不准时选 `partial` 并把不确定项写清楚 ——
   带完整证据的 `partial` 比空洞的 `success` 更可用，也更接近评分维度的要求。
