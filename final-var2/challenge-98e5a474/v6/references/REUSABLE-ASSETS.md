# REUSABLE-ASSETS — 可复用资产清单与采纳阶梯

本文件回答一个具体问题：**如果别人（或别的技能题）想用本包的成果，
可以拿走哪一块、怎么拿、拿完怎么知道拿对了。**

清单分四类：**题集与金标准**、**规范与字典**、**校验与对拍工具**、
**预设与模板**。每项给出：资产位置、复用方式、依赖、以及**采纳验证**
（拿对没拿对，怎么一眼看出）。

## 1. 资产总表（A1–A12）

| # | 资产 | 位置 | 类型 | 复用方式 | 采纳验证 |
|-|-|-|-|-|-|
| **A1** | 合成示例题集（schematic / chart / edit 三件套 + 合成材料） | `examples/case.json`、`examples/case_chart.json`、`examples/case_edit.json`、`examples/sources/*` | 题集 | 直接当新技能的回归夹具；或改造成新案例（保持字段结构） | `run_examples.py --out <tmp>` **exit 0** 且三份契约各 VALID |
| **A2** | 期望产物清单（文字版金标准） | `examples/EXPECTED-OUTPUT.md` | 金标准 | 作为"应该产出什么"的对照表；新案例照抄结构填新值 | 逐条对照真实产物：文件齐全、字段取值一致 |
| **A3** | ER 清单规范 | `references/ER_MANIFEST.md` | 规范 | 任何"材料→结构图"任务都可直接采用（实体/关系/分组/图例/data/style 六块） | 用 `scripts/manifest.py <m.json>` 规范化不报错；`spec_lint.py` 能判 valid/invalid |
| **A4** | 图形语法规范（关系语义→箭头/线型/颜色、方向判定、分组/层级） | `references/DRAWING_GRAMMAR.md` | 规范 | 迁移到任何"关系图"类技能；给 LLM 当判定依据 | 构造一对"激活 vs 抑制"关系，判定结果必须不同 |
| **A5** | 连接规则字典（机器可读） | `assets/relation-dict.json` | 字典 | 直接加载：`kind → {arrow, line, dash, color}`；spec_lint / 渲染 / 图例三方共用 | 7 类规范 kind 全部能在字典里找到；缺一类则 `spec.relation_dict` 报 fail |
| **A6** | CP1–CP5 检查点清单（机器可读） | `assets/checklist.json` | 清单 | 当作"验收脚本的条目来源"；或用于生成人工复核表 | 文件里 CP1..CP5 五个 id 齐全（`selftest.py` 有断言） |
| **A7** | 契约校验器（G1–G8 硬门） | `scripts/validate_result.py` | 工具 | 任何"必须产出结构化 result.json"的技能都能改用它的门模型 | 对**缺产物**与**假成功**两种坏输入必须非 VALID（`selftest.py` 有断言） |
| **A8** | 检查名索引（含级别与科学含义） | `references/CHECK-INDEX.md` | 字典 | 把"检查名 → 含义"当术语表；新技能照此给自己定名 | 索引里的每个检查名都能在 `scripts/` 里找到；`doccheck.py` 自动对拍 |
| **A9** | 文档↔代码一致性对拍器（只读） | `scripts/doccheck.py` | 工具 | **与本题无关的纯工具**：任何有"文档承诺 + 代码产出"的项目都能用 | `--json` 输出结构稳定；对本包自身 exit 0；对故意加一个假检查名的副本 exit 1 |
| **A10** | 源文件自描述模式（内嵌清单 + `data-*` 属性） | `scripts/svgbuilder.py`、`scripts/edit.py` | 模式 | 任何"可编辑图稿"任务都可照此把语义写进产物本身 | `--edit-svg` 指向**无内嵌清单**的 SVG 必须被拒（exit 2） |
| **A11** | 字体探针（候选族 + 确定性结论） | `scripts/textfont.py` | 工具 | 任何要渲染 CJK 的技能都可复用（--list/--probe 两个入口） | 同机两次 `--probe` 结论一致；`--list` 逐候选打印命中情况 |
| **A12** | 导出预检清单（DPI/色彩/文字可编辑/PDF/字体） | `scripts/checks.py`、`references/OUTPUT_CONTRACT.md` §4 | 清单 | 当作"导出前必查项"的模板；阈值可按目标期刊改 | 把 `--dpi` 降到阈值下必须触发 `bitmap.dpi_print` 非 ok（**M4 的推翻实验**） |

## 2. 采纳阶梯（L0–L4）：按改造成本从低到高

