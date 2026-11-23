# TEST.md — academic-talk-organizer v7（确定性轴）自测记录

> 本文件里出现的**每条命令都真跑过**，输出为实测摘要（不是设计稿）。
> 实测环境：Windows 11 / Git Bash（MSYS2）/ Python **3.13.9** /
> python-pptx **1.0.2** / Pillow **12.3.0** / pypdf **6.14.2** /
> 无 LibreOffice（`which soffice` 与 `which libreoffice` 均无输出）。
>
> **硬规矩：绝不在包内目录跑脚本** —— 那会生成 `__pycache__`，合规硬门直接拒收。
> 下面的命令一律在**包外**的临时目录里跑，且脚本把技能**复制到沙箱**后再调用。

## 0. 准备（包外沙箱）

```bash
PKG="<本包所在目录>"                    # 含 SKILL.md 的那个目录
SB=/tmp/atk-v7 && rm -rf "$SB" && mkdir -p "$SB"
cp -r "$PKG" "$SB/skill"                # 在包外操作副本，包内目录全程只读
SKILL_DIR="$SB/skill"
cd "$SB"                                # cwd 故意不在技能根
```

## T1 · 主流程（最小调用）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out "$SB/out"
```

实测输出：

```
[plan] 12 pages, narrative=group_meeting, audience=familiar, P-gates valid=True
[deck] 12 slides, mode=built-in-theme, verify valid=True
[preview] wrote 13 preview files (PIL simulation)
[done] status=partial deck_ok=True preview_ok=True plan_gates=True evidence_audit=True validate_valid=True contract_valid=True
[done] output: <SB>/out
```

**exit code = 0**。`result.json` 顶层键数 = **20**：

```
case_id, status, title, report_goal, audience, duration_min, slide_count, summary,
main_line, pages, evidence_map, artifacts, sources, uncertainty, contract,
change_records, environment, generated_by, generated_at, audit
```

> `status=partial` 是**正确结果**：合成示例案例的 `materials/dataset_card.pdf` 故意不存在
> （用例演示"声明材料缺失"分支），因此 `partial` + `uncertainty` 两条。不是失败。

产物清单（**21 个文件**：8 个顶层产物 + `previews/` 13 个）：

```
result.json  self_check.json  talk_plan.json  evidence_map.json  plan_gates.json
evidence_audit.json  deck_audit.json  editable_deck.pptx
previews/{cover_preview.png, preview_grid.png, preview_manifest.json, slide_002..011.png}
```

## T2 · 四件独立复核（全部 exit 0）

```bash
python "$SKILL_DIR/scripts/validate_result.py" "$SB/out/result.json"    # → checks=7 errors=0 warnings=1
python "$SKILL_DIR/scripts/check_contract.py"  "$SB/out/result.json"    # → declared=16 missing=0 wrong_type=0
python "$SKILL_DIR/scripts/evidence_audit.py"  "$SB/out/result.json"    # → 逐页审计通过
python "$SKILL_DIR/scripts/verify_deck.py" "$SB/out/editable_deck.pptx" \
       --expect-pages 12 --plan "$SB/out/talk_plan.json"                # → checks=8 errors=0
```

实测摘要：

| 脚本 | 关键输出 | exit |
|-|-|-|
| `validate_result.py` | `"summary": "checks=7 errors=0 warnings=1"` | 0 |
| `check_contract.py` | `"checked_against": "sibling self_check.json contract_applied"`、`"summary": "declared=16 missing=0 wrong_type=0"` | 0 |
| `evidence_audit.py` | 逐页条目（含 structural 页分类） | 0 |
| `verify_deck.py` | `"slide_count": 12`、`"normalized_sha256": "3a3ece0940a04eb60708f2a89da7f9f0c08f4be4ea72f92fa46a52fd3df28dd3"`、`"summary": "checks=8 errors=0"` | 0 |

> `warnings=1` 是"页面数字需人工对照源材料"的**提示级**结论，不是错误。

## T3 · 全链路自检 + 包约束（G1–G10）

```bash
python "$SKILL_DIR/scripts/selftest.py" "$SB/out" --package-check "$SKILL_DIR"
```

实测摘要：`"summary": "checks=6 errors=0"`，其中包约束段
`{"check": "symlinks=[]"} ok=true`、`{"check": "no_pycache", "detail": "pycache=[]"} ok=true`、
`"summary": "text=39 total_bytes=362375 max_file=42426"`。**exit code = 0**。

> 三个硬门数字：文本文件 **39** 个（上限 50）、合计 **362,375 B**（上限 2 MB）、
> 单文件最大 **42,426 B**（上限 500 KB）。

## T4 · ★ 确定性探针（本轴的核心测试）

```bash
python "$SKILL_DIR/scripts/determinism.py" \
    --case "$SKILL_DIR/examples" \
    --out-root "$SB/det" --report "$SB/det/determinism_report.json" --runs 5
