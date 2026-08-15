# 道人家文本缓存状态

> 最近更新：2026-08-15 13:42（Asia/Shanghai）  
> 状态：正在通过官方移动接口补充多卷书籍正文

## 当前进度

| 项目 | 数量 |
| --- | ---: |
| 发现书目 | 1524 |
| 已缓存正文 | 266 |
| 当前失败记录 | 5 |
| 待下载 | 1253 |
| 已缓存字符 | 2,389,442 |
| 已缓存字节 | 7,083,190 |

缓存目录：`cache/daorenjia/`

- `texts/`：每本书的UTF-8纯文本。
- `metadata/`：URL、标题、字符数、抓取时间和SHA-256。
- `catalog.json`：去重后的1524本书目。
- `manifest.jsonl`：逐书状态清单。
- `summary.json`：最近一次运行汇总。
- `robots.txt`：采集时使用的站点访问规则快照。

缓存目录已加入 `.gitignore`，正文不提交到Git。

## 中断原因

第267本开始出现读取超时，随后该域名的HTTPS连接持续在握手阶段失败，HTTP连接也返回空响应。短时恢复探测和一次断点续传均未成功。

采集器在连续5次失败后自动暂停，避免来源不可用时持续请求。当前失败不代表对应书籍不存在，需要在站点连接恢复后重新获取。

## 续传命令

```bash
./scripts/cache_daorenjia_texts.py \
  --reuse-catalog \
  --delay 1.0 \
  --timeout 60 \
  --retries 3
```

该命令会校验并跳过已经成功缓存的266本，重试失败项并继续剩余书目。不要使用 `--force`，否则会重新下载全部成功文件。

主站不可用但官方移动接口可用时：

```bash
./scripts/cache_daorenjia_texts.py \
  --reuse-catalog \
  --source mobile-api \
  --delay 1.0 \
  --timeout 60 \
  --retries 3
```

移动站公开前端使用 `m.daorenjia.com/api/neirongapi.php?id=...` 获取书籍正文。采集器仍按原始书籍URL保存来源，并在逐书元数据的 `fetched_from` 中记录实际接口地址。

离线重建状态清单：

```bash
./scripts/cache_daorenjia_texts.py --manifest-only
```

## 完成判定

部分书籍只提供图片版，正文接口返回“请看右上图片版”。项目不下载图片，因此这类书籍记录为 `text_unavailable`，不伪造文本。只有 `summary.json` 同时满足以下条件，才能标记可用文本缓存完成：

```text
cached_books + text_unavailable_books = 1524
failed_books = 0
pending_books = 0
interrupted = false
```

完成后还需要抽样检查标题、正文容器、空文本、异常短文本和校验值，不应只以文件数量作为验收依据。
