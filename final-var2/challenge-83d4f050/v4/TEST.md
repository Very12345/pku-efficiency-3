# TEST.md — 自测方法、期望输出与实测记录（合规文本包）

> 本文件回答两件事：**别人怎么自测**、**期望看到什么**；附录是本次打包机器上的真实实测
> 输出（含 sha256 与确定性双跑），供复核与复跑。
> 实测时间：2026-11-22（+08）。环境：Windows，Python 3.13.9（`python`），
> matplotlib + Pillow 可用；命令均在**临时目录的包副本**上执行，`cwd` 不是技能根目录
> （用于证明自定位）。

## 0. 自测三步（任何人可复跑）

```bash
# 0) 定位技能根目录（含 SKILL.md 的那一层），复制到临时目录
export SKILL_DIR=/tmp/challenge-83d4f050          # 本机解压路径；平台容器为 /skills/weekly-skill

# 1) 冒烟：示例案例 + 已核验规格 → 期望 exit 0、status=success、gates 8/8
python3 "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /tmp/t2

# 2) 契约独立复查 → 期望 exit 0（C01–C07 全 pass）
python3 "$SKILL_DIR/scripts/check_contract.py" --result /tmp/t2/result.json \
    --case "$SKILL_DIR/examples/case.json"

# 3) 图面/模型/图例/导出全检 → 期望 exit 0（fails=0）
python3 "$SKILL_DIR/scripts/validate_figure.py" --out /tmp/t2
```

**判据**（三条都成立才算自测通过）：
1. 第 1 步退出码 0，`/tmp/t2` 下出现 7 个文件
   （`diagram.svg` / `diagram.png` / `diagram.pdf` / `result.json` / `model.json` /
   `topology.json` / `legend_audit.json`）；
2. 第 2、3 步退出码均为 0；
3. `result.json` 顶层含 `references/OUTPUT_CONTRACT.md` §2 的全部字段
   ＋ `case.json` 的 `output_contract` 字段，且**顶层无 null**。

## 1. 期望输出速查

| 场景 | 命令要点 | 期望 status / exit | 产物 |
|-|-|-|-|
| 已核验规格 + matplotlib | `--model-file ...` | `success` / **0** | 7 件，`gates 8/8` |
| 已核验规格 + 只要求 SVG | `--model-file ... --formats svg` | `partial` / **2**（G5=false，诚实说明未请求预览） | SVG + 4 个 JSON |
| 已核验规格 + 无 matplotlib | 同 1 | `partial` / **2**（仅缺 PNG/PDF，SVG 与有 matplotlib 时逐字节相同） | SVG + 4 个 JSON |
| 自动草稿（未人工核验） | 省略 `--model-file` | `partial` / **2**（`uncertainty` 提示逐条复核） | 7 件 |
| 规格不过 schema 门 | `--model-file <bad.json>`（如 `type="banana"`） | `failed` / **3**（`reason="schema gate fail"`） | 仅 `result.json` |
| 材料缺失/不可读 | 空材料目录 | `failed` / **3** | 仅 `result.json` |

## 2. T1 编译检查 —— 通过

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py
```

11 个脚本全部 COMPILE OK（打包时 `python -m py_compile` 无输出、退出码 0）。

## 3. T2 冒烟：示例案例 + 已核验机制规格 —— 通过（success）

```bash
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /tmp/t2
```

```
[main] case_id=example-egfr-mapk status=success entities=9 edges=9 bands=4 verified=True
SUMMARY {... "status": "success", "self_check_passed": true, "failures": 0, "warnings": 0,
         "gates": "8/8", "extraction": {"method": "manual", "verified_by_agent": true}}
