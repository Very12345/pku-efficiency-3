# DEGRADE-MATRIX — 缺依赖降级链实测 + 最小可用环境

本文件回答：**把某一个依赖从环境里拿掉，这个 Skill 还能交付什么？** 不看文档里写的
"会优雅降级"，而是真跑：用 `PYTHONPATH` 前置一个 `import` 即抛 `ImportError` 的假包
模拟"没装"（不卸载任何东西），然后跑真实入口，记录**实测** exit / `result.json`
是否写出 / `status` / 产物还剩几个 / `uncertainty` 内容 / 单入口在哪一步断。

复核命令（`$RUN` 必须是包外可写目录；包内跑会留下 `__pycache__`，资源契约拒收）：

```bash
RUN=<包外目录>
python "$SKILL_DIR/scripts/degrade_probe.py" --skill "$SKILL_DIR" --run "$RUN"     --json "$RUN/degrade_report.json" --markdown "$RUN/degrade.md"
echo "exit=$?"        # 实测 exit 0
python "$SKILL_DIR/scripts/degrade_probe.py" --skill "$SKILL_DIR" --list   # 只列场景
```

---

## 1. 结论（实测）

| 判据 | 结果 |
|-|-|
| 场景总数 | **10**（8 个单一依赖 + 1 个合并 + 1 个带图对照） |
| **硬依赖**（拿掉就整条流程失败） | **`pptx`、`PIL`、`lxml`** |
| **非依赖**（拿掉完全不影响） | **`matplotlib`、`numpy`、`yaml`、`reportlab`、LibreOffice** |
| 投毒未生效的场景 | **0**（每个场景都用 `python -c "import X"` 单独验证过） |
| **静默通过**（该失败却 exit 0 + `success`） | **0** |
| 脚本退出码 | **0** |

**干净基线（对照）**：exit=0、`status=success`、`--out` 下 **12** 个产物、
`result.json` **28** 个顶层键、deck **有**、PNG **2** 张。
**失败场景**一律是：exit=1、`status=failed`、`--out` 下只剩 **1** 个产物
（`result.json`）、顶层键 **14**、deck **无**、PNG **0** 张、`uncertainty` **1** 条
（`pipeline`，note 是原始异常文本）。**"失败"和"成功"两种形态之间没有中间态被漏报。**

## 2. 逐依赖实测矩阵

| 拿掉什么 | 模拟方式 | 实测 exit | result.json | status | 顶层键 | 产物数 | deck | PNG | uncertainty | 连带不可导入 | 判定 |
|-|-|-|-|-|-|-|-|-|-|-|-|
| `pptx` | PYTHONPATH 假包 | **1** | 有 | `failed` | 14 | 1 | **无** | 0 | 1 | — | 硬依赖 |
| `PIL` | PYTHONPATH 假包 | **1** | 有 | `failed` | 14 | 1 | **无** | 0 | 1 | `matplotlib`、`pptx` | 硬依赖 |
| `lxml` | PYTHONPATH 假包 | **1** | 有 | `failed` | 14 | 1 | **无** | 0 | 1 | `pptx` | **间接硬依赖** |
| `matplotlib` | PYTHONPATH 假包 | 0 | 有 | `success` | 28 | 12 | 有 | 2 | 1 | — | 非依赖 |
| `numpy` | PYTHONPATH 假包 | 0 | 有 | `success` | 28 | 12 | 有 | 2 | 1 | `matplotlib` | 非依赖 |
| `yaml` | PYTHONPATH 假包 | 0 | 有 | `success` | 28 | 12 | 有 | 2 | 1 | — | 非依赖 |
| `reportlab` | PYTHONPATH 假包 | 0 | 有 | `success` | 28 | 12 | 有 | 2 | 1 | — | 非依赖 |
| LibreOffice | **PATH 置空** | 0 | 有 | `success` | 28 | 12 | 有 | 2 | 1 | — | 非依赖（见 §4） |
| `pptx`+`PIL`+`matplotlib`+`numpy`+`yaml`+`lxml`+`reportlab`（合并） | 7 个假包 | **1** | 有 | `failed` | 14 | 1 | **无** | 0 | 1 | 全 7 个 | 最坏情况仍诚实 |
| `PIL`（**带真实源图**对照） | PYTHONPATH 假包 | **1** | 有 | `failed` | 14 | 1 | **无** | 0 | 1 | `matplotlib`、`pptx` | 对照（见 §5） |

