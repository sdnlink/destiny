import { Copy } from "lucide-react";

/**
 * 交互结果展示组件。
 * 根据交互类型渲染不同的结果格式。
 */
export default function InteractionResultDisplay({ data, showCopy = false }) {
  if (!data) return null;

  const copyBtn = showCopy && (
    <button
      className="copy-interaction-btn"
      onClick={() => {
        const text = typeof data === "string" ? data : JSON.stringify(data, null, 2);
        navigator.clipboard.writeText(text).catch(() => {});
      }}
      title="复制此条交互结果"
    >
      <Copy size={12} />复制
    </button>
  );

  // 深度追问结果
  if (data.type === "deep_question" && data.analysis) {
    return (
      <div className="interaction-result deep-question-result">
        <div className="interaction-item-header">
          <p><strong>追问：</strong>{data.question}</p>
          {copyBtn}
        </div>
        {data.detected_symbols && data.detected_symbols.length > 0 && (
          <p className="result-meta-line">检测到符号类型：{data.detected_symbols.join("、")}</p>
        )}
        <pre className="deep-analysis">{data.analysis}</pre>
      </div>
    );
  }

  // 换角度结果
  if (data.type === "angle_shift" && data.reinterpretation) {
    return (
      <div className="interaction-result angle-shift-result">
        <div className="interaction-item-header">
          <p><strong>新角度：</strong>{data.new_angle}</p>
          {copyBtn}
        </div>
        {data.matched_preset && <p className="result-meta-line">匹配预设：{data.matched_preset}</p>}
        {data.shift_focus && <p className="result-meta-line"><em>{data.shift_focus}</em></p>}
        <pre className="deep-analysis">{data.reinterpretation}</pre>
        {data.suggested_angles && data.suggested_angles.length > 0 && (
          <div className="suggested-angles">
            <strong>其他建议角度：</strong>
            {data.suggested_angles.map((a, i) => <span key={i} className="angle-tag">{a}</span>)}
          </div>
        )}
      </div>
    );
  }

  if (data.description) {
    return (
      <div className="interaction-result">
        <div className="interaction-item-header">
          <span></span>
          {copyBtn}
        </div>
        <p>{data.description}</p>
        {data.options && (
          <ul>{data.options.map((o, i) => <li key={i}>{o}</li>)}</ul>
        )}
        {data.interpretation_shift && (
          <div className="interpretation-shift">
            <strong>解读视角调整：</strong>
            <p>{data.interpretation_shift.note}</p>
            {data.interpretation_shift.suggested_angles && (
              <ul>{data.interpretation_shift.suggested_angles.map((a, i) => <li key={i}>{a}</li>)}</ul>
            )}
          </div>
        )}
      </div>
    );
  }
  if (data.parties) {
    return (
      <div className="interaction-result">
        <div className="interaction-item-header"><span></span>{copyBtn}</div>
        {data.parties.map((p, i) => (
          <div key={i} className="party-card">
            <strong>{p.party}</strong>
            <p>用神：{p.yongshen}</p>
            <p>立场：{p.position}</p>
            <p>心态：{p.mindset}</p>
            <p>诉求：{p.demands}</p>
            {p.deep_analysis && <pre className="deep-analysis">{p.deep_analysis}</pre>}
          </div>
        ))}
        {data.focus_party && (
          <div className="focus-party">
            <h5>聚焦人物深化</h5>
            <pre>{JSON.stringify(data.focus_party, null, 2)}</pre>
          </div>
        )}
      </div>
    );
  }
  if (data.choices) {
    return (
      <div className="interaction-result">
        <div className="interaction-item-header"><span></span>{copyBtn}</div>
        {data.choices.map((c, i) => (
          <div key={i} className="choice-card">
            <strong>{c.choice}</strong>
            <p>分析角度：{c.analysis_angle}</p>
            <p>风险等级：{c.risk_level}</p>
            <p>趋势：{c.trend}</p>
            <p>利：{c.pros.join("；")}</p>
            <p>弊：{c.cons.join("；")}</p>
          </div>
        ))}
        {data.recommendation && <p className="recommendation"><strong>综合建议：</strong>{data.recommendation}</p>}
      </div>
    );
  }
  if (data.verified !== undefined) {
    return (
      <div className="interaction-result review-result">
        <div className="interaction-item-header"><span></span>{copyBtn}</div>
        <p><strong>现实结果：</strong>{data.actual_outcome}</p>
        <p><strong>应验象：</strong></p>
        <ul>{data.verified.map((v, i) => <li key={i}>{v}</li>)}</ul>
        <p><strong>未应验象：</strong></p>
        <ul>{data.unverified.map((v, i) => <li key={i}>{v}</li>)}</ul>
        <p><strong>多角度分析：</strong></p>
        {Object.entries(data.analysis || {}).map(([k, v]) => (
          <p key={k}><em>{k}：</em>{v}</p>
        ))}
        <p><strong>经验教训：</strong></p>
        <ul>{data.lessons.map((l, i) => <li key={i}>{l}</li>)}</ul>
      </div>
    );
  }
  return (
    <div className="interaction-result">
      <div className="interaction-item-header"><span></span>{copyBtn}</div>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
