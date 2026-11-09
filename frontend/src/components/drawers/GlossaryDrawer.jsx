import { useState } from "react";
import { BookOpen, Search, X } from "lucide-react";
import { GLOSSARY_CATEGORIES, GLOSSARY_ITEMS } from "../../lib/glossary";

export default function GlossaryDrawer({ open, onClose }) {
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
