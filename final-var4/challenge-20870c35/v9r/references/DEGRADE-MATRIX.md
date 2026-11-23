# DEGRADE-MATRIX.md — 缺依赖降级链逐项实测

> **数据全部来自真跑**。`scripts/degrade_probe.py` 用**受控导入拦截**
> （子进程 `sys.meta_path` 上的前缀拦截器）模拟评测机缺某个第三方库，然后逐个配置
> 跑完整主流程（`scripts/main.py` 真子进程），再从每格的 `result.json` 与产物目录
> **读回**实测值。拦截只作用于被启动的那个子进程，不改本机任何已安装包。
>
> 复核命令（`$SKILL_DIR` = 含 SKILL.md 的包根；cwd 任意）：
>
> ```bash
> python "$SKILL_DIR/scripts/degrade_probe.py" \
>     --sandbox /tmp/dg --report /tmp/dg/degrade_matrix_report.json
> # 期望：probes=12 unreadable=0 unmet=0; ladder=5，退出码 0
> ```
>
> 实测环境：Python 3.13.9 / win32；本机已装 python-pptx 1.0.2、Pillow 12.3.0、
> pypdf 6.14.2、matplotlib 3.10.6、numpy 2.3.5、PyYAML 6.0.3；
> **`soffice` 与 `libreoffice` 都不在 PATH 上**（`shutil.which` 返回 None）。
> 案例 = 包内合成示例案例 `example-synthalign-talk-01`（其 `dataset_card.pdf` 故意不存在），
> 因此每一格的 `status` 都是 `partial` —— 那是材料缺失的如实降级，与依赖无关。

## 0. 一句话结论

12 个缺失配置 + 5 级最小环境，**全部 exit 0、全部写出 result.json**（`unreadable=0`）；
没有任何一种缺依赖形态会崩、会静默、或丢 `result.json`。
**但代价差异极大**：完整环境 21 个产物；只缺 python-pptx 仍有 19 个；
**一旦缺 Pillow，产物掉到 6 个**（deck 与 12 张预览同时消失）。

## 1. 关键实测发现（三条，都是这次跑出来的）

### 1.1 ★ 缺 Pillow 会**连带**让可编辑 .pptx 也产不出来

`python-pptx` 自己声明依赖 `Pillow >=3.3.2`（`importlib.metadata.distribution("python-pptx").requires`
实测输出：`['Pillow >=3.3.2', 'XlsxWriter >=0.5.7', 'lxml >=3.1.0', 'typing-extensions >=4.9.0']`），
`deck_builder.py` 的顶层 `try: from pptx import ...` 因此失败，整套被判定为
「python-pptx 不可用」。实测证据：

| 格 | 被拦 | `result.json.environment` | 产物数 | deck | 预览 PNG |
|-|-|-|-|-|-|
| D-00 | 无 | pptx=1.0.2 / pillow=12.3.0 / pypdf=6.14.2 | 21 | 有 | 12 |
| D-01 | `pptx` | **pptx=null** / pillow=12.3.0 / pypdf=6.14.2 | 19 | 无 | 12 |
| D-02 | `PIL` | **pptx=null / pillow=null** / pypdf=6.14.2 | **6** | 无 | **0** |
| C-02 | `pptx`+`PIL` | pptx=null / pillow=null | 6 | 无 | 0 |

### 1.2 ★ 只放行顶层模块 `pptx` **不够**，传递依赖必须一起在

最小环境阶梯 M-02（只放行 `pptx`）实测 deck 仍为「无」，原因是
`[degrade_probe] non-whitelisted third-party module lxml blocked`。
把传递依赖一起放行（M-04）后 deck 立刻恢复。⇒ **「装了 python-pptx」与
「能 import python-pptx」是两件事**，安装清单必须写全（见 §5）。

### 1.3 ★ 拦截是否真的生效，由 `sys.modules` 证明

每个子进程退出前把自己加载过的模块清单写成 JSON。实测：

| 被拦模块 | 该子进程里是否加载过 | 结论 |
|-|-|-|
| `matplotlib` | False | 包内**没有任何脚本导入它** —— 这一格是纯 no-op，不是"降级通过" |
| `numpy` | False | 同上（Pillow 的预览路径不经过 numpy） |
| `yaml` / `ruamel` | False | 包内没有 YAML 读取代码（frontmatter 由平台解析），纯 no-op |
| `pptx` | False（D-01/C-01/C-02/C-03/M-01/M-02） | 拦截生效 |
| `PIL` | False（D-02/C-02/C-03/O-02/M-01/M-02） | 拦截生效 |
| `pypdf` | False（D-03/C-01/C-03/M-01…M-04） | 拦截生效 |

