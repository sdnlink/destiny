# 天机演象 · 项目介绍与框架说明

> 本文档为仓库级说明，汇总「天机演象」项目的定位、系统框架、目录结构、技术实现与运行方式，是新成员和协作者了解全貌的入口。

---

## 1. 项目概述

**天机演象**（英文代号 *Destiny Engine*）是一个**传统术数数字化研究与辅助分析平台**。它把历法、周易、梅花易数、六爻、八字、紫微斗数、奇门遁甲、大六壬、阳宅风水等传统术数体系，从"口传心授、依赖个人经验"转化为**可复现、可追溯、可审核的确定性工程计算**，并为专业顾问与研究者提供辅助排盘、综合研判与经典文献考据能力。

项目遵循的核心原则：

- **计算正确、结果可复现**：所有正式计算绑定不可变输入快照与规则版本，同一输入必然得到同一结果。
- **规则可治理**：每条工程规则独立编号、带来源引用、可审核、可发布/下线，历史结果不随规则变更而失真。
- **术数领域解耦**：各术数体系为独立领域内核，单个模块失败不影响其他模块。
- **语料驱动**：ClickHouse 语料服务基于双来源（Wikisource 开放文本与道人家古籍）构建大规模文献语料；引擎结论另由本地多来源典籍库（91 部：维基文库 53 + 殆知阁 GitHub 存档 34 + 公开古籍网站转录 4，支持简繁双向检索）提供原文依据。
- **审慎输出**：当前所有规则均为工程草稿，推演结果用于研究参考，不替代经专家签署的专业意见。

> **当前阶段定位**：已完成项目设计、双来源书籍语料与 ClickHouse 检索、91 部本地典籍库，以及历法、周易、梅花易数、六爻、大六壬、风水方位（含八宅/玄空下卦挨星与替卦起星盘）、八字（含流年事实序列、子平月令取格候选、个人生平时间轴）、紫微、奇门、皇极经世元会运世定位等确定性工程计算内核。铁板神数因条文底本/编号表/考刻算法未入库，仅提供数据缺口状态端点。解释、类象、元会运世纪元锚点、玄空替卦盘署名字段及规则发布仍须按来源、版本和专家案例逐项审核。

---

## 2. 技术栈

| 层次 | 技术选型 |
| --- | --- |
| 后端语言 | Python 3.11+ |
| 后端框架 | FastAPI（API 层）、Python `http.server`（内部只读语料 API） |
| 前端框架 | React 19 + Vite 8 + lucide-react，Playwright 浏览器测试 |
| 历法底层 | `lunar-python`（1.4.8）+ 自研时区/真太阳时内核 |
| 数据仓库 | ClickHouse（Docker Compose 部署），ReplacingMergeTree 引擎 |
| 规则与数据 | JSON（规则注册表、验证案例、生成语料，均带 SHA-256 校验和） |
| 测试 | pytest（后端单测/领域回归）、Playwright（前端冒烟） |
| 部署 | Docker Compose + 一键脚本（bat / ps1 / sh） |

---

## 3. 系统架构

系统采用**清洁架构（Clean Architecture）**与**模块化单体（Modular Monolith）**结合的分层设计。前端只通过 HTTP/RESTful JSON 访问后端，AI 服务不在核心计算调用链中。

```text
┌────────────────────────────────────────────────────────────────┐
│                    前端表现层（React 19 + Vite）                │
│  InputPanel 输入面板 · ResultWorkspace 结果工作台                │
│  规则目录 · 概念速查 · 历史推演与案例库 · 多主题                 │
└─────────────────────────────┬──────────────────────────────────┘
                              │ HTTP / RESTful JSON
┌─────────────────────────────▼──────────────────────────────────┐
│                 API 调度与接入网关（FastAPI main.py）           │
│  Pydantic 入参校验 · 幂等请求哈希 · 顺序计算封装                 │
│  Bearer Token 鉴权 · 统一错误信封 · 常量/规则/验证接口          │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                    多模块推演编排层（app/core）                 │
│  Synthesis 综合研判 · Comparison 多源对比 · Advisory 建议       │
│  Imagery 类象 · YuanHui 元会运世 · Literature 文献 · 定向推演    │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│           9 大独立领域推理计算内核（backend/app/<domain>）      │
│  calendar 历法 · zhouyi 周易 · meihua 梅花易数 · liuyao 六爻     │
│  bazi 八字 · ziwei 紫微 · qimen 奇门 · daliuren 大六壬 · fengshui│
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│              公共基础与象数基石层（backend/app/common）          │
│  hexagrams 卦象 · trigrams 八卦 · ganzhi 干支 · five_elements 五行│
│  casting 随机起卦协议 · serialization 结果契约                  │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                   数据存储与语料检索层                          │
│  ClickHouse（语料/常量/规则/验证案例） · data/ JSON 规则资产      │
│  cache/ 古籍缓存 · scripts/ 采集与装载脚本                      │
└────────────────────────────────────────────────────────────────┘
```

