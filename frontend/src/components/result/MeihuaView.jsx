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

function MeihuaView({ result }) {
  if (!result) return <MissingModule name="梅花易数" />;
  const { facts } = result;
  const bodyUse = facts.body_use;
  return (
    <div className="view-stack">
      <section className="view-heading">
        <div><span className="section-kicker">MEIHUA YISHU</span><h2>梅花易数</h2><p>起卦、动爻、体用生克与五行关系分层展示。</p></div>
        <span className="version-badge">{result.rule_version}</span>
      </section>
      <section className="hexagram-primary-grid">
        <HexagramTile title="本卦" hexagram={facts.original} moving={facts.moving_lines} featured />
        <div className="change-arrow"><ArrowRight size={22} /><span>第 {facts.moving_line} 爻动</span></div>
        <HexagramTile title="变卦" hexagram={facts.changed} featured />
      </section>
      <CastingIdentity facts={facts} />
      <section className="body-use-band">
        <div className="body-use-item body">
          <span>体卦</span><strong>{bodyUse.body_trigram.symbol} {bodyUse.body_trigram.name}</strong>
          <p>{bodyUse.body_trigram.element} · {bodyUse.body_position === "upper" ? "上卦" : "下卦"}</p>
        </div>
        <div className="body-use-relation">
          <span>{result.evidence[0]?.label}</span><ArrowRight size={20} />
        </div>
        <div className="body-use-item use">
          <span>用卦</span><strong>{bodyUse.use_trigram.symbol} {bodyUse.use_trigram.name}</strong>
          <p>{bodyUse.use_trigram.element} · {bodyUse.use_position === "upper" ? "上卦" : "下卦"}</p>
        </div>
      </section>
      <section className="data-band">
        <div className="band-heading">
          <div><span className="band-icon"><ShieldCheck size={16} /></span><div><h3>关系证据</h3><p>关系事实不直接映射吉凶</p></div></div>
        </div>
        <Evidence items={result.evidence} />
      </section>
      <section className="data-band">
        <div className="band-heading">
          <div><span className="band-icon"><ListTree size={16} /></span><div><h3>计算依据</h3><p>{result.engine_version}</p></div></div>
        </div>
        <Steps steps={result.steps} />
      </section>
    </div>
  );
}

export { MeihuaView };
