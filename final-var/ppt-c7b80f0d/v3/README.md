# paper-to-academic-ppt · 机制与复用显性版（efficiency-3 / ppt-c7b80f0d）

把论文或研究材料转换成**主线清晰、证据可追溯、可编辑**的学术汇报 PPT 的 Skill 包。
本版（`v3`）沿 **创新增益（15 分）+ 生态贡献（10 分）** 两条轴做了实质增强：
不再只是"有这些功能"，而是把**机制**（哪些做法是别人不容易稳定实现的）、
**反事实**（没有它会怎样）与**复用路径**（别人怎么搬到自己的题上）全部写出来并可复核。
平台加载本 Skill 后在 3 个固定案例上真实运行；**本包不含任何预制答案**。

## 一、四份文档，四种问题

| 文档 | 回答的问题 | 亮点 |
|-|-|-|
| `references/MECHANISM.md` | 这套做法里**哪些是机制**、**没有它会怎样** | 9 项机制，每项四段（常规做法 / 本包做法 / 反事实 / 边界）；反事实要么是本机实测数字，要么是有据可查的真实故障 |
| `references/GAIN-PROTOCOL.md` | 怎么证明它更强 | 三臂同输入对照 + 14 个指标定义 + 两组真实记录 + §4.3 按机制读消融 |
| `references/REUSE-KIT.md` | 别人怎么把它搬走 | 五类可复用资产 + 五步移植流程（R1–R5）+ 移植检查清单 + "不可直接复用"清单 |
| `references/failure-modes.md` | 出问题时怎么办 | **六条回退链**逐级列明；§4 给出"降级 ⇒ 哪项机制失效"，防止把"没测"说成"通过" |

## 二、九项机制与"没有它会怎样"（一句话版）

| # | 机制 | 没有它会怎样 |
|-|-|-|
| M1 | 契约先行 + **文档-代码同源核对**（`check_contract.py` 读 Markdown 字段表） | 文档说 19 字段、实现只回显一部分，这种漂移不会被发现（本血脉确实发生过） |
| M2 | **方案先行 + 前置 lint 门**（先写页级 `deck-spec`，过 BL-1…BL-4 才生成） | 主张退化成 `SKELETON` 占位文本、证据行数 6→1、备注只覆盖 3/6 页（消融实测） |
| M3 | **双形态证据映射 + 行数守恒门 G7** | "讲了不存在的图"无法被机检；评审只能人眼抽查 |
| M4 | **占位框的诚实语义**（缺图只留占位框并登记） | 示意图被当成实验数据展示——题面点名的高频失败 |
| M5 | **OOXML 主题字体注入**（泛型 Part 双形态 + latin/ea 双写） | 换机字体被替换、版面崩坏；且注入失败是**静默**的（本血脉确实发生过） |
| M6 | **对象分层命名**（`claim-title-02`、`figure-06-Fig.-1`…） | "可编辑"只能是口头承诺，无法用脚本证明对象能被按名定位 |
| M7 | **运行时资源自生成**（包内只有 7 种文本扩展名） | 平台预检直接拒收整包（本平台已有 19 枪中 18 枪被拒的实测） |
| M8 | **三道关口 + 退出码语义 + 字节码卫生** | 非 UTF-8 控制台下"产物写好、进程却崩"；包里混进 `__pycache__` 使合规验收 FAIL |
| M9 | **自定位**（`$SKILL_DIR` / `__file__`） | 评测容器换目录后所有示例命令失败 → 判"没找到完整解"（本血脉确实发生过） |

逐条展开（含证据与复核命令）见 `references/MECHANISM.md` §2。

## 三、本版相对同族基线的实质改动（逐条）

