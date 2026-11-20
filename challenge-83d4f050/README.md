# README.md —— 生物机制图与通路图 Skill 包

挑战：`challenge-83d4f050`（生物机制图与通路图 · figures 组，学术效率第三期）。
类型：Skill 创作题——平台加载本 Skill 后，用 DeepSeek Harness 在 3 个固定案例上运行，
自动判分（实际效果 40 / 使用增益 25 / 创新增益 15 / 可靠体验 10 / 生态贡献 10，另有
GitHub 公开链接 5 分）。

## 1. 这是什么

把科研机制/通路材料（文本、表格、PDF 中的通路描述、基因-蛋白-化合物关系）变成：

- **可编辑分层 SVG 源文件**（`diagram.svg`）：图层分组、元素带 data-id/data-type/data-source，
  改一个标签即可重新导出；
- **PNG/PDF 预览**（`diagram.png` / `diagram.pdf`）：同一布局引擎渲染，与源文件一致；
- **契约化 result.json**：case_id、deliverables、scientific_content（实体/边/图例/布局）、
  来源、uncertainty、change_records、export_checks、self_check。
- 每个实体/边带来源（材料文件+行号），图例与图面颜色/线宽逐值自洽，5 类箭头语义
  （激活/抑制/结合/修饰/转运）由材料动词映射，区室按 胞外→膜→胞质→核 分层布局。

## 2. 目录结构

```
SKILL.md                    # Skill 定义（frontmatter + 完整执行说明）
README.md                   # 本文件
TEST.md                     # 本机实测记录（命令/产物/结论）
GITHUB_URL.txt              # GitHub 公开作品链接（占位，发布时覆写）
references/
  OUTPUT_CONTRACT.md        # result.json 字段契约（机器校验基准）
  RUBRIC_MAP.md             # 五维评分 → 设计覆盖映射
  DIAGRAM_SPEC.md           # 绘图规范（形状/箭头/区室/命名/导出参数/校验规则）
scripts/
  main.py                   # 入口：读 case → 建模 → 布局 → SVG/PNG/PDF → 校验 → result.json
  model.py                  # 数据模型 + 样式常量表（改风格只改这里）
  extract.py                # 结构化材料草稿抽取器（表格/动词/数据映射）
  layout.py                 # 确定性区室布局 + 正交边路由（反馈右侧绕行）
  svg_backend.py            # 可编辑分层 SVG 生成 + well-formed 检查
  mpl_backend.py            # matplotlib PNG/PDF 预览（可选依赖，缺失自动降级）
  validate.py               # 独立校验器（M/T/L/D/S/F 检查族）
  result_writer.py          # result.json 契约生成 + output_contract 合并
examples/
  case.json                 # 最小示例输入（标注 示例，非正式案例）
  materials/example_material.md
  output/                   # 示例输出（result.json/diagram.svg/png/pdf/model.json）
```

## 3. 运行方法

依赖：Python ≥3.8 标准库（必）；matplotlib ≥3.5（选，用于 PNG/PDF 预览；缺失时 SVG
仍可生成，status 记 partial 并写明原因）。

**平台运行时（容器）**
```bash
cd /skills/weekly-skill                      # 脚本自定位，不依赖 cwd
python3 scripts/main.py --case /input/case.json --out /app/output
# 材料若为 PDF/散文，先由 agent 读取并建模：
#   python3 scripts/main.py --model-file /app/work/model.json \
#     --case /input/case.json --out /app/output
```

**本地演示**
```bash
python scripts/main.py --case examples/case.json --out examples/output --verbose
```

**CLI 参数**
| 参数 | 默认 | 说明 |
|---|---|---|
| `--case` | /input/case.json → examples/case.json | case.json 路径 |
| `--task` | /input/task.md | task.md 路径 |
| `--out` | $TASK_OUTPUT → `<case目录>/output` | 输出目录 |
| `--materials-dir` | 由 case.json `materials` 提供 | 材料目录（可重复） |
| `--model-file` | 无（自动草稿抽取） | 人工核验后的 model.json |
| `--formats` | svg,png,pdf | 导出格式 |
| `--dpi` | 150 | 预览分辨率 |

## 4. 失败处理

| 现象 | 原因 | 处置 |
|---|---|---|
| `failed` 且无 SVG | 材料无可解析实体/关系 | Agent 读材料手工建 model.json 后用 `--model-file` |
| 有 SVG、无 PNG/PDF | matplotlib 不可用 | 记录 partial + export_checks 说明；SVG 仍是有效源文件 |
| `partial`（checks 有 fail） | 实体/边缺来源、图例不一致等 | 按 self_check.failures 逐项修复 model.json 后重跑 |
| 中文成方框（预览） | 容器无中文字体 | 告警写进 export_checks；SVG 字体栈由查看端决定，不受影响 |

## 5. 限制

- 不解析 PDF 内部布局（无第三方 PDF 依赖设计）；PDF 材料由 Agent 抽文本后再走本管线。
- 自动抽取只覆盖结构化语句；散文材料依赖人工核验（SKILL.md 步骤 2，准确优先设计）。
- 位图编辑（直接在 PNG 上改）不在范围内——本包的设计是“改源文件（SVG/model.json）再导出”。

## 6. 自查与验证

`scripts/validate.py` 提供机器校验（实体 id/端点/来源/图例覆盖/箭头语义/颜色自洽/方向/
产物/契约），`main.py` 每次运行末自动执行并写入 result.json `self_check`。
验收示例：`python scripts/main.py --case examples/case.json --out <tmp>` 应输出
`status=success, failures=0` 且产物齐全（见 TEST.md）。

## 7. 维护与分享

- 改风格：`scripts/model.py` 顶部的 NODE_TYPES / EDGE_TYPES / COMPARTMENT_DEFAULT /
  data_mapping（全图与图例自动同步）。
- 增类型：在 model.py 加样式 + 词表，validate.py 自动纳入 L01/L02 校验。
- 公开链接：`GITHUB_URL.txt` 首行仓库地址、次行作品相对路径（发布代理覆写）。