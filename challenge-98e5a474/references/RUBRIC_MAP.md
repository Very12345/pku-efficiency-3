# RUBRIC_MAP — 五维评分 → 本包文件/机制（逐条映射）

官方题面评分维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
生态贡献 10**，外加 **GitHub 公开作品链接 5 分**（`GITHUB_URL.txt`）。

下面的每一行都指向**本包里真实存在的文件或可执行的机制**（脚本、检查门、
退出码语义），不是文字自述；"自述不替代运行证据"这一条由
`scripts/run_examples.py`（示例现场复跑 + G1–G8 校验）与 `TEST.md`（本机
实测记录）承担。**行文中的路径均相对技能根**，命令一律写成
`"$SKILL_DIR/..."` 以便在任意 cwd 下执行。

---

## 1. 实际效果 40 分

| 评分点 | 分值 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 任务完成度 | 15 | 完整"材料→图稿→导出"链路，一条命令可跑：读实际文件 →（`extract.py` 候选草稿）→ ER 清单 → CP1 lint → 可编辑分层 SVG → PNG/PDF → result.json；示例三件套（schematic / chart / edit）**现场跑通并留真实产物**（产物不入包，见下条） | `scripts/main.py`、`scripts/extract.py`、`scripts/spec_lint.py`、`scripts/run_examples.py`、`examples/EXPECTED-OUTPUT.md` |
| 结果正确性 | 15 | ①每个实体/关系带 `source`+`evidence`，写入 result.json `evidence` 与 SVG `data-*` 属性；②关系 kind 经 7 类规范词表映射（**激活≠抑制**，未知 kind = fail 而非猜）；③**containment 必须用分组框**，禁止画箭头（`spec.containment_group`）；④图例↔图面双向一致（缺项 fail / 孤儿项 warn）；⑤chart 类别只来自数据表：表外类别触发 **G8 硬门 INVALID** | `references/DRAWING_GRAMMAR.md`、`references/ER_MANIFEST.md`、`assets/relation-dict.json`、`scripts/spec_lint.py`、`scripts/checks.py`、`scripts/validate_result.py` |
| 结果完整性 | 5 | 图面要素齐全：实体节点、关系边（方向语义）、分组框、图题/副题、图例（每项带 `source`）、单位上轴（chart）、来源页脚；SVG 语义图层 `layer-background/groups/edges/nodes/legend/footer` + `<title>/<desc>` | `scripts/svgbuilder.py`、`scripts/layout.py`、`scripts/render.py` |
| 结果可核验性 | 5 | 元素级 `data-entity`/`data-relation`/`data-canon`/`data-source` 审计（写入 `verification.checks`）；`<metadata id="er-manifest">` 内嵌 ER 清单 → 图稿自描述；`validate_result.py` 的 G1–G8 可由第三方独立复跑；`determinism.spec_sha16` 提供双跑一致性探针 | `scripts/checks.py`、`scripts/svgbuilder.py`、`scripts/validate_result.py`、`references/OUTPUT_CONTRACT.md` |

> **产物形态声明**：包内**不预置**任何 PDF/PNG/SVG（平台不支持的文件类型 +
> 预置产物容易被误当正式答案）。示例期望产物以文字清单形式写在
> `examples/EXPECTED-OUTPUT.md`，并由 `scripts/run_examples.py` 现场生成
> 到包外目录 —— 这条同时也是"实际效果"的可复核入口。

## 2. 使用增益 25 分

| 评分点 | 分值 | 本包机制 | 落到哪个文件 |
|-|-|-| -|
| 质量增益 | 15 | 同一输入/画布/导出参数下，**三层门每次运行自动执行**：CP1 生成前 lint（`spec_lint.py`）→ CP2 产物检查（`checks.py`：溯源/图例/数据映射/DPI/色彩/PDF 结构/字体）→ CP3 契约门（`validate_result.py` G1–G8）；失败不静默：`status` 降为 `partial` 并列出 fail 明细；生成→检查→编辑→再校验闭环 | `scripts/spec_lint.py`、`scripts/checks.py`、`scripts/validate_result.py`、`SKILL.md` §3 S3/S5/S7 |
| 效率增益 | 5 | 素材→图稿一条命令；`extract.py` 现场产出**带定位的候选 ER 清单**，减少人工抽取；数据/图例改动只改 manifest 即整体重绘（不是重画）；编辑任务直接读 SVG 内嵌清单做增量修改（`--edit-svg`），无需重新抽取；`run_examples.py` 一条命令复跑三示例并校验契约 | `scripts/main.py`、`scripts/extract.py`、`scripts/edit.py`、`scripts/run_examples.py` |
| 增益可验证性 | 5 | `TEST.md` 记录本机实测（脚本自测项数、三示例 exit code、契约校验 VALID、确定性双跑）；`run_examples.py` 输出每步 exit code + result.json 顶层键覆盖 + 声明产物落盘核对，任何一步失败即非零退出；`verification.determinism.spec_sha16` 提供同输入同 sha 探针 | `TEST.md`、`scripts/run_examples.py`、`scripts/selftest.py` |

> **对照口径**：白板/基础 Agent 对照由平台按相同案例执行，参赛者不提供
> 隐藏测试；本包给出的自证是"同一夹具可复跑 + 门控结果可独立复核"。

## 3. 创新增益 15 分

