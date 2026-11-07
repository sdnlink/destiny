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

// 四课上下神关系：后端只会给这三种，未知值原样显示而不是一律当成「上克下」
const LESSON_RELATION_LABELS = {
  none: "无直接克",
  lower_controls_upper: "下克上",
  upper_controls_lower: "上克下",
};

function LiurenView({ result }) {
  if (!result) return <MissingModule name="大六壬" />;
  const { facts } = result;
  const transmission = facts.three_transmissions;
  const [hoverBranch, setHoverBranch] = useState(null);

  return (
    <div className="view-stack">
      <section className="view-heading">
        <div>
          <span className="section-kicker">DA LIU REN</span>
          <h2>大六壬盘</h2>
          <p>月将、占时、天地盘、四课、三传、天将乘神与时空交互网络。</p>
        </div>
        <span className="version-badge">{result.rule_version}</span>
      </section>

      <section className="liuren-facts-band">
        <DataState label="占日" value={facts.day_pillar} />
        <DataState label="占时" value={facts.occupation_time.branch} />
        <DataState label="月将" value={`${facts.month_general.name} · ${facts.month_general.branch}`} />
        <DataState label="旬空" value={facts.xun.empty_branches.join("、")} />
      </section>

      <CastingIdentity facts={facts} />

      <section className="data-band">
        <div className="band-heading">
          <div>
            <span className="band-icon"><Workflow size={16} /></span>
            <div>
              <h3>天地盘与十二天将乘神</h3>
              <p>{facts.month_general.boundary_term}后月将 · {facts.heavenly_generals.distribution_direction}</p>
            </div>
          </div>
        </div>
        <div className="liuren-plate-wrap">
          <div className="liuren-plate-row row-label">
            <b>地盘</b>
            {facts.earth_plate.map((branch) => (
              <span
                key={branch}
                className={hoverBranch === branch ? "branch-active" : ""}
                onMouseEnter={() => setHoverBranch(branch)}
                onMouseLeave={() => setHoverBranch(null)}
              >
                {branch}
              </span>
            ))}
          </div>
          <div className="liuren-plate-row">
            <b>天盘</b>
            {facts.earth_plate.map((branch) => (
              <strong
                key={branch}
                className={hoverBranch === branch ? "branch-active" : ""}
                onMouseEnter={() => setHoverBranch(branch)}
                onMouseLeave={() => setHoverBranch(null)}
              >
                {facts.heaven_plate[branch]}
              </strong>
            ))}
          </div>
          <div className="liuren-plate-row generals">
            <b>天将</b>
            {facts.earth_plate.map((branch) => (
              <span
                key={branch}
                className={hoverBranch === branch ? "branch-active" : ""}
                onMouseEnter={() => setHoverBranch(branch)}
                onMouseLeave={() => setHoverBranch(null)}
              >
                {facts.heavenly_generals.by_ground[branch]}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="liuren-detail-grid">
        <div className="data-band">
          <div className="band-heading">
            <div><span className="band-icon"><Grid3X3 size={16} /></span><div><h3>四课</h3><p>下神 → 上神</p></div></div>
          </div>
          <div className="four-lessons">
            {facts.four_lessons.map((lesson) => (
              <div key={lesson.sequence}>
                <span>第{lesson.sequence}课</span>
                <strong>{lesson.lower} → {lesson.upper}</strong>
                <small>{LESSON_RELATION_LABELS[lesson.relation] || lesson.relation || "—"}</small>
              </div>
            ))}
          </div>
        </div>
        <div className="data-band">
          <div className="band-heading">
            <div><span className="band-icon"><Workflow size={16} /></span><div><h3>三传</h3><p>{transmission.status === "completed" ? `${transmission.lesson_type}路径` : "规则路径未覆盖"}</p></div></div>
          </div>
          {transmission.status === "completed" ? (
            <div className="transmission-row">
              {["初传", "中传", "末传"].map((label, index) => (
                <div key={label}>
                  <span>{label}</span>
                  <strong>{transmission.transmissions[index]}</strong>
                </div>
              ))}
            </div>
          ) : (
            <Notice tone="warning" icon={CircleAlert}>待实现课体：{transmission.pending_path}。系统未生成猜测值。</Notice>
          )}
        </div>
      </section>

      <section className="data-band">
        <div className="band-heading">
          <div><span className="band-icon"><ListTree size={16} /></span><div><h3>推演步骤</h3><p>{result.engine_version}</p></div></div>
        </div>
        <Steps steps={result.steps} />
      </section>
    </div>
  );
}

export { LiurenView };
