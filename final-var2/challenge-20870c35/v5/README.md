# academic-talk-organizer · v5 多案例泛化与题集版（challenge-20870c35 · 学术汇报内容组织）

把**已有**的论文/研究材料组织成：结构清楚、证据可追溯、可编辑、符合听众/时长/模板约束的学术汇报产物。
本包是「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35 的 Skill 交付物（**合规重打包版**）。

`SKILL.md` 为 Skill 本体（Agent 加载入口）；`scripts/`、`templates/`、`assets/`、`references/`、
`examples/`、`COMPARE.md` 为运行必需的资源与说明。实测记录见 [TEST.md](TEST.md)，
对照方案见 [COMPARE.md](COMPARE.md)，五维评分落点见 [references/RUBRIC_MAP.md](references/RUBRIC_MAP.md)。

## 本版新增：换题材、换汇报类型、换量级，看它还是不是同一个交付物

`examples/` 里的最小示例只有一个题材（NLP）。**单一案例跑通不等于能用** ——
本版另加两个**自包含的合成案例**，专门用来撞边界：

```bash
SKILL_DIR="<本包根目录>"; OUT="<包外空目录>"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/case-a-muon-defense/case.json" --out "$OUT/a"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/case-b-scrna-review/case.json"   --out "$OUT/b"
```

| 案例 | 题材 | 汇报类型 | 时长/页数 | 难度 | 考察点 |
|-|-|-|-|-|-|
| `case-a-muon-defense` | 凝聚态实验物理（μSR 反演） | `defense` 答辩 | 25 min / 15 页 | L2 | 数值证据链；局限靠前；图引用无文件→诚实占位 |
| `case-b-scrna-review` | 计算生物学（单细胞去噪） | `review` 评审 | 12 min / 8 页 | L3 | **结论先行**；**两个矛盾指标必须同页** |

- **逐案实测 + 可判定的期望结构 + 可接受区间**：[references/CASE-SET.md](references/CASE-SET.md) §2。
  两案实测均为 `exit 0` / `status=completed` / P-gates 8/8 / `evidence_audit.errors=0`。
- **同一文件 §4 专门写"泛化到哪里会失效"**，三条已实测的边界：
  ① 未知 `report_type` 被静默替换成组会模板（`agenda` 页消失）；
  ② `slide_count` 被硬钳制在 [6, 30] 且不报不确定度；
  ③ 纯英文材料能抽出主张却全部退化成概括页（**已修**：抽出 ≥3 条主张而全部内容页都是
  `derived` 时升级为 `status=partial` + 明确 `uncertainty`，并附两案回归证据）。
- **题集可整块复用**：每个案例是自包含目录，换 `materials/` 与描述字段即成新案例，**不需要改代码**。

> **资源形态**（题面 Runtime contract：*at most 50 UTF-8 text files, 500KB each and 2MB total,
> no symlinks*）：本包**只含 UTF-8 文本资源**（`.md/.py/.json/.txt/.csv/.yaml/.yml`）。
> 示例用到的 `.pdf` / `.png` 不随包提交，由 `scripts/make_synthetic_inputs.py` 在运行时现场生成；
> 可编辑 `.pptx` 与预览 `.png` 属于 **runtime artifacts**，同样由运行时产生。
> 包内不含任何本机绝对路径、`__pycache__`、符号链接。

## 一、运行方法

`$SKILL_DIR` = 本包根目录（含 `SKILL.md` 的目录；平台安装后即 `/skills/weekly-skill`）。
**所有脚本自定位**（`os.path.dirname(__file__)`），命令与当前 cwd 无关。

```bash
# 0) 示例专用：先生成运行时二进制输入（正式案例不需要，材料由平台提供）
python "$SKILL_DIR/scripts/make_synthetic_inputs.py"

# 1) 最小调用（示例案例 → 输出目录）
python "$SKILL_DIR/scripts/main.py" \
  --case "$SKILL_DIR/examples/case.json" --out "$OUT"

# 2) 平台运行期形态（等价于 /input、/app/output）
python "$SKILL_DIR/scripts/main.py" \
  --case /input/case.json --task /input/task.md --out /app/output

# 3) 显式指定材料目录 / 模板 / 跳过逐页缩略图
python "$SKILL_DIR/scripts/main.py" --case case.json --out out --materials ./materials \
       --template ./template.pptx --skip-previews

# 4) 独立复核（全部退出码 0 = 通过）
python "$SKILL_DIR/scripts/validate_result.py" "$OUT/result.json"
python "$SKILL_DIR/scripts/check_contract.py"  "$OUT/result.json"
python "$SKILL_DIR/scripts/evidence_audit.py"  "$OUT/result.json"
python "$SKILL_DIR/scripts/verify_deck.py" "$OUT/editable_deck.pptx" \
       --expect-pages <N> --plan "$OUT/talk_plan.json"
python "$SKILL_DIR/scripts/selftest.py" "$OUT" --package-check "$SKILL_DIR"   # G1–G10 全链路 + 包约束
```

**退出码**：`0` = 已产出通过 validate + contract 的 `result.json`（`status` 字段说明是 `completed`
还是 `partial`——诚实降级不会被当成崩溃）；`1` = 没有可用的契约结果；`2` = 参数用法错误。

## 二、输入输出

**输入**：`case.json`（case_id / report_goal / audience / duration_min / slide_count /
report_type / materials / template·start_deck / figure_files / output_contract）+ `task.md` + 材料
（md/txt/PDF 与图片）。脚本**实际读取文件**，不按标签预设内容；材料目录缺省为 `<case 目录>/materials`。

