/**
 * 独立工作区（命运 / 阳宅等）的 Markdown 报告生成。
 *
 * 与综合推演的 generateMarkdownReport 分开：这些接口只返回单个体系结果，
 * 没有 module_results / advisory / literature 外壳，直接按各体系 facts 落笔。
 */
import { generateMarkdownReport } from "./export";

function valueOr(value, fallback = "—") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function numberOr(value, fallback = "—") {
  if (value === null || value === undefined || value === "") return fallback;
  return Number.isFinite(Number(value)) ? String(value) : fallback;
}

function reportHead(title, context = {}) {
  const lines = [`# ${title}`, ""];
  if (context.subtitle) lines.push(`> ${context.subtitle}  `);
  if (context.calculatedAt) lines.push(`> **计算时间**：${context.calculatedAt}  `);
  if (context.note) lines.push(`> ${context.note}`);
  lines.push("", "---", "");
  return lines;
}

function warningSection(warnings) {
  if (!Array.isArray(warnings) || warnings.length === 0) return [];
  return ["## 边界与提示", "", ...warnings.map((warning) => `- ${warning}`), ""];
}

function mountainText(mountain) {
  if (!mountain) return "—";
  const parts = [mountain.name, mountain.trigram, mountain.element, mountain.direction].filter(Boolean);
  return parts.join(" · ");
}

function directionReport(result, context) {
  const facts = result.facts || {};
  const facing = facts.facing || {};
  const sitting = facts.sitting || {};
  const lines = reportHead(context.title || "阳宅风水 · 坐向测量", context);
  lines.push(
    "## 真北坐向",
    "",
    `- **向首**：${numberOr(facts.true_facing_degree)}° · ${mountainText(facing.mountain)}`,
    `- **坐山**：${numberOr(facts.true_sitting_degree)}° · ${mountainText(sitting.mountain)}`,
    `- **测量区间**：向首 ${numberOr(facing.measurement_interval?.start_degree)}°–${numberOr(facing.measurement_interval?.end_degree)}°`,
    `- **距山界**：${numberOr(facing.distance_to_boundary)}° · 分类${facts.classification_stable ? "稳定" : "不稳定"}`,
  );
  if (facing.candidate_mountains?.length > 1) {
    lines.push(`- **候选山向**：${facing.candidate_mountains.map((mountain) => mountain.name).join("、")}`);
  }
  if (facts.boundary_warning) lines.push(`- **边界提示**：${facts.boundary_warning}`);
  lines.push("");
  if (result.evidence?.length) {
    lines.push("## 规则依据", "");
    result.evidence.forEach((item) => lines.push(`- ${valueOr(item.title || item.rule_id)}：${valueOr(item.excerpt || item.note)}`));
    lines.push("");
  }
  lines.push(...warningSection(result.warnings));
  return lines.join("\n");
}

function measurementsReport(result, context) {
  const facts = result.facts || {};
  const consensus = facts.consensus || {};
  const aggregate = consensus.aggregate || {};
  const lines = reportHead(context.title || "阳宅风水 · 多次共识", context);
  lines.push(
    "## 圆周共识",
    "",
    `- **读数数量**：${numberOr(consensus.sample_count)}`,
    `- **共识状态**：${valueOr(consensus.status)}`,
    `- **圆周均值**：${numberOr(consensus.circular_mean_degree)}°`,
    `- **角离散**：${numberOr(consensus.angular_spread)}° · 最大偏差 ${numberOr(consensus.maximum_deviation)}°`,
    `- **有效误差**：${numberOr(consensus.effective_measurement_error)}°`,
    "",
    "## 汇总坐向",
    "",
    `- **向首**：${numberOr(aggregate.true_facing_degree)}° · ${mountainText(aggregate.facing?.mountain)}`,
    `- **坐山**：${numberOr(aggregate.true_sitting_degree)}° · ${mountainText(aggregate.sitting?.mountain)}`,
    `- **分类**：${aggregate.classification_stable ? "稳定" : "不稳定"}`,
    "",
  );
  if (preserveMeasurements(facts.measurements)) {
    lines.push("## 原始读数", "", "| # | 向首读数 | 基准 | 磁偏角 | 误差 |", "| --- | --- | --- | --- | --- |");
    facts.measurements.forEach((item, index) => {
      const input = item.input || item;
      lines.push(`| ${index + 1} | ${numberOr(input.facing_degree)}° | ${valueOr(input.input_reference)} | ${numberOr(input.magnetic_declination)}° | ±${numberOr(input.measurement_error)}° |`);
    });
    lines.push("");
  }
  lines.push(...warningSection(result.warnings));
  return lines.join("\n");
}

