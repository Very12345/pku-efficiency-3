# academic-talk-organizer v2 · challenge-20870c35（学术汇报内容组织 · slides 组）

把**已有**的论文/研究材料组织成：结构清楚、证据可追溯、可编辑、符合听众/时长/模板约束的学术汇报产物。
本包是「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35 的 Skill 交付物 v2（加强包）；
`SKILL.md` 为 Skill 本体（Agent 加载入口），`scripts/`、`templates/`、`assets/`、`references/`、
`examples/` 为运行必需的脚本与资源。v2 相对 v1 基包的增强点见 [COMPARE.md](COMPARE.md)，
实测记录见 [TEST.md](TEST.md)。

## 一、运行方法

```bash
# 1) 最小调用（示例案例 → 示例输出，本机已实跑）
python scripts/main.py --case examples/case.json --out examples/output

# 2) 平台运行期形态（等价于 /input、/app/output）
python3 scripts/main.py --case /input/case.json --task /input/task.md --out /app/output

# 3) 显式指定材料目录 / 模板 / 跳过逐页缩略图
python scripts/main.py --case case.json --out out --materials ./materials \
       --template ./template.pptx --skip-previews

# 4) 独立复核（全部退出码 0 = 通过）
python scripts/validate_result.py out/result.json
python scripts/check_contract.py  out/result.json
python scripts/evidence_audit.py  out/result.json
python scripts/verify_deck.py out/editable_deck.pptx \
       --expect-pages <N> --plan out/talk_plan.json
python scripts/selftest.py out --package-check <skill-root>   # G1–G10 全链路
```

> 所有脚本用 `os.path.dirname(__file__)` 自定位，运行命令不依赖当前目录；
> 平台把 Skill 装在 `/skills/weekly-skill` 时，把 `scripts/main.py` 换成
> `"$SKILL_ROOT/scripts/main.py"` 即可（`SKILL_ROOT`= 含 SKILL.md 的目录）。

## 二、输入输出

**输入**：`case.json`（case_id / report_goal / audience / duration_min / slide_count /
report_type / materials / template·start_deck / figure_files / output_contract）+ `task.md` + 材料
（md/txt/PDF 与图片）。脚本**实际读取文件**，不按标签预设内容；材料目录缺省为 `<case 目录>/materials`。

**输出**（契约见 `references/OUTPUT_CONTRACT.md`）：

```
result.json            # 主结构 + status/sources/uncertainty/change_records + audit{plan_gates,evidence,deck,gates}
talk_plan.json         # 页级计划（可编辑中间产物）
plan_gates.json        # 计划契约门 P1–P8（assets/plan.schema.json 驱动）
evidence_map.json      # 源文件 → {页, 图表引用} 反向映射
evidence_audit.json    # 逐页逐字引文审计
deck_audit.json        # deck 机器校验（打开/页数/备注/claim 元素/OPC/规范化 sha）
editable_deck.pptx     # 可编辑演示文件（模板适配或内置主题，确定性元素命名）
previews/              # cover_preview.png / slide_NNN.png / preview_grid.png / preview_manifest.json
self_check.json        # validate + contract + 门快照 + 确定性探针
```

## 三、依赖

| 依赖 | 用途 | 版本要求 |
|-|-|-|
| Python | 解释器 | ≥ 3.8（本机验证 3.13.9） |
| python-pptx | 可编辑 .pptx 生成/模板适配 | 1.0.2（验证） |
| Pillow | PNG 预览渲染 | 12.x（验证；≥8 支持 anchor 参数） |
| pypdf（可选） | PDF 文本抽取 | 6.x（验证）；缺失时如实降级为「未解析」 |
| reportlab（仅示例生成） | 生成本包示例 PDF | 5.0（本机验证，非运行必需） |

无网络依赖、无 cwd 依赖、不调用 LibreOffice/PowerPoint（预览为 PIL 模拟，如实标注）。

## 四、核心流程（v2）

1. **CP1 输入契约**：读 case.json/task.md/材料/模板，output_contract 归一；
2. **CP2 计划门**：`scaffold_plan` 生成页级计划 → `validate_plan` 按
   `assets/plan.schema.json` 执行 P1–P8（含冻结页数校准）；
3. **CP3 生成门**：`deck_builder` 生成 .pptx（模板适配/内置主题 + 确定性元素命名）→
   `verify_deck` 校验（打开/页数/备注/命名/OPC）；
4. **CP4 渲染门**：`render` PIL 模拟预览（带水印 + manifest 限制说明）；
5. **CP5 审计收口门**：`evidence_audit` 逐字审计 → `finalize_result` 组装 result.json
   （契约四形态回显）+ self_check（validate/contract/门/确定性探针）。

决策规则 D1–D14 与检查点 CP1–CP5 见 `SKILL.md` §4/§6；失败模式全表 F1–F20 见
`references/FAILURE_MODES.md`；质量门 G1–G10 见 `references/QUALITY_GATES.md`。

## 五、与"基础 Agent 直接做"的差异（使用增益）

- 基础 Agent 典型表现：摘要/Results 逐段搬页、页数与时长脱节、图表与结论不对应、
  讲稿缺失、被追问无准备；
- 本包：叙事顺序/页预算按 `talk_config.json`（听众+时长驱动）+ 计划门强制；
  一页一主张 + 逐字引文 + 证据强度；每页备注【主张/证据/讲解/备答】；qa 备用页预埋追问；
  每次运行都产出可复核的审计链路（plan_gates / evidence_audit / deck_audit / self_check）。

## 六、限制与边界

- 不负责论文精读成稿、写作成稿与科研绘图素材生产（相邻课题承担）；
- PDF 无解析器时按「未解析」降级，相关证据弱化但不编造；
- 预览为 PIL 模拟渲染，正式视觉效果以 .pptx 打开为准；
- 证据定位是行级/章节级近似锚点，源材料变化后需复核引文。

## 七、GitHub

见 `GITHUB_URL.txt`（第一行仓库链接，第二行本作品相对路径）。