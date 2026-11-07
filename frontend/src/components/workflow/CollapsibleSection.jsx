// 由 WorkflowPanel.jsx 拆分而来（审计 13），只搬代码未改逻辑。
import { ChevronDown, ChevronRight } from "lucide-react";

export default function CollapsibleSection({ title, collapsed, onToggle, children, defaultOpen }) {
  const isOpen = collapsed === undefined ? defaultOpen : !collapsed;
  return (
    <div className={`collapsible-section ${isOpen ? "open" : "closed"}`}>
      <div className="collapsible-header" onClick={onToggle}>
        {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        <h4>{title}</h4>
      </div>
      {isOpen && <div className="collapsible-body">{children}</div>}
    </div>
  );
}
