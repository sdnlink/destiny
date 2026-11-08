/**
 * Export and formatting utilities for Tianji Yanxiang deduction reports.
 */

export function generateMarkdownReport(result, context) {
  if (!result) return "";

  const timeStr = new Date(result.calculated_at || Date.now()).toLocaleString("zh-CN", { hour12: false });
  const question = context?.question || "事项推演";
  const category = context?.category || "综合";
  const reportTitle = context?.reportTitle || "天机演象 · 综合推演研判报告";

  let md = `# ${reportTitle}\n\n`;
  md += `> **推演事项**：${question}  \n`;
  md += `> **事项领域**：${category}  \n`;
  md += `> **推演时间**：${timeStr}  \n`;
  md += `> **任务编号**：\`${result.task_id || "N/A"}\`  \n\n`;
  md += `---\n\n`;

  // 0. 针对所问事项 · 象数专项推断结论
  const targeted = result.targeted_deduction || result.interpretation?.targeted_findings;
  if (targeted && targeted.findings?.length) {
    md += `## 🎯 针对所问事项 · 象数精准推断结论\n\n`;
    md += `> ${targeted.summary}\n\n`;
    targeted.findings.forEach((f) => {
      md += `### ${f.title}\n\n`;
      md += `${f.conclusion}\n\n`;
      if (f.palette?.length) {
        md += `- **推算色系**：${f.palette.join("、")}\n`;
      }
      md += `- **推导依据**：${f.evidence}\n`;
      md += `- **依据规则**：\`${f.rules?.join(" · ")}\` (${f.confidence})\n\n`;
    });
    md += `---\n\n`;
  }

  // 1. 历法与时空背景
  const cal = result.module_results?.find((m) => m.module === "calendar")?.result;
  if (cal) {
    md += `## 一、 历法与时空基准\n\n`;
    md += `- **公历时刻**：${cal.time?.effective_local_datetime || cal.input?.local_datetime} (${cal.input?.timezone})\n`;
    md += `- **农历生辰**：${cal.lunar?.year}年 ${cal.lunar?.is_leap_month ? "闰" : ""}${cal.lunar?.month_name}月${cal.lunar?.day_name}\n`;
    md += `- **四柱干支**：年柱【${cal.pillars?.year}】 · 月柱【${cal.pillars?.month}】 · 日柱【${cal.pillars?.day}】 · 时柱【${cal.pillars?.time}】\n`;
    md += `- **节气背景**：${cal.solar_terms?.previous_month_boundary?.name || ""} → ${cal.solar_terms?.next_month_boundary?.name || ""}\n`;
    md += `- **日柱旬空**：${cal.xun?.empty_branches?.join("、") || "无"}\n`;
    if (cal.almanac) {
      const a = cal.almanac;
      md += `- **黄历择吉**：十二建星【${a.duty_officer}日】 · 二十八宿【${a.twenty_eight_mansion?.name}宿·${a.twenty_eight_mansion?.luck}】 · 值日天神【${a.day_tian_shen?.type}·${a.day_tian_shen?.name}】\n`;
      if (a.lucky_directions) {
        md += `- **吉神方位**：喜神【${a.lucky_directions.joy_deity}】 · 财神【${a.lucky_directions.wealth_deity}】 · 福神【${a.lucky_directions.blessing_deity}】 · 阳贵【${a.lucky_directions.yang_noble}】 · 阴贵【${a.lucky_directions.yin_noble}】\n`;
      }
      if (a.favorable_activities?.length) {
        md += `- **当日宜忌**：【宜】${a.favorable_activities.slice(0, 8).join("、")}  |  【忌】${a.unfavorable_activities?.slice(0, 6).join("、") || "无"}\n`;
      }
      if (a.pengzu) {
        md += `- **彭祖百忌**：${a.pengzu.gan} · ${a.pengzu.zhi}\n`;
      }
    }
    md += `\n`;
  }

  // 2. 核心研判与策略建议
  if (result.advisory) {
    const adv = result.advisory;
    md += `## 二、 综合研判与策略指引\n\n`;
    md += `### 核心定调\n\n**【${adv.conclusion?.headline}】**\n\n${adv.conclusion?.text}\n\n`;

    if (adv.multi_system_resonance) {
      const res = adv.multi_system_resonance;
      md += `### 多术数共振与交叉印证（共振指数：${res.score}% · ${res.level}）\n\n`;
      md += `> ${res.description}\n\n`;
      if (res.matrix?.length) {
        md += `| 术数体系 | 立场判定 | 核心论据 | 五行/格局焦点 |\n`;
        md += `| :--- | :--- | :--- | :--- |\n`;
        res.matrix.forEach((m) => {
          md += `| **${m.system_name}** | \`${m.stance_label}\` | ${m.key_evidence} | ${m.element_focus} |\n`;
        });
        md += `\n`;
      }
      if (res.synergies?.length) {
        md += `**核心共振契合点**：\n`;
        res.synergies.forEach((s) => { md += `- 💡 ${s}\n`; });
        md += `\n`;
      }
      if (res.tensions?.length) {
        md += `**交叉张力与风控防范**：\n`;
        res.tensions.forEach((t) => { md += `- ⚠️ ${t}\n`; });
        md += `\n`;
      }
    }

    if (adv.domain_analysis) {
      md += `### 现状、趋向与风险剖析\n\n`;
      if (adv.domain_analysis.status_quo?.length) {
        md += `#### 1. 现状与基本面\n`;
        adv.domain_analysis.status_quo.forEach((p) => { md += `- ${p}\n`; });
        md += `\n`;
      }
      if (adv.domain_analysis.trend_evolution?.length) {
        md += `#### 2. 演变趋向与转折\n`;
        adv.domain_analysis.trend_evolution.forEach((p) => { md += `- ${p}\n`; });
        md += `\n`;
      }
      if (adv.domain_analysis.risk_and_pitfalls?.length) {
        md += `#### 3. 潜在盲区与风险\n`;
        adv.domain_analysis.risk_and_pitfalls.forEach((p) => { md += `- ${p}\n`; });
        md += `\n`;
      }
    }

    if (adv.recommendations?.length) {
      md += `### 分阶段落地行动建议\n\n`;
      adv.recommendations.forEach((r) => {
        md += `#### 第${r.priority}阶段：${r.title} (${r.phase})\n`;
        md += `- **建议详情**：${r.detail}\n`;
        md += `- **依据原理**：${r.basis}\n\n`;
      });
    }

    if (adv.verification_questions?.length) {
      md += `### 决策前关键核实清单\n\n`;
      adv.verification_questions.forEach((q, i) => {
        md += `${i + 1}. ${q}\n`;
      });
      md += `\n`;
    }
  }

  // 3. 各模块盘面事实
  md += `## 三、 各体系排盘数理事实\n\n`;

  // 八字四柱
  const bazi = result.module_results?.find((m) => m.module === "bazi")?.result;
  if (bazi) {
    const st = bazi.day_master_strength || {};
    md += `### 1. 子平八字四柱与大运\n\n`;
    md += `- **日元命主**：【${bazi.day_master}】（属${st.element}） · 能量状态：**${st.level}** (得分 ${st.score}/100)\n`;
    md += `- **喜用五行**：${st.favorable_elements?.join("、") || "—"}  |  **忌神五行**：${st.unfavorable_elements?.join("、") || "—"}\n`;
    md += `- **四柱八字**：\n`;
    const p = bazi.facts?.pillars || {};
    md += `  - 年柱：${p.year?.ganzhi} (${p.year?.nayin}) · 十神【${p.year?.stem_ten_god}】 · 长生【${p.year?.twelve_stage}】 · 神煞【${p.year?.shensha?.join("、") || "无"}】\n`;
    md += `  - 月柱：${p.month?.ganzhi} (${p.month?.nayin}) · 十神【${p.month?.stem_ten_god}】 · 长生【${p.month?.twelve_stage}】 · 神煞【${p.month?.shensha?.join("、") || "无"}】\n`;
    md += `  - 日柱：${p.day?.ganzhi} (${p.day?.nayin}) · 十神【日元】 · 长生【${p.day?.twelve_stage}】 · 神煞【${p.day?.shensha?.join("、") || "无"}】\n`;
    md += `  - 时柱：${p.hour?.ganzhi} (${p.hour?.nayin}) · 十神【${p.hour?.stem_ten_god}】 · 长生【${p.hour?.twelve_stage}】 · 神煞【${p.hour?.shensha?.join("、") || "无"}】\n`;
    if (bazi.luck_pillars?.length) {
      md += `- **大运流年**：\n`;
      bazi.luck_pillars.forEach((lp) => {
        md += `  - 第${lp.index}步（${lp.start_age}~${lp.end_age}岁 / ${lp.start_year}~${lp.end_year}年）：【${lp.ganzhi}】${lp.stem_ten_god} · ${lp.nayin}\n`;
      });
    }
    md += `\n`;
  }

  // 奇门遁甲
  const qimen = result.module_results?.find((m) => m.module === "qimen")?.result;
  if (qimen) {
    md += `### 2. 时家转盘奇门遁甲\n\n`;
    md += `- **局象定局**：【${qimen.dun_type}${qimen.ju_number}局 · ${qimen.yuan_type}】 · 节气：${qimen.solar_term}\n`;
    md += `- **值符与值使**：值符【${qimen.zhi_fu_star}】落${qimen.zhi_fu_palace}宫 · 值使【${qimen.zhi_shi_gate}】落${qimen.zhi_shi_palace}宫\n`;
    if (qimen.favorable_directions?.length) {
      md += `- **吉方研判**：\n`;
      qimen.favorable_directions.forEach((fd) => {
        md += `  - ${fd.direction} (${fd.palace_name})：临【${fd.gate}】+【${fd.star}】，八神【${fd.spirit}】护佑\n`;
      });
    }
    md += `\n`;
  }

  // 周易 / 梅花 / 六爻
  const zhouyi = result.module_results?.find((m) => m.module === "zhouyi")?.result;
  if (zhouyi) {
    md += `### 3. 周易卦象\n\n`;
    md += `- 本卦：【${zhouyi.facts?.original?.name}卦】（${zhouyi.facts?.original?.symbol}）  →  变卦：【${zhouyi.facts?.changed?.name}卦】（${zhouyi.facts?.changed?.symbol}）\n`;
    md += `- 动爻：${zhouyi.facts?.moving_lines?.length ? zhouyi.facts.moving_lines.map((l) => `第${l}爻`).join("、") : "静卦无动爻"}\n\n`;
  }

  const liuyao = result.module_results?.find((m) => m.module === "liuyao")?.result;
  if (liuyao?.facts?.yongshen) {
    const yongshen = liuyao.facts.yongshen;
    md += `### 4. 六爻用神焦点\n\n`;
    const renderRelPositions = (positions) => {
      if (!positions || positions.length === 0) return "本卦不现";
      const map = (p) => {
        if (p.startsWith("伏")) return `伏神第${p.slice(1)}爻`;
        if (p.startsWith("变")) return `变爻第${p.slice(1)}爻`;
        return `本卦第${p}爻`;
      };
      return positions.map(map).join("、");
    };
    md += `- **所取用神**：${(yongshen.targets || []).join("、") || "—"}\n`;
    md += `- **原神**：${yongshen.yuan_shen?.relative || "—"} ${yongshen.yuan_shen?.element || ""} ${renderRelPositions(yongshen.yuan_shen?.positions)}\n`;
    md += `- **忌神**：${yongshen.ji_shen?.relative || "—"} ${yongshen.ji_shen?.element || ""} ${renderRelPositions(yongshen.ji_shen?.positions)}\n`;
    md += `- **仇神**：${yongshen.chou_shen?.relative || "—"} ${yongshen.chou_shen?.element || ""} ${renderRelPositions(yongshen.chou_shen?.positions)}\n`;
    if (yongshen.candidates?.length) {
      md += `\n| 候选 | 来源 | 爻位 | 地支 | 五行 | 动静 | 旺衰 | 空破 | 排序 |\n`;
      md += `| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n`;
      yongshen.candidates.forEach((candidate, index) => {
        md += `| ${index + 1} | ${candidate.source} | 第 ${candidate.position} 爻 | ${candidate.branch} | ${candidate.element} | ${candidate.moving ? "动爻" : "静爻"} | ${candidate.month_strength || "—"} | ${candidate.void_state || "不空"} | ${candidate.rank_score} |\n`;
      });
    }
    if (yongshen.selection_note) md += `\n> ${yongshen.selection_note}\n`;
    md += `\n`;
  }

  const liuren = result.module_results?.find((m) => m.module === "liuren")?.result;
  if (liuren) {
    const t = liuren.facts?.three_transmissions || {};
    md += `### 5. 大六壬三传四课\n\n`;
    md += `- 占日【${liuren.facts?.day_pillar}】 · 占时【${liuren.facts?.occupation_time?.branch}】 · 月将【${liuren.facts?.month_general?.name}】\n`;
    md += `- 三传：初传【${t.transmissions?.[0] || "—"}】 → 中传【${t.transmissions?.[1] || "—"}】 → 末传【${t.transmissions?.[2] || "—"}】 (${t.lesson_type || "课体"})\n\n`;
  }

  // 4. 古籍典籍引证
  if (result.literature?.books?.length) {
    md += `## 四、 经典古籍断语引证\n\n`;
    result.literature.books.forEach((b) => {
      md += `### 《${b.title}》 (${b.matched_term} · ${b.calculation_role})\n\n`;
      md += `> ${b.excerpt}\n\n`;
      md += `- **书中观点**：${b.book_opinion}\n`;
      md += `- **事项参考**：${b.application_note}\n\n`;
    });
  }

  md += `---\n\n`;
  md += `*本推演报告由「天机演象」数字化术数研判工作台确定性生成，仅供学术研究与决策参考。*\n`;

  return md;
}

export function downloadMarkdownFile(content, filename = "tianji-yanxiang-report.md") {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function copyToClipboard(text) {
  if (navigator.clipboard?.writeText) {
    return navigator.clipboard.writeText(text);
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
}
