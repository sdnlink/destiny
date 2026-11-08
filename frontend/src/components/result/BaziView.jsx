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
import { LifelineView } from "./LifelineView";

function BaziPillarCard({ pillar, title }) {
  if (!pillar) return null;
  return (
    <div className="bazi-pillar-card">
      <div className="bazi-pillar-header">
        <span className="pillar-title">{title}</span>
        <span className="pillar-nayin">{pillar.nayin}</span>
      </div>

      <div className="bazi-pillar-main">
        <div className="ganzhi-box stem">
          <span className="ten-god-tag">{pillar.stem_ten_god}</span>
          <strong className="ganzhi-char" style={{ color: ELEMENT_COLORS[pillar.stem_element] || "inherit" }}>
            {pillar.stem}
          </strong>
          <small className="element-label">{pillar.stem_element}</small>
        </div>

        <div className="ganzhi-box branch">
          <span className="stage-tag">{pillar.twelve_stage}</span>
          <strong className="ganzhi-char" style={{ color: ELEMENT_COLORS[pillar.branch_element] || "inherit" }}>
            {pillar.branch}
          </strong>
          <small className="element-label">{pillar.branch_element}</small>
        </div>
      </div>

      <div className="bazi-hidden-section">
        <span className="hidden-label">地支藏干</span>
        <div className="hidden-stems-list">
          {pillar.hidden_stems.map((h, i) => (
            <div key={i} className="hidden-stem-item">
              <span className="h-stem" style={{ color: ELEMENT_COLORS[h.element] || "inherit" }}>{h.stem}</span>
              <span className="h-god">{h.ten_god}</span>
              <span className="h-type">{h.type}</span>
            </div>
          ))}
        </div>
      </div>

      {pillar.shensha && pillar.shensha.length > 0 && (
        <div className="bazi-shensha-section">
          {pillar.shensha.map((s) => (
            <span key={s} className="bazi-shensha-tag">{s}</span>
          ))}
        </div>
      )}
    </div>
  );
}

