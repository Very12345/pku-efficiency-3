---
name: scientific-figure-craft
description: >
  科研数据图表生成与编辑 Skill（v7 · 字节级可复现轴）。当输入包含科研数据表格
  （CSV/TSV/JSON）、统计结果、实验记录或生物源材料，或需要生成/编辑示意图、机制图、
  流程图、柱状图、折线图、散点图、箱线图、热图、扇区图、通路图、多面板组合图
  （关键词：figure、chart、plot、diagram、数据图、科研绘图、机制图、通路图、
  graphical abstract、SVG、可编辑图稿、制图、出图、可复现、确定性）时使用。
  本版把「同输入同参数重复运行是否逐字节一样」变成一条可跑的命令与一个四档阶梯：
  scripts/determinism.py 跨进程 / 跨 cwd / 跨 PYTHONHASHSEED 连跑 N 次，对全部
  产物做 sha256 比对，并按 N1–N4 归一化规则逐字段定位不稳定来源（时间戳 / 运行根
  路径 / 自引用哈希 / PDF 内嵌日期）。流程仍是：读契约 → 盘点材料 → 抽取 → 规格门
  → 生成分层可编辑 SVG + PNG/PDF → 双校验 → 契约落地，只是每一步都留下可复跑的
  字节证据。严格以真实文件为准，不臆造数据、不提交预制答案。
---

# 科研数据图表生成与编辑 · v7（字节级可复现轴）

面向「玻尔产品周赛 · 北大专区 · 学术效率 · 第三期」 `challenge-1bd90d8a`。

本题的「结果可核验性」不是一句形容词 —— 它等价于一个问题：
**别人拿同一份 `case.json` 和同一组参数再跑一次，能不能得到同一张图、同一份 `result.json`？**
这一版把这个问题做成了可执行的东西：`scripts/determinism.py`。

## 0. 本版的轴：把「可复现」拆成可判定的一步

| # | 断言 | 可复跑证据 |
|-|-|-|
| A1 | 可编辑源（`figure-*.svg`）、预览位图（`figure-*.png`）、`data_manifest.json`、`validation.json` 是**逐字节可复现**的 | `determinism.py` 实测 6/11 个产物文件在 5 次重复中字节全同 |
| A2 | `result.json` 与两份报告**逐字节不同**，但差异 100% 落在四类已知字段上，施加 N1–N4 后完全一致 | 阶梯 exit 2；`volatile_classes = {"run_root_path": 2, "self_reference_hash": 2, "timestamp": 2}`，无 `unknown` |
| A3 | 产物里还有 4 处本机绝对路径，**不影响同机重跑，但会影响换机复现** | `abs_path_leaks` 4 条，逐条列出文件与字段 |
| A4 | 脚本自定位，`cwd` 轮转 4 种角色（运行目录 / 系统临时目录 / 案例目录 / 技能根）都产出同样结果 | 5 次运行的 `cwd_role` 与 `exit/status/键数` 完全相同 |

实测参数与结果（本机：Windows + Python 3.13.9）：

```
重复 5 次（独立进程）× cwd 轮转 × PYTHONHASHSEED={0,1,12345,7,99}
每次 exit=0、status=completed、result.json 顶层 29 键
→ identical=False，normalized_identical=True，阶梯 exit 2
```

## 1. 先跑这一条命令（本轴的核心）

```bash
# $SKILL_DIR = 本文件所在目录（平台安装期为 /skills/weekly-skill）
python "$SKILL_DIR/scripts/determinism.py" \
    --case /input/case.json --runs 5 \
    --seeds 0,1,12345,7,99 --mode isolated \
    --workroot /app/work/det --out /app/work/det/determinism_report.json
```

它做四件事（缺一不可）：

1. 每一次重复都是**独立进程**（`subprocess`），不是同进程里复用；
2. 每次换一个 **cwd**（运行目录 → 系统临时目录 → 案例目录 → 技能根，循环）；
3. 每次换一个 **`PYTHONHASHSEED`**（证明产物不依赖 dict/set 的哈希顺序）；
4. 每次换一个**输出目录绝对路径**（`--mode isolated`），把「路径泄漏进产物」也一起测。

