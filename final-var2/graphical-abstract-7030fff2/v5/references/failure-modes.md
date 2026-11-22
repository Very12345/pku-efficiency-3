# failure-modes.md — 失败模式、降级策略与状态一致性（v5 轴：多案例泛化与题集）

> 本文件是「可靠体验（10 分）」的落点：把"材料异常 / 模板缺失 / 依赖缺失 / 契约四形态 /
> 状态一致性"五类问题**逐条绑定到本包的真实机制**（脚本、退出码、`result.json` 字段），
> 并尽量给出**来自题集实测**的证据（哪个案例、哪条字段）。
>
> **原则：任何降级都不允许静默成功** —— 要么写进 `uncertainty` / `warnings` /
> `render_log.json`，要么直接非零退出。
> 判据（可判定）：进程 `exit 0` 且 `status=success`，而注入/构造的缺陷在 `uncertainty`
> 与相关字段里都没有记录 ⇒ 属于**静默失败**，是本包要避免的形态。

## 1. 退出码语义（脚本级硬契约）

| 脚本 | 退出码 | 含义 | 行为 |
|-|-|-|-|
| `scripts/main.py` | `0` | 运行完成，`status ∈ {success, partial}` | 已写出 `result.json` 与全部产物 |
| `scripts/main.py` | `1` | **硬输入错误**：`case.json` 缺失/不可解析、抽取失败、`--plan` 不可解析 | 打印 JSON 错误到 stdout，**不留半成品冒充成功** |
| `scripts/main.py` | `2` | **环境/内部错误**：输出目录不可用、版面或 SVG 失败、`status=failed` | 打印 JSON 错误（`output directory not usable` 等） |
| `scripts/scaffold.py` | `0` / `1` | 方案骨架生成成功 / `case.json` 缺失或抽取失败 | `1` 时不写 plan |
| `scripts/spec_lint.py` | `0` / `1` | lint 通过 / 有 problems（**退出码即判据**） | problems 逐条打印 |
| `scripts/check_contract.py` | `0` / `1` / `2` | 契约全覆盖且无 null / 有缺口 / 用法或文件错误 | 缺口逐条打印 |

> `partial` 仍返回 `0`（产物完整、限制已记录）；**只有**读不到输入或产不出关键产物才是非零。
> 题集里的 L3 案例（`urban-heat-001`）就是 `status=partial` 且 exit `0` 的正当例子。

## 2. 五类失败模式（逐条附题集/实测证据）

### 2.1 材料异常

| 情形 | 检测点 | 处置 | 记录位点 | 证据 |
|-|-|-|-|-|
| `case.json` 不存在 / 不可解析 | `main.py` 读取阶段 | **exit 1** + `{"status":"failed","error":…}` | stdout | 本包对同源脚本的失败注入实测（F01/F02） |
| `case.json` 缺 `case_id` | 回退链 `case_id→id→case→文件名` | 用文件名兜底，**不伪造** | `result.case_id` | F03 实测：`case_id` 取文件名、`status=partial` |
| 声明的材料路径不存在 | 材料预检 | 继续用其余材料，**点名缺失路径** | `uncertainty` | F04 实测：`uncertainty` 含"材料路径不存在" |
| 材料是二进制 / PDF | 魔数 `%PDF-` 或 NUL 探测 | 有 `pypdf` 则抽文本层（标 `material(pdf-text)`）；否则跳过并声明"数值不上画布" | `uncertainty` + `provenance.source_files[].role` | F05/F16 实测（有/无 `pypdf` 两条路径） |
| 材料非 UTF-8 | 逐文件 UTF-8 探针 | 以替换字符读取，不中断，**并记录** | `uncertainty` | 材料预检新增项 |
| 一条材料都没读到 | `extract.run()` 末尾 | 面板只放要点文本；note 使 `status` 降 `partial` | `notes` → `warnings` | F04/F16 实测 |
| **指标名有、数值缺失**（题集 L3 构造） | `audit.missing_values` | 图上「数值缺失」占位，**绝不编造** | `audit.missing_values` + `uncertainty` | **L3 实测**：`missing_values=['夜间地表温度差']`，`uncertainty` 含占位说明 |
| **材料同一指标两处数值矛盾**（题集 L3 构造） | 材料事实与 case 声明同 id 时比较数值 | 首见优先；两处数值与各自 `src` **并列**进 `uncertainty`；**不取平均、不择优** | `uncertainty` | **L3 实测**：「case.json 取 0.14，材料另给 0.19（两处 src=case.json[data] / material:35）」 |
| 实体重名 / 歧义 | 同 id 首见优先 | 两项都列出并说明歧义 | `uncertainty` | D6 |
| 散文里的数字（"衰减到 80%"） | 事实行解析器只认独立行 | **不抽取**（宁缺勿错） | 该指标进 `missing_values` | `CASE-SET.md` §4 边界 1 |
| 带比较符/区间的值（`≈13.6 µg/mL`、`0.8–1.2 mg/L`） | 数值解析器要求"数字 + 单位" | 不作为数值上画布 | `audit.missing_values` | `CASE-SET.md` §4 边界 5 |

