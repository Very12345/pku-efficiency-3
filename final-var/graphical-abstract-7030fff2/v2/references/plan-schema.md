# plan-schema.md — 设计方案 schema（方案先行，v2）

> 高分意图：**先出设计方案，再动笔**（75112 唯一同时带 plan-schema 与 rubric-map；
> 84402 的 spec_template.json 也是"规格先行"）。本文件定义"设计方案 plan.json"
> 的结构与使用流程。

## 1. 为什么先出方案

图形摘要的失败大多发生在动笔之前：实体张冠李戴、数值无源、面板缺要素、图例与数据
失联。方案先行把"画什么、表达什么、证据在哪"固化成可 lint 的中间产物，让
`scripts/spec_lint.py`（lint_plan）在**绘制前**就拦住这些问题。

## 2. plan.json schema（`scripts/scaffold.py` 生成骨架，Agent 定稿）

```jsonc
{
  "schema": "plan-schema/v2",
  "case_id": "与 case.json 一致",
  "title": "图题",

  // 四要素：每个面板一句话说明"这一面板表达什么"（不能空）
  "four_elements": {
    "question":   "一句话：研究问题（缺省待 Agent 填充）",
    "method":     "一句话：方法/机制",
    "results":    "一句话：核心结果",
    "conclusion": "一句话：结论与意义"
  },

  // 科学实体（必须带 src：材料定位）
  "entities": [ { "name": "DOX（阿霉素）", "type": "molecule", "panel": "method",
                  "src": "material.md:12", "note": "化疗药物" } ],

  // 关系（方向与正负由材料决定；抑制=negative）
  "relations": [ { "from": "mPEG-PLA 胶束", "to": "DOX（阿霉素）", "label": "自组装包载",
                   "kind": "positive", "src": "material.md:18" } ],

  // 数据（value 必须能在材料中定位；kind ∈ bar_length|color_scale|area|value_label）
  "data": [ { "label": "粒径", "value": 95, "unit": "nm", "kind": "bar_length",
              "src": "case.json[data]" } ],

  // 图面约束（覆盖 case 的同名字段）
  "figure_constraints": {
    "width": 1200, "height": 800, "dpi": 300, "colorblind": true,
    "flow_arrows": true, "raster_scale": 2, "pdf": true, "language": "zh"
  },

  "panels_hint": { "question": ["要点1", "要点2"], "method": [], "results": [], "conclusion": [] },
  "plan_source": "scaffold | agent-plan",
  "skill_version": "2.0.0",
  "skeleton": true            // true = 仍待定稿；正式运行应为 false
}
```

## 3. 方案 lint（CP1，绘制前必跑）

```bash
# CP1 门：方案 lint（退出码即判据：0 = 通过；1 = 有 problems）
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan plan.json
# 等价写法：python "$SKILL_DIR/scripts/spec_lint.py" --plan plan.json
# 校验点：four_elements 四面板非空；entities/relations/data 逐项带 src；
#         画布尺寸在 [600,4000] 夹紧范围；plan_hash 稳定（确定性探针）
```

`main.py --plan plan.json` 会把 plan 的图面约束作为设计覆盖（plan 赢，但内容仍
来自真实材料），并把方案 lint 结果写进 `result.plan.lint`。

## 4. 使用流程

1. `python "$SKILL_DIR/scripts/scaffold.py" --case <case.json> --out plan.json`（真实抽取实体/关系/数据，
   附来源定位）；
2. Agent 阅读材料后填充 `four_elements`（一句话/面板）、必要时修剪实体/数据（哪些上图、
   哪些只进图注）、定稿 `figure_constraints`；
3. 方案 lint 通过后：`python "$SKILL_DIR/scripts/main.py" --case <case.json> --plan plan.json --out <out>`；
4. 绘制后 `spec_lint.lint(spec)` 再核一遍最终图面规格（CP1b），问题进
   `result.spec_lint` 与 `uncertainty`，status 不允许在 lint 有问题时标 success。

## 5. 与 templates/资产的对应

- 空骨架模板见 `assets/spec_template.json`（可直接复制为新案例的 plan 起点）；
- 期望结果形态见 `assets/result_example.json`（说明 result.json 该长什么样）；
- 材料样例见 `assets/example_material.txt`（演示 "实体/数据必须能在材料中找到" 的写法）。