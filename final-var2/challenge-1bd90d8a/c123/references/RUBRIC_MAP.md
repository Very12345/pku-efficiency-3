# RUBRIC_MAP.md — 五维评分 → 机制与复用显性版的落点对照

官方口径（题面 §2）：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
生态贡献 10**，另加 GitHub 公开作品链接 5（附加）。

> **证据规则**：题面明写「文字自述不能替代实际运行证据」。下表每一行的「证据」列
> 都指向**本包内真实存在的文件**或**可复跑的命令**。
> 真机实测见 `TEST.md`；本版相对基线的增改见 `REFINEMENT-NOTES.md`。

**本版的强化定位**：主攻「**创新增益 15**」与「**生态贡献 10**」两个维度，手段是：
① 新增 `references/MECHANISM.md` —— 把支撑链路的**四个咬合机制**写清楚，
每个都给出"**没有它会怎样**"的具体症状、实现落点与复验命令；
② 新增 `references/REUSE-KIT.md` —— 可复用资产按 A/B/C 三级分级，
给出**三条复用路径**、**十条验收清单**与"**不要带走的五项**"；
③ `README.md` §6 给出三条路径的**可操作版本**。

该强化的收益不靠自述，靠两件事成立：**① 机制可被单独验证**（每个机制都有对应的
复核命令，见 `README.md` §3.1）；**② 复用步骤的实测与失败记录**（`TEST.md` T4
记录了第一次复用演练**失败**并据此修正文档——那次演练推翻了"只拿 3 个脚本就够"的假设）。

---

## 1. 实际效果（40 分）

| 评分点 | 分 | 本版机制 | 可复跑证据 |
|-|-|-|-|
| 任务完成度 | 15 | 链路按四个机制组织（E0 读契约 → E1 盘点 → E2 抽取 → **E3 规格门** → **E4 生成** → **E5 三向核对** → E6 交付门 → **E7 确定性** → **E8 契约落地**），每一环标注它依赖哪个机制（`SKILL.md` §5）；八种图型 + `panel` + `network` 在 `chartkit.py` | `main.py --case examples/case.json --out <out> --style nature` → **exit 0**、`completed`、11 个产物（`TEST.md` T2） |
| 结果正确性 | 15 | **M1 三向闭合**：图元 `data-*` ↔ `data_manifest.json` ↔ **重读源表**的值（容差 1e-9，不得放宽）；单位与误差语义显式声明；显著性只转述；实体名以原文为准（M1-R5） | `mapcheck` 实测 `121 checked / 0 mismatched / 0 unmatched`（T3.1）；**手工反查一条**（`mean_um3` row 4 = 1180.0）三处一致 |
| 结果完整性 | 5 | 六类检查点各有机器判据并在 `checkpoints.cp5_figcheck.six_checkpoints` 盖戳；本版进一步说明**每类检查点由哪个机制保证**（`SKILL.md` §4.2 的"服务于"列） | `figcheck_report.json` 六项 `covered=true` |
| 结果可核验性 | 5 | 源文件 sha256 + 行列数（`sources`）、每产物 sha256（`artifacts_sha256`）、人工确认与脚本流水（`change_records`）、**同输入字节级稳定**（M4②，含 PDF） | `verify_rerun` `DETERMINISTIC (identical=9 differ=0)`；T3.5 的**受控反向验证**（拿掉机制 → 5 个 DIFF；带机制 → 全 SAME） |

## 2. 使用增益（25 分）

| 评分点 | 分 | 本版机制 | 可复跑证据 |
|-|-|-|-|
| 质量增益 | 15 | 把六类"看不见的错误"变成机器判据：缺列不猜（**M1-F6**）、空值计数不补造、图例-系列一一对应（fail 阻断）、中文回退链、量级异常只 warn、显著性缺配对 fail。**本版把这些判据与四个机制建立了归属关系**，因此"为什么它能防住这类错误"是可追溯的 | `validation.json` 八类检查；`references/failure-modes.md` 的 G-M1..G-M4 分组；T3.1–T3.3 |
| 效率增益 | 5 | 一次调用走完全链路；**M2 的声明式规格**让"改样式 = 改预设键"（加期刊 = 加键，不改代码）；**M3 的单一场景**让"改一处不必改两处"（含 PDF 归一化只需在一处修） | `SKILL.md` §5 命令；`MECHANISM.md` §2.4 / §3.4；T6（1.51 s / 11 产物） |
| 增益可验证性 | 5 | 本版一并保留 **B 轴资产**：`references/GAIN-PROTOCOL.md`（6 条公平性条件 + 12 项指标 + 实测 A 1/12 · B 12/12）+ `examples/{baseline_agent,measure_ab}.py`。**并且本版把它用在了自己的机制上** —— T3.5 的受控反向验证就是这套方法的应用 | `GAIN-PROTOCOL.md` §3–§5；`TEST.md` T5；**T3.5 的受控对照表** |

