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

function ExplanationView({ explanation, advisory, literature, imagery, yuanHui, interpretation }) {
  const icons = { zhouyi: BookOpen, meihua: Compass, liuyao: Grid3X3, liuren: Workflow, qimen: Compass, bazi: Sparkles, ziwei: Sparkles, fengshui: Mountain };

  const targeted = interpretation?.targeted_findings;

  return (
    <div className="view-stack">
      <section className="view-heading">
        <div>
          <span className="section-kicker">ADVISORY & CORPUS INSIGHTS</span>
          <h2>综合推演研判与古籍引证</h2>
          <p>融合事项研判策略、卦象含义、3300万字经典古籍引证与多维决策清单。</p>
        </div>
        <span className="version-badge">{advisory?.schema_version || "2.0"}</span>
      </section>

      {targeted && <TargetedFindings targeted={targeted} />}

      {advisory && (
        <>
          <section className="advisory-headline-card">
            <div className="advisory-headline-badge">{advisory.context.category_label}领域 · 核心研判</div>
            <h3>{advisory.conclusion.headline}</h3>
            <p className="advisory-headline-summary">{advisory.conclusion.text}</p>
          </section>

          {advisory.multi_system_resonance && (
            <section className="data-band resonance-band">
              <div className="band-heading">
                <div>
                  <span className="band-icon"><Sparkles size={16} /></span>
                  <div>
                    <h3>多术数立体共振指数与交叉印证矩阵</h3>
                    <p>综合周易、梅花、六爻、六壬、奇门与八字之数理多维共振打分</p>
                  </div>
                </div>
                <div className="resonance-badge-group">
                  <span className="resonance-score-pill">共振指数 {advisory.multi_system_resonance.score}%</span>
                  <span className="resonance-level-tag">{advisory.multi_system_resonance.level}</span>
                </div>
              </div>

              <div className="resonance-banner">
                <div className="resonance-meter">
                  <div className="resonance-meter-fill" style={{ width: `${advisory.multi_system_resonance.score}%` }} />
                </div>
                <p className="resonance-desc">{advisory.multi_system_resonance.description}</p>
              </div>

              {/* 交叉印证对照方阵 */}
              <div className="resonance-matrix-grid">
                {advisory.multi_system_resonance.matrix.map((item) => (
                  <div key={item.system_id} className={`res-card stance-${item.stance_type}`}>
                    <div className="res-card-head">
                      <strong>{item.system_name}</strong>
                      <span className={`res-stance-pill ${item.stance_type}`}>{item.stance_label}</span>
                    </div>
                    <p className="res-evidence">{item.key_evidence}</p>
                    <small className="res-focus">{item.element_focus}</small>
                  </div>
                ))}
              </div>

              {/* 共识与张力 */}
              <div className="resonance-insights-row">
                <div className="res-insight-col synergy">
                  <strong>💡 核心共振契合点</strong>
                  <ul>
                    {advisory.multi_system_resonance.synergies.map((s, idx) => (
                      <li key={idx}>{s}</li>
                    ))}
                  </ul>
                </div>
                <div className="res-insight-col tension">
                  <strong>⚠️ 交叉张力与风控防范</strong>
                  <ul>
                    {advisory.multi_system_resonance.tensions.map((t, idx) => (
                      <li key={idx}>{t}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </section>
          )}

          <section className="advisory-domain-grid">
            <div className="data-band domain-status-band">
              <div className="band-heading">
                <div><span className="band-icon"><CheckCircle2 size={16} /></span><div><h3>现状与格局剖析</h3><p>立足当前基本面与各系统定位</p></div></div>
              </div>
              <ul className="styled-list">
                {advisory.domain_analysis.status_quo.map((point, i) => <li key={i}>{point}</li>)}
              </ul>
            </div>

            <div className="data-band domain-trend-band">
              <div className="band-heading">
                <div><span className="band-icon"><ArrowRight size={16} /></span><div><h3>演变趋向与关口</h3><p>动变爻位、三传发端与运势流转</p></div></div>
              </div>
              <ul className="styled-list">
                {advisory.domain_analysis.trend_evolution.map((point, i) => <li key={i}>{point}</li>)}
              </ul>
            </div>

            <div className="data-band domain-risk-band">
              <div className="band-heading">
                <div><span className="band-icon"><CircleAlert size={16} /></span><div><h3>潜在盲区与风险点</h3><p>化忌考验、动爻生克与决策红线</p></div></div>
              </div>
              <ul className="styled-list">
                {advisory.domain_analysis.risk_and_pitfalls.map((point, i) => <li key={i}>{point}</li>)}
              </ul>
            </div>
          </section>

          <section className="data-band advisory-recommendations-band">
            <div className="band-heading">
              <div><span className="band-icon"><ShieldCheck size={16} /></span><div><h3>分阶段落地行动策略</h3><p>象法指导、卦德践行与务实风控结合</p></div></div>
            </div>
            <div className="advisory-recs-list">
              {advisory.recommendations.map((recommendation) => (
                <div className="rec-card" key={recommendation.title}>
                  <div className="rec-priority">{recommendation.priority}</div>
                  <div className="rec-body">
                    <div className="rec-top">
                      <h4>{recommendation.title}</h4>
                      <span className="rec-phase-tag">{recommendation.phase}</span>
                    </div>
                    <p>{recommendation.detail}</p>
                    <small>依据与原理：{recommendation.basis}</small>
                    <div className="explanation-rules">
                      {recommendation.rule_ids.map((rule) => <code key={rule}>{rule}</code>)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="advisory-support-grid">
            <div className="data-band verification-band">
              <div className="band-heading">
                <div><span className="band-icon"><FileSearch size={16} /></span><div><h3>关键决策核实清单</h3><p>在采取不可逆行动前逐一回答</p></div></div>
              </div>
              <ol className="styled-ol">{advisory.verification_questions.map((question) => <li key={question}>{question}</li>)}</ol>
            </div>
            <div className="data-band basis-band">
              <div className="band-heading">
                <div><span className="band-icon"><ListTree size={16} /></span><div><h3>推演事实依据</h3><p>本次建议引用的数理结构事实</p></div></div>
              </div>
              {advisory.evidence_basis.length ? advisory.evidence_basis.map((basis, idx) => (
                <div className="advisory-basis-row" key={idx}>
                  <strong>{basis.module === "zhouyi" ? "周易" : basis.module === "meihua" ? "梅花" : basis.module === "bazi" ? "八字" : basis.module === "qimen" ? "奇门" : basis.module}</strong>
                  <span>{basis.fact}</span>
                  <code>{basis.rule_ids.join(" · ")}</code>
                </div>
              )) : <p className="empty-inline">融合周易卦德、梅花体用、六爻世应、子平八字与紫微命盘事实。</p>}
            </div>
          </section>
        </>
      )}

      <section className="data-band literature-band">
        <div className="band-heading">
          <div>
            <span className="band-icon"><BookOpen size={16} /></span>
            <div>
              <h3>典籍引证与高价值古籍断语</h3>
              <p>从 3300 万字经典古籍库中精准召回与本次卦象、日主及事项高度相关的断语</p>
            </div>
          </div>
          <span className={`literature-status ${literature?.status || "unavailable"}`}>{literature?.status || "unavailable"}</span>
        </div>
        {literature?.books?.length ? (
          <div className="literature-list">
            {literature.books.map((book) => (
              <article className="literature-item" key={book.citation_id}>
                <header>
                  <div>
                    <span>{book.citation_id}</span>
                    <h4>《{book.title}》</h4>
                    {book.is_fallback && <span className="fallback-badge">内置经典库</span>}
                  </div>
                  <div className="lit-meta-right">
                    <span className="relevance-score-badge">相关度 {book.relevance_score}</span>
                    <small>{book.calculation_role} · 匹配“{book.matched_term}”</small>
                  </div>
                </header>
                <blockquote>{book.excerpt}</blockquote>
                <div className="book-opinion">
                  <strong>书中观点</strong>
                  <p>{book.book_opinion}</p>
                </div>
                <div className="book-application">
                  <strong>当前事项参考</strong>
                  <p>{book.application_note}</p>
                </div>
                <footer>
                  <span>{book.chunk_id} · hash {book.content_sha256?.slice(0, 12)}</span>
                  <a href={book.source_url} target="_blank" rel="noreferrer">查看来源 <ExternalLink size={13} /></a>
                </footer>
              </article>
            ))}
          </div>
        ) : (
          <Notice tone="neutral" icon={BookOpen}>{literature?.warnings?.[0] || "当前没有找到与卦象直接匹配的书籍片段。"}</Notice>
        )}
        {literature?.warnings?.map((warning) => (
          <Notice tone="warning" icon={CircleAlert} key={warning}>{warning}</Notice>
        ))}
      </section>

      {interpretation && (
        <section className="data-band correspondence-band">
          <div className="band-heading">
            <div>
              <span className="band-icon"><BookOpen size={16} /></span>
              <div>
                <h3>推演结果 · 卦象含义全景解析</h3>
                <p>本卦卦德、大象传精义、动爻演变、体用生克与世应神煞详解</p>
              </div>
            </div>
            <span className="draft-state">理象详解</span>
          </div>
          <div className="correspondence-lead">
            <strong>{interpretation.headline}</strong>
            <p>{interpretation.summary}</p>
          </div>
          <div className="correspondence-list">
            {interpretation.modules.map((item, index) => (
              <article key={item.module} className="interp-module-card">
                <div className="interp-module-header">
                  <span className="explanation-index">{index + 1}</span>
                  <h4>{item.title}</h4>
                </div>
                <div className="interp-module-body">
                  <div className="interp-fact-pill">
                    <strong>盘面事实：</strong><span>{item.chart_fact}</span>
                  </div>
                  {item.great_image && (
                    <div className="interp-quote">
                      <b>象传警策：</b><em>“{item.great_image}”</em>
                    </div>
                  )}
                  <div className="interp-content">
                    <p>{item.correspondence}</p>
                  </div>
                  <div className="interp-action-hint">
                    <strong>现实指导：</strong><span>{item.verification}</span>
                  </div>
                  <div className="explanation-rules">
                    {item.rule_ids.map((rule) => <code key={rule}>{rule}</code>)}
                  </div>
                </div>
              </article>
            ))}
          </div>
          {interpretation.cross_layer.map((item) => (
            <div className="correspondence-cross" key={item.title}>
              <strong>{item.title}</strong>
              <p>{item.text}</p>
              <div className="explanation-rules">{item.rule_ids.map((rule) => <code key={rule}>{rule}</code>)}</div>
            </div>
          ))}
          {interpretation.limitations.map((limitation) => <Notice tone="neutral" icon={ShieldCheck} key={limitation}>{limitation}</Notice>)}
        </section>
      )}

      {yuanHui && (
        <section className="data-band yuanhui-band">
          <div className="band-heading">
            <div><span className="band-icon"><Clock3 size={16} /></span><div><h3>元会运世</h3><p>{yuanHui.status}</p></div></div>
            <span className="version-badge">{yuanHui.rule_version}</span>
          </div>
          <div className="yuanhui-grid">
            {[["元", yuanHui.facts.yuan], ["会", yuanHui.facts.hui], ["运", yuanHui.facts.yun], ["世", yuanHui.facts.shi]].map(([label, period]) => (
              <div key={label}>
                <span>{label}</span><strong>{period.label}{label === "会" ? ` · ${period.branch}${period.element}` : ""}</strong>
                <small>{period.start_year} 至 {period.end_year}</small>
              </div>
            ))}
          </div>
          <div className="yuanhui-meta">
            <span>世内第 {yuanHui.facts.shi.year_in_shi} 年</span>
            <span>纪元：{yuanHui.facts.epoch.label}</span>
            <code>YHYS-CYCLE-001</code>
          </div>
        </section>
      )}

      {imagery && (
        <section className="data-band imagery-band">
          <div className="band-heading">
            <div><span className="band-icon"><Layers3 size={16} /></span><div><h3>类象关联</h3><p>{imagery.context.priority_dimensions.join(" · ")} · {imagery.status}</p></div></div>
            <span className="version-badge">{imagery.rule_version}</span>
          </div>
          <div className="imagery-list">
            {imagery.candidates.map((candidate) => (
              <div className="imagery-row" key={candidate.candidate_id}>
                <div className="imagery-symbol"><strong>{candidate.symbol}</strong><span>{candidate.element}</span></div>
                <div>
                  <span className="imagery-role">{IMAGERY_MODULE_LABELS[candidate.module]} · {IMAGERY_STAGE_LABELS[candidate.stage]} · {IMAGERY_ROLE_LABELS[candidate.role]}</span>
                  <p>{Object.entries(candidate.selected_imagery).map(([dimension, values]) => `${dimension}：${values.join("、")}`).join("；")}</p>
                </div>
                <code>{candidate.rule_ids.join(" · ")}</code>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="explanation-lead">
        <span>计算结果摘要</span>
        <p>{explanation.summary}</p>
      </section>

      {explanation.modules.map((module) => {
        const Icon = icons[module.module] || FileText;
        return (
          <section className="data-band explanation-module" key={module.module}>
            <div className="band-heading">
              <div><span className="band-icon"><Icon size={16} /></span><div><h3>{module.title}</h3><p>{module.summary}</p></div></div>
            </div>
            <div className="explanation-sections">
              {module.sections.map((section, index) => {
                const ruleBadge = section.rule_id || (Array.isArray(section.rule_ids) ? section.rule_ids.join(" · ") : "");
                const headingText = section.heading || section.title || "";
                return (
                  <div className="explanation-section" key={`${ruleBadge || index}-${index}`}>
                    <div className="section-meta">
                      <span className="explanation-index">{index + 1}</span>
                      {ruleBadge && <span className="rule-badge">{ruleBadge}</span>}
                    </div>
                    <div className="section-body">
                      {headingText && <h4>{headingText}</h4>}
                      <p>{section.text}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        );
      })}
    </div>
  );
}

export { ExplanationView };
