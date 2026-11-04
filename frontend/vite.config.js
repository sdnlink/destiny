import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    // 单包 389KB 全部前置下载：把第三方库单独切块，业务代码改动时这部分缓存不失效。
    // Vite 8（rolldown）只接受函数形式的 manualChunks。
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) return undefined;
          if (id.includes("lucide-react")) return "icons";
          if (id.includes("react")) return "react";
          return "vendor";
        },
      },
    },
    chunkSizeWarningLimit: 600,
  },
  // 组件渲染测试（vitest + jsdom）。只收 tests/components 下的 jsx 用例，
  // tests/*.test.mjs 是 node --test 的纯模块测试，由 npm run test:node 负责。
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.js"],
    include: ["tests/components/**/*.test.{js,jsx}"],
  },
  server: {
    port: 5173,
    strictPort: false,
    watch: {
      usePolling: true,
      interval: 500,
    },
    proxy: {
      "/api": {
        // 默认指向本地 8090；端口被占用或连远程后端时用 VITE_PROXY_TARGET 覆盖，
        // 不必再改这份配置（改配置会让每个开发者都要维护自己的本地副本）。
        target: process.env.VITE_PROXY_TARGET || "http://127.0.0.1:8090",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
