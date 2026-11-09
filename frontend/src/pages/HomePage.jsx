import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  CalendarRange,
  Check,
  CircleAlert,
  Compass,
  Grid3X3,
  Layers3,
  Mountain,
  Orbit,
  Sparkles,
  Workflow,
} from "lucide-react";
import { MODULE_GROUPS } from "../lib/modules";
import { analyzeCalendar } from "../lib/api";

const ICONS = {
  zhouyi: BookOpen,
  meihua: Compass,
  liuyao: Grid3X3,
  bazi: CalendarRange,
  ziwei: Orbit,
  qimen: Compass,
  liuren: Workflow,
  fengshui: Mountain,
  workflow: Layers3,
};

function CalendarQuickCheck() {
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");
  const now = new Date();
  const localNow = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);

  const handleCheck = async () => {
    setLoading(true);
    setError("");
    try {
      setPreview(
        await analyzeCalendar({
          local_datetime: localNow,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Shanghai",
          true_solar: false,
        }),
      );
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="home-calendar-card">
      <div className="section-title"><CalendarRange size={16} /><span>历法速览</span></div>
      <p className="home-card-desc">
        各模块内部都内置时间基准校验；这里单独提供一个不进入任何排盘的历法速查入口。
      </p>
      <div className="home-calendar-controls">
        <span className="home-calendar-now">当前本地时间：{localNow.replace("T", " ")}</span>
        <button type="button" className="secondary-command" onClick={handleCheck} disabled={loading}>
          {loading ? "校验中…" : "校验当前时间"}
        </button>
      </div>
      {error && (
        <div className="standalone-error" role="alert"><CircleAlert size={16} /><span>{error}</span></div>
      )}
      {preview && (
        <div className="calendar-confirmation" aria-live="polite">
          <div className="confirmation-title"><Check size={14} />时间已校验</div>
          <div className="pillar-row mini">
            {Object.entries(preview.pillars).slice(0, 4).map(([key, value]) => (
              <span key={key}><small>{{ year: "年", month: "月", day: "日", time: "时" }[key]}</small>{value}</span>
            ))}
          </div>
          <p>{preview.lunar.month_name}月{preview.lunar.day_name}</p>
        </div>
      )}
    </section>
  );
}

export default function HomePage() {
  return (
    <main className="home-page">
      <header className="home-hero">
        <div className="brand-mark"><span>☰</span><span>☷</span></div>
        <span className="section-kicker">TIANJI YANXIANG · 推演工作台</span>
        <h1>天机演象</h1>
        <p className="home-hero-desc">
          按术数分模块独立推演：卜筮、命理、时空、堪舆与交互工作流各自成页，
          共用确定性工程基线，不自动给出吉凶评分。
        </p>
      </header>

      <CalendarQuickCheck />

      {MODULE_GROUPS.map((group) => (
        <section className="home-module-group" key={group.id}>
          <h2 className="home-group-title">{group.label}</h2>
          <div className="home-module-grid">
            {group.modules.map((module) => {
              const Icon = ICONS[module.id] || Sparkles;
              return (
                <Link to={module.to} className="home-module-card" key={module.id}>
                  <div className="home-module-card-head">
                    <Icon size={20} />
                    <strong>{module.label}</strong>
                  </div>
                  <p>{module.desc}</p>
                  <span className="home-module-enter">
                    进入 <ArrowRight size={14} />
                  </span>
                </Link>
              );
            })}
          </div>
        </section>
      ))}
    </main>
  );
}
