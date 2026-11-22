# audit-rules.md — 审计规则（检查标准与处置）

交付前审计分为三层，逐层定义检查项、级别、触发与处置。executor 为
`figcheck.py`（G1–G8）、`mapcheck.py`（映射）、`spec_lint.py`（生成门）；
本文件是这些检查的人读标准，也是 Agent 自查的依据。

## 1. 检查项总表

| 层 | id | 检查内容 | 级别 | 失败条件 | 处置 |
|-|-|-|-|-|-|
| 规格 | E1 | 图型词表 | error | type ∉ {bar,line,scatter,box,heatmap,pie,network,panel,auto} | 改 spec 或降级 partial |
| 规格 | E2 | 图 id | error | 缺 id | 补 id |
| 规格 | E3 | 列存在 | error | x/y/hue/error 列不在数据 | 用 extract 画像修正列名；禁止补造列 |
| 规格 | E4 | 误差语义 | warn | semantics 非常规（非 SE/SD/CI） | 按源元数据更正 |
| 规格 | E5 | 显著性锚点 | error/warn | 缺 from/to/at、引用不存在分类、无 p/来源 | 锚点错误→error；缺 p 来源→warn |
| 规格 | E6 | 轴标签单位 | warn | 源列带单位但 spec 未给单位 | 补 unit |
| 规格 | E7 | panel 子规格 | error | panels[] 缺失或子规格无效 | 补/修子规格 |
| 规格 | E8 | 网络实体/关系 | error | 无实体来源；边引用未定义节点 | 补 entities_file/修正关系；悬空边不画并记录 |
| 规格 | E9 | filter 列存在 | error | filter.column 不存在 | 修正 filter |
| 规格 | E10 | 画布尺寸 | warn | width/height > 5000 | 缩小画布 |
| 校验 | provenance | 图元溯源覆盖 | ok/warn | 存在无 role 图元 | 补 data-*；无法溯源元素不上图（D1） |
| 校验 | legend-mapping | 图例↔系列 | fail | 缺/多图例项 | 图例自动重排或修 spec |
| 校验 | axis-units | 轴标签 | warn | 缺 x/y 轴标签 | 补 label/unit |
| 校验 | range-covers-data | 范围覆盖 | warn | 数据点出轴范围 | 调 pad/轴范围 |
| 校验 | cjk-font | CJK 字体 | warn | 有 CJK 文本但无 CJK 字体 | 记录 uncertainty（SVG 回退链仍正常） |
| 校验 | significance | 显著性配对 | fail | 线段数≠文字数 | 修 spec annotations |
| 校验 | null-handling | 空值处理 | ok | — | 记录计数 |
| 校验 | occlusion | 文本遮挡 | warn | N 处重叠 | 自动旋转/移图例/手给坐标，N>0 记 warn |
| 映射 | G3 | manifest↔SVG 1:1 | fail | unmatched>0 | 查 manifest 生成逻辑 |
| 映射 | G4 | 图元源定位 | fail | 有图元无源信息 | 补 data-* / 不上图 |
| 映射 | value | 图元↔源值 | fail | 值核对不等 | 查 filter/列映射，绝不"修正"数据 |
| 交付 | G1–G2 | 信封/契约 | fail | result 不可解析/契约字段缺 | 重跑 main |
| 交付 | G5 | SVG 可编辑性 | fail | 无分层/无溯源/文字转曲/XXE | 重生成（chartkit 保证不转曲） |
| 交付 | G6 | 预览/导出参数 | fail | PNG/PDF 缺失或损坏 | 查 Pillow/导出路径 |
| 交付 | G7 | 六项校验 | fail | 任一 fail | 修复后重跑 |
| 交付 | G8 | status 诚实 | fail | completed 但存在失败项 | 降级 partial + uncertainty |

## 2. 级别语义

- **error / fail**（阻止交付）：必须修复后重跑；修不了 → status=partial（D10/D16）。
- **warn**（允许交付但须说明）：逐个判断处置 —— 能修则修（记录 adjustments），
  不能修则写入 uncertainty 并说明原因与复验路径（不静默不管）。
- **ok**：通过，detail 留证据。

## 3. 审计执行顺序与结论

```bash
# $SKILL_DIR = 本包绝对路径（平台为 /skills/weekly-skill）；脚本自定位，任意 cwd 均可
python "$SKILL_DIR/scripts/spec_lint.py" --spec <case.json> --case <case.json>  # 生成前：规格门
python "$SKILL_DIR/scripts/main.py" --case <case.json> --out <out>              # 生成 + 内建校验
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>  # 契约覆盖
python "$SKILL_DIR/scripts/figcheck.py" --dir <out> --case <case.json>          # G1–G8 交付门
python "$SKILL_DIR/scripts/mapcheck.py" --dir <out> --case <case.json>          # 映射值核对
python "$SKILL_DIR/scripts/verify_rerun.py" --case <case.json> --out <out>      # 确定性
```

结论三档：
1. **ALL GATES PASS**（figcheck exit 0）→ 可交付，status=completed。
2. 有 warn、无 fail → 可交付，uncertainty 说明 warn 项。
3. 有 fail/error → 修复重跑；时间不足 → status=partial + failed_figures/uncertainty，
   **禁止伪装完成**（G8）。

## 4. 人工介入点

- 网络图标签遮挡：在 spec 中手给节点 `x/y`（D13/D17），重跑后 occlusion 应降为 0。
- 显著性标注只转述材料已给的 p 值与检验方法，加在图注脚（D6）。
- 手动改图（编辑器/脚本）后用 `--note "..."` 追加 change record（D11）。
- 词表扫描命中的候选实体：Agent 核对源材料原文后上图，并移除 uncertain 标记（D4）。