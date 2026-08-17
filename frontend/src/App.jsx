import { useEffect, useMemo, useState } from "react";
import {
  Archive,
  BookOpenCheck,
  Database,
  FileClock,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Settings,
  ShieldCheck,
  X,
} from "lucide-react";
import InputPanel from "./components/InputPanel";
import ResultWorkspace from "./components/ResultWorkspace";
import { analyzeCalendar, checkHealth, compareCalculations, loadRules } from "./lib/api";

function localDateTimeValue(date = new Date()) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

function newCastNonce() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID().replaceAll("-", "");
  const bytes = new Uint8Array(16);
  globalThis.crypto.getRandomValues(bytes);
  return Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
}

function initialForm() {
  return {
    scene: "combined",
    category: "career",
    question: "近期事项推演",
    localDatetime: localDateTimeValue(),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Shanghai",
    trueSolar: false,
    longitude: "",
    castNonce: newCastNonce(),
    yiMethod: "auto",
    lines: [7, 8, 7, 8, 7, 8],
    yiLower: "8",
    yiUpper: "8",
    meihuaMethod: "auto",
    mhUpper: "8",
    mhLower: "8",
    liuyaoMethod: "auto",
    lyLower: "8",
    lyUpper: "8",
    liurenMethod: "auto",
    lrNumber: "8",
    ziweiMethod: "time",
    ziweiGender: "男",
    fsFacing: "180",
    fsMode: "single",
    fsMeasurements: ["179", "180", "181"],
    fsReference: "magnetic",
    fsDeclination: "0",
    fsError: "1",
  };
}

function calendarPayload(form) {
  const payload = {
    local_datetime: form.localDatetime,
    timezone: form.timezone,
    use_true_solar_time: form.trueSolar,
  };
  if (form.trueSolar) payload.longitude = Number(form.longitude);
  return payload;
}

function buildCalculations(form) {
  const calendar = calendarPayload(form);
  const auto = { ...calendar, cast_nonce: form.castNonce };
  const calculations = [{ module: "calendar", method: "analyze", input: calendar }];
  if (form.scene === "combined" || form.scene === "zhouyi") {
    calculations.push(
      form.yiMethod === "auto"
        ? { module: "zhouyi", method: "auto", input: auto }
        : form.yiMethod === "time"
        ? { module: "zhouyi", method: "time", input: calendar }
        : form.yiMethod === "manual"
        ? { module: "zhouyi", method: "manual", input: { lines: form.lines } }
        : {
            module: "zhouyi",
            method: "numbers",
            input: { lower_number: Number(form.yiLower), upper_number: Number(form.yiUpper) },
          },
    );
  }
  if (form.scene === "combined" || form.scene === "meihua") {
    calculations.push(
      form.meihuaMethod === "auto"
        ? { module: "meihua", method: "auto", input: auto }
        : form.meihuaMethod === "time"
        ? { module: "meihua", method: "time", input: calendar }
        : {
            module: "meihua",
            method: "numbers",
            input: { upper_number: Number(form.mhUpper), lower_number: Number(form.mhLower) },
          },
    );
  }
  if (form.scene === "combined" || form.scene === "liuyao") {
    calculations.push(
      form.liuyaoMethod === "auto"
        ? { module: "liuyao", method: "auto", input: auto }
        : form.liuyaoMethod === "time"
        ? { module: "liuyao", method: "time", input: calendar }
        : {
            module: "liuyao",
            method: "numbers",
            input: { ...calendar, lower_number: Number(form.lyLower), upper_number: Number(form.lyUpper) },
          },
    );
  }
  if (form.scene === "combined" || form.scene === "liuren") {
    calculations.push(
      form.liurenMethod === "auto"
        ? { module: "liuren", method: "auto", input: auto }
        : form.liurenMethod === "time"
        ? { module: "liuren", method: "time", input: calendar }
        : { module: "liuren", method: "numbers", input: { ...calendar, number: Number(form.lrNumber) } },
    );
  }
  if (form.scene === "combined" || form.scene === "ziwei") {
    calculations.push(
      form.ziweiMethod === "auto"
        ? { module: "ziwei", method: "auto", input: { ...auto, gender: form.ziweiGender } }
        : { module: "ziwei", method: "time", input: { ...calendar, gender: form.ziweiGender } },
    );
  }
  if (form.scene === "fengshui") {
    calculations.push({
      module: "fengshui",
      method: form.fsMode === "multiple" ? "measurements" : "direction",
      input: form.fsMode === "multiple"
        ? {
            measurements: form.fsMeasurements.map((degree) => ({
              facing_degree: Number(degree),
              input_reference: form.fsReference,
              magnetic_declination: Number(form.fsDeclination),
              measurement_error: Number(form.fsError),
              measurement_method: "web_multi_entry",
            })),
          }
        : {
            facing_degree: Number(form.fsFacing),
            input_reference: form.fsReference,
            magnetic_declination: Number(form.fsDeclination),
            measurement_error: Number(form.fsError),
            measurement_method: "web_manual_entry",
          },
    });
  }
  return calculations;
}

