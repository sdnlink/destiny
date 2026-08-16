# 中文维基文库开放术数语料

> 来源：<https://zh.wikisource.org/>  
> API：<https://zh.wikisource.org/w/api.php>  
> 许可：Creative Commons Attribution-Share Alike 4.0  
> 使用范围：开放许可研究语料，引用和再利用必须保留署名及相同方式共享要求

## 采集边界

“互联网全部书籍”不是可穷尽、可验证的集合。本来源只采集 [开放书目清单](../../data/sources/wikisource-books.json) 中明确登记的17部核心典籍，不抓取许可不明网站、不绕过登录或访问控制，也不下载图片、PDF和扫描件。

书目覆盖周易经传、象数、梅花易数、六爻、大六壬、阳宅和堪舆。采集器读取站点官方 `rightsinfo`，只有许可URL与清单预期一致才继续。每个文档保存：

- 根页面、实际正文子页和页面修订号。
- 页面URL与历史URL，用于履行署名追溯。
- 提取方法、采集时间、字符数、字节数和SHA-256。
- 许可名称、许可URL、用途范围和领域分类。

## 完成状态

| 指标 | 数值 |
| --- | ---: |
| 登记书目 | 17 |
| 已缓存 | 17 |
| 失败 | 0 |
| 正文页面 | 272 |
| 字符 | 1,105,862 |
| UTF-8字节 | 3,154,481 |
| 无损文本块 | 914 |

语料哈希：`6b14084be64ffbc3c9f103b414d4361939f538590e713d1bb02e4c98347d2400`。

缓存位于 `cache/wikisource/`，生成数据位于 `data/generated/wikisource-corpus/`，两者均不提交Git。可复现命令：

```bash
./scripts/cache_wikisource_texts.py --delay 3.0
./scripts/build_wikisource_corpus.py
./scripts/load_corpus_clickhouse.sh
```

## 质量限制

- Wikisource整理文本不等同于权威校勘本。
- 原文、注释、目录和模板展开内容可能混合，正式规则引用前仍需逐页校核。
- 同一书名可能存在不同底本，本批清单只代表登记页面版本。
- 开放许可允许再利用不等于术数规则已经获得专家认可。

