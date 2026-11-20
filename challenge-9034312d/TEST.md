# TEST.md — 本地实测记录（challenge-9034312d）

实测环境：Windows / Anaconda Python 3.13.9；Pillow 12.3.0、reportlab 5.0.0
（cairosvg/svgwrite 不可用，因此 SVG 为手写 XML，PNG/PDF 由同一布局模型渲染）。
时间：2026-11-20（Asia/Shanghai）。

## 测试 1 · 结构化案例（examples/case.json）——验收命令

```
cd D:/Work/科学挑战赛/work/efficiency-3/build/challenge-9034312d
python scripts/main.py --case examples/case.json --task examples/task.md --out D:/BuildTemp/final-smoke
```

结果：**成功**（exit 0，check_ok=true，issues=[]，status=success），产物：

```
D:/BuildTemp/final-smoke/demo-biotech-route-01/
  figure.svg   9628 B   (可编辑分层 SVG 源文件，<text> 真实文本)
  figure.png   54982 B  (PNG 预览 2362x1496 px @200 dpi)
  figure.pdf   12704 B  (PDF 预览，矢量，STSong-Light)
  layout.json  10884 B  (结构化中间表示)
  result.json  9541 B   (output_contract 全字段 + case_id)
```

自查：`python scripts/check.py D:/BuildTemp/final-smoke/demo-biotech-route-01/result.json`
→ `ok: true`，24 项 checks 全 true，issues=[]（10 实体 / 9 关系 / 编号 1..7 连续 / 无断头箭头）。

内容验证（程序化）：
- 实体 10 个：E1–E10，kind=step×5/material×2/data/milestone/product，
  每实体带 source（task.md §2.1–§5）；
- 关系 9 条 R1–R9 方向正确：E3→E2（质粒→转导）、E2→E4（转导→药筛）、E8→E9（测序→FastQ）、
  E9→E10（FastQ→靶基因）；跨列关系为正交肘型线；
- 盒子无重叠、无画布溢出；请求画布 300×190mm，实际 311.1×166mm 自动等比缩放入画布。

## 测试 2 · 自由文本兜底（结构化字段缺失）

```
python scripts/main.py --case D:/BuildTemp/smoke-9034312d-text/case.json --out D:/BuildTemp/smoke-9034312d-text/out
```

结果：**成功运行**（exit 0，check_ok=true），status=partial（诚实降级）。
- extraction=text-heuristic：从「由…组成/构成」抽出 3 个设备（冻干机主机/冷阱/真空泵），
  从「第N步:内容」抽出 8 个步骤，按正文顺序串联 sequence 关系；
- uncertainty 如实记录：3 个设备实体无连接（代理需复核连线）+ 文本解构说明；
- 产物：figure.svg/png/pdf + layout.json + result.json 全部生成。

## 测试 3 · Agent 人工修正（--merge）

```
python scripts/main.py --case examples/case.json --merge D:/BuildTemp/merge-demo.json --out D:/BuildTemp/smoke-9034312d-merge
```

结果：**成功**（check_ok=true）。合并生效：
- E5 类别 material → product（source 标注「人工复核」）；
- R4 方向修正为 recycle（E5→E4，回流虚线）；
- change_record 由 1 条增到 3 条（初始生成 1 + 人工修正 2），by=agent。

## 测试 4 · 单测/模块自检

```
python -m py_compile scripts/main.py scripts/model.py scripts/layout.py \
    scripts/export_svg.py scripts/export_preview.py scripts/fonts.py scripts/check.py
python scripts/model.py examples/case.json examples/task.md   # SIR 自检
```

结果：全部通过（模组自检输出 10 entities / 9 relations / extraction=structured；退出码 0）。

## 已知限制（如实记录）

- matplotlib 3.10.6 会把中文 `<text>` 展平为路径，因此**可编辑 SVG 用手写 XML 生成**
  （预试验 font_test.svg 中 text 元素数为 0，避免采用）；
- 本机中文字体：找到 `C:\Windows\Fonts\msyh.ttc`（PNG 用）；PDF 用 reportlab 内置 CID
  STSong-Light（查看方需具备中文字体，result.json.fonts 已如实记录）；cairosvg 不可用，
  PNG/PDF 与 SVG 共享同一布局模型而非互相转换——几何一致，非逐字节等价；
- 自由文本案例 status=partial 是正确的预期行为（组织方约定 partial 需说明），非缺陷。