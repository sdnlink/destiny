import { beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { fireEvent, render, screen, within } from "@testing-library/react";
import HomePage from "../../src/pages/HomePage";
import { RECENT_MODULES_KEY } from "../../src/lib/modules";

vi.mock("../../src/lib/api.js", () => ({
  analyzeCalendar: vi.fn(),
}));

function renderHome() {
  return render(<MemoryRouter><HomePage /></MemoryRouter>);
}

describe("HomePage 引导页", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("列出全部术数入口，可按名称或描述关键词过滤", () => {
    renderHome();
    expect(screen.getByRole("heading", { name: "天机演象" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /六爻/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /紫微斗数/ })).toBeInTheDocument();

    // 「纳甲」只出现在六爻描述里
    fireEvent.change(screen.getByLabelText("搜索功能模块"), { target: { value: "纳甲" } });
    expect(screen.getByRole("link", { name: /六爻/ })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /紫微斗数/ })).not.toBeInTheDocument();

    // 清空搜索恢复全部
    fireEvent.click(screen.getByRole("button", { name: "清除搜索" }));
    expect(screen.getByRole("link", { name: /紫微斗数/ })).toBeInTheDocument();
  });

  it("无匹配结果时给出明确提示", () => {
    renderHome();
    fireEvent.change(screen.getByLabelText("搜索功能模块"), { target: { value: "不存在的术数" } });
    expect(screen.getByText(/没有匹配「不存在的术数」/)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /六爻/ })).not.toBeInTheDocument();
  });

  it("展示最近使用入口，并过滤已下线的路径", () => {
    localStorage.setItem(RECENT_MODULES_KEY, JSON.stringify(["/ziwei", "/retired-page"]));
    renderHome();

    const section = screen.getByRole("heading", { name: /最近使用/ }).closest("section");
    expect(within(section).getByRole("link", { name: "紫微斗数" })).toBeInTheDocument();
    expect(within(section).getAllByRole("link")).toHaveLength(1);
  });

  it("没有最近使用记录时不显示该区块", () => {
    renderHome();
    expect(screen.queryByRole("heading", { name: /最近使用/ })).not.toBeInTheDocument();
  });
});