> 本版不声称任何"提升百分比"；`GAIN-PROTOCOL.md` §6 明确列出本协议**不做的事**。

## 3. 创新增益（15 分）— 本版主攻维度

| 评分点 | 分 | 本版机制 | 可复跑证据 |
|-|-|-|-|
| 新增能力 | 5 | ① **M1 三向闭合**（图元↔manifest↔源表值，程序核对而非人工抽查）；② **M2 声明式规格 + 生成门**；③ **M3 单一场景双端输出**（矢量与位图逐元素同源，文字永不转曲）；④ **M4 契约四形态回显 + 确定性归一化**（禁 null、时间戳归一化让 sha256 成为证据）；⑤ 中文标注与字体回退 | `MECHANISM.md` 四个机制各有"实现落点"表 + 复验命令；T3.1–T3.5 |
| 方法改进 | 5 | **本版的方法改进不是新增功能，而是"把机制说清楚并给出边界"**：`MECHANISM.md` §5 给出四机制的**咬合图**与"拿掉任何一个的连带损失"表；§6 给出相对**通用绘图库 / 现成模板 / 一次性脚本**的**边界对照表**（含"本包不声称的"一列） | `MECHANISM.md` §5 / §6；`SKILL.md` §10 的限制段 |
| 创新证据 | 5 | ① **受控反向验证**：拿掉 M4② → 稳定复现 5 个 DIFF，恢复 → 全 SAME（同一实验、只切换一个变量）；② **被实测推翻的假设**：复用演练第一次**失败**（`ModuleNotFoundError: figcheck`），据此把"最小集合"从 3 个脚本修正为全部 10 个脚本；③ 边界写明（含 `spec_lint` 不查列存在性的实测确认，T3.2） | `TEST.md` T3.5 / **T4.1（失败记录）** / T3.2；`MECHANISM.md` §4.5；`REUSE-KIT.md` §2 路径一的"⚠ 实测修正" |

## 4. 可靠体验（10 分）

| 评分点 | 分 | 本版机制 | 可复跑证据 |
|-|-|-|-|
| 调用与易用性 | 3 | 单一入口 `main.py`；**任意 cwd 可运行**（自定位 + bash/PowerShell 双写法）；`case.json` 多形态兼容；`task.md` 自动发现；契约四形态自动回显；**10 个参数成表**（`README.md` §2.1）；**6 个脚本退出码成表**（§2.2） | `SKILL.md` §3；`README.md` §2；T2（cwd ≠ 技能根仍 exit 0） |
| 运行稳定性 | 4 | 单图失败不阻塞其他图（`status=partial`）；Pillow 缺失保 SVG + 全部 JSON；模板缺失回退内置默认；**M4② 使确定性真正成立**（含受控反向验证） | `TEST.md` T3.5（受控对照）· T7（异常路径） |
| 异常处理 | 3 | `references/failure-modes.md` **按"破坏哪个机制"分组**为 G-M1(7) / G-M2(6) / G-M3(6) / G-M4(9) / G-X(13)，共 **41 条分支**，每条给出触发条件、检出点、处置、落痕、复验命令；这样分组使分支表**可直接当验收清单用**（担心哪个机制就看哪一组） | `references/failure-modes.md` 全表；`SKILL.md` §7；T7 |

## 5. 生态贡献（10 分）— 本版主攻维度

