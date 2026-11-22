# examples/ — 最小调用示例（示例，非正式案例）

> ⚠ **本目录全部内容都是「示例，非正式案例」**：文件与产物由本包脚本在两个**合成**
> 案例上真实运行产生，仅用于演示接口与最小调用流程，**不参与正式评分、不冒充正式结果、
> 不含任何预制答案**。正式案例、白板与评分由平台提供/执行。

## 1. 文件

| 文件 | 作用 |
|-|-|
| `case.json` | **route 图类**示例输入（CRISPR 文库药物筛选技术路线；10 实体 / 9 关系 / 3 阶段） |
| `task.md` | 上述案例的任务说明与**虚构**材料节选（route 例的 `source` 定位即指向它的 §2.1–§5） |
| `apparatus_spec.example.json` | **apparatus 图类**示例输入（冷冻干燥机装配；6 实体 / 5 关系；三桶布局） |
| `route_spec.example.json` | route 的**结构化 Spec 形态**（与 `case.json` 同源；演示「Agent 直接给 Spec」用法） |
| `route_spec.mutation.example.json` | **编辑用例**：作为 `--merge` 传给 `main.py`，同名 id 替换、新 id 追加 |
| `EXPECTED-OUTPUT.md` | ★ 期望产物清单、`result.json` 契约字段与本机实测值（替代随包的二进制产物） |
| `output/` | 两个示例案例的**文本类**运行产物（`evidence/layout/verify_report/result.json`） |

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

## 3. 与 `output/` 的关系

`output/` 里是上面 ①/②/③ 运行结果的**文本类**产物（证据链、布局模型、校验报告、
结果 JSON）；`figure.svg` / `figure.png` / `figure.pdf` 三个交付件**不随包发布**，
由脚本在运行时现场生成（平台对 Skill 资源只接受 UTF-8 文本文件）。
因此直接对包内**冻结的** `result.json` 跑 `check.py`，会如实报出 G3/G4 的
「可编辑源文件/导出件不存在」——这不是缺陷，而是「包内不带二进制产物」的直接后果；
正确的自查对象是**你自己新跑出来的**那份 `result.json`（见 `EXPECTED-OUTPUT.md` §4）。
