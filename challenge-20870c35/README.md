# academic-talk-organizer · challenge-20870c35（学术汇报内容组织 · slides 组）

把**已有**的论文/研究材料组织成：结构清楚、证据可追溯、可编辑、符合听众/时长/模板约束的学术汇报产物。
本包是「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35 的 Skill 交付物；
`SKILL.md` 为 Skill 本体（Agent 加载入口），`scripts/`、`templates/`、`references/`、`examples/`
为运行必需的脚本与资源。

## 一、运行方法

```bash
# 1) 最小调用（示例案例 → 示例输出）
python scripts/main.py --case examples/case.json --out examples/sample-output

# 2) 平台运行期形态（等价于 /input、/app/output）
python3 scripts/main.py --case /input/case.json --task /input/task.md --out /app/output

# 3) 显式指定材料目录 / 模板 / 跳过逐页缩略图
python scripts/main.py --case case.json --out out --materials ./materials \
       --template ./template.pptx --skip-previews

# 4) 独立复核（退出码 0 = 通过）
python scripts/validate_result.py out/result.json
python scripts/check_contract.py out/result.json
```

> 所有脚本用 `os.path.dirname(__file__)` 自定位，运行命令不依赖当前目录；
> 平台把 Skill 装在 `/skills/weekly-skill` 时，把 `scripts/main.py` 换成
> `"$SKILL_ROOT/scripts/main.py"` 即可（`SKILL_ROOT`= 含 SKILL.md 的目录）。

## 二、输入输出

**输入**：`case.json`（case_id / report_goal / audience / duration_min / slide_count /
report_type / materials / template·start_deck / figure_files / output_contract）+ `task.md` + 材料
（md/txt/PDF 与图片）。脚本**实际读取文件**，不按标签预设内容；材料目录缺省为 `<case 目录>/materials`。

**输出**（`result.json`、`talk_plan.json`、`evidence_map.json`、`editable_deck.pptx`、
`previews/`（封面/逐页/网格 PNG + manifest）、`self_check.json`），契约见
`references/OUTPUT_CONTRACT.md`。

## 三、依赖

| 依赖 | 用途 | 版本要求 |
|-|-|-|
| Python | 解释器 | ≥ 3.8（本机验证 3.13.9） |
| python-pptx | 可编辑 .pptx 生成/模板适配 | 1.0.2（验证） |
| Pillow | PNG 预览渲染 | 12.x（验证；≥8 支持 anchor 参数） |
| pypdf（可选） | PDF 文本抽取 | 6.x（验证）；缺失时如实降级为「未解析」 |
| reportlab（仅示例生成） | 生成本包示例 PDF | 5.0（本机验证，非运行必需） |

无网络依赖、无 cwd 依赖、不调用 LibreOffice/PowerPoint（预览为 PIL 模拟，如实标注）。

## 四、限制与诚实约定

- **预览是 PIL 模拟**，非 Office 真实栅格化：每张 PNG 带「PIL 模拟预览 · 非 Office 渲染」水印，
  `previews/preview_manifest.json` 说明限制；正式视觉以 .pptx 在 PowerPoint/LibreOffice 打开为准。
- **PDF 仅文本抽取代理**（pypdf）：布局/图表不恢复，且无 pypdf 时按未解析降级，绝不猜内容。
- **无图时是占位框**，不是伪图；**一页一主张**来自源材料逐字引文，证据强度自动分级，
  数字一致性由 validate_result 以警告提示人工复核。
- 不提交预制答案：`examples/` 仅为接口演示（`"sample": true`），正式案例由平台在运行期提供。

## 五、失败处理

| 症状 | 处理 |
|-|-|
| 退出码 1（自检 errors） | 读 `self_check.json → validate.errors`，按提示修复后重跑 |
| status=partial | 逐条读 `uncertainty`：材料缺失→补材料；PDF 无解析→装 pypdf 或用文本版；预览失败→重跑渲染 |
| status=failed | `change_records` 有 deck 异常，重跑并给 `--template` 或检查材料路径 |
| 超时/预算 | 中间产物（talk_plan/editable_deck/result）已尽早落盘，可直接作为部分交付 |

## 六、目录结构

```
SKILL.md               Skill 本体（frontmatter + 步骤/异常/自查）
scripts/               main·evidence·planner·deck_builder·render·validate_result·check_contract·common
templates/             talk_config.json（可编辑叙事规则）+ narrative_template.md
references/            OUTPUT_CONTRACT.md · RUBRIC_MAP.md（五维→覆盖）· METHODS.md
examples/              最小 case.json + task.md + 材料 + sample-output（示例，非正式案例）
README.md / TEST.md / GITHUB_URL.txt
```

更多细节：`templates/narrative_template.md`（叙事模板）、`references/METHODS.md`（方法）、
`references/RUBRIC_MAP.md`（评分对照）、`SKILL.md`（完整调用协议）。