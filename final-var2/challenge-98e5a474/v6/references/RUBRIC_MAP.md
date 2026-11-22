# RUBRIC_MAP — 五维评分 → 本包文件/机制（v6 · 全维合并版）

官方题面维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**，
外加 **GitHub 公开作品链接 5 分**（`GITHUB_URL.txt`）。

本包是 **union 包**：把五条强化轴合并到同一套脚本与文档上，因此本表不只列"落到
哪个文件"，还标出每一栏由**哪条轴的实测证据**支撑：

| 轴 | 来源 | 主要证据文件 |
|-|-|-|
| 决策显性化（D1–D16 / L0–L3） | 决策系统版 | `SKILL.md` §4、`references/failure-modes.md` |
| 增益可验证（I1–I10 / F1–F8） | 增益可验证版 | `references/GAIN-PROTOCOL.md`、`TEST.md` |
| 机制显性（M1–M5）+ 复用（A1–A12） | 机制显性版 | `references/MECHANISM.md`、`references/REUSABLE-ASSETS.md` |
| 失败注入（四形态 × 25 条） | 失败注入版 | `references/FAULT-MATRIX.md`、`scripts/fault_inject.py` |
| 多案例泛化（5 案 + 5 探针） | 题集版 | `references/CASE-SET.md`、`scripts/case_probe.py` |

---

## 1. 实际效果 40 分

| 评分点 | 分 | 本包机制 | 落到哪个文件 / 哪条实测 |
|-|-|-|-|
| 任务完成度 | 15 | 完整"材料 → 图稿 → 导出"链路一条命令跑通；**五个案例**（含两个新题材：细胞生物学机制图、转录组热图）现场跑出真实产物 | `scripts/main.py`、`scripts/case_probe.py`、`references/CASE-SET.md` §3 |
| 结果正确性 | 15 | ①每个实体/关系带 `source`+`evidence`（实测 100%）；②**M1** 拦未知 kind（`spec.relation_kind` fail）；③**M1** 强制 containment 用分组（`spec.containment_group` fail，实测题集 B5）；④图例↔图面双向一致；⑤chart 表外类别 = G8 INVALID | `scripts/spec_lint.py`、`scripts/checks.py`、`scripts/validate_result.py`、`references/FAULT-MATRIX.md` §3.2 |
| 结果完整性 | 5 | 三类产物由 `artifact.<role>` 逐类核验（题集把 `roles` 设为常驻判据）；SVG 语义图层 + `<title>`；图面要素（分组框、图例、单位轴、来源脚注）齐备 | `scripts/svgbuilder.py`、`scripts/layout.py`、`scripts/checks.py` |
| 结果可核验性 | 5 | **M2** 让图稿自描述（内嵌清单 + `data-*`）；G1–G8 第三方可复跑；`determinism.spec_sha16` 双跑探针；**`case-report.json` 把"期望/实测/是否满足"逐条落盘** | `scripts/checks.py`、`scripts/validate_result.py`、`scripts/case_probe.py`、`references/CHECK-INDEX.md` |

## 2. 使用增益 25 分

| 评分点 | 分 | 本包机制 | 落到哪个文件 / 哪条实测 |
|-|-|-|-|
| 质量增益 | 15 | 三层门每次运行自动执行（**M1** 生成前 → **M4** 产物后 → 契约门）；失败不静默（25 条注入实测：0 条静默失败）；**画布预算规则**把"图被裁"这类返工前置到绘图之前 | `scripts/spec_lint.py`、`scripts/checks.py`、`references/MECHANISM.md` §M1/§M4、`references/CASE-SET.md` §5 |
| 效率增益 | 5 | 素材→图稿一条命令；改数据只改清单即重绘（实测 SVG sha 变化）；**M2** 让编辑走内嵌清单增量改；**M3** 让"没装 PDF 库"不再阻塞整轮（实测 stdlib 回退抽到 15 字） | `scripts/main.py`、`scripts/edit.py`、`scripts/pdftext.py`、`references/FAULT-MATRIX.md` §3.3 |
| 增益可验证性 | 5 | 对照协议 **F1–F8** 条款 + 指标 **I1–I10** + 真实读数 **R1–R13**，并**明确写出哪些指标未测量**；`TEST.md` 按轴取证；`doccheck.py` 保证判据不漂移 | `references/GAIN-PROTOCOL.md`、`TEST.md`、`scripts/doccheck.py` |

## 3. 创新增益 15 分（本包主战场：五个具名机制 + 两套"会自己找错"的工具）

