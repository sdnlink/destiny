# 天机演象

天机演象是传统术数数字化研究与辅助分析项目。当前已完成项目设计、基础常量、道人家内部学习语料、ClickHouse导入和本地只读检索服务；周易、梅花易数、六壬和风水推演规则仍按专家审核与标准案例逐项开发。

## 文档入口

- [详细项目计划](./docs/detailed-project-plan.md)
- [设计文档索引](./docs/design/README.md)
- [语料分析报告](./docs/data/corpus-analysis.md)
- [语料服务说明](./docs/development/corpus-service.md)
- [数据导入说明](./docs/data-ingestion.md)

## 本地启动

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
./app/corpus_api.py --port 8088
```

验证：

```bash
python3 -m unittest discover -s tests -v
./scripts/verify_daorenjia_cache.py \
  --report cache/daorenjia/verification.json
```

## 当前数据

- 书目：1,524。
- 可用正文：1,522本。
- 无损文本块：26,681。
- 字符：32,360,859。
- 语料哈希：`7e654ac9338c6ed2f88bff5498266320b8aff46a32e475ea3b7c0c8b3bb47755`。
- 使用范围：`internal_research`。

语料不得未经许可对外再发布，也不能直接替代经过专家审核的术数规则和标准案例。
