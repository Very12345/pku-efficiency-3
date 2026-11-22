# GAIN-PROTOCOL.md — 「加载本 Skill」与「不加载 Skill 的基础做法」公平对照协议

> 本文件回答一个必须能被第三方复核的问题：**用了这个 Skill，到底改善了哪几项、改善多少？**
> 协议由三部分组成：① 可比条件（防止条件不对等导致对照失真）；② 指标口径 G1–G8
> （全部由只读测量器 `scripts/gain_harness.py` 复算）；③ 本地已真实执行的对照记录
> （含**对 A 不利**的观测，未做任何美化）。
>
> 三条诚实声明（先写在最前面）：
> 1. 本文件的对照是**本地代理对照**：条件 B 由最小复现脚本执行，衡量的是**机制层面**的差距；
>    平台官方的"基础 Agent vs Skill Agent"白板对照由组织方用同一案例生成，以那个为正式依据。
> 2. 指标是**结构与文本级**判据（层数 / 属性数 / 字符串可定位性 / 契约字段覆盖），
>    不评价图的美观，也不评价领域结论是否正确。
> 3. 全部数字来自本机一次可复现的执行，**没有估计值、没有填充值**；对 A 不利的数字原样保留。

---

## 1. 两组条件的定义

| 条件 | 定义 | 执行方式 |
|-|-|-|
| **A：加载本 Skill** | 使用本包的完整链路（抽取 → 方案先行 → 版面/编码 → 分层 SVG → 渲染 → audit → 契约） | `python "$SKILL_DIR/scripts/main.py" --case <case.json> --out <out_A>` |
| **B：不加载 Skill 的基础做法** | 拿到 `case.json` 直接画一张图：标题 + 实体文字框 + 关系文字箭头 + 数据条形，一次运行出 PNG/SVG，再写一份最小 `result.json` | 单次脚本（最小复现见 §6），`python baseline_one_shot.py --case <case.json> --out <out_B>` |
| **B+：给 B 最有利的可编辑性设置** | 同 B，但显式设置 `matplotlib.rcParams["svg.fonttype"]="none"`（保留真 `<text>`），即**把 B 的最弱项补到最强**再比 | 同 B，仅多一行 rcParams 覆盖 |

> B/B+ 都**不做**人工补画、事后编辑或二次排版 —— 与 A 一样是"一条命令一次运行"的产物。

## 2. 可比条件（逐条可核对）

| 维度 | 要求 | 本次执行 |
|-|-|-|
| 输入 | 同一个 `case.json` / `task.md` / `source_material` | 同一份合成示例案例（6 实体 / 5 关系 / 7 数据点） |
| 图面约束 | 同一 `figure_constraints`（1200×800、300 dpi、色盲安全、流程箭头、2× 光栅、PDF） | 两侧一致 |
| 入口 | 一条命令、无交互、无人为干预 | A：`main.py`；B：`baseline_one_shot.py` |
| 运行环境 | 同机、同 Python、同库版本 | Python 3.13.9 / matplotlib 3.10.6 / Pillow 12.3.0 / 同一次会话窗口 |
| 预算口径 | 记单次运行墙钟（E1）+ 达到"契约完整且溯源可核验"所需返工步数（E2） | A：1 次运行即达标；B：未达标（见 §4） |
| 判定 | 全部指标由 `gain_harness.py` 计算，不由任何一方自述 | 复算命令见 §3 |

## 3. 指标口径 G1–G8（每条都给出算法与复算命令）

测量器：`scripts/gain_harness.py`（只读；只依赖标准库；**不生成任何图**）。

```bash
# 单条件
python "$SKILL_DIR/scripts/gain_harness.py" --out <out_dir> \
       --case <case.json> --material <material.md> --label <A|B|B+> [--json report.json]
# 确定性（G6）
python "$SKILL_DIR/scripts/gain_harness.py" --compare <out_run1> <out_run2>
```

