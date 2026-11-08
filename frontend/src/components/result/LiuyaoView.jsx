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

const NAJIA_TABLE = {
  乾: { lower: ["甲子", "甲寅", "甲辰"], upper: ["壬午", "壬申", "壬戌"] },
  坤: { lower: ["乙未", "乙巳", "乙卯"], upper: ["癸丑", "癸亥", "癸酉"] },
  震: { lower: ["庚子", "庚寅", "庚辰"], upper: ["庚午", "庚申", "庚戌"] },
  巽: { lower: ["辛丑", "辛亥", "辛酉"], upper: ["辛未", "辛巳", "辛卯"] },
  坎: { lower: ["戊寅", "戊辰", "戊午"], upper: ["戊申", "戊戌", "戊子"] },
  离: { lower: ["己卯", "己丑", "己亥"], upper: ["己酉", "己未", "己巳"] },
  艮: { lower: ["丙辰", "丙午", "丙申"], upper: ["丙戌", "丙子", "丙寅"] },
  兑: { lower: ["丁巳", "丁卯", "丁丑"], upper: ["丁亥", "丁酉", "丁未"] },
};

const BRANCH_ELEMENTS_MAP = {
  子: "水", 丑: "土", 寅: "木", 卯: "木", 辰: "土", 巳: "火",
  午: "火", 未: "土", 申: "金", 酉: "金", 戌: "土", 亥: "水",
};

const FIVE_ELEMENTS_GENERATES = { 木: "火", 火: "土", 土: "金", 金: "水", 水: "木" };

const FIVE_ELEMENTS_CONTROLS = { 木: "土", 土: "水", 水: "火", 火: "金", 金: "木" };

function getLiuyaoRelative(palaceElement, lineElement) {
  if (palaceElement === lineElement) return "兄弟";
  if (FIVE_ELEMENTS_GENERATES[lineElement] === palaceElement) return "父母";
  if (FIVE_ELEMENTS_GENERATES[palaceElement] === lineElement) return "子孙";
  if (FIVE_ELEMENTS_CONTROLS[lineElement] === palaceElement) return "官鬼";
  if (FIVE_ELEMENTS_CONTROLS[palaceElement] === lineElement) return "妻财";
  return "比和";
}

function buildHiddenSpirits(facts) {
  const backend = facts.hidden_flying_spirits;
  if (backend && backend.status === "completed" && Array.isArray(backend.hidden_spirits)) {
    return backend.hidden_spirits.map((item) => ({
      position: item.position,
      ganzhi: `${item.najia_stem}${item.najia_branch}`,
      element: item.element,
      relative: item.six_relative,
      relation: item.relation,
      flying: item.flying_spirit,
    }));
  }
  // 兼容旧会话：本宫首卦纳甲 → 缺失六亲逐位补出
  const pureConfig = NAJIA_TABLE[facts.palace.name];
  const pureGanzhi = pureConfig ? [...pureConfig.lower, ...pureConfig.upper] : [];
  const currentRelatives = new Set(facts.line_chart.map((line) => line.six_relative));
  const missingRelatives = ["父母", "兄弟", "子孙", "妻财", "官鬼"].filter(
    (relative) => !currentRelatives.has(relative)
  );
  return pureGanzhi
    .map((ganzhi, index) => {
      const element = BRANCH_ELEMENTS_MAP[ganzhi[1]] || "土";
      return {
        position: index + 1,
        ganzhi,
        element,
        relative: getLiuyaoRelative(facts.palace.element, element),
      };
    })
    .filter((item) => missingRelatives.includes(item.relative));
}

// 元神/忌神/仇神爻位：本卦仅列数字，伏神/变爻以「伏N/变N」标注来源，转为可读文本。
function renderRelPositions(positions) {
  if (!positions || positions.length === 0) return "本卦不现";
  const map = (p) => {
    if (p.startsWith("伏")) return `伏神第${p.slice(1)}爻`;
    if (p.startsWith("变")) return `变爻第${p.slice(1)}爻`;
    return `本卦第${p}爻`;
  };
  return positions.map(map).join("、");
}

