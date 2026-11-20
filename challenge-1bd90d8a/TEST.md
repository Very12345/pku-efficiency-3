# TEST — 本地实测记录

> 全部实测于 2026-11-20（Asia/Shanghai），Windows 11 + Anaconda Python 3.13.9。
> 记录真实命令、真实产物、真实结果；不冒充正式案例。

## 0. 环境

| 项 | 值 |
|-|-|
| OS | Windows 11（Git for Windows Bash） |
| Python | 3.13.9 (Anaconda) |
| Pillow | 12.3.0 |
| 其他库 | matplotlib 3.10.6 / numpy 2.3.5 可用但**未使用**（引擎=标准库+Pillow）；cairosvg/svgwrite 无 |
| 工作目录 | `D:\Work\科学挑战赛\work\efficiency-3\build\challenge-1bd90d8a`（脚本自定位，不依赖 cwd） |

## 1. 示例全链路实测（3 次完整运行，均成功）

命令（每次均先清空输出目录）：

```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-1bd90d8a --style nature --note "final smoke verification"
```

**产物（D:/BuildTemp/smoke-1bd90d8a，最近一次运行）**：

| 文件 | 大小 | sha256（前 16 位） |
|-|-|-|
| figure-fig-01.svg | 21,320 B | ae7edb2b43ad83fe |
| figure-fig-01.png | 84,521 B | 265c7fdd09ab1250 |
| figure-fig-01.pdf | 111,717 B | 5761d052a835de8f |
| figure-fig-02.svg | 12,149 B | eaa641d006bd1a5a |
| figure-fig-02.png | 61,296 B | 599e40b3c4de239c |
| figure-fig-02.pdf | 70,626 B | 4956dc0d9b0d6b4c |
| data_manifest.json | 26,908 B | 0e2f60f34577bb8a |
| validation.json | 2,528 B | b5bffd9ed2cb4e92 |
| result.json | 7,262 B | ac792dbbe7455cd5 |

运行结果（stdout 摘要）：

```
[main] case_id=example-science-figure-01 status=completed figures=['fig-01', 'fig-02'] failed=[]
```

**成功判据**：status=completed；两张图（panel 柱状+折线、network 通路图）全部产出 SVG+PNG+PDF；
无 failed_figures；uncertainty 为空（无隐藏失败）。

## 2. 独立复核（契约 + 文件 + SVG/PNG/PDF）

```bash
python scripts/validate_result.py --dir D:/BuildTemp/smoke-1bd90d8a --case examples/case.json
```

结果：**29/29 PASS**（SUMMARY: ALL PASS），覆盖：result.json 可解析、case_id 与输入一致、
output_contract 字段齐全、SVG/PNG/PDF 全部存在、SVG 良构无外部实体、分层 `<g>`、metadata 溯源块、
data-* 属性（fig-01: 225 处 / fig-02: 115 处）、PNG 可打开（3437×1406 / 1479×1093）、PDF 以 %PDF 头开始。

## 3. 数据 ↔ 图元映射核验（程序化抽查）

对 figure-fig-01.svg 做 XML 解析：

```
bars (data-value, data-category, 柱高px):
  1180.0 '0' 506 | 902.0 '1' 387 | 610.0 '5' 262 | 485.0 '20' 208
significance: data-role=significance-text '**' 存在；significance-line 1 条（0↔20）
```

- 柱值 = `data.csv` 中 `time_h=24` 行（filter 生效），柱高与数值成比例 ✔
- 每根柱带 `data-column`/`data-row-index`/`data-category`/`data-series` ✔
- figure-fig-02.svg：7 节点 7 关系，节点 `data-cite` ∈ {Fig. 2A…2E} ✔

## 4. 标注校验（validation.json）

fig-01：provenance ok / legend-mapping ok / axis-units ok / significance ok / cjk-font ok
（找到 simsun-extg 渲染中文）/ null-handling ok / occlusion ok（0 处重叠）。
fig-02：同前 8 项，occlusion warn（密集网络图标签贴近，诚实记录；SKILL 指示需时手给节点坐标）。

## 5. 重复运行确定性（同输入同参数）

两次运行（`D:/BuildTemp/det-a` 与 `det-b`）逐文件 sha256 对比：

```
data_manifest.json  SAME     figure-fig-01.png SAME    figure-fig-01.svg SAME
figure-fig-02.png   SAME     figure-fig-02.svg SAME    validation.json SAME
figure-fig-01.pdf   DIFF(仅 /CreationDate +4s) figure-fig-02.pdf DIFF(仅日期)  result.json DIFF(时间戳流水)
```

结论：**SVG/PNG/manifest/validation 字节级稳定**；PDF 仅内嵌时间戳不同（Pillow PDF 写入行为）；
result.json 的 steps/change_records 含真实时间戳（过程记录，理应变化）。SKILL D12 承诺如实限定在图稿字节。

## 6. 异常路径实测（可靠体验）

| 场景 | 命令 | 结果 |
|-|-|-|
| 缺源数据 | 空目录 case（无 data_files） | status=partial；uncertainty 明示"未发现任何源数据文件"；不猜内容 ✔ |
| filter 无匹配 | `{"column":"time_h","eq":"99"}` | SpecError 明示可用取值；failed_figures 记录 ✔ |
| network 实体文件缺失 | entities_file 指向不存在路径 | SpecError "文件不存在：…"；failed_figures 记录 ✔ |

（以上由代码路径审阅 + 单例复现验证，未列入正式产物。）

## 7. 结论

- 示例全链路 **成功**：case.json → 2 张可投稿图稿（可编辑 SVG + PNG/PDF 预览）→ 8 类校验 → 契约化 result.json。
- 独立复核 **29/29 PASS**；重复运行图稿字节级稳定；失败分支均如实记录不臆造。
- 本记录只证明 Skill 在**示例输入**上可运行、可复核；不构成任何正式案例成绩。