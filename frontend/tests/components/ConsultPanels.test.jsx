import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import DivinationPanel from "../../src/components/consult/DivinationPanel";
import SpacetimePanel from "../../src/components/consult/SpacetimePanel";
import * as api from "../../src/lib/api";

vi.mock("../../src/components/result/ZhouyiView", () => ({
  ZhouyiView: ({ result }) => <div>周易结果：{result.rule_id}</div>,
}));
vi.mock("../../src/components/result/MeihuaView", () => ({
  MeihuaView: ({ result }) => <div>梅花结果：{result.rule_id}</div>,
}));
vi.mock("../../src/components/result/LiuyaoView", () => ({
  LiuyaoView: ({ result }) => <div>六爻结果：{result.rule_id}</div>,
}));
vi.mock("../../src/components/result/QimenView", () => ({
  QimenView: ({ result }) => <div>奇门结果：{result.rule_id}</div>,
}));
vi.mock("../../src/components/result/LiurenView", () => ({
  LiurenView: ({ result }) => <div>六壬结果：{result.rule_id}</div>,
}));

const advisory = {
  conclusion: { headline: "先定边界再谈推进", text: "盘面事实与所问事项分开陈述。" },
  recommendations: [],
};

function responseFor(module, ruleId) {
  return {
    module_results: [{ module, result: { rule_id: ruleId } }],
    advisory,
  };
}

describe("卜筮与时空盘独立工作区", () => {
  afterEach(() => vi.restoreAllMocks());

  it("卜筮专项只提交当前页签体系，并复用同一个事项上下文", async () => {
    const spy = vi.spyOn(api, "compareCalculations").mockResolvedValue(responseFor("zhouyi", "ZY-001"));
    render(<DivinationPanel />);

    expect(screen.getByRole("heading", { name: "卜筮专项" })).toBeTruthy();
    fireEvent.click(screen.getByText("开始起卦"));

    await waitFor(() => expect(screen.getByText("周易结果：ZY-001")).toBeTruthy());
    const [calculations, context] = spy.mock.calls[0];
    expect(calculations.some((item) => item.module === "zhouyi")).toBe(true);
    expect(calculations.some((item) => item.module === "meihua")).toBe(false);
    expect(context).toEqual({ category: "career", question_summary: "近期事项推演" });
    expect(screen.getByText("先定边界再谈推进")).toBeTruthy();
  });

  it("时空盘专项切换到六壬页签后提交 liuren 模块", async () => {
    const spy = vi.spyOn(api, "compareCalculations").mockResolvedValue(responseFor("liuren", "LR-001"));
    render(<SpacetimePanel />);

    fireEvent.click(screen.getByRole("tab", { name: /大六壬/ }));
    fireEvent.click(screen.getByText("开始排盘"));

    await waitFor(() => expect(screen.getByText("六壬结果：LR-001")).toBeTruthy());
    const [calculations] = spy.mock.calls[0];
    expect(calculations.some((item) => item.module === "liuren")).toBe(true);
    expect(calculations.some((item) => item.module === "qimen")).toBe(false);
  });
});
