# TEST.md — 自测清单与期望输出（全维 union 版）

四层自测，**每层都以退出码或实测数字收口**：

| 层 | 回答什么 | 命令 | 期望 |
|-|-|-|-|
| ① 合规 | 技能资源是否合法 | `validate_pkg.py <pkg>` | PASS，0 FAIL |
| ② 健康路径 | 端到端能不能跑 | `main.py` + 两道门 | 0 / 0 / 0 |
| ③ 失败路径 | 坏了会不会被看见 | `fault_inject.py` | 24 条注入，**静默失败 0**，恢复 19/19 |
| ④ 泛化路径 | 换题材还成立吗 | `run_case_set.py` | **3/3 在验收区间内** |

> 全部命令都在**包外副本**上跑（包内跑会生成 `__pycache__`，技能资源只允许文本文件）：
> ```bash
> cp -r "$SKILL_DIR" /tmp/skill-test && S=/tmp/skill-test
> ```

---

## 0. 环境

```bash
python -V                                            # ≥3.8（本机 3.13.9）
python -c "import pptx, PIL; print(pptx.__version__, PIL.__version__)"
python -c "import matplotlib; print(matplotlib.__version__)"   # 可选
```

## 1. 合规层

| # | 命令 | 期望（本版实测） |
|-|-|-|
| 1.1 | `find "$S" -type f \| wc -l` | ≤ 50（本版 **47**） |
| 1.2 | `du -sb "$S"` | ≤ 2 MiB（本版 **~452 KB**） |
| 1.3 | `find "$S" -type f -size +500k` | 空（最大单文件 **57 KB**） |
| 1.4 | `find "$S" -name '__pycache__' -o -name '*.pyc'` | 空 |
| 1.5 | `grep -rnE "([A-Za-z]:[\/])|/Users/|[A-Za-z]:\\\\" "$S"` | 空（字体探测候选路径除外，需点名） |
| 1.6 | `python -m py_compile $(find "$S" -name '*.py')` | 无输出 |

## 2. 健康路径层

```bash
OUT=/tmp/out-healthy
python "$S/scripts/main.py" --case "$S/examples/case.json" \
    --task "$S/examples/task.md" --spec "$S/examples/deck-spec.json" --out "$OUT"
python "$S/scripts/export_check.py" --result "$OUT/result.json" --out-dir "$OUT" \
    --case "$S/examples/case.json"
python "$S/scripts/check_contract.py" --result "$OUT/result.json" \
    --contract "$S/references/OUTPUT_CONTRACT.md" --case "$S/examples/case.json"
```

| # | 检查项 | 期望（本机实测） |
|-|-|-|
| 2.1 | 三个退出码 | **0 / 0 / 0** |
| 2.2 | `status` | `completed` |
| 2.3 | 顶层字段数 | **19** |
| 2.4 | `deck.file` / `slide_count` | `academic_deck.pptx` / **8** |
| 2.5 | `previews` | **7** |
| 2.6 | `evidence_mapping.entries` / `gaps` | **6** / `[]` |
| 2.7 | `uncertainty` | 1（示例声明了未生成的模板 ⇒ 回退内置版式，预期） |
| 2.8 | 换 cwd 再跑 | 仍 exit 0（自定位 M9） |

## 3. 失败路径层（24 条注入）

```bash
cp -r "$S" /tmp/skill-drill
python /tmp/skill-drill/scripts/fault_inject.py --out /tmp/drill \
    --emit-matrix /tmp/drill/matrix.md; echo "exit=$?"
```

| # | 检查项 | 期望（本机实测） |
|-|-|-|
| 3.1 | 健康基线（注入前） | exit 0 / completed / 8 页 / 19 字段 / 7 预览 / 0 uncertainty |
| 3.2 | 注入条数 | **24**（输入 8 · 模板 5 · 依赖 4 · 契约 5 · 状态 2） |
| 3.3 | **静默失败** | **0** |
| 3.4 | 与文档口径不一致 | **0** |
| 3.5 | 恢复演练 | **19/19** 回到 `exit 0 + completed` |
| 3.6 | 已知检测缺口 | **3**（CT-05 / ST-01 / ST-02，见 `failure-modes.md` §4–§5） |
| 3.7 | `fault_inject.py` 退出码 | **0** |
| 3.8 | 包内残留 | 注入后 `__pycache__` 仍为空 |

逐条抽查（防"报喜不报忧"）：

