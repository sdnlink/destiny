import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LifelineView } from "../../src/components/result/LifelineView";
import * as api from "../../src/lib/api";

const mockResult = {
  solar_datetime: "1984-02-10T10:00:00+08:00",
  gender: "男",
  input: {
    local_datetime: "1984-02-10 10:00:00",
    timezone: "Asia/Shanghai",
    gender: "男",
    longitude: null,
    use_true_solar_time: false,
  },
};

const mockLifeline = {
  school: "ziping-yueling-engineering-baseline-v1",
  status: "engineering_baseline_draft",
  rule_id: "BZ-LIFELINE-001",
  ziping: {
    month_branch: "寅",
    month_element: "木",
    rule: "淵海子平·宝法第二：先看提纲为重",
    hidden_stems: [{ stem: "甲", ten_god: "比肩", qi: "本气", exposed: true }],
    pattern_candidates: [{ pattern_candidate: "比肩格候选", basis: "月令本气甲透出月干" }],
  },
  timeline: [{
    year: 2030, ganzhi: "庚戌", stem_ten_god: "偏印", nayin: "钗钏金",
    age: 46, virtual_age: 47, lichun_datetime: "2030-02-04 03:08:28",
    luck_pillar: { index: 5, ganzhi: "己巳" },
    taisui_branch: "戌", suipo_branch: "辰",
    suiyun: {
      true_taisui: false, suiyun_binglin: true, day_year_parallel: false, zheng_taisui: false,
      relations: { with_luck_pillar: { ganzhi: "己巳", branch_relations: ["六冲"] } },
    },
    yuan_hui_yun_shi: {
      yuan: "第1元", hui: "第7会", yun: "第12运", shi: "第10世", year_in_shi: 13,
    },
    recorded_events: [{ label: "已发生：迁居" }],
  }],
  warnings: ["只列可查证事实，不生成吉凶断语"],
};

describe("LifelineView", () => {
  afterEach(() => vi.restoreAllMocks());

  it("不自动请求，点击后才生成时间轴", async () => {
    const spy = vi.spyOn(api, "analyzeLifeline").mockResolvedValue(mockLifeline);
    render(<LifelineView result={mockResult} />);
    expect(spy).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("生成时间轴"));
    await waitFor(() => expect(screen.getByText("月令提纲：寅（木）")).toBeTruthy());
    expect(spy).toHaveBeenCalledTimes(1);
    expect(spy.mock.calls[0][0]).toEqual({
      local_datetime: "1984-02-10 10:00:00",
      timezone: "Asia/Shanghai",
      gender: "男",
      longitude: null,
      use_true_solar_time: false,
      count: 12,
      events: [],
    });
  });

  it("保留非东八区与真太阳时入参", async () => {
    const spy = vi.spyOn(api, "analyzeLifeline").mockResolvedValue(mockLifeline);
    const resultWithTrueSolar = {
      ...mockResult,
      solar_datetime: "1984-02-10T10:00:00-05:00",
      input: {
        local_datetime: "1984-02-10 10:00:00",
        timezone: "America/New_York",
        gender: "女",
        longitude: -74,
        use_true_solar_time: true,
      },
    };
    render(<LifelineView result={resultWithTrueSolar} />);
    fireEvent.click(screen.getByText("生成时间轴"));
    await waitFor(() => expect(spy).toHaveBeenCalledTimes(1));
    expect(spy.mock.calls[0][0]).toMatchObject({
      local_datetime: "1984-02-10 10:00:00",
      timezone: "America/New_York",
      gender: "女",
      longitude: -74,
      use_true_solar_time: true,
    });
  });

  it("旧结果缺少 input 时剥离 offset，不再直接触发 422", async () => {
    const spy = vi.spyOn(api, "analyzeLifeline").mockResolvedValue(mockLifeline);
    render(<LifelineView result={{ solar_datetime: "1984-02-10T10:00:00+08:00", gender: "男" }} />);
    expect(screen.getByText(/旧版本/)).toBeTruthy();
    fireEvent.click(screen.getByText("生成时间轴"));
    await waitFor(() => expect(spy).toHaveBeenCalledTimes(1));
    expect(spy.mock.calls[0][0]).toMatchObject({
      local_datetime: "1984-02-10T10:00:00",
      timezone: "Asia/Shanghai",
      use_true_solar_time: false,
    });
  });

  it("把录入事件按年份解析后发送", async () => {
    const spy = vi.spyOn(api, "analyzeLifeline").mockResolvedValue(mockLifeline);
    render(<LifelineView result={mockResult} />);
    fireEvent.change(screen.getByLabelText("已发生事件（可选，每行：年份 描述）"), {
      target: { value: "2030 迁居\n2031 入职" },
    });
    fireEvent.click(screen.getByText("生成时间轴"));
    await waitFor(() => expect(spy).toHaveBeenCalledTimes(1));
    expect(spy.mock.calls[0][0].events).toEqual([
      { year: 2030, label: "迁居" },
      { year: 2031, label: "入职" },
    ]);
  });

  it("展示岁运组合、皇极背景与已录事件，且列出警告", async () => {
    vi.spyOn(api, "analyzeLifeline").mockResolvedValue(mockLifeline);
    render(<LifelineView result={mockResult} />);
    fireEvent.click(screen.getByText("生成时间轴"));
    await waitFor(() => expect(screen.getByText("岁运并临 · 大运六冲")).toBeTruthy());
    expect(screen.getByText("第1元 / 第7会")).toBeTruthy();
    expect(screen.getByText("已发生：迁居")).toBeTruthy();
    expect(screen.getByText("只列可查证事实，不生成吉凶断语")).toBeTruthy();
    expect(screen.getByText(/engineering_baseline_draft/)).toBeTruthy();
  });

  it("请求失败时展示错误提示", async () => {
    vi.spyOn(api, "analyzeLifeline").mockRejectedValue(new Error("生平时间轴加载失败"));
    render(<LifelineView result={mockResult} />);
    fireEvent.click(screen.getByText("生成时间轴"));
    await waitFor(() => expect(screen.getByText("生平时间轴加载失败")).toBeTruthy());
  });
});
