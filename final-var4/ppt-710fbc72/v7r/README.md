# Academic Slide Adapter — 学术 PPT 模板与格式适配 Skill（slides 组）
## 本轴：确定性与字节级可复现（v7）

`ppt-710fbc72`（玻尔产品周赛·北大专区·学术效率）的可运行 Skill 包。

**功能不变**：把论文/研究材料组织成结构清楚、证据可追溯、可编辑、符合模板
要求的学术汇报 —— 两阶段工作流：先出**适配方案**（母版/版式/占位符审计 +
页→版式分配 + 批量规则 + 图表放置计划，`adopt_plan.json`，CP1 门），再按方案
真实套用模板建册（占位符继承可查、方案↔执行一致性可查），逐页主张 + 图号引用
+ 讲稿备注 + 页→来源证据映射，统一页脚页码、图表等比适配，交付
`deck.pptx` + PNG 预览 + `result.json`（CP3 契约门 G1–G8）。

**本轴新增的是"可复现性的证据"**，不是又一批功能：

| 新增 | 作用 | 判据 |
|-|-|-|
| `scripts/determinism.py` | 用 5 组受控条件共 16 次真实重跑，对**每个产物**做 sha256 比对，并把差异**归因到具体 JSON 字段** | exit 0 |
| `references/DETERMINISM.md` | 逐字段说明哪些是**故意**不稳定的、稳定化办法、未覆盖声明 | 与实测报告一致 |

**一句话结论（实测，非声明）**：跨进程 / 跨 cwd / 跨 `PYTHONHASHSEED` /
相对与绝对参数共 16 次运行中，**可编辑 `.pptx` 与两张预览 PNG 逐字节一致**；
全部 JSON 记录在去掉"声明的时间戳 + 宿主锚点 + 锚点派生摘要"后**收敛为单一值**；
**声明表外的差异字段 0 条**。

**本包只含 UTF-8 文本资源**（`.md/.py/.json/.txt`，≤50 个、单文件 ≤500KB、
合计 ≤2MB、无符号链接）：模板、示例图、预览等二进制一律**运行时生成**，
所以仓库里看不到 `.pptx`/`.png`。

## 运行方法

环境：Python 3.9+；依赖 `python-pptx`、`Pillow`（运行必需）。
本机实测：Python 3.13.9 / python-pptx 1.0.2 / Pillow 12.3.0。
无 LibreOffice/PPT 时预览为 PIL 示意图（如实标注，**不产伪 PDF**）。

`$SKILL_DIR` = 本包根目录（平台装到 `/skills/weekly-skill`）。**下面所有命令在
任意 cwd 下都能跑**：脚本用 `os.path.dirname(__file__)` 自定位，不依赖 cwd。

**① 正式流程**（产物写 `--out`，两阶段自动完成）：

```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> --task <task.md> --out <out>
```

官方运行时：`--case /input/case.json --task /input/task.md --work /app/work --out /app/output`。

**② 复现性实验**（必须给**包外**目录；包内跑会留下 `__pycache__`，资源契约拒收）：

```bash
RUN=<包外目录>
python "$SKILL_DIR/scripts/determinism.py" --skill "$SKILL_DIR" --run "$RUN" \
    --runs 3 --json "$RUN/determinism_report.json" --markdown "$RUN/determinism.md"
echo "exit=$?"        # 本机实测 0
```

只跑某几个条件（调试用）：

```bash
python "$SKILL_DIR/scripts/determinism.py" --skill "$SKILL_DIR" --run "$RUN" \
    --condition c1,c4
```

条件含义：`c1` 独立进程 ×3 · `c2` 隔 1.2 s 再跑 ×3 · `c3` 三种 cwd 深度 ·
`c4` `PYTHONHASHSEED` = 0/1/12345/未设置 · `c5` 相对参数 vs 绝对参数。

**③ 契约门**：

```bash
python "$SKILL_DIR/scripts/validate_result.py" --case <case.json> --result <out>/result.json
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --out-dir <out> --case <case.json>
```

## 判据速查（determinism.py）

| 层 | 含义 | 谁必须过 |
|-|-|-|
| L1 | 原始字节 | `.pptx`、两张 PNG、`summary.txt`、`_runtime/builtin.pptx` |
| L2 | 去掉声明的时间戳/版本字段 | （诊断层，不作判据） |
| L3 | 再归宿主锚点 `<CWD>/<OUT>/<CASEDIR>` | `spec/adopt_plan/content/render_log` |
| L4 | 再去锚点派生摘要 `<DERIVED>` | 全部 JSON（含 `audit.json`、`result.json`） |

另有 **`unexpected_volatile` 必须为 0**：任何落在四张声明表之外的差异字段都会让
脚本 exit 1，并逐条打印字段路径。这就是"声明表只能新增并写明理由，不能放宽匹配"
的强制机制。

## 依赖与限制

- 运行必需：`python-pptx`（建/读 deck）、`Pillow`（预览）。两者缺失时管线
  **如实写 `status=failed` 的 result.json**，不静默成功（见 `references/failure-modes.md`）。
- 预览是 **PIL 示意图**：无 LibreOffice/PowerPoint 时不产伪 PDF，`render_log.json`
  与 `_PREVIEW_ARE_SCHEMATIC.txt` 双重标注。
- **跨机器**可复现性**未验证**：本实验全部 run 在同一台机器、同一 Python 上。
  `tool_versions` 与字体探测字段保留下来，正是为了让跨机器差异**看得见**。
- `determinism.py` 会把包**整体复制**到 `--run/skill` 再执行：既避免污染提交包，
  也保证被测的是"包里那一份字节"。

## 维护

- 改管线任何一步 → **必须重跑 `determinism.py`** 并把新报告重新渲染进
  `references/DETERMINISM.md`；声明表只允许"新增 + 写明理由"。
- 交付前包外验收：`python validate_pkg.py <包目录>`（扩展名白名单、≤50 文件、
  ≤500KB/个、≤2MB、无 `__pycache__`、无本机绝对路径、`py_compile`）。
- 二进制资源永不入包：模板由 `make_template.py`、示例图由
  `make_synthetic_inputs.py`、产物由运行期生成。

## 许可与来源

本包为参赛作品，示例案例是**合成示意数据**（`examples/README.md` 已标注），
不含任何正式案例答案；正式案例与白板由平台提供。
