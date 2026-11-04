import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import InteractionResultDisplay from "../../src/components/InteractionResultDisplay";

describe("InteractionResultDisplay", () => {
  beforeEach(() => {
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
  });

  it("没有数据时不渲染", () => {
    const { container } = render(<InteractionResultDisplay data={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("深度追问结果渲染问题、符号类型与解读正文", () => {
    render(
      <InteractionResultDisplay
        data={{
          type: "deep_question",
          question: "这笔合作能否落地？",
          detected_symbols: ["坎", "离"],
          analysis: "坎为险，离为明。",
        }}
      />
    );

    expect(screen.getByText("这笔合作能否落地？")).toBeInTheDocument();
    expect(screen.getByText("检测到符号类型：坎、离")).toBeInTheDocument();
    expect(screen.getByText("坎为险，离为明。")).toBeInTheDocument();
  });

  it("换角度结果渲染新角度、匹配预设与建议角度标签", () => {
    render(
      <InteractionResultDisplay
        data={{
          type: "angle_shift",
          new_angle: "从对方立场看",
          reinterpretation: "对方更在意时间成本。",
          matched_preset: "利益视角",
          shift_focus: "关系张力",
          suggested_angles: ["长期视角", "成本视角"],
        }}
      />
    );

    expect(screen.getByText("从对方立场看")).toBeInTheDocument();
    expect(screen.getByText("匹配预设：利益视角")).toBeInTheDocument();
    expect(screen.getByText("关系张力")).toBeInTheDocument();
    expect(screen.getByText("对方更在意时间成本。")).toBeInTheDocument();
    expect(screen.getByText("长期视角")).toBeInTheDocument();
    expect(screen.getByText("成本视角")).toBeInTheDocument();
  });

  it("描述型结果渲染选项列表与解读视角调整", () => {
    render(
      <InteractionResultDisplay
        data={{
          description: "当前信息不足以判断。",
          options: ["补充出生时间", "改用六爻"],
          interpretation_shift: {
            note: "先确认时间基准",
            suggested_angles: ["历法口径", "起卦方式"],
          },
        }}
      />
    );

    expect(screen.getByText("当前信息不足以判断。")).toBeInTheDocument();
    expect(screen.getByText("补充出生时间")).toBeInTheDocument();
    expect(screen.getByText("改用六爻")).toBeInTheDocument();
    expect(screen.getByText("解读视角调整：")).toBeInTheDocument();
    expect(screen.getByText("先确认时间基准")).toBeInTheDocument();
    expect(screen.getByText("历法口径")).toBeInTheDocument();
  });

  it("多方取象渲染每个人物的用神、立场、心态与诉求", () => {
    render(
      <InteractionResultDisplay
        data={{
          parties: [
            {
              party: "求测者",
              yongshen: "世爻",
              position: "主动方",
              mindset: "焦虑",
              demands: "尽快确定",
              deep_analysis: "世爻旬空，心里没底。",
            },
          ],
        }}
      />
    );

    expect(screen.getByText("求测者")).toBeInTheDocument();
    expect(screen.getByText("用神：世爻")).toBeInTheDocument();
    expect(screen.getByText("立场：主动方")).toBeInTheDocument();
    expect(screen.getByText("心态：焦虑")).toBeInTheDocument();
    expect(screen.getByText("诉求：尽快确定")).toBeInTheDocument();
    expect(screen.getByText("世爻旬空，心里没底。")).toBeInTheDocument();
  });

  it("多抉择结果把利弊数组用分号拼接", () => {
    render(
      <InteractionResultDisplay
        data={{
          choices: [
            {
              choice: "接受 offer",
              analysis_angle: "事业",
              risk_level: "中",
              trend: "上行",
              pros: ["收入提升", "平台更好"],
              cons: ["通勤变远"],
            },
          ],
          recommendation: "先谈条件再决定。",
        }}
      />
    );

    expect(screen.getByText("接受 offer")).toBeInTheDocument();
    expect(screen.getByText("利：收入提升；平台更好")).toBeInTheDocument();
    expect(screen.getByText("弊：通勤变远")).toBeInTheDocument();
    expect(screen.getByText("先谈条件再决定。")).toBeInTheDocument();
  });

  it("复盘结果区分应验与未应验象", () => {
    render(
      <InteractionResultDisplay
        data={{
          verified: ["上级主动联系"],
          unverified: ["薪资未涨"],
          actual_outcome: "接受新岗位",
          analysis: { 时间: "应期偏早" },
          lessons: ["别忽略时间成本"],
        }}
      />
    );

    expect(screen.getByText("接受新岗位")).toBeInTheDocument();
    expect(screen.getByText("上级主动联系")).toBeInTheDocument();
    expect(screen.getByText("薪资未涨")).toBeInTheDocument();
    expect(screen.getByText("时间：")).toBeInTheDocument();
    expect(screen.getByText("应期偏早")).toBeInTheDocument();
    expect(screen.getByText("别忽略时间成本")).toBeInTheDocument();
  });

  it("无法识别的结构回落为 JSON 展示", () => {
    render(<InteractionResultDisplay data={{ foo: "bar" }} />);
    expect(screen.getByText(/"foo": "bar"/)).toBeInTheDocument();
  });

  it("showCopy 时渲染复制按钮，点击把内容写入剪贴板", () => {
    render(<InteractionResultDisplay data={{ type: "deep_question", question: "问", analysis: "答" }} showCopy />);

    const button = screen.getByTitle("复制此条交互结果");
    fireEvent.click(button);

    expect(navigator.clipboard.writeText).toHaveBeenCalledTimes(1);
    const copied = navigator.clipboard.writeText.mock.calls[0][0];
    expect(JSON.parse(copied)).toMatchObject({ question: "问", analysis: "答" });
  });
});
