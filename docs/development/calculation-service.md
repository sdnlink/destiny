# MVP计算服务

> 状态：工程基线可运行，术数解释规则与标准案例待专家签署  
> 服务入口：`http://127.0.0.1:8090`  
> 详细算法与架构文档：参见 [全系统推理引擎算法与项目架构规范](./engine-algorithms-and-framework.md)

## 1. 能力边界

当前服务提供确定性的历法、周易、梅花易数、六爻、大六壬和阳宅方位事实计算，以及多模块并列计算和结构化判断比较。计算内核不调用语言模型，也不根据未经审核的经典文本生成正式吉凶和应期。用户显式提供事项类别和问题摘要时，服务可生成标记为未审核的研究性决策检查清单和事项相关类象候选；该内容不进入正式`judgements`。包含历法模块时，结果同时输出待审核纪元基线下的元会运世位置和盘面五行关系事实。

设置`SERVE_WEB=1`后，服务会在所有API路由之后挂载`frontend/dist`。生产启动脚本负责设置该变量；计算内核本身不依赖前端代码。

已实现：

- 显式IANA时区、公农历、节气、四柱和可选真太阳时。
- 结构化干支、月建、立春生肖、旬空，以及节气绝对时刻的本地时区和UTC表示。
- 周易手工六爻、兼容双数起卦、版本化三数起卦及本卦、变卦、互卦、错卦、综卦。
- 梅花农历时间、两数、三数和个体自动起卦，以及本互变卦、体用和五行关系事实。
- 六爻六爻值、三枚硬币、时间、双数和个体自动排盘，以及八宫、世应、纳甲、六亲、六神、月建、日辰和旬空；逐爻推导月令旺衰、月破、日辰生克合冲、日破暗动与旬空填实/冲空，按本宫首卦同位补缺生成伏神飞神，给出变卦纳甲与动爻进退神，并汇总动爻与日月爻支齐备的三合局、六合组合。
- 大六壬时间、数字占时和个体报数排盘，输出月将、天地盘、四课、十二天将、旬空和逐课体覆盖矩阵；三传已覆盖贼克、克、比用、涉害、遥克、昴星、别责、八专、伏吟和返吟，遥克多候选比用不定时继续按涉害取深，不再返回待选状态。
- 奇门遁甲按节气与三元起局，输出九宫星门神仪、时旬空落宫与驿马落宫。
- 紫微斗数输出十四主星与十二宫，并为每宫给出三方四正（本宫、三合两宫、对宫）；按生年支与生月安红鸾、天喜、天刑、天姚、咸池五颗杂曜；生年四化同时输出《全书》通行本与通行别本两套变体并标注分歧。
- 风水除坐向测量共识外，提供八宅大游年九星与命卦配宅（`/v1/fengshui/bazhai`）、玄空三元九运下卦挨星盘与格局条件（`/v1/fengshui/xuankong`）、租户隔离的房屋档案存储（`/v1/fengshui/buildings`，文件/PostgreSQL 双后端）。
- 典籍依据：所有引擎结果的 `evidence` 字段从本地多来源典籍库（91 部，`/v1/classics/search` 可检索，支持简繁双向查询）引用原文段落，含来源链接与许可信息。
- 八字除四柱、十神神煞、五行旺衰与八步大运外，提供流年岁运事实序列（`/v1/bazi/liunian`：逐年干支、十神、纳音、太岁岁破、所属大运区间及与四柱的冲合刑害组合事实，仅列事实不断吉凶）。
- 阳宅坐向角度归一化、磁偏角真北修正、二十四山、测量误差候选和边界预警。
- 阳宅三至十二次读数的圆周均值、最小覆盖弧、保守误差包络和一致性状态。
- 周易、梅花、六爻和六壬个体自动排盘；各模块使用独立派生域并支持凭证重放。
- 规范输入哈希、幂等任务编号、多模块顺序计算。
- 规则登记、来源引用、规则集合校验和工程案例回归。
- 对已发布结构化判断进行一致、互补、冲突和无法判断分类。
- 根据本次计算事实生成可追溯的结果摘要和逐模块详细说明。
- 按本卦和变卦检索内部书籍语料，返回可定位原文和明确的书籍参考意见。
- 从实际盘面提取八卦、地支、六亲等类象，并按事项类别排序展示维度。
- 问测语义智能解析引擎（`inquiry_parser`）：自动提取用户问测实体（人物/主体）与核心意图（服饰颜色、当前行为动作、方位场所、心境神态、随身配饰、出行方式、脏腑健康、射覆寻物、应期吉凶）。
- 象数精准专项推断内核（`targeted_deduction`）：融合梅花体用生克、八卦万物类象、六爻纳甲六神、大六壬三传发端、奇门遁甲八门值使与紫微斗数命盘主星，给出直观明确的针对性推断结论与完整的易理证据链。
- 按公历年生成元、会、运、世位置，并比较会支五行与盘面结构五行。