function preserveMeasurements(rows) {
  return Array.isArray(rows) && rows.length > 0;
}

function bazhaiReport(result, context) {
  const facts = result.facts || {};
  const life = facts.life_match;
  const lines = reportHead(context.title || "阳宅风水 · 八宅大游年", context);
  lines.push(
    "## 宅卦",
    "",
    `- **坐山**：${valueOr(facts.sitting_mountain)}`,
    `- **宅卦**：${valueOr(facts.sitting_trigram)} · ${valueOr(facts.house_group)}`,
    `- **吉方**：${(facts.lucky_directions || []).join("、") || "—"}`,
    `- **凶方**：${(facts.unlucky_directions || []).join("、") || "—"}`,
    "",
  );
  if (life) {
    lines.push(
      "## 宅命配法",
      "",
      `- **命卦**：${valueOr(life.life_trigram)}（${valueOr(life.life_group)}）`,
      `- **宅卦**：${valueOr(facts.sitting_trigram)}（${valueOr(facts.house_group)}）`,
      `- **同异组**：${life.group_match ? "同组" : "异组"}`,
    );
    if (life.note) lines.push(`- **说明**：${life.note}`);
    lines.push("");
  }
  if (facts.directions?.length) {
    lines.push("## 八方九星", "", "| 方位 | 宫位 | 星 | 性质 |", "| --- | --- | --- | --- |");
    facts.directions.forEach((item) => {
      lines.push(`| ${valueOr(item.direction)} | ${valueOr(item.palace)} | ${valueOr(item.star)}（${valueOr(item.star_animal)}·${valueOr(item.element)}） | ${valueOr(item.nature)} |`);
    });
    lines.push("");
  }
  if (facts.song) {
    lines.push("## 大游年歌", "", `> ${facts.song}`, "");
    if (facts.song_note) lines.push(`> ${facts.song_note}`, "");
  }
  lines.push(...warningSection(result.warnings));
  return lines.join("\n");
}

