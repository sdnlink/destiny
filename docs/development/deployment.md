# 构建、启动与部署

> 适用范围：当前MVP单机部署

## 1. 脚本总览

| Linux/macOS 脚本 | Windows 脚本 (CMD / PowerShell) | 作用 |
| --- | --- | --- |
| `scripts/build_all.sh` | `scripts/build_all.bat` / `scripts/build_all.ps1` (根目录快捷: `build_all.bat`) | 在一个脚本中完成后端依赖、Python编译、后端测试、前端依赖和生产构建 |
| `scripts/start_all.sh` | `scripts/start_all.bat` / `scripts/start_all.ps1` (根目录快捷: `start_all.bat`) | 启动生产服务，由FastAPI同源提供API和已编译Web文件 |
| `scripts/deploy.sh` | `scripts/deploy.ps1` / `scripts/deploy.bat` | 一键执行统一构建并启动生产服务 |
| `scripts/start_dev.sh` | `scripts/start_dev.bat` / `scripts/start_dev.ps1` (根目录快捷: `start_dev.bat`) | 开发模式：一键同时启动后端API与前端Vite并打开浏览器 |
| `scripts/run_mvp_api.sh` | `scripts/run_mvp_api.bat` / `scripts/run_mvp_api.ps1` | 只启动FastAPI计算服务 |
| `scripts/run_web.sh` | `scripts/run_web.bat` / `scripts/run_web.ps1` | 只启动Vite开发服务 |
| `scripts/run_corpus_api.sh` | `scripts/run_corpus_api.bat` / `scripts/run_corpus_api.ps1` | 独立启动内部语料只读服务 |

所有脚本使用自身位置解析项目根目录，可以从任意当前工作目录调用。Windows 环境下支持直接双击根目录下的 `.bat` 批处理文件。

## 2. 统一构建

```bash
./scripts/build_all.sh
```

默认依次执行：

1. 检查 Python 3.11+（优先自动检测 Conda `base` 环境，支持 `CONDA_PREFIX`、`PYTHON_BIN`）和 `npm`。
2. 从 `backend/requirements.txt` 和 `backend/requirements-dev.txt` 安装固定版本 Python 依赖。
3. 安装前端依赖。
4. 编译 `backend/app` 和 `backend/tests` 中的 Python 文件。
5. 使用 pytest 运行全部后端测试。
6. 以同源 API 模式构建 React 前端到 `frontend/dist`。
7. 检查 `frontend/dist/index.html` 存在。

可用参数：

```bash
# 已安装依赖时跳过pip和npm ci
BUILD_INSTALL_DEPENDENCIES=0 ./scripts/build_all.sh

# 只编译和构建，不执行后端测试
BUILD_RUN_TESTS=0 ./scripts/build_all.sh
```

部署构建使用空的`VITE_API_ROOT`，浏览器直接请求当前来源的`/health`和`/v1/*`。开发构建未设置该变量时仍使用`/api`代理。

## 3. 生产启动

统一构建完成后：

```bash
./scripts/start_all.sh
```

默认监听`127.0.0.1:8090`，以下内容使用同一来源：

- Web界面：`http://127.0.0.1:8090/`
- 健康检查：`http://127.0.0.1:8090/health`
- OpenAPI：`http://127.0.0.1:8090/docs`
- 计算接口：`http://127.0.0.1:8090/v1/*`

修改端口：

```bash
APP_API_PORT=8091 ./scripts/start_all.sh
```

需要同时启动ClickHouse时：

```bash
START_CLICKHOUSE=1 ./scripts/start_all.sh
```

计算服务本身不依赖ClickHouse；只有语料服务和分析数据功能需要该数据库。

默认启用书籍观点，并在`8088`语料服务不可用时由`start_all.sh`自动启动。该子进程由启动脚本统一管理，退出主服务时一并关闭。相关参数：

