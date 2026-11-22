# RUBRIC_MAP.md — 五维评分逐条映射（v2 增益可验证版）

原题满分 100：**实际效果 40 / 使用增益 25 / 创新增益 15 / 可靠体验 10 / 生态贡献 10**，
另加 GitHub 公开作品链接附加分 5。本版的重心是**使用增益 25 分**：把"增益"从形容词
变成可复跑的对照装置、明确的指标定义与原始实测记录（含**不利于本包**的结果）。
实测命令与观测见 [TEST.md](TEST.md)，对照协议见 [references/GAIN-PROTOCOL.md](references/GAIN-PROTOCOL.md)。

## 1. 实际效果（40 分）

| 评分点 | 分 | 本包落点 | 判定/复算 |
|-|-|-|-|
| 任务完成度 | 15 | `scripts/main.py` 一条命令闭环（材料实读 → 计划 → 计划门 → deck → 预览 → 审计 → 契约收口）；页数按时长推导并**校准到冻结页数** | 退出码 0；`plan_gates.gates[P3] pages=12 target=12`；`TEST.md` §1 |
| 结果正确性 | 15 | 页内容逐字取自源材料；`evidence_audit.py` 逐页逐字核验 + 行号区间 + 数字对源；强度按词法门分级 | `audit.evidence.summary{content_pages:10, ok_pages:10, errors:0}`（`TEST.md` §4） |
| 结果完整性 | 5 | `main_line` / `pages` / `figure_ref` / `one_liner`+`notes` / `deck_mode` / `previews` 六方面齐备 | `result.json` 直接可查；`examples/EXPECTED-OUTPUT.md` 列清单 |
| 结果可核验性 | 5 | 每页 `evidence{source_file,section,line_no,locator,quote,strength}`；`evidence_map.json` 反向映射；三道审计内嵌 `result.audit`；**证据链七环（E1–E7）写进 SKILL.md 并逐环给复算命令** | `validate_result.py` / `evidence_audit.py` / `verify_deck.py` / `selftest.py` 退出码 0 |

## 2. 使用增益（25 分）★ 本版重点

| 评分点 | 分 | 本包落点 | 判定/复算 |
|-|-|-|-|
| 质量增益 | 15 | 可判定的机制差异（`COMPARE.md` §2 的 11 行对照表）+ **两个臂的同尺子实测**：讲稿覆盖率 0.0→1.0、来源定位覆盖率 0→1.0、问答条目 0→4、证据行 0→11、`result.json` 顶层键 0→20、有效 PNG 预览 0→12 | `python "$SKILL_DIR/scripts/gain_ab.py" --case examples/case.json --work RUN/gain`；数字见 `GAIN-PROTOCOL.md` §6 |
| 效率增益 | 5 | 一条命令完成全流程（E 组 E2）：**达到冻结页数的运行轮数 2 → 1**（A 臂首轮只排 3 页，需 1 轮返工）；返工定位成本可只改 `talk_plan.json`/`talk_config.json` 重跑 | 同上；`gain_run_record.json.arms.A.pages_before_rework = 3` |
| 增益可验证性 | 5 | **对照装置可复跑**：`scripts/gain_ab.py` 不 import 本包模块、只读产物、缺项记 0/null；**指标定义写死在 `GAIN-PROTOCOL.md` §4**（D/C/E 三组，逐个给计算式）；**原始记录随包**（`references/gain-run-record.json`，装置直出未编辑）；**不利结果一并公布**（A 臂在 D6/D7 上更优） | 复跑两次 D 组指标逐项相等（`TEST.md` §2）；不利结果见 `GAIN-PROTOCOL.md` §7.1 |
| 不越界宣称 | （纪律） | 明写"不是平台白板、不是真实基础 Agent、不是质量提升百分比"，未测项逐条列出（GAIN-PROTOCOL.md §7.3） | 读 §7.3；`COMPARE.md` §4 |

## 3. 创新增益（15 分）

