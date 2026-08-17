# Backend

天机演象后端使用 Python 3.11+（支持 Conda `base` 环境）、FastAPI 和确定性计算内核。

## 目录

```text
backend/
├── app/
│   ├── main.py          # MVP计算API
│   ├── corpus_api.py    # 内部语料只读API
│   └── core/            # 历法、周易、梅花、六爻、大六壬、风水、规则和综合内核
├── tests/               # Python单元、回归和API测试
└── requirements.txt     # 固定版本依赖
```

所有命令从仓库根目录执行：

```bash
# 激活 Conda base 环境并安装依赖
conda activate base
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt

# 启动计算API或运行测试
./scripts/run_mvp_api.sh
python -m pytest backend/tests
```

统一生产构建和启动：

```bash
./scripts/build_all.sh
./scripts/start_all.sh
```

`backend/app/core/registry.py`会读取根目录`data/`中的共享规则和案例。后端不得反向依赖`frontend/`源码。
