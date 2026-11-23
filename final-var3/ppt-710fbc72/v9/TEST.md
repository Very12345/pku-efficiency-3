# TEST —— 本地实测记录（v9 · 缺依赖降级链）

环境：Windows 11 + Git Bash(MSYS2)；`python` = Anaconda **Python 3.13.9**；
python-pptx 1.0.2 / Pillow 12.3.0 / lxml 已装 / numpy 2.3.5 / matplotlib 3.10.6；
**未装 LibreOffice**。日期：2026-11-23（Asia/Shanghai）。

约定：`$SKILL_DIR` = 本包根目录；`$RUN` = **包外**可写临时目录。
**所有命令都在 cwd ≠ `$SKILL_DIR` 下执行**，并且**从不在包内跑脚本**——包内执行会
留下 `scripts/__pycache__/*.pyc`，而 `.pyc` 是题面资源契约明确拒收的类型。

```bash
SKILL_DIR=<本包根目录>
RUN=<包外临时目录>; mkdir -p "$RUN"
cp -r "$SKILL_DIR/examples" "$RUN/examples"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
```

## 0. 语法编译检查

在**包外临时副本**上跑 `python -m py_compile "$TMP"/scripts/*.py`。
结果：**成功**（exit 0，14 个脚本含本轴新增的 `degrade_probe.py` 全部通过）。

## 1. 正式流程冒烟（main.py）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"; echo "exit=$?"
```

实测输出（原文）：

```
figure ready: examples/figs/fig1.png (11108 B)
figure ready: examples/figs/fig2.png (15422 B)
audit ok: 19 checks, fails=0, warns=0
main ok: case=example-catalyst-201 status=success slides=10 contract_gates=ok out=out
exit=0
```

- **exit = 0**，`status=success`，10 页，`contract_gates=ok`
- `result.json` **顶层键 28 个**（21 信封 + 3 固定 + 示例契约回显 4）
- `--out` 下 **12 个产物**（含 `deck.pptx` 与两张 PNG）

## 2. 契约门

`validate_result.py` exit=0；`check_contract.py` exit=0、`"valid": true`、G1–G8 全 `ok`
（G3 detail 原文 `missing=[] null_placeholders=[]`）。

## 3. ★ 本轴核心：degrade_probe.py（10 个场景）

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" --skill "$SKILL_DIR" --run "$RUN/dp" \
    --json "$RUN/dp.json" --markdown "$RUN/dp.md"; echo "exit=$?"
```

实测输出末尾（原文）：

```
[degrade_probe] baseline: exit=0 status=success artifacts=12
  ...
[degrade_probe] json  -> <RUN>/dp.json
[degrade_probe] table -> <RUN>/dp.md
[degrade_probe] 10 scenarios, 0 silent pass(es), 0 ineffective poison(s)
exit=0
```

**逐场景实测**（`dp.json` 的 `scenarios[]`；`失败形态` = exit=1 + `failed` + 1 产物）：

| 场景 | 缺什么 | 模拟 | 投毒生效 | exit | result.json | status | 顶层键 | 产物 | deck | PNG | uncertainty | 连带不可导入 | 判定 |
|-|-|-|-|-|-|-|-|-|-|-|-|-|-|
| 01 | `pptx` | PYTHONPATH 假包 | 是 | **1** | 有 | `failed` | 14 | 1 | 无 | 0 | 1 | — | 按声明 |
| 02 | `PIL` | PYTHONPATH 假包 | 是 | **1** | 有 | `failed` | 14 | 1 | 无 | 0 | 1 | `matplotlib`,`pptx` | 按声明 |
| 03 | `matplotlib` | PYTHONPATH 假包 | 是 | 0 | 有 | `success` | 28 | 12 | 有 | 2 | 1 | — | 按声明 |
| 04 | `numpy` | PYTHONPATH 假包 | 是 | 0 | 有 | `success` | 28 | 12 | 有 | 2 | 1 | `matplotlib` | 按声明 |
| 05 | `yaml` | PYTHONPATH 假包 | 是 | 0 | 有 | `success` | 28 | 12 | 有 | 2 | 1 | — | 按声明 |
| 06 | `lxml` | PYTHONPATH 假包 | 是 | **1** | 有 | `failed` | 14 | 1 | 无 | 0 | 1 | `pptx` | 按声明 |
| 07 | `reportlab` | PYTHONPATH 假包 | 是 | 0 | 有 | `success` | 28 | 12 | 有 | 2 | 1 | — | 按声明 |
| 08 | LibreOffice | **PATH 置空** | 是 | 0 | 有 | `success` | 28 | 12 | 有 | 2 | 1 | — | 按声明 |
| 09 | 全部 7 个 Python 依赖 | 7 个假包 | 是 | **1** | 有 | `failed` | 14 | 1 | 无 | 0 | 1 | 全 7 个 | 按声明（对照） |
| 10 | `PIL` + **真实源图** | PYTHONPATH 假包 | 是 | **1** | 有 | `failed` | 14 | 1 | 无 | 0 | 1 | `matplotlib`,`pptx` | 按声明（对照） |

**分类（`dp.json` 顶层字段，实测）**：

