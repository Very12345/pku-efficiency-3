# RUBRIC_MAP.md — 五维评分逐条落点（可复现优先版）

> 官方五维：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**。
> 下表把每个**评分点**映射到本包里**能被复核的具体文件/机制/实测数字**。
> 数字出处：`references/DETERMINISM.md`、`references/FAULT-MATRIX.md`、`references/GAIN-PROTOCOL.md`、`TEST.md`。

## 1. 实际效果（40）

| 评分点 | 分 | 本包落点 | 复核方式 |
|-|-|-|-|
| 任务完成度 | 15 | 主链一条命令产出 四要素单页 + **可编辑分层 SVG** + PNG（+PDF）：`scripts/main.py` | `python "$SKILL_DIR/scripts/main.py" --case examples/case.json --out /tmp/o` → exit 0 |
| 结果正确性 | 15 | 逐元素 `data-src` 溯源；材料定位不到的数值不上画布；`audit.entity_coverage` / `encoding_consistency` / `four_element_coverage` | 读 `/tmp/o/audit.json`；`gain_harness.py` 复算覆盖率 |
| 结果完整性 | 5 | 契约字段全覆盖（信封 18 ∪ 案例契约 8）+ G1–G8 硬性门 | `check_contract.py --result … --case …` → exit 0 |
| 结果可核验性 | 5 | `provenance.source_files[].sha256`、`change_records`、全量 `audit`、`spec.json`、`render_log.json`；**外加逐产物 sha256 的复现报告** | `determinism.py` 报告的 `per_file_sha256`（三次运行的哈希列表） |

## 2. 使用增益（25）

| 评分点 | 分 | 本包落点 | 复核方式 |
|-|-|-|-|
| 质量增益 | 15 | 对照协议（A=加载 Skill / B=不加载 / B+=B 最有利设置）与指标口径：[`GAIN-PROTOCOL.md`](GAIN-PROTOCOL.md) | 同协议重跑 |
| 效率增益 | 5 | 达标返工步数 0（B 条件未达标：无 audit/render_log/spec、无 `data-src`、无分层）；**如实记录 A 单次更慢** | [`GAIN-PROTOCOL.md`](GAIN-PROTOCOL.md) §4.3 |
| 增益可验证性 | 5 | 只读测量器 `scripts/gain_harness.py` 对**任意**输出目录复算同一组指标（分层 7、真文字 61、溯源 0.903、四要素 4/4、契约 8/8） | `gain_harness.py --out <out> --case <case>` → exit 0 |

## 3. 创新增益（15）

| 评分点 | 分 | 本包落点 | 复核方式 |
|-|-|-|-|
| 新增能力 | 5 | **可复现性做成可执行判据**：`scripts/determinism.py` 的 L0/L1/L2 三级 + 跨进程/跨 cwd/跨哈希种子；外加方案先行、双 lint 门、契约回显 | `determinism.py --runs 5` → exit 0；报告 `per_file`/`volatile_fields` |
| 方法改进 | 5 | 易变字段**先归类再比较**（V1–V4 逐条给"为什么允许它变 + 怎么稳定化"），而不是笼统声称"输出稳定" | [`DETERMINISM.md`](DETERMINISM.md) §5 |
| 创新证据 | 5 | **阴性对照**：注入随机字段后判据立刻从 `canonical-stable` 变 `unstable`、exit 1、抓到 5 个文件 + 1 条字段级差异 | [`DETERMINISM.md`](DETERMINISM.md) §6 与 `TEST.md` §3 |

## 4. 可靠体验（10）

| 评分点 | 分 | 本包落点 | 复核方式 |
|-|-|-|-|
| 调用与易用性 | 3 | `SKILL.md` §1 三条命令即可跑通；脚本自定位（cwd 任意）；每个入口的 `--flag` 与退出码逐条列出 | 复制到包外直接跑 |
| 运行稳定性 | 4 | **同一输入 5 次运行 8/8 产物掩码后一致、0 处未解释差异**；`spec_sha16` 五次相同 | `determinism.py --runs 5` |
| 异常处理 | 3 | 四形态 23 条注入实测（`ok 23 / silent 0`）；20 条决策规则 D1–D20；退出码 0/1/2 语义稳定；非法契约与 PDF 缺席原因两处已修为"必须留痕" | `fault_inject.py --fail-on strict` → exit 0 |

## 5. 生态贡献（10）

| 评分点 | 分 | 本包落点 | 复核方式 |
|-|-|-|-|
| 文档完整性 | 3 | 13 份 reference（契约/五维/失败模式/注入矩阵/确定性/增益协议/机制/复用/方案 schema/四要素/图层/模板）+ SKILL/README/TEST | 目录清单见 `SKILL.md` §5 |
| 资源可复用性 | 4 | 资产三件套、SVG 图层命名契约、方案 schema、契约 + G1–G8、只读测量器、注入器、**复现判据脚本（可搬到任何以 `main.py --case/--out` 为入口的出图 Skill）** | [`REUSE-KIT.md`](REUSE-KIT.md) §1–§3 |
| 分享推广价值 | 3 | `GITHUB_URL.txt`；可分享的"易变字段清单 + 稳定化配方"（任何出图流水线都能照搬这套口径）；示例报告随包（`examples/determinism_report.example.json`） | 打开 `GITHUB_URL.txt` |

## 6. 自评（如实）

| 维度 | 强度 | 依据 | 短板 |
|-|-|-|-|
| 实际效果 | 强 | 三件套产物齐全 + 契约门 + 结构审计 | 图面美观度不由结构判据保证 |
| 使用增益 | 中强 | 对照协议 + 只读测量器 | 对照只做了本机一轮 A/B/B+，未跨机器复测 |
| 创新增益 | 强 | 判据可执行 + 可证伪 + 易变字段分类 | 不是新绘图算法，而是可验证性方向的创新 |
| 可靠体验 | 强 | 复现 5 次 + 注入 23 条 | 跨机器一致性明确不承诺 |
| 生态贡献 | 强 | 13 份 reference + 可移植判据 | 未提供第三方真实案例的复用记录 |