function xuankongReport(result, context) {
  const facts = result.facts || {};
  const lines = reportHead(context.title || "阳宅风水 · 玄空挨星", context);
  lines.push(
    "## 盘面",
    "",
    `- **坐山**：${valueOr(facts.sitting_mountain)}（${valueOr(facts.sitting_yuan_dragon)}元龙）`,
    `- **向首**：${valueOr(facts.facing_mountain)}（${valueOr(facts.facing_yuan_dragon)}元龙）`,
    `- **运**：${valueOr(facts.period)} · ${valueOr(facts.period_label)}`,
    `- **飞布**：山${valueOr(facts.fly_direction?.sitting)} / 向${valueOr(facts.fly_direction?.facing)}`,
    "",
  );
  if (facts.grid?.length) {
    lines.push("## 九宫挨星", "", "| 宫位 | 运星 | 山星 | 向星 |", "| --- | --- | --- | --- |");
    facts.grid.forEach((cell) => {
      lines.push(`| ${valueOr(cell.palace)} | ${numberOr(cell.period_star)} | ${numberOr(cell.mountain_star)} | ${numberOr(cell.facing_star)} |`);
    });
    lines.push("");
  }
  if (facts.conditions?.length) {
    lines.push("## 格局条件", "");
    facts.conditions.forEach((condition) => {
      lines.push(`- **${valueOr(condition.name)}**：${condition.met ? "成立" : "不成立"}${condition.note ? `（${condition.note}）` : ""}`);
    });
    lines.push("");
  }
  if (facts.tihua_reference) {
    lines.push(
      "## 替星表参考",
      "",
      `- 坐山：${valueOr(facts.tihua_reference.sitting?.mountain)} → ${numberOr(facts.tihua_reference.sitting?.tihua_star)} 入中`,
      `- 向首：${valueOr(facts.tihua_reference.facing?.mountain)} → ${numberOr(facts.tihua_reference.facing?.tihua_star)} 入中`,
    );
    if (facts.tihua_reference.note) lines.push(`- ${facts.tihua_reference.note}`);
    lines.push("");
  }
  if (facts.tihua_chart) {
    lines.push("## 替卦起星盘（工程基线）", "");
    ["sitting", "facing"].forEach((key) => {
      const data = facts.tihua_chart[key];
      if (!data) return;
      lines.push(
        `### ${key === "sitting" ? "坐山" : "向首"}`,
        "",
        `- 到星 ${numberOr(data.arriving_star)} · 替星 ${numberOr(data.tihua_star)} · ${valueOr(data.substitute_mountain, "无替可寻")} · ${valueOr(data.fly_direction)}`,
      );
      if (data.chart) {
        lines.push("", "| 宫位 | 星 |", "| --- | --- |");
        Object.entries(data.chart).forEach(([palace, star]) => lines.push(`| ${palace} | ${numberOr(star)} |`));
      }
      lines.push("");
    });
  }
  lines.push(...warningSection(result.warnings));
  return lines.join("\n");
}

function ziweiReport(result, context) {
  const facts = result.facts || {};
  const lines = reportHead(context.title || "命运专项 · 紫微斗数", context);
  lines.push(
    "## 命盘概要",
    "",
    `- **五行局**：${valueOr(facts.bureau?.name)}（${valueOr(facts.bureau?.nayin)}）`,
    `- **乾坤造**：${valueOr(facts.yin_yang_gender)}`,
    `- **大限方向**：${facts.is_forward_decade ? "顺行" : "逆行"}`,
    `- **命主 / 身主**：${valueOr(facts.ming_zhu)} / ${valueOr(facts.shen_zhu)}`,
    "",
    "## 十二宫",
    "",
    "| 宫位 | 宫干支 | 主星 | 生年四化 | 大限 |",
    "| --- | --- | --- | --- | --- |",
  );
  (facts.palaces_by_branch || []).forEach((palace) => {
    const mainStars = (palace.main_stars || []).map((star) => star.name).join("、") || "—";
    const siHua = (palace.si_hua || []).map((item) => {
      if (typeof item === "string") return item;
      return `${item.star || item.name || ""}${item.hua || item.type || ""}`;
    }).join("、") || "—";
    lines.push(`| ${valueOr(palace.name)} | ${valueOr(palace.palace_stem_branch)} | ${mainStars} | ${siHua} | ${numberOr(palace.major_limit_start)}–${numberOr(palace.major_limit_end)} |`);
  });
  lines.push("");
  if (facts.si_hua) {
    lines.push("## 生年四化", "", Object.entries(facts.si_hua).map(([hua, star]) => `- ${hua}：${star}`).join("\n"), "");
  }
  lines.push(...warningSection(result.warnings));
  return lines.join("\n");
}

