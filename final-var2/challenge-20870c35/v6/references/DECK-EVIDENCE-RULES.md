# DECK-EVIDENCE-RULES.md — 页面/版式规则 + 证据审计规范（v6 合并版）

> 由 `references/deck-rules.md` 与 `references/evidence-audit.md` 合并，内容逐字保留。


---

# 【合并段】页面 / 版式 / 命名规则（全文）

> 本段原为独立文件 `references/deck-rules.md`，在 v6（union 包）中并入本文件以守住「≤50 文件」硬门；**内容逐字保留**，未删减。

# deck-rules.md — 页面/版式规则（deck rules）

> 对应高分 intent 的 `deck_rules.md`（75.33 分包核心文档之一："页面/deck 规则"）。
> 机器可执行部分在 `templates/talk_config.json` 的 `deck_rules` 段与
> `scripts/verify_deck.py`；本文档解释规则与理由。

## 1. 页级内容规则（一页一主张）

| 规则 | 值 | 执行/校验 |
|-|-|-|
| 每页唯一主张 | claim 逐字取自源材料（6–500 字） | validate_plan P5/P7 |
| 每页一句可讲的话 | one_liner ≤ 64 字，与页面结论对应 | P7、`scaffold_plan._one_liner` |
| 每页备注 | notes 含【本页主张】【证据】【讲解】（+【备答】） | verify_deck（notes 非空）、P8 |
| 封面/目录/收尾 | 也写 notes（讲解责任分离） | verify_deck 全页检查 |
| weak 页显式提示 | 页内"※ 间接概括"行 + uncertainty 记录 | deck_builder、main |

## 2. 图表规则（图表引用 ↔ 页内结论对应）

- `figure_ref` 提取自源材料中的引用标记（Fig./图/Table/表/Scheme…，见
  `evidence.extract_figure_refs`），页内结论与它绑定（不是随便配图）；
- 图绑定：按引用 token 与材料图片文件名匹配（'Fig. 2' → fig2.png）——
  找不到图片 → **诚实占位框**（标注"材料未提供图片文件"，不虚构插图）；
- 图占位/绑定状态写入 evidence_audit + deck_audit（figure_element/占位框），
  preview 相应区域也提示。

## 3. 版式与可编辑性规则

- **布局来源**：案例模板/起始 deck → `python-pptx` 打开并**沿用其母版与版式**；
  模板自带的示例页会被丢弃（`deck_mode.template_slides_present/dropped` 记明），
  页数一律按冻结计划重建，保证**最终页数 == 冻结页数**（见 failure-modes F22）；
  无模板 → 包内置主题（16:9 母版 + 主题色 + 底栏装饰 master-accent-bar）；
- **确定性元素命名**（可编辑性的机器证据，也是人工定位入口）：

  | 元素 | 命名 |
  |-|-|
  | 封面标题 | `cover-title`（无标题占位时）/ 复用占位符 |
  | 封面元信息 | `cover-meta` |
  | 内容页标题 | `page-title-NN`（无标题占位时）/ 复用占位符 |
  | 内容页主张区 | `page-claim-NN`（必检：verify_deck G6） |
  | 图/占位区 | `page-figure-NN` |
  | 页脚 | `page-footer-NN` |
  | 母版底栏 | `master-accent-bar` |

- **字体**：西文 Arial / CJK Microsoft YaHei（`a:ea` 显式写 east-asian typeface，
  换机不丢中文字体）；预览用 PIL 按候选路径探测系统 CJK 字体（Windows/Linux/macOS），
  探测结果（仅文件名）记入 `result.json.environment.cjk_font` 与 `preview_manifest.json`；
  找不到则 `load_default` 继续并在 manifest 记明字形可能缺失（failure-modes F26）。
- **页数脚注**：每页页脚 `NN / total · case_id`，便于答辩现场按页对证据。

## 4. 导出与预览规则

- 主交付 = 可编辑 `editable_deck.pptx`；预览 = PIL 模拟 PNG（水印 + manifest 限制说明），
  非 Office 栅格化，不作"已渲染美观"的虚假声明；
- `decks` 由 `verify_deck.py` 校验：打开、页数 == 计划、每页备注与 claim 元素、OPC 完整；
- `preview_manifest.json` 列出全部预览文件与限制。

