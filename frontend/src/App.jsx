import {
  lazy,
  Suspense,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  Archive,
  ArrowRight,
  BookOpen,
  BookOpenCheck,
  CalendarRange,
  Compass,
  Database,
  Download,
  FileClock,
  Grid3X3,
  Layers3,
  Library,
  Menu,
  Moon,
  Mountain,
  Orbit,
  PanelLeftClose,
  PanelLeftOpen,
  Palette,
  Search,
  ShieldCheck,
  Sparkles,
  Sun,
  Trash2,
  Upload,
  Workflow,
  X,
} from "lucide-react";
import {
  BrowserRouter,
  Navigate,
  NavLink,
  Outlet,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import ClassicsDrawer from "./components/ClassicsDrawer";
import { MODULE_GROUPS } from "./lib/modules";
import { GLOSSARY_CATEGORIES, GLOSSARY_ITEMS } from "./lib/glossary";
import { checkHealth, loadRules } from "./lib/api";
import { generateMarkdownReport, downloadMarkdownFile } from "./lib/export";
import { migrateHistoryItem } from "./lib/sessionMigration";
import { listSessions } from "./lib/sessionApi";
import {
  clearDeductionHistory,
  deleteDeductionHistory,
  exportAllHistoryJSON,
  getDeductionHistory,
  importHistoryJSON,
} from "./lib/storage";
import HomePage from "./pages/HomePage";
import ConsultModulePage from "./pages/ConsultModulePage";
import BaziPage from "./pages/BaziPage";
import ZiweiPage from "./pages/ZiweiPage";

const WorkflowPanel = lazy(() => import("./components/WorkflowPanel"));
const FengshuiPanel = lazy(() => import("./components/fengshui/FengshuiPanel"));

const NAV_ICONS = {
  zhouyi: BookOpen,
  meihua: Sparkles,
  liuyao: Grid3X3,
  bazi: CalendarRange,
  ziwei: Orbit,
  qimen: Compass,
  liuren: Workflow,
  fengshui: Mountain,
  workflow: Layers3,
};

const SCENE_TO_ROUTE = {
  zhouyi: "/zhouyi",
  meihua: "/meihua",
  liuyao: "/liuyao",
  qimen: "/qimen",
  liuren: "/liuren",
  ziwei: "/ziwei",
  natal: "/bazi",
  liunian: "/bazi",
  bazi: "/bazi",
};

function AppNavigation({ collapsed, setCollapsed, onOpenHistory, onOpenRules, onOpenGlossary, onOpenClassics, serviceOnline, theme, setTheme }) {
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
        {MODULE_GROUPS.map((group) => (
          <div className="nav-group" key={group.id}>
            {!collapsed && <span className="nav-group-label">{group.label}</span>}
            {group.modules.map((module) => {
              const Icon = NAV_ICONS[module.id] || Sparkles;
              return (
                <NavLink
                  key={module.id}
                  to={module.to}
                  className={({ isActive }) => (isActive ? "active" : "")}
                  title={module.desc}
                >
                  <Icon size={18} />
                  <span>{module.label}</span>
                </NavLink>
              );
            })}
          </div>
        ))}
        <div className="nav-group">
          {!collapsed && <span className="nav-group-label">资料</span>}
          <button onClick={onOpenHistory} title="历史推演记录、案例库与 JSON 备份导入导出"><Archive size={18} /><span>历史与案例</span></button>
          <button onClick={onOpenRules} title="规则目录"><BookOpenCheck size={18} /><span>规则目录</span></button>
          <button onClick={onOpenGlossary} title="术数典籍与核心概念速查"><BookOpen size={18} /><span>概念速查</span></button>
          <button onClick={onOpenClassics} title="在本地典籍库检索原文段落与出处"><Library size={18} /><span>典籍检索</span></button>
        </div>
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

  const filteredItems = (GLOSSARY_ITEMS || []).filter((item) => {
    const matchCat = selectedCat === "all" || item.category === selectedCat;
    const matchQuery =
      !searchQuery.trim() ||
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.desc.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.source.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.tag.toLowerCase().includes(searchQuery.toLowerCase());
    return matchCat && matchQuery;
  });

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
          {(GLOSSARY_CATEGORIES || []).map(({ id, label }) => (
            <button key={id} className={selectedCat === id ? "active" : ""} onClick={() => setSelectedCat(id)}>{label}</button>
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

function HistoryDrawer({ open, onClose, onLoadHistory, onOpenWorkflowSession }) {
  const [history, setHistory] = useState([]);
  const [importStatus, setImportStatus] = useState("");
  const [migratingId, setMigratingId] = useState(null);
  const [migrationError, setMigrationError] = useState("");
  const [backendSessions, setBackendSessions] = useState([]);
  const [backendLoading, setBackendLoading] = useState(false);
  const [backendError, setBackendError] = useState("");
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (open) {
      setHistory(getDeductionHistory());
      setImportStatus("");
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setBackendLoading(true);
    setBackendError("");
    listSessions(50)
      .then((rows) => { if (!cancelled) setBackendSessions(Array.isArray(rows) ? rows : []); })
      .catch((requestError) => { if (!cancelled) { setBackendSessions([]); setBackendError(requestError.message); } })
      .finally(() => { if (!cancelled) setBackendLoading(false); });
    return () => { cancelled = true; };
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
    if (history.length === 0) { alert("当前暂无历史记录可导出。"); return; }
    exportAllHistoryJSON();
  };

  const handleMigrate = async (item, e) => {
    e.stopPropagation();
    if (migratingId) return;
    setMigratingId(item.id);
    setMigrationError("");
    try {
      const { sessionId } = await migrateHistoryItem(item);
      onOpenWorkflowSession(sessionId);
    } catch (error) {
      setMigrationError(error.message);
    } finally {
      setMigratingId(null);
    }
  };

  const handleFileImport = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result;
      if (typeof content === "string") {
        const res = importHistoryJSON(content);
        if (res.success) { setHistory(getDeductionHistory()); setImportStatus(`成功导入 ${res.count} 条案例（总计 ${res.total} 条）`); }
        else { setImportStatus(`导入失败：${res.error}`); }
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
            <button className="history-json-btn" onClick={handleExportAllJSON} title="导出全部案例为 JSON 备份包"><Download size={14} /><span>备份导出</span></button>
            <button className="history-json-btn" onClick={() => fileInputRef.current?.click()} title="从 JSON 文件导入案例包"><Upload size={14} /><span>导入备份</span></button>
            <input type="file" ref={fileInputRef} accept=".json" style={{ display: "none" }} onChange={handleFileImport} />
            {history.length > 0 && (
              <button className="clear-history-btn" onClick={handleClear} title="清空全部历史"><Trash2 size={14} /><span>清空</span></button>
            )}
            <button className="icon-button" onClick={onClose} aria-label="关闭历史抽屉"><X size={19} /></button>
          </div>
        </header>

        <div className="drawer-notice">
          <FileClock size={16} />
          <span>本地保存最近 50 次推演记录，可复盘、导出 Markdown 或整包 JSON 备份；也可用「转到后端」按存档时刻重建为交互推演会话。</span>
        </div>

        {importStatus && (<div className="history-import-banner"><span>{importStatus}</span></div>)}
        {migrationError && (<div className="history-import-banner"><span>转到后端会话失败：{migrationError}</span></div>)}

        <div className="history-list-wrap backend-sessions" role="region" aria-label="后端推演会话">
          <p className="section-kicker">SERVER SESSIONS</p>
          {backendError ? (
            <div className="drawer-loading">后端会话不可达：{backendError}（本地存档仍可正常使用）</div>
          ) : backendLoading ? (
            <div className="drawer-loading">正在读取后端会话…</div>
          ) : backendSessions.length === 0 ? (
            <div className="drawer-loading">后端暂无推演会话。切到「交互推演」新建一次即可同步到这里。</div>
          ) : (
            <div className="history-items-list">
              {backendSessions.map((session) => (
                <div key={session.session_id} className="history-item-card" onClick={() => onOpenWorkflowSession(session.session_id)}>
                  <div className="item-top">
                    <div className="item-badges">
                      <span className="cat-badge">{session.system || "auto"}</span>
                      <span className="scene-badge">{session.status || "draft"}</span>
                    </div>
                    <time>{session.updated_at ? new Date(session.updated_at).toLocaleString("zh-CN", { hour12: false }) : ""}</time>
                  </div>
                  <strong className="item-question">{session.question || "（无题）"}</strong>
                  <div className="item-actions">
                    <button className="btn-load-history"><ArrowRight size={13} /><span>在交互推演中打开</span></button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="history-list-wrap">
          {history.length === 0 ? (
            <div className="drawer-loading">暂无历史推演记录。从左侧进入某个功能模块发起一次推演即可自动保存。</div>
          ) : (
            <div className="history-items-list">
              {history.map((item) => (
                <div key={item.id} className="history-item-card" onClick={() => onLoadHistory(item)}>
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
                    <button className="btn-load-history"><ArrowRight size={13} /><span>复盘载入</span></button>
                    <button className="btn-export-history" onClick={(e) => handleExport(item, e)}><Download size={13} /><span>导出</span></button>
                    <button className="btn-export-history" onClick={(e) => handleMigrate(item, e)} disabled={Boolean(migratingId)} title="用存档的事由与起盘时刻在后端重建一个交互推演会话">
                      <ArrowRight size={13} /><span>{migratingId === item.id ? "重建中…" : "转到后端"}</span>
                    </button>
                    <button className="btn-delete-history" onClick={(e) => handleDelete(item.id, e)} title="删除记录"><Trash2 size={13} /></button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <footer>
          <Database size={15} />
          <span>共 {history.length} 条本地推演存档 · 后端 {backendSessions.length} 个会话</span>
        </footer>
      </aside>
    </div>
  );
}

function MobileTopbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const options = MODULE_GROUPS.flatMap((group) => group.modules);
  const current = options.find((module) => module.to === location.pathname);
  return (
    <div className="mobile-topbar">
      <div className="brand-mark"><span>☰</span><span>☷</span></div>
      <strong>天机演象</strong>
      <select
        className="mobile-view-select"
        value={current ? current.to : "/"}
        onChange={(event) => navigate(event.target.value)}
        aria-label="切换功能模块"
      >
        <option value="/">首页</option>
        {options.map((module) => (
          <option key={module.id} value={module.to}>{module.label}</option>
        ))}
      </select>
      <button className="icon-button" onClick={() => document.querySelector(".app-navigation")?.classList.toggle("mobile-open")} aria-label="切换导航">
        <Menu size={20} />
      </button>
    </div>
  );
}

function Layout() {
  const [navCollapsed, setNavCollapsed] = useState(false);
  const [rulesOpen, setRulesOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [glossaryOpen, setGlossaryOpen] = useState(false);
  const [classicsOpen, setClassicsOpen] = useState(false);
  const [rules, setRules] = useState([]);
  const [rulesLoading, setRulesLoading] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem("tianji_theme") || "paper");
  const [serviceOnline, setServiceOnline] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("tianji_theme", theme);
  }, [theme]);

  useEffect(() => {
    checkHealth().then(() => setServiceOnline(true)).catch(() => setServiceOnline(false));
  }, []);

  const openRules = async () => {
    setRulesOpen(true);
    if (rules.length) return;
    setRulesLoading(true);
    try {
      const response = await loadRules();
      setRules(response.data || response);
    } catch (requestError) {
      setRules([]);
    } finally {
      setRulesLoading(false);
    }
  };

  const openWorkflowSession = (sessionId) => {
    setHistoryOpen(false);
    navigate("/workflow", { state: { recoverSessionId: sessionId } });
  };

  const handleLoadHistory = (item) => {
    setHistoryOpen(false);
    navigate(SCENE_TO_ROUTE[item.scene] || "/");
  };

  return (
    <div className="app-shell">
      <AppNavigation
        collapsed={navCollapsed}
        setCollapsed={setNavCollapsed}
        onOpenHistory={() => setHistoryOpen(true)}
        onOpenRules={openRules}
        onOpenGlossary={() => setGlossaryOpen(true)}
        onOpenClassics={() => setClassicsOpen(true)}
        serviceOnline={serviceOnline}
        theme={theme}
        setTheme={setTheme}
      />
      <MobileTopbar />
      <Suspense fallback={<div className="loading-placeholder">正在加载…</div>}>
        <Outlet />
      </Suspense>
      <RulesDrawer open={rulesOpen} onClose={() => setRulesOpen(false)} rules={rules} loading={rulesLoading} />
      <HistoryDrawer
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        onLoadHistory={handleLoadHistory}
        onOpenWorkflowSession={openWorkflowSession}
      />
      <GlossaryDrawer open={glossaryOpen} onClose={() => setGlossaryOpen(false)} />
      <ClassicsDrawer open={classicsOpen} onClose={() => setClassicsOpen(false)} />
    </div>
  );
}

function WorkflowRoute() {
  const location = useLocation();
  const navigate = useNavigate();
  const recoverSessionId = location.state?.recoverSessionId;
  return (
    <WorkflowPanel
      recoverSessionId={recoverSessionId}
      // 恢复完成后只清掉 location.state（防止再次进入时重复恢复），用户仍留在 /workflow
      onRecovered={() => navigate("/workflow", { replace: true, state: null })}
    />
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="zhouyi" element={<ConsultModulePage moduleKey="zhouyi" />} />
          <Route path="meihua" element={<ConsultModulePage moduleKey="meihua" />} />
          <Route path="liuyao" element={<ConsultModulePage moduleKey="liuyao" />} />
          <Route path="qimen" element={<ConsultModulePage moduleKey="qimen" />} />
          <Route path="liuren" element={<ConsultModulePage moduleKey="liuren" />} />
          <Route path="bazi" element={<BaziPage />} />
          <Route path="ziwei" element={<ZiweiPage />} />
          <Route path="fengshui" element={<FengshuiPanel />} />
          <Route path="workflow" element={<WorkflowRoute />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