然后对**输出目录里的全部文件**（不是只对 `result.json` 里登记的那几个）做 sha256 比对，
并给出两级判定：`identical`（原始字节）与 `normalized_identical`（归一化之后）。

退出码就是结论 —— **四档阶梯**：

| 退出码 | 含义 | 拿到它意味着 |
|-|-|-|
| 0 | 全部产物逐字节相同 | 最强；任何人同输入都能得到同一份字节 |
| 2 | 字节级不同，但归一化后完全一致 | 不确定性 100% 被 N1–N4 解释，**不是随机** |
| 3 | 归一化后仍有差异 | 存在未解释的不确定性，报告给首个差异文件与字节偏移 |
| 1 | 至少一次运行没产出可解析的 `result.json` | 无法判定（先修主流程） |

### 1.1 归一化规则 N1–N4（哪些是**故意**不稳定的）

| 规则 | 对象 | 为什么这样定 |
|-|-|-|
| **N1** | JSON 里键名为 `ts` 的值 → `<TS>` | `chartkit.now_ts()` 记的是本地时间；本包把它当审计线索**故意保留** |
| **N2** | 本次运行根路径 → `<RUNROOT>` | `figcheck_report.json` / `mapcheck_report.json` 的 `dir` 写的是输出目录绝对路径 |
| **N3** | `artifacts_sha256.<file>` → 该文件归一化后的 sha256 | 自引用哈希：PDF 日期一变，它跟着变，但不代表内容变了 |
| **N4** | PDF 的 `/CreationDate`、`/ModDate` → `(D:0)` | Pillow 保存 PDF 时嵌的当前时间；实测这是 PDF 唯一的差异来源（`date_only_diff=True`） |

实测四条规则**全部被触发过**（`normalization_rules_applied = N1, N2, N3, N4`），
且 `volatile_fields` 里没有一条 `unknown` —— 差异是被逐字段解释完的，不是"总体看起来差不多"。

### 1.2 对照实验：把「输出目录」这个变量排除

```bash
python "$SKILL_DIR/scripts/determinism.py" --case /input/case.json \
    --runs 3 --mode inplace --workroot /app/work/det-inplace \
    --out /app/work/det-inplace/determinism_inplace_report.json
```

`--mode inplace` 让每次重复都写**同一个绝对输出目录**。实测结果：
逐字节相同的文件从 6/11 升到 8/11，`run_root_path` 这一类**整体消失** ——
证明 `figcheck_report.json` / `mapcheck_report.json` 的唯一不稳定来源就是那个 `dir` 字段。

## 2. 什么时候用 / 什么时候不要用

**适用**：任何「数据表或生物源材料 → 可编辑科研图」的请求；以及任何需要回答
「这张图能不能被别人复现」的场合（投稿、复核、返修、评审留证）。

**不适用**：
- 不做统计推断（显著性只转述源材料给的 p 值，见 D6）；
- 不做实验设计，不替用户下科学结论；
- **阶梯 0 不是本包的运行前提**。本包故意保留 `change_records` 的时间戳，
  所以同机重跑落在阶梯 2（差异已被逐字段解释）；要拿阶梯 0 需要冻结时钟，
  配方写在 `references/DETERMINISM.md` §8。

## 3. 自定位（本轴把它从"约定"变成"被测对象"）

本包所有命令用 `$SKILL_DIR` 前缀；脚本内部一律用
`os.path.dirname(os.path.abspath(__file__))` 解析 `templates/`、`references/`。
这一版更进一步：`determinism.py` **主动轮转 cwd** 来测它 ——
运行目录之外还会用系统临时目录、案例目录、技能根目录各跑一次，四者结果必须一致。

```bash
SKILL_DIR=/skills/weekly-skill
python -c "import sys,os;sys.path.insert(0,os.environ['SKILL_DIR']+'/scripts');import chartkit;print(chartkit.skill_root())"
```

## 4. 输入与输出

### 输入（运行期）
- `/input/case.json`：`case_id`、`figures[]`（图规格）、数据引用、`output_contract`（契约）。
- `/input/task.md` 与材料：源数据表（CSV/TSV/JSON）；生物源材料用于网络/机制图。
- 契约可写成四种形态：字段名列表 / 名称→类型 / 嵌套 `fields` 列表 / 嵌套 `fields` 映射。

