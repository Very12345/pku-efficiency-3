---
name: paper-to-academic-ppt
description: 把论文/研究材料转换成主线清晰、证据可追溯、可编辑的学术汇报 PPT，并把"缺依赖时到底还剩什么"做成逐项实测。本版新增 scripts/degrade_probe.py：在子进程里用受控导入拦截（sys.meta_path finder 抛 ModuleNotFoundError）分别模拟缺 python-pptx / Pillow / matplotlib / numpy / PyYAML，并把 LibreOffice 从 PATH 剥离，逐场景跑真实端到端流程并记录实测降级形态（产物还剩什么、status、是否写出 result.json、退出码、是否有静默降级），另附依赖关系实测与"最小可用环境"清单。实测 8 个场景：缺 python-pptx 或 Pillow → 导入期失败、0 个产物、连 result.json 都没有；缺 matplotlib/numpy → 仍产出 11 个产物但重建图文件不再落盘（uncertainty 如实记录）；缺 PyYAML 与无 LibreOffice → 与基线完全一致；静默降级 0 条。Use when a task asks to turn a paper or research material into an academic slide deck (论文转PPT、学术汇报PPT、slides from paper、presentation from paper) and you need to know what still works when a dependency is missing, especially before promising "graceful degradation" in a constrained runtime.
---

# 论文转学术 PPT（缺依赖降级链实测版 · paper-to-academic-ppt）

"缺库时会优雅降级"是一句谁都会写的承诺，问题在于**降级发生在哪一层、还剩什么、退出码是什么**。
本版把这句话变成逐项实测：用受控导入拦截在子进程里真的把某个库"拿掉"，跑完整的端到端流程，
然后如实记录产物、状态与退出码——包括**静默降级**（自称完成、产物却已经残缺）这种最危险的情形。

```
S0 基线对照  →  S1..S6 缺库场景（真跑）  →  S7 环境场景  →  依赖关系实测  →  最小可用环境清单
degrade_probe.py                 逐场景记录产物/status/退出码          谁依赖谁           写在 DEGRADE-MATRIX.md
```

不负责：论文精读结论、科研绘图美化、学术写作润色；不使用预制答案：正式运行只依据案例
实际提供的文件，`examples/` 仅说明接口。

## 1. 触发条件与适用边界

适用：把论文/研究材料变成学术汇报（主线成立、页级可追溯、模板内可编辑、有预览）；
以及**运行环境受限**、需要先知道"缺了什么会彻底不可用、缺了什么只是少一样产物"的场合。

触发词：论文转PPT、学术汇报PPT、slides from paper、presentation from paper、
依赖缺失、降级、最小可用环境、没有 python-pptx 怎么办、graceful degradation。

不适用：环境完备且只关心成稿质量时，不必跑降级探针（它不改变产物，只测量）。

## 2. 输入 / 输出 / 自定位

| 方向 | 位置（以环境实际挂载为准） | 内容 |
|-|-|-|
| 输入 | `/input/case.json` | `case_id`、`output_contract`、材料/模板定位、受众/时长/页数 |
| 输入 | `/input/task.md` | 任务说明（存在时读取，advisory） |
| 工作 | `/app/work` | 中间件：抽取文本、图片、`deck-spec.json` |
| 输出 | `/app/output` | `result.json`、`academic_deck.pptx`、`preview-approx-*.png`、`evidence_mapping.md`、`evidence_map.json`、可选 `chart-*.png/.svg` |
| 输出 | 任意（探针目录） | `scenarios/<场景>/out/**`（各场景的产物现场）+ `degrade_matrix.json` + 可选 `DEGRADE-MATRIX.md` |

**自定位**：资源根 = `SKILL.md` 所在目录，记作 `$SKILL_DIR`；所有脚本用
`os.path.dirname(os.path.abspath(__file__))` 解析自身位置，**任意 cwd 都能跑**：

```bash
SKILL_DIR="<SKILL.md 所在目录>"     # 平台安装到 /skills/weekly-skill 时即该路径
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```

