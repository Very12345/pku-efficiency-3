# REUSE-KIT.md — 可复用资产清单与复用步骤

本文件回答"生态贡献"里的两问：**哪些东西别人能直接拿走用**，以及**怎么拿**。
所有路径都相对本包根目录（`$SKILL_DIR`）；参数名与 `scripts/*.py --help` 逐字一致。

## 1. 资产总览

| # | 资产 | 路径 | 依赖 | 可独立使用 | 适合谁 |
|-|-|-|-|-|-|
| A | 叙事配置（块/权重/顺序/问答模板） | `templates/talk_config.json` | 无（纯 JSON） | ✅ 只改配置即改行为 | 想复用"按听众与时长换页序"的人 |
| B | 计划契约模式（P1–P8 的单点真相） | `assets/plan.schema.json` | 无 | ✅ 可照抄成自己的校验条款 | 做同类"先计划后生成"工具的人 |
| C | 题集骨架（三种汇报的输入模板） | `assets/case-set.json` | 无 | ✅ 复制改字段即可 | 要造新案例/新题的人 |
| D | 页级金标准（结构版） | `assets/page-gold-standard.json` | 无 | ✅ 结构判定 + 人工复核清单 | 评审、对照实验、回归测试 |
| E | 校验清单（上台前 / 提交前 / 质量门） | `templates/slide-checklist-template.md`、`references/quality-gates.md`、`SKILL.md` §6 | 无 | ✅ 打印即用 | 讲者本人、提交前自检 |
| F | 导出预设（预览与 deck 的实测默认值） | 本文件 §6（与 `scripts/render.py`、`scripts/deck_builder.py` 一致） | 无 | ✅ 参数表 | 要复刻本包渲染效果的人 |
| G | 配色与版式规范 | 本文件 §7、`references/deck-rules.md` | 无 | ✅ 色值与命名可直接抄 | 要统一视觉/做模板的人 |
| H | 证据审计器 | `scripts/evidence_audit.py` | Python（无第三方） | ✅ 独立 CLI | 任何"页面必须有出处"的产物 |
| I | 对照装置（A/B 度量器） | `scripts/gain_ab.py` | python-pptx（读 deck） | ✅ 换 `--case` 即可量别的 Skill | 要做公平对照的参赛者/研究者 |
| J | 指标口径文档 | `references/GAIN-PROTOCOL.md` | 无 | ✅ 可裁剪 | 同上 |
| K | 状态一致性检查器（v1 同源思路） | 见 `references/failure-modes.md` §6 的规则集 | 无 | ✅ 规则可移植 | 任何有 `status` 字段的产物 |
| L | 失败模式与分支族 | `references/failure-modes.md` | 无 | ✅ 表格可直接改题 | 做可靠性设计的人 |

## 2. 资产 A/B/C/D 的用法（换题不改码）

```bash
# 1) 取一个题集骨架 → 变成自己的 case.json
cp "$SKILL_DIR/assets/case-set.json" /tmp/case-set.json     # 读 §templates 里任一条
#    填 case_id / title / report_goal / materials 的真实路径，保留 output_contract

# 2) 想换叙事策略：只改配置，不改代码
#    templates/talk_config.json 里每个 report_type 的 blocks（权重/顺序）与 qa 模板

# 3) 想换计划门条款：改 assets/plan.schema.json（P1–P8 的驱动源）
python "$SKILL_DIR/scripts/validate_plan.py" <out>/talk_plan.json --materials-dir <材料目录>

# 4) 按页级金标准做结构复核（assets/page-gold-standard.json 的 machine_checks）
python "$SKILL_DIR/scripts/verify_deck.py" <out>/editable_deck.pptx --expect-pages <N> --plan <out>/talk_plan.json
```

## 3. 资产 H/I/J 的用法（把"可核验"打包带走）

```bash
# 任何产出"页/条目 + 出处"的 Skill 都能用证据审计器（只要求 result.json 形状）
python "$SKILL_DIR/scripts/evidence_audit.py" <out>/result.json
python "$SKILL_DIR/scripts/evidence_audit.py" <out>/result.json --sources-dir <材料目录> --out <复读报告.json>

# 对另一个 Skill 做同一把尺子的对照：把它的产物放进 arm-B 形态，或直接量它的目录
python "$SKILL_DIR/scripts/gain_ab.py" --case <case.json> --work <RUN>/gain --skill-dir "$SKILL_DIR"
python "$SKILL_DIR/scripts/gain_ab.py" --case <case.json> --work <RUN>/gain-A --skip-arm-b   # 只量基线臂
```

> `gain_ab.py` 不 import 本包任何模块、只读产物；指标定义写在 `references/GAIN-PROTOCOL.md` §4。
> 换到别的题目时，需要替换的只有 §4 的指标集合与 A 臂模拟器，度量与记录管线可原样复用。

## 4. 资产 E/L 的用法（把清单直接搬走）

- `templates/slide-checklist-template.md`：上台前逐页核对（人核）；
- `references/quality-gates.md`：G1–G10 全链路收口，其中 G10 就是题面资源硬门；
- `SKILL.md` §6 的收尾清单：**每条都给了机器判定方式**，可直接作为提交前自检表；
- `references/failure-modes.md`：五族分支（材料/模板/依赖/契约/状态）+ 状态一致性规则，
  改掉示例文字即可用于别的 Skill 包。

## 5. 三个典型复用场景（逐步命令）

**场景 1：只想复用"按听众与时长排页序"（不动整条流水线）**

