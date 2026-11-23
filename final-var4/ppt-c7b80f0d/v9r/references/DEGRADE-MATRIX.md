# DEGRADE-MATRIX.md — 缺依赖降级链（**逐项实测**）

> 本文件由 `scripts/degrade_probe.py --emit-md` 从**真实运行**生成。每个场景在子进程里用受控导入拦截（`sys.meta_path` finder 抛 `ModuleNotFoundError`）模拟缺库，然后跑**未经修改的**端到端入口。
> 原始记录见 `references/degrade-matrix-data.json`。

## 0. 运行命令与判据

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" --out <探针目录> \
  --emit-md "$SKILL_DIR/references/DEGRADE-MATRIX.md"
```

| 退出码 | 含义 |
|-|-|
| 0 | 测量完成：基线对照写出 `result.json`，且没有场景是**静默降级** |
| 1 | 有场景静默降级（自称 `completed`，但 deck 或预览已经没了） |
| 2 | 参数/输入错误 |
| 3 | 基线对照本身失败（探针环境有问题） |

判定口径：`full success`（写出 result.json 且 status=completed、deck 与预览都在）／`honest partial/failed`（写出 result.json 但如实降级）／`crash (no result.json)`（导入期就失败）／**`silent degradation`**（自称完成但产物残缺）。

## 1. 场景总表（实测）

| 场景 | 屏蔽 | exit | result.json | status | deck 落盘 | 预览数 | 重建图 | uncertainty | 剩余产物 | 判定 |
|-|-|-|-|-|-|-|-|-|-|-|
| S0-baseline | （无） | 0 | 是 | completed | 是 | 7 | 2 | 1 | 13 | full success |
| S1-no-pptx | pptx | 1 | **否** | — | **否** | 0 | 0 | 0 | 0 | crash (no result.json) |
| S2-no-PIL | PIL | 1 | **否** | — | **否** | 0 | 0 | 0 | 0 | crash (no result.json) |
| S3-no-matplotlib | matplotlib | 0 | 是 | completed | 是 | 7 | 0 | 2 | 11 | full success |
| S4-no-numpy | numpy | 0 | 是 | completed | 是 | 7 | 0 | 2 | 11 | full success |
| S5-no-yaml | yaml | 0 | 是 | completed | 是 | 7 | 2 | 1 | 13 | full success |
| S6-no-pptx-no-PIL | pptx, PIL | 1 | **否** | — | **否** | 0 | 0 | 0 | 0 | crash (no result.json) |
| S7-no-soffice | （无） | 0 | 是 | completed | 是 | 7 | 2 | 1 | 13 | full success |

注意 S3/S4：`status` 仍是 `completed`，但 `uncertainty` 从 1 条升到 2 条、重建图文件（`chart-*.png/svg`）不再落盘 —— 降级**被如实记录**，所以判 `full success` 而不是 `silent degradation`；这正是本探针要区分的两种情况。

汇总：场景 8 个；`full success` 5；`honest partial/failed` 0；`crash` 3；**`silent degradation` 0**。

## 2. 逐场景细节（产物还剩什么）

### S0-baseline · 对照：什么都不屏蔽

- 屏蔽：`（无）`；exit=`0`；`soffice` 在 PATH 上：False
- `result.json`：status=completed，deck=academic_deck.pptx（落盘=True），previews=7（落盘 7），重建图记录=1 / 落盘文件=2，rendered_with=`pil-approximation (no PowerPoint/LibreOffice attached)`，self_check=True
  - uncertainty：`declared template 'template-example.pptx' was not usable — built-in 16:9 academic layout used instead (deck.template.kind=builtin); run make_template.py if a real .pptx t`
- 输出目录剩余产物（13 个）：`academic_deck.pptx, chart-Fig_1.png, chart-Fig_1.svg, evidence_map.json, evidence_mapping.md, preview-approx-001.png, preview-approx-002.png, preview-approx-003.png, preview-approx-004.png, preview-approx-005.png, preview-approx-006.png, preview-approx-cover.png, result.json`
- 末尾输出：`self_check   : OK | artifacts    : <PROBE_DIR>\scenarios\S0-baseline\out | ================================================================`

### S1-no-pptx · 缺 python-pptx

- 屏蔽：`['pptx']`；exit=`1`；`soffice` 在 PATH 上：False
- 失败导入：`ModuleNotFoundError: No module named 'pptx' (blocked by degrade_probe)`
- **没有 `result.json`** —— 主流程在产出任何评分产物之前就结束了
- 输出目录剩余产物（0 个）：`（空）`
- 末尾输出：`        "No module named '%s' (blocked by degrade_probe)" % fullname, |         name=fullname) | ModuleNotFoundError: No module named 'pptx' (blocked by degrade_probe)`

### S2-no-PIL · 缺 Pillow(PIL)

- 屏蔽：`['PIL']`；exit=`1`；`soffice` 在 PATH 上：False
- 失败导入：`ModuleNotFoundError: No module named 'PIL' (blocked by degrade_probe)`
- **没有 `result.json`** —— 主流程在产出任何评分产物之前就结束了
- 输出目录剩余产物（0 个）：`（空）`
- 末尾输出：`        "No module named '%s' (blocked by degrade_probe)" % fullname, |         name=fullname) | ModuleNotFoundError: No module named 'PIL' (blocked by degrade_probe)`

### S3-no-matplotlib · 缺 matplotlib

- 屏蔽：`['matplotlib']`；exit=`0`；`soffice` 在 PATH 上：False
- `result.json`：status=completed，deck=academic_deck.pptx（落盘=True），previews=7（落盘 7），重建图记录=1 / 落盘文件=0，rendered_with=`pil-approximation (no PowerPoint/LibreOffice attached)`，self_check=True
  - uncertainty：`declared template 'template-example.pptx' was not usable — built-in 16:9 academic layout used instead (deck.template.kind=builtin); run make_template.py if a real .pptx t`
  - uncertainty：`reconstructed chart skipped: matplotlib missing: No module named 'matplotlib' (blocked by degrade_probe)`
- 输出目录剩余产物（11 个）：`academic_deck.pptx, evidence_map.json, evidence_mapping.md, preview-approx-001.png, preview-approx-002.png, preview-approx-003.png, preview-approx-004.png, preview-approx-005.png, preview-approx-006.png, preview-approx-cover.png, result.json`
- 末尾输出：`self_check   : OK | artifacts    : <PROBE_DIR>\scenarios\S3-no-matplotlib\out | ================================================================`

### S4-no-numpy · 缺 numpy

- 屏蔽：`['numpy']`；exit=`0`；`soffice` 在 PATH 上：False
- `result.json`：status=completed，deck=academic_deck.pptx（落盘=True），previews=7（落盘 7），重建图记录=1 / 落盘文件=0，rendered_with=`pil-approximation (no PowerPoint/LibreOffice attached)`，self_check=True
  - uncertainty：`declared template 'template-example.pptx' was not usable — built-in 16:9 academic layout used instead (deck.template.kind=builtin); run make_template.py if a real .pptx t`
  - uncertainty：`reconstructed chart skipped: matplotlib missing: No module named 'numpy' (blocked by degrade_probe)`
- 输出目录剩余产物（11 个）：`academic_deck.pptx, evidence_map.json, evidence_mapping.md, preview-approx-001.png, preview-approx-002.png, preview-approx-003.png, preview-approx-004.png, preview-approx-005.png, preview-approx-006.png, preview-approx-cover.png, result.json`
- 末尾输出：`self_check   : OK | artifacts    : <PROBE_DIR>\scenarios\S4-no-numpy\out | ================================================================`

### S5-no-yaml · 缺 PyYAML

- 屏蔽：`['yaml']`；exit=`0`；`soffice` 在 PATH 上：False
- `result.json`：status=completed，deck=academic_deck.pptx（落盘=True），previews=7（落盘 7），重建图记录=1 / 落盘文件=2，rendered_with=`pil-approximation (no PowerPoint/LibreOffice attached)`，self_check=True
  - uncertainty：`declared template 'template-example.pptx' was not usable — built-in 16:9 academic layout used instead (deck.template.kind=builtin); run make_template.py if a real .pptx t`
- 输出目录剩余产物（13 个）：`academic_deck.pptx, chart-Fig_1.png, chart-Fig_1.svg, evidence_map.json, evidence_mapping.md, preview-approx-001.png, preview-approx-002.png, preview-approx-003.png, preview-approx-004.png, preview-approx-005.png, preview-approx-006.png, preview-approx-cover.png, result.json`
- 末尾输出：`self_check   : OK | artifacts    : <PROBE_DIR>\scenarios\S5-no-yaml\out | ================================================================`

### S6-no-pptx-no-PIL · 同时缺 python-pptx 与 Pillow

- 屏蔽：`['pptx', 'PIL']`；exit=`1`；`soffice` 在 PATH 上：False
- 失败导入：`ModuleNotFoundError: No module named 'pptx' (blocked by degrade_probe)`
- **没有 `result.json`** —— 主流程在产出任何评分产物之前就结束了
- 输出目录剩余产物（0 个）：`（空）`
- 末尾输出：`        "No module named '%s' (blocked by degrade_probe)" % fullname, |         name=fullname) | ModuleNotFoundError: No module named 'pptx' (blocked by degrade_probe)`

### S7-no-soffice · PATH 里没有 LibreOffice(soffice)

- 屏蔽：`（无）`；exit=`0`；`soffice` 在 PATH 上：False
- `result.json`：status=completed，deck=academic_deck.pptx（落盘=True），previews=7（落盘 7），重建图记录=1 / 落盘文件=2，rendered_with=`pil-approximation (no PowerPoint/LibreOffice attached)`，self_check=True
  - uncertainty：`declared template 'template-example.pptx' was not usable — built-in 16:9 academic layout used instead (deck.template.kind=builtin); run make_template.py if a real .pptx t`
- 输出目录剩余产物（13 个）：`academic_deck.pptx, chart-Fig_1.png, chart-Fig_1.svg, evidence_map.json, evidence_mapping.md, preview-approx-001.png, preview-approx-002.png, preview-approx-003.png, preview-approx-004.png, preview-approx-005.png, preview-approx-006.png, preview-approx-cover.png, result.json`
- 末尾输出：`self_check   : OK | artifacts    : <PROBE_DIR>\scenarios\S7-no-soffice\out | ================================================================`

## 3. 模块可导入性矩阵（同一屏蔽下逐个 `importlib.import_module`）

| 模块 | S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7 |
|-|-|-|-|-|-|-|-|-|
| `cli_io` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `assetkit` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `deckgen` | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| `ooxml_kit` | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| `preview` | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| `spec_lint` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `export_check` | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| `check_contract` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `make_template` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `make_synthetic_inputs` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `main` | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| `degrade_probe` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

可导入模块数：S0-baseline=12/12；S1-no-pptx=7/12；S2-no-PIL=7/12；S3-no-matplotlib=12/12；S4-no-numpy=12/12；S5-no-yaml=12/12；S6-no-pptx-no-PIL=7/12；S7-no-soffice=12/12

## 4. LibreOffice：文档化能力与实现的差距（如实声明）

## 3.5 依赖关系实测（谁真的依赖谁）

| 探测 | 屏蔽 | 结果 | 说明 |
|-|-|-|-|
| `import pptx` | （无） | OK | 基线：python-pptx 可导入 |
| `import PIL` | （无） | OK | 基线：Pillow 可导入 |
| `import matplotlib` | （无） | OK | 基线：matplotlib 可导入 |
| `import numpy` | （无） | OK | 基线：numpy 可导入 |
| `import yaml` | （无） | OK | 基线：PyYAML 可导入 |
| `import pptx` | PIL | FAIL | python-pptx 是否依赖 Pillow -> `IMPORT_FAIL ModuleNotFoundError: No module named 'PIL' (blocked by degrade_probe)` |
| `import matplotlib` | numpy | FAIL | matplotlib 是否依赖 numpy -> `IMPORT_FAIL ModuleNotFoundError: No module named 'numpy' (blocked by degrade_probe)` |
| `import matplotlib` | PIL | FAIL | matplotlib 是否依赖 Pillow -> `IMPORT_FAIL ModuleNotFoundError: No module named 'PIL' (blocked by degrade_probe)` |
| `import PIL` | pptx | OK | Pillow 是否反向依赖 python-pptx |

> 这张表解释了为什么 S1 与 S2 的可导入性矩阵**完全一样**：`python-pptx` 自己导入 Pillow，因此“缺 Pillow”在这条管线里等价于“缺 python-pptx”。把硬依赖写成两个独立条件是不准确的，准确写法是“python-pptx（含其 Pillow 依赖）”。


- 静态扫描 `scripts/*.py`（11 个文件）：命中 `soffice|libreoffice|LibreOffice` **3 处**，其中疑似真的去调用子进程的 **没有**。
  - `main.py:314`：`rendered_with = "pil-approximation (no PowerPoint/LibreOffice attached)"`
  - `preview.py:6`：`Why honest: without PowerPoint or LibreOffice we cannot run the real rendering`
  - `preview.py:11`：`"pil-approximation (no PowerPoint/LibreOffice)". They are NOT screenshots of the`
- **口径提醒**：本机基线环境里本来就没有 `soffice`（S0 行的 `soffice` 在 PATH 上同样是 False），所以 S7 只是把这件事显式化；「LibreOffice 缺失无影响」的实质证据是上面的**静态扫描（0 处调用）**，不是 S7 本身。
- 环境场景实测：把 `soffice` 从 PATH 去掉后，本次运行的 exit / status / 产物与基线一致（见 §1 的 S7 行）。
- ⇒ **结论（诚实口径）**：LibreOffice 缺失在当前实现里**不构成降级路径**，因为代码从不调用它；SKILL.md 中「有 LibreOffice 时可转真 PDF」是**文档化的目标**而非已实现能力，预览恒为 PIL 近似并如实标注。

## 5. 最小可用环境（由上面的实测反推）

- **硬依赖（实测：缺则主流程连 `result.json` 都写不出）**：`python-pptx`（S1 导入期失败）与其 **Pillow 依赖**（S2 导入期失败；实测 `import pptx` 在屏蔽 PIL 时同样失败）。两者不是"可选回退"，而是 `scripts/deckgen.py` / `scripts/ooxml_kit.py` / `scripts/preview.py` 的模块级导入链。
- **软依赖（实测：缺则可降级，产物形态变化）**：`matplotlib`（S3：重建图跳过，其余产物照常）、`numpy`（S4：只影响 matplotlib 自身）。
- **未被主流程使用（实测：屏蔽后与基线一致）**：`PyYAML`（S5，代码里没有任何 `yaml` 导入）——它属于平台环境清单里的资源，不是本 Skill 的依赖。
- **外部引擎**：LibreOffice 未实现调用，缺失无影响；模板与预览是运行期自生成的文本→二进制流程。
- **最低可用组合（把上面的实测拼起来）**：Python ≥3.8 + `python-pptx` + `Pillow`；要 PDF 素材再加 `PyMuPDF`/`pypdf`/`pdfplumber` 任一；要重建图再加 `matplotlib`。只缺 `matplotlib` 时仍产出完整 `result.json`：`charts` 记录仍在但带 `reason`、重建图文件不落盘（实测 S3/S4 的 `uncertainty` 从 1 条升到 2 条，第 2 条即 `reconstructed chart skipped: …`）。
- **排障顺序建议**：先看 `result.json` 是否存在 → 不存在就先解决 `python-pptx`/`Pillow`；存在但 `status=partial` → 读 `uncertainty`（它逐条写了哪一步降级）；再跑 `export_check.py` / `check_contract.py` 确认契约面。

## 6. 未覆盖声明（如实列出）

- **PDF 解析库未纳入**：`PyMuPDF`/`pypdf`/`pdfplumber` 的缺失降级没有实测，因为自带示例案例的材料是纯文本（`.txt`），PDF 分支不会被走到；要覆盖它需要一份 PDF 素材并屏蔽三个库。
- **未测组合爆炸**：只测了单缺 5 个库 + 一个双缺组合；三缺以上的组合未测。
- **未测操作系统级缺失**：例如系统字体目录为空、只读输出目录、磁盘满；这些属于环境故障，不是依赖缺失。
- **未测 LibreOffice 真实存在时的行为**：本机没有 LibreOffice，因此只能测“不存在”这一侧（见 §4 的静态扫描结论）。
- **未测子进程被中断**（Ctrl-C/超时）时的产物一致性。
- **`--demo` 分支与材料不可读分支未与屏蔽矩阵交叉**（它们由 `failure-modes.md` 的状态一致性条目覆盖）。