| 抽查 | 命令 | 期望 |
|-|-|-|
| 缺 python-pptx 不再崩溃 | `--only DP-01` | exit 1 + `status=failed` + `deck=null` + `deck_error` + **result.json 存在** |
| 无方案不再报成功 | `--only IN-05` | exit 1 + `status=failed` + 记录 "no spec loaded" |
| 损坏模板不再丢 deck | `--only TP-02,TP-03,TP-05` | exit 0 + `status=partial` + `template.kind=builtin` + `template.error` |
| 契约形态④ 不再缺字段 | `--only CT-02` | exit 0 + `check_contract --case` exit 0 |
| 事后删字段能被抓 | `--only CT-04` | `check_contract` exit 1 并逐个列出缺失字段 |
| 三格缺口确实拦不住 | `--only CT-05,ST-01,ST-02` | `export_check` exit 0（**未拦住**）⇒ 按 §5 人工兜底 |

## 4. 泛化路径层（3 个题材）

```bash
cp -r "$S" /tmp/skill-set
python /tmp/skill-set/scripts/run_case_set.py --out /tmp/case-out \
    --include-example --emit-md /tmp/case-out/case-set.md; echo "exit=$?"
```

| # | 检查项 | 期望（本机实测） |
|-|-|-|
| 4.1 | 案例数 / 退出码 | **3** / **0** |
| 4.2 | 逐案 `exit` / `status` | 全 **0** / 全 `completed` |
| 4.3 | 页数 | 示例 8；两个新案例各 **11**（9 内容页 + 封面 + 收尾） |
| 4.4 | 证据行 | 示例 6；两个新案例各 **9**（下限 6） |
| 4.5 | 两道门 | 每案 `export 0 / contract 0` |
| 4.6 | 数字逐字命中 | 每案 `must_keep_verbatim` **8/8** |
| 4.7 | 越界表述 | `must_not_claim` **0 命中** |
| 4.8 | `self_check.ok` | 全 true |
| 4.9 | 包内残留 | `__pycache__` 仍为空 |

关键抽查：打开 `/tmp/case-out/case-muon-battery/academic_deck.pptx`，
在图文同页（第 5 页）**搜到 `90.8` 与 `88.6`** —— 这是题集 G1 修好后的回归判据。

## 5. 增益路径层（三臂对照）

```bash
python "$S/scripts/gain_probe.py" --out /tmp/gain --arms baseline,skill,ablation --repeat 2
python -c "import json;print(json.load(open('/tmp/gain/gain-report.json',encoding='utf-8')).keys())"
```

| # | 检查项 | 期望 |
|-|-|-|
| 5.1 | 退出码 | 0（2 = 缺 python-pptx，3 = 输入不可读） |
| 5.2 | 三臂都有记录 | `baseline` / `skill` / `ablation` 各一行；实测 `substantive_claim_coverage` 0.0 / 1.0 / 0.0，`evidence_rows` 0 / 6 / 1，契约字段 7 / 19 / 19，`rework_points` 6 / 0 / 2 |
| 5.3 | 口径 | 报告里写明这是**本机结构性对照**，不是平台白板分数 |
| 5.4 | 不污染包 | 产物只在 `--out`；跑完 `__pycache__` 仍为空 |

## 6. 抗漂移检查（文档 ↔ 实现）

| # | 命令 | 期望 |
|-|-|-|
| 6.1 | 删掉**副本**里的 `references/OUTPUT_CONTRACT.md` 再跑 `main.py` | exit 1，`self_check.problems` 点名契约（契约同源 M1） |
| 6.2 | 把某案例 `output_contract` 改成 list（形态④） | `check_contract --case` 仍 exit 0 |
| 6.3 | 把案例 `slide_count` 调小 2 | `page_budget_met=false` + uncertainty |
| 6.4 | `grep -c 'add_argument' "$S/scripts/"*.py` | 基线 11 个脚本的参数数不变；三个演练件各带自己的参数 |

## 7. 三格已知缺口的人工兜底（必须做）

```bash
python -c "import json;a=json.load(open('result.json',encoding='utf-8'));b=json.load(open('case.json',encoding='utf-8'));print('OK' if a['case_id']==b['case_id'] else 'MISMATCH')"
python -c "import json;r=json.load(open('result.json',encoding='utf-8'));print('OK' if r['status']!='completed' or (not r['uncertainty'] and not (r.get('evidence_mapping') or {}).get('gaps')) else 'INCONSISTENT')"
python -c "import json;r=json.load(open('result.json',encoding='utf-8'));print('OK' if not r['uncertainty'] or r['change_records'] else 'MISSING RECORD')"
```

## 8. 通过标准

- §1 全过（硬门）；§2 三个 0；§3 的 3.3 = 0、3.5 = 19/19、3.7 = 0；
- §4 的 4.1 = 0、4.6 全中、4.7 = 0；§5 退出码 0；§6 的 6.1 通过；§7 在交付前真的做过。
