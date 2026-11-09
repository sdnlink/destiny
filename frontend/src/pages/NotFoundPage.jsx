import { Link, useLocation } from "react-router-dom";
import { ArrowRight, Compass, SearchX } from "lucide-react";
import { ALL_MODULES } from "../lib/modules";

const QUICK_LINKS = ["zhouyi", "bazi", "ziwei", "liuyao", "fengshui"];

export default function NotFoundPage() {
  const location = useLocation();
  const quick = ALL_MODULES.filter((module) => QUICK_LINKS.includes(module.id));

  return (
    <main className="not-found-page">
      <span className="section-kicker">404 · PAGE NOT FOUND</span>
      <div className="not-found-icon"><SearchX size={40} /></div>
      <h1>没有这个页面</h1>
      <p>
        路径 <code>{location.pathname}</code> 不在功能模块清单中，可能链接已失效或地址输入有误。
      </p>
      <Link to="/" className="primary-button not-found-home">
        <Compass size={16} />
        返回首页
      </Link>
      <section className="not-found-quick">
        <h2>常用模块</h2>
        <div className="not-found-links">
          {quick.map((module) => (
            <Link key={module.id} to={module.to} className="not-found-link">
              {module.label}
              <ArrowRight size={14} />
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
