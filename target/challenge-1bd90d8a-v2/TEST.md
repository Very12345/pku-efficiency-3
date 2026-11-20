# TEST.md — 本地实测记录（v2 加强包，2026-11-21 02:0x +08）

> 本文件记录 v2 包在本机的真实执行结果，供复核与复跑。机器：Windows；Python 3.13.9
> （命令 `python`）；Pillow 12.3.0。全部命令在技能根目录
> `work/efficiency-3/target/challenge-1bd90d8a-v2/` 下执行（脚本自定位，不依赖 cwd）。
> 冒烟输出目录使用 `D:/BuildTemp/smoke-challenge-1bd90d8a-v2`（不在包内）。

## T1 编译检查 —— 通过

```bash
python -m py_compile scripts/*.py        # 9 个脚本（chartkit/extract/figcheck/main/
                                         # mapcheck/spec_lint/svgtext/cjkfont/verify_rerun）
                                         # 全部 COMPILE OK，exit 0
```

## T2 冒烟：示例案例全链路（CP1→CP6）—— 通过

```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-challenge-1bd90d8a-v2
```

结果：`status=completed`，`exit 0`，`gates.all_pass=true`（G1–G8 全过），
`output_contract_applied=true`，图 fig-01（panel）+ fig-02（network）全部成功，failed=[]。

产出 11 个文件（sha256 前缀 / 字节数）：

```
data_manifest.json          a40ab7d3231b573e  28979
figcheck_report.json        1b5fc20b77df2439   8393
figure-fig-01.pdf           5c1163c450b5142e 343392
figure-fig-01.png           29ba17ff6530bc7c 281926
figure-fig-01.svg           78c0b6491d73ab9e  21303
figure-fig-02.pdf           32720dfbaca46a61  72656
figure-fig-02.png           46f274f9b99a9683 122579
figure-fig-02.svg           b8f76f6d1e21f26b  11931
mapcheck_report.json        7d0b9ee3890127cc  27581
result.json                 6d053755b1577c2b   9409
validation.json             09fe23ca671fe23a   2526
```

`result.json` 契约字段全部回显（output_contract 四形态：case_id/status/title/
sources/outputs/editable_source/rendered_preview/field_mapping/validation_report/
uncertainty/change_records/checkpoints/gates 等）。checkpoints 六项 CP1–CP6 全 ok。

## T3 spec 级样式内联覆盖（D17）—— 通过

示例 case.json 的 fig-01 声明 `"style":"nature"`（300 dpi、Nature 字号线宽），fig-02
未声明。实测 spec 级样式优先合并：

```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/t3-default          # 默认样式
python scripts/main.py --case examples/case.json --out D:/BuildTemp/t3-style-nature --style nature
# 结果（sha16）：
#   figure-fig-01.svg  78c0b6491d73ab9e == 78c0b6491d73ab9e   （一致：fig-01 spec 已声明 nature）
#   figure-fig-01.png  29ba17ff6530bc7c == 29ba17ff6530bc7c   （一致）
#   figure-fig-02.svg  b8f76f6d1e21f26b != 8e2c97d76d85fddb   （fig-02 无 spec 样式：默认 vs nature 预设）
#   figure-fig-02.png  46f274f9b99a9683 != c486b38aff0d03ad   （不同）
# ⇐ spec["style"] 命名预设生效（fig-01 两跑一致），CLI --style 作为基样式被再合并
#   （fig-02 nature 跑为 300 dpi / tick 17 / palette #E64B35，默认跑 150 dpi / tick 20）。
```

（spec 内联字段如 `title_size` 亦按 `resolve_figure_style()` 合并，最高优先级。）

## T4 确定性：同输入同参数双跑 —— SVG/PNG/manifest/validation 逐字节一致

```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/det-A
python scripts/main.py --case examples/case.json --out D:/BuildTemp/det-B
```

| 文件 | 双跑 sha256 | 结论 |
|---|---|---|
| figure-fig-01.svg | 78c0b649 / 78c0b649 | **一致**（SVG 无时间戳） |
| figure-fig-01.png | 29ba17ff / 29ba17ff | **一致** |
| figure-fig-02.svg | b8f76f6d / b8f76f6d | **一致** |
| figure-fig-02.png | 46f274f9 / 46f274f9 | **一致** |
| data_manifest.json | a40ab7d3 / a40ab7d3 | **一致** |
| validation.json | 09fe23ca / 09fe23ca | **一致** |
| figure-*.pdf | 不同 | 差异（Pillow 内嵌 PDF CreationDate 时间戳，如实记录） |
| result.json | 6d053755 / 不同 | 仅 `steps[].ts`、`change_records[].ts` 与自哈希不同（其余归一化一致） |
| figcheck/mapcheck_report | 不同 | 仅内嵌 `.dir` 绝对路径不同（其余一致） |

