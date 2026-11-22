# TEST.md — 自测清单与期望输出（多案例泛化题集版）

自测分三层：**① 合规**（技能资源硬门）、**② 健康路径**（端到端 + 两道交付门）、
**③ 题集**（三个不同题材的案例逐条对验收区间）。第 ③ 层是本版主轴——它回答
"换题材还成立吗"，而且答案是一个**退出码**，不是一段形容词。

> 所有命令都请在**包外副本**上跑（包内跑会生成 `__pycache__`，而技能资源只允许文本文件）：
> ```bash
> cp -r "$SKILL_DIR" /tmp/skill-test && S=/tmp/skill-test
> ```

---

## 0. 环境

```bash
python -V                                             # ≥3.8（本机 3.13.9）
python -c "import pptx, PIL; print(pptx.__version__, PIL.__version__)"
python -c "import matplotlib; print(matplotlib.__version__)"   # 可选
```

---

## 1. 合规层（技能资源硬门）

| # | 命令 | 期望 |
|-|-|-|
| 1.1 | `find "$S" -type f \| wc -l` | ≤ 50（本版实测 40） |
| 1.2 | `du -sb "$S"` | ≤ 2 MiB（本版实测 ~294 KB） |
| 1.3 | `find "$S" -type f -size +500k` | 空 |
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
| 2.1 | `main.py` 退出码 | **0** |
| 2.2 | `status` | `completed` |
| 2.3 | `result.json` 顶层字段数 | **19** |
| 2.4 | `deck.file` / `deck.slide_count` | `academic_deck.pptx` / **8** |
| 2.5 | `previews` | **7** 个 `preview-approx-*.png` |
| 2.6 | `evidence_mapping.entries` / `gaps` | **6** / `[]` |
| 2.7 | `export_check` / `check_contract` | **0** / **0** |
| 2.8 | 自定位（换 cwd 再跑） | 仍 **exit 0** |

## 3. 题集层（本版主轴）

```bash
cp -r "$S" /tmp/skill-set
python /tmp/skill-set/scripts/run_case_set.py \
    --out /tmp/case-out --include-example --emit-md /tmp/case-out/case-set.md; echo "exit=$?"
```

| # | 检查项 | 期望（本机实测，2026-11-22） |
|-|-|-|
| 3.1 | 案例数 | **3**（示例 + μ 子 + 睡眠队列） |
| 3.2 | `run_case_set.py` 退出码 | **0**（三个案例全部在验收区间内） |
| 3.3 | 逐案 `run_exit` | 全部 **0** |
| 3.4 | 逐案 `status` | 全部 `completed` |
| 3.5 | 页数 | 示例 8；两个新案例各 **11**（9 内容页 + 封面 + 收尾） |
| 3.6 | 证据映射行数 | 示例 6；两个新案例各 **9**（≥6 下限） |
| 3.7 | 证据缺口 `gaps` | 全部 0 |
| 3.8 | `uncertainty` | 示例 1（模板缺席，预期）；两个新案例 0 |
| 3.9 | 两道门 | 每案 `export 0 / contract 0` |
| 3.10 | 数字逐字命中 | 每个案例的 `must_keep_verbatim` **8/8** 全中 |
| 3.11 | 越界表述 | `must_not_claim` **0 命中** |
| 3.12 | `self_check.ok` | 全部 true |
| 3.13 | 包内残留 | `find "$S" -name '__pycache__'` 仍为空 |

**关键抽查（这两条最容易"看起来通过、其实没通过"）**

| 抽查 | 命令 | 期望 |
|-|-|-|
| 数字真的落在**页面上**（不是只在 JSON 里） | 打开 `/tmp/case-out/case-muon-battery/academic_deck.pptx`，搜 `90.8` 与 `88.6` | 命中（题集 G1 修好后） |
| 图文同页不丢字 | 同上，第 5 页（`layout_hint=figure`）正文含四档透射率 | 命中 4 个数字 |
| 越界措辞真的不在 | `grep -c "导致" /tmp/case-out/case-sleep-cohort/evidence_mapping.md` | 0（材料本身也规避了因果动词） |

## 4. 抗漂移检查（文档 ↔ 实现）

| # | 命令 | 期望 |
|-|-|-|
| 4.1 | 删掉**副本**里的 `references/OUTPUT_CONTRACT.md` 再跑 `main.py` | `exit 1`，`self_check.problems` 点名契约 |
| 4.2 | 把某案例 `output_contract` 改成 list（形态④）再跑该案 | `check_contract --case` 仍 exit 0 |
| 4.3 | 把案例 `slide_count` 改小 2 再跑 | `deck.page_budget_met=false` + uncertainty（口径：预算是内容页数） |
| 4.4 | `grep -c 'add_argument' "$S/scripts/"*.py` | 与基线一致 + `run_case_set.py` 自己的 7 个参数 |

## 5. 题集**已经抓到**的两个问题（回归用）

| # | 症状 | 现在应看到 |
|-|-|-|
| G1 | 图文同页时页级 bullets 被插图覆盖 ⇒ 该页文字从幻灯片 XML 里消失 | 已修：`deckgen._fill_body_placeholder` 跳过图片占位符，图文同页时正文走左半幅；`90.8`/`88.6` 可在 deck 里搜到 |
| G2 | 案例 `slide_count=9` 却产出 11 页 ⇒ `page_budget_met=false` | 已对齐：两个新案例的 `slide_count=11`（含封面与收尾），口径写进 `CASE-SET.md` §3 |

## 6. 通过标准

- §1 全过（硬门）；
- §2 退出码 0/0/0 且表中各项一致；
- §3 的 3.2 = 0、3.10 全中、3.11 = 0、3.13 为空；
- §4 的 4.1 通过；
- 若对外声称"换题材也成立"，必须能给出 §3 的命令与退出码。
