# Task — EXAMPLE workorder（示例任务书，非正式案例）

Source: `sources/figure03-note.md`（合成演示材料）。

请完成一次完整的"来源材料 → 可编辑图稿 → 合规导出"：

1. 通读 `sources/figure03-note.md`（标题字段只作标识，以文件实际内容为准）。
2. 从材料提取实体、关系、分组与图例要求，形成 ER 清单
   （本示例的 `case.json` 已含一份完整 `manifest`，可直接运行；
   正式案例中由 Agent 在 `/app/work/entities.json` 现场抽取）。
3. 运行流水线脚本（`$SKILL_DIR` = 本 SKILL.md 所在目录，任意 cwd 可跑）：
   ```
   python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/sse-task
   ```
   期望产物清单见 `EXPECTED-OUTPUT.md`（包内不预置任何图稿/渲染件）。
4. 核对生成物：`figure.svg`（可编辑分层源文件）、`figure.png`、
   `figure.pdf`、`result.json`；检查项全部记录在 result.json 的
   `verification.checks`。
5. 如实填写/确认 `uncertainty` 与 `change_records`，不编造数据。

验收要点（与本 Skill 的自查清单一致）：
- 实体名可逐一到 `sources/figure03-note.md` 溯源；箭头的激活/抑制/转录
  方向与 §3.1 一致（RIPK1→NF-κB 是激活，不是抑制）；
- 图例三项与图面实际使用的箭头类型一一对应，无缺项无孤儿项；
- 导出件 PNG 打印 DPI、SVG 文字可编辑性检查通过。

> 本示例输出全部标注"示例，非正式案例"，不可作为正式测试案例或
> 预置答案提交。