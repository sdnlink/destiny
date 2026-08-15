import {
  BookOpen,
  CalendarClock,
  Check,
  ChevronRight,
  CircleAlert,
  Compass,
  Layers3,
  LoaderCircle,
  LocateFixed,
  Play,
  RotateCcw,
} from "lucide-react";

const SCENES = [
  { id: "combined", label: "综合推演", icon: Layers3 },
  { id: "zhouyi", label: "周易", icon: BookOpen },
  { id: "meihua", label: "梅花", icon: Compass },
];

const LINE_OPTIONS = [
  { value: 6, label: "老阴", glyph: "⚋ ×" },
  { value: 7, label: "少阳", glyph: "⚊" },
  { value: 8, label: "少阴", glyph: "⚋" },
  { value: 9, label: "老阳", glyph: "⚊ ○" },
];

const LINE_NAMES = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"];

function FieldLabel({ children, optional }) {
  return (
    <span className="field-label">
      {children}
      {optional && <span className="optional">选填</span>}
    </span>
  );
}

function NumberPair({ firstLabel, secondLabel, first, second, onFirst, onSecond }) {
  return (
    <div className="number-pair">
      <label>
        <FieldLabel>{firstLabel}</FieldLabel>
        <input type="number" value={first} onChange={(event) => onFirst(event.target.value)} required />
      </label>
      <label>
        <FieldLabel>{secondLabel}</FieldLabel>
        <input type="number" value={second} onChange={(event) => onSecond(event.target.value)} required />
      </label>
    </div>
  );
}

