# scientific-figure-craft · v9（缺依赖降级链轴）

科研数据图表生成与编辑 Skill。输入科研数据表或生物源材料，输出**可编辑的分层矢量源
（SVG）+ 预览（PNG/PDF）+ 图元到源数据的双向映射 + 结构化结果 `result.json`**。

本版在完整链路之上只强化一件事：**把「缺依赖时会优雅降级」变成 17 档实测 + 一份最小可用环境清单**
（`scripts/degrade_probe.py`）。

## 1. 依赖（逐条实测，不是自述）

| 依赖 | 必需 | 实测证据 |
|-|-|-|
| Python 3.8+ | ✅ | 只用标准库 |
| **Pillow**（`pip install pillow`） | ✅ | 拦掉 PIL：exit 1、`status=failed`、`result.json` 29→6 键、丢 5 个产物 |
| python-pptx | ❌ | 拦掉后产物**与基线逐字节一致**（0 次 import） |
| matplotlib / numpy / pandas / scipy | ❌ | 同上 |
| PyYAML（`yaml`） | ❌ | 同上（本包不读 `environment/resources.yaml`） |
| lxml / pypdf / cairosvg / svgwrite / reportlab / fontTools | ❌ | 同上 |
| LibreOffice / pandoc / inkscape / ImageMagick / gnuplot / dot / pdflatex | ❌ | 假 CLI 陷阱 0 次调用 + 脚本内 0 处 `subprocess`/`os.system` 调用点 |
| 网络 | ❌ | 运行期不访问网络（`environment.no_network = true`） |

**最小可用环境 = Python 3.8+ 标准库 + Pillow。** 完整实测见 `references/DEGRADE-MATRIX.md`。

## 2. 安装

把本目录整体放到任意位置（平台安装到 `/skills/weekly-skill`）。
```bash
pip install pillow        # 唯一需要装的第三方包
```
所有命令用 `$SKILL_DIR` 自定位，**任意 cwd 均可运行**。

## 3. 最小调用

```bash
SKILL_DIR=/skills/weekly-skill

# ① 生成
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output --work /app/work

# ② 契约字段回显
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json

# ③ 交付门 G1–G8
python "$SKILL_DIR/scripts/figcheck.py" --dir /app/output --case /input/case.json

# ④ ★ 本版新增：缺依赖降级链实测（17 档）
python "$SKILL_DIR/scripts/degrade_probe.py" --src "$SKILL_DIR" --case /input/case.json \
    --workdir /app/work/dp --out /app/work/dp/degrade_probe_report.json
```

## 4. 参数总览

| 脚本 | 参数 |
|-|-|
| `main.py` | `--case --out --work --task --data --style --dpi --note --lang --no-pdf` |
| `degrade_probe.py` | `--src --case --workdir --out --only --no-cli --json --keep --timeout --quiet` |
| `extract.py` | `--case --data --out --json` |
| `spec_lint.py` | `--spec --case --json` |
| `figcheck.py` | `--dir --case --json` |
| `mapcheck.py` | `--dir --case --json` |
| `verify_rerun.py` | `--case --out --rerun-dir --record-only --dir --json` |
| `check_contract.py` | `--result --case --contract --json` |

退出码：`main.py` 0=completed / 2=partial / 1=failed；`spec_lint.py` 2=有 error；
`figcheck.py`/`mapcheck.py` 1=有失败项；`check_contract.py` 1=有缺口、2=用法错误；
`degrade_probe.py` 0=跑完且报告已写出 / 2=所有档都没产出 `result.json` / 1=用法或环境错误。

## 5. 输出

`/app/output`：`figure-<id>.svg|.png|.pdf`、`data_manifest.json`、`validation.json`、
`mapcheck_report.json`、`figcheck_report.json`、`result.json`；中间产物写 `--work`。

**哪些产物依赖 Pillow（实测）**：`figure-*.png`、`figure-*.pdf`、`figcheck_report.json`；
`figure-*.svg`、`data_manifest.json`、`validation.json`、`mapcheck_report.json` 不需要 Pillow
即可落盘（但缺 Pillow 时 `result.json` 会降级为失败信封，`outputs` 为空）。

## 6. 降级链结论（本版的实质产出）

| 结论 | 实测数字 |
|-|-|
| 唯一硬依赖是 Pillow；其余 12 个第三方模块**一个都不需要** | 拦掉后产物与基线**逐字节一致**、拦截记录 0 次 |
| 缺 Pillow 的降级**不优雅** | exit 1 / `status=failed` / `result.json` 29→**6 键** / 产物 11→**6** / 两个已生成的 SVG 从 `outputs` 里消失 |
| 根因可定位到行 | 拦截证据：`chartkit.py:41`（在 `try` 里）、`cjkfont.py:114`、`chartkit.py:1851`、`figcheck.py:157`（**裸导** → 整链失败） |
| 不依赖外部 CLI | 假 CLI 陷阱 0 次调用（阳性对照已验证陷阱能触发）+ 静态扫描 0 处调用点 |
| PNG 字节依赖 PATH 解析到的 FreeType | 收窄 PATH 后只有 PNG 变；把含 `freetype.dll` 的目录加回即可复现原字节 |

逐档明细、最小可用环境清单、未覆盖声明：`references/DEGRADE-MATRIX.md`。

## 7. 限制

- 缺 Pillow 时的不优雅降级**只登记、不改脚本**（修它要动 `figcheck.py` 的导入方式与
  `main.py` 的异常边界，属于行为变更）。
- 环境条件是**模拟**的（受控导入拦截 / PATH 收窄 / 假 CLI），但对被测代码与"真的没装"等价，
  且每次拦截都有 `(module, frame)` 记录可查。
- 字体目录不可用（`FONT_PATHS` 收窄）不在本轴范围；未在 Linux / macOS 复测。
- 统计推断与实验设计不在范围内。

## 8. 维护

- 加探针 = 往 `scripts/degrade_probe.py` 的 `MODULE_PROBES` 或 `CLI_NAMES` 里加一条，
  重跑后把实测结果写进 `references/DEGRADE-MATRIX.md`（先跑后写，不许编数）。
- 改依赖 = 先跑一遍 `degrade_probe.py` 确认"是否真的被 import"，再改 README 的依赖表
  （DEP1：只声明实测被真正 import 的包）。
- 改契约 = 同时改 `references/OUTPUT_CONTRACT.md` 的 `REQUIRED-FIELDS` 块与 `scripts/check_contract.py`。