function BaziView({ result, calendar }) {
  if (!result) return <MissingModule name="八字命理" />;
  const facts = result.facts || {};
  const pillars = facts.pillars || {};
  const strength = result.day_master_strength || facts.day_master_strength || {};
  const distribution = result.element_distribution || facts.element_distribution || [];
  const luckPillars = result.luck_pillars || facts.luck_pillars || [];
  const luckInfo = result.luck_start_info || facts.luck_start_info || {};
  const advisory = result.advisory || {};

  return (
    <div className="view-stack">
      <section className="view-heading">
        <div>
          <span className="section-kicker">BAZI ZIPING FOUR PILLARS</span>
          <h2>八字四柱与大运排盘</h2>
          <p>子平正统四柱排盘、藏干十神、五行旺衰强弱、吉凶神煞与大运起运推演。</p>
        </div>
        <span className="version-badge">{result.rule_id}</span>
      </section>

      <section className="liuren-facts-band">
        <DataState label="日元命主" value={`${result.day_master}（${strength.element}）`} />
        <DataState label="命造性别" value={result.gender === "男" ? "乾造（男命）" : "坤造（女命）"} />
        <DataState label="公历时刻" value={result.solar_datetime} />
        <DataState label="农历生辰" value={result.lunar_datetime} />
      </section>

      <section className="data-band">
        <div className="band-heading">
          <div><span className="band-icon"><Sparkles size={16} /></span><div><h3>四柱八字神煞全盘</h3><p>年柱根基 · 月柱提纲 · 日柱自身 · 时柱归宿</p></div></div>
        </div>
        <div className="bazi-pillars-grid">
          <BaziPillarCard pillar={pillars.year} title="年柱（祖荫父母）" />
          <BaziPillarCard pillar={pillars.month} title="月柱（事业提纲）" />
          <BaziPillarCard pillar={pillars.day} title="日柱（日元坐下）" />
          <BaziPillarCard pillar={pillars.hour} title="时柱（子女晚景）" />
        </div>
      </section>

      <section className="bazi-analysis-grid">
        <div className="data-band strength-band">
          <div className="band-heading">
            <div><span className="band-icon"><ShieldCheck size={16} /></span><div><h3>日主强弱与喜忌五行</h3><p>{strength.analysis?.summary || ""}</p></div></div>
          </div>
          <div className="bazi-strength-content">
            <div className="strength-header-pill">
              <span className="master-title">日元【{strength.day_master}{strength.element}】</span>
              <span className={`strength-level-badge level-${strength.level}`}>{strength.level}</span>
              <span className="strength-score">综合评分 {strength.score} / 100</span>
            </div>
            <div className="favorable-pill-row">
              <div className="fav-group">
                <span className="group-label">喜用五行：</span>
                {strength.favorable_elements?.map((elem) => (
                  <span key={elem} className="elem-pill fav" style={{ backgroundColor: `${ELEMENT_COLORS[elem]}20`, color: ELEMENT_COLORS[elem], borderColor: ELEMENT_COLORS[elem] }}>
                    {elem}
                  </span>
                ))}
              </div>
              <div className="fav-group">
                <span className="group-label">忌神五行：</span>
                {strength.unfavorable_elements?.map((elem) => (
                  <span key={elem} className="elem-pill unfav" style={{ backgroundColor: `${ELEMENT_COLORS[elem]}15`, color: ELEMENT_COLORS[elem] }}>
                    {elem}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="data-band distribution-band">
          <div className="band-heading">
            <div><span className="band-icon"><Layers3 size={16} /></span><div><h3>全局五行能量分布</h3><p>综合四柱天干与地支藏干权重折算</p></div></div>
          </div>
          <div className="bazi-elements-meter">
            {distribution.map((item) => (
              <div key={item.element} className="meter-row">
                <div className="meter-info">
                  <span className="meter-elem" style={{ color: ELEMENT_COLORS[item.element] || "inherit" }}>
                    {item.element}
                  </span>
                  <span className="meter-score">{item.score} 分</span>
                  <span className="meter-pct">{item.percentage}%</span>
                </div>
                <div className="meter-bar-track">
                  <div
                    className="meter-bar-fill"
                    style={{
                      width: `${Math.min(item.percentage, 100)}%`,
                      backgroundColor: ELEMENT_COLORS[item.element] || "#a66d1e",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="data-band">
        <div className="band-heading">
          <div>
            <span className="band-icon"><Clock3 size={16} /></span>
            <div>
              <h3>大运排盘与起运流年</h3>
              <p>{luckInfo.description || `大运【${luckInfo.direction}】`}</p>
            </div>
          </div>
          <span className="luck-direction-badge">{luckInfo.direction}</span>
        </div>
        <div className="bazi-luck-timeline">
          {luckPillars.map((luck) => (
            <div key={luck.index} className="bazi-luck-card">
              <span className="luck-order">第 {luck.index} 步大运</span>
              <strong className="luck-ganzhi">{luck.ganzhi}</strong>
              <span className="luck-god">{luck.stem_ten_god}</span>
              <span className="luck-nayin">{luck.nayin}</span>
              <div className="luck-ages">
                <b>{luck.start_age} - {luck.end_age} 岁</b>
                <small>{luck.start_year} - {luck.end_year} 年</small>
              </div>
            </div>
          ))}
        </div>
      </section>

      <LifelineView result={result} calendar={calendar} />

      {advisory && Object.keys(advisory).length > 0 && (
        <section className="data-band advisory-band">
          <div className="band-heading">
            <div><span className="band-icon"><BookOpen size={16} /></span><div><h3>子平命理研判与调候指引</h3><p>结合五行喜用流通与事项策略</p></div></div>
          </div>
          <div className="bazi-advisory-cards">
            {advisory.general && (
              <div className="bazi-adv-card">
                <strong>【全局调候】</strong>
                <p>{advisory.general}</p>
              </div>
            )}
            {advisory.career && (
              <div className="bazi-adv-card">
                <strong>【事业进取】</strong>
                <p>{advisory.career}</p>
              </div>
            )}
            {advisory.wealth && (
              <div className="bazi-adv-card">
                <strong>【求财之道】</strong>
                <p>{advisory.wealth}</p>
              </div>
            )}
            {advisory.health && (
              <div className="bazi-adv-card">
                <strong>【养生调理】</strong>
                <p>{advisory.health}</p>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}

export { BaziView };
