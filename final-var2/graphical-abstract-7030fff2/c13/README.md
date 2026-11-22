# graphical-abstract — 图形摘要 Skill（文档轴 C：机制与复用）

把一项研究压进**单页**（研究问题 → 方法 → 核心结果 → 结论），交付**可编辑分层 SVG**
（不是位图）、PNG/PDF 预览，以及字段完整的 `result.json`。数值只来自材料，**不编造**。

本包的组织方式不是功能列表，而是**三个机制**：

| 机制 | 一句话 | 没有它会怎样 |
|-|-|-|
| **M1 来源挂接** | 每个科学元素带 `data-src`；没有来源的元素不许上画布 | 图能看但不可查；缺值可能被"看起来合理"的数字填掉 |
| **M2 双 lint 门** | 绘制前拦方案（CP1）、绘制后拦规格；两道门都是退出码判据 | 错误只能在画完之后发现，返工等于整张重画 |
| **M3 契约与状态一致性** | 契约四形态回显（禁 null）；`status` 不得虚报 | 交付态无法自动复核；"图没出来却报成功"这类虚报会发生 |

机制的完整反事实推理、实测负控实验与**失效边界**见 [`references/MECHANISM.md`](references/MECHANISM.md)。

## 0. 自定位

```bash
SKILL_DIR=/skills/weekly-skill        # 官方评测容器
SKILL_DIR=/abs/path/to/<skill-root>   # 本机解压目录
SKILL_DIR="$(pwd)"; while [ ! -f "$SKILL_DIR/SKILL.md" ] && [ "$SKILL_DIR" != "/" ]; do SKILL_DIR="$(dirname "$SKILL_DIR")"; done
```

## 1. 五步跑通

```bash
# ① 方案先行：出骨架（含真实抽取结果与 src 定位）→ 读材料后填 four_elements
python "$SKILL_DIR/scripts/scaffold.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/plan.json

# ② CP1 门（M2）：exit 0 才继续
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan /tmp/plan.json

# ③ 出图（一次命令产出 SVG/PNG/PDF/spec/content/audit/render_log/result.json）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --plan /tmp/plan.json --out /tmp/ga-out

# ④ 规格门（M2，独立复跑）
python "$SKILL_DIR/scripts/spec_lint.py" --spec /tmp/ga-out/spec.json --content /tmp/ga-out/content.json

# ⑤ 契约门（M3）：exit 0 = 顶层覆盖「信封 18 键 ∪ 案例契约」且无 null
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/ga-out/result.json --case "$SKILL_DIR/examples/case.json"
```

官方案例形态：`python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output`

## 2. 参数与依赖

| 参数 | 说明 |
|-|-|
| `--case` / `--task` / `--material` | 案例 / 任务说明 / 材料（缺省从 case 解析） |
| `--plan` | 设计方案（`scaffold.py` 生成、Agent 定稿；可选） |
| `--raster-scale` / `--pdf` / `--no-pdf` | 预览分辨率与 PDF 开关（默认取 `figure_constraints`） |
| `--out` | 输出目录（默认 `<skill>/out`） |

依赖：Python ≥ 3.8（核心流程只用标准库，含纯 Python PNG 回退）；可选 `matplotlib`（默认渲染 + PDF）、
`Pillow`（二级渲染），缺失时逐级回退并写入 `render_log.json`；字体按候选路径运行期探测
（`C:/Windows/Fonts`、`/usr/share/fonts`、`/System/Library/Fonts`）；**不联网**；
`scripts/gain_harness.py`（只读测量器）只用标准库且不出图。

## 3. 可复用资产清单（13 项）

