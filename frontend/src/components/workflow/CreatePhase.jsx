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

export default function CreatePhase({
  form,
  setForm,
  error,
  recoverId,
  setRecoverId,
  showRecover,
  setShowRecover,
  sessionList,
  showHistory,
  setShowHistory,
  loadingHistory,
  historySearch,
  setHistorySearch,
  historyFilter,
  setHistoryFilter,
  isLoading,
  anyLoading,
  handleCreate,
  handleRecover,
  loadSessionList,
  handleRestoreFromList,
  handleDeleteSession,
  handleExportSessionsJSON,
  handleImportSessionsJSON,
}) {
    return (
      <div className="workflow-panel">
        <div className="workflow-header">
          <div className="workflow-title">
            <Sparkles size={22} />
            <h2>交互式推演工作台</h2>
          </div>
          <div className="header-actions">
            <button
              className="btn-secondary btn-small"
              onClick={() => {
                setShowHistory(!showHistory);
                if (!showHistory) loadSessionList();
              }}
            >
              <History size={14} />历史会话
            </button>
            <button className="btn-secondary btn-small" onClick={() => setShowRecover(!showRecover)}>
              <FolderOpen size={14} />恢复会话
            </button>
          </div>
        </div>
        <p className="workflow-subtitle">7步标准化排盘推理 · 盘面永久不可变 · 多轮交互深化解读</p>

        {showHistory && (
          <div className="session-history-panel">
            <div className="history-panel-header">
              <h4><History size={16} />最近推演会话</h4>
              <div style={{ display: "flex", gap: 6 }}>
                <button className="btn-small btn-secondary" onClick={handleExportSessionsJSON} title="导出全部会话为JSON">
                  <Download size={12} />导出
                </button>
                <button className="btn-small btn-secondary" onClick={() => document.getElementById("session-import-input")?.click()} title="从JSON导入会话">
                  <FolderOpen size={12} />导入
                </button>
                <input
                  id="session-import-input"
                  type="file"
                  accept=".json"
                  style={{ display: "none" }}
                  onChange={handleImportSessionsJSON}
                />
                <button className="btn-small btn-secondary" onClick={loadSessionList} disabled={loadingHistory}>
                  {loadingHistory ? <RefreshCw size={12} className="spin" /> : <RefreshCw size={12} />}刷新
                </button>
              </div>
            </div>
            <div className="history-search-row">
              <input
                type="text"
                value={historySearch}
                onChange={(e) => setHistorySearch(e.target.value)}
                placeholder="搜索求测问题..."
              />
              <select value={historyFilter} onChange={(e) => setHistoryFilter(e.target.value)}>
                <option value="all">全部状态</option>
                <option value="casted">已排盘</option>
                <option value="interacting">交互中</option>
                <option value="reviewed">已复盘</option>
                <option value="draft">待排盘</option>
              </select>
            </div>
            {loadingHistory ? (
              <p className="history-loading">加载中...</p>
            ) : (() => {
              const filtered = sessionList.filter((s) => {
                const matchSearch = !historySearch || (s.question || "").toLowerCase().includes(historySearch.toLowerCase());
                const matchFilter = historyFilter === "all" || s.status === historyFilter;
                return matchSearch && matchFilter;
              });
              if (filtered.length === 0) {
                return <p className="empty-hint">暂无匹配的会话。</p>;
              }
              return (
                <div className="session-list">
                  {filtered.map((s) => (
                    <div
                      key={s.session_id}
                      className="session-list-item"
                      onClick={() => handleRestoreFromList(s.session_id)}
                    >
                      <div className="session-item-main">
                        <span className="session-question">{s.question || "(无标题)"}</span>
                        <div className="session-item-meta">
                          <span className="session-category">{categoryLabel(s.category)}</span>
                          <span className="session-status status-badge">{statusLabel(s.status)}</span>
                          <span className="session-date">{formatDate(s.created_at)}</span>
                        </div>
                      </div>
                      <button
                        className="session-delete-btn"
                        onClick={(e) => handleDeleteSession(s.session_id, e)}
                        title="删除会话"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              );
            })()}
          </div>
        )}

        {showRecover && (
          <div className="recover-panel">
            <div className="recover-row">
              <input
                type="text"
                value={recoverId}
                onChange={(e) => setRecoverId(e.target.value)}
                placeholder="输入会话ID（sess_xxx）恢复已有推演"
                onKeyDown={(e) => e.key === "Enter" && handleRecover()}
              />
              <button className="btn-primary btn-small" onClick={handleRecover} disabled={anyLoading || !recoverId.trim()}>
                {isLoading("recover") ? <Loader2 size={14} className="spin" /> : <RotateCcw size={14} />}
                恢复
              </button>
            </div>
          </div>
        )}

        <div className="workflow-form">
          <div className="form-group">
            <label>求测事由 *</label>
            <textarea
              value={form.question}
              onChange={(e) => setForm({ ...form, question: e.target.value })}
              placeholder="请描述你想求测的事项，例如：近期事业发展如何？这笔投资能否盈利？"
              rows={3}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) handleCreate();
              }}
            />
            <span className="form-hint">Ctrl+Enter 快速提交</span>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>事项类别</label>
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                {CATEGORIES.map((c) => (
                  <option key={c.id} value={c.id}>{c.label}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>术数门类</label>
              <select value={form.system} onChange={(e) => setForm({ ...form, system: e.target.value })}>
                {SYSTEMS.map((s) => (
                  <option key={s.id} value={s.id}>{s.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>起盘方式</label>
              <select value={form.castingMethod} onChange={(e) => setForm({ ...form, castingMethod: e.target.value })}>
                {CASTING_METHODS.map((m) => (
                  <option key={m.id} value={m.id}>{m.label}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>性别（八字/紫微用）</label>
              <select value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })}>
                <option value="男">男</option>
                <option value="女">女</option>
              </select>
            </div>
          </div>

          {/* 报数起卦输入 */}
          {form.castingMethod === "numbers" && (
            <div className="form-group numbers-input">
              <label>报数（至少2个正整数，梅花易数用前3个）</label>
              <div className="numbers-row">
                {[0, 1, 2].map((i) => (
                  <input
                    key={i}
                    type="number"
                    min="1"
                    value={form.numbers[i]}
                    onChange={(e) => {
                      const nums = [...form.numbers];
                      nums[i] = e.target.value;
                      setForm({ ...form, numbers: nums });
                    }}
                    placeholder={`第${i + 1}个数`}
                  />
                ))}
              </div>
            </div>
          )}

          {/* 手工起卦输入 */}
          {form.castingMethod === "manual" && (
            <div className="form-group manual-input">
              <label>手工起卦</label>
              <div className="manual-row">
                <input
                  type="text"
                  value={form.manualUpper}
                  onChange={(e) => setForm({ ...form, manualUpper: e.target.value })}
                  placeholder="上卦（如：乾、坎、艮）"
                />
                <input
                  type="text"
                  value={form.manualLower}
                  onChange={(e) => setForm({ ...form, manualLower: e.target.value })}
                  placeholder="下卦（如：坤、离、兑）"
                />
                <input
                  type="number"
                  min="1"
                  max="6"
                  value={form.manualMoving}
                  onChange={(e) => setForm({ ...form, manualMoving: e.target.value })}
                  placeholder="动爻(1-6)"
                />
              </div>
            </div>
          )}

          <div className="form-group">
            <label>当前阶段（可选，有助于取象）</label>
            <input
              type="text"
              value={form.currentStage}
              onChange={(e) => setForm({ ...form, currentStage: e.target.value })}
              placeholder="例如：尚未开始 / 进行中遇阻 / 已出结果待抉择"
            />
          </div>

          {error && <div className="error-message"><AlertCircle size={16} />{error}</div>}

          <button className="btn-primary btn-large" onClick={handleCreate} disabled={anyLoading}>
            {isLoading("create") ? <RefreshCw size={18} className="spin" /> : <Play size={18} />}
            {isLoading("create") ? "创建中..." : "创建推演会话"}
          </button>

          <div className="workflow-notice">
            <ShieldCheck size={14} />
            <span>铁律：原始排盘一经生成永久固定，后续交互仅调整解读视角，绝不修改原始盘面。</span>
          </div>
        </div>
      </div>
    );
  
}
