import { describe, expect, it } from "vitest";
import { SCHOOLS, schoolForSystem } from "../../src/lib/schools";

describe("schools", () => {
  it("每个体系只归入一个流派", () => {
    const systems = SCHOOLS.flatMap((school) => school.systems);
    expect(new Set(systems).size).toBe(systems.length);
  });

  it("未知体系回落到综合，不抛错", () => {
    expect(schoolForSystem("unknown")).toBe(SCHOOLS[0]);
    expect(schoolForSystem("liuyao").label).toBe("易占");
    expect(schoolForSystem("ziwei").label).toBe("命理");
    expect(schoolForSystem("liuyao").menu).toBe("卜筮专项");
  });
});
