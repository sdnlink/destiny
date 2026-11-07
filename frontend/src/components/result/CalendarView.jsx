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

export { CalendarView };
