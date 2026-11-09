import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import BaziPage from "../../src/pages/BaziPage";
import ZiweiPage from "../../src/pages/ZiweiPage";
import * as api from "../../src/lib/api";

vi.mock("../../src/components/result/BaziView", () => ({
  BaziView: ({ result }) => <div>本命盘结果：{result.rule_id}</div>,
}));
vi.mock("../../src/components/result/LifelineView", () => ({
  LifelineView: ({ result }) => <div>时间轴入参：{result.input.local_datetime}</div>,
}));
vi.mock("../../src/components/result/ZiweiView", () => ({
  ZiweiView: ({ result }) => <div>紫微结果：{result.rule_id}</div>,
}));
vi.mock("../../src/components/destiny/LiunianView", () => ({
  LiunianView: ({ data, result }) => {
    const d = data || result;
    return (
      <div>
        <span>流年结果：</span>
        <span>{d.rule_id}</span>
        <span>{d.years?.[0]?.year}</span>
      </div>
    );
  },
}));

function fillBirthProfile() {
  fireEvent.change(screen.getByLabelText("公历出生日期时间"), { target: { value: "1984-02-10T10:00" } });
  fireEvent.change(screen.getByLabelText("出生地时区"), { target: { value: "Asia/Shanghai" } });
}

const liunianData = {
  rule_id: "BZ-LIUNIAN-001",
  school: "ziping-yueling-engineering-baseline-v1",
  status: "engineering_baseline_draft",
  day_master: "甲",
  birth_year: 1984,
  start_year: 2026,
  count: 2,
  years: [
    { year: 2026, ganzhi: "丙午", stem: "丙", branch: "午", stem_ten_god: "食神", nayin: "天河水", age: 42, virtual_age: 43, luck_pillar: { index: 5, ganzhi: "己巳", stem_ten_god: "正财" }, taisui_branch: "午", suipo_branch: "子", branch_relations: [{ type: "六冲", with: "年柱", branches: "午子" }], stem_relations: [] },
    { year: 2027, ganzhi: "丁未", stem: "丁", branch: "未", stem_ten_god: "伤官", nayin: "天河水", age: 43, virtual_age: 44, luck_pillar: null, taisui_branch: "未", suipo_branch: "丑", branch_relations: [], stem_relations: [] },
  ],
  warnings: ["只列可查证事实，不生成吉凶断句"],
};

describe("八字与紫微模块页", () => {
  afterEach(() => vi.restoreAllMocks());

  it("用同一份出生信息排本命盘", async () => {
    const spy = vi.spyOn(api, "evaluateCalculation").mockResolvedValue({ result: { rule_id: "BZ-BAZI-001" } });
    render(<BaziPage />);
    fillBirthProfile();
    fireEvent.click(screen.getByText("排本命盘"));
    await waitFor(() => expect(screen.getByText("本命盘结果：BZ-BAZI-001")).toBeTruthy());
    expect(spy).toHaveBeenCalledWith("bazi", "time", {
      local_datetime: "1984-02-10T10:00",
      timezone: "Asia/Shanghai",
      gender: "男",
      longitude: null,
      use_true_solar_time: false,
    });
  });

  it("紫微斗数页复用出生信息与性别", async () => {
    const spy = vi.spyOn(api, "evaluateCalculation").mockResolvedValue({ result: { rule_id: "ZW-PAN-001" } });
    render(<ZiweiPage />);
    fillBirthProfile();
    fireEvent.click(screen.getByText("排紫微盘"));
    await waitFor(() => expect(screen.getByText("紫微结果：ZW-PAN-001")).toBeTruthy());
    expect(spy).toHaveBeenCalledWith("ziwei", "time", {
      local_datetime: "1984-02-10T10:00",
      timezone: "Asia/Shanghai",
      gender: "男",
      longitude: null,
      use_true_solar_time: false,
    });
  });

  it("流年页签复用出生信息并传起止年份", async () => {
    const spy = vi.spyOn(api, "analyzeLiunian").mockResolvedValue(liunianData);
    render(<BaziPage />);
    fillBirthProfile();
    fireEvent.click(screen.getByRole("tab", { name: /流年/ }));
    fireEvent.change(screen.getByLabelText("起始年份"), { target: { value: "2026" } });
    fireEvent.change(screen.getByLabelText("年数"), { target: { value: "2" } });
    fireEvent.click(screen.getByText("生成流年"));
    await waitFor(() => expect(screen.getByText("2026")).toBeTruthy());
    expect(spy).toHaveBeenCalledWith({
      local_datetime: "1984-02-10T10:00",
      timezone: "Asia/Shanghai",
      gender: "男",
      longitude: null,
      use_true_solar_time: false,
      start_year: 2026,
      count: 2,
    });
    expect(screen.getByText("BZ-LIUNIAN-001")).toBeTruthy();
  });

  it("生平时间轴页签把出生信息交给现有时间轴组件", () => {
    render(<BaziPage />);
    fillBirthProfile();
    fireEvent.click(screen.getByRole("tab", { name: /生平时间轴/ }));
    expect(screen.getByText("时间轴入参：1984-02-10T10:00")).toBeTruthy();
  });

  it("出生时间未填时不发起计算", () => {
    render(<BaziPage />);
    expect(screen.getByText("排本命盘").closest("button").disabled).toBe(true);
    fireEvent.click(screen.getByRole("tab", { name: /流年/ }));
    expect(screen.getByText("生成流年").closest("button").disabled).toBe(true);
  });
});
