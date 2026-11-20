# OUTPUT_CONTRACT.md — result.json 输出契约（v2）

本 Skill 每个案例运行后必须在输出目录生成 `result.json`（外加可编辑演示文件、
预览件、证据映射双形态与版本记录）。本文件定义结构、字段语义、判读规则与
**G1–G8 硬性门**；`scripts/result_tool.py` 依据本契约与
`templates/result_envelope.json` 自动校验（CP4 检查点）。

## 1. 顶层字段（必填）

| 字段 | 类型 | 说明 |
|-|-|-|
| `case_id` | string | 案例标识，必须与 case.json 一致（G2） |
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
| `evidence_map_json` | string | 机器可读证据映射文件名（`evidence_map.json`） |
| `manifest` | string | 产物 sha256 清单文件名（`manifest.json`） |
| `log` | string | 本次运行的日志文件（相对路径） |
| `checks` | object | 自检结果 `{all_pass, checks:[{name, ok, detail}]}` |
| `environment` | object | 实测运行环境版本（python/pptx/matplotlib/PIL/reportlab） |
| `run_meta` | object | 运行元信息（checkpoints/spec_lint/render_qa/timestamp…） |
| 契约回显字段 | 任意 | `case.json.output_contract` 声明的字段逐项镜像（四形态，禁 null） |

## 2. deck 对象

```jsonc
{
  "editable": "work/deck.pptx",          // 可编辑源，相对输出目录
  "format": "pptx",
  "template": "default",                 // 或模板文件名
  "template_pptx": "",                   // 组织方模板（若有；母版不动只填槽位）
  "starting_deck": "",                   // 起始稿（若有，备份到 work/original_inputs/ 后替换页面）
  "slide_count": 6,
  "slides": [                            // 页级结构：页序+叙事角色+主张+证据
    {
      "index": 1, "role": "cover", "role_label": "封面", "title": "…",
      "claims": [{"text": "…", "evidence": ["§方法", "表(结果表)"],
                  "verified": true, "missing_numbers": []}],
      "figure": {"ref": "表(结果表)", "kind": "chart_image",
                 "table_id": "results.csv", "image": "work/chart_results.csv.png",
                 "note": "…"},
      "notes": ["…"],                    // 讲稿/备注要点（与页面文字分离生成）
      "evidence_footer": "证据: … | 图表: …"
    }
  ],
  "notes": true,                          // 每页均有演讲者备注（G6）
  "receipt": []                           // 页面构建回执（每页字号/图表细节）
}
```

## 3. status 规则

- `success`：PPTX 生成、预览渲染、契约校验（G1–G8）、自检全部完成；
  `unverified_claims` 为空。
- `partial`：核心产物可用但部分步骤降级（图表重绘降级原生表格、PDF 预览缺、
  预览缺 CJK 字体、CP2 lint 有偏差、编辑未应用、unverified_claims 非空）。
  每条降级原因必须写进 `uncertainty`。
- `failed`：无法读取输入或无法生成任何可打开产物；仍写最小 result.json 说明
  原因（D1），绝不假装成功。

## 4. evidence 对象

```jsonc
{
  "map": [{"page": 1, "role": "cover", "title": "…",
           "evidence": [], "figure_ref": "", "figure_kind": "none"}],
  "unverified_claims": [{"page": 4, "text": "…", "missing_numbers": ["0.123"]}],
  "material_warnings": ["…"]
}
```

规则（evidence_check.py 强制）：
1. 每页主张必须能指回 图/表/章节/数据（claims 非空且无证据 → G4 硬性报错）；
2. 数字出现在页面上但材料中找不到（`unverified_claims`）属**未核验主张**，
   脚本主动留痕且不视为正确数据；
3. 材料缺失与运行失败分别写 `material_warnings` 与 `uncertainty`，不得混淆。

## 5. previews 对象

```jsonc
{
  "pngs": ["preview/slide_01.png", "…"],
  "pdf": "preview/preview.pdf",            // reportlab 不可用时为 ""
  "method": "PIL/reportlab 预览渲染，非 PowerPoint 导出",
  "warnings": ["预览未找到 CJK 字体…"]
}
```

预览文件名与 `method` 都明确标注**预览渲染**：运行环境无 PowerPoint/
LibreOffice 时预览由页面模型渲染（PIL 画布 + reportlab 文本页），供肉眼检查
版式与内容；它不是 Office 导出件，也不冒充（D8）。

## 6. 双形态证据映射

- `evidence_map.md`：人读表格（每页 → 角色/标题/证据定位/状态 mapped|gap）；
- `evidence_map.json`：机器可读（同一来源 `deck.slides`，行数一致）。
- 自检（selftest.py）与 G4 门校验两文件存在且行数 = 页数。

## 7. 判读规则（供评审与复跑）

1. 可复核性：`sources[].sha256` 对拍输入；`manifest.json` 对拍全部产出文件；
   `changelog.jsonl` 记录每轮改动；`deck` 可被 python-pptx 重新打开。
2. 不编造：`claims.verified=false` 或 `unverified_claims` 中的应用不算正确
   数据；宁可标注"未核验/缺失"也不臆造数字、指标或图表。
3. 编辑链条：`--edit` 每次修改写一条 `{version, op, page, target, reason}`，
   deck 以 `deck_<version>.pptx` 归档，任一版本可回退重放（EDIT_OPS.md）。
4. 复跑一致性：同一 case、同一 spec、无 `--edit` 时结构确定输出；差异仅限
   时间戳（created_at / generated_at / 日志文件名）——见 TEST.md 双跑记录。

## 8. CP4 硬性门：G1–G8（result_tool.py validate 强制）

| 门 | 检查 | 不通过后果 |
|-|-|-|
| G1 | result.json 可解析；顶层/deck/evidence/previews 必备字段齐；status 在词汇表 | error |
| G2 | case_id 非空且与 case.json 一致（不一致为 warning）；output_contract 声明字段全部回显且非 null | error |
| G3 | deck.editable 存在、python-pptx 可重开、页数=deck.slide_count=deck.slides 数 | error |
| G4 | 每页有 role/title；claims 非空的页必须有证据或显式 gap；unverified_claims 与 status 一致性 | error |
| G5 | 预览 PNG ≥1 且存在；pdf 缺→warning；method 如实标注"预览" | error |
| G6 | 每页演讲备注非空 | error |
| G7 | sources 每项带 sha256（缺→warning）；manifest.json 存在（缺→warning） | warning |
| G8 | 结果信封 templates/result_envelope.json 声明字段类型合规 | error/warning 按类型 |

校验命令（独立复核，与 main.py 内嵌同一实现）：

```bash
python scripts/result_tool.py --result <输出>/result.json --out-dir <输出> \
    --case <case.json> --envelope templates/result_envelope.json
# {"valid": true} 且 exit 0 才算通过
```