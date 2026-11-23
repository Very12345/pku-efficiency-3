# TEST.md — academic-talk-organizer v9（缺依赖降级轴）自测记录

> 本文件里出现的**每条命令都真跑过**，输出为实测摘要（不是设计稿）。
> 实测环境：Windows 11 / Git Bash（MSYS2）/ Python **3.13.9**；
> 本机第三方库：python-pptx **1.0.2**、Pillow **12.3.0**、pypdf **6.14.2**、
> matplotlib **3.10.6**、numpy **2.3.5**、PyYAML **6.0.3**；
> **`soffice` 与 `libreoffice` 都不在 PATH 上**（`shutil.which` 均返回 None）。
>
> **硬规矩：绝不在包内目录跑脚本**（会生成 `__pycache__`，合规硬门直接拒收）。
> `degrade_probe.py` 会把技能复制到沙箱、并让被调用的入口也指向沙箱副本。

## 0. 准备（包外沙箱）

```bash
PKG="<本包所在目录>"
SB=/tmp/atk-v9 && rm -rf "$SB" && mkdir -p "$SB"
cp -r "$PKG" "$SB/skill"
SKILL_DIR="$SB/skill"
cd "$SB"                       # cwd 故意不在技能根
```

## T1 · 主流程（最小调用）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out "$SB/out"
```

实测：

```
[plan] 12 pages, narrative=group_meeting, audience=familiar, P-gates valid=True
[deck] 12 slides, mode=built-in-theme, verify valid=True
[preview] wrote 13 preview files (PIL simulation)
[done] status=partial deck_ok=True preview_ok=True plan_gates=True evidence_audit=True validate_valid=True contract_valid=True
```

**exit code = 0**；`result.json` 顶层键 **20**；顶层 null 值 **0**；
`self_check.json → contract_check` = `declared=16 missing=0 wrong_type=0`。
`result.json.environment` 实测：

```json
{"python": "3.13.9", "platform": "win32", "python_pptx": "1.0.2",
 "pillow": "12.3.0", "pypdf": "6.14.2",
 "cjk_font": {"found": true, "file": "msyh.ttc", "family": "windows"}}
```

## T2 · 独立复核（全部 exit 0）

```bash
python "$SKILL_DIR/scripts/validate_result.py" "$SB/out/result.json"    # checks=7 errors=0 warnings=1
python "$SKILL_DIR/scripts/check_contract.py"  "$SB/out/result.json"    # declared=16 missing=0 wrong_type=0
python "$SKILL_DIR/scripts/evidence_audit.py"  "$SB/out/result.json"    # 逐页审计通过
python "$SKILL_DIR/scripts/verify_deck.py" "$SB/out/editable_deck.pptx" \
       --expect-pages 12 --plan "$SB/out/talk_plan.json"                # checks=8 errors=0
python "$SKILL_DIR/scripts/selftest.py" "$SB/out" --package-check "$SKILL_DIR"
```

实测：5 个命令 **exit code 全 0**；`selftest.py` → `"summary": "checks=6 errors=0"`，
`no_pycache`/`symlinks=[]` 均 `ok=true`。

## T3 · ★ 降级探针（本轴的核心测试）

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" \
    --sandbox "$SB/dg" --report "$SB/dg/degrade_matrix_report.json"
```

实测输出（12 个配置 + 5 级阶梯，墙钟约 18 秒）：

```
[OK] D-00   exit=0 status=partial deck=True  previews=12  期望全部命中
[OK] D-01   exit=0 status=partial deck=False previews=12  期望全部命中
[OK] D-02   exit=0 status=partial deck=False previews=0   期望全部命中
[OK] D-03 … D-06  同 D-00 形态                             期望全部命中
[OK] C-01   exit=0 status=partial deck=False previews=12  期望全部命中
[OK] C-02   exit=0 status=partial deck=False previews=0   期望全部命中
[OK] C-03   exit=0 status=partial deck=False previews=0   期望全部命中
[OK] O-01   exit=0 status=partial deck=True  previews=12  期望全部命中
[OK] O-02   exit=0 status=partial deck=False previews=0   期望全部命中
[OK] M-01 … M-05                                          期望全部命中
[degrade] probes=12 unreadable=0 unmet=0; ladder=5
```

**exit code = 0**。核心实测值：

| 项 | 实测 |
|-|-|
| 配置数 / 无法判读 / 期望未命中 | **12 / 0 / 0** |
| 最小环境阶梯级数 | **5**（全部可判读） |
| 各配置退出码 | 全 **0** |
| 各配置 `status` | 全 `partial`（合成案例缺 `dataset_card.pdf` 的如实降级，与依赖无关） |
| 各配置是否写 `result.json` | **全部写了**（`unreadable=0`） |
| 本机依赖快照 | `{"pptx":"1.0.2","PIL":"12.3.0","pypdf":"6.14.2","matplotlib":"3.10.6","numpy":"2.3.5","yaml":"6.0.3","_cli_soffice":null,"_cli_libreoffice":null}` |

### T3.1 逐配置产物数与形态（实测）

