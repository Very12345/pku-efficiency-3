# DEGRADE-MATRIX.md — 缺依赖降级链实测（本包 v9 的轴）

> 本文所有数字来自 `scripts/degrade_probe.py` 的现场实测，表格按报告的 `conditions[]` /
> `minimal_env` 逐项渲染。
> 复核命令：`python "$SKILL_DIR/scripts/degrade_probe.py" --json /tmp/degrade_report.json`

`references/failure-modes.md` 写了"缺 Pillow/reportlab 就降级"的口径。口径不是证据。
这一轴把**每个依赖逐个抽走**，跑同一份输入，实测"产物还剩什么、status 变什么、
还写不写 result.json、退出码是多少"，并给出**最小可用环境**清单。

## 0. 一句话结论

- 本包**真正用到**的第三方依赖只有两个：**Pillow（PIL）** 与 **reportlab**；
- 但两者**不是并列关系**：`reportlab/lib/utils.py` 在导入期就 `from PIL import Image`，
  所以 **Pillow 一缺，PNG 和 PDF 同时没了**（这是本轮实测出来的、与直觉相反的硬事实）；
- 规格点名的其余依赖（`yaml` / `numpy` / `matplotlib` / `python-pptx`）与
  LibreOffice CLI —— **本包一行都没 import**，抽走它们**零差异**（13 个条件里 5 个是这类）；
- 纯标准库环境下仍能产出 **5 件**：可编辑 SVG 源文件 + `evidence.json` + `layout.json` +
  `verify_report.json` + `result.json`（`status=partial`，契约 JSON 完整）。

## 1. 方法：受控导入拦截（可自证生效）

拦截方式不是"改脚本"、不是"卸载包"，而是在**子进程**里装一个 `sys.meta_path` 拦截器
（现场生成 `_blocker_driver.py`），对命中前缀的模块 `find_spec` 直接抛
`ModuleNotFoundError("No module named 'X' (blocked by degrade_probe)")`，
然后用 `runpy` 跑真实 `scripts/main.py`。被拦进程的一切行为等价于"这台机器上没装这个包"。

**拦截器自证**（防"拦了没拦住"）：`c04-no-PIL.Image` 只拦 **子模块** `PIL.Image`，
实测与整包拦 `PIL` 产生**同样的降级**（PNG 与 PDF 双双失败，产物 5 件）；
`c11`/`c12` 拦关键标准库 `xml` / `hashlib` 后**流水线整体不可用**（连 `result.json`
都写不出）。三条合起来证明：拦截器真的能拦住、且不同依赖的影响面确实不同。

`c10-no-soffice` 用的是另一种手法（属同一条轴）：把 `PATH` 指向空目录、并把
`SOFFICE_BIN`/`LIBREOFFICE_BIN` 指到不存在的路径，模拟"机器上没有 LibreOffice"。

## 2. 逐项实测（13 个条件）

| id | 条件 | 拦截模块 | 隐藏 CLI | 退出码 | status | 写出 result.json | 产物数 | 实测形态 | 声明期望 |
|---|---|---|---|---|---|---|---|---|---|
| c00-base | 对照：不拦截任何依赖 | — | 否 | 0 | success | 是 | 7 | full | full |
| c01-no-PIL | 缺 Pillow（PIL） | PIL | 否 | 3 | partial | 是 | 5 | degrade | degrade |
| c02-no-reportlab | 缺 reportlab | reportlab | 否 | 0 | partial | 是 | 6 | degrade | degrade |
| c03-no-PIL-no-reportlab | 两者都缺（最坏真实情形） | PIL,reportlab | 否 | 3 | partial | 是 | 5 | degrade | degrade |
| c04-no-PIL.Image | 只拦 PIL.Image（子模块级） | PIL.Image | 否 | 3 | partial | 是 | 5 | degrade | degrade |
| c05-no-yaml | 缺 PyYAML（规格点名） | yaml | 否 | 0 | success | 是 | 7 | zero-diff | zero-diff |
| c06-no-numpy | 缺 numpy（规格点名） | numpy | 否 | 0 | success | 是 | 7 | zero-diff | zero-diff |
| c07-no-matplotlib | 缺 matplotlib（规格点名） | matplotlib | 否 | 0 | success | 是 | 7 | zero-diff | zero-diff |
| c08-no-pptx | 缺 python-pptx（规格点名） | pptx | 否 | 0 | success | 是 | 7 | zero-diff | zero-diff |
| c09-no-named-five | 规格点名依赖全缺（yaml+numpy+matplotlib+pptx+PIL+reportlab） | yaml,numpy,matplotlib,pptx,PIL,reportlab | 否 | 3 | partial | 是 | 5 | degrade | degrade |
| c10-no-soffice | 无 LibreOffice CLI（PATH 指向空目录） | — | 是 | 0 | success | 是 | 7 | zero-diff | zero-diff |
| c11-no-xml | 缺 xml（关键标准库对照） | xml | 否 | 1 | — | **否** | 0 | broken | broken |
| c12-no-hashlib | 缺 hashlib（关键标准库对照） | hashlib | 否 | 1 | — | **否** | 0 | broken | broken |

