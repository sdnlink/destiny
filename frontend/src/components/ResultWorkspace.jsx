import {
  ArrowRight,
  BookOpen,
  CalendarDays,
  CheckCircle2,
  CircleAlert,
  Clock3,
  Compass,
  FileSearch,
  FileText,
  GitCompareArrows,
  Info,
  Layers3,
  ListTree,
  ShieldCheck,
} from "lucide-react";

const TABS = [
  { id: "overview", label: "总览", icon: Layers3 },
  { id: "calendar", label: "输入与历法", icon: CalendarDays },
  { id: "zhouyi", label: "周易", icon: BookOpen },
  { id: "meihua", label: "梅花易数", icon: Compass },
  { id: "comparison", label: "对照分析", icon: GitCompareArrows },
  { id: "explanation", label: "结论建议", icon: FileText },
];

const PILLAR_LABELS = { year: "年柱", month: "月柱", day: "日柱", time: "时柱" };
const CATEGORY_LABELS = {
  career: "事业",
  finance: "财务",
  relationship: "关系",
  travel: "出行",
  study: "学业",
  other: "其他",
};

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

function HexagramLines({ lines, moving = [] }) {
  if (!lines) return null;
  return (
    <div className="hexagram-lines" aria-label="六爻卦象">
      {[...lines].map((line, index) => ({ line, position: index + 1 })).reverse().map(({ line, position }) => (
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
          <div className="hexagram-name"><span>{hexagram.symbol}</span><strong>{hexagram.name}</strong></div>
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
  return <div className={`notice ${tone}`}><Icon size={17} /><div>{children}</div></div>;
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

function Overview({ result, context, calendar, zhouyi, meihua, onTab }) {
  const comparison = result.comparison;
  return (
    <div className="view-stack">
      <section className="summary-band">
        <div className="summary-copy">
          <span className="eyebrow">{CATEGORY_LABELS[context.category]} · {context.scene === "combined" ? "综合推演" : context.scene === "zhouyi" ? "周易" : "梅花易数"}</span>
          <h2>{context.question}</h2>
          <p>本次输出保留盘面事实与计算依据。当前解释规则尚未发布，不生成自动吉凶评分。</p>
        </div>
        <div className="summary-status">
          <CheckCircle2 size={22} />
          <div><strong>计算完成</strong><span>{result.module_results.length} 个模块</span></div>
        </div>
      </section>

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
              <div key={recommendation.priority}><b>{recommendation.priority}</b><span>{recommendation.title}</span></div>
            ))}
          </div>
        </section>
      )}

      <section className="data-band result-explanation-summary">
        <div className="band-heading">
          <div><span className="band-icon"><FileText size={16} /></span><div><h3>推演结果</h3><p>确定性模板说明 · {result.explanation.review_status}</p></div></div>
          <button className="text-button" onClick={() => onTab("explanation")}>详细说明 <ArrowRight size={14} /></button>
        </div>
        <p className="result-summary-text">{result.explanation.summary}</p>
        <div className="module-summary-list">
          {result.explanation.modules.filter((module) => module.module !== "calendar").map((module) => (
            <div key={module.module}>
              <strong>{module.title}</strong>
              <span>{module.summary}</span>
            </div>
          ))}
        </div>
        <Notice tone="neutral" icon={ShieldCheck}>{result.explanation.conclusion.text}</Notice>
      </section>

      <section className="data-band">
        <div className="band-heading">
          <div><span className="band-icon"><GitCompareArrows size={16} /></span><div><h3>对照分析</h3><p>只比较引用已发布规则的结构化判断</p></div></div>
          <button className="text-button" onClick={() => onTab("comparison")}>查看详情 <ArrowRight size={14} /></button>
        </div>
        <div className="comparison-counts">
          <DataState label="一致" value={comparison.counts.consistent} />
          <DataState label="互补" value={comparison.counts.complementary} />
          <DataState label="冲突" value={comparison.counts.conflicts} />
          <DataState label="可比较判断" value={comparison.comparable_judgement_count} />
        </div>
        {comparison.notices.map((notice) => <Notice key={notice}>{notice}</Notice>)}
      </section>
    </div>
  );
}

