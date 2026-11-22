# RUBRIC_MAP.md — 五维评分逐条映射（v3 机制与复用版）

原题满分 100：**实际效果 40 / 使用增益 25 / 创新增益 15 / 可靠体验 10 / 生态贡献 10**，
另加 GitHub 公开作品链接附加分 5。本版把重点放在**创新增益 15** 与**生态贡献 10**：
用 `references/MECHANISM.md` 说清八个不可省略的机制（各带"没有它会怎样"与可证伪判据），
用 `references/REUSE-KIT.md` + `assets/` 把可复用资产与复用步骤落到具体文件。
实测命令与观测见 [TEST.md](TEST.md)，对照协议见 [references/GAIN-PROTOCOL.md](references/GAIN-PROTOCOL.md)。

## 1. 实际效果（40 分）

| 评分点 | 分 | 本包落点 | 判定 |
|-|-|-|-|
| 任务完成度 | 15 | 一条命令闭环（P1–P7）；页数按时长推导并校准到冻结页数（M1/M3） | 退出码 0；`plan_gates.gates[P3] pages=12 target=12`（`TEST.md` §2/§5） |
| 结果正确性 | 15 | 页内容逐字取自源材料；逐字证据审计 + 行号区间 + 数字对源（M2） | `audit.evidence.summary{content_pages:10, ok_pages:10, errors:0}` |
| 结果完整性 | 5 | 主线 / 页结构 / 图表引用 / 讲解逻辑 / 模板约束 / 导出渲染六方面齐备 | `result.json` + `examples/EXPECTED-OUTPUT.md` |
| 结果可核验性 | 5 | 每页 `evidence{...}`；`evidence_map.json` 反向映射；三道审计内嵌；**机制 × 阶段 × 字段对照表**（`SKILL.md` §3）指出每个字段由哪个机制产出 | `validate_result.py` / `evidence_audit.py` / `verify_deck.py` / `selftest.py` 退出码 0 |

## 2. 使用增益（25 分）

| 评分点 | 分 | 本包落点 | 判定 |
|-|-|-|-|
| 质量增益 | 15 | 机制差异（M1–M8）+ 两个臂的同尺子实测：讲稿覆盖率 0.0→1.0、定位覆盖率 0→1.0、问答 0→4、证据行 0→11、`result.json` 顶层键 0→20、有效预览 0→12 | `scripts/gain_ab.py` 复跑；数字见 `GAIN-PROTOCOL.md` §6 |
| 效率增益 | 5 | 达到冻结页数的运行轮数 **2 → 1**（A 臂首轮仅 3 页）；返工只需改 `talk_plan.json`/`talk_config.json` | `gain-run-record.json.arms.A.pages_before_rework = 3` |
| 增益可验证性 | 5 | 对照装置 + 指标定义 + 原始记录三件套随包；**不利结果一并公布**（A 臂在可见文本逐字可溯源率、数字可对源率上更好） | 复跑复现同一组结构性数字（`TEST.md` §3）；`GAIN-PROTOCOL.md` §7.1 |

## 3. 创新增益（15 分）★ 本版重点

| 评分点 | 分 | 本包落点 | 判定 |
|-|-|-|-|
| 新增能力 | 5 | ① 听众适配（10/18/30%）；② 页级规划 + 计划契约门；③ 问答预演；④ 对照装置与指标口径；⑤ **本版新增：机制显性化 + 可复用资产（题集骨架 / 页级金标准 / 复用步骤）** | `references/MECHANISM.md` 每节四段结构；`assets/case-set.json`、`assets/page-gold-standard.json` 可解析（`TEST.md` §1） |
| 方法改进 | 5 | ① 计划先行（M1）；② 逐字证据审计（M2）；③ 叙事配置化（M3）；④ 模板适配 + 自带页丢弃（M5）；⑤ 契约四形态与状态可见性（M6）；⑥ 运行时文本化资源（M7）；⑦ 确定性探针（M8） | `MECHANISM.md` 各节的"落点"列均可指到真实文件与字段 |
| 创新证据 | 5 | **每个机制都给出"可证伪判据"**（第三方能推翻它的检查）+ **连锁效应表**（去掉一环会怎样，含实测数字）；对照记录随包 | `MECHANISM.md` §1–§8 各节末行、§9 组合效应表；`gain-run-record.json` |