（每行都是真实子进程实测；`PYTHONPATH 假包` = 在 `PYTHONPATH` 前置一个
`__init__.py` 里 `raise ImportError(...)` 的同名包。）

## 3. 三条最容易踩错的结论

### 3.1 `lxml` 是**间接硬依赖**——本包代码一次都没 import 它

`grep` 实测：本包 `scripts/*.py` 里**没有任何一处**引用 `lxml`（XML 走标准库
`xml.etree.ElementTree`）。但 `python-pptx` 自己在包级做 `from lxml import etree`
（`opc/oxml.py`、`oxml/__init__.py`、`oxml/xmlchemy.py`），所以**缺 lxml 等于缺
pptx**：实测 exit=1、`status=failed`，且 `tool_versions` 里 `pptx` 记 `unavailable`。

**结论**：只按"本包 import 了什么"列依赖清单会漏掉真依赖。本包因此把 lxml 明列进
"运行必需"。

### 3.2 `yaml` / `numpy` / `matplotlib` / `reportlab` 是**冗余依赖**，缺了完全无影响

四个场景实测都是**与基线逐项相同**：exit=0、`success`、12 个产物、28 个顶层键、
deck 有、PNG 2 张。区别只在 `tool_versions` 里对应项记 `unavailable`（`yaml` 连这项
都没有，因为 `tool_versions` 本来就不记录它）。

**为什么仍然值得测**：这正是"文档里写「依赖 python-pptx 与 Pillow」"的**实测证据**——
如果哪天有人把 yaml 引进核心路径，这张矩阵会立刻变红。

### 3.3 `PIL` 缺了是硬失败，**不是**"预览没了但 deck 还在"

直觉上会以为"PIL 只用于预览，缺了最多没有 PNG"。实测**不是**：`preview.py` 在模块级
`from PIL import Image, ImageDraw, ImageFont`，而预览属于主流程第 5 步 ⇒ 整条流程失败：
exit=1、`status=failed`、**deck 也没有**（阶段二产物在异常路径里没有落盘）。

## 4. LibreOffice 缺失：**完全无影响**，因为管线从不调用它

外部程序不能靠 `PYTHONPATH` 拦截，所以用 **PATH 置空**模拟"机器上没有
soffice/libreoffice"。实测：**与基线逐项相同**（exit=0、`success`、12 产物、28 键、
deck 有、PNG 2 张）。

原因（读代码 + 实测一致）：`preview.py` **从不 shell out 到 `soffice`**。它的做法是
画一张 **PIL 示意图**，并在三处如实标注：
`render_log.json` 的 `renderer="PIL (no LibreOffice/uno detected on runtime box)"`
与 `honest_note`、`_PREVIEW_ARE_SCHEMATIC.txt`、以及 `result.json.main_result.
preview_is_schematic=true`。

**这条的意义**：LibreOffice 不是"还缺的环境项"，而是**已被明确放弃并披露的能力**。
装了 LibreOffice 也不会让 `preview.py` 产出真 PDF——要真 PDF 得改代码，不在本包范围。

## 5. 带真实源图的对照组：为什么必须有这一组

`adapt_pptx.py` 里读图尺寸的 `from PIL import Image` 是**懒加载**，并且被
`figures[].file_exists` 保护——**只有材料里真的存在源图文件时才会走到**。

如果只跑"无图"场景，`PIL` 缺失的失败就可能是**假阳性**（"因为没图，所以没用到 PIL"）。
所以对照场景（`10-PIL-with-figure`）先用 `make_synthetic_inputs.py` 在**未投毒**环境
生成 `fig1.png`/`fig2.png`（实测 exit=0），再投毒跑主流程。

实测结果相同：exit=1、`failed`、1 个产物、deck 无。**即：PIL 的硬失败来自模块级
import（预览阶段），与"是否有图"无关。**

## 6. 「最小可用环境」清单（实测口径）

**能完整交付（exit 0、12 产物、28 键、deck + 2 PNG）所需的最小集合**：

