# examples/ — 最小调用示例与题集案例（示例，非正式案例）

> **文档路径重定向（本包 v7）**
>
> * `references/CASE-SET.md` → 已全文并入 `references/FAULT-MATRIX.md` 尾部的「并入全文」附录（本包 v7 为守住平台「≤50 个 UTF-8 文本文件」硬门而合并，**内容一字未删**）；本文出现的旧路径请按该附录阅读。

> ⚠ **本目录全部内容都是「示例，非正式案例」**：文件与产物由本包脚本在**合成**案例上
> 真实运行产生，仅用于演示接口与最小调用流程，**不参与正式评分、不冒充正式结果、
> 不含任何预制答案**。正式案例、白板与评分由平台提供/执行。
>
> 本文件在合并版里同时承担原 `examples/output/README-EXAMPLE.md` 的职责
> （见 §7：运行产物的保留范围、净化说明、两个示例的实测值与复跑方法）。

## 1. 文件

| 文件 / 目录 | 作用 |
|-|-|
| `case.json` | **route 图类**示例输入（CRISPR 文库药物筛选技术路线；10 实体 / 9 关系 / 3 阶段） |
| `task.md` | 上述案例的任务说明与**虚构**材料节选（route 例的 `source` 定位即指向它的 §2.1–§5） |
| `apparatus_spec.example.json` | **apparatus 图类**示例输入（冷冻干燥机装配；6 实体 / 5 关系；三桶布局） |
| `route_spec.example.json` | route 的**结构化 Spec 形态**（与 `case.json` 同源；演示「Agent 直接给 Spec」用法） |
| `route_spec.mutation.example.json` | **编辑用例**：作为 `--merge` 传给 `main.py`，同名 id 替换、新 id 追加 |
| `EXPECTED-OUTPUT.md` | ★ 期望产物清单、`result.json` 契约字段与本机实测值（替代随包的二进制产物） |
| `cases/` | **题集**的合成案例（每个目录 `case.json` + `task.md`；见 §3） |
| `output/` | 两个示例案例的**文本类**运行产物（`result.json` + `artifacts.json`；见 §4） |

## 2. 三种调用形态

```bash
SKILL_DIR=/skills/weekly-skill      # 技能根 = 含 SKILL.md 的目录

# ① 目录形态：--case 给目录 → 自动取该目录下 case.json（并取同目录 task.md）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/out

# ② 文件形态：显式给 case/task（官方运行时为 /input/*.json + /app/output）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" --out /tmp/out

# ③ 装置图示例（单独给文件时不猜同目录 task.md，材料来源宁可少而准）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/apparatus_spec.example.json" \
  --out /tmp/out-app

# ④ 编辑既有图稿（--merge；动作写入 change_record，by=agent）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" \
  --merge "$SKILL_DIR/examples/route_spec.mutation.example.json" --out /tmp/out-merge
```

期望：`exit 0`，`status=success`，`verify_ok=true`，`check.py` 输出 `ok:true`（G1–G10 全过），
产物 7 个文件写在 `<out>/<case_id>/`。逐项实测值见 `EXPECTED-OUTPUT.md`。

## 3. 题集案例（`cases/`）

`cases/<case_id>/{case.json,task.md}` 是**题集**里的两个新题材合成案例：

| 目录 | 题材 | 图类 | 难度 | 实体/关系 |
|-|-|-|-|-|
| `cases/mbr-wastewater-flow-01/` | 环境工程 · 市政污水 MBR 工段物质流向 | flow | 中 | 14 / 14 |
| `cases/dtms-stage-route-01/` | 分子生物学 · CRISPRi 四阶段技术路线 | route | 高 | 18 / 18 |

它们与上面的示例一样**不参与正式评分、不含预制答案**。逐案的期望产出结构、可接受区间、
不变量与实测值见 `../references/CASE-SET.md`；批量运行与验收：

```bash
python "$SKILL_DIR/scripts/case_set_run.py" --list                    # 先看题集与期望
python "$SKILL_DIR/scripts/case_set_run.py" --text-only --out <TMP>/case-set
# 退出码 0 = 全部案例 PASS；--text-only 同时给出"结构化 → 纯文本"的泛化损失
```

## 4. 运行产物的组织方式（`output/`）

每个示例目录保留 **两份**文本类文件：

