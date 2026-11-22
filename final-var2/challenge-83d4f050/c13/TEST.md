# TEST.md — 自测、机制验证与实测记录（机制与复用版）

> 四部分：**自测三步**（§0–§1）、**机制是否真的生效**（§2，故意失败用例是必跑项）、
> **2026-11-22 实测数字**（§3–§9）、**合规与未解决项**（§10–§11）。
> 所有运行都在**包外临时目录副本**上执行、`cwd` 不是技能根；包内不跑脚本（避免 `__pycache__`）。

## 0. 自测三步

```bash
export SKILL_DIR=/path/to/challenge-83d4f050

# 1) 主路径 → 期望 exit 0 / 7 件产物
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /tmp/t2
# 2) 契约复查 → 期望 exit 0
python3 "$SKILL_DIR/scripts/check_contract.py" --result /tmp/t2/result.json \
    --case "$SKILL_DIR/examples/case.json"
# 3) 图面全检 → 期望 exit 0（30 项、fails=0）
python3 "$SKILL_DIR/scripts/validate_figure.py" --out /tmp/t2
```

## 1. 机制验证信号（四问，对应 M1–M6）

| 问 | 怎么看 | 期望 |
|---|---|---|
| M2 门还活着吗？ | 把某实体 `type` 改成枚举外值（如 `banana`）后重跑 | **exit 3 / failed**（若返回 0，说明门被绕过） |
| M3 审计在跑吗？ | 两个审计产物是否落盘；`validate_figure.py` 是否 exit 0 | `topology.json` + `legend_audit.json` 存在；exit 0 |
| M4 产物可编辑可追吗？ | SVG 里 `layer-*` 组数与 `data-source` 计数；能否按 id 定位元素 | ≥7 层；`data-source` ≥ 边数；`data-id` 齐备 |
| M5 可复现吗？ | 同输入跑两次比对 sha256 | SVG/PNG/model/topology/legend_audit 一致（PDF 例外） |

**必跑的故意失败用例**：

```bash
python3 - <<'PY'
import json,os
p=os.environ['SKILL_DIR']+"/examples/model.example.json"
m=json.load(open(p,encoding='utf-8')); m['entities'][0]['type']='banana'
json.dump(m,open('/tmp/bad-model.json','w',encoding='utf-8'),ensure_ascii=False)
PY
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file /tmp/bad-model.json --out /tmp/t-bad; echo "exit=$?   # 期望 3"
```

## 2. 2026-11-22 实测环境

| 项 | 值 |
|---|---|
| Python | 3.13.9（Windows 控制台，入口已 reconfigure UTF-8） |
| 可选依赖 | matplotlib ✅、Pillow ✅ |
| 运行位置 | 包外临时目录副本，`cwd` = 临时根（不是技能根） |
| 包内是否跑过脚本 | 否 |

## 3. CLI 组合矩阵（实跑）

| 组合 | 命令要点 | exit | status | gates | 备注 |
|---|---|---|---|---|---|
| A | `--case` + `--model-file` | 0 | success | 8/8 | PNG 203655 B；耗时 2.51 s |
| B | A + `--task examples/task.md` | 0 | success | 8/8 | — |
| C | A + `--verbose` | 0 | success | 8/8 | — |
| D | A + `--dpi 300` | 0 | success | 8/8 | PNG 252382 B |
| E | A + `--formats svg` | 2 | partial | 7/8 | SVG sha16 与 A 相同 |
| F | A + `--formats png` | 2 | partial | 8/8 | 缺 PDF → partial |
| G | A + `--materials-dir <目录>` | 0 | success | 8/8 | 基线版崩溃，见 §7 |

## 4. 主路径产物（实测 sha16 / 字节）

```
diagram.svg 27f344a0dfb2e90f 17771 | diagram.png 9137715961238f3f 203655 | diagram.pdf 108045
result.json 28918 | model.json f93a20a283492f73 11418
topology.json eb826fc5557fccfc 1434 | legend_audit.json efdb1805c839d648 1807
```

## 5. 机制验证结果（对应 §1 的四问）