```bash
# 完全关闭书籍检索
ENABLE_LITERATURE=0 ./scripts/start_all.sh

# 使用已由外部进程管理的语料服务，不自动启动本地进程
START_CORPUS_API=0 CORPUS_API_URL=http://127.0.0.1:8088 ./scripts/start_all.sh
```

若语料服务或ClickHouse不可用，计算仍会继续，`literature.status`返回`unavailable`并给出警告。

启动脚本会在以下情况立即失败并给出提示：

- Python 环境依赖缺失（未安装 uvicorn、fastapi 等）。
- `frontend/dist/index.html`不存在。
- 请求启动ClickHouse但系统没有Docker。
- 绑定非回环地址但没有配置`APP_API_TOKEN`。

## 4. 一键部署

```bash
./scripts/deploy.sh
```

该命令先执行`build_all.sh`，成功后以前台进程启动生产服务。进程收到`SIGINT`或`SIGTERM`时由Uvicorn正常关闭。

常见模式：

```bash
# 只生成部署产物，不启动
DEPLOY_START=0 ./scripts/deploy.sh

# 复用已经验证的构建产物并启动
DEPLOY_SKIP_BUILD=1 ./scripts/deploy.sh

# 跳过依赖安装和测试，复用本机环境后部署
BUILD_INSTALL_DEPENDENCIES=0 BUILD_RUN_TESTS=0 ./scripts/deploy.sh
```

`deploy.sh`不会在后台遗留未管理的PID，也不会自动覆盖操作系统服务配置。正式服务器应由systemd、容器编排或等价进程管理器调用`start_all.sh`。

## 5. 开发模式

一键启动（后端 `--reload` + 前端 Vite，退出时清理两个进程）：

```bash
./scripts/start_dev.sh        # Linux / macOS
.\scripts\start_dev.ps1       # Windows PowerShell
```

或分开启动两个终端：

```bash
# 终端一
./scripts/run_mvp_api.sh

# 终端二
./scripts/run_web.sh
```

此时Web位于`5173`，Vite把`/api`代理到`8090`，并提供热更新。不要使用Vite开发服务承担生产流量。

### 环境变量

| 变量 | 用途 | 缺省行为 |
| --- | --- | --- |
| `CLICKHOUSE_URL` / `CLICKHOUSE_USER` / `CLICKHOUSE_PASSWORD` | ClickHouse 连接 | 口令不再有代码内置默认值；缺失时记录警告，数据库相关接口按端点不同降级为 `unavailable` / `in_memory_fallback` / `file_cache`，并在响应的 `source` 字段标注来源 |
| `APP_API_TOKEN` | `/v1` 接口 Bearer 鉴权 | 未设置时启动即记录「仅本地开发可用」警告 |
| `SESSION_STORAGE_DIR` | 会话 JSON 目录 | 默认 `data/sessions` |

参考 `.env.example`。

## 6. 安全边界

当前Web界面没有登录和令牌输入能力。生产服务应继续监听`127.0.0.1`，由同机反向代理负责TLS、身份认证、访问控制和限流，再转发到`8090`。

设置`APP_API_TOKEN`后，鉴权覆盖`/v1/*`、`/docs`、`/openapi.json`和`/redoc`；`/health`探活与`SERVE_WEB=1`挂载的静态页面保持公开（浏览器无法携带Bearer头，整站401属于配置冲突，中间件已按此边界放行）。因此Token只保护数据与计算接口，页面本身仍需反向代理层面的访问控制。

不要把`APP_API_TOKEN`编译进前端，也不要为了直接公网监听而关闭非回环绑定保护。若部署在容器网络并必须监听`0.0.0.0`，应先完成统一身份认证设计，或由受保护的内部网络和反向代理注入服务端认证。

## 7. 部署验证

```bash
curl --fail http://127.0.0.1:8090/
curl --fail http://127.0.0.1:8090/health
WEB_BASE_URL=http://127.0.0.1:8090 npm --prefix frontend run test:browser
```

浏览器测试会实际提交计算并验证桌面、移动端、规则目录和控制台错误。部署失败时不得只检查首页200，还必须检查API和真实推演流程。
