# RUBRIC_MAP.md — 五维评分 → v2 设计覆盖对照

本题评分维度（实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
生态贡献 10，另加 GitHub 公开链接 5）。本表把每个评分点映射到 v2 作品内的
具体设计与**可复跑证据**（TEST.md / examples/output / COMPARE.md）。
原则：自述不算证据，全部用可复跑命令与产出文件对照。

## 实际效果（40）

| 评分点 | v2 覆盖 | 证据位置 |
|-|-|-|
| 任务完成度 15 | 读实际 case 文件 → 抽取主线 → 页序+页级叙事角色（slide_text.alloc_roles）→ 生成可编辑 PPTX + 每页演讲备注 + 预览渲染；页数与页序由 `spec.max_slides` 决定并记录在 `deck.slides[].role`。 | `scripts/main.py`、`scripts/slide_text.py`、`scripts/deck_tool.py` |
| 结果正确性 15 | 页面上每个数字与材料交叉核验（`evidence_check.check_claim_numbers`），找不到的数字进 `evidence.unverified_claims` 且不当作正确数据；图表只重绘自真实数据表；位图无数据只做诚实占位；编辑引入的新数字同样再核验。 | `scripts/evidence_check.py`、`scripts/deck_tool.py build_chart/bind_figures`、OUTPUT_CONTRACT §4 |
| 结果完整性 5 | 六类要素全覆盖：主线（overview）、页结构（roles）、图表引用（figure.ref + evidence footer）、讲解逻辑（notes 与文字分离）、模板约束（三级模板来源）、导出渲染（PNG+PDF 预览）。 | `result.json deck.slides` / `previews`；DECK_SPEC.md |
| 结果可核验性 5 | `sources[].sha256` 对拍输入；`manifest.json` 对拍全部产出；`evidence_map.md` + `evidence_map.json` 双形态逐页映射；`changelog.jsonl` 版本记录；CP4 G1–G8 硬性门（result_tool + selftest）。 | `scripts/result_tool.py`、`scripts/selftest.py`、OUTPUT_CONTRACT §8 |

## 使用增益（25）

| 评分点 | v2 覆盖 | 证据位置 |
|-|-|-|
| 质量增益 15 | 与"基础 Agent 整段塞页"对照：每页一个叙事角色、≤7 条要点、数字核验、字号自动收敛不溢出、证据脚注每页可见、图表可编辑（重绘图/原生表格）；CP2 plan_lint 把页面纪律变成可执行门。 | `deck_tool._fit_size`、`evidence_check.plan_lint`、TEST.md 对照记录 |
| 效率增益 5 | `--edit` 局部修改（改一条主张/加备注/重排页序/换图表）不用全稿重做；`--version` 归档历史版本，回退=复制旧版重跑；EDIT_OPS.md 编辑决策树让回放 Agent 知道"改什么用什么操作"。 | `deck_tool.apply_edits`、`references/EDIT_OPS.md` |
| 增益可验证性 5 | 同一 case 用基础流程与本 Skill 各跑一次并逐页 diff；`--no-chart` 降级开关与 `--max-slides` 保证可比条件；双跑确定性记录在 TEST.md。 | `TEST.md`、`examples/README.md` |

## 创新增益（15）

| 评分点 | v2 覆盖 | 证据位置 |
|-|-|-|
| 新增能力 5 | 页序规划（roles 分配器）+ 页级主张的证据绑定（每页 evidence footer / notes）+ 图表-数据绑定（表→重绘图或原生可编辑表格）+ 局部编辑与版本回退（--edit + deck_<v>.pptx）+ 双形态证据映射（md+json 机器可读）。基础 Agent 没有这些可复现能力。 | `slide_text.py`、`deck_tool.py`、`result_tool.py` |
| 方法改进 5 | 确定性内容取舍规则（方法≤4 条、结果表→2 条量化主张、无表才回落散文）；数字核验器（claim↔material，编辑链路同样生效）；模板槽位约束数据驱动（不写死字号颜色）；CP1–CP4 检查点把"读材料→规划→构建→验证"四个动作显式化。 | `slide_text.py`、`evidence_check.py`、`templates/default.json` |
| 创新证据 5 | 相对题面"常见失败清单"逐条给机制：整段塞页→要点上限+plan_lint；抄错数字→数字核验器；占位图/凭空曲线→仅重绘真实数据表；模板被覆盖→外部模板只填槽位+三级来源；改一页坏全稿→局部编辑+版本归档；导出字体/溢出→_fit_size+render QA+诚实标注预览。 | 本表各列 + DECK_SPEC.md + TEST.md |

## 可靠体验（10）

| 评分点 | v2 覆盖 | 证据位置 |
|-|-|-|
| 调用与易用性 3 | 单条命令 `python scripts/main.py --case … --out …`；SKILL.md 写明调用方式、输入输出、D1–D12 决策规则、异常表；脚本全部 `os.path.dirname(__file__)` 自定位，任意 cwd 可跑。 | `SKILL.md`、`README.md` |
| 运行稳定性 4 | 不同材料形态（md/txt/csv/html/PDF 兜底）、不同页数（3–20）、不同模板（default / template_pptx / starting_deck）持续产出；每步独立 try/except + 先存部分产物；`--no-chart`、缺 reportlab、缺 CJK 字体等降级路径全部记录。 | `main.py`、`deck_extract.py`、`deck_tool.py`、`render_qa.py` |
| 异常处理 3 | D1 材料缺失→minimal result；D2 PDF 加密→如实说明；D3 扫描件→标注图像型 PDF；D5 位图无数据→诚实占位；D6 模板损坏/占位符不足→内置模板回退；D7 页数超限→压缩记录；D8 字体缺失→回落+预警；D9 图表重绘失败→原生表格；D10 契约字段无值→四形态空值；D12 超预算→先存部分产物。 | `SKILL.md` §5 决策表、各脚本 except 分支 |

## 生态贡献（10）

| 评分点 | v2 覆盖 | 证据位置 |
|-|-|-|
| 文档完整性 3 | README（运行/依赖/限制/失败处理）、OUTPUT_CONTRACT（含 G1–G8）、RUBRIC_MAP、EDIT_OPS（编辑操作目录）、DECK_SPEC（蓝图+槽位）、TEST（实测记录）、COMPARE（三方对照）、examples/README + output 示意。 | 根目录与 references/ |
| 资源可复用性 4 | 模板 spec 参数化（templates/default.json）；结果信封声明（templates/result_envelope.json）可被任何验证器复用；脚本四层职责（extract/build/render/verify）模块化；数据表→原生 PPTX 表格无需 matplotlib；最小示例整体可复制运行。 | `templates/`、`scripts/`、`examples/` |
| 分享推广价值 3 | 沉淀"学术汇报页面骨架方法"：roles 分配规则、证据脚注约定、编辑操作目录、版本记录格式、双形态证据映射，均可迁移到其他汇报工具；示例案例标注"示例，非正式案例"。 | `slide_text.py`、`EDIT_OPS.md`、`examples/` |

## GitHub 公开链接（5，额外分）

`GITHUB_URL.txt` 第一行为公开仓库链接，第二行为作品相对路径；评审无需登录
即可打开并定位本作品。

## 对照建议（评审复跑）

1. 基础 Agent：给同一 case 直接让它做 PPT（不加载本 Skill）。
2. 本 Skill：按 SKILL.md 运行 `scripts/main.py --case … --out …`。
3. 对比 `deck.slides` 的 roles、verified 比例、备注、模板约束命中、
   `result_tool.py` G 门通过率；逐页 diff 方法见 TEST.md。