```bash
# a) 抄 assets/plan.schema.json 的条款与 templates/talk_config.json 的块定义
# b) 在自己管线里实现两步：听众 → 背景比例；时长 × 每页秒数 → 页预算 → 校准冻结页数
# c) 用 references/quality-gates.md 的 G4（计划门）做回归
```

**场景 2：接进已有管线（把本包当"计划 + 审计"两段）**

```bash
# a) 用 scaffold_plan/validate_plan 产出并校验 talk_plan.json（不生成 deck 也能用）
python "$SKILL_DIR/scripts/validate_plan.py" <你的 out>/talk_plan.json --materials-dir <材料>
# b) 你自己的渲染器负责出页；交付前用 evidence_audit.py 审"页面主张 ↔ 源材料"
python "$SKILL_DIR/scripts/evidence_audit.py" <你的 out>/result.json
```

**场景 3：当作对照基线（量别人，或让别人量你）**

```bash
# a) 完整对照（A 臂模拟器 + B 臂本包）
python "$SKILL_DIR/scripts/gain_ab.py" --case <case.json> --work <RUN>/gain --skill-dir "$SKILL_DIR"
# b) 只跑 A 臂，然后把你自己的产物按同样目录形态放进 arm-B 的位置，用同一度量函数比对
python "$SKILL_DIR/scripts/gain_ab.py" --case <case.json> --work <RUN>/gain-A --skip-arm-b
# c) 记录随包：把 gain_report.json 与 GAIN-PROTOCOL.md 一起提交，别人即可复算
```

## 6. 导出预设（与代码里的实测默认值一致）

| 项 | 值 | 出处 |
|-|-|-|
| deck 画布 | 16:9，13.333 in × 7.5 in（`Inches(13.333)` × `Inches(7.5)`） | `scripts/deck_builder.py` |
| 预览画布 / 缩略图 | 1280 × 720 / 960 × 540 px | `scripts/render.py`（`CANVAS_W/H`、`THUMB_W/H`） |
| 预览形态 | 逐页缩略图 + 封面 + 网格（`--skip-previews` 可只留封面与网格） | `scripts/main.py` / `render.py` |
| 预览水印 | 每张 PNG 带「PIL 模拟预览」标注 | `scripts/render.py` |
| 字体（deck） | 西文 `Arial`、中文 `Microsoft YaHei`（运行环境缺字体时由 Office 侧回退） | `scripts/deck_builder.py`（`FONT_LATIN`/`FONT_CJK`） |
| 字体（预览） | 运行时探测：`C:/Windows/Fonts/msyh.ttc` → … → `/usr/share/fonts/...` → `/System/Library/Fonts/...`；找不到用 Pillow 内置位图字体并记明 | `scripts/render.py::FONT_CANDIDATES/font_status` |
| 元素命名 | `page-title-NN` / `page-claim-NN` / `page-figure-NN` / `page-footer-NN` / `cover-meta` / `master-accent-bar` | `scripts/deck_builder.py` |
| 常用开关 | `--skip-previews`（省时间）、`--quiet`（少输出）、`--template`（显式模板） | `scripts/main.py --help` |

## 7. 配色与版式规范（可直接抄）

| 用途 | 色值 | 出处 |
|-|-|-|
| 主色（页眉/底栏） | `#1F4E79` | `deck_builder.PRIMARY` / `render.PRIMARY` |
| 强调色 | `#C0504D` | `ACCENT` |
| 正文深色 / 次要灰 | `#262626` / `#5A5A5A` | `DARK` / `GRAY` |
| 浅底（引用块） | `#F2F5F9` | `LIGHT` |
| 证据强度标记 | strong `#2E7D32`、medium `#C07F00`、weak `#8A8A8A` | `STRENGTH_COLOR` |

版式约定：母版底部 0.22 in 强调条；正文区左起 0.5 in；每页右下角页脚含页码与会话标识；
引用块用于承载【证据】行（缩略图与 deck 同构）。细则见 `references/deck-rules.md`。

## 8. 复用时的注意事项与已知坑

1. **不要在包内直接跑脚本**：会生成 `__pycache__`，平台预检判为非法二进制 —— 复制到包外再跑；
2. **契约字段禁 `null`**：复用 `apply_contract` 的思路时，缺失按容器类型给 `""/[]/{}/0/False`；
3. **模板自带页必须丢弃**：否则最终页数 = 冻结页数 + 自带页数（见 `MECHANISM.md` M5）；
4. **预览不是 Office 渲染**：只用于"布局可检查"，别把它写进验收口径；
5. **对照片面的对称性**：A 臂只读 case 显式声明的材料，而本包会扫描材料目录（`GAIN-PROTOCOL.md` §8 第 3 条），
   做对照时要么双方都扫，要么双方都不扫；
6. **状态三处记录**：`status` + `uncertainty` + `change_records`，缺一即"静默降级"。

## 9. 复用产出如何自证

```bash
python "$SKILL_DIR/scripts/validate_result.py" <out>/result.json      # 结构/文件/数字
python "$SKILL_DIR/scripts/check_contract.py"  <out>/result.json      # 契约字段与类型
python "$SKILL_DIR/scripts/evidence_audit.py"  <out>/result.json      # 逐页逐字引文
python "$SKILL_DIR/scripts/verify_deck.py" <out>/editable_deck.pptx --expect-pages <N> --plan <out>/talk_plan.json
python "$SKILL_DIR/scripts/selftest.py" <out> --package-check "$SKILL_DIR"   # G1–G10 + 包约束
python "$SKILL_DIR/scripts/gain_ab.py" --case <case.json> --work <RUN>/gain --skill-dir "$SKILL_DIR"   # 对照
```

六条命令的退出码语义统一：**0 = 通过**；非 0 时报告里逐条给出字段与实测值。