function CalendarView({ calendar }) {
  if (!calendar) return <MissingModule name="历法" />;
  const correction = calendar.time.correction;
  return (
    <div className="view-stack">
      <section className="view-heading">
        <div><span className="section-kicker">CALENDAR BASELINE</span><h2>输入与历法</h2><p>原始时间、时区转换、节气位置和四柱边界完整保留。</p></div>
        <span className="version-badge">{calendar.rule_version}</span>
      </section>
      <section className="data-band pillar-band">
        <div className="band-heading"><div><span className="band-icon"><CalendarDays size={16} /></span><div><h3>四柱</h3><p>立春换年 · 节令换月 · 子初23时换日</p></div></div></div>
        <Pillars calendar={calendar} />
      </section>
      <section className="two-column-data">
        <div className="data-band">
          <div className="band-heading"><div><span className="band-icon"><Clock3 size={16} /></span><div><h3>时间转换</h3><p>{calendar.input.timezone}</p></div></div></div>
          <div className="key-value-list">
            <DataState label="原始本地时间" value={calendar.time.original_local_datetime} mono />
            <DataState label="UTC时间" value={calendar.time.utc_datetime} mono />
            <DataState label="有效计算时间" value={calendar.time.effective_local_datetime} mono />
            <DataState label="总修正" value={`${correction.total_correction_minutes} 分钟`} />
          </div>
        </div>
        <div className="data-band">
          <div className="band-heading"><div><span className="band-icon"><Compass size={16} /></span><div><h3>农历与节气</h3><p>{calendar.lunar.year}年</p></div></div></div>
          <div className="key-value-list">
            <DataState label="农历" value={`${calendar.lunar.is_leap_month ? "闰" : ""}${calendar.lunar.month_name}月${calendar.lunar.day_name}`} />
            <DataState label="上一节气" value={calendar.solar_terms.previous ? `${calendar.solar_terms.previous.name} · ${calendar.solar_terms.previous.datetime}` : "—"} />
            <DataState label="当前节气" value={calendar.solar_terms.current?.name || "非交节时刻"} />
            <DataState label="下一节气" value={calendar.solar_terms.next ? `${calendar.solar_terms.next.name} · ${calendar.solar_terms.next.datetime}` : "—"} />
          </div>
        </div>
      </section>
      <section className="data-band">
        <div className="band-heading"><div><span className="band-icon"><ListTree size={16} /></span><div><h3>计算过程</h3><p>{calendar.engine_version}</p></div></div></div>
        <Steps steps={calendar.steps} />
      </section>
    </div>
  );
}

function ZhouyiView({ result }) {
  if (!result) return <MissingModule name="周易" />;
  const { facts } = result;
  return (
    <div className="view-stack">
      <section className="view-heading">
        <div><span className="section-kicker">ZHOUYI</span><h2>周易卦盘</h2><p>六爻自下而上排列，动爻位置在卦线右侧标记。</p></div>
        <span className="version-badge">{result.rule_version}</span>
      </section>
      <section className="hexagram-primary-grid">
        <HexagramTile title="本卦" hexagram={facts.original} moving={facts.moving_lines} featured />
        <div className="change-arrow"><ArrowRight size={22} /><span>{facts.moving_lines.length ? `第 ${facts.moving_lines.join("、")} 爻动` : "无动爻"}</span></div>
        <HexagramTile title="变卦" hexagram={facts.changed} featured />
      </section>
      <section className="data-band">
        <div className="band-heading"><div><span className="band-icon"><Layers3 size={16} /></span><div><h3>关联卦</h3><p>互卦、错卦与综卦仅作为结构事实展示</p></div></div></div>
        <div className="related-hexagrams">
          <HexagramTile title="互卦" hexagram={facts.mutual} />
          <HexagramTile title="错卦" hexagram={facts.opposite} />
          <HexagramTile title="综卦" hexagram={facts.reversed} />
        </div>
      </section>
      <section className="data-band">
        <div className="band-heading"><div><span className="band-icon"><ListTree size={16} /></span><div><h3>计算依据</h3><p>{result.engine_version}</p></div></div></div>
        <Steps steps={result.steps} />
      </section>
      {result.warnings.map((warning) => <Notice tone="warning" icon={CircleAlert} key={warning}>{warning}</Notice>)}
    </div>
  );
}

function MeihuaView({ result }) {
  if (!result) return <MissingModule name="梅花易数" />;
  const { facts } = result;
  const bodyUse = facts.body_use;
  return (
    <div className="view-stack">
      <section className="view-heading">
        <div><span className="section-kicker">MEIHUA YISHU</span><h2>梅花易数</h2><p>起卦、动爻、体用与五行关系分层展示。</p></div>
        <span className="version-badge">{result.rule_version}</span>
      </section>
      <section className="hexagram-primary-grid">
        <HexagramTile title="本卦" hexagram={facts.original} moving={facts.moving_lines} featured />
        <div className="change-arrow"><ArrowRight size={22} /><span>第 {facts.moving_line} 爻动</span></div>
        <HexagramTile title="变卦" hexagram={facts.changed} featured />
      </section>
      <section className="body-use-band">
        <div className="body-use-item body">
          <span>体卦</span><strong>{bodyUse.body_trigram.symbol} {bodyUse.body_trigram.name}</strong><p>{bodyUse.body_trigram.element} · {bodyUse.body_position === "upper" ? "上卦" : "下卦"}</p>
        </div>
        <div className="body-use-relation">
          <span>{result.evidence[0]?.label}</span><ArrowRight size={20} />
        </div>
        <div className="body-use-item use">
          <span>用卦</span><strong>{bodyUse.use_trigram.symbol} {bodyUse.use_trigram.name}</strong><p>{bodyUse.use_trigram.element} · {bodyUse.use_position === "upper" ? "上卦" : "下卦"}</p>
        </div>
      </section>
      <section className="data-band">
        <div className="band-heading"><div><span className="band-icon"><ShieldCheck size={16} /></span><div><h3>关系证据</h3><p>关系事实不直接映射吉凶</p></div></div></div>
        <Evidence items={result.evidence} />
      </section>
      <section className="data-band">
        <div className="band-heading"><div><span className="band-icon"><ListTree size={16} /></span><div><h3>计算依据</h3><p>{result.engine_version}</p></div></div></div>
        <Steps steps={result.steps} />
      </section>
      {result.warnings.map((warning) => <Notice tone="warning" icon={CircleAlert} key={warning}>{warning}</Notice>)}
    </div>
  );
}

