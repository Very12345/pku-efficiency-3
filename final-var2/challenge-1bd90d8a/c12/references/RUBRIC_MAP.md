# RUBRIC_MAP.md — 五维评分 → 增益可验证版的落点对照

官方口径（题面 §2）：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
生态贡献 10**，另加 GitHub 公开作品链接 5（附加）。

> **证据规则**：题面明写「文字自述不能替代实际运行证据」。下表每一行的「证据」列
> 都指向**本包内真实存在的文件**或**可复跑的命令**。
> 真机实测见 `TEST.md`；本版相对基线的增改见 `REFINEMENT-NOTES.md`。

**本版的强化定位**：主攻「**使用增益 25 分**」，手段是新增
`references/GAIN-PROTOCOL.md`（公平对照协议 + 12 项可测指标 + 真实对照记录）
与两个对照工具（`examples/baseline_agent.py` / `examples/measure_ab.py`）。
该强化的收益不靠自述，靠两件事成立：**① 协议可复跑**（同一份代码判两侧、
每条件各跑两次）；**② 如实公布自己不占优的项**（条件 A 也通过 Q12）。

---

## 1. 实际效果（40 分）

| 评分点 | 分 | 本版机制 | 可复跑证据 |
|-|-|-|-|
| 任务完成度 | 15 | 阶段化编排 `scripts/main.py`（G0 读契约 → G1 盘点 → G2 抽取 → G3 规格门 → G4 生成 → G5 映射核对 → G6 交付门 → G7 确定性 → G8 契约落地），每阶段有**进入/退出条件**（`SKILL.md` §4）；八种图型 + `panel` + `network` 在 `chartkit.py` | `main.py --case examples/case.json --out <out> --style nature` → **exit 0**、`completed`、11 个产物（`TEST.md` T2） |
| 结果正确性 | 15 | 图元带 `data-column`/`data-row-index`/`data-value`/`data-role`；`mapcheck.py` **重读源文件逐行核对**（容差 1e-9）+ SVG↔manifest 双向闭合；单位与误差语义显式声明；显著性只转述（**R6**）；实体名以原文为准（**R4**） | `mapcheck` 实测 `121 checked / 0 mismatched / 0 unmatched`（T3）；**指标 Q5** `rows_checked=24 mismatched=0`（T5） |
| 结果完整性 | 5 | 六类检查点各有机器判据并在 `checkpoints.cp5_figcheck.six_checkpoints` 盖戳：科学实体 · 空间关系 · 数据编码 · 图例标注 · 可编辑源文件 · 导出格式 | `figcheck_report.json` 六项 `covered=true`；**指标 Q1–Q8** 覆盖前四类 |
| 结果可核验性 | 5 | 源文件 sha256 + 行列数（`sources`）、每产物 sha256（`artifacts_sha256`）、人工确认与脚本流水（`change_records`）、**同输入字节级稳定**（含 PDF，本版已修） | **指标 Q10**（`sources=2 with_sha256=2`）· **Q11**（`change_records=7`）· **Q12**（归一化后 `differ=0`）；`verify_rerun` `DETERMINISTIC (identical=9 differ=0)` |

## 2. 使用增益（25 分）— 本版主攻维度

| 评分点 | 分 | 本版机制 | 可复跑证据 |
|-|-|-|-|
| 质量增益 | 15 | 把六类"看不见的错误"变成机器判据：缺列不猜、空值计数不补造、图例-系列一一对应（fail 阻断）、中文回退链、量级异常只 warn、显著性缺配对 fail。**本版再往前一步：把这些判据同时组织成 12 项可测指标**，使"加载后是否更好"可以直接读出数字 | **Q1–Q11 逐项**（T5）；`validation.json` 八类检查；`references/GAIN-PROTOCOL.md` §5.2 |
| 效率增益 | 5 | 一次调用走完全链路（11 个产物）；样式走预设（改预设键即改样式，不重写代码）；**效率口径已明确化**：不做"耗时缩短 x%"的声称（条件 A 更快是因为做的事更少），只报可测的量 | `GAIN-PROTOCOL.md` §5.4（耗时 1.51 s / 命令数 1 / 重绘 = 改预设键）；T7 |
| 增益可验证性 | 5 | ★ **本版核心**：`GAIN-PROTOCOL.md` 给出 6 条公平性条件（同输入文件、同数据版本、同导出参数、**同一套判定代码**、不允许人工润色、每条件跑两次）、归一化规则（只对**真正无法消除的环境变量**归一化，并说明方向性）、12 项指标的**逐项判定规则**、以及**实测记录（A 1/12 · B 12/12）** | `references/GAIN-PROTOCOL.md` 全文；`examples/measure_ab.py`；**复跑命令见协议 §4** |

