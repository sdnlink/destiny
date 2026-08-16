# MVP计算服务

> 状态：工程基线可运行，术数解释规则与标准案例待专家签署
> 服务入口：`http://127.0.0.1:8090`

## 1. 能力边界

当前服务提供确定性的历法、周易、梅花易数、六爻和大六壬事实计算，以及多模块并列计算和结构化判断比较。计算内核不调用语言模型，也不根据未经审核的经典文本生成正式吉凶和应期。用户显式提供事项类别和问题摘要时，服务可生成标记为未审核的研究性决策检查清单和事项相关类象候选；该内容不进入正式`judgements`。包含历法模块时，结果同时输出待审核纪元基线下的元会运世位置和盘面五行关系事实。

设置`SERVE_WEB=1`后，服务会在所有API路由之后挂载`frontend/dist`。生产启动脚本负责设置该变量；计算内核本身不依赖前端代码。

已实现：

- 显式IANA时区、公农历、节气、四柱和可选真太阳时。
- 结构化干支、月建、立春生肖、旬空，以及节气绝对时刻的本地时区和UTC表示。
- 周易手工六爻、兼容双数起卦、版本化三数起卦及本卦、变卦、互卦、错卦、综卦。
- 梅花农历时间起卦、双数起卦、体用和五行关系事实。
- 周易、梅花、六爻和六壬个体自动排盘；各模块使用独立派生域并支持凭证重放。
- 规范输入哈希、幂等任务编号、多模块并行计算。
- 规则登记、来源引用、规则集合校验和工程案例回归。
- 对已发布结构化判断进行一致、互补、冲突和无法判断分类。
- 根据本次计算事实生成可追溯的结果摘要和逐模块详细说明。
- 按本卦和变卦检索内部书籍语料，返回可定位原文和明确的书籍参考意见。
- 从实际盘面提取八卦、地支、六亲等类象，并按事项类别排序展示维度。
- 按公历年生成元、会、运、世位置，并比较会支五行与盘面结构五行。

未实现或未批准：

- 周易事项解释、梅花旺衰、应期和行动建议。
- 任何自动吉凶总分、现实概率或准确率。
- 专家规则发布工作流及签署后的生产规则。
- 用户账号、案例档案、持久化任务、报告和前端结果页。
- 六壬、八宅、玄空飞星及其他专业风水规则。

## 2. 启动与安全

安装依赖后启动：

```bash
./scripts/run_mvp_api.sh
```

默认只监听`127.0.0.1:8090`。修改端口：

```bash
APP_API_PORT=8091 ./scripts/run_mvp_api.sh
```

监听非回环地址时必须设置令牌，否则启动脚本直接退出：

```bash
APP_API_BIND=0.0.0.0 APP_API_TOKEN='replace-me' ./scripts/run_mvp_api.sh
```

启用令牌后，所有请求添加`Authorization: Bearer <token>`。当前令牌方案只用于受控内部环境，不能替代正式账号、租户权限、限流、审计和TLS。

## 3. 接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/health` | 健康状态和模块版本 |
| `GET` | `/v1/constants/trigrams` | 八卦常量 |
| `GET` | `/v1/constants/hexagrams` | 六十四卦常量 |
| `GET` | `/v1/rules` | 规则目录，可按`system`、`status`筛选 |
| `GET` | `/v1/validation-cases` | 工程案例，可按`system`筛选 |
| `POST` | `/v1/validation-cases/run` | 执行全部工程案例回归 |
| `POST` | `/v1/calendar/analyze` | 历法和四柱分析 |
| `POST` | `/v1/zhouyi/manual` | 手工六爻起卦 |
| `POST` | `/v1/zhouyi/auto` | 周易个体三枚铜钱自动起卦 |
| `POST` | `/v1/zhouyi/time` | 周易传统农历时间起卦 |
| `POST` | `/v1/zhouyi/numbers` | 周易双数起卦 |
| `POST` | `/v1/zhouyi/three-numbers` | 周易三数独立取上卦、下卦和动爻 |
| `POST` | `/v1/meihua/auto` | 梅花时间结构加个体数起卦 |
| `POST` | `/v1/meihua/time` | 梅花传统时间起卦 |
| `POST` | `/v1/meihua/numbers` | 梅花双数起卦 |
| `POST` | `/v1/liuyao/auto` | 六爻个体三枚铜钱自动排盘及纳甲 |
| `POST` | `/v1/liuyao/time` | 六爻传统时间排盘及纳甲 |
| `POST` | `/v1/liuyao/numbers` | 六爻双数排盘及纳甲 |
| `POST` | `/v1/liuren/auto` | 大六壬个体报数自动排盘 |
| `POST` | `/v1/liuren/time` | 大六壬传统时间排盘 |
| `POST` | `/v1/liuren/numbers` | 大六壬数字占时排盘 |
| `POST` | `/v1/calculations/evaluate` | 统一单模块计算封装 |
| `POST` | `/v1/calculations/compare` | 最多8个模块并行计算和综合比较 |