exit=0
```

产物 7 件（sha256 前 16 位 / 字节数）：

```
diagram.svg         27f344a0dfb2e90f   17771
diagram.png         9137715961238f3f  203655
diagram.pdf         （每次不同，见 T4） 108045
result.json         （含时间戳，见 T4）   ~28.8 KB
model.json          f93a20a283492f73   11418
topology.json       eb826fc5557fccfc    1434
legend_audit.json   efdb1805c839d648    1807
```

`self_check`：32 项检查全 pass、`failures=0`、`warnings=0`；`gates` G1–G8 全 `pass`；
实体 9 / 边 9 / 区室 4（胞外→膜→胞质→核），5 类箭头全部在用，负反馈环 1 条右侧绕行；
`export_checks` 三项全 pass；`output_contract` 的两个自定义字段回显到顶层
（`custom_demo_field`: str、`custom_list_field`: list），**顶层无 null**。

## 4. T3 冒烟：自动草稿（未核验路径） —— 通过（partial，符合设计）

```bash
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/t3
# [main] ... status=partial entities=9 edges=9 bands=4 verified=False ; exit=2
```

- `status=partial`、`exit=2`：**未人工核验的草稿不允许 success**；
- `self_check`：32 项、`failures=0`、`warnings=1`（`P03` 逆流边 `r9`：核内 ERK→RAF 需人工
  确认是否反馈环——正是留给 Agent 核验的信号）；`gates 8/8`；
- `uncertainty` 明确写出"实体/关系由草稿提取器自动生成，尚未由 Agent 逐条复核（CP4 未过）"；
- 草稿提取器：`entities=9`、`edges=9`、`method=auto-draft`，无解析告警。

## 5. T4 确定性：同输入双跑 —— SVG/PNG/JSON 逐字节一致，PDF 仅时间戳差异

```bash
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /tmp/t4a
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /tmp/t4b
```

| 文件 | 双跑 sha256（前 16 位） | 结论 |
|-|-|-|
| `diagram.svg` | `27f344a0dfb2e90f` / `27f344a0dfb2e90f` | **一致**（SVG 无时间戳，为输入+布局纯函数） |
| `diagram.png` | `9137715961238f3f` / `9137715961238f3f` | **一致** |
| `model.json` | `f93a20a283492f73` / `f93a20a283492f73` | **一致** |
| `topology.json` | `eb826fc5557fccfc` / `eb826fc5557fccfc` | **一致** |
| `legend_audit.json` | `efdb1805c839d648` / `efdb1805c839d648` | **一致** |
| `diagram.pdf` | `b3c8d1c4bf147d8` / `8ed51b8a1cd35c7` | 差异：matplotlib 内嵌 PDF `CreationDate` 时间戳（如实记录） |
| `result.json` | 含 `provenance.ts` / `change_records[].ts` | 去时间戳后与本次一致（自检探针 `model_sha16`/`svg_sha16` 双跑相等） |

`self_check.determinism` = `model_sha16=f93a20a283492f73`、`svg_sha16=27f344a0dfb2e90f`，
两次运行相同。**确定性承诺 = SVG/PNG/model/topology/legend_audit**；PDF 与 result.json
含时间戳，不作确定性承诺。

## 6. T5 契约独立复查 —— 通过

```bash
python3 "$SKILL_DIR/scripts/check_contract.py" --result /tmp/t2/result.json \
    --case "$SKILL_DIR/examples/case.json"
```

```
pass C01 case_id 非空 / C02 status 三值枚举 / C03 信封字段齐全 / C04 顶层禁止 null /
     C05 output_contract 全部回显 / C06 deliverables 路径存在 / C07 硬性门 G1–G8 全过
