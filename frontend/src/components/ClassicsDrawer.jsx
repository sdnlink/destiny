import { useEffect, useState } from "react";
import { BookOpen, ExternalLink, Loader2, Search, X } from "lucide-react";
import { loadClassicsStatus, searchClassics } from "../lib/api";

const CATEGORY_LABELS = {
  mingli: "命理",
  yangzhai: "阳宅",
  kanyu: "堪舆",
  liuyao: "六爻",
  zhouyi: "周易",
  meihua: "梅花",
  qimen: "奇门",
  liuren: "六壬",
  ziwei: "紫微",
  calendar: "历法",
  xiangshu: "象数",
};

function categoryLabel(category) {
  return CATEGORY_LABELS[category] || category || "典籍";
}

function formatCount(value) {
  if (!Number.isFinite(Number(value))) return "—";
  return Number(value).toLocaleString("zh-CN");
}

export default function ClassicsDrawer({ open, onClose }) {
  const [status, setStatus] = useState(null);
  const [statusError, setStatusError] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    let active = true;
    setStatus(null);
    setStatusError("");
    loadClassicsStatus()
      .then((data) => {
        if (active) setStatus(data || null);
      })
      .catch((requestError) => {
        if (active) setStatusError(requestError.message || "典籍库状态读取失败");
      });
    return () => {
      active = false;
    };
  }, [open]);

  if (!open) return null;

  const unavailable = status?.available === false;

  const handleSearch = async (event) => {
    event.preventDefault();
    const keyword = query.trim();
    if (!keyword) {
      setResults([]);
      setSearched(false);
      setError("");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const rows = await searchClassics(keyword);
      setResults(Array.isArray(rows) ? rows : []);
      setSearched(true);
    } catch (requestError) {
      setResults([]);
      setSearched(true);
      setError(requestError.message || "典籍原文检索失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="drawer-layer" role="presentation" onMouseDown={onClose}>
      <aside className="rules-drawer classics-drawer" role="dialog" aria-modal="true" aria-label="典籍原文检索" onMouseDown={(event) => event.stopPropagation()}>
        <header>
          <div>
            <p className="section-kicker">CLASSICS SEARCH</p>
            <h2>典籍原文检索</h2>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="关闭典籍检索"><X size={19} /></button>
        </header>

        <form className="classics-search-form" onSubmit={handleSearch}>
          <Search size={16} />
          <input
            type="text"
            aria-label="典籍原文关键词"
            placeholder="输入关键词，例如「月令」「用神」「大游年」"
            maxLength={100}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <button type="submit" className="primary-button" disabled={loading || unavailable}>
            {loading ? <Loader2 size={14} className="spin" /> : <Search size={14} />}
            检索
          </button>
        </form>

        <div className="classics-status">
          {statusError ? (
            <span className="classics-status-warn">{statusError}，仍可尝试检索</span>
          ) : status === null ? (
            <span>正在读取典籍库…</span>
          ) : status.available === false ? (
            <span className="classics-status-warn">本地典籍库未就绪，暂不能检索原文。</span>
          ) : (
            <>
              <span>已收录 {formatCount(status.documents)} 部 · {formatCount(status.chunks)} 段 · {formatCount(status.characters)} 字</span>
            </>
          )}
        </div>

        <div className="classics-hits-wrap">
          {unavailable ? (
            <div className="drawer-loading">典籍库不可用。请先准备本地语料库，再重启服务。</div>
          ) : loading ? (
            <div className="drawer-loading">正在检索原文段落…</div>
          ) : error ? (
            <div className="drawer-loading classics-error">{error}</div>
          ) : !searched ? (
            <div className="drawer-loading">
              <BookOpen size={18} />
              <span>检索结果只展示本地已收录的原文段落与出处，不补写、不改写原文。</span>
            </div>
          ) : results.length === 0 ? (
            <div className="drawer-loading">未检索到匹配原文，可换关键词或缩短限定。</div>
          ) : (
            <div className="classics-hits">
              {results.map((passage) => (
                <article className="classics-hit" key={passage.classic_id || `${passage.document_id}-${passage.chunk_index}`}>
                  <div className="classics-hit-head">
                    <strong>{passage.title || "未题典籍"}</strong>
                    <span>{categoryLabel(passage.category)} · 第 {passage.chunk_index ?? "—"} 段 · 命中 {formatCount(passage.match_count)} 次</span>
                  </div>
                  <p>{passage.excerpt || "（本段无原文摘录）"}</p>
                  <div className="classics-hit-foot">
                    <span>{passage.license_name || "许可信息未标注"}</span>
                    {passage.source_url ? (
                      <a href={passage.source_url} target="_blank" rel="noreferrer">
                        查看原文
                        <ExternalLink size={12} />
                      </a>
                    ) : null}
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>

        <footer>
          <BookOpen size={15} />
          <span>{searched && !loading ? `本次命中 ${results.length} 段原文` : "按关键词检索本地典籍原文段落"}</span>
        </footer>
      </aside>
    </div>
  );
}