| 评分点 | 分 | 本包机制 | 落到哪个文件 / 哪条实测 |
|-|-|-|-|
| 新增能力 | 5 | ①**M2 源文件自描述**（ER 清单内嵌 SVG ⇒ 可增量编辑，不是重画）②**可运行的失败注入器**（四形态 × 25 条，只动包外副本）③**可运行的题集执行器**（逐案真跑 + 对区间 + 边界探针） | `scripts/svgbuilder.py`、`scripts/fault_inject.py`、`scripts/case_probe.py` |
| 方法改进 | 5 | ①**M1 生成前门**（错误在绘制前被拦）②**M3 四段 PDF 回退** + 诚实 backend ③**M5 单一字体事实源**（render/checks/result 同源）④**静默失败判据**（exit 0 + success + 无痕迹 ⇒ 判失效）⑤**独立复核器交叉验证**（主流程说 ok ≠ 契约门说 ok） | `scripts/spec_lint.py`、`scripts/pdftext.py`、`scripts/textfont.py`、`references/FAULT-MATRIX.md` §2/§6 |
| 创新证据 | 5 | 每个机制给出**可证伪判据**与**已知盲区**（`MECHANISM.md`）；25 条注入 + 10 项题集都留下机器可读报告（`fault-matrix.json` / `case-report.json`）；注入过程**发现并修掉两个真实缺陷**（字典损坏崩流水线、缺依赖不留失败记录），并**公开六个拦不住的盲区** | `references/MECHANISM.md`、`references/FAULT-MATRIX.md` §4/§5、`references/CASE-SET.md` §4 |

## 4. 可靠体验 10 分

| 评分点 | 分 | 本包机制 | 落到哪个文件 / 哪条实测 |
|-|-|-|-|
| 调用与易用性 | 3 | 全部命令自定位（`$SKILL_DIR`，任意 cwd 可跑）；`--case` 兼容文件与目录；两个新工具都支持 `--list` / 分组 / 单项筛选；产物一律写包外，越界写入被拒绝 | `SKILL.md` §2、`scripts/fault_inject.py`、`scripts/case_probe.py` |
| 运行稳定性 | 4 | 四形态 25/25 符合期望、**0 条静默失败**；题集 10/10 落在声明区间；退出码 0/1/2 与 `status` 同向；依赖缺失也写 `failed` 的 `result.json` | `references/FAULT-MATRIX.md` §2/§3、`references/CASE-SET.md` §3 |
| 异常处理 | 3 | **D1–D16** 决策规则 + **L0–L3** 降级档位 + 恢复条件；六条已知盲区**逐条公开**（材料内容不可读、语义方向错、独立 `spec_lint.py` 对坏字典仍崩、Pillow 与 matplotlib 缺失去别、`--skip-checks` 自选降级、加密 PDF 主流程不感知） | `references/failure-modes.md`、`references/FAULT-MATRIX.md` §4、`SKILL.md` §5 |

## 5. 生态贡献 10 分

| 评分点 | 分 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 文档完整性 | 3 | 说明/依赖/字体/参数/示例/边界/维护齐全；`SKILL.md` 按"输入→执行→失败→增益→机制→复用"重排并逐节索引到各 reference | `README.md`、`SKILL.md`、`TEST.md`、`references/*` |
| 资源可复用性 | 4 | 12 项可复用资产 **A1–A12** + 5 级采纳阶梯（`REUSABLE-ASSETS.md`）；机器可读连接规则字典与自查清单；契约校验器与文档对拍器；**两个可迁移的工具**（注入器/题集执行器都能对任意同族技能包跑：`--skill-root` 指向别处即可） | `references/REUSABLE-ASSETS.md`、`assets/*`、`scripts/fault_inject.py`、`scripts/case_probe.py`、`scripts/doccheck.py` |
| 分享推广价值 | 3 | 沉淀了可直接分享的四类材料：**题集**（5 案 2 题材，含"加案例三步法"）、**故障矩阵**（25 条四形态，可当日志格式复用）、**对照协议 + 记账模板**、**边界清单**（拦得住／拦不住但可计算／根本拦不住三分类）；均可脱离本题单独使用 | `references/CASE-SET.md`、`references/FAULT-MATRIX.md`、`references/GAIN-PROTOCOL.md` |

## 6. GitHub 公开作品链接 5 分

| 项 | 内容 | 文件 |
|-|-|-|
| 根目录 `GITHUB_URL.txt` 第一行给出公开仓库链接，指向本作品目录（第二行可选作品相对路径） | 发布前用**未登录**窗口打开确认可见 | `GITHUB_URL.txt` |

---

## 7. 自评口径（避免自说自话）

- 本表的每一栏都必须能指到**可跑的检查**或**一条真实读数**（`TEST.md` 里的
  命令与输出、`fault-matrix.json` / `case-report.json` 里的字段）；
- **文字自述不算证据**：题面明确"文字自述不能替代实际运行证据"，因此本表
  不写"效果好/很可靠"这类形容词，只写"哪个判据、哪条实测"；
- **没测的不写**：平台分数、`line`/`scatter` 分支、真实论文 PDF、>60 节点拓扑、
  EPS/TIFF 导出与期刊字体嵌入审计均**未测量**，本表不为它们背书。