**反模式（禁止）**：为了图"完整"给缺值项补一个看起来合理的数字；把材料里没有的实体画上画布。
两者会直接打掉「结果正确性 15」与「结果可核验性 5」。

### 2.2 模板缺失 / 预置资源缺失

本包**不含任何二进制模板**（无 `.pptx/.png/.pdf/.svg/.ttf`）——"模板"= 代码 + 文本规格 + 运行时生成。

| 原形态（已删除） | 替代机制 | 缺失时的行为 |
|-|-|-|
| 预置示例图 `*.svg/.png/.pdf` | `svgbuilder.py` + `preview.py` 运行时生成 | 生成失败 ⇒ `status=failed` + exit 2，并说明后端错误 |
| 预置图面规格 | `figurespec.py` 纯函数确定性生成 | 版面异常 ⇒ `audit.bounds` / `layout_log` 记录 |
| 预置方案模板 | `assets/spec_template.json`（纯 JSON 文本） | 缺失不影响出图；`scaffold.py` 仍可从材料抽骨架 |
| 字体文件 `.ttf/.otf` | `preview.py::PIXEL_FONT_CANDIDATES` 运行期探测（`C:/Windows/Fonts`、`/usr/share/fonts`、`/System/Library/Fonts`） | 逐级回退并用默认字体；字体名如实记录 |
| `task.md` 缺失 | 面板要点改由材料小节标题映射 | 要点为空时面板保留结构，不放填充句（`warnings`） |

**判定法**：如果某文件缺失会导致"必须由作者本机补一份二进制"，那它就不该进包。

### 2.3 依赖缺失（逐级降级，禁止静默）

| 情形 | 处置 | 记录位点 | 证据 |
|-|-|-|-|
| `matplotlib` 不可导入 | 回退 Pillow；`status` 降 `partial` | `render_log.backend` + `uncertainty` | 失败注入 F13 实测 |
| `Pillow` 不可导入 | **matplotlib 自身 `import PIL`，会连带失效** ⇒ 落到纯 Python PNG | 两级失败原文进 `render_log`，`uncertainty` 说明降级 | F14 实测（真实耦合，不是缺陷） |
| 两级都不可用 | 纯 Python PNG 仍出图（文字占位并注明） | `render_log.warnings` | F15 实测：`backend=pure-python-png`、`status=partial` |
| `pypdf` 不可导入且材料是 PDF | 不抽文本层，**声明数值不上画布** | `uncertainty` | F16 实测 |
| PDF 后端/开关不可用 | PNG 照常；PDF 条目 `present:false` + `reason` | `deliverables[format=pdf]` | L2/L3 案例声明 `pdf=false`，实测 `reason="disabled by constraints (pdf=false)"` |
| 输出目录不可用（`--out` 是文件） | **exit 2** + `{"error":"output directory not usable: …"}` | stdout | F17 实测 |

### 2.4 契约四形态

| 情形 | 形态 | 处置 | 记录位点 |
|-|-|-|-|
| 字段无真实值 | ①类型提示 | 按类型给空值（字符串 `""`），**禁 null** | 顶层字段 + `uncertainty` |
| 字段声明为 `null` | ①类型提示 | 归一化为空值并记录（**不允许原样回显 null**） | 顶层字段 + `uncertainty` |
| 键与信封保留键冲突（如 `summary`） | 任意 | 顶层保留信封值，案例值移入 `output_contract_echo` | `result.output_contract_echo` |
| 声明数字、实值为字符串 | ①类型提示 | 以**真实值**为准写入，类型偏差可被复核方看到 | 顶层字段 |
| 容器字段无真实值 | ②容器 | 写 `[]`（空列表是合法值，**不得**被 `null`/`""` 替换） | 顶层字段 |
| 布尔开关无真实值 | ③布尔 | 写 `false`（真布尔，不写 0/字符串） | 顶层字段 |
| 字段清单无真实值 | ④字段清单 | 写 `[]`；有值时回显实际图层名 | 顶层字段 + `audit.layer_naming.found` |
| 案例完全没有 `output_contract` | — | 信封 18 键仍须齐全 | 顶层 18 键 |

三个题集案例的 `output_contract` 都覆盖了四形态（类型提示 / 容器 / 布尔 / 字段清单），
并逐案通过 `check_contract.py`（exit 0）。

### 2.5 状态一致性

