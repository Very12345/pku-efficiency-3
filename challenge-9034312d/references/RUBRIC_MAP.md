# RUBRIC_MAP.md — 评分维度 → 设计覆盖映射（challenge-9034312d）

题面评分维度共五维（外加 GitHub 5 分）。下表逐维说明本 Skill 的设计如何覆盖，
以及证据具体落在哪个文件/字段，便于评委复核。

## 一、实际效果（40 分）＝ 完成度15 + 正确性15 + 完整性5 + 可核验性5

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 任务完成度 15 | 输入材料 → 直接产出可用的装置图/技术路线图（SVG 分层源文件 + PNG/PDF 预览），不是文字描述或截图 | `scripts/main.py` 全流程；`figure.svg/png/pdf` |
| 结果正确性 15 | 科学实体与连接正确：名称数量对应、接口对应、上下游顺序、箭头方向、标注数值与来源一致；实体/关系全部带 source；断头箭头自动过滤 | `model.py`（source 解析）、`layout.py`（正交连线与方向）、`check.py`（断头箭头、编号连续性）、`result.json.output_contract.element_traceability` |
| 结果完整性 5 | 覆盖六类要素：科学实体（entities）、空间关系（布局 x/y/w/h）、数据编码（kind 类别+配色）、图例标注（legend）、可编辑源文件（SVG）、导出格式（PNG/PDF） | `layout.json`、`figure.svg` 图层、`template/palette.json` |
| 结果可核验性 5 | 图稿/源文件/中间表示/渲染记录全落盘，他人可独立复核与重绘 | `layout.json`（SIR→几何证据）、`result.json`（checksum + change_record + uncertainty + element_traceability） |

## 二、使用增益（25 分）＝ 质量15 + 效率5 + 增益可验证性5

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 质量增益 15 | 结构化中间表示 → 确定性布图（阶段分列、步骤编号、正交箭头、图例映射），相比基础 Agent「画出像却错」显著降低错连/反箭头/编号错位 | `SKILL.md §4` 步骤复核清单（实体/方向/编号/图例四项显式自查） |
| 效率增益 5 | 一键 `python scripts/main.py` 从材料到成图，人工仅需复核修正；`--merge` 支持增量修正免重画 | `SKILL.md §3` 接口；`main.py --merge` |
| 增益可验证性 5 | 同输入复跑确定性一致（无随机）；本地实测记录 | `TEST.md`（实际命令+产物+是否成功）；`README.md` 复跑说明 |

## 三、创新增益（15 分）＝ 新增能力5 + 方法改进5 + 创新证据5

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 新增能力 5 | 从装置清单/方法文本解析「实体—连接—步骤—流向」结构化中间表示（SIR），再据此布图与自检——基础 Agent 或现有绘图方案难以稳定实现 | `model.py`（SIR）、`layout.json` 落盘 |
| 方法改进 5 | 三后端共享同一布局模型（SVG/PIL-PNG/reportlab-PDF 几何一致）；文本解构兜底；`--merge` 人工修正闭环写入 change_record | `layout.py` + `export_*.py`；`scripts/main.py` |
| 创新证据 5 | 边界与价值有文档：适用条件、限制、失败清单、诚实降级规则 | `SKILL.md §2/5/7`、`README.md`、`LAYOUT_SPEC.md` |

## 四、可靠体验（10 分）＝ 调用易用3 + 运行稳定4 + 异常处理3

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 调用与易用性 3 | 单命令从输入走到导出；SKILL.md 给出完整调用步骤；脚本自定位，不依赖 cwd | `SKILL.md §3`；各脚本 `os.path.dirname(__file__)` |
| 运行稳定性 4 | 不同复杂度（10 实体 9 关系示例 / 纯文本装置）重复运行可连续产图；确定性布局无随机 | `TEST.md` 两个案例实测；`layout.py` 确定性算法 |
| 异常处理 3 | 部件参数缺失、工艺歧义、字体缺失、导出失败、画布溢出都有识别与处置 | `SKILL.md §5 异常处理表`；`main.py` 兜底 failed result.json；`fonts.py` 降级 |

## 五、生态贡献（10 分）＝ 文档3 + 复用4 + 分享3

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 文档完整性 3 | 使用说明、输入约定、图元规范、导出参数、示例、限制、维护信息齐全 | `README.md`、`SKILL.md`、`LAYOUT_SPEC.md` |
| 资源可复用性 4 | 图元配色模板（palette.json）、布局规范、SIR 模型、导出脚本均可被他人直接复用 | `templates/palette.json`、`references/LAYOUT_SPEC.md`、`scripts/*` |
| 分享推广价值 3 | 沉淀可分享的图例规范、布局经验与失败清单 | `LAYOUT_SPEC.md`（含失败清单） |

## 加分项：GitHub 公开作品链接（5 分）

- `GITHUB_URL.txt` 第一行：仓库/目录链接（发布代理统一覆写为精确链接）；
- 第二行：相对路径提示（`build/challenge-9034312d/`）。

## 覆盖缺口（诚实声明）

- 图内标注「数值」的数据通道：本 Skill 聚焦实体/关系/流向表达，**不做数值拟合**；
  若材料含可标注原值（如温度、浓度），实体 props 可带，渲染端当前不强标数值注记——这属于明确边界。
- 复杂图的局部放大/跨页：当前未实现局部放大视图，复杂装配图建议在 Inkscape 微调。