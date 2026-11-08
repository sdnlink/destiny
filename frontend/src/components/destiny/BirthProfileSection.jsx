import { CalendarClock, LocateFixed } from "lucide-react";

/** 命运专项共用的出生信息；本命盘、流年、生平时间轴都从这里取同一份入参。 */
export function BirthProfileSection({ profile, onChange }) {
  const update = (key, value) => onChange(key, value);

  return (
    <section className="form-section destiny-birth-section" aria-label="出生信息">
      <div className="section-title"><CalendarClock size={16} /><span>出生信息</span></div>
      <p className="standalone-form-hint">
        只用于本次命运分析，不写入经典推演存档；四个页签共用同一份出生时刻。
      </p>

      <label>
        <span className="field-label">公历出生日期时间</span>
        <input
          type="datetime-local"
          value={profile.localDatetime}
          min="1900-01-01T00:00"
          max="2100-12-31T23:59"
          onChange={(event) => update("localDatetime", event.target.value)}
          required
        />
      </label>

      <label>
        <span className="field-label">出生地时区</span>
        <div className="input-with-icon">
          <LocateFixed size={15} />
          <input
            value={profile.timezone}
            onChange={(event) => update("timezone", event.target.value)}
            placeholder="Asia/Shanghai"
            required
          />
        </div>
      </label>

      <div className="destiny-gender-row">
        <span className="field-label">性别</span>
        <div className="segmented method-switch" role="radiogroup" aria-label="命造性别">
          {["男", "女"].map((gender) => (
            <button
              key={gender}
              type="button"
              role="radio"
              aria-checked={profile.gender === gender}
              className={profile.gender === gender ? "active" : ""}
              onClick={() => update("gender", gender)}
            >
              {gender === "男" ? "乾造（男）" : "坤造（女）"}
            </button>
          ))}
        </div>
      </div>

      <div className="toggle-row">
        <div>
          <span className="field-label">真太阳时</span>
          <small>关闭时按出生地钟表时间；开启后需提供出生地经度</small>
        </div>
        <button
          className={`toggle ${profile.trueSolar ? "on" : ""}`}
          type="button"
          role="switch"
          aria-checked={profile.trueSolar}
          onClick={() => update("trueSolar", !profile.trueSolar)}
        >
          <span />
        </button>
      </div>

      {profile.trueSolar && (
        <label>
          <span className="field-label">出生地经度</span>
          <div className="input-with-suffix">
            <input
              type="number"
              min="-180"
              max="180"
              step="0.000001"
              value={profile.longitude}
              onChange={(event) => update("longitude", event.target.value)}
              placeholder="例如 116.4074"
              required
            />
            <span>°</span>
          </div>
        </label>
      )}
    </section>
  );
}

/** 四个页签统一使用的出生时刻 payload。 */
export function birthPayload(profile) {
  return {
    local_datetime: profile.localDatetime,
    timezone: profile.timezone.trim(),
    gender: profile.gender,
    longitude: profile.trueSolar ? Number(profile.longitude) : null,
    use_true_solar_time: profile.trueSolar,
  };
}
