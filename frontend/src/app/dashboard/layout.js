"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Users, Briefcase, CheckSquare, ExternalLink } from "lucide-react";

export default function DashboardLayout({ children }) {
  const pathname = usePathname();

  const navItems = [
    { name: 'Overview', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Contacts', path: '/dashboard/customers', icon: Users },
    { name: 'Pipeline', path: '/dashboard/deals', icon: Briefcase },
    { name: 'Tasks', path: '/dashboard/tasks', icon: CheckSquare },
  ];

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden">
      
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r border-border bg-surface flex flex-col">
        <div className="p-6 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-text flex items-center justify-center text-surface shadow-soft">
              <span className="font-serif font-bold text-lg leading-none">D</span>
            </div>
            <div>
              <div className="font-semibold tracking-tight text-sm text-text">Digital FTE</div>
              <div className="text-xs text-muted">Customer Success</div>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-4 py-4 flex flex-col gap-1">
          <div className="px-2 text-[0.65rem] font-medium text-muted uppercase tracking-wider mb-2">Workspace</div>
          
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.path;
            
            return (
              <Link
                key={item.name}
                href={item.path}
                className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                  isActive 
                  ? 'bg-accent/10 text-accent' 
                  : 'text-text/70 hover:bg-border hover:text-text'
                }`}
              >
                <Icon size={16} strokeWidth={isActive ? 2.5 : 2} />
                {item.name}
              </Link>
            );
          })}

          <div className="px-2 text-[0.65rem] font-medium text-muted uppercase tracking-wider mb-2 mt-6">Quick Links</div>
          <Link
            href="/"
            target="_blank"
            className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium text-text/70 hover:bg-border hover:text-text transition-all duration-200"
          >
            <ExternalLink size={16} />
            Landing Page
          </Link>
        </nav>

        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-2 px-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
            </span>
            <span className="text-xs font-medium text-muted">Agent System Online</span>
          </div>
        </div>
      </aside>

      {/* Main Container */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-14 border-b border-border bg-surface flex items-center justify-between px-6 flex-shrink-0">
          <div className="text-sm font-medium text-muted">
            {pathname.replace('/dashboard', '').replace('/', '') || 'Overview'}
          </div>
          <div className="flex items-center gap-4">
            <div className="text-xs font-medium text-muted">
              {new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
            </div>
            <div className="w-7 h-7 rounded-full bg-border flex items-center justify-center text-xs font-semibold text-text cursor-pointer hover:bg-black/5 transition-colors">
              A
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-8 bg-background">
          <div className="max-w-6xl mx-auto w-full animate-fade-in">
            {children}
          </div>
        </main>
      </div>
      
    </div>
  );
}