| 评分点 | 分值 | 本包机制（相对"基础 Agent 直接画图"新增的能力） | 落到哪个文件 |
|-|-|-|-|
| 新增能力 | 5 | ①**CP1 生成前 lint 门**：在画之前就拦下未知 kind、containment 画成箭头、图例缺项、调色板 < 类别数；②材料→候选 ER 清单抽取（中英文关系动词词表 + `_draft` 标注 + 未知类型 fail 而不猜）；③PDF 文本抽取（fitz→pypdf→PyPDF2→**stdlib 回退**，诚实记录 backend）；④数据表驱动图例/颜色重绘；⑤导出前合规检查（有效 DPI、色彩、`<text>` 可编辑性、PDF 结构、字体） | `scripts/spec_lint.py`、`scripts/extract.py`、`scripts/pdftext.py`、`scripts/render.py`、`scripts/checks.py` |
| 方法改进 | 5 | ①SVG **内嵌 ER 清单** → 源文件自包含、可源文件级增量编辑（未改动元素保持原样）；②手写分层 SVG（语义图层 + id + `data-*`）+ matplotlib 镜像预览保持语义一致；③matplotlib `svg.fonttype=none` 保住文字可编辑（默认 path 化会毁掉可编辑性）；④共享字体探针 `textfont.py` 让 render/checks/result 三方同源、不再各猜字体 | `scripts/svgbuilder.py`、`scripts/edit.py`、`scripts/render.py`、`scripts/textfont.py` |
| 创新证据 | 5 | `selftest.py` 覆盖模块级断言（含 CP1 好/坏清单、G 门拒绝假成功、pdftext 回退、字体探针确定性）；`run_examples.py` 复跑三示例并逐份跑 G1–G8；示例编辑任务产出恰 3 条 `change_records`（rename/relabel/note）且未改动元素保持 | `scripts/selftest.py`、`scripts/run_examples.py`、`examples/EXPECTED-OUTPUT.md` §3 |

## 4. 可靠体验 10 分

| 评分点 | 分值 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 调用与易用性 | 3 | YAML frontmatter 的 name/description 明确触发条件；**自定位**：文档命令用 `"$SKILL_DIR/..."` 绝对路径，脚本内部用 `os.path.dirname(__file__)`，任意 cwd 可跑；`--case` 同时接受 case.json 文件与目录（`--case examples`）；一条命令出图；`--help` 覆盖全部参数 | `SKILL.md` §2/S4、`scripts/main.py` |
| 运行稳定性 | 4 | 三类图型（schematic/chart/edit）重复运行稳定；无 cairosvg/svgwrite 时镜像渲染降级并如实标注；无 PDF 第三方库时 stdlib 回退；产物写出后再汇总；失败仍写 `status=failed` 的 result.json（工作不丢失）；确定性 sha 探针 | `scripts/render.py`、`scripts/pdftext.py`、`scripts/main.py`、`scripts/report.py` |
| 异常处理 | 3 | 明确退出码语义：**0** = success（可含 warn 且已 ack）/ **1** = partial 或 failed（result.json 仍写出）/ **2** = 致命（case 缺失、目录无 case.json、编辑目标无内嵌清单、渲染致命错）；D1–D12 覆盖材料缺失、方向矛盾、未知 kind、图表不符、颜色×类别数、CJK 字体缺失、PDF 加密/扫描件、导出失败 | `scripts/main.py`、`SKILL.md` §4§5、`references/failure-modes.md` |

## 5. 生态贡献 10 分

| 评分点 | 分值 | 本包机制 | 落到哪个文件 |
|-|-|-|-|
| 文档完整性 | 3 | 用途/适用条件/输入输出/调用方式/执行步骤/决策规则/异常处理/依赖与字体/限制/维护一应俱全；示例明确标注"示例，非正式案例"；资源形态约束（≤50 文本文件、≤500KB、≤2MB、无符号链接）写在 SKILL.md 与 README.md | `SKILL.md`、`README.md`、`TEST.md`、`references/*`、`examples/README.md` |
| 资源可复用性 | 4 | **机器可读连接规则字典**（kind→arrow/line/dash/color）可直接被别的绘图流程复用；CP1–CP5 自查清单（机器可读）；ER 清单规范 + 图形语法规范；契约校验器（G1–G8）与示例题集（schematic/chart/edit）可直接复跑或改造成新案例 | `assets/relation-dict.json`、`assets/checklist.json`、`references/ER_MANIFEST.md`、`references/DRAWING_GRAMMAR.md`、`scripts/validate_result.py`、`examples/*` |
| 分享推广价值 | 3 | 失败形态文档（本题 12 类失败的检测→处置）可迁移到同类示意图题；三示例题集 + 期望产物清单构成最小可复现题集；GITHUB_URL.txt 指向公开仓库（未登录可读） | `references/failure-modes.md`、`examples/EXPECTED-OUTPUT.md`、`GITHUB_URL.txt` |

## 6. GitHub 公开作品链接 5 分

`GITHUB_URL.txt`（包根，第一行）：

```
https://github.com/Very12345/pku-efficiency-3/tree/main/challenge-98e5a474
```

发布前需用**未登录**的浏览器窗口打开一次确认可访问；链接无效则本项 0 分，
其余评分项按原规则计分。

---

## 7. 自查方式（交付前逐条自评）

```bash
python "$SKILL_DIR/scripts/selftest.py"                          # 逻辑自测
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-ex     # 三示例 + G1–G8
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/sse-out
python "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/case.json" --result /tmp/sse-out/result.json
```

四条命令都应 **exit 0**；示例产物全部落在包外（`/tmp/...`），
包内只保留 UTF-8 文本资源。
