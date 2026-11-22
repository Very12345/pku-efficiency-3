# encoding-spec.md — 编码规范（字符 / 单位 / 实体命名 / SVG 编码）

本文件约束图上一切文字与编码行为；执行端为 `svgtext.py`（转义/清理）、
`cjkfont.py`（字体）、`chartkit.py`（输出）。

## 1. 字符编码

1. **全部脚本产出 UTF-8**；写文件用 `newline="\n"`（跨平台稳定，避免 CRLF 注入）。
2. **XML 转义**：SVG 内一切文本经 `svgtext.encoded_svg_text()` ——
   先剔除 XML 1.0 非法控制字符，再转义 `& < > " '`。科学实体名中的
   `>` `<` `&`（如 "A>B"、"TGF-β1 & Wnt"）必须转义后写入。
3. **禁止**：把文本转曲为路径（文字始终是 `<text>`，G5 硬检查）；把中文
   替换成方框/点号；用 `?` 替代无法渲染字符。

## 2. 中文与多语言标注（CJK）

1. CJK 判定：`cjkfont.is_cjk()`（中文/日文假名/韩文/全角符号）。
2. SVG：含 CJK 的 `<text>` 使用 `font-family` 回退链
   `Microsoft YaHei, Noto Sans CJK SC, Source Han Sans SC, SimHei, WenQuanYi Zen Hei, PingFang SC, sans-serif`。
3. PNG：`FontMap` 扫描 Windows/Linux/macOS 字体目录 + `FONT_PATHS`，
   找到 CJK 字体则用其渲染；未找到 → validation `cjk-font` warn + uncertainty 记录
   （SVG 打开不受影响）。
4. 字体嵌入：正式投稿矢量源以 SVG 为准（字体族声明由查看方字体解析）；
   如需自包含，用 Inkscape/fonttools 嵌入后另存，并在 change_records 说明。

## 3. 科学实体命名

1. **实体名以源材料原文为准**：不翻译、不"优化"拼写、不修正拼写
   （gene/protein/species/compound 名称照抄；希腊字母/上下标保持原样）。
2. 无法确认的实体 → 保留原文 + `uncertain` 标记，不得自行编造同义词。
3. 网络图实体/关系必须带来源（cite 图表编号或源文件），否则不得上图（D1/D4）。

## 4. 数值与单位

1. 轴标签带单位（源数据带单位时）：`标签 (单位)`，如 `Time (h)`、`Tumor volume (μm³)`。
2. 单位从列名括号提取（`time (h)` → h）入 spec；语义不能从列名读出时在 spec 明确写。
3. 数值格式：`fmt_num`（1e6 级科学计数；一般 ≤4 位有效；不切尾导致失真）。
4. 误差线语义（SE/SD/CI）以源元数据为准（D8），写入 manifest 并校验。
5. 量级异常（数值 vs 标题语义差 10 倍+）→ warn 保留原值，不"修正"（D2）。

## 5. 可编辑源文件（SVG）编码

1. 分层：`<g id="layer-{axes|data|text|legend|annotation}">` 固定顺序；
2. 溯源：`<metadata id='provenance'>` CDATA 块（生成者/源文件 sha256/方法）；
   每个数据图元 `data-*` 属性（file/column/row-index/value/category/…）；
3. id：确定性命名的 svg_id（`bar-1`、`el-role-N`），与 `data_manifest.json` 对齐，
   保证同输入重复运行字节级一致；不用内建 `id()`；
4. 禁止外部实体（`<!DOCTYPE`/`<!ENTITY`），防止 XXE 与解析器风险；
5. 文本永不转曲（G5）；`xml:space="preserve"` 保留首尾空格语义。

## 6. 导出格式编码

| 导出 | 格式 | 编码/参数 | 记录 |
|-|-|-|-|
| 可编辑源 | SVG 1.1 | UTF-8、分层、未转曲 | environment |
| 预览位图 | PNG | RGBA → sRGB、dpi=样式预设（nature/cell=300） | environment.dpi |
| 预览 | PDF | 光栅预览嵌入（PIL），`%PDF` 头 | renders |
| （可选）EPS/PDF-via-SVG | — | 需外部转换器；本包不含 | uncertainty 说明工具 |

## 7. 自检命令

```bash
python "$SKILL_DIR/scripts/svgtext.py" '<测试文本：剂量 ≥20 mg/kg (β-catenin, n=6) <vehicle> & "CTRL">'
python "$SKILL_DIR/scripts/cjkfont.py"            # 字体发现报告
python "$SKILL_DIR/scripts/figcheck.py" --dir <out> --case <case.json>   # G5 real_text / 编码检查
```