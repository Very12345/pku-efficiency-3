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

## 6. 资源形态与打包门（R1–R6）—— 平台预检会直接拒包，必须包内自查

> 依据题面英文契约原文：*Skill resources: at most 50 UTF-8 text files, 500KB each and
> 2MB total, no symlinks. Runtime artifacts may be binary and are retained independently
> of final JSON validity.* 违反形态门的包会在预检阶段被判「不支持的文件类型」或
> 「文件数量超限」，**与算法质量无关**；因此把形态也做成可自查的门。

| 门 | 规则 | 处置 | 检查方式 |
|-|-|-|-|
| R1 文本白名单 | 包内只允许 `.md .py .json .txt .csv .yaml .yml`（小写）；**不得**出现 `.pdf/.png/.jpg/.pptx/.svg/.jsonl/.zip/.pyc/.ttf` 等 | 二进制/矢量资源一律删除，改为**运行时生成**（本包的 `figure.svg/png/pdf` 即如此）；确需矢量图时由脚本用字符串模板现场写 SVG | 按扩展名扫描（见 R6 命令） |
| R2 文件数 | ≤ **50** 个（按 `outputs/` 计；平台会把同一份复制到 `results/`，同样要 ≤50） | 合并冗余文档；示例产物只留**文本类**（`examples/output/*/` 已由 7 文件缩到 4 文件/例） | 数文件 |
| R3 体积 | 单文件 ≤ **500KB**，合计 ≤ **2MB** | 大 JSON 精简；不要把运行产物整套塞进包 | 统计字节 |
| R4 符号链接 | 不允许 `symlink` | 复制实体文件；不要用链接"省空间" | 检查 `os.path.islink` |
| R5 无 `__pycache__` | 包内不得有 `__pycache__/`、`*.pyc` | 所有脚本首部置 `sys.dont_write_bytecode = True`；**冒烟/自测后务必删掉脚本目录下的 `__pycache__`** | 扫描 |
| R6 无本机绝对路径 | 包内文本不得含本机绝对路径：「盘符 + 反斜杠」形态（盘符紧跟一个反斜杠）、`/Users/…`、以及 Windows 长路径（UNC 扩展）前缀 | 改为相对路径或运行时值；**字体探测候选路径**属跨平台探测逻辑，改写为正斜杠形式（Windows 根优先取 `%WINDIR%`），可在交付说明里点名保留 | `grep -rnE '(^|[^A-Za-z])[A-Za-z]:[\/]' <包目录>` 应无输出（URL 里的 `https://` 不会被该式命中）；`python validate_pkg.py <包目录>` 应 PASS |

| 常见触发 | 现象 | 处置 |
|-|-|-|
| 包内放了 `figure.pdf` / `*.png` 预览 | 预检报 `unsupported Skill resource: …` | 删；改为运行时由 `export_preview.py` 生成 |
| 示例目录把整套运行产物都带上 | 预检报 `文件数量 N 超过上限 50` | 只保留文本类证据（`evidence/layout/verify_report/result`），其余靠复跑 |
| 本机跑完自测没清 `__pycache__` | 形态门 FAIL（R5） | 删 `scripts/__pycache__/`；脚本已置 `dont_write_bytecode` 防止复现 |
| 文档里粘了本机临时输出目录 | 形态门 FAIL（R6），且会误导回放 Agent | 文档里的路径一律用 `<TMP>`/`$SKILL_DIR`/`/input`/`/app/output` 这类占位与运行时路径 |
