# scientific-figure-craft · v8（契约四形态 × 边界值矩阵轴）

科研数据图表生成与编辑 Skill。输入科研数据表或生物源材料，输出**可编辑的分层矢量源
（SVG）+ 预览（PNG/PDF）+ 图元到源数据的双向映射 + 结构化结果 `result.json`**。

本版在完整链路之上只强化一件事：**把「契约四种容器形态都兼容」变成 38 行实测矩阵**
（`scripts/contract_matrix.py`），并把「哪些情况会一路绿灯但有缺口」逐行点名。

## 1. 依赖

| 依赖 | 必需 | 说明 |
|-|-|-|
| Python 3.8+ | ✅ | 只用标准库 |
| Pillow（`pip install pillow`） | ✅（渲染 PNG/PDF） | 缺它时 SVG 仍产出，PNG/PDF 与 `figcheck_report.json` 缺失 |
| matplotlib / numpy / pandas / python-pptx / yaml / lxml | ❌ | 不需要 |
| LibreOffice / pandoc / inkscape | ❌ | 不调用 |
| 网络 | ❌ | 运行期不访问网络（`environment.no_network = true`） |

中文字体由 `scripts/cjkfont.py` 运行时扫描系统字体目录（`FONT_PATHS` 可追加候选目录）。

## 2. 安装

把本目录整体放到任意位置（平台安装到 `/skills/weekly-skill`）；无需编译或安装步骤。
所有命令用 `$SKILL_DIR` 自定位，**任意 cwd 均可运行**。

## 3. 最小调用

```bash
SKILL_DIR=/skills/weekly-skill

# ① 生成
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output --work /app/work

# ② 契约字段回显（exit 1 = 有缺口）
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json

# ③ 交付门 G1–G8（其中 G2 = 契约回显门）
python "$SKILL_DIR/scripts/figcheck.py" --dir /app/output --case /input/case.json

# ④ ★ 本版新增：契约四形态 × 边界值矩阵（exit 2 = 存在静默通过）
python "$SKILL_DIR/scripts/contract_matrix.py" --case /input/case.json \
    --workspace /app/work/cm --out /app/work/cm/contract_matrix_report.json
```

## 4. 参数总览

| 脚本 | 参数 |
|-|-|
| `main.py` | `--case --out --work --task --data --style --dpi --note --lang --no-pdf` |
| `contract_matrix.py` | `--case --workspace --out --only --json --keep --timeout --no-cross --quiet` |
| `extract.py` | `--case --data --out --json` |
| `spec_lint.py` | `--spec --case --json` |
| `figcheck.py` | `--dir --case --json` |
| `mapcheck.py` | `--dir --case --json` |
| `verify_rerun.py` | `--case --out --rerun-dir --record-only --dir --json` |
| `check_contract.py` | `--result --case --contract --json` |

退出码：`main.py` 0=completed / 2=partial / 1=failed；`spec_lint.py` 2=有 error；
`figcheck.py`/`mapcheck.py` 1=有失败项；`check_contract.py` 1=有缺口、2=用法错误；
`contract_matrix.py` 0=无静默通过 / **2=存在静默通过** / 1=用法或环境错误。

## 5. 输出

`/app/output`：`figure-<id>.svg|.png|.pdf`、`data_manifest.json`、`validation.json`、
`mapcheck_report.json`、`figcheck_report.json`、`result.json`；中间产物写 `--work`。
契约字段、类型与 G1–G8 硬门：`references/OUTPUT_CONTRACT.md`（字段块逐字保留）。

## 6. 契约矩阵结论（本版的实质产出）

| 结论 | 实测数字 |
|-|-|
| 四形态与 22 个别名回显正确 | 14 行 `echo_complete`；A1 一次回显 22 个字段全绿 |
| 存在「一路绿灯但有缺口」的行 | **11/38 行** `silent_pass`，分两款：形态非法被静默降级（7）、`applied=true` 却零回显（4） |
| `output_contract_applied` **不能**当契约完整性用 | 7 行 `applied=true` 且零字段回显（B1、D5、D6、D8、D9、D10、D12） |
| 门是有效的（反向证据） | 5 行被 G2 / `check_contract` 抓住：A2–A5（内部瞬态键被 `pop`）+ B1（空字段名） |
| 主流程与校验器存在口径分歧 | 仅 B1 一行 `parser_disagreement=true` |

逐行表格、静默通过分型、未覆盖声明：`references/CONTRACT-MATRIX.md`。

**给回放方的硬规则**：判断契约是否满足，必须同时看
`check_contract` 的 `missing/null/contract_missing`、`figcheck` 的 G2、以及 `status` 是否被降级；
只看 `output_contract_applied` 或只看 main 退出码都会被上面的反例骗过去。

## 7. 限制

- 静默降级本轮**只登记、不改脚本**（改 `apply_output_contract` 会变更既有脚本语义）。
- 矩阵覆盖自造字段与别名集合；真实平台案例的具体契约字段未知。
- 未覆盖：字段取值的科学语义正确性、嵌套深度 > 2、CRLF/LF 差异、并发重入
  （见 `references/CONTRACT-MATRIX.md` §9）。
- 统计推断与实验设计不在范围内。

## 8. 维护

- 改契约 = 同时改 `references/OUTPUT_CONTRACT.md` 的 `REQUIRED-FIELDS` 块与
  `scripts/check_contract.py`（脚本直接解析该块）。
- 加矩阵行 = 往 `scripts/contract_matrix.py` 的 `ROWS` 里加一条，重跑后把实测结果写进
  `references/CONTRACT-MATRIX.md`（本文件要求「先跑后写」，不许编数）。
- 加期刊样式 = 往 `templates/journal_styles.json` 加预设键，不改代码。
