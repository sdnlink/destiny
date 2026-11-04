# 天机演象 · 交互式推演工程师重构方案

> 本文档对照「古法术数推演工程师」角色规范，对现有项目做差距分析，并给出可落地的重构架构与实施计划。

---

## 1. 角色规范核心要求提炼

角色规范定义了一个**有状态、多轮交互、强制流程、盘面不可变**的术数推演工程师，核心约束：

| 维度 | 要求 |
| --- | --- |
| **盘面铁律** | 原始排盘、卦盘、干支、用神、动爻一经生成永久固定，绝不因用户反馈/主观修改/现实不符而改动；仅可调整事理翻译与解读视角 |
| **强制7步流程** | 信息校验→完整排盘→定用神→旺衰计算→象义拆解→综合吉凶→行动建议，禁止跳过 |
| **术数调度** | 未指定门派默认主用梅花易数+六爻辅助；指定六爻/奇门/大六壬则完整装卦 |
| **交互模块A-G** | 起盘前信息补全、排盘后现实校验、拓展参考资料库、后续交互入口、多方人物取象、多抉择分支推演、事后复盘 |
| **固定输出格式** | 求测事由→起盘方式→完整排盘→用神定位→旺衰分析→象义解读→综合推演→趋吉避凶→文化提示→拓展资料库→现状核对→后续入口 |
| **多轮规则** | 同一件事追问沿用原盘深化；全新问题完整重起；指定换门派完整重起；用户不参与核对直接响应其他指令 |

---

## 2. 现有项目能力盘点

| 能力域 | 现有实现 | 成熟度 |
| --- | --- | --- |
| 历法计算 | `calendar/engine.py`，真太阳时、干支四柱、节气边界、十二时辰轮盘 | 高 |
| 周易/梅花/六爻/大六壬排盘 | 各领域 `engine.py`，支持自动/时间/数字/手工/铜钱起卦 | 中高 |
| 八字/紫微/奇门排盘 | 各领域 `engine.py`，时间/自动起盘 | 中 |
| 风水方位 | `fengshui/engine.py`，二十四山、磁偏角、多次测量共识 | 中 |
| 综合研判 | `core/synthesis.py`，多模块共振指数、共识矩阵、极性判断 | 中 |
| 象义映射 | `core/interpretation.py`，六親/六神/体用关系→现实事件 | 中 |
| 事项建议 | `core/advisory.py`，按类别输出建议与核实清单 | 中 |
| 文献引证 | `core/literature.py`，匹配卦象书籍原文 | 中 |
| 类象/元会运世 | `core/imagery.py`、`core/yuanhui.py` | 中 |
| 定向推演 | `core/inquiry_parser.py`、`core/targeted_deduction.py` | 中 |
| 规则注册表 | `core/registry.py`，84条草稿规则，结构校验 | 中 |
| 验证案例 | `core/validation.py`，31个回归案例 | 低 |
| 语料检索 | `corpus_api.py` + ClickHouse，1,524书目/3,300万字符 | 高 |
| Web界面 | React+Vite，输入面板+结果工作台+规则目录+概念速查+历史 | 中 |

---

## 3. 差距分析

### 3.1 核心差距（必须重构）

| # | 差距 | 影响 | 重构方向 |
| --- | --- | --- | --- |
| G1 | **无会话状态管理**：当前API无状态，每次请求独立，无法保留盘面、交互历史、用户反馈 | 无法实现多轮交互、盘面不可变铁律、事后复盘 | 新增 `app/session/` 不可变推演会话模型 |
| G2 | **无强制7步工作流**：当前直接返回计算结果，不区分步骤、不保证流程完整 | 违反"禁止跳过逻辑直接输出结论" | 新增 `app/workflow/` 7步编排引擎 |
| G3 | **无交互模块A-G**：无信息补全、现实校验、拓展资料库、后续入口、多方取象、分支推演、事后复盘 | 无法实现角色规范的完整交互闭环 | 新增 `app/interaction/` 模块集 |
| G4 | **盘面不可变未在模型层强制执行**：当前无快照哈希、无版本锁定、可重复计算覆盖 | 违反"原始盘面永久固定"铁律 | 会话模型中快照哈希+写入即冻结 |
| G5 | **无固定输出格式**：当前输出为结构化JSON，不遵循角色规范的固定文案格式 | 前端无法直接渲染规范格式 | 工作流引擎输出统一格式渲染器 |
| G6 | **无术数调度逻辑**：当前用户任选模块，无"默认梅花+六爻辅助"的调度策略 | 不符合门派调度规则 | 工作流引擎内置调度策略 |

