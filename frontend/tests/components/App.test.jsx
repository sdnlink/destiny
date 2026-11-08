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

import { checkHealth } from "../../src/lib/api.js";
import App from "../../src/App";

describe("App", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    checkHealth.mockResolvedValue({ status: "ok" });
  });

  it("启动后渲染导航、输入面板与空结果工作区（含懒加载）", async () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "推演参数" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "主导航" })).toBeInTheDocument();
    // ResultWorkspace 是 React.lazy，等待 Suspense 落地
    expect(await screen.findByText("从一次可复核的推演开始", {}, { timeout: 5000 })).toBeInTheDocument();
  });

  it("健康检查成功后显示服务在线状态", async () => {
    render(<App />);

    expect(await screen.findByText("计算服务在线")).toBeInTheDocument();
    expect(checkHealth).toHaveBeenCalledTimes(1);
  });

  it("切换到交互推演视图时懒加载 WorkflowPanel", async () => {
    render(<App />);

    fireEvent.click(screen.getByTitle("交互式推演工作流（7步标准化）"));

    expect(await screen.findByRole("heading", { name: "交互式推演工作台" })).toBeInTheDocument();
  });

  it("切换到命运专项视图时懒加载四个页签", async () => {
    render(<App />);

    fireEvent.click(screen.getByTitle("命运专项：本命盘、紫微斗数、流年与生平时间轴"));

    expect(await screen.findByRole("heading", { name: "命运专项" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /本命盘/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /紫微斗数/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /流年/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /生平时间轴/ })).toBeInTheDocument();
  });

  it("切换到卜筮专项视图时懒加载三个页签", async () => {
    render(<App />);

    fireEvent.click(screen.getByTitle("卜筮专项：周易、梅花易数与六爻"));

    expect(await screen.findByRole("heading", { name: "卜筮专项" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /周易/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /梅花易数/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /六爻/ })).toBeInTheDocument();
  });

  it("切换到时空盘专项视图时懒加载两个页签", async () => {
    render(<App />);

    fireEvent.click(screen.getByTitle("时空盘专项：奇门遁甲与大六壬"));

    expect(await screen.findByRole("heading", { name: "时空盘专项" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /奇门遁甲/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /大六壬/ })).toBeInTheDocument();
  });

  it("切换到阳宅风水视图时懒加载独立工作区", async () => {
    render(<App />);

    fireEvent.click(screen.getByTitle("阳宅风水：坐向、二十四山与多次测量共识"));

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