```

实测输出：

```
[determinism] runs=5 exit_codes=[0]
[determinism] raw identical=False | content-projection identical=True | normalized-archive identical=True
[determinism] products=21 varying_raw=['editable_deck.pptx','previews/preview_manifest.json',
              'result.json','self_check.json','talk_plan.json'] varying_stable=[] leaks=0
[determinism] result.json top-level keys per run: [20]
```

**exit code = 0**。逐项实测值：

| 项 | 实测 |
|-|-|
| run 数 | 5 |
| 各 run cwd 形态 | `empty_temp_dir`（run0/run3）与 `skill_root_copy`（run1/2/4） |
| 各 run `--out` 形态 | `absolute`（run0/run3）与 `relative(../ 从技能根)`（run1/2/4） |
| `PYTHONHASHSEED` 取值 | `['0','1','2','4','8']` |
| 各 run exit code | 全 **0** |
| 各 run 墙钟（秒） | 1.162 / 1.056 / 1.065 / 1.064 / 1.121 |
| 各 run `result.json` 顶层键数 | 全 **20** |
| 产物总数 | **21** |
| raw sha256 唯一值 = 1 的产物 | **16** |
| raw 有差异的产物 | **5**（上表 `varying_raw`） |
| 稳定化后仍有差异的产物 | **0** |
| 产物树整体 sha256 | raw 5 个不同值 / 稳定化后 **1** 个（`b7b531d96c9d67ac…`） |
| 归一化归档产物树 sha256 | **1** 个（`79d2050196f529e0…`） |
| 本机绝对路径泄漏 | **0 命中**（4 类正则 × 每次 run 的 8 个 JSON 产物 × 5 次 run） |
| `zip_metadata_only_files` | `['editable_deck.pptx']` |

### T4.1 为什么 raw 不同：手工复核证据

```bash
python - <<'EOF'
import zipfile, hashlib
a, b = "<run0>/out/editable_deck.pptx", "<run1>/out/editable_deck.pptx"
za, zb = zipfile.ZipFile(a), zipfile.ZipFile(b)
same = all(hashlib.sha256(za.read(n)).digest() == hashlib.sha256(zb.read(n)).digest()
           for n in za.namelist())
print("entries:", len(za.namelist()), "entry-content-identical:", same)
print("zip mtimes differ:", {i.date_time for i in za.infolist()} != {i.date_time for i in zb.infolist()})
EOF
```

实测：`entries: 87 entry-content-identical: True`、`zip mtimes differ: True`。
⇒ **87 个 zip 成员解压后字节完全相同，只有成员时间戳不同**。

### T4.2 归一化归档的 raw 一致性

```bash
python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" \
  "<det 沙箱>/normalized/run0/editable_deck.pptx"
python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" \
  "<det 沙箱>/normalized/run1/editable_deck.pptx"
```

实测两次输出**相同**（固定 `date_time=(1980,1,1,0,0,0)`、成员名排序、压缩级别 9）。

## T5 · 降级分支（确定性探针不因缺依赖而失真）

模拟方式：在包**外**的沙箱里放一个 `sitecustomize.py`（解释器启动即加载），
用 `sys.meta_path` 前缀拦截器禁止 `pptx` 导入；`PYTHONPATH` 会被子进程继承，
所以 `determinism.py` 拉起的每个 run 都同样缺 deck。

```bash
mkdir -p "$SB/nopep" && cat > "$SB/nopep/sitecustomize.py" <<'EOF'
import sys
class _B:
    def find_spec(self, name, path=None, target=None):
        if name == "pptx" or name.startswith("pptx."):
            raise ImportError("pptx blocked (sitecustomize, T5)")
        return None
