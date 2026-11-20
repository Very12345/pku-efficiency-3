# examples/ — 最小示例（示例，非正式案例）

本目录是 **v2 流水线的最小调用示例**，用于说明接口与完整使用流程：

| 文件 | 说明 |
|-|-|
| `case.json` | 最小案例输入（虚构材料：蛋白质二级结构预测），声明 `output_contract` 待回显字段 |
| `task.md` | 任务说明（受众/时长/页数/交付要求） |
| `material.md` | 虚构研究材料（摘要/引言/方法/结果/讨论局限/结论） |
| `results.csv` | 虚构数据表（Q3/Q8/SOV/参数/时延），供图表重绘与数字核验 |
| `edit_demo.json` | 演示局部编辑操作（update_bullet / add_note / reorder_pages） |
| `output/` | 本机真实跑出的示意产物（文件名带 `.example.` 标注，见 output/README-EXAMPLE.md） |

> ⚠ **本目录全部材料为虚构示例**，仅用于演示 Skill 接口；**它们不是、也不
> 代表平台正式 3 个固定案例的输出**。正式案例由平台提供，Skill 在运行时依据
> 实际输入重新生成全部产物，不含任何预制答案。

## 复跑命令（Skill 根目录执行）

```bash
# 完整流水线（产物写 <输出目录>）
python scripts/main.py --case examples/case.json --out <输出目录>

# CP4 契约校验（G1–G8）
python scripts/result_tool.py --result <输出目录>/result.json \
    --out-dir <输出目录> --case examples/case.json \
    --envelope templates/result_envelope.json

# 产物自检
python scripts/selftest.py --out <输出目录> --case examples/case.json

# 局部编辑 + 版本归档（演示稿迭代）
python scripts/main.py --case examples/case.json \
    --out <输出目录>-edit --edit examples/edit_demo.json --version v2
```

本机实测记录（含退出码与产物清单）见 `../TEST.md`。