### 3.1 架构原则

- **事务数据与分析数据分离**：业务事实与不可变分析明细分开存储。
- **计算内核不直接访问用户数据库**：领域引擎只消费输入快照，不感知用户体系。
- **确定性优先**：`calculate` 为确定性函数；时区、时间边界、流派版本必须显式传入，禁止读取服务器隐式默认值。
- **报告只消费已保存的结构化结果**，不重新排盘。
- **单个术数模块失败不拖垮整体**：综合研判允许 `partially_completed` 状态。
- **AI 解释可缺失**：AI 服务失败只影响解释文本，不影响结构化结果。

---

## 4. 仓库目录结构

```text
destiny/
├── backend/                  # Python 后端
│   ├── app/
│   │   ├── main.py           # FastAPI 计算 API 主入口（含交互式推演会话端点，SERVE_WEB 时挂载前端静态资源）
│   │   ├── corpus_api.py     # 内部只读语料检索 API（标准库实现，独立端口）
│   │   ├── common/           # 公共基础层：卦象/八卦/干支/五行/随机起卦/序列化
│   │   ├── core/             # 编排与能力层：综合研判、类象、文献、元会运世、规则注册表、
│   │   │                     #   定向推演、事项解析、建议生成、ClickHouse 仓库访问
│   │   ├── session/          # 不可变推演会话模型：会话/快照/交互记录/JSON存储（盘面铁律强制执行）
│   │   ├── workflow/         # 7步工作流引擎：调度/排盘/步骤/格式渲染（强制完整流程）
│   │   ├── interaction/      # 交互模块A-G：信息补全/现实校验/多方取象/分支推演/事后复盘
│   │   └── calendar/ zhouyi/ meihua/ liuyao/ bazi/ ziwei/ qimen/ daliuren/ fengshui/
│   │                         # 9 大领域引擎，每域统一 engine.py / models.py / rules.py
│   └── tests/                # pytest 测试（领域回归、API、语料、边界、工作流会话等 30+ 文件）
├── frontend/                 # React + Vite Web 推演工作台
│   ├── src/
│   │   ├── App.jsx           # 应用壳：导航（经典/交互/命运专项三模式）、抽屉、状态编排
│   │   ├── components/       # InputPanel.jsx / ResultWorkspace.jsx / WorkflowPanel.jsx（交互式工作流）
│   │   ├── lib/              # api.js（HTTP 封装）/ sessionApi.js（会话API）/ export.js（Markdown 导出）
│   │   │                     # storage.js（历史本地持久化）/ glossary.js（概念速查）
│   │   └── styles.css        # 宣纸/玄墨/青铜多主题
│   └── tests/smoke.mjs       # Playwright 浏览器冒烟测试
├── clickhouse/init/          # ClickHouse 建表脚本（001_schema.sql）
├── data/
│   ├── rules/                # 规则注册表（mvp-engineering-baseline.json 等）
│   ├── validation-cases/     # 工程回归验证案例
│   ├── sources/              # 语料来源清单（wikisource-books.json 等）
│   ├── generated/            # 生成的结构化常量语料（JSONL：干支/八卦/六十四卦/廿八宿/三垣/河图数…）
│   └── generated/calendar-corpus/ corpus/ wikisource-corpus/   # 历法与经典语料
├── scripts/                  # 根级脚本：启动、构建、部署、采集、语料装载、校验
├── cache/                    # 道人家 / Wikisource 古籍抓取缓存
├── docs/                     # 项目计划、设计决策（ADR）、数据/开发文档
├── docker-compose.yml        # ClickHouse 等基础设施编排
├── README.md                 # 根 README（快速启动入口）
├── build_all.bat / start_all.bat / start_dev.bat / data-sources.json
└── 数据/历法/                 # 历法类原始资料
```

### 4.1 共享数据约定

