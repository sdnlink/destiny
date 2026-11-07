// 由 WorkflowPanel.jsx 拆分而来（审计 13：超大组件拆分），只搬 JSX 未改逻辑。
// 阶段组件本身不持有状态：所有 state 与请求函数仍由 WorkflowPanel 持有并透传。
import {
  Sparkles,
  Play,
  CheckCircle2,
  AlertCircle,
  Users,
  GitBranch,
  History,
  MessageSquare,
  RefreshCw,
  ChevronRight,
  ChevronDown,
  X,
  ShieldCheck,
  Copy,
  Check,
  RotateCcw,
  FolderOpen,
  Loader2,
  Download,
} from "lucide-react";
import { CATEGORIES, CASTING_METHODS, FORTUNE_COLORS, SYSTEMS, categoryLabel, formatDate, statusLabel } from "../../lib/labels";

export default function CompletionPhase({
  sessionId,
  completion,
  completionAnswers,
  setCompletionAnswers,
  error,
  isLoading,
  anyLoading,
  handleSkipCompletion,
  handleApplyCompletion,
}) {
    return (
      <div className="workflow-panel">
        <div className="workflow-header">
          <h2>起盘前信息补全</h2>
          <p className="workflow-subtitle">会话ID：{sessionId}</p>
        </div>
        {completion.ready ? (
          <div className="completion-ready">
            <CheckCircle2 size={32} />
            <p>信息已充足，可直接起盘。</p>
            <button className="btn-primary" onClick={handleSkipCompletion} disabled={anyLoading}>
              {isLoading("cast") ? <RefreshCw size={16} className="spin" /> : null}
              {isLoading("cast") ? "排盘中..." : "立即起盘"}
            </button>
          </div>
        ) : (
          <div className="completion-questions">
            {completion.questions.map((q, i) => (
              <div key={i} className="completion-item">
                <label>{q.question}</label>
                <input
                  type="text"
                  value={completionAnswers[q.field] || ""}
                  onChange={(e) => setCompletionAnswers({ ...completionAnswers, [q.field]: e.target.value })}
                  placeholder="请输入（可留空）"
                  onKeyDown={(e) => e.key === "Enter" && handleApplyCompletion()}
                />
              </div>
            ))}
            <div className="completion-actions">
              <button className="btn-primary" onClick={handleApplyCompletion} disabled={anyLoading}>
                {isLoading("cast") ? <RefreshCw size={16} className="spin" /> : null}
                {isLoading("cast") ? "排盘中..." : "提交并起盘"}
              </button>
              <button className="btn-secondary" onClick={handleSkipCompletion} disabled={anyLoading}>
                直接起盘，不用多问
              </button>
            </div>
            <p className="completion-hint">{completion.instruction}</p>
          </div>
        )}
        {error && <div className="error-message"><AlertCircle size={16} />{error}</div>}
      </div>
    );
  
}