未实现或未批准：

- 周易事项级吉凶/应期/行动建议解释（`core/explanation` 不产出事项级版本；工作流 step4 已产出通用旺衰、step7 已产出行动建议、应期推算已实现）。梅花旺衰由工作流 step4 产出，引擎层不直接产出。
- 任何自动吉凶总分、现实概率或准确率。
- 专家规则发布工作流及签署后的生产规则。
- 用户账号、案例档案、持久化任务和正式报告。
- 专业风水规则的专家签署与正式发布版本：八宅大游年、玄空下卦挨星已实现且规则状态仍为 `draft`，不生成吉凶断语；形势、择日等其他流派规则未实现。
- 大六壬全部发传规则的专家签署与正式发布版本；当前均为工程草稿。
- 六爻吉凶断语；用神候选、伏神出伏条件、三合成局条件已按库内《卜筮正宗》原文推导并挂典籍原文（请求带 `focus`），最终判断仍须人工复核。
- 玄空替卦（起星盘）：《沈氏玄空學》原文已在库，起星盘已按库内「起星图 216 局」实例实现为工程基线，`include_tihua_chart=true` 显式请求才提供、默认关闭，不覆盖下卦挨星盘、不含吉凶断语；替星表「寅午庚丁」已由库内两套挨星口诀（弼星9）与 422 条起星图实例逆行计算裁定为 9，原工程草稿 8（左辅）废弃（裁定记录 `TIHUA_TABLE_DISCREPANCY`）；中宫五按原典「五到向，无替可寻」不替、仍 5 入中，顺逆视山向阴阳，全 216 组合恒 `completed`；产物仍属工程基线，专家签署与正式规则发布流程另行。

## 据库内古籍原文与历法逆行计算落地的算法（工程基线，非生产签署）

以下七项此前列为「待专家口径」，现已依库内原典明文 + 历法同源计算 + 经典案例逆行反推实现，
仍属 `engineering_baseline`，不生成吉凶断语：

- **六壬月将时区基准**：《六壬指南》「正月雨水后日躔娵訾之次入亥宫，乃登明将也」→ 月将按十二中气换将，并改用 `CalendarEngine` 的 `solar_term_reference_datetime`，与四柱节气同源（真太阳时/非东八区不再错将）。
- **八字起运与四柱同源**：起运重建改用 `normalized_input.effective_local_datetime`（含真太阳时修正），不再另用未修正的原始时间。
- **玄空替卦坐度边界**：《沈氏玄空學·論起星》「兼一二分者无须寻替，若兼三四分者当用替星」→ 3.0 度边界归入起替区间（闭区间）；并新增实测角度所属山与声明坐山的一致性事实，不一致时提示复测。
- **奇门中五宫值使基准**：《遁甲演義》「直使在五官，寄坤二官」→ 值使步进起点与值符统一采用已寄坤二宫的基准，消除同盘两套基准。
- **紫微大限顺逆**：《紫微斗數全書·安大限诀》「阳男阴女从命前一宫起顺行，是父母宫；阴男阳女从命后一宫起逆行，是兄弟宫」→ 顺逆公式按原典校正（顺行第二限父母宫、逆行第二限兄弟宫）。
- **六爻填实**：《卜筮正宗·旬空论第十》「待其出旬、值日…填补之法」、占验「应于丑日者出旬之日也」→ 不再把当日伪状态写成「填实」，改以六十甲子历法顺推每个旬空支「出旬值日」的确定性应期 `facts.void_fill_prospects`。
- **六爻出伏与三合入墓**：《卜筮正宗·伏神正传第六》「伏待出露」、黄金策「空下伏神易于引拔」、飞伏生克吉凶歌「伏克飞神为出暴，飞来克伏反伤身」→ 出伏 blocker 改按伏神自身地支/五行与飞伏生克关系判定，不再把飞神状态冒充伏神；三合入墓依「合待冲开」「墓中人，不冲不发」改为按实际墓爻静/空/破判定，消除恒真条件。