- `data/generated/*.jsonl` 为**生成的结构化常量语料**（八卦、六十四卦、干支、五行、二十四节气、二十八宿、三垣、洛书九宫、河图数、风水二十四山、历史历法等），经 `scripts/build_*.py` 从权威来源生成，可装载进 ClickHouse。
- `data/rules/*.json` 为**规则注册表**，每条规则含 `rule_id/version/system/school/status/title/purpose/preconditions/inputs/procedure/outputs/source_refs/limitations/owner/reviewers/implementation` 等字段，带 SHA-256 校验和。
- `data/validation-cases/*.json` 为**工程回归案例**，含 `case_id/system/school/method/input/expected/tags/review_status/source_refs` 等字段。
- `data/validation-cases/xuankong-reverse-cases.json` 为**从典籍原文派生的起星图样例**（216 局 / 430 条可解析实例），由 `scripts/build_xuankong_reverse_cases.py` 重建；原始 20MB 语料不入库，CI 直接读取该样例。
- `data/validation-cases/classics-fixture/` 为**典籍检索压缩夹具**（10 条原文片段），由 `scripts/build_classics_test_fixture.py` 重建；完整语料不存在时测试自动改读该夹具，完整语料存在时仍校验真实规模与来源清单。
- `cache/` 为抓取缓存（道人家、Wikisource 的 metadata/texts），供离线复现。

---

## 5. 后端框架详解

### 5.1 API 层（`backend/app/main.py`）

FastAPI 应用 `APP_VERSION = "0.2.0"`，提供以下能力：

- **健康检查**：`GET /health` 返回服务名、版本与当前模块清单。
- **常量只读接口**：`/v1/constants/*`（八卦、卦象、卦爻解释、五行、天干、地支、节气、六十甲子、风水山、洛书九宫、廿八宿、三垣、历史历法、河图数、月相）。优先读 ClickHouse，数据库不可用时自动降级到内存常量。
- **规则与验证接口**：`GET /v1/rules`、`GET /v1/validation-cases`、`POST /v1/validation-cases/run`。
- **历法分析**：`POST /v1/calendar/analyze`。
- **各术数排盘接口**：`/v1/{module}/{method}`，覆盖：
  - `zhouyi`：manual（六爻手工）、auto（自动）、time（时间）、numbers（两数）、three-numbers（三数）
  - `meihua`：time / auto / numbers / three-numbers
  - `liuyao`：time / auto / numbers / lines / coins
  - `liuren`：time / auto / numbers
  - `ziwei`：time / auto（含 gender）
  - `bazi`：time / auto（含 gender）
  - `qimen`：time / auto
  - `fengshui`：direction（单次朝向）/ measurements（多次测量共识）/ bazhai（八宅，GET+POST）/ xuankong（玄空，GET+POST）/ buildings（房屋档案，GET 列表与详情、POST 保存、DELETE 删除）
- **综合推演**：`POST /v1/calculations/evaluate`（单模块）+ `POST /v1/calculations/compare`（多模块顺序执行 + 综合研判）。
- **鉴权与错误**：可选 `APP_API_TOKEN` Bearer 校验；统一错误信封 `{error: {code, message}}`；`ValueError` 映射为 422。
- **静态托管**：设置 `SERVE_WEB=1` 时挂载 `frontend/dist`，实现单端口生产部署。

**计算封装（Calculation Envelope）**：每次计算生成 `task_id = calc_{sha256[:24]}` 与 `input_hash = sha256:...`，保证相同输入幂等可复现。

### 5.2 领域引擎层（9 大内核）

每个领域目录统一包含 `engine.py`（主引擎）、`models.py`（Pydantic/数据模型）、`rules.py`（规则编号引用），并通过 `__init__.py` 暴露 `*_cast` / `calculate_*` 等函数。全部引擎统一返回**版本化结果契约**：

```json
{
  "schema_version": "2.0",
  "system": "zhouyi",
  "school": "three-number-engineering-baseline",
  "engine_version": "...",
  "algorithm_version": "...",
  "rule_version": "...",
  "input": {...},
  "normalized_input": {...},
  "facts": {...},
  "calculation_trace": ["..."],
  "steps": [{"sequence": 1, "operation": "...", "inputs": {...}, "output": {...}, "rule_ids": ["YI-..."]}],
  "evidence": [],
  "judgements": [],
  "warnings": ["..."],
  "interpretation": {...}
}
```

关键约定：`facts` 为确定性事实；`steps` 每一步可回溯到 `rule_ids`；`warnings` 声明"待专家签署"等限制。各引擎简介：

