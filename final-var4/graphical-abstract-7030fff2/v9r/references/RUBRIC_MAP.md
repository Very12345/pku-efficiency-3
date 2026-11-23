# RUBRIC_MAP.md — 五维评分逐条落点（降级链优先版）

> 官方五维：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**。
> 每行给出本包里**可复核的具体文件/机制/实测数字**；数字出处：
> [`DEGRADE-MATRIX.md`](DEGRADE-MATRIX.md)、[`FAULT-MATRIX.md`](FAULT-MATRIX.md)、
> [`GAIN-PROTOCOL.md`](GAIN-PROTOCOL.md)、[`../TEST.md`](../TEST.md)。

## 1. 实际效果（40）

| 评分点 | 分 | 落点 | 复核方式 |
|-|-|-|-|
| 任务完成度 | 15 | `scripts/main.py` 产出 四要素单页 + 可编辑分层 SVG + PNG（+PDF）；**缺绘图库时仍然产出可编辑源文件**（P09 实测） | `main.py --case examples/case.json --out /tmp/o` → exit 0 |
| 结果正确性 | 15 | 逐元素 `data-src`；缺值不上画布；`audit.entity_coverage` / `encoding_consistency` / `four_element_coverage` | 读 `/tmp/o/audit.json` |
| 结果完整性 | 5 | 契约字段全覆盖 + G1–G8；**降级时 `status=partial` 且限制逐条列在 `uncertainty`/`warnings`/`reason`** | `check_contract.py` → exit 0；`degrade_probe.py` P02–P09 |
| 结果可核验性 | 5 | `provenance.source_files[].sha256` + `audit` + `render_log.backend`/`font` + **逐场景降级矩阵报告** | `examples/degrade_matrix.example.json` |

## 2. 使用增益（25）

| 评分点 | 分 | 落点 | 复核方式 |
|-|-|-|-|
| 质量增益 | 15 | 对照协议与指标口径（A=加载 Skill / B=不加载 / B+=B 最有利） | [`GAIN-PROTOCOL.md`](GAIN-PROTOCOL.md) |
| 效率增益 | 5 | 达标返工步数 0；**缺库时不必重画**：三级后端自动回退，`status` 与原因自动留痕 | [`GAIN-PROTOCOL.md`](GAIN-PROTOCOL.md) §4.3 |
| 增益可验证性 | 5 | 只读测量器 `gain_harness.py`（分层 7 / 真文字 61 / 溯源 0.903 / 四要素 4/4 / 契约 8/8）**与依赖无关**：换成纯 Python 后端仍可复算 | `gain_harness.py --out <out> --case <case>` |

## 3. 创新增益（15）

| 评分点 | 分 | 落点 | 复核方式 |
|-|-|-|-|
| 新增能力 | 5 | **受控导入拦截 + 12 场景降级矩阵**：每场景一个只含待拦模块的 shim 目录（写命中日志后 `raise ImportError`）、PATH 假 CLI | `degrade_probe.py --out /tmp/dg` |
| 方法改进 | 5 | 把"可选依赖"拆成**两条独立证据**：静态导入点（`import_sites.pipeline`）与运行时命中（`shim_hits`）——于是能区分"根本没这条边"（pptx/yaml/LibreOffice）与**传递依赖**（`numpy 0 导入点` 但会拖垮 matplotlib） | [`DEGRADE-MATRIX.md`](DEGRADE-MATRIX.md) §6 |
| 创新证据 | 5 | 12 场景实测 **0 crash、12/12 仍写 `result.json`、退出码全 0**；发现 1 处"不可见降级"（PDF `reason=null`）并纯增量修好；给出**由实测得出的最小可用环境清单** | [`DEGRADE-MATRIX.md`](DEGRADE-MATRIX.md) §4–§5 |

## 4. 可靠体验（10）

| 评分点 | 分 | 落点 | 复核方式 |
|-|-|-|-|
| 调用与易用性 | 3 | `SKILL.md` §1 三条命令跑通；`--flag` 与退出码逐条列出；脚本自定位（cwd 任意） | 复制到包外直接跑 |
| 运行稳定性 | 4 | 12 个降级场景退出码全 0、12/12 写出 `result.json`；四形态注入 23 条 0 静默（回归） | `degrade_probe.py --fail-on strict` + `fault_inject.py --fail-on strict` |
| 异常处理 | 3 | 三级渲染回退 + PDF `present:false` + **reason**；PDF 材料文本层缺失如实登记；20 条决策规则 D1–D20 | 矩阵 P02–P09；`failure-modes.md` §3 |

## 5. 生态贡献（10）

| 评分点 | 分 | 落点 | 复核方式 |
|-|-|-|-|
| 文档完整性 | 3 | 13 份 reference（含**依赖地图与降级矩阵**）+ SKILL/README/TEST + 示例报告 | 目录清单见 `SKILL.md` §6 |
| 资源可复用性 | 4 | 依赖地图 / 最小可用环境清单 / 资产三件套 / 契约与硬性门 / **降级探测脚本可搬到任何 Python Skill 上** | [`REUSE-KIT.md`](REUSE-KIT.md) §1–§3 |
| 分享推广价值 | 3 | `GITHUB_URL.txt`；可分享的"哪些依赖是真的、缺了会掉成什么样"的实测口径；随包 `examples/degrade_matrix.example.json` | 打开 `GITHUB_URL.txt` |

## 6. 自评（如实）

| 维度 | 强度 | 依据 | 短板 |
|-|-|-|-|
| 实际效果 | 强 | 12 场景全部产出 SVG+PNG+result.json | 纯 Python 后端下文字为占位框（已声明） |
| 使用增益 | 中强 | 对照协议 + 与依赖无关的测量器 | 对照未跨机器复测 |
| 创新增益 | 强 | 拦截式降级矩阵 + 静态/运行时双证据 + 1 处修复 | 只模拟 ImportError，版本不兼容未测 |
| 可靠体验 | 强 | 12 场景 0 crash + 23 条注入 0 静默 | 字体缺失无法完整模拟 |
| 生态贡献 | 强 | 依赖地图与最小环境清单可被任何 Skill 复用 | 未提供第三方 Skill 的实测复用记录 |