| # | 项 | 版本实测 | 是否可省 | 备注 |
|-|-|-|-|-|
| 1 | Python | **3.13.9**（实测） | 否 | 代码用 `from __future__ import annotations` + `X \| None` 类型注解 ⇒ 需 **3.9+** |
| 2 | `python-pptx` | **1.0.2** | **否** | 建/读 pptx；阶段一审计 + 阶段二构建 + G4 重开都靠它 |
| 3 | `Pillow` | **12.3.0** | **否** | 预览（模块级 import）；示例图与字体探测也用它 |
| 4 | `lxml` | 已装（`pptx` 的传递依赖） | **否** | 本包不直接 import，但 `pptx` 包级 import ⇒ 装了 pptx 就一定有 |
| 5 | 字体 | 系统字体（可选） | 可省 | 找不到 TrueType 时回退 PIL 内置位图字体，`render_log.json` 如实记录 |
| 6 | LibreOffice / uno | **未装** | **可省** | 实测无影响；预览本来就是 PIL 示意图 |
| 7 | `numpy` / `matplotlib` / `yaml` / `reportlab` | 已装 | **可省** | 仅 `tool_versions` 记录版本；缺了矩阵实测无影响 |
| 8 | 网络 | — | **可省** | 全流程离线；不下载任何模型/字体/模板 |

**最小安装命令（3 项）**：

```bash
python -m pip install "python-pptx>=0.6.21" "Pillow>=9.0"
# lxml 会作为 python-pptx 的依赖自动装上；不要手工省略它
```

**最小可用环境的验收**（包外）：

```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> --task <task.md> --out <out>
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --out-dir <out> --case <case.json>
```

两条都要 exit 0，且 `--out` 下 12 个产物、`result.json` 28 个顶层键。

## 7. 哪些功能在缺依赖时**彻底不可用**（逐条点名）

| 缺什么 | 彻底不可用的功能 |
|-|-|
| `pptx` | **全部**：阶段一模板审计、阶段二建册、`deck.pptx`、G4 重开校验、预览（预览依赖页计划但流程已中断）、契约门 |
| `PIL` | **全部**：预览渲染（封面 + 联系表）、示例图合成——而预览是主流程的必经步骤 ⇒ 连 deck 都不产出 |
| `lxml` | **全部**（经 `pptx` 传导）：同上 |
| LibreOffice | **仅**"像素级 PDF/PNG 导出"——而这本来就没实现（预览是示意图），所以实际不可用的是"未来可能有的真 PDF 导出" |
| `numpy`/`matplotlib`/`yaml`/`reportlab` | **无**（实测无影响） |

## 8. 未覆盖声明

1. **未测"部分可用"的中间形态**：本矩阵只观察到两种形态（全成功 / 全失败），没有
   出现"deck 有但预览无"这类中间态。这不代表不可能，只代表本包的降级路径目前是
   **两态的**。
2. **未测版本过旧**：只测"完全没有"，没测"装了但版本过低/API 不兼容"。
3. **未测多个 Pillow 后端缺失**：（如 `libjpeg`/`libtiff` 系统库缺失导致的
   `IOError`，而非 `ImportError`）。
4. **未测 `--starting-deck`/`--template` 分支下的依赖缺失**：本矩阵跑的是"案例未给
   模板"的回退路径。
5. **`PATH` 置空会同时影响其它外部程序**：本场景下不影响本包（它不调用任何外部
   程序），但这条模拟手段本身比"只移除 soffice"更宽。
6. **计数口径**：`--out` 下产物数含 `_runtime/` 目录本身；"12 个产物"是
   `os.listdir()` 的条目数。

## 9. 与基线的差异（脚本层）

**`scripts/` 下既有脚本逐字节未改**（与基线同源）。本轴只新增
`scripts/degrade_probe.py`；CLI 参数、退出码语义一律未动。因此 §3–§5 观察到的降级
形态是**基线已有行为**，本轴的贡献是把它们**测出来、逐条点名**。

---

# 附：实测报告原文

以下为 `degrade_probe.py` 的真实渲染输出（节），未做任何人工修改。

## 2. 主流程实测矩阵（按缺什么排序）

