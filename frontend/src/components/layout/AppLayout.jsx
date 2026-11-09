import { Suspense, useEffect, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import ClassicsDrawer from "../ClassicsDrawer";
import GlossaryDrawer from "../drawers/GlossaryDrawer";
import HistoryDrawer from "../drawers/HistoryDrawer";
import RulesDrawer from "../drawers/RulesDrawer";
import AppNavigation from "./AppNavigation";
import MobileTopbar from "./MobileTopbar";
import { checkHealth, loadRules } from "../../lib/api";
import {
  MODULE_BY_PATH,
  pageTitleForPath,
  pushRecentModule,
} from "../../lib/modules";

// 本地历史存档的 scene → 该场景现在所属的模块页（复盘时回到对应模块）
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

export default function AppLayout() {
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
  const location = useLocation();

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("tianji_theme", theme);
  }, [theme]);

  useEffect(() => {
    checkHealth().then(() => setServiceOnline(true)).catch(() => setServiceOnline(false));
  }, []);

  // 浏览器标签标题跟随路由；顺带记录「最近使用」，供首页快捷入口使用
  useEffect(() => {
    document.title = pageTitleForPath(location.pathname);
    if (MODULE_BY_PATH[location.pathname]) pushRecentModule(location.pathname);
  }, [location.pathname]);

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
