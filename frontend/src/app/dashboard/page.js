"use client";

import { useState, useEffect } from "react";
import { Activity, Clock, Server, CheckCircle2 } from "lucide-react";

export default function DashboardOverview() {
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  
  const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const fetchData = async () => {
      try {
        const statsRes = await fetch(`${BACKEND}/api/v1/crm/stats`);
        if (statsRes.ok) setStats(await statsRes.json());
        
        const logsRes = await fetch(`${BACKEND}/api/v1/crm/audit-logs?limit=8`);
        if (logsRes.ok) setLogs(await logsRes.json());
      } catch (err) {
        console.error(err);
      }
    };
    
    fetchData();
    const id = setInterval(fetchData, 10000);
    return () => clearInterval(id);
  }, [BACKEND]);

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="font-serif text-3xl font-medium tracking-tight text-text">Overview</h1>
        <p className="text-muted text-sm mt-1">Real-time system pulse and performance metrics.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: "System Uptime", value: "99.99%", icon: Server },
          { label: "Avg Response", value: "< 1.2s", icon: Clock },
          { label: "Availability", value: "24 / 7", icon: CheckCircle2 },
          { label: "Automated Actions", value: stats?.actions_taken?.toLocaleString() || "—", icon: Activity },
        ].map((s, i) => (
          <div key={i} className="bg-surface rounded-xl p-6 border border-border shadow-soft flex flex-col justify-between hover:border-border/80 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <s.icon size={18} className="text-muted" />
            </div>
            <div>
              <div className="text-2xl font-semibold text-text tracking-tight">{s.value}</div>
              <div className="text-xs font-medium text-muted uppercase tracking-wider mt-1">{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Activity Logs */}
      <div className="bg-surface rounded-xl border border-border overflow-hidden shadow-soft">
        <div className="px-6 py-4 border-b border-border bg-background/50 flex justify-between items-center">
          <h2 className="text-sm font-semibold text-text">Live System Feed</h2>
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            <span className="text-[0.65rem] uppercase tracking-wider text-muted font-medium">Recording</span>
          </div>
        </div>
        <div className="p-0">
          {logs.length > 0 ? (
            <div className="divide-y divide-border">
              {logs.map((log) => (
                <div key={log.id} className="flex px-6 py-4 hover:bg-background/40 transition-colors">
                  <div className="w-24 flex-shrink-0 text-xs text-muted font-medium pt-0.5">
                    {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  <div className="flex-1 text-sm text-text/80">
                    {log.message}
                  </div>
                  <div className="flex-shrink-0 pl-4">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
                      ${log.action_type.includes('success') ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-blue-50 text-blue-700 border border-blue-200'}`}>
                      {log.action_type.split('_')[0]}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="px-6 py-8 text-center text-sm text-muted">
              Listening for events...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
