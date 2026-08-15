# Web推演工作台

> 状态：MVP前端可运行

## 1. 已实现范围

Web界面位于`frontend/`，使用React、Vite和Lucide图标，连接现有MVP计算API。首屏直接进入推演工作台，不包含营销落地页。

当前支持：

- 综合推演、单独周易和单独梅花易数三种场景。
- 事项分类、会话内问题摘要、IANA时区和可选真太阳时输入。
- 周易手工六爻与双数起卦。
- 梅花时间起卦与双数起卦。
- 计算前历法校验及四柱确认。
- 总览、历法、周易、梅花易数和对照分析结果页。
- 本卦、变卦、互卦、错卦、综卦及动爻可视化。
- 体用和五行关系证据、规则编号、计算步骤及中间值。
- 规则目录和草稿状态提示。
- 桌面与移动端响应式布局。

界面遵守当前计算边界：问题摘要不发送给算法，未审核关系事实不转换为事项吉凶，多模块结果不生成自动评分。

## 2. 本地启动

先启动计算API：

```bash
./scripts/run_mvp_api.sh
```

首次安装前端依赖：

```bash
cd frontend
npm install
```

从项目根目录启动Web界面：

```bash
./scripts/run_web.sh
```

默认地址为`http://127.0.0.1:5173`。Vite将`/api`代理到`http://127.0.0.1:8090`，浏览器不会产生跨域请求。可通过`VITE_API_ROOT`在构建时指定其他API根路径。

## 3. 构建与验证

```bash
cd frontend
npm run build
npm run test:browser
```

浏览器冒烟测试使用本机Google Chrome，执行以下流程：

1. 加载桌面输入界面并检查横向溢出。
2. 提交真实综合计算。
3. 切换周易、梅花易数结果页。
4. 打开并读取规则目录。
5. 在390像素宽移动视口重新计算和检查盘面。
6. 检查浏览器控制台错误。

测试截图写入`/tmp/tianji-input-desktop.png`、`/tmp/tianji-result-desktop.png`和`/tmp/tianji-result-mobile.png`，不进入Git。

## 4. 目录

| 路径 | 内容 |
| --- | --- |
| `frontend/src/App.jsx` | 应用状态、计算请求、导航和规则抽屉 |
| `frontend/src/components/InputPanel.jsx` | 推演输入与历法预校验 |
| `frontend/src/components/ResultWorkspace.jsx` | 全部结果视图和卦盘组件 |
| `frontend/src/lib/api.js` | API请求与错误归一化 |
| `frontend/src/styles.css` | 视觉系统和响应式规则 |
| `frontend/tests/smoke.mjs` | Chrome端到端冒烟测试 |

## 5. 当前限制

- 任务和问题摘要只保存在当前浏览器内存，刷新后消失。
- 案例库、历史任务、用户设置、账号和报告尚无后端实现，因此入口显示为待建设且不可操作。
- 当前API采用同步计算，界面没有异步排队和部分模块重试状态。
- 开发代理未传递生产环境令牌配置。部署到非回环网络前，需要统一身份认证、TLS、限流及安全响应头。
- 当前不提供规则发布操作，只读展示工程草稿。

这些限制必须在持久化任务与账号权限服务完成后再解除，不能仅在前端伪造本地历史记录作为正式案例档案。
