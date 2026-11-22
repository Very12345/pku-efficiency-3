# RUBRIC_MAP — 五维评分 → 本包文件/机制（v3 · 机制与复用显性轴）

官方题面维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**，
外加 **GitHub 公开作品链接 5 分**（`GITHUB_URL.txt`）。本变体的强化轴是
**机制显性化 + 复用显性化**，因此"创新增益"与"生态贡献"两栏给到最细，
其余三栏照常指到真实文件与可跑机制。

---

## 1. 实际效果 40 分

| 评分点 | 分 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 任务完成度 | 15 | 完整"材料→图稿→导出"链路一条命令跑通；示例三件套现场跑通并留真实产物（V5 联合判据） | `scripts/main.py`、`scripts/run_examples.py`、`TEST.md` §V5 |
| 结果正确性 | 15 | ①每个实体/关系带 `source`+`evidence`；②**M1** 拦住未知 kind（`spec.relation_kind`）；③**M1** 强制 containment 用分组（`spec.containment_group`）；④图例↔图面双向一致；⑤chart 表外类别 = G8 INVALID | `scripts/spec_lint.py`、`references/DRAWING_GRAMMAR.md`、`assets/relation-dict.json`、`scripts/validate_result.py` |
| 结果完整性 | 5 | 图面要素齐全 + SVG 语义图层 + `<title>/<desc>`；三类产物由 `artifact.<role>` 逐类核验 | `scripts/svgbuilder.py`、`scripts/layout.py`、`scripts/checks.py` |
| 结果可核验性 | 5 | **M2** 让图稿自描述（内嵌清单 + `data-*`）；G1–G8 可第三方复跑；`determinism.spec_sha16` 双跑探针；**`references/CHECK-INDEX.md` 把每个判据的检查名列全** | `scripts/checks.py`、`scripts/svgbuilder.py`、`scripts/validate_result.py`、`references/CHECK-INDEX.md` |

## 2. 使用增益 25 分

| 评分点 | 分 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 质量增益 | 15 | 三层门每次运行自动执行（**M1** 生成前 → **M4** 产物后 → 契约门）；失败不静默；每个机制都给出"没有它会怎样"的具体退化形态，而不是笼统说"更可靠" | `scripts/spec_lint.py`、`scripts/checks.py`、`scripts/validate_result.py`、`references/MECHANISM.md` §M1.2/§M4.2 |
| 效率增益 | 5 | 素材→图稿一条命令；改数据只改清单即重绘（V5 实测 sha 变化）；**M2** 让编辑走内嵌清单增量改而非重画；**M3** 让"没装 PDF 库"不再阻塞整轮 | `scripts/main.py`、`scripts/edit.py`、`scripts/pdftext.py` |
| 增益可验证性 | 5 | `TEST.md` 按机制取证（V1–V5 逐条对应 `MECHANISM.md` 的判据）；每个机制都有**可证伪判据**与**推翻实验**（例：无内嵌清单必须被拒、坏清单必须被拦）；`doccheck.py` 保证判据不漂移 | `TEST.md` §V1–§V5、`references/MECHANISM.md`、`scripts/doccheck.py` |

## 3. 创新增益 15 分（本变体的主战场）

| 评分点 | 分 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 新增能力 | 5 | ①**M1** 生成前 lint 门；②材料→候选 ER 清单抽取（`_draft` + 未知类型 fail）；③**M3** PDF 抽取四段回退 + 诚实 backend；④数据表驱动图例/颜色重绘；⑤**M4** 导出前合规检查；⑥**M5** 字体单一事实源 | `scripts/spec_lint.py`、`scripts/extract.py`、`scripts/pdftext.py`、`scripts/checks.py`、`scripts/textfont.py` |
| 方法改进 | 5 | ①**M2** 源文件自描述（清单内嵌 + `data-*`）→ 可增量编辑；②手写分层 SVG + matplotlib 镜像保持语义一致；③`svg.fonttype=none` 保住文字可编辑；④**把机制之间的关系画成依赖图**（改 M5 会影响 M4 的判据强度）；⑤把"机制盲区"写进文档（M2.4、M4.4、M5.4） | `scripts/svgbuilder.py`、`scripts/edit.py`、`scripts/render.py`、`references/MECHANISM.md` |
| 创新证据 | 5 | **每个机制都有正向判据 + 推翻条件 + 已知盲区**，且判据在 `TEST.md` 里有真实读数；`selftest.py` 断言各模块；`run_examples.py` 复跑三示例并逐份跑 G1–G8；`doccheck.py` 对拍文档与代码 | `references/MECHANISM.md`（全文）、`TEST.md` §V1–§V5、`scripts/selftest.py`、`scripts/doccheck.py` |

