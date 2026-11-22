# GAIN-PROTOCOL.md — 把"好用在哪"变成可复算的五个问题

> 本文件属于「机制与复用」轴：它不重复声明本包有什么能力，只回答**能力带来的差别是多少**，
> 并且把回答方式交给一把任何人都能拿起来的尺子 —— `scripts/gain_harness.py`（只读、标准库、不出图）。
>
> 三个前置声明：
> ① 这里的对照是**本地代理对照**（条件 B 由最小复现脚本执行），平台官方对照以组织方白板为准；
> ② 指标是**结构与文本级**判据，不评价美观，也不评价领域结论；
> ③ 数字全部来自实跑，**对 A 不利的照原样保留**（§5）——只报好话的对照不会被采信。

---

## 1. 三个条件

| 代号 | 是什么 | 怎么跑 |
|-|-|-|
| **A** | 加载本 Skill 的完整链路 | `python "$SKILL_DIR/scripts/main.py" --case <case.json> --out <out_A>` |
| **B** | 不加载 Skill 的基础做法：拿到 `case.json` 直接出图（标题 + 实体框 + 关系文字 + 数据条形），另写一份最小 `result.json` | `python baseline_one_shot.py --case <case.json> --out <out_B>`（全文见 §7） |
| **B+** | 在 B 上只补一项最强设置：`matplotlib.rcParams["svg.fonttype"]="none"`（保留真 `<text>`） | 同 B，多一行 rcParams 覆盖 |

三条件都遵守同一纪律：**一条命令、一次运行、无人工补画、无事后排版**。

## 2. 什么才算"公平"（逐条自检）

| 检查项 | 本次执行 |
|-|-|
| 用的是同一个 `case.json` / `task.md` / 材料？ | 是（同一合成示例：6 实体 / 5 关系 / 7 数据点） |
| 图面约束相同？ | 是（1200×800 @300dpi、色盲安全、流程箭头、2× 光栅、PDF 开） |
| 入口都是"一条命令"？ | 是（`main.py` / `baseline_one_shot.py`） |
| 同机、同 Python、同库版本、同会话窗口？ | 是（Python 3.13.9 / matplotlib 3.10.6 / Pillow 12.3.0） |
| 判定用的是同一把尺子？ | 是（全部指标由 `gain_harness.py` 计算，双方都不得自述） |
| 是否给了 B 最有利的条件？ | 是（专门做了 B+，把 B 最弱的可编辑性补满） |
| 是否保留了对 A 不利的结果？ | 是（§5 三条） |

## 3. 尺子：指标与字段路径

```bash
python "$SKILL_DIR/scripts/gain_harness.py" --out <dir> [--case <case.json>] [--material <材料>] \
       [--label <名字>] [--json <报告.json>]
python "$SKILL_DIR/scripts/gain_harness.py" --compare <dir1> <dir2>
```

| 测量对象 | 报告字段 | 单位/取值 | 怎么判读 |
|-|-|-|-|
| 分层结构 | `editable.layers` | 计数 | 0 = 源文件没有结构，接手者只能整张重画 |
| 文字可编辑性 | `editable.text_nodes` / `editable.glyph_use_nodes` | 计数 | 真文字多、字形引用少 = 可以直接改字 |
| 来源挂接 | `provenance.src_attrs` / `provenance.science_elems` / `provenance.coverage` | 计数 / 比值 | 覆盖率越接近 1 越好；0 = 每个元素都无法回查 |
| 叙事完整性 | `four_elements.on_canvas` | 0–4 | 4 = 一页讲完问题→方法→结果→结论 |
| 数值可核验 | `numbers.on_canvas` / `numbers.found_in_material` / `numbers.unlocated` | 计数 | 分子/分母 + 残差清单；残差要能解释（刻度、id 片段等） |
| 契约完整 | `contract.{expected,covered,missing_or_null,verdict,result_toplevel_keys}` | 计数 / 枚举 | `verdict=complete` 才算交付态可用 |
| 交付证据 | `evidence.{result_json,audit_json,render_log,spec_json}` | 布尔 | 缺 audit/render_log = 复核者只能目视位图 |
| 结构确定性 | `--compare` 的 `structure_identical` / `diff_keys` | 布尔 / 列表 | 两次运行逐项一致 = 同输入同布局 |
| 效率 | 墙钟（`time`）+ 返工步数（人工计数） | 秒 / 次 | 见 §5 的口径说明 |