`/input` 不存在时先探测 `CASE_PATH` / `OUTPUT_DIR` 或 cwd 下的 `case.json`，
**以实际可读文件为准**。

## 3. 资源清单与 CLI 契约（`$SKILL_DIR`）

| 入口 | 作用 | 参数（**全部保留**） |
|-|-|-|
| `scripts/main.py` | 端到端：CP1 lint → 抽取 → 生成 → 预览 → 导出检查 → result.json | `--case` `--task` `--spec` `--materials` `--out` `--demo` `--verbose` |
| **`scripts/degrade_probe.py`（本版新增）** | **降级链实测**：受控导入拦截 + 环境剥离，逐场景真跑并记录产物/status/退出码 | `--case` `--spec` `--entry` `--python` `--out` `--only` `--timeout` `--emit-md` `--json` `--redact-paths` `--quiet` |
| `scripts/assetkit.py` | 素材层：材料定位、PDF 抽取、按表格数字重建图（**matplotlib 缺失时的降级点**） | `--pdf` `--out` |
| `scripts/deckgen.py` | 生成层：模板适配 + 页级排版 + 备注 + 证据映射页 + 形状命名（**模块级导入 python-pptx**） | 库模块 |
| `scripts/ooxml_kit.py` | OOXML 层：主题字体、分层命名、容器健全检查（**模块级导入 pptx.util**） | 库模块 + `__main__` 审计 |
| `scripts/spec_lint.py` | **CP1**：deck-spec 结构校验（BL-1…BL-4，纯标准库） | `--spec` |
| `scripts/export_check.py` | **CP3**：契约回显 + OOXML + 命名 + 证据表一致性（G1–G8） | `--result` `--out-dir` `--case` |
| `scripts/check_contract.py` | 契约顶层字段覆盖核对 | `--result` `--contract` `--case` `--quiet` |
| `scripts/preview.py` | PIL 近似预览（**模块级导入 Pillow**） | 库模块 |
| `scripts/make_template.py` | **运行期生成**回退模板 `.pptx`（pptx 延迟导入，缺库时退出码 2） | `--out` `--name` `--no-starter` |
| `scripts/make_synthetic_inputs.py` | **运行期生成**合成夹具（PIL/matplotlib/PDF 均为延迟导入） | `--out` |
| `scripts/cli_io.py` | 控制台加固 | 库模块 |

| 文档 / 资源 | 作用 |
|-|-|
| `references/OUTPUT_CONTRACT.md` | result.json 顶层字段清单 + 四形态回显 + G1–G8（**必读**） |
| `references/DEGRADE-MATRIX.md` | **本版主轴**：8 个场景逐项实测 + 模块可导入性矩阵 + 依赖关系实测 + LibreOffice 口径 + 最小可用环境（由 `--emit-md` 现场生成） |
| `references/degrade-matrix-data.json` | 降级矩阵原始记录（含每个场景的产物清单与 uncertainty） |
| `references/slide-blueprint.md` | 论文→页面蓝图映射 + deck-spec schema + 逐页证据表格式 |
| `references/RUBRIC_MAP.md` | 五维评分 → 本包落点 + 对照协议 |
| `references/failure-modes.md` | 失败模式与降级策略 + 依赖缺失逐库对照 + 退出码语义 |
| `references/layer-naming.md` | PPTX 分层命名规范 |
| `examples/` | 最小示例（合成案例，标注"示例，非正式案例"） |

依赖（**实测结论见 §6**）：`python-pptx`（含其 Pillow 依赖）为硬依赖；`matplotlib` 为软依赖
（缺则重建图跳过）；`PyYAML` 未被主流程使用；PDF 解析三选一。

## 4. 执行阶段 G0–G6（检查点 CP1 / CP3 / **CP5 环境前置**）

### G0 环境前置（本版新增的检查点 CP5）
1. 先问三个问题，再决定怎么跑：**`python-pptx` 能导入吗？Pillow 能导入吗？matplotlib 能导入吗？**
   ```bash
   python "$SKILL_DIR/scripts/degrade_probe.py" --out "<探针目录>" --only S0-baseline,S1-no-pptx,S2-no-PIL
   # 输出三元组：基线是否成功 / 缺 pptx 会怎样 / 缺 Pillow 会怎样
   ```
