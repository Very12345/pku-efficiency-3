# README.md — 科研数据图表生成与编辑 Skill（决策显性化版）

`challenge-1bd90d8a` · 玻尔产品周赛 · 北大专区 · 学术效率 · 第三期

本包把「科研数据表 / 生物源材料 → 可直接投稿的可编辑图稿」这条链路做成一条
**有判定门、有决策表、有失败分支**的可执行流程。它不替你选统计方法，也不替你
下科学结论；它保证的是：**图上的每个图元都能回到源数据，标注与图例与数据一致，
交付物可编辑、可复核、可重跑。**

---

## 1. 依赖与安装

| 项 | 要求 |
|-|-|
| Python | 3.8+（开发与实测环境为 CPython 3.13.9） |
| 必需 | 标准库 |
| 推荐 | `Pillow`（渲染 PNG/PDF 预览）。缺失时**自动降级**：SVG 与全部 JSON 照常产出，PNG/PDF 记为缺失并写入 `uncertainty`（SKILL.md FM-E8） |
| 非必需 | `matplotlib` / `cairosvg` / `svgwrite` —— 本包不使用，装了也不会被调用 |
| 网络 | **不需要**，且脚本内不做任何网络访问 |
| 字体 | 运行时自动扫描常见字体目录；含 CJK 标签时优先命中 CJK 字体，可用环境变量 `FONT_PATHS` 追加 |

```bash
pip install Pillow            # 可选但推荐
```

**无需安装本包**：`scripts/` 是纯标准库模块，按路径直接调用即可。

---

## 2. 怎么调用

`$SKILL_DIR` = 本包所在目录的绝对路径（平台安装期为 `/skills/weekly-skill`）。
脚本内部用 `os.path.dirname(os.path.abspath(__file__))` 自定位资源，**cwd 与技能根
不同也能跑**（SKILL.md §2）。

```bash
SKILL_DIR=/skills/weekly-skill

# 主链路：读 case → 生成 SVG/PNG/PDF + manifest + validation + result.json
python "$SKILL_DIR/scripts/main.py" \
       --case /input/case.json --out /app/output --work /app/work --style nature

# 四道复核（全部 exit 0 才算交付合格）
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json
python "$SKILL_DIR/scripts/figcheck.py"       --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/mapcheck.py"       --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/verify_rerun.py"   --case /input/case.json --out /app/output
```

### 2.1 全部命令行参数

| 参数 | 默认 | 说明 |
|-|-|-|
| `--case` | 必需 | `case.json` 路径 |
| `--out` | `out` | 产物目录（图、预览、manifest、validation、报告、`result.json`） |
| `--work` | 无 | 中间产物目录（`extract.json`、`spec_lint.json`） |
| `--task` | 自动发现 | 显式指定 `task.md` |
| `--data` | 自动发现 | 显式指定数据文件（`;` 分隔多个） |
| `--style` | `default` | 样式预设名：`default`/`nature`/`cell`/`prism`/`minimal`/`ppt` |
| `--dpi` | 预设值 | PNG 渲染分辨率，覆盖样式预设 |
| `--note` | 无 | 追加一条人工变更记录进 `change_records` |
| `--lang` | `zh` | 标签语言：`zh` / `en` |
| `--no-pdf` | 关 | 跳过 PDF 预览 |

### 2.2 退出码语义（可靠体验的核心：非零码有确定含义）

| 脚本 | 0 | 1 | 2 |
|-|-|-|-|
| `main.py` | `completed` 且 G1–G8 全过 | `failed`（运行异常） | `partial`（部分图失败或有缺口） |
| `figcheck.py` | G1–G8 全过 | 有门未过 | — |
| `mapcheck.py` | 0 mismatch / 0 unmatched | 有 mismatch | — |
| `spec_lint.py` | spec 合法 | 用法/文件错误 | spec 有 error（**不得进入生成**） |
| `check_contract.py` | 字段覆盖完整 | 有 missing/null | 契约文档或 result 不可读 |
| `verify_rerun.py` | 确定性通过 | 有非时间戳差异 | — |

---

## 3. 设计：三条不变量

1. **溯源闭合**：SVG 图元 ↔ `data_manifest.json` ↔ 源表值，三向闭合由 `mapcheck.py`
   机器执行（不是人工抽查）。任何一环断开，`status` 不得为 `completed`。
2. **契约先行**：先读 `references/OUTPUT_CONTRACT.md` 再动手，交付前用
   `check_contract.py` 复核字段覆盖——把"字段是否齐"从目检变成一条命令。
3. **诚实优先**：`status` 与产物事实严格自洽；缺口、缺字、缺依赖一律写进
   `uncertainty`，绝不把失败写成完成（SKILL.md D10 / D16）。

### 3.1 决策表与失败分支表在哪

- **决策规则 D1–D16**：`SKILL.md` §5，每条为「触发条件 → 动作 → 失败降级 → 落痕字段」。
- **决策优先级**：`SKILL.md` §5.1，四条冲突消解规则。
- **失败分支表**：`SKILL.md` §6，按 FM-M（材料）/ FM-D（数据）/ FM-R（图面）/
  FM-E（导出）/ FM-C（契约四形态）/ FM-X（依赖模板）六族给出速查。
- **详细推理与复验命令**：`references/failure-modes.md`。

---

## 4. 适用范围与限制

**适用**：平台固定 3 个案例；也适用于任何「数据表或生物源材料 → 可编辑科研图」的请求。
支持八种图型：`bar` / `line` / `scatter` / `box` / `heatmap` / `pie` / `network` / `panel`
（`panel` 可递归嵌套，`type: auto` 按列语义自动推断）。

**限制（如实声明）**：
- 不做统计推断——显著性只转述材料给的 p 值（D6）。
- 机制/通路图自动布局是启发式的；复杂通路建议在 spec 手给节点坐标（D13）。
- PDF 预览是光栅预览嵌入 PDF，供检查用；矢量可编辑源以 SVG 为准。
- 中文字体依赖运行环境；缺字体时 SVG 靠回退链、PNG 记 warn（D5）。
- 本包**不含任何二进制资源**，也不含任何预制成品图。

---

## 5. 维护

| 要改什么 | 改哪里 | 不要改什么 |
|-|-|-|
| 加一个期刊样式 | `templates/journal_styles.json` 加一个键 | 不用改代码（D17 式规则化：样式即配置） |
| 加一种关系类型的着色/线型 | `templates/entity_glossary.json` | 不用改代码 |
| 加一个标注检查项 | `scripts/chartkit.py` 的校验段 + `references/OUTPUT_CONTRACT.md` §4 的检查项表 | 改契约须**同时**改文档与脚本两处（契约是机器可读的） |
| 新增必需字段 | `references/OUTPUT_CONTRACT.md` 的 `REQUIRED-FIELDS` 块 + `scripts/main.py` 写入处 | 字段名不得只改一处 |
| 加一张图的图型 | `scripts/chartkit.py` 的场景构建 | CLI 接口不得变 |

**契约一致性铁律**：`references/OUTPUT_CONTRACT.md` 是**机器可读**的
（`check_contract.py` 直接解析其中的 `REQUIRED-FIELDS` 块）。改契约 = 同时改文档与脚本。
