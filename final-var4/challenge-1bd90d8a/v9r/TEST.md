# TEST.md — v9（缺依赖降级链轴）真机实测记录

> 所有命令都在**包外**的临时副本上跑；探针自己也把被测包复制到 `--workdir` 再跑，
> 所以包内不产生 `__pycache__`。数字来自 `degrade_probe_report.json`。

环境：Windows / Python 3.13.9 / Pillow 12.3.0。
当前已安装（探针实测）：`PIL`=12.3.0、`pptx`=1.0.2、`matplotlib`=3.10.6、`numpy`=2.3.5、
`yaml`=6.0.3、`lxml`=6.1.1、`pypdf`=6.14.2、`reportlab`=5.0.0、`pandas`=2.3.3、
`scipy`=1.16.3、`fontTools`=4.60.1；**`cairosvg` 与 `svgwrite` 本机未安装**（探针如实记录 `ABSENT`）。

---

## T1 语法编译

```bash
python -m py_compile scripts/*.py
```

结果：**exit 0，11/11 通过**（10 个既有入口 + `degrade_probe.py`）。

## T2 端到端冒烟（包外副本）

```bash
cp -r v9 /tmp/v9 && cd /tmp/v9
python scripts/main.py --case examples/case.json --out /tmp/out --work /tmp/work
```

```
[main] case_id=example-science-figure-01 status=completed figures=['fig-01', 'fig-02'] failed=[]
[main] gates: G1=OK G2=OK G3=OK G4=OK G5=OK G6=OK G7=OK G8=OK all_pass=OK
EXIT=0
```

`result.json` 顶层 **29 键**，`status=completed`，`outputs` 6 项。

## T3 既有入口逐个跑（能力未丢）

| 命令 | 实测 |
|-|-|
| `check_contract.py --result /tmp/out/result.json --case examples/case.json` | `SUMMARY: PASS (required=18 missing=0 null=0 contract_missing=0)`，exit 0 |
| `figcheck.py --dir /tmp/out --case examples/case.json --json` | `all_pass=True`，G1–G8 全 True，exit 0 |
| `mapcheck.py --dir /tmp/out --case examples/case.json --json` | `summary={'checked': 121, 'mismatches': 0, 'unmatched': 0}`，exit 0 |
| `spec_lint.py --spec examples/case.json --case examples/case.json --json` | `{"valid": true, "counts": {"figures": 2, "errors": 0, "warnings": 0}}`，exit 0 |
| `extract.py --case examples/case.json --out /tmp/extract --json` | 输出 `tables[]` 列画像，exit 0 |
| `verify_rerun.py --record-only --dir /tmp/out` | 逐文件 sha256，exit 0 |

## T4 ★ 本版新增：全量缺依赖探针（17 档）

```bash
python scripts/degrade_probe.py --src /tmp/v9 --case /tmp/v9/examples/case.json \
    --workdir /tmp/dp --out /tmp/dp/degrade_probe_report.json
```

真实输出（尾部）：

```
[degrade_probe] PIL            exit=1 status=failed    files=6   result.json=有
[degrade_probe] ALL_OPTIONAL   exit=1 status=failed    files=6   result.json=有
[degrade_probe] CLI_PATH_MIN   exit=0 status=completed files=11  稳定产物与基线不一致：figure-fig-01.png, figure-fig-02.png
[degrade_probe] CLI_SHIM_TRAP  exit=0 status=completed files=11  稳定产物与基线逐字节一致
[degrade_probe] 探针 17 档；产出 result.json 的档数 17
EXIT=0
```

关键数字：

| 档 | exit | status | result.json 键数 | 产物数 | 与基线逐字节一致 |
|-|-|-|-:|-:|-|
| NONE（基线） | 0 | completed | 29 | 11 | —— |
| **PIL** | 1 | failed | **6** | **6** | ❌（丢 5 个产物） |
| **ALL_OPTIONAL**（拦 13 个） | 1 | failed | **6** | **6** | ❌ |
| 其余 12 个模块（逐个） | 0 | completed | 29 | 11 | ✅ 完全一致（拦截记录 0 次） |
| CLI_PATH_MIN | 0 | completed | 29 | 11 | ❌（只有 2 个 PNG 变） |
| CLI_SHIM_TRAP | 0 | completed | 29 | 11 | ✅ |

缺 PIL 时的拦截证据（`(module, frame)`）：`chartkit.py:41`、`cjkfont.py:114`、
`chartkit.py:1851`、`figcheck.py:157` —— 前三个包在 `try` 里（降级），最后一个**裸导**（整链失败）。

## T5 定点复核（`--only`）

```bash
python scripts/degrade_probe.py --only PIL,ALL_OPTIONAL,CLI_SHIM_TRAP --json
```

实测三档结论与全量一致（PIL/ALL_OPTIONAL：exit 1、6 键；CLI_SHIM_TRAP：与基线一致）。
CLI 两档的编号与模块档同表，可单独复核。

## T6 外部 CLI 三层证据

| 层 | 实测 |
|-|-|
| (a) PATH 收窄 | 稳定产物中只有 `figure-fig-01.png` / `figure-fig-02.png` 变化；SVG 与全部 JSON 一致。`binary_delta`：281926→281625 字节（首个差异偏移 3881）、122579→122527 字节（偏移 7080） |
| (b) 假 CLI 陷阱 | 阳性对照 `soffice.cmd` **被真的调用**（exit 1、日志写入 = true）；主流程跑完后调用日志 **0 条** |
| (c) 静态扫描 | `subprocess`/`os.system`/`os.popen`/`shutil.which` 等调用点 **0 处** |

**根因（已定位）**：Windows 的 DLL 搜索顺序包含 PATH，收窄后同一字体文件由**另一个 FreeType**
光栅化。对照实验：把本机含 `freetype.dll` 的目录加回收窄后的 PATH → PNG 位图恢复与 full PATH 一致。
详细的四步定位过程写在 `references/DEGRADE-MATRIX.md` §5.1。

## T7 边界与异常

| 用例 | 命令 | 实测 |
|-|-|-|
| `--only` 写错编号 | `degrade_probe.py --only Z9` | 报错并列出全部可用编号，exit 1 |
| `--src` 下没有 `scripts/` | `degrade_probe.py --src /tmp` | 报错，exit 1 |
| `--workdir` 落在被测包内 | `degrade_probe.py --src . --workdir ./w --only PIL` | 启动即拒绝（会把包复制进自己的子目录），exit 1 |
| 跳过 CLI 层 | `degrade_probe.py --no-cli` | 只跑模块档，`cli_evidence` 缺失 |
| 保留副本与输出 | `degrade_probe.py --keep` | 整包副本与各档输出目录保留在 `--workdir` |
| 报告可移植 | 见 T8 | —— |

## T8 报告合规

```bash
# validate_pkg.py 用的就是同一组本机路径标记（盘符前缀 / 用户目录 / UNC 前缀），
# 把包与报告一起扫一遍：
python validate_pkg.py .
```

实测：报告与文档在**同一组标记**下 0 命中（`<WORKDIR>` / `<SKILL_DIR>` / `<CASEDIR>` / `<ABS>` 占位符已替换本机路径；
注意报告里连"含 freetype.dll 的目录"也只写相对描述，不写盘符）。

```bash
python validate_pkg.py <本包目录>
```

见提交前的合规验收记录（`[PASS]`，0 条 FAIL）。
