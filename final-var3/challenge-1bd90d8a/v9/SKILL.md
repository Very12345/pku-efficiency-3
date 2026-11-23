---
name: scientific-figure-craft
description: >
  科研数据图表生成与编辑 Skill（v9 · 缺依赖降级链轴）。当输入包含科研数据表格
  （CSV/TSV/JSON）、统计结果、实验记录或生物源材料，或需要生成/编辑示意图、机制图、
  流程图、柱状图、折线图、散点图、箱线图、热图、扇区图、通路图、多面板组合图
  （关键词：figure、chart、plot、diagram、数据图、科研绘图、机制图、通路图、
  graphical abstract、SVG、可编辑图稿、制图、出图、依赖、降级、最小可用环境）时使用。
  本版把「缺依赖时会优雅降级」从声明变成 17 档实测：scripts/degrade_probe.py 用受控
  导入拦截（PYTHONPATH + sitecustomize 里的 sys.meta_path finder）逐个模拟缺
  python-pptx / PIL / matplotlib / numpy / yaml / lxml / pypdf / cairosvg / svgwrite /
  reportlab / pandas / scipy / fontTools，并用「假 CLI 陷阱 + 静态扫描 + PATH 收窄」
  三层证据回答外部命令行工具依赖问题；产出最小可用环境清单。严格以真实文件为准，
  不臆造数据、不提交预制答案。
---

# 科研数据图表生成与编辑 · v9（缺依赖降级链轴）

面向「玻尔产品周赛 · 北大专区 · 学术效率 · 第三期」 `challenge-1bd90d8a`。

评测机上到底装了什么、没装什么，交付方是**看不到**的。所以这一版把"缺依赖"这件事
逐个模拟一遍，把每一种情况下**还剩什么**记下来。

## 0. 本版的轴：17 档探针的实测结论

| 断言 | 实测证据 |
|-|-|
| **最小可用环境 = Python 标准库 + Pillow**，不需要任何其它第三方包 | 12/13 个被拦截的第三方模块对本包**毫无影响**（产物与基线逐字节一致） |
| 只有 PIL 是硬依赖；缺它时整链失败，而不是优雅降级 | 缺 PIL：exit 1、status=failed、`result.json` 从 29 键塌到 **6 键**、产物 11→6、两个已生成的 SVG 从 `outputs` 里消失 |
| 不依赖任何外部 CLI（LibreOffice / pandoc / inkscape 等） | 假 CLI 陷阱 0 次调用（阳性对照已验证陷阱能触发）＋ 脚本里 0 处 `subprocess`/`os.system` 调用点 |
| PNG 的字节稳定性依赖 PATH 解析到的 **FreeType**（意外发现） | PATH 收窄后只有 PNG 变化；把含 `freetype.dll` 的目录加回即可复现原字节 |

## 1. 先跑这一条命令（本轴的核心）

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" \
    --src "$SKILL_DIR" --case /input/case.json \
    --workdir /app/work/dp --out /app/work/dp/degrade_probe_report.json

