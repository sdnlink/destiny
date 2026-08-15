# 构建、启动与部署

> 适用范围：当前MVP单机部署

## 1. 脚本总览

| 脚本 | 作用 |
| --- | --- |
| `scripts/build_all.sh` | 在一个脚本中完成后端依赖、Python编译、后端测试、前端依赖和生产构建 |
| `scripts/start_all.sh` | 启动生产服务，由FastAPI同源提供API和已编译Web文件 |
| `scripts/deploy.sh` | 一键执行统一构建并启动生产服务 |
| `scripts/run_mvp_api.sh` | 只启动FastAPI计算服务 |
| `scripts/run_web.sh` | 只启动Vite开发服务 |
| `scripts/run_corpus_api.sh` | 独立启动内部语料只读服务 |

所有脚本使用自身位置解析项目根目录，可以从任意当前工作目录调用。

## 2. 统一构建

```bash
./scripts/build_all.sh
```

默认依次执行：

1. 检查`python3`和`npm`。
2. 不存在时创建根目录`.venv`。
3. 从`backend/requirements.txt`安装固定版本Python依赖。
4. 使用`npm ci`按锁文件安装前端依赖。
5. 编译`backend/app`和`backend/tests`中的Python文件。
6. 运行全部后端测试。
7. 以同源API模式构建React前端到`frontend/dist`。
8. 检查`frontend/dist/index.html`存在。

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

启动脚本会在以下情况立即失败并给出提示：

- `.venv/bin/uvicorn`不存在。
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

开发时使用两个终端：

```bash
# 终端一
./scripts/run_mvp_api.sh

# 终端二
./scripts/run_web.sh
```

此时Web位于`5173`，Vite把`/api`代理到`8090`，并提供热更新。不要使用Vite开发服务承担生产流量。

## 6. 安全边界

当前Web界面没有登录和令牌输入能力。生产服务应继续监听`127.0.0.1`，由同机反向代理负责TLS、身份认证、访问控制和限流，再转发到`8090`。

不要把`APP_API_TOKEN`编译进前端，也不要为了直接公网监听而关闭非回环绑定保护。若部署在容器网络并必须监听`0.0.0.0`，应先完成统一身份认证设计，或由受保护的内部网络和反向代理注入服务端认证。

## 7. 部署验证

```bash
curl --fail http://127.0.0.1:8090/
curl --fail http://127.0.0.1:8090/health
WEB_BASE_URL=http://127.0.0.1:8090 npm --prefix frontend run test:browser
```

浏览器测试会实际提交计算并验证桌面、移动端、规则目录和控制台错误。部署失败时不得只检查首页200，还必须检查API和真实推演流程。
