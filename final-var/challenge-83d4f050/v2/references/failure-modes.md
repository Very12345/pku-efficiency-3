# failure-modes.md — 失败模式与其"可测足迹"（F01–F22）

> 本版把每条失败模式都绑到**一个可测量的后果**上：失败不是"感觉出错了"，而是
> `gain_probe.py` 的某个指标掉下来、某条审计命令非零退出、或 `status` 与退出码不一致。
> 这样"降级是否被正确处理"也能被第三方复核（判据见 `references/GAIN-PROTOCOL.md` §2）。
> 决策规则编号对应 `SKILL.md` §3 的 P1–P10。

## 1. 材料异常（F01–F06）

| # | 失败模式 | 触发信号 | 处置 | 可测足迹 | P |
|---|---|---|---|---|---|
| F01 | 材料缺失/目录为空 | CP1.3 fail | 三级查找（case 路径 → `--materials-dir` → 同目录文件）；仍无 → `failed` | exit **3**；产物只有 `result.json`；A5 低、A1–A7 为 0 | P1 |
| F02 | PDF/扫描件不可结构化 | 抽取器报 `manual-required` | 抽文本另存 `.md`，或手工建规格（`extraction.method=manual`） | 实测 exit **3**、`reason=manual-required`、`files=["result.json"]` | P1/P2 |
| F03 | 缺方向信息 | 边无法定向 | 只画结合类无向语义边 + `uncertain=true` | A3 仍为 1.0（有 `data-type`），但 `uncertainty` 出现该边 id | P6 |
| F04 | 同名基因/蛋白歧义 | 拓扑 P04 | 拆两个实体并写 `note`；无法区分则合并 + `uncertain` | `topology.json` 的 P04 条目状态变化 | — |
| F05 | 数值矛盾 | 人工核验 | 以材料原文为准，双处标注 | `uncertainty` 与 `change_records` 同时出现同一数值 | — |
| F06 | 只有实体无关系 | `counts.edges == 0` | 照画并 `partial`；实体也为空则 `failed` | exit **2**（有实体）或 **3**（全空） | P7 |

## 2. 资产缺失（F07–F09）

| # | 失败模式 | 触发信号 | 处置 | 可测足迹 | P |
|---|---|---|---|---|---|
| F07 | `palettes.json` 缺失 | 读资产异常 | 回退内置默认调色板；图例语义不因此改变 | A4 应保持 1.0000（图例仍声明全部在用箭头） | — |
| F08 | `mechanism-spec.schema.json` 缺失 | `S01` warn | 用内置默认 schema，不阻断 | `self_check.warnings` 非空但 exit 仍为 0/2 | P2 |
| F09 | 核对清单模板缺失 | 模板不存在 | 用 `SKILL.md` 的交付自查清单代替 | `change_records` 出现"模板回退"条目 | — |

## 3. 依赖缺失（F10–F12）

| # | 失败模式 | 触发信号 | 处置 | 可测足迹 | P |
|---|---|---|---|---|---|
| F10 | matplotlib 不可用 | import 抛异常 | 只交付 SVG；`partial`；`previews/exports=[]` | exit **2**；**A7 = 0.0000**；`gates.g5_png=false`；SVG sha16 与全量运行相同 | P8 |
| F11 | Pillow 缺失 | 尺寸校验无法执行 | PNG 照常写出，尺寸校验降为 warn | `self_check.warnings` 非空 | P8 |
| F12 | 中文字体缺失 | 渲染告警 | SVG 用字体栈不受影响；PNG 记录 `font` | `export_checks` 出现 font 告警项 | P8 |
| F12b | 显式只请求 SVG | `--formats svg` | 不算失败：`partial` + 空数组 + 说明 | 实测 exit **2**、A7 = 0.5000、SVG 与全量运行**逐字节相同** | P10 |

## 4. 契约四形态（F13–F16）与状态一致性（F17–F20）

| # | 失败模式 | 触发信号 | 处置 | 可测足迹 | P |
|---|---|---|---|---|---|
| F13 | 标量字段无值 | 声明值为 `str` | 填 `""` | A5 应回到 19/19；`null` 数必须为 0 | P5 |
| F14 | 列表字段无值 | 声明值为 `list` | 填 `[]` | 同上 | P5 |
| F15 | 布尔字段无值 | 声明值为 `bool` | 填 `false` | 同上 | P5 |
| F16 | 数值/字典字段无值 | 声明值为 `number`/`dict` | 填 `0` / `{}` | 同上 | P5 |
| F17 | schema 门不过 | `S01` fail | 阻断渲染，改正后重跑 | 实测 exit **3**、只写 `result.json`、顶层仅 **14 键**（信封 13/19） | P2 |
| F18 | 契约回显不全 | `check_contract.py` 非 0 | 按缺项补齐（四形态） | 实测对 failed 结果 exit **1**（`checks=7`） | P5 |
| F19 | failed 信封缺 6 项 | 缺 `title/skill/data_mapping/extraction/export_checks/provenance` | 若需交付则补写为空值形态 | A5 从 13/19 → 19/19（补写后复测） | P5 |
| F20 | 三元组不一致 | `status`/退出码/`gates` 互相矛盾 | 以退出码为真，取保守档 | exit 与 `status` 必须成对：0↔success、2↔partial、3↔failed | P9 |

## 5. 渲染与可读性（F21–F22）

| # | 失败模式 | 触发信号 | 处置 | 可测足迹 | P |
|---|---|---|---|---|---|
| F21 | 图面元素过多不可读 | 布局溢出/字号到下限 | 收缩节点或拆子图 | `layout.warnings` 非空；结构指标不变 | — |
| F22 | 目标导出格式不支持 | `F01_xxx` fail | 至少 SVG + PNG；其余如实说明 | 实测 `--formats png` → exit **2**、`partial`、PNG 203655 字节、A7 = 0.5000 | P10 |

## 6. 与增益协议的关系

- **可测足迹列**是本版新增的：它把"降级做对了吗"变成可复核的读数，
  用同一套指标（A1–A8）在降级前后各量一次即可。
- 反预制答案与反编造规则不变：正式案例必须现场读材料；
  `examples/` 与 `scripts/baseline_emulator.py` 的产物都**不得**冒充正式输出或平台对照结果。