## 3. 产物还剩什么（逐条件）

| id | 还剩的产物 | 丢掉的产物 | uncertainty scope | 契约门 check_ok |
|---|---|---|---|---|
| c00-base | evidence.json, figure.pdf, figure.png, figure.svg, layout.json, result.json, verify_report.json |  |  | True |
| c01-no-PIL | evidence.json, figure.svg, layout.json, result.json, verify_report.json | figure.pdf, figure.png | pdf, png | False |
| c02-no-reportlab | evidence.json, figure.png, figure.svg, layout.json, result.json, verify_report.json | figure.pdf | pdf | True |
| c03-no-PIL-no-reportlab | evidence.json, figure.svg, layout.json, result.json, verify_report.json | figure.pdf, figure.png | pdf, png | False |
| c04-no-PIL.Image | evidence.json, figure.svg, layout.json, result.json, verify_report.json | figure.pdf, figure.png | pdf, png | False |
| c05-no-yaml | evidence.json, figure.pdf, figure.png, figure.svg, layout.json, result.json, verify_report.json |  |  | True |
| c06-no-numpy | evidence.json, figure.pdf, figure.png, figure.svg, layout.json, result.json, verify_report.json |  |  | True |
| c07-no-matplotlib | evidence.json, figure.pdf, figure.png, figure.svg, layout.json, result.json, verify_report.json |  |  | True |
| c08-no-pptx | evidence.json, figure.pdf, figure.png, figure.svg, layout.json, result.json, verify_report.json |  |  | True |
| c09-no-named-five | evidence.json, figure.svg, layout.json, result.json, verify_report.json | figure.pdf, figure.png | pdf, png | False |
| c10-no-soffice | evidence.json, figure.pdf, figure.png, figure.svg, layout.json, result.json, verify_report.json |  |  | True |
| c11-no-xml |  | evidence.json, figure.pdf, figure.png, figure.svg, layout.json, result.json, verify_report.json | — | — |
| c12-no-hashlib |  | evidence.json, figure.pdf, figure.png, figure.svg, layout.json, result.json, verify_report.json | — | — |

## 4. 可用性结论

| 条件 | 退出码 | status | 还能交付什么 | 结论 |
|-|-|-|-|-|
| 什么都装齐（c00） | 0 | `success` | 7 件：SVG + PNG + PDF + 3 份 JSON + result | 完整 |
| 缺 reportlab（c02） | 0 | `partial` | 6 件（无 `figure.pdf`） | **可交付**：SVG 是源文件，PNG 是预览，PDF 是"尽力而为" |
| 缺 Pillow（c01/c09） | 3 | `partial` | 5 件（无 PNG、无 PDF） | **可交付但降级**：`exports=[]` ⇒ `G4` 不过 ⇒ 退出码 3（契约门诚实地报错，不是崩） |
| 缺 yaml/numpy/matplotlib/pptx（c05–c08） | 0 | `success` | 7 件 | **零差异**：本包不依赖它们 |
| 无 LibreOffice CLI（c10） | 0 | `success` | 7 件 | **零差异**：本包不调用外部 CLI |
| 缺 xml / hashlib（c11/c12） | 1 | 无 | **0 件**，连 `result.json` 都没有 | **彻底不可用**：这两条是流水线的地基 |

三条把结果钉住的事实：

1. **`status` 从不撒谎**：三个降级条件的 `status` 都是 `partial`，并且
   `result.json.uncertainty` 里逐条写明 `{"scope":"png"|"pdf", "issue":"… 失败: <原因>", "action": …}`
   —— 见下表 `uncertainty scope` 一列（例如 `c02` 只有 `pdf`，`c01` 有 `png` 与 `pdf` 两条）。
2. **退出码会跟着变**：缺失导致 `exports` 为空时 `check.py` 的 `G4` 不过 ⇒ `main.py` 返回 **3**
   （不是 0、也不是崩）。这是"契约门在降级时仍然工作"的机器证据。
3. **`result.json` 始终落盘**（除 `xml`/`hashlib` 两个地基条件外）：即使 PNG/PDF 全失败，
   结构化结果仍在，回放可见。

## 5. 哪些功能**彻底**不可用

| 缺什么 | 彻底不可用的功能 | 实测证据 |
|-|-|-|
| `xml`（`xml.etree.ElementTree`） | **一切**：`check.py` 在导入期就依赖 ET，`main.py` 的导入链直接失败 | c11：退出码 1，0 件产物，`ModuleNotFoundError: No module named 'xml'` |
| `hashlib` | **一切**：`evidence.json` 的素材 sha256、SVG 的 `checksum_sha256` 都靠它 | c12：退出码 1，0 件产物 |
| `PIL` | **两个预览**（PNG 与 PDF 一起） | c01：`exports=[]`（而非只少 PNG） |

