import Link from 'next/link';
import { useRouter } from 'next/router';

const IconHome       = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>;
const IconUsers      = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>;
const IconBriefcase  = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>;
const IconCheckSq    = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>;
const IconExternal   = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>;

export default function Layout({ children }) {
  const router = useRouter();

  const navItems = [
    { name: 'Overview',  path: '/dashboard',           icon: <IconHome /> },
    { name: 'Contacts',  path: '/dashboard/customers', icon: <IconUsers /> },
    { name: 'Pipeline',  path: '/dashboard/deals',     icon: <IconBriefcase /> },
    { name: 'Tasks',     path: '/dashboard/tasks',     icon: <IconCheckSq /> },
  ];

  return (
    <div className="crm-app">

      {/* ── Sidebar ── */}
      <aside className="crm-sidebar">
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <div className="sidebar-brand-dot">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3"/>
                <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
              </svg>
            </div>
            <div>
              <div className="sidebar-brand-name">Digital FTE</div>
              <div className="sidebar-brand-tag">Customer Success</div>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="sidebar-section-label">Workspace</div>
          {navItems.map(item => {
            const active = router.pathname === item.path;
            return (
              <Link key={item.name} href={item.path} className={`nav-item${active ? ' active' : ''}`}>
                <span className="nav-icon">{item.icon}</span>
                <span className="nav-text">{item.name}</span>
              </Link>
            );
          })}

          <div className="sidebar-section-label" style={{ marginTop: '0.75rem' }}>Quick links</div>
          <a href="/" target="_blank" rel="noreferrer" className="nav-item">
            <span className="nav-icon"><IconExternal /></span>
            <span className="nav-text">Contact form</span>
          </a>
        </nav>

        <div className="sidebar-footer">
          <div className="agent-status">
            <span className="live-dot" aria-label="System active" />
            <span>Agent active</span>
          </div>
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="crm-main-container">

        {/* Top bar */}
        <header className="crm-topbar">
          <div className="crm-topbar-search">
            <input
              type="search"
              placeholder="Search contacts, deals, tasks…"
              className="form-control no-icon"
              style={{ paddingLeft: '1rem', width: 280, height: 38, fontSize: '0.875rem' }}
              aria-label="Search"
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>
              {new Date().toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })}
            </div>
            <div className="crm-topbar-avatar" title="Your account">A</div>
          </div>
        </header>

        {/* Page content */}
        <main className="crm-content">
          {children}
        </main>
      </div>

    </div>
  );
}
