# failure-modes.md — 失败模式处置表（F01–F22）

> 本表与 `SKILL.md` **§1 决策规则 D1–D23** 和 **§2 失败分支总表**一一对应：
> 每个 F 编号在 SKILL.md §2 里有同一编号的行，并指明它由哪条 D 规则管辖。
> 表中"实测"列来自 2026-11-22 在**临时目录副本**上真跑的记录（命令与输出见 `TEST.md` §5–§9），
> 不是设计意图的复述。
>
> 使用方式：**发现异常 → 找到 F 编号 → 按"处置"做 → 把结果写进"记录位点"。**
> 记录位点没有内容 = 这次运行不可核验 = 交付缺陷（哪怕图本身画对了）。

## 1. 材料异常（F01–F06）

| # | 失败模式 | 触发信号（怎么发现） | 处置 | 记录位点 | D 规则 |
|---|---|---|---|---|---|
| F01 | 材料缺失 / 目录为空 | CP1.3 `fail`；`SUMMARY ... "reason": "CP1 fail"` | 按 D7 三级查找（case 相对路径 → `--materials-dir` → case 同目录）；都没有 → `status=failed` + 补救路径 | `status` / `reason` / `uncertainty` | D7 |
| F02 | 材料是 PDF / 扫描件，抽不出结构化文本 | 抽取器返回 `manual-required`；实测 `SUMMARY {"status": "failed", "reason": "manual-required"}`，exit **3** | 先抽文本另存为 `.md`；仍不可结构化 → CP2b 手工建 `model.json`，`extraction.method=manual` | `extraction.method` / `change_records` | D5 |
| F03 | 材料没写上下游方向 | 边无法定向；人工核验 CP3 发现 | 只画结合类无向语义边，`uncertain=true`，布局不给方向暗示 | `uncertainty` / 边的 `uncertain` | D1 |
| F04 | 同名基因与蛋白歧义 | 拓扑审计 P04 | 拆两个实体（gene 斜体 / protein 正体）并写 `note`；无法区分则合并 + `uncertain` | `note` / `uncertainty` | D2 |
| F05 | 材料数值自相矛盾 | 人工核验 CP3 | 以材料原文为准，图与结果**两处**都标矛盾点 | `uncertainty` + `change_records` | D4 |
| F06 | 只有实体没有关系 / 材料全空 | `scientific_content.counts.edges == 0` 或 entities 也为 0 | 有实体：照画并 `status=partial` 说明"边清单为空"；全空：`failed`，**不画空图** | `status` / `counts` | D6 |

## 2. 资产缺失（F07–F09）

| # | 失败模式 | 触发信号 | 处置 | 记录位点 | D 规则 |
|---|---|---|---|---|---|
| F07 | `assets/palettes.json` 缺失或损坏 | 读资产异常 / JSON 解析失败 | 回退 `scripts/model.py` 内置默认调色板继续跑；**不得**因此改变图例语义 | `uncertainty` | D18 |
| F08 | `assets/mechanism-spec.schema.json` 缺失 | 检查 `S01` 记 `warn` | 用内置默认 schema 继续（**不阻断**），但在自检里留下 warn | `self_check.warnings` | D18 |
| F09 | `templates/relation-checklist-template.md` 缺失 | 模板路径不存在 | 用 `SKILL.md` §7 自查清单代替核验载体，仍要逐条留痕 | `change_records` | D18 |

## 3. 依赖缺失（F10–F12）

| # | 失败模式 | 触发信号 | 处置 | 记录位点 | D 规则 |
|---|---|---|---|---|---|
| F10 | matplotlib 不可用 | `import matplotlib` 抛异常 | 只交付可编辑 SVG：`status=partial`、exit **2**、`gates.g5_png.pass=false`（实测 7/8 门过）、`previews/exports` 保持 `[]` | `deliverables` / `export_checks` / `uncertainty` | D16 |
| F11 | Pillow 缺失 | 尺寸校验无法执行 | PNG 仍由 matplotlib 写出；尺寸校验降级为 warn | `self_check.warnings` | D16 |
| F12 | 系统中文字体缺失 | 渲染期字体探测告警 | SVG 用 CSS 字体栈（不受影响）；PNG 记录 `font` 与告警，**不静默输出乱码** | `export_checks` / `uncertainty` | D17 |
| F12b | 运行者显式只要 SVG（`--formats svg`） | 命令行显式指定 | 不算失败：`partial` + exit 2，SVG 与全量运行**逐字节相同**（实测 sha16 `27f344a0dfb2e90f`） | `uncertainty` / 空 `previews` | D16 |