contract|ok|case=example-egfr-mapk|status=success|checks=7      exit=0
```

## 7. T6 图面全检（build 后 verify 成对） —— 通过

```bash
python3 "$SKILL_DIR/scripts/validate_figure.py" --out /tmp/t2
# standalone-verify|ok=True|fails=0|warns=0     exit=0
```

30 项检查全 pass：M（模型）、T（溯源）、P01–P08（拓扑/方向/区室/消歧/反馈）、
L01–L08 与 E01/E02（图例覆盖、箭头=图例、颜色⊆图例∪映射、虚线语义、线宽映射、
数值溯源、色带端点、图层命名）、F01/F02（产物存在、PNG 可打开）、S01（schema 门）、
D01（确定性探针）。

## 8. T7 schema 门拦截（CP2 阻断） —— 通过

```bash
# 把示例规格的首个实体 type 改成 "banana"（raw 未归一化直接校验，防静默改写）
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file /tmp/bad.json --out /tmp/t7
# SUMMARY {"status": "failed", ..., "reason": "schema gate fail"}      exit=3
```

## 9. T8 抽取器独立 CLI —— 通过

```bash
python3 "$SKILL_DIR/scripts/extract.py" "$SKILL_DIR/examples/materials/example_material.md"
# {"entities": 9, "edges": 9, "method": "auto-draft", "warnings": []}
```

## 10. T9 降级路径（两条都真跑过） —— 通过

| 场景 | 命令 | 实测 | SVG 是否仍产出 |
|-|-|-|-|
| 显式只要 SVG | `--formats svg` | `partial` / exit 2 / G5=false / `previews=[]`、`exports=[]`，`uncertainty` 记"PNG/PDF 预览未生成或未请求" | 是，`svg_sha16=27f344a0dfb2e90f`（与全量运行**逐字节相同**） |
| matplotlib 不可用 | `PYTHONPATH=<shadow> ` 模拟 `import matplotlib` 失败 | 同上（异常被捕获，降级为仅 SVG） | 是，`svg_sha16` 同样为 `27f344a0dfb2e90f` |

⇒ 预览能力缺失时**绝不假装有预览**：`deliverables.previews/exports` 为空数组、
`uncertainty` 写明原因与补救命令，可编辑源不受影响。

## 11. T10 本次合规重打包中发现并修复的缺陷（诚实记录）

均为本机实跑发现，修复后重新验证：

1. **`deliverables.audits` 恒为空**：`result_writer.py` 用 `out_paths.get("topology.json")`
   查键，而实际键名是 `topology` / `legend_audit` → 审计产物永远列不进交付物，
   与 `OUTPUT_CONTRACT.md` §5 不一致；已改为按真实键取 basename（现输出
   `["topology.json","legend_audit.json"]`）。
2. **`--formats svg` 直接崩溃**：`mpl_backend.render_preview` 在只请求 SVG 时返回的字典
   没有 `png`/`pdf` 键（与它自己的 docstring 矛盾）→ `KeyError: 'png'`，退出码 1；
   已改为始终携带 `png/pdf` 键，并在 `main.py` 中未请求预览时**跳过预览渲染**
   （纯标准库路径因此成立）。
3. **`UnboundLocalError: ex`**：`uncertainty` 记录复制了 except 分支里才存在的 `ex`
   变量，改成对 `preview_meta["warnings"]` 统一记录。
4. **`files` 依赖目录残留**：首次运行时 `files` 不含 `result.json`，重跑才含
   （因为清单在写盘前生成）→ 现固定并集 `{"result.json"}`，首次与重跑一致。
5. **本机绝对路径泄漏**（合规硬门）：`examples/output/result.json` 里既有
   `provenance.command/case_file` 的 Windows 盘符绝对路径，也有检查详情里的绝对产物路径；
   `scripts/main.py` 增加 `portable_path()`（技能根内 → 相对路径，容器路径如
   `/input`、`/app/output` 原样保留），`scripts/validate_figure.py` 的检查详情改用
   basename；示例产物已用**相对命令**重跑生成（`--out examples/output`）。
6. **`provenance.schema` 在 Windows 上写成反斜杠**（`assets\mechanism-spec.schema.json`）
   → 统一走 `portable_path()`，输出 `assets/mechanism-spec.schema.json`。

## 12. T11 失败注入与恢复演练 —— 通过（24/24 符合期望 · 0 静默 · 6/6 恢复）

命令（包外副本上执行，避免 `__pycache__` 污染）：

```bash
cp -r "$SKILL_DIR" /tmp/fault-skill
python3 /tmp/fault-skill/scripts/fault_inject.py --skill /tmp/fault-skill --out /tmp/fault-out
# SUMMARY {"scenarios": 24, "expect_ok": 24, "mismatch": [],
#          "silent_failures": [], "recovery": "6/6"}          exit=0
```

四形态覆盖与实测读数（完整 24 行表见 `references/FAULT-MATRIX.md` §2）：

| 形态 | 场景数 | 实测退出码集合 | 实测 status 集合 | 静默失败 |
|-|-|-|-|-|
| 输入 | 8 | `1`(入口拒绝) / `3`(failed) / `2`(partial) / `0`(带留痕) | —/failed/partial/success | 0 |
| 模板 | 5 | `0` | success | 0（缺 schema 记 warn；缺核对清单/结果模板属**文档资产**，主流程不读） |
| 依赖 | 4 | `2` | partial | 0（`g5_png=false`，previews 为空，原因入 `export_checks`+`uncertainty`） |
| 契约 | 7 | `0`(主流程) / `1`(校验 CLI) | success / — | 0（`check_contract.py` 实测能抓顶层 null 与缺产物） |

恢复演练 6/6：修好注入源后复跑均为 `exit 0 / status=success / gates 8/8`。

**演练发现并修掉的三处静默失败**（修复前后逐条实测，详见 `FAULT-MATRIX.md` §4）：

| # | 注入 | 修复前 | 修复后 |
|-|-|-|-|
| G1 | 边指向不存在的实体 id | `exit 0 / success / uncertainty 0`（丢边无痕） | `uncertainty=1`，精确到 `e2→e999` |
| G2 | 删掉 / 弄坏 `assets/palettes.json` | `exit 0 / success / 零留痕` | `uncertainty=1`，区分 `FileNotFoundError`/`JSONDecodeError` |
| G3 | `case.json` 无 `task` 且无 `task.md` | CP1.2 判 warn 但被丢弃 | `uncertainty=1`：CP1 前置检查降级 |

> 这三处修复**只增加代码**：`scripts/model.py` 381→437 行（+56）、`scripts/main.py` 482→512 行（+30），
> 删除行数 0；CLI 参数名、默认值、退出码语义未改；其余脚本与 `assets/` 逐字节未改。

## 13. 合规自检（本包文本形态）

| 项 | 实测 | 上限 |
|-|-|-|
| 文件数 | 见包根汇报（`validate_pkg.py` 输出） | 50 |
| 扩展名 | 仅 `.md .py .json .txt` | 七种白名单 |
| 包内二进制 | 无（`diagram.svg/png/pdf` 运行时生成） | 禁止 |
| `__pycache__` / `.pyc` | 无 | 禁止 |
| 包内本机盘符绝对路径（字母＋冒号＋反斜杠） | 无（`grep -rn` 0 命中） | 禁止 |
| 单文件 / 总字节 | 见汇报（均远低于 500KB / 2MB） | 500KB / 2MB |

## 14. 环境备注与限制（如实声明）

- **终端编码**：脚本入口把 stdout/stderr 重配置为 UTF-8；Windows 控制台若仍按 GBK 解码，
  中文摘要可能显示为乱码——用 `chcp 65001` 或 UTF-8 终端即可，**文件内容始终是 UTF-8**。
- 渲染后端本文档实测为 matplotlib；无 matplotlib 时按 T9 降级，SVG 源不受影响。
- 实体抽取依赖材料文本结构（表格 / `A | 动词 | B` / `- A 动词 B（证据）`）；散文与 PDF
  材料需 Agent 手工建规格（CP2b/CP3），这是"准确率优先"的刻意设计。
- PDF 与 `result.json` 含时间戳，不作确定性承诺；确定性承诺见 T4。
- `examples/` 全部标注"示例，非正式案例"，与平台固定 3 个正式案例无关。
