# CASE-SET.md — 多案例泛化题集、可接受区间与失效边界

> **本文件里的每个数字都是 `scripts/case_check.py` 现场跑出来的**，不是设计意图。
> 复现（`$SKILL_DIR` = 技能根目录，`<包外目录>` 必须是包外的可写目录）：
>
> ```bash
> python "$SKILL_DIR/scripts/case_check.py" --list
> python "$SKILL_DIR/scripts/case_check.py" --pkg "$SKILL_DIR" --work <包外目录> --probes
> ```
>
> 本机实测环境：Windows + Python 3.13 + python-pptx 1.0.2 + matplotlib 3.10.6 +
> Pillow 12.3.0 + reportlab 5.0.0。

## 0. 题集总览：两个案例、两种题材、两个难度层

| | 案例 A | 案例 B |
|-|-|-|
| 目录 | `examples/cases/case-a-perovskite/` | `examples/cases/case-b-climate-text/` |
| 题材 | **实验科学 / 材料器件**（钙钛矿电池界面钝化） | **理论 / 文本与文献计量**（气候政策议题迁移） |
| 难度层 | **基础层**：有数值数据表（CSV）、章节结构清晰 | **困难层**：**没有任何数值表**、位图无取数、页数只有 6 页、材料带大量方括号引用 |
| 输入文件 | `case.json` + `material.md` + `jv.csv` + `task.md`（4 个） | `case.json` + `material.md` + `task.md`（3 个） |
| 受众 / 时长 / 页数 | 答辩 / 12 分钟 / 8 页 | 同行研讨会 / 8 分钟 / 6 页 |
| 关键检验点 | 数值表要**原样重绘**、结果页有图表、结论数字不得走样 | **不许凭空画曲线**（无表 → 不能出现 `chart_image`）、引用编号要能指回材料 |
| 期望产出结构 | 8 页、`cover…takeaway`、含 `chart_image` 或 `table`、备注与脚注 100% | 6 页、`cover…takeaway`、图表形态只允许 `none`/`placeholder`、备注与脚注 100% |

两个案例都**刻意不写答案**：材料里只有论文式正文与数据，没有"成稿幻灯片"；
`examples/cases/**` 里不存在任何 `result.json` 或幻灯片成品。

## 1. 期望结构（写在哪、怎么读）

期望写在每个 `case.json` 的 `_case_set` 里，分两块：

```jsonc
"_case_set": {
  "difficulty": "基础层（数据表齐备、结构清晰）",
  "topic": "实验科学 / 材料器件",
  "expect": {                       // ① 硬判据：不满足即 FAIL
    "status_any_of": ["success", "partial"],
    "slide_count": 8,
    "roles_head": "cover", "roles_tail": "takeaway",
    "must_have_figure_kind": ["chart_image", "table"],
    "unverified_claims_max": 2,
    "min_notes_coverage": 1.0, "min_evidence_footer_coverage": 1.0,
    "must_mention_in_deck": ["PABr", "1.12", "92"],
    "forbid_in_deck": ["95.0％", "30 年", "Science 2024"]
  },
  "known_gaps": {                   // ② 已知缺口：实测未达成，只记录（advisory），不计入 FAIL
    "unverified_claims_max": 0,
    "why": "材料没有『背景』小节 → background 页写占位主张 → unverified=1 → status=partial。"
  }
}
```

**为什么把"允许 partial"写进硬判据**：材料的缺口是材料的事实。
案例 A 没有"背景"小节、案例 B 没有"研究问题"小节，于是对应页会写一条
**占位主张**（"材料未提供…段落；请在讲稿中补充，不臆造引用"）并进 `unverified_claims`，
按 `main.py` 的状态规则就应当是 `partial`。**把 partial 判成 FAIL 才是错的**——
那会逼着实现去粉饰。

**为什么要有 `known_gaps`**：像"材料里的年份是否进了页面"这种**内容覆盖**问题，
当前实现确实做不到（见 §3 GAP-B2）。如果把它写成硬判据，本台就会长期红着，
久了没人看。写进 `known_gaps` 的效果是：判定 PASS，但每次运行都会**把缺口打印出来**，
逼它不被忘记。

## 2. 逐案实测（2026-11-23，两案例各跑一次）

### 2.1 案例 A `ppt-6ad93034-case-a-perovskite-001`