| 引擎 | 职责要点 |
| --- | --- |
| **历法 Calendar** | 统一历法基线：IAIN 时区解析、真太阳时修正（经度+均时差）、干支四柱（年以立春/月以节令/日子初分界）、月支与节气边界一致性校验、当日十二时辰吉凶时序轮盘、闰月/农历信息。`calendar-engine-2.0.0+lunar-python-1.4.8` |
| **周易 Zhouyi** | 文王六十四卦矩阵、八卦二进制编码、本卦/变卦/互卦/错卦/综卦派生；支持手工/自动/时间/两数/三数起卦，含三数映射版本管理 |
| **梅花易数 Meihua** | 时间/自动/数字/三数起卦，卦象派生与类象关联 |
| **六爻 Liuyao** | 时间/自动/数字/手工爻/铜钱起卦，纳甲与动爻处理 |
| **八字 Bazi** | 四柱排盘（gender 参数），年/月/日/时柱与十神 |
| **紫微斗数 Ziwei** | 时间/自动排盘（gender 参数），十二宫与星曜 |
| **奇门遁甲 Qimen** | 时间/自动起局，八门九星八神等 |
| **大六壬 Daliuren** | 时间/自动/数字起课，三传四课、特殊传递（涉害/返吟/伏吟等） |
| **阳宅风水 Fengshui** | 真北坐向、二十四山、磁偏角与测量误差、多次测量共识统计；只处理空间事实，不依赖历法 |

**自动起卦协议（app/common/casting.py）**：以用户提供的 16–128 位 `cast_nonce` 为种子，通过 `sha256(nonce + sequence)` 派生 2–3 的整数/铜钱序列，实现"个人化、可复现、同一 nonce 不重卦"的随机性方案。

### 5.3 编排与综合研判层（`app/core`）

| 模块 | 职责 |
| --- | --- |
| `synthesis.py` | 多模块结果综合研判（resonance 共振指数、共识矩阵），仅比较已发布规则的结构化判断，不生成自动吉凶总分 |
| `comparison`（main.py） | 多模块顺序计算 + 综合 + 解释 + 建议 + 文献 + 类象 + 元会运世 + 定向推演，统一返回 |
| `advisory.py` | 按事项类别（职业/财运/感情/学业/出行等）生成研究性结论、优先建议与核实清单 |
| `interpretation.py` | 事项与卦象的对应解释（explain_correspondences） |
| `imagery.py` | 万物类象映射：八卦/地支等维度类象候选 |
| `yuanhui.py` | 元会运世（邵雍）宏观时空背景关联 |
| `literature.py` | 匹配卦象的书籍原文观点收集，含来源链接与未审核标注 |
| `inquiry_parser.py` | 定向事项意图解析（职业/财帛/健康/出行等） |
| `targeted_deduction.py` | 定向推演引擎：基于事项类别 + 对应术数（奇门/紫微等）的针对性推断 |
| `registry.py` | 规则注册表加载与结构校验（必填字段、唯一性、规则集引用、状态枚举、校验和） |
| `validation.py` | 验证案例批量运行与比对 |
| `hexagram_service.py` | 六十四卦解释服务（含文件缓存与 ClickHouse 回源） |
| `db.py` | ClickHouse 数据仓库只读访问（`db_repository`） |
| `iching.py / meihua.py / liuyao.py / liuren.py` | 各领域可复用的核心推导逻辑 |

### 5.4 内部语料服务（`corpus_api.py`）

基于标准库 `ThreadingHTTPServer` 的只读检索 API（独立于主 API），提供语料文档/文本块检索、摘要（snippet）、分页、来源范围控制（`source_specific_policy`）与内容哈希校验，供文献引用与类象检索使用。默认运行在 `:8088`。

### 5.5 交互式推演工作流引擎（`session/` + `workflow/` + `interaction/`）

这是本次重构的核心新增层，将项目从"无状态计算引擎"升级为"有状态、多轮交互、强制流程、盘面不可变"的标准化术数推演工程师。

#### 5.5.1 不可变会话模型（`app/session/`）

| 组件 | 职责 |
| --- | --- |
| `DivinationSession` | 推演会话：求测事由、术数门类、起盘方式、起盘素材、用户画像、状态机、不可变快照、交互记录列表 |
| `DivinationSnapshot` | 不可变排盘快照：`frozen=True` 写入即冻结，含原始盘面 `raw_plate`、各模块结果、输入哈希 `input_hash`、规则版本、使用体系 |
| `InteractionRecord` | 交互记录：只追加不修改，含 `interpretation_shift`（解读视角调整，与原始盘面分离） |
| `SessionStore` | JSON 文件持久化（`data/sessions/`），生产可替换为 PostgreSQL |

**铁律强制执行**：
- `freeze_snapshot()` 是唯一可设置快照的入口；已冻结快照再次调用抛 `RuntimeError("盘面已冻结，不可重新排盘")`。
- `append_interaction()` 只追加记录，绝不触碰 `session.snapshot`。
- 所有交互模块返回 `snapshot_unchanged: True`，明确声明原始盘面未被修改。

**会话状态机**：`draft` → `casted`（排盘后冻结快照）→ `interacting`（首次交互后）→ `reviewed`（事后复盘后）。

#### 5.5.2 7步工作流引擎（`app/workflow/`）

强制完整执行7步流程，禁止跳过逻辑直接输出结论：

