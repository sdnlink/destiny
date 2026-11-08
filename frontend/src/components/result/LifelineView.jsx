import { useState } from "react";
import { CalendarRange, CircleAlert, Loader2 } from "lucide-react";
import { analyzeLifeline } from "../../lib/api";
import { Notice } from "./shared";

const FLAG_LABELS = {
  true_taisui: "真太岁",
  suiyun_binglin: "岁运并临",
  day_year_parallel: "日年相并",
  zheng_taisui: "征太岁",
};

function summarizeSuiyun(suiyun) {
  if (!suiyun) return "—";
  const flags = Object.entries(FLAG_LABELS)
    .filter(([key]) => suiyun[key])
    .map(([, label]) => label);
  const relations = [];
  const withLuck = suiyun.relations?.with_luck_pillar;
  if (withLuck?.branch_relations?.length) {
    relations.push(`大运${withLuck.branch_relations.join("、")}`);
  }
  return [...flags, ...relations].join(" · ") || "无显著冲合";
}

function withoutTimezoneOffset(value) {
  if (typeof value !== "string") return "";
  // 后端 CalendarEngine 只接受 naive local_datetime；旧结果没有 input 时，
  // 至少把 solar_datetime 末尾的 Z/+08:00 剥掉，避免直接触发 422。
  return value.replace(/(?:Z|[+-]\d{2}:?\d{2})$/, "");
}

function parseRecordedEvents(text) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const match = line.match(/^(\d{4})\s+([^ ].*)$/);
      if (!match) {
        throw new Error("事件格式应为「年份 描述」，例如：2030 迁居");
      }
      const year = Number(match[1]);
      if (year < 1900 || year > 2100) {
        throw new Error("事件年份需在 1900-2100 之间");
      }
      return { year, label: match[2].trim() };
    });
}

/** 个人生平时间轴：按需向 /v1/bazi/lifeline 请求，只展示确定事实。 */
export function LifelineView({ result }) {
  const [state, setState] = useState({ status: "idle", data: null, error: null });
  const [eventsText, setEventsText] = useState("");
  const natalInput = result?.input || {};
  const hasSourceInput = Boolean(natalInput.local_datetime);
  const localDatetime = withoutTimezoneOffset(natalInput.local_datetime || result?.solar_datetime);
  const timezone = natalInput.timezone || "Asia/Shanghai";
  const gender = natalInput.gender || result?.gender || "男";
  const longitude = natalInput.longitude ?? null;
  const useTrueSolarTime = Boolean(natalInput.use_true_solar_time);

  async function load() {
    if (!localDatetime) return;
    let events;
    try {
      events = parseRecordedEvents(eventsText);
    } catch (error) {
      setState({ status: "error", data: null, error: error.message });
      return;
    }
    setState({ status: "loading", data: null, error: null });
    try {
      const data = await analyzeLifeline({
        local_datetime: localDatetime,
        timezone,
        gender,
        longitude,
        use_true_solar_time: useTrueSolarTime,
        count: 12,
        events,
      });
      setState({ status: "ready", data, error: null });
    } catch (error) {
      setState({ status: "error", data: null, error: error.message || "生平时间轴加载失败" });
    }
  }

  const ziping = state.data?.ziping;
  const timeline = state.data?.timeline || [];

  return (
    <section className="data-band">
      <div className="band-heading">
        <div>
          <span className="band-icon"><CalendarRange size={16} /></span>
          <div>
            <h3>个人生平时间轴（子平 · 岁运 · 皇极经世）</h3>
            <p>月令取格候选、大运流年组合事实与宏观周期背景对齐；不含吉凶断语</p>
          </div>
        </div>
        <button type="button" className="ghost-action" onClick={load} disabled={state.status === "loading"}>
          {state.status === "loading" ? <Loader2 size={14} className="spin" /> : null}
          {state.status === "ready" ? "重新计算" : "生成时间轴"}
        </button>
      </div>

      {state.status === "idle" && (
        <p className="muted-copy">按需生成起运后 12 年的逐年事实序列（含立春交接时刻与皇极经世背景）。</p>
      )}
      {!hasSourceInput && (
        <Notice tone="warning" icon={CircleAlert}>
          该结果来自旧版本，缺少原始时区与真太阳时入参；时间轴将按东八区重建，可能与原盘不一致。
        </Notice>
      )}
      <div className="lifeline-events">
        <label htmlFor="lifeline-events">已发生事件（可选，每行：年份 描述）</label>
        <textarea
          id="lifeline-events"
          value={eventsText}
          onChange={(event) => setEventsText(event.target.value)}
          rows={2}
          placeholder={"2030 迁居\n2031 入职"}
        />
        <small>只做时间对齐展示，不参与计算、不预测未来、不用于反推生辰。</small>
      </div>
      {state.status === "error" && <Notice tone="warning" icon={CircleAlert}>{state.error}</Notice>}
      {state.status === "ready" && (
        <>
          <div className="lifeline-ziping">
            <strong>月令提纲：{ziping?.month_branch}（{ziping?.month_element}）</strong>
            <p>{ziping?.rule}</p>
            <p>
              藏干：{ziping?.hidden_stems?.map((row) => `${row.stem}·${row.ten_god}·${row.qi}${row.exposed ? "（透）" : ""}`).join("；")}
            </p>
            {ziping?.pattern_candidates?.length > 0 ? (
              <p>格局候选：{ziping.pattern_candidates.map((c) => c.pattern_candidate).join("、")}</p>
            ) : (
              <p>月令藏干未透出天干，不列格局候选。</p>
            )}
          </div>

          <div className="lifeline-table-wrap">
            <table className="lifeline-table">
              <thead>
                <tr>
                  <th>年份 / 干支</th>
                  <th>大运 / 年龄</th>
                  <th>立春交接</th>
                  <th>岁运组合事实</th>
                  <th>皇极经世背景</th>
                  <th>已录事件</th>
                </tr>
              </thead>
              <tbody>
                {timeline.map((row) => (
                  <tr key={row.year}>
                    <td><b>{row.year}</b> {row.ganzhi}<small>{row.stem_ten_god} · {row.nayin}</small></td>
                    <td>
                      {row.luck_pillar ? `${row.luck_pillar.ganzhi}（第${row.luck_pillar.index}步）` : "未入大运"}
                      <small>{row.age} 岁 / 虚岁 {row.virtual_age}</small>
                    </td>
                    <td><small>{row.lichun_datetime}</small></td>
                    <td>{summarizeSuiyun(row.suiyun)}<small>太岁 {row.taisui_branch} · 岁破 {row.suipo_branch}</small></td>
                    <td>
                      {row.yuan_hui_yun_shi.yuan} / {row.yuan_hui_yun_shi.hui}
                      <small>{row.yuan_hui_yun_shi.yun} · {row.yuan_hui_yun_shi.shi}（世内 {row.yuan_hui_yun_shi.year_in_shi} 年）</small>
                    </td>
                    <td>{row.recorded_events?.length ? row.recorded_events.map((e) => e.label || "已录事件").join("、") : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {(state.data?.warnings || []).map((warning, index) => (
            <Notice key={index} tone="warning" icon={CircleAlert}>{warning}</Notice>
          ))}
          <p className="muted-copy">{state.data?.school} · {state.data?.status} · {state.data?.rule_id}</p>
        </>
      )}
    </section>
  );
}