sys.meta_path.insert(0, _B())
EOF

PYTHONPATH="$SB/nopep" python "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples" --out "$SB/out-nodeck" --quiet
PYTHONPATH="$SB/nopep" python "$SKILL_DIR/scripts/determinism.py" \
    --case "$SKILL_DIR/examples" --out-root "$SB/det-nodeck" \
    --report "$SB/det-nodeck/r.json" --runs 3
```

实测输出（主流程）：

```
[deck] SKIPPED (dependency missing): python-pptx 不可用（pptx blocked (sitecustomize, T5)）
status=partial pages=12 deck=False validate_valid=True contract_valid=True
exit=0
status: partial | editable_deck: None | deck_limitation: python-pptx 不可用（pptx blocked…）
```

实测输出（确定性探针，3 runs）：

```
[determinism] runs=3 exit_codes=[0]
[determinism] raw identical=False | content-projection identical=True | normalized-archive identical=True
[determinism] products=19 varying_raw=['previews/preview_manifest.json','result.json',
              'self_check.json','talk_plan.json'] varying_stable=[] leaks=0
```

⇒ **缺 deck 时判据同样成立**：产物从 21 降到 **19**，`varying_raw` 从 5 个降到 **4** 个
（少了 `editable_deck.pptx`），`content_identical` 仍为 **True**、`leaks` 仍为 **0**。
完整逐配置降级矩阵（12 个配置 + 5 级最小环境）见 v9 轴的 `references/DEGRADE-MATRIX.md`。

## T6 · 负例（必须非 0 退出）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SB/does-not-exist.json" --out "$SB/out-fail"
python "$SKILL_DIR/scripts/main.py" --out "$SB/out-fail2"
```

实测：

| 命令 | stdout | exit | result.json |
|-|-|-|-|
| 不存在的 case.json | `FATAL: case.json unreadable: [Errno 2] No such file or directory: '...'` | **1** | 写了最小失败信封，8 个键：`artifacts, case_id, change_records, error, sources, status, title, uncertainty`；`status=failed`；`error` 文本**已净化**为 `case.json unreadable: [Errno 2] No such file or directory: 'does-not-exist.json'`（本机绝对前缀被改写掉） |
| 缺 `--case` | `main.py: error: the following arguments are required: --case` | **2** | 无（argparse 用法错误，不写产物） |

## 7. 汇总

| 测试 | 命令要点 | 期望 | 实测 |
|-|-|-|-|
| T1 | `main.py --case examples --out out` | exit 0，写出 `result.json` | ✅ exit 0，20 个顶层键 |
| T2 | 四件独立复核 | 全 exit 0 | ✅ 4/4 exit 0 |
| T3 | `selftest.py <out> --package-check` | exit 0，无 error | ✅ `checks=6 errors=0`；`text=39 total_bytes=362375 max_file=42426` |
| T4 | `determinism.py --runs 5` | exit 0，`content identical`、`leaks=0` | ✅ 5 runs 全 exit 0；`varying_stable=[]`；`leaks=0` |
| T5 | 遮蔽 `pptx` 后再跑主流程与探针 | 判据仍成立 | ✅ 产物 19、`varying_raw` 4 个、`content_identical=True`、exit 0 |
| T6 | 负例（case 不存在 / 缺参数） | exit 1 / exit 2 | ✅ 1 / 2（失败信封 8 键，`error` 已净化） |

**判据一句话**：T4 的 `files_varying_raw` 必须恰好是那 5 个文件、`files_varying_stable`
必须为空、`leaks` 必须为 0；任何偏离都要在 `references/DETERMINISM.md` 里登记到源码行为，
否则视为本次改动引入了新的不确定性。
