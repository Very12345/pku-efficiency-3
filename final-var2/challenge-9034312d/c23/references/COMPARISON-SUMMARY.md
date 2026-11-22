# COMPARISON-SUMMARY.md — 三层机制的反例对照（本包内附的实测摘要）

> `references/MECHANISM.md` 里每一句"没有它会怎样"都对应本文件的一张表。
> 对照的一侧是 `scripts/bare_baseline.py`（**把 M1/M2/M3 三层全部拿掉**：
> 不抽取证据、改用固定网格排版、不做任何规则审计），另一侧是本包完整流水线。
> 两侧读**同一份** `case.json`、同一台机、同一个 Python、各跑一轮。
>
> 完整逐项数据（含 sha16、耗时、字节数）见随包的 `references/comparison-data.json`。

## 0. 怎么复跑（三条命令）

```bash
SKILL_DIR=<本包目录>; CASE=<case.json>; TMP=<临时目录>

python "$SKILL_DIR/scripts/bare_baseline.py" --case "$CASE" --out "$TMP/c0"    # 无三层机制
python "$SKILL_DIR/scripts/main.py"          --case "$CASE" --out "$TMP/c1"    # 有全部机制
python "$SKILL_DIR/scripts/check.py" "$TMP/c1/<case_id>/result.json"           # 契约门 G1–G10
```

两个合成案例：
- `clean`：8 实体 / 7 关系，材料自洽（`case.json` sha256 前 16 位 `c7af792527dda9d6`）；
- `defective`：12 实体 / 13 关系，**预注入 5 类缺陷**（断头关系、非法类别、缺 `source`、
  重复 id、非法关系种类；sha256 前 16 位 `5afbea68e9c8ee84`）。

## 1. M1（证据中间层）的对照

| 观测量 | 无 M1 | 有 M1 | 缺陷案例（同上） |
|-|-|-|-|
| 有 `locator` 的元素 / 元素总数 | **0.00** | **1.00** | **1.00**（24 条证据 / 12 实体 + 12 关系） |
| 材料版本可查 | 无 | `evidence.source_files[].sha256` | 同左 |
| 元素↔材料双向回溯 | 无 | `element_traceability[]` + `evidence.items[].ref` | 同左 |

> 读法：M1 的差是**从"没有这个字段"到"每个元素都有出处"**，不是精度差异。

## 2. M2（确定性布局 + 规格探针）的对照

| 观测量 | 无 M2 | 有 M2 |
|-|-|-|
| 排版 | 固定 4 列网格 | 按图类选模板（route 分列 / apparatus 三桶 / flow 链路） |
| 同输入两轮 | 网格稳定（简陋所以稳定） | `figure.svg`/`layout.json`/`evidence.json`/`verify_report.json` **4/4 逐字节一致**（两个案例各验一次） |
| "是不是同一张图"的判据 | 只能肉眼 | `verify_report.json.determinism.spec_sha16` 一个指纹 |
| 三交付件同源 | 只有一个真 SVG | SVG/PNG/PDF 共享同一布局模型（PNG 39 136–47 080 B @200 DPI） |

> 注意：**"稳定"本身不是 M2 的卖点**（固定网格也稳定）。M2 的卖点是**稳定可证**
> ——上表第二行给了两侧；下界实现没有任何指纹可以让人对拍。

## 3. M3（规则资产机器审计）的对照

这一层的对照最关键，因为它需要排除"违规是别处顺带产生的"。
所以除了"无 M3"（下界实现），还跑了一个 **"同代码但审计关闭"** 条件：
`main.py --rules <空对象 json>`。

| 观测量 | 无 M3（下界实现） | 审计关闭（同代码 `--rules {}`） | 有 M3（正常） |
|-|-|-|-|
| 端点不存在的关系 | **照画**（外露 **1** 条） | 丢弃（外露 0） | 丢弃（外露 0） |
| 违规暴露条数 | **0** | **0** | **3**（error `no-self-loop`、error `sequence-step-only`、warn `recycle-review`） |
| `status` | 无该字段 | `partial` | `partial` |
| 退出码 | 0 | 3 | **3** |
| `figure.svg` sha16（缺陷案例） | `b5e603db8f30cdd8` | `46dcf42a9749a89c` | `46dcf42a9749a89c` |
| `layout.json` sha16（缺陷案例） | （无该文件） | `e661e8c3b770ecae` | `e661e8c3b770ecae` |
| `verify_report.json` sha16 | （无该文件） | `1c04d7a51ba92920` | `6ab174447ee34a4a` |

**这张表要点**：中间列与右列的 `figure.svg`/`layout.json` **sha 完全相同**，
唯一的差在 `verify_report.json` 与违规条数（0 → 3）。
⇒ 这 3 条违规**只能**来自规则审计这一层，不可能来自布图或渲染。

对照的另一个方向：**干净案例上两侧的违规都是 0**（无 M3 是 0，有 M3 也是 0）。
这说明 M3 不会凭空造出违规——它只在输入真的有结构性缺陷时说话。
这条负面观察同样收录在 `references/comparison-data.json` 里。

## 4. 三层一起看：产物形态的整体差

| 产物 | 无三层机制 | 有全部三层机制 |
|-|-|-|
| 可编辑源文件 | `figure.svg`（有 `<text>`？**0 个**，只有色块 `<rect>`） | 5 层 `layer:*`、真实 `<text>`、实体组带 `data-entity/data-source/...` |
| PNG 预览 | **0 字节占位** | 39 136–47 080 B（200 DPI，与画布 × DPI 一致） |
| PDF 预览 | **0 字节占位** | 4 028–4 522 B（reportlab 矢量，CID 字体 `STSong-Light`） |
| 证据链 | 无 | `evidence.json` + 回显进 `result.json.evidence` |
| 布局模型 | 无（几何只存在于一次性写出的 SVG 里） | `layout.json`（可复核、可重绘） |
| 校验报告 | 无 | `verify_report.json`（含 `spec_sha16`） |
| 状态与不确定性 | **无 `status` 字段**，无法表达"完成到哪一步" | `status`（`success`/`partial`）+ `uncertainty[].scope` + `change_record[]` |
| 输出总字节 | 2 491–3 814 B | 78 509–105 444 B |

> 字节数变大是**结果不是卖点**：多出来的是真 PNG/PDF 与四份结构化证据。
> 单轮耗时也同样变大（0.100–0.112 s → 0.497–0.593 s），本包**不**声称运行更快。

## 5. 这份摘要的边界

- 下界实现 `bare_baseline.py` 是**一个**反例实现，不代表所有既有方案；
- 只跑了 apparatus 图类的两个合成案例（route/flow/hybrid 未测）；
- 每条件一轮（避免"多跑几次取最好"的选择性报告），不做统计显著性结论；
- 这些数字**不构成**对平台正式评分的预测——正式案例与白板由平台提供；
- 想要机器可读的完整数据（含每次运行的 sha16 与耗时）请读
  `references/comparison-data.json`。
