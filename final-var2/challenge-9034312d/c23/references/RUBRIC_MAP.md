# RUBRIC_MAP.md — 评分五维落点（v3 机制与复用显性化版）

题面评分维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10
· GitHub 链接 +5**。本文件按**两个重点维度**编排：**创新增益（15）**与**生态贡献（10）**
——基线在这两栏给的是"有这个机制""有这些资产"的清单，本版给的是
**机制的反例对照**与**资产的复用说明**。

**一句话定位**：把散在功能描述里的设计收敛成**三层串联机制**（M1 证据中间层 /
M2 确定性布局与规格探针 / M3 规则资产的机器审计），逐层给出"没有它会怎样"的
**可执行对照**（`references/COMPARISON-SUMMARY.md`），并把配套资产整理成
**7 类 15 项 + 四步复用流程 + 三个陷阱**（`references/REUSE-GUIDE.md`）。

## 0. 五维速查

| # | 维度 | 分 | 落点 | 可复跑验证 |
|-|-|-|-|-|
| 1 | 实际效果 | 40 | `main.py` 一键出图 + 可编辑分层 SVG + 真实 PNG/PDF + 四份 JSON | 四形态实测 `exit 0`；契约 18/18；G1–G10 全过 |
| 2 | 使用增益 | 25 | 三层机制带来的可核验性差异 + `GAIN-PROTOCOL.md` + `gain_probe.py` | 对照摘要 §1–§3 |
| 3 | **创新增益** | **15** | **`MECHANISM.md`（三层机制 + 每层"没有它会怎样"）+ `COMPARISON-SUMMARY.md`（实测）+ C2 条件（同代码关掉审计）** | §3 的三张对照表 |
| 4 | 可靠体验 | 10 | D1–D16（按机制层/结构层/交付层分组）+ 状态聚合优先级 + 退出码语义 | 负例 `exit 3` |
| 5 | **生态贡献** | **10** | **`REUSE-GUIDE.md`（15 项资产 + 四步流程 + 三陷阱）+ 规则资产/契约骨架/复算器 + `GITHUB_URL.txt`** | §5 的资产清单 |
| +5 | GitHub | 5 | `GITHUB_URL.txt` | 未登录浏览器可打开 |

## 1. 实际效果（40）= 完成度15 + 正确性15 + 完整性5 + 可核验性5

| 评分点 | 覆盖 | 证据 |
|-|-|-|
| 完成度 15 | 材料 → 可编辑分层 SVG（5 层、真实 `<text>`、实体组带 `data-*`）+ 真实 PNG（39–47 KB @200 DPI）+ 矢量 PDF + 四份结构化产物 | `scripts/main.py`；`TEST.md` T2 |
| 正确性 15 | M1 逐条溯源 + M3 规则审计（含断头丢弃、自环拦截、sequence 语义、装置图物料不作终点） | `gain_evidence.py`；`svg_verify.py`；对照摘要 §3 |
| 完整性 5 | 题面六类要素全覆盖（实体/空间关系/数据编码/图例/可编辑源文件/导出格式） | `layout.json`；`figure.svg` 五层；`templates/palette.json` |
| 可核验性 5 | 四份 JSON 落盘 + 确定性探针 `spec_sha16` + **三层机制各有可执行反例对照**（别人能自己把机制拿掉再比） | `COMPARISON-SUMMARY.md §0`（三条命令）；`comparison-data.json` |

## 2. 使用增益（25）= 质量15 + 效率5 + 增益可验证性5

| 评分点 | 覆盖 | 证据 |
|-|-|-|
| 质量增益 15 | M1：来源绑定率 **0.00 → 1.00**；M3：缺陷输入上违规暴露 **0 → 3**、断头外露 **1 → 0**；M2：PNG/PDF **0 字节 → 真实导出件** | `COMPARISON-SUMMARY.md §1–§4` |
| 效率增益 5 | E3 人工干预步骤 ≥3 → **0**；E4 返工轮次 1 → **0**（`--merge` 增量）。**运行效率无增益**（0.10 s → 0.50–0.59 s），如实记录 | `COMPARISON-SUMMARY.md §4`；`GAIN-PROTOCOL.md §4.3` |
| 增益可验证性 5 | 三条件（无机制 / 有机制 / 同代码关掉审计）× 四个固定项 + 预注册指标 + 独立复算器（不 import 包内模块） | `GAIN-PROTOCOL.md`；`scripts/gain_probe.py` |

