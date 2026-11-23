# Academic Slide Adapter — 学术 PPT 模板与格式适配 Skill（slides 组）
## 本轴：缺依赖降级链实测 + 最小可用环境（v9）

`ppt-710fbc72`（玻尔产品周赛·北大专区·学术效率）的可运行 Skill 包。

**功能不变**：两阶段工作流（先出适配方案 + CP1 门，再按方案真实套用模板建册 +
CP2/CP3 门），逐页主张 + 图号引用 + 讲稿备注 + 页→来源证据映射，统一页脚页码、
图表等比适配，交付 `deck.pptx` + PNG 预览 + `result.json`。

**本轴新增的是"环境不完整时会怎样"的实测证据**：

| 新增 | 作用 | 判据 |
|-|-|-|
| `scripts/degrade_probe.py` | 用受控导入拦截 / 空 `PATH` 逐个拿掉依赖，跑真实入口，记录**实测**降级形态；并单独校验"投毒确实生效" | exit 0（无静默通过、无投毒失效） |
| `references/DEGRADE-MATRIX.md` | 10 场景逐项实测 + 最小可用环境清单 + 彻底不可用清单 | 与实测报告一致 |

**一句话结论（实测 10 场景）**：
**硬依赖 = `python-pptx` · `Pillow` · `lxml`**（拿掉任一 ⇒ exit=1、`status=failed`、
只剩失败信封 `result.json`、deck 不产出）；
**非依赖 = `numpy` · `matplotlib` · `yaml` · `reportlab` · LibreOffice**
（拿掉任一 ⇒ 与基线逐项相同：12 个产物、28 个顶层键、deck + 2 PNG）。
**静默通过 0 个，投毒失效 0 个。**

其中 **`lxml` 是间接硬依赖**：本包代码一次都没 import 它，但 `python-pptx` 在包级
`from lxml import etree` ⇒ 缺 lxml 等于缺 pptx。

**本包只含 UTF-8 文本资源**（≤50 个、单文件 ≤500KB、合计 ≤2MB、无符号链接）；
模板/示例图/预览一律**运行时生成**。

## 运行方法

### 最小可用环境（实测）

```bash
python -m pip install "python-pptx>=0.6.21" "Pillow>=9.0"
# lxml 会作为 python-pptx 的依赖自动装上；不要手工省略
```

| 项 | 本机实测 | 可省？ |
|-|-|-|
| Python | 3.13.9 | 否（代码需 3.9+） |
| `python-pptx` | 1.0.2 | **否** |
| `Pillow` | 12.3.0 | **否** |
| `lxml` | 已装（pptx 的依赖） | **否** |
| 系统字体 | 有 | 可省（回退位图字体并记录） |
| LibreOffice / uno | **未装** | **可省**（实测无影响） |
| `numpy`/`matplotlib`/`yaml`/`reportlab` | 已装 | **可省**（实测无影响） |
| 网络 | — | 可省（全流程离线） |

### 命令

`$SKILL_DIR` = 本包根目录（平台装到 `/skills/weekly-skill`）；**所有命令在任意
cwd 下都能跑**（脚本用 `os.path.dirname(__file__)` 自定位）。

```bash
# ① 正式流程
python "$SKILL_DIR/scripts/main.py" --case <case.json> --task <task.md> --out <out>

# ② 缺依赖降级实测（--run 必须包外；包内跑会留下 __pycache__，资源契约拒收）
RUN=<包外目录>
python "$SKILL_DIR/scripts/degrade_probe.py" --skill "$SKILL_DIR" --run "$RUN" \
    --json "$RUN/degrade_report.json" --markdown "$RUN/degrade.md"
echo "exit=$?"        # 本机实测 0

# ③ 契约门
python "$SKILL_DIR/scripts/validate_result.py" --case <case.json> --result <out>/result.json
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --out-dir <out> --case <case.json>
```

常用开关：`--list` 列场景；`--only D01,D06` 或 `--only pptx,lxml` 只跑部分；
`--skip ...` 跳过；`--timeout 180` 单次超时。

## 判据速查（degrade_probe.py）

| 项 | 要求 |
|-|-|
| 每个场景的 exit / status / 是否写 result.json | 与场景声明一致 |
| **投毒有效性** | 每个被投毒的包，`python -c "import X"` 必须**失败**；否则该场景判失败 |
| **静默通过** | 必须为 **0**（= 与声明不符但 exit 0 且 `status=success`） |
| 失败时的诚实性 | 必须有失败信封 `result.json` + `uncertainty` 里的原始异常文本，**不能抛裸栈** |

## 依赖缺失时的行为（实测，不是声明）

| 缺什么 | exit | status | 产物 | deck |
|-|-|-|-|-|
| `pptx` / `PIL` / `lxml` | **1** | `failed` | 1（仅 `result.json`，14 键） | 无 |
| `numpy` / `matplotlib` / `yaml` / `reportlab` / LibreOffice | 0 | `success` | 12 | 有 |

## 限制

- **预览是 PIL 示意图**：无 LibreOffice 时不产伪 PDF；三处标注（`render_log.json`、
  `_PREVIEW_ARE_SCHEMATIC.txt`、`result.json.main_result.preview_is_schematic`）。
  **装了 LibreOffice 也不会**变成真 PDF——这是已被明确放弃的能力，不是缺环境项。
- **未测"中间态"**：本包降级目前是两态（全成功 / 全失败），未观察到"deck 有但预览无"。
- **未测版本过旧**：只测"完全没有"，没测"装了但 API 不兼容"。
- **未测系统库缺失**（如 Pillow 装了但 `libjpeg` 缺失导致的 `IOError`）。
- `degrade_probe.py` 会把包**整体复制**到 `--run/skill` 再执行：既避免污染提交包，
  也保证被测的是"包里那一份字节"。

## 维护

- **改动任何 `import` 或依赖版本 → 必须重跑 `degrade_probe.py`** 并把新报告重新渲染
  进 `references/DEGRADE-MATRIX.md`；新增第三方依赖后先跑一次"把它拿掉"的场景，
  再决定要不要写进必需依赖。
- 交付前包外验收：`python validate_pkg.py <包目录>`。

## 许可与来源

参赛作品；示例案例是**合成示意数据**（`examples/README.md` 已标注），不含正式案例
答案；正式案例与白板由平台提供。
