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
import CreatePhase from "./workflow/CreatePhase";
import CompletionPhase from "./workflow/CompletionPhase";
import ResultPhase from "./workflow/ResultPhase";
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


export default function WorkflowPanel({ recoverSessionId = null, onRecovered = null } = {}) {
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

  // 从历史抽屉里点"在交互推演中打开"时，由外壳把 session_id 传进来，这里直接恢复该会话。
  useEffect(() => {
    if (!recoverSessionId) return;
    handleRestoreFromList(recoverSessionId).finally(() => onRecovered?.());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recoverSessionId]);

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
      <CreatePhase
        form={form}
        setForm={setForm}
        error={error}
        recoverId={recoverId}
        setRecoverId={setRecoverId}
        showRecover={showRecover}
        setShowRecover={setShowRecover}
        sessionList={sessionList}
        showHistory={showHistory}
        setShowHistory={setShowHistory}
        loadingHistory={loadingHistory}
        historySearch={historySearch}
        setHistorySearch={setHistorySearch}
        historyFilter={historyFilter}
        setHistoryFilter={setHistoryFilter}
        isLoading={isLoading}
        anyLoading={anyLoading}
        handleCreate={handleCreate}
        handleRecover={handleRecover}
        loadSessionList={loadSessionList}
        handleRestoreFromList={handleRestoreFromList}
        handleDeleteSession={handleDeleteSession}
        handleExportSessionsJSON={handleExportSessionsJSON}
        handleImportSessionsJSON={handleImportSessionsJSON}
      />
    );
  }

  // ========== 信息补全阶段 ==========
  if (phase === "completion" && completion) {
    return (
      <CompletionPhase
        sessionId={sessionId}
        completion={completion}
        completionAnswers={completionAnswers}
        setCompletionAnswers={setCompletionAnswers}
        error={error}
        isLoading={isLoading}
        anyLoading={anyLoading}
        handleSkipCompletion={handleSkipCompletion}
        handleApplyCompletion={handleApplyCompletion}
      />
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
    return (
      <ResultPhase
        sessionId={sessionId}
        result={result}
        error={error}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        interactionLog={interactionLog}
        realityResponse={realityResponse}
        setRealityResponse={setRealityResponse}
        realityDetails={realityDetails}
        setRealityDetails={setRealityDetails}
        multiPartyInput={multiPartyInput}
        setMultiPartyInput={setMultiPartyInput}
        multiChoiceInput={multiChoiceInput}
        setMultiChoiceInput={setMultiChoiceInput}
        reviewInput={reviewInput}
        setReviewInput={setReviewInput}
        deepQuestionInput={deepQuestionInput}
        setDeepQuestionInput={setDeepQuestionInput}
        angleInput={angleInput}
        setAngleInput={setAngleInput}
        copied={copied}
        resultRef={resultRef}
        collapsed={collapsed}
        isLoading={isLoading}
        anyLoading={anyLoading}
        handleRealityCheck={handleRealityCheck}
        handleMultiParty={handleMultiParty}
        handleMultiChoice={handleMultiChoice}
        handleReview={handleReview}
        handleDeepQuestion={handleDeepQuestion}
        handleAngleShift={handleAngleShift}
        handleCopyResult={handleCopyResult}
        handleExportResult={handleExportResult}
        handleReset={handleReset}
        toggleSection={toggleSection}
      />
    );
  }

  return null;
}