> **为什么这算"创新"而不是"堆功能"**：判据是**可证伪**的。
> 例：若"无内嵌清单的 SVG 也能被编辑"（M2 的推翻条件），
> 或"坏清单能通过 CP1"（M1 的推翻条件），机制即被推翻 —— 任何人都能做这两个实验。

## 4. 可靠体验 10 分

| 评分点 | 分 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 调用与易用性 | 3 | frontmatter 说明触发条件并**点名五个机制**；自定位（任意 cwd 可跑，V5 给出同 sha 证据）；`--case` 兼容文件与目录；README 给出"想知道什么看哪里"的对照表 | `SKILL.md` §1/§4、`README.md`、`scripts/main.py` |
| 运行稳定性 | 4 | 三类图型重复运行稳定；**M3** 让缺库也能跑；**M5** 让字体结论一致；失败仍写 `result.json`；确定性 sha 探针；每条降级都指到受影响机制 | §4、§5、`references/MECHANISM.md` 依赖图、`TEST.md` §V5 |
| 异常处理 | 3 | 退出码 0/1/2 与 `status` 同向；**降级表把每条降级映射到机制**（例：镜像渲染 → M4 判据强度下降）；**机制盲区被写出来**（M2.4 的 `edit.*` 只进 stdout），并给出替代判据（条数对拍） | §5、§6、`references/MECHANISM.md` 各节盲区 |

## 5. 生态贡献 10 分（本变体的第二主战场）

| 评分点 | 分 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 文档完整性 | 3 | 用途/适用条件/输入输出/调用/机制索引/流程/降级/异常/依赖/限制/维护齐全；限制表**按机制归类**；示例标注"示例，非正式案例" | `SKILL.md`、`README.md`、`TEST.md` §V7、`references/*` |
| 资源可复用性 | 4 | **`references/REUSABLE-ASSETS.md`：A1–A12 资产总表（每项给"复用方式 + 采纳验证"）+ L0–L4 采纳阶梯（按改造成本分级）+ 三步复用操作 + 复用验证**；资产涵盖题集/金标准/规范/字典/校验器/对拍器/字体探针/自描述模式 | `references/REUSABLE-ASSETS.md`、`assets/*`、`scripts/validate_result.py`、`scripts/doccheck.py`、`examples/*` |
| 分享推广价值 | 3 | **机制写法本身可迁移**：任何技能题都能照"是什么 / 没有它会怎样 / 可证伪判据 / 已知盲区"四段来写自己的机制；`doccheck.py` 与自描述模式是跨题可用的通用件；复用三坑（只抄文件不抄判据、改判据不更新文档、把示例当答案）是给复用者的直接提醒 | `references/MECHANISM.md`、`references/REUSABLE-ASSETS.md` §2/§4、`scripts/doccheck.py` |

## 6. GitHub 公开作品链接 5 分

`GITHUB_URL.txt`（包根，单行）：

```
https://github.com/Very12345/pku-efficiency-3/tree/main/final-var/challenge-98e5a474/v3
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
# 加上两个"推翻实验"（机制的判据才算被检验过）
python "$SKILL_DIR/scripts/main.py" --case <无 manifest 的 case> --out /tmp/sse-fail   # 期望 exit 1
python "$SKILL_DIR/scripts/main.py" --case <edit case> --edit-svg <无内嵌清单的 svg> --out /tmp/sse-rej  # 期望 exit 2
```

五条主命令都应 **exit 0**；两个推翻实验应分别 `exit 1` / `exit 2`。
示例产物全部落在包外；包内只保留 UTF-8 文本资源。
