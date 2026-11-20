# OUTPUT_CONTRACT.md — result.json 契约（challenge-9034312d · figures 组）

本文件定义 `result.json` 的结构化契约。Skill 运行后必须写出的 result.json
含下列**全部字段**与 `case_id`。字段缺失或类型不符 ⇒ `scripts/check.py` 报 isssue，
status 不能为 success。

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
       "layers": ["title","arrows","entities","legend"],
       "editability": "文字为可编辑 <text>、实体组带 data-entity/data-source",
       "checksum_sha256": "…"}
    ],
    "exports": [
      {"kind": "png", "path": "figure.png", "format": "image/png",
       "width_px": 2362, "height_px": 1496, "dpi": 200,
       "font_ttf": "C:\\Windows\\Fonts\\msyh.ttc(可空)"},
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

  // ===== 元数据 =====
  "canvas": {"width_mm": 311.11, "height_mm": 166.0, "requested": {"width_mm": 300, "height_mm": 190}},
  "fonts": [{"role": "svg|png|pdf", "mode": "…", "family/path/name": "…", "found/embedded": …}],
  "sources": [{"id": "input-case", "file": "case.json", "note": "case.json"}],
  "uncertainty": [{"scope": "…", "issue": "…", "action": "…"}],   // 诚实记录，可为 []
  "change_record": [{"time": "ISO8601", "action": "…", "target": "…", "reason": "…", "by": "…"}],
  "execution": {"script": "main.py", "python": "3.13.9", "out_dir": "…"},
  "checksum": "sha256(case_id+entities+relations+svg_sha)"
}
```

## 状态语义（status）

| 取值 | 判定 |
|-|-|
| `success` | 实体≥1；SVG/PNG/PDF 均生成；自查通过；无孤儿实体降级条件 |
| `partial` | 存在未解决的 uncertainty（如孤儿实体、文本解构、缺字体、某个预览失败）→ 必须说明 |
| `failed` | 管线异常（输入缺失/不可解析）→ main.py 兜底写出含 error 的 result.json |

## element_traceability（元素可追溯）

- SVG 每个实体组 `entity-<id>` 与 data_mapping 一一对应；
- 每条箭头 `arrow-<id>` 记录 from/to 与 source；
- 保证「图面元素 ↔ 输入材料」可双向回溯，支撑他人独立复核与重绘。

## 自查命令

```
python scripts/check.py <result.json>
```

产出 `{ok, checks, issues}`；`ok:true` 且 issues 为空才算交付完整。
check.py 检查项：必需字段、editable_sources/exports/data_mapping/element_traceability、
产物文件真实存在且非空、SVG 可解析且 `<text>`≥3 + 分层 `<g>`≥3、关系无断头箭头、
route/flow 步骤编号连续、status 与 data_mapping 一致。