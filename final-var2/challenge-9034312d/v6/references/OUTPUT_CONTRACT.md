# OUTPUT_CONTRACT.md — result.json 契约（challenge-9034312d · figures 组 · v2）

> **本文件是契约字段的唯一权威处**，并且是 `result.json` 最小形态示例的唯一出处（示例见文末附录；原 `assets/result_example.json` 的内容已并入本文件文末，包内不再单列该文件 —— 若你在旧文档或注释里看到这个路径，指的就是那份附录）。任何文档只解释"什么情况下字段值会变成什么"，不重新定义字段。
>
> **按"故障时会发生什么"读这份契约**（实测见 `references/FAULT-MATRIX.md` §4）：
>
> | 契约段 | 注入后实测 | 拦住它的门 |
> |-|-|-|
> | `output_contract` 整段缺失 | G2/G3/G4/G5/G6 同时报 | G2 |
> | `exports` 置 `null` | G2+G4 | G2/G4 |
> | 四段全置 `[]` | G3+G4+G5+G6 | G3–G6 |
> | `exports[].path` 指向不存在的文件 | G4 | G4 |
> | `data_mapping` 少一行 | G5 | G5 |
> | `element_traceability` 少一条 `arrow-*` | G6 | G6 |
> | `status=success` 但 `verify.ok=false` | G9+G10 | G9/G10 |
> | `result.json` 被截断 | G1 | G1 |
> | `output_contract` 写成字符串 | 检查器抛栈（无门号，退出码非 0） | —（缺口 H） |
>
> 题集（`references/CASE-SET.md`）与故障矩阵（`references/FAULT-MATRIX.md`）都以本文件的字段名为准，不另起别名。
本文件定义 `result.json` 的结构化契约。Skill 运行后必须写出的 result.json
含下列**全部字段**与 `case_id`。字段缺失或类型不符 ⇒ `scripts/check.py` 报
issue，status 不能为 success。v2 新增 `evidence`（证据链）与 `verify`
（校验/规则审计）两个段落，作为「来源可核验」的机器证据。

## 顶层字段清单（必填，缺一即 `check.py` 报 issue）

```
case_id  title  status  workorder  figure_type  extraction
entities  relations
output_contract  evidence  verify
canvas  fonts  sources  uncertainty  change_record  execution  checksum
```

> 复核命令（`$SKILL_DIR` = 含 SKILL.md 的技能根）：
> `python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <tmp>/out`
> 然后对 `<tmp>/out/<case_id>/result.json` 顶层键与上表逐条比对，应无缺项。

## 顶层结构

