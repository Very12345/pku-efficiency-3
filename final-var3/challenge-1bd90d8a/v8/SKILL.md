---
name: scientific-figure-craft
description: >
  科研数据图表生成与编辑 Skill（v8 · 契约四形态 × 边界值矩阵轴）。当输入包含科研数据
  表格（CSV/TSV/JSON）、统计结果、实验记录或生物源材料，或需要生成/编辑示意图、机制图、
  流程图、柱状图、折线图、散点图、箱线图、热图、扇区图、通路图、多面板组合图
  （关键词：figure、chart、plot、diagram、数据图、科研绘图、机制图、通路图、
  graphical abstract、SVG、可编辑图稿、制图、出图、输出契约、output_contract）时使用。
  本版把「契约四种容器形态都兼容」从声明变成 38 行实测矩阵：scripts/contract_matrix.py
  逐行注入形态与边界值（空串 / 空数组 / 0 / 超长 / 非法类型 / 缺字段 / 布尔 / 字符串 /
  浮点 / 深嵌套），真的跑一遍主流程，再让两个独立校验器（figcheck 的 G2 门、
  check_contract 的字段回显）各判一次，记录 exit / status / 契约回显 / 是否静默通过。
  严格以真实文件为准，不臆造数据、不提交预制答案。
---

# 科研数据图表生成与编辑 · v8（契约四形态 × 边界值矩阵轴）

面向「玻尔产品周赛 · 北大专区 · 学术效率 · 第三期」 `challenge-1bd90d8a`。

交付方的 `result.json` 是本题**唯一的评分产物**，而它的顶层字段由 `case.json` 的
`output_contract` 决定。契约写歪了会怎样？这一版不猜，直接**逐行注入、逐行实测**。

## 0. 本版的轴：把契约兼容性做成 38 行矩阵

| 断言 | 实测证据 |
|-|-|
| 四形态（list / {name:type} / {fields:[…]} / {fields:{…}}）与 22 个别名**回显正确** | 14 行判 `echo_complete`；A1 一次回显 22 个字段全绿 |
| **11 行「一路绿灯但有缺口」**：契约形态不在登记范围内时被静默降级成默认值 | `silent_pass` 清单 + 分型（见 §3） |
| **7 行 `output_contract_applied = true` 却一个声明字段都没回显** | 该布尔值**不能**当契约完整性用 |
| 4 个内部瞬态键被声明时字段会消失，**但 G2 与 check_contract 都抓住了** | 5 行判 `caught`，status 降级 `partial`、main 退出码 2 |
| main.py 与校验器对「空字段名」口径不一致 | 只有 B1 一行 `parser_disagreement=True` |

## 1. 先跑这一条命令（本轴的核心）

```bash
python "$SKILL_DIR/scripts/contract_matrix.py" \
    --case /input/case.json --workspace /app/work/cm \
    --out /app/work/cm/contract_matrix_report.json

# 定点复核（编号见 references/CONTRACT-MATRIX.md）
python "$SKILL_DIR/scripts/contract_matrix.py" --only A2,A4,D5,B1 --json
```

每一行做什么：把案例目录整份复制到 `--workspace/<行号>/`，**只改 `case.json` 的
`output_contract`**，然后

1. 以 `cwd = workspace`（不是技能根）跑 `main.py`（顺带验证自定位）；
2. 用 `figcheck.py --dir <out> --case <case>` 拿 G1–G8（重点看 G2 契约回显门）；
3. 用 `check_contract.py --result <out>/result.json --case <case>` 拿 `contract_missing`；
4. 记 `exit` / `status` / 顶层键数 / 声明字段的回显 / 是否静默通过。

退出码：`0` = 全跑完且无静默通过；**`2` = 存在静默通过**；`1` = 用法或环境错误。
本次实测 exit **2**、38 行 / 64.1 秒，判定分布
`{"echo_complete": 14, "silent_pass": 11, "caught": 5, "no_contract": 8}`。

## 2. 每行落到一个 verdict（判定口径）

| verdict | 含义 |
|-|-|
| `echo_complete` | 声明字段全部回显、非 null，容器类型也对得上 |
| `caught` | 有缺口，但被 main 退出码 / status / G2 / check_contract 任一捕获 |
| `silent_pass` | **有缺口却一路绿灯**：exit 0、status=completed、G2 通过、check_contract 通过，且 `uncertainty` 里没有一句关于契约的说明 |
| `no_contract` | 压根没有声明契约（缺键 / `null` / 假值 / 合法但零字段）—— **合法情形**，不计入静默通过 |
| `run_error` | main.py 没产出可解析的 `result.json` |