2. 判断规则（来自实测，见 `DEGRADE-MATRIX.md` §1/§5）：**pptx 或 Pillow 缺 → 端到端不可用**
   （导入期失败、0 个产物、连 `result.json` 都没有），此时应当**先装依赖**而不是继续跑；
   **只有 matplotlib 缺 → 可以继续**（重建图跳过、被如实记录）。
3. 读 `task.md`（若存在）与 `/input/case.json`，记录 `case_id` 与 `output_contract` 清单。

### G1 读实际文件（不许按标签假设内容）
4. 抽取材料：
   ```bash
   python "$SKILL_DIR/scripts/assetkit.py" --pdf "<材料路径>" --out /app/work/extract
   ```
   PDF 库三选一逐级回退；无库时转文本并**如实记录工具**。

### G2 蓝图规划（论文结构 → 页面骨架）
5. 按 `references/slide-blueprint.md` §1 重写为 问题→方法→证据→结论→局限 页序；
   抽页级证据（图/表/公式编号、页码、图注、数值与单位**逐字**带出）。

### G3 写 deck-spec.json + **CP1**
6. 按 schema 写 `/app/work/deck-spec.json`（每页 `claim` + ≤6 条短语化 bullets +
   `evidence` 或 `evidence_gap` + `notes`）。
7. **CP1 检查点**：`python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json`
   （纯标准库，任何缺库环境都能跑——这也是它被放在生成之前的理由之一）。

### G4 构建可编辑源
8. 端到端入口：
   ```bash
   python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
     --spec /app/work/deck-spec.json --out /app/output
   ```
9. 模板三铁律：只填占位符、不碰 master、布局按名匹配→索引回退→内置版式；
   无模板是正常分支（`deck.template.kind="builtin"` + `uncertainty`）。

### G5 渲染与 **CP3**
10. 无 Office 引擎时预览为 PIL 近似（`preview-approx-*.png`，文件名 + `kind` +
    `rendered_with` 三处标注）。
11. **CP3 导出检查**：
    ```bash
    python "$SKILL_DIR/scripts/export_check.py" --result /app/output/result.json \
      --out-dir /app/output --case /input/case.json
    ```

### G6 写 result.json + 交付前环境复核 + 自评
12. 字段清单以 `references/OUTPUT_CONTRACT.md` §1 为准：
    ```bash
    python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
      --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case /input/case.json
    ```
13. **交付前环境复核（CP5）**：确认本次运行用到的依赖都在，且"哪些能力没用上"被记录：
    ```bash
    python "$SKILL_DIR/scripts/degrade_probe.py" --out "<探针目录>" \
      --emit-md "<探针目录>/DEGRADE-MATRIX.md"
    # exit 0 = 测量完成且没有静默降级；exit 3 = 基线对照都跑不通（先修环境）
    ```
14. 按 `references/RUBRIC_MAP.md` 五维自评，补足可复跑证据（测试记录 → TEST.md）。

预算纪律：总 64 次模型请求 / 900 秒 / 单响应 16384 tokens（含推理）；脚本运行秒级
（单次端到端 1.3–1.5 s；8 个场景的降级矩阵约 32 s），不占模型预算大头。

## 5. 决策规则 L01–L12（依赖 / 环境 / 材料 / 模板 / 契约 / 状态）

