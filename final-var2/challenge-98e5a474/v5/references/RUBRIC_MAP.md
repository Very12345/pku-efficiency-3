# RUBRIC_MAP — 五维评分 → 本包文件/机制（v1 · 决策显性化轴）

官方题面维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**，
外加 **GitHub 公开作品链接 5 分**（`GITHUB_URL.txt`）。本变体的强化轴是
**决策显性化**（D 规则 + L 档位 + 执行锚点），因此下表每行都指到
**本包里真实存在的文件或可执行机制**，并尽量给出可跑的命令——
"文字自述不能替代实际运行证据"这一条由 `TEST.md`（逐条实测）与
`scripts/doccheck.py`（文档↔代码对拍）承担。

---

## 1. 实际效果 40 分

| 评分点 | 分 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 任务完成度 | 15 | 完整"材料→图稿→导出"链路一条命令跑通：读实际文件 →（`extract.py` 候选草稿）→ ER 清单 → CP1 lint → 可编辑分层 SVG → PNG/PDF → result.json；示例三件套现场跑通并留真实产物 | `scripts/main.py`、`scripts/extract.py`、`scripts/spec_lint.py`、`scripts/run_examples.py` |
| 结果正确性 | 15 | ①每个实体/关系带 `source`+`evidence`；②kind 经 7 类规范词表映射（**激活≠抑制**，未知 kind = fail 不猜）；③containment 必须用分组框；④图例↔图面双向一致；⑤chart 表外类别 = G8 INVALID；**⑥每条正确性门都绑定一条 D 规则 → 出错时的处置是预先写好的，不是当场发挥** | `references/DRAWING_GRAMMAR.md`、`assets/relation-dict.json`、`scripts/spec_lint.py`、`scripts/validate_result.py`、SKILL.md §3.3 |
| 结果完整性 | 5 | 图面要素齐全：实体节点、关系边、分组框、图题/副题、图例、单位上轴、来源页脚；SVG 语义图层 + `<title>/<desc>` | `scripts/svgbuilder.py`、`scripts/layout.py`、`scripts/render.py` |
| 结果可核验性 | 5 | 元素级 `data-entity`/`data-relation`/`data-canon`/`data-source` 审计；`<metadata id="er-manifest">` 内嵌清单 → 图稿自描述；G1–G8 可第三方复跑；`determinism.spec_sha16` 双跑探针；**新增 `references/CHECK-INDEX.md` 把全部检查名连同级别与含义列全** | `scripts/checks.py`、`scripts/svgbuilder.py`、`scripts/validate_result.py`、`references/CHECK-INDEX.md` |

> **产物形态声明**：包内**不预置**任何 PDF/PNG/SVG（平台不支持的类型 + 预置产物
> 易被误当正式答案）。期望产物以文字清单写在 `examples/EXPECTED-OUTPUT.md`，
> 由 `scripts/run_examples.py` 现场生成到包外目录。

## 2. 使用增益 25 分

| 评分点 | 分 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 质量增益 | 15 | 同一输入/画布/导出参数下，三层门每次运行自动执行：CP1 生成前 lint → CP2 产物检查 → CP3 契约门；失败不静默（`status` 降 `partial` 并列出 fail 明细）；**D 规则把返工点前置**：能在生成前拦下的绝不拖到画完 | `scripts/spec_lint.py`、`scripts/checks.py`、`scripts/validate_result.py`、SKILL.md §4 |
| 效率增益 | 5 | 素材→图稿一条命令；`extract.py` 现场产出带定位的候选清单；改数据只改清单即整体重绘（实测 SVG sha 随之变化）；编辑走 SVG 内嵌清单增量改；**`doccheck.py` 一条命令替代人工比对文档与代码** | `scripts/main.py`、`scripts/extract.py`、`scripts/edit.py`、`scripts/doccheck.py` |
| 增益可验证性 | 5 | `TEST.md` 逐条给出**D 规则 → 实测档位**的对应表（含退出码、日志原文、检查名）；`run_examples.py` 输出每步 exit code + 顶层键覆盖 + 产物落盘核对，任一步失败即非零退出；`doccheck.py` 给出可复跑的"文档↔代码"一致性数字 | `TEST.md` §T6、`scripts/run_examples.py`、`scripts/doccheck.py` |

> **对照口径**：白板/基础 Agent 对照由平台按相同案例执行，参赛者不提供隐藏测试；
> 本包给出的自证是"同一夹具可复跑 + 门控结果可独立复核 + 文档与代码可对拍"。

## 3. 创新增益 15 分