```
result.json     结构化结果（OUTPUT_CONTRACT 的 18 个顶层字段 + output_contract + evidence + verify）
artifacts.json  三份产物的合并版（按 key 嵌套，内容逐字保留）：
                  evidence        证据链（实体/关系 locator+quote + 材料 sha256/size/role）
                  layout          布局模型（盒子 x/y/w/h、正交连线路径、图例、画布）
                  verify_report   校验报告（图层/文本/箭头/编号/图例/规则 + spec_sha16）
```

**不随包发布**（平台对 Skill 资源只接受 UTF-8 文本文件，二进制/矢量文件会在预检被拒）：
`figure.svg`（可编辑源文件）、`figure.png`、`figure.pdf`。这三个交付件**由
`scripts/main.py` 在运行时现场生成**，其清单与实测值见 `EXPECTED-OUTPUT.md`。

> 为什么把三份产物并成 `artifacts.json`：合并版要守住"≤50 个文本文件"的硬约束，
> 同属一个案例的运行产物合并后与 `result.json` 并列更清楚；**内容未删**，
> 只是改为按 key 嵌套。

## 5. 自查的正确对象（重要）

```bash
python "$SKILL_DIR/scripts/check.py" <TMP>/repro-route/demo-biotech-route-01/result.json   # → exit 0, ok:true
```

**不要**拿本目录里**冻结的** `result.json` 去跑 `check.py`：它引用的
`figure.svg`/`figure.png`/`figure.pdf` 按合规要求没有随包发布，`check.py` 会如实报出
G3/G4「文件不存在」。这不是缺陷，而是「包内不带二进制产物」的直接后果 ——
请对自己新跑出来的那份 `result.json` 自查（上面的命令）。

## 6. 净化说明（合规改动）

为满足「包内不得出现本机绝对路径」的硬约束，本目录的 JSON 已做**最小净化**，
未改动任何语义或数值：

| 字段 | 原值（本机运行痕迹） | 现值 |
|-|-|-|
| `result.json.execution.out_dir` | 本机临时输出目录的绝对路径 | `examples/output`（包内相对路径） |
| `result.json.fonts[role=png].path`、`output_contract.exports[].font_ttf` | 本机字体文件绝对路径 | 字体**文件名**（如 `msyh.ttc`） |
| `artifacts.json.evidence.sources[].path` | 本机输入文件绝对路径 | 包内相对路径（`examples/case.json`、`examples/task.md`、`examples/apparatus_spec.example.json`） |

`sha256`、`size`、实体/关系、布局、校验结论均与原始运行逐字节/逐值一致
（除上述字段外与复跑结果完全相同，见 `../TEST.md` T3）。

## 7. 两个示例的实测值与复跑（原 `output/README-EXAMPLE.md` 正文）

| 目录 | 案例 | 图类 | 实体/关系 | `verify_report.ok` | `spec_sha16` | 冻结 `figure.svg` 的 sha256 |
|-|-|-|-|-|-|-|
| `demo-biotech-route-01/` | CRISPR 文库药物筛选技术路线 | route | 10 / 9 | true | `e04e9d47e8ca0099` | `f8b01ce26b622187…`（复跑一致） |
| `demo-apparatus-001/` | 冷冻干燥机装置（三桶布局） | apparatus | 6 / 5 | true | `4603787adcb287d7` | `c6d422febfa1a1b9…`（复跑一致） |

> `figure.svg` 的 sha256 记录在 `result.json.output_contract.editable_sources[0].checksum_sha256`；
> 复跑同一输入会得到同一个值（确定性）。

复跑（同输入 → 同产物）：

```bash
SKILL_DIR=/skills/weekly-skill

# route 示例（--case 给目录时自动取 case.json + task.md）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <TMP>/repro-route

# apparatus 示例
python "$SKILL_DIR/scripts/main.py" \
  --case "$SKILL_DIR/examples/apparatus_spec.example.json" --out <TMP>/repro-app

# 编辑用例（--merge：同名替换 / 新 id 追加，动作写入 change_record）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" \
  --merge "$SKILL_DIR/examples/route_spec.mutation.example.json" --out <TMP>/repro-merge
```

期望：`exit 0`；`figure.svg`/`layout.json`/`evidence.json`/`verify_report.json` 与
本次冻结值逐字节一致；`result.json` 仅 `change_record` 时间戳与 `execution.out_dir` 不同。
