import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import StructuredDisplay from "../../src/components/StructuredDisplay";

const FULL = {
  step1: {
    question: "是否接受新的工作机会",
    category_label: "事业",
    casting_method: "个体自动",
    system: "梅花易数",
    user_profile: { gender: "男" },
    ready: true,
    missing_fields: [],
  },
  step2: {
    systems: ["梅花易数", "六爻纳甲"],
    plates: {
      meihua: {
        facts: { original: { name: "水风井", upper: "坎", lower: "巽" }, moving_lines: [3] },
      },
    },
    calendar: {
      pillars: { year: "甲辰", month: "丙寅", day: "戊午", hour: "庚申" },
      solar_term: { next: { name: "雨水" } },
    },
  },
  step3: {
    primary_yongshen: "官鬼",
    secondary_yongshen: "父母",
    logic: "问事业以官鬼为主",
    party_yongshen: [{ party: "求测者", yongshen: "世爻", role: "当事人" }],
  },
  step4: {
    yongshen_wangshuai: { level: "旺", reason: "得月建生扶" },
    tiyong_relation: { type: "用生体", meaning: "事情来就我" },
    analysis_chain: ["月建生官鬼", "官鬼生父母"],
  },
  step5: {
    hexagram_name: "水火既济",
    symbol_mappings: [{ symbol: "井", event_mapping: "需要修缮", original_meaning: "井养而不穷" }],
  },
  step6: {
    fortune_level: "偏吉",
    current_status: "刚起步",
    trend: "缓慢上行",
    timing: "三个月内",
    favorable: ["有贵人"],
    obstacles: ["流程冗长"],
    fortune_basis: ["用神得生", "动爻化进"],
  },
  step7: {
    advice: ["先谈条件再落笔", "避免一次性投入过多"],
    disclaimer: "本内容为传统文化推演，不构成决策依据。",
  },
};

