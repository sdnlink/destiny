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


if "SESSION_STORAGE_DIR" not in os.environ:
    _session_dir = tempfile.mkdtemp(prefix="destiny-test-sessions-")
    os.environ["SESSION_STORAGE_DIR"] = _session_dir
    atexit.register(shutil.rmtree, _session_dir, True)
