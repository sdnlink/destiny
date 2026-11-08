/** 独立功能页共用的两栏外壳：左侧输入、右侧结果。 */
export function WorkspaceShell({ kicker, title, description, badge, sidebar, children }) {
  return (
    <main className="standalone-workspace">
      <header className="standalone-header">
        <div>
          <span className="section-kicker">{kicker}</span>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        {badge && <span className="standalone-mode-badge">{badge}</span>}
      </header>
      <div className="standalone-layout">
        <aside className="standalone-input-column">{sidebar}</aside>
        <section className="standalone-output">{children}</section>
      </div>
    </main>
  );
}
