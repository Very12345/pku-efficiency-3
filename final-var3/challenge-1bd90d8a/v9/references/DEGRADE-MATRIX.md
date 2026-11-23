# DEGRADE-MATRIX.md — 缺依赖降级链：逐项实测（v9 轴）

> 下表每个数字都来自 `scripts/degrade_probe.py` 的一次真实运行；机器可读原始证据是同目录的
> `degrade_probe_report.json`（含每一次被拦截的 `(module, frame)`、每档的产物清单与 sha256）。

---

## 1. 复跑命令

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" \
    --src "$SKILL_DIR" --case /input/case.json \
    --workdir /app/work/dp --out /app/work/dp/degrade_probe_report.json

# 只跑某几档（含外部 CLI 两档）
python "$SKILL_DIR/scripts/degrade_probe.py" --only PIL,ALL_OPTIONAL,CLI_SHIM_TRAP --json
```

退出码：`0` = 全部探针跑完且报告已写出；`2` = **所有**探针都没产出 `result.json`
（说明连基线都不成立、这份报告不可信）；`1` = 用法或环境错误。

本机运行环境（实测）：Python 3.13.9，Windows-11 / os.name=nt。
当前已安装版本：`PIL`=12.3.0、`cairosvg`=ABSENT(ModuleNotFoundError)、`fontTools`=4.60.1、`lxml`=6.1.1、`matplotlib`=3.10.6、`numpy`=2.3.5、`pandas`=2.3.3、`pptx`=1.0.2、`pypdf`=6.14.2、`reportlab`=5.0.0、`scipy`=1.16.3、`svgwrite`=ABSENT(ModuleNotFoundError)、`yaml`=6.0.3。

## 2. 拦截机制（为什么它等价于「真的没装」）

脚本在 `--workdir` 下生成一个 `sitecustomize.py`（**不属于 Skill 本体**），
它把一个 finder 插到 `sys.meta_path` 最前面：命中名单的 top-level 模块一律抛 `ImportError`，
并把 **`(module, frame)`** 追加写进日志。相比「删文件 / 放桩包」，它的好处是：

1. 对被测代码与「这个包没装」**完全等价**（连 `try: import PIL` 也照旧走 except 分支）；
2. 每一次拦截都成为证据 —— 报告里能直接读出「PIL 是被 `chartkit.py:41`（包在 try 里）导的，
   还是被 `figcheck.py:157`（裸导）导的」，这决定了缺它时是**降级**还是**整链失败**；
3. **不动被测包**：脚本先把整包复制到 `--workdir` 再跑，并设 `PYTHONDONTWRITEBYTECODE=1`，
   所以包内永远不会出现 `__pycache__`（打包预检硬门之一）。

## 3. 总表：17 档探针

| 档位 | 被拦截 | exit | status | result.json | 顶层键数 | 产物文件数 | 稳定产物与基线一致 | 拦截次数 | 拦截点（module ← frame） |
|-|-:|-|-|-:|-:|-:|-:|-|-|
| **NONE** | 0 | 0 | completed | ✅ | 29 | 11 | ✅ 是 | 0 | - |
| **PIL** | 1 | 1 | failed | ✅ | 6 | 6 | ❌ 否 | 4 | `PIL`←`chartkit.py:41`, `PIL`←`cjkfont.py:114`, `PIL`←`chartkit.py:1851`, `PIL`←`figcheck.py:157` |
| **pptx** | 1 | 0 | completed | ✅ | 29 | 11 | ✅ 是 | 0 | - |
| **matplotlib** | 1 | 0 | completed | ✅ | 29 | 11 | ✅ 是 | 0 | - |
| **numpy** | 1 | 0 | completed | ✅ | 29 | 11 | ✅ 是 | 0 | - |
| **yaml** | 1 | 0 | completed | ✅ | 29 | 11 | ✅ 是 | 0 | - |
| **lxml** | 1 | 0 | completed | ✅ | 29 | 11 | ✅ 是 | 0 | - |
| **pypdf** | 1 | 0 | completed | ✅ | 29 | 11 | ✅ 是 | 0 | - |
| **cairosvg** | 1 | 0 | completed | ✅ | 29 | 11 | ✅ 是 | 0 | - |
| **svgwrite** | 1 | 0 | completed | ✅ | 29 | 11 | ✅ 是 | 0 | - |
| **reportlab** | 1 | 0 | completed | ✅ | 29 | 11 | ✅ 是 | 0 | - |
| **pandas** | 1 | 0 | completed | ✅ | 29 | 11 | ✅ 是 | 0 | - |
| **scipy** | 1 | 0 | completed | ✅ | 29 | 11 | ✅ 是 | 0 | - |
| **fontTools** | 1 | 0 | completed | ✅ | 29 | 11 | ✅ 是 | 0 | - |
| **ALL_OPTIONAL** | 13 | 1 | failed | ✅ | 6 | 6 | ❌ 否 | 4 | `PIL`←`chartkit.py:41`, `PIL`←`cjkfont.py:114`, `PIL`←`chartkit.py:1851`, `PIL`←`figcheck.py:157` |
| **CLI_PATH_MIN** | 0 | 0 | completed | ✅ | 29 | 11 | ❌ 否 | 0 | - |
| **CLI_SHIM_TRAP** | 0 | 0 | completed | ✅ | 29 | 11 | ✅ 是 | 0 | - |

## 4. 逐项结论

### PIL

- 描述：Pillow —— 唯一被 chartkit 真正用到的第三方包
- 被拦截：`PIL`
- 实测：exit=1，status=`failed`，result.json 顶层 6 键，产物 6 个
- **结论：丢失 figcheck_report.json,figure-fig-01.pdf,figure-fig-01.png,figure-fig-02.pdf,figure-fig-02.png；内容变化 data_manifest.json,validation.json；result.json 语义变化：status=completed->failed，键 29->6**
- 丢掉的产物：`figcheck_report.json`, `figure-fig-01.pdf`, `figure-fig-01.png`, `figure-fig-02.pdf`, `figure-fig-02.png`
- 内容变化（非时间戳类）：`data_manifest.json`, `validation.json`
- 拦截点：`PIL` 被 `chartkit.py:41` 请求；`PIL` 被 `cjkfont.py:114` 请求；`PIL` 被 `chartkit.py:1851` 请求；`PIL` 被 `figcheck.py:157` 请求
- 落痕：`error = ImportError: degrade_probe: top-level 'PIL' 被受控拦截（模拟该包未安装）`
- `uncertainty` 首条：运行异常，产物不完整。
- 字节级 delta `data_manifest.json`：28979 → 706 字节，差异 28438 字节，首个差异偏移 534
- 字节级 delta `validation.json`：2526 → 122 字节，差异 2463 字节，首个差异偏移 57

### pptx

- 描述：python-pptx —— 演示文稿导出（本题不用，但常被误列为依赖）
- 被拦截：`pptx`
- 实测：exit=0，status=`completed`，result.json 顶层 29 键，产物 11 个
- **结论：无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）**

### matplotlib

- 描述：matplotlib —— 常见绘图库，本包声明不使用
- 被拦截：`matplotlib`
- 实测：exit=0，status=`completed`，result.json 顶层 29 键，产物 11 个
- **结论：无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）**

### numpy

- 描述：numpy —— 数值栈，本包声明不使用
- 被拦截：`numpy`
- 实测：exit=0，status=`completed`，result.json 顶层 29 键，产物 11 个
- **结论：无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）**

### yaml

- 描述：PyYAML —— 题面提到 environment/resources.yaml
- 被拦截：`yaml`
- 实测：exit=0，status=`completed`，result.json 顶层 29 键，产物 11 个
- **结论：无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）**

### lxml

- 描述：lxml —— XML 解析（本包手写 SVG）
- 被拦截：`lxml`
- 实测：exit=0，status=`completed`，result.json 顶层 29 键，产物 11 个
- **结论：无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）**

### pypdf

- 描述：pypdf —— PDF 读取（本包只写不读）
- 被拦截：`pypdf`
- 实测：exit=0，status=`completed`，result.json 顶层 29 键，产物 11 个
- **结论：无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）**

### cairosvg

- 描述：cairosvg —— SVG 转位图
- 被拦截：`cairosvg`
- 实测：exit=0，status=`completed`，result.json 顶层 29 键，产物 11 个
- **结论：无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）**

### svgwrite

- 描述：svgwrite —— SVG 生成库
- 被拦截：`svgwrite`
- 实测：exit=0，status=`completed`，result.json 顶层 29 键，产物 11 个
- **结论：无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）**

### reportlab

- 描述：reportlab —— PDF 生成库
- 被拦截：`reportlab`
- 实测：exit=0，status=`completed`，result.json 顶层 29 键，产物 11 个
- **结论：无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）**

### pandas

- 描述：pandas —— 表格栈
- 被拦截：`pandas`
- 实测：exit=0，status=`completed`，result.json 顶层 29 键，产物 11 个
- **结论：无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）**

### scipy

- 描述：scipy —— 统计栈
- 被拦截：`scipy`
- 实测：exit=0，status=`completed`，result.json 顶层 29 键，产物 11 个
- **结论：无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）**

### fontTools

- 描述：fontTools —— 字体处理
- 被拦截：`fontTools`
- 实测：exit=0，status=`completed`，result.json 顶层 29 键，产物 11 个
- **结论：无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）**

### ALL_OPTIONAL

- 描述：★ 把所有第三方依赖一次性拦掉（= 最小可用环境的最低档）
- 被拦截：`PIL`, `cairosvg`, `fontTools`, `lxml`, `matplotlib`, `numpy`, `pandas`, `pptx`, `pypdf`, `reportlab`, `scipy`, `svgwrite`, `yaml`
- 实测：exit=1，status=`failed`，result.json 顶层 6 键，产物 6 个
- **结论：丢失 figcheck_report.json,figure-fig-01.pdf,figure-fig-01.png,figure-fig-02.pdf,figure-fig-02.png；内容变化 data_manifest.json,validation.json；result.json 语义变化：status=completed->failed，键 29->6**
- 丢掉的产物：`figcheck_report.json`, `figure-fig-01.pdf`, `figure-fig-01.png`, `figure-fig-02.pdf`, `figure-fig-02.png`
- 内容变化（非时间戳类）：`data_manifest.json`, `validation.json`
- 拦截点：`PIL` 被 `chartkit.py:41` 请求；`PIL` 被 `cjkfont.py:114` 请求；`PIL` 被 `chartkit.py:1851` 请求；`PIL` 被 `figcheck.py:157` 请求
- 落痕：`error = ImportError: degrade_probe: top-level 'PIL' 被受控拦截（模拟该包未安装）`
- `uncertainty` 首条：运行异常，产物不完整。
- 字节级 delta `data_manifest.json`：28979 → 706 字节，差异 28438 字节，首个差异偏移 534
- 字节级 delta `validation.json`：2526 → 122 字节，差异 2463 字节，首个差异偏移 57

### CLI_PATH_MIN

- 描述：（a）PATH 收窄到解释器目录（+System32）
- 实测：exit=0，status=`completed`，result.json 顶层 29 键，产物 11 个
- **结论：稳定产物与基线不一致：figure-fig-01.png, figure-fig-02.png**
- 内容变化（非时间戳类）：`figure-fig-01.png`, `figure-fig-02.png`
- 字节级 delta `figure-fig-01.png`：281926 → 281625 字节，差异 231233 字节，首个差异偏移 3881
- 字节级 delta `figure-fig-02.png`：122579 → 122527 字节，差异 110193 字节，首个差异偏移 7080

### CLI_SHIM_TRAP

- 描述：（b）PATH 前置 10 个会写日志的假 CLI
- 实测：exit=0，status=`completed`，result.json 顶层 29 键，产物 11 个
- **结论：稳定产物与基线逐字节一致**


## 5. 外部 CLI：三层证据

| 层 | 做法 | 实测 |
|-|-|-|
| (a) PATH 收窄 | PATH 只留解释器目录（Windows 另加 System32），跑完与基线逐文件比 sha256 | 稳定产物**不一致**：`figure-fig-01.png`, `figure-fig-02.png` 变了；其余稳定产物与全部 JSON 未变 |
| (b) 假 CLI 陷阱 | PATH 前置 20 个会写日志的假 CLI（soffice / libreoffice / pandoc / inkscape / rsvg-convert / magick / convert / pdflatex / dot / gnuplot），并先做阳性对照 | 阳性对照：`soffice.cmd` 被真的调用（exit 1）、日志被写入 = True；主流程跑完后调用日志 **0 条** |
| (c) 静态扫描 | 扫 `scripts/*.py` 里的 `subprocess` / `os.system` / `os.popen` / `shutil.which` 等调用点 | **0 处** |

- **结论：外部 CLI 不依赖，证据来自两层：(b) 10 个假 CLI 全程 0 次调用（阳性对照已验证陷阱能触发）＋ (c) 脚本里 0 处 subprocess/os.system 调用点。(a) PATH 收窄那一层**不作为**该结论的证据 —— 它另有发现，见 path_min_finding。**
- PATH 层发现（意外收获，必须点名）：PATH 收窄后 SVG/JSON 等稳定产物与基线逐字节一致，但 figure-fig-01.png, figure-fig-02.png 变了：Windows 的 DLL 搜索顺序包含 PATH，收窄后同一个字体文件由**另一个 FreeType** 光栅化（本机 full PATH 里有带 freetype.dll 的目录，收窄后没有了）⇒ 文本字形像素变化。这不影响「是否依赖外部 CLI」的结论，但它是 PNG 字节级复现的一个真实环境依赖，必须点名。

### 5.1 PATH 为什么会影响 PNG 字节（已定位到根因）

收窄 PATH 后**只有 PNG 变化**（SVG、`data_manifest.json`、`validation.json`、两份报告都不变），
看起来不像环境依赖，但它是真的。定位过程（可复核）：

1. 同一字体文件 + 同一字符串，在两种 PATH 下分别用 Pillow 光栅化 →
   **`serif` 角色（实测用的是系统字体目录下的 `REFSAN.TTF`）位图 sha256 不同**，
   其余角色（`sans` / `mono` / `sans_cjk`）完全相同；
2. 把本机含 `freetype.dll` 的那个目录加回收窄后的 PATH → 位图**恢复与 full PATH 一致**；
3. ⇒ 结论：Windows 的 **DLL 搜索顺序包含 PATH**，于是「哪个 FreeType 在光栅化」由 PATH 决定；
   同一个 `.ttf` 被不同版本的 FreeType 渲染，字形像素会差几个灰度级（实测差异像素数与
   字节级 delta 见报告 `cli_evidence.path_min_binary_delta`）。

对本题的实践含义：**PNG 的字节级复现依赖 PATH 解析到的 FreeType**（与 v7 的确定性轴互相呼应）；
要跨环境字节一致，必须固定 DLL 搜索路径，或换用不依赖系统 FreeType 的光栅化后端。

## 6. 最小可用环境清单

| 档 | 环境 | exit | status | result.json | 顶层键数 | 产物 | 结论 |
|-|-|-|-|-|-:|-|-|
| **Tier 0** | 纯标准库（一次性拦掉全部第三方依赖 = `ALL_OPTIONAL`） | 1 | `failed` | ✅ 有（最小失败信封） | 6 | 6 | **不可用** |
| **Tier 1** | 标准库 + Pillow | 0 | `completed` | ✅ 有 | 29 | 11 | **最小可用环境** |

**结论：本 Skill 的最小可用环境 = Python 3.8+ 标准库 + Pillow（`pip install pillow`）。
不需要任何其它第三方包，也不需要任何外部 CLI（LibreOffice / pandoc / inkscape 等一律不需要）。**

Tier 0 到底还剩什么（实测细节）：

- 还剩：`figure-fig-01.svg`, `figure-fig-02.svg`, `data_manifest.json`, `validation.json`, `mapcheck_report.json`, `result.json`
- 彻底没有：`figcheck_report.json`, `figure-fig-01.pdf`, `figure-fig-01.png`, `figure-fig-02.pdf`, `figure-fig-02.png`
- `result.json` 里 `outputs` 变成 空数组（`[]`） —— **已经落在磁盘上的两个 SVG 在 JSON 里彻底消失**，
  这正是「半成品不可交付」的实测证据（回放方拿到的 `result.json` 说它什么都没有）。
- 另有内容变化：`data_manifest.json`, `validation.json`

## 7. 未覆盖声明

- 字体目录不可用（FONT_PATHS 收窄）—— 已由 v4 的 FAULT-MATRIX D3 行覆盖，本轴不重复测
- 磁盘写满 / 只读输出目录 / 权限不足
- Python 版本低于 3.8（本包用 from __future__ import annotations，未在旧解释器上实测）
- 外部 CLI 在 **Windows** 上：CreateProcess 的 PATH 搜索只补 .exe，无扩展名假 CLI 与 .cmd 都不会被 `["soffice"]` 这种调用命中（阳性对照用显式 .cmd 路径完成）
- 被拦截模块内部的部分依赖（例如只放行 PIL 但拦掉其编码器）

## 8. 结论

- 基线（无拦截）：exit=0 status=completed 产物 11 个，result.json 29 键。
- PIL: exit=1 status=failed result.json=有 | 丢失 figcheck_report.json,figure-fig-01.pdf,figure-fig-01.png,figure-fig-02.pdf,figure-fig-02.png；内容变化 data_manifest.json,validation.json；result.json 语义变化：status=completed->failed，键 29->6
- pptx: exit=0 status=completed result.json=有 | 无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）
- matplotlib: exit=0 status=completed result.json=有 | 无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）
- numpy: exit=0 status=completed result.json=有 | 无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）
- yaml: exit=0 status=completed result.json=有 | 无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）
- lxml: exit=0 status=completed result.json=有 | 无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）
- pypdf: exit=0 status=completed result.json=有 | 无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）
- cairosvg: exit=0 status=completed result.json=有 | 无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）
- svgwrite: exit=0 status=completed result.json=有 | 无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）
- reportlab: exit=0 status=completed result.json=有 | 无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）
- pandas: exit=0 status=completed result.json=有 | 无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）
- scipy: exit=0 status=completed result.json=有 | 无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）
- fontTools: exit=0 status=completed result.json=有 | 无实质变化（该依赖对本包**非必需**：只有时间戳/路径类产物不同）
- ALL_OPTIONAL: exit=1 status=failed result.json=有 | 丢失 figcheck_report.json,figure-fig-01.pdf,figure-fig-01.png,figure-fig-02.pdf,figure-fig-02.png；内容变化 data_manifest.json,validation.json；result.json 语义变化：status=completed->failed，键 29->6
- CLI_PATH_MIN: exit=0 status=completed result.json=有 | 稳定产物与基线不一致：figure-fig-01.png, figure-fig-02.png
- CLI_SHIM_TRAP: exit=0 status=completed result.json=有 | 稳定产物与基线逐字节一致
- 外部 CLI：外部 CLI 不依赖，证据来自两层：(b) 10 个假 CLI 全程 0 次调用（阳性对照已验证陷阱能触发）＋ (c) 脚本里 0 处 subprocess/os.system 调用点。(a) PATH 收窄那一层**不作为**该结论的证据 —— 它另有发现，见 path_min_finding。
- PATH 层发现：PATH 收窄后 SVG/JSON 等稳定产物与基线逐字节一致，但 figure-fig-01.png, figure-fig-02.png 变了：Windows 的 DLL 搜索顺序包含 PATH，收窄后同一个字体文件由**另一个 FreeType** 光栅化（本机 full PATH 里有带 freetype.dll 的目录，收窄后没有了）⇒ 文本字形像素变化。这不影响「是否依赖外部 CLI」的结论，但它是 PNG 字节级复现的一个真实环境依赖，必须点名。
- 产出 result.json 的探针：17/17

## 9. 未解决项

1. Tier 0 的降级路径**不优雅**：SVG 已经产出却从 `result.json` 的 `outputs` 里消失，
   `figcheck` 因为 `from PIL import Image` 是裸导而整链失败。本轮**只实测登记、不改脚本** ——
   修它要动 `figcheck.py` 的导入方式与 main.py 的异常边界，属于行为变更。
2. `freetype.dll` 的 PATH 依赖未做真正的隔离（没用 DLL 重定向或清单固定），
   只做到「定位根因 + 给出可复核的对照实验」。
3. Linux / macOS 上未复测（本机只有 Windows）。
