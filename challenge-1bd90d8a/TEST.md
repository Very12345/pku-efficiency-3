# TEST.md — 真机实测记录（合规重打包版）

> 本文件记录**本包当前版本**的真实执行结果，供评审与复核者复跑对拍。
> 测试机：Windows；Python 3.13.9（命令 `python`）；Pillow 12.3.0；无网络。
> 所有命令都在**临时目录里的包副本**上执行，且**故意让 cwd 不等于技能根目录**
> （验证自定位）。文中 `<TMP>` 代表本次使用的临时目录（每台机器不同，故不写死）。
>
> 复跑方式：把本包复制到任意临时目录，设 `SKILL_DIR=<该副本绝对路径>`，
> 然后逐条执行 §T1–§T7 的命令即可。

## T1 编译检查 —— 通过

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py
# 10/10 脚本 COMPILE OK（chartkit / check_contract / cjkfont / extract / figcheck /
#                        main / mapcheck / spec_lint / svgtext / verify_rerun）
```

## T2 冒烟：示例案例全链路 CP1→CP6 —— 通过（exit 0）

```bash
cd <TMP>/cwd-not-skill-root          # 故意不是技能根目录
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
       --out <TMP>/out --style nature
```

```
[main] case_id=example-science-figure-01 status=completed figures=['fig-01', 'fig-02'] failed=[]
[main] outputs -> <TMP>/out
  - figure-fig-01.svg (editable_svg)   - figure-fig-01.png (png_preview)   - figure-fig-01.pdf (pdf_preview)
  - figure-fig-02.svg (editable_svg)   - figure-fig-02.png (png_preview)   - figure-fig-02.pdf (pdf_preview)
[main] gates: G1=OK G2=OK G3=OK G4=OK G5=OK G6=OK G7=OK G8=OK all_pass=OK
exit = 0
```

## T3 产物清单与 sha256（第一次运行）

```
data_manifest.json         9cf8ba70f1d4603c    28977
figcheck_report.json       405f5e155f49b0dd     8388   ← 含运行目录（每次不同），余者一致
figure-fig-01.pdf          06269c45b573e54c   343392   ← 含内嵌时间戳（每次不同），尺寸稳定
figure-fig-01.png          29ba17ff6530bc7c   281926
figure-fig-01.svg          78c0b6491d73ab9e    21303
figure-fig-02.pdf          01e6e0a079183824   188923
figure-fig-02.png          c486b38aff0d03ad   289132
figure-fig-02.svg          8e2c97d76d85fddb    11931
mapcheck_report.json       268185a8d9c5c6f0    27575   ← 同上（含运行目录）
result.json                bb7608be37334b07     9725   ← 含时间戳与自哈希（每次不同）
validation.json            09fe23ca671fe23a     2526
```

## T4 契约覆盖自查 —— PASS

```bash
python "$SKILL_DIR/scripts/check_contract.py" --result <TMP>/out/result.json \
       --case "$SKILL_DIR/examples/case.json"
```

```
[check_contract] status=completed 顶层字段=29
   [OK] case_id status outputs editable_sources renders sources figure_checks uncertainty
        change_records environment steps spec_lint checkpoints gates artifacts_sha256
        figcheck_report mapcheck_report output_contract_applied
[check_contract] case.json output_contract 回显：
   [OK] case_id status title sources outputs editable_source rendered_preview
        field_mapping validation_report uncertainty change_records checkpoints gates
[check_contract] SUMMARY: PASS (required=18 missing=0 null=0 contract_missing=0)
exit = 0
```

> 即：`result.json` 顶层覆盖 `references/OUTPUT_CONTRACT.md` §0 的全部 18 个必需字段，
> 且 `case.json` 声明的 13 个契约字段全部回显、无一为 null。

## T5 双校验 + 确定性（独立 CLI，全部 exit 0）

```bash
python "$SKILL_DIR/scripts/figcheck.py"    --dir <TMP>/out --case "$SKILL_DIR/examples/case.json"
# GATES: G1=OK G2=OK G3=OK G4=OK G5=OK G6=OK G7=OK G8=OK ; SUMMARY: ALL GATES PASS

python "$SKILL_DIR/scripts/mapcheck.py"    --dir <TMP>/out --case "$SKILL_DIR/examples/case.json"
# [PASS] fig-01: 79 elements, 0 orphans ; [PASS] fig-02: 42 elements, 0 orphans
# SUMMARY: ALL PASS (121 checked / 0 mismatched / 0 unmatched)

python "$SKILL_DIR/scripts/verify_rerun.py" --case "$SKILL_DIR/examples/case.json" --out <TMP>/out
# SUMMARY: DETERMINISTIC (identical=9 differ=0 missing=0)
```

## T6 第二次运行 → 确定性逐字节对比 —— 6/6 一致

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
       --out <TMP>/out2 --style nature          # exit 0
```

