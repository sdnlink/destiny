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

function MountainFact({ label, direction }) {
  const mountain = direction.mountain;
  return (
    <div className="direction-fact">
      <span>{label}</span>
      <strong>{mountain.name}</strong>
      <b>{direction.degree}°</b>
      <p>{mountain.trigram}卦 · {mountain.element} · {mountain.direction}</p>
      <small>区间 [{mountain.start_degree}°, {mountain.end_degree}°)</small>
    </div>
  );
}

function FengshuiCompassDial({ facingDegree = 0, sittingDegree = 180 }) {
  return (
    <div className="fengshui-compass-widget">
      <svg viewBox="0 0 300 300" className="luopan-svg" aria-label="二十四山罗盘">
        <circle cx="150" cy="150" r="140" fill="#252b28" stroke="#a66d1e" strokeWidth="3" />
        <circle cx="150" cy="150" r="120" fill="#2d3531" stroke="#d9d8d1" strokeWidth="1" strokeDasharray="3 3" />
        <circle cx="150" cy="150" r="85" fill="#202622" stroke="#a66d1e" strokeWidth="1.5" />
        <circle cx="150" cy="150" r="40" fill="#181d1a" stroke="#823024" strokeWidth="2" />
        
        <text x="150" y="28" textAnchor="middle" fill="#d9d8d1" fontSize="13" fontWeight="bold">北 (子)</text>
        <text x="278" y="154" textAnchor="middle" fill="#d9d8d1" fontSize="13" fontWeight="bold">东 (卯)</text>
        <text x="150" y="282" textAnchor="middle" fill="#d9d8d1" fontSize="13" fontWeight="bold">南 (午)</text>
        <text x="22" y="154" textAnchor="middle" fill="#d9d8d1" fontSize="13" fontWeight="bold">西 (酉)</text>

        <g transform={`rotate(${facingDegree}, 150, 150)`}>
          <polygon points="150,45 143,150 157,150" fill="#c62828" />
          <polygon points="150,255 143,150 157,150" fill="#1565c0" />
          <circle cx="150" cy="150" r="6" fill="#a66d1e" />
        </g>
      </svg>
      <div className="luopan-legend">
        <span className="legend-facing"><i />向首：{facingDegree}°</span>
        <span className="legend-sitting"><i />坐山：{sittingDegree}°</span>
      </div>
    </div>
  );
}

