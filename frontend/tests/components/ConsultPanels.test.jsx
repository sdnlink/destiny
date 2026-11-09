import { MemoryRouter } from "react-router-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import ConsultModulePage from "../../src/pages/ConsultModulePage";
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
vi.mock("../../src/components/result/ExplanationView", () => ({
  ExplanationView: ({ advisory }) => <div>结论视图：{advisory?.conclusion?.headline}</div>,
}));
vi.mock("../../src/components/result/CalendarView", () => ({
  CalendarView: () => <div>历法视图</div>,
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

function renderModule(key) {
  return render(
    <MemoryRouter>
      <ConsultModulePage moduleKey={key} />
    </MemoryRouter>
  );
}

describe("卜筮与时空盘独立模块页", () => {
  afterEach(() => vi.restoreAllMocks());

  it("周易模块页只提交 zhouyi 体系，并复用同一个事项上下文", async () => {
    const spy = vi.spyOn(api, "compareCalculations").mockResolvedValue(responseFor("zhouyi", "ZY-001"));
    renderModule("zhouyi");

    expect(screen.getByRole("heading", { name: "周易" })).toBeTruthy();
    fireEvent.click(screen.getByText("开始起卦"));

    await waitFor(() => expect(screen.getByText("周易结果：ZY-001")).toBeTruthy());
    const [calculations, context] = spy.mock.calls[0];
    expect(calculations.some((item) => item.module === "zhouyi")).toBe(true);
    expect(calculations.some((item) => item.module === "meihua")).toBe(false);
    expect(context).toEqual({ category: "career", question_summary: "近期事项推演" });
    expect(screen.getByText("先定边界再谈推进")).toBeTruthy();
  });

  it("六壬模块页提交 liuren 模块", async () => {
    const spy = vi.spyOn(api, "compareCalculations").mockResolvedValue(responseFor("liuren", "LR-001"));
    renderModule("liuren");

    fireEvent.click(screen.getByText("开始排盘"));

    await waitFor(() => expect(screen.getByText("六壬结果：LR-001")).toBeTruthy());
    const [calculations] = spy.mock.calls[0];
    expect(calculations.some((item) => item.module === "liuren")).toBe(true);
    expect(calculations.some((item) => item.module === "qimen")).toBe(false);
  });

  it("独立结果可切换盘面、结论建议与历法，并保留导出入口", async () => {
    vi.spyOn(api, "compareCalculations").mockResolvedValue({
      module_results: [
        { module: "zhouyi", result: { rule_id: "ZY-002" } },
        { module: "calendar", result: { input: { local_datetime: "2026-11-08T12:00" } } },
      ],
      advisory,
      explanation: { summary: "确定性说明" },
    });
    renderModule("zhouyi");

    fireEvent.click(screen.getByText("开始起卦"));
    await waitFor(() => expect(screen.getByText("周易结果：ZY-002")).toBeTruthy());

    expect(screen.getByRole("tab", { name: "盘面" })).toHaveAttribute("aria-selected", "true");
    fireEvent.click(screen.getByRole("tab", { name: "结论建议" }));
    expect(screen.getByText("结论视图：先定边界再谈推进")).toBeTruthy();

    fireEvent.click(screen.getByRole("tab", { name: "历法" }));
    expect(screen.getByText("历法视图")).toBeTruthy();
    expect(screen.getByRole("button", { name: /导出报告/ })).toBeTruthy();
  });
});