```jsonc
{
  "case_id": "string，必填，输入案例标识（case.json 的 case_id/id，缺失时取文件名）",
  "title": "string，图稿标题",
  "status": "success | partial | failed，诚实状态（见 §状态语义）",
  "workorder": "apparatus_and_technical_route（固定，标识本工作单）",
  "figure_type": "route | apparatus | flow | hybrid",
  "extraction": "structured | text-heuristic（实体来源方式）",

  // 与图面对应的结构化数据（自检与复核依据）
  "entities": [
    {"id": "E1", "name": "…", "kind": "step|phase|device|material|product|data|decision|milestone|waste|container",
     "stage": "阶段(可空)", "step_no": "1(可空)", "source": "任务材料出处(可空)"}
  ],
  "relations": [
    {"id": "R1", "from": "E1", "to": "E2", "kind": "flow|connect|depend|recycle|sequence|causation",
     "label": "…(可空)", "source": "出处(可空)"}
  ],

  // ===== output_contract：组织方契约字段 =====
  "output_contract": {
    "editable_sources": [
      {"kind": "svg", "path": "figure.svg", "format": "image/svg+xml",
       "layers": ["layer-background","layer-title","layer-arrows","layer-entities","layer-legend"],
       "editability": "文字为可编辑 <text>、实体组带 data-entity/data-source/data-step-no",
       "checksum_sha256": "…"}
    ],
    "exports": [
      {"kind": "png", "path": "figure.png", "format": "image/png",
       "width_px": 2362, "height_px": 1496, "dpi": 200,
       "font_ttf": "运行时探测到的本机 TTF 文件名（未找到则 null；包内不写本机绝对路径）"},
      {"kind": "pdf", "path": "figure.pdf", "format": "application/pdf",
       "vector": true, "font": "STSong-Light"}
    ],
    "data_mapping": [
      {"entity_id": "E1", "kind": "step", "source": "task.md §2.1", "svg_group": "entity-E1"}
    ],
    "element_traceability": [
      {"element": "entity-E1", "source": "…", "kind": "…", "stage": "…"},
      {"element": "arrow-R1", "from": "E3", "to": "E2", "source": "…"}
    ]
  },

  // ===== v2 新增：证据链 =====
  "evidence": {
    "source": "gain_evidence",
    "extraction": "structured | text-heuristic",
    "items": [ {"id": "EV1", "type": "entity|relation", "ref": "E1", "locator": "task.md §2.1", "quote": "原文引用(≤120字)"} ],
    "source_files": [ {"file": "case.json", "sha256": "…", "size": 1234, "role": "case|task|material"} ],
    "notes": [ "材料缺口/兜底说明" ],
    "meta": {"source": "gain_evidence", "item_count": {}, "notes": []}
  },

  // ===== v2 新增：校验与规则审计 =====
  "verify": {
    "ok": true,                       // svg_verify 无 error 级违规
    "checks": {},                     // 逐项布尔（layers/editable_text/arrows/numbering/legend_kinds/…）
    "errors": [ {"rule": "…", "severity": "error", "detail": "…"} ],
    "warnings": [ {"rule": "…", "severity": "warn", "detail": "…"} ],
    "determinism": {"spec_sha16": "布局确定性探针(前16位)"},   // 同输入同布局的机器证据
    "summary": {"status": "pass|attention", "entities": n, "relations": m, "errors": e, "warnings": w, "issues": i}
  },

  // ===== 元数据 =====
  "canvas": {"width_mm": 311.11, "height_mm": 166.0, "requested": {"width_mm": 300, "height_mm": 190}},
  "fonts": [{"role": "svg|png|pdf", "mode": "…", "family/path/name": "…", "found/embedded": …}],
  "sources": [{"id": "input-case", "file": "case.json", "note": "case.json"}],
  "uncertainty": [{"scope": "…", "issue": "…", "action": "…"}],   // 诚实记录，可为 []
  "change_record": [{"time": "ISO8601", "action": "…", "target": "…", "reason": "…", "by": "…"}],
  "execution": {"script": "main.py", "skill_version": "2.0.0", "python": "3.13.9", "out_dir": "…"},
  "checksum": "sha256(case_id+entities+relations+svg_sha)"
}
```

## 状态语义（status）

| 取值 | 判定 |
|-|-|
| `success` | 实体≥1；SVG/PNG/PDF 均生成；**verify.ok=true（无 error 级规则违规）**；G1–G10 全部通过；无孤儿实体降级条件 |
| `partial` | 存在未解决的 uncertainty（孤儿实体、文本解构、缺字体、某个预览失败）**或 svg_verify 存在 error 级连接规则违规（D11）** → 必须说明 |
| `failed` | 管线异常（输入缺失/不可解析）→ main.py 兜底写出含 error 的 result.json |

## G1–G10 硬性门（scripts/check.py 可执行）

| 门 | 内容 |
|-|-|
| G1 | result.json 存在、可解析、含 case_id、status 合法 |
| G2 | output_contract 四段（editable_sources/exports/data_mapping/element_traceability）齐全且不为 null |
| G3 | 可编辑源文件真实存在；SVG 可解析且 <text>≥3、分层 <g>≥3 |
| G4 | 导出件真实存在且非空（png 至少 1 个；pdf 尽力而为） |
| G5 | data_mapping 行数 == entities 数，entity_id 唯一且与实体集合一致 |
| G6 | element_traceability 覆盖全部实体（entity-<id>）与箭头（arrow-<id>） |
| G7 | 关系两端实体均存在（无断头箭头） |
| G8 | route/flow 图步骤编号 1..N 连续 |
| G9 | verify_report.json 存在且 verify.ok=true（svg_verify 全绿） |
| G10 | status=success 时 G1–G9 全过且无未解决降级不确定性（status 诚实） |

## element_traceability（元素可追溯）

- SVG 每个实体组 `entity-<id>` 与 data_mapping 一一对应；
- 每条箭头 `arrow-<id>` 记录 from/to 与 source；
- 证据链 `evidence.items`（locator+quote）把「图面元素 ↔ 输入材料」做成可双向回溯，
  支撑他人独立复核与重绘（评分点「结果可核验性」）。

## 自查命令

脚本自定位（`os.path.dirname(__file__)`），**任何 cwd 都可运行**；
`$SKILL_DIR` = 含 `SKILL.md` 的技能根（平台安装位置为 `/skills/weekly-skill`）。

