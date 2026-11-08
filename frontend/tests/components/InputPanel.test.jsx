import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import InputPanel from "../../src/components/InputPanel";

function baseForm(overrides = {}) {
  return {
    scene: "combined",
    category: "career",
    question: "近期事项推演",
    localDatetime: "2026-01-01T12:00",
    timezone: "Asia/Shanghai",
    trueSolar: false,
    longitude: "",
    castNonce: "abcdef1234567890",
    yiMethod: "auto",
    lines: [7, 8, 7, 8, 7, 8],
    yiLower: "8",
    yiUpper: "8",
    yiNumbers: ["1", "2", "3"],
    meihuaMethod: "auto",
    mhUpper: "8",
    mhLower: "8",
    mhNumbers: ["1", "2", "3"],
    liuyaoMethod: "auto",
    lyLower: "8",
    lyUpper: "8",
    lyLines: [7, 8, 7, 8, 7, 8],
    lyCoins: [[2, 2, 3], [2, 3, 3], [3, 2, 2], [2, 2, 2], [3, 3, 2], [2, 3, 2]],
    liurenMethod: "auto",
    lrNumber: "8",
    qimenMethod: "time",
    baziMethod: "time",
    baziGender: "男",
    ziweiMethod: "time",
    ziweiGender: "男",
    fsFacing: "180",
    fsMode: "single",
    fsMeasurements: ["179", "180", "181"],
    fsReference: "magnetic",
    fsDeclination: "0",
    fsError: "1",
    ...overrides,
  };
}

// 受控组件：用真实 state 承接 setForm，保证交互链路和 App 里一致
function Harness({ initialForm = baseForm(), onSubmit = vi.fn(), ...rest }) {
  const [form, setForm] = useState(initialForm);
  return (
    <InputPanel
      form={form}
      setForm={setForm}
      onSubmit={onSubmit}
      onPreview={vi.fn()}
      onReset={vi.fn()}
      onRecast={vi.fn()}
      loading={false}
      previewLoading={false}
      preview={null}
      error=""
      {...rest}
    />
  );
}

