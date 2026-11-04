import sys
sys.path.insert(0, "backend")
from app.common.classics import get_library

lib = get_library()
for query in ["用神多現", "伏神", "三合局", "元神", "忌神", "大游年", "四化", "替卦", "旺相"]:
    print("##", query)
    for p in lib.search(query, limit=3):
        print(" -", p["title"], p["chunk_index"], repr(p["excerpt"][:160]))
