# OUTPUT_CONTRACT.md — result.json 输出契约

本 Skill 每个案例运行后必须在输出目录生成 `result.json`（外加可编辑演示文件、
预览件、证据映射与版本记录）。本文件定义结构、字段语义与判读规则；平台若有
`/input/case.json` 内联的 `output_contract`，脚本会把它声明的字段原样镜像到
`result.json` 顶层并给出容器类型默认值（`""` / `[]` / `{}` / `0` / `false`），
保证只读该 schema 的验证器也能通过；诚实性通过 `status` 与 `uncertainty`
表达，绝不填充编造值。

## 1. 顶层字段（必填）

| 字段 | 类型 | 说明 |
|-|-|-|
| `case_id` | string | 案例标识，必须与 case.json 一致 |
| `title` | string | 汇报标题（来自材料标题，非自造） |
| `status` | string | `success` / `partial` / `failed`，见 §3 |
| `created_at` | string | ISO-8601 本地时间 |
| `skill_version` | string | Skill 版本号 |
| `deck` | object | 可编辑演示文件信息，见 §2 |
| `evidence` | object | 页级证据映射，见 §4 |
| `previews` | object | 渲染预览，见 §5 |
| `sources` | array | 实际读取的输入文件 `{role, path, sha256}` |
| `uncertainty` | array | 每条一个字符串：无法核验/缺失/降级的事实，宁多勿漏 |
| `change_records` | array | 版本记录（每次构建/编辑一条） |
| `log` | string | 本次运行的日志文件（相对路径） |
| `checks` | object | 自检结果 `{all_pass, checks:[{name, ok, detail}]}` |
| `environment` | object | 实测运行环境（python/pptx/matplotlib/PIL/reportlab 版本） |
| `output_contract` 声明字段 | 任意 | 若 case.json 带 `output_contract` 字典，逐项镜像 |

## 2. deck 对象

```jsonc
{
  "editable": "work/deck.pptx",          // 可编辑源，相对输出目录
  "format": "pptx",
  "template": "default",                 // 或模板文件名
  "template_pptx": "",                   // 组织方模板（若有）
  "starting_deck": "",                   // 起始稿（若有，将备份并适配）
  "slide_count": 8,
  "slides": [                            // 页级结构：页序+叙事角色+主张+证据
    {
      "index": 1, "role": "cover", "role_label": "封面", "title": "…",
      "claims": [{"text": "…", "evidence": ["§方法", "表(结果表)"],
                  "verified": true, "missing_numbers": []}],
      "figure": {"ref": "表(结果表)", "kind": "chart_image",
                 "table_id": "results.csv", "image": "work/chart_results.csv.png",
                 "note": "…"},
      "notes": ["…"],                    // 讲稿/备注要点
      "evidence_footer": "证据: … | 图表: …"
    }
  ],
  "notes": true,                          // 每页均有演讲者备注
  "receipt": []                           // 页面构建回执（每页字号/图表细节）
}
```

## 3. status 规则

- `success`：PPTX 生成、预览渲染、result.json 与自检全部完成。
- `partial`：核心产物可用但部分步骤降级（如 matplotlib 不可用改原生表格、
  PDF 预览缺字体、编辑未应用），降级原因必须写进 `uncertainty`。
- `failed`：无法读取输入或无法生成任何可打开产物；仍要写一个最小 result.json
  说明原因，绝不假装成功。

## 4. evidence 对象

```jsonc
{
  "map": [{"page": 1, "role": "cover", "title": "…",
           "evidence": ["摘要/引言"], "figure_ref": "", "figure_kind": "none"}],
  "unverified_claims": [{"page": 4, "text": "…", "missing_numbers": ["0.123"]}],
  "material_warnings": ["…"]
}
```

规则：每页主张必须能指回 图/表/章节/数据；数字出现在页面上但材料中找不到
（`unverified_claims`）属于**未核验主张**，脚本会主动留痕且不视为正确数据。

## 5. previews 对象

```jsonc
{
  "pngs": ["preview/slide_01.png", "…"],
  "pdf": "preview/preview.pdf",
  "method": "PIL/reportlab 预览渲染，非 PowerPoint 导出",
  "warnings": ["预览未找到 CJK 字体…"]
}
```

预览文件名与 `method` 字段都明确标注**预览渲染**：运行环境无 PowerPoint/
LibreOffice，因此预览由页面模型渲染（PIL 画布 + reportlab 文本页），供肉眼
检查版式与内容；它不是 Office 导出件，也不冒充。

## 6. 判读规则（供评审与复跑）

1. 可复核性：以 `sources[].sha256` 对拍输入；以 `manifest.json`（输出目录根）
   对拍全部产出文件；`changelog.jsonl` 记录每轮改动。
2. 不编造规则：`claims.verified=false` 或 `uncertainty` 中的应用不算正确数据；
   宁可标注"未核验/缺失"也不臆造数字、指标或图表。
3. 编辑链条：`--edit` 每次修改在 `change_records` 新增一条
   `{version, op, page, target, reason}`，deck 以 `deck_v{n}.pptx` 归档，
   任一版本可回退重放。
4. 复跑一致性：同一 case、同一 spec、无 `--edit` 时，脚本输出确定性结构；
   仅时间戳与 sha256 不同。

本契约由 `scripts/check_contract.py <result.json> [<case.json>]` 自动校验。