describe("InputPanel", () => {
  it("渲染面板标题、起卦凭证与九个体系选项", () => {
    render(<Harness />);

    expect(screen.getByRole("heading", { name: "推演参数" })).toBeInTheDocument();
    expect(screen.getByText("凭证 abcdef12")).toBeInTheDocument();

    const radios = screen.getAllByRole("radio");
    expect(radios).toHaveLength(9);
    expect(screen.getByRole("radio", { name: /综合推演/ })).toHaveAttribute("aria-checked", "true");
  });

  it("模块数按真实请求列表显示，而不是写死的数字", () => {
    render(<Harness />);
    // 综合推演 = 日历 + 周易/梅花/六爻/六壬/奇门/八字/紫微 = 8
    expect(screen.getByText("8 个计算模块")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("radio", { name: /八字/ }));
    // 单一体系 = 日历 + 该体系 = 2
    expect(screen.getByText("2 个计算模块")).toBeInTheDocument();
  });

  it("事项分类下拉使用统一的 CATEGORIES 选项", () => {
    render(<Harness />);

    const select = screen.getByRole("combobox");
    expect(select).toHaveValue("career");
    const labels = within(select).getAllByRole("option").map((option) => option.textContent);
    expect(labels).toEqual([
      "事业",
      "财运",
      "感情姻缘",
      "考试学业",
      "官司是非",
      "出行",
      "寻人",
      "失物",
      "健康",
      "抉择",
      "其他谋事",
    ]);
  });

  it("快捷示例胶囊把分类与问题一起注入表单", () => {
    render(<Harness />);

    const questionInput = screen.getByPlaceholderText("例如：是否接受新的工作机会");
    expect(questionInput).toHaveValue("近期事项推演");

    fireEvent.click(screen.getByText("近期重大项目投资与资金布局可行性"));

    expect(questionInput).toHaveValue("近期重大项目投资与资金布局可行性");
    expect(screen.getByRole("combobox")).toHaveValue("finance");
  });

  it("切到风水体系时只显示风水参数区块", () => {
    render(<Harness />);

    expect(screen.getByText("周易参数")).toBeInTheDocument();
    expect(screen.queryByText("阳宅坐向测量")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("radio", { name: /风水/ }));

    expect(screen.getByText("阳宅坐向测量")).toBeInTheDocument();
    expect(screen.queryByText("周易参数")).not.toBeInTheDocument();
    expect(screen.queryByText("六爻参数")).not.toBeInTheDocument();
    expect(screen.getByRole("spinbutton", { name: /向首方位角/ })).toHaveValue(180);
  });

  it("手工排盘模式可以逐爻修改阴阳老少", () => {
    render(<Harness />);

    fireEvent.click(screen.getAllByText("手工排盘")[0]);

    const oldYang = screen.getByRole("button", { name: "初爻 9 老阳" });
    expect(oldYang).not.toHaveClass("active");

    fireEvent.click(oldYang);
    expect(oldYang).toHaveClass("active");

    // 六个爻位各四个选项
    expect(screen.getAllByRole("button", { name: /^(初|二|三|四|五|上)爻 [6789] / })).toHaveLength(24);
  });

  it("六爻支持手工爻与铜钱两种排盘输入", () => {
    render(<Harness />);
    fireEvent.click(screen.getByRole("radio", { name: /六爻/ }));

    fireEvent.click(screen.getByText("手工排盘"));
    expect(screen.getAllByRole("button", { name: /^(初|二|三|四|五|上)爻 [6789] / })).toHaveLength(24);

    fireEvent.click(screen.getByText("铜钱排盘"));
    expect(screen.getByLabelText("初爻 第1枚铜钱")).toHaveValue("2");
    expect(screen.getByLabelText("上爻 第3枚铜钱")).toHaveValue("2");
  });

  it("周易与梅花支持三数排盘", () => {
    render(<Harness />);

    fireEvent.click(within(screen.getByText("周易参数").closest("section")).getByText("三数排盘"));
    expect(screen.getByDisplayValue("1")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("radio", { name: /梅花/ }));
    fireEvent.click(screen.getByText("三数排盘"));
    expect(screen.getAllByDisplayValue("1").length).toBeGreaterThan(0);
  });

  it("启用真太阳时后要求填写经度", () => {
    render(<Harness />);

    expect(screen.queryByPlaceholderText("例如 116.4074")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("switch"));

    expect(screen.getByRole("switch")).toHaveAttribute("aria-checked", "true");
    expect(screen.getByPlaceholderText("例如 116.4074")).toBeInTheDocument();
  });

  it("多次共识模式下可以增删向首读数", () => {
    render(<Harness />);
    fireEvent.click(screen.getByRole("radio", { name: /风水/ }));

    fireEvent.click(screen.getByText("多次共识"));
    expect(screen.getByText("3 / 12")).toBeInTheDocument();

    fireEvent.click(screen.getByText("增加读数"));
    expect(screen.getByText("4 / 12")).toBeInTheDocument();
    expect(screen.getByLabelText("第4次向首读数")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "删除第4次读数" }));
    expect(screen.getByText("3 / 12")).toBeInTheDocument();
  });

  it("提交表单时把原始事件交给 onSubmit", () => {
    const onSubmit = vi.fn((event) => event.preventDefault());
    const { container } = render(<Harness onSubmit={onSubmit} />);

    fireEvent.submit(container.querySelector("form"));

    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it("错误信息以 alert 角色呈现", () => {
    render(<Harness error="历法服务不可用" />);
    expect(screen.getByRole("alert")).toHaveTextContent("历法服务不可用");
  });

  it("校验成功后在面板内展示四柱与农历日期", () => {
    render(
      <Harness
        preview={{
          pillars: { year: "丙午", month: "庚寅", day: "甲子", hour: "庚午" },
          lunar: { month_name: "正月", day_name: "初二" },
          time: { effective_local_datetime: "2026-01-01T12:00:00" },
        }}
      />
    );

    expect(screen.getByText("时间已校验")).toBeInTheDocument();
    expect(screen.getByText("正月月初二 · 2026-01-01 12:00")).toBeInTheDocument();
    expect(screen.getByText("丙午")).toBeInTheDocument();
  });

  it("loading 时禁用提交按钮并显示推演中", () => {
    render(<Harness loading />);
    const submit = screen.getByRole("button", { name: /正在推演/ });
    expect(submit).toBeDisabled();
  });
});
