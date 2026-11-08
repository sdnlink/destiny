import { CircleAlert, Grid3X3, Info } from "lucide-react";

const PALACE_LAYOUT = [
  ["巽", "离", "坤"],
  ["震", "中", "兑"],
  ["艮", "坎", "乾"],
];

export function XuankongView({ result }) {
  const facts = result?.facts;
  if (!facts) {
    return (
      <div className="standalone-empty" role="status">
        <CircleAlert size={22} />
        <strong>玄空结果缺少盘面事实</strong>
        <p>后端返回中没有 facts 字段，未渲染空盘。</p>
      </div>
    );
  }

  const grid = Object.fromEntries((facts.grid || []).map((row) => [row.palace, row]));

  return (
    <div className="view-stack">
      <section className="view-heading">
        <div>
          <span className="section-kicker">XUAN KONG</span>
          <h2>玄空挨星盘</h2>
          <p>
            坐山 {facts.sitting_mountain} · 向首 {facts.facing_mountain} · {facts.period_label}。
            运星入中顺逆飞布，山星、向星分列各宫；格局条件为确定性判定，不含吉凶断语。
          </p>
        </div>
      </section>

      <div className="xuankong-summary">
        <div><span>坐山</span><strong>{facts.sitting_mountain}</strong><small>元龙 {facts.sitting_yuan_dragon}</small></div>
        <div><span>向首</span><strong>{facts.facing_mountain}</strong><small>元龙 {facts.facing_yuan_dragon}</small></div>
        <div><span>运</span><strong>{facts.period}</strong><small>{facts.period_label}</small></div>
        <div><span>飞布</span><strong>{facts.fly_direction?.sitting}</strong><small>山 {facts.fly_direction?.sitting} / 向 {facts.fly_direction?.facing}</small></div>
      </div>

      <section className="data-section">
        <div className="section-title"><Grid3X3 size={16} /><span>九宫挨星</span></div>
        <div className="xuankong-grid">
          {PALACE_LAYOUT.flat().map((palace) => {
            const row = grid[palace];
            return (
              <article className={`xuankong-cell ${palace === "中" ? "center" : ""}`} key={palace}>
                <div className="xuankong-cell-head"><span>{palace}宫</span></div>
                <div className="xuankong-stars">
                  <span className="period">运 {row?.period_star ?? "—"}</span>
                  <span className="mountain">山 {row?.mountain_star ?? "—"}</span>
                  <span className="facing">向 {row?.facing_star ?? "—"}</span>
                </div>
              </article>
            );
          })}
        </div>
      </section>

      <section className="data-section">
        <div className="section-title"><Info size={16} /><span>格局条件</span></div>
        <div className="xuankong-conditions">
          {(facts.conditions || []).map((condition) => (
            <div className={condition.met ? "condition met" : "condition"} key={condition.name}>
              <b>{condition.name}</b>
              <span>{condition.met ? "成立" : "不成立"}</span>
              {condition.note && <small>{condition.note}</small>}
            </div>
          ))}
        </div>
      </section>

      <section className="data-section">
        <div className="section-title"><Info size={16} /><span>替卦判定</span></div>
        <p className="standalone-form-hint">{facts.ti_pu?.note}</p>
        <small className="standalone-form-hint">{facts.fly_direction?.note}</small>
      </section>

      {facts.tihua_reference && (
        <section className="data-section">
          <div className="section-title"><Info size={16} /><span>替星表参考</span></div>
          <div className="xuankong-tihua">
            <div>
              <span>坐山替星</span>
              <strong>{facts.tihua_reference.sitting?.mountain} → {facts.tihua_reference.sitting?.tihua_star} 入中</strong>
            </div>
            <div>
              <span>向首替星</span>
              <strong>{facts.tihua_reference.facing?.mountain} → {facts.tihua_reference.facing?.tihua_star} 入中</strong>
            </div>
          </div>
          <small className="standalone-form-hint">{facts.tihua_reference.note}</small>
        </section>
      )}

      {facts.tihua_chart && (
        <section className="data-section">
          <div className="section-title"><Grid3X3 size={16} /><span>替卦起星盘（工程基线）</span></div>
          <div className="tihua-chart-blocks">
            {[["坐山", facts.tihua_chart.sitting], ["向首", facts.tihua_chart.facing]].map(([label, data]) => (
              data && (
                <div className="tihua-chart-block" key={label}>
                  <strong>{label} {data.status === "completed" ? "已起星" : data.status}</strong>
                  <small>
                    到星 {data.arriving_star} · 替星 {data.tihua_star}
                    {data.substitute_mountain ? ` · 替山 ${data.substitute_mountain}` : " · 无替可寻"}
                    {data.fly_direction ? ` · ${data.fly_direction}` : ""}
                  </small>
                  <div className="tihua-chart-grid">
                    {PALACE_LAYOUT.flat().map((palace) => (
                      <div className={palace === "中" ? "center" : ""} key={palace}>
                        <span>{palace}</span>
                        <b>{data.chart?.[palace] ?? "—"}</b>
                      </div>
                    ))}
                  </div>
                </div>
              )
            ))}
          </div>
          <small className="standalone-form-hint">{facts.tihua_chart.note}</small>
        </section>
      )}

      {result.warnings?.length > 0 && (
        <section className="data-section">
          <div className="section-title"><CircleAlert size={16} /><span>边界</span></div>
          {result.warnings.map((warning) => <p className="standalone-form-hint" key={warning}>{warning}</p>)}
        </section>
      )}
    </div>
  );
}
