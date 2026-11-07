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

  it("按后端真实卦象结构（lines + 上下卦对象）渲染爻象，不能退化成全阴", () => {
    const { container } = render(
      <HexagramView
        plateData={meihuaPlate({
          // 大有：乾下离上，六爻自下而上是 1,1,1,1,0,1
          original: {
            name: "大有",
            ordinal: 14,
            symbol: "䷍",
            lines: [1, 1, 1, 1, 0, 1],
            lower_trigram: { name: "乾", element: "金" },
            upper_trigram: { name: "离", element: "火" },
          },
        })}
      />
    );

    expect(screen.getByText("大有")).toBeInTheDocument();
    expect(screen.getByText("☰乾")).toBeInTheDocument();
    expect(screen.getByText("☲离")).toBeInTheDocument();
    // 旧实现读 orig.upper/orig.lower，两者为空 → 六爻全是阴爻（坤为地）
    expect(container.querySelectorAll(".hex-line.yang")).toHaveLength(5);
    expect(container.querySelectorAll(".hex-line.yin")).toHaveLength(1);
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

  it("六神按爻位顺序渲染：初爻用数组第一个，而不是把整份颠倒", () => {
    const { container } = render(
      <HexagramView
        plateData={meihuaPlate({
          original: { name: "乾为天", upper: "乾", lower: "乾" },
          six_spirits: ["玄武", "青龙", "朱雀", "勾陈", "螣蛇", "白虎"],
        })}
      />
    );

    const lines = Array.from(container.querySelectorAll(".hex-line"));
    // DOM 从上爻渲染到初爻
    const byPosition = {};
    for (const line of lines) {
      const pos = line.querySelector(".line-position").textContent;
      byPosition[pos] = line.querySelector(".line-spirit")?.textContent || "";
    }
    expect(byPosition["初爻"]).toBe("玄武");
    expect(byPosition["上爻"]).toBe("白虎");
    expect(byPosition["三爻"]).toBe("朱雀");
  });

  it("梅花与六爻同时存在时，六神取六爻那份而不是回落到默认序列", () => {
    render(
      <HexagramView
        plateData={{
          plates: {
            meihua: { facts: { original: { name: "乾为天", upper: "乾", lower: "乾" } } },
            liuyao: {
              facts: {
                original: { name: "地天泰", upper: "坤", lower: "乾" },
                six_spirits: ["玄武", "青龙", "朱雀", "勾陈", "螣蛇", "白虎"],
              },
            },
          },
        }}
      />
    );

    // 卦名仍取第一个体系（梅花），六神来自六爻
    expect(screen.getByText("乾为天")).toBeInTheDocument();
    expect(screen.getByText("玄武")).toBeInTheDocument();
    expect(screen.getByText("白虎")).toBeInTheDocument();
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
