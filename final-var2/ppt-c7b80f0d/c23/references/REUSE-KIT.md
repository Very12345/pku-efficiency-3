# REUSE-KIT.md — 可复用资产清单与复用步骤

> 本文件是 **生态贡献（10 分：文档完整性 3 · 资源可复用性 4 · 分享推广价值 3）** 的落点。
> 它把本包里"别人可以直接拿走用"的东西列成清单，并给出**从零移植到另一道
> 「文档 → 演示」题**的五步流程与验收清单。所有资产都是文本文件，可整目录复制。

## 1. 可复用资产清单

### 1.1 题集（最小可跑案例）

| 资产 | 位置 | 形态 | 怎么用 |
|-|-|-|-|
| 示例案例输入 | `examples/case.json` | JSON | 演示"契约在 case 里怎么声明"（含布尔形态与清单形态两种字段） |
| 示例任务说明 | `examples/task.md` | Markdown | 演示"任务说明与页数/受众约束怎么写" |
| 示例页级方案 | `examples/deck-spec.json` | JSON | **可直接当页级大纲模板**：6 页、含 `figure/table/evidence/notes` 全字段 |
| 合成论文材料 | `examples/materials/paper-mini.txt` | 纯文本 | 管道回归用；人物/机构/数值均虚构，明确标注"非正式案例" |
| 预期产物清单 | `examples/EXPECTED-OUTPUT.md` | Markdown | **金标准的文字形态**：13 个输出文件 + 19 个契约字段的期望值 |

> 正式案例由平台提供；本包不预置任何正式答案（这是题面硬要求）。

### 1.2 金标准与验收阈值

| 资产 | 位置 | 判据 |
|-|-|-|
| 契约字段清单（19 项） | `references/OUTPUT_CONTRACT.md` §1 | `check_contract.py` 读到 `19/19`、`missing=[]`、`present_but_null=[]` |
| 硬性门 G1–G8 | `references/OUTPUT_CONTRACT.md` §5 | `export_check.py` `valid=true`、`errors=[]` |
| 蓝图规则 BL-1…BL-4 | `references/slide-blueprint.md` §1 | `spec_lint.py` `{"valid": true}` |
| 命名前缀表 | `references/layer-naming.md` §2 | `.pptx` 内形状名命中前缀；命名审计无 unnamed/auto 告警 |
| 内容确定性阈值 | `TEST.md`（确定性项） | 同输入两跑：`differing` OPC 部件 = **0**（实测 72/72 一致） |
| 增益指标判据 | `references/GAIN-PROTOCOL.md` §3 | 见下表 §1.3 |

### 1.3 校验清单（五条命令，可整段粘走）

```bash
SKILL_DIR="<包根>"
python "$SKILL_DIR/scripts/spec_lint.py"     --spec <work>/deck-spec.json          # 关口 1：蓝图
python "$SKILL_DIR/scripts/main.py"          --case /input/case.json \
  --task /input/task.md --spec <work>/deck-spec.json --out /app/output             # 端到端
python "$SKILL_DIR/scripts/export_check.py"  --result /app/output/result.json \
  --out-dir /app/output --case /input/case.json                                    # 关口 3：G1–G8
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md"                            # 契约覆盖
python "$SKILL_DIR/scripts/gain_probe.py"    --out <scratch> \
  --arms baseline,skill,ablation --repeat 2                                        # 增益对照
```

| 命令 | 通过判据 | 失败时看哪 |
|-|-|-|
| `spec_lint` | exit 0 且 `{"valid": true}` | `problems[]` 逐条；处置见 `failure-modes.md` Q1 段 |
| `main.py` | exit 0 且 `self_check.ok=true` | `run_meta.self_check.problems`；`status`/`uncertainty` |
| `export_check` | exit 0 且 `errors=[]` | `errors[]` 逐条给出违反的门号（G1–G8）与对象路径 |
| `check_contract` | exit 0 且 `missing=[]` | 缺哪个字段直接补 `output_contract` 回显 |
| `gain_probe` | exit 0；`skill.rework_points=0` | `<scratch>/gain-report.json` 的 `rework[]` 原文 |

### 1.4 导出预设（可直接改字段名复用）

| 预设 | 位置 | 复用点 |
|-|-|-|
| 页级方案 schema | `references/slide-blueprint.md` §3 | 换题目时**只换字段语义**，结构与 lint 规则不动 |
| 论文结构 → 页面骨架映射表 | `references/slide-blueprint.md` §1 | 把"问题→方法→证据→结论→局限"换成别的叙事骨架即可 |
| 逐页证据映射表格式 | `references/slide-blueprint.md` §2 | md 表列固定为 `页 / 标题 / 主张 / 证据定位 / 状态` |
| 契约四形态回显规则 | `references/OUTPUT_CONTRACT.md` §2 | 任何"case 声明字段 → result 回显"的题都通用 |
| 退出码语义 | `references/failure-modes.md` §1 | `0 通过 / 1 门未过 / 2 资源不可用 / 3 输入不可读` |
| 对照指标定义 | `references/GAIN-PROTOCOL.md` §3 | 14 个指标可直接搬去做别的"文档→产物"题的对照 |

### 1.5 配色与规范