| # | 位置 | 改了什么 |
|-|-|-|
| 1 | `references/MECHANISM.md`（**新增**） | 9 项机制 × 四段结构 + 机制依赖关系图 + 与已有方案的边界表 |
| 2 | `references/REUSE-KIT.md`（**新增**） | 五类资产清单（题集/金标准/校验清单/导出预设/配色与规范）+ 五步移植 + 检查清单 + 不可复用清单 |
| 3 | `references/GAIN-PROTOCOL.md`（**新增，含 v3 追加**） | 公平对照协议 + 指标定义 + 两组真实记录 + **§4.3 按机制读消融**（把差值归因到 M2） |
| 4 | `scripts/gain_probe.py`（**新增**） | 三臂对照执行件；只写 `--out`，且原地运行不留 `__pycache__` |
| 5 | `SKILL.md` | 全篇按**三层（机制/执行/证据）+ 复用**重写；阶段编号改为 1–7、关口 **K1–K3**、规则 **M01–M14**；新增 §6「机制 → 证据 → 复核命令」矩阵与 §7 复用段 |
| 6 | `references/failure-modes.md` | 重写为**六条回退链**（材料/图片/模板/字体渲染/契约/依赖）逐级列明；新增 §4「降级 ⇒ 哪项机制失效」 |
| 7 | `references/RUBRIC_MAP.md` | 重写为以**创新增益 + 生态贡献**为主轴；新增自评口径四条（防止把"没测"说成"通过"） |
| 8 | `TEST.md` | 新增机制消融实测、字节码卫生对照（0 vs 2）、**跨包可复现性**（v2/v3 同探针）、复用清单自检、沿革表 |

算法与既有 `scripts/*.py` 的 CLI 接口**未改动**（新增脚本是追加件，不改变任何既有入口）。

## 四、快速开始（任意 cwd 均可，`$SKILL_DIR` = SKILL.md 所在目录）

```bash
SKILL_DIR="<本包根目录>"        # 平台安装到 /skills/weekly-skill 时即该路径

# 1) 关口 K1：写完 deck-spec 后必跑
python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json

# 2) 端到端生成
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
  --spec /app/work/deck-spec.json --out /app/output

# 3) 关口 K3：两道交付门
python "$SKILL_DIR/scripts/export_check.py"  --result /app/output/result.json \
  --out-dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case /input/case.json

# 4) 可选：三臂增益对照（只写 --out；原地跑也不留 __pycache__）
python "$SKILL_DIR/scripts/gain_probe.py" --out "<scratch>" \
       --arms baseline,skill,ablation --repeat 2
```

产出（均在 `--out`）：`academic_deck.pptx`（可编辑、对象分层命名）、
`preview-approx-*.png`（PIL 近似，如实标注）、`evidence_mapping.md` +
`evidence_map.json`（双形态同源）、`result.json`（19 字段 + `case_id`）、
可选 `chart-*.png/.svg`（由论文表格数字重建）。

> ⚠️ **除 `gain_probe.py` 外，不要在包内直接跑脚本**：Python 会在 `scripts/` 下写
> `__pycache__`，而技能资源只允许文本文件，合规验收会直接 FAIL。实测对照见
> `TEST.md` T-C17（只跑 `gain_probe` → 0 个；再跑 `make_template.py` → 2 个）。

## 五、复用（五步，详见 `references/REUSE-KIT.md` §2）

| 步 | 做什么 | 关键点 |
|-|-|-|
| **R1 搬骨架** | 复制 `scripts/` + `references/OUTPUT_CONTRACT.md` + `layer-naming.md` | `SKILL.md` 只改 frontmatter 与"不负责"段 |
| **R2 换题面与输入契约** | 改 `OUTPUT_CONTRACT.md` §1 的字段清单，写新的 `examples/case.json` | **`check_contract.py` 不用改**——它读的就是这份文档（机制 M1 的红利） |
| **R3 换蓝图映射** | 改 `slide-blueprint.md` §1 的"输入结构 → 页面骨架"表与 §3 schema 语义 | BL-1…BL-4 通常无需改 |
| **R4 换配色与命名前缀** | 改 `deckgen.ACADEMIC_THEME` 色值；新对象类型先在 `ooxml_kit.PREFIX_BY_KIND` 注册前缀，再同步 `layer-naming.md` §2 | 配色与命名表必须同源 |
| **R5 跑校验并写回新数字** | 跑 `REUSE-KIT.md` §1.3 的五条命令；把新数字写进新包的 `TEST.md` 与 `GAIN-PROTOCOL.md` §4 | **禁止沿用旧数字**；最后跑一次包外 `validate_pkg.py` |

## 六、调用参数

| 参数 | 必填 | 说明 |
|-|-|-|
| `--case` | 是 | `case.json` 路径（给目录时取其内 `case.json`） |
| `--task` | 否 | `task.md`（存在时读取，advisory） |
| `--spec` | 否* | Agent 写好的页级 `deck-spec.json`；缺省仅 `--demo` 允许自动骨架 |
| `--materials` | 否 | 覆盖材料目录/文件（优先级高于 case 内声明） |
| `--out` | 是 | 输出目录（最终产物落位） |
| `--demo` | 否 | 允许自动骨架 spec（状态降 `partial`；也是消融臂） |
| `--verbose` | 否 | 打印 traceback |

