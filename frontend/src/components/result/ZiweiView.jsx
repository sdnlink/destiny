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

function ZiweiPalaceCard({ palace, isSelected, isSanFang, onClick }) {
  if (!palace) return null;
  const isMing = palace.name === "命宫";
  return (
    <div
      className={`ziwei-cell ${isMing ? "is-ming" : ""} ${palace.is_body_palace ? "is-shen" : ""} ${isSelected ? "is-selected" : ""} ${isSanFang ? "is-sanfang" : ""}`}
      onClick={() => onClick && onClick(palace.earthly_branch)}
      style={{ cursor: "pointer" }}
    >
      <div className="ziwei-cell-header">
        <span className="ziwei-palace-name">
          {palace.name}
          {palace.is_body_palace && <span className="ziwei-shen-badge">身</span>}
        </span>
        <span className="ziwei-palace-stem">{palace.palace_stem_branch}</span>
      </div>

      <div className="ziwei-stars-area">
        <div className="ziwei-main-stars">
          {palace.main_stars.map((star) => (
            <div key={star.name} className="ziwei-star main">
              <span className="star-name">{star.name}</span>
              {star.si_hua && <span className={`sihua-badge ${star.si_hua}`}>{star.si_hua}</span>}
            </div>
          ))}
        </div>

        <div className="ziwei-lucky-stars">
          {palace.lucky_stars.map((star) => (
            <span key={star.name} className="ziwei-star lucky">
              {star.name}
              {star.si_hua && <span className={`sihua-badge mini ${star.si_hua}`}>{star.si_hua}</span>}
            </span>
          ))}
        </div>

        <div className="ziwei-bad-stars">
          {palace.bad_stars.map((star) => (
            <span key={star.name} className="ziwei-star bad">{star.name}</span>
          ))}
        </div>

        {(palace.minor_stars || []).length > 0 && (
          <div className="ziwei-minor-stars">
            {palace.minor_stars.map((star) => (
              <span key={star.name} className="ziwei-star minor">{star.name}</span>
            ))}
          </div>
        )}
      </div>

      <div className="ziwei-cell-footer">
        <span className="ziwei-limit">{palace.major_limit_start}-{palace.major_limit_end}</span>
        <span className="ziwei-branch-name">{palace.earthly_branch}</span>
      </div>
    </div>
  );
}

const BRANCH_RING = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];