判「有没有缺口」时，声明字段的解析**按校验器口径**（`figcheck._contract_fields()` /
`check_contract.contract_fields()` 只过滤非字符串、**不过滤空串**），
并单独比对 main.py 的口径（`apply_output_contract()` 里有 `if not f: continue`）——
两者不一致就记 `parser_disagreement`。

## 3. 静默通过清单（本轴要交的东西）

| 分型 | 行 | 缺口是什么 |
|-|-|-|
| `illegal_shape_tolerated` | F5、F6、B4、B5、B6、B8、D11 | 契约形态不在登记的四形态内（或类型位置写了非字符串），被**降级成默认值**而不是报错 |
| `illegal_shape_applied_true` | D5、D6、D8、D12 | 契约形态完全非法（布尔 / 字符串 / 浮点 / `fields` 是字符串），但 `output_contract_applied` 仍被写成 **true** |

被校验器抓住的 5 行（这是"门有效"的反向证据）：

| 行 | 注入 | 结果 |
|-|-|-|
| A2–A5 | 声明 `warnings_collected` / `_pipeline` / `manifest_figures` / `adjustments_collected` | 字段在最终 `result.json` 里消失 → G2=false、status=partial、exit 2、check_contract exit 1 |
| B1 | 字段名 = 空串 `[""]` | main 跳过空名不写；校验器要求它存在 → 同一份契约两边判断相反 |

## 4. 回放 Agent 应该怎么用这些绿灯

题面要求交付 `result.json`，而"契约是否满足"是评分维度「可靠体验 / 结果可核验性」的直接依据。
本轴的结论给出一条硬规则：

> **不要只看 `output_contract_applied`，也不要只看 main 的退出码。**
> 必须同时跑两条命令，并同时看三个量：
> ```bash
> python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json
> python "$SKILL_DIR/scripts/figcheck.py" --dir /app/output --case /input/case.json
> # 看：missing / null / contract_missing 全为 0；G2 为 true；status 未被降级
> ```

## 5. 输入与输出

### 输入
- `/input/case.json`：`case_id`、`figures[]`、数据引用、`output_contract`（本轴的被测对象）。
- `/input/task.md` 与材料：源数据表（CSV/TSV/JSON）、生物源材料（网络/机制图）。
- 契约四形态：① `["case_id","status"]` ② `{"title":"string"}` ③ `{"fields":[...]}`
  ④ `{"fields":{"title":"string"}}`。**边界值不在登记范围内**（本轴实测的就是这些）。

### 输出（`/app/output`，UTF-8）
`figure-<id>.svg` / `.png` / `.pdf`、`data_manifest.json`、`validation.json`、
`mapcheck_report.json`、`figcheck_report.json`、`result.json`；
中间产物 `extract.json` / `spec_lint.json` 写 `--work`。

## 6. 执行流程（七步，第 ⑤ 步是本版新增）

| 步骤 | 命令 |
|-|-|
| ① 读契约 | `references/OUTPUT_CONTRACT.md`（字段表 + §2 四形态规则 + G1–G8） |
| ② 生成 | `python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output --work /app/work` |
| ③ 映射核对 | `python "$SKILL_DIR/scripts/mapcheck.py" --dir /app/output --case /input/case.json` |
| ④ 交付门 | `python "$SKILL_DIR/scripts/figcheck.py" --dir /app/output --case /input/case.json` |
| ⑤ **契约矩阵实测** | `python "$SKILL_DIR/scripts/contract_matrix.py" --case /input/case.json --workspace /app/work/cm --out /app/work/cm/contract_matrix_report.json` |
| ⑥ 契约回显复核 | `python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json` |
| ⑦ 规格门 | `python "$SKILL_DIR/scripts/spec_lint.py" --spec /input/case.json --case /input/case.json` |

## 7. 决策规则（CM1–CM12：契约分支怎么走）

- **CM1 契约先读后跑**：先判 `output_contract` 属于哪种形态，再决定验收命令看哪些字段。
- **CM2 四形态等价**：`["a"]`、`{"a":"string"}`、`{"fields":["a"]}`、`{"fields":{"a":"string"}}`
  必须给出同样的回显；不等价就是缺陷。
- **CM3 非法形态要留痕**：契约不是四形态之一时，主流程应追加一条 `uncertainty`；
  **本版实测这一点尚未做到**（11 行静默通过），所以回放时必须靠 §4 的三量齐看兜底。
- **CM4 `applied` 不是完整性信号**：`output_contract_applied=true` 与"字段齐了"是两件事
  （实测 7 行反例）。
