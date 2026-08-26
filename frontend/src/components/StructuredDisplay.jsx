import HexagramView from "./HexagramView";

/**
 * 7步工作流结构化数据展示组件。
 * 对每一步的数据做友好展示，而非纯 JSON dump。
 */
export default function StructuredDisplay({ workflow }) {
  const steps = [
    { key: "step1", label: "信息校验", icon: "📋" },
    { key: "step2", label: "完整排盘", icon: "☯️" },
    { key: "step3", label: "用神定位", icon: "🎯" },
    { key: "step4", label: "旺衰分析", icon: "⚖️" },
    { key: "step5", label: "象义解读", icon: "🔮" },
    { key: "step6", label: "综合推演", icon: "📊" },
    { key: "step7", label: "趋吉避凶", icon: "🧭" },
  ];

  return (
    <div className="structured-display">
      {steps.map((s) => {
        const data = workflow[s.key];
        if (!data) return null;
        return (
          <div key={s.key} className="structured-step">
            <h4>{s.icon} 步骤{s.key.slice(-1)}：{s.label}</h4>
            <StructuredStepContent stepKey={s.key} data={data} />
          </div>
        );
      })}
      {workflow.reference_library && (
        <div className="structured-step">
          <h4>📚 拓展参考资料库</h4>
          <pre>{JSON.stringify(workflow.reference_library, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

function StructuredStepContent({ stepKey, data }) {
  if (stepKey === "step1") {
    return (
      <div className="structured-friendly">
        {data.question && <div className="friendly-row"><span className="friendly-label">求测事由：</span><span>{data.question}</span></div>}
        {data.category_label && <div className="friendly-row"><span className="friendly-label">事项类别：</span><span>{data.category_label}</span></div>}
        {data.casting_method && <div className="friendly-row"><span className="friendly-label">起盘方式：</span><span>{data.casting_method}</span></div>}
        {data.system && <div className="friendly-row"><span className="friendly-label">术数门类：</span><span>{data.system}</span></div>}
        {data.user_profile && Object.keys(data.user_profile).length > 0 && (
          <div className="friendly-row"><span className="friendly-label">用户画像：</span><span>{Object.entries(data.user_profile).map(([k,v]) => `${k}:${v}`).join("，")}</span></div>
        )}
        <div className="friendly-row">
          <span className="friendly-label">信息状态：</span>
          <span style={{ color: data.ready ? "var(--jade)" : "var(--vermilion)", fontWeight: 600 }}>
            {data.ready ? "✓ 信息充足，可排盘" : `✗ 缺失：${(data.missing_fields || []).join("、")}`}
          </span>
        </div>
      </div>
    );
  }
  if (stepKey === "step2") {
    return (
      <div className="structured-friendly">
        {data.systems && <div className="friendly-row"><span className="friendly-label">使用体系：</span><span>{(data.systems || []).join("、")}</span></div>}
        <HexagramView plateData={data} />
        {data.calendar && (
          <div className="friendly-row">
            <span className="friendly-label">历法基线：</span>
            <span>
              {data.calendar.ganzhi && `${data.calendar.ganzhi.year}年 ${data.calendar.ganzhi.month}月 ${data.calendar.ganzhi.day}日`}
              {data.calendar.solar_term && ` · ${data.calendar.solar_term}`}
            </span>
          </div>
        )}
      </div>
    );
  }
  if (stepKey === "step3") {
    return (
      <div className="structured-friendly">
        {data.primary_yongshen && <div className="friendly-row"><span className="friendly-label">主用神：</span><span>{data.primary_yongshen}</span></div>}
        {data.secondary_yongshen && <div className="friendly-row"><span className="friendly-label">辅助用神：</span><span>{data.secondary_yongshen}</span></div>}
        {data.logic && <div className="friendly-row"><span className="friendly-label">取用逻辑：</span><span>{data.logic}</span></div>}
        {data.party_yongshen && data.party_yongshen.length > 0 && (
          <div className="friendly-row">
            <span className="friendly-label">多方用神：</span>
            <ul>{data.party_yongshen.map((p, i) => <li key={i}>{p.party}：{p.yongshen}（{p.role}）</li>)}</ul>
          </div>
        )}
      </div>
    );
  }
  if (stepKey === "step4") {
    return (
      <div className="structured-friendly">
        {data.yongshen_wangshuai && (
          <div className="friendly-row">
            <span className="friendly-label">用神旺衰：</span>
            <span>{data.yongshen_wangshuai.level || "未知"}</span>
            {data.yongshen_wangshuai.reason && <span className="friendly-sub">（{data.yongshen_wangshuai.reason}）</span>}
          </div>
        )}
        {data.tiyong_relation && <div className="friendly-row"><span className="friendly-label">体用关系：</span><span>{data.tiyong_relation.type} — {data.tiyong_relation.meaning}</span></div>}
        {data.analysis_chain && Array.isArray(data.analysis_chain) && (
          <div className="friendly-row">
            <span className="friendly-label">生克链条：</span>
            <ul>{data.analysis_chain.map((c, i) => <li key={i}>{c}</li>)}</ul>
          </div>
        )}
      </div>
    );
  }
  if (stepKey === "step5") {
    return (
      <div className="structured-friendly">
        {data.hexagram_name && <div className="friendly-row"><span className="friendly-label">主卦：</span><span>{data.hexagram_name}</span></div>}
        {data.symbol_mappings && data.symbol_mappings.length > 0 && (
          <div className="friendly-row">
            <span className="friendly-label">符号映射：</span>
            <ul>
              {data.symbol_mappings.map((m, i) => (
                <li key={i}>
                  <strong>{m.symbol}</strong>：{m.event_mapping}
                  {m.original_meaning && <span className="friendly-sub">（原义：{m.original_meaning}）</span>}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }
  if (stepKey === "step6") {
    return (
      <div className="structured-friendly">
        {data.fortune_level && <div className="friendly-row"><span className="friendly-label">吉凶等级：</span><span className="fortune-inline">{data.fortune_level}</span></div>}
        {data.current_status && <div className="friendly-row"><span className="friendly-label">当前现状：</span><span>{data.current_status}</span></div>}
        {data.trend && <div className="friendly-row"><span className="friendly-label">发展趋势：</span><span>{data.trend}</span></div>}
        {data.timing && <div className="friendly-row"><span className="friendly-label">参考应期：</span><span>{data.timing}</span></div>}
        {data.favorable && Array.isArray(data.favorable) && data.favorable.length > 0 && (
          <div className="friendly-row"><span className="friendly-label">有利因素：</span><ul>{data.favorable.map((f, i) => <li key={i}>{f}</li>)}</ul></div>
        )}
        {data.obstacles && Array.isArray(data.obstacles) && data.obstacles.length > 0 && (
          <div className="friendly-row"><span className="friendly-label">阻碍因素：</span><ul>{data.obstacles.map((o, i) => <li key={i}>{o}</li>)}</ul></div>
        )}
        {data.fortune_basis && Array.isArray(data.fortune_basis) && (
          <div className="friendly-row"><span className="friendly-label">判定依据：</span><span>{data.fortune_basis.join("；")}</span></div>
        )}
      </div>
    );
  }
  if (stepKey === "step7") {
    return (
      <div className="structured-friendly">
        {data.advice && data.advice.length > 0 && (
          <div className="friendly-row">
            <span className="friendly-label">趋吉避凶建议：</span>
            <ol style={{ margin: 0, paddingLeft: "20px" }}>
              {data.advice.map((a, i) => <li key={i} style={{ marginBottom: 4 }}>{a}</li>)}
            </ol>
          </div>
        )}
        {data.disclaimer && (
          <div className="friendly-row" style={{ marginTop: 8, paddingTop: 8, borderTop: "1px solid var(--line)" }}>
            <span className="friendly-label">文化提示：</span>
            <span style={{ fontSize: 12, color: "var(--muted)" }}>{data.disclaimer}</span>
          </div>
        )}
      </div>
    );
  }
  return <pre>{JSON.stringify(data, null, 2)}</pre>;
}
