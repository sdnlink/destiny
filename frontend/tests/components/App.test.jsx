import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

vi.mock("../../src/lib/api.js", () => ({
  checkHealth: vi.fn().mockResolvedValue({ status: "ok" }),
  loadRules: vi.fn().mockResolvedValue({ data: [] }),
  analyzeCalendar: vi.fn(),
  compareCalculations: vi.fn(),
  evaluateCalculation: vi.fn(),
  analyzeLiunian: vi.fn(),
  analyzeFengshuiDirection: vi.fn(),
  analyzeFengshuiMeasurements: vi.fn(),
}));

vi.mock("../../src/lib/sessionApi.js", () => ({
  createSession: vi.fn(),
  castSession: vi.fn(),
  getSession: vi.fn(),
  listSessions: vi.fn().mockResolvedValue([]),
  deleteSession: vi.fn(),
  realityCheck: vi.fn(),
  multiPartyAnalysis: vi.fn(),
  multiChoiceAnalysis: vi.fn(),
  reviewOutcome: vi.fn(),
  deepQuestion: vi.fn(),
  angleShift: vi.fn(),
  applyCompletion: vi.fn(),
}));

vi.mock("../../src/components/WorkflowPanel", () => ({
  default: ({ onRecovered }) => (
    <div>
      <h2>交互式推演工作台</h2>
      <button onClick={() => onRecovered?.()}>模拟恢复完成</button>
    </div>
  ),
}));
vi.mock("../../src/components/fengshui/FengshuiPanel", () => ({
  default: () => (
    <div>
      <h2>阳宅风水</h2>
      <button>生成阳宅坐向</button>
    </div>
  ),
}));

import { checkHealth } from "../../src/lib/api.js";
import App from "../../src/App";

describe("App", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    checkHealth.mockResolvedValue({ status: "ok" });
    // 每个用例都从首页开始，避免 BrowserRouter 沿用上个用例 pushState 后的 URL
    window.history.replaceState({}, "", "/");
  });

  it("启动后渲染主导航与首页引导（含各术数入口）", async () => {
    render(<App />);

    expect(screen.getByRole("navigation", { name: "主导航" })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "天机演象" })).toBeInTheDocument();
    // 导航按功能模块拆分，每个术数独立成链接
    expect(screen.getByRole("link", { name: "周易" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "梅花易数" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "六爻" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "八字命理" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "紫微斗数" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "奇门遁甲" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "大六壬" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "阳宅风水" })).toBeInTheDocument();
  });

  it("健康检查成功后显示服务在线状态", async () => {
    render(<App />);

    expect(await screen.findByText("计算服务在线")).toBeInTheDocument();
    expect(checkHealth).toHaveBeenCalledTimes(1);
  });

  it("导航到八字命理页面会渲染本命盘页签", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("link", { name: "八字命理" }));

    expect(await screen.findByRole("heading", { name: "八字命理" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /本命盘/ })).toBeInTheDocument();
  });

  it("导航到交互推演会懒加载 WorkflowPanel", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("link", { name: "交互推演" }));

    expect(await screen.findByRole("heading", { name: "交互式推演工作台" })).toBeInTheDocument();
  });

  it("恢复历史会话后仍留在 /workflow（onRecovered 只能清 state，不能导航离开）", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("link", { name: "交互推演" }));
    await screen.findByRole("heading", { name: "交互式推演工作台" });
    expect(window.location.pathname).toBe("/workflow");

    fireEvent.click(screen.getByRole("button", { name: "模拟恢复完成" }));

    expect(window.location.pathname).toBe("/workflow");
    expect(screen.getByRole("heading", { name: "交互式推演工作台" })).toBeInTheDocument();
  });

  it("导航到阳宅风水会懒加载独立工作区", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("link", { name: "阳宅风水" }));

    expect(await screen.findByRole("heading", { name: "阳宅风水" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /生成阳宅坐向/ })).toBeInTheDocument();
  });

  it("打开历史与案例抽屉时渲染提示区（图标导入缺失会整块白屏）", async () => {
    render(<App />);

    fireEvent.click(screen.getByTitle("历史推演记录、案例库与 JSON 备份导入导出"));

    expect(
      await screen.findByText(/本地保存最近 50 次推演记录/)
    ).toBeInTheDocument();
  });
});