function MeasurementConsensusView({ result }) {
  const { measurements, consensus } = result.facts;
  const aggregate = consensus.aggregate;
  const statusLabels = { consistent: "一致", boundary_sensitive: "跨山界", inconsistent: "读数不一致" };
  return (
    <div className="view-stack">
      <section className="view-heading">
        <div><span className="section-kicker">FENGSHUI MEASUREMENT CONSENSUS</span><h2>阳宅多次测量共识</h2><p>每次读数独立修正真北，再以圆周统计汇总方向和保守误差。</p></div>
        <span className="version-badge">{result.rule_version}</span>
      </section>
      <section className="liuren-facts-band">
        <DataState label="测量次数" value={consensus.sample_count} />
        <DataState label="共识状态" value={statusLabels[consensus.status]} />
        <DataState label="最小覆盖弧" value={`${consensus.angular_spread}°`} />
        <DataState label="方向集中度" value={consensus.resultant_length} mono />
      </section>
      {aggregate ? (
        <>
          <section className="direction-primary-grid">
            <MountainFact label="共识坐山" direction={aggregate.sitting} />
            <div className="direction-axis"><ArrowRight size={24} /><span>相差 180°</span></div>
            <MountainFact label="共识向首" direction={aggregate.facing} />
          </section>
          <FengshuiCompassDial facingDegree={aggregate.facing.degree} sittingDegree={aggregate.sitting.degree} />
          <section className="data-band">
            <div className="band-heading"><div><span className="band-icon"><ShieldCheck size={16} /></span><div><h3>保守误差范围</h3><p>包含每次读数偏差与设备误差</p></div></div></div>
            <div className="comparison-counts">
              <DataState label="圆周均值" value={`${consensus.circular_mean_degree}°`} />
              <DataState label="最大偏差" value={`${consensus.maximum_deviation}°`} />
              <DataState label="合并误差 ±" value={`${consensus.effective_measurement_error}°`} />
              <DataState label="向首候选" value={aggregate.facing.candidate_mountains.map((item) => item.name).join("、")} />
            </div>
          </section>
        </>
      ) : <Notice tone="warning" icon={CircleAlert}>这些读数不能形成唯一方向，系统未生成合并山向。请检查是否混入坐山读数或测量方向相反。</Notice>}
      <section className="data-band">
        <div className="band-heading"><div><span className="band-icon"><Compass size={16} /></span><div><h3>逐次真北读数</h3><p>原始输入与修正结果并列保留</p></div></div></div>
        <div className="measurement-table-wrap">
          <table className="measurement-table">
            <thead><tr><th>次数</th><th>原始角度</th><th>基准</th><th>磁偏角</th><th>真北角</th><th>山向</th><th>距分界</th></tr></thead>
            <tbody>{measurements.map((row) => <tr key={row.sequence}>
              <td>{row.sequence}</td><td>{row.input.facing_degree}°</td><td>{row.input.input_reference === "magnetic" ? "磁北" : "真北"}</td>
              <td>{row.input.magnetic_declination}°</td><td>{row.true_facing_degree}°</td><td>{row.facing_mountain.name}</td><td>{row.distance_to_boundary}°</td>
            </tr>)}</tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function FengshuiView({ result }) {
  if (!result) return <MissingModule name="阳宅风水" />;
  if (result.facts.mode === "multiple_measurements") return <MeasurementConsensusView result={result} />;
  const { facts } = result;
  const facing = facts.facing;
  const sitting = facts.sitting;
  return (
    <div className="view-stack">
      <section className="view-heading">
        <div><span className="section-kicker">FENGSHUI DIRECTION</span><h2>阳宅真北坐向与二十四山</h2><p>磁偏角、坐向换算、二十四山和测量误差按独立规则计算。</p></div>
        <span className="version-badge">{result.rule_version}</span>
      </section>

      <section className="direction-primary-grid">
        <MountainFact label="坐山" direction={sitting} />
        <div className="direction-axis"><ArrowRight size={24} /><span>相差 180°</span></div>
        <MountainFact label="向首" direction={facing} />
      </section>

      <FengshuiCompassDial facingDegree={facts.true_facing_degree} sittingDegree={facts.true_sitting_degree} />

      <section className="two-column-data">
        <div className="data-band">
          <div className="band-heading"><div><span className="band-icon"><Compass size={16} /></span><div><h3>真北修正</h3><p>{result.normalized_input.input_reference === "magnetic" ? "磁北输入" : "真北输入"}</p></div></div></div>
          <div className="key-value-list">
            <DataState label="原始角度" value={`${result.normalized_input.input_degree}°`} />
            <DataState label="应用磁偏角" value={`${result.normalized_input.applied_declination}°`} />
            <DataState label="真北向首" value={`${facts.true_facing_degree}°`} />
            <DataState label="真北坐山" value={`${facts.true_sitting_degree}°`} />
          </div>
        </div>
        <div className="data-band">
          <div className="band-heading"><div><span className="band-icon"><ShieldCheck size={16} /></span><div><h3>测量稳定性</h3><p>误差 ±{result.normalized_input.measurement_error}°</p></div></div></div>
          <div className="key-value-list">
            <DataState label="分类状态" value={facts.classification_stable ? "稳定" : "跨越分界"} />
            <DataState label="距最近分界" value={`${facing.distance_to_boundary}°`} />
            <DataState label="向首候选" value={facing.candidate_mountains.map((item) => item.name).join("、")} />
            <DataState label="坐山候选" value={sitting.candidate_mountains.map((item) => item.name).join("、")} />
          </div>
        </div>
      </section>
      <section className="data-band">
        <div className="band-heading"><div><span className="band-icon"><ListTree size={16} /></span><div><h3>计算依据</h3><p>{result.engine_version}</p></div></div></div>
        <Steps steps={result.steps} />
      </section>
    </div>
  );
}

export { FengshuiView };
