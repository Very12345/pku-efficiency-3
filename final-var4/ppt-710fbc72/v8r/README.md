# Academic Slide Adapter — 学术 PPT 模板与格式适配 Skill（slides 组）
## 本轴：契约四形态 × 边界值矩阵（v8）

`ppt-710fbc72`（玻尔产品周赛·北大专区·学术效率）的可运行 Skill 包。

**功能不变**：两阶段工作流（先出适配方案 `adopt_plan.json` + CP1 门，再按方案真实
套用模板建册 + CP2/CP3 门），逐页主张 + 图号引用 + 讲稿备注 + 页→来源证据映射，
统一页脚页码、图表等比适配，交付 `deck.pptx` + PNG 预览 + `result.json`。

**本轴新增的是"交付契约的行为证据"**：

| 新增 | 作用 | 判据 |
|-|-|-|
| `scripts/contract_matrix.py` | 把 `output_contract` 的 6 种容器形态 + 14 个边界值 + 6 个输入缺陷逐个注入并真跑，再用**独立门**复查 | exit 0（无静默通过） |
| `references/CONTRACT-MATRIX.md` | 26 用例逐行实测 + 静默通过清单 + 未覆盖声明 | 与实测报告一致 |

**一句话结论（实测 26 用例）**：六种容器形态全部**保持声明类型**并按类型默认值回显；
`null` 占位 **0/26**；`0`/`false`/`""`/`[]`/`{}` 等 falsy 值**仍然出现在顶层**；
契约键未回显 **0 个**；**静默通过 0 个**。两处"值被改写"（`preview_png:false` 被
按真值改写为 `true`；非对象契约触发诚实失败并让 `result.json` 降级为 14 键）已在
`references/CONTRACT-MATRIX.md` §5 逐条说明。

**本包只含 UTF-8 文本资源**（≤50 个、单文件 ≤500KB、合计 ≤2MB、无符号链接）；
模板/示例图/预览一律**运行时生成**。

## 运行方法

环境：Python 3.9+；运行必需 `python-pptx` + `Pillow`。
本机实测：Python 3.13.9 / python-pptx 1.0.2 / Pillow 12.3.0。
无 LibreOffice 时预览为 PIL 示意图（如实标注，**不产伪 PDF**）。

`$SKILL_DIR` = 本包根目录；**所有命令在任意 cwd 下都能跑**。

**① 正式流程**：

```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> --task <task.md> --out <out>
```

**② 契约矩阵实验**（`--run` 必须包外；包内跑会留下 `__pycache__`，资源契约拒收）：

```bash
RUN=<包外目录>
python "$SKILL_DIR/scripts/contract_matrix.py" --skill "$SKILL_DIR" --run "$RUN" \
    --json "$RUN/contract_matrix_report.json" --markdown "$RUN/contract_matrix.md"
echo "exit=$?"        # 本机实测 0
```

常用开关：`--list` 列用例；`--only A01,B06` / `--skip C05` 只跑部分；
`--timeout 180` 单次超时。

**③ 契约门**：

```bash
python "$SKILL_DIR/scripts/validate_result.py" --case <case.json> --result <out>/result.json
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --out-dir <out> --case <case.json>
```

## 判据速查

| 项 | 要求 |
|-|-|
| 契约键集合 | 契约里每个键都必须出现在 `result.json` 顶层 |
| 容器类型 | 与声明一致（string/array/object/number/boolean/nested） |
| `null` | 顶层**不允许**出现 `null` 占位（哪怕契约自己声明了 `null`） |
| falsy 值 | `0` / `false` / `""` / `[]` / `{}` 必须仍然出现（存在 ≠ 真值） |
| 派生值可查 | 已知语义的键列在 `verification.contract_echo_derived` |
| 静默通过 | **必须为 0**（判定口径见 `references/CONTRACT-MATRIX.md` §2） |

## 依赖与限制

- 运行必需：`python-pptx`、`Pillow`；缺失时如实写 `status=failed`，不静默成功。
- 预览是 **PIL 示意图**，`render_log.json` + `_PREVIEW_ARE_SCHEMATIC.txt` 双重标注。
- **契约只从 `case.json` 读取**：写在 `task.md` 里的契约不被识别（未实现路径）。
- G3 只检查**顶层键存在且非 null**，不校验"回显值是否等于声明值"——这是本轴实测到的
  关键边界，详见 `references/CONTRACT-MATRIX.md` §1/§5。
- **契约不是对象时管线会失败**（既有行为，本轴只报告不修），代价是 `result.json`
  降级为 14 键的失败信封。

## 维护

- 改契约回显或门逻辑 → **必须重跑 `contract_matrix.py`** 并重新渲染
  `references/CONTRACT-MATRIX.md`；实测与声明不符时改**期望值并写明理由**，
  不许放宽用例让它变绿。
- 交付前包外验收：`python validate_pkg.py <包目录>`。

## 许可与来源

参赛作品；示例案例是**合成示意数据**（`examples/README.md` 已标注），不含正式案例
答案；正式案例与白板由平台提供。
