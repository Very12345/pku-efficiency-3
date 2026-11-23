# DEGRADE-MATRIX.md — 缺依赖降级链：逐项实测矩阵（v9 轴）

> 本文件是 v9 的**轴文档**。权威测量器 = `scripts/degrade_probe.py`（只依赖标准库）；
> 机器可读结果 = 包根 `degrade_report.json`（本机实跑，不是预置答案）。
> 「最小可用环境」清单见同目录 `references/MINIMAL-ENV.md`。

## 1. 这份文档回答的问题

Skill 声称"标准库即可产出可编辑 SVG 与全部审计产物，matplotlib 只影响预览"。
**这句话必须能被逐个依赖地证实或证伪**，否则它就是一句没有证据的自我描述。
所以本轴做三件事：

1. **受控导入拦截**（装在子进程里的 `sys.meta_path` 拦截器）逐个屏蔽
   `matplotlib` / `numpy` / `PIL` / `yaml` / `pptx` / `lxml` / `pypdf`，各跑一次**真实主流程**；
2. **PATH 处理**模拟 LibreOffice CLI **命令不存在**（PATH 清空）与**存在但失败**（桩命令退出 127；
   桩会先写调用标记文件，用来证明"到底有没有真的调用过"）；
3. 每一行记录**实测**降级形态：退出码 / `status` / 剩余产物 / 是否写 `result.json` /
   失败检查项 id / `gates.g4,g5` / `uncertainty` 留痕。

**拦截器自证**：每个屏蔽行都会先在子进程里 `__import__` 被屏蔽的模块并记录结果；
只有确实 `ImportError` 的行才被采信（否则报告里标记"拦截未生效，该行结论不可用"）。
本机 13 行全部 `importable = false`（详见 `degrade_report.json → rows[*].import_interception`）。

## 2. 怎么跑

```bash
export SKILL_DIR=/skills/weekly-skill
python3 "$SKILL_DIR/scripts/degrade_probe.py" --help

python3 "$SKILL_DIR/scripts/degrade_probe.py" \
    --work /tmp/dg --report /tmp/degrade_report.json        # 13 行全跑
python3 "$SKILL_DIR/scripts/degrade_probe.py" --only s03     # 只跑缺 PIL 那一行
python3 "$SKILL_DIR/scripts/degrade_probe.py" --json > /tmp/dg.json
```

退出码：`0` = 全部场景跑完；`2` = **控制行**（全依赖）就不通 → 环境本身有问题、结论不可用；`4` = 参数错误。

环境：CPython 3.13.9 / win32；基线解释器装有 matplotlib 3.10.6、Pillow 12.3.0、PyYAML、python-pptx、lxml、pypdf；
`config.host_has_libreoffice = false`（**本机本来就没有 LibreOffice** —— 见 §5 的诚实声明）。

## 3. 逐项实测矩阵（13 行）

`产物` = 输出目录里实际留下的文件数；`剩余` 只列关键件。

| # | 行 id | 拿掉的东西 | exit | status | 产物 | 剩余关键件 | 失败检查项 | 留痕 | 判定 |
|-|-|-|-|-|-|-|-|-|-|
| 1 | `s00-baseline` | 无（对照） | 0 | success | 7 | SVG·PNG·PDF·result.json·审计×2 | — | `uncertainty = 0` | 全能力 |
| 2 | `s01-no-matplotlib` | `matplotlib` | **2** | **partial** | 5 | SVG·result.json·model·审计×2 | `F01_png` `F01_pdf` | 1 条（含真实 ImportError 文本） | 预览全失，源件与审计不受影响 |
| 3 | `s02-no-numpy` | `numpy` | 2 | partial | 5 | 同上 | `F01_png` `F01_pdf` | 1 条 | 同 s01（matplotlib 无法导入） |
| 4 | `s03-no-pil` | `PIL` | 2 | partial | 5 | 同上 | `F01_png` `F01_pdf` | 1 条 | **PNG 与 PDF 一起丢**（见 §4） |
| 5 | `s04-no-yaml` | `yaml` | **0** | **success** | 7 | 全部 | — | 0 条 | 无影响（本包不 import yaml） |
| 6 | `s05-no-pptx` | `pptx` | 0 | success | 7 | 全部 | — | 0 条 | 无影响 |
| 7 | `s06-no-lxml` | `lxml` | 0 | success | 7 | 全部 | — | 0 条 | 无影响（用标准库 `xml.etree`） |
| 8 | `s07-no-pypdf` | `pypdf` | 0 | success | 7 | 全部 | — | 0 条 | 无影响（不解析 PDF） |
| 9 | `s08-no-mpl-no-pil` | `matplotlib`+`numpy`+`PIL` | 2 | partial | 5 | 同 s01 | `F01_png` `F01_pdf` | 1 条 | 最坏情况仍交付 SVG+审计 |
| 10 | `s09-svg-only` | 无，但 `--formats svg`（**有意**） | **2** | **partial** | 5 | 同 s01 | `F01_png` `F01_pdf` | 1 条（"本次未请求 PNG/PDF 预览"） | 有意降级被记为 fail（见 §6） |
| 11 | `s10-libreoffice-missing` | PATH 里无 `soffice`/`libreoffice` | 0 | success | 7 | 全部 | — | 0 条 | 无影响 |
| 12 | `s11-libreoffice-failing` | 桩命令存在但退出 127 | 0 | success | 7 | 全部 | — | 0 条 | 无影响；**桩未被调用**（标记文件未生成） |
| 13 | `s12-pil-png-microtrace` | `PIL`（**不经主流程**，直接调 matplotlib） | 1 | —（微追溯） | — | `micro.png` 未写出 | — | — | 机制证据，见 §4 |

