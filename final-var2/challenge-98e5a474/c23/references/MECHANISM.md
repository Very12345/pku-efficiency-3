# MECHANISM — 五个机制的完整说明（含"没有它会怎样"与可证伪判据）

本文件是 `SKILL.md` §3 机制索引的完整版。每个机制写四段：

1. **是什么** — 机制的定义与落点；
2. **没有它会怎样** — 具体会退化成哪一种失败（不是"差一点"，而是可指名的失败形态）；
3. **可证伪判据** — 什么观测会**推翻**"这个机制在起作用"；
4. **已知盲区** — 这个机制**测不到**什么（写出来，免得它变成万能借口）。

> 写作约定：判据必须是**可跑的命令或可读的字段**，不能是"感觉更可靠"。
> 检查名与级别的完整清单见 `references/CHECK-INDEX.md`；
> 每个判据在本机是否实测过，见 `TEST.md` §V2。

---

## M1 方案先行（plan-before-draw）

### M1.1 是什么
在**画之前**跑一道 lint 门：`scripts/spec_lint.py --manifest <entities.json>`。
门覆盖：实体非空且 id/name 有效；关系 `from`/`to` 指向存在实体；
`kind` 能映射到 7 类规范词表（activation / inhibition / recruitment / process /
transcriptional / causal / containment）；containment **必须**用 `groups` 表达；
图例与图面箭头类型**双向**一致；chart 调色板长度 ≥ 唯一类别数、单位已声明。
`main.py` 默认内嵌这道门（`--lint` 默认开）。

### M1.2 没有它会怎样
退化为"先画出来再说"。具体后果按严重度排：

| 后果 | 为什么 | 对应检查名 |
|-|-|-|
| 未知关系类型被悄悄画成某种箭头 | 画图阶段没有词表可依，凭感觉选箭头 | `spec.relation_kind` 本应 fail |
| 包含关系被画成箭头（层级被读成因果） | containers 与 relations 在画布上都表现为"线"，不拦就会混 | `spec.containment_arrow` / `spec.containment_group` |
| 图例缺项或孤儿项 | 图例往往在画完后"补"，补的时候已经和画面对不上 | `spec.legend_missing_kinds` |
| 调色板不够分 | 颜色数 < 类别数时会出现"两类同色" | `spec.color_category_count` |
| 发现错误的时机最晚 | 错误在成品里才暴露，返工要重排整张图 | — |

### M1.3 可证伪判据
- **正向**：`spec_lint.py --manifest <m.json>` 对**好清单**输出 `VALID (CP1)` 且退出码 0；
  对**坏清单**（未知 kind）输出 `INVALID (CP1)` 且退出码 1 —— 本机已实测（`TEST.md` §V2）；
- **反向（推翻条件）**：如果一份含未知 `kind` 或未分组 containment 的清单**也能**
  让 `spec_lint.py` 输出 `valid: true`，或让 `main.py` 的
  `verification.spec_lint.valid` 不为 false，则 M1 不成立；
- **端到端**：坏清单走 `main.py` 时，`status` 必须降为 `partial` 且
  `fails` 出现 `spec_lint.<检查名>` —— 本机已实测（`TEST.md` §V2）。

### M1.4 已知盲区
- M1 只做**结构**判断：它不知道"抑制"在生物学上是否真的成立，
  只检查这个关系有没有被声明为可映射的类型；
- 它不检查实体名是否**真的**出现在材料里（那需要逐条对照 `evidence`，
  属 Agent 判断 + `spec.traceability` warn）；
- `--no-lint` 会把 M1 整个关掉，而 `result.json` 里只会留下一个空对象
  （`verification.spec_lint = {}`）⇒ 交付前必须用默认参数重跑。

---

## M2 源文件自描述（self-describing source）

### M2.1 是什么
把 ER 清单**内嵌**进生成的 SVG：`<metadata id="er-manifest">` 里保存
entities / relations / groups / legend / style 的完整 JSON；每个图元带
`id` 与 `data-entity` / `data-relation` / `data-canon` / `data-source` 属性。
结果是：**SVG 自己就是数据源**，不需要回头找清单文件。
`scripts/edit.py` 正是靠读这份内嵌清单做增量编辑。

### M2.2 没有它会怎样
退化为"图与数据分离"：

| 后果 | 为什么 | 对应检查名 |
|-|-|-|
| 改一个标签要重画整张图 | 没有清单可改，只能改画布 | — |
| 无法做**源文件级**增量编辑 | 编辑需要"知道每个图元对应哪个实体" | `svg.manifest_embedded` |
| 图元与清单可能不一致 | 两份数据各自演化，没有校验点 | `svg.manifest_matches` |
| 溯源属性无法审计 | `data-*` 属性是溯源的载体 | `svg.data_entity_attrs` / `svg.data_relation_attrs` / `svg.data_source_attrs` |

### M2.3 可证伪判据
- **正向**：`figure.svg` 里能按 XML 解析出 `<metadata id="er-manifest">`，
  且 `svg.manifest_embedded` 与 `svg.manifest_matches` 为 ok；编辑后
  `change_records` 含 `before`/`after` —— 本机已实测（`TEST.md` §V2/§V3）；