## 5. 人核辅助

上台前用 `templates/HUMAN-TEMPLATES.md`（逐页核对清单）复查：
主张可溯源、引文未改写、图表对应、强度匹配、讲稿不重复、数字一致。

---

# 【合并段】证据审计规范（全文）

> 本段原为独立文件 `references/evidence-audit.md`，在 v6（union 包）中并入本文件以守住「≤50 文件」硬门；**内容逐字保留**，未删减。

# evidence-audit.md — 证据审计规范（claim → 定位 → 引文 机器核验）

> 对应高分 intent 的 `evidence_audit.py` / `audit_evidence` 脚本形态（"内容从材料出发"）。
> 执行者：`scripts/evidence_audit.py`；产物：`<out>/evidence_audit.json`；随
> `result.json` 的 `audit.evidence` 归档；`selftest.py` 可对已产出结果独立复跑。

## 1. 为什么需要它

评分三件事：**页面上每一个论断是否能在源材料里找到对应位置、叙事顺序是否服务于
听众与时长、从源材料到成稿的取舍过程能否被他人复核**。前两件靠计划/叙事/引文，
第三件必须落到"逐页证据可机器复核"：每一页的 `quote` 都应**逐字**出现在实际读取的
源文本中，`locator`（L行·§章节）应在源文本边界内，`source_file` 应在 `sources` 声明。

## 2. 审计条目（每个内容页一条）

| 字段 | 含义 |
|-|-|
| `page_no` / `block` / `title` | 页面标识 |
| `kind` | `structural`（title/agenda/qa，轻查）或 `content` |
| `derived` | 该页是否由章节概括而成（无直接主张 → frame） |
| `quote_found` | true=逐字命中；false+derived=概括语（如实标注）；false 非 derived=错误；null=源文本不可得 |
| `line_ok` / `line_text` | line_no 是否在源文本行界内 + 该行原文前 80 字 |
| `numbers_not_in_source` | claim 中未在源文本逐字出现的数字（警告级，合理换算可忽略） |
| `figure_ref` / `figure_bound` | 图表引用与图片绑定状态（未绑定=诚实占位框） |
| `notes` | 该页审计说明（含 derived/未命中/缺图等） |

## 3. 判定规则

- `valid` = 所有 content 页 `ok`（无硬错误）；derived 页未逐字命中**不算**硬错误，
  但必须标注"概括语 + weak"，由 `scaffold_plan` 在规划期就标记 `derived=true`；
- `source_file` 未在 `sources` 声明 = 硬错误（对应 validate_result 的
  evidence-sources-declared 检查）；
- 数字对源为警告级——同 `validate_result.py` 的口径（"92"由"92.3%"截断而来不算失信）。
- 运行期（main.py）审计使用**实际读取的材料文本**（`material_records[].text`），
  独立复跑（selftest）则尽力从磁盘重读；磁盘不可得时记 `quote_found=null` + 说明。

## 4. 与高分流的关系

- "无证据审计、直接把摘要搬上页"的包 → 本技能每页强制 locator+quote 且机器逐字核验；
- 高分 75.33 包的 `evidence_audit.py` 与 74.67 的 `audit_evidence.py` 都是独立审计脚本
  —— 本包 `evidence_audit.py` 与之同名同责，并增强为"逐字命中 + 定位边界 + 数字对源 +
  derived 诚实标注"四合一。

## 5. 独立复核

```bash
# $SKILL_DIR = 本包根目录（含 SKILL.md）；脚本自定位，cwd 任意
python "$SKILL_DIR/scripts/evidence_audit.py" <out>/result.json --out <out>/evidence_audit_reread.json
python "$SKILL_DIR/scripts/evidence_audit.py" <out>/result.json --sources-dir <case材料目录>
python "$SKILL_DIR/scripts/selftest.py" <out>            # 内含 evidence_audit 重跑
```

> 独立复跑时若源材料不在 result 目录旁，用 `--sources-dir` 指向材料目录，
> 否则该来源会记 `quote_found=null`（"源文本不可用"）——这**不是**错误，
> 但会少一层逐字核验；运行期由 `main.py` 用实际读取的文本执行完整核验。