function lifelineReport(result, context) {
  const lines = reportHead(context.title || "命运专项 · 生平时间轴", context);
  lines.push(
    "## 时间轴范围",
    "",
    `- **出生年**：${numberOr(result.birth_year)}`,
    `- **起始年**：${numberOr(result.start_year)} · 共 ${numberOr(result.count)} 年`,
    `- **日元**：${valueOr(result.day_master)}`,
    `- **立春交接**：按立春划分流年，逐年只做事实对齐`,
    "",
  );
  if (result.ziping) {
    lines.push(
      "## 月令提纲",
      "",
      `- **月支**：${valueOr(result.ziping.month_branch)} · ${valueOr(result.ziping.month_element)}`,
      `- **取格规则**：${valueOr(result.ziping.rule)}`,
      "",
    );
  }
  const timeline = result.timeline || [];
  if (timeline.length) {
    lines.push("## 逐年事实", "", "| 年份 | 干支 | 十神 | 纳音 | 年龄 | 大运 | 已录事件 |", "| --- | --- | --- | --- | --- | --- | --- |");
    timeline.forEach((row) => {
      const luck = row.luck_pillar
        ? `${row.luck_pillar.ganzhi}（${row.luck_pillar.start_year}–${row.luck_pillar.end_year}）`
        : "—";
      const events = (row.recorded_events || []).map((event) => event.label || "已录事件").join("、") || "—";
      lines.push(`| ${numberOr(row.year)} | ${valueOr(row.ganzhi)} | ${valueOr(row.stem_ten_god)} | ${valueOr(row.nayin)} | ${numberOr(row.age)} | ${luck} | ${events} |`);
    });
    lines.push("");
    const suiyun = timeline.map((row) => ({ year: row.year, suiyun: row.suiyun })).filter((row) => row.suiyun);
    if (suiyun.length) {
      lines.push("## 岁运组合事实", "", "```json", JSON.stringify(suiyun, null, 2), "```", "");
    }
  }
  lines.push(...warningSection(result.warnings));
  return lines.join("\n");
}

function liunianReport(result, context) {
  const lines = reportHead(context.title || "命运专项 · 流年", context);
  lines.push(
    "## 流年范围",
    "",
    `- **出生年**：${numberOr(result.birth_year)}`,
    `- **起始年**：${numberOr(result.start_year)} · 共 ${numberOr(result.count)} 年`,
    `- **日元**：${valueOr(result.day_master)}`,
    "",
  );
  if (result.years?.length) {
    lines.push("## 逐年事实", "", "| 年份 | 干支 | 十神 | 纳音 | 年龄 | 大运 | 地支关系 |", "| --- | --- | --- | --- | --- | --- | --- |");
    result.years.forEach((year) => {
      const luck = year.luck_pillar
        ? `${year.luck_pillar.ganzhi}（${year.luck_pillar.start_year}–${year.luck_pillar.end_year}）`
        : "—";
      const relations = (year.branch_relations || []).map((item) => `${item.type}${item.with || ""}`).join("、") || "—";
      lines.push(`| ${year.year} | ${year.ganzhi} | ${valueOr(year.stem_ten_god)} | ${valueOr(year.nayin)} | ${numberOr(year.age)} | ${luck} | ${relations} |`);
    });
    lines.push("");
  }
  if (result.judgements) {
    lines.push("## 判定摘要", "", "```json", JSON.stringify(result.judgements, null, 2), "```", "");
  }
  lines.push(...warningSection(result.warnings));
  return lines.join("\n");
}

export function generateStandaloneReport(result, context = {}) {
  if (!result) return "";
  const title = context.title || "天机演象 · 专项排盘报告";
  switch (context.module) {
    case "ziwei":
      return ziweiReport(result, { ...context, title });
    case "liunian":
      return liunianReport(result, { ...context, title });
    case "lifeline":
      return lifelineReport(result, { ...context, title });
    case "fengshui-direction":
      return directionReport(result, { ...context, title });
    case "fengshui-measurements":
      return measurementsReport(result, { ...context, title });
    case "fengshui-bazhai":
      return bazhaiReport(result, { ...context, title });
    case "fengshui-xuankong":
      return xuankongReport(result, { ...context, title });
    default:
      return generateMarkdownReport(
        { module_results: [{ module: context.module, result }] },
        {
          question: context.question || "专项排盘",
          category: context.category || "专项",
          reportTitle: title,
        },
      );
  }
}
