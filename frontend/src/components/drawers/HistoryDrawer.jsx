import { useEffect, useRef, useState } from "react";
import { ArrowRight, Database, Download, FileClock, Trash2, Upload, X } from "lucide-react";
import { downloadMarkdownFile, generateMarkdownReport } from "../../lib/export";
import { migrateHistoryItem } from "../../lib/sessionMigration";
import { listSessions } from "../../lib/sessionApi";
import {
  clearDeductionHistory,
  deleteDeductionHistory,
  exportAllHistoryJSON,
  getDeductionHistory,
  importHistoryJSON,
} from "../../lib/storage";

export default function HistoryDrawer({ open, onClose, onLoadHistory, onOpenWorkflowSession }) {
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