前两条是"地基"，第三条是**本包的真实依赖结构**（不是文档里写的那种"PNG 靠 PIL、PDF 靠 reportlab"的并列假设）。

### reportlab 依赖 PIL 的根因（逐条可复核）

```
$ python -c "import reportlab"        # 有 PIL 时正常
$ DEGRADE_BLOCK=PIL python -c "import reportlab.pdfgen.canvas"
  File ".../reportlab/lib/utils.py", line 15, in <module>
    from PIL import Image
ModuleNotFoundError: No module named 'PIL' (blocked by degrade_probe)
```

⇒ 安装顺序上 **Pillow 在前**：只装 reportlab 而不装 Pillow，两个预览都拿不到。

## 6. 最小可用环境清单

| 档位 | 需要什么 | 能产出什么（实测） | status | 退出码 |
|---|---|---|---|---|
| ① 纯标准库 | CPython 3.10+（json/hashlib/math/xml.etree/dataclasse… | 5 件：evidence.json, figure.svg, layout.json, result.j… | partial | 3 |
| ② + Pillow（PIL） | Pillow | 6 件（+ figure.png） | success | 0 |
| ③ + reportlab | reportlab（且必须有 Pillow） | 7 件（+ figure.pdf） | success | 0 |

**要点**：第 ① 档（**纯标准库**）就能产出本题最关键的交付物 —— **可编辑 SVG 源文件**
与**完整契约 JSON**（含 `evidence` / `verify` / `output_contract` 四段）。
PNG/PDF 预览是"加档"能力：加 Pillow 得 PNG（并让 reportlab 可用），再加 reportlab 得 PDF。

**明确不需要**（抽走零差异）：

| 依赖 | 实测证据 |
|---|---|
| yaml | c05 零差异 |
| numpy | c06 零差异 |
| matplotlib | c07 零差异 |
| python-pptx(pptx) | c08 零差异 |
| LibreOffice CLI(soffice) | c10 零差异（PATH 清空后同产物） |

## 7. 与 `references/failure-modes.md` 的口径对照

| 口径（文档原话方向） | 本轮实测 | 处置 |
|-|-|-|
| "无 Pillow ⇒ PNG 降级" | 实测是 **PNG + PDF 一起降级**（reportlab 依赖 PIL） | 本文纠正；`failure-modes.md` 的 D9/D10 决策规则不变（仍走 `partial` + `uncertainty`），只是影响面变大 |
| "无 reportlab ⇒ PDF 降级" | 一致（只少 PDF，`status=partial`，退出码 0） | 无需改 |
| "依赖缺失要在 `uncertainty` 记明" | 一致（实测每个降级条件都有对应 scope） | 无需改 |
| "导出件缺失 ⇒ `G4` 不过" | 一致（`exports=[]` ⇒ 退出码 3） | 无需改 |

> 本文只**补事实**，不改既有脚本与既有决策规则；`scripts/export_preview.py`、
> `scripts/fonts.py` 逐字节未改。

## 8. 未覆盖声明

| 未覆盖项 | 为什么 |
|-|-|
| 间接依赖（PIL 自己依赖的 zlib/zip 等） | 本探针只拦顶层包/子模块；要拦 C 扩展得换手法 |
| 磁盘满 / 输出目录只读 / 无写权限 | 不属"缺依赖"，归 `scripts/fault_inject.py` 的模板族与未覆盖项 |
| Python 版本过低（3.9 及以下）造成的语法级不可用 | 本探针不换解释器 |
| 字体缺失 | 属"依赖"但走 `fonts.py` 的探测链，`fault_inject.py` 的 F3-* 已覆盖 |
| Linux/macOS 上的同一矩阵 | 本轮只在 Windows 11 + CPython 3.13.9 实测；拦截机制是纯 Python，预期可移植但**未实测** |
| `pip install` 顺序/虚拟环境隔离 | 不属运行时降级，属部署 |

## 9. 复现命令

```bash
# 全矩阵（13 条件，约 6 秒）
python "$SKILL_DIR/scripts/degrade_probe.py" --json /tmp/degrade_report.json

# 只看真实依赖两条
python "$SKILL_DIR/scripts/degrade_probe.py" --only c01-no-PIL --only c02-no-reportlab

# 只看拦截器是否真的生效（子模块级拦截）
python "$SKILL_DIR/scripts/degrade_probe.py" --only c04-no-PIL.Image

# 列出条件表（不执行）
python "$SKILL_DIR/scripts/degrade_probe.py" --list

# 回归断言：与声明期望不符的条件数一变就 attention
python "$SKILL_DIR/scripts/degrade_probe.py" --expect-deviations 0
```