**输出**（契约见 [references/OUTPUT_CONTRACT.md](references/OUTPUT_CONTRACT.md)；
完整清单与示例实测数量见 [examples/EXPECTED-OUTPUT.md](examples/EXPECTED-OUTPUT.md)）：

```
result.json            # 唯一评分产物：契约字段 + status/sources/uncertainty/change_records/
                       #   environment + audit{plan_gates,evidence,deck,gates}
talk_plan.json         # 页级计划（可编辑中间产物）
plan_gates.json        # 计划契约门 P1–P8（assets/plan.schema.json 驱动）
evidence_map.json      # 源文件 → {页, 图表引用} 反向映射
evidence_audit.json    # 逐页逐字引文审计
deck_audit.json        # deck 机器校验（打开/页数/备注/claim 元素/OPC/规范化 sha）
editable_deck.pptx     # 可编辑演示文件（运行期产物）
previews/              # cover_preview.png / slide_NNN.png / preview_grid.png / preview_manifest.json（运行期产物）
self_check.json        # validate + contract + 门快照 + 确定性探针
```

`result.json` 里的路径一律**可移植**：写盘时把本机绝对路径（`X:\...`/UNC）改写成相对案例目录的形式
（如 `materials/fig2.png`），POSIX 运行期路径（`/input/...`、`/app/...`）原样保留。

## 三、依赖

| 依赖 | 用途 | 版本要求 | 缺失时 |
|-|-|-|-|
| Python | 解释器 | ≥ 3.8（本机验证 3.13.9） | — |
| python-pptx | 可编辑 `.pptx` 生成/模板适配 | 1.0.2（验证） | 跳过 deck，`status=partial`，其余产物照常（命令仍返回 0） |
| Pillow | PNG 预览、图片校验（python-pptx 亦依赖它） | 12.x（验证；≥8 支持 `anchor`） | 跳过预览（非致命）；python-pptx 亦不可用 |
| pypdf / PyPDF2（可选） | PDF 文本抽取 | 6.x（验证） | PDF 记 `parsed=false` 并降级 `partial` |
| （无） | `make_synthetic_inputs.py` 零第三方依赖 | — | — |

无网络依赖、无 cwd 依赖、不调用 LibreOffice/PowerPoint（预览为 PIL 模拟并如实标注）。

## 四、核心流程

1. **CP1 输入契约**：读 case.json/task.md/材料/模板；output_contract 归一；**环境预检**（依赖 + 中文字体）；
2. **CP2 计划门**：`scaffold_plan` 生成页级计划 → `validate_plan` 按 `assets/plan.schema.json`
   执行 P1–P8（含冻结页数校准）；
3. **CP3 生成门**：`deck_builder` 生成 `.pptx`（模板适配则复用母版/版式并丢弃自带示例页；否则内置主题）
   → `verify_deck` 校验（打开/页数/备注/命名/OPC）；
4. **CP4 渲染门**：`render` PIL 模拟预览（带水印 + manifest 限制说明 + 字体探测结果）；
5. **CP5 审计收口门**：`evidence_audit` 逐字审计 → `finalize_result` 组装 result.json
   （契约四形态回显 + environment）与 self_check。

决策规则 D1–D17 与检查点 CP1–CP5 见 `SKILL.md` §4/§6；失败模式全表 F1–F26 见
[references/failure-modes.md](references/failure-modes.md)；质量门 G1–G10 见
[references/quality-gates.md](references/quality-gates.md)。

## 五、与"基础 Agent 直接做"的差异（使用增益）

- 基础 Agent 典型表现：摘要/Results 逐段搬页、页数与时长脱节、图表与结论不对应、
  讲稿缺失、被追问无准备；
- 本包：叙事顺序/页预算按 `templates/talk_config.json`（听众+时长驱动）+ 计划门强制；
  一页一主张 + 逐字引文 + 证据强度；每页备注【主张/证据/讲解/备答】；`qa` 备用页预埋追问；
  每次运行都产出可复核的审计链路（plan_gates / evidence_audit / deck_audit / self_check / environment）。
- 逐条可判定的差异点与 A/B 口径见 [COMPARE.md](COMPARE.md)（并列出**不利于本包**的对照结果）。

## 六、限制与边界

- 不负责论文精读成稿、写作成稿与科研绘图素材生产（相邻课题承担）；
- PDF 无解析器时按「未解析」降级，相关证据弱化但不编造；
- 预览为 PIL 模拟渲染，正式视觉效果以 `.pptx` 打开为准；
- 证据定位是行级/章节级近似锚点，源材料变化后需复核引文；
- 模板适配会丢弃起始演示文件自带的示例页，以保证页数等于冻结值（记录在 `change_records`）。

## 七、维护与更新

- 改行为：`templates/talk_config.json`（页权重/顺序/问答模板/deck_rules）、
  `assets/plan.schema.json`（计划门条款）——**改配置即改行为，不必改代码**；
- 改规则文字：`references/*.md`（契约/门/失败模式/版式规则）；
- 回归自测：按 [TEST.md](TEST.md) 的 T1–T13 顺序跑一遍（含六条降级/失败分支的负例），
  期望：除 T12（`case.json` 不可读，应为 1）外全部退出码 0；
- 提交前：`selftest.py <out> --package-check "$SKILL_DIR"` 必须全 ✓，且包内无 `__pycache__`、无二进制残留。

## 八、GitHub

见 `GITHUB_URL.txt`（第一行仓库链接，第二行本作品相对路径）。