export default function InputPanel({
  form,
  setForm,
  onSubmit,
  onPreview,
  onReset,
  loading,
  previewLoading,
  preview,
  error,
}) {
  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const updateLine = (index, value) => {
    const lines = [...form.lines];
    lines[index] = value;
    update("lines", lines);
  };
  const showZhouyi = form.scene !== "meihua";
  const showMeihua = form.scene !== "zhouyi";

  return (
    <aside className="input-panel" aria-label="推演输入">
      <div className="panel-heading">
        <div>
          <p className="section-kicker">新建推演</p>
          <h1>推演参数</h1>
        </div>
        <button className="icon-button" type="button" onClick={onReset} title="重置全部输入" aria-label="重置全部输入">
          <RotateCcw size={17} />
        </button>
      </div>

      <form onSubmit={onSubmit}>
        <section className="form-section">
          <div className="section-title"><Layers3 size={16} /><span>体系与事项</span></div>
          <div className="segmented scene-switch" role="radiogroup" aria-label="推演体系">
            {SCENES.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                role="radio"
                aria-checked={form.scene === id}
                className={form.scene === id ? "active" : ""}
                onClick={() => update("scene", id)}
              >
                <Icon size={15} />{label}
              </button>
            ))}
          </div>
          <div className="field-grid">
            <label>
              <FieldLabel>事项分类</FieldLabel>
              <select value={form.category} onChange={(event) => update("category", event.target.value)}>
                <option value="career">事业</option>
                <option value="finance">财务</option>
                <option value="relationship">关系</option>
                <option value="travel">出行</option>
                <option value="study">学业</option>
                <option value="other">其他</option>
              </select>
            </label>
            <label>
              <FieldLabel>问题摘要</FieldLabel>
              <input
                value={form.question}
                onChange={(event) => update("question", event.target.value)}
                placeholder="仅用于本次会话标记"
                maxLength={80}
                required
              />
            </label>
          </div>
        </section>

        <section className="form-section">
          <div className="section-title"><CalendarClock size={16} /><span>时间基准</span></div>
          <label>
            <FieldLabel>本地日期时间</FieldLabel>
            <input
              type="datetime-local"
              value={form.localDatetime}
              min="1900-01-01T00:00"
              max="2100-12-31T23:59"
              onChange={(event) => update("localDatetime", event.target.value)}
              required
            />
          </label>
          <label>
            <FieldLabel>时区</FieldLabel>
            <div className="input-with-icon">
              <LocateFixed size={15} />
              <input
                value={form.timezone}
                onChange={(event) => update("timezone", event.target.value)}
                placeholder="Asia/Shanghai"
                required
              />
            </div>
          </label>
          <div className="toggle-row">
            <div>
              <span className="field-label">真太阳时</span>
              <small>默认关闭，启用后需提供经度</small>
            </div>
            <button
              className={`toggle ${form.trueSolar ? "on" : ""}`}
              type="button"
              role="switch"
              aria-checked={form.trueSolar}
              onClick={() => update("trueSolar", !form.trueSolar)}
            >
              <span />
            </button>
          </div>
          {form.trueSolar && (
            <label>
              <FieldLabel>经度</FieldLabel>
              <div className="input-with-suffix">
                <input
                  type="number"
                  min="-180"
                  max="180"
                  step="0.000001"
                  value={form.longitude}
                  onChange={(event) => update("longitude", event.target.value)}
                  placeholder="例如 116.4074"
                  required
                />
                <span>°</span>
              </div>
            </label>
          )}
          <button className="secondary-button full-button" type="button" onClick={onPreview} disabled={previewLoading}>
            {previewLoading ? <LoaderCircle className="spin" size={16} /> : <CalendarClock size={16} />}
            校验历法
          </button>
          {preview && (
            <div className="calendar-confirmation" aria-live="polite">
              <div className="confirmation-title"><Check size={14} />时间已校验</div>
              <div className="pillar-row mini">
                {Object.entries(preview.pillars).slice(0, 4).map(([key, value]) => (
                  <span key={key}><small>{{ year: "年", month: "月", day: "日", time: "时" }[key]}</small>{value}</span>
                ))}
              </div>
              <p>{preview.lunar.month_name}月{preview.lunar.day_name} · {preview.time.effective_local_datetime.slice(0, 16).replace("T", " ")}</p>
            </div>
          )}
        </section>

        {showZhouyi && (
          <section className="form-section">
            <div className="section-title"><BookOpen size={16} /><span>周易参数</span></div>
            <div className="segmented method-switch" role="radiogroup" aria-label="周易起卦方式">
              <button type="button" className={form.yiMethod === "manual" ? "active" : ""} onClick={() => update("yiMethod", "manual")}>手工六爻</button>
              <button type="button" className={form.yiMethod === "numbers" ? "active" : ""} onClick={() => update("yiMethod", "numbers")}>双数起卦</button>
            </div>
            {form.yiMethod === "manual" ? (
              <div className="line-inputs">
                {[...form.lines].reverse().map((value, reversedIndex) => {
                  const index = 5 - reversedIndex;
                  return (
                    <div className="line-input" key={index}>
                      <span>{LINE_NAMES[index]}</span>
                      <div className="line-options">
                        {LINE_OPTIONS.map((option) => (
                          <button
                            type="button"
                            key={option.value}
                            className={value === option.value ? "active" : ""}
                            onClick={() => updateLine(index, option.value)}
                            title={`${option.value} · ${option.label}`}
                            aria-label={`${LINE_NAMES[index]} ${option.value} ${option.label}`}
                          >
                            <b>{option.value}</b><span>{option.glyph}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <NumberPair
                firstLabel="下卦数"
                secondLabel="上卦数"
                first={form.yiLower}
                second={form.yiUpper}
                onFirst={(value) => update("yiLower", value)}
                onSecond={(value) => update("yiUpper", value)}
              />
            )}
          </section>
        )}

        {showMeihua && (
          <section className="form-section">
            <div className="section-title"><Compass size={16} /><span>梅花参数</span></div>
            <div className="segmented method-switch" role="radiogroup" aria-label="梅花起卦方式">
              <button type="button" className={form.meihuaMethod === "time" ? "active" : ""} onClick={() => update("meihuaMethod", "time")}>时间起卦</button>
              <button type="button" className={form.meihuaMethod === "numbers" ? "active" : ""} onClick={() => update("meihuaMethod", "numbers")}>双数起卦</button>
            </div>
            {form.meihuaMethod === "time" ? (
              <div className="method-note">
                <CalendarClock size={16} />
                <p>采用上方已确认时间，按年支、农历月日及时支取数。</p>
              </div>
            ) : (
              <NumberPair
                firstLabel="上卦数"
                secondLabel="下卦数"
                first={form.mhUpper}
                second={form.mhLower}
                onFirst={(value) => update("mhUpper", value)}
                onSecond={(value) => update("mhLower", value)}
              />
            )}
          </section>
        )}

        {error && <div className="form-error" role="alert"><CircleAlert size={17} /><span>{error}</span></div>}

        <div className="submit-bar">
          <div className="submit-meta">
            <span>{form.scene === "combined" ? "3 个计算模块" : "2 个计算模块"}</span>
            <small>工程基线 · 无自动吉凶评分</small>
          </div>
          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? <LoaderCircle className="spin" size={17} /> : <Play size={17} fill="currentColor" />}
            {loading ? "正在推演" : "开始推演"}
            {!loading && <ChevronRight size={16} />}
          </button>
        </div>
      </form>
    </aside>
  );
}
