# DEGRADE-MATRIX — 缺依赖降级链实测（v9 主轴）

本文件回答一个部署期问题，而且只回答它：

> 目标机**缺**某个库（或某个外部命令）时，本技能**还剩什么**？退出码是什么、
> `status` 变成什么、还写不写 `result.json`、产物少了哪几件、`uncertainty` 里有没有
> 痕迹、有没有"**静默降级**"？

读数来自包内可运行脚本 `scripts/degrade_probe.py`：**16 条探针**，每条都在**包外副本**
里用**受控导入拦截**（`sitecustomize.py` + `sys.meta_path`）或**净化 PATH** 制造缺失，
然后真跑主流程 / 子工具，记录**实测**形态。机器可读证据：`<out>/degrade-matrix.json`。

---

## 1. 注入方法与它为什么忠实

| 项 | 做法 | 为什么等价于"目标机没装" |
|-|-|-|
| 缺 Python 库 | scratch 副本里生成 `sitecustomize.py`：`sys.meta_path` 上插一个 `MetaPathFinder`，对指定**顶层模块名**抛 `ModuleNotFoundError`；用 `PYTHONPATH=<scratch fx>` 启动被测脚本（并清掉 `sys.modules` 里同族模块） | `import` 的可达性与"没装该库"完全一致；**不 patch 被测代码**，被测脚本的 CLI/退出码语义一字未改 |
| 缺外部命令（LibreOffice） | `PATH` 净化为"只有解释器所在目录"，子进程里 `shutil.which("soffice")` 为空 | 等价于"系统里没有这个命令"，且本机实测本来就未安装 LibreOffice |
| 只读原包 | 每条探针各自 `copytree` 到 `tempfile.mkdtemp()`，在副本里注入与运行；`--out` 指包内直接拒绝（exit 2） | 交付包不会被污染（无 `__pycache__`、无产物） |
| 不伪造 | 报告只记录子进程真实 `returncode`、真实 `result.json` 字段与真实产物文件；拿不到就记 `unavailable` | 每条读数都能被第三方用同一条命令推翻 |

---

## 2. 运行命令（cwd 不是技能根也能跑；产物一律在包外）

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"
RUN="<包外临时目录>"

