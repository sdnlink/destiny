import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import HexagramView from "../../src/components/HexagramView";

function meihuaPlate(facts) {
  return { plates: { meihua: { facts } } };
}

describe("HexagramView", () => {
  it("没有卦象数据时不渲染任何内容", () => {
    const { container } = render(<HexagramView plateData={{ plates: {} }} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("从梅花排盘事实中取卦名与上下卦，渲染六爻", () => {
    const { container } = render(
      <HexagramView
        plateData={meihuaPlate({
          original: { name: "乾为天", upper: "乾", lower: "乾" },
        })}
      />
    );

    expect(screen.getByText("乾为天")).toBeInTheDocument();
    // 上下卦都是乾，所以 ☰乾 出现两次，分别是上卦与下卦
    expect(screen.getAllByText("☰乾")).toHaveLength(2);
    expect(screen.getByText("上")).toBeInTheDocument();
    expect(screen.getByText("下")).toBeInTheDocument();
    expect(container.querySelectorAll(".hex-line")).toHaveLength(6);
    // 乾卦六爻全为阳爻
    expect(container.querySelectorAll(".hex-line.yang")).toHaveLength(6);
    expect(container.querySelectorAll(".hex-line.yin")).toHaveLength(0);
  });

  it("按上下卦拆爻：下卦巽上卦坎得到阴阳混合的卦象", () => {
    const { container } = render(
      <HexagramView plateData={meihuaPlate({ original: { name: "水风井", upper: "坎", lower: "巽" } })} />
    );

    expect(screen.getByText("☵坎")).toBeInTheDocument();
    expect(screen.getByText("☴巽")).toBeInTheDocument();
    // 下卦巽 = [0,1,1]，上卦坎 = [0,1,0] → 3 阳 3 阴
    expect(container.querySelectorAll(".hex-line.yang")).toHaveLength(3);
    expect(container.querySelectorAll(".hex-line.yin")).toHaveLength(3);
  });

  it("标记动爻并输出动爻提示", () => {
    const { container } = render(
      <HexagramView
        plateData={meihuaPlate({
          original: { name: "乾为天", upper: "乾", lower: "乾" },
          moving_lines: [2, 5],
        })}
      />
    );

    expect(container.querySelectorAll(".hex-line.moving")).toHaveLength(2);
    expect(screen.getByText("动爻：二爻、五爻")).toBeInTheDocument();
  });

  it("没有六神数据时回落到默认六神序列，并渲染六亲标签", () => {
    render(
      <HexagramView
        plateData={meihuaPlate({
          original: { name: "乾为天", upper: "乾", lower: "乾" },
          liuqin: ["父母", "兄弟", "子孙", "妻财", "官鬼", "父母"],
        })}
      />
    );

    expect(screen.getByText("青龙")).toBeInTheDocument();
    expect(screen.getByText("玄武")).toBeInTheDocument();
    expect(screen.getAllByText("父母")).toHaveLength(2);
    expect(screen.getByText("官鬼")).toBeInTheDocument();
  });

  it("六爻排盘同样可解析，且支持 compact 紧凑模式", () => {
    const { container } = render(
      <HexagramView
        compact
        plateData={{ plates: { liuyao: { result: { facts: { original_hexagram: "地天泰" } } } } }}
      />
    );

    expect(container.querySelector(".hexagram-view")).toHaveClass("compact");
    expect(screen.getByText("地天泰")).toBeInTheDocument();
  });
});