- **CM5 字段名不得为空**：空字段名会让 main 与校验器判断相反（B1）；给出契约时应拒绝空名。
- **CM6 类型名必须是字符串**：`{"x":0}` / `{"x":true}` / `{"x":["array"]}`
  都会落到默认 `""`（实测），不要用它们表达容器语义。
- **CM7 零字段声明等于没声明**：`{}` / `[]` / `{"fields":{}}` / `{"fields":[]}` 都不产生回显。
- **CM8 别声明内部瞬态键**：`manifest_figures` / `warnings_collected` /
  `adjustments_collected` / `_pipeline` 会被 `pop`，声明它们必然触发 G2 失败。
- **CM9 别名优先**：`editable_source` / `rendered_preview` / `field_mapping` /
  `validation_report` / `figcheck_report` / `mapcheck_report` 等别名指向真实产物，
  比自造字段名更有信息量。
- **CM10 长取值不截断**：超长 title（实测 3605 字符）原样回显；不要为了瘦身截断证据。
- **CM11 缺陷只登记不隐瞒**：矩阵里出现的静默通过必须写进 `references/CONTRACT-MATRIX.md`，
  不允许因为"不好看"而从文档里删掉。
- **CM12 契约与状态分离**：`status` 只描述产物完整性；契约缺口由 G2 / `contract_missing` 表达，
  两者都要过才算这一段可交付。

## 8. 失败分支

| 情形 | 处置 | 落痕 |
|-|-|-|
| 契约缺键 / `null` / 假值 | 合法：`output_contract_applied=false`，不要求字段回显 | `no_contract` |
| 契约形态非法但真值 | **当前会静默容忍**（实测）；回放时按 §4 三量齐看 | `silent_pass` + 分型 |
| 声明字段被 `pop` 掉 | G2 会抓到，status 降级 partial；换一个字段名或改契约 | `caught` |
| 空字段名 | main 与校验器口径不同；去掉空名 | `parser_disagreement` |
| 矩阵某行 main 崩了 | 记 `run_error`，该行不参与统计结论 | 报告 `rows[].errors` |
| 案例目录里有子目录/额外文件 | 整目录复制（跳过 `out/`、`work/`、`__pycache__`），保证注入只发生在副本上 | `<workspace>/<行号>/` |

## 9. 脚本与参数（相对 `$SKILL_DIR`；**既有入口与参数一个不少**）

| 脚本 | 参数 | 作用 |
|-|-|-|
| `scripts/main.py` | `--case --out --work --task --data --style --dpi --note --lang --no-pdf` | 单一入口：CP1→CP6 |
| `scripts/contract_matrix.py` | `--case --workspace --out --only --json --keep --timeout --no-cross --quiet` | ★ 本版新增：契约四形态 × 边界值矩阵实测台 |
| `scripts/chartkit.py` | （库） | 渲染引擎：Scene → SVG/PNG/PDF |
| `scripts/extract.py` | `--case --data --out --json` | 列画像 + 实体/关系抽取 |
| `scripts/spec_lint.py` | `--spec --case --json` | 图规格生成门（exit 2 = error） |
| `scripts/figcheck.py` | `--dir --case --json` | G1–G8 交付门（exit 1 = 有失败项） |
| `scripts/mapcheck.py` | `--dir --case --json` | 图元 ↔ 源数据双向核对 |
| `scripts/verify_rerun.py` | `--case --out --rerun-dir --record-only --dir --json` | 再跑验证 / 记录 sha256 |
| `scripts/check_contract.py` | `--result --case --contract --json` | 契约覆盖自查 |
| `scripts/cjkfont.py` | （库） | 中文字体发现与回退 |
| `scripts/svgtext.py` | （库） | SVG 文本转义 + 防转曲检查 |

包内只含 UTF-8 文本资源；`figure-*.svg/png/pdf` 一律运行时生成。

## 10. 自定位

```bash
SKILL_DIR=/skills/weekly-skill        # 安装到别处就填那个绝对路径
python "$SKILL_DIR/scripts/contract_matrix.py" --case /input/case.json --workspace /app/work/cm
```

`contract_matrix.py` 自己就用 `cwd=<workspace>` 跑主流程（故意的）——
如果脚本依赖 cwd 找资源，这一条命令会立刻暴露问题。

## 11. 限制与未解决项

- 静默降级**只登记、不改脚本**：改 `apply_output_contract` 属于行为变更，会动到既有脚本语义。
- B1 的口径分歧未统一（涉及两个脚本的解析函数）。
- 未覆盖：真实平台案例的具体契约字段、字段取值的科学语义正确性、嵌套深度 > 2、
  CRLF/LF 差异、并发重入。逐条写在 `references/CONTRACT-MATRIX.md` §9。
- 统计推断与实验设计不在范围内。
