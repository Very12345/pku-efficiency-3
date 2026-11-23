# academic-talk-organizer v7 · challenge-20870c35（学术汇报内容组织 · slides 组）

把**已有**的论文/研究材料组织成：结构清楚、证据可追溯、可编辑、符合听众/时长/模板约束的学术汇报产物；
并且**同输入连跑多次可逐字节复核**。

本包是「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35 的 Skill 交付物，
轴 = **确定性与字节级可复现**（v7）。`SKILL.md` 是 Agent 加载入口；
实测命令与观测见 [TEST.md](TEST.md)；对照口径见 [COMPARE.md](COMPARE.md)；
五维落点见 [references/RUBRIC_MAP.md](references/RUBRIC_MAP.md)；
**本轴核心文档**是 [references/DETERMINISM.md](references/DETERMINISM.md)。

> **资源形态**（题面 Runtime contract：*at most 50 UTF-8 text files, 500KB each and 2MB total,
> no symlinks*）：本包**只含 UTF-8 文本资源**（`.md/.py/.json/.txt/.csv/.yaml/.yml`）。
> `.pdf`/`.png`/`.pptx` 一律由脚本运行时生成；包内无本机绝对路径、无 `__pycache__`、无符号链接。

## 一、v7 的核心资产：确定性探针

```bash
$SKILL_DIR=/skills/weekly-skill   # 或本包实际目录；所有脚本自定位，cwd 任意

python "$SKILL_DIR/scripts/determinism.py" \
  --case "$SKILL_DIR/examples" \
  --out-root /tmp/det --report /tmp/det/determinism_report.json --runs 5
```

一次调用做四件事：

1. **跨进程**：N 次 run 各起一个新 `subprocess`（被调用入口是沙箱内技能副本，包内目录只读）；
2. **跨 cwd / 跨 `--out` 形态**：cwd 在"空临时目录"与"技能根副本"之间轮转，
   `--out` 在"绝对路径"与"`../outN` 相对路径"之间轮转，且都解析到同一个绝对输出目录；
3. **跨 `PYTHONHASHSEED`**：0/1/2/4/8…，排除哈希随机化影响；
4. **逐产物 sha256 + 稳定化**：给出三个**互不等价**的结论 ——
   `identical`（raw 字节）/ `content_identical`（剔除记录性时间戳）/ `normalized_archive_identical`
   （把 zip 容器重写成固定时间戳后 raw 也相同），外加 `volatile_fields[]`（逐字段为什么不稳定、怎么稳定化）
   与 `path_leak_scan`（产物里有没有本机绝对路径）。

本机 5 次实测摘要（完整表见 `references/DETERMINISM.md`）：

| 结论 | 实测 |
|-|-|
| raw 字节 5 次全同 | **否** —— 5 个文件不同：`editable_deck.pptx`、`result.json`、`self_check.json`、`talk_plan.json`、`previews/preview_manifest.json` |
| 内容投影 5 次全同 | **是** —— 稳定化后 21 个产物、产物树整体哈希 5 次同一个值 |
| 归一化归档 5 次全同 | **是** —— 5 次同一个 raw sha256 |
| 路径泄漏 | **0 命中** |
| 各 run 退出码 / `result.json` 顶层键数 | 全部 `0` / 全部 `20` |

**为什么 raw 会不同**：`python-pptx` 用 `zipfile.ZipFile(...).writestr()` 写 OOXML 包，
CPython 在 `date_time` 早于 1980 时填入当前本地时间（python-pptx 的
`opc/serialized.py` 只传 `compression`）⇒ 整包 sha 每次都变，但
**87 个 zip 成员解压后字节完全相同**。这条不是猜测，是 `per_file_sha256` 的
`stable_method = "zip-payload(no core.xml)"` 与 `zip_metadata_only_files` 两处证据。

## 二、运行方法

```bash
# 0) 示例专用：先生成运行时二进制输入（正式案例不需要）
python "$SKILL_DIR/scripts/make_synthetic_inputs.py"

# 1) 最小调用（示例案例 → 输出目录）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out "$OUT"

# 2) 平台运行期形态（等价于 /input、/app/output）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output

# 3) 显式材料目录 / 模板 / 跳过逐页缩略图
python "$SKILL_DIR/scripts/main.py" --case case.json --out out --materials ./materials \
       --template ./template.pptx --skip-previews

# 4) 独立复核（全部退出码 0 = 通过）
python "$SKILL_DIR/scripts/validate_result.py" "$OUT/result.json"
python "$SKILL_DIR/scripts/check_contract.py"  "$OUT/result.json"
python "$SKILL_DIR/scripts/evidence_audit.py"  "$OUT/result.json"
python "$SKILL_DIR/scripts/verify_deck.py" "$OUT/editable_deck.pptx" \
       --expect-pages <N> --plan "$OUT/talk_plan.json"
python "$SKILL_DIR/scripts/selftest.py" "$OUT" --package-check "$SKILL_DIR"

# 5) ★ 确定性复核
python "$SKILL_DIR/scripts/determinism.py" --case "$OUT/../case" --out-root /tmp/det --runs 5
```

