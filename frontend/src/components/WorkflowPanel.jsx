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

const CATEGORIES = [
  { id: "career", label: "事业" },
  { id: "finance", label: "财运" },
  { id: "relationship", label: "感情姻缘" },
  { id: "study", label: "考试学业" },
  { id: "lawsuit", label: "官司是非" },
  { id: "travel", label: "出行" },
  { id: "missing_person", label: "寻人" },
  { id: "lost_item", label: "失物" },
  { id: "health", label: "健康" },
  { id: "decision", label: "抉择" },
  { id: "other", label: "其他谋事" },
];

const SYSTEMS = [
  { id: "auto", label: "默认（梅花+六爻）" },
  { id: "meihua", label: "梅花易数" },
  { id: "liuyao", label: "六爻纳甲" },
  { id: "qimen", label: "奇门遁甲" },
  { id: "daliuren", label: "大六壬" },
  { id: "bazi", label: "八字命理" },
  { id: "ziwei", label: "紫微斗数" },
];

const CASTING_METHODS = [
  { id: "auto", label: "自动起卦" },
  { id: "time", label: "时间起卦" },
  { id: "numbers", label: "报数起卦" },
  { id: "manual", label: "手工起卦" },
];

const FORTUNE_COLORS = {
  大吉: "#297267",
  小吉: "#3a8a7d",
  平: "#a66d1e",
  小凶: "#b85c3a",
  大凶: "#a53e2d",
};

function localDateTimeValue() {
  const d = new Date();
  const local = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

function newCastNonce() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID().replaceAll("-", "");
  const bytes = new Uint8Array(16);
  globalThis.crypto.getRandomValues(bytes);
  return Array.from(bytes, (v) => v.toString(16).padStart(2, "0")).join("");
}

function categoryLabel(cat) {
  const found = CATEGORIES.find((c) => c.id === cat);
  return found ? found.label : cat || "未知";
}

function statusLabel(status) {
  const map = { draft: "待排盘", casted: "已排盘", interacting: "交互中", reviewed: "已复盘" };
  return map[status] || status || "未知";
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
  } catch {
    return dateStr;
  }
}

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
              <button className="btn-small btn-secondary" onClick={loadSessionList} disabled={loadingHistory}>
                {loadingHistory ? <RefreshCw size={12} className="spin" /> : <RefreshCw size={12} />}刷新
              </button>
            </div>
            {loadingHistory ? (
              <p className="history-loading">加载中...</p>
            ) : sessionList.length === 0 ? (
              <p className="empty-hint">暂无历史会话。创建第一个推演会话后会显示在这里。</p>
            ) : (
              <div className="session-list">
                {sessionList.map((s) => (
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
            )}
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
                  <InteractionResultDisplay data={item.data} />
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

// ========== 结构化数据展示 ==========
function StructuredDisplay({ workflow }) {
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
  // 对特定步骤做友好展示
  if (stepKey === "step3") {
    return (
      <div className="structured-friendly">
        {data.primary_yongshen && <div className="friendly-row"><span className="friendly-label">主用神：</span><span>{data.primary_yongshen}</span></div>}
        {data.auxiliary_yongshen && <div className="friendly-row"><span className="friendly-label">辅助用神：</span><span>{data.auxiliary_yongshen}</span></div>}
        {data.yongshen_logic && <div className="friendly-row"><span className="friendly-label">取用逻辑：</span><span>{data.yongshen_logic}</span></div>}
        {data.multi_party_yongshen && (
          <div className="friendly-row">
            <span className="friendly-label">多方用神：</span>
            <ul>{Object.entries(data.multi_party_yongshen).map(([k, v]) => <li key={k}>{k}：{v}</li>)}</ul>
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
            {data.yongshen_wangshuai.details && <span className="friendly-sub">（{data.yongshen_wangshuai.details}）</span>}
          </div>
        )}
        {data.ti_yong_relation && <div className="friendly-row"><span className="friendly-label">体用关系：</span><span>{data.ti_yong_relation}</span></div>}
        {data.shengke_chain && Array.isArray(data.shengke_chain) && (
          <div className="friendly-row">
            <span className="friendly-label">生克链条：</span>
            <ul>{data.shengke_chain.map((c, i) => <li key={i}>{c}</li>)}</ul>
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
  // 默认：JSON 展示
  return <pre>{JSON.stringify(data, null, 2)}</pre>;
}

// ========== 交互结果展示 ==========
function InteractionResultDisplay({ data }) {
  if (!data) return null;

  // 深度追问结果
  if (data.type === "deep_question" && data.analysis) {
    return (
      <div className="interaction-result deep-question-result">
        <p><strong>追问：</strong>{data.question}</p>
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
        <p><strong>新角度：</strong>{data.new_angle}</p>
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
  return <pre className="interaction-result">{JSON.stringify(data, null, 2)}</pre>;
}