function ComparisonView({ comparison }) {
  const categories = [
    ["consistent", "一致", "同维度、同时间范围内倾向相同"],
    ["complementary", "互补", "不同模块提供不同侧面的判断"],
    ["conflicts", "冲突", "同维度、同时间范围内出现明确相反判断"],
    ["unpaired", "未配对", "只有一个模块提供了可用判断"],
  ];
  return (
    <div className="view-stack">
      <section className="view-heading">
        <div><span className="section-kicker">COMPARISON</span><h2>对照分析</h2><p>保留模块独立结果，不通过加权或平均隐藏分歧。</p></div>
        <span className="version-badge">无自动评分</span>
      </section>
      <section className="comparison-counts large">
        {categories.map(([key, label]) => <DataState key={key} label={label} value={comparison.counts[key]} />)}
        <DataState label="排除" value={comparison.counts.excluded} />
      </section>
      {comparison.notices.map((notice) => <Notice key={notice}>{notice}</Notice>)}
      <section className="data-band comparison-method">
        <div className="band-heading"><div><span className="band-icon"><GitCompareArrows size={16} /></span><div><h3>分类结果</h3><p>{comparison.strategy}</p></div></div></div>
        {categories.map(([key, label, description]) => (
          <div className="comparison-category" key={key}>
            <div><strong>{label}</strong><span>{description}</span></div>
            <b>{comparison[key].length}</b>
          </div>
        ))}
      </section>
      <Notice tone="neutral" icon={ShieldCheck}>
        当前工程规则均处于草稿状态，模块没有已发布的解释判断。因此此处只报告“暂无可比较判断”，不会从卦象或体用关系自动推断事项吉凶。
      </Notice>
    </div>
  );
}

