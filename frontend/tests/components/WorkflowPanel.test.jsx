import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// 会话 API 全部打桩：工作流面板只在用户操作时才发请求，这里只需保证不会真的访问网络
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

import { createSession } from "../../src/lib/sessionApi.js";
import WorkflowPanel from "../../src/components/WorkflowPanel";

describe("WorkflowPanel", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("挂载后渲染创建阶段表单（冒烟）", () => {
    render(<WorkflowPanel />);

    expect(screen.getByRole("heading", { name: "交互式推演工作台" })).toBeInTheDocument();
    expect(
      screen.getByText("7步标准化排盘推理 · 盘面永久不可变 · 多轮交互深化解读")
    ).toBeInTheDocument();
    expect(screen.getByText("求测事由 *")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/请描述你想求测的事项/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /创建推演会话/ })).toBeInTheDocument();
  });

  it("事由为空时点击创建给出本地校验错误，不调用接口", () => {
    render(<WorkflowPanel />);

    fireEvent.click(screen.getByRole("button", { name: /创建推演会话/ }));

    expect(screen.getByText("请输入求测事由")).toBeInTheDocument();
    expect(createSession).not.toHaveBeenCalled();
  });

  it("填写事由后创建会话并进入信息补全阶段", async () => {
    createSession.mockResolvedValue({ session_id: "sess_demo", info_completion: { ready: true } });

    render(<WorkflowPanel />);
    fireEvent.change(screen.getByPlaceholderText(/请描述你想求测的事项/), {
      target: { value: "这笔合作能否落地" },
    });
    fireEvent.click(screen.getByRole("button", { name: /创建推演会话/ }));

    expect(await screen.findByText("信息已充足，可直接起盘。")).toBeInTheDocument();
    expect(screen.getByText("会话ID：sess_demo")).toBeInTheDocument();
    expect(createSession).toHaveBeenCalledTimes(1);
    expect(createSession.mock.calls[0][0]).toMatchObject({
      question: "这笔合作能否落地",
      category: "career",
      system: "auto",
    });
  });
});