### 输出（`/app/output`，UTF-8）
`figure-<id>.svg`（分层可编辑源，文字永远是真实 `<text>`）、`figure-<id>.png` / `.pdf`（预览）、
`data_manifest.json`（图元 ↔ 源数据）、`validation.json`（八类标注校验）、
`mapcheck_report.json` / `figcheck_report.json`（双校验 + G1–G8）、
`result.json`（契约全部字段 + `status`/`sources`/`uncertainty`/`change_records`/`gates`/`artifacts_sha256`）。
中间产物写 `--work`（默认 `<out>/../work`）：`extract.json`、`spec_lint.json`。

## 5. 执行流程（六步，每步都留下可复跑的字节证据）

| 步骤 | 命令 | 本轴新增的判据 |
|-|-|-|
| ① 读契约 | 读 `references/OUTPUT_CONTRACT.md`（字段表 + G1–G8） | —— |
| ② 生成 | `python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output --work /app/work` | `artifacts_sha256` 覆盖每个产物 → 后续比对有基准 |
| ③ 映射核对 | `python "$SKILL_DIR/scripts/mapcheck.py" --dir /app/output --case /input/case.json` | 图元 ↔ 源数据双向闭合（值核对容差 1e-9） |
| ④ 交付门 | `python "$SKILL_DIR/scripts/figcheck.py" --dir /app/output --case /input/case.json` | G1–G8；G8 要求 status 与产物自洽 |
| ⑤ **确定性实测** | `python "$SKILL_DIR/scripts/determinism.py" --case /input/case.json --runs 5 --workroot /app/work/det --out /app/work/det/determinism_report.json` | ★ 本轴核心：阶梯 0/2/3/1 + `volatile_fields` |
| ⑥ 契约回显复核 | `python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json` | `missing=0 null=0 contract_missing=0` 才算契约落地 |

⑤ 与包内既有的 `verify_rerun.py` 是两个互补口径，不要互相替代：

| 口径 | 覆盖 | 输出 |
|-|-|-|
| `verify_rerun.py`（既有） | 只对比 `result.json` 登记的那几个产物；`result.json` 做时间戳归一化、PDF 做日期剔除 | 一句话 + 逐文件 SAME/DIFF |
| `determinism.py`（本版新增） | **输出目录内全部文件**；跨进程/跨 cwd/跨哈希种子；两级判定 + 逐字段定位 + 绝对路径扫描 | 机器可读 `determinism_report.json` |

## 6. 决策规则（DET1–DET12：分支决定怎么影响「可复现」）

- **DET1 源文件指纹优先**：先对每个输入文件算 sha256 并写进 `result.json.sources`；
  没有指纹的产物不可复核。
- **DET2 不写运行时间进图**：SVG/PNG 里不得出现时间戳（实测 PNG 无 `tIME`/`iTXt`，
  SVG 无时间字段）；时间只允许出现在 `result.json.steps[].ts` 与 `change_records[].ts`。
- **DET3 自引用哈希只记别的文件**：`artifacts_sha256` 在 `result.json` 尚未写出时计算，
  不含自身；一旦发现包含自身，说明写入顺序被打乱。
- **DET4 路径不得进位**：产物 JSON 里的 `file` 字段一律是**相对 `/app/output` 的文件名**；
  确需写绝对路径的字段（`figcheck_report.dir`）已在 `references/DETERMINISM.md` §9 点名。
- **DET5 判定分级**：先看 `identical`，不同再看 `normalized_identical`；
  **不允许**用"归一化后一样"掩盖 `unknown` 类差异。
- **DET6 阶梯不入 status**：确定性是**运行属性**，不写进 `result.json.status`；
  `status` 只描述产物完整性（completed/partial/failed）。
- **DET7 cwd 无关**：任何脚本不得读 `os.getcwd()` 决定资源位置；`cwd` 只用于写用户给的相对路径。
- **DET8 环境如实记录**：`result.json.environment` 记 Python 版本、Pillow 版本、实际发现的字体、
  dpi、`no_network`。缺 Pillow 时如实记 `null` 而不是编一个版本号。
- **DET9 跨机差异要说清**：换机器/换目录后字节不一致时，先看是不是 §9 的绝对路径字段，
  再考虑环境（字体/库版本），不要笼统归因于"环境不同"。
