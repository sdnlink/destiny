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
});