| 配置 | 被拦导入 | 产物数 | deck | 预览 PNG | 依赖相关 uncertainty |
|-|-|-|-|-|-|
| `D-00` | —（对照） | **21** | 有 | 12 | 2 条（含 deck 模式说明） |
| `D-01` | `pptx` | **19** | 无 | 12 | 「运行环境缺少 python-pptx…本次未生成可编辑 .pptx」 |
| `D-02` | `PIL` | **6** | 无 | **0** | 「PNG 预览渲染失败或未执行」+「缺少 python-pptx（PIL 被拦）」 |
| `D-03` | `pypdf` | 21 | 有 | 12 | 无新增（案例 PDF 本就缺文件） |
| `D-04` | `matplotlib` | 21 | 有 | 12 | 无（纯 no-op） |
| `D-05` | `numpy` | 21 | 有 | 12 | 无（纯 no-op） |
| `D-06` | `yaml`,`ruamel` | 21 | 有 | 12 | 无（纯 no-op） |
| `C-01` | `pptx`,`pypdf` | **19** | 无 | 12 | 缺 python-pptx 条目 |
| `C-02` | `pptx`,`PIL` | **6** | 无 | **0** | 缺 python-pptx + 预览失败 |
| `C-03` | `pptx`,`PIL`,`pypdf` | **6** | 无 | **0** | 上述 +「pypdf/PyPDF2 不可用」 |
| `O-01` | 无（soffice 本就不在 PATH） | 21 | 有 | 12 | 预览为 PIL 模拟（既有条目） |
| `O-02` | `PIL` + 无 soffice | **6** | 无 | **0** | 预览失败 + 缺 python-pptx |

### T3.2 三个关键实测发现

1. **缺 Pillow 会连带让可编辑 `.pptx` 也产不出来**。实测 `result.json.environment`
   变成 `pptx=null / pillow=null`；`change_records` 里 `deck SKIPPED` 的原因字符串是
   `python-pptx 不可用（[degrade_probe] PIL blocked by controlled import interception）`。
   根因：`python-pptx` 声明依赖 `Pillow >=3.3.2`（`importlib.metadata` 实测
   `['Pillow >=3.3.2', 'XlsxWriter >=0.5.7', 'lxml >=3.1.0', 'typing-extensions >=4.9.0']`）。
2. **只放行顶层模块 `pptx` 不够**。阶梯 M-02 实测 deck 仍无，原因字符串为
   `non-whitelisted third-party module lxml blocked`。
3. **`matplotlib`/`numpy`/`yaml` 的缺失是纯 no-op 且可证**：三个子进程导出的
   `sys.modules` 清单里对应模块**从未出现**，产物与对照格逐项相同。

### T3.3 最小环境阶梯（实测）

| 级 | 放行的第三方顶层模块 | exit | 产物数 | deck | 预览 PNG |
|-|-|-|-|-|-|
| `M-01` | （无，只有标准库） | 0 | **6** | 无 | 0 |
| `M-02` | `pptx` | 0 | 6 | 无 | 0 |
| `M-03` | `PIL` | 0 | **19** | 无 | **12** |
| `M-04` | `pptx`,`PIL`,`lxml`,`xlsxwriter`,`typing_extensions` | 0 | **21** | **有** | **12** |
| `M-05` | 上一级 + `pypdf` | 0 | **21** | **有** | **12** |

`minimal_environments[]` 实测（报告自动汇总）：

```json
[{"id":"MIN-json-only","measured":{"observed_in":"M-01","exit_code":0,"status":"partial",
   "has_deck":false,"preview_png_count":0,"product_count":6,"writes_result_json":true}},
 {"id":"MIN-json+previews","measured":{"observed_in":"M-03", "...":"...","preview_png_count":12}},
 {"id":"MIN-full","measured":{"observed_in":"M-05", "...":"...","has_deck":true,"preview_png_count":12}}]
```

## T4 · 拦截是否真的生效（不靠自述）

```bash
python -c "import json;d=json.load(open(r'<SB>/dg/sandbox/probes/D-04/loaded_modules.json'));
print('matplotlib' in [m.split('.')[0] for m in d['loaded_modules']])"
```

实测：**`False`** —— 被拦模块从未被加载。同类核对：`D-01/C-01/C-02/C-03/M-01/M-02`
的 `pptx` 为 False、`D-02/C-02/C-03/O-02/M-01/M-02` 的 `PIL` 为 False、
`D-03/C-01/C-03/M-01…M-04` 的 `pypdf` 为 False。

## T5 · 负例（必须非 0 退出）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SB/nope.json" --out "$SB/out-fail"   # → exit 1
python "$SKILL_DIR/scripts/main.py" --out "$SB/x"                                 # → exit 2
```

实测：`exit=1`（写出最小失败信封，`status=failed`，`error` 文本已净化）、
`exit=2`（argparse 用法错误，不写产物）。
`degrade_probe.py --only D-02` 可单配置复跑。

## 6. 汇总

| 测试 | 命令要点 | 期望 | 实测 |
|-|-|-|-|
| T1 | `main.py --case examples --out out` | exit 0，`result.json` 完整 | ✅ exit 0；20 键；null 0 个 |
| T2 | 五个独立复核 | 全 exit 0 | ✅ 5/5 exit 0 |
| T3 | `degrade_probe.py` | exit 0、`unreadable=0`、`unmet=0` | ✅ 12/12 配置 + 5/5 阶梯，全 exit 0 |
| T3.2 | 三个关键发现 | 可复现 | ✅ 缺 Pillow 连带 deck；只放行 pptx 不够；matplotlib/numpy/yaml 纯 no-op |
| T4 | `sys.modules` 证据 | 被拦模块从未加载 | ✅ 全部 False |
| T5 | 负例 | exit 1 / exit 2 | ✅ |

**判据一句话**：`degrade_probe.py` 必须在 **exit 0** 下给出 `probes=12`、`unreadable=0`、
`unmet=0`，且**每一个配置都写出 `result.json`**；
出现任何一格 `unreadable` 就说明"缺依赖"被误报成了崩溃，必须修而不是改期望值。