| 机制 | 实测信号 | 结论 |
|---|---|---|
| M1 规格先行 | 改一处规格 → 1 次重跑（1.76 s）→ SVG/PNG/PDF 全部重生成、新标签出现在 SVG | ✅ |
| M2 raw 门 | 枚举外类型 → **exit 3**、`reason` 说明、只写 `result.json`（14 键） | ✅ 门生效 |
| M3 双审计 | `topology.json` + `legend_audit.json` 落盘；`validate_figure.py` exit 0（30 项、fails=0） | ✅ |
| M4 分层与溯源 | 7 个 `layer-*` 组；18 处 `data-source`；元素带 `data-id/data-type` | ✅ |
| M5 确定性 | 双跑：SVG/PNG/model/topology/legend_audit 逐字节一致（5/6）；PDF 内含时间戳 | ✅（PDF 例外已声明） |
| M6 契约 | 信封 19/19、顶层 null 0、gates 8/8、exit 0；`check_contract.py` exit 0 | ✅ |

**对照（同一批运行）**：把同样的两条审计命令指向**没有这套机制的产物**（扁平 SVG，
由随包的 `scripts/baseline_emulator.py` 复现，见 `ASSET-INDEX.md` A13）→ `check_contract.py` exit **1**（无 `result.json`）、
`validate_figure.py` exit **1**（`ok=False`）；图层 0、`data-source` 0、`data-id` 0。
⇒ M3/M4/M6 的"没有它会怎样"在实测里成立。完整对照口径见 `references/MECHANISM.md` §4。

## 6. 降级路径实测

| 场景 | exit | status | 机制层的表现 |
|---|---|---|---|
| `--formats svg` | 2 | partial | M4 不受影响（SVG 与全量运行逐字节相同）；`gates.g5_png=false` |
| `--formats png` | 2 | partial | PNG 203655 B 正常，PDF 缺失 |
| 自动草稿（未核验） | 2 | partial | M1 规格未核验 → `verified_by_agent=false`、`warnings=1`（`P03`） |
| schema 门失败 | 3 | failed | M2 生效；只写最小信封（14 键） |
| 材料不可解析 | 3 | failed | M1 输入不可得；`reason=manual-required` |

## 7. `--materials-dir` 缺陷修复（基线 → 本版）

| 版本 | 实测 |
|---|---|
| 基线 | exit **1**，`TypeError: _path_normpath: path should be string… not list`，无产物 |
| 本版 | exit **0**，success，7 件产物 |

根因：argparse `action="append"` 给 list，`resolve_paths()` 按 str 处理；修复只做入参归一化，
不改参数名与退出码语义（详见 `worklog.md` §4）。
> 这也是 `ASSET-INDEX.md` §5 的第 1 条坑：复用时不要把这个修复丢掉。

## 8. 复用路径自测（照 `ASSET-INDEX.md` §3 走一遍）

| 步骤 | 实测 |
|---|---|
| 搬骨架（scripts/assets/契约文件） | 目录复制完成，脚本仍在任意 cwd 下可跑（自定位） |
| 换语义（schema/palettes/语义表三处同步） | 本包自身即"已同步"状态：图例覆盖检查 L01/L02 通过 |
| 验一遍（0 / 0 / 0 / 3） | 主路径 0、契约 0、全检 0、故意失败用例 3 —— 与 `ASSET-INDEX.md` §3 的期望一致 |

## 9. 合规自检

| 项 | 实测 | 上限 |
|---|---|---|
| 文件数 | 见 `validate_pkg.py` 汇报（39） | 50 |
| 扩展名 | 仅白名单七种 | `.md .py .json .txt .csv .yaml .yml` |
| 二进制 / `__pycache__` / 符号链接 | 无 | 禁止 |
| 包内本机盘符绝对路径 | **0 命中**（排除 URL 方案前缀后；无需豁免项） | 禁止 |
| 单文件 / 总字节 | 均远低于 500KB / 2MB | 500KB / 2MB |

## 10. 未解决项（如实）

1. **科学判断上限**不由机制保证：类型枚举能挡住"枚举外的类型"，挡不住"类型判错"（MECHANISM §5）。
2. 美观度不作承诺；布局是确定性规则布局。
3. 跨领域复用时必须重定义枚举与配色，否则会制造新的错误（`ASSET-INDEX.md` §5 第 3–5 条）。
4. failed 路径的 14 键最小信封是脚本既有行为；本版记录而未改脚本（属接口层）。
5. PDF/`result.json` 非确定性；PNG 跨 matplotlib 版本可能变化。
6. Windows GBK 控制台下中文摘要显示为乱码（文件内容始终 UTF-8）。
