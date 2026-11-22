# academic-talk-organizer · v3 机制与复用版　（challenge-20870c35 · 学术汇报内容组织）

把**已有**科研材料组织成"可讲、可编辑、证据可追溯"的学术汇报产物。
本版把包里**不可省略的机制**与**可被别人整块拿走的资产**都写明：
机制各有一条"没有它会怎样"和可证伪判据；资产各有入口、依赖与复用步骤。

- Skill 本体：[SKILL.md](SKILL.md)（八机制总览 / 机制×阶段×字段 / 降级 / 核对清单）
- **机制说明**：[references/MECHANISM.md](references/MECHANISM.md)（M1–M8 + 连锁效应 + 实测证据）
- **复用清单与步骤**：[references/REUSE-KIT.md](references/REUSE-KIT.md)（题集 / 金标准 / 清单 / 导出预设 / 配色）
- 对照协议与实测：[references/GAIN-PROTOCOL.md](references/GAIN-PROTOCOL.md) + [references/gain-run-record.json](references/gain-run-record.json)
- 字段契约：[references/OUTPUT_CONTRACT.md](references/OUTPUT_CONTRACT.md)　·　五维映射：[references/RUBRIC_MAP.md](references/RUBRIC_MAP.md)
- 实测命令与观测：[TEST.md](TEST.md)　·　对照方法论：[COMPARE.md](COMPARE.md)

> **资源形态**（题面 Runtime contract：*at most 50 UTF-8 text files, 500KB each and 2MB total,
> no symlinks*）：本包只含 UTF-8 文本资源（`.md/.py/.json/.txt/.csv/.yaml/.yml`）；
> `.pptx`/`.png`/`.pdf` 一律运行期生成；包内无本机绝对路径、无 `__pycache__`、无符号链接。

## 一、快速开始

`$SKILL_DIR` = 含 `SKILL.md` 的目录（平台安装后即 `/skills/weekly-skill`）。脚本自定位，cwd 任意。

```bash
# 1) 主流程
python "$SKILL_DIR/scripts/make_synthetic_inputs.py"                 # 示例专用：生成运行时输入
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out "$OUT"

# 2) 复核（全部退出码 0 = 通过）
python "$SKILL_DIR/scripts/validate_result.py" "$OUT/result.json"
python "$SKILL_DIR/scripts/check_contract.py"  "$OUT/result.json"
python "$SKILL_DIR/scripts/evidence_audit.py"  "$OUT/result.json"
python "$SKILL_DIR/scripts/verify_deck.py" "$OUT/editable_deck.pptx" \
       --expect-pages <N> --plan "$OUT/talk_plan.json"
python "$SKILL_DIR/scripts/selftest.py" "$OUT" --package-check "$SKILL_DIR"
```

## 二、★ 复用步骤（三条主线，逐步可跑）

> 资产总览、依赖与注意事项见 [references/REUSE-KIT.md](references/REUSE-KIT.md)；
> 下面只给"最短可用路径"。

**主线 1：只复用"按听众与时长排页序"（不接管整条流水线）**

```bash
# a) 取叙事配置与计划模式作为参考（纯 JSON，可直接抄进你的项目）
#    → templates/talk_config.json（report_type → 块/权重/顺序/问答模板）
#    → assets/plan.schema.json（P1–P8 条款：冻结页数、证据定位、强度词法）
# b) 在你的管线里实现两步：听众 → 背景比例；时长 → 页预算 → 校准冻结页数
# c) 用 references/quality-gates.md 的 G4（计划门）做回归
```

**主线 2：把本包当"计划 + 审计"两段接进已有管线**

```bash
# a) 只产出并校验计划（不需要本包的 deck 生成）
python "$SKILL_DIR/scripts/validate_plan.py" <你的 out>/talk_plan.json --materials-dir <材料目录>
# b) 交付前审"页面主张 ↔ 源材料"是否逐字可回溯
python "$SKILL_DIR/scripts/evidence_audit.py" <你的 out>/result.json
#    需要离开运行期复读时：--sources-dir <材料目录> --out <复读报告.json>
```

**主线 3：做公平对照（量别人，或让别人量你）**

```bash
# a) 完整对照：A 臂（内置基线模拟器）+ B 臂（本包 main.py），同一把尺子
python "$SKILL_DIR/scripts/gain_ab.py" --case <case.json> --work <RUN>/gain --skill-dir "$SKILL_DIR"
# b) 只跑 A 臂，然后把你自己的产物按同样目录形态放进 arm-B，用同一指标口径比对
python "$SKILL_DIR/scripts/gain_ab.py" --case <case.json> --work <RUN>/gain-A --skip-arm-b
# c) 随包提交 gain_report.json 与 GAIN-PROTOCOL.md，别人即可复算（含不利结果）
```

**附：题集与金标准**（造新案例 / 做结构回归时）

```bash
# a) assets/case-set.json 里三种汇报的输入骨架，复制一条填 case_id/title/materials 即为新案例
# b) assets/page-gold-standard.json 给出每类汇报的块顺序与每页必填字段，并附机器判定命令
python "$SKILL_DIR/scripts/verify_deck.py" "$OUT/editable_deck.pptx" --expect-pages <N> --plan "$OUT/talk_plan.json"
```

## 三、依赖

| 依赖 | 用途 | 缺失时 |
|-|-|-|
| Python ≥ 3.8（本机 3.13.9 实测） | 解释器 | — |
| `python-pptx`（1.0.2 实测） | 生成/适配可编辑 `.pptx`；对照装置读 deck | 跳过 deck，`status=partial`，其余产物照常，**命令仍返回 0** |
| `Pillow`（12.3.0 实测） | PNG 预览、图片校验 | 跳过预览（非致命） |
| `pypdf` / `PyPDF2`（6.14.2 实测，可选） | PDF 文本抽取 | PDF 记 `parsed=false` 并降级 |

## 四、限制与边界

- 不负责论文精读成稿、写作成稿、科研绘图素材生产；
- 预览是 Pillow 模拟渲染（带水印），不是 Office 栅格化；
- 证据定位是行级/章节级近似锚点，源材料更新后需按引文复核；
- 模板适配会丢弃起始演示自带页以保证页数等于冻结值（记入 `change_records`）；
- 对照是单案例、单机的机制与可测性证据，**不是平台白板、不是平台分数**；
- `assets/case-set.json` 与 `assets/page-gold-standard.json` 只给**输入骨架与结构标准**，
  不含任何案例的内容答案，不得当作正式案例的作答使用。

## 五、维护

- 改行为：`templates/talk_config.json`、`assets/plan.schema.json`（改配置即改行为）；
- 改机制描述：`references/MECHANISM.md`（每条机制的落点必须能在代码里指到）；
- 改资产清单：`references/REUSE-KIT.md` §1（表格增删要与实际文件一致）+ 本 README 第二节；
- 改对照口径：`references/GAIN-PROTOCOL.md` §4 与 `scripts/gain_ab.py` 必须同步改；
- 本版新增文件：`references/{MECHANISM.md,REUSE-KIT.md,GAIN-PROTOCOL.md,gain-run-record.json}`、
  `assets/{case-set.json,page-gold-standard.json}`、`scripts/gain_ab.py`；
  其余文件的算法与 CLI 接口与基线一致。

## 六、GitHub

见 `GITHUB_URL.txt`（第一行为作品在仓库中的目录链接）。
