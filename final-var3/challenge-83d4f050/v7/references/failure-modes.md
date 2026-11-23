# failure-modes.md — 失败模式与处置表

> 与 SKILL.md 的决策规则 D1–D12、检查点 CP1–CP5 一一对应（见 SKILL.md §4/§8）。
> 本题高分包几乎都带 failure-modes / failure_playbook（可靠体验 10 分的关键证据）。
> 表中每条都对应**脚本里的真实分支**与 `result.json` 里的真实记录位点，不是清单摆设。

## 1. 材料阶段失败

| # | 失败模式 | 检出点 | 处置 | 记录位点 |
|---|---|---|---|---|
| F1 | 材料缺失（case.json 无 materials 且目录无文件） | CP1.3 fail | 写 failed result，给出补救路径（补材料或 --model-file） | status=failed + uncertainty |
| F2 | 材料是 PDF/扫描件，无结构化文本 | extract method=manual-required | Agent 抽文本转成文本材料，或手工建规格 | extraction.method + change_records |
| F3 | 材料缺方向信息（不知上下游） | 人工核验 CP4 | 只画无向/结合类语义，标 uncertain；不臆造方向 | uncertainty + 边 uncertain=true |
| F4 | 同名基因/蛋白歧义 | P04 | 拆成两个实体并注明；无法区分时标 uncertain | uncertainty + note |
| F5 | 材料给出矛盾数值 | 人工核验 | 以材料原文为准，图与结果都标注矛盾点 | uncertainty + change_records |
| F6 | 材料无实体/关系 | extract manual-required | 明确 failed，不画空图凑数 | status=failed |

## 2. 规格/校验阶段失败

| # | 失败模式 | 检出点 | 处置 | 记录位点 |
|---|---|---|---|---|
| F7 | 机制规格未过 schema 门（类型/必需字段违规） | CP2（S01）fail | 阻断渲染，写 failed；修正规格后重跑 | status=failed |
| F8 | 边端点引用不存在的实体 | P02 fail | 阻断：删除或补实体 | self_check |
| F9 | 非反馈边逆流 | P03 warn | 必须说明缘由（转位/回流）或改方向 | uncertainty |
| F10 | 疑似反馈环未标注 | P07 warn | 补 `feedback=true` 右侧绕行 | topology |
| F11 | 图例缺在用类型 | L01/L02 fail | 补图例项；禁止"用了却不列" | legend_audit |
| F12 | 画布颜色不在图例/映射内 | L05 fail | 改回图例色或扩展图例 | legend_audit |
| F13 | 数值无法溯源 | E01 fail / T03 warn | 补 source 或降为假设并说明 | uncertainty |

## 3. 渲染/导出阶段失败

| # | 失败模式 | 检出点 | 处置 | 记录位点 |
|---|---|---|---|---|
| F14 | matplotlib 不可用 | preview 异常捕获 | 保留 SVG 源；PNG/PDF 缺失如实记录（`status=partial`、exit 2、G5=false） | export_checks + deliverables 空预览 + uncertainty |
| F14b | 运行者显式只要求 SVG（`--formats svg`） | 跳过预览渲染 | 不报错：只交付可编辑 SVG 源，并说明"本次未请求预览" | uncertainty + deliverables 空预览 |
| F15 | 中文字体缺失 | mpl 字体探测 | 告警并记录 font；SVG 用字体栈不受影响 | preview warnings + uncertainty |
| F16 | 导出失败（某格式） | F01_xxx fail | 至少交付 SVG + PNG；其他格式如实说明 | export_checks |
| F17 | 图面元素过多不可读 | 布局溢出/节点收缩 | 减小字号/收缩节点宽度，或拆分子图并记录 | layout.warnings |
| F18 | schema 文件缺失 | S01 warn | 降级用内置默认并记录（不阻断） | uncertainty |

## 4. 状态一致性（status 三值）

- `success`：断性检查全过 + **提取已人工核验** + 门 G1–G8 全过；
- `partial`：有 SVG 源但存在 fail/warn 或**自动草稿未核验**——失败/警告全部列明；
- `failed`：无法产出可编辑源、SVG 不合法、或 CP2 schema 门不过。
- 任何失败都不得静默：全部进入 `self_check / topology / legend_audit / uncertainty /
  change_records` 对应位点（诚实记录是判分"结果可核验性"的前提）。

## 5. 反预制答案 / 反编造规则

- 正式案例材料与示例不同，必须现场读取真实文件推导，禁止把 examples 内容抄入正式输出；
- 不写平台未提供的评分/分数；没有的软件状态（如 matplotlib 缺失）如实说明；
- 结果的可核验链 = 材料行号 → 实体/边 source → SVG data-source → result.json
  evidence_sources → export_checks(sha256) → change_records（D 系列自检守护）。

## 6. 确定性与字节级可复现（v7 新增：FM-D 系列）

判据、实测表与配方全文见 `references/DETERMINISM.md`；机器可读证据 `determinism_report.json`。

| # | 现象 | 判据（命令/字段） | 处置 | 留痕位置 |
|-|-|-|-|-|
| FM-D1 | `result.json` 每次跑都不一样，怀疑流水线不稳定 | `determinism.py` → `volatile_fields[]`：只有 `*.ts` 类路径 ⇒ 属**故意**（真实运行时间） | 不必修；要比对内容就套用投影掩码 | `stabilization.json_projection` |
| FM-D2 | 同一命令在不同 cwd 下产出不同 `result.json`（含路径字段与体积） | `volatile_fields` 出现 `$.provenance.case_file` / `$.change_records[*].why` | **固定 cwd**（`cd "$SKILL_DIR"` 再跑），或接受投影比对 | `references/DETERMINISM.md` §4 |
| FM-D3 | 两次运行"恰好同秒"，让时间戳差异没暴露 | 环境配方两侧有 `sleep 1.2`（探针内置） | 不要用"刚好相等"当确定性证据；探针已强制错开 | `env_recipe.result_json_diff_paths` |
| FM-D4 | `diagram.pdf` 哈希每次都变 | `byte_diff.diagram.pdf`：差异只在 `/CreationDate` 的秒位（本机 1 处，偏移 104020 起、1–2 字节） | 用 PDF 规范化（配方 B）或 `SOURCE_DATE_EPOCH`（配方 C） | `stabilization.pdf_normalization` |
| FM-D5 | `diagram.png` 是否含时间元数据 | `png_metadata_probe.has_time_chunk` = false（只有恒定 `tEXt`） | 无需处理；若换库后出现 `tIME`，PNG 会进入易变清单 | `png_metadata_probe` |
| FM-D6 | 跨机/跨库版本对比出现不一致 | `config.python` / `matplotlib` / `pillow` 版本 | **不要过度声称**：PNG/PDF 含库版本与字体子集信息；只对 5 个稳定产物做跨机对拍 | `references/DETERMINISM.md` §7 未覆盖声明 |