| 步骤 | 函数 | 输出 |
| --- | --- | --- |
| 1. 信息校验 & 起盘数据源确认 | `step1_info_validation` | 求测事由、起盘方式、起盘素材、缺失字段、是否可排盘 |
| 2. 完整排盘输出 | `step2_format_plate` | 各体系盘面客观数据（卦名/体用/动爻/干支/计算轨迹），不含主观判断 |
| 3. 定用神，锁定分析焦点 | `step3_identify_yongshen` | 主用神/辅助用神、取用逻辑、多方人物用神 |
| 4. 旺衰状态计算 | `step4_wangshuai_analysis` | 用神旺衰（得令/相/休/囚/死）、体用关系、生克链条、月令日辰上下文 |
| 5. 象义拆解推理 | `step5_xiangyi_deduction` | 卦爻符号→现实事件映射，禁止单纯摘抄古文，必须结合测事场景 |
| 6. 综合吉凶定性 & 事态推演 | `step6_synthesis_judgement` | 当前现状、有利点、阻碍点、趋势、参考应期、吉凶等级（大吉/小吉/平/小凶/大凶；未排卦象体系时为「未评级」且不出分）+ 判定依据 |
| 7. 行动建议与免责提示 | `step7_advice_and_disclaimer` | 可落地趋吉避凶建议 + 文化提示免责 |

**术数调度策略**（`scheduler.py`）：
- 未指定门派（`auto`）：默认主用**梅花易数 + 六爻辅助**参断
- 指定六爻：单体系完整纳甲装卦
- 指定奇门：时家奇门单体系
- 指定大六壬：月将日辰四课三传单体系
- 历法始终作为基线预处理

**固定输出格式**（`format.py`）：渲染为角色规范定义的固定文案格式——求测事由→起盘方式→完整排盘→用神定位→旺衰分析→象义解读→综合推演→趋吉避凶→文化提示→拓展参考资料库→卦象现状核对→后续交互入口。

**排盘执行器**（`casting.py`）：按序调用各领域引擎，复用现有 9 大领域计算内核，不重复实现算法。

#### 5.5.3 交互模块A-G（`app/interaction/`）

| 模块 | 文件 | 功能 |
| --- | --- | --- |
| **A 起盘前信息补全** | `info_completion.py` | 检测缺失字段（最多3项），生成补全问题；用户回复"直接起盘"则跳过 |
| **B 排盘后现实校验** | `reality_check.py` | 用户回复符合/部分符合/不符合；符合→进入拓展；部分符合→保留原盘调整象义映射；不符合→询问重起或换取象角度。**原始盘面始终不动** |
| **C 拓展参考资料库** | 内置于 `workflow/engine.py` | 固定输出5项：核心符号原始象义/重点风险隐患/参考时间窗口/多发展可能性与触发条件/常见误读误区 |
| **D 后续交互入口** | 内置于 `workflow/engine.py` | 固定输出6项菜单：核对现状/深度追问/换角度解读/更换门派/代入选择推演/留存复盘 |
| **E 多方人物取象** | `multi_party.py` | 自动识别问题中涉及人物，分别取各方专属用神（世爻/应爻/官鬼/妻财等），解析立场/心态/诉求；支持单一人物深化解读 |
| **F 多抉择分支推演** | `multi_choice.py` | 基于现有卦盘做分支推演，输出各选择利弊/风险/趋势/综合建议；原盘信息不足时如实告知 |
| **G 事后复盘** | `review.py` | 用户反馈现实结果，保留原始卦盘完全不变；区分应验象/未应验象，从用神/旺衰/应期/人为外部干扰角度分析，输出经验教训 |

#### 5.5.4 交互式推演会话 API

| 端点 | 方法 | 功能 |
| --- | --- | --- |
| `/v1/sessions` | POST | 创建推演会话（返回信息补全提示） |
| `/v1/sessions` | GET | 列出会话列表 |
| `/v1/sessions/{id}` | GET | 获取会话完整状态（含不可变快照、交互记录、工作流结果） |
| `/v1/sessions/{id}/cast` | POST | 执行7步工作流排盘，冻结不可变快照，返回完整推演结果 |
| `/v1/sessions/{id}/interact` | POST | 交互入口：reality_check / multi_party / multi_choice / review / deep_question / angle_shift / info_completion |
| `/v1/sessions/{id}` | DELETE | 删除推演会话（含不可变快照与交互记录） |

**安全约束**：`/cast` 在快照已冻结时返回 409 `SNAPSHOT_FROZEN`，强制盘面不可变；`/interact` 所有操作均返回 `snapshot_unchanged: True`。

---

## 6. 前端框架详解（Web 推演工作台）

