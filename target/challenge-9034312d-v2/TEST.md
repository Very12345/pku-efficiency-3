# TEST.md — 本地实测记录（v2；制作子代理 agent-59，2026-11-21 00:50 +08）

> 本文件记录 v2 包在本机的真实执行结果，供复核。
> 机器：Windows 11 / Anaconda Python 3.13.9（命令 `python`）；
> Pillow 12.3.0、reportlab 5.0.0；cairosvg/svgwrite 不可用（SVG 为手写 XML，
> PNG/PDF 由同一布局模型渲染）。
> 工作目录：`D:/Work/科学挑战赛/work/efficiency-3/target/challenge-9034312d-v2`
> （命令均在该目录执行；脚本自定位，不依赖 cwd）。

## T1 编译与导入检查 —— 通过

```bash
python -m py_compile scripts/*.py        # COMPILE OK（8 个脚本全过）
```

## T2 验收冒烟：route 示例 —— 成功（exit 0，status=success，10/10 门全过）

```bash
python scripts/main.py --case examples/case.json --task examples/task.md \
  --out D:/BuildTemp/smoke-challenge-9034312d-v2
```

输出摘要（stdout 回显）：

```
status   : success
verify_ok: true
gates    : G1–G10 全部 true
issues   : []
check_ok : true（exit 0）
```

产物（7 个文件，`D:/BuildTemp/smoke-challenge-9034312d-v2/demo-biotech-route-01/`）：

```
evidence.json      实体 10 / 关系 9 / 证据条目 19 / 材料文件 2（case.json+task.md，含 sha256）
layout.json        布局模型（3 列 = 文库构建/筛选/鉴定；步骤编号 1..7 连续）
figure.svg         可编辑分层 SVG（5 层 layer:*；<text> 真实文本；实体组带 data-source）
figure.png         PNG 预览 2362×1496 px @200 dpi（PIL + msyh.ttc）
figure.pdf         PDF 预览（reportlab 矢量，STSong-Light）
verify_report.json 全绿：layers/editable_text/arrows/numbering/legend_kinds/规则 0 errors 0 warnings
result.json        output_contract 全字段 + case_id + evidence + verify + checksum
```

内容验证（程序化抽查）：
- 实体 10 个带 source（task.md §2.1–§5）；关系 9 条方向正确（E3→E2 质粒→转导、
  E2→E4 转导→药筛、E8→E9 测序→FastQ、E9→E10 FastQ→靶基因）；
- 图例 4 项（step/material/data/milestone）与图面 kind 集合一致；
- `python scripts/check.py <result.json>` → ok:true，G1–G10 全过，issues=[]。

## T3 确定性：同输入两次运行 —— 逐字节一致（含 examples/output 对拍）

```bash
python scripts/main.py --case examples/case.json --task examples/task.md --out D:/BuildTemp/det-A
python scripts/main.py --case examples/case.json --task examples/task.md --out D:/BuildTemp/det-B
```

| 文件 | 两次 sha256 | 结论 |
|-|-|-|
| figure.svg | `f8b01ce26b622187…896e042b`（双跑一致） | SAME |
| layout.json | `c6c8e155bb6cd7f1…b630c16a`（双跑一致） | SAME |
| evidence.json | `63778d5d28e7bcac…69bacaa8`（双跑一致） | SAME |
| verify_report.json | `5ed91e2a4a13df1d…8678415`（双跑一致） | SAME |
| result.json | 仅 `change_record` 时间戳与 `execution.out_dir`（输出路径参数）不同；`checksum` 一致 | 记录差异（预期） |

且 `examples/output/demo-biotech-route-01/` 与 det-A 对拍：figure.svg 等 4 个确定性
文件逐字节一致（route 示例 sha：`f8b01ce26b…`）。

## T4 装置示例（apparatus 三桶布局）—— 成功（exit 0，status=success）

```bash
python scripts/main.py --case examples/apparatus_spec.example.json --out examples/output
```

- 实体 6（material C1 → device C2/C3/C4 → product C5/waste C6），关系 5
  （S1 flow 进样、S2/S3 connect 管路、S4 flow 产物、S5 flow 凝华）；
- verify_report：0 errors 0 warnings，`spec_sha16=4603787adcb287d7`；
- 连接规则生效验证：`product-terminal`（warn）与 `apparatus-flow-into-material`
  （error）均按规则命中/不命中符合预期（本示例无违规 → success）。

## T5 连接规则错误门（负例验证）—— 按预期拦截

构造违规案例（`D:/BuildTemp/violation-case.json`：apparatus 内 V1 流向物料、
V2 sequence 连 container、V3 产物反向流入装置）：

```bash
python scripts/main.py --case D:/BuildTemp/violation-case.json --out D:/BuildTemp/smoke-violation-v2
```

结果（**符合设计，非缺陷**）：
- `status=partial`，`verify_ok=false`，`check_ok=false`（exit 3 → 即 G9 拦截）；
- verify_report errors：`sequence-step-only`（V2）+ `apparatus-flow-into-material`
  （V1），warnings：`product-terminal`（V3）；
- result.json.uncertainty 追加 `scope=rule_violation`（error 违规未解决 ⇒ partial，D11）。

## T6 编辑用例（--merge mutation）—— 成功（exit 0，status=success）

```bash
python scripts/main.py --case examples/case.json --task examples/task.md \
  --merge examples/route_spec.mutation.example.json --out D:/BuildTemp/smoke-merge-v2
```

- 同名替换：E5 图面标签 → 药物（激酶抑制剂）；
- 新 id 追加：E11（DMSO 对照孔 material）+ R10（E6→E4 recycle 复筛回流）+ R11
  （E11→E4 flow 对照孔）；
- change_record 由 1 条增到 4 条（初始生成 + 3 条 agent 人工修正）；by=agent；
- verify_ok=true（recycle warn 列入 warnings，不阻断 success——如设计）；
- checksum 随 entities/relations 变化而变化（编辑生效的机器证据）。

## 限制（如实声明）

- 渲染后端实测为 PIL + reportlab；无 Pillow/reportlab 环境自动降级
  （PNG/PDF 缺失 → status=partial，SVG 源文件不受影响）；
- PNG 中文字体依赖本机 TTF（本机为 msyh.ttc）；无字体时 fonts.found=false 如实记录；
- 实体抽取依赖材料文本结构；复杂表格/多图材料需 Agent 复核证据链（CP1）；
- 示例材料与产物均为合成（标注「示例，非正式案例」），与平台正式案例无关。