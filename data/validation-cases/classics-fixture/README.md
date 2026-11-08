# 典籍检索压缩夹具

这是 `backend/tests/` 在**完整典籍语料不存在**时使用的 10 条原文片段，
只为让 CI 真实执行检索、简繁变体与证据链，不替代 20MB 的完整语料。

- 生成：`python scripts/build_classics_test_fixture.py`
- 内容：`corpus_documents.jsonl` / `corpus_chunks.jsonl`，每条文档一个段落。
- 来源：各条 `source_url` 指向原书公开页面，正文为可复核的短摘录。
- 完整语料存在时，`conftest.py` 不会启用本夹具；规模/来源清单断言仍跑真实语料。
- 本夹具不参与生产运行，只通过测试环境的 `CLASSICS_CORPUS_DIR` 生效。
