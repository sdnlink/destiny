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
import { generateMarkdownReport, downloadMarkdownFile, copyToClipboard } from "../lib/export";

const TABS = [
  { id: "overview", label: "总览", icon: Layers3 },
  { id: "calendar", label: "输入与历法", icon: CalendarDays },
  { id: "zhouyi", label: "周易", icon: BookOpen },
  { id: "meihua", label: "梅花易数", icon: Compass },
  { id: "liuyao", label: "六爻", icon: Grid3X3 },
  { id: "liuren", label: "大六壬", icon: Workflow },
  { id: "qimen", label: "奇门遁甲", icon: Compass },
  { id: "bazi", label: "八字命理", icon: Sparkles },
  { id: "ziwei", label: "紫微斗数", icon: Sparkles },
  { id: "fengshui", label: "阳宅风水", icon: Mountain },
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
const SCENE_LABELS = {
  combined: "综合推演",
  zhouyi: "周易",
  meihua: "梅花易数",
  liuyao: "六爻",
  liuren: "大六壬",
  qimen: "奇门遁甲",
  bazi: "八字命理",
  ziwei: "紫微斗数",
  fengshui: "阳宅风水",
};
const IMAGERY_MODULE_LABELS = {
  zhouyi: "周易",
  meihua: "梅花",
  liuyao: "六爻",
  liuren: "六壬",
  qimen: "奇门",
  bazi: "八字",
  ziwei: "紫微",
};
const IMAGERY_STAGE_LABELS = { original: "本盘", changed: "变盘" };
const CAST_METHOD_LABELS = {
  personalized_three_coin: "个体三枚铜钱",
  personalized_lunar_time: "个体时间取数",
  personalized_report_number: "个体报数",
  lunar_time: "传统时间",
  time: "传统时间",
  number_hour: "数字排盘",
  two_numbers: "数字排盘",
};
const IMAGERY_ROLE_LABELS = {
  upper_trigram: "上卦",
  lower_trigram: "下卦",
  body: "体卦",
  use: "用卦",
  changed_use: "变卦之用",
  palace: "卦宫",
  month_general: "月将",
  initial_transmission: "初传",
  middle_transmission: "中传",
  final_transmission: "末传",
};

const ELEMENT_COLORS = {
  木: "#2e7d32",
  火: "#c62828",
  土: "#d87a16",
  金: "#b78103",
  水: "#1565c0",
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
            <p>吉方：{qimen.favorable_directions?.[0]?.direction}（{qimen.favorable_directions?.[0]?.gate}）</p>
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

function CalendarView({ calendar }) {
  if (!calendar) return <MissingModule name="历法" />;
  const { input, solar, lunar, pillars, zodiac, xun, solar_term, time } = calendar;
  return (
    <div className="view-stack">
      <section className="view-heading">
        <div>
          <span className="section-kicker">CHINESE CALENDAR ENGINE</span>
          <h2>历法基准与干支四柱</h2>
          <p>定气法、节令边界、真太阳时与干支纪时严格对齐。</p>
        </div>
        <span className="version-badge">{calendar.engine_version}</span>
      </section>

      <section className="data-band">
        <div className="band-heading">
          <div><span className="band-icon"><CalendarDays size={16} /></span><div><h3>四柱干支</h3><p>年依立春 · 月依节令 · 日依子初（23:00）</p></div></div>
        </div>
        <Pillars calendar={calendar} />
      </section>

      <section className="two-column-data">
        <div className="data-band">
          <div className="band-heading">
            <div><span className="band-icon"><Clock3 size={16} /></span><div><h3>时间基准与修正</h3><p>真太阳时与标准时区转换</p></div></div>
          </div>
          <div className="key-value-list">
            <DataState label="输入本地时间" value={input.local_datetime} />
            <DataState label="所在时区" value={input.timezone} />
            <DataState label="真太阳时修正" value={time.correction?.enabled ? `${time.correction.total_correction_minutes} 分钟` : "未启用"} />
            <DataState label="有效计算时间" value={time.effective_local_datetime} />
          </div>
        </div>

        <div className="data-band">
          <div className="band-heading">
            <div><span className="band-icon"><Compass size={16} /></span><div><h3>农历与节气</h3><p>二十四节气定气法时刻</p></div></div>
          </div>
          <div className="key-value-list">
            <DataState label="农历日期" value={`${lunar.year}年 ${lunar.is_leap_month ? "闰" : ""}${lunar.month_name}月${lunar.day_name}`} />
            <DataState label="年生肖" value={`${zodiac.name}（${zodiac.branch}）`} />
            <DataState label="旬空（日柱）" value={xun.empty_branches.join("、")} />
            <DataState label="相邻节气" value={`${solar_term.previous_month_boundary?.name || "前节"} → ${solar_term.next_month_boundary?.name || "后节"}`} />
          </div>
        </div>
      </section>

      {/* 黄历择吉与建除星宿 */}
      {calendar.almanac && (
        <section className="data-band almanac-band">
          <div className="band-heading">
            <div>
              <span className="band-icon"><Sparkles size={16} /></span>
              <div>
                <h3>天时时空与建除星宿</h3>
                <p>十二建星 · 二十八宿 · 黄道天神 · 宜忌择吉</p>
              </div>
            </div>
            <span className={`almanac-hd-badge ${calendar.almanac.day_tian_shen?.type === "黄道" ? "is-huangdao" : "is-heidao"}`}>
              {calendar.almanac.day_tian_shen?.type} · {calendar.almanac.day_tian_shen?.name} ({calendar.almanac.day_tian_shen?.luck})
            </span>
          </div>

          <div className="almanac-grid">
            <div className="almanac-card">
              <span className="almanac-label">十二建星</span>
              <strong className="almanac-duty">【{calendar.almanac.duty_officer}日】</strong>
              <small>执掌当令时序吉凶</small>
            </div>
            <div className="almanac-card">
              <span className="almanac-label">二十八宿</span>
              <strong className="almanac-mansion">【{calendar.almanac.twenty_eight_mansion?.name}宿 · {calendar.almanac.twenty_eight_mansion?.luck}】</strong>
              <small>{calendar.almanac.twenty_eight_mansion?.song || "星宿当值"}</small>
            </div>
            <div className="almanac-card">
              <span className="almanac-label">九星值日</span>
              <strong className="almanac-ninestar">{calendar.almanac.day_nine_star}</strong>
              <small>紫白九星天运流转</small>
            </div>
          </div>

          <div className="almanac-activities-row">
            <div className="activity-group favorable">
              <span className="act-tag-label">【宜】</span>
              <div className="act-pills">
                {calendar.almanac.favorable_activities?.slice(0, 10).map((act) => (
                  <span key={act} className="act-pill fav">{act}</span>
                ))}
              </div>
            </div>
            <div className="activity-group unfavorable">
              <span className="act-tag-label">【忌】</span>
              <div className="act-pills">
                {calendar.almanac.unfavorable_activities?.slice(0, 8).map((act) => (
                  <span key={act} className="act-pill unfav">{act}</span>
                ))}
              </div>
            </div>
          </div>

          {calendar.almanac.lucky_directions && (
            <div className="almanac-deities-grid">
              <div className="deity-item"><span className="deity-label">喜神</span><strong>{calendar.almanac.lucky_directions.joy_deity}</strong></div>
              <div className="deity-item"><span className="deity-label">财神</span><strong>{calendar.almanac.lucky_directions.wealth_deity}</strong></div>
              <div className="deity-item"><span className="deity-label">福神</span><strong>{calendar.almanac.lucky_directions.blessing_deity}</strong></div>
              <div className="deity-item"><span className="deity-label">阳贵神</span><strong>{calendar.almanac.lucky_directions.yang_noble}</strong></div>
              <div className="deity-item"><span className="deity-label">阴贵神</span><strong>{calendar.almanac.lucky_directions.yin_noble}</strong></div>
            </div>
          )}

          {calendar.almanac.pengzu && (
            <div className="almanac-pengzu-row">
              <span className="pengzu-label">彭祖百忌：</span>
              <span>{calendar.almanac.pengzu.gan} · {calendar.almanac.pengzu.zhi}</span>
            </div>
          )}

          {calendar.almanac.hourly_timeline?.length > 0 && (
            <div className="almanac-hourly-section">
              <div className="hourly-section-title">
                <Clock3 size={15} />
                <span>当日十二时辰吉凶时序（择吉与时值天神）</span>
              </div>
              <div className="hourly-timeline-grid">
                {calendar.almanac.hourly_timeline.map((item) => {
                  const isCurrentHour = item.branch === calendar.time_branch?.name;
                  const isHuangdao = item.tian_shen?.type === "黄道";
                  return (
                    <div
                      key={item.hour}
                      className={`hourly-card ${isHuangdao ? "is-huangdao" : "is-heidao"} ${isCurrentHour ? "is-current-hour" : ""}`}
                    >
                      <div className="hourly-top">
                        <span className="hourly-branch">{item.branch}时</span>
                        <span className={`hourly-tag ${isHuangdao ? "fav" : "unfav"}`}>
                          {item.tian_shen?.name} ({item.tian_shen?.type})
                        </span>
                      </div>
                      <div className="hourly-time-range">{item.time_range}</div>
                      <div className="hourly-ganzhi">{item.ganzhi}</div>
                      <small className="hourly-clash">冲{item.clash?.animal} · 煞{item.clash?.direction}</small>
                      {item.favorable_activities?.length > 0 && (
                        <div className="hourly-yi">宜: {item.favorable_activities.slice(0, 3).join(" ")}</div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </section>
      )}

      <section className="data-band">
        <div className="band-heading">
          <div><span className="band-icon"><ListTree size={16} /></span><div><h3>推演步骤</h3><p>{calendar.engine_version}</p></div></div>
        </div>
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

const NAJIA_TABLE = {
  乾: { lower: ["甲子", "甲寅", "甲辰"], upper: ["壬午", "壬申", "壬戌"] },
  坤: { lower: ["乙未", "乙巳", "乙卯"], upper: ["癸丑", "癸亥", "癸酉"] },
  震: { lower: ["庚子", "庚寅", "庚辰"], upper: ["庚午", "庚申", "庚戌"] },
  巽: { lower: ["辛丑", "辛亥", "辛酉"], upper: ["辛未", "辛巳", "辛卯"] },
  坎: { lower: ["戊寅", "戊辰", "戊午"], upper: ["戊申", "戊戌", "戊子"] },
  离: { lower: ["己卯", "己丑", "己亥"], upper: ["己酉", "己未", "己巳"] },
  艮: { lower: ["丙辰", "丙午", "丙申"], upper: ["丙戌", "丙子", "丙寅"] },
  兑: { lower: ["丁巳", "丁卯", "丁丑"], upper: ["丁亥", "丁酉", "丁未"] },
};

const BRANCH_ELEMENTS_MAP = {
  子: "水", 丑: "土", 寅: "木", 卯: "木", 辰: "土", 巳: "火",
  午: "火", 未: "土", 申: "金", 酉: "金", 戌: "土", 亥: "水",
};

const FIVE_ELEMENTS_GENERATES = { 木: "火", 火: "土", 土: "金", 金: "水", 水: "木" };
const FIVE_ELEMENTS_CONTROLS = { 木: "土", 土: "水", 水: "火", 火: "金", 金: "木" };

function getLiuyaoRelative(palaceElement, lineElement) {
  if (palaceElement === lineElement) return "兄弟";
  if (FIVE_ELEMENTS_GENERATES[lineElement] === palaceElement) return "父母";
  if (FIVE_ELEMENTS_GENERATES[palaceElement] === lineElement) return "子孙";
  if (FIVE_ELEMENTS_CONTROLS[lineElement] === palaceElement) return "官鬼";
  if (FIVE_ELEMENTS_CONTROLS[palaceElement] === lineElement) return "妻财";
  return "比和";
}

function buildHiddenSpirits(facts) {
  const backend = facts.hidden_flying_spirits;
  if (backend && backend.status === "completed" && Array.isArray(backend.hidden_spirits)) {
    return backend.hidden_spirits.map((item) => ({
      position: item.position,
      ganzhi: `${item.najia_stem}${item.najia_branch}`,
      element: item.element,
      relative: item.six_relative,
      relation: item.relation,
      flying: item.flying_spirit,
    }));
  }
  // 兼容旧会话：本宫首卦纳甲 → 缺失六亲逐位补出
  const pureConfig = NAJIA_TABLE[facts.palace.name];
  const pureGanzhi = pureConfig ? [...pureConfig.lower, ...pureConfig.upper] : [];
  const currentRelatives = new Set(facts.line_chart.map((line) => line.six_relative));
  const missingRelatives = ["父母", "兄弟", "子孙", "妻财", "官鬼"].filter(
    (relative) => !currentRelatives.has(relative)
  );
  return pureGanzhi
    .map((ganzhi, index) => {
      const element = BRANCH_ELEMENTS_MAP[ganzhi[1]] || "土";
      return {
        position: index + 1,
        ganzhi,
        element,
        relative: getLiuyaoRelative(facts.palace.element, element),
      };
    })
    .filter((item) => missingRelatives.includes(item.relative));
}

function LiuyaoView({ result }) {
  if (!result) return <MissingModule name="六爻" />;
  const { facts } = result;
  const [selectedPos, setSelectedPos] = useState(facts.palace.host_line || 1);

  // 伏神优先采用后端推导（本宫首卦同位补缺），旧会话缺该字段时回退本地计算
  const hiddenSpirits = buildHiddenSpirits(facts);

  const activeLine = facts.line_chart.find((l) => l.position === selectedPos) || facts.line_chart[0];
  const activeHidden = hiddenSpirits.find((h) => h.position === selectedPos);

  return (
    <div className="view-stack">
      <section className="view-heading">
        <div>
          <span className="section-kicker">LIU YAO NA JIA</span>
          <h2>六爻纳甲盘与伏神飞神</h2>
          <p>八宫世应、纳甲六亲、六神与动变爻位立体交互排盘。</p>
        </div>
        <span className="version-badge">{result.rule_version}</span>
      </section>

      <section className="hexagram-primary-grid">
        <HexagramTile title="本卦" hexagram={facts.original} moving={facts.moving_lines} featured />
        <div className="change-arrow"><ArrowRight size={22} /><span>第 {facts.moving_lines.join("、")} 爻动</span></div>
        <HexagramTile title="变卦" hexagram={facts.changed} featured />
      </section>

      <CastingIdentity facts={facts} />

      <section className="data-band">
        <div className="band-heading">
          <div>
            <span className="band-icon"><Grid3X3 size={16} /></span>
            <div>
              <h3>{facts.palace.name}宫 · {facts.palace.stage}</h3>
              <p>世爻 {facts.palace.host_line} · 应爻 {facts.palace.response_line} · {facts.xun.name}空 {facts.xun.empty_branches.join("、")}</p>
            </div>
          </div>
        </div>
        <div className="liuyao-table-wrap">
          <table className="liuyao-table">
            <thead>
              <tr>
                <th>爻位</th>
                <th>六神</th>
                <th>六亲</th>
                <th>纳甲</th>
                <th>五行</th>
                <th>世应</th>
                <th>状态</th>
                <th>本宫伏神</th>
              </tr>
            </thead>
            <tbody>
              {[...facts.line_chart].reverse().map((line) => {
                const hidden = hiddenSpirits.find((h) => h.position === line.position);
                return (
                  <tr
                    key={line.position}
                    className={`${line.is_moving ? "moving-line" : ""} ${selectedPos === line.position ? "selected-line" : ""}`}
                    onClick={() => setSelectedPos(line.position)}
                    style={{ cursor: "pointer" }}
                  >
                    <td><strong>{line.position === 6 ? "上爻" : line.position === 1 ? "初爻" : `${line.position}爻`}</strong></td>
                    <td><span className="spirit-badge">{line.six_spirit}</span></td>
                    <td><strong>{line.six_relative}</strong></td>
                    <td>{line.najia_stem}{line.najia_branch}</td>
                    <td><span style={{ color: ELEMENT_COLORS[line.element] || "inherit" }}>{line.element}</span></td>
                    <td>{(line.roles || []).some((role) => role === "世" || role === "世爻") ? <span className="shi-badge">世</span> : (line.roles || []).some((role) => role === "应" || role === "应爻") ? <span className="ying-badge">应</span> : "—"}</td>
                    <td>
                      {line.is_moving ? <span className="moving-badge">发动 ○</span> : "静爻"}
                      {line.void_state ? ` · ${line.void_state}` : line.is_void ? " · 旬空" : ""}
                      {line.is_month_break ? " · 月破" : ""}
                      {line.is_day_break ? " · 日破" : ""}
                      {line.is_dark_move ? " · 暗动" : ""}
                      {line.advance_retreat ? ` · ${line.advance_retreat}` : ""}
                    </td>
                    <td>
                      {hidden ? (
                        <span className="hidden-pill-tag" title={`伏于${line.najia_branch}下`}>
                          伏 {hidden.relative} {hidden.ganzhi}
                        </span>
                      ) : (
                        <small className="inspect-link">查看详情</small>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* 伏神飞神聚焦研判卡片 */}
      {hiddenSpirits.length > 0 && (
        <section className="data-band hidden-spirits-band">
          <div className="band-heading">
            <div>
              <span className="band-icon"><Sparkles size={16} /></span>
              <div>
                <h3>本宫八纯伏神对照（{palaceName}为{palaceName}）</h3>
                <p>本卦缺【{missingRelatives.join("、")}】，从本宫纯卦提取伏神以明隐微之事</p>
              </div>
            </div>
          </div>
          <div className="hidden-spirits-grid">
            {hiddenSpirits.map((h) => {
              const flyLine = facts.line_chart[h.position - 1];
              let relType = "同气比和";
              let relDesc = "比和得气，同气相求。";
              if (FIVE_ELEMENTS_GENERATES[flyLine.element] === h.element) {
                relType = "飞生伏";
                relDesc = "飞来生伏得长生，虽伏易出，吉象。";
              } else if (FIVE_ELEMENTS_GENERATES[h.element] === flyLine.element) {
                relType = "伏生飞";
                relDesc = "伏去生飞泄气，耗神泄力。";
              } else if (FIVE_ELEMENTS_CONTROLS[flyLine.element] === h.element) {
                relType = "飞克伏";
                relDesc = "飞来克伏受制，为害最深，难拔难出。";
              } else if (FIVE_ELEMENTS_CONTROLS[h.element] === flyLine.element) {
                relType = "伏克飞";
                relDesc = "伏去克飞为财，冲克飞神方能显现。";
              }

              return (
                <div key={h.position} className="hidden-spirit-card">
                  <div className="h-card-head">
                    <strong>伏神【{h.relative} {h.ganzhi}（{h.element}）】</strong>
                    <span className={`h-rel-badge rel-${relType}`}>{relType}</span>
                  </div>
                  <p className="h-card-detail">
                    伏于第 {h.position} 爻 <b>{flyLine.six_relative} {flyLine.najia_stem}{flyLine.najia_branch}（{flyLine.element}）</b> 飞神之下。
                  </p>
                  <small className="h-card-desc">{relDesc}</small>
                </div>
              );
            })}
          </div>
        </section>
      )}

      <section className="data-band">
        <div className="band-heading">
          <div><span className="band-icon"><ListTree size={16} /></span><div><h3>计算依据</h3><p>{result.engine_version}</p></div></div>
        </div>
        <Steps steps={result.steps} />
      </section>
    </div>
  );
}

function LiurenView({ result }) {
  if (!result) return <MissingModule name="大六壬" />;
  const { facts } = result;
  const transmission = facts.three_transmissions;
  const [hoverBranch, setHoverBranch] = useState(null);

  return (
    <div className="view-stack">
      <section className="view-heading">
        <div>
          <span className="section-kicker">DA LIU REN</span>
          <h2>大六壬盘</h2>
          <p>月将、占时、天地盘、四课、三传、天将乘神与时空交互网络。</p>
        </div>
        <span className="version-badge">{result.rule_version}</span>
      </section>

      <section className="liuren-facts-band">
        <DataState label="占日" value={facts.day_pillar} />
        <DataState label="占时" value={facts.occupation_time.branch} />
        <DataState label="月将" value={`${facts.month_general.name} · ${facts.month_general.branch}`} />
        <DataState label="旬空" value={facts.xun.empty_branches.join("、")} />
      </section>

      <CastingIdentity facts={facts} />

      <section className="data-band">
        <div className="band-heading">
          <div>
            <span className="band-icon"><Workflow size={16} /></span>
            <div>
              <h3>天地盘与十二天将乘神</h3>
              <p>{facts.month_general.boundary_term}后月将 · {facts.heavenly_generals.distribution_direction}</p>
            </div>
          </div>
        </div>
        <div className="liuren-plate-wrap">
          <div className="liuren-plate-row row-label">
            <b>地盘</b>
            {facts.earth_plate.map((branch) => (
              <span
                key={branch}
                className={hoverBranch === branch ? "branch-active" : ""}
                onMouseEnter={() => setHoverBranch(branch)}
                onMouseLeave={() => setHoverBranch(null)}
              >
                {branch}
              </span>
            ))}
          </div>
          <div className="liuren-plate-row">
            <b>天盘</b>
            {facts.earth_plate.map((branch) => (
              <strong
                key={branch}
                className={hoverBranch === branch ? "branch-active" : ""}
                onMouseEnter={() => setHoverBranch(branch)}
                onMouseLeave={() => setHoverBranch(null)}
              >
                {facts.heaven_plate[branch]}
              </strong>
            ))}
          </div>
          <div className="liuren-plate-row generals">
            <b>天将</b>
            {facts.earth_plate.map((branch) => (
              <span
                key={branch}
                className={hoverBranch === branch ? "branch-active" : ""}
                onMouseEnter={() => setHoverBranch(branch)}
                onMouseLeave={() => setHoverBranch(null)}
              >
                {facts.heavenly_generals.by_ground[branch]}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="liuren-detail-grid">
        <div className="data-band">
          <div className="band-heading">
            <div><span className="band-icon"><Grid3X3 size={16} /></span><div><h3>四课</h3><p>下神 → 上神</p></div></div>
          </div>
          <div className="four-lessons">
            {facts.four_lessons.map((lesson) => (
              <div key={lesson.sequence}>
                <span>第{lesson.sequence}课</span>
                <strong>{lesson.lower} → {lesson.upper}</strong>
                <small>{lesson.relation === "none" ? "无直接克" : lesson.relation === "lower_controls_upper" ? "下克上" : "上克下"}</small>
              </div>
            ))}
          </div>
        </div>
        <div className="data-band">
          <div className="band-heading">
            <div><span className="band-icon"><Workflow size={16} /></span><div><h3>三传</h3><p>{transmission.status === "completed" ? `${transmission.lesson_type}路径` : "规则路径未覆盖"}</p></div></div>
          </div>
          {transmission.status === "completed" ? (
            <div className="transmission-row">
              {["初传", "中传", "末传"].map((label, index) => (
                <div key={label}>
                  <span>{label}</span>
                  <strong>{transmission.transmissions[index]}</strong>
                </div>
              ))}
            </div>
          ) : (
            <Notice tone="warning" icon={CircleAlert}>待实现课体：{transmission.pending_path}。系统未生成猜测值。</Notice>
          )}
        </div>
      </section>

      <section className="data-band">
        <div className="band-heading">
          <div><span className="band-icon"><ListTree size={16} /></span><div><h3>推演步骤</h3><p>{result.engine_version}</p></div></div>
        </div>
        <Steps steps={result.steps} />
      </section>
    </div>
  );
}

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

function BaziView({ result }) {
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
  if (!result) return <MissingModule name="紫微斗数" />;
  const facts = result.facts;
  const branchMap = {};
  facts.palaces_by_branch.forEach((p) => {
    branchMap[p.earthly_branch] = p;
  });

  const [selectedBranch, setSelectedBranch] = useState("寅");

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

      <section className="data-band">
        <div className="band-heading"><div><span className="band-icon"><ListTree size={16} /></span><div><h3>推演步骤</h3><p>{result.engine_version}</p></div></div></div>
        <Steps steps={result.steps} />
      </section>
    </div>
  );
}

function MountainFact({ label, direction }) {
  const mountain = direction.mountain;
  return (
    <div className="direction-fact">
      <span>{label}</span>
      <strong>{mountain.name}</strong>
      <b>{direction.degree}°</b>
      <p>{mountain.trigram}卦 · {mountain.element} · {mountain.direction}</p>
      <small>区间 [{mountain.start_degree}°, {mountain.end_degree}°)</small>
    </div>
  );
}

function FengshuiCompassDial({ facingDegree = 0, sittingDegree = 180 }) {
  return (
    <div className="fengshui-compass-widget">
      <svg viewBox="0 0 300 300" className="luopan-svg" aria-label="二十四山罗盘">
        <circle cx="150" cy="150" r="140" fill="#252b28" stroke="#a66d1e" strokeWidth="3" />
        <circle cx="150" cy="150" r="120" fill="#2d3531" stroke="#d9d8d1" strokeWidth="1" strokeDasharray="3 3" />
        <circle cx="150" cy="150" r="85" fill="#202622" stroke="#a66d1e" strokeWidth="1.5" />
        <circle cx="150" cy="150" r="40" fill="#181d1a" stroke="#823024" strokeWidth="2" />
        
        <text x="150" y="28" textAnchor="middle" fill="#d9d8d1" fontSize="13" fontWeight="bold">北 (子)</text>
        <text x="278" y="154" textAnchor="middle" fill="#d9d8d1" fontSize="13" fontWeight="bold">东 (卯)</text>
        <text x="150" y="282" textAnchor="middle" fill="#d9d8d1" fontSize="13" fontWeight="bold">南 (午)</text>
        <text x="22" y="154" textAnchor="middle" fill="#d9d8d1" fontSize="13" fontWeight="bold">西 (酉)</text>

        <g transform={`rotate(${facingDegree}, 150, 150)`}>
          <polygon points="150,45 143,150 157,150" fill="#c62828" />
          <polygon points="150,255 143,150 157,150" fill="#1565c0" />
          <circle cx="150" cy="150" r="6" fill="#a66d1e" />
        </g>
      </svg>
      <div className="luopan-legend">
        <span className="legend-facing"><i />向首：{facingDegree}°</span>
        <span className="legend-sitting"><i />坐山：{sittingDegree}°</span>
      </div>
    </div>
  );
}

function MeasurementConsensusView({ result }) {
  const { measurements, consensus } = result.facts;
  const aggregate = consensus.aggregate;
  const statusLabels = { consistent: "一致", boundary_sensitive: "跨山界", inconsistent: "读数不一致" };
  return (
    <div className="view-stack">
      <section className="view-heading">
        <div><span className="section-kicker">FENGSHUI MEASUREMENT CONSENSUS</span><h2>阳宅多次测量共识</h2><p>每次读数独立修正真北，再以圆周统计汇总方向和保守误差。</p></div>
        <span className="version-badge">{result.rule_version}</span>
      </section>
      <section className="liuren-facts-band">
        <DataState label="测量次数" value={consensus.sample_count} />
        <DataState label="共识状态" value={statusLabels[consensus.status]} />
        <DataState label="最小覆盖弧" value={`${consensus.angular_spread}°`} />
        <DataState label="方向集中度" value={consensus.resultant_length} mono />
      </section>
      {aggregate ? (
        <>
          <section className="direction-primary-grid">
            <MountainFact label="共识坐山" direction={aggregate.sitting} />
            <div className="direction-axis"><ArrowRight size={24} /><span>相差 180°</span></div>
            <MountainFact label="共识向首" direction={aggregate.facing} />
          </section>
          <FengshuiCompassDial facingDegree={aggregate.facing.degree} sittingDegree={aggregate.sitting.degree} />
          <section className="data-band">
            <div className="band-heading"><div><span className="band-icon"><ShieldCheck size={16} /></span><div><h3>保守误差范围</h3><p>包含每次读数偏差与设备误差</p></div></div></div>
            <div className="comparison-counts">
              <DataState label="圆周均值" value={`${consensus.circular_mean_degree}°`} />
              <DataState label="最大偏差" value={`${consensus.maximum_deviation}°`} />
              <DataState label="合并误差 ±" value={`${consensus.effective_measurement_error}°`} />
              <DataState label="向首候选" value={aggregate.facing.candidate_mountains.map((item) => item.name).join("、")} />
            </div>
          </section>
        </>
      ) : <Notice tone="warning" icon={CircleAlert}>这些读数不能形成唯一方向，系统未生成合并山向。请检查是否混入坐山读数或测量方向相反。</Notice>}
      <section className="data-band">
        <div className="band-heading"><div><span className="band-icon"><Compass size={16} /></span><div><h3>逐次真北读数</h3><p>原始输入与修正结果并列保留</p></div></div></div>
        <div className="measurement-table-wrap">
          <table className="measurement-table">
            <thead><tr><th>次数</th><th>原始角度</th><th>基准</th><th>磁偏角</th><th>真北角</th><th>山向</th><th>距分界</th></tr></thead>
            <tbody>{measurements.map((row) => <tr key={row.sequence}>
              <td>{row.sequence}</td><td>{row.input.facing_degree}°</td><td>{row.input.input_reference === "magnetic" ? "磁北" : "真北"}</td>
              <td>{row.input.magnetic_declination}°</td><td>{row.true_facing_degree}°</td><td>{row.facing_mountain.name}</td><td>{row.distance_to_boundary}°</td>
            </tr>)}</tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function FengshuiView({ result }) {
  if (!result) return <MissingModule name="阳宅风水" />;
  if (result.facts.mode === "multiple_measurements") return <MeasurementConsensusView result={result} />;
  const { facts } = result;
  const facing = facts.facing;
  const sitting = facts.sitting;
  return (
    <div className="view-stack">
      <section className="view-heading">
        <div><span className="section-kicker">FENGSHUI DIRECTION</span><h2>阳宅真北坐向与二十四山</h2><p>磁偏角、坐向换算、二十四山和测量误差按独立规则计算。</p></div>
        <span className="version-badge">{result.rule_version}</span>
      </section>

      <section className="direction-primary-grid">
        <MountainFact label="坐山" direction={sitting} />
        <div className="direction-axis"><ArrowRight size={24} /><span>相差 180°</span></div>
        <MountainFact label="向首" direction={facing} />
      </section>

      <FengshuiCompassDial facingDegree={facts.true_facing_degree} sittingDegree={facts.true_sitting_degree} />

      <section className="two-column-data">
        <div className="data-band">
          <div className="band-heading"><div><span className="band-icon"><Compass size={16} /></span><div><h3>真北修正</h3><p>{result.normalized_input.input_reference === "magnetic" ? "磁北输入" : "真北输入"}</p></div></div></div>
          <div className="key-value-list">
            <DataState label="原始角度" value={`${result.normalized_input.input_degree}°`} />
            <DataState label="应用磁偏角" value={`${result.normalized_input.applied_declination}°`} />
            <DataState label="真北向首" value={`${facts.true_facing_degree}°`} />
            <DataState label="真北坐山" value={`${facts.true_sitting_degree}°`} />
          </div>
        </div>
        <div className="data-band">
          <div className="band-heading"><div><span className="band-icon"><ShieldCheck size={16} /></span><div><h3>测量稳定性</h3><p>误差 ±{result.normalized_input.measurement_error}°</p></div></div></div>
          <div className="key-value-list">
            <DataState label="分类状态" value={facts.classification_stable ? "稳定" : "跨越分界"} />
            <DataState label="距最近分界" value={`${facing.distance_to_boundary}°`} />
            <DataState label="向首候选" value={facing.candidate_mountains.map((item) => item.name).join("、")} />
            <DataState label="坐山候选" value={sitting.candidate_mountains.map((item) => item.name).join("、")} />
          </div>
        </div>
      </section>
      <section className="data-band">
        <div className="band-heading"><div><span className="band-icon"><ListTree size={16} /></span><div><h3>计算依据</h3><p>{result.engine_version}</p></div></div></div>
        <Steps steps={result.steps} />
      </section>
    </div>
  );
}

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
              {module.sections.map((section, index) => (
                <div className="explanation-section" key={`${section.rule_id}-${index}`}>
                  <div className="section-meta">
                    <span className="explanation-index">{index + 1}</span>
                    <span className="rule-badge">{section.rule_id}</span>
                  </div>
                  <div className="section-body">
                    <h4>{section.heading}</h4>
                    <p>{section.text}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        );
      })}
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
  const [copied, setCopied] = useState(false);

  if (!result) return <main className="result-workspace"><EmptyWorkspace /></main>;
  const calendar = findModule(result, "calendar");
  const zhouyi = findModule(result, "zhouyi");
  const meihua = findModule(result, "meihua");
  const liuyao = findModule(result, "liuyao");
  const liuren = findModule(result, "liuren");
  const qimen = findModule(result, "qimen");
  const bazi = findModule(result, "bazi");
  const ziwei = findModule(result, "ziwei");
  const fengshui = findModule(result, "fengshui");

  const handleCopyReport = async () => {
    const md = generateMarkdownReport(result, context);
    await copyToClipboard(md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadReport = () => {
    const md = generateMarkdownReport(result, context);
    const dateStr = new Date().toISOString().slice(0, 10);
    const filename = `天机演象推演报告_${context?.question?.slice(0, 10) || "事项"}_${dateStr}.md`;
    downloadMarkdownFile(md, filename);
  };

  return (
    <main className="result-workspace">
      <header className="result-header">
        <div className="task-identity">
          <div className="status-dot" />
          <div><strong>{context.question}</strong><span>{result.task_id}</span></div>
        </div>
        <div className="task-meta">
          <div className="export-action-group">
            <button className="export-btn" onClick={handleCopyReport} title="复制 Markdown 研判摘要">
              {copied ? <Check size={14} className="copied-icon" /> : <Copy size={14} />}
              <span>{copied ? "已复制" : "复制报告"}</span>
            </button>
            <button className="export-btn" onClick={handleDownloadReport} title="下载 Markdown 报告文件">
              <Download size={14} />
              <span>导出报告</span>
            </button>
            <button className="export-btn" onClick={() => window.print()} title="打印或导出为 PDF 文件">
              <Printer size={14} />
              <span>打印/PDF</span>
            </button>
          </div>
          <time>{new Date(result.calculated_at).toLocaleString("zh-CN", { hour12: false })}</time>
        </div>
      </header>
      <nav className="result-tabs" aria-label="结果视图">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id} aria-label={label} className={activeTab === id ? "active" : ""} onClick={() => setActiveTab(id)}>
            <Icon size={16} /><span>{label}</span>
          </button>
        ))}
      </nav>
      <div className="result-content">
        {activeTab === "overview" && (
          <Overview
            result={result}
            context={context}
            calendar={calendar}
            zhouyi={zhouyi}
            meihua={meihua}
            liuyao={liuyao}
            liuren={liuren}
            qimen={qimen}
            bazi={bazi}
            ziwei={ziwei}
            fengshui={fengshui}
            onTab={setActiveTab}
          />
        )}
        {activeTab === "calendar" && <CalendarView calendar={calendar} />}
        {activeTab === "zhouyi" && <ZhouyiView result={zhouyi} />}
        {activeTab === "meihua" && <MeihuaView result={meihua} />}
        {activeTab === "liuyao" && <LiuyaoView result={liuyao} />}
        {activeTab === "liuren" && <LiurenView result={liuren} />}
        {activeTab === "qimen" && <QimenView result={qimen} />}
        {activeTab === "bazi" && <BaziView result={bazi} />}
        {activeTab === "ziwei" && <ZiweiView result={ziwei} />}
        {activeTab === "fengshui" && <FengshuiView result={fengshui} />}
        {activeTab === "comparison" && <ComparisonView comparison={result.comparison} />}
        {activeTab === "explanation" && (
          <ExplanationView
            explanation={result.explanation}
            advisory={result.advisory}
            literature={result.literature}
            imagery={result.imagery}
            yuanHui={result.yuan_hui_yun_shi}
            interpretation={result.interpretation}
          />
        )}
      </div>
    </main>
  );
}
