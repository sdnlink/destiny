"""pytest 全局隔离配置。

`SessionStore` 默认把会话 JSON 写到仓库内的 `data/sessions/`，跑一次测试就会
在那里留下几十个文件，既污染工作区，也可能和开发者真实保存的推演记录混在一起。
这里在任何 `app` 模块被导入前把 `SESSION_STORAGE_DIR` 指向临时目录，
测试结束后自动清理。

如果显式设置了 `SESSION_STORAGE_DIR`（例如排查问题时想保留现场），这里不会覆盖。
"""

import atexit
import os
import shutil
import tempfile
from pathlib import Path


if "SESSION_STORAGE_DIR" not in os.environ:
    _session_dir = tempfile.mkdtemp(prefix="destiny-test-sessions-")
    os.environ["SESSION_STORAGE_DIR"] = _session_dir
    atexit.register(shutil.rmtree, _session_dir, True)

# 完整典籍语料（约 20MB）按仓库约定不入库；CI 上没有 data/generated/ 时，
# 测试改用 data/validation-cases/classics-fixture 的压缩原文片段，保证检索/
# 证据链仍被真实执行。完整语料的规模断言会在该目录存在时自动启用。
_ROOT = Path(__file__).resolve().parents[2]
_FULL_CORPUS = _ROOT / "data" / "generated" / "wikisource-corpus" / "corpus_chunks.jsonl"
_FIXTURE_CORPUS = _ROOT / "data" / "validation-cases" / "classics-fixture"
if (
    not _FULL_CORPUS.exists()
    and "CLASSICS_CORPUS_DIR" not in os.environ
    and (_FIXTURE_CORPUS / "corpus_chunks.jsonl").exists()
):
    os.environ["CLASSICS_CORPUS_DIR"] = str(_FIXTURE_CORPUS)
