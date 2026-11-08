import { useState } from "react";
import { CalendarRange, CircleAlert, GitBranch, LoaderCircle, Sparkles } from "lucide-react";
import { analyzeLiunian, evaluateCalculation } from "../../lib/api";
import { BaziView } from "../result/BaziView";
import { LifelineView } from "../result/LifelineView";
import { BirthProfileSection, birthPayload } from "./BirthProfileSection";
import { LiunianView } from "./LiunianView";

const TABS = [
  { id: "natal", label: "本命盘", icon: Sparkles, desc: "四柱、藏干十神与大运排盘" },
  { id: "liunian", label: "流年", icon: CalendarRange, desc: "逐年干支、十神、岁运组合事实" },
  { id: "lifeline", label: "生平时间轴", icon: GitBranch, desc: "起运后逐年事实与已发生事件对齐" },
];

function EmptyState({ title, desc }) {
  return (
    <div className="destiny-empty" role="status">
      <Sparkles size={22} />
      <strong>{title}</strong>
      <p>{desc}</p>
    </div>
  );
}

export default function DestinyPanel() {
  const [profile, setProfile] = useState({
    localDatetime: "",
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Shanghai",
    gender: "男",
    trueSolar: false,
    longitude: "",
  });
  const [activeTab, setActiveTab] = useState("natal");
  const [natal, setNatal] = useState(null);
  const [liunian, setLiunian] = useState(null);
  const [startYear, setStartYear] = useState(String(new Date().getFullYear()));
  const [count, setCount] = useState("10");
  const [loading, setLoading] = useState(null);
  const [error, setError] = useState("");

  const payload = birthPayload(profile);
  const profileReady = Boolean(profile.localDatetime && profile.timezone.trim());

  const changeProfile = (key, value) => {
    setProfile((current) => ({ ...current, [key]: value }));
    // 出生信息变了，旧的本命盘/流年结果不再对应当前输入，直接清空避免误读。
    setNatal(null);
    setLiunian(null);
    setError("");
  };

  const validateProfile = () => {
    if (!profileReady) {
      setError("请先填写公历出生日期时间与时区");
      return false;
    }
    if (profile.trueSolar && profile.longitude === "") {
      setError("开启真太阳时后必须填写出生地经度");
      return false;
    }
    return true;
  };

  const handleNatal = async () => {
    if (!validateProfile()) return;
    setLoading("natal");
    setError("");
    try {
      const response = await evaluateCalculation("bazi", "time", payload);
      setNatal(response.result);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(null);
    }
  };

  const handleLiunian = async () => {
    if (!validateProfile()) return;
    const start = Number(startYear);
    const years = Number(count);
    if (!Number.isInteger(start) || start < 1900 || start > 2100) {
      setError("起始年份需在 1900–2100 之间");
      return;
    }
    if (!Number.isInteger(years) || years < 1 || years > 60) {
      setError("流年年数需在 1–60 之间");
      return;
    }
    if (start + years - 1 > 2100) {
      setError("起始年份加年数不能超过 2100");
      return;
    }
    setLoading("liunian");
    setError("");
    try {
      setLiunian(await analyzeLiunian({ ...payload, start_year: start, count: years }));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(null);
    }
  };

  const active = TABS.find((tab) => tab.id === activeTab) || TABS[0];

  return (
    <main className="destiny-workspace">
      <header className="destiny-header">
        <div>
          <span className="section-kicker">DESTINY WORKSPACE</span>
          <h1>命运专项</h1>
          <p>以出生时刻为唯一输入，分别查看本命盘、逐年流年与生平时间轴；全部复用既有八字接口。</p>
        </div>
        <span className="destiny-mode-badge">本命 · 流年 · 时间轴</span>
      </header>

      <div className="destiny-layout">
        <aside className="destiny-input-column">
          <BirthProfileSection profile={profile} onChange={changeProfile} />
        </aside>

        <section className="destiny-output">
          <div className="destiny-tabs" role="tablist" aria-label="命运专项页签">
            {TABS.map(({ id, label, icon: Icon, desc }) => (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={activeTab === id}
                className={activeTab === id ? "active" : ""}
                onClick={() => {
                  setActiveTab(id);
                  setError("");
                }}
                title={desc}
              >
                <Icon size={16} />
                <span>{label}</span>
              </button>
            ))}
          </div>

          <div className="destiny-tab-body" role="tabpanel" aria-label={active.label}>
            {error && (
              <div className="destiny-error" role="alert">
                <CircleAlert size={16} />
                <span>{error}</span>
              </div>
            )}

            {activeTab === "natal" && (
              <div className="destiny-action-row">
                <div>
                  <h2>本命盘</h2>
                  <p>四柱、藏干十神、五行旺衰与大运起运；不混入生平时间轴。</p>
                </div>
                <button
                  type="button"
                  className="primary-button"
                  onClick={handleNatal}
                  disabled={!profileReady || loading === "natal"}
                >
                  {loading === "natal" ? <LoaderCircle size={16} className="spin" /> : <Sparkles size={16} />}
                  {natal ? "重新排盘" : "排本命盘"}
                </button>
              </div>
            )}

            {activeTab === "liunian" && (
              <div className="destiny-action-row destiny-range-row">
                <div>
                  <h2>流年</h2>
                  <p>按公历年份列出流年干支、十神、纳音、大运区间与四柱冲合。</p>
                </div>
                <div className="destiny-range-controls">
                  <label>
                    <span>起始年份</span>
                    <input
                      type="number"
                      min="1900"
                      max="2100"
                      value={startYear}
                      onChange={(event) => setStartYear(event.target.value)}
                    />
                  </label>
                  <label>
                    <span>年数</span>
                    <input
                      type="number"
                      min="1"
                      max="60"
                      value={count}
                      onChange={(event) => setCount(event.target.value)}
                    />
                  </label>
                  <button
                    type="button"
                    className="primary-button"
                    onClick={handleLiunian}
                    disabled={!profileReady || loading === "liunian"}
                  >
                    {loading === "liunian" ? <LoaderCircle size={16} className="spin" /> : <CalendarRange size={16} />}
                    {liunian ? "重新生成" : "生成流年"}
                  </button>
                </div>
              </div>
            )}

            {activeTab === "lifeline" && (
              <div className="destiny-action-row">
                <div>
                  <h2>生平时间轴</h2>
                  <p>起运后逐年事实、立春交接与皇极经世背景；已发生事件只做只读对齐。</p>
                </div>
              </div>
            )}

            {activeTab === "natal" && (
              natal ? (
                <BaziView result={natal} showLifeline={false} />
              ) : (
                <EmptyState title="尚未排本命盘" desc="填写出生信息后，点击「排本命盘」。" />
              )
            )}

            {activeTab === "liunian" && (
              liunian ? (
                <LiunianView data={liunian} />
              ) : (
                <EmptyState title="尚未生成流年" desc="设置起始年份与年数后，点击「生成流年」。" />
              )
            )}

            {activeTab === "lifeline" && (
              profileReady ? (
                <LifelineView
                  key={JSON.stringify(profile)}
                  result={{ input: payload }}
                />
              ) : (
                <EmptyState title="尚未录入出生信息" desc="填写出生信息后，在本页生成生平时间轴。" />
              )
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