OpenAPI文档位于`/docs`，机器契约位于`/openapi.json`。

周易三数示例：

```bash
curl -X POST http://127.0.0.1:8090/v1/zhouyi/three-numbers \
  -H 'Content-Type: application/json' \
  -d '{"numbers":[23,47,5],"mapping_version":"earlier-heaven-number-v1"}'
```

三数法中第一数取上卦、第二数取下卦、第三数独立取动爻。旧`/v1/zhouyi/numbers`是第一数下卦、第二数上卦、两数之和取动爻的兼容规则，二者不可混用。

个体自动接口除历法参数外必须提交16至128位ASCII `cast_nonce`。同一凭证、时间和规则版本可复算；新起卦应生成新的128位随机凭证。服务只在结果中返回`cast_nonce_hash`，不回传原始凭证。有限卦象空间中不同用户可能自然得到相同本卦，系统以完整爻值、动爻、时间、事项上下文和派生过程区分任务，不强制制造不同卦象。

### 3.1 历法示例

```bash
curl -X POST http://127.0.0.1:8090/v1/calendar/analyze \
  -H 'Content-Type: application/json' \
  -d '{"local_datetime":"2026-08-15T16:00:00","timezone":"Asia/Shanghai"}'
```

`local_datetime`不能自带偏移，必须另外提供IANA时区。启用真太阳时时同时提交`longitude`和`use_true_solar_time: true`。

历法响应的`solar_terms`同时保留东八区参考时刻、用户时区时刻和UTC时刻；年柱和月柱按节气绝对时刻切换，日柱和时柱按有效当地时间计算。`zodiac`采用立春边界，农历年份仍按春节切换，两者不得混为同一个字段。

### 3.2 多模块比较示例

```bash
curl -X POST http://127.0.0.1:8090/v1/calculations/compare \
  -H 'Content-Type: application/json' \
  -d '{
    "calculations": [
      {"module":"zhouyi","method":"numbers","input":{"lower_number":8,"upper_number":8}},
      {"module":"meihua","method":"time","input":{"local_datetime":"2026-08-15T16:00:00","timezone":"Asia/Shanghai"}}
    ],
    "context": {
      "category": "career",
      "question_summary": "是否接受新的工作机会"
    }
  }'
```

相同计算集合及相同上下文不受字段顺序和模块顺序影响，返回相同`task_id`和`input_hash`。事项类别或问题摘要变化时任务身份也随之变化。当前任务和问题摘要只在请求期间处理，尚未持久化。

### 3.3 推演结果与详细说明

多模块接口返回`explanation`：

```json
{
  "generation_method": "deterministic_fact_template",
  "review_status": "factual_only_pending_expert_rules",
  "summary": "本次完成历法、周易、梅花易数模块的确定性推演……",
  "modules": [
    {
      "module": "zhouyi",
      "title": "周易推演结果",
      "summary": "本卦、动爻和变卦摘要",
      "sections": [
        {"title": "本卦结构", "text": "……", "rule_ids": ["YI-MANUAL-001"]}
      ],
      "limitations": []
    }
  ],
  "conclusion": {
    "status": "factual_result_only",
    "text": "当前没有引用已发布解释规则的结构化判断……"
  },
  "limitations": []
}
```