| 观测量 | 实测 | 判定 |
|-|-|-|
| `exit` / `status` | `1` / `partial` | ✅ `status ∈ {success, partial}` |
| `deck.slide_count` | **8** | ✅ |
| 角色序列 | `cover → overview → background → discussion → question → method → result → takeaway` | ✅ 首 `cover` / 末 `takeaway` |
| 图表形态 | `chart_image × 1`（第 7 页，`table_id=jv.csv`，8 行原样重绘）+ `none × 7` | ✅ |
| `unverified_claims` / `material_warnings` / `uncertainty` | 1 / 0 / 0 | ✅ ≤2 |
| 备注覆盖 / 证据脚注覆盖 | **1.0 / 1.0** | ✅ |
| 关键内容入页 | `PABr` ✓、`1.12` ✓（以 `1.` + `12 V` 断句形式出现）、`92` ✓ | ✅ |
| 禁列内容 | 无 `95.0％` / `30 年` / `Science 2024` | ✅ 无编造 |
| 契约门 / 自检 / deck 重开 | `valid=true` / `all_pass=true` / 8 页可重开 | ✅ |
| `result.json` 顶层键数 | **20**（18 个基键 + `case_topic`、`difficulty`、`is_synthetic` 三个契约回显） | ✅ |
| **advisory 缺口** | `unverified_claims_max`：实测 1（期望 0）——原因见 `known_gaps.why` | 记录，不判 FAIL |

### 2.2 案例 B `ppt-6ad93034-case-b-climate-text-001`

| 观测量 | 实测 | 判定 |
|-|-|-|
| `exit` / `status` | `1` / `partial` | ✅ |
| `deck.slide_count` | **6** | ✅ |
| 角色序列 | `cover → overview → question → method → result → takeaway` | ✅ 首末正确；材料 5 节被压进 4 个内容页 |
| 图表形态 | **`none × 6`**（没有任何图表，也没有凭空曲线） | ✅ 允许集合 `{none, placeholder}`；✅ 未出现 `chart_image` |
| `unverified_claims` / `material_warnings` / `uncertainty` | 1 / 0 / 0 | ✅ ≤3 |
| 备注 / 脚注覆盖 | **1.0 / 1.0** | ✅ |
| 禁列内容 | 无 `87.6％` / `12.4 万篇` / `Nature Climate Change 影响因子` | ✅ 无编造 |
| 契约门 / 自检 / deck 重开 | `valid=true` / `all_pass=true` / 6 页可重开 | ✅ |
| **advisory 缺口** | `must_mention_in_deck`：缺失 `['2009', '2015']` —— 见 §3 GAP-B2 | 记录，不判 FAIL |

**两案对比得出的第一条结论**：同一套流程在"有数值表"与"无数值表"两种题材上都能产出
结构完整的稿子，且**无表时不会编造图表**（案例 B 实测 `figure_kinds = {none: 6}`，
被禁的 `chart_image` 一次都没出现）。

## 3. 泛化失效边界（实测，不是推测）

### 3.1 从两个案例直接观察到的缺口

| 编号 | 现象（实测） | 触发条件 | 影响 |
|-|-|-|-|
| **GAP-A1** | `background` 页出现占位主张，`unverified_claims=1`，`status=partial` | 材料**没有**"背景"小节（案例 A） | 状态降级、多一条待核验项；**是诚实降级，不是错误** |
| **GAP-B1** | `overview` 页出现一条只写了 `1.` 的退化主张 | 材料正文里的**编号小标题**（`## 1. …`）被当作列表项切分，且该项只有一个序号 | 该页多一条无意义要点；`plan_lint` 未拦（长度合规） |
| **GAP-B2** | 材料 §2 里的年份 `2009`/`2015` **没有进入任何页** | 章节名不是"标准论文骨架"（本案为"三阶段/争论焦点/方法与数据争议"），角色→章节映射落空 | 关键时间信息丢失；页面仍能通过全部结构与契约判据 |
| **GAP-B3** | 结果页取到的是**摘要**（不是最像"结果"的小节），方法页取到的是"方法与数据争议（局限）" | 同上：角色→章节靠标题关键词匹配 | 内容编排与论文实际结构错位；**页序与角色本身仍完整** |
| **GAP-A2** | 材料 §3 的 markdown 表格（表 1，含 PCE 24.8% 等）**没有**成为数据源，数据源是 CSV `jv.csv` | 材料同时有 markdown 表与 CSV | 表 1 里的关键指标没进页面；`unverified` 未增加（因为不是"数字对不上"，而是"没被用上"） |

### 3.2 四种边界变形探针（`--probes`，全部实测）