| 评分点 | 分 | 本包机制（相对"基础 Agent 直接画图"新增的能力） | 落到哪个文件 |
|-|-|-|-|
| 新增能力 | 5 | ①CP1 **生成前** lint 门；②材料→候选 ER 清单抽取（`_draft` 标注 + 未知类型 fail 而不猜）；③PDF 文本抽取四段回退 + 诚实 backend；④数据表驱动图例/颜色重绘；⑤导出前合规检查 | `scripts/spec_lint.py`、`scripts/extract.py`、`scripts/pdftext.py`、`scripts/checks.py` |
| 方法改进 | 5 | ①SVG **内嵌 ER 清单** → 源文件自包含、可增量编辑；②手写分层 SVG + matplotlib 镜像预览保持语义一致；③`svg.fonttype=none` 保住文字可编辑；④共享字体探针三方同源；**⑤把"边界情况处置"提升为一等公民：D 规则带唯一编号、降级档位、恢复条件，并与检查名一一对拍** | `scripts/svgbuilder.py`、`scripts/edit.py`、`scripts/textfont.py`、SKILL.md §3、`references/EDIT-ACTION-SCHEMA.md` |
| 创新证据 | 5 | `selftest.py` 模块级断言（含 CP1 好/坏清单、G 门拒绝假成功、pdftext 回退、字体探针确定性）；`run_examples.py` 复跑三示例并逐份跑 G1–G8；**`doccheck.py` 用真实计数证明"文档里提到的每个检查名都在代码里真实存在"** | `scripts/selftest.py`、`scripts/run_examples.py`、`scripts/doccheck.py` |

## 4. 可靠体验 10 分（本变体的主战场）

| 评分点 | 分 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 调用与易用性 | 3 | YAML frontmatter 说明触发条件；**自定位**（`$SKILL_DIR`，任意 cwd 可跑）；`--case` 同时接受文件与目录；一条命令出图；**"我该看哪张表"在 README 里有速查** | `SKILL.md` §2/§4、`README.md`、`scripts/main.py` |
| 运行稳定性 | 4 | 三类图型（schematic/chart/edit）重复运行稳定；镜像渲染降级、PDF stdlib 回退、失败仍写 result.json（工作不丢失）；确定性 sha 探针；**每条降级都有恢复条件，不会一次降级永久生效** | `scripts/render.py`、`scripts/pdftext.py`、`scripts/main.py`、SKILL.md §3.2 |
| 异常处理 | 3 | 退出码语义 **0/1/2** 与 `status` 同向（不变式 B）；**D1–D16 覆盖输入、依据、图面、契约、编辑、环境、参数七类分支**，每条带降级档位与恢复条件；失败分支表按"谁先发现"分组，便于现场定位 | SKILL.md §3.3/§3.4/§5、`references/failure-modes.md`、`references/CHECK-INDEX.md` |

## 5. 生态贡献 10 分

| 评分点 | 分 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 文档完整性 | 3 | 用途/适用条件/输入输出/调用方式/执行骨架/决策规则/异常处理/依赖与字体/限制/维护一应俱全；示例明确标注"示例，非正式案例"；资源形态约束写在 SKILL.md 与 README | `SKILL.md`、`README.md`、`TEST.md`、`references/*` |
| 资源可复用性 | 4 | 机器可读连接规则字典；CP1–CP5 自查清单；ER 清单规范；图形语法规范；契约校验器（G1–G8）；**D 规则—检查名—脚本锚点三点对拍表 + 检查名索引 + 只读对拍工具**；三示例题集 | `assets/*`、`references/*`、`scripts/validate_result.py`、`scripts/doccheck.py`、`examples/*` |
| 分享推广价值 | 3 | "失败形态 → D 规则 → 档位"这套写法可直接迁移到任何"有硬门 + 有降级"的技能题；`doccheck.py` 是通用的"文档是否吹牛"检查器；三示例题集构成最小可复现题集 | `references/failure-modes.md`、`references/CHECK-INDEX.md`、`scripts/doccheck.py`、`examples/EXPECTED-OUTPUT.md` |

## 6. GitHub 公开作品链接 5 分

`GITHUB_URL.txt`（包根，单行）：

```
https://github.com/Very12345/pku-efficiency-3/tree/main/final-var/challenge-98e5a474/v1
```

发布前用**未登录**窗口打开一次确认可访问；链接无效则本项 0 分，其余项按原规则计分。

---

## 7. 自查方式（交付前逐条自评）

```bash
python "$SKILL_DIR/scripts/selftest.py"                          # 逻辑自测
PYTHONDONTWRITEBYTECODE=1 python -B "$SKILL_DIR/scripts/doccheck.py"   # 文档↔代码对拍
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-ex     # 三示例 + G1–G8
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/sse-out
python "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/case.json" --result /tmp/sse-out/result.json
```

五条命令都应 **exit 0**；示例产物全部落在包外（`/tmp/...`），
包内只保留 UTF-8 文本资源。