### 3.2 次要差距（可扩展）

| # | 差距 | 重构方向 |
| --- | --- | --- |
| G7 | 多方人物取象未独立成模块 | `interaction/multi_party.py` |
| G8 | 多抉择分支推演未独立成模块 | `interaction/multi_choice.py` |
| G9 | 事后复盘无机制 | `interaction/review.py` + 会话结局记录 |
| G10 | 前端无工作流交互界面 | 新增 WorkflowSession 组件 |
| G11 | 无现实校验后的解读视角切换机制 | `interaction/reality_check.py` |

---

## 4. 重构架构设计

### 4.1 总体分层

```text
┌─────────────────────────────────────────────────────────────┐
│                    前端表现层（React + Vite）                 │
│  WorkflowSession 工作流会话组件（信息补全→排盘→核对→后续）    │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / RESTful JSON
┌──────────────────────────────▼──────────────────────────────┐
│              API 层（main.py 新增会话端点）                    │
│  POST /v1/sessions          创建推演会话                       │
│  POST /v1/sessions/{id}/cast 执行排盘（冻结盘面）             │
│  POST /v1/sessions/{id}/interact  交互（核对/追问/分支/复盘） │
│  GET  /v1/sessions/{id}     获取会话完整状态                   │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│              工作流引擎层（app/workflow/）                    │
│  7步编排引擎 · 步骤执行器 · 固定格式渲染器 · 术数调度策略      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│              交互模块层（app/interaction/）                   │
│  A信息补全 · B现实校验 · C拓展资料库 · D后续入口               │
│  E多方取象 · F分支推演 · G事后复盘                             │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│              会话模型层（app/session/）                       │
│  不可变推演快照（hash锁定）· 交互记录 · 会话状态机              │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│         现有领域引擎 + 编排层（复用，不改动）                   │
│  9大领域引擎 · synthesis · interpretation · advisory · 语料   │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 不可变会话模型

```python
DivinationSession {
    session_id: str              # 唯一标识
    question: str                # 求测事由
    category: str                # 事项类别
    system: str                  # 术数门类（meihua/liuyao/qimen/daliuren/auto）
    casting_method: str          # 起盘方式（auto/time/numbers/manual/coins）
    casting_source: dict         # 起盘素材（时间/数字/方位等）
    status: str                  # draft → casting → casted → interacting → reviewed
    snapshot: DivinationSnapshot # 不可变排盘快照（cast后冻结）
    interactions: [InteractionRecord]  # 交互记录列表（追加写）
    created_at / updated_at
}

DivinationSnapshot {
    snapshot_id: str             # hash(snapshot_content)
    frozen: bool = True          # 写入即冻结
    raw_plate: dict              # 原始盘面数据（卦盘/干支/用神/动爻）
    module_results: [dict]       # 各模块计算结果
    input_hash: str              # 输入哈希
    rule_version: str            # 规则版本
    created_at
}

