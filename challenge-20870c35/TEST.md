# TEST.md — 本地实测记录（challenge-20870c35）

- 测试时间：2026-11-20 22:31 +08（Asia/Shanghai）
- 测试机：Windows（Git Bash / MSYS2），Python 3.13.9（Anaconda）
- 代码状态：本目录全部文件，`scripts/` 7 个 Python 脚本最后一次 `py_compile` 通过后未再改动

## 1. 环境确认

```
$ python --version
Python 3.13.9
$ python -c "import pptx,PIL; print('python-pptx',pptx.__version__,'| Pillow',PIL.__version__)"
python-pptx 1.0.2 | Pillow 12.3.0
$ python -c "import pypdf; print('pypdf',pypdf.__version__)"
pypdf 6.14.2
```

## 2. 语法检查

```
$ python -m py_compile scripts/*.py
=> 无输出，退出码 0（COMPILE_OK）
```

## 3. 主流程实测（验收 smoke）

命令（等价于父任务验收命令，`<script> --case examples/case.json --out <out>`）：

```
$ python scripts/main.py --case examples/case.json --out "D:/BuildTemp/smoke-20870c35"
[plan] 12 pages, narrative=group_meeting, audience=familiar
[deck] 12 slides, mode=built-in-theme
[preview] wrote 13 preview files (PIL simulation)
[done] status=completed deck_ok=True preview_ok=True validate_valid=True contract_valid=True
[done] output: D:\BuildTemp\smoke-20870c35
退出码 0
```

实际产出（D:/BuildTemp/smoke-20870c35，均为真实文件）：

| 文件 | 大小 | 说明 |
|-|-|-|
| result.json | 29,547 B | status=completed；output_contract 16 字段全在顶层；sources 含 md×2 + pdf×1(parsed)+png×1(附件) |
| talk_plan.json | 24,134 B | 12 页计划（叙事/每页主张/证据/讲稿/问答） |
| evidence_map.json | 458 B | 源文件 → 页 + 图表引用 反向映射 |
| editable_deck.pptx | 74,599 B | python-pptx 可编辑；12 页，每页含讲稿备注 |
| previews/cover_preview.png | 97,357 B | 1280×720 封面预览（PIL 模拟，带水印） |
| previews/slide_002..011.png | 各 ~50–65 KB | 10 张逐页缩略图（PIL 模拟，带水印） |
| previews/preview_grid.png | 101,149 B | 整包网格 |
| previews/preview_manifest.json | 680 B | 预览清单 + 限制说明 |
| self_check.json | 约 2 KB | validate + contract 双自检 |

自检（内嵌于 self_check.json，亦可用独立 CLI 复核）：

```
$ python scripts/validate_result.py D:/BuildTemp/smoke-20870c35/result.json
=> valid: true, checks=8 errors=0 warnings=0
$ python scripts/check_contract.py D:/BuildTemp/smoke-20870c35/result.json
=> valid: true, declared=16 missing_required=0 wrong_type=0
```

内容抽查（talk_plan.json 页级主张均为源材料逐字引文，证据定位 L行号 · §章节）：

- 第 2 页 motivation（strong）「本文研究问题：…」← L19 · §1 引言
- 第 7–10 页 results（strong）：「Table 1 显示…」「两个基线…」「Fig. 2…」「Acc@1 曲线…」← §3 结果（L32–L35）
- 第 9 页绑定插图：fig=Fig. 2 → img=examples/materials/fig2.png（真实嵌入）
- 第 6/7 页 Fig. 3 / Table 1 无图片文件 → 页内诚实占位框
- 第 12 页问答备用页；question_bank=6 条预判追问

## 4. 二次运行（可复现性）

```
$ python scripts/main.py --case examples/case.json --out "D:/BuildTemp/smoke-20870c35b" --quiet
status=completed pages=12 deck=True validate_valid=True contract_valid=True
```

两次 `talk_plan.json` 在去掉 `generated_at` 时间戳后 `==` 相等 → **确定性**：✓

## 5. 模板适配模式

用 python-pptx 生成一个外部模板后传入：

```
$ python scripts/main.py --case examples/case.json --out "D:/BuildTemp/smoke-tpl" --template "D:/BuildTemp/tpl.pptx" --quiet
status=completed ... validate_valid=True contract_valid=True
result.json → artifacts.template_used = D:\BuildTemp\tpl.pptx
           → artifacts.deck_mode.mode = template-adapt（沿用模板母版/版式新增页面）
```

## 6. --skip-previews 模式

```
$ python scripts/main.py --case examples/case.json --out "D:/BuildTemp/smoke-nopre" --skip-previews --quiet
status=completed ... 退出码 0
previews/ 只含 cover_preview.png + preview_grid.png + preview_manifest.json
```

## 7. 打包示例输出（examples/sample-output，标注"示例，非正式案例"）

```
$ python scripts/main.py --case examples/case.json --out examples/sample-output --skip-previews --quiet
status=completed ... 退出码 0
产生：result.json、talk_plan.json、evidence_map.json、editable_deck.pptx(74,599 B)、
      previews/{cover_preview.png, preview_grid.png, preview_manifest.json}、self_check.json
```

`examples/case.json` 含 `"sample": true`、标题含「示例（非正式案例）」；
`examples/task.md` 首行声明「仅演示接口，不是平台正式测试案例」。

## 8. 产出文件 SHA-256（D:/BuildTemp/smoke-20870c35）

```
result.json          c568425feb1496e24ffa667dbe4f8791b85f0d2a11964d5f22abf50c2bed7c97
talk_plan.json       f13f1e0d00ee2e0a6ab43853b43e395997d41f0cdd3ae515def6d6b74f75c19b
evidence_map.json    9db62f69c50149f17f15e2195571c85e2a2cfb7ec44619866f0d2ecdf26463cc
editable_deck.pptx   f2dfa9f8d2b0d18b71f19231603773ea1e638c123719520bc76670df886979f4
previews/cover_preview.png    07b2d0f3f60caa5c403b293cc9f3046765bc9105a812248e7decf6d300398ac4
previews/preview_grid.png     9479ff9685622148c8f2f2ac19d856054d4e235be897fe5fb4e11914531d6f5a
```

## 9. 资源约束

- 文本文件数：按 find 统计 = 见最终清单（≤50）✓
- 单文件 ≤500KB、总计 ≤2MB、无符号链接 ✓
- SKILL.md frontmatter `name/description` 由 yaml 解析通过 ✓

成功。全部命令真实执行、产物为真实文件；预览为 Pillow 模拟渲染（如实标注）。