# CASE-SET.md — 多案例题集与泛化边界

> **这份文件的用途**：把"这个 Skill 换个题材还成立吗"从形容词变成**可复跑的对照**。
> `scripts/run_case_set.py` 对题集里每个案例**真跑一遍**，逐条对验收区间，
> 把结果渲染成 `references/CASE-SET.md` §2 这张表。表里的每个数字都来自本机实跑
> （Python 3.13.9 / Windows / 无 Office 引擎），**不接受手抄**。

## 1. 题集（3 个案例：1 个最小示例 + 2 个不同题材的合成案例）

| # | 案例（`examples/` 下） | 题材 | 输入 | 期望产出结构 | 可接受区间（`expected.json`） | 难度层 |
|-|-|-|-|-|-|-|
| 1 | `case.json` + `deck-spec.json` + `materials/paper-mini.txt` | 计算机科学（检索增强的代码评审） | 合成论文文本 + 8 页上限 | 问题→方法→证据→结论→局限（8 页） | `status ∈ {completed, partial}`；证据行 ≥ 6；页数 8 | 容易（示例基线，管道验证用） |
| 2 | `cases/case-muon-battery/`（`case.json` / `material.md` / `deck-spec.json` / `expected.json`） | **实验物理 / 无损检测**（μ 子透射成像分辨电池析锂） | 虚构论文全文（含 Table 1 四档数值、Figure 1/2 图注、§5 局限 4 条） | 问题→装置→设计与统计→主结果（趋势）→反演厚度与验证→判读口径→在线化约束→局限→结论 | `status ∈ {completed, partial}`；证据行 ≥ 6；页数 8–11；`92.4/90.8/88.6/87.1/8.6/15.9/3.2/74%` 必须逐字出现；禁止出现"析锂是唯一原因""50% SoC 以下没有析锂""可在线检测" | 中等 |
| 3 | `cases/case-sleep-cohort/` | **临床流行病学**（睡眠时长与代谢综合征的横断面关联） | 虚构论文全文（含 Table 1 患病率与 OR、Figure 1/2 图注、§5 局限 4 条） | 问题→人群与纳排→暴露/结局/协变量→主结果→非线性形状→稳健性→判读→局限→结论 | 同上页数与证据行；`41.2/30.1/27.8/36.7/1.58/1.09/1.31/0.03` 必须逐字出现；禁止出现"睡眠不足导致代谢综合征""延长睡眠可降低风险""性别差异显著" | 中等偏难（**语言纪律**是主要难点） |

两个新案例都是**合成材料**：作者、机构、期刊、数值全部虚构，材料首行明确标注；
它们**不是**正式评测案例，也不提供任何"标准答案产物"——skill 必须在运行时按材料重新生成。

**为什么选这两个题材**（而不是再加两个计算机案例）：它们各自压住一类风险——
物理案例压"数值与量纲必须逐字、结论不能从'低于分辨下限'升级成'没有析锂'"；
流行病学案例压"**动词**必须与设计匹配（横断面不能说因果）"。
这两类是"把论文转成 PPT"最常见的翻车点，也最难靠模板化流程蒙对。

## 2. 逐案实测结果

<!-- CASE-SET-BEGIN -->
<!-- 本表由 scripts/run_case_set.py --emit-md 从真实运行数据渲染；不要手改数字，重跑即可。 -->

| 案例 | 题材难度层 | 实测 exit | status | 页数 | 预览 | 证据行 | 缺口 | uncertainty | self_check | 两道门 | 逐条验收 |
|-|-|-|-|-|-|-|-|-|-|-|-|
| `example-ppt-c7b80f0d` | — | 0 | `completed` | 8 | 7 | 6 | 0 | 1 | OK | export 0 / contract 0 | 全部通过 |
| `case-muon-battery` | 中等 | 0 | `completed` | 11 | 10 | 9 | 0 | 0 | OK | export 0 / contract 0 | 全部通过 |
| `case-sleep-cohort` | 中等偏难 | 0 | `completed` | 11 | 10 | 9 | 0 | 0 | OK | export 0 / contract 0 | 全部通过 |

**统计（本次实测）**：案例 3 个 · 在验收区间内 3 个 · 未通过 0 个。

> 生成命令：`python "$SKILL_DIR/scripts/run_case_set.py" --out <报告目录> --include-example --emit-md <本表>`；协议 `case-set/1.0`；Python 3.13.9；Windows-11-10.0.22621-SP0。
<!-- CASE-SET-END -->

**每个案例逐条通过的检查**（`case-set-report.json` 原文）：

| 检查 | 示例 | μ 子案例 | 睡眠案例 |
|-|-|-|-|
| `status in band` | ✅ | ✅ `completed`（区间含 partial，未降级） | ✅ `completed` |
| `evidence entries >= min` | ✅ 6 ≥ 6 | ✅ **9** ≥ 6 | ✅ **9** ≥ 6 |
| `slide count in band` | ✅ 8 | ✅ 11（9 内容页 + 封面 + 收尾） | ✅ 11（同） |
| `uncertainty within budget when completed` | ⚠️ 1（见下） | ✅ 0 | ✅ 0 |
| `verbatim numbers preserved` | ✅ | ✅（8/8 个关键数字） | ✅（8/8） |
| `forbidden claims absent` | ✅ | ✅ | ✅ |
| `export_check` / `check_contract` | 0 / 0 | 0 / 0 | 0 / 0 |
| `self_check.ok` | ✅ | ✅ | ✅ |

> 示例案例的 `uncertainty=1` 是**预期的**：它的 `case.json` 声明了一个组织方模板
> （`template-example.pptx`），而技能包按合规要求不携带二进制模板 ⇒ 如实记录
> "declared template was not usable → builtin"。这正是"模板缺席是正常分支"的现场样本。

