# pku-efficiency-3 — 学术效率第三期 Skill 包公开仓库

玻尔产品周赛 · 北大专区 · 学术效率第三期（efficiency-3）的 9 个已制作 Skill 包聚合。

每个子目录是一个完整的 Skill 包，包含：
- `SKILL.md` — Skill 本体（YAML frontmatter + 执行步骤 + 异常处理 + 自查清单）
- `README.md` — 包说明
- `TEST.md` — 本地实测记录
- `scripts/` — 自定位可运行脚本（不依赖 cwd）
- `examples/` — 示例输入/输出
- `references/` — 规范与参考材料
- （部分包含 `templates/`、`styles/`）

## 包目录

| 目录 | Skill 名 | 说明 |
|-|-|-|
| [graphical-abstract-7030fff2](graphical-abstract-7030fff2/) | `graphical-abstract` | 论文图形摘要（Graphical Abstract）生成 |
| [challenge-98e5a474](challenge-98e5a474/) | `scientific-schematic-editor` | 科研示意图生成与编辑（可编辑 SVG + 多格式导出 + 结构化 result.json） |
| [challenge-1bd90d8a](challenge-1bd90d8a/) | `scientific-figure-craft` | 科学图形制作 |
| [challenge-83d4f050](challenge-83d4f050/) | `biological-mechanism-pathway-diagram` | 生物机制/通路示意图 |
| [challenge-9034312d](challenge-9034312d/) | `apparatus-and-route-diagrams` | 装置与路线示意图 |
| [ppt-c7b80f0d](ppt-c7b80f0d/) | `paper-to-academic-ppt` | 论文/研究材料转学术汇报 PPT（可编辑 + 证据可追溯） |
| [challenge-20870c35](challenge-20870c35/) | `academic-talk-organizer` | 学术汇报组织 |
| [ppt-710fbc72](ppt-710fbc72/) | `academic-slide-adapt` | 学术幻灯片模板适配 |
| [ppt-6ad93034](ppt-6ad93034/) | `academic-ppt-builder` | 论文/文献材料生成可编辑学术演示稿（PPTX） |

## 使用方式

以 skill 目录方式加载某个包，例如：

```bash
# 以 challenge-98e5a474 为例
cp -r challenge-98e5a474 /path/to/skills/scientific-schematic-editor
```

每个包内的 `SKILL.md` 描述完整执行流程；`scripts/` 内脚本自定位运行，不依赖调用时的 cwd。

## 许可与说明

- 本仓库为参赛作品的公开存档，仅供学习交流。
- 各包内 `README.md` 含与其主办方题目的对应关系与本地实测记录。