## 3. 创新增益（15）= 新增能力5 + 方法改进5 + 创新证据5

### 3.1 新增能力（5）：三层机制

| 层 | 能力 | 没有它会怎样（实测） |
|-|-|-|
| M1 证据中间层 | 每个图面元素带 `locator`+`quote`；每份材料带 `sha256`/`size`/`role` | 来源绑定率 **0.00**（产物里没有这个字段） |
| M2 确定性布局 + 规格探针 | 纯函数布图 → 三后端共享几何 → `spec_sha16` 指纹 | 无 `layout.json`、无指纹可对拍；PNG/PDF 为 0 字节占位 |
| M3 规则资产机器审计 | 连接语义做成可编辑 JSON，按 severity 决定降级或仅提示 | 断头照画（外露 **1** 条）、违规暴露 **0** 条 |

### 3.2 方法改进（5）：三层为什么是串联而不是并列

| 若只保留 | 会失去什么 | 后果 |
|-|-|-|
| 只有 M1 | 元素可追溯但没有稳定几何与语义审计 | 仍靠人眼查连接 |
| 只有 M2 | 图面稳定但元素来源与连接正确性无人过问 | **稳定地画出错误结构**（比不稳定更危险） |
| 只有 M3 | 能发现违规但审计对象本身在变 | 违规结论不可复现 |
| 三层齐备 | — | 元素可回溯 → 几何可复现 → 语义可审计 |

**归因设计（本版关键方法改进）**：为了让"M3 抓到的违规"不被误算成别处的功劳，
本版引入 **C2 条件**——同一份代码只把 `--rules` 指向空对象文件。
实测 C1 与 C2 的 `figure.svg`/`layout.json` **sha 完全相同**，只有
`verify_report.json` 与违规条数不同（3 → 0）。⇒ 这 3 条违规**只能**归因于 M3。

### 3.3 创新证据（5）

| 证据 | 内容 |
|-|-|
| 边界文档 | `MECHANISM.md §6` 明确写出"这份文件不能证明什么"（不能预测分数、不证明三层是唯一正确设计、下界实现只是一个反例） |
| 机制↔题材迁移表 | `MECHANISM.md §5`：每层"要换什么、不用换什么" |
| 负面结果 | 干净输入上 M3 两侧违规都是 0；运行效率无增益——两条都写进记录 |
| 反例实现 | `scripts/bare_baseline.py`：把三层全拿掉的可运行代码（不是假想） |

## 4. 可靠体验（10）= 调用易用3 + 运行稳定4 + 异常处理3

| 评分点 | 覆盖 | 证据 |
|-|-|-|
| 调用易用性 3 | 单命令出图；`SKILL.md §3` 给出接口，并特别说明 `--rules`/`--palette` **换的是机制的数据层**；脚本自定位、任何 cwd 可运行 | `SKILL.md §3`；`TEST.md` T2/T5 |
| 运行稳定性 4 | 结构化/文本解构双路径；M2 无随机（4 文件 × 2 案例逐字节一致）；`--rules`/`--palette` 指向异常时静默降级 | `TEST.md` T3；`COMPARISON-SUMMARY.md §2` |
| 异常处理 3 | D1–D16 **按层分组**（机制层 8 条 / 结构层 7 条 / 交付层 1 条），每层归属一目了然；退出码 0/1/2/3 语义明确 | `SKILL.md §6/§7`；`references/failure-modes.md`；负例 `exit 3` |

## 5. 生态贡献（10）= 文档3 + 复用4 + 分享3

### 5.1 文档完整性（3）

使用说明（`README.md`，含 `§0 这一版改了什么`）、输入约定与调用（`SKILL.md §3`）、
图元规范（`references/figure-blueprint.md`）、导出参数（`SKILL.md §4` 产出表）、
示例与期望产物（`examples/README.md` + `EXPECTED-OUTPUT.md`）、限制（含四条机制相关边界）、
维护（含"改一层要复核机制文档"的纪律）。

