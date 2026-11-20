# TEST —— 本地实测记录

环境：Windows 11 + Git Bash(MSYS2)；`python` = Anaconda Python 3.13.9（`D:\Code\anaconda\python.exe`）；
python-pptx 1.0.2 / matplotlib 3.10.6 / Pillow 12.3.0 / numpy 2.3.5 / reportlab 5.0.0；
cairosvg、svgwrite **不可用**（与本 Skill 无关——SVG 由手写 XML 产出，不依赖 SVG 库）。
所有命令在 Skill 根目录 `graphical-abstract-7030fff2/` 执行。

## 0. 语法编译检查

命令：
```bash
python -m py_compile scripts/common.py scripts/extract.py scripts/figurespec.py scripts/svgbuilder.py scripts/preview.py scripts/audit.py scripts/main.py
```
结果：**成功**（`ALL_COMPILE_OK`，exit 0）。

## 1. 正式冒烟（示例案例）

命令：
```bash
python scripts/main.py --case examples/case.json --task examples/task.md --material examples/material.md --out D:/BuildTemp/smoke-graphical-abstract-7030fff2
```
结果：**成功（exit 0）**，status=`success`。产出文件（位于 `D:/BuildTemp/smoke-graphical-abstract-7030fff2/`）：

| 文件 | 大小 | 校验 |
|-|-|-|
| `example-micelle-001_graphical_abstract.svg` | 32 KB | 良构（ElementTree 回解析 ok）、7 个 `id="layer:*"`、61 个 `<text>`、24 处 `data-entity-id`、57 处 `data-src` |
| `example-micelle-001_graphical_abstract.png` | 388 KB | PNG 签名 ok，2400×1600，5492 种颜色（非空白） |
| `example-micelle-001_graphical_abstract.pdf` | 145 KB | 头 `%PDF-1.4`，`header_ok: true` |
| `result.json` | 5.4 KB | status=success；case_id=example-micelle-001；`output_contract` 8 个字段全部镜像进顶层（target_format/resolution_dpi/colorblind_safe/require_legend/require_scale_bar/layer_names/provenance_attr/deliverable） |
| `spec.json` | 42 KB | 113 个几何元素，读取顺序 question→method→results→conclusion |
| `content.json` / `audit.json` / `render_log.json` | — | 2 实体 6、关系 14（5 JSON + 9 文本补充）、数据 7、面板要点 12 |

审计摘要：实体覆盖率 **6/6**；数值编码一致性 **7/7**；画布越界 **0**；缺值 **0**；灰度弱区分对 6（记录于 `grayscale_check`，信息性报告）。

## 2. 确定性复现（同输入 → 同输出）

命令：同一命令二次运行到 `D:/BuildTemp/smoke2`，对比两轮产物：

```text
SVG sha256:  e42694e9…39444   （两轮一致：逐字节相同）
PNG sha256:  23e99277…d83d    （两轮一致：逐字节相同）
spec.json:   identical == True
```
**通过**：布局为确定性纯函数；`result.json` 仅 `generated_utc` 与时间戳类字段不同（如实记录，非图面内容）。

## 3. 鲁棒性用例

### 3a. 空案例（无实体/无数据）
输入：`{case_id: empty-case-01, title: …}`（材料不存在）。结果：**成功（exit 0）**，status=`partial`；
SVG+PNG 产出；`content.notes` 与 `warnings` 如实说明「未发现实体/数据」。

### 3b. 缺数值案例
输入：实体「催化剂A」+ 数据点 `产率: null`，材料文本「产率：未记录」。
结果：**成功（exit 0）**，status=`partial`；`audit.missing_values=["产率"]`、`uncertainty` 声明
「未编造数值」；SVG 内「数值缺失」占位存在。

### 3c. PDF 关闭
`constraints.pdf=false` 时 deliverables 中 pdf 项 `present:false, reason:"disabled by constraints (pdf=false)"`，流水线不出错。

## 4. 开发期发现并修复的问题（真实记录）

| # | 现象 | 根因 | 修复 |
|-|-|-|-|
| 1 | layout 抛 `TypeError: unhashable type: 'dict'` | `extract.run` 文本关系用了 `existing`（id→实体 dict）映射，from_id 变成 dict | 改用 `by_name_lower`（名→id）；已回归通过 |
| 2 | 预览全元素被跳过 | matplotlib 补丁类在函数内 import，而绘制函数在模块级引用 | 改为将 `patches` 字典传入 `_mpl_draw` |
| 3 | 中文字体 `findfont` 海量告警 | rcParams 家族含未注册的 Helvetica/Arial | 只登记存在的字体文件（Microsoft YaHei 等）+ DejaVu Sans 兜底 |
| 4 | 实体 6 个只覆盖 5 个 | `slug()` 纯 ASCII，中文名碰撞（肿瘤细胞/肿瘤组织都→item） | slug 保留 Unicode 词字符；回归后 6/6 |
| 5 | `data-src` 统计为 57 | — | 属正常（24 实体属性 + 33 关系/数据/图例属性） |
| 6 | pdf `checks` 变成列表 | `…b"%PDF-"},` 尾随逗号使赋值变成 1 元组 | 删除尾随逗号；回归后为 dict |

## 5. 边界与未覆盖

- 未在 Linux/macOS 实跑（脚本仅标准库路径操作，理论上可移植；渲染回退链已为"无 matplotlib"设计）。
- CJK 字体回退依赖本机字体（实测 Microsoft YaHei 可用）；跨机若缺字体会如实记录 `render_log.json`。
- 未提交平台、未创建仓库（按分工由发布代理执行）。