| # | 资产 | 位置 | 拿去做的事 | 复用前必须改 |
|-|-|-|-|-|
| 1 | SVG 图层命名契约 | `references/layer-naming.md` | 让图具备可定位、可机器校验的分层结构 | 新增图层要在契约登记并同步 `audit.py` 的白名单 |
| 2 | 四要素内容知识 | `references/ga-four-elements.md` | 判断什么必须上画布、什么只进图注；面板容量上限 | 领域举例换成你的（Q-M-R-C 不变式保留） |
| 3 | 方案 schema | `references/plan-schema.md` | 把设计决策变成可 lint 的中间产物 | `figure_constraints` 按你的出版要求改 |
| 4 | 结果契约 + 硬性门 G1–G8 | `references/OUTPUT_CONTRACT.md` | 定义你自己的结果字段与交付检查 | **字段名不得改**；新增走契约字段通道 |
| 5 | 面板模板 / 视觉通道 / 色板与字号 | `references/TEMPLATE.md` | 直接套用四列布局与 Okabe-Ito 色板 | 换配色时覆盖 `constraints.palette`；字号下限 8px 建议保留 |
| 6 | 资产三件套 | `assets/spec_template.json`、`result_example.json`、`example_material.txt` | 新案例的方案起点 / 结果形态 / 材料写法 | 替换为你的结构（均为合成示例） |
| 7 | 最小可跑案例 | `examples/` | 5 分钟验证环境与两道门 | 换成你的案例（数值须同时出现在材料里） |
| 8 | 只读测量器 | `scripts/gain_harness.py` | 量任意产物：分层/真文字/覆盖率/四要素/数值可定位/契约/结构指纹 | 无需改 |
| 9 | 对照协议 | `references/GAIN-PROTOCOL.md` | 做一次公平对照，把"改进多少"写成可复算数字 | 条件 B 换成你自己的基线做法 |
| 10 | 机制说明写法 | `references/MECHANISM.md` | 借用"机制 + 反事实 + 失效条件"的写法写你的技术说明 | 换成你的机制；保留"未实现/未验证"一节 |
| 11 | 决策矩阵 | `SKILL.md` §3（K1–K16）+ `references/failure-modes.md` | 沿用"触发→检测→降级→证据"表结构 | 编号两边保持一致 |
| 12 | 两个 exit-code 自查器 | `scripts/spec_lint.py`、`scripts/check_contract.py` | 提交前/CI 当门用 | 契约字段变化时同步信封键集合 |
| 13 | 题集与金标准协议 + 校验清单 | `references/REUSE-KIT.md` | 组织内部可复跑题集与发布前检查 | 难度层按你的材料调整 |

## 4. 复用步骤（三步）

```bash
# ① 换案例：复制 examples/case.json，替换 entities/relations/data/figure_constraints；
#    把每个数值写进你的材料文件（M1 的前置条件）
# ② 跑通五步（见 §1）：scaffold → 方案门 → 出图 → 规格门 → 契约门；门不过就改 plan/spec
# ③ 复核：用同一把尺子量你的产物（可与自己原来的做法对照）
python "$SKILL_DIR/scripts/gain_harness.py" --out /tmp/your-out --case /path/to/your/case.json \
       --material /path/to/your/material.md --label mine
```

详细版（含"复用前必须改什么"逐项、题集/金标准协议、发布前校验清单、扩展点、6 条常见错误）
见 [`references/REUSE-KIT.md`](references/REUSE-KIT.md)。

## 5. 限制与失败处理

- 失败处理全表见 [`references/failure-modes.md`](references/failure-modes.md)（K1–K16，含退出码语义、
  按机制归组的矩阵、**机制管不到的 5 条边界**）；`SKILL.md` §3 为速查版；
- 对错分诊：退出码 0/1/2 → 阶段；`result.status` → 严重度；`audit.json` 六项红线 → 具体规则；
- 已知边界（不掩饰）：`case.json` 数值与材料正文冲突时**不会自动拦截**（实测反例见 `MECHANISM.md` §2④）；
  渲染件只做签名/尺寸/良构检查，不做逐像素回归；对照记录是单案例、单机观测，不做显著性声明；
- `examples/` 为合成示例，与平台正式案例无关；正式案例由平台挂载运行。

## 6. 维护

- 版本号：`scripts/common.py` 的 `SKILL_VERSION`；历史见 git 与 `result.json.change_records`；
- 改东西的规矩（K16）：**规范 / 脚本 / `TEST.md` 三处齐了才算改完** ——
  加图层同步 `layer-naming.md` + `audit.py`；加指标同步 `GAIN-PROTOCOL.md` §3 + `gain_harness.py` + `TEST.md`；
- 更新对照记录时连同不利项一起更新；机制说明里的"未实现/未验证"一节保持最新。