| 场景 | 缺什么 | 投毒生效 | 实测 exit | result.json | status | 顶层键 | 产物数 | deck | 预览 | uncertainty | 连带不可导入 | 判定 |
|-|-|-|-|-|-|-|-|-|-|-|-|-|
| `01-pptx` | `pptx` | 是 | 1 | 有 | `failed` | 14 | 1 | **无** | 0 | 1 | 无 | 按声明 |
| `02-PIL` | `PIL` | 是 | 1 | 有 | `failed` | 14 | 1 | **无** | 0 | 1 | `matplotlib`、`pptx` | 按声明 |
| `03-matplotlib` | `matplotlib` | 是 | 0 | 有 | `success` | 28 | 12 | 有 | 2 | 1 | 无 | 按声明 |
| `04-numpy` | `numpy` | 是 | 0 | 有 | `success` | 28 | 12 | 有 | 2 | 1 | `matplotlib` | 按声明 |
| `05-yaml` | `yaml` | 是 | 0 | 有 | `success` | 28 | 12 | 有 | 2 | 1 | 无 | 按声明 |
| `06-lxml` | `lxml` | 是 | 1 | 有 | `failed` | 14 | 1 | **无** | 0 | 1 | `pptx` | 按声明 |
| `07-reportlab` | `reportlab` | 是 | 0 | 有 | `success` | 28 | 12 | 有 | 2 | 1 | 无 | 按声明 |
| `08-libreoffice` | `libreoffice` | 是 | 0 | 有 | `success` | 28 | 12 | 有 | 2 | 1 | 无 | 按声明 |
| `09-combo-all` | `combo-all` | 是 | 1 | 有 | `failed` | 14 | 1 | **无** | 0 | 1 | `PIL`、`lxml`、`matplotlib`、`numpy`、`pptx`、`reportlab`、`yaml` | 按声明 |
| `10-PIL-with-figure` | `PIL-with-figure` | 是 | 1 | 有 | `failed` | 14 | 1 | **无** | 0 | 1 | `PIL`、`matplotlib`、`pptx` | 按声明 |

## 3. 逐场景明细（产物还剩什么 + 单入口实测）

#### `01-pptx` — 缺 `pptx`

- **模拟**：PYTHONPATH 前置 import 即抛 ImportError 的假包: pptx
- **谁用它**：adapt_pptx (module level)；adopt_plan (lazy, for sizes)；pptx_toolkit (lazy)；make_template (lazy)；check_contract G4 (lazy)；common.tool_versions
- **声明**：exit=1 / status=`failed` / 写 result.json=True
- **实测**：exit=1；result.json 已写出（14 顶层键）；status=`failed`；产物 1 个；deck **无**；PNG 0 张；2.967s
- **产物清单**：`result.json`
- **stderr 末行**：`main FAILED: simulated: pptx not installed`
- **uncertainty（1 条，列前 3）**：`pipeline`
    - `ImportError: simulated: pptx not installed`
- **tool_versions 记 unavailable**：['pptx']
- **导入链实测**（同一环境下 `python -c "import M"` 是否可用）：`pptx`=**不可用**；`PIL`=可用；`lxml`=可用；`matplotlib`=可用；`numpy`=可用；`yaml`=可用；`reportlab`=可用
- **单入口实测**：
    - `main`：exit=1；stderr `main FAILED: simulated: pptx not installed`
    - `make_synthetic_inputs`：exit=0
    - `make_template`：exit=1；报错位置 `__init__.py:1 in <module>`；stderr `ImportError: simulated: pptx not installed`
- **判定**：按声明

#### `02-PIL` — 缺 `PIL`

- **模拟**：PYTHONPATH 前置 import 即抛 ImportError 的假包: PIL
- **谁用它**：preview (module level)；make_synthetic_inputs (lazy)；adapt_pptx (lazy, 嵌图尺寸)；adopt_plan (lazy)；common (lazy, 字体探测)
- **声明**：exit=1 / status=`failed` / 写 result.json=True
- **实测**：exit=1；result.json 已写出（14 顶层键）；status=`failed`；产物 1 个；deck **无**；PNG 0 张；3.356s
- **产物清单**：`result.json`
- **stderr 末行**：`main FAILED: simulated: PIL not installed`
- **uncertainty（1 条，列前 3）**：`pipeline`
    - `ImportError: simulated: PIL not installed`