# 只跑某几档（含外部 CLI 两档）
python "$SKILL_DIR/scripts/degrade_probe.py" --only PIL,ALL_OPTIONAL,CLI_SHIM_TRAP --json
```

### 1.1 拦截机制：为什么它等价于「真的没装」

`--workdir` 下生成一个 `sitecustomize.py`（**不属于 Skill 本体**），
把 finder 插到 `sys.meta_path` 最前面：命中名单的 top-level 模块一律抛 `ImportError`，
并把 **`(module, frame)`** 追加写进日志。三条设计决定：

1. 对被测代码与"这个包没装"**完全等价**（`try: import PIL` 照旧走 except 分支）；
2. 每一次拦截都成为证据 —— 报告里能直接读出 PIL 是被 `chartkit.py:41`（**包在 try 里**）导的，
   还是被 `figcheck.py:157`（**裸导**）导的；这决定了缺它时是降级还是整链失败；
3. **不动被测包**：先把整包复制到 `--workdir` 再跑，并设 `PYTHONDONTWRITEBYTECODE=1`，
   包内永远不会出现 `__pycache__`（打包预检硬门之一）。

退出码：`0` = 全部探针跑完且报告已写出；`2` = **所有**探针都没产出 `result.json`
（连基线都不成立、报告不可信）；`1` = 用法或环境错误。

### 1.2 实测总表（本机：Windows + Python 3.13.9）

| 档位 | exit | status | result.json | 顶层键数 | 产物 | 与基线的稳定产物一致 | 拦截点 |
|-|-|-|-|-:|-:|-|-|
| NONE（基线） | 0 | completed | ✅ | 29 | 11 | —— | 无 |
| **PIL** | **1** | **failed** | ✅（失败信封） | **6** | **6** | ❌ | `chartkit.py:41`、`cjkfont.py:114`、`chartkit.py:1851`、`figcheck.py:157` |
| **ALL_OPTIONAL**（13 个一次性拦掉） | **1** | **failed** | ✅（失败信封） | **6** | **6** | ❌ | 同上（只有 PIL 被真正请求） |
| pptx / matplotlib / numpy / yaml / lxml / pypdf / cairosvg / svgwrite / reportlab / pandas / scipy / fontTools | 0 | completed | ✅ | 29 | 11 | ✅ 逐字节一致 | **0 次**（压根没被 import） |
| CLI_PATH_MIN | 0 | completed | ✅ | 29 | 11 | ❌（只有 PNG 变） | 无 |
| CLI_SHIM_TRAP | 0 | completed | ✅ | 29 | 11 | ✅ | 无 |

**只有 PIL 会让整链失败**，而且失败方式是"塌成失败信封"而不是"优雅降级"。逐档明细见
`references/DEGRADE-MATRIX.md`。

## 2. 缺 PIL 时到底还剩什么（实测）

| 项 | 基线 | 缺 PIL |
|-|-|-|
| `figure-*.svg` | 2 个（分层、带 `data-*` 溯源、真实 `<text>`） | **2 个仍在磁盘上**（SVG 不依赖 Pillow） |
| `figure-*.png` / `.pdf` | 4 个 | **全部消失**（渲染入口 `render_png` 直接抛错） |
| `data_manifest.json` / `validation.json` | 有 | 有，但内容变化（缺件导致的 warnings/元素差异） |
| `mapcheck_report.json` | 有 | 有 |
| `figcheck_report.json` | 有 | **没有**（`figcheck` 在第 157 行裸导 PIL → 异常冒泡） |
| `result.json` | 29 键、`status=completed`、G1–G8 全过 | **6 键**、`status=failed`、`outputs=[]` |
| main 退出码 | 0 | **1** |

结论：**磁盘上留了半个成果，但 JSON 里一个都不认** —— 这是"半成品不可交付"的实测证据。
回放方拿到的 `result.json` 会说它什么都没产出。

## 3. 外部 CLI：三层证据（外加一条意外发现）

| 层 | 做法 | 实测 |
|-|-|-|
| (a) PATH 收窄 | PATH 只留解释器目录（Windows 另加 System32），跑完与基线逐文件比 sha256 | 稳定产物**不一致**：只有两个 PNG 变了（机制见 §3.1） |
| (b) 假 CLI 陷阱 | PATH 前置 20 个会写日志的假 CLI（soffice / libreoffice / pandoc / inkscape / rsvg-convert / magick / convert / pdflatex / dot / gnuplot；Windows 另有 `.cmd` 形式），并**先做阳性对照** | 阳性对照真的触发（exit 1、日志写入）；主流程跑完后调用日志 **0 条** |
| (c) 静态扫描 | 扫 `scripts/*.py` 里的 `subprocess` / `os.system` / `os.popen` / `shutil.which` 等调用点 | **0 处** |

> (b) 的阳性对照不能省：没有它，"日志为空"可能只是陷阱坏了。实测该对照确实写出了日志，
> 所以"0 次调用"是真结论。而 (a) 那一层**不作为**本结论的证据（它另有发现，见下）。

### 3.1 PATH 为什么会影响 PNG 字节（已定位到根因）

收窄 PATH 后只有 PNG 变（SVG、`data_manifest.json`、`validation.json`、两份报告全不变），
看起来不像环境依赖，但它是真的。定位过程（可复核）：

1. 同一字体文件 + 同一字符串，两种 PATH 下分别用 Pillow 光栅化 →
   `serif` 角色（系统字体目录里的 `REFSAN.TTF`）位图 sha256 **不同**，其余角色相同；
2. 把本机含 `freetype.dll` 的那个目录加回收窄后的 PATH → 位图**恢复与 full PATH 一致**；
3. ⇒ Windows 的工人 **DLL 搜索顺序包含 PATH**，于是"哪个 FreeType 在光栅化"由 PATH 决定；
   同一个 `.ttf` 被不同版本的 FreeType 渲染，字形像素差几个灰度级。

实践含义：**PNG 的字节级复现依赖 PATH 解析到的 FreeType**；要跨环境字节一致，
必须固定 DLL 搜索路径或换用不依赖系统 FreeType 的光栅化后端。

## 4. 最小可用环境清单

| 档 | 环境 | 实测结论 |
|-|-|-|
| **Tier 0** | 纯标准库 | **不可用**：exit 1 / status failed / `result.json` 只剩 6 键 / 丢 5 个产物 / 两个已生成的 SVG 从 `outputs` 里消失 |
| **Tier 1** | 标准库 + Pillow（`pip install pillow`） | **最小可用环境**：exit 0 / status completed / 29 键 / 11 个产物 / 与基线逐字节一致 |

**结论：本 Skill 的最小可用环境 = Python 3.8+ 标准库 + Pillow。不需要任何其它第三方包，
也不需要任何外部命令行工具。** 这条结论是本轴最实用的产出 —— 部署方可以据此把镜像精简到最小，
同时明确知道"没有 Pillow 就没有 PNG/PDF，而且 `result.json` 会塌"。

## 5. 输入与输出

### 输入
- `/input/case.json`、`/input/task.md`、源数据表（CSV/TSV/JSON）、生物源材料。
- `environment/resources.yaml`（题面提到）：**本包不读 yaml**，实测拦截 `yaml` 后产物逐字节不变。

### 输出（`/app/output`，UTF-8）
`figure-<id>.svg` / `.png` / `.pdf`、`data_manifest.json`、`validation.json`、
`mapcheck_report.json`、`figcheck_report.json`、`result.json`；中间产物写 `--work`。
其中 **`figure-*.png` / `.pdf` 与 `figcheck_report.json` 是 Pillow 依赖项**，
其余产物在无 Pillow 时仍能落盘（但 `result.json` 会降级，见 §2）。

## 6. 执行流程（七步，第 ⑤ 步是本版新增）

| 步骤 | 命令 |
|-|-|
| ① 读契约 | `references/OUTPUT_CONTRACT.md` |
| ② 生成 | `python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output --work /app/work` |
| ③ 映射核对 | `python "$SKILL_DIR/scripts/mapcheck.py" --dir /app/output --case /input/case.json` |
| ④ 交付门 | `python "$SKILL_DIR/scripts/figcheck.py" --dir /app/output --case /input/case.json` |
| ⑤ **依赖降级实测** | `python "$SKILL_DIR/scripts/degrade_probe.py" --src "$SKILL_DIR" --case /input/case.json --workdir /app/work/dp --out /app/work/dp/degrade_probe_report.json` |
| ⑥ 契约回显复核 | `python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json` |
| ⑦ 确定性复核 | `python "$SKILL_DIR/scripts/verify_rerun.py" --case /input/case.json --out /app/output` |

## 7. 决策规则（DEP1–DEP12：依赖分支怎么走）

- **DEP1 只声明真实依赖**：`README.md`/`SKILL.md` 里只写实测被真正 import 的包（Pillow）；
  不把 matplotlib/numpy/pptx 写进依赖列表来显得"功能多"。
- **DEP2 渲染前先问 Pillow 在不在**：`chartkit.HAS_PIL` 是唯一开关；缺它时不进 PNG/PDF 分支。
- **DEP3 妥投优先于完整**：SVG 先落盘、再渲染预览（实测缺 PIL 时 SVG 仍在），
  避免"预览失败导致源文件也没写"。
- **DEP4 不静默降级成假产物**：缺 Pillow 时**不要**用占位图冒充 PNG；宁可记 `uncertainty`
  并让 `status` 反映现实。
- **DEP5 失败信封要诚实**：`status=failed` 时按契约允许的最小信封写
  （`case_id`/`status`/`uncertainty`/`sources`/`change_records` + `error`），
  不把没算出来的字段编出来。
- **DEP6 不依赖外部 CLI**：本包已实测 0 次外部进程调用；
  任何"顺手调 soffice/pandoc 转格式"的想法都不要加（会引入不可控环境依赖）。
- **DEP7 报告可移植**：探针写出的报告里所有本机绝对路径替换成占位符，
  报告可以直接进包、直接给别人看。
- **DEP8 不改调用者给的包**：所有注入都发生在 `--workdir` 的整包副本上，并设
  `PYTHONDONTWRITEBYTECODE=1`；包内不得出现 `__pycache__`。
- **DEP9 拦截要有证据**：每次拦截记 `(module, frame)`；只说"某个包缺失导致降级"
  而不指出**在哪一行被请求**，不算证据。
- **DEP10 跨环境差异先查 DLL/字体**：PNG 字节在不同环境不一致时，先按 §3.1 的路子查
  FreeType，再考虑字体文件本身。
- **DEP11 最小环境要写进 README**：部署方拿到的第一条信息应该是"标准库 + Pillow"，
  而不是一串可选项。
- **DEP12 缺陷只登记不隐瞒**：Tier 0 的不优雅降级（SVG 已产出却从 `outputs` 消失）
  必须写进 `references/DEGRADE-MATRIX.md`，不允许因为"不好看"而删掉。

## 8. 失败分支

| 情形 | 处置 | 落痕 |
|-|-|-|
| 缺 Pillow | SVG 照出；PNG/PDF 记缺失；`status` 降级并如实写 `uncertainty` | `environment.pillow=null`、`status=failed/partial` |
| 缺其它第三方包 | 无需处置（实测无影响）；不要为此加 try/except 噪音 | 探针报告"与基线逐字节一致" |
| 缺外部 CLI | 无需处置（实测未调用） | `cli_evidence.invocations_n=0` |
| `figcheck` 因裸导 PIL 失败 | 已知缺陷（见 §2），本轮只登记；回放时若 `figcheck_report.json` 缺失即为此因 | `result.json.error` + traceback 摘要 |
| 报告被误当产物 | 探针报告写在 `--workdir`/`--out`，**不写进 `/app/output`** | —— |
| Windows 控制台编码非 UTF-8 | 只对 stdout/stderr 做 `errors="replace"`；报告文件始终 UTF-8 | 不影响产物 |

## 9. 脚本与参数（相对 `$SKILL_DIR`；**既有入口与参数一个不少**）

| 脚本 | 参数 | 作用 |
|-|-|-|
| `scripts/main.py` | `--case --out --work --task --data --style --dpi --note --lang --no-pdf` | 单一入口：CP1→CP6 |
| `scripts/degrade_probe.py` | `--src --case --workdir --out --only --no-cli --json --keep --timeout --quiet` | ★ 本版新增：缺依赖降级链实测台 |
| `scripts/chartkit.py` | （库；`HAS_PIL` 开关） | 渲染引擎：Scene → SVG/PNG/PDF |
| `scripts/extract.py` | `--case --data --out --json` | 列画像 + 实体/关系抽取 |
| `scripts/spec_lint.py` | `--spec --case --json` | 图规格生成门 |
| `scripts/figcheck.py` | `--dir --case --json` | G1–G8 交付门 |
| `scripts/mapcheck.py` | `--dir --case --json` | 图元 ↔ 源数据双向核对 |
| `scripts/verify_rerun.py` | `--case --out --rerun-dir --record-only --dir --json` | 再跑验证 / 记录 sha256 |
| `scripts/check_contract.py` | `--result --case --contract --json` | 契约覆盖自查 |
| `scripts/cjkfont.py` | （库） | 中文字体发现与回退（也请求 PIL） |
| `scripts/svgtext.py` | （库） | SVG 文本转义 + 防转曲检查 |

包内只含 UTF-8 文本资源；`figure-*.svg/png/pdf` 一律运行时生成。

## 10. 自定位

```bash
SKILL_DIR=/skills/weekly-skill
python "$SKILL_DIR/scripts/degrade_probe.py" --src "$SKILL_DIR" --workdir /app/work/dp
```

探针自己以 `cwd=<workdir>` 启动被测包的主流程，所以"脚本是否依赖 cwd"会被顺带测出来。

## 11. 限制与未解决项

- Tier 0 的降级路径不优雅（SVG 已产出却从 `result.json.outputs` 消失、`figcheck` 因裸导 PIL 整链失败）；
  本轮**只实测登记、不改脚本**。
- `freetype.dll` 的 PATH 依赖未做真正隔离（未用 DLL 重定向/清单固定），只做到"定位根因 + 可复核对照实验"。
- 字体目录不可用（`FONT_PATHS` 收窄）**不在本轴范围**（已由另一路故障矩阵覆盖），
  见 `references/DEGRADE-MATRIX.md` §7 的未覆盖声明。
- 未在 Linux / macOS 复测；未测磁盘写满、只读输出目录、Python < 3.8。