退出码（**未变**）：`main.py` → `0` 已产出通过 validate+contract 的 `result.json`、
`1` 没有可用的契约结果、`2` 参数用法错误；`determinism.py` → `0` 判据全过、
`1` 真实不一致或某 run 失败、`2` 参数用法错误。

## 三、输入输出

**输入**：`case.json`（`case_id`/`report_goal`/`audience`/`duration_min`/`slide_count`/
`report_type`/`materials`/`template`·`start_deck`/`figure_files`/`output_contract`）+
`task.md` + 材料目录。脚本**实际读取文件**；材料目录缺省为 `<case 目录>/materials`。

**输出**（契约见 [references/OUTPUT_CONTRACT.md](references/OUTPUT_CONTRACT.md)）：

```
result.json          # 唯一评分产物：契约字段 + status/sources/uncertainty/change_records/
                     #   environment + audit{plan_gates,evidence,deck,gates} + contract{...}
talk_plan.json  plan_gates.json  evidence_map.json  evidence_audit.json  deck_audit.json
editable_deck.pptx   previews/{cover_preview,slide_NNN,preview_grid}.png  previews/preview_manifest.json
self_check.json      # validate + contract + P/G 门 + determinism 探针（plan/evidence_map 投影 sha）
```

`result.json` 里的路径一律**可移植**（写盘时把本机绝对路径改写成相对案例目录的形式；
POSIX 运行期路径原样保留）—— 这也是 `path_leak_scan` 能拿到 0 命中的原因。

## 四、依赖

| 依赖 | 用途 | 缺失时 |
|-|-|-|
| Python ≥ 3.8（本机 3.13.9） | 解释器（`determinism.py` 只用标准库） | — |
| python-pptx 1.0.2（验证） | 可编辑 `.pptx` | 跳过 deck，`status=partial`，其余产物照常，命令仍返回 0 |
| Pillow 12.x（验证） | PNG 预览（python-pptx 亦依赖它） | 跳过预览；**python-pptx 连带不可用**（见 v9 轴的 `references/DEGRADE-MATRIX.md`） |
| pypdf 6.x（可选） | PDF 文本抽取 | PDF 记 `parsed=false` 并降级 `partial` |

无网络依赖、无 cwd 依赖、不调用 LibreOffice/PowerPoint。

## 五、核心流程

CP1 输入契约（读 case/task/材料/模板 + 环境预检）→ CP2 计划门（`scaffold_plan` → `validate_plan` P1–P8）
→ CP3 生成门（`deck_builder` → `verify_deck`）→ CP4 渲染门（`render` PIL 模拟预览）
→ CP5 审计收口门（`evidence_audit` → `finalize_result` 组装 result.json + self_check）。

决策规则 D1–D17、失败模式 F1–F26、质量门 G1–G10 分别见 `SKILL.md` §8、
[references/failure-modes.md](references/failure-modes.md)、
[references/quality-gates.md](references/quality-gates.md)。

## 六、限制与边界

- 不负责论文精读成稿、写作成稿与科研绘图素材生产（相邻课题承担）；
- PDF 无解析器时按「未解析」降级，相关证据弱化但不编造；
- 预览为 PIL 模拟渲染（本机无 LibreOffice），正式视觉效果以 `.pptx` 打开为准；
- **不承诺"raw 字节级相同"**：`.pptx` 的 zip 容器成员时间戳由 CPython/zipfile 决定，
  本包给的是等价物（内容投影 + 归一化归档），并把差异逐字段登记；
- 确定性结论**只在同机同版本实测过**：跨机器时 `environment` 与字体探测结果必然不同（设计内行为）。

## 七、维护与更新

- 改行为：`templates/talk_config.json`（页权重/顺序/问答模板/deck_rules）、
  `assets/plan.schema.json`（计划门条款）—— 改配置即改行为；
- 改规则文字：`references/*.md`；
- **回归自测**：先跑 [TEST.md](TEST.md) 的 T1–T12（含六条降级/失败分支），
  再跑 T13 确定性探针；判据是"差异文件清单与 `references/DETERMINISM.md` §2 完全一致"，
  多出任何一个文件都必须解释到源码行为；
- 提交前：`selftest.py <out> --package-check "$SKILL_DIR"` 全 ✓，包内无 `__pycache__`、无二进制残留。

## 八、GitHub

见 `GITHUB_URL.txt`（第一行仓库链接）。