function AppNavigation({ collapsed, setCollapsed, openRules, serviceOnline }) {
  return (
    <nav className={`app-navigation ${collapsed ? "collapsed" : ""}`} aria-label="主导航">
      <div className="brand-lockup">
        <div className="brand-mark"><span>☰</span><span>☷</span></div>
        {!collapsed && <div><strong>天机演象</strong><span>推演工作台</span></div>}
      </div>
      <div className="nav-items">
        <button className="active" title="新建推演"><Plus size={18} /><span>新建推演</span></button>
        <button disabled title="案例库尚未启用"><Archive size={18} /><span>案例库</span><small>待建设</small></button>
        <button onClick={openRules} title="规则目录"><BookOpenCheck size={18} /><span>规则目录</span></button>
        <button disabled title="历史任务尚未持久化"><FileClock size={18} /><span>历史任务</span><small>待建设</small></button>
      </div>
      <div className="nav-bottom">
        <button disabled title="设置尚未启用"><Settings size={18} /><span>设置</span></button>
        <div className="service-state" title={serviceOnline ? "计算服务在线" : "计算服务离线"}>
          <i className={serviceOnline ? "online" : ""} />
          {!collapsed && <span>{serviceOnline ? "计算服务在线" : "服务连接异常"}</span>}
        </div>
        <button className="collapse-button" onClick={() => setCollapsed(!collapsed)} title={collapsed ? "展开导航" : "收起导航"}>
          {collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
          <span>{collapsed ? "展开" : "收起"}</span>
        </button>
      </div>
    </nav>
  );
}

function RulesDrawer({ open, onClose, rules, loading }) {
  const [system, setSystem] = useState("all");
  const filtered = useMemo(
    () => (system === "all" ? rules : rules.filter((rule) => rule.system === system)),
    [rules, system],
  );
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
          {[["all", "全部"], ["calendar", "历法"], ["zhouyi", "周易"], ["meihua", "梅花"], ["liuyao", "六爻"], ["liuren", "六壬"], ["ziwei", "紫微"], ["fengshui", "风水"]].map(([id, label]) => (
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

export default function App() {
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [resultContext, setResultContext] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [error, setError] = useState("");
  const [serviceOnline, setServiceOnline] = useState(false);
  const [navCollapsed, setNavCollapsed] = useState(false);
  const [mobileInputOpen, setMobileInputOpen] = useState(true);
  const [rulesOpen, setRulesOpen] = useState(false);
  const [rules, setRules] = useState([]);
  const [rulesLoading, setRulesLoading] = useState(false);

  useEffect(() => {
    checkHealth().then(() => setServiceOnline(true)).catch(() => setServiceOnline(false));
  }, []);

  const handlePreview = async () => {
    setPreviewLoading(true);
    setError("");
    try {
      setPreview(await analyzeCalendar(calendarPayload(form)));
    } catch (requestError) {
      setError(requestError.message);
      setPreview(null);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await compareCalculations(buildCalculations(form), {
        category: form.category,
        question_summary: form.question,
      });
      setResult(response);
      setResultContext({ scene: form.scene, category: form.category, question: form.question });
      setActiveTab("overview");
      setServiceOnline(true);
      setMobileInputOpen(false);
      const calendar = response.module_results.find((item) => item.module === "calendar")?.result;
      if (calendar) setPreview(calendar);
    } catch (requestError) {
      setError(requestError.message);
      if (requestError instanceof TypeError) setServiceOnline(false);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setForm(initialForm());
    setResult(null);
    setResultContext(null);
    setPreview(null);
    setError("");
    setActiveTab("overview");
  };

  const handleRecast = () => {
    setForm((current) => ({ ...current, castNonce: newCastNonce() }));
    setResult(null);
    setResultContext(null);
    setError("");
    setActiveTab("overview");
  };

  const openRules = async () => {
    setRulesOpen(true);
    if (rules.length) return;
    setRulesLoading(true);
    try {
      const response = await loadRules();
      setRules(response.data || response);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setRulesLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <AppNavigation collapsed={navCollapsed} setCollapsed={setNavCollapsed} openRules={openRules} serviceOnline={serviceOnline} />
      <div className="mobile-topbar">
        <div className="brand-mark"><span>☰</span><span>☷</span></div>
        <strong>天机演象</strong>
        <button className="icon-button" onClick={() => setMobileInputOpen(!mobileInputOpen)} aria-label="切换输入面板"><Menu size={20} /></button>
      </div>
      <div className={`input-column ${mobileInputOpen ? "mobile-open" : ""}`}>
        <InputPanel
          form={form}
          setForm={setForm}
          onSubmit={handleSubmit}
          onPreview={handlePreview}
          onReset={handleReset}
          onRecast={handleRecast}
          loading={loading}
          previewLoading={previewLoading}
          preview={preview}
          error={error}
        />
      </div>
      <ResultWorkspace result={result} context={resultContext} activeTab={activeTab} setActiveTab={setActiveTab} />
      <RulesDrawer open={rulesOpen} onClose={() => setRulesOpen(false)} rules={rules} loading={rulesLoading} />
    </div>
  );
}