## 4. 可靠体验（10 分）

| 评分点 | 分 | 本包落点 | 判定 |
|-|-|-|-|
| 调用与易用性 | 3 | 触发词 + 自定位（`$SKILL_DIR`，cwd 任意）+ 一条命令全流程 + 三条复用主线的逐步命令 | `TEST.md` §2/§3 全部在包外 cwd 执行；`README.md` §二 |
| 运行稳定性 | 4 | 无网络；必需依赖仅 python-pptx + Pillow；**缺依赖不崩**（`TEST.md` §4）；材料异常/无模板/模板自带页各有分支；双跑确定性（M8） | `TEST.md` §4/§5；`self_check.determinism` |
| 异常处理 | 3 | 降级三处留痕（status/uncertainty/change_records）；退出码 0/1/2；**按"哪一环坏了"组织的降级表**（`SKILL.md` §6）；`references/failure-modes.md` 全表 | `TEST.md` §4；`failure-modes.md` |

## 5. 生态贡献（10 分）★ 本版重点

| 评分点 | 分 | 本包落点 | 判定 |
|-|-|-|-|
| 文档完整性 | 3 | `SKILL.md`（八机制 + 机制×阶段×字段 + 降级 + 清单）、`README.md`（**含三条复用主线的逐步命令**）、`TEST.md`、`COMPARE.md`、`references/` 十份规范（新增 MECHANISM / REUSE-KIT / GAIN-PROTOCOL）、`assets/` 两份新资产、`examples/` | 文件清单见 `README.md` 首段；`selftest.py --package-check` |
| 资源可复用性 | 4 | **题集**：`assets/case-set.json`（三种汇报输入骨架）；**金标准**：`assets/page-gold-standard.json`（块顺序 + 每页必填字段 + 机器判定命令）；**校验清单**：`SKILL.md` §7 + `references/quality-gates.md` + `templates/slide-checklist-template.md`；**导出预设**：`references/REUSE-KIT.md` §6（与代码默认值一致）；**配色与规范**：§7（色值/字体/命名，可直抄）；另有可独立 CLI 的脚本（含对照装置） | `REUSE-KIT.md` §1 总览表 + §5 三场景命令；`TEST.md` §3 显示对照装置可独立复跑 |
| 分享推广价值 | 3 | 沉淀"机制 → 没有它会怎样 → 可证伪判据"的写法、**增益对照方法论**（三层证据 + 四条度量硬要求 + 公布不利结果）、**资产复用路径**；`GITHUB_URL.txt` 公开链接 | `MECHANISM.md`、`COMPARE.md` §1/§3、`GAIN-PROTOCOL.md` §1/§3 |

## 6. GitHub 公开链接（+5）

`GITHUB_URL.txt` 第一行为作品所在目录链接（评审无需登录即可打开）。

## 7. 本版相对基线的实质增改（逐条）

| 类型 | 内容 |
|-|-|
| 新增文件 | `references/MECHANISM.md`（M1–M8：机制 / 落点 / 没有它会怎样 / 可证伪判据 + 连锁效应）、`references/REUSE-KIT.md`（资产总览 + 三个复用场景 + 导出预设 + 配色规范）、`assets/case-set.json`（题集骨架）、`assets/page-gold-standard.json`（页级金标准·结构版）、`scripts/gain_ab.py`、`references/GAIN-PROTOCOL.md`、`references/gain-run-record.json`（后三件与 v2 逐字节相同） |
| 重写文件 | `SKILL.md`（改为机制式结构：八机制 → 机制×阶段×字段 → 连锁效应 → 复用 → 按环降级）、`README.md`（新增三条复用主线的逐步命令）、`TEST.md`（新增资产可用性与"装置复跑 vs 随包记录对拍"） |
| 补充说明 | `references/OUTPUT_CONTRACT.md` 重写页首说明并新增 §7（机制 ↔ 字段对照）；**§1–§6 字段块逐字未动** |
| 未改动 | `scripts/` 既有 14 个脚本、`templates/`、`examples/`、`references/` 其余规范 —— 算法与 CLI 接口不变 |