> 本版**不声称任何"提升百分比"**：12 项指标的通过数是可复算事实，分数化的"提升"
> 需要平台的白板与基础 Agent，本机没有。这一边界写在 `GAIN-PROTOCOL.md` §0 与 §6。

## 3. 创新增益（15 分）

| 评分点 | 分 | 本版机制 | 可复跑证据 |
|-|-|-|-|
| 新增能力 | 5 | ① 图元↔源数据双向映射机器校验（三向闭合）；② 图例-系列自动对齐；③ 中文标注与字体回退；④ 手写 XML 分层 SVG（文字永不转曲）；⑤ 声明式管线（schema → lint → 绘制 → 校验）；⑥ **PDF 元数据确定性归一化**（本版新增，见 §2 的证据列）；⑦ **可复跑的 A/B 对照工具链**（本版新增） | `mapcheck.py` · `svgtext.py` · `cjkfont.py` · `chartkit.stamp_pdf_deterministic` · `examples/measure_ab.py`；T5/T6 |
| 方法改进 | 5 | **同一图元场景（`Scene`）双端输出**：SVG 与 PNG/PDF 由同一个 Scene 逐元素产生，杜绝"矢量好看、位图不同"；**新增：把"确定性"从纪律提升为硬指标**，使交付件 sha256 具备证据力 | `chartkit.py` 的 `Scene`/`export_figure`；**Q12**；T6 |
| 创新证据 | 5 | 边界写明（`SKILL.md` §8 限制 + `TEST.md` 6 条未解决项，含实测发现的 `spec_lint` 不查列存在性）；**相对"通用绘图库/现成模板"的差异由对照实验逐项量化**（Q1–Q11），且**公布自己不占优的 Q12** | `GAIN-PROTOCOL.md` §5–§6；`TEST.md` T5；`examples/EXPECTED-OUTPUT.md` |

## 4. 可靠体验（10 分）

| 评分点 | 分 | 本版机制 | 可复跑证据 |
|-|-|-|-|
| 调用与易用性 | 3 | 单一入口 `main.py`；**任意 cwd 可运行**（自定位 + bash/PowerShell 双写法）；`case.json` 多形态兼容；`task.md` 自动发现；契约四形态自动回显；**10 个参数成表**（`README.md` §2.1）；**6 个脚本的退出码成表**（§2.2） | `SKILL.md` §2；`README.md` §2；T2（cwd ≠ 技能根仍 exit 0） |
| 运行稳定性 | 4 | 单图失败不阻塞其他图（`status=partial`）；Pillow 缺失保 SVG + 全部 JSON；模板缺失回退内置默认；**确定性经修复后真正成立**（PDF 时间戳归一化，这是本版最重要的一处稳定性改进） | `TEST.md` T6（修复前后逐文件对照）· T8（异常路径） |
| 异常处理 | 3 | `references/failure-modes.md` **按"打击哪项指标"重新组织**为 7 组（F-A..F-G），共 **49 条分支**，每条给出触发条件、检出点、处置、落痕、复验命令；官方点名的五类情形逐类有落点：材料异常（F-G1..G5/G12）· 模板缺失（F-G7/F-G8）· 依赖缺失（F-F4 / F-G9/F-G10）· **契约四形态（F-E1..F-E5）** · 状态一致性（§8 三态 + 四条禁止） | `references/failure-modes.md` 全表；`SKILL.md` §6；T8 |

## 5. 生态贡献（10 分）