技术栈：React 19 + Vite 8 + lucide-react，纯前端 SPA，通过 `lib/api.js` 调用后端。

**核心交互流程**：

1. **输入面板（InputPanel）**：选择推演场景（综合 / 单术数 / 风水）、事项类别与问题；设定本地时间、时区、真太阳时与经度；每种术数可切换起卦方式（自动/时间/数字/手工/铜钱等）；支持历法即时预览与一键"设为当前时间"。
2. **提交推演**：每次提交自动生成新的 `cast_nonce`，`buildCalculations()` 按场景组装多模块请求，调用 `POST /v1/calculations/compare` 顺序计算；结果自动存入本地历史（最近 50 条）。
3. **结果工作台（ResultWorkspace）**：多标签展示——综合概览、历法详情、逐模块结果、综合研判与建议、文献引证、类象候选、元会运世、定向推演；支持导出 Markdown 推演报告。
4. **辅助抽屉**：
   - **规则目录**：按系统过滤查看规则注册表（标注"工程草稿，未专家签署"）。
   - **概念速查（Glossary）**：术数典籍与核心概念（卦名、十神、八门九星、二十四山等）按类别检索。
   - **历史推演与案例库**：本地持久化（localStorage）50 条记录，支持复盘载入、Markdown 导出、JSON 全量备份/还原。

**主题与视觉**：宣纸素雅 / 玄墨深邃 / 青铜古韵三种主题，通过 `data-theme` 属性切换并持久化。

**三模式导航**：左侧导航提供「经典推演」「交互推演」与「命运专项」三种模式切换：
- **经典推演**：原有 InputPanel + ResultWorkspace 流程，适合快速多模块对照计算。
- **命运专项（DestinyPanel）**：以出生时刻为唯一输入，复用既有八字接口，提供三个子功能：
  1. **本命盘**：四柱、藏干十神、五行旺衰与大运起运（`POST /v1/calculations/evaluate`，`bazi/time`）。
  2. **流年**：按公历起止年份列出流年干支、十神、纳音、大运区间与岁运组合事实（`POST /v1/bazi/liunian`）。
  3. **生平时间轴**：复用 `LifelineView`，独立录入生辰与已发生事件，调用 `POST /v1/bazi/lifeline`；事件只做只读对齐，不预测未来。
  紫微流年/大限暂未拆入该工作区，因为后端尚无对应独立流年能力；六爻/奇门/六壬属事件型起盘，也不作为年度命运入口。
- **交互推演（WorkflowPanel）**：标准化7步工作流界面，完整实现角色规范的交互闭环：
  1. **创建会话**：输入求测事由、事项类别、术数门类、起盘方式、性别、当前阶段。
  2. **信息补全（模块A）**：系统检测缺失信息并按需提问（最多3项），支持"直接起盘"跳过。
  3. **7步排盘**：执行强制7步流程，盘面生成后立即冻结，显示完整格式化推演结果（含吉凶定性横幅）。
  4. **结果标签页**：完整推演文本 / 结构化7步数据 / 交互深化 / 交互记录。
  5. **交互深化（模块B/E/F/G）**：
     - 现实校验：符合/部分符合/不符合，仅调整解读视角不改盘面。
     - 多方人物取象：输入角色列表，分别解析立场/心态/诉求。
     - 多抉择分支推演：输入备选方案，输出各方案利弊/风险/趋势/综合建议。
     - 事后复盘：反馈现实结果，对比应验/未应验，输出经验教训。
     - 深度追问 / 换角度解读。
  6. **交互记录**：所有交互追加记录，原始快照始终不变。

前端通过 `lib/sessionApi.js` 调用交互式会话 API（`/v1/sessions` 系列端点）。

