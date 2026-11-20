# scientific-schematic-editor

科研示意图生成与编辑 Skill 包（challenge-98e5a474 · 玻尔产品周赛 · 北大
专区 · 学术效率第三期 · figures 组）。

把来源材料（论文图注/正文摘录/Markdown/CSV）变成：
**可编辑分层 SVG 源文件 + PNG/PDF（/TIFF/EPS）导出件 + 结构化 result.json**，
全程带实体—关系溯源、图例/数据映射一致性与导出合规检查。

## 目录结构

```
challenge-98e5a474/
├── SKILL.md                 # Skill 本体（YAML frontmatter + 执行步骤 + 异常处理 + 自查清单）
├── README.md                # 本文档
├── GITHUB_URL.txt           # GitHub 公开作品链接（第一行占位，发布代理覆写）
├── TEST.md                  # 本地实测记录（命令 / 产物 / 结论 / 限制）
├── scripts/                 # 可运行脚本（自定位，不依赖 cwd）
│   ├── main.py              #   流水线入口
│   ├── manifest.py          #   ER 清单：加载/规范化/校验/词表
│   ├── layout.py            #   布局引擎（SVG 与预览共用）
│   ├── svgbuilder.py        #   手写分层可编辑 SVG
│   ├── render.py            #   matplotlib 镜像预览 + 图表渲染
│   ├── checks.py            #   溯源/图例/数据映射/导出预检
│   ├── edit.py              #   源文件级增量编辑（内嵌清单）
│   ├── validate_result.py   #   result.json 契约校验
│   └── selftest.py          #   23 项逻辑自测
├── references/
│   ├── ER_MANIFEST.md       # 实体—关系清单规范（提取/绘图唯一数据源）
│   ├── OUTPUT_CONTRACT.md   # result.json 契约
│   └── RUBRIC_MAP.md        # 五维评分 → 设计覆盖
└── examples/                # 最小示例（示例，非正式案例）
    ├── case.json            #   schematic 示例
    ├── case_chart.json      #   chart 示例
    ├── case_edit.json       #   源文件级编辑示例
    ├── task.md              #   示例任务书
    ├── sources/             #   合成演示材料
    └── output/              #   示例产物（已生成，标注"示例"）
```

## 依赖与安装

- Python 3.9+（本机实测 3.13.9 / Anaconda）
- `matplotlib`（渲染预览、图表）、`Pillow`（位图检查）、`numpy`（heatmap）
- 其余（SVG 生成、清单、检查、契约）仅 Python 标准库
- 无需 cairosvg / svgwrite / PowerPoint / LibreOffice；无这些工具时的
  行为已在 TEST.md 中如实记录（预览=同一 layout 的 matplotlib 镜像）

```bash
pip install matplotlib pillow numpy   # 若尚未安装
```

## 运行方法（三条真实链路）

```bash
# 1) schematic（机制/通路/流程示意图）
python <skill_root>/scripts/main.py \
    --case <skill_root>/examples/case.json \
    --out /app/output                  # 或任意目录

# 2) chart（数据表驱动图表，图例由表生成）
python <skill_root>/scripts/main.py \
    --case <skill_root>/examples/case_chart.json \
    --out /app/output-chart

# 3) 源文件级编辑（对已有 figure.svg 增量修改）
python <skill_root>/scripts/main.py \
    --case <skill_root>/examples/case_edit.json \
    --edit-svg /app/output/figure.svg \
    --out /app/output-edited

# 契约校验
python <skill_root>/scripts/validate_result.py \
    --case <skill_root>/examples/case.json \
    --result /app/output/result.json
```

正式案例：`--case /input/case.json`（Agent 先在 /app/work/entities.json
抽取 ER 清单），`--out /app/output`。更多参数见 `python main.py --help`：
`--manifest`（显式清单）、`--work`（工作区）、`--base-name`、
`--exports png,pdf,svg,tiff,eps`、`--dpi`（默认 300）、`--skip-checks`。

## 关键方法（一句话）

1. **ER 清单 = 图稿数据库**：图里每个实体/关系/图例条目都挂
   `source + evidence`，方向语义按材料原文映射到 7 种规范化箭头
   （激活/抑制/招募/转录/因果/包含等），映射不上的关系显式标 fail；
2. **数据驱动重绘**：改清单/数据表 → 重跑同一条命令，图例、颜色、
   布局、导出全部同步更新，"改动数据后图能同步更新"由构造保证；
3. **可编辑源文件**：手写分层 SVG（`<text>` 文字、`layer-*` 分层、
   `id`/`data-*` 溯源属性、内嵌 ER 清单）；图表 SVG 用
   `matplotlib rcParams["svg.fonttype"]="none"` 保住真实文字；
4. **源根编辑**：figure.svg 内嵌清单 → 下次编辑无需重新抽取材料，
   未改元素保持原样，动作记入 `change_records`；
5. **画图即核验**：溯源比例、图例双向一致、数据映射、DPI/色彩/文字
   可编辑性全部自动检查并写入 result.json `verification.checks`。

## 限制与失败处理

| 限制/失败 | 行为 |
|-|-|
| 无 cairosvg/svgwrite | PNG/PDF 预览 = 同一 layout+manifest 的 matplotlib 镜像（语义一致，非逐像素），写入 uncertainty |
| 无 CJK 字体 | 自动探测微软雅黑/SimHei/Noto CJK；仍缺失则 PNG 预览可能缺字（SVG 文字不受影响），写入 uncertainty |
| PDF 字体审计 | 尽力而为（Type3/FontFile 计数），完整审计缺失如实标注 warn |
| 材料缺失/矛盾 | 记录到 sources/uncertainty；方向冲突以材料原文为准并双写说明 |
| 渲染/导出异常 | 捕获并写出 status=failed 的 result.json（含 pipeline fail 明细），工作不丢失 |
| 无清单且无数据 | 明确停止——不画无来源依据的图（宁缺毋滥） |

## 验收自检

1. `python scripts/selftest.py` → 23 项全 PASS；
2. 任一路径 `main.py` 退出码 0 且生成 figure.svg/png/pdf + result.json；
3. `validate_result.py` 输出 VALID（退出码 0）。

## 维护与边界

- 词表（关系动词→箭头）扩充在 `scripts/manifest.py` 的
  `CANONICAL_KINDS`；新箭头样式在 `scripts/svgbuilder.py` 的
  `EDGE_STYLES`；
- 布局族扩展在 `scripts/layout.py`（layered/hierarchy/cycle/manual）；
- 本包 ≤50 个文本文件、单文件 ≤500KB、总 ≤2MB、无符号链接；
- 示例产物标注"示例，非正式案例"，不可冒充正式结果。