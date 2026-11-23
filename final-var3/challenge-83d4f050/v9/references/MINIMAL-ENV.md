# MINIMAL-ENV.md — 最小可用环境清单（v9 实测推导）

> 本清单**不是**从 `import` 语句抄的，而是从 `scripts/degrade_probe.py` 的 13 行实测里推出的
> （逐行证据见 `references/DEGRADE-MATRIX.md` 与包根 `degrade_report.json`）。
> 本机实测环境：CPython **3.13.9** / win32 / matplotlib 3.10.6 / Pillow 12.3.0。

## 1. 三个档位（按"你要拿到什么"选）

| 档位 | 需要装什么 | 实测能拿到 | 实测状态 |
|-|-|-|-|
| **A. 最小（无第三方依赖）** | 只需 Python 3 | `diagram.svg`（可编辑分层源）· `model.json` · `topology.json` · `legend_audit.json` · `result.json`（含全部审计与不确定性） | exit **2** / `status=partial`（缺 PNG/PDF，`F01_png`/`F01_pdf` 失败） |
| **B. 完整（推荐，评测容器默认近似）** | `pip install matplotlib`（会带上 `numpy` 与 `Pillow`） | 档位 A 的全部 ＋ `diagram.png`（150 dpi）＋ `diagram.pdf`（矢量） | exit **0** / `status=success` |
| **C. 只做 SVG 的显式降级** | 同 A（但显式 `--formats svg`） | 同档位 A | exit **2** / `status=partial`（**有意降级也会被记为 fail**，见 DEGRADE-MATRIX §6） |

```bash
# 档位 B 的一行安装
python3 -m pip install "matplotlib>=3.5"
```

## 2. 逐依赖判定（全部来自实测，不是推测）

| 依赖 | 是否本包直接 import | 实测影响 | 结论 |
|-|-|-|-|
| Python 3 标准库 | 是（`json os re math xml.etree hashlib subprocess argparse`） | — | **必需** |
| `matplotlib` | 是（`scripts/mpl_backend.py`，**运行时按需导入**、失败被捕获） | 缺 → exit 2 / partial / 无 PNG 无 PDF；SVG 与审计不受影响 | **可选**（决定 PNG/PDF） |
| `numpy` | **否**（本包零 import） | 缺 → 与缺 matplotlib 完全一致（matplotlib 的硬依赖） | **可选但事实必需**（装了 matplotlib 就有） |
| `PIL`/Pillow | 只在 `scripts/validate_figure.py` 的 `F02_png` 里显式 import | 缺 → **PNG 与 PDF 一起丢失**（`matplotlib.colors` 顶层 `from PIL import Image`，且 `mpl_backend` 先存 PNG 再存 PDF） | **可选但事实必需**（见 DEGRADE-MATRIX §4 的微追溯证据） |
| `PyYAML` | 否 | 缺 → 零影响（exit 0 / success / 7 件产物齐全） | **不需要** |
| `python-pptx` | 否 | 缺 → 零影响 | **不需要** |
| `lxml` | 否（用标准库 `xml.etree.ElementTree`） | 缺 → 零影响 | **不需要** |
| `pypdf` | 否（不解析 PDF） | 缺 → 零影响 | **不需要** |
| LibreOffice / `soffice` | 否（从不 shell out；桩命令的调用标记未生成） | 缺或失败（退出 127）→ 零影响 | **不需要** |

## 3. 评测容器里的实际含义

- 只装标准库（档位 A）：**仍能拿到全部科学内容表达与可核验痕迹**（SVG + 三份审计 + 契约 `result.json`），
  只是 `status=partial`、退出码 2。
- 容器里若有 `matplotlib`：档位 B，`status=success`、退出码 0。
- 若容器缺 `PIL` 而"看起来"有 matplotlib：**实测会掉到档位 A**（这点最容易误判为渲染 bug）。
- 本包**不会**因为缺 LibreOffice / PyYAML / python-pptx / lxml / pypdf 而失败或降级。

## 4. 与 README 的关系

`README.md` 的「依赖」一节应与本清单一致：**声明"标准库必需 + matplotlib 可选（含 numpy/Pillow）"，
其余一律不声明为依赖**。若两份文件不一致，以本清单为准（它有逐行实测支撑），并同步修 README。
