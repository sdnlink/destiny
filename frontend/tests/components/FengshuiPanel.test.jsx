import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

vi.mock("../../src/lib/api.js", () => ({
  analyzeFengshuiDirection: vi.fn(),
  analyzeFengshuiMeasurements: vi.fn(),
  analyzeFengshuiBazhai: vi.fn(),
  analyzeFengshuiXuankong: vi.fn(),
  listFengshuiBuildings: vi.fn(),
  saveFengshuiBuilding: vi.fn(),
  deleteFengshuiBuilding: vi.fn(),
}));

vi.mock("../../src/components/result/FengshuiView", () => ({
  FengshuiView: ({ result }) => <div data-testid="fengshui-view">{result.facts.mode}</div>,
}));

vi.mock("../../src/components/result/BazhaiView", () => ({
  BazhaiView: ({ result }) => <div data-testid="bazhai-view">{result.facts.house_group}</div>,
}));

vi.mock("../../src/components/result/XuankongView", () => ({
  XuankongView: ({ result }) => <div data-testid="xuankong-view">{result.facts.period_label}</div>,
}));

import {
  analyzeFengshuiBazhai,
  analyzeFengshuiDirection,
  analyzeFengshuiMeasurements,
  analyzeFengshuiXuankong,
  listFengshuiBuildings,
  saveFengshuiBuilding,
} from "../../src/lib/api.js";
import { MemoryRouter, useLocation } from "react-router-dom";
import FengshuiPanel from "../../src/components/fengshui/FengshuiPanel";

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{location.search}</div>;
}

function renderPage(ui, initialEntries = ["/"]) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      {ui}
      <LocationProbe />
    </MemoryRouter>
  );
}

describe("FengshuiPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("URL 中的 tool 参数决定初始子工具，切换后同步地址栏", () => {
    listFengshuiBuildings.mockResolvedValue([]);
    renderPage(<FengshuiPanel />, ["/fengshui?tool=bazhai"]);

    expect(screen.getByRole("tab", { name: /八宅/ })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByTestId("location").textContent).toContain("tool=bazhai");

    fireEvent.click(screen.getByRole("tab", { name: /坐向测量/ }));
    expect(screen.getByTestId("location").textContent).toBe("");
  });

  it("单次分析提交向首角度、基准与误差", async () => {
    analyzeFengshuiDirection.mockResolvedValue({ facts: { mode: "single_direction" } });
    renderPage(<FengshuiPanel />);

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
    renderPage(<FengshuiPanel />);

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
    renderPage(<FengshuiPanel />);

    fireEvent.click(screen.getByRole("button", { name: "多次共识" }));
    fireEvent.click(screen.getByRole("button", { name: /增加读数/ }));
    expect(screen.getByLabelText("第4次向首读数")).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("删除第4次读数"));
    expect(screen.queryByLabelText("第4次向首读数")).not.toBeInTheDocument();
    expect(screen.getByLabelText("删除第1次读数")).toBeDisabled();
  });

  it("逐次读数为空时不发请求并提示", async () => {
    renderPage(<FengshuiPanel />);

    fireEvent.click(screen.getByRole("button", { name: "多次共识" }));
    fireEvent.change(screen.getByLabelText("第1次向首读数"), { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: /生成阳宅坐向/ }));

    expect(analyzeFengshuiMeasurements).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent("有效数字");
  });

  it("八宅按坐山与宅命信息提交", async () => {
    analyzeFengshuiBazhai.mockResolvedValue({ facts: { house_group: "东四宅" } });
    renderPage(<FengshuiPanel />);

    fireEvent.click(screen.getByRole("tab", { name: "八宅" }));
    fireEvent.click(screen.getByRole("button", { name: /排八宅盘/ }));

    await waitFor(() => expect(analyzeFengshuiBazhai).toHaveBeenCalledTimes(1));
    expect(analyzeFengshuiBazhai).toHaveBeenCalledWith({
      sitting_mountain: "子",
      gender: "男",
      birth_year: 1984,
    });
    expect(await screen.findByTestId("bazhai-view")).toHaveTextContent("东四宅");
  });

  it("八宅出生年份越界时不发请求并提示", async () => {
    renderPage(<FengshuiPanel />);

    fireEvent.click(screen.getByRole("tab", { name: "八宅" }));
    fireEvent.change(screen.getByLabelText("出生年份（选填）"), { target: { value: "1800" } });
    fireEvent.click(screen.getByRole("button", { name: /排八宅盘/ }));

    expect(analyzeFengshuiBazhai).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent("1864–2100");
  });

  it("玄空按坐山、运与年份提交", async () => {
    analyzeFengshuiXuankong.mockResolvedValue({ facts: { period_label: "下元9运" } });
    renderPage(<FengshuiPanel />);

    fireEvent.click(screen.getByRole("tab", { name: "玄空" }));
    fireEvent.click(screen.getByRole("button", { name: /排玄空盘/ }));

    await waitFor(() => expect(analyzeFengshuiXuankong).toHaveBeenCalledTimes(1));
    expect(analyzeFengshuiXuankong).toHaveBeenCalledWith({
      sitting_mountain: "子",
      include_tihua_reference: false,
      include_tihua_chart: false,
      year: 2026,
    });
    expect(await screen.findByTestId("xuankong-view")).toHaveTextContent("下元9运");
  });

  it("房屋档案页签读取已存档案", async () => {
    listFengshuiBuildings.mockResolvedValue([
      {
        building_id: "building-1",
        updated_at: "2026-11-08T08:00:00Z",
        profile: { name: "自宅 · 主卧", measurements: [{ facing_degree: 180 }], note: "三层" },
      },
    ]);
    renderPage(<FengshuiPanel />);

    fireEvent.click(screen.getByRole("tab", { name: "房屋档案" }));

    await waitFor(() => expect(listFengshuiBuildings).toHaveBeenCalledWith("local"));
    expect(await screen.findByText("自宅 · 主卧")).toBeInTheDocument();
    expect(screen.getByText(/building-1 · 1 次读数/)).toBeInTheDocument();
  });

  it("保存档案须先勾选知情同意并提交当前坐向", async () => {
    listFengshuiBuildings.mockResolvedValue([]);
    saveFengshuiBuilding.mockResolvedValue({ building_id: "building-new" });
    renderPage(<FengshuiPanel />);

    fireEvent.click(screen.getByRole("tab", { name: "房屋档案" }));
    await waitFor(() => expect(listFengshuiBuildings).toHaveBeenCalled());
    fireEvent.change(screen.getByLabelText("档案名称"), { target: { value: "自宅" } });
    fireEvent.click(screen.getByRole("button", { name: "保存档案" }));

    expect(saveFengshuiBuilding).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent("知情同意");

    fireEvent.click(screen.getByLabelText("已取得屋主知情同意"));
    fireEvent.click(screen.getByRole("button", { name: "保存档案" }));

    await waitFor(() => expect(saveFengshuiBuilding).toHaveBeenCalledTimes(1));
    expect(saveFengshuiBuilding).toHaveBeenCalledWith(expect.objectContaining({
      tenantId: "local",
      buildingId: expect.any(String),
      profile: expect.objectContaining({
        name: "自宅",
        owner_consent: true,
        measurements: [expect.objectContaining({ facing_degree: 180 })],
      }),
    }));
  });
});