function ExplanationView({ explanation, advisory }) {
  const icons = { calendar: CalendarDays, zhouyi: BookOpen, meihua: Compass };
  return (
    <div className="view-stack explanation-view">
      <section className="view-heading">
        <div><span className="section-kicker">CONCLUSION & ADVICE</span><h2>事项结论与详细建议</h2><p>结合所问事情、盘面关系和事项检查清单，给出可核实的下一步建议。</p></div>
        <span className="version-badge">{explanation.generation_method}</span>
      </section>

      {advisory && (
        <>
          <section className="advisory-lead">
            <div className="advisory-status"><span>{advisory.context.category_label}</span><small>{advisory.review_status}</small></div>
            <p className="advisory-question">“{advisory.context.question_summary}”</p>
            <h3>{advisory.conclusion.headline}</h3>
            <p className="advisory-conclusion">{advisory.conclusion.text}</p>
            <div className="advisory-confidence"><Info size={15} /><span>{advisory.conclusion.confidence_label} · 倾向：暂不判定</span></div>
          </section>

          <section className="data-band recommendations-band">
            <div className="band-heading">
              <div><span className="band-icon"><CheckCircle2 size={16} /></span><div><h3>建议行动</h3><p>按优先级执行，并用实际反馈校正后续决策</p></div></div>
            </div>
            <div className="recommendation-list">
              {advisory.recommendations.map((recommendation) => (
                <div className="recommendation-row" key={recommendation.priority}>
                  <span>{recommendation.priority}</span>
                  <div>
                    <strong>{recommendation.title}</strong>
                    <p>{recommendation.detail}</p>
                    <small>依据：{recommendation.basis}</small>
                    <div className="explanation-rules">{recommendation.rule_ids.map((rule) => <code key={rule}>{rule}</code>)}</div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="advisory-support-grid">
            <div className="data-band verification-band">
              <div className="band-heading"><div><span className="band-icon"><FileSearch size={16} /></span><div><h3>需要核实</h3><p>作出决定前回答</p></div></div></div>
              <ol>{advisory.verification_questions.map((question) => <li key={question}>{question}</li>)}</ol>
            </div>
            <div className="data-band basis-band">
              <div className="band-heading"><div><span className="band-icon"><ListTree size={16} /></span><div><h3>推演依据</h3><p>本次建议引用的结构事实</p></div></div></div>
              {advisory.evidence_basis.length ? advisory.evidence_basis.map((basis) => (
                <div className="advisory-basis-row" key={`${basis.module}-${basis.fact}`}>
                  <strong>{basis.module === "zhouyi" ? "周易" : "梅花"}</strong><span>{basis.fact}</span>
                  <code>{basis.rule_ids.join(" · ")}</code>
                </div>
              )) : <p className="empty-inline">当前没有可用于建议的模块关系事实。</p>}
            </div>
          </section>

          <section className="advisory-risk-band">
            <div><CircleAlert size={18} /><strong>决策边界</strong></div>
            <ul>{advisory.risk_notes.map((note) => <li key={note}>{note}</li>)}</ul>
          </section>
        </>
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
              {module.sections.map((section, index) => (
                <div className="explanation-row" key={section.title}>
                  <span className="explanation-index">{index + 1}</span>
                  <div>
                    <strong>{section.title}</strong>
                    <p>{section.text}</p>
                    <div className="explanation-rules">{section.rule_ids.map((rule) => <code key={rule}>{rule}</code>)}</div>
                  </div>
                </div>
              ))}
            </div>
            {module.limitations.map((limitation) => (
              <Notice tone="warning" icon={CircleAlert} key={limitation}>{limitation}</Notice>
            ))}
          </section>
        );
      })}

      <section className="data-band conclusion-band">
        <div className="band-heading">
          <div><span className="band-icon"><GitCompareArrows size={16} /></span><div><h3>{explanation.conclusion.title}</h3><p>{explanation.conclusion.status}</p></div></div>
        </div>
        <p>{explanation.conclusion.text}</p>
        <div className="comparison-counts">
          <DataState label="一致" value={explanation.conclusion.counts.consistent} />
          <DataState label="互补" value={explanation.conclusion.counts.complementary} />
          <DataState label="冲突" value={explanation.conclusion.counts.conflicts} />
          <DataState label="排除" value={explanation.conclusion.counts.excluded} />
        </div>
      </section>

      <section className="limitations-band">
        <div><ShieldCheck size={18} /><strong>说明边界</strong></div>
        <ul>{explanation.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul>
      </section>
    </div>
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

function EmptyWorkspace() {
  return (
    <div className="empty-workspace">
      <div className="empty-symbol" aria-hidden="true">
        <span>☰</span><i>易</i><span>☷</span>
      </div>
      <p className="section-kicker">CALCULATION WORKSPACE</p>
      <h2>从一次可复核的推演开始</h2>
      <p>填写左侧时间与起卦参数。结果将依次展示历法基准、卦盘事实、体用证据和对照限制。</p>
      <div className="empty-features">
        <span><CheckCircle2 size={15} />确定性计算</span>
        <span><ShieldCheck size={15} />规则可追溯</span>
        <span><GitCompareArrows size={15} />冲突不隐藏</span>
      </div>
    </div>
  );
}

export default function ResultWorkspace({ result, context, activeTab, setActiveTab }) {
  if (!result) return <main className="result-workspace"><EmptyWorkspace /></main>;
  const calendar = findModule(result, "calendar");
  const zhouyi = findModule(result, "zhouyi");
  const meihua = findModule(result, "meihua");
  return (
    <main className="result-workspace">
      <header className="result-header">
        <div className="task-identity">
          <div className="status-dot" />
          <div><strong>{context.question}</strong><span>{result.task_id}</span></div>
        </div>
        <div className="task-meta"><span>已完成</span><time>{new Date(result.calculated_at).toLocaleString("zh-CN", { hour12: false })}</time></div>
      </header>
      <nav className="result-tabs" aria-label="结果视图">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id} aria-label={label} className={activeTab === id ? "active" : ""} onClick={() => setActiveTab(id)}>
            <Icon size={16} /><span>{label}</span>
          </button>
        ))}
      </nav>
      <div className="result-content">
        {activeTab === "overview" && <Overview result={result} context={context} calendar={calendar} zhouyi={zhouyi} meihua={meihua} onTab={setActiveTab} />}
        {activeTab === "calendar" && <CalendarView calendar={calendar} />}
        {activeTab === "zhouyi" && <ZhouyiView result={zhouyi} />}
        {activeTab === "meihua" && <MeihuaView result={meihua} />}
        {activeTab === "comparison" && <ComparisonView comparison={result.comparison} />}
        {activeTab === "explanation" && <ExplanationView explanation={result.explanation} advisory={result.advisory} />}
      </div>
    </main>
  );
}
