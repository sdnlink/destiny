# Web推演工作台

> 状态：MVP前端可运行

## 1. 已实现范围

Web界面位于`frontend/`，使用React、Vite和Lucide图标，连接现有MVP计算API。首屏直接进入推演工作台，不包含营销落地页。

当前支持：

- 综合推演与 10 类单独模块场景（周易、梅花、六爻、大六壬、奇门、八字、紫微、风水方位等）。
- 事项分类、会话内问题摘要、IANA时区和可选真太阳时输入。
- 周易手工六爻、双数、三数与时间起卦。
- 梅花时间、双数与三数起卦。
- 六爻时间、双数、手工爻与铜钱起卦，并可指定用神焦点（自身 / 六亲 / 问事类别）。
- 计算前历法校验及四柱确认。
- 总览、历法、各术数模块结果页（含六爻典籍依据面板、八字大运/流年展示）及对照分析结果页。
- 命运专项工作区的本命盘、紫微斗数、逐年流年与生平时间轴四个独立页签；紫微结果内按起运年龄列出十二宫大限区间，标记当前年龄所在区间，点击可回看宫位。
- 卜筮专项工作区的周易、梅花易数与六爻三个独立页签，共用事项与时间基准。
- 时空盘专项工作区的奇门遁甲与大六壬两个独立页签，共用起盘时刻与时区。
- 独立工作区结果内提供“盘面 / 结论建议 / 历法”子页签；卜筮、时空盘、命运（含生平时间轴）、阳宅均提供 Markdown 报告导出（单模块结果由 `moduleReport.js` 按体系落笔）。
- 六爻用神焦点：请求带 `focus` 时在纳甲盘之外展示用神、原神、忌神、仇神与候选排序；下拉支持按事项或直接按六亲/世爻取用，未指定只排盘不取用神。
- 阳宅风水工作区的坐向测量（单次 / 多次共识）、八宅与玄空三个页签。
- 总览中的事项结论，以及独立“结论建议”页面。
- 本卦、变卦、互卦、错卦、综卦及动爻可视化。
- 体用和五行关系证据、规则编号、计算步骤及中间值。
- 历法、卦盘、动爻、体用、五行关系和综合状态的逐段说明。
- 结合询问类别和摘要生成的优先建议、核实问题、推演依据和决策边界。
- 与本卦、变卦匹配的书名、原文、书中观点、当前事项参考及来源链接。
- 规则目录和草稿状态提示。
- 桌面与移动端响应式布局。

问题摘要随统一计算请求发送，用于组织当前事项建议，但不进入起卦、历法或体用公式，也不持久化。未审核关系事实不转换为事项吉凶，多模块结果不生成自动评分。

计算说明直接展示后端返回的`explanation`，事项结论和建议直接展示`advisory`，前端不自行推断或改写。每段内容展示对应规则编号；限制和未审核状态在桌面与移动端均保持可见。

书籍区域直接展示`literature.books`。原文使用引用样式，书中观点与当前事项参考分栏显示，并保留文本块、哈希和来源链接。`automatic_candidate_unreviewed`状态和语料限制不得隐藏。

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

生产模式使用统一脚本构建，并由FastAPI在`8090`同源托管Web资源：

```bash
./scripts/build_all.sh
./scripts/start_all.sh
```

生产部署参数见[构建、启动与部署](./deployment.md)。

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
| `frontend/src/components/destiny/DestinyPanel.jsx` | 命运专项工作区（本命盘 / 紫微斗数 / 流年 / 生平时间轴） |
| `frontend/src/components/destiny/BirthProfileSection.jsx` | 命运专项共用出生信息表单 |
| `frontend/src/components/destiny/LiunianView.jsx` | 流年逐年事实表 |
| `frontend/src/components/fengshui/FengshuiPanel.jsx` | 阳宅风水工作区（坐向测量 / 八宅 / 玄空） |
| `frontend/src/components/consult/ConsultPanel.jsx` | 卜筮/时空盘共用工作区壳（共享事项、时间基准、结果子页签与导出） |
| `frontend/src/components/consult/DivinationPanel.jsx` | 卜筮专项页签（周易 / 梅花易数 / 六爻） |
| `frontend/src/components/consult/SpacetimePanel.jsx` | 时空盘专项页签（奇门遁甲 / 大六壬） |
| `frontend/src/components/workspace/WorkspaceShell.jsx` | 独立功能页共用的两栏外壳 |
| `frontend/src/components/result/FengshuiView.jsx` | 阳宅坐向、二十四山罗盘与测量共识 |
| `frontend/src/components/result/BazhaiView.jsx` | 八宅大游年盘、八方九星与宅命配法 |
| `frontend/src/components/result/XuankongView.jsx` | 玄空下卦挨星九宫、格局条件与替卦判定 |
| `frontend/src/components/InputPanel.jsx` | 推演输入与历法预校验 |
| `frontend/src/components/ResultWorkspace.jsx` | 全部结果视图和卦盘组件 |
| `frontend/src/lib/api.js` | API请求与错误归一化 |
| `frontend/src/lib/moduleReport.js` | 命运、阳宅等单体系结果的 Markdown 报告生成 |
| `frontend/src/lib/export.js` | 综合推演报告生成、文件下载与剪贴板复制 |
| `frontend/src/lib/formDefaults.js` | 经典推演与独立工作区共用的表单初值 |
| `frontend/src/styles.css` | 视觉系统和响应式规则 |
| `frontend/tests/smoke.mjs` | Chrome端到端冒烟测试 |

## 5. 当前限制

- 任务和问题摘要不持久化，只在当前请求及浏览器内存中使用，刷新后消失。
- 账号、设置同步与正式报告仍无后端实现；历史与案例已通过浏览器 localStorage 提供本地存档（最近 50 条），刷新后可恢复，但不跨设备同步。
- 当前API采用同步计算，界面没有异步排队和部分模块重试状态。
- 开发代理未传递生产环境令牌配置。部署到非回环网络前，需要统一身份认证、TLS、限流及安全响应头。
- 当前不提供规则发布操作，只读展示工程草稿。

这些限制必须在持久化任务与账号权限服务完成后再解除，不能仅在前端伪造本地历史记录作为正式案例档案。