| 编号 | 计算方式（源码位置） | 判读 |
|-|-|-|
| G1a 分层数 | SVG 中匹配 `<g ... id="layer:*">` 的次数 | 0 = 源文件无结构，接手者只能整张重画 |
| G1b 真文字节点 | 匹配 `<text ...>` 的次数 | 0 且 G1c 很大 = 文字已被轮廓化，改字必须回原工具 |
| G1c 字形引用 | 匹配 `<use ...>` 的次数 | >0 提示字体以轮廓/引用方式嵌入 |
| G2 溯源覆盖率 | `data-src="` 出现次数 ÷ `data-role="(entity\|relation\|datum\|icon)…"` 元素数 | 1.0 = 每个科学元素都能回到材料 |
| G3 四要素覆盖 | 图面文本中可检测到的面板语义数（研究问题/方法/结果/结论）÷ 4 | 4/4 = 一页讲完整条故事线 |
| G4 数值可定位率 | SVG 文本中抽取的数值 token 中，能在材料原文里字符串级命中的比例 | 分母是图面数值标签数，分子是可回到材料者 |
| G5 契约完整率 | `result.json` 顶层非空覆盖的案例 `output_contract` 字段数 ÷ 契约字段数；`verdict ∈ {complete, partial, absent}` | 附 `result.json` 顶层键总数 |
| G6 结构确定性 | `--compare` 比较结构指纹（层数、文字数、角色元素数、排序后文本集合、顶层键集合、`spec_sha16`） | 逐项一致 = 同输入同布局 |
| G7 证据完备性 | `audit.json` / `render_log.json` / `spec.json` 是否存在 | 缺 = 复核者只能目视位图 |
| G8 效率 | E1 单次运行墙钟（`time` 实测）；E2 达标所需返工步数（人工计数） | 见 §4 的诚实差异 |

## 4. 实测记录（本机真实执行，原样记录）

执行时间：本地一次连续会话（约 3 分钟，含 4 次出图 + 2 次对照出图）。
命令（逐字）：

```bash
SKILL_DIR=<包副本目录>
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <tmp>/A1   # A 第 1 次
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <tmp>/A2   # A 第 2 次（确定性）
python baseline_one_shot.py --case "$SKILL_DIR/examples/case.json" --out <tmp>/B1           # B 第 1 次
python baseline_one_shot.py --case "$SKILL_DIR/examples/case.json" --out <tmp>/B2           # B 第 2 次
python bplus.py            --case "$SKILL_DIR/examples/case.json" --out <tmp>/B1plus        # B+（fonttype=none）
python "$SKILL_DIR/scripts/gain_harness.py" --out <tmp>/A1 --case "$SKILL_DIR/examples/case.json" \
       --material "$SKILL_DIR/examples/material.md" --label A-skill
python "$SKILL_DIR/scripts/gain_harness.py" --out <tmp>/B1 --case "$SKILL_DIR/examples/case.json" \
       --material "$SKILL_DIR/examples/material.md" --label B-baseline
python "$SKILL_DIR/scripts/gain_harness.py" --compare <tmp>/A1 <tmp>/A2
python "$SKILL_DIR/scripts/gain_harness.py" --compare <tmp>/B1 <tmp>/B2
```

### 4.1 主表（测量器原始输出）

| 指标 | A（加载 Skill） | B（基础做法，matplotlib 默认） | B+（B 的最有利设置） |
|-|-|-|-|
| G1a 分层数 | **7**（`layer:annotations/background/data/entities/legend/panels/relations`） | 0 | 0 |
| G1b 真文字节点 | **61** | 0 | **38** |
| G1c 字形引用 | 0 | 435 | 12 |
| G2 溯源覆盖率 | **0.903（56/62）** | 0（0/0） | 0（0/0） |
| G3 四要素覆盖 | **4/4**（question/method/results/conclusion） | 0/4 | 1/4（仅 results） |
| G4 数值可定位率 | **14/16** | 0/0 | 7/15 |
| G5 契约 | **8/8，verdict=complete，顶层 26 键** | 0/8，verdict=absent，顶层 4 键 | 0/8，verdict=absent，顶层 4 键 |
| G6 结构确定性 | 两次**逐项一致** | 两次**逐项一致** | 未测（不参与结论） |
| G7 证据文件 | audit + render_log + spec **齐备** | 三者全缺 | 三者全缺 |
| G8 E1 单次墙钟 | 2.441 s / 2.156 s | **1.707 s / 1.514 s** | — |
| G8 E2 达标返工步数 | **0**（首次运行即 26 键 + `check_contract.py` exit 0） | 未达标：契约 0/8、无 audit/render_log/spec、无 `data-src`、无分层 | 未达标（同 B，仅可编辑性改善） |