| 级 | 名称 | 拿什么 | 改什么 | 验证 | 适合谁 |
|-|-|-|-|-|-|
| **L0** | 只读参考 | 规范类：A3 / A4 / A8 / A12 | 不改，只当文档读 | 无（阅读即可） | 想理解"关系图该怎么建模"的人 |
| **L1** | 直接复用工具 | A7（契约校验器）、A9（对拍器）、A11（字体探针） | 只改调用路径（命令里的 `$SKILL_DIR`） | 各工具自己的最小自测：A7 对坏输入非 VALID、A9 对自身 exit 0、A11 两次结论一致 | 已有自己的流水线，只缺校验/对拍/字体探测 |
| **L2** | 复用夹具与字典 | A1（题集）、A2（金标准）、A5（关系字典）、A6（检查点清单） | 换案例内容，保留字段结构与文件形态 | `run_examples.py --out <tmp>` 在**改造后**仍 exit 0；或新写一个等价的复现脚本 | 要给自己的技能做回归测试的人 |
| **L3** | 复用模式 | A10（源文件自描述） | 需要改渲染层：把语义写进产物、实现"读产物做增量编辑" | 两条不变式：无内嵌清单必须被拒；编辑后未改动元素保持一致 | 做"可编辑图稿/可编辑文档"类技能的人 |
| **L4** | 整套方法 | 全部 + `SKILL.md` 的机制/决策结构 | 换成自己领域的机制与判据（M1–M5 换成自己的 M'） | 每个新机制都要有"没有它会怎样"与"可证伪判据"，且判据要有实测读数 | 要从零做一道同类技能题的人 |

> **不建议的采纳方式**：把本包的机制名原样抄进别的领域（例如把
> "containment 必须分组"套到没有包含关系的任务上）。机制的价值在于
> "判据可被观测"，不在于名字。

## 3. 复用步骤（照着做）

### 3.1 只想用校验器（L1，约 5 分钟）
```bash
# 1) 复制工具（单文件、纯标准库）
cp "$SKILL_DIR/scripts/validate_result.py" <你的项目>/tools/
# 2) 用你自己的 result.json 与 case.json 跑一遍
python <你的项目>/tools/validate_result.py --case <你的 case.json> --result <你的 result.json>
# 3) 确认它对自己的坏输入也会拒绝（这一步不能省）
#    构造一个 artifacts 为空的结果 → 必须出现 G7 的 INVALID
```

### 3.2 想给自己的文档做一致性对拍（L1，约 10 分钟）
```bash
cp "$SKILL_DIR/scripts/doccheck.py" <你的项目>/tools/
python <你的项目>/tools/doccheck.py --root <你的项目根> --json
# 输出：check ids 文档/代码 对照、规则编号缺号、缺失的 --flag
```
`doccheck.py` 的设计前提只有两条：① 代码里用带点小写标识符报检查名；
② 文档是 markdown。不满足这两条时它会报环境错误（exit 2）而不是瞎猜。

### 3.3 想复用题集做回归（L2，约 30 分钟）
```bash
cp -r "$SKILL_DIR/examples" <你的项目>/tests/fixtures/sse/
# 改 fixtures 里的 case.json / 材料，保持字段结构
python <你的项目>/scripts/run_examples.py --out /tmp/your-regression
```
**验收**：三步（schematic / chart / edit）各 exit 0，且三份 `result.json`
过你自己版本的契约门。若你把契约也换了，**必须同时换判据**（别用旧门判新字段）。

### 3.4 想复用"源文件自描述"模式（L3，约半天）
两个必须一起做的事：
1. **写进去**：渲染时把语义清单嵌进产物（本包用 `<metadata id="er-manifest">` + `data-*`）；
2. **读出来**：编辑入口先尝试从产物里读清单，读不到就**明确拒绝**而不是猜。
```bash
# 拒绝路径必须真实存在（否则"自描述"只是个说法）
python <你的项目>/edit.py <无内嵌清单的产物>   # 期望：非零退出 + 明确说明
```

## 4. 复用时最容易踩的三个坑

| 坑 | 现象 | 正确做法 |
|-|-|-|
| 只抄文件不抄判据 | 工具能跑，但不知道"什么算通过" | 连同 `references/CHECK-INDEX.md` 的级别语义一起抄；明确 fail/warn 的分界 |
| 改判据后不更新文档 | 文档说 A，代码做 B | 复用时把 `doccheck.py` 一并引入，让它替你发现漂移 |
| 把"示例"当"正式答案" | 复用了示例夹具，却把它当比赛答案交出去 | 示例明确标注"示例，非正式案例"；正式案例由平台提供 |

## 5. 与其它变体的关系（供评审理解本包定位）

- 本包（v3）包含"机制显性化"与"复用显性化"两条轴；
  决策规则与失败分支的**权威描述**仍在 `references/failure-modes.md`
  与 `SKILL.md` §5/§6（本包不重复展开，只把每条分支指到受影响机制）；
- 因此复用时若要完整理解"出错时会怎样"，应同时读
  `references/failure-modes.md`（现象→处置）与 `references/MECHANISM.md`
  （机制→判据→盲区）——**前者回答"怎么办"，后者回答"凭什么相信它是有效的"**。

## 6. 资产的许可与来源（如实说明）

- 全部资产均为本作品原创（脚本、规范、字典、示例夹具），随包提供；
- 示例材料（`examples/sources/*`）是**合成内容**，不来自任何真实论文，
  也不含任何第三方数据；
- 包内不含字体文件、不含二进制资源；字体探测只**读取**系统字体目录的
  可用性，不分发字体；
- 复用本包资产时请保留 `references/CHECK-INDEX.md` 与
  `references/OUTPUT_CONTRACT.md`（它们是判据的一部分，不是可选文档）。
