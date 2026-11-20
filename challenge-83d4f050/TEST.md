# TEST.md —— 本机实测记录

本文件记录本 Skill 包在本地（Windows / Python 3.13.9 / Anaconda）的真实测试命令与结果。
测试时间：2026-11-20 22:1x（Asia/Shanghai）。所有路径均可在本仓库根目录 `build/challenge-83d4f050/` 下复现。

## 0. 环境

- 系统：Windows（Git for Windows Bash）；Python 3.13.9（Anaconda）。
- 关键包：matplotlib 3.10.6（可用）、Pillow 12.3.0、reportlab 5.0.0、numpy 2.3.5；
  cairosvg / svgwrite **不可用**（本包不依赖它们）。
- 中文字体：SimHei、Microsoft YaHei 可用（PNG 预览中文正常；缺失时脚本会告警并降级）。

## 1. 验收命令（与派单验收一致）

```bash
cd build/challenge-83d4f050
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-83d4f050
```

**结果：成功。**

```
SUMMARY {"status": "success", "case_id": "example-egfr-mapk", ...,
         "self_check_passed": true, "failures": 0, "warnings": 0,
         "extraction": {"method": "auto-draft", "verified_by_agent": false}}
```

产出文件（sha256 为该次运行实测值）：

| 文件 | 大小 | sha256(前16位) | 说明 |
|---|---|---|---|
| diagram.svg | 18,641 B | 15e309dc316594cd | 可编辑分层 SVG（7 图层，13 实体组，12 条语义边） |
| diagram.png | 184,318 B | e21a4ce437f1b49d | 预览 1200×900 @150dpi |
| diagram.pdf | 107,456 B | d4aa29b5c4b917c1 | 矢量 PDF 预览 |
| result.json | 22,779 B | 7b67a95e1506674a | 契约化结果（23 项自检全过） |
| model.json | 13,709 B | 5a181c0bd63d4ef7 | 规范化模型（实体/边/图例/来源） |

## 2. 附加验证

| # | 命令 | 结果 |
|---|---|---|
| V1 | 从工作区根目录用绝对脚本路径运行（验证自定位） | `status=success, failures=0` ✅ |
| V2 | `--model-file examples/output/model.json`（验证人工建模路径） | `status=success, failures=0` ✅ |
| V3 | `python -m py_compile scripts/*.py` | 全部通过 ✅ |
| V4 | SKILL.md YAML frontmatter（PyYAML safe_load） | name/description 合法，description > 40 字符 ✅ |
| V5 | 重复运行 3 次 | model.json sha 恒定；SVG 除时间戳/注释外逐字节一致（结构稳定） ✅ |
| V6 | 布局体检（脚本内） | 同区室节点两两无重叠；全部边在画布内；4 区室带 y/h 正常 ✅ |
| V7 | SVG 审计（grep） | 图例 4 种箭头 marker：三角×5、横杠×3、圆点×4、菱形×2；`data-type` 覆盖全部 12 边/13 实体 ✅ |
| V8 | 结果契约核对 | result.json 含 OUTPUT_CONTRACT.md §1 全部字段 + case.json output_contract 自定义字段回显 ✅ |
| V9 | 素材点检 | 材料 13 实体/12 关系全部被抽取；方向与示例材料一致（激活/抑制/结合/修饰/转运各就各位） ✅ |
| V10 | 中文渲染 | SimHei 命中；PNG 图例/区室/标题中文正常（像素级抽查非空） ✅ |

## 3. 冒烟过程中发现并修复的问题（诚实记录）

1. `extract.py` 表行解析：把材料“表1/表2”普通数据行误当实体（症状：实体多出、区室带多出）；
   修复：行解析按“实体清单/关系清单”章节门控 + 复合类型判定，普通数据表行不再入模型。
2. 关系行首格残留 `"- "` 前缀导致实体名错配；修复：`_strip_table_row` 剥离项目符号。
3. `svg_backend` 对 `marker=none`（binding）误查 MARKERS 表 → KeyError；修复：跳过无箭头 marker 定义。
4. `LEGEND_W` 未在 svg_backend 定义 → NameError；修复：本地常量。
5. 校验器 L05 把区室带/标题装饰色当成语义色误报；修复：颜色审计限定在实体组与类型边内。
6. PNG 预览缺 SVG 中的 sources 页脚；修复：mpl_backend 增加同源 footer，源/预览保持一致。
7. T03 逻辑反了（无假设来源时误报 warn）；修复。

## 4. 已知限制（与 README/SKILL 一致）

- PDF 材料不做直接解析（无第三方 PDF 依赖设计）；Agent 抽文本或经 `--model-file` 手工建模。
- 自动抽取只保证结构化语句；散文材料依赖 Agent 核验（SKILL.md 步骤 2）。
- 容器若缺 matplotlib，PNG/PDF 降级（status=partial，export_checks 写明），SVG 仍有效。

## 5. 结论

端到端管线（读材料 → 抽取 → 建模 → 布局 → 可编辑 SVG → PNG/PDF 预览 → 校验 →
契约 result.json）**在本机真实跑通**：验收命令成功、0 失败、双后端一致、重复运行稳定。
示例输入与输出位于 `examples/`（明确标注“示例，非正式案例”）。