说明由确定性模板直接读取本次盘面和步骤生成，不访问语料，不调用语言模型。每个说明段落保留规则编号。当前`review_status`表示只允许复述事实；在解释规则发布前，不能生成事项吉凶、应期和行动建议。

### 3.4 结合询问事项的暂行建议

提交`context`后，多模块接口同时返回`advisory`：

```json
{
  "status": "provisional_research_advice",
  "review_status": "unreviewed_engineering_template",
  "context": {
    "category": "career",
    "question_summary": "是否接受新的工作机会"
  },
  "conclusion": {
    "headline": "先处理外部约束，再决定推进速度",
    "polarity": "indeterminate",
    "confidence_label": "不评估现实概率"
  },
  "recommendations": [],
  "verification_questions": [],
  "evidence_basis": [],
  "risk_notes": [],
  "rule_ids": ["ADV-CONTEXT-001", "ADV-MH-RELATION-001"]
}
```

支持`career`、`finance`、`relationship`、`travel`、`study`和`other`六类事项。建议综合事项类别、问题摘要、周易动爻和梅花本卦阶段体用关系，输出行动清单和待核实问题。它只作为研究性决策整理工具，不改变综合引擎的正式判断，也不允许将`polarity`改成有利或不利。

### 3.5 书籍原文与观点

启用文献检索后，响应包含`literature`：

```json
{
  "status": "available",
  "usage_scope": "internal_research",
  "query_terms": [
    {"term": "履卦", "hexagram": "履", "role": "梅花本卦"}
  ],
  "books": [
    {
      "citation_id": "BOOK-001",
      "title": "道德真经广圣义(杜光庭)",
      "source_url": "https://www.daorenjia.com/...",
      "chunk_id": "...",
      "content_sha256": "...",
      "excerpt": "君子察其所履……《易》履卦云视履考祥是也。",
      "book_opinion": "这段文字强调先辨明位置、责任和实际履行……",
      "application_note": "对应当前事项，可优先核对角色、承诺和实际行动是否一致。",
      "review_status": "automatic_candidate_unreviewed"
    }
  ],
  "warnings": []
}
```

检索词只来自本次计算得到的本卦和变卦，不使用任意问题文本搜索全文。每个不同卦优先保留一本候选书，再按书名、易学语境和明确意见词排序，默认最多3本。原文保留文档、文本块、哈希和来源链接。

`book_opinion`和`application_note`是对命中句及相邻句的确定性主题归纳。若段落只提及卦名而没有完整断语，系统必须明确说明不能直接套用，不得为了给出肯定答案而补写书中没有的内容。

## 4. 综合分类规则

综合层只处理包含`dimension`、`time_range`、`polarity`和`rule_ids`的结构化`judgements`。所有规则编号必须存在且状态为`published`，否则判断进入`excluded`，不参与综合结果。

同一分析维度和完全相同的时间范围内：

- 多条相同倾向进入`consistent`。
- 同时包含`favorable`和`unfavorable`进入`conflicts`。
- 其他不同倾向进入`complementary`。
- 只有一条判断进入`unpaired`。
- 包含`indeterminate`进入`indeterminate`。

当前登记的14条规则均为`draft`工程基线，各模块也没有解释性`judgements`，因此正常综合结果是保留模块事实，并提示没有可比较的已发布判断。两个`ADV-*`规则只产生未审核检查清单，不把五行关系转换为吉凶。

## 5. 规则与案例

- 规则登记表：`data/rules/mvp-engineering-baseline.json`
- 工程案例集：`data/validation-cases/mvp-engineering-baseline.json`
- 批量执行器：`scripts/run_validation_cases.py`

执行案例：

```bash
./scripts/run_validation_cases.py
```

当前7个案例是代码回归基线，不是计划书要求的专家标准案例。案例文件使用`engineering_regression_pending_expert_review`标识，审核人为空。专家签署前不得将其状态改为已批准或对外声称为权威案例。

## 6. 验证

```bash
.venv/bin/python -m pytest backend/tests
.venv/bin/python -m compileall -q backend/app backend/tests
./scripts/run_validation_cases.py
```

提交前还应检查`git diff --check`。计算规则变更必须同步更新规则版本、案例预期和ADR；不得用新结果覆盖旧任务或旧报告。