| # | 情形 | 决策（做什么 → 记录在哪） |
|-|-|-|
| L01 | `python-pptx` **或** Pillow 不可导入 | **不要继续跑端到端**：导入期就会失败、0 个产物、连 `result.json` 都写不出（实测 S1/S2/S6）。先装依赖；用户坚持无依赖时改为交付"材料抽取 + deck-spec + 预览占位"的诚实部分产物 → `DEGRADE-MATRIX.md` §1 |
| L02 | 只有 `matplotlib`（或 numpy）缺失 | 继续跑：重建图跳过、`charts[].chart.reason` 与 `uncertainty` 记明、`chart-*.png/svg` 不落盘；**其余 11 个产物照常**（实测 S3/S4） |
| L03 | 出现"自称完成但产物残缺" | 视为**静默降级**（探针会把它单列并让退出码变 1）：必须让某一层如实记录（`uncertainty` / `status=partial`） → `degrade_probe.py` 报告的 `silent_degrade` |
| L04 | LibreOffice 缺失 | 无需处理：实测管线**从不调用** `soffice`（静态扫描 0 处调用），预览恒为 PIL 近似且如实标注；不要声称"已生成真 PDF 预览" → `DEGRADE-MATRIX.md` §4 |
| L05 | 依赖关系推断 | 不要凭包名猜：实测 `python-pptx → Pillow`、`matplotlib → numpy/Pillow`、`Pillow ↛ python-pptx`；把"两个独立硬依赖"写成"python-pptx（含其 Pillow 依赖）" → `DEGRADE-MATRIX.md` §3.5 |
| L06 | 材料缺失/PDF 加密/无文本层 | 不补造；`status=failed` 或 `partial`，如实记录工具与原因 → `sources` + `uncertainty` |
| L07 | 图/表抽不出 | 保留**显式占位框**（标注"需补齐，非原图"），不伪造 → `figure.placed=placeholder` + `uncertainty` |
| L08 | 模板不可用/损坏/占位符不足/文件不存在 | 内置 16:9 学术版式回退；需要模板时跑 `make_template.py`（缺 pptx → 退出码 2） → `deck.template.kind` + `uncertainty` |
| L09 | 页数超限 | 合并/精简并记录，绝不静默丢证据页 → `page_budget_met=false` + `change_records` |
| L10 | 契约字段未知/无值 | 四形态按类型给 `""`/`[]`/`{}`，**禁止 null**；语义字段取真实值 → `check_contract.py` exit 0 |
| L11 | 状态一致性 | `completed` 只允许"材料可读 + deck 生成 + 预览生成 + 无未标注缺口 + CP1 通过"；任一降级即 `partial`/`failed` → `status` + `uncertainty` |
| L12 | 探针本身可疑 | 用 `--only S0-baseline --entry <一个什么都不写的入口>` 做阴性对照：基线对照失败时探针退出码应为 3（实测如此） → 报告 `summary` 与退出码 |

被降级的任何步骤都必须把"发生了什么 + 影响"写进 `uncertainty` / `change_records`，
并在最终回复里说明限制。

**与基线 D 编号的对应**（`references/failure-modes.md`、`slide-blueprint.md` 里出现的
D 编号按此行解读，CLI 与退出码语义未变）：L06 = D1/D2/D3、L07 = D5、L08 = D6/D11、
L10 = D10、L11 = 状态一致性约束；**L01–L05、L09、L12 为本版新增或细化**。

## 6. 本版实测数字（降级矩阵，可复核）

| 场景 | 屏蔽 | exit | `result.json` | status | 产物数 | 判定 |
|-|-|-|-|-|-|-|
| S0 基线对照 | （无） | 0 | 是 | completed | 13 | full success |
| S1 缺 python-pptx | `pptx` | 1 | **否** | — | **0** | crash |
| S2 缺 Pillow | `PIL` | 1 | **否** | — | **0** | crash |
| S3 缺 matplotlib | `matplotlib` | 0 | 是 | completed | 11 | full success（重建图不落盘，uncertainty 记录） |
| S4 缺 numpy | `numpy` | 0 | 是 | completed | 11 | 同上（matplotlib 因 numpy 缺失而失效） |
| S5 缺 PyYAML | `yaml` | 0 | 是 | completed | 13 | 与基线一致（管线不使用 yaml） |
| S6 缺 pptx+Pillow | `pptx,PIL` | 1 | **否** | — | **0** | crash |
| S7 无 LibreOffice | （PATH 剥离） | 0 | 是 | completed | 13 | 与基线一致（管线不调用它） |

- **静默降级 0 条**（探针退出码 0）；崩溃 3 条（S1/S2/S6），全部是"导入期失败、无产物"，
  属于**响亮失败**而不是静默；