## 4. 记录：五个问题 × 三条件

同机同输入实测（原始 JSON 片段见 §4.2）：

| 问题 | 指标 | A | B | B+ |
|-|-|-|-|-|
| **能不能改？**（接手者能否继续编辑） | 分层数 / 真文字 / 字形引用 | **7 / 61 / 0** | 0 / 0 / 435 | 0 / 38 / 12 |
| **能不能查？**（元素与数值能否回到材料） | 溯源覆盖率 / 数值可定位 | **0.903（56/62）/ 14⁄16** | 0（0/0）/ 0⁄0 | 0（0/0）/ 7⁄15 |
| **讲全了吗？**（四要素是否齐） | 四要素覆盖 | **4/4** | 0/4 | 1/4 |
| **能自动复核吗？**（契约与证据文件） | 契约 / 顶层键 / 证据文件 | **8⁄8 complete / 26 键 / audit+render_log+spec 齐** | 0⁄8 absent / 4 键 / 三缺 | 0⁄8 absent / 4 键 / 三缺 |
| **值不值得？**（效率） | 单次墙钟 / 返工步数 | 2.33–2.44 s / **0 步** | **1.33–1.71 s** / 未达标 | — / 未达标 |

### 4.1 确定性（同一把尺子的第二种用法）

```json
{"dir_a": "outA", "dir_b": "outA2", "structure_identical": true, "diff_keys": []}
{"dir_a": "outBase", "dir_b": "outBase2", "structure_identical": true, "diff_keys": []}
```

⇒ **B 也做到了两次一致**。所以本包不宣称"唯有本包可复现"，只宣称"本包把复现性写成了可检查的字段"。

### 4.2 原始片段（未改写）

```json
// A
"editable": {"layers": 7, "text_nodes": 61, "glyph_use_nodes": 0},
"provenance": {"src_attrs": 56, "science_elems": 62, "coverage": 0.903},
"numbers": {"on_canvas": 16, "found_in_material": 14, "unlocated": ["001", "6.5"]},
"contract": {"expected": 8, "covered": 8, "missing_or_null": [], "verdict": "complete",
             "result_toplevel_keys": 26},
"evidence": {"result_json": true, "audit_json": true, "render_log": true, "spec_json": true}

// B
"editable": {"layers": 0, "text_nodes": 0, "glyph_use_nodes": 435},
"provenance": {"src_attrs": 0, "science_elems": 0, "coverage": 0.0},
"contract": {"expected": 8, "covered": 0, "verdict": "absent", "result_toplevel_keys": 4},
"evidence": {"result_json": true, "audit_json": false, "render_log": false, "spec_json": false}

// B+
"editable": {"layers": 0, "text_nodes": 38, "glyph_use_nodes": 12},
"four_elements": {"on_canvas": 1, "panels": ["results"], "expected": 4},
"numbers": {"on_canvas": 15, "found_in_material": 7,
            "unlocated": ["20", "40", "60", "80", "18.0", "85.0", "72.0", "95.0"]}
```

## 5. 三条对 A 不利的观测（必须一起读）

1. **A 单次更慢**：A ≈ 2.33–2.44 s，B ≈ 1.33–1.71 s（两次独立会话各测，同机同输入）。
   多出的时间花在抽取、方案 lint、图层化、audit 与契约回填上。
   ⇒ 口径只能是"**A 的收益在免返工与可核验性，不在单次速度**"。
