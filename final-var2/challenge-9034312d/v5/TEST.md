# TEST.md — 本版验收记录（全部为本机真跑，命令与观测原样保留）

> 所有命令都在**包外临时副本**里执行（`cp -r <本包> <临时目录>` 后再跑），
> 因为在本包目录里跑脚本会生成 `__pycache__`，打包形态门 R5 会 FAIL。
> 所有数字都是跑出来的；本文件不含估计值。

- 环境：Windows 11（10.0.22621）· CPython **3.13.9** · Pillow 12.3.0 · reportlab 5.0.0 · 本机有中文字体
- 被测包：本包（v5 多案例泛化与题集版），`scripts/main.py` 等既有脚本**未做任何修改**
- 复跑总耗时：约 10 秒（4 案结构化 + 4 案文本探针 + 若干负例）

## T1 · 合规形态

```bash
python validate_pkg.py <本包目录>
```

期望与实测：`[PASS]`，无 `FAIL`。检查项：扩展名白名单、文件数 ≤50、单文件 ≤500KB、
合计 ≤2MB、无符号链接、无 `__pycache__`/`.pyc`、全部 UTF-8、每个 `.py` 可编译、
包内无本机绝对路径（Windows 盘符+反斜杠形态、`/Users/`、Windows 长路径前缀）。

## T2 · 题集跑批（本版核心，4 案）

```bash
cd <包外副本>
python scripts/case_set_run.py --out <临时输出目录> --json <临时输出目录>/report.json
```

实测（原样摘要）：

```
case_set_run · 案例 4 个 · PASS 4 / FAIL 0 · 期望表已加载 · python 3.13.9 (win32)
case_id                    图类        难度       退出   status    实体   关系   verify 结论
apparatus-spec-01          apparatu  低        0    success   6    5    True   PASS
demo-biotech-route-01      route     低        0    success   10   9    True   PASS
dtms-stage-route-01        route     高        0    success   18   18   True   PASS
mbr-wastewater-flow-01     flow      中        0    success   14   14   True   PASS
```

逐案详值（同一份报告）：

| case_id | 退出码 | `status` | 实体 | 关系 | `verify.ok` | 告警 | 失败门 | `spec_sha16` | PNG / PDF 字节 | 耗时 |
|-|-|-|-|-|-|-|-|-|-|-|
| `apparatus-spec-01` | 0 | success | 6 | 5 | true | — | 无 | `4603787adcb287d7` | 28 884 / 3 889 | 0.71 s |
| `demo-biotech-route-01` | 0 | success | 10 | 9 | true | — | 无 | `e04e9d47e8ca0099` | 54 982 / 4 448 | 0.69 s |
| `dtms-stage-route-01` | 0 | success | 18 | 18 | true | `recycle-review` | 无 | `cb33950dedb47795` | 82 561 / 5 421 | 0.69 s |
| `mbr-wastewater-flow-01` | 0 | success | 14 | 14 | true | `recycle-review` | 无 | `5b65c6612f7714e0` | 53 567 / 5 149 | 0.58 s |

四个案例的 `result.json` 顶层键均为 **18 个**（与契约一致），`output_contract` 四段齐全。

## T3 · 泛化探针（`--text-only`，本版最重要的测量）

把每个案例压扁成"只留 `text` 字段"，再跑一遍同样流程：

| case_id | 实体 结构化→文本 | 关系 结构化→文本 | 实体保留率 | 关系保留率 | 丢失的告警 | 文本版 `status` | 文本版 `uncertainty` |
|-|-|-|-|-|-|-|-|
| `apparatus-spec-01` | 6 → 4 | 5 → **0** | 0.667 | **0.000** | — | **`partial`** | `orphan_entities`, `relations` |
| `demo-biotech-route-01` | 10 → 2 | 9 → 1 | 0.200 | 0.111 | — | `success` | `relations` |
| `dtms-stage-route-01` | 18 → 7 | 18 → 6 | 0.389 | 0.333 | `recycle-review` | `success` | `relations` |
| `mbr-wastewater-flow-01` | 14 → 6 | 14 → 5 | 0.429 | 0.357 | `recycle-review` | `success` | `relations` |