| 资产 | 位置 | 值 / 规则 |
|-|-|-|
| 学术配色（`ACADEMIC_THEME`） | `scripts/deckgen.py` | `primary #1F4E79`（深学术蓝）· `accent #2E74B5` · `light #F2F7FC` · `ink #262626` · `muted #595959` · `warn #C0504D` · `white #FFFFFF` |
| 字体策略 | `scripts/ooxml_kit.py` | 主题 major/minor 注入 + run 级 **latin + east-asian 双写**；预览字体跨平台探测，失败降级并记录 |
| 诚实标注规范 | `references/OUTPUT_CONTRACT.md` §4 | 预览必须 `preview-approx-*` + `kind=pil-approximation` + `rendered_with` 三处标注；重建图必须写 `reconstructed_from_table`；缺失图只留占位框 |
| 命名规范 | `references/layer-naming.md` | `<kind>-<NN>[-<safe-ref>]`；模板自带形状不改名 |
| 交付目录形态 | `README.md` 目录结构节 | 根 `SKILL.md` + `references/` + `scripts/` + `examples/`，全部为 7 种文本扩展名 |

## 2. 从零移植到另一道「文档 → 演示」题（五步）

**R1 搬骨架**：把 `scripts/`（除 `gain_probe.py` 可按需保留）、`references/OUTPUT_CONTRACT.md`、
`references/layer-naming.md` 原样复制到新包；`SKILL.md` 只改 frontmatter 的 `name/description`
与"不负责"段落。

**R2 换题面与输入契约**：改 `references/OUTPUT_CONTRACT.md` §1 的字段清单
（**必须同时改 `check_contract.py` 无需改动**——它读的是文档，所以改文档即可）；
把新题的 `output_contract` 声明写进新的 `examples/case.json`。

**R3 换蓝图映射**：改 `references/slide-blueprint.md` §1 的"输入结构 → 页面骨架"表，
以及 §3 schema 里各字段的语义说明；`spec_lint` 的 BL-1…BL-4 一般不需要改
（"一页一主张 / 短语化 / 证据或显式 gap / 页序"对大多数演示题都成立）。

**R4 换配色与命名前缀**：改 `scripts/deckgen.py` 的 `ACADEMIC_THEME` 色值；
新增对象种类时先在 `scripts/ooxml_kit.py` 的 `PREFIX_BY_KIND` 注册前缀，
再同步 `references/layer-naming.md` §2 的表格。

**R5 跑对照与验收**：依次跑 §1.3 的五条命令；把新跑出的数字写进新包的
`TEST.md` 与 `references/GAIN-PROTOCOL.md` §4（**禁止沿用旧数字**）；
最后跑一次包外 `validate_pkg.py`。

## 3. 移植检查清单（逐条勾）

- [ ] 包内只有 7 种扩展名；无 `__pycache__`/`.pyc`；文件数 ≤50、单文件 ≤500KB、合计 ≤2MB；
- [ ] 包内无本机绝对路径（字体探测候选路径除外，且已点名说明）；
- [ ] `SKILL.md` 的命令全部用 `$SKILL_DIR`；脚本 `__file__` 自定位；
- [ ] `references/OUTPUT_CONTRACT.md` 的字段块**未被改名**；`check_contract.py` 读到同一清单；
- [ ] 三道关口（lint / 构建 / 导出检查）都能 exit 0；
- [ ] 契约 19 字段全覆盖、无 null；`case_id` 与 case 逐字一致；
- [ ] 同输入两跑 OPC 部件差异为 0；
- [ ] 写进文档的每个数字都能用 §1.3 的命令复跑出来；
- [ ] 已明确写出"哪些结论**不能**从这个对照里推出"（口径边界）。

## 4. 已知不可直接复用的部分（诚实声明）

| 内容 | 为什么不能直接复用 |
|-|-|
| `examples/materials/paper-mini.txt` | 是**合成**论文（ExampleNet 等均虚构），只能当管道夹具，不能当科研材料 |
| `TEST.md` / `GAIN-PROTOCOL.md` §4 的具体数字 | 依赖本机环境（Python 3.13.9 / python-pptx 1.0.2 / 无 LibreOffice）与示例案例规模；换机换案例必须重跑 |
| `scripts/deckgen.py` 的模板适配分支 | 依赖"占位符级"策略；遇到 SmartArt 等复杂版式不重排（已在限制里声明） |
| 真实组织方模板 | **不随包携带**（技能资源只允许文本文件）；由案例提供或 `make_template.py` 运行时现产 |
| 三条平台级实测记录（预检拒收、相对路径判词、主题字体静默失败） | 属于**本平台本轮**的观测，换平台/换版本需重新取证 |

## 5. 分享推广价值

- **可分享的实践**：把"演示类交付物"的验收从主观判断变成五条命令 + 硬性门；
  把"更强"从形容词变成三臂可复跑对照（`GAIN-PROTOCOL.md`）；
  把"可编辑"从承诺变成对象命名这一可机检量（`named_shapes`）。
- **可迁移的题面**：任何"把长文档变成离散页级表达 + 必须保留溯源 + 必须适配给定模板"的
  任务，都能直接套 R1–R5；蓝图骨架换成"背景→方案→对比→取舍→风险"即可用于技术方案汇报。
- **公开入口**：`GITHUB_URL.txt` 第一行即本作品目录链接（提交前请用未登录窗口确认可打开）。

## 6. 维护

- 新增可复用资产 → 追加到 §1 对应小节，并写清"位置 / 形态 / 怎么用"三列；
- 资产被改名或搬移 → 同步更新本文件与引用它的 `README.md` 目录结构；
- 移植步骤若因脚本变化失效 → 先修 §2 步骤，再改实现，避免"文档承诺 > 代码事实"。
