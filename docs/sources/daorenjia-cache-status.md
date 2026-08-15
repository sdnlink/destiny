# 道人家文本缓存状态

> 最近更新：2026-08-15 16:49（Asia/Shanghai）
> 状态：可用文本缓存完成，完整性校验通过

## 当前进度

| 项目 | 数量 |
| --- | ---: |
| 已发现书目 | 1524 |
| 已缓存正文 | 1522 |
| 来源仅提供图片、无文本 | 2 |
| 已发现分卷入口 | 2534 |
| 已缓存分卷正文 | 2533 |
| 来源返回空文本的分卷 | 1 |
| 已验证字符 | 32,360,859 |
| 已验证字节 | 95,689,621 |
| 失败记录 | 0 |
| 待处理记录 | 0 |
| 校验错误 | 0 |
| 校验警告 | 0 |

缓存目录：`cache/daorenjia/`

- `texts/`：每本书的UTF-8纯文本。
- `metadata/`：URL、标题、字符数、抓取时间和SHA-256。
- `catalog.json`：去重后的1524本书目。
- `manifest.jsonl`：逐书状态清单。
- `summary.json`：最近一次运行汇总。
- `robots.txt`：采集时使用的站点访问规则快照。

缓存目录已加入 `.gitignore`，正文不提交到Git。

## 执行记录

主站曾在第267本开始出现读取超时，后改用网站移动前端公开使用的正文接口继续缓存。进一步检查发现部分长书的主记录仅包含分卷目录，因此采集器升级为同时读取 `apiscontent.php` 分卷接口。

按分卷规则处理过程中，来源曾多次连续超时。主站、移动站和API子域也曾在TLS握手阶段失败，采集器依靠断点、哈希校验和冷却重试继续完成。

采集器在连续5次失败后自动暂停，避免来源不可用时持续请求。最终在来源恢复后完成全部可用文本。

## 来源缺失项

网站没有为以下书籍提供文本正文，只返回“请看右上图片版”：

- `daozang25-1308`：《灵棋卜法》。
- `daozang9-293`：《云篆度人妙经》。

《弘道录》共发现25个分卷组，其中分卷ID `757`（卷四十五、四十八至五十，信·君臣之信）由官方接口返回空字符串；其余24个分卷组均已缓存。项目按照用户要求不下载图片，也不伪造缺失文本。

## 续传命令

持续运行直到完成：

```bash
./scripts/complete_daorenjia_cache.sh
```

来源连续失败时脚本默认冷却60秒再续传，可以通过 `CACHE_RETRY_COOLDOWN` 调整冷却时间，但不应降低请求间隔或使用高并发。

单次断点续传：

```bash
./scripts/cache_daorenjia_texts.py \
  --reuse-catalog \
  --source mobile-api \
  --delay 1.0 \
  --timeout 60 \
  --retries 3
```

该命令会校验并跳过已经按当前解析器版本成功缓存的文件，重试失败项并继续剩余书目。不要使用 `--force`，否则会重新下载全部成功文件。

移动站公开前端使用 `m.daorenjia.com/api/neirongapi.php?id=...` 获取书籍主记录，并使用 `apiscontent.php` 获取分卷正文。采集器仍按原始书籍URL保存来源，并在逐书元数据中记录实际接口和分卷编号。

离线重建状态清单：

```bash
./scripts/cache_daorenjia_texts.py --manifest-only
```

全量完整性校验：

```bash
./scripts/verify_daorenjia_cache.py \
  --report cache/daorenjia/verification.json
```

校验会检查目录唯一性、元数据状态、解析器版本、UTF-8、字符数、字节数、SHA-256、分卷编号、文件集合、仅图片书籍及官方接口为空的分卷记录。命令退出码为0且报告中 `complete: true` 才表示验收通过。

## 完成判定

部分书籍只提供图片版，正文接口返回“请看右上图片版”。项目不下载图片，因此这类书籍记录为 `text_unavailable`，不伪造文本。只有 `summary.json` 同时满足以下条件，才能标记可用文本缓存完成：

```text
cached_books + text_unavailable_books = 1524
failed_books = 0
pending_books = 0
interrupted = false
```

完成后还需要抽样检查标题、正文容器、空文本、异常短文本和校验值，不应只以文件数量作为验收依据。

本次最终 `summary.json` 满足全部完成条件，`verification.json` 返回 `complete: true`、`error_count: 0`、`warning_count: 0`。
