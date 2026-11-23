# RUBRIC_MAP.md — 五维评分逐条落点（契约优先版）

> 官方五维：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**。
> 每行给出本包里**可复核的具体文件/机制/实测数字**；数字出处：
> [`CONTRACT-MATRIX.md`](CONTRACT-MATRIX.md)、[`FAULT-MATRIX.md`](FAULT-MATRIX.md)、
> [`GAIN-PROTOCOL.md`](GAIN-PROTOCOL.md)、[`../TEST.md`](../TEST.md)。

## 1. 实际效果（40）

| 评分点 | 分 | 落点 | 复核方式 |
|-|-|-|-|
| 任务完成度 | 15 | `scripts/main.py` 一条命令产出 四要素单页 + 可编辑分层 SVG + PNG/PDF | `main.py --case examples/case.json --out /tmp/o` → exit 0 |
| 结果正确性 | 15 | 逐元素 `data-src`；缺值不上画布；`audit.entity_coverage` / `encoding_consistency` / `four_element_coverage` | 读 `/tmp/o/audit.json` |
| 结果完整性 | 5 | 契约回显四形态全覆盖：**26 行注入 / 26 ok**、顶层 null 0 行、契约字段 null 0 行 | `contract_matrix.py --fail-on strict` → exit 0 |
| 结果可核验性 | 5 | `provenance.source_files[].sha256` + `sources[]` + `change_records` + 全量 `audit` + **逐行契约矩阵报告** | `examples/contract_matrix.example.json`；`check_contract.py` |

## 2. 使用增益（25）

| 评分点 | 分 | 落点 | 复核方式 |
|-|-|-|-|
| 质量增益 | 15 | 对照协议与指标口径（A=加载 Skill / B=不加载 / B+=B 最有利） | [`GAIN-PROTOCOL.md`](GAIN-PROTOCOL.md) |
| 效率增益 | 5 | 达标返工步数 0（B 条件无 audit/render_log/spec、无 `data-src`、无分层）；A 单次更慢这一事实照实记录 | [`GAIN-PROTOCOL.md`](GAIN-PROTOCOL.md) §4.3 |
| 增益可验证性 | 5 | 只读测量器 `scripts/gain_harness.py`：分层 7、真文字 61、溯源 0.903、四要素 4/4、**契约 8/8 verdict=complete** | `gain_harness.py --out <out> --case <case>` → exit 0 |

## 3. 创新增益（15）

| 评分点 | 分 | 落点 | 复核方式 |
|-|-|-|-|
| 新增能力 | 5 | **把 `output_contract` 当接口来测**：六种容器形态 × 九类边界值 + 非法容器 + 保留键冲突的**可执行矩阵**（26 行，每行真实出图） | `contract_matrix.py --out /tmp/cm` |
| 方法改进 | 5 | 判级引入**"静默通过"**这个可操作定义（期望未满足 ∧ status=success ∧ 无任何记录），把"文档承诺 vs 实现"变成可判定；两类 null 作用域分开算 | [`CONTRACT-MATRIX.md`](CONTRACT-MATRIX.md) §2 |
| 创新证据 | 5 | 矩阵发现 **3 条静默通过**（C19/C21/C22）→ 纯增量 `extract.py` +7 净行修复 → 复测 **0 条**；另有 3 条不构成违规但记录在案的观察 | [`CONTRACT-MATRIX.md`](CONTRACT-MATRIX.md) §4–§5 |

## 4. 可靠体验（10）

| 评分点 | 分 | 落点 | 复核方式 |
|-|-|-|-|
| 调用与易用性 | 3 | `SKILL.md` §1 两条命令跑通；`--flag` 与退出码逐条列出；脚本自定位（cwd 任意） | 复制到包外直接跑 |
| 运行稳定性 | 4 | 契约矩阵 26 行全部 exit 0、`check_contract` 失败 0；四形态注入 23 条 0 静默（回归） | `contract_matrix.py --fail-on strict` + `fault_inject.py --fail-on strict` |
| 异常处理 | 3 | 非法形态不崩且**必须留痕**（D14–D17）；`null` 归一化 + 记录；保留键冲突进 echo；退出码 0/1/2 语义稳定 | 矩阵 C16/C19–C24 行 + `failure-modes.md` §3 |

## 5. 生态贡献（10）

| 评分点 | 分 | 落点 | 复核方式 |
|-|-|-|-|
| 文档完整性 | 3 | 13 份 reference（含**契约矩阵**）+ SKILL/README/TEST + 示例报告 | 目录清单见 `SKILL.md` §6 |
| 资源可复用性 | 4 | 契约 schema + G1–G8 + 资产三件套 + 方案 schema + **契约矩阵脚本可直接搬到任何有 `output_contract` 的 Skill 上** | [`REUSE-KIT.md`](REUSE-KIT.md) §1–§3 |
| 分享推广价值 | 3 | `GITHUB_URL.txt`；可分享的"契约回显规则 + 边界值清单 + 静默通过判据"；随包 `examples/contract_matrix.example.json` | 打开 `GITHUB_URL.txt` |

## 6. 自评（如实）

| 维度 | 强度 | 依据 | 短板 |
|-|-|-|-|
| 实际效果 | 强 | 产物三件套 + 契约 26 行全绿 | 契约矩阵不校验字段语义（画布是否真按 dpi 出图由 audit 覆盖） |
| 使用增益 | 中强 | 对照协议 + 只读测量器 | 对照未跨机器复测 |
| 创新增益 | 强 | "静默通过"判据 + 26 行注入 + 3→0 的修复闭环 | 覆盖的是接口形态，不是新绘图算法 |
| 可靠体验 | 强 | 26 行契约 + 23 条注入，双 0 静默 | 跨字段一致性未覆盖 |
| 生态贡献 | 强 | 矩阵脚本可移植、报告可分享 | 未提供第三方案例复用记录 |
