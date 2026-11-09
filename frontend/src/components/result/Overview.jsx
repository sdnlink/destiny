// 由 ResultWorkspace.jsx 拆分而来（审计 13：超大组件拆分），只搬代码未改逻辑。
import { useState } from "react";
import {
  ArrowRight,
  BookOpen,
  CalendarDays,
  Check,
  CheckCircle2,
  CircleAlert,
  Clock3,
  Compass,
  Copy,
  Download,
  FileSearch,
  FileText,
  ExternalLink,
  GitCompareArrows,
  Grid3X3,
  Info,
  Layers3,
  ListTree,
  Mountain,
  Printer,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Volume2,
  Workflow,
} from "lucide-react";
import { CATEGORY_LABELS, CAST_METHOD_LABELS, ELEMENT_COLORS, IMAGERY_MODULE_LABELS, IMAGERY_ROLE_LABELS, IMAGERY_STAGE_LABELS, PILLAR_LABELS, SCENE_LABELS } from "./labels";
import { CastingIdentity, DataState, Evidence, HexagramLines, HexagramTile, MissingModule, Notice, Pillars, Steps, TargetedFindings, findModule } from "./shared";

function Overview({ result, context, calendar, zhouyi, meihua, liuyao, liuren, qimen, bazi, ziwei, fengshui, onTab }) {
  const targeted = result?.targeted_deduction || result?.interpretation?.targeted_findings;
  return (
    <div className="view-stack">
      <section className="summary-band">
        <div className="summary-copy">
          <span className="eyebrow">{CATEGORY_LABELS[context.category]} · {SCENE_LABELS[context.scene]}</span>
          <h2>{context.question}</h2>
          <p>本次输出保留盘面事实与计算依据。融合周易卦德、梅花体用、六爻纳甲、六壬三传、奇门九宫与子平大运。</p>
        </div>
        <div className="summary-status">
          <CheckCircle2 size={22} />
          <div><strong>计算完成</strong><span>{result.module_results.length} 个模块</span></div>
        </div>
      </section>

      {targeted && <TargetedFindings targeted={targeted} />}

      <section className="overview-grid">
        <button className="overview-section calendar-overview" onClick={() => onTab("calendar")}>
          <div className="overview-head"><span><CalendarDays size={16} />历法基准</span><ArrowRight size={15} /></div>
          <Pillars calendar={calendar} compact />
          <p>{calendar?.lunar.month_name}月{calendar?.lunar.day_name} · {calendar?.input.timezone}</p>
        </button>

        {zhouyi && (
          <button className="overview-section" onClick={() => onTab("zhouyi")}>
            <div className="overview-head"><span><BookOpen size={16} />周易</span><ArrowRight size={15} /></div>
            <div className="overview-hexagram">
              <HexagramLines lines={zhouyi.facts.original.lines} moving={zhouyi.facts.moving_lines} />
              <div><strong>{zhouyi.facts.original.symbol} {zhouyi.facts.original.name}</strong><span>变 {zhouyi.facts.changed.name}</span></div>
            </div>
            <p>动爻：{zhouyi.facts.moving_lines.length ? zhouyi.facts.moving_lines.join("、") : "无"}</p>
          </button>
        )}

        {meihua && (
          <button className="overview-section" onClick={() => onTab("meihua")}>
            <div className="overview-head"><span><Compass size={16} />梅花易数</span><ArrowRight size={15} /></div>
            <div className="overview-hexagram">
              <HexagramLines lines={meihua.facts.original.lines} moving={meihua.facts.moving_lines} />
              <div><strong>{meihua.facts.original.symbol} {meihua.facts.original.name}</strong><span>{meihua.evidence[0]?.label}</span></div>
            </div>
            <p>体 {meihua.facts.body_use.body_trigram.name} · 用 {meihua.facts.body_use.use_trigram.name}</p>
          </button>
        )}

        {liuyao && (
          <button className="overview-section" onClick={() => onTab("liuyao")}>
            <div className="overview-head"><span><Grid3X3 size={16} />六爻纳甲</span><ArrowRight size={15} /></div>
            <div className="overview-hexagram">
              <HexagramLines lines={liuyao.facts.original.lines} moving={liuyao.facts.moving_lines} />
              <div><strong>{liuyao.facts.original.symbol} {liuyao.facts.original.name}</strong><span>{liuyao.facts.palace.name}宫 · {liuyao.facts.palace.stage}</span></div>
            </div>
            <p>世 {liuyao.facts.palace.host_line} · 应 {liuyao.facts.palace.response_line} · 空 {liuyao.facts.xun.empty_branches.join("、")}</p>
          </button>
        )}

        {liuren && (
          <button className="overview-section" onClick={() => onTab("liuren")}>
            <div className="overview-head"><span><Workflow size={16} />大六壬</span><ArrowRight size={15} /></div>
            <div className="liuren-overview-core">
              <strong>{liuren.facts.month_general.name}将</strong>
              <span>{liuren.facts.month_general.branch}加临{liuren.facts.occupation_time.branch}时</span>
            </div>
            <p>{liuren.facts.three_transmissions.status === "completed" ? `三传 ${liuren.facts.three_transmissions.transmissions.join(" · ")}` : `待补 ${liuren.facts.three_transmissions.pending_path}`}</p>
          </button>
        )}

        {qimen && (
          <button className="overview-section" onClick={() => onTab("qimen")}>
            <div className="overview-head"><span><Compass size={16} />奇门遁甲</span><ArrowRight size={15} /></div>
            <div className="qimen-overview-core">
              <strong>【{qimen.dun_type}{qimen.ju_number}局·{qimen.yuan_type}】</strong>
              <span>值符【{qimen.zhi_fu_star}】 · 值使【{qimen.zhi_shi_gate}】</span>
            </div>
            <p>三吉门落宫：{qimen.favorable_directions?.[0]?.direction}（{qimen.favorable_directions?.[0]?.gate}）</p>
          </button>
        )}

        {bazi && (
          <button className="overview-section" onClick={() => onTab("bazi")}>
            <div className="overview-head"><span><Sparkles size={16} />八字命理</span><ArrowRight size={15} /></div>
            <div className="bazi-overview-core">
              <strong>日元 {bazi.day_master}（{bazi.day_master_strength.element}）</strong>
              <span>{bazi.day_master_strength.level} · 喜【{bazi.day_master_strength.favorable_elements.join("、")}】</span>
            </div>
            <p>四柱：{bazi.facts.pillars.year.ganzhi} {bazi.facts.pillars.month.ganzhi} {bazi.facts.pillars.day.ganzhi} {bazi.facts.pillars.hour.ganzhi}</p>
          </button>
        )}

        {ziwei && (
          <button className="overview-section" onClick={() => onTab("ziwei")}>
            <div className="overview-head"><span><Sparkles size={16} />紫微斗数</span><ArrowRight size={15} /></div>
            <div className="ziwei-overview-core">
              <strong>{ziwei.facts.bureau.name}</strong>
              <span>命在{ziwei.facts.ming_palace.palace_stem_branch} · 身在{ziwei.facts.shen_palace.palace_stem_branch}</span>
            </div>
            <p>
              {ziwei.facts.palaces_by_order.find((p) => p.name === "命宫")?.main_stars.map((s) => s.name).join("、") || "命宫无主星"}
              {" · "}
              {Object.entries(ziwei.facts.si_hua).map(([k, v]) => `${v}${k}`).join(" ")}
            </p>
          </button>
        )}

        {fengshui && (
          <button className="overview-section" onClick={() => onTab("fengshui")}>
            <div className="overview-head"><span><Mountain size={16} />阳宅坐向</span><ArrowRight size={15} /></div>
            {(fengshui.facts.mode === "multiple_measurements" ? fengshui.facts.consensus.aggregate : fengshui.facts) ? (() => {
              const direction = fengshui.facts.mode === "multiple_measurements" ? fengshui.facts.consensus.aggregate : fengshui.facts;
              return (
                <>
                  <div className="direction-overview-core">
                    <div><span>坐</span><strong>{direction.sitting.mountain.name}</strong><small>{direction.true_sitting_degree}°</small></div>
                    <ArrowRight size={22} />
                    <div><span>向</span><strong>{direction.facing.mountain.name}</strong><small>{direction.true_facing_degree}°</small></div>
                  </div>
                  <p>{direction.classification_stable ? "山向分类稳定" : "测量误差跨界，需复测确认"}</p>
                </>
              );
            })() : (
              <div className="direction-overview-empty"><CircleAlert size={22} /><strong>读数不一致</strong><span>未生成合并山向</span></div>
            )}
          </button>
        )}
      </section>

      {result.advisory && (
        <section className="advisory-overview">
          <div className="advisory-overview-head">
            <div><span>结合所问事项</span><strong>{result.advisory.conclusion.headline}</strong></div>
            <button className="text-button" onClick={() => onTab("explanation")}>查看详细建议 <ArrowRight size={14} /></button>
          </div>
          <p>{result.advisory.conclusion.text}</p>
          <div className="advisory-quick-actions">
            {result.advisory.recommendations.slice(0, 2).map((recommendation) => (
              <div key={recommendation.title}>
                <strong>{recommendation.title}</strong>
                <span>{recommendation.detail}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export { Overview };