| 情形 | 处置 | 记录位点 |
|-|-|-|
| 规格 lint 不过 | `status` 判 `partial`，**不做 success** | `result.spec_lint` + `uncertainty` |
| 方案 lint 不过 | 同上（方案门与规格门都要能拦住 success） | `result.plan.lint` |
| 渲染后端降级 | `status` 降 `partial` | `uncertainty` + `render_log` |
| 存在缺值 / 实体缺失 / 越界 / 输入 notes | `status` 降 `partial` | `audit.*` + `warnings` |
| SVG 不良构 / PNG 无效 | `status=failed` + **exit 2**，已写出产物保留 | `audit.checks` + stderr |
| 方案覆盖案例 constraints | 设计决策以 plan 为准，**并写入 `change_records`** | `result.change_records` |
| 重跑结构漂移 | 视为缺陷：检查是否把时间戳/随机数带进图面 | `audit.determinism_probe.spec_sha16` |

## 3. 题集如何暴露"只在一个案例上能跑"的假泛化（实测记录）

把案例从 1 个扩到 3 个（跨题材 + 跨单位形态 + 故意含材料异常）之后，以下问题**立刻出现**，
且都不在单案例下可见；修复后三案复跑通过：

| 现象 | 根因（代码位置） | 修复后判据 |
|-|-|-|
| L2 的 `25.4 mA/cm2`、`3.1e11 cm-2` 被判「数值缺失」，值其实就在材料里 | 数值解析的单位字符类不含数字与 `-` `/` | L2 `missing_values=[]` |
| L2 说明文字渲染成 `310000000000.0`，audit 却按 `:g` 找 `3.1e+11` ⇒ **G6 门报"数值未上画布"** | `figurespec._simple_datum` 用原始 float | L2 `encoding_consistency.missing_from_canvas=[]` |
| 材料行被整批误判成"关系"（L2 `relations` 被灌到 25，声明只有 5 条），**材料数值进不了数据通道** | 箭头正则分隔符写成可选 `⇒?` | L2 `relations=9`；材料数值进入数据通道 |
| L3 材料里 0.14 / 0.19 两处数值，第二个被静默丢弃 | 材料事实与 case 声明同 id 时直接跳过、不比较 | L3 `uncertainty` 出现数值不一致条目（含两处 `src`） |

> 与本包其它文档的分工：本节记录"跨案例暴露的问题"，逐案输入/期望/区间/失效边界见
> [`CASE-SET.md`](CASE-SET.md)；同源脚本的四形态注入矩阵（23 条用例、修复前后对照）
> 见 v4 包的 `references/FAULT-MATRIX.md`。

## 4. 科学诚实性红线（比任何降级都优先）

1. 材料里定位不到的数值**不得上画布**，只能进 `uncertainty` 并以「数值缺失」占位。
2. 两处数值矛盾**不取平均、不择优、不改写**，两处 `src` 并列交人判断。
3. 二进制 / 扫描件材料取不到文本时，**宁可少画也不编造**（数值一律不上画布）。
4. 任何降级都要留记录；**"静默成功"本身就是缺陷**。

## 5. 复现本文件结论的最小命令集

```bash
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2
PKG=$(mktemp -d) && cp -r "$SKILL_DIR" "$PKG" && cd "$PKG"

# 三案冒烟 + 契约门（判据 = 退出码）
for c in examples/case.json examples/cases/calab-perovskite-001/case.json examples/cases/urban-heat-001/case.json; do
  out=/tmp/ga-$(basename "$(dirname "$c")")
  python scripts/main.py --case "$c" --out "$out"; echo "run exit=$?"
  python scripts/check_contract.py --result "$out/result.json" --case "$c" >/dev/null; echo "contract exit=$?"
done

# 看 L3 的两条降级记录（必须两条都在）
python -c "import json;print(*json.load(open('/tmp/ga-cases/result.json',encoding='utf-8'))['uncertainty'],sep='\n')" 2>/dev/null || \
python -c "import json,glob;print(*json.load(open(sorted(glob.glob('/tmp/ga-*/result.json'))[-1],encoding='utf-8'))['uncertainty'],sep='\n')"

# 数值可定位自查（题集自检）
python - <<'PY'
import json, os, glob
for case_path in glob.glob("examples/cases/*/case.json") + ["examples/case.json"]:
    case = json.load(open(case_path, encoding="utf-8"))
    mat = open(os.path.join(os.path.dirname(case_path), "material.md"), encoding="utf-8").read()
    miss = [d["label"] for d in case.get("data", [])
            if d.get("value") and str(d["value"]).split()[0] not in mat]
    print(case["case_id"], "-> values not literal in material:", miss)
PY
```

## 6. 表外情形怎么办（"先记后判"）

遇到规则表没列出的情形时：**先把观察写进 `uncertainty` / `warnings`，再判断是否可以继续。**
禁止"因为规则没写，所以静默忽略"。新增规则时须在四处同步：`SKILL.md` §6、本文件 §2/§3、
`references/CASE-SET.md` §4（若属于泛化边界）、以及对应脚本的注释。
