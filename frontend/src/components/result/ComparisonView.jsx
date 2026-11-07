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

function ComparisonView({ comparison }) {
  if (!comparison) return <MissingModule name="对照分析" />;

  const consistentItems = comparison.consistent || comparison.agreements || [];
  const conflictItems = comparison.conflicts || [];
  const complementaryItems = comparison.complementary || [];
  const indeterminateItems = [
    ...(comparison.indeterminate || []),
    ...(comparison.undetermined || []),
    ...(comparison.unpaired || []),
  ];
  const excludedItems = comparison.excluded || [];

  const counts = comparison.counts || {
    consistent: consistentItems.length,
    conflicts: conflictItems.length,
    complementary: complementaryItems.length,
    indeterminate: indeterminateItems.length,
    excluded: excludedItems.length,
  };

  const categories = [
    { title: "确定性直接重合 (Consistent)", items: consistentItems, tone: "agreement", desc: "各术数体系在同维度和时段具有同向判定" },
    { title: "规则冲突或分歧 (Conflicts)", items: conflictItems, tone: "conflict", desc: "各术数体系在同一维度出现吉凶方向对立" },
    { title: "互补证据与类象 (Complementary)", items: complementaryItems, tone: "complementary", desc: "各术数体系相互补充不同侧面的证据与线索" },
    { title: "系统边界与未配对 (Indeterminate / Unpaired)", items: indeterminateItems, tone: "undetermined", desc: "仅单系统具备判定或处于无法决定的边界状态" },
  ];

  return (
    <div className="view-stack">
      <section className="view-heading">
        <div>
          <span className="section-kicker">CROSS-DISCIPLINE COMPARISON</span>
          <h2>多模块推演对照分析</h2>
          <p>仅比较结构化规则证据与盘面事实，保持学术客观性，不强制合并吉凶。</p>
        </div>
        <span className="version-badge">{comparison.strategy || comparison.rule_version || "evidence-comparison"}</span>
      </section>

      {comparison.notices?.length > 0 && (
        <div className="comparison-notices">
          {comparison.notices.map((notice, idx) => (
            <Notice key={idx} tone="info" icon={Info}>{notice}</Notice>
          ))}
        </div>
      )}

      <section className="comparison-counts">
        <DataState label="同向重合" value={counts.consistent ?? consistentItems.length} />
        <DataState label="冲突分歧" value={counts.conflicts ?? conflictItems.length} />
        <DataState label="互补补充" value={counts.complementary ?? complementaryItems.length} />
        <DataState label="边界/独立" value={counts.indeterminate ?? indeterminateItems.length} />
      </section>

      {categories.map(({ title, items, tone, desc }) => (
        <section className={`data-band ${tone}-band`} key={title}>
          <div className="band-heading">
            <div>
              <span className="band-icon"><GitCompareArrows size={16} /></span>
              <div>
                <h3>{title}</h3>
                <p>{desc} · 共 {items.length} 组</p>
              </div>
            </div>
          </div>
          {items.length ? (
            <div className="comparison-items">
              {items.map((item, idx) => {
                const isGroup = Array.isArray(item.judgements);
                const titleText = isGroup ? `【${item.dimension}】${item.time_range ? JSON.stringify(item.time_range) : ""}` : item.title;
                const polarities = item.polarities || [item.polarity].filter(Boolean);
                const judgements = item.judgements || [item];

                return (
                  <article className="comparison-card" key={item.item_id || `${item.dimension}-${idx}`}>
                    <header>
                      <strong>{titleText}</strong>
                      <div className="module-tags">
                        {polarities.map((p) => (
                          <span key={p} className={`polarity-tag ${p}`}>{p}</span>
                        ))}
                      </div>
                    </header>
                    {item.description && <p>{item.description}</p>}
                    <div className="comparison-judgements-list">
                      {judgements.map((j, jIdx) => (
                        <div key={j.judgement_id || jIdx} className="comparison-judgement-row">
                          <span className="judgement-system-tag">{j.system}</span>
                          <span className="judgement-id">{j.judgement_id}</span>
                          <span className={`judgement-pol ${j.polarity}`}>{j.polarity}</span>
                          {j.rule_ids?.length > 0 && (
                            <div className="rule-ref">{j.rule_ids.join(" · ")}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </article>
                );
              })}
            </div>
          ) : <div className="empty-inline">本次推演中未检测到该类关系。</div>}
        </section>
      ))}

      {excludedItems.length > 0 && (
        <section className="data-band conflict-band">
          <div className="band-heading">
            <div>
              <span className="band-icon"><CircleAlert size={16} /></span>
              <div>
                <h3>已排除判定 (Excluded)</h3>
                <p>未发布或结构不完整规则，已从对照中隔离 · 共 {excludedItems.length} 项</p>
              </div>
            </div>
          </div>
          <div className="comparison-items">
            {excludedItems.map((ex, idx) => (
              <div key={idx} className="excluded-row">
                <strong>{ex.judgement_id || ex.system}</strong>
                <span>原因：{ex.reasons?.join("；")}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export { ComparisonView };
