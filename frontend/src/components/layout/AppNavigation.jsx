import {
  Archive,
  BookOpen,
  BookOpenCheck,
  CalendarRange,
  Compass,
  Grid3X3,
  Layers3,
  Library,
  Moon,
  Mountain,
  Orbit,
  Palette,
  PanelLeftClose,
  PanelLeftOpen,
  Sparkles,
  Sun,
  Workflow,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { MODULE_GROUPS } from "../../lib/modules";

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

export default function AppNavigation({
  collapsed,
  setCollapsed,
  onOpenHistory,
  onOpenRules,
  onOpenGlossary,
  onOpenClassics,
  serviceOnline,
  theme,
  setTheme,
}) {
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