### 4.2 关键原始片段（测量器输出摘录，未改写）

A（`--label A-skill`）：

```json
"editable": {"layers": 7, "text_nodes": 61, "glyph_use_nodes": 0},
"provenance": {"src_attrs": 56, "science_elems": 62, "coverage": 0.903},
"four_elements": {"on_canvas": 4, "expected": 4},
"numbers": {"on_canvas": 16, "found_in_material": 14, "unlocated": ["001", "6.5"]},
"contract": {"expected": 8, "covered": 8, "missing_or_null": [], "verdict": "complete",
             "result_toplevel_keys": 26},
"evidence": {"result_json": true, "audit_json": true, "render_log": true, "spec_json": true}
```

B（`--label B-baseline`）：

```json
"editable": {"layers": 0, "text_nodes": 0, "glyph_use_nodes": 435},
"provenance": {"src_attrs": 0, "science_elems": 0, "coverage": 0.0},
"four_elements": {"on_canvas": 0, "expected": 4},
"numbers": {"on_canvas": 0, "found_in_material": 0, "unlocated": []},
"contract": {"expected": 8, "covered": 0, "verdict": "absent", "result_toplevel_keys": 4},
"evidence": {"result_json": true, "audit_json": false, "render_log": false, "spec_json": false}
```

B+（`svg.fonttype="none"`，把 B 的可编辑性补到最强）：

```json
"editable": {"layers": 0, "text_nodes": 38, "glyph_use_nodes": 12},
"four_elements": {"on_canvas": 1, "panels": ["results"], "expected": 4},
"numbers": {"on_canvas": 15, "found_in_material": 7,
            "unlocated": ["20", "40", "60", "80", "18.0", "85.0", "72.0", "95.0"]},
"contract": {"expected": 8, "covered": 0, "verdict": "absent"}
```

确定性比较（G6）：

```json
{"dir_a": "A1", "dir_b": "A2", "structure_identical": true, "diff_keys": []}
{"dir_a": "B1", "dir_b": "B2", "structure_identical": true, "diff_keys": []}
```

### 4.3 三条对 A 不利、但必须记录的观测

1. **单次速度 A 更慢**：A = 2.441 s / 2.156 s，B = 1.707 s / 1.514 s（同机同输入，`time` 实测）。
   A 多出的时间用在抽取、方案 lint、图层化、audit 与契约回填上。
   **结论的口径因此必须是**："A 的增益体现在 E2 免返工与结构/溯源/契约的可核验性，
   而不是单次运行更快。"
2. **确定性不是 A 的独占优势**：G6 上 B 也两次一致（matplotlib 输出本身确定）。
   本包不再宣称"只有 A 才能复现"，只宣称"A 把复现性做成了可检查的字段
   （`audit.determinism_probe`）"。
3. **A 的 G2 不是 1.000 而是 0.903**：残差 6 个是 `<g data-role="relation:…">` **关系组容器**
   （其子元素带 `data-src`，容器本身不带）。包内 `audit.layer_naming.elements_without_src`
   按文档化的角色白名单统计为 0，两处口径不同 —— 这里按**更严格的口径**记录 0.903，
   不取好看的那个数。

### 4.4 附带发现（B 侧的真实工程风险）

B 的中文标签在 PNG 里**渲染缺失**：运行 stdout 出现 **177 条**
`Glyph … missing from font(s) DejaVu Sans` 告警，涉及 **59 个**不同字形
（中文实体名与面板文字）。A 侧的 `render_log.json` 记录为
`backend=matplotlib`、`font="Microsoft YaHei,SimHei,Arial,Segoe UI"`、`warnings=[]`
—— 即 A 的字体探测链把中文渲染救回来了，并且**把用了什么字体写进了证据文件**。
这不是排版偏好问题：B 的交付物在中文场景下会直接丢字。

