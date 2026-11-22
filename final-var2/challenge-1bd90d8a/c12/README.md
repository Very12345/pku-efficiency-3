# README.md — 科研数据图表生成与编辑 Skill（增益可验证版）

`challenge-1bd90d8a` · 玻尔产品周赛 · 北大专区 · 学术效率 · 第三期

一句话说明本版的立场：**本 Skill 的价值应当被测量，而不是被声称。**
所以本包除了完整可跑的链路之外，还带一套**口径公开、可复跑的 A/B 对照实验**
（`examples/baseline_agent.py` + `examples/measure_ab.py` + `references/GAIN-PROTOCOL.md`）。

---

## 1. 依赖与安装

| 项 | 要求 |
|-|-|
| Python | 3.8+（开发与实测环境：CPython **3.13.9**） |
| 必需 | 标准库 |
| 推荐 | `Pillow`（渲染 PNG/PDF 预览）。缺失时**自动降级**：SVG 与全部 JSON 照常产出，PNG/PDF 记为缺失并写入 `uncertainty` |
| 对照实验额外需要 | `matplotlib`（**只有** `examples/baseline_agent.py` 用它来构造"基准条件"。主链路完全不依赖它） |
| 非必需 | `cairosvg` / `svgwrite` —— 本包不使用 |
| 网络 | **不需要**，脚本内不做任何网络访问 |
| 字体 | 运行时自动扫描常见字体目录；可用环境变量 `FONT_PATHS` 追加 |

```bash
pip install Pillow            # 可选但推荐
pip install matplotlib        # 仅在你想复跑对照实验时需要
```

**无需安装本包**：`scripts/` 是纯标准库模块，按路径直接调用即可。

---

## 2. 怎么调用

`$SKILL_DIR` = 本包所在目录的绝对路径（平台安装期为 `/skills/weekly-skill`）。
脚本用 `os.path.dirname(os.path.abspath(__file__))` 自定位资源，
**cwd 与技能根不同也能跑**。

```bash
SKILL_DIR=/skills/weekly-skill

# 主链路（阶段 G0→G8 一次跑完）
python "$SKILL_DIR/scripts/main.py" \
       --case /input/case.json --out /app/output --work /app/work --style nature

# 四道复核（全部 exit 0 才算交付合格；main.py 内部已跑过，这里可单独重放）
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json
python "$SKILL_DIR/scripts/figcheck.py"       --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/mapcheck.py"       --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/verify_rerun.py"   --case /input/case.json --out /app/output
```

### 2.1 全部命令行参数

| 参数 | 默认 | 说明 |
|-|-|-|
| `--case` | 必需 | `case.json` 路径 |
| `--out` | `out` | 产物目录 |
| `--work` | 无 | 中间产物目录（`extract.json`、`spec_lint.json`） |
| `--task` | 自动发现 | 显式指定 `task.md` |
| `--data` | 自动发现 | 显式指定数据文件（`;` 分隔多个） |
| `--style` | `default` | 样式预设：`default`/`nature`/`cell`/`prism`/`minimal`/`ppt` |
| `--dpi` | 预设值 | PNG 渲染分辨率，覆盖样式预设 |
| `--note` | 无 | 追加一条人工变更记录进 `change_records` |
| `--lang` | `zh` | 标签语言：`zh` / `en` |
| `--no-pdf` | 关 | 跳过 PDF 预览 |

### 2.2 退出码语义

| 脚本 | 0 | 1 | 2 |
|-|-|-|-|
| `main.py` | `completed` 且 G1–G8 全过 | `failed` | `partial` |
| `figcheck.py` | G1–G8 全过 | 有门未过 | — |
| `mapcheck.py` | 0 mismatch / 0 unmatched | 有 mismatch | — |
| `spec_lint.py` | spec 合法 | 用法/文件错误 | spec 有 error（**不得进入生成**） |
| `check_contract.py` | 字段覆盖完整 | 有 missing/null | 契约文档或 result 不可读 |
| `verify_rerun.py` | 确定性通过 | 有非时间戳差异 | — |
| `examples/measure_ab.py` | 判定完成（**通过数在报告里，不看退出码**） | 参数错误 | — |

---

## 3. 设计：三条不变量（与本版的"可验证"定位直接相关）