| 评分点 | 分 | 本版机制 | 可复跑证据 |
|-|-|-|-|
| 文档完整性 | 3 | `SKILL.md`（机制主张 / M1–M4 / 咬合图 / 链路 E0–E8 / 规则按机制分组 / 失败分支按机制分组 / 复用索引 / 限制）· `README.md`（依赖 / 参数 / 退出码 / **复核命令↔机制对应表** / 维护表含两条一致性铁律 / **§6 三条复用路径的可操作版本**）· `TEST.md`（机制逐条实测 + **含失败记录的复用演练** + 7 条未解决项）· `REFINEMENT-NOTES.md` · `references/` **九份** · `templates/` 四份 | 包内文件清单（全部 UTF-8 文本）；`check_contract.py` 用机器可读契约块自查 |
| 资源可复用性 | 4 | ★ `references/REUSE-KIT.md`：资产按 **A 级（复制即用）/ B 级（换数据换键即用）/ C 级（需理解机制后改造）** 三级分级，每项标注**前置条件**；三条复用路径（10 分钟 / 30 分钟 / 1 小时）各有**验收标准**；**十条验收清单**；**不要带走的五项**。并且路径一的**最小脚本集合经实测修正**（3 → 10），失败记录保留在文档里 | `REUSE-KIT.md` §1–§4；**T4.1/T4.2 的两次演练实测** |
| 分享推广价值 | 3 | 适用于「数据表/生物源材料 → 投稿级可编辑图」的一般场景；**更重要的是四个机制与三套方法论可整段迁移**：机制四段写法（是什么 → 常规做法 → 没有它会怎样 → 落点与复验）、失败分支按"破坏哪个机制"分组、复用资产 A/B/C 分级 + 三路径 | `MECHANISM.md` §7（四个机制迁移到别的题的形态表）；`REUSE-KIT.md` §5；`GAIN-PROTOCOL.md` §8 |

## 6. GitHub 公开作品链接（5 分，附加）

- 根路径 `GITHUB_URL.txt` 第一行是公开仓库中本题作品的目录链接（无需登录可打开），
  第二行是本提交目录内的相对入口文件。
- 评审无需登录即可打开并找到本次提交的作品 → 得 5 分；缺交或链接无效 → 0 分。

## 7. 提交前自查（命令级）

```bash
SKILL_DIR=/skills/weekly-skill; OUT=<临时输出目录>

python "$SKILL_DIR/scripts/main.py"           --case "$SKILL_DIR/examples/case.json" --out "$OUT" --style nature
python "$SKILL_DIR/scripts/spec_lint.py"      --spec "$SKILL_DIR/examples/case.json" --case "$SKILL_DIR/examples/case.json"
python "$SKILL_DIR/scripts/mapcheck.py"       --dir "$OUT" --case "$SKILL_DIR/examples/case.json"
python "$SKILL_DIR/scripts/figcheck.py"       --dir "$OUT" --case "$SKILL_DIR/examples/case.json"
python "$SKILL_DIR/scripts/verify_rerun.py"   --case "$SKILL_DIR/examples/case.json" --out "$OUT"
python "$SKILL_DIR/scripts/check_contract.py" --result "$OUT/result.json" --case "$SKILL_DIR/examples/case.json"
```

| # | 检查 | 对应维度 | 期望 |
|-|-|-|-|
| 1 | `main.py` 退出码与 `result.json.status` | 实际效果 | `0` + `completed` |
| 2 | `spec_lint.py` | 创新（M2） | exit 0 |
| 3 | `mapcheck.py` | 创新（M1）/ 实际效果 | `mismatched=0 unmatched=0` |
| 4 | `figcheck.py` G1–G8 + 六类检查点 | 实际效果 / 创新（M3） | 全 OK，exit 0 |
| 5 | `verify_rerun.py` | 创新（M4②）/ 可靠体验 | `DETERMINISTIC`，exit 0 |
| 6 | `check_contract.py` | 创新（M4①） | `PASS`，`missing=0 null=0` |
| 7 | `MECHANISM.md` 的复验命令 ↔ 实际 CLI | 创新 / 生态 | 逐字一致，无"文档命令跑不通" |
| 8 | `REUSE-KIT.md` §3 验收清单 ↔ 实际包内文件 | 生态 | 清单里的文件名都存在，前置条件写明 |
| 9 | `references/failure-modes.md` 分组 ↔ `SKILL.md` §7 | 可靠体验 | G-M1..G-M4 + G-X 一致 |
| 10 | `GITHUB_URL.txt` | 附加 5 分 | 未登录可访问且指向本题作品 |
