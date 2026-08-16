# 天机演象设计文档索引

本目录保存正式开发前需要评审的设计文档。项目总范围以 [详细项目计划](../detailed-project-plan.md) 为准，本目录负责说明产品和系统如何实现该范围。

## 文档清单

| 文档 | 主要读者 | 解决的问题 | 状态 |
| --- | --- | --- | --- |
| [产品与交互设计](./product-design.md) | 产品、设计、专家、测试 | 用户如何完成建档、排盘、查看依据和报告 | 评审稿 |
| [系统架构设计](./system-architecture.md) | 架构、研发、运维、测试 | 服务如何拆分、调用、部署和监控 | 评审稿 |
| [规则与数据设计](./rule-and-data-design.md) | 专家、数据、研发、测试 | 规则、来源、案例和计算记录如何治理 | 评审稿 |
| [评审与决策记录](./review-checklist.md) | 项目负责人及各负责人 | 哪些问题已决定，是否允许进入开发 | 待评审 |

已采用的局部技术决策：

- [ADR-001：内部语料基础设施](./decisions/001-corpus-foundation.md)
- [ADR-002：MVP计算与规则工程基线](./decisions/002-mvp-engineering-baseline.md)
- [ADR-003：前后端仓库布局](./decisions/003-frontend-backend-repository-layout.md)
- [ADR-004：四体系自动排盘与数字排盘工程基线](./decisions/004-four-system-casting-baseline.md)
- [ADR-005：类象与元会运世工程基线](./decisions/005-imagery-and-yuanhui-baseline.md)
- [ADR-006：个体化自动起卦协议](./decisions/006-personalized-auto-casting.md)
- [ADR-007：术数领域边界与公共卦象核心](./decisions/007-domain-boundaries-and-hexagram-core.md)

## 文档优先级

发生冲突时，按以下顺序处理：

1. 已签署的决策记录和范围变更记录。
2. 详细项目计划。
3. 本目录中的专项设计。
4. 项目摘要和早期技术验证文档。

任何设计变化如果影响MVP范围、术数规则、隐私策略、验收标准或里程碑，必须先更新详细项目计划，再更新专项设计。

## 状态定义

- 草稿：内容不完整，不能作为开发依据。
- 评审稿：内容已完整，可组织产品、技术和专家评审。
- 已批准：负责人已签署，可作为开发和验收依据。
- 已废止：被新版本替代，仅用于历史追溯。

当前所有设计文档均未批准，不代表正式开发授权。
