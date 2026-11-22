# TEST.md — 自测清单与期望输出（失败注入与恢复演练版）

自测分三层：**① 合规**（技能资源硬门）、**② 健康路径**（端到端 + 两道交付门）、
**③ 失败路径**（24 条注入 + 19 条恢复演练）。第 ③ 层是本版的主轴，
它才是"这个包在出事时还值不值得信任"的证据。

> 所有命令都请在**包外副本**上跑（包内跑会生成 `__pycache__`，
> 而技能资源只允许文本文件）：
> ```bash
> cp -r "$SKILL_DIR" /tmp/skill-test && cd /tmp && S=/tmp/skill-test
> ```

---

## 0. 环境

```bash
python -V                       # 期望 ≥3.8（本机实测 3.13.9）
python -c "import pptx, PIL; print(pptx.__version__, PIL.__version__)"
python -c "import matplotlib; print(matplotlib.__version__)"     # 可选
python -c "import fitz" 2>/dev/null || python -c "import pypdf; print('pypdf ok')"
```

---

## 1. 合规层（技能资源硬门）

| # | 命令 | 期望 |
|-|-|-|
| 1.1 | `find "$S" -type f \| wc -l` | ≤ 50 |
| 1.2 | `du -sb "$S"` | ≤ 2 MiB |
| 1.3 | `find "$S" -type f -size +500k` | 空 |
| 1.4 | `find "$S" -name '__pycache__' -o -name '*.pyc'` | 空 |
| 1.5 | `grep -rnE "([A-Za-z]:[\/])|/Users/|[A-Za-z]:\\\\" "$S"` | 空（字体探测候选路径除外，需点名） |
| 1.6 | `python -m py_compile $(find "$S" -name '*.py')` | 无输出 |

## 2. 健康路径层（端到端 + 两道门）

```bash
OUT=/tmp/out-healthy
python "$S/scripts/main.py" --case "$S/examples/case.json" \
    --task "$S/examples/task.md" --spec "$S/examples/deck-spec.json" --out "$OUT"; echo "exit=$?"
python "$S/scripts/export_check.py" --result "$OUT/result.json" --out-dir "$OUT" \
    --case "$S/examples/case.json"; echo "exit=$?"
python "$S/scripts/check_contract.py" --result "$OUT/result.json" \
    --contract "$S/references/OUTPUT_CONTRACT.md" --case "$S/examples/case.json"; echo "exit=$?"
```

| # | 检查项 | 期望（本机实测） |
|-|-|-|
| 2.1 | `main.py` 退出码 | **0** |
| 2.2 | `status` | `completed` |
| 2.3 | `result.json` 顶层字段数 | **19**（`OUTPUT_CONTRACT.md` §1 全覆盖） |
| 2.4 | `deck.file` / `deck.slide_count` | `academic_deck.pptx` / **8** |
| 2.5 | `previews` | **7** 个 `preview-approx-*.png`，`kind=pil-approximation` |
| 2.6 | `evidence_mapping.entries` / `gaps` | **6** / `[]`（与 md 表行数一致，G7） |
| 2.7 | `spec_lint.valid` / `uncertainty` 条数 | `true` / **0** |
| 2.8 | `export_check` / `check_contract` 退出码 | **0** / **0** |
| 2.9 | `run_meta.rendered_with` | `pil-approximation (no PowerPoint/LibreOffice attached)` |
| 2.10 | 自定位：把 cwd 换到别处再跑 2.1 | 仍 **exit 0**（脚本用 `__file__` 自解析） |

## 3. 失败路径层（本版主轴）

```bash
cp -r "$S" /tmp/skill-drill
python /tmp/skill-drill/scripts/fault_inject.py \
    --out /tmp/drill --emit-matrix /tmp/drill/matrix.md; echo "exit=$?"
```