- 模块可导入性：屏蔽 pptx 或 Pillow 时 12 个模块只剩 7 个可导入
  （`deckgen`/`ooxml_kit`/`preview`/`export_check`/`main` 全部失败）；其余场景 12/12；
- 依赖关系实测：`import pptx`（屏蔽 PIL）→ 失败；`import matplotlib`（屏蔽 numpy 或 PIL）→ 失败；
  `import PIL`（屏蔽 pptx）→ 成功；
- LibreOffice 静态扫描：11 个管线脚本中 3 处提及（都是注释/字符串），**0 处调用**；
- 探针耗时：8 个场景 + 9 个依赖探测约 32 s。

## 7. 交付前自查清单（逐条）

- [ ] **CP5 已跑**：`pptx`/`Pillow` 可用；若 `matplotlib` 不可用，已知重建图会跳过且被记录；
- [ ] 已读真实 `case.json` / `task.md` / 论文文件；已把 `output_contract` 抄成字段清单；
- [ ] deck-spec 按蓝图规划，每页有 `claim`；bullets ≤6 条；`evidence` 或 `evidence_gap` 二选一；
- [ ] 页上数字/单位/方法名/图号与论文逐字一致（抽查 3 处以上）；
- [ ] notes 与页面文字分离，`notes_separated=true`（含封面/收尾页）；
- [ ] `/app/output` 内存在：`result.json`（19 字段 + `case_id`）、`academic_deck.pptx`、
      `preview-approx-*.png`、`evidence_mapping.md` + `evidence_map.json`；
- [ ] `export_check.py` → `valid=true` 且 exit 0；`check_contract.py` → exit 0（无 null）；
- [ ] **降级矩阵 exit 0、静默降级 0 条**；任何降级都能在 `uncertainty` 里找到对应条目；
- [ ] status / uncertainty / change_records 诚实；已按 RUBRIC_MAP 五维自评。

## 8. 限制与口径边界

- 降级矩阵**未覆盖 PDF 解析库**（示例材料是纯文本）、未覆盖三缺以上组合、
  未覆盖系统级故障（字体目录为空/只读输出目录/磁盘满）——逐条见 `DEGRADE-MATRIX.md` §6；
- 拦截是**模块级**的：它模拟"这个库不存在"，不模拟"库存在但某个 API 行为不同"；
- 本机基线环境就没有 LibreOffice，因此 S7 只是把"不存在"显式化，实质证据是静态扫描；
- 预览为 PIL 近似渲染，不等同于 PowerPoint/LibreOffice 结果；
- `charts[].chart.file` 携带输出目录绝对路径（已知限制）；模板适配为"占位符级"；
- **非 `main` 入口的启动方式**：`scripts/*.py` 中只有 `main.py` 自己把脚本目录插入 `sys.path`，
  其余入口按 `python "$SKILL_DIR/scripts/x.py"` 的方式设计；若用 `-c` 之类的方式包一层启动，
  需要同时把 `scripts/` 放进 `PYTHONPATH`，否则会以 `ModuleNotFoundError: cli_io` 这类
  **假故障**失败（这是启动方式问题，不是降级路径，本包实测中已区分）；
- 包内**只携带文本资源**；模板、预览、示意图等二进制一律运行时生成或由案例提供。

## 9. 维护（改什么就重跑什么）

| 改动 | 必须重跑 |
|-|-|
| `scripts/*.py` 的导入链（新增/移动 import） | `degrade_probe.py`（可导入性矩阵会变）+ `main.py` + 两道交付门 |
| 新增依赖或去掉依赖 | 更新 `DEGRADE-MATRIX.md` §3.5 的 `DEP_PROBES` 与 §5 的最小可用环境清单 |
| 新增降级分支 | 必须同时写进 `uncertainty`，并同步 `references/failure-modes.md` 与 SKILL.md §5 的 L 规则 |
| 版本 | `scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；本版新增 `scripts/degrade_probe.py`，**既有 11 个脚本逐字节未改** |