```
python "$SKILL_DIR/scripts/check.py" <result.json>      # 契约门 G1–G10
python "$SKILL_DIR/scripts/svg_verify.py" --layout <layout.json> --svg <figure.svg> \
       --out <verify_report.json>
```

产出 `{ok, gates, checks, issues}`；`check_ok:true` 且 issues 为空才算交付完整。
check.py 检查项：G1–G10、产物文件真实存在且非空、SVG 可解析且 <text>≥3 + 分层 <g>≥3、
关系无断头箭头、route/flow 步骤编号连续、status 与 verify/uncertainty 一致。

## 形式要求（四形态回显，禁止 null）

- 契约四段一律是**列表**形态（`[]` 也可，但缺失键/null 记为违规）；
- 证据/校验段 v2 起为**必填**（官方判分回放会检查来源与核验性）；
- `uncertainty`/`change_record` 为列表，可为空，但字段必须存在（不用 null）。

---

## 附录 · result.json 最小形态示例（原 assets/result_example.json）

> 最小可交付形态：字段一个不少，但实体/关系只有一条，用来对照字段名与容器类型。

```json
{
  "_doc": "result.json 最小形态示例（复用参考，非正式案例产物）。正式产出见 examples/output/*/result.json。结构与 references/OUTPUT_CONTRACT.md 一致，字段类型/语义以契约为准。",
  "case_id": "demo-route-000",
  "title": "示意图标题",
  "status": "success",
  "workorder": "apparatus_and_technical_route",
  "figure_type": "route",
  "extraction": "structured",
  "entities": [
    {
      "id": "E1",
      "name": "步骤/部件名",
      "kind": "step",
      "stage": "阶段一",
      "step_no": "1",
      "source": "task.md §2.1"
    }
  ],
  "relations": [
    {
      "id": "R1",
      "from": "E1",
      "to": "E2",
      "kind": "flow",
      "label": "流向",
      "source": "task.md §2.2"
    }
  ],
  "output_contract": {
    "editable_sources": [
      {
        "kind": "svg",
        "path": "figure.svg",
        "format": "image/svg+xml",
        "layers": [
          "layer-background",
          "layer-title",
          "layer-arrows",
          "layer-entities",
          "layer-legend"
        ],
        "editability": "text 元素真实文本、实体组带 data-entity/data-source/data-step-no",
        "checksum_sha256": "…"
      }
    ],
    "exports": [
      {
        "kind": "png",
        "path": "figure.png",
        "format": "image/png",
        "width_px": 2362,
        "height_px": 1496,
        "dpi": 200
      },
      {
        "kind": "pdf",
        "path": "figure.pdf",
        "format": "application/pdf",
        "vector": true,
        "font": "STSong-Light"
      }
    ],
    "data_mapping": [
      {
        "entity_id": "E1",
        "kind": "step",
        "source": "task.md §2.1",
        "svg_group": "entity-E1"
      }
    ],
    "element_traceability": [
      {
        "element": "entity-E1",
        "source": "task.md §2.1",
        "kind": "step",
        "stage": "阶段一"
      },
      {
        "element": "arrow-R1",
        "from": "E1",
        "to": "E2",
        "source": "task.md §2.2"
      }
    ]
  },
  "evidence": {
    "source": "gain_evidence",
    "extraction": "structured",
    "items": [
      {
        "id": "EV1",
        "type": "entity",
        "ref": "E1",
        "locator": "task.md §2.1",
        "quote": "原文句子…"
      }
    ],
    "source_files": [
      {
        "file": "case.json",
        "sha256": "…",
        "size": 1024,
        "role": "case"
      }
    ],
    "notes": [],
    "meta": {
      "source": "gain_evidence",
      "item_count": {},
      "notes": []
    }
  },
  "verify": {
    "ok": true,
    "checks": {},
    "errors": [],
    "warnings": [],
    "determinism": {
      "spec_sha16": "…"
    },
    "summary": {
      "status": "pass",
      "entities": 1,
      "relations": 1,
      "errors": 0,
      "warnings": 0,
      "issues": 0
    }
  },
  "canvas": {
    "width_mm": 311.11,
    "height_mm": 166.0,
    "requested": {
      "width_mm": 300,
      "height_mm": 190
    }
  },
  "fonts": [],
  "sources": [
    {
      "id": "input-case",
      "file": "case.json",
      "note": "case.json"
    }
  ],
  "uncertainty": [],
  "change_record": [],
  "execution": {
    "script": "main.py",
    "skill_version": "2.0.0",
    "python": "3.13.9",
    "out_dir": "…"
  },
  "checksum": "sha256(case_id+entities+relations+svg_sha)"
}
```