**所有行的 `gates.g4_svg_layers` 都是 `true`** —— 可编辑 SVG 源在任何缺依赖情形下都还在（7 层图层完整）。
`g5_png` 只在 PNG 真的产出时为 `true`（s01–s03、s08–s10 的对应行为 `false`）。

## 4. 关键机制：为什么缺 PIL 会连 PDF 一起丢（微追溯实测）

`s03` 只屏蔽 `PIL`，结果与"屏蔽 matplotlib"**完全一样**（无 PNG、无 PDF、partial、`F01_png`+`F01_pdf` 失败）。
`s12` 微追溯给出因果证据：**不经主流程**、直接 `matplotlib.use("Agg")` + `fig.savefig("micro.png")`，
在屏蔽 PIL 的子进程里退出码 `1`、`micro.png` **未写出**，traceback 尾部（已剔除主机路径行，省略 3 行）实测为：

```text
    from . import _api, _version, cbook, _docstring, rcsetup
    from matplotlib.colors import Colormap, is_color_like
    from PIL import Image
  File "<WORK>/shim_blocked.py", line 18, in find_spec
    raise ImportError(
        "degrade_probe: import of %r is blocked in this environment" % fullname)
ImportError: degrade_probe: import of 'PIL' is blocked in this environment
```

⇒ **结论（可直接引用）**：`PIL` 不是"只被 `validate_figure.py` 的 `F02_png` 尺寸检查用到"，
而是 **matplotlib 自己的硬依赖**（`matplotlib.colors` 顶层 `from PIL import Image`）。
再加上 `scripts/mpl_backend.py` 是**先存 PNG、再存 PDF**（PNG 保存抛错 → 后面的 PDF 永远不执行），
所以"缺 PIL"= "缺 matplotlib" = **预览全失**。这是本轴最有价值的一条实测：它推翻了仅凭 `import` 语句
做的静态依赖猜测（静态看，`PIL` 只出现在 `validate_figure.py` 的 `F02_png` 里）。

`numpy` 同理：它没有出现在本包任何 `import` 里，但 matplotlib 需要它 —— 屏蔽 numpy 的实测结果与屏蔽 matplotlib 一致。

## 5. LibreOffice 两格 + 诚实声明

| 行 | PATH 状态 | `shutil.which("soffice")` 实测 | 桩是否被调用 | 交付 |
|-|-|-|-|-|
| `s00-baseline` | 继承 | `None`（本机本来就没有） | — | 7 件全在 |
| `s10` | 清空的自建目录 | `None` | — | 7 件全在（exit 0 / success） |
| `s11` | 前置桩目录 | `<WORK>/stubbin/soffice.BAT` | **否**（标记文件 `stub-calls.txt` 未生成，`stub_invoked = false`） | 7 件全在（exit 0 / success） |

