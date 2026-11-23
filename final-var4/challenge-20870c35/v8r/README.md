# academic-talk-organizer v8 · challenge-20870c35（学术汇报内容组织 · slides 组）

把**已有**的论文/研究材料组织成可讲、可编辑、证据可追溯的学术汇报产物，
并且对平台声明的 `output_contract` 做**四形态 × 边界值**的逐格验证。

本包是「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35 的 Skill 交付物，
轴 = **契约四形态 × 边界值矩阵**（v8）。`SKILL.md` 是 Agent 加载入口；
**本轴核心文档**是 [references/CONTRACT-MATRIX.md](references/CONTRACT-MATRIX.md)；
实测命令与观测见 [TEST.md](TEST.md)；五维落点见 [references/RUBRIC_MAP.md](references/RUBRIC_MAP.md)。

> **资源形态**（题面 Runtime contract）：本包**只含 UTF-8 文本资源**
> （`.md/.py/.json/.txt/.csv/.yaml/.yml`）；`.pdf`/`.png`/`.pptx` 一律运行时生成；
> 包内无本机绝对路径、无 `__pycache__`、无符号链接。

## 一、v8 的核心资产：契约矩阵

```bash
$SKILL_DIR=/skills/weekly-skill   # 或本包实际目录；所有脚本自定位，cwd 任意

python "$SKILL_DIR/scripts/contract_matrix.py" \
    --sandbox /tmp/cm \
    --report /tmp/cm/contract_matrix_report.json \
    --emit-md /tmp/cm/matrix-table.md
# 期望：cells=31 unreadable=0 expectation_unmet=0 silent_pass=0，退出码 0
```

31 个格子分布在五条轴上：

| 轴 | 格数 | 覆盖 |
|-|-|-|
| C 容器形态 | 7 | 字符串 / 列表 / 对象 / 数值 / 布尔 / `any` / 嵌套 schema |
| B 边界值 | 9 | 空串 · null 项 · 0 · false · 空数组 · 空对象 · 超长字段名(129) · 非法类型 · 缺 `name` · `container` 键 · 与真产出冲突 |
| S 声明形状 | 6 | 裸列表 / 列表 of dict / dict of type(大写) / JSON-schema / task.md fenced / `required:false` |
| E 非法或缺失 | 8 | 空对象 · 字符串形态 · 非法 JSON · 无契约键 · 表格(<5 行 / ≥5 行) · 空 task.md · 无声明 |
| P 平台额外字段 | 1 | 只声明 1 个字段时仍须与内置默认字段共存 |

每格都真跑主流程（`scripts/main.py` 真子进程），再从 `result.json` / `self_check.json`
**读回** exit / status / 契约字段回显 / 回显值 JSON 类型 / 顶层 null 值 / 契约痕迹条数 / 是否静默通过。

### 实测结论（本机，31 格）

| 项 | 实测 |
|-|-|
| 期望命中 / 未命中 / 无法判读 | **31 / 0 / 0** |
| 退出码集合 | **`[0]`** |
| 契约门 `valid` | **31/31 True** |
| 顶层 `null` 值 | **0 个** |
| 静默通过 | **0**（另逐格声明 3 个"无留痕通道、静默容忍"格：B-01/B-02/E-02） |

**修 D1/D2/D3 之前**同一套矩阵的实测是：**8 格期望不中**、**5 格出现 null（13 个 null 值）**、
**退出码集合 `[0, 1]`**。三个缺陷与逐条修法点名见
[references/CONTRACT-MATRIX.md](references/CONTRACT-MATRIX.md) §1/§2。

## 二、运行方法

```bash
# 0) 示例专用：先生成运行时二进制输入
python "$SKILL_DIR/scripts/make_synthetic_inputs.py"

# 1) 最小调用
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out "$OUT"

# 2) 平台运行期形态
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output

# 3) 独立复核（退出码 0 = 通过）
python "$SKILL_DIR/scripts/validate_result.py" "$OUT/result.json"
python "$SKILL_DIR/scripts/check_contract.py"  "$OUT/result.json"
python "$SKILL_DIR/scripts/check_contract.py"  "$OUT/result.json" --contract '<inline-json>'
python "$SKILL_DIR/scripts/evidence_audit.py"  "$OUT/result.json"
python "$SKILL_DIR/scripts/verify_deck.py" "$OUT/editable_deck.pptx" --expect-pages <N> --plan "$OUT/talk_plan.json"
python "$SKILL_DIR/scripts/selftest.py" "$OUT" --package-check "$SKILL_DIR"

# 4) ★ 契约矩阵
python "$SKILL_DIR/scripts/contract_matrix.py" --sandbox /tmp/cm --report /tmp/cm/r.json --emit-md /tmp/cm/t.md
```

退出码（**未变**）：`0` 已产出通过 validate+contract 的 `result.json`、`1` 没有可用的契约结果、
`2` 参数用法错误；`contract_matrix.py` → `0` 全部格子可判读、`1` 有格子连 `result.json` 都没写出来、
`2` 参数用法错误。