确定性再跑自动验证（D18）退出码 0：

```bash
python scripts/verify_rerun.py --case examples/case.json \
    --out D:/BuildTemp/smoke-challenge-1bd90d8a-v2 --rerun-dir D:/BuildTemp/rerun-tmp
# SUMMARY: DETERMINISTIC (identical=9 differ=0 missing=0) — exit 0
python scripts/verify_rerun.py --case examples/case.json \
    --out D:/BuildTemp/smoke-challenge-1bd90d8a-v2 --json
# {"all_pass": true, "summary": {"identical": 9, "differ": 0, "missing": 0}} — exit 0
```

## T5 双校验独立复核（build 后 verify 成对）—— 通过

```bash
python scripts/figcheck.py --dir D:/BuildTemp/smoke-challenge-1bd90d8a-v2 --case examples/case.json
# GATES: G1=OK G2=OK G3=OK G4=OK G5=OK G6=OK G7=OK G8=OK ; SUMMARY: ALL GATES PASS — exit 0

python scripts/mapcheck.py --dir D:/BuildTemp/smoke-challenge-1bd90d8a-v2 --case examples/case.json
# [PASS] fig-01: 79 elements, 0 orphans ; fig-02: 42 elements, 0 orphans
# SUMMARY: ALL PASS (121 checked / 0 mismatched / 0 unmatched) — exit 0
```

## T6 抽取与生成门独立 CLI —— 通过

```bash
python scripts/extract.py --case examples/case.json --out D:/BuildTemp/work
# {"tables": 1, "networks": 1, "uncertain": 0, ...} — exit 0（CP2）

python scripts/spec_lint.py --spec examples/case.json --case examples/case.json
# SUMMARY: VALID (0 errors / 0 warnings / 2 figures) — exit 0（CP3）
```

## T7 示例产物与本机真实运行一对一对拍 —— 通过

```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/gen-ex --style nature
# 与 examples/output/*.example.* 逐字节一致（除 PDF 内嵌日期/result.json 时间戳）：
#   figure-fig-01.svg       78c0b6491d73ab9e  == figure-fig-01.example.svg
#   figure-fig-01.png       29ba17ff6530bc7c  == figure-fig-01.example.png
#   figure-fig-02.svg       8e2c97d76d85fddb  == figure-fig-02.example.svg
#   figure-fig-02.png       c486b38aff0d03ad  == figure-fig-02.example.png
#   data_manifest.json      9cf8ba70f1d4603c  == data_manifest.example.json
#   validation.json         09fe23ca671fe23a  == validation.example.json
```

## T8 异常路径：缺文件/坏 case —— 通过（如实降级）

```bash
python scripts/main.py --case D:/BuildTemp/not-exist.json --out D:/BuildTemp/t8
# exit 1，result.json status=failed，uncertainty 记录"运行异常/材料缺失"，不臆造（D10/G8）
python scripts/main.py --case examples/case.json --out D:/BuildTemp/t8b --data D:/BuildTemp/empty.csv
# 数据为空 → 图 SpecError 记录 failed_figures，status=partial —— 不阻塞其他图（D9/D10）
```

## T9 修复记录（v2 制作期间本机实测发现并修复）

1. **spec 级样式被忽略**：`export_figure()` 只取 `ctx["style"]`，`spec["style"]` 命名预设
   与内联样式键（D17/SCHEMA 承诺）静默失效 → 新增 `resolve_figure_style()` 三层合并
   （基样式 → spec.style 预设 → spec 内联键），fig-01 nature 预设实测生效（T3）；
2. **verify_rerun `--json` stdout 被 main 日志污染**：重跑 main 的 `[main] ...` 过程日志
   先行为 stdout，`--json` 输出无法被 `json.load` 直接消费 → main 过程日志重定向到
   `rerun_dir/rerun_main.log`（`--json` 下静默），stdout 只留 JSON 报告（T4 实测）；
3. `__pycache__` 与空目录（examples/smoke）已清除，包内无编译缓存/符号链接。
4. 示例产物 examples/output 用 `--style nature` 重生成（旧产物为 historical build 版），
   与当前脚本逐字节对拍（T7）。

## 限制（如实声明）

- 渲染预览依赖 Pillow；无 Pillow 环境 SVG 仍产出、PNG/PDF 缺失并如实记录（SKILL D5）；
- PDF 与 result.json 含时间戳，不作为确定性承诺对象；确定性承诺 = SVG/PNG/data_manifest/
  validation（同输入逐字节一致，T4 实测）；
- examples/ 全部标注「示例，非正式案例」，与平台正式 3 案例无关；正式运行禁止照抄
  示例内容。