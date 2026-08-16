# 天机演象

天机演象是传统术数数字化研究与辅助分析项目。当前已完成项目设计、双来源书籍语料与ClickHouse检索，以及历法、周易、梅花易数、六爻和大六壬的确定性工程计算内核。推演结果已增加事项相关类象候选和元会运世时间背景。解释、类象、元会运世纪元和专业风水规则仍须按来源、版本和专家案例逐项审核。

## 文档入口

- [详细项目计划](./docs/detailed-project-plan.md)
- [设计文档索引](./docs/design/README.md)
- [语料分析报告](./docs/data/corpus-analysis.md)
- [多来源术数知识库分析](./docs/data/multi-source-corpus-analysis.md)
- [语料服务说明](./docs/development/corpus-service.md)
- [MVP计算服务说明](./docs/development/calculation-service.md)
- [Web推演工作台说明](./docs/development/web-interface.md)
- [构建、启动与部署说明](./docs/development/deployment.md)
- [前后端仓库布局决策](./docs/design/decisions/003-frontend-backend-repository-layout.md)
- [数据导入说明](./docs/data-ingestion.md)

## 仓库结构

```text
backend/       Python 3.11+、FastAPI、领域计算内核和pytest测试
frontend/      React、Vite、Web界面和浏览器测试
clickhouse/    ClickHouse数据库结构
data/          前后端共享规则、案例和生成数据
scripts/       根级启动、采集和数据装载脚本
docs/          项目计划、设计决策和运行手册
```

前端只通过HTTP API访问后端。框架代码和依赖分别保存在`frontend/`与`backend/`，共享基础设施不归属任一界面框架。

## 本地启动

首次安装后端依赖：

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
.venv/bin/pip install -r backend/requirements-dev.txt
```

启动ClickHouse：

```bash
docker-compose up -d clickhouse
```

构建并导入全部语料：

```bash
./scripts/load_corpus_clickhouse.sh
```

启动内部只读语料API：

```bash
./scripts/run_corpus_api.sh --port 8088
```

启动MVP计算API：

```bash
./scripts/run_mvp_api.sh
```

计算API默认位于`http://127.0.0.1:8090`，交互文档位于`http://127.0.0.1:8090/docs`。

首次安装并启动Web推演工作台：

```bash
cd frontend
npm install
cd ..
./scripts/run_web.sh
```

Web界面默认位于`http://127.0.0.1:5173`，启动前需确保计算API正在运行。

## 统一构建与部署

统一编译后端、运行测试并构建前端：

```bash
./scripts/build_all.sh
```

启动编译后的前后端单端口服务：

```bash
./scripts/start_all.sh
```

一键构建并部署：

```bash
./scripts/deploy.sh
```

生产模式的Web界面和API均位于`http://127.0.0.1:8090`。完整参数和安全要求见[部署说明](./docs/development/deployment.md)。

验证：

```bash
.venv/bin/python -m pytest backend/tests
./scripts/run_validation_cases.py
npm --prefix frontend run build
npm --prefix frontend run test:browser
./scripts/verify_daorenjia_cache.py \
  --report cache/daorenjia/verification.json
```

## 当前数据

- 书目：1,524。
- 可用正文：1,522本。
- 无损文本块：26,681。
- 字符：32,360,859。
- 道人家语料哈希：`7e654ac9338c6ed2f88bff5498266320b8aff46a32e475ea3b7c0c8b3bb47755`。
- Wikisource开放语料哈希：`6b14084be64ffbc3c9f103b414d4361939f538590e713d1bb02e4c98347d2400`。
- ClickHouse当前共1,541个文档、27,595个文本块、33,466,721字符。
- 使用范围：`internal_research`。

## 当前计算基线

- 14条可追溯工程规则，状态均为`draft`，待专家审核。
- 7个工程回归案例，当前全部通过，不代表专家签署案例。
- 历法、周易和梅花共13个健康、常量、规则、案例及计算接口。
- 多模块综合只比较引用已发布规则的结构化判断，不生成自动吉凶总分。
- 推演结果包含确定性摘要和逐模块详细说明，每段可回溯规则编号。
- 输入事项可生成未审核的研究性结论、优先建议和核实清单，不替代正式专业意见。
- 结果可引用匹配卦象的书籍原文，明确展示书中观点、事项参考、来源链接和未审核状态。

语料不得未经许可对外再发布，也不能直接替代经过专家审核的术数规则和标准案例。
