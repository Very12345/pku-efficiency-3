# 页级证据映射（复核用）

> 由 deck-spec.json 生成；引用项对应论文的图/表/章节/页码。
> “证据缺失”是显式标注，不是作者无中生有。

| 页 | 标题 | 主张（一句话） | 证据定位 | 状态 |
|---|---|---|---|---|
| P01 | 研究问题：评语通用、缺上下文 | 代码评审自动化受限于评审模型缺少项目上下文。 | §1 Introduction (p.1) | mapped |
| P02 | 方法：索引→检索→条件生成 | ExampleNet 用三阶段流水线实现免微调的检索增强评审。 | §2 Method (p.2) | mapped |
| P03 | 结果：主表（Table 1） | k=5 时 ROUGE-L F1 提到 0.695，超过基线 8.3 点。 | Table 1 (p.3) | mapped |
| P04 | 结果：检索量 vs 质量（重建图） | 重建图：ROUGE-L F1 随 k 先升后降，k=5 为甜点。 | Table 1 (p.3); Fig. 1 (p.3) | mapped |
| P05 | 结论 | 所有配置均优于基线；k=5 是信息量与噪声的平衡点。 | §4 Conclusion (p.4) | mapped |
| P06 | 局限与展望 | 局限明确：合成基准、索引内存、服务成本、非英语未测。 | §4 Limitations (p.4) | mapped |

附件：源文件 academic_deck.pptx；导出预览见 previews/（PIL 近似渲染）。