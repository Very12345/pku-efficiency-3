# DECK_RULES.md — 页面/版式规则（deck rules）

> 对应高分 intent 的 `deck_rules.md`（75.33 分包核心文档之一："页面/deck 规则"）。
> 机器可执行部分在 `templates/talk_config.json` 的 `deck_rules` 段与
> `scripts/verify_deck.py`；本文档解释规则与理由。

## 1. 页级内容规则（一页一主张）

| 规则 | 值 | 执行/校验 |
|-|-|-|
| 每页唯一主张 | claim 逐字取自源材料（6–500 字） | validate_plan P5/P7 |
| 每页一句可讲的话 | one_liner ≤ 64 字，与页面结论对应 | P7、`scaffold_plan._one_liner` |
| 每页备注 | notes 含【本页主张】【证据】【讲解】（+【备答】） | verify_deck（notes 非空）、P8 |
| 封面/目录/收尾 | 也写 notes（讲解责任分离） | verify_deck 全页检查 |
| weak 页显式提示 | 页内"※ 间接概括"行 + uncertainty 记录 | deck_builder、main |

## 2. 图表规则（图表引用 ↔ 页内结论对应）

- `figure_ref` 提取自源材料中的引用标记（Fig./图/Table/表/Scheme…，见
  `evidence.extract_figure_refs`），页内结论与它绑定（不是随便配图）；
- 图绑定：按引用 token 与材料图片文件名匹配（'Fig. 2' → fig2.png）——
  找不到图片 → **诚实占位框**（标注"材料未提供图片文件"，不虚构插图）；
- 图占位/绑定状态写入 evidence_audit + deck_audit（figure_element/占位框），
  preview 相应区域也提示。

## 3. 版式与可编辑性规则

- **布局来源**：案例模板/起始 deck → `python-pptx` 打开并沿用其母版与版式新增页面
  （模板约束不破坏）；无模板 → 包内置主题（16:9 母版 + 主题色 + 底栏装饰 master-accent-bar）；
- **确定性元素命名**（可编辑性的机器证据，也是人工定位入口）：

  | 元素 | 命名 |
  |-|-|
  | 封面标题 | `cover-title`（无标题占位时）/ 复用占位符 |
  | 封面元信息 | `cover-meta` |
  | 内容页标题 | `page-title-NN`（无标题占位时）/ 复用占位符 |
  | 内容页主张区 | `page-claim-NN`（必检：verify_deck G6） |
  | 图/占位区 | `page-figure-NN` |
  | 页脚 | `page-footer-NN` |
  | 母版底栏 | `master-accent-bar` |

- **字体**：西文 Arial / CJK Microsoft YaHei（`a:ea` 显式写 east-asian typeface，
  换机不丢中文字体）；预览用 PIL 找系统 CJK 字体渲染，找不到则 load_default 并继续。
- **页数脚注**：每页页脚 `NN / total · case_id`，便于答辩现场按页对证据。

## 4. 导出与预览规则

- 主交付 = 可编辑 `editable_deck.pptx`；预览 = PIL 模拟 PNG（水印 + manifest 限制说明），
  非 Office 栅格化，不作"已渲染美观"的虚假声明；
- `decks` 由 `verify_deck.py` 校验：打开、页数 == 计划、每页备注与 claim 元素、OPC 完整；
- `preview_manifest.json` 列出全部预览文件与限制。

## 5. 人核辅助

上台前用 `templates/slide-checklist-template.md`（逐页核对清单）复查：
主张可溯源、引文未改写、图表对应、强度匹配、讲稿不重复、数字一致。