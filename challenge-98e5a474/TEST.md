# TEST.md — 本地实测记录

记录建包机（Windows 11 + Anaconda Python 3.13.9）上的真实运行记录。
每段给出**实际命令、退出码、产物**；结论（通过/部分/失败）如实标注，
不虚构。

## 0. 环境

| 项 | 值 |
|-|-|
| OS | Windows 11（Git Bash，cp936 控制台） |
| python | 3.13.9（Anaconda，命令 `python`） |
| matplotlib | 3.10.6（Agg 后端） |
| Pillow | 12.3.0 |
| numpy | 2.3.5 |
| reportlab | 5.0.0（未在流水线中使用，仅报告版本） |
| cairosvg / svgwrite | **不可用**（实测 import 失败）→ 预览采用同 layout 的 matplotlib 镜像，见 §4 |

## 1. 语法编译

```bash
cd build/challenge-98e5a474/scripts
python -m py_compile main.py manifest.py layout.py svgbuilder.py render.py checks.py edit.py report.py validate_result.py selftest.py
# 结果：COMPILE_OK（无 SyntaxError；修正过一处 SyntaxWarning 后以
# -W error::SyntaxWarning 复核通过）
```

## 2. 逻辑自测（selftest.py，23 项）

```bash
python scripts/selftest.py
```
结果：**23/23 PASS**（关系词表映射、未知类型标记、清单 JSON 往返、
射线裁剪、分层布局、SVG 可编辑性/内嵌清单/图例分层、图表渲染与
图例一致性、图例缺项检测、编辑动作 rename/add/remove 与 change records）。

## 3. 三条冒烟链路（exit code 均 0）

### 3.1 schematic（验收命令）

```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-98e5a474
# rc=0  CHECK SUMMARY: success (0 fails, 0 warns, 0 acks)
# 产物：
#   figure.svg  15241 B  （可编辑源：19 个 <text>、6 个 data-entity 组、
#                        5 个 data-relation 组、3 个图例项、3 个 marker、
#                        内嵌 ER 清单且与绘图清单一致）
#   figure.png  124129 B （4500x2580 RGBA；18 cm 宽有效 DPI ≈ 635）
#   figure.pdf  37929 B  （1 页；2 个 Type3 字体定义）
#   result.json 8993 B   （契约全字段 + case_id=example-schematic-001）
```

### 3.2 chart（数据表驱动）

```bash
python scripts/main.py --case examples/case_chart.json --out D:/BuildTemp/smoke-98e5a474-chart
# rc=0  CHECK SUMMARY: success (0 fails, 0 warns, 0 acks)
# 说明：matplotlib 默认 svg.fonttype=path 会把文字转成路径（实测第 1 版
# 图表 SVG 为 0 个 <text>，被 svg.editable_text 判 fail）；已强制
# rcParams["svg.fonttype"]="none" 后 16 个真实 <text>，检查全绿。
```

### 3.3 源文件级编辑（source-preserving edit）

```bash
python scripts/main.py --case examples/case_edit.json \
    --edit-svg D:/BuildTemp/smoke-98e5a474/figure.svg \
    --out D:/BuildTemp/smoke-98e5a474-edit
# rc=0  CHECK SUMMARY: success (0 fails, 0 warns, 0 acks)
# result.json change_records = [rename E2 TNFR1→"TNFR1 (receptor)",
#   relabel R5→"upregulates IL6 transcription", note]（before→after 齐）
```

## 4. 契约校验（validate_result.py）

```bash
python scripts/validate_result.py --case examples/case.json \
    --result D:/BuildTemp/smoke-98e5a474/result.json          → VALID rc=0
python scripts/validate_result.py --result ...-chart/result.json → VALID rc=0
python scripts/validate_result.py --result ...-edit/result.json  → VALID rc=0
```
（初版把空 `change_records`/`legend_mapping` 当退化值误判 INVALID，已按
"合法空列表"修正——无编辑、无图例的案例是正常状态。）

## 5. 失败路径（异常处理实测）

| 用例 | 命令 | 结果 |
|-|-|-|
| 无 ER 清单且 case 无数据 | `--case D:/BuildTemp/fail-no-manifest/case.json` | rc=1；明确提示"不画无依据的图"；写出 **status=failed** 的 result.json（pipeline fail 明细），不编造 |
| 图例缺"抑制"项但图上有抑制箭头 | `--case D:/BuildTemp/fail-legend/case.json` | rc=1；`legend.missing_kinds fail`；校验汇总 **partial**，检查明细进 result.json |
| 来源材料路径不存在 | 上述 no-manifest 用例附带 | 记录 WARN + 写入 result.json uncertainty("unresolved source materials")，不静默 |

修复记录：`_write_failed_result` 曾因位置参数错位抛 TypeError（
"could not write failed result.json"），已修为关键字参数并复测通过。

## 6. 产物程序化审计（可信度证据）

```python
# SVG：xml.etree 解析 well-formed；6 entity groups、5 relation groups、
# 19 <text>、marker×3（activation/open/inhibition）、legend-item×3、
# <metadata id=er-manifest> 可解析且 entities 与绘图清单一致
# PNG：PIL 采样 46 种颜色；实体填充色 #DEEBF7/#FCE4D6/#E2EFDA 均在；
# 箭头色 activation-#0072B2 出现 284 像素、recruitment-#009E73 940 像素、
# transcriptional-#CC79A7 112 像素；inhibition-#D55E00 为 0 —— 因为示例
# 图无抑制关系，0 像素符合预期（不是 bug）
```

## 7. 限制（已如实入包，见 README/result.json uncertainty）

- 无 cairosvg/svgwrite：PNG/PDF 预览 = 同一 layout+manifest 的
  matplotlib 镜像（语义一致、非逐像素）——这是环境的**故意降级设计**，
  不是隐藏故障；
- CJK 字体：resolve_font_stack 优先微软雅黑/SimHei/Noto CJK（本机命中
  微软雅黑）；无 CJK 字体的机器上 PNG 预览可能缺字（SVG 文字不受影响）；
- PDF 字体嵌入审计为尽力而为（Type3/FontFile 计数），完整审计在无
  专用 PDF 库的情况下如实标注 warn；
- 控制台在 Windows cp936 下不显示 §/≈ 等字符（文件内容为 UTF-8，无损）。

## 8. 包约束检查

```bash
find . -type f | wc -l        # 34（阈值 50 文本文件；剔除 __pycache__ 后）
find . -type f -size +500k    # 0
du -sb .                      # ≈ 492 KB（阈值 2MB）
find . -type l | wc -l        # 0（无符号链接）
```

## 9. 结论

- 必做验收 `python scripts/main.py --case examples/case.json --out
  <目录>`：**通过**（rc=0，真实产出 figure.svg/png/pdf + result.json）；
- SKILL.md：**完整**（YAML frontmatter + 用途/条件/输入输出/七步执行/
  异常处理表/自查清单/资源/限制/禁止）；
- OUTPUT_CONTRACT.md：**定义了完整 result.json 契约**；
- 失败分支全部能在不编造的前提下落盘说明（failed/partial 语义）。