2. **确定性不是独占优势**：B 两次运行同样结构一致（§4.1）。
3. **A 的溯源覆盖率是 0.903，不是 1.000**：残差 6 个为 `relation` 组容器（子元素带 `src`，容器本身不带）。
   包内 `audit.layer_naming.elements_without_src` 按文档化角色白名单统计为 0；本文件按更严格口径记录 0.903。

**附带发现（B 侧的真实风险）**：B 的运行出现 **177 条** `Glyph … missing from font(s) DejaVu Sans`
告警，涉及 **59 个**不同字形（中文标签在 PNG 里缺失）；A 侧 `render_log.json` 记录
`font="Microsoft YaHei,SimHei,Arial,Segoe UI"`、`warnings=[]` —— 字体探测链把中文救了回来，
并且把"用了什么字体"写进了证据文件。

## 6. 这套记录的边界

- 条件 B 是**最小复现脚本**，不是真实的无 Skill LLM Agent：它衡量机制层面的差距，
  不能替代平台官方的 Agent 对照；
- 单案例、单机、单版本；**不做统计显著性声明**；
- 指标只覆盖结构与文本层面（不等于图"讲得对"）；
- 当 `case.json` 与材料正文数值冲突时，本包的机制**不会拦**（见 `references/MECHANISM.md` §2④ 的 E3 反例）——
  这也是本协议如实保留的一条失效边界。

## 7. 条件 B 的最小复现（对照用；不随包运行、不被 `main.py` 调用）

```python
import argparse, json, os, re
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
ap = argparse.ArgumentParser(); ap.add_argument("--case", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args(); case = json.load(open(a.case, encoding="utf-8")); os.makedirs(a.out, exist_ok=True)
num = lambda s: float((re.search(r"-?\d+(?:\.\d+)?", str(s)) or re.match("0", "0")).group(0))
ents = case.get("entities", [])[:6]; rels = case.get("relations", [])[:5]; data = case.get("data", [])[:7]
fig, (top, bot) = plt.subplots(2, 1, figsize=(12, 8), dpi=300); top.axis("off")
fig.suptitle(case.get("title", "Graphical Abstract"), fontsize=16)
for i, e in enumerate(ents):
    top.text(0.08 + i * (0.84 / max(len(ents), 1)), 0.6, e.get("name", ""), fontsize=11,
             bbox=dict(boxstyle="round", fc="#eef3f8", ec="#4a6fa5"))
for j, r in enumerate(rels):
    top.text(0.06, 0.2 - j * 0.05, "%s -> %s (%s)" % (r.get("from"), r.get("to"), r.get("label")), fontsize=9)
bot.barh([str(d.get("label", "")) for d in data][::-1], [num(d.get("value", 0)) for d in data][::-1], color="#0072B2")
fig.tight_layout(); fig.savefig(os.path.join(a.out, "figure.png")); fig.savefig(os.path.join(a.out, "figure.svg"), format="svg")
json.dump({"case_id": case.get("case_id"), "status": "success",
           "deliverables": [{"kind": "preview", "format": "png"}, {"kind": "editable_source", "format": "svg"}]},
          open(os.path.join(a.out, "result.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
# B+：在 import 后加一行 matplotlib.rcParams["svg.fonttype"] = "none"
```

## 8. 给复核者的一页摘要

1. 尺子：`scripts/gain_harness.py`（只读、标准库、`--compare` 比结构指纹）；
2. 条件：A / B / B+，同输入、同约束、一条命令；
3. A 的强项：可编辑性（7 层 / 61 真文字）、来源挂接（0.903）、四要素（4/4）、契约（8/8，26 键）、证据文件齐备；
4. A 的弱项：单次墙钟更慢；确定性非独占；覆盖率非 1.000；
5. 结论口径：**A 的收益是可核验性与免返工，不是单次速度**；
6. 移植：把 `gain_harness.py` 指向你自己的产物目录，即可用同一把尺子量你自己的做法（`REUSE-KIT.md` §4 第 3 步）。
