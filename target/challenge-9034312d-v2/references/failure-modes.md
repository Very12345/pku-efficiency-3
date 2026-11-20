# failure-modes.md — 失败模式与决策规则（D1–D12）清单（v2）

> 与高分包「失败清单显式化」意图对齐：把异常识别与处置写成可查文档，
> 每条都给出 **决策规则 D#**、**现象 → 根因 → 处置 → 证据落点**。
> 机器可判的部分由 `svg_verify.py`/`check.py` 执行；Agent 见 `SKILL.md §5`。

## 0. 决策规则速查（D1–D12）

| 规则 | 触发条件 | 处置 | 状态影响 |
|-|-|-|-|
| D1 | case.json 不存在/不可解析 | 立即终止，写 status=failed 的失败 result.json，说明原因；不猜内容 | failed |
| D2 | 无结构化 entities，仅文本 | 走文本解构（extraction=text-heuristic），uncertainty 说明解构方式 | partial（孤儿实体时） |
| D3 | 关系指向不存在实体（断头） | 丢弃该关系（不画），uncertainty 记录「断头箭头已过滤」，Agent 复核 | partial |
| D4 | 实体无 source 出处 | source=null + 列入 uncertainty.sources，不编造出处 | 记录（success 可保留 w/o 缺失） |
| D5 | 类别/关系不在词表 | model 容错归一化；svg_verify 报 error 违规 → 对照材料修正 | error ⇒ partial |
| D6 | 方向/连接与材料冲突（如流向物料） | 连接规则审计报 error；Agent 用 --merge 修正方向 | error ⇒ partial |
| D7 | 同名/近似实体歧义 | 保留并列入 uncertainty（scope=ambiguity），Agent 决定合并/区分 | 记录 |
| D8 | 画布溢出 | 自动等比缩放居中放入画布（不裁剪）；或 --width-mm/--height-mm 重跑 | 记录 requested vs actual |
| D9 | 本机无中文字体 | fonts.found=false 如实记录；SVG/PDF 不受影响（字体名声明/CID） | partial（字体注意） |
| D10 | PNG/PDF 渲染失败 | 保留已有产物与 SVG 源文件，status=partial，uncertainty 记录异常 | partial |
| D11 | svg_verify 存在 error 级规则违规 | 不得 status=success；列出违规项，用 --merge 修正后重跑 | error ⇒ partial |
| D12 | 材料歧义/信息冲突 | 记入 uncertainty（scope+issue+action），不擅自补造数据 | 记录 |

## 1. 输入与解析类

| 现象 | 根因 | 处置 | D# |
|-|-|-|-|
| case.json 不存在/JSON 坏 | 挂载错误/文件损坏 | 终止并写 failed result，不猜内容 | D1 |
| 只有自由文本，无实体 | 材料未结构化 | 文本解构 + extraction=text-heuristic | D2 |
| 实体名重复/近似 | 材料表述歧义 | 保留并 uncertainty 记录，Agent 决定 | D7 |
| 材料文件引用缺失 | 材料路径写错 | 读取实际文件失败即报错；不伪造材料内容 | D1 |
| 数值/参数缺失 | 材料未提供 | 不编造；与绘图无关的数值不强标（见 RUBRIC_MAP 缺口） | D12 |

## 2. 实体/关系正确性类

| 现象 | 根因 | 处置 | D# |
|-|-|-|-|
| 断头箭头 | 关系引用不存在实体 | model 过滤 + uncertainty；Agent 补连 | D3 |
| 箭头方向反向 | 材料顺序理解错 | 规则审计报错 → --merge 修正方向 | D6 |
| 接口错连（connect 到物料） | 连接语义混淆 | connect 规则报 error → 修正 | D5/D6 |
| sequence 连到非步骤 | kind 标错 | sequence 规则报 error → 修正 kind | D5 |
| 编号错位/断号 | 正文顺序与列序不一致 | G8 检查；Agent 对照正文用 --merge 修正 | D6 |
| 图例与图元不一致 | 图例静态生成 | legend_kinds 校验自动发现（G9） | D11 |

## 3. 渲染/导出/字体类

| 现象 | 根因 | 处置 | D# |
|-|-|-|-|
| PNG 中文变方框 | 本机无 TTF 中文字体 | fonts.found=false 记录；SVG/PDF 仍可用 | D9 |
| PDF 渲染失败 | reportlab 异常 | 保留 SVG/PNG，status=partial | D10 |
| PNG 渲染失败 | Pillow 缺失 | 同上；如实记录 | D10 |
| 画布溢出 | 实体过多/标签过长 | 自动等比缩放；或加大画布重跑 | D8 |
| 长标签重叠 | 文本超盒 | 自动拆行；或 Agent 精简 label | D8 |
| SVG 非法 XML | 渲染 bug | svg_verify 捕获；修复后重跑；不得交付坏文件 | D11 |

## 4. 契约/校验类

| 现象 | 根因 | 处置 | D# |
|-|-|-|-|
| result.json 缺字段 | 契约未全量回显 | check.py G1/G2 发现；修复后重跑 | D11 |
| verify 有 error 违规却报 success | 状态判断错误 | G10 拦截：error 未解决 ⇒ partial | D11 |
| verify_report.json 缺失 | 校验步骤被跳过 | G9 拦截；main.py 恒内置 svg_verify | D11 |
| 契约字段为 null | 映射表未覆盖 | 按契约容器类型补 ""/[]/{}（四形态，禁止 null） | D11 |

## 5. 流程级

| 现象 | 根因 | 处置 | D# |
|-|-|-|-|
| 整体管线异常 | 意外 bug | main.py 兜底写 failed result.json + traceback；不自称成功 | D1 |
| Agent 手动微调 SVG | 复杂装配细节 | 保存后在 change_record 增补 action=manual-edit 记录 | D12 |

> 处置原则：**诚实优先**——无法解决就降级 partial/failed 并说明，绝不伪造状态或数据。