## 2. 逐配置实测表（D 单依赖 / C 组合 / O 真实栅格化）

| id | 轴 | 被拦导入 | exit | status | 产物数 | 可编辑 deck | 预览 PNG | 写 result.json | 依赖相关 uncertainty | 判读 |
|-|-|-|-|-|-|-|-|-|-|-|-|
| `D-00` | 对照（不拦） | — | 0 | partial | 21 | 有 | 12 | 是 | 2 条（含 deck 模式说明） | 命中 |
| `D-01` | 单依赖 | `pptx` | 0 | partial | 19 | **无** | 12 | 是 | 「运行环境缺少 python-pptx…本次未生成可编辑 .pptx」 | 命中 |
| `D-02` | 单依赖 | `PIL` | 0 | partial | **6** | **无** | **0** | 是 | 「PNG 预览渲染失败或未执行」+「缺少 python-pptx（PIL 被拦）」 | 命中 |
| `D-03` | 单依赖 | `pypdf` | 0 | partial | 21 | 有 | 12 | 是 | 无新增（本案例 PDF 本就缺文件） | 命中 |
| `D-04` | 单依赖 | `matplotlib` | 0 | partial | 21 | 有 | 12 | 是 | 无（纯 no-op，模块从未加载） | 命中 |
| `D-05` | 单依赖 | `numpy` | 0 | partial | 21 | 有 | 12 | 是 | 无（纯 no-op） | 命中 |
| `D-06` | 单依赖 | `yaml`,`ruamel` | 0 | partial | 21 | 有 | 12 | 是 | 无（纯 no-op） | 命中 |
| `C-01` | 组合 | `pptx`,`pypdf` | 0 | partial | 19 | **无** | 12 | 是 | 缺 python-pptx 条目 | 命中 |
| `C-02` | 组合 | `pptx`,`PIL` | 0 | partial | 6 | **无** | **0** | 是 | 缺 python-pptx + 预览失败两条 | 命中 |
| `C-03` | 组合 | `pptx`,`PIL`,`pypdf` | 0 | partial | 6 | **无** | **0** | 是 | 上述 +「pypdf/PyPDF2 不可用」 | 命中 |
| `O-01` | 真实栅格化 | 无（soffice 本就不在 PATH） | 0 | partial | 21 | 有 | 12 | 是 | 预览为 PIL 模拟（既有条目） | 命中 |
| `O-02` | 真实栅格化 | `PIL` + 无 soffice | 0 | partial | 6 | **无** | **0** | 是 | 预览失败 + 缺 python-pptx | 命中 |

**期望全部命中：12/12**；**无法判读：0**。

### 2.1 产物清单（哪些文件还在）——按形态分三档

| 形态 | 实测格 | 产物数 | 具体文件 |
|-|-|-|-|
| 完整 | D-00、D-03…D-06、C-01、O-01 | 21 / 19 | `result.json`、`self_check.json`、`talk_plan.json`、`evidence_map.json`、`plan_gates.json`、`evidence_audit.json`、`deck_audit.json`、`editable_deck.pptx`、`previews/`（cover + grid + 12 张 slide PNG + manifest） |
| 缺 pptx（有预览） | D-01、C-01 | 19 | 同上**减去** `editable_deck.pptx` 与 `deck_audit.json` |
| 缺 Pillow（预览与 deck 都没） | D-02、C-02、C-03、O-02 | **6** | 只剩 `result.json`、`self_check.json`、`talk_plan.json`、`evidence_map.json`、`plan_gates.json`、`evidence_audit.json` |

⇒ **最坏情况下仍然交付**：页级计划、计划门、证据映射、证据审计、自检与 `result.json`
（含全部契约字段）。丢掉的只有「可编辑 deck」与「图形预览」这两类**可视产物**。

## 3. 哪些功能彻底不可用（硬结论）

| 功能 | 在什么条件下彻底不可用 | 实测依据 |
|-|-|-|
| 可编辑 `.pptx` | 缺 `python-pptx`，**或**缺 `Pillow`（连带），**或**缺 `lxml` 等传递依赖 | D-01 / D-02 / M-02 |
| PNG 预览（含逐页缩略图） | 缺 `Pillow` | D-02、C-02、C-03、O-02 |
| Office 真实栅格化（PDF/PNG 导出保真） | **本机就是不可用**（无 soffice/libreoffice）；本包不调用它，用 PIL 模拟代替并在 `uncertainty` 声明 | O-01 实测：与 D-00 逐项相同 |
| PDF 材料文本解析 | 缺 `pypdf`（退化为「按未解析如实记录」，不崩） | D-03、C-03 |
| 页计划 / 证据链 / 计划门 / 证据审计 / `result.json` | **没有任何一种缺依赖形态能让它消失** | M-01 实测（只剩标准库，6 个产物里仍含 `result.json`） |

