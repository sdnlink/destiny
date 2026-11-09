import { describe, expect, it } from "vitest";
import { applyUrlOverrides, syncFormToSearchParams } from "../../src/lib/urlForm";

const baseForm = () => ({
  scene: "zhouyi",
  question: "近期事项推演",
  localDatetime: "2026-01-01T09:00",
  timezone: "Asia/Shanghai",
  category: "career",
});

describe("URL 表单参数编解码", () => {
  it("合法参数预填表单且不改动其它字段", () => {
    // URL 中 + 表示空格，含 + 的时区必须编码为 %2B（写回时 URLSearchParams 会自动处理）
    const params = new URLSearchParams("q=项目是否可行&at=2026-11-09T10:00&tz=Etc%2FGMT%2B8&cat=decision");
    const form = applyUrlOverrides(baseForm(), params);
    expect(form.question).toBe("项目是否可行");
    expect(form.localDatetime).toBe("2026-11-09T10:00");
    expect(form.timezone).toBe("Etc/GMT+8");
    expect(form.category).toBe("decision");
    expect(form.scene).toBe("zhouyi");
  });

  it("拒绝非法时间、时区、分类，并把超长事项截断", () => {
    const params = new URLSearchParams(
      `q=${"x".repeat(300)}&at=not-a-date&tz=<script>&cat=hacked`
    );
    const form = applyUrlOverrides(baseForm(), params);
    expect(form.localDatetime).toBe("2026-01-01T09:00");
    expect(form.timezone).toBe("Asia/Shanghai");
    expect(form.category).toBe("career");
    expect(form.question.length).toBe(120);
  });

  it("空参数原样返回表单", () => {
    expect(applyUrlOverrides(baseForm(), new URLSearchParams())).toEqual(baseForm());
  });

  it("写回时保留无关参数、更新输入、清理空值", () => {
    const params = new URLSearchParams("tab=liunian&q=old");
    const next = syncFormToSearchParams(params, {
      ...baseForm(),
      question: "新事项",
      localDatetime: "",
    });
    expect(next.get("tab")).toBe("liunian");
    expect(next.get("q")).toBe("新事项");
    expect(next.get("at")).toBeNull();
    expect(next.get("tz")).toBe("Asia/Shanghai");
    expect(next.get("cat")).toBe("career");
  });

  it("预填与写回可往返，得到同一份关键输入", () => {
    const form = {
      ...baseForm(),
      question: "团队邀请是否值得接受",
      localDatetime: "2026-11-09T10:00",
      category: "decision",
    };
    const params = syncFormToSearchParams(new URLSearchParams(), form);
    const restored = applyUrlOverrides(baseForm(), params);
    expect(restored.question).toBe(form.question);
    expect(restored.localDatetime).toBe(form.localDatetime);
    expect(restored.timezone).toBe(form.timezone);
    expect(restored.category).toBe(form.category);
  });

  it("起卦方式与三数可往返", () => {
    const form = {
      ...baseForm(),
      yiMethod: "three_numbers",
      yiNumbers: ["12", "34", "56"],
    };
    const params = syncFormToSearchParams(new URLSearchParams(), form);
    expect(params.get("method")).toBe("three_numbers");
    expect(params.get("n1")).toBe("12");
    expect(params.get("n3")).toBe("56");

    const restored = applyUrlOverrides(baseForm(), params);
    expect(restored.yiMethod).toBe("three_numbers");
    expect(restored.yiNumbers).toEqual(["12", "34", "56"]);
  });

  it("手工排盘爻线与六爻铜钱可往返", () => {
    const liuyao = { ...baseForm(), scene: "liuyao", liuyaoMethod: "lines", lyLines: [6, 7, 8, 9, 7, 8] };
    const lineParams = syncFormToSearchParams(new URLSearchParams(), liuyao);
    expect(lineParams.get("lines")).toBe("6,7,8,9,7,8");
    expect(applyUrlOverrides({ ...baseForm(), scene: "liuyao" }, lineParams).lyLines)
      .toEqual([6, 7, 8, 9, 7, 8]);

    const coins = [[2, 2, 3], [2, 3, 3], [3, 2, 2], [2, 2, 2], [3, 3, 2], [2, 3, 2]];
    const coinParams = syncFormToSearchParams(new URLSearchParams(), {
      ...baseForm(), scene: "liuyao", liuyaoMethod: "coins", lyCoins: coins,
    });
    expect(coinParams.get("coins")).toBe("223,233,322,222,332,232");
    expect(applyUrlOverrides({ ...baseForm(), scene: "liuyao" }, coinParams).lyCoins)
      .toEqual(coins);
  });

  it("拒绝非法起卦方式/爻线/数字", () => {
    const bad = new URLSearchParams("method=hacked&lines=1,2&n1=abc&p1=-5&coins=999,999");
    const form = applyUrlOverrides(baseForm(), bad);
    expect(form.yiMethod).toBeUndefined();
    expect(form.yiNumbers).toBeUndefined();
    expect(form.lines).toBeUndefined();
  });

  it("切换起卦方式后写回会清掉上一轮的配套参数", () => {
    const oldParams = syncFormToSearchParams(new URLSearchParams(), {
      ...baseForm(), yiMethod: "manual", lines: [7, 8, 7, 8, 7, 8],
    });
    expect(oldParams.get("lines")).toBe("7,8,7,8,7,8");

    const next = syncFormToSearchParams(oldParams, { ...baseForm(), yiMethod: "time" });
    expect(next.get("method")).toBe("time");
    expect(next.get("lines")).toBeNull();
  });

  it("无起卦方式的体系不写入 method", () => {
    const next = syncFormToSearchParams(new URLSearchParams(), { ...baseForm(), scene: "qimen" });
    expect(next.get("method")).toBeNull();
  });
});
