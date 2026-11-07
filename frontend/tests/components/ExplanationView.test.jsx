import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ExplanationView } from "../../src/components/result/ExplanationView";

describe("ExplanationView", () => {
  it("正确渲染后端格式的模块标题、小节标题（title）与规则徽章（rule_ids）", () => {
    const mockExplanation = {
      summary: "本次完成历法与周易推演。",
      modules: [
        {
          module: "calendar",
          title: "历法与时间基准",
          summary: "农历丙午年，四柱已定。",
          sections: [
            {
              title: "时间标准化",
              text: "原始本地时间经标准化换算为UTC时间。",
              rule_ids: ["CAL-NORMALIZE-001", "CAL-SOLAR-TIME-001"],
            },
            {
              title: "真太阳时处理",
              text: "已根据经度修正平太阳时时差。",
              rule_ids: ["CAL-SOLAR-TIME-001"],
            },
          ],
        },
      ],
    };

    render(
      <ExplanationView
        explanation={mockExplanation}
        advisory={null}
        literature={null}
        imagery={null}
        yuanHui={null}
        interpretation={null}
      />
    );

    // 模块头部与小节标题必须正常展示，不能是 undefined
    expect(screen.getByText("历法与时间基准")).toBeInTheDocument();
    expect(screen.getByText("时间标准化")).toBeInTheDocument();
    expect(screen.getByText("真太阳时处理")).toBeInTheDocument();
    expect(screen.getByText("原始本地时间经标准化换算为UTC时间。")).toBeInTheDocument();

    // 规则徽章需合并展示
    expect(screen.getByText("CAL-NORMALIZE-001 · CAL-SOLAR-TIME-001")).toBeInTheDocument();
    expect(screen.getByText("CAL-SOLAR-TIME-001")).toBeInTheDocument();
  });

  it("兼容 heading 与单数 rule_id 历史属性", () => {
    const mockExplanation = {
      summary: "历史格式测试。",
      modules: [
        {
          module: "zhouyi",
          title: "周易推演结果",
          summary: "本卦大有。",
          sections: [
            {
              heading: "本卦结构解析",
              text: "火天大有，顺天依时。",
              rule_id: "YI-LEGACY-001",
            },
          ],
        },
      ],
    };

    render(
      <ExplanationView
        explanation={mockExplanation}
        advisory={null}
        literature={null}
        imagery={null}
        yuanHui={null}
        interpretation={null}
      />
    );

    expect(screen.getByText("周易推演结果")).toBeInTheDocument();
    expect(screen.getByText("本卦结构解析")).toBeInTheDocument();
    expect(screen.getByText("YI-LEGACY-001")).toBeInTheDocument();
  });
});

