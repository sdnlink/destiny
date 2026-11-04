"""后台回归运行器 v2：流式写入 pytest 输出，定位挂起测试。"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

OUT = Path(r"e:/code/destiny/data/generated/last_regression.txt")
OUT.parent.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with OUT.open("w", encoding="utf-8") as handle:
    handle.write(f"started {stamp}\n")
    handle.flush()
    proc = subprocess.run(
        [sys.executable, "-u", "-X", "utf8", "-m", "pytest", "backend/tests", "-v",
         "--tb=line", "-p", "no:cacheprovider", "-q"],
        cwd=r"e:/code/destiny", stdout=handle, stderr=subprocess.STDOUT,
        timeout=1200,
    )
    handle.write(f"\nexit={proc.returncode}\n")
print("done", proc.returncode)