```
hard_fail_dependencies   = ["pptx", "PIL", "lxml"]
unaffected_dependencies  = ["matplotlib", "numpy", "yaml", "reportlab", "libreoffice"]
control_scenarios        = [{"id": "09-combo-all", "kind": "combo", "exit": 1}]
silent_pass_count        = 0
ineffective_poison_count = 0
```

**投毒有效性校验（`poison_probe`）**：每个被投毒的包都单独跑过
`python -c "import X"`，实测全部**非 0 退出**；未投毒的场景（08）跳过这项。
这条校验是本轴防止"测了个寂寞"的闸门——若投毒没生效，脚本直接判失败。

**失败场景的产物清单（实测完全一致）**：

```
--out 下只有 1 个条目：result.json（14 个顶层键）
uncertainty = [{"item": "pipeline", "note": "ImportError: simulated: pptx not installed"}]
stderr 末行  = main FAILED: simulated: pptx not installed
```

**单入口实测**（`entries`，exit）：

| 场景 | `main.py` | `make_synthetic_inputs.py` | `make_template.py` |
|-|-|-|-|
| 01 `pptx` | 1 | 0 | 1（`__init__.py:1 in <module>`） |
| 02 `PIL` | 1 | 1 | 1（`__init__.py:1 in <module>`） |
| 03–08（非依赖） | 0 | 0 | 0 |
| 09 合并 | 1 | 1 | 1 |
| 10 `PIL`+真实源图 | 1 | 1 | 1 |

## 4. 两条专项验证（本轴的关键否定性证据）

### 4.1 `lxml`：本包不 import，但缺了整条流程失败

```bash
$SKILL_DIR 内 grep「lxml」        # 实测：scripts/*.py 0 命中
python -c "import pptx, pathlib; root=pathlib.Path(pptx.__file__).parent; \
           print([str(f.relative_to(root)) for f in root.rglob('*.py') if 'lxml' in f.read_text('utf-8','replace')][:5])"
```
实测：本包 0 命中；`python-pptx` 侧有 **20 个文件**提到 lxml，其中
`opc/oxml.py`、`oxml/__init__.py`、`oxml/xmlchemy.py` 是**包级** `from lxml import etree`。
⇒ 缺 lxml ⇒ `import pptx` 失败 ⇒ 场景 06 走与场景 01 完全相同的失败路径
（exit=1、`failed`、1 产物、`tool_versions.pptx=unavailable`）。

### 4.2 LibreOffice：PATH 置空后与基线**逐项相同**

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" --skill "$SKILL_DIR" --run "$RUN/dp2" --only libreoffice
```
实测：exit=0、`success`、12 产物、28 键、deck 有、2 PNG。
原因：`preview.py` **从不 shell out 到 `soffice`**（`grep -n "subprocess\|soffice"` 在
`preview.py` 无命中），它画 PIL 示意图并在三处标注（`render_log.json.renderer`/
`honest_note`、`_PREVIEW_ARE_SCHEMATIC.txt`、`result.json.main_result.preview_is_schematic`）。

## 5. 开关与失败路径（实测）

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" --skill "$SKILL_DIR" --list
#   → 打印 10 个场景的 id / kind / 依赖名，exit 0
python "$SKILL_DIR/scripts/degrade_probe.py" --skill "$SKILL_DIR" --run "$RUN/dp3" --only pptx,lxml
#   → 只跑 2 个场景（支持用场景 id 或依赖名过滤），exit 0
python "$SKILL_DIR/scripts/degrade_probe.py" --skill "$SKILL_DIR" --run "$SKILL_DIR/scratch"
#   → 拒绝：stderr 说明包内跑会留下 __pycache__，exit 2
```

## 6. 对照：本轴没有改动任何既有脚本

实测：基线 13 个 `scripts/*.py` **逐字节相同**（`cmp` 无输出）；新增文件仅
`scripts/degrade_probe.py` 1 个。CLI 参数、退出码语义未动。
⇒ §3/§4 的降级形态都是**基线已有行为**，本轴的贡献是把它们测出来、逐条点名，
并把 `lxml` 这条"隐形硬依赖"写进必需依赖清单。

## 7. 未通过 / 已知限制

1. **只观察到两态降级**（全成功 / 全失败）：没有出现"deck 有但预览无"这类中间态。
   这不代表不可能，只代表本包的降级路径目前是两态的。
2. **未测版本过旧**：只测"完全没有"，没测"装了但版本过低 / API 不兼容"。
3. **未测系统库缺失**：如 Pillow 装了但 `libjpeg`/`libtiff` 缺失导致的 `IOError`
   （不是 `ImportError`），不在受控导入拦截的覆盖范围。
4. **`PATH` 置空是比"只移除 soffice"更宽的模拟**：本场景下不影响本包（它不调用任何
   外部程序），但手段本身更宽，已在 `references/DEGRADE-MATRIX.md` §8 声明。
5. **未测 `--starting-deck`/`--template` 分支下的依赖缺失**：本实验跑的是"案例未给
   模板"的回退路径（`opened_from=builtin`）。
6. **计数口径**：`--out` 下"12 个产物"是 `os.listdir()` 的条目数（含 `_runtime/` 目录）。