回归护栏见 `backend/tests/test_classics_based_algorithms.py`（原典案例逆行验证 + 全六十甲子/全组合不变量）。

数据边界（非"未实现"，仅记录残余缺口）：典籍待补清单已清账，八宅明镜/阳宅十书/沈氏玄空学/紫微斗数全书/卜筮正宗均由公开来源补齐入库（详见 `/v1/classics/status` 的 `sourcing_backlog`）；《紫微斗數全書》卷四图说（站方仅 PDF 扫描）与《阳宅三要》暂缺。

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

启用令牌后，所有请求添加`Authorization: Bearer <token>`（服务端用常量时间比较）。当前令牌方案只用于受控内部环境，不能替代正式账号、租户权限、限流、审计和TLS：

- 房屋档案的 `tenant_id` 默认由调用方声明，单 token 部署下不构成身份隔离；多租户部署必须设置 `FENGSHUI_TENANT_ID`，此后所有读写强制绑定到该服务端租户、忽略客户端声明。
- 会话模块尚无归属字段，`/v1/sessions` 会列出全部会话，仅适用于单租户本地环境；接入账号体系前不得部署为共享服务。
- ClickHouse 口令不再内置默认值，应用与 `scripts/load_*.sh` 均需显式注入 `CLICKHOUSE_PASSWORD`。

## 3. 接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/health` | 健康状态和模块版本 |
| `GET` | `/v1/constants/trigrams` | 八卦常量及全维度万物类象（优先自数据库读取） |
| `GET` | `/v1/constants/trigram-imagery` | 八卦类象明细表，支持按`trigram`和`dimension`维度筛选 |
| `GET` | `/v1/constants/hexagrams` | 六十四卦常量（自数据库读取） |
| `GET` | `/v1/constants/five-elements` | 五行生克与方位时令常量（自数据库读取） |
| `GET` | `/v1/constants/stems` | 十天干属性与方位常量（自数据库读取） |
| `GET` | `/v1/constants/branches` | 十二地支生肖藏干方位常量（自数据库读取） |
| `GET` | `/v1/constants/solar-terms` | 二十四节气黄经度数与季节常量（自数据库读取） |
| `GET` | `/v1/constants/sexagenary-cycle` | 六十甲子与纳音五行常量（自数据库读取） |
| `GET` | `/v1/constants/fengshui-mountains` | 风水二十四山度数与八卦归属常量（自数据库读取） |
| `GET` | `/v1/constants/luoshu-palaces` | 洛书九宫五行方位常量（自数据库读取） |
| `GET` | `/v1/constants/twenty-eight-mansions` | 二十八宿四象、禽星、古宿度与类象常量（自数据库读取，支持`quadrant`筛选） |
| `GET` | `/v1/constants/three-enclosures` | 三垣星官体系与步天歌总诀常量（自数据库读取） |
| `GET` | `/v1/constants/historical-calendars` | 中国历代代表性历法（太初/大明/大衍/授时/时宪等）参数与算法常量（自数据库读取，支持`dynasty`筛选） |
| `GET` | `/v1/constants/hetu-numerology` | 河图五行生成数理与干支化气常量（自数据库读取，支持`element`筛选） |
| `GET` | `/v1/constants/lunar-phases` | 西周金文四分月相（初吉/既生霸/既望/既死霸）定义与历谱常量（自数据库读取） |
| `GET` | `/v1/database/stats` | ClickHouse 数据库连接状态与表行数统计 |
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
| `POST` | `/v1/meihua/three-numbers` | 梅花三数独立取上卦、下卦和动爻 |
| `POST` | `/v1/liuyao/auto` | 六爻个体三枚铜钱自动排盘及纳甲 |
| `POST` | `/v1/liuyao/time` | 六爻传统时间排盘及纳甲 |
| `POST` | `/v1/liuyao/numbers` | 六爻双数排盘及纳甲 |
| `POST` | `/v1/liuyao/lines` | 六个6/7/8/9爻值排盘及纳甲 |
| `POST` | `/v1/liuyao/coins` | 六轮三枚硬币排盘及纳甲 |
| `POST` | `/v1/liuren/auto` | 大六壬个体报数自动排盘 |
| `POST` | `/v1/liuren/time` | 大六壬传统时间排盘 |
| `POST` | `/v1/liuren/numbers` | 大六壬数字占时排盘 |
| `POST` | `/v1/fengshui/direction` | 阳宅真北坐向、二十四山及误差分析 |
| `POST` | `/v1/fengshui/measurements` | 阳宅多次坐向测量圆周共识 |
| `POST` | `/v1/calculations/evaluate` | 统一单模块计算封装（含 `bazi/liunian`） |
| `POST` | `/v1/calculations/compare` | 最多8个模块顺序计算和综合比较 |
| `POST` | `/v1/bazi/liunian` | 八字流年岁运事实序列（干支/十神/大运区间/冲合刑害/典籍依据） |
| `GET` | `/v1/classics/status` | 多来源典籍库状态与来源补齐记录 |
| `GET` | `/v1/classics/search` | 典籍原文段落检索（简繁双向查询） |
| `GET` `POST` | `/v1/fengshui/bazhai` | 八宅大游年九星与命卦配宅 |
| `GET` `POST` | `/v1/fengshui/xuankong` | 玄空三元九运下卦挨星与格局条件 |
| `GET` `POST` `DELETE` | `/v1/fengshui/buildings[/{id}]` | 租户隔离的房屋档案（文件/PostgreSQL 双后端） |

