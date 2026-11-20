# RUBRIC_MAP.md — 评分五维 → 本 Skill v2 设计覆盖（challenge-9034312d）

题面评分维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
生态贡献 10 · GitHub 公开链接 +5**。下表逐维说明本 Skill v2 的设计覆盖与
**可核验证据落点**（证据路径相对 Skill 根；文字自述不替代实际运行证据）。

## 1. 实际效果（40 分）＝ 完成度15 + 正确性15 + 完整性5 + 可核验性5

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 任务完成度 15 | 输入材料 → 直接产出可用的装置图/技术路线图：**可编辑分层 SVG 源文件 + PNG/PDF 渲染件 + evidence/layout 中间表示**，不是文字描述或截图；三个图类（route/apparatus/flow/hybrid）自动选布局模板 | `scripts/main.py` 一键流水线；`examples/output/*/figure.{svg,png,pdf}` |
| 结果正确性 15 | 实体名称与数量、接口对应、上下游顺序、箭头方向、标注与来源一致：**证据先行**（每条实体/关系带 locator+quote）→ **连接规则审计**（assets/connection_rules.json 机器检查类别词表/方向/语义）→ 断头箭头自动过滤并记录 | `scripts/gain_evidence.py`（证据链）；`scripts/svg_verify.py`（规则审计）；`result.json.evidence/verify` |
| 结果完整性 5 | 覆盖题面六类要素：科学实体（entities）、空间关系（layout x/y/w/h）、数据编码（kind→形状/配色）、图例标注（legend↔kind 自动一致）、可编辑源文件（分层 SVG）、导出格式（PNG/PDF） | `layout.json`；`figure.svg` 五层 `layer:*`；`templates/palette.json` |
| 结果可核验性 5 | 图稿/源文件/证据清单/布局模型/校验报告全落盘，他人可独立复核与重绘；确定性探针 spec_sha16 证明同输入同布局 | `evidence.json` + `layout.json` + `verify_report.json` + `result.json`（checksum/change_record/uncertainty） |

## 2. 使用增益（25 分）＝ 质量15 + 效率5 + 增益可验证性5

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 质量增益 15 | 相对基础 Agent「画得像却错」：①实体全部 source-bound（evidence）②连接规则机器审计（类别/方向/语义）③步骤编号与正文逐条对照（G8）④图例↔图元一致（G9）⑤布局确定性 | `scripts/svg_verify.py`；`SKILL.md §4`；`TEST.md` 实测 |
| 效率增益 5 | 一键 `python scripts/main.py` 从材料到成图；`--merge` 增量修正免重画（编辑既有图稿）；重复运行零人工干预 | `README.md`；`main.py --merge/--material/--figure-type` |
| 增益可验证性 5 | 同输入复跑确定性一致（无随机）；TEST.md 记录两次运行 sha256 对比；check.py G1–G10 全部可执行 | `TEST.md`（双跑 sha）；`scripts/check.py` |

## 3. 创新增益（15 分）＝ 新增能力5 + 方法改进5 + 创新证据5

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 新增能力 5 | 从装置清单/工艺描述解析「实体—连接—步骤—流向」结构化中间表示（SIR）→ 再据其布图与自检；**证据先行**（gain_evidence）+ **连接规则资产驱动审计**（connection_rules.json 可扩展）双创新 | `scripts/model.py`（SIR）；`scripts/gain_evidence.py`；`assets/connection_rules.json` |
| 方法改进 5 | ①三后端共享同一布局模型（SVG/PIL/reportlab 几何一致）②获取素材即校验（svg_verify 内置在流水线）③确定性探针（同输入同布局可复现）④`--merge` 编辑闭环写入 change_record | `scripts/layout.py`+`render_svg.py`+`export_preview.py`；`verify_report.json.determinism` |
| 创新证据 5 | 边界与价值文档化：与现有绘图方案的差异（可编辑源+溯源+机器校验）、适用条件、限制、失败清单 | `README.md`、`references/figure-blueprint.md`、`references/failure-modes.md` |

## 4. 可靠体验（10 分）＝ 调用易用3 + 运行稳定4 + 异常处理3

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 调用与易用性 3 | 单命令从输入走到导出；SKILL.md 完整调用步骤；脚本自定位（os.path.dirname(__file__)），任何 cwd 可运行 | `SKILL.md §3`；各脚本头部 |
| 运行稳定性 4 | 不同装置复杂度/不同路线结构/纯文本材料均可连续产图（结构化/文本解构双路径）；布局确定性无随机；规则资产缺失时静默降级 | `TEST.md` 多案例实测；`main.py` 兜底 failed result.json |
| 异常处理 3 | 输入缺失/材料歧义/接口冲突/字体缺失/导出失败/画布溢出/规则违规均有识别与处置（D1–D12 决策规则 + 异常表），error 级违规强制 status=partial | `SKILL.md §5`；`references/failure-modes.md`；`main.py`/`check.py` |

## 5. 生态贡献（10 分）＝ 文档3 + 复用4 + 分享3

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 文档完整性 3 | 使用说明、输入约定、图元规范、导出参数、示例、限制、维护信息齐全（SKILL/README/TEST/5 份 references/2 份 templates） | 全部文档 |
| 资源可复用性 4 | **connection_rules.json（连接规则字典）**、palette.json（图元配色）、component-connection-checklist + entity-relation-checklist（核对模板）、result_example.json（结果形态示例）、SIR 模型与导出脚本均可直接复用或扩展 | `assets/`、`templates/`、`scripts/*` |
| 分享推广价值 3 | 沉淀可分享的图例规范、布局经验、连接规则、失败清单；GITHUB_URL.txt 提供公开作品入口 | `references/figure-blueprint.md`、`references/failure-modes.md`、`GITHUB_URL.txt` |

## 6. GitHub 公开作品链接（+5 分）

- `GITHUB_URL.txt` 第一行：公开仓库链接（发布代理统一覆写为精确链接）；
- 第二行：相对路径提示 `target/challenge-9034312d-v2/`。

## 7. 覆盖缺口（诚实声明）

- 图内标注「数值」（温度/浓度等原值注记）：材料含可标注原值时实体 props 可带，
  渲染端当前不强标数值注记——属明确边界（本 Skill 聚焦装置/流程/路线表达，不做数值拟合）；
- 复杂装配图的局部放大视图未内置：建议在 Inkscape 微调源文件并如实记录 manual-edit；
- 装置图深度（多级装配/嵌套接口）：三桶布局可表达单层装配，深层结构需 Agent
  拆分画布或增补 stage 列（限制见 failure-modes.md）。