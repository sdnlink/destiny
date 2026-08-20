import { useEffect, useMemo, useRef, useState } from "react";
import {
  Archive,
  ArrowRight,
  BookOpen,
  BookOpenCheck,
  Database,
  Download,
  FileClock,
  Menu,
  Moon,
  Palette,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  Sun,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import InputPanel from "./components/InputPanel";
import ResultWorkspace from "./components/ResultWorkspace";
import { analyzeCalendar, checkHealth, compareCalculations, loadRules } from "./lib/api";
import { generateMarkdownReport, downloadMarkdownFile } from "./lib/export";
import { GLOSSARY_CATEGORIES, GLOSSARY_ITEMS } from "./lib/glossary";
import {
  clearDeductionHistory,
  deleteDeductionHistory,
  exportAllHistoryJSON,
  getDeductionHistory,
  importHistoryJSON,
  saveDeductionHistory,
} from "./lib/storage";

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
    qimenMethod: "time",
    baziMethod: "time",
    baziGender: "男",
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
  if (form.scene === "combined" || form.scene === "qimen") {
    calculations.push(
      form.qimenMethod === "auto"
        ? { module: "qimen", method: "auto", input: auto }
        : { module: "qimen", method: "time", input: calendar },
    );
  }
  if (form.scene === "combined" || form.scene === "bazi") {
    calculations.push(
      form.baziMethod === "auto"
        ? { module: "bazi", method: "auto", input: { ...auto, gender: form.baziGender || form.ziweiGender || "男" } }
        : { module: "bazi", method: "time", input: { ...calendar, gender: form.baziGender || form.ziweiGender || "男" } },
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

function AppNavigation({ collapsed, setCollapsed, openRules, openHistory, openGlossary, serviceOnline, theme, setTheme }) {
  const nextTheme = theme === "paper" ? "dark" : theme === "dark" ? "jade" : "paper";
  const themeLabel = theme === "paper" ? "宣纸素雅" : theme === "dark" ? "玄墨深邃" : "青铜古韵";
  const ThemeIcon = theme === "paper" ? Sun : theme === "dark" ? Moon : Palette;

  return (
    <nav className={`app-navigation ${collapsed ? "collapsed" : ""}`} aria-label="主导航">
      <div className="brand-lockup">
        <div className="brand-mark"><span>☰</span><span>☷</span></div>
        {!collapsed && <div><strong>天机演象</strong><span>推演工作台</span></div>}
      </div>
      <div className="nav-items">
        <button className="active" title="新建推演"><Plus size={18} /><span>新建推演</span></button>
        <button onClick={openHistory} title="历史推演记录与案例库"><Archive size={18} /><span>案例库</span></button>
        <button onClick={openRules} title="规则目录"><BookOpenCheck size={18} /><span>规则目录</span></button>
        <button onClick={openGlossary} title="术数典籍与核心概念速查"><BookOpen size={18} /><span>概念速查</span></button>
        <button onClick={openHistory} title="历史推演记录"><FileClock size={18} /><span>历史任务</span></button>
      </div>
      <div className="nav-bottom">
        <button className="theme-toggle-btn" onClick={() => setTheme(nextTheme)} title={`切换主题（当前：${themeLabel}，点击切换）`}>
          <ThemeIcon size={18} />
          {!collapsed && <span>{themeLabel}</span>}
        </button>
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

function GlossaryDrawer({ open, onClose }) {
  const [selectedCat, setSelectedCat] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredItems = useMemo(() => {
    return GLOSSARY_ITEMS.filter((item) => {
      const matchCat = selectedCat === "all" || item.category === selectedCat;
      const matchQuery =
        !searchQuery.trim() ||
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.desc.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.source.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.tag.toLowerCase().includes(searchQuery.toLowerCase());
      return matchCat && matchQuery;
    });
  }, [selectedCat, searchQuery]);

  if (!open) return null;

  return (
    <div className="drawer-layer" role="presentation" onMouseDown={onClose}>
      <aside className="rules-drawer glossary-drawer" role="dialog" aria-modal="true" aria-label="术数典籍与核心概念速查" onMouseDown={(e) => e.stopPropagation()}>
        <header>
          <div>
            <p className="section-kicker">CLASSICAL KNOWLEDGE BASE</p>
            <h2>术数典籍与概念速查</h2>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="关闭概念速查"><X size={19} /></button>
        </header>

        <div className="drawer-search-row">
          <Search size={15} />
          <input
            type="text"
            placeholder="快速检索卦名、十神、八门九星、二十四山、典籍出处..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button className="clear-search-btn" onClick={() => setSearchQuery("")}><X size={14} /></button>
          )}
        </div>

        <div className="segmented drawer-filter">
          {GLOSSARY_CATEGORIES.map(({ id, label }) => (
            <button
              key={id}
              className={selectedCat === id ? "active" : ""}
              onClick={() => setSelectedCat(id)}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="glossary-items-wrap">
          {filteredItems.length === 0 ? (
            <div className="drawer-loading">未找到匹配的术数概念词条。</div>
          ) : (
            <div className="glossary-cards-list">
              {filteredItems.map((item, idx) => (
                <div key={idx} className="glossary-card">
                  <div className="glossary-card-top">
                    <span className="glossary-tag">{item.tag}</span>
                    <span className="glossary-source">{item.source}</span>
                  </div>
                  <strong className="glossary-title">{item.title}</strong>
                  <p className="glossary-desc">{item.desc}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <footer>
          <BookOpen size={15} />
          <span>共收录 {filteredItems.length} 条结构化典籍概念与释义</span>
        </footer>
      </aside>
    </div>
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
          {[["all", "全部"], ["calendar", "历法"], ["zhouyi", "周易"], ["meihua", "梅花"], ["liuyao", "六爻"], ["liuren", "六壬"], ["qimen", "奇门"], ["bazi", "八字"], ["ziwei", "紫微"], ["fengshui", "风水"]].map(([id, label]) => (
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

function HistoryDrawer({ open, onClose, onLoadHistory }) {
  const [history, setHistory] = useState([]);
  const [importStatus, setImportStatus] = useState("");
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (open) {
      setHistory(getDeductionHistory());
      setImportStatus("");
    }
  }, [open]);

  const handleDelete = (id, e) => {
    e.stopPropagation();
    const updated = deleteDeductionHistory(id);
    setHistory(updated);
  };

  const handleClear = () => {
    if (window.confirm("确定要清空所有本地推演历史记录吗？")) {
      clearDeductionHistory();
      setHistory([]);
    }
  };

  const handleExport = (item, e) => {
    e.stopPropagation();
    const md = generateMarkdownReport(item.result, item.context);
    const dateStr = new Date(item.timestamp).toISOString().slice(0, 10);
    const filename = `推演报告_${item.question.slice(0, 8)}_${dateStr}.md`;
    downloadMarkdownFile(md, filename);
  };

  const handleExportAllJSON = () => {
    if (history.length === 0) {
      alert("当前暂无历史记录可导出。");
      return;
    }
    exportAllHistoryJSON();
  };

  const handleFileImport = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result;
      if (typeof content === "string") {
        const res = importHistoryJSON(content);
        if (res.success) {
          setHistory(getDeductionHistory());
          setImportStatus(`成功导入 ${res.count} 条案例（总计 ${res.total} 条）`);
        } else {
          setImportStatus(`导入失败：${res.error}`);
        }
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  if (!open) return null;

  return (
    <div className="drawer-layer" role="presentation" onMouseDown={onClose}>
      <aside className="rules-drawer history-drawer" role="dialog" aria-modal="true" aria-label="历史推演与案例库" onMouseDown={(e) => e.stopPropagation()}>
        <header>
          <div>
            <p className="section-kicker">LOCAL PERSISTENCE</p>
            <h2>历史推演与案例库</h2>
          </div>
          <div className="header-actions">
            <button className="history-json-btn" onClick={handleExportAllJSON} title="导出全部案例为 JSON 备份包">
              <Download size={14} />
              <span>备份导出</span>
            </button>
            <button className="history-json-btn" onClick={() => fileInputRef.current?.click()} title="从 JSON 文件导入案例包">
              <Upload size={14} />
              <span>导入备份</span>
            </button>
            <input
              type="file"
              ref={fileInputRef}
              accept=".json"
              style={{ display: "none" }}
              onChange={handleFileImport}
            />
            {history.length > 0 && (
              <button className="clear-history-btn" onClick={handleClear} title="清空全部历史">
                <Trash2 size={14} />
                <span>清空</span>
              </button>
            )}
            <button className="icon-button" onClick={onClose} aria-label="关闭历史抽屉"><X size={19} /></button>
          </div>
        </header>

        <div className="drawer-notice">
          <FileClock size={16} />
          <span>本地保存最近 50 次推演记录，支持一键复盘、Markdown 导出与 JSON 数据全量备份还原。</span>
        </div>

        {importStatus && (
          <div className="history-import-banner">
            <span>{importStatus}</span>
          </div>
        )}

        <div className="history-list-wrap">
          {history.length === 0 ? (
            <div className="drawer-loading">暂无历史推演记录。从左侧发起一次推演即可自动保存。</div>
          ) : (
            <div className="history-items-list">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="history-item-card"
                  onClick={() => {
                    onLoadHistory(item);
                    onClose();
                  }}
                >
                  <div className="item-top">
                    <div className="item-badges">
                      <span className="cat-badge">{item.category}</span>
                      <span className="scene-badge">{item.scene}</span>
                    </div>
                    <time>{new Date(item.timestamp).toLocaleString("zh-CN", { hour12: false })}</time>
                  </div>
                  <strong className="item-question">{item.question}</strong>
                  <p className="item-summary">{item.summary}</p>
                  <div className="item-actions">
                    <button className="btn-load-history">
                      <ArrowRight size={13} />
                      <span>复盘载入</span>
                    </button>
                    <button className="btn-export-history" onClick={(e) => handleExport(item, e)}>
                      <Download size={13} />
                      <span>导出</span>
                    </button>
                    <button className="btn-delete-history" onClick={(e) => handleDelete(item.id, e)} title="删除记录">
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <footer>
          <Database size={15} />
          <span>共 {history.length} 条本地推演存档</span>
        </footer>
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
  const [historyOpen, setHistoryOpen] = useState(false);
  const [glossaryOpen, setGlossaryOpen] = useState(false);
  const [rules, setRules] = useState([]);
  const [rulesLoading, setRulesLoading] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem("tianji_theme") || "paper");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("tianji_theme", theme);
  }, [theme]);

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

    // Generate fresh castNonce for each submission so automatic casting yields a new random seed
    const activeNonce = newCastNonce();
    const activeForm = { ...form, castNonce: activeNonce };
    setForm(activeForm);

    try {
      const response = await compareCalculations(buildCalculations(activeForm), {
        category: activeForm.category,
        question_summary: activeForm.question,
      });
      const ctx = { scene: activeForm.scene, category: activeForm.category, question: activeForm.question };
      setResult(response);
      setResultContext(ctx);
      setActiveTab("overview");
      setServiceOnline(true);
      setMobileInputOpen(false);

      // Auto save to local history
      saveDeductionHistory(response.task_id, ctx, response);

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

  const handleLoadHistory = (item) => {
    setResult(item.result);
    setResultContext(item.context);
    setActiveTab("overview");
    const cal = item.result?.module_results?.find((m) => m.module === "calendar")?.result;
    if (cal) setPreview(cal);
  };

  return (
    <div className="app-shell">
      <AppNavigation
        collapsed={navCollapsed}
        setCollapsed={setNavCollapsed}
        openRules={openRules}
        openHistory={() => setHistoryOpen(true)}
        openGlossary={() => setGlossaryOpen(true)}
        serviceOnline={serviceOnline}
        theme={theme}
        setTheme={setTheme}
      />
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
      <HistoryDrawer open={historyOpen} onClose={() => setHistoryOpen(false)} onLoadHistory={handleLoadHistory} />
      <GlossaryDrawer open={glossaryOpen} onClose={() => setGlossaryOpen(false)} />
    </div>
  );
}