**三条结论**（逐条可复跑）：

1. 文本解构只串联相邻步骤 ⇒ 分流/合流/回流/依赖/里程碑整体丢失；
2. 装置图最危险：5 条关系全丢 + 4 个孤实体 ⇒ `status` 由 `success` 掉到 **`partial`**；
3. **输入退化不自动降级**：C-3 只剩 2 实体 1 关系仍报 `success`（只有出现孤儿实体才降级）
   ⇒ 复核时要同时看 `extraction`（应为 `text-heuristic`）与实体数是否与材料规模相称。

## T4 · 期望表能否真的判 FAIL（两个负例，都真跑过）

判据必须"能判错"，否则等于装饰。做了两件事：

**(a) 把期望改成不可能满足的值** —— 临时把 C-1 的 `entities.min` 从 14 改成 30，
再跑 `--only mbr-wastewater-flow-01`：该案判 **FAIL**，偏差明细为
`实体数 14 < 允许下限 30`，脚本退出码 **1**。⇒ 区间判据是活的。

**(b) 放一个未登记的案例目录** —— 在 `examples/cases/` 下新建 `zz-probe-unregistered`
（内容复制 C-2、只改 `case_id`）但不登记进 `case-set.json`，再全量跑批：

```
case_set_run · 案例 5 个 · PASS 3 / FAIL 2 · 期望表已加载
mbr-wastewater-flow-01     flow   中   0  success  14  14  True  FAIL
    ↳ 实体数 14 < 允许下限 30
zz-probe-unregistered      route   -   0  success  18  18  True  NO-EXPECTATION

有 1 个案例未登记期望：跑了但没验收 —— 请在 references/case-set.json 补登（见 SKILL.md D13）
```

⇒ 未登记的案例**会被跑**但标 `NO-EXPECTATION`（不算 FAIL，退出码仍按 FAIL 计），
且脚本会打印提醒。这正是 `SKILL.md` 的 D13 要防的"加了案例却等于没验收"。

## T5 · 主流程单案可跑（基线行为未变）

```bash
python scripts/main.py --case examples/cases/dtms-stage-route-01 --out <临时目录>
```

实测：退出码 **0**，`status=success`，`verify_ok=true`，`check_ok=true`，
`gates` G1–G10 全 true、`issues=[]`，产物 7 件
（`evidence.json` / `layout.json` / `figure.svg` / `figure.png` / `figure.pdf` /
`verify_report.json` / `result.json`）。

## T6 · 形态自检（提交前必跑）

```bash
python validate_pkg.py <本包目录>                          # 期望 PASS
grep -rnE '(^|[^A-Za-z])[A-Za-z]:[\\/]' <本包目录>         # 期望无输出
find <本包目录> -name '__pycache__' -o -name '*.pyc'       # 期望无输出
```

## T7 · 本次**没有**测的（如实列出）

| 未测项 | 为什么 |
|-|-|
| 平台固定 3 个案例 | 材料与白板由组织方提供，参赛者不可见；本包全部数字来自合成案例 |
| 与"不加载 Skill 的裸 Agent"的质量对照 | 本版聚焦多案例泛化，未起裸 Agent 臂 |
| 实体数 > 24 / 阶段数 > 5 | 未纳入本轮题集；布局拥挤度未评估 |
| Linux / 容器环境 | 本轮仅 Windows 11 + CPython 3.13.9；案例与判据本身跨平台，但未实测 |
| 非 UTF-8 材料、超长材料、并发运行 | 未纳入本轮 |
| 任何分数 | 本包不宣称具体分数；评分由平台执行 |