## 4. 逐级最小环境阶梯（实测）

| 级 | 放行的第三方顶层模块 | exit | 产物数 | deck | 预览 PNG | status |
|-|-|-|-|-|-|-|
| `M-01` | （无，只有标准库） | 0 | 6 | 无 | 0 | partial |
| `M-02` | `pptx` | 0 | 6 | 无 | 0 | partial（`lxml` 被拦） |
| `M-03` | `PIL` | 0 | 19 | 无 | 12 | partial |
| `M-04` | `pptx`,`PIL`,`lxml`,`xlsxwriter`,`typing_extensions` | 0 | **21** | **有** | **12** | partial |
| `M-05` | 上一级 + `pypdf` | 0 | **21** | **有** | **12** | partial |

> 五级的 `status` 都是 `partial`：这是合成示例案例缺 `dataset_card.pdf` 造成的，
> 与依赖无关（对照格 D-00 在完整环境下同样是 `partial`）。

## 5. 「最小可用环境」清单

### 5.1 只要契约结果（不需要可视化）

```bash
# 无任何第三方依赖：Python 3.8+ 标准库即可
python "$SKILL_DIR/scripts/main.py" --case <case> --out <out> --quiet
# 实测（M-01）：exit 0，产物 6 个，result.json 契约字段齐全，status=partial（deck/预览缺失已记入 uncertainty）
```

### 5.2 要预览（推荐给只做内容复核的场景）

```
python-pptx  ❌ 不需要
Pillow       ✅ 必需（预览）        # 实测 M-03：19 个产物，12 张 PNG
```

### 5.3 要完整形态（可编辑 deck + 预览 + PDF 解析）

```
python-pptx          1.0.2      ✅ 必需
  ├─ Pillow          >=3.3.2    ✅ 立即装（缺它连 import pptx 都失败，见 §1.1）
  ├─ lxml            >=3.1.0    ✅ 必需（缺它 import pptx 直接 ImportError，见 §1.2）
  ├─ XlsxWriter      >=0.5.7    ✅ 随 python-pptx 一起装
  └─ typing-extensions >=4.9.0  ✅ 随 python-pptx 一起装
pypdf                6.14.2     ⭕ 仅当材料含 PDF 时需要（缺了按未解析如实记录）
```

```bash
python -m pip install "python-pptx>=1.0" "Pillow>=10" "pypdf>=6"
# 可选（本包不依赖，实测为 no-op，不必安装）：matplotlib / numpy / PyYAML
# 可选（本机没有；本包不调用，仅用于人工核对 deck 视觉）：LibreOffice / PowerPoint
```

### 5.4 平台评测容器的最小可行安装

按实测，**`python-pptx` + `Pillow` + `lxml` 三者齐备**即可拿到完整形态；
`pypdf` 只在材料是 PDF 时才需要。若容器只允许装一个包，
装 `Pillow` 的收益（12 张预览）大于装 `python-pptx` 的收益（一个 deck 但缺预览时仍 19 个产物）——
两者收益不同类，不能互相替代。

## 6. 未覆盖声明

- **导入成功但运行期抛错**：拦截器只模拟"导入失败"；「python-pptx 在盘但 `Presentation()` 抛错」
  属于 `status=failed` 路径，本探针未覆盖。
- **磁盘写满 / 只读输出目录**：属环境故障而非缺依赖，未模拟。
- **无 CJK 字体**：本机有 `msyh.ttc`，未模拟字体缺失（该路径由 `render.font_status()` 记录）。
- **跨平台**：只在 Windows + Python 3.13.9 上实测；Linux 容器上的差异（如 pypdf 的可选
  `cryptography`）未测。
- **pypdf 的真实解析降级**：合成案例的 PDF 本就缺文件，因此 D-03 只验证了"不崩"，
  未验证「有 PDF 但缺 pypdf」时的降级文案。

## 7. 复核清单

1. 跑 §头部的命令 → 期望 `probes=12 unreadable=0 unmet=0`，退出码 0。
2. 打开报告 JSON，核对 `host_dependency_snapshot`（六个库版本 + 两个 CLI 为 null）
   与本机实际一致。
3. 任取 `D-02`，读 `<sandbox>/probes/D-02/out/result.json`：
   `environment.python_pptx` 与 `environment.pillow` 都应为 `null`，
   `uncertainty` 里应有一条「PNG 预览渲染失败或未执行」。
4. 读 `<sandbox>/probes/D-04/loaded_modules.json`，确认 `matplotlib` 不在里面
   （证明 no-op 判定不是猜的）。