**交互推演优化（v2）**：
- **报数/手工起卦**：选择报数起卦时显示3个数字输入框，手工起卦时显示上卦/下卦/动爻输入，不再硬编码默认值。
- **独立 loading 状态**：每个交互区域有独立的加载指示器，避免全局 loading 阻塞其他操作。
- **交互后自动跳转**：提交交互后自动切换到"交互记录"标签，即时查看结果。
- **会话恢复**：创建阶段支持输入会话ID恢复已有推演结果和交互记录。
- **复制结果**：一键复制完整推演文本到剪贴板。
- **折叠式交互区**：交互深化区域可折叠/展开，默认展开第一个，减少页面长度。
- **结构化数据友好展示**：用神定位、旺衰分析、综合推演等步骤使用卡片式友好展示，而非纯 JSON dump。
- **角度快捷按钮**：换角度解读提供"对方立场/长期视角/财务角度/风险角度/机会角度"快捷预设。
- **Enter 快捷提交**：所有输入框支持 Enter 提交，求测事由支持 Ctrl+Enter。
- **错误自动清除**：错误提示6秒后自动消失。
- **深度追问真正实现**：基于已冻结盘面的卦名/动爻/用神/六亲/六神/五行/旺衰等符号，自动检测追问方向并生成针对性深化解读（10种符号类型）。
- **换角度解读真正实现**：8种预设角度（对方立场/长期视角/财务/感情/事业/风险/机会等）+ 自定义角度，重新映射卦象象义并输出调整后的解读视角，原始盘面不变。
- **会话历史列表**：创建页可浏览最近50个推演会话（问题/类别/状态/时间），点击直接恢复，支持删除。
- **导出推演报告**：一键将完整推演结果导出为 Markdown 文件。
- **表单草稿自动保存**：求测事由等输入自动保存到 localStorage，刷新或误关页面后自动恢复。
- **会话删除 API**：新增 `DELETE /v1/sessions/{id}` 端点，支持删除会话及关联快照与交互记录。

---

## 7. 数据存储：ClickHouse

`clickhouse/init/001_schema.sql` 定义 `destiny` 库，全部业务表采用 `ReplacingMergeTree`，按业务键去重并保留最新版本。主要表分组：

- **术数常量表**：`five_elements`、`heavenly_stems`、`earthly_branches`、`trigrams`、`hexagrams`、`hexagram_explanations`、`solar_terms`、`sexagenary_cycle`、`fengshui_mountains`、`luoshu_palaces`、`twenty_eight_mansions`、`three_enclosures`、`historical_calendars`、`hetu_numerology`、`lunar_phase_regimes`、`branch_imagery`、`trigram_imagery`。
- **规则与验证**：`rule_definitions`（带生效区间）、`validation_cases`。
- **语料表**：`data_sources`、`knowledge_passages`、`corpus_documents`、`corpus_chunks`（带 ngram 倒排索引 `ngrambf_v1` 支持全文检索）、`corpus_ingestion_runs`。
- **业务/合规预留**：`user_inputs`（加密）、`geo_features`、`fengshui_properties`、`floorplan_features`、`fengshui_assessments`。

所有常量/规则/语料表均带 `source_id` 与 `rule_version` 字段，保证来源可追溯、版本可区分。

---

## 8. 规则与验证体系

- **规则注册表**：`data/rules/mvp-engineering-baseline.json`，当前 **89 条可追溯工程规则**（全部纳入 `rule_sets` 引用），状态均为 `draft`，待专家审核；每条规则独立编号（如 `YI-3NUM-INPUT-001`、`MH-THREE-NUMBER-001`），含来源引用、前置条件、输入、程序、输出、限制与责任人。
- **工程回归案例**：`data/validation-cases/mvp-engineering-baseline.json`，当前 **31 个案例全部通过**，代表工程基线而非专家签署案例。
- **校验链**：`POST /v1/validation-cases/run` 执行回归；`scripts/run_validation_cases.py` 命令行校验；`test_rule_registry.py` 校验注册表结构（必填字段、唯一性、引用完整性）。
- **治理目标**：规则发布需审核、绑定来源、案例回归；历史结果通过 `rule_version` 引用还原，即使规则下线也不失真。

---

## 9. 运行与部署

### 9.1 本地开发启动

```bash
# 1. 后端依赖（Conda base 环境）
conda activate base
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt

# 2. 启动 ClickHouse
docker-compose up -d clickhouse

# 3. 构建并导入语料
./scripts/load_corpus_clickhouse.sh

# 4. 内部只读语料 API（:8088）
./scripts/run_corpus_api.sh --port 8088

# 5. MVP 计算 API（:8090，交互文档 /docs）
./scripts/run_mvp_api.sh          # Windows: .\scripts\run_mvp_api.bat

# 6. Web 推演工作台（:5173）
cd frontend && npm install && cd ..
./scripts/run_web.sh              # Windows: .\scripts\run_web.bat
# 或开发模式一键：双击 start_dev.bat
```

### 9.2 构建与生产部署

```bash
# 统一构建：后端编译 + 测试 + 前端 build
./scripts/build_all.sh            # Windows: build_all.bat

# 单端口生产服务（前后端同服，:8090）
./scripts/start_all.sh            # Windows: start_all.bat

# 一键构建并部署
./scripts/deploy.sh
```

详细参数与安全要求见 [`docs/development/deployment.md`](./development/deployment.md)。

### 9.3 验证

```bash
python -m pytest backend/tests
./scripts/run_validation_cases.py
npm --prefix frontend run build
npm --prefix frontend run test:unit
npm --prefix frontend run test:node
npm --prefix frontend run test:browser
./scripts/verify_daorenjia_cache.py --report cache/daorenjia/verification.json
```