## 5. 结论怎么表述才不失真

可以说的：
- 在同一输入、同一约束、同一条命令入口下，A 的产物**结构可核验性**（分层/真文字/`data-src`/
  audit/契约）与 B 不在同一量级；
- A 首次运行即满足契约（26 顶层键、`check_contract.py` exit 0），B 需要另行补写这些层才能达标；
- A 把"用了什么后端、什么字体、哪些降级"写进了证据文件，B 没有。

不可以说的：
- ❌ "A 比基础 Agent 快" —— 单次墙钟 A 更慢（§4.3-1）；
- ❌ "只有 A 能做到确定复现" —— B 也做到了（§4.3-2）；
- ❌ 把本表的数字当作平台官方对照结果 —— 官方对照由平台用真实基础 Agent 生成；
- ❌ 用单案例、单机的观测推断统计显著性 —— 这里只有一次可复现的执行记录。

## 6. 条件 B 的最小复现（对照用，**不随包运行、不被 `main.py` 调用**）

```python
# baseline_one_shot.py —— 条件 B：拿到 case.json 直接画一张图（对照用最小实现）
import argparse, json, os, re
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser(); ap.add_argument("--case", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args(); case = json.load(open(a.case, encoding="utf-8")); os.makedirs(a.out, exist_ok=True)
ents, rels, data = case.get("entities", [])[:6], case.get("relations", [])[:5], case.get("data", [])[:7]
num = lambda s: float((re.search(r"-?\d+(?:\.\d+)?", str(s)) or re.match("0", "0")).group(0))
fig, (top, bot) = plt.subplots(2, 1, figsize=(12, 8), dpi=300)
fig.suptitle(case.get("title", "Graphical Abstract"), fontsize=16); top.axis("off")
for i, e in enumerate(ents):
    top.text(0.08 + i * (0.84 / max(len(ents), 1)), 0.6, e.get("name", ""), fontsize=11,
             bbox=dict(boxstyle="round", fc="#eef3f8", ec="#4a6fa5"))
for j, r in enumerate(rels):
    top.text(0.06, 0.2 - j * 0.05, "%s -> %s (%s)" % (r.get("from"), r.get("to"), r.get("label")), fontsize=9)
labels = [str(d.get("label", "")) for d in data]; vals = [num(d.get("value", 0)) for d in data]
bot.barh(labels[::-1], vals[::-1], color="#0072B2"); bot.set_title("core data", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(a.out, "figure.png"))
fig.savefig(os.path.join(a.out, "figure.svg"), format="svg")      # B+ 额外加一行：
# matplotlib.rcParams["svg.fonttype"] = "none"                    # 保留真 <text>（B+ 条件）
json.dump({"case_id": case.get("case_id"), "status": "success",
           "deliverables": [{"kind": "preview", "format": "png"}, {"kind": "editable_source", "format": "svg"}]},
          open(os.path.join(a.out, "result.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
```

该脚本刻意保持"合理但朴素"：不做溯源、不做图层、不做 lint、不做契约回填 —— 这样 A/B 的
差距才能归因到**机制**，而不是"谁写得更认真"。

## 7. 把本协议用到你自己的项目（三步）

1. 用同一 `case.json` 跑两次你的做法（一次其原始形态、一次把最强项补满），输出到两个目录；
2. `python scripts/gain_harness.py --out <dir> --case <case.json> --material <材料> --label <名字>`；
3. 用 `--compare` 检查你自己的确定性，然后**连同不利项一起**写进你的说明文档 ——
   只报有利项的自述，评审通常不会采信。

## 8. 可追溯性清单

| 项 | 值 |
|-|-|
| 测量器 | `scripts/gain_harness.py`（标准库；只读；不参与流水线） |
| 出图入口 | `scripts/main.py`（参数：`--case/--task/--material/--plan/--raster-scale/--pdf/--no-pdf/--out`） |
| 环境 | Python 3.13.9 · matplotlib 3.10.6 · Pillow 12.3.0 |
| 原始报告 | 由 §3 命令重新生成（含 `--json` 可落盘） |
| 复现记录 | `TEST.md` 的对照链小节（含退出码与命令） |