### 5.2 资源可复用性（4）—— 本版的正面回答

| 资产类 | 项数 | 代表项 | 可独立复用性 |
|-|-|-|-|
| A 规则与词表 | 3 | `assets/connection_rules.json`（**改 JSON 即改审计结论**） | ★★★ 拿走只改数据 |
| B 结构与证据 | 4 | `evidence.json` 清单格式、`verify_report.json` 字段结构、`spec_sha16` 思路 | ★★★ 格式可原样沿用 |
| C 校验与门禁 | 3 | `check.py`（G1–G10）、`svg_verify.py`、**R1–R6 打包门（一行都不用改）** | ★★★ |
| D 判据与用例 | 3 | 三条对照命令、对照数据字段布局、`gain_probe.py` 指标算法（不 import 包内模块） | ★★★ |
| E 文档骨架 | 2 | 契约文档组织方式、DECISION-CASES/GAIN-PROTOCOL 的"期望 vs 实测"表式 | ★★ |
| F 运行期实现 | 3 | `layout.py` 模板机制、`render_svg.py` 分层写法、`bare_baseline.py`（反例方法本身） | ★★ |
| G 清单模板 | 2 | 组件连接核对清单、实体关系核对表 CSV | ★★★ |

完整清单（每项写清"拿走要改什么"）与四步复用流程、三个搬运陷阱见 `references/REUSE-GUIDE.md`。

### 5.3 分享推广价值（3）

沉淀可分享的**图例规范、布局经验、连接规则字典、失败清单与打包门 R1–R6**，
外加两件更有推广价值的产物：**三层机制的价值论证方法**（拿掉它再比）
与**资产复用流程**（选层 → 换数据 → 接门禁 → 自证）。
公开入口：`GITHUB_URL.txt`。

## 6. GitHub 公开作品链接（+5）

- `GITHUB_URL.txt` 第一行：公开作品位置直链；可选第二行写相对文件路径；
- 题面要求提交前用未登录浏览器打开一次；本包不含需登录的地址。

## 7. 改包后的自检顺序

```bash
SKILL_DIR=/skills/weekly-skill

# 1) 功能没坏
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/out      # exit 0
python "$SKILL_DIR/scripts/check.py" /tmp/out/demo-biotech-route-01/result.json      # exit 0

# 2) 三层机制的价值仍可复现（本版核心自检）
python "$SKILL_DIR/scripts/bare_baseline.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/c0
printf '{}' > /tmp/empty-rules.json
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
       --rules /tmp/empty-rules.json --out /tmp/c2
#   期望：/tmp/out 与 /tmp/c2 的 figure.svg / layout.json sha 相同，verify_report.json 不同

# 3) 指标可独立复算（不依赖包内模块）
python "$SKILL_DIR/scripts/gain_probe.py" --result /tmp/out/demo-biotech-route-01/result.json

# 4) 负例（异常必须被暴露）
python "$SKILL_DIR/scripts/main.py" --case <违例案例> --out /tmp/neg     # 期望 exit 3, status=partial
```

## 8. 覆盖缺口（诚实声明）

- **机制对照只跑了 apparatus 图类的两个合成案例**（route/flow/hybrid 未测）；
  迁移性论断依据是"机制与题材解耦"，不是实测；
- **下界实现只是一个反例**：换一个更聪明的既有方案，三层与它的差距会缩小；
  但三层各自解决的可观测问题（不可回溯 / 不可复现 / 无审计）不会消失；
- **`evidence.json` 的 sha 跨目录会变**（记运行时真实输入路径）：一致性对拍请用
  `figure.svg`/`layout.json`/`verify_report.json`；
- **M3 只审结构语义，不判科学正确性**；类别非法值被静默归一化、关系全断头时退化成顺序链
  这两条"安静"行为已点名并给出复核办法（`SKILL.md §9`）；
- 图内数值注记不强制渲染；局部放大视图未内置；装置图为单层装配；
- `examples/` 是**合成**示例（标注「示例，非正式案例」），不含预制答案，不冒充正式结果；
  包内冻结的 `examples/output/**/result.json` 因不含运行期图稿，对它跑 `check.py`
  会如实报 G3/G4——正确自查对象是新跑出来的那份。
