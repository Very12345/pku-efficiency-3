# academic-talk-organizer v9 · challenge-20870c35（学术汇报内容组织 · slides 组）

把**已有**的论文/研究材料组织成可讲、可编辑、证据可追溯的学术汇报产物，
并且对"评测机上少装了哪个库"给出**逐项实测的降级形态**与**最小可用环境**。

本包是「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35 的 Skill 交付物，
轴 = **缺依赖降级链实测**（v9）。`SKILL.md` 是 Agent 加载入口；
**本轴核心文档**是 [references/DEGRADE-MATRIX.md](references/DEGRADE-MATRIX.md)；
实测命令与观测见 [TEST.md](TEST.md)；五维落点见 [references/RUBRIC_MAP.md](references/RUBRIC_MAP.md)。

> **资源形态**（题面 Runtime contract）：本包**只含 UTF-8 文本资源**
> （`.md/.py/.json/.txt/.csv/.yaml/.yml`）；`.pdf`/`.png`/`.pptx` 一律运行时生成；
> 包内无本机绝对路径、无 `__pycache__`、无符号链接。

## 一、v9 的核心资产：降级探针

```bash
$SKILL_DIR=/skills/weekly-skill   # 或本包实际目录；所有脚本自定位，cwd 任意

python "$SKILL_DIR/scripts/degrade_probe.py" \
    --sandbox /tmp/dg --report /tmp/dg/degrade_matrix_report.json
# 期望：probes=12 unreadable=0 unmet=0; ladder=5，退出码 0
```

**怎么模拟缺库**：在**子进程**的 `sys.meta_path` 上装一个按模块名前缀拒绝导入的拦截器，
再 `runpy.run_path()` 执行 `scripts/main.py`。拦截只作用于该子进程，**不改本机任何已安装包**；
子进程退出前把加载过的模块清单写成 JSON ⇒ "拦截是否真的生效"由证据说话。

覆盖：12 个缺失配置（单依赖 `pptx`/`PIL`/`pypdf`/`matplotlib`/`numpy`/`yaml` +
组合 `pptx+pypdf`、`pptx+PIL`、`pptx+PIL+pypdf` + 真实栅格化两条）+ 5 级最小环境阶梯。

### 实测结论（全部 exit 0，`result.json` 无一缺失）

| 形态 | 配置 | 产物数 | deck | 预览 PNG |
|-|-|-|-|-|
| 完整 | D-00、D-03…D-06、C-01、O-01 | 21 / 19 | 有 | 12 |
| 缺 `pptx`（有预览） | D-01、C-01 | 19 | **无** | 12 |
| 缺 `Pillow` | D-02、C-02、C-03、O-02 | **6** | **无** | **0** |

### 三个关键发现

1. **缺 Pillow 会连带让可编辑 `.pptx` 也产不出来** —— `python-pptx` 声明依赖
   `Pillow >=3.3.2`，`deck_builder.py` 的顶层 `try: from pptx import ...` 因此失败。
   只报"缺 Pillow 则没预览"是**不完整**的。
2. **只放行顶层模块 `pptx` 不够** —— 实测报 `non-whitelisted third-party module lxml blocked`；
   传递依赖（`Pillow`/`lxml`/`XlsxWriter`/`typing-extensions`）必须一起在。
3. **`matplotlib`/`numpy`/`yaml` 的缺失是纯 no-op 且可证** —— 三格的 `sys.modules`
   清单里对应模块从未出现，产物与对照格逐项相同。把它们记成"降级通过"是错的，
   正确说法是**本包不依赖它们**。

## 二、运行方法

```bash
# 0) 示例专用：先生成运行时二进制输入
python "$SKILL_DIR/scripts/make_synthetic_inputs.py"

# 1) 最小调用
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out "$OUT"

# 2) 平台运行期形态
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output

# 3) 独立复核（退出码 0 = 通过）
python "$SKILL_DIR/scripts/validate_result.py" "$OUT/result.json"
python "$SKILL_DIR/scripts/check_contract.py"  "$OUT/result.json"
python "$SKILL_DIR/scripts/evidence_audit.py"  "$OUT/result.json"
python "$SKILL_DIR/scripts/verify_deck.py" "$OUT/editable_deck.pptx" --expect-pages <N> --plan "$OUT/talk_plan.json"
python "$SKILL_DIR/scripts/selftest.py" "$OUT" --package-check "$SKILL_DIR"

# 4) ★ 降级探针
python "$SKILL_DIR/scripts/degrade_probe.py" --sandbox /tmp/dg --report /tmp/dg/r.json
```