## 4. 契约四形态（F13–F16）

判定顺序：先看 `case.json` 的 `output_contract` 里**声明值的 JSON 形态**，再决定空值怎么写。

| # | 形态 | 声明示例 | 无真实值时的填空 | 机器判定 | D 规则 |
|---|---|---|---|---|---|
| F13 | ① 字段 → 标量 | `"custom_demo_field": "示例文本"` | `""` | `check_contract.py` C05 | D19 / D20 |
| F14 | ② 字段 → 容器 | `"custom_list_field": ["示例"]` | `[]` | 同上 | D19 / D20 |
| F15 | ③ 布尔开关 | `"colorblind_safe": true` | `false` | 同上 | D19 / D20 |
| F16 | ④ 数值 / 字典 | `"resolution_dpi": 150` | `0` / `{}` | 同上 | D19 / D20 |

统一铁律：**顶层不得出现 `null`**（实测 C04 会直接判 fail）。
声明值本身是 `null` 时按形态 ① 处理（填 `""`），并在 `uncertainty` 说明判据。

## 5. 状态一致性（F17–F20）

| # | 失败模式 | 触发信号 | 处置 | 记录位点 | D 规则 |
|---|---|---|---|---|---|
| F17 | 机制规格没过 schema 门 | CP2 `S01` fail；实测 `SUMMARY ... "reason": "机制规格未通过 schema 门"`，exit **3**，输出目录**只有 `result.json`** | 阻断渲染；按违规清单修正规格后重跑；修正过程写进 `change_records` | `status` / `reason` / `change_records` | D21 |
| F18 | 契约回显不完整 | `check_contract.py` 非 0；实测对 failed 结果返回 `contract\|fail\|...\|checks=7`，exit **1** | 按报出的缺项补齐（填空规则见第 4 节）；同一缺项两次修不好就停止重跑并如实记录 | `result.json` / `uncertainty` | D20 |
| F19 | failed 路径信封不全 | 实测 schema 门失败时 `result.json` 只有 **14 个顶层键**，缺 `title / skill / data_mapping / extraction / export_checks / provenance` **6 项**（信封 13/19） | 若平台要求 failed 运行也必须带全契约：把这 6 项按 D19 空值形态补写后再自查；**不得**把 failed 报成 success | `result.json` | D21 |
| F20 | `status` / `gates` / 退出码互相矛盾 | 三者不一致（例如 status=success 但 exit 2） | 以**退出码为真**重算三元组；取更保守的档位（success→partial→failed），并写明取值理由 | `uncertainty` | D22 |

**状态一致性速查（实测口径）**

| 情形 | status | exit | gates | 说明 |
|---|---|---|---|---|
| 已核验规格 + 预览齐全 | `success` | 0 | 8/8 | 唯一允许 success 的组合 |
| 自动草稿未核验 / 缺预览 / 只要 SVG | `partial` | 2 | 7/8 或 8/8 | 必须列明 warn/fail |
| schema 门不过 / 材料不可解析 | `failed` | 3 | 不适用（`gates={}`） | 只写最小信封（见 F19） |

## 6. 渲染与可读性（F21–F22）

| # | 失败模式 | 触发信号 | 处置 | 记录位点 | D 规则 |
|---|---|---|---|---|---|
| F21 | 图面元素过多、不可读 | 布局溢出 / 节点被压缩到字号下限 | 减小默认字号、收缩节点宽度，或拆子图；严重时降 `partial` | `layout.warnings` / `uncertainty` | — |
| F22 | 目标导出格式不支持 | `F01_xxx` fail / 请求了未知格式 | 至少交付 SVG + PNG；其余格式如实说明不支持（实测 `--formats png` → exit 2、`partial`、PNG 正常产出 203655 字节） | `export_checks` | D16 |

## 7. 反预制答案 / 反编造（所有 F 的共同前提）

- 正式案例材料与 `examples/` 不同，**必须现场读取真实文件**推导；禁止把示例实体/边/数值抄进正式输出；
- 不写平台未提供的评分；没有的软件状态（如 matplotlib 缺失）如实说明，不假装有预览；
- 追溯链必须是完整的：**材料行号 → 实体/边 `source[]` → SVG `data-source` → `result.json.evidence_sources`
  → `export_checks[].sha256` → `change_records`**；断在任意一环都按上面某条 F 处理并在对应记录位点留痕。