describe("StructuredDisplay", () => {
  it("空工作流时只渲染容器，不出现任何步骤标题", () => {
    const { container } = render(<StructuredDisplay workflow={{}} />);
    expect(container.querySelectorAll(".structured-step")).toHaveLength(0);
    expect(screen.queryByText(/步骤1/)).not.toBeInTheDocument();
  });

  it("按步骤渲染 7 个步骤标题", () => {
    render(<StructuredDisplay workflow={FULL} />);
    expect(screen.getByText("📋 步骤1：信息校验")).toBeInTheDocument();
    expect(screen.getByText("☯️ 步骤2：完整排盘")).toBeInTheDocument();
    expect(screen.getByText("🧭 步骤7：趋吉避凶")).toBeInTheDocument();
  });

  it("步骤1 渲染求测事由、类别与信息充足状态", () => {
    render(<StructuredDisplay workflow={FULL} />);
    expect(screen.getByText("是否接受新的工作机会")).toBeInTheDocument();
    expect(screen.getByText("事业")).toBeInTheDocument();
    expect(screen.getByText("个体自动")).toBeInTheDocument();
    expect(screen.getByText("梅花易数")).toBeInTheDocument();
    expect(screen.getByText("gender:男")).toBeInTheDocument();
    expect(screen.getByText("✓ 信息充足，可排盘")).toBeInTheDocument();
  });

  it("信息不足时列出缺失字段", () => {
    render(
      <StructuredDisplay
        workflow={{ step1: { ready: false, missing_fields: ["出生时间", "性别"] } }}
      />
    );
    expect(screen.getByText("✗ 缺失：出生时间、性别")).toBeInTheDocument();
  });

  it("步骤2 内嵌卦象视图并展示历法基线与节气", () => {
    const { container } = render(<StructuredDisplay workflow={FULL} />);
    expect(screen.getByText("梅花易数、六爻纳甲")).toBeInTheDocument();
    expect(screen.getByText("水风井")).toBeInTheDocument();
    expect(container.querySelectorAll(".hexagram-view")).toHaveLength(1);
    expect(screen.getByText("甲辰年 丙寅月 戊午日 庚申时 · 雨水（下一节气）")).toBeInTheDocument();
  });

  it("步骤3 到步骤6 渲染用神、旺衰、象义与吉凶结论", () => {
    render(<StructuredDisplay workflow={FULL} />);
    expect(screen.getByText("官鬼")).toBeInTheDocument();
    expect(screen.getByText("问事业以官鬼为主")).toBeInTheDocument();
    expect(screen.getByText("求测者：世爻（当事人）")).toBeInTheDocument();
    expect(screen.getByText("旺")).toBeInTheDocument();
    expect(screen.getByText("（得月建生扶）")).toBeInTheDocument();
    expect(screen.getByText("用生体 — 事情来就我")).toBeInTheDocument();
    expect(screen.getByText("月建生官鬼")).toBeInTheDocument();
    // 符号映射行直连文本节点是「：事件映射」，原义放在子 span 里
    expect(screen.getByText("：需要修缮")).toBeInTheDocument();
    expect(screen.getByText("（原义：井养而不穷）")).toBeInTheDocument();
    expect(screen.getByText("偏吉")).toBeInTheDocument();
    expect(screen.getByText("三个月内")).toBeInTheDocument();
    expect(screen.getByText("有贵人")).toBeInTheDocument();
    expect(screen.getByText("流程冗长")).toBeInTheDocument();
    expect(screen.getByText("用神得生；动爻化进")).toBeInTheDocument();
  });

  it("非卦象体系（八字）在步骤2 渲染盘面摘要，而不是空白", () => {
    render(
      <StructuredDisplay
        workflow={{
          step2: {
            systems: ["八字命理"],
            plates: {
              bazi: {
                system_label: "八字命理",
                facts: {},
                summary: { 日主: "癸（水）", 四柱: "丙午 戊戌 癸未 丁巳", 日主旺衰: "偏弱", 大运: "8 步" },
              },
            },
          },
        }}
      />
    );

    expect(screen.getByText("八字命理盘面：")).toBeInTheDocument();
    expect(screen.getByText("日主：癸（水）")).toBeInTheDocument();
    expect(screen.getByText("四柱：丙午 戊戌 癸未 丁巳")).toBeInTheDocument();
    expect(screen.getByText("大运：8 步")).toBeInTheDocument();
  });

  it("非卦象体系：步骤3 标出取用体系，步骤6 显示未评级", () => {
    render(
      <StructuredDisplay
        workflow={{
          step3: {
            yongshen_framework: "八字命理",
            primary_yongshen: "喜用五行（火、木）",
            secondary_yongshen: "忌神五行（水、金）",
            logic: "日主【癸水】极弱。喜用五行：火、木。",
          },
          step6: {
            fortune_level: "未评级",
            current_status: "本次以八字命理盘面为据，未取卦象用神。",
            fortune_basis: ["本次未排卦象体系（梅花/六爻/周易），按 WF-FORTUNE-001 的口径无法出具卦象吉凶等级"],
          },
        }}
      />
    );

    expect(screen.getByText("八字命理")).toBeInTheDocument();
    expect(screen.getByText("喜用五行（火、木）")).toBeInTheDocument();
    expect(screen.getByText("未评级")).toBeInTheDocument();
    expect(screen.queryByText(/官鬼/)).toBeNull();
  });

  it("非卦象体系的步骤5 给出盘面说明，而不是空白卡片", () => {
    render(
      <StructuredDisplay
        workflow={{ step5: { hexagram_name: "", symbol_mappings: [] } }}
      />
    );
    expect(
      screen.getByText(/本次盘面未排卦象体系，无卦象符号可解读/)
    ).toBeInTheDocument();
  });

  it("步骤7 以有序列表渲染建议并附文化提示", () => {
    render(<StructuredDisplay workflow={FULL} />);
    expect(screen.getByText("先谈条件再落笔")).toBeInTheDocument();
    expect(screen.getByText("本内容为传统文化推演，不构成决策依据。")).toBeInTheDocument();
  });

  it("拓展参考资料库以 JSON 形式展示", () => {
    render(<StructuredDisplay workflow={{ reference_library: { 梅花易数: ["卷一"] } }} />);
    expect(screen.getByText("📚 拓展参考资料库")).toBeInTheDocument();
    expect(screen.getByText(/"梅花易数"/)).toBeInTheDocument();
  });
});