| 评分点 | 分 | 本包落点 | 判定/复算 |
|-|-|-|-|
| 新增能力 | 5 | ① 听众适配（10/18/30% 背景比例）；② 页级规划 + 计划契约门 P1–P8；③ 问答预演（局限/风险 + strong 结果各一条追问）；④ **本版新增：可复跑的 A/B 对照装置 + 指标口径** | `plan_gates.json`；`pages[].qa`；`gain_ab.py` 运行输出 |
| 方法改进 | 5 | ① 叙事模板化；② 逐字证据审计；③ deck 机器校验（打开/页数/备注/命名/OPC/规范化 sha）；④ 运行时资源生成（二进制不随包）；⑤ 产物路径净化；⑥ **证据链七环化**（每环一条复算命令） | `evidence_audit.json` / `deck_audit.json` / `preview_manifest.json`；包内无盘符路径 |
| 创新证据 | 5 | 对照装置 + 指标定义 + 原始记录三者可独立核对；**把"不利结果"写进包里**（这在同类作品中很罕见，也是可验证性的直接证据）；确定性探针落盘 | `gain-run-record.json` 与 `GAIN-PROTOCOL.md` §6 数字逐项对得上 |

## 4. 可靠体验（10 分）

| 评分点 | 分 | 本包落点 | 判定/复算 |
|-|-|-|-|
| 调用与易用性 | 3 | frontmatter 触发词 + 自定位（`$SKILL_DIR`，cwd 任意）+ 一条命令全流程；`gain_ab.py --help` 独立可用 | `TEST.md` §1/§2/§3 全部在包外 cwd 执行 |
| 运行稳定性 | 4 | 无网络；必需依赖仅 python-pptx + Pillow；**缺依赖不崩**（命令仍返回 0，`TEST.md` §3-T3）；材料缺失/空材料/无模板/模板自带页各有分支；重复运行确定性 | `TEST.md` §3；`self_check.determinism` |
| 异常处理 | 3 | "三处记录"纪律：`status` 降级 + `uncertainty{item,impact,mitigation}` + `change_records{at,step,action}`；退出码 0/1/2 语义明确；`references/failure-modes.md` 全表 | `TEST.md` §3 两条降级用例；`failure-modes.md` |

## 5. 生态贡献（10 分）

| 评分点 | 分 | 本包落点 | 判定/复算 |
|-|-|-|-|
| 文档完整性 | 3 | `SKILL.md`（证据链七环 + 增益怎么被证明 + 降级纪律）、`README.md`（快速开始 + `gain_ab.py` 是什么/不是什么）、`TEST.md`、`COMPARE.md`（方法论三层证据）、`references/` 八份规范（**新增 GAIN-PROTOCOL.md**）、`examples/` | 文件清单见 `README.md`；`selftest.py --package-check` |
| 资源可复用性 | 4 | **`scripts/gain_ab.py` 可脱离本包复用**：换 `--case` 即可对任何"读材料 → 产出 deck/result.json"的同类 Skill 做同一把尺子的对照（A 臂模拟器可替换为对方的基线）；指标定义文档化、可裁剪；另有 `templates/talk_config.json`、`assets/plan.schema.json` 可编辑 | `gain_ab.py --help`；`GAIN-PROTOCOL.md` §5 复跑步骤 |
| 分享推广价值 | 3 | 沉淀"**增益怎么证**"的可复制方法论：三层证据（机制/口径/实测）+ 四条度量硬要求 + 不利结果公布惯例；`GITHUB_URL.txt` 公开链接 | `COMPARE.md` §1/§3；`GAIN-PROTOCOL.md` §1/§3 |

## 6. GitHub 公开链接（+5）

`GITHUB_URL.txt` 第一行为作品所在目录链接（评审无需登录即可打开）。

## 7. 本版相对基线的实质增改（逐条）

| 类型 | 内容 |
|-|-|
| 新增文件 | `references/GAIN-PROTOCOL.md`（协议 + D/C/E 指标定义 + 实测表 + 不利结果 + 待改进项）、`scripts/gain_ab.py`（A/B 对照装置，不 import 本包模块）、`references/gain-run-record.json`（装置直出的原始记录） |
| 重写文件 | `SKILL.md`（改为证据链结构 E1–E7 + 增益证明 + 降级纪律）、`COMPARE.md`（改为方法论三层证据 + 不利事实汇总）、`README.md`、`TEST.md`（新增对照装置两次复跑与两条降级用例） |
| 补充说明 | `references/OUTPUT_CONTRACT.md` 重写页首说明并新增 §7（指标 ↔ 字段对照）；**§1–§6 字段块逐字未动** |
| 未改动 | `scripts/` 既有 14 个脚本、`templates/`、`assets/`、`examples/`、`references/` 其余规范 —— 算法与 CLI 接口不变 |
