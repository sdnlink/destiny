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
import StructuredDisplay from "../StructuredDisplay";
import InteractionResultDisplay from "../InteractionResultDisplay";
import CollapsibleSection from "./CollapsibleSection";

export default function ResultPhase({
  sessionId,
  result,
  error,
  activeTab,
  setActiveTab,
  interactionLog,
  realityResponse,
  setRealityResponse,
  realityDetails,
  setRealityDetails,
  multiPartyInput,
  setMultiPartyInput,
  multiChoiceInput,
  setMultiChoiceInput,
  reviewInput,
  setReviewInput,
  deepQuestionInput,
  setDeepQuestionInput,
  angleInput,
  setAngleInput,
  copied,
  resultRef,
  collapsed,
  isLoading,
  anyLoading,
  handleRealityCheck,
  handleMultiParty,
  handleMultiChoice,
  handleReview,
  handleDeepQuestion,
  handleAngleShift,
  handleCopyResult,
  handleExportResult,
  handleReset,
  toggleSection,
}) {
    const wf = result.workflow_result || {};
    const formatted = result.formatted_text || "";
    const hasHexagram = Boolean((wf.step5 || {}).hexagram_name);
    const step6 = wf.step6 || {};
    const fortune = step6.fortune_level || "平";

    return (
      <div className="workflow-panel result-state" ref={resultRef}>
        <div className="result-header">
          <div>
            <h2>推演结果</h2>
            <p className="result-meta">
              会话：{sessionId} · 快照：{result.snapshot_id} ·
              <span className="frozen-badge"><ShieldCheck size={12} />盘面已冻结</span>
            </p>
          </div>
          <div className="result-actions">
            <button className="btn-secondary btn-small" onClick={() => window.print()} title="打印推演报告 (Ctrl+P)">
              <Download size={14} />打印
            </button>
            <button className="btn-secondary btn-small" onClick={handleExportResult} title="导出为 Markdown 文件">
              <Download size={14} />导出
            </button>
            <button className="btn-secondary btn-small" onClick={handleCopyResult} title="复制完整推演文本">
              {copied ? <Check size={14} /> : <Copy size={14} />}
              {copied ? "已复制" : "复制"}
            </button>
            <button className="btn-secondary btn-small" onClick={handleReset}>
              <RefreshCw size={14} />新起一盘
            </button>
          </div>
        </div>

        <div className="fortune-banner" style={{ borderLeftColor: FORTUNE_COLORS[fortune] || "#a66d1e" }}>
          <span className="fortune-label">吉凶定性</span>
          <span className="fortune-value" style={{ color: FORTUNE_COLORS[fortune] || "#202622" }}>{fortune}</span>
          <span className="fortune-basis">{(step6.fortune_basis || []).join("；")}</span>
        </div>

        <div className="result-tabs">
          {[
            { id: "overview", label: "完整推演" },
            { id: "structured", label: "结构化数据" },
            { id: "interact", label: "交互深化" },
            { id: "history", label: `交互记录(${interactionLog.length})` },
          ].map((tab) => (
            <button
              key={tab.id}
              className={activeTab === tab.id ? "active" : ""}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "overview" && (
          <div className="result-content">
            <pre className="formatted-result">{formatted}</pre>
          </div>
        )}

        {activeTab === "structured" && (
          <div className="result-content structured-view">
            <StructuredDisplay workflow={wf} />
          </div>
        )}

        {activeTab === "interact" && (
          <div className="result-content interact-view">
            <h3><MessageSquare size={18} />交互深化（原始盘面不变，仅调整解读视角）</h3>

            <CollapsibleSection
              title="📌 盘面现状核对"
              collapsed={collapsed.reality}
              onToggle={() => toggleSection("reality")}
              defaultOpen={true}
            >
              <p className="interact-hint">回复符合/部分符合/不符合，仅调整事理解读视角</p>
              <div className="interact-row">
                <select value={realityResponse} onChange={(e) => setRealityResponse(e.target.value)}>
                  <option value="">请选择...</option>
                  <option value="符合">符合</option>
                  <option value="部分符合">部分符合</option>
                  <option value="不符合">不符合</option>
                </select>
                <input
                  type="text"
                  value={realityDetails}
                  onChange={(e) => setRealityDetails(e.target.value)}
                  placeholder="补充细节（哪些符合/不符）"
                  onKeyDown={(e) => e.key === "Enter" && handleRealityCheck()}
                />
                <button className="btn-primary btn-small" onClick={handleRealityCheck} disabled={anyLoading || !realityResponse}>
                  {isLoading("reality") ? <Loader2 size={14} className="spin" /> : "提交"}
                </button>
              </div>
            </CollapsibleSection>

            <CollapsibleSection
              title={<><Users size={16} /> 多方人物取象</>}
              collapsed={collapsed.multiparty}
              onToggle={() => toggleSection("multiparty")}
            >
              <p className="interact-hint">输入涉及的人物角色，用逗号分隔</p>
              <div className="interact-row">
                <input
                  type="text"
                  value={multiPartyInput}
                  onChange={(e) => setMultiPartyInput(e.target.value)}
                  placeholder="例如：求测人,对方,领导,客户"
                  onKeyDown={(e) => e.key === "Enter" && handleMultiParty()}
                />
                <button className="btn-primary btn-small" onClick={handleMultiParty} disabled={anyLoading || !multiPartyInput.trim()}>
                  {isLoading("multiparty") ? <Loader2 size={14} className="spin" /> : "分析"}
                </button>
              </div>
            </CollapsibleSection>

            <CollapsibleSection
              title={<><GitBranch size={16} /> 多抉择分支推演</>}
              collapsed={collapsed.multichoice}
              onToggle={() => toggleSection("multichoice")}
            >
              <p className="interact-hint">每行输入一个备选方案</p>
              <div className="interact-col">
                <textarea
                  value={multiChoiceInput}
                  onChange={(e) => setMultiChoiceInput(e.target.value)}
                  placeholder={"方案A：继续当前路径\n方案B：转换新方向"}
                  rows={3}
                />
                <button className="btn-primary btn-small" onClick={handleMultiChoice} disabled={anyLoading || !multiChoiceInput.trim()}>
                  {isLoading("multichoice") ? <Loader2 size={14} className="spin" /> : "推演分支"}
                </button>
              </div>
            </CollapsibleSection>

            <CollapsibleSection
              title={<><History size={16} /> 事后复盘</>}
              collapsed={collapsed.review}
              onToggle={() => toggleSection("review")}
            >
              <p className="interact-hint">反馈现实结果，对比应验与未应验</p>
              <div className="interact-col">
                <textarea
                  value={reviewInput}
                  onChange={(e) => setReviewInput(e.target.value)}
                  placeholder="描述实际发生的结果..."
                  rows={2}
                />
                <button className="btn-primary btn-small" onClick={handleReview} disabled={anyLoading || !reviewInput.trim()}>
                  {isLoading("review") ? <Loader2 size={14} className="spin" /> : "复盘"}
                </button>
              </div>
            </CollapsibleSection>

            <CollapsibleSection
              title="🔍 深度追问 / 换角度"
              collapsed={collapsed.deep}
              onToggle={() => toggleSection("deep")}
            >
              <div className="interact-row">
                <input
                  type="text"
                  value={deepQuestionInput}
                  onChange={(e) => setDeepQuestionInput(e.target.value)}
                  placeholder={hasHexagram
                    ? "针对某符号/断语深度追问，如：动爻代表什么？"
                    : "针对某符号/断语深度追问，如：用神代表什么？"}
                  onKeyDown={(e) => e.key === "Enter" && handleDeepQuestion()}
                />
                <button className="btn-secondary btn-small" onClick={handleDeepQuestion} disabled={anyLoading || !deepQuestionInput.trim()}>
                  {isLoading("deep") ? <Loader2 size={14} className="spin" /> : "追问"}
                </button>
              </div>
              <div className="interact-row" style={{ marginTop: 8 }}>
                <input
                  type="text"
                  value={angleInput}
                  onChange={(e) => setAngleInput(e.target.value)}
                  placeholder="换角度解读，如：从对方立场/长期视角/财务角度"
                  onKeyDown={(e) => e.key === "Enter" && handleAngleShift()}
                />
                <button className="btn-secondary btn-small" onClick={handleAngleShift} disabled={anyLoading || !angleInput.trim()}>
                  {isLoading("angle") ? <Loader2 size={14} className="spin" /> : "换角度"}
                </button>
              </div>
              <div className="angle-presets">
                <span className="angle-presets-label">快捷角度：</span>
                {["对方立场", "长期视角", "财务角度", "风险角度", "机会角度"].map((a) => (
                  <button key={a} className="angle-preset-btn" onClick={() => setAngleInput(a)}>
                    {a}
                  </button>
                ))}
              </div>
            </CollapsibleSection>

            {error && <div className="error-message"><AlertCircle size={16} />{error}</div>}
          </div>
        )}

        {activeTab === "history" && (
          <div className="result-content history-view">
            {interactionLog.length === 0 ? (
              <p className="empty-hint">暂无交互记录。切换到"交互深化"进行多轮推演。</p>
            ) : (
              interactionLog.map((item, i) => (
                <div key={i} className="history-item">
                  <div className="history-item-header">
                    <span className="history-type">{item.label}</span>
                    <span className="history-time">{item.time}</span>
                  </div>
                  <InteractionResultDisplay data={item.data} showCopy={true} />
                </div>
              ))
            )}
          </div>
        )}
      </div>
    );
  
}
