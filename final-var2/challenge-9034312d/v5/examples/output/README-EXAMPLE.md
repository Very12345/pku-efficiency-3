# examples/output/ — 示例运行产物（示例，非正式案例）

> ⚠ 本目录内容由本包脚本在两个**合成**示例案例上**真实运行**产生，
> **不是组织方正式案例的结果**，也不含任何预制答案。正式案例与白板由平台提供。

## 1. 保留了什么 / 没保留什么

每个示例目录保留 **4 个文本类产物**：

```
evidence.json       证据链（实体/关系 locator+quote + 材料 sha256/size/role）
layout.json         布局模型（SIR → 几何：盒子 x/y/w/h、正交连线路径、图例、画布）
verify_report.json  校验报告（layers/editable_text/arrows/no_dangling/numbering/legend/规则 + spec_sha16）
result.json         结构化结果（OUTPUT_CONTRACT 的 18 个顶层字段 + output_contract + evidence + verify）
```

**不随包发布**（平台对 Skill 资源只接受 UTF-8 文本文件，二进制/矢量文件会在预检被拒）：
`figure.svg`（可编辑源文件）、`figure.png`、`figure.pdf`。这三个交付件**由
`scripts/main.py` 在运行时现场生成**，其清单与实测值见 `../EXPECTED-OUTPUT.md`。

## 2. 净化说明（合规改动）

为满足「包内不得出现本机绝对路径」的硬约束，本目录的 JSON 已做**最小净化**，
未改动任何语义或数值：

| 字段 | 原值（本机运行痕迹） | 现值 |
|-|-|-|
| `result.json.execution.out_dir` | 本机临时输出目录的绝对路径 | `examples/output`（包内相对路径） |
| `result.json.fonts[role=png].path`、`output_contract.exports[].font_ttf` | 本机字体文件绝对路径 | 字体**文件名**（如 `msyh.ttc`） |
| `evidence.json.sources[].path` | 本机输入文件绝对路径 | 包内相对路径（`examples/case.json`、`examples/task.md`、`examples/apparatus_spec.example.json`） |

`sha256`、`size`、实体/关系、布局、校验结论均与原始运行逐字节/逐值一致
（除上述字段外与复跑结果完全相同，见 `../../TEST.md` T3）。

## 3. 两个示例

| 目录 | 案例 | 图类 | 实体/关系 | `verify_report.ok` | `spec_sha16` | 冻结 `figure.svg` 的 sha256 |
|-|-|-|-|-|-|-|
| `demo-biotech-route-01/` | CRISPR 文库药物筛选技术路线 | route | 10 / 9 | true | `e04e9d47e8ca0099` | `f8b01ce26b622187…`（复跑一致） |
| `demo-apparatus-001/` | 冷冻干燥机装置（三桶布局） | apparatus | 6 / 5 | true | `4603787adcb287d7` | `c6d422febfa1a1b9…`（复跑一致） |

> `figure.svg` 的 sha256 记录在 `result.json.output_contract.editable_sources[0].checksum_sha256`；
> 复跑同一输入会得到同一个值（确定性）。

## 4. 复跑（同输入 → 同产物）

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

## 5. 自查的正确对象（重要）

```bash
python "$SKILL_DIR/scripts/check.py" <TMP>/repro-route/demo-biotech-route-01/result.json   # → exit 0, ok:true
```

**不要**拿本目录里**冻结的** `result.json` 去跑 `check.py`：它引用的
`figure.svg`/`figure.png`/`figure.pdf` 按合规要求没有随包发布，`check.py` 会如实报出
G3/G4「文件不存在」。这不是缺陷，而是「包内不带二进制产物」的直接后果——
请对自己新跑出来的那份 `result.json` 自查（上面的命令）。
