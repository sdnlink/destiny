import { beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import ConsultModulePage from "../../src/pages/ConsultModulePage";
import { getLatestHistoryByScene, saveDeductionHistory } from "../../src/lib/storage";
import * as api from "../../src/lib/api";

vi.mock("../../src/components/result/ZhouyiView", () => ({
  ZhouyiView: ({ result }) => <div>周易结果：{result.rule_id}</div>,
}));
vi.mock("../../src/components/result/MeihuaView", () => ({ MeihuaView: () => <div>梅花</div> }));
vi.mock("../../src/components/result/LiuyaoView", () => ({ LiuyaoView: () => <div>六爻</div> }));
vi.mock("../../src/components/result/QimenView", () => ({ QimenView: () => <div>奇门</div> }));
vi.mock("../../src/components/result/LiurenView", () => ({ LiurenView: () => <div>六壬</div> }));

const RESTORED_RESULT = {
  module_results: [{ module: "zhouyi", result: { rule_id: "ZY-OLD" } }],
  advisory: {
    conclusion: { headline: "旧结论", text: "上次推演的结论" },
    recommendations: [],
  },
};

function renderZhouyi() {
  return render(
    <MemoryRouter>
      <ConsultModulePage moduleKey="zhouyi" />
    </MemoryRouter>
  );
}

describe("模块页刷新恢复上次推演结果", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("getLatestHistoryByScene 只取本场景、结构完整的记录", () => {
    saveDeductionHistory("t-meihua", { scene: "meihua", question: "梅花" }, RESTORED_RESULT);
    saveDeductionHistory("t-broken", { scene: "zhouyi", question: "残缺" }, { result: { rule_id: "X" } });
    expect(getLatestHistoryByScene("zhouyi")).toBeNull();

    saveDeductionHistory("t-zhouyi", { scene: "zhouyi", question: "周易事项" }, RESTORED_RESULT);
    expect(getLatestHistoryByScene("zhouyi")?.question).toBe("周易事项");
  });

  it("打开模块页自动恢复结果并显示提示，重新起卦后提示消失", async () => {
    saveDeductionHistory("t-restore", {
      scene: "zhouyi", question: "上次的问题", category: "career",
    }, RESTORED_RESULT);
    vi.spyOn(api, "compareCalculations").mockResolvedValue({
      module_results: [{ module: "zhouyi", result: { rule_id: "ZY-NEW" } }],
      advisory: RESTORED_RESULT.advisory,
    });

    renderZhouyi();

    expect(screen.getByText("周易结果：ZY-OLD")).toBeTruthy();
    expect(screen.getByText(/已恢复上次推演结果/)).toBeTruthy();
    expect(screen.getByText(/结合所问：上次的问题/)).toBeTruthy();

    fireEvent.click(screen.getByText("开始起卦"));
    await waitFor(() => expect(screen.getByText("周易结果：ZY-NEW")).toBeTruthy());
    expect(screen.queryByText(/已恢复上次推演结果/)).not.toBeTruthy();
  });

  it("恢复提示可手动关闭，且不影响结果展示", () => {
    saveDeductionHistory("t-close", { scene: "zhouyi", question: "问题" }, RESTORED_RESULT);
    renderZhouyi();

    fireEvent.click(screen.getByRole("button", { name: "关闭恢复提示" }));

    expect(screen.queryByText(/已恢复上次推演结果/)).not.toBeTruthy();
    expect(screen.getByText("周易结果：ZY-OLD")).toBeTruthy();
  });

  it("无本场景存档时保持空态", () => {
    saveDeductionHistory("t-other", { scene: "meihua", question: "别的体系" }, RESTORED_RESULT);
    renderZhouyi();

    expect(screen.queryByText(/已恢复上次推演结果/)).not.toBeTruthy();
    expect(screen.getByText(/尚未起周易卦/)).toBeTruthy();
  });
});
