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

function findModule(result, module) {
  return result?.module_results?.find((item) => item.module === module)?.result;
}

function DataState({ label, value, mono = false }) {
  return (
    <div className="data-state">
      <span>{label}</span>
      <strong className={mono ? "mono" : ""}>{value ?? "—"}</strong>
    </div>
  );
}

function CastingIdentity({ facts }) {
  if (!facts.method) return null;
  const derived = facts.input_lines
    ? facts.input_lines.join(" · ")
    : facts.personal_number
    ? `个体数 ${facts.personal_number}`
    : facts.report_number
    ? `报数 ${facts.report_number}`
    : "—";
  return (
    <section className="liuren-facts-band">
      <DataState label="起卦方式" value={CAST_METHOD_LABELS[facts.method] || facts.method} />
      <DataState label="派生结果" value={derived} mono />
      <DataState label="凭证哈希" value={facts.cast_nonce_hash?.slice(7, 19) || "—"} mono />
    </section>
  );
}

function HexagramLines({ lines, moving = [] }) {
  if (!lines) return null;
  return (
    <div className="hexagram-lines" aria-label="六爻卦象">
      {[...lines]
        .map((line, index) => ({ line, position: index + 1 }))
        .reverse()
        .map(({ line, position }) => (
          <div className={`yao ${line ? "yang" : "yin"} ${moving.includes(position) ? "moving" : ""}`} key={position}>
            {line ? <span /> : <><span /><span /></>}
            {moving.includes(position) && <i>{position}</i>}
          </div>
        ))}
    </div>
  );
}

function HexagramTile({ title, hexagram, moving = [], featured = false }) {
  if (!hexagram) return null;
  return (
    <div className={`hexagram-tile ${featured ? "featured" : ""}`}>
      <div className="hexagram-tile-head">
        <span>{title}</span>
        <small>第 {hexagram.ordinal} 卦</small>
      </div>
      <div className="hexagram-core">
        <HexagramLines lines={hexagram.lines} moving={moving} />
        <div>
          <div className="hexagram-name">
            <span>{hexagram.symbol}</span>
            <strong>{hexagram.name}</strong>
          </div>
          <p>{hexagram.upper_trigram.name}上 · {hexagram.lower_trigram.name}下</p>
          <div className="element-pair">
            <span>{hexagram.upper_trigram.element}</span>
            <ArrowRight size={13} />
            <span>{hexagram.lower_trigram.element}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function Pillars({ calendar, compact = false }) {
  if (!calendar) return null;
  return (
    <div className={`pillars ${compact ? "compact" : ""}`}>
      {Object.entries(calendar.pillars).slice(0, 4).map(([key, value]) => (
        <div key={key}>
          <span>{PILLAR_LABELS[key]}</span>
          <strong>{value}</strong>
          {!compact && <small>{value?.[0]} · {value?.[1]}</small>}
        </div>
      ))}
    </div>
  );
}

function Notice({ tone = "info", icon: Icon = Info, children }) {
  return (
    <div className={`notice ${tone}`}>
      <Icon size={17} />
      <div>{children}</div>
    </div>
  );
}

function Steps({ steps = [] }) {
  return (
    <div className="step-list">
      {steps.map((step) => (
        <div className="step-row" key={`${step.sequence}-${step.operation}`}>
          <span className="step-number">{step.sequence}</span>
          <div>
            <strong>{step.operation}</strong>
            <p>{step.rule_ids.join(" · ")}</p>
          </div>
          <details>
            <summary>中间值</summary>
            <pre>{JSON.stringify(step.output, null, 2)}</pre>
          </details>
        </div>
      ))}
    </div>
  );
}

function Evidence({ items = [] }) {
  if (!items.length) {
    return <div className="empty-inline">当前模块仅有盘面事实，暂无结构化规则证据。</div>;
  }
  return (
    <div className="evidence-list">
      {items.map((item) => (
        <div className="evidence-row" key={item.evidence_id}>
          <span className="evidence-mark">{item.stage === "changed" ? "变" : "本"}</span>
          <div>
            <strong>{item.label}</strong>
            <p>{item.body_element}（体） · {item.use_element}（用）</p>
          </div>
          <div className="rule-ref">{item.rule_ids.join(" · ")}</div>
        </div>
      ))}
    </div>
  );
}

function TargetedFindings({ targeted }) {
  if (!targeted || !targeted.findings || targeted.findings.length === 0) return null;
  return (
    <section className="data-band targeted-findings-band">
      <div className="band-heading">
        <div>
          <span className="band-icon"><Sparkles size={16} /></span>
          <div>
            <h3>针对所问事项 · 象数精准推断结论</h3>
            <p>基于八卦万物类象、梅花体用生克、六爻纳甲神煞与六壬神课，直接推演回答具体问题</p>
          </div>
        </div>
        <span className="version-badge">象数专项推演</span>
      </div>
      <div className="targeted-findings-lead">
        <p>{targeted.summary}</p>
      </div>
      <div className="targeted-findings-grid">
        {targeted.findings.map((item, idx) => (
          <article key={item.key || idx} className="targeted-card">
            <div className="targeted-card-header">
              <h4>{item.title}</h4>
              {item.highlight && <span className="targeted-pill">{item.highlight}</span>}
            </div>
            <div className="targeted-card-body">
              <div className="targeted-conclusion-text">
                <p>{item.conclusion}</p>
              </div>
              {item.palette && item.palette.length > 0 && (
                <div className="targeted-palette-row">
                  <span className="palette-label">推算色系：</span>
                  <div className="palette-chips">
                    {item.palette.map((color) => (
                      <span key={color} className="color-chip">{color}</span>
                    ))}
                  </div>
                </div>
              )}
              <div className="targeted-evidence-box">
                <strong>推导依据：</strong>
                <span>{item.evidence}</span>
              </div>
              <div className="targeted-rules">
                <span className="confidence-tag">{item.confidence}</span>
                {item.rules && item.rules.map((rule) => <code key={rule}>{rule}</code>)}
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function MissingModule({ name }) {
  return (
    <div className="empty-view">
      <FileSearch size={34} />
      <h2>本次未运行{name}</h2>
      <p>在左侧将体系切换为综合推演或{name}后重新计算。</p>
    </div>
  );
}

export { findModule, DataState, CastingIdentity, HexagramLines, HexagramTile, Pillars, Notice, Steps, Evidence, TargetedFindings, MissingModule };
