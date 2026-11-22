# academic-talk-organizer · v2 增益可验证版　（challenge-20870c35 · 学术汇报内容组织）

把**已有**科研材料组织成"可讲、可编辑、证据可追溯"的学术汇报产物。
本版的核心主张不是"功能更多"，而是**每一步都留下可被第三方复算的证据**，
并把"加载本包之后到底多出了什么、多花了什么"写成可复跑的对照协议（含**不利于本包**的结果）。

- Skill 本体：[SKILL.md](SKILL.md)（证据链 E1–E7 / 增益怎么被证明 / 降级纪律 / 核对清单）
- **对照协议与实测**：[references/GAIN-PROTOCOL.md](references/GAIN-PROTOCOL.md)
- **原始对照记录**：[references/gain-run-record.json](references/gain-run-record.json)（`gain_ab.py` 直出，未手工编辑）
- 字段契约：[references/OUTPUT_CONTRACT.md](references/OUTPUT_CONTRACT.md)
- 五维评分落点：[references/RUBRIC_MAP.md](references/RUBRIC_MAP.md)
- 对照口径（方法论层）：[COMPARE.md](COMPARE.md)　·　实测命令与观测：[TEST.md](TEST.md)

> **资源形态**（题面 Runtime contract：*at most 50 UTF-8 text files, 500KB each and 2MB total,
> no symlinks*）：本包只含 UTF-8 文本资源（`.md/.py/.json/.txt/.csv/.yaml/.yml`）；
> `.pptx`/`.png`/`.pdf` 一律运行期生成；包内无本机绝对路径、无 `__pycache__`、无符号链接。

## 一、快速开始

`$SKILL_DIR` = 含 `SKILL.md` 的目录（平台安装后即 `/skills/weekly-skill`）。
所有脚本自定位（`os.path.dirname(__file__)`），命令与当前 cwd 无关。

```bash
# 1) 主流程（示例案例；正式案例把 --case/--task 换成 /input 下的路径）
python "$SKILL_DIR/scripts/make_synthetic_inputs.py"          # 示例专用：生成运行时二进制输入
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out "$OUT"

# 2) 复核（全部退出码 0 = 通过）
python "$SKILL_DIR/scripts/validate_result.py" "$OUT/result.json"
python "$SKILL_DIR/scripts/check_contract.py"  "$OUT/result.json"
python "$SKILL_DIR/scripts/evidence_audit.py"  "$OUT/result.json"
python "$SKILL_DIR/scripts/verify_deck.py" "$OUT/editable_deck.pptx" \
       --expect-pages <N> --plan "$OUT/talk_plan.json"
python "$SKILL_DIR/scripts/selftest.py" "$OUT" --package-check "$SKILL_DIR"

# 3) 增益对照（本版核心；RUN 必须是包外临时目录）
python "$SKILL_DIR/scripts/gain_ab.py" --case "$SKILL_DIR/examples/case.json" \
       --work "$RUN/gain" --skill-dir "$SKILL_DIR"
# → 写出 $RUN/gain/gain_report.json，并把两个臂的产物留在 arm-A/ 与 arm-B/
```

## 二、`gain_ab.py` 是什么、不是什么

| 是 | 不是 |
|-|-|
| 一条命令跑两个臂的**对照装置**：A 臂 = 内置的确定性基线模拟器，B 臂 = 本包 `main.py` | **不是**本包的运行路径（`main.py` 从不调用它；平台评分也不依赖它） |
| 只读产物的**独立度量器**（不 import 本包任何模块，避免自己量自己） | 不是"质量评分器"：它量结构性指标与墙钟时间，不评判美观与科学正确性 |
| 复现题面所述"基础形态"的**代理臂** | **不是**平台真实基础 Agent 的运行，也不是平台白板 |

指标定义（D/C/E 三组）、公平性约束、复跑步骤、实测数字、以及两项**A 臂更优**的指标，
全部写在 [references/GAIN-PROTOCOL.md](references/GAIN-PROTOCOL.md)；
原始输出在 [references/gain-run-record.json](references/gain-run-record.json)。

## 三、依赖

| 依赖 | 用途 | 缺失时 |
|-|-|-|
| Python ≥ 3.8（本机 3.13.9 实测） | 解释器 | — |
| `python-pptx`（1.0.2 实测） | 生成/适配可编辑 `.pptx`；对照装置也用它读 deck | 跳过 deck，`status=partial`，其余产物照常，**命令仍返回 0** |
| `Pillow`（12.3.0 实测） | PNG 预览、图片校验 | 跳过预览（非致命） |
| `pypdf` / `PyPDF2`（6.14.2 实测，可选） | PDF 文本抽取（B 臂与 A 臂共用） | PDF 记 `parsed=false` 并降级 |

## 四、证据链一览

| 环节 | 产物 | 复算命令 |
|-|-|-|
| E1 材料实读 | `sources[]`、`environment` | 对拍磁盘 |
| E2 计划先行 | `talk_plan.json` | 改 `report_type` 重跑并 diff |
| E3 计划门 | `plan_gates.json` | `validate_plan.py` |
| E4 生成 deck | `editable_deck.pptx`、`deck_mode` | `verify_deck.py` |
| E5 渲染 | `previews/`、`preview_manifest.json` | 看 PNG 魔数与 manifest |
| E6 逐字证据审计 | `evidence_audit.json`、`evidence_map.json` | `evidence_audit.py` |
| E7 契约与自检 | `result.json.contract`、`self_check.json` | `check_contract.py` / `validate_result.py` / `selftest.py` |

## 五、限制与边界

- 不负责论文精读成稿、写作成稿、科研绘图素材生产；
- 对照是**单案例、单机**的机制与可测性证据，**不声称平台分数或"质量提升 X%"**；
- 预览是 Pillow 模拟渲染（带水印），不是 Office 栅格化；
- 证据定位是行级/章节级近似锚点，源材料更新后需按引文复核；
- 模板适配会丢弃起始演示自带页以保证页数等于冻结值（记入 `change_records`）；
- `gain_ab.py` 的 A 臂只使用 `case.json` 显式声明的材料（见 GAIN-PROTOCOL.md §8 第 3 条）。

## 六、维护

- 改行为：`templates/talk_config.json`、`assets/plan.schema.json`（改配置即改行为）；
- 改对照口径：`references/GAIN-PROTOCOL.md` §4（指标定义）与 `scripts/gain_ab.py`（实现）——
  **两者必须同步修改**，否则 `gain-run-record.json` 会与协议对不上；
- 附录：本版新增文件为 `scripts/gain_ab.py`、`references/GAIN-PROTOCOL.md`、
  `references/gain-run-record.json`；其余文件的算法与 CLI 接口与基线一致；
- 回归自测：按 [TEST.md](TEST.md) 跑一遍（含对照装置复跑与降级用例）；
- 提交前：`selftest.py <out> --package-check "$SKILL_DIR"` 全 ✓。

## 七、GitHub

见 `GITHUB_URL.txt`（第一行为作品在仓库中的目录链接）。
