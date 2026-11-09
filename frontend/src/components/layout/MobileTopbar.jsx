import { Menu } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { ALL_MODULES } from "../../lib/modules";

export default function MobileTopbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const current = ALL_MODULES.find((module) => module.to === location.pathname);
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
        {ALL_MODULES.map((module) => (
          <option key={module.id} value={module.to}>{module.label}</option>
        ))}
      </select>
      <button className="icon-button" onClick={() => document.querySelector(".app-navigation")?.classList.toggle("mobile-open")} aria-label="切换导航">
        <Menu size={20} />
      </button>
    </div>
  );
}