- **DET10 契约与确定性分开判**：契约字段齐不齐看 `check_contract.py`，
  字节稳不稳看 `determinism.py`；两个都过才算这一段可交付。
- **DET11 诚实优先于漂亮数字**：为了让阶梯好看而删除时间戳属于**伪造可复现**；
  正确做法是保留审计字段 + 提供归一化与稳定化两条路。
- **DET12 差异必须落到字段**：报"有差异"时必须给出「文件 + 字段路径 + 类别 + 样例」；
  只给一个布尔值不算证据。

## 7. 失败分支（与本轴相关的部分）

| 情形 | 处置 | 落痕 |
|-|-|-|
| 某次运行的 `result.json` 缺失/不可解析 | 阶梯直接判 1（无法判定），不拿剩下几次硬算 | 报告 `runs[].errors` |
| 归一化后仍有差异 | 阶梯 3，报告给首个差异文件与字节偏移；**不得改判成 2** | `differing_files` + `volatile_fields.unknown` |
| 文件集合在不同运行间不一致 | `file_set_identical=false`，优先查写盘失败/竞态 | 报告顶层字段 |
| PDF 差异不止日期 | `date_only_diff=false`，按"未解释差异"处理 | `binary_notes[].first_diff_offset` |
| 产物里出现非预期绝对路径 | 记进 `abs_path_leaks` 并在文档点名 | 报告顶层字段 |
| Windows 控制台编码非 UTF-8 | 脚本只对 stdout/stderr 做 `errors="replace"`；报告文件始终 UTF-8 | 不影响产物 |
| 缺 Pillow | 主流程降级（PNG/PDF 记缺失），确定性实测照跑并如实记阶梯 | `environment.pillow=null` |

## 8. 脚本与参数（相对 `$SKILL_DIR`；**既有入口与参数一个不少**）

| 脚本 | 参数 | 作用 |
|-|-|-|
| `scripts/main.py` | `--case --out --work --task --data --style --dpi --note --lang --no-pdf` | 单一入口：CP1→CP6，生成全部产物与 `result.json` |
| `scripts/determinism.py` | `--case --runs --seeds --mode --workroot --out --main --json --keep --timeout --abs-policy --quiet` | ★ 本版新增：字节级可复现实测台 |
| `scripts/chartkit.py` | （库；`import chartkit`） | 渲染引擎：Scene → SVG/PNG/PDF + 八类校验 |
| `scripts/extract.py` | `--case --data --out --json` | 列画像 + 实体/关系抽取（`extract.json`） |
| `scripts/spec_lint.py` | `--spec --case --json` | 图规格生成门（exit 2 = 有 error） |
| `scripts/figcheck.py` | `--dir --case --json` | G1–G8 交付门（exit 1 = 有失败项） |
| `scripts/mapcheck.py` | `--dir --case --json` | 图元 ↔ 源数据双向核对 |
| `scripts/verify_rerun.py` | `--case --out --rerun-dir --record-only --dir --json` | 再跑验证 / 记录 sha256 |
| `scripts/check_contract.py` | `--result --case --contract --json` | `result.json` 字段覆盖自查 |
| `scripts/cjkfont.py` | （库） | 中文字体发现与回退链 |
| `scripts/svgtext.py` | （库） | SVG 文本转义/清理 + 防转曲检查 |

只读资源：`templates/`（图规格 schema、结果模板、期刊样式、实体词表）、
`references/`（契约、评分映射、失败模式、编码规范、排版预设、字段映射，以及**本版的
`DETERMINISM.md`**）、`examples/`（合成示例：case/data/entities/material/task + 预期产物说明）。
包内**不含任何二进制**，所有图与预览都由 `main.py` 运行时生成。

## 9. 限制与未解决项

- 阶梯 0 需要冻结时钟；本包选择保留审计时间戳，因此同机重跑落在阶梯 2。
- `figcheck_report.json.dir` / `mapcheck_report.json.dir` 仍是绝对路径（未改既有脚本）。
- 本轮只在 Windows + Python 3.13.9 实测；Linux 上 PDF 的 `/CreationDate` 由哪个库写需重测。
- 未测并发写同一输出目录的场景。
- 统计方法本身不在范围内；机制图自动布局是启发式，复杂图请在 spec 里手给节点坐标。
