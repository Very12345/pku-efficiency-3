# TEST.md — 本地实测记录（v2 加强包，2026-11-21 00:5x +08）

> 本文件记录 v2 包在本机的真实执行结果，供复核与复跑。机器：Windows；Python 3.13.9
> （命令 `python`）；matplotlib 3.10.6、Pillow 12.3.0。全部命令在技能根目录
> `challenge-83d4f050-v2/` 下执行（脚本自定位，不依赖 cwd）。

## T1 编译检查 —— 通过

```bash
python -m py_compile scripts/*.py        # 11 个脚本 COMPILE OK
```

## T2 冒烟：示例案例 + 已核验机制规格（人工核验路径） —— 通过

```bash
python scripts/main.py --case examples/case.json \
    --model-file examples/model.example.json \
    --out D:/BuildTemp/smoke-challenge-83d4f050-v2
```

结果：`status=success`，`exit 0`，`self_check_passed=true`，`failures=0`，`warnings=0`，
`gates=8/8`（G1–G8 全过）。产出 7 个文件（sha256 前缀 / 字节数）：

```
diagram.svg         27f344a0dfb2e90f  17771
diagram.png         9137715961238f3f  203655
diagram.pdf         fa0b6285d93fa777  108045
result.json         d2da107a57edd7f7  29153
model.json          f93a20a283492f73  11418
topology.json       eb826fc5557fccfc  1434
legend_audit.json   efdb1805c839d648  1807
```

实体 9 / 边 9 / 区室 4（4 区室 + 核内嵌胞质），5 类箭头全部在用，负反馈环右侧绕行，
数据映射（表达量 → 节点填充色）与图例一致；`result.json` 含 output_contract 自定义字段
回显（`custom_demo_field`/`custom_list_field`）。

## T3 冒烟：示例案例 + 自动草稿（未核验路径） —— 通过（partial）

```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/t3-draft
```

结果：`status=partial`（`exit 2`，符合设计——自动草稿未人工核验，`verified_by_agent=false`
时不允许 success），`self_check_passed=true`，`failures=0`，`warnings=1`（P03：逆流边
r9 e8→e5 须人工确认是否为反馈环并补 `feedback=true`——正是留给 Agent 核验的信号），
`gates=8/8`。草稿提取器：entities=9，edges=9，method=auto-draft，无解析告警。

## T4 确定性：同输入双跑 —— SVG/PNG/JSON 逐字节一致，PDF 仅有时间戳差异

```bash
python scripts/main.py --case examples/case.json \
    --model-file examples/model.example.json --out D:/BuildTemp/det-A
python scripts/main.py --case examples/case.json \
    --model-file examples/model.example.json --out D:/BuildTemp/det-B
```

| 文件 | 双跑 sha256 | 结论 |
|---|---|---|
| diagram.svg | 27f344a0 / 27f344a0 | **一致**（SVG 无时间戳，为输入+布局纯函数） |
| diagram.png | 91377159 / 91377159 | **一致** |
| model.json | f93a20a2 / f93a20a2 | **一致** |
| topology.json | eb826fc5 / eb826fc5 | **一致** |
| legend_audit.json | efdb1805 / efdb1805 | **一致** |
| diagram.pdf | 79567267 / a088ec23 | 差异（matplotlib 内嵌 PDF CreationDate 时间戳，如实记录） |
| result.json | d2da107a / 不同 | 仅 `provenance.ts` 与 `change_records[].ts` 不同（去除 ts 并归一化运行目录后逐字节一致） |

`self_check.determinism`（model_sha16/svg_sha16）双跑相等。

## T5 契约独立复查 —— 通过

```bash
python scripts/check_contract.py \
    --result D:/BuildTemp/smoke-challenge-83d4f050-v2/result.json \
    --case examples/case.json
# C01–C07 全 pass；contract|ok|case=example-egfr-mapk|status=success — exit 0
```

契约检查：信封字段齐全、status 三值枚举、顶层无 null（四形态回显）、output_contract
字段全部回显、deliverables 路径存在、G1–G8 全过。

## T6 独立全检（build 后 verify 成对）—— 通过

```bash
python scripts/validate_figure.py --out D:/BuildTemp/smoke-challenge-83d4f050-v2
# standalone-verify|ok=True|fails=0|warns=0 — exit 0
```

对产物目录重跑聚合检查（M/T/P/L/E/S/F/D 系列 + schema 门 + 图层命名 + PNG 可打开）。

## T7 schema 门拦截（CP2 阻断）—— 通过

```bash
# 构造 type="banana" 的非法规格（raw 未归一化直接校验，防静默改写）
python scripts/main.py --case examples/case.json --model-file D:/BuildTemp/bad2.json --out D:/BuildTemp/t7
# status=failed，reason="schema gate fail"，exit 3
```

## T8 抽取器独立 CLI —— 通过

```bash
python scripts/extract.py examples/materials/example_material.md
# {"entities": 9, "edges": 9, "method": "auto-draft", "warnings": []}
```

## T9 调试中修复的问题（诚实记录，均为本机实测发现）

1. `mpl_backend.py` 缺 `SKILL_VERSION` 导入 → PNG/PDF 预览 NameError（已补导入）；
2. `extract.py` 对 `- A 动词 B（证据）`（A 与动词间有空格）时 left 尾随空格，
   导致草稿边端点无法解析为实体（9 条边全部脱靶）→ left 增加空白/括号剥离；示例材料
   改写为带空格的写法后 9/9 边可解析；
3. `extract.py` 二遍扫描把"信号流向：…"约束行误抽为实体（10 个实体含垃圾项）→
   要求左侧含（区室）或右侧为"名称（类型）"锚点才建实体，约束行被跳过；
4. schema 门最初校验归一化后的模型，未知 type 被归一化为 other 导致门失效
   （T7 无法拦截）→ 改为对 **raw** 规格校验（CP2 门），T7 实测拦截成功（exit 3）；
5. Windows GBK 控制台打印 `⊆` 等字符 UnicodeEncodeError → 各 CLI 入口 stdout/stderr
   reconfigure UTF-8；
6. 基包 `validate.py→validate_figure.py` 拆分后，结果契约新增 `topology/legend_audit/
   gates` 字段与 `self_check.determinism`，`check_contract.py` C07 门补到 8 门。

## 限制（如实声明）

- 渲染后端本文档实测为 matplotlib（本机可用）；无 matplotlib 环境自动降级
  （SVG 源仍产出，PNG/PDF 缺失如实记录），方法见 `SKILL.md` §8（D9）；
- 实体抽取依赖材料文本结构（表格/`A|动词|B`/`- A 动词 B` 行）；散文/PDF 材料需 Agent
  手工建规格（CP2b），这是刻意"准确率优先"的设计；
- PDF 与 result.json 含时间戳，不作为确定性承诺对象；确定性承诺 = SVG/PNG/model/topology/
  legend_audit（同输入逐字节一致，T4 实测）；
- examples/ 全部标注"示例，非正式案例"，与平台正式 3 案例无关