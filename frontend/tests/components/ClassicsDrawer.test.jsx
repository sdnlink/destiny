import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

vi.mock("../../src/lib/api.js", () => ({
  loadClassicsStatus: vi.fn(),
  searchClassics: vi.fn(),
}));

import { loadClassicsStatus, searchClassics } from "../../src/lib/api.js";
import ClassicsDrawer from "../../src/components/ClassicsDrawer";

describe("ClassicsDrawer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("展示典籍库规模并检索原文段落", async () => {
    loadClassicsStatus.mockResolvedValue({ available: true, documents: 95, chunks: 4803, characters: 5860817 });
    searchClassics.mockResolvedValue([
      {
        classic_id: "c1",
        title: "三命通會",
        category: "mingli",
        chunk_index: 87,
        excerpt: "大运虽吉，其小运不通，未可便言吉利。",
        match_count: 22,
        source_url: "https://example.com/classic",
        license_name: "公有领域",
      },
    ]);
    render(<ClassicsDrawer open onClose={() => {}} />);

    expect(await screen.findByText(/已收录 95 部/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("典籍原文关键词"), { target: { value: "月令" } });
    fireEvent.click(screen.getByRole("button", { name: "检索", exact: true }));

    await waitFor(() => expect(searchClassics).toHaveBeenCalledWith("月令"));
    expect(await screen.findByText("三命通會")).toBeInTheDocument();
    expect(screen.getByText(/大运虽吉/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /查看原文/ })).toHaveAttribute("href", "https://example.com/classic");
  });

  it("典籍库不可用时禁用检索并提示", async () => {
    loadClassicsStatus.mockResolvedValue({ available: false });
    render(<ClassicsDrawer open onClose={() => {}} />);

    expect(await screen.findByText(/本地典籍库未就绪/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "检索", exact: true })).toBeDisabled();
    expect(searchClassics).not.toHaveBeenCalled();
  });

  it("关闭时不渲染抽屉", () => {
    render(<ClassicsDrawer open={false} onClose={() => {}} />);
    expect(screen.queryByRole("dialog", { name: "典籍原文检索" })).not.toBeInTheDocument();
  });
});