**诚实声明**：`config.host_has_libreoffice = false` —— 本机基线环境本来就没有 LibreOffice，
所以 `s10` 严格说只证明"PATH 被清空后行为不变"；**真正有信息量的是 `s11`**：
它把 `soffice`/`libreoffice` 放进 PATH 且让它们存在（`which` 能解析到桩），
再用**先写标记再退出 127** 的桩证明：**主流程从未 shell out 到 LibreOffice**
（标记文件没有出现），因此"LibreOffice 缺失/失败"对本 Skill 的交付**没有影响**。
本包的 PDF 由 matplotlib 的 PDF 后端生成，不需要外部办公套件——这与"模板/文档类 Skill"是相反的依赖形态。

## 6. 有意降级 vs 被迫降级（`s09`）

`s09-svg-only` 是**用户主动**只要 SVG（`--formats svg`）：依赖齐全，但实测 **exit 2 / status partial**，
失败项同样是 `F01_png` `F01_pdf`。原因在 `scripts/main.py` 的 CP3：未请求的格式会把
`out_files["png"]/["pdf"]` 置 `None`，而 `validate_figure.run_checks()` 的 `F01_png/F01_pdf`
是"文件不存在即 fail"——**有意降级与被迫降级在检查层不可区分**。
流水线自己的 `uncertainty` 如实写了"本次未请求 PNG/PDF 预览（--formats svg）"，
所以这是"结论正确、状态偏严"的情形，不是静默失败。

⇒ 使用建议：**需要 `status=success` 就始终请求 `svg,png,pdf`**；只做 SVG 时不要把 `partial` 当成渲染失败。

## 7. 可用性结论（按能力归类）

| 能力 | 依赖什么 | 缺依赖时 |
|-|-|-|
| `diagram.svg` 可编辑分层源 + `data-*` 溯源属性 | **无第三方依赖**（标准库字符串模板） | 始终可用（13 行实测 g4 全 true） |
| `model.json` / `topology.json` / `legend_audit.json` | 无第三方依赖 | 始终可用 |
| 拓扑审计 P01–P08、图例/编码审计 L01–L08+E01–E02 | 无第三方依赖 | 始终可用 |
| `result.json`（契约 + 门 + 自检 + 不确定性） | 无第三方依赖 | 始终可用（含 `status=partial`） |
| `diagram.png` 预览 | matplotlib + numpy + Pillow | **彻底不可用**（缺任一个都拿不到） |
| `diagram.pdf` 矢量导出 | 同上（且受 PNG 保存顺序牵连） | **彻底不可用** |
| PNG 尺寸/可打开性检查 `F02_png` | Pillow | 随 PNG 一起不可用 |
| LibreOffice 类外部导出 | 不使用 | 无影响（实测从未调用） |

**一句话**：缺 `matplotlib`/`numpy`/`PIL` ⇒ 丢**预览**（PNG/PDF）、保留**源件与全部审计**，
状态降为 `partial`、退出码 2；缺 `yaml`/`pptx`/`lxml`/`pypdf`/LibreOffice ⇒ **实测零影响**。

## 8. 未覆盖声明（本轴没测的）

1. **字体真的缺失**（无中文字体）时的渲染：只记录 matplotlib 自身的字体告警，不卸载系统字体做对照。
2. **部分损坏的安装**（如 matplotlib 可 import 但 Agg 后端缺 C 扩展）：本轴只覆盖"整模块不可导入"。
3. **`README.md` 声明的依赖之外**的第三方库：本包 `scripts/` 的 import 并集已逐个覆盖，别的不测。
4. **平台真实评测容器**的依赖集（不可见）：结论只对本机实测的解释器/版本组合有效。
5. **磁盘满 / 只读输出目录 / 权限不足**：属故障注入轴，不在依赖轴内。
6. **`--materials-dir`、`TASK_OUTPUT` 等其它入口在缺依赖下的行为**：本轴只用
   `--case/--model-file/--out/--formats/--dpi`。

## 9. 复现本文件全部数字

```bash
export SKILL_DIR=/path/to/challenge-83d4f050
python3 "$SKILL_DIR/scripts/degrade_probe.py" \
    --work /tmp/dg --report /tmp/degrade_report.json           # 退出码 0
python3 - <<'PY'
import json
d = json.load(open("/tmp/degrade_report.json", encoding="utf-8"))
for r in d["rows"]:
    print(r["id"], r["exit_code"], r["status"], r["artifacts_present"], r["failed_checks"])
print(json.dumps(d["minimal_environment"], ensure_ascii=False, indent=2))
PY
```