| 文件 | 第一次 | 第二次 | 结论 |
|-|-|-|-|
| `figure-fig-01.svg` | 78c0b6491d73ab9e | 78c0b6491d73ab9e | **逐字节一致** |
| `figure-fig-01.png` | 29ba17ff6530bc7c | 29ba17ff6530bc7c | **逐字节一致** |
| `figure-fig-02.svg` | 8e2c97d76d85fddb | 8e2c97d76d85fddb | **逐字节一致** |
| `figure-fig-02.png` | c486b38aff0d03ad | c486b38aff0d03ad | **逐字节一致** |
| `data_manifest.json` | 9cf8ba70f1d4603c | 9cf8ba70f1d4603c | **逐字节一致** |
| `validation.json` | 09fe23ca671fe23a | 09fe23ca671fe23a | **逐字节一致** |

**如实记录的不一致项**：`figure-*.pdf`（Pillow 写入内嵌 CreationDate）、`result.json`
（`steps[].ts`/`change_records[].ts`/自哈希）、`figcheck_report.json` 与
`mapcheck_report.json`（顶层 `dir` 记录运行目录）。归一化后
`verify_rerun.py` 判定 `identical=9 differ=0`——确定性承诺的范围就是
**SVG / PNG / data_manifest / validation**。

## T7 归档示例 JSON 与现跑输出对比 —— 除声明的净化外全部一致

`examples/output/` 里的 5 个 JSON 是本包在示例案例上真实运行后归档的。把同一个
命令在临时副本上重跑一次，与归档件对比（归一化项：报告顶层 `dir`、时间戳、
PDF/result 自哈希、以及归档时改写的任务说明路径记录）：

| 归档文件 | 原始字节 | 归一化后 |
|-|-|-|
| `data_manifest.example.json` | **一致** | 一致 |
| `validation.example.json` | **一致** | 一致 |
| `mapcheck_report.example.json` | 差异（仅 `dir`） | 一致 |
| `figcheck_report.example.json` | 差异（仅 `dir`） | 一致 |
| `result.example.json` | 差异（`dir`/时间戳/自哈希/任务说明路径记录） | 一致 |

> 即归档的示例报告没有过期、也不是手写的：它们与当前脚本的输出同源同值。

## T8 异常路径（如实降级，不静默）—— 通过

| 场景 | 命令 | exit | 结果 |
|-|-|-|-|
| case.json 不存在 | `main.py --case <TMP>/nope.json --out <TMP>/negA` | **1** | `result.json.status=failed`，键为最小诚实信封 `case_id/status/error/uncertainty/sources/change_records`（traceback 摘要入 `uncertainty`） |
| 数据表只有表头 | `main.py … --data <TMP>/empty.csv --out <TMP>/negB` | **2** | `status=partial`；`fig-01` 因"源数据为空"记入 `failed_figures`，`fig-02`（network，依赖 entities.json）仍正常产出 |
| 失败信封的契约检查 | `check_contract.py --result <TMP>/negA/result.json` | **0** | 按最小信封判定 `required=5 missing=0`（不要求把没算出来的字段编出来） |
| 输出目录无 result.json | `figcheck.py --dir <TMP>/negC` | **1** | `SUMMARY: ISSUES FOUND`（G1 未过） |

## T8 合规自检（本次重打包的核心目的）

```bash
python <efficiency-3>/validate_pkg.py <包目录>
# [PASS] challenge-1bd90d8a  files=38   （0 条 FAIL）
```

```bash
# 盘符绝对路径与其它本机痕迹检查（正则用字符类/分组，避免本文档自身引入该字面量）
grep -rnE '[A-Za-z]:\\' <包目录>              # 无命中
grep -rnE '/(Users|home)/|[?][?]' <包目录>     # 无命中
```

- **文件数 38（上限 50）**；总字节 ≈ **0.375 MB（约 393 KB；文档微调会浮动几十字节）**
  （上限 2 MB）；最大单文件
  `scripts/chartkit.py` **83,245 B ≈ 81 KB**（上限 500 KB）。
- **扩展名**全部落在允许集 `.md/.py/.json/.txt`；包内**没有** `.pdf/.png/.svg/.pptx/.pyc`，
  `__pycache__/` 不存在，无符号链接。
- **无本机绝对路径**：示例 JSON 中的运行目录已净化为 `"."`、任务说明路径改写为
  `examples/task.md`；`scripts/cjkfont.py` 的字体候选目录改为运行时拼装
  （`windows_font_dirs()`），源码里不再出现盘符字面量。

> ⚠ 复跑提示：**直接在包内运行会生成 `scripts/__pycache__/`**（Python 的字节码缓存）。
> 本包的实测与验收一律在临时副本上进行；若在包内跑过，交付前请删掉
> `__pycache__/` 与 `*.pyc` 再打包（平台预检对文件形态有硬性要求）。

## 限制（如实声明）

- 渲染预览依赖 Pillow；无 Pillow 环境仍产出 SVG 与全部 JSON，PNG/PDF 缺失并记入
  `uncertainty`（不静默）。
- PDF 与 `result.json` 含时间戳，**不在确定性承诺范围内**；承诺范围 = SVG / PNG /
  data_manifest / validation。
- 本机字体环境（示例运行实测发现 `sans`/`sans_cjk`/`serif`/`mono` 各一）只影响 PNG 字形，
  不影响 SVG 可编辑源；换机器时 `environment.fonts` 会变，这是如实记录而非缺陷。
- `examples/` 全部标注「示例，非正式案例」，与平台正式 3 个案例无关；
  正式运行禁止照抄示例内容。