## 3. 题集**抓到的**两个真实问题（泛化测试的价值所在）

这两条不是"设计时想到的"，而是**跑出来的**：

| # | 现象（实测） | 根因 | 处置 |
|-|-|-|-|
| G1 | μ 子案例第一轮：`90.8` 与 `88.6` 两个透射率**没有出现在产物文字里**，逐字一致性检查报红 | 该页 `layout_hint="figure"`，内置版式取到 `Picture with Caption`，其中 idx 1 **就是图片框**；页级 bullets 被写进图片框后又被插图**覆盖销毁**——幻灯片 XML 里那段文字彻底不存在（静默内容丢失） | 修 `deckgen._fill_body_placeholder`（跳过图片框 + 图文同页时正文走左半幅）；修完复跑，8/8 数字全部逐字命中 |
| G2 | 两个新案例第一轮：`slide_count=9` 却产出 11 页，`page_budget_met=false` + uncertainty 报警 | 页数预算原口径只数**内容页**，而最终 deck 另加封面与收尾两页 | 把案例的 `slide_count` 改成 **11**（"8–11 含封面与收尾"）。**口径本身不下结论**：既有做法（预算=内容页）在别处也成立，这里只是让验收区间与真实产物结构一致 |

**这两条合起来说明一件事**：失败注入（`FAULT-MATRIX.md`）覆盖的是"**故障形态**"，
题集覆盖的是"**题材与产物结构**"——两者互为盲区的补集。G1 是注入没覆盖到的静默丢失，
G2 是注入没覆盖到的口径错位。

## 4. 泛化到哪里会**失效**（如实写明）

以下是**已知**的失效/降级边界，分三类写清楚，不含"以后可能改进"这类空话：

### 4.1 已被本机实测确认的失效点

| 边界 | 事实 | 影响 |
|-|-|-|
| **图文同页的版式** | 修 G1 后，图文同页时正文走**左半幅**文本框（内置版式）；组织方模板下仍按占位符填充，模板自己若把正文框放在图下，由模板决定 | 若某模板的正文占位符与图片占位符重叠，肉眼仍可能看到遮挡（文字不会丢，但版面会挤） |
| **页数预算口径** | 预算是"内容页数"，产物含封面/收尾 ⇒ 案例若按产物页数填 `slide_count`，实际会富余 2 页 | 案例作者必须知道这个差 2 的口径，否则会看到 `page_budget_met=false` |
| **形态④ 契约的回显语义** | 形态④（字段清单）只知道**名字**，不知道类型 ⇒ `title` 等语义字段靠 spec 推断，缺 spec 时给 `""` | 用形态④声明的案例，`slides` 等容器只能得到空值（除非 result 里已有真值） |
| **三格检测缺口** | 伪造 `status`、抹掉 `uncertainty`、`case_id` 与案例不一致（见 `failure-modes.md` §4） | 静态校验器拦不住，必须人工兜底（`failure-modes.md` §5） |

### 4.2 结构上未验证、**不得声称支持**的场景

- **扫描件/图像型 PDF**：没有文本层时本包只标注"图像型 PDF"并引用可抽取的图，
  不做 OCR；此类材料**没有**进入题集实测，其"页级主张"质量无从保证；
- **>20 页的大汇报**：题集三个案例都在 8–11 页；页数更多时，页数预算、证据密度、
  版式拥挤都没有实测数据；
- **非中英文材料**：CJK 加权（一个字算两个宽度）与字体探测都在中英混排下验证；
  纯阿拉伯文/天城文等**未测**；
- **真正的组织方模板**：题集三个案例全部走内置版式；`template_mode="replace"`、
  SmartArt、复杂母版等只在代码路径上覆盖，题集没有实测样本；
- **多篇材料合并**：本包按"单篇论文/研究报告"设计，多个材料的取舍未定义。

### 4.3 依赖与环境的限制

- 需要一个**可写的输出目录**与 `python-pptx`（+ `Pillow`）；无 Office 引擎时预览
  只能是 PIL 近似（`previews[].kind=pil-approximation`），**不等于** PowerPoint 渲染；
- 题集实测均在**本机 Python 3.13.9 / Windows** 上完成；容器里的路径与字体不同，
  字体探测会回退（`run_meta.preview_font` 会变，这是设计内的降级）。

## 5. 怎么复跑 / 怎么加案例

```bash
# 复跑整个题集（务必在包外副本上跑）
cp -r "$SKILL_DIR" /tmp/skill-set
python /tmp/skill-set/scripts/run_case_set.py \
    --out /tmp/case-out --include-example --emit-md /tmp/case-out/case-set.md
# 退出码：0 = 全部在验收区间内；1 = 有案例越界（报告点名）；2 = 全部没跑出产物；3 = 参数错
# 单跑一个：  --only case-muon-battery
```

**加一个新案例**只要四步（不需要改任何脚本）：

1. 建目录 `examples/cases/<case-id>/`；
2. 放 `case.json`（`material` 指向同目录材料）与 `material.md`（或 `.txt`/`.pdf` 材料）；
3. 放 `expected.json`：`difficulty_tier` + `expected_structure` + `acceptance_band`
   （页数区间 / 证据行下限 / `must_keep_verbatim` / `must_not_claim`）+ `failure_boundary`；
4. 放一份 `deck-spec.json`（**Agent 写的页级方案**，真实运行时由 Agent 现写；
   放到目录里是为了让题集可离线复跑）。

`run_case_set.py` 会自动发现新案例并把它纳入统计；`acceptance_band` 里
`must_keep_verbatim` 用的是**产物文字**（deck 全部文本框 + 备注 + 证据表），
因此"数字没落到页面上"会被判红——这正是 G1 被抓住的方式。