## 三、输入输出

**输入**：`case.json` + `task.md` + 材料目录。**两者都可能声明 `output_contract`**，
声明形态四类（裸列表 / 列表 of dict / dict of type / JSON-schema）都支持；
`task.md` 里**多个 fenced JSON 块**时，后声明的契约覆盖先声明的（并 `warnings.warn` 记录被覆盖块号）。

**输出**（契约见 [references/OUTPUT_CONTRACT.md](references/OUTPUT_CONTRACT.md)，字段块逐字保留）：

```
result.json          # 契约字段 + 页级主结果 + 证据定位 + status/sources/uncertainty/
                     #   change_records/environment + audit{...} + contract{declared_source,
                     #   applied, pipeline_produced_fields, echo_initialized_fields}
talk_plan.json  plan_gates.json  evidence_map.json  evidence_audit.json  deck_audit.json
editable_deck.pptx   previews/{...}.png  previews/preview_manifest.json  self_check.json
```

契约相关的新增可查点：

| 位置 | 字段 | 含义 |
|-|-|-|
| `result.json.contract` | `pipeline_produced_fields` | 管线**真产出**的顶层字段（回显前快照） |
| `result.json.contract` | `echo_initialized_fields` | 由契约回显**补齐**的字段 |
| `self_check.json.contract_check` | `type_conflicts_on_real_values` | 声明容器与真值不一致（**记录但不让门失败**） |
| `self_check.json.contract_check` | `wrong_type` | 非真值字段的类型不符（仍然硬失败） |

## 四、依赖

| 依赖 | 用途 | 缺失时 |
|-|-|-|
| Python ≥ 3.8（本机 3.13.9） | 解释器（`contract_matrix.py` 只用标准库） | — |
| python-pptx 1.0.2（验证） | 可编辑 `.pptx` | 跳过 deck，`status=partial`，其余照常，命令仍返回 0 |
| Pillow 12.x（验证） | PNG 预览（python-pptx 亦依赖它） | 跳过预览；python-pptx 连带不可用 |
| pypdf 6.x（可选） | PDF 文本抽取 | PDF 记 `parsed=false` 并降级 `partial` |

无网络依赖、无 cwd 依赖、不调用 LibreOffice/PowerPoint。

## 五、本版改了哪些既有脚本（逐条点名）

v8 是 v7/v8/v9 三份里**唯一**改了既有脚本的一份，且三处都是**纯增量**：

1. `scripts/common.py`
   - `apply_contract()` +4 行：契约类型解析为 `None` 时回落 `""`（**D2**，禁止 null）；
   - `normalize_output_contract()` 改 1 行：JSON-schema 的 `properties` 里每个名字都按
     "已声明 ⇒ 必须存在"（**D3 前半**）；
   - `parse_output_contract_from_task()` 重写块扫描：**后声明覆盖先声明** + `warnings.warn` +
     把"候选块但用不起来"的具体原因写进返回的 note（**D3 后半**）；
   - **新增** `contract_annotations()` / `contract_specs()`（不改任何既有函数名与签名）。
2. `scripts/check_contract.py`：`check()` 增加**带默认值**的可选参数 `produced_names`，
   返回值增加 `type_conflicts_on_real_values` / `produced_names_supplied`（**D1**）；`main()` 未动。
3. `scripts/finalize_result.py`：契约回显**前**快照产出字段名并传入 `check()`；
   `result["contract"]` 增写两个字段。

其余脚本（含 `main.py`）**逐字节未变**；CLI 参数名/默认值/退出码语义未改。

## 六、限制与边界

- 只在顶层做契约回显；嵌套 `properties` **不逐层填充**（已声明边界，见 C-07）；
- `required:false` 且管线不产出的字段会**跳过**、不出现在顶层（契约规定行为，不算缺陷，见 S-06）；
- 3 个格子（B-01/B-02/E-02）所在的解析路径在 `main.py` 里**没有留痕分支**，
  本版不动 `main.py`，因此逐格声明为"静默容忍"而非"通过"；
- 不负责论文精读成稿、写作成稿与科研绘图素材生产；
- 预览为 PIL 模拟渲染（本机无 LibreOffice）。

## 七、维护与更新

- 改契约行为：改 `scripts/common.py` 的契约三函数；改判定口径：`scripts/check_contract.py`；
- 改完**必须重跑契约矩阵**，并把 `references/CONTRACT-MATRIX.md` §5 的逐格表重新生成
  （`--emit-md` 直接产表，不要手抄）；
- 回归自测：按 [TEST.md](TEST.md) 的 T1–T12 顺序跑一遍，最后跑 T13 契约矩阵；
- 提交前：`selftest.py <out> --package-check "$SKILL_DIR"` 全 ✓，包内无 `__pycache__`、无二进制残留。

## 八、GitHub

见 `GITHUB_URL.txt`（第一行仓库链接）。