`gain_probe.py`：`--case` / `--spec`（默认指向 `examples/`）、`--out`（**必填**）、
`--arms`（默认 `baseline,skill`，可加 `ablation`）、`--repeat`、`--json`、`--quiet`。

## 七、依赖

- 必需：Python ≥3.8、`python-pptx`、`Pillow`；
- 可选（逐级回退，见六条回退链）：PDF 解析 `PyMuPDF ≻ pypdf ≻ pdfplumber ≻ 外部 .txt`；
  重建图 `matplotlib`；预览字体 `C:/Windows/Fonts` → `/System/Library/Fonts` →
  `/usr/share/fonts` → PIL 默认（`SKILL_PREVIEW_FONT` 可覆盖）。
- 参考运行环境（见 `TEST.md`）：Windows 11 / Python 3.13.9 / python-pptx 1.0.2 /
  Pillow 12.3.0 / matplotlib 3.10.6 / PyMuPDF 1.28.0；**无 LibreOffice**。

## 八、目录结构

```
SKILL.md                        三层结构：机制/执行/证据 + 阶段 1–7 + K1–K3 + M01–M14
README.md                       本文件：机制速查、本版改动、复用五步、依赖、维护
TEST.md                         实测：15 条关口/回退链 + 4 条机制与对照 + 沿革表
GITHUB_URL.txt                  公开作品链接（单行）
references/MECHANISM.md         ★9 项机制 + "没有它会怎样" + 依赖关系 + 边界
references/REUSE-KIT.md         ★可复用资产清单 + 五步移植 + 检查清单
references/GAIN-PROTOCOL.md     ★公平对照协议 + 指标定义 + 真实记录 + 按机制读消融
references/failure-modes.md     六条回退链 + 降级⇒机制失效对照
references/RUBRIC_MAP.md        五维落点（以创新增益/生态贡献为主轴）+ 自评口径
references/OUTPUT_CONTRACT.md   result.json 顶层字段 + 四形态回显 + 硬性门 G1–G8
references/slide-blueprint.md   论文→页面蓝图映射 + deck-spec schema + 证据表格式
references/layer-naming.md      PPTX 分层命名规范（与 PREFIX_BY_KIND 同源）
scripts/main.py                 端到端入口（--case/--out 必填）
scripts/gain_probe.py           ★三臂对照执行件（只写 --out）
scripts/assetkit.py deckgen.py ooxml_kit.py   素材 / 生成 / OOXML 三层
scripts/spec_lint.py            K1 结构 lint
scripts/export_check.py         K3 导出检查（G1–G8）
scripts/check_contract.py       契约字段覆盖核对（读 Markdown 字段表）
scripts/preview.py              PIL 近似预览
scripts/make_template.py        运行期生成回退模板
scripts/make_synthetic_inputs.py  运行期生成合成夹具
scripts/cli_io.py               控制台加固
examples/                       最小示例（合成案例）：case/spec/task/材料/预期产物
```

## 九、限制

- 预览为**近似**渲染，非 PowerPoint/LibreOffice 实际结果；
- PDF 图片抽取依赖库与版式，个别图以显式占位框呈现（**不代表**论文原图）；
- 模板适配为"占位符级"，SmartArt 不重排；模板自带形状不改名；
- **对照口径**：`baseline` 是结构性代理而非具体 LLM 的测量；`wall_seconds` 只反映
  脚本开销（`TEST.md` T-C18 显示结构指标跨包一致、时间会波动）；权威口径是平台白板对照；
- 结论正确性上限 = 论文原文；本 Skill 不验证论文结论；
- 单一示例案例上的机制消融不能外推到所有论文类型。

## 十、失败处理与维护

- 六条回退链、退出码语义与"降级 ⇒ 哪项机制失效"见 `references/failure-modes.md`
  （与 `SKILL.md` §5 的 M01–M14 同号）；一切降级同时写入 `uncertainty` 与 `change_records`。
- 版本号在 `scripts/main.py` 的 `VERSION`（当前 `2.1.0`）。
- **三处同步铁律**：改机制 → `MECHANISM.md`（必须仍能回答"没有它会怎样"）；
  改规则 → `failure-modes.md` 同号条目；改指标/数字 → `GAIN-PROTOCOL.md` §3–§4 与
  `TEST.md`（**禁止沿用旧数字**）。新增可复用资产 → `REUSE-KIT.md` §1 追加一行。
