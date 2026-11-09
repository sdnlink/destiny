import { useState } from "react";
import { Database, ShieldCheck, X } from "lucide-react";

const RULE_SYSTEM_FILTERS = [
  ["all", "全部"], ["calendar", "历法"], ["zhouyi", "周易"], ["meihua", "梅花"],
  ["liuyao", "六爻"], ["liuren", "六壬"], ["qimen", "奇门"], ["bazi", "八字"],
  ["ziwei", "紫微"], ["fengshui", "风水"],
];

export default function RulesDrawer({ open, onClose, rules, loading }) {
  const [system, setSystem] = useState("all");
  const filtered = (system === "all" ? rules : rules.filter((rule) => rule.system === system));
  if (!open) return null;
  return (
    <div className="drawer-layer" role="presentation" onMouseDown={onClose}>
      <aside className="rules-drawer" role="dialog" aria-modal="true" aria-label="规则目录" onMouseDown={(event) => event.stopPropagation()}>
        <header>
          <div><p className="section-kicker">RULE REGISTRY</p><h2>规则目录</h2></div>
          <button className="icon-button" onClick={onClose} aria-label="关闭规则目录"><X size={19} /></button>
        </header>
        <div className="drawer-notice"><ShieldCheck size={16} /><span>当前规则均为工程草稿，尚未经过专家签署。</span></div>
        <div className="segmented drawer-filter">
          {RULE_SYSTEM_FILTERS.map(([id, label]) => (
            <button key={id} className={system === id ? "active" : ""} onClick={() => setSystem(id)}>{label}</button>
          ))}
        </div>
        <div className="rules-table-wrap">
          {loading ? <div className="drawer-loading">读取规则目录...</div> : (
            <table className="rules-table">
              <thead><tr><th>规则编号</th><th>名称</th><th>版本</th><th>状态</th></tr></thead>
              <tbody>
                {filtered.map((rule) => (
                  <tr key={rule.rule_id}>
                    <td><code>{rule.rule_id}</code></td>
                    <td><strong>{rule.title}</strong><span>{rule.purpose}</span></td>
                    <td>{rule.version}</td>
                    <td><span className="draft-state">草稿</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <footer><Database size={15} /><span>{filtered.length} 条规则 · mvp-engineering-baseline</span></footer>
      </aside>
    </div>
  );
}