function ZiweiView({ result }) {
  const [selectedBranch, setSelectedBranch] = useState("寅");

  if (!result) return <MissingModule name="紫微斗数" />;
  const facts = result.facts;
  const branchMap = {};
  facts.palaces_by_branch.forEach((p) => {
    branchMap[p.earthly_branch] = p;
  });

  const limitPalaces = [...facts.palaces_by_branch]
    .filter((palace) => Number.isFinite(Number(palace.major_limit_start)))
    .sort((left, right) => Number(left.major_limit_start) - Number(right.major_limit_start));

  const currIdx = BRANCH_RING.indexOf(selectedBranch);
  const oppBranch = BRANCH_RING[(currIdx + 6) % 12];
  const trine1Branch = BRANCH_RING[(currIdx + 4) % 12];
  const trine2Branch = BRANCH_RING[(currIdx + 8) % 12];
  const sanFangBranches = new Set([oppBranch, trine1Branch, trine2Branch]);

  return (
    <div className="view-stack">
      <section className="view-heading">
        <div>
          <span className="section-kicker">ZI WEI DOU SHU NATAL CHART</span>
          <h2>紫微斗数全景天盘</h2>
          <p>十二宫位、五行局、十四正曜与生年四化交互命盘（点击宫位查看三方四正对宫关联）。</p>
        </div>
        <span className="version-badge">{result.rule_version}</span>
      </section>

      <section className="liuren-facts-band">
        <DataState label="五行局" value={`${facts.bureau.name}（${facts.bureau.nayin}）`} />
        <DataState label="乾坤造" value={facts.yin_yang_gender} />
        <DataState label="大限方向" value={facts.is_forward_decade ? "顺行大限" : "逆行大限"} />
        <DataState label="命主 / 身主" value={`${facts.ming_zhu} / ${facts.shen_zhu}`} />
      </section>

      <section className="ziwei-plate-wrapper">
        <div className="ziwei-plate-grid">
          <div className="grid-cell p-si"><ZiweiPalaceCard palace={branchMap["巳"]} isSelected={selectedBranch === "巳"} isSanFang={sanFangBranches.has("巳")} onClick={setSelectedBranch} /></div>
          <div className="grid-cell p-wu"><ZiweiPalaceCard palace={branchMap["午"]} isSelected={selectedBranch === "午"} isSanFang={sanFangBranches.has("午")} onClick={setSelectedBranch} /></div>
          <div className="grid-cell p-wei"><ZiweiPalaceCard palace={branchMap["未"]} isSelected={selectedBranch === "未"} isSanFang={sanFangBranches.has("未")} onClick={setSelectedBranch} /></div>
          <div className="grid-cell p-shen"><ZiweiPalaceCard palace={branchMap["申"]} isSelected={selectedBranch === "申"} isSanFang={sanFangBranches.has("申")} onClick={setSelectedBranch} /></div>

          <div className="grid-cell p-chen"><ZiweiPalaceCard palace={branchMap["辰"]} isSelected={selectedBranch === "辰"} isSanFang={sanFangBranches.has("辰")} onClick={setSelectedBranch} /></div>
          <div className="grid-center-plate">
            <div className="center-info-content">
              <h3>紫微斗数命盘 · 交互中宫</h3>
              <div className="center-info-grid">
                <div><b>生辰八字：</b><span>{facts.four_pillars.year}年 {facts.four_pillars.month}月 {facts.four_pillars.day}日 {facts.four_pillars.hour}时</span></div>
                <div><b>农历日期：</b><span>{facts.lunar_calendar.lunar_year}年 {facts.lunar_calendar.is_leap ? "闰" : ""}{facts.lunar_calendar.lunar_month}月{facts.lunar_calendar.lunar_day}日</span></div>
                <div><b>格局属性：</b><span>{facts.yin_yang_gender} · {facts.bureau.name}</span></div>
                <div><b>当前聚焦：</b><span className="highlight-tag">{branchMap[selectedBranch]?.name || "宫位"}（{selectedBranch}宫）</span></div>
              </div>
              <div className="center-sihua-row">
                <span className="sihua-title">生年四化：</span>
                {Object.entries(facts.si_hua).map(([k, v]) => (
                  <span key={k} className={`sihua-tag ${k}`}>{v}{k}</span>
                ))}
              </div>
            </div>
          </div>
          <div className="grid-cell p-you"><ZiweiPalaceCard palace={branchMap["酉"]} isSelected={selectedBranch === "酉"} isSanFang={sanFangBranches.has("酉")} onClick={setSelectedBranch} /></div>

          <div className="grid-cell p-mao"><ZiweiPalaceCard palace={branchMap["卯"]} isSelected={selectedBranch === "卯"} isSanFang={sanFangBranches.has("卯")} onClick={setSelectedBranch} /></div>
          <div className="grid-cell p-xu"><ZiweiPalaceCard palace={branchMap["戌"]} isSelected={selectedBranch === "戌"} isSanFang={sanFangBranches.has("戌")} onClick={setSelectedBranch} /></div>

          <div className="grid-cell p-yin"><ZiweiPalaceCard palace={branchMap["寅"]} isSelected={selectedBranch === "寅"} isSanFang={sanFangBranches.has("寅")} onClick={setSelectedBranch} /></div>
          <div className="grid-cell p-chou"><ZiweiPalaceCard palace={branchMap["丑"]} isSelected={selectedBranch === "丑"} isSanFang={sanFangBranches.has("丑")} onClick={setSelectedBranch} /></div>
          <div className="grid-cell p-zi"><ZiweiPalaceCard palace={branchMap["子"]} isSelected={selectedBranch === "子"} isSanFang={sanFangBranches.has("子")} onClick={setSelectedBranch} /></div>
          <div className="grid-cell p-hai"><ZiweiPalaceCard palace={branchMap["亥"]} isSelected={selectedBranch === "亥"} isSanFang={sanFangBranches.has("亥")} onClick={setSelectedBranch} /></div>
        </div>
      </section>

      {limitPalaces.length > 0 && (
        <section className="ziwei-limit-section">
          <div className="band-heading">
            <div>
              <span className="band-icon"><ListTree size={16} /></span>
              <div>
                <h3>大限区间</h3>
                <p>按起运年龄排序，点击区间可回到对应宫位；只列宫位与大限区间事实，不生成大限断语。</p>
              </div>
            </div>
          </div>
          <div className="ziwei-limit-grid">
            {limitPalaces.map((palace) => (
              <button
                key={palace.earthly_branch}
                type="button"
                className={`ziwei-limit-item ${selectedBranch === palace.earthly_branch ? "is-selected" : ""}`}
                onClick={() => setSelectedBranch(palace.earthly_branch)}
              >
                <span className="ziwei-limit-range">
                  {palace.major_limit_start}–{palace.major_limit_end} 岁
                </span>
                <strong>{palace.name}</strong>
                <span className="ziwei-limit-meta">
                  {palace.heavenly_stem}{palace.earthly_branch}
                  {palace.main_stars?.length ? ` · ${palace.main_stars.map((star) => star.name).join("、")}` : ""}
                </span>
              </button>
            ))}
          </div>
        </section>
      )}

      <section className="data-band">
        <div className="band-heading"><div><span className="band-icon"><ListTree size={16} /></span><div><h3>推演步骤</h3><p>{result.engine_version}</p></div></div></div>
        <Steps steps={result.steps} />
      </section>
    </div>
  );
}

export { ZiweiView };
