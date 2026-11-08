import { CircleAlert, Info } from "lucide-react";

export function BazhaiView({ result }) {
  const facts = result?.facts;
  if (!facts) {
    return (
      <div className="standalone-empty" role="status">
        <CircleAlert size={22} />
        <strong>八宅结果缺少盘面事实</strong>
        <p>后端返回中没有 facts 字段，未渲染空盘。</p>
      </div>
    );
  }

  return (
    <div className="view-stack">
      <section className="view-heading">
        <div>
          <span className="section-kicker">BA ZHAI</span>
          <h2>八宅大游年盘</h2>
          <p>按坐山定宅卦与东西四宅，再以《八宅明鏡》大游年歌排出八方九星。只列方位事实，不生成吉凶断语。</p>
        </div>
      </section>

      <div className="bazhai-summary">
        <div>
          <span>坐山</span>
          <strong>{facts.sitting_mountain}</strong>
          <small>{facts.sitting_trigram}卦</small>
        </div>
        <div>
          <span>宅卦</span>
          <strong>{facts.sitting_trigram}</strong>
          <small>{facts.house_group}</small>
        </div>
        <div>
          <span>吉方</span>
          <strong>{facts.lucky_directions.join(" · ")}</strong>
          <small>生气 / 天医 / 延年 / 伏位</small>
        </div>
        <div>
          <span>凶方</span>
          <strong>{facts.unlucky_directions.join(" · ")}</strong>
          <small>五鬼 / 六煞 / 祸害 / 绝命</small>
        </div>
      </div>

      <section className="data-section">
        <div className="section-title"><Info size={16} /><span>宅命配法</span></div>
        {facts.life_match ? (
          <div className="bazhai-life-match">
            <p>
              命卦 <strong>{facts.life_match.life_trigram}</strong>（{facts.life_match.life_group}） · 宅卦{" "}
              <strong>{facts.life_match.house_group}</strong> ·{" "}
              <strong>{facts.life_match.group_match ? "宅命同组" : "宅命异组"}</strong>
            </p>
            <small>{facts.life_match.note}</small>
          </div>
        ) : (
          <p className="standalone-form-hint">未填写出生年份，本盘只排宅卦与大游年方位，不做宅命配法。</p>
        )}
      </section>

      <section className="data-section">
        <div className="section-title"><Info size={16} /><span>八方九星</span></div>
        <div className="bazhai-grid">
          {facts.directions.map((row) => (
            <article className={`bazhai-cell ${row.nature === "吉" ? "auspicious" : "inauspicious"}`} key={row.palace}>
              <div className="bazhai-cell-head">
                <span>{row.direction} · {row.palace}宫</span>
                <b>{row.nature}</b>
              </div>
              <strong>{row.star}</strong>
              <p>{row.star_animal} · {row.element}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="data-section">
        <div className="section-title"><Info size={16} /><span>大游年歌</span></div>
        <p className="bazhai-song">{facts.song}</p>
        <small className="standalone-form-hint">{facts.song_note}</small>
      </section>

      {result.warnings?.length > 0 && (
        <section className="data-section">
          <div className="section-title"><CircleAlert size={16} /><span>边界</span></div>
          {result.warnings.map((warning) => <p className="standalone-form-hint" key={warning}>{warning}</p>)}
        </section>
      )}
    </div>
  );
}
