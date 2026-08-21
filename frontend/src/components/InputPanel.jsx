import {
  BookOpen,
  CalendarClock,
  Check,
  ChevronRight,
  CircleAlert,
  Compass,
  Grid3X3,
  Layers3,
  LoaderCircle,
  LocateFixed,
  Mountain,
  Plus,
  Play,
  RefreshCw,
  RotateCcw,
  Sparkles,
  Trash2,
  Workflow,
} from "lucide-react";

const SCENES = [
  { id: "combined", label: "综合推演", icon: Layers3 },
  { id: "zhouyi", label: "周易", icon: BookOpen },
  { id: "meihua", label: "梅花", icon: Compass },
  { id: "liuyao", label: "六爻", icon: Grid3X3 },
  { id: "liuren", label: "六壬", icon: Workflow },
  { id: "qimen", label: "奇门", icon: Compass },
  { id: "bazi", label: "八字", icon: Sparkles },
  { id: "ziwei", label: "紫微", icon: Sparkles },
  { id: "fengshui", label: "风水", icon: Mountain },
];

const QUESTION_PRESETS = [
  { category: "other", question: "推算李笑穿的是什么颜色的衣服，他正在做什么事情" },
  { category: "other", question: "遗失的钱包钥匙在什么方位，物品特征如何" },
  { category: "travel", question: "推算对方随身带了什么配饰，采用何种出行方式" },
  { category: "other", question: "推算身体哪个部位需要注意调理与保养" },
  { category: "career", question: "是否接受新的工作机会与团队邀请" },
  { category: "finance", question: "近期重大项目投资与资金布局可行性" },
  { category: "relationship", question: "跨团队商务合作与关键人际沟通走势" },
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
  onRecast,
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
  const updateMeasurement = (index, value) => {
    const measurements = [...form.fsMeasurements];
    measurements[index] = value;
    update("fsMeasurements", measurements);
  };
  const addMeasurement = () => {
    if (form.fsMeasurements.length < 12) update("fsMeasurements", [...form.fsMeasurements, "180"]);
  };
  const removeMeasurement = (index) => {
    if (form.fsMeasurements.length > 3) {
      update("fsMeasurements", form.fsMeasurements.filter((_, current) => current !== index));
    }
  };
  const showZhouyi = form.scene === "combined" || form.scene === "zhouyi";
  const showMeihua = form.scene === "combined" || form.scene === "meihua";
  const showLiuyao = form.scene === "combined" || form.scene === "liuyao";
  const showLiuren = form.scene === "combined" || form.scene === "liuren";
  const showQimen = form.scene === "combined" || form.scene === "qimen";
  const showBazi = form.scene === "combined" || form.scene === "bazi";
  const showZiwei = form.scene === "combined" || form.scene === "ziwei";
  const showFengshui = form.scene === "fengshui";

  return (
    <aside className="input-panel" aria-label="推演输入">
      <div className="panel-heading">
        <div>
          <p className="section-kicker">新建推演</p>
          <h1>推演参数</h1>
        </div>
        <div className="panel-heading-actions">
          <span className="cast-token" title="本次起卦凭证">凭证 {form.castNonce.slice(0, 8)}</span>
          <button className="icon-button" type="button" onClick={onRecast} title="重新起卦" aria-label="重新起卦">
            <RefreshCw size={17} />
          </button>
          <button className="icon-button" type="button" onClick={onReset} title="重置全部输入" aria-label="重置全部输入">
            <RotateCcw size={17} />
          </button>
        </div>
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
                placeholder="例如：是否接受新的工作机会"
                maxLength={200}
                required
              />
              <small className="field-hint">用于生成事项建议，不进入排盘公式且不持久化</small>
            </label>
          </div>
          <div className="preset-questions-row">
            <span className="preset-label">快捷示例：</span>
            <div className="preset-chips">
              {QUESTION_PRESETS.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="preset-chip"
                  onClick={() => {
                    update("category", p.category);
                    update("question", p.question);
                  }}
                >
                  {p.question}
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="form-section">
          <div className="section-title"><CalendarClock size={16} /><span>时间基准</span></div>
          <div className="field-head-with-action">
            <FieldLabel>本地日期时间</FieldLabel>
            <button
              type="button"
              className="link-action-btn"
              onClick={() => {
                const now = new Date();
                const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
                update("localDatetime", local.toISOString().slice(0, 16));
              }}
            >
              设为当前时间
            </button>
          </div>
          <label>
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
              <button type="button" className={form.yiMethod === "auto" ? "active" : ""} onClick={() => update("yiMethod", "auto")}>个体自动</button>
              <button type="button" className={form.yiMethod === "time" ? "active" : ""} onClick={() => update("yiMethod", "time")}>传统时间</button>
              <button type="button" className={form.yiMethod === "numbers" ? "active" : ""} onClick={() => update("yiMethod", "numbers")}>数字排盘</button>
              <button type="button" className={form.yiMethod === "manual" ? "active" : ""} onClick={() => update("yiMethod", "manual")}>手工排盘</button>
            </div>
            {form.yiMethod === "auto" ? (
              <div className="method-note">
                <RefreshCw size={16} />
                <p>按本次独立凭证模拟六次三枚铜钱，结果可复算。</p>
              </div>
            ) : form.yiMethod === "time" ? (
              <div className="method-note">
                <CalendarClock size={16} />
                <p>采用上方时间，按年支、农历月日及时支自动生成卦盘。</p>
              </div>
            ) : form.yiMethod === "manual" ? (
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
              <button type="button" className={form.meihuaMethod === "auto" ? "active" : ""} onClick={() => update("meihuaMethod", "auto")}>个体自动</button>
              <button type="button" className={form.meihuaMethod === "time" ? "active" : ""} onClick={() => update("meihuaMethod", "time")}>传统时间</button>
              <button type="button" className={form.meihuaMethod === "numbers" ? "active" : ""} onClick={() => update("meihuaMethod", "numbers")}>数字排盘</button>
            </div>
            {form.meihuaMethod === "auto" ? (
              <div className="method-note">
                <RefreshCw size={16} />
                <p>年月日時取数加入本次独立个体数，保留传统时间结构。</p>
              </div>
            ) : form.meihuaMethod === "time" ? (
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

        {showLiuyao && (
          <section className="form-section">
            <div className="section-title"><Grid3X3 size={16} /><span>六爻参数</span></div>
            <div className="segmented method-switch" role="radiogroup" aria-label="六爻排盘方式">
              <button type="button" className={form.liuyaoMethod === "auto" ? "active" : ""} onClick={() => update("liuyaoMethod", "auto")}>个体自动</button>
              <button type="button" className={form.liuyaoMethod === "time" ? "active" : ""} onClick={() => update("liuyaoMethod", "time")}>传统时间</button>
              <button type="button" className={form.liuyaoMethod === "numbers" ? "active" : ""} onClick={() => update("liuyaoMethod", "numbers")}>数字排盘</button>
            </div>
            {form.liuyaoMethod === "auto" ? (
              <div className="method-note">
                <RefreshCw size={16} />
                <p>按本次独立凭证生成六次铜钱结果，再排八宫、纳甲和六亲。</p>
              </div>
            ) : form.liuyaoMethod === "time" ? (
              <div className="method-note">
                <CalendarClock size={16} />
                <p>按时间取卦，并自动生成八宫、世应、纳甲、六亲、六神与旬空。</p>
              </div>
            ) : (
              <NumberPair
                firstLabel="下卦数"
                secondLabel="上卦数"
                first={form.lyLower}
                second={form.lyUpper}
                onFirst={(value) => update("lyLower", value)}
                onSecond={(value) => update("lyUpper", value)}
              />
            )}
          </section>
        )}

        {showLiuren && (
          <section className="form-section">
            <div className="section-title"><Workflow size={16} /><span>大六壬参数</span></div>
            <div className="segmented method-switch" role="radiogroup" aria-label="大六壬排盘方式">
              <button type="button" className={form.liurenMethod === "auto" ? "active" : ""} onClick={() => update("liurenMethod", "auto")}>个体自动</button>
              <button type="button" className={form.liurenMethod === "time" ? "active" : ""} onClick={() => update("liurenMethod", "time")}>传统时间</button>
              <button type="button" className={form.liurenMethod === "numbers" ? "active" : ""} onClick={() => update("liurenMethod", "numbers")}>数字排盘</button>
            </div>
            {form.liurenMethod === "auto" ? (
              <div className="method-note">
                <RefreshCw size={16} />
                <p>由本次独立凭证生成报数决定占时，同时保留实际时支。</p>
              </div>
            ) : form.liurenMethod === "time" ? (
              <div className="method-note">
                <CalendarClock size={16} />
                <p>采用实际时支为占时，排月将、天地盘、四课、三传和十二天将。</p>
              </div>
            ) : (
              <label>
                <FieldLabel>占时数</FieldLabel>
                <input type="number" value={form.lrNumber} onChange={(event) => update("lrNumber", event.target.value)} required />
                <small className="field-hint">除以12取余映射子至亥，仅替换占时，不修改历法日柱</small>
              </label>
            )}
          </section>
        )}

        {showQimen && (
          <section className="form-section">
            <div className="section-title">
              <Compass size={16} />
              <span>时家转盘奇门遁甲</span>
            </div>
            <div className="segmented method-switch" role="radiogroup" aria-label="奇门排盘模式">
              <button
                type="button"
                className={(form.qimenMethod || "time") === "time" ? "active" : ""}
                onClick={() => update("qimenMethod", "time")}
              >
                传统时间
              </button>
              <button
                type="button"
                className={form.qimenMethod === "auto" ? "active" : ""}
                onClick={() => update("qimenMethod", "auto")}
              >
                个体自动
              </button>
            </div>
            <div className="method-note">
              <Compass size={16} />
              <p>拆补法定阴阳局，排布九星、八门、八神与三奇六仪格局。</p>
            </div>
          </section>
        )}

        {showBazi && (
          <section className="form-section">
            <div className="section-title">
              <Sparkles size={16} />
              <span>八字四柱命理</span>
            </div>
            <div className="segmented method-switch" role="radiogroup" aria-label="八字排盘模式">
              <button
                type="button"
                className={form.baziMethod === "time" ? "active" : ""}
                onClick={() => update("baziMethod", "time")}
              >
                传统时间
              </button>
              <button
                type="button"
                className={form.baziMethod === "auto" ? "active" : ""}
                onClick={() => update("baziMethod", "auto")}
              >
                个体自动
              </button>
            </div>
            <div className="input-row">
              <label>
                <FieldLabel>命造性别</FieldLabel>
                <div className="segmented">
                  <button
                    type="button"
                    className={(form.baziGender || "男") === "男" ? "active" : ""}
                    onClick={() => update("baziGender", "男")}
                  >
                    乾造（男命）
                  </button>
                  <button
                    type="button"
                    className={form.baziGender === "女" ? "active" : ""}
                    onClick={() => update("baziGender", "女")}
                  >
                    坤造（女命）
                  </button>
                </div>
                <small className="field-hint">用于顺逆排布大运与起运交运折算</small>
              </label>
            </div>
          </section>
        )}

        {showZiwei && (
          <section className="form-section">
            <div className="section-title">
              <Sparkles size={16} />
              <span>紫微斗数</span>
            </div>
            <div className="segmented method-switch" role="radiogroup" aria-label="紫微斗数排盘模式">
              <button
                type="button"
                className={form.ziweiMethod === "time" ? "active" : ""}
                onClick={() => update("ziweiMethod", "time")}
              >
                传统时间
              </button>
              <button
                type="button"
                className={form.ziweiMethod === "auto" ? "active" : ""}
                onClick={() => update("ziweiMethod", "auto")}
              >
                个体自动
              </button>
            </div>
            <div className="input-row">
              <label>
                <FieldLabel>命造性别</FieldLabel>
                <div className="segmented">
                  <button
                    type="button"
                    className={form.ziweiGender === "男" ? "active" : ""}
                    onClick={() => update("ziweiGender", "男")}
                  >
                    乾造（男命）
                  </button>
                  <button
                    type="button"
                    className={form.ziweiGender === "女" ? "active" : ""}
                    onClick={() => update("ziweiGender", "女")}
                  >
                    坤造（女命）
                  </button>
                </div>
                <small className="field-hint">用于推算阴阳男女与起运大限顺逆</small>
              </label>
            </div>
          </section>
        )}

        {showFengshui && (
          <section className="form-section">
            <div className="section-title"><Mountain size={16} /><span>阳宅坐向测量</span></div>
            <div className="segmented method-switch" role="radiogroup" aria-label="坐向测量模式">
              <button type="button" className={form.fsMode === "single" ? "active" : ""} onClick={() => update("fsMode", "single")}>单次分析</button>
              <button type="button" className={form.fsMode === "multiple" ? "active" : ""} onClick={() => update("fsMode", "multiple")}>多次共识</button>
            </div>
            {form.fsMode === "single" ? (
              <label>
                <FieldLabel>向首方位角</FieldLabel>
                <input type="number" step="0.01" value={form.fsFacing} onChange={(event) => update("fsFacing", event.target.value)} required />
                <small className="field-hint">正北为 0°，顺时针增加；应填写建筑向首的现场测量值</small>
              </label>
            ) : (
              <div className="measurement-inputs">
                <div className="measurement-inputs-head"><FieldLabel>向首读数</FieldLabel><small>{form.fsMeasurements.length} / 12</small></div>
                {form.fsMeasurements.map((value, index) => (
                  <div className="measurement-input-row" key={index}>
                    <span>{index + 1}</span>
                    <input aria-label={`第${index + 1}次向首读数`} type="number" step="0.01" value={value} onChange={(event) => updateMeasurement(index, event.target.value)} required />
                    <button className="icon-button" type="button" title="删除本次读数" aria-label={`删除第${index + 1}次读数`} disabled={form.fsMeasurements.length <= 3} onClick={() => removeMeasurement(index)}><Trash2 size={15} /></button>
                  </div>
                ))}
                <button className="secondary-command" type="button" disabled={form.fsMeasurements.length >= 12} onClick={addMeasurement}><Plus size={15} />增加读数</button>
              </div>
            )}
            <div className="segmented method-switch" role="radiogroup" aria-label="方位角基准">
              <button type="button" className={form.fsReference === "magnetic" ? "active" : ""} onClick={() => update("fsReference", "magnetic")}>磁北测量</button>
              <button type="button" className={form.fsReference === "true" ? "active" : ""} onClick={() => update("fsReference", "true")}>真北测量</button>
            </div>
            <div className="number-pair">
              <label>
                <FieldLabel>磁偏角</FieldLabel>
                <input type="number" step="0.01" value={form.fsDeclination} onChange={(event) => update("fsDeclination", event.target.value)} required />
              </label>
              <label>
                <FieldLabel>测量误差 ±</FieldLabel>
                <input type="number" step="0.01" min="0" max="180" value={form.fsError} onChange={(event) => update("fsError", event.target.value)} required />
              </label>
            </div>
            <div className="method-note">
              <LocateFixed size={16} />
              <p>{form.fsMode === "multiple" ? "每次读数独立修正真北，再用圆周均值汇总；离散超过 10° 时不生成可信坐向。" : "磁北角按“真北角 = 磁北角 + 磁偏角”修正；误差跨界时保留全部候选。"}</p>
            </div>
          </section>
        )}

        {error && <div className="form-error" role="alert"><CircleAlert size={17} /><span>{error}</span></div>}

        <div className="submit-bar">
          <div className="submit-meta">
            <span>{form.scene === "combined" ? "5 个计算模块" : "2 个计算模块"}</span>
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