退出码（**未变**）：`0` 已产出通过 validate+contract 的 `result.json`（含诚实降级）、
`1` 没有可用的契约结果、`2` 参数用法错误；`degrade_probe.py` → `0` 全部配置可判读、
`1` 有配置连 `result.json` 都没写出来、`2` 参数用法错误。

## 三、输入输出

**输入**：`case.json` + `task.md` + 材料目录（`md`/`txt`/`PDF`/图片；缺省 `<case 目录>/materials`）。

**输出**（契约见 [references/OUTPUT_CONTRACT.md](references/OUTPUT_CONTRACT.md)）：

```
result.json          # 契约字段 + status/sources/uncertainty/change_records/environment + audit{...}
talk_plan.json  plan_gates.json  evidence_map.json  evidence_audit.json  deck_audit.json
editable_deck.pptx   previews/{...}.png  previews/preview_manifest.json  self_check.json
```

**降级时最该看的三个位置**：

| 位置 | 有依赖缺失时 |
|-|-|
| `result.json.status` | 变 `partial`（**不是** `failed`，也不崩） |
| `result.json.artifacts.editable_deck` / `deck_limitation` | `null` + 具体原因字符串 |
| `result.json.uncertainty[]` / `change_records[]` | 至少一条与该依赖相关的条目（实测每格都有） |

## 四、「最小可用环境」三档（均有实测对应格）

| 档 | 装什么 | 实测格 | 得到什么 |
|-|-|-|-|
| 只要契约结果 | 无（Python 标准库） | M-01 | exit 0；**6 个产物**；`result.json` 契约字段齐全；`status=partial` |
| 要预览 | `Pillow` | M-03 | exit 0；**19 个产物**；12 张 PNG 预览 |
| 完整形态 | `python-pptx` + `Pillow` + `lxml`(+`XlsxWriter`/`typing-extensions`) + 可选 `pypdf` | M-04 / M-05 | exit 0；**21 个产物**；deck + 12 张预览 |

```bash
python -m pip install "python-pptx>=1.0" "Pillow>=10" "pypdf>=6"
# 实测为 no-op（不必安装）：matplotlib / numpy / PyYAML
# 本机没有且本包不调用（仅人工核对视觉时需要）：LibreOffice / PowerPoint
```

## 五、依赖

| 依赖 | 用途 | 缺失时 |
|-|-|-|
| Python ≥ 3.8（本机 3.13.9） | 解释器（`degrade_probe.py` 只用标准库） | — |
| python-pptx 1.0.2（验证） | 可编辑 `.pptx` | 跳过 deck（19 个产物），`status=partial`，命令仍返回 0 |
| Pillow 12.x（验证） | PNG 预览 | 跳过预览，**且连带 deck 也不可用**（6 个产物） |
| pypdf 6.x（可选） | PDF 文本抽取 | PDF 记 `parsed=false` 并降级 `partial` |
| LibreOffice / PowerPoint | 真实栅格化 | **本机就没有**；本包不调用，用 PIL 模拟并如实声明 |

无网络依赖、无 cwd 依赖。

## 六、本版没有改任何既有脚本

v9 的全部工作都在**新增** `scripts/degrade_probe.py` 与**新增** `references/DEGRADE-MATRIX.md`；
基线 14 个 `scripts/*.py` 与全部 CLI flag 逐字节保留、行为不变。

## 七、限制与边界

- 拦截器只模拟**导入失败**；"导入成功但运行期抛错"（`status=failed` 路径）未覆盖；
- 未模拟磁盘写满/只读输出目录、无 CJK 字体（本机有 `msyh.ttc`）、跨平台差异；
- 合成案例的 `dataset_card.pdf` 本就缺文件，因此 D-03 只验证"缺 pypdf 不崩"，
  未验证"有 PDF 但缺 pypdf"的降级文案；
- 不负责论文精读成稿、写作成稿与科研绘图素材生产。

## 八、维护与更新

- 新增可选依赖时，**必须**把它加进 `scripts/degrade_probe.py` 的 `PROBES` 与 `ENV_LADDER`，
  并重跑把实测结果回填 `references/DEGRADE-MATRIX.md`（不许手抄数字）；
- 回归自测：按 [TEST.md](TEST.md) 的 T1–T12 跑一遍，最后跑 T13 降级探针；
- 提交前：`selftest.py <out> --package-check "$SKILL_DIR"` 全 ✓，包内无 `__pycache__`、无二进制残留。

## 九、GitHub

见 `GITHUB_URL.txt`（第一行仓库链接）。
