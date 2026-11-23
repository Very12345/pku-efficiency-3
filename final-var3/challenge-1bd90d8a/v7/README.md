# scientific-figure-craft · v7（字节级可复现轴）

科研数据图表生成与编辑 Skill。输入科研数据表或生物源材料，输出**可编辑的分层矢量源
（SVG）+ 预览（PNG/PDF）+ 图元到源数据的双向映射 + 结构化结果 `result.json`**。

本版在完整链路之上只强化一件事：**把「同输入同参数重复运行是否逐字节一样」变成一条可跑的命令
与一个四档阶梯**（`scripts/determinism.py`）。

## 1. 依赖

| 依赖 | 必需 | 说明 |
|-|-|-|
| Python 3.8+ | ✅ | 只用标准库（`json`/`csv`/`math`/`hashlib`/`xml` 手写 SVG） |
| Pillow（`pip install pillow`） | ✅（渲染 PNG/PDF 用） | 缺它时 SVG 仍可产出，PNG/PDF 与 `figcheck_report.json` 缺失，`result.json` 降级为失败信封 |
| matplotlib / numpy / pandas / python-pptx / yaml / lxml | ❌ | **不需要**（逐条实测见 `references/DEGRADE-MATRIX.md` 的口径，本包只依赖 Pillow） |
| LibreOffice / pandoc / inkscape | ❌ | **不调用**（假 CLI 陷阱实测 0 次调用 + 静态扫描 0 处调用点） |
| 网络 | ❌ | 运行期不访问网络（`environment.no_network = true`） |

无第三方字体文件：中文字体由 `scripts/cjkfont.py` 在运行时扫描系统字体目录（可用
`FONT_PATHS` 环境变量追加候选目录）；找不到 CJK 字体时 SVG 走字体族回退链、PNG 记 warn。

## 2. 安装

把本目录整体放到任意位置（平台安装到 `/skills/weekly-skill`），无需编译、无需安装步骤。
所有命令用 `$SKILL_DIR` 自定位，**任意 cwd 均可运行**（cwd 轮转本身也被 `determinism.py` 测过）。

## 3. 最小调用

```bash
SKILL_DIR=/skills/weekly-skill

# ① 生成（CP1–CP6：盘点 → 抽取 → 规格门 → 生成 → 双校验 → 契约落地）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output --work /app/work

# ② 契约回显自查（exit 1 = 有缺口）
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json

# ③ 交付门 G1–G8（exit 1 = 有失败项）
python "$SKILL_DIR/scripts/figcheck.py" --dir /app/output --case /input/case.json

# ④ ★ 本版新增：字节级可复现实测（exit 0/2/3/1 = 阶梯）
python "$SKILL_DIR/scripts/determinism.py" --case /input/case.json --runs 5 \
    --seeds 0,1,12345,7,99 --mode isolated \
    --workdir /app/work/det --out /app/work/det/determinism_report.json
```

## 4. 参数总览

| 脚本 | 参数 |
|-|-|
| `main.py` | `--case --out --work --task --data --style --dpi --note --lang --no-pdf` |
| `determinism.py` | `--case --runs --seeds --mode --workroot --out --main --json --keep --timeout --abs-policy --quiet` |
| `extract.py` | `--case --data --out --json` |
| `spec_lint.py` | `--spec --case --json` |
| `figcheck.py` | `--dir --case --json` |
| `mapcheck.py` | `--dir --case --json` |
| `verify_rerun.py` | `--case --out --rerun-dir --record-only --dir --json` |
| `check_contract.py` | `--result --case --contract --json` |

退出码约定：`main.py` 0=completed / 2=partial / 1=failed；`spec_lint.py` 2=有 error；
`figcheck.py`/`mapcheck.py` 1=有失败项；`check_contract.py` 1=有缺口、2=用法错误；
`determinism.py` 见下；`determinism.py` 的阶梯 0>2>3>1 语义写在 `references/DETERMINISM.md` §3。

## 5. 输出

`/app/output`：`figure-<id>.svg`（分层可编辑源）、`figure-<id>.png`、`figure-<id>.pdf`、
`data_manifest.json`、`validation.json`、`mapcheck_report.json`、`figcheck_report.json`、
`result.json`。中间产物（`extract.json`、`spec_lint.json`）写在 `--work`。

契约字段、类型与 G1–G8 硬门：`references/OUTPUT_CONTRACT.md`（字段块逐字保留）。

## 6. 可复现性结论（本版的实质产出）

| 结论 | 实测数字 |
|-|-|
| 可编辑源与主要数据产物**逐字节可复现** | 6/11 个产物在 5 次重复（跨进程/跨 cwd/跨 `PYTHONHASHSEED`）中 sha256 全同 |
| `result.json` 与两份报告的差异**100% 可解释** | 阶梯 exit 2；`volatile_classes = {run_root_path:2, self_reference_hash:2, timestamp:2}`，无 `unknown` |
| 「输出目录绝对路径」是两份报告的唯一不稳定来源 | 换成 `--mode inplace` 后这一类整体消失，逐字节相同文件数 6/11 → 8/11 |
| PDF 的唯一差异来源是 Pillow 写入的 `/CreationDate`、`/ModDate` | 两次运行首个差异偏移固定在文件尾部，`date_only_diff = True` |

完整实测表、逐字段说明、稳定化配方：`references/DETERMINISM.md`。

## 7. 限制

- 统计推断（显著性计算/拟合/检验）不在范围内：只转述材料给定的 p 值与检验方法。
- 机制图自动布局是启发式（按 group 分层）；复杂图请在 spec 里手给节点 `x/y`。
- PDF 预览是光栅预览嵌入 PDF（供检查用）；投稿用的矢量可编辑源以 SVG 为准。
- 阶梯 0 需要冻结时钟；本包故意保留 `change_records` 时间戳，因此默认落在阶梯 2。
- 测试只在 Windows + Python 3.13.9 上做过；跨平台差异的处置写在
  `references/DETERMINISM.md` §9 与 `references/failure-modes.md`。

## 8. 维护

- 改契约 = 同时改 `references/OUTPUT_CONTRACT.md` 的 `REQUIRED-FIELDS` 块与
  `scripts/check_contract.py`（脚本直接解析该块）。
- 加期刊样式 = 往 `templates/journal_styles.json` 加一个预设键，不改代码。
- 加/改确定性规则 = 改 `scripts/determinism.py` 的 `normalize_bytes()`，
  并在 `references/DETERMINISM.md` §4 的 N1–N4 表里补一行（实测后补）。
