# layer-naming.md — PPTX 分层命名规范（v2）

> 目的：让"可编辑"不再是口头承诺。每个由本 Skill 添加的对象都有**确定性名称**，
> 任何编辑器、脚本或另一个 Agent 都能按名称找到并修改它。名称由
> `scripts/ooxml_kit.name_shape()` 统一分配，`scripts/export_check.py` 在交付前
> 对命名做审计（unnamed/auto 形状进入 warnings）。

## 1. 命名总则

- 名称格式：`<kind>-<NN>[-<safe-ref>]`，`NN` 为运行内递增序号（01, 02, …）；
- `<safe-ref>` 为图/表编号的安全化形式（`Fig. 1` → `Fig.-1`，仅保留
  字母数字、中文、`.`、`-`；最长 48 字符）；
- 名称对同输入重跑**确定**（同一 spec 两次运行，对象名序列一致）；
- 组织方模板自带的占位符/形状**不改名**（placeholder-fill-only 铁律）；
  命名审计只审计**我们添加**的对象，模板自带对象不强制。

## 2. 命名前缀（deckgen 添加对象）

| kind 前缀 | 对象 | 示例 |
|-|-|-|
| `claim-title-` | 页面标题（无标题占位符时补画的文本框） | `claim-title-02` |
| `claim-strip-` | 内置版式主张条（标题下） | `claim-strip-05` |
| `body-bullets-` | 内容页正文（占位符或文本框） | `body-bullets-03` |
| `figure-` | 图区域：嵌入图片 / 占位框 / 图注 | `figure-06-Fig.-1`、`figure-07-Fig.-1-placeholder`、`figure-06-Fig.-1-caption` |
| `table-` | 嵌入表格 | `table-08-Table-1` |
| `footer-page-` | 内置版式页码页脚 | `footer-page-01` |
| `outline-` | 自动"汇报主线"页正文 | `outline-04` |
| `evidence-map-` | 自动"证据映射"页正文 | `evidence-map-05` |
| `closing-` | 谢谢/讨论页正文 | `closing-09` |
| `cover-` | 封页文字（无标题占位符时） | `cover-01` |

## 3. OOXML 注入点（ooxml_kit.py 提供的底层操作）

| 操作 | 函数 | 说明 |
|-|-|-|
| 形状命名 | `name_shape(shape, kind, idx, ref)` | 写 `p:sp/p:pic/p:graphicFrame` 的 `name` 属性 |
| 主题字体 | `set_theme_fonts(prs, latin, ea)` | 写 theme part 的 `a:majorFont/a:minorFont` 的 latin/ea，换机不丢中文字体 |
| 运行字体 | `set_shape_font(run, name, size, bold, color)` | 同写 `a:latin` + `a:ea` |
| 容器健全 | `zip_sanity(pptx_path)` | 检查 OPC zip：`[Content_Types].xml`/`_rels/.rels`/`ppt/presentation.xml` 存在且 XML 良构 |
| 命名审计 | `naming_audit(prs)` | 列出每页形状名，报告 unnamed/auto 形状 |
| 备注读取 | `iter_notes(prs)` | 逐页读 notes part 文本，供"备注分离"校验 |

## 4. 导出文件命名规范

| 产物 | 命名 | 含义 |
|-|-|-|
| 可编辑源 | `<output_name>.pptx`（默认 `academic_deck.pptx`） | 模板适配结果，占位符级可编辑 |
| 预览 | `preview-approx-<cover|NNN>.png` | PIL 近似渲染，**必须带 approx**（诚实标注） |
| 证据映射 | `evidence_mapping.md` + `evidence_map.json` | 逐页映射表（人读 + 机器读，同源） |
| 重建图 | `chart-<safe-ref>.png` / `chart-<safe-ref>.svg` | 从论文表格数字重建（可编辑 SVG 源） |
| 结果 | `result.json` | 契约完整 + case_id |

## 5. 检查与维护

- 交付前运行 `python scripts/export_check.py --result <out>/result.json --out-dir <out>`
  —— G4/G5（可重开 + OOXML 健全）与命名审计（warning 级）自动执行；
- 新增对象类型时在 `ooxml_kit.PREFIX_BY_KIND` 注册前缀，保持本表与代码一致；
- 修改命名规则后，同输入重跑一次并在 TEST.md 记录两次运行对象名序列一致。