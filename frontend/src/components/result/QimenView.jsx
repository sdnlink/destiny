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

function QimenPalaceCard({ palace, isZhiFu, isZhiShi }) {
  if (!palace) return null;
  return (
    <div className={`qimen-cell p-${palace.palace_number} ${isZhiFu ? "is-zhifu" : ""} ${isZhiShi ? "is-zhishi" : ""}`}>
      <div className="qimen-cell-header">
        <span className="qimen-palace-name">{palace.palace_name}</span>
        <span className="qimen-palace-dir">{palace.direction} · {palace.element}</span>
      </div>

      {/* 神盘 */}
      <div className="qimen-spirit-row">
        <span className="qimen-spirit-tag">{palace.eight_spirit}</span>
        {isZhiFu && <span className="zhifu-badge">值符星</span>}
        {isZhiShi && <span className="zhishi-badge">值使门</span>}
      </div>

      {/* 天盘九星与天盘奇仪 */}
      <div className="qimen-star-stem-row">
        <span className="qimen-star">{palace.nine_star}</span>
        <strong className="qimen-tian-stem" style={{ color: ELEMENT_COLORS[palace.element] || "inherit" }}>
          {palace.tian_pan_stem}
        </strong>
        {palace.is_tian_qin_present && (
          <small className="qin-stem-tag">禽{palace.qin_stem}</small>
        )}
      </div>

      {/* 人盘八门 */}
      <div className="qimen-gate-row">
        <span className={`qimen-gate ${["开门", "休门", "生门"].includes(palace.eight_gate) ? "auspicious-gate" : palace.eight_gate === "死门" ? "dead-gate" : ""}`}>
          {palace.eight_gate}
        </span>
      </div>

      {/* 地盘奇仪 */}
      <div className="qimen-di-stem-row">
        <small className="di-stem-label">地盘</small>
        <span className="qimen-di-stem">{palace.di_pan_stem}</span>
      </div>

      {/* 格局标签 */}
      {palace.patterns && palace.patterns.length > 0 && (
        <div className="qimen-pattern-tags">
          {palace.patterns.map((pat) => (
            <span key={pat.name} className={`qimen-pattern-pill ${pat.type}`} title={pat.desc}>
              {pat.name}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function QimenView({ result }) {
  if (!result) return <MissingModule name="奇门遁甲" />;
  const palaces = result.palaces || {};
  const favs = result.favorable_directions || [];
  const advisory = result.advisory || {};

  return (
    <div className="view-stack">
      <section className="view-heading">
        <div>
          <span className="section-kicker">QIMEN DUNJIA TIME CHART</span>
          <h2>时家转盘奇门遁甲</h2>
          <p>拆补法定局、地盘三奇六仪、转盘九星、八门、八神排布与奇门吉凶格局。</p>
        </div>
        <span className="version-badge">{result.rule_id}</span>
      </section>

      <section className="liuren-facts-band">
        <DataState label="定局局象" value={`【${result.dun_type}${result.ju_number}局 · ${result.yuan_type}】`} />
        <DataState label="当前节气" value={result.solar_term} />
        <DataState label="时辰旬首" value={result.xun_shou} />
        <DataState label="值符星 / 值使门" value={`【${result.zhi_fu_star}】落${result.zhi_fu_palace}宫 / 【${result.zhi_shi_gate}】落${result.zhi_shi_palace}宫`} />
      </section>

      {/* 洛书九宫方阵 (Row 1: 4, 9, 2; Row 2: 3, 5, 7; Row 3: 8, 1, 6) */}
      <section className="qimen-plate-wrapper">
        <div className="qimen-grid">
          <QimenPalaceCard palace={palaces[4]} isZhiFu={result.zhi_fu_palace === 4} isZhiShi={result.zhi_shi_palace === 4} />
          <QimenPalaceCard palace={palaces[9]} isZhiFu={result.zhi_fu_palace === 9} isZhiShi={result.zhi_shi_palace === 9} />
          <QimenPalaceCard palace={palaces[2]} isZhiFu={result.zhi_fu_palace === 2} isZhiShi={result.zhi_shi_palace === 2} />

          <QimenPalaceCard palace={palaces[3]} isZhiFu={result.zhi_fu_palace === 3} isZhiShi={result.zhi_shi_palace === 3} />
          <QimenPalaceCard palace={palaces[5]} isZhiFu={result.zhi_fu_palace === 5} isZhiShi={result.zhi_shi_palace === 5} />
          <QimenPalaceCard palace={palaces[7]} isZhiFu={result.zhi_fu_palace === 7} isZhiShi={result.zhi_shi_palace === 7} />

          <QimenPalaceCard palace={palaces[8]} isZhiFu={result.zhi_fu_palace === 8} isZhiShi={result.zhi_shi_palace === 8} />
          <QimenPalaceCard palace={palaces[1]} isZhiFu={result.zhi_fu_palace === 1} isZhiShi={result.zhi_shi_palace === 1} />
          <QimenPalaceCard palace={palaces[6]} isZhiFu={result.zhi_fu_palace === 6} isZhiShi={result.zhi_shi_palace === 6} />
        </div>
      </section>

      {/* 吉方研判 */}
      {favs.length > 0 && (
        <section className="data-band">
          <div className="band-heading">
            <div><span className="band-icon"><Compass size={16} /></span><div><h3>奇门优选用事方位</h3><p>三吉门（开、休、生）结合三奇与吉神优选</p></div></div>
          </div>
          <div className="qimen-fav-grid">
            {favs.map((f) => (
              <div key={f.palace_number} className="qimen-fav-card">
                <div className="fav-card-head">
                  <strong className="fav-dir">{f.direction}（{f.palace_name}）</strong>
                  <span className="fav-score-badge">吉度 {f.score} 分</span>
                </div>
                <div className="fav-elements-row">
                  <span className="fav-gate">{f.gate}</span>
                  <span className="fav-star">{f.star}</span>
                  <span className="fav-spirit">{f.spirit}</span>
                </div>
                <p className="fav-summary">{f.summary}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 奇门决策策略 */}
      {advisory && (
        <section className="data-band advisory-band">
          <div className="band-heading">
            <div><span className="band-icon"><BookOpen size={16} /></span><div><h3>奇门运筹与决策策略</h3><p>审机夺势，动静有常</p></div></div>
          </div>
          <div className="bazi-advisory-cards">
            <div className="bazi-adv-card">
              <strong>【局象综述】</strong>
              <p>{advisory.general}</p>
            </div>
            <div className="bazi-adv-card">
              <strong>【用事行动】</strong>
              <p>{advisory.action}</p>
            </div>
            <div className="bazi-adv-card" style={{ gridColumn: "1 / -1" }}>
              <strong>【运筹谋略】</strong>
              <p>{advisory.strategy}</p>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

export { QimenView };
