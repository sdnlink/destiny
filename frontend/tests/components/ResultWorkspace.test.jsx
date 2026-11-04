import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ResultWorkspace from "../../src/components/ResultWorkspace";

const CONTEXT = { question: "该不该跳槽", category: "career", scene: "combined" };

describe("ResultWorkspace", () => {
  it("没有结果时渲染空工作区引导", () => {
    render(<ResultWorkspace result={null} context={null} activeTab="overview" setActiveTab={vi.fn()} />);

    expect(screen.getByText("从一次可复核的推演开始")).toBeInTheDocument();
    expect(screen.getByText("确定性计算")).toBeInTheDocument();
  });

  it("有结果时渲染任务标识、模块数量与全部结果标签页（冒烟）", () => {
    const result = {
      task_id: "task_demo",
      calculated_at: "2026-01-01T00:00:00Z",
      module_results: [],
    };

    render(<ResultWorkspace result={result} context={CONTEXT} activeTab="overview" setActiveTab={vi.fn()} />);

    // 任务头部与总览摘要各出现一次
    expect(screen.getAllByText("该不该跳槽")).toHaveLength(2);
    expect(screen.getByText("task_demo")).toBeInTheDocument();
    expect(screen.getByText("计算完成")).toBeInTheDocument();
    expect(screen.getByText("0 个模块")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /总览|周易|对照分析|结论建议/ })).toHaveLength(4);
  });

  it("点击结果标签页时回调目标 tab", () => {
    const setActiveTab = vi.fn();
    const result = { task_id: "task_demo", calculated_at: "2026-01-01T00:00:00Z", module_results: [] };

    render(
      <ResultWorkspace result={result} context={CONTEXT} activeTab="overview" setActiveTab={setActiveTab} />
    );

    fireEvent.click(screen.getByRole("button", { name: "对照分析" }));
    expect(setActiveTab).toHaveBeenCalledWith("comparison");
  });

  it("未运行的模块给出提示而不是崩溃", () => {
    const result = { task_id: "task_demo", calculated_at: "2026-01-01T00:00:00Z", module_results: [] };

    render(
      <ResultWorkspace result={result} context={CONTEXT} activeTab="meihua" setActiveTab={vi.fn()} />
    );

    expect(screen.getByText("本次未运行梅花易数")).toBeInTheDocument();
  });
});