---

## 10. 测试体系

- **后端 pytest（30+ 文件）**：覆盖历法引擎、周易（含三数）、梅花领域、六爻领域、大六壬领域（含特殊传递）、八字、紫微、奇门、风水方向与测量共识、类象、解释、综合研判、定向推演、元会运世、规则注册表、语料构建/缓存、语料 API、MVP API 与系统边界、**工作流会话模型（不可变快照铁律/交互模块A-G/术数调度/会话存储）**。
- **前端 Playwright**：`frontend/tests/smoke.mjs` 浏览器冒烟。
- **数据完整性**：`scripts/check_database_full_integrity.py`、`verify_corpus_clickhouse.py` 校验语料装载完整性。
- **重构验证**：`scripts/verify_refactoring.py` 独立验证交互式工作流核心逻辑（10项断言）。

---

## 11. 文档导航

| 主题 | 文档 |
| --- | --- |
| 项目总计划 | [`docs/detailed-project-plan.md`](./detailed-project-plan.md)、[`docs/project-plan.md`](./project-plan.md) |
| 设计文档索引 | [`docs/design/README.md`](./design/README.md)（含 16 条 ADR 决策记录） |
| 产品与交互 | [`docs/design/product-design.md`](./design/product-design.md) |
| 系统架构 | [`docs/design/system-architecture.md`](./design/system-architecture.md) |
| 规则与数据设计 | [`docs/design/rule-and-data-design.md`](./design/rule-and-data-design.md) |
| 引擎算法与框架规范 | [`docs/development/engine-algorithms-and-framework.md`](./development/engine-algorithms-and-framework.md) |
| 计算服务说明 | [`docs/development/calculation-service.md`](./development/calculation-service.md) |
| 语料服务说明 | [`docs/development/corpus-service.md`](./development/corpus-service.md) |
| Web 界面说明 | [`docs/development/web-interface.md`](./development/web-interface.md) |
| 部署说明 | [`docs/development/deployment.md`](./development/deployment.md) |
| 语料分析报告 | [`docs/data/corpus-analysis.md`](./data/corpus-analysis.md)、[`docs/data/multi-source-corpus-analysis.md`](./data/multi-source-corpus-analysis.md) |
| 数据导入 | [`docs/data-ingestion.md`](./data-ingestion.md) |
| 来源状态 | [`docs/sources/daorenjia.md`](./sources/daorenjia.md)、[`docs/sources/wikisource.md`](./sources/wikisource.md) |
| 风水模块 | [`docs/fengshui-module.md`](./fengshui-module.md) |
| 交互式推演重构方案 | [`docs/refactoring-plan.md`](./refactoring-plan.md) |

---

## 12. 当前数据与状态基线

**语料数据**：

- 书目 1,524 本，可用正文 1,522 本。
- 无损文本块 26,681，字符 32,360,859。
- 道人家语料哈希：`7e654ac9338c6ed2f88bff5498266320b8aff46a32e475ea3b7c0c8b3bb47755`。
- Wikisource 开放语料哈希：`6b14084be64ffbc3c9f103b414d4361939f538590e713d1bb02e4c98347d2400`。
- ClickHouse 当前共 1,541 个文档、27,595 个文本块、33,466,721 字符。
- 使用范围：`internal_research`（内部研究，不得未经许可对外再发布）。

**计算基线**：

- 89 条可追溯工程规则，状态均为 `draft`，待专家审核。
- 31 个工程回归案例，当前全部通过（不代表专家签署案例）。
- 健康、常量、规则、案例、计算、典籍检索与风水档案接口持续增补，机器契约以 `/openapi.json` 为准。
- 多模块综合只比较引用已发布规则的结构化判断，不生成自动吉凶总分。
- 推演结果含确定性摘要和逐模块详细说明，每段可回溯规则编号。
- 输入事项可生成未审核的研究性结论、优先建议和核实清单，不替代正式专业意见。
- 结果可引用匹配卦象的书籍原文，明确展示书中观点、事项参考、来源链接和未审核状态。

---

## 13. 后续规划方向

- 解释、类象、元会运世纪元和专业风水规则按来源、版本与专家案例逐项审核。
- 面向 MVP 的业务层（身份权限、档案案例、报告分享、管理审计）按 [`docs/design/system-architecture.md`](./design/system-architecture.md) 落地。
- 规则发布工作流（in_review → approved → published）与更完整的案例回归门禁。
- 更多术数流派（school）版本化支持与多流派对照。

---

*本文档由代码与现有文档综合分析生成，作为仓库级框架说明；具体规则与数据口径以 `docs/` 下的专项文档为准。*
