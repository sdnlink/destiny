# 内部学习语料服务

## 1. 作用

该服务为天机演象开发阶段提供只读语料访问，支持统计、书目、分块和全文检索。顶层响应标记 `usage_scope: source_specific_policy`；每个文档和检索结果同时返回自身的 `source_id`、`usage_scope`、许可和署名URL。道人家文本仍只限内部研究，Wikisource文本按CC BY-SA 4.0处理。不得忽略逐来源许可而将接口整体直接暴露为公开古籍全文服务。

## 2. 构建与导入

```bash
./scripts/load_corpus_clickhouse.sh
```

该命令依次执行：

1. 验证原始缓存完整性。
2. 生成无损文档和文本块。
3. 创建ClickHouse表。
4. 导入文档、文本块和运行记录。
5. 对比文档数、块数、文档字符和块字符。

生成文件位于 `data/generated/corpus/`，已由 `.gitignore` 排除。

## 3. 启动服务

```bash
./scripts/run_corpus_api.sh --port 8088
```

默认只监听 `127.0.0.1`。如果绑定到非回环地址，必须设置访问令牌：

```bash
CORPUS_API_TOKEN='replace-with-secret' \
CORPUS_API_BIND='0.0.0.0' \
./scripts/run_corpus_api.sh
```

请求使用：

```text
Authorization: Bearer replace-with-secret
```

## 4. 接口

| 方法与路径 | 用途 |
| --- | --- |
| `GET /health` | ClickHouse连接和文档数 |
| `GET /v1/corpus/stats` | 总量、分类和最近导入运行 |
| `GET /v1/corpus/documents` | 书目分页和筛选 |
| `GET /v1/corpus/documents/{id}` | 单本文档元数据 |
| `GET /v1/corpus/documents/{id}/chunks` | 单本文本块分页 |
| `GET /v1/corpus/search` | 全文子串检索 |

### 4.1 书目筛选

```bash
curl --get \
  --data-urlencode 'category=c18' \
  --data-urlencode 'q=周易' \
  --data-urlencode 'limit=20' \
  http://127.0.0.1:8088/v1/corpus/documents
```

支持参数：`category`、`status`、`q`、`limit`和`offset`。

### 4.2 全文检索

```bash
curl --get \
  --data-urlencode 'q=阴阳五行' \
  --data-urlencode 'limit=20' \
  http://127.0.0.1:8088/v1/corpus/search
```

搜索词长度为2至100个字符，返回文档、文本块、块内匹配偏移、上下文片段、原始页面和内容哈希。当前检索是确定性子串检索，不包含向量召回和模型生成。

## 5. 环境变量

| 变量 | 默认值 |
| --- | --- |
| `CLICKHOUSE_URL` | `http://localhost:18123` |
| `CLICKHOUSE_USER` | `destiny` |
| `CLICKHOUSE_PASSWORD` | `destiny_local` |
| `CORPUS_API_BIND` | `127.0.0.1` |
| `CORPUS_API_PORT` | `8088` |
| `CORPUS_API_TOKEN` | 空；仅回环地址允许为空 |

本地默认密码只用于开发环境。共享环境必须使用密钥管理系统，不能将生产凭据提交到Git。

## 6. 数据边界

- 接口只读，不提供文本修改或规则发布。
- 服务不会调用外部AI、向量数据库或嵌入服务。
- 搜索结果是候选证据，不是已审核规则。
- 对外产品只能引用许可允许的片段和来源信息。
- 全文内容不进入日志、埋点或错误响应。
- 非回环绑定必须启用Bearer Token，并应由反向代理补充TLS和访问审计。

## 7. 后续开发

- 术语与实体词典。
- 专家段落标注和审核状态。
- 规则候选与原文引用关系。
- 授权范围内的混合关键词/向量检索。
- 检索评测集和召回质量指标。
- PostgreSQL业务身份和租户权限接入。