| # | 变形 | exit | status | slides | 图表形态 | unverified | unc | 实测结论 |
|-|-|-|-|-|-|-|-|-|
| P1 | 材料给**两张**数据表（`jv.csv` + `jv_second.csv`） | 1 | partial | 8 | `chart_image ×1` + `none ×7` | 1 | 0 | ❌ **只绑定第一张**：`material_view` 里两张表都在（`jv.csv` 8 行、`jv_second.csv` 8 行），但页面只用了 `jv.csv`；第二张被忽略且**没有任何 uncertainty 记录** |
| P2 | 材料**没有任何章节标题**（纯段落） | 1 | partial | 8 | `chart_image ×1` + `none ×7` | 3 | 1 | ⚠️ 占位主张从 1 条涨到 3 条（背景/讨论/方法各一条），同时 `plan_lint` 报出 `page 2 bullet too long (chars=95, CJK-weighted=162 vs limit=90)` 并进 `uncertainty` → **降级路径本身是留痕的**（D4 生效） |
| P3 | 页数上限压到 **3**（材料内容远超） | 0 | success | 3 | `chart_image ×1` + `none ×2` | 0 | 0 | ⚠️ 角色被压成 `cover → overview → result`，**中间页直接消失**；`change_records` 里**只有一条 `start`**，没有任何"压缩了哪些页"的记录（D7 说"不静默丢证据页"，实测记录为空） |
| P4 | 用 `--edit` 往页面塞一个材料里没有的数字（`31.7%`） | 1 | partial | 8 | `chart_image ×1` + `none ×7` | **2** | 0 | ✅ **编辑链路仍过 D2**：新主张进 `unverified_claims`（`missing_numbers=["31.7%"]`），`change_records` 多一条 `{version: probe, op: update_bullet, page: 8, reason: 探针：材料里没有 31.7%}`。**没有因为"是用户让改的"就放行** |

### 3.3 边界结论（可直接引用的四句话）

1. **结构面很稳**：四种变形 + 两个题材，`exit ∈ {0,1}`、都有 `result.json`、
   deck 全部可重开、页数全部等于 `spec.max_slides`、备注与脚注覆盖全部 1.0。
   即：**换题材、换结构、压页数都不会让它塌成"不成稿"。**
2. **内容映射面不稳**：角色→章节靠标题关键词，材料越是"非标准骨架"
   （人文/理论/综述），越容易出现 GAP-B1/B2/B3 这类**内容错位但不报错**的结果。
   这类问题不会被 G1–G8 或自检抓到，**必须人工看页面**。
3. **多模态资源只认第一份**：材料给了两张表时只绑定第一张（P1），且不留痕。
   需要多表时，应在材料侧把要用的表**放在 `material[]` 的第一位**。
4. **页数压缩不记录**（P3）：`max_slides` 过紧时角色被裁掉却没有 `change_records`。
   要么放宽 `max_slides`，要么在交付说明里人工写明"哪些页被合并"。

## 4. 怎么加新案例（生态贡献：题集是可扩展的）

1. 在 `examples/cases/` 下新建目录，放 `case.json` + 材料文件（`.md`/`.csv`/`.txt` 等文本）；
2. 在 `case.json` 里写 `_case_set.expect`（硬判据）与 `_case_set.known_gaps`（已知缺口）；
   **硬判据只写"诚实行为"**：能接受 `partial`、不许出现被禁图表形态、要求备注/脚注覆盖；
3. 跑 `python "$SKILL_DIR/scripts/case_check.py" --pkg "$SKILL_DIR" --work <包外>`；
4. 想把新案例也当探针底：`--probe-case <你的案例目录名>`。

**判据写法小抄**（本包里两个案例都用到了）：

| 判据 | 用途 | 例 |
|-|-|-|
| `status_any_of` | 允许诚实降级 | `["success","partial"]` |
| `slide_count` | 页数必须等于上限 | `8` |
| `roles_head` / `roles_tail` | 首末角色固定 | `cover` / `takeaway` |
| `must_have_figure_kind` | 必须有某种图表形态 | `["chart_image","table"]` |
| `forbid_figure_kind` | **不许编造**（无数表时禁止 `chart_image`） | `["chart_image"]` |
| `unverified_claims_max` | 待核验项上限 | `2` |
| `min_notes_coverage` / `min_evidence_footer_coverage` | 备注/脚注覆盖 | `1.0` |
| `must_mention_in_deck` | 关键数字/术语必须入页 | `["PABr","1.12","92"]` |
| `forbid_in_deck` | 禁列内容（防编造） | `["95.0％","30 年"]` |

## 5. 诚实边界

1. **两个案例都是合成材料**（虚构数据、虚构引用），只用于演示与交叉验证，
   **不是正式案例、不含正式答案**；`case.json` 里的 `_note` 已逐条标注。
2. **案例数量是 2**，不是"覆盖了整个学术 PPT 领域"：题材只覆盖"实验科学 / 理论文本"两端，
   没有覆盖医学统计、工程图纸、教学课件等形态。
3. **判定是结构+覆盖判据，不是质量判据**：本台能证明"页数对、角色在、备注全、没编造"，
   **不能证明"这一版讲得好"**——那需要人工评审。
4. **探针只有 4 种**（多表 / 无标题 / 页数过紧 / 编辑引入新数字），
   没有覆盖非 UTF-8 材料、超长材料、跨语言材料；非 UTF-8 由 `FAULT-MATRIX.md` 的
   `F-IN-08` 覆盖（属失败注入面，不属泛化面）。
