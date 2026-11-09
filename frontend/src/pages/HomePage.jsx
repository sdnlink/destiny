import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  CalendarRange,
  Check,
  CircleAlert,
  Clock3,
  Compass,
  Grid3X3,
  Layers3,
  Mountain,
  Orbit,
  Search,
  Sparkles,
  Workflow,
  X,
} from "lucide-react";
import { MODULE_BY_PATH, MODULE_GROUPS, readRecentModules } from "../lib/modules";
import { analyzeCalendar } from "../lib/api";

const ICONS = {
  zhouyi: BookOpen,
  meihua: Sparkles,
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
            {Object.entries(preview.pillars || {}).slice(0, 4).map(([key, value]) => (
              <span key={key}><small>{{ year: "年", month: "月", day: "日", time: "时" }[key]}</small>{value}</span>
            ))}
          </div>
          <p>{preview.lunar?.month_name}月{preview.lunar?.day_name}</p>
        </div>
      )}
    </section>
  );
}

export default function HomePage() {
  const [query, setQuery] = useState("");
  const recent = readRecentModules();
  const keyword = query.trim().toLowerCase();

  const groups = MODULE_GROUPS.map((group) => ({
    ...group,
    modules: group.modules.filter((module) =>
      !keyword ||
      module.label.toLowerCase().includes(keyword) ||
      module.desc.toLowerCase().includes(keyword) ||
      group.label.includes(keyword)
    ),
  })).filter((group) => group.modules.length > 0);
  const total = groups.reduce((count, group) => count + group.modules.length, 0);

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

      {recent.length > 0 && (
        <section className="home-recent">
          <h2><Clock3 size={15} />最近使用</h2>
          <div className="home-recent-links">
            {recent.map((path) => (
              <Link key={path} to={path} className="home-recent-chip">
                {MODULE_BY_PATH[path].label}
              </Link>
            ))}
          </div>
        </section>
      )}

      <div className="home-search-row">
        <Search size={16} />
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="搜索功能模块，如「六爻」「纳甲」「紫微」…"
          aria-label="搜索功能模块"
        />
        {query && (
          <button type="button" onClick={() => setQuery("")} aria-label="清除搜索"><X size={14} /></button>
        )}
      </div>

      <CalendarQuickCheck />

      {total === 0 ? (
        <div className="home-no-result" role="status">
          没有匹配「{query.trim()}」的功能模块，试试「六爻」「八字」「风水」或清空搜索。
        </div>
      ) : (
        groups.map((group) => (
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
        ))
      )}
    </main>
  );
}