| # | 检查项 | 期望（本机实测，2026-11-22） |
|-|-|-|
| 3.1 | 健康基线（注入前） | `exit 0` / `status=completed` / 8 页 / 19 字段 / 7 预览 / 0 uncertainty |
| 3.2 | 注入条数 | **24**（输入 8 · 模板 5 · 依赖 4 · 契约 5 · 状态 2） |
| 3.3 | **静默失败**条数 | **0**（exit 0 + completed + 零留痕的条数） |
| 3.4 | 与文档口径不一致条数 | **0** |
| 3.5 | 恢复演练 | 19 条有恢复动作的**全部**回到 `exit 0 + completed` |
| 3.6 | 已知检测缺口 | **3** 条（CT-05 / ST-01 / ST-02，如实申报，见 `failure-modes.md` §5） |
| 3.7 | `fault_inject.py` 自身退出码 | **0** |
| 3.8 | 包内残留 | 跑完注入后 `find "$S" -name '__pycache__'` 仍为空 |
| 3.9 | cwd 复核 | 所有子进程 cwd = 沙箱（不是技能根）⇒ 顺带复核"任意 cwd 可跑" |

**逐条抽查**（不看全表也能确认脚本没在"报喜不报忧"）：

| 抽查 | 命令 | 期望 |
|-|-|-|
| 缺 python-pptx 不再崩溃 | `python .../fault_inject.py --out /tmp/d1 --only DP-01` | `exit 1` + `status=failed` + `deck=null` + `deck_error` 有值 + **result.json 存在** |
| 无方案不再报成功 | `--only IN-05` | `exit 1` + `status=failed` + `spec_lint` 记录 "no spec loaded" |
| 损坏模板不再丢 deck | `--only TP-02,TP-03,TP-05` | `exit 0` + `status=partial` + `deck.template.kind=builtin` + `template.error` 有值 |
| 契约形态④ 不再缺字段 | `--only CT-02` | `exit 0` + `check_contract --case` `exit 0` |
| 事后删字段能被抓 | `--only CT-04` | `check_contract` `exit 1` 且**逐个列出** `run_meta`、`evidence_map_json` |
| 三格已知缺口确实拦不住 | `--only CT-05,ST-01,ST-02` | `export_check` `exit 0`（**未拦住**）⇒ 必须按 §5 人工兜底 |

## 4. 抗漂移检查（文档 ↔ 实现）

| # | 命令 | 期望 |
|-|-|-|
| 4.1 | 删掉**副本**里的 `references/OUTPUT_CONTRACT.md` 再跑 `main.py` | `exit 1`，`self_check.problems` 点名契约（契约同源门） |
| 4.2 | 把 `result.json` 的 `case_id` 改成别的值再跑 `export_check --case` | **历史缺口**：不报错（G1 只查非空）——按 §5 人工兜底 |
| 4.3 | `grep -c 'add_argument' "$S/scripts/"*.py` | 与基线一致（CLI 未增删参数） |
| 4.4 | 把 `main.py`/`deckgen.py` 回退到基线再跑 §3 | DP-01/DP-02/IN-05/IN-06/TP-02/TP-03/TP-05/CT-02 共 8 条翻红 |

## 5. 三格已知检测缺口 + 人工兜底（必须做，不要跳）

脚本门（G1–G8 + §1 字段覆盖）是**静态产物校验器**，它看不到历史状态、也不外联对照，
因此下面三件事**必须由交付者手工确认**：

| 缺口 | 为什么会漏 | 人工兜底动作 |
|-|-|-|
| `case_id` 与案例不一致 | G1 只断言 result 自己的 `case_id` 非空 | 交付前**肉眼对拍** `result.case_id` 与 `case.json.case_id`（一行 `python -c` 即可） |
| 伪造 `status`（把 partial 改成 completed） | 校验器看不到"上一次运行的真实状态" | 交付前复核：`status=completed` ⇒ `uncertainty=[]` 且 `evidence_mapping.gaps=[]` |
| 抹掉 `uncertainty`（降级不留痕） | 清空后产物自身仍然自洽 | 交付前复核：有任何 `evidence_gap` / 占位框 / 回退 ⇒ `uncertainty` 必须非空 |

## 6. 通过标准

- §1 全过（**硬门**，不过则技能不被接受）；
- §2 退出码 0/0/0 且表中各项与实测一致；
- §3 的 3.3 = 0、3.5 = 19/19、3.7 = 0；
- §4 的 4.1 通过；
- §5 的人工兜底在交付前**真的做过**（不是"知道有这回事"）。