InteractionRecord {
    interaction_id: str
    type: str                    # info_completion / reality_check / followup / multi_party / multi_choice / review
    user_input: dict             # 用户输入
    system_response: dict        # 系统响应（可含解读视角调整，但不改snapshot）
    created_at
}
```

**不可变保证**：
- `snapshot` 字段在 `casted` 状态后写入即冻结，任何后续交互不得修改 `snapshot.raw_plate`。
- 交互记录只追加，不修改历史记录。
- 解读视角调整记录在 `interaction.system_response.interpretation_shift` 中，与原始盘面分离。

### 4.3 7步工作流引擎

```python
WorkflowEngine.run(session) -> WorkflowResult:
    step1_info_validation(session)      # 信息校验&起盘数据源确认
    step2_complete_casting(session)     # 完整排盘（调用领域引擎，冻结快照）
    step3_identify_yongshen(session)    # 定用神
    step4_wangshuai_analysis(session)   # 旺衰状态计算
    step5_xiangyi_deduction(session)    # 象义拆解推理
    step6_synthesis_judgement(session)  # 综合吉凶定性&事态推演
    step7_advice_and_disclaimer(session) # 行动建议与免责提示
    return format_output(workflow_result)  # 固定格式渲染
```

每一步的输出都记录在会话中，步骤间数据单向流动，后续步骤只能读取前面步骤的输出，不能回写修改。

### 4.4 术数调度策略

```python
def select_systems(user_specified, question):
    if user_specified == "liuyao":
        return ["liuyao"]  # 完整纳甲装卦
    if user_specified == "qimen":
        return ["qimen"]   # 时家奇门
    if user_specified == "daliuren":
        return ["daliuren"] # 月将日辰四课三传
    # 默认：主用梅花易数 + 六爻辅助参断
    return ["meihua", "liuyao"]
```

### 4.5 交互模块设计

每个交互模块接收当前会话 + 用户输入，返回系统响应（不修改快照）：

| 模块 | 输入 | 输出 | 核心逻辑 |
| --- | --- | --- | --- |
| A 信息补全 | 初始求测 | 最多3个补全问题 | 检测缺失字段（起盘方式/性别年龄/现状/门派），按需提问 |
| B 现实校验 | 符合/部分符合/不符合 | 解读视角调整建议 | 符合→进入拓展；部分符合→保留原盘调整象义映射；不符合→询问是否重起或换取象角度 |
| C 拓展资料库 | 会话快照 | 5项固定输出 | 核心符号象义/风险隐患/时间窗口/多发展可能性/误读误区 |
| D 后续入口 | — | 6项菜单 | 固定输出交互菜单 |
| E 多方取象 | 涉及人物描述 | 各方用神+立场心态 | 识别人物角色，分配六親/用神，分别解析 |
| F 分支推演 | 备选方案列表 | 各方案利弊趋势 | 基于原盘取象分支，原盘不足时建议重起 |
| G 事后复盘 | 现实结局 | 应验/未应验分析 | 对比结局，从用神/旺衰/应期/人为干扰分析 |

---

## 5. 实施计划

### 阶段一：后端核心（本次重构）
1. `app/session/` — 不可变会话模型 + JSON文件存储
2. `app/workflow/` — 7步引擎 + 固定格式渲染 + 术数调度
3. `app/interaction/` — 模块A-G
4. `main.py` — 新增会话API端点
5. 后端测试

### 阶段二：前端重构
1. 新增 WorkflowSession 组件
2. 信息补全交互界面
3. 现实校验交互界面
4. 后续交互菜单
5. 多方取象/分支推演/事后复盘界面

### 阶段三：规则与文档
1. 工作流规则注册表条目
2. 验证案例补充
3. 文档更新

---

## 6. 与现有代码的关系

- **不改动**：9大领域引擎、synthesis、interpretation、advisory、literature、imagery、yuanhui、语料服务、现有API端点
- **新增**：session、workflow、interaction 三个模块，以及会话API端点
- **复用**：工作流引擎的步骤2-6直接调用现有领域引擎和编排层
- **前端**：新增工作流组件，现有输入面板/结果工作台保留为底层组件

这种设计保证了重构的**增量性**和**向后兼容性**——现有功能完全不受影响，新交互能力作为上层叠加。