- **反向（推翻条件）**：如果 `--edit-svg` 指向一个**没有**内嵌清单的 SVG
  也能成功编辑，或编辑后的 `figure.svg` 里查不到 `data-*` 属性，则 M2 不成立。
  实测后者会走 `exit 2` + `FATAL: no embedded ER manifest in …`；
- **增量性**：编辑后未改动元素应与编辑前一致（同一 `<text>` 内容、
  同一 `id`）；若整张图被重写，增量性不成立。

### M2.4 已知盲区（**必须写出来**）
编辑动作的错误（`edit.*`）**只出现在 stdout 日志**里：不进 `result.json`、
不改退出码。因此：

- 一个"目标不存在"的编辑请求会让 `change_records` 为空，
  而命令仍可能 `exit 0`、契约门仍然 `VALID`；
- 唯一可靠的判据是**条数对拍**："请求条数（按
  `references/EDIT-ACTION-SCHEMA.md` §1 推算期望值）" vs "`change_records` 条数"；
- 这不是"以后会修"的托词，而是**当前必须由 Agent 执行的检查步骤**，
  已写进 `SKILL.md` 的自查清单。

---

## M3 抽取四段回退（four-stage extraction fallback）

### M3.1 是什么
`scripts/pdftext.py` 按 **fitz → pypdf → PyPDF2 → stdlib（zlib + `Tj`/`TJ` 解析）**
逐级尝试抽取 PDF 文本，并把实际使用的 backend **如实写进结果**。
任何一个后端不可用都不导致整体失败。

### M3.2 没有它会怎样
退化为两种坏结果之一：

| 退化 | 后果 | 证据面 |
|-|-|-|
| 直接失败 | 环境里没有 PyMuPDF 就完全读不了 PDF，案例无法开始 | — |
| 静默空转 | 抽不出文本却继续往下走，图上出现"看起来像真的"的内容 | 这正是题面点名的失败形态 F12 |

没有 M3 时，"PDF 是扫描件/加密件"这类材料会被当成"有文本"处理，
而**编造文本**是本题最严重的错误之一。

### M3.3 可证伪判据
- **正向**：在**没有** fitz/pypdf 的环境里，`pdftext.py` 仍能对一个
  可抽取的 PDF 产出文本，且 backend 字段显示 stdlib 回退（`selftest.py`
  对回退路径有断言，见 `TEST.md` §V1）；
- **反向（推翻条件）**：如果 `pdftext.py` 对**不存在的文件**返回 0，
  或对伪造的 `%PDF` 头文件崩溃而非返回非零，则 M3 的边界处理不成立。
  实测：不存在 → `exit 2` + `FATAL: pdf not found`；伪造头 → `exit 1`（不崩）；
- **诚实性**：若 backend 字段恒为同一个值（无论实际用了哪个库），
  则"如实记录"这一点不成立。

### M3.4 已知盲区
- stdlib 回退的抽取**质量**取决于 PDF 的文本编码方式（压缩流、子集字体、
  自定义编码都可能抽不全）；回退成功 ≠ 抽全；
- 加密/扫描件**本来就不该**被抽出来，M3 的职责是"如实报告不可抽取"，
  不是"想办法抽出来"（OCR 属其它工具）。

---

## M4 导出预检（export pre-flight）

### M4.1 是什么
在写出产物后立刻检查，并把逐项明细写进 `result.json.verification.checks`：
`svg.editable_text`（文字是真实 `<text>`，未被 path 化）、`svg.layers`（语义图层）、
`bitmap.dimensions` / `bitmap.dpi_print`（18 cm 宽下的有效 DPI，印刷 ≥300 / 屏幕 ≥150）、
`bitmap.colourspace`（RGB 族）、`pdf.header` / `pdf.pages` / `pdf.fonts_embedded`、
`font.cjk`，以及每类产物的 `artifact.<role>` 存在性。

### M4.2 没有它会怎样
退化为"导出来再说"，失败在**投稿节点**才暴露：

| 后果 | 为什么 | 对应检查名 |
|-|-|-|
| 图能用但投不出去 | 分辨率/色彩/字体不合要求，改要重导 | `bitmap.dpi_print`、`bitmap.colourspace` |
| 文字不可选、图层不可拆 | 预览是栅格图被当成"源文件" | `svg.editable_text`、`svg.layers` |
| 缺文件却报成功 | 没有产物存在性检查 | `artifact.figure` / `artifact.preview` / `artifact.pdf` |
| 中文标注乱码未被发现 | 没有字体可用性检查 | `font.cjk` |

### M4.3 可证伪判据
- **正向**：一次正常运行的 `verification.checks` 里能读到上述项的实测值
  （本机实测：DPI ≈635 ≥300、色彩 RGBA、`svg.editable_text` ok、
  `font.cjk` True —— `TEST.md` §V3）；
