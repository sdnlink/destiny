# Frontend

天机演象Web工作台使用React和Vite，通过`/api`代理连接后端计算API。

## 目录

```text
frontend/
├── src/
│   ├── components/     # 输入和结果领域组件
│   ├── lib/            # API客户端
│   ├── App.jsx         # 应用状态与工作台外壳
│   └── styles.css      # 视觉系统和响应式规则
├── tests/              # Chrome浏览器冒烟测试
├── package.json
└── vite.config.js
```

```bash
npm install
npm run dev
npm run build
npm run test:browser
```

生产部署不运行Vite服务。`scripts/build_all.sh`使用同源API模式生成`frontend/dist`，随后由FastAPI静态托管：

```bash
./scripts/build_all.sh
./scripts/start_all.sh
```

完整运行说明见`docs/development/web-interface.md`。前端不得直接读取ClickHouse、语料文件或后端规则JSON，所有运行数据通过API获取。
