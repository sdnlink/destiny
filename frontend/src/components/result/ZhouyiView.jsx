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

function ZhouyiView({ result }) {
  if (!result) return <MissingModule name="周易" />;
  const { facts } = result;
  return (
    <div className="view-stack">
      <section className="view-heading">
        <div><span className="section-kicker">ZHOU YI CORE</span><h2>周易本变卦象</h2><p>本卦、变卦、互卦、错卦与综卦结构全景对照。</p></div>
        <span className="version-badge">{result.rule_version}</span>
      </section>
      <section className="hexagram-primary-grid">
        <HexagramTile title="本卦" hexagram={facts.original} moving={facts.moving_lines} featured />
        <div className="change-arrow">
          <ArrowRight size={22} />
          <span>{facts.moving_lines.length ? `第 ${facts.moving_lines.join("、")} 爻动` : "静卦无动爻"}</span>
        </div>
        <HexagramTile title="变卦" hexagram={facts.changed} featured />
      </section>
      <CastingIdentity facts={facts} />
      <section className="data-band">
        <div className="band-heading">
          <div><span className="band-icon"><Layers3 size={16} /></span><div><h3>四象演变对照</h3><p>互卦 · 错卦 · 综卦</p></div></div>
        </div>
        <div className="hexagram-secondary-grid">
          <HexagramTile title="互卦" hexagram={facts.mutual} />
          <HexagramTile title="错卦" hexagram={facts.opposite} />
          <HexagramTile title="综卦" hexagram={facts.reversed} />
        </div>
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

export { ZhouyiView };