// 伏神出伏状态（《卜筮正宗·伏神正传》空破/日月克伤/飞伏生克口径），返回可读文本或 null。
function renderEmerge(emerge) {
  if (!emerge || emerge.length === 0) return null;
  return emerge
    .map((e) => {
      const status = e.can_emerge ? "可出伏" : "暂不可出伏";
      const reasons = (e.reasons || []).join("；");
      return `伏神第${e.position}爻：${status}${reasons ? `（${reasons}）` : ""}`;
    })
    .join("；");
}

function LiuyaoView({ result }) {
  if (!result) return <MissingModule name="六爻" />;
  const { facts } = result;
  const [selectedPos, setSelectedPos] = useState(facts.palace.host_line || 1);

  // 伏神优先采用后端推导（本宫首卦同位补缺），旧会话缺该字段时回退本地计算
  const hiddenSpirits = buildHiddenSpirits(facts);
  const palaceName = facts.palace.name;
  const missingRelatives = hiddenSpirits.map((h) => h.relative);

  const activeLine = facts.line_chart.find((l) => l.position === selectedPos) || facts.line_chart[0];
  const activeHidden = hiddenSpirits.find((h) => h.position === selectedPos);

  return (
    <div className="view-stack">
      <section className="view-heading">
        <div>
          <span className="section-kicker">LIU YAO NA JIA</span>
          <h2>六爻纳甲盘与伏神飞神</h2>
          <p>八宫世应、纳甲六亲、六神与动变爻位立体交互排盘。</p>
        </div>
        <span className="version-badge">{result.rule_version}</span>
      </section>

      <section className="hexagram-primary-grid">
        <HexagramTile title="本卦" hexagram={facts.original} moving={facts.moving_lines} featured />
        <div className="change-arrow"><ArrowRight size={22} /><span>{facts.moving_lines.length ? `第 ${facts.moving_lines.join("、")} 爻动` : "静卦无动爻"}</span></div>
        <HexagramTile title="变卦" hexagram={facts.changed} featured />
      </section>

      <CastingIdentity facts={facts} />

      {facts.yongshen && (
        <section className="data-band yongshen-band">
          <div className="band-heading">
            <div>
              <span className="band-icon"><Info size={16} /></span>
              <div>
                <h3>用神焦点 · {facts.yongshen.focus}</h3>
                <p>{facts.yongshen.note || "按所问事项列出用神候选，不直接断吉凶。"}</p>
              </div>
            </div>
          </div>
          <div className="yongshen-grid">
            <div>
              <span>用神</span>
              <strong>{(facts.yongshen.targets || []).join("、") || "—"}</strong>
              <small>{facts.yongshen.support ? `原神 ${facts.yongshen.support}` : "无指定原神"}</small>
            </div>
            <div>
              <span>原神</span>
              <strong>{facts.yongshen.yuan_shen?.relative || "—"}</strong>
              <small>{facts.yongshen.yuan_shen?.element || ""} {renderRelPositions(facts.yongshen.yuan_shen?.positions)}</small>
              {renderEmerge(facts.yongshen.yuan_shen?.emerge) && (
                <small className="emerge-note">{renderEmerge(facts.yongshen.yuan_shen?.emerge)}</small>
              )}
            </div>
            <div>
              <span>忌神</span>
              <strong>{facts.yongshen.ji_shen?.relative || "—"}</strong>
              <small>{facts.yongshen.ji_shen?.element || ""} {renderRelPositions(facts.yongshen.ji_shen?.positions)}</small>
              {renderEmerge(facts.yongshen.ji_shen?.emerge) && (
                <small className="emerge-note">{renderEmerge(facts.yongshen.ji_shen?.emerge)}</small>
              )}
            </div>
            <div>
              <span>仇神</span>
              <strong>{facts.yongshen.chou_shen?.relative || "—"}</strong>
              <small>{facts.yongshen.chou_shen?.element || ""} {renderRelPositions(facts.yongshen.chou_shen?.positions)}</small>
              {renderEmerge(facts.yongshen.chou_shen?.emerge) && (
                <small className="emerge-note">{renderEmerge(facts.yongshen.chou_shen?.emerge)}</small>
              )}
            </div>
          </div>
          <div className="yongshen-candidates">
            {(facts.yongshen.candidates || []).length > 0 ? facts.yongshen.candidates.map((candidate, index) => (
              <div className="yongshen-candidate" key={`${candidate.source}-${candidate.position}-${candidate.branch}`}>
                <span>候选 {index + 1}</span>
                <strong>{candidate.source}第 {candidate.position} 爻 · {candidate.branch}（{candidate.element}）</strong>
                <small>
                  {candidate.moving ? "动爻" : "静爻"} · {candidate.month_strength || "—"}
                  {candidate.void_state ? ` · ${candidate.void_state}` : " · 不空"}
                  {candidate.is_month_break ? " · 月破" : ""}
                  {candidate.is_day_break ? " · 日破" : ""}
                  {candidate.rank_score !== undefined ? ` · 排序 ${candidate.rank_score}` : ""}
                  {candidate.source === "伏神" && candidate.can_emerge !== undefined ? (
                    <>
                      {" · "}
                      {candidate.can_emerge ? "可出伏" : "暂不可出伏"}
                      {candidate.emerge_reasons?.length ? `（${candidate.emerge_reasons.join("；")}）` : ""}
                    </>
                  ) : null}
                </small>
              </div>
            )) : <p className="standalone-form-hint">本卦未见对应六亲，暂无用神候选。</p>}
          </div>
          <p className="standalone-form-hint">{facts.yongshen.selection_note}</p>
        </section>
      )}

      <section className="data-band">
        <div className="band-heading">
          <div>
            <span className="band-icon"><Grid3X3 size={16} /></span>
            <div>
              <h3>{facts.palace.name}宫 · {facts.palace.stage}</h3>
              <p>世爻 {facts.palace.host_line} · 应爻 {facts.palace.response_line} · {facts.xun.name}空 {facts.xun.empty_branches.join("、")}</p>
            </div>
          </div>
        </div>
        <div className="liuyao-table-wrap">
          <table className="liuyao-table">
            <thead>
              <tr>
                <th>爻位</th>
                <th>六神</th>
                <th>六亲</th>
                <th>纳甲</th>
                <th>五行</th>
                <th>世应</th>
                <th>状态</th>
                <th>本宫伏神</th>
              </tr>
            </thead>
            <tbody>
              {[...facts.line_chart].reverse().map((line) => {
                const hidden = hiddenSpirits.find((h) => h.position === line.position);
                return (
                  <tr
                    key={line.position}
                    className={`${line.is_moving ? "moving-line" : ""} ${selectedPos === line.position ? "selected-line" : ""}`}
                    onClick={() => setSelectedPos(line.position)}
                    style={{ cursor: "pointer" }}
                  >
                    <td><strong>{line.position === 6 ? "上爻" : line.position === 1 ? "初爻" : `${line.position}爻`}</strong></td>
                    <td><span className="spirit-badge">{line.six_spirit}</span></td>
                    <td><strong>{line.six_relative}</strong></td>
                    <td>{line.najia_stem}{line.najia_branch}</td>
                    <td><span style={{ color: ELEMENT_COLORS[line.element] || "inherit" }}>{line.element}</span></td>
                    <td>{(line.roles || []).some((role) => role === "世" || role === "世爻") ? <span className="shi-badge">世</span> : (line.roles || []).some((role) => role === "应" || role === "应爻") ? <span className="ying-badge">应</span> : "—"}</td>
                    <td>
                      {line.is_moving ? <span className="moving-badge">发动 ○</span> : "静爻"}
                      {line.void_state ? ` · ${line.void_state}` : line.is_void ? " · 旬空" : ""}
                      {line.is_month_break ? " · 月破" : ""}
                      {line.is_day_break ? " · 日破" : ""}
                      {line.is_dark_move ? " · 暗动" : ""}
                      {line.advance_retreat ? ` · ${line.advance_retreat}` : ""}
                    </td>
                    <td>
                      {hidden ? (
                        <span className="hidden-pill-tag" title={`伏于${line.najia_branch}下`}>
                          伏 {hidden.relative} {hidden.ganzhi}
                        </span>
                      ) : (
                        <small className="inspect-link">查看详情</small>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* 伏神飞神聚焦研判卡片 */}
      {hiddenSpirits.length > 0 && (
        <section className="data-band hidden-spirits-band">
          <div className="band-heading">
            <div>
              <span className="band-icon"><Sparkles size={16} /></span>
              <div>
                <h3>本宫八纯伏神对照（{palaceName}为{palaceName}）</h3>
                <p>本卦缺【{missingRelatives.join("、")}】，从本宫纯卦提取伏神以明隐微之事</p>
              </div>
            </div>
          </div>
          <div className="hidden-spirits-grid">
            {hiddenSpirits.map((h) => {
              const flyLine = facts.line_chart[h.position - 1];
              let relType = "同气比和";
              let relDesc = "比和得气，同气相求。";
              if (FIVE_ELEMENTS_GENERATES[flyLine.element] === h.element) {
                relType = "飞生伏";
                relDesc = "飞来生伏得长生，虽伏易出，吉象。";
              } else if (FIVE_ELEMENTS_GENERATES[h.element] === flyLine.element) {
                relType = "伏生飞";
                relDesc = "伏去生飞泄气，耗神泄力。";
              } else if (FIVE_ELEMENTS_CONTROLS[flyLine.element] === h.element) {
                relType = "飞克伏";
                relDesc = "飞来克伏受制，为害最深，难拔难出。";
              } else if (FIVE_ELEMENTS_CONTROLS[h.element] === flyLine.element) {
                relType = "伏克飞";
                relDesc = "伏去克飞为财，冲克飞神方能显现。";
              }

              return (
                <div key={h.position} className="hidden-spirit-card">
                  <div className="h-card-head">
                    <strong>伏神【{h.relative} {h.ganzhi}（{h.element}）】</strong>
                    <span className={`h-rel-badge rel-${relType}`}>{relType}</span>
                  </div>
                  <p className="h-card-detail">
                    伏于第 {h.position} 爻 <b>{flyLine.six_relative} {flyLine.najia_stem}{flyLine.najia_branch}（{flyLine.element}）</b> 飞神之下。
                  </p>
                  <small className="h-card-desc">{relDesc}</small>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {facts.branch_structures && (facts.branch_structures.sanhe.length > 0 || facts.branch_structures.liuhe.length > 0) && (
        <section className="data-band branch-structures-band">
          <div className="band-heading">
            <div>
              <span className="band-icon"><Sparkles size={16} /></span>
              <div>
                <h3>三合局与六合</h3>
                <p>动爻、月建、日辰爻支构成的齐备组合，来源逐支标注</p>
              </div>
            </div>
          </div>
          <div className="structure-list">
            {facts.branch_structures.sanhe.map((s) => (
              <p key={s.element + s.branches.join("")} className="structure-line">
                <b>{s.branches.join("")}{s.element}局</b>
                {" "}（{s.members.map((m) => `${m.branch}：${m.sources.join("、")}`).join("；")}）
              </p>
            ))}
            {facts.branch_structures.liuhe.map((p) => (
              <p key={p.branches.join("")} className="structure-line">
                <b>{p.branches.join("")}六合</b>
                {" "}（{p.members.map((m) => `${m.branch}：${m.sources.join("、")}`).join("；")}）
              </p>
            ))}
          </div>
        </section>
      )}

      <section className="data-band">
        <div className="band-heading">
          <div><span className="band-icon"><ListTree size={16} /></span><div><h3>计算依据</h3><p>{result.engine_version}</p></div></div>
        </div>
        <Steps steps={result.steps} />
      </section>

      {(result.evidence || []).length > 0 && (
        <section className="data-band classics-evidence-band">
          <div className="band-heading">
            <div>
              <span className="band-icon"><BookOpen size={16} /></span>
              <div>
                <h3>典籍依据</h3>
                <p>结论相关原文出自本地维基文库存档，点击链接可逐条校对</p>
              </div>
            </div>
          </div>
          <div className="evidence-list">
            {result.evidence.map((item) => (
              <div key={item.classic_id} className="evidence-item">
                <div className="evidence-meta">
                  <b>《{item.title}》</b>
                  <span>第 {item.chunk_index + 1} 段 · {item.license_name || "公开许可"}</span>
                  {item.source_url && (
                    <a href={item.source_url} target="_blank" rel="noreferrer">原文来源</a>
                  )}
                </div>
                <p className="evidence-text">{item.excerpt}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export { LiuyaoView };
