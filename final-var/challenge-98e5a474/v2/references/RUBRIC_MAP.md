# RUBRIC_MAP — 五维评分 → 本包文件/机制（v2 · 增益可验证轴）

官方题面维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**，
外加 **GitHub 公开作品链接 5 分**（`GITHUB_URL.txt`）。本变体的强化轴是
**增益可验证化**，因此下表把"使用增益"三块**逐块**指到真实文件，
并明确区分"已由实测支撑"与"未测量"。

---

## 1. 实际效果 40 分

| 评分点 | 分 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 任务完成度 | 15 | 材料→ER 清单→CP1→可编辑 SVG→PNG/PDF→result.json 一条命令跑通；每例的 exit code / 耗时 / 顶层键数都留档（R1–R4） | `scripts/main.py`、`scripts/extract.py`、`scripts/run_examples.py`、`TEST.md` §M3/M4 |
| 结果正确性 | 15 | ①实体/关系带 `source`+`evidence`；②kind 经 7 类规范词表映射（未知 kind = fail 不猜）；③containment 必须分组框；④图例↔图面双向一致；⑤chart 表外类别 = G8 INVALID | `references/DRAWING_GRAMMAR.md`、`assets/relation-dict.json`、`scripts/spec_lint.py`、`scripts/validate_result.py` |
| 结果完整性 | 5 | 图面要素齐全（节点/边/分组框/图题/图例/单位轴/来源脚注）+ SVG 语义图层 + `<title>/<desc>` | `scripts/svgbuilder.py`、`scripts/layout.py`、`scripts/render.py` |
| 结果可核验性 | 5 | 元素级 `data-*` 溯源审计；`<metadata id="er-manifest">` 内嵌清单；G1–G8 可第三方复跑；`determinism.spec_sha16` 双跑探针；**指标字典（I1–I10）把每个读数指到具体检查名** | `scripts/checks.py`、`scripts/validate_result.py`、`references/GAIN-PROTOCOL.md` §2 |

## 2. 使用增益 25 分（本变体的主战场）

| 评分点 | 分 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 质量增益 | 15 | 同一输入/画布/导出参数下三层门每次运行自动执行（CP1→CP2→CP3）；失败不静默；**质量相关读数（I3 可编辑性、I5 语义、I6 图例、I7 数据映射、I8 导出）逐项定义并可取值**；降级必须写 `uncertainty`（F2/G2） | `scripts/spec_lint.py`、`scripts/checks.py`、`scripts/validate_result.py`、`references/GAIN-PROTOCOL.md` §2 |
| 效率增益 | 5 | 素材→图稿一条命令（实测 ≈1.5 s/例，R1）；`extract.py` 现场产出带定位的候选清单（0.12 s，R12）；改数据只改清单即重绘（R6）；编辑走内嵌清单增量改（R10）；**I9 返工轮次以"CP1 第 k 次 valid"这一可复现事实记账** | `scripts/main.py`、`scripts/extract.py`、`scripts/edit.py`、`references/GAIN-PROTOCOL.md` §2/§5 |
| 增益可验证性 | 5 | **对照协议 F1–F8 + 指标 I1–I10 + 实测 R1–R13 + 记账模板 + "能支撑/不能支撑"表**；判据固定为同一个 `validate_result.py`（F5），并写明该判据的有偏性如何处理（§1.1）；**未跑过的指标一律标注"未测量"（F8/§4）** | `references/GAIN-PROTOCOL.md`（全文）、`TEST.md` §M5/M8 |

> **对照口径**：白板/基础 Agent 对照由平台按相同案例执行，参赛者不提供隐藏测试；
> 本包给出的是"本技能一侧可复跑 + 判据固定 + 未测量项列明"。

## 3. 创新增益 15 分