- **反向（推翻条件）**：
  - 把 `--dpi` 降到远低于阈值后 `bitmap.dpi_print` **仍然 ok** ⇒ 判据失效；
  - 删掉某一个产物（或让它写失败）后**没有**出现 `artifact.<role>` fail ⇒ 存在性检查失效；
  - 把文字改成 path（或换成 fonttype 非 none）后 `svg.editable_text` **仍 ok** ⇒ 可编辑性检查失效；
- 以上三条都是可构造的"推翻实验"，任何人都能做——这正是 M4 可被检验的原因。

### M4.4 已知盲区
- `pdf.fonts_embedded` 是**尽力而为**的审计（解析 PDF 字体表），
  不等于目标期刊的硬性要求；
- `bitmap.dpi_print` 假设"18 cm 宽"这一常见印刷宽度，其它版面宽度需自行换算；
- 预检**不知道审美**：重叠、配色观感、字号是否合适，只做阈值与结构判断；
- `--skip-checks` 会跳过整个 M4（`verification.checks` 为空），
  而此时 `status` 仍可能是 `success` ⇒ 该次运行不得当作交付版本。

---

## M5 单一字体事实源（single source of font truth）

### M5.1 是什么
`scripts/textfont.py` 探测系统可用字体（候选族：微软雅黑 / SimHei / Noto CJK 等），
`render.py`、`checks.py`、`result.json` 三方**共用同一个探测结果**，
不再各自 fallback。`--list` 打印逐候选族的命中情况，`--probe` 输出机器可读结论。

### M5.2 没有它会怎样
退化为"三处各猜一个字体"：

| 后果 | 为什么 |
|-|-|
| 预览用的字体与检查报告的字体不一致 | 渲染与检查各自探测，环境差异时结论互相矛盾 |
| `result.json` 里的字体信息不可信 | 第三处又猜一次 |
| 中文缺字问题被误报或漏报 | 探测口径不同 ⇒ `font.cjk` 的布尔值没有统一定义 |
| 无法定位"为什么这台机器上字变了" | 没有单一的 `--list` 入口 |

### M5.3 可证伪判据
- **正向**：`textfont.py --probe` 输出包含解析到的族名与 `cjk_ok` 布尔，
  且同一输入下**两次运行结果相同**（确定性）—— `selftest.py` 对确定性有断言
  （`TEST.md` §V1）；
- **反向（推翻条件）**：如果 `render.py` 用的字体族与 `result.json` 里记录的
  字体族在**同一台机器同一次运行**里不一致，则"单一事实源"不成立；
  这个检查可以直接比对 `verification.render` 与渲染日志；
- **可定位性**：`--list` 应逐候选族打印 `[x]/[ ]` 与最终解析结果；
  若 `--list` 不给出逐候选信息，则"可定位"这一点不成立。

### M5.4 已知盲区
- 探测**只回答"能不能用"**，不回答"字形对不对"（数学符号覆盖、
  连字、上标下标可能仍缺）；
- 没有 CJK 字体时，PNG 会缺字而 SVG 文字仍在 —— M5 只能报告，
  不能凭空补出字体；
- 字体探测依赖运行环境的字体目录，**跨机器结果会不同**，
  因此 `font.cjk` 的取值必须与机器信息一起记录才有意义。

---

## 机制之间的关系与联合判据

| 联合场景 | 需要哪几个机制同时成立 | 联合判据（可跑） |
|-|-|-|
| "错误在生成前被拦下" | M1 | 坏清单 → `spec_lint` INVALID（exit 1）；走 `main.py` → `status=partial` 且 `fails=[spec_lint.*]` |
| "图可以被继续维护" | M2 | 编辑后 `change_records` 含 before/after；未改动元素保持；`svg.manifest_matches` ok |
| "看得懂的材料都能读" | M3 | 有无第三方 PDF 库都能跑；backend 字段随实际路径变化 |
| "交出去能被期刊接住" | M4 + M5 | `bitmap.dpi_print` 达标、`svg.editable_text` ok、`font.cjk` 有记录 |
| "换了人/换了机器还能复现" | M1+M2+M5 | 确定性双跑同 sha；`font.cjk` 与机器信息一起记录 |

**联合判据的意义**：单个机制的判据可能被"恰好通过"蒙混，但联合判据要求
多个不相关的事实同时成立，蒙混成本高得多。

## 机制的修改纪律

改动任何一个机制（改检查名、改字段名、改回退顺序、改字体候选）时：

1. 先在本文件更新对应的**可证伪判据**（判据变了，机制的定义就变了）；
2. 同步**受影响的下游**：本文件的依赖图给出了影响范围
   （例：改 M5 的候选族会影响 M4 的 `font.cjk` 与预览保真）；
3. 重跑 `python "$SKILL_DIR/scripts/selftest.py"` 与
   `PYTHONDONTWRITEBYTECODE=1 python -B "$SKILL_DIR/scripts/doccheck.py"`
   （后者会检查"文档提到的检查名"是否还真实存在）；
4. 在 `TEST.md` 里补一条新的实测读数 —— **没有实测读数的机制判据视为未验证**。