| 评分点 | 分 | 本版机制 | 可复跑证据 |
|-|-|-|-|
| 文档完整性 | 3 | `SKILL.md`（主张与证据边界 / 自定位 / 输入输出 / 阶段 G0–G8 / 规则 R1–R14 / 失败分支分类 / 实测增益 / 限制）· `README.md`（依赖 / 参数表 / 退出码表 / 设计不变量 / **对照实验入口表** / 维护表含"指标一致性铁律"）· `TEST.md`（9 组实测 + 6 条未解决项）· `REFINEMENT-NOTES.md` · `references/` **八份**（含 `GAIN-PROTOCOL.md`）· `templates/` 四份 | 包内文件清单（全部 UTF-8 文本）；`check_contract.py` 用机器可读契约块自查 |
| 资源可复用性 | 4 | 引擎库化（`import chartkit`）；六个校验/生成脚本各有独立 CLI；样式预设可扩展；规格契约开放；**A/B 对照工具链可整段搬走**（`baseline_agent.py` + `measure_ab.py` + 协议模板）；失败分支按指标归类，可直接当作**验收清单**用 | `README.md` §5 维护表；`GAIN-PROTOCOL.md` §8（迁移到别的交付型 Skill 的 5 条做法） |
| 分享推广价值 | 3 | 适用于「数据表/生物源材料 → 投稿级可编辑图」的一般场景；示例覆盖 panel 与 network 两类；**本版的可分享产物是"如何为一个 Skill 证明增益"的方法**：指标优先于自述、公开不占优项、协议驱动改进而非驱动结论 | `GAIN-PROTOCOL.md` §8；`examples/README.md` §5（三条使用纪律）；`TEST.md` 的复跑命令 |

## 6. GitHub 公开作品链接（5 分，附加）

- 根路径 `GITHUB_URL.txt` 第一行是公开仓库中本题作品的目录链接（无需登录可打开），
  第二行是本提交目录内的相对入口文件。
- 评审无需登录即可打开并找到本次提交的作品 → 得 5 分；缺交或链接无效 → 0 分。

## 7. 提交前自查（命令级）

```bash
SKILL_DIR=/skills/weekly-skill; OUT=<临时输出目录>; T=<临时对比目录>

python "$SKILL_DIR/scripts/main.py"           --case "$SKILL_DIR/examples/case.json" --out "$OUT" --style nature
python "$SKILL_DIR/scripts/check_contract.py" --result "$OUT/result.json" --case "$SKILL_DIR/examples/case.json"
python "$SKILL_DIR/scripts/figcheck.py"       --dir "$OUT" --case "$SKILL_DIR/examples/case.json"
python "$SKILL_DIR/scripts/mapcheck.py"       --dir "$OUT" --case "$SKILL_DIR/examples/case.json"
python "$SKILL_DIR/scripts/verify_rerun.py"   --case "$SKILL_DIR/examples/case.json" --out "$OUT"
# 对照实验（使用增益维度的主证据）
python "$SKILL_DIR/examples/measure_ab.py"    --label B --case "$SKILL_DIR/examples/case.json" \
       --out "$OUT" --run2 "$T/rerun"
```

| # | 检查 | 对应维度 | 期望 |
|-|-|-|-|
| 1 | `main.py` 退出码与 `result.json.status` | 实际效果 | `0` + `completed` |
| 2 | `check_contract.py` | 实际效果 / 可靠体验 | `PASS`，`missing=0 null=0 contract_missing=0` |
| 3 | `figcheck.py` G1–G8 + 六类检查点 | 实际效果 / 创新 | 全 OK，exit 0 |
| 4 | `mapcheck.py` | 实际效果 / 创新 | `mismatched=0 unmatched=0` |
| 5 | `verify_rerun.py` | **使用增益** / 可靠体验 | `DETERMINISTIC`，exit 0 |
| 6 | `measure_ab.py` 两侧判定 | **使用增益** | 与 `GAIN-PROTOCOL.md` §5.2 的数字一致（含 A 通过的那一项） |
| 7 | `GAIN-PROTOCOL.md` §5.1 指标表 ↔ `measure_ab.py` 的指标集 | 使用增益 | 逐条对应，无"文档有、代码无"的指标 |
| 8 | `references/failure-modes.md` 的分组 ↔ `SKILL.md` §6 | 可靠体验 | F-A..F-G 一致 |
| 9 | `GITHUB_URL.txt` | 附加 5 分 | 未登录可访问且指向本题作品 |
