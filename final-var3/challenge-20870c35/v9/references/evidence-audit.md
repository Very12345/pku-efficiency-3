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