1. **可核验优先于可好看**：交付件的 `sha256` 只有在**同输入可复现**时才构成证据。
   因此本包把"确定性"当成硬指标（Q12），并为此修掉了 PDF 时间戳缺陷（见
   `references/GAIN-PROTOCOL.md` §7）。
2. **测量优先于自述**：质量、可编辑性、映射闭合、契约完整性全部有机器判据；
   报告里**同时列出自己不占优的项**（条件 A 通过 Q12），不做选择性报告。
3. **诚实优先于完整**：`status` 与产物事实严格自洽；缺口、缺字、缺依赖一律写进
   `uncertainty`。

### 3.1 对照实验的入口

| 想知道什么 | 看哪里 |
|-|-|
| 对照协议（6 条公平性条件、归一化规则、边界声明） | `references/GAIN-PROTOCOL.md` §2–§3、§6 |
| 12 项指标的定义与判定规则 | `references/GAIN-PROTOCOL.md` §5.1 |
| 实测结果（逐项数字） | `references/GAIN-PROTOCOL.md` §5.2；`TEST.md` T5 |
| 效率侧的数字与"为什么不做耗时声称" | `references/GAIN-PROTOCOL.md` §5.4 |
| 怎么自己复跑 | `references/GAIN-PROTOCOL.md` §4；`examples/README.md` §5 |

---

## 4. 适用范围与限制

**适用**：平台固定 3 个案例；也适用于任何「数据表或生物源材料 → 可编辑科研图」的请求。
支持八种图型：`bar` / `line` / `scatter` / `box` / `heatmap` / `pie` / `network` / `panel`
（`panel` 可递归嵌套；`type: auto` 按列语义自动推断）。

**限制（如实声明）**：
- 不做统计推断——显著性只转述材料给的 p 值。
- 机制/通路图自动布局是启发式的；复杂通路建议在 spec 手给节点坐标。
- PDF 预览是光栅预览嵌入 PDF；矢量可编辑源以 SVG 为准。
- 中文字体依赖运行环境；缺字体时 SVG 走回退链、PNG 记 warn。
- **对照实验的边界**：条件 A 是本包内置的常规做法参照实现，**不是平台官方基础 Agent**；
  本地 12 项指标数字**不等于**平台评分。
- `spec_lint.py` **不核对列存在性**（实测：引用不存在的列仍返回 `VALID`、exit 0）；
  真实兜底在 `mapcheck`。本版未改代码（CLI 与算法接口不得变动）。
- 本包**不含任何二进制资源**，也不含任何预制成品图。

---

## 5. 维护

| 要改什么 | 改哪里 | 注意事项 |
|-|-|-|
| 加一个期刊样式 | `templates/journal_styles.json` 加一个键 | 不用改代码 |
| 加一种关系类型的着色/线型 | `templates/entity_glossary.json` | 不用改代码 |
| 加一个标注检查项 | `scripts/chartkit.py` 的校验段 + `references/OUTPUT_CONTRACT.md` §4 的检查项表 | 契约是机器可读的，改契约 = 同时改文档与脚本两处 |
| 新增必需字段 | `references/OUTPUT_CONTRACT.md` 的 `REQUIRED-FIELDS` 块 + `scripts/main.py` 写入处 | 字段名不得只改一处 |
| 加一张图的图型 | `scripts/chartkit.py` 的场景构建 | CLI 接口不得变 |
| **加一项对照指标** | `examples/measure_ab.py` 加一个 `metric(...)` 调用 | **必须同时写进 `GAIN-PROTOCOL.md` §5.1**，否则指标集与文档脱节 |
| **改对照协议** | `references/GAIN-PROTOCOL.md` §2–§3 | 改了协议必须**重跑并更新 §5.2 的数字**，不允许只改文字 |

**契约一致性铁律**：`references/OUTPUT_CONTRACT.md` 是**机器可读**的
（`check_contract.py` 直接解析其中的 `REQUIRED-FIELDS` 块）。改契约 = 同时改两处。
**指标一致性铁律**：`measures_ab.py` 的指标集与 `GAIN-PROTOCOL.md` §5.1 的表
必须逐条对应 —— 指标集是可复跑实验的一部分，不是可以各改各的文档。
