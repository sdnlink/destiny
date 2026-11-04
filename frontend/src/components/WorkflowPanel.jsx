import { useState, useRef, useEffect, useCallback } from "react";
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
import {
  createSession,
  castSession,
  realityCheck,
  multiPartyAnalysis,
  multiChoiceAnalysis,
  reviewOutcome,
  deepQuestion,
  angleShift,
  applyCompletion,
  getSession,
  listSessions,
  deleteSession,
} from "../lib/sessionApi";
import HexagramView from "./HexagramView";
import StructuredDisplay from "./StructuredDisplay";
import InteractionResultDisplay from "./InteractionResultDisplay";
import {
  CATEGORIES,
  CASTING_METHODS,
  FORTUNE_COLORS,
  SYSTEMS,
  categoryLabel,
  statusLabel,
  formatDate,
} from "../lib/labels";
import { localDateTimeValue, newCastNonce } from "../lib/castingInput";


export default function WorkflowPanel() {
  const [phase, setPhase] = useState("create");
  const [sessionId, setSessionId] = useState(null);
  const [form, setForm] = useState({
    question: "",
    category: "career",
    system: "auto",
    castingMethod: "auto",
    gender: "男",
    currentStage: "",
    numbers: ["", "", ""],
    manualUpper: "",
    manualLower: "",
    manualMoving: "",
  });
  const [completion, setCompletion] = useState(null);
  const [completionAnswers, setCompletionAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [loadingType, setLoadingType] = useState(null);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("overview");
  const [interactionLog, setInteractionLog] = useState([]);
  const [realityResponse, setRealityResponse] = useState("");
  const [realityDetails, setRealityDetails] = useState("");
  const [multiPartyInput, setMultiPartyInput] = useState("");
  const [multiChoiceInput, setMultiChoiceInput] = useState("");
  const [reviewInput, setReviewInput] = useState("");
  const [deepQuestionInput, setDeepQuestionInput] = useState("");
  const [angleInput, setAngleInput] = useState("");
  const [collapsed, setCollapsed] = useState({});
  const [copied, setCopied] = useState(false);
  const [recoverId, setRecoverId] = useState("");
  const [showRecover, setShowRecover] = useState(false);
  const [sessionList, setSessionList] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [historySearch, setHistorySearch] = useState("");
  const [historyFilter, setHistoryFilter] = useState("all");
  const resultRef = useRef(null);
  const errorTimer = useRef(null);
  const DRAFT_KEY = "destiny_workflow_draft";

  // 恢复草稿
  useEffect(() => {
    try {
      const saved = localStorage.getItem(DRAFT_KEY);
      if (saved) {
        const draft = JSON.parse(saved);
        setForm((prev) => ({ ...prev, ...draft }));
      }
    } catch {
      // ignore
    }
  }, []);

  // 自动保存草稿
  useEffect(() => {
    if (phase === "create") {
      try {
        localStorage.setItem(DRAFT_KEY, JSON.stringify(form));
      } catch {
        // ignore
      }
    }
  }, [form, phase]);

  // 键盘快捷键
  useEffect(() => {
    if (phase !== "result") return;
    const handler = (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT") return;
      if (e.key >= "1" && e.key <= "4") {
        const tabs = ["overview", "structured", "interact", "history"];
        setActiveTab(tabs[parseInt(e.key, 10) - 1]);
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "p") {
        e.preventDefault();
        window.print();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [phase]);

  const isLoading = (type) => loadingType === type;
  const anyLoading = loadingType !== null;

  // 错误自动清除
  const showError = useCallback((msg) => {
    setError(msg);
    if (errorTimer.current) clearTimeout(errorTimer.current);
    errorTimer.current = setTimeout(() => setError(""), 6000);
  }, []);

  useEffect(() => {
    return () => {
      if (errorTimer.current) clearTimeout(errorTimer.current);
    };
  }, []);

  const handleCreate = async () => {
    if (!form.question.trim()) {
      showError("请输入求测事由");
      return;
    }
    setLoadingType("create");
    try {
      const castingSource = {
        local_datetime: localDateTimeValue(),
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Shanghai",
        cast_nonce: newCastNonce(),
        use_true_solar_time: false,
      };
      if (form.castingMethod === "numbers") {
        const nums = form.numbers.map((n) => parseInt(n, 10)).filter((n) => !isNaN(n) && n > 0);
        if (nums.length < 2) {
          showError("报数起卦请至少输入2个正整数");
          setLoadingType(null);
          return;
        }
        castingSource.numbers = nums;
      }
      if (form.castingMethod === "manual") {
        if (!form.manualUpper || !form.manualLower) {
          showError("手工起卦请填写上卦和下卦");
          setLoadingType(null);
          return;
        }
        castingSource.manual = {
          upper_trigram: form.manualUpper,
          lower_trigram: form.manualLower,
          moving_line: form.manualMoving ? parseInt(form.manualMoving, 10) : null,
        };
      }
      const userProfile = {};
      if (form.gender) userProfile.gender = form.gender;
      if (form.currentStage) userProfile.current_stage = form.currentStage;

      const data = await createSession({
        question: form.question,
        category: form.category,
        system: form.system,
        casting_method: form.castingMethod,
        casting_source: castingSource,
        user_profile: userProfile,
      });
      setSessionId(data.session_id);
      setCompletion(data.info_completion);
      setCompletionAnswers({});
      setPhase("completion");
    } catch (e) {
      showError(e.message);
    } finally {
      setLoadingType(null);
    }
  };

  const doCast = async () => {
    setPhase("casting");
    try {
      const data = await castSession(sessionId);
      setResult(data);
      setPhase("result");
      setActiveTab("overview");
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    } catch (e) {
      showError(e.message);
      setPhase("completion");
    }
  };

  const handleSkipCompletion = async () => {
    setLoadingType("cast");
    try {
      await doCast();
    } catch (e) {
      showError(e.message);
    } finally {
      setLoadingType(null);
    }
  };

  const handleApplyCompletion = async () => {
    setLoadingType("cast");
    try {
      if (Object.keys(completionAnswers).length > 0) {
        await applyCompletion(sessionId, completionAnswers);
      }
      await doCast();
    } catch (e) {
      showError(e.message);
    } finally {
      setLoadingType(null);
    }
  };

  const addInteraction = (type, label, data) => {
    setInteractionLog((prev) => [...prev, { type, label, data, time: new Date().toLocaleTimeString() }]);
    // 自动切换到交互记录标签
    setActiveTab("history");
  };

  const handleRealityCheck = async () => {
    if (!realityResponse) return;
    setLoadingType("reality");
    try {
      const data = await realityCheck(sessionId, realityResponse, realityDetails);
      addInteraction("reality_check", `现实校验：${realityResponse}`, data.interaction_result);
      setRealityResponse("");
      setRealityDetails("");
    } catch (e) {
      showError(e.message);
    } finally {
      setLoadingType(null);
    }
  };

  const handleMultiParty = async () => {
    if (!multiPartyInput.trim()) return;
    setLoadingType("multiparty");
    try {
      const parties = multiPartyInput.split(/[,，、]/).map((s) => s.trim()).filter(Boolean);
      const data = await multiPartyAnalysis(sessionId, parties);
      addInteraction("multi_party", `多方取象：${parties.join("、")}`, data.interaction_result);
      setMultiPartyInput("");
    } catch (e) {
      showError(e.message);
    } finally {
      setLoadingType(null);
    }
  };

  const handleMultiChoice = async () => {
    if (!multiChoiceInput.trim()) return;
    setLoadingType("multichoice");
    try {
      const choices = multiChoiceInput.split(/\n/).map((s) => s.trim()).filter(Boolean);
      const data = await multiChoiceAnalysis(sessionId, choices);
      addInteraction("multi_choice", `分支推演：${choices.length}个方案`, data.interaction_result);
      setMultiChoiceInput("");
    } catch (e) {
      showError(e.message);
    } finally {
      setLoadingType(null);
    }
  };

  const handleReview = async () => {
    if (!reviewInput.trim()) return;
    setLoadingType("review");
    try {
      const data = await reviewOutcome(sessionId, reviewInput);
      addInteraction("review", "事后复盘", data.interaction_result);
      setReviewInput("");
    } catch (e) {
      showError(e.message);
    } finally {
      setLoadingType(null);
    }
  };

  const handleDeepQuestion = async () => {
    if (!deepQuestionInput.trim()) return;
    setLoadingType("deep");
    try {
      const data = await deepQuestion(sessionId, deepQuestionInput);
      addInteraction("deep_question", `深度追问：${deepQuestionInput.slice(0, 20)}`, data.interaction_result);
      setDeepQuestionInput("");
    } catch (e) {
      showError(e.message);
    } finally {
      setLoadingType(null);
    }
  };

  const handleAngleShift = async () => {
    if (!angleInput.trim()) return;
    setLoadingType("angle");
    try {
      const data = await angleShift(sessionId, angleInput);
      addInteraction("angle_shift", `换角度：${angleInput}`, data.interaction_result);
      setAngleInput("");
    } catch (e) {
      showError(e.message);
    } finally {
      setLoadingType(null);
    }
  };

  const handleRecover = async () => {
    if (!recoverId.trim()) return;
    setLoadingType("recover");
    try {
      const data = await getSession(recoverId.trim());
      if (data.snapshot) {
        setSessionId(data.session_id);
        setResult({
          session_id: data.session_id,
          snapshot_id: data.snapshot.snapshot_id,
          workflow_result: data.workflow_result,
          formatted_text: data.formatted_text,
        });
        setInteractionLog(data.interactions || []);
        setPhase("result");
        setActiveTab("overview");
        setShowRecover(false);
        setRecoverId("");
      } else {
        showError("该会话尚未排盘，无法恢复结果");
      }
    } catch (e) {
      showError(e.message);
    } finally {
      setLoadingType(null);
    }
  };

  const loadSessionList = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const data = await listSessions(50);
      setSessionList(Array.isArray(data) ? data : []);
    } catch (e) {
      showError(e.message);
    } finally {
      setLoadingHistory(false);
    }
  }, [showError]);

  const handleRestoreFromList = async (sid) => {
    setLoadingType("recover");
    try {
      const data = await getSession(sid);
      if (data.snapshot) {
        setSessionId(data.session_id);
        setResult({
          session_id: data.session_id,
          snapshot_id: data.snapshot.snapshot_id,
          workflow_result: data.workflow_result,
          formatted_text: data.formatted_text,
        });
        setInteractionLog(data.interactions || []);
        setPhase("result");
        setActiveTab("overview");
        setShowHistory(false);
      } else {
        showError("该会话尚未排盘，无法恢复结果");
      }
    } catch (e) {
      showError(e.message);
    } finally {
      setLoadingType(null);
    }
  };

  const handleDeleteSession = async (sid, e) => {
    e.stopPropagation();
    if (!confirm("确定删除该会话？删除后不可恢复。")) return;
    try {
      await deleteSession(sid);
      setSessionList((prev) => prev.filter((s) => s.session_id !== sid));
    } catch (err) {
      showError(err.message);
    }
  };

  const handleExportSessionsJSON = () => {
    const data = JSON.stringify(sessionList, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `推演会话备份_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleImportSessionsJSON = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const imported = JSON.parse(ev.target.result);
        if (Array.isArray(imported)) {
          setSessionList((prev) => {
            const existing = new Set(prev.map((s) => s.session_id));
            const merged = [...prev];
            for (const item of imported) {
              if (item.session_id && !existing.has(item.session_id)) {
                merged.push(item);
                existing.add(item.session_id);
              }
            }
            return merged;
          });
          showError(`已导入 ${imported.length} 条会话记录（仅列表，完整数据需后端支持）`);
        } else {
          showError("导入文件格式不正确");
        }
      } catch {
        showError("JSON 解析失败");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  const handleCopyResult = async () => {
    const formatted = result?.formatted_text || "";
    if (!formatted) return;
    try {
      await navigator.clipboard.writeText(formatted);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      showError("复制失败，请手动选择文本复制");
    }
  };

  const handleExportResult = () => {
    const formatted = result?.formatted_text || "";
    if (!formatted) return;
    const question = result?.question || form.question || "推演报告";
    const blob = new Blob([formatted], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `推演报告_${question.slice(0, 20)}_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const clearDraft = () => {
    try {
      localStorage.removeItem(DRAFT_KEY);
    } catch {
      // ignore
    }
  };

  const handleReset = () => {
    setPhase("create");
    setSessionId(null);
    setResult(null);
    setCompletion(null);
    setInteractionLog([]);
    setError("");
    setActiveTab("overview");
    setCollapsed({});
    clearDraft();
  };

  const toggleSection = (key) => {
    setCollapsed((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // ========== 创建阶段 ==========
  if (phase === "create") {
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
            <span>铁律：原始排盘一经生成永久固定，后续交互仅调整解读视角，绝不修改卦盘本身。</span>
          </div>
        </div>
      </div>
    );
  }

  // ========== 信息补全阶段 ==========
  if (phase === "completion" && completion) {
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

  // ========== 排盘中 ==========
  if (phase === "casting") {
    return (
      <div className="workflow-panel casting-state">
        <RefreshCw size={48} className="spin large" />
        <h2>正在执行7步排盘推理...</h2>
        <p>信息校验 → 完整排盘 → 定用神 → 旺衰计算 → 象义拆解 → 综合推演 → 行动建议</p>
        <p className="casting-note">盘面生成后将永久冻结，不可修改。</p>
      </div>
    );
  }

  // ========== 结果与交互阶段 ==========
  if (phase === "result" && result) {
    const wf = result.workflow_result || {};
    const formatted = result.formatted_text || "";
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
              title="📌 卦象现状核对"
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
                  placeholder="针对某符号/断语深度追问，如：动爻代表什么？"
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

  return null;
}

// ========== 折叠面板组件 ==========
function CollapsibleSection({ title, collapsed, onToggle, children, defaultOpen }) {
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

