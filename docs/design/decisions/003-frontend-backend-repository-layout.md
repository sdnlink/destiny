# ADR-003：前后端仓库布局

> 状态：已采用
> 日期：2026-08-15

## 背景

项目最初只有Python计算和数据脚本，应用代码位于根目录`app/`。Web工作台加入后，根目录同时出现后端应用、前端应用、共享数据和基础设施配置，框架边界不清晰，启动脚本和测试也依赖隐式的根目录导入路径。

## 决策

采用单仓库、前后端独立应用结构：

```text
destiny/
├── backend/             # Python/FastAPI应用边界
│   ├── app/
│   ├── tests/
│   └── requirements.txt
├── frontend/            # React/Vite应用边界
│   ├── src/
│   ├── tests/
│   ├── package.json
│   └── vite.config.js
├── clickhouse/          # 共享分析数据库结构
├── data/                # 共享规则、案例和生成数据
├── scripts/             # 仓库级启动、采集和装载工具
└── docs/                # 跨应用设计和运行文档
```

边界规则：

- 后端可读取根目录受版本控制的`data/rules`和`data/validation-cases`，不读取前端源码。
- 前端只通过HTTP API读取计算、规则和案例数据，不直接读取Python模块、ClickHouse或根目录数据文件。
- 根级`scripts/`只负责跨目录编排和数据基础设施；框架内部代码分别留在`backend/`与`frontend/`。
- Python依赖固定在`backend/requirements.txt`，Node依赖固定在`frontend/package.json`和锁文件。
- 后端与前端测试分别位于各自目录。浏览器测试通过真实HTTP边界验证集成。
- 根级启动脚本解析绝对项目路径，因此可以从任意当前目录调用。

## 运行方式

开发环境使用两个独立进程：

```text
浏览器 → frontend:5173 → /api代理 → backend:8090
                                      └→ 共享规则与案例数据
```

语料只读API是后端内部服务，独立监听`8088`并访问ClickHouse。它不经过Web前端代理。

## 影响

- 原`app/`迁移为`backend/app/`，原`tests/`迁移为`backend/tests/`。
- 根级启动脚本保持稳定，外部使用者不需要记忆框架内部入口。
- 未来容器化时可分别为`backend/`和`frontend/`建立构建上下文，共享数据通过部署配置挂载或发布。
- 当前仍是单仓库，不代表前后端必须拆成两个Git仓库或独立发布周期。
