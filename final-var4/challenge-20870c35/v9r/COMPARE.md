# COMPARE.md — v9（缺依赖降级轴）对照口径：基础 Agent 直接做 vs 加载本 Skill

> 只写**可判定**差异，并列出**不利于本包**的对照结果。
> 数字来自 `TEST.md` 真跑过的命令；平台白板与正式分数由组织方生成，本包不预置、不冒充。

## 1. 对照臂定义

| 臂 | 做法 |
|-|-|
| **A 臂**：基础 Agent 直接做 | 把材料交给基础 Agent，在**同一个缺依赖容器**里让它出 slides。它通常直接 import 失败抛栈、或用 `try/except` 吞掉错误后**静默输出半成品**（既不写结果文件，也不说明缺什么） |
| **B 臂**：加载本 Skill | `python "$SKILL_DIR/scripts/main.py" --case <case> --out <out>`；缺依赖时跳过对应产物但**照常写出 `result.json`** 并记明原因 |

两臂在**同一批缺依赖配置**下比较（12 个配置），输入相同。

## 2. 可判定差异

| # | 差异点 | A 臂（典型） | B 臂（本包实测） | 怎么判 |
|-|-|-|-|-|
| Q1 | 缺 `python-pptx` | 抛 ImportError，或吞掉后不写任何结构化结果 | **exit 0**；19 个产物；`result.json` 完整；`status=partial`；`artifacts.editable_deck=null` + `deck_limitation` | D-01 |
| Q2 | 缺 `Pillow` | 同上 | **exit 0**；6 个产物；`uncertainty` 含「PNG 预览渲染失败或未执行」 | D-02 |
| Q3 | 缺 `pypdf` | 常在解析处崩或静默跳过 | **exit 0**；PDF 记 `parsed=false` + 原因 | D-03 |
| Q4 | 缺 `matplotlib`/`numpy`/`yaml` | 可能报"环境不满足"而拒答 | **exit 0**；与对照格**逐项相同**（本包不依赖它们） | D-04…D-06（`sys.modules` 证明从未加载） |
| Q5 | 三个依赖全缺 | 通常直接失败 | **exit 0**；6 个产物，含完整 `result.json` | C-03 |
| Q6 | 无 LibreOffice | 可能声称"无法导出"而放弃 | **exit 0**；与完整环境逐项相同（用 PIL 模拟并如实声明） | O-01 |
| Q7 | 降级是否可见 | 无记录 | 每个配置都有依赖相关 `uncertainty` 与 `change_records` 条目；`environment` 如实记 null | 报告逐格字段 |
| Q8 | 最少要装什么 | 无说法 | 三档「最小可用环境」+ 逐级阶梯，全部有实测格 | 见 `references/DEGRADE-MATRIX.md` §4/§5 |

## 3. ★ 本轴独有的增益：**"缺什么会丢什么"是可查的表，不是形容词**

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" --sandbox /tmp/dg --report /tmp/dg/r.json
```

实测基线（12 个配置 + 5 级阶梯，全部 exit 0、全部写出 `result.json`）：

| 形态 | 实测格 | 产物数 | deck | 预览 PNG |
|-|-|-|-|-|
| 完整 | D-00、D-03…D-06、C-01、O-01 | 21 / 19 | 有 | 12 |
| 缺 `pptx`（有预览） | D-01、C-01 | 19 | 无 | 12 |
| 缺 `Pillow` | D-02、C-02、C-03、O-02 | **6** | 无 | **0** |

**下界**：没有任何缺依赖形态能让 `result.json` 消失，也没有任何一格返回非零退出码。

## 4. 不利对照（照实写）

1. **缺 Pillow 时本包也产不出 deck** —— 与"有 Pillow 就该有 deck"的直觉相反：
   `python-pptx` 声明依赖 `Pillow`，缺它连 `import pptx` 都失败。
   本包的做法是**如实记录连带关系**（`environment` 两项同时为 null），而不是假装 deck 还能出来。
2. **最坏形态只剩 6 个产物**（页计划/证据链/审计/`result.json`）；
   可编辑演示文件与图形预览**全丢**。这不是"降级得很好"，只是"没有静默、没有崩"。
3. **`status` 恒为 `partial`**（合成案例缺 `dataset_card.pdf`），
   因此本轴无法用 `status` 区分依赖形态，只能看产物清单与 `environment`。
4. **拦截器只模拟导入失败**：`python-pptx` 在盘但 `Presentation()` 抛错的路径未覆盖。
5. **未模拟**：磁盘写满、只读输出目录、无 CJK 字体、跨平台（只在 Windows + Python 3.13.9 实测）。
6. **`pypdf` 的真实解析降级未验证**：合成案例的 PDF 本就缺文件，D-03 只验证了"不崩"。

## 5. 结论边界

本对照证明的是**机制差异与可判定性**，不是平台分数。
平台的三案例 × 三重复公平对照由组织方执行；本包不预置白板、不提交预制答案。