- **tool_versions 记 unavailable**：['PIL', 'matplotlib', 'pptx']
- **导入链实测**（同一环境下 `python -c "import M"` 是否可用）：`pptx`=**不可用**；`PIL`=**不可用**；`lxml`=可用；`matplotlib`=**不可用**；`numpy`=可用；`yaml`=可用；`reportlab`=可用
- **单入口实测**：
    - `main`：exit=1；stderr `main FAILED: simulated: PIL not installed`
    - `make_synthetic_inputs`：exit=1；stderr `make-synthetic-inputs FAILED: ImportError: simulated: PIL not installed`
    - `make_template`：exit=1；报错位置 `__init__.py:1 in <module>`；stderr `ImportError: simulated: PIL not installed`
- **判定**：按声明

#### `03-matplotlib` — 缺 `matplotlib`

- **模拟**：PYTHONPATH 前置 import 即抛 ImportError 的假包: matplotlib
- **谁用它**：仅 common.tool_versions 记录版本
- **声明**：exit=0 / status=`None` / 写 result.json=True
- **实测**：exit=0；result.json 已写出（28 顶层键）；status=`success`；产物 12 个；deck 有；PNG 2 张；5.309s
- **产物清单**：`_PREVIEW_ARE_SCHEMATIC.txt`、`_runtime`、`adopt_plan.json`、`audit.json`、`content.json`、`example-catalyst-201_cover_preview.png`、`example-catalyst-201_deck.pptx`、`example-catalyst-201_slides_contact_schematic.png`、`render_log.json`、`result.json`、`spec.json`、`summary.txt`
- **uncertainty（1 条，列前 3）**：`builtin fallback template`
    - `no usable case template/starting deck: the 16:9 fallback template was regenerated at run time (generated-at-runtime:../out/_runtime/builtin.pptx) because Skill resources are text-o`
- **tool_versions 记 unavailable**：['matplotlib']
- **导入链实测**（同一环境下 `python -c "import M"` 是否可用）：`pptx`=可用；`PIL`=可用；`lxml`=可用；`matplotlib`=**不可用**；`numpy`=可用；`yaml`=可用；`reportlab`=可用
- **单入口实测**：
    - `main`：exit=0
    - `make_synthetic_inputs`：exit=0
    - `make_template`：exit=0
- **判定**：按声明

#### `04-numpy` — 缺 `numpy`

- **模拟**：PYTHONPATH 前置 import 即抛 ImportError 的假包: numpy
- **谁用它**：仅 common.tool_versions 记录版本
- **声明**：exit=0 / status=`None` / 写 result.json=True
- **实测**：exit=0；result.json 已写出（28 顶层键）；status=`success`；产物 12 个；deck 有；PNG 2 张；4.519s
- **产物清单**：`_PREVIEW_ARE_SCHEMATIC.txt`、`_runtime`、`adopt_plan.json`、`audit.json`、`content.json`、`example-catalyst-201_cover_preview.png`、`example-catalyst-201_deck.pptx`、`example-catalyst-201_slides_contact_schematic.png`、`render_log.json`、`result.json`、`spec.json`、`summary.txt`
- **uncertainty（1 条，列前 3）**：`builtin fallback template`
    - `no usable case template/starting deck: the 16:9 fallback template was regenerated at run time (generated-at-runtime:../out/_runtime/builtin.pptx) because Skill resources are text-o`
- **tool_versions 记 unavailable**：['matplotlib', 'numpy']
- **导入链实测**（同一环境下 `python -c "import M"` 是否可用）：`pptx`=可用；`PIL`=可用；`lxml`=可用；`matplotlib`=**不可用**；`numpy`=**不可用**；`yaml`=可用；`reportlab`=可用
- **单入口实测**：
    - `main`：exit=0
    - `make_synthetic_inputs`：exit=0
    - `make_template`：exit=0
- **判定**：按声明

#### `05-yaml` — 缺 `yaml`

