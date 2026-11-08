import { CalendarRange, CircleAlert, GitBranch } from "lucide-react";
import { Notice } from "../result/shared";

function relationText(year) {
  const relations = [
    ...(year.branch_relations || []).map((row) => `${row.type}${row.with}（${row.branches}）`),
    ...(year.stem_relations || []).map((row) => `${row.type}${row.with}（${row.stems}）`),
  ];
  return relations.length ? relations.join(" · ") : "无显著冲合";
}

function luckText(luckPillar) {
  if (!luckPillar) return "未入大运";
  return `${luckPillar.ganzhi}（第${luckPillar.index}步）`;
}

/** 逐年流年事实表：只展示确定性干支、十神、大运区间与冲合组合。 */
export function LiunianView({ data }) {
  if (!data) return null;
  const years = data.years || [];
  const luckStart = data.natal_summary?.luck_start_info || {};

  return (
    <section className="data-band destiny-liunian-band">
      <div className="band-heading">
        <div>
          <span className="band-icon"><CalendarRange size={16} /></span>
          <div>
            <h3>流年逐年事实（子平岁运）</h3>
            <p>流年干支、十神、纳音、大运区间与四柱冲合；不生成吉凶断语</p>
          </div>
        </div>
        <span className="version-badge">{data.rule_id}</span>
      </div>

      <div className="liuren-facts-band destiny-liunian-summary">
        <div><small>日元</small><b>{data.day_master || "—"}</b></div>
        <div><small>出生年</small><b>{data.birth_year || "—"}</b></div>
        <div><small>覆盖区间</small><b>{data.start_year}–{(years[years.length - 1] || {}).year || data.start_year}</b></div>
        <div><small>起运</small><b>{luckStart.description || "见本命盘大运"}</b></div>
      </div>

      <div className="lifeline-table-wrap">
        <table className="lifeline-table destiny-liunian-table">
          <thead>
            <tr>
              <th>年份 / 干支</th>
              <th>年龄</th>
              <th>十神 · 纳音</th>
              <th>所属大运</th>
              <th>岁运组合事实</th>
              <th>太岁 / 岁破</th>
            </tr>
          </thead>
          <tbody>
            {years.map((year) => (
              <tr key={year.year}>
                <td><b>{year.year}</b> {year.ganzhi}<small>{year.stem} · {year.branch}</small></td>
                <td>{year.age} 岁<small>虚岁 {year.virtual_age}</small></td>
                <td>{year.stem_ten_god}<small>{year.nayin}</small></td>
                <td>{luckText(year.luck_pillar)}<small>{year.luck_pillar?.stem_ten_god || "未覆盖"}</small></td>
                <td className="destiny-relation-cell">{relationText(year)}</td>
                <td>{year.taisui_branch} / {year.suipo_branch}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {(data.warnings || []).map((warning, index) => (
        <Notice key={index} tone="warning" icon={CircleAlert}>{warning}</Notice>
      ))}
      <p className="muted-copy">
        <GitBranch size={13} /> {data.school} · {data.status}
      </p>
    </section>
  );
}