python "$SKILL_DIR/scripts/degrade_probe.py" --list
python "$SKILL_DIR/scripts/degrade_probe.py" --skill-root "$SKILL_DIR" --out "$RUN/dg"
python "$SKILL_DIR/scripts/degrade_probe.py" --skill-root "$SKILL_DIR" --out "$RUN/dg" --json
python "$SKILL_DIR/scripts/degrade_probe.py" --skill-root "$SKILL_DIR" --out "$RUN/dg" --only G01,G03c,H01
```

- `--out` 在技能包内 ⇒ **拒绝**（exit 2）；
- 退出码：`0` = 每条探针都留下可解释的实测形态（含"缺依赖 ⇒ 如实失败"）；
  `1` = 有探针**静默**（出问题但退出码 0、fail/warn/`uncertainty` 全空）；`2` = 参数或环境错误；
- 每条探针自带 `--timeout`（默认 180 s），超时也作为一条可判定读数记录。

---

## 3. 逐项实测表（16 条探针，2026-11-23 本机；Python 3.13.9）

`status`/`artifacts` 来自 `result.json`；`sec` 是子进程墙钟。合计 **18.3 秒**跑完 16 条。

| id | 缺什么 | 跑什么 | exit | status | 产物还剩什么 | fail/warn | `uncertainty` 痕迹（实测原文摘要） | 档位 | 静默 |
|-|-|-|-|-|-|-|-|-|-|
| **G00** | （什么都不缺，对照组） | 主流程 schematic | 0 | success | figure:svg + preview:png + pdf:pdf | 0 / 0 | 常规两条（auto-layout；preview 非逐像素） | full | 否 |
| **G01** | `matplotlib` | 主流程 schematic | **1** | **failed** | **无** | 1 / 0 | `missing runtime dependency: render.matplotlib: ModuleNotFoundError('injected absence: matplotlib') (pip install matplotlib pillow numpy)` | **unavailable** | 否 |
| **G02** | `PIL`(Pillow) | 主流程 schematic | **1** | **failed** | **无** | 1 / 0 | `… render.matplotlib: ModuleNotFoundError('injected absence: PIL') …` | **unavailable** | 否 |
| **G03** | `numpy` | 主流程 schematic | **1** | **failed** | **无** | 1 / 0 | `… render.matplotlib: ModuleNotFoundError('injected absence: numpy') …` | **unavailable** | 否 |
| **G03b** | `numpy` | 主流程 chart(bar) | **1** | **failed** | **无** | 1 / 0 | 同 G03 | **unavailable** | 否 |
| **G03c** | `numpy` | 主流程 chart(heatmap+matrix) | **1** | **failed** | **无** | 1 / 0 | 同 G03 | **unavailable** | 否 |
| **G04** | `yaml`(PyYAML) | 主流程 schematic | 0 | success | 全套三件 | 0 / 0 | 无该库相关痕迹（运行路径上没有它） | full | 否 |
| **G05** | `pptx`(python-pptx) | 主流程 schematic | 0 | success | 全套三件 | 0 / 0 | 同上 | full | 否 |
| **G06** | `lxml` | 主流程 schematic | 0 | success | 全套三件 | 0 / 0 | 同上（lxml 只在题集执行器里被优先选用） | full | 否 |
| **G07** | `fitz`+`pypdf`+`PyPDF2` | 主流程（来源=真实 PDF 材料） | 0 | success | 全套三件 | 0 / 0 | 无缺库痕迹；**来源路径已解析**（夹具把 case 与 `sources/` 放同目录） | full | 否 |
| **G08** | `reportlab` | 主流程 schematic | 0 | success | 全套三件 | 0 / 0 | 同上（可选依赖，只在 `tool_versions` 里尽力探测） | full | 否 |
| **G09** | LibreOffice CLI | 主流程 schematic（PATH 净化） | 0 | success | 全套三件 | 0 / 0 | 同上（PDF 导出走 matplotlib，不经 LibreOffice） | full | 否 |
| **G10** | `yaml`+`pptx`+`lxml`+`reportlab`+`fitz`+`pypdf`+`PyPDF2` | 主流程 schematic | 0 | success | 全套三件 | 0 / 0 | 同上 —— **所有可选依赖全缺也只靠 matplotlib+Pillow 跑满** | full | 否 |
| **H01** | `fitz`+`pypdf`+`PyPDF2` | `pdftext.py`（真实 Flate PDF 夹具） | 0 | —（子工具） | `<stem>.txt` + `<stem>.extract.json` | — | **backend = `stdlib`**、pages = 1、**抽到 52 字** | **degraded-usable** | 否 |
| **H02** | `lxml` | `case_probe.py --only example-schematic-001` | 0 | —（子工具） | `case-report.json` | — | **xml_backend = `stdlib`**、1/1 conforms、deviating = `[]` | **degraded-usable** | 否 |
| **H03** | `reportlab` | 主流程 chart(bar) | 0 | success | 全套三件 | 0 / 0 | 无该库痕迹 | full | 否 |

**汇总（`degrade-matrix.json.summary` 实测）**

| 计数 | 值 |
|-|-|
| 探针数 | **16** |
| 档位分布 | `full 9 · unavailable 5 · degraded-usable 2` |
| **静默降级** | **0**（`silent_ids = []`） |
| 在运行路径上的模块 | `matplotlib`、`PIL`、`numpy` |
| 不在运行路径上的模块 | `yaml`、`pptx`、`lxml`、`reportlab`、`fitz`、`pypdf`、`PyPDF2`、LibreOffice CLI |
| 探针总墙钟 | 18.3 秒 |

---

## 4. 可用性结论（逐条来自上表）

1. **硬必需 = `matplotlib` + `Pillow`**：缺任一个 ⇒ 依赖门在 import 期失败 ⇒
   `exit 1` + `status=failed` 的 `result.json`（**不是裸 traceback**），产物为零；
2. **`numpy` 也是硬必需 —— 这一点与直觉相反**：`numpy` 只在 `render.py` 的
   chart `heatmap + matrix` 分支被显式 `import`，但 **matplotlib 自身硬依赖 numpy**，
   所以缺 numpy 时连 schematic 都起不来（G03/G03b/G03c 三条实测一致）。
   报告里 `uncertainty` 会写明缺失的模块名（`injected absence: numpy`），
   但 `fails` 的检查名是 `pipeline`、失败原因标成 `render.matplotlib` ⇒
   **只看检查名会误判成"缺 matplotlib"**，必须读 `uncertainty` 原文才能分辨（见 §7 第 3 条）；
3. **PDF 文本抽取是"四段降级链"**：`fitz` → `pypdf` → `PyPDF2` → **stdlib**
   （zlib 解 Flate + 抓 `Tj/TJ` 字面量）。实测 H01：三个库全缺时 `backend=stdlib`、
   **仍抽到 52 字**（夹具字面量 52 字符）⇒ "没装 PDF 库"不会阻塞整轮，
   但 **stdlib 回退只抓字面量文本、不重建版面**（这一点必须如实说明）；
4. **题集执行器的 XML 校验有两档后端**：优先 lxml，缺则标准库
   `xml.etree`（H02 实测 `xml_backend=stdlib`，1/1 仍 conforms）；
5. **可选依赖真的可选**：`reportlab`（G08/H03）、`lxml`（G06）、`fitz/pypdf/PyPDF2`（G07）
   缺失时主流程**逐字节等价于基线**（产物角色与 fail/warn 计数都与 G00 相同）；
6. **两个"与本题无关"的依赖被实测证伪/证实**：
   - `yaml`、`pptx`：本技能的运行路径**不解析 YAML、不产出 pptx** ⇒ 缺它们**实测无影响**（G04/G05）；
   - **LibreOffice CLI**：PDF 导出走 matplotlib，**不经 LibreOffice** ⇒ 缺它**实测无影响**（G09，
     且本机本来就没装 `soffice`）；
7. **组合最坏情形（G10）**：把上表里**所有可选依赖一起屏蔽**，主流程仍然 `exit 0` /
   `success` / 三件产物齐全 ⇒ 最小可用环境就是 §6 的前三行。

---

## 5. 彻底不可用清单（缺什么 ⇒ 什么能力完全不可用 + 恢复）

| 缺失 | 完全不可用的能力 | 实测证据 | 恢复 |
|-|-|-|-|
| `matplotlib` | 全部出图能力（SVG 源文件仍能写？实测**不能**：依赖门在绘图前就停了，产物为零） | G01：`exit 1` / `failed` / 无产物 | `pip install matplotlib` |
| `PIL`(Pillow) | 同上（matplotlib 的 `colors.py` 在 import 期就 `from PIL import Image`） | G02 | `pip install Pillow` |
| `numpy` | 同上（matplotlib 的硬依赖） | G03 / G03b / G03c | `pip install numpy` |
| `fitz`+`pypdf`+`PyPDF2`（**全部**） | 只影响**版面级** PDF 抽取质量：仍能抽到字面量，但**表格/坐标/换行等版面信息丢失** | H01：`backend=stdlib`、52 字 | `pip install pymupdf pypdf`（任一即可升级 backend） |
| `lxml` | 只影响 XML 校验后端（功能等价，性能与严格度略有差异） | H02：`xml_backend=stdlib` | `pip install lxml` |
| （无） | `yaml` / `pptx` / `reportlab` / LibreOffice CLI 缺失 **不使任何能力不可用** | G04/G05/G08/G09/H03 全部 `full` | 无需安装 |

---

## 6. 「最小可用环境」清单（本项目交付/部署时要什么）

| 模块 / 命令 | 是否必需 | 缺了会怎样 | 证据探针 | 回退或恢复 |
|-|-|-|-|-|
| `matplotlib` | **必需** | 流水线不可用：只写 `failed` 的 `result.json`，无任何图稿/导出件 | G01 | `pip install matplotlib` |
| `Pillow`(PIL) | **必需** | 同上一行（失败原因里写作 `render.matplotlib`） | G02 | `pip install Pillow` |
| `numpy` | **必需（传递依赖）** | 同上一行；**注意它不是"只有热图才要"** | G03 / G03b / G03c | `pip install numpy` |
| `fitz` / `pypdf` / `PyPDF2` | 可选（**至少装一个更好**） | 仍能抽到字面量文本（stdlib 回退），但**不重建版面** | H01、G07 | `pip install pymupdf pypdf` |
| `lxml` | 可选 | XML 校验回退标准库，功能等价 | H02、G06 | `pip install lxml` |
| `reportlab` | 可选 | 无影响（只在 `tool_versions` 里尽力探测） | G08、H03 | `pip install reportlab` |
| `PyYAML` | **不在运行路径上** | 实测无影响（本技能不解析 YAML） | G04、G10 | 不需要 |
| `python-pptx` | **不在运行路径上** | 实测无影响（本技能不产出 pptx） | G05、G10 | 不需要 |
| LibreOffice CLI | **不在运行路径上** | 实测无影响（PDF 由 matplotlib 直接导出） | G09 | 不需要 |
| Python | 3.9+（实测 3.13.9） | 语法/标准库要求 | 全部探针 | — |

**一句话**：把 `matplotlib + Pillow + numpy` 装上就能跑满；
`pymupdf`（或 `pypdf`）装上能把 PDF 抽取从"只抓字面量"升级为"版面级"。

---

## 7. 未覆盖声明（本包**不**为这些背书）

1. **半损坏的库**（装了但 ABI/版本不匹配、缺 DLL）：本轮只测"完全缺失"这一种；
2. **跨 OS / 跨 Python 版本**：只测了本机 Windows + Python 3.13.9；
3. **字体缺失 / 无 CJK 字体**：属另一条链路（`font.cjk` warn），本轮**未**纳入降级矩阵；
4. **matplotlib 后端依赖**（缺 `tkinter`/`Agg` 之外的 GUI 后端、缺 FreeType）**未测**；
5. **磁盘/权限类失败**（只读输出目录、磁盘满）**未测**；
6. **`--skip-checks` / `--no-lint` 叠加缺依赖的组合**未测；
7. **G03c 的 heatmap 夹具是合成的**（`matrix` 2×3 合成值）—— 它只用来暴露
   `import numpy` 那条分支，**不代表**真实转录组数据的表现；
8. **`numpy` 缺失时的"失败原因标签"**（`fails=[pipeline]` + 说明写成
   `render.matplotlib`）是**如实记录到的现象**，不是本包认为正确的分类；
   复核时请以 `uncertainty` 原文里的模块名为准。