| 评分点 | 分 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 新增能力 | 5 | ①CP1 **生成前** lint 门；②材料→候选 ER 清单（`_draft` + 未知类型 fail）；③PDF 抽取四段回退 + 诚实 backend；④数据表驱动图例/颜色重绘；⑤导出前合规检查 | `scripts/spec_lint.py`、`scripts/extract.py`、`scripts/pdftext.py`、`scripts/checks.py` |
| 方法改进 | 5 | ①SVG 内嵌 ER 清单 → 可增量编辑；②手写分层 SVG + matplotlib 镜像保持语义一致；③`svg.fonttype=none` 保住文字可编辑；④共享字体探针三方同源；**⑤把"可测"作为一等公民：每个改进都绑定一个可取值指标或明确标注不可测** | `scripts/svgbuilder.py`、`scripts/edit.py`、`scripts/textfont.py`、`references/GAIN-PROTOCOL.md` §2/§3.5 |
| 创新证据 | 5 | `selftest.py` 模块级断言；`run_examples.py` 复跑三示例并逐份跑 G1–G8；`doccheck.py` 用真实计数对拍文档与代码；**`GAIN-PROTOCOL.md` §3 的 R1–R13 是可复跑的实测，§4 明确哪些结论尚未被支撑** | `scripts/selftest.py`、`scripts/run_examples.py`、`scripts/doccheck.py`、`references/GAIN-PROTOCOL.md` §3/§4 |

## 4. 可靠体验 10 分

| 评分点 | 分 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 调用与易用性 | 3 | frontmatter 说明触发条件与"每次运行都产出可比较指标"；**自定位**（任意 cwd 可跑，R2 给出同 sha 证据）；`--case` 兼容文件与目录；"我该看哪张表"在 README 有速查 | `SKILL.md` §1/§4、`README.md`、`scripts/main.py` |
| 运行稳定性 | 4 | 三类图型重复运行稳定（R1–R4）；镜像渲染降级、PDF stdlib 回退、失败仍写 result.json；确定性 sha 探针（R5）；预算与平台契约一致（F3） | `scripts/render.py`、`scripts/pdftext.py`、`scripts/main.py`、`references/GAIN-PROTOCOL.md` §1 |
| 异常处理 | 3 | 退出码 0/1/2 与 `status` 同向；**G1–G8 专治"会污染测量"的分支**（未检查当已通过、降级不记录、改条件后互比、编辑未生效、丢弃失败、无基线就声明更好、把 ack 写成 ok、材料不可抽取时造假）；每个失败形态在 `failure-modes.md` 里多一列"对读数的影响" | `SKILL.md` §5/§6、`references/failure-modes.md` |

## 5. 生态贡献 10 分

| 评分点 | 分 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 文档完整性 | 3 | 用途/适用条件/输入输出/调用方式/执行路线/决策规则/异常处理/依赖/限制/维护齐全；**限制里明确写出"未测量"清单**；示例标注"示例，非正式案例" | `SKILL.md`、`README.md`、`TEST.md` §M8、`references/*` |
| 资源可复用性 | 4 | **对照协议 + 记账模板（可直接被别的技能题复用）**；指标字典；检查名索引；机器可读连接规则字典；CP1–CP5 自查清单；ER 清单规范；图形语法；契约校验器；文档↔代码对拍器；三示例题集 | `references/GAIN-PROTOCOL.md`、`references/CHECK-INDEX.md`、`assets/*`、`scripts/validate_result.py`、`scripts/doccheck.py`、`examples/*` |
| 分享推广价值 | 3 | "如何诚实地报告增益"这套写法（协议条款 + 可支撑/不可支撑表 + 未测量清单）可直接迁移到任何"人机对照"类技能题；`doccheck.py` 与 `GAIN-PROTOCOL.md` §5 模板即插即用 | `references/GAIN-PROTOCOL.md` §1/§4/§5、`scripts/doccheck.py` |

## 6. GitHub 公开作品链接 5 分

`GITHUB_URL.txt`（包根，单行）：

```
https://github.com/Very12345/pku-efficiency-3/tree/main/final-var/challenge-98e5a474/v2
```

发布前用**未登录**窗口打开一次确认可访问；链接无效则本项 0 分。

---

## 7. 自查方式（交付前逐条自评）

```bash
python "$SKILL_DIR/scripts/selftest.py"
PYTHONDONTWRITEBYTECODE=1 python -B "$SKILL_DIR/scripts/doccheck.py"
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-ex
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/sse-out
python "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/case.json" --result /tmp/sse-out/result.json
```

五条命令都应 **exit 0**；示例产物全部落在包外；包内只保留 UTF-8 文本资源。
