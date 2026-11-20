# README.md — 生物机制图与通路图 Skill（v2 加强包）

> 题目：玻尔产品周赛·北大专区·学术效率·第三期 - challenge-83d4f050（生物机制与通路图，
> 组：figures）。本目录是 v2 加强包（基底：`build/challenge-83d4f050`；意图对齐：
> `highscore-intel/challenge-83d4f050.md`；三方对照见 `COMPARE.md`）。
> 只制作，不提交平台、不发布仓库。

## 1. 这是什么

一个可被 Agent 调用的 Skill，把科研机制/通路材料转成**可逐条质疑的机制图**：
实体（基因/蛋白/复合物/小分子/区室）与相互作用（激活/抑制/结合/修饰/转运）全部
source-bound，图例/数据编码与图面自洽，交付可编辑分层 SVG 源 + PNG/PDF 预览 +
审计产物 + 契约化 result.json。

v2 相对基底的核心升级（详见 COMPARE.md）：
1. **CP1–CP4 检查点流水线** + **决策规则 D1–D12**（SKILL.md）：材料异常/规格违规/
   图例不一致/数值无源/字体缺失等失败分支全部显式化；
2. **机制规格 schema 前置**（CP2 门，`assets/mechanism-spec.schema.json`，对 raw 规格
   校验防静默归一）；
3. **拓扑审计**（`scripts/topology.py`：方向/区室/同名消歧/重复边/自环/反馈标注）
   与**图例/数据编码审计**（`scripts/legend_audit.py`：箭头=图例、颜色⊆图例∪映射、
   虚线语义、数值溯源）双 linter，产物落盘 topology.json / legend_audit.json；
4. **契约四形态回显 + G1–G8 硬性门**（`references/output-contract.md` +
   `scripts/check_contract.py` 独立复查）；
5. **确定性**：SVG/PNG/model/topology/legend_audit 同输入双跑逐字节一致
   （TEST.md T4 实测），result.json 仅时间戳字段不同；
6. 修复基包抽取器两个缺陷（"A 动词 B" 空白尾随、约束行误抽为实体），新增
   `templates/relation-checklist-template.md`（人工核验执行载体，对齐 76.67 极简包）。

## 2. 快速开始

```bash
# 1) 已核验规格路径（人工核验后正式出图）
python scripts/main.py --case examples/case.json \
    --model-file examples/model.example.json --out D:/BuildTemp/out
# 2) 自动草稿路径（产出 partial，提示 Agent 复核）
python scripts/main.py --case examples/case.json --out D:/BuildTemp/out2
# 3) 独立复查
python scripts/check_contract.py --result <out>/result.json --case examples/case.json
python scripts/validate_figure.py --out <out>
```

平台运行时：技能被安装到 `/skills/weekly-skill`，输入在 `/input/case.json` 与
`/input/task.md`（+ 材料目录），输出写 `/app/output`；等价命令
`cd /skills/weekly-skill && python3 scripts/main.py --case /input/case.json --out /app/output`。

## 3. 输入与输出

**输入**：`case.json`（case_id/title/task/materials/render/output_contract）+
`task.md` + 材料文件（文本/Markdown/表格，PDF 由 Agent 抽文或手工建规格）。

**输出**（`--out` 目录）：
`result.json`（契约，见 references/output-contract.md）、`diagram.svg`（7 层可编辑源、
data-id/data-type/data-source）、`diagram.png`/`diagram.pdf`（预览）、`model.json`
（机制规格）、`topology.json`/`legend_audit.json`（审计产物）。

## 4. 目录结构

```
SKILL.md                 入口：用途/输入输出/CP 检查点流水线/D1–D12 决策规则/自查
README.md / TEST.md / COMPARE.md / worklog.md / GITHUB_URL.txt
scripts/                 11 个脚本（build=extract/model/main；render=layout/pathway_svg/
                         mpl_backend；verify=topology/legend_audit/validate_figure/
                         check_contract/result_writer）
references/              output-contract / rubric-map / mechanism-spec /
                         legend-encoding / failure-modes
assets/                  mechanism-spec.schema.json / palettes.json / result.template.json
templates/               relation-checklist-template.md（关系核对清单）
examples/                case.json + task.md + materials/ + model.example.json +
                         output/（本机实跑产物，标注"示例，非正式案例"）
```

## 5. 依赖与环境

- 运行：Python 3（标准库）；PNG/PDF 预览需要 matplotlib（缺失时自动降级，
  SVG 源不受影响）；PNG 尺寸检查需要 Pillow（可选）。
- 本机实测：Python 3.13.9 / matplotlib 3.10.6 / Pillow 12.3.0，全部脚本通过
  `py_compile`（TEST.md T1）。
- 脚本自定位（`os.path.dirname(__file__)`），不依赖 cwd；风格常量集中在
  `assets/palettes.json`（缺省回退 model.py 内置默认）。

## 6. 适用范围与限制

- 适用：机制图/通路图/信号级联/调控网络/流程图/图表编辑，包括改错箭头/按数据上色/补图例。
- 不适用：数值统计、实验设计、论文写作与版式美化（相邻课题负责）。
- 自动抽取器只处理结构化语句；散文/PDF 材料需 Agent 手工建规格（CP2b/CP3 强制），
  这是"准确率优先"的刻意设计；PDF 导出含时间戳，不作为确定性承诺对象。
- 完整失败模式见 `references/failure-modes.md`；重要对话与实测记录见 `worklog.md`。

## 7. 维护与更新

- 改颜色/线宽：只改 `assets/palettes.json`（全图与图例同步）；
- 改契约/门：`references/output-contract.md` + `scripts/check_contract.py` 同步；
- 改校验规则：`scripts/topology.py` / `legend_audit.py` / `validate_figure.py`，
  更新 `references/mechanism-spec.md` §7 校验一览；
- 改完跑 TEST.md T1–T8 全套并更新记录（确定性/门/契约退出码必须重新验证）。