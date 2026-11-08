import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

vi.mock("../../src/lib/api.js", () => ({
  analyzeFengshuiDirection: vi.fn(),
  analyzeFengshuiMeasurements: vi.fn(),
}));

vi.mock("../../src/components/result/FengshuiView", () => ({
  FengshuiView: ({ result }) => <div data-testid="fengshui-view">{result.facts.mode}</div>,
}));

import { analyzeFengshuiDirection, analyzeFengshuiMeasurements } from "../../src/lib/api.js";
import FengshuiPanel from "../../src/components/fengshui/FengshuiPanel";

describe("FengshuiPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("单次分析提交向首角度、基准与误差", async () => {
    analyzeFengshuiDirection.mockResolvedValue({ facts: { mode: "single_direction" } });
    render(<FengshuiPanel />);

    fireEvent.click(screen.getByRole("button", { name: /生成阳宅坐向/ }));

    await waitFor(() => expect(analyzeFengshuiDirection).toHaveBeenCalledTimes(1));
    expect(analyzeFengshuiDirection).toHaveBeenCalledWith({
      facing_degree: 180,
      input_reference: "magnetic",
      magnetic_declination: 0,
      measurement_error: 1,
      measurement_method: "web_manual_entry",
    });
    expect(await screen.findByTestId("fengshui-view")).toHaveTextContent("single_direction");
  });

  it("多次共识按每条读数提交测量数组", async () => {
    analyzeFengshuiMeasurements.mockResolvedValue({ facts: { mode: "multiple_measurements" } });
    render(<FengshuiPanel />);

    fireEvent.click(screen.getByRole("button", { name: "多次共识" }));
    fireEvent.click(screen.getByRole("button", { name: /生成阳宅坐向/ }));

    await waitFor(() => expect(analyzeFengshuiMeasurements).toHaveBeenCalledTimes(1));
    expect(analyzeFengshuiMeasurements).toHaveBeenCalledWith({
      measurements: [
        { facing_degree: 179, input_reference: "magnetic", magnetic_declination: 0, measurement_error: 1, measurement_method: "web_multi_entry" },
        { facing_degree: 180, input_reference: "magnetic", magnetic_declination: 0, measurement_error: 1, measurement_method: "web_multi_entry" },
        { facing_degree: 181, input_reference: "magnetic", magnetic_declination: 0, measurement_error: 1, measurement_method: "web_multi_entry" },
      ],
    });
  });

  it("多次共识增加与删除读数时保持 3–12 次边界", async () => {
    render(<FengshuiPanel />);

    fireEvent.click(screen.getByRole("button", { name: "多次共识" }));
    fireEvent.click(screen.getByRole("button", { name: /增加读数/ }));
    expect(screen.getByLabelText("第4次向首读数")).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("删除第4次读数"));
    expect(screen.queryByLabelText("第4次向首读数")).not.toBeInTheDocument();
    expect(screen.getByLabelText("删除第1次读数")).toBeDisabled();
  });

  it("逐次读数为空时不发请求并提示", async () => {
    render(<FengshuiPanel />);

    fireEvent.click(screen.getByRole("button", { name: "多次共识" }));
    fireEvent.change(screen.getByLabelText("第1次向首读数"), { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: /生成阳宅坐向/ }));

    expect(analyzeFengshuiMeasurements).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent("有效数字");
  });
});