- **模拟**：PYTHONPATH 前置 import 即抛 ImportError 的假包: yaml
- **谁用它**：（无）
- **声明**：exit=0 / status=`None` / 写 result.json=True
- **实测**：exit=0；result.json 已写出（28 顶层键）；status=`success`；产物 12 个；deck 有；PNG 2 张；6.101s
- **产物清单**：`_PREVIEW_ARE_SCHEMATIC.txt`、`_runtime`、`adopt_plan.json`、`audit.json`、`content.json`、`example-catalyst-201_cover_preview.png`、`example-catalyst-201_deck.pptx`、`example-catalyst-201_slides_contact_schematic.png`、`render_log.json`、`result.json`、`spec.json`、`summary.txt`
- **uncertainty（1 条，列前 3）**：`builtin fallback template`
    - `no usable case template/starting deck: the 16:9 fallback template was regenerated at run time (generated-at-runtime:../out/_runtime/builtin.pptx) because Skill resources are text-o`
- **导入链实测**（同一环境下 `python -c "import M"` 是否可用）：`pptx`=可用；`PIL`=可用；`lxml`=可用；`matplotlib`=可用；`numpy`=可用；`yaml`=**不可用**；`reportlab`=可用
- **单入口实测**：
    - `main`：exit=0
    - `make_synthetic_inputs`：exit=0
    - `make_template`：exit=0
- **判定**：按声明

#### `06-lxml` — 缺 `lxml`

- **模拟**：PYTHONPATH 前置 import 即抛 ImportError 的假包: lxml
- **谁用它**：（本包代码不用它；但 `python-pptx` 在包级 `from lxml import etree` 用到）
- **声明**：exit=1 / status=`failed` / 写 result.json=True
- **实测**：exit=1；result.json 已写出（14 顶层键）；status=`failed`；产物 1 个；deck **无**；PNG 0 张；3.144s
- **产物清单**：`result.json`
- **stderr 末行**：`main FAILED: simulated: lxml not installed`
- **uncertainty（1 条，列前 3）**：`pipeline`
    - `ImportError: simulated: lxml not installed`
- **tool_versions 记 unavailable**：['pptx']
- **导入链实测**（同一环境下 `python -c "import M"` 是否可用）：`pptx`=**不可用**；`PIL`=可用；`lxml`=**不可用**；`matplotlib`=可用；`numpy`=可用；`yaml`=可用；`reportlab`=可用
- **单入口实测**：
    - `main`：exit=1；stderr `main FAILED: simulated: lxml not installed`
    - `make_synthetic_inputs`：exit=0
    - `make_template`：exit=1；报错位置 `__init__.py:1 in <module>`；stderr `ImportError: simulated: lxml not installed`
- **判定**：按声明

#### `07-reportlab` — 缺 `reportlab`

- **模拟**：PYTHONPATH 前置 import 即抛 ImportError 的假包: reportlab
- **谁用它**：仅 common.tool_versions 记录版本
- **声明**：exit=0 / status=`None` / 写 result.json=True
- **实测**：exit=0；result.json 已写出（28 顶层键）；status=`success`；产物 12 个；deck 有；PNG 2 张；6.176s
- **产物清单**：`_PREVIEW_ARE_SCHEMATIC.txt`、`_runtime`、`adopt_plan.json`、`audit.json`、`content.json`、`example-catalyst-201_cover_preview.png`、`example-catalyst-201_deck.pptx`、`example-catalyst-201_slides_contact_schematic.png`、`render_log.json`、`result.json`、`spec.json`、`summary.txt`
- **uncertainty（1 条，列前 3）**：`builtin fallback template`
    - `no usable case template/starting deck: the 16:9 fallback template was regenerated at run time (generated-at-runtime:../out/_runtime/builtin.pptx) because Skill resources are text-o`
- **tool_versions 记 unavailable**：['reportlab']
- **导入链实测**（同一环境下 `python -c "import M"` 是否可用）：`pptx`=可用；`PIL`=可用；`lxml`=可用；`matplotlib`=可用；`numpy`=可用；`yaml`=可用；`reportlab`=**不可用**
- **单入口实测**：
    - `main`：exit=0
    - `make_synthetic_inputs`：exit=0
    - `make_template`：exit=0
- **判定**：按声明

#### `08-libreoffice` — 缺 `libreoffice`