以上接口在设置 `APP_API_TOKEN` 时统一要求 `Authorization: Bearer <token>`；静态页面与 `/health` 探活保持公开。
OpenAPI文档位于`/docs`，机器契约位于`/openapi.json`。

周易三数示例：

```bash
curl -X POST http://127.0.0.1:8090/v1/zhouyi/three-numbers \
  -H 'Content-Type: application/json' \
  -d '{"numbers":[23,47,5],"mapping_version":"earlier-heaven-number-v1"}'
```

三数法中第一数取上卦、第二数取下卦、第三数独立取动爻。旧`/v1/zhouyi/numbers`是第一数下卦、第二数上卦、两数之和取动爻的兼容规则，二者不可混用。

梅花三数接口同样使用`numbers`数组，但规则属于梅花领域：

```bash
curl -X POST http://127.0.0.1:8090/v1/meihua/three-numbers \
  -H 'Content-Type: application/json' \
  -d '{"numbers":[25,38,5]}'
```

第一数取上卦、第二数取下卦、第三数取动爻，并继续执行梅花自己的互卦和体用规则；不会生成六爻世应或纳甲。

六爻值和硬币接口均按初爻至上爻排列。六爻值只允许6、7、8、9；硬币必须为六轮，每轮三枚且每枚只允许2或3，正面编码为3、反面编码为2。两种接口均输出每爻原值、老少阴阳、动静和变化后阴阳，并附加逐爻月令旺衰（旺/相/休/囚/死）、月破、日辰关系（临/冲/合/受生/泄气/受克）、日破、暗动、旬空状态（旬空/填实/冲空）、变卦纳甲与进退神。伏神飞神按本宫首卦（八纯卦）同位补缺推导，返回`status: completed`；首卦同一六亲多处出现时取最低爻位，其余写入`alternative_positions`。

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

当前登记的84条规则均为`draft`工程基线，各模块也没有解释性`judgements`，因此正常综合结果是保留模块事实，并提示没有可比较的已发布判断。两个`ADV-*`规则只产生未审核检查清单，不把五行关系转换为吉凶。

## 5. 规则与案例

- 规则登记表：`data/rules/mvp-engineering-baseline.json`
- 工程案例集：`data/validation-cases/mvp-engineering-baseline.json`
- 批量执行器：`scripts/run_validation_cases.py`

执行案例：

```bash
./scripts/run_validation_cases.py
```

当前31个案例是代码回归基线，不是计划书要求的专家标准案例。案例文件使用`engineering_regression_pending_expert_review`标识，审核人为空。专家签署前不得将其状态改为已批准或对外声称为权威案例。

## 6. 验证

```bash
python -m pytest backend/tests
python -m compileall -q backend/app backend/tests
./scripts/run_validation_cases.py
```

提交前还应检查`git diff --check`。计算规则变更必须同步更新规则版本、案例预期和ADR；不得用新结果覆盖旧任务或旧报告。