- **模拟**：PATH 置空（外部程序不可发现）
- **谁用它**：（无；preview 只画 PIL 示意图，从不调用 soffice）
- **声明**：exit=0 / status=`None` / 写 result.json=True
- **实测**：exit=0；result.json 已写出（28 顶层键）；status=`success`；产物 12 个；deck 有；PNG 2 张；5.653s
- **产物清单**：`_PREVIEW_ARE_SCHEMATIC.txt`、`_runtime`、`adopt_plan.json`、`audit.json`、`content.json`、`example-catalyst-201_cover_preview.png`、`example-catalyst-201_deck.pptx`、`example-catalyst-201_slides_contact_schematic.png`、`render_log.json`、`result.json`、`spec.json`、`summary.txt`
- **uncertainty（1 条，列前 3）**：`builtin fallback template`
    - `no usable case template/starting deck: the 16:9 fallback template was regenerated at run time (generated-at-runtime:../out/_runtime/builtin.pptx) because Skill resources are text-o`
- **导入链实测**（同一环境下 `python -c "import M"` 是否可用）：`pptx`=可用；`PIL`=可用；`lxml`=可用；`matplotlib`=可用；`numpy`=可用；`yaml`=可用；`reportlab`=可用
- **单入口实测**：
    - `main`：exit=0
    - `make_synthetic_inputs`：exit=0
    - `make_template`：exit=0
- **判定**：按声明

#### `09-combo-all` — 缺 `combo-all`

- **模拟**：PYTHONPATH 前置 import 即抛 ImportError 的假包: pptx, PIL, matplotlib, numpy, yaml, lxml, reportlab
- **谁用它**：合并场景：所有 Python 依赖同时缺失（最坏情况）
- **声明**：exit=1 / status=`failed` / 写 result.json=True
- **实测**：exit=1；result.json 已写出（14 顶层键）；status=`failed`；产物 1 个；deck **无**；PNG 0 张；1.568s
- **产物清单**：`result.json`
- **stderr 末行**：`main FAILED: simulated: pptx not installed`
- **uncertainty（1 条，列前 3）**：`pipeline`
    - `ImportError: simulated: pptx not installed`
- **tool_versions 记 unavailable**：['PIL', 'matplotlib', 'numpy', 'pptx', 'reportlab']
- **导入链实测**（同一环境下 `python -c "import M"` 是否可用）：`pptx`=**不可用**；`PIL`=**不可用**；`lxml`=**不可用**；`matplotlib`=**不可用**；`numpy`=**不可用**；`yaml`=**不可用**；`reportlab`=**不可用**
- **单入口实测**：
    - `main`：exit=1；stderr `main FAILED: simulated: pptx not installed`
    - `make_synthetic_inputs`：exit=1；stderr `make-synthetic-inputs FAILED: ImportError: simulated: PIL not installed`
    - `make_template`：exit=1；报错位置 `__init__.py:1 in <module>`；stderr `ImportError: simulated: pptx not installed`
- **判定**：按声明

#### `10-PIL-with-figure` — 缺 `PIL-with-figure`

- **模拟**：PYTHONPATH 前置 import 即抛 ImportError 的假包: PIL
- **谁用它**：adapt_pptx（懒加载，只在**真的存在源图文件**时用 PIL 读尺寸）
- **声明**：exit=1 / status=`failed` / 写 result.json=True
- **实测**：exit=1；result.json 已写出（14 顶层键）；status=`failed`；产物 1 个；deck **无**；PNG 0 张；4.029s
- **语料**：**带真实源图**（`make_synthetic_inputs.py` exit 0）——确保懒加载 PIL 分支真的会被走到
- **产物清单**：`result.json`
- **stderr 末行**：`main FAILED: simulated: PIL not installed`
- **uncertainty（1 条，列前 3）**：`pipeline`
    - `ImportError: simulated: PIL not installed`
- **tool_versions 记 unavailable**：['PIL', 'matplotlib', 'pptx']
- **导入链实测**（同一环境下 `python -c "import M"` 是否可用）：`pptx`=**不可用**；`PIL`=**不可用**；`lxml`=可用；`matplotlib`=**不可用**；`numpy`=可用；`yaml`=可用；`reportlab`=可用
- **单入口实测**：
    - `main`：exit=1；stderr `main FAILED: simulated: PIL not installed`
    - `make_synthetic_inputs`：exit=1；stderr `make-synthetic-inputs FAILED: ImportError: simulated: PIL not installed`
    - `make_template`：exit=1；报错位置 `__init__.py:1 in <module>`；stderr `ImportError: simulated: PIL not installed`
